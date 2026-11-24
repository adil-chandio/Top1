# Director's Cut — master manifest

> **v2 is the current delivery** (`Director-Cut-v2`): water optics, cold seabed palette and the
> rebuilt mix. This file describes **v1**; v2's numbers are at the bottom. v1 is kept because its
> measurements are what exposed both defects.

**File:** `exports/extinct-channel-huayuan/director-cut-master/Director-Cut-V6-IMAX.mp4`
**Size:** 72,989,041 B (69.61 MiB) · **SHA-256:** `ee7b467c56a92747a061b5bfad4c2fd183bc33313d0f928387c3c578d6142f4f`
**Spec:** 1920×1080, 30 fps, 1,800 f, 60.000 s, H.264 crf 16 (bt709), AAC 48 kHz muxed.
**Audio:** the previously approved mix, unchanged — picture was recut only, nothing was retimed,
re-recorded or regenerated.

## Forensic QA (`verify_imax_mp4`, 17 cut frames, loop check off)

| Gate | Result |
|---|---|
| Decoded frames | **1800** (exact) |
| Black / dropped frames | none — `min_luma 10.89` (gate is > 8.0) |
| A→B→A single-frame flicker | **0 spikes** |
| Integrated loudness | **−15.2 LUFS** (gate −15.4 … −13.2) |
| True peak | **−1.5 dBFS** (gate ≤ −0.9) |

All asserts in `forensic_qa_sdk.verify_imax_mp4` cleared. The function returns a metrics dict
rather than a `pass` flag; the pass is the absence of an assertion, and every number above is from
that run.

## Cut

17 shots, cut frames **0, 120, 258, 315, 472, 560, 617, 663, 690, 990, 1176, 1290, 1420, 1517,
1637, 1722, 1779**. ASL 3.53 s, median 3.23 s, longest 10.00 s (2.83×), shortest 0.70 s (0.20×),
max/min 14.3×, anchor 16.7% of runtime. Eight focal lengths: 14 / 24 / 28 / 35 / 50 / 85 / 100 mm.
Full shot table and motivations in `DIRECTOR-CUT-PLAN.md`.

## Proof

`PROOF-FRAMES.jpg` — 18 frames pulled from the master itself (f45 … f1795), one per shot plus the
reveal's midpoint. Contact sheet, 1680×2094.

## Delivery

Google Drive: `Huayuan-60s-DIRECTORS-CUT-V6.mp4`, id `1h8bx-hBRrgEaWI_UqKqwZvHEgZQnGUqT`,
shared `anyone` / reader, uploaded size verified against the local file.


---

# v2 — the enhanced master

**File:** `exports/extinct-channel-huayuan/director-cut-master-v2/Huayuan-60s-DIRECTORS-CUT-v2.mp4`
**Size:** 74,580,820 B · **SHA-256:** `892f5b1e4465e6df98ec3d63fe914f342cb14f99120678641f0f41448b404eff`
**Spec:** 1920×1080, 30 fps, 1,800 f, 60.000 s, H.264 crf 16, AAC 256 kbps 48 kHz.

## What changed from v1

**Water (the sea read as a lit room, not water).** Three layers were missing entirely:
- *light shafts* — crossed additive planes under a soft falloff, one group of 9, so the light has
  a volume and a direction instead of appearing as a flat dome gradient;
- *caustics* — a moving two-wave interference pattern on the bed at y −1.50;
- *marine snow* — 1,500 drifting points, so the water between the lens and the animal is not empty.
All three are driven by the same `key` curve, so the crisis darkens them together.

**Palette (the bed was warm).** Measured: bed R/B **1.22** at f1400 under a *cyan* key — the
warmth was coming from a neutral-sand albedo, the preset's amber rim light and a warm fog, not
from the key. Fixed all three: bed albedo → `#5c6f74` with rim off, creature albedos cooled, rim
light → `#7fd8e8` at 0.44, fog → `#17505f` at 0.046. **Measured after: R/B 0.29.** The only warm
light left in the sea is the rim on the animals' backs.

**Audio (the actual complaint).** The approved mix had no bed at all — 10.5 s of literal silence
across five gaps (the worst 3.00 s, 20.00–23.00 s) — and it also **clipped**: 795 samples above
1.0, decoded peak 1.1679. A synthesised score was built that follows the cut (chord change on the
extinction at 23 s, pulse only through the crisis, riser + sub drop into the cut), then mixed with
a **sidechain measured from voice activity** (10 ms RMS, gated, 30 ms attack / 300 ms release):
the bed drops 62% under speech and returns in every gap. Full method in `MIX-V2.md`.

## v2 QA (`verify_imax_mp4`, 17 cut frames)

| Gate | Result |
|---|---|
| Decoded frames | **1800** (exact) |
| Black / dropped frames | none — `min_luma 13.23` |
| A→B→A flicker | **0 spikes** |
| Integrated loudness | **−15.4 LUFS** (gate −15.4 … −13.2) |
| True peak | **−1.3 dBFS** (gate ≤ −0.9) |

Note on the QA catching a real defect: the first v2 remux failed with **true peak −0.2 dBFS** —
the AAC encoder overshot the sample-peak ceiling I had set. The mix was pulled down 0.9 dB and
re-muxed, and the gate then passed at −1.3. The gate did its job; it is not decoration.

## Proof

`PROOF-FRAMES-v2.jpg` — 18 frames from the v2 master, same frames as v1 for a direct comparison.

## Delivery

Google Drive: `Huayuan-60s-DIRECTORS-CUT-v2.mp4`, id `1-FRmJADHTdVBbkXMMN-m19misF5UhtEq`,
shared `anyone` / reader; uploaded size verified byte-for-byte against the local file.
