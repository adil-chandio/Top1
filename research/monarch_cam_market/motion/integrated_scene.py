"""Combined-scene feasibility iteration. Not an approved final video.
Tidewater MIT humpback + attributed Trouvaille CC BY 4.0 orca derivative.
"""
from pathlib import Path
import sys,json,math
import bpy,numpy as np
BASE=Path(__file__).parent
exec(compile((BASE/'animate_tidewater.py').read_text().split("if '--poses' in sys.argv:")[0],str(BASE/'animate_tidewater.py'),'exec'))
# Correct packed R/G height decoding and use upstream roughness alpha.
# Upstream shader: hh = (R*.99611 + G*.00389) * physical_height_range.
nt=m.node_tree;sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(height.outputs['Color'],sep.inputs['Color'])
r=nt.nodes.new('ShaderNodeMath');r.operation='MULTIPLY';r.inputs[1].default_value=.99611;nt.links.new(sep.outputs['Red'],r.inputs[0])
g=nt.nodes.new('ShaderNodeMath');g.operation='MULTIPLY';g.inputs[1].default_value=.00389;nt.links.new(sep.outputs['Green'],g.inputs[0])
add=nt.nodes.new('ShaderNodeMath');add.operation='ADD';nt.links.new(r.outputs[0],add.inputs[0]);nt.links.new(g.outputs[0],add.inputs[1]);nt.links.new(add.outputs[0],b.inputs['Height'])
b.inputs['Distance'].default_value=meta['textures']['heightRange'][1]-meta['textures']['heightRange'][0];b.inputs['Strength'].default_value=.6
nt.links.new(tex.outputs['Alpha'],bs.inputs['Roughness'])
# Actual imported geometry, not procedural proxy.
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.import_scene.gltf(filepath=str(BASE/'out/orca/orca_decoded.glb'))
imported=list(bpy.context.selected_objects)
meshes=[o for o in imported if o.type=='MESH']
# Bake scene transforms before independent motion. Keep material slots and UVs.
for o in meshes:
 world=o.matrix_world.copy();o.parent=None;o.matrix_world=world
 bpy.context.view_layer.objects.active=o
 o.select_set(True);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.select_set(False)
for o in imported:
 if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
allco=np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in meshes]);lo=allco.min(0);hi=allco.max(0)
print('ORCA BOUNDS',lo.tolist(),hi.tolist(),flush=True)
root=bpy.data.objects.new('Orca one motion root',None);bpy.context.collection.objects.link(root)
orcas=[]
for o in meshes:
 o.parent=root
 for poly in o.data.polygons:poly.use_smooth=True
 # Preserve author texture, adjust only immersion gloss response.
 for material in o.data.materials:
  if material and material.use_nodes:
   principled=material.node_tree.nodes.get('Principled BSDF')
   if principled:principled.inputs['Roughness'].default_value=.45
 orcas.append((o,np.array([v.co[:] for v in o.data.vertices],dtype=np.float32)))
second=bpy.data.objects.new('Orca two motion root',None);bpy.context.collection.objects.link(second)
second_meshes=[]
for o,original in orcas:
 clone=o.copy();clone.data=o.data.copy();bpy.context.collection.objects.link(clone);clone.parent=second;second_meshes.append((clone,original.copy()))
# Darker distant environment and controlled side/back lighting, no noisy full-volume approximation.
for light in bpy.data.objects:
 if light.type=='LIGHT':light.data.energy*=.6
area('surface rim revised',(1,7,12),4800,(.32,.73,.9),9)
area('subject key revised',(3,-10,8),2400,(.65,.87,1),10)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.22
s.world.mist_settings.start=15;s.world.mist_settings.depth=80
cam.data.lens=43
s.render.resolution_x=960;s.render.resolution_y=540;s.render.resolution_percentage=100;s.cycles.samples=12
outdir=BASE/'out/integrated';outdir.mkdir(exist_ok=True)

def update_scene(t):
 pose(t)
 ob.location=(-2+t*.12,0,.10*math.sin(t*.4))
 ob.rotation_euler.z=.025*math.sin(t*.28)
 for i,(rt,parts) in enumerate([(root,orcas),(second,second_meshes)]):
  rt.location=(4+t*.10+i*2.8,5+i*3.6,1.1+i*.8)
  rt.scale=(.85 if i==0 else .75,)*3
  rt.rotation_euler.z=.12*math.sin(t*.2+i)
  for mesh_obj,original in parts:
   co=original.copy();k=np.clip((-co[:,0]-.3)/3.2,0,1)
   co[:,2]+=.16*k*k*np.sin(t*1.65+i*1.7+k*.7)
   mesh_obj.data.vertices.foreach_set('co',co.ravel());mesh_obj.data.update()
 cam.location=(12+t*.07,-28,8)
 target=Vector((.5+t*.12,2,.2));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()

for t in ([2,10,18] if '--poses' in sys.argv else [2]):
 update_scene(t);s.render.filepath=str(outdir/f'scene_{t:02}.png');bpy.ops.render.render(write_still=True)
(outdir/'inspection.json').write_text(json.dumps({'orca_import_bounds':[lo.tolist(),hi.tolist()],'orca_meshes':len(meshes),'orca_vertices':sum(len(o.data.vertices) for o in meshes),'status':'combined pose inspection only; no completed integrated video or sound review'},indent=2))
