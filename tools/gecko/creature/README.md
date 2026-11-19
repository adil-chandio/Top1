# Tokay on Glass — creature and motion proof

One uncut animation take to evaluate the [Baldeón realism benchmark](../REFERENCE-BENCHMARK.md) before expanding the treatment across the 62-second film. This is a separate **8⅔ s proof**, not an alternate full-length master. No part of either existing master is overwritten. The proof runs on the original edit interval `[774, 982)` at 24 fps (32.250–40.917 seconds), with four intact caption cues and the matching contiguous excerpt of the original English v2 recording. The renderer receives only picture parameters. Audio and caption compositing run locally.

| Within proof | Mechanic / camera beat |
| --- | --- |
| 0–0.708 s | Near forefoot reaches and opens; the other three feet remain anchored. |
| 0.708–2.710 s | Foot plants. Torso advances and shifts away toward the other supports before release. |
| 2.710–6.610 s | A continuous lens move draws attention to the pad. Digital contact rolls back from the tips with a fixed wrist base. |
| 6.610–7.700 s | Wrist can lift only after the modeled adhesive contact region clears; the same toe is visible beside its pane reflection. |
| 7.700–8.667 s | Keep the released foot and pane in view through the resolve. |

`motion.js` is the authored IK/foot schedule and camera. `export.mjs` seals the take at the desired frame rate. `geometry.py` builds one custom skin mesh connecting the head, torso, tail, shoulders and hips, with integrated palms, joined pads, shallow lamellar folds and a seated iris/spectacle. `surface.py` separates bound pigment from roughness, scale relief and soft scattering. `habitat.py` uses physical depth layers and a thin dielectric pane. The only image asset is `assets/conservatory.jpg`, an original generated far background. It does not contain the creature. No third-party model or reference picture, footage or score is embedded. Toe and lamellar motion are qualitative, not an exact biological measurement or a model of molecular forces.

## Rebuild

Use Node 22, a Blender 4.3 installation with Cycles, and FFmpeg with libass, libx264 and FFprobe. The renderer also works with Python 3.11, `bpy==4.3.0` and `numpy==1.26.4` on Linux with Blender's normal shared-library dependencies. Test stills first; tracing all 208 frames on a 2-core CPU can take a while.

```sh
node tools/gecko/creature/export.mjs
blender -b --python tools/gecko/creature/render.py -- \
  --width 576 --samples 10 --out .cache/monarch-gecko/creature/render
node tools/gecko/creature/print.mjs
CHROMIUM=/path/to/chromium node tools/gecko/creature/playback.mjs
npm test
```

`--stills 0,17,65,105,134,159,185,207` or `--range first:end-exclusive` are optional for inspection/checkpoints. Choose a fresh output directory when render inputs or settings change; the fingerprint prevents mixing old/new takes. `print.mjs` takes an optional picture directory or preassembled picture-only MP4 and optional new output path. Default output is `deliverables/How-Does-a-Gecko-Let-Go-Creature-Proof.mp4`. Supply the private v2 WAV and SRT at their usual paths or via `GECKO_VOICE` and `GECKO_CAPTIONS`. `FFMPEG`, `FFPROBE`, and `GECKO_FONT_DIR` can be overridden. Use `GECKO_AUDIO_ONLY=1` to generate just the preview mix and subtitle overlay. The WAV excerpt is sample exact; no text is regenerated. A short original score and six timed Foley cues support it without any literal suction or molecular sound.

The print step verifies full decode, fast-start, video count/cadence, metadata, true peak and time-aligned source narration. Browser QA exercises unmuted playback and the timed transitions on an emulated phone. Tests additionally verify reachable limbs, fixed planted coordinates, non-increasing distal contact, the held wrist and preserved digit arc length. Media, private WAV/SRT, generated proof frames, binary render runtimes and mix stems do not belong in Git.
