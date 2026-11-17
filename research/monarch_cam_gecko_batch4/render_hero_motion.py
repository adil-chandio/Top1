"""36-frame original foot skin-deformation shot, qualitative schematic only.
NOT a bone/tendon rig or measured Tokay gait. Preserves side/digit identities.
"""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
OUT=Path('studio/runtime/gecko/motion-pass/hero');OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path('studio/runtime/gecko/visual-pass/source-informed-foot.blend').resolve()))
s=bpy.context.scene;s.cycles.samples=4;s.render.resolution_x=512;s.render.resolution_y=512;s.render.film_transparent=True;s.render.image_settings.color_mode='RGBA';s.render.fps=24
# Capture original external skin + curve geometry; a common warp avoids ridges detaching.
meshes=[];curves=[]
for o in s.objects:
 if o.type=='MESH' and o.name=='original_continuous_foot_skin':meshes.append((o,[v.co.copy() for v in o.data.vertices]))
 if o.type=='CURVE':
  for sp in o.data.splines:curves.append((o,sp,[Vector(p.co[:3]) for p in sp.points]))
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def deform(v,progress):
 # DigitIV points to screen-left in the established left-pes ventral convention.
 if v.x>=-.7 or abs(v.y-.12)>.65:return v.copy()
 distance=-v.x-.7;u=min(1,distance/2.65);N=80;ds=distance/N;cx=0;cz=0;theta=0
 for k in range(N):
  f=(k+.5)/N*u;theta=1.15*f*smooth((progress-(1-f)*.6)/.4);cx+=ds*math.cos(theta);cz+=ds*math.sin(theta)
 # Ventralz+; hyperextension curls away from ventral surface, towards dorsalz-.
 return Vector((-.7-cx+v.z*math.sin(theta),v.y,-cz+v.z*math.cos(theta)))
qc=[]
for frame in range(36):
 p=smooth(frame/35)
 for o,base in meshes:
  for vertex,orig in zip(o.data.vertices,base):vertex.co=deform(orig,p)
  o.data.update()
 for o,sp,base in curves:
  inv=o.matrix_world.inverted()
  for pt,orig in zip(sp.points,base):
   world=o.matrix_world@orig;co=inv@deform(world,p);pt.co=(*co,1)
 assert all(math.isfinite(v.co.z) for o,_ in meshes for v in o.data.vertices)
 qc.append({'frame':frame,'progress':p})
 s.render.filepath=str(OUT/f'{frame:04}.png');bpy.ops.render.render(write_still=True)
(OUT/'motion-note.json').write_text(json.dumps({'frames':36,'fps':24,'kind':'common skin-and-ridge qualitative warp for digitIV; not biological articulation validation','qc':qc},indent=2))
print('HERO_MOTION_COMPLETE',flush=True)
