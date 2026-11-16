"""Shared production and delivery barriers. Never generates quality approvals.

Ported from the three-channel system with `studio.` -> `accounts_studio.`,
`channel` -> `account`, and the release manifest renamed. The barriers are
identical in force: they check that approved bytes are still the same bytes,
and that every independent review receipt is intact and bound to the exact
artifact hashes it claims to have inspected.
"""
import hashlib
import json
from pathlib import Path


def artifact_integrity(job, result):
    """Every artifact recorded in a result must still exist with the same hash."""
    from accounts_studio.pipeline import owned
    for item in result.get('artifacts', []):
        path = owned(job, item['path'])
        if not path.is_file():
            raise ValueError('approved artifact missing or changed')
        if hashlib.sha256(path.read_bytes()).hexdigest() != item.get('sha256'):
            raise ValueError('approved artifact missing or changed')


def production_preflight():
    """Full-render clearance must exist before a production stage may run."""
    from accounts_studio.pipeline import ROOT
    from accounts_studio.release_gate import check
    manifest = ROOT / 'accounts_studio/active_release.json'
    if not manifest.is_file():
        raise ValueError('no active_release.json; full render not cleared')
    check(json.loads(manifest.read_text(encoding='utf-8')))


def delivery_preflight(job, state):
    """Also called from the direct Drive adapter, so no caller can skip QC."""
    from accounts_studio.pipeline import owned
    production_preflight()
    if state.get('user_rejected') is True:
        raise ValueError('user-rejected output cannot be delivered again')
    for stage in ('production', 'qc', 'packaging'):
        result = state.get('outputs', {}).get(stage)
        if not result:
            raise ValueError('missing completed ' + stage)
        artifact_integrity(job, result)
        proof = state.get('accepted_reviews', {}).get(stage)
        if not proof:
            raise ValueError('missing independent ' + stage + ' review')
        path = owned(job, proof['path'])
        if not path.is_file():
            raise ValueError('review receipt changed')
        if hashlib.sha256(path.read_bytes()).hexdigest() != proof.get('sha256'):
            raise ValueError('review receipt changed')
        review = json.loads(path.read_text(encoding='utf-8'))
        if review.get('approved') is not True:
            raise ValueError('review not approved')
        if set(review.get('inspected_artifacts', [])) != {
                a['sha256'] for a in result['artifacts']}:
            raise ValueError('review artifact binding mismatch')
    videos = [a for a in state['outputs']['production']['artifacts']
              if a['path'].lower().endswith('.mp4')]
    if len(videos) != 1:
        raise ValueError('exactly one final video required')
    if videos[0]['sha256'] in state.get('rejected_video_hashes', []):
        raise ValueError('rejected video hash cannot be redelivered')
    if state['outputs']['qc'].get('reviewed_production_sha256') != videos[0]['sha256']:
        raise ValueError('QC belongs to different video')
    return True
