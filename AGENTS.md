# Top1 Repository — Autonomous 3D Cinema Studio (`V6 HOLLYWOOD IMAX` Standard)

> **MANDATORY REPOSITORY CONSTITUTION FOR ALL CODING AGENTS:** Read and obey every rule in this file BEFORE exploring, planning, or writing code for any 3D video, animation, Short, or documentary task in `Top1`.

---

## 1. STRICT DEPRECATION BAN — NEVER COPY LEGACY FOLDERS!

The following older folders in `tools/` are **DEPRECATED V1–V3 PROTOTYPES**:
- `tools/extinct-life/` ❌ *(uses slow `0.6 fps` screenshot loops & basic materials — DO NOT COPY OR RUN)*
- `tools/monarchs-edit/` ❌ *(legacy draft pipeline — DO NOT COPY)*
- `tools/monarch-ant/`, `tools/monarch-ant-v2/`, `tools/monarch-ant-v3/` ❌ *(pre-V6 prototypes — DO NOT COPY)*
- `tools/gecko/`, `tools/demo-render/` ❌ *(legacy demos — DO NOT COPY)*

**NEVER** copy `render.mjs`, `MeshStandardMaterial` setups, primitive `BoxGeometry`/`SphereGeometry`/`CylinderGeometry` hero actors, or CSS `@font-face` patterns from those legacy folders.

---

## 2. MANDATORY CREATIVE BRAIN (`tools/director-producer-os/`) + ENGINE (`tools/monarch-v6-imax-sdk/`)

Every new 3D video (`9:16` Viral Short or `16:9` Long Documentary) MUST pass **Gate 0.5 — Creative Producer & Film Director Pre-Production Lock (`tools/director-producer-os/`)** BEFORE writing any Three.js scene code, and build on **`tools/monarch-v6-imax-sdk/`** + **`docs/v6-imax-production-bible/`**:
- **`tools/director-producer-os/SKILL.md`** & **`docs/v6-imax-production-bible/03-Master-Production-Director-And-Creative-Producer-Bible.md`** *(Master 5-Hat Producer/Director Brain, Anti-Clone Law, Bruce Block Visual Arc, Roger Deakins Optics, Walter Murch Editing & Villeneuve Silence)*
- **`docs/v6-imax-production-bible/01-Monarch-Cam-03-Long-V6-Complete-Forensic-Case-Study.md`** *(A-to-Z forensic trace of our 5-minute `9,008`-frame Long V6 IMAX feature)*
- **`docs/v6-imax-production-bible/02-Universal-Any-Topic-V6.2-Hollywood-IMAX-Master-Playbook.md`** *(Universal 7-Gate SOP & Starter Prompt for ANY topic)*
- **Gold-Standard `9:16` Short Reference:** **`tools/monarch-cockroach/short_v6/`** (`1080×1920`, `1,050` frames, infinite loop)
- **Gold-Standard `16:9` Long Documentary Reference:** **`tools/monarch-cockroach/long_v6/`** (`1920×1080`, `9,008` frames, 7 chapters, 35 shot cuts, hybrid `2×` WOFF2 HUD compositor)

0. **Step 0 — Mandatory Pre-Production Director Plan & Anti-Clone Gate (`0` Errors Required!):**
   - **NEVER copy a single theme, dark-pedestal turntable, obsidian/teal/amber palette, or HUD layout across consecutive videos!**
   - Inspect `tools/director-producer-os/catalog/production_fingerprints.json` and `world_archetypes.json` (`W01`–`W24` + `H0`–`H5`), author `projects/<slug>/director-plan.json` conforming to `tools/director-producer-os/schemas/director-plan.schema.json`, and pass all **32 deterministic cinema, optical, `180°`/`30°`, Eye-Trace, Bruce Block, and Anti-Clone (`>= 65%` divergence) checks**:
     ```bash
     python3 tools/director-producer-os/validators/director_linter.py projects/<slug>/director-plan.json
     ```
   - After Gate 6 passes on a finished video, register its fingerprint via `python3 tools/director-producer-os/validators/register_fingerprint.py projects/<slug>/director-plan.json`.

1. **Step 1 — Bootstrap GPU + DSP Runtime (`/tmp/`):**
   ```bash
   bash tools/monarch-v6-imax-sdk/bootstrap_v6_runtime.sh
   ```
   This explicitly decompresses `@sparticuz/chromium` `133.0.0` Brotli archives (`al2023.tar.br`, `swiftshader.tar.br`, `fonts.tar.br`) into `/tmp/sparticuz_libs/*`, writes the absolute `/tmp/sparticuz_libs/swiftshader/libvk_swiftshader.so` into `vk_swiftshader_icd.json`, and installs `three`, `vite`, `playwright-core`, `Space Grotesk` & `IBM Plex Mono` `.woff2` fonts, and Python `numpy`/`scipy`/`soundfile`/`Pillow`/`pytest`/`imageio-ffmpeg` in `/tmp/` while keeping persistent workspace size `< 128 MiB`.

