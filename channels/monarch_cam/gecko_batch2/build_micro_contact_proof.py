#!/usr/bin/env python3
"""Original conceptual macro-scale depiction: NOT an anatomically scaled simulation."""
import bpy, math
from mathutils import Vector
from pathlib import Path
out=Path(__file__).resolve().parent/'micro_contact_proof';out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16
s.render.resolution_x=800;s.render.resolution_y=450;s.render.resolution_percentage=100
s.frame_start=1;s.frame_end=36;s.render.fps=12
s.view_settings.view_transform='AgX';s.world.color=(.04,.04,.04)
def mat(n,c,rough=.5,metal=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
skin=mat('Pad cross section - concept',(.47,.24,.11));hair=mat('Seta and tips - concept',(.9,.65,.3));surface=mat('Surface',(.06,.18,.24),.38)
def cube(name,loc,scale,material,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 if bevel:
  mod=o.modifiers.new('soft edges','BEVEL');mod.width=bevel;mod.segments=3
  o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
 return o
def line(name,a,b,r,material,parent=None):
 a,b=Vector(a),Vector(b);v=b-a;mid=(a+b)/2
 bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=v.length,location=mid);o=bpy.context.object;o.name=name;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();o.data.materials.append(material)
 if parent:o.parent=parent
 return o
cube('Surface block',(0,0,-.18),(7,4,.32),surface,.06)
# Translate the entire schematic pad + setae vertically; not a force or detach simulation.
root=bpy.data.objects.new('Concept pad motion',None);bpy.context.collection.objects.link(root)
pad=cube('Schematic pad section',(0,0,1.6),(5.0,2.5,.34),skin,.16);pad.parent=root
# Branching shapes deliberately enlarged and sparse. No scale or numerical force implied.
for ix in range(9):
 for iy in range(5):
  x=-2+ix*.5;y=-.96+iy*.48
  junction=(x+.16,y, .65);line('Schematic seta',(x,y,1.43),junction,.035,hair,root)
  for dx,dy in [(-.19,-.12),(.05,-.16),(.24,0),(.05,.16),(-.19,.12)]:
   tip=(x+.16+dx,y+dy,.015)
   line('Schematic branch',junction,tip,.014,hair,root)
   line('Schematic broad tip',(tip[0]-.06,tip[1],.015),(tip[0]+.06,tip[1],.015),.018,hair,root)
for frame,z in [(1,.8),(10,0),(21,0),(36,.8)]:
 root.location.z=z;root.keyframe_insert(data_path='location',frame=frame)
# Motion is only a clear vertical illustration. Do not claim this represents a real gecko release.
bpy.ops.object.camera_add(location=(7.3,-10.5,5.6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.75))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8.0;s.camera=cam
for loc,power,size in [((1,-6,8),1150,7),((-4,4,5),850,5)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,.6))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'micro-contact-concept.blend'))
for f in range(1,37,3):
 s.frame_set(f);s.render.filepath=str(out/f'frame-{f:02}.png');bpy.ops.render.render(write_still=True)
