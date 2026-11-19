import * as THREE from 'three';
import { pbr, mesh, texture, rng, V } from '../demo-render/stage.js';
import { clamp, mix, smooth, between, digitSamples, geckoPose } from './motion.js';

const TAU = Math.PI * 2;
const S = (n) => Math.sin(n);
const MOUTH_START = 1.112, MOUTH_END = 2.177, BODY_START = -3.18, BODY_END = 2.213;
const mouthPhase = y => Math.asin(mix(-.193,-.363,between(y,MOUTH_START,MOUTH_END)));
const C = (n) => Math.cos(n);
const color = (r,g,b) => `rgb(${r|0},${g|0},${b|0})`;
const basisX = V(1,0,0), basisY = V(0,1,0), basisZ = V(0,0,1);

// UV spot pigmentation and two kinds of relief: smaller granular scales and
// larger irregular tubercles. The shade and height atlases share boundaries.
function skinMaps(kind, seed) {
  const body = kind === 'body';
  const [nx,ny,w,h] = body ? [176,69,2048,1024] : kind==='digit' ? [37,27,512,384] : [69,41,896,640];
  const rnd = rng(seed), spots=[];
  const count = body ? 136 : kind==='digit'?11:32;
  for(let i=0;i<count;i++) {
    const u = rnd(), v = (rnd()*.68+.92)%1;
    spots.push([u,v,body ? .0065+.0105*rnd() : .021+.037*rnd(), .021+.032*rnd(), rnd(), rnd()]);
  }
  const colorCanvas=document.createElement('canvas'), bumpCanvas=document.createElement('canvas');
  for (const can of [colorCanvas,bumpCanvas]) {can.width=w;can.height=h;}
  const co=colorCanvas.getContext('2d'), bu=bumpCanvas.getContext('2d');
  co.fillStyle = '#546261';co.fillRect(0,0,w,h);
  bu.fillStyle='#3c3c3c';bu.fillRect(0,0,w,h);
  const sx=w/nx,sy=h/ny;
  for(let j=-1;j<=ny;j++) for(let i=-1;i<=nx;i++) {
    const x=(i+.50+(j%2?.485:0)+(rnd()-.5)*.32)*sx;
    const y=(j+.51+(rnd()-.5)*.31)*sy;
    const u=x/w, v=((1-y/h)%1+1)%1;
    const dorsal=smooth((S(v*TAU)+.45)/.94);
    const head=body?between(u,.78,.9):0;
    const ridge=.64*S(22*u+7.2*v)+.36*S(47*u-8*v)+.18*S(131*u+24*v);
    let red=0;
    for(const [a,b,r,f,d,p] of spots){
      const dy=Math.min(Math.abs(v-b),1-Math.abs(v-b));
      const q=Math.hypot((u-a)/r,dy/f);
      red=Math.max(red,smooth((1.12 + .12*S(21*u+17*v+p*TAU)-q)*2.10)*(.61+.39*d));
    }
    red *= .09+.91*dorsal;
    const grain=12*(rnd()-.5) + ridge*14;
    const mottling=9*S(157*u+29*v)*C(76*u-38*v)+5*S(289*u-82*v);
    const pearl=body&&u<.58&&dorsal>.6 && rnd()>.957 ? 20 : 0;
    const rgb=[mix(154,109,dorsal),mix(140,127,dorsal),mix(119,136,dorsal)];
    const band=body?(1-between(u,.23,.43))*.30*(.5+.5*C(u*114+v*2))**1.64:0;
    const pigment=[mix(181,211,head),96+14*ridge,45+9*ridge];
    const shades=rgb.map((n,k)=>mix(n*(1-band)+grain+pearl+mottling,pigment[k]+grain+mottling*.75,red));
    const knobs=rnd()>.946&&dorsal>.5?1.13:1;
    const rX=sx*(.562+(rnd()-.5)*.11)*knobs,rY=sy*(.552+(rnd()-.5)*.12)*knobs;
    const points=[];
    for(let k=0;k<7;k++) { const a=(k+(rnd()-.5)*.23)*TAU/7;const k0=.87+.18*rnd();points.push([x+C(a)*rX*k0,y+S(a)*rY*k0]); }
    for(const [ctx,isHeight] of [[co,false],[bu,true]]) {
      ctx.beginPath(); ctx.moveTo(...points[0]); for(let k=1;k<points.length;k++) ctx.lineTo(...points[k]); ctx.closePath();
      const g=ctx.createRadialGradient(x-rX*.16,y-rY*.25,.06*Math.min(rX,rY),x,y,Math.max(rX,rY)*1.035);
      if (isHeight) { g.addColorStop(0,knobs>1?'#dedede':'#bcbcbc');g.addColorStop(.58,'#a4a4a4');g.addColorStop(1,'#595959'); }
      else {g.addColorStop(0,color(...shades.map(x=>x*1.09+5)));g.addColorStop(.68,color(...shades));g.addColorStop(1,color(...shades.map(x=>x*.82)));}
      ctx.fillStyle=g;ctx.fill();
    }
  }
  if(body) {
    // Closed mouth crease lives on the continuous head surface. Both the
    // color and relief follow the same curve (no floating strips or plates).
    for(const side of [-1,1]) for (const [offset,width,tint] of [[-.0042,2.7,'#c9b59a80'],[0,2.5,'#201914cb']]) {
      for(let i=0;i<120;i++){
        const a=i/120,b=(i+1)/120,fade=between(a,0,.11)*(1-between(a,.92,1));
        const toXY=(u)=>{const y=mix(MOUTH_START,MOUTH_END,u),angle=mouthPhase(y);const v=side>0 ? 1+angle/TAU : .5-angle/TAU;
          return [(y-BODY_START)/(BODY_END-BODY_START)*w,(1-v+offset)*h];};
        co.beginPath();co.moveTo(...toXY(a));co.lineTo(...toXY(b));co.lineWidth=width*fade+.10;co.lineCap='round';co.strokeStyle=tint;co.stroke();
      }
    }
  }
  const map=new THREE.CanvasTexture(colorCanvas);map.colorSpace=THREE.SRGBColorSpace;
  const bump=new THREE.CanvasTexture(bumpCanvas);
  map.anisotropy=4; bump.anisotropy=4;
  return {map,bumpMap:bump};
}

