# Desi 3D Explainer — Build Guide (MONARCHs Edit channel · P1 + E1 + long-form)

**Status: build source — nothing is published.** The 3D explainers are illustrative 3D models of the pilots: P1 ("Metal ya Lakri — Baraf Pehle Kahan Pighlegi?"), E1 ("Metal Ka Chamach Zyada Thanda Kyun Lagta Hai?") and the first long-form companion ("Baraf pehle kahan pighlegi — metal ya lakri?", 16:9 · 92 s). They are not substitutes for the physical runs the audit requires (three paired runs, swapped sides, raw footage kept). See the decision record at [../research/MONARCHS-EDIT-DESI-EXPLAINER-2026-11-21.md](../research/MONARCHS-EDIT-DESI-EXPLAINER-2026-11-21.md) for what is decided and what is not.

## Layout

| File | Role |
| --- | --- |
| `scenarios.js` | Pilot registry (`PILOTS`, `getPilot`) — the one lookup used by the compositor and the harness. |
| `p1/timeline.js` | Pure P1 beat sheet, shared clock, illustrative melt curves, caption text. |
| `p1/scene.js` | Three.js scene graph — two blocks (metal / lakri) + two ice cubes + heat-transfer arrows. No DOM, no renderer; safe to import in Node. |
| `e1/timeline.js` | Pure E1 beat sheet, shared clock, illustrative warmth-drain curves, paddle pose, caption text. |
| `e1/scene.js` | Three.js scene graph — two blocks (metal / lakri) + one warm paddle with emissive warmth that drains via the timeline's curves. No DOM, no renderer; safe to import in Node. |
| `long/timeline.js` | Pure long-form (16:9) beat sheet, shared clock, illustrative melt curves, caption text. |
| `long/scene.js` | Three.js scene graph — two wide blocks (metal / lakri) + two ice cubes + heat-transfer arrows, composed for the 16:9 frame. No DOM, no renderer; safe to import in Node. |
| `index.html` | Compositor entry (9:16 default; per-pilot via the timeline's `FRAME`). Pilot selected with `?pilot=p1|e1|long` (default `p1`). |
| `main.js` | Renderer + 2D caption layer (METAL/LAKRI labels, T+ clock, TIME-LAPSE marker, reveal beat, outro card, beat rail). Publishes `window.top1Frame(seconds)`. |
| `render.mjs` | Headless render harness (stills or full MP4). Pilot selected with `TOP1_DESI3D_PILOT=p1|e1|long`. Still images follow the pilot's own `view.stillTimes`. |

## Run it

Requires Node 22.12+ and a Playwright-compatible Chromium. A full MP4 also requires FFmpeg with libx264 and AAC on `PATH` (or `FFMPEG=`).

```sh
npm ci

# Stills only — no ffmpeg needed — writes the pilot's stills to .cache/monarch-desi-3d-explainer/stills
CHROMIUM=/path/to/chromium TOP1_DESI3D_STILLS=1 TOP1_DESI3D_PILOT=long node tools/monarchs-edit/desi-3d-explainer/render.mjs
CHROMIUM=/path/to/chromium TOP1_DESI3D_STILLS=1 TOP1_DESI3D_PILOT=p1 node tools/monarchs-edit/desi-3d-explainer/render.mjs
CHROMIUM=/path/to/chromium TOP1_DESI3D_STILLS=1 TOP1_DESI3D_PILOT=e1 node tools/monarchs-edit/desi-3d-explainer/render.mjs

# Full MP4 — renders the pilot's duration at 24 fps and encodes with ffmpeg
CHROMIUM=/path/to/chromium FFMPEG=/path/to/ffmpeg TOP1_DESI3D_PILOT=long node tools/monarchs-edit/desi-3d-explainer/render.mjs
CHROMIUM=/path/to/chromium FFMPEG=/path/to/ffmpeg TOP1_DESI3D_PILOT=p1 node tools/monarchs-edit/desi-3d-explainer/render.mjs
TOP1_DESI3D_PILOT=e1 CHROMIUM=/path/to/chromium FFMPEG=/path/to/ffmpeg node tools/monarchs-edit/desi-3d-explainer/render.mjs

# Mux optional voice-over audio (local file only — nothing is uploaded or sent)
TOP1_DESI3D_AUDIO=/path/to/narration.m4a TOP1_DESI3D_PILOT=e1 node tools/monarchs-edit/desi-3d-explainer/render.mjs
```

Output defaults to `.cache/monarch-desi-3d-explainer/` so channel assets never land in the public storefront folder. `TOP1_DESI3D_OUT` overrides the folder. MP4 output names are pilot-specific (`desi-3d-explainer-p1.mp4`, `desi-3d-explainer-e1.mp4`, `desi-3d-explainer-long.mp4`).

## The scenes, and what they must never claim

P1 — two labelled blocks, matching ice cubes, room temperature and a shared clock:

- The metal/lakri melt difference is **illustrative** — a direction, not a measurement. The frame carries a persistent `ILLUSTRATIVE 3D MODEL — NOT A TEST RESULT` badge and the reveal caption repeats the honest line.
- The 3D model is not a physics simulation of conduction, mass, time or temperature. No conductivity, force or temperature number is shown. No result is staged with synthetic footage.
- The physical P1 test (camera, real cubes, real timing, swapped sides, raw footage) is the only honest way to claim a result. Until it is done, the channel must describe the 3D explainer as an illustration and a first draft.

E1 — one warm paddle touching the same metal block and the same lakri/wood block:

- The paddle's emissive warmth drains via the timeline's curves: fast on metal, slow on wood, held cool mid-flight. Same honesty boundary as P1 — a direction, not a measurement.
- No temperature or conduction number is shown. The channel must describe E1 as an illustration, not a result.

Long-form — two wide blocks, the shared same-room clock, and an expanded arc (promise → early proof → mechanism → honest evidence → what this is not → payoff → identity):

- The scene and its camera are composed for 1280×720; the overlay layout and the 16:9 camera are pilot-specific (`view.layout`, `view.camera` in `scenarios.js`), not a rescaled 9:16. P1 and E1 are untouched and fall back to the original hardcoded 9:16 layout.
- Same honesty boundary as P1: the melt difference is a direction, not a measurement. The badge and the reveal caption stay.

## Scope

- Three pilots built: P1 (ice melt), E1 (warmth drain) and the long-form companion (16:9 · 92 s · the same premise as P1, expanded arc with evidence/honesty beats). Any further pilot should be added the same way — a new `e{N}/timeline.js` + `e{N}/scene.js` (or a `long/` pair) registered in `scenarios.js`, with its own Node test file.
- The long-form pilot is the first video in the 16:9 format — it is picture-only, no narration, no voice, no channel uploads. It inherits P1's honesty boundary: illustrative only, not a substitute for the physical run.
- No narration, voice, music, captions or channel uploads are produced here. The explainers are picture-only build sources; add narration locally, in the channel's own tools, after the owner approves the first draft.
- The scene stays separate from the Top1 storefront and from the Monarch Studio intro videos. It never appears in `public/demos/` or the site.
