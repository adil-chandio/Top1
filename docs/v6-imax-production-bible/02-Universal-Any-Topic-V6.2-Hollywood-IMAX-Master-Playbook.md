# Universal Any-Topic V6.2 Hollywood IMAX 3D Video Master Playbook
## How to Build Luxury Cinema-Hall `9:16` Shorts & `16:9` Documentaries on ANY Topic With Zero Flaws

This playbook is the **topic-agnostic engineering & directing blueprint** for producing Hollywood IMAX-grade 3D animated videos in `Top1` across **any domain** — Animal Biomechanics, Human Body / Surgery / Medicine, Astrophysics / Space Missions, Mechanical & Civil Engineering, Aviation / Motorsports, Physics & Chemistry, or Historical Reconstructions — in either **`9:16` Viral Short (`1080×1920`, `~30–45s` infinite loop)** or **`16:9` Feature Documentary (`1920×1080`, `3–10+ min`)** format.

---

## WHY OTHER CHATS FAIL — AND HOW THIS PLAYBOOK PREVENTS EVERY FAILURE

| Common Failure in Ordinary Chats | V6.2 Hollywood IMAX Solution Built Into `Top1` |
|---|---|
| Visuals animated on guessed timestamps -> out-of-sync cuts | **Gate 2 (Audio-First Frame Lock):** Synthesize natural VO first (`0%` stretch), tighten dead air `< 0.48s`, extract exact `30 fps` word/beat frame indices into `voice-lock.json` BEFORE writing `director.js`. |
| Toy-like primitive cylinders/spheres/boxes & flat Three.js lighting | **Gate 3 (`monarch-v6-imax-sdk`):** Parametric cross-section lofting (`buildLoftGeometry`), 2-bone IK (`solveTwoBoneIK`), Sobel normal maps (`buildNormalFromCanvas`), 3D X-Ray/cutaway rigs, volumetric cones, ACES + Kodak 2383 + Vogel bokeh! |
| T-pose human `.glb` arms, clipped limbs, or blurry hero shots | **Gate 5 (Mandatory 2-Pass Storyboard Eye-Gate):** Render `12/16-Beat QA Sheet` + `Cover/Thumbnail` FIRST, inspect with `read_file`, verify bone axes via quaternion math, fix every flaw, and verify Pass 2 BEFORE full render! |
| Long renders timing out or running out of RAM | **Gate 6 (`--max-chunks` + Hybrid Compositor):** Resumable `300`-frame raw-RGBA WebSocket chunks (`plate_000..N.mp4` + `.json`), `1920×1080` Lanczos upscale + cached `2×` `WOFF2` HUD compositing in `< 50 MB` RAM! |
| Black frames, Z-fighting flicker, or `0.0 dBFS` AAC clipping | **Gate 7 (`forensic_qa_sdk.py` `pytest`):** Streaming `O(1)`-RAM full-frame MP4 decode audit (`min_luma > 8`, `0` `A->B->A` spikes), `-af alimiter=limit=0.708:level=false` post-AAC True Peak `<= -1.0 dBFS`, + Decoded-MP4 Proof Sheet! |

---

## THE 7 MANDATORY PRODUCTION GATES (EXECUTE IN EXACT ORDER FOR ANY TOPIC)

### GATE 0 — Sync `Top1` Studio Constitution & Bootstrap `/tmp` GPU/DSP Runtime
1. If working in an older branch created before the latest `main` update, sync first:
   ```bash
   git fetch origin main && git merge origin/main --no-edit
   ```
2. Read `AGENTS.md`, `tools/monarch-cockroach/short_v6/` (for `9:16` Shorts), and `tools/monarch-cockroach/long_v6/` (for `16:9` Long Features). **Never** copy deprecated `tools/extinct-life`, `tools/monarchs-edit`, `tools/monarch-ant*`, `tools/gecko`, or `tools/demo-render`.
3. Bootstrap headless Chromium + SwiftShader Vulkan + WOFF2 fonts + Python DSP in `/tmp`:
   ```bash
   bash tools/monarch-v6-imax-sdk/bootstrap_v6_runtime.sh
   ```

