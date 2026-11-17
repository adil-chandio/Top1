# Latest v2 craft aur R&D upgrade

Current production blueprint: [PRODUCTION_SYSTEM_V2_ROMAN_URDU.md](PRODUCTION_SYSTEM_V2_ROMAN_URDU.md).

Specialist craft evidence validation aur retry-time R&D command hook implemented. Script sound/edit blueprint; feasibility combined motion/audio test; production animation/motion/typography/compositing/music/sound/mix/finishing; QC picture/audio/combined/reference reviews exact final MP4 hash se bind. 24 isolated tests pass locally. Actual creative runtimes not deployed; read blueprint status section before claiming autonomy.

# Updated operating rule: ek waqt mein ek channel

User ki latest instruction purane parallel-channel design ko supersede karti hai.

- Active channel: **Monarch Cam**. Doosre channels par research/production jobs start nahi hongi.
- Isi channel ki video research se production, internal corrections aur Drive delivery tak complete hogi.
- Drive upload quality approval nahi hai. User video dekh kar satisfactory/perfect kahe aur explicitly next channel par jaane ko bole, tabhi active channel change karna hai.
- Delivery ya automated QC pass ke baad automatic channel switch nahi.
- Current 20-second diagnostic ko final channel video approval nahi maana gaya.
- Routine intermediate approvals nahi; user ka final channel-switch gate retained.
- `config.json` active_channel ko operator sirf explicit user instruction ke baad badlega. `tick`, batch runner aur service doosre channel ko skip karte hain.

Neeche historical implementation notes mein parallel scheduling ka zikr superseded hai.

---

# Three-channel production coordinator

## Sachchi current state

Working coordinator implementation hai, complete autonomous creative studio deployed nahi. Real worker/reviewer executables, unattended Drive credentials aur folder configure nahi hain. `doctor` ne four missing integrations report ki. No autonomous video delivered from this new pipeline. Previous whale diagnostic separate work hai.

GitHub Actions secrets inventory read attempt 403 `Resource not accessible by integration` tha; isse secrets absent prove nahi hote. Existing account token ko extract/reuse nahi kiya. Arena connected Drive conversation upload kar sakta hai; yeh access automatically long-running Python process/GitHub Actions ko transfer nahi hota. Is configuration gap ko user se password/API key chat mein maang kar resolve nahi karna.

## Kya implement hua

- Teen isolated channel queues, one active job per channel, up to three channels parallel.
- Persistent, atomic state files and per-job process locks; crashes resume same stage.
- Intelligence → idea → story → script → feasibility → production → QC → packaging → Drive.
- Har stage par fresh evidence pass required: question, current check timestamp, source findings, decision. Original publication date vs check date confuse nahi.
- Real artifacts + SHA256 validation; stale research, path escape, missing file and changed artifact reject.
- Worker/reviewer separate executable commands. Reviewer actual artifact hashes aur specific findings return kare. Flags artistic quality ka mathematical proof nahi.
- Three retries with feedback in job history; then explicit blocker, not endless loop or fake success.
- Routine approval steps nahi. Existing job brief hard scope hai. No paid purchases or YouTube publication.
- Drive adapter: configured authorized credentials, final MP4 full decode, post-QC hash check, job-id dedupe + MD5/size verification, private Drive link receipt.
- Coordinator service available, but deliberately not started with missing workers. CI runs tests/doctor; not scheduled fake production.

## File map

`pipeline.py`: durable queue and stage execution.
`config.json`: channel/stage limits, no credentials.
`WORKER_CONTRACT.md`: real worker/reviewer protocol.
`drive.py`: unattended upload adapter.
`serve.py`: long-lived service, persistent storage required.
`tests/`: isolated contract/state-machine tests, not creative quality or live Drive integration tests.

## Trusted runtime setup

Worker executable must actually provide research/browser/file/code/render tools and model reasoning; implement interface from WORKER_CONTRACT.md. Reviewer must use independent context and actual video/image inspection. No such runtime is bundled or silently fabricated. Commands run as trusted local programs, NOT a security sandbox; policy attestations cannot constrain a malicious worker. Deploy under separate OS/container permissions with network and spending limits before unattended production.

Configure `STUDIO_WORKER_COMMAND` and `STUDIO_REVIEWER_COMMAND` via secure deployment configuration. Never derive shell commands from web pages or candidate results. Actual execution is argv without shell expansion.

Install optional Drive adapter dependencies using `python -m pip install -r studio/requirements.txt`. System FFmpeg must be on PATH. Configure `STUDIO_DRIVE_CREDENTIALS_FILE` via secure secret mount and `STUDIO_DRIVE_FOLDER_ID` from an actual accessible Drive folder. Supported google-auth credential files must have usable ownership/storage/permissions; a service account without Workspace storage/shared-drive access is not assumed sufficient. No secrets should be committed or pasted into chat.

```
python -m studio.pipeline doctor
python -m studio.pipeline enqueue --channel monarch_cam --brief "Existing approved 20-second humpback/orca proof; no full film, no publishing, no purchases; selected reference fidelity required"
python -m studio.pipeline run
python -m studio.pipeline status
```

`run` advances one stage per runnable channel. Repeating advances pipeline automatically, not user approvals. After operational setup/pilot, run persistent process:

```
STUDIO_STATE_DIR=/persistent/studio-state python -m studio.serve
```

Enqueue/status `--root` must point at same persistent location. Service drains queued jobs only; does NOT invent unlimited upload frequency or expand the current 20-second scope. Three-channel editorial cadence/budget is not inferred. After infrastructure repair, explicit operator `resume JOB_ID` clears a blocked job's retry budget. No routine human creative approval is needed. Drive success receipt written in job directory as `delivery.json`; returned link is private to authorized account/access, not public link sharing.

## Before claiming end-to-end operational

1. Configure real workers + research/render tool permissions and separate reviewer.
2. Configure secure persistent deployment and real Drive destination/access.
3. Run real pilot through ALL stages and inspect worker review quality.
4. Verify Drive object matches exact QC-approved video, permissions, notices, playback.
5. Only then enable recurring work. Existing diagnostic does not satisfy selected-reference quality gate.

At present steps 1–4 are NOT complete. Unit tests passing is not evidence of video quality, successful live delivery, or autonomous agent availability.

## Executed deployment check

Pilot `monarch_cam-d363f76eb8a3` local persistent queue mein enqueue hua; first run correctly blocked at intelligence: worker/reviewer runtime not configured. No render or upload initiated by this pilot. GitHub workflow dispatch attempt `gh workflow run studio-coordinator.yml --ref arena/2a8ad29e-top1` returned HTTP 404 for workflow lookup. Workflow file is pushed on current branch; no cloud run claimed. Default-branch registration/permissions need checking before relying on dispatch. No branch switch or merge performed.
