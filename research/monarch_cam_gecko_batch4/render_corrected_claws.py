"""36-frame original foot skin-deformation shot, qualitative schematic only.
NOT a bone/tendon rig or measured Tokay gait. Preserves side/digit identities.
"""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
OUT=Path('studio/runtime/gecko/claw-framing-pass/hero');OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path('studio/runtime/gecko/visual-pass/source-informed-foot.blend').resolve()))
s=bpy.context.scene;s.cycles.samples=4;s.render.resolution_x=512;s.render.resolution_y=512;s.render.film_transparent=True;s.render.image_settings.color_mode='RGBA';s.render.fps=24
# Replace straight claw markers with original tapered recurved keratin schematics.
spec=json.loads(Path('research/monarch_cam_gecko_batch2/LEFT_PES_LAYOUT_SPEC.json').read_text())
for obj in list(s.objects):
 if obj.name.startswith('claw_marker_'):bpy.data.objects.remove(obj,do_unlink=True)
clawmat=bpy.data.materials.get('illustrative keratin claw')
claws=[]
for g in spec['digits']:
 if not g['claw']:continue
 a=Vector(((g['start'][0]-500)/100,(450-g['start'][1])/100,0))*.65
 b=Vector(((g['tip'][0]-500)/100,(450-g['tip'][1])/100,0));axis=(b-a).normalized()
 controls=[b-axis*.16+Vector((0,0,-.11)),b+axis*.06+Vector((0,0,-.40)),b+axis*.45+Vector((0,0,-.26)),b+axis*.25+Vector((0,0,.12))]
 c=bpy.data.curves.new('recurvedclaw_'+g['id'],'CURVE');c.dimensions='3D';c.bevel_depth=.07;c.bevel_resolution=3
 sp=c.splines.new('POLY');sp.points.add(24)
 for i,p in enumerate(sp.points):
  t=i/24;v=controls[0]*(1-t)**3+controls[1]*3*(1-t)**2*t+controls[2]*3*(1-t)*t*t+controls[3]*t**3
  p.co=(*v,1);p.radius=max(.015,(1-t)**.8)
 obj=bpy.data.objects.new('tapered_claw_'+g['id'],c);bpy.context.collection.objects.link(obj);c.materials.append(clawmat);claws.append(g['id'])
assert claws==['II','III','IV','V']
lengths=[(Vector(g['tip'])-Vector(g['start'])).length for g in spec['digits']]
assert lengths[0]==min(lengths)
(OUT/'external-feature-check.json').write_text(json.dumps({'claws':claws,'clawless_digit':'I','shortest_digit':'I','form':'original taper/recurve; illustrative not measured morphology','biological_joint_validation':False},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'corrected-foot.blend'))
# Lateral diagnostic specifically checks the curved/tapered end, not a new production shot.
cam=s.camera;savedloc=cam.location.copy();savedrot=cam.rotation_euler.copy();savedscale=cam.data.ortho_scale
cam.location=(-4.2,-1.2,1.2);cam.rotation_euler=(Vector((-3.05,.15,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.5
s.render.filepath=str(OUT/'claw-lateral-check.png');bpy.ops.render.render(write_still=True)
cam.location=savedloc;cam.rotation_euler=savedrot;cam.data.ortho_scale=savedscale

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
