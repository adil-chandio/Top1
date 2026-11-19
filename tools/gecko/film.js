import * as THREE from 'three';
import { background, bevel, camera, frame, glowTexture, mesh, pbr, rng, texture, V } from '../demo-render/stage.js';
import { between, clamp, digitSamples, mix, release } from './motion.js';
import { digit, foot, gecko, geckoPalette } from './model.js';
import { microscope } from './microscope.js';

const pi=Math.PI;
const nightShots=new Set(['eye','step','climb','through','walk-out','hero']);
const microShots=new Set(['setae','branched','field','vanderwaals','axis','angles','recap-contact']);
const lensShots=new Set(['eye','step','through','lamella','branched','vanderwaals','peel-side','hero']);
const timeTracks = (p,q,a,b,mm,aperture=7,roll=[0,0],up=[0,1,0])=>({p,q,a,b,mm,aperture,roll,up});

const cams={
  eye: timeTracks([2.96,2.31,1.78],[2.28,1.91,1.72],[.26,1.51,.68],[.29,1.54,.74],[51,55],12,[-.18,-.25]),
  step: timeTracks([-1.37,.83,2.50],[-.92,.44,2.37],[-.118,.240,.043],[-.066,.254,.05],[53,57],8,[-.092,-.161]),
  climb: timeTracks([2.68,.81,9.54],[2.34,.95,8.75],[.05,-.38,.22],[.11,-.29,.23],[49,48],5,[-.22,-.185]),
  through: timeTracks([-2.57,1.62,-5.49],[-1.81,1.99,-4.63],[-.44,.81,.15],[-.52,.96,.14],[45,49],8,[.125,.11]),
  foot: timeTracks([-1.83,2.53,-5.60],[-.75,2.41,-4.42],[.16,1.01,.03],[.12,1.03,.04],[47,50],9,[.15,.06]),
  lamella: timeTracks([-.40,-1.75,-4.23],[.25,-1.80,-3.58],[.26,.06,.11],[.21,.037,.096],[42,50],7,[-.02,-.10],[0,-1,0]),
  setae: timeTracks([-.93,-5.92,2.76],[-.16,-5.09,2.64],[-.02,-.05,.86],[.09,-.13,.83],[31,33],7,[.05,.01],[0,0,1]),
  branched: timeTracks([1.24,-3.78,1.25],[1.52,-2.98,1.34],[.63,-.19,.66],[.66,-.12,.57],[47,50],10,[.02,-.06],[0,0,1]),
  field: timeTracks([3.76,-5.94,2.56],[3.04,-5.54,2.32],[.04,-.15,.76],[.12,-.16,.72],[32,34],7,[.025,.04],[0,0,1]),
  vanderwaals: timeTracks([.31,-3.03,.69],[.88,-2.67,.53],[.59,-.118,.36],[.65,-.14,.27],[48,52],10,[.012,-.031],[0,0,1]),
  axis: timeTracks([-2.42,-6.66,1.31],[-1.29,-6.07,1.28],[.22,-.169,.82],[.23,-.146,.75],[31,35],5,[0,.03],[0,0,1]),
  shear: timeTracks([.42,-7.10,2.37],[.19,-6.72,1.88],[.04,-.11,.43],[-.10,-.140,.35],[30,32],5,[.035,0],[0,0,1]),
  'peel-wide': timeTracks([.34,-7.02,1.19],[.18,-6.85,1.39],[-.041,-.02,.38],[-.13,-.009,.43],[31,32],6,[.02,.01],[0,0,1]),
  'peel-side': timeTracks([.52,-5.91,.96],[.34,-5.83,1.58],[.04,.027,.45],[-.12,.004,.77],[36,36],6,[.015,0],[0,0,1]),
  peeled: timeTracks([-2.21,2.55,5.83],[-1.36,2.72,5.92],[.026,.39,.48],[.045,.28,1.08],[35,36],7,[-.095,-.072]),
  replay: timeTracks([-.72,6.73,1.33],[-.73,6.36,1.77],[-.021,.028,.53],[-.13,.008,.76],[31,33],6,[0,-.05],[0,0,1]),
  angles: timeTracks([1.56,-4.64,1.52],[.85,-3.97,1.87],[.67,-.16,.55],[.57,-.14,.65],[47,51],8,[.03,.015],[0,0,1]),
  'walk-out': timeTracks([-2.41,.43,8.86],[-2.17,.79,8.21],[.024,-.22,.21],[.04,-.20,.25],[47,45],5,[.15,.16]),
  'recap-contact': timeTracks([1.05,-3.29,.78],[.88,-3.03,.67],[.55,-.16,.36],[.57,-.17,.29],[48,52],7,[.04,.02],[0,0,1]),
  'recap-shear': timeTracks([.64,-6.92,2.25],[.47,-6.71,1.98],[-.04,-.12,.37],[-.14,-.12,.33],[30,32],6,[.02,0],[0,0,1]),
  'recap-peel': timeTracks([.33,-6.10,1.15],[.24,-6.10,1.61],[.11,.025,.43],[-.11,.025,.77],[36,35],7,[0,.023],[0,0,1]),
  hero: timeTracks([3.99,1.62,6.28],[3.13,1.04,8.81],[.10,.75,.47],[.02,-.29,.27],[50,48],9,[-.085,-.15]),
};

