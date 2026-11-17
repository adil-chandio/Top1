"""Assemble full-length 3D visual development cut, not final production.
Retains selected voice, transcript-constrained captions and explicit schematic labels.
"""
import sys,json,subprocess,hashlib,math
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_story_animatic import draw_frame,fonts,BEATS,BG,WHITE,TEAL,MUTED
import imageio_ffmpeg
ASSETS=Path('studio/runtime/gecko/visual-pass');OUT=ASSETS/'cut';OUT.mkdir(parents=True,exist_ok=True)
foot=Image.open(ASSETS/'foot-ventral.png').convert('RGBA');micro=Image.open(ASSETS/'setae-contact.png').convert('RGBA')
pads={int(p.stem):Image.open(p).convert('RGB') for p in (ASSETS/'pad').glob('*.png')}
def picture(t):
 im=draw_frame(t);d=ImageDraw.Draw(im);bid,start,end,_,_=next(b for b in BEATS if b[1]<=t<b[2]);p=(t-start)/(end-start)
 d.rectangle((0,183,539,811),fill=BG);d.rectangle((350,20,539,50),fill=BG);d.text((350,24),'3D ROUGH CUT',font=fonts[14],fill=MUTED)
 def center(y,s,size=20,col=WHITE):
  box=d.textbbox((0,0),s,font=fonts[size]);d.text(((540-box[2])/2,y),s,font=fonts[size],fill=col)
 def paste(source,size,y):
  a=source.resize((size,size),Image.Resampling.LANCZOS)
  im.paste(a,((540-size)//2,y),a if a.mode=='RGBA' else None)
 if bid=='B1':
  paste(foot,round(490+20*p),220);center(748,'Tokay left hind foot • schematic',18,MUTED)
 elif bid in ['B3','B4']:
  paste(micro,round(520+10*p),210);center(736,'Branched tips • scale simplified',18,TEAL)
  if bid=='B4':center(774,'van der Waals forces',20,WHITE)
 else:
  if bid=='B2':frame=round(31+16*math.sin(p*math.pi))
  elif bid=='B5':frame=30
  elif bid=='B6':frame=round(31+21*max(0,min(1,(t-34.5)/6))) if t<41.5 else 60
  elif bid=='B7':frame=48
  else:frame=30 if t<55.82 else (44 if t<60.5 else 60)
  nearest=min(pads,key=lambda k:abs(k-frame));paste(pads[nearest],520,210)
  d.text((35,690),'BASE',font=fonts[16],fill=TEAL);d.text((450,690),'TIP',font=fonts[16],fill=TEAL)
  if bid=='B5':
   d.line((400,723,145,723),fill=TEAL,width=4);d.polygon([(145,723),(165,713),(165,733)],fill=TEAL);center(752,'Toward the base • symbolic shear',18,TEAL)
  elif bid=='B6':center(748,'TIP → BASE',24,TEAL)
  elif bid=='B7':center(736,'Toe movement ≠ microscopic setal angle',18,TEAL)
  elif bid=='B8':
   center(731,'CONTACT  /  DIRECTION  /  MOVEMENT',18,TEAL)
   if t>=63.68:center(773,'Sources: Autumn 2006 • Higham 2025 • Russell 2026',14,MUTED)
  else:center(748,'Controlled grip and release',20,TEAL)
 d.rectangle((0,923,539,959),fill=BG);d.text((17,933),'SCHEMATIC • FINAL ANATOMY / AUDIO QC PENDING',font=fonts[14],fill=MUTED)
 return im

def main():
 ff=imageio_ffmpeg.get_ffmpeg_exe();path=OUT/'gecko-english-3d-visual-cut-v1.mp4';audio='studio/runtime/gecko/narration/english-narration-v1.wav'
 with (OUT/'encode.log').open('wb') as log:
  p=subprocess.Popen([ff,'-y','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r','24','-i','-','-i',audio,'-map','0:v','-map','1:a','-c:v','libx264','-crf','20','-preset','veryfast','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-af','apad','-t','66','-movflags','+faststart',str(path)],stdin=subprocess.PIPE,stderr=log)
  try:
   for i in range(66*24):p.stdin.write(picture(i/24).tobytes())
   p.stdin.close();assert p.wait()==0
  except BaseException:p.kill();raise
 nums=[0,7,13,22,28,35,38,41,46,54,59,65];sheet=Image.new('RGB',(2160,2880))
 for i,t in enumerate(nums):
  im=picture(t);ImageDraw.Draw(im).text((25,65),f'{t}s',font=fonts[20],fill=WHITE);sheet.paste(im,((i%4)*540,(i//4)*960))
 sheet.save(OUT/'visual-cut-qc.jpg')
 dec=subprocess.run([ff,'-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True);assert dec.returncode==0 and not dec.stderr
 receipt={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'seconds':66,'fps':24,'resolution':[540,960],'audio':'same selected voice09,63.68s,not newly listening-reviewed','full_decode_exit':dec.returncode,'full_decode_errors':dec.stderr,'assets':'original Blender procedural foot,microstructure,pad-shotassets','limitations':['schematic unmeasured foot and placeholder claws; no anatomically solved gait','pad keyframes sampled/held; not final smooth motion','foot/microstructure use rendered stills with scale moves, not articulated animation','noBGM/SFX/finalmix','not final production or anatomy/audioQC pass']}
 Path('research/monarch_cam_gecko_batch3/THREED_VISUAL_CUT_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print('FULL_3D_VISUAL_CUT_RENDERED')
if __name__=='__main__':main()
