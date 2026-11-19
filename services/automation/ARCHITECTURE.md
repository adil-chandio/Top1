# Agentic Workflow — Architecture

**Reality check pehle:** aapka engine **renderer** hai, **generator** nahi.
`tools/demo-render/scenes.js` line 382 — har film ka scene haath se likha function hai:
```js
export const SCENES = { 'phone-storage': phone, 'halo-desk-lamp': halo, 'last-signal': signal };
```
`tools/gecko/edit.json` — shot list haath se frame-timed. `titles.js` — captions haath se.

Iska matlab: render + QA **already solved** hai. Content generation **solved nahi** hai. Neeche wahi pipeline hai jo baaki khaali jagah bharega.

---

## 8 stages, har ek ka status

### ① IDEA — `idea.mjs`
**Input:** niche, audience, previous episodes list, optional trends
**Output:**
```json
{
  "candidates": [
    { "topic": "...", "angle": "...", "promise": "...", "why_now": "...", "competition": "low|med|high" }
  ]
}
```
**Kaise:** LLM + episode history (repeat na ho) + "one audience, one promise" rule.
**Aaj:** ❌. Prompt ka base `src/prompts.js` mein hai — reuse karo.

---

### ② ANGLE — `angle.mjs`
Ek candidate chuno → 3 hooks → ek final.
**Rule (aapki films se):** hook ek **visual** ho, sawaal na ho. Can film: "Is can ko kisi ne dabaya nahi" + buckled can pehle frame par. Reflector: "Ye light jalti dikhti hai. Lekin is mein battery hi nahi."
**Output:** `{ hook, promise, payoff, riskNotes }`
**Aaj:** ❌

---

### ③ SCRIPT — `script.mjs`
**Output:**
```json
{
  "beats": [
    { "start": 0.0, "end": 3.8, "vo": "...", "visual": "...", "purpose": "hook" },
    { "start": 3.9, "end": 18.0, "vo": "...", "visual": "...", "purpose": "explain" },
    { "start": 18.1, "end": 29.0, "vo": "...", "visual": "...", "purpose": "payoff" }
  ],
  "wordBudget": 62,
  "language": "roman-urdu"
}
```
**Word budget (measured from aapki films):** 29s film ≈ 62 Urdu words, hamara 55 words / 25s = 2.2 words/sec. Isko hard limit rakho — agent lamba likhta hai.
**Aaj:** ⚠️ prompt builder hai, structure nahi.

---

### ④ VOICE — `voice.mjs`
TTS → `vo.m4a` + word-level timestamps.
**Captions isse banti hain** — haath se nahi. Ye aapka biggest speedup hai.
**Output:** `vo.m4a`, `vo.words.json`, `captions.srt`
**Aaj:** ❌. Aapki films ki VO haath se record hui thi (`air-crush-vo.m4a`).
**Trap:** TTS ki timing script ke estimate se match nahi karti — **pehle VO banao, phir shot timing lock karo.** Ulta karoge to har caption drift karega.

---

### ⑤ SHOT PLAN — `shotplan.mjs`
**Ye pipeline ka dil hai.** Script → shot-plan.json (schema `shot-plan.schema.json` mein).
**Aaj:** ⚠️ format maujood hai (`tools/gecko/edit.json`, `src/air-crush.js`) par generalize nahi.
**Rule:** har cut 24 fps frame boundary par. Har shot ka `kind` parametric moves se aana chahiye (neeche).

---

### ⑥ ASSEMBLY — `assemble.mjs`
`shot-plan.json` + model library → Three.js scene config.
**Aaj:** ❌ **sabse mushkil layer.** `PARAMETRIC-MOVES.md` padho.

---

### ⑦ RENDER — `render.mjs` (wraps existing)
`tools/render-demos.mjs` ka logic reuse: Playwright → frames → FFmpeg.
**Aaj:** ✅ **maujood hai.** Sirf queue + retry + progress log add karna hai.
**Change:** fixed `DEMOS` list ki jagah shot-plan se config. `render-demos.mjs` ko **chhеड़na nahi** — naya file `automation/render.mjs` likho jo uska logic copy kare.

---

### ⑧ QA + DELIVER — `qa.mjs`, `deliver.mjs`
**QA (aaj maujood):** `tools/verify-reflector.mjs` — decode, loudness −14.5 LUFS, faststart, byte range, SHA. `test/film-motion.test.js` — frame-aligned cuts, caption bounds, no accidental holds.
**Deliver (aaj ❌):** Drive folder + `manifest.json` + `status.csv`.

**QA report = aapka differentiator.** Har video ke saath `qa-report.json` do. Koi competitor nahi deta.

---

## Orchestration — kya use karein

| Option | Kab | Note |
| --- | --- | --- |
| **GitHub Actions** | Aapka own channel | Repo mein already `worker.yml.in` pattern hai (`tools/gecko/natural/`) |
| **n8n** | Buyer ka install | Visual, buyer khud dekh sakta hai, debugging aasan |
| **Node CLI + cron** | Local install | Sabse simple, sabse reliable |

**Suggestion:** core `automation/*.mjs` (pure Node), aur n8n/Actions sirf wrapper. Isse ek hi codebase 3 deploy models sambhal legi.

---

## State / database

**Stage 1 (pilot):** files + JSON.
```
channel/
├── config.json          niche, audience, models allowed, language
├── episodes.json        [{id, topic, status, driveLink, qaHash}]
└── episodes/2026-11-19-slug/
    ├── 01-idea.json  02-angle.json  03-script.json
    ├── vo.m4a  vo.words.json  captions.srt
    ├── shot-plan.json  scene-config.json
    ├── final.mp4  poster.webp  qa-report.json
```
**Stage 2:** Supabase (connector already on hai) — multi-channel, dashboard, retry logic.

Files-first se shuru karo. Database baad mein.

---

## Guardrails (ye likhna zaroori hai)

1. **Fact check gate** — script ke claims ek `claims.json` mein nikalte hain, LLM unhe verify karta hai, unsure ho to visual ko "illustration" label karta hai. Aapki films already ye karti hain ("not a finite-element simulation").
2. **No stock footage** — sirf generated + licensed assets.
3. **Max 1 video/day** — burst production = mass-production signal. Ye technical limit nahi, **policy** limit hai.
4. **Human approval gate** — script aur still par buyer/owner approve karta hai. Fully unattended mat becho; ye policy risk hai aur quality bhi girti hai.
5. **Policy link** — har product doc mein YouTube inauthentic content policy ka link.

---

## Timeline (honest)

| Mahina | Deliverable |
| --- | --- |
| 2 | Shot-plan schema + 5 parametric moves + 2 models |
| 2 | Ek film end-to-end **bina haath lagaye** (script se MP4) |
| 3 | 10 moves + 5 models, Drive delivery, QA report, 10 test videos |
| 4 | Pilot install (1 buyer) + docs + pricing final |

Ye 3–4 mahine hai. 6 hafte ka nahi. Jo koi "2 hafte mein agentic video system" bole, wo jhooth bol raha hai.