function softShadow(parent,w,h,opacity,tex) {
  const m=new THREE.MeshBasicMaterial({ map:tex,color:'#050d10',transparent:true,opacity,depthWrite:false });
  const shadow=mesh(parent,new THREE.PlaneGeometry(w,h),m);shadow.renderOrder=1;return shadow;
}

function matteSurface() {
  const map=texture(896,896,(ctx,w,h)=>{
    const rand=rng(14633);const grad=ctx.createLinearGradient(0,0,w,h*.4);grad.addColorStop(0,'#53615b');grad.addColorStop(.43,'#475d5a');grad.addColorStop(1,'#293939');
    ctx.fillStyle=grad;ctx.fillRect(0,0,w,h);
    for(let i=0;i<9560;i++) {
      const r=.29+rand()*1.65;ctx.fillStyle=i%3?'#4476701c':'#a9a48a21';ctx.fillRect(rand()*w,rand()*h,r,r);
    }
    for(let i=0;i<60;i++) {ctx.fillStyle=i%2?'#bec9b608':'#07171825';ctx.fillRect(rand()*w,rand()*h,1+rand()*95,.4+rand()*.7);}
    for(let i=0;i<5;i++) {
      const x=9+rand()*w*.83, g=ctx.createLinearGradient(x,0,x+12,0);
      g.addColorStop(0,'#d5e1d000');g.addColorStop(.5,'#aadcdd20');g.addColorStop(1,'#d5e1d000');ctx.fillStyle=g;ctx.fillRect(x,0,12,h);
    }
  });
  return pbr('#b4c3bd',.54,.35,{map,bumpMap:map,bumpScale:.010,envMapIntensity:.65});
}