---

### GATE 1 — Primary-Source Research & "Visual Paradox Chain" Scriptwriting
1. **Fact Collection (Zero Hallucinated Numbers):**
   - If the user provides a research paper, Google Doc, or Drive asset, read it via `google_drive` / `google_docs` or `read_file`.
   - If the topic requires external scientific/engineering facts and web tools (`web_search`, `fetch_page`) are enabled in the session, fetch primary peer-reviewed papers, NASA/ESA technical reports, or official engineering specs first and record exact numbers, units, dimensions, velocities, forces, temperatures, and failure thresholds.
2. **Structure the Script as a Relentless Visual Paradox Chain (NOT a Wikipedia Summary):**
   - **Cold-Open Hook (`0–18s` Long / `0–4s` Short):** Put the viewer inside a relatable real-world moment with an everyday physical scale object (a coin, human hand, car tire, needle eye, Boeing 747 wing) and show an seemingly impossible physical feat.
   - **The "Wait." Twist Beat:** Immediately after the cold-open feat, drop `180–230 ms` of complete digital silence (`-180 dBFS` pre-mux) right before `"Wait."` / `"Wait a second."` and state the core mechanical/physical paradox.
   - **Escalating Chapters / Beats (`Question -> 3D Test -> Surprising Twist -> Human Analogy -> Climax`):**
     - Every `8–15s` (Long) or `2.5–3.5s` (Short) must introduce a **new camera angle, scale shift, 3D X-Ray cutaway, multi-lane comparison race, or physical analogy** (like our human wide-arm push-up collapse in Ch 04!).
     - Reserve **Protected Pure-Cinema Climax Windows** where narration pauses or breathes and **`100%` of text/HUD/leader lines turn OFF** so the viewer experiences pure unobstructed IMAX spectacle.
   - **Resolution & Primary-Source Finale:** Close by synthesizing how the mechanism inspires real-world technology/medicine/engineering (or loops seamlessly back into `Frame 0` for `9:16` Shorts!).

---

### GATE 2 — Audio-First Frame Lock & Dolby Cinema Sound Design
**RULE: Never animate a single 3D shot before `voice-lock.json` exists.**
1. **Voiceover Synthesis (`0.00%` Time-Stretch):**
   - Audition voice via `add_voice` (`narration` or `educational`) if no voice is locked yet in the session, then synthesize crystal-clear clauses via `generate_speech`.
   - Trim inter-clause dead air to `0.18–0.45s` (`max <= 0.48s`) while leaving spoken syllables **`100.0%` untouched (`time_stretch_applied = False`)**.
2. **Generate `voice-lock.json` + `.srt` / `.vtt` Captions:**
   - Compute exact `30.000 fps` (`frame = round(t_sec * 30)`) anchor frames for every chapter, shot cut, impact transient, protected climax window, and caption cue.
3. **Dolby-Style Multi-Stem Master Mix (`48 kHz / 24-bit` WAV via `audio_imax_dsp.py`):**
   - **Stem 1 (Narration):** Centered, clear `220 Hz – 4 kHz` pocket.
   - **Stem 2 (`< 190 Hz` Sub-Bass Braaams & Impact Drops):** Locked to paradox reveals and physical slams.
   - **Stem 3 (Physical Modal Foley & Chronometer Ticks):** Synthesized/layered material impacts (metal, bone, water cavitation, laser scan hum, `8 Hz` slow-motion ticks).
   - **Stem 4 (Atmospheric Room Tone & Subtle Harmonic Pulse):** Ducked via `55 ms` look-ahead sidechain whenever narration speaks, and **muted to `-180 dBFS` inside the Pre-Twist Vacuum Window**!
   - Master to **`-14.2 LUFS`** (`-1.5 dBFS` WAV ceiling).

---

