"""Original 3D illustrative assets for the full film assembly, not measured anatomy.
Source-informed foot identities; no borrowed image/model pixels. Blender bpy4.2.
"""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
OUT=Path('studio/runtime/gecko/visual-pass');OUT.mkdir(parents=True,exist_ok=True)
def reset():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(name,color,rough=.5):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
def sphere(name,pos,scale,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=pos);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(ma)
 for p in o.data.polygons:p.use_smooth=True
 return o
def mesh(name,verts,faces,ma):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);m.materials.append(ma)
 for p in m.polygons:p.use_smooth=True
 return o
def curve(name,pts,r,ma):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2;s=c.splines.new('POLY');s.points.add(len(pts)-1)
 for p,co in zip(s.points,pts):p.co=(*co,1)
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(ma);return o
def setup(target,loc,scale):
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True;s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.world.color=(.045,.06,.085)
 bpy.ops.object.camera_add(location=loc);c=bpy.context.object;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=scale;s.camera=c
 for name,pos,energy,size,col in [('key',(-3,-1,6),650,5,(1,.85,.67)),('rim',(3,3,4),500,3,(.44,.73,1)),('fill',(1,-4,2),160,4,(.7,.9,1))]:
  bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 s.render.film_transparent=True;return s
reset();skin=mat('original warm skin',(.62,.32,.13));ridge=mat('ventral transverse ridges',(.77,.47,.24));claw=mat('illustrative keratin claw',(.66,.59,.43));parts=[]
# z-positive is VENTRAL by construction. Looking from positive z preserves Fig1b layout.
parts.append(sphere('plantar body',(0,0,0),(.69,.68,.20),skin))
parts.append(sphere('ankle context',(.63,-.88,-.07),(.42,.94,.24),skin))
spec=json.loads(Path('research/monarch_cam_gecko_batch2/LEFT_PES_LAYOUT_SPEC.json').read_text());ridgelist=[]
for g in spec['digits']:
 a=Vector(((g['start'][0]-500)/100,(450-g['start'][1])/100,0))*.65;b=Vector(((g['tip'][0]-500)/100,(450-g['tip'][1])/100,0));axis=(b-a).normalized();side=Vector((-axis.y,axis.x,0));verts=[];N=40;K=20
 for i in range(N):
  u=i/(N-1);c=a.lerp(b,u);w=(g['width']/100)*(.50+.5*math.sin(math.pi*u)**.6);cap=min(1,(1-u)*15+.08)
  for k in range(K):
   th=2*math.pi*k/K;p=c+side*w*math.sin(th)*cap+Vector((0,0,.15*math.cos(th)*cap));verts.append(tuple(p))
 faces=[]
 for i in range(N-1):
  for k in range(K):
   q=i*K+k;n=i*K+(k+1)%K;faces.append((q,n,n+K,q+K))
 faces+=[tuple(reversed(range(K))),tuple((N-1)*K+k for k in range(K))];parts.append(mesh('digit_'+g['id'],verts,faces,skin))
 # Scale count is deliberately illustrative, not a taxonomic measurement/LDT boundary.
 for k in range(3,19):
  u=k/21;c=a.lerp(b,u);w=(g['width']/100)*(.50+.5*math.sin(math.pi*u)**.6);pts=[]
  for j in range(21):
   t=-1+2*j/20;p=c+side*w*t*.94+axis*(.025*(1-t*t))+Vector((0,0,.15*math.sqrt(max(0,1-(t*.94)**2))+.012));pts.append(tuple(p))
  ridgelist.append(('scale_'+g['id'],pts))
 if g['claw']:
  # Dorsal terminal claw is a placeholder. No exact ungual articulation asserted.
  pts=[tuple(b-axis*.13+Vector((0,0,-.12))),tuple(b+axis*.10+Vector((0,0,-.18))),tuple(b+axis*.25+Vector((0,0,-.11)))];curve('claw_marker_'+g['id'],pts,.035,claw)
# Join skin and voxel-remesh for a single connected external skin, not floating capsules.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bpy.ops.object.join();o=bpy.context.object;o.name='original_continuous_foot_skin';o.data.remesh_voxel_size=.045;bpy.ops.object.voxel_remesh();mod=o.modifiers.new('surface smoothing','SMOOTH');mod.factor=.5;mod.iterations=3
for p in o.data.polygons:p.use_smooth=True
# Check skin connectivity, not just an object name suggesting continuity.
adj=[[] for _ in o.data.vertices]
for e in o.data.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();components=0
for i in range(len(adj)):
 if i in seen:continue
 components+=1;stack=[i];seen.add(i)
 while stack:
  for n in adj[stack.pop()]:
   if n not in seen:seen.add(n);stack.append(n)
assert components==1, ('disconnected skin',components)
(OUT/'skin-topology.json').write_text(json.dumps({'connected_components':components,'vertices':len(adj),'status':'external skin only; no biological articulation proof'},indent=2))
for name,pts in ridgelist:curve(name,pts,.016,ridge)
s=setup((.1,-.15,0),(.1,-.15,9),7.8);s.render.filepath=str(OUT/'foot-ventral.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'source-informed-foot.blend'))
# Separate authored microstructure scene, never a literal microscopy reconstruction.
reset();hair=mat('setae warm',(.79,.50,.22));tip=mat('spatula schematic',(.18,.72,.61));substrate=mat('substrate',(.045,.11,.15))
for row in range(3):
 for k in range(6):
  x=-2.3+k*.85;y=-.8+row*.78
  curve('setal shaft',[(x-.24,y,1.7),(x-.1,y,1.05),(x+.04,y,.52)],.035,hair)
  for j in range(3):
   xx=x+(j-1)*.22;curve('branch',[(x+.04,y,.52),(xx,y,.24),(xx+.08,y,.04)],.012,hair)
   sphere('flattened_tip',(xx+.10,y,.025),(.11,.055,.018),tip)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,.0,-.13));bpy.context.object.scale=(6,3.8,.2);bpy.context.object.data.materials.append(substrate)
s=setup((0,0,.65),(4,-6,4.4),6.5);s.render.filepath=str(OUT/'setae-contact.png');bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'setae-schematic.blend'))
print('VISUAL_ASSETS_RENDERED',flush=True)
