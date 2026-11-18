"""Durable handoff to the active Arena agent's tools; never impersonates another agent.
No tokens, paid API, polling worker or approval fabrication. A pending task is work for
an equipped operator/agent, not a request for routine user approval.
"""
import argparse,hashlib,json,os
from pathlib import Path

COMMANDS={'arena-session-worker':'worker','arena-session-reviewer':'reviewer'}
class Pending(Exception):
    def __init__(self,task):self.task=task

def exchange(command,request,response):
    from studio.pipeline import save
    request=Path(request);response=Path(response)
    task={'role':COMMANDS[command],'request':str(request),'response':str(response),
          'request_sha256':hashlib.sha256(request.read_bytes()).hexdigest()}
    envelope=response.with_suffix('.submission.json')
    if not envelope.exists():raise Pending(task)
    data=json.loads(envelope.read_text())
    if data.get('request_sha256')!=task['request_sha256']:raise ValueError('stale session submission')
    identity=data.get('executor',{})
    if not identity.get('id') or not identity.get('capabilities'):raise ValueError('executor identity and actual capabilities required')
    if task['role']=='reviewer':
        worker=json.loads(response.with_name('result.submission.json').read_text())['executor']
        if identity['id']==worker['id']:raise ValueError('same executor cannot independently approve its own work')
        if identity.get('independent_context') is not True:raise ValueError('review must explicitly identify independent context')
    save(response,data['result']);return data['result']

def step(job):
    from studio.pipeline import CONFIG,tick
    state=json.loads((Path(job)/'state.json').read_text())
    if CONFIG['stages'][state['stage']]=='delivery' and state['status'] in ('queued','blocked','awaiting_connector'):
        from studio.connector_delivery import prepare
        prepare(job)
        return 'awaiting_connector'
    values={CONFIG['worker_command_env']:'arena-session-worker',CONFIG['reviewer_command_env']:'arena-session-reviewer'}
    previous={key:os.environ.get(key) for key in values}
    try:
        os.environ.update(values)
        return tick(Path(job))
    finally:
        for key,value in previous.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value

def submit(job,result,executor,capabilities,independent_context=False):
    """No advance/approve shortcut: actual result goes through normal validation on step."""
    import fcntl
    from studio.pipeline import save,owned
    job=Path(job).resolve()
    with (job/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=json.loads((job/'state.json').read_text());task=state.get('pending_task')
        if not task:raise ValueError('no pending session task')
        request=owned(job,task['request']);response=owned(job,task['response'])
        if hashlib.sha256(request.read_bytes()).hexdigest()!=task['request_sha256']:raise ValueError('pending request changed')
        envelope=response.with_suffix('.submission.json')
        if envelope.exists():raise ValueError('submission already exists; process it before retry')
        save(envelope,{'request_sha256':task['request_sha256'],'executor':{'id':executor,'capabilities':capabilities,'independent_context':independent_context},'result':result})

def attach(job):
    """Move an unstarted blocked legacy job onto session transport, retaining history."""
    import fcntl
    from studio.pipeline import ROOT,NOW,save
    job=Path(job).resolve()
    with (job/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=json.loads((job/'state.json').read_text())
        if state['stage']!=0 or state.get('outputs') or state['status']!='blocked':raise ValueError('attach is only for unstarted blocked jobs')
        if state['channel']!='monarch_cam':raise ValueError('no binding brief for this channel')
        content=(ROOT/'studio/creative_brief.json').read_bytes()
        if state.get('creative_brief_sha256'):
            from studio.lifecycle import validate_upstream
            validate_upstream(job,state)
        else:
            (job/'creative_brief.json').write_bytes(content)
            state['creative_brief_sha256']=hashlib.sha256(content).hexdigest()
        state['status']='queued';state['blocker']=None
        state.setdefault('history',[]).append({'at':NOW().isoformat(),'outcome':'session_transport_attached','note':'Existing user-authorized scope; no creative or reviewer approval implied'})
        save(job/'state.json',state)

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('step');a.add_argument('job')
    a=sub.add_parser('attach');a.add_argument('job')
    a=sub.add_parser('submit');a.add_argument('job');a.add_argument('--result',required=True);a.add_argument('--executor',required=True);a.add_argument('--capability',action='append',required=True);a.add_argument('--independent-context',action='store_true')
    a=p.parse_args()
    if a.cmd=='attach':
        attach(a.job);return
    if a.cmd=='submit':submit(a.job,json.loads(Path(a.result).read_text()),a.executor,a.capability,a.independent_context)
    else:
        status=step(a.job);state=json.loads((Path(a.job)/'state.json').read_text())
        print(json.dumps({'status':status,'task':state.get('pending_task')},indent=2))
if __name__=='__main__':main()
