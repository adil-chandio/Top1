"""Add readable explanatory HUD and package prototype, never source reference media."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from toe_cycle_geometry import phase
root=Path('studio/runtime/gecko/continuous-cycle')
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(fontpath,19);small=ImageFont.truetype(fontpath,14)
frames=[]
for f in range(1,61):
 im=Image.open(root/f'{f:04}.png').convert('RGB');d=ImageDraw.Draw(im)
 d.rectangle((0,0,768,67),fill='#10202d');d.text((18,8),f'{phase(f)}  |  {f:02}/60',font=font,fill='white')
 d.text((18,38),'Original schematic - NOT measured Tokay anatomy, timing or forces',font=small,fill='#c1d1dd')
 d.rectangle((0,382,768,432),fill='#10202d');d.text((18,389),'PROXIMAL / base                                  DISTAL / tip',font=small,fill='white')
 d.text((18,409),'Green strip = mesh proximity, not adhesive strength or setal contact area',font=small,fill='#73dfbd')
 if 21<=f<=30:
  d.line((340,345,220,345),fill='#ffe18a',width=5);d.polygon([(220,345),(236,337),(236,353)],fill='#ffe18a')
  d.text((270,315),'Proximal shear: symbolic only',font=small,fill='#ffe18a')
 frames.append(im)
frames[0].save(root/'continuous-cycle-preview.gif',save_all=True,append_images=frames[1:],duration=100,loop=0)
nums=[1,6,12,25,36,37,38,39,40,48,54,60]
out=Image.new('RGB',(768*3,432*4))
for i,f in enumerate(nums):out.paste(frames[f-1],((i%3)*768,(i//3)*432))
out.save(root/'visual-qc.jpg')
frames[24].save(root/'loading-frame.png')