function atrium(parent,glow) {
  const metal=pbr('#324949',.38,.62), edge=pbr('#9caaa1',.37,.58);
  const backdrop=mesh(parent,new THREE.PlaneGeometry(9.60,21),matteSurface(),0,1.72,-.018);
  backdrop.material.envMapIntensity=.80;
  const wall=new THREE.Group();parent.add(wall);
  for(const side of [-1,1]) {
    bevel(wall,[.32,21,.244],.05,metal,[side*2.81,1.72,-.17]);
    bevel(wall,[.025,21,.026],.006,edge,[side*2.645,1.72,.023]);
    for(let i=0;i<4;i++) bevel(wall,[.16,.12,.23],.027,edge,[side*2.725,-5.4+i*4.57,-.114]);
  }
  const grime=texture(1024,256,(ctx,w,h)=>{
    const rand=rng(71821);ctx.clearRect(0,0,w,h);
    for(let n=0;n<240;n++) { const x=rand()*w,y=rand()*h, r=2+rand()*13;
      const l=ctx.createRadialGradient(x,y,0,x,y,r);l.addColorStop(0,'#e5f0d239');l.addColorStop(1,'#e5f0d200');ctx.fillStyle=l;ctx.fillRect(x-r,y-r,r*2,r*2);
    }
  });
  const skyReflections=texture(256,512,(ctx,w,h)=>{
    ctx.clearRect(0,0,w,h);
    const rng2=rng(7162);
    // Broad smeared reflections, not droplets on the adhesive surface.
    for(let i=0;i<69;i++){
      const x=rng2()*w,y=rng2()*h,r=5+rng2()*29;
      const l=ctx.createRadialGradient(x,y,0,x,y,r);
      l.addColorStop(0,i%5?'#a1d5b931':'#efbf8973');l.addColorStop(1,'#90bdb800');
      ctx.save();ctx.translate(x,y);ctx.scale(.56,1.30);ctx.translate(-x,-y);
      ctx.fillStyle=l;ctx.fillRect(x-r,y-r,r*2,r*2);ctx.restore();
    }
  });
  const reflections=mesh(parent,new THREE.PlaneGeometry(6.4,15.6),new THREE.MeshBasicMaterial({map:skyReflections,transparent:true,depthWrite:false,opacity:.57,side:THREE.DoubleSide}),.29,2.12,.001);
  reflections.rotation.z=-.24;
  const cloud = new THREE.Mesh(
    new THREE.PlaneGeometry(9,3.4),new THREE.MeshBasicMaterial({map:grime,transparent:true,opacity:.34,depthWrite:false,side:THREE.DoubleSide})
  );cloud.position.set(-1.24,1.95,-.024);cloud.rotation.z=.70;parent.add(cloud);
  const gleam = new THREE.Mesh(new THREE.PlaneGeometry(18,5.7),new THREE.MeshBasicMaterial({map:glow,color:'#a3e5d6',opacity:.22,transparent:true,blending:THREE.AdditiveBlending,depthWrite:false,side:THREE.DoubleSide}));
  gleam.position.set(-1.45,2.09,.0018);gleam.rotation.z=.89;parent.add(gleam);
  const amber=new THREE.Mesh(new THREE.PlaneGeometry(10.9,4.9),new THREE.MeshBasicMaterial({map:glow,color:'#ffb979',opacity:.20,transparent:true,blending:THREE.AdditiveBlending,depthWrite:false,side:THREE.DoubleSide}));
  amber.position.set(2.31,-.48,.002);amber.rotation.z=.66;parent.add(amber);
  const dustGroup = new THREE.Group();parent.add(dustGroup);
  const rand=rng(40317), m=new THREE.PointsMaterial({ size:.093,color:'#e9c8a2',transparent:true,opacity:.37,map:glow,depthWrite:false,blending:THREE.AdditiveBlending });
  const pt=Array.from({length:92},()=>[(rand()-.5)*16,(rand()-.48)*26, .26+rand()*5.4]).flat();
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pt,3));dustGroup.add(new THREE.Points(g,m));
  return {update(t,through){
    backdrop.visible=!through;cloud.visible=through;gleam.visible=amber.visible=true;
    reflections.position.x = .33 + .062*Math.sin(t*.58);reflections.material.opacity=through?.76:.38;
    dustGroup.visible=!through;dustGroup.position.set(.09*Math.sin(t*.54),.16*Math.sin(t*.342),.1*Math.cos(t*.19));
    const wind=between(t,55,62);
    m.opacity= .36+.051*wind;
  }};
}

