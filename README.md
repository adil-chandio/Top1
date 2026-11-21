# Top1 Kits

A mobile-first prototype for a storefront selling original prompt workflows and offering custom Shorts plans. It is a prompt shop, not a video editor or a hosted AI service.

## Run it

Use Node.js 22.12+.

```sh
npm ci
npm run dev
npm test
npm run build
```

The dev server binds to `0.0.0.0` and accepts Arena's `*.e2b.app` preview host. The production build is static and can be served at the root of a static site from `dist/`. There are no API keys, calls to a paid AI service, or a database. Fonts and artwork are served with the app.

## Try it on Android

1. Open the Arena preview in Chrome. Select **Watch Cinema Cuts** to play a film, or **Build a free prompt** to start from a topic.
2. Pick a topic, language, format, and length, then select **Build my prompt**. Copy it into your AI chat or save a `.txt` copy. Use the copy selection fallback if the browser blocks clipboard permissions.
3. View **The 25-Second Script** to download the original prompt and the hand-written example (`public/samples/25-second-short.md`). Explore the Starter Kit to see its outline and sample.
4. Under **Custom Work**, create a brief and copy or save it. The brief is composed locally and is never sent in the prototype.

## What to do before selling

1. Validate the first offer: give a few creators the free sample, ask them to produce a Short, and find out which part saved time or needed revision.
2. Finish the six workflows outlined on the kit page. Test them on several different topics in both languages. Prepare a setup guide, editable prompt files, examples, and plain-language license/refund terms. Keep the premium files out of the public site and any public repository.
3. Pick a price and a contact channel for custom work. Start with a clearly scoped service (script, shot plan, captions; no rendered video). Add a real delivery/communication channel before claiming the brief has been sent.
4. After checking seller eligibility, payout options, and fees for a payment provider, add a real checkout. Deliver premium files only after payment is verified on the server or by the provider; don’t put a paid download behind a frontend-only flag. Test the payment and fulfilment flow before opening it.

This preview has **no live checkout, customer accounts, or order submissions**. The storefront and builder can be hosted statically; a permanent domain, payment fees, and the AI chat chosen by the customer may have separate costs.

## Monarch Studio

[Monarch Studio](monarch-studio/) is a separately branded screening and production space at **`/monarch-studio/`**. The first project is *Who Crushed the Can? — Cinema Edition*, with the original film, 11 playable chapter cues, the Roman Urdu transcript, and [detailed production notes](monarch-studio/PRODUCTION.md). Open it from **Open Monarch Studio** on the homepage or from the can film's player. Project 001 shares the original MP4 and blueprint with the storefront rather than duplicating them. The store, kit preview and prompt builder remain at their existing routes.

**Project 002 — [The Light With No Battery](monarch-studio/reflector/)** is a finished 50-second Urdu film about bicycle reflectors, at `/monarch-studio/reflector/`. Open the **NEW 002** link on the homepage or the new project card inside Monarch Studio. It has 18 chapter cues and an [editable worked example](public/samples/reflector-blueprint.md). The separate [Dailymotion visual audit](public/samples/reflector-reference-audit.md) covers the 1,200 decoded source frames, with [numerical measurements](public/samples/reflector-reference-frames.csv) and no third-party imagery. The original reflector and corner-cube model are animated in Three.js; the road brightness is illustrative, not a visibility test.

## Monarch Edit channel — Desi 3D explainer

The Monarch Edit channel (@MONARCHsEdit) is now a Desi 3D explainer: everyday science and design, test-first, spoken Hindi–Urdu, with a clearly labelled 3D visual treatment. Two pilots are built: P1 — *Metal ya Lakri — Baraf Pehle Kahan Pighlegi?* (ice on metal vs lakri/wood) and E1 — *Metal Ka Chamach Zyada Thanda Kyun Lagta Hai?* (the warm paddle touches metal, then lakri/wood). The build source lives at [`tools/monarchs-edit/desi-3d-explainer/`](tools/monarchs-edit/desi-3d-explainer/) with the decision record in [`tools/monarchs-edit/research/MONARCHS-EDIT-DESI-EXPLAINER-2026-11-21.md`](tools/monarchs-edit/research/MONARCHS-EDIT-DESI-EXPLAINER-2026-11-21.md).

Both rendered scenes are **illustrative models, not test results**: the melt difference and the warmth-drain difference are directions, not measurements. No physical test has been run, and no video is published. Physical P1 and E1 (three paired runs, swapped sides, raw footage) are required before any result may be claimed; the blank scorecard is [`desi-3d-explainer-scorecard.csv`](tools/monarchs-edit/research/desi-3d-explainer-scorecard.csv).

