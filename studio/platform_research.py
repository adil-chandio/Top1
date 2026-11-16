"""YouTube-first research tools. Public access only; no auth/DRM/geo bypass.
Discovery/metadata are NOT viewing/listening. Media extracts are reference-only.
All generated files default to ignored studio/runtime, never source control.
"""
import argparse,datetime as dt,hashlib,json,os,re,shutil,statistics,subprocess,sys
from pathlib import Path
from urllib.parse import urlparse,parse_qs

ROOT=Path(__file__).resolve().parents[1]
STAGE_QUESTIONS={
 'intelligence':'Find direct competitors, topic winners, adjacent craft and packaging references; compare public performance without inventing private analytics.',
 'idea':'Which audience question and original angle is supported by relevant long-form and Shorts examples?',
 'story':'Inspect actual hook, information sequence, complication and payoff; distinguish observation from causal hypothesis.',
 'script':'Compare narration/reveal timing against picture, not transcript alone. Produce original edit/sound blueprint.',
 'feasibility':'Inspect selected reference segments for staging, movement, animation, visual hierarchy and sonic perspective; test the hardest relevant principle.',
 'production':'Resolve a specific editing/animation/compositing/sound problem with timestamped references; do not endlessly browse.',
 'qc':'Compare exact produced media to inspected references: picture-only, audio-only and combined. Record defects, not generic praise.',
 'packaging':'Inspect actual thumbnail and title as a pair and whether delivered content fulfills the promise.',
 'delivery':'Recheck provenance/rights and final artifact identity; platform research never grants reuse rights.'}
LANES=('direct_competitor','topic_winner','adjacent_craft','packaging')

def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):
 from studio.pipeline import save
 save(path,data)

def video_url(value):
 if re.fullmatch(r'[A-Za-z0-9_-]{11}',value):vid=value
 else:
  p=urlparse(value)
  if p.scheme!='https' or p.username or p.password or p.port not in (None,443):raise ValueError('HTTPS YouTube URL required')
  host=p.hostname
  if host=='youtu.be':vid=p.path.strip('/')
  elif host in ('youtube.com','www.youtube.com','m.youtube.com'):
   parts=p.path.strip('/').split('/')
   vid=parse_qs(p.query).get('v',[''])[0] if p.path=='/watch' else (parts[1] if len(parts)==2 and parts[0] in ('shorts','embed') else '')
  else:raise ValueError('only YouTube video URLs accepted')
 if not re.fullmatch(r'[A-Za-z0-9_-]{11}',vid):raise ValueError('invalid video ID')
 return 'https://www.youtube.com/watch?v='+vid

def channel_url(value,tab='videos'):
 p=urlparse(value)
 if p.scheme!='https' or p.netloc not in ('www.youtube.com','youtube.com'):raise ValueError('public YouTube channel required')
 path=p.path.rstrip('/')
 if not re.fullmatch(r'/(@[A-Za-z0-9_.-]+|channel/UC[A-Za-z0-9_-]{22})(/(videos|shorts))?',path):raise ValueError('use channel ID or handle')
 path=re.sub(r'/(videos|shorts)$','',path)
 if tab not in ('videos','shorts'):raise ValueError('invalid channel tab')
 return 'https://www.youtube.com'+path+'/'+tab

def ytdlp(args,timeout=90):
 env=os.environ.copy();local=ROOT/'.local-motion'
 env['PYTHONPATH']=str(local)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
 runtime=['--js-runtimes','node'] if shutil.which('node') else []
 command=[sys.executable,'-m','yt_dlp',*runtime,'--ignore-config','--no-cache-dir','--socket-timeout','12','--retries','0','--extractor-retries','0',*args]
 proc=subprocess.run(command,capture_output=True,text=True,env=env,timeout=timeout)
 if proc.returncode:raise RuntimeError('public_platform_access_failed: '+proc.stderr[-1800:])
 return json.loads(proc.stdout)

