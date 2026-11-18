"""Arena Drive connector handoff. OAuth stays inside the connected app.
Prepare -> actual upload_file -> actual get_file/list_permissions -> finalize.
Never treats an upload request, local receipt or a link as proof of delivery.
"""
import fcntl,hashlib,json,subprocess
from pathlib import Path
from studio.guards import delivery_preflight
from studio.pipeline import save

def prepare(job):
    from studio.media import ffmpeg_command
    job=Path(job).resolve()
    with (job/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=json.loads((job/'state.json').read_text())
        from studio.pipeline import CONFIG
        if state['channel']!=CONFIG['active_channel']:raise ValueError('inactive channel')
        if CONFIG['stages'][state['stage']]!='delivery' or state['status'] not in ('queued','blocked','awaiting_connector'):raise ValueError('job not ready for delivery')
        delivery_preflight(job,state)
        from studio.lifecycle import validate_upstream
        validate_upstream(job,state)
        brief=json.loads((job/'creative_brief.json').read_text());folder=brief['drive_folder_id']
        item=next(a for a in state['outputs']['production']['artifacts'] if a['path'].lower().endswith('.mp4'))
        video=job/item['path'];data=video.read_bytes()
        if len(data)>100*1024*1024:raise ValueError('connector size limit; do not upload')
        ffmpeg=ffmpeg_command()
        if not ffmpeg:raise ValueError('FFmpeg required')
        subprocess.run([ffmpeg,'-v','error','-xerror','-i',str(video),'-f','null','-'],check=True,timeout=600,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        name=state['id']+'-r'+str(len(state.get('revisions',[])))+'.mp4'
        task={'name':name,'file_path':str(video),'folder':folder,'bytes':len(data),'sha256':item['sha256'],'md5':hashlib.md5(data).hexdigest(),
              'instructions':'Search exact name in folder before upload. Recover matching existing file; do not duplicate on uncertain upload. Then get_file metadata and all list_permissions pages. Never create public permissions.',
              'upload_input':{'name':name,'file_path':str(video),'parents':[folder],'content_mime_type':'video/mp4','target_mime_type':None,'description':state['outputs']['production'].get('attribution',''),'starred':False,'fields':'id,name,size,md5Checksum,parents,webViewLink','supports_all_drives':True}}
        save(job/'connector_delivery_task.json',task);state['status']='awaiting_connector';save(job/'state.json',state)
        return task

def finalize(job,metadata,permissions):
    """Operator supplies unmodified actual connector get_file and permission results.
    Local checks prove consistency, not authenticity of an arbitrary caller's dict.
    """
    job=Path(job).resolve()
    with (job/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if metadata.get('success') is False or permissions.get('success') is False:raise ValueError('connector returned failure')
        metadata=metadata.get('file',metadata)
        metadata={**metadata,'md5Checksum':metadata.get('md5Checksum',metadata.get('md5_checksum'))}
        state=json.loads((job/'state.json').read_text())
        if state['status']!='awaiting_connector':raise ValueError('no pending connector upload')
        delivery_preflight(job,state)
        from studio.lifecycle import validate_upstream
        validate_upstream(job,state)
        task=json.loads((job/'connector_delivery_task.json').read_text())
        brief=json.loads((job/'creative_brief.json').read_text())
        video=next(a for a in state['outputs']['production']['artifacts'] if a['path'].lower().endswith('.mp4'))
        if task['sha256']!=video['sha256'] or task['folder']!=brief['drive_folder_id']:raise ValueError('stale delivery task')
        if metadata.get('name')!=task['name'] or metadata.get('parents')!=[task['folder']]:raise ValueError('wrong destination/name')
        if metadata.get('md5Checksum')!=task['md5'] or int(metadata.get('size',-1))!=task['bytes']:raise ValueError('remote integrity mismatch')
        if not metadata.get('id') or metadata.get('trashed'):raise ValueError('invalid remote file')
        if 'permissions' not in permissions or permissions.get('nextPageToken') or permissions.get('next_page_token'):raise ValueError('complete permission evidence required')
        if any(p.get('type') in ('anyone','domain') for p in permissions['permissions']):raise ValueError('private delivery required')
        receipt={'file_id':metadata['id'],'link':'https://drive.google.com/file/d/'+metadata['id']+'/view','sha256':video['sha256'],'bytes':task['bytes'],'public_sharing_enabled':False,'transport':'arena_google_drive_connector'}
        save(job/'connector_delivery_evidence.json',{'metadata':metadata,'permissions':permissions})
        save(job/'delivery.json',receipt);state['delivery']=receipt;state['status']='awaiting_user_evaluation';state['blocker']=None;save(job/'state.json',state)
        return receipt


def main():
    import argparse
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('prepare');a.add_argument('job')
    a=sub.add_parser('finalize');a.add_argument('job');a.add_argument('--metadata',required=True);a.add_argument('--permissions',required=True)
    args=p.parse_args()
    if args.cmd=='prepare':result=prepare(args.job)
    else:result=finalize(args.job,json.loads(Path(args.metadata).read_text()),json.loads(Path(args.permissions).read_text()))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
