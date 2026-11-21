# MONARCHs Edit — Desi 3D Explainer decision (2026-11-21)

**Owner decision · 2026-11-21 · overrides the checkpoint "no to changing MONARCHs Edit"**

The owner chose to merge the **Desi 3D explainer** into the **existing** Monarch Edit channel (@MONARCHsEdit / @monarchsedit). This is an explicit channel-direction change made after reviewing the separate-pilot recommendation in the 2026-11-20 screenshot checkpoint.

## What is decided

1. The Monarch Edit channel stops being only a Urdu motivation/personality channel.
2. The channel's identity becomes the **Desi 3D explainer**: everyday science and design, test-first, spoken Hindi–Urdu/Hindustani, with a clearly labelled 3D visual treatment.
3. The first pilot stays the audit's P1 — *Metal ya Lakri — Baraf Pehle Kahan Pighlegi?* (ice on metal vs wood) — presented as a 3D explainer.
4. The 3D explainer is the channel's shared visual treatment, not a separate channel or a pivot of the poster/identity.

## What is NOT decided or done yet

- **No pilot is launched.** No YouTube video is posted, scheduled, or updated. Nothing is published.
- **No physical test has been run.** The 3D scene is an illustrative model of the heat-transfer direction. It is **not** a measurement or a substitute for the physical run the audit requires (three paired runs, swapped sides, raw footage kept).
- **No narration, voice, music or captions have been recorded.** The explainer is a picture-only build source.
- **No rename, deletes or rebrand of the channel.** The Monarch Edit channel's name, about and uploads are outside this repo and were not touched.
- **No six-Short trial has been authorized.** The trial remains gated on the feasible P1/E1 offline results and the owner's go-ahead.

## Build source

The channel's two pilots are wired into the repo as an isolated 3D explainer:

```
tools/monarchs-edit/desi-3d-explainer/
  scenarios.js    — pilot registry (PILOTS, getPilot); P1 + E1 + the long-form companion
  p1/timeline.js  — pure P1 beat sheet, shared clock and illustrative melt curves
  p1/scene.js     — Three.js scene graph: 2 blocks (metal/lakri) + 2 ice cubes + heat arrows
  e1/timeline.js  — pure E1 beat sheet, shared clock, illustrative warmth-drain curves, paddle pose
  e1/scene.js     — Three.js scene graph: 2 blocks (metal/lakri) + one warm paddle with emissive warmth
  long/timeline.js — pure long-form beat sheet, shared clock, illustrative melt curves (16:9 · 92 s)
  long/scene.js    — Three.js scene graph: two wide blocks (metal/lakri) + 2 ice cubes + heat arrows
  main.js         — compositor + 2D caption layer (METAL/LAKRI labels, T+clock, TIME-LAPSE/touch markers, reveal)
  index.html      — compositor entry
  render.mjs      — headless render: stills (no ffmpeg) or full MP4 (ffmpeg required)
```

See the [build guide](../desi-3d-explainer/README.md) for render instructions and caveats.

## Scene boundaries (honesty)

- The scene is an **illustrative 3D model** — it is not a measurement of conduction, a simulation of the heat transfer, or a verified result.
- The metal/wood melt difference is a *direction*, not a rate. No temperature, force, or conductivity number is shown.
- Everything about the physical tests (P1, E1) is pending: a real camera, real cubes, real timing, raw footage and raw results kept. Until then, nothing in this channel may claim an observed outcome.
- The scene deliberately shows the two blocks at the same room temperature and the same clock. It does not stage the result with synthetic footage.

## The first long-form companion (16:9 · 92 s)

The first video in the long-form format is built as a `long` pilot — a genuinely fresh 16:9 build, not a rescaled short:

- **Frame:** 1280×720 (16:9), 92 s at 24 fps. Overlay layout (`view.layout`) and camera (`view.camera`) are pilot-specific in `scenarios.js`; P1/E1 are untouched and keep the original hardcoded 9:16 layout.
- **Beats:** 0–9s opening promise, 9–24s early proof (same room, same clock), 24–56s time-lapse mechanism, 56–68s honest evidence context (three paired runs, swapped sides, raw footage), 68–76s what this is not, 76–86s payoff + illustrative arrows, 86–92s identity outro.
- **Honest evidence beat:** the 56–68s window states what a real test needs (three paired runs, swapped sides, raw footage kept) — illustrative text, no numbers claimed.
- **Same honesty boundary as P1:** the melt difference is a direction, not a measurement. The badge and the reveal caption stay; nothing may claim an observed outcome.
- **What it is not:** picture-only, no narration, no voice, no music, no channel upload, nothing published. The long-form pilot inherits the P1 physical-run requirement.

## First pilot (P1) and direct explainer (E1)

| Beat | Content | Status |
| --- | --- | --- |
| 0–5s | Both choices visible. "Baraf pehle kahan pighlegi — metal ya lakri?" | 3D scene: present |
| 5–10s | Both blocks room temperature, same clock | 3D scene: present |
| 10–22s | TIME-LAPSE, synchronized clock, illustrative melt | 3D scene: present |
| 22–32s | Reveal: heat direction via arrows; honest illustrative caption | 3D scene: present |
| 32–38s | Identity outro | 3D scene: present |

E1 — *Metal Ka Chamach Zyada Thanda Kyun Lagta Hai?* — the matching direct explainer (one warm paddle, two blocks). **It is built** as the channel's second pilot, sharing the compositor and harness with P1 (selected with `?pilot=e1` / `TOP1_DESI3D_PILOT=e1`). Beats: 0–4s question ("Metal ka chamach zyada thanda kyun lagta hai?"), 4–10s setup (same room temp, one warm paddle), 10–18s touch on metal (warmth drains fast), 18–26s then touch on lakri (warmth drains slower), 26–32s honest reveal, 32–38s identity outro. The paddle touches the metal block, then the lakri block, with emissive warmth draining faster on metal — **still illustrative, not a measurement**; no temperature or conduction number is shown.

## Metrics gate (not filled until measured)

See `desi-3d-explainer-scorecard.csv` — rows are blank until the first physical run exists. Primary metric: engaged views at a matching 7-day age; guardrails: stayed-to-watch and APV. The 16:9 long-form companion is built as the first long-form pilot; it inherits the same physical-run requirement as P1/E1 and must not publish before one exists.
