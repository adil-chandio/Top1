"""Create a branch-scoped render workflow from an allowlist of picture assets.

No narration, captions, reference media, or recipient private key are staged.
The generated workflow is temporary; remove it once receipt verification ends.
"""
import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

R=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('certificate',type=Path)
p.add_argument('--work',type=Path,default=Path('.cache/monarch-gecko/natural/work'))
p.add_argument('--dispatch',type=Path,default=Path('.cache/monarch-gecko/natural/dispatch'))
p.add_argument('--width',type=int,default=648)
p.add_argument('--samples',type=int,default=9)
p.add_argument('--draft',action='store_true',help='Stage original-only inputs locally without publishing')
a=p.parse_args()
sh=lambda *args,**kw:subprocess.check_output(args,text=True,**kw).strip()
branch=sh('git','branch','--show-current')
assert re.fullmatch(r'arena/[A-Za-z0-9/-]+',branch),branch
repo=sh('gh','repo','view','--json','nameWithOwner','--jq','.nameWithOwner')
assert a.width>=216 and a.width%2==0 and a.samples>0
manifest={**{f'creature/{n}':R.parent/'creature'/n for n in ('geometry.py','surface.py','habitat.py','assets/conservatory.jpg')},
          **{f'natural/{n}':R/n for n in ('render.py','filmlight.py')},'natural/take.json':a.work/'take.json'}
raw=io.BytesIO()
with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as z,tarfile.open(fileobj=z,mode='w') as f:
    for name,file in manifest.items():
        b=file.read_bytes();m=tarfile.TarInfo(name);m.size=len(b)
        f.addfile(m,io.BytesIO(b))
archive=raw.getvalue();assert 0<len(archive)<8_000_000,len(archive)
cert=a.certificate.read_text().strip()
assert re.fullmatch(r'-----BEGIN CERTIFICATE-----\n[A-Za-z0-9+/=\n]+\n-----END CERTIFICATE-----',cert)
parts=json.loads((a.work/'plan.json').read_text())['parts']
assert 0<len(parts)<=40 and all(0<=s['first']<s['end']<=1488 for s in parts)
a.dispatch.mkdir(exist_ok=True,parents=True)
(a.dispatch/'picture-only.tgz').write_bytes(archive)
sha=hashlib.sha256(archive).hexdigest()
blob=hashlib.sha1(f'blob {len(archive)}\0'.encode()+archive).hexdigest()
if not a.draft:
    posted=sh('gh','api','-X','POST',f'repos/{repo}/git/blobs','--input','-','--jq','.sha',
              input=json.dumps({'encoding':'base64','content':base64.b64encode(archive).decode('ascii')}))
    assert posted==blob
workflow=(R/'worker.yml.in').read_text()
for k,v in {'BRANCH':branch,'SOURCE':blob,'SHA256':sha,'WIDTH':str(a.width),'SAMPLES':str(a.samples),
            'RANGES':'\n'.join(f"          - {{first: {s['first']}, end: {s['end']}}}" for s in parts),
            'RECIPIENT':'\n'.join('        '+line for line in cert.splitlines())}.items():
    assert f'@{k}@' in workflow
    workflow=workflow.replace(f'@{k}@',v)
output=a.dispatch/'workflow.yml' if a.draft else Path('.github/workflows/creature-edition-render.yml')
output.parent.mkdir(exist_ok=True,parents=True);output.write_text(workflow)
record={'blob':blob,'sha256':sha,'bytes':len(archive),'width':a.width,'samples':a.samples,'parts':parts,'branch':branch,'repo':repo}
(a.dispatch/'request.json').write_text(json.dumps(record,indent=2)+'\n')
print(f'{len(parts)} ranges, synthetic rig only ({len(archive):,} bytes); {output}')
