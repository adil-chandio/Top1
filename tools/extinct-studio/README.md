# Extinct Studio OS — production foundation

**Status: build source — not a published pipeline.** This foundation is the
shared substrate the owner asked for (schemas, state machine, idea scorecard,
claims/rights manifest, automated QA skeleton). It is **not** a finished
production tool: no publish, upload, or "published" state is possible from
any of this code. Every verification is reported honestly — a check that
cannot run is `unavailable`, never a fake `pass`.

## What this is

The architecture the 2026-11-21 strategic review (Extinct Studio OS) asks for;
see section V (version and status), W (workflow DAG), X–Z in the chat record.

```
tools/extinct-studio/
  schemas/          — 14 draft-07 JSON schemas for the project records
  validate.js       — zero-dependency JSON Schema validator (subset, explicit)
  state-machine.js  — formal state machine (15 states) + dependency DAG
  scorecard.js      — 100-point idea scorecard + production-candidate gates
  claims-rights.js  — claims classification (8 categories) + rights manifest rules
  qa-skeleton.js    — automated QA skeleton (honest status reporting)
  README.md         — this file
```

## The state machine

```
idea → researched → shortlisted → owner-selected → claim-checked → scripted
  → proof-pending → proof-passed → voice-locked → picture-locked → mix-locked
  → qa-passed → owner-accepted → private-uploaded → published
```

- Forward-only — skipping a state is rejected; going backwards is rejected.
- Each gated target requires its receipt/flag (see `GATES` in
  `state-machine.js`); receipts are real artifacts, not booleans.
- `published` cannot be set by any tool — publication is an owner act.
- A change re-runs its affected scope via the DAG (claim → script review;
  mix → audio QA; thumbnail → packaging; …), never the full film.

## The idea scorecard

100 points, eight dimensions:

| Dimension | Weight |
| --- | --- |
| Viewer promise clarity | 20 |
| Visible proof potential | 20 |
| Novelty | 15 |
| Evidence strength | 15 |
| Emotional/stakes value | 10 |
| Short/long format fit | 10 |
| Rights certainty | 5 |
| Production feasibility | 5 |

An idea reaches `production-candidate` only when the score is **strong**
(default threshold 75, documented heuristic — the owner may tighten it) **and**
every gate is green: claim ledger complete, title/thumbnail promise clear, an
8–12 s proof possible, owner selection. An idea that is only an interesting
fact (zero visual proof potential) is **rejected**.

## Claims + rights manifest

Every narration line must be classified:
`directly-observed`, `measured`, `published-finding`, `derived-calculation`, `modelled-reconstruction`, `illustrative-animation`, `hypothesis`, `unknown-limitation`.
Direct/measured/published-finding categories **require evidence references**.
Illustrative or modelled content is refused when presented as a direct observation.

Every third-party source is checked separately — `paper`, `data`, `font`,
`sound`, `texture`, `model`, `code`, `reference-image`, `voice`. Unknown or
unclear license is **not safe to use**, and "free download" alone is not a
license. Commercial use must be consistent with the license — the manifest
refuses a `commercialAllowed: true` with an all-rights-reserved license.

## Automated QA skeleton

`runSkeleton()` builds the honest report. In this environment every check
returns `unavailable` with a reason; real probe results are injected by the
caller via `probeOverrides`. The skeleton never marks a check `ok` on its own.

Video checks: frame count, FPS, black frames, duplicate frames, freeze frames,
dropped frames, color range, audio/video duration, clipping, caption overflow,
safe area, OCR readability, scene-change continuity, visual diff, phone-size
playback.

Audio checks: LUFS, true peak, AAC re-encode, mono compatibility, phone
speaker review.

## What is deliberately NOT here

- No publish, upload, or silent publication. The state machine will not move
  a project to `published` from tool code.
- No chrome/ffmpeg/media probe — none runs in this environment.
- No old video, public archive, or storefront untouched by this foundation.
- No new topic's production candidate until the foundation is in place.

## Test

```sh
npm test   # includes the Extinct Studio suite (state machine, scorecard,
           # claims/rights, schemas, QA skeleton)
```

The 14 fixture artifacts live in `test/fixtures/extinct-studio/` and validate
clean against the schemas; any failing check is reported honestly.
