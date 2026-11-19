# Gecko WebGL film — concept

12-second vertical English visual concept. Original procedural Three.js geometry and animation, frame-by-frame headless Chromium rendering, and FFmpeg H.264/AAC encoding. The simple synthesized background tone is original; there is no voiceover. It is not a realistic animal, an anatomical/physical simulation, or a finished science film. It does not pass the outstanding Batch 2 asset, reference and scientific-visual proof gates.

## Render

Install Node dependencies with `npm ci`; install FFmpeg with libx264 and AAC, plus a compatible headless Chromium and its system libraries. Set `CHROMIUM` to its executable and optionally `FFMPEG` to the FFmpeg executable, then run `npm run render`. The output is `output/gecko-webgl-concept.mp4`. Set `GECKO_STILLS=1` to render seven JPEG review frames instead. The renderer uses a temporary Vite build and captures deterministic frames at 24 fps, matching the broad Monarch Studio workflow, not the original studio project itself.

## QC

Rendered 288 frames, 540×960, 24 fps, 12 seconds, H.264 and stereo AAC; both streams decoded to completion with FFmpeg. Reviewed stills at 2, 8, and 11 seconds. Gecko and microscopic branching are stylized and simplified; the foot motion is approximate. Audio was generated and decoded, not listened to. This is a concept, not Batch 2 completion.
