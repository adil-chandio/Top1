"""Cloud-only final assembly helper. Media relayed via temporary unreferenced git blobs
because local artifact CDN is inaccessible. No media added to branch tree.
"""
from pathlib import Path
import subprocess,base64,json,hashlib,os
BASE=Path(__file__).parent;OUT=BASE/'out';OUT.mkdir(exist_ok=True)
def api(path):return json.loads(subprocess.check_output(['gh','api',path]))
def blob(sha):return base64.b64decode(api('repos/adil-chandio/Top1/git/blobs/'+sha)['content'])
trigger=json.loads((BASE/'opening_finish_trigger.json').read_text())
(OUT/'opening_narration.wav').write_bytes(blob(trigger['narration_blob_sha']))
for name,info in json.loads((BASE/'opening_audio_sources.json').read_text()).items():
 path=info['path'];repo=info['repository'];ref=info['commit']
 data=api(f'repos/{repo}/contents/{path}?ref={ref}')
 body=api(data['git_url']);raw=base64.b64decode(body['content'])
 if hashlib.sha256(raw).hexdigest()!=info['sha256']:raise RuntimeError('audio source hash mismatch')
 dest=OUT/'audio'/name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
subprocess.run(['python',str(BASE/'finish_opening.py')],check=True)
# Upload only deliverable, inspection frames and technical receipt, not 480 frame blobs.
manifest={}
for name in ['MONARCH_CAM_OPENING_20S_REVIEW.mp4','opening_delivery_receipt.json']+[f'opening_review_frame_{f:04}.jpg' for f in [36,144,240,324,432]]:
 data=(OUT/name).read_bytes()
 result=json.loads(subprocess.check_output(['gh','api','repos/adil-chandio/Top1/git/blobs','--input','-'],input=json.dumps({'content':base64.b64encode(data).decode(),'encoding':'base64'}).encode()))
 manifest[name]={'blob_sha':result['sha'],'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
result=json.loads(subprocess.check_output(['gh','api','repos/adil-chandio/Top1/git/blobs','--input','-'],input=json.dumps({'content':json.dumps(manifest),'encoding':'utf-8'}).encode()))
with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('manifest_sha='+result['sha']+'\n')
