"""Bounded legitimate-publisher media discovery; no access-control bypass."""
import json,os,re,urllib.request
URL='https://www.annualreviews.org/content/journals/10.1146/annurev-ecolsys-120213-091839'
req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0 (research reference inspection)'})
error=None
try:
 with urllib.request.urlopen(req,timeout=45) as f: html=f.read(3000000).decode('utf-8','replace')
except Exception as exc:
 html='';error={'type':type(exc).__name__,'message':str(exc)[:1000]}
 # Diagnostic only: do not retry alternate hosts, challenge endpoints or authentication.
blocks=re.findall(r'<video\b.*?</video>',html,re.S|re.I)
media=[{'index':i+1,'html':b[:8000]} for i,b in enumerate(blocks)]
report={'source_url':URL,'retrieval_error':error,'video_blocks':media,'media_links':sorted(set(re.findall(r'''["']([^"']+\.(?:mp4|mov|webm)(?:\?[^"']*)?)["']''',html,re.I)))[:30],'pixels_inspected':False,'rights':'Publisher: Copyright2014 Annual Reviews, all rights reserved. Research only, no production reuse.'}
base='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']
data={'name':'gecko-live-motion-discovery','head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':'Publisher media source discovery; NOT watched','summary':json.dumps(report)[:60000]}}
r=urllib.request.Request(base+'/check-runs',data=json.dumps(data).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(r,timeout=30) as f: print(json.load(f)['id'])
