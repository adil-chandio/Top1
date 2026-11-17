"""Macro-contact/caption revision of whole motion cut. All schematic holds remain.
No claim of full audio listening/biological validation/final production signoff.
"""
import json,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
import imageio_ffmpeg
from build_motion_cut import picture as prior_picture,fonts,BG,WHITE,TEAL,MUTED
ROOT=Path('studio/runtime/gecko/macro-pass');OUT=ROOT/'cut';OUT.mkdir(parents=True,exist_ok=True)
assert len(list(ROOT.glob('*.png')))==48,'macro render incomplete'
macro=[Image.open(ROOT/f'{i:04}.png').convert('RGBA') for i in range(48)]
CUES=json.loads(Path('research/monarch_cam_gecko_batch4/REVIEW_CAPTION_CUES.json').read_text())['cues']
def picture(t):
 im=prior_picture(t);d=ImageDraw.Draw(im)
 d.rectangle((330,20,539,50),fill=BG);d.text((360,24),'REVIEW CUT v3',font=fonts[14],fill=MUTED)
 def center(y,text,size=20,col=WHITE):
  b=d.textbbox((0,0),text,font=fonts[size]);d.text(((540-b[2])/2,y),text,font=fonts[size],fill=col)
 if 11.08<=t<26.59:
  d.rectangle((0,183,539,811),fill=BG)
  index=max(0,min(47,round((t-16.14)*24)));frame=macro[index]
  if t>=20.27:
   # Authored crop for tip emphasis, not microscope-magnification evidence.
   u=min(1,(t-20.27)/2);margin=round(40*u);frame=frame.crop((margin,margin,512-margin,512-margin))
  a=frame.resize((520,520),Image.Resampling.LANCZOS);im.paste(a,(10,210),a)
  center(735,'Close-contact schematic',20,TEAL);center(771,'Counts, spacing and motion simplified',16,MUTED)
 # Replace inherited captions with terminology-preserving exact-transcript groups.
 d.rectangle((0,813,539,920),fill=BG)
 cue=next((c for c in CUES if c['start']<=t<c['end']+.06),None)
 if cue:
  d.rectangle((16,818,524,915),fill='#07111b');lines=[];current=''
  for token in cue['text'].split():
   test=(current+' '+token).strip()
   if d.textbbox((0,0),test,font=fonts[24])[2]>470:lines.append(current);current=token
   else:current=test
  if current:lines.append(current)
  assert len(lines)<=3
  for i,line in enumerate(lines):center(833+i*29,line,24)
 d.rectangle((0,923,539,959),fill=BG);d.text((24,933),'QUALITATIVE SCHEMATICS • REVIEW COPY',font=fonts[14],fill=MUTED)
 return im

def main():
 ff=imageio_ffmpeg.get_ffmpeg_exe();path=OUT/'gecko-english-review-cut-v3.mp4'
 with (OUT/'encode.log').open('wb') as log:
  proc=subprocess.Popen([ff,'-y','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r','24','-i','-','-i','studio/runtime/gecko/motion-pass/sound-draft-v1.wav','-map','0:v','-map','1:a','-c:v','libx264','-crf','20','-preset','veryfast','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','66','-movflags','+faststart',str(path)],stdin=subprocess.PIPE,stderr=log)
  try:
   for i in range(1584):proc.stdin.write(picture(i/24).tobytes())
   proc.stdin.close();assert proc.wait()==0
  except BaseException:proc.kill();raise
 dec=subprocess.run([ff,'-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True);assert dec.returncode==0 and not dec.stderr
 sheet=Image.new('RGB',(2160,2880))
 for i,t in enumerate([0,4,13,16.14,17,18.14,22,28,37.5,46,61,65]):
  a=picture(t);ImageDraw.Draw(a).text((25,65),f'{t}s',font=fonts[20],fill=WHITE);sheet.paste(a,((i%4)*540,(i//4)*960))
 sheet.save(OUT/'review-qc.jpg')
 receipt={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'seconds':66,'resolution':[540,960],'fps':24,'macro_frames':48,'macro_fps':24,'macro_active_start':16.14,'macro_kind':'qualitative original approach/contact animation; no measured setal engagement trajectory','caption_cues':'REVIEW_CAPTION_CUES.json; supplied script + approximate acoustic timing','full_decode_exit':dec.returncode,'full_decode_errors':dec.stderr,'sound':'same technically mastered draft,not newly listening-reviewed','holds':['exactanatomy/claw/LDT/biologicalrig','pronunciation/prosody/seam/effects listening review','full picture/audio/combined craftQC and finalcreditsdelivery'],'final_pass':False}
 Path('research/monarch_cam_gecko_batch4/REVIEW_CUT_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print('REVIEW_CUT_V3_COMPLETE')
if __name__=='__main__':main()
