"""Recover bounded research-only YouTube thumbnail copies via ephemeral runner.
No video media; thumbnails are emitted to temporary checks for inspection, then cleared.
"""
import base64,hashlib,io,json,os,urllib.request
from PIL import Image
from pathlib import Path
rows=json.loads(Path('research/monarch_cam_restart_batch1/ANIMAL_PERFORMANCE_COHORTS.json').read_text())
ids=[r['id'] for c in rows['cohorts'] for r in c['rows']]
root=Path('research/monarch_cam_restart_batch1')
for filename in ['ADDITIONAL_PRIMARY_COHORTS.json','CONTEXTUAL_PRIMARY_CONTROLS.json']:
 extra=json.loads((root/filename).read_text())
 ids.extend(r['id'] for c in extra['cohorts'] for r in c['rows'])
ids.extend(r['id'] for r in json.loads((root/'BIZARRE_BEASTS_CURRENT_COHORT.json').read_text())['rows'])
ids=list(dict.fromkeys(ids))
def api(path,body):
 req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+path,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
for vid in ids:
 try:
  url='https://i.ytimg.com/vi/'+vid+'/hqdefault.jpg'
  with urllib.request.urlopen(url,timeout=25) as r: raw=r.read(2000000)
  im=Image.open(io.BytesIO(raw)).convert('RGB'); original_size=im.size;im.thumbnail((480,360))
  b=io.BytesIO();im.save(b,'JPEG',quality=65); data=b.getvalue()
  if len(data)>40000:raise ValueError('bounded_output_exceeded')
  payload={'id':vid,'source_url':url,'source_sha256':hashlib.sha256(raw).hexdigest(),'source_size':original_size,'inspection_copy_sha256':hashlib.sha256(data).hexdigest(),'jpeg_base64':base64.b64encode(data).decode(),'source_bytes_persisted_to_disk':False}
  out=api('/check-runs',{'name':'market-thumbnail-'+vid,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':'Temporary market thumbnail; not playback or reuse clearance','summary':json.dumps(payload)}})
  print(vid,out['id'])
 except Exception as e:print(vid,'FAILED',type(e).__name__)
