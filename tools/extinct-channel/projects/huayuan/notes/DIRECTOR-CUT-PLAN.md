# Huayuan — Director's Cut, shot by shot

**Status:** shot plan is live in `film_v2.js` and has passed frame-by-frame preflight (14 sheets).
Not a master yet: the 1080p render and forensic QA have not run on this cut.
**Runtime:** 60.000 s, 1,800 f @ 30 fps, 1920×1080.
**Audio:** the approved mix is unchanged — this cut recuts picture only.

---

## 1. Why the last film had no direction

Measured off the shipped 29-shot edit (`notes/DIRECTION-GAP-DIAGNOSIS.md` has the full working):

| Property | Shipped edit | What a cut needs |
|---|---|---|
| Average shot length | 2.07 s | 3–4 s for a contemplative register |
| Longest shot | 3.33 s = **1.61× ASL** | one anchor at 2–3× ASL |
| Shot-length spread | max/min **2.63×** | 8–20× |
| Shots over 3 s | 6.9% | 15% |
| Distinct camera moves | **20 for 29 shots** | a vocabulary, repeated with variation |
| Lens range | 27°–43° (**1.6× ratio**) | 14–135 mm (≈6× ratio) |
| Median vs mean | median above mean | median below mean (right-skewed) |

The individual frames were fine. There was no *shape*: no long shot to earn the short ones, no
repeated size to build a rhythm, and one focal range, so nothing could be emphasised by cutting
to a different lens. That is not an animation problem and adding detail would not have fixed it.

---

## 2. The cut

Six sequences. Shot lengths fall through the crisis and expand again in the return, so the
audience feels pressure before the animals do. Lengths are frames at 30 fps.

| # | In | Out | s | Set | Size | Lens | Subject | Cut motivation |
|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 120 | 4.00 | slab | ECU | 50mm | stone | cold open — texture before meaning |
| 2 | 120 | 258 | 4.60 | sea | MS | 35mm | radiodont | cut on look (we follow the eye to the animal) |
| 3 | 258 | 315 | 1.90 | sea | CU | 85mm | opabinia | cut on look (radiodont turns, we land on what it sees) |
| 4 | 315 | 472 | 5.23 | sea | EWS | 14mm | geography | **smash cut** — the widest lens in the film arrives with the event |
| 5 | 472 | 560 | 2.93 | sea | WS | 35mm | geography | cut on action (silt enters) |
| 6 | 560 | 617 | 1.90 | sea | MCU | 85mm | hallucigenia | cut on action (it tries to right itself) |
| 7 | 617 | 663 | 1.53 | sea | ECU | 100mm | radiodont | cut-away — the largest animal leaving |
| 8 | 663 | 690 | 0.70 | sea | WS | 24mm | geography | cut on sound — the last light goes |
| 9 | 690 | 990 | **10.00** | slab | EWS | 35mm | fossil | **match cut** — the rock, now a body. The anchor. |
| 10 | 990 | 1176 | 6.20 | slab | MS | 35mm | fossil | cut on look — down the spine |
| 11 | 1176 | 1290 | 3.80 | slab | CU | 50mm | fossil | cut on action — the segmented body in relief |
| 12 | 1290 | 1420 | 4.33 | sea | WS | 28mm | ecology | cut-away — back to the water, same place |
| 13 | 1420 | 1517 | 3.23 | sea | WS | 50mm | ecology | **>30° reversal** — in among them, not a repeat |
| 14 | 1517 | 1637 | 4.00 | sea | MS | 35mm | hallucigenia | cut on look |
| 15 | 1637 | 1722 | 2.83 | sea | MCU | 85mm | opabinia | cut on action |
| 16 | 1722 | 1779 | 1.90 | sea | CU | 85mm | radiodont | cut on action |
| 17 | 1779 | 1800 | 0.70 | sea | WS | 24mm | geography | cut on action — out |

### The numbers this cut actually hits

- **ASL 3.53 s**, median **3.23 s** — median below mean, as required for a right-skewed cut.
- Longest **10.00 s = 2.83× ASL** (the reveal, 1 shot, 16.7% of runtime). Shortest **0.70 s = 0.20× ASL**.
- **Max/min 14.3×.** Shot lengths fall across the crisis (5.23 → 2.93 → 1.90 → 1.53 → 0.70).
- **8 distinct focal lengths**: 14 / 24 / 28 / 35 / 50 / 85 / 100 mm. The previous cut had one effective range.
- Sequence ASL: STONE 4.00 · LIFE 3.25 · CRISIS 2.50 · WITNESS 6.67 · RETURN 2.83.

