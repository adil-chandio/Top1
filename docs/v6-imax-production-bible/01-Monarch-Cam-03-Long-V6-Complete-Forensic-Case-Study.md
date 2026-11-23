# Monarch Cam #03 — Long Video V6 (Hollywood IMAX Cinema Hall Edition)
## Complete A-to-Z Forensic Production Case Study (Zero-Omission Technical & Creative Trace)

This document records **every single source, tool, file, mathematical formula, shader pass, camera move, audio DSP stage, visual bug fix, render command, forensic test, and cloud upload** executed to build **`Monarch Cam #03 — Long Video V6 (Hollywood IMAX Cinema Hall Edition)`** (`1920×1080`, `30.000 fps`, `9,008` frames = `300.267s` / `5m 00.27s`).

---

## 1. Exact Tools, Connectors, Directories & External Access Trace (Where We Went, What We Opened, and Why)

### 1.1 Web Tabs / Browser Usage (Exact Truth)
- **External Web Search / Public Web Pages Opened:** **`0` external web tabs** were needed during the V6 rebuild because the primary peer-reviewed paper (`Jayaram & Full, 2016, PNAS 113(8): E950–E957`, `PMC4776529`) had already been extracted and verified in the repository manifests, and outbound network access in the build sandbox is strictly scoped to `github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`, plus authenticated Arena connectors (`google_drive`, `google_docs`).
- **Local Headless Chromium Tabs Opened (`Playwright` + `Vite` Loopback Server):**
  - Headless `@sparticuz/chromium` (`v133.0.0`, unpacked to `/tmp/chromium` with Vulkan SwiftShader `/tmp/sparticuz_libs/swiftshader/libvk_swiftshader.so`) connected strictly to local Vite dev server `http://127.0.0.1:<ephemeral_port>/tools/monarch-cockroach/long_v6/page_long_v6.html`:
    1. **Pre-Flight Tab (`?w=1920&h=1080`):** Exported `36` native `1920×1080` RGBA typography/gauge/end-card PNGs, rendered the Hero `1920×1080` YouTube Thumbnail (`f=352` bespoke framing), and rendered `16` full-HD dramatic storyboard stills across all 7 chapters (`Pass 1` and `Pass 2`).
    2. **Parallel Render Worker Tabs (`?w=1280&h=720`, `2` workers `W0` & `W1`):** Streamed `9,008` raw RGBA WebGL2 beauty frames (`3,686,400` bytes/frame) over binary loopback WebSocket (`ws://127.0.0.1:<ws_port>/?w=0|1`) into `31` FFmpeg `CRF 12` `vflip` chunk encoders (`plate_000.mp4` .. `plate_030.mp4`).

### 1.2 Google Drive Connector Access (`list_connector_tools` + `call_connector_tool`)
1. **Root Folder Inspected:** `04 - Proof & Videos` (`1Olz2fw9CrJ61SsfroJo3vYp8WbCX5CH5`) via `google_drive:list_files`.
2. **Source Folder Inspected & Staged From:** `Long Video (16x9 Feature)` (`10fv6L6iG5cPkRhWaUQhrzR4XnL65FnSW`) via `google_drive:list_files` and `google_drive:download_file` into `/tmp/v6_long/` (never left inside Git):
   - **`Monarch-Cam-03-Long-Video-Dry-Voiceover-Master-V5.wav`** (`17ovc7uAtrySzivTOiqiRr9YcUnv4LM-Y`, `48,000 Hz`, `24-bit` stereo, `300.267s` = `14,412,800` samples; originally synthesized with Arena `generate_speech` `voice-02` masculine `en-US` narration with **`0.00%` VO time-stretch** and narrative pauses surgically tightened to `<= 0.48s`).
   - **4 Physical SFX Reels (`VID_20261113_012128_753.mp4`, `VID_20261113_012137_703.mp4`, `VID_20261113_012154_590.mp4`, `VID_20261113_012158_998.mp4`):** Extracted to `48 kHz` WAV stems (`/tmp/v6_long/sfx_raw_*.wav`) for tactile wood/chitin/click layering alongside procedural Dolby DSP synthesis.
