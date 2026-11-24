# Forensic capability audit — what this sandbox can actually deliver, and how to reach "next level"

Date: 2026-11-24 · Branch: `arena/5712b84e-top1` · **Read-only research. No video, no storyboard, no render, no audio generated.**
Every number below was measured in this environment today, or read from the repo. Nothing is assumed.

---

## 0. TL;DR — the three facts that change the whole plan

1. **Headless WebGL2 works.** ANGLE → Vulkan → SwiftShader (`WebGL 2.0 (OpenGL ES 3.0 Chromium)`, `EXT_color_buffer_half_float` = true, max texture 8192). A real cinematic stack ran end-to-end.
2. **Math/quality is affordable; pixels are not free.** Measured: no-post 32 fps, bloom+ACES 2.44 fps, DOF+bloom+ACES+CA+SMAA 0.27 fps at 720p (1080p light = 1.14 fps). **Choreography, physics, timing, camera curves cost ~nothing. Post-processing costs everything.**
3. **The current film has no body language to film.** Every creature asset ships exactly **one** animation clip named `Idle`; the three human GLBs have **zero** animations. That is the mechanical root of "static, boring, repetitive" — not the camera work.

Corollary: the "next level" is **not** more effects. It is (a) real authored performance + physics, (b) a *small* set of expensive post effects used surgically, (c) a storytelling grammar with measured pacing, (d) a high-quality audio mix that does the emotional lifting.

---

## 1. Environment — measured, not assumed

| Capability | Status | Measurement |
|---|---|---|
| Node 22.22.3, 2 vCPU, 3.9 GB RAM, 20 GB disk | ✅ | `nproc`, `free`, `df` |
| Headless Chromium 133 (Spartuz) + SwiftShader | ✅ | renderer string above; extracted to `/tmp` |
| three **r160** + postprocessing **6.37.8** (tested build; 6.39 latest on registry) | ✅ | imported, rendered, benchmarked |
| Rapier3D 0.14 (WASM physics) | ✅ | 240 rigid bodies settled to y = −4.98 on ground plane |
| troika-three-text (SDF 3D type) | ✅ | resolved via importmap (`bidi-js`, `troika-*`, `webgl-sdf-generator`) |
| **WebGPU adapter** | ⚠️ present but not chosen | `navigator.gpu` true, adapter vendor `google` (Dawn/SwiftShader). three's WebGPU backend = unproven here; do not design on it |
| FFmpeg 9.0.2 static (imageio) | ✅ | libx264/x265/vp9/opus/aac, `libplacebo`, `minterpolate`, `vidstab*`, `nlmeans`, `cas`, `lut3d`, `vmaf`, `rubberband` |
| Pedalboard 0.9.26 (JUCE DSP) | ✅ installed + tested | reverb/compressor/limiter ran on 2 s buffer |
| OpenCV 5.1 headless | ✅ installed + tested | DIS + Farneback optical flow available |
| pyloudnorm / pysubs2 / scikit-image / librosa | ✅ on PyPI | |
| **Blender `bpy`** | ❌ **impossible** | `ImportError: libXrender.so.1`; no Debian/Ubuntu repo access (`deb.debian.org` = 000). Modo alternativo: Pakerevd X libs — not available |
| **Real-ESRGAN / RIFE (ncnn binary)** | ❌ | GitHub release asset = 302 → `objects.githubusercontent.com` blocked |
| Hugging Face / jsDelivr / raw.githubusercontent | ❌ | all `000` |
| Working allowlist | ✅ | `github.com`, `api.github.com`, `codeload.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org` |

**Consequence:** every asset/dependency decision must resolve through npm or PyPI. Anything that only lives in a GitHub release zip or on Hugging Face is unavailable today.

---

## 2. Repository forensics — the real weaknesses

### 2.1 Asset inventory (GLB headers parsed, not guessed)

