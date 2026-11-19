import { REFLECTOR, REFLECTOR_BEATS as B } from '../src/reflector.js';

// Unity-gain limiter with headroom for AAC reconstruction. The mono voice
// is centered in stereo; avoid FFmpeg's default limiter make-up gain.
export function reflectorMix(fx = 1, voice = 2) {
  return `[${fx}:a]volume=0.78[fx];[${voice}:a]pan=stereo|FL=c0|FR=c0,volume=0.91[vo];[fx][vo]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.80:level=0:latency=1[mix]`;
}

const RATE = 48000;
const TAU = 2 * Math.PI;
const bell = (t, hz, fall, amp) => amp*Math.exp(-fall*t)*Math.sin(TAU*hz*t);
const unit = (x) => Math.max(0,Math.min(1,x));
const ease = (x) => { const t=unit(x); return t*t*(3-2*t); };

function stereoWav(left,right) {
  const out=Buffer.allocUnsafe(44+left.length*4);
  out.write('RIFF',0);out.writeUInt32LE(out.length-8,4);out.write('WAVEfmt ',8);
  out.writeUInt32LE(16,16);out.writeUInt16LE(1,20);out.writeUInt16LE(2,22);
  out.writeUInt32LE(RATE,24);out.writeUInt32LE(RATE*4,28);out.writeUInt16LE(4,32);out.writeUInt16LE(16,34);
  out.write('data',36);out.writeUInt32LE(left.length*4,40);
  for(let i=0;i<left.length;i++) {
    out.writeInt16LE(Math.round(Math.max(-1,Math.min(1,left[i]))*32767),44+i*4);
    out.writeInt16LE(Math.round(Math.max(-1,Math.min(1,right[i]))*32767),46+i*4);
  }
  return out;
}

export function reflectorScore(duration=REFLECTOR.duration) {
  const n=Math.round(duration*RATE), L=new Float32Array(n), R=new Float32Array(n);
  let state=103532, low=0, grit=0;
  const noise=()=>((state=(Math.imul(state,1664525)+1013904223)>>>0)/2147483648)-1;
  // Quiet tunnel air and a restrained optical-bench harmonic bed. No library loops.
  for(let s=0;s<n;s++) {
    const t=s/RATE, fade=ease(t/.39)*ease((duration-t)/.63);
    const road=1-ease((t-13.72)/.48)+ease((t-38.53)/.68);
    const voidBeat=1-.77*ease((t-42.69)/.53)*(1-ease((t-45.55)/.54));
    low=.978*low+.022*noise();grit=.864*grit+.136*noise();
    const modulation=.68+.32*Math.sin(TAU*.178*t);
    const sub=.035*Math.sin(TAU*46.249*t + .16*Math.sin(t*.78));
    const bench=.015*Math.sin(TAU*138.591*t+ .44*Math.sin(t*.8))+.009*Math.sin(TAU*184.996*t + .64*Math.sin(t*.39));
    const passing=road*(.065*low+.019*grit)+(.013*low+.010*grit);
    const both=fade*voidBeat*(sub*(.68+.32*road)+bench*modulation+passing);
    const side=fade*voidBeat*.009*Math.sin(TAU*92.499*t+.49*Math.sin(t));
    L[s]=both+side;R[s]=both-side;
  }
  const lay=(at,length,pan,generator)=>{
    const from=Math.round(at*RATE), to=Math.min(n,from+Math.round(length*RATE));
    const l=Math.sqrt(.5*(1-pan)),r=Math.sqrt(.5*(1+pan));
    for(let i=from;i<to;i++) {
      if(i<0) continue;
      const a=(i-from)/RATE,s=generator(a,noise());
      L[i]+=l*s;R[i]+=r*s;
    }
  };
  for(const [i,at] of [B.hookOn,B.lampOn,B.lampOff,B.payoffOn].entries()) {
    lay(at,.37,i===2?-.31:-.18,(t,w)=>attack(t)*(bell(t,82,10,.20)+bell(t,460,31,.088)+w*.121*Math.exp(-70*t)));
    if(i!==2) lay(at+.048,.62,.20,(t,w)=>ease(t/.10)*(1-ease(t/.62))*(bell(t,217.9,4.1,.038)+w*.012));
  }
  const beats=[B.mirrorHit,...B.hits,B.rayExit];
  beats.forEach((at,i)=>lay(at,.78,(i%3-1)*.35,(t,w)=> attack(t)*(bell(t,308+i*61,15,.098)+bell(t,666+i*121,14,.048)+w*.081*Math.exp(-36*t))));
  for(const at of [1.48,4.02,8.75,13.80,19.42,22.07,24.31,27.16,35.28,38.73,42.07,45.59]) {
    let tone=0;
    lay(at-.072,.32,.2,(t,w)=>{tone=.78*tone+.22*w;return tone*.084*Math.sin(Math.PI*t/.32)**2+bell(t,74,17,.054)*ease(t/.05);});
  }
  lay(19.77,1.30,-.21,(t,w)=>ease(t/.31)*(1-ease((t-.66)/.64))*(bell(t,128,1.7,.06)+w*.020));
  lay(47.04,2.55,.06,(t)=>ease(t/.19)*(1-ease((t-1.3)/1.25))*(bell(t,277.183,1.0,.073)+bell(t,415.305,.93,.052)+bell(t,554.365,1.21,.047)));
  return stereoWav(L,R);
}

const attack = (t) => ease(t/.007);
