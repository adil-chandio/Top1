# Two-account production system — A se Z tak poora structure

Ye document batata hai ke **soc_01 (Account 1 — PEHRA dark cinema)** aur **soc_02 (Account 2 — One-Man Cinema Lab)** ke liye poora workflow system kaise kaam karta hai: kaun, kya, kab, kis tarah, kis order mein, aur kya evidence chahiye.

Legend: **✅ built** = code maujood hai aur test pass. **⏳ planned** = design tay hai, implementation baqi.

---

## A — Account (kaun sa account)

Do accounts, ek waqt mein **sirf ek active**:

| ID | Naam | Content | Reference |
|---|---|---|---|
| `soc_01` | Account 1 — PEHRA dark cinema | Dark 3D cinema, Urdu true-twist, masked cinema | `production/account1_ep01/EP01_PEHRA_PRODUCTION_BIBLE.md` |
| `soc_02` | Account 2 — One-Man Cinema Lab | Paired BTS breakdown — video asal mein kaise bani | — |

- `config.json` → `active_account: "soc_01"`.
- `soc_02` ka job `paused_other_account` return karta hai — chalta nahi.
- Switch **sirf** user ke explicit bolne par. Delivery ya QC pass se automatic switch **nahi**. ✅

---

## B — Brief (scope)

Job banate waqt brief likha jata hai. Ye **hard scope** hai — worker us se bahar nahi ja sakta.

Misal:
```
python -m accounts_studio.pipeline enqueue \
  --account soc_01 \
  --brief "PEHRA 15s preview: 1080x1920, 30fps, 450 frames, zero still-image plates; no full-film authorization"
```

- Full film, publishing, paid spend — brief mein explicitly allowed na ho to **mana**.
- Har stage par worker ko yahi brief milta hai (`request.json → job.brief`). ✅

---

## C — Config (settings)

`accounts_studio/config.json` — koi credential nahi, sirf policy:

| Key | Value | Matlab |
|---|---|---|
| `max_attempts` | 3 | Har stage max 3 koshish, phir blocked |
| `worker_timeout_seconds` | 1800 | Ek worker call max 30 min |
| `research_max_age_hours` | 72 | Research 72h se purani ho to reject |
| `paid_spend_allowed` | false | Koi purchase nahi |
| `publishing_allowed` | false | Koi upload-to-platform nahi |
| `account_switch_requires_user_approval` | true | Automatic switch band |

✅

---

## D — Doctor (readiness check)

Production se **pehle**:

```
python -m accounts_studio.pipeline doctor
```

8 checks, sab true hone par `ready: true`:

1. `worker` — `ACCOUNTS_WORKER_COMMAND` set hai?
2. `reviewer` — `ACCOUNTS_REVIEWER_COMMAND` set hai?
3. `drive_credentials` — `ACCOUNTS_DRIVE_CREDENTIALS_FILE` set hai?
4. `drive_folder` — `ACCOUNTS_DRIVE_FOLDER_ID` set hai?
5. `credentials_file_exists` — file asal mein maujood hai?
6. `ffmpeg` — PATH par hai?
7. `worker_executable` — command ka binary milta hai?
8. `reviewer_executable` — command ka binary milta hai?

Aaj ka sach: **sab false** — worker/reviewer runtime aur unattended Drive credentials abhi configure nahi. ✅ (fail-closed sahi kaam kar raha hai)

---

## E — Enqueue (job banao)

```
python -m accounts_studio.pipeline enqueue --account soc_01 --brief "..."
```

- Folder banta hai: `accounts_studio/runtime/soc_01-<12 hex>/`
- `state.json`: `status=queued`, `stage=0`, `attempts={}`, `history=[]`, `outputs={}`
- Ek account ka ek active job. ✅

---

## F — Har stage ka common rule (FRESH RESEARCH)

**Har stage par research lazmi** — sirf pehle stage par nahi:

```json
"research": {
  "checked_at": "2026-11-16T10:00:00+00:00",
  "question": "Is stage ka specific sawal",
  "decision": "Evidence ne kya badla",
  "sources": [{"url": "https://...", "finding": "kya dekha + limitation"}]
}
```

Reject hota hai agar:
- `checked_at` timezone-less ho
- 72h se purani ya future-dated ho
- `question` ya `decision` khaali ho
- koi source `https://` na ho ya `finding` khaali ho

