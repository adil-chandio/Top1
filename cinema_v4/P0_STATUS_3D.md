# P0 · 3D STAGE — STATUS (honest)

**Branch:** `arena/2a8ad29e-top1` · **Date:** 15 Nov 2026
**Koi video nahi bana. Blender chal gaya, scene adhoora hai.**

---

## 1. Jo naya aur asli hai

| Cheez | Status |
|---|---|
| **Blender 5.0.1 headless is sandbox me** | ✅ chal raha hai |
| X/GL libs (nahi thi image me) | ✅ 61 no-op symbols ke stubs bana kar (`naam_film/tools/xstubs.sh`) |
| **Cycles CPU render** | ✅ `cycles.device='CPU'`, OIDN denoise, AgX |
| **Greenscreen key** | ✅ `plates/char_keyed.png` — 54.9% opaque, 44.2% clean, spill suppressed |
| **Chest opened (D1 ke liye)** | ✅ `plates/char_xray.png` — chest region ka alpha 0.10 tak khula |
| **3D rig** | ✅ ribcage (torus arcs + spine), emissive heart + heart light |
| **Set** | ⚠️ bana hai par **bekaar lagta hai** (neeche) |

`naam_film/scene3d.py` — 7 shots: `hero · macro · xray · d1 · surfaceoff · wordmatter · mask`.

## 2. Naapa hua render cost (yeh sabse important number hai)

| Res / spp | Time per frame |
|---|---|
| 540×960 / 24 spp | **55–75 s** |
| 594×1056 / 28–32 spp | **96–133 s** |
| 1080×1920 / 48 spp (extrapolated) | **~8–11 min** |

**2 CPU cores.** Iska matlab:

> **Poori 48-second film 3D me = 1440 frames × ~9 min = 200+ ghante. Namumkin.**

Toh production rule badalna padega — aur yeh aapka faisla hai:

**Option A — 3D sirf hero shots par.** 6 shots × 1.6 s = 288 frames ≈ **6–9 ghante**.
Baaki film 2.5D plate stage par (jo abhi 48 s me 12 min leta hai).
Yeh spec ke "55% frames Cycles par" wale plan ko bhi todta hai — reality 2 cores hai.

**Option B — 3D sirf P0 stills par** (6 frames ≈ 1 ghanta), aur film 2.5D + in stills ko
texture/plate ki tarah use karke bane.

**Option C — render kisi GPU box par** (aapke paas ho to) — tab poora 3D film possible hai.

## 3. Scene kyun abhi kharab lag raha hai — 4 defects, exact

1. **Framing galat.** 72 mm @ 1.05 m — sirf torso aata hai. 50 mm @ 2.4 m chahiye.
2. **Exposure jal raha hai.** Plate emission 0.62 + key 150 → chehra pink blob ban jaata hai.
   Plate ko 0.35 par lana hai aur key ko 60 tak.
3. **Rib placement.** Ribcage plate ke *aage* aa jaata hai (y ordering), aur scale 0.62 par bhi
   bada hai. Chest ellipse ke andar clip karna hai.
4. **Background.** Boxes se banaya hua kamra sasta lagta hai. Behtar: **photographic plate**
   ko depth planes par rakhna (Layer B), aur 3D sirf character + rig + light ke liye.

`p0_wip/WIP_hero_pass3.png` me yeh defects apni aankh se dekh lo — main ise "final" nahi keh raha.

## 4. Aage ka kaam (jab aap bolo)

1. Framing + exposure fix (1 render, ~2 min)
2. Rib clip + ordering fix (1 render)
3. Photographic background plates (p01/p03) depth planes par — room boxes hata kar
4. Tab 6 P0 stills, 1080×1920, 48 spp → **aapka HAAN**
5. Phir P1 hero 5 s (150 frames ≈ 20–25 min at 540×960) → **aapka HAAN**

## 5. Jo main galat kar raha tha, aur ab nahi karunga

Pichle teen turn me maine aapko mukammal cheez dikha kar "next level" kaha — jabki woh
stills par 2D effects the. **Ab jab tak scene aapko theek na lage, main full render nahi karunga.**
