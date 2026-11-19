# Offer C — Agentic Production Workflow

**Status:** NOT BUILT. Architecture taiyaar hai, code nahi. 3–4 mahine.
**Model:** Product + install service. **Template NAHI** — running system.

---

## Aap kya bech rahe ho (ye exact likho)

> Ek running production system jo buyer ke apne accounts par chalta hai. Ye idea choose karta hai, unique script likhta hai, shot plan banata hai, 3D video render karta hai, QA karta hai, aur final file Google Drive mein daal deta hai. Uploading buyer khud karta hai.

**Jo ye NAHI hai (important):**
- ❌ Template / preset pack nahi
- ❌ "Same video, topic badal do" wala tool nahi
- ❌ Views / monetization / subscriber guarantee nahi
- ❌ Aapki API keys include nahi (buyer ke accounts)

**Kyun ye behtar bikta hai:** buyer ko *unique* content chahiye, kyunki YouTube ki inauthentic content policy template-based mass production ko demonetize karti hai. Aapka system **composition** unique banata hai. Ye aapka strongest pitch hai — aur sach hai.

---

## Pipeline (8 stages)

```
① IDEA        niche + audience + recent topic gaps → 5 candidate topics
② ANGLE       ek topic chuno, one promise, 3 hooks
③ SCRIPT      3 beats, word budget, VO text, B-roll notes
④ VOICE       TTS (buyer ki key) → audio stem + per-word timestamps
⑤ SHOT PLAN   script → shot-plan.json (frame-locked, tags, marks)
⑥ ASSEMBLY    shot plan + model library → Three.js scene config
⑦ RENDER      Chromium frames → FFmpeg → MP4 + poster + srt
⑧ QA + DELIVER decode/loudness/caption checks → Drive folder + manifest
```

Har stage ke details `../automation/ARCHITECTURE.md` mein. Shot plan ka schema `../automation/shot-plan.schema.json`.

---

## Pricing

| Package | Kya | Price | Duration |
| --- | --- | --- | --- |
| **Pilot** | 1 channel, 3 videos, aap saath banao, QA + Drive delivery | **$500–800** | 2 hafte |
| **Full Install** | Poora system unke accounts par, 1 niche tuned, handover doc | **$1,500–3,000** | 3–4 hafte |
| **Niche Pack** | Naya visual vocabulary + models (e.g. biology, finance) | **$500–900** | 1–2 hafte |
| **Managed** | Aap chala rahe ho, 8–12 videos/mahina | **$600–1,200/mo** | ongoing |
| **Support** | Install ke baad monthly | **$200–400/mo** | ongoing |

**Payment:** milestone contract. 30% start / 40% working demo / 30% install + handover.
MoR (Lemon Squeezy) se **nahi** bech sakte — wo services allow nahi karte. Direct invoice.

---

## Deploy models (buyer ko chunne do)

| Model | Kaun pay karta hai | Aapka kaam | Kisko |
| --- | --- | --- | --- |
| **BYO keys** (default) | Buyer: LLM + TTS + Google | Install, config, guardrails | Serious buyer |
| **Hosted** | Aap, monthly fee se recover | Server, metering, invoicing | Non-technical buyer |
| **Local install** | Buyer ka PC render karta hai | Setup + support | Privacy-conscious |

Har model mein **buyer ke accounts, buyer ke costs** — contract mein bada likho. Aur video ka running cost estimate do (`../automation/RUNNING-COSTS.md`).

---

## Google Drive — 2 tareeqe (ek chuno)

**A. Service account + Shared Drive** (recommended)
- Workspace account chahiye (free Gmail mein Shared Drive nahi hota)
- Service account ko Shared Drive member banao
- ✅ Clean, no consent screen, roborock nahi

**B. OAuth as user** (normal Gmail)
- Buyer ek baar consent deta hai, refresh token save
- ✅ Free Gmail bhi chalega
- ⚠️ Token revoke ho sakta hai, error handling chahiye

❌ **Service account + My Drive = kaam nahi karega.** Service account ka apna storage quota nahi hota.

Folder structure `../drive/STRUCTURE.md` mein.

---

## Contract mein ye 8 cheezein zaroor

1. Scope: 1 niche, 1 channel, X videos
2. Buyer ke accounts + costs (LLM, TTS, Drive, Google Cloud)
3. Aapki keys kabhi share nahi hoti
4. QA report har video ke saath — lekin "technically verified" ka matlab quality/monetization guarantee nahi
5. YouTube policy: buyer khud responsible, inauthentic content policy ka link
6. Support window: install ke baad 14 din free, uske baad $200–400/mo
7. Code ownership: buyer ko internal use license, resale nahi
8. Refund: milestone-based, delivered milestone ka refund nahi

---

## Sales pitch (30 second)

> "Aapka channel chahiye, par aap har video haath se nahi bana sakte. Template se banane par YouTube demonetize kar deta hai.
>
> Main aapke accounts par ek system install karta hoon jo idea se le kar final MP4 tak sab karta hai — original script, original 3D shots, QA verified — aur file aapke Google Drive mein daal deta hai. Aap sirf upload karte ho.
>
> Aapke accounts, aapki keys, aapka content. Main system deta hoon, content nahi."

Pilot offer karo. Pilot ke baghair koi $2,000 nahi dega.

---

## ⚠️ Sabse bada risk

Layer ⑥ (assembly) ka scope. Arbitrary 3D AI se nahi banta — isliye **parametric vocabulary** zaroori hai. Details `../automation/PARAMETRIC-MOVES.md` mein. Pehle 10 moves + 5 models banao, ek film end-to-end banao, **phir** bechо. Ulta karoge to pilot mein phatt jayega.
