"""Actual two-species 3D blocking with source meshes and shared depth buffer.
INTERNAL, low-LOD/simple-lighting study. Not an accepted integrated creative proof.
No final score/effects, no reference footage, no public upload.
"""
import io,json,math,hashlib,subprocess,os
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import imageio_ffmpeg
import render_metric_motion as raster
from test_native_orca_rig import load,accessor
BASE=Path(__file__).parent;LOOK=os.environ.get('MONARCH_WATER_LOOK')=='1';OUT=BASE/('out/water-look-v3' if LOOK else 'out/native-scene-v2');FPS=24;N=150;W,H=(1280,720) if LOOK else (640,360)
raster.W=W;raster.H=H

def hump_source():
 folder=BASE/'out/tidewater';meta=json.loads((folder/'humpback.json').read_text());raw=(folder/'humpback.bin').read_bytes();lv=meta['levels'][0 if LOOK else 2]
 def floats(key,n):return np.frombuffer(raw,dtype='<f4',count=lv['vertices']*n,offset=lv[key]).reshape(-1,n).copy()
 p=floats('position',3);uv=floats('uv',2);rig=floats('rig',4);faces=np.frombuffer(raw,dtype='<u4',count=lv['indices'],offset=lv['index']).reshape(-1,3).astype(int)
 texture=np.array(Image.open(folder/'humpback_albedo.png').convert('RGB'))
 def pose(t):
  q=p.astype(float).copy()
  for part,key,sign in [(1,'left',1),(2,'right',-1)]:
   mask=np.abs(rig[:,1]-part)<.2;root=np.array(meta['pectoral'][key]['origin']);axis=np.array(meta['pectoral'][key]['basis'])[2];axis/=np.linalg.norm(axis)
   angle=sign*.10*np.sin(t*.62+(.35 if part==2 else 0))*(.8+.35*rig[mask,2]);v=q[mask]-root;c=np.cos(angle)[:,None];sn=np.sin(angle)[:,None]
   q[mask]=root+v*c+np.cross(np.broadcast_to(axis,v.shape),v)*sn+(v@axis)[:,None]*axis*(1-c)
  z=rig[:,0];k=np.clip((-z-.6)/8.1,0,1);phase=t*1.2
  displacement=.40*k*k*np.sin(phase+k*.85);slope=(.8*k*np.sin(phase+k*.85)+.34*k*k*np.cos(phase+k*.85))*(-1/8.1);angle=np.arctan(slope)
  centre=np.interp(z,np.array(meta['centerline']['z'])[::-1],np.array(meta['centerline']['y'])[::-1]);dy=q[:,1]-centre;dz=q[:,2]-z
  q[:,1]=centre+displacement+dy*np.cos(angle)+dz*np.sin(angle);q[:,2]=z-dy*np.sin(angle)+dz*np.cos(angle)
  return np.stack([q[:,2],q[:,1],-q[:,0]],axis=1)
 return pose,faces,uv,texture,lv

def orca_source():
 g,b=load(BASE/'out/orca/orca_metric_rig.glb');p=g['meshes'][0]['primitives'][0];faces=accessor(g,b,p['indices']).ravel().reshape(-1,3).astype(int);uv=accessor(g,b,p['attributes']['TEXCOORD_0'])
 v=g['bufferViews'][g['images'][0]['bufferView']];start=v.get('byteOffset',0);tex=np.array(Image.open(io.BytesIO(b[start:start+v['byteLength']])).convert('RGB'))
 poses=json.loads((BASE/'out/orca/metric_rig_scene_poses.json').read_text())
 far=json.loads((BASE/'out/orca/metric_rig_far_scene_poses.json').read_text())
 return poses,far,faces,uv,tex

def transform(p,location,yaw=0):
 c=math.cos(yaw);s=math.sin(yaw);q=p.copy();q[:,0]=p[:,0]*c+p[:,2]*s;q[:,2]=-p[:,0]*s+p[:,2]*c
 # Shared camera target, all animals in same world coordinates.
 return q+np.array(location)-np.array([5.,0.,4.])

