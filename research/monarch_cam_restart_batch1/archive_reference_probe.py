"""One public archive reference at a time; temporary raw footage, no upload artifacts."""
import os,json,urllib.request,urllib.parse,tempfile,subprocess,base64,hashlib
from pathlib import Path

def fetch(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'MonarchCam-reference-research/1.0'}),timeout=40) as f:return json.load(f)
def check(name,summary):
 body={'name':name,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':name,'summary':summary}}
 req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/check-runs',data=json.dumps(body,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as f:json.load(f)
r={'visual_review_complete':False,'media_acquired':False,'frames_decoded':False,'metadata':[]}
try:
 for ident in ['how-a-car-engine-works','the-densest-city-on-earth','youtube_-_UCnZeeKO8qVdtkrA4-uKhtTw_2023']:
  m=fetch('https://archive.org/metadata/'+ident)
  files=[{k:f.get(k) for k in ['name','size','format','source','original']} for f in m.get('files',[]) if f.get('name','').lower().endswith(('.mp4','.webm','.info.json'))]
  r['metadata'].append({'identifier':ident,'metadata':{k:m.get('metadata',{}).get(k) for k in ['title','creator','description','source','external-identifier','licenseurl']},'files':files[:80],'restricted':m.get('is_dark',False) or m.get('metadata',{}).get('access-restricted-item',False)})
 first=r['metadata'][0]
 candidates=[f for f in first['files'] if f['name'].endswith('.mp4') and int(f.get('size') or 0)<180000000]
 if first['restricted'] or not candidates:raise RuntimeError('no_small_unrestricted_mp4')
 chosen=min(candidates,key=lambda x:int(x['size']));r['chosen_file']=chosen
 with tempfile.TemporaryDirectory() as directory:
  root=Path(directory);path=root/'reference.mp4'
  url='https://archive.org/download/how-a-car-engine-works/'+urllib.parse.quote(chosen['name'])
  h=hashlib.sha256();total=0
  with urllib.request.urlopen(url,timeout=40) as response,path.open('wb') as out:
   while True:
    block=response.read(1024*1024)
    if not block:break
    total+=len(block)
    if total>180000000:raise RuntimeError('byte_limit')
    h.update(block);out.write(block)
  r.update(media_acquired=True,bytes=total,sha256=h.hexdigest(),download_url=url)
  info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)],timeout=30));r['probe']={'duration':info['format'].get('duration'),'streams':[{k:s.get(k) for k in ['codec_type','codec_name','width','height','r_frame_rate']} for s in info['streams']]}
  # Whole-duration chronological survey: one frame per two seconds, sheets 8x5.
  subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(path),'-vf',"fps=1/2,scale=160:-1,drawtext=text='%{pts\\:hms}':x=2:y=2:fontsize=11:fontcolor=white:box=1:boxcolor=black@0.7,tile=8x5",'-q:v','6',str(root/'survey-%02d.jpg')],check=True,timeout=100)
  r['frames_decoded']=True
  for image in sorted(root.glob('survey-*.jpg')):
   encoded=base64.b64encode(image.read_bytes()).decode()
   # Split across check outputs to stay below GitHub's per-summary limit.
   for n in range(0,len(encoded),50000):check('archive-'+image.stem+'-'+str(n//50000),encoded[n:n+50000])
  r['survey_sheet_count']=len(list(root.glob('survey-*.jpg')))
 r['temporary_media_deleted']=not Path(directory).exists()
except Exception as e:r['error_type']=type(e).__name__;r['error_message']=str(e)[:300]
finally:
 if 'directory' in locals():r['temporary_media_deleted']=not Path(directory).exists()
 check('archive-reference-probe',json.dumps(r,ensure_ascii=False))
