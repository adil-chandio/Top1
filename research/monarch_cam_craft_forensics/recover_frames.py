"""Recover temporary check-run image transport into ignored local research runtime.
Does not mark images inspected. Receipts remain small tracked text; frames stay ignored.
"""
import argparse,base64,hashlib,json,subprocess
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('sha');a=p.parse_args()
 out=Path('studio/runtime/craft-forensics')/a.sha[:7];out.mkdir(parents=True,exist_ok=True)
 runs=[];page=1
 while True:
  raw=subprocess.check_output(['gh','api',f'repos/adil-chandio/Top1/commits/{a.sha}/check-runs?per_page=100&page={page}'])
  items=json.loads(raw)['check_runs'];runs+=items
  if len(items)<100:break
  page+=1
 chunks={};receipts=[]
 for c in runs:
  name=c['name'];text=(c.get('output') or {}).get('summary','')
  if name.startswith('cf-') and '-image-' in name:
   stem,index=name.rsplit('__',1);chunks.setdefault(stem,{})[int(index)]={'check_id':c['id'],'text':text}
  elif name.startswith('cf-') and '-receipt-' in name:
   receipts.append({'check_id':c['id'],'name':name,'receipt':json.loads(text)})
 manifest=[]
 for stem,parts in sorted(chunks.items()):
  indices=sorted(parts);assert indices==list(range(len(parts))),stem
  raw=base64.b64decode(''.join(parts[i]['text'] for i in indices),validate=True)
  assert raw.startswith(b'\xff\xd8'),stem
  path=out/(stem+'.jpg');path.write_bytes(raw)
  manifest.append({'file':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'transport_check_ids':[parts[i]['check_id'] for i in indices],'actually_inspected':False})
 result={'source_commit':a.sha,'receipts':receipts,'recovered_sheets':manifest,'actual_listening':False,'full_every_frame_review':False}
 dest=Path('research/monarch_cam_craft_forensics')/('RECOVERY_'+a.sha[:7]+'.json');dest.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'receipts':len(receipts),'sheets':len(manifest),'output':str(dest)}))
if __name__=='__main__':main()
