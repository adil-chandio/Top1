# Monarch Cam · Episode #03 (`Periplaneta americana` Crevice Mechanics)

**Working Title:** *How This Cockroach Runs Without Its Feet*  
**Format:** `9:16` Portrait Short (`1080×1920`, `30 fps`, `38.000 s` / `1,140 frames`)  
**Spine:** `Visible Ability → Hidden Control → Real Limit`

This directory contains the share-safe Step 02 pre-production package and the verified Step 02.5 **Hardest-Contact Kinematic Proof** solver for Monarch Cam Episode #03. Existing channel builds (`tools/monarch-ant*`, `tools/gecko*`) remain untouched.

---

## 1. Primary-Source Claim Ledger (`C01–C11`)

**Primary Source (`P1`):** Jayaram K, Full RJ (2016). *Cockroaches traverse crevices, crawl rapidly in confined spaces, and inspire a soft, legged robot*. **PNAS** 113(8): E950–E957. DOI: `10.1073/pnas.1514591113` · PMCID: `PMC4776529` (Full text, *Results*, *Methods*, *SI Methods*, *SI Eqs. S1–S14*, and *Tables S1–S2* verified).

| ID | Script / Visual Claim | Primary Evidence & Scope Boundary | Status |
|---|---|---|---|
| **C01** | Standing/running *P. americana* is ~half an inch (`12.5 mm`) tall | `P1` *Results*: `12.52 ± 1.48 mm` freestanding height (`0.493 in`), length `31.10 ± 2.16 mm`, mass `0.76 ± 0.16 g` (`n = 21` adult males). | **Approved** (species-scoped to *P. americana*) |
| **C02** | Traverses horizontal crevices down to `3 mm` (`3.2 mm` precision gate — two stacked US pennies) in under a second | `P1` *Results* & `Fig. 1A,D`: `3 mm` (`3.2 ± 0.05 mm` tested gate), explicitly compared to two stacked US pennies; traversal IQR `288–821 ms`. | **Approved** |
| **C03** | Shell does not bend like soft rubber; stiff chitin plates slide/shingle as soft arthrodial joints fold ~in half | `P1` p. E955 & `Table S1`: sclerotized plates remain stiff (`~3.36 GPa` reference tibia stiffness) while soft **arthrodial membranes** provide `41–57%` segmental compression (`47 ± 3%` abdominal compression at `3.2 mm`; `60 ± 12%` viscoelastic resilience at `0.5 mm/s`). | **Approved** |
| **C04** | Under extreme low ceiling (`4 mm`), legs splay wide (`~80°`), claws lose normal engagement, and tibial sensory spines push the floor | `P1` `Fig. 2B`, `Fig. 5D`, *SI Methods* & `Table S2`: sprawl angle widens up to `~81°` while tarsus midline distance stays `11.89 ± 0.96 mm`; *SI Methods* confirms compressed roaches use **tibial spines** for ground thrust (`μ_leg = 0.84–2.04`). | **Approved** (do not reenact tarsus-ablation test) |
| **C05** | Normal alternating tripod gait breaks down at `4 mm`, and both middle legs shove in synchrony | `P1` p. E952: alternating tripod maintained at `12, 9, 6 mm`, breaking down at `4 mm` *"with the middle legs often applying force in synchrony to thrust the body forward."* | **Approved** |
| **C06** | Crawling speed holds near `58 cm/s` (`12 → 6 mm`), then drops 4× to `14.5 cm/s` at `4 mm` with slipping & zigzag paths | `P1` `Fig. 2C`: `58.05 ± 2.33 cm/s` across `12, 9, 6 mm` (`P = 0.56`) vs `14.52 ± 0.98 cm/s` at `4 mm` (`P < 0.001`), with constant stride period `61.05 ± 6.06 ms`, higher foot slip, and lower straightness index. | **Approved** |
| **C07** | Rough ceilings monotonically cut speed; floor friction has an intermediate goldilocks peak due to belly drag | `P1` `Fig. 3B,C` & *SI Eqs. S8–S14*: dorsal ceiling friction (`μ_c = 0.09 → 0.46`) monotonically reduces stride length & speed; ventral ground friction peaks at medium (`40-grit`) because `20-grit` belly drag (`μ_g = 0.76`) counteracts spine thrust. | **Approved** |
| **C08** | Pass rate drops from `72%` (`6.1 mm`) to `17%` (`3.2 mm`); turning back dominates and `9%` get wedged at the thorax | `P1` `Fig. 1F` (`315` trials): `72 ± 5%` pass at `6.1 mm` vs `17 ± 3%` at `3.2 mm` (`P < 0.001`); `9 ± 2%` stuck mid-thorax. | **Approved** |
| **C09** | Normal load in `3.2 mm` slit averages `~300×` body weight; cyclic tests reached `~900×` body weight without injury | `P1` `Fig. 5B` (`2.25 ± 1.17 N` @ `3.2 mm` ≈ `300× BW`; `6.08 ± 1.61 N` dynamic peak ≈ `700–900× BW`). | **Optional sidecar note only** (hydraulic-press spectacle excluded from film) |
| **C10** | "Cockroaches are indestructible / nuclear-proof / survive anything" | Unsupported internet trope; `P1` shows `83%` fail/turn-back rate at `3.2 mm` and `9%` fatal thorax wedging. | **Rejected** |
| **C11** | All cockroach species share identical millimeter limits | `P1` tested adult male *Periplaneta americana* at `28 ± 2 °C`. | **Scoped** (`this cockroach` + *P. americana* super/credits) |

