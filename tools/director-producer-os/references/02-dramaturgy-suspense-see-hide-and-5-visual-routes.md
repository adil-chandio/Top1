# 02 — Dramaturgy, Suspense vs Surprise, See/Hide Engine & The 5 Concrete Visual Routes

## 1. Story Dramaturgy Is Information Control
A Director does not merely "illustrate" narration sentences one by one. Doing whatever the voiceover just said (`voice says "crack" -> show crack`) is **redundant wallpaper**, and viewers tune out because neither channel adds new meaning.

Instead, great film direction runs on **Counterpoint & Information Asymmetry**:
- **Voice gives the Question or Context; Picture gives the Physical Evidence.**
- **Picture plants the Danger early; Voice only names it seconds later.**

---

## 2. Hitchcock's Three Modes (`dramaturgy.dominant_mode`)
Choose ONE primary engine per video (or per act in `16:9` long-form):

1. **`SUSPENSE` (Audience Knows MORE Than the Subject / Before the Event):**
   - *Mechanism:* Show the blocked steam vent or rising thermal stress *in Shot 1*, then return to the calm exterior object while pressure climbs. Every second now carries unbearable tension.
   - *Best For:* Engineering failures, predator-prey encounters, countdown physics, biological traps.
2. **`MYSTERY` (Audience Sees a Baffling Clue & Investigates Why):**
   - *Mechanism:* Open on an impossible physical result (*"Two unrelated species curled nose-to-tail inside sealed stone"*, *"An ant clamped at exactly 25 cm on the north side of a leaf"*). Peel away false explanations until the mechanism clicks.
   - *Best For:* Paleontology, forensic mysteries, counterintuitive everyday phenomena.
3. **`SURPRISE_PIVOT` (Controlled Expectation -> Instant Reframe):**
   - *Mechanism:* Lead the viewer into an intuitive assumption for `3–5s`, then reveal a scale jump or hidden cross-section that overturns the assumption in a single frame.
   - *Rule:* Never rely on surprise alone for an entire film; convert `SURPRISE_PIVOT` immediately into `SUSPENSE` or `MYSTERY`.

---

## 3. The `See -> Hide -> Reveal` Law
**No reveal lands unless it was actively withheld earlier.**
In `director-plan.json`, `dramaturgy.see_hide_pairs` enforces `hide_shot.t0 < reveal_shot.t0`:
- **Ways to Hide (`withholding_technique`):**
  1. *Opaque Geometry:* Intact metal casing, rock matrix, bark, frosted condensation, closed lid.
  2. *Framing Exclusion:* Tight close-up on the symptom while the cause sits just off-screen.
  3. *Scale Blindness:* Viewing at human `1:1` scale where a `20-micron` micro-fissure is invisible until the `probe_macro_glide` enters.
  4. *Shadow / Backlight Silhouette:* Showing only the rim outline until a motivated practical or grazing light sweeps across the surface.

---

## 4. The 5 Concrete Visual Routes for Abstract Ideas
Whenever a script beat mentions an abstract concept (*pressure*, *evolutionary time*, *entropy*, *neural hijack*, *thermal gradient*), translate it into one of **5 concrete filmable routes** — and **use at least 2 distinct routes per film** (`director_linter.py` hard gate):

| Route Enum | What the Camera Actually Photographs | Example |
|---|---|---|
| `LITERAL_SPECIMEN` | Tangible physical object, anatomy, fossil, hardware | Pitted brass whistle valve on a dented aluminum lid |
| `PROCESS_MECHANISM` | Cutaway / cross-section / force-transfer mechanics in motion | Superheated steam bubbles nucleating under `200 kPa` against a softening fusible alloy |
| `PHYSICAL_ANALOGY` | Familiar tactile object demonstrating an invisible scale or force | Comparing `15 MPa` jaw pressure to a car tire resting on a thumbtack |
| `CONSEQUENCE_AFTERMATH` | Physical scar, fracture, crater, sediment burial left behind | Melted silver-grey alloy droplet solidified on the lid's rim while the pot stays intact |
| `HUMAN_OR_CREATURE_WITNESS` | Scale reference or living behavior reacting to the phenomenon | A hand reaching toward the stove handle just as the safety plug vents upward |

---

## 5. Changed-Meaning Visual Motifs (`dramaturgy.motifs`)
Every memorable film plants at least **one visual motif early** (`planted_shot_id`) and returns to it at the end (`callback_shot_id`) with **transformed meaning**:
- *Shot 1 (`planted`):* Tiny dull hex nut on the pressure-cooker lid looks like an ugly manufacturing rivet.
- *Final Shot (`callback`):* The same hex nut — now vented open cleanly — reads as a life-saving sacrificial fuse, looping seamlessly back into Shot 1.
