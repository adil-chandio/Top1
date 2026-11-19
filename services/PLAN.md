# Top1 — 3D Video Services + Agentic Workflow Business Plan

**Status:** Planning only. Koi code change nahi. Ye "kya, kahan se, kaise" ka jawab hai.

---

## 1. Repo ka asli sach (technical)

### Jo maujood hai — aur uski asli taqat

| Cheez | Kahan | Kaam |
| --- | --- | --- |
| 5 finished 3D films | `public/demos/` | Portfolio / service ka proof |
| Render engine | `tools/render-demos.mjs` + Playwright Chromium + FFmpeg | Frame-by-frame 3D → MP4, deterministic |
| Blender pipeline | `tools/gecko/*` (bpy 4.3) | Gecko jaisa complex model |
| **Verification culture** | `tools/verify-reflector.mjs`, `audit.py`, 38 tests | Decode check, loudness (−14.5 LUFS), faststart, SHA — **ye aapka asli moat hai** |
| Production docs | `monarch-studio/PRODUCTION.md` | Client ko dikhane wala proof |

### Jo maujood NAHI hai (aur ye sabse important baat hai)

```
scenes.js  →  har film ka scene HAATH SE likha function hai
              ('phone-storage': phone, 'halo-desk-lamp': halo, 'last-signal': signal)
edit.json  →  shot list HAATH SE frame-number par timed hai
titles.js  →  captions HAATH SE likhe hain
render-demos.mjs →  fixed list se ID leta hai, naya content nahi banata
```

**Matlab:** aapke paas ek **excellent render + QA engine** hai. Wo engine aapke haath ka likha content render karta hai. Wo apne aap se kisi bhi topic ka 3D scene **nahi bana sakta**.

Isi liye "agent khud unique video banayega" kehne ke liye ek khaali pipe bharna hai — aur wahi asli product hai. Ye 6 hafte ka kaam nahi, 3–4 mahine ka kaam hai. Neeche architecture.

---

## 2. Offer C — Agentic Production Workflow (aapka matlab sahi hai, scope ye hai)

### Aap kya de rahe ho

Ek **running system** jo buyer ke apne accounts par chalta hai:

```
Idea choose  →  Research + angle  →  Script (unique)  →  VO + captions
   →  Shot plan (JSON)  →  3D scene assembly  →  Render  →  QA agent
   →  Google Drive folder mein final MP4 + manifest  →  buyer khud YouTube par upload karta hai
```

Aap **template nahi** bech rahe — aap **wo machine** bech rahe ho jo har video ka content naya banati hai. Bilkul sahi positioning hai. Isme aap YouTube policy ke un-aam sellers se **behtar** position par ho.

### Architecture — 6 layers (aur har layer ka status)

| # | Layer | Kya karta hai | Aaj ka status |
| --- | --- | --- | --- |
| 1 | **Brief agent** | Niche + audience → topic chunk, angle, promise | ❌ banana hai (LLM) |
| 2 | **Script + VO agent** | Hook/beats/timing → narration → TTS → per-word caption timing | ⚠️ prompt builder hai (`src/prompts.js`), VO haath se record hui thi |
| 3 | **Shot plan agent** | Script se `edit.json` jaisa shot spec banata hai | ❌ banana hai — **schema aapke paas already hai** (`tools/gecko/edit.json`) |
| 4 | **Scene synthesis** | Shot spec → Three.js scene | ❌ **sabse mushkil** — neeche detail |
| 5 | **Render + QA** | Chromium frames → FFmpeg → verify | ✅ **maujood hai**, bas queue/orchestration chahiye |
| 6 | **Delivery agent** | Google Drive folder + manifest + status log | ❌ banana hai |

### Layer 4 — yahan sab phansenge, isliye seedha sach

Arbitrary 3D scene AI se generate karna abhi bhi reliable nahi hai. Isliye **akele** ye problem solve karne ki koshish mat karo.

