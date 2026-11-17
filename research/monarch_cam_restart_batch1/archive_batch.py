"""Bounded sequential reference research. Never commits/uploads raw media."""
import os,json,urllib.request,urllib.parse,subprocess,tempfile,base64,hashlib
from pathlib import Path
BASE='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']
HEADERS={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
def get(url,auth=False):
 with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS if auth else {'User-Agent':'MonarchCam-reference-research/1.0'}),timeout=45) as f:return json.load(f)
def publish(name,data):
 s=data if isinstance(data,str) else json.dumps(data,ensure_ascii=False)
 req=urllib.request.Request(BASE+'/check-runs',data=json.dumps({'name':name,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':name,'summary':s}},ensure_ascii=False).encode(),headers=HEADERS)
 with urllib.request.urlopen(req,timeout=30) as f:return json.load(f)
cfg=json.loads(Path('research/monarch_cam_restart_batch1/archive_batch_config.json').read_text())
for sha in cfg.get('clear_shas',[]):
 for c in get(BASE+'/commits/'+sha+'/check-runs?per_page=100',True)['check_runs']:
  if c['name'].startswith('ab-image-'):
   req=urllib.request.Request(BASE+'/check-runs/'+str(c['id']),method='PATCH',data=json.dumps({'output':{'title':'Inspected frames cleared','summary':'Temporary image transport cleared after actual inspection.'}}).encode(),headers=HEADERS)
   with urllib.request.urlopen(req,timeout=30) as f:json.load(f)
if cfg['mode']=='cleanup':publish('ab-cleanup',{'cleared':cfg['clear_shas']});raise SystemExit
for ident in cfg['identifiers']:
 r={'identifier':ident,'actual_visual_inspection':False,'media_acquired':False}
 try:
  m=get('https://archive.org/metadata/'+ident);meta=m.get('metadata',{})
  r['metadata']={k:meta.get(k) for k in ['title','creator','description','source','date','licenseurl','external-identifier']}
  r['restricted']=bool(m.get('is_dark') or meta.get('access-restricted-item'))
  r['media_files']=[{k:f.get(k) for k in ['name','size','format','source']} for f in m.get('files',[]) if f.get('name','').lower().endswith(('.mp4','.webm'))]
  # Small provenance files only, not a bulk mirror.
  info=[f for f in m.get('files',[]) if f.get('name','').endswith('.info.json') and int(f.get('size') or 0)<2000000]
  for f in info[:2]:
   d=get('https://archive.org/download/'+ident+'/'+urllib.parse.quote(f['name']));r.setdefault('original_metadata',[]).append({k:d.get(k) for k in ['id','title','channel','channel_id','webpage_url','duration','view_count','upload_date','license']})
  if cfg['mode']=='metadata':publish('ab-meta-'+ident,r);continue
  choices=[f for f in r['media_files'] if int(f.get('size') or 0)<cfg.get('max_bytes',180000000)]
  if ident in cfg.get('files',{}):choices=[f for f in choices if f['name']==cfg['files'][ident]]
  if r['restricted'] or not choices:raise RuntimeError('No small unrestricted media')
  chosen=min(choices,key=lambda f:int(f['size']));r['chosen']=chosen
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);path=root/'source.mp4';url='https://archive.org/download/'+ident+'/'+urllib.parse.quote(chosen['name']);h=hashlib.sha256();total=0
   with urllib.request.urlopen(url,timeout=45) as response,path.open('wb') as out:
    while True:
     b=response.read(1048576)
     if not b:break
     total+=len(b)
     if total>cfg.get('max_bytes',180000000):raise RuntimeError('byte limit')
     h.update(b);out.write(b)
   r.update(media_acquired=True,bytes=total,sha256=h.hexdigest())
   probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)],timeout=30));duration=float(probe['format']['duration']);r['duration']=duration;r['video']=[{k:s.get(k) for k in ['width','height','r_frame_rate']} for s in probe['streams'] if s['codec_type']=='video']
   interval=cfg.get('interval',2) if duration<90 else cfg.get('long_interval',4);r['survey_interval']=interval
   subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(path),'-vf',f"fps=1/{interval},scale=200:-1,drawtext=text='%{{pts\\:hms}}':x=2:y=2:fontsize=12:fontcolor=white:box=1:boxcolor=black@0.7,tile=6x5",'-q:v','6',str(root/'survey-%02d.jpg')],check=True,timeout=150)
   # Detect candidate scene boundaries, then inspect native consecutive frames around them.
   import re
   scenes=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-i',str(path),'-vf',"select='gt(scene,0.3)',showinfo",'-an','-f','null','-'],capture_output=True,text=True,timeout=150)
   boundaries=[float(t) for t in re.findall(r'pts_time:([0-9.]+)',scenes.stderr)]
   r['scene_candidates_seconds']=boundaries
   selected=boundaries[:3] if duration<90 else [boundaries[i] for i in sorted(set([0,len(boundaries)//2,len(boundaries)-1]))] if boundaries else []
   windows=cfg.get('windows',{}).get(ident,[0]+[max(0,t-0.35) for t in selected]+[max(0,duration-1.1)])
   r['dense_windows']=windows
   for i,start in enumerate(windows):
    # consecutive native frames, 24 per sheet; duration varies with source fps.
    subprocess.run(['ffmpeg','-nostdin','-v','error','-ss',str(start),'-i',str(path),'-vf','scale=200:-1,tile=6x4','-frames:v','1','-q:v','6',str(root/f'dense-{i:02d}.jpg')],check=True,timeout=30)
   for image in sorted(root.glob('*.jpg')):
    encoded=base64.b64encode(image.read_bytes()).decode()
    # Store whole images in individual chunks; no Actions artifacts.
    for n in range(0,len(encoded),55000):publish('ab-image-'+ident+'__'+image.stem+'__'+str(n//55000),encoded[n:n+55000])
   r['sheets']=len(list(root.glob('*.jpg')))
  r['temporary_media_deleted']=not Path(folder).exists()
 except Exception as e:
  r['error_type']=type(e).__name__;r['error']=str(e)[:200]
  if 'folder' in locals():r['temporary_media_deleted']=not Path(folder).exists()
 publish('ab-receipt-'+ident,r)
