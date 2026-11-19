# Running Costs — per video (buyer ke accounts)

Buyer ko **launch se pehle** ye estimate do. Warna 2 mahine baad blame aap par aayega.

**Ye estimates hain, guarantee nahi.** Har provider ka pricing badalta hai — signup se pehle verify karo.

---

## Per video (30 second, 9:16, 1 render)

| Item | Kitna | Cost (approximately) | Kaun deta hai |
| --- | --- | --- | --- |
| LLM — idea, angle, script, shot plan | ~15–25k tokens in + 5k out | **$0.01–0.08** | Buyer key |
| TTS — ~60 words Urdu/English VO | 1 file | **$0.10–0.50** | Buyer key |
| Captions | Word timestamps TTS se free | **$0** | — |
| Render compute | 700 frames software WebGL | **$0** local / **$0.20–1.50** cloud | Buyer machine |
| Drive storage | ~15 MB/video | negligible | Buyer |
| **Total per video** | | **~$0.15–2.00** | |

**Aapka time** isme nahi hai — wo install fee se cover hota hai.

---

## Monthly (8 videos/mahina)

| Model | Buyer ka monthly cost |
| --- | --- |
| Local install (apna PC) | **$3–15/mahina** (sirf LLM + TTS) |
| Cloud render | **$5–30/mahina** |
| Hosted (aap chala rahe ho) | Aapka cost + **$300–600 fee** |

---

## Render time — ye pehle measure karo

`tools/render-demos.mjs` software WebGL use karta hai. README kehta hai: "software WebGL renders can take a while."

**Aapko ye number chahiye:**
```sh
node services/tools/render-budget.mjs
```

Ye tumhe batayega: ek 30s film kitna time leti hai (agar measure kiya ho), aur hafte/mahine mein kitni kar sakte ho. **Iske baghair pricing guess hai.**

Aapki films ka asli data:
- 29s film: 696 frames
- 50s film: 1,200 frames
- 62s film: 1,488 frames

Agar 1 frame = 4 seconds (typical software WebGL at 691×1229), to:
```
696 frames × 4s = 46 min  → 29s film ≈ 45–60 min render
1200 frames × 4s = 80 min → 50s film ≈ 1.5–2 hour render
```
**Plus** re-renders (revision), preview stills, encode. Realistic: **ek 30s film = 2–4 ghante machine time.**

Isliye: ek laptop par hafte mein **4–8 films** max. Price usi hisaab se. Ya cloud machine (GitHub Actions pattern repo mein already hai) use karo.

---

## Buyer ko kya batana hai (copy/paste)

```
Costs jo aap apne accounts par pay karenge (estimate):
- LLM: ~$0.01–0.08 per video
- Voiceover: ~$0.10–0.50 per video
- Render: $0 agar aapke PC par, ya ~$0.20–1.50 cloud par
- Total: ~$0.15–2.00 per video

Ye aapke accounts ke costs hain, meri fee nahi.
Meri fee install + handover ke liye one-time hai.
Aapki key main kabhi store ya share nahi karta.
```