**Sahi rasta: parametric visual vocabulary.**

Apni 5 films ko dekho — unme sirf ~10 visual moves repeat ho rahe hain:

```
1. Object reveal (slow orbit + rim light)
2. Exploded / cutaway view
3. Mechanism motion (rig flip, hinge, buckle)
4. Comparison (do states side by side)
5. Data/quantity visualization (bars, blocks, flow)
6. Camera push-in on detail
7. Arrow / vector / tracer overlay
8. Freeze + label ("this part")
9. Slow replay (same motion, 0.5× clock)
10. Title / payoff card
```

Agar ye 10 moves **parametric functions** ban jayein (`reveal({model, duration})`, `cutaway({model, axis})`), to agent ko poora 3D scene likhna nahi padta — agent **shot plan** likhta hai (`reveal → cutaway → mechanism → payoff`), aur engine usko assemble karta hai. Ye dramatically reliable hai.

**Iska matlab:** har naya topic 100% unique 3D nahi hoga. **Composition** unique hogi, **model library** shared hogi. Aur ye bilkul theek hai — bilkul waise hi jaise ek animation studio karta hai. Client ko yahi samjhao: "3D models ki library hai, har video ka edit, script aur arrangement naya hota hai." Jhooth mat bolo ki har baar scratch se naya model banta hai.

### Pehla niche — ek chuno, warna product bekaar

Sabse aasan aur sabse zyada bikne wala: **"X kaise kaam karta hai" — physical mechanism explainers** (can, reflector, gecko, lamp — ye chaaron isi family ke hain).

Isme aapko: ~8 reusable models, 10 reusable moves, ek repeatable script rhythm. Dusre niche ke liye poori library dobara banti hai. **Pehla version ek niche ke liye becho.**

### Google Drive — do technical traps jo abhi jaan lo

1. **Service account seedha My Drive mein upload nahi kar sakta.** Google service accounts ka apna storage quota nahi hota — error aata hai. Do hi hal hain:
   - **Workspace account** → Shared Drive use karo (service account ko member banao). Ye clean hai.
   - **Normal Gmail** → Shared Drive nahi hota, is liye **OAuth as the user** (refresh token) karna padega. Buyer ko ek baar consent screen dikhega.
2. **Folder structure** pehle tay karo, warna 50 videos ke baad chaos:
```
/ChannelName/
  /2026-11-19_topic-slug/
     final.mp4          (1080×1920, H.264, faststart)
     poster.webp
     captions.srt
     script.md
     shot-plan.json
     qa-report.json     (duration, loudness, decode, hash)
```
`manifest.json` + `status.csv` (episode, status, render time, cost, link) — buyer ko yahi chahiye hota hai.

### "API ki baat nahi kar rahe" — par ek sach

Buyer ke paas LLM, TTS aur Drive ke **accounts** hone hi padenge. Iske 3 model hain:

| Model | Kaun pay karta hai | Aapko kya karna | Price |
| --- | --- | --- | --- |
| **BYO keys** (recommended) | Buyer apna OpenAI/Gemini + TTS + Google account lagata hai | Install + config + guardrails | $1,500–3,000 setup |
| **Aapka hosted** | Aap pay karte ho, buyer ko monthly | Server, metering, invoicing | $300–600/mo per channel |
| **Local install** | Buyer ka laptop/PC render karta hai | Setup + support | $800–1,500 |

Aap API **bech** nahi rahe — aap wo system bech rahe ho jo unki API par chalta hai. Ye bilkul theek hai, bas contract mein likho: "buyer ke accounts, buyer ke costs."

Aur realistically: har video ka running cost = LLM (cents) + TTS (~$0.10–0.50) + render compute (aapka software WebGL — **slow**, isko pehle measure karo). Buyer ko iska estimate do, warna 2 mahine baad blame aap par aayega.

### QA agent — yahi aapka differentiator hai