const irisAtlas = () => texture(512,512,(ctx,w,h)=>{
  const img=ctx.createImageData(w,h), p=img.data;
  for(let y=0;y<h;y++) for(let x=0;x<w;x++){
    const u=(x-(w-1)*.5)/(w*.5),v=(y-(h-1)*.5)/(h*.5),r=Math.hypot(u,v),a=Math.atan2(v,u);
    const d=S(a*41+S(r*12+a*8)*2.2)*.40+S(a*93-r*5.3+1.9*C(a*11))*.27+S(a*167+S(a*12+r*17)*1.5)*.23;
    const vein=Math.pow(.5+.5*S(92*a+2*S(r*27+8*a)+2.5*C(a*9)),14);
    const clusters=14*S(a*7.1+r*17)*C(a*5+r*33)+12*S(a*44.1+r*7.61)*C(a*14.6-r*41);
    const glow=27*S(2.19*Math.min(r,1)) + 31*d - 35*vein + clusters + 7*S(x*17.74+y*1.744+r*26);
    const fade=1-between(r,.83,1.07)*.76, i=4*(y*w+x);
    p[i]=clamp((153+glow*1.57)*fade,0,255);p[i+1]=clamp((103+glow)*fade,0,255);p[i+2]=clamp((48+glow*.59)*fade,0,255);p[i+3]=255;
  }
  ctx.putImageData(img,0,0);
  // The lens isn't an emissive eye: a narrow pupil sits inside a ridged iris.
  ctx.save();ctx.scale(w,h);ctx.fillStyle='#08090a';ctx.beginPath();ctx.moveTo(.52,.09);ctx.bezierCurveTo(.539,.25,.548,.33,.553,.401);ctx.bezierCurveTo(.543,.435,.555,.49,.562,.519);ctx.bezierCurveTo(.547,.635,.537,.80,.505,.909);ctx.bezierCurveTo(.479,.754,.466,.617,.458,.559);ctx.bezierCurveTo(.476,.493,.470,.453,.453,.42);ctx.bezierCurveTo(.477,.318,.492,.218,.52,.09);ctx.fill();ctx.restore();
});

