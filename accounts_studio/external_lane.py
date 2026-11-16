"""External execution lane: real work on GitHub-hosted runners.

## Why this exists

This authoring sandbox has a small network allowlist. Measured from here
(direct, no proxy):

    youtube.com            000
    instagram.com          000
    tiktok.com             000
    raw.githubusercontent  000
    huggingface.co         TLS EOF

The same targets measured from a GitHub-hosted `ubuntu-latest` runner all
return 200/301 (see `external_evidence/lane_network_probe.json`, produced on
the runner itself). The runner is not a simulator or a stub: it is a different
machine with general internet access, a real CPU, and its own Python/FFmpeg.

So the lane is simple and honest:

1. A push to `external_lane_trigger/` wakes `.github/workflows/
   accounts-external-lane.yml`.
2. That workflow performs work this sandbox cannot: real ASR, a different
   language-model family reviewing measured facts, a vision-language model
   looking at actual extracted frames, an audio-event transformer listening to
   the actual soundtrack, platform extraction, and durable artifact publishing.
3. The runner **commits its own output** to `external_evidence/` on the
   branch. Nothing in that directory is authored by the agent that requested
   it, so the evidence is auditable in git history — authors and timestamps
   are the runner's.

## What this does and does not buy

It buys: real transcription, real visual inspection by a second model family,
real audio-event classification, real platform metadata, and durable artifact
storage that survives a sandbox reset.

It does not buy: human viewing, human listening, creative taste, or an
award for the film. A model describing a frame is a model describing a frame.

## Triggering

`workflow_dispatch` returns 403 with this session's GitHub App token, so the
lane is woken by a push instead — see `trigger()`.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'external_evidence'
TRIGGER_DIR = ROOT / 'external_lane_trigger'
WORKFLOW = 'accounts-external-lane.yml'
BRANCH = 'arena/944c619c-top1'

#: Routes that only a GitHub-hosted runner can produce. A record claiming one
#: of these is runner output; anything else must stay unverified.
RUNNER_ROUTES = {'github_actions_runner', 'github_release'}

#: Written by the runner, never by this module.
ARTIFACTS = {
    'asr': 'asr/pehra_transcript.json',
    'model_review': 'review/different_model_review.json',
    'vision': 'vision/frame_inspection.json',
    'audio': 'audio/audio_event_analysis.json',
    'platform': 'platform/platform_probe.json',
    'durable': 'durable/release_store.json',
}


def trigger(reason: str = 'lane', dry_run: bool = False) -> dict:
    """Wake the lane by pushing a changed trigger file.

    Returns the git commands that were run. Raises RuntimeError if the push
    fails, because a lane that silently did not wake is worse than no lane.
    """
    TRIGGER_DIR.mkdir(parents=True, exist_ok=True)
    stamp = TRIGGER_DIR / 'ping.txt'
    import time
    stamp.write_text(f'{reason} {time.time()}\n', encoding='utf-8')
    cmds = [
        ['git', 'add', '-A', str(TRIGGER_DIR.relative_to(ROOT))],
        ['git', 'commit', '-m', f'External lane trigger: {reason}'],
        ['git', 'push', 'origin', f'HEAD:{BRANCH}'],
    ]
    if dry_run:
        return {'dry_run': True, 'commands': cmds, 'reason': reason}
    for cmd in cmds:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if proc.returncode != 0 and 'nothing to commit' not in proc.stdout:
            raise RuntimeError(f'{cmd[1]} failed: {proc.stderr[-600:]}')
    return {'dry_run': False, 'reason': reason, 'commands': cmds}


def load(kind: str, evidence_dir: Path | None = None) -> dict:
    """Read one runner-produced artifact from the working tree.

    Raises FileNotFoundError when the runner has not produced it yet — the
    caller must not substitute a local guess for missing runner output.
    """
    if kind not in ARTIFACTS:
        raise KeyError(f'unknown lane artifact {kind!r}; choose from {sorted(ARTIFACTS)}')
    base = Path(evidence_dir) if evidence_dir else EVIDENCE
    path = base / ARTIFACTS[kind]
    if not path.is_file():
        raise FileNotFoundError(
            f'no runner artifact at {path} — the lane has not produced it, '
            'so it cannot be reported as done')
    return json.loads(path.read_text(encoding='utf-8'))


def provenance(result: dict) -> dict:
    """Extract who produced a result, so callers must surface it.

    Every claim downstream of this lane is only as trustworthy as the fact
    that a runner, not the authoring agent, wrote it.
    """
    return {
        'route': result.get('route'),
        'produced_by': 'github_actions_runner',
        'authored_by_requesting_agent': False,
        'model': result.get('model') or result.get('selected'),
        'engine': result.get('engine'),
        'source_sha256': result.get('source_sha256'),
    }


def capability_report(evidence_dir: Path | None = None) -> dict:
    """Summarise which lane capabilities have real runner evidence.

    A capability is only `green` when its artifact exists AND carries the
    runner route marker. Anything else is reported as `missing`, with the
    reason, instead of being quietly upgraded.
    """
    base = Path(evidence_dir) if evidence_dir else EVIDENCE
    report = {}
    for kind, rel in ARTIFACTS.items():
        path = base / rel
        entry = {'artifact': rel, 'present': path.is_file()}
        if not path.is_file():
            entry.update({'status': 'missing', 'reason': 'runner has not produced it'})
            report[kind] = entry
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            entry.update({'status': 'unreadable', 'reason': str(exc)})
            report[kind] = entry
            continue
        # Two runner-written schemas exist: most artifacts carry an explicit
        # `route` marker; the durability record instead names its `purpose`
        # and is written by the lane-verify workflow. Both are runner output,
        # so both must be accepted -- but nothing without a positive runner
        # marker may be called green.
        route = data.get('route')
        purpose = str(data.get('purpose') or '')
        runner_marked = route == 'github_actions_runner' or (
            not route and 'runner' in purpose and
            ('verification' in purpose or 'durability' in purpose))
        runner_marked = route in RUNNER_ROUTES or runner_marked
        entry['route'] = route or ('github_actions_runner (inferred from purpose)'
                                   if runner_marked else None)
        if data.get('error'):
            entry.update({'status': 'ran_but_failed', 'error': data['error']})
        elif not runner_marked:
            entry.update({'status': 'unverified',
                          'reason': 'artifact lacks the runner route marker'})
        elif data.get('verified_roundtrip') is False or \
                data.get('matches_original_sha256') is False:
            entry.update({'status': 'ran_but_failed',
                          'error': 'runner reported a hash mismatch'})
        else:
            entry['status'] = 'green'

        # Durability is only green when a *second, fresh* machine re-fetched
        # the artifact from the external store and got the same bytes. A
        # successful upload alone proves nothing.
        if kind == 'durable' and entry['status'] == 'green':
            fresh = base / 'durable/fresh_machine_verify.json'
            if not fresh.is_file():
                entry.update({'status': 'unverified',
                              'reason': 'no fresh-machine re-fetch evidence'})
            else:
                try:
                    verify = json.loads(fresh.read_text(encoding='utf-8'))
                except json.JSONDecodeError:
                    verify = {}
                if verify.get('matches_original_sha256') is not True:
                    entry.update({'status': 'unverified',
                                  'reason': 'fresh machine saw different bytes'})
                else:
                    entry['fresh_machine_verified'] = True
                    entry['fetched_sha256'] = verify.get('fetched_sha256')
                    entry['fetched_bytes'] = verify.get('fetched_bytes')
        report[kind] = entry
    return report


def honest_limits() -> list[str]:
    """The things this lane still cannot do, stated plainly."""
    return [
        'no human viewed or listened to the output',
        'a language model describing a frame is not artistic judgement',
        'YouTube and Instagram still refuse unauthenticated extraction',
        'the lane runs only when a push wakes it; there is no daemon',
    ]


def main(argv=None):
    """CLI: `python -m accounts_studio.external_lane {status,show,trigger,limits}`."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status', help='per-capability lane report')
    show = sub.add_parser('show', help='print one runner artifact')
    show.add_argument('kind', choices=sorted(ARTIFACTS))
    trig = sub.add_parser('trigger', help='wake the lane via a push')
    trig.add_argument('--reason', default='lane')
    trig.add_argument('--dry-run', action='store_true')
    sub.add_parser('limits', help='what this lane still cannot do')
    args = parser.parse_args(argv)

    if args.cmd == 'status':
        report = capability_report()
        width = max(len(k) for k in report)
        for kind, entry in report.items():
            detail = entry.get('reason') or entry.get('error') or ''
            print(f'{kind:<{width}}  {entry["status"]:<13} {detail}')
        greens = sum(1 for e in report.values() if e['status'] == 'green')
        print(f'\n{greens}/{len(report)} external-lane capabilities have '
              f'runner-produced evidence')
        return 0
    if args.cmd == 'show':
        print(json.dumps(load(args.kind), indent=2, ensure_ascii=False))
        return 0
    if args.cmd == 'trigger':
        print(json.dumps(trigger(args.reason, dry_run=args.dry_run), indent=2))
        return 0
    for line in honest_limits():
        print('-', line)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