3. **Reference Folder Inspected:** `Monarch-Cam-03-Short-V6-IMAX` (`1c_e5d_0F4q9Gg4CwJu_ZYsYpkpAsFm2s`) to mirror naming & deliverable packaging 1-to-1.
4. **Output Folder Created & Populated:** `Monarch-Cam-03-Long-V6-IMAX` (`1WvZffJGkfT8jv9foY1Suk_4kBPZUwPl6`) via `google_drive:create_file` + `10` verified `google_drive:upload_file` calls (`0` errors).

### 1.3 Repository Files Read & Audited (`/home/user/Top1`)
Before writing or refactoring V6 Long code, the following exact repository files were read via `read_file` to guarantee `100%` contract compatibility and zero regressions:
- `AGENTS.md`, `CLAUDE.md`, `docs/Master-3D-Animation-Video-Production-Prompt-V6-IMAX.md`
- `tools/monarch-v6-imax-sdk/bootstrap_v6_runtime.sh`
- `tools/monarch-v6-imax-sdk/index.js`
- `tools/monarch-v6-imax-sdk/core/postfx_imax_sdk.js`
- `tools/monarch-v6-imax-sdk/core/vfx_physics_sdk.js`
- `tools/monarch-v6-imax-sdk/core/sculpt_ik_rig_sdk.js`
- `tools/monarch-v6-imax-sdk/python/forensic_qa_sdk.py`
- `tools/monarch-cockroach/v4/cockroach3d_v4.js` (`lines 1–340`: verified `roachHero.update` takes `phase` in cycles, not radians, and returns `{ landmarks }`; verified `xrayRig.update` `showPlaten` flag)
- `tools/monarch-cockroach/v4/assets/{homeowner,researcher,athlete}.glb` (parsed GLTF binary headers in Python to extract exact `mixamorig:Hips`, `LeftShoulder`, `RightShoulder`, `LeftArm`, `RightArm`, `LeftForeArm`, `RightForeArm` rest quaternions!)
- `tools/monarch-cockroach/v5/materials_v5.js` (verified `SHARED_LIGHT_UNIFORMS` keys)
- `tools/monarch-cockroach/v5/world_v5.js` (`lines 1–601`: verified `updateShadowMap` texel-snapping & group names)
- `tools/monarch-cockroach/v5/humans3d_v5.js` (`lines 115–213`: diagnosed why `rz` caused horizontal T-pose arms in V4/V5)
- `tools/monarch-cockroach/v5/director_v5.js` (`lines 1–1102` complete: verified all 32 base shots, exact cut frames, and landmark keys)
- `tools/monarch-cockroach/v5/titles_v5.js` (`lines 1–150`: verified `Jayaram & Full 2016` ceiling-drag vs floor-grit numbers)

### 1.4 `/tmp` Runtime Stack Bootstrapped (`tools/monarch-v6-imax-sdk/bootstrap_v6_runtime.sh`)
- **Node Packages (`/tmp/v6_runtime`):** `three@0.160.0`, `vite@5.4.11`, `playwright-core@1.49.0`, `@sparticuz/chromium@133.0.0`, `@fontsource/space-grotesk`, `@fontsource/ibm-plex-mono`.
- **Python Packages (`/tmp/py`):** `numpy`, `scipy`, `soundfile`, `Pillow` (with native Brotli `.woff2` FreeType support), `imageio-ffmpeg` (bundled static `ffmpeg` binary), `pytest`.
- **Critical Fresh-Container Fix Applied to `bootstrap_v6_runtime.sh`:** Outside AWS Lambda (`AWS_LAMBDA_JS_RUNTIME` unset), `@sparticuz/chromium` `133.0.0` skips unpacking `al2023.tar.br` (`libnss3.so`), and extracting `swiftshader.tar.br` overwrites `vk_swiftshader_icd.json` with a relative `./libvk_swiftshader.so` path. We patched `bootstrap_v6_runtime.sh` to explicitly decompress `al2023.tar.br`, `swiftshader.tar.br`, and `fonts.tar.br` via Node `zlib.brotliDecompressSync` into `/tmp/sparticuz_libs/*` FIRST, and write the absolute `/tmp/sparticuz_libs/swiftshader/libvk_swiftshader.so` ICD JSON AFTER extraction.

---

## 2. Primary Scientific Grounding (`Jayaram & Full, 2016, PNAS` — `PMC4776529`)