export function geckoPalette() {
  const skin=(kind,seed,rough,bump)=>pbr('#ffffff',rough,.035,{...skinMaps(kind,seed),bumpScale:bump});
  const body=skin('body',17216,.52,.036);
  const leg=skin('limb',290716,.55,.026);
  const pad=skin('digit',1927,.56,.018);
  const lid=skin('digit',7384,.59,.012);
  const lamella=pbr('#b8b5a6',.57,.019,{emissive:'#423125',emissiveIntensity:.09});
  const lamellaLit=pbr('#cbc4af',.60,.025,{emissive:'#5d786d',emissiveIntensity:.12});
  const claw=pbr('#b9a582',.38,.018);
  const iris=new THREE.MeshPhysicalMaterial({color:0xffffff,map:irisAtlas(),roughness:.23,metalness:.025,clearcoat:1,clearcoatRoughness:.075});
  return {body,leg,pad,lid,lamella,lamellaLit,claw,iris};
}

function smoothMesh(parent, n, sides, material) {
  const p = new Float32Array((n+1)*(sides+1)*3), uv=new Float32Array((n+1)*(sides+1)*2), idx=[];
  for(let i=0;i<=n;i++) for(let j=0;j<=sides;j++) {
    const k=i*(sides+1)+j;uv[k*2]=i/n;uv[k*2+1]=j/sides;
    if(i<n&&j<sides) idx.push(k,k+sides+1,k+1,k+1,k+sides+1,k+sides+2);
  }
  const geom=new THREE.BufferGeometry();
  geom.setAttribute('position',new THREE.BufferAttribute(p,3).setUsage(THREE.DynamicDrawUsage));
  geom.setAttribute('uv',new THREE.BufferAttribute(uv,2));geom.setIndex(idx);
  const model=mesh(parent,geom,material);model.frustumCulled=false;
  const ca=Array.from({length:sides+1},(_,i)=>C(TAU*i/sides)),sa=Array.from({length:sides+1},(_,i)=>S(TAU*i/sides));
  return {model,update(sampler){
    for(let i=0,u=0;i<=n;i++) {
      const [center,right,up,rx,rz,sectionShape]=sampler(i/n,i,n);
      for(let j=0;j<=sides;j++) {
        const [x,z]=sectionShape ? sectionShape(rx,rz,ca[j],sa[j]) : [rx*ca[j],rz*sa[j]];
        p[u++]=center.x+right.x*x+up.x*z;
        p[u++]=center.y+right.y*x+up.y*z;
        p[u++]=center.z+right.z*x+up.z*z;
      }
    }
    geom.attributes.position.needsUpdate=true;geom.computeVertexNormals();
  }};
}
const sample8 = (list,s) => {
  const t=clamp(s)*(list.length-1),i=Math.min(list.length-2,Math.floor(t)),u=t-i;
  const a=list[i],b=list[i+1];
  return {x:mix(a.x,b.x,u),z:mix(a.z,b.z,u),roll:mix(a.roll,b.roll,u),width:mix(a.width,b.width,u),height:mix(a.height,b.height,u),contact:u>.5?b.contact:a.contact};
};
const doll = new THREE.Object3D();
const sphereSmall=new THREE.SphereGeometry(1,12,8);