| Asset | Size | Animations | Skin | Joints | Vertices | Morph |
|---|---|---|---|---|---|---|
| `radiodont.glb` (Anomalocaris) | 1.81 MB | **1 (`Idle`)** | 1 | 61 | 83,743 | ❌ |
| `hallucigenia.glb` | 5.64 MB | **1 (`Idle`)** | 1 | 109 | 28,082 | ❌ |
| `opabinia.glb` | 1.44 MB | **1 (`Idle`)** | 1 | 18 | 3,008 | ❌ |
| `coast_rocks_01/03.glb`, `rock_07.glb` | 0.56–0.99 MB | 0 | 0 | 0 | 2.9k–26.7k | ❌ |
| `athlete/homeowner/researcher.glb` | 2.35–2.58 MB | **0** | 1 | 49 | 6,154 | ❌ |

So:
- **No locomotion, no feeding, no escape, no death, no flocking.** Radiodont (the hero) can only idle — a 60 s film of a 20 cm animal doing nothing is exactly what the existing critiques describe.
- **No facial rig anywhere** (no morph targets), so "expressions" cannot be produced from these assets. Any face/expression requirement needs either a new asset pipeline or performance conveyed through body/silhouette/camera — the honest choice.
- Polys are low for hero macro work (radiodont 83k verts is okay; opabinia 3k is far too low for a close-up).

### 2.2 Production code vs. the V6.2 gates (film.js)

Present: `buildLoftGeometry`, `buildNormalFromCanvas`, `createCinemaCameraRig`, `createImaxOpticalPass`, `createGpuHudCompositor`, `loadVerifiedCinemaFonts`.
**Missing:** `makeImaxMaterial`, `setImaxLightingPreset`, `createTexelSnappedShadowRig`, `volumetrics`, `laser/X-ray`, `createBallisticParticleSystem`, `solveTwoBoneIK`, `assertSafeLatinGlyphs`.
**No shadow pass at all** (`shadowMap` / `castShadow` / `receiveShadow` = 0 occurrences) ⇒ Zero-Flicker Law 3 unsatisfiable; no contact shadows ⇒ floaty, synthetic feel.
Lighting is raw `HemisphereLight` + 2 `DirectionalLight`; 3× `MeshStandardMaterial`; one `FogExp2`.
17 shots over 1,800 frames = **ASL 3.5 s** with mostly static subjects — the pacing is fine on paper but empty in content.

### 2.3 Governance gap

No `voice-lock.json`, `claims.json`, `rights.json`, `story.json`, `shot-plan.json` for Huayuan, although `tools/extinct-studio/` defines 14 schemas and a 15-state machine. The 60 s review was produced **before** an audio lock, which is why it can never be re-cut cleanly.

---

## 3. External research — what is genuinely worth importing

### 3.1 Rendering / look (npm, all compatible with three r160+)

| Package | Version | License | Verdict |
|---|---|---|---|
| `postprocessing` (pmndrs) | 6.39.6 | Zlib | **Adopt.** Effect merging, DOF, bloom, ACES, SMAA, TAA. Measured cost is the constraint, not the API. |
| `three-mesh-bvh` | 0.9.18 | MIT | **Adopt** for ray-casts, occlusion queries, fast collision against rocks, and "camera can't pass through geometry" checks. |
| `troika-three-text` | 0.53.1 | MIT | **Adopt** for crisp, resolution-independent 3D-tracked labels (replaces blurry canvas HUD at 4K). |
| `@dimforge/rapier3d-compat` | 0.21.0 | Apache-2.0 | **Adopt** for Newtonian debris, sedimentation, collapse, current drag. Deterministic and step-cheap (measured ~0 ms). |
| `three-look` | 0.1.x | MIT | Interesting (one-call cinematic preset, PCSS soft shadows, GTAO) but **1 star, unproven** → read for ideas, do not depend on it. |
| `realism-effects` (SSGI/TRAA) | — | MIT | Last push 2024, requires extra velocity pass. **Reject** at our frame budget (SSGI alone would be minutes/frame). |
| `theatre.js` | 4.x | Apache-2.0 | **Adopt selectively** as an authoring tool for camera/light keyframes; it serialises to JSON that the renderer reads. Not a runtime dependency in the film page. |
| `Tone.js` | 15.x | MIT | Useful for procedural score prototyping, but final score should be baked WAV via Pedalboard/NumPy. |

### 3.2 What can be generated procedurally (no external assets needed)

