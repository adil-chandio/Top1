# Huayuan — production manifests (V6.2 pass 2)

Locked before a single frame is rendered. Every on-screen claim traces to a source row; every
whisper-caption traces to the approved narration SRT (voice 1.000×, no retime, no re-record).

## 1. Approval boundary

| Item | State |
|---|---|
| Audio | Approved **mixed** stereo track, stream-copied from `Huayuan-60s-3D-review-WIP.mp4` (`4caf0167…4baea`, 36,576,841 B). PCM SHA-256 `6bb74d9c8645b6e4ea1438ade1a7738d7d69865b013b1b5c2c581f2e30ab9348` — re-verified on 2026-11-24 against the Drive file. |
| Voice speed | **1.000×** — the track is used untouched end-to-end. No stretch, no retime, no re-voice. |
| What the mix is | Music + SFX are **baked in** with the narration. Therefore this pass cannot claim an independent score, and all new sound work is limited to what a picture cut may add *under* it without touching the narration band, which is impossible without stems — so: **no new audio is added at all.** |
| Captions | Derived from the approved SRT, re-timed only where the film's own shot grid requires a cue boundary (text never contradicts the spoken line). |

## 2. Sources

| ID | Claim | Source |
|---|---|---|
| S1 | ~512 Ma, lower Cambrian Stage 4, outer-shelf deep-water setting, Yangtze Block, Hunan, South China | Nature 2025, `s41586-025-10030-0` (abstract) |
| S2 | 153 animal species, 16 phylum-level clades, dominated by arthropods, poriferans, cnidarians; 59 % of species new | ibid. |
| S3 | Dated shortly **after** the Sinsk event (the first Phanerozoic mass extinction) | ibid. |
| S4 | Preserved cellular tissues in overwhelmingly soft-bodied forms | ibid. |
| S5 | Possible Cambrian environmental change; precise causes and local timing uncertain | Myrow et al., `par.nsf.gov/servlets/purl/10520526` |
| S6 | Deeper-water refuge as an explanation is a **suggestion**, not a demonstrated cause | PROJECT-STATUS.md; Nature abstract does not assert a refuge |

## 3. Claim classification per beat

| Beat | Frames | Type | Rule |
|---|---|---|---|
| 1 Stone | 0–150 | **Observation** (the rock exists; BST preservation is documented) | ok to state |
| 2 Life | 150–390 | **Reconstruction** (illustrative animals) | must be labelled `RECONSTRUCTION` |
| 3 Burial | 390–720 | **Process** (BST preservation mechanism, standard) + illustrative crisis | label `CONCEPTUAL` |
| 4 Evidence | 720–930 | **Observation** (eyes/gills/nerves reported; 153/16 counted) | cite on screen |
| 5 Refuge | 930–1200 | **Hypothesis** | label `HYPOTHESIS` |

## 4. Model credits (must ship with any release)

- Radiodont/Anomalocaris model: Skache, CC BY 4.0, Sketchfab `dad76e60589a41e18a42db1e979f81f8`; rigged derivative via `chengong201/prehistoric-animal-museum`. **Generic reconstruction — not a Huayuan specimen.**
- Opabinia: billionlioe, CC BY 4.0, `d2111e360cdc4243aac23871836c49f5`; same derivative repo.
- Hallucigenia: huykhoi2407, CC BY 4.0, `fad8306e863a4960b48e49c16c3806cf`; same derivative repo.
- Rocks: Coast Rocks 01/03 (Rob Tuytel, Rico Cilliers, CC0, Poly Haven), Rock 07 (Jenelle van Heerden, CC0, Poly Haven); derivatives via `2600th/web-ocean-3d` `ASSET_LICENSES.md`.
- No creator endorses this film.

## 5. Honest gate status at the time of writing

| Gate | State |
|---|---|
| G5 two-pass preflight eye-gate | will run in this pass; results recorded in `notes/` |
| G7 forensic QA | will run; loudness/true-peak already known from the parent master (−15.2 LUFS, −1.5 dBTP) |
| Human creative review | **not performed** — a technical pass is not a creative pass |
| Expert science review | **not performed** |
| Continuous subjective listening | **not performed** |
