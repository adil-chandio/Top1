// Original metric-space replacement rig for the licensed static derivative mesh.
// Does not reuse upstream OrcaRig code. CC-BY mesh attribution remains mandatory.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import * as THREE from './out/tools/node_modules/three/build/three.module.js';
import {GLTFLoader} from './out/tools/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
const base=path.dirname(fileURLToPath(import.meta.url));
const raw=fs.readFileSync(path.join(base,'out/orca/orca_decoded.glb'));
const n=raw.readUInt32LE(12);const json=JSON.parse(raw.subarray(20,20+n));
const bo=20+n;const bin=raw.subarray(bo+8,bo+8+raw.readUInt32LE(bo));
json.materials=[{}];delete json.images;delete json.textures;delete json.samplers;
for(const m of json.meshes)for(const p of m.primitives)p.material=0;
let jt=Buffer.from(JSON.stringify(json));jt=Buffer.concat([jt,Buffer.alloc((4-jt.length%4)%4,32)]);
const head=Buffer.alloc(20);head.writeUInt32LE(0x46546c67,0);head.writeUInt32LE(2,4);head.writeUInt32LE(20+jt.length+8+bin.length,8);head.writeUInt32LE(jt.length,12);head.writeUInt32LE(0x4e4f534a,16);
const bh=Buffer.alloc(8);bh.writeUInt32LE(bin.length,0);bh.writeUInt32LE(0x004e4942,4);const input=Buffer.concat([head,jt,bh,bin]);
const gltf=await new GLTFLoader().parseAsync(input.buffer.slice(input.byteOffset,input.byteOffset+input.byteLength),'');
let source;gltf.scene.traverse(o=>{if(o.isMesh&&!source)source=o;});
const geometry=source.geometry.clone();const positions=geometry.attributes.position;
// Author-selected design landmarks, not measured biological joint positions.
const xs=[2.4,.8,-.5,-1.6,-2.4,-3.1];const bones=[];
xs.forEach((x,i)=>{const b=new THREE.Bone();b.name='Monarch_metric_spine_'+i;b.position.x=i?x-xs[i-1]:x;if(i)bones[i-1].add(b);bones.push(b);});
for(const side of [-1,1]){const b=new THREE.Bone();b.name='Monarch_metric_pectoral_'+side;b.position.set(1.65-xs[0],-1,side*.55);bones[0].add(b);bones.push(b);}
const smooth=x=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x);};
const indices=new Uint16Array(positions.count*4);const weights=new Float32Array(positions.count*4);
for(let i=0;i<positions.count;i++){
 const x=positions.getX(i),y=positions.getY(i),z=positions.getZ(i);
 let a=0,b=0,w=0;
 if(x<=xs.at(-1)){a=b=xs.length-1;}else if(x<xs[0]){
  a=xs.findIndex((v,k)=>k<xs.length-1&&x<=v&&x>=xs[k+1]);b=a+1;w=smooth((xs[a]-x)/(xs[a]-xs[b]));
 }
 const fin=smooth((Math.abs(z)-.60)/.60)*smooth((x-1.05)/.2)*smooth((2.25-x)/.2)*smooth((-.65-y)/.35);
 indices.set([a,b,z<0?6:7,0],i*4);weights.set([(1-w)*(1-fin),w*(1-fin),fin,0],i*4);
}
geometry.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(indices,4));geometry.setAttribute('skinWeight',new THREE.Float32BufferAttribute(weights,4));
const mesh=new THREE.SkinnedMesh(geometry,new THREE.MeshBasicMaterial());mesh.add(bones[0]);mesh.updateMatrixWorld(true);mesh.bind(new THREE.Skeleton(bones));
function pose(t,enabled=true){
 for(let i=0;i<6;i++)bones[i].rotation.z=enabled?(i<2?0:(.035+(i-2)*.012)*Math.sin(t*2.15-i*.30)):0;
 bones[6].rotation.x=enabled?.08*Math.sin(t*1.05):0;bones[7].rotation.x=enabled?-.08*Math.sin(t*1.05+.3):0;
 mesh.updateMatrixWorld(true);mesh.skeleton.update();
 return Array.from({length:positions.count},(_,j)=>mesh.applyBoneTransform(j,new THREE.Vector3().fromBufferAttribute(positions,j)).toArray());
}
const rest=pose(0,false);let bindError=0;
rest.forEach((p,i)=>{bindError=Math.max(bindError,new THREE.Vector3(...p).distanceTo(new THREE.Vector3().fromBufferAttribute(positions,i)));});
if(bindError>1e-5)throw Error('metric bind changed rest mesh');
const restbox=new THREE.Box3().setFromBufferAttribute(positions).getSize(new THREE.Vector3());const samples=[],poses=[];
for(let i=0;i<9;i++){
 const time=i*.25;const p=pose(time);const box=new THREE.Box3().setFromPoints(p.map(v=>new THREE.Vector3(...v))).getSize(new THREE.Vector3());
 let maximum=0;for(let j=0;j<p.length;j++)maximum=Math.max(maximum,new THREE.Vector3(...p[j]).distanceTo(new THREE.Vector3(...rest[j])));
 const ratio=Math.max(box.x/restbox.x,box.y/restbox.y,box.z/restbox.z);
 if(!Number.isFinite(maximum)||ratio>1.5||maximum>1)throw Error('metric skin sanity failed');
 samples.push({time,bbox_extent:box.toArray(),max_displacement_from_bind_metres:maximum,max_extent_ratio:ratio});poses.push({time,positions:p});
}
const result={type:'original_metric_rig_ThreeJS_skinning_test',source_geometry_unchanged:true,bind_max_error:bindError,bones:bones.length,vertices:positions.count,technical_size_sanity_passed:true,original_native_clip_used:false,biomechanics_validated:false,independent_review:false,limitation:'Artist-designed eight-bone rig, not measured cetacean skeletal anatomy. Source rig incompatibility confirmed by supported-loader comparison; mesh remains CC-BY derivative.',samples};
fs.writeFileSync(path.join(base,'out/orca/metric_rig_test.json'),JSON.stringify(result,null,2)+'\n');
fs.writeFileSync(path.join(base,'out/orca/metric_rig_poses.json'),JSON.stringify(poses));
console.log(JSON.stringify(result,null,2));
