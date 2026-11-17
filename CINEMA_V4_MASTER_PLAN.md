# MONARCH® CINEMA V4 — "DIGITAL HUMAN" PRODUCTION PLAN
### EP5 `Main Abhi Bhi Apni Taraf Hoon` — next-level rebuild, structure + shot bible + audio map

**Date:** 14 Nov 2026 · **Branch:** `arena/2a8ad29e-top1` · **Current delivered build:** `696180a` (V3, three.js WebGL, low-poly `suit.glb`)
**Verdict:** V3 ko aage nahi barhana. Uska *engine* hi problem hai. Neeche naya engine, naya structure, aur exact beat-by-beat shot bible hai.

---

## 0. EK LINE MEIN SACH

> V3 me **renderer** galat nahi tha — **asset** galat tha. `suit.glb` ek **CC0 low-poly cartoon mannequin** hai (5 mesh nodes, flat materials, koi skin pore nahi, koi hair strand nahi, koi cloth simulation nahi). Usse tum world-class lighting bhi de do, woh **plastic toy** hi lagega. Isliye face/hair realistic nahi lag raha — kyunki wahan realistic *cheez* hi maujood nahi thi.

---

## 1. FORENSIC — V3 KYUN "MAZA NAHI AA RAHA" (5 root causes)

| # | Symptom jo tumne bola | Asli root cause (code se proven) | Fix direction |
|---|---|---|---|
| **1** | *"character reference se match nahi ho raha, hair/face realistic nahi"* | Asset hi `suit.glb` hai — Papyszoo CC0 **PS1-era low-poly**: `Suit_Head/Cube006`, flat `Skin` material, hair ek painted blob, `Pistol`/`Suit_Head` primitives abhi strip kiye. 5 mesh nodes total. Koi PBR skin, koi SSS, koi strand hair, koi facial rig — **zero**. | Character ko **asset** se replace karna padega: photoreal digital human (skin SSS + groomed hair + real eyes), reference-locked. Section 4. |
| **2** | *"environment/buildings mazedar nahi"* | 12 beats ke liye ~9 primitive props: `BoxGeometry` pillars, `PlaneGeometry` panels, ek flat gradient sky. `RoomEnvironment` PMREM = generic grey studio IBL. Koi scanned texture, koi HDRI, koi volumetrics nahi. Har shot same do teen boxes. | **True 3D set-build** + Poly Haven CC0 scanned PBR + HDRI + volumetric atmos. Section 5. |
| **3** | *"animations, movement, physics nahi"* | Animations sirf 3 GLB clips (`Walk`/`Idle`/`Interact`) loop + `Math.sin` bob. Koi ragdoll, koi cloth, koi rigid body, koi contact shadow, koi secondary motion (cap lag, breathing, blink). Camera = `Vector3.lerp` straight lines → "drone" feel, momentum zero. | **Real solver physics + physical camera**. Section 6. |
| **4** | *"VFX / lightning / cinema level nahi"* | `ACESFilmicToneMapping` + 3 point lights. Koi DOF, koi motion blur, koi bloom/halation, koi grain, koi CA, koi flare, koi god ray. 30 fps par shutter angle nahi. | **Full Cycles path-traced comp stack**. Section 7. |
| **5** | *"repo se SFX uthake lagana"* | `build_audio.py` line 23 `EARSHOT_DIR = assets/earshot_takes` **manga raha hai — woh folder repo me maujood hi nahi** (`ls: No such file`). Isliye sirf 4 procedural numpy sounds (`sub_boom`, `whoosh`, `glass_shatter`, `heartbeat`) chal rahe the, fallback me har jagah same `sub_boom`. | **Asli SFX library repo me build + commit** karni hai, phir frame-locked cue sheet. Section 8. |

**Matlab:** jo kami tum dekh rahe ho, woh taste ka masla nahi — **production pipeline ka masla** hai. Aaj se hum isko **drop** kar rahe hain.

---

## 2. KYA PHENK RAHE HAIN (drop list — irrevocable)

