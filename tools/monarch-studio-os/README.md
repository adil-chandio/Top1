# Monarch Studio OS (`tools/monarch-studio-os/`)

Closed-loop pre-production, native rendering, claim-linting, packaging, and full-decode QA operating system for **Monarch Cam** (and reusable across sibling channels without touching archived Episode `#01A` Ant or Episode `#02` Gecko files).

## Core Principle

No workflow can truthfully guarantee virality on every upload—YouTube distribution depends on audience timing, impressions, and competition. **Monarch Studio OS** guarantees that no weak idea enters production, no unverified claim enters narration, no unproven mechanism skips an `8–12 s` native moving 3D proof, no automated script promotes a video to `published`, and every published upload feeds structured learning back into the next episode.

## Strategic Epistemological Chain (Mandatory in Every Film)

1. **What the viewer just saw** (`what_viewer_saw`)
2. **The physical / biomechanical mechanism** (`physical_mechanism`)
3. **What the primary evidence actually is** (`supporting_evidence`)
4. **What the evidence does NOT prove** (`what_evidence_does_not_prove`)
5. **How the viewer's understanding changed** (`viewer_understanding_shift`)

## Directory Map

- `schemas/` — JSON Schema (`2020-12`) definitions for `project.json`, `claims.json`, `scorecard.json`, `rights.json`, `shot-plan.json`, `packaging.json`, and `qa-report.json`.
- `bible/monarch-cam-series-bible.json` — Palette, mobile-first typography rules, narration cadence bounds (`8.5–11.5` avg words/sentence), and separated `16:9` Long vs `9:16` Short editorial grammars.
- `manifests/dependencies.json` — Pinned compiler & wheel registry with purpose, version, release artifact, license, SHA-256, security risk, and replacement option.
- `validators/state_machine.py` — Formal 15-state lifecycle (`idea` → `published`, blocking automated promotion to `owner-selected`, `owner-accepted`, or `published`) + content-addressed Workflow Dependency DAG.
- `validators/claim_linter.py` — Automated 1-to-1 paragraph claim linter, forbidden overstatement detector, 100-point scorecard verifier, and Zero-Trust Privacy scanner.
- `validators/media_qa.py` — Full-decode `PyAV` + `NumPy` + `SciPy` + `pyloudnorm` QA validator (exact CFR frame count, black/freeze detector, A/V sync, EBU R128 `LUFS-I`, `4×` oversampled True Peak `dBTP`, mono correlation, and `480/320/176/120px` mobile readability).
- `warehouse/cohort_store.py` — Typed SQLite research warehouse builder enforcing `views_descriptive_only = 1`.
