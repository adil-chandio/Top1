# Huayuan — shot plan (pass 2)

5 beats · 29 shots · 1,800 frames @ 30 fps = **60.0 s**.

> Updated after preflight 18. The earlier 1,200-frame plan left frames 1200-1800 on a locked
> hold; the shot list below is the one that actually ships.

## Pacing law

Measured cut rhythm, not a metronome (Cutting et al. 2010, 1/f structure; Gannon & Grubb, gaze
re-converges ~200 ms after a cut): **short-short-long** clusters, with exactly two long rests —
one at the fossil reveal (§4) and one at the final hypothesis (§5).

| Mean shot length | 2.0 s |
|---|---|
| Shortest | 0.87 s (26 f, beat 3 collapse) |
| Longest | 3.80 s (114 f, beat 4 fossil) |
| Shots under 2.5 s | 15 of 20 |

## Beat map

| # | Frames | Time | Beat | Content | Claim type | HUD |
|---|---|---|---|---|---|---|
| 1 | 0–150 | 0.0–5.0 s | **Stone** | Black → slab surface macro push. Light rakes across a dust-covered fracture. | Observation | `HUAYUAN · HUNAN` `512 Ma` — *no claim text* |
| 2 | 150–390 | 5.0–13.0 s | **Life** | Widen into water. Radiodont swims across frame right-to-left (metachronal flap wave), a second one far behind; opabinia drifts; hallucigenia walks the seabed; sponges breathe. | Reconstruction | `RECONSTRUCTION` (permanent stamp during this beat) |
| 3 | 390–720 | 13.0–24.0 s | **Crisis** | Light fails. Sediment rain intensifies (Rapier-driven). Current slams. One radiodont recoils; hallucigenia curls; opabinia tumbles. Emissive collapses. | Conceptual | `CONCEPTUAL · SEDIMENT EVENT` |
| 4 | 720–930 | 24.0–31.0 s | **Evidence** | Black → single raking light on the slab. Three anatomy callouts land (eye, gill, nerve cord) as labels, not as glowing features. Then the count: `153 SPECIES` → `16 GROUPS`. | Observation | `SCHEMATIC — NOT A HUAYUAN SPECIMEN` |
| 5 | 930–1800 | 31.0–60.0 s | **Refuge** | Rise back into deep water, dimmer and slower. The remaining animals drift downward, out of the light cone. Final card: `DEEP-WATER REFUGE - HYPOTHESIS`. Hold on stillness. | Hypothesis | `HYPOTHESIS` |

## Shot list (as shipped)

| # | f0 | f1 | len | Shot | Camera |
|---|---|---|---|---|---|
| 1 | 0 | 62 | 62 | Slab emergence | Explicit, slow 42 % push |
| 2 | 62 | 150 | 88 | Slab rake, fracture detail | Explicit lateral slider R->L |
| 3 | 150 | 196 | 46 | Through the water to light | Solved reef, lift 0.10->0.62 |
| 4 | 196 | 268 | 72 | Radiodont hero crossing | Solved, subject-tracked |
| 5 | 268 | 316 | 48 | Opabinia drift | Solved, fill 0.50 |
| 6 | 316 | 390 | 74 | Hallucigenia on seabed | Solved low dolly, lift 0.20->0.12 |
| 7 | 390 | 428 | 38 | Light begins failing | Solved reef push-in |
| 8 | 428 | 470 | 42 | Sediment rain starts | Solved handheld micro-shake |
| 9 | 470 | 512 | 42 | Current hits the reef crest | Solved whip-pan, blur 0.60->0.34 |
| 10 | 512 | 560 | 48 | Radiodont recoil | Solved snap-out, fill 0.58->0.22 |
| 11 | 560 | 604 | 44 | Hallucigenia curls | Solved overhead descending |
| 12 | 604 | 642 | 38 | Opabinia tumbling | Solved dutch-roll |
| 13 | 642 | 682 | 40 | Light collapses to a point | Solved vertigo counter-zoom |
| 14 | 682 | 720 | 38 | Stillness, suspended silt | Solved locked wide |
| 15 | 720 | 768 | 48 | Fossil emerge from black | Explicit top-light dolly |
| 16 | 768 | 820 | 52 | Callout 1: eye | Explicit macro arc, fov 27 |
| 17 | 820 | 872 | 52 | Callout 2: gills | Explicit rack-focus slider |
| 18 | 872 | 930 | 58 | Callout 3: nerve cord | Explicit lateral rake |
| 19 | 930 | 1004 | 74 | Rise to deep dark | Solved crane up |
| 20 | 1004 | 1072 | 68 | Animals sink out of frame | Solved down-tilt |
| 21 | 1072 | 1140 | 68 | Radiodont re-cross | Solved, subject-tracked |
| 22 | 1140 | 1230 | 90 | Vertigo into the column | Solved, lift 0.52->0.80 |
| 23 | 1230 | 1330 | 100 | Wide crane over the reef | Solved, lift 0.10->0.62 |
| 24 | 1330 | 1400 | 70 | Opabinia hold | Solved, lift 0.34 |
| 25 | 1400 | 1470 | 70 | Hallucigenia walk | Solved low dolly |
| 26 | 1470 | 1540 | 70 | Handheld drift | Solved, shake 0.030 |
| 27 | 1540 | 1620 | 80 | Overhead of the reef | Solved, lift 0.78->0.92 |
| 28 | 1620 | 1700 | 80 | Dutch roll | Solved, lift 0.58->0.66 |
| 29 | 1700 | 1800 | 100 | Final card over stillness | Solved final hold |

