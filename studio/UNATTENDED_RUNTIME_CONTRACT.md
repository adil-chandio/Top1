# Unattended runtime contract

Deployment files are templates for an operator-owned persistent Linux host, NOT an activated service in Arena. No new API spending or public publishing is authorized.

## Agent integration
Existing trusted worker/reviewer programs take `--request ABS_PATH --response ABS_PATH`. Normal production uses `WORKER_CONTRACT.md`. Each must actually have research, file/execution, moving-picture and audio access. Model chat/text-only completion is not sufficient. Creator/reviewer identity and context must differ. Neither a shell wrapper nor repeating JSON flags supplies these capabilities.

For a request with `operation: capability_probe`, do no production work or network purchases. Return:

```
{
  "challenge": "exact request.challenge",
  "role": "worker or reviewer matching request.role",
  "paid_spend": false,
  "executor": {
    "id": "real stable executor identity",
    "unattended": true,
    "independent_context": true
  },
  "capabilities": {
    "research_tools": true,
    "file_tools": true,
    "execute_tools": true,
    "moving_picture": true,
    "audio_listening": true
  }
}
```

Only attest actual capabilities. This challenge establishes live command transport and records attestations, NOT independent media competence. Actual end-to-end pilot must still verify research access, picture/audio inspection, a deliberately defective sample rejected by reviewer, correction/re-review and exact-byte private Drive delivery. Existing production gates stay in force.

## Persistent host deployment

- Host repository at `/opt/top1`, on session branch `arena/2a8ad29e-top1`; do not switch/create branches automatically.
- Separate unprivileged `studio` service account; trusted agent executables installed outside writable job data. Python environment `/opt/top1/.venv`. Install reviewed `studio/requirements.txt` and actual render/agent dependencies in the host environment.
- Private persistent jobs/storage at `/var/lib/monarch-studio/jobs`, owned by service account, not Git. Migrate job state AND referenced artifacts together while coordinator is stopped; verify absolute session paths before resuming. Do not silently reset the active job or bypass pending review.
- Root/operator-provided `/etc/monarch-studio/runtime.env` holds `STUDIO_WORKER_COMMAND`, `STUDIO_REVIEWER_COMMAND`, `STUDIO_DRIVE_CREDENTIALS_FILE`, `STUDIO_DRIVE_FOLDER_ID`. Never put secret values in chat or Git. Service identity needs read permission on its credential file and existing destination folder authorization. Arena connector credentials are not exported.
- Service templates in `studio/deploy/` apply least-privilege filesystem settings and cgroup cleanup. Agent caches/output must live under the writable state directory; adjust host config deliberately if a reviewed renderer requires another path.
- Run preflight/live probe and the real media pilot first. Only then have the operator enable the timer. No automatic package installation, credential collection, billing activation or unverified agent download is performed by these files.
- `python -m studio.supervisor --check` inspects configuration; `python -m studio.runtime_probe` performs harmless live challenge when config exists. Missing config returns exit 2 without consuming production attempts.
- Supervisor stops on missing infra, bounded budget, blocked QC, pending session/connector, or final evaluation. Timer retries service execution; it does not itself fix missing capabilities or reset exhausted stage budgets. Review heartbeat/probe JSON for precise status.
- Per-command timeout kills descendant processes. Service timeout also kills its entire cgroup. Time budget is checked between stages, not a hard bound for an in-flight stage.

## Current deployment truth

This sandbox has no configured unattended AI creator/reviewer and no standalone Drive credential file. It is not a persistent managed host provisioned by these templates. No service/timer has been enabled; full automatic operation is NOT claimed. Active chat Drive uploads remain available. Newly shared video previews must be privately uploaded with links without waiting for another user request.
