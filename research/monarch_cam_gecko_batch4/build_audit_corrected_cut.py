"""Targeted audit corrections; not a final signoff or new anatomy/audio approval."""
import json,hashlib,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
import imageio_ffmpeg
from build_review_cut import picture as prior_picture,fonts,BG,TEAL,MUTED,WHITE
from build_motion_cut import pads,release_index
OUT=Path('studio/runtime/gecko/audit-corrected');OUT.mkdir(parents=True,exist_ok=True)
def picture(t):
 im=prior_picture(t);d=ImageDraw.Draw(im)
 d.rectangle((330,20,539,50),fill=BG);d.text((360,24),'REVIEW CUT v4',font=fonts[14],fill=MUTED)
 def center(y,s,size=18,col=TEAL):
  b=d.textbbox((0,0),s,font=fonts[size]);d.text(((540-b[2])/2,y),s,font=fonts[size],fill=col)
 if 44.02<=t<52.19:
  # Keep detached state after B6; do not silently snap back into proximal contact.
  d.rectangle((0,183,539,811),fill=BG);a=pads[179].resize((520,520),Image.Resampling.LANCZOS);im.paste(a,(10,210),a)
  d.text((35,690),'BASE',font=fonts[16],fill=TEAL);d.text((450,690),'TIP',font=fonts[16],fill=TEAL)
  center(736,'Toe movement ≠ microscopic setal angle')
 if 52.19<=t<55.82:center(190,'RECAP — CONTACT STATE',16,MUTED)
 if t>=63.68:
  d.rectangle((0,765,539,811),fill=BG);center(767,'Sources: Autumn • Higham • Russell',16,MUTED);center(790,'Full references in the credits sheet',16,MUTED)
 return im

def main():
 ff=imageio_ffmpeg.get_ffmpeg_exe();path=OUT/'gecko-english-review-cut-v4.mp4'
 with (OUT/'encode.log').open('wb') as log:
  p=subprocess.Popen([ff,'-y','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r','24','-i','-','-i','studio/runtime/gecko/motion-pass/sound-draft-v1.wav','-map','0:v','-map','1:a','-c:v','libx264','-crf','20','-preset','veryfast','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','66','-movflags','+faststart',str(path)],stdin=subprocess.PIPE,stderr=log)
  try:
   for i in range(1584):p.stdin.write(picture(i/24).tobytes())
   p.stdin.close();assert p.wait()==0
  except BaseException:p.kill();raise
 dec=subprocess.run([ff,'-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True);assert dec.returncode==0 and not dec.stderr
 nums=[43.9,44.1,46,51.9,52.3,54,63.8,65];sheet=Image.new('RGB',(2160,1920))
 for i,t in enumerate(nums):
  im=picture(t);ImageDraw.Draw(im).text((25,65),f'{t}s',font=fonts[20],fill=WHITE);sheet.paste(im,((i%4)*540,(i//4)*960))
 sheet.save(OUT/'correction-qc.jpg')
 receipt={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'seconds':66,'fps':24,'resolution':[540,960],'corrections':['B7detachedposeheld44.02–52.19s','recapcontactresetexplicit52.19–55.82s','readablebriefsourcesandcompanioncreditspointer63.68–66s'],'full_decode_exit':dec.returncode,'full_decode_errors':dec.stderr,'final_pass':False,'holds':['exactanatomy/claw/LDT/biologicalrig','actualaudio/listening/fullAVQC','remainingfinalcraftsignoff']}
 Path('research/monarch_cam_gecko_batch4/AUDIT_CORRECTION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print('AUDIT_CORRECTED_CUT_COMPLETE')
if __name__=='__main__':main()
