"""Evaluate original glTF skin/animation without Blender or replacing authored rig.
Numerical native linear-blend-skinning test, NOT biomechanical/creative approval.
"""
import argparse,json,struct
from pathlib import Path
import numpy as np

def load(path):
 raw=Path(path).read_bytes();magic,version,total=struct.unpack_from('<III',raw)
 if magic!=0x46546c67 or version!=2 or total!=len(raw):raise ValueError('invalid GLB')
 n,k=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+n]);off=20+n;size,kind=struct.unpack_from('<II',raw,off)
 if kind!=0x004e4942:raise ValueError('BIN chunk required')
 return g,raw[off+8:off+8+size]

def accessor(g,blob,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
 types={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'};sizes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
 dtype=np.dtype(types[a['componentType']]);count=sizes[a['type']];offset=v.get('byteOffset',0)+a.get('byteOffset',0)
 stride=v.get('byteStride',count*dtype.itemsize)
 data=np.ndarray((a['count'],count),dtype=dtype,buffer=blob,offset=offset,strides=(stride,dtype.itemsize)).copy()
 if a.get('normalized') and dtype.kind in 'ui':data=data.astype(float)/np.iinfo(dtype).max
 return data

def matrix(node):
 if 'matrix' in node:return np.array(node['matrix']).reshape(4,4).T
 x,y,z,w=node.get('rotation',[0,0,0,1]);r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
 m=np.eye(4);m[:3,:3]=r@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0]);return m

def slerp(a,b,t):
 a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);dot=np.dot(a,b)
 if dot<0:b=-b;dot=-dot
 if dot>.9995:q=a+(b-a)*t;return q/np.linalg.norm(q)
 theta=np.arccos(np.clip(dot,-1,1));return (np.sin((1-t)*theta)*a+np.sin(t*theta)*b)/np.sin(theta)

def evaluate(g,blob,time):
 nodes=[dict(n) for n in g['nodes']];clip=g['animations'][0]
 for ch in clip['channels']:
  s=clip['samplers'][ch['sampler']]
  if s.get('interpolation','LINEAR')!='LINEAR':raise ValueError('explicit support needed for non-linear sampler')
  ts=accessor(g,blob,s['input']).ravel();values=accessor(g,blob,s['output']);i=max(0,min(len(ts)-2,int(np.searchsorted(ts,time,side='right')-1)))
  u=float(np.clip((time-ts[i])/(ts[i+1]-ts[i]),0,1));kind=ch['target']['path']
  v=slerp(values[i],values[i+1],u) if kind=='rotation' else values[i]*(1-u)+values[i+1]*u
  nodes[ch['target']['node']][kind]=v
 parent={c:i for i,n in enumerate(nodes) for c in n.get('children',[])};cache={}
 def world(i):
  if i not in cache:cache[i]=(world(parent[i]) if i in parent else np.eye(4))@matrix(nodes[i])
  return cache[i]
 mesh_id=next(i for i,n in enumerate(nodes) if 'mesh' in n and 'skin' in n);node=nodes[mesh_id];skin=g['skins'][node['skin']]
 primitive=g['meshes'][node['mesh']]['primitives'][0];attrs=primitive['attributes']
 positions=accessor(g,blob,attrs['POSITION']);joints=accessor(g,blob,attrs['JOINTS_0']);weights=accessor(g,blob,attrs['WEIGHTS_0'])
 if not np.allclose(weights.sum(axis=1),1,atol=.02):raise ValueError('skin weight sum failed')
 inversebind=accessor(g,blob,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
 inversemesh=np.linalg.inv(world(mesh_id));transforms=np.array([inversemesh@world(j)@inversebind[k] for k,j in enumerate(skin['joints'])])
 hp=np.c_[positions,np.ones(len(positions))];output=np.zeros((len(hp),4))
 for k in range(4):output+=np.einsum('nij,nj->ni',transforms[joints[:,k].astype(int)],hp)*weights[:,k:k+1]
 return output[:,:3],positions

def main():
 p=argparse.ArgumentParser();p.add_argument('--asset',default=str(Path(__file__).parent/'out/orca/orca_decoded.glb'));p.add_argument('--out',required=True);a=p.parse_args()
 g,blob=load(a.asset);clip=g['animations'][0];timeline=accessor(g,blob,clip['samplers'][0]['input']).ravel();start,end=float(timeline[0]),float(timeline[-1]);times=np.linspace(start,end,9)
 reference,rest=evaluate(g,blob,start);samples=[]
 for t in times:
  q,_=evaluate(g,blob,float(t));d=np.linalg.norm(q-reference,axis=1)
  if not np.isfinite(q).all():raise ValueError('nonfinite skinned vertices')
  samples.append({'bbox_extent_to_rest_extent_max_ratio':float(np.max(np.ptp(q,axis=0)/np.maximum(np.ptp(rest,axis=0),1e-6))),'time':float(t),'max_vertex_displacement_from_clip_start_model_units':float(d.max()),'moving_vertices_over_0_001':int((d>.001).sum())})
 if max(s['max_vertex_displacement_from_clip_start_model_units'] for s in samples)<.001:raise ValueError('native animation has no measurable deformation')
 compatibility=max(s['bbox_extent_to_rest_extent_max_ratio'] for s in samples)<5
 result={'native_rig_ready_for_production':compatibility,'compatibility_status':'numerically_plausible_not_approved' if compatibility else 'FAILED_size_sanity_requires_independent_loader_crosscheck','type':'actual_native_glTF_animation_skinning_evaluation','clip_name':clip.get('name'),'clip_seconds':[start,end],'joints':len(g['skins'][0]['joints']),'animation_channels':len(clip['channels']),'vertices_tested':len(reference),'native_skin_preserved':True,'weight_sums_checked':True,'finite_samples':True,'samples':samples,'decision':'Do not deploy this native skin yet: numerical output shows implausible bounding extents relative to rest mesh. Cross-check decoded asset, bind transforms and evaluator against a supported loader before blaming source rig. Preserve source hierarchy for investigation; previous integrated_scene.py drops rig objects. Finite movement alone is not a pass.','creative_or_anatomy_approval':False}
 Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
