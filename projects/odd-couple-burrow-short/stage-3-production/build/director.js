import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { createImaxOpticalPass } from '/tools/monarch-v6-imax-sdk/core/postfx_imax_sdk.js';

const _params = new URLSearchParams(location.search);
const W = parseInt(_params.get('w') || '1080', 10);
const H = parseInt(_params.get('h') || '1920', 10);
const ASPECT = W / H;
const S = W / 1080; // scale factor for HUD/captions

const FPS = 30;
const DUR = 29.94;
const TOTAL_FRAMES = Math.round(DUR * FPS);

const CAPTIONS = [
  [0.00, 2.80, 'THIS ROCK'],
  [0.35, 2.80, 'HOLDS TWO ANIMALS'],
  [3.00, 5.80, '250 MILLION YEARS AGO'],
  [4.20, 5.80, 'ONE CURLED UP ASLEEP'],
  [6.00, 8.80, 'MAMMAL RELATIVE'],
  [7.20, 8.80, 'BESIDE AN AMPHIBIAN'],
  [9.10, 10.90, 'WAIT.'],
  [9.60, 10.90, 'NOT ENEMIES'],
  [11.00, 14.80, 'RIBS HEALING'],
  [12.20, 14.80, 'NO BITE MARKS'],
  [15.00, 16.80, 'NOT A HUNT'],
  [17.00, 19.80, 'LIKELY STORY'],
  [18.00, 19.80, 'CRAWLED IN FOR SHELTER'],
  [20.00, 23.80, 'PROBABLY AESTIVATION'],
  [21.20, 23.80, 'DEEP DORMANCY'],
  [24.00, 27.80, 'FLOOD FILLED BURROW'],
  [25.50, 27.80, 'SEALED THEM'],
  [28.00, 30.80, 'THE CLUE THE ROCK KEPT'],
  [31.00, 33.00, 'THIS ROCK'],
  [31.30, 33.00, 'HOLDS TWO ANIMALS'],
];

function clamp01(x){ return Math.max(0, Math.min(1, x)); }
function smoothstep(a,b,x){ const t=clamp01((x-a)/(b-a)); return t*t*(3-2*t); }
function lerp(a,b,t){ return a+(b-a)*t; }
function easeOut(t){ t=clamp01(t); return 1-Math.pow(1-t,3); }
function easeInOut(t){ t=clamp01(t); return t<0.5 ? 4*t*t*t : 1-Math.pow(-2*t+2,3)/2; }

function makeCanvasTexture(draw, w=512, h=512, opts={}){
  const c=document.createElement('canvas'); c.width=w; c.height=h;
  const ctx=c.getContext('2d');
  draw(ctx,w,h);
  const tex=new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = opts.wrap ?? THREE.RepeatWrapping;
  tex.repeat.set(opts.rx??1, opts.ry??1);
  tex.colorSpace = opts.colorSpace ?? THREE.SRGBColorSpace;
  if(opts.aniso) tex.anisotropy = opts.aniso;
  return tex;
}

function buildRockTextures(){
  const albedo = makeCanvasTexture((ctx,w,h)=>{
    ctx.fillStyle='#5a5248'; ctx.fillRect(0,0,w,h);
    for(let i=0;i<9000;i++){
      const x=Math.random()*w, y=Math.random()*h, r=Math.random()*2.8+0.2;
      const v = Math.floor(40+Math.random()*90);
      ctx.fillStyle = Math.random()>0.5 ? `rgba(${v+40},${v+30},${v+20},${0.08+Math.random()*0.12})` : `rgba(${20},${18},${16},${0.08+Math.random()*0.18})`;
      ctx.beginPath(); ctx.arc(x,y,r,0,Math.PI*2); ctx.fill();
    }
    for(let i=0;i<120;i++){
      ctx.strokeStyle=`rgba(20,15,10,${0.03+Math.random()*0.08})`;
      ctx.lineWidth=0.5+Math.random()*2.5;
      ctx.beginPath();
      let x=Math.random()*w, y=Math.random()*h;
      ctx.moveTo(x,y);
      for(let s=0;s<6;s++){ x+= (Math.random()-0.5)*120; y+= (Math.random()-0.5)*80; ctx.lineTo(x,y); }
      ctx.stroke();
    }
  }, 1024,1024,{rx:2.2,ry:1.4});
  const roughness = makeCanvasTexture((ctx,w,h)=>{
    ctx.fillStyle='#b8b0a8'; ctx.fillRect(0,0,w,h);
    for(let i=0;i<6000;i++){
      const v=Math.floor(120+Math.random()*120);
      ctx.fillStyle=`rgb(${v},${v},${v})`;
      ctx.fillRect(Math.random()*w,Math.random()*h,1+Math.random()*3,1+Math.random()*3);
    }
  },512,512,{rx:2.2,ry:1.4,colorSpace:THREE.NoColorSpace});
  const normal = makeCanvasTexture((ctx,w,h)=>{
    ctx.fillStyle='#8080ff'; ctx.fillRect(0,0,w,h);
    for(let i=0;i<5000;i++){
      const x=Math.random()*w,y=Math.random()*h,r=Math.random()*3+0.5;
      const nx=128+Math.floor((Math.random()-0.5)*30);
      const ny=128+Math.floor((Math.random()-0.5)*30);
      ctx.fillStyle=`rgb(${nx},${ny},255)`;
      ctx.beginPath(); ctx.arc(x,y,r,0,Math.PI*2); ctx.fill();
    }
  },512,512,{rx:2.2,ry:1.4,colorSpace:THREE.NoColorSpace});
  return {albedo, roughness, normal};
}

