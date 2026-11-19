# How Does a Gecko Let Go?

[Premiere Edition](premiere/README.md) is the enhanced picture and score. The separate [Tokay on Glass proof](creature/README.md) tests the sculpt and contact motion against the [creature realism benchmark](REFERENCE-BENCHMARK.md). The full [Creature Edition](natural/README.md) extends that original Tokay to the wildlife shots, while retaining the illustrated science at the locked narration beats. This note describes the original release.

A private 62-second, vertical explanatory film cut to the provided 60.80-second English narration v2. The edit has 22 camera setups, including a wall climb, a pad view through glass, lamella-to-seta scale changes, a parallel-loading graphic, a continuous distal-to-proximal toe roll, and a return to the same climb. This is a new rendering, not a remux or enhancement of the earlier V6 review.

## Rebuild locally

Use Node 22, `npm ci`, a Playwright-compatible Chromium, and FFmpeg/ffprobe on `PATH` or set `CHROMIUM`, `FFMPEG`, and `FFPROBE` to the executables. Default paths assume commands run from the repository root. Software WebGL renders can take a while.

1. Place the exact v2 narration at `.cache/monarch-gecko/input/narration.wav`, or set `GECKO_VOICE` to its path. The mix and master verifier check the source hash. The voice stays at its original start/speed; delivery gain, a low cut, stereo center placement, and a peak limiter are part of the mix.
2. Supply the local delivery SRT at `deliverables/How-Does-a-Gecko-Let-Go.en.srt`, or set `GECKO_CAPTIONS`. `edit.json` contains the frame-locked camera edit and action cues, not the dialogue.
3. Run `node tools/gecko/render.mjs`. This writes `.cache/monarch-gecko/master/picture.mp4`. The delivery is 1080×1920 at 24 fps, composited with native-resolution captions over a 702×1248 animated plate. `GECKO_RASTER=1` is available for a slower native-resolution plate. For inspection, set `GECKO_STILLS` to comma-separated seconds and `GECKO_OUTPUT` to a folder, or render a `GECKO_FRAMES=first:endExclusive` diagnostic range to a separate MP4.
4. Run `node tools/gecko/mix.mjs` and `node tools/gecko/finish.mjs`. `mix.mjs` writes a timed cue sheet and AAC mix under `.cache/monarch-gecko/mix/`. `finish.mjs` verifies the combined export before renaming it to `deliverables/How-Does-a-Gecko-Let-Go.mp4`.

The renderer loads the private caption file only into an ephemeral browser bundle. Neither the raw audio, finished MP4, private captions, nor the prior review ZIP belongs in the public website build or on a public branch.

## Picture, sound and verification

- `motion.js`: stance-locked footprints, ramped travel, split-diagonal support, two-bone IK and segment-integrated toe curl. The tests check foothold invariance, reachable bones, at least two supporting pads in the authored climb, and disappearance of distal contact before the palm rises in the slow view.
- `model.js`, `film.js`, `microscope.js`: original procedural model, wall, optics, pad inserts and illustrative setal views. Shot changes always occur on a 24 fps frame. The wall surface and toe pads share a contact plane; the graphic is not a measurement of force or contact area.
- `score.mjs`: the repo's `tick`, `glass`, and `air` generator kernels from `tools/soundtrack.mjs` adapted to actual stance transitions and edit markers, over a quiet, ducked bed. The micro-contact accent is editorial, not the supposed sound of intermolecular adhesion. No old narration, film audio, stock track or recorded reference footage is used.
- `verify.mjs`: probes the streams, checks fast start, decodes image and audio, meters the *decoded* audio and compares speech-bearing windows with the source to detect substitution or drift. This is not a substitute for human listening or pronunciations approval.

## Scientific visualization boundaries

The gecko resembles a Tokay; its pose, proportions, scales and movements are artist-authored, not a photogrammetric scan or a measured gait. The labeled micro sequences are enlarged qualitative illustrations. They do not imply suction cups, springs, literal flashes, a specific interaction distance, or an exact conversion between a toe angle and a seta angle. No reference figure or photo is embedded in the film.

- [Autumn et al., frictional adhesion](https://doi.org/10.1242/jeb.02486): shear in the attachment direction; loading is parallel to the surface.
- [Hu et al., digital hyperextension](https://doi.org/10.1098/rsif.2012.0108): toe deployment and distal-to-proximal release.
- [Tian et al., hierarchical adhesive structure](https://doi.org/10.1073/pnas.0608841103): toe pads, setae and terminal spatulae.
- [Russell, Delannoy & Garner, pad boundaries](https://doi.org/10.1111/joa.70251): do not treat every expanded scale as the same functional setal area.
