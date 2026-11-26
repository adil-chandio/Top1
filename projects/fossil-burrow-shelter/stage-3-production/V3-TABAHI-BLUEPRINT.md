# Fossil Burrow Shelter — V3 "Tabahi Next Level" Blueprint

## Sources reviewed (repo + external)
- **claude-animation-skills** (`/tmp/claude-animation-skills`, cloned from `artemnovitckii/claude-animation-skills`)
  - Useful patterns: shot-based deterministic director (`update(t)` depends only on time), poseable character rig helpers, prop/effect primitives, slow-motion impact beats, camera shake, DOF/bloom, 1-3 word captions timed to VO, 2-4s cuts, hook→misconception→"But" twist→build→payoff structure (`skills/zach-d-films/SKILL.md`).
  - Render pattern: spec/shot code -> headless Chromium/Playwright -> frame capture -> ffmpeg.
- **zack-d-films-ai-video-generator** (`/tmp/zack-d-films-ai-video-generator`, cloned from `Anil-matcha/zack-d-films-ai-video-generator`)
  - Useful patterns: curiosity-loop script (every line opens a micro-question), 2 shots per beat (wide establishing + macro/detail/cross-section), camera motion variance, 2-4s pacing, zoom-in on key beats, transition/impact editing (`SKILL.md`, `references/beat-layer.md`).
  - Not directly usable as 3D renderer (AI keyframe/video pipeline), but storytelling/beat grammar is directly applicable.
- **Existing Top1 V6 IMAX pipeline**
  - `tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs` - Vite + Playwright Chromium SwiftShader + raw RGBA WS + ffmpeg plates + preflight/QA.
  - `tools/monarch-cockroach/short_v6/*` - gold reference: deterministic page hooks (`__READY__`, `renderFramePNG`, `renderCoverPNG`, `connectRawWS`, `streamFramesWS`, `measureLoopSeamMAE`), audio build with EBU R128, captions/voice lock, 12-beat QA sheet.
  - Current fossil V2: `projects/fossil-burrow-shelter/stage-3-production/{page_v6.html,director_v6.js,titles_v6.js,build_audio_v6.py}`.

## Creative target (user brief)
"Zack Snyder-esque / tabahi next level": cinematic 3D, high contrast, volumetric light, dramatic camera, premium materials, living/non-living motion, SFX/eargasm, storytelling psychology, hook in <1s, no boring dead frames, every second advances story.

## Script lock (10 beats)
1. "This rock holds two animals." (HOOK)
2. "Two hundred fifty million years ago, one curled up asleep." (TIME/INTIMACY)
3. "It was a mammal relative, beside an amphibian." (IDENTITY)
4. "Wait. They were not enemies." (TWIST INTERRUPT)
5. "The amphibian's ribs were healing, with no bite marks." (EVIDENCE)
6. "So this was not a hunt." (REFRAME)
7. "The likely story: it crawled in for shelter." (RECONSTRUCTION)
8. "The other was probably in aestivation, a deep dormancy." (SCIENCE DETAIL)
9. "Then a flood filled the burrow and sealed them." (DISASTER)
10. "That is the clue the rock kept." (PAYOFF/LOOP)

## V3 shot plan (2 shots per beat = 20 shots, 35s / 1050f @30fps)

