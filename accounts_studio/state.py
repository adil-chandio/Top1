"""Durable state that survives a chat/sandbox reset.

The pipeline's `runtime/` directory is sandbox-local and gitignored, so a
conversation reset loses it — verified once already (job
`monarch_cam-d363f76eb8a3` vanished). This module provides a recoverable
checkpoint route instead of pretending the filesystem is durable:

- `save(job)` writes a compact, deterministic checkpoint to
  `accounts_studio/state/<job_id>.json` which IS tracked by git (force-added,
  small, no media).
- `restore(job_id)` rebuilds a job directory from that checkpoint.
- `list_checkpoints()` enumerates recoverable jobs.

Media and artifacts are NOT copied into git. A checkpoint references them by
hash and path; if the bytes are gone, the checkpoint says so instead of
implying the artifact still exists.
"""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / 'accounts_studio' / 'state'
TRACKED_KEYS = ('id', 'account', 'brief', 'created_at', 'status', 'stage',
                'attempts', 'history', 'outputs', 'blocker', 'delivery',
                'user_rejected', 'rejected_video_hashes', 'revisions',
                'creative_brief_sha256')


def _digest(path):
    path = Path(path)
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(job, note=None):
    """Write a git-trackable checkpoint for a job directory."""
    job = Path(job).resolve()
    state = json.loads((job / 'state.json').read_text(encoding='utf-8'))
    checkpoint = {key: state[key] for key in TRACKED_KEYS if key in state}
    artifacts = []
    for stage, result in (state.get('outputs') or {}).items():
        for item in result.get('artifacts', []):
            path = job / item['path']
            present = path.is_file()
            artifacts.append({
                'stage': stage,
                'path': item['path'],
                'declared_sha256': item.get('sha256'),
                'present': present,
                'actual_sha256': _digest(path) if present else None,
            })
    checkpoint['artifacts'] = artifacts
    checkpoint['checkpoint'] = {
        'schema': 1,
        'created_at': state.get('created_at'),
        'job_dir': str(job),
        'artifact_count': len(artifacts),
        'artifacts_present': sum(1 for a in artifacts if a['present']),
        'note': note or ('State only. Artifact bytes live outside git; '
                         '`present` reflects the moment of checkpointing.'),
    }
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    dest = STATE_DIR / (state['id'] + '.json')
    dest.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False) + '\n',
                    encoding='utf-8')
    return dest


def load(job_id):
    path = STATE_DIR / (job_id + '.json')
    if not path.is_file():
        raise FileNotFoundError(f'no checkpoint for {job_id}')
    return json.loads(path.read_text(encoding='utf-8'))


def list_checkpoints():
    if not STATE_DIR.is_dir():
        return []
    out = []
    for path in sorted(STATE_DIR.glob('*.json')):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            continue
        out.append({
            'job_id': data.get('id'),
            'account': data.get('account'),
            'status': data.get('status'),
            'stage': data.get('stage'),
            'artifacts_present': data.get('checkpoint', {}).get('artifacts_present'),
            'artifacts_total': data.get('checkpoint', {}).get('artifact_count'),
        })
    return out


def restore(job_id, base=None, force=False):
    """Rebuild a job directory from a checkpoint (bytes are not restored)."""
    data = load(job_id)
    if base is not None:
        base_dir = Path(base)
    else:
        saved_job_dir = data.get('checkpoint', {}).get('job_dir')
        base_dir = (Path(saved_job_dir).parent if saved_job_dir
                    else ROOT / 'accounts_studio' / 'runtime')
    base_dir = base_dir.resolve()
    job = base_dir / job_id
    if job.exists() and not force:
        raise FileExistsError(f'{job} already exists; pass force=True to overwrite state')
    job.mkdir(parents=True, exist_ok=True)
    state = {k: v for k, v in data.items()
             if k not in ('artifacts', 'checkpoint')}
    (job / 'state.json').write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    missing = []
    for entry in data.get('artifacts', []):
        declared_path = job / entry['path']
        if not declared_path.is_file() or not declared_path.stat().st_size:
            missing.append(entry['path'])
        elif entry.get('declared_sha256') and _digest(declared_path) != entry['declared_sha256']:
            missing.append(entry['path'] + ' (changed since checkpoint)')
    result = {
        'job_dir': str(job),
        'restored_state': True,
        'artifacts_declared': len(data.get('artifacts', [])),
        'artifacts_missing': missing,
        'honest_limit': ('Restored metadata only. Missing artifacts must be '
                         're-produced; the checkpoint never pretends bytes survived.'),
    }
    return result
