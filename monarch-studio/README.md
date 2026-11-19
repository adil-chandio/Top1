# Monarch Studio

A separate film and production-notes space within Top1, served at **`/monarch-studio/`**. It has its own HTML entry point, styles, and player; the Top1 Kits storefront stays at `/`.

## Project 001 — Who Crushed the Can?

- [Production notes](./PRODUCTION.md): the actual script-to-render workflow, tooling, and verification.
- [Script, shot plan, and reference study](../public/samples/air-crush-blueprint.md): Roman Urdu narration, 11 cuts, and an editable production brief.
- [Published film](../public/demos/air-crush-cinema-edition.mp4) and [poster](../public/demos/air-crush-cinema-edition.webp): the same files used in the storefront. This folder does not store a second copy.
- [`src/air-crush.js`](../src/air-crush.js): the shared film metadata, chapter cues, and caption timing. `stills/` contains three small crops from the encoded film for the studio's shot guide.

Run `npm ci` and `npm run dev` at the repository root, then open `/monarch-studio/`. `npm run build` builds the studio and storefront together; serve `dist/` at the root of a static site with index.html directory resolution. Playback and downloads do not require an account or backend.

## Project 002 — The Light With No Battery

- **Screening:** `/monarch-studio/reflector/`. The 50-second film is separate from the 29-second Project 001 master. Both projects load their own video only after a tap.
- [Worked script and 18-shot plan](../public/samples/reflector-blueprint.md) · [visual reference audit](../public/samples/reflector-reference-audit.md) · [1,200-frame measurements](../public/samples/reflector-reference-frames.csv). These research files describe the Dailymotion reference; they do not contain the source imagery or audio.
- [Published film](../public/demos/reflector-no-battery.mp4) and [poster](../public/demos/reflector-no-battery.webp). The three crops under `reflector/stills/` come from the original 002 render, not from the research reference.
- [`src/reflector.js`](../src/reflector.js) holds the production timeline. The path geometry is in [`reflector-optics.js`](../tools/demo-render/reflector-optics.js), scene composition in [`reflector-film.js`](../tools/demo-render/reflector-film.js), and the on-device-readable caption layout in [`reflector-titles.js`](../tools/demo-render/reflector-titles.js). These modules are for offline frame generation, not the studio viewer.
- To reconstruct the finished film, run `CHROMIUM=/path/to/chromium FFMPEG=/path/to/ffmpeg npm run render:demos -- reflector`. The edited voice stem and procedural score are local; a Dailymotion connection, voice API, or Actions runner isn't needed. When software rendering, the default scene plate is 720×1280, composited with text at 1080×1920. Use `TOP1_FULL_QUALITY=1` for native-resolution scene rasterization. This doesn't change the 50-second timeline.

### Project 002 master verification

- **MP4:** `19,556,300` bytes; SHA-256 `78aeecaab90a5eed6cc22df6c95ed0c9b4f9a20ac100b98e477168de9fe1087f`.
- **Delivery:** 50.000 s picture and sound, 1,200 frames at 24 fps, 1080×1920. H.264 High Level 4.0 / 4:2:0 / limited-range BT.709 and AAC-LC stereo at 48 kHz. `moov` before `mdat` for fast start. Full picture and sound decode passed. The decoded mix measured −14.5 LUFS integrated, 3.2 LU range and −1.8 dBTP.
- **Picture review:** decoded selects from all 18 setups and adjacent frames around the three bounces, the side move and the lamp-off comparison. In the same overhead setup, a beam-region luma measurement fell from 34.4 to 19.6 on an 8-bit scale when the lamp was turned off. That checks the rendered contrast only, not road illuminance.
- **Site:** 30 tests and production build passed. Preview accepted an `.e2b.app` Host header, preserved query strings on both directory redirects, and served `206` byte ranges for the master. Chromium's Pixel 7 emulation played the film inline with unmuted audio, sought via the proof and full chapter list, reached 50.00 s, and saved the exact master bytes. Also checked no-JS/error fallbacks, 320–1440 px layouts, builder prefill, and Project 001 playback. This is not a physical Android device test or a production hosting check.

Run `FFMPEG=/path/to/ffmpeg FFPROBE=/path/to/ffprobe node tools/verify-reflector.mjs` to repeat the master verification against the committed file.
