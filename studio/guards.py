"""Shared production and delivery barriers. Never generates quality approvals."""
import hashlib,json
from pathlib import Path

def artifact_integrity(job,result):
    from studio.pipeline import owned
    for item in result.get('artifacts',[]):
        path=owned(job,item['path'])
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item.get('sha256'):
            raise ValueError('approved artifact missing or changed')

def production_preflight():
    from studio.pipeline import ROOT
    from studio.release_gate import check
    check(json.loads((ROOT/'studio/active_release.json').read_text()))

def delivery_preflight(job,state):
    """Also called from direct Drive adapter, preventing a caller skipping coordinator QC."""
    from studio.pipeline import owned
    production_preflight()
    if state.get('user_rejected') is True:raise ValueError('user-rejected output cannot be delivered again')
    for stage in ('production','qc','packaging'):
        result=state.get('outputs',{}).get(stage)
        if not result:raise ValueError('missing completed '+stage)
        artifact_integrity(job,result)
        proof=state.get('accepted_reviews',{}).get(stage)
        if not proof:raise ValueError('missing independent '+stage+' review')
        path=owned(job,proof['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest()!=proof.get('sha256'):raise ValueError('review receipt changed')
        review=json.loads(path.read_text())
        if review.get('approved') is not True:raise ValueError('review not approved')
        if set(review.get('inspected_artifacts',[]))!={a['sha256'] for a in result['artifacts']}:raise ValueError('review artifact binding mismatch')
    videos=[a for a in state['outputs']['production']['artifacts'] if a['path'].lower().endswith('.mp4')]
    if len(videos)!=1:raise ValueError('exactly one final video required')
    if state['outputs']['qc'].get('reviewed_production_sha256')!=videos[0]['sha256']:raise ValueError('QC belongs to different video')
    return True