function buildBoneTextures(){
  const albedo = makeCanvasTexture((ctx,w,h)=>{
    ctx.fillStyle='#cfc2a8'; ctx.fillRect(0,0,w,h);
    for(let i=0;i<5000;i++){
      const v=Math.floor(150+Math.random()*80);
      ctx.fillStyle=`rgba(${v},${v-20},${v-45},${0.05+Math.random()*0.08})`;
      ctx.fillRect(Math.random()*w,Math.random()*h,1+Math.random()*4,1+Math.random()*2);
    }
  },512,512,{rx:1,ry:1});
  const roughness = makeCanvasTexture((ctx,w,h)=>{
    ctx.fillStyle='#9a9388'; ctx.fillRect(0,0,w,h);
    for(let i=0;i<3000;i++){
      const v=Math.floor(100+Math.random()*120); ctx.fillStyle=`rgb(${v},${v},${v})`;
      ctx.fillRect(Math.random()*w,Math.random()*h,2,2);
    }
  },256,256,{colorSpace:THREE.NoColorSpace});
  return {albedo, roughness};
}

function createRockMaterial(tex){
  return new THREE.MeshStandardMaterial({
    map: tex.albedo,
    roughnessMap: tex.roughness,
    normalMap: tex.normal,
    normalScale: new THREE.Vector2(0.55,0.55),
    roughness: 1.0,
    metalness: 0.02,
    color: new THREE.Color('#8a7e70'),
  });
}

function createBoneMaterial(tex, tint='#d8ccb4', emissive='#000000', emissiveIntensity=0){
  return new THREE.MeshStandardMaterial({
    map: tex.albedo,
    roughnessMap: tex.roughness,
    roughness: 0.72,
    metalness: 0.03,
    color: new THREE.Color(tint),
    emissive: new THREE.Color(emissive),
    emissiveIntensity,
  });
}

