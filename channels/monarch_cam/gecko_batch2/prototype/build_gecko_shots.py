#!/usr/bin/env python3
"""Procedural gecko prototype, stylised and not a species-accurate model."""
import bpy, math
from pathlib import Path
from mathutils import Vector
out=Path(__file__).resolve().parent/'rendered_v2';out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.render.resolution_x=640;s.render.resolution_y=360;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.world.color=(.07,.07,.07)
def material(name,color,rough=.5):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
skin=material('Original orange-green skin',(.26,.32,.15));gold=material('Golden iris',(.75,.40,.08));black=material('Pupil',(.015,.01,.005));pad=material('Toe pads',(.40,.28,.16));rock=material('Surface',(.075,.13,.12))
nt=skin.node_tree;n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=13;n.inputs['Detail'].default_value=3
r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.35;r.color_ramp.elements[0].color=(.09,.14,.055,1);r.color_ramp.elements[1].position=.66;r.color_ramp.elements[1].color=(.48,.31,.13,1)
nt.links.new(n.outputs['Fac'],r.inputs['Fac']);nt.links.new(r.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
def ell(name,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat);bpy.ops.object.shade_smooth();return o
def bone(name,a,b,r1,mat):
 a,b=Vector(a),Vector(b);d=b-a;o=ell(name,(a+b)/2,(r1,r1,d.length/2+r1),mat);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
body=ell('Body',(-.25,0,.62),(1.03,.44,.35),skin);head=ell('Head',(.85,0,.69),(.55,.42,.31),skin);ell('Muzzle',(1.2,0,.59),(.34,.32,.19),skin)
for y in (-1,1):
 ell('Eye',(.99,y*.333,.80),(.19,.12,.19),gold);ell('Pupil',(1.015,y*.429,.81),(.048,.035,.16),black)
points=[(-1.05,0,.68),(-1.55,.02,.56),(-2.0,.10,.44),(-2.40,.18,.39),(-2.65,.23,.39)]
for i in range(len(points)-1):bone('Tail',points[i],points[i+1],.24*(1-i/5),skin)
# Stylized pads are broad cues only; neither precise tokay morphology nor gait.
for x in (-.75,.62):
 for side in (-1,1):
  a=(x,side*.3,.60);b=(x-.1,side*.62,.36);c=(x+.12,side*.86,.07)
  bone('Upper limb',a,b,.12,skin);bone('Lower limb',b,c,.10,skin);ell('Foot',c,(.22,.20,.095),skin)
  for j in range(5):
   t=(x+.16+(j-2)*.105,side*(1.08+.09*(1-abs(j-2)/2)),.015)
   bone('Digit',c,t,.045,skin);ell('Broad illustrative pad',t,(.08,.105,.035),pad)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.17));floor=bpy.context.object;floor.name='Surface';floor.scale=(12,9,.3);floor.data.materials.append(rock)
root=bpy.data.objects.new('Whole gecko drift',None);bpy.context.collection.objects.link(root)
for o in list(bpy.context.scene.objects):
 if o.type=='MESH' and o!=floor:o.parent=root
# Keep the animal stationary: a sliding rigid body would imply a false gait.
root.location.x=0
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';s.camera=cam
for f,loc,target,scale in [(1,(4.6,-6.8,3.8),(0,0,.55),6.0),(24,(4,-6,3.4),(0,0,.55),5.6),(25,(2.5,-3.2,2.4),(.7,-.9,.15),2.15),(48,(2.3,-3,2.2),(.7,-.9,.15),2.0)]:
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 cam.keyframe_insert(data_path='location',frame=f);cam.keyframe_insert(data_path='rotation_euler',frame=f);cam.data.keyframe_insert(data_path='ortho_scale',frame=f)
# No blend between shot 1 and shot 2.
for ob in (cam,cam.data):
 for c in ob.animation_data.action.fcurves:
  for k in c.keyframe_points:k.interpolation='CONSTANT' if k.co.x==24 else 'LINEAR'
for loc,power,size in [((1,-4,7),1100,5),((-3,3,5),700,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,.5))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).resolve().parent/'gecko-concept-v2.blend'))
for f in range(1,49):s.frame_set(f);s.render.filepath=str(out/f'{f:03}.png');bpy.ops.render.render(write_still=True)
