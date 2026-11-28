# 03 — Bruce Block's *The Visual Story* & Physical Color-Script Engineering

## 1. The Master Principle: Visual Contrast = Dramatic Intensity
From Bruce Block (*The Visual Story*, 3rd ed.):
- **Greater Visual Contrast -> Higher Dramatic Tension & Energy.**
- **Greater Visual Affinity (Similarity) -> Calm, Restraint, or Resolution.**

If Act 1 already uses maximum color saturation, maximum shadow contrast, Dutch angles, fast camera movement, and glowing particles, **the climax has nowhere left to climb** — the film feels flat despite high spectacle!

### Synchronizing the Story Graph & Visual Graph (`bruce_block_visual_arc`)
1. Plot every narrative beat's `intensity_0_to_100` in `dramaturgy.beats`.
2. Reserve **peak visual contrast (`>= 65/100`)** across at least 3 of Block's 7 components strictly for `climax_beat_id`.
3. Drop visual contrast into **visual affinity (`>= 55/100`)** during the final resolution beat so the viewer emotionally exhales (or snaps into the loop seam).

---

## 2. The 7 Visual Components & How We Control Them in 3D Cinema

| # | Component | High Affinity (Calm / Exposition / Resolution) | High Contrast (Conflict / Rupture / Climax) |
|---|---|---|---|
| **1** | **Space** | Flat plane (`50–85mm` parallel to wall/surface, orthographic feel) | Deep 3-plane longitudinal space (`18–28mm` close FG + MG + distant BG converging lines) |
| **2** | **Line** | Horizontal & gentle curved lines | Steep diagonals intersecting verticals (`30°–60°` shear / fracture trajectories) |
| **3** | **Shape** | Soft circles / organic rounded silhouettes | Hard triangles / jagged wedges colliding against smooth curves |
| **4** | **Tone (Luminance)** | Compressed tonal range (high-key `1.5:1` or muted mid-tone `2:1`) | Chiaroscuro (`8:1` to `16:1`) — bright specular highlight directly abutting `0.02` shadow |
| **5** | **Color** | Monochromatic / analogous temperature & low saturation | Complementary Kelvin clash (`2200K` molten tungsten vs `6800K` cold rain/shadow) + **Reserved Accent Hue** |
| **6** | **Movement** | Locked tripod (`static`) or slow horizontal glide parallel to frame | Z-axis motion toward/away from lens or perpendicular screen-diagonal rupture |
| **7** | **Rhythm** | Even, unhurried `3.2–4.5s` shot cadence | Accelerating staccato (`1.1–1.6s`) OR sudden held `3.5s` silence right before `0.8s` impact |

---

## 3. Color-Script Law & The Reserved Accent Hue
Every `production_design.color_script` obeys **3 non-negotiable rules**:
1. **`base_hex` (`2–4` muted environmental tones):** Covers `85–92%` of screen area (walls, soil, stone, foliage, metal body, sky, shadow).
2. **`reserved_accent_hex` (`1` focal color — `5–10%` of screen area):** Strictly forbidden from appearing in `base_hex` (`director_linter.py` enforced). It appears **ONLY** on the causal hero mechanism (e.g., crimson spore stalk, molten copper fuse, saffron tracer dye, ultraviolet arc).
3. **Act-by-Act Progression (`act1_palette_mood -> act2_palette_mood -> act3_palette_mood`):**
   - *Example (`W01_SUNLIT_DOMESTIC_MORNING`):*
     - Act 1: Warm sunlit cream ceramic & brushed aluminum (`5400K`, `2.5:1` airy morning calm).
     - Act 2: Rising steam clouds shadow the counter; internal cutaway shifts to pressurized steel-grey + creeping `#C83E2B` thermal load (`5:1` contrast).
     - Act 3: Clean upward steam release restores sunlit kitchen clarity (`2.5:1` affinity return).

---

## 4. Physical Lighting Motivation (`lighting_paradigm`)
Never place an unmotivated floating point light in Three.js. Every light must answer **"What physical object off-screen emits or bounces this photon?"**
- **Window / Skylight (`5200K–6500K`):** Soft directional key through architectural opening + warm floor/wood bounce fill (`kelvinToSrgb01()` + `parseContrastRatio()` in `director_optics_sdk.js`).
- **Overcast / Canopy Sky (`5800K–6500K`):** Broad top hemisphere wrap (`2:1`) + negative-fill dark soil/bark occlusion underneath so undersides keep 3D modeling.
- **High-Key Clinical Softbox (`5600K`):** Large overhead diffused bank + white cyclorama bounce (`1.5:1`) — crisp dark contact shadows under objects prevent "floating CG" look.
- **Practical / Incandescent / Fire / Molten (`1800K–3200K`):** Inverse-square falloff from visible source inside or just beside the frame (`8:1` to `12:1`), paired with cool `6500K` ambient night/sky rim only where skylight physically reaches.