function bench(parent,glow,palette) {
  const trim=pbr('#4c7368',.29,.60), bed=pbr('#213936',.325,.50,{emissive:'#1b302d',emissiveIntensity:.22});
  const glass = bevel(parent,[7.5,4.7,.22],.045,bed,[0,0,-.110]);
  const flash=mesh(parent,new THREE.PlaneGeometry(7,2.16),new THREE.MeshBasicMaterial({map:glow,color:'#9edccf',blending:THREE.AdditiveBlending,depthWrite:false,transparent:true,opacity:.25}),.86,-.57,.001);
  flash.rotation.z=.19;
  const plate=new THREE.Group();parent.add(plate);
  for (const f of [-1,1]) {
    bevel(plate,[7.47,.037,.037],.009,trim,[0,f*2.305,-.056]);
    bevel(plate,[.037,4.61,.046],.008,trim,[f*3.719,0,-.061]);
  }
  const tile=new THREE.Group();parent.add(tile);tile.scale.setScalar(5.95);
  const big=digit(tile,palette,.614,1.19,true,68,15);
  const heel=mesh(tile,new THREE.SphereGeometry(1,28,18),palette.leg);heel.scale.set(.212,.110,.057);
  const toes=new THREE.Group();parent.add(toes);toes.scale.setScalar(4.21);
  const palm=foot(toes,palette,1,true);
  const wrist = mesh(toes,new THREE.CapsuleGeometry(.094,.405,6,22),palette.leg,0,-.22,.113);
  wrist.rotation.x=-.272;
  const sh=softShadow(parent,6.06,1.83,.46,glow);sh.position.set(-.16,-.021,.002);sh.rotation.z=.049;
  const ribbon = new THREE.Group();parent.add(ribbon);
  const loadIn=new THREE.MeshBasicMaterial({color:'#b6eadc',transparent:true,opacity:.83,depthTest:true,depthWrite:false,toneMapped:false});
  const vect=new THREE.ArrowHelper(V(-1,0,0),V(1.37,-.67,.055),2.15,'#c1f7e2',.24,.15);ribbon.add(vect);
  vect.line.material=new THREE.LineBasicMaterial({color:'#ade6d4',transparent:true,opacity:.7,depthWrite:false,toneMapped:false});vect.cone.material=loadIn;
  const bar = mesh(ribbon,new THREE.CylinderGeometry(.016,.016,1,12),loadIn);bar.rotation.z=pi/2;
  mesh(ribbon,new THREE.PlaneGeometry(3.36,.014),new THREE.MeshBasicMaterial({color:'#698980',transparent:true,opacity:.38,depthWrite:false}),-.08,-.708,.021);
  const marks = Array.from({length:12},()=>mesh(parent,new THREE.PlaneGeometry(.170,.028),new THREE.MeshBasicMaterial({
    color:'#97e1c3',transparent:true,opacity:.75,depthWrite:false,toneMapped:false})));
  return function update(t,kind,cut) {
    const beneath=kind==='foot'||kind==='lamella';
    const wide=kind==='foot'||kind==='peeled';
    const recap=kind==='recap-peel', replay=kind==='replay';
    const shear=kind==='shear'||kind==='recap-shear';
    const slowT=replay?mix(35.51,38.82,clamp((t-41.125)/3.53)):recap?mix(35.37,39.32,clamp((t-55.458)/2.37)):t;
    const action = release(slowT,cut.marks.curlStart,cut.marks.digitRelease);
    const c = (shear||beneath)?0:action.curl;
    const lift = (shear||beneath||replay)?0:action.palmLift;
    const showContact=shear||beneath;
    glass.visible=flash.visible=!beneath;plate.visible=true;
    sh.visible=!beneath;sh.material.opacity=.58*(1-.81*lift/.22);sh.rotation.z=wide?pi/2:.041;
    sh.position.set(wide?-.07:-.39,wide?.78:-.09,.0019);
    tile.visible=!wide;toes.visible=wide;
    if(wide){
      palm.update([-.036,-.110,lift],.092+.06*between(t,39.04,40.47),c,showContact);
      wrist.position.set(-.022,-.32,lift+.112);
    } else {
      const offset=shear?.008*between(t,kind==='shear'?cut.marks.shear:54.22,kind==='shear'?30.42:54.81):0;
      const x=-.291-offset, z=lift*.68;
      big.update([x,0,z],pi/2,c,showContact);
      heel.position.set(x-.135,0,z+.064);
      const footprint = digitSamples(.614,c,1.19,96);
      const peel=kind==='peel-wide'||kind==='peel-side'||recap||replay;
      for(const [i,m] of marks.entries()){
        const s=mix(.288,.909,i/(marks.length-1)),sample=footprint[Math.round(s*96)];
        const visibility = !shear ? between(slowT,35.44,36.03) : between(t,kind==='shear'?29.41:54.43,kind==='shear'?30.05:54.72);
        m.visible=(shear||peel)&&sample.contact&&z<.016;
        m.position.set((x+.614*s)*5.95,replay?.66:-.565,.006);
        m.material.opacity=.57*visibility;
      }
    }
    if(wide)for(const m of marks)m.visible=false;
    ribbon.visible=shear;
    if(shear) {
      const a=kind==='shear'?cut.marks.shear:54.13, b=kind==='shear'?30.83:55.07;
      const l=.15+between(t,a,b)*1.98;
      vect.setLength(l,.16,.14);vect.position.set(1.47,-.829,.059);
      bar.position.set(1.47-l*.5,-.829,.059);bar.scale.y=Math.max(.029,l-.10);
      loadIn.opacity=.05+.90*between(t,a-.09,a+.51);
      vect.line.material.opacity=loadIn.opacity;
    }
  };
}