**Rule:** research ka check date ≠ source ki publication date. Purana paper aaj check karna "naya paper" nahi. ✅

---

## G — Gates (craft evidence)

Stage ke hisaab se departments lazmi hain (`craft.py`):

| Stage | Departments |
|---|---|
| `script` | story_design, edit_sound_blueprint |
| `feasibility` | art_direction, integrated_motion_test, asset_provenance |
| `production` | editing, animation, motion_design, typography, compositing, sound_design, music, mix, finishing |
| `qc` | picture_only_review, audio_only_review, combined_review, reference_comparison, delivery_integrity |

Har department ke liye:

```json
"animation": {
  "status": "pass",
  "observations": "asli specific finding, adjective nahi",
  "rationale": "ye choice story/reference ko kaise serve karti hai",
  "evidence": ["job-relative verified artifact path"]
}
```

- `status`: sirf `pass` ya `not_applicable`.
- `not_applicable` **sirf typography** ke liye allowed — sound/compositing/finishing silently ghayab nahi ho sakte.
- Evidence path `artifacts` list mein hona chahiye aur SHA256 match karna chahiye. ✅

---

## H — Har stage ka kaam (H se R tak detail)

Neeche har stage: kaun karta hai, kya output, kya gate.

### 1. `intelligence` — market/audience research

| | |
|---|---|
| Kaun | Research worker |
| Kaam | Channel, audience, competitors, format, hook patterns — asal sources inspect |
| Output | findings + uncertainty + dated research + opportunity decision |
| Gate | `research` block + min 1 artifact (findings doc) |

### 2. `idea` — angle selection

| | |
|---|---|
| Kaun | Idea worker |
| Kaam | 3+ angles compare: demand × originality × production feasibility |
| Output | selected angle + rejected angles + reasons |
| Gate | research + artifacts |

### 3. `story` — narrative structure

| | |
|---|---|
| Kaun | Story worker |
| Kaum | Question → mechanism → stakes → payoff |
| Output | beat map, source-backed narrative |
| Gate | research + artifacts |

### 4. `script` — narration + sound blueprint

| | |
|---|---|
| Kaun | Script worker |
| Kaam | Source ledger, original narration, visual story, sound architecture |
| Output | script doc + VO plan + shot list + sound map |
| Gate | `story_design` + `edit_sound_blueprint` |

### 5. `feasibility` — sab se mushkil hissa test karo

| | |
|---|---|
| Kaun | Art direction + technical worker |
| Kaam | Representative frame design, hardest integrated sequence, asset licensing |
| Output | **combined motion + audio MP4** (silent rig diagnostic nahi) |
| Gate | `asset_rights`, `hardest_shot_test`, `actual_motion`, `reference_fidelity` **sab true** + `integrated_motion_test` evidence mein `.mp4` |

Yahan **PEHRA ka fail point** tha: lookdev frames ne "reference_fidelity" pass nahi kiya, phir bhi full render chal gaya. Naye system mein ye rukta hai.

### 6. `production` — full render + assembly

| | |
|---|---|
| Kaun | Render + finish workers |
| Kaam | Animation, motion design, typography, compositing, sound design, music, mix, finishing |
| Output | **ek final MP4** + full attribution manifest |
| Gate | 9 departments + `attribution` non-empty |

### 7. `qc` — 5 reviews

| | |
|---|---|
| Kaun | QC worker + **independent reviewer** |
| Kaam | picture-only, audio-only, combined, reference comparison, delivery integrity |
| Output | `reviewed_production_sha256` = exact final MP4 hash |
| Gate | 8 `checks` true + `defects` empty + hash match |

**Ahem:** video badli to hash badla → purana QC invalid. Re-review lazmi.

### 8. `packaging` — title/thumbnail

| | |
|---|---|
| Kaun | Packaging worker |
| Kaam | Current title/thumbnail references research, original execution |
| Output | title, thumbnail, description |
| Gate | `promise_matches_content: true` |

### 9. `delivery` — Drive upload

| | |
|---|---|
| Kaun | `drive.py` (unattended) |
| Kaam | Full decode → post-QC hash check → dedupe → upload |
| Output | `delivery.json` receipt |
| Gate | MD5 + size match, public sharing **off** |

---

## I — Isolation (3-channel system se alag)

