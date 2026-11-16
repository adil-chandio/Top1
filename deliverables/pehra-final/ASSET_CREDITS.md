# PEHRA 15s Preview — Asset & Audio Credits

## Visual pipeline

All 450 picture frames are animated **Blender 4.2 LTS / Cycles CPU path-traced 3D renders**. There are **zero still-image plates, zero flat backgrounds, and zero 2D cutouts** in the scene. Editorial captions are generated as transparent motion-graphic text overlays after rendering.

Rendering features: AgX view transform, OpenImageDenoise, volumetric midnight fog, shallow depth of field, motion blur, animated practical lights, real geometry displacement, dust motes, and compositor fog-glow.

## Poly Haven — CC0 photogrammetry / PBR assets

Downloaded at render time from `https://api.polyhaven.com/files/<id>` and `https://polyhaven.com/a/<id>`:

| Asset ID | Use in PEHRA |
| --- | --- |
| `sweet_potato` | Earthy tubers in the midnight field and the overflowing basket |
| `Lantern_01` | Swinging foreground hurricane lantern |
| `street_lamp_01` | 1786 Paris guard-yard lamp post |
| `bolt_action_rifle_7_62` | Guard rifle / bayonet silhouette detail |
| `chess_set` | Mirror-black chess board and marble pieces |
| `wooden_candlestick` | MONARCH and basket practical candles |
| `wicker_basket_01` | Golden-lit potato basket in the final shot |
| `marble_bust_01` | Obsidian MONARCH bust / shoulder silhouette |
| `dry_mud_field_001` | Displaced wet mud ground, normal / roughness / height maps |
| `cobblestone_floor_06` | Wet cobblestone courtyard and gate floor |

## Khronos glTF-Sample-Assets — CC0

| Model | Use |
| --- | --- |
| `DiffuseTransmissionPlant.glb` | Translucent swaying potato foliage |
| `GlassHurricaneCandleHolder.glb` | Foreground glass candle bokeh |
| `Lantern.glb` | Distant practical lantern geometry |

Source: `https://github.com/KhronosGroup/glTF-Sample-Assets`

## mrdoob/three.js example models — MIT

| Model | Use |
| --- | --- |
| `venice_mask.glb` | Ornate MONARCH mask geometry |
| `Soldier.glb` | Animated royal guard silhouettes |
| `LeePerrySmith.glb` | 3D human head under the mask |

Source: `https://github.com/mrdoob/three.js`

## Audio

- Urdu narration: user-selected `voice-00` masculine voice, generated as `vo/beat_01.wav`–`vo/beat_03.wav`.
- Sound design: deterministic `numpy` / `scipy` physical foley synthesis — sub impacts, night wind, lantern creak, boot crunch, rifle clack, padlock snap, chain drop, iron gate groan, whisper risers, marble chess slam, and golden dust resonance.
- Mastering: FFmpeg EBU R128 `loudnorm` to **-14.0 LUFS / -1.0 dBTP**, 48 kHz stereo.

## Story verification

Episode 01 `PEHRA` is based on Antoine-Augustin Parmentier's guarded Sablons potato field near Paris (1786–87): daytime armed guards were deliberately withdrawn at night so Parisians would steal and adopt the potato. The full episode later connects this to the potato tributes at his Père Lachaise grave.
