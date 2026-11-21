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

The channel's first pilot is wired into the repo as an isolated 3D explainer:

```
tools/monarchs-edit/desi-3d-explainer/
  timeline.js   — pure beat sheet, shared clock and illustrative melt curves
  scene.js      — Three.js scene graph: 2 blocks (metal/lakri) + 2 ice cubes + heat arrows
  main.js       — compositor + 2D caption layer (METAL/LAKRI labels, T+clock, TIME-LAPSE, reveal)
  index.html    — compositor entry
  render.mjs    — headless render: stills (no ffmpeg) or full MP4 (ffmpeg required)
```

See the [build guide](../desi-3d-explainer/README.md) for render instructions and caveats.

## Scene boundaries (honesty)

- The scene is an **illustrative 3D model** — it is not a measurement of conduction, a simulation of the heat transfer, or a verified result.
- The metal/wood melt difference is a *direction*, not a rate. No temperature, force, or conductivity number is shown.
- Everything about the physical test (P1) is pending: a real camera, real cubes, real timing, raw footage and raw results kept. Until then, nothing in this channel may claim an observed outcome.
- The scene deliberately shows the two blocks at the same room temperature and the same clock. It does not stage the result with synthetic footage.

## First pilot (P1) and direct explainer (E1)

| Beat | Content | Status |
| --- | --- | --- |
| 0–5s | Both choices visible. "Baraf pehle kahan pighlegi — metal ya lakri?" | 3D scene: present |
| 5–10s | Both blocks room temperature, same clock | 3D scene: present |
| 10–22s | TIME-LAPSE, synchronized clock, illustrative melt | 3D scene: present |
| 22–32s | Reveal: heat direction via arrows; honest illustrative caption | 3D scene: present |
| 32–38s | Identity outro | 3D scene: present |

E1 — *Metal Ka Chamach Zyada Thanda Kyun Lagta Hai?* — is the matching direct explainer (one warmer hand, two blocks). It is **not built yet**; the 3D source is reusable.

## Metrics gate (not filled until measured)

See `desi-3d-explainer-scorecard.csv` — rows are blank until the first physical run exists. Primary metric: engaged views at a matching 7-day age; guardrails: stayed-to-watch and APV. The 16:9 long-form companion is explicitly out of scope until after the short-format confirm tests.
