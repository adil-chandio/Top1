import test from 'node:test';
import assert from 'node:assert/strict';
import { naturalEdit, picturePlan, premiere } from '../tools/gecko/natural/edit.mjs';
import { lived, staged, liveCamera } from '../tools/gecko/natural/poses.mjs';
import { editionCues } from '../tools/gecko/natural/sound.mjs';
import { inFrame, outFrame, action } from '../tools/gecko/creature/motion.js';
import { loadGeckoEdit, validateGeckoEdit } from '../tools/gecko/session.mjs';

const cut=await naturalEdit(), edit=picturePlan(cut);
const dist=(a,b)=>Math.hypot(...a.map((v,j)=>v-b[j]));
const byKind=(kind)=>edit.entries.find(e=>e.kind===kind);
const length=s=>s.end-(s.first??s.frame);

test('new film keeps the original 62-second lock, changes wildlife, and preserves the scientific sequence',async()=>{
  const old=await loadGeckoEdit({from:premiere});
  assert.equal(cut.frames,1488);
  assert.equal(cut.voiceDuration,old.voiceDuration);
  assert.deepEqual(cut.marks,old.marks);
  assert.equal(validateGeckoEdit(cut),cut);
  assert.equal(edit.entries[0].frame,0);
  assert.equal(edit.entries.at(-1).end,1488);
  assert.equal(edit.entries.reduce((n,s)=>n+length(s),0),1488);
  assert.deepEqual(edit.entries.slice(0,3).map(s=>s.frame),[0,28,56]);
  for(const original of old.shots.filter(s=>['lamella','contact-ground','vanderwaals','shear','angles','recap-shear'].includes(s.kind))){
    const shot=byKind(original.kind);assert.equal(shot.frame,original.frame);assert.equal(shot.source,'science');
  }
  assert.equal(edit.spans.filter(s=>s.source==='trace').reduce((a,s)=>a+length(s),0),636);
  assert.deepEqual([byKind('creature-release').frame,byKind('creature-release').end],[inFrame,outFrame]);
  assert.equal(byKind('settled').end,byKind('replay').frame);
});

test('the new stride loads stable anchors and always leaves diagonal or three-plus support',()=>{
  let prior=lived(0),peels=0,swings=0;
  for(let f=0;f<cut.frames;f++){
    const p=lived(f/cut.fps), ground=p.limbs.filter(l=>l.planted);
    assert.ok(ground.length>=2);
    if(ground.length===2){
      assert.equal(ground[0].side,-ground[1].side);
      assert.notEqual(ground[0].front,ground[1].front);
    }
    for(const [j,l] of p.limbs.entries()){
      const old=prior.limbs[j];
      assert.ok(l.reachable);
      const [a,b]=l.bones;
      assert.ok(Math.abs(dist(l.shoulder,l.knee)-a)<1e-5);
      assert.ok(Math.abs(dist(l.knee,l.wrist)-b)<1e-5);
      if(l.planted&&old.planted)assert.ok(dist(l.at,old.at)<1e-6);
      if(l.airborne){
        swings++;
        assert.ok(l.at[2]>=0);
        if(old.planted){assert.ok(old.curl>.8);peels++;}
      }
      assert.ok(l.digits.every(d=>d.points.every(q=>q[1]>=0)));
    }
    prior=p;
  }
  assert.ok(peels>=25&&swings>=300);
});

test('all traced cameras and the slow-angle pads stay on the planned side of the window',()=>{
  for(const s of edit.entries.filter(s=>s.source==='trace'))for(let f=s.frame;f<s.end;f++){
    const u=(f-s.frame)/length(s), q=staged(s.kind,f,u), v=q.camera??liveCamera(q,s.kind,u);
    assert.ok(v.place.every(Number.isFinite));
    assert.ok(v.place[2]*(v.side==='beneath'?-1:1)>1e-2);
    assert.ok(v.focal>=29&&v.aperture>=5);
    assert.ok(q.limbs.every(l=>l.reachable));
  }
  const s=byKind('replay'), first=staged(s.kind,s.frame,0),middle=staged(s.kind,s.frame+50,.575),end=staged(s.kind,s.end-1,.997);
  assert.ok(first.limbs[1].curl<middle.limbs[1].curl&&end.limbs[1].curl>.99);
  assert.ok(middle.limbs[1].at[2]<end.limbs[1].at[2]);
});

test('new Foley lands with real v2 edit beats and never assigns impacts to microscopic contact',()=>{
  const events=editionCues(cut), pads=events.filter(e=>e.kind==='pad');
  assert.ok(events.every((e,i)=>e.t>=0&&e.t<62&&(!i||events[i-1].t<=e.t)));
  assert.ok(pads.length>=19);
  for(const p of pads){
    assert.ok(Math.abs(p.touchdown-p.t)<=1/cut.fps);
    assert.notEqual(edit.entries.findLast(s=>s.frame<=p.touchdown*cut.fps).source,'science');
  }
  assert.equal(pads.find(e=>e.role.includes('right forepad')).touchdown,inFrame/cut.fps+action.plant);
  assert.ok(events.find(e=>e.role.includes('wrist leaves')).t>cut.marks.digitRelease);
});