---

## 2. Standalone Comparative Script Audit

| Reference | Observed Structure (Watch-Page / Transcript) | Lesson Adopted / Pitfall Avoided |
|---|---|---|
| **Deep Look** — *Cockroach vs. Hydraulic Press: Who Wins?* (`MMeh_G0iEfs`, `03:57`, Sep 2023, `815,663` views) | Opens with household pest disgust (salmonella/asthma) → speed → chitin plates → 1-sentence `"army-crawl"` mention → `900×` press → rescue robots. | **Whitespace confirmed:** Deep Look never explains *how* legs push when splayed flat. We skip pest disgust, hydraulic-press harm framing, and robot tangents to own the `arthrodial fold + tibial-spine + 3.2 mm bottleneck` story. |
| **Deep Look** — *Tiger Beetles Bite First, Ask Questions Never* (`ojMnlGGWV1o`, `03:29`, Sep 2025, `246,480` views) | Visible sprint → motion-blur limit → blinded vs antenna-less obstacle test. | **Adopt:** immediate physical scale cue (`half an inch` vs `two pennies`) and concrete sensory/contact shift (`claws → shin spines`) without taxonomy detours. |
| **Monarch Cam 01A** — *Short V2 / Voice Match* (`34.000 s`, `105` words, `25` cues) | Cold-open action → midair vs sand-contact contrast → rim clear vs wall hit (`3` lab hits) → closing question. | **Adopt:** `~2.8 words/sec` natural documentary cadence (`108` words in `38.0 s`), frame-pinned contact Foley, honest lab failure count (`17%` pass, `9%` wedged), and loop seam back to `f0`. |
| **Monarch Cam #02** — *Gecko Creature Edition* (`62.0 s`, `24 fps`, `32` cues) | Distinguishes macroscopic animal motion from labeled anatomical diagram cuts; invariant planted-foot solver. | **Adopt:** explicit `Illustrative reconstruction` label on cutaways and automated geometric invariant tests (`test_rig.py`) before full frame rendering. |

---

## 3. Asset & Rights Ledger

- **Geometry & Cutaways:** `100%` original procedural millimeter-scale solver (`rig.py`) authored in this repository. Zero third-party 3D models, zero scraped textures, and zero copied figures or high-speed frames from `PMC4776529` or PBS/KQED.
- **Typography:** System/repo open-licensed DejaVu / OFL sans & mono fonts only.
- **Audio (Step 03+):** Fresh dry English VO via owner-selected `add_voice` speaker + procedural/OFL-clean micro-contact stems.

---

## 4. Files & Verification Commands

- [`script.md`](script.md) — Beat-by-beat `SCRIPT V1`, `PICTURE ONLY` camera notes, `24` mobile-safe caption cues, and Foley discipline.
- [`narration.txt`](narration.txt) — Spoken English lines only (`108` words, `6` takes).
- [`story.json`](story.json) & [`edit.plan`](edit.plan) — Structured take timing & `1,140`-frame (`30 fps`) shot/contact pin schedule.
- [`rig.py`](rig.py) & [`test_rig.py`](test_rig.py) — Pure-Python biomechanical posture, tergite-shingle clearance, tibial-spine engagement, and Coulomb stick–slip solver + invariant unit tests.
- [`proof.py`](proof.py) — Renders the `1080×1920` portrait **Hardest-Contact Kinematic Proof** sheet and JSON receipt into gitignored `.cache/monarch-cockroach/proof/`.

```bash
# Run biomechanical & geometric invariant unit tests (zero external deps)
python3 -B -m unittest discover -s tools/monarch-cockroach -v

# Render 1080x1920 portrait Hardest-Contact Kinematic Proof into .cache/
python3 -B tools/monarch-cockroach/proof.py
```

---

## 5. Gate Status

- [x] **Step 01:** Channel-first comparable refresh + primary `PNAS` (`PMC4776529`) verification.
- [x] **Step 02:** Claim-locked `SCRIPT V1` (`108` words / `38.000 s`), `24`-cue mobile caption map, and `1,140`-frame `edit.plan`.
- [x] **Step 02.5 (Hardest Visual/Technical Risk Proof):** `6/6` kinematic & friction invariants passing (`0` tergite collisions, rigid plate chords preserved, `55.2° → 81.5°` sprawl shift, `tarsi` lifted `> 0.42 mm` while `3` tibial spines plant at `z = 0.00 mm`, `Fig. 3` ceiling/floor stick–slip curves reproduced).
- [ ] **Step 03 (Next — Requires Owner Voice Pick):** Run `add_voice` audition on `story.json["audition_excerpt"]`, synthesize `6` dry English WAV takes, and lock sample-exact `1,140`-frame edit/SRT clocks.
- [ ] **Step 04:** Full `1,140`-frame `1080×1920` procedural render, dry-forward `-16 LUFS` Foley mix, full-decode QA, and authorized Drive package handoff.
