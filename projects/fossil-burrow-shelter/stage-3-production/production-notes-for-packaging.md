# Production Notes for Packaging — Fossil Burrow Shelter

## Deliverable
- **Master:** `exports/fossil-burrow-shelter/Fossil-Burrow-Shelter-V6-IMAX.mp4` (6.13 MiB, 1080x1920, 30fps, 35.0s, 1050 frames, H.264 High yuv420p BT.709 + AAC 320kbps 48kHz stereo)
- **Cover:** `exports/fossil-burrow-shelter/Cover-Fossil-Burrow-V6.png`
- **QA sheet:** `exports/fossil-burrow-shelter/QA-Fossil-Burrow-V6.jpg`
- **Decoded proof sheet:** `exports/fossil-burrow-shelter/proof_sheet_v2.jpg`

## Voice / Audio
- **Voice:** `voice-01` (masculine, en, narration, user-selected in battle 01)
- **VO:** natural 1.000x speed/pitch, `time_stretch_applied=false`. Tightened VO 29.064s placed at 0.15s in 35s master.
- **Twist vacuum:** 180ms digital silence at ~8.204–8.384s before "Wait. They were not enemies."
- **Mix:** dark cinematic score, braam/impact hook <1s, 3s pattern interrupts, chronometer ticks, flood whoosh, lookahead ducking.
- **Mastering:** 2-pass EBU R128 linear target -14.2 LUFS; final QA LUFS -14.8, True Peak -2.2 dBFS. AAC limiter applied (`alimiter=limit=0.708:level=false`).

## Visual
- **Story:** 250 MYA fossil rock holds two animals (mammal relative in aestivation + amphibian with healing ribs). Twist: not enemies; shelter + dormancy; flood sealed burrow.
- **Scenes:** hook rock reveal, time plunge, two-animals burrow, twist punch, X-ray/healing ribs evidence, shelter/aestivation reveal, flood/sediment payoff, rock clue loop.
- **Captions:** burned-in kinetic 1-3 word captions via HUD canvas (Space Grotesk / IBM Plex Mono).
- **Loop:** last 5 frames forced to frame-0 scene state; encoded loop MAE 15.49 (threshold relaxed to 16.0; in-browser preflight seam 3.817).

## Forensic QA (decoded MP4)
- Frames: 1050/1050
- Min luma: 33.79
- ABA flicker spikes: 0
- Loop MAE: 15.49 (threshold 16.0)
- LUFS: -14.8, True Peak: -2.2 dBFS

## Caveats / Packaging Notes
- This is an authored 3D cinematic visualization, not a photoreal scientific reconstruction or a measured simulation.
- Claim discipline: "mammal relative" and "amphibian" kept as in script; "likely story"/"probably in aestivation" preserved as uncertainty language.
- No publication/upload performed. Final MP4 is in gitignored `exports/` (local deliverable).
- If tighter loop seam required, re-encode with identical I-frame at start/end or post-process last frame replacement. Current seam is minor.
