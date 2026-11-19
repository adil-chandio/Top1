# Offer A — Done-for-you 3D Short

**Status:** READY. Proof maujood hai (5 films `public/demos/` mein). Aaj se bech sakte ho.
**Model:** Service. Fixed scope, fixed price, milestone payment.

---

## Kya milta hai (deliverable)

| Cheez | Detail |
| --- | --- |
| Final film | 1080×1920, H.264, 24 fps, AAC stereo, faststart MP4 |
| Length | 15s / 30s / 50s (3 tiers) |
| Script | Idea + 3 beats, client se approve karwa ke aage badhna |
| Voiceover | Urdu ya English. Buyer apni recorded voice de sakta hai (free), warna TTS ya aapki record |
| Captions | Baked-in + `.srt` file dono |
| Poster | `.webp` thumbnail |
| QA report | Duration, loudness, decode pass, SHA-256 |
| Revisions | 2 (script stage 1, picture stage 1) |
| Format | 9:16 default. 1:1 ya 16:9 optional (+20%) |

**Kya NAHI milta (contract mein bhi likho):**
- YouTube upload ya channel management
- Views/monetization ka koi wada
- Raw project files (Three.js/Blender source) — sirf final MP4. Raw files +60%.
- Client ki di hui copyrighted footage ka use (sirf licensed/own assets)
- 3 se zyada revisions

---

## Pricing

| Tier | Length | Pakistan (PKR) | International (USD) | Delivery |
| --- | --- | --- | --- | --- |
| **Short** | 15s | 25,000 | $150 | 5 working days |
| **Standard** | 30s | 45,000 | $280 | 7 working days |
| **Deep** | 50s | 70,000 | $450 | 10 working days |
| Custom model/character | — | +40,000 | +$250 | +5 days |
| 1:1 / 16:9 version | — | +5,000 | +$35 | +1 day |
| Raw source files | — | +40,000 | +$150 | +2 days |
| **Rush** (half time) | — | +40% | +40% | — |

**Pehle 3 clients:** 50% off, **is condition par** ke case study publish kar sako (naam chaho to hide kar sakte ho). Ye discount hai, permanent price nahi — contract mein likho.

**Market anchor:** international freelancer 3D product animation $25–75/hr, 5–15s clip $1,000–2,000. Aap entry price par ho, capability dekh ke badhao.

---

## Payment

- **50% advance, 50% delivery se pehle** (watermarked preview dikhane ke baad).
- International: Fiverr/Upwork escrow (sabse safe) ya Payoneer invoice.
- Local: bank transfer / Easypaisa / JazzCash. Advance ke baghair kaam shuru nahi.
- **Refund:** advance non-refundable jab script approve ho jaye. Uske pehle full refund.

---

## Delivery process (6 step)

```
1. BRIEF (day 0)      → client form bharta hai, 50% advance
2. SCRIPT (day 1-2)   → 3 beats + VO script. Client approve karta hai. ← revision gate 1
3. STYLE STILL (day 2-3) → ek single frame (still) bhejo, lighting + look approve
4. RENDER (day 3-6)   → poora film, watermark ke saath preview
5. REVISION (day 6-7) → 1 picture revision. ← revision gate 2
6. DELIVERY (day 7)   → final MP4 + poster + srt + QA report. 50% payment.
```

**Step 3 sabse important hai.** Ek still approve karwana 10 minute leta hai; poora galat render 3 din kha jata hai. Skip mat karo.

---

## Brief form ke 5 sawaal (isse zyada nahi)

1. Video kis cheez ke baare mein hai? (product / concept / mechanism)
2. Kaun dekhega? (audience — ek line)
3. Kya takeaway chahiye? (video ke baad viewer kya soche)
4. Kya reference hai? (link ya "no reference")
5. Bhasha + voice: Urdu / English / apni voice file?

Optional: brand color, logo file, product photos.

---

## Reply template — pehla inquiry aane par

```
Salam [naam],

Shukriya message ka. [Unka product/topic] ka 30s 3D film main bana sakta hoon.

Scope:
- 30 sec, 9:16, 3D (Three.js), voiceover + captions
- Script approval + 1 still approval + 1 picture revision
- Delivery: 7 working days
- Price: [X]

Kaam ka proof: [showreel link] aur [2 film links]

Shuru karne ke liye 5 sawaal ke jawab chahiye:
1-5: [brief form link]

Advance 50%, baqi delivery se pehle. Batao, aage badhein?

[naam]
```

---

## Pehla gig (Fiverr) — copy/paste

**Title:** `I will create a 3D product explainer video in 9:16 for Shorts and Reels`

**Description:**
```
I build short 3D explainer films — not stock clips, not AI slideshows.
Every shot is modelled and rendered, then technically verified before delivery.

What you get:
- 15/30/50 second vertical film (1080x1920, 24fps, MP4)
- Original 3D visuals built for your product or idea
- Voiceover (Urdu or English) + baked captions + SRT
- Poster image + QA report (duration, loudness, decode check)

My work: [showreel] | [film 1] | [film 2]

Process: brief -> script approval -> still approval -> render -> 1 revision -> delivery.
2 revisions included. No stock footage. No template reuse.
```
**Tags:** 3d animation, product video, explainer, vertical video, reels

---

## Capacity (isko ignore mat karo)

`node services/tools/render-budget.mjs` chala kar apna asli number dekho. Software WebGL render slow hai — **pehle measure karo, phir promise karo**. Agar ek 30s film 3 din leti hai, to hafte mein 2 film max. Price usi hisaab se.
