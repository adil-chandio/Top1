"""Whale-only fixed-camera locomotion diagnostic; not final concept fidelity.
MIT Tidewater mesh, native part/span tags used; custom simplified motion, not upstream full rig.
"""
import os,sys,json,math,hashlib,subprocess
from pathlib import Path
import bpy,numpy as np
BASE=Path(__file__).parent
# Reuse inspected importer; deliberately skip its still render.
code=(BASE/'inspect_tidewater.py').read_text().split('cam.location=(9,-23,6)')[0]
exec(compile(code,str(BASE/'inspect_tidewater.py'),'exec'))
DEST=BASE/'out/swim20';DEST.mkdir(exist_ok=True)
rig=np.frombuffer(raw,dtype='<f4',count=lv['vertices']*4,offset=lv['rig']).reshape(-1,4).copy()
rest=pos.astype(np.float64).copy()
FPS=12;FRAMES=240
s.render.resolution_x=640;s.render.resolution_y=360;s.render.resolution_percentage=100
s.cycles.samples=4;s.render.threads=2;s.render.fps=FPS
# This is intentionally locked off; all image motion must come from geometry.
cam.location=(9,-23,6);target=Vector((-1.6,0,-.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=43
# Fixed root: swimming-in-place makes deformation visible without translation masking it.

def pose(t):
 q=rest.copy()
 for part,key,sign in [(1,'left',1),(2,'right',-1)]:
  mask=np.abs(rig[:,1]-part)<.2
  root=np.array(meta['pectoral'][key]['origin'])
  axis=np.array(meta['pectoral'][key]['basis'])[2];axis=axis/np.linalg.norm(axis)
  angle=sign*.13*np.sin(t*.62+(.35 if part==2 else 0))*(.8+.35*rig[mask,2])
  v=q[mask]-root;c=np.cos(angle)[:,None];sn=np.sin(angle)[:,None]
  q[mask]=root+v*c+np.cross(np.broadcast_to(axis,v.shape),v)*sn+(v@axis)[:,None]*axis*(1-c)
 # Native longitudinal attachment tags keep flippers on their chest section.
 z=rig[:,0];k=np.clip((-z-.6)/8.1,0,1)
 w=t*1.2
 disp=.5*k*k*np.sin(w+k*.85)
 # First derivative gives local pitch, so peduncle/fluke cross-sections follow the bend.
 slope=(k*np.sin(w+k*.85)+.425*k*k*np.cos(w+k*.85))*(-1/8.1)
 theta=np.arctan(slope)
 yc=np.interp(z, np.array(meta['centerline']['z'])[::-1],np.array(meta['centerline']['y'])[::-1])
 dy=q[:,1]-yc;dz=q[:,2]-z
 q[:,1]=yc+disp+dy*np.cos(theta)+dz*np.sin(theta)
 q[:,2]=z-dy*np.sin(theta)+dz*np.cos(theta)
 out=np.stack((q[:,2],q[:,0],q[:,1]),axis=1).astype(np.float32)
 ob.data.vertices.foreach_set('co',out.ravel());ob.data.update()
 return out

if '--poses' in sys.argv:
 for f in [0,16,32,48]:
  pose(f/FPS);s.render.filepath=str(DEST/f'pose_{f:03}.png');bpy.ops.render.render(write_still=True)
else:
 samples=[]
 for f in range(FRAMES):
  pnow=pose(f/FPS)
  if f in [0,16,32,48,120,239]:samples.append({'frame':f,'max_vertex_displacement_m':float(np.max(np.linalg.norm(pnow-verts,axis=1))),'finite':bool(np.isfinite(pnow).all())})
  output=DEST/f'{f:04}.png'
  if not output.exists():s.render.filepath=str(output);bpy.ops.render.render(write_still=True)
  if f%12==0:print('PROGRESS',f,FRAMES,flush=True)
 import imageio_ffmpeg
 ff=imageio_ffmpeg.get_ffmpeg_exe()
 video=BASE/'out/HUMPBACK_20S_MOTION_DIAGNOSTIC.mp4'
 subprocess.run([ff,'-y','-framerate',str(FPS),'-i',str(DEST/'%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-movflags','+faststart',str(video)],check=True)
 receipt={'duration_s':20,'fps':FPS,'frames':FRAMES,'resolution':[640,360],'camera':'fixed','root':'fixed','audio':False,'scope':'whale-only diagnostic; no orcas, not selected-concept fidelity','motion':'native mesh part/span tags; custom Rodrigues fin rotation and vertical caudal bend; simplified, not expert-validated biomechanics','samples':samples,'video_bytes':video.stat().st_size,'sha256':hashlib.sha256(video.read_bytes()).hexdigest()}
 (BASE/'out/motion_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
