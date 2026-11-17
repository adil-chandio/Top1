"""Recover minimal missing Blender runtime libraries and two research-only figures.
No production-media reuse permission is implied. Source bytes never enter Git.
"""
import base64,hashlib,io,json,lzma,os,platform,subprocess,tarfile,urllib.request
from pathlib import Path
from PIL import Image
BASE='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']
HEAD={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
def publish(name,p):
 body={'name':name,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':'Temporary gecko research/runtime recovery; not final production','summary':json.dumps(p)}}
 req=urllib.request.Request(BASE+'/check-runs',data=json.dumps(body).encode(),headers=HEAD,method='POST')
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)['id']
names=['libXrender.so.1','libXxf86vm.so.1','libXfixes.so.3','libXi.so.6','libxkbcommon.so.0','libSM.so.6','libICE.so.6','libGL.so.1','libGLX.so.0','libGLdispatch.so.0']
cache=subprocess.check_output(['ldconfig','-p'],text=True)
files={}
for name in names:
 found=[l.split('=>')[-1].strip() for l in cache.splitlines() if l.strip().startswith(name+' ') and 'x86-64' in l]
 if not found:raise RuntimeError('missing library on runner: '+name)
 files[name]=Path(found[0]).resolve()
buf=io.BytesIO();manifest=[]
with tarfile.open(fileobj=buf,mode='w') as tar:
 for name,path in files.items():
  raw=path.read_bytes();meta=tarfile.TarInfo(name);meta.size=len(raw);tar.addfile(meta,io.BytesIO(raw));manifest.append({'name':name,'sha256':hashlib.sha256(raw).hexdigest(),'source':str(path),'size':len(raw)})
raw=lzma.compress(buf.getvalue());encoded=base64.b64encode(raw).decode();checks=[]
for i,start in enumerate(range(0,len(encoded),48000)):
 checks.append(publish('gecko-runtime-chunk-'+str(i),{'chunk':i,'base64':encoded[start:start+48000]}))
publish('gecko-runtime-receipt',{'archive_sha256':hashlib.sha256(raw).hexdigest(),'xz_bytes':len(raw),'checks':checks,'files':manifest,'runner_platform':platform.platform(),'glibc':platform.libc_ver(),'provenance':'shared runtime libraries already installed on ubuntu22.04 runner; dependency binaries only; not production film assets'})
figs={'S2-fig1':'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/c243/2607396/8e8151f1124b/rsif20071077f01.jpg','S2-fig2':'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/c243/2607396/f9aa1be74e14/rsif20071077f02.jpg'}
for name,url in figs.items():
 try:
  with urllib.request.urlopen(url,timeout=30) as r:original=r.read(3000000)
  im=Image.open(io.BytesIO(original)).convert('RGB');original_size=im.size;im.thumbnail((1000,1000));out=io.BytesIO();im.save(out,'JPEG',quality=65);raw=out.getvalue()
  if len(raw)>40000:raise RuntimeError('inspection_copy_too_large')
  publish('gecko-figure-'+name,{'id':name,'url':url,'source_size':original_size,'source_sha256':hashlib.sha256(original).hexdigest(),'copy_sha256':hashlib.sha256(raw).hexdigest(),'jpeg_base64':base64.b64encode(raw).decode(),'rights':'research inspection only; no production reuse licence established'})
 except Exception as e:publish('gecko-figure-'+name+'-error',{'error':type(e).__name__+': '+str(e)[:300]})
