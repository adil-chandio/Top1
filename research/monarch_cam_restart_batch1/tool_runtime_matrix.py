"""Bounded real execution of suggested tools. No credentials supplied to tools.
Douyin executes exact YouTube function with normal HTTPS adapter, not recorder loop.
"""
import os,json,urllib.request,urllib.error,subprocess,tempfile,zipfile,io,ast,asyncio,re,time
from pathlib import Path
KIND=os.environ['TOOL_KIND'];r={'tool':KIND,'media_verified':False,'visual_review_complete':False}
def github_file(repo,path,ref):
 req=urllib.request.Request(f'https://api.github.com/repos/{repo}/contents/{path}?ref={ref}',headers={'Accept':'application/vnd.github.raw+json','User-Agent':'MonarchResearch'})
 with urllib.request.urlopen(req,timeout=30) as response:return response.read().decode()
try:
 if KIND=='douyin':
  source=github_file('ihmily/DouyinLiveRecorder','src/spider.py','add187f8d8c7ff7d231fcbee45cbb4f1ed247d3a')
  tree=ast.parse(source);names=['get_youtube_stream_url','get_play_url_list'];nodes=[n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name in names]
  for n in nodes:n.decorator_list=[]
  async def async_req(url,**kw):
   if kw.get('proxy_addr') or kw.get('proxy'):raise ValueError('No proxy')
   def request():
    req=urllib.request.Request(url,headers=kw.get('headers',kw.get('header',{})))
    with urllib.request.urlopen(req,timeout=25) as response:return response.read(4000000).decode()
   return await asyncio.to_thread(request)
  env={'async_req':async_req,'OptionalStr':str|None,'List':list,'re':re,'json':json}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'reviewed-youtube-handler','exec'),env)
  out=asyncio.run(asyncio.wait_for(env['get_youtube_stream_url']('https://www.youtube.com/watch?v=ZQvfHyfgBtA'),timeout=45))
  r.update(execution='exact isolated YouTube handler; standard HTTPS adapter; no decorator',result={k:v for k,v in out.items() if k not in ('m3u8_url','play_url_list')},stream_returned=bool(out.get('m3u8_url')))
 elif KIND=='last30days':
  with tempfile.TemporaryDirectory() as folder:
   url='https://codeload.github.com/mvanhorn/last30days-skill/zip/9cee9178210ee8492fac558df89855ef334adbcc'
   with urllib.request.urlopen(url,timeout=45) as response:data=response.read(60000000)
   with zipfile.ZipFile(io.BytesIO(data)) as archive:archive.extractall(folder)
   script=next(Path(folder).glob('*/skills/last30days/scripts/last30days.py'))
   env={k:v for k,v in os.environ.items() if not any(s in k for s in ('TOKEN','API_KEY','SECRET'))};env.update(HOME=folder,LAST30DAYS_MEMORY_DIR=folder+'/memory',LAST30DAYS_YOUTUBE_BACKEND='yt-dlp')
   command=['python',str(script),'educational animation channels','--search','youtube','--emit=json','--save-dir',folder+'/results']
   p=subprocess.run(command,capture_output=True,text=True,timeout=150,env=env)
   r.update(execution='actual CLI YouTube-only, no paid provider keys',exit_code=p.returncode,stdout_tail=p.stdout[-13000:],stderr_tail=p.stderr[-5000:])
 elif KIND=='rsshub':
  p=subprocess.run(['docker','run','-d','--rm','--name','rsshub-test','-p','127.0.0.1:1200:1200','diygod/rsshub:latest'],capture_output=True,text=True,timeout=200)
  r['container_started']=p.returncode==0
  if p.returncode==0:
   # Startup allowance, then one actual channel-feed request; no rotating instances.
   time.sleep(15)
   try:
    with urllib.request.urlopen('http://127.0.0.1:1200/youtube/channel/UCnZeeKO8qVdtkrA4-uKhtTw',timeout=80) as response:
     text=response.read(1500000).decode()
     import xml.etree.ElementTree as ET
     def parse_feed(text):
      channel=ET.fromstring(text).find('channel')
      return {'channel':channel.findtext('title'),'items':[{'title':i.findtext('title'),'url':i.findtext('link'),'feed_date_unverified':i.findtext('pubDate')} for i in channel.findall('item')[:12]]}
     r.update(http_status=response.status,feed_item_count=text.count('<item>'),feeds=[parse_feed(text)],date_warning='Feed dates may be reconstructed from relative ages; verify exact upload dates independently.')
     for handle in ['fern-tv','zackdfilms','neoexplains','realscience','veritasium','BranchEducation']:
      try:
       with urllib.request.urlopen('http://127.0.0.1:1200/youtube/user/@'+handle,timeout=25) as other:r['feeds'].append(parse_feed(other.read(1500000).decode()))
      except Exception as exc:r.setdefault('feed_failures',[]).append({'handle':handle,'error_type':type(exc).__name__})
   except urllib.error.HTTPError as e:r.update(http_status=e.code,response_excerpt=e.read(4500).decode(errors='replace'))
   finally:subprocess.run(['docker','stop','rsshub-test'],capture_output=True,timeout=30)
  else:r['startup_error']=p.stderr[-2500:]
except Exception as e:r['error_type']=type(e).__name__
finally:
 body={'name':KIND+'-actual-runtime-receipt','head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':'Actual bounded runtime, not reference review','summary':json.dumps(r)}}
 req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/check-runs',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as response:json.load(response)