| Cheez | 3-channel | Ye system |
|---|---|---|
| Package | `studio/` | `accounts_studio/` |
| Branch | `arena/2a8ad29e-top1` | `arena/944c619c-top1` |
| Worker env | `STUDIO_WORKER_COMMAND` | `ACCOUNTS_WORKER_COMMAND` |
| Reviewer env | `STUDIO_REVIEWER_COMMAND` | `ACCOUNTS_REVIEWER_COMMAND` |
| R&D env | `STUDIO_RD_COMMAND` | `ACCOUNTS_RD_COMMAND` |
| Drive creds | `STUDIO_DRIVE_CREDENTIALS_FILE` | `ACCOUNTS_DRIVE_CREDENTIALS_FILE` |
| Drive folder | `STUDIO_DRIVE_FOLDER_ID` | `ACCOUNTS_DRIVE_FOLDER_ID` |
| State dir | `STUDIO_STATE_DIR` | `ACCOUNTS_STATE_DIR` |
| Drive key | `studio_job` | `accounts_job` |
| Workflow | `studio-coordinator.yml` | `accounts-studio-verify.yml` |
| Concurrency | `studio-<ref>` | `accounts-studio-<ref>` |

Zero imports, zero shared state, zero shared files. ✅

---

## J — Job state machine

```
queued
  │
  ├─ tick() ─► stage ka worker call
  │              │
  │              ├─ validate() fail ─► attempt++ ─► queued (max 3)
  │              │                                   └─ 3 par ─► blocked
  │              │
  │              ├─ reviewer reject ─► attempt++ ─► queued / blocked
  │              │
  │              └─ reviewer approve ─► stage++ ─► queued
  │
  ├─ stage == 9 ─► delivery ─► delivered
  │
  └─ account != active_account ─► paused_other_account
```

State file: `runtime/soc_01-<hex>/state.json`
Lock file: `runtime/soc_01-<hex>/lock` (fcntl — do processes ek job par nahi chal sakte) ✅

---

## K — Keep-going (retry + R&D)

Attempt fail hone par:

1. `blocker` mein bounded reason (400 chars) save.
2. `history` mein rejected entry.
3. Attempt 2+ par `ACCOUNTS_RD_COMMAND` set ho to **R&D hook** chalta hai.

R&D ka contract (`remediation.py`):
- `problem` + `acceptance_test` lazmi
- 1–3 candidates
- **exactly 1 selected**
- selected candidate mein: `source_url`, `decision_reason`, `version`, `license_review`, `security_review`, `compatibility`, `test_evidence`, `comparison`, `rollback`, `test_passed: true`

R&D **guidance** hai — khud code execute nahi karta, approval nahi deta. Production phir independently apply + validate karta hai. ✅

3 attempts ke baad `blocked` — infinite loop nahi.

Manual resume:
```
python -m accounts_studio.pipeline resume soc_01-<hex>
```
(attempts reset + queued)

---

## L — Licence & rights (har asset, har file)

- Licence check **per asset** — repo ki code licence kaafi nahi.
- `ASSET_CREDITS.md` deliverable ke saath jata hai.
- Attribution manifest production stage par lazmi.
- Reference video ki music/SFX **rip nahi**.
- Public domain (CC0) / permissive (MIT) preferred; pinned commit + SHA256 verify.

PEHRA ka existing pattern: `production/account1_ep01/fetch_assets.py` — pinned URL + byte-size + hash verify. ✅

---

## M — Media pipeline (picture)

**PEHRA ka maujooda path (✅):**

```
fetch_assets.py        → pinned CC0/MIT assets + manifest.json
        ↓
render_scene.py        → Blender 4.2.15 Cycles CPU, 1080×1920, 30fps
  (--shot S1..S6)         AzX Medium High Contrast, OIDN denoise,
                          motion blur, DOF, animated volume fog
        ↓
frames/f_000001..450   → 6 shot ranges, ek shared frame sequence
        ↓
assemble_preview.py    → grade, captions, grain, vignette, fades
        ↓
PEHRA_15s_PREVIEW_1080x1920.mp4
```

**Naya accounts pattern (⏳ planned):**

```
accounts_render.yml    → 4 shards × ~N frames (bpy, 40 min timeout)
        ↓
accounts_finish.yml    → mix + composite + encode + decode check
        ↓
deliverables/accounts-soc_01/
```

