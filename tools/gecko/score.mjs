import { soundtrackCue } from '../soundtrack.mjs';
import { between, clamp, contactEvents } from './motion.js';

const RATE = 48000;
const TAU = 2 * Math.PI;
const sin = (t,hz,w=0)=>Math.sin(TAU*t*hz+w);
const pulse = (t,a,b,fade=.4) => between(t,a,a+fade)*(1-between(t,b-fade,b));

export function geckoCues(cut) {
  const at = (id) => cut.shots.find(({kind})=>kind===id).frame / cut.fps;
  const cues = [];
  const add = (time,kind,gain,pan,role,pitch=164.81) => cues.push({time,kind,gain,pan,role,pitch});
  for(const {t,side,foot} of contactEvents(cut.duration)) {
    if (t >= at('foot') && t < at('walk-out') || t >= at('recap-contact') && t < at('hero')) continue;
    const close=t>=at('step')&&t<at('climb')&&foot===0;
    add(t,'tick',close?.94:foot<2?.47:.33,side*.59,'planted pad');
  }
  for (const [id,gain,pan] of [['foot',.68,-.22],['setae',1.02,.26],['vanderwaals',.54,-.30],['angles',.78,.22],['walk-out',.65,-.18]]) {
    add(at(id)-.60,'air',gain,pan,'scale transition');
  }
  add(cut.marks.microContact-.032,'glass',.32,-.18,'editorial contact cue',174.61);
  add(cut.marks.shear-.026,'glass',.24,.25,'loading vector cue',146.83);
  add(cut.marks.curlStart+.35,'air',.57,.32,'distal roll');
  add(cut.marks.footClear-.61,'air',.65,-.23,'pad clearance');
  add(at('replay')-.599,'air',.77,-.31,'replay');
  add(53.59-.026,'glass',.33,-.18,'recap contact cue',174.61);
  add(54.22-.03,'glass',.23,.25,'recap loading cue',146.83);
  add(56.05,'air',.57,.28,'recap curl');
  add(at('hero')-.6,'air',.77,.19,'return to wall');
  return cues.sort((a,b)=>a.time-b.time);
}

export function geckoScore(cut) {
  const f = Math.round(cut.duration * RATE);
  const wav = Buffer.alloc(44+f*4);
  wav.write('RIFF',0);wav.writeUInt32LE(wav.length-8,4);wav.write('WAVEfmt ',8);
  wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);wav.writeUInt16LE(2,22);
  wav.writeUInt32LE(RATE,24);wav.writeUInt32LE(RATE*4,28);wav.writeUInt16LE(4,32);wav.writeUInt16LE(16,34);
  wav.write('data',36);wav.writeUInt32LE(f*4,40);
  const curves = geckoCues(cut).map(c=>({...c,l:Math.sqrt((1-c.pan)*.5),r:Math.sqrt((1+c.pan)*.5)}));
  let state=0xd0ed7398, room=0, med=0, slow=0, head=0, tail=0;
  for(let i=0;i<f;i++) {
    const t=i/RATE;
    state=(Math.imul(state,1664525)+1013904223)>>>0;
    const white=state/2147483648-1;
    room+=.018*(white-room);med+=.142*(white-med);slow+=.0008*(white-slow);
    const field=pulse(t,10.35,48.99,1.12);
    const space=1-field*.64;
    const drift=.86+.14*sin(t,.173);
    const finish=between(t,57.53,61.12);
    const peel = 1-.45*pulse(t,34.66,40.66,.56);
    const root=.029*sin(t,48.999,.16*sin(t,.11));
    const roomTone=.027*room+.066*slow+.013*med;
    const carrier=(.009+.004*field)*sin(t,146.997,.23*sin(t,.159)) + (.009+.012*finish)*sin(t,195.998,.23*sin(t,.182));
    const suspense=.009*pulse(t,20.25,33.82,2.17)*sin(t,155.56,.24*sin(t,.296));
    const bloom=finish*(.020*sin(t,97.999)+.018*sin(t,246.942,.19*sin(t,.124)));
    const center=(root+carrier+roomTone*space+suspense+bloom)*drift*peel;
    const spread=.011*sin(t,195.998,.71+.54*sin(t,.114))*drift + .008*(med-room)*space;
    let l=center+spread,r=center-spread;
    while(tail<curves.length&&curves[tail].time<=t)tail++;
    while(head<tail&&curves[head].time<t-1.85)head++;
    for(let n=head;n<tail;n++) {
      const e=curves[n],age=t-e.time,k=(e.kind==='air'?med-room:med);
      // A dry pad/claw touch is a very short, quiet tick, not a suction pop.
      const gain=e.kind==='tick'?Math.exp(-8*age):1;
      const fx= soundtrackCue(e.kind,age,k,e.pitch)*e.gain*gain;
      l+=fx*e.l;r+=fx*e.r;
    }
    const fade=between(t,0,.38)*(1-between(t,61.03,cut.duration));
    wav.writeInt16LE(Math.round(clamp(l*fade,-1,1)*32767),44+i*4);
    wav.writeInt16LE(Math.round(clamp(r*fade,-1,1)*32767),46+i*4);
  }
  return wav;
}

export function mixFilters(duration, gain=1.18) {
  return `[0:a]aresample=48000,highpass=f=47,pan=stereo|FL=c0|FR=c0,volume=${gain},apad=whole_dur=${duration},asplit=2[voice][key];`+
    `[1:a]volume=1.19[bed];[bed][key]sidechaincompress=threshold=0.041:ratio=3:attack=13:release=260:link=average[duck];`+
    `[voice][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.785:level=0:latency=1,atrim=duration=${duration}[mix]`;
}