def metadata(raw):
 vid=raw.get('id','');url=video_url(vid)
 # Deliberately omit signed format URLs, cookies and private payloads from saved evidence.
 keys=('id','title','channel','channel_id','channel_url','duration','view_count','like_count','comment_count','upload_date','timestamp','description','thumbnail','availability','live_status','width','height')
 return {'url':url,'checked_at':now(),'access':'metadata_only','data':{k:raw.get(k) for k in keys},'limits':['No CTR/retention/watch-time available from public metadata','Views do not prove why a video performed','No video viewing or audio listening claimed']}

def discover(query,limit=10):
 if not query.strip() or len(query)>400 or not 1<=limit<=20:raise ValueError('bounded query and limit 1–20 required')
 raw=ytdlp(['--flat-playlist','--playlist-end',str(limit),'--dump-single-json','--skip-download','--',f'ytsearch{limit}:{query}'])
 return {'query':query,'checked_at':now(),'access':'discovery_only','candidates':[metadata(x) for x in raw.get('entries',[]) if x and re.fullmatch(r'[A-Za-z0-9_-]{11}',x.get('id',''))]}

def inspect_video(url):return metadata(ytdlp(['--no-playlist','--skip-download','--dump-single-json','--',video_url(url)]))
def inspect_channel(url,tab='videos',limit=12):
 if not 1<=limit<=30:raise ValueError('limit 1–30 required')
 target=channel_url(url,tab)
 raw=ytdlp(['--flat-playlist','--skip-download','--playlist-end',str(limit),'--dump-single-json','--',target])
 return {'url':target,'checked_at':now(),'format_lane':tab,'access':'channel_listing_only','entries':[metadata(x) for x in raw.get('entries',[]) if x and re.fullmatch(r'[A-Za-z0-9_-]{11}',x.get('id',''))]}

def baseline(target,comparables):
 """Public outlier hint only, same-channel/format/age cohort supplied explicitly."""
 required=('channel_id','format','age_band','views','id')
 if any(k not in target for k in required):raise ValueError('target cohort fields missing')
 cohort=[x for x in comparables if all(k in x for k in required) and x['id']!=target['id'] and all(x[k]==target[k] for k in ('channel_id','format','age_band')) and isinstance(x['views'],(int,float)) and x['views']>=0]
 cohort=list({x['id']:x for x in cohort}.values())
 if len(cohort)<5:raise ValueError('at least five distinct comparable uploads required')
 if not isinstance(target['views'],(int,float)) or target['views']<0:raise ValueError('invalid target views')
 median=statistics.median(x['views'] for x in cohort)
 return {'sample_size':len(cohort),'median_views':median,'relative_views':target['views']/median if median else None,'label':'public_performance_hint_not_causal_or_private_analytics'}

def import_evidence(out,url,content,kind,method,lane):
 """Save actual web_search/fetch_page or operator results without upgrading access level."""
 if kind not in ('search_results','page_text','transcript','thumbnail'):raise ValueError('import media via sample, not a text assertion')
 if lane not in LANES or not method.strip():raise ValueError('lane and actual tool/method required')
 url=video_url(url);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 source=Path(content).resolve()
 if not source.is_file() or not source.stat().st_size:raise ValueError('nonempty captured evidence required')
 # Preserve evidence bytes rather than a mutable external path.
 target=out/('capture'+source.suffix);target.write_bytes(source.read_bytes())
 record={'url':url,'lane':lane,'checked_at':now(),'kind':kind,'method':method,'path':target.name,'sha256':digest(target),'viewed_video':False,'listened_audio':False}
 write(out/'evidence.json',record);return record

