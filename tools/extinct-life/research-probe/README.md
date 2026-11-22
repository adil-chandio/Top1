# Extinct Life — bounded research route probe

**Status:** Proof of concept, not a production research system, audience-demand measurement, recommendation or approval to produce videos. All work is on the session branch. The workflow is push-triggered only by changes to the probe or its workflow on this branch; there is no schedule, upload or publication step. This repository is public: check annotations and logs are public. Do not add private channel data or secrets to the probe, output or repository.

## Latest YouTube API recheck

[Successful run 44990681888](https://github.com/adil-chandio/Top1/actions/runs/44990681888) on commit `b4eb96b` reached the YouTube Data API with a configured key and returned three public video records, including titles, upload dates, duration and view snapshots. The job reports only public metadata; no credential value is displayed. This validates the bounded `videos.list` request, not bulk collection, channel enumeration, search quota, analytics, or historical growth tracking. The earlier no-key observation below describes the previous run, not the latest state.

## Earlier evidence: 22 November 2026

[Successful GitHub Actions run 44989118473](https://github.com/adil-chandio/Top1/actions/runs/44989118473) on commit `f903d01`: public check annotations report the results below. A successful job alone does not mean every source succeeded: the script deliberately reports unavailable routes separately.

- **YouTube Data API:** authenticated request skipped: no candidate API secret was made available to this run. A no-key request returned HTTP 403; this shows the runner reached an HTTP response, not that it can retrieve authorized YouTube data. No view counts collected. Do not infer that a key exists, is valid, or would fix access.
- **Crossref:** queried DOI `10.1126/science.adw3536` and returned its metadata title. This verifies a metadata route, not the entire scientific claim.
- **Europe PMC:** known DOI query returned one hit. A query for dinosaur and fossil in title/abstract since 2025 through 2026-11-22 returned 53 hits. The first three by date included two `PPR` preprints and a turtle paper. Search output can include irrelevant results, preprints and incomplete records; none were scientifically reviewed. It is a discovery lead list, not proof of novelty, audience demand, or validity.
- **Hugging Face registry:** public metadata for `sentence-transformers/all-MiniLM-L6-v2` retrieved successfully.
- **Hugging Face actual inference:** separate test downloaded public pinned ONNX/tokenizer files for `Xenova/all-MiniLM-L6-v2` at revision `751bff37182d3f1213fa05d7196b954e230abad9`, ran CPU inference locally on the runner and deleted temporary model files. Model registry marks it Apache-2.0; review license and model card before production use. Only synthetic text and four already-public video titles were processed; no channel credentials or private data were sent to the model host.

For the query `How did clay preserve the skin of a dinosaur mummy?`, title similarity was: University of Chicago [mummy discovery](https://www.youtube.com/watch?v=i2OYcptFl9c) **0.5106**, Ben G Thomas [tyrannosaur last meal](https://www.youtube.com/watch?v=eGGb9GFVEpM) **0.4483**, Eons [trees](https://www.youtube.com/watch?v=yN4Ck8CSdWU) **0.2438**, Moth [ground sloths](https://www.youtube.com/watch?v=ii92Yx0orEw) **0.2096**. These are cosine similarities on four hand-selected titles, not accuracy, audience interest, percentages or viral probabilities. It demonstrates semantic retrieval, not broad overlap coverage; independently evaluate on a labeled representative sample before relying on it. PPR means preprint, not verified peer review.

## Access and use limitations

The runner reaches services unavailable directly to the Arena sandbox, but that does not grant permission to scrape YouTube, bypass controls, or download video. Use official APIs and applicable terms. Any later YouTube API integration must check quota, developer policies, derived metrics permissions, refresh/deletion requirements and no storage of private authorized data in public artifacts. The current probe's output consists only of public or synthetic material. GitHub Actions costs/limits can change; the repo is public and this probe uses a standard Linux runner, but usage and billing still need review before scaling.

Do not confuse the registry-only check with the actual inference step. Model outputs have not been validated on a representative benchmark. The YouTube Analytics API for the user's own channel would need separately authorized access and a private handling design; competitor private CTR/retention remains unavailable. Neither Google Trends nor vidIQ was connected or measured in this test.

## What is built

- `.github/workflows/extinct-life-research-probe.yml` — bounded branch-only runner, `contents: read`, timeout, pinned checkout, no scheduled work and no upload.
- `probe.py` — safe public API/registry access checks with bounded responses and sanitized errors.
- `semantic_probe.py` — small ONNX semantic retrieval test with fixed inputs and bounded model downloads.

The repository-wide GitHub Actions permissions endpoint returned 403 to the current integration, although the above actual run succeeded. Do not assume administrative permissions, current secret availability, or that a branch-only workflow can be manually dispatched under GitHub's default-branch rules.

**Possible next phase, pending authorization:** design a separate, modular public-data pipeline and manually review YouTube/Google data handling rules; test an authenticated official API route on the runner if a properly configured secret and permissions are available. Add age/format matched comparisons, overlap retrieval, scientific-source verification, human review and explicit uncertainty. A single similarity value is not an idea-ranking system.
