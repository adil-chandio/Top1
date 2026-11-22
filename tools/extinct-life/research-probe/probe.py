#!/usr/bin/env python3
"""One-shot, public-data-only research route probe for GitHub Actions.

The runner logs are public. Never print secrets, request URLs containing secrets,
raw remote responses, or exception messages that could contain credentials.
This is an access test, not a scraper, trend model, or production collector.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT_SECONDS = 18
HEADERS = {"User-Agent": "ExtinctLifeResearchProbe/1.0", "Accept": "application/json"}


def request_json(url, headers=None):
    request = urllib.request.Request(url, headers={**HEADERS, **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        # Error bodies and request URLs can contain sensitive data: do not log them.
        return exc.code, None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None, None


def youtube():
    # Try one pre-existing key if available. Do not display even its name or value.
    candidates = ("YOUTUBE_API_KEY", "YTAP1", "YTAPI1", "YT_KEY", "YT_API_KEY")
    key = next((os.environ.get(name) for name in candidates if os.environ.get(name)), None)
    if not key:
        status, _ = request_json(
            "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=Ya99xCWXQdc"
        )
        print(f"YouTube Data API: SKIPPED — no configured key; unauthenticated endpoint HTTP {status or 'network error'}")
        return
    query = urllib.parse.urlencode({
        "part": "snippet,statistics,contentDetails",
        "id": "Ya99xCWXQdc,yN4Ck8CSdWU,i2OYcptFl9c",
    })
    status, result = request_json(
        "https://www.googleapis.com/youtube/v3/videos?" + query,
        {"X-Goog-Api-Key": key},
    )
    if status != 200 or not isinstance(result, dict):
        print(f"YouTube Data API: FAILED — HTTP {status or 'network error'}; reason not logged")
        return
    items = result.get("items", [])
    print(f"YouTube Data API: OK — {len(items)} public video records returned")
    for item in items:
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        print(json.dumps({
            "id": item.get("id"), "channel": snippet.get("channelTitle"),
            "title": snippet.get("title"), "published": snippet.get("publishedAt"),
            "views": stats.get("viewCount"), "duration": item.get("contentDetails", {}).get("duration"),
        }, ensure_ascii=True))


def huggingface():
    status, result = request_json(
        "https://huggingface.co/api/models/sentence-transformers/all-MiniLM-L6-v2"
    )
    if status != 200 or not isinstance(result, dict):
        print(f"Hugging Face model registry: FAILED — HTTP {status or 'network error'}")
        return
    print(json.dumps({"source": "Hugging Face model registry", "status": "OK",
                      "model": result.get("id"), "pipeline_tag": result.get("pipeline_tag"),
                      "model_sha": result.get("sha")}))
    print("Registry connectivity alone does not establish model inference; see the separate model test.")


def crossref():
    doi = "10.1126/science.adw3536"
    status, result = request_json("https://api.crossref.org/works/" + doi)
    if status != 200 or not isinstance(result, dict):
        print(f"Crossref: FAILED — HTTP {status or 'network error'}")
        return
    work = result.get("message", {})
    title = (work.get("title") or [None])[0]
    print(json.dumps({"source": "Crossref", "status": "OK", "doi": work.get("DOI"), "title": title}))


def europe_pmc():
    query = urllib.parse.urlencode({"query": "DOI:10.1126/sciadv.adi0505", "format": "json", "pageSize": 1})
    status, result = request_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + query)
    if status != 200 or not isinstance(result, dict):
        print(f"Europe PMC: FAILED — HTTP {status or 'network error'}")
        return
    print(json.dumps({"source": "Europe PMC", "status": "OK", "hits": result.get("hitCount")}))
    terms = 'TITLE_ABS:dinosaur AND TITLE_ABS:fossil AND FIRST_PDATE:[2025-01-01 TO 2026-11-22] sort_date:y'
    query = urllib.parse.urlencode({"query": terms, "format": "json", "pageSize": 3})
    status, result = request_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + query)
    if status != 200 or not isinstance(result, dict):
        print(f"Europe PMC discovery search: FAILED — HTTP {status or 'network error'}")
        return
    matches = result.get("resultList", {}).get("result", [])
    print(json.dumps({"source": "Europe PMC discovery search", "status": "OK",
                      "hits": result.get("hitCount"),
                      "results": [{"title": item.get("title"), "doi": item.get("doi"),
                                   "date": item.get("firstPublicationDate"), "source": item.get("source")}
                                  for item in matches]}))
    print("Discovery results are unreviewed leads, not verified science or viral ideas.")


if __name__ == "__main__":
    print("Research route probe: public metadata only; one bounded run")
    youtube()
    huggingface()
    crossref()
    europe_pmc()
