"""Fresh macro exterior look-development scene. Not measured anatomy or final motion.
No imports of the rejected V1 mesh/generator; original procedural meshes/textures.
"""
import bpy,math,random,json,hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path('studio/runtime/gecko/rebuilt-hero-v2');OUT.mkdir(parents=True,exist_ok=True)
random.seed(17);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def material(name,color,rough=.6):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
skin=material('slate blue granular skin',(.12,.23,.25));scale=material('raised blue scales',(.19,.30,.30));rust=material('muted ochre markings',(.43,.16,.055));pad=material('warm lamellar surface',(.54,.39,.22));horn=material('tapered keratin',(.29,.23,.13),.32);stone=material('weathered mineral surface',(.09,.115,.105),.88)
for ma,sz,dist in [(skin,62,.018),(scale,100,.009),(pad,125,.007),(stone,7,.13)]:
 n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF');tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=sz;tex.inputs['Detail'].default_value=4;b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.5;b.inputs['Distance'].default_value=dist;l.new(tex.outputs['Fac'],b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal'])
SPHERES={}
def ell(name,co,sz,ma):
 if ma.name not in SPHERES:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8)
  o=bpy.context.object;o.data.materials.append(ma)
  for f in o.data.polygons:f.use_smooth=True
  SPHERES[ma.name]=o.data
 else:
  o=bpy.data.objects.new(name,SPHERES[ma.name]);bpy.context.collection.objects.link(o)
 o.name=name;o.location=co;o.scale=sz
 return o
def mesh(name,v,f,ma):
 m=bpy.data.meshes.new(name);m.from_pydata(v,[],f);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);m.materials.append(ma)
 for p in m.polygons:p.use_smooth=True
 return o
def curve(name,pts,r,ma,taper=False):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=3;sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
 for i,(p,co) in enumerate(zip(sp.points,pts)):p.co=(*co,1);p.radius=max(.025,1-i/(len(pts)-1)) if taper else 1
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(ma);return o
# Nonuniform external pad, narrowing into a distinct claw-bearing distal sector.
# Dorsal surface and ventral ridges remain separate visual structures, not internal bones.
def digit(name,base,angle,length,width,lift,clawed=True):
 ax=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-ax.y,ax.x,0));base=Vector(base);N=81;K=24;cent=[];x=0;z=0;prev=0
 for i in range(N):
  u=i/(N-1);q=max(0,min(1,(u-.43)/.57));th=lift*q*q*(3-2*q)
  if i:x+=length/(N-1)*math.cos((th+prev)/2);z+=length/(N-1)*math.sin((th+prev)/2)
  c=base+ax*x+Vector((0,0,z));w=width*(.48+.52*math.sin(math.pi*u)**.8)*(1-.76*max(0,(u-.86)/.14));h=.10*(.8+.2*math.sin(math.pi*u));cent.append((c,w,h,th));prev=th
 v=[];faces=[]
 for c,w,h,th in cent:
  norm=Vector((-ax.x*math.sin(th),-ax.y*math.sin(th),math.cos(th)))
  for k in range(K):a=2*math.pi*k/K;v.append(tuple(c+side*w*math.sin(a)+norm*h*math.cos(a)))
 for i in range(N-1):
  for k in range(K):a=i*K+k;b=i*K+(k+1)%K;faces.append((a,b,b+K,a+K))
 faces += [tuple(reversed(range(K))),tuple((N-1)*K+k for k in range(K))];mesh(name,v,faces,skin)
 for i in range(8,72,3):
  c,w,h,th=cent[i];norm=Vector((-ax.x*math.sin(th),-ax.y*math.sin(th),math.cos(th)));pts=[]
  for j in range(25):
   a=math.pi*.54+math.pi*.92*j/24;pts.append(tuple(c+side*w*math.sin(a)+norm*(h+.012)*math.cos(a)))
  curve('ventral_transverse_scale_'+name,pts,.021,pad)
 # Raised dorsal scales are geometry, not merely a noisy albedo mask.
 for i in range(3,76,2):
  c,w,h,th=cent[i];norm=Vector((-ax.x*math.sin(th),-ax.y*math.sin(th),math.cos(th)))
  for j in range(-3,4):
   lateral=j/3.6;a=math.asin(lateral);co=c+side*w*lateral+norm*(h*math.cos(a)+.012);ma=rust if math.sin(i*.39+j*1.2)>.72 else scale
   o=ell('dorsal_granule',co,(.045,.032,.018),ma);o.rotation_euler=norm.to_track_quat('Z','Y').to_euler()
 if clawed:
  c,w,h,th=cent[-1];norm=Vector((-ax.x*math.sin(th),-ax.y*math.sin(th),math.cos(th)));tangent=ax*math.cos(th)+Vector((0,0,math.sin(th)));pts=[tuple(c+tangent*(.26*u)+norm*(.08+.09*math.sin(math.pi*u)-.09*u)) for u in [i/20 for i in range(21)]];curve('integrated_terminal_claw_'+name,pts,.045,horn,True)
 return cent
