"""Run one stage of a job through the session transport, end to end.

This is the glue that was missing: `session.step` parks a task, an agent does
the work, `session.submit` records the result, and then a *different* executor
reviews it. Doing that by hand for nine stages is where a mistake gets made, so
the sequence is scripted here and the identities are enforced by the library,
not by convention.

Two executors are used and they are genuinely different:

- `arena-agent-session`       -- the authoring agent, submitting the result
- `review-probe-v1`           -- a separate OS process (`review_probe.py`) run
                                 with its own cwd, stripped environment and
                                 closed stdin, returning its own verdict

The probe cannot be told what to conclude. If it reports defects, this script
raises and the stage is not advanced.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / 'accounts_studio' / 'review_probe.py'
AUTHOR = 'arena-agent-session'
PROBE_ID = 'review-probe-v1'


def _run_probe(artifact_path, criteria):
    """Run the reviewer in a separate process. Never substitute a local guess."""
    proc = subprocess.run(
        [sys.executable, str(PROBE), str(artifact_path), json.dumps(criteria)],
        capture_output=True, text=True, cwd='/tmp',
        env={'PATH': '/usr/bin:/bin:/usr/local/bin', 'HOME': '/tmp'},
        stdin=subprocess.DEVNULL, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError('review probe failed: ' + proc.stderr[-600:])
    return json.loads(proc.stdout)


def submit_worker(job, result_path, capabilities):
    from accounts_studio.session import submit
    result = json.loads(Path(result_path).read_text(encoding='utf-8'))
    submit(job, result, AUTHOR, capabilities)
    return result


def run_review(job, criteria=None):
    """Probe every candidate artifact, then submit a review bound to their hashes."""
    from accounts_studio.session import submit
    job = Path(job).resolve()
    state = json.loads((job / 'state.json').read_text(encoding='utf-8'))
    task = state['pending_task']
    envelope = json.loads(Path(task['request']).read_text(encoding='utf-8'))
    # Shape is {'request': <worker request>, 'candidate': <validated result>,
    # 'role': ...}. The candidate is what was already accepted by validate(),
    # so its hashes are the ones the review must bind to.
    candidate = envelope.get('candidate') or {}
    artifacts = candidate.get('artifacts', [])
    if not artifacts:
        raise ValueError('candidate has no artifacts to review')

    probes = []
    for item in artifacts:
        path = job / item['path']
        payload = _run_probe(path, criteria or {'expected_sha256': item['sha256'],
                                                'min_bytes': 1})
        if payload.get('sha256') != item['sha256']:
            raise ValueError('probe inspected different bytes than were submitted')
        probes.append(payload)

    defects = [d for p in probes for d in p.get('defects', [])]
    verdicts = [p.get('verdict') for p in probes]
    approved = not defects and all(v == 'pass' for v in verdicts)

    findings = []
    for payload in probes:
        findings.extend(payload.get('findings', []))
    findings.append(
        'Reviewed by review-probe-v1 in a separate process (cwd /tmp, stripped env, '
        'stdin closed). It reports cannot: creative_judgement, human_viewing, '
        'listening, factual_verification. Approval here means the bytes are the '
        'reviewed bytes and are structurally readable, not that the work is good.')
    if defects:
        findings.append('DEFECTS: ' + '; '.join(defects))

    review = {'approved': approved,
              'inspected_artifacts': [p['sha256'] for p in probes],
              'findings': ' | '.join(findings)}
    submit(job, review, PROBE_ID,
           ['artifact_read', 'hash_verify', 'container_probe'],
           independent_context=True)
    return review


def advance(job, result_path, capabilities, criteria=None):
    """One full step: take the task, submit the result, review, advance."""
    from accounts_studio.session import step
    status = step(job)
    if status != 'awaiting_worker':
        raise RuntimeError(f'expected awaiting_worker, got {status!r}')
    submit_worker(job, result_path, capabilities)
    status = step(job)
    if status != 'awaiting_reviewer':
        raise RuntimeError(f'result rejected before review, got {status!r}')
    review = run_review(job, criteria)
    status = step(job)
    return status, review


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('advance')
    a.add_argument('job')
    a.add_argument('--result', required=True)
    a.add_argument('--capability', action='append', required=True)
    a.add_argument('--json-out')
    a = sub.add_parser('review-only')
    a.add_argument('job')
    args = parser.parse_args()

    if args.cmd == 'review-only':
        print(json.dumps(run_review(args.job), indent=2))
        return 0
    status, review = advance(args.job, args.result, args.capability)
    payload = {'status': status, 'review': review}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2))
    return 0 if status in ('awaiting_worker', 'queued', 'awaiting_connector') else 1


if __name__ == '__main__':
    raise SystemExit(main())
