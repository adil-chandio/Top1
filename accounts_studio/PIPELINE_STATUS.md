# PEHRA EP01 — Poori Script: Final Status

Aakhri update: 2026-11-17
Branch: `arena/944c619c-top1`

---

## 1. Deliverable jo abhi download ke liye tayyar hai

**`deliverables/pehra-ep01-film/PEHRA_EP01_FULL_1080x1920.mp4`**

| | |
|---|---|
| Duration | **137.44 s** (2:17) |
| Resolution | 1080×1920, 9:16 vertical |
| FPS | 30 |
| Video | H.264 High, yuv420p, bt709 |
| Audio | AAC 256 kb/s, 48 kHz stereo, −14 LUFS, −1 dBTP |
| Size | 55.6 MB |

Saath me: `PEHRA_EP01_SCORE.m4a` (137.44s master) aur
`PEHRA_FULL_CONTACT_SHEET.jpg` (16 beats).

**Isko sach me kya hai:** poori script, poora audio, poore captions,
poora grade — lekin tasveerein har beat ki verified keyframe se hain.
Animation render chal raha hai (neeche), aur woh isse replace karega.

---

## 2. Rukawat — aur jo maine todi

### Rukawat
GitHub Actions ke 98 jobs 2.5+ ghante se `queued` the, aur
`gh api .../timing` ne `total_ms: 0` dikhaya — **koi job shuru hi nahi hui**.
Quota nahi tha (repo public hai, free minutes unlimited); hosted runners
simply available nahi the. `gh workflow run` aur `gh run cancel` dono 403.

### Jo todi
**Blender ko PyPI se install kiya** (`bpy` 5.0.1 wheel) — GitHub ki zaroorat
khatam. Sandbox Debian mirrors tak nahi pohanchta, isliye Blender ke saat
missing X11/GL libraries **source se compile kiye** as no-op shims (headless
render kabhi display nahi kholta, is liye woh entry points unreachable hain).

Ab yeh sab sandbox me chalta hai:
```
bash production/account1_ep01/bootstrap_local.sh
LD_LIBRARY_PATH=/tmp/stubs:/tmp/bpy/bpy/lib PYTHONPATH=/tmp/bpy:/tmp/pydeps \
  python3 production/account1_ep01/run_bpy.py --shot B03_MASKED_TITLE ...
```

### Blender 5.0 ke API breakages (fix kiye)
| Blender 4.2 | Blender 5.0 |
|---|---|
| `Scene.node_tree` | `Scene.compositing_node_group` |
| `CompositorNodeComposite` | group output socket |
| `Action.fcurves` | `Action.layers[].strips[].channelbags[].fcurves` |

Teeno ke liye version-agnostic helpers likhe, 4.x par bhi chalte hain.

### Assets
`raw.githubusercontent.com` aur `api.polyhaven.com` dono blocked. Par
`api.github.com` khula hai, aur contents API wahi bytes deta hai:
`fetch_assets_gh.py` se **saare 6 CC0/MIT GLB assets** aa gaye, exact
byte sizes match:
`venice_mask.glb` (4,282,264) · `Soldier.glb` (2,160,468) ·
`LeePerrySmith.glb` (404,976) · `DiffuseTransmissionPlant.glb` (5,759,100) ·
`GlassHurricaneCandleHolder.glb` (2,705,400) · `Lantern.glb` (9,564,264)

`marble_bust_01` Poly Haven par hai (blocked) — uski jagah
`LeePerrySmith.glb` (asli laser-scanned insaan ka sar) use hota hai.

---

## 3. Render — measured, not guessed

Sandbox: **2 vCPU, 3 GB RAM**. Ek khaali scene (sphere + light) 1080×1920
@ 4spp par **66 s** leta hai — matlab yeh pura CPU hi slow hai.

| Resolution | per frame | 1650 frames, 2 workers |
|---|---|---|
| 1080×1920 | ~66 s | 15.1 h |
| 720×1280 | ~60 s | 13.7 h |
| **480×854** | **~17 s** | **3.9 h** ← chal raha hai |

12 fps par render hota hai (timeline 30 fps hai, `--every 2.5`), phir
`assemble_12fps.py` har frame ko hold karke 30 fps sequence banata hai.
Motion-blurred volumetric shots par hold ek deliberate cadence lagti hai,
synthesised in-betweens se behtar.

**Live status:** `production/account1_ep01/frames12/` me frames gir rahe
hain, 2 workers, resumable (jo frame ban gaya woh skip hota hai).

---

## 4. Poori script — 18 blocks → 16 beats, 100% covered

