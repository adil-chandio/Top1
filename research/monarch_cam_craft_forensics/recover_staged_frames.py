"""Hash-verified recovery only from a completed per-reference manifest."""
import argparse,base64,hashlib,json,subprocess
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('sha');a=p.parse_args();runs=[];page=1
 while True:
  data=json.loads(subprocess.check_output(['gh','api',f'repos/adil-chandio/Top1/commits/{a.sha}/check-runs?per_page=100&page={page}']))['check_runs'];runs+=data
  if len(data)<100:break
  page+=1
 dest=Path('research/monarch_cam_craft_forensics')/('STAGED_RECOVERY_'+a.sha[:7]+'.json')
 previous=json.loads(dest.read_text()) if dest.exists() else {}
 inspected={(s['file'],s['sha256']):s for s in previous.get('recovered_sheets',[])}
 byid={c['id']:c for c in runs};results=[];sheets=[]
 for c in runs:
  if not(c['name'].startswith('cs-') and c['name'].endswith('-receipt')):continue
  label=c['name'][3:-8];r=json.loads(c['output']['summary']);results.append({'label':label,'check_id':c['id'],'receipt':r})
  if not r.get('success'):continue
  out=Path('studio/runtime/craft-forensics')/a.sha[:7]/label;out.mkdir(parents=True,exist_ok=True)
  for item in r['sheets']:
   raw=base64.b64decode(''.join(byid[i]['output']['summary'] for i in item['checks']),validate=True)
   assert hashlib.sha256(raw).hexdigest()==item['sha256'] and len(raw)==item['bytes']
   path=out/item['name'];path.write_bytes(raw)
   sheet={'file':str(path),'sha256':item['sha256'],'bytes':item['bytes'],'transport_check_ids':item['checks'],'actually_inspected':False}
   prior=inspected.get((str(path),item['sha256']),{})
   for key in ('actually_inspected','inspection_method','inspection_report'):
    if key in prior:sheet[key]=prior[key]
   sheets.append(sheet)
 result={'source_commit':a.sha,'references':results,'recovered_sheets':sheets,'actual_listening':False,'full_every_frame_review':False}
 dest=Path('research/monarch_cam_craft_forensics')/('STAGED_RECOVERY_'+a.sha[:7]+'.json');dest.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'references':[(r['label'],r['receipt']['success']) for r in results],'hash_verified_sheets':len(sheets),'receipt':str(dest)}))
if __name__=='__main__':main()