Every single visual, animation, gauge bar, and narration line in the 5-minute documentary is locked to exact measurements from **Kaushik Jayaram & Robert J. Full (2016), UC Berkeley Poly-PEDAL Laboratory**:
1. **Species & Free-Standing Dimensions:** *Periplaneta americana* — `12.5 mm` (`~0.5 in`) free-standing height, `31.1 mm` body length.
2. **Crevice Clearance Scale:** `3.20 mm` closed doorway gap vs `2` stacked US pennies (`2 × 1.52 mm = 3.04 mm`).
3. **500 FPS Traversal (`288–821 ms`):** `5` distinct biomechanical moves:
   - Move 1: Antennae sweep & probe the slot
   - Move 2: Head tips downward & wedges in
   - Move 3: Pronotum shield rolls slightly (`~11°`) to slip inside
   - Move 4: Planted external hind legs shove the thickest thoracic section through
   - Move 5: Flattened abdomen clears & shell rebounds immediately (`41–57%` vertical compression absorbed by accordion *arthrodial* membrane folds while rigid dorsal *tergite* chord lengths stay constant).
4. **104 Confined Corridor Trials (`15 cm` tunnel):**
   - `12 mm` open -> `9 mm` -> `6 mm` roof (half standing height): **near-full sprint holds at `58.1 cm/s` (`6 mm`: `57.9 cm/s`)** with `61.1 ms` (`~16.37 Hz`) alternating tripod stride beat; legs splay from `55°` to `75°` while foot track stays `~11.9 mm` from midline.
   - **`4.0 mm` Body-Compression Cliff:** Just `2 mm` lower squeezes the shell, collapsing alternating tripod coordination and **crashing speed `4×` to `14.5 cm/s`**.
5. **Tibial Crampon Takeover (`>80°` Leg Splay):**
   - Under `4.0 mm` roof, femora splay past `80°`, tipping distal hooked claws (*ungues*) and *arolium* pad sideways **`+0.47 mm` off normal floor engagement** (demonstrated via the `>80°` wide-arm human push-up collapse analogy).
   - Passive tibial crampon spines engage the floor; middle legs row synchronously like oars generating **`~38 mN` (`~5×` body weight) thrust per leg**.
6. **Footless Shear & `638` Surface-Roughness Runs:**
   - Excised-tarsi friction tests confirm tibial spines lock in alone (`μ = 1.73–2.04`).
   - **Ceiling Roughness:** Rougher roofs **always slow traversal** (`6.64 -> 5.63 -> 0.36 cm/s` as dorsal shell drag rises).
   - **Floor Grit Trade-Off (`4 mm`):** Medium `40-grit` wins (`5.26 cm/s`); `100-grit` slick slips spines (`1.57 cm/s`); coarse `20-grit` snags flattened ventral belly (`3.69 cm/s`).
7. **Hydraulic Load Cell & `315` Crevice Gate Trials:**
   - Survives up to **`~900×` body weight (`6.08 N` distributed across `~3 cm²` down to a `2 mm` stop)** and sprints away unimpaired at **`76.7 cm/s`**.
   - Across `315` gate attempts: `72%` pass at `5.8 mm`, dropping to **`17%` pass at `3.2 mm`** (`83%` fail: **`74%` turn back** after antennal check, **`9%` wedge at the thorax**).
8. **Bio-Inspired Soft Robotics (`CRAM`):**
   - Compressible Robot with Articulated Mechanisms (`75 mm -> 35 mm` laser-cut origami shell + spiny splayed legs) crawls under confinement at `~50%` open speed.

---

## 3. Complete Chapter-by-Chapter & Shot-by-Shot Storyboard Architecture (`9,008` Frames)

All `35` hard camera-cut frames are locked in `SHOT_CUTS_LONG_V6` (`director_long_v6.js` & `test_long_v6.py`) so `180°`-shutter velocity blur (`uMotionVec`) is **strictly zeroed on every cut**:

