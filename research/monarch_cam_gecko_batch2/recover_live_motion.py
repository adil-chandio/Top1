"""Bounded public publisher Vimeo reference study; no cookies/login/access bypass."""
import base64,hashlib,json,os,subprocess,urllib.request
from pathlib import Path
from PIL import Image,ImageDraw
OUT=Path('/tmp/tokay-motion');OUT.mkdir(exist_ok=True)
base='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']
def emit(name,report):
 data={'name':name,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':'Temporary research reference; not production reuse','summary':json.dumps(report)}}
 r=urllib.request.Request(base+'/check-runs',data=json.dumps(data).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(r,timeout=30) as f:print(json.load(f)['id'],flush=True)
def run(cmd,timeout=90):return subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,check=True)
try:
 run(['yt-dlp','--no-playlist','--no-warnings','--socket-timeout','20','--retries','0','--max-filesize','50M','--match-filter','duration < 60','-f','best[height<=480]/best','--write-info-json','-o',str(OUT/'video.%(ext)s'),'https://vimeo.com/105308288'],150)
 info=json.loads((OUT/'video.info.json').read_text());video=next(p for p in OUT.glob('video.*') if p.suffix!='.json')
 probe=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(video)]).stdout)
 duration=float(probe['format']['duration']);assert duration<60
 # Whole movie one-second survey plus native consecutive frames in first release candidate interval.
 files=[]
 for mode,seek,vf,limit in [('survey',0,'fps=1,scale=320:-1',60),('dense',4,'scale=320:-1',72)]:
  folder=OUT/mode;folder.mkdir(exist_ok=True)
  run(['ffmpeg','-v','error','-ss',str(seek),'-i',str(video),'-vf',vf,'-vsync','0','-frames:v',str(limit),str(folder/'%04d.jpg')])
  frames=sorted(folder.glob('*.jpg'))
  for start in range(0,len(frames),24):
   sheet=Image.new('RGB',(1280,4*264),(22,22,22));draw=ImageDraw.Draw(sheet)
   for j,p in enumerate(frames[start:start+24]):
    im=Image.open(p);im.thumbnail((320,235));x=(j%4)*320;y=(j//4)*176
    # rows are 176px: retain source aspect ratio in 320x150 image area.
    im.thumbnail((320,150));sheet.paste(im,(x,y+24));draw.text((x+5,y+5),f'{mode} index {start+j}'+(f' ~{start+j}s' if mode=='survey' else f' seek4s frame+{start+j}'),fill='white')
   dest=OUT/f'{mode}-{start//24:02}.jpg';sheet.save(dest,quality=85);files.append((dest,len(frames[start:start+24])))
 receipt={'url':'https://vimeo.com/105308288','title':info.get('title'),'uploader':info.get('uploader'),'id':info.get('id'),'duration':duration,'media_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'streams':[{k:s.get(k) for k in ['codec_type','width','height','avg_frame_rate','nb_frames']} for s in probe['streams']],'pixels_inspected':False,'capture_rate_not_established':True,'rights':'Annual Reviews copyright; reference only; no production reuse clearance'}
 emit('tokay-motion-receipt',receipt)
 for p,count in files:
  raw=p.read_bytes();enc=base64.b64encode(raw).decode()
  for i,start in enumerate(range(0,len(enc),45000)):
   emit('tokay-motion-'+p.stem+'-'+str(i),{'file':p.name,'part':i,'parts':(len(enc)+44999)//45000,'base64':enc[start:start+45000],'sha256':hashlib.sha256(raw).hexdigest(),'cells':count})
except Exception as e:
 emit('tokay-motion-error',{'type':type(e).__name__,'error':str(e)[:1000],'stderr':getattr(e,'stderr','')[-4000:],'pixels_inspected':False});raise
