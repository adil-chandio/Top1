# Capability register — verified 2026-11-16

Har row ka evidence actual test hai, README claim nahi. Jo cheez bilkul reachable
nahi woh `blocked` rehti hai — usay "green" nahi likha gaya.

## Network reality (measured this session)

| Host | HTTP | Note |
|---|---|---|
| `api.github.com` | 200 | reachable |
| `pypi.org` | 200 | reachable |
| `youtube.com` | 000 | blocked |
| `instagram.com` | 000 | blocked |
| `tiktok.com` | 000 | blocked |
| `raw.githubusercontent.com` | 000 | blocked |
| `huggingface.co` | TLS EOF | blocked |

## Route 1 — Reference AV inspection

| Field | Before | Now | Evidence |
|---|---|---|---|
| `moving_video_inspection` | ❌ unavailable | ✅ **available** | downloaded `big_buck_bunny.mp4` 5,510,872 bytes via `api.github.com`, decoded with FFmpeg, extracted 5 frames, inspected them visually |
| `actual_audio_listening` | ❌ unavailable | ⚠️ **spectral_analysed** (not listening) | 60.10 s WAV, FFT spectral centroid per frame, 57 onsets detected, silence ratio 0.535 |
| `transcript_access` | ❌ unavailable | ❌ **still blocked** | faster-whisper installed, but model host `huggingface.co` unreachable |
| competitor platform playback | ❌ | ❌ **still blocked** | network 000 |

**Implementation:** `accounts_studio/reference_av.py`
**Honest label used:** `video_viewed` (real frames inspected) and
`spectral_analysed`. Never `audio_listened`.

## Route 2 — Independent reviewer

| Field | Before | Now | Evidence |
|---|---|---|---|
| `independent_reviewer` | ❌ unavailable | ✅ **separate_process_context** | `review_probe.py` runs with different cwd (`/tmp`), different env, closed stdin |
| distinct language model | ❌ | ❌ **honestly still false** | same model family; only the context is separate |
| creative/human review | ❌ | ❌ **not claimed** | probe reports `cannot: [creative_judgement, human_viewing, listening, factual_verification]` |
| ephemeral runner route | ❌ | ✅ **implemented** (`github_review`) but not fabricated | prepares a request; never invents the runner's answer |

**Implementation:** `accounts_studio/reference_review.py`, `review_probe.py`

**What this actually buys us:** hash binding, container/stream verification,
defect detection, and a genuine second execution context. **What it does not
buy us:** a second opinion on taste.

## Route 3 — Durable state

| Field | Before | Now | Evidence |
|---|---|---|---|
| `durable_state_storage` | ❌ partial (sandbox-local) | ✅ **git-tracked checkpoint + restore** | full `runtime/` wipe, then restore recovered job `soc_01-2eae823b0144` with account, status, stage, created_at and brief intact |
| artifacts survive | ❌ | ❌ **honestly still no** | checkpoint records `present`/`actual_sha256` per artifact and restore re-verifies; missing media is reported as missing, never faked |
| background execution | partial | partial (GitHub Actions only) | unchanged |

**Implementation:** `accounts_studio/state.py`, checkpoints in
`accounts_studio/state/<job_id>.json` (force-added past `.gitignore`).

## Test evidence

```
python3 -m unittest discover -s accounts_studio/tests
Ran 39 tests ... OK
```

15 of those 39 tests exist specifically to keep these three routes honest,
including:

- `test_probe_cannot_claim_creative_review` — asserts the probe lists
  `creative_judgement` under `cannot`.
- `test_subprocess_review_is_honest_about_independence` — asserts
  `different_language_model` is **False**.
- `test_github_review_never_fabricates_a_result` — asserts the request
  contains no `approved` or `verdict` key.
- `test_restore_does_not_claim_media_survived` — asserts a deleted artifact is
  reported missing, and that the response says the checkpoint "never pretends
  bytes survived".
- `test_spectral_labels_never_claim_listening` — asserts the label
  `spectral_analysed` and the `not_claimed` list are present.

## Summary

| Red item | Status | Honest qualifier |
|---|---|---|
| Reference AV inspection | 🟢 **green** | via GitHub-hosted public media; competitor platforms still blocked |
| Independent reviewer | 🟡 **green, limited** | separate process context + ephemeral runner route; not a different model, not human, not creative |
| Durable state | 🟢 **green** | state survives reset; media does not and is reported as missing |

Nothing here converts a blocked platform into a working one. Nothing here
turns a mechanical check into artistic approval.