export function digit(parent,palette,length,breadth,clawed=true,steps=36,ribs=13) {
  const fiber=smoothMesh(parent,steps,16,palette.pad);
  const lamella=new THREE.InstancedMesh(sphereSmall,palette.lamella,ribs);
  lamella.instanceMatrix.setUsage(THREE.DynamicDrawUsage);lamella.frustumCulled=false;parent.add(lamella);
  const shell=smoothMesh(parent,12,10,palette.claw);shell.model.visible=clawed;
  const rot=new THREE.Matrix4(),x=V(0,0,0),y=V(0,0,0),z=V(0,0,0);
  const skinPoint=V(0,0,0), lateral=V(1,0,0);
  function orient(base,dx,dy,q) {
    skinPoint.set(base[0]+dx*q.x,base[1]+dy*q.x,base[2]+q.z);
    z.set(-dx*S(q.roll),-dy*S(q.roll),C(q.roll));
    y.set(dx*C(q.roll),dy*C(q.roll),S(q.roll));
    return [skinPoint,lateral,z,q.width,q.height];
  }
  return {model:fiber.model,update(base,yaw,curl,highlight=false){
    const dx=S(yaw),dy=C(yaw); lateral.set(dy,-dx,0);
    const path=digitSamples(length,curl,breadth,steps);
    fiber.update((s,i)=>orient(base,dx,dy,path[i]));
    for(let j=0;j<ribs;j++) {
      const u=.287+.604*j/(ribs-1), a=sample8(path,u);
      orient(base,dx,dy,a);
      const ridgeHeight = .0096 + .042 * (1-u)**5;
      doll.position.copy(skinPoint).addScaledVector(z,-a.height-(.006+.043*(1-u)**5) + ridgeHeight+.0011);
      rot.makeBasis(lateral,y,z);doll.quaternion.setFromRotationMatrix(rot);
      doll.scale.set(a.width*.86, length/ribs*.213, ridgeHeight);
      doll.updateMatrix();lamella.setMatrixAt(j,doll.matrix);
      lamella.setColorAt(j,new THREE.Color(a.contact&&highlight?'#d9fff0':j%2===0?'#f7eadd':'#e2d3b9'));
    }
    lamella.instanceMatrix.needsUpdate=true;
    if(lamella.instanceColor)lamella.instanceColor.needsUpdate=true;
    if(clawed) {
      const tip=sample8(path,.974);orient(base,dx,dy,tip);
      const tipP=skinPoint.clone(), tangent=y.clone(), up=z.clone();
      shell.update((s)=>[tipP.clone().addScaledVector(tangent,s*.054).addScaledVector(up,.011+.013*S(Math.PI*s)-.004*s),lateral,up,.0103*(1-s)**.7+.0007,.0091*(1-s)**.69+.0008]);
    }
  }};
}

export function foot(parent,palette,side=1,enhanced=false) {
  const palm = mesh(parent, new THREE.SphereGeometry(1,24,16),palette.leg);
  const lengths=[.276,.418,.514,.475,.344];
  const bend=[-.96,-.49,-.071,.391,.920];
  const digits=lengths.map((l,i)=>digit(parent,palette,l,[.90,.96,1.11,1.00,.88][i],i!==0,enhanced?54:24,enhanced?14:10));
  return {update(base, angle, curl, showContact=false){
    const dx=S(angle),dy=C(angle);
    palm.position.set(base[0]+dx*.035,base[1]+dy*.035,base[2]+.063);
    palm.scale.set(.141,.145,.059);palm.rotation.z=-angle;
    for (let i=0;i<5;i++) {
      const d=(i-2)*.046*side,forward=.083-.015*Math.abs(i-2), a=angle+bend[i]*side;
      const c=clamp(curl*(.914+.043*i));
      digits[i].update([base[0]+dx*forward+dy*d,base[1]+dy*forward-dx*d,base[2]],a,c,showContact);
    }
  }};
}

