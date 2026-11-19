"""Verify, decrypt and count native frames from an explicitly chosen Actions run."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('run',type=int)
p.add_argument('--dispatch',type=Path,default=Path('.cache/monarch-gecko/natural/dispatch'))
p.add_argument('--partial',action='store_true',help='Download and check currently finished ranges for review')
a=p.parse_args(); spec=json.loads((a.dispatch/'request.json').read_text());repo=spec['repo']
assert re.fullmatch(r'[\w.-]+/[\w.-]+',repo)
key=Path((a.dispatch/'key-path').read_text().strip()).resolve()
probe=os.environ.get('FFPROBE','ffprobe')
out=a.dispatch/str(a.run);os.umask(0o077);out.mkdir(parents=True,exist_ok=True)
expected={(r['first'],r['end']) for r in spec['parts']}
with tarfile.open(a.dispatch/'picture-only.tgz') as arc:
    h=hashlib.sha256()
    for src in ('natural/take.json','creature/assets/conservatory.jpg','creature/geometry.py','creature/surface.py','creature/habitat.py','natural/filmlight.py','natural/render.py'):
        h.update(arc.extractfile(src).read())
    h.update(f"{spec['width']}:{spec['samples']}:4.3.0".encode())
    fingerprint=h.hexdigest()

def gh(route,*args,text=True):
    return subprocess.check_output(['gh','api',f'repos/{repo}/{route}',*args],text=text)

run=json.loads(gh(f'actions/runs/{a.run}'))
assert run['head_branch']==spec['branch'] and run['path'].endswith('creature-edition-render.yml'),run['path']
alljobs=json.loads(gh(f'actions/runs/{a.run}/jobs?filter=latest&per_page=100'))
assert alljobs['total_count']==len(expected)
jobs=[j['id'] for j in alljobs['jobs'] if j['conclusion']=='success']
if not a.partial:
    assert run['conclusion']=='success' and len(jobs)==len(expected),f"{len(jobs)}/{len(expected)} successful; a complete edit requires every frame"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def get(job):
    msg=gh(f'check-runs/{job}/annotations','--paginate','--jq','.[]|select(.title=="Sealed Creature Edition picture")|.message').strip()
    m=re.fullmatch(r'([0-9]+):([0-9]+):([0-9a-f]{40}):([0-9a-f]{64}):([0-9a-f]{64})',msg)
    assert m,f'Run receipt absent for {job}'
    f,e,obj,sha256,source=m.groups(); first,end=int(f),int(e)
    assert (first,end) in expected and source==fingerprint,(first,end,source,fingerprint)
    dst=out/f'f-{first}-{end}.mp4'
    if not dst.exists() or sha(dst)!=sha256:
        with tempfile.TemporaryDirectory(dir=out) as d:
            d=Path(d);packet=d/'packet.cms';part=d/'part.mp4'
            import base64
            packet.write_bytes(base64.b64decode(gh(f'git/blobs/{obj}','--jq','.content',text=False)))
            assert subprocess.check_output(['git','hash-object',packet],text=True).strip()==obj
            subprocess.run(['openssl','cms','-decrypt','-binary','-inform','DER','-in',packet,'-recip',key/'cert.pem','-inkey',key/'key.pem','-out',part],check=True)
            assert sha(part)==sha256
            part.replace(dst)
    inspect=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-of','json',dst]))
    assert len(inspect['streams'])==1
    v=inspect['streams'][0]
    assert [v['codec_name'],v['width'],v['height'],v['avg_frame_rate'],int(v['nb_read_frames']),v['color_range'],v['color_space']]==[
        'h264',spec['width'],2*round(8*spec['width']/9),'24/1',end-first,'tv','bt709']
    print(f'Verified picture frames {first:04}–{end:04} (exclusive) · {dst.stat().st_size:,} bytes',flush=True)
    return {'first':first,'end':end,'blob':obj,'sha256':sha256,'fingerprint':fingerprint,'job':job,'file':dst.name}

with ThreadPoolExecutor(max_workers=5) as pool:
    rows=sorted(pool.map(get,jobs),key=lambda r:r['first'])
found={(r['first'],r['end']) for r in rows};assert len(found)==len(rows)
if not a.partial:assert found==expected
(out/('partial.json' if a.partial else 'receipts.json')).write_text(json.dumps({'complete':found==expected,'run':a.run,'parts':rows},indent=2)+'\n')
print(f'{len(rows)}/{len(expected)} sealed ranges verified locally → {out}')
