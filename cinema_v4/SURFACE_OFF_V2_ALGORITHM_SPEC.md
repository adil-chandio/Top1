# SURFACE-OFF v2 — ALGORITHM-CALIBRATED CINEMA
## EP5 · `Main Abhi Bhi Apni Taraf Hoon` · plan only (zero build)
**Date:** 14 Nov 2026 · Branch `arena/2a8ad29e-top1`

---

# 0. Kya badla v1 se

v1 ek **khoobsurat format** tha. v2 ek **algorithm ke liye design kiya hua weapon** hai.
Har beat ko ek ranking signal se bandh diya gaya hai (shares / completion / saves / comments), hook ko frame-0 par shift kiya, loop ko **measurable** banaya (SSIM ≥ 0.92), aur **ek production se 3 lengths** nikalne ka plan bana diya.

| v1 | v2 |
|---|---|
Hook = macro shard | **Frame 0 = aadha photo / aadha x-ray chehra** (thumbnail = hook = frame 0) |
Loop = "loop seed" | Loop = **pixel-measured**, f0 ≈ f1243 (SSIM ≥ 0.92) → retention >100% |
1 delivery (41.5 s) | **3 deliveries**: MASTER 41.5s · TIGHT 28s · TEASER 12s |
5 devices | **5 core + 5 support devices** (D6–D10) |
SFX bank | + **SURFACE-OFF STING** (reusable 6s signature sound → audio-trend vector) |
12 QC gates | **18 QC gates**, incl. signal-specific ones |

---

# 1. ALGORITHM — jo 2026 me actually count hota hai

### Instagram Reels (ranking order)
1. **DM shares (sends per reach) — #1**, strongest for non-followers
2. **Watch completion / rewatch** — #2
3. **Saves** — #3
4. **Comments (depth, not emoji)** — #4
5. Story shares — #5 · Likes — #6 (**weakest**)
Plus: first 3 seconds gate → first 30–60 min test group decides non-follower distribution; completion >50% = keeps spreading; replay/loops matter; **originality score** (reposters get removed from recommendations).

### YouTube Shorts
- **First 30 s retention is a direct ranking input** (Apr 2026), not a diagnostic.
- **First frame IS the hook** — intro cards/logo kill 10–20 pp of retention.
- **Visual/audio beat every 2–3 s.** Loops push retention **above 100%** (replays count).
- Strong 70–85%; **>85% exceptional.**
- Hook = thumbnail + frame 0, same promise (bait-and-switch = algorithmic suppression).
- **60–80% watch muted** → burned-in captions from frame 0 lift retention 25–40%.

> Isliye v2 me: face-first frame 0, muted-proof captions, 2.2 s pattern interrupts, measured loop, DM-share moment, save card, comment question. Har ek intentionally.

---

# 2. SIGNAL MAP — kaunsa beat kaunsa signal kamata hai

| Beat | Time | Kaam | Primary signal |
|---|---|---|---|
**1 Cold Open** | 0.0–2.9 | **Impossible frame**: half photo / half x-ray face + 2-frame caption. Question paida karo | **3-s retention** |
**2 Khwaab** | 2.9–8.6 | Curiosity gap: "khwaab" lafz mitti ban kar tootta hai | completion (early) |
**3 Excuses** | 8.6–14.7 | **SURFACE-OFF** world reveal + monolith slam | pattern interrupt #1 |
**4 Sukoon** | 14.7–19.7 | Warm lounge → cold sweep (trap) | tension |
**5 **X-Ray** | 19.7–24.4 | **PHOTO-TO-FLESH** — *"yeh dekh"* moment | 🔥 **DM SHARES #1** |
**6 Micro** | 24.4–28.4 | Macro ink bleed + scale gag | completion (mid) |
**7 10 min** | 28.4–33.0 | **10:00 save card** — clean, readable, pause-worthy | 💾 **SAVES #3** |
**8 Stairs** | 33.0–37.2 | Monumental ascent, 8 god rays | completion (late) |
**9 Portrait** | 37.2–39.0 | **Masked MONARCH reveal** — identity | 🧠 **COMMENTS #4 + FOLLOW** |
**10 Loop** | 39.0–41.5 | Orb reignites → **seamless to frame 0** | ♻️ **REWATCH** |

**Re-hook points (designed anti-drop zones):** 3.0s · 8.6s · 14.7s · 19.7s · 24.4s · 28.4s · 33.0s · 37.2s — har ek par ek naya visual ya sonic event, taake curve plateau bane (cliff nahi).

---

# 3. FRAME 0 DOCTRINE (sabse bada upgrade)

