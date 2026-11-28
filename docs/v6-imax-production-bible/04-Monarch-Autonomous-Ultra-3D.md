# Monarch Autonomous Ultra 3D — Complete Studio Architecture & Production Manifest (`V7.0`)

This document archives the complete architecture, research-backed DSP/biomechanical upgrades, Creative Producer & Film Director OS, and verified productions built across the **`monarch autonomous ultra 3d`** milestone in `Top1`.

---

## 1. Core Studio Modules Added & Upgraded

### A. Creative Producer & Film Director OS (`tools/director-producer-os/`)
- **Catalogs & Schemas:**
  - `catalog/world_archetypes.json` — 24 distinct physical world archetypes (`W01`–`W24`) paired with 6 HUD philosophies (`H0`–`H5`) to eliminate visual repetition across productions.
  - `catalog/production_fingerprints.json` — Historical production registry enforcing `>= 65%` structural, spatial, optical, and chromatic divergence against recent films.
  - `schemas/director-plan.schema.json` — Strict Gate 0.5 JSON schema governing story spine, Bruce Block visual intensity arc, Roger Deakins Kelvin/focal-length progression, `180°` spatial axis, `30°` cut separation, Walter Murch eye-trace continuity, and protected `0%`-HUD climax windows.
- **Validators & Regression Suite:**
  - `validators/director_linter.py` & `validators/anti_clone_validator.py` — 32 deterministic pre-production checks (`9/9` unit tests in `tests/test_director_producer_os.py`).

### B. Eargasm Broadcast Audio & Physical Foley Engine (`tools/monarch-v6-imax-sdk/python/audio_eargasm_v7.py`)
- **Uniform Per-Clip Broadcast Dialogue Leveling (`level_and_polish_voice_clip`):**
  - Eliminates raw TTS clip-to-clip volume drops (`0.00 dB` dry voiced RMS spread across all lines; `1.000x` natural speech speed preserved with `time_stretch_applied = False`).
  - Chain: `85 Hz` Butterworth HPF -> `-2.5 dB @ 310 Hz` mud cut -> `+1.8 dB @ 3.6 kHz` presence shelf -> `2.6:1` optical speech compression -> voiced-window RMS normalization (`-18.00 dBFS`) -> soft-knee `tanh` peak ceiling + micro-RMS trim.
- **Zero-Hiss Sub-Air Ambience (`kellet_pink_noise` + `zero_hiss_ambient_air`):**
  - Replaces broadband `210–6200 Hz` white-noise wind/room beds with Paul Kellet 3-pole pink turbulence low-passed strictly `< 230 Hz` (`-72.42 dBFS` stationary `2.5–7.0 kHz` post-AAC floor).
- **Physical Foley & 4-Act Acoustic Score:**
  - Perry Cook `PhISEM` Poisson particle sweeps (`asmr_brush_sweep`, `crawl_footstep_grit`), free-bar inharmonic modal resonators (`modal_stone_fracture`, `modal_bone_click` `1 : 2.76 : 5.40 : 8.93`), aeroacoustic `Strouhal` camera whooshes (`strouhal_camera_whoosh`), and Minnaert `f = 3.26 / r` rising bubble chirps (`minnaert_bubble_chirp`).
  - Jaffe-Smith Karplus-Strong acoustic guitar (`karplus_strong_pluck`), Fletcher-Rossing wooden marimba (`marimba_strike` `1 : 4 : 10`), warm bowed cello pads (`warm_cello_pad_note`), Shepard curiosity risers (`shepard_riser`), `-4.5 dB @ 1.85 kHz` vocal-pocket carving (`carve_vocal_pocket`), and `15 ms` / `380 ms` lookahead sidechain ducking (`lookahead_sidechain_duck`).

### C. Living 3D Biomechanics, Secondary Motion & Optics (`tools/monarch-v6-imax-sdk/`)
- `js/monarch_ultra_rig_v7.js` — Non-linear retention easing (`snapGlide`, `recoilSpring`), traveling vertebrate S-wave spine undulation (`evaluateSpineWave`), partner-gated quadruped gait & injured limp (`evaluateQuadrupedStep`), natural blink curves (`evaluateBlinkCurve`), asymmetric breathing waves (`evaluateBreathingWave`), wind cloth/paper flutter (`evaluateFlutterDisplacement`), and ballistic footstep/brush dust puffs (`createDustPuffBurst`).
- `core/director_optics_sdk.js` & `core/pbr_shadow_sdk.js` — Exact focal-length to `9:16` / `16:9` FOV math, Kelvin blackbody lighting, procedural sandstone strata & excavation grit normal maps, and Karoo fossil/burrow plugins (`plugins/karoo_burrow_plugins.js`).
- `python/forensic_qa_sdk.py` — Streaming `O(1)`-RAM decoded-MP4 video + post-AAC audio validator enforcing frame count, zero black/flicker spikes, seamless loop MAE `<= 2.5`, EBU R128 loudness, True Peak `<= -1.0 dBTP`, pre-twist digital vacuum, spoken-line uniformity (`<= 3.5 dB` post-AAC), and stationary HF hiss floor (`<= -55.0 dBFS`).

---

## 2. Productions Delivered & Archived

1. **Karoo Burrow V7.0 — Autonomous Ultra Monarch Edition (`projects/extinct-karoo-ultra-v7/`)**
   - `1080×1920 @ 30 fps`, `1,080` frames (`36.00s`), `0.565 / 255` seamless loop MAE, `0.00 dB` dry VO spread (`2.72 dB` full-mix post-AAC), `-72.42 dBFS` zero-buzz floor, `-14.60 LUFS`, `-2.20 dBTP`, `-129.63 dBFS` vacuum.
   - Google Drive Archive: `https://drive.google.com/drive/folders/1H_QRKZ3fVLoZKq4Y3_95gJXwbU7Zwg2A` (`Karoo-Burrow-Ultra-Monarch-V7.mp4` -> `13kV9wYIi05BB-ZKlL2ucf0-FQJGdojDQ`).
2. **Karoo Burrow V6.3 — Scorched Field-Dig Edition (`projects/extinct-karoo-field-v63/`)**
   - Google Drive Archive: `https://drive.google.com/drive/folders/1FgilIc8v2N1_5kM2ny_VEjmpe6kqwiee` (`1pM3Y140TDcpACyvt2MYr6SFnqbJVTHsV`).
3. **Karoo Burrow V6.2 — Synchrotron Dark-Lab Edition (`projects/extinct-karoo-burrow/`)**
   - Google Drive Archive: `1CJRpDPbXtJWvtNpaXCSP8qa5QAVfHHUC`.
4. **Thermal Shock V6 Ultra (`projects/monarch-edits-thermal-shock/`)**
   - Google Drive Archive: `1zkveNaWexKaIcb2LvNzNZncICeiBqYx7`.
