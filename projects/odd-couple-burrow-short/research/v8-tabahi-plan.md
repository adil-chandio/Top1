# V8 Tabahi Plan — Odd Couple Burrow

## Sources reviewed
- `/tmp/ref_anim` (artemnovitckii/claude-animation-skills): local Three.js/Playwright animation skills. `zach-d-films` engine = procedural 3D cartoon explainer (`shots.js`, `human.js`, `props.js`, `anim.js`, `main.js`, `render.mjs`). Uses `renderAt(t)`, shot-based timeline, captions, camera shake/ripple, VO-timed cuts.
- `/tmp/ref_zack` (Anil-matcha/zack-d-films-ai-video-generator): MuAPI/Veo-based AI pipeline (external API dependent, not runnable in-sandbox). Useful methodology: curiosity-loop script, 2 shots/beat, 2-4s cadence, camera variance, zoom impacts, character consistency sheets, 3D SSS/clay/Zack D style, ffmpeg transitions/shakes/captions.

## Sandbox-realistic V8 approach
- Keep Three.js + Chromium SwiftShader + ffmpeg + V6 SDK postfx pipeline.
- No MuAPI/Veo/external AI video APIs. Visuals are procedural 3D + GLB kitbash + PBR materials + postfx.
- Add BGM/SFX layers in ffmpeg (drones, risers, hits, whooshes, heart pulse, flood rumble) mixed under VO.

## Beat map (script-locked)
1. Hook (0-3s): "This rock holds two animals" — macro rock push-in, dust, shock caption, impact SFX.
2. 250M years ago (3-6s): time plunge, curled sleeper reveal, warm dormancy light.
3. Mammal relative beside amphibian (6-9s): two-shot reveal, split-lighting teal/amber.
4. Wait. Not enemies (9-11s): hard cut, dolly zoom, silence/vacuum, red/teal pulse.
5. Ribs healing, no bite marks (11-15s): macro cross-section feel, healing glow markers, scan sweep.
6. Not a hunt (15-17s): wide reality check, label card.
7. Crawled in for shelter (17-20s): likely-story reenactment ghost pass, inference label.
8. Aestivation/deep dormancy (20-24s): calm breathing, cool dormancy palette, plausible label.
9. Flood filled burrow (24-28s): water rise, debris, rumble, seal.
10. Clue the rock kept / loop (28-29.94s): return to opening rock frame for seamless loop.

## Cinematic upgrades
- Camera: push-in, crane, dolly zoom, macro snap, handheld drift, impact shake, smooth ease curves.
- Characters: higher-detail procedural skeletons (skull/jaw/vertebrae/ribs/pelvis/limbs), bone PBR, emissive scan, healing markers.
- Environment: layered rock strata, burrow cutaway, sediment floor, debris, fog volumes, light shafts.
- Postfx: ACES, bloom/halation, vignette, grain, chromatic aberration subtle, teal/orange grade, crushed blacks.
- Audio: VO + ambient drone + whoosh/hit/rumble SFX + subtle pulse; -14 LUFS target, -1 dBTP.
- Captions: kinetic, safe-area, high contrast, 1-3 words/line where possible.
