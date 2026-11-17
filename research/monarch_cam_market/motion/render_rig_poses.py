"""CPU rasterized pose-inspection sheet, not final lookdev or motion review.
Uses licensed source texture as reference; required attribution travels with output.
"""
import io,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from test_native_orca_rig import load,accessor
BASE=Path(__file__).parent;OUT=BASE/'out/orca'
def main():
 g,b=load(OUT/'orca_decoded.glb');a=g['meshes'][0]['primitives'][0];faces=accessor(g,b,a['indices']).ravel().reshape(-1,3).astype(int);uv=accessor(g,b,a['attributes']['TEXCOORD_0'])
 view=g['bufferViews'][g['images'][0]['bufferView']];start=view.get('byteOffset',0);texture=np.array(Image.open(io.BytesIO(b[start:start+view['byteLength']])).convert('RGB'))
 texuv=uv[faces].mean(1)%1;colors=texture[(texuv[:,1]*(texture.shape[0]-1)).astype(int),(texuv[:,0]*(texture.shape[1]-1)).astype(int)]
 poses=json.loads((OUT/'metric_rig_poses.json').read_text());sheet=Image.new('RGB',(900,1200),(17,26,34))
 eye=np.array([.35,.25,1.]);eye/=np.linalg.norm(eye);right=np.cross([0,1,0],eye);right/=np.linalg.norm(right);up=np.cross(eye,right)
 light=np.array([.1,1,.6]);light/=np.linalg.norm(light)
 for row,index in enumerate([0,3,5]):
  p=np.array(poses[index]['positions']);tri=p[faces];normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-8)
  shade=.5+.5*np.abs(normals@light);rgb=np.clip(colors*shade[:,None],0,255).astype('uint8');xy=np.c_[p@right*105+450,-p@up*105+225]
  image=Image.new('RGB',(900,400),(17,26,34));d=ImageDraw.Draw(image)
  for j in np.argsort(tri.mean(1)@eye):d.polygon([tuple(q) for q in xy[faces[j]]],fill=tuple(rgb[j]))
  d.text((20,15),f'INTERNAL METRIC RIG POSE | t={poses[index]["time"]:.2f}s | NOT FINAL',fill=(165,185,195))
  d.text((20,375),'Killer Whale by Abner Wu / Trouvaille - CC BY 4.0 | Original replacement rig by this project',fill=(135,155,165))
  sheet.paste(image,(0,row*400))
 sheet.save(OUT/'metric-rig-poses.jpg',quality=94)
 (OUT/'RIG_ATTRIBUTION.txt').write_text((BASE/'ATTRIBUTION-ORCA.md').read_text()+'\nThis test replaces skeleton/weights with original project-authored metric rig. Source texture retained.\n')
if __name__=='__main__':main()