| Chapter | Frame Range | Shot Cuts (`f`) | Visual Set, Camera Choreography, Physics & V6 IMAX VFX |
|---|---|---|---|
| **Ch 01: Under the Door** | `0 .. 921` (`00:00–00:30.7`) | `0, 145, 214, 330, 538` *(Note: `0->145` is a continuous single-take whip-crane across switch snap `f=29`!)* | `2:14 AM` volumetric silver-blue moonlight (`[0..28]`, homeowner ergonomic chest-height reach) -> `f=29` switch SNAP, warm `3000K` tungsten doorway light-blade + `130` pinpoint Tyndall motes, `-3.4°` Dutch-banked whip-boom dive onto sprinting cockroach -> `[145..214]` `12.5 mm` standing profile -> `[214..330]` `2` stacked copper pennies (`3.04 mm`) -> **`[330..538]` PROTECTED CLIMAX #1** (zero text, sympathetic penny micro-tremor + `96`-particle Newtonian oak-dust burst) -> `[538..921]` `"Wait a second."` `-107 dBFS` audio vacuum + Hitchcock Vertigo counter-zoom (`+4.2°` FOV) bullet-time orbit! |
| **Ch 02: Five Moves Through the Slot** | `921 .. 2288` (`00:30.7–01:16.3`) | `921, 1224, 1819` | `[921..1224]` UC Berkeley Poly-PEDAL Lab wide crane (quaternion-solved researcher hands over optical bench & oscilloscope + `4` surgical overhead volumetric cones) -> `[1224..1819]` `500 fps` macro slot sequence (`Moves 1–5` continuous forward progression + Move 4 ballistic silicon-carbide sparks) -> `[1819..2288]` **3D Holographic Cyan Laser Tomography Curtain (`[1819..1898]`)** + surgical 3D X-Ray cutaway showing constant-chord roof-tile *tergites* & accordion cyan *arthrodial* hinges under clean acrylic ceiling! |
| **Ch 03: The Low-Ceiling Surprise** | `2288 .. 3607` (`01:16.3–02:00.2`) | `2288, 2592, 2986, 3287` | Continuous `1.88 m` confined acrylic corridor sprint stepping roof `12 -> 9 -> 6 mm` at `~58.1 cm/s` (`[2961..3020]` `"It didn't."` Vertigo punch-in + dorsal `55°->75°` splay view) -> `[3287..3607]` **3-Lane Side-by-Side Race Arena (`12 mm` vs `6 mm` vs `4 mm`)** with radial cyan shockwave ring at `f=3294` + live 3-bar speed gauge (`58.1` vs `57.9` vs `14.5 cm/s`)! |
| **Ch 04: When Shins Become Feet** | `3607 .. 5312` (`02:00.2–02:57.1`) | `3607, 3883, 4138, 4350, 4481, 4923, 5097` | `[3607..4138]` Open-stance hooked claws & pale *arolium* pad tracking dolly -> `[4138..4350]` `4.0 mm` squeeze (`>80°` splay) with **Emerald Optical Floor-Clearance Laser Grid** proving claws sit `+0.47 mm` off the floor -> `[4350..4481]` **Biomechanical Match-Cut to 3D Human Athlete Push-Up Collapse** (`f=4418` Newtonian restitution bounce + `1.25 m` amber shockwave ring + live Ground Reaction Force arrows tilting from green vertical lift to amber lateral shear) -> `[4481..4662]` match-cut back to spiny tibia -> **`[4662..4923]` PROTECTED CLIMAX #2** (razor-sharp ultra-macro crampon strike + parabolic golden sparks, zero text) -> `[4923..5312]` synchronous middle-leg oar stroke (`~5×` BW thrust)! |
| **Ch 05: The Rough-Floor Trap** | `5312 .. 6591` (`02:57.1–03:39.7`) | `5312, 5620, 5864, 6223` | `[5312..5620]` Footless shear traction rig (`μ = 1.73–2.04`) -> `[5620..5864]` `100 / 40 / 20` silicon-carbide grit swatches -> `[5864..6223]` `638` confined runs showing rougher roofs slow speed (`6.64 -> 5.63 -> 0.36 cm/s`) -> `[6223..6591]` 3-lane floor-grit race (`40-grit` wins at `5.26 cm/s` vs `100-grit` `1.57` slip & `20-grit` `3.69` belly snag at `f=6415`) + live 3-bar gauge! |
| **Ch 06: Tough Shell, Tight Limit** | `6591 .. 8032` (`03:39.7–04:27.7`) | `6591, 6877, 7183, 7519, 7891` | `[6591..6877]` **`~900×` Body-Weight (`6.08 N`) Hydraulic Load-Cell Platen Slam (`f=6785`)** with golden force arrows, expanding golden shockwave ring, & live `0.00 -> 6.08 N (~896x BW)` telemetry -> `[6877..7183]` **`76.7 cm/s` Post-Load Sprint** (`-1.6°` Dutch tilt + `-0.0045` speed streak) -> `[7183..8032]` `315` gate trials (`72% -> 17%` pass; `74%` antennal turn-back + `9%` thorax wedge jam at `f=7948` with coral shockwave + 3-bar gauge)! |
| **Ch 07: Hinges, Spines & Soft Robots** | `8032 .. 9008` (`04:27.7–05:00.27`) | `8032, 8143, 8212, 8502, 8692, 8922, 8956` | `[8032..8143]` `1×` Real-Speed Reprise setup -> **`[8143..8502]` PROTECTED CLIMAX #3** (real-speed sub-second doorway vanish + viscoelastic rebound, zero text) -> `[8502..8692]` biomechanical synthesis -> `[8692..8922]` **UC Berkeley CRAM Origami Robot (`75 -> 35 mm`) crawling side-by-side with cockroach** -> **`[8922..8956]` PROTECTED CLOSING HOLD** on glowing two-penny doorway -> `[8956..9008]` **Frosted-Obsidian `Jayaram & Full (2016) PNAS` End Card** over creamy Vogel bokeh! |