def main():
 OUT.mkdir(parents=True,exist_ok=True);hp,hf,hu,ht,level=hump_source();poses,farposes,of,ou,ot=orca_source()
 if len(poses)!=N:raise ValueError('150 actual metric rig samples required')
 yy,xx=np.mgrid[0:H,0:W];v=np.exp(-((xx-W*.65)/(W*.8))**2-((yy+30)/(H*1.1))**2)
 bg=np.stack([6+v*11,20+v*26,30+v*35],axis=2).astype('uint8')
 if LOOK:
  nx=xx/W;ny=yy/H
  shaft=np.zeros((H,W))
  for centre,width in [( .35,.035),(.55,.07),(.8,.025)]:
   shaft+=np.exp(-((nx-centre-ny*.24)/width)**2)*np.exp(-ny*2.8)
  bg=np.clip(bg.astype(float)+shaft[:,:,None]*np.array([8,24,29]),0,255).astype('uint8')
 ff=imageio_ffmpeg.get_ffmpeg_exe();silent=OUT/'NATIVE_SCENE_SILENT_INTERNAL.mp4'
 command=[ff,'-nostdin','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(silent)]
 process=subprocess.Popen(command,stdin=subprocess.PIPE);stills=[];trace=[]
 try:
  for f in range(N):
   t=f/FPS;pixels=bg.copy();z=np.full((H,W),-np.inf);o=np.array(poses[f]['positions']);hb=hp(t)
   if not np.isfinite(hb).all():raise ValueError('nonfinite humpback deformation')
   near=(-8+t*.9,0,1);far=(-11+t*.82,-.8,7);approach=(20-t*1.35,-.4,9-t*.12)
   for vertices,faces,uv,tex,loc,yaw in [(np.array(farposes[f]['positions'])*.88,of,ou,ot,far,-.035),(hb,hf,hu,ht,approach,math.pi+.10),(o,of,ou,ot,near,.045)]:
    raster.render(transform(vertices,loc,yaw)- (np.array([t*.12,0,0]) if LOOK else 0),faces,uv,tex,camera=(.16,.20,1) if LOOK else (.1,.4,1),scale=(28*(1+t*.009)) if LOOK else 13,canvas=pixels,zbuffer=z,draw_labels=False,water_look=LOOK)
   image=Image.fromarray(pixels);d=ImageDraw.Draw(image);
   if LOOK:
    image.save(OUT/f'look-frame-{f:03}.jpg',quality=95) if f in (0,75,149) else None
   d.text((14,12),'INTERNAL NATIVE-MESH BLOCKING / NOT FINAL',fill=(145,172,184));d.text((14,27),'Shared 3D scene | low-LOD humpback | original rig study',fill=(115,145,160))
   d.text((14,H-26),'Orca: Abner Wu / Trouvaille, CC BY 4.0 | Humpback: Tidewater, MIT',fill=(125,151,162));d.text((14,H-13),'Project-authored motion/staging. No documented encounter reconstructed.',fill=(105,132,146))
   if f in (0,75,149):image.save(OUT/f'native-scene-{f:03}.jpg',quality=95);stills.append(image)
   process.stdin.write(image.tobytes());trace.append({'frame':f,'near_orca':near,'far_orca':far,'humpback':approach,'humpback_extent':np.ptp(hb,axis=0).tolist()})
   if f%25==0:print('RENDER',f,N,flush=True)
  process.stdin.close()
  if process.wait(timeout=60):raise ValueError('encoder failed')
 except BaseException:process.kill();process.wait();raise
 voice=BASE/'out/narration-timing/original_opening_narration.wav';dest=OUT/'NATIVE_SCENE_VOICE_INTERNAL.mp4'
 if hashlib.sha256(voice.read_bytes()).hexdigest()!='ed564baafb631f4599ebb09e0dc61f9d2fd7108304809efb90ba3de3dbe45e37':raise ValueError('original narration changed')
 subprocess.run([ff,'-nostdin','-y','-v','error','-xerror','-i',str(silent),'-i',str(voice),'-map','0:v:0','-map','1:a:0','-t',str(N/FPS),'-c:v','copy','-c:a','aac','-b:a','160k','-movflags','+faststart',str(dest)],check=True,timeout=60)
 subprocess.run([ff,'-nostdin','-v','error','-xerror','-i',str(dest),'-f','null','-'],check=True,timeout=60)
 sheet=Image.new('RGB',(W,H*3))
 for i,image in enumerate(stills):sheet.paste(image,(0,H*i))
 sheet.save(OUT/'native-scene-sheet.jpg',quality=94)
 (OUT/'trajectory.json').write_text(json.dumps(trace,indent=2));(OUT/'ATTRIBUTION-ORCA.md').write_text((BASE/'ATTRIBUTION-ORCA.md').read_text()+'\nOriginal project metric skeleton, skin weights and motion; source material retained.\n');(OUT/'LICENSE-TIDEWATER.txt').write_text((BASE/'LICENSE-TIDEWATER.txt').read_text())
 report={'type':'actual_native_mesh_scene_voice_blocking_NOT_final','frames':N,'fps':FPS,'duration_seconds':N/FPS,'resolution':[W,H],'actors':{'orcas':2,'far_orca_phase_offset_seconds':.85,'far_orca_relative_scale':.88,'orca_vertices_each':len(o),'humpback_vertices':level['vertices'],'humpback_triangles':level['indices']//3},'camera_static':not LOOK,'water_look_development':LOOK,'physically_based_path_tracer':False,'shared_zbuffer':True,'independent_world_trajectories':True,'actual_geometry_deformation':True,'voice_only':True,'speed_or_pitch_change':False,'music_or_sfx_added':False,'full_decode_passed':True,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size,'source_orca_glb_sha256':hashlib.sha256((BASE/'out/orca/orca_metric_rig.glb').read_bytes()).hexdigest(),'source_humpback_hashes':{name:hashlib.sha256((BASE/'out/tidewater'/name).read_bytes()).hexdigest() for name in ('humpback.bin','humpback.json','humpback_albedo.png')},'independent_review':False,'actual_sound_listening':False,'production_release':False,'limits':['CPU raster lookdev, not final cinematic quality; LOD0 humpback when water look enabled','No anatomically vetted prey asset yet, so hunt target remains unresolved','No collision, successful rescue or measured animal intent depicted','No independent, reference-AV or integrated sound-design gate cleared']}
 (OUT/'scene_receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