```
DROP  three.js / WebGL scene.html renderer        (path-traced GI nahi de sakta)
DROP  suit.glb aur uske saare primitives          (low-poly, reference se match impossible)
DROP  RoomEnvironment PMREM generic IBL           (flat studio look ki jad)
DROP  Walk / Idle / Interact clip loops           (loop = mechanical, "mazedar nahi")
DROP  Vector3.lerp camera moves                   (momentum/ease/physics feel zero)
DROP  ACESFilmic + 3-point-light lighting         (no GI, no bounce, no atmosphere)
DROP  procedural-numpy-only SFX fallback          (4 sounds, repeated = fatigue)
KEEP  voice-06 Urdu VO (10 beats, 41.461s)        (script + delivery approved — dubara nahi banana)
KEEP  timeline_synced.json word-lock mechanism    (yeh V3 ki asli jeet thi — ±1 frame sync)
KEEP  -14 LUFS / -1 dBTP master gate              (broadcast-safe)
```

---

## 3. NAYA ENGINE — 6 LAYERS (Ek hi pipeline, koi shortcut nahi)

```
LAYER 6  SOUND    48 kHz/24-bit SFX bank + word-locked cue sheet + stems + LUFS master
LAYER 5  COMP     bloom · halation · film grain · CA · vignette · lens dirt · god rays · dust
LAYER 4  CAMERA   physical lens/f-stop/shutter-angle · DOF · motion blur · handheld impulse
LAYER 3  PHYSICS  rigid body · cloth · paper · dust · contact shadows · secondary motion
LAYER 2  WORLD    true 3D sets · scanned PBR · HDRI · volumetrics · practical lights
LAYER 1  HUMAN    photoreal digital human — skin SSS · groomed hair · real eyes · facial rig
         ENGINE   Blender 4.x · Cycles path tracing (CPU) + OIDN denoise · AgX view transform
```

**Kyun Cycles (aur yeh honest baat hai):** photoreal skin ko **subsurface scattering**, hair ko **strand curves**, aur light ko **bounce/GI** chahiye. WebGL in teeno ko sach me nahi kar sakta — isliye V3 plastic lag raha tha. Cycles CPU par GitHub Actions ke 4-core runner pe **~14-18 s/frame**, aur hum 8 parallel chunk jobs chalate hain → **1244 frames ≈ 45–60 min wall clock**, native 1080×1920 @ 30 fps. Budget ke andar hai.

---

## 4. LAYER 1 — CHARACTER (tumhari #1 shikayat, isliye #1 priority)

### 4.1 Sach: "reference se match" ka matlab
Koi bhi free rigged GLB tumhare reference insaan se **chehra match nahi karega** — woh generic hoga. Reference-locked face ke sirf 3 raste hain, aur hum **hybrid** lenge:

| Tier | Technique | Face realism | Body motion | Verdict |
|---|---|---|---|---|
| **A** | **Photoreal digital-human plate** — reference se matched photoreal renders (4 views + expressions) → monocular depth (Depth-Anything-V2, runner pe) → multi-layer relief mesh + derived normal/AO → Cycles me **relight** hota hai (true 3D shadows, world light se react) | **10/10 — literally photographic** | ±20° yaw orbit | **CLOSE-UP shots** ✅ |
| **B** | **True 3D body** — CC0 anatomically-correct base mesh (MakeHuman base, ~19.6k verts) + CC0 PBR skin + cloth sim | 6/10 (face is small in frame) | Full walk/climb/reach | **WIDE + action shots** ✅ |
| **C** | Low-poly GLB (jo V3 me tha) | 1/10 | Loop clips | ❌ **BANNED** |

**Rule:** jab face frame ka **>15%** ho → Tier A. Jab body action ho ya face chhota ho → Tier B. Dono ek hi scene, ek hi light-rig, ek hi lens se shoot honge — isliye cut par koi style jump nahi hoga (yeh V3 ka sabse bada galti thi: realistic bear → cartoon bear).

### 4.2 Character spec (locked)
- **Skin:** real PBR albedo (pore/blemish level) + **SSS** (`Subsurface Weight 0.35`, radius R3 G2 B1.2 mm) + specular breakup + peach-fuzz rim.
- **Hair:** strand-based groom (cap ke neeche sides + beard), `Principled Hair BSDF`, roughness 0.28, **beard 3 density zones** (moustache/chin/jaw), flyaway strands on key light.
- **Eyes:** real cornea refraction + iris parallax + wet-line + micro-saccade (2° drift, 1.5–4 Hz), blink every 3.4–5.2 s **randomised** (koi metronome nahi).
- **Face micro-motion:** brow micro-tension on stress words, jaw set on the "Band." line, breath-driven nostril flare, neck/cap **lag** (cap 2 frames behind head = real momentum).
- **Body:** cloth-simulated jacket (shoulder fold on reach), heel-strike weight shift, contact shadows.
- **Wardrobe:** matte black (roughness 0.62, no plastic sheen) + cap fabric weave + tiny lint for realism.

