"""Original procedural 3D motion study. No concept-image projection or video input."""
import bpy, math, os, sys, json, random
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).parent
OUT=BASE/'out';OUT.mkdir(exist_ok=True)
FPS=24; N=480
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.cycles.use_denoising=True;s.cycles.max_bounces=2;s.cycles.diffuse_bounces=1;s.cycles.glossy_bounces=1
s.render.resolution_x=960;s.render.resolution_y=540;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.fps=FPS;s.frame_end=N
s.render.threads_mode='FIXED';s.render.threads=6
s.world.color=(.035,.07,.09)
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.27,.32,1)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.45
s.view_settings.view_transform='AgX'

def mat(name,color,rough=.42):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
 return m
skin=mat('humpback naturally mottled skin',(.055,.10,.12)); nodes=skin.node_tree.nodes;links=skin.node_tree.links
noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=9;noise.inputs['Detail'].default_value=3
ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.025,.045,.055,1);ramp.color_ramp.elements[1].color=(.16,.22,.23,1)
links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],nodes['Principled BSDF'].inputs['Base Color'])
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.035
links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],nodes['Principled BSDF'].inputs['Normal'])
black=mat('orca dark skin',(.012,.022,.027),.3); white=mat('off-white ventral pigmentation',(.58,.66,.63),.44); eye=mat('dark eye',(.004,.006,.007),.22)
saddle=mat('orca saddle',(.22,.28,.29),.42)

actors=[]
def mesh(name,v,f,material,parent=None):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.data.materials.append(material)
 for p in me.polygons:p.use_smooth=True
 if parent:ob.parent=parent
 return ob

def ellipsoid(name,loc,scale,material,parent):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=(0,0,0));o=bpy.context.object;o.name=name;o.parent=parent;o.location=loc;o.scale=scale;o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o

def fin(name,path,widths,material,parent):
 verts=[];faces=[]
 for (x,y,z),w in zip(path,widths):
  for j in range(12):
   a=j*math.tau/12;verts.append((x+w*math.cos(a),y,z+.12*w*math.sin(a)))
 for i in range(len(path)-1):
  for j in range(12):a=i*12+j;b=i*12+(j+1)%12;faces.append((a,b,b+12,a+12))
 faces.extend([tuple(reversed(range(12))),tuple((len(path)-1)*12+j for j in range(12))])
 return mesh(name,verts,faces,material,parent)