Each pilot renders through the same compositor and harness — select it with the `pilot` query param (compositor) or `TOP1_DESI3D_PILOT=p1|e1` (render harness). Stills write to `.cache/monarch-desi-3d-explainer/`; MP4s are named `desi-3d-explainer-p1.mp4` / `desi-3d-explainer-e1.mp4`.

## Extinct Studio OS — production foundation

The architecture behind every Monarch video (per the 2026-11-21 strategic review — A–Z / closed-loop): a shared, zero-dependency production substrate. It is **build source — not a published pipeline**: no publish, upload, or silent publication.

```
tools/extinct-studio/
  schemas/          — 14 JSON schemas for project records (project, research, claims,
                      rights, story, shot-plan, proof-receipt, voice-lock, render-manifest,
                      audio-qa, video-qa, packaging, release-status, idea-scorecard)
  validate.js       — zero-dependency JSON Schema validator (subset, explicit)
  state-machine.js  — 15-state formal lifecycle (idea → published) + dependency DAG
  scorecard.js      — 100-point idea scorecard + production-candidate gates
  claims-rights.js  — claims classification (8 categories) + rights manifest rules
  qa-skeleton.js    — automated QA skeleton (honest status reporting)
```

- **State machine**: forward-only, receipt-gated, never sets `published` from tool code.
- **Idea scorecard**: 100 points; `production-candidate` requires a strong score + every gate green; an idea with zero visual proof potential is rejected.
- **Claims/rights manifest**: every narration line classified (no "animation = real footage"); every third-party source separately checked ("free download" is not a license).
- **QA skeleton**: honest `unavailable` statuses — real probe results inject via `probeOverrides`; never a fake pass.

The Desi 3D explainer (P1 + E1) stays scoped to its own channel files; this foundation is the shared substrate, not a replacement.

## Original cinema cuts

**Cinema Cuts** on the homepage plays four original 9:16 films. The gallery requests just the posters; the 24 fps H.264/AAC video loads on play (1080 × 1920 for the Lab Cinema Edition, 720 × 1280 for the other films). The narrated Lab film plays with sound when tapped; the other examples start muted. The homepage opens the featured cut directly, and the player’s shot guide seeks to the standout shots. Each companion prompt contains the visual direction without implying that the builder renders a movie.

The MP4/WebP pairs in `public/demos/` are the required delivery files. The Lab feature uses the distinct `air-crush-cinema-edition` filename. The cinema-cut filename separates these exports from the original preview clips. The three original Cinema Cuts each have three camera setups, depth-based focus, optical effects, captions, and an original stereo score/Foley mix. The phone's falling blocks are a visualization, not real parts inside a device. Halo is a fictional product with a damped mechanical hinge. The probe follows a time-compressed Keplerian path; its signal is visualized for the fictional story.

**Top1 Lab 01 — Who Crushed the Can? (Cinema Edition)** is a 29-second Urdu explainer with baked kinetic Roman Urdu captions. The featured player offers a [script, timed shot list, editable prompt and reference study](public/samples/air-crush-blueprint.md). The can's real opening and cutaway stay consistent through 11 setups. The new cut uses a rim-mounted lift/flip rig, fixed rolled lid, multi-stage shell buckle, displaced water, splash crown, ballistic droplets and restrained pressure cues. The close-ups use depth focus; faster motion uses two within-shot sub-exposures. No persistent labels, cards or progress bar. The motion is explanatory, not a finite-element or fluid-simulation result. Narration is a local, edited stem at `tools/demo-render/audio/air-crush-vo.m4a`, mixed on rebuild with `tools/air-crush-score.mjs`; no voice service is needed to rebuild it.

`tools/demo-render/` contains the 3D sets, textures, shutter/focus look, and motion models. `tools/soundtrack.mjs` synthesizes the soundtracks. Use local Chromium and FFmpeg with libx264, AAC, and WebP support to rebuild the assets:

```sh
CHROMIUM=/path/to/chromium FFMPEG=/path/to/ffmpeg npm run render:demos
CHROMIUM=/path/to/chromium FFMPEG=/path/to/ffmpeg npm run render:demos -- air-crush
CHROMIUM=/path/to/chromium FFMPEG=/path/to/ffmpeg npm run render:demos -- reflector
```

Rendering builds an isolated Three.js compositor in scratch space; no shop server or outside service is required. The default balances software render time and output detail (the Cinema Edition composites captions at 1080 × 1920 over a 691 × 1229 3D plate). Set `TOP1_FULL_QUALITY=1` for native-resolution 3D rasterization, `TOP1_STILLS=1` for shot-review stills (`TOP1_STILL_TIMES` optionally selects comma-separated seconds), or `TOP1_RENDER_OUT` to review renders in another folder before publishing. The shop only serves the final files and never runs the compositor.