---

## 4. Audio DSP Engineering (`tools/monarch-cockroach/long_v6/build_audio_long_v6.py`)

1. **Zero VO Time-Stretch:** `time_stretch_applied = False` (`0.00%` speed or pitch alteration on all spoken words).
2. **Multi-Stem Dolby Cinema Architecture (`48,000 Hz`, `24-bit`):**
   - **Clean Vocal Pocket (`220 Hz – 4 kHz`):** Sub-bass braaams and room drones are low-passed `< 190 Hz` so narration intelligibility stays razor-clear.
   - **Pre-Twist Digital Vacuum Drop (`[17.85s .. 18.08s]`, right before `f=538` `"Wait a second."`):** Complete acoustic mute across music/ambience/SFX stems (`-180.0 dBFS` pre-mux WAV; **`-107.28 dBFS`** verified inside final muxed AAC MP4!).
   - **14 Frame-Locked Physical Transients:** Light-switch snap (`f=29`), chitinous doorway shove (`f=374`), `500 fps` chronometer ticks + laser hum (`f=1819`), `4.0 mm` speed cliff sub-drop (`f=3294`), human force-plate slam (`f=4418`), crampon silicon-carbide micro-rasps (`[4662..4923]`), `~900×` hydraulic press impact (`f=6785`), and thorax wedge thud (`f=7948`).
   - **Look-Ahead Sidechain Ducking (`55 ms` look-ahead) + Two-Pass EBU R128 Mastering + Post-AAC True-Peak Protection:**
     - During muxing (`assemble_master_long_v6.py`), lossy `AAC 256k` psychoacoustic Gibbs overshoot was prevented via `-af "alimiter=limit=0.708:level=false"`, yielding verified muxed MP4 loudness of **`-14.6 LUFS`** and post-AAC True Peak of **`-1.1 dBFS`**.

---

## 5. Five Real Bugs Caught & Solved During Our 2-Pass Pre-Flight & Forensic Gates

1. **Mixamo `.glb` Human T-Pose / Horizontal Salute Bug (`Panel 1` & `Panel 6` in Pre-Flight Pass 1):**
   - *Cause:* Inspecting the raw quaternions inside `homeowner.glb` and `researcher.glb` revealed `LeftShoulder = [0.524, 0.464, -0.573, 0.426]` and `Hips = [0, 0.7071, 0, 0.7071]`. Under that rest basis, rotating `LeftArm`/`RightArm` around `rz` swings arms **horizontally (`world ±X`)** at shoulder height!
   - *Exact Quaternion Fix (`director_long_v6.js` `poseHomeownerV6` & `poseResearcherV6`):* Rotating `rx = +1.18 .. +1.26` drops both upper arms straight down along the ribcage (`world Y = -0.97`), while `LeftForeArm rz = +0.92` and `RightForeArm rz = -0.95` bend both elbows cleanly forward (`actor +X`) onto the optical lab bench and chest-height light switch.
