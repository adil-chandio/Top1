"""Stage-visible, time-bounded research decoder. Never asserts actual inspection.
Temporary raw copies only; no production/republication permission implied.
"""
import base64,hashlib,json,os,subprocess,tempfile,time,urllib.parse,urllib.request
from pathlib import Path
LABEL=os.environ['REFERENCE_LABEL']
TARGETS={
 'microchips':('branch-education','How are Microchips Made_ 🖥️🛠️ CPU Manufacturing Process Steps.ia.mp4',[0,124,154,470,626,1096,1398]),
 'storm':('youtube-ZcEyC-Ixf-g','ZcEyC-Ixf-g.webm',[0,3.5,10,18,26,34,40,46]),
}
BASE='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']
HEAD={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
def publish(name,obj):
 text=obj if isinstance(obj,str) else json.dumps(obj,ensure_ascii=False)
 body={'name':'cs-'+LABEL+'-'+name,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':'Research transport: '+name,'summary':text}}
 req=urllib.request.Request(BASE+'/check-runs',data=json.dumps(body).encode(),headers=HEAD,method='POST')
 with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)['id']
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
  chosen=next(f for f in meta['files'] if f['name']==name);assert 0<int(chosen['size'])<=180000000
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
   run(['ffmpeg','-nostdin','-v','error','-i',str(path),'-map','0:v:0','-an','-vf',"fps=1,scale=200:-1,drawtext=text='%{pts\\:hms}':x=2:y=2:fontsize=12:fontcolor=white:box=1:boxcolor=black@0.7,tile=6x5",'-q:v','12',str(root/'survey-%03d.jpg')],300)
   stage='dense';log(stage,windows=windows)
   for i,t in enumerate(windows):
    run(['ffmpeg','-nostdin','-v','error','-ss',str(t),'-i',str(path),'-map','0:v:0','-an','-vf','scale=240:-1,tile=6x4','-frames:v','1','-q:v','10',str(root/f'dense-{i:02}.jpg')],45)
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
