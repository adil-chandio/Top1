"""Decode current candidate, not a source-frame reconstruction. No listening claim."""
import hashlib,json,subprocess
from pathlib import Path
import imageio_ffmpeg
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path('studio/runtime/gecko/v5-whole-audit')
VIDEO=Path('studio/runtime/gecko/claw-framing-pass/cut/gecko-english-review-cut-v5.mp4')

def main():
 ROOT.mkdir(parents=True,exist_ok=True)
 ff=imageio_ffmpeg.get_ffmpeg_exe()
 p=subprocess.Popen([ff,'-v','error','-i',str(VIDEO),'-map','0:v:0','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 n=540*960*3;count=0;black=[];diffs=[];last=None;samples=[]
 while True:
  raw=p.stdout.read(n)
  if not raw:break
  assert len(raw)==n,'partial frame'
  a=np.frombuffer(raw,dtype=np.uint8).reshape(960,540,3)
  if a.mean()<1:black.append(count)
  small=a[::8,::8].astype(np.int16)
  if last is not None:diffs.append(float(np.abs(small-last).mean()))
  last=small
  if count%24==0:
   im=Image.fromarray(a);im.thumbnail((270,480));samples.append(im.copy())
  count+=1
 errors=p.stderr.read().decode();assert p.wait()==0 and not errors,errors
 sheets=[]
 for start in range(0,len(samples),18):
  group=samples[start:start+18];sheet=Image.new('RGB',(1620,1536),(18,24,29));d=ImageDraw.Draw(sheet)
  for k,im in enumerate(group):
   x=(k%6)*270;y=(k//6)*512;sheet.paste(im,(x,y));d.text((x+8,y+482),f'v5 decoded {start+k:02d}.00s',fill='white')
  path=ROOT/f'chronological-{start//18+1}.jpg';sheet.save(path,quality=92);sheets.append(str(path))
 runs=[];begin=None
 for i,value in enumerate(diffs+[999],1):
  if value<.12 and begin is None:begin=i-1
  elif value>=.12 and begin is not None:
   if i-1-begin>=24:runs.append({'start':round(begin/24,3),'end':round((i-1)/24,3),'meaning':'low raster change, not automatic craft failure'})
   begin=None
 cues=json.loads(Path('research/monarch_cam_gecko_batch4/REVIEW_CAPTION_CUES.json').read_text())['cues']
 flags=[{'start':c['start'],'end':c['end'],'text':c['text'],'cps':round(len(c['text'])/(c['end']-c['start']),2)} for c in cues if len(c['text'])/(c['end']-c['start'])>20 or c['end']-c['start']<.7]
 out={'file':str(VIDEO),'sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),'decoded_frames':count,'full_decode_errors':errors,'nearblack_frames':black,'sample_times_seconds':list(range(len(samples))),'sample_sheets':sheets,'sheets_actually_inspected':False,'low_change_runs':runs,'caption_review_flags':flags,'caption_flag_rule':'over20characters/second OR under0.7s; heuristic, not listening/reading approval','native_playback':False,'listening':False,'final_pass':False}
 Path('research/monarch_cam_gecko_batch5/CURRENT_CANDIDATE_WHOLE_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