### GATE 3 — Multi-Scale 3D World, Custom Shaders & Volumetric Atmosphere
Import directly from `/tools/monarch-v6-imax-sdk/index.js`:
1. **Consistent Physical World Units:** Define an explicit physical unit (`1 unit = 1 mm`, `1 cm`, `1 m`, or `1,000 km` per set) so velocities, gravity (`y = v0·t - ½g·t²`), and camera `focusDist` behave physically.
2. **Bespoke High-Poly Hero Assets (Zero Toy Primitives):**
   - Organic/aerodynamic/mechanical forms: `buildLoftGeometry` (sealed cross-section tubes/shells/organs/fuselages) + `buildNormalFromCanvas` (procedural micro-bump/grain/weave/crater normal maps).
   - Articulated limbs/pistons/linkages: `solveTwoBoneIK` + `InstancedMesh` micro-details (spines, rivets, cells, debris).
   - Internal mechanism reveal: Build a dedicated **3D Translucent X-Ray / Sagittal Cutaway Rig** (`depthWrite: false`, explicit `renderOrder: 16..18` over `renderOrder: 5` opaque internals) swept by `createLaserTomographyScanner`!
   - Rigged `.glb` Humans (`loadRiggedHumanActor`): **Always verify local bone rest quaternions in Python/Node before posing** (`rx` vs `rz` under `Shoulder` rest quaternions) so actors never T-pose or clip through props!
3. **Multi-Mood Volumetric Lighting & Zero-Flicker Setup:**
   - Design `4–6` distinct lighting moods (`midnight`, `warm_practical`, `surgical_xray`, `macro_amber`, `lab_clean`, `studio_dramatic`) driving `uKeyDir`, `uKeyColor`, `uFillColor`, `uRimLightCol`, `uSkyColor`, `uGroundColor`, `uFogColor`.
   - Add `createVolumetricLightBlade` / `createVolumetricSpotlightCone` + pinpoint `createLoopLockedDustMotes` (**always set volumetric `visible = false` during the `30 Hz` shadow depth pass** so light cones never cast opaque shadows, and clamp dust motes clear of the macro near-plane!).
   - Enforce all **5 Zero-Flicker Laws** (`>= 0.2` plane separation + `polygonOffset`, `depthWrite: false` + ascending `renderOrder` on transparencies, `30 Hz` texel-snapped shadows every frame, dynamic `near`/`far`, non-`15 Hz` oscillations & zero `%` snap-backs).

---

### GATE 4 — Virtual Cinema Director, Newtonian Physics & 3D-Tracked Action Graphics
1. **`director.js` (`directFrame(world, camera, frame)`):**
   - List **every single hard camera cut** in `SHOT_CUTS = new Set([...])` and pass it to `createCinemaCameraRig(camera, { totalFrames, shotCuts: SHOT_CUTS, impacts })`.
   - Combine **motivated Hollywood camera moves**:
     - Whip-crane / whip-pan transitions (`dutchDeg` banking + angular-pan `180°` shutter blur)
     - Hitchcock Vertigo counter-zooms on psychological/paradox reveals (pull camera back while narrowing/widening `fov`)
     - Tight tracking dollies (`dPos == dLook`, keeping hero razor-sharp via angular-pan velocity `(dLook - dPos) / focusDist`)
     - Visual Match-Cuts between microscopic/cosmic mechanics and relatable human-scale analogies!
   - Drive **Newtonian physics** on every interaction: parabolic debris/sparks (`createBallisticParticleSystem`), expanding impact rings (`createImpactShockwaveRing`), exponential restitution bounce (`A * exp(-k*t) * |sin(ω*t)|`), and sympathetic micro-tremors on nearby scale props.
2. **`titles.js` (Typography, 3D-Tracked Callouts & Gauges):**
   - Pass every string through `assertSafeLatinGlyphs(...)` at startup so headless Linux WOFF2 rendering never produces missing-glyph boxes (`□`).
   - Project 3D world anchors (`camera.project()`) to `1920×1080` / `1080×1920` screen coordinates for live tracked pointer lines & reticles.
   - Enforce **`100%` zero text/HUD/leaders inside Protected Climax Windows**!

---

