# Gecko WebGL production replacement

Execution follows the earlier Three.js/Chromium frame-capture approach rather than CPU Cycles. This does **not** certify equivalence to, or superiority over, the prior Bear episodes.

## Production

1. From repository root, export the original illustrative subject:
   `LD_LIBRARY_PATH=$PWD/studio/runtime/gecko OMP_NUM_THREADS=2 studio/runtime/seatbelt-env/bin/python research/monarch_cam_gecko_batch5/webgl/export_subject.py`
2. In this directory: `npm ci --no-audit --no-fund`.
3. `node render_full.mjs --samples` creates twelve shot samples. `node render_full.mjs` renders all remaining frame checkpoints and runs the encoder.

Outputs remain ignored under `studio/runtime/gecko/webgl-production/`. Inputs include the original `.blend` created by `build_cinematic_replacement.py`, the locked narration WAV, the approved-script caption cues, and a local Python environment with Pillow and imageio_ffmpeg. Neither model nor narration binaries are committed here. This is a local-workspace production pipeline, not a clean-clone standalone release bundle.

The Chromium npm package supplies compressed shared libraries; the production runner extracts its pinned `al2023.tar.br` into ignored runtime storage. No external model download, browser-profile credentials, reference-image pixels, music, or SFX are used. npm dependency licenses remain their respective licenses; this is not independent commercial clearance of narration/dependencies.

## Frames and integrity

- 720×1280 native WebGL frame capture, 25 fps, 1,592 frames, 63.68 seconds.
- Three visual worlds: static posed whole-animal exterior with moving perspective cameras; a continuously deforming original local digit with ventral lamellae and claw; original 3D microscopic schematic.
- Deterministic procedural skin/wall textures, directional warm/cool lighting, shadow maps, ACES tone mapping, English HUD/captions. This scene does not currently use the old Bear composer's bloom/grade shader.
- Twelve-sample infrastructure benchmark is distinct from full-production timing and is not a quality pass.
- Production input hashes guard subsequent checkpoint resumes. Changing scene/assets/cues requires invalidating affected frame checkpoints and explicitly establishing a new manifest. In this initial run, unaffected exterior/microscopic checkpoints were retained across macro-only framing/contact corrections; affected macro checkpoints were removed and rendered again.
- Loaded local lamellar minimum reaches the declared substrate plane within numerical tolerance; sampled tip heights increase through the release. These narrow authored-geometry tests are not biological validation or a collision/anatomical pass.
- Encoder checks every expected JPEG/dimensions, asserts exact approved narration source SHA-256, encodes H.264/AAC, and performs full decode QC. No claim of assistant native audiovisual listening.

## Explicit unresolved quality limitations

The subject derives from the previous original whole-animal **self-review-failed** procedural asset, with smoothing, smaller eyes and replacement material work. It is not a newly acquired production-quality animal scan or a validated rig. Toy-like proportions, simple environment and illustrative digit geometry remain real limitations. Do not call this production photoreal, scientifically validated, user accepted, or above the Bear benchmark merely because the new renderer is faster or the complete file exists. Whole-animal gait is not animated. The local toe is a qualitative explanatory view, not a measured species-specific motion reconstruction. Public publication remains unauthorized.

The initial bpy export wrote a valid GLB and reported export completion, then its process exited 139 during teardown. The exported file's header/declared length and actual GLTFLoader import were checked separately; process success must not be claimed for that attempt.
