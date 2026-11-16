# Studio v3 — binding execution manual

## Authority aur creative intent

`creative_brief.json` is waqt Monarch Cam ke original script ki continuous opening 20s ko define karta hai. Har naye Cam job mein immutable snapshot aur SHA256 save hota hai; worker request ke andar brief aur stage responsibility actually attach hoti hai. Brief tamper ho to continuation fails. Role names se imaginary agents create nahi hote.

Storytelling mein curiosity, animal readability, believable weight, authored editing, purposeful graphics aur sonic space chahiye. Kinetic typography optional; high-end editing, compositing aur sound work optional nahi. User-rejected captions/progress rail/weak sound ko reusable approved template nahi maana jayega. Scope: proof only, no full film/publishing/purchase.

## Single-video lifecycle

1. `enqueue` creates durable job and brief snapshot.
2. Earliest unfinished active-channel video owns queue. Blocked ya awaiting-user job ko skip karke doosra video start nahi hota.
3. `run` advances one stage; `serve` repeatedly schedules only eligible job. Shared per-channel OS lock prevents separate processes running different jobs concurrently. Job lock serializes feedback and execution.
4. At each stage: upstream artifacts unchanged → binding brief unchanged → stage task + evidence → worker → validation → independent reviewer receipt → persist accepted output.
5. Retry has bounded per-revision budget; actual attempt folders globally increasing so revisions never overwrite earlier experiments. Optional R&D guidance includes real test/rights/security/rollback contract; never auto-executes downloaded repo code.
6. Full production requires shared release gate. Delivery additionally checks exact MP4 and persisted reviewer receipts. Previous user-rejected video SHA cannot be relabelled and delivered.
7. Successful upload sets `awaiting_user_evaluation`, not accepted. Same channel cannot start another video while this waits. Other channels always paused.
8. User feedback `accept` marks accepted; does NOT switch channel. `revise`/`reject` archives delivery and downstream evidence, remembers rejected video hash, invalidates downstream reviewer receipts and schedules rework. No routine intermediate approval prompts.

## Stage routing and required craft

- intelligence: current targeted market/craft research, actual access labels.
- idea: evidence, originality, feasible visual story.
- story: central puzzle, mechanism and qualified payoff.
- script: original copy + independent editing/sound blueprint.
- feasibility: art direction, provenance and internal 4–6s combined motion/edit/compositing/audio proof.
- production: editing, animation, motion design, typography decision, compositing, sound design, music, mix, finishing.
- qc: actual picture-only, audio-only, combined, reference and integrity reviews linked to production SHA.
- packaging: truthful promise and relevant artifacts, no unauthorized publication.
- delivery: exact approved MP4 decode, Drive integrity/dedupe and link.

`roles.json` attaches owner/task/exit instructions to every stage. `WORKER_CONTRACT.md`, `craft.py`, `release_gate.py`, `guards.py` enforce report/artifact contracts. Hashes prove unchanged bytes, not artistic merit. Reference text/still access cannot be claimed as watching/listening.

## Operator commands — not user micromanagement

```
python -m studio.pipeline doctor
python -m studio.pipeline enqueue --channel monarch_cam --brief "Original full-film opening 20 seconds; binding creative brief applies"
python -m studio.pipeline run
python -m studio.pipeline status
python -m studio.pipeline feedback JOB_ID --decision reject --reason "Actual user feedback" --restart-from feasibility
python -m studio.pipeline feedback JOB_ID --decision accept --reason "User explicitly accepted delivered video"
```

Operator converts actual user feedback to CLI state; no fabricated acceptance. `resume` only repairs blocked infrastructure/jobs, cannot bypass final user evaluation. Use same persistent `--root` for all CLI calls and `STUDIO_STATE_DIR` for service. Infrastructure setup is operator work, not asking user to repeatedly approve creative stages.

## Real runtime requirements and start behaviour

`readiness.py` checks executable configuration and unattended delivery prerequisites; `serve` exits 2 with explicit missing configuration instead of starting an empty worker illusion. Real worker and separate reviewer programs must implement CLI contract with actual research, file, render and AV-inspection tools. Independent review context/capability cannot be established by command names alone. Credentials only through secure deployment, never chat/repository. Existing connected Drive can upload in active Arena conversation; its authorization is not exported to a service.

```
python -m studio.serve
```

Do not launch a supervisor and call it filmmaking when worker runtime absent. No continuously running service started in this implementation pass. Creative runtime and unattended Drive configuration still absent; no new film claimed.

## What was actually tested

50 tests cover existing research/craft/release contracts plus real child-process fixture worker/reviewer execution for one stage, brief propagation, immutable upstream evidence, channel ownership, blocked-first-job behaviour, rejection invalidation, unique attempt history, final acceptance and delivery-awaiting-user transitions. Fixture opens real bytes but is explicitly synthetic: not real market research, video generation, audiovisual listening, premium art or actual Drive integration test.

## Acceptance of the whole system

Code implementation verified != autonomous deployment verified != creative production validated. Operational acceptance still needs real equipped runtimes and end-to-end real pilot, with actual AV reference review, combined proof and accepted final result. No source document or test count can substitute that.

## Active-session alternative (new)

External daemon configuration above applies only to unattended service. Active Arena session can now use `python -m studio.session step JOB_DIRECTORY` and connected Drive delivery without exporting credentials. See `SESSION_EXECUTION_ROMAN_URDU.md` for actual operator flow, identity/review rules and live evidence. This route does not invent external agents or autonomous off-chat execution.
