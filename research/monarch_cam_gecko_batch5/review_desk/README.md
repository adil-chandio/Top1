# V6 native-speed review desk

Run from repository root:

```sh
python research/monarch_cam_gecko_batch5/review_desk/server.py --port 8765
```

Open the live preview. The server binds0.0.0.0 and uses same-origin relative media URLs. The ignored runtime V6 MP4 must already exist with the exact expected SHA-256; startup refuses a missing/mismatched candidate. This is a local review tool, not a deployed production service. No added authentication: keep the sandbox preview link within the review team, and do not deploy this unauthenticated server publicly.

## Workflow
1. Play the entire66second film at normal speed with audio; use headphones for detailed seam/mix checks.
2. Use timestamp buttons to revisit named terms, critical negation, narration seam, continuity and recap.
3. Record actual observations, not assumptions from captions or ASR. All checks initially unreviewed. Seeking/playing does not automatically change an observation.
4. Export JSON notes. Notes are stored only in browser localStorage (if available); no notes/identity are sent to this server. A downloaded JSON is not automatically ingested into project state.
5. Return the exported observations for targeted corrections and QC reconciliation. Favorable observations alone never authorize publication or clear the separate specialist anatomy hold.

The desk provides no approval API. Every export explicitly retains final_signoff=false, project_holds_cleared=false, publication_authorized=false. Reviewer name is optional. Do not treat observations as authenticated reviewer signatures.

## Serving and tests
Only `/`, `/film.mp4`, `/credits.txt` are served, not repository paths. Single byte ranges and HEAD are supported so the player can seek without downloading the full MP4 first. Unsupported/multiple/unsatisfiable ranges return416. No writes, uploads, analytics, CDNs or connector credentials.

```sh
python -m unittest discover -s research/monarch_cam_gecko_batch5/review_desk -p 'test*.py'
node research/monarch_cam_gecko_batch5/review_desk/test_frontend.cjs
```

Executed:6HTTP/range/candidate tests passed; frontend dependency-free DOM harness passed (8review fields, seek does not mark review, draft/export/reset, hold invariants); inline JavaScript syntax check passed. Preview starts listening on0.0.0.0:8765 with no platform warnings. **No native browser/media playback or actual listening test performed by the agent.** The DOM harness is not evidence that native playback has been watched/heard.

## Current boundary
No new film version generated. V6 remains the exact current review candidate. Independent ASR confusions are unverified, not narration defects. Exact Tokay anatomy/biological rig, actual pronunciation/prosody/seam/mix listening and whole-native-AV craft review remain unresolved. Autonomous technical checks cannot honestly replace these perceptual/specialist reviews; repeated exports or generic toe renders are not next-step evidence.
