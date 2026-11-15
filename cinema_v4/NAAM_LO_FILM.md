# NAAM LO — the film · SURFACE-OFF cut

**`cinema_v4/naam_film/naam_so.mp4`** · 1080×1920 · 30 fps · **48.00 s** · 27 MB

> **Pichli koshish ghalat thi.** Woh ek slideshow tha — plates par zoom, neeche subtitle.
> Wahi "CapCut 3D-zoom" commodity jise spec ne **ban** kiya hai. Yeh cut usko replace karta hai:
> depth-warped plates, chalti hui roshni, x-ray dissolve, tootte lafz, chhupe hue cut.

---

## Spec jo follow hua (`SURFACE_OFF_TREND_SPEC.md`, `SURFACE_OFF_V2_ALGORITHM_SPEC.md`)

| Device | Kahan hai |
|---|---|
| **D1 PHOTO-TO-FLESH** | 41.6–43.2 + 44.8–46.4 — mask ke neeche **skull** ubharta hai: cranium, socket, teeth, aur chest me dhadakta heart jo jabde ko neeche se roshan karta hai |
| **D2 SURFACE-OFF** | 19.2–20.8 aur 38.4–40.0 — plate wireframe + depth-contour + grid me ghulti hai, phir dust |
| **D3 WORD-MATTER** | 7 cards apne hot word par **tootte** hain (CARD, NAHI, NAAM, KAUN, ZINDAGI) — 50 shards, gravity + rotation |
| **D4 ONE-TAKE ILLUSION** | 29 cuts, koi dikhta nahi: har cut par 4-frame directional whip blur + camera overshoot |
| **D5 LIGHT-HANDSHAKE** | har shot me ek moving key light — sweep, god-ray, cold moon, daylight, red band |
| **D6 ANAMORPHIC** | 1 shot (mask reveal) — horizontal red flare, band se match |
| **D9 SILENCE PUNCH** | 38.86–39.42 = **asli digital silence** (−∞ dBFS) |
| **D10 SHADOW TRUTH** | plates me baked contact shadows |

## Cut rhythm (QC #4/#5)
**30 shots · 48.00 s · har shot 1.60 s · max gap without a visual event = 1.6 s.**
Pehle 17 shots / 5.7 s the — wahi "slides" ka sabab tha.

## Captions (QC #14 — muted watch-through)
**15 cards, 2–5 words**, 74–84 px, charcoal par cream, hot word red. Poora 195-word script
ab **VO script** hai (record hona baaki), screen par sirf woh lafz hain jo chalees second me padhe jaayein.

```
TEEN SAU CARD. · PAANCH NAAM. · NAAM EK BHI NAHI. · LOG HAIN. ·
LOGON KE NAAM NAHI HOTE. · PENCIL RUK GAYI. · EK NAAM. · TEESRA — NAHI. ·
PURANI LADAAI. · SAU PLATE. · KAUN AAYAA THA? · UNGLI GINTI PAR. ·
LOG NAHI. · JINKE NAAM TUM NAHI LE SAKTE, · UNKE NAAM PE APNI ZINDAGI NAHI.
```

## Engine
`naam_film/surface_off.py` — python + numpy + PIL, koi Blender nahi, koi GPU nahi.
1. **depth** = normalised, heavily blurred luma (per plate, baked once)
2. **warp** = per-pixel 2.5D: `src = centre + (p−centre)/z(depth) + shift(depth)` + whole-camera pan,
   half-res bilinear gather → 1080p. **Koi band nahi, koi seam nahi, koi bend nahi.**
3. light-blob sweeps · god-rays · x-ray skull · blueprint · shatter · whip · halation · grain

`build_audio48.py` — 48.0 s mix, 3-layer rule, pop **38.40**, peak **−1.00 dBFS**, mean **−16.1 dB**.

## Jo abhi bhi adhoora hai (honest)
- **Loop (QC #6) engineer nahi hua** — film mask par khatam hoti hai, cards par wapas nahi aati.
  Agli iteration me last 2 shots ko frame-0 par SSIM ≥0.92 se milana hai.
- **Depth luma se hai**, asli depth model se nahi — isliye warp gentle rakha (0.85).
  ONNX Depth-Anything mil jaaye to isko 3× strong kiya ja sakta hai.
- **VO nahi hai.** 195-word script bola nahi gaya; screen par 15 cards hain.
