// Authored climbing mechanics. Coordinates: +Y up the wall, +Z away from it.
// Qualitative animation, not a tendon, stress, or measured animal-gait model.
export const clamp = (x, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, x));
export const mix = (a, b, t) => a + (b - a) * t;
export const smooth = (x) => { const t = clamp(x); return t*t*(3-2*t); };
export const smoother = (x) => { const t = clamp(x); return t*t*t*(10+t*(-15+6*t)); };
export const between = (t, a, b) => smooth((t-a)/(b-a));
const add = (a, b) => a.map((x, i) => x + b[i]);
const sub = (a, b) => a.map((x, i) => x - b[i]);
const mul = (a, s) => a.map((x) => x*s);
const dot = (a, b) => a.reduce((n, x, i) => n + x*b[i], 0);
const norm = (a) => Math.hypot(...a);
const unit = (a) => mul(a, 1 / Math.max(1e-8,norm(a)));

export const DUTY = .70;
export const STRIDE = 1.115;
export const BODY_Y0 = -3.5;
// LF, RF, LH, RH. Diagonals alternate; the timing offsets avoid simultaneous
// four-foot release. At the end of each wide passage all four pads are down.
export const LIMBS = [
  { side:-1, front:true, phase:.00 }, { side:1, front:true, phase:.47 },
  { side:-1, front:false, phase:.54 }, { side:1, front:false, phase:.065 },
];
const TRACKS = [ { from:0, to:9.82, first:.11, last:3.105 }, { from:48.92,to:61.4,first:3.105,last:7.105 } ];

// Unit area ramped trapezoid integral. Body velocity goes to zero before the
// cutaway; the creature doesn't drift or freeze mid-air between environments.
function pace(u, ramp = .135) {
  u = clamp(u);
  if (u < ramp) return (u*u/(2*ramp))/(1-ramp);
  if (u > 1-ramp) return 1 - pace(1-u,ramp);
  return (u-ramp/2)/(1-ramp);
}
export function climbCycle(t) {
  let phase = TRACKS[0].first;
  for (const { from,to,first,last } of TRACKS) {
    if (t < from) break;
    phase = mix(first,last,pace((t-from)/(to-from)));
  }
  return phase;
}
export function stance(def, c) {
  const relative = c + def.phase, k = Math.floor(relative), phase = relative-k;
  const swing = smoother((phase - DUTY) / (1 - DUTY));
  const reach = def.front ? .42 : .39;
  const origin = BODY_Y0 + STRIDE * (k - def.phase) + (def.front ? .58 : -.84);
  const footprint = (n) => def.side * (def.front ? 1.11 : 1.18) + .14*Math.sin(n*.67+def.side*.6);
  const lift = .305*Math.sin(Math.PI*swing)**1.45;
  const at = [mix(footprint(k), footprint(k+1), swing) + def.side * .085*Math.sin(Math.PI*swing),origin+reach+STRIDE*swing,lift];
  const curl = between(phase,.606,.774) * (1 - between(phase,.832,.9998))*.90;
  const yaw = def.side * (def.front ? .61 : 1.28) + .09*Math.sin(Math.PI*swing);
  return { at, curl, yaw, planted: phase < DUTY, phase };
}

// Triangle IK in the plane of the two bones plus the intended bend direction.
export function solveJoint(root, foot, a, b, bend) {
  const delta = sub(foot,root), d = norm(delta), forward = unit(delta);
  const distance = clamp(d, Math.abs(a-b)+1e-6, a+b-1e-6);
  const parallel = (a*a - b*b + distance*distance) / (2*distance);
  const height = Math.sqrt(Math.max(0, a*a - parallel*parallel));
  const normal = unit(sub(bend,mul(forward,dot(bend,forward))));
  return { point: add(root,add(mul(forward,parallel),mul(normal,height))), reachable: Math.abs(d-distance) < 2e-6 };
}

export function geckoPose(t) {
  const c = climbCycle(t);
  const x = .067*Math.sin(c*Math.PI*2-.7)+.09*Math.sin(c*1.11);
  const y = BODY_Y0 + STRIDE*c;
  const z = .018*Math.sin(c*Math.PI*4+.3) + .008*Math.sin(t*2.66);
  const twist = .072*Math.sin(c*6.283-.5);
  const limb = LIMBS.map((def) => {
    const foot = stance(def,c);
    const p = def.front ? .76 : -.79;
    const shoulder = [x + def.side*(def.front?.36:.405) + twist*p, y+p, .49+z+def.side*.018*Math.sin(c*6.283)];
    const wrist = add(foot.at,[0,0,.085]);
    const lengths = def.front ? [.685,.726] : [.726,.752];
    const knee = solveJoint(shoulder,wrist,...lengths,[def.side*.86,def.front?-.57:.72,.27]);
    return { ...foot, shoulder,wrist,knee:knee.point,reachable:knee.reachable,front:def.front,side:def.side };
  });
  return { c,x,y,z,twist,limb };
}

export function digitProfile(s, breadth=1) {
  const pad = between(s,.244,.484) * (1-between(s,.861,.997));
  const tip = 1-.94*between(s,.941,1);
  return { width:breadth*(.031 + pad*.058 + .008*(1-s))*tip, height:(.018 + .013*pad + .025*(1-s)**3)*tip };
}

// A segment-integrated curl. Arc length of the centerline is preserved; the
// curled distal part moves away from the plane while the proximal pad holds.
// The scale/keratin layer adds small offsets outside this skeleton.
export function digitSamples(length, curl, breadth=1, count=28) {
  curl = clamp(curl);
  const front = mix(.985,.208,curl ** .65);
  const bend = 2.31*smooth(curl*1.37);
  const angle = (s) => bend * smooth((s-front)/(1-front));
  const res=[];
  let x=0,z=0;
  for (let i=0;i<=count;i++) {
    const s=i/count;
    if(i) { const theta=angle(s-.5/count); x+=length/count*Math.cos(theta); z+=length/count*Math.sin(theta); }
    const p=digitProfile(s,breadth), theta=angle(s);
    res.push({ s, x, z:z+p.height+.006+.043*(1-s)**5, roll:theta, ...p, contact:s>=.275&&s<=.927&&s<=front+.008 });
  }
  return res;
}

export function release(t, begin=34.96,end=38.86) {
  const curl = smoother((t-begin)/(end-begin));
  return { curl, palmLift:.22*between(t,end-.32,end+1.16) };
}

export function contactEvents(duration=62) {
  const events=[];
  const fps=240;
  let before=geckoPose(0).limb;
  for(let i=1;i<=Math.floor(duration*fps);i++) {
    const t=i/fps, after=geckoPose(t).limb;
    for(let j=0;j<after.length;j++) if(after[j].planted&&!before[j].planted) events.push({t,side:after[j].side,foot:j});
    before=after;
  }
  return events;
}