function buildBetterSkeleton(boneTex, {scale=1, tint='#d8ccb4', accent='#c0b090', curl=0}={}){
  const g = new THREE.Group();
  const mat = createBoneMaterial(boneTex, tint, '#000', 0);
  const darkMat = createBoneMaterial(boneTex, accent, '#000', 0);

  const skullGeo = new THREE.SphereGeometry(0.52*scale, 24, 20);
  skullGeo.scale(1.25, 0.95, 1.0);
  const skull = new THREE.Mesh(skullGeo, mat);
  skull.position.set(1.75*scale, 0.28*scale, 0);
  skull.castShadow = false; skull.receiveShadow = true; g.add(skull);

  const snout = new THREE.Mesh(new THREE.BoxGeometry(0.75*scale, 0.32*scale, 0.55*scale), mat);
  snout.position.set(2.25*scale, 0.12*scale, 0); g.add(snout);
  const jaw = new THREE.Mesh(new THREE.BoxGeometry(0.72*scale, 0.14*scale, 0.5*scale), darkMat);
  jaw.position.set(2.15*scale, -0.08*scale, 0); g.add(jaw);
  for(let s of [-1,1]){
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.09*scale,12,10), new THREE.MeshStandardMaterial({color:'#1a1510', roughness:1}));
    eye.position.set(1.95*scale, 0.32*scale, s*0.28*scale); g.add(eye);
  }

  const spineCount = 18;
  for(let i=0;i<spineCount;i++){
    const t=i/(spineCount-1);
    const r = lerp(0.22,0.14,Math.abs(t-0.5)*1.2)*scale;
    const v = new THREE.Mesh(new THREE.SphereGeometry(r,12,10), i%2?mat:darkMat);
    const x = lerp(1.3,-1.6,t)*scale;
    const y = (0.12 - curl*Math.sin(t*Math.PI)*0.35 + Math.sin(t*Math.PI)*0.05)*scale;
    v.position.set(x,y,0); v.scale.set(1.2,0.9,1.1);
    g.add(v);
  }

  for(let i=0;i<10;i++){
    const t=i/9;
    const x = lerp(1.05,-0.65,t)*scale;
    const R = (0.48 - Math.abs(t-0.45)*0.22)*scale;
    const rib = new THREE.Mesh(new THREE.TorusGeometry(R, 0.038*scale, 8, 28, Math.PI*1.15), mat);
    rib.rotation.y = Math.PI/2; rib.rotation.z = Math.PI;
    rib.position.set(x, -0.02*scale, 0);
    g.add(rib);
  }

  const pelvis = new THREE.Mesh(new THREE.BoxGeometry(0.55*scale, 0.22*scale, 0.75*scale), darkMat);
  pelvis.position.set(-0.95*scale, 0.0, 0); g.add(pelvis);

  const limbMat = mat;
  function limb(px,py,pz,rx,rz,len,thick){
    const upper = new THREE.Mesh(new THREE.CapsuleGeometry(thick*scale, len*0.55*scale,6,12), limbMat);
    upper.position.set(px*scale,py*scale,pz*scale); upper.rotation.z=rz; upper.rotation.x=rx; g.add(upper);
    const lower = new THREE.Mesh(new THREE.CapsuleGeometry(thick*0.75*scale, len*0.45*scale,6,12), limbMat);
    lower.position.set((px+Math.sin(rz)*len*0.35)*scale, (py-len*0.45)*scale, pz*scale); lower.rotation.z=rz*0.5; g.add(lower);
  }
  limb(0.75,-0.25,0.42,0.2,0.55,0.9,0.085);
  limb(0.75,-0.25,-0.42,-0.2,-0.55,0.9,0.085);
  limb(-0.95,-0.22,0.45,0.15,0.35,0.95,0.095);
  limb(-0.95,-0.22,-0.45,-0.15,-0.35,0.95,0.095);

  for(let i=0;i<12;i++){
    const t=i/11;
    const r=lerp(0.12,0.03,t)*scale;
    const seg=new THREE.Mesh(new THREE.SphereGeometry(r,10,8), i%2?mat:darkMat);
    seg.position.set((-1.3-t*1.5)*scale, (-0.05-t*0.35*curl - t*0.1)*scale, 0);
    seg.scale.x=1.4; g.add(seg);
  }

  g.traverse(o=>{ if(o.isMesh){ o.castShadow=false; o.receiveShadow=true; }});
  return g;
}

function buildBurrow(rockTex){
  const g = new THREE.Group();
  const rockMat = createRockMaterial(rockTex);

  const outer = new THREE.Mesh(new THREE.CylinderGeometry(3.8,4.0,16,48,1,true), rockMat);
  outer.rotation.z = Math.PI/2; outer.receiveShadow=true; g.add(outer);

  const innerMat = new THREE.MeshStandardMaterial({color:'#1a1512', roughness:1, metalness:0, side:THREE.BackSide});
  const inner = new THREE.Mesh(new THREE.CylinderGeometry(2.85,3.05,15.5,48,1,true), innerMat);
  inner.rotation.z = Math.PI/2; inner.receiveShadow=true; g.add(inner);

  const floorMat = new THREE.MeshStandardMaterial({color:'#2b231c', roughness:1, metalness:0, map:rockTex.albedo});
  const floor = new THREE.Mesh(new THREE.BoxGeometry(15.5,0.7,5.2), floorMat);
  floor.position.y = -2.55; floor.receiveShadow=true; g.add(floor);

  const backMat = new THREE.MeshStandardMaterial({color:'#15110e', roughness:1, metalness:0});
  const back = new THREE.Mesh(new THREE.PlaneGeometry(18,10), backMat);
  back.position.set(0,0.5,-2.8); back.receiveShadow=true; g.add(back);

  for(let i=0;i<7;i++){
    const slab = new THREE.Mesh(new THREE.BoxGeometry(1.8+Math.random()*1.4,0.25,1.2+Math.random()), rockMat);
    slab.position.set(-5+i*1.7, 2.5+Math.random()*0.3, -0.2+Math.random()*0.5);
    slab.rotation.z = (Math.random()-0.5)*0.3;
    slab.rotation.x = (Math.random()-0.5)*0.2;
    g.add(slab);
  }

  for(let i=0;i<18;i++){
    const d = new THREE.Mesh(new THREE.DodecahedronGeometry(0.08+Math.random()*0.22,0), rockMat);
    d.position.set(-5+Math.random()*10, -2.2+Math.random()*0.15, -1.5+Math.random()*3);
    d.rotation.set(Math.random()*2,Math.random()*2,Math.random()*2);
    g.add(d);
  }

  const shellMat = new THREE.MeshStandardMaterial({color:'#6b6156', roughness:0.85, metalness:0.05, transparent:true, opacity:0.18, side:THREE.DoubleSide});
  const shell = new THREE.Mesh(new THREE.CylinderGeometry(4.05,4.25,16.2,48,1,true), shellMat);
  shell.rotation.z = Math.PI/2; shell.renderOrder=5; g.add(shell);
  g.userData.shell = shell;
  return g;
}

