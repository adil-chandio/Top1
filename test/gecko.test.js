import test from 'node:test';
import assert from 'node:assert/strict';
import { contactEvents, digitSamples, geckoPose, release } from '../tools/gecko/motion.js';
import { soundtrackCue } from '../tools/soundtrack.mjs';

const separation = (a,b) => Math.hypot(...a.map((v,i)=>v-b[i]));
const close = (a,b,eps=1e-6) => assert.ok(Math.abs(a-b)<eps, `${a} vs ${b}`);

test('gecko climb reaches fixed footholds, with support through both diagonal phases', () => {
  let prev;
  for(let i=0; i<62*96; i++) {
    const {limb} = geckoPose(i/96);
    let supports=0;
    limb.forEach((l,j)=>{
      assert.ok(l.reachable);
      const bones=l.front ? [.685,.726] : [.726,.752];
      close(separation(l.shoulder,l.knee),bones[0]);
      close(separation(l.knee,l.wrist),bones[1]);
      assert.ok(l.at[2] >= 0);
      if (l.at[2]===0 && digitSamples(.52,l.curl).some(x=>x.contact)) supports++;
      if(l.planted && prev?.[j].planted) assert.deepEqual(l.at,prev[j].at);
    });
    assert.ok(supports>=2, `Support lost at ${i/96}s`);
    prev=limb;
  }
});

test('toe curls at constant centerline arc length; contact releases tip to base before palm lifts', () => {
  let before;
  for(let i=3400;i<4050;i+=2) {
    const {curl,palmLift}=release(i/100);
    const path=digitSamples(.614,curl*.914,1,72);
    const contacts=path.filter(x=>x.contact).map(x=>x.s);
    if (before) assert.deepEqual(before.slice(0,contacts.length),contacts);
    const spineZ=({s,z,height})=>z-height-.006-.043*(1-s)**5;
    let arc=0;
    for(let j=1;j<path.length;j++) arc+=Math.hypot(path[j].x-path[j-1].x,spineZ(path[j])-spineZ(path[j-1]));
    close(arc,.614);
    if(palmLift>1e-7) assert.equal(contacts.length,0);
    before=contacts;
  }
});

test('repo contact Foley is aligned to a real swing/stance crossing, not an arbitrary beat grid', () => {
  const events=contactEvents(62);
  assert.equal(events.length,28);
  for(const {t,foot} of events){
    assert.equal(geckoPose(t).limb[foot].planted,true);
    assert.equal(geckoPose(t-1/240).limb[foot].planted,false);
  }
  assert.ok(!events.some(({t})=>t>9.82&&t<48.92));
  assert.equal(soundtrackCue('tick',-.001,.23,164.81),0);
  assert.equal(soundtrackCue('tick',1.86,.23,164.81),0);
  assert.ok(Math.abs(soundtrackCue('tick',.0041,.23,164.81))>.006);
});

test('the private film edit has frame cuts and mechanism events without source audio in its timeline', async () => {
  const { loadGeckoEdit,readGeckoSrt,validateGeckoEdit } = await import('../tools/gecko/session.mjs');
  const cut=await loadGeckoEdit({from:new URL('../tools/gecko/edit.json',import.meta.url)});
  assert.equal(cut.frames,1488);assert.equal(cut.shots.length,22);assert.equal(cut.captions,undefined);
  assert.equal(cut.shots.findLast(s=>s.frame/24<=cut.marks.microContact).kind,'branched');
  assert.equal(cut.shots.findLast(s=>s.frame/24<=cut.marks.shear).kind,'shear');
  assert.equal(cut.shots.findLast(s=>s.frame/24<=cut.marks.footClear).kind,'peeled');
  assert.deepEqual(readGeckoSrt('1\r\n00:00:00,250 --> 00:00:02,400\r\nExample line\r\n'),[[.25,2.4,'Example line']]);
  assert.throws(()=>validateGeckoEdit({...cut,frames:1487}));
});

test('Premiere covers the full narration with 29 camera setups and one consistent support/release edit', async () => {
  const {loadGeckoEdit}=await import('../tools/gecko/session.mjs');
  const {setups}=await import('../tools/gecko/premiere/camera.js');
  const cut=await loadGeckoEdit({from:new URL('../tools/gecko/premiere/edit.json',import.meta.url)});
  assert.equal(cut.shots.length,29);assert.equal(Object.keys(setups).length,29);
  assert.ok(cut.shots.every(s=>setups[s.kind]));
  const at=t=>cut.shots.findLast(s=>s.frame<=cut.fps*t).kind;
  assert.equal(at(1.75),'grip-anchor');assert.equal(at(3.188),'step');
  assert.equal(at(cut.marks.microContact),'branched');assert.equal(at(cut.marks.shear),'shear');
  assert.equal(at(cut.marks.curlStart),'peel-wide'); assert.equal(at(cut.marks.footClear),'peeled');
  assert.equal(at(60.79),'hero-eye');
});

test('Premiere Foley keeps live pad transients on the existing footprint events', async () => {
  const {loadGeckoEdit}=await import('../tools/gecko/session.mjs');
  const {premiereCues}=await import('../tools/gecko/premiere/score.mjs');
  const cut=await loadGeckoEdit({from:new URL('../tools/gecko/premiere/edit.json',import.meta.url)});
  const cues=premiereCues(cut);
  assert.equal(cues.length,35);
  const plants=cues.filter(c=>c.role==='pad plant');
  const matched=new Set(contactEvents(cut.duration).map(e=>e.t));
  assert.ok(plants.length>15&&plants.every(c=>matched.has(c.t)));
  assert.ok(cues.every((c,i)=>c.t>=0&&c.t<cut.duration&&(!i||c.t>=cues[i-1].t)));
  assert.ok(cues.some(c=>c.role==='editorial close-contact accent'&&Math.abs(c.t-cut.marks.microContact)<1/cut.fps));
});

test('the modeled lamellar ellipses meet the contact plane without crossing it through the curl', () => {
  for(const length of [.276,.418,.514,.475,.344,.614]){
    const n=length===.614?60:24, ribs=length===.614?15:10;
    for(let phase=0;phase<=160;phase++){
      const path=digitSamples(length,phase/160,1,n);
      for(let j=0;j<ribs;j++){
        const u=.287+.604*j/(ribs-1),i=Math.min(n-1,Math.floor(u*n)),a=u*n-i;
        const at=(p)=>path[i][p]*(1-a)+path[i+1][p]*a;
        const ridge=.0096+.042*(1-u)**5, theta=at('roll'),cos=Math.cos(theta);
        const bottom=at('z')+cos*(-at('height')-.006-.043*(1-u)**5+ridge+.0011)
          -Math.hypot(ridge*cos,length/ribs*.213*Math.sin(theta));
        assert.ok(bottom>0);
        if(phase===0)assert.ok(bottom<.002);
      }
    }
  }
});
