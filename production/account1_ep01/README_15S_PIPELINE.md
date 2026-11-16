# PEHRA — 15s True 3D Preview Pipeline

This folder produces the mandatory quality-check gate for Account 1 (`soc-01`), Episode 01 **`PEHRA`**: a **15.000s, 1080×1920, 30fps, 450-frame** dark-cinema preview made from animated Blender Cycles 3D renders with `voice-00` Urdu narration and a frame-locked -14 LUFS soundtrack.

## Files

| File | Purpose |
| --- | --- |
| `ep01_pehra.txt` | Approved 18-beat conversational Roman-Urdu script |
| `vo/beat_*.wav` | Generated `voice-00` Urdu narration |
| `build_audio_15s.py` | Builds the exact 15s soundtrack + `build/timeline_15s.json` |
| `fetch_assets.py` | Downloads verified Poly Haven / Khronos / three.js 3D assets |
| `render_scene.py` | Builds and path-traces the six animated 3D shots in Blender 4.2 LTS |
| `assemble_preview.py` | Adds captions/grade/grain/vignette, muxes audio, writes QC + keyframes |
| `ASSET_CREDITS.md` | CC0 / MIT asset credits and audio provenance |
| `.github/workflows/account1-ep01-preview.yml` | Parallel GitHub Actions render + assembly workflow |

## GitHub Actions runs

The workflow is manual so the lookdev frames can be approved before the full 450-frame render.

### 1) Six-frame lookdev contact sheet

```bash
gh workflow run account1-ep01-preview.yml \
  --ref arena/944c619c-top1 \
  -f mode=lookdev \
  -f samples=18 \
  -f res_pct=75
```

Download artifact `pehra-preview-lookdev-<run_id>` and inspect `PEHRA_15s_LOOKDEV_CONTACT_SHEET.jpg` plus `keyframes/`.

### 2) Final 15s video

```bash
gh workflow run account1-ep01-preview.yml \
  --ref arena/944c619c-top1 \
  -f mode=final \
  -f samples=4 \
  -f res_pct=100
```

Download artifact `pehra-preview-final-<run_id>`. The deliverable is:

```text
PEHRA_15s_PREVIEW_1080x1920.mp4
PEHRA_15s_CONTACT_SHEET.jpg
PEHRA_15s_QC.json
keyframes/*.png
master_15s.m4a
timeline_15s.json
ASSET_CREDITS.md
```

## Local equivalent

Requires Blender 4.2 LTS, FFmpeg/FFprobe, Python 3.11 with `numpy scipy pillow`:

```bash
python production/account1_ep01/build_audio_15s.py
python production/account1_ep01/fetch_assets.py
# Render each of the six shot IDs; see the workflow matrix for exact commands.
python production/account1_ep01/assemble_preview.py --mode final
```

## Hard quality rule

No still images are used as scene plates. Every delivered picture frame originates from an animated 3D scene; captions are transparent editorial text overlays generated after the render.
