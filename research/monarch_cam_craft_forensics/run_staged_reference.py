"""Stage-visible, time-bounded research decoder. Never asserts actual inspection.
Temporary raw copies only; no production/republication permission implied.
"""
import base64,hashlib,json,os,subprocess,tempfile,time,urllib.parse,urllib.request,urllib.error
from pathlib import Path
LABEL=os.environ['REFERENCE_LABEL']
TARGETS={
 'microchips':('branch-education','How are Microchips Made_ 🖥️🛠️ CPU Manufacturing Process Steps.ia.mp4',[0,124,154,470,626,1096,1398]),
 'storm':('youtube-ZcEyC-Ixf-g','ZcEyC-Ixf-g.webm',[0,3.5,10,18,26,34,40,46]),
 'watch':('youtube-9_QsCLYs2mY',None,[0,43,95,133,249,397]),
 'diesel':('youtube-cIQ0yIZgQeE',None,[31,157,191,239,255,898,1019]),
 'microchips-actions':('branch-education','How are Microchips Made_ 🖥️🛠️ CPU Manufacturing Process Steps.ia.mp4',[346,357,375,1120,1141,1447]),
}
BASE='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']
HEAD={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
def publish(name,obj):
 text=obj if isinstance(obj,str) else json.dumps(obj,ensure_ascii=False)
 body={'name':'cs-'+LABEL+'-'+name,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':'Research transport: '+name,'summary':text}}
 req=urllib.request.Request(BASE+'/check-runs',data=json.dumps(body).encode(),headers=HEAD,method='POST')
 for attempt in range(5):
  try:
   with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)['id']
  except urllib.error.HTTPError as e:
   if e.code not in (403,429,500,502,503,504) or attempt==4:raise
   time.sleep(min(60,int(e.headers.get('Retry-After',5*(attempt+1)))))
  except (TimeoutError,urllib.error.URLError):
   if attempt==4:raise
   time.sleep(3*(attempt+1))
def log(stage,**kw):
 data={'stage':stage,**kw};print(json.dumps(data),flush=True);publish('stage-'+stage,data)
def getjson(url):
 with urllib.request.urlopen(url,timeout=30) as r:return json.load(r)
def run(args,timeout):
 p=subprocess.run(args,timeout=timeout,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-1200:])
 return p.stdout

