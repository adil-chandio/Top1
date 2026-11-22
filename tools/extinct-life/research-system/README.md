# Extinct Life research desk

A bounded, read-only research workflow. It collects YouTube public video metadata, finds literature leads, runs local semantic matching on scientific titles, and assembles a source-separated report and a human decision worksheet. It is **not** an automatic viral predictor, a fully autonomous topic selector, a video-production tool or a publication tool.

## What runs

1. `research.py youtube` uses the official YouTube Data API for each configured channel's uploads playlist (up to 30 entries) and three targeted candidate searches (up to 8 results each), then gets video metadata. Counts are lifetime snapshots. Short videos, uploads with unusual formats, sponsorships, etc. are not automatically excluded; review those manually. Search and playlist results are not exhaustive. Individual channel groups and search results are kept separate.
2. `research.py science` fetches candidate DOI metadata from Crossref and recent leads from Europe PMC. This is not a substitute for reading the papers. A `PPR` source denotes a preprint and is not automatically peer-reviewed. Coverage and relevance vary.
3. `semantic_science.py` downloads a pinned, public Hugging Face quantized model and uses CPU inference to compare each configured scientific question with Europe PMC paper titles. This step **does not consume YouTube API data**. Cosine similarity is only an uncalibrated relevance hint, not scientific validity, demand or probability of success. It has not been evaluated on a representative labeled set.
4. `research.py report` assembles `REPORT.md` and a qualitative worksheet. A human reviewer can optionally supply a decision JSON identifying a recommendation, strongest alternative, reasoning, overlap, scientific limits, visual/rights proof and source links. The code does not infer a winner from API views. Users must review original sources and thumbnail images; thumbnail URLs are not proof an image was inspected.
5. `research.py gate` fails when an input is missing or a source reports an error. A complete collection does **not** mean the scientific, copyright or editorial review is complete.

## YouTube policy gate — important

[YouTube's developer policies](https://developers.google.com/youtube/terms/developer-policies) and [derived metrics policy](https://developers.google.com/youtube/terms/derived-metrics-policy) restrict creating new/derived metrics from API data unless the required analytics use case has been applied for and approved. Therefore this version intentionally does **not** compute API-derived medians, outlier scores, views per day, relative rankings, topic tags, YouTube-title embeddings or automated topic scores. Providing an API key does not establish such approval. The prior plan to calculate these automatically is **not implemented**; check the current policies and obtain appropriate approval before extending the tool. This is an engineering precaution, not legal advice or a compliance certification. API results and independently sourced science/model outputs are visibly separated.

## Safety and retention

- Public repository: do **not** put secrets, personal data, Studio exports, private analytics or credentials in code, logs, reports or public artifacts. The YouTube step receives configured GitHub Actions secrets only as environment variables for that step. Errors are sanitized and the collector does not print API response bodies or secret-bearing URLs.
- The Actions report and raw response extracts contain **public YouTube API data**, go into a GitHub Actions artifact with `retention-days: 1`, and are not committed. The job logs print status only, not YouTube metadata. YouTube data have refresh/deletion rules: if reports are downloaded or copied elsewhere, handle and delete/refresh them according to current policy. No long-term historical stats database is provided.
- No transcription, bulk downloading, scraping, bypassing access controls, uploading, scheduling or modifying YouTube content. No external audio/video files are stored.
- The semantic model is run locally in the runner. Only Hugging Face model files are downloaded; no private channel data is sent to Hugging Face. Temporary weights are deleted after inference.

## Inputs and outputs

`config.json` defines four channels, 30 latest uploads per channel, three candidate search phrases and DOI references, and three science searches. This is a small discovery sample, not a representative or channel-performance baseline. Config validation caps channels, queries and results. Adapt the terms/candidates as research evolves, without committing API responses.

Each run yields an `extinct-life-research-report` artifact containing:

- `REPORT.md`: grouped public YouTube observations; source-separated scientific lead list; model-assisted scientific-title matches; decision worksheet; limitations and failures.
- `youtube.json`, `science.json`, `semantic.json`: machine-readable extracts from their respective sources. Their public contents should be treated as time-limited. Data inside may be incomplete even if the quality gate passed.

Open the run on GitHub → **Artifacts** → `extinct-life-research-report`, download and open `REPORT.md`. The artifact expires after one day; rerun the workflow for a fresh report. Downloaded copies are your responsibility under source policies. No report content is injected into public job logs. In this Arena sandbox, GitHub's artifact storage redirect was not directly reachable during testing; the user can download it from GitHub in their browser, but the agent cannot claim to have read that artifact here. To review its contents together, the user can attach the public-data report in chat before it expires.

## Running and configuring

The branch-only workflow is `.github/workflows/extinct-life-research-system.yml`. It runs on a push changing the workflow or research-system directory on the current session branch. It is not scheduled, and `workflow_dispatch` requires the workflow to exist on the repository's default branch; do not assume a manual run button exists on this branch. API access was verified in a separate probe; the actual collection must still be checked. When extending or merging, review triggers, quotas, permissions and costs first.

Offline tests:

```sh
python3 -m unittest discover -s tools/extinct-life/research-system/tests -v
```

To assemble a report locally from already-collected files in a private scratch directory:

```sh
python3 tools/extinct-life/research-system/research.py report --out .cache/extinct-life-research
```

Optional human decision: create a local JSON document (not in Git) with the following fields, using two **different IDs from config.json** and real supporting HTTPS sources. Then pass `--review path/to/review.json` to `report`. This is a human-authored decision, not a score calculated by the tool.

```json
{
  "recommended_id": "clay-mummy",
  "alternative_id": "gorgosaurus-meal",
  "reason": "Replace with reviewed reasoning.",
  "science_limit": "Replace with the scientific uncertainty.",
  "visual_proof": "Replace with the specific proof and rights check.",
  "overlap": "Replace with checked competing coverage and the difference.",
  "alternative_reason": "Replace with the strongest alternative's rationale.",
  "sources": ["https://www.science.org/doi/10.1126/science.adw3536"]
}
```

The example is **only a format example**, not an approved current topic. Do not commit API-derived report data or a completed review containing time-limited API metadata to Git. The code does not schedule runs or make a channel-wide baseline assertion.

## Tested, limitations, and extensions

A successful prior Actions probe confirmed the runner can reach Crossref, Europe PMC, Hugging Face and the authenticated YouTube Data API for three video records. This complete workflow's own run should be inspected separately. Unit tests use fake fixtures and do not prove network access. HTTP/quota errors are captured without leaking keys; partial reports are generated, but the final gate fails.

The repository is public. API policy review, privacy policy and any required analytics-use approvals are separate requirements before wider deployment. To later support richer relative performance / historical snapshots, first obtain appropriate YouTube authorization and implement compliant retention, refresh/delete, isolated storage and quota monitoring. A private owner-authorized Studio analytics integration is not built.
