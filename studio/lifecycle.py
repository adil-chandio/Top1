"""Durable rework and final user-evaluation lifecycle, not creative approval generation."""
import hashlib,json
from pathlib import Path

def select_job(base,channel):
    """One unfinished video, including blocked/rejected/awaiting-user work, owns channel."""
    candidates=[]
    for path in Path(base).glob('*/state.json'):
        state=json.loads(path.read_text())
        if state['channel']==channel and state['status'] not in ('accepted','cancelled'):
            candidates.append((state.get('created_at',''),path.parent.name,path.parent,state))
    if not candidates:return None
    _,_,job,state=min(candidates)
    return job if state['status'] in ('queued','awaiting_worker','awaiting_reviewer') else None

def feedback(job,decision,reason,restart_from='feasibility'):
    """Explicit operator/user instruction only. Serialize with execution lock."""
    import fcntl
    from studio.pipeline import CONFIG,NOW,save
    job=Path(job).resolve()
    if not reason.strip():raise ValueError('specific user feedback required')
    with (job/'lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('job is executing; apply feedback after current step')
        state=json.loads((job/'state.json').read_text())
        if decision=='accept':
            if state['status'] not in ('awaiting_user_evaluation','delivered'):raise ValueError('only delivered video can be accepted')
            state['status']='accepted'
        elif decision in ('revise','reject'):
            if restart_from not in CONFIG['stages'][:-1]:raise ValueError('invalid rework stage')
            if CONFIG['stages'].index(restart_from)>CONFIG['stages'].index('production'):raise ValueError('rejected video must be reworked before QC')
            for a in state.get('outputs',{}).get('production',{}).get('artifacts',[]):
                if a['path'].lower().endswith('.mp4'):
                    state.setdefault('rejected_video_hashes',[]).append(a['sha256'])
            start=CONFIG['stages'].index(restart_from)
            archive={'at':NOW().isoformat(),'reason':reason,'outputs':{},'reviews':{},'delivery':state.pop('delivery',None)}
            for stage in CONFIG['stages'][start:]:
                if stage in state.get('outputs',{}):archive['outputs'][stage]=state['outputs'].pop(stage)
                if stage in state.get('accepted_reviews',{}):archive['reviews'][stage]=state['accepted_reviews'].pop(stage)
            state.setdefault('revisions',[]).append(archive)
            # Preserve old attempt counters: new revisions must not overwrite old attempt artifacts.
            state['stage']=start;state['status']='queued';state['user_rejected']=True;state['blocker']=reason
            state['revision_attempts']={}
            state.pop('pending_task',None)
        else:raise ValueError('unknown feedback decision')
        state.setdefault('history',[]).append({'at':NOW().isoformat(),'outcome':'user_'+decision,'reason':reason})
        save(job/'state.json',state);return state

def validate_upstream(job,state):
    from studio.guards import artifact_integrity
    for result in state.get('outputs',{}).values():artifact_integrity(job,result)
    path=Path(job)/'creative_brief.json'
    if state.get('creative_brief_sha256'):
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=state['creative_brief_sha256']:
            raise ValueError('binding creative brief changed; explicit rebrief required')
