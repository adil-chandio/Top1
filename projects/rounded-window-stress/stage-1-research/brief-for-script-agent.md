# Stage 1 → Stage 2 brief — `rounded-window-stress`

**Format:** `9:16` Short, target 35–45 s, loopable · **Date:** 2026-11-25 · **Decision:** `not-yet` (owner gate + claim ledger deliberately open)

> **Evidence status (read first):** the official-API outlier workflow was pushed but could not be dispatched from this sandbox (`HTTP 403`, missing `actions: write`). All `outlier_multiple` values below are therefore **unverified — not computed**. Sources are public YouTube pages fetched with `fetch_page`; only titles, dates, lengths, public view counts, descriptions and transcripts were observed. No image/thumbnail was visually inspected, no comments were mined, and no media was reused.

## Ranked ideas

| # | Idea | Observed signal (NOT outlier score) | `outlier_multiple` | Paradox / "Wait." beat | 3D proof concept | Thumbnail concept | CPM / retention potential |
|---|---|---|---|---|---|---|---|
| 1 | **The shape that stopped planes tearing open** — round vs square cabin window | LuxPlanes 26 s short: 376,625 views; Crayon Monkey 8 min physical demo: 5,522 views ([E6AUYtJwiLs](https://www.youtube.com/watch?v=E6AUYtJwiLs), [hrHw4oxeBzE](https://www.youtube.com/watch?v=hrHw4oxeBzE)) | `null` — unverified | "It wasn't the engine. It wasn't the wings. It was the **corners**." → four sharp corners concentrate stress; a round opening lets it flow around. | Sealed aluminium fuselage panel, parametric lofted skin, alternating pressure cycles; square cutout vs round cutout side-by-side; illustrative stress glow at corners; microcrack propagation along a rivet line; X-ray/sagittal layer showing frame reinforcement around old cockpit windows. Explicitly labelled illustrative, not FEA. | Split frame: square window with red corners vs round window with calm blue flow, 3 words max: **"SAME SKIN. DIFFERENT FATE."** Subject centred, left/right safe zone clear. | High — aviation + engineering advertising; 26 s short at 376k and an 8 min demo both drew attention, so both hook-first and explainer-first formats have precedent. |
| 2 | **A wire holds 5 kg once — and snaps under less** — metal fatigue | Paperclip demo 5,189 views; car-parts fatigue 223 views ([CvHX7l5nPj4](https://www.youtube.com/watch?v=CvHX7l5nPj4), [J2jG0-dwXTU](https://www.youtube.com/watch?v=J2jG0-dwXTU)) | `null` — unverified | "Nothing changed in the metal. Only the *direction* of the force changed." | Single paperclip wire lofted as a curve, 1 static load then 30 cyclic bends, crack initiation at the inner radius, beachmark close-up, shot-peened compressive surface layer vs untreated. Newtonian bending, no torus/box toys. | One bent paperclip, fracture point glowing, text **"ONE BEND TOO MANY"**. | Medium-high — engineering/manufacturing CPM; practical payoff, strong loop on the final snap. |
| 3 | **Gravity-defying lizard, zero glue** — gecko setae | History of Simple Things 8:35: 2,732 views ([−koT6H6Ew_Q](https://www.youtube.com/watch?v=-koT6H6Ew_Q)) | `null` — unverified | "No glue. No suction. No sticky residue — yet it hangs from glass." | Hierarchical macro-to-nano setae/spatulae field via instanced geometry, contact-point count animation, peel-angle release, Van der Waals attraction shown as illustrative field lines (never as measured force). | Gecko toe macro with lattice pattern and ceiling silhouette, text **"NOT STICKY"**. | Medium — biology/nature CPM; high curiosity, lower direct monetisation than engineering. |
| 4 | **The sign with no bulb** — retroreflection | Road Guy Rob 12:40: 567,821 views; BIS compliance video: 381 views ([iPVlw2kBDCU](https://www.youtube.com/watch?v=iPVlw2kBDCU), [ujunNZDnL58](https://www.youtube.com/watch?v=ujunNZDnL58)) | `null` — unverified | "It has no power — it sends *your own headlights* back at you." | Corner-cube with three perpendicular bounces, antiparallel return path, microbead sheeting, controlled lamp-on/lamp-off comparison. | Dark road, single glowing sign, text **"NO BULB. STILL BRIGHT."** | **Do not greenlight as new topic** — this is already shipped as Monarch Studio Project 002 (*The Light With No Battery*). Use only as a format benchmark. |
| 5 | Format reference only — extreme-heat satisfying | RHCB 3:01: 3,144,190 views ([Hf0HNtBJek8](https://www.youtube.com/watch?v=Hf0HNtBJek8)) | `null` — unverified | "Hot metal meets ice — what survives?" | N/A for this project. | N/A | Not a candidate: adjacent-niche 10x format signal. Bend the *rhythm* (rapid object-by-object reveal, ASMR payoff) into our engineering explanations; do not copy the content. |

**Cross-niche format bending (Stage A requirement):** idea 1 borrows the "one object after another / satisfying demonstration" cadence from idea 5, but replaces destruction with a **shape change** and a visual stress reveal. That keeps the retention beat while staying 100% sponsor-safe.

## Winner: `rounded-window-stress`

* **One-line promise:** "Why a single shape choice — round instead of square — stopped aircraft skins from tearing."
* **Twist ("Wait." beat):** at ~55% of the film, freeze the square corner, kill the sound for ~180 ms, then reveal stress lines pooling in that corner while the round version stays calm.
* **Loop:** end on the round window silhouette morphing back to the square one at frame 0.
* **Visual proof plan:** parametric fuselage loft → cutaway skin/rivets/frame → square vs round apertures → 6 pressure cycles → illustrative stress glow → microcrack → safe round result. All physics is explanatory; no FEA claim.
* **Brand safety:** historical 1950s engineering lesson only. No crash imagery, no fatalities shown, no gore, no unverified current-aircraft safety claim. A source line may cite the publicly documented de Havilland Comet investigation without reusing footage.

## Three hook variants for Stage 2

1. "You've flown a hundred times and never noticed this: your window is round for a reason." *(observational, from [The Null Project] transcript)*
2. "You might think it's a design quirk. It's not — it's where the metal used to tear." *(contradiction, from LuxPlanes transcript)*
3. "Same aircraft skin. Same pressure. One corner shape changed everything." *(parallel-structure, loop-friendly)*

## Audience questions to answer (from observed transcripts)

* Why not just make the cockpit/door windows square too? → reinforced frames; modern types round these as well (observed in [hrHw4oxeBzE]).
* Didn't engineers already know about metal fatigue? → they knew the material; they underestimated **pressure cycles** (observed in [hrHw4oxeBzE], [CvHX7l5nPj4]).
* Is the stress glow real measurement? → **No.** Illustrative visualisation only; say it on screen.

## Claws Vision takeaways

**Blocked, not faked.** `i.ytimg.com` is unreachable from this sandbox (`SSL_ERROR_SYSCALL`), and image search returned unrelated stock images rather than the exact thumbnails. No palette/focal-subject/word-count audit was performed. Stage 2 must either run Claws Vision where image access exists or mark the thumbnail concept as an untested hypothesis. The thumbnail directions above are derived from video titles and descriptions, not from inspected pixels.

## Gate status for Stage 2

| Gate | Status | Note |
|---|---|---|
| Visual proof | PASS (concept) | Fully 3D-provable with lofting, cutaway, cyclic motion |
| Paradox / "Wait." | PASS | Corner stress reveal |
| V6.2 IMAX feasibility | PASS (concept) | Uses SDK loft/cutaway/physics; no primitive hero actors |
| Brand safety | CONDITIONAL | Educational framing only; no crash footage or gore |
| Claim ledger | **NOT COMPLETE** | No claim ledger yet — Stage 2 must build it |
| Owner selection | **NOT COMPLETE** | Scorecard therefore stays `not-yet` |

Schema-valid artifacts: `research.json`, `idea-scorecard.json`. Do not promote to `production-candidate` until the owner gate and claim ledger are green.
