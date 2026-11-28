# Brief for script agent — Monarch Cam

Project: `hen-egg-factory-limit` · Channel: Monarch Cam (`monarch-cam`) · Language: English · Format: 9:16 Short · Spine: *visible animal ability → hidden biomechanical control → real physical limit*.

## Winner

**A hen builds a complete egg in about 25 hours, and almost all of that time is a calcium clock.** The visible ability is one egg a day. The hidden control is a five-station oviduct assembly line with per-station timers. The real limit is the shell gland: 18–20 hours of calcification, 2.5 g of calcium per egg against roughly 2 g absorbable per day, so the hen borrows the rest from her own medullary bone. One egg a day is not a habit; it is the ceiling.

## Run and evidence

Official scan run `46154175359`, branch `arena/96d9eaf9-top1`, keywords `x-ray animal, inside insect, how it works 3d, microscopic world, animal anatomy`, min views 5,000, max subs 500,000, min ratio 2.0, 365-day lookback.
Result: 50 candidates, 44 qualified, 25 rows, 0 errors, 584 estimated quota units. Every row has `subscriber_count_known: false`; no channel-size claim is possible.

## Ranked screened candidates

1. **Hen egg factory clock — 2,138.2x** (`cDXrpGbp34c`, SP CLASSES, 6,694,593 views, 149 s). Education category, English gap because narration is Hindi. **SELECTED.** Perfect spine fit: ability → hidden machinery → hard limit.
2. **Kinesin walking protein — 180.6x** (`Mrz-K8Jwrl0`, 19,103,948 views, 6 s). Huge hook, but it is human cell biology, not an animal ability, and the 6 s clip is a loop rather than a story. Keep as Series B.
3. **Fingers never touch atoms — 1,257.6x** (`yFVO4W0hyOg`, 9,959,323 views, 62 s). Physics, off-spine for Monarch Cam; better fit for Monarch Edits Hindi.
4. **Octopus vs crab limb regrowth — 118.3x** (`8U6chIFhnfw`, 4,035,250 views, 42 s). Strong but regeneration framing pulls toward gore-adjacent visuals; parked.
5. **Inside the ant hill — 15,503.8x** (`mUH-ArooSr4`, 25,403,044 views, 45 s). AI macro footage; Monarch Cam already ran an ant Short at 7.9K views, so demand overlap is weak.
6. **Tiny protein micro-loop — 180.6x**, **hydraulic clutch — 2,330.1x**, **turbo — 141.5x**. Mechanical, not animal; rejected for this channel's spine.
7. **Inside a Horse: X-Ray vs CT vs MRI — 140.2x** (`0iAiYbswzMU`, 4,213,133 views, 9 s). Real medical scans of a live animal; looks reused and hints at animal-distress bait. Rejected on rights and brand-safety.
8. **Animal-hospital Roblox / pet-loss Shorts — 66.0x, 13.8x**. Rejected: not provable 3D, emotional bait.

## Competitor structure audit

`cDXrpGbp34c` is a 149 s Hindi 3D walkthrough of ovary → infundibulum → magnum → isthmus → uterus → vagina, closing on "most eggs are unfertilised". Its retention device is the conveyor-belt tour. Its weakness is pacing: the shell gland gets its 18–20 hours explained in a single sentence, so the actual limit is buried.

**The English 30 s version must invert that:** open on the finished egg, jump straight to the shell gland clock, and land the calcium debt as the twist. Do not tour five organs by name; name only the magnum, the shell gland, and the clock.

**Claws Vision status:** thumbnails could not be audited. `i.ytimg.com` fails with `SSL_ERROR_SYSCALL` from this sandbox, and image search returned unrelated stock art. No palette, contrast, focal-point or caption claim is made for any competitor.

## Angle for the script

- Hook promise: this egg is not made. It is *built*, on a clock, at the cost of the hen's own bones.
- Twist beat: the shell is the slow part, and the hen cannot eat enough calcium to finish it, so she dissolves her skeleton to pay for it.
- Loop: frame 0 shows a cracked egg in a pan; the last line returns to the same pan and the same clock.
- Banned: "friends", "happy hen", "mother's love", spoken like/subscribe CTA, pest or filth bait, implied real dissection footage.

## 3D setlist (V6.2 IMAX, `tools/monarch-v6-imax-sdk/` only)

1. Hero macro of a whole egg rotating on obsidian, amber rim light, no kitchen props.
2. Parametric hen body shell, true sagittal cutaway, oviduct lofted as a five-segment tube with per-segment timer rings.
3. Yolk release at the stigma, cilia sweep, 0.2x slow-mo.
4. Magnum: albumen ribbons laid in 3 hours, hydrated layers, cyan additive pass.
5. Isthmus: shrink-wrap shell membrane, 75 minutes compressed into 1 second.
6. Shell gland: calcium carbonate crystal growth on a fibrous scaffold, 18 hours mapped to ~6 s, amber→gold palette shift.
7. Medullary bone cutaway: calcium rods dissolving into the blood stream, labelled `borrowed calcium`.
8. Physics: crystal growth as a seeded reaction-diffusion pass, particles driven by a 30 Hz solver, no hand-animated shells.
9. Loop reset: shell closes, egg drops into the pan, frame matches frame 0.

## Claim constraints for Stage 2

Must be sourced and cited on screen or in the description:

- 23–26 h total oviduct transit (Poultry Hub Australia).
- Magnum ≈3 h, ~40% of albumen; uterus 18–20 h, shell plus ~40% albumen.
- ~2.5 g calcium per egg; ~2.0 g/day absorbable from feed; shortfall from medullary bone.
- Hens lay without a rooster; unfertilised eggs are normal.
- One egg per day is near the ceiling because calcification dominates the cycle.

Must never be stated as fact: exact per-breed timings, "always exactly 25 hours", any claim that the animation shows real tissue, any veterinary or nutritional advice.

Illustrative-only labels: cutaway geometry, crystal growth speed, medullary-bone dissolve, all camera moves.

## Handoff

Stage 2 must produce the 5-hook bake-off, a 70–85-word English script at 25–35 s with `[3D_CUE]` every 2–3 s, `[TWIST_BEAT]`, `[SFX_CUE]`, pronunciation notes, a full `claims.json` ledger, and schema-valid `story.json`. No audio, voiceover or render in this stage.

Gates still red: `claimLedgerComplete`, `ownerSelection`. Score 91 → decision `not-yet`.
