"""Durable handoff to the active agent's tools; never impersonates another agent.

No tokens, no paid API, no polling worker, no approval fabrication. A pending
task is work for an equipped operator/agent -- not a request for routine user
approval.

## Why this exists

This coordinator refuses to run a stage without a real worker and a real
reviewer (`pipeline.tick` blocks with `worker/reviewer runtime not configured`).
That refusal is correct: an unattended stub must never be allowed to approve
production. But it also meant a queued job could never move, because nothing
in this sandbox was configured as the worker.

The session transport fixes that honestly. Instead of a subprocess, the worker
command is a *named role* (`arena-session-worker`). `exchange()` writes the
task into the job state and raises `Pending`; `pipeline.tick` records it and
returns `awaiting_worker`. An equipped agent then submits a real result with
its own identity. Nothing about validation loosens: the submitted result goes
through the exact same `validate()` + independent-review path as a subprocess
worker would.

## What it deliberately cannot do

- `submit()` has no "advance" or "approve" shortcut. It only records a result.
- The reviewer identity must differ from the worker identity, and must declare
  `independent_context: true`. The same executor cannot approve its own work.
- The request is hash-bound; a tampered request makes the submission stale.
- A submission cannot be overwritten, so a failed step cannot be retried by
  quietly editing history.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

COMMANDS = {
    'arena-session-worker': 'worker',
    'arena-session-reviewer': 'reviewer',
}


class Pending(Exception):
    """Raised when the work must be done by an equipped agent, not a subprocess."""

    def __init__(self, task):
        super().__init__(task.get('role', 'pending'))
        self.task = task


def _submission_path(response):
    response = Path(response)
    return response.with_suffix('.submission.json')


def exchange(command, request, response):
    """Consume an agent submission, or raise Pending to ask for one."""
    from accounts_studio.pipeline import save
    request = Path(request)
    response = Path(response)
    task = {
        'role': COMMANDS[command],
        'request': str(request),
        'response': str(response),
        'request_sha256': hashlib.sha256(request.read_bytes()).hexdigest(),
    }
    envelope = _submission_path(response)
    if not envelope.exists():
        raise Pending(task)
    data = json.loads(envelope.read_text(encoding='utf-8'))
    if data.get('request_sha256') != task['request_sha256']:
        raise ValueError('stale session submission')
    identity = data.get('executor', {})
    if not identity.get('id') or not identity.get('capabilities'):
        raise ValueError('executor identity and actual capabilities required')
    if task['role'] == 'reviewer':
        worker_envelope = response.with_name('result.submission.json')
        if not worker_envelope.is_file():
            raise ValueError('reviewer cannot run before a worker result exists')
        worker = json.loads(worker_envelope.read_text(encoding='utf-8'))['executor']
        if identity['id'] == worker['id']:
            raise ValueError('same executor cannot independently approve its own work')
        if identity.get('independent_context') is not True:
            raise ValueError('review must explicitly identify independent context')
    save(response, data['result'])
    return data['result']


def step(job):
    """Advance one stage, routing work through the session when needed."""
    from accounts_studio.pipeline import CONFIG, tick
    job = Path(job)
    state = json.loads((job / 'state.json').read_text(encoding='utf-8'))
    stage = CONFIG['stages'][state['stage']]
    if stage == 'delivery' and state['status'] in (
            'queued', 'blocked', 'awaiting_connector'):
        from accounts_studio.connector_delivery import prepare
        prepare(job)
        return 'awaiting_connector'
    values = {CONFIG['worker_command_env']: 'arena-session-worker',
              CONFIG['reviewer_command_env']: 'arena-session-reviewer'}
    previous = {key: os.environ.get(key) for key in values}
    try:
        os.environ.update(values)
        return tick(Path(job))
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def submit(job, result, executor, capabilities, independent_context=False):
    """Record a real result for the pending task. Never advances or approves."""
    import fcntl
    from accounts_studio.pipeline import save, owned
    job = Path(job).resolve()
    if not capabilities:
        raise ValueError('an executor must declare what it actually did')
    with (job / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = json.loads((job / 'state.json').read_text(encoding='utf-8'))
        task = state.get('pending_task')
        if not task:
            raise ValueError('no pending session task')
        request = owned(job, task['request'])
        response = owned(job, task['response'])
        if hashlib.sha256(request.read_bytes()).hexdigest() != task['request_sha256']:
            raise ValueError('pending request changed')
        envelope = _submission_path(response)
        if envelope.exists():
            raise ValueError('submission already exists; process it before retry')
        save(envelope, {
            'request_sha256': task['request_sha256'],
            'executor': {'id': executor,
                         'capabilities': list(capabilities),
                         'independent_context': bool(independent_context)},
            'result': result,
        })


def attach(job):
    """Move an unstarted blocked legacy job onto session transport, keeping history."""
    import fcntl
    from accounts_studio.pipeline import ROOT, NOW, save
    job = Path(job).resolve()
    with (job / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = json.loads((job / 'state.json').read_text(encoding='utf-8'))
        # Two legitimate entry points: a blocked job created before the brief
        # existed, and a queued job that has never run a stage. Anything that
        # has already produced output must not be re-briefed through attach.
        unstarted = state['stage'] == 0 and not state.get('outputs')
        if not unstarted:
            raise ValueError('attach is only for unstarted jobs')
        if state['status'] not in ('blocked', 'queued'):
            raise ValueError('attach is only for unstarted blocked or queued jobs')
        if state.get('creative_brief_sha256'):
            raise ValueError('job is already bound to a creative brief')
        if state['account'] != 'soc_01':
            raise ValueError('no binding brief for this account')
        brief_path = ROOT / 'accounts_studio/creative_brief.json'
        if not brief_path.is_file():
            raise ValueError('accounts_studio/creative_brief.json is missing')
        content = brief_path.read_bytes()
        if state.get('creative_brief_sha256'):
            from accounts_studio.lifecycle import validate_upstream
            validate_upstream(job, state)
        else:
            (job / 'creative_brief.json').write_bytes(content)
            state['creative_brief_sha256'] = hashlib.sha256(content).hexdigest()
        state['status'] = 'queued'
        state['blocker'] = None
        state.setdefault('history', []).append({
            'at': NOW().isoformat(),
            'outcome': 'session_transport_attached',
            'note': 'Existing user-authorized scope; no creative or reviewer '
                    'approval implied',
        })
        save(job / 'state.json', state)


def main():
    parser = argparse.ArgumentParser(description='Session transport for accounts_studio')
    sub = parser.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('step', help='advance one stage (or park a pending task)')
    a.add_argument('job')
    a = sub.add_parser('attach', help='put an unstarted blocked job on session transport')
    a.add_argument('job')
    a = sub.add_parser('submit', help='record a real result for the pending task')
    a.add_argument('job')
    a.add_argument('--result', required=True)
    a.add_argument('--executor', required=True)
    a.add_argument('--capability', action='append', required=True)
    a.add_argument('--independent-context', action='store_true')
    args = parser.parse_args()

    if args.cmd == 'attach':
        attach(args.job)
        return 0
    if args.cmd == 'submit':
        submit(args.job, json.loads(Path(args.result).read_text(encoding='utf-8')),
               args.executor, args.capability, args.independent_context)
        return 0
    status = step(args.job)
    state = json.loads((Path(args.job) / 'state.json').read_text(encoding='utf-8'))
    print(json.dumps({'status': status, 'task': state.get('pending_task')}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
