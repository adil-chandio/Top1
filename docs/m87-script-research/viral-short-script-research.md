# M87* Short — GitHub research and script-forensics memo

**Research date:** 2026-11-22
**Scope:** Public GitHub repositories and source files; the existing M87* script and project rules.
**Not a promise:** No repository or API provides a reliable “viral formula.” A script score or a video's public view count is not evidence that a writing pattern caused distribution.

## Executive findings

1. The useful distinction is **discovery → evidence → script → measurement**, not “copy the viral hook.” Repositories offer APIs, transcript tools, workflow checklists, and generated-script rubrics; none of the inspected code demonstrates that its rubric predicts actual viral reach.
2. Public YouTube-facing metadata can help find candidate videos and compare visible counts. It cannot reveal another creator's private audience-retention graph. The inspected Analytics implementation uses `ids=channel==MINE`; its retention query requests `audienceWatchRatio` and `relativeRetentionPerformance` by `elapsedVideoTimeRatio`, which is creator-account analytics—not a public competitor endpoint.
3. The current M87* script is compact and evidence-bounded: **63 words across six clauses**, averaging **10.5 words/clause**. It already moves through identification → observing wavelength → shadow/emission distinction → lensing → flat-disk explanation → CGI limitation. Its opening is accurate but begins with exposition rather than a viewer question or a misconception correction; that is the clearest *future* test, not a reason to claim the current script will fail.
4. The M87* narration and audio remain locked. This memo does not alter or re-record them. If a new voice pass is later authorized, test one opening variable at a time and preserve the existing claim ledger.

## GitHub repository review

### 1) Official Google API client sample

