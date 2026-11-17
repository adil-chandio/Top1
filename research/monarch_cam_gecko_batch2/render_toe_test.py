"""Original schematic release test; NOT a measured anatomical/gait reconstruction.
Run using bpy4.2 Python with runtime dependencies. Output stays ignored.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
OUT=Path('studio/runtime/gecko/toe-test');OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(name,col):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);return m
skin=mat('schematic amber',(0.85,.35,.055));pad=mat('ventral pad',(.23,.09,.035));contact=mat('illustrative contact NOT force data',(.08,.8,.58));wall=mat('substrate',(.09,.14,.19));white=mat('labels',(.8,.89,.94))
def cube(name,loc,scale,ma):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(ma);return o
cube('substrate',(1.8,0,-.12),(5.4,2.4,.2),wall)
# Twelve deformation links represent a continuous pad, NOT twelve phalanges.
links=[];marks=[];n=12;L=.28
for i in range(n):
 bpy.ops.object.empty_add();pivot=bpy.context.object;pivot.name=f'deformation_link_NOT_bone_{i}'
 if i:pivot.parent=links[-1];pivot.location=(L,0,0)
 else:pivot.location=(0,0,.16)
 width=.40+.12*math.sin(math.pi*i/(n-1))
 o=cube('continuous_pad_segment',(0,0,0),(L*1.035,width,.28),skin);o.parent=pivot;o.location=(L/2,0,0)
 for x in [.065,.18]:
  o=cube('transverse_lamella_schematic',(0,0,0),(.035,width*.97,.027),pad);o.parent=pivot;o.location=(x,0,-.143)
 links.append(pivot)
 marks.append(cube('contact_overlay_not_force',((i+.5)*L,-.36,.001),(L*.90,.055,.018),contact))
def label(text,loc,size):
 bpy.ops.object.text_add(location=loc);o=bpy.context.object;o.data.body=text;o.data.size=size;o.data.extrude=0;o.data.materials.append(white)
label('SCHEMATIC / NOT MEASURED TOKAY GAIT',(-.55,-1.05,.02),.14)
label('PROXIMAL',(-.25,.72,.01),.14);label('DISTAL TIP',(2.9,.72,.01),.14)
label('Green = illustrative contact region',(-.4,-.75,.02),.13)
# Camera reads the side/front and dorsal surface; underside lamellae remain visible on lift.
bpy.ops.object.camera_add(location=(5.1,-7.5,5.4));cam=bpy.context.object;cam.rotation_euler=(Vector((1.6,0,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8;bpy.context.scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(1,-3,6));bpy.context.object.data.energy=650;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=5
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=True;s.render.resolution_x=640;s.render.resolution_y=360;s.render.resolution_percentage=100;s.world.color=(.15,.15,.15);s.render.image_settings.file_format='PNG';s.render.fps=18
qc=[]
for frame in range(1,37):
 links[0].location.z=.16+max(0,(frame-29)/7)*.38
 # Distal links bend first. Positive upward curvature leaves proximal contacts fixed.
 for i,p in enumerate(links):
  onset=7+(n-1-i)*1.5;t=max(0,min(1,(frame-onset)/8));smooth=t*t*(3-2*t)
  p.rotation_euler[1]=-math.radians(9)*smooth
 bpy.context.view_layer.update();count=0;minz=100
 for i,p in enumerate(links):
  # Lower corners conservatively check surface exclusion.
  z=min((p.matrix_world@Vector((x,y,-.157))).z for x in [0,L] for y in [-.28,.28]);minz=min(minz,z)
  touching=z<.012;marks[i].hide_render=not touching;count+=touching
 qc.append({'frame':frame,'contact_links':count,'lowest_pad_z':minz,'segment_length':L})
 s.render.filepath=str(OUT/f'{frame:04}.png');bpy.ops.render.render(write_still=True)
assert all(x['lowest_pad_z']>=-.00001 for x in qc)
assert qc[0]['contact_links']==n and qc[-1]['contact_links']==0
(OUT/'numeric-qc.json').write_text(json.dumps(qc,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'schematic-toe.blend'))
print('RENDER_AND_NUMERIC_QC_COMPLETE',flush=True)
