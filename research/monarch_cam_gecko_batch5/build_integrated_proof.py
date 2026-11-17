"""Original 5s integrated visual feasibility proof, explicitly user-authorized.
Qualitative exterior only: no measured anatomy, biological rig or gait claim.
Run with local bpy environment; output stays in ignored studio/runtime.
"""
import argparse, math, json, hashlib, subprocess
from pathlib import Path
import bpy
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
P=argparse.ArgumentParser();P.add_argument('--preview',action='store_true');args=P.parse_args()
OUT=Path('studio/runtime/gecko/integrated-proof-v1');OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(name,color,rough=.5):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
skin=mat('authored warm muted skin',(.34,.23,.13),.62)
n=skin.node_tree.nodes;l=skin.node_tree.links;p=n.get('Principled BSDF');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=65;noise.inputs['Detail'].default_value=2;bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.028;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
# Authored procedural dorsal coloration and cell-scale surface relief, no image textures.
spots=n.new('ShaderNodeTexNoise');spots.inputs['Scale'].default_value=5.8;spots.inputs['Detail'].default_value=2
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.58;ramp.color_ramp.elements[0].color=(.16,.235,.23,1);ramp.color_ramp.elements[1].position=.69;ramp.color_ramp.elements[1].color=(.48,.18,.065,1)
l.new(spots.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
noise.inputs['Scale'].default_value=95;bump.inputs['Strength'].default_value=.4;bump.inputs['Distance'].default_value=.045
lam=mat('ventral illustrative lamellae',(.47,.34,.19),.65);clawmat=mat('keratin illustrative',(.37,.30,.19),.35);wall=mat('matte slate substrate',(.055,.095,.11),.8)
n=wall.node_tree.nodes;l=wall.node_tree.links;p=n.get('Principled BSDF');no=n.new('ShaderNodeTexNoise');no.inputs['Scale'].default_value=95;bu=n.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.18;bu.inputs['Distance'].default_value=.025;l.new(no.outputs['Fac'],bu.inputs['Height']);l.new(bu.outputs['Normal'],p.inputs['Normal'])
def mesh(name,verts,faces,ma):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);m.materials.append(ma)
 for p in m.polygons:p.use_smooth=True
 return o
def ell(name,pos,scale,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=pos);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(ma)
 for p in o.data.polygons:p.use_smooth=True
 return o
def tube(name,pts,r,ma):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=3;sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(ma);return o,sp
R=73;K=24;L=3.45
faces=[]
for i in range(R-1):
 for j in range(K):a=i*K+j;b=i*K+(j+1)%K;faces.append((a,b,b+K,a+K))
faces += [tuple(reversed(range(K))),tuple((R-1)*K+j for j in range(K))]
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def dimensions(u):
 # Broad mid/distal pad with a distinctly narrowing terminal region. Unmeasured.
 width=.19+.14*math.sin(math.pi*u)**.8
 if u>.85:width*=1-.77*smooth((u-.85)/.15)
 return width,.115 if u<.87 else .115*(1-.38*smooth((u-.87)/.13))
def centers(progress):
 front=1-.69*progress;out=[];x=-.6;z=.145;last=0
 for i in range(R):
  u=i/(R-1);theta=1.95*progress*smooth((u-front)/max(.01,1-front))
  if i:x+=L/(R-1)*math.cos((theta+last)/2);z+=L/(R-1)*math.sin((theta+last)/2)
  out.append((x,-.65-.08*u,z,theta));last=theta
 return out
def surface(cs):
 v=[]
 for i,(x,y,z,t) in enumerate(cs):
  w,h=dimensions(i/(R-1))
  for j in range(K):
   a=2*math.pi*j/K;off=h*math.cos(a);v.append((x-math.sin(t)*off,y+w*math.sin(a),z+math.cos(t)*off))
 return v
hero=mesh('digit_IV_qualitative_external_surface',surface(centers(0)),faces,skin)
ridges=[]
for i in range(9,64,3):
 ob,sp=tube('authored_ventral_ridge_not_measured_count',[(0,0,0)]*17,.018,lam);ridges.append((i,sp))
claw,clawsp=tube('digit_IV_terminal_claw_illustrative',[(0,0,0)]*13,.042,clawmat)
# Original palm, ankle and cropped adjacent limb; context is never dropped.
parts=[ell('plantar_context',(-1.05,.15,.23),(.92,.79,.25),skin),ell('ankle_context',(-1.9,.47,.32),(.76,.43,.30),skin),ell('adjacent_limb',(-2.65,.92,.52),(.48,1.05,.42),skin),ell('digit_IV_root',(-.75,-.56,.17),(.47,.32,.17),skin)]
# Qualitative five-digit left-pes layout. I clawless, II-V claw-bearing; proportions not measured.
for label,start,end,width in [('I',(-.65,.70),(.10,1.68),.20),('II',(-.90,.73),(-.37,2.30),.24),('III',(-.42,.38),(1.47,1.65),.27),('V',(-1.45,-.15),(-1.13,-1.80),.25)]:
 a=Vector((*start,.15));b=Vector((*end,.15));axis=(b-a).normalized();side=Vector((-axis.y,axis.x,0));v=[]
 for i in range(R):
  u=i/(R-1);c=a.lerp(b,u);w=width*(.65+.35*math.sin(math.pi*u));cap=1-.72*smooth((u-.85)/.15)
  for j in range(K):
   th=2*math.pi*j/K;v.append(tuple(c+side*w*cap*math.sin(th)+Vector((0,0,.118*math.cos(th)*cap))))
 parts.append(mesh('digit_'+label,v,faces,skin))
 if label!='I':
  pts=[tuple(b+axis*(-.05+.27*(j/12))+Vector((0,0,.085+.095*math.sin(math.pi*j/12)-.055*j/12))) for j in range(13)]
  _,sp=tube('claw_'+label,pts,.038,clawmat)
  for j,p in enumerate(sp.points):p.radius=max(.04,1-j/12)