[googleapis/google-api-nodejs-client — YouTube search sample](https://github.com/googleapis/google-api-nodejs-client/blob/main/samples/youtube/search.js) is Google's supported Node client example. It demonstrates `youtube.search.list` and Google auth. The sample requests the broad `youtube` OAuth scope; a research-only implementation should use the narrowest read-only authorization it can, never copy a write-capable scope by default. The repository is a client library/sample, not a “viral-video predictor.”

**Use:** a supported client surface for a future, least-privilege metadata research tool.
**Limit:** public search/statistics are descriptive; this sample does not provide retention for other creators.

### 2) YouTube analytics MCP server

[pauling-ai/youtube-mcp-server](https://github.com/pauling-ai/youtube-mcp-server) is MIT-licensed. Its README describes Data API, Analytics API, Reporting API and a broad MCP toolset. I inspected the actual `analytics.py` and `quota.py`, not just its README:

- `analytics.py` sets `ids="channel==MINE"` and requests analytics for the authenticated owner's channel.
- `youtube_analytics_retention()` asks for `audienceWatchRatio,relativeRetentionPerformance` with `elapsedVideoTimeRatio`, filtered to a video ID. This is the relevant way to study *your own* retention curve when that owner account is authorized.
- The same server includes upload, playlist, comments and publishing surfaces. Do **not** install/authorize its full toolset just to research scripts; isolate read-only analytics and review OAuth scopes first.
- `quota.py` is a local in-memory counter keyed to `date.today()` with a hard-coded cost table. It is a useful guardrail pattern, not authoritative server quota or a shared multi-process ledger; do not rely on it alone to prevent quota exhaustion.

**Use:** learn the metric/query shape for owner-authorized analytics, then apply least privilege.
**Limit:** it does not unlock competitors' private retention; README feature claims should be checked against implementation and current API access.

### 3) YouTube transcripts

[jdepoix/youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) is MIT-licensed and returns timestamped transcript snippets, including generated captions when available. Its README explicitly warns that YouTube blocks many cloud-provider IPs and that proxies do not guarantee availability.

**Use:** a convenient research prototype for captions that are publicly available and where use is permitted. Keep timestamps and language/generated status with the text.
**Limit:** it is not the official YouTube Data API; it can fail or be blocked, captions can be absent or inaccurate, and transcript text alone misses visuals, edits, delivery, and audience response. Do not treat scraper access or proxy rotation as a dependable or automatically permitted data source.

### 4) Video/script automation repo

[Chamanrajragu/purffle-shorts — script module](https://github.com/Chamanrajragu/purffle-shorts/blob/main/purffle_shorts/script.py) is MIT-licensed. Its code has useful production mechanics: a JSON schema for scenes, hook/title/scene outputs, word-budget planning, and a second “Script Doctor” review with separate hook, curiosity, pacing, specificity, payoff and accuracy fields. It uses a nominal `WORDS_PER_SECOND = 2.6` and a weighted 0–100 score.

**Useful as:** a checklist and structured-output pattern.
**Do not mistake for evidence:** the weighted score is self/LLM assessment; I found no demonstrated calibration against creator analytics in the inspected module. A universal 2.6 words/second target can make a science explainer too rushed, especially across languages and names. The “viral” style templates are creative heuristics, not measured causal laws. Keep fact checking outside the model score.

### 5) Workflow and analytics practice

[yanhua1010/self-media-content-workflow](https://github.com/yanhua1010/self-media-content-workflow) is MIT-licensed. Its `self-media-short-video/SKILL.md` recommends one central judgment, an early conflict/result/benefit or concrete situation, spoken-natural copy, and visuals that prove/demonstrate rather than repeat narration. Its analytics skill calls for same-platform, same-format, similar-age comparisons; medians/P75 instead of a viral-skewed mean; one primary experimental variable; and explicit “correlation is not causation” limits. The explainer reference proposes a hook/question/proof/payoff structure but is a craft guide, not a published causal study.

These process choices align with this repository's own claim ledger, `views_descriptive_only = 1` research warehouse and approval gates. They are stronger safeguards than copying a generic “viral formula.”

### 6) Downloaders

[yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) describes itself as an audio/video downloader. I did not use it to fetch or copy other creators' videos. For script research, prefer authorized public metadata, user-provided links, and permitted captions; don't rehost clips or bypass platform controls.

## Safe research/API plan

If a YouTube research connection is later authorized:

1. **Discover candidates with public metadata.** Query narrowly by topic/language/time window; record video ID, channel, title, publish time, duration, visible views/likes/comments if exposed, and observation timestamp. Keep API quota logging. Avoid storing credentials in Git or transcripts in public logs.
2. **Normalize before ranking.** A raw view count confounds age, channel size, topic, paid promotion, and platform distribution. Compare same-platform, same-format, similar publication age; use a creator's own median/P75 as the baseline. View velocity is only a candidate signal, not proof of quality or causality.
3. **Code the creative structure.** For each candidate, mark: opening premise; time to the central question; first visible proof; claim/evidence pairing; scene/shot changes; sentence/word density; payoff; CTA; and whether the title/thumbnail promise is fulfilled. Keep exact timestamps and separate spoken words from on-screen text.
4. **Use retention only where authorized.** Public competitor statistics do not contain their private retention graphs. Use YouTube Analytics/Reporting for the authenticated channel owner (or a permitted connector), then compare first-seconds loss, audienceWatchRatio curve, average view duration/percentage and traffic source against that channel's baseline. Do not infer retention from views or likes.
5. **Run a small controlled test.** Change one thing—e.g. the first spoken line *or* first-frame visual—while keeping topic, body, length, title/thumbnail, audience and distribution as comparable as possible. Define the metric and observation window first. Report uncertainty; don't promise “viral.”
6. **Human science/legal review.** Verify every numeric or causal claim against the cited primary source. Captions and LLM summaries are navigation aids, never source-of-truth evidence.

## Forensic read of the current M87* narration

The six locked clauses contain 63 whitespace-delimited words (9, 12, 8, 12, 12, 10). The project schedules them from 0.18–31.50 s and leaves a 3.5 s clean image hold. That is concise enough for the existing selected voice and preserves a useful sequence of concepts.

**What works**

- One understandable subject: what the M87* image shows.
- A precise observation detail (1.3 mm) appears early.
- The key distinction is explicitly spoken: the dark region is the shadow, not a photographed horizon surface.
- The physical disk stays flat; lensed appearance is described as an image effect.
- The final sentence bounds the procedural CGI as explanatory rather than numerical simulation.
- The final clean visual hold avoids stuffing a final CTA or extra fact into the caveat beat.

**What is testable, not a proven defect**

- Clause 1 identifies the object but does not itself pose a question or reverse a common misconception. A future version could test a truthful shadow-versus-horizon opening, with the CGI visibly labelled and the answer proved promptly. Do not make the viewer believe the EHT photographed a horizon surface.
- The central mystery becomes explicit at the shadow clause. An unlocked future draft could surface that promise in the first breath, then use 1.3 mm as evidence rather than introductory context.
- The close correctly states the model limitation, but the final *voice* line is not an open-ended engagement CTA. That is a deliberate fit for this scientific cut; do not add a “comment/follow” line unless the owner wants that goal and the evidence/caveat timing still works.
- `packaging.json` has title/thumbnail concepts but records `promise_match_verified: false` and no completed experiment. The 86/100 score is a pre-production gate, **not** a viral prediction or post-publication result.

## Recommended 35-second architecture for a future, newly approved script

This is a planning template, **not replacement narration**:

| Time | Script job | Visual proof job |
|---|---|---|
| 0–2 s | One honest contrast/misconception, immediately understandable | Open on the ring/shadow image; no logo preamble |
| 2–6 s | Name M87* and the exact question | Keep the original-CGI label; establish the EHT context |
| 6–12 s | Give the 1.3 mm observation as evidence | Show the illustrative monitor and readable wavelength cue |
| 12–18 s | Distinguish shadow from horizon and surrounding emission | Separate dark silhouette from warm emission ring |
| 18–26 s | Explain one mechanism: bending light makes a flat disk look wrapped | Trace only schematic paths; show physical plane and separate apparent arcs |
| 26–31.5 s | State what this CGI does *not* claim | Keep caveat legible and source attribution accurate |
| 31.5–35 s | Let the image resolve; no new spoken claim | Preserve the clean, loop-friendly visual hold |

Keep natural delivery pace; a rough word count is only a timing check. The current six clauses already average 10.5 words each. A second read should be reviewed for pronunciation, breath points, caption fit and scientific ambiguity—not merely optimized to a target words/second number.

## Bounded public YouTube metadata run — follow-up

The repository Actions secret-list endpoint returned HTTP 403 (`Resource not accessible by integration`), which blocked **listing** secret names; it did not mean the `YOUTUBE_API_KEY` secret was absent or invalid. A user-provided screenshot confirmed the secret exists. I did not read, print, copy, or expose its value.

A metadata-only workflow then completed successfully, including the YouTube request step:

- Initial run: [45588983415](https://github.com/adil-chandio/Top1/actions/runs/45588983415), commit `bdac1bb`.
- Persisted-report run: [45589162101](https://github.com/adil-chandio/Top1/actions/runs/45589162101), commit `c71462a`.
- Fixed-JSON rerun: [45589494357](https://github.com/adil-chandio/Top1/actions/runs/45589494357), commit `0c9eb5d`.
- The final JSON report is stored at [`recent-public-video-candidates.json`](recent-public-video-candidates.json). The workflow makes six `search.list` queries, then batches public video/channel metadata; the latest report records six searches, three video lookups, and two channel lookups. No playback, transcripts, thumbnails, or private analytics are collected.

**Important date-integrity warning:** the latest Actions API run and report say `2026-11-25`, while the trusted session date is `2026-11-22`. The report's search window therefore starts on a future date relative to this session. Treat the report as a successful API/pipeline test, **not a valid current-date sample**, until the clock/date discrepancy is resolved and a correctly dated run is made.

**Sample-quality warning:** a title-only spot check shows obvious relevance contamination in both cohorts (for example, a Chihuahua comedy video mentioning a black hole, “What if You Fart in Space,” a moon-emblem story, and a space-jump story). Search relevance and `order=viewCount` do not produce a scientific-video cohort. The displayed `views_per_day_since_publish` is lifetime views divided by age—not current velocity. These are discovery leads only, not evidence of viral causes or guaranteed performance. Any serious content analysis still needs human viewing/source checks and same-format/channel baselines; competitor retention remains private.

The report is public metadata only and contains no credential. Its first saved version had a literal `\\n` suffix that made the JSON invalid; the workflow was corrected in commit `0c9eb5d`, and the rerun report parses as valid JSON. No script, locked narration, audio, or M87* scientific claim was changed.