Baaki log "automation" bechte hain jo chup-chaap tut jata hai. Aapke repo mein pehle se:
- Full picture + sound decode test
- Loudness/peak measure (−14.5 LUFS target)
- Caption bounds + frame-aligned cuts + no accidental holds (`test/film-motion.test.js`)
- Byte-range serve check, SHA-256 manifest

**Isko product feature banao.** Har video ke saath `qa-report.json` — "ye video technically verified hai." Koi competitor ye nahi deta.

### Pricing (ye template se 10× zyada hai, kyunki kaam bhi 10× hai)

| Package | Kya | Price |
| --- | --- | --- |
| **Pilot** (1 channel, 3 videos) | Install + 3 videos saath mein banao + QA + Drive delivery | **$500–800** (isi mein case study lo) |
| **Full install** | Poora system, unke accounts par, 1 niche ke liye tuned, 2 hafte support | **$1,500–3,000** |
| **Managed** | Aap chala rahe ho, mahine ke 8–12 videos | **$600–1,200/mo** ya per-video $60–120 |
| **Niche library add-on** | Naya visual vocabulary + models | **$500–900** |

Monthly support **alag** rakho ($200–400/mo), warna forever free consulting ban jaoge.

---

## 3. Teen offers — final order (yahi karo)

| Offer | Kya | Kab | Kitna |
| --- | --- | --- | --- |
| **A. 3D Short service** | Ek film, 15–50s, done-for-you | **Abhi** (proof ready) | PKR 25–60k / $150–400 |
| **B. Process kit** | Script→shotplan→render checklist | 3–4 hafte | $49 → $99–149 |
| **C. Agentic workflow** | Poora system, Drive tak | 3–4 **mahine** | $1,500–3,000 + support |

Offer A pehle kyun: wo aapke render pipeline ko **paise dete hue test** karta hai, aur Offer C ka **proof** banta hai. Jab tak 5 real clients ke films nahi banaye, aapko nahi pata aapka system kahan tootta hai.

---

## 4. Paisa kahan se (Pakistan)

| Kya | Kahan se | Payout |
| --- | --- | --- |
| Service A | Fiverr / Upwork / direct invoice (advance 50%) | Payoneer → local bank |
| Product B | Lemon Squeezy ya Payhip (MoR) | Payoneer / wire |
| **Workflow C** | **Direct invoice only** (contract, milestone-based) | Bank transfer / Payoneer invoice |

**Zaroori:** Lemon Squeezy/Paddle **services allow nahi karte** — sirf digital products. Isliye C kabhi MoR se nahi. C ke liye milestone contract: 30% start, 40% working demo, 30% install + handover. Gumroad se bacho (Stripe-only, Pakistan unsupported).

Verify karo signup se pehle — rules badalte rehte hain.

---

## 5. Promotion — results dikha kar bechna

```
1. Short post (proof)  →  2. Free sample / screening room  →  3. Order / kit / pilot
   Reels + TikTok + YT       /monarch-studio/, /kit.html        Fiverr, invoice, LS
```

- **Pehle 20 posts** maojaooda 5 films ke clips se — naya render nahi chahiye. Ek film = 4–6 clips.
- **60–70% process dikhao** (wireframe → lighting → final), 30% final film. Isse "khud bana sakta hoon?" doubt khatam hota hai.
- C ke liye content ka angle: **"system kaise kaam karta hai"** — ek video ki screen recording: topic → shot plan → render → Drive. Ye Offer C ka best sales asset hai.
- **Niche:** mechanism/"how X works". Dono nahi.

---

## 6. Website par kya badalna padega

Abhi site kehti hai "Product preview only. Checkout is not open." aur `#custom`: "Planning files, not a finished video." Ye aapke naye offer ke khilaf hai.

