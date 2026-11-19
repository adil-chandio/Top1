# Monarch Studio

A separate film and production-notes space within Top1, served at **`/monarch-studio/`**. It has its own HTML entry point, styles, and player; the Top1 Kits storefront stays at `/`.

## Project 001 — Who Crushed the Can?

- [Production notes](./PRODUCTION.md): the actual script-to-render workflow, tooling, and verification.
- [Script, shot plan, and reference study](../public/samples/air-crush-blueprint.md): Roman Urdu narration, 11 cuts, and an editable production brief.
- [Published film](../public/demos/air-crush-cinema-edition.mp4) and [poster](../public/demos/air-crush-cinema-edition.webp): the same files used in the storefront. This folder does not store a second copy.
- [`src/air-crush.js`](../src/air-crush.js): the shared film metadata, chapter cues, and caption timing. `stills/` contains three small crops from the encoded film for the studio's shot guide.

Run `npm ci` and `npm run dev` at the repository root, then open `/monarch-studio/`. `npm run build` builds the studio and storefront together; serve `dist/` at the root of a static site with index.html directory resolution. Playback and downloads do not require an account or backend.
