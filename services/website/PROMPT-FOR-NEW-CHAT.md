# Prompt — is chat ko repo ke saath kholo

Neeche diya gaya poora block copy karo aur **naye chat** mein paste kar do.
Naya chat `adil-chandio/Monarch.studio` repo khol le, phir kaam shuru kar de.

---

```
Repo: https://github.com/adil-chandio/Monarch.studio
Branch: main (repo abhi bilkul khali hai — pehli push tum karo)

TASK: Ek single-file static website deploy karo. Kaam tayyar hai, sirf copy karna hai.

=== SOURCE FILE ===
Repo mein is path par file maujood hai (60 KB, ek hi self-contained HTML):
  services/website/top1-services-site-standalone.html

Path: adil-chandio/Top1, branch: arena/0c977a6f-top1, commit: bb99014

Uss file ka poora content padho. Usme CSS, JS aur config — sab inline hai.
Koi dependency nahi, koi build step nahi, koi node_modules nahi.

=== KYA KARNA HAI ===

1. Us file ka content uthao aur Monarch.studio repo mein
   `index.html` naam se daalo (root mein, kisi folder mein nahi).

2. Commit message:
   "Add Top1 3D explainer film services site"

3. GitHub Pages enable karo:
   Settings → Pages → Source: "Deploy from a branch"
   → Branch: main → Folder: / (root) → Save

4. Live URL hoga:
   https://adil-chandio.github.io/Monarch.studio/

5. URL khol ke verify karo (curl ya browser):
   - Page load hoti hai, 404 nahi
   - "Your idea, rendered." h1 nazar aata hai
   - 9 film cards render hote hain
   - Prices 25,000 / 45,000 / 70,000 dikhte hain
   - "Get a quote" form submit karne par mailto khulta hai
     (alipvip19@gmail.com par)
   Report karo kya pass hua, kya fail.

=== FILE KE ANDAR KYA HAI (reference) ===
- Top1 ka 3D explainer film services offer page — dark cinematic design
- 9 films, sab Google Drive se stream hote hain (public folder
  1xdVBLKSzKWUdasQDZ6DZeVuF6LwCZON8), koi MP4 repo mein nahi
- 3 pricing tiers: Short 15s = PKR 25,000 | Standard 30s = PKR 45,000
  | Deep 50s = PKR 70,000
- 8 sections: hero, work, services, process, brief, workflow (hidden),
  faq, band
- Brief form mailto mode mein hai, CONFIG.email = alipvip19@gmail.com
- Film thumbnails Drive ke thumbnail endpoint se:
  https://drive.google.com/thumbnail?id=FILE_ID&sz=w1080
- Film embeds Drive preview iframe se:
  https://drive.google.com/file/d/FILE_ID/preview

=== ZAROORI BAATEIN ===
- Teen pages aur unka content purane WordPress site par pehle se live hai
  (https://adilchandio4.wordpress.com). Unhe chhedna nahi. Yeh GitHub
  wala naya clean deployment hai.
- Repo Public rehna chahiye, warna free GitHub Pages kaam nahi karega.
- Agar file 100 MB se bara ho to split mat karo — 60 KB hai, seedha push.
- Agar push 403 de to batao; matlab credentials ka masla hai, file ka nahi.
- Deploy ke baad URL zaroor verify karo, "ho gaya" maan kar mat chhodo.

=== ACCEPTANCE ===
https://adil-chandio.github.io/Monarch.studio/ khulta hai, saaf dikhta hai,
9 films ke thumbnails load hote hain, form email draft banata hai.
```

---

## Note (tumhare liye, prompt ka hissa nahi)

Do cheezein jo prompt mein daali hain kyunki woh aage kaam aayengi:

1. **Exact path aur commit** — taake naya chat file dhoondhta na rahe.
2. **Verification step** — taake woh bhi "ho gaya" keh kar na chhode,
   jaisa main kar raha tha.