**Rule:** frame 0 = thumbnail = hook = promise. Koi fade-in, koi logo, koi "hello" nahi.

Frame 0 composition:
- **Aadha chehra aapki asli photo** (left), **aadha x-ray** — ribs + glowing heart (right). Split vertical, red band peeche.
- Caption frame 0 se: **`TUMHARI HAAR`** (2 words, 84 px+, high contrast)
- 12 frames me split-line camera ki taraf move karti hai → reveal "photo vs 3D"
- Frame 12–24: whip → void → story shuru (back-pay, kyunki viewer already committed)

**Kyun:** "photo hai ya 3D?" ek **honest question** hai — bait-and-switch nahi. Isse early drop-off (jo algorithm suppress karta hai) nahi hota, aur comment thread khulta hai.

---

# 4. LOOP ENGINEERING (measurable, kyunki rewatch = #2)

| Requirement | Metric | Gate |
|---|---|---|
End frame → frame 0 visual continuity | **SSIM(f0, f_last) ≥ 0.92** | fail → shot 10.2 re-block |
Motion continuity | last-frame motion vector ≈ first-frame motion vector (±15°) | fail → re-time |
Colour continuity | ΔE(mean f0, mean f_last) < 3 | auto |
Audio loop | last 200 ms → first 200 ms **zero click**, tail room-tone match | null test |

**Beat 10 ka design:** orb reignites → camera wapas usi macro shard composition par aata hai, same lens, same light — bas 2 frame ka difference. Viewer ko "khatam" ka ehsas hi nahi hota. **Retention 100% se upar.**

---

# 5. TEEN DELIVERIES (ek production, teen cuts)

| Cut | Length | Kaam | Note |
|---|---|---|---|
**MASTER** | **41.46s** | Main Reels/Shorts/FB upload — poori kahani, 10 beats | maujooda VO (voice-06) |
**TIGHT** | **28.0s** | TikTok + Reels sweet spot (15–30s), higher completion | **naya 5-line script**, voice-06, beats 1→3→5→7→9 compress |
**TEASER** | **12.0s** | Hook test + Stories + trailer | **no VO** — sirf sound design + captions; 0–3s hook + photo-to-flesh tease + loop |

**Kyun:** pehle 12s ke **2 hook variants** test karo (face-first vs x-ray-first), 3-second retention dekho, phir jeetne wale hook ko MASTER me lock karo. Ye "guess" nahi, measurement hai.

---

# 6. DEVICE STACK v2

### Core 5 (signature)
**D1 PHOTO-TO-FLESH** · **D2 SURFACE-OFF** · **D3 WORD-MATTER** · **D4 ONE-TAKE ILLUSION** · **D5 LIGHT-HANDSHAKE**

### Support 5 (premium tells)
| # | Device | Kaam |
|---|---|---|
**D6** | **ANAMORPHIC LIGHT** | horizontal flares — episode ki red band se match, sirf 3 shots me |
**D7** | **MACRO TRUTH** | 100 mm skin/ink/glass macro — "yeh CGI nahi lagta" ka sabab |
**D8** | **DATA LAYER** | zaroorat par technical HUD (restrained, 2 shots only) |
**D9** | **SILENCE PUNCH** | "band." aur "Main abhi bhi apni taraf" par bed 6 frames cut — retention hack |
**D10** | **SHADOW TRUTH** | har contact par asli shadow (floating feel khatam) |

### Colour script (emotional arc = colour arc)
`charcoal cold (B1–B3)` → `sickly warm trap (B4)` → **gold ignition (B5)** → `bone/paper (B6–B7)` → `steel + haze (B8)` → **red accusation (B9)** → `cold resolve (B10 → loop)`

---

# 7. SOUND — STING + BANK

### 7.1 SURFACE-OFF STING (naya, trend vector)
6.0 s, reusable, instantly recognisable:
`sub-drop (34 Hz)` → `glass shimmer riser` → **4-note motif (D–F–A–D)** on felt piano + bowed metal → `reverse tail`
- File: `sound/surface_off_sting.wav` (48 kHz/24-bit) + 0.8 s loop-safe `sting_button.wav`
- Har episode yahi sting (brand recall), aur log ise **original audio** ke tor par use kar sakte hain → audio-driven discovery.
- IG/TikTok par "original audio" upload → trending-audio slot.

### 7.2 SFX bank
23 files (48 kHz/24-bit) `assets/earshot_takes/` — jaisa v1 me tha + `surface_off.wav` + `sting_tail.wav`.
**3-layer rule** per action: transient + body + tail. **±1 frame** sync gate. **-14 LUFS / -1 dBTP** + stems.