Fayda: render aur assembly **alag** — ek fail ho to doosra dobara nahi chalta.

---

## N — Narration & audio

**PEHRA (✅):**
- `vo/beat_01.wav … beat_04.wav` — voice-00, 24kHz mono 16-bit
- `build_audio_15s.py` — 48kHz stereo, 720,000 samples
- Drone, wind, impacts, boots, rifle, ticks, riser, padlock, gate groan, whoosh, marble slam, final pulse
- VO RMS 0.16 + sidechain duck
- `loudnorm=I=-14.0:TP=-1.0:LRA=9.0`, AAC 256k, `-t 15.000 -movflags +faststart`

**Naya system (⏳):**
- Narration = generated VO (voice-XX) ya licensed recording
- Music/field = CC0 pinned + hash verified
- Mix: `sidechaincompress` duck under voice
- **Listening review lazmi** — waveform/transcript se "sun liya" claim nahi

---

## O — Output & encode

Targets (PEHRA jaisa hi bar):

| Spec | Value |
|---|---|
| Resolution | 1080×1920 (9:16) |
| FPS | 30 |
| Duration | 15.000s (ya jitna brief) |
| Frames | 450 (15 × 30) |
| Video | H.264 High, yuv420p, CRF 17, BT.709 |
| Audio | AAC 256k, 48kHz, stereo |
| Faststart | `+faststart` |
| Decode check | `ffmpeg -xerror -f null -` |

QC JSON mein `ffprobe` ka pura output save hota hai. ✅

---

## P — Packaging (title/thumbnail)

- Title/thumbnail current references research ke saath
- Original execution — copy nahi
- `promise_matches_content: true` lazmi — video jo dikhata hai wahi promise

---

## Q — QC (5 reviews)

| Review | Kya dekhta hai |
|---|---|
| `picture_only_review` | Sirf picture — composition, lighting, motion, continuity |
| `audio_only_review` | Sirf audio — intelligibility, levels, harshness, sync |
| `combined_review` | Picture + audio saath — emotional impact |
| `reference_comparison` | Reference ke against — kahan kam hai |
| `delivery_integrity` | Hash, size, decode, metadata |

Plus `checks` (8): claims, rights, anatomy_or_continuity, motion, audio, export, brief_match, visual_review — sab true.
Plus `defects: []` — koi unresolved defect nahi.
Plus `reviewed_production_sha256` — exact MP4 hash. ✅

---

## R — Review (independent reviewer)

Reviewer worker ke output ko **dekh kar / sun kar** approve karta hai:

```json
{
  "approved": true,
  "inspected_artifacts": ["<exact sha256 of each artifact>"],
  "findings": "specific observations aur limitations"
}
```

Reject hota hai agar:
- `approved` true nahi
- `inspected_artifacts` khaali
- `findings` khaali
- artifact hashes worker ke hashes se match nahi

**Ahem:** different command path = independent nahi. Asal mein alag runtime/context chahiye. ✅

---

## S — Stages ka order (S = sequence)

```
intelligence → idea → story → script → feasibility
     → production → qc → packaging → delivery
```

Ek stage approve hone par hi agla khulta hai. Stage skip nahi hota. ✅

---

## T — Testing

```
python -m unittest discover -s accounts_studio/tests -v
```

**24 tests** (✅ sab pass):

| Test file | Kya cover karta hai |
|---|---|
| `test_pipeline.py` (12) | other account paused, fresh research, stale research reject, path escape, mutated artifact, quality fail, no runtime blocks, independent review required, retry budget, stage advance, wrong review hash |
| `test_craft.py` (12) | production contract, sound cannot be omitted, typography can be omitted, report-only feasibility rejected, missing department, unlisted evidence, changed evidence, R&D: valid/untested/shortlist/license/rollback |

Plus CI: `.github/workflows/accounts-studio-verify.yml` — push par tests + doctor. ✅

---

## U — Upload to Drive

`drive.py`:

1. Production stage ka **exact** MP4 dhundo (ek hi hona chahiye)
2. SHA256 QC-approved hash se match karo
3. **Poora decode** karo (`-xerror`)
4. `appProperties.accounts_job = <job id>` se dedupe search
5. Nahi mila → multipart upload
6. MD5 + size verify
7. `delivery.json` receipt: `file_id`, `link`, `sha256`, `bytes`, `public_sharing_enabled: false`