1. Naya section: **"Done-for-you 3D Short"** — 3 tiers + delivery time + order button.
2. `#custom` copy badlo — finished film bech rahe ho.
3. **Contact channel add karo** (email + brief form) — abhi zero hai, koi order kar hi nahi sakta.
4. **Agentic workflow page** — "ek system, aapka channel, aapke accounts" + demo screen recording + pilot CTA.
5. Showreel 60–90s.
6. Product checkout site par nahi — MoR link.

---

## 7. Roadmap

**Hafta 1 — paisa on**
- Showreel 90s (existing films se)
- Fiverr gig + Upwork profile
- Email + brief form live, site par link
- WP: 2 case-study posts

**Hafta 2 — outreach**
- Roz 10 DMs (product brands, science/tech educators, Urdu tech pages)
- Roz 1 process reel
- Pehle 3 clients 50% off, case study ki condition par

**Hafta 3–4 — deliver + document**
- Pehla paid film, 2 revisions max, verified export, invoice
- Jo process use kiya wo likho → Offer B ka raw material
- **Offer B $49 par launch**

**Mahina 2 — Offer C ka engine (asli kaam)**
- Layer 3 shot-plan schema finalize (`edit.json` se generalize)
- Layer 4: 10 parametric moves + 5 models → ek film end-to-end agent se banao
- **Measure:** ek video ka render time + cost. Ye number poora pricing decide karega
- Layer 6: Drive delivery (Shared Drive ya OAuth — pehle decide)

**Mahina 3 — internal test**
- Apne ek channel par 10 videos, bina haath lagaye
- QA agent ke saath
- 3 pilot buyers dhundo ($500–800)

**Mahina 4 — sell**
- Pilot deliverables → real installs
- Niche library add-on launch

---

## 8. Repo mein kya banega (jab bolo)

| # | Kaam | File | Kab |
| --- | --- | --- | --- |
| 1 | Showreel cut | `tools/showreel.mjs` | Hafta 1 |
| 2 | Service section + tiers + CTA | `index.html`, `src/styles.css` | Hafta 1 |
| 3 | Brief form | `src/brief.js` | Hafta 1 |
| 4 | Process kit docs | `kits/3d-process/` (private) | Hafta 3 |
| 5 | **Shot-plan schema** (`edit.json` generalize) | `automation/schema/shot-plan.json` | Mahina 2 |
| 6 | **Parametric moves library** | `tools/grammar/moves/*.js` | Mahina 2 |
| 7 | Orchestrator (idea→Drive) | `automation/pipeline.mjs` | Mahina 2 |
| 8 | QA report generator | `automation/qa.mjs` | Mahina 3 |
| 9 | Agentic workflow product page | `workflow.html` | Mahina 4 |

Note: `npm ci` chalana padega — sandbox mein `node_modules` nahi tha, isliye 2 tests "fail" dikhe (vite missing). Code ki ghalti nahi.

---

## 9. Risks

1. **Layer 4 ka scope** — arbitrary 3D AI se nahi banta. Parametric vocabulary se shuru karo, warna 6 mahine kuch deliver nahi hoga.
2. **Render capacity** — software WebGL slow hai. Pehle measure karo, phir delivery promise karo. 8 videos/mahina shayad laptop par na ho.
3. **Buyer ke accounts** — LLM/TTS/Drive costs buyer ke. Contract mein likho, warna blame aap par.
4. **Google Drive quota** — service account My Drive mein upload nahi karta. Test karo pehle.
5. **Policy** — aapka model (unique script + custom 3D) defensible hai. Kabhi "monetization guarantee" mat bolo. Har product ke saath YouTube ki inauthentic content policy ka link do.
6. **Portfolio self-initiated hai** — koi real client kaam nahi. Pehle 3 sasta karo, case study lo.
7. **Support trap** — "install + 2 hafte support" likho, warna buyer 6 mahine tak free consulting karega.

---

## 10. Aaj ke 3 kaam

1. Showreel 90s cut (5 films, FFmpeg).
2. **Render speed measure karo** — ek 10s film render karke time note karo. Ye number sab kuch decide karega.
3. Email address + site par link. Bas.