def acquire(url,out,start,duration,rights_basis):
 """Public permitted reference segment only. No account cookies, DRM or anti-bot bypass."""
 from studio.media import ffmpeg_command
 if not rights_basis.strip():raise ValueError('actual lawful reference acquisition basis required')
 if start<0 or not 0<duration<=60:raise ValueError('bounded segment required')
 url=video_url(url);out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise ValueError('new empty acquisition folder required')
 out.mkdir(parents=True,exist_ok=True);ffmpeg=ffmpeg_command()
 if not ffmpeg:raise ValueError('FFmpeg required')
 raw=ytdlp(['--no-playlist','--no-simulate','--dump-single-json','--ffmpeg-location',ffmpeg,'--download-sections',f'*{start}-{start+duration}',
            '--max-filesize','25M','--limit-rate','2M','-f','worst[height<=480]/worst','--merge-output-format','mp4','-o',str(out/'reference.%(ext)s'),'--',url],timeout=240)
 record=metadata(raw);record.update({'access':'segment_acquired_not_inspected','source_start':start,'duration_requested':duration,'rights_basis':rights_basis,'reuse_in_production':False,'files':[{'path':p.name,'sha256':digest(p)} for p in out.glob('reference.*') if p.is_file() and p.suffix not in ('.part','.ytdl')]})
 if not record['files']:raise ValueError('extractor did not produce a complete reference segment')
 write(out/'acquisition.json',record);return record

def sample(media,out,url,start,duration,rights_basis):
 """Extract bounded local reference media. Never download a competitor library.
 User/operator must possess permission/lawful analysis basis; not a reuse licence.
 """
 from studio.media import ffmpeg_command
 if not rights_basis.strip():raise ValueError('actual lawful acquisition/analysis basis required')
 if start<0 or not 0<duration<=60:raise ValueError('segment must be 0–60 seconds with nonnegative start')
 media=Path(media).resolve();out=Path(out).resolve()
 if not media.is_file() or not media.stat().st_size:raise ValueError('actual local media file required')
 url=video_url(url);ffmpeg=ffmpeg_command()
 if not ffmpeg:raise ValueError('FFmpeg required')
 if out.exists() and any(out.iterdir()):raise ValueError('new empty segment folder required')
 out.mkdir(parents=True,exist_ok=True)
 # One frame/second for orientation only; motion requires actual clip inspection.
 prefix=[ffmpeg,'-nostdin','-v','error','-xerror','-protocol_whitelist','file,pipe,crypto','-ss',str(start),'-i',str(media),'-t',str(duration)]
 subprocess.run(prefix+['-map','0:v:0','-vf','fps=1,scale=640:-2','-frames:v',str(max(1,int(duration)) ),str(out/'frame-%03d.jpg')],check=True,timeout=120,capture_output=True)
 subprocess.run(prefix+['-map','0:v:0','-map','0:a?','-vf','scale=640:-2','-c:v','libx264','-preset','fast','-crf','23','-c:a','aac',str(out/'segment.mp4')],check=True,timeout=180,capture_output=True)
 probe=subprocess.run([ffmpeg,'-nostdin','-v','error','-i',str(out/'segment.mp4'),'-progress','pipe:1','-f','null','-'],check=True,timeout=120,capture_output=True,text=True)
 times=re.findall(r'out_time_us=(\d+)',probe.stdout)
 actual=max((int(x)/1000000 for x in times),default=0)
 if actual<=0:raise ValueError('empty segment; source timestamp unavailable')
 # Optional audio stream; failed audio extraction is not disguised as listening evidence.
 audio=subprocess.run(prefix+['-vn','-map','0:a:0','-c:a','pcm_s16le',str(out/'audio.wav')],timeout=120,capture_output=True)
 if audio.returncode:
  (out/'audio.wav').unlink(missing_ok=True)
 files=[{'path':p.name,'sha256':digest(p)} for p in sorted(out.iterdir()) if p.is_file()]
 record={'url':url,'source_sha256':digest(media),'checked_at':now(),'source_start':start,'duration_requested':duration,'duration_actual':actual,'rights_basis':rights_basis,'reuse_in_production':False,'audio_extracted':audio.returncode==0,'files':files,'viewed_video':False,'listened_audio':False,'note':'Extraction only. Open actual clip for motion and actually hear audio before recording observations. Frames alone are not motion review.'}
 write(out/'media_evidence.json',record);return record