# Original adjacent-foot silhouette: five distinct digits, I clawless; qualitative layout.
pieces=[ell('palm',(-1.18,.57,.22),(.83,.66,.23),skin),ell('ankle',(-1.9,1.0,.33),(.48,.67,.31),skin),ell('limb_entering_frame',(-2.15,1.93,.49),(.41,1.13,.38),skin)]
for label,b,a,L,w,li,cl in [('IV',(-.75,-.07,.155),-.13,2.85,.32,1.60,True),('III',(-.72,.65,.16),.40,2.45,.28,.06,True),('II',(-1.03,.98,.16),1.00,1.82,.24,.10,True),('I',(-1.5,1.05,.16),1.73,1.05,.19,.05,False),('V',(-1.4,.1,.16),-1.13,1.70,.25,.18,True)]:digit(label,b,a,L,w,li,cl)
# Small granules on palm and ankle; no disconnected pebble collage used as anatomy.
for _ in range(480):
 x=random.uniform(-1.8,-.50);y=random.uniform(-.01,1.12);q=((x+1.18)/.83)**2+((y-.57)/.66)**2
 if q<.94:
  z=.22+.23*math.sqrt(1-q);ma=rust if math.sin(x*19)*math.cos(y*17)>.63 else scale;ell('palm_scale',(x,y,z),(.045,.035,.020),ma)
# Rough stone masonry relief provides real foreground/background depth and scale cues.
for x in range(-3,4):
 for y in range(-3,4):
  bpy.ops.mesh.primitive_cube_add(size=1,location=(x*2.35+(y%2)*1.17,y*2.12,-.30-random.random()*.025));o=bpy.context.object;o.name='mineral_block';o.scale=(2.32,2.09,.55);o.data.materials.append(stone);be=o.modifiers.new('worn_edges','BEVEL');be.width=.055;be.segments=3;o.modifiers.new('weighted_normals','WEIGHTED_NORMAL')
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=2;s.render.resolution_x=720;s.render.resolution_y=1280;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.world.color=(.025,.035,.045);s.view_settings.view_transform='AgX'
bpy.ops.object.camera_add(location=(4.9,-6.8,5.8));cam=bpy.context.object;target=Vector((-.40,.58,.35));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=43;cam.data.dof.use_dof=True;cam.data.dof.focus_distance=(cam.location-Vector((.50,-.1,.5))).length;cam.data.dof.aperture_fstop=9;s.camera=cam
for pos,energy,size,color in [((1,-3,4),650,2.1,(1,.79,.48)),((-3,3,5),950,3.0,(.43,.70,1)),((2,4,3),180,2,(.70,.83,1))]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=energy;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,.3,.2))-o.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(OUT/'rebuilt-gecko-hero-v2.png');bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'rebuilt-hero-v2.blend'))
f=OUT/'rebuilt-gecko-hero-v2.png';(OUT/'receipt.json').write_text(json.dumps({'image':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'resolution':[720,1280],'type':'actual3D render; look-development still only','measured_anatomy':False,'motion_validated':False,'user_approved':False,'third_party_image_textures':False},indent=2)+'\n')
