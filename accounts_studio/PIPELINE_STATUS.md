# PEHRA EP01 — Poori Script: Final Status

Aakhri update: 2026-11-17

---

## 1. Deliverable jo abhi maujood hai

**`deliverables/pehra-ep01-film/PEHRA_EP01_FULL_1080x1920.mp4`**

| | |
|---|---|
| Duration | **137.44 s** (2:17) |
| Resolution | 1080×1920, 9:16 vertical |
| Frame rate | 30 fps, 4123 frames |
| Video | H.264 High, yuv420p, bt709 |
| Audio | AAC 256 kb/s, 48 kHz stereo, −14 LUFS, −1 dBTP |
| Size | 55.6 MB |

Isko **sach me kya hai**: poori script, poora audio, poore captions, poora
grade — lekin tasveerein har beat ki **verified keyframe** se hain, animation
nahi. Animation render GitHub runner quota ki wajah se rukа hua hai.

---

## 2. Kya-kya mukammal ho gaya

### Script — 18 blocks → 16 beats, 100% covered

`plan_full.py` poori narration ko naap kar timeline banata hai. Koi line
nahi chhooti, koi line duplicate nahi.

| # | Beat | Frames | Time |
|---|---|---|---|
| 01 | B01_AERIAL_FIELD | 1–208 | 0.00–6.94 |
| 02 | B02_GUARDED_FIELD | 209–367 | 6.94–12.24 |
| 03 | B03_MASKED_TITLE | 368–568 | 12.24–18.94 |
| 04 | B04_HUNGRY_PARIS | 569–733 | 18.94–24.44 |
| 05 | B05_POTATO_PROMISE | 734–903 | 24.44–30.10 |
| 06 | B06_POISONED_MIND | 904–1136 | 30.10–37.88 |
| 07 | B07_FREE_BASKETS | 1137–1364 | 37.88–45.46 |
| 08 | B08_SILENT_PIVOT | 1365–1561 | 45.46–52.04 |
| 09 | B09_FORTY_ACRES | 1562–1816 | 52.04–60.54 |
| 10 | B10_WHISPERS | 1817–2232 | 60.54–74.40 |
| 11 | B11_LAST_ORDER | 2233–2398 | 74.40–79.94 |
| 12 | B12_SUNSET_WITHDRAWAL | 2399–2768 | 79.94–92.28 |
| 13 | B13_NIGHT_THEFT | 2769–3061 | 92.28–102.02 |
| 14 | B14_EMPTY_FIELD_DAWN | 3062–3307 | 102.02–110.24 |
| 15 | B15_GRAVE_200_YEARS | 3308–3647 | 110.24–121.58 |
| 16 | B16_FINAL_MONARCH | 3648–4123 | 121.58–137.44 |

### Narration — 16/16, asli performance

voice-00, 24 kHz mono, poora script block-by-block:

| | | | |
|---|---|---|---|
| b01 5.84s | b02 4.20 | b03 5.60 | b04 4.40 |
| b05 4.56 | b06 6.68 | b07 6.48 | b08 5.48 |
| b09 7.40 | b10 12.76 | b11 4.44 | b12 11.24 |
| b13 8.64 | b14 7.12 | b15 10.24 | b16 13.56 |

**Total 109.98 s speech**, 27.5 s instrumental breath. Poore clips repo me
gzip+base64 (`narration_b64.json`, 6.05 MB) — CI khud restore karta hai
(`restore_narration.py`), WAVs git me nahi.

### Captions — clutter khatam

Pehle har frame par 5 elements (brand mark, `PEHRA · 1786`, `03/06` counter,
eyebrow + rules + dot, timecode). Ab **sirf ek Urdu line neeche**, halke
scrim + ek highlight word ke saath. Top of frame bilkul saaf.

16 captions asli narration se quote kiye hue hain, isliye lower third hamesha
wahi kehta hai jo awaaz keh rahi hai us waqt.

### 3D — 16 beats, visually verified

Har beat ka real Cycles lookdev render karke aankhon se check kiya
(`deliverables/pehra-lookdev-full/`).

Jo theek kiya:
- B03/B08/B16 — blobby procedural head → asli `marble_bust_01` + scanned `venice_mask.glb`
- B11 — bilkul khaali frame → camera + key light theek
- B13 — pitch black → moon key, deewar peeche khiski
- B15 — "lakri ka dibba" → asli limestone headstone + 20 aaloo paude
- B16 — lock chehra dhak raha tha → gate peeche, face clear

Assets: Poly Haven (`marble_bust_01`, `sweet_potato`, `dry_mud_field_001`,
`wicker_basket_01`) + three.js (`venice_mask.glb`, `Soldier.glb`). Zero
still-image plates.

### Grade — shadows lift kiye

Pehle `brightness=-0.015` — render aur dark ho raha tha. Ab
`brightness=0.055, gamma=1.16, gamma_weight=0.72, saturation=1.06`,
vignette PI/6.5, film grain, 0.34s caption fades.

### Pipeline — 5 asli bugs fix kiye

| Bug | Asar | Fix |
|---|---|---|
| `--frames` argument hi nahi tha | Har shard 0 frames, 30/30 fail | Implemented + shot-range clamp |
| Timeline narration se **pehle** banti thi | Har beat 4.0s fallback → galat film | Order swap |
| `FULL_SHOT_BUILDERS` self-reference | Koi bhi import fail | Dict repair |
| Shards 2923 PNGs git me commit karte | ~5.6 GB bloat | Artifact-only flow |
| Gate `-14 LUFS` line parse karta | Render block | Robust sed parse |

---

## 3. Baqi — sirf animation render

**Status:** GitHub Actions runner quota khatam. Do runs queued hain:
`44022584682` (1h51m), `44025626550` (1h25m). `gh workflow run` 403 hai,
runs sirf push se chalte hain, `gh run cancel` bhi 403 hai.

**Jab runners wapas aayen:**

```
37 shards × 150 frames × ~73 s/frame ≈ 3 h/job
20 parallel → ~3–4 h wall
```

Sharding verified hai: 37 shards, 4123/4123 frames exactly contiguous, har
shard apne beat ke andar. `--frames` path Blender 4.2.15 par test ho chuka —
3 frames, 330 s, exit 0.

Assemble verified hai: poora 137.44 s film locally bani, QC pass
(h264 1080×1920 @ 137.44 s, AAC 48 kHz stereo).

---

## 4. Honest limitations

- Animation render baqi — keyframes verified hain, motion nahi
- Characters procedural rigs, koi facial animation / lip-sync nahi
- B05 aaloo aur B06 potato simple spheres
- B02 guards static line me, walk cycle nahi
- Urdu VO AI voice-00 hai, human actor nahi
- 3 volumes me fog hai — har frame ~73–110 s, isliye 4123 frames mehnga hai
