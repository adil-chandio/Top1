"""TEST FIXTURE ONLY. Not a real research/creative or audiovisual-review agent."""
import argparse,datetime as dt,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--role',required=True);p.add_argument('--request');p.add_argument('--response');a=p.parse_args()
r=json.loads(Path(a.request).read_text())
if a.role=='worker':
 out=Path(r['output_directory'])/'fixture-evidence.txt';out.write_text('TEST FIXTURE: validates subprocess plumbing only, no research performed.')
 result={'status':'complete','paid_spend':False,'research':{'checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),'question':'Fixture protocol?','decision':'Verify real subprocess wiring, not creative quality','sources':[{'url':'https://example.org/test-fixture','finding':'Synthetic test data, not inspected external research'}]},'artifacts':[{'path':str(out.relative_to(Path(r['job_directory']))),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}]}
else:
 candidate=r['candidate'];job=Path(r['request']['job_directory']);hashes=[]
 for item in candidate['artifacts']:
  data=(job/item['path']).read_bytes();digest=hashlib.sha256(data).hexdigest()
  assert digest==item['sha256'];hashes.append(digest)
 result={'approved':True,'inspected_artifacts':hashes,'findings':'Fixture bytes opened and hash checked. NOT audiovisual or artistic approval.'}
Path(a.response).write_text(json.dumps(result))
