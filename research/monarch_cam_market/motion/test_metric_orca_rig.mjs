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
for(let i=0;i<indices.length;i++)if(weights[i]===0)indices[i]=0;
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

// Export a self-contained GLB, preserving source textures/materials/UV/geometry.
// Legacy incompatible skin/animation is replaced, never patched in place.
pose(0,false);
const exported=JSON.parse(raw.subarray(20,20+n));
let binary=Buffer.from(bin);
function appendAccessor(array,type,componentType,count,min,max){
 const padding=(4-binary.length%4)%4;binary=Buffer.concat([binary,Buffer.alloc(padding)]);
 const offset=binary.length,data=Buffer.from(array.buffer,array.byteOffset,array.byteLength);binary=Buffer.concat([binary,data]);
 const vi=exported.bufferViews.length;exported.bufferViews.push({buffer:0,byteOffset:offset,byteLength:data.length});
 const acc={bufferView:vi,componentType,count,type};if(min)acc.min=min;if(max)acc.max=max;
 const ai=exported.accessors.length;exported.accessors.push(acc);return ai;
}
const ji=appendAccessor(indices,'VEC4',5123,positions.count),wi=appendAccessor(weights,'VEC4',5126,positions.count);
for(const ai of [ji,wi])exported.bufferViews[exported.accessors[ai].bufferView].target=34962;
for(const primitive of exported.meshes[0].primitives){primitive.attributes.JOINTS_0=ji;primitive.attributes.WEIGHTS_0=wi;}
const inverse=new Float32Array(bones.length*16);mesh.skeleton.boneInverses.forEach((m,i)=>inverse.set(m.elements,i*16));
const ibi=appendAccessor(inverse,'MAT4',5126,bones.length);
exported.nodes=[{name:'Licensed_orca_metric_mesh',mesh:0,skin:0},...bones.map(b=>{const node={name:b.name,translation:b.position.toArray()};const children=b.children.filter(c=>c.isBone).map(c=>bones.indexOf(c)+1);if(children.length)node.children=children;return node;})];
exported.scenes=[{name:'Monarch_metric_rig_candidate',nodes:[0,1]}];exported.scene=0;
exported.skins=[{name:'Monarch_original_metric_skin',joints:bones.map((_,i)=>i+1),skeleton:1,inverseBindMatrices:ibi}];
const times=new Float32Array(145);for(let f=0;f<times.length;f++)times[f]=f/24;
const ti=appendAccessor(times,'SCALAR',5126,times.length,[0],[6]);const samplers=[],channels=[];
for(let i=0;i<bones.length;i++){
 const values=new Float32Array(times.length*4);
 for(let f=0;f<times.length;f++){pose(times[f]);values.set(bones[i].quaternion.toArray(),f*4);}
 const output=appendAccessor(values,'VEC4',5126,times.length);samplers.push({input:ti,output,interpolation:'LINEAR'});channels.push({sampler:i,target:{node:i+1,path:'rotation'}});
}
exported.animations=[{name:'Monarch_metric_swim_study_6s_NOT_biomechanics_approved',samplers,channels}];
exported.asset.extras={...exported.asset.extras,monarch_changes:'Original eight-bone metric skeleton and weights replace incompatible legacy skin; original source geometry, UVs, material and embedded images preserved. Original project-authored six-second motion clip. Not scientifically validated.',attribution:'Killer Whale by Abner Wu / Trouvaille, CC-BY-4.0. See accompanying LICENSE.md and ATTRIBUTION-ORCA.md.'};
binary=Buffer.concat([binary,Buffer.alloc((4-binary.length%4)%4)]);exported.buffers=[{byteLength:binary.length}];
function pack(doc,bytes){
 let text=Buffer.from(JSON.stringify(doc));text=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]);
 const h=Buffer.alloc(20);h.writeUInt32LE(0x46546c67,0);h.writeUInt32LE(2,4);h.writeUInt32LE(20+text.length+8+bytes.length,8);h.writeUInt32LE(text.length,12);h.writeUInt32LE(0x4e4f534a,16);
 const b=Buffer.alloc(8);b.writeUInt32LE(bytes.length,0);b.writeUInt32LE(0x004e4942,4);return Buffer.concat([h,text,b,bytes]);
}
const destination=path.join(base,'out/orca/orca_metric_rig.glb');fs.writeFileSync(destination,pack(exported,binary));
// Real reimport checks, with image decoding disabled in Node copy only.
const check=structuredClone(exported);check.materials=[{}];delete check.images;delete check.textures;delete check.samplers;
for(const m of check.meshes)for(const p of m.primitives)p.material=0;
const checkBytes=pack(check,binary);const loaded=await new GLTFLoader().parseAsync(checkBytes.buffer.slice(checkBytes.byteOffset,checkBytes.byteOffset+checkBytes.byteLength),'');
let imported;loaded.scene.traverse(o=>{if(o.isSkinnedMesh)imported=o;});
const mix=new THREE.AnimationMixer(loaded.scene);const act=mix.clipAction(loaded.animations[0]);act.setLoop(THREE.LoopOnce,1);act.clampWhenFinished=true;act.play();
let maxRoundtripError=0;const dense=[];
for(let f=0;f<144;f++){
 const time=f/24;mix.setTime(time);loaded.scene.updateMatrixWorld(true);imported.skeleton.update();const verts=[];
 const wanted=pose(time);for(let j=0;j<positions.count;j++){
  const v=imported.applyBoneTransform(j,new THREE.Vector3().fromBufferAttribute(imported.geometry.attributes.position,j));
  maxRoundtripError=Math.max(maxRoundtripError,v.distanceTo(new THREE.Vector3(...wanted[j])));verts.push(v.toArray());
 }
 dense.push({time,positions:verts});
}
if(maxRoundtripError>1e-4)throw Error('export roundtrip changed animation');
const roundtrip={type:'actual_animated_GLB_export_and_supported_loader_reimport',frames_evaluated:144,fps:24,clip_seconds:6,bones:imported.skeleton.bones.length,maximum_vertex_roundtrip_error:maxRoundtripError,geometry_preserved:true,source_image_buffer_views_preserved:exported.images.length,source_materials_preserved:exported.materials.length,independent_review:false,production_release:false};
fs.writeFileSync(path.join(base,'out/orca/metric_rig_roundtrip.json'),JSON.stringify(roundtrip,null,2)+'\n');
fs.writeFileSync(path.join(base,'out/orca/metric_rig_dense_poses.json'),JSON.stringify(dense));
console.log(JSON.stringify(roundtrip,null,2));
// Separate longer scene-study sampling; exported GLB/roundtrip scope remains six seconds.
const scenePoses=Array.from({length:150},(_,f)=>({time:f/24,positions:pose(f/24)}));
fs.writeFileSync(path.join(base,'out/orca/metric_rig_scene_poses.json'),JSON.stringify(scenePoses));
const farScenePoses=Array.from({length:150},(_,f)=>({time:f/24,phase_offset_seconds:.85,positions:pose(f/24+.85)}));
fs.writeFileSync(path.join(base,'out/orca/metric_rig_far_scene_poses.json'),JSON.stringify(farScenePoses));