const profile=[
  [BODY_START,.19,.001,.002],[-3.04,.205,.028,.021],[-2.78,.235,.070,.045],[-2.47,.276,.095,.075],[-2.15,.337,.134,.093],[-1.82,.381,.182,.116],[-1.49,.433,.239,.159],[-1.16,.491,.305,.201],[-.89,.537,.377,.239],[-.63,.589,.49,.293],[-.24,.612,.568,.327],[.13,.606,.599,.318],[.46,.58,.549,.296],[.726,.550,.430,.239],[.92,.554,.406,.237],[1.08,.589,.502,.268],[1.26,.617,.609,.297],[1.43,.629,.589,.306],[1.61,.640,.527,.287],[1.78,.636,.438,.233],[1.91,.625,.351,.181],[2.012,.612,.286,.139],[2.092,.602,.223,.106],[2.148,.603,.156,.075],[2.190,.607,.085,.045],[BODY_END,.608,.003,.003],
];
function section(y) {
  let i=0;while(i<profile.length-2&&y>profile[i+1][0])i++;
  const a=profile[i],b=profile[i+1],c=profile[Math.max(0,i-1)],d=profile[Math.min(profile.length-1,i+2)];
  const u=clamp((y-a[0])/(b[0]-a[0]));
  const h=b[0]-a[0], p=(u*u*(3-2*u));
  return [1,2,3].map((j)=>{
    const m=(b[j]-c[j])/(b[0]-c[0])*h, n=(d[j]-a[j])/(d[0]-a[0])*h;
    return mix(a[j],b[j],p)+m*u*(1-u)**2-n*u*u*(1-u);
  });
}
const spineX = (y,twist,c) => y<-.74 ? twist*(-.74)+.27*S(c*4.6-1.42*(y+.74))*(1-between(y,-2.84,-.72))+.285*(1-between(y,-3.20,-.93)) : twist*y;
const local = (p,y,x,z) => {
  const a = between(y,.84,1.86), drift = p.headLook*a;
  const cheek = p.refined ? 1+.083*between(y,.88,1.28)*(1-between(y,2.02,2.212)) : 1;
  const length = p.refined ? y-.203*between(y,.89,2.213) : y;
  return V(p.x+spineX(y,p.twist,p.c)+x*cheek+drift,p.y+length,z+p.z+p.headTilt*a+.005*S(p.c*2+y*.42));
};
function sculpt(y) {
  const head=between(y,.892,1.250)*(1-between(y,2.188,BODY_END));
  const seam=mouthPhase(y), open=between(y,MOUTH_START,1.228)*(1-between(y,2.15,MOUTH_END));
  return (rx,rz,c,s)=>{
    const exponent=1-.278*head;
    const cheek=1+head*.046*Math.max(0,-s);
    const crease=.014 * open * Math.exp(-((s-S(seam))**2)/.0021);
    return [Math.sign(c)*(rx*Math.abs(c)**exponent*cheek-crease),rz*Math.sign(s)*Math.abs(s)**(1-.185*head)];
  };
}

const orientFace = (g,n) => g.quaternion.setFromUnitVectors(basisZ,n);

function lensGeometry() {
  const n=64,rings=22,p=[0,0,.08],uv=[.5,.5],ix=[];
  for(let j=1;j<=rings;j++) {
    const r=j/rings;
    for(let i=0;i<n;i++) {
      const a=i*TAU/n,x=r*C(a),y=r*S(a);
      p.push(x*.204,y*.202,.088*Math.sqrt(Math.max(0,1-r*r)));uv.push(.5+.5*x,.5+.5*y);
      const k=1+(j-1)*n+i, kn=1+(j-1)*n+(i+1)%n;
      if(j===1)ix.push(0,k,kn);else ix.push(k-n,k,kn, k-n,kn,kn-n);
    }
  }
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ix);g.computeVertexNormals();return g;
}

