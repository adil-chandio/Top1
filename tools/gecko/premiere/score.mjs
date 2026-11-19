import { soundtrackCue } from '../../soundtrack.mjs';
import { between, clamp, contactEvents } from '../motion.js';

const hz=48000, tau=2*Math.PI;
const sin=(phase)=>Math.sin(tau*phase);
const note=(midi)=>440*2**((midi-69)/12);
const curve=(x)=>clamp(x)**2*(3-2*clamp(x));
const window=(t,d,a,b)=>curve(t/a)*curve((d-t)/b);

// Commission-style original score: D minor, with a short borrowed luminous
// sixth in the reveal. Tempo is a guide, not a quantizer for the real Foley.
const phrases=[
  {from:0,to:5.1,low:38,notes:[50,53,57,64],drive:.48},
  {from:5.0,to:10.61,low:36,notes:[48,55,57,64],drive:.74},
  {from:10.54,to:16.24,low:41,notes:[53,57,60,64],drive:.67},
  {from:16.13,to:22.34,low:38,notes:[50,57,60,64],drive:.55},
  {from:22.26,to:27.34,low:43,notes:[55,58,62,65],drive:.52},
  {from:27.17,to:34.28,low:33,notes:[45,52,55,61],drive:.82},
  {from:34.15,to:40.61,low:38,notes:[50,53,57,62],drive:.32},
  {from:40.53,to:45.01,low:34,notes:[46,53,57,60],drive:.49},
  {from:44.90,to:49.02,low:33,notes:[45,52,58,62],drive:.62},
  {from:48.87,to:52.67,low:36,notes:[48,55,60,64],drive:.81},
  {from:52.55,to:57.72,low:38,notes:[50,53,57,64],drive:.73},
  {from:57.54,to:62.0,low:38,notes:[50,57,59,64],drive:.91},
];

// A hand-ridden fader gives the score room in the longer acoustic gaps. All
// windows end before the next syllable; the narration itself never moves.
const spaces=[[2.43,2.79],[4.91,5.45],[10.16,10.71],[15.80,16.19],[20.06,20.52],[27.08,27.39],
  [34.02,34.37],[40.79,41.27],[44.68,45.10],[48.84,49.21],[52.43,52.96],[60.47,61.83]];

export function premiereCues(cut) {
  const shot=(id)=>cut.shots.find(s=>s.kind===id).frame/cut.fps;
  const cues=[];
  const add=(t,kind,gain,pan,role,pitch=174.61)=>cues.push({t,kind,gain,pan,role,pitch});
  for(const {t,foot,side} of contactEvents(cut.duration)) {
    const live=(t<shot('foot') || (t>shot('walk-out')&&t<shot('recap-contact')) || t>=shot('hero'));
    if(!live) continue;
    const close=t>shot('grip-anchor')&&t<shot('climb')&&foot===0 || t>=shot('no-yank')&&t<shot('recap-contact');
    add(t,'tick',close?.79:(foot<2?.41:.31), side*(close?.36:.57),'pad plant');
  }
  for(const [kind,gain,pan] of [['through',.61,-.32],['foot',.74,.25],['setae',1.02,.36],['vanderwaals',.56,-.27],['replay',.69,.27],['angles',.71,-.22],['walk-out',.60,.37],['hero',.67,-.28]]) {
    add(shot(kind)-.60,'air',gain,pan,'perspective change');
  }
  add(cut.marks.microContact-.03,'glass',.40,-.20,'editorial close-contact accent',207.652);
  add(cut.marks.shear-.041,'glass',.25,-.07,'parallel load graphic',146.832);
  add(35.75-.57,'air',.65,.27,'distal peel');
  add(cut.marks.footClear-.60,'air',.73,-.18,'palm clearance');
  add(53.59-.033,'glass',.30,-.20,'recap: close contact',196);
  add(54.22-.038,'glass',.25,.24,'recap: load',155.564);
  add(56.11,'air',.54,.31,'recap: roll');
  return cues.sort((a,b)=>a.t-b.t);
}

