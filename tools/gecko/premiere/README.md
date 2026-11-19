# How Does a Gecko Let Go? — Premiere Edition

The 62-second enhanced film retains the exact 60.80-second v2 recording and original scientific structure. It's an independent master, not a color filter over the first MP4. No new dialogue, speed changes, or replacement recordings.

## What changed

- **The first step:** a tight Tokay eye insert, an anchored pad, then the same pad peeling and planting. The new eye/skin textures, subdued glass reflections, contact occlusion and layered wet-forest backdrop are lit and photographed in Three.js. The animal, digits and fibres are 3D models; the distant canopy and surface color plates are original AI-generated production assets, not footage of a real gecko.
- **The mechanism:** 29 camera setups at 24 fps. Clearer pad-to-lamella-to-seta scale changes; the toe base and distal tip callouts follow the animated mesh. The load vector is parallel to the substrate. The release/contact markers track the supported part of the toe. A separate setal sequence distinguishes microscopic fibre bending from digital hyperextension.
- **The mix:** original stereo D-minor score with felt-like plucks, a low pulse, bowed textures and a glass-mallet motif. The music rises in selected narration gaps and ducks under the voice. Existing repo `tick`, `air` and `glass` kernels contribute to 35 authored action/editorial cues. No musical or Foley claim is made about literal suction or microscopic noises. The final soundtrack is AAC-LC stereo at 48 kHz, 256 kb/s target.
- **The limits:** the authored IK pose, cutaway anatomy and micro imagery are explanatory, not measured force data, a live-action animal, or a molecular-scale simulation. The [scientific design sources](../README.md#scientific-visualization-boundaries) still apply.

## Rebuild

From the repo root use Node 22, `npm ci`, Chromium (`CHROMIUM`), FFmpeg (`FFMPEG`) and ffprobe (`FFPROBE`). Put the source narration at `.cache/monarch-gecko/input/narration.wav` or set `GECKO_VOICE`. Use the same private English SRT from the first master (`GECKO_CAPTIONS` to override). The new shot/edit table is in `edit.json`; the caption wording remains local.

```sh
GECKO_EDITION=premiere node tools/gecko/render.mjs
node tools/gecko/premiere/mix.mjs
GECKO_EDITION=premiere node tools/gecko/finish.mjs
```

Defaults render the moving 3D plate at 778×1382 and composite at 1080×1920 with full-resolution text. All 1,488 unique frame positions are rendered, with six atomic chapters fingerprinted by inputs and the browser bundle for resumption. Set `GECKO_RASTER=1` for a slower native-resolution plate. `GECKO_STILLS` and `GECKO_FRAMES` are available for shot proofing. `finish.mjs` adds the exact mix without a new video encode and verifies the complete MP4 before moving it to `deliverables/How-Does-a-Gecko-Let-Go-Premiere-Edition.mp4`. The original master and Drive upload remain separate.
