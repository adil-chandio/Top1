"""Durable rework and final user-evaluation lifecycle, not creative approval generation.

Ported from the three-channel system. The important property is preserved: a
revise/reject decision archives the superseded outputs *and* their review
receipts, records the rejected video hash so it can never be redelivered, and
resets the stage pointer. Retry counters are preserved so a new revision cannot
overwrite the artifacts of an earlier attempt.
"""
import hashlib
import json
from pathlib import Path


def select_job(base, account):
    """One unfinished video, including blocked/rejected work, owns the account."""
    candidates = []
    for path in Path(base).glob('*/state.json'):
        state = json.loads(path.read_text(encoding='utf-8'))
        if state['account'] != account:
            continue
        if state['status'] in ('delivered', 'cancelled', 'accepted'):
            continue
        candidates.append((state.get('created_at', ''), path.parent.name,
                           path.parent, state))
    if not candidates:
        return None
    _, _, job, state = min(candidates)
    runnable = ('queued', 'awaiting_worker', 'awaiting_reviewer')
    return job if state['status'] in runnable else None


def feedback(job, decision, reason, restart_from='feasibility'):
    """Explicit operator/user instruction only. Serialized with the execution lock."""
    import fcntl
    from accounts_studio.pipeline import CONFIG, NOW, save
    job = Path(job).resolve()
    if not str(reason).strip():
        raise ValueError('specific user feedback required')
    with (job / 'lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('job is executing; apply feedback after current step')
        state = json.loads((job / 'state.json').read_text(encoding='utf-8'))
        if decision == 'accept':
            if state['status'] not in ('awaiting_user_evaluation', 'delivered'):
                raise ValueError('only a delivered video can be accepted')
            state['status'] = 'accepted'
        elif decision in ('revise', 'reject'):
            if restart_from not in CONFIG['stages'][:-1]:
                raise ValueError('invalid rework stage')
            if CONFIG['stages'].index(restart_from) > CONFIG['stages'].index('production'):
                raise ValueError('rejected video must be reworked before QC')
            for a in state.get('outputs', {}).get('production', {}).get('artifacts', []):
                if a['path'].lower().endswith('.mp4'):
                    state.setdefault('rejected_video_hashes', []).append(a['sha256'])
            start = CONFIG['stages'].index(restart_from)
            archive = {'at': NOW().isoformat(), 'reason': reason,
                       'outputs': {}, 'reviews': {},
                       'delivery': state.pop('delivery', None)}
            for stage in CONFIG['stages'][start:]:
                if stage in state.get('outputs', {}):
                    archive['outputs'][stage] = state['outputs'].pop(stage)
                if stage in state.get('accepted_reviews', {}):
                    archive['reviews'][stage] = state['accepted_reviews'].pop(stage)
            state.setdefault('revisions', []).append(archive)
            state['stage'] = start
            state['status'] = 'queued'
            state['user_rejected'] = True
            state['blocker'] = reason
            state['revision_attempts'] = {}
            state.pop('pending_task', None)
        else:
            raise ValueError('unknown feedback decision')
        state.setdefault('history', []).append(
            {'at': NOW().isoformat(), 'outcome': 'user_' + decision,
             'reason': reason})
        save(job / 'state.json', state)
        return state


def validate_upstream(job, state):
    """Upstream artifacts and the binding creative brief must be unchanged."""
    from accounts_studio.guards import artifact_integrity
    for result in state.get('outputs', {}).values():
        artifact_integrity(job, result)
    path = Path(job) / 'creative_brief.json'
    if state.get('creative_brief_sha256'):
        if not path.is_file():
            raise ValueError('binding creative brief deleted; explicit rebrief required')
        if hashlib.sha256(path.read_bytes()).hexdigest() != state['creative_brief_sha256']:
            raise ValueError('binding creative brief changed; explicit rebrief required')