| # | Beat | Time | Shot A (wide/establish) | Shot B (macro/detail) | Camera | SFX/VFX |
|---|---|---:|---|---|---|---|
| 1 | Rock holds two animals | 0.0-2.5 | Extreme macro rock surface, dust motes, razor light slice | Push through crack into dark burrow void | Crash push-in + micro shake | Stone scrape, deep sub hit, dust sparkle |
| 2 | 250M years ago, curled asleep | 2.5-5.5 | Burrow wide, warm/cool split, mammal relative curled | Macro breathing rib/shoulder, eye twitch | Slow dolly + breathing parallax | Low drone, heartbeat-soft pulse, sand grains |
| 3 | Mammal relative beside amphibian | 5.5-8.5 | Two-body composition, clear silhouette separation | Face/skin texture contrast insert | Arc left-to-right | Creature breath layers, subtle insect ambience |
| 4 | Wait. Not enemies | 8.5-10.8 | Hard interrupt: camera slam, red/warm alarm contrast | Eye line between them, no aggression posture | Snap zoom + whip pan | Record-stop/vacuum drop, reverse riser, impact whoosh |
| 5 | Ribs healing, no bite marks | 10.8-15.0 | Amphibian side profile, clinical moonlight | X-ray rib scan, healed callus glow, bite-mark absence overlay | Probe dolly + macro orbit | X-ray sweep, crystalline ping, soft medical hum |
| 6 | Not a hunt | 15.0-17.2 | Pull back to peaceful coexistence frame | Claw/teeth relaxed detail, no blood | Slow crane up | Tension release, warm pad swell |
| 7 | Crawled in for shelter | 17.2-21.0 | Flashback reconstruction: injured amphibian entering burrow mouth | Foot/limb dragging over sand, rain outside | Tracking follow + handheld micro | Rain, wind, wet stone, limb drag foley |
| 8 | Other in aestivation | 21.0-24.5 | Mammal curled in deep dormancy chamber | Dust settling on fur, slow breath, heartbeat graph-like pulse | Locked macro + gentle push | Low heartbeat, dry air, cave reverb tail |
| 9 | Flood filled burrow, sealed them | 24.5-30.5 | Water surge entering burrow, debris/sediment chaos | Mud/silt particles burying bodies, bubbles, last light | Handheld chaos cam + upward crane escape | Water roar, sub boom, debris hits, muffled underwater tail |
| 10 | Clue the rock kept | 30.5-35.0 | Return to present rock slab, serene fossil reveal | Macro fossil imprint/detail, title lockup | Hero pull-back to loop-clean frame | Score resolve, stone ring, wind fade to loop seam |

## Technical upgrade plan (V3)

### A. Visuals / 3D
- **Creatures**: replace primitive spheres/boxes with higher-detail procedural rigs (segmented spine, scapula/pelvis hints, jaw articulation, breathing, blink, subtle idle). Evaluate CC0 GLB kitbash for rocks/bones/debris; keep story-specific creatures procedural if no matching GLB.
- **Environment**: layered burrow geology (strata, cracks, roots, pebbles), wet/dry material variants, water plane with animated normals, sediment volume, dust motes with depth.
- **Lighting**: key/rim/fill motivated by "moonlight through crack" + warm interior bounce; lightning/rain exterior for shelter beat; volumetric light shaft (shader/fake godray mesh) with dust scattering.
- **Materials**: roughness/normal variation, wetness map during flood, subsurface-ish fake for flesh (rim + emissive tint), bone/fossil matte.

### B. Camera / editing
- Deterministic shot scheduler with per-shot camera grammar: crash push, dolly, arc, snap zoom, probe macro, crane, handheld noise (seeded), whip pan.
- 2-4s cuts, no dead hold >3s without internal motion.
- Impact frames: 2-3 frame exposure punch + chroma/radial blur on twist/flood.
- Loop-clean end frame: final 5 frames blend/lock to frame 0.

### C. Audio/SFX (eargasm but VO-first)
- Keep `voice-01` VO clean and dominant (-14.2 LUFS integrated, -1.0 dBTP max). 
- Add layered SFX: stone, cave wind, breaths, heartbeat, x-ray sweep, vacuum drop at "Wait.", rain/flood roar, debris, bubbles, fossil chime.
- Sidechain ducking under VO; transient impacts aligned to beat cuts.
- Keep captions burned-in, high contrast, mobile-safe, 80% readable muted.

### D. Render/perf
- Keep V6 CLI/WS/plate pipeline; 720p render + 1080p lanczos upscale for speed, optional 1080p hero pass.
- 10-14 chunks, 2 workers (CPU cap). Preflight QA sheet mandatory before full render.
- Verify: ffprobe duration/fps/frames, decoded frame count, black frames, loop seam, loudness/TP, no missing captions.

## Production gates
1. **Storyboard lock** - shot list + camera + SFX + caption map approved.
2. **Lookdev preflight** - 12-beat QA sheet, no black/muddy frames, creatures readable.
3. **Audio pass** - VO lock, SFX/music, loudness QA.
4. **Full render + QA** - decoded proof, loop seam, audio peaks.
5. **Delivery** - present MP4, upload Drive, share link.

## Immediate next actions
- [ ] Upgrade `director_v6.js` into V3 shot scheduler with 20-shot beat map.
- [ ] Add SFX build pass (`build_audio_v3.py` or extend v6 builder) with beat-aligned impacts.
- [ ] Add macro insert rigs (rib x-ray, fossil imprint, water/sediment sim layers).
- [ ] Run 12-beat preflight QA, iterate, then full 720p->1080p render.
- [ ] QA + Drive upload + present.
