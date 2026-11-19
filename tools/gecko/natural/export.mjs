import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import { naturalEdit, picturePlan } from './edit.mjs';
import { staged, liveCamera } from './poses.mjs';
import { inFrame, outFrame, poseAt, cameraAt } from '../creature/motion.js';
const dest=resolve(process.argv[2]??'.cache/monarch-gecko/natural/work');
await mkdir(dest,{recursive:true});
const cut=await naturalEdit(), plan=picturePlan(cut);
const take=[];
for(const s of plan.entries.filter(s=>s.source==='trace'))for(let frame=s.frame;frame<s.end;frame++){
  const u=(frame-s.frame)/(s.end-s.frame);
  const p=staged(s.kind,frame,u);
  assert.ok(p.limbs.every(l=>l.reachable),`${s.kind} has an unreachable limb at ${frame}`);
  const camera=p.camera??liveCamera(p,s.kind,u);
  take.push({...p,camera,frame,shot:s.kind});
}
const parts=[];
// Frame ranges may cross from one consecutive camera setup into the next,
// never across an insertion. A stable grouping makes retries shard-specific.
const limit=+(process.env.NATURAL_PACKET??36);
for(const span of plan.spans.filter(s=>s.source==='trace')) {
  const count=span.end-span.first,n=Math.ceil(count/limit);
  for(let i=0;i<n;i++){
    const first=span.first+Math.round(count*i/n),end=span.first+Math.round(count*(i+1)/n);
    parts.push({first,end});
  }
}
assert.equal(take.length,636);
await writeFile(`${dest}/edit.json`,JSON.stringify(cut,null,2)+'\n');
await writeFile(`${dest}/plan.json`,JSON.stringify({...plan,fps:cut.fps,frames:cut.frames,inFrame,outFrame,parts},null,2)+'\n');
await writeFile(`${dest}/take.json`,JSON.stringify({fps:cut.fps,frames:cut.frames,take},(_,v)=>typeof v==='number'?Math.round(v*1e6)/1e6:v));
// The last five continuity frames match the proof's bind, lens and lighting.
// Continue its breathing and tail interpolation rather than holding a still.
if(process.env.GECKO_SETTLE==='1'){
  const existing=JSON.parse(await readFile(process.env.GECKO_PROOF_POSES??'.cache/monarch-gecko/creature/poses/take.json','utf8'));
  const n=plan.entries.find(s=>s.source==='settle').end-outFrame;
  for(let j=0;j<n;j++){
    const i=existing.frames+j,t=i/cut.fps;
    existing.take.push({...poseAt(t),t,camera:cameraAt(t)});
  }
  existing.frames+=n;
  await writeFile(`${dest}/settle.json`,JSON.stringify(existing,(_,v)=>typeof v==='number'?Math.round(v*1e7)/1e7:v));
}
console.log(`Full ${cut.frames}-frame cut; ${take.length} newly traced frames across ${parts.length} packets. Proof ${inFrame}–${outFrame}; retained illustration intervals are indexed separately.`);