- **Micro-detail:** the SDK's `buildNormalFromCanvas` + `makeImaxMaterial` already cover this; add triplanar detail to avoid UV stretching on rocks.
- **Water/sediment:** custom shaders — cheap, no textures. Correct approach at 2 vCPU.
- **SDF/flat 3D typography:** troika (CPU SDF) — measured working.
- **Physics:** Rapier — measured working.
- **Audio:** Pedalboard + NumPy — measured working; convolution reverb from a synthetic impulse response is viable (`afir` in FFmpeg or Pedalboard's `Reverb`/`Convolution`).

### 3.3 What must NOT be promised

- Photoreal **path-traced** frames (Cycles/Octane): bpy is impossible here; three-gpu-pathtracer on SwiftShader would be minutes per frame at 320×180.
- AI **super-resolution / frame interpolation** (Real-ESRGAN, RIFE): binaries unreachable; PyTorch CPU wheel is 800 MB+ and would still be too slow, and it cannot invent correct animation.
- **Facial performance** from the current assets: no morph targets, no facial bones.
- "Hypnotic/psychologically controlling" as a factual claim. What is real and citable is *attention* research (§4). We can engineer attention; we cannot guarantee trance.

---

## 4. Storytelling & engagement — evidence, not vibes

Citable findings (all from published research, links in §7):

1. **Cut rhythm converges on human attention.** Cutting et al. (2010, *Psychological Science*) measured every shot in 150 popular films 1935–2005: shot lengths moved toward a **1/f** distribution — the same statistical structure as natural attention shifts. Practical rule: **vary shot lengths deliberately (a short-short-long pattern), never a metronome.**
2. **Shorter shots → tighter gaze convergence.** Gannon & Grubb: shorter average shot length (ASL) produced higher inter-subject attentional synchrony; after a cut, gaze is *most* variable in the first **200 ms**, then re-converges. Practical rule: put the story-critical object **where the eye lands** (motion vector / centre of contrast) immediately after a cut — not in a corner.
3. **Faster cutting lowers eyeblink rate and raises arousal**, and cuts are frequently invisible ("edit blindness", ~25–33 % of continuity cuts). Practical rule: cut **on motion** (match-cut on a moving subject's vector) for invisible cuts; cut on stillness for deliberate jolts.
4. **Continuous-action editing makes clips feel longer than discontinuous editing** while raising processing load. Practical rule: use *continuity* cutting inside an act (keeps the viewer inside the world), and reserve **discontinuity** for the two or three act breaks where you want a "time passes / everything changed" beat.
5. **Music/SFX drive arousal more reliably than picture alone.** Use the audio to carry tension in the shots where the imagery must be quiet (macro, dark water).

Design consequences (these are the actual "psychology" levers, honestly framed):
- **Hook ≤ 4 s** with one legible, high-contrast action + one sound that resolves.
- **Open loop every 8–15 s**: a question is raised before the previous one closes.
- **Pattern break every ~20 s**: a change of scale (micro → macro), palette, or silence.
- **One protected pure-cinema window** (~6–8 s) with zero text — the payoff the whole film builds to.
- **Payoff must be visible, not narrated.** If the narration says it, the image must *show* it in the same beat.

---

## 5. The measured production budget (this decides scope honestly)

From `bench.mjs` today, 2 vCPU SwiftShader:

| Preset | Resolution | ms/frame | 1,050 f (35 s) | 1,800 f (60 s) |
|---|---|---|---|---|
| Bare (no post) | 1280×720 | 31 | **0.5 min** | **1 min** |
| Light (bloom + ACES) | 1280×720 | 410 | 7 min | 12 min |
| Light (bloom + ACES) | 1920×1080 | 879 | 15 min | 26 min |
| Full (DOF + bloom + ACES + CA + SMAA) | 1280×720 | 3,753 | 66 min | 113 min |

**Chosen architecture (the only one that fits quality × time):**
> Render **beauty plates at 1280×720 with a light post stack**, then upscale to 1920×1080 with FFmpeg `libplacebo`/`zscale` + `cas` + `unsharp`, then apply **DOF and chromatic aberration per-shot in FFmpeg** (only on the shots that need them), then encode CRF 14–16. This buys ~85 % of the "full" look for ~15 % of the time.

Also: keep **motion blur** inside the renderer as *analytic camera blur* (cheap, already in the SDK's angular-pan math) and avoid per-pixel motion vectors entirely.

---

## 6. Priority upgrade list (impact × feasibility, ordered)

| # | Upgrade | Why it matters | Cost here |
|---|---|---|---|
| 1 | **Author real performances** — 6–10 hand-built clips per creature (drift, pulse, splay, strike, recoil, death-settle) layered over `Idle` via additive AnimationMixer + procedural sine layers on joints | Kills "static/boring". Anatomy already rigged (61/109 joints) | Pure math, ~0 render cost |
| 2 | **Contact shadows + one real light rail** — `createTexelSnappedShadowRig` every frame, key/fill/rim tied to depth | Grounds everything; removes "floating plastic" look | Moderate (1 shadow pass) |
| 3 | **Rapier physics pass** — sediment rain, debris on impact, current drag on soft bodies | Turns "particles" into cause-and-effect | ~0 (measured) |
| 4 | **Camera language: 1 idea per shot** — push-in on reveal, parallax dolly past rocks, whip-pan on the crisis, one long locked-off "witness" shot for the payoff | "Camera motions" was an explicit ask | Free |
| 5 | **Shot-length curve, not metronome** — 1/f-ish pattern, 12–20 shots/35 s, no shot > 4.5 s without an internal move | Directly from §4 research | Free |
| 6 | **Post stack, surgical** — bloom + ACES + vignette global; DOF only on 4–6 hero shots; CA only on crisis | Measured cost discipline | 12–26 min per pass |
| 7 | **Sound first, then picture** — VO locked to frames, sub-bass on reveals, one moment of true silence before the turn, convolution space per environment | The real "eargasm" lever, and it survives compression | Pedalboard, cheap |
| 8 | **3D-tracked typography** (troika SDF) instead of canvas HUD | Crisp at 1080p/4K, no tofu, no blur | ~0 |
| 9 | **Provenance & claims manifests** before any render (`claims/rights/story/shot-plan/voice-lock`) | Prevents the "certified final" ambiguity the last cut suffered | Writing only |
| 10 | **Optional Blender refinement in a *different* environment** (a machine with X libs or GPU) if true path-traced hero shots are ever required | The honest path to photoreal | Not available here |

---

## 7. Sources

- Cutting, DeLong & Nothelfer (2010), *Attention and the evolution of Hollywood film*, Psychological Science — shot-length 1/f structure.
- Gannon & Grubb, *Editing patterns and attentional synchrony* (Psychology of Aesthetics, Creativity, and the Arts) — ASL vs gaze convergence; 200 ms post-cut variability.
- *Movie editing influences spectators' time perception*, Scientific Reports 2022 — continuity vs discontinuity cutting.
- *Eyeblink rate watching classical Hollywood and post-classical MTV editing styles*, Scientific Reports 2017 — ASL vs blink rate.
- Huayuan biota: Nature 2025, `s41586-025-10030-0` (512 Ma, 153 species / 16 groups); Myrow et al. (possible Cambrian environmental change; causes uncertain).
- Package data: `registry.npmjs.org`, `pypi.org` metadata (versions/licenses as listed in §3.1). Repo evidence: GLB headers parsed with a Python GLB reader; benchmark harness in `/tmp/probe` (`bench.mjs`, 4 configs).

---

## 8. What is still missing before a *real* production pass

1. **Owner decision on format and length** (35 s `9:16` Short vs 60 s `16:9` vs 5 min feature) — each implies a different budget from §5.
2. **Audio authority**: either a verified dry stem of the *accepted* script (1.000×, no retime) or an explicit written decision to treat the mixed track as final and never claim a remix.
3. **Scientific scope**: which claims are permitted to appear as text on screen, and which stay narration-only.
4. **Permission to generate** new voice/audio at all.
5. A decision on whether a second, GPU-capable environment may be used for hero close-ups (this affects achievable realism ceiling, per §3.3).
