"""Original animated low-angle setae/contact schematic, not literal microscopy.
48 per-frame poses at24fps. No experimental angles/counts/times asserted.
"""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
OUT=Path('studio/runtime/gecko/macro-pass');OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*c,1);return m
hair=mat('schematic shaft',(.72,.43,.18));tip=mat('flattened branching tips',(.12,.58,.47));wall=mat('substrate',(.045,.1,.15))
def curve(pts,r):
 c=bpy.data.curves.new('originalbranchedseta','CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=1;sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 o=bpy.data.objects.new('schematic branch',c);bpy.context.collection.objects.link(o);c.materials.append(hair);return o
moving=[]
# Inclined shafts give no impression of an upright loaded hair forest.
for row in range(2):
 for col in range(4):
  x=-2+col*1.0;y=-.55+row*1.1
  shaft=curve([(x-.6,y,.52),(x-.1,y,.32),(x+.45,y,.16)],.024);moving.append(shaft)
  for j in range(3):
   yy=y+(j-1)*.22;branch=curve([(x+.45,y,.16),(x+.62,yy,.07),(x+.82,yy,.024)],.009);moving.append(branch)
   bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=(x+.87,yy,.020));o=bpy.context.object;o.name='flattened contact tip';o.scale=(.11,.065,.02);o.data.materials.append(tip);moving.append(o)
   for p in o.data.polygons:p.use_smooth=True
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.13));o=bpy.context.object;o.scale=(6.5,3.6,.22);o.data.materials.append(wall)
bpy.ops.object.camera_add(location=(3.8,-5.8,3.8));cam=bpy.context.object;target=Vector((0,0,.2));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=6.9;s=bpy.context.scene;s.camera=cam
for pos,energy,size in [((-2,-2,5),650,5),((3,2,3),350,4)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=energy;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='CYCLES';s.cycles.samples=4;s.cycles.use_denoising=True;s.render.resolution_x=512;s.render.resolution_y=512;s.render.resolution_percentage=100;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.world.color=(.08,.08,.08)
base=[(o,o.location.copy()) for o in moving]
for i in range(48):
 u=i/47;smooth=u*u*(3-2*u);gap=.20*(1-smooth)
 for o,loc in base:o.location=loc+Vector((-.10*(1-smooth),0,gap))
 s.render.filepath=str(OUT/f'{i:04}.png');bpy.ops.render.render(write_still=True)
(OUT/'geometry-note.json').write_text(json.dumps({'frames':48,'fps':24,'motion':'qualitative group approach/shear positioning; not measured engagement sequence','scale':'illustrative counts/spacing/angles','substrate_top':-.02,'lowest_final_tip_z':0,'note':'microscopic separation/nearcontact schematic; not simulated molecular bonds'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'macro-contact.blend'));print('MACRO_CONTACT_COMPLETE',flush=True)
