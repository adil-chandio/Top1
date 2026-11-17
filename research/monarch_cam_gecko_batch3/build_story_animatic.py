"""Full English story animatic: original schematic graphics + generated narration.
NOT final anatomy/animation, independent speech validation or production-QC pass.
Requires Pillow11.3 and imageio-ffmpeg0.8.1. Outputs remain ignored.
"""
from pathlib import Path
import json,math,re,subprocess,hashlib
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
ROOT=Path('studio/runtime/gecko/story-animatic');ROOT.mkdir(parents=True,exist_ok=True)
WORDS=json.loads(Path('research/monarch_cam_gecko_batch3/ENGLISH_WORD_ALIGNMENT.json').read_text())['words']
W,H,FPS,DURATION=540,960,24,66
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
fonts={n:ImageFont.truetype(FONT,n) for n in [14,16,18,20,22,24,28,32,36,40]}
BG='#101c29';WHITE='#e9f0f4';MUTED='#9eafbf';TEAL='#74dfc1';AMBER='#e9bc7d'
BEATS=[('B1',0,5.71,'STRONG GRIP.','HOW DOES IT LET GO?'),('B2',5.71,11.08,'NOT JUST STRENGTH','CONTROL'),('B3',11.08,20.27,'UNDER THE TOE','SET A E'.replace(' ','')),('B4',20.27,26.59,'NOT SUCTION','CLOSE CONTACT'),('B5',26.59,33.2,'DIRECTION MATTERS','PROXIMAL SHEAR'),('B6',33.2,44.02,'TIP-FIRST RELEASE','CONTACT BREAKS IN SEQUENCE'),('B7',44.02,52.19,'DIGITAL HYPEREXTENSION','TOE MOVEMENT'),('B8',52.19,66,'GRIP + RELEASE','WORKING TOGETHER')]
# Approximate transcript-constrained cue timings, not independently verified speech timing.
CAPS=[(c['start'],c['end'],c['text']) for c in json.loads(Path('research/monarch_cam_gecko_batch3/ENGLISH_CAPTION_CUES.json').read_text())['cues']]
FOOT=Image.open('studio/runtime/gecko/anatomy/left-pes-layout-study.png').convert('RGB').crop((110,100,780,790)).resize((430,450),Image.Resampling.LANCZOS)

