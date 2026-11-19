import { clamp, mix, smooth, smoother, solveJoint, geckoPose, LIMBS, DUTY, stance } from '../motion.js';
import { digits, poseAt } from '../creature/motion.js';
const TAU=Math.PI*2,S=Math.sin;
const shift=(p,q)=>p.map((v,j)=>v+q[j]);
const path=(a,b,u)=>a.map((v,j)=>mix(v,b[j],u));
const yawAxis=(a)=>[Math.sin(a),Math.cos(a),0];
// Compressed stride and real weight transfer, using precisely the existing
// stance/swing clock, so locked audio cues are still on the foot plants.
export function lived(t){
  const p=geckoPose(t), {c}=p;
  const x=p.x+.058*S(TAU*c-.73), y=p.y*.76+.047;
  const weight=S(c*TAU-.526);
  const z=p.z-.024-.018*S(2*TAU*c+.36),twist=p.twist*.96,roll=weight*.095;
  const headAngle=.185+.112*S(t*1.21+.42)+.034*S(t*3.89),headLift=.028+.019*S(t*1.48+.99);
  const pushOff=.748;
  const limbs=p.limb.map((l,j)=>{
    // Curl while the heel is still anchored. Keep the existing plant times
    // but shorten the airborne interval so the weight shifts before travel.
    const f=l.phase;
    const meant=f<DUTY?f:f<pushOff?DUTY:mix(DUTY,1,(f-pushOff)/(1-pushOff));
    const k=stance(LIMBS[j],c+meant-f);
    const peel=smoother((f-.614)/(pushOff-.614))*(1-smoother((f-.838)/.161));
    const {side,front}=l;
    const p0=front?.745:-.786;
    const at=[k.at[0]*.942,k.at[1]*.76+.047+(front?.094:-.118),k.at[2]*.877];
    const yaw=k.yaw*.766;
    const foot={at,yaw,curl:peel,planted:f<pushOff,airborne:f>=pushOff};
    const shoulder=[x+side*(front?.304:.374)+twist*p0,y+p0,.487+z+side*roll*.54];
    const wrist=shift(at,[-.020*S(yaw),-.020*Math.cos(yaw),.082]);
    const bones=front?[.756,.789]:[.780,.792];
    const knee=solveJoint(shoulder,wrist,...bones,[side*.91,front?-.58:.63,.253]);
    return {...foot,side,front,shoulder,knee:knee.point,wrist,digits:digits(foot,side),reachable:knee.reachable,bones};
  });
  return {t,c,x,y,z,twist,roll,headAngle,headLift,limbs,tailFollow:.145*S(TAU*(c-.26))};
}

function camera(p,a,b,f,fr=5.6,side='inside',roll=0,illum='habitat'){
  return {place:p,aim:a,focus:b,focal:f,aperture:fr,side,roll,illum};
}
const opts=(b,a,p,f,fr,side,rotate)=>camera(shift(b,p),shift(b,a),shift(b,a),f,fr,side,rotate);
function footA(q,j,h=.15){
  const l=q.limbs[j], y=yawAxis(l.yaw);
  return shift(l.at,[y[0]*h,y[1]*h,.031]);
}
const palette=(a,b,u)=>path(a,b,smoother(u));
export function liveCamera(p,shot,u){
  const d=smoother(u), x0=[p.x,p.y,0];
  // Body scale is 1 unit = 6.2 cm. Lenses are true vertical sensor fits.
  if(shot==='eye'||shot==='hero-eye'){
    const offset=.075*S(p.t*1.42);
    const loc=[p.x+.54+.63*p.headAngle,p.y+1.424+offset*.44,.697+p.z+p.headLift];
    const close=shot==='eye';
    return camera(shift(loc,palette(close?[1.56,.38,.56]:[1.88,-.31,.47],close?[1.48,.28,.46]:[1.69,-.14,.40],u)),
      shift(loc,close?[-.041,.036,-.018]:[-.082,.119,-.031]),loc,mix(close?35:34,close?39:39,d),close?7.1:6.5,'inside',mix(-.082,-.039,d));
  }
  if(shot==='grip-anchor'||shot==='step'||shot==='no-yank'){
    const q=footA(p,0,shot==='step'?.19:.15);
    q[2]=mix(.046,q[2],.48);
    const lean=shot==='grip-anchor';
    return opts(q,lean?[.045,-.038,.035]:[.08,-.077,.122],
      lean?palette([-1.61,.24,1.28],[-1.52,.34,1.52],u):palette([-2.01,-.04,1.76],[-1.75,.076,1.72],u),
      lean?34:36,7.,'inside',lean?.10:.15);
  }
  if(shot==='foot'){
    const q=footA(p,1,.18);
    return opts(q,[.005,.040,-.011],palette([.94,.71,-2.76],[.77,.51,-2.30],u),mix(36,42,d),8.7,'beneath',-.10);
  }
  if(shot==='through'){
    return opts(x0,palette([-.19,.24,.16],[.020,.47,.22],u),palette([.57,1.37,-7.76],[1.11,1.16,-7.07],u),mix(31,33,d),8.4,'beneath',mix(.109,.024,d));
  }
  if(shot==='walk-out'){
    return opts(x0,palette([-.12,.49,.416],[-.04,.60,.317],u),palette([-4.31,1.42,6.74],[-4.30,1.26,6.15],u),mix(31,35,d),6.8,'inside',.087);
  }
  if(shot==='hero'){
    return opts(x0,palette([.17,-.37,.365],[.13,.43,.497],u),palette([3.29,.78,8.31],[3.60,1.12,7.91],u),mix(29,33,d),7.1,'inside',-.128);
  }
  return opts(x0,palette([.11,-.30,.32],[.06,-.01,.43],u),palette([3.52,.88,8.26],[3.26,1.06,8.03],u),mix(31,33,d),7.7,'inside',mix(-.075,-.046,d));
}

export function staged(shot,frame,u){
  const t=frame/24;
  if(shot==='replay'||shot==='recap-peel'){
    const replay=shot==='replay';
    const local=mix(replay?2.82:3.34,replay?7.32:7.04,smooth(u));
    const p=poseAt(local);
    const q=footA(p,1,.19);
    const camera=opts(q,replay?[-.035,.046,.024]:[-.047,-.014,.063],
      replay?palette([2.38,-.20,.81],[2.45,-.13,1.08],u):palette([2.62,.48,1.9],[2.37,.34,1.62],u),
      replay?43:48,replay?10.7:9.3,'inside',replay?-.071:.041);
    return {...p,storyTime:t,camera};
  }
  return lived(t);
}
