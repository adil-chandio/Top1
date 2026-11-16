"""Author custom animated editorial graphics, mix licensed tracks and encode exact 20s.
Not an automatic artistic/listening quality certification.
"""
from pathlib import Path
import subprocess,math,json,hashlib,shutil,wave
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import imageio_ffmpeg
BASE=Path(__file__).parent;OUT=BASE/'out';FRAMES=OUT/'opening_frames';FPS=24;W,H=768,432
FF=imageio_ffmpeg.get_ffmpeg_exe()
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
font=lambda n,b=False:ImageFont.truetype(BOLD if b else FONT,n)

def smooth(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def envelope(t,a,b):return min(smooth((t-a)/.35),smooth((b-t)/.3))
def tracked(d,text,xy,size,fill,spacing):
 x,y=xy
 for ch in text:
  d.text((x,y),ch,font=font(size,True),fill=fill);x+=d.textlength(ch,font=font(size,True))+spacing

def composite(f):
 t=f/FPS
 im=Image.open(FRAMES/f'{f:04}.png').convert('RGBA')
 # Editorial bottom plate: subtle tonal separation, not a still-image animation.
 overlay=Image.new('RGBA',(W,H));arr=np.zeros((H,W,4),np.uint8)
 yy=np.arange(H)[:,None];arr[:,:,3]=np.clip((yy-H*.61)/(H*.39)*110,0,110).astype(np.uint8)
 overlay=Image.fromarray(arr);im=Image.alpha_composite(im,overlay)
 g=Image.new('RGBA',(W,H));d=ImageDraw.Draw(g)
 # Constant honest reconstruction label and brand.
 d.text((30,21),'MONARCH / CAM',font=font(11,True),fill=(224,237,239,210))
 d.text((W-205,22),'ILLUSTRATIVE RECONSTRUCTION',font=font(8),fill=(180,209,215,200))
 # Segmented progress rail is editorial timing, not animal-measurement data.
 d.line((30,42,30+708*min(1,t/20),42),fill=(100,218,218,180),width=1)
 cues=[(0,3.8,'01 / ENCOUNTER','ORCAS','Shikaar jaari hai.'),(3.8,8.7,'02 / APPROACH','HUMPBACK','Unhi ki taraf.'),(8.7,11.5,'03 / DIET ILLUSTRATION','ALAG KHANA','Krill + chhoti machhliyan'),(11.5,15.5,'04 / OBSERVED BEHAVIOUR','PEECHHA','Approach aur follow'),(15.5,20,'05 / OBSERVED DISPLAYS','FLIPPERS + DUM','Displays record kiye gaye hain.')]
 for a,b,kicker,title,sub in cues:
  alpha=envelope(t,a,b)
  if alpha<=0:continue
  local=Image.new('RGBA',(W,H));ld=ImageDraw.Draw(local);slide=round((1-smooth((t-a)/.6))*16)
  ld.line((30,304+slide,67,304+slide),fill=(98,228,220,round(255*alpha)),width=3)
  tracked(ld,kicker,(78,298+slide),9,(154,226,226,round(255*alpha)),1)
  tracked(ld,title,(28,316+slide),30,(240,247,247,round(255*alpha)),1.5*(1-smooth((t-a)/.8)))
  ld.text((31,357+slide),sub,font=font(12),fill=(207,226,230,round(255*alpha)))
  im=Image.alpha_composite(im,local)
  if 8.7<=t<11.5:
   # Clear separation of illustrated food examples from observed encounter.
   ld=ImageDraw.Draw(im);ld.rounded_rectangle((500,303,737,370),radius=7,fill=(2,18,30,195),outline=(85,159,172,150))
   ld.text((513,313),'DIET / BALEEN FILTER FEEDER',font=font(9,True),fill=(112,222,219,230))
   ld.text((513,335),'Fish silhouettes illustrative hain',font=font(10),fill=(216,232,234,230))
 im=Image.alpha_composite(im,g)
 # Fade from black only on opening; no end fade that pretends full story resolution.
 if t<.25:im=Image.blend(Image.new('RGBA',im.size,(0,0,0,255)),im,smooth(t/.25))
 return im.convert('RGB')

if '--preview' in __import__('sys').argv:
 for f in [36,144,240,324,432]:
  # Tests are before final corrections; preview only.
  original=FRAMES/f'{f:04}.png';temp=False
  if not original.exists():shutil.copy(FRAMES/f'test_{f:04}.png',original);temp=True
  composite(f).save(OUT/f'opening_graphic_preview_{f:04}.png')
  if temp:original.unlink()
 raise SystemExit

missing=[f for f in range(480) if not (FRAMES/f'{f:04}.png').exists()]
if missing:raise RuntimeError(f'{len(missing)} rendered frames missing')
# Mix externally sourced music/field recordings under narration. No fake whale calls.
audio=OUT/'opening_mix.wav'
filters=';'.join([
 '[0:a]atempo=0.93,highpass=f=75,loudnorm=I=-16:TP=-2:LRA=7,adelay=600|600,apad,atrim=duration=20,asplit=2[voice][key]',
 '[1:a]atrim=start=0:end=20,asetpts=PTS-STARTPTS,highpass=f=70,lowpass=f=8500,loudnorm=I=-25:TP=-5:LRA=8,afade=t=in:d=1.1,afade=t=out:st=19:d=1[music]',
 '[music][key]sidechaincompress=threshold=0.035:ratio=6:attack=18:release=300[ducked]',
 '[2:a]atrim=duration=20,asetpts=PTS-STARTPTS,highpass=f=120,lowpass=f=1700,volume=0.14,afade=t=in:d=1,afade=t=out:st=19:d=1[water]',
 '[3:a]atrim=duration=3,asetpts=PTS-STARTPTS,highpass=f=100,lowpass=f=1200,volume=0.045,afade=t=in:d=0.2,afade=t=out:st=2:d=1,adelay=11500|11500,apad,atrim=duration=20[detail]',
 '[voice][ducked][water][detail]amix=inputs=4:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=8,aresample=48000,atrim=duration=20[out]'])
subprocess.run([FF,'-y','-i',str(OUT/'opening_narration.wav'),'-i',str(OUT/'audio/beneath.mp3'),'-stream_loop','-1','-i',str(OUT/'audio/under_reef.ogg'),'-i',str(OUT/'audio/uw_swim.ogg'),'-filter_complex',filters,'-map','[out]','-ac','2',str(audio)],check=True)
video=OUT/'MONARCH_CAM_OPENING_20S_REVIEW.mp4'
command=[FF,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(audio),'-map','0:v','-map','1:a','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','20','-movflags','+faststart','-metadata','comment=Illustrative reconstruction. Killer Whale by Trouvaille/dashdu CC BY 4.0; Tidewater humpback MIT DRG Software Solutions LLC; Beneath by AERIS MUSIC CC0. Changes: geometry animation, materials, staging, compositing and audio mix. See accompanying credits.',str(video)]
proc=subprocess.Popen(command,stdin=subprocess.PIPE)
for f in range(480):
 proc.stdin.write(composite(f).tobytes())
proc.stdin.close()
if proc.wait()!=0:raise RuntimeError('encode failed')
subprocess.run([FF,'-v','error','-xerror','-i',str(video),'-f','null','-'],check=True)
for f in [36,144,240,324,432]:composite(f).save(OUT/f'opening_review_frame_{f:04}.jpg',quality=92)
receipt={'file':video.name,'duration_s':20,'frames':480,'fps':24,'resolution':[W,H],'audio':'stereo AAC 48k, recorded generated narration plus externally sourced CC0 music/field recordings','voice_id':'voice-07','source_narration_s':17.72,'voice_tempo_factor':.93,'voice_delay_s':.6,'rendered_frames':480,'narration_scope':'original v2 opening through record kiya gaya hai; no condensed ending','sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'bytes':video.stat().st_size,'full_decode':'pass','review_status':'review cut; actual listening and independent artistic validation not established'}
(OUT/'opening_delivery_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
