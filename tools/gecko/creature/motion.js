import { between, clamp, mix, smooth, smoother, solveJoint } from '../motion.js';

// Coordinate frame shared with the main film: x across the pane, y up,
// z away from the pane. Authored anatomical staging, not a force measurement.
export const fps = 24;
export const inFrame = 774;
export const outFrame = 982;
export const frames = outFrame - inFrame;
export const action = Object.freeze({ plant: 17 / fps, transfer: 2.71, peel: 34.96 - inFrame / fps,
  free: 38.86 - inFrame / fps, wristClear: 39.95 - inFrame / fps });
const still = [ [-1.085,1.345,0], null, [-1.17,-.96,0], [1.16,-1.09,0] ];
const lengths = [ .254,.348,.456,.414,.302 ];
const angles = [ -1.08,-.57,-.102,.378,.89 ];
export const rings = 40;

// x, y, z, head turn, head lift, shoulder twist, body roll. Use position holds
// and two distinct transfers, before and after loading the new footprint.
const bodyKeys = [
  [0,-.106,-.204,-.015,.125,.020,-.038,-.021],
  [.71,-.138,-.112,-.018,.238,.026,-.027,-.046],
  [1.81,.079,.243,-.063,.18,.017,.077,.085],
  [2.02,.083,.280,-.071,.16,.032,.063,.094],
  [2.71,-.137,.319,-.033,.232,.056,-.043,-.065],
  [5.95,-.154,.351,-.027,.188,.042,-.045,-.056],
  [6.61,-.164,.349,-.023,.186,.031,-.044,-.061],
  [7.70,-.181,.388,.001,.225,.047,-.055,-.073],
  [frames/fps,-.182,.396,.000,.25,.057,-.061,-.071],
];
function bodyAt(t){
  const i=bodyKeys.findIndex((k)=>k[0]>t);
  if(i<1)return bodyKeys.at(i===0?0:-1).slice(1);
  const a=bodyKeys[i-1],b=bodyKeys[i],u=smoother((t-a[0])/(b[0]-a[0]));
  return a.slice(1).map((v,k)=>mix(v,b[k+1],u));
}
export function toesAt(length, curl, breadth=1){
  curl=clamp(curl);
  const edge=mix(.975,.206,curl**.61);
  const maxAngle=2.12*smooth(curl*1.30);
  const phi = s => maxAngle*smooth((s-edge)/(1-edge));
  let x=0,z=0;
  const points=[];
  for(let j=0;j<=rings;j++){
    const s=j/rings;
    if(j){const a=phi(s-.5/rings);x+=length/rings*Math.cos(a);z+=length/rings*Math.sin(a);}
    const pad=between(s,.235,.475)*(1-between(s,.805,.997));
    const end=1-.95*between(s,.942,1);
    const width=breadth*(.023+.047*pad+.015*(1-s))*end;
    const halfHeight=(.014+.010*pad+.034*(1-s)**5)*end;
    // z here is the integrated midline lift; the flattened skin envelope is
    // added independently so shortening/compression doesn't change arc length.
    points.push([x,z,phi(s),width,halfHeight,s>=.25&&s<=.925&&s<=edge?1:0]);
  }
  return points;
}

export function digits(foot,side){
  const a=foot.yaw,dx=Math.sin(a),dy=Math.cos(a);
  return lengths.map((n,j)=>{
    const d=(j-2)*.040*side,f=.063-.012*Math.abs(j-2);
    // The slightly staggered tips roll in the same distal-first direction.
    const q=clamp(foot.curl + (j-2)*.036*Math.sin(Math.PI*foot.curl));
    return {base:[foot.at[0]+dx*f+dy*d,foot.at[1]+dy*f-dx*d,foot.at[2]],
      yaw:a+angles[j]*side,points:toesAt(n, q, [.81,1.04,1.13,1.02,.88][j])};
  });
}

export function poseAt(time){
  const t=clamp(time,0,frames/fps);
  const [x,y,dz,headAngle,headLift,twist,roll]=bodyAt(t);
  const z=dz+.004*Math.sin(t*4.14+.57), reach=smoother(t/action.plant);
  const lift=smoother((t-action.free)/(action.wristClear-action.free));
  const curl=smoother((t-action.peel)/(action.free-action.peel));
  const flight=t<action.plant;
  const active={at:[mix(.986,1.171,reach)+.225*lift,mix(.62,1.395,reach)+.188*lift,
      .168*(1-reach)+.115*Math.sin(Math.PI*reach)**1.5+.235*lift],
    yaw:mix(.506,.265,reach)-.12*lift, curl:flight?.47*(1-reach):curl,
    planted:!flight && t<action.free, airborne:flight||lift>0};
  const limbs=still.map((v,i)=>{
    const side=i%2===0?-1:1, front=i<2;
    const foot=v?{at:v,yaw:side*(front?.315:1.06),curl:0,planted:true,airborne:false}:active;
    const d=front?.748:-.805;
    const shoulder=[x+side*(front?.306:.372)+twist*d,y+d,.491+z+side*roll*.49];
    const wrist=[foot.at[0]-.020*Math.sin(foot.yaw),foot.at[1]-.020*Math.cos(foot.yaw),foot.at[2]+.082];
    const bones=front?[.755,.782]:[.769,.782];
    const knee=solveJoint(shoulder,wrist,...bones,[side*.92,front?-.54:.62,.27]);
    return {...foot,side,front,shoulder,wrist,knee:knee.point,bones,reachable:knee.reachable,digits:digits(foot,side)};
  });
  return {t,x,y,z,twist,roll,headAngle,headLift,limbs};
}

export function cameraAt(t){
  const u=smoother((t-.62)/6.96);
  const glide = u * (1-u);
  return {
    place:[mix(5.15,5.63,u),mix(2.60,1.52,u)+.12*glide,mix(3.42,1.60,u)],
    aim:[mix(.681,1.195,u),mix(1.211,1.617,u),mix(.346,.119,u)],
    focus:[mix(.57,1.36,u),mix(1.386,1.68,u),mix(.60,.106,u)],
    focal:mix(42,57,u), aperture:mix(6.5,9.4,u),
  };
}
