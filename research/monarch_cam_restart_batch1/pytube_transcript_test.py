"""One anonymous request per independent tool; no authentication or routing changes."""
import os,json,tempfile,urllib.request,importlib.metadata,subprocess
from pathlib import Path
kind=os.environ['TEST_KIND'];r={'tool':kind,'video_id':'ZQvfHyfgBtA','media_acquired':False,'frames_decoded':False,'visual_review_complete':False}
try:
 if kind=='pytube':
  from pytube import YouTube
  r['version']=importlib.metadata.version('pytube')
  yt=YouTube('https://www.youtube.com/watch?v='+r['video_id'],use_oauth=False,allow_oauth_cache=False)
  info=yt.vid_info;r['playability_status']=info.get('playabilityStatus',{}).get('status')
  # Do not call age-gate fallback or authenticated methods on refusals.
  if r['playability_status']!='OK':raise RuntimeError('playback_refused')
  streams=yt.streams.filter(only_video=True,file_extension='mp4').order_by('resolution')
  stream=streams.first()
  if not stream or stream.filesize>60000000:raise RuntimeError('no_bounded_stream')
  with tempfile.TemporaryDirectory() as folder:
   path=stream.download(output_path=folder,filename='source.mp4',timeout=20,max_retries=0)
   r['media_acquired']=Path(path).stat().st_size>0
   test=subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',path,'-an','-frames:v','1','-f','null','-'],timeout=25,capture_output=True)
   r['frames_decoded']=test.returncode==0
  r['temporary_media_deleted']=not Path(folder).exists()
 else:
  from youtube_transcript_api import YouTubeTranscriptApi
  r['version']=importlib.metadata.version('youtube-transcript-api')
  transcript=YouTubeTranscriptApi().fetch(r['video_id'],languages=['en'])
  rows=transcript.to_raw_data();r.update(transcript_acquired=True,segments=len(rows),preview=rows[:3],limitation='Captions only, not watching/listening.')
except Exception as e:
 r['error_type']=type(e).__name__
 if hasattr(e,'code'):r['http_status']=e.code
body={'name':kind+'-bounded-execution','head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':'Actual anonymous tool test, not visual-review completion','summary':json.dumps(r)}}
request=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/check-runs',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
with urllib.request.urlopen(request,timeout=30) as response:json.load(response)