2. **Step 2 — Import the Battle-Tested V6 IMAX SDK (`tools/monarch-v6-imax-sdk/index.js`):**
   Do **NOT** waste your code/token budget rewriting shaders, post-FX, font loaders, or WebSocket renderers from scratch! Import them directly from `/tools/monarch-v6-imax-sdk/index.js` and spend **100% of your custom engineering budget** on **bespoke high-poly parametric 3D sculpting, anatomical/mechanical X-ray cutaways, Newtonian physics choreography, rich multi-set environments, and multi-pass visual polish**:
   - **GLSL PBR + Sobel Normal Maps + `30 Hz` Texel-Snapped Shadows:** `makeImaxMaterial`, `setImaxLightingPreset`, `createTexelSnappedShadowRig`, `buildNormalFromCanvas`, `buildOpticalBreadboardTexture`, `buildWoodPlankTexture`, `buildStoneGritTexture`, `buildMetricRulerTexture`
   - **True Linear-Light ACES Filmic HDR Post-FX:** `createImaxOpticalPass` (Panavision `2.35×` horizontal anamorphic bloom, `12`-tap Golden-Angle Vogel bokeh DoF, peripheral chromatic dispersion, `7`-tap `180°`-shutter velocity motion blur, Kodak 2383 split-tone grade, Narkowicz ACES Filmic tone mapping + `35mm` fine grain)
   - **3D Volumetric Lighting, Lasers & Newtonian VFX:** `createVolumetricLightBlade`, `createVolumetricSpotlightCone`, `createLoopLockedDustMotes`, `createLaserTomographyScanner`, `createClearanceLaserGrid`, `createImpactShockwaveRing`, `createBallisticParticleSystem`
   - **High-Poly Sculpting, 2-Bone IK, `.glb` Humans & Cinema Camera Rig:** `GLM`, `buildLoftGeometry`, `createGroundContactAO`, `BUILTIN_HUMAN_GLBS`, `loadRiggedHumanActor`, `createCinemaCameraRig`
   - **Director Optics, Kelvin Blackbody & Continuity Math:** `lensMmToThreeFovY`, `computeCinemaFraming`, `distanceForSubjectWidth`, `applyShotOpticsToCamera`, `kelvinToSrgb01`, `parseContrastRatio`, `check180AxisSide`, `compute30DegreeSeparation`, `projectNormalizedEyeTrace`
   - **V7 Living Biomechanics, Secondary Motion & Retention Easing (`tools/monarch-v6-imax-sdk/js/monarch_ultra_rig_v7.js`):** `snapGlide`, `recoilSpring`, `evaluateSpineWave`, `evaluateQuadrupedStep`, `evaluateBlinkCurve`, `evaluateBreathingWave`, `evaluateFlutterDisplacement`, `createDustPuffBurst`
   - **Verified Binary WOFF2 Fonts, Tofu Guard & GPU HUD:** `assertSafeLatinGlyphs`, `loadVerifiedCinemaFonts`, `createGpuHudCompositor`, `drawImaxShortHud`
   - **Universal Parallel Raw-RGBA WebSocket Renderer (`7.5+ fps`):** `tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs`
   - **V7 Broadcast Dialogue Leveler, Zero-Hiss Pink Sub-Air, Physical Foley & 4-Act Score (`tools/monarch-v6-imax-sdk/python/audio_eargasm_v7.py`):** `level_and_polish_voice_clip`, `kellet_pink_noise`, `zero_hiss_ambient_air`, `karplus_strong_pluck`, `marimba_strike`, `warm_cello_pad_note`, `shepard_riser`, `asmr_brush_sweep`, `modal_stone_fracture`, `modal_bone_click`, `crawl_footstep_grit`, `minnaert_bubble_chirp`, `strouhal_camera_whoosh`, `carve_vocal_pocket`, `lookahead_sidechain_duck`
   - **Decoded-MP4 + Post-AAC Dialogue Uniformity & Zero-Hiss Validator:** `tools/monarch-v6-imax-sdk/python/forensic_qa_sdk.py` (`verify_imax_mp4(..., line_windows=..., max_line_spread_db=3.5, max_hiss_floor_db=-55.0)`)

---

## 3. NON-NEGOTIABLE HOLLYWOOD IMAX PRODUCTION LAWS