def draw_frame(t):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 def text(x,y,s,size=24,color=WHITE):d.text((x,y),s,font=fonts[size],fill=color)
 def center(y,s,size=24,color=WHITE):
  b=d.textbbox((0,0),s,font=fonts[size]);text((W-b[2])/2,y,s,size,color)
 def line(pts,col,width=4):d.line(pts,fill=col,width=width,joint='curve')
 def arrow(x,y,xx,yy,col=TEAL):
  line([(x,y),(xx,yy)],col,5);a=math.atan2(yy-y,xx-x)
  d.polygon([(xx,yy),(xx-17*math.cos(a-.5),yy-17*math.sin(a-.5)),(xx-17*math.cos(a+.5),yy-17*math.sin(a+.5))],fill=col)
 def pad(progress=0,lift=0,y=430):
  # Original schematic continuous centerline; no bones/joint angles asserted.
  pts=[];z=0;x=70;ds=400/70
  for i in range(71):
   u=i/70;onset=(1-u)*.6;v=max(0,min(1,(progress-onset)/.4));th=1.3*u*v*v*(3-2*v)
   if i:x+=ds*math.cos(th);z+=ds*math.sin(th)
   pts.append((x,y-z-lift))
  line([(45,y+15),(495,y+15)],'#567386',3)
  left=[];right=[]
  for k,(xx,yy) in enumerate(pts):
   a=pts[max(0,k-1)];b=pts[min(len(pts)-1,k+1)];angle=math.atan2(b[1]-a[1],b[0]-a[0]);nx=-math.sin(angle)*15;ny=math.cos(angle)*15
   left.append((xx+nx,yy+ny));right.append((xx-nx,yy-ny))
  d.polygon(left+right[::-1],fill=AMBER)
  for i in range(0,71,3):
   px,py=pts[i]
   if y-py<4 and lift<3:line([(px-3,y+13),(px+3,y+13)],TEAL,5)
  text(45,y+55,'BASE',18,MUTED);text(426,y+55,'TIP',18,MUTED)
  return pts
 def hairs(contact=True):
  line([(45,540),(495,540)],'#617c8c',4)
  for k in range(5):
   x=80+k*85;line([(x-25,370),(x-8,425),(x+2,477)],AMBER,7)
   for j in range(3):
    xx=x-24+j*24;line([(x+2,477),(xx,505),(xx+8,535 if contact else 518)],AMBER,3)
    line([(xx+3,535 if contact else 518),(xx+17,535 if contact else 518)],TEAL,4)
  center(585,'BRANCHING TIPS',20,TEAL)
  center(621,'Schematic — scale simplified',16,MUTED)
 b=next(b for b in BEATS if b[1]<=t<b[2]);bid,start,end,title,sub=b;p=(t-start)/(end-start)
 text(24,24,'MONARCH CAM',16,TEAL);text(360,24,'STORY ANIMATIC',14,MUTED)
 center(110,title,28);center(160,sub,20,TEAL)
 if bid=='B1':
  im.paste(FOOT,(55,245));center(718,'Tokay foot layout • schematic',18,MUTED)
 elif bid=='B2':
  pad(.65*(.5+.5*math.sin(p*math.pi*2)),y=510);center(670,'Contact. Loading. Movement.',20,TEAL)
 elif bid in ['B3','B4']:
  hairs();
  if bid=='B4':center(285,'van der Waals forces',28,WHITE)
  else:center(285,'Tiny, hair-like structures',22,WHITE)
 elif bid=='B5':
  pad(y=480);arrow(405,610,140,610);center(670,'Toward the base • along the surface',18,MUTED);center(710,'Qualitative loading arrow — not force data',16,MUTED)
 elif bid=='B6':
  # Release follows narrated explanation and holds clear for whole-pad contrast.
  progress=min(1,max(0,(t-34.5)/6));lift=max(0,min(1,(t-41)/1.5))*48
  pad(progress,lift,y=535);center(650,'TIP → BASE',28,TEAL);center(705,'One continuous explanatory shot',16,MUTED)
 elif bid=='B7':
  pad(.88,y=470);center(595,'Whole-toe motion',24,TEAL)
  center(645,'≠',36,WHITE);center(705,'Microscopic setal angles',22,MUTED)
 else:
  pad(.8,max(0,(p-.5))*70,y=445)
  labels=[('CLOSE CONTACT',55.82),('LOAD DIRECTION',57.2),('TOE MOVEMENT',58.63)]
  for i,(label,onset) in enumerate(labels):
   if t>=onset:center(565+i*48,label,24,TEAL)
  if t>=63.68:
   center(730,'Sources / original schematic',16,MUTED)
   center(755,'Autumn et al. 2006 • Higham & Russell 2025',14,MUTED)
   center(778,'Russell et al. 2026 • Full credits pending',14,MUTED)
 # English captions from known transcript, boundaries from constrained alignment.
 cap=next((s for a,z,s in CAPS if a<=t<z+.10),'')
 if cap:
  tokens=cap.split();lines=[];cur=''
  for tok in tokens:
   test=(cur+' '+tok).strip()
   if d.textbbox((0,0),test,font=fonts[24])[2]>470:lines.append(cur);cur=tok
   else:cur=test
  if cur:lines.append(cur)
  d.rectangle((16,818,524,915),fill='#07111b')
  for i,s in enumerate(lines[:3]):center(833+i*29,s,24)
 text(24,932,'SCHEMATIC • ANATOMY / SOUND QC PENDING',14,MUTED)
 return im

def main():
 ff=imageio_ffmpeg.get_ffmpeg_exe();audio=Path('studio/runtime/gecko/narration/english-narration-v1.wav')
 path=ROOT/'gecko-english-story-animatic-v1.mp4'
 cmd=[ff,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-af','apad','-t',str(DURATION),'-movflags','+faststart',str(path)]
 with (ROOT/'encode.log').open('wb') as log:
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
  try:
   for i in range(FPS*DURATION):proc.stdin.write(draw_frame(i/FPS).tobytes())
   proc.stdin.close();code=proc.wait()
   if code:raise RuntimeError('ffmpeg encode failed:'+str(code))
  except BaseException:
   proc.kill();raise
 nums=[0,7,13,22,28,35,38,41,46,54,59,65];sheet=Image.new('RGB',(W*4,H*3))
 for i,t in enumerate(nums):
  im=draw_frame(t);ImageDraw.Draw(im).text((25,65),f'{t}s',font=fonts[20],fill=WHITE);sheet.paste(im,((i%4)*W,(i//4)*H))
 sheet.save(ROOT/'story-qc-sheet.jpg')
 result=subprocess.run([ff,'-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True)
 receipt={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'seconds':DURATION,'fps':FPS,'size':[W,H],'audio_seconds':63.68,'end_hold_seconds':2.32,'full_decode_exit':result.returncode,'full_decode_errors':result.stderr,'beat_bounds_method':'approximate transcript-constrained acoustic alignment; not listening-verified','beat_bounds':BEATS,'status':'story animatic only, final production/anatomy/audioQC not passed','no_bgm_or_sfx':True}
 Path('research/monarch_cam_gecko_batch3/STORY_ANIMATIC_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
 assert result.returncode==0 and not result.stderr
 print('FULL_STORY_ANIMATIC_COMPLETE',path)
if __name__=='__main__':main()
