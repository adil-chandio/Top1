# PEHRA EP01 — Full Script: Kaam ka Status

Aakhri update: 2026-11-16 (raat)

---

## 1. Kya maanga gaya tha

1. Top ke bilawaja kharab captions hatao → **ho gaya**
2. 3D animation + editing next level → **ho gaya** (16 naye shots)
3. Poori script par poori video → **pipeline tayyar, render baqi**
4. "Tabahi level" quality → **per-shot visually verify kiya ja raha hai**

---

## 2. Poori script = 97.44s, 2923 frames, 16 beats

Pehle 15s teaser tha (6 shots). Ab `plan_full.py` poori narration ko
naap kar timeline banata hai — har cut sentence par girta hai, uske aas-paas
nahi:

| # | Beat | Frames | Time | Picture |
|---|---|---|---|---|
| 01 | B01_AERIAL_FIELD | 1–208 | 0.00–6.94 | Drone khet par, fauji, lantern |
| 02 | B02_GUARDED_FIELD | 209–367 | 6.94–12.24 | Boot-level track, muskets |
| 03 | B03_MASKED_TITLE | 368–568 | 12.24–18.94 | Marble bust + venice mask, gate band |
| 04 | B04_HUNGRY_PARIS | 569–733 | 18.94–24.44 | Khaali bread table, bhookhe log |
| 05 | B05_POTATO_PROMISE | 734–903 | 24.44–30.10 | Ek aaloo, candle, orbit |
| 06 | B06_POISONED_MIND | 904–1136 | 30.10–37.88 | Aaloo gutter me, boots |
| 07 | B07_FREE_BASKETS | 1137–1364 | 37.88–45.46 | Free tokriyan, koi nahi chhua |
| 08 | B08_SILENT_PIVOT | 1365–1561 | 45.46–52.04 | Mask extreme close-up |
| 09 | B09_FORTY_ACRES | 1562–1816 | 52.04–60.54 | Chaalis acre, stakes, dusk |
| 10 | B10_WHISPERS | 1817–1969 | 60.54–65.64 | Fence ke peeche sargoshi |
| 11 | B11_LAST_ORDER | 1970–2122 | 65.64–70.74 | Do silhouettes, hukm |
| 12 | B12_SUNSET_WITHDRAWAL | 2123–2275 | 70.74–75.84 | Time-lapse sunset, gate khula |
| 13 | B13_NIGHT_THEFT | 2276–2428 | 75.84–80.94 | Deewar par chadhna, bori |
| 14 | B14_EMPTY_FIELD_DAWN | 2429–2581 | 80.94–86.04 | Khaali khet → 36 khidkiyan |
| 15 | B15_GRAVE_200_YEARS | 2582–2734 | 86.04–91.14 | Parmentier qabar, aaloo paude |
| 16 | B16_FINAL_MONARCH | 2735–2923 | 91.14–97.44 | Mask, gate slam, 1.2s dead air |

---

## 3. Captions: kya hataya

Pehle har frame par **5 cheezein** thi: `MONARCH / EP01`, `PEHRA · 1786`,
`03 / 06` counter, ek eyebrow + rules + dot, aur niche plate + timecode.
Picture ke upar shor.

Ab **sirf ek line** Urdu, screen ke niche, halka sa scrim. Bas.

---

## 4. 3D: kya asli hai (visually verified)

Har beat ka real Cycles lookdev frame render karke aankhon se check kiya:

- **B03 / B08 / B16** — Poly Haven `marble_bust_01` + scanned `venice_mask.glb`,
  crimson eye glow mask ke peeche se leak
- **B01 / B09 / B13 / B14** — `sweet_potato`, `dry_mud_field_001` displacement
- **B02 / B04 / B11 / B13** — three.js `Soldier.glb` rigs, rigged pose
- **B07** — Poly Haven `wicker_basket_01` + spilled potatoes
- **B15** — limestone headstone, 20 aaloo paude qabar ke gird

**Jo theek kiya** (har ek lookdev me dikha):
- B03/B08/B16 pehle blobby procedural head tha → asli marble + mask
- B11 pehle bilkul khaali frame tha → camera + key light theek
- B13 pehle pitch black tha → moon key, deewar peeche khiski
- B15 pehle "lakri ka dibba" lag raha tha → asli limestone tone
- B16 pehle lock monarch ka chehra dhak raha tha → gate peeche, face clear

---

## 5. Audio

`build_audio_full.py` timeline-driven hai: har narration line wahan baithti hai
jahan timeline kehta hai, har beat ka apna foley cue.

**9 / 16 beats ki narration ban chuki hai** (voice-00):
B01 5.84s · B02 4.20 · B03 5.60 · B04 4.40 · B05 4.56 · B06 6.68 · B07 6.48 ·
B08 5.48 · B09 7.40

Baqi 7 (B10–B16) is turn ke speech quota (10) ki wajah se baqi hain —
agli turn me pehla kaam.

---

## 6. Baqi kaam (order me)

1. B10–B16 ki 7 narration lines generate karna
2. `build_audio_full.py` dobara → 16/16 narration, −14 LUFS master
3. `pehra-final-render.yml` dispatch → 2923 frames, ~113 shards
   (26 frames/shard, max-parallel 18, ~4–5 ghante runner time)
4. `assemble_preview.py --mode final` → 97.4s film + clean captions
5. Drive upload + visual QC

---

## 7. Honest limitations

- 97s film, **render abhi nahi hui** — sirf 16 keyframes verify hue hain
- Characters procedural rigs hain (facial animation / lip-sync nahi)
- B05 ka aaloo aur B06 ka rolling potato simple spheres hain
- B02 ke guards static line me hain — walk cycle nahi
- Urdu VO AI voice-00 hai, human actor nahi
- `workflow_dispatch` is token scope me 403, runs push se trigger hote hain
