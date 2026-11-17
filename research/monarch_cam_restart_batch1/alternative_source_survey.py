"""Bounded public-source discovery, without downloading media or bypassing access controls."""
import json,os,urllib.request,urllib.parse,concurrent.futures,re

def get(url):
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'MonarchCam-reference-research/1.0'})
  with urllib.request.urlopen(req,timeout=25) as f:
   raw=f.read(2500000);content=f.headers.get('Content-Type','')
  if 'json' in content:return {'url':url,'data':json.loads(raw)}
  text=raw.decode('utf-8','replace')
  return {'url':url,'media_links':list(dict.fromkeys(re.findall(r'''(?:https?:)?//[^\s<>"']+\.(?:mp4|webm|m3u8|gif)(?:\?[^\s<>"']*)?''',text)))[:30],'youtube_ids':list(dict.fromkeys(re.findall(r'(?:embed/|watch\?v=)([\w-]{11})',text)))[:20]}
 except Exception as e:return {'url':url,'error_type':type(e).__name__,'status':getattr(e,'code',None)}
queries=['creator:"Animagraffs"','title:"How a Car Engine Works"','title:"The Densest City on Earth"','creator:"Zack D"','creator:"fern" AND mediatype:movies','creator:"Branch Education"','creator:"Real Science" AND mediatype:movies','creator:"Veritasium" AND mediatype:movies']
urls=['https://archive.org/advancedsearch.php?'+urllib.parse.urlencode({'q':q,'output':'json','rows':8,'fl[]':['identifier','title','mediatype','creator']},doseq=True) for q in queries]
urls += ['https://huggingface.co/api/datasets?'+urllib.parse.urlencode({'search':s,'limit':8}) for s in ['animagraffs','zack','youtube video','Video-MME']]
urls += ['https://animagraffs.com/how-a-car-engine-works/','https://animagraffs.com/how-a-handgun-works/','https://www.zackdfilms.com/']
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(get,urls))
# Dataset metadata and archive search results only. No bulk dataset download.
r={'method':'public_creator_archive_dataset_discovery','media_downloaded':False,'visual_review_complete':False,'results':rows}
summary=json.dumps(r)
if len(summary)>60000:summary=summary[:59000]+' [TRUNCATED]'
body={'name':'alternative-public-source-survey','head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':'Creator sites, archive search and Hugging Face actually requested','summary':summary}}
req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/check-runs',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=30) as f:json.load(f)
