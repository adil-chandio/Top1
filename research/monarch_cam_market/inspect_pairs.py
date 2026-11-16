"""Bounded public watch-page metadata and thumbnail inspection; no video downloads."""
import concurrent.futures
import datetime as dt
import json
from pathlib import Path
import urllib.request

BASE=Path('research/monarch_cam_market')
PAIRS=[('ocean_winner','Tm8PtCTt2j8'),('ocean_second_winner','foi5WtXV7E0'),('ocean_weak','leLeWBxhNa0'),('ocean_middle','rq6n-33dK8Q'),('human_winner','49_Ph2q6uIM'),('human_repeat_winner','SD7XyG2wd1k'),('human_weak','6TzPQ0046lw'),('human_recent','m10wP37tWp4'),('animal_new_weak','A7-bGTOei5M'),('bear_weak','vTCopBqq8LY')]

def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept-Language':'en-US,en;q=0.9'})
 with urllib.request.urlopen(req,timeout=25) as r:return r.read()

def extract_object(html,marker):
 start=html.find(marker)
 if start<0:return None
 start=html.find('{',start+len(marker))
 if start<0:return None
 try:return json.JSONDecoder().raw_decode(html[start:])[0]
 except ValueError:return None

def inspect(pair):
 label,vid=pair
 result={'label':label,'video_id':vid,'url':'https://www.youtube.com/watch?v='+vid,'status':'attempted','limits':'No video or audio downloaded. Thumbnail is packaging evidence, not film-quality evidence.'}
 try:
  html=fetch(result['url']+'&hl=en').decode()
  p=extract_object(html,'var ytInitialPlayerResponse =') or extract_object(html,'ytInitialPlayerResponse =')
  if p:
   d=p.get('videoDetails',{});m=p.get('microformat',{}).get('playerMicroformatRenderer',{})
   result.update({'status':'player_metadata_retrieved','details':{k:d.get(k) for k in ['videoId','title','lengthSeconds','channelId','shortDescription','viewCount','author','isLiveContent']},'microformat':{k:m.get(k) for k in ['publishDate','uploadDate','category','isFamilySafe','isUnlisted','ownerChannelName']},'playability':p.get('playabilityStatus',{}).get('status'),'caption_tracks':[{k:t.get(k) for k in ['name','languageCode','kind','vssId']} for t in p.get('captions',{}).get('playerCaptionsTracklistRenderer',{}).get('captionTracks',[])]})
  else:result['status']='no_player_json'
 except Exception as e:result['status']='watch_page_failed';result['reason']=type(e).__name__
 try:
  path=BASE/'packaging'/f'{label}_{vid}.jpg';path.parent.mkdir(exist_ok=True)
  data=fetch('https://i.ytimg.com/vi/'+vid+'/hqdefault.jpg')
  if len(data)>1000 and data[:2]==b'\xff\xd8':path.write_bytes(data);result['thumbnail_file']=str(path)
 except Exception as e:result['thumbnail_error']=type(e).__name__
 return result

if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(3) as pool:rows=list(pool.map(inspect,PAIRS))
 report={'collected_at':dt.datetime.now(dt.timezone.utc).isoformat(),'trusted_session_date':'2026-11-14','selection':'Purposive matched-channel winners and lower-view counterexamples, not age controlled.','videos':rows}
 (BASE/'data/paired_inspection.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
 print(json.dumps([{'id':r['video_id'],'status':r['status'],'thumbnail':bool(r.get('thumbnail_file'))} for r in rows]))