### 4.3 Reference lock (tumse chahiye)
Face/hair match tabhi hoga jab reference saaf ho. Mujhe chahiye:
1. **Front** face — sharp, even light (phone selfie bhi chalega, bas blur na ho)
2. **3/4 ya side** — hairline, beard shape, jaw, ear
3. Optional: full body (kapde ka fit)

Ye mile to main pehle **character bible sheet** (4 angles, consistent, photoreal) render karke dikhaunga — approval ke baad hi shots.

---

## 5. LAYER 2 — WORLD (environment "mazedar" banane ka plan)

**Har beat ka apna set. Koi set do beats me repeat nahi. Koi `BoxGeometry` nahi.**

| Beat | Set (true 3D) | Signature material (scanned PBR) | Light design |
|---|---|---|---|
| 1 Hook | Shattered glass gallery, floating shard field | frosted glass, brushed steel | cold key + hot shard glints |
| 2 Khwaab | Infinite void of dying memory-orbs | wax/subsurface orbs, volumetric haze | bokeh ocean, orbs as the only light |
| 3 Excuses | Colossal engraved monolith corridor | rough limestone, dust, iron inlays | single hard shaft through slot, dust motes |
| 4 Sukoon | Luxury trap lounge — velvet, marble, rain window | velvet sheen, polished marble, rain streaks | warm practicals → cold sweep on reveal |
| 5 X-Ray | Hero interior / anatomy chamber | volumetric emission, artery geometry | bioluminescent heart as key light |
| 6 Micro | Macro desk — one page, one pen | real paper fibre, ink bleed shader | single lamp shaft + dust |
| 7 10 Minutes | Warm study desk, notebook, flipped phone | leather, glass screen, clock brass | lamp pool, shallow DOF |
| 8 Stairs | Monumental staircase, cathedral scale | marble steps, brass rails, haze | hard god rays, 8 shafts |
| 9 Portrait | Monumental dark hall, single spotlight | black stone, bronze | single hard key, deep falloff |
| 10 Loop | Rooftop void, orbs reigniting | wet asphalt, mist | backlit rim, near-silhouette |

**Her set me mandatory:** HDRI environment (captured, CC0) + **1 hero practical light** + **volumetric medium** (mist/dust) + **3-layer depth** (foreground element / subject / deep background) — yahi "khaali" feel ko khatam karta hai.

---

## 6. LAYER 3 + 4 — PHYSICS & CAMERA BIBLE

### 6.1 Physics (real solvers, koi `sin()` fake nahi)
- **Rigid body:** 40–120 shards (bullet/rigid solver), real mass/friction/restitution, floor contact.
- **Cloth:** jacket + curtain + banner; wind field driven by the same beat.
- **Soft/paper:** notebook page flutter (paper sim), ink bleed (shader).
- **Particles:** dust motes volumetric (2–4 µm look), smoke plume, rain streaks on glass.
- **Contact:** footstep dust puffs + contact shadows on every step; pen contact flex.
- **Secondary motion:** cap lag, coat hem drag, head/neck overlap, breath (chest 0.25 Hz).

### 6.2 Camera (physical, not "lerp")
- **Sensor:** 36 mm full-frame equiv · **aspect 9:16** (1080×1920) · **shutter 180°** (0.5 frame motion blur) — motion blur hi movement ko "cinema" banata hai.
- **Lens table:** 24 mm (monumental) · 35 mm (walk) · 50 mm (default dialogue) · 85 mm (portrait CU) · 100 mm macro (pen/ink/skin) · 135 mm (compressed portrait).
- **Aperture:** portrait f/1.4–f/2 · walk f/2.8 · set reveal f/4–f/5.6 (real DOF, real bokeh).
- **Move library:** rail dolly, jib crane, orbit arc, whip-pan (2-frame blur), rack focus (0.4 s), dutch 6°, macro slider, overhead descend.
- **Inertia:** har move par ease `cubic-bezier(0.16, 1, 0.3, 1)` equivalent — **accel → settle**, koi constant velocity nahi.
- **Handheld:** Perlin drift 0.6–1.4 mm + **impulse shake** on impacts (decay 240 ms, 2 axes, phase-offset).
- **Cut rhythm:** **avg 1.6 s per shot, max 2.2 s, min 0.6 s** (26 shots / 41.46 s). V3 me 8.9 s ka ek hi shot tha — wahi boredom ka ilzaam hai.

