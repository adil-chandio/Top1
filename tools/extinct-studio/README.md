# Extinct Studio OS

This is the new, topic-agnostic operating layer for the Extinct channel. It is a
workflow and quality system, not a public archive and not a publisher.

The historical `tools/extinct-life/` work remains reference material only. A new
project must be created under a separate project directory and must not silently
reuse a historical subject, voice, shot, source plate, or release status.

## What this adds

- A sequential editorial state machine from `idea` through `private-uploaded`.
- A scored idea gate that separates editorial readiness from viral prediction.
- Machine-readable research, claim, rights, story, proof, voice, render, audio,
  video, owner-signoff, and Studio receipts.
- Safety checks for private Drive/Docs URLs, credentials, unknown rights, stale
  claims, reused source footage, failed proof gates, and unsanctioned status jumps.
- Read-only commands. The CLI never uploads, shares, schedules, publishes, or
  edits a project status.

## Commands

Run from the repository root:

```sh
npm run studio:check
node tools/extinct-studio/cli.mjs score path/to/ideas.json
node tools/extinct-studio/cli.mjs validate path/to/project
node tools/extinct-studio/cli.mjs check-transition path/to/project researched
```

`check-transition` checks the next state without writing anything. `published` is
intentionally rejected by the CLI; publication is a separate owner-manual action.

## State machine

```text
idea
→ researched
→ shortlisted
→ owner-selected
→ claims-locked
→ scripted
→ proof-pending
→ proof-passed
→ voice-locked
→ picture-locked
→ mix-locked
→ qa-passed
→ owner-accepted
→ private-uploaded
→ published (owner-manual only)
```

A state is not a quality claim by itself. The corresponding receipts must pass.
For example, `proof-passed` requires an 8–12 second native moving proof, a
frame-count clock, a phone review, a human review, and an explicit assertion
that third-party source footage was not reused.

## Idea gate

Ideas use 0–5 ratings with these weights:

| Dimension | Weight |
| --- | ---: |
| Audience clarity | 20 |
| Visual proof | 20 |
| Novelty | 15 |
| Evidence strength | 15 |
| Stakes | 10 |
| Format fit | 10 |
| Rights certainty | 5 |
| Feasibility | 5 |

A score of 80 is only an owner-review threshold. It is not a view forecast or a
promise of virality. Weak evidence, weak visual proof, or uncertain rights blocks
owner review even when the numeric score is high.

## Project contract

A project directory eventually contains:

```text
project.json
release-status.json
research.json
idea-score.json
owner-decision.json
claims.json
rights.json
story.json
proof-receipt.json
voice-lock.json
render-manifest.json
audio-qa.json
video-qa.json
owner-signoff.json
studio-receipt.json
publication-receipt.json
```

`templates/` contains blank, topic-neutral starter shapes. It is not an active
slate. Do not put private Drive links, tokens, raw voice, plates, or source media
in these manifests. Store a redacted source ID and a local/private receipt hash.

A redacted Studio observation can be checked with `analytics-check`. It stores
format and calendar age so Shorts and long-form results are not mixed. It must not
contain viewer-level rows, private links, or credentials.

## External-tool intake rule

Before adding a GitHub or Internet dependency, record its purpose, exact release or
commit, license, hash, runtime cost, and removal plan. Code may be imported after
review. Unlicensed footage, music, voices, thumbnails, or “free download” assets
are not automatically production-safe. Large/private media stays outside Git and
is referenced by a hash and approved private handoff.
