# 05 — Walter Murch Editing, 9-Zone Eye-Trace, Sequence Grammars & Pacing Curves

## 1. Walter Murch's *Rule of Six* (`murch_cut_driver`)
From Walter Murch (*In the Blink of an Eye*), every cut is evaluated in strict descending weight:
1. **`EMOTION_51` (`51%`):** Does the cut land at the exact micro-instant the audience's emotional state shifts? If yes, preserve it above all else.
2. **`STORY_23` (`23%`):** Does the new shot advance causal information (never repeating what the previous shot already proved)?
3. **`RHYTHM_10` (`10%`):** Does the cut duration sit musically on the breath, beat, or physical transient?
4. **`EYE_TRACE_7` (`7%`):** Where was the viewer's fovea at the end of Shot A (`eye_trace_end_xy`), and does Shot B catch the eye within `<= 0.36` normalized screen distance (`eye_trace_start_xy`)?
5. **`AXIS_2D_5` (`5%`):** Are screen vectors (`180°` line) preserved cleanly on the 2D plane?
6. **`SPACE_3D_4` (`4%`):** Does the audience still feel the 3D room/biome geography?

---

## 2. Eye-Trace Choreography Across `9:16` & `16:9` Cuts
In fast short-form (`1.5–3.2s` shots), if Shot A ends with the viewer staring at `(0.82, 0.80)` (bottom-right) and Shot B places the tiny hero valve at `(0.15, 0.18)` (top-left), the human eye wastes `250–400 ms` hunting across the screen — **killing comprehension**.
- **Rule:** Keep `hypot(curr.eye_trace_start_xy - prev.eye_trace_end_xy) <= 0.36` (`director_linter.py` enforced), OR use movement inside Shot A (`eye_trace_start_xy -> eye_trace_end_xy`) to **escort** the viewer's gaze into the zone where Shot B opens!
- **Exception:** Set `deliberate_eye_trace_shock: true` ONLY on a violent rupture/ambush where disorientation IS the point.

---

## 3. The 7 Non-Repetitive Sequence Grammars (`dominant_sequence_pattern`)
Rotate across these 7 editorial architectures so consecutive videos never share the same structural rhythm:

1. **`orient_escalate_payoff`:** Grounded world establishing -> hidden internal escalation -> held breath -> irreversible physical release -> transformed return.
2. **`thesis_counterexample_synthesis`:** Show intuitive everyday case (survives) -> show subtle variable flip (fails catastrophically) -> zoom into microscopic boundary explaining both.
3. **`micro_clue_macro_reveal`:** Start `MACRO` (`100–135mm`) on an alien-looking texture/symptom -> pull back step-by-step (`CU -> MS -> WS`) to reveal the surprising familiar host!
4. **`parallel_crosscut_convergence`:** Cross-cut two timelines or two scales (`modern Antarctic ice drill` <-> `90 Ma warm polar forest`; or `human hand approaching handle` <-> `fusible plug softening inside`) until both collide at the climax.
5. **`forensic_peel_layer_by_layer`:** Start at crime-scene aftermath -> peel outer shell -> peel fluid/thermal layer -> isolate root-cause atom/joint -> replay failure forward at real speed.
6. **`time_lapse_transformation`:** Anchor camera in one geographic axis while time accelerates across seasons/centuries/millennia around the specimen (`W04` / `W07` / `W15`).
7. **`single_breath_oner_with_inserts`:** Continuous spatial journey following energy/fluid along its physical path, punctuated by `2–3` razor-sharp static tactical inserts.

---

## 4. Motivated Cut-In Transitions (`cut_in_type`)
Never slap random dissolves or flashy wipes between shots. Choose the exact grammatical transition:
- **`HARD_CUT_ON_ACTION`:** Cut mid-motion (valve lifting, drop falling, hand turning) so momentum hides the seam.
- **`MATCH_CUT_GEOMETRY`:** Match circular whistle top (`Shot A`) to circular microscopic pore (`Shot B`) at identical screen `(x, y)`.
- **`J_CUT_AUDIO_LEAD`:** Start next world's sound (`hiss`, `rainforest cicada`, `ice crack`) `0.25–0.60s` *before* cutting the picture.
- **`L_CUT_AUDIO_TRAIL`:** Let reverberant impact decay bleed over the calm aftermath shot.
- **`OCCLUSION_WIPE_NATURAL`:** Foreground steam cloud, passing leaf, rock edge, or human arm naturally wipes the frame into the next scale.
- **`LIGHT_OR_FLASH_BRIDGE`:** Motivated arc flash, lightning strike, or specular glint bridges scales.
- **`LOOP_SEAM_MATCH`:** Final frame matches Frame 0 pose/eye-trace (`<= 0.12` delta) for infinite short-form replay.

---

## 5. Short (`9:16`) vs Long (`16:9`) Pacing Benchmarks
- **`9:16_short` (`28–52s`):**
  - Frame `0` (`0.00s`) MUST be poster-grade mid-tension (zero black fade-in, zero slow empty pan).
  - Visual/verbal paradox lands by **`<= 2.0–2.5s`**.
  - Average shot length **`2.2–3.6s`** (`9–16` shots across `32–45s`), with **`1` held stillness beat (`2.4–3.5s`)** right before or during the climax so speed has weight.
- **`16:9_long` (`8–18 min` IMAX Documentary):**
  - Cold open visual mystery lands within **`<= 15s`**.
  - Alternates high-density investigative sequences (`2.8–4.5s` ASL) with Villeneuve/Deakins breathing landscapes (`6.0–11.0s` ASL) at chapter turns (`H5_EDITORIAL_CHAPTER_CARDS`).
