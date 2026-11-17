"""Original reference-informed 2D blocking study, NOT traced or measured anatomy.
Identities/side/claw rule from Russell et al2026 Fig1b; formula from Fig2b.
"""
from pathlib import Path
import math,json
from PIL import Image,ImageDraw,ImageFont
OUT=Path('studio/runtime/gecko/anatomy');OUT.mkdir(parents=True,exist_ok=True)
S=2;W=1400;H=1000
im=Image.new('RGB',(W*S,H*S),'#101b27');d=ImageDraw.Draw(im)
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def font(n):return ImageFont.truetype(fontpath,n*S)
def text(pos,t,n=20,col='#dce8ed'):d.text((pos[0]*S,pos[1]*S),t,font=font(n),fill=col)
def line(ps,fill,width):d.line([(x*S,y*S) for x,y in ps],fill=fill,width=round(width*S),joint='curve')
def polygon(ps,fill):d.polygon([(x*S,y*S) for x,y in ps],fill=fill)
def ellipse(box,col):d.ellipse(tuple(v*S for v in box),fill=col)
text((40,26),'TOKAY / LEFT HIND FOOT',32);text((40,72),'Ventral layout study — original procedural blocking, not a measured reconstruction',20,'#8ec8da')
# Deliberately non-traced coordinates. Foot side/orientation matches Fig1b's labelled view.
# Orders/proportions are layout decisions; no fan angle or length measurements claimed.
digits=[{'id':'I','start':(570,440),'tip':(730,355),'width':42,'claw':False,'phalanges':2},
 {'id':'II','start':(550,395),'tip':(640,210),'width':48,'claw':True,'phalanges':3},
 {'id':'III','start':(485,370),'tip':(435,160),'width':49,'claw':True,'phalanges':4},
 {'id':'IV','start':(425,440),'tip':(195,435),'width':52,'claw':True,'phalanges':5},
 {'id':'V','start':(470,500),'tip':(355,715),'width':50,'claw':True,'phalanges':4}]
# Ankle / plantar body are intentionally simplified. Only distal digit topology is studied.
polygon([(495,470),(590,455),(695,645),(620,690)],'#9c704e')
ellipse((405,345,605,550),'#c2986a')
for g in digits:
 x0,y0=g['start'];xt,yt=g['tip'];dx=xt-x0;dy=yt-y0;length=math.hypot(dx,dy);tx=dx/length;ty=dy/length;nx=-ty;ny=tx
 def point(u):return x0+dx*u,y0+dy*u
 def radius(u):return g['width']*(.46+.54*math.sin(math.pi*u)**.55)
 # Capsule-like toe outline with original analytic width profile.
 left=[];right=[]
 for i in range(41):
  u=i/40;x,y=point(u);r=radius(u);left.append((x+nx*r,y+ny*r));right.append((x-nx*r,y-ny*r))
 polygon(left+right[::-1],'#deb889');ellipse((xt-20,yt-20,xt+20,yt+20),'#deb889')
 # Transverse enlarged scale marks, not definitive LDT-zone or setal-field boundaries.
 for k in range(2,16):
  u=k/17;x,y=point(u);r=radius(u)*.90
  pts=[]
  for j in range(13):
   v=-1+2*j/12;bend=6*(1-v*v)
   pts.append((x+nx*r*v+tx*bend,y+ny*r*v+ty*bend))
  line(pts,'#8a603f',2)
 if g['claw']:
  # Placement marker only: no claim to reconstructed ungual anatomy or articulation.
  claw=[(xt+nx*11,yt+ny*11),(xt+tx*24+nx*8,yt+ty*24+ny*8),(xt+tx*34-nx*5,yt+ty*34-ny*5),(xt+tx*17-nx*4,yt+ty*17-ny*4)]
  polygon(claw,'#ece2c9')
 lx=xt+tx*55;ly=yt+ty*55;text((lx-12,ly-15),g['id'],25,'#72debe')
text((665,675),'ANKLE',16,'#a8b7c5')
line([(790,140),(790,830)],'#31465a',2)
text((835,150),'PINNED ANATOMY',25,'#72debe')
for i,t in enumerate(['Species: Gekko gecko','Side: LEFT pes (hind foot)','View: VENTRAL / underside','I: shortest, no claw','II–V: claw-bearing digits']):text((835,205+i*39),t,19)
text((835,435),'Radiograph: pes phalanges',20,'#8ec8da');text((835,475),'I    II    III    IV    V',22);text((835,514),'2    3      4      5     4',22,'#72debe')
text((835,575),'NOT YET VALIDATED',21,'#ffd086')
for i,t in enumerate(['Exact lengths / fan angles','Claw shape / pivots','LDT-zone boundary','Scale counts / force / gait']):text((835,620+i*34),t,18)
text((50,810),'No human thumb • No claw on I • No copied forefoot formula',21,'#8ec8da')
text((40,867),'Original layout informed by Russell, Delannoy & Garner (2026), Figs 1b and 2b.',17)
text((40,898),'DOI 10.1111/joa.70251 • Source article CC BY 4.0 • No source image pixels embedded.',17)
text((40,929),'Transverse marks indicate scale layout only; they do not define the true adhesive area.',17,'#ffd086')
im.resize((W,H),Image.Resampling.LANCZOS).save(OUT/'left-pes-layout-study.png')
Path('research/monarch_cam_gecko_batch2/LEFT_PES_LAYOUT_SPEC.json').write_text(json.dumps({'species':'Gekko gecko','side':'left','appendage':'pes','view':'ventral','geometry_status':'original unmeasured2Dblocking, not traced; not final anatomy','source_figures':{'layout':'2026 Fig1b left pes ventral','phalangeal_counts':'2026 Fig2b right pes dorsal; counts transferable, image coordinates NOT transferred'},'digits':digits,'warning':'pixel coordinates/widths are illustration choices, NOT biological measurements; claw marks are placeholders'},indent=2)+'\n')
assert [g['phalanges'] for g in digits]==[2,3,4,5,4]
assert sum(g['claw'] for g in digits)==4 and not digits[0]['claw']
assert len(digits)==5
lengths=[math.dist(g['start'],g['tip']) for g in digits]
assert lengths[0]==min(lengths)
print('Layout generated;5digits,4claw markers,clawlessI; anatomy proportions still unvalidated')
