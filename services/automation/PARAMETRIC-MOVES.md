# Parametric Moves — Layer ⑥ ka asli hal

## Problem

AI se arbitrary 3D scene generate karna abhi bhi reliable nahi hai. Har video ka scene haath se likhna = aapka current tarika = scale nahi karta.

## Solution

Aapki 5 films ke shots dekho — sirf **10 visual moves** repeat ho rahe hain. Inhe **parametric functions** banao.

Phir agent ko poora 3D scene nahi likhna padta. Agent **shot plan** likhta hai:
```
reveal(can) → cutaway(can, axis:z) → mechanism(rig, motion:flip) → compare(pressure) → replay(slow:0.63) → payoff()
```
Engine usko assemble karta hai. **Ye 100× zyada reliable hai.**

---

## 10 moves (aapki films se nikale)

| # | Move | Kya karta hai | Aapki film mein | Params |
| --- | --- | --- | --- | --- |
| 1 | `reveal` | Object slow orbit + rim light, background dark | Halo lamp hero shot | model, orbit°, keyLight, rimColor |
| 2 | `cutaway` | Front sector hata kar andar dikhao | Can axial cutaway | model, axis, angle |
| 3 | `mechanism` | Rig se actual motion (flip, hinge, buckle) | Can flip, lamp hinge | model, motion, duration, easing |
| 4 | `compare` | Do states side-by-side ya A→B | Pressure inside vs outside | stateA, stateB, labels |
| 5 | `quantity` | Bars/blocks/flow se number dikhao | Phone storage blocks | values, color, layout |
| 6 | `pushIn` | Detail par camera push, depth focus | Lid macro, prism array | target, from, to, fStop |
| 7 | `overlay` | Arrow / vector / tracer / ray | Pressure arrows, light ray | type, path, color, animated |
| 8 | `freezeLabel` | Freeze + ek label "this part" | Cutaway ID | atSecond, label, anchor |
| 9 | `slowReplay` | Wahi motion, slow clock | Can replay 0.63× | sourceShot, clockRate |
| 10 | `payoff` | Title + final held image | "Can ko hawa ne kuchla" | text, holdSec |

**Inhe banao, is order mein:**

```
Week 1-2:  reveal, pushIn, payoff          (3 sabse aasan, 60% shots cover)
Week 3:    overlay, freezeLabel, slowReplay
Week 4:    cutaway, mechanism              (model ke saath tight coupled)
Week 5:    compare, quantity
```

---

## Har move ka contract

```js
// services/automation/moves/reveal.js — ye spec hai, code nahi
export const reveal = {
  id: 'reveal',
  needs: ['model'],
  params: {
    model:     { type: 'ref', required: true },
    orbit:     { type: 'number', default: 25, min: 0, max: 180 },   // degrees
    keyLight:  { type: 'color', default: '#ffd9a0' },
    rimColor:  { type: 'color', default: '#7fd4ff' },
    duration:  { type: 'number', default: 3.0 },
  },
  // assemble(...) => { scene, camera, timeline }
  // Har move deterministic hona chahiye: same input = same frames
};
```

**Deterministic zaroori hai** — warna QA aur re-render bekaar.

---

## Model library — 5 se shuru

Ek niche pakro. Mechanism explainers ke liye:

| Model | Source | Reuse |
| --- | --- | --- |
| `can` | `tools/demo-render/air-crush.js` (already hai) | Pressure/heat topics |
| `reflector-cone` | `reflector-models.js` (already hai) | Optics topics |
| `lamp` | `scenes.js` halo (already hai) | Product/light topics |
| `phone` | `scenes.js` phone (already hai) | Tech topics |
| `generic-prism` | Naya, 1 din | Koi bhi "how X works" |

**Ye 5 models 20+ topics cover kar sakte hain.** Naya model = 1–2 din. Isliye niche narrow rakho.

---

## Honest limitation (client ko bhi bolo)

Har video **100% scratch se naya 3D** nahi hoga. Hoga:
- ✅ Naya script, naya edit, nayi composition, naya caption timing
- ✅ Models library se, moves library se
- ❌ Har video ka naya hero model

**Ye bilkul theek hai** — asli animation studios bhi aise kaam karte hain. Bas jhooth mat bolo. Client ko yahi bolo:

> "Har video ka script, edit aur shot arrangement naya hota hai. 3D models ki ek library hai jo har project ke saath badhti hai. Naya custom model chahiye to wo alag charge hai."

---

## Success test

```
Ek topic do: "pressure cooker kaise kaam karta hai"
→ system bina haath lagaye shot plan banaye
→ render kare
→ QA pass kare
→ Drive mein final MP4 daale
```
Jab ye chal jaye, **tab** Offer C becho. Pehle nahi.