## Protected pure-cinema window

Frames **682-720** (1.27 s) and **1102-1140** (1.27 s): **zero text, zero HUD, zero leaders.**
Everything else carries at most one label at a time.

## Camera system

Two regimes, deliberately:

- **Solved** (24 of 29 shots). A shot declares `who` (subject), `fill` (fraction of frame height
  the subject must occupy) and `az` (orbit angle). The lens is then placed at
  `d = L / (2 * fill * tan(fov/2))` from the subject, aimed at it, with a hard floor at
  y = -1.10 so the lens never sinks into the silt. Creature shots carry a 1.9x presence gain
  because these bodies are long and low, so projected height under-reports them.
- **Explicit** (5 shots: the slab). A bedding plane is scenery, not a character - an orbit solve
  over-crops it into sand. These five keep framing verified frame-by-frame.

The floor clamp is load-bearing: preflight 18 measured 344 frames below luma 20 because the
vertigo shot drove the lens under the relief plane. After the fix the darkest frame is
comfortably above the QA gate.

## Absolute rules for this pass

1. No shot may exceed 3.8 s without an internal camera move.
2. Every cut that hides itself must cut on a moving subject's vector.
3. Any label naming an anatomical feature must also carry the schematic stamp for its whole duration.
4. `HYPOTHESIS` and `RECONSTRUCTION` never appear simultaneously in the same frame with a factual number.

## Bugs this pass found by measurement (not by looking)

Three defects were invisible in the preflight loop and only surfaced in the full 1080p master,
because preflight renders *isolated beats* while the master renders *every frame in order*:

1. **Shot plan ended at 1200 while TOTAL was 1800.** Twenty seconds of frozen frame. Fixed by
   extending the plan to 29 shots / 1800 frames.
2. **`lightAt()` returned 0 after frame 720** while sea shots resume at 930, so half the film
   was unlit. Fixed by carrying the curve through to the end.
3. **State drifted because `draw()` mutated transforms with `+=` / `-=`.** `opa.grp.position.z += k`
   accumulated once per drawn frame, so sequential rendering walked the animals several units
   below the seabed (the camera then framed bare silt: luma 4.1). Random-access preflight reset
   state each call and never saw it. All animated transforms are now pure functions of `frame`,
   anchored to a captured `HOME` pose.

A fourth was a rig contract mismatch: `createCinemaCameraRig` sets
`near = clamp(focusDist * 0.08, minNear, maxNear)`, so a wide shot with `focusDist ≈ 13` put the
near plane at ~1.05 u and clipped the entire reef to black. `maxNear` now caps it at 0.06.

Measured after the fixes, sampling every 10th frame of the finished master:
`min luma 22.07`, `mean 35.60`, lowest frames in the final hold - comfortably above the `> 8`
QA gate.
