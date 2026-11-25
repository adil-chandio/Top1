#!/usr/bin/env python3
"""Bounded, bot-block-free YouTube outlier scanner for Top1 Stage 1 research.

Design rules (non-negotiable):
  * Official YouTube Data API v3 only -- no yt-dlp, no scraping, no retries on blocked routes.
  * The API key is sent as an HTTP header, never in a URL, log line or artifact.
  * Every request is bounded (count, page size, response bytes, timeout).
  * Sameness: outlier_multiple = views / median(10 nearest surrounding uploads,
    excluding the candidate itself). Candidates with fewer than 5 usable neighbours
    are dropped instead of being scored on weak evidence.
  * Offline fixture mode exists for deterministic tests; it never reads a key.

Usage (real scan):
  YOUTUBE_API_KEY=... python3 tools/research-agent/outlier_scan.py \
    --keywords "everyday physics,hidden engineering" \
    --min-views 3000 --max-subs 100000 --min-ratio 2.0 \
    --format short --out /tmp/research_vision/outlier_scan.json

Usage (offline test):
  python3 tools/research-agent/outlier_scan.py --fixture tests/fixture.json --out /tmp/out.json
"""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import json
import os
from pathlib import Path
import re
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request

API_ROOT = "https://www.googleapis.com/youtube/v3/"
USER_AGENT = "Top1OutlierScan/1.0 (bounded research; official API only)"
KEY_NAMES = ("YOUTUBE_API_KEY", "YT_API_KEY", "YT_KEY", "YTAP1", "YTAPI1")

MAX_KEYWORDS = 5
MAX_RESULTS_PER_KEYWORD = 10
MAX_UPLOADS_PER_CHANNEL = 30
SURROUNDING_UPLOADS = 10
MIN_SURROUNDING_UPLOADS = 5
MAX_RESPONSE_BYTES = 3_000_000
TIMEOUT_SECONDS = 25
MAX_ERRORS = 20
MAX_OUTLIERS = 25

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
CHANNEL_ID = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
KEYWORD = re.compile(r"^[\w\s'\-.]+$", re.UNICODE)