---

## 7. LAYER 5 — COMP STACK (Hollywood veneer)

| Pass | Setting | Kaam |
|---|---|---|
| View transform | **AgX** | plastic highlights khatam, filmic rolloff |
| Denoise | OIDN + albedo/normal guide | clean 1080p at 64 spp |
| Bloom | threshold 0.86, radius 18 px, 0.35 | practical glows |
| Halation | red-orange, 0.12 | film emulsion feel |
| Chromatic aberration | radial, 0.35 px edge | lens truth |
| Vignette | 28% | eye guidance |
| Grain | 35 mm, 0.045, **animated per frame** | digital "deadness" remove |
| Flare | anamorphic streak on hero lights only | premium cue |
| Grade | teal-shadow / amber-highlight, split-tone | MONARCH look |
| Text | kinetic Roman-Urdu captions, safe-area 12% bottom | legibility 100% |

---

## 8. LAYER 6 — SOUND (tumhari explicit demand: repo SFX + perfect sync)

### 8.1 Pehle repo me asli SFX bank banao
`build_audio.py` **already** `panama_plus_3d_kit/assets/earshot_takes/` dhundh raha hai — folder hi nahi hai. Hum use **bana kar commit** karenge:

```
assets/earshot_takes/
  sub_drop.wav            braam_hit.wav         riser_2s.wav
  whoosh_3band.wav        glass_shatter_l1..l3.wav
  impact_concrete.wav     stone_slam.wav        cloth_swish.wav
  footstep_stone.wav      footstep_marble.wav    page_turn.wav
  pen_scribble.wav        phone_flip_clack.wav   clock_tick.wav
  heartbeat_ignite.wav    heart_pulse.wav        breath_in.wav
  rain_window.wav         room_tone_hall.wav     crowd_murmur.wav
  ink_bleed.wav           orb_chime.wav          light_ignite.wav
```
- 48 kHz / 24-bit, peak-normalized, loop-safe tails, semantic names.
- Kuch DSP se synthesize, kuch repo ke existing DSP code se derive (same tonal DNA), sab **committed** taake har episode reuse kare.
- `sfx_map.json`: har cue ka `{beat, frame, sound, gain_db, pan, layer}`.

### 8.2 Sync method (V3 ka proven hissa, upgrade karke)
- VO se **phrase-onset detection** (15 ms RMS) → `timeline_synced.json` word-lock.
- Har SFX cue ek **anchor** se bandha: ya frame-exact word, ya **2-frame pre-roll** (impact ko word se 2 frame pehle — human perception me "tight" lagta hai).
- **QC gate:** koi bhi cue ±1 frame se zyada door = build fail.
- **Layering:** har action me 3 elements — `transient (impact) + body (whoosh/cloth) + tail (room/reverb)` — isi se "expensive" sound banta hai.
- **Ducking:** VO -0 dB, bed -9 dB sidechained, SFX -6 dB under speech.
- **Master:** -14.0 LUFS integrated, -1.0 dBTP, true-peak limiter, **stems** (VO / SFX / Music / Atmos) bhi deliver.

---

## 9. EP5 — NAYA SHOT BIBLE (10 beats · 26 shots · 41.46 s)

> VO unchanged (`voice-06`, 41.461 s). Sirf visual + sound + camera naya. Har shot ka number frame-range ke saath.

### BEAT 1 — `hook_shatter` · f0–87 (0.00–2.91 s)
| Shot | Frames | Lens / move | Action & VFX | Sound |
|---|---|---|---|---|
| 1.1 | 0–24 | 100 mm macro, rack focus shard→eye | slow-mo glass shard field, refracted hero eye in shard | `glass_shatter_l1+l2` + `sub_drop` @f0 |
| 1.2 | 24–56 | 24 mm whip-pan → wide | void opens, hero silhouette on floating shard platform, 6 god rays | `whoosh_3band` + `braam_hit` |
| 1.3 | 56–87 | 35 mm dolly-in | eyes catch light, dust motes, cap micro-lag | `breath_in`, bed enters |