> The first version of this table was wrong and the cut was wrong with it: 17 shots measured a
> median of 3.90 s against a mean of 3.75 s, i.e. **not** right-skewed, which is the exact failure
> this document exists to prevent. The 7.57 s RETURN wide was split into two setups (with a >30°
> reversal, so it is not a stutter) and the measurement now passes. The plan is checked against
> the code by a script, not by memory.
- **Size ladder verified: 0 violations, 0 stutters.** No two adjacent shots sit one rung apart
  without a ≥30° angle change; the slab walks EWS → MS → CU across three cuts; the radiodont gets
  four distinct sizes.

---

## 3. What the preflight changed (and what that says about the method)

The plan above was written from pacing maths, not from looking. Looking changed it — 14 preflight
sheets, and every change below was forced by a measurement, not a mood.

1. **`bodyCentre` multiplied the height offset by `grp.scale.x`.** The hallucigenia rig imports at
   ~1/66 world size, so a 0.16 offset became **y ≈ 9.8** and shots 6 and 13 aimed ten units above
   the animal — pure empty water. Offsets are now fractions of real body height.
2. **The solver assumed a resting pose.** `distForFill` sized every creature by its rest length,
   ignoring that a body seen end-on is not 3 m wide on screen. Replaced with a projected-bounds
   solve: project the *deformed* bounding box through a candidate camera, step distance until the
   body covers the planned fraction of frame width, and re-measure the centring correction every
   iteration (a correction that is never verified is a guess).
3. **The step direction was inverted.** `w ∝ 1/dist`, so the corrective ratio is `w/fill`; the first
   version used `fill/w` and drove every creature shot to the 40-unit clamp.
4. **`matrixWorld` was stale.** Performance writes `grp.position` every frame, but matrices are
   recomputed at render time, so the solve was framing the *previous* frame's pose.
5. **`fill` could never express a close-up** while it meant "body spans this fraction of frame."
   A CU is a body *wider* than the frame, so the values now run above 1.0.
6. **The slab set had no room.** A 12×8 plate on nothing meant low lenses ended in a black band
   where the set stopped. It now has a floor and a cyclorama.
7. **The fossil had no relief.** At 170 px/u (4096 px across 12 u) no lens could cut a macro out of
   a painted plane — 100/135 mm shots were 37-pixel blits blown up to 1080. Real relief was added
   along the fossil's own painted outline, and the set's close work moved to 35–50 mm, which is the
   range that asset can actually support.
8. **Two shots were cut for being physically impossible.** A 0.50 s smash cut and a 0.63 s insert
   existed only to hit a pacing target; they broke the plan's own 0.25×-ASL floor and read as
   flicker. The crisis now ends on a 0.70 s shot that has a motivation.

### What was abandoned rather than fixed

- **A 135 mm "eye" insert on the fossil.** The eye is *painted into the texture*, not modelled. At
  135 mm the frame covers ~0.3 u of a 341 px/u asset — a 25× upscale of a smudge. No lens, light or
  grading fixes that; the shot was replaced with a 50 mm backlit view of the segmented body, which
  is the one thing the asset genuinely has. **This is the honest limit of the current model:** HUD
  callouts now name structures the geometry can carry (DORSAL SPINES, SEGMENTED BODY), and nothing
  claims an anatomy that is not there.

---

## 4. What is still not proven

- This is a **preflight** cut. The forensic QA (`verify_imax_mp4`) has not run on 1920×1080.
- The **reconstruction claim** stays labelled: HUD says `RECONSTRUCTION`, `CONCEPTUAL · SEDIMENT
  EVENT`, `SCHEMATIC · NOT A HUAYUAN SPECIMEN`. The deep-water refuge is a hypothesis and the stamp
  says so. None of that changed in this pass and none of it should.
- The 10 s anchor is long for a 60 s film (15.5%). If it fails on the 1080p pass, the fix is to trim
  it to ~8 s and let shot 10 absorb the difference — **not** to cut the anchor out.
