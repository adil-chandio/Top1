"""Full-length replacement production job. Original illustrative assets.
Native 720x1280 rendered frames, not a quality/anatomy certification.
"""
import bpy, math, json, hashlib, subprocess, sys
from pathlib import Path
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
ROOT=Path.cwd();OUT=ROOT/'studio/runtime/gecko/cinematic-full-v2';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'studio/runtime/gecko/cinematic-replacement/replacement.blend'))
s=bpy.context.scene;s.render.resolution_x=720;s.render.resolution_y=1280;s.render.resolution_percentage=100;s.cycles.samples=12;s.render.threads_mode='FIXED';s.render.threads=2
s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-1.0
# Correct oversized eye presentation; do not claim this constitutes anatomical validation.
for o in bpy.data.objects:
 if o.name.startswith(('iris','slit pupil','raised eye rim')):o.scale*=.68
skin=bpy.data.materials.get('Tokay-inspired blue grey with irregular ochre patches');p=skin.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.72;p.inputs['Subsurface Weight'].default_value=.025
for n in skin.node_tree.nodes:
 if n.type=='VALTORGB':
  for e in n.color_ramp.elements:
   if .58<e.position<.60:e.color=(.26,.075,.025,1)
# Keep exterior and micro visual worlds separate.
exterior=list(bpy.data.objects)
def material(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.55;return m
hair=material('illustrative keratin',(.43,.28,.105));surface=material('microscopic substrate',(.025,.095,.12))
def strand(name,pts,r):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2;sp=c.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for b,pt in zip(sp.bezier_points,pts):b.co=pt;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(hair)
for row in range(4):
 for j in range(9):
  x=(j-4)*.43;y=(row-1.5)*.49
  strand('setal shaft',[(x-.15,y,1.5),(x-.13,y,1.05),(x,y,.43)],.025)
  for k in range(4):
   xx=x+(k-1.5)*.07;strand('branch',[(x,y,.48),(xx+.08,y,.20),(xx+.13,y,.035)],.009)
   bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=6,location=(xx+.13,y,.02));o=bpy.context.object;o.scale=(.065,.035,.013);o.data.materials.append(hair)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.22));o=bpy.context.object;o.scale=(10,10,.42);o.data.materials.append(surface)
micro=[o for o in bpy.data.objects if o not in exterior]
cam=s.camera;cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=7.1
lights=[o for o in exterior if o.type=='LIGHT']
audio=ROOT/'studio/runtime/gecko/narration/english-narration-v1.wav';assert hashlib.sha256(audio.read_bytes()).hexdigest()=='1d7a3284670a93ded1ad21f24aee980f3f39eba2766daa6a16e85580c3e41cc8'
cues=json.loads((ROOT/'research/monarch_cam_gecko_batch3/ENGLISH_CAPTION_CUES.json').read_text())['cues']
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';ft=ImageFont.truetype(font,30);small=ImageFont.truetype(font,19);titlefont=ImageFont.truetype(font,33)
def wrap(d,text,font,width):
 lines=[];line=''
 for w in text.split():
  new=(line+' '+w).strip()
  if d.textlength(new,font=font)>width and line:lines.append(line);line=w
  else:line=new
 if line:lines.append(line)
 return lines
ff=imageio_ffmpeg.get_ffmpeg_exe();movie=OUT/'gecko-complete-cinematic-v2.mp4'
encoder=subprocess.Popen([ff,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','25','-i','-','-i',str(audio),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-t','63.68','-movflags','+faststart',str(movie)],stdin=subprocess.PIPE)
shots=[(0,11.08,(3.8,5.5,13),(0,-.45,.25),'STRONG GRIP. CONTROLLED RELEASE.'),(11.08,20.27,(3.0,-4.7,3.8),(0,0,.55),'FROM PAD TO MICROSCOPIC HAIRS'),(20.27,26.59,(1.6,-2.8,1.25),(0,0,.16),'CLOSE CONTACT, NOT SUCTION'),(26.59,33.20,(2.9,1.7,3.6),(1.40,1.25,.14),'DIRECTION MATTERS'),(33.20,44.02,(2.4,2.7,2.8),(1.4,1.25,.14),'RELEASE: TIP TOWARD BASE'),(44.02,47.95,(-2.5,3.8,5.8),(0,1.5,.32),'DIGITAL HYPEREXTENSION'),(47.95,52.19,(2.2,-3.1,2.4),(0,0,.50),'TWO DIFFERENT SCALES'),(52.19,63.68,(3.3,5.8,12.7),(0,-.45,.25),'CONTACT. DIRECTION. CONTROL.')]
lastmode=None
for f in range(1592):
 t=f/25;start,end,pos,target,title=next(sh for sh in shots if sh[0]<=t<sh[1]);u=(t-start)/(end-start);ismicro=11.08<=t<26.59 or 47.95<=t<52.19
 if ismicro!=lastmode:
  for o in exterior:
   if o.type not in ['CAMERA','LIGHT']:o.hide_render=ismicro
  for o in micro:o.hide_render=not ismicro
  lastmode=ismicro
 cam.location=Vector(pos)+Vector((.13*math.sin(u*math.pi),-.18*u,-.25*u));tar=Vector(target);cam.rotation_euler=(tar-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.dof.focus_distance=(cam.location-tar).length;cam.data.lens=48
 for o in lights:o.data.energy=(420 if ismicro else 620) if o==lights[0] else (220 if ismicro else 300)
 # Source is illustrative: no fabricated walk cycle or validated toe-release simulation.
 s.render.filepath=str(OUT/'current.png');bpy.ops.render.render(write_still=True)
 im=Image.open(OUT/'current.png').convert('RGB');d=ImageDraw.Draw(im);d.rectangle((0,0,720,150),fill=(4,14,19));d.text((34,24),'MONARCH CAM / GECKO',font=small,fill=(153,185,183))
 for j,line in enumerate(wrap(d,title,titlefont,650)):d.text((34,65+j*40),line,font=titlefont,fill=(236,221,190))
 cue=next((c for c in cues if c['start']<=t<c['end']),None)
 if cue:
  lines=wrap(d,cue['text'],ft,638);y=1230-len(lines)*40;d.rounded_rectangle((24,y-14,696,1250),radius=12,fill=(4,14,19))
  for j,line in enumerate(lines):d.text(((720-d.textlength(line,font=ft))/2,y+j*40),line,font=ft,fill=(243,235,217))
 d.text((34,1040),'3D SCHEMATIC / NOT TO SCALE' if ismicro else 'ILLUSTRATIVE ANATOMY / NOT VALIDATED',font=small,fill=(180,201,198))
 encoder.stdin.write(im.tobytes())
 if f%125==0:im.save(OUT/f'review-{f:04}.jpg');(OUT/'progress.json').write_text(json.dumps({'frames_completed':f+1,'frames_total':1592,'seconds_encoded':(f+1)/25,'quality_pass':False}));print('FULL_RENDER_FRAME',f,flush=True)
encoder.stdin.close();assert encoder.wait()==0
check=subprocess.run([ff,'-v','error','-i',str(movie),'-f','null','-'],capture_output=True,text=True);assert check.returncode==0 and not check.stderr
(OUT/'receipt.json').write_text(json.dumps({'file':str(movie),'frames':1592,'duration':63.68,'native_render_resolution':[720,1280],'fps':25,'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'decode_pass':True,'quality_pass':False,'anatomy_validated':False,'native_av_listened':False,'limitations':'Illustrative original animal, static pose with moving perspective cameras; no validated toe release or gait; no claim of user acceptance.'},indent=2));print('FULL_VIDEO_COMPLETE',movie,flush=True)
