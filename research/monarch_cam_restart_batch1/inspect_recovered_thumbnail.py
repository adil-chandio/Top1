"""Acquire exactly one existing runner inspection copy; no fresh media download.
Run with CHECK_ID. Delete previous local JPEG before acquiring the next.
"""
import base64,hashlib,json,subprocess,sys
from pathlib import Path
root=Path('studio/runtime/market-thumbnails');root.mkdir(parents=True,exist_ok=True)
for old in root.glob('*.jpg'):old.unlink()
c=json.loads(subprocess.check_output(['gh','api','repos/adil-chandio/Top1/check-runs/'+sys.argv[1]]))
p=json.loads(c['output']['summary']);raw=base64.b64decode(p.pop('jpeg_base64'),validate=True)
assert hashlib.sha256(raw).hexdigest()==p['inspection_copy_sha256']
assert len(raw)<=40000
f=root/(p['id']+'.jpg');f.write_bytes(raw)
p.update(check_id=c['id'],head_sha=c['head_sha'],local_path=str(f),status='acquired_not_yet_visually_inspected')
log=Path('research/monarch_cam_restart_batch1/THUMBNAIL_ACQUISITION_RECEIPTS.jsonl')
with log.open('a') as out:out.write(json.dumps(p)+'\n')
print(str(f))
