# PEHRA EP01 — 15s 3D Cinema: Haqeeqat ka Status

Aakhri update: 2026-11-16

---

## 1. Kya deliver hua

| Cheez | Value |
|---|---|
| File | `PEHRA_EP01_15s_3D_CINEMA_1080x1920.mp4` |
| Drive link | https://drive.google.com/file/d/1a_-gbkLkKcueK5XGgMHZgL9mc7B0gy2u/view |
| Size | 37,413,966 bytes (35.7 MB) |
| MD5 | `0bfca6231b651784276025183b4562af` |
| Resolution | 1080 × 1920 (9:16 vertical) |
| FPS / frames | 30 fps · 450 frames · 15.000 s |
| Picture | **450/450 Blender Cycles path-traced 3D frames** — zero still plates |
| Audio | Urdu voice-00 VO + frame-locked foley, −14 LUFS, stereo 48 kHz |
| Captions | 6 burned-in Urdu editorial cards |

Drive par file **public link** hai (anyone with link → reader), discovery off.

---

## 2. Pichla delivery kyūn reject hua

Pehli film **numpy abstract geometry** thi — 2D shapes ka motion graphics.
Metrics sab green the (449/449 moving frames, −14 LUFS, green CI) lekin
**picture me koi 3D nahi tha**. Woh galat rasta tha, aur woh film dobara
deliver nahi hogi.

Repo me pehle se ek asli renderer mojood tha jo maine bypass kar diya tha:
`production/account1_ep01/render_scene.py` — 1931 lines, Blender 4.2 LTS
Cycles, real PBR materials, volumetric fog, particles, imported CC0 meshes.

---

## 3. Is film me kya asli 3D hai (verified)

Har shot ke numbers asli render logs se hain, guess nahi:

| Shot | Frames | Scene | Kya asli asset use hua |
|---|---|---|---|
| S1 MIDNIGHT_FURROW | 1–72 | Khet, aaloo, potted plant | Poly Haven `sweet_potato` + `DiffuseTransmissionPlant.glb` |
| S2 ROYAL_GUARDS | 73–156 | Barred window, 3 guards | three.js `Soldier.glb` (3×) + procedural tricorn |
| S3 LOCKED_IRON | 157–207 | Brass padlock, chain | procedural lock + `MAT_AGED_BRASS` PBR |
| S4 UNGUARDED_GATE | 208–270 | Khuli gate, chowk | `cobblestone_floor_06` PBR + `Soldier.glb` |
| S5 MASKED_MONARCH | 271–310 | Marble bust + mask | Poly Haven `marble_bust_01` + `venice_mask.glb` |
| S6 MASTER_MOVE | 311–450 | Chess board, knight slam | Poly Haven `chess_set` + `wicker_basket_01` |

**Do bade fixes** jo is version me kiye:

1. **S5** pehle ek plastic mannequin tha jis par mask hawa me tair raha tha.
   Ab asli scanned Venetian mask (`venice_mask.glb`) marble bust ke chehre par
   baithta hai — size face width se calculate hota hai (0.262 m), eye slots
   bust ki eye line par. Crimson eye glow mask ke peeche se leak karta hai.
2. **S6** pehle procedural knight tha (flat slab). Ab Poly Haven ka asli
   chess set hai — 15 white + 15 black pieces, wet-marble reflections,
   candle bokeh, shallow DoF.

---

## 4. Render kaise chala (reproducible)

`.github/workflows/pehra-final-render.yml` — 3 jobs:

- **bootstrap** — timeline + Urdu soundtrack build, CC0 assets fetch
  (65 files / 338.7 MB), Blender 4.2.15 ek dafa download karke artifact se
  pass (22 parallel shards ek saath download kar rahe the aur fail ho rahe the).
- **render** — 8 wide × 6 shots = 44 shards, `max-parallel: 18`, har shard
  apne frames git par commit karta hai (sandbox artifact storage tak nahi
  pahunch sakta).
- **assemble** — 450 frames verify → ffmpeg grade + 6 captions + mux → QC.

Settings: `--mode final --samples 4 --res-pct 100`, Cycles CPU,
OpenImageDenoise, 42–70 s per frame.

---

## 5. Honest limitations

- Ye ek **preview** hai, feature nahi. 15 s, 6 shots.
- Characters procedural rigs hain (koi facial animation / lip-sync nahi).
- Urdu VO voice-00 hai (AI voice), human actor nahi.
- S2 ke guards static posing me hain — unka alag skeleton animation nahi.
- `workflow_dispatch` is token scope me 403 deta hai, isliye runs push se
  trigger hote hain.

---

## 6. Test suite

`python3 -m unittest discover -s accounts_studio/tests` → **86 tests OK**

Delivery barriers covered: missing receipt, changed receipt, review of other
bytes, two final videos, rejected hash, `user_rejected`, QC bound to a
different video.