def observation(out,record):
 """Timestamped human/equipped-agent observation tied to unchanged captured media."""
 out=Path(out);manifest=json.loads((out/'media_evidence.json').read_text())
 for item in manifest['files']:
  path=out/item['path']
  if not path.is_file() or digest(path)!=item['sha256']:raise ValueError('reference evidence changed')
 required=('executor','mode','start','end','observation','interpretation','application','do_not_copy','method')
 if any(not str(record.get(k,'' )).strip() for k in required):raise ValueError('complete specific breakdown required')
 if record['mode'] not in ('picture','audio','combined'):raise ValueError('invalid inspection mode')
 if not 0<=record['start']<record['end']<=min(manifest['duration_requested'],manifest['duration_actual']):raise ValueError('segment-relative timestamps out of range')
 if record['mode'] in ('audio','combined') and not manifest['audio_extracted']:raise ValueError('audio unavailable')
 if record.get('actually_inspected') is not True:raise ValueError('actual inspection attestation required')
 if record['method'] in ('transcript','metadata','page_text','waveform'):raise ValueError('text/metrics are not audiovisual inspection')
 path=out/'observations.json';records=json.loads(path.read_text()) if path.exists() else []
 records.append({**record,'checked_at':now(),'media_manifest_sha256':digest(out/'media_evidence.json'),'source_start':manifest['source_start']+record['start'],'source_end':manifest['source_start']+record['end']})
 write(path,records);return records[-1]

def packet(stage,job=None):
 if stage not in STAGE_QUESTIONS:raise ValueError('unknown stage')
 return {'stage':stage,'question':STAGE_QUESTIONS[stage],'priority':['youtube_long','youtube_shorts','instagram_reels','tiktok'],'lanes':list(LANES),'tools':{'discover':'python -m studio.platform_research discover QUERY --out FILE','video':'python -m studio.platform_research inspect URL --out FILE','channel':'python -m studio.platform_research channel URL --tab videos --out FILE','capture':'python -m studio.platform_research capture URL --content ACTUAL_TOOL_CAPTURE --kind page_text --method fetch_page --lane topic_winner --out FOLDER','acquire':'python -m studio.platform_research acquire URL --start 0 --duration 15 --rights-basis ACTUAL_BASIS --out FOLDER','sample':'python -m studio.platform_research sample LOCAL_PERMITTED_MEDIA --url URL --start 0 --duration 15 --rights-basis ACTUAL_BASIS --out FOLDER','observe':'python -m studio.platform_research observe FOLDER --record ACTUAL_BREAKDOWN.json'},'fallback':'If direct public extractor fails, use available web_search/fetch_page for discovery/text and preserve exact access labels. Move AV task to an authorized media-capable runner; never forge playback or use bypass proxies. IG/TikTok are secondary manual/browser research lanes, not implemented downloader adapters.','stopping_rule':'Bound search to a specific unresolved question; shortlist relevant evidence, make a decision and test it. No endless feed browsing.','artifact_requirement':'Attach platform evidence and timestamped findings as ordinary verified artifacts; text cannot clear audiovisual release gates.','job_directory':str(job) if job else None}

def verify_bundle(job,stage,result):
 """Enforce AV evidence at proof/production/QC for briefs opting into this policy.
 File integrity and attestations are enforced, not the truth of human perception.
 """
 if stage not in ('feasibility','production','qc'):return
 job=Path(job);brief=job/'creative_brief.json'
 if not brief.exists() or not json.loads(brief.read_text()).get('platform_reference_policy',{}).get('require_av_before_production'):return
 from studio.pipeline import owned
 refs=result.get('platform_references',[])
 if not refs:raise ValueError('YouTube-first audiovisual reference bundle required')
 artifacts={x['path']:x['sha256'] for x in result['artifacts']}
 for ref in refs:
  if ref.get('lane') not in LANES or ref.get('format') not in ('youtube_long','youtube_shorts','instagram_reels','tiktok'):raise ValueError('reference lane/format required')
  if not ref.get('selection_reason') or not ref.get('applied_decision'):raise ValueError('reference must influence a specific decision')
  mp=ref['media_manifest'];op=ref['observations']
  for path in (mp,op):
   if path not in artifacts or digest(owned(job,path))!=artifacts[path]:raise ValueError('reference evidence not in verified artifacts')
  media_path=owned(job,mp);manifest=json.loads(media_path.read_text());notes=json.loads(owned(job,op).read_text())
  video_url(manifest['url'])
  if not manifest.get('audio_extracted'):raise ValueError('reference audio evidence required')
  for item in manifest['files']:
   p=owned(job,str(media_path.parent/item['path']))
   rel=str(p.relative_to(job.resolve()))
   if rel not in artifacts or artifacts[rel]!=item['sha256'] or digest(p)!=item['sha256']:raise ValueError('reference media missing/changed')
  modes=set()
  for note in notes:
   if note.get('media_manifest_sha256')!=digest(media_path) or note.get('actually_inspected') is not True:raise ValueError('reference observation not bound to actual evidence')
   if not note.get('executor') or not note.get('observation') or not note.get('application') or note.get('method') in (None,'','transcript','metadata','page_text','waveform'):raise ValueError('specific AV inspection required')
   if not 0<=note['start']<note['end']<=min(manifest['duration_requested'],manifest['duration_actual']):raise ValueError('reference timestamp out of range')
   modes.add(note.get('mode'))
  if not ('combined' in modes or {'picture','audio'}<=modes):raise ValueError('both picture and actual audio observations required')
 if not any(r['format'] in ('youtube_long','youtube_shorts') for r in refs):raise ValueError('YouTube reference required for YouTube channel')

