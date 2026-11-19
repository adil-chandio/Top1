# Website — kya add karna hai (spec only)

**Ye file koi code nahi hai.** Design + copy specification hai, taake jab integrate karo to ek chhota, saaf PR bane.

⚠️ **Is chat mein site ki ek bhi file nahi chhui.** Ye sirf spec hai. Integration alag PR mein, alag chat mein.

---

## Abhi site kya kehti hai (aur problem)

| Jagah | Current text | Problem |
| --- | --- | --- |
| `kit.html` hero | "Product preview only. Checkout is not open." | Buyer ko lagta hai shop band hai |
| `index.html` `#custom` | "Draft a brief for a tailored script and scene plan" | Aap **finished film** bech rahe ho, plan nahi |
| `index.html` `#custom` aside | "Planning files, not a finished video." | Ye ab galat hai |
| Poore site | **koi email/form/contact nahi** | **Aaj koi order kar hi nahi sakta** |

---

## Priority 1 — Contact + order channel (yeh sabse pehle)

Site par 3 jagah contact chahiye:

1. **Header** — "Start a project" button (prominent, `Try it free` ke bagal mein)
2. **`#custom` section** — button badlo: "Create a custom brief" → **"Get a 3D quote"**
3. **Footer** — email link

**Bina iske promotion bekaar hai.** Ye ek ghante ka kaam hai, aur bina iske baaki sab ruk jaata hai.

---

## Priority 2 — Naya section: `#services`

`#kits` ke **baad** aur `#builder` se **pehle** — kyunki visitor ko pehle "main ye bana sakta hoon" pata chalna chahiye, phir prompt builder.

```
┌──────────────────────────────────────────────────────┐
│  03 / DONE FOR YOU                                    │
│                                                       │
│  Your idea, rendered.                                 │
│  Original 3D films for Shorts and Reels —             │
│  scripted, modelled, voiced, and verified.            │
│                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │ 15 SEC  │  │ 30 SEC  │  │ 50 SEC  │              │
│  │ PKR 25k │  │ PKR 45k │  │ PKR 70k │              │
│  │ 5 days  │  │ 7 days  │  │ 10 days │              │
│  └─────────┘  └─────────┘  └─────────┘              │
│                                                       │
│  [ Get a quote ]        Includes / Not included →     │
└──────────────────────────────────────────────────────┘
```

**Kicker number:** abhi `#builder` = 03, `#sample` = 04, `#custom` = 05, FAQ = 06.
Naya section 03 ho jayega, baaki +1. Ya `#custom` ko hi replace kar do (behtar — kam scroll).

---

## Copy — exact text

**Heading:** `Your idea, rendered.`
**Lede:** `Original 3D films for Shorts and Reels. Scripted, modelled, voiced, and technically verified before delivery.`

**3 cards:**

| Card | Title | Price | Delivery | Line |
| --- | --- | --- | --- | --- |
| Short | 15 seconds | PKR 25,000 | 5 days | One clear mechanism or product reveal |
| Standard | 30 seconds | PKR 45,000 | 7 days | The three-beat explainer format |
| Deep | 50 seconds | PKR 70,000 | 10 days | Full topic with cutaways and replay |

**Included list:**
- Original 3D animation (no stock footage, no templates)
- Script + voiceover (Urdu or English)
- Baked captions + `.srt` file
- Poster image
- QA report (duration, loudness, decode verification)
- 2 revisions

**Not included:**
- Uploading to any platform
- Views, monetization, or subscriber guarantees
- Raw 3D project files (available at extra cost)

**CTA:** `Get a quote` → brief form
**Secondary:** `Watch the films` → `#demos`

---

## Priority 3 — `#custom` copy fix

**Before:**
> "Draft a brief for a tailored script and scene plan. Bring the topic and audience; specify the tone and takeaway you want."
> "Planning files, not a finished video."

**After:**
> "Tell us the topic, the audience, and the takeaway. You get a finished 3D film — script, voiceover, captions, and a verified export."
> "A finished film, not a planning document."

Aside list bhi badlo:
- Before: "Hook and voiceover script / Shot-by-shot visual direction / Caption ideas and editable prompts"
- After: "Finished 1080×1920 film / Original 3D animation / Voiceover + captions / QA-verified export"

---

## Priority 4 — Brief form

**Ek page, 5 fields, koi account nahi:**

```
1. What's the video about?          [text, required]
2. Who is it for?                   [text, required]
3. What should they take away?      [text, required]
4. Reference or link (optional)     [url]
5. Language + length                [select: Urdu 15s / Urdu 30s / ...]
   + Your email                     [email, required]

[ Send brief ]
```

**Kaise kaam kare (3 options, aasan se mushkil):**

| Option | Kaam | Effort |
| --- | --- | --- |
| **mailto:** (fastest) | Form submit → user ka email client khul jaye, body prefilled | 30 min |
| **Formspree / Tally** | Free tier, email par aata hai | 1 ghanta |
| **Vercel function + Resend** | Own domain se email, professional | 3 ghante |

**Recommendation:** shuru mein Tally ya Formspree. Vercel function baad mein.

⚠️ Jab tak email actually receive na ho raha ho, form **publish mat karo**. Test karo pehle.

---

## Priority 5 — Offer C page (`/workflow/`)

Sirf 4 hafte ke baad, jab ek video end-to-end chal jaye.

```
Heading:  One system. Your channel. Your accounts.
Lede:     An agentic production pipeline that goes from topic to a
          finished, QA-verified video in your Google Drive.
          You upload. It does the rest.

[ screen recording of the pipeline — 40 sec ]

What it does:        ① idea  ② script  ③ voice  ④ shot plan
                     ⑤ 3D render  ⑥ QA  ⑦ Drive delivery

What you get:         system install, config, one niche tuned,
                      handover docs, 14 days support

What it isn't:        a template pack, a "make money" tool,
                      a view guarantee, or our API keys

Pricing:              Pilot $500–800 · Install $1,500–3,000

[ Book a pilot ]
```

**Policy line (zaroor rakho):**
> "This system produces original scripts and compositions. It does not generate templated or mass-produced content. Clients are responsible for platform compliance, including YouTube's inauthentic content policy."

---

## Priority 6 — Nav update

```
Cinema Cuts | 3D Services | The Kits | Prompt Builder | Workflow
```

Naya `3D Services` sabse pehle (paisa wahan se aata hai). `Workflow` sirf jab ready ho.

---

## Integration rules (agar main karta hoon)

1. Sirf `index.html` + `src/styles.css` + ek naya `src/brief.js`
2. `vite.config.js` mein koi change nahi
3. Koi naya dependency nahi
4. `npm test` pass rehna chahiye
5. **Ek commit, ek PR** — takay dusri chat se takraav na ho
6. `#kits` aur `#demos` ka content **chhua nahi** — wo already accha hai

---

## Jo change nahi karna

- ❌ Cinema Cuts section — wo proof hai, badalne ki zaroorat nahi
- ❌ Prompt builder — wo free funnel hai
- ❌ Monarch Studio — uski apni branding hai
- ❌ MP4/WebP files — already optimized
