"""Render original, continuous-mesh mechanism prototype. Not tokay anatomy approval."""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from toe_cycle_geometry import *
OUT=Path('studio/runtime/gecko/continuous-cycle');OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
skin=material('original illustrative pad',(.74,.33,.10));lam=material('transverse ventral ridges',(.28,.105,.035));wall=material('neutral substrate',(.055,.09,.12));green=material('contact proximity indicator',(.03,.85,.52))
def mesh(name,verts,faces,mat):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);o.data.materials.append(mat);return o
faces=[]
for i in range(RINGS-1):
 for j in range(SIDES):
  a=i*SIDES+j;b=i*SIDES+(j+1)%SIDES;faces.append((a,b,b+SIDES,a+SIDES))
faces += [tuple(reversed(range(SIDES))),tuple((RINGS-1)*SIDES+j for j in range(SIDES))]
toe=mesh('single_connected_pad_NOT_skeleton',surface(1),faces,skin)
for p in toe.data.polygons:p.use_smooth=True
# Original procedural ridges. Count/spacing are illustrative, not a tokay census.
ridges=[]
for ri in range(5,RINGS-4,4):
 curve=bpy.data.curves.new('lamella_schematic','CURVE');curve.dimensions='3D';curve.bevel_depth=.008;curve.bevel_resolution=1
 sp=curve.splines.new('POLY');sp.points.add(16)
 ob=bpy.data.objects.new('transverse_ridge',curve);bpy.context.collection.objects.link(ob);curve.materials.append(lam);ridges.append((ri,sp))
bpy.ops.mesh.primitive_cube_add(size=1,location=(1.65,0,-.10));bpy.context.object.scale=(5,2,.2);bpy.context.object.data.materials.append(wall)
marks=[]
for i in range(20):
 bpy.ops.mesh.primitive_cube_add(size=1,location=((i+.5)*LENGTH/20,-.40,.008));o=bpy.context.object;o.scale=(LENGTH/20*.88,.045,.012);o.data.materials.append(green);marks.append(o)
bpy.ops.object.camera_add(location=(4.2,-7.8,4.7));cam=bpy.context.object;cam.rotation_euler=(Vector((1.6,0,1.15))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8.5;bpy.context.scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(0,-3,6));bpy.context.object.data.energy=700;bpy.context.object.data.size=5
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=6;s.cycles.use_denoising=True;s.render.resolution_x=768;s.render.resolution_y=432;s.render.resolution_percentage=100;s.world.color=(.12,.12,.12);s.render.image_settings.file_format='PNG';s.render.fps=15
# Verify every mesh vertex stays inside camera and outside HUD bands for all frames.
from bpy_extras.object_utils import world_to_camera_view
bpy.context.view_layer.update()
for frame in range(1,FRAMES+1):
 for co in surface(frame):
  uv=world_to_camera_view(s,cam,Vector(co))
  assert .02 < uv.x < .98 and .13 < uv.y < .84, (frame,tuple(uv))
qc=[]
for f in range(1,FRAMES+1):
 verts=surface(f)
 for v,co in zip(toe.data.vertices,verts):v.co=co
 toe.data.update();centers=centerline(f)
 for ri,sp in ridges:
  x,z,theta=centers[ri];w=width(ri/(RINGS-1))
  for j,p in enumerate(sp.points):
   a=math.pi*.56+math.pi*.88*j/16;off=(RADIUS_Z+.003)*math.cos(a)
   p.co=(x-math.sin(theta)*off,(w+.002)*math.sin(a),z+math.cos(theta)*off,1)
 flags=contact_flags(f)
 for i,o in enumerate(marks):o.hide_render=not flags[round((i+.5)*(RINGS-1)/20)]
 minz=min(v[2] for v in verts)
 assert minz>=0
 qc.append({'frame':f,'phase':phase(f),'lowest_mesh_z':minz,'contact_rings':sum(flags)})
 s.render.filepath=str(OUT/f'{f:04}.png');bpy.ops.render.render(write_still=True)
(OUT/'numeric-qc.json').write_text(json.dumps(qc,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'continuous-schematic.blend'))
print('CONTINUOUS_CYCLE_COMPLETE',flush=True)