function makeLabelSprite(text, color='#ffffff'){
  const c=document.createElement('canvas'); c.width=512; c.height=128;
  const ctx=c.getContext('2d');
  ctx.clearRect(0,0,512,128);
  ctx.fillStyle='rgba(10,12,16,0.62)'; ctx.strokeStyle=color; ctx.lineWidth=5;
  const rr=18; ctx.beginPath(); ctx.moveTo(16+rr,24); ctx.arcTo(496,24,496,104,rr); ctx.arcTo(496,104,16,104,rr); ctx.arcTo(16,104,16,24,rr); ctx.arcTo(16,24,496,24,rr); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle=color; ctx.font='700 34px Arial, sans-serif'; ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillText(text,256,66);
  const tex=new THREE.CanvasTexture(c); tex.colorSpace=THREE.SRGBColorSpace;
  const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:tex, transparent:true, opacity:0, depthTest:false, depthWrite:false}));
  sp.scale.set(2.8,0.7,1); sp.renderOrder=30; return sp;
}

export async function director({ mode='play', startFrame=0, endFrame=TOTAL_FRAMES-1 }={}){
  const renderer = new THREE.WebGLRenderer({ antialias:true, powerPreference:'high-performance', preserveDrawingBuffer:true });
  renderer.setPixelRatio(1);
  renderer.setSize(W,H,false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  renderer.shadowMap.enabled = false;
  renderer.autoClear = true;
  document.body.style.margin='0'; document.body.style.background='#000'; document.body.style.overflow='hidden';
  document.body.appendChild(renderer.domElement);
  renderer.domElement.style.width='100vw'; renderer.domElement.style.height='100vh'; renderer.domElement.style.objectFit='contain';

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#030506');
  scene.fog = new THREE.FogExp2('#070b0f', 0.024);

  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

  const camera = new THREE.PerspectiveCamera(34, ASPECT, 0.08, 120);
  camera.position.set(0,1.8,18);

  const amb = new THREE.AmbientLight(0x7fb0c8, 0.22); scene.add(amb);
  const key = new THREE.DirectionalLight(0xffb36a, 5.8);
  key.position.set(7,8,6); scene.add(key);
  const fill = new THREE.DirectionalLight(0x5aaed4, 0.9);
  fill.position.set(-6,3,5); scene.add(fill);
  const rim = new THREE.DirectionalLight(0x7fdcff, 3.8);
  rim.position.set(-4,5,-6); scene.add(rim);
  const top = new THREE.PointLight(0xffe0b0, 35, 30, 2);
  top.position.set(0,4.5,2); scene.add(top);
  const warmBounce = new THREE.PointLight(0xff8a3d, 18, 18, 2);
  warmBounce.position.set(3,-1.2,3); scene.add(warmBounce);
  const coolBack = new THREE.PointLight(0x4fc3ff, 22, 25, 2);
  coolBack.position.set(-3,1.5,-4); scene.add(coolBack);

  const rockTex = buildRockTextures();
  const boneTex = buildBoneTextures();

  const root = new THREE.Group(); scene.add(root);
  const burrow = buildBurrow(rockTex); root.add(burrow);

  const contact = new THREE.Mesh(new THREE.PlaneGeometry(16,8), new THREE.MeshBasicMaterial({color:'#000', transparent:true, opacity:0.35}));
  contact.rotation.x = -Math.PI/2; contact.position.y = -2.49; contact.position.z=0.2; root.add(contact);

  const thrin = buildBetterSkeleton(boneTex, {scale:0.82, tint:'#dce7df', accent:'#a8b8ae', curl:0.85});
  thrin.position.set(-1.5,-1.35,0.15); thrin.rotation.y = 0.35; thrin.rotation.z = 0.1;
  root.add(thrin);

  const amph = buildBetterSkeleton(boneTex, {scale:0.95, tint:'#e4c89d', accent:'#bfa072', curl:0.15});
  amph.position.set(1.95,-1.45,-0.15); amph.rotation.y = Math.PI + 0.15;
  root.add(amph);

  const healGroup = new THREE.Group();
  for(let i=0;i<3;i++){
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.16,0.022,10,28), new THREE.MeshBasicMaterial({color:0x7fffd4, transparent:true, opacity:0, blending:THREE.AdditiveBlending, depthWrite:false}));
    ring.position.set(1.45-i*0.28,-0.95,0.38); ring.rotation.y=Math.PI/2; healGroup.add(ring);
  }
  root.add(healGroup);

  const sweep = new THREE.Mesh(new THREE.PlaneGeometry(0.22,7.5), new THREE.MeshBasicMaterial({color:0x7fdcff, transparent:true, opacity:0, blending:THREE.AdditiveBlending, depthWrite:false}));
  sweep.position.set(-7,0,2.4); sweep.renderOrder=20; root.add(sweep);

  const shaftMat = new THREE.MeshBasicMaterial({color:0xffcc88, transparent:true, opacity:0.045, blending:THREE.AdditiveBlending, depthWrite:false, side:THREE.DoubleSide});
  const shaft = new THREE.Mesh(new THREE.ConeGeometry(2.2,7,32,1,true), shaftMat);
  shaft.position.set(2.5,2.8,0.5); shaft.rotation.z = Math.PI; shaft.rotation.x=0.2; root.add(shaft);

  const shaft2 = new THREE.Mesh(new THREE.ConeGeometry(1.6,6,32,1,true), new THREE.MeshBasicMaterial({color:0x88d7ff, transparent:true, opacity:0.025, blending:THREE.AdditiveBlending, depthWrite:false, side:THREE.DoubleSide}));
  shaft2.position.set(-2.8,2.5,-0.5); shaft2.rotation.z=Math.PI; shaft2.rotation.x=-0.15; root.add(shaft2);

  const dustCount=260;
  const dustGeo=new THREE.BufferGeometry();
  const dp=new Float32Array(dustCount*3); const ds=new Float32Array(dustCount);
  for(let i=0;i<dustCount;i++){ dp[i*3]=(Math.random()-0.5)*12; dp[i*3+1]=-2+Math.random()*5.5; dp[i*3+2]=(Math.random()-0.5)*4.5; ds[i]=0.3+Math.random()*0.7; }
  dustGeo.setAttribute('position', new THREE.BufferAttribute(dp,3));
  const dustMat=new THREE.PointsMaterial({color:0xd9e7f0, size:0.035, transparent:true, opacity:0.35, depthWrite:false, blending:THREE.AdditiveBlending});
  const dust=new THREE.Points(dustGeo,dustMat); root.add(dust);

  const floodCount=700;
  const floodGeo=new THREE.BufferGeometry();
  const fp=new Float32Array(floodCount*3); const fv=new Float32Array(floodCount);
  for(let i=0;i<floodCount;i++){ fp[i*3]=(Math.random()-0.5)*9; fp[i*3+1]=3.5+Math.random()*4; fp[i*3+2]=(Math.random()-0.5)*3.5; fv[i]=0.5+Math.random()*1.5; }
  floodGeo.setAttribute('position', new THREE.BufferAttribute(fp,3));
  const floodMat=new THREE.PointsMaterial({color:0x7fb6d8, size:0.055, transparent:true, opacity:0, depthWrite:false});
  const flood=new THREE.Points(floodGeo,floodMat); root.add(flood);

  const lblInference = makeLabelSprite('INFERENCE','#ffd187'); lblInference.position.set(2.2,1.9,1.2); root.add(lblInference);
  const lblPlausible = makeLabelSprite('MOST PLAUSIBLE','#88f4ee'); lblPlausible.position.set(-1.4,2.2,1.0); root.add(lblPlausible);
  const lblNoBite = makeLabelSprite('NO BITE MARKS','#7fffd4'); lblNoBite.position.set(2.6,0.45,1.6); root.add(lblNoBite);

  const hudCanvas=document.createElement('canvas'); hudCanvas.width=W; hudCanvas.height=H;
  const hudCtx=hudCanvas.getContext('2d');
  const hudTex=new THREE.CanvasTexture(hudCanvas); hudTex.colorSpace=THREE.SRGBColorSpace;
  const hudScene=new THREE.Scene(); const hudCam=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
  const hudQuad=new THREE.Mesh(new THREE.PlaneGeometry(2,2), new THREE.MeshBasicMaterial({map:hudTex,transparent:true,depthTest:false,depthWrite:false}));
  hudScene.add(hudQuad);

  const postfx = createImaxOpticalPass(renderer, W, H);

  function drawCaption(t){
    hudCtx.clearRect(0,0,W,H);
    const active=CAPTIONS.filter(c=>t>=c[0] && t<=c[1]).slice(-2);
    hudCtx.textAlign='center'; hudCtx.textBaseline='middle';
    active.forEach((c,i)=>{
      const y=(1525*S) - (active.length-1-i)*(78*S);
      const a=Math.min(1, (t-c[0])*5, (c[1]-t)*5);
      hudCtx.globalAlpha=Math.max(0,a);
      const pop = 1 + 0.08*Math.max(0, 1-(t-c[0])*4);
      hudCtx.save();
      hudCtx.translate(W/2, y);
      hudCtx.scale(pop, pop);
      hudCtx.font=`900 ${Math.round(58*S)}px Arial Black, Arial, sans-serif`;
      hudCtx.lineJoin='round'; hudCtx.strokeStyle='rgba(0,0,0,0.85)'; hudCtx.lineWidth=14*S;
      hudCtx.strokeText(c[2],0,0);
      const grad = hudCtx.createLinearGradient(-220*S,0,220*S,0);
      if(c[2].includes('WAIT') || c[2].includes('NOT')){ grad.addColorStop(0,'#ff6b6b'); grad.addColorStop(1,'#ffd1d1'); }
      else { grad.addColorStop(0,'#fff3d4'); grad.addColorStop(0.5,'#ffffff'); grad.addColorStop(1,'#9fe7ff'); }
      hudCtx.fillStyle = grad;
      hudCtx.fillText(c[2],0,0);
      hudCtx.restore();
    });
    hudCtx.globalAlpha=1;
  }

  function setPose(t){
    const xray = smoothstep(2.5,3.5,t) * (1-smoothstep(10.5,11.2,t)) + smoothstep(11.0,12.0,t)*0.35*(1-smoothstep(27.5,28.5,t));
    burrow.userData.shell.material.opacity = lerp(0.18, 0.04, xray);
    burrow.userData.shell.material.emissive = new THREE.Color(0x1a3a44);
    burrow.userData.shell.material.emissiveIntensity = xray*0.6;

    thrin.traverse(o=>{ if(o.isMesh && o.material.emissive){ o.material.emissive.set('#1b4d5a'); o.material.emissiveIntensity = 0.12*xray; }});
    amph.traverse(o=>{ if(o.isMesh && o.material.emissive){ o.material.emissive.set('#5a3a1b'); o.material.emissiveIntensity = 0.10*xray; }});

    const sweepA = (t>2.5 && t<6.5) ? 0.55 : (t>28.5 ? 0.5 : 0);
    sweep.material.opacity = sweepA;
    const sweepT = (t>28.5) ? smoothstep(28.5,29.9,t) : ((t%3)/3);
    sweep.position.x = lerp(-6.5,6.5, sweepT);

    const pulse = Math.exp(-Math.pow((t-9.6)*3.2,2));
    root.scale.setScalar(1 + pulse*0.012);

    const healA = smoothstep(11.0,11.8,t)*(1-smoothstep(14.8,15.5,t));
    healGroup.children.forEach((m,i)=>{ m.material.opacity=healA*(0.65+0.35*Math.sin(t*6+i)); m.scale.setScalar(1+0.06*Math.sin(t*5+i)); });
    lblNoBite.material.opacity = smoothstep(11.2,11.8,t)*(1-smoothstep(14.5,15.2,t));

    lblInference.material.opacity = smoothstep(17.2,17.8,t)*(1-smoothstep(19.6,20.2,t));
    lblPlausible.material.opacity = smoothstep(20.2,20.8,t)*(1-smoothstep(23.6,24.2,t));

    const floodA = smoothstep(24.0,24.8,t)*(1-smoothstep(27.8,28.2,t));
    flood.material.opacity = floodA*0.75;
    const pos=flood.geometry.attributes.position.array;
    for(let i=0;i<floodCount;i++){
      if(floodA>0.001){
        pos[i*3+1] -= 0.018*fv[i]*(1+floodA*2.2);
        if(pos[i*3+1] < -2.1) pos[i*3+1] = -2.1 + Math.random()*0.25;
      } else {
        pos[i*3+1] = 3.5+Math.random()*4;
      }
    }
    flood.geometry.attributes.position.needsUpdate=true;

    const dpos=dust.geometry.attributes.position.array;
    for(let i=0;i<dustCount;i++){
      dpos[i*3] += Math.sin(t*0.2+i)*0.0008;
      dpos[i*3+1] += Math.cos(t*0.15+i*0.7)*0.0005;
      if(dpos[i*3]>6.5) dpos[i*3]=-6.5;
      if(dpos[i*3]<-6.5) dpos[i*3]=6.5;
    }
    dust.geometry.attributes.position.needsUpdate=true;

    amph.visible = t > 5.2;
    if(t>17 && t<20){
      const k=easeInOut(smoothstep(17,19.5,t));
      amph.position.x = lerp(4.8,1.95,k);
      amph.position.z = lerp(1.0,-0.15,k);
    } else if(t>=20){
      amph.position.x = 1.95; amph.position.z = -0.15;
    }

    thrin.position.y = -1.35 + Math.sin(t*1.1)*0.008;
    thrin.rotation.z = 0.1 + Math.sin(t*0.7)*0.003;
    if(amph.visible) amph.position.y = -1.45 + Math.sin(t*0.8+1.0)*0.005;

    shaftMat.opacity = 0.035 + 0.02*Math.sin(t*0.4) + xray*0.02;
  }

  function setCamera(t){
    let pos=new THREE.Vector3(0,1.7,18), look=new THREE.Vector3(0,-0.4,0), fov=34;
    if(t<3){
      const k=easeOut(smoothstep(0,3,t));
      pos.set(lerp(0.6,0.2,k), lerp(0.9,0.75,k), lerp(11.5,10.2,k));
      look.set(0,-0.75,0); fov=31;
    } else if(t<6){
      const k=smoothstep(3,6,t);
      pos.set(lerp(-2.2,-1.4,k), -0.45, lerp(7.2,6.6,k));
      look.set(-1.45,-1.15,0.1); fov=29;
    } else if(t<9){
      const k=easeInOut(smoothstep(6,9,t));
      pos.set(lerp(-1.0,1.6,k), lerp(0.1,0.35,k), lerp(8.2,8.8,k));
      look.set(lerp(-1.0,0.4,k), -0.9, 0); fov=33;
    } else if(t<11){
      const k=easeInOut(smoothstep(9,10.8,t));
      pos.set(lerp(0.8,0.0,k), lerp(0.5,0.7,k), lerp(8.5,5.6,k));
      look.set(0.1,-0.8,0); fov=lerp(32,54,k);
    } else if(t<15){
      const k=smoothstep(11,15,t);
      pos.set(lerp(2.6,2.0,k), -0.55, lerp(5.2,4.6,k));
      look.set(1.5,-0.95,0.35); fov=27;
    } else if(t<17){
      pos.set(0.0,0.7,12.0); look.set(0,-0.7,0); fov=37;
    } else if(t<20){
      const k=smoothstep(17,20,t);
      pos.set(lerp(3.2,2.2,k), 0.6, 9.2);
      look.set(lerp(2.5,1.2,k), -0.8, 0); fov=33;
    } else if(t<24){
      const k=smoothstep(20,24,t);
      pos.set(lerp(-2.8,-1.8,k), 0.7, 8.6);
      look.set(-1.4,-1.0,0); fov=31;
    } else if(t<28){
      const k=smoothstep(24,28,t);
      pos.set(lerp(0.3,-0.2,k), lerp(1.6,1.1,k), lerp(10.2,9.2,k));
      look.set(0,-0.7,0); fov=35;
    } else {
      const k=easeInOut(smoothstep(28,29.94,t));
      pos.set(lerp(-0.2,0.2,k), lerp(1.1,0.8,k), lerp(9.2,10.5,k));
      look.set(0,-0.75,0); fov=lerp(34,31,k);
    }

    const driftX = Math.sin(t*0.7)*0.015 + Math.sin(t*1.9)*0.005;
    const driftY = Math.cos(t*0.6)*0.012 + Math.sin(t*1.3)*0.004;
    pos.x += driftX; pos.y += driftY;

    camera.position.copy(pos);
    camera.lookAt(look);
    camera.fov = fov;
    camera.updateProjectionMatrix();
  }

  const _mVec = new THREE.Vector2();
  function renderFrame(f){
    const t = Math.min(DUR, f/FPS);
    setPose(t);
    const prevP = camera.position.clone();
    setCamera(t);
    _mVec.set((prevP.x-camera.position.x)*0.002, (prevP.y-camera.position.y)*0.002);

    const impact = Math.exp(-Math.pow((t-9.6)*5.5,2)) + Math.exp(-Math.pow((t-24.2)*4.0,2))*0.6;
    const shakeAmt = impact * 0.012;
    camera.position.x += (Math.sin(t*60)*shakeAmt);
    camera.position.y += (Math.cos(t*55)*shakeAmt);
    camera.updateProjectionMatrix();

    const params = {
      focusDist: camera.position.distanceTo(new THREE.Vector3(0,-0.8,0)),
      dofRange: 18.0,
      maxBlur: 2.8,
      bloomAmt: 0.62 + impact*0.25,
      exposure: 1.08 + impact*0.08,
      time: t,
      motionVec: _mVec,
    };
    postfx.render(scene, camera, params);

    drawCaption(t);
    hudTex.needsUpdate = true;
    renderer.autoClear = false;
    renderer.clearDepth();
    renderer.render(hudScene, hudCam);
    renderer.autoClear = true;
  }

  const gl = renderer.getContext();
  const pixelBuf = new Uint8Array(W * H * 4);
  let activeWS = null;
  let wsWaitResolve = null;

  window.renderFramePNG = (f, hudOpts={}) => {
    renderFrame(f);
    return renderer.domElement.toDataURL('image/png');
  };

  window.renderCoverPNG = () => {
    renderFrame(30);
    hudCtx.save();
    hudCtx.fillStyle='rgba(0,0,0,0.38)'; hudCtx.fillRect(0,0,W,520*S);
    hudCtx.textAlign='center';
    hudCtx.fillStyle='#fff5e0'; hudCtx.font=`900 ${Math.round(92*S)}px Arial Black, Arial`;
    hudCtx.fillText('ODD COUPLE',W/2,210*S);
    hudCtx.font=`800 ${Math.round(52*S)}px Arial Black, Arial`; hudCtx.fillStyle='#88e6ff';
    hudCtx.fillText('250 MILLION YEARS',W/2,300*S);
    hudCtx.font=`600 ${Math.round(36*S)}px Arial, sans-serif`; hudCtx.fillStyle='#ffd187';
    hudCtx.fillText('A burrow. Two animals. One clue.',W/2,380*S);
    hudCtx.restore();
    hudTex.needsUpdate=true;
    renderer.autoClear=false; renderer.clearDepth(); renderer.render(hudScene,hudCam); renderer.autoClear=true;
    return renderer.domElement.toDataURL('image/png');
  };

  window.connectRawWS = (wsPort, workerId) => new Promise((resolve, reject) => {
    const ws = new WebSocket(`ws://127.0.0.1:${wsPort}/?w=${workerId}`);
    ws.binaryType='arraybuffer';
    ws.onmessage = () => { if(wsWaitResolve){ const r=wsWaitResolve; wsWaitResolve=null; r(); } };
    ws.onopen = () => { activeWS=ws; resolve(true); };
    ws.onerror = (e) => reject(e);
  });

  window.streamFramesWS = async (fStart, fEnd) => {
    if (fStart > 0) renderFrame(fStart - 1);
    for (let f=fStart; f<fEnd; f++) {
      renderFrame(f);
      gl.readPixels(0,0,W,H,gl.RGBA,gl.UNSIGNED_BYTE,pixelBuf);
      await new Promise((res)=>{ wsWaitResolve=res; activeWS.send(pixelBuf); });
    }
  };

  window.__IMAX_READY__ = true;
  window.__SHORT_V6_READY__ = true;

  for (let i=0; i<3; i++) renderFrame(i);

  if(mode==='play'){
    let frame=startFrame;
    function loop(){
      renderFrame(frame);
      frame=(frame+1)%TOTAL_FRAMES;
      requestAnimationFrame(loop);
    }
    loop();
  } else {
    renderFrame(startFrame);
  }

  return { evaluateFrame: renderFrame, TOTAL_FRAMES, FPS, DUR };
}
