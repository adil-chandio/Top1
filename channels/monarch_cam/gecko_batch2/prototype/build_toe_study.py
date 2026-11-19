#!/usr/bin/env python3
"""Conceptual gecko digit underside, not a scale-accurate anatomical reconstruction."""
import bpy, math
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.render.resolution_x=800;s.render.resolution_y=450;s.view_settings.view_transform='AgX';s.world.color=(.03,.03,.03)
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;q=m.node_tree.nodes.get('Principled BSDF');q.inputs['Base Color'].default_value=(*c,1);q.inputs['Roughness'].default_value=.55;return m
skin=mat('Warm gecko pad',(.29,.15,.075));scale=mat('Lamellae',(.59,.37,.19));bg=mat('Dark background',(.025,.065,.075));claw=mat('claw',(.11,.09,.06))
def sph(name,pos,size,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=pos);o=bpy.context.object;o.name=name;o.scale=size;o.data.materials.append(m);bpy.ops.object.shade_smooth();return o
# The broad toe is viewed from its plantar side, enlarged; the model is schematic.
sph('Toe pad',(.05,0,.25),(2.15,.72,.27),skin);sph('Proximal digit',(-2.1,0,.24),(.65,.38,.23),skin)
# Curved thin transverse bands on the visible underside. Curves follow the toe's outline.
for i in range(22):
 x=-1.73+i*.165; u=(x-.05)/2.15; width=.72*math.sqrt(max(0,1-u*u))*.96
 pts=[]
 for j in range(25):
  y=-width+2*width*j/24;z=.25+.27*math.sqrt(max(0,1-u*u-(y/.72)**2))+.012
  pts.append((x+.045*(y/width)**2,y,z))
 cu=bpy.data.curves.new('Lamella arc','CURVE');cu.dimensions='3D';cu.resolution_u=2;cu.bevel_depth=.022;cu.bevel_resolution=3;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for k,co in enumerate(pts):sp.points[k].co=(*co,1)
 ob=bpy.data.objects.new('Lamella schematic',cu);bpy.context.collection.objects.link(ob);ob.data.materials.append(scale)
# Hint of a terminal claw; not all gecko digits carry one.
sph('Claw base',(2.09,0,.26),(.22,.18,.12),claw)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.08));bpy.context.object.data.materials.append(bg)
bpy.ops.object.camera_add(location=(.0,-2.8,8));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.15))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.8;s.camera=cam
for loc,power,size in [((-2,-3,5),850,5),((3,3,4),650,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,0,0))-l.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(p/'toe-study.png');bpy.ops.render.render(write_still=True)
