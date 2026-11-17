"""Recover check receipts/images for actual review; keep image bytes out of Git."""
import sys,subprocess,json,re,base64
from pathlib import Path
sha=sys.argv[1];groups={};receipts=[]
page=1
while True:
 d=json.loads(subprocess.check_output(['gh','api',f'repos/adil-chandio/Top1/commits/{sha}/check-runs?per_page=100&page={page}']))
 for c in d['check_runs']:
  name=c['name'];summary=c.get('output',{}).get('summary') or ''
  if name.startswith('ab-image-') and not summary.startswith('Temporary'):
   key,n=name.rsplit('__',1);groups.setdefault(key,{})[int(n)]=summary
  elif name.startswith('ab-receipt-'):
   try:receipts.append(json.loads(re.sub(r'\\(?!["\\/bfnrtu])',r'\\\\',summary)))
   except ValueError:print('Invalid receipt',name)
 if len(d['check_runs'])<100:break
 page+=1
root=Path('studio/runtime/archive-batch');root.mkdir(parents=True,exist_ok=True)
for key,parts in groups.items():
 try:(root/(key+'.jpg')).write_bytes(base64.b64decode(''.join(parts[n] for n in range(max(parts)+1))));print(key)
 except Exception as e:print('Incomplete image',key,type(e).__name__)
p=Path('research/monarch_cam_restart_batch1/runtime_receipts')/('archive-batch-'+sha+'.json');p.write_text(json.dumps(receipts,indent=2)+'\n')
for r in receipts:print(r['identifier'],r.get('duration'),r.get('video'),r.get('error'),r.get('dense_windows'),r.get('temporary_media_deleted'))
