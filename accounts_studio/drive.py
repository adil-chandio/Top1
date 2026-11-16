"""Drive delivery using operator-provided credentials, not Arena connector credentials.
No public sharing. Recover already-uploaded job by appProperties + exact MD5/size.

Isolated from the three-channel studio system: uses ACCOUNTS_* env vars and
the 'accounts_job' appProperty, so deliveries never collide with that system.
"""
import hashlib,json,os,subprocess
from pathlib import Path

def deliver(job,state):
    from google.auth import load_credentials_from_file
    from google.auth.transport.requests import AuthorizedSession
    path=os.getenv('ACCOUNTS_DRIVE_CREDENTIALS_FILE');folder=os.getenv('ACCOUNTS_DRIVE_FOLDER_ID')
    if not path or not folder:raise RuntimeError('Drive unattended credentials/folder not configured')
    credentials,_=load_credentials_from_file(path,scopes=['https://www.googleapis.com/auth/drive.file'])
    session=AuthorizedSession(credentials)
    candidates=[job/a['path'] for a in state['outputs']['production']['artifacts'] if a['path'].lower().endswith('.mp4')]
    if len(candidates)!=1:raise ValueError('one final production MP4 required')
    video=candidates[0].resolve()
    if not video.is_relative_to(job.resolve()):raise ValueError('path escape')
    data=video.read_bytes();sha=hashlib.sha256(data).hexdigest();md5=hashlib.md5(data).hexdigest()
    original=next(a for a in state['outputs']['production']['artifacts'] if a['path'].lower().endswith('.mp4'))
    if sha!=original['sha256']:raise ValueError('video changed after QC')
    # Decode entire stream, not just header metadata.
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],check=True,timeout=600,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    url='https://www.googleapis.com/drive/v3/files'
    # Job id is locally generated, folder supplied by trusted operator configuration.
    if "'" in folder:raise ValueError('invalid folder')
    q=f"trashed = false and '{folder}' in parents and appProperties has {{ key='accounts_job' and value='{state['id']}' }}"
    r=session.get(url,params={'q':q,'fields':'files(id,name,size,md5Checksum,webViewLink)','supportsAllDrives':'true','includeItemsFromAllDrives':'true'},timeout=60);r.raise_for_status()
    existing=r.json().get('files',[])
    if existing:
        if len(existing)!=1 or existing[0].get('md5Checksum')!=md5 or int(existing[0].get('size',0))!=len(data):raise ValueError('existing delivery conflicts; no duplicate uploaded')
        item=existing[0]
    else:
        metadata={'name':state['id']+'.mp4','parents':[folder],'appProperties':{'accounts_job':state['id'],'sha256':sha},'description':state['outputs']['production'].get('attribution','')}
        r=session.post('https://www.googleapis.com/upload/drive/v3/files',params={'uploadType':'multipart','supportsAllDrives':'true','fields':'id,name,size,md5Checksum,webViewLink'},files={'metadata':('metadata',json.dumps(metadata),'application/json'),'file':(video.name,data,'video/mp4')},timeout=600);r.raise_for_status();item=r.json()
        if item.get('md5Checksum')!=md5 or int(item.get('size',0))!=len(data):raise ValueError('upload integrity mismatch')
    receipt={'file_id':item['id'],'link':item.get('webViewLink') or 'https://drive.google.com/file/d/'+item['id']+'/view','sha256':sha,'bytes':len(data),'public_sharing_enabled':False}
    from accounts_studio.pipeline import save
    save(job/'delivery.json',receipt);return receipt
