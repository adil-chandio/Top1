"""Full63.68s English private review cut: corrected 3D plates +12Hz rendered
release, authored explanatory graphic inserts,25fps compositing, approved narration.
Not native720p3D or validated anatomy; exact sources and limitations in receipt.
"""
from pathlib import Path
import math,json,hashlib,subprocess
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import imageio_ffmpeg
OUT=Path('studio/runtime/gecko/full-review-v1');A=OUT/'assets';OUT.mkdir(parents=True,exist_ok=True)
W,H=720,1280;FPS=25;DURATION=63.68;N=1592
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
fonts={k:ImageFont.truetype(FONT,k) for k in [17,20,23,26,30,34,42,48]}
CUES=json.loads(Path('research/monarch_cam_gecko_batch3/ENGLISH_CAPTION_CUES.json').read_text())['cues']
audio=Path('studio/runtime/gecko/narration/english-narration-v1.wav');assert hashlib.sha256(audio.read_bytes()).hexdigest()=='1d7a3284670a93ded1ad21f24aee980f3f39eba2766daa6a16e85580c3e41cc8'
plates={name:Image.open(A/(name+'.png')).convert('RGB').resize((W,H),Image.Resampling.LANCZOS) for name in ['exterior','loaded','released']}
release=[Image.open(A/f'release-{i:04}.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS) for i in range(132)]
cream=(238,230,208);muted=(151,183,183);gold=(218,177,102)
def label(d,xy,text,size=23,color=cream):d.text(xy,text,font=fonts[size],fill=color)
def centered(d,y,text,size=30,color=cream):
 box=d.textbbox((0,0),text,font=fonts[size]);d.text(((W-(box[2]-box[0]))/2,y),text,font=fonts[size],fill=color)
def wrapped(d,text,size=34,maxwidth=620):
 words=text.split();lines=[];line=''
 for word in words:
  candidate=(line+' '+word).strip()
  if d.textlength(candidate,font=fonts[size])>maxwidth and line:lines.append(line);line=word
  else:line=candidate
 if line:lines.append(line)
 return lines
shade=Image.new('RGBA',(W,H))
pix=shade.load()
for y in range(H):
 alpha=int(215*max(0,1-y/260)+235*max(0,(y-970)/310))
 for x in range(W):pix[x,y]=(3,12,17,alpha)
def plate(name,t):
 im=plates[name];z=1.015+.035*(.5+.5*math.sin(t*.18));nw=int(W*z);nh=int(H*z);im=im.resize((nw,nh),Image.Resampling.BICUBIC);return im.crop(((nw-W)//2,(nh-H)//2,(nw+W)//2,(nh+H)//2)).convert('RGBA')
def micro(t,contact=True):
 # Authored explanatory drawing: hair/branches are illustrative, not microscopy.
 im=Image.new('RGBA',(W,H),(7,22,29,255));d=ImageDraw.Draw(im)
 for y in range(H):d.line((0,y,W,y),fill=(7+int(y/H*6),22+int(y/H*8),29+int(y/H*8)))
 d.polygon([(0,881),(720,780),(720,1025),(0,1126)],fill=(39,64,69));d.line([(0,881),(720,780)],fill=(136,170,171),width=3)
 shift=0 if contact else 60
 for row in range(3):
  for k in range(7):
   x=65+k*95+row*15;y=881-x*(101/720);top=y-200-row*48-shift
   # Same persistent inclined substrate; curved shafts and branched flattened tips.
   pts=[(x-30,top),(x-20,top+70),(x+5,y-70-shift),(x+15,y-13-shift)]
   d.line([(a+4,b+5) for a,b in pts],fill=(2,8,10),width=13);d.line(pts,fill=(167+row*15,143+row*10,96),width=9)
   for j in [-1,0,1]:
    end=(x+15+j*16,y-shift);d.line([(x+5,y-70-shift),end],fill=(220,192,134),width=3);d.ellipse((end[0]-10,end[1]-3,end[0]+10,end[1]+3),fill=(211,203,168))
 label(d,(44,230),'SCHEMATIC · NOT TO SCALE',17,muted)
 return im

def frame(t):
 if t<11.08:im=plate('exterior',t);chapter='THE QUESTION';title='Strong grip. Controlled release.'
 elif t<20.27:im=micro(t,t>=16.14);chapter='FROM PAD TO CONTACT';title='Branching microscopic hairs'
 elif t<26.59:im=micro(t);chapter='CLOSE CONTACT';title='Not suction. Van der Waals forces.'
 elif t<33.20:im=plate('loaded',t);chapter='DIRECTION MATTERS';title='Loading toward the base'
 elif t<44.02:
  ix=min(131,max(0,round((t-33.20)/10.82*131)));im=release[ix].convert('RGBA');chapter='ONE CONTINUOUS RELEASE';title='Tip first. Then toward the base.'
 elif t<47.95:im=plate('released',t);chapter='THE TOE MOVEMENT';title='Digital hyperextension'
 elif t<52.19:im=micro(t);chapter='TWO DIFFERENT SCALES';title='Whole toe ≠ microscopic hair angle'
 else:im=plate('released',t);chapter='THE ANSWER';title='Contact. Direction. Control.'
 im.alpha_composite(shade);d=ImageDraw.Draw(im);label(d,(44,43),'MONARCH CAM  /  HOW DOES A GECKO LET GO?',17,muted);label(d,(44,99),chapter,20,gold)
 for j,line in enumerate(wrapped(d,title,34,632)):label(d,(44,139+j*43),line,34)
 if 26.59<=t<33.20:
  # Explanatory screen-direction arrow; not a solved biological force vector.
  d.line((530,960,235,960),fill=gold,width=4);d.polygon([(235,960),(253,950),(253,970)],fill=gold);label(d,(255,979),'Toward base · qualitative cue',20,gold)
 if not (11.08<=t<26.59 or 47.95<=t<52.19):label(d,(44,1060),'Illustrative exterior · explanatory local view',17,muted)
 cue=next((c for c in CUES if c['start']<=t<c['end']),None)
 if cue:
  lines=wrapped(d,cue['text'],30,626);height=len(lines)*40+25;d.rounded_rectangle((29,1110,691,1110+height),radius=13,fill=(4,14,19,225))
  for j,line in enumerate(lines):centered(d,1122+j*40,line,30)
 if t>=60.4:label(d,(44,1240),'Science: Autumn2006 · Higham2025 · Russell2026',17,muted)
 return im.convert('RGB')
ff=imageio_ffmpeg.get_ffmpeg_exe();movie=OUT/'gecko-complete-english-review-v1.mp4'
cmd=[ff,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000','-t',str(DURATION),'-movflags','+faststart',str(movie)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for f in range(N):
 im=frame(f/FPS);p.stdin.write(im.tobytes())
 if f in [0,150,325,475,650,825,950,1075,1200,1375,1550]:im.save(OUT/f'review-{f:04}.jpg',quality=92)
 if f%125==0:print('ASSEMBLED',f,'/',N,flush=True)
p.stdin.close();assert p.wait()==0
check=subprocess.run([ff,'-v','error','-i',str(movie),'-f','null','-'],capture_output=True,text=True);assert check.returncode==0 and not check.stderr
receipt={'file':str(movie),'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'bytes':movie.stat().st_size,'seconds':DURATION,'frames':N,'fps':FPS,'output_resolution':[W,H],'source_3d_resolution':[432,768],'source_release_pose_rate_hz':12,'source_release_pose_count':132,'composition':'3D rendered plates with2D camera reframing, continuous3D release sampled12Hz, original2D schematic inserts, English caption overlays','audio_source_sha256':hashlib.sha256(audio.read_bytes()).hexdigest(),'audio_source_seconds':63.68,'audio_user_approved':True,'new_narration':False,'decode_exit':check.returncode,'decode_errors':check.stderr,'quality_or_anatomy_pass':False,'native_av_listened_by_assistant':False,'publication_authorized':False,'scope':'User explicitly requested full script-length private review movie and Drive upload; no public permissions change'}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('COMPLETE',movie,flush=True)
