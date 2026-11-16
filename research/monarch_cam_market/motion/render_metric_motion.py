"""Actual skinned-vertex motion diagnostic with UV texture/z-buffer CPU rendering.
Not final lighting, not a cinematic render, not an integrated sound proof.
"""
import io,json,subprocess,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import imageio_ffmpeg
from test_native_orca_rig import load,accessor
BASE=Path(__file__).parent;OUT=BASE/'out/orca';W,H=720,405

def render(p,faces,uv,texture,*,camera=(.35,.25,1.),scale=82,canvas=None,zbuffer=None,draw_labels=True,water_look=False):
 eye=np.array(camera,dtype=float);eye/=np.linalg.norm(eye);right=np.cross([0,1,0],eye);right/=np.linalg.norm(right);up=np.cross(eye,right)
 xy=np.c_[p@right*scale+W*.50,-p@up*scale+H*.54];depth=p@eye
 n=np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]])
 vn=np.zeros_like(p)
 for k in range(3):np.add.at(vn,faces[:,k],n)
 vn/=np.maximum(np.linalg.norm(vn,axis=1,keepdims=True),1e-8)
 light=np.array([.1,1,.8]);light/=np.linalg.norm(light);shade=.30+.70*np.maximum(0,vn@light)
 pixels=canvas if canvas is not None else np.full((H,W,3),(17,27,36),dtype='uint8');zbuf=zbuffer if zbuffer is not None else np.full((H,W),-np.inf)
 for indices in faces:
  q=xy[indices];x0=max(0,int(np.floor(q[:,0].min())));x1=min(W-1,int(np.ceil(q[:,0].max())));y0=max(0,int(np.floor(q[:,1].min())));y1=min(H-1,int(np.ceil(q[:,1].max())))
  if x1<x0 or y1<y0:continue
  a,b,c=q;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-8:continue
  yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
  u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
  v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w=1-u-v
  z=u*depth[indices[0]]+v*depth[indices[1]]+w*depth[indices[2]]
  region=zbuf[y0:y1+1,x0:x1+1];mask=(u>=0)&(v>=0)&(w>=0)&(z>region)
  if not mask.any():continue
  tu=u*uv[indices[0],0]+v*uv[indices[1],0]+w*uv[indices[2],0];tv=u*uv[indices[0],1]+v*uv[indices[1],1]+w*uv[indices[2],1]
  # Source GLTF texture coordinates use the embedded image origin (flipY false).
  tx=np.clip((tu*(texture.shape[1]-1)).astype(int),0,texture.shape[1]-1);ty=np.clip((tv*(texture.shape[0]-1)).astype(int),0,texture.shape[0]-1)
  intensity=u*shade[indices[0]]+v*shade[indices[1]]+w*shade[indices[2]]
  color=np.clip(texture[ty,tx]*intensity[:,:,None],0,255).astype('uint8')
  if water_look:
   # Shade in linear light; a broad wet-skin lobe, skylight and wavelength
   # dependent extinction. This is lookdev, not a physical path tracer.
   normal=u[:,:,None]*vn[indices[0]]+v[:,:,None]*vn[indices[1]]+w[:,:,None]*vn[indices[2]]
   normal/=np.maximum(np.linalg.norm(normal,axis=2,keepdims=True),1e-8)
   ndl=np.maximum(0,normal@light);halfway=light+eye;halfway/=np.linalg.norm(halfway)
   spec=np.maximum(0,normal@halfway)**48*.28
   fresnel=(1-np.maximum(0,normal@eye))**5*.12
   albedo=(texture[ty,tx]/255.)**2.2
   linear=albedo*(.09+ndl[:,:,None]*.72)*np.array([.60,.86,1.0])
   linear+=(spec+fresnel)[:,:,None]*np.array([.40,.70,.82])
   distance=np.maximum(1.,26.-z)
   transmission=np.exp(-distance[:,:,None]*np.array([.062,.025,.017]))
   linear=linear*transmission+np.array([.008,.050,.070])*(1-transmission)
   color=np.clip(linear**(1/2.2)*255,0,255).astype('uint8')
  pixels[y0:y1+1,x0:x1+1][mask]=color[mask];region[mask]=z[mask]
 image=Image.fromarray(pixels)
 if not draw_labels:return image
 d=ImageDraw.Draw(image);d.text((15,12),'INTERNAL RIG MOTION / NOT FINAL LOOKDEV',fill=(155,177,190));d.text((15,H-20),'Killer Whale: Abner Wu / Trouvaille, CC BY 4.0 | Original metric rig',fill=(130,151,166))
 return image

def main():
 g,b=load(OUT/'orca_metric_rig.glb');a=g['meshes'][0]['primitives'][0];faces=accessor(g,b,a['indices']).ravel().reshape(-1,3).astype(int);uv=accessor(g,b,a['attributes']['TEXCOORD_0'])
 v=g['bufferViews'][g['images'][0]['bufferView']];start=v.get('byteOffset',0);tex=np.array(Image.open(io.BytesIO(b[start:start+v['byteLength']])).convert('RGB'))
 frames=json.loads((OUT/'metric_rig_dense_poses.json').read_text());ff=imageio_ffmpeg.get_ffmpeg_exe();dest=OUT/'METRIC_RIG_MOTION_INTERNAL.mp4'
 command=[ff,'-nostdin','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','24','-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-movflags','+faststart',str(dest)]
 process=subprocess.Popen(command,stdin=subprocess.PIPE);samples=[]
 try:
  for i,f in enumerate(frames):
   image=render(np.array(f['positions']),faces,uv,tex)
   if i in (0,72,143):image.save(OUT/f'metric-motion-{i:03}.jpg',quality=95);samples.append(image)
   process.stdin.write(image.tobytes())
  process.stdin.close()
  if process.wait(timeout=60):raise RuntimeError('encoding failed')
 except BaseException:process.kill();process.wait();raise
 subprocess.run([ff,'-nostdin','-v','error','-xerror','-i',str(dest),'-f','null','-'],check=True,timeout=60)
 sheet=Image.new('RGB',(W,H*3))
 for i,image in enumerate(samples):sheet.paste(image,(0,H*i))
 sheet.save(OUT/'metric-motion-sheet.jpg',quality=94)
 report={'type':'actual_textured_metric_mesh_motion_diagnostic','frames':len(frames),'fps':24,'duration_seconds':len(frames)/24,'encoded_resolution':[720,406],'camera_fixed':True,'actual_skinned_geometry_per_frame':True,'uv_texture_interpolated':True,'full_decode_passed':True,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size,'audio':False,'independent_review':False,'production_release':False,'limits':'Simple CPU diagnostic lighting/rasterizer; not final shading, anatomy signoff or sound-integrated feasibility.'}
 (OUT/'metric_motion_receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
