#!/usr/bin/env python3
"""Assemble draft using Pillow and imageio-ffmpeg; synthesized bed is original."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math, subprocess, wave, struct, imageio_ffmpeg
p=Path(__file__).resolve().parent; dst=p/'preview_frames_v2';dst.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',25);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
for i in range(72):
 if i<48:
  im=Image.open(p/'rendered_v2'/f'{i+1:03}.png').convert('RGB');headline='Many geckos can climb smooth surfaces' if i<24 else 'Adhesive toe pads help them grip'
 else:
  # Static diagram with gentle push-in: the earlier rigid lifting animation is misleading.
  base=Image.open(p.parent/'micro_contact_proof'/'frame-10.png').convert('RGB'); zoom=1+0.08*(i-48)/23; w=int(800/zoom);h=int(450/zoom); im=base.crop(((800-w)//2,(450-h)//2,(800+w)//2,(450+h)//2)).resize((640,360),Image.Resampling.LANCZOS);headline='Microscopic structures make close contact'
 over=Image.new('RGBA',im.size);d=ImageDraw.Draw(over);d.rectangle((0,282,640,360),fill=(4,12,17,220));d.text((22,293),headline,font=font,fill='white');d.text((22,330),'CONCEPT PROTOTYPE  •  schematic, not to scale',font=small,fill=(178,208,210,255));im=Image.alpha_composite(im.convert('RGBA'),over).convert('RGB');im.save(dst/f'{i:03}.png')
# Simple original electronic chord bed; not a simulation of natural gecko sounds.
sr=22050; duration=9; audio=p/'prototype-bed.wav'
with wave.open(str(audio),'wb') as w:
 w.setparams((1,2,sr,sr*duration,'NONE','not compressed'))
 data=bytearray()
 for n in range(sr*duration):
  t=n/sr;fade=min(1,t/1.3,(duration-t)/1.3);v=sum(math.sin(2*math.pi*f*t)*a for f,a in [(110,.35),(164.81,.22),(220,.15),(329.63,.08)])*.13*fade
  data.extend(struct.pack('<h',round(v*32767)))
 w.writeframes(data)
ff=imageio_ffmpeg.get_ffmpeg_exe();subprocess.run([ff,'-y','-loglevel','error','-framerate','8','-i',str(dst/'%03d.png'),'-i',str(audio),'-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-movflags','+faststart','-shortest',str(p/'gecko-concept-v2.mp4')],check=True)
audio.unlink();print('Built',p/'gecko-concept-v2.mp4')