# Fuse static context to avoid floating capsule intersections. Hero root overlaps the fused root.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bpy.ops.object.join();o=bpy.context.object;o.name='original_fused_foot_ankle_limb_context';o.data.remesh_voxel_size=.055;bpy.ops.object.voxel_remesh();mod=o.modifiers.new('gentle_surface_smoothing','SMOOTH');mod.factor=.55;mod.iterations=3
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.19));o=bpy.context.object;o.name='persistent_solid_substrate';o.scale=(200,200,.36);o.data.materials.append(wall)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=8;s.render.threads_mode='FIXED';s.render.threads=2;s.cycles.use_denoising=True;s.render.resolution_x=540;s.render.resolution_y=960;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.fps=24;s.world.color=(.12,.12,.12)
s.view_settings.view_transform='AgX'
bpy.ops.object.camera_add(location=(6.8,-9.2,6.6));cam=bpy.context.object;target=Vector((-.20,.18,.40));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=9.1;s.camera=cam
for name,pos,energy,size,col in [('large_warm_key',(-1,-4,7),1000,5,(1,.84,.64)),('cool_edge',(3,4,5),1250,4,(.52,.77,1)),('soft_front',(-5,-1,4),400,4,(.83,.9,1))]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,.3))-o.location).to_track_quat('-Z','Y').to_euler()
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
F=ImageFont.truetype(font,27);small=ImageFont.truetype(font,17);mid=ImageFont.truetype(font,20)
qc=[]
frames=[0,60,119] if args.preview else range(120)
for f in frames:
 t=f/24;progress=smooth((t-.8)/3.35);cs=centers(progress);vs=surface(cs)
 for v,co in zip(hero.data.vertices,vs):v.co=co
 hero.data.update()
 for i,sp in ridges:
  x,y,z,theta=cs[i];w,h=dimensions(i/(R-1))
  for j,p in enumerate(sp.points):
   a=math.pi*.53+math.pi*.94*j/16;off=(h+.008)*math.cos(a);p.co=(x-math.sin(theta)*off,y+w*math.sin(a),z+math.cos(theta)*off,1)
 x,y,z,theta=cs[-1]
 for j,p in enumerate(clawsp.points):
  u=j/12;p.radius=max(.04,1-u);along=-.035+.25*u;off=.075+.08*math.sin(math.pi*u)-.05*u;p.co=(x+math.cos(theta)*along-math.sin(theta)*off,y,z+math.sin(theta)*along+math.cos(theta)*off,1)
 lowest=min(v[2] for v in vs);assert lowest>=-.001,(f,lowest)
 dest=OUT/f'{f:04d}.png';s.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
 im=Image.open(dest).convert('RGB');dr=ImageDraw.Draw(im);dr.text((34,48),'HOW DOES A GECKO LET GO?',font=small,fill=(153,186,191));dr.text((34,80),'A controlled release',font=F,fill=(241,230,207));dr.text((34,830),'Local view · substrate below',font=small,fill=(169,184,184));dr.text((34,862),'INTEGRATED VISUAL PROOF  /  5 SEC',font=small,fill=(207,217,215));dr.text((34,893),'Qualitative motion · not measured anatomy',font=small,fill=(169,184,184));im.save(dest)
 qc.append({'frame':f,'time':t,'progress':progress,'minimum_hero_surface_z':lowest,'tip_center_z':cs[-1][2]});print('PROOF_FRAME',f,flush=True)
if not args.preview:
 ff=imageio_ffmpeg.get_ffmpeg_exe();movie=OUT/'gecko-integrated-visual-proof-v1.mp4';subprocess.run([ff,'-y','-v','error','-framerate','24','-i',str(OUT/'%04d.png'),'-frames:v','120','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(movie)],check=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'original-integrated-proof.blend'))
 (OUT/'numeric-qc.json').write_text(json.dumps(qc,indent=2)+'\n');(OUT/'render-receipt.json').write_text(json.dumps({'movie':str(movie),'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'frames':120,'fps':24,'seconds':5,'resolution':[540,960],'audio':'silent visual-only proof; approved narration unchanged','anatomy_approved':False,'native_av_approved':False,'production_scope':'explicit user permission for4–6s proof only'},indent=2)+'\n')
