# 04 — Scene Geography, Blocking-Before-Camera, Cinema Optics & Camera Motivation

## 1. The Golden Order: Geography -> Blocking -> Distance -> Lens -> Move
Adapted from Roger Deakins, Joseph Mascelli (*The Five C's of Cinematography*), `cinematography-director`, and `SceneForge`:
1. **Map the Physical Set (`scene_geography`):** Define world dimensions (`bounds_xyz_m`), the primary light vector, the **Scale Reference Object** (`scale_reference_object` — human hand, ceramic mug, `10 cm` field scale bar, raindrop, ant leg), and the **`180°` Line of Action (`line_of_action_xz`)**.
2. **Block the Subject Action FIRST:** Place subjects and physical forces in world meters (`S2` metric space) and keep physical damage/state persistent across cuts (`cracked glass stays cracked`, `melted plug stays melted`).
3. **Set Camera Distance FIRST:** Distance alone governs perspective compression/expansion and emotional intimacy.
4. **Choose Focal Length (`lens_mm_equiv`) SECOND:** Focal length crops that perspective to the desired `shot_size` (`EWS`..`MACRO`).
5. **Move the Camera LAST (Only If Earned):** Default to a locked tripod (`static`, `HOLD_STILLNESS`). Add movement ONLY when static framing fails a specific narrative task.

---

## 2. Full-Frame Cinema Lens Psychology & Three.js `fovY` Reference Table
Computed via `director_optics_sdk.js` (`20.25×36.00mm` `9:16` vertical gate vs `36.00×20.25mm` `16:9` gate):

| Lens (`mm`) | Psychological / Spatial Character | `9:16` Three.js `fovY` | `16:9` Three.js `fovY` | Best Narrative Task |
|---|---|---|---|---|
| **`18mm`** | Vast monumental immersion, steep perspective | `90.0°` | `53.1°` | Caverns, cataclysms, towering architecture |
| **`24mm`** | Visceral proximity, energetic parallax | `73.7°` | `45.8°` | Tight interiors, dynamic action proximity |
| **`28mm`** | Grounded environmental context | `65.5°` | `39.7°` | Field sites, kitchen/workshop establishing |
| **`35mm`** | Human-eye journalism, honest presence | `54.4°` | `32.3°` | Documentary realism, witness POV |
| **`50mm`** | Neutral observational truth, zero distortion | `39.6°` | `22.9°` | Balanced mechanical & anatomical clarity |
| **`85mm`** | Intimate isolation, compressed planes | `23.9°` | `13.6°` | Emotional/forensic portrait, quiet tension |
| **`100mm`** | Surgical macro inspection | `20.4°` | `11.6°` | Valve seats, insect mandibles, micro-fractures |
| **`135mm`** | Claustrophobic compression, crushing scale | `15.2°` | `8.6°` | Impending threat looming right behind subject |

### Horizontal Clipping Prevention Formula (`9:16` Portrait Law)
In `9:16`, width is `9/16 = 0.5625x` of height! Always verify:
$$\text{visible\_width\_m} = 2 \cdot d \cdot \frac{10.125}{\text{lens\_mm}} \ge 1.18 \times \text{subject\_width\_m}$$
`director_linter.py` and `distanceForSubjectWidth()` enforce this automatically so no hero object ever clips against left/right phone edges.

---

## 3. Feeling-to-Move & Scene-Task-to-Move Decision Matrix
Synthesized from `AustinZ21/cinematic-skills` (`cheat-sheets.md`) & `jayaprakash-pixel/cinematography-director`:

| Dramatic Need / Audience Feeling | Right Camera Choice | Motivation Tag | Forbidden Mistake |
|---|---|---|---|
| **Dread, irreversible pressure building** | Slow creeping `push_in` (`easeInOutCubic`) | `APPROACH` | Fast orbit (breaks tension into spectacle) |
| **Sudden realization of tiny scale / aftermath** | Slow `pull_out` revealing vast surroundings | `WITHDRAW` | Zoom without parallax |
| **Hidden cause sitting right beside symptom** | `truck_lateral` or `pan` past foreground occluder | `REVEAL` | Unmotivated cut that loses spatial link |
| **Connecting Force A directly to Failure B** | Single `crane_arc` or `rack_focus_locked` | `RELATE` | Cutting rapidly without showing linkage |
| **Micro-world journey inside narrow cavity** | `probe_macro_glide` along physical channel | `SUBJECTIVE` | Clipping straight through solid walls without cutaway |
| **Shocking realization / world turning inside-out** | `dolly_zoom` (**MAX 1 per Short!**) | `EXPRESSIVE` | Using `dolly_zoom` twice (turns into gimmick) |
| **Reading a crucial number / quiet awe before climax** | `static` locked frame (`held_stillness_beat: true`) | `HOLD_STILLNESS` | Floating handheld sway while viewer reads |

---

## 4. Spatial Continuity & Restraint Budgets (Hard Linter Gates)
1. **`180°` Line of Action:** Every shot in `scene_id` stays on `allowed_camera_side` (`+1` or `-1` of `line_of_action_xz` cross-product) so left-to-right screen flow never flips accidentally.
2. **`30°` Jump-Cut Rule:** Consecutive shots of the same `subject_id` in the same `scene_id` MUST shift camera sightline by **`>= 30°`** OR change `shot_size` by **`>= 1` step** (`WS -> MS -> CU`).
3. **3-Layer Parallax Law (`FG / MG / BG`):** Every moving parallax shot MUST populate foreground, midground, and background depth elements (`layers_fg_mg_bg`). Moving a camera in an empty room creates zero parallax.
4. **Restraint Ceilings:**
   - Moving shots **`<= 70%`** (target `40–55%`) + **`>= 1` explicit stillness beat**.
   - Shallow DoF **`<= 45%`** (keep mechanisms and wide geography crisp in deep/moderate focus).
   - Zero vague buzzwords (`"cinematic"`, `"epic"`, `"dynamic"`, `"cool"`, `"stunning"`).
   - At least **3 key shots** record a concrete `rejected_alternative` explaining why a weaker framing was discarded.
