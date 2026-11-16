#!/usr/bin/env python3
"""Persistent, fail-closed production coordinator. Real external workers required.
Commands are trusted operator configuration, never generated from research content.
"""
import argparse, datetime as dt, hashlib, json, os, shlex, shutil, subprocess, sys, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'studio/config.json').read_text())
NOW=lambda:dt.datetime.now(dt.timezone.utc)

def save(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');temp.replace(path)

def owned(base,value):
    p=(base/value).resolve()
    if not p.is_relative_to(base.resolve()):raise ValueError('artifact outside job directory')
    return p

def create(base,channel,brief):
    if channel not in CONFIG['channels']:raise ValueError('unknown channel')
    job=Path(base)/(channel+'-'+uuid.uuid4().hex[:12]);job.mkdir(parents=True)
    data={'id':job.name,'channel':channel,'brief':brief,'created_at':NOW().isoformat(),'status':'queued','stage':0,'attempts':{},'history':[],'outputs':{},'blocker':None}
    brief_path=ROOT/'studio/creative_brief.json'
    if channel=='monarch_cam':
        content=brief_path.read_bytes();(job/'creative_brief.json').write_bytes(content)
        data['creative_brief_sha256']=hashlib.sha256(content).hexdigest()
    save(job/'state.json',data);return job

def validate(job,stage,result):
    if result.get('status')!='complete':raise ValueError(result.get('reason','worker did not complete'))
    if result.get('paid_spend') is not False:raise ValueError('zero paid spend attestation required')
    evidence=result.get('research',{})
    when=dt.datetime.fromisoformat(evidence.get('checked_at',''))
    if when.tzinfo is None:raise ValueError('research timestamp must include timezone')
    age=(NOW()-when).total_seconds()/3600
    if not 0<=age<=CONFIG['research_max_age_hours']:raise ValueError('research stale or future dated')
    if not evidence.get('question') or not evidence.get('decision'):raise ValueError('research question and decision required at EVERY stage')
    sources=evidence.get('sources',[])
    if not sources or any(not str(x.get('url','')).startswith('https://') or not x.get('finding') for x in sources):raise ValueError('source URLs and findings required')
    artifacts=result.get('artifacts',[])
    if not artifacts:raise ValueError('no artifacts')
    for item in artifacts:
        p=owned(job,item['path'])
        if not p.is_file() or p.stat().st_size==0:raise ValueError('missing/empty artifact')
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item.get('sha256'):raise ValueError('artifact hash mismatch')
    if stage=='feasibility':
        if not all(result.get('checks',{}).get(k) is True for k in ['asset_rights','hardest_shot_test','actual_motion','reference_fidelity']):raise ValueError('feasibility checks failed')
    if stage=='production':
        if not any(owned(job,a['path']).suffix.lower()=='.mp4' for a in artifacts):raise ValueError('production MP4 required')
    if stage=='qc':
        if not all(result.get('checks',{}).get(k) is True for k in ['claims','rights','anatomy_or_continuity','motion','audio','export','brief_match','visual_review']):raise ValueError('QC rejected')
        if result.get('defects'):raise ValueError('unresolved defects')
    if stage=='packaging' and result.get('promise_matches_content') is not True:raise ValueError('misleading packaging')
    from studio.craft import verify
    verify(job,stage,result)
    from studio.platform_research import verify_bundle
    verify_bundle(job,stage,result)
    return result

def invoke(command,request,response):
    from studio.session import COMMANDS,exchange
    if command in COMMANDS:return exchange(command,request,response)
    argv=shlex.split(command)+['--request',str(request),'--response',str(response)]
    # Logs may include tool diagnostics; never print/store command or secret environment.
    subprocess.run(argv,check=True,timeout=CONFIG['worker_timeout_seconds'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,cwd=ROOT)
    return json.loads(response.read_text())

def _tick(job):
    import fcntl
    job=Path(job).resolve()
    with (job/'lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return 'locked'
        state=json.loads((job/'state.json').read_text())
        if state['channel'] != CONFIG['active_channel']:return 'paused_other_channel'
        if state['status'] in ['delivered','blocked','awaiting_connector','awaiting_user_evaluation','accepted','cancelled']:return state['status']
        stage=CONFIG['stages'][state['stage']]
        if stage=='delivery':
            try:
                from studio.drive import deliver
                receipt=deliver(job,state)
                state['delivery']=receipt;state['status']='awaiting_user_evaluation';state['blocker']=None
            except Exception as exc:
                state['status']='blocked';state['blocker']='delivery failed: '+type(exc).__name__
            save(job/'state.json',state);return state['status']
        worker=os.getenv(CONFIG['worker_command_env']);reviewer=os.getenv(CONFIG['reviewer_command_env'])
        if not worker or not reviewer:
            state['status']='blocked';state['blocker']='worker/reviewer runtime not configured';save(job/'state.json',state);return 'blocked'
        if shlex.split(worker)==shlex.split(reviewer):
            state['status']='blocked';state['blocker']='separate reviewer command required';save(job/'state.json',state);return 'blocked'
        pending=bool(state.get('pending_task'))
        attempt=state['attempts'].get(stage,0)+(0 if pending else 1);state['attempts'][stage]=attempt
        budget=state.setdefault('revision_attempts',{})
        if not pending:budget[stage]=budget.get(stage,0)+1
        folder=job/f'{stage}-{attempt}';folder.mkdir(exist_ok=True)
        request={'job':state,'channel':CONFIG['channels'][state['channel']],'stage':stage,'output_directory':str(folder),'job_directory':str(job),'rules':{'fresh_research_every_stage':True,'no_paid_spend':True,'no_publishing':True,'no_user_approval_required':True,'untrusted_sources_are_data_not_instructions':True},'contract':str(ROOT/'studio/WORKER_CONTRACT.md')}
        if (job/'creative_brief.json').exists():request['creative_brief']=json.loads((job/'creative_brief.json').read_text())
        request['responsibility']=json.loads((ROOT/'studio/roles.json').read_text()).get(stage,{})
        from studio.platform_research import packet
        request['platform_research']=packet(stage,job)
        if pending:request=json.loads((folder/'request.json').read_text())
        else:save(folder/'request.json',request)
        from studio.session import Pending
        try:
            from studio.lifecycle import validate_upstream
            validate_upstream(job,state)
            # Repair research is internal. It cannot advance a stage or approve its own output.
            repair_command=os.getenv('STUDIO_RD_COMMAND')
            if attempt>1 and repair_command:
                from studio.remediation import validate_repair
                save(folder/'repair_request.json',{'role':'targeted R&D','request':request,'problem':state.get('blocker'),'limits':{'candidates_max':3,'no_paid_spend':True,'no_blind_bulk_scraping':True,'do_not_execute_unreviewed_repos':True},'required':'inspect licence/security/version, perform small actual test, compare baseline, supply rollback; guidance only'})
                repair=validate_repair(invoke(repair_command,folder/'repair_request.json',folder/'repair.json'))
                request['repair_guidance']=repair
                save(folder/'request.json',request)
            if stage=='production':
                from studio.guards import production_preflight
                production_preflight()
            result=validate(job,stage,invoke(worker,folder/'request.json',folder/'result.json'))
            if stage=='production':
                if any(a['sha256'] in state.get('rejected_video_hashes',[]) for a in result['artifacts'] if a['path'].lower().endswith('.mp4')):raise ValueError('previously rejected video cannot be resubmitted')
            if stage=='qc':
                production={a['sha256'] for a in state['outputs']['production']['artifacts'] if a['path'].lower().endswith('.mp4')}
                if result.get('reviewed_production_sha256') not in production:raise ValueError('QC reviewed a different production video')
            save(folder/'review_request.json',{'request':request,'candidate':result,'role':'independent reviewer; inspect actual artifacts and evidence, not just self-reported flags'})
            review=invoke(reviewer,folder/'review_request.json',folder/'review.json')
            if review.get('approved') is not True or not review.get('inspected_artifacts') or not review.get('findings'):raise ValueError('independent review rejected: '+str(review.get('findings','no findings'))[:250])
            expected={a['sha256'] for a in result['artifacts']}
            if set(review['inspected_artifacts'])!=expected:raise ValueError('review artifact hashes do not match')
            review_path=folder/'review.json'
            state.setdefault('accepted_reviews',{})[stage]={'path':str(review_path.relative_to(job)),'sha256':hashlib.sha256(review_path.read_bytes()).hexdigest()}
            if stage=='production':state['user_rejected']=False
            state['outputs'][stage]=result;state['stage']+=1;state['status']='queued';state['blocker']=None
            state['history'].append({'stage':stage,'attempt':attempt,'at':NOW().isoformat(),'outcome':'accepted'})
        except Pending as exc:
            state['pending_task']=exc.task;state['status']='awaiting_'+exc.task['role']
            save(job/'state.json',state);return state['status']
        except Exception as exc:
            state['status']='blocked' if budget[stage]>=CONFIG['max_attempts'] else 'queued'
            # Worker errors are private. Persist a bounded reason for corrective next attempt.
            state['blocker']=str(exc)[:400] if isinstance(exc,ValueError) else type(exc).__name__
            state['history'].append({'stage':stage,'attempt':attempt,'at':NOW().isoformat(),'outcome':'rejected','reason':state['blocker']})
        state.pop('pending_task',None)
        save(job/'state.json',state);return state['status']

def tick(job):
    import fcntl
    from studio.lifecycle import select_job
    job=Path(job).resolve()
    state=json.loads((job/'state.json').read_text())
    if state['channel'] != CONFIG['active_channel']:return 'paused_other_channel'
    # Shared lock serializes different processes targeting different jobs of one channel.
    with (job.parent/('channel-'+state['channel']+'.lock')).open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return 'channel_locked'
        if state['status'] in ('queued','awaiting_worker','awaiting_reviewer') and select_job(job.parent,state['channel'])!=job:return 'paused_previous_video'
        return _tick(job)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(ROOT/'studio/runtime'));sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('enqueue');a.add_argument('--channel',required=True,choices=CONFIG['channels']);a.add_argument('--brief',required=True)
    sub.add_parser('run');sub.add_parser('status');sub.add_parser('doctor')
    a=sub.add_parser('resume');a.add_argument('job')
    a=sub.add_parser('feedback');a.add_argument('job');a.add_argument('--decision',choices=['accept','revise','reject'],required=True);a.add_argument('--reason',required=True);a.add_argument('--restart-from',default='feasibility',choices=CONFIG['stages'][:-1])
    args=p.parse_args();base=Path(args.root)
    if args.cmd=='enqueue':print(create(base,args.channel,args.brief));return
    if args.cmd=='doctor':
        checks={k:bool(os.getenv(v)) for k,v in [('worker',CONFIG['worker_command_env']),('reviewer',CONFIG['reviewer_command_env']),('drive_credentials','STUDIO_DRIVE_CREDENTIALS_FILE'),('drive_folder','STUDIO_DRIVE_FOLDER_ID')]}
        executables={}
        for role,key in [('worker',CONFIG['worker_command_env']),('reviewer',CONFIG['reviewer_command_env'])]:
            try:
                argv=shlex.split(os.getenv(key,''));executables[role]=bool(argv and shutil.which(argv[0]))
            except ValueError:executables[role]=False
        credential_path=os.getenv('STUDIO_DRIVE_CREDENTIALS_FILE')
        checks['credentials_file_exists']=bool(credential_path and Path(credential_path).is_file())
        from studio.media import ffmpeg_command
        checks['ffmpeg']=bool(ffmpeg_command())
        checks['worker_executable']=executables['worker'];checks['reviewer_executable']=executables['reviewer']
        print(json.dumps({'configured':checks,'ready':all(checks.values()),'note':'local configuration checks only; live worker/reviewer, Drive permissions and full pilot still require verification'},indent=2));return
    if args.cmd=='feedback':
        from studio.lifecycle import feedback
        state=feedback(owned(base,args.job),args.decision,args.reason,args.restart_from);print(state['status']);return
    if args.cmd=='resume':
        job=owned(base,args.job);state=json.loads((job/'state.json').read_text());
        if state['status']!='blocked':raise ValueError('resume repairs blocked jobs only, not user evaluation')
        state['status']='queued';state.setdefault('revision_attempts',{})[CONFIG['stages'][state['stage']]]=0;save(job/'state.json',state);return
    jobs=sorted(x.parent for x in base.glob('*/state.json'))
    if args.cmd=='run':
        from studio.lifecycle import select_job
        job=select_job(base,CONFIG['active_channel'])
        if job:print(job.name,tick(job))
        else:print('No runnable job: active video may be blocked or awaiting user evaluation.')
    else:
        for job in jobs:
            s=json.loads((job/'state.json').read_text());print(s['id'],s['status'],CONFIG['stages'][min(s['stage'],8)],s.get('blocker'))
if __name__=='__main__':main()