### GATE 5 — Mandatory 2-Pass Storyboard Visual Critique (`--mode preflight`)
**NEVER start a full render before completing BOTH passes of this visual gate:**
1. Run `--mode preflight` to render the **Hero Thumbnail / Cover PNG** + **`12`-Beat (Short) or `16`-Beat (Long) Multi-Chapter Storyboard Sheet JPG** (printing per-beat `mean_luma` to verify `luma > 20`).
2. **Pass 1 Critique (`read_file` on BOTH images):** Inspect every panel with your own eyes for:
   - Horizontal/vertical FOV clipping (`GLM.visibleHorizontalWidth` in `9:16`!)
   - `.glb` human bone angles, prop-limb intersections, or background poles/lamps photobombing the hero
   - Excessive motion blur on tracked macro shots or oversized dust particles near the lens
   - Typography contrast, safe-zone margins, and leader-line target accuracy.
3. **Fix & Verify Pass 2:** Patch every flaw in code, re-run `--mode preflight`, and re-inspect via `read_file` until **every single panel is 10/10 cinema-hall quality**.

---

### GATE 6 — Resumable Raw-RGBA WebSocket Render & Master Compositing
- **For `9:16` Shorts (`~900–1,350` frames):**
  - Stream native `1080×1920` raw-RGBA frames (with GPU HUD composited live) via `tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs --mode render` (`CRF 16`, single-SPS/PPS `bt709` `+faststart`).
- **For `16:9` Long Documentaries (`3,000–18,000+` frames):**
  - Use the proven **Hybrid Two-Stage IMAX Architecture** (`tools/monarch-cockroach/long_v6/render_long_v6.mjs` + `assemble_master_long_v6.py`):
    1. Render resumable `300`-frame `1280×720` `CRF 12` `vflip` beauty chunks (`plate_000..N.mp4` + per-frame `plate_000..N.json` projection metadata) in safe `--max-chunks` batches so zero work is ever lost to command timeouts.
    2. Stream all chunks through FFmpeg `scale=1920:1080:flags=lanczos` into Python, compositing `2×`-supersampled 3D leader lines, cached `IBM Plex Mono` `.woff2` telemetry pills, and pre-baked `1920×1080` `Space Grotesk` RGBA cards in `< 50 MB` RAM!
    3. Encode with `-c:v libx264 -preset medium -crf 18 -maxrate 2120k -bufsize 4400k` (keeping a 5-minute feature `< 95 MB` for direct Google Drive upload) and **`-af "alimiter=limit=0.708:level=false" -c:a aac -b:a 256k`** so post-AAC True Peak stays `<= -1.1 dBFS`!

---

### GATE 7 — Streaming `O(1)`-RAM Forensic `pytest` Gate, Decoded-MP4 Proof Sheet & Delivery
1. Run `pytest` calling `verify_imax_mp4(...)` (`tools/monarch-v6-imax-sdk/python/forensic_qa_sdk.py`):
   - `decoded_frames == TOTAL_FRAMES`, `0` FFmpeg decode errors
   - `min_luma > 8.0` (`0` black/dropped frames)
   - `aba_spikes == 0` (`0` single-frame flicker spikes across all non-cut frames)
   - `loop_mae < 9.5` (for seamless infinite-loop Shorts)
   - `-15.4 <= lufs <= -13.2` and **post-AAC `true_peak_dbfs <= -0.9 dBFS`**
   - `vacuum_rms_db < -48.0 dBFS` inside the Pre-Twist Vacuum Window
   - `0` overlay/HUD/leader violations inside all Protected Climax Windows!
2. Decode `12` or `16` actual frames directly from the finished `.mp4` into a **Decoded-MP4 Proof Sheet** and inspect via `read_file` to confirm final muxed perfection.
3. Upload the complete deliverable bundle (`.mp4`, `Thumbnail/Cover .png`, `QA Sheet .jpg`, `Master Mix .wav`, `Dry VO .wav`, `.srt`, `.vtt`, `Launch Copy .md`, `Forensic QA Receipt .json`) to Google Drive, clean heavy `.wav`/scratch files so persistent `/home/user/Top1` untracked size stays `< 100 MiB` (`< 128 MiB` cap), commit clean code, and open the `.mp4` via `present_file`!