export function gecko(parent,palette) {
  const refined=!!palette.refined;
  const body=smoothMesh(parent,refined?134:98,refined?50:40,palette.body);
  const irisFrame=new THREE.Matrix4();
  const slit=pbr('#28241c',.71,0);
  const heads=[-1,1].map((side)=>{
    const eye=new THREE.Group();parent.add(eye);
    const socket=mesh(eye,new THREE.SphereGeometry(1,32,18),palette.lid);
    socket.scale.set(refined?.229:.241,refined?.209:.221,.143); socket.position.z=refined?-.106:-.092;
    const orbit=mesh(eye,new THREE.TorusGeometry(.196,refined?.006:.013,9,64),palette.lid);orbit.scale.set(1,.94,.84);orbit.position.z=-.010;
    const retina=mesh(eye,lensGeometry(),palette.iris,0,0,-.004);retina.scale.set(1,.945,.67);
    const nostril=mesh(parent,sphereSmall,slit);nostril.scale.set(refined?.017:.021,refined?.014:.018,.006);
    const ear=mesh(parent,sphereSmall,slit);ear.scale.set(.029,.042,.006);
    return {side,eye,retina,nostril,ear};
  });
  const legs=[-1,1,-1,1].map((s)=>({limb:smoothMesh(parent,28,20,palette.leg),foot:foot(parent,palette,s)}));
  return {update(t){
    const p=geckoPose(t);
    p.refined=refined;
    p.eyePoints=[];
    p.headLook=.105*S(t*.83-.44)+.061*S(t*1.72);
    p.headTilt=.041*S(t*1.64+.74)+.014*S(t*2.26);
    body.update((s)=>{
      const y0=mix(profile[0][0],profile.at(-1)[0],s),[h,w,r]=section(y0);
      const breath=1+.028*S(t*3.1+(y0+.4)*.91)*between(y0,-1,-.54)*(1-between(y0,.45,1.01));
      const cheek = refined ? 1+.083*between(y0,.88,1.28)*(1-between(y0,2.02,2.212)) : 1;
      const outline=sculpt(y0);
      const shape=refined?(rx,rz,c,d)=>{
        const [x,z]=outline(rx,rz,c,d);
        const a=(Math.atan2(d,c)/TAU+1)%1;
        const gain=(.0007+.0041*between(y0,-2.61,-.45))*(.23+.77*between(d,-.54,.40));
        const relief=(palette.reliefAt(s,a)-.50)*gain;
        return [x+c*relief,z+d*relief];
      }:outline;
      return [local(p,y0,0,h),basisX,basisZ,Math.max(.002,w*breath*cheek),Math.max(.002,r*breath),shape];
    });
    for(const {side,eye,retina,nostril,ear} of heads){
      const v=local(p,refined?1.431:1.447,side*(refined?.544:.552),.764);eye.position.copy(v);eye.scale.setScalar(refined?.777:.77);
      const normal=V(side*.903,.104,.415).normalize();
      if(refined) {
        const up=V(0,.105,1).addScaledVector(normal,-V(0,.105,1).dot(normal)).normalize();
        const right=up.clone().cross(normal).normalize();
        irisFrame.makeBasis(right,up,normal);eye.quaternion.setFromRotationMatrix(irisFrame);
      } else {orientFace(eye,normal);eye.rotateZ(side*.063);}
      retina.rotation.z=.028*S(t*1.8+side);
      p.eyePoints.push(v.clone().addScaledVector(normal,.038));
      const dotOnSurface=(item,y,angle,depth)=>{
        const [h,w,r]=section(y),[x,z]=sculpt(y)(w,r,side*C(angle),S(angle));
        const n=V(side*C(angle),.23,S(angle)).normalize();
        item.position.copy(local(p,y,x,h+z)).addScaledVector(n,depth);orientFace(item,n);
      };
      dotOnSurface(nostril,2.054,.543,.0015);
      dotOnSurface(ear,1.084,-.062,-.005);
    }
    legs.forEach(({limb,foot:Foot},i)=>{
      const q=p.limb[i], a=V(...q.shoulder),b=V(...q.knee),c=V(...q.wrist);
      const p1=a.clone().lerp(b,.85),p2=b.clone().lerp(c,.19);
      const curve=new THREE.CatmullRomCurve3([a,a.clone().lerp(b,.48),p1,p2,c.clone().lerp(b,.17),c]);
      limb.update(s=>{
        const point=curve.getPoint(s),forward=curve.getTangent(s),right=V(forward.y,-forward.x,0).normalize(),up=right.clone().cross(forward).normalize();
        const thickness=mix(q.front?.150:.186,.057,s)+.025*S(Math.PI*s*1.27);
        return [point,right,up,thickness,thickness*.77];
      });
      Foot.update(q.at,q.yaw,q.curl);
    });
    return p;
  }};
}
