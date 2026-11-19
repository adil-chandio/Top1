# services/ — Business workspace

Ye folder **poora alag space** hai. Yahan jo hai wo business ka kaam hai, product code nahi.

## Rule #1 — koi purani file chhoti nahi

Is folder se bahar (`src/`, `tools/`, `index.html`, `kit.html`, `monarch-studio/`, `public/`, `test/`) **kuch bhi change nahi hota**. Ye workspace un files ko sirf **padhta** hai (context ke liye).

Agar kabhi site par integrate karna ho, tab ek **alag, chhota PR** banega jismein sirf wo change hoga jo zaroori hai. Aaj tak zero integration.

## Rule #2 — koi build script nahi

`package.json`, `vite.config.js`, `npm test` — inme kuch add nahi kiya. `services/` mein sirf `.md`, `.json`, `.mjs` (standalone) hain. `npm run build` aur `npm test` **jaise the waise** chalte hain.

`services/tools/` ke scripts **apne aap chalti hain** (`node services/tools/x.mjs`), build ka hissa nahi.

## Rule #3 — dusri chat ka kaam safe

Kyunki (a) koi purani file chhoti nahi, (b) koi script build/tests mein add nahi — dusri chat jo bhi `src/` ya `tools/` mein kar rahi hai, usse takraav **nahi** hoga. Merge conflict ka risk sirf tab hai agar koi **naya** file isi naam se banaye.

## Kya kahan hai

```
services/
├── START-HERE.md          ← yahan se shuru karo
├── PLAN.md                ← poora business plan (repo root se yahan move kiya)
├── MISTAKES.md            ← ghaltiyan jo bachni hain
├── website/               ← site par kya add karna hai (spec only, code nahi)
├── offers/                ← teeno offers ki asli copy: price, scope, delivery
├── design/                ← portfolio taglines, post ideas, outreach scripts
├── drive/                 ← Google Drive setup + folder structure
├── automation/            ← agentic workflow: architecture, schema, phases
├── ops/                   ← contracts, pricing calculator, client process
└── tools/                 ← standalone helpers (build ka hissa nahi)
```

## Merge karne se pehle

Agar kisi aur chat ne `services/` mein bhi kaam kiya, `git status` dekho — sirf apne files dekho. Ye folder naya hai, isliye conflict sirf tab hoga jab koi **wahi path** use kare.

Commit karte waqt sirf apna scope:
```sh
git add services/PLAN.md services/MISTAKES.md services/offers/
git status            # check karo kuch extra add na ho
git commit -m "docs(services): offers aur plan"
```
