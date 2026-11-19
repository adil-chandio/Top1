# Portfolio Content — taglines, posts, captions

Sab kuch asli films se. Clips ka source `public/demos/`.

---

## Taglines (ek chuno, sab jagah wahi)

| Tagline | Kisko pasand aayegi | Vibe |
| --- | --- | --- |
| **"3D films for ideas that deserve better than a slideshow."** | International | Professional |
| **"Aapke idea ko 3D mein samjhao, 60 second mein."** | Pakistani/Urdu | Seedha |
| **"Rendered, not recycled."** | Anti-AI-slop audience | Sharp |
| **"Har shot banaya gaya hai. Koi stock footage nahi."** | Buyers jinhe AI slop se nafrat hai | Trust |

**Recommendation:** Fiverr/Upwork par #1, Instagram par #2, website par #3.

---

## Bio (Fiverr / Upwork)

```
3D explainer films for Shorts and Reels. Every shot modelled and rendered,
then technically verified (decode, loudness, caption timing) before delivery.
Urdu + English. 9:16 native. 5 finished films — link in portfolio.
No templates. No stock footage.
```

---

## Post formula (har post) — 3 slide structure

```
SLIDE 1  →  Final shot (clean, no text)  +  1 line hook
SLIDE 2  →  Wireframe / viewport / grey-box    (process)
SLIDE 3  →  Final + CTA "aise 3D film banwani ho to DM"
```

**60–70% posts = process, 30% = final film.** Process dekhne se "khud bana sakta hoon?" wala doubt khatam hota hai.

---

## 20 posts — existing films se, naya render nahi chahiye

Source files: `air-crush-cinema-edition.mp4` (29s), `reflector-no-battery.mp4` (50s), `halo-desk-lamp-cinema-cut.mp4` (10s), `phone-storage-cinema-cut.mp4` (11s), `last-signal-cinema-cut.mp4` (12s)

| # | Clip source | Hook (Roman Urdu) | Type |
| --- | --- | --- | --- |
| 1 | air-crush 0.0–2.0 | "Is can ko kisi ne dabaya nahi. Phir ye pichak kaise gaya?" | Final |
| 2 | air-crush 8.8–11.5 | "Can ka munh paani ke neeche — yahan asli khel shuru hota hai" | Final |
| 3 | air-crush 22.9–25.1 | "Slow motion: pehli silan kaise phailti hai" | Process |
| 4 | air-crush full | "29 second. 11 shots. Har shot frame par timed." | Process |
| 5 | reflector 0.0–2.5 | "Ye light jalti dikhti hai. Battery hi nahi." | Final |
| 6 | reflector 21.1–25.8 | "Reflector ke andar 3 chhote kone — asli jawab" | Final |
| 7 | reflector 27.3–34.4 | "Ek kiran, teen bounces, poori ulti wapas" | Process |
| 8 | reflector 42.8–46.8 | "Lamp off. Ab batao, chamak kahan se aayi?" | Final |
| 9 | halo 0–3.0 | "Chhoti table, badi roshni" | Final |
| 10 | halo 6.8–10 | "Copper ring lamp — concept se render tak" | Process |
| 11 | phone-storage 0–3.3 | "Phone full? Asal wajah screen par nahi hoti" | Final |
| 12 | phone-storage 4.4–7.1 | "Files aise girti hain — ye visualization hai, animation nahi" | Process |
| 13 | last-signal 0–4 | "Ek chhota satellite, ek khamosh chaand" | Final |
| 14 | last-signal 6.1–9 | "Signal bheja. Jawab aaya." | Final |
| 15 | air-crush 3.85–8.9 | "Cutaway: 3D ke andar 3D" | Process |
| 16 | reflector 14.9–17.5 | "Aam aaina vs reflector — fark ek bounce ka hai" | Final |
| 17 | halo 0–2.8 | "Machined switch ka macro shot" | Process |
| 18 | air-crush 18.8–21 | "Bahar ki hawa andar dhakka de rahi thi" | Final |
| 19 | phone-storage 7.1–11 | "Delete karne se pehle ye check karo" | Final |
| 20 | air-crush full | "Ye 5 films maine banayi hain. Aapki agali ho sakti hai." | CTA |

**Clips nikalne ka tareeqa** (FFmpeg install karke, apni machine par):
```sh
ffmpeg -ss 8.8 -to 11.5 -i public/demos/air-crush-cinema-edition.mp4 -c copy clip.mp4
```

⚠️ Sandbox mein FFmpeg nahi hai, isliye main clips nahi kaat sakta. `services/tools/clip-plan.mjs` chala kar poora list + commands generate kar lo.

---

## Caption template (Instagram/TikTok)

```
[Hook line]

[1 line: kya dikh raha hai]
[1 line: kaise bana — "Three.js, 700 frames, 52 min render"]

3D explainer films banata hoon — product, science, mechanism.
DM for rates.

#3danimation #explainervideo #reels #urdu #motiongraphics #threejs #blender
```

---

## First 20 DM targets (outreach script neeche)

| Type | Kaun | Kyun |
| --- | --- | --- |
| 1. Product brands | Chhote desk lamp / gadget / kitchen tool brands (IG par 5–50k followers) | Product 3D promo chahiye |
| 2. Science educators | IG/YT science pages (Urdu + English) | Mechanism explainers |
| 3. SaaS startups | Indian/Pakistani early-stage | Product demo video |
| 4. Kickstarter/Indiegogo | Launch se pehle | Product animation |
| 5. Agencies | Chhoti video agencies | White-label 3D |

**Rule:** 10/day, har message personalized. Bulk DM mat karo — account ban ho jayega.

---

## Outreach script (DM)

```
Salam [naam] — [unka recent post/product] dekha, [specific baat] acha laga.

Main 3D explainer films banata hoon (9:16, Shorts/Reels ke liye).
Ye 2 mera kaam hai:
[film 1 link]
[film 2 link]

[Unke product] par ek 3D reveal soch raha hoon — 15 seconds, product
kaise kaam karta hai wo dikhaye. Sample chahiye to bana ke bhej doon?
Free hai, sirf feedback chahiye.
```

**"Free sample" trick:** ek chhota 5-second test render banao. Ye 2 ghante lagta hai aur conversion 3–5× badhata hai. **Pehle 10 prospects ke liye hi karo**, sabke liye nahi.

---

## Kya post NAHI karna

- ❌ "AI ne banaya" — log scroll kar dete hain
- ❌ Views/paise ke claims
- ❌ Before/after "AI vs us" comparisons — cheap lagta hai
- ❌ Har post par price — DM mein batao