2. **Macro Tracking Shutter-Blur Smear (`Panel 12` `f=4780` Climax #2 in Pre-Flight Pass 1):**
   - *Cause:* `createCinemaCameraRig` originally computed `combined = 0.55 * dPos + 0.45 * dLook`, smearing a tightly tracked hero (`focusDist ~ 14 mm`) even when the camera moved at the exact velocity of the cockroach (`dPos == dLook`).
   - *Exact Optical Fix (`sculpt_ik_rig_sdk.js`):* Changed camera shutter velocity to **angular lens pan `(dLook - dPos) / max(14.0, focusDist)`** — keeping pure tracking dollies **100% razor-sharp** on tibial crampon spines & ballistic sparks while preserving genuine whip-pan blur on camera whips!
3. **Near-Lens Dust Disc & Hydraulic Shaft Photobomb (`Panels 4, 7, 8` & `Thumbnail`):**
   - *Fix:* Reduced Tyndall dust mote radius (`0.155 -> 0.046 mm`) and clamped `z` behind the macro focal corridor; set `showPlaten: false` in `Ch 02D` (`[1819..2288]`) with clean crystal acrylic ceiling, reserving the steel hydraulic press column exclusively for `Ch 06A` (`~900×` body weight); framed `Thumbnail` (`f=352`) with copper pennies cleanly at `(-10.5, 0, 15.8)` free of leg overlap.
4. **SwiftShader Bokeh `sin`/`cos`/`sqrt` Bottleneck & Shadow-Pass Volumetric Leak:**
   - *Fix (`postfx_imax_sdk.js` & `director_long_v6.js`):* Precomputed compile-time `VOGEL_8` Golden-Angle bokeh offsets (eliminating `>10.1M` transcendental evaluations/frame in SwiftShader) and hid all additive volumetric cones before `updateShadowMap(...)` so volumetrics never cast opaque depth shadows. Added `--max-chunks` resumable batching to `render_long_v6.mjs`.
5. **Container RAM & File-Size Ceiling (`assemble_master_long_v6.py` & `forensic_qa_sdk.py`):**
   - *Fix:* Upgraded `verify_imax_mp4` to `O(1)`-memory streaming `subprocess.Popen` (`< 6 MB` RAM across `9,008` frames instead of `2.8 GB`), and tuned `libx264 -crf 18 -maxrate 2120k -bufsize 4400k` so the final `5m 00.27s` `1920×1080` MP4 lands at **`90.10 MB`** (`< 100 MB` Google Drive API limit) with zero visual loss.

---

## 6. Verified Deliverables & Cloud IDs (`Google Drive` + `Git`)

- **Git Commit on `Top1`:** `tools/monarch-cockroach/long_v6/*` + `tools/monarch-v6-imax-sdk/*`
- **Google Drive Folder (`Monarch-Cam-03-Long-V6-IMAX`):** `1WvZffJGkfT8jv9foY1Suk_4kBPZUwPl6`
  - `Monarch-Cam-03-Long-Video-Master-V6-IMAX.mp4`: `1ulSjxLfiA3lfGMeZ5G4rLRvaosD7Pwtd` (`90,096,186` bytes; duplicate also in `Long Video (16x9 Feature)` as `1dNAnJTbNw2HCgp3AD9pfx8P14W_lAB6I`)
  - `Monarch-Cam-03-Long-Video-Thumbnail-V6-IMAX.png`: `1ruwPSJRt0LYwMr5DYvVy1gyY43sKVc7U`
  - `Monarch-Cam-03-Long-Video-16Beat-QA-Sheet-V6-IMAX.jpg`: `11y9d0qd-uP1B4dFOzvsTLxM74xDxcjEe`
  - `Monarch-Cam-03-Long-Video-Master-Mix-V6-IMAX.wav`: `1jXqIh5JorogDTWyIbb931oQ81TlrYt3f`
  - `Monarch-Cam-03-Long-Video-Dry-Voiceover-Master-V6-IMAX.wav`: `1dfN4FmzaSegqsB6YIV5ejCPecnz7WF7Z`
  - `Monarch-Cam-03-Long-Video-Captions-V6-IMAX.srt`: `1ABUK5-CVfEvd9t-trWP5vZ-p8ICBG6G0`
  - `Monarch-Cam-03-Long-Video-Captions-V6-IMAX.vtt`: `18ptaf0QPYGub5trsxLIi28ZV3AXokeDU`
  - `Monarch-Cam-03-Long-Video-Launch-Copy-V6-IMAX.md`: `1ym0W5R4fOg6g46ZCS9kBXi97Ezy5D0GT`
  - `Monarch-Cam-03-Long-Video-Forensic-QA-Receipt-V6-IMAX.json`: `1sOKQvE_5YaNFq6C2SOYTAggFGumbu1XM`
