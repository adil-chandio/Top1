"""Bounded unattended coordinator loop; never substitutes polling for an agent.
Run --check before deployment. Runtime executables are trusted operator config.
"""
import argparse
import json
import os
import shlex
import shutil
import time
from pathlib import Path
from studio.pipeline import CONFIG, ROOT, NOW, save, tick
from studio.session import COMMANDS
from studio.lifecycle import select_job


def preflight(environ=None):
    env = os.environ if environ is None else environ
    checks = {}
    commands = []
    for role in ('worker', 'reviewer'):
        raw = env.get(CONFIG[role + '_command_env'], '')
        try:
            argv = shlex.split(raw)
        except ValueError:
            argv = []
        checks[role + '_executable'] = bool(argv and shutil.which(argv[0]))
        checks[role + '_unattended_transport'] = bool(argv and argv[0] not in COMMANDS)
        commands.append(argv)
    checks['separate_commands'] = bool(all(commands) and commands[0] != commands[1])
    credentials = env.get('STUDIO_DRIVE_CREDENTIALS_FILE', '')
    checks['drive_credentials_file'] = bool(credentials and Path(credentials).is_file())
    checks['drive_folder'] = bool(env.get('STUDIO_DRIVE_FOLDER_ID'))
    return {'ready_for_attempt': all(checks.values()), 'checks': checks,
            'limits': 'Configuration only, not proof of model access, independent media review, valid Drive authorization or free execution.'}


def run(base, *, max_ticks=30, max_seconds=3600, interval=10):
    if not 1 <= max_ticks <= 100 or not 1 <= max_seconds <= 21600 or not 1 <= interval <= 300:
        raise ValueError('bounded tick/time/interval limits required')
    base = Path(base).resolve()
    base.mkdir(parents=True, exist_ok=True)
    import fcntl
    with (base / 'supervisor.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'already_running'}
        report = preflight()
        status_file = base / 'supervisor_status.json'
        def record(status, ticks=0, **extra):
            receipt = {'status': status, 'heartbeat_at': NOW().isoformat(),
                       'ticks': ticks, 'preflight': report, **extra}
            save(status_file, receipt)
            return receipt
        if not report['ready_for_attempt']:
            return record('blocked_infrastructure')
        started = time.monotonic()
        for n in range(max_ticks):
            if time.monotonic() - started >= max_seconds:
                return record('time_budget_reached', n)
            job = select_job(base, CONFIG['active_channel'])
            if job is None:
                return record('no_runnable_job', n)
            record('executing', n, job=job.name)
            outcome = tick(job)
            record(outcome, n + 1, job=job.name)
            if outcome not in ('queued', 'locked', 'channel_locked'):
                # Pending session/connector tasks cannot be solved by blind polling.
                return record(outcome, n + 1, job=job.name)
            if n + 1 < max_ticks:
                time.sleep(interval)
        return record('tick_budget_reached', max_ticks)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=ROOT / 'studio/runtime')
    p.add_argument('--check', action='store_true')
    p.add_argument('--max-ticks', type=int, default=30)
    p.add_argument('--max-seconds', type=int, default=3600)
    p.add_argument('--interval', type=int, default=10)
    args = p.parse_args()
    result = preflight() if args.check else run(args.root, max_ticks=args.max_ticks,
                                                max_seconds=args.max_seconds, interval=args.interval)
    print(json.dumps(result, indent=2))
    return 2 if result.get('status') == 'blocked_infrastructure' or (args.check and not result['ready_for_attempt']) else 0

if __name__ == '__main__':
    raise SystemExit(main())
