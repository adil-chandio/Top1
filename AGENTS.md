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

## 2. MANDATORY ENGINE — ALWAYS BUILD ON `tools/monarch-v6-imax-sdk/`

Every new 3D video (`9:16` Viral Short or `16:9` Long Documentary) MUST be built directly on top of **`tools/monarch-v6-imax-sdk/`** and match or exceed the **Gold-Standard Reference Productions** in **`tools/monarch-cockroach/short_v6/`** (`V6 Hollywood IMAX Short`) and **`tools/monarch-cockroach/v5/`** (`V5 Broadcast Long Documentary`):

1. **Step 1 — Bootstrap GPU + DSP Runtime (`/tmp/`):**
   ```bash
   bash tools/monarch-v6-imax-sdk/bootstrap_v6_runtime.sh
   ```
   This sets up WebGL2 + SwiftShader Vulkan (`/tmp/chromium` + absolute `vk_swiftshader_icd.json` + `/tmp/lib*.so` symlinks), `three`, `vite`, `playwright-core`, `Space Grotesk` & `IBM Plex Mono` `.woff2` fonts, and Python `numpy`/`scipy`/`soundfile`/`Pillow`/`pytest`/`imageio-ffmpeg` in `/tmp/` (`7.5+ fps` GPU rendering while keeping persistent workspace size `< 128 MiB`).

2. **Step 2 — Import the Battle-Tested V6 IMAX SDK (`tools/monarch-v6-imax-sdk/index.js`):**
   Do **NOT** waste your code/token budget rewriting shaders, post-FX, font loaders, or WebSocket renderers from scratch! Import them directly from `/tools/monarch-v6-imax-sdk/index.js` and spend **100% of your custom engineering budget** on **bespoke high-poly parametric 3D sculpting, anatomical/mechanical X-ray cutaways, Newtonian physics choreography, rich multi-set environments, and multi-pass visual polish**:
   - **GLSL PBR + Sobel Normal Maps + `30 Hz` Texel-Snapped Shadows:** `makeImaxMaterial`, `setImaxLightingPreset`, `createTexelSnappedShadowRig`, `buildNormalFromCanvas`, `buildOpticalBreadboardTexture`, `buildWoodPlankTexture`, `buildStoneGritTexture`, `buildMetricRulerTexture`
   - **True Linear-Light ACES Filmic HDR Post-FX:** `createImaxOpticalPass` (Panavision `2.35×` horizontal anamorphic bloom, `12`-tap Golden-Angle Vogel bokeh DoF, peripheral chromatic dispersion, `7`-tap `180°`-shutter velocity motion blur, Kodak 2383 split-tone grade, Narkowicz ACES Filmic tone mapping + `35mm` fine grain)
   - **3D Volumetric Lighting, Lasers & Newtonian VFX:** `createVolumetricLightBlade`, `createVolumetricSpotlightCone`, `createLoopLockedDustMotes`, `createLaserTomographyScanner`, `createClearanceLaserGrid`, `createImpactShockwaveRing`, `createBallisticParticleSystem`
   - **High-Poly Sculpting, 2-Bone IK, `.glb` Humans & Cinema Camera Rig:** `GLM`, `buildLoftGeometry`, `createGroundContactAO`, `BUILTIN_HUMAN_GLBS`, `loadRiggedHumanActor`, `createCinemaCameraRig`
   - **Verified Binary WOFF2 Fonts, Tofu Guard & GPU HUD:** `assertSafeLatinGlyphs`, `loadVerifiedCinemaFonts`, `createGpuHudCompositor`, `drawImaxShortHud`
   - **Universal Parallel Raw-RGBA WebSocket Renderer (`7.5+ fps`):** `tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs`
   - **Dolby Sub-Braaam + Pre-Twist Vacuum Drop + Zero-Stretch Audio DSP & EBU R128 Mastering:** `tools/monarch-v6-imax-sdk/python/audio_imax_dsp.py`
   - **Decoded-MP4 Forensic Validator:** `tools/monarch-v6-imax-sdk/python/forensic_qa_sdk.py`

---

