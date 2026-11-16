"""Bounded public YouTube research. Never prints API credentials or request URLs."""
import datetime as dt
import json
import os
from pathlib import Path
import time
import urllib.request
import urllib.parse
import urllib.error

QUERIES = [
 ('wildlife_behavior','why bears animal behavior explained'),
 ('wildlife_behavior','animal behavior explained'),
 ('human_wildlife','urban wildlife animals cities explained'),
 ('human_wildlife','wildlife crossings explained'),
 ('adaptations','strange animal adaptations explained'),
 ('adaptations','animal camouflage explained'),
 ('animal_science','animal biology animation'),
 ('animal_science','ocean animals explained'),
 ('prehistory','prehistoric animals explained'),
 ('prehistory','ancient humans animation'),
 ('mechanisms','how things work 3d animation'),
 ('geography','geography explained animation'),
]
OUT = Path(os.getenv('RESEARCH_OUT', 'research/monarch_cam_market/data'))
OUT.mkdir(parents=True, exist_ok=True)
key = next((os.getenv(k) for k in ['YOUTUBE_API_KEY','YTAP1','YTAPI1','YT_KEY','YT_API_KEY'] if os.getenv(k)), None)
report = {'collected_at':dt.datetime.now(dt.timezone.utc).isoformat(), 'trusted_session_date':'2026-11-14', 'status':'running', 'searches':[], 'videos':[], 'channels':[], 'inventories':[], 'comments':[], 'errors':[], 'quota_estimate':0, 'limits':{'search_calls_max':24,'inventory_channels_max':24,'comment_videos_max':12,'coverage':'nonrandom English-relevance convenience sample; not all YouTube','recent_cutoff':'2026-07-01T00:00:00Z','future_publication_cutoff':'2026-11-15T00:00:00Z','growth':'single snapshot cannot measure subscriber growth','format':'duration alone does not establish Shorts status'}}
def save():
 (OUT/'snapshot.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
def api(endpoint, **params):
 report['quota_estimate'] += 100 if endpoint=='search' else 1
 params['key']=key
 req=urllib.request.Request('https://www.googleapis.com/youtube/v3/'+endpoint+'?'+urllib.parse.urlencode(params))
 try:
  with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
 except urllib.error.HTTPError as e:
  try: reason=json.loads(e.read()).get('error',{}).get('errors',[{}])[0].get('reason','unknown')
  except Exception:reason='unparsed'
  report['errors'].append({'endpoint':endpoint,'status':e.code,'reason':reason})
  if e.code in (403,429):raise RuntimeError('API_DENIED_'+str(e.code)+'_'+reason) from None
  return {}
 except (TimeoutError,urllib.error.URLError):
  report['errors'].append({'endpoint':endpoint,'reason':'network_timeout_or_error'});return {}
 finally:time.sleep(.15)
if not key:
 report['status']='blocked_no_configured_secret';save();raise SystemExit(0)
try:
 # Cheap key check: avoid wasting searches when key/quota is unavailable.
 check=api('videos',part='snippet',id='X0whihfTI0Y')
 if not check.get('items'):raise RuntimeError('KEY_CHECK_NO_ITEM')
 ids=set()
 for lane,q in QUERIES:
  for order in ['date','viewCount']:
   d=api('search',part='snippet',q=q,type='video',order=order,maxResults=25,publishedAfter='2026-07-01T00:00:00Z',publishedBefore='2026-11-15T00:00:00Z',relevanceLanguage='en')
   items=d.get('items',[])
   report['searches'].append({'lane':lane,'query':q,'order':order,'returned':len(items),'video_ids':[x['id']['videoId'] for x in items]})
   ids.update(x['id']['videoId'] for x in items);save()
 def batches(seq,n=50):
  seq=list(seq)
  for i in range(0,len(seq),n):yield seq[i:i+n]
 videos={}
 for b in batches(sorted(ids)):
  for v in api('videos',part='snippet,statistics,contentDetails',id=','.join(b)).get('items',[]):videos[v['id']]=v
 channelids={v['snippet']['channelId'] for v in videos.values()}
 for b in batches(sorted(channelids)):
  report['channels']+=api('channels',part='snippet,statistics,contentDetails',id=','.join(b)).get('items',[])
 channels={c['id']:c for c in report['channels']}
 # Inventory selected small-channel candidates, not merely winners. Choice is recorded.
 ranked=sorted(channels.values(),key=lambda c:(int(c.get('statistics',{}).get('subscriberCount',10**10))>250000,-max([int(v.get('statistics',{}).get('viewCount',0)) for v in videos.values() if v['snippet']['channelId']==c['id']] or [0])))
 extra=set()
 for c in ranked[:24]:
  playlist=c.get('contentDetails',{}).get('relatedPlaylists',{}).get('uploads')
  if not playlist:continue
  items=api('playlistItems',part='snippet,contentDetails',playlistId=playlist,maxResults=30).get('items',[])
  vi=[x['contentDetails']['videoId'] for x in items]
  report['inventories'].append({'channel_id':c['id'],'selection':'bounded discovery ranking; small-channel priority, then highest discovered views','video_ids':vi,'limit':30});extra.update(vi)
 for b in batches(sorted(extra-set(videos))):
  for v in api('videos',part='snippet,statistics,contentDetails',id=','.join(b)).get('items',[]):videos[v['id']]=v
 # Avoid turning tiny samples into a success-rate estimate.
 best=sorted(videos.values(),key=lambda v:-int(v.get('statistics',{}).get('viewCount',0)))[:12]
 for v in best:
  d=api('commentThreads',part='snippet',videoId=v['id'],maxResults=30,order='relevance',textFormat='plainText')
  report['comments'].append({'video_id':v['id'],'items':d.get('items',[]),'sample':'up to 30 relevance-ranked top-level comments; not representative'})
 report['videos']=list(videos.values());report['status']='completed_bounded_collection'
except RuntimeError as e:
 report['status']='blocked_or_partial';report['blocker']=str(e)
finally:
 if 'videos' in locals():report['videos']=list(videos.values())
 save()
print(json.dumps({'status':report['status'],'searches':len(report['searches']),'videos':len(report['videos']),'channels':len(report['channels']),'quota_estimate':report['quota_estimate']}))
