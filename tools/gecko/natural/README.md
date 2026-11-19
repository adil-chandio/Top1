# Creature Edition — complete Tokay film

A separate 62-second, vertical master. The wildlife shots use the original
connected Tokay sculpt from the [continuous proof](../creature/README.md),
with new gait, close framing, two-sided glass and lamellar pad shading. The
microscope and load-vector sections remain illustrations, not wildlife
photography or a numerical adhesion simulation. The live-action look is a
CGI study, not claimed parity with the [reference film](../REFERENCE-BENCHMARK.md).

- **Locked cut**: 1,488 output frames, 24 fps. Eye, anchored pad and reaching
  pad open the film at frames 0, 28 and 56. The new digital animal accounts for
  636 newly traced frames plus a 213-frame continuous contact/release take.
  The remaining 639 frames retain the corrected Premiere scientific models
  and direction marks and explicitly identify them as illustrations.
- **Contact**: a pad lands before the body moves over it. Gait has fixed
  footprints; when two feet support it they are diagonal. In the central
  release the right front foot plants, loads, and peels tip-first with three
  other supports before the wrist clears. Then a second angle and a separate
  setal illustration distinguish whole-toe curl from microscopic shaft angle.
- **Sound and type**: untouched v2 source VO (same clock, no retime/edits), all
  32 original caption cues, and a scored mix with dry contact Foley timed to
  visible plants. The sound changes at illustration cuts are editorial, not
  audible effects attributed to setae or suction.

## Build locally

Use Python 3.11 with Blender `bpy==4.3.0` and NumPy 1.26.4, plus `ffmpeg` with
libx264, `ffprobe`, Node, and the repo's Playwright Chromium and fonts. For the
QA sheet, also install Pillow. See [creature runtime notes](../creature/README.md).
Private inputs stay in the ignored cache or deliverables directory. Set
`GECKO_VOICE`, `GECKO_CAPTIONS`, `GECKO_SCIENCE_PLATE`, `GECKO_PROOF_PLATE` or
`CHROMIUM` for alternate local paths. Use the corrected Premiere plate (with
its original titles), and the uncaptioned proof plate.

```sh
node tools/gecko/creature/export.mjs
GECKO_SETTLE=1 node tools/gecko/natural/export.mjs
G=.cache/monarch-gecko/natural

# This can be split into the closed-open frame ranges in work/plan.json.
python3 -u tools/gecko/natural/render.py --width 648 --samples 9
python3 -u tools/gecko/creature/render.py --width 576 --samples 10 \
  --poses "$G/work/settle.json" --out "$G/picture/settle" --range 208:213
node tools/gecko/natural/titles.mjs
node tools/gecko/natural/mix.mjs
node tools/gecko/natural/master.mjs --native

M=deliverables/How-Does-a-Gecko-Let-Go-Creature-Edition.mp4
python3 tools/gecko/natural/audit.py "$M"
node tools/gecko/natural/playback.mjs "$M"
```

The 1080×1920 H.264/AAC MP4 upscales the new 648×1152 native picture and the
576×1024 continuity take; captions and graphic overlays are at the output
raster. `GECKO_PREPARE=1` prints the illustration and proof segments while
other frames render. Use `GECKO_REMASTER=1` if changing a prepared span's inputs.
Never overwrite Classic, Premiere, or the separate proof.

## Optional picture-only workers

`dispatch.py` packages only allowlisted, original picture assets. Its
`--draft` mode stages locally without uploading. If Actions rendering is
needed, generate a fresh recipient certificate and keep its private key
outside the repo. Publish the temporary workflow on the active work branch
only. Do not send narration, captions, reference AV, or a private key.
`retrieve.py RUN` checks the successful native ranges against their exact
frame plan, renderer fingerprint, output SHA-256, Git object hash, and decoded
frame count before final assembly. `master.mjs "$G/dispatch/RUN"` works from
the verified packets. Retire the workflow and destroy the throwaway key only
after local verification.

QA measures frame pacing, accidental holds, in-shot range joins, complete
A/V decode, exact VO alignment, post-AAC loudness and peak, and unmuted seek
and playback behavior in a mobile browser emulation. It cannot certify
photorealism or playback on all physical devices.
