# Desi 3D Explainer — Build Guide (MONARCHs Edit channel · P1)

**Status: build source — nothing is published.** The P1 3D explainer is an illustrative 3D model of the first pilot ("Metal ya Lakri — Baraf Pehle Kahan Pighlegi?"). It is not a substitute for the physical run the audit requires (three paired runs, swapped sides, raw footage kept). See the decision record at [../research/MONARCHS-EDIT-DESI-EXPLAINER-2026-11-21.md](../research/MONARCHS-EDIT-DESI-EXPLAINER-2026-11-21.md) for what is decided and what is not.

## Layout

| File | Role |
| --- | --- |
| `timeline.js` | Pure beat sheet, shared clock, illustrative melt curves, caption text. |
| `scene.js` | Three.js scene graph — two blocks (metal / lakri) + two ice cubes + heat-transfer arrows. No DOM, no renderer; safe to import in Node. |
| `index.html` | Compositor entry (720 × 1280, 9:16). |
| `main.js` | Renderer + 2D caption layer (METAL/LAKRI labels, T+ clock, TIME-LAPSE marker, reveal beat, outro card, beat rail). Publishes `window.top1Frame(seconds)`. |
| `render.mjs` | Headless render harness (stills or full MP4). |

## Run it

Requires Node 22.12+ and a Playwright-compatible Chromium. A full MP4 also requires FFmpeg with libx264 and AAC on `PATH` (or `FFMPEG=`).

```sh
npm ci

# Stills only — no ffmpeg needed — writes 6 JPEG stills to .cache/monarch-desi-3d-explainer/stills
CHROMIUM=/path/to/chromium TOP1_DESI3D_STILLS=1 node tools/monarchs-edit/desi-3d-explainer/render.mjs

# Full MP4 — renders 38 s at 24 fps and encodes with ffmpeg
CHROMIUM=/path/to/chromium FFMPEG=/path/to/ffmpeg node tools/monarchs-edit/desi-3d-explainer/render.mjs

# Mux optional voice-over audio (local file only — nothing is uploaded or sent)
TOP1_DESI3D_AUDIO=/path/to/narration.m4a node tools/monarchs-edit/desi-3d-explainer/render.mjs
```

Output defaults to `.cache/monarch-desi-3d-explainer/` so channel assets never land in the public storefront folder. `TOP1_DESI3D_OUT` overrides the folder.

## The scene, and what it must never claim

- The scene shows the two choices (metal vs lakri) with matching ice cubes, room temperature and a shared clock.
- The metal/wood melt difference is **illustrative** — a direction, not a measurement. The frame carries a persistent `ILLUSTRATIVE 3D MODEL — NOT A TEST RESULT` badge and the reveal caption repeats the honest line.
- The 3D model is not a physics simulation of conduction, mass, time or temperature. No conductivity, force or temperature number is shown. No result is staged with synthetic footage.
- The physical P1 test (camera, real cubes, real timing, swapped sides, raw footage) is the only honest way to claim a result. Until it is done, the channel must describe the 3D explainer as an illustration and a first draft.

## Scope

- First pilot only. The channel's second episode (E1 — metal spoon feels cooler) is not built yet; the 3D source is designed to be reused (new look, same beats).
- No narration, voice, music, captions or channel uploads are produced here. The explainer is a picture-only build source; add narration locally, in the channel's own tools, after the owner approves the first draft.
- The scene stays separate from the Top1 storefront and from the Monarch Studio intro videos. It never appears in `public/demos/` or the site.
