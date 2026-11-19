# Services Website

Ek **alag, standalone website** — poori tarah self-contained. Isse main app (`/index.html`, `/src/`, Vite) ka koi taalluq nahi.

```
services/website/
├── serve.mjs          ← standalone dev server (apna port)
├── site.test.mjs      ← 21 static checks
└── site/
    ├── index.html
    ├── site.css
    ├── site.js        ← sab kuch config se render hota hai
    ├── config.js      ← ⭐ SIRF YAHAN BADLO
    └── assets/        ← apni videos yahan daalo
```

## Chalana

```sh
node services/website/serve.mjs
# → http://localhost:4173
```

Custom port:
```sh
node services/website/serve.mjs --port 5000
```

Test:
```sh
node services/website/site.test.mjs      # 21 checks
```

**Note:** `npm test` aur `npm run build` is site ko touch nahi karte. Ye alag hai.

---

## ⭐ Videos kaise daalni hain (2 steps)

Abhi site **tumhari maujooda 5 films** dikha rahi hai (`public/demos/` se, read-only).

Jab nayi videos aayein:

### Step 1 — Files daalo

```
services/website/site/assets/
├── my-new-film.mp4        ← 1080×1920, H.264, faststart
└── my-new-film.webp       ← poster thumbnail
```

**Video specs (site ke liye):**
| Cheez | Value |
| --- | --- |
| Resolution | 1080×1920 (9:16) |
| Codec | H.264, yuv420p, BT.709 |
| Audio | AAC stereo 48kHz |
| Faststart | **zaroori** (`-movflags +faststart`) |
| Bitrate | 4–7 Mbps (max 25 MB per file) |
| Poster | WebP, 1080×1920 ya 720×1280 |

Poster banane ka tareeqa:
```sh
ffmpeg -ss 26.6 -i my-new-film.mp4 -frames:v 1 -q:v 80 my-new-film.webp
```

### Step 2 — `config.js` mein entry add karo

```js
{
  id: 'my-new-film',                    // unique, lowercase, dashes
  title: 'How X Works',
  category: 'Mechanism',                // Mechanism / Optics / Product / Explainer / Story
  duration: '24s',
  path: '/assets/my-new-film.mp4',
  poster: '/assets/my-new-film.webp',
  aspect: '9:16',
  featured: false,                      // true = hero mein dikhega
  line: 'One sentence about the film.',
},
```

Bas. Server reload karo — grid khud update ho jayegi. `#p-films` counter bhi khud badh jayega.

**Hero film** = jo entry `featured: true` ho aur **sabse pehle** aaye. Ek hi featured rakho.

---

## Contact setup — ye pehle karo

`config.js` mein ye 3 cheezein bharo, warna form kaam nahi karega:

```js
email: 'hello@tumhara-domain.com',
whatsapp: '923001234567',        // country code, + nahi, space nahi
formMode: 'mailto',              // 'mailto' | 'formspree' | 'none'
```

### Form mode kya chuno

| Mode | Kaise kaam karta hai | Kab |
| --- | --- | --- |
| `mailto` | User ka email app khulta hai, draft ready | **Abhi** — 0 setup |
| `formspree` | Form seedha email par aata hai, user ka app nahi khulta | Jab professional chahiye |
| `none` | Form hide, sirf email/WhatsApp | Kabhi nahi (bekaar) |

**Formspree setup (5 min, free 50/month):**
1. formspree.io par account banao
2. New form → endpoint copy karo (`https://formspree.io/f/xxxxxxx`)
3. `config.js` mein: `formspree: 'https://formspree.io/f/xxxxxxx'`, `formMode: 'formspree'`
4. Ek test submission bhejo, email check karo. Phir live.

⚠️ Jab tak email actually receive na ho, form **live mat karo**.

---

## Pricing badalna

`config.js`:
```js
pricing: {
  short: 25000,      // 15 sec
  standard: 45000,   // 30 sec
  deep: 70000,       // 50 sec
},
currency: 'PKR',     // ya 'USD'
```

`0` rakho → "Get a quote" dikhega, price nahi (negotiation-friendly).

**Baaki price list** (custom model, extra revision, rush) — `../ops/PRICING.md` mein.

---

## Offer C ko on karna

Abhi off hai. Jab pipeline ek video end-to-end bana le:

```js
showWorkflow: true,
```

Section `#workflow` khud dikh jayega. Tab tak hidden hai — jhoota promise nahi.

---

## Site ka structure

| Section | Kya |
| --- | --- |
| Hero | Featured film + tagline + 3 proof numbers |
| `#work` | 5 films ka grid, tap par lightbox |
| `#services` | 3 tiers, price, delivery time, included/excluded |
| `#process` | 6 steps, 2 approval gates |
| `#brief` | 5-field form + direct contact |
| `#workflow` | Offer C (hidden until ready) |
| `#faq` | 8 questions |
| Footer | Contact + socials |

---

## Production deploy

Ye plain static files hain. Koi build step nahi.

**Vercel (connector on hai):**
```sh
# Vercel ko repo se connect karo
# Root directory: services/website/site
# Framework: Other
# Build command: (khali)
# Output directory: .
```

**Ya Netlify / Cloudflare Pages:** wahi — directory `services/website/site`, no build.

**Zaroori:** deploy se pehle `config.js` mein contact + pricing bharo. Warna live site par form dead hoga.

### Apni domain
`top1.studio` jaisa domain le lo (PKR ~4,000/year). Fiverr/Upwork par professional lagta hai. Deploy ke baad DNS point karo.

---

## Kya main app ko chhua?

**Nahi.** Ye ek audit hai:

| Main app | Status |
| --- | --- |
| `index.html` | chhua nahi |
| `kit.html` | chhua nahi |
| `src/` | chhua nahi |
| `vite.config.js` | chhua nahi |
| `package.json` | chhua nahi |
| `npm test` | is site ko touch nahi karta |
| `public/demos/` | sirf **read** hota hai |

Server `public/` se videos read karta hai (read-only, path-traversal blocked, tested).

Ye site main site ko **replace** nahi karti. Main site = Top1 Kits + Monarch Studio (prompt shop). Ye site = **3D services** (paise yahan se aate hain).

**Do alag businesses ek repo mein.** Baad mein decide karo: merge karna hai ya alag rakhna hai.

---

## Agla kaam

1. ⬜ `config.js` mein email + WhatsApp daalo
2. ⬜ Form test karo (apna hi email)
3. ⬜ `services/website/site/assets/` mein apni videos daalo
4. ⬜ Vercel par deploy karo
5. ⬜ Domain kharido
6. ⬜ Fiverr/Upwork profile par yahi link daalo
