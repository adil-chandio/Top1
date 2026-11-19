# Offer B — The 3D Production Kit

**Status:** SKELETON. `kit.html` par 6-step outline hai, asli files nahi. 3–4 hafte ka kaam.
**Model:** Digital product. Passive income. Buyer khud render karta hai.

---

## Product kya hai

Ek **working production system** ka documentation + assets, jo buyer ko apna 3D explainer banane deta hai — bina aapke.

**Positioning:** "Ye course nahi hai. Ye wo actual files hain jinse maine 5 films banayi hain."

Ye sach hai — `monarch-studio/PRODUCTION.md`, `public/samples/air-crush-blueprint.md`, `reflector-blueprint.md` asli production documents hain. Unhi ko generalize karna hai.

---

## Contents (8 items — ye deliver karna hai)

| # | File | Kya | Aaj status |
| --- | --- | --- | --- |
| 1 | `01-angle-and-hook.md` | Topic → one audience + one promise + 3 hook options | Banana hai |
| 2 | `02-script-formula.md` | 3-beat structure, word budget (45–55 words / 25s), Urdu + English examples | ⚠️ partly `src/prompts.js` mein |
| 3 | `03-shot-plan-spec.md` | Shot list kaise likho: frame numbers, tags, jumpTo. **`src/air-crush.js` ka asli format** | ✅ Format maujood |
| 4 | `04-visual-direction.md` | Prompt per shot: subject, framing, motion, style lock | ✅ `public/samples/*.md` mein |
| 5 | `05-render-setup.md` | Three.js + Chromium + FFmpeg setup, resolution strategy, render time | ✅ `README.md` mein, generalize karna hai |
| 6 | `06-qa-checklist.md` | Decode, loudness (−14.5 LUFS), faststart, caption bounds, hash | ✅ `tools/verify-reflector.mjs` |
| 7 | `blueprints/` | 2 poore worked examples (can + reflector), editable | ✅ **ready** |
| 8 | `walkthrough.mp4` | 12–15 min screen recording: ek film shuru se end tak | Banana hai |

**Item 1, 2, 8 banana hai. Baqi 5 generalize karna hai.** Isliye 3–4 hafte, 3 mahine nahi.

---

## Pricing

| Tier | Kya | Price |
| --- | --- | --- |
| **Kit** | 8 items, no support | **$49** launch → $99 |
| **Kit + Walkthrough** | + 15 min video + email support 30 din | **$79** → $149 |
| **Studio** | + 1-on-1 call (60 min) + apni film ka review | **$199** → $299 |

**Launch strategy:** 20 "founding" copies $29 par, is condition par ke feedback do. Phir $49. Phir $99. Har 50 sales par badhao.

---

## Kahan bechna hai

| Platform | Kyun | Note |
| --- | --- | --- |
| **Lemon Squeezy** | MoR, VAT sambhalta hai, Payoneer payout Pakistan ✅ | **Digital products allow, services nahi** |
| **Payhip** | Simple, PayPal/Payoneer | Backup |
| **Gumroad** | ❌ **mat karo** — Stripe-only payout, Pakistan unsupported | — |

Launch se pehle khud verify karo: platform ki country page + TOS. Rules badalte rehte hain.

**Delivery:** MoR ka secure file link. Repo mein premium files **nahi** (`.gitignore` mein `/deliverables/` already hai — wahan rakho, ya private repo).

⚠️ **Kabhi premium files public repo mein na rakho.** Aaj `public/samples/` mein 2 free samples hain (theek hai, wo marketing hai). Paid items private rahenge.

---

## Launch checklist

```
[ ] 8 items complete
[ ] 2 blueprints editable versions (with notes)
[ ] Walkthrough recorded + captioned
[ ] License likha: personal + commercial use for own videos, redistribution nahi
[ ] Refund policy: 7 din, agar files download nahi ki (ya platform ki policy)
[ ] Lemon Squeezy product page + price
[ ] 3 sample pages free (funnel)
[ ] Launch post: Reels + LinkedIn + Urdu tech groups
[ ] Support email + 48h response promise
```

---

## License (simple rakho)

**Buyer kar sakta hai:** apne ya client ke videos banane ke liye use kare (commercial OK), modify kare.
**Buyer nahi kar sakta:** kit ko dobara bechے, course bana ke bechे, public repo mein daale.
**Aap:** warranty nahi ke aapka render unke hardware par chalega; support 30 din.

---

## Funnel — free se paid tak

```
Free: /samples/25-second-short.md  +  /kit.html outline  +  Showreel
   ↓  (email capture)
Email list: weekly ek process tip + ek clip
   ↓
$29–49 kit
   ↓
$199 studio tier / custom work (Offer A)
```

**Email capture abhi nahi hai** — ye pehla kaam hai. Bina list ke product launch = ek din ka traffic, phir zero.
