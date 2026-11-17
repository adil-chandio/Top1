"""Isolated asset inspection, no claim of completed motion or final fidelity.
Requires ignored downloaded tidewater files; upstream MIT notice retained there.
"""
import runpy,sys,json
from pathlib import Path
import bpy,numpy as np
BASE=Path(__file__).parent
# Load experimental scene definitions without executing its render branch.
code=(BASE/'render_proof.py').read_text().split("if '--test' in sys.argv:")[0]
exec(compile(code,str(BASE/'render_proof.py'),'exec'))
# Hide old humpback and both low-detail orcas for asset-only review.
for a in actors:
 for ob in list(bpy.data.objects):
  if ob==a['root'] or ob.parent==a['root']:ob.hide_render=True
p=BASE/'out/tidewater';meta=json.loads((p/'humpback.json').read_text());lv=meta['levels'][0];raw=(p/'humpback.bin').read_bytes()
pos=np.frombuffer(raw,dtype='<f4',count=lv['vertices']*3,offset=lv['position']).reshape(-1,3)
uv=np.frombuffer(raw,dtype='<f4',count=lv['vertices']*2,offset=lv['uv']).reshape(-1,2)
idx=np.frombuffer(raw,dtype='<u4',count=lv['indices'],offset=lv['index']).reshape(-1,3)
# Upstream Three Y-up, snout +Z -> Blender Z-up, snout +X (proper rotation).
verts=np.stack((pos[:,2],pos[:,0],pos[:,1]),axis=1)
ob=mesh('Tidewater MIT humpback inspection',verts.tolist(),idx.tolist(),skin)
layer=ob.data.uv_layers.new(name='UVMap')
for poly in ob.data.polygons:
 for li in poly.loop_indices:layer.data[li].uv=(float(uv[ob.data.loops[li].vertex_index][0]),1-float(uv[ob.data.loops[li].vertex_index][1]))
m=bpy.data.materials.new('Tidewater albedo + height');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=.47
tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(p/'humpback_albedo.png'));l.new(tex.outputs['Color'],bs.inputs['Base Color'])
height=n.new('ShaderNodeTexImage');height.image=bpy.data.images.load(str(p/'humpback_height.png'));height.image.colorspace_settings.name='Non-Color'
b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.45;b.inputs['Distance'].default_value=.065;l.new(height.outputs['Color'],b.inputs['Height']);l.new(b.outputs['Normal'],bs.inputs['Normal']);ob.data.materials.clear();ob.data.materials.append(m)
cam.location=(9,-23,6);target=Vector((0,0,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
s.cycles.samples=16;s.render.filepath=str(BASE/'out/tidewater_inspection.png');bpy.ops.render.render(write_still=True)
(BASE/'out/tidewater_inspection.json').write_text(json.dumps({'vertices':len(verts),'triangles':len(idx),'bounds':{'min':verts.min(axis=0).tolist(),'max':verts.max(axis=0).tolist()},'motion_tested':False},indent=2))