### BEAT 2 — `khwaab_fade` · f87–259 (2.91–8.63 s) — *"Baikis us din hoti hai…"*
| Shot | Frames | Lens / move | Action & VFX | Sound |
|---|---|---|---|---|
| 2.1 | 87–140 | 50 mm crane-down through orbs | thousands of memory-orbs, volumetric bokeh | `orb_chime` ×3 random + `rain_window` bed |
| 2.2 | 140–190 | 24 mm low-angle | giant shadow sweeps orbs away, paper-flutter physics | `whoosh_3band` ×2, `cloth_swish` |
| 2.3 | 190–232 | 85 mm CU | orb dims in hero's palm, SSS wax glow dying | `light_ignite` reverse + `heart_pulse` faint |
| 2.4 | 232–259 | 35 mm pull-back | silhouette physically shrinks as orbs die = *"chhota"* | `sub_drop` soft |

### BEAT 3 — `excuse_monoliths` · f259–442 (8.63–14.72 s) — *"Phir: mere bas ka nahi…"*
| Shot | Frames | Lens / move | Action & VFX | Sound |
|---|---|---|---|---|
| 3.1 | 259–305 | 24 mm dutch 6°, slow rise | monolith corridor, engraved excuses, dust in hard shaft | `room_tone_hall`, `footstep_stone` |
| 3.2 | 305–360 | 35 mm tracking | hero walks between slabs, cloth + dust puffs | `footstep_stone` ×3 (contact-locked) |
| 3.3 | 360–410 | 24 mm static, then impulse | monolith **slams** into frame, shockwave, camera kick 240 ms | `stone_slam` + `impact_concrete` + `sub_drop` |
| 3.4 | 410–442 | 85 mm CU, hard sliver key | face in one light sliver — *"band."* | silence punch (bed cut 6 f), `breath_in` |

### BEAT 4 — `sukoon_trap` · f442–592 (14.72–19.73 s) — *"hai tum theek ho?…"*
| Shot | Frames | Lens / move | Action & VFX | Sound |
|---|---|---|---|---|
| 4.1 | 442–492 | 35 mm slow push | velvet lounge, marble, rain-streaked window, warm practicals | `rain_window`, `crowd_murmur` faint |
| 4.2 | 492–540 | 50 mm | hero sinks into sofa (cushion compression sim) | `cloth_swish` |
| 4.3 | 540–592 | 85 mm CU hand→chest | breath, then **cold light sweep** = trap reveal | `heart_pulse`, cold `braam_hit` tail |

### BEAT 5 — `xray_ignition` · f592–733 (19.73–24.43 s) — *"karke uska naam sukoon mat"*
| Shot | Frames | Lens / move | Action & VFX | Sound |
|---|---|---|---|---|
| 5.1 | 592–645 | 85 mm orbit ±18° | x-ray dissolve: ribs + heart become translucent, filament ignites | `light_ignite` + `riser_2s` |
| 5.2 | 645–700 | 100 mm macro | heart pulse, arteries glow, bloom + halation | `heartbeat_ignite`, `heart_pulse` ×2 |
| 5.3 | 700–733 | 50 mm | fake-sukoon smoke burns out inside the chest cavity | `whoosh_3band` reverse + `sub_drop` |

### BEAT 6 — `micro_promise` · f733–852 (24.43–28.39 s) — *"Aaj poori zindagi nahi badalni,"*
| Shot | Frames | Lens / move | Action & VFX | Sound |
|---|---|---|---|---|
| 6.1 | 733–775 | 100 mm macro tilt-shift | single page + pen + dust in one lamp shaft | `room_tone_hall` tight, `clock_tick` |
| 6.2 | 775–820 | 100 mm macro slider | hand writes one line, ink bleeds into fibre (shader) | `pen_scribble` (word-locked) |
| 6.3 | 820–852 | 24 mm fast pull-back | tiny desk revealed inside the void — scale gag | `whoosh_3band` |

### BEAT 7 — `desk_ten_min` · f852–989 (28.39–32.98 s) — *"nibhana hai. Kholo, sirf das minute usay do."*
| Shot | Frames | Lens / move | Action & VFX | Sound |
|---|---|---|---|---|
| 7.1 | 852–895 | 85 mm slow-mo | journal page flutter open (paper sim) | `page_turn` |
| 7.2 | 895–935 | 100 mm macro | **"10:00" ink** pristine (V3 bug fixed & re-proven) | `pen_scribble` short + `ink_bleed` |
| 7.3 | 935–965 | 50 mm top-down | phone flipped face-down, screen glow dies | `phone_flip_clack` |
| 7.4 | 965–989 | 100 mm macro | clock hand ticks; 10-min time-lapse via light sweep | `clock_tick` ×4 accel |