1. **Zero Primitive Toy Models & Quaternion-Verified `.glb` Rigging:** Hero organisms, machines, planets, and props MUST use sealed parametric cross-section lofting (`buildLoftGeometry`), bevelled extrusions, sculpted joint condyles, `solveTwoBoneIK`, procedural normal maps (`buildNormalFromCanvas`), `InstancedMesh` micro-structures, and translucent 3D X-Ray / Sagittal Cutaway rigs. Before posing any `.glb` skeletal actor (`loadRiggedHumanActor`), inspect bone rest quaternions (`Shoulder`/`Hips` basis) so upper arms drop naturally along the torso (`rx = +1.18..+1.26` on Mixamo rigs, NOT `rz` horizontal T-poses!).
2. **Newtonian Momentum, Inertia & Angular-Pan Camera Physics:**
   - Subjects decelerate before obstacles, bank into turns, accelerate through power strokes, obey `y = v0*t - 0.5*g*t²` with restitution floor bounce (`e ~ 0.38`) on drops/debris, snap back elastically on load release, and trigger sympathetic micro-tremors on nearby props.
   - Use `createCinemaCameraRig` for critically-damped impact shake, Vertigo dolly-zoom on paradox beats, Dutch roll banking, and angular-pan `180°`-shutter velocity motion blur (`(dLook - dPos) / focusDist`, keeping locked tracking subjects razor-sharp while blurring whip-pans — **strictly zeroed across `shotCuts`**, with `evaluateFrame(fStart - 1)` warm-up at the start of every worker chunk).
   - Always set additive volumetric cones/blades `visible = false` prior to the `30 Hz` orthographic shadow depth pass so volumetrics never cast opaque depth shadows!
3. **`9:16` Portrait FOV Trigonometry Guard:**
   - In Three.js, `camera.fov` is vertical (`fovY`). At `aspect = 9/16 = 0.5625`, horizontal width is `GLM.visibleHorizontalWidth(dist, fovYDeg, 9/16)` (`fovY = 38° -> fovX = 22.0°`!). Always verify full subject width fits inside left/right margins and offset bright background lab lamps/props off the center axis so nothing clips or photobombs!
4. **The 5 Ironclad Zero-Flicker Laws:**
   - **Law 1:** Zero coplanar surfaces (separate stacked planes by `>= 0.2–1.8` units + `polygonOffset` on base floors).
   - **Law 2:** Every `transparent: true` material has `depthWrite: false`, `uReceiveShadow: 0.0`, `castShadow = false`, and explicit ascending `renderOrder` (`2` AO -> `5` internals -> `10..12` glass -> `16..18` X-ray shell -> `21..26` additive volumetrics).
   - **Law 3:** Update `createTexelSnappedShadowRig` **every single frame (`30 Hz`, never `15 Hz`)**.
   - **Law 4:** Bracket `camera.near` and `camera.far` dynamically to `focusDist`.
   - **Law 5:** Never oscillate at `15.0 Hz` (`30 fps` Nyquist) and never teleport positions with `%` modulo.
5. **Zero VO Time-Stretch + Dolby Trailer Sound + Post-AAC True-Peak Guard:**
   - `time_stretch_applied = False` (`1.000x` natural speech speed/pitch).
   - Layer `< 190 Hz` cinema sub-braaams (keeping `220 Hz–4 kHz` vocal pocket clean), a `150–230 ms` `-180 dBFS` complete digital vacuum silence right before the twist word (*"Wait."*), `8 Hz` bullet-time chronometer ticks, physical modal foley, loop-locked harmonic score, `55 ms` look-ahead ducking, and two-pass linear EBU R128 mastering (`-14.2 LUFS`). When muxing lossy `AAC`, apply `-af "alimiter=limit=0.708:level=false"` so psychoacoustic Gibbs overshoot never pushes post-AAC True Peak above `-1.0 dBFS`.
6. **Mandatory 2-Pass Pre-Flight Critique + Resumable `--max-chunks` Render + Decoded-MP4 Gate:**
   - **NEVER** trust Pre-Flight Pass 1 blindly! Render Cover/Thumbnail PNG + `12/16`-Beat QA Sheet (`--mode preflight`), inspect BOTH visually via `read_file`, explicitly list every visual flaw (edge clipping, T-pose bones, near-lens dust discs, motion-blur smear, HUD placement), fix them in code, re-run Pre-Flight Pass 2 to confirm perfection, and **only then** run full render (using resumable `--max-chunks` batches + `assemble_master_long_v6.py` for multi-minute `16:9` features, keeping final MP4 `< 95 MB` for direct Drive upload).
   - Run `O(1)`-RAM streaming `verify_imax_mp4(...)` (`pytest`) AND visually inspect a Decoded-MP4 Proof Sheet via `read_file` before presenting.
7. **Git & Workspace Snapshot Hygiene (`< 128 MiB`):**
   - Keep intermediate WAV/video chunks in `/tmp/`, write final deliverables to `exports/<project-slug>/` (gitignored so heavy `.mp4` files never bloat Git commits), keep persistent workspace untracked files `< 126 MiB`, upload deliverables to Google Drive when requested, and present the final `.mp4` via `present_file`.
