import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fps, inFrame, outFrame, frames, action, poseAt, cameraAt, toesAt } from '../tools/gecko/creature/motion.js';

const corr=(u,v)=>Math.hypot(...u.map((n,i)=>n-v[i]));
const count=(q)=>q.digits.reduce((n,d)=>n+d.points.filter(p=>p[5]).length,0);
const held=poseAt(action.plant);

test('creature proof keeps three exact anchors; every joint reaches through the transfer and peel',()=>{
  for(let n=0;n<=frames*4;n++){
    const t=n/(fps*4);const a=poseAt(t);
    assert.ok(a.limbs.filter(l=>l.planted).length>=3);
    a.limbs.forEach((leg,i)=>{
      assert.ok(leg.reachable,`${t}, foot ${i}`);
      assert.ok(Math.abs(corr(leg.shoulder,leg.knee)-leg.bones[0])<2e-6);
      assert.ok(Math.abs(corr(leg.knee,leg.wrist)-leg.bones[1])<2e-6);
      assert.ok(leg.at[2]>=0);
      if(i!==1||t>=action.plant&&t<=action.free){
        assert.deepEqual(leg.at,held.limbs[i].at);
        assert.equal(leg.yaw,held.limbs[i].yaw);
      }
    });
  }
  assert.ok(poseAt(1.82).x>0);
  assert.ok(poseAt(action.peel).x<-.1);
  assert.ok(poseAt(action.wristClear).limbs[1].at[2]>.2);
});

test('all five distal edges move back along the tip-to-base contact prefix before the palm moves',()=>{
  let previous=count(held.limbs[1]);
  assert.ok(previous>120);
  for(let i=0;i<=340;i++){
    const t=action.peel+(action.wristClear-action.peel)*i/340;
    const foot=poseAt(t).limbs[1];const n=count(foot);
    assert.ok(n<=previous);previous=n;
    for(const d of foot.digits){
      const cs=d.points.map((p,i)=>p[5]?i:null).filter(x=>x!==null);
      assert.ok(!cs.length || cs[0]===10);
      assert.ok(cs.every((s,j)=>!j||s===cs[j-1]+1));
      const len=d.points.slice(1).reduce((sum,p,k)=>sum+Math.hypot(p[0]-d.points[k][0],p[1]-d.points[k][1]),0);
      assert.ok([.254,.348,.456,.414,.302].some(x=>Math.abs(x-len)<1e-8));
    }
    if(foot.at[2]>1e-9)assert.equal(n,0);
  }
  assert.equal(previous,0);
  assert.equal(toesAt(.418,1).at(-1)[5],0);
});

test('single lens move stays on one side of the dry pane and uses the locked v2 interval',()=>{
  assert.equal(inFrame,774);assert.equal(outFrame,982);assert.equal(frames,208);
  assert.equal(inFrame/fps+action.peel,34.96);
  assert.equal(inFrame/fps+action.free,38.86);
  assert.equal(inFrame/fps+action.wristClear,39.95);
  for(let i=0;i<frames;i++){
    const p=cameraAt(i/fps);assert.ok(p.place[2]>1.5&&p.aim[2]>0);
    assert.ok(p.focal>=40&&p.focal<60);
    if(i)assert.ok(corr(p.place,cameraAt((i-1)/fps).place)<.038);
  }
});
