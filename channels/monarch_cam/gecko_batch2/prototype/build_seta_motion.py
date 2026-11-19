#!/usr/bin/env python3
"""Conceptual multiscale animation, illustrative only; not a physics simulation."""
import bpy, math
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parent;out=p/'seta_frames';out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=6;s.render.resolution_x=640;s.render.resolution_y=360;s.view_settings.view_transform='AgX';s.world.color=(.035,.035,.035)
def mat(name,c,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;q=m.node_tree.nodes.get('Principled BSDF');q.inputs['Base Color'].default_value=(*c,1);q.inputs['Roughness'].default_value=.48;q.inputs['Metallic'].default_value=metal;return m
stemmat=mat('seta body',(.55,.31,.13));tipmat=mat('spatula tips',(.94,.65,.27));padmat=mat('lamella section',(.30,.16,.08));surface=mat('contact surface',(.04,.19,.24),.1)
def box(n,loc,scale,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.scale=scale;o.data.materials.append(m);return o
box('Surface',(0,0,-.16),(8,4,.3),surface);pad=box('Lamella section',(0,0,2.25),(6,2.4,.32),padmat)
def curve(name,material,r):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=8;c.bevel_depth=r;c.bevel_resolution=2;sp=c.splines.new('BEZIER');sp.bezier_points.add(3)
 for pt in sp.bezier_points:pt.handle_left_type='AUTO';pt.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(material);return o
structures=[]
for iy in range(3):
 for ix in range(5):
  x=-2+ix*.95;y=(iy-1)*.75;main=curve('Enlarged seta',stemmat,.045);branches=[]
  for j in range(7):
   phi=(j-3)*.38; b=curve('Schematic branch',tipmat,.014)
   bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6);tip=bpy.context.object;tip.name='Conceptual contact tip';tip.scale=(.10,.055,.022);tip.data.materials.append(tipmat);branches.append((phi,b,tip))
  structures.append((x,y,main,branches))
bpy.ops.object.camera_add(location=(6,-8,4.5));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=7.8;s.camera=cam
for loc,power,size in [((0,-4,7),1100,5),((-4,3,4),800,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler()
def setpts(o,pts):
 for q,co in zip(o.data.splines[0].bezier_points,pts):q.co=co
for frame in range(24):
 # Small lateral movement of lamella relative to fixed tips represents a concept of loading,
 # not measurements, adhesion force or a real motion sequence.
 shift=.30*(.5-.5*math.cos(math.pi*min(frame,18)/18));pad.location.x=shift
 for x,y,main,branches in structures:
  top=Vector((x+shift,y,2.10)); junction=Vector((x+.42+shift*.4,y,.61));
  setpts(main,[top,(x+.12+shift*.8,y,1.65),(x+.28+shift*.6,y,1.13),junction])
  for phi,b,tip in branches:
   end=Vector((x+.7+phi*.4,y+phi*.19,.025)); q=junction.lerp(end,.45);q.z=.35
   setpts(b,[junction,junction.lerp(q,.7),q,end]);tip.location=end;tip.rotation_euler.z=phi*.3
 s.render.filepath=str(out/f'{frame:03}.png');bpy.ops.render.render(write_still=True)