function writer(n) {
  const wav=Buffer.alloc(44+n*4);
  wav.write('RIFF');wav.writeUInt32LE(wav.length-8,4);wav.write('WAVEfmt ',8);
  wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);wav.writeUInt16LE(2,22);wav.writeUInt32LE(hz,24);
  wav.writeUInt32LE(hz*4,28);wav.writeUInt16LE(4,32);wav.writeUInt16LE(16,34);wav.write('data',36);wav.writeUInt32LE(n*4,40);
  return wav;
}
const add={
  pad:(a,h,s)=>{
    const w=sin(a*.24+s)*.028+sin(a*.084+s*.54)*.078;
    return .60*sin(a*h+w)+.20*sin(a*h*2.002+w*.7)+.12*sin(a*h*3+w*.31)+.04*sin(a*h*4.007)+.015*sin(a*h*5.003);
  },
  pluck:(a,h,s)=>{
    const bend=Math.exp(-38*a)*.22;
    return Math.exp(-3.16*a)*.76*sin(h*a+.075*expEdge(a))*curve(a/.007) + .18*sin(2.007*h*a+bend+s)*Math.exp(-8.2*a)*curve(a/.004) + .091*sin(3.997*h*a+s*.2)*Math.exp(-15.5*a)*curve(a/.003);
  },
  bell:(a,h,s)=>curve(a/.016)*(.67*sin(a*h)*Math.exp(-2.95*a)+.21*sin(a*h*2.008+s)*Math.exp(-4.79*a)+.09*sin(a*h*4.37)*Math.exp(-11.5*a)),
  pulse:(a,h)=>curve(a/.025)*Math.exp(-4.4*a)*(.7*sin(a*h+.23*expEdge(a))+.21*sin(a*h*2+.08)+.09*sin(a*h*3)),
};
const expEdge=(t)=>1-Math.exp(-19*t);
export function buildPremiereScore(cut,{cues,creature=false}={}) {
  const n=Math.round(cut.duration*hz), L=new Float32Array(n), R=new Float32Array(n), FL=new Float32Array(n), FR=new Float32Array(n);
  const voices=[];
  const place=(t,sec,kind,midi,gain,pan=0,attack=.04,decay=.15,seed=.8)=>voices.push({t,sec,kind,f:note(midi),gain,pan,attack,decay,seed});
  phrases.forEach(({from,to,low,notes,drive},i)=>{
    if(creature)drive*=i===6?.79:i===0?1.10:1.00;
    const len=to-from;
    place(from,len,'pad',low,.065*drive,-.04,.69,.94,.661*i);
    notes.forEach((m,j)=>place(from+j*.034,len-j*.034,'pad',m,.023+.007*(j===1),j*.36-.56,1.2,1.13,.216*(i+j+1)));
    const eighth=60/105/2;
    const anchor=from+.19+(i%3)*.05;
    for(let j=0;anchor+eighth*j<to-.19;j++){
      const pattern=j%12;
      const dark=i===6 || i===3;
      if([0,3,7,10].includes(pattern)&&(!dark||pattern===3)) {
        const pitch=notes[[0,2,1,3][[0,3,7,10].indexOf(pattern)]]+(pattern===10?12:0);
        place(anchor+eighth*j,1.26,'pluck',pitch,(pattern===0?.044:.029)*drive,pattern%2?.40:-.36,.007,.26,.17*(i+1));
      }
      if(pattern===0 || pattern===6&&drive>.6)place(anchor+eighth*j,.64,'pulse',low-2, .035*drive,-.02,.018,.12);
    }
  });
  // A three-note signature is hinted at in the hook and resolves after the
  // final line. These quieter gestures occupy gaps or stay behind speech.
  for(const [t,m,g,p] of [[.016,74,.075,.18],[.195,81,.046,-.41],[2.36,77,.034,.43],[4.94,76,.060,-.16],[10.10,72,.066,-.23],[15.81,69,.054,.32],[20.12,74,.044,.25],[26.99,77,.045,.40],[34.035,73,.049,-.40],[40.71,77,.044,.36],[48.86,76,.050,.44],[52.36,74,.053,-.32],[60.36,74,.062,-.32],[60.67,81,.063,.30],[61.08,83,.051,.12]])
    place(t,Math.min(2.23,62-t),'bell',m,g,p,.020,.32,.23+m*.016);
  if(creature){
    // A spare bowed answer in the wildlife chapter and a shorter acoustic
    // window around the actual three-support transfer. The bed stays VO-led.
    for(const [t,f,m,g,p] of [[.014,.70,62,.045,-.21],[1.08,1.38,69,.024,.23],[2.295,.58,50,.061,-.04],
      [10.12,1.28,67,.017,.31],[32.28,2.18,50,.029,-.25],[33.28,1.76,57,.025,.20],
      [38.55,1.39,62,.034,.21],[40.57,1.45,65,.030,-.31],[48.88,1.63,52,.052,-.21],
      [60.33,1.65,62,.065,-.32],[60.66,1.34,74,.054,.32]])place(t,f,t<2.5||t>=60.0?'pluck':'pad',m,g,p,.037,.251,t*.161);
  }
  for(const v of voices) {
    const i0=Math.round(v.t*hz),end=Math.min(n,i0+Math.round(v.sec*hz));
    const l=Math.sqrt(.5*(1-v.pan))*v.gain,r=Math.sqrt(.5*(1+v.pan))*v.gain;
    for(let i=i0;i<end;i++) {
      const a=(i-i0)/hz;
      const envelope=window(a,v.sec,v.attack,v.decay);
      const val=envelope*add[v.kind](a,v.f,v.seed);
      L[i]+=l*val;R[i]+=r*val;
    }
  }
  const cs=cues??premiereCues(cut);
  let seed=0xa548eb, warm=0, fast=0, room=0, first=0,last=0;
  for(let i=0;i<n;i++) {
    const t=i/hz;
    seed=(Math.imul(seed,1664525)+1013904223)>>>0;
    const white=seed/2147483648-1;
    fast+=.21*(white-fast);warm+=.023*(white-warm);room+=.003*(white-room);
    // Air changes perspective with the edit. No simulated liquid, suction,
    // body impact, or loud sounds from invisible microscopic interactions.
    const interior=between(t,10.28,11.08)*(1-between(t,48.93,49.31));
    const night=1-interior*.70;
    let ml=(warm*.029+room*.020)*night+(fast-warm)*.008;
    let mr=(warm*.022+room*.020)*night-(fast-warm)*.009;
    while(last<cs.length&&cs[last].t<=t)last++;
    while(first<last&&cs[first].t<=t-1.85)first++;
    for(let k=first;k<last;k++){
      const c=cs[k],a=t-c.t;
      let s=soundtrackCue(c.kind,a,c.kind==='air'?fast-warm:warm,c.pitch);
      if(c.kind==='tick')s=s*.78+curve(a/.004)*Math.exp(-42*a)*(.030*sin(a*201)+.055*(fast-warm));
      if(c.kind==='pad')s=curve(a/.0035)*Math.exp(-a*37)*(.154*(fast-warm)+.039*sin(a*229)+.014*sin(a*607));
      if(c.kind==='brush')s=window(a,c.length,.09,.13)*((fast-warm)*.084+warm*.095+room*.021);
      const l=Math.sqrt(.5*(1-c.pan))*c.gain,r=Math.sqrt(.5*(1+c.pan))*c.gain;
      ml+=s*l;mr+=s*r;
    }
    // Short fabric/glass tail rather than a literal microscopic pop.
    const tailL=i>1176?FL[i-1176]*.12:0,tailR=i>1728?FR[i-1728]*.10:0;
    FL[i]=ml+tailR;FR[i]=mr+tailL;
  }
  const music=writer(n), foley=writer(n);
  let wetL=0,wetR=0,faderIndex=0;
  const read=(arr,i)=>i>=0?arr[i]:0;
  for(let i=0;i<n;i++) {
    const t=i/hz, end=1-between(t,61.09,62);
    const roomL=read(R,i-2003)*.153+read(L,i-5177)*.107+read(R,i-11393)*.078+read(L,i-18419)*.034;
    const roomR=read(L,i-2617)*.149+read(R,i-6127)*.119+read(L,i-13801)*.061+read(R,i-19991)*.035;
    wetL+=(roomL-wetL)*.097;wetR+=(roomR-wetR)*.097;
    const reveal=1-.41*between(t,34.04,35.07)*(1-between(t,39.89,41.48));
    while(faderIndex<spaces.length&&t>spaces[faderIndex][1])faderIndex++;
    const gap=spaces[faderIndex];
    const lift=gap&&t>=gap[0]?window(t-gap[0],gap[1]-gap[0],.13,.123):0;
    // A brief hush on entry to the continuous take protects the soft end of
    // the preceding line and reveals the dry plant without a big score hit.
    const focus=creature?1-.64*between(t,32.08,32.215)*(1-between(t,32.51,32.73)):1;
    const bed=end*reveal*focus*(1+.52*lift);
    for(const [wav,left,right] of [[music,(L[i]+wetL)*bed,(R[i]+wetR)*bed],[foley,FL[i]*end,FR[i]*end]]) {
      wav.writeInt16LE(Math.round(clamp(left,-1,1)*32767),44+i*4);
      wav.writeInt16LE(Math.round(clamp(right,-1,1)*32767),46+i*4);
    }
  }
  return {music,foley,cues:cs};
}
