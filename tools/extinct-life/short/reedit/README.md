# Atlantic Tracks — Short 01 · V2 Kinetic Recut

Same Short, revised in response to the pauses and the on-picture edit. **Why Dinosaur Footprints Can Fool You** now runs **24.50 s** (735 frames at 30 fps); the earlier 34 s master stays intact. This rebuild uses the original dry narration and scene inputs, **not** a time-remap, crop or pixel reuse from the old export. No film, permission or Studio publication action is automated.

## Editorial changes

- **Cut the voice first.** Fourteen aligned phrases are extracted from the checksum-locked original recordings, with measured quiet splice edges and guards for breath and consonants. There is no respeed or syllable trim. The longest *aligned inter-phrase* pause fell from 2,603 to 170 ms; this differs from the longest low-RMS window in the speech stem, which also counts unvoiced sounds. The decoded mix is measured on phone-band mono, including its replay seam. Rebuilt ambience, a continuous 122 BPM pulse and 19 sync cues replace long quiet holds.
- **Animate in camera, then add graphics.** The opening has a tighter arc plus a short contact impulse. The firm/soft test uses the same dolly, foot and movement clock. A tracked close shot picks up that relaxing soft bed, then the two results are stacked at equal scale without running the shots over one another. In Brazil/Cameroon, the map-colored tracing rides the original illustrated relief. The globe has a continuous view, engraved parallels and an independent epoch reveal. A shortened return preserves the action seam; no separate outro.
- **Type follows speech.** Readable phrase groups, 14 full English SRT cues and per-word accent timing all use the same sample and frame clock. Selected words have beveled faces and seven depth slices projected through a rotating camera plane; they settle rather than bouncing throughout every line. Captions are not laid on permanent black boxes. Scene labels and geometric pins have their own UI-safe spacing audit.
- **Sound tells the materials apart.** Low contact bodies, real wet releases and granular edges lead into short stone and atlas accents. The end breath/score folds into the next hook. A voice-keyed mix gives syllables space without turning the score off. The mixed stereo bed uses a six-millisecond codec edge taper, not an extra silent hold.
- CGI and the illustrated track surfaces remain identified as such. The two dated map layers are independent snapshots, not an animation of empirical plate velocities. 125 Ma is a geographic snapshot, not a track age. The region pins are independent and are not connected by a route. Research and licensed asset credits are in the Studio sheet; see also the [original production notes](../README.md).

| Frame | Time | Edit |
| ---: | ---: | --- |
| 0 | 0.00 | Contact on frame 5; lift and imprint reveal |
| 62 | 2.07 | Firm mud |
| 117 | 3.90 | Softer mud, matched dolly |
| 160 | 5.33 | Failing edge with late chip at frame 190 |
| 207 | 6.90 | Firm/soft, stacked at the same scale |
| 253 | 8.43 | Sousa Basin, Brazil |
| 323 | 10.77 | Koum Basin, Cameroon |
| 364 | 12.13 | Position and distance today |
| 438 | 14.60 | Continuous globe camera; rewind from frame 442 to 496 |
| 598 | 19.93 | Rock face; connected land is not a known trail |
| 696 | 23.20 | Return to incoming foot; loop |

## Render and verify

Run from repo root, C++17/OpenMP and Python 3.11+, same [pinned dependencies](../requirements.txt). Restore the untouched dry six takes and texture swatches from the V1 production record if the cache is cold. `prepare_reedit.py` checks Space Grotesk against the Google Fonts pin as well as preparing the existing shared fields, sound assets and other fonts. Original releases are read-only to these scripts.

```sh
SHORT=tools/extinct-life/short
REEDIT="$SHORT/reedit"
python3 -m pip install --target .cache/atlantic-short/python -r "$SHORT/requirements.txt"
export PYTHONPATH="$PWD/.cache/atlantic-short/python" PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python3 "$REEDIT/prepare_reedit.py"
python3 "$REEDIT/mix_edit.py"
python3 "$REEDIT/build_reedit.py" --phone-cut
python3 "$REEDIT/verify_reedit.py" --phone
python3 "$REEDIT/build_reedit.py"
python3 "$REEDIT/verify_reedit.py"
```

An optional `--proof` builds stills only. Native delivery is a 1152 × 2048 source render composited at 1080 × 1920 and encoded to H.264 High plus 48 kHz stereo AAC. `--verify-only` checks a promoted local delivery rather than a staged file. The verifier checks every decoded frame, motion through the replay seam, contrast, map labels, caption bounds, the audio sample count, per-phrase shifts and mono-band clarity, transient placement, residual quiet gaps and file identity before staging. Proof/encoded probe images, timeline, traces, mixer and final verification reports are in `.cache/atlantic-short/reedit/qa/`. These are instrumented checks and visual reviews, not a human narration/accent sign-off.

Release artifacts: `deliverables/extinct-life-short-01-v2/Atlantic-Tracks-Short-01-V2.mp4`, `.en.srt`, and `-Studio.txt`. Deliver V2 separately under the existing **Atlantic Tracks - Short 01** folder so the original V1 links cannot point at mismatched captions or be overwritten. No second subject, thumbnail file or publication.
