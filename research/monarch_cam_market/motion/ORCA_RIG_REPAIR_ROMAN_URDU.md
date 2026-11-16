# Orca rig: actual investigation and bounded repair

## Problem ko guess nahi kiya

Pichhle numerical evaluator mein 7m static mesh ka animated extent hundreds of units ho raha tha. Three.js 0.180.0 ke actual GLTFLoader, AnimationMixer aur SkinnedMesh se same decoded asset evaluate ki. Same distortion reproduce hui. Python aur supported loader ke maximum displacement difference 0.001 model units se kam hai. Isliye issue sirf custom evaluator ki calculation kehkar dismiss nahi kiya.

## Source reading se correction

Pinned upstream `lib/scene/orca/loadOrcaMesh.ts` actually read kiya. Upstream static, world-baked, centered metric geometry return karta hai aur kehta hai rig separately add hogi. Asset licence confirms mesh geometry reoriented/scaled to 7m. Existing skin/clip ka metric compatibility establish nahi tha. Isliye pehle kaha gaya native animation ko preserve karna hi solution hai, woh assumption superseded hai. Purane importer ka rig discard karna apne aap root bug nahi.

Source: https://github.com/GilRaitses/orcastrike/blob/eb23633cb6779c0d81198fcd91d994b7c18653c3/lib/scene/orca/loadOrcaMesh.ts

## Actual candidate

Original project-authored eight-bone metric-space rig: six longitudinal bones, two pectoral bones. Smooth local weighting and dorsoventral tail articulation. Mesh rest geometry remains unchanged; bones/weights rebuilt in same metric space. Upstream custom rig source code not copied. Source mesh and texture remain credited CC-BY-4.0 work.

Supported Three.js skinning tests:
- 1,656 vertices evaluated.
- Bind pose maximum error below 1e-5.
- Nine time samples checked.
- No nonfinite output or explosive extent.
- Configured max extent ratio 1.5 and max displacement 1m sanity limits passed.

These broad numerical limits catch catastrophic defects, not correct anatomy or desirable acting. Not biologically measured joint positions. Source mesh's particular sex/body proportions must also be considered before cloning into pod.

## Actual visual inspection

Three deformed mesh poses rasterized with source texture and opened in image tool. Body proportions retained; tail pose changes without previous size explosion. CPU face-average texture renderer is coarse, faceted and not a final lookdev renderer. No full-motion viewing, sound, independent artistic/anatomical approval claimed.

## Reproduce

```
python research/monarch_cam_market/motion/fetch_opening_assets.py
npm install --prefix research/monarch_cam_market/motion/out/tools --ignore-scripts --no-audit --no-fund @gltf-transform/core@4.4.0 @gltf-transform/extensions@4.4.0 meshoptimizer@0.25.0 three@0.180.0
node research/monarch_cam_market/motion/decode_orca.mjs
node research/monarch_cam_market/motion/crosscheck_orca_loader.mjs
node research/monarch_cam_market/motion/test_metric_orca_rig.mjs
PYTHONPATH=.local-motion python3 research/monarch_cam_market/motion/render_rig_poses.py
```

Python render requires existing `requirements-layout.txt` dependencies. Generated media, installed packages and recovered source assets stay ignored. Source geometry licence/attribution in `ATTRIBUTION-ORCA.md`; inspection output carries attribution. Package versions are pinned and lifecycle scripts disabled; no claim of exhaustive package security audit.

## Execution boundary

This repair is a testable rig candidate for upcoming native-mesh staging. It does not advance coordinator stages or clear actual reference AV, integrated short-test, listening or independent-review gates. No user approval requested. Original broken clip remains intact for rollback/comparison. Neither distorted native skin nor flat CPU diagnostic is promoted as final animation.

## Animated asset export continuation

Candidate now exports `out/orca/orca_metric_rig.glb`, retaining original embedded source images, material, UV and geometry. Original metric skeleton/weights and a six-second sampled clip replace incompatible legacy animation. Reimport through actual Three.js loader evaluates 144 frames; max vertex disagreement below 1e-4. Original source GLB unchanged.

Official Khronos validator added (`gltf-validator@2.0.0-dev.3.10`, npm lifecycle scripts disabled). Initial schema findings—empty children arrays, nonzero joint indices at zero weights and mesh-root structure—were corrected. Latest result: zero errors, zero warnings, 11 informational unused old-accessor notices. Old unused buffer/accessor data retained; not hidden as a clean/no-notices result.

Actual six-second textured motion diagnostic rendered from evaluated skin geometry at 24fps. CPU rasterizer now interpolates texture UVs per pixel with a depth buffer, instead of coloring each face from one texture sample. Simple lighting remains diagnostic, not cinematic lookdev. Fixed-camera sample stills actually opened. No audio or independent full-motion review claimed.

Reproduce additions:
```
node research/monarch_cam_market/motion/test_metric_orca_rig.mjs
npm install --prefix research/monarch_cam_market/motion/out/tools --ignore-scripts --no-audit --no-fund --save-exact gltf-validator@2.0.0-dev.3.10
node research/monarch_cam_market/motion/validate_metric_asset.mjs
PYTHONPATH=.local-motion python3 research/monarch_cam_market/motion/render_metric_motion.py
```

Latest structured receipt: `ORCA_ANIMATED_ASSET_RECEIPT.json`. Generated GLB/video and dense pose arrays remain ignored. Integrated animal-scene/audio proof and independent review remain separate from this engineering result.

## Shared native scene continuation

`render_native_scene_study.py` renders two repaired native orca meshes and the pinned Tidewater humpback in one world, with shared depth buffer and independent trajectories. Humpback native part/span tags drive restrained pectoral and vertical caudal deformation; low LOD deliberately limits diagnostic cost. Original recovered narration attached unchanged for 6.25-second working timing. No background score/effects added. Full decode passed.

Producer actually opened v1 still sheet: opposite movement readable, but hunt target absent and cloned orca poses too synchronized. V2 uses .85-second offset evaluated continuously (no modulo wrap), smaller far individual and different trajectory. Missing prey and non-final lighting remain explicit defects; cannot approve complete hunt storytelling from this render. No claim of actual listening or independent review.

Reproduce after asset recovery/tool setup and original voice recovery:
```
node research/monarch_cam_market/motion/test_metric_orca_rig.mjs
PYTHONPATH=.local-motion python3 research/monarch_cam_market/motion/render_native_scene_study.py
```

Renderer-specific actual checks: draw order does not change occlusion, nearer surface wins. Current tracked receipt `NATIVE_SCENE_STUDY_RECEIPT.json`; generated media/trajectories/attribution copies in ignored `out/native-scene-v2`.