## 3. NON-NEGOTIABLE HOLLYWOOD IMAX PRODUCTION LAWS

1. **Zero Primitive Toy Models:** Hero organisms, machines, planets, and props MUST use sealed parametric cross-section lofting (`buildLoftGeometry`), bevelled extrusions, sculpted joint condyles, `solveTwoBoneIK`, procedural normal maps (`buildNormalFromCanvas`), `InstancedMesh` micro-structures, and translucent 3D X-Ray / Sagittal Cutaway rigs.
2. **Newtonian Momentum, Inertia & Camera Physics:**
   - Subjects decelerate before obstacles, bank into turns, accelerate through power strokes, obey `y = v0*t - 0.5*g*t²` with restitution floor bounce (`e ~ 0.38`) on drops/debris, snap back elastically on load release, and trigger sympathetic micro-tremors on nearby props.
   - Use `createCinemaCameraRig` for critically-damped impact shake, Vertigo dolly-zoom on paradox beats, Dutch roll banking, and `180°`-shutter velocity motion blur (**strictly zeroed across `shotCuts`**, with `evaluateFrame(fStart - 1)` warm-up at the start of every worker chunk).
3. **`9:16` Portrait FOV Trigonometry Guard:**
   - In Three.js, `camera.fov` is vertical (`fovY`). At `aspect = 9/16 = 0.5625`, horizontal width is `GLM.visibleHorizontalWidth(dist, fovYDeg, 9/16)` (`fovY = 38° -> fovX = 22.0°`!). Always verify full subject width fits inside left/right margins and offset bright background lab lamps/props off the center axis so nothing clips or photobombs!
4. **The 5 Ironclad Zero-Flicker Laws:**
   - **Law 1:** Zero coplanar surfaces (separate stacked planes by `>= 0.2–1.8` units + `polygonOffset` on base floors).
   - **Law 2:** Every `transparent: true` material has `depthWrite: false`, `uReceiveShadow: 0.0`, `castShadow = false`, and explicit ascending `renderOrder` (`2` AO -> `5` internals -> `10..12` glass -> `16..18` X-ray shell -> `21..26` additive volumetrics).
   - **Law 3:** Update `createTexelSnappedShadowRig` **every single frame (`30 Hz`, never `15 Hz`)**.
   - **Law 4:** Bracket `camera.near` and `camera.far` dynamically to `focusDist`.
   - **Law 5:** Never oscillate at `15.0 Hz` (`30 fps` Nyquist) and never teleport positions with `%` modulo.
5. **Zero VO Time-Stretch + Dolby Trailer Sound:**
   - `time_stretch_applied = False` (`1.000x` natural speech speed/pitch).
   - Layer `< 190 Hz` cinema sub-braaams (keeping `220 Hz–4 kHz` vocal pocket clean), a `150–200 ms` `-180 dBFS` complete digital vacuum silence right before the mid-video twist word (*"Wait."*), `8 Hz` bullet-time chronometer ticks, physical modal foley, loop-locked harmonic score, `55 ms` look-ahead ducking, and two-pass linear EBU R128 mastering (`-14.2 LUFS`, `<= -1.4 dBTP`).
6. **Mandatory 2-Pass Pre-Flight Critique BEFORE Full Render:**
   - **NEVER** trust Pre-Flight Pass 1 blindly! Render Cover PNG + `12`-Beat QA Sheet (`--mode preflight`), inspect BOTH visually via `read_file`, explicitly list every visual flaw (edge clipping, prop-limb overlap, dull lighting, scale mismatch, HUD placement), fix them in code, re-run Pre-Flight Pass 2 to confirm perfection, and **only then** run `--mode render` + `verify_imax_mp4(...)` (`pytest`).
7. **Git & Workspace Snapshot Hygiene (`< 128 MiB`):**
   - Keep intermediate WAV/video chunks in `/tmp/`, write final deliverables to `exports/<project-slug>/` (gitignored so heavy `.mp4` files never bloat Git commits), keep persistent workspace untracked files `< 126 MiB`, upload deliverables to Google Drive when requested, and present the final `.mp4` via `present_file`.
