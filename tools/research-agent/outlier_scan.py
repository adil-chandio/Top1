#!/usr/bin/env python3
"""Zero-dependency YouTube Data API v3 outlier scanner with neighbour-median scoring."""

import argparse
import csv
import datetime as dt
import json
import os
import statistics
import sys
import urllib.parse
import urllib.request


API_BASE = "https://www.googleapis.com/youtube/v3"


def api_get(endpoint: str, params: dict, api_key: str) -> dict:
    query = dict(params)
    query["key"] = api_key
    url = f"{API_BASE}/{endpoint}?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_iso_duration_seconds(iso: str) -> int:
    # Minimal ISO-8601 duration parser (e.g., PT1M30S, PT45S)
    if not iso or not iso.startswith("PT"):
        return 0
    s = iso[2:]
    total = 0
    num = ""
    for ch in s:
        if ch.isdigit():
            num += ch
        else:
            val = int(num or 0)
            num = ""
            if ch == "H":
                total += val * 3600
            elif ch == "M":
                total += val * 60
            elif ch == "S":
                total += val
    return total


def get_channel_median_views(channel_id: str, api_key: str) -> float | None:
    ch = api_get("channels", {"part": "contentDetails", "id": channel_id}, api_key)
    items = ch.get("items", [])
    if not items:
        return None
    uploads_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    pl = api_get(
        "playlistItems",
        {"part": "contentDetails", "playlistId": uploads_id, "maxResults": 15},
        api_key,
    )
    vid_ids = [it["contentDetails"]["videoId"] for it in pl.get("items", [])]
    if not vid_ids:
        return None
    vids = api_get(
        "videos",
        {"part": "statistics", "id": ",".join(vid_ids)},
        api_key,
    )
    views = [int(v["statistics"].get("viewCount", 0)) for v in vids.get("items", [])]
    return float(statistics.median(views)) if views else None


def scan_keyword(
    keyword: str,
    api_key: str,
    min_views: int,
    max_subs: int,
    min_ratio: float,
    months: int,
    with_median: bool,
) -> list[dict]:
    published_after = (
        dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30 * months)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    search_res = api_get(
        "search",
        {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "order": "viewCount",
            "maxResults": 25,
            "publishedAfter": published_after,
        },
        api_key,
    )
    video_ids = [
        it["id"]["videoId"]
        for it in search_res.get("items", [])
        if it.get("id", {}).get("videoId")
    ]
    if not video_ids:
        return []

    vids_res = api_get(
        "videos",
        {"part": "snippet,statistics,contentDetails", "id": ",".join(video_ids)},
        api_key,
    )
    videos = vids_res.get("items", [])
    channel_ids = list({v["snippet"]["channelId"] for v in videos})

    ch_res = api_get(
        "channels",
        {"part": "snippet,statistics", "id": ",".join(channel_ids)},
        api_key,
    )
    channels = {c["id"]: c for c in ch_res.get("items", [])}

    results = []
    median_cache: dict[str, float | None] = {}

    for v in videos:
        vid = v["id"]
        snippet = v["snippet"]
        stats = v.get("statistics", {})
        views = int(stats.get("viewCount", 0))
        if views < min_views:
            continue

        cid = snippet["channelId"]
        ch = channels.get(cid, {})
        ch_stats = ch.get("statistics", {})
        if ch_stats.get("hiddenSubscriberCount"):
            continue
        subs = int(ch_stats.get("subscriberCount", 0))
        if subs <= 0 or subs > max_subs:
            continue

        ratio = round(views / subs, 2)
        if ratio < min_ratio:
            continue

        outlier_multiple = None
        if with_median:
            if cid not in median_cache:
                median_cache[cid] = get_channel_median_views(cid, api_key)
            med = median_cache[cid]
            if med and med >= 500:
                outlier_multiple = round(views / med, 2)

        results.append(
            {
                "keyword": keyword,
                "video_id": vid,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "thumbnail_url": f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg",
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "channel_id": cid,
                "published_at": snippet.get("publishedAt", ""),
                "duration_sec": parse_iso_duration_seconds(
                    v.get("contentDetails", {}).get("duration", "")
                ),
                "views": views,
                "subs": subs,
                "views_to_subs_ratio": ratio,
                "outlier_multiple": outlier_multiple,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="YouTube Outlier Scanner")
    parser.add_argument("keywords", nargs="+", help="Search keywords")
    parser.add_argument("--min-views", type=int, default=3000)
    parser.add_argument("--max-subs", type=int, default=100000)
    parser.add_argument("--min-ratio", type=float, default=2.0)
    parser.add_argument("--months", type=int, default=18)
    parser.add_argument("--no-median", action="store_true")
    parser.add_argument("--out-dir", default=".")
    args = parser.parse_args()

    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        print("ERROR: YOUTUBE_API_KEY environment variable is not set.", file=sys.stderr)
        return 1

    all_rows = []
    seen = set()
    for kw in args.keywords:
        rows = scan_keyword(
            kw,
            api_key,
            args.min_views,
            args.max_subs,
            args.min_ratio,
            args.months,
            with_median=not args.no_median,
        )
        for r in rows:
            if r["video_id"] not in seen:
                seen.add(r["video_id"])
                all_rows.append(r)

    all_rows.sort(
        key=lambda x: (x["outlier_multiple"] or 0, x["views_to_subs_ratio"]),
        reverse=True,
    )

    os.makedirs(args.out_dir, exist_ok=True)
    json_path = os.path.join(args.out_dir, "outlier_scan.json")
    csv_path = os.path.join(args.out_dir, "outlier_scan.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, indent=2, ensure_ascii=False)

    fieldnames = [
        "keyword",
        "video_id",
        "url",
        "thumbnail_url",
        "title",
        "channel",
        "views",
        "subs",
        "views_to_subs_ratio",
        "outlier_multiple",
        "duration_sec",
        "published_at",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Scanned {len(args.keywords)} keywords -> {len(all_rows)} outliers saved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