class FetchError(Exception):
    """Sanitized fetch failure: never carries a URL, key or response body."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # A credential in a header must never survive a redirect to another host.
        return None


def get_json(url: str, key: str | None = None) -> dict:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if key:
        headers["X-Goog-Api-Key"] = key
    request = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise FetchError("response exceeded size limit")
        body = json.loads(payload)
    except urllib.error.HTTPError as exc:
        raise FetchError(f"HTTP {exc.code}") from None
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        raise FetchError("network or JSON error") from None
    if not isinstance(body, dict):
        raise FetchError("unexpected response shape")
    return body


class CountingFetch:
    """Wraps the fetch callable and accounts for quota without logging URLs."""

    def __init__(self, inner, stats: dict):
        self.inner = inner
        self.stats = stats

    def __call__(self, url: str, key: str | None = None) -> dict:
        self.stats["api_calls"] += 1
        endpoint = urllib.parse.urlsplit(url).path.rsplit("/", 1)[-1]
        self.stats["quota_units_estimate"] += 100 if endpoint == "search" else 1
        return self.inner(url, key=key)


class FixtureFetch:
    """Deterministic offline fetch. Matches endpoint + required query params."""

    def __init__(self, fixture: dict):
        entries = fixture.get("responses")
        if not isinstance(entries, list):
            raise ValueError("fixture must contain a 'responses' list")
        self.entries = entries

    def __call__(self, url: str, key: str | None = None) -> dict:
        if key is not None:
            raise FetchError("fixture mode must never use an API key")
        parts = urllib.parse.urlsplit(url)
        endpoint = parts.path.rsplit("/", 1)[-1]
        query = {k: v[0] for k, v in urllib.parse.parse_qs(parts.query).items()}
        for entry in self.entries:
            if entry.get("endpoint") != endpoint:
                continue
            required = entry.get("params", {})
            if all(query.get(k) == str(v) for k, v in required.items()):
                return json.loads(json.dumps(entry["body"]))
        raise FetchError(f"no fixture response for {endpoint}")


def api_get(endpoint: str, params: dict, key: str | None, fetch) -> dict:
    url = API_ROOT + endpoint + "?" + urllib.parse.urlencode(params)
    return fetch(url, key=key)


def parse_keywords(raw: str) -> list[str]:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("keywords must not be empty")
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts or len(parts) > MAX_KEYWORDS:
        raise ValueError(f"provide 1-{MAX_KEYWORDS} comma-separated keywords")
    seen: set[str] = set()
    result: list[str] = []
    for part in parts:
        if len(part) > 80 or not KEYWORD.fullmatch(part):
            raise ValueError("keyword contains unsupported characters or is too long")
        if part.lower() not in seen:
            seen.add(part.lower())
            result.append(part)
    return result


def positive_int(value: str, name: str, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be an integer") from None
    if not 1 <= number <= maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}")
    return number


def positive_float(value: str, name: str, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number") from None
    if not 0 < number <= maximum:
        raise ValueError(f"{name} must be greater than 0 and at most {maximum}")
    return number


def parse_format(value: str) -> str:
    choice = value.strip().lower()
    if choice not in {"short", "long", "both"}:
        raise ValueError("format must be short, long or both")
    return choice


def resolve_key(env: dict) -> str:
    for name in KEY_NAMES:
        value = env.get(name)
        if value and value.strip():
            return value.strip()
    raise SystemExit("No YouTube API key found. Set YOUTUBE_API_KEY (or a documented alias).")


def iso_datetime(value) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def published_after(lookback_days: int, now: dt.datetime | None = None) -> str:
    moment = now or dt.datetime.now(dt.timezone.utc)
    stamp = (moment - dt.timedelta(days=lookback_days)).replace(microsecond=0)
    return stamp.isoformat().replace("+00:00", "Z")


def search_candidates(keyword: str, after: str, key: str | None, fetch) -> list[dict]:
    body = api_get("search", {
        "part": "snippet", "type": "video", "order": "date",
        "publishedAfter": after, "maxResults": str(MAX_RESULTS_PER_KEYWORD), "q": keyword,
    }, key, fetch)
    found: list[dict] = []
    for item in body.get("items", []):
        video_id = (item.get("id") or {}).get("videoId")
        snippet = item.get("snippet") or {}
        if not isinstance(video_id, str) or not VIDEO_ID.fullmatch(video_id):
            continue
        found.append({
            "video_id": video_id,
            "keyword": keyword,
            "title": snippet.get("title"),
            "channel_id": snippet.get("channelId"),
            "channel_title": snippet.get("channelTitle"),
            "published_at": snippet.get("publishedAt"),
        })
    return found


def video_details(ids: list[str], key: str | None, fetch) -> dict[str, dict]:
    details: dict[str, dict] = {}
    unique = list(dict.fromkeys(v for v in ids if isinstance(v, str) and VIDEO_ID.fullmatch(v)))
    for start in range(0, len(unique), 50):
        chunk = unique[start:start + 50]
        body = api_get("videos", {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(chunk), "maxResults": "50",
        }, key, fetch)
        for item in body.get("items", []):
            if isinstance(item.get("id"), str):
                details[item["id"]] = item
    return details


def channel_upload_playlists(channel_ids: list[str], key: str | None, fetch) -> dict[str, str]:
    playlists: dict[str, str] = {}
    unique = list(dict.fromkeys(c for c in channel_ids if isinstance(c, str) and CHANNEL_ID.fullmatch(c)))
    for start in range(0, len(unique), 50):
        chunk = unique[start:start + 50]
        body = api_get("channels", {
            "part": "contentDetails", "id": ",".join(chunk), "maxResults": "50",
        }, key, fetch)
        for item in body.get("items", []):
            uploads = ((item.get("contentDetails") or {}).get("relatedPlaylists") or {}).get("uploads")
            if isinstance(item.get("id"), str) and isinstance(uploads, str):
                playlists[item["id"]] = uploads
    return playlists


def playlist_video_ids(playlist_id: str, key: str | None, fetch) -> list[str]:
    body = api_get("playlistItems", {
        "part": "contentDetails", "playlistId": playlist_id,
        "maxResults": str(MAX_UPLOADS_PER_CHANNEL),
    }, key, fetch)
    ids: list[str] = []
    for item in body.get("items", []):
        video_id = ((item.get("contentDetails") or {}).get("videoId"))
        if isinstance(video_id, str) and VIDEO_ID.fullmatch(video_id):
            ids.append(video_id)
    return ids


def as_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def duration_seconds(value) -> int | None:
    if not isinstance(value, str) or not value.startswith("PT"):
        return None
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value)
    if not match:
        return None
    hours, minutes, seconds = (int(x or 0) for x in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def thumbnail_urls(video_id: str, snippet: dict) -> dict[str, str]:
    thumbs = snippet.get("thumbnails") if isinstance(snippet, dict) else {}
    thumbs = thumbs if isinstance(thumbs, dict) else {}
    best = None
    for size in ("maxres", "high", "medium", "default"):
        if isinstance(thumbs.get(size), dict) and thumbs[size].get("url"):
            best = thumbs[size]["url"]
            break
    return {
        # maxresdefault is not guaranteed to exist; the API-provided URL is the safe one.
        "thumbnail_url": best or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        "thumbnail_maxres": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
    }


def median_surrounding(
    video_id: str, published_at, uploads: list[dict], count: int = SURROUNDING_UPLOADS
) -> tuple[float | None, int]:
    anchor = iso_datetime(published_at)
    if anchor is None:
        return None, 0
    neighbours = []
    for upload in uploads:
        if upload["video_id"] == video_id:
            continue
        stamp = iso_datetime(upload.get("published_at"))
        if stamp is None or not isinstance(upload.get("views"), int):
            continue
        neighbours.append((abs((stamp - anchor).total_seconds()), upload["video_id"], upload["views"]))
    neighbours.sort(key=lambda row: (row[0], row[1]))
    chosen = neighbours[:count]
    if len(chosen) < MIN_SURROUNDING_UPLOADS:
        return None, len(chosen)
    return float(statistics.median([row[2] for row in chosen])), len(chosen)


def sanitize_error(message, key: str | None) -> str:
    """Defence in depth: even a misbehaving fetch cannot leak the key into an artifact."""
    text = str(message)
    if key:
        text = text.replace(key, "[REDACTED]")
    return text[:200]


def record_error(errors: list[str], message: str, key: str | None = None) -> None:
    if len(errors) < MAX_ERRORS:
        errors.append(sanitize_error(message, key))


def scan(*, keywords: list[str], min_views: int, max_subs: int, min_ratio: float,
         fmt: str, lookback_days: int, key: str | None, fetch, now: dt.datetime | None = None,
         limit: int = MAX_OUTLIERS) -> dict:
    stats = {"api_calls": 0, "quota_units_estimate": 0}
    counted = CountingFetch(fetch, stats)
    after = published_after(lookback_days, now)
    errors: list[str] = []
    excluded: Counter[str] = Counter()
    candidates_seen = 0
    qualified: list[dict] = []

    caches: dict[str, dict] = {"details": {}, "playlists": {}, "uploads": {}}

    def details_for(ids: list[str]) -> dict[str, dict]:
        missing = [v for v in dict.fromkeys(ids) if v not in caches["details"]]
        if missing:
            try:
                caches["details"].update(video_details(missing, key, counted))
            except FetchError as exc:
                record_error(errors, f"videos.list: {exc}", key)
        return {v: caches["details"][v] for v in ids if v in caches["details"]}

    for keyword in keywords:
        try:
            found = search_candidates(keyword, after, key, counted)
        except FetchError as exc:
            record_error(errors, f"search.list: {exc}", key)
            continue
        candidates_seen += len(found)
        details = details_for([c["video_id"] for c in found])
        channel_ids = [c["channel_id"] for c in found if c.get("channel_id")]
        missing_channels = [c for c in dict.fromkeys(channel_ids) if c not in caches["playlists"]]
        if missing_channels:
            try:
                caches["playlists"].update(channel_upload_playlists(missing_channels, key, counted))
            except FetchError as exc:
                record_error(errors, f"channels.list: {exc}", key)

        for candidate in found:
            video_id = candidate["video_id"]
            detail = details.get(video_id)
            if not detail:
                excluded["missing-video-details"] += 1
                continue
            snippet = detail.get("snippet") or {}
            statistics = detail.get("statistics") or {}
            views = as_int(statistics.get("viewCount"))
            subs = as_int(statistics.get("subscriberCount"))
            if views is None or views < min_views:
                excluded["below-min-views"] += 1
                continue
            if subs is None or subs > max_subs:
                excluded["above-max-subscribers-or-unknown"] += 1
                continue
            channel_id = snippet.get("channelId") or candidate.get("channel_id")
            playlist = caches["playlists"].get(channel_id)
            if not playlist:
                excluded["no-uploads-playlist"] += 1
                continue
            if playlist not in caches["uploads"]:
                try:
                    neighbour_ids = playlist_video_ids(playlist, key, counted)
                    neighbour_details = details_for(neighbour_ids)
                    caches["uploads"][playlist] = [{
                        "video_id": vid,
                        "published_at": (detail_of.get("snippet") or {}).get("publishedAt"),
                        "views": as_int(((detail_of.get("statistics") or {}).get("viewCount"))),
                    } for vid, detail_of in neighbour_details.items()]
                except FetchError as exc:
                    record_error(errors, f"playlistItems.list: {exc}", key)
                    caches["uploads"][playlist] = []
            median, sample = median_surrounding(
                video_id, snippet.get("publishedAt") or candidate.get("published_at"),
                caches["uploads"][playlist],
            )
            if median is None or median <= 0:
                excluded["insufficient-surrounding-sample"] += 1
                continue
            ratio = views / median
            if ratio < min_ratio:
                excluded["below-min-ratio"] += 1
                continue
            seconds = duration_seconds((detail.get("contentDetails") or {}).get("duration"))
            qualified.append({
                "video_id": video_id,
                "keyword": keyword,
                "title": snippet.get("title") or candidate.get("title"),
                "channel_id": channel_id,
                "channel_title": snippet.get("channelTitle") or candidate.get("channel_title"),
                "published_at": snippet.get("publishedAt") or candidate.get("published_at"),
                "duration_seconds": seconds,
                "format_hint": ("short" if seconds is not None and seconds <= 180 else "long"),
                "view_count": views,
                "subscriber_count": subs,
                "median_surrounding_views": round(median, 3),
                "surrounding_sample_size": sample,
                "outlier_multiple": round(ratio, 4),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                **thumbnail_urls(video_id, snippet),
            })

    qualified.sort(key=lambda row: (-row["outlier_multiple"], -row["view_count"], row["video_id"]))
    return {
        "tool": "youtube-outlier-scan",
        "schema_version": 1,
        "source": "YouTube Data API v3",
        "generated_at": (now or dt.datetime.now(dt.timezone.utc)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "parameters": {
            "keywords": keywords,
            "min_views": min_views,
            "max_subs": max_subs,
            "min_ratio": min_ratio,
            "format": fmt,
            "lookback_days": lookback_days,
            "surrounding_uploads": SURROUNDING_UPLOADS,
            "min_surrounding_uploads": MIN_SURROUNDING_UPLOADS,
            "results_per_keyword": MAX_RESULTS_PER_KEYWORD,
            "uploads_per_channel": MAX_UPLOADS_PER_CHANNEL,
        },
        "stats": {
            **stats,
            "candidates_seen": candidates_seen,
            "qualified": len(qualified),
            "excluded": dict(sorted(excluded.items())),
        },
        "errors": errors,
        "outliers": qualified[:limit],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keywords", default="", help="1-5 comma-separated niche keywords")
    parser.add_argument("--min-views", default="3000")
    parser.add_argument("--max-subs", default="100000")
    parser.add_argument("--min-ratio", default="2.0")
    parser.add_argument("--format", default="short", choices=("short", "long", "both"))
    parser.add_argument("--lookback-days", default="180")
    parser.add_argument("--out", default="/tmp/research_vision/outlier_scan.json")
    parser.add_argument("--fixture", default="", help="offline raw-response fixture (no API key used)")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        keywords = parse_keywords(args.keywords) if not args.fixture else ["fixture-keyword"]
        min_views = positive_int(args.min_views, "min_views", 10_000_000)
        max_subs = positive_int(args.max_subs, "max_subs", 100_000_000)
        min_ratio = positive_float(args.min_ratio, "min_ratio", 1000.0)
        lookback = positive_int(args.lookback_days, "lookback_days", 3650)
        fmt = parse_format(args.format)
    except ValueError as exc:
        raise SystemExit(f"Invalid input: {exc}") from None

    if args.fixture:
        try:
            fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SystemExit(f"Could not read fixture: {exc}") from None
        fetch = FixtureFetch(fixture)
        key = None
    else:
        key = resolve_key(os.environ)
        fetch = get_json

    report = scan(
        keywords=keywords, min_views=min_views, max_subs=max_subs, min_ratio=min_ratio,
        fmt=fmt, lookback_days=lookback, key=key, fetch=fetch,
    )
    if args.fixture:
        report["source"] = "offline fixture (synthetic; not YouTube data)"
        report["parameters"]["keywords"] = ["fixture-keyword"]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Scanned {report['stats']['candidates_seen']} candidates; "
          f"{report['stats']['qualified']} qualified; {len(report['errors'])} sanitized errors. "
          f"Wrote {out}")


if __name__ == "__main__":
    main()