---

## UNIVERSAL COPY-PASTE STARTER PROMPT FOR ANY NEW CHAT IN `Top1`

```markdown
## PROJECT BRIEF — V6.2 HOLLYWOOD IMAX 3D PRODUCTION
- **TOPIC / STORY:** [Yahan koi bhi topic likhein — e.g., Mantis Shrimp Cavitation Punch / How Jet Engines Survive 1,700°C / Inside a Black Hole Accretion Disk / How Human Heart Valves Snap Shut 100,000x a Day]
- **FORMAT:** [9:16 Viral Short (1080x1920, ~35s seamless loop) OR 16:9 Long Documentary (1920x1080, ~5:00)]
- **LANGUAGE IN CHAT:** Roman Urdu / Hindi (code, math, shaders, DSP & git exact)

## MANDATORY V6.2 EXECUTION PROTOCOL (ZERO SHORTCUTS, ZERO FLAWS)
1. Sync `main` if needed (`git fetch origin main && git merge origin/main --no-edit`) and read:
   - `AGENTS.md`
   - `docs/v6-imax-production-bible/02-Universal-Any-Topic-V6.2-Hollywood-IMAX-Master-Playbook.md`
   - `docs/v6-imax-production-bible/01-Monarch-Cam-03-Long-V6-Complete-Forensic-Case-Study.md`
   - Reference implementations: `tools/monarch-cockroach/short_v6/` (9:16 Short) & `tools/monarch-cockroach/long_v6/` (16:9 Long Feature).
2. Run `bash tools/monarch-v6-imax-sdk/bootstrap_v6_runtime.sh` and build directly on `/tools/monarch-v6-imax-sdk/index.js` (NEVER copy deprecated `extinct-life`, `monarchs-edit`, `monarch-ant*`, `gecko`, or `demo-render`).
3. Execute all **7 Mandatory Gates** without skipping a single step:
   - Gate 1: Primary-source verified facts + Visual Paradox Chain script with Protected Pure-Cinema Climax Windows.
   - Gate 2: `0.00%` stretch VO (`add_voice` + `generate_speech`) -> exact `30 fps` `voice-lock.json` + Dolby `<190 Hz` sub-braaam + `-180 dBFS` Pre-Twist Vacuum Drop + `-14.2 LUFS` mix.
   - Gate 3: Multi-scale high-poly 3D sets (`buildLoftGeometry`, `solveTwoBoneIK`, `buildNormalFromCanvas`, 3D X-Ray Cutaway + Laser Scanner, quaternion-verified `.glb` poses, volumetric cones hidden during shadow pass).
   - Gate 4: Virtual Cinema Director (`createCinemaCameraRig` angular-pan shutter blur zeroed across `SHOT_CUTS`, whip-cranes, Vertigo zooms, match-cuts, Newtonian parabolic debris/sparks & shockwaves) + `assertSafeLatinGlyphs` 3D-tracked HUD.
   - Gate 5: **2-Pass Visual Pre-Flight Gate** — render Thumbnail/Cover + 12/16-Beat QA Sheet, inspect via `read_file`, fix every visual defect, and re-verify Pass 2 BEFORE full render.
   - Gate 6: Resumable raw-RGBA WebSocket render (`--max-chunks` batches for Long features) + Lanczos 1080p compositing + `-af "alimiter=limit=0.708:level=false"` post-AAC True Peak protection (`< 95 MB` MP4).
   - Gate 7: Pass `pytest` (`verify_imax_mp4`: `0` decode errors, `min_luma > 8`, `0` `A->B->A` flicker spikes, post-AAC TP `<= -0.9 dBFS`), visually inspect a Decoded-MP4 Proof Sheet via `read_file`, upload deliverables to Google Drive, keep workspace `< 126 MiB`, and call `present_file`!
```
