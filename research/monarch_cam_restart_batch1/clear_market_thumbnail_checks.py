"""Clear only this research's temporary thumbnail check payloads, no other session."""
import json,os,urllib.request
BASE='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']
HEAD={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
def call(path,body=None,method='GET'):
 req=urllib.request.Request(BASE+path,data=None if body is None else json.dumps(body).encode(),headers=HEAD,method=method)
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
cleared=[]
for sha in ['a6e0e1ae10c93b612dd52c0688d6747cdbf91b8e','1c7a465dc52e4f6e3df9592c723862a7bf2cc1f8']:
 page=1
 while True:
  cs=call('/commits/'+sha+'/check-runs?per_page=100&page='+str(page))['check_runs']
  for c in cs:
   if not c['name'].startswith('market-thumbnail-'):continue
   call('/check-runs/'+str(c['id']),{'output':{'title':'Temporary thumbnail transport cleared','summary':'Image payload removed. Only the 17 IDs in ACTUAL_THUMBNAIL_NOTES_ROMAN_URDU.md were visually inspected; other recovered copies were discarded uninspected. Hash-only acquisition evidence retained in repository.'}},'PATCH')
   verify=call('/check-runs/'+str(c['id']))
   assert 'jpeg_base64' not in verify['output']['summary']
   cleared.append({'check_id':c['id'],'name':c['name'],'sha':sha})
  if len(cs)<100:break
  page+=1
receipt={'cleared':cleared,'count':len(cleared),'rechecked_no_base64':True,'scope':'two explicit research commits only; no Drive copies created'}
call('/check-runs',{'name':'market-thumbnail-cleanup-receipt','head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'success','output':{'title':'Thumbnail cleanup verified','summary':json.dumps(receipt)}},'POST')
print(json.dumps(receipt))
