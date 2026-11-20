# Monarch Cam · Field Note 01A

**This Ant Bites the Ground to Escape** — an offline 3D reconstruction and review edit, not a release workflow. `proof.plan` is the native 24 fps close-to-wide contact study; `cut.py` builds the seven-beat review around the locked Batch 3 WAV. No step changes sharing, deploys anything, or publishes the film.

## What is animated

- `scene.hpp` defines the sand funnel, antlion/ant geometry, ant joint rig, toe targets, jaw sweep, grain trajectories and camera moves. The success passage solves min-tip height to the slope before a separately keyed body trajectory. The failed trajectory hits the inner wall and returns into the pit. This is a **qualitative reconstruction**, not a granular-material solver, fitted lab motion, or measurement of force, time, scale, or frequency.
- `render.cpp`, `gpu.hpp` and `shaders.hpp` are an offscreen OpenGL ES renderer with lit 3D meshes, a shadow pass and a depth-based macro blur. The two AI-generated 2D materials are sand albedo and distant bokeh; they are not the creature animation. There is no matched or pasted lab footage. `prepare.py` composes the editorial graphics and labels the reconstructed timebase.
- `sound.py` generates designed stereo sand ticks, grain swells, contact, landing, and a restrained air bed. No field recordings or score. The VO is sample-locked, with 31 seconds of intentional picture holds inserted between takes/into the coda. Only a common gain is applied; no word edits or time-stretch.
- `captions.py` lays out the current script text from the locked take timings. ASR is used for time anchors only. `delivery.py` checks decoded H.264/AAC, technical sound levels, geometric event order, and VO correlation at the intended offsets.

## Reproduce the review

Requires Linux x86-64, GCC with C++17, Node/npm, Pillow and NumPy, FFmpeg with `libx264`, and an ANGLE/SwiftShader build with an EGL/GLES client ABI. With `@sparticuz/chromium@131.0.1` only the contained `swiftshader.tar.br` is needed; later builds can have different exports.

```sh
G=/tmp/monarch-ant-gl
mkdir -p "$G"
A=$(npm pack --silent @sparticuz/chromium@131.0.1 --pack-destination "$G")
tar -xOf "$G/$A" package/bin/swiftshader.tar.br \
  | node -e 'process.stdin.pipe(require("zlib").createBrotliDecompress()).pipe(process.stdout)' \
  | tar -xf - -C "$G"
export MONARCH_EGL="$G" FFMPEG=ffmpeg
C=.cache/monarch-cam-ant-film
D=deliverables/monarch-cam-step-4
mkdir -p "$C/assets" "$C/work" "$C/qa"
cp "$D/source-assets/"{sand-albedo,beyond-the-rim}.png "$C/assets/"
cp "$D/source-assets/"{film.plan,film.json} "$C/work/"
# The captured plan is derived from Batch 3's edit receipt. To change shots,
# restore that receipt and regenerate with `python3 -B tools/monarch-ant/cut.py 768 432`.
python3 -B tools/monarch-ant/prepare.py 768 432 $(awk '{print $7}' "$C/work/film.plan" | sort -u)
VIDEO_MAXRATE=1950k VIDEO_BUFSIZE=3800k X264_PRESET=veryfast \
  tools/monarch-ant/encode.sh 768 432 "$C/work/film.plan" "$C/work/film-picture.mp4" \
    --trace "$C/qa/film-motion.csv" --draft 1
python3 -B tools/monarch-ant/sound.py film "$C/work/film-mix-v1.wav" "$C/qa/film-audio-v1.json" --timing "$C/work/film.json"
# Delivery uses the checked-in-workspace .srt sidecar under $D and the locked
# Batch 3 voice WAV at deliverables/monarch-cam-step-3/Monarch-Cam-Ant-VO-v1.wav.
python3 -B tools/monarch-ant/delivery.py film
```

For labeled proof frames, use a separate `MONARCH_ANT_CACHE` so the RGBA overlays match dimensions, copy the two materials into its `assets/`, run `prepare.py 1280 720 proof` in that context, then `encode.sh 1280 720 tools/monarch-ant/proof.plan ...` **without** `--draft`. Use `sound.py proof` for the frame-82 sound cue. `encode.sh` writes an atomic video-only asset; final mux should include the stereo track and BT.709 tags. The decode gate expects the proof trace under `$C/proof/qa/contact-motion.csv`. Set `X264_PRESET=veryfast VIDEO_CRF=17` for the contact proof (not the long-form VBV settings).

The review picture is 768×432 at 24 fps. It renders all contact close-up, wide clearance, and failure frames; slower B-roll blends within shots between native frames to limit CPU rendering time. For a new master, disable this preview mode, render at the delivery resolution, review cuticle/locomotion and grain occlusion on the larger raster, and audition the Foley on headphones and speakers before locking. Do not apply a YouTube upload step to the review copy.

## References

- [Larabee & Suarez (2015), PLOS ONE](https://doi.org/10.1371/journal.pone.0124871) — contact sequence, successful and failed escape jumps, observational outcomes and the two handled conditions. Figures 3–4 and Tables 1–2 are the study reference, not pixels in the edit.
- [Sutton et al. (2022), JEB](https://doi.org/10.1242/jeb.244077) — the study of jaw closure, elastic head capsule and muscle–attachment unit. The head cutaway does **not** represent a CT scan.
- [Büsse et al. (2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8440033/) — supporting pit-maintenance context in a different antlion species, not trajectory evidence for this animal.
