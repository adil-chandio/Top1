"""Idempotent bounded cleanup; preserve partial progress and exact HTTP diagnostics."""
import json,os,time,urllib.request,urllib.error
BASE='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']
HEAD={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
def call(path,body=None,method='GET'):
 for attempt in range(3):
  req=urllib.request.Request(BASE+path,data=None if body is None else json.dumps(body).encode(),headers=HEAD,method=method)
  try:
   with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
  except urllib.error.HTTPError as e:
   detail=e.read(2000).decode(errors='replace')
   transient=e.code in (429,502,503,504) or (e.code==403 and e.headers.get('Retry-After'))
   if transient and attempt<2:
    time.sleep(min(60,int(e.headers.get('Retry-After','5'))));continue
   raise RuntimeError(json.dumps({'path':path,'http':e.code,'detail':detail})) from e
cleared=[];errors=[]
for sha in ['a6e0e1ae10c93b612dd52c0688d6747cdbf91b8e','1c7a465dc52e4f6e3df9592c723862a7bf2cc1f8']:
 try:
  page=1
  while True:
   cs=call('/commits/'+sha+'/check-runs?per_page=100&page='+str(page))['check_runs']
   for c in cs:
    if not c['name'].startswith('market-thumbnail-'):continue
    try:
     if 'jpeg_base64' in (c['output']['summary'] or ''):
      time.sleep(1)
      call('/check-runs/'+str(c['id']),{'output':{'title':'Temporary thumbnail transport cleared','summary':'Image payload removed. Only the 17 IDs in ACTUAL_THUMBNAIL_NOTES_ROMAN_URDU.md were visually inspected; other copies discarded uninspected. Hash-only acquisition evidence retained.'}},'PATCH')
     verify=call('/check-runs/'+str(c['id']))
     assert 'jpeg_base64' not in (verify['output']['summary'] or '')
     cleared.append({'check_id':c['id'],'name':c['name'],'sha':sha})
    except Exception as e:errors.append({'id':c['id'],'error':str(e)[:2400]})
   if len(cs)<100:break
   page+=1
 except Exception as e:errors.append({'sha':sha,'error':str(e)[:2400]})
receipt={'cleared':cleared,'count':len(cleared),'errors':errors,'rechecked_no_base64':not errors and len(cleared)==59,'scope':'two explicit research commits only; no Drive reference images'}
call('/check-runs',{'name':'market-thumbnail-cleanup-receipt','head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'failure' if errors else 'success','output':{'title':'Thumbnail cleanup bounded receipt','summary':json.dumps(receipt)}},'POST')
print(json.dumps(receipt))
if errors:raise SystemExit(1)
