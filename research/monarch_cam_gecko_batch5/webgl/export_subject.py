"""Export original authored subject for WebGL; no external reference pixels.
Illustrative asset, not scientifically validated or user-approved.
"""
import bpy
from pathlib import Path
out=Path('studio/runtime/gecko/webgl-production');out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path('studio/runtime/gecko/cinematic-replacement/replacement.blend').resolve()))
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o.name.startswith(('continuous_gecko','iris','raised eye rim','slit pupil')):
  if o.name.startswith(('iris','raised eye rim','slit pupil')):o.scale*=.62
  if o.name.startswith('continuous_gecko'):
   sm=o.modifiers.new('soft silhouette','SMOOTH');sm.factor=.65;sm.iterations=6
   sub=o.modifiers.new('surface refinement','SUBSURF');sub.levels=1;sub.render_levels=1
  o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/'subject.glb'),use_selection=True,export_format='GLB',export_yup=False,export_apply=True)
print('SUBJECT_EXPORTED',flush=True)