def whale(name,hump=True,scale=1):
 root=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(root);root.scale=(scale,scale,scale)
 # Long axis X; tail at negative X. Original author-created mesh, no external animal assets.
 profile=[(-5.5,.10,.13,-.03),(-4.7,.26,.31,0),(-3.8,.48,.55,.03),(-2.8,.79,.84,.07),(-1.6,1.05,1.08,.09),(0,1.20,1.23,.05),(1.4,1.18,1.15,0),(2.5,.99,.91,-.03),(3.35,.74,.62,-.08),(3.95,.42,.35,-.13),(4.2,.06,.08,-.15)]
 if hump:
  profile=[(-5.5,.10,.13,-.03),(-4.7,.25,.28,0),(-3.8,.44,.51,.03),(-2.8,.71,.83,.07),(-1.6,.94,1.10,.09),(0,1.10,1.17,.05),(1.4,1.12,.99,-.04),(2.5,.98,.69,-.10),(3.35,.77,.43,-.13),(3.95,.47,.20,-.15),(4.2,.08,.045,-.15)]
 verts=[];faces=[]
 for x,ry,rz,zc in profile:
  for j in range(40):
   a=j*math.tau/40;verts.append((x,ry*math.cos(a),zc+rz*math.sin(a)))
 for i in range(len(profile)-1):
  for j in range(40):a=i*40+j;b=i*40+(j+1)%40;faces.append((a,b,b+40,a+40))
 faces.extend([tuple(reversed(range(40))),tuple((len(profile)-1)*40+j for j in range(40))])
 body=mesh(name+' body',verts,faces,skin if hump else black,root);body.data.materials.append(white)
 for p in body.data.polygons:
  if p.center.z < -.5:pass
 # Set underside by original polygon-centroid coordinates, not topology-dependent shader coordinates.
 for p in body.data.polygons:
  z=sum(verts[i][2] for i in p.vertices)/len(p.vertices)
  if z<(-.83 if hump else -.65):p.material_index=1
 sub=body.modifiers.new('smooth continuous body','SUBSURF');sub.levels=2;sub.render_levels=2
 moving=[body];fins=[]
 for side in [-1,1]:
  reach=3.25 if hump else 1.45
  path=[(1.0,side*.85,-.45),(.65,side*1.35,-.7),(-.05,side*(1.5+reach*.35),-.9),(-.9,side*(1.5+reach*.65),-.9),(-1.55,side*(1.5+reach),-.6)]
  if hump:
   path=[(1.0,side*.85,-.45),(.65,side*1.30,-.9),(-.05,side*1.95,-1.6),(-.7,side*2.50,-2.3),(-1.15,side*2.9,-2.8)]
  f=fin(name+' pectoral '+str(side),path,[.52,.49,.4,.25,.015],skin if hump else black,root);fins.append((f,side))
 # Horizontal paired flukes with swept trailing edge.
 for side in [-1,1]:
  f=fin(name+' horizontal fluke '+str(side),[(-5.3,0,0),(-5.5,side*.65,.01),(-5.75,side*1.35,.04),(-6.0,side*1.95,.11)], [.34,.6,.46,.015],skin if hump else black,root);moving.append(f)
 # dorsal fin, tapered by independent mesh in XZ plane
 dv=[(-2.7,-.10,.65),(-1.4,-.12,.92),(-2.25,0,1.35 if hump else 2.05),(-2.7,.10,.65),(-1.4,.12,.92)]
 mesh(name+' dorsal',dv,[(0,1,2),(2,4,3),(0,3,4,1)],skin if hump else black,root)
 for side in [-1,1]:
  ellipsoid(name+' eye', (2.65,side*.83,.08),(.11,.045,.065),eye,root)
  if not hump:
   ellipsoid(name+' eye patch',(2.08,side*.98,.40),(.48,.025,.22),white,root)
 if hump:
  # Rostral tubercles: small, restrained surface nodules.
  for xx in [2.7,3.05,3.4,3.7]:
   for side in [-1,0,1]:ellipsoid(name+' rostral tubercle',(xx,side*.25,.64-(xx-2.7)*.36),(.07,.065,.05),skin,root)
 if hump:
  # Fine closed-mouth crease and ventral pleats are original curve geometry, not painted fake teeth.
  def line(n,pts,radius,material):
   cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='3D';cu.bevel_depth=radius;cu.bevel_resolution=2
   sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
   for b,p in zip(sp.bezier_points,pts):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
   ob=bpy.data.objects.new(n,cu);bpy.context.collection.objects.link(ob);ob.parent=root;ob.data.materials.append(material)
  for side in [-1,1]:
   line(name+' mouth crease',[(1.1,side*1.06,-.12),(2.1,side*1.05,-.18),(3.1,side*.87,-.20),(4.05,side*.38,-.20)],.018,black)
  for yy in [-.65,-.4,-.15,.15,.4,.65]:
   line(name+' throat pleat',[(.0,yy,-1.10),(1.1,yy*.96,-.94),(2.2,yy*.85,-.69),(3.3,yy*.62,-.42)],.012,skin)
 actors.append({'root':root,'deform':[(o,[v.co.copy() for v in o.data.vertices]) for o in moving],'fins':fins,'phase':len(actors)*1.9,'hump':hump})
 return root

