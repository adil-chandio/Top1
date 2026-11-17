"""Replacement asset foundation: continuous remeshed whole-animal silhouette.
Original authored illustrative geometry, not measured anatomy. No rejected mesh imports.
"""
import bpy, math, random
from pathlib import Path
from mathutils import Vector
random.seed(91)
OUT=Path('studio/runtime/gecko/cinematic-replacement');OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(name,color,rough=.5):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
skin=mat('Tokay-inspired blue grey with irregular ochre patches',(.12,.25,.26));n=skin.node_tree.nodes;l=skin.node_tree.links;p=n.get('Principled BSDF');p.inputs['Subsurface Weight'].default_value=.055
tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=4.8;tex.inputs['Detail'].default_value=3
r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.39;r.color_ramp.elements[0].color=(.045,.13,.16,1);r.color_ramp.elements[1].position=.66;r.color_ramp.elements[1].color=(.29,.42,.40,1);e=r.color_ramp.elements.new(.59);e.color=(.48,.17,.065,1);l.new(tex.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color'])
v=n.new('ShaderNodeTexVoronoi');v.inputs['Scale'].default_value=155;v.feature='DISTANCE_TO_EDGE';b=n.new('ShaderNodeBump');b.inputs['Distance'].default_value=.012;b.inputs['Strength'].default_value=.38;l.new(v.outputs['Distance'],b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal'])
eye=mat('golden iris',(.64,.43,.12),.24);black=mat('vertical pupil',(.003,.006,.006),.12);stone=mat('aged plaster',(.15,.18,.17),.93)
parts=[]
def ell(name,co,scale,ma=skin,collect=True):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=co);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma)
 for f in o.data.polygons:f.use_smooth=True
 if collect:parts.append(o)
 return o
def tube(name,pts,widths):
 verts=[];faces=[];K=16
 for i,pt in enumerate(pts):
  tangent=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)]);tangent.normalize();side=tangent.cross(Vector((0,0,1))).normalized();up=side.cross(tangent).normalized()
  for j in range(K):
   a=j*2*math.pi/K;verts.append(tuple(Vector(pt)+widths[i]*(side*math.cos(a)+up*math.sin(a))))
 for i in range(len(pts)-1):
  for j in range(K):a=i*K+j;bb=i*K+(j+1)%K;faces.append((a,bb,bb+K,a+K))
 faces.extend([tuple(reversed(range(K))),tuple((len(pts)-1)*K+j for j in range(K))]);me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(skin);parts.append(o)
ell('torso',(0,0,.43),(.59,1.45,.36));ell('neck',(0,1.28,.39),(.40,.55,.30));ell('broad head',(0,1.96,.40),(.65,.66,.30));ell('muzzle',(0,2.37,.33),(.48,.38,.20))
pts=[(.3*math.sin(i/25*2.7),-1.1-i*.105,.37-i*.005) for i in range(40)];tube('continuous tapered tail',pts,[max(.012,.32*(1-i/40)**1.35) for i in range(40)])
for side in [-1,1]:
 for hind in [False,True]:
  y=-.86 if hind else .90; palm=Vector((side*1.49,y+.37,.13));tube('bent limb',[(side*.38,y,.42),(side*.91,y-.28,.28),tuple(palm)],[.24,.19,.14]);ell('palm',palm,(.23,.28,.11))
  for j in range(5):
   a=(-.95+j*.46);direction=Vector((side*math.cos(a),math.sin(a),0));length=[.36,.55,.68,.65,.47][j];start=palm+Vector((0,(j-2)*.075,0));pts=[tuple(start+direction*(length*i/12)+Vector((0,0,.025*math.sin(i/12*math.pi)))) for i in range(13)];tube('tapered digit',pts,[.068*(1-.65*i/12) for i in range(13)]);mid=start+direction*(length*.62);o=ell('expanded adhesive digit sector',mid,(length*.28,.10,.045));o.rotation_euler.z=math.atan2(direction.y,direction.x)
# Union intersections rather than stacked disconnected ellipses.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();body=bpy.context.object;body.name='continuous_gecko_illustrative_surface';mod=body.modifiers.new('continuous tissue union','REMESH');mod.mode='VOXEL';mod.voxel_size=.026;bpy.ops.object.modifier_apply(modifier=mod.name);sm=body.modifiers.new('soft tissue smoothing','SMOOTH');sm.factor=.8;sm.iterations=4;bpy.ops.object.modifier_apply(modifier=sm.name)
for f in body.data.polygons:f.use_smooth=True
for side in [-1,1]:
 ell('raised eye rim',(side*.48,2.09,.59),(.22,.26,.16),skin,False);ell('iris',(side*.49,2.13,.70),(.147,.18,.085),eye,False);ell('slit pupil',(side*.49,2.13,.775),(.019,.137,.012),black,False)
bpy.ops.mesh.primitive_plane_add(size=200);wall=bpy.context.object;wall.name='vertical-wall local coordinate plane';wall.data.materials.append(stone)
n=stone.node_tree.nodes;l=stone.node_tree.links;p=n.get('Principled BSDF');t=n.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=12;t.inputs['Detail'].default_value=5;b=n.new('ShaderNodeBump');b.inputs['Distance'].default_value=.045;l.new(t.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal'])
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=2;s.render.resolution_x=720;s.render.resolution_y=1280;s.render.resolution_percentage=100;s.world.color=(.008,.012,.022);s.view_settings.view_transform='AgX'
bpy.ops.object.camera_add(location=(4.5,5.8,9));cam=bpy.context.object;target=Vector((0,-.35,.25));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=48;s.camera=cam
for loc,energy,color,size in [((-4,4,4),850,(.42,.69,1),3),((3,-2,2.5),600,(1,.61,.25),2),((0,5,2),260,(.7,1,1),1.5)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.color=color;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'replacement.blend'));s.render.filepath=str(OUT/'replacement-establishing.png');bpy.ops.render.render(write_still=True)