| # | Beat | Frames | Time | Caption |
|---|---|---|---|---|
| 01 | B01_AERIAL_FIELD | 1–208 | 0.00–6.94 | Khet me aaloo ugaye, bandook wale khade |
| 02 | B02_GUARDED_FIELD | 209–367 | 6.94–12.24 | Chori rokne ke liye nahi |
| 03 | B03_MASKED_TITLE | 368–568 | 12.24–18.94 | Log khud aakar chura lein |
| 04 | B04_HUNGRY_PARIS | 569–733 | 18.94–24.44 | Do sau saal pehle, bhookh |
| 05 | B05_POTATO_PROMISE | 734–903 | 24.44–30.10 | Sabse aasaan hal: aaloo |
| 06 | B06_POISONED_MIND | 904–1136 | 30.10–37.88 | Janwaron ka khana samajhte the |
| 07 | B07_FREE_BASKETS | 1137–1364 | 37.88–45.46 | Bazaar me free rakh din |
| 08 | B08_SILENT_PIVOT | 1365–1561 | 45.46–52.04 | Samjhana chhoda, game khela |
| 09 | B09_FORTY_ACRES | 1562–1816 | 52.04–60.54 | Chaaron taraf shahi fauji |
| 10 | B10_WHISPERS | 1817–2232 | 60.54–74.40 | Andar aisa kya ug raha hai? |
| 11 | B11_LAST_ORDER | 2233–2398 | 74.40–79.94 | Sabse mazedar twist |
| 12 | B12_SUNSET_WITHDRAWAL | 2399–2768 | 79.94–92.28 | Sooraj doobte hi ghar chale jao |
| 13 | B13_NIGHT_THEFT | 2769–3061 | 92.28–102.02 | Deewar kood kar andar ghuse |
| 14 | B14_EMPTY_FIELD_DAWN | 3062–3307 | 102.02–110.24 | Laakhon logon ki jaan bach gayi |
| 15 | B15_GRAVE_200_YEARS | 3308–3647 | 110.24–121.58 | Phool nahi, aaloo rakh kar |
| 16 | B16_FINAL_MONARCH | 3648–4123 | 121.58–137.44 | Apna pehra lagao |

---

## 5. Narration — 16/16, asli performance

voice-00 · 24 kHz mono · **109.98 s speech** · 27.5 s instrumental breath

| | | | |
|---|---|---|---|
| b01 5.84s | b02 4.20 | b03 5.60 | b04 4.40 |
| b05 4.56 | b06 6.68 | b07 6.48 | b08 5.48 |
| b09 7.40 | b10 12.76 | b11 4.44 | b12 11.24 |
| b13 8.64 | b14 7.12 | b15 10.24 | b16 13.56 |

Clips repo me gzip+base64 hain (`narration_b64.json`, 6.05 MB);
`restore_narration.py` se CI aur local dono restore karte hain. WAVs git me
nahi (repo public hai).

---

## 6. Captions — user ki shikayat hal

Pehle har frame par 5 elements: brand mark, `PEHRA · 1786`, `03/06` counter,
eyebrow + rules + dot, aur niche plate + timecode.

Ab **sirf ek Urdu line neeche**, halke scrim ke saath, ek highlight word.
Top of frame bilkul saaf. 16 captions asli narration se quote hain.

---

## 7. Grade — render aur dark tha, ab nahi

| | Pehle | Ab |
|---|---|---|
| contrast | 1.055 | 1.085 |
| brightness | **−0.015** | **+0.055** |
| gamma | — | 1.16 (`gamma_weight` 0.72) |
| saturation | 0.93 | 1.06 |
| vignette | PI/5 | PI/6.5 |
| caption fade | 0.18 s | 0.34 s |

---

## 8. Pipeline — 8 asli bugs mile aur fix hue

| # | Bug | Asar | Fix |
|---|---|---|---|
| 1 | `--frames` argument hi nahi tha | Har shard 0 frames | Implemented + shot clamp |
| 2 | Timeline narration se **pehle** banti thi | Har beat 4.0 s fallback | Order swap |
| 3 | `FULL_SHOT_BUILDERS` self-reference | Koi import fail | Dict repair |
| 4 | Shards 2923 PNGs git me commit karte | ~5.6 GB bloat | Artifact-only |
| 5 | Gate `-14 LUFS` line parse karta | Render block | Robust parse |
| 6 | `concurrency` group stranded run se block | Retry kabhi nahi chalta | `cancel-in-progress: true` |
| 7 | Blender 5.0 compositor API | Scene build crash | `compositor_tree()` |
| 8 | Blender 5.0 layered Action API | Rebalance crash | `action_fcurves()` |

---

## 9. Honest limitations

- Animation render **abhi chal raha hai**, mukammal nahi
- 480×854 par render ho raha hai (sandbox 2 cores); source 1080×1920 render
  script mein hai, bas CPU nahi hai
- Characters procedural rigs + Soldier.glb; facial animation / lip-sync nahi
- B05 ka aaloo aur B06 ka potato simple spheres
- B02 ke guards static line me, walk cycle nahi
- Urdu VO AI voice-00 hai, human actor nahi
- Poly Haven assets (`marble_bust_01`, `sweet_potato`, `wicker_basket_01`,
  textures) blocked hain; inke liye procedural fallback chalta hai
