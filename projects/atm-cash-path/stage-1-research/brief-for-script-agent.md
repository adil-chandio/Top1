# Stage 1 brief — ATM cash path (API-verified outlier)

Status: Stage F handoff package · 2026-11-25 · format 9:16 Short · **decision: not-yet (89/100)**

## What changed vs the fallback package

Earlier `projects/rounded-window-stress/stage-1-research/` was built from public web fallback only. GitHub Actions permission was fixed (App `4187077`, `actions=write`) and the official YouTube Data API v3 scanner ran successfully:

- Run `45623586499`; artifact assembled at `/tmp/research_vision/outlier_scan.json`.
- 40 candidates, 38 qualified, 25 outliers, 12 API calls (476 quota units), `errors: []`.
- Every candidate has `subscriber_count_known: false` because YouTube hides `subscriberCount`; the "small channel" part of the outlier thesis is **unverified**. Treat ratios as noisy relative signals.

The fallback package is retained as evidence history but superseded as winner selection.

## Ranked candidates (real API ratios)

1. **ATM cash path — 13,978.76x** (39.56M views / median 2,830; 40 s; Discover Inside, `NArAKj4zbB8`). Public page fetched. Hook mechanism: "press withdraw → money appears; what happens in between?" 3D cutaway shows authentication → authorization → cash counting → verify → dispense.
2. **Medieval castle arrow slit — 1,840.72x** (20.10M / median 10,918; 26 s, `06rlNjokJNA`). Strong outside-vs-inside reversal: tiny gap outside, wide firing arc inside. Excellent geometry but contains weapon/violence context; lower brand-safety fit for this brief.
3. **RBC under microscope — 1,334.22x** (3.34M / median 2,503; 62 s, `sxN7z9UTqpM`). Visual grid/scale mechanic, but diagnostic language risks unverified medical claims.
4. **Touch / Pauli exclusion — 775.69x** (7.81M / median 10,066; 31 s, `BK2LymqGNPw`). Hook strong; fetched transcript is music-only so script proof must come from primary physics sources, not that video.
5. **Kinesin walking — 344.46x** (11.58M / median 14,074; 6 s, `vwN2OTHZl3I`). Description admits significant editing and fair-use reuse → rejected by rights gate.

Raw ratio winners such as 20,254.10x mechanical-failure compilations are meme/reused reaction clips, not original engineering; excluded for rights and brand safety despite view ratios.

## Winner: `atm-cash-path`

Hook variants ( ≤10 words, promise visible in first frame ):
- “Where does the ATM hide 20 notes?”
- “Press withdraw. Watch the machine count.”
- “The cash travels 40 cm in 4 seconds.”

Paradox / “Wait.” beat: the money does **not** come from a slot behind the screen — an internal belt moves each note past sensors before the shutter opens.

Feasibility: 9:16, ~30–45 s. Use our own parametric lofting for the ATM housing, roller/cassette belts, note stack, sensor gate and dispenser shutter. Include one X-ray/sagittal cutaway and one close slow-motion beat. Newtonian physics only: rollers accelerate notes, friction separates them, sensors count them; no fantasy quantum hand-waving.

## Gates still open (do not advance)

- `claimLedgerComplete: false` — every on-screen count/timing claim needs a primary source or must be shown as a stylized simulation.
- `ownerSelection: false` — human owner must approve winner, title and music/sound cues.
- No Claws Vision audit: `i.ytimg.com` unreachable from this sandbox; no thumbnail palette/contrast/focal/text/safe-zone comparison was possible. Do **not** claim visual competitor proof.
- Subscriber counts hidden for all candidates; do not call these verified small-channel outliers.

## Script agent instructions

1. Keep hook, visual proof and caption in first 2 seconds.
2. Never reuse competitor CGI frames, captions, audio or shot ordering.
3. Prefer generic mechanism language; no claims about a specific bank, currency security design, or exact denomination counts without a ledger entry.
4. End on loopable cutaway reset (cash path returns to cassette) for replay.
5. Return claim ledger + asset needs + duration beats; Stage 2 cannot mark `production-candidate` until the two false gates are green.

Evidence: `research.json`, `idea-scorecard.json`, `projects/rounded-window-stress/stage-1-research/` (fallback history), scan run `45623586499`.