def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
 for name in ('discover','inspect','channel'):
  a=s.add_parser(name);a.add_argument('target');a.add_argument('--out',required=True)
  if name in ('discover','channel'):a.add_argument('--limit',type=int,default=10)
  if name=='channel':a.add_argument('--tab',choices=['videos','shorts'],default='videos')
 a=s.add_parser('baseline');a.add_argument('--target',required=True);a.add_argument('--comparables',required=True);a.add_argument('--out',required=True)
 a=s.add_parser('packet');a.add_argument('stage');a.add_argument('--out',required=True)
 a=s.add_parser('capture');a.add_argument('url');a.add_argument('--content',required=True);a.add_argument('--kind',required=True);a.add_argument('--method',required=True);a.add_argument('--lane',required=True);a.add_argument('--out',required=True)
 a=s.add_parser('sample');a.add_argument('media');a.add_argument('--url',required=True);a.add_argument('--start',type=float,default=0);a.add_argument('--duration',type=float,default=15);a.add_argument('--rights-basis',required=True);a.add_argument('--out',required=True)
 a=s.add_parser('acquire');a.add_argument('url');a.add_argument('--start',type=float,default=0);a.add_argument('--duration',type=float,default=15);a.add_argument('--rights-basis',required=True);a.add_argument('--out',required=True)
 a=s.add_parser('observe');a.add_argument('folder');a.add_argument('--record',required=True)
 a=p.parse_args()
 try:
  if a.cmd=='discover':result=discover(a.target,a.limit)
  elif a.cmd=='inspect':result=inspect_video(a.target)
  elif a.cmd=='channel':result=inspect_channel(a.target,a.tab,a.limit)
  elif a.cmd=='baseline':result=baseline(json.loads(Path(a.target).read_text()),json.loads(Path(a.comparables).read_text()))
  elif a.cmd=='packet':result=packet(a.stage)
  elif a.cmd=='capture':result=import_evidence(a.out,a.url,a.content,a.kind,a.method,a.lane)
  elif a.cmd=='acquire':result=acquire(a.url,a.out,a.start,a.duration,a.rights_basis)
  elif a.cmd=='sample':result=sample(a.media,a.out,a.url,a.start,a.duration,a.rights_basis)
  else:result=observation(a.folder,json.loads(Path(a.record).read_text()))
 except (ValueError,RuntimeError,subprocess.SubprocessError) as exc:
  result={'status':'access_or_validation_failed','checked_at':now(),'error':str(exc),'viewed_video':False,'listened_audio':False}
  if hasattr(a,'out'):write(Path(a.out) if a.cmd in ('discover','inspect','channel','packet','baseline') else Path(a.out)/'failure.json',result)
  print(json.dumps(result,indent=2));raise SystemExit(2)
 if a.cmd in ('discover','inspect','channel','packet','baseline'):write(a.out,result)
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
