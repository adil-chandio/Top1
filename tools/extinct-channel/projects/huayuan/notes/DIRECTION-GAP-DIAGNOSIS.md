# Huayuan — why it reads as a slideshow, measured

The user's own diagnosis is correct and it is the right one: **the animation is not the
problem, the direction is.** This file proves it with numbers taken from the shipped
`film_v2.js`, then names the rule that was missing and states what is still open.

Nothing here is a matter of taste. Every claim below is a count.

---

## 1. The film has no shape

29 shots, 60.0 s, ASL 2.07 s.

| Check | Target (DirectorSKILL `editing-and-assembly.md`) | Ours | |
|---|---|---|---|
| Longest shot | 2.0–3.0 × ASL | 3.33 s = **1.61 ×** | FAIL |
| Shortest shot | 0.25–0.5 × ASL | 1.27 s = **0.61 ×** | FAIL |
| Share of long shots | ~15 % | **6.9 %** | FAIL |
| Share near ASL | ~40 % | 48.3 % | pass |
| Share short | ~45 % | 44.8 % | pass |
| max/min shot length | 5 × or more | **2.63 ×** | FAIL |
| Median below mean | must be | 2.067 vs 2.069 | pass (barely) |

The median is below the mean by 2 ms. That is not shape, that is a rounding accident. The
film is an even spread from 1.27 s to 3.33 s with no anchor and no punctuation. This is
exactly what an editor means by "it has no rhythm."

**The two numbers that matter:** the longest hold is 1.6× the average instead of 2–3×, and
the shortest cut is 0.61× instead of 0.25–0.5×. The film never rests and never punches.

## 2. The moves are recycled, not chosen

29 shots but only **20 unique camera moves**. Nine moves appear twice:

`rake, craneUp, trackRadiodont, staticOpabinia, lowDolly, handheld, overhead, dutchRoll, vertigo`

Opabinia is the subject of **8 of 29 shots** and is shot from the same four setups
(`staticOpabinia`, `overhead`, `dutchRoll`, `vertigo`) every time — four of them run
back to back across 18.67–22.73 s, then three of the same four run again across 51.33–56.67 s.
The hallucigenia gets **2 shots in 60 seconds**. The second radiodont gets **1**.

A director would not spend 8 of 29 shots on the same animal from the same four angles while a
character with a 2 s walk cycle is on screen for four seconds total.

## 3. No lens language

Focal range across the whole film: **27°–43° fov**, an effective ~24–50 mm equivalent band.
Never wider than 24 mm, never longer than ~50 mm. There is no compression, no expansion, no
moment where the lens states anything. Every shot sits in the same middle register.

## 4. No shot-to-shot logic

Cuts land on a frame boundary and change camera position. Nothing else is specified:

- No cut is motivated (`cut on action`, `cut on look`, `cut-away`, `reaction`, `match cut`).
  The cut motivation taxonomy in `editing-and-assembly.md` names 10; we use none.
- No screen-direction continuity is tracked. Animals cross frame left/right with no
  established axis, so a 180° break cannot even be detected, let alone avoided.
- No size ladder. Sizes are expressible only as `fill` in the solver, and were never planned
  across a sequence — each shot picked its own fill independently.

## 5. No story structure

Five "beats" exist on paper (Stone / Life / Crisis / Evidence / Refuge) but the shot plan is a
uniform rotation through the same 20 camera moves. There is no escalation, no reveal timing, no
turn. A 60 s film needs at most one turn and this one has none placed.

**"Tabahi next level" is not an animation problem.** It is: anchor, punch, escalation, one
turn, and a lens that says something. All five are absent.

---

## 6. What can be adopted, with licence

Researched 2026-11-24. Only repos whose licence permits reuse are listed as adoptable.

| Repo | Stars | Licence | What it actually gives us | Verdict |
|---|---|---|---|---|
| [wuwangzhang1216/DirectorSKILL](https://github.com/wuwangzhang1216/DirectorSKILL) | 408 | MIT | 13-step pipeline; **pacing math** (ASL → shot count → right-skewed distribution); 10-item **cut motivation taxonomy**; 6-rung size ladder with the 2-rung / 30° rule; 180° axis, screen direction, eyeline, enter/exit-frame; focal-length table and lens decision table; **F1–F19 failure taxonomy** with a 60 s triage tree and a prevention map; 20 director-style overlays with machine-readable YAML | **Adopt.** The pacing math, cut taxonomy, size ladder and lens table are what sections 1–4 above prove we are missing. |
| [yzsp-studio/cinematic-camera-engine](https://github.com/yzsp-studio/cinematic-camera-engine) | 0 | MIT | Scene-type × emotion decision tree (12 × 8) → shot scale, movement, angle, focal length; 8 classic shot-flow templates; six transition rules incl. jump ≥2 scale levels and no 180° reversal; six-point self-check | **Adopt the rules**, not the text. Same rules as DirectorSKILL but expressed as a checker, which is the form we need. |
| [PardoAlejo/MovieCuts](https://github.com/PardoAlejo/MovieCuts) | 39 | MIT | 173,967 clips labelled with **10 professional cut types**; best model 47.7 % mAP | **Reference only.** We cannot train on it here, but its 10 labels are the vocabulary our cut planner should emit. |
| [Vchitect/ShotBench](https://github.com/Vchitect/ShotBench) | — | (dataset CC-BY-NC-ND) | ShotQA: ~70k cinematography QA pairs; the benchmark that shows GPT-4o scores 60.8 % on expert shot questions | **Cite only.** NC licence — do not ship weights or data derived from it. |
| [jahoi12345/cinematic-grammar-tokenizer](https://github.com/jahoi12345/cinematic-grammar-tokenizer) | 0 | MIT (code) | One 13-slot token row per shot — size, lens, angle, framing, light, comp, key, DoF, people, sound, length, palette, move — as a searchable Parquet table | **Adopt the token row as our shot-plan schema.** It is the right intermediate representation and it makes violations checkable. |

Not adoptable / not useful here: ShotVerse and FilmFlow are generation pipelines for diffusion
models, not for a real-time three.js scene; Cinematographic Camera Diffusion needs training;
XCam needs a live VR operator; the autonomous-cinematography literature (CameraCreature,
Virtual Cinematographer, Director's Lens, Cine-AI) is real-time *selection* for interactive
worlds and solves a problem we do not have — we are offline and can plan exactly.

## 7. Honest boundary

This pass produced a **diagnosis, not a new film.** The delivered master is unchanged and
still carries the flaws counted above. Rewriting the shot plan against the pacing math, the
cut taxonomy and the lens table is the next piece of work and it is a re-render, not a patch.

What is not in dispute: the render pipeline is sound (1800 frames, min luma 19.27, no flicker,
−15.2 LUFS, TP −1.5), and the camera solver behaves predictably. The failure is upstream of
both — in what was chosen to shoot.
