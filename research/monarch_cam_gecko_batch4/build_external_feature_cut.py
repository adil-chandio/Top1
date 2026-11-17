"""Audit-targeted external-feature/framing revision. Qualitative illustration only."""
import json,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
import imageio_ffmpeg
from build_audit_corrected_cut import picture as previous,fonts,BG,TEAL,MUTED,WHITE
from build_motion_cut import pads,release_index,BEATS
ROOT=Path('studio/runtime/gecko/claw-framing-pass');OUT=ROOT/'cut';OUT.mkdir(parents=True,exist_ok=True)
hero=[Image.open(ROOT/'hero'/f'{i:04}.png').convert('RGBA') for i in range(36)]
boxes=[im.getbbox() for im in hero];box=(max(0,min(b[0] for b in boxes)-12),max(0,min(b[1] for b in boxes)-12),min(512,max(b[2] for b in boxes)+12),min(512,max(b[3] for b in boxes)+12))
macro=[Image.open(Path('studio/runtime/gecko/macro-pass')/f'{i:04}.png').convert('RGBA') for i in range(48)]
def picture(t):
 im=previous(t);d=ImageDraw.Draw(im);bid,start,end,_,_=next(b for b in BEATS if b[1]<=t<b[2]);p=(t-start)/(end-start)
 d.rectangle((300,20,539,50),fill=BG);d.text((320,24),'SCHEMATIC REVIEW v5',font=fonts[14],fill=MUTED)
 d.rectangle((0,183,539,811),fill=BG)
 def center(y,s,size=18,col=TEAL):
  b=d.textbbox((0,0),s,font=fonts[size]);d.text(((540-b[2])/2,y),s,font=fonts[size],fill=col)
 def paste(a,xy,size):
  a=a.resize(size,Image.Resampling.LANCZOS);im.paste(a,xy,a)
 if bid=='B1':
  hi=max(0,min(35,round((t-2.7)*24)));a=hero[hi].crop(box);a.thumbnail((500,520),Image.Resampling.LANCZOS);im.paste(a,((540-a.width)//2,215),a)
  center(750,'Tokay foot • source-informed schematic')
 elif bid in ['B3','B4']:
  a=macro[max(0,min(47,round((t-16.14)*24)))].crop((45,100,490,425));paste(a,(10,265),(520,380))
  center(715,'Close-contact schematic',20);center(754,'Counts, spacing and motion simplified',16,MUTED)
 else:
  if bid in ['B2','B5']:index=0
  elif bid=='B6':index=release_index(t-34.5)
  elif bid=='B7':index=179
  else:index=release_index(t-55.82)
  # Deliberately crop peripheral substrate, not pad, to increase mechanism size.
  paste(pads[index].crop((60,90,460,425)),(10,245),(520,436))
  d.text((35,695),'BASE',font=fonts[16],fill=TEAL);d.text((450,695),'TIP',font=fonts[16],fill=TEAL)
  if bid=='B5':
   d.line((400,735,145,735),fill=TEAL,width=4);d.polygon([(145,735),(165,725),(165,745)],fill=TEAL);center(768,'Toward the base • symbolic shear')
  elif bid=='B6':center(750,'TIP → BASE',24)
  elif bid=='B7':center(750,'Toe movement ≠ microscopic setal angle')
  elif bid=='B8':
   if t<55.82:center(190,'RECAP — CONTACT STATE',16,MUTED)
   center(731,'CONTACT  /  DIRECTION  /  MOVEMENT')
  else:center(750,'Controlled grip and release',20)
 if t>=63.68:center(767,'Sources: Autumn • Higham • Russell',16,MUTED);center(790,'Full references in the credits sheet',16,MUTED)
 return im

def main():
 ff=imageio_ffmpeg.get_ffmpeg_exe();file=OUT/'gecko-english-review-cut-v5.mp4'
 with (OUT/'encode.log').open('wb') as log:
  p=subprocess.Popen([ff,'-y','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r','24','-i','-','-i','studio/runtime/gecko/motion-pass/sound-draft-v1.wav','-map','0:v','-map','1:a','-c:v','libx264','-crf','20','-preset','veryfast','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','66','-movflags','+faststart',str(file)],stdin=subprocess.PIPE,stderr=log)
  try:
   for i in range(1584):p.stdin.write(picture(i/24).tobytes())
   p.stdin.close();assert p.wait()==0
  except BaseException:p.kill();raise
 dec=subprocess.run([ff,'-v','error','-i',str(file),'-f','null','-'],capture_output=True,text=True);assert dec.returncode==0 and not dec.stderr
 sheet=Image.new('RGB',(2160,2880))
 for i,t in enumerate([0,4,13,17.5,23,28,35,38,42,46,54,65]):
  a=picture(t);ImageDraw.Draw(a).text((25,65),f'{t}s',font=fonts[20],fill=WHITE);sheet.paste(a,((i%4)*540,(i//4)*960))
 sheet.save(OUT/'v5-qc.jpg')
 receipt={'file':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'seconds':66,'resolution':[540,960],'fps':24,'hero_crop':box,'pad_crop':[60,90,460,425],'macro_crop':[45,100,490,425],'external_feature_check':json.loads((ROOT/'hero/external-feature-check.json').read_text()),'full_decode_exit':dec.returncode,'full_decode_errors':dec.stderr,'final_pass':False,'scope':'source-informed external schematic; not exact anatomy or bone/tendonrig','audio':'same mastered draft; listeningQC still open'}
 Path('research/monarch_cam_gecko_batch5/EXTERNAL_FEATURE_CORRECTION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print('SCHEMATIC_REVIEW_V5_COMPLETE')
if __name__=='__main__':main()
