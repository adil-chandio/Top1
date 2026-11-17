# Platform tooling: actual access evidence

## Implemented, not merely proposed

`platform_research.py`: bounded YouTube discovery, separate channel videos/shorts listing, public metadata, public permitted bounded acquisition, actual local frame/clip/WAV extraction, actual duration probe, public comparable-cohort baseline, evidence capture, timestamped AV observations, strict verified AV bundles. Pipeline attaches tools to new requests. New Monarch briefs require AV evidence at feasibility/production/QC. Old pending requests/brief snapshots are not silently rewritten.

Optional tools installed locally: yt-dlp 2026.10.26 and official yt-dlp-ejs 0.8.0. Node runtime explicitly declared; remote JS component fetching not enabled. Dependency pinning is not a claim of exhaustive source-code security audit. No cookies/passwords collected, no paid service, no bot/DRM bypass.

## Live public-page research

Actual `web_search` query: site:youtube.com/watch humpback whales orcas interfere hunt.

Actual `fetch_page`, chunk 0:
- https://www.youtube.com/watch?v=W9KfHky9sMo — primary page text with title, channel, public metrics, description and comments surfaced. Same response also contained Error 401 and bot confirmation/player failure. Label: page_text only.
- https://www.youtube.com/watch?v=3DkEePjRP04 — primary page text with title, channel, public metrics and description surfaced. Same access warnings. Label: page_text only.

Selected-field excerpts and hashed captures are in ignored `studio/runtime/platform-live/`. These are explicitly selected excerpts, not alleged complete raw tool responses. They are not audiovisual breakdowns, verified thumbnails, or private analytics. No comments treated as scientific evidence.

## Direct local extractor test

Metadata-only request for W9KfHky9sMo actually executed, timeout/retries bounded. TLS EOF. No video bytes acquired; no listening/viewing claimed.

## Separate public runner test

Public repo confirmed. Standard public GitHub runner; no paid API or credentials requested.

1. Run https://github.com/adil-chandio/Top1/actions/runs/43859084580 installed tools, then public request failed. Report recovered without repeating request by run https://github.com/adil-chandio/Top1/actions/runs/43859356586 . Recovery succeeded, but that does not mean YouTube access succeeded.
2. Actual report exposed missing declared JS runtime AND YouTube bot confirmation. Fixed tool setup to explicitly use Node and pinned official EJS package.
3. One corrected probe: https://github.com/adil-chandio/Top1/actions/runs/43859512813 . Runtime warning gone; actual result still `public_access_failed`: YouTube requires sign-in to confirm not a bot. Access attempt failed; reporting/evidence check succeeded. No further automatic retry loop launched.

Actual result readable through GitHub check `platform-access-evidence` on commit 84781295b7e2a9e5155d1a9b2f3689902109d28e. Raw recovered check output saved in ignored runtime. GitHub Actions result timestamps are recorded by the runner; not presented as the user's local date.

## Real media-processing smoke test

Generated owned synthetic moving test pattern + sine audio locally with FFmpeg. Toolkit actually extracted a 2.0-second playable MP4, two JPEG frames, and PCM WAV and wrote SHA256 evidence manifest. Files in ignored `studio/runtime/platform-smoke/`. This is an actual decoder/extractor execution test, NOT actual competitor video analysis. No synthetic content was passed off as the linked source.

## Automated checks

96 tests pass, including URL restrictions, bounded search, public metric cohort separation/deduplication, access labelling, no text-to-AV upgrade, timestamp bounds, changed media, path traversal, required AV evidence, and actual coordinator request propagation. Other existing studio tests remain passing.

## Exact present boundary

Agents have executable research/media-processing hands and an active-session web-search/page-text route. Selected YouTube public page text was actually obtained. Direct competitor moving-picture/audio acquisition/playback has NOT been established in these two tested network environments. Tools/runner are not equivalent to a verified AV-capable agent. Instagram/TikTok downloader/browser adapters are not implemented; they remain secondary discovery/manual research lanes. No authentication/bot-control bypass or invented watching/listening substituted for missing access.
