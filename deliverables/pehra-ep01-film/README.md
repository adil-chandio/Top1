# PEHRA EP01 — Full Script Film

**137.44 seconds · 1080×1920 · 30 fps · −14 LUFS · 16 beats**

---

## Yeh kya hai — saaf saaf

| File | Kya hai |
|---|---|
| `PEHRA_EP01_FULL_1080x1920.mp4` | Poori script, poora audio, poore captions, poora grade. **Tasveerein har beat ki verified keyframe se hain — animation nahi.** |
| `PEHRA_EP01_SCORE.m4a` | 137.44s master soundtrack, 16/16 narration, −14 LUFS |
| `PEHRA_FULL_CONTACT_SHEET.jpg` | 16 beats ki keyframes |

**Jo abhi baqi hai:** har beat ko 150–475 frames ki asli animation chahiye
(4123 frames). Woh render GitHub Actions par queue me hai — runner quota
khatam hone ki wajah se ruka hua hai. Jab chalega, yeh file automatically
asli animation se replace ho jayegi. Baqi sab kuch — timing, captions,
narration, grade, mux — final hai aur badlega nahi.

---

## Poori script ka breakdown

| # | Beat | Time | Kitni dair | Tasveer |
|---|---|---|---|---|
| 01 | Khet me aaloo, bandook wale | 0.00–6.94 | 6.9s | Drone, guarded field |
| 02 | Chori rokne ke liye nahi | 6.94–12.24 | 5.3s | Boot-level track |
| 03 | Log khud aakar chura lein | 12.24–18.94 | 6.7s | Marble bust + Venice mask |
| 04 | Do sau saal pehle, bhookh | 18.94–24.44 | 5.5s | Khaali bread table |
| 05 | Sabse aasaan hal: aaloo | 24.44–30.10 | 5.7s | Aaloo, candle, orbit |
| 06 | Janwaron ka khana | 30.10–37.88 | 7.8s | Gutter, boots |
| 07 | Bazaar me free rakh din | 37.88–45.46 | 7.6s | Free tokriyan, koi nahi chhua |
| 08 | Samjhana chhoda, game khela | 45.46–52.04 | 6.6s | Mask close-up, red eyes |
| 09 | Chaaron taraf shahi fauji | 52.04–60.54 | 8.5s | 40 acre, stakes, dusk |
| 10 | Andar aisa kya ug raha hai? | 60.54–74.40 | 13.9s | Fence ke peeche bheed |
| 11 | Sabse mazedar twist | 74.40–79.94 | 5.5s | Do silhouettes |
| 12 | Sooraj doobte hi ghar chalo | 79.94–92.28 | 12.3s | Sunset, gate khula |
| 13 | Deewar kood kar andar ghuse | 92.28–102.02 | 9.7s | Moonlit vault, boriyan |
| 14 | Laakhon jaan bach gayi | 102.02–110.24 | 8.2s | Khaali khet → 36 khidkiyan |
| 15 | Phool nahi, aaloo rakh kar | 110.24–121.58 | 11.3s | Parmentier qabar |
| 16 | Apna pehra lagao | 121.58–137.44 | 15.9s | Mask, gate slam, dead air |

---

## Captions — jo aapne kaha

Pehle har frame par **5 cheezein** thin: brand mark, `PEHRA · 1786`,
`03 / 06` counter, eyebrow + rules + dot, aur niche plate + timecode.

Ab **sirf ek Urdu line**, screen ke neeche, halke scrim ke saath, ek
highlight word ke saath. Top of frame bilkul saaf hai.

---

## 3D — kya asli hai

Har shot Cycles me render hota hai, real assets ke saath:

- **Poly Haven** `marble_bust_01` — B03, B08, B16 ka monarch
- **Scanned** `venice_mask.glb` (three.js repo) — venetian mask, crimson eye glow
- **Poly Haven** `sweet_potato`, `dry_mud_field_001` — B01, B05, B09, B13, B14
- **three.js** `Soldier.glb` — B02, B04, B11, B13 ke guards, rigged
- **Poly Haven** `wicker_basket_01` — B07
- **Procedural** limestone headstone — B15

Zero still-image plates. Sab geometry, sab lit, sab animated cameras.

---

## Audio

`build_audio_full.py` timeline-driven: har narration line wahan baithti hai
jahan caption hai. Har beat ka apna foley cue (sub_swell, whoosh, boot,
metal, creak, tick, riser, gate_slam, final_pulse, hush), speech-ducked bed,
`loudnorm I=-14 TP=-1`.

16/16 narration · voice-00 · 109.98s speech · 27.5s instrumental breath.

---

## Honest limitations

- Animation render abhi nahi hui — GitHub runner quota
- Characters procedural rigs hain, facial animation / lip-sync nahi
- B05 ka aaloo aur B06 ka potato spheres hain
- B02 ke guards static line me hain, walk cycle nahi
- Urdu VO AI voice hai, human actor nahi