Credentials: `ACCOUNTS_DRIVE_CREDENTIALS_FILE` + `ACCOUNTS_DRIVE_FOLDER_ID`.
**Kabhi chat mein password/token nahi maanga jata.** ✅

---

## V — Verify (end-to-end)

Delivered ke baad check:

- `state.json → status: delivered`
- `delivery.json` maujood
- Drive link private hai (public sharing off)
- Video ka SHA256 receipt se match
- QC JSON ka `reviewed_production_sha256` = delivered file ka hash

---

## W — Workflows (GitHub Actions)

| Workflow | Trigger | Kaam | Status |
|---|---|---|---|
| `accounts-studio-verify.yml` | push `accounts_studio/**` | 24 tests + doctor | ✅ |
| `accounts-render.yml` | push `accounts_studio/render_trigger.txt` | 4 shards frames render | ⏳ |
| `accounts-finish.yml` | push `accounts_studio/finish_trigger.json` | mix + encode + decode check | ⏳ |
| `account1-ep01-preview.yml` | push `production/account1_ep01/**` | PEHRA 15s render | ✅ |

Sab workflows `arena/944c619c-top1` branch par scoped. Koi cron nahi jab tak pilot pass na ho. ✅

---

## X — eXecution (local vs cloud)

| Kaam | Kahan | Kyun |
|---|---|---|
| Coordinator, tests, doctor | Local ya CI | Halka, fast |
| Blender render | GitHub Actions (ubuntu-latest) | Sandbox mein Blender nahi |
| Assembly/encode | GitHub Actions | Sandbox mein ffmpeg nahi |
| Drive upload (unattended) | Local/worker runtime | Credentials chahiye |
| Drive upload (conversation) | Arena connector | Aapke interactive session mein |

Sandbox limits: 2 vCPU / 3.8 GiB RAM, no system ffmpeg/ffprobe/blender. ✅

---

## Y — whY (quality bar)

Ye system "flags pass" ko quality nahi maanta:

- **Adjective se pass nahi** — `premium`, `cinematic` bolne se gate pass nahi hota. Specific observation + evidence chahiye.
- **Test pass ≠ creative quality.** 24 tests green hone ka matlab video acchi hai — ye **nahi**.
- **Delivery ≠ acceptance.** Drive upload ka matlab aap ne approve kiya — ye **nahi**.
- **Self-certification band** — department apne aap ko pass nahi kar sakta, reviewer alag hai.
- **Reference se compare** — "reference se behtar" claim bina measurement nahi.

$1000/min craftsmanship **ambition** hai — guaranteed score nahi.

---

## Z — Zero-tolerance rules

1. **Zero still-image scene plates** — background/shot asli 3D render hona chahiye.
2. **Zero fake QC** — bina dekhe/sune "reviewed" nahi.
3. **Zero stale research** — 72h se purani check reject.
4. **Zero silent department** — sound/compositing/finishing ghayab nahi ho sakte.
5. **Zero paid spend** bina authorization.
6. **Zero publishing** bina authorization.
7. **Zero automatic account switch**.
8. **Zero secrets in chat** — password/token kabhi nahi.
9. **Zero infinite retry** — 3 attempts, phir blocked.
10. **Zero wrong-hash delivery** — QC hash = delivered hash.

---

## Ab kya baqi hai (build order)

| # | Kaam | Kaun | Status |
|---|---|---|---|
| 1 | `accounts_studio` coordinator + tests | ✅ done | ✅ |
| 2 | `accounts-studio-verify.yml` CI | ✅ done | ✅ |
| 3 | `accounts-render.yml` (sharded render) | ⏳ | next |
| 4 | `accounts-finish.yml` (mix + encode + QC) | ⏳ | |
| 5 | PEHRA ke liye `active_release.json` gates fill | ⏳ | |
| 6 | Render + audio scripts ko accounts_studio ke under wire karna | ⏳ | |
| 7 | Real worker/reviewer runtime configure | user/operator | |
| 8 | Drive credentials + folder configure | user/operator | |
| 9 | Full pilot end-to-end | — | |

**Sachchi baat:** step 7–8 ke baghair system autonomously video nahi banata. Wo infrastructure user ke paas hai, code ke andar forge nahi kiya ja sakta.
