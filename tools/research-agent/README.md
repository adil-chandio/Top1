# Stage 1 — YouTube Outlier Scanner

`outlier_scan.py` is the missing Stage A primitive. It uses **only the official YouTube Data API v3** through GitHub Actions — no `yt-dlp`, no scraping, no retry loops against bot walls.

## Files

| File | Purpose |
|---|---|
| `outlier_scan.py` | Bounded scanner; writes `outlier_scan.json` sorted by `outlier_multiple` |
| `outlier_scan.schema.json` | Draft-07 schema for the produced artifact |
| `tests/test_outlier_scan.py` | Offline `unittest` suite (no key, no network) |
| `.github/workflows/youtube-outlier-scan.yml` | Manual-dispatch workflow with artifact upload |

## Definition of the outlier score

```
outlier_multiple = candidate views / median(views of the 10 nearest surrounding uploads)
```

* Surrounding uploads come from the **same channel's uploads playlist** (first 30 items, newest first), excluding the candidate itself.
* Fewer than 5 usable neighbours → candidate is dropped, never scored on thin evidence.
* Filters: `views >= min_views`, `subscriber_count <= max_subs` (unknown subscriber counts are retained with `subscriber_count_known: false` and must be verified by a human), `outlier_multiple >= min_ratio`.
* Results are sorted by `outlier_multiple` desc, then views desc; at most 25 are kept.

## Run it

```sh
gh workflow run youtube-outlier-scan.yml \
  -f keywords="everyday physics,hidden engineering" \
  -f min_views=3000 -f max_subs=100000 -f min_ratio=2.0 \
  -f format=short -f lookback_days=365

gh run list --workflow=youtube-outlier-scan.yml -L 1
gh run download <RUN_ID> -n youtube-outlier-scan -D /tmp/research_vision/
```

The workflow accepts `YOUTUBE_API_KEY` (or `YT_API_KEY`, `YT_KEY`, `YTAP1`, `YTAPI1`) from repository secrets. The key is sent as an `X-Goog-Api-Key` header, never in a URL, log line or artifact. HTTP redirects are blocked, response size is capped at 3 MB, and errors are reduced to `HTTP <code>` / `network or JSON error` with a final redaction pass.

**Quota:** one `search.list` (100 units) per keyword + 1-unit `videos`/`channels`/`playlistItems` calls. Five keywords stay far below the default 10,000-unit daily quota.

## Offline / test mode

```sh
python3 -m unittest discover -s tools/research-agent/tests -v
python3 tools/research-agent/outlier_scan.py \
  --fixture /path/to/raw-responses.json --out /tmp/outlier_scan.json
```

A fixture is `{"responses": [{"endpoint": "search|videos|channels|playlistItems", "params": {"id": "..."}, "body": {...}}]}`. Every `params` entry must exactly match the corresponding decoded query value; omit `params` to match any request to that endpoint, and the first matching entry wins. Fixture mode never reads an API key and labels the artifact as synthetic.

## What Stage 1 does next

1. **Claws Vision:** take `thumbnail_url` (API-provided, safe) and `thumbnail_maxres` (may 404) from the top 9–12 outliers, build a labelled contact sheet in `/tmp/research_vision/`, inspect it with `read_file`.
2. **Transcript/comment mining:** `web_search`/`fetch_page` on the surviving videos; no automated platform login.
3. **4 gates + scorecard:** `tools/extinct-studio/scorecard.js`, `state-machine.js`, V6 SDK feasibility, brand safety.
4. **Handoff:** `projects/<slug>/stage-1-research/{research.json,idea-scorecard.json,brief-for-script-agent.md}`, validated against `tools/extinct-studio/schemas/research.json.schema.json` and `idea-scorecard.json.schema.json`.

If the workflow is unavailable in a target checkout, use bounded `web_search`/`fetch_page` research and mark the source honestly — never loop on blocked video downloaders.
