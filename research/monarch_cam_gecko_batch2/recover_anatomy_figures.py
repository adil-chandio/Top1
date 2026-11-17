"""Temporary CC-BY4.0 scientific-reference transport, never a production asset pass."""
import base64,hashlib,io,json,os,urllib.request
from PIL import Image
base='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']
headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
figures={'fig3-digit-IV-multiview':'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/ce3a/13617260/1579b8950185/JOA-9999-0-g007.webp','fig4-digit-IV-SEM':'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/ce3a/13617260/dff809b6e633/JOA-9999-0-g017.webp'}
for name,url in figures.items():
 with urllib.request.urlopen(url,timeout=30) as f:raw=f.read(5000000)
 im=Image.open(io.BytesIO(raw)).convert('RGB');size=im.size;im.thumbnail((2000,2000));b=io.BytesIO();im.save(b,'JPEG',quality=85);copy=b.getvalue();encoded=base64.b64encode(copy).decode()
 for n,start in enumerate(range(0,len(encoded),45000)):
  summary={'figure':name,'part':n,'parts':(len(encoded)+44999)//45000,'base64':encoded[start:start+45000],'source_url':url,'source_size':size,'source_sha256':hashlib.sha256(raw).hexdigest(),'copy_sha256':hashlib.sha256(copy).hexdigest(),'article':'https://pmc.ncbi.nlm.nih.gov/articles/PMC13617260/','credit':'Russell, Delannoy & Garner2026; Journal of Anatomy; DOI10.1111/joa.70251','license':'CC BY4.0 per article; check figure-specific credit before reuse'}
  data={'name':'gecko-anatomy-'+name+'-'+str(n),'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':'Temporary reference transport; cleanup required','summary':json.dumps(summary)}}
  req=urllib.request.Request(base+'/check-runs',data=json.dumps(data).encode(),headers=headers,method='POST')
  with urllib.request.urlopen(req,timeout=30) as f:print(json.load(f)['id'])
