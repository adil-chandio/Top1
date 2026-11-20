# Monarch Cam • trap-jaw ant cinematic review V2

This is a new shot plan, native (per-output-frame) offline CGI renderer, and sample-spotted audio mix for the locked English episode **This Ant Bites the Ground to Escape**. Nothing decodes or interpolates V1 frames. Source science and sound credits go into the review sidecar, not a slate, subtitle stream, or burn-in. The renderer shares procedural math/scene primitives with `../monarch-ant/`.

## Inputs

- The selected `Monarch-Cam-Ant-VO-v1.wav` from Batch 3, SHA-256 `4a3d3c596005cee1f077cc24c0b3a8e55ae9c29614b1f4ed77d119fd5fbf5929`, and its edit receipt. The 02/04 pickups are already in this master. No new voice selection or time-stretch.
- `fine-quartz.png`, `fern-light.png`, and `chitin-micro.png` from the V2 review's `source-assets/`, in `$MONARCH_V2_CACHE/assets/`. These are generated material/plate inputs, not filmed ants. `MONARCH_V2_CACHE` defaults to `.cache/monarch-ant-v2`.
- `audio_sources.py` verifies the recorded Foley and instrument bank inputs and preserves their original repository/revision/blob identities. Pass `--fetch` to populate a clean cache using `gh`. Only the nine specified CC0 recordings and three CC BY instrument banks are used. Read licenses in the film's review/credits sidecar before publishing.

## Build

Run from checkout root. Requires C++17, ANGLE EGL/GLESv2 and Vulkan SwiftShader, an FFmpeg with libx264/AAC, Python 3, Pillow, and NumPy. This is an offline renderer; there is no network service or frontend dependency.

```sh
export MONARCH_EGL=/path/to/angle-and-swiftshader
export FFMPEG=/path/to/ffmpeg
# Optional if using alternate locations:
# export MONARCH_VO_RECEIPT=/path/to/edit-receipt.json
# export MONARCH_VO_WAV=/path/to/Monarch-Cam-Ant-VO-v1.wav
python3 -B tools/monarch-ant-v2/audio_sources.py --fetch
python3 -B tools/monarch-ant-v2/assets.py
python3 -B tools/monarch-ant-v2/cut.py
python3 -B tools/monarch-ant-v2/mix.py
bash tools/monarch-ant-v2/chapters.sh
python3 -B tools/monarch-ant-v2/delivery.py
```

`chapters.sh` is restartable by chapter number, e.g. `chapters.sh 3`. It requires a matching plan and one completed picture/trace per chapter to assemble the film. The anchors in the plan are **illustrative animation time**, not measured milliseconds from the experiments. The renderer solves plant/strike, release, rim clearance, and a separate wall-hit path. Posed animals and ejecta are evaluated each frame at the film clock; depth and color of the *static set* can be held across a locked camera. LOD changes detail by optical set-up, never samples or repeats a moving frame. The cutaway is a diagram in 3D with independently moving capsule and muscle–attachment elements, not a literal anatomical dissection.

`mix.py` arranges recorded music samples with separately spotted sand, tarsus, pincers, impact and landing cues. It ducks the bed under speech and action. The locked VO moves only at original inter-take gaps and has a single fixed gain. Engine output is Rec.709 1280×720 at 30 fps with 48 kHz stereo; deliverable MP4 contains a video and an audio stream only.

`delivery.py` promotes the MP4 only after checking whole-film decode, frame-PTS lattice, duplicate pixels in the key sequences, native motion trace/contact/clearance/failure, soft cue onset, source VO alignment, duration, and loudness. Image boards are local QA, never baked into the master. These gates don't simulate viewer playback, artistic approval or audience response.
