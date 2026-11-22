# MASTER 3D CINEMA & HOLLYWOOD IMAX VIDEO PRODUCTION ENGINE — SDK-POWERED PROMPT (V6.1 REPO EDITION)

> **HOW TO USE IN ANY NEW CHAT CONNECTED TO `Top1`:**
> Because `AGENTS.md`, `CLAUDE.md`, `tools/monarch-v6-imax-sdk/`, and the Gold-Standard `tools/monarch-cockroach/short_v6/` reference film are now **pre-installed inside `Top1` (`main`)**, you can paste the **Short Trigger Prompt** below (or the full file) into any new chat connected to `Top1`!
>
> *(If pasting into an **OLDER ALREADY-OPEN CHAT** that was created before this merge, include the first `git fetch` line so that branch pulls the V6 IMAX SDK from `main` immediately!)*

---

## QUICK COPY-PASTE PROMPT FOR NEW OR EXISTING `Top1` CHATS

```markdown
## PROJECT BRIEF — V6 HOLLYWOOD IMAX 3D PRODUCTION
- **TOPIC / VIDEO IDEA:** [Yahan apna topic likhein — e.g., Titan Methane Rain / Huayuan Cambrian Fossils / Mantis Shrimp Cavitation Punch]
- **FORMAT & DURATION:** [9:16 Viral IMAX Short (1080x1920, ~35s seamless loop) OR 16:9 Long Video (1920x1080, ~5:00)]
- **CHAT LANGUAGE:** Roman Urdu / Hindi (keep code, shaders, DSP & physics terms exact)

## MANDATORY EXECUTION PROTOCOL (ZERO SHORTCUTS)
1. **Sync & Read Studio Constitution First:**
   - Run `git fetch origin main && git merge origin/main --no-edit` (if this branch predates the V6 IMAX SDK merge) and read `AGENTS.md` + `tools/monarch-v6-imax-sdk/README.md` + `tools/monarch-cockroach/short_v6/` (Gold-Standard V6 IMAX Reference).
   - **STRICT BAN:** NEVER copy or run legacy code from `tools/extinct-life/`, `tools/monarchs-edit/`, `tools/monarch-ant*`, `tools/gecko/`, or `tools/demo-render/`.
2. **Bootstrap & Import `tools/monarch-v6-imax-sdk/` Directly (Do NOT Rewrite Boilerplate!):**
   - Run `bash tools/monarch-v6-imax-sdk/bootstrap_v6_runtime.sh`.
   - Import `makeImaxMaterial`, `setImaxLightingPreset`, `createTexelSnappedShadowRig`, `buildNormalFromCanvas`, `createImaxOpticalPass` (Linear-Light ACES Filmic + 12-Tap Vogel Bokeh + Panavision 2.35x Anamorphic Bloom + 7-Tap Shutter Motion Blur), `createVolumetricLightBlade`, `createVolumetricSpotlightCone`, `createLoopLockedDustMotes`, `createLaserTomographyScanner`, `createImpactShockwaveRing`, `createBallisticParticleSystem`, `GLM`, `buildLoftGeometry`, `loadRiggedHumanActor`, `createCinemaCameraRig`, `assertSafeLatinGlyphs`, `loadVerifiedCinemaFonts`, `createGpuHudCompositor`, and `drawImaxShortHud` directly from `/tools/monarch-v6-imax-sdk/index.js`.
   - Spend **100% of your custom code budget** on **bespoke high-poly parametric 3D hero sculpting (`buildLoftGeometry` + `solveTwoBoneIK` + 3D X-Ray Cutaway), rich multi-set environments, Newtonian momentum/inertia/gravity/bounce choreography, and primary-source scientific accuracy**!
3. **Dolby-Cinema Audio Lock (`tools/monarch-v6-imax-sdk/python/audio_imax_dsp.py`):**
   - Audition & synthesize natural speech (`0.00%` VO time-stretch: `time_stretch_applied = False`).
   - Build a `48 kHz 24-bit` Dolby-style mix with `<190 Hz` sub-braaams (clean `220 Hz–4 kHz` vocal pocket), a `150–200 ms` `-180 dBFS` vacuum silence drop right before the twist word (*"Wait."*), `8 Hz` bullet-time chronometer ticks, physical modal foley, integer-cycle loop-locked score, `55 ms` look-ahead ducking, and 2-pass linear EBU R128 mastering (`-14.2 LUFS` / `-1.5 dBTP`).
4. **MANDATORY 2-PASS VISUAL PRE-FLIGHT CRITIQUE (BEFORE FULL RENDER!):**
   - Run `node tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs --mode preflight ...` to generate the Cover PNG + `12`-Beat QA Sheet JPG.
   - Inspect BOTH images visually via `read_file`. Do **NOT** rubber-stamp Pass 1: explicitly check `GLM.visibleHorizontalWidth` (`9:16` horizontal clipping), prop-limb intersections, background lamp photobombs, lighting contrast, and HUD legibility -> fix every flaw in code -> re-run Pre-Flight Pass 2 and verify via `read_file`!
5. **Parallel Raw-RGBA WebSocket Master Render & Forensic `pytest` Gate:**
   - Render full master via `tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs --mode render` (`CRF 16`, unified single-SPS/PPS `bt709` `+faststart`, `320k AAC`).
   - Run `pytest` calling `verify_imax_mp4(...)` from `tools/monarch-v6-imax-sdk/python/forensic_qa_sdk.py` (`0` decode errors, exact frame count, `0` `A->B->A` flicker spikes, seamless loop MAE `< 9.5`, `-14.2 ± 1.0 LUFS`, workspace `< 126 MiB`), then present the master `.mp4` (and upload to Google Drive if requested).
```

