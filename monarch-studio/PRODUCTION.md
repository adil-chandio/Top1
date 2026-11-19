# Who Crushed the Can? — Cinema Edition

**Monarch Studio · Production file 001**

Original Top1 Lab film · 29 seconds · Urdu narration · Roman Urdu captions

## 1. Idea aur reference

Pehli frame par can already ulti hai; 0:00.25 par pichakti hai. Viewer pehle result dekhta hai, phir sawaal sunta hai: “Is can ko kisi ne dabaya nahi. Phir ye pichak kaise gaya?” Rewind ke baad har cut ek causal beat explain karta hai. Bhaap zyada tar andar ki hawa hata deti hai; doobi hui opening se bahar ki hawa jaldi wapas nahi aa pati; bhaap condense hoti hai aur andar ka pressure girta hai. Bahar ka pressure badhta nahi. Pressure difference shell ko andar ki taraf buckle karta hai. Paani raasta band karta hai, force hawa deti hai.

[Script aur blueprint](../public/samples/air-crush-blueprint.md) mein exact narration, timings, adaptable production prompt aur reference sources hain. Dailymotion listings topics aur runtimes ke liye dekhi gayi; embedded players nahi chale. Shot-level reference alag published breakdowns se aaya. Film ka set, sound, visuals aur narration us reference footage se copy nahi kiye. Physics [UW–Madison](https://wonders.physics.wisc.edu/collapsing-can/) se check ki. Ye explanation hai, home experiment ke instructions nahi.

## 2. Set, lens aur lighting

- **Three.js/WebGL:** Can ke sidewall ke liye dense ring mesh; rolled lid, stamped pull tab, actual open port, aur recessed base separate meshes. Cutaway mein shell ka front sector hata kar andar ka metal aur cut edges dikhaye. Hero prop, pedestal, bath aur rim ko pakarne wali rig procedural geometry se banaaye.
- **Canvas 2D texture maps:** Fictional FIZZ/TOP1 LAB label ko UV coordinates se shell par wrap kiya. Shell deform ho to print bhi saath fold hota hai. Roughness aur bump variation se brushed aluminium ki highlights stretch aur break hoti hain; copper uski finish ka rang hai.
- **Light:** Broad reflection cards ka filtered environment, warm key, cool rim aur controlled fill. Heater aur bath ki amber/steel-blue contrast scene ke andar hai. Camera world mein move karta hai; foreground lid aur distant rig ki parallax actual 3D movement se aati hai.
- **Optics:** Roughly 36–52 mm equivalent virtual lenses. Lid, submerged port aur replay mein depth-based focus. Flip aur snap ke 68 fast frames mein do within-shot sub-exposures; hard cuts ke across frames blend nahi kiye.

## 3. Rig, metal aur water

Rig 8.930–10.021 s mein eased rotation se can ko flip karti hai. Lift aur clearance geometry se test kiye gaye; lower karte waqt port **10.250 s** par bath ki surface cross karta hai. Splash, ripples aur water Foley isi cue se start hote hain. Water surface shader analytic displacement aur normals use karta hai. Droplets ballistic trajectories follow karti hain; surface ke neeche hawaa mein floating nahi rehti.

Crush uniform scale animation nahi hai. Angle aur height se har sidewall vertex ke folds calculate hote hain; lid stable hai, base shift/tilt karta hai, aur ring joins attached rehte hain. Main crease ke baad secondary fold aur damped shiver; dent wapas nahi khulta. Replay mein same motion slow clock par chalti hai (hook `1.62×`, replay `0.63×`). Tracers aur pressure arrows explanatory graphics hain. Outside arrows steady rehte hain; inside arrows shorten. Ye authored VFX hain, CFD, finite-element solve ya real pressure readings nahi.

## 4. Edit aur sound

| Cut | Shot |
| --- | --- |
| 0:00.00 | Cold open, first snap at 0:00.25 |
| 0:01.63 | Rewind to the intact can |
| 0:04.42 | Hot water cutaway |
| 0:06.50 | Lid macro; vapor and air exit the port |
| 0:08.88 | Lift, flip and dip; contact at 0:10.25 |
| 0:11.50 | Actual opening beneath the waterline |
| 0:13.58 | Condensation on the inside wall |
| 0:16.67 | Inside pressure drops; outside stays steady |
| 0:19.17 | Exterior air pushes inward |
| 0:22.96 | Slow replay; snap at 0:23.08 |
| 0:25.08 | Settling ripples and payoff |

Arena voice audition ki selected Urdu voice ko six takes mein generate kiya; silence trim, fades aur level treatment ke baad local [VO stem](../tools/demo-render/audio/air-crush-vo.m4a) save ki. Cinema Edition ne wohi performance reuse ki. [Foley code](../tools/air-crush-score.mjs) lab hum, rig, splash, metal transient aur secondary tick synthesize karta hai. Replay ke crack se pehle background bed peeche jaata hai aur voice rukti hai. Final encoded mix roughly −14.5 LUFS, −0.6 dBTP measured tha.

14 Roman Urdu phrase cues DM Sans mein draw kiye; staggered rise/fade aur ek word ka copper ya ice accent. Black boxes, permanent corner tags aur progress bar first cut se remove kiye. Capture ke waqt text directly frames par composite hua. Main snap 22.81–24.60 s ke caption gap mein aata hai.

## 5. Export aur verification

Node aur Vite isolated render bundle banate hain. Playwright headless Chromium ko har `frame / 24` timestamp par Three.js scene draw karne ko kehta hai. JPEG frame stream FFmpeg ko milti hai; x264 video aur AAC stereo mix final fast-start MP4 mein combine hote hain. Cinema Edition ka **final canvas 1080 × 1920** hai, captions bhi isi size par. Delivered export ki **3D plate 691 × 1229** se upscale hui; native 1080p 3D render is file mein use nahi hua.

Final: **29.00 s · 696 frames · 24 fps · H.264 High / BT.709 / yuv420p · AAC stereo 48 kHz · 14.4 MB**. Clean poster 26.66 s se nikla. Encoded frames dekhe, full video/audio decode ki, range seeking check ki. Desktop aur emulated Android par playback/chapters test hue; physical Android test ka claim nahi hai.

## 6. Rebuild from the repo

[`src/air-crush.js`](../src/air-crush.js) timings aur captions share karta hai; [`tools/demo-render/`](../tools/demo-render/) set, camera, motion, titles aur VFX rakhta hai. [`tools/render-demos.mjs`](../tools/render-demos.mjs) render aur encode run karta hai. Existing stem included hai, isliye rebuild par voice service call nahi hoti.

On a render machine with Node, Chromium, and FFmpeg:

```sh
npm ci
CHROMIUM=/path/to/chromium FFMPEG=/path/to/ffmpeg npm run render:demos -- air-crush
```

`TOP1_STILLS=1` review frames ke liye, `TOP1_RENDER_OUT` staging folder ke liye, aur `TOP1_FULL_QUALITY=1` optional native raster ke liye. Android par commands chalane ki zarurat nahi; website ready MP4 serve karti hai.
