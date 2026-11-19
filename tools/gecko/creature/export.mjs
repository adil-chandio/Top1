import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { poseAt, cameraAt, fps, frames, inFrame, outFrame, action } from './motion.js';

const path=resolve(process.argv[2]??'.cache/monarch-gecko/creature/poses/take.json');
await mkdir(dirname(path),{recursive:true});
const take=Array.from({length:frames},(_,i)=>({...poseAt(i/fps),camera:cameraAt(i/fps)}));
if(take.some((p)=>p.limbs.some((l)=>!l.reachable)))throw new Error('Proof has an unreachable stance');
await writeFile(path,JSON.stringify({fps,frames,inFrame,outFrame,action,take},(_,v)=>typeof v==='number'?Math.round(v*1e7)/1e7:v));
console.log(`Authored ${frames} frames at ${fps} fps, exact narration interval ${inFrame/fps}—${outFrame/fps} s → ${path}`);
