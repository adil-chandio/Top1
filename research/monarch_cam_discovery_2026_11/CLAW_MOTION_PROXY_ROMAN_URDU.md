# Claw mechanism — original articulated motion asset

## Actual naya deliverable

`assets/claw-mechanism-proxy.gltf` ek self-contained glTF2.0 asset hai. Is mein real parent-child hinge animation hai; photograph par pan/zoom nahi. Fixed proxy palm/finger alag hain aur moving dactyl apne hinge ke around rotate karta hai. Jet, cavity aur pressure-event markers ke separate scale-animation channels hain.

**Yeh geometry jaan boojh kar simple mechanical proxy hai. Species-accurate claw, realistic final shot, head/hood model ya approved production animation nahi.** Isay final video ke badlay deliver nahi kiya ja raha. Yeh pehle mechanical timing aur rig behavior ka bounded test hai.

## Implemented timing

| Event | Illustrative test seconds |
|---|---:|
| Closure shuru | 0.60 |
| Closure complete / jet marker shuru | 1.00 |
| Cavity marker shuru | 1.12 |
| Cavity khatam / pressure marker shuru | 1.70 |
| Pressure marker khatam | 2.20 |
| Test duration | 3.00 |

**Yeh slowed explanatory timing hai, measured animal biomechanics nahi.** Jet, cavity aur closure ke physical events asal mein bohat tez aur coupled hote hain. In timings se biological speed ya delay quote nahi karna. Main authored sound attack baad mein collapse event se align ho sakta hai; abhi koi audio synthesize ya listen nahi hua. Markers literal underwater visible spheres/solid water arrows ka scientific claim nahi.

## Rebuild aur verification

```sh
python3 research/monarch_cam_discovery_2026_11/build_claw_motion_proxy.py
python3 -m unittest discover -s research/monarch_cam_discovery_2026_11 -p 'test_claw_motion_proxy.py' -v
```

- Standard-library Python generator; koi external mesh/figure trace nahi.
- Five tests: ordered events, actual hinge angle change, cavity-before-pressure relation, finite positive scales, binary buffers/hierarchy/animation serialization.
- Khronos glTF validator se separate structure check kiya. Exact results `CLAW_MOTION_PROXY_RECEIPT.json` mein hain.
- Structural tests anatomical validation, actual realtime playback, visual-art approval ya independent review nahi.

## Model search ki consequential finding

3dsam79 ka original Sketchfab Pistol Shrimp model identify hua, lekin description family-level Alpheidae hai, specific A.heterochaelis aur vetted rig establish nahi hue. [1](https://sketchfab.com/3d-models/pistol-shrimp-779f39e9837142758023fa4239ae3bde)

Usi creator ka commercial listing bhi mila. Is wajah se mirror ka 'free download' label permission ka reliable substitute nahi maana; koi model download/purchase nahi kiya. [4](https://free3d.com/3d-model/pistol-shrimp-2733.html)

GitHub repository searches `shrimp blender` aur `shrimp 3d` ne is run mein zero results diye; yeh internet par model na hone ka proof nahi. Unverified mirror download ki bajaye original minimal proxy likha.

## Production se pehle baqi

- Species-specific snapping-claw interior/plunger geometry independently verify karni hai; current proxy mein calibrated plunger/socket nahi.
- Correct head/hood mesh aur animal articulated rig unresolved.
- Actual realtime playback/visual inspection is batch mein nahi hui.
- No final video render, soundtrack/listening, user acceptance ya Drive upload claimed.
