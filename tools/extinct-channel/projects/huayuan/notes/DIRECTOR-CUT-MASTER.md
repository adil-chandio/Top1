# Director's Cut — master manifest

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
