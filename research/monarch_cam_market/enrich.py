"""Second-stage bounded channel inventories and date-ordered discovery; public metadata only."""
import concurrent.futures
import datetime as dt
import json
import subprocess
from pathlib import Path
OUT=Path('research/monarch_cam_market/data')
SEEDS=[
 ('@MinuteEarth','established illustrated-science control'),
 ('@mndiaye_97','established wildlife commentary control'),
 ('@realscience','established biology-documentary control'),
 ('@NaturalWorldFacts','ocean documentary control'),
 ('@daninblue','discovered mimicry breakout candidate'),
 ('@ButWhatGives','discovered animal-explainer breakout candidate'),
 ('@DolphinExplains','discovered smaller ocean-explainer candidate'),
 ('@theoceanatlas','discovered lower-view ocean counterexample'),
 ('@NaturesDarkLab','discovered lower-view adaptation counterexample'),
 ('@PawsyBrain','discovered lower-view animal counterexample'),
 ('@MugExplains','discovered lower-view bear counterexample'),
 ('@WildExplained-b3m','discovered lower-view bear counterexample'),
 ('@Spinosnack','discovered prehistory breakout candidate'),
 ('@ProfessorWildfang','discovered prehistory candidate'),
 ('@EvolutionExplained-n5r','discovered prehistory candidate'),
 ('@Microfaun','discovered prehistoric-human breakout candidate'),
 ('@Inkexplainer96','prehistoric-human breakout comparator'),
 ('@HypotheticallyHQ','prehistoric-human counterpoint'),
 ('@HistoryofHumankind','discovered human-evolution breakout comparator'),
 ('@Zoanfly','ocean/prehistory crossover candidate'),
 ('@ThePaintExplainer','multi-topic illustrated-explainer comparator'),
 ('@GeniusEngineering','discovered mechanism comparator'),
 ('@3dcasuallearning','discovered mechanism comparator'),
 ('@carinfo3d-En','discovered mechanism comparator'),
 ('@GeomapUnveiled25','discovered geography breakout comparator'),
 ('@FactSpark','discovered geography breakout comparator'),
 ('@ZoologyWithWill','encounter commentary candidate from web research'),
 ('@AnimalTheoryTV18','animation candidate from web discovery; not validated'),
 ('@ApexmorphOfficial','prior-research lead requiring independent verification'),
 ('@animalbehaviorcorner7972','search-discovered animal-behavior counterexample'),
]
QUERIES=['animal behavior explained','wildlife documentary animation','animal camouflage explained','ocean animals explained','prehistoric animals explained','ancient humans animation','how things work 3d animation','geography explained animation']
report={'collected_at':dt.datetime.now(dt.timezone.utc).isoformat(),'trusted_session_date':'2026-11-14','status':'running','channels':[],'recent_searches':[],'limits':{'inventory':'up to 30 recent video-tab entries per selected channel, not full catalogue; Shorts tab separate and not collected','selection':'purposeful candidate/control/counterexample set, not random','dates':'approximate relative-date reconstruction if supplied by yt-dlp; not publication API timestamps','growth':'one snapshot is not growth','media':'no actual audiovisual playback; no retention/CTR/RPM evidence','clock':'runner may differ from trusted date; future-estimated dates excluded from age-based comparison'}}
def save():(OUT/'enrichment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
def extract(url):
 try:
  r=subprocess.run(['yt-dlp','--flat-playlist','--playlist-end','30','--dump-single-json','--skip-download','--no-warnings','--socket-timeout','12','--retries','0','--extractor-args','youtubetab:approximate_date',url],capture_output=True,text=True,timeout=65)
  if r.returncode:return {'status':'failed','reason':'public_metadata_unavailable_or_verification_required'}
  d=json.loads(r.stdout)
  # Drop thumbnails and ephemeral renderer details to keep source-control footprint small.
  fields=['id','title','url','webpage_url','channel','channel_id','channel_url','channel_follower_count','uploader','uploader_id','description','duration','view_count','timestamp','upload_date','release_timestamp','availability','live_status']
  keep={k:d.get(k) for k in fields if d.get(k) is not None}
  keep['entries']=[{k:x.get(k) for k in fields if x.get(k) is not None} for x in d.get('entries',[]) if x]
  keep['status']='success';return keep
 except (subprocess.TimeoutExpired,ValueError):return {'status':'failed','reason':'timeout_or_invalid_json'}
def channel(pair):
 handle,why=pair;d=extract('https://www.youtube.com/'+handle+'/videos');return {'requested_handle':handle,'selection_reason':why,'data':d}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for d in pool.map(channel,SEEDS):report['channels'].append(d);save()
def search(q):return {'query':q,'order':'date','data':extract('ytsearchdate25:'+q)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for d in pool.map(search,QUERIES):report['recent_searches'].append(d);save()
report['status']='completed_bounded_attempts';save()
print(json.dumps({'channels_attempted':len(report['channels']),'channels_success':sum(x['data']['status']=='success' for x in report['channels']),'date_searches':len(report['recent_searches'])}))