### 7.3 Sound-off law
Poori video **mute dekh kar** samajh aani chahiye. Captions frame 0 se, **2–4 words per card**, 84 px+, contrast ≥ 4.5:1, safe area 12%. QC gate #14.

---

# 8. TIGHT CUT — naya 5-line script (28 s)
> **1.** Tumhari haar tab nahi hoti — jab tum khud ko chhota maan lete ho.
> **2.** "Mere bas ka nahi" — yeh jumla sab se mehnga hai.
> **3.** Sukoon woh nahi jo tumhe rokta hai. Sukoon woh hai jo tumhe uthata hai.
> **4.** Poori zindagi nahi. Sirf das minute. Roz.
> **5.** Main abhi bhi apni taraf hoon.

Beats: `hook → excuses → x-ray → 10-min → portrait/loop` (5 shots groups, ~28.0 s)
Script sirf tight cut ke liye — MASTER ka VO bilkul chhua nahi jayega.

---

# 9. 18 QC GATES (auto, build fail on any)

1. 1080×1920 · 30.000 fps · duration ±0.02 s
2. Frame 0 = thumbnail composition (face split present, caption present)
3. **No intro card / no fade-in** (frame 0 luminance ramp = flat)
4. Cut rhythm: 0.6 s ≤ shot ≤ 2.2 s (avg 1.6)
5. **Max gap without visual event ≤ 2.6 s**
6. **Loop SSIM(f0, last) ≥ 0.92**
7. Audio loop null-test: click-free, tail match
8. Skin-detail energy floor on face shots (plastic detector)
9. DOF + motion-blur metrics active
10. Photographic plate present in ≥ 6 shots (D1/D5 audit)
11. Device audit: D1–D5 all present; D6 3 shots; D8 ≤ 2 shots
12. Every SFX cue ±1 frame of anchor
13. Silence punches present at B3 & B9
14. **Muted watch-through**: captions carry full story (manual + contrast check)
15. -14.0 LUFS ±0.5 · -1.0 dBTP max
16. No channel clipping > 0.5% pixels; grain active; banding-free gradients
17. Caption safe area 12% + contrast ≥ 4.5:1
18. **Asset provenance**: only own plates + CC0 assets (originality-safe, no AI-video label risk)

---

# 10. LAUNCH OPS (video ke baad, 7 din)

| Din | Kaam |
|---|---|
D0 | MASTER upload (PKT 20:00–22:00), pinned comment: *"SURFACE-OFF · technique breakdown soon"* · first 60 min me har comment ka jawab |
D0 | TEASER variant A + B (12 s) — 3-s retention compare |
D1 | TIGHT cut (28 s) post — alag hook, same format |
D2 | Sting ko original-audio ke tor par publish + 15 s "how the sting was made" clip |
D3 | "Photo hai ya 3D?" carousel (frame grabs) — saves/Explore play |
D5 | **Tutorial EP1 (45 s)**: sirf D3 WORD-MATTER sikhana → log copy karein, credit dein |
D7 | Series announce: `SURFACE-OFF · EP6` + palette tease |

**Hashtags:** `#SurfaceOff #TabahiCinema #Monarch #3DEditing #VFXBreakdown`
**Watermark:** `SURFACE-OFF` 2% opacity, 3 shots.

---

# 11. KYA BANEGA — phases

| Phase | Output | Gate |
|---|---|---|
**P0** | 6 look-dev **stills** (frame 0 split, photo-to-flesh, surface-off monolith, 10:00 card, masked reveal, loop pair) | aapka HAAN |
**P1** | **5.0 s hero test** — pipeline + sting + captions | HAAN = style lock |
**P2** | plate rig · x-ray anatomy rig · 10 sets · 24 SFX · sting · sfx_map | auto QC |
**P3** | MASTER 1244 frames (8 parallel jobs) | preflight |
**P4** | TIGHT 28 s + TEASER 12 s + comp + mix + stems | 18 gates |
**P5** | Deliver: 3 MP4s + contact sheet + cue sheet + stems → Drive public | green |

---

# 12. Honest note

Koi bhi "algorithm hil jayega" ka wada nahi kar sakta — distribution platform ke haath me hai.
Jo hum control kar sakte hain aur kar rahe hain:
**frame-0 doctrine · measured loop · DM-share moment · save card · comment question · muted-proof captions · 2.2 s pattern interrupts · original audio sting · originality-safe assets · 3 lengths for A/B.**
Ye 10 cheezein wahi hain jo top-performing shorts me measurably kaam karti hain. Baaki execution ka faisla P1 hero test karega.
