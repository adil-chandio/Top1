"""Bounded caption readability correction, preserve v5 picture mechanism and AAC stream."""
import sys,json,subprocess,hashlib,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'monarch_cam_gecko_batch4'))
from build_external_feature_cut import picture as prior_picture,fonts,BG,MUTED,WHITE
from PIL import Image,ImageDraw
import imageio_ffmpeg
OUT=Path('studio/runtime/gecko/caption-readability');OUT.mkdir(parents=True,exist_ok=True)
BASE=Path('research/monarch_cam_gecko_batch5')
old=json.loads(Path('research/monarch_cam_gecko_batch4/REVIEW_CAPTION_CUES.json').read_text())['cues']
# Merge short orphan words and contiguous sentence fragments; preserve every word.
merge_pairs={0:1,4:5,9:10,26:27,32:33}
CUES=[];i=0
while i<len(old):
 c=old[i].copy()
 if i in merge_pairs:
  c['text']+=' '+old[i+1]['text'];c['end']=old[i+1]['end'];i+=1
 CUES.append(c);i+=1
for i,c in enumerate(CUES):
 limit=CUES[i+1]['start'] if i+1<len(CUES) else 63.68
 c['end']=round(min(limit,max(c['end'],c['start']+max(.7,len(c['text'])/20))),3)
assert all(c['end']-c['start']>=.7 and len(c['text'])/(c['end']-c['start'])<=20.01 for c in CUES)
assert re.findall(r"[a-z]+(?:'[a-z]+)?",' '.join(c['text'] for c in CUES).lower())==re.findall(r"[a-z]+(?:'[a-z]+)?",' '.join(c['text'] for c in old).lower())

def picture(t):
 im=prior_picture(t);d=ImageDraw.Draw(im)
 d.rectangle((300,20,539,50),fill=BG);d.text((320,24),'SCHEMATIC REVIEW v6',font=fonts[14],fill=MUTED)
 d.rectangle((0,813,539,920),fill=BG)
 cue=next((c for c in CUES if c['start']<=t<c['end']),None)
 if cue:
  d.rectangle((16,818,524,915),fill='#07111b');lines=[];s=''
  for word in cue['text'].split():
   test=(s+' '+word).strip()
   if d.textbbox((0,0),test,font=fonts[24])[2]>470:lines.append(s);s=word
   else:s=test
  if s:lines.append(s)
  assert len(lines)<=3
  for i,line in enumerate(lines):
   width=d.textbbox((0,0),line,font=fonts[24])[2];d.text(((540-width)/2,833+i*29),line,font=fonts[24],fill=WHITE)
 return im

def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

def main():
 ff=imageio_ffmpeg.get_ffmpeg_exe();src='studio/runtime/gecko/claw-framing-pass/cut/gecko-english-review-cut-v5.mp4';file=OUT/'gecko-english-review-cut-v6.mp4'
 (BASE/'READABILITY_CAPTION_CUES.json').write_text(json.dumps({'method':'exact script regrouped; approximate alignment; no independent listening approval','cues':CUES,'target_max_cps':20,'minimum_duration':.7},indent=2)+'\n')
 (OUT/'english-captions-review-v6.srt').write_text('\n\n'.join(f"{i}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i,c in enumerate(CUES,1))+'\n')
 with (OUT/'encode.log').open('wb') as log:
  p=subprocess.Popen([ff,'-y','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r','24','-i','-','-i',src,'-map','0:v','-map','1:a:0','-c:v','libx264','-crf','20','-preset','veryfast','-pix_fmt','yuv420p','-c:a','copy','-t','66','-movflags','+faststart',str(file)],stdin=subprocess.PIPE,stderr=log)
  try:
   for i in range(1584):p.stdin.write(picture(i/24).tobytes())
   p.stdin.close();assert p.wait()==0
  except BaseException:p.kill();raise
 dec=subprocess.run([ff,'-v','error','-i',str(file),'-f','null','-'],capture_output=True,text=True);assert dec.returncode==0 and not dec.stderr
 audio_hashes=[]
 for path in [src,str(file)]:
  raw=subprocess.run([ff,'-v','error','-i',path,'-map','0:a:0','-c:a','copy','-f','adts','-'],capture_output=True,check=True).stdout;audio_hashes.append(hashlib.sha256(raw).hexdigest())
 assert audio_hashes[0]==audio_hashes[1]
 # All-frame layout check above; inspect actual encoded samples, not the source image.
 times=[2,8,19,21.4,32.8,49.7,55.3,63.1];sheet=Image.new('RGB',(2160,1920))
 for i,t in enumerate(times):
  raw=subprocess.run([ff,'-v','error','-ss',str(t),'-i',str(file),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
  im=Image.frombytes('RGB',(540,960),raw);ImageDraw.Draw(im).text((24,65),f'v6 decoded {t}s',font=fonts[20],fill=WHITE);sheet.paste(im,((i%4)*540,(i//4)*960))
 sheet.save(OUT/'caption-corrections.jpg',quality=92)
 receipt={'file':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'seconds':66,'fps':24,'full_decode_exit':dec.returncode,'full_decode_errors':dec.stderr,'caption_count_before':len(old),'caption_count_after':len(CUES),'caption_flags_before':8,'caption_flags_after':0,'rule':'duration >=0.7s and <=20characters/second; not reading/listening signoff','exact_word_sequence_preserved':True,'aac_stream_identical':True,'aac_adts_sha256':audio_hashes[0],'decoded_correction_sample_times':times,'decoded_samples_inspected':False,'same_underlying_v5_picture_mechanism':True,'actual_listening':False,'final_pass':False}
 (BASE/'CAPTION_READABILITY_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