### BEAT 8 — `stairs_ascent` · f989–1116 (32.98–37.19 s) — *"ko yaad dilane ke liye:"*
| Shot | Frames | Lens / move | Action & VFX | Sound |
|---|---|---|---|---|
| 8.1 | 989–1035 | 24 mm low-angle crane-up | monumental staircase, 8 god rays, heavy haze | `room_tone_hall` wide, `riser_2s` |
| 8.2 | 1035–1085 | 35 mm tracking from below | hero climbs, real heel-strike weight, cloth drag | `footstep_marble` ×4 |
| 8.3 | 1085–1116 | 50 mm rise with subject | camera ascends with him, haze letters form | `braam_hit` soft + choir pad |

### BEAT 9 — `monarch_portrait` · f1116–1169 (37.19–38.96 s) — *"Main abhi bhi apni taraf"*
| Shot | Frames | Lens / move | Action & VFX | Sound |
|---|---|---|---|---|
| 9.1 | 1116–1169 | 135 mm, f/1.4 push-in | monumental portrait, single hard key, sculpted falloff, **skin pores + beard strands visible** | music drops to piano alone; `breath_in` |

### BEAT 10 — `loop_question` · f1169–1244 (38.96–41.46 s) — *"waala waada kya hai?"*
| Shot | Frames | Lens / move | Action & VFX | Sound |
|---|---|---|---|---|
| 10.1 | 1169–1210 | 35 mm back-to-camera | hero walks into light, orbs reignite behind him | `orb_chime` rising |
| 10.2 | 1210–1244 | 24 mm → black | single orb pulse, title lockup, **loop seed** to shot 1.1 | `sub_drop` tail, room to silence |

---

## 10. PRODUCTION RUN — PHASES & GATES

| Phase | Kya banega | Gate |
|---|---|---|
| **P0 · Look-dev** | 6 photoreal look-dev stills (character CU, x-ray, stairs, desk macro, monolith, portrait) + character bible 4-view | **Tumhara HAAN** |
| **P1 · Hero test** | **5.0 s** clip, 1080×1920 @30 fps, full pipeline (Cycles + comp + SFX) — Beat 1 poora | **HAAN** (yahan hi style lock hoga) |
| **P2 · Asset & SFX bank** | character rig, 10 sets, HDRI/PBR pack, 23-file SFX bank, `sfx_map.json` | auto QC: file/format/dup check |
| **P3 · Full render** | 1244 frames, 8 parallel chunk jobs | auto preflight: lum/DOF/strip/asset-audit |
| **P4 · Comp + mix** | grade, grain, captions, mix, master, stems | -14 LUFS / -1 dBTP / ±1-frame cue sync |
| **P5 · Deliver** | MP4 + contact sheet + stems + cue sheet → Drive (public) + repo | 12-point QC green |

**Rule:** P0 aur P1 ke bagair **koi full render nahi**. Tumhara waqt aur mera compute dono bachega.

---

## 11. 12-POINT AUTO QC (har build pe)

1. 1080×1920, 30.000 fps, duration ±0.02 s
2. Koi blank/near-black frame nahi (perceptual luminance floor)
3. Har shot ≥0.6 s aur ≤2.2 s (cut-rhythm audit)
4. Koi low-poly/inherited primitive mesh render me nahi (asset provenance allowlist)
5. Face shots me measurable skin-detail energy (laplacian variance floor) = "plastic detector"
6. DOF + motion blur active (frame-diff blur metric)
7. Har SFX cue ±1 frame of anchor
8. Output -14.0 LUFS ±0.5, -1.0 dBTP max
9. Caption safe-area + contrast ratio ≥4.5:1
10. Koi repeated frame-pair (loop arrest) >0.4 s nahi
11. Grain active, banding-free gradient test
12. Colour: no channel clipping >0.5% of pixels

---

## 12. TUMSE 2 CHEEZEIN CHAHIYE (isi turn ke baad)

1. **Reference images** — front + 3/4 (ya side), sharp. Face/hair match iske bagair "accurate" nahi ho sakta.
2. **P0 look-dev stills par HAAN** (main pehle wohi banaunga — 6 stills, koi video nahi). Uske baad P1 ka 5-second hero test.

> Baaki decisions main khud le raha hoon: engine (Cycles), character hybrid (Tier A face + Tier B body), shot count (26), cut rhythm (1.6 s avg), sound design (23-file bank), colour (AgX + teal/amber). In par tumhein sirf final look par veto karna hai.