---

## FULL ARCHITECTURAL REFERENCE CHECKLIST

### A. The 5 Ironclad Zero-Flicker Laws
1. **Zero Coplanar Surfaces:** Separate stacked floors/overlays by `>= 0.2–1.8` world units; set `polygonOffset: true, polygonOffsetFactor: 2, polygonOffsetUnits: 2` on base ground meshes; keep `>= 0.3` air gaps around glass bevel trim.
2. **Deterministic Transparency:** Every `transparent: true` material MUST use `depthWrite: false`, `uReceiveShadow: 0.0`, `castShadow = false`, and explicit ascending `renderOrder` (`2` contact AO -> `5` opaque internals -> `10..12` glass -> `16..18` X-ray shell -> `21..26` additive volumetrics/lasers/shockwaves).
3. **`30 Hz` Every-Frame Light-Space Texel-Snapped Shadows:** Call `shadowRig.updateShadowMap(scene, focusCenter, frustumHalf)` on **every single frame (`30 Hz`, never `15 Hz`)**.
4. **Dynamic Near/Far Clipping:** `cameraRig.apply(...)` automatically brackets `camera.near` and `camera.far` to `focusDist`.
5. **Anti-Nyquist Oscillations & Zero `%` Teleports:** Never oscillate limbs/waves at `15.0 Hz` (`30 fps` Nyquist) and never snap positions back with `x % L`.

### B. `9:16` Portrait Framing & Seamless Infinite Loop (`Shorts`)
- Always compute `GLM.visibleHorizontalWidth(dist, fovY, 9/16)` so wide subjects, multi-lane arenas, and splayed human arms fit cleanly inside `1080×1920` horizontal margins.
- Keep single-line frosted-glass captions (`1–4` words, `44px Space Grotesk`) at `x = 486, y = 1318` (clear of right-side icons `x > 905` and bottom chrome `y > 1490`).
- For `35.0s` seamless Shorts, whip-pan back into the Opening Set `~18` frames before the end under peak `uMotionVec.x` shutter blur and decelerate (`GLM.easeOutQuint`) onto the canonical `Frame 0` camera, lighting, prop, and hero pose while ending the final spoken clause mid-sentence into `0.00s`!