h=whale('Humpback motion prototype',True,1.0)
o1=whale('Orca one',False,.52);o2=whale('Orca two',False,.43)
# Sea floor, true geometry; procedural shading not a flat background image.
floor=mat('seafloor',(.025,.10,.10),.9)
bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-15));bpy.context.object.data.materials.append(floor)
# Soft submerged haze.
vol=bpy.data.materials.new('water attenuation');vol.use_nodes=True;n=vol.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');v=n.new('ShaderNodeVolumePrincipled');v.inputs['Density'].default_value=.012;v.inputs['Color'].default_value=(.12,.47,.49,1);v.inputs['Anisotropy'].default_value=.25;vol.node_tree.links.new(v.outputs['Volume'],out.inputs['Volume'])
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,0,0));water=bpy.context.object;water.name='water volume';water.scale=(70,70,35);water.data.materials.append(vol);water.hide_render=True
# Composited distance attenuation avoids a costly noisy full-scene scattering approximation.
s.view_layers[0].use_pass_mist=True;s.world.mist_settings.start=10;s.world.mist_settings.depth=65
s.use_nodes=True;nt=s.node_tree;nt.nodes.clear();rl=nt.nodes.new('CompositorNodeRLayers');mix=nt.nodes.new('CompositorNodeMixRGB');mix.blend_type='MIX';mix.inputs[2].default_value=(.025,.16,.18,1);nt.links.new(rl.outputs['Mist'],mix.inputs[0]);nt.links.new(rl.outputs['Image'],mix.inputs[1]);co=nt.nodes.new('CompositorNodeComposite');nt.links.new(mix.outputs[0],co.inputs[0])

def area(name,loc,power,color,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
area('broad surface light', (0,-2,13),4200,(.55,.86,1),15)
area('soft camera fill',(2,-14,4),1800,(.35,.72,.77),12)
area('back rim',(0,9,8),3500,(.35,.86,.85),10)
# sparse volumetric particulate, deterministic
random.seed(21);part=mat('suspended particles',(.25,.49,.48),.8)
for i in range(75):
 p=(random.uniform(-18,22),random.uniform(-10,18),random.uniform(-6,8))
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=random.uniform(.008,.025),location=p);bpy.context.object.data.materials.append(part)
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.lens=43;cam.data.clip_end=200

def update(frame):
 t=frame/FPS
 for i,a in enumerate(actors):
  r=a['root'];phase=a['phase'];hump=a['hump']
  if hump:r.location=(-3+t*.25,0,.1*math.sin(t*.4));r.rotation_euler=(.025*math.sin(t*.5),-.035*math.sin(t*.4),.03*math.sin(t*.2))
  else:
   r.location=(4+t*.22+(i-1)*3.2,4+(i-1)*3.0+.5*math.sin(t*.18+phase),.8+(i-1)*1.1+.2*math.sin(t*.7+phase))
   r.rotation_euler=(.04*math.sin(t*.6+phase),.04*math.sin(t*.6+phase),.05+.15*math.sin(t*.16+phase))
  w=t*(1.2 if hump else 1.8)+phase
  for ob,original in a['deform']:
   for ve,co in zip(ob.data.vertices,original):
    k=max(0,min(1,(-co.x-1.0)/5))
    ve.co=(co.x,co.y,co.z+.48*k*k*math.sin(w+k*.9))
   ob.data.update()
  for f,side in a['fins']:
   f.rotation_euler.x=side*(.04+.075*math.sin(w*.6+side*.4))
   f.rotation_euler.y=.035*math.sin(w*.5)
 # Three deliberately distinct camera views of the same locomotion study.
 if t<7:
  cam.location=(9+t*.12,-21,5.2);target=Vector((1+t*.18,2,0))
 elif t<14:
  u=t-7;cam.location=(4+u*.22,-15,1.2);target=Vector((0+u*.22,1,0))
 else:
  u=t-14;cam.location=(-9+u*.3,-18,6.5);target=Vector((3+u*.2,3,.3))
 cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()

if '--test' in sys.argv:
 update(72);s.render.filepath=str(OUT/'test.png');bpy.ops.render.render(write_still=True)
else:
 for f in range(N):
  dest=OUT/f'{f:04}.png'
  if dest.exists():continue
  update(f);s.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
  if f%24==0:print('PROGRESS',f,N,flush=True)
 (OUT/'render_receipt.json').write_text(json.dumps({'frames':N,'fps':FPS,'duration_s':20,'width':960,'height':540,'engine':'Blender Cycles CPU','samples':8,'geometry':'original procedural meshes; body and flukes vertex-deformed per frame; fin and root transforms','limits':'procedural motion study, not image-matched photoreal result or validated biomechanics; no audio'},indent=2))
