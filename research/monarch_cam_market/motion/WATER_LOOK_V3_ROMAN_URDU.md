# Underwater look development v3

User ki lighting/camera/realism correction par actual 150-frame render execute hua.

Reproduce: `MONARCH_WATER_LOOK=1 PYTHONPATH=.local-motion python3 research/monarch_cam_market/motion/render_native_scene_study.py`

- 1280x720, 24fps, 6.25s; original voice unchanged; full FFmpeg decode pass.
- Humpback native LOD0: 40,212 vertices / 79,870 triangles, pehle 908 vertices thay.
- Optional linear-light surface shading, broad specular response, wavelength-dependent distance extinction; background light-shaft approximation. Physical volumetric scattering/path tracing ka dawa nahi.
- Camera angle lower, slow tracking/reframing aur slight push-in. Projection abhi orthographic hai, true perspective/dolly nahi.
- Output: out/water-look-v3/NATIVE_SCENE_VOICE_INTERNAL.mp4
- SHA256: 968a372f8b804dd7b845b33fcdda777543c621a8a2329387c819db4a3df4fd14
- Render time is machine par takreeban 22.6 minutes; future composition work full LOD0 sequence se pehle sparse samples par karna hai.

## Actual self-inspection
Frame 075 khol kar inspect hua. Surface smoothness, depth colour aur light direction improve hue. Lekin wide empty composition, weak subject separation, artificial-looking shafts aur dark animals abhi cinematic realism ko rok rahe hain. Yeh requested realistic quality tak nahi pohancha. Full moving-picture/audio independent review nahi hua; koi release gate clear nahi.

Agla correction: sparse-frame hero camera composition aur lighting balance pehle; perspective camera + stronger motivated key/fill aur meaningful near/far layering. Hunt target abhi unresolved hai. Fog/particles se storytelling ya anatomy ki kami hide nahi karni.

Validation: 103 tests pass; diff check pass. Existing diagnostic defaults unchanged; water look opt-in hai.