export function geckoFilm(environment,cut) {
  const scene=new THREE.Scene();scene.environment=environment;
  const jungle=background(['#101f28','#304943','#53694c4c']);
  const lab=background(['#0d1d24','#304340','#31535366']);
  const micros=background(['#111a21','#3d5350','#9f5e3c54']);
  const key=new THREE.DirectionalLight('#ffdfb9',3.0);key.position.set(2.73,5.84,4.18);scene.add(key);
  const edge = new THREE.DirectionalLight('#97ddd8',2.3);edge.position.set(-5.78,2.66,1.16);scene.add(edge);
  const below=new THREE.DirectionalLight('#f4e7ca',.70);below.position.set(3.62,1.67,-3.62);scene.add(below);
  const amb=new THREE.HemisphereLight('#a7c8cc','#301e20',.5);scene.add(amb);
  const glow=glowTexture(), palette=geckoPalette();
  const outside=new THREE.Group(), macro=new THREE.Group(), micro=new THREE.Group();scene.add(outside,macro,micro);
  const place=atrium(outside,glow);
  const shadowBody=softShadow(outside,1.78,4.92,.41,glow), feet=Array.from({length:4},()=>softShadow(outside,1.11,.99,.76,glow));
  const animal=gecko(outside,palette);
  const pad=bench(macro,glow,palette), field=microscope(micro);
  const cam=camera();cam.near=.033;cam.updateProjectionMatrix();
  function update(t,shot) {
    const {kind,progress}=shot, live=nightShots.has(kind), microscope=microShots.has(kind);
    const glass=kind==='through'||kind==='foot'||kind==='lamella';
    outside.visible=live;macro.visible=!live&&!microscope;micro.visible=microscope;
    scene.background=live?jungle:microscope?micros:lab;
    scene.environmentIntensity=live?.47:microscope?.49:.54;
    key.position.set(live?2.76:2.18,live?6.0:3.5,live?4.47:4.61);
    key.intensity=live?2.69:microscope?2.90:2.45;
    edge.intensity=live?2.21:microscope?1.94:2.18;
    below.intensity=glass?2.43:.29;amb.intensity=glass?.67:.62;
    let origin=V(0,0,0);
    if (live) {
      const p=animal.update(t);
      origin.set(p.x,p.y,0);
      if(kind==='step'){
        const {at}=p.limb[0];
        origin.set(mix(at[0],p.x-1.075,.32),mix(at[1],p.y+.66,.34),at[2]*.30);
      }
      place.update(t,glass);
      shadowBody.visible=!glass;
      shadowBody.position.set(p.x-.095,p.y-.27,.008);shadowBody.rotation.z=-.06*Math.sin(p.c*3.8);
      feet.forEach((shadow,i)=>{
        const {at,curl,yaw}=p.limb[i];
        shadow.visible=!glass;
        shadow.position.set(at[0]+Math.sin(yaw)*(.23-.11*curl),at[1]+Math.cos(yaw)*(.23-.11*curl),.006);
        shadow.rotation.z=-yaw;shadow.material.opacity=.39-.30*clamp(at[2]/.30);shadow.scale.setScalar(1+.44*clamp(at[2]/.30));
      });
    } else if (microscope) field(t,kind,cut.marks);
    else pad(t,kind,cut);
    const {p,q,a,b,mm,aperture,roll,up}=cams[kind];
    cam.up.set(...up);
    frame(cam,progress,[V(...p).add(origin),V(...q).add(origin)],[V(...a).add(origin),V(...b).add(origin)],null,{mm,aperture,roll,bloom:kind==='eye'?.64:.44,exposure:microscope?.99:1.07,smear:kind==='step'?.69:0});
  }
  return {scene,cam,update,usesLens:(kind)=>lensShots.has(kind)};
}
