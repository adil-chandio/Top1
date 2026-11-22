# CLAUDE.md — Top1 Autonomous 3D Cinema Studio (`V6 HOLLYWOOD IMAX`)

**CRITICAL — READ `AGENTS.md` AND `docs/Master-3D-Animation-Video-Production-Prompt-V6-IMAX.md` IMMEDIATELY BEFORE STARTING ANY VIDEO OR 3D TASK.**

1. **NEVER** copy or run deprecated V1–V3 code in `tools/extinct-life/`, `tools/monarchs-edit/`, `tools/monarch-ant*`, `tools/gecko/`, or `tools/demo-render/`.
2. **ALWAYS** bootstrap `/tmp` GPU + DSP via `bash tools/monarch-v6-imax-sdk/bootstrap_v6_runtime.sh` and import directly from **`tools/monarch-v6-imax-sdk/index.js`**, **`tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs`**, **`tools/monarch-v6-imax-sdk/python/audio_imax_dsp.py`**, and **`tools/monarch-v6-imax-sdk/python/forensic_qa_sdk.py`**.
3. Study **`tools/monarch-cockroach/short_v6/`** (`9:16` V6 Hollywood IMAX Short) and **`tools/monarch-cockroach/v5/`** (`16:9` V5 Broadcast Documentary) as the mandatory Gold-Standard Reference Implementations.
4. Enforce **2-Pass Visual Pre-Flight Inspection (`read_file` on 12-Beat QA Sheet v1 -> fix defects -> verify v2)** BEFORE full rendering, and pass **`verify_imax_mp4(...)` (`pytest`)** BEFORE presenting any video.
