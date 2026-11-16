# Two-account production coordinator (isolated system)

Ye system **3-channel studio system se bilkul alag** hai. Apna folder, apna config, apne env vars, apna state dir, apna workflow. Dono systems ek-doosre ko touch nahi karte.

## Accounts

- **soc_01 — Account 1 (PEHRA dark cinema):** Dark 3D cinema, Urdu true-twist stories, masked cinema style. Reference: `production/account1_ep01/EP01_PEHRA_PRODUCTION_BIBLE.md`.
- **soc_02 — Account 2 (One-Man Cinema Lab):** Paired BTS breakdown cut — cinema videos asal mein kaise bante hain.

Active account: **soc_01**. Doosre account par tabhi jana jab user delivered video dekh kar explicitly bole. Delivery ya QC pass ke baad automatic switch nahi.

## Isolation (3-channel system se alag)

| Cheez | 3-channel system | Ye system |
|---|---|---|
| Package | `studio/` | `accounts_studio/` |
| Branch | `arena/2a8ad29e-top1` | `arena/944c619c-top1` |
| Worker env | `STUDIO_WORKER_COMMAND` | `ACCOUNTS_WORKER_COMMAND` |
| Reviewer env | `STUDIO_REVIEWER_COMMAND` | `ACCOUNTS_REVIEWER_COMMAND` |
| R&D env | `STUDIO_RD_COMMAND` | `ACCOUNTS_RD_COMMAND` |
| Drive creds env | `STUDIO_DRIVE_CREDENTIALS_FILE` | `ACCOUNTS_DRIVE_CREDENTIALS_FILE` |
| Drive folder env | `STUDIO_DRIVE_FOLDER_ID` | `ACCOUNTS_DRIVE_FOLDER_ID` |
| State dir env | `STUDIO_STATE_DIR` | `ACCOUNTS_STATE_DIR` |
| Drive dedupe key | `studio_job` | `accounts_job` |
| Workflow | `studio-coordinator.yml` | `accounts-studio-verify.yml` |
| Concurrency group | `studio-<ref>` | `accounts-studio-<ref>` |

Koi import, koi shared state, koi shared workflow nahi. Ye system 3-channel system ki files ko na read karta hai na likhta hai.

## Stages

`intelligence → idea → story → script → feasibility → production → qc → packaging → delivery`

Har stage par fresh research (72h limit), worker artifacts SHA256-verified, reviewer independent inspection, specialist craft gates (`craft.py`), retry par bounded R&D (`remediation.py`). QC exact final MP4 hash se bind hai.

## Sachchi current state

Working coordinator implementation hai, complete autonomous creative studio deployed nahi. Real worker/reviewer executables, unattended Drive credentials aur folder configure nahi hain. `doctor` missing integrations report karega. Arena connected Drive conversation upload kar sakta hai; ye access automatically long-running Python process/GitHub Actions ko transfer nahi hota. No secrets chat mein maang kar resolve nahi karne.

## Commands

```
python -m accounts_studio.pipeline doctor
python -m accounts_studio.pipeline enqueue --account soc_01 --brief "PEHRA 15-second preview pilot; no full-film authorization"
python -m accounts_studio.pipeline run
python -m accounts_studio.pipeline status
```

Persistent service (sirf doctor + real pilot ke baad):

```
ACCOUNTS_STATE_DIR=/persistent/accounts-state python -m accounts_studio.serve
```

## Files

- `pipeline.py`: durable queue and stage execution (2 accounts).
- `config.json`: account/stage limits, no credentials.
- `WORKER_CONTRACT.md`: real worker/reviewer protocol.
- `drive.py`: unattended upload adapter (`accounts_job` dedupe key).
- `serve.py`: long-lived service, persistent storage required.
- `release_gate.py`: full-render preflight (5 creative gates).
- `tests/`: isolated contract/state-machine tests, not creative quality or live Drive integration tests.

## CI

`.github/workflows/accounts-studio-verify.yml` — push par `accounts_studio/**` change ho to safety tests + doctor chalata hai. Render trigger nahi; real worker runtime, persistent storage aur unattended Drive credentials configure hone aur complete pilot pass hone tak koi cron/render nahi.
