# Monarch V6 Hollywood IMAX 3D Cinema SDK (`tools/monarch-v6-imax-sdk`)

Reusable, production-hardened 3D Cinema, Optical HDR Shader, Volumetric & Newtonian Physics VFX, Dolby-Style Audio DSP, Parallel Raw-RGBA WebSocket Renderer, and Decoded-MP4 Forensic QA SDK for **every new 3D Short (`1080×1920`) and Long Documentary (`1920×1080`)** built in `Top1`.

## Quick Start for Any New Video Project

1. **Bootstrap the `/tmp` GPU + DSP Runtime (1 command):**
   ```bash
   bash tools/monarch-v6-imax-sdk/bootstrap_v6_runtime.sh
   ```
2. **Import the SDK directly in your custom film's ES modules (DO NOT rewrite shaders, post-FX, font loaders, or renderers from scratch!):**
   ```js
   import {
     makeImaxMaterial,
     setImaxLightingPreset,
     createTexelSnappedShadowRig,
     buildNormalFromCanvas,
     buildOpticalBreadboardTexture,
     buildWoodPlankTexture,
     buildStoneGritTexture,
     createImaxOpticalPass,
     createVolumetricLightBlade,
     createVolumetricSpotlightCone,
     createLoopLockedDustMotes,
     createLaserTomographyScanner,
     createClearanceLaserGrid,
     createImpactShockwaveRing,
     createBallisticParticleSystem,
     GLM,
     buildLoftGeometry,
     createGroundContactAO,
     BUILTIN_HUMAN_GLBS,
     loadRiggedHumanActor,
     createCinemaCameraRig,
     assertSafeLatinGlyphs,
     loadVerifiedCinemaFonts,
     createGpuHudCompositor,
     drawImaxShortHud,
   } from '/tools/monarch-v6-imax-sdk/index.js';
   ```
3. **Build Audio with Zero VO Stretch + Dolby Sub-Braaams + EBU R128 Mastering:**
   Import from `tools/monarch-v6-imax-sdk/python/audio_imax_dsp.py`.
4. **Run Mandatory 2-Pass Visual Pre-Flight (`preflight`) BEFORE Full Render (`render`):**
   ```bash
   node tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs --page /tools/<your-film>/page.html --mode preflight ...
   ```
   Visually inspect BOTH the Cover PNG and 12-Beat QA Sheet via `read_file`, fix every framing/clipping/prop/lighting defect in Pass 2, then run `--mode render` and `verify_imax_mp4(...)` from `tools/monarch-v6-imax-sdk/python/forensic_qa_sdk.py`.

## Gold-Standard Reference Implementations in Repo
- **`9:16` Hollywood IMAX Viral Short (`1080×1920`, `35.0s`):** `tools/monarch-cockroach/short_v6/`
- **`16:9` Broadcast 3D Documentary (`1920×1080`, `5m 02s`):** `tools/monarch-cockroach/v5/`
- **Shared Rigged 53-Bone Human `.glb` Assets:** `tools/monarch-cockroach/v4/assets/{homeowner,researcher,athlete}.glb`
