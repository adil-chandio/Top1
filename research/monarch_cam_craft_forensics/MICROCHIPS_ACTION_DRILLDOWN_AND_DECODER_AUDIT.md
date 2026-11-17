# Microchips action windows — actual timestamped review and decoder correction

2026-11-14. Original https://www.youtube.com/watch?v=dX9CGRZwD-w . Research only, no Gecko production.

## Defect, correction, actual verification
Initial action run44088321358/source9e0e6d4 successfully transported18sheets but SHA256 audit found each window's three pages identical. Only24unique frame cells/window were available, NOT72. Opened all three pages for windows00/01 and first page of02–05:10files opened,6unique sheets/144cells. Other8files are hash-identical repeats, not additional temporal evidence. Its receipt dense_method72claim is superseded by this audit.

Cause consistent with FFmpeg4.x image-output timestamp synchronization duplicating the first tiled image after setpts adds a large seek offset. Corrected sourcef99952f4aef83b2b1a34d9130d5bc71492cdc2c7 adds output `-vsync 0` and rejects any window unless3timestamped pages have3distinct hashes. Run44088883088 SUCCESS; recovered18sheets all18hashes distinct. **All18corrected sheets actually opened**, six72consecutive-frame windows =432frame cells,14.4seconds total at30fps. The first24cells/window overlap the initial run: do NOT add144old cells as unique coverage. Survey/dense overlap also not additional unique time.

Decoder correction actually verified in Actions output and reviewed timestamp progression: e.g.05:46.000→05:46.767,05:46.800→05:47.567,05:47.600→05:48.367. This is displayed filter PTS+requested seek, not independent packet PTS/cut-boundary validation. Native ffmpeg9 local synthetic test could not exercise legacy `-vsync` (removed there); default ffmpeg9 produced3unique pages, so local synthetic did NOT reproduce4.x failure. Actual Actions corrected output, not that failed local test, is the success evidence. Corrected decoder is verified for Actions Ubuntu22.04 environment, not every FFmpeg version.

Source file matches prior Microchips hash3fc369f5a7ecb8c1bb7dc347862b201dcd391931552d3d404157f7ed3c40fb7e,854x480/30fps.320px frame cells improve labels vs prior200px survey but cannot certify original full-resolution fine-detail quality. No listening/nativeAV/every-native-frame completion, easing measurement or manufacturing-science validation.

## Actual observed local progression
|Displayed range|Observed change|Craft decision, limits|
|---|---|---|
|05:46.000–05:48.367|Complex copper-colored raised pattern gradually becomes a more uniform pale planar top. Substrate side edge remains continuous; blue Oxide Deposition step above. State completes then holds.|Before/during/after readable from one fixed base. Do not replace mechanism with a crossfade between unrelated views; exact manufacturing interpretation still schematic.|
|05:57.000–05:59.367|Green coat holds over substrate, workflow key moves. Around05:58.9 a small colored rectangle grows toward a patterned central region while camera stays almost fixed.|There is preparatory hold, then one localized change. Stable waiting is intentional; don't force a cut simply because little moves. No claim full pattern sequence ends here.|
|06:15.000–06:17.367|Etching-labeled close surface; fine longitudinal details continue, small surface/color change; main section bounds remain stable.|This probe is subtler than hoped and does not capture a dramatic full etch cycle. Need not manufacture a strong finding; use only as stable-reference evidence.|
|18:40.000–18:42.367|Purple projection volume spans gap between patterned plane and green slab; path/cycle key stays right; patterned upper plane stays separate.|Two scales/states share screen; kept gap/edges clarify relation. Mostly a sustained explanatory state, not a complete exposure/develop sequence.|
|19:01.000–19:03.367|Patterned green surface and side cutaway steady. Bright red/pale falling particles begin around19:01.6 and become denser while map stays visible.|Effect onset is staged after geometry established. Particles obscure some pattern at peak: Gecko must not bury the contact edge under effects. No inference of physical particle speed/count.|
|24:07.000–24:09.367|Substrate slides into lower foreground beneath separated die. Dense blue connection lines become visible across gap; camera approaches and lower patterned plane fills more frame.|Exploded relation remains spatially continuous; lines connect two known planes. Biological schematic must not borrow this as literal manufactured gecko wiring.|

## Changed treatment rules
- Show meaningful before→during→after geometry, then a brief clear hold. A glow/particle field cannot be the only indication that something happened.
- During toe release, preserve the wall/contact reference edge as these slabs preserve side boundaries.
- Teach solid silhouette/gap first (new locomotive03:11 review), then enlarge schematic detail with one retained landmark.
- Reduce opacity/overlays only when they reveal something necessary; do not compromise the mechanism silhouette.

## Retention/cleanup
Earlier73sheets source48f4e79:176temporary image-check payloads now independently verified cleared after resume run44087384602; receipts/text/local ignored images preserved. New9e0e6d4/292611b/f99952f payloads not yet cleared at this checkpoint. Clear only after appropriate coverage evidence preserved; do not silently erase unreviewed unique media. Duplicates can be classified by hashes without falsely marking individually viewed.
