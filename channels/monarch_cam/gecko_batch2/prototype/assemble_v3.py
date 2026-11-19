#!/usr/bin/env python3
"""Assemble 12-second research prototype, not a final scientific simulation."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math,struct,wave,subprocess,imageio_ffmpeg
p=Path(__file__).resolve().parent;out=p/'preview_frames_v3';out.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',24);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
for i in range(96):
 if i<48:
  im=Image.open(p/'rendered_v2'/f'{i+1:03}.png').convert('RGB');head='Many geckos climb smooth surfaces' if i<24 else 'Adhesive toe pads help them grip'
 elif i<72:
  base=Image.open(p/'toe-study.png').convert('RGB');zoom=1+.10*(i-48)/23;w=int(800/zoom);h=int(450/zoom);im=base.crop(((800-w)//2,(450-h)//2,(800+w)//2,(450+h)//2)).resize((640,360),Image.Resampling.LANCZOS);head='Toe pads have rows called lamellae'
 else:
  im=Image.open(p/'seta_frames'/f'{i-72:03}.png').convert('RGB');head='Tiny setae branch into contact tips'
 over=Image.new('RGBA',im.size);d=ImageDraw.Draw(over);d.rectangle((0,282,640,360),fill=(4,12,17,225));d.text((22,293),head,font=font,fill='white');d.text((22,330),'RESEARCH PROTOTYPE  •  schematic, not to scale',font=small,fill=(178,208,210,255));Image.alpha_composite(im.convert('RGBA'),over).convert('RGB').save(out/f'{i:03}.png')
sr=22050;duration=12;audio=p/'temporary-sound.wav'
with wave.open(str(audio),'wb') as w:
 w.setparams((1,2,sr,sr*duration,'NONE','not compressed'));data=bytearray()
 for n in range(sr*duration):
  t=n/sr;fade=min(1,t/1.3,(duration-t)/1.3);v=sum(math.sin(2*math.pi*f*t)*a for f,a in [(110,.35),(164.81,.22),(220,.15),(329.63,.08)])*.13*fade;data.extend(struct.pack('<h',round(v*32767)))
 w.writeframes(data)
ff=imageio_ffmpeg.get_ffmpeg_exe();subprocess.run([ff,'-y','-loglevel','error','-framerate','8','-i',str(out/'%03d.png'),'-i',str(audio),'-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-movflags','+faststart','-shortest',str(p/'gecko-concept-v3.mp4')],check=True);audio.unlink();print('Built',p/'gecko-concept-v3.mp4')
