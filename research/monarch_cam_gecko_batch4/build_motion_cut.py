"""Full 66s English motion/mix draft. Uses newly rendered per-output-frame release.
No optical flow/frame-blending interpolation. Final biological/audio QC still open.
"""
import sys,json,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
import imageio_ffmpeg
sys.path.insert(0,str(Path('research/monarch_cam_gecko_batch3').resolve()))
from build_story_animatic import draw_frame,fonts,BEATS,BG,WHITE,TEAL,MUTED
ASSETS=Path('studio/runtime/gecko/visual-pass');MOTION=Path('studio/runtime/gecko/motion-pass');OUT=MOTION/'cut';OUT.mkdir(parents=True,exist_ok=True)
assert len(list((MOTION/'pad').glob('*.png')))==180,'release render incomplete'
assert len(list((MOTION/'hero').glob('*.png')))==36,'hero render incomplete'
hero=[Image.open(MOTION/'hero'/f'{i:04}.png').convert('RGBA') for i in range(36)]
pads=[Image.open(MOTION/'pad'/f'{i:04}.png').convert('RGBA') for i in range(180)]
micro=Image.open(ASSETS/'setae-contact.png').convert('RGBA')
def release_index(elapsed):return max(0,min(179,round(elapsed*24)))
def picture(t):
 im=draw_frame(t);d=ImageDraw.Draw(im);bid,start,end,_,_=next(b for b in BEATS if b[1]<=t<b[2]);p=(t-start)/(end-start)
 d.rectangle((0,183,539,811),fill=BG);d.rectangle((330,20,539,50),fill=BG);d.text((330,24),'MOTION / MIX DRAFT',font=fonts[14],fill=MUTED)
 def center(y,s,size=20,col=WHITE):
  box=d.textbbox((0,0),s,font=fonts[size]);d.text(((540-box[2])/2,y),s,font=fonts[size],fill=col)
 def paste(source,size,y):
  a=source.resize((size,size),Image.Resampling.LANCZOS);im.paste(a,((540-size)//2,y),a)
 if bid=='B1':
  hi=max(0,min(35,round((t-2.7)*24)));paste(hero[hi],510,210);center(748,'Left hind foot • qualitative motion',18,MUTED)
 elif bid in ['B3','B4']:
  paste(micro,round(520+10*p),210);center(736,'Branched tips • scale simplified',18,TEAL)
  if bid=='B4':center(774,'van der Waals forces',20,WHITE)
 else:
  if bid in ['B2','B5']:frame=0
  elif bid=='B6':frame=release_index(t-34.5)
  elif bid=='B7':frame=135
  else:frame=release_index(t-55.82)
  paste(pads[frame],520,210)
  d.text((35,690),'BASE',font=fonts[16],fill=TEAL);d.text((450,690),'TIP',font=fonts[16],fill=TEAL)
  if bid=='B5':
   d.line((400,723,145,723),fill=TEAL,width=4);d.polygon([(145,723),(165,713),(165,733)],fill=TEAL);center(752,'Toward the base • symbolic shear',18,TEAL)
  elif bid=='B6':center(748,'TIP → BASE',24,TEAL)
  elif bid=='B7':center(736,'Toe movement ≠ microscopic setal angle',18,TEAL)
  elif bid=='B8':
   center(731,'CONTACT  /  DIRECTION  /  MOVEMENT',18,TEAL)
   if t>=63.68:center(773,'Sources: Autumn 2006 • Higham 2025 • Russell 2026',14,MUTED)
  else:center(748,'Controlled grip and release',20,TEAL)
 d.rectangle((0,923,539,959),fill=BG);d.text((17,933),'SCHEMATIC • ANATOMY / LISTENING QC PENDING',font=fonts[14],fill=MUTED)
 return im

def main():
 ff=imageio_ffmpeg.get_ffmpeg_exe();path=OUT/'gecko-english-motion-mix-v1.mp4';audio=MOTION/'sound-draft-v1.wav'
 with (OUT/'encode.log').open('wb') as log:
  p=subprocess.Popen([ff,'-y','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r','24','-i','-','-i',str(audio),'-map','0:v','-map','1:a','-c:v','libx264','-crf','20','-preset','veryfast','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','66','-movflags','+faststart',str(path)],stdin=subprocess.PIPE,stderr=log)
  try:
   for i in range(66*24):p.stdin.write(picture(i/24).tobytes())
   p.stdin.close();assert p.wait()==0
  except BaseException:p.kill();raise
 dec=subprocess.run([ff,'-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True);assert dec.returncode==0 and not dec.stderr
 nums=[0,4,13,28,35,37.5,40,42,46,56,61,65];sheet=Image.new('RGB',(2160,2880))
 for i,t in enumerate(nums):
  a=picture(t);ImageDraw.Draw(a).text((25,65),f'{t}s',font=fonts[20],fill=WHITE);sheet.paste(a,((i%4)*540,(i//4)*960))
 sheet.save(OUT/'motion-cut-qc.jpg')
 receipt={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'seconds':66,'fps':24,'resolution':[540,960],'release_sequence':{'rendered_frames':180,'fps':24,'seconds':7.5,'mapping':'B6 output34.5s onwards selects new per-frame rendered pose; recap55.82s onwards','no_opticalflow_or_frameblending':True},'hero_frames':36,'hero_method':'original external skin/ridge warp; NOT bone/tendon or measured gait','full_decode_exit':dec.returncode,'full_decode_errors':dec.stderr,'sound_receipt':'SOUND_DRAFT_RECEIPT.json','holds':['exactanatomy/claw/LDT and footrig not passed','listeningQC/pronunciation/prosody/seam/effectsbalance not performed','macro still with scale move remains','not final film or private delivery']}
 Path('research/monarch_cam_gecko_batch4/MOTION_CUT_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print('MOTION_MIX_CUT_COMPLETE')
if __name__=='__main__':main()