def main():
 ident,name,windows=TARGETS[LABEL];result={'identifier':ident,'selected_file':name,'actual_visual_inspection':False,'audio_listened':False,'stages':[]};stage='metadata';folder=None
 try:
  log(stage,identifier=ident)
  meta=getjson('https://archive.org/metadata/'+ident);m=meta.get('metadata',{})
  if meta.get('is_dark') or m.get('access-restricted-item'):raise RuntimeError('restricted source')
  if name is None:
   candidates=[f for f in meta.get('files',[]) if f['name'].lower().endswith(('.mp4','.webm')) and 0<int(f.get('size',0))<=180000000]
   if not candidates and LABEL!='watch':
    result['available_media']=[{k:f.get(k) for k in ('name','size','format')} for f in meta.get('files',[]) if f['name'].lower().endswith(('.mp4','.webm'))]
    raise RuntimeError('No eligible bounded media at independent original identifier; available files preserved')
   if not candidates:
    query='animagraffs OR "9_QsCLYs2mY"'
    discovery=getjson('https://archive.org/advancedsearch.php?'+urllib.parse.urlencode({'q':query,'output':'json','rows':25,'fl[]':['identifier','title','creator']},doseq=True))
    result['discovery']=discovery.get('response',{})
    for doc in result['discovery'].get('docs',[])[:12]:
     candidate_ident=doc.get('identifier')
     if not candidate_ident:continue
     candidate_meta=getjson('https://archive.org/metadata/'+urllib.parse.quote(candidate_ident))
     cm=candidate_meta.get('metadata',{})
     if candidate_meta.get('is_dark') or cm.get('access-restricted-item'):continue
     for f in candidate_meta.get('files',[]):
      fn=f['name'].lower()
      if not(fn.endswith(('.mp4','.webm')) and 0<int(f.get('size',0))<=180000000):continue
      if '9_qsclys2my' in fn or ('mechanical watch' in fn and 'animagraffs' in json.dumps(cm).lower()):
       candidates.append(f);meta=candidate_meta;m=cm;ident=candidate_ident
     if candidates:break
    if not candidates:raise RuntimeError('Exact identifier and broader creator metadata scan yielded no bounded matching watch media; discovery preserved')
    result['identifier']=ident
   chosen=min(candidates,key=lambda f:int(f['size']));name=chosen['name'];result['selected_file']=name
  else:chosen=next(f for f in meta['files'] if f['name']==name)
  assert 0<int(chosen['size'])<=180000000
  result['source_metadata']={k:m.get(k) for k in ['title','creator','source','licenseurl']};result['listed_bytes']=int(chosen['size'])
  stage='download';log(stage,bytes=int(chosen['size']))
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);path=root/'source';h=hashlib.sha256();size=0;start=time.monotonic();last=0
   url='https://archive.org/download/'+ident+'/'+urllib.parse.quote(name)
   with urllib.request.urlopen(url,timeout=30) as response,path.open('wb') as out:
    while True:
     if time.monotonic()-start>240:raise TimeoutError('total download budget240s exceeded')
     b=response.read(1048576)
     if not b:break
     size+=len(b)
     if size>180000000:raise RuntimeError('byte cap exceeded')
     out.write(b);h.update(b)
     if size-last>=16777216:print('download_bytes',size,flush=True);last=size
   assert size==int(chosen['size']),'truncated download'
   result.update(bytes=size,sha256=h.hexdigest());stage='probe';log(stage,bytes=size,sha256=h.hexdigest())
   probe=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)],30))
   video=next(s for s in probe['streams'] if s['codec_type']=='video' and not s.get('disposition',{}).get('attached_pic'))
   duration=float(probe['format']['duration']);result.update(duration=duration,video={k:video.get(k) for k in ['width','height','r_frame_rate','nb_frames']},survey_interval=1)
   stage='survey';log(stage,duration=duration)
   # Full-duration every-second survey. PTS is resampled: not exact source cut timing.
   if not LABEL.endswith('-actions'):
    run(['ffmpeg','-nostdin','-v','error','-i',str(path),'-map','0:v:0','-an','-vf',"fps=1,scale=200:-1,drawtext=text='%{pts\\:hms}':x=2:y=2:fontsize=12:fontcolor=white:box=1:boxcolor=black@0.7,tile=6x5",'-q:v','12',str(root/'survey-%03d.jpg')],300)
   else:result['survey_interval']=None;result['survey_omitted']='Action drill-down only; full1fps survey already inspected in48f4e79'
   stage='dense';log(stage,windows=windows)
   for i,t in enumerate(windows):
    vf="scale=320:-1,setpts=PTS+"+str(t)+"/TB,drawtext=text='%{pts\\:hms}':x=2:y=2:fontsize=14:fontcolor=white:box=1:boxcolor=black@0.7,tile=6x4"
    run(['ffmpeg','-nostdin','-v','error','-ss',str(t),'-i',str(path),'-map','0:v:0','-an','-vf',vf,'-vsync','0','-frames:v','3','-q:v','8',str(root/f'dense-{i:02}-%02d.jpg')],60)
    pages=sorted(root.glob(f'dense-{i:02}-*.jpg'))
    assert len(pages)==3 and len({hashlib.sha256(p.read_bytes()).hexdigest() for p in pages})==3,'Dense window requires three distinct timestamped pages; duplicate-output coverage rejected'
   result['dense_method']='72 consecutive decoded frames per seek, in three24-cell sheets; displayed filter PTS plus requested seek offset, not independent demuxer packet-PTS verification'
   result['dense_windows']=windows
   stage='transport';images=sorted(root.glob('*.jpg'));log(stage,sheets=len(images));manifest=[]
   for image in images:
    raw=image.read_bytes();encoded=base64.b64encode(raw).decode();ids=[]
    for i in range(0,len(encoded),55000):ids.append(publish('image-'+image.stem+'__'+str(i//55000),encoded[i:i+55000]))
    manifest.append({'name':image.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'checks':ids})
    print('transported',image.name,len(raw),flush=True)
   result['sheets']=manifest;result['success']=True
  result['temporary_media_deleted']=not Path(folder).exists();log('complete',sheets=len(result['sheets']))
 except Exception as e:
  result.update(success=False,failed_stage=stage,error=type(e).__name__+': '+str(e)[:1500])
  if folder:result['temporary_media_deleted']=not Path(folder).exists()
 finally:publish('receipt',result)
 if not result.get('success'):raise SystemExit(result['error'])
if __name__=='__main__':main()
