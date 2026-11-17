"""Corrected original 3D assets for explicitly requested complete private review cut.
Removes bead meshes and finite set edge from failed hero candidate. Not anatomy approval.
"""
from pathlib import Path
import math,json
import bpy
from mathutils import Vector
src=Path('research/monarch_cam_gecko_batch5/build_rebuilt_hero.py').read_text().split("s.render.filepath=str(OUT/")[0]
src=src.replace("range(3,76,2)","range(0)").replace('range(480)','range(0)').replace('range(-3,4)','range(-9,10)')
src=src.replace(".32,1.60,True", ".32,0.0,True")
exec(compile(src,'fresh_corrected_full_cut_scene','exec'))
OUT=Path('studio/runtime/gecko/full-review-v1/assets');OUT.mkdir(parents=True,exist_ok=True)
# Fine procedural cell relief instead of bead geometry; origin remains wholly authored.
n=skin.node_tree.nodes;l=skin.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(.10,.20,.21,1)
vor=n.new('ShaderNodeTexVoronoi');vor.feature='DISTANCE_TO_EDGE';vor.inputs['Scale'].default_value=82;b=n.new('ShaderNodeBump');b.inputs['Distance'].default_value=.012;b.inputs['Strength'].default_value=.42;l.new(vor.outputs['Distance'],b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal'])
# Rebuild only the illustrated foreground digit; continuously changing geometry.
hero=bpy.data.objects['IV'];ridges=sorted([o for o in bpy.data.objects if o.name.startswith('ventral_transverse_scale_IV')],key=lambda o:o.name);claw=bpy.data.objects['integrated_terminal_claw_IV']
base=Vector((-.75,-.07,.155));angle=-.13;ax=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-ax.y,ax.x,0));N=81;K=24;L=2.85

def pose(progress):
 front=1-.64*progress;x=z=prev=0;cent=[]
 for i in range(N):
  u=i/(N-1);q=max(0,min(1,(u-front)/max(.001,1-front)));th=1.7*progress*q*q*(3-2*q)
  if i:x+=L/(N-1)*math.cos((th+prev)/2);z+=L/(N-1)*math.sin((th+prev)/2)
  c=base+ax*x+Vector((0,0,z));w=.32*(.48+.52*math.sin(math.pi*u)**.8)*(1-.76*max(0,(u-.86)/.14));h=.10*(.8+.2*math.sin(math.pi*u));cent.append((c,w,h,th));prev=th
 verts=[]
 for c,w,h,th in cent:
  norm=Vector((-ax.x*math.sin(th),-ax.y*math.sin(th),math.cos(th)))
  for j in range(K):a=2*math.pi*j/K;verts.append(c+side*w*math.sin(a)+norm*h*math.cos(a))
 for v,co in zip(hero.data.vertices,verts):v.co=co
 hero.data.update()
 for o,i in zip(ridges,range(8,72,3)):
  c,w,h,th=cent[i];norm=Vector((-ax.x*math.sin(th),-ax.y*math.sin(th),math.cos(th)))
  for j,p in enumerate(o.data.splines[0].points):a=math.pi*.54+math.pi*.92*j/24;p.co=(*(c+side*w*math.sin(a)+norm*(h+.012)*math.cos(a)),1)
 c,w,h,th=cent[-1];norm=Vector((-ax.x*math.sin(th),-ax.y*math.sin(th),math.cos(th)));tangent=ax*math.cos(th)+Vector((0,0,math.sin(th)))
 for j,p in enumerate(claw.data.splines[0].points):u=j/20;p.co=(*(c+tangent*(.26*u)+norm*(.08+.09*math.sin(math.pi*u)-.09*u)),1)
 assert min(v.z for v in verts)>0
 return float(cent[-1][0].z)

def aim(location,target,lens=43):
 cam.location=location;target=Vector(target);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.dof.focus_distance=(cam.location-target).length
s.render.resolution_x=432;s.render.resolution_y=768;s.cycles.samples=6;cam.data.dof.aperture_fstop=12
for name,loc,target,pr in [('exterior',(4.2,-5.8,5.2),(-.4,.55,.2),0),('loaded',(3.6,-4.7,3.5),(.55,-.1,.2),0),('released',(3.6,-4.7,3.5),(.55,-.1,.4),1)]:
 pose(pr);aim(loc,target);s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);print('ASSET',name,flush=True)
aim((3.6,-4.7,3.5),(.55,-.1,.35));qc=[]
# Continuous 10.82s release:132 actual authored poses at12Hz, held to24fps in assembly.
for f in range(132):
 u=f/131;t=max(0,min(1,(u-.10)/.78));pr=t*t*(3-2*t);tip=pose(pr);s.render.filepath=str(OUT/f'release-{f:04}.png');bpy.ops.render.render(write_still=True);qc.append({'frame':f,'progress':pr,'tip_z':tip});print('RELEASE',f,flush=True)
(OUT/'motion-qc.json').write_text(json.dumps(qc,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'complete-review-scene.blend'))
