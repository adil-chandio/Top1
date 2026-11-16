# NAAM // PRIME — 48 s · 1080×1920 · 24 fps

**Deliverable:** `deliverables/MONARCH_NAAM_PRIME_1080x1920.mp4`
**Branch:** `arena/2a8ad29e-top1`

---

## Kya hai yeh

Ek 48-second, 8-shot, 1080×1920 premium cut. **Har shot me asli camera move hai** — koi
pan/zoom slideshow nahi, koi repeated image nahi (8 shots = 8 unique visuals).

| # | Shot | Source | Move |
|---|------|--------|------|
| 01 | EYES | photographic plate | slow push-in + light sweep |
| 02 | EDGE | **Cycles 3D** (gold slab stack + red string) | true-Z dolly (real depth buffer) |
| 03 | HANDS | photographic plate | push-in + rise |
| 04 | WRITING | photographic plate | lateral drift |
| 05 | SHARDS | **Cycles 3D** (gold shards + string fragments) | pull-back + roll + flash |
| 06 | MASK | photographic plate | dolly back |
| 07 | PAGE | photographic plate | drift + embers |
| 08 | TYPE | **Cycles 3D** (extruded gold NAAM in fog) | push + captions |

## Teen engine, ek film (hybrid 3D, jaisa spec kehta hai)

1. **Cycles 3D stage** — `prime/scene3d.py`. Asli geometry, asli metal, asli volumetrics,
   asli DOF (AgX, OIDN, 44 spp, 777×1382). Har CG shot ka **real View-Z depth buffer** bhi
   render hota hai → us Z se camera move *exactly* sahi parallax deta hai.
2. **Photographic plate stage** — 5 AI plates (768×1376, pure black background, single hard
   light). Inke liye luminance se depth field banti hai, phir per-frame re-projection.
3. **Comp stage** — `prime/film.py`: depth-correct reprojection, 3D dust field (true
   perspective), light sweep, DOF ramp, bloom, halation, filmic grade, chroma, grain,
   vignette, type, fades.

## Zero-compromise cheezein

- Koi repeated shot/plate nahi (8/8 unique).
- Koi pan-zoom nahi — har frame reprojected hai (parallax + dust perspective).
- Audio: numpy synth — sub drone 43 Hz, cut impacts, 60→96 BPM heartbeat, riser,
  **47.30–47.80 s silence punch**, final 38 Hz hit. Mono 48 kHz → AAC 192k.
- Type: DejaVu Serif/Mono, cream `#F3ECE2`, red `#D63026`, gold `#D6A85C`.

## Story (8 lines, no VO)

1. chehra — kaun hai yeh
2. sone ke 44 card — qeemat
3. haath — jinke liye
4. likhna — 5 naam
5. shatter — jo tootta hai
6. mask — jo rokta hai
7. jalta page — jo reh jaata hai
8. **NAAM** — "Jinke naam tum nahi le sakte / unke naam pe apni zindagi / nahi de sakte."

## Rebuild

```bash
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install bpy imageio-ffmpeg pillow imageio numpy
bash tools/xstubs.sh                      # X/GL stubs for headless bpy
cd cinema_v4/prime
LD_LIBRARY_PATH=/tmp/xstub /tmp/venv/bin/python scene3d.py all build 0.72 44
/tmp/venv/bin/python film.py             # renders 1152 frames + audio + mp4
```

Timing (2 CPU cores): Cycles stills 18–70 s each; comp 2.4 s/frame; full film ≈ 46 min.
