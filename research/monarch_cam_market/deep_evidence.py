"""Public about-page provenance and caption attempts. Captions are not visual review."""
import concurrent.futures
import datetime as dt
import json
import re
import urllib.request
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
OUT=Path('research/monarch_cam_market/data')
handles=['@ApexmorphOfficial','@DolphinExplains','@daninblue','@ButWhatGives','@theoceanatlas','@EvolutionExplained-n5r','@Inkexplainer96','@AnimalTheoryTV18']
j=json.loads((OUT/'enrichment.json').read_text())
ids={x['requested_handle']:x['data'].get('channel_id') or x['data'].get('id') for x in j['channels']}
keys={'joinedDateText','joinedDate','viewCountText','subscriberCountText','videoCountText','country','countryText','canonicalChannelUrl','description','channelId','title'}
def extract_named(o,result):
 if isinstance(o,dict):
  for k,v in o.items():
   if k in keys and isinstance(v,(str,dict,list)):
    result.append({'key':k,'value':v})
   extract_named(v,result)
 elif isinstance(o,list):
  for v in o:extract_named(v,result)
def about(h):
 result={'handle':h,'channel_id':ids[h],'source':'public about HTML + public WEB browse endpoint','status':'attempted','evidence':[]}
 try:
  req=urllib.request.Request('https://www.youtube.com/'+h+'/about',headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=20) as r:html=r.read().decode()
  m=re.search(r'(?:var )?ytInitialData\s*=\s*(\{.*?\});',html)
  if m:extract_named(json.loads(m.group(1)),result['evidence'])
  cv=re.search(r'"INNERTUBE_CLIENT_VERSION"\s*:\s*"([^"]+)"',html)
  payload={'context':{'client':{'clientName':'WEB','clientVersion':cv.group(1) if cv else '2.20261114.00.00','hl':'en'}},'browseId':ids[h],'params':'EgVhYm91dA%3D%3D'}
  req=urllib.request.Request('https://www.youtube.com/youtubei/v1/browse',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=20) as r:extract_named(json.load(r),result['evidence'])
  result['status']='retrieved_public_fields'
 except Exception as e:result['status']='partial_or_blocked';result['reason']=type(e).__name__
 return result
videos=['foi5WtXV7E0','Tm8PtCTt2j8','GrtKxfATyTw','49_Ph2q6uIM','A7-bGTOei5M','vTCopBqq8LY']
def transcript(v):
 try:
  t=YouTubeTranscriptApi().fetch(v,languages=['en'])
  return {'video_id':v,'status':'retrieved','language':t.language_code,'generated':t.is_generated,'segments':t.to_raw_data(),'limit':'caption text only; no actual visual/audio review'}
 except Exception as e:return {'video_id':v,'status':'unavailable','reason':type(e).__name__}
report={'collected_at':dt.datetime.now(dt.timezone.utc).isoformat(),'about':[],'captions':[]}
with concurrent.futures.ThreadPoolExecutor(4) as pool:report['about']=list(pool.map(about,handles))
with concurrent.futures.ThreadPoolExecutor(3) as pool:report['captions']=list(pool.map(transcript,videos))
(OUT/'deep_evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'about_status':[x['status'] for x in report['about']],'caption_status':[x['status'] for x in report['captions']]}))
