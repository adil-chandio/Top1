# YouTube-first agents: actual tools aur operating process

## Agent ke haath mein kya diya gaya

`studio/platform_research.py` CLI + importable API, pinned optional `yt-dlp` dependency, existing real FFmpeg integration, stage-specific worker task packets, strict AV-reference bundles for new Monarch briefs, aur public GitHub runner workflow. Koi platform API password, paid service, cookie extraction, proxy rotation ya access-control bypass nahi.

### Tools

- `discover QUERY --limit 10 --out FILE`: bounded public YouTube search, discovery labels only.
- `channel CHANNEL_URL --tab videos|shorts --limit 12 --out FILE`: separate long/Shorts listings.
- `inspect VIDEO_URL --out FILE`: public metadata; signed media URLs/private extractor payload save nahi hota.
- `acquire VIDEO_URL --start 0 --duration 15 --rights-basis ACTUAL_BASIS --out NEW_FOLDER`: public permitted short segment; max requested 60 sec, low-resolution, size/rate/time limits. Acquisition permission must be real; reference rights are not production reuse rights. Segment cutting accuracy must be checked, not assumed.
- `capture VIDEO_URL --content ACTUAL_CAPTURE --kind page_text --method fetch_page --lane topic_winner --out NEW_FOLDER`: actual web tool capture when direct extractor unavailable. Text never becomes watching/listening evidence.
- `sample LOCAL_PERMITTED_MEDIA --url VIDEO_URL --start 0 --duration 15 --rights-basis ACTUAL_BASIS --out NEW_FOLDER`: frames, actual playable segment, optional extracted WAV, actual duration probe and SHA256 manifest.
- `observe SEGMENT_FOLDER --record ACTUAL_OBSERVATION.json`: actual executor's timestamped picture/audio/combined findings, tied to unchanged media.
- `packet STAGE --out FILE`: stage question, lanes, tool commands, fallback and stopping rule.

Commands ka prefix `python -m studio.platform_research` hai. Install: `python -m pip install -r studio/requirements-platforms.txt`. Existing local installation `.local-motion` se extractor adapter automatically use kar sakta hai.

## Research lead ka runbook

1. Binding brief padho. Subject, intended viewer, format aur current unresolved question identify karo.
2. Four lanes: direct competitor, topic winner, adjacent craft, packaging.
3. YouTube long-form first; Shorts ko separate comparison lane mein rakho. Instagram/TikTok secondary discovery/manual inspection lanes hain; unke executable downloader adapters is pass mein implemented nahi.
4. Bounded initial search. Relevant candidates shortlist, irrelevant examples reject with reason. Har video ko full download nahi karna.
5. Same channel ke comparable format/age-band uploads ke public views compare karo. `baseline()` at least five distinct comparables maangta hai. Public ratio causal virality/CTR/retention nahi.
6. Selected public watch pages, title, thumbnail and relevant comments actually inspect karo. Comments are audience clues, not representative survey or scientific facts.
7. Actual video/audio access ho to carefully selected relevant segments inspect karo. Long-form opening, explanatory middle, payoff; Shorts ko unke separate format context mein dekho. Arbitrary fixed-duration snapshots cannot prove complete-video review.
8. Timestamped observation → interpretation → application → what not to copy. Har choice original implementation mein translate karo.
9. Question resolve ho to stop browsing, small test execute karo. Defect aaye to targeted new research, not endless inspiration collection.

## Stage handoffs

- intelligence: source/format/access-labelled shortlist, public metric context, limits.
- idea: audience question, angle comparison, originality decision.
- story: actual inspected information sequence and original beat map.
- script: narration/reveal relationship, edit/sound blueprint, no transcript-only visual claims.
- feasibility: reference staging/motion/sonic principles plus actual integrated proof.
- production: specific animation/edit/compositing/sound problem and applied reference decision.
- qc: exact output versus inspected references; picture, audio, combined defects.
- packaging: actual title-thumbnail promise and delivery match.
- delivery: provenance, permissions and exact final identity; no reference ripping.

Every newly emitted coordinator request contains `platform_research` instructions and real tool commands. Already pending requests remain frozen; do not rewrite their hashes to pretend new instructions were always present. Existing brief snapshots also remain immutable; new jobs get the updated platform policy. If an older job must adopt it, record an explicit rebrief/restart rather than silently editing the snapshot.

## AV bundle schema (new strict Monarch jobs)

Feasibility, production and QC results must include `platform_references`:

```json
[{
  "lane": "adjacent_craft",
  "format": "youtube_long",
  "selection_reason": "Actual relevance and performance context",
  "applied_decision": "Specific original execution decision",
  "media_manifest": "references/segment/media_evidence.json",
  "observations": "references/segment/observations.json"
}]
```

Manifest, observations AND every linked media evidence file must be ordinary job artifacts with correct hashes. At least one YouTube reference required. Combined inspection, or both picture and audio observations, required. Metadata/transcripts/waveforms cannot satisfy AV inspection. Code checks missing/changed evidence, timestamp bounds and declarations; it cannot independently prove an executor's subjective perceptual honesty or artistic taste.

Observation record fields: executor, mode (picture/audio/combined), start/end (segment-relative), observation, interpretation, application, do_not_copy, method, actually_inspected true. Source timestamps also recorded. Extracted media starts uninspected; generating frames/WAV never auto-marks it watched/heard.

## Actual perception handoff

Equipped agent opens extracted frames through image tools for composition, opens moving segment with actual video-capable inspection for motion, and actually listens with audio-capable inspection for sound. A still-image tool cannot certify movement; a player file sitting on disk cannot certify listening. This toolkit prepares the media and binds reports; it does not silently add a vision/audio model to a text-only executor.

## Network routing

Local public extractor is one route. Available Arena web_search/fetch_page are discovery/text fallback routes. `Public YouTube research tools` GitHub workflow is a separate public-network runner with bounded metadata/segment actions. Free standard runner in this public repo; no paid API. It publishes actual access result, including failures, into a small readable GitHub check and short-retention artifact. Neither another machine nor another command name guarantees platform playback access.

Do not retry a bot challenge endlessly, import account cookies, solicit passwords or bypass sign-in/DRM. Preserve successful discovery/text evidence, keep audiovisual work explicitly unresolved and route to an authorized AV-capable execution environment. Never convert a network failure into a fake reference review.

## Verified in this implementation pass

- Actual YouTube discovery via web_search and actual public watch-page text via fetch_page.
- Two primary watch-page text captures include real page content but also bot/player errors: access labelled page text, not playback.
- Local direct yt-dlp probe actually attempted: TLS EOF failure; no video/audio claimed.
- Real local synthetic test: FFmpeg generated moving/audio fixture, then toolkit extracted actual playable segment, two frames, WAV and measured 2.0 sec duration. Synthetic technical test, not competitor-film inspection.
- Public runner probe executed; exact access outcome recorded separately in `PLATFORM_ACCESS_EVIDENCE_ROMAN_URDU.md`.
- Automated tests distinguish URL safety, bounds, cohorts, metadata access, media integrity, timestamping and mandatory AV bundles.
