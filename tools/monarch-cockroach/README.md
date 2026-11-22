# Monarch Cam · Episode #03 (`Periplaneta americana` Crevice & Shin-Spine Mechanics)

**Recommended Title:** *How This Cockroach Runs Without Its Feet*  
**Active Primary Edition:** `16:9` English Long-Form Documentary (`1920×1080`, `30 fps`, `SCRIPT V2` — `794` spoken words, `81` sentences at `9.8` avg words/sentence, `7` chapters / `30` paragraphs, `78` planned shots)  
**Spine:** `Visible Ability → Hidden Control → Real Limit`

This directory holds the share-safe biomechanical solver, unit tests, and separated edition plans for Monarch Cam Episode #03. Existing channel builds (`tools/monarch-ant*`, `tools/gecko*`) remain untouched (`0` diffs), and no private Drive IDs or binary renders are stored in Git.

---

## Edition Layout (Strict Separation)

- **[`feature/`](feature/) — Active Primary Build (`16:9` Long-Form Documentary):**
  - [`feature/script.md`](feature/script.md) — `SCRIPT V2` (`794` words, `81` sentences, `9.8` avg / `18` max words/sentence, `7` scenes, `PICTURE ONLY` staging notes, verbatim multi-million-view viral script audit, V1→V2 scorecard, and `PMC4776529` claim gate).
  - [`feature/narration.txt`](feature/narration.txt) — Spoken English narration only (`30` paragraphs mapped across `7` chapter takes).
  - [`feature/story.json`](feature/story.json) — Structured chapter metadata, paragraph bounds `[0, 6, 10, 14, 19, 23, 27, 30]`, `32 s` picture-hold budget, and Step 03 `audition_excerpt`.
  - [`feature/feature_cut.py`](feature/feature_cut.py) & [`feature/feature.plan`](feature/feature.plan) — Deterministic `78`-shot `16:9` (`30 fps`) schedule ready to lock onto Step 03 WAV sample anchors.
  - [`feature/proof_16x9.py`](feature/proof_16x9.py) — Renders the `1920×1080` (`2×` supersampled) **Long-Form Hardest-Contact & Multi-Experiment Kinematic Proof** board into `.cache/monarch-cockroach/feature-proof/`.
  - [`feature/export_script_booklet.py`](feature/export_script_booklet.py) — Builds the 8-page widescreen `Step 02` (`SCRIPT V2`) review PDF booklet and HTML export in `.cache/monarch-cockroach/script-export/`.
  - [`feature/launch-copy-draft.txt`](feature/launch-copy-draft.txt) — Pre-VO `16:9` YouTube title, description, 7-chapter timestamps, and primary `PNAS` citation draft.
- **[`short/`](short/) — Preserved Separate Draft (`9:16` Vertical Short, Held):**
  - Isolated `38.000 s` (`108`-word) portrait Short draft preserved untouched until after the `16:9` Long-Form Feature is completed.
- **Shared Millimeter-Scale Biomechanical Solver:**
  - [`rig.py`](rig.py) & [`test_rig.py`](test_rig.py) — Pure-Python solver + `10/10` invariant tests covering the `5`-stage `3.2 mm` crevice squeeze, rigid tergite chord conservation & arthrodial hinge folding, `12→9→6→4 mm` corridor speed cliff, `tarsal-claw → tibial-spine` transition, `638`-trial stick–slip friction tradeoff, and `315`-trial crevice bottleneck (`Jayaram & Full, PNAS 2016, PMC4776529`).

---

## Verification Commands

```bash
# 1. Run all 10 biomechanical & geometric invariant unit tests
python3 -B -m unittest discover -s tools/monarch-cockroach -v

# 2. Verify the 78-shot 16:9 feature schedule
python3 -B tools/monarch-cockroach/feature/feature_cut.py

# 3. Render 1920x1080 Long-Form Kinematic Proof + 7-page Step 02 Booklet PDF into .cache/
PYTHONPATH=/tmp/py python3 -B tools/monarch-cockroach/feature/proof_16x9.py
PYTHONPATH=/tmp/py python3 -B tools/monarch-cockroach/feature/export_script_booklet.py
```

---

## Production Gate Status (`16:9` Long-Form Feature)

- [x] **Step 01:** Channel-first comparable audit + full primary `PNAS` (`PMC4776529`) verification.
- [x] **Step 02 (`SCRIPT V1` → Upgraded `SCRIPT V2`):** `794`-word / `81`-sentence (`9.8` avg w/sent) / `7`-chapter / `30`-paragraph Long-Form documentary script upgraded after line-by-line multi-million-view transcript audit, `78`-shot `feature.plan`, and 8-page editorial review PDF booklet (`V1` preserved non-destructively).
- [x] **Step 02.5 (`16:9` Kinematic Proof):** `10/10` solver tests passing + `1920×1080` visual proof verified.
- [ ] **Step 03 (`VO V1` — Next Gate):** Audition narrator via `add_voice`, synthesize `7` clean dry chapter WAV takes, verify pronunciation/loudness, and lock `feature.plan` + `.en.srt` to exact sample timestamps.
- [ ] **Step 04 (`Opening Pilot` → `Full 16:9 Cut`):** Native `1920×1080` / `1280×720` procedural 3D/2.5D chapter renders, synced micro-contact Foley + chamber score mix, full-decode QA, and Google Drive handoff.
