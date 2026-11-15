# NAAM LO — the film

**`cinema_v4/naam_film/naam_lo.mp4`** · 1080×1920 · 30 fps · **55.00 s** · 21 MB · H.264 + AAC
Cover: `cinema_v4/naam_film/cover.png`

Rendered this session, from the v6 script. Nothing is stock. Every frame is built here.

---

## Kaise bana

**Engine:** PIL plate stage → camera move → grade → vignette → 35 mm grain → code-alpha
typography → x264. Frames pipe straight into ffmpeg (`render_naam.py`). Co saath banaya, do
files me, dobara chalane par same film nikalti hai:

| file | kaam |
|---|---|
| `naam_film/render_naam.py` | 17 shots, camera moves, type, grain, encode |
| `naam_film/build_audio.py` | poori sound design, 48 kHz stereo, zero samples of music |
| `naam_film/plates/` | 10 photographic plates (768×1376) |
| `naam_film/audio/naam.wav` | rendered mix |

**Re-render:** `python3 build_audio.py audio/naam.wav && python3 render_naam.py naam_lo.mp4`
— 6 minute.

---

## Shot list — 17 cuts, hard cuts only, koi dissolve nahi

| # | in–out | plate | move | line |
|---|---|---|---|---|
| 1 | 0.0–2.2 | teen sau card, rassi se bandhe | slow push | `TEEN SAU CARD.` |
| 2 | 2.2–5.9 | darwaze pe nange pair, card bikhre | push + tilt | Beta ko paanch naam chahiye the… |
| 3 | 5.9–9.2 | budhe haath, register, chashma | push | Abbu ke paas teen sau card the… |
| 4 | 9.2–10.3 | register par tight | micro push | **Beta ne poocha.** |
| 5 | 10.3–11.2 | usi par thoda aur | micro push | **Kis ka naam likhun?** |
| 6 | 11.2–14.2 | Abbu ka moonh, aankhein frame ke bahar | push | …log hain, aur logon ke naam nahi hote |
| 7 | 14.2–18.9 | **pencil teen sau card ke upar hawa me** | push | …hawa me ruk gayi |
| 8 | 18.9–19.8 | pencil tip kaaghaz par | push | **Ek naam.** |
| 9 | 19.8–25.9 | khaali kaaghaz, graphite | slow push | Do naam kaaghaz pe aaye… |
| 10 | 25.9–31.0 | raat, beta ki peeth, khidki | push | Raat bhar beta chup baitha… |
| 11 | 31.0–35.1 | sau khaali plate, subah ki roshni | push | …kaun plate laya tha? |
| 12 | 35.1–39.1 | ungli card ki ginti par | push | …ungli card ki ginti par wapas |
| 13 | 39.1–41.0 | haath, lifafa, andhera | push | Phir aakhri lifafa uthaya. |
| 14 | 41.0–42.5 | pencil tip kaaghaz me dhansa | fast push | **Us pe likha tha, log nahi.** |
| — | 42.5–43.3 | **black** | — | 800 ms / **POP** |
| 15 | 43.3–47.1 | card andhere me, stack ke neeche | pull | …us almari me, jahan koi kabhi nahi dekhta |
| 16 | 47.1–50.6 | teen sau card, wahi opening shot | pull back | Teen sau card, sau plate… |
| 17 | 50.6–55.0 | **mask** — red eyes | slow push | …apni zindagi nahi de sakte |
| — | 53.2–55.0 | `— T A B A H I —` lockup | — | brand |

Shot 16 jaan-boojh kar shot 1 hai. Film apni hi opening image par wapas aati hai — **loop**,
aur wahi line jo shuru me sirf ek ginti thi, ab hisaab ban chuki hai.

---

## Sound — `build_audio.py`

- room tone (sirf hawa), card ki sarsarahat ×12, pencil ki khisk ×14, ungli ke tap ×7
- **sub drone** 38→52 Hz, 20 s se 42 s tak chadhta hua
- **dhadkan** 31 s se, 62 → 96 bpm
- riser 41.02 → **pop 42.18** (1300 Hz → 72 Hz, 420 ms)
- **42.63–43.34: asli digital silence** (−∞ dBFS). Yeh film ka sabse loud moment hai.
- moral ke neeche ek 46 Hz tone, jo khatam hota hai
- **music: zero.**

Master: mean **−20.5 dB**, peak **−0.6 dB**.

---

## Kya nahi mila (honest)

- Image generator ne **10 plates** diye, phir limit lag gayi. **Lifafa-in-hand** aur
  **almari-ke-andar** ke do plate nahi bane — unki jagah card-stack aur pencil-tip ke
  existing plates se kaam liya (shots 13–15).
- Ek plate me English naam likhe the (`Amelia & Owen`) — desi film me woh galat tha, isliye
  **woh plate poori tarah bench par hai.** Uske badle khaali kaaghaz ka macro use kiya, jo
  line se zyada sach hai: teesra naam aaya hi nahi.
- Koi face frame me nahi hai except the mask. Yeh choice nahi, majboori thi — aur film ka
  fayda ban gayi: chehra chhup gaya, hisaab saamne aa gaya.

---

## Caption (upload ke liye)

> Teen sau card. Sau plate. Aur ek aadmi ke paas paanch naam nahi.
> Kaaghaz lo. Paanch naam likho — un logon ke, jinke liye tum apni zindagi jee rahe ho.
> Zyadatar log teen par ruk jaate hain.
>
> `#NAAMLO #TABAHI`

**On-screen text already burned in.** Upload as-is, no extra subtitle layer.
