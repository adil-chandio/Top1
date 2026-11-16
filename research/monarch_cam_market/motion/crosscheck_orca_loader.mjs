// Actual Three.js GLTFLoader/AnimationMixer/SkinnedMesh evaluation, no WebGL needed.
// Materials removed IN MEMORY only because Node has no image decoder; geometry,
// skin, bind matrices, transforms, weights and animation remain unchanged.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import * as THREE from './out/tools/node_modules/three/build/three.module.js';
import {GLTFLoader} from './out/tools/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
const base=path.dirname(fileURLToPath(import.meta.url));
const raw=fs.readFileSync(path.join(base,'out/orca/orca_decoded.glb'));
const n=raw.readUInt32LE(12);const json=JSON.parse(raw.subarray(20,20+n));
const binOffset=20+n;const bin=raw.subarray(binOffset+8,binOffset+8+raw.readUInt32LE(binOffset));
json.materials=[{}];delete json.images;delete json.textures;delete json.samplers;
for(const m of json.meshes)for(const p of m.primitives)p.material=0;
let jt=Buffer.from(JSON.stringify(json));const pad=(4-jt.length%4)%4;jt=Buffer.concat([jt,Buffer.alloc(pad,32)]);
const header=Buffer.alloc(20);header.writeUInt32LE(0x46546c67,0);header.writeUInt32LE(2,4);header.writeUInt32LE(20+jt.length+8+bin.length,8);header.writeUInt32LE(jt.length,12);header.writeUInt32LE(0x4e4f534a,16);
const bh=Buffer.alloc(8);bh.writeUInt32LE(bin.length,0);bh.writeUInt32LE(0x004e4942,4);
const input=Buffer.concat([header,jt,bh,bin]);
const gltf=await new GLTFLoader().parseAsync(input.buffer.slice(input.byteOffset,input.byteOffset+input.byteLength),'');
const meshList=[];gltf.scene.traverse(o=>{if(o.isSkinnedMesh)meshList.push(o);});
const mixer=new THREE.AnimationMixer(gltf.scene);const clip=gltf.animations[0];const action=mixer.clipAction(clip);action.setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;action.play();
const start=1/24,end=clip.duration;const samples=[];let reference=null;
for(let i=0;i<9;i++){
 const t=start+(end-start)*i/8;mixer.setTime(t);gltf.scene.updateMatrixWorld(true);
 const points=[];let displacement=0;const bounds=new THREE.Box3();
 for(const mesh of meshList){mesh.skeleton.update();const a=mesh.geometry.attributes.position;
  for(let j=0;j<a.count;j++){const p=new THREE.Vector3().fromBufferAttribute(a,j);mesh.applyBoneTransform(j,p);bounds.expandByPoint(p);points.push(p);}
 }
 if(!reference)reference=points.map(p=>p.clone());
 points.forEach((p,j)=>{displacement=Math.max(displacement,p.distanceTo(reference[j]));});
 samples.push({time:t,bbox_extent:bounds.getSize(new THREE.Vector3()).toArray(),max_vertex_displacement_from_start:displacement,vertices:points.length});
}
const result={type:'supported_ThreeJS_GLTFLoader_AnimationMixer_crosscheck',three_revision:THREE.REVISION,source_asset_unchanged:true,node_materials_disabled_for_decoder_only:true,skinned_meshes:meshList.length,joints:meshList[0].skeleton.bones.length,clip:clip.name,samples,creative_approval:false};
fs.writeFileSync(path.join(base,'out/orca/three_native_crosscheck.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
