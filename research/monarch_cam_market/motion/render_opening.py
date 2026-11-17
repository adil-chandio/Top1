"""Render 20s continuous opening imagery. No reference-image projection, no reused video.
Small batch + process exit avoids observed bpy interpreter shutdown crash after completed writes.
"""
from pathlib import Path
import sys,os,math,json
import bpy,numpy as np
BASE=Path(__file__).parent
code=(BASE/'integrated_scene.py').read_text().split('for t in ([2,10,18]')[0]
exec(compile(code,str(BASE/'integrated_scene.py'),'exec'))
FPS=24;TOTAL=480
s.render.resolution_x=768;s.render.resolution_y=432;s.render.resolution_percentage=100
s.cycles.samples=3;s.render.threads=2;s.render.fps=FPS;s.render.use_persistent_data=True
s.world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.12,.19,1)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.18
# Refine existing low-poly asset without claiming biologically accurate remodelling.
for mo,_ in orcas+second_meshes:
 sub=mo.modifiers.new('surface refinement','SUBSURF');sub.levels=1;sub.render_levels=1
# Stable art-direction grade; depth fade remains linked to real mist pass.
for node in s.node_tree.nodes:
 if node.type=='MIX_RGB':node.inputs[2].default_value=(.006,.047,.080,1)
s.world.mist_settings.start=12;s.world.mist_settings.depth=65
# Accent surface shaft columns are lights, not physical measured caustics.
for light in bpy.data.objects:
 if light.type=='LIGHT':light.data.energy*=.75
area('cool broad surface',(0,1,16),5200,(.35,.65,1),9)
area('left edge separation',(-5,5,5),2800,(.18,.65,.75),7)
# Original small fish geometries for diet insert; explanatory illustration only.
fish=[]
for i in range(14):
 rt=bpy.data.objects.new('small fish root',None);bpy.context.collection.objects.link(rt)
 body=ellipsoid('small fish silhouette',(0,0,0),(.23,.055,.085),saddle,rt)
 tail=mesh('small fish tail',[(-.20,0,0),(-.35,0,.12),(-.35,0,-.12)],[(0,1,2)],saddle,rt)
 rt.location=(i*.43-3,(i%3)*.6-5,-1+(i%4)*.25);fish.append(rt)
frames=BASE/'out/opening_frames';frames.mkdir(exist_ok=True)

def opening_pose(frame):
 t=frame/FPS;update_scene(t)
 # Orcas head left, humpback approaches right. No physical contact or invented successful rescue.
 for i,rt in enumerate([root,second]):
  rt.location=(7-t*.12+i*3,6+i*3,1+i*.7)
  rt.rotation_euler.z=math.pi+.05*math.sin(t*.3+i)
  for child in rt.children:child.hide_render=8.7<=t<11.5
 ob.location=(-5+t*.3,0,.12*math.sin(t*.4))
 for i,rt in enumerate(fish):
  rt.location.x=(i*.43-3)+(t-9)*.35;rt.rotation_euler.z=.1*math.sin(t*2+i)
  rt.hide_render=not 8.7<=t<11.5
  for child in rt.children:child.hide_render=rt.hide_render
 # Show same narrative encounter through distinct genuinely rendered camera positions.
 if t<3.8:
  cam.location=(1+t*.16,-10,3.5);target=Vector((8-t*.12,5,1));cam.data.lens=48
 elif t<8.7:
  u=t-3.8;cam.location=(6+u*.18,-22,4.5);target=Vector((-2+u*.12,.7,.1));cam.data.lens=43
 elif t<11.5:
  # Detail of humpback with explanatory small-fish layer, not a fabricated feeding event.
  cam.location=(9,-15,2.5);target=Vector((.1,-1,-.2));cam.data.lens=40
 elif t<15.5:
  u=t-11.5;cam.location=(-3+u*.25,-24,8.5);target=Vector((1,2,.4));cam.data.lens=40
 else:
  u=t-15.5;cam.location=(-6+u*.22,-17,1.8);target=Vector((-1.2+u*.12,.5,-.15));cam.data.lens=38
 cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()

if '--test' in sys.argv:
 for f in [36,144,240,324,432]:
  opening_pose(f);s.render.filepath=str(frames/f'test_{f:04}.png');bpy.ops.render.render(write_still=True)
else:
 start=int(os.getenv('FRAME_START','0'));end=int(os.getenv('FRAME_END',str(TOTAL)))
 for f in range(start,end):
  dest=frames/f'{f:04}.png'
  if dest.exists():continue
  opening_pose(f);s.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
  if f%24==0:print('FRAME',f,'OF',TOTAL,flush=True)
 print('BATCH COMPLETE',start,end,flush=True)
# Artifacts flushed before bypassing bpy interpreter finalization; no running render abandoned.
sys.stdout.flush();sys.stderr.flush();os._exit(0)
