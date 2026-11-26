import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

export function createDirector({ THREE, scene, camera, renderer, W, H }) {
  const FPS = 30, TOTAL_FRAMES = 1050, DUR = TOTAL_FRAMES / FPS;
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const lerp=(a,b,t)=>a+(b-a)*t;
  const smooth=(t)=>{t=clamp(t,0,1); return t*t*(3-2*t);};
  const easeOut=(t)=>1-Math.pow(1-clamp(t,0,1),4);
  const easeInOut=(t)=>{t=clamp(t,0,1); return t<0.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;};
  const easeIn=(t)=>{t=clamp(t,0,1); return t*t*t;};
  const hash1=(n)=>{ const x=Math.sin(n*127.1)*43758.5453123; return x-Math.floor(x); };
  const noise1=(n)=>{ const i=Math.floor(n), f=n-i; const u=f*f*(3-2*f); return lerp(hash1(i),hash1(i+1),u); };

  scene.background = new THREE.Color(0x0a1018);
  scene.fog = new THREE.FogExp2(0x0b121a, 0.011);

  const amb = new THREE.AmbientLight(0xaec8e4, 0.55); scene.add(amb);
  const key = new THREE.DirectionalLight(0xffe2bb, 8.8);
  key.position.set(8, 11, 7); key.castShadow = true;
  key.shadow.mapSize.set(2048,2048);
  key.shadow.camera.left=-12; key.shadow.camera.right=12; key.shadow.camera.top=12; key.shadow.camera.bottom=-12;
  key.shadow.camera.near=0.5; key.shadow.camera.far=45; key.shadow.bias=-0.00025; key.shadow.normalBias=0.03;
  scene.add(key); scene.add(key.target);
  const rim = new THREE.DirectionalLight(0xa8dcff, 4.8); rim.position.set(-9,6,-8); scene.add(rim);
  const fill = new THREE.PointLight(0xffb06a, 4.2, 60); fill.position.set(0,3.8,5.8); scene.add(fill);
  const accent = new THREE.PointLight(0xff5530, 0, 35); accent.position.set(0,1.5,3); scene.add(accent);
  const coldFill = new THREE.PointLight(0x9fd4ff, 2.2, 45); coldFill.position.set(-3,1.4,-2.5); scene.add(coldFill);
  const moon = new THREE.SpotLight(0xcfe6ff, 0, 70, Math.PI*0.22, 0.45, 1.2);
  moon.position.set(2,8,4); moon.target.position.set(0,-0.2,0); moon.castShadow=true; scene.add(moon); scene.add(moon.target);
  const burrowFill = new THREE.PointLight(0xffd39a, 2.8, 18); burrowFill.position.set(0,0.8,1.8); scene.add(burrowFill);

  function makeCanvas(w,h,fn){ const c=document.createElement('canvas'); c.width=w; c.height=h; fn(c.getContext('2d'),w,h); return c; }
  function texFromCanvas(c, srgb=true){ const t=new THREE.CanvasTexture(c); t.wrapS=t.wrapT=THREE.RepeatWrapping; if(srgb) t.colorSpace=THREE.SRGBColorSpace; t.needsUpdate=true; return t; }
  function noiseTex(c1,c2,speck=5000,lines=40){
    return texFromCanvas(makeCanvas(256,256,(g,w,h)=>{
      g.fillStyle=c1; g.fillRect(0,0,w,h);
      for(let i=0;i<speck;i++){ const x=Math.random()*w,y=Math.random()*h; g.fillStyle=`rgba(0,0,0,${Math.random()*0.14})`; g.fillRect(x,y,1+Math.random()*2,1+Math.random()*2); }
      for(let i=0;i<speck*0.45;i++){ const x=Math.random()*w,y=Math.random()*h; g.fillStyle=`rgba(255,255,255,${Math.random()*0.08})`; g.fillRect(x,y,1,1); }
      g.strokeStyle=c2; g.globalAlpha=0.18; for(let i=0;i<lines;i++){ g.lineWidth=0.5+Math.random()*1.5; g.beginPath(); g.moveTo(Math.random()*w,Math.random()*h); g.bezierCurveTo(Math.random()*w,Math.random()*h,Math.random()*w,Math.random()*h,Math.random()*w,Math.random()*h); g.stroke(); }
    }));
  }
  function normalFromNoise(){
    return texFromCanvas(makeCanvas(256,256,(g,w,h)=>{
      g.fillStyle='#8080ff'; g.fillRect(0,0,w,h);
      for(let i=0;i<3500;i++){ const x=Math.random()*w,y=Math.random()*h,r=1+Math.random()*3; const nx=128+(Math.random()-0.5)*50, ny=128+(Math.random()-0.5)*50; g.fillStyle=`rgb(${nx|0},${ny|0},255)`; g.beginPath(); g.arc(x,y,r,0,Math.PI*2); g.fill(); }
    }), false);
  }

  const rockMap=noiseTex('#6b6254','#352f28',6000,55); rockMap.repeat.set(3,3);
  const rockN=normalFromNoise(); rockN.repeat.set(3,3);
  const soilMap=noiseTex('#4a392a','#241b14',5000,35); soilMap.repeat.set(3,3);
  const wetSoil=noiseTex('#2f241b','#1a140f',4000,20); wetSoil.repeat.set(3,3);

  const rootGroup=new THREE.Group(); scene.add(rootGroup);
  const env=new THREE.Group(); rootGroup.add(env);
  const burrow=new THREE.Group(); burrow.position.set(0,-0.1,0); rootGroup.add(burrow);
  const fx=new THREE.Group(); rootGroup.add(fx);

  const ground=new THREE.Mesh(new THREE.PlaneGeometry(90,90), new THREE.MeshStandardMaterial({color:'#171310', map:soilMap, roughness:1, metalness:0}));
  ground.rotation.x=-Math.PI/2; ground.position.y=-3.4; ground.receiveShadow=true; env.add(ground);

  const rockMat=new THREE.MeshStandardMaterial({color:'#7b7163', map:rockMap, normalMap:rockN, normalScale:new THREE.Vector2(1.1,1.1), roughness:0.95, metalness:0.02});
  const rockDark=new THREE.MeshStandardMaterial({color:'#433b32', map:soilMap, roughness:1, metalness:0.01});
  const rockWet=new THREE.MeshStandardMaterial({color:'#3a332c', map:wetSoil, roughness:0.55, metalness:0.03});

  function addBox(parent,geo,mat,x,y,z,rx=0,ry=0,rz=0){ const m=new THREE.Mesh(geo,mat); m.position.set(x,y,z); m.rotation.set(rx,ry,rz); m.castShadow=true; m.receiveShadow=true; parent.add(m); return m; }
  // rock slab
  addBox(env,new THREE.BoxGeometry(9.0,1.2,5.8),rockMat,0,-0.6,0);
  addBox(env,new THREE.BoxGeometry(8.0,0.55,5.0),rockMat,0.1,0.28,0.05);
  addBox(env,new THREE.BoxGeometry(6.8,0.35,4.2),rockDark,0.15,0.72,0.08);
  for(let i=0;i<10;i++){ addBox(env,new THREE.BoxGeometry(8.4-i*0.18,0.07,5.2-i*0.12), i%2?rockMat:rockDark, (Math.random()-0.5)*0.15, -1.0+i*0.19, 0.04, 0,0,0); }
  for(let i=0;i<45;i++){
    const s=0.15+Math.random()*1.1; const geo=Math.random()>0.45?new THREE.DodecahedronGeometry(s,0):new THREE.BoxGeometry(s*1.5,s,s*1.2);
    const m=new THREE.Mesh(geo, i%3===0?rockDark:rockMat);
    m.position.set((Math.random()-0.5)*10, -0.5+Math.random()*1.8, (Math.random()-0.5)*6.5);
    m.rotation.set(Math.random()*2,Math.random()*2,Math.random()*2); m.scale.y*=0.7+Math.random()*0.8;
    m.castShadow=true; m.receiveShadow=true; env.add(m);
  }
  // roots/cracks
  for(let i=0;i<10;i++){
    const r=new THREE.Mesh(new THREE.CylinderGeometry(0.03,0.06,2.2+Math.random()*2.2,6), new THREE.MeshStandardMaterial({color:'#2a2018', roughness:1}));
    r.position.set(-2.5+Math.random()*5,0.8+Math.random()*1.2,-1.2+Math.random()*2.4); r.rotation.z=(Math.random()-0.5)*1.2; r.rotation.x=(Math.random()-0.5)*0.8;
    r.castShadow=true; env.add(r);
  }

  const burrowShell = new THREE.Mesh(new THREE.CylinderGeometry(3.4,3.6,6.2,56,1,true,Math.PI*0.10,Math.PI*1.80), new THREE.MeshStandardMaterial({color:'#4a3f32', map:soilMap, roughness:1, metalness:0.01, transparent:true, opacity:0.28, side:THREE.DoubleSide}));
  burrowShell.rotation.z=Math.PI/2; burrowShell.rotation.y=Math.PI/2; burrowShell.position.set(0,-0.72,0.22);
  burrowShell.receiveShadow=true; burrow.add(burrowShell);
  const burrowFloor = new THREE.Mesh(new THREE.BoxGeometry(6.4,0.4,3.8), new THREE.MeshStandardMaterial({color:'#4a3a2a', map:soilMap, roughness:0.95}));
  burrowFloor.position.set(0,-1.15,0.25); burrowFloor.receiveShadow=true; burrow.add(burrowFloor);
  const burrowVoid = new THREE.Mesh(new THREE.SphereGeometry(2.5,32,20,0,Math.PI*2,0,Math.PI/2), new THREE.MeshBasicMaterial({color:'#0a0806', transparent:true, opacity:0.08}));
  burrowVoid.scale.set(1.4,0.62,1.12); burrowVoid.position.set(0,-0.66,0.28); burrow.add(burrowVoid);

  // Creature rig
  function buildCreature({main,belly,dark,amphibian=false,scale=1}){
    const g=new THREE.Group(); g.userData={amphibian};
    const mat=new THREE.MeshStandardMaterial({color:main, roughness:0.62, metalness:0.04, map:noiseTex(main,dark,3500,25), emissive:new THREE.Color(main), emissiveIntensity:0.18});
    const bMat=new THREE.MeshStandardMaterial({color:belly, roughness:0.76, metalness:0.01, emissive:new THREE.Color(belly), emissiveIntensity:0.12});
    const dMat=new THREE.MeshStandardMaterial({color:dark, roughness:0.85, metalness:0.02});
    const body=new THREE.Group(); g.add(body); g.userData.body=body;
    const segs=amphibian?8:7;
    for(let i=0;i<segs;i++){
      const t=i/(segs-1);
      const r=(amphibian?0.40:0.45)*Math.sin(t*Math.PI)*0.75 + (amphibian?0.20:0.24);
      const s=new THREE.Mesh(new THREE.SphereGeometry(r,22,18), mat);
      s.position.set(lerp(-0.82,0.82,t), Math.sin(t*Math.PI)*0.09-(amphibian?0.05:0), 0);
      s.scale.set(1.28, amphibian?0.70:0.84, 1.02); s.castShadow=true; s.receiveShadow=true; body.add(s);
    }
    const bellyMesh=new THREE.Mesh(new THREE.SphereGeometry(0.36,20,16), bMat);
    bellyMesh.scale.set(1.7, amphibian?0.34:0.44, 0.82); bellyMesh.position.set(0,-0.17,0.13); body.add(bellyMesh);
    const head=new THREE.Group(); head.position.set(1.0,0.08,0); g.add(head); g.userData.head=head;
    const skull=new THREE.Mesh(new THREE.SphereGeometry(0.22,20,16), mat); skull.scale.set(1.15,0.85,0.95); skull.castShadow=true; head.add(skull);
    const snout=new THREE.Mesh(new THREE.BoxGeometry(0.34,0.14,0.22), mat); snout.position.set(0.24,-0.04,0); snout.castShadow=true; head.add(snout);
    const jaw=new THREE.Mesh(new THREE.BoxGeometry(0.26,0.07,0.18), dMat); jaw.position.set(0.22,-0.13,0); head.add(jaw); g.userData.jaw=jaw;
    const eyeWhite=new THREE.MeshStandardMaterial({color:'#d8d2c8', roughness:0.3});
    const eyePupil=new THREE.MeshStandardMaterial({color:'#111', emissive:amphibian?'#1a3a2a':'#2a1a10', emissiveIntensity:0.8, roughness:0.2});
    const lids=[];
    for(const s of [-1,1]){
      const eye=new THREE.Mesh(new THREE.SphereGeometry(0.038,12,10), eyeWhite); eye.position.set(0.12,0.07,0.145*s); head.add(eye);
      const pupil=new THREE.Mesh(new THREE.SphereGeometry(0.02,10,8), eyePupil); pupil.position.set(0.145,0.07,0.155*s); head.add(pupil);
      const lid=new THREE.Mesh(new THREE.SphereGeometry(0.042,12,10,0,Math.PI*2,0,Math.PI/2), dMat); lid.position.set(0.12,0.075,0.145*s); lid.rotation.x=Math.PI; lid.scale.y=0.35; head.add(lid); lids.push(lid);
    }
    g.userData.lids=lids;
    const limbs=[];
    const limbPos=amphibian?[[0.48,-0.20,0.40],[0.48,-0.20,-0.40],[-0.38,-0.22,0.44],[-0.38,-0.22,-0.44]]:[[0.48,-0.26,0.38],[0.48,-0.26,-0.38],[-0.42,-0.24,0.42],[-0.42,-0.24,-0.42]];
    limbPos.forEach((p,idx)=>{
      const limb=new THREE.Group(); limb.position.set(p[0],p[1],p[2]); limb.userData.base=p.slice(); limb.userData.idx=idx;
      const upper=new THREE.Mesh(new THREE.CapsuleGeometry(amphibian?0.058:0.062, amphibian?0.28:0.24, 4, 10), mat); upper.castShadow=true; limb.add(upper);
      const lower=new THREE.Mesh(new THREE.CapsuleGeometry(amphibian?0.045:0.05, amphibian?0.22:0.18, 4, 8), mat); lower.position.set(0,-0.22,p[2]>0?0.05:-0.05); lower.rotation.x=p[2]>0?0.35:-0.35; lower.castShadow=true; limb.add(lower);
      const paw=new THREE.Mesh(new THREE.SphereGeometry(amphibian?0.075:0.068,10,8), dMat); paw.position.set(0,-0.38,p[2]>0?0.08:-0.08); paw.scale.set(1.3,0.55,1.5); limb.add(paw);
      limb.rotation.z = idx<2?0.65:-0.65; limb.rotation.x = p[2]>0?0.45:-0.45;
      g.add(limb); limbs.push(limb);
    });
    g.userData.limbs=limbs;
    const tail=new THREE.Group(); tail.position.set(-0.95,-0.03,0); g.add(tail); g.userData.tail=tail;
    const tailSegs=[];
    for(let i=0;i<6;i++){ const t=i/5; const r=lerp(amphibian?0.13:0.10,0.025,t); const seg=new THREE.Mesh(new THREE.SphereGeometry(r,10,8), mat); seg.position.x=-t*(amphibian?0.75:0.58); seg.position.y=-t*0.07; seg.castShadow=true; tail.add(seg); tailSegs.push(seg); }
    g.userData.tailSegs=tailSegs;
    for(let i=0;i<6;i++){ const t=i/5; const b=new THREE.Mesh(new THREE.SphereGeometry(0.035,6,6), dMat); b.position.set(lerp(-0.55,0.55,t), 0.28-(amphibian?0.04:0), 0); body.add(b); }
    g.scale.setScalar(scale);
    return g;
  }

  const mammal = buildCreature({main:'#7a6854', belly:'#c7b392', dark:'#45382d', amphibian:false, scale:1.0});
  mammal.position.set(-0.85,-0.18,0.35); mammal.rotation.y=0.12; mammal.rotation.z=-0.08; burrow.add(mammal);
  const amphib = buildCreature({main:'#5f7563', belly:'#9bb08e', dark:'#324136', amphibian:true, scale:1.05});
  amphib.position.set(1.0,-0.28,0.25); amphib.rotation.y=Math.PI-0.22; amphib.rotation.z=0.04; burrow.add(amphib);

  // X-ray ribs
  const ribsGroup=new THREE.Group(); burrow.add(ribsGroup);
  const ribMatBase=()=>new THREE.MeshBasicMaterial({color:'#7fffd4', transparent:true, opacity:0, depthWrite:false, blending:THREE.AdditiveBlending});
  for(let i=0;i<9;i++){ const rib=new THREE.Mesh(new THREE.TorusGeometry(0.24-i*0.011,0.013,8,30,Math.PI), ribMatBase()); rib.position.set(0.18-i*0.10, -0.02, 0); rib.rotation.y=Math.PI/2; rib.rotation.x=0.08; ribsGroup.add(rib); }
  const healGlow=new THREE.Mesh(new THREE.SphereGeometry(0.40,24,18), new THREE.MeshBasicMaterial({color:'#9fffe0', transparent:true, opacity:0, depthWrite:false, blending:THREE.AdditiveBlending})); healGlow.position.set(-0.12,0,0); ribsGroup.add(healGlow);
  const xrayShell=new THREE.Mesh(new THREE.SphereGeometry(0.78,28,22), new THREE.MeshBasicMaterial({color:'#7fffd4', transparent:true, opacity:0, wireframe:true, depthWrite:false, blending:THREE.AdditiveBlending}));
  xrayShell.scale.set(1.45,0.72,0.95); ribsGroup.add(xrayShell);

  // Water/sediment
  const waterMat=new THREE.MeshPhysicalMaterial({color:'#2a7ea8', transparent:true, opacity:0, roughness:0.06, metalness:0.02, transmission:0, depthWrite:false, thickness:0.6});
  const water=new THREE.Mesh(new THREE.BoxGeometry(6.2,1.6,4.0), waterMat); water.position.set(0,-1.25,0.25); water.renderOrder=10; burrow.add(water);
  const waterTop=new THREE.Mesh(new THREE.PlaneGeometry(6.1,3.9), new THREE.MeshBasicMaterial({color:'#8fdcff', transparent:true, opacity:0, depthWrite:false, blending:THREE.AdditiveBlending, side:THREE.DoubleSide}));
  waterTop.rotation.x=-Math.PI/2; waterTop.position.set(0,-0.45,0.25); waterTop.renderOrder=11; burrow.add(waterTop);

  const sedCount=320; const sedPos=new Float32Array(sedCount*3); const sedSeed=new Float32Array(sedCount);
  for(let i=0;i<sedCount;i++){ sedSeed[i]=Math.random(); sedPos[i*3]=(Math.random()-0.5)*6.0; sedPos[i*3+1]=1.8+Math.random()*3.0; sedPos[i*3+2]=(Math.random()-0.5)*3.6; }
  const sedBase=sedPos.slice(); const sedGeo=new THREE.BufferGeometry(); sedGeo.setAttribute('position', new THREE.BufferAttribute(sedPos,3));
  const sedMat=new THREE.PointsMaterial({color:'#c9b07a', size:0.045, transparent:true, opacity:0, depthWrite:false});
  const sediment=new THREE.Points(sedGeo,sedMat); sediment.renderOrder=12; burrow.add(sediment);

  const dustCount=220; const dPos=new Float32Array(dustCount*3); const dSeed=new Float32Array(dustCount);
  for(let i=0;i<dustCount;i++){ dSeed[i]=Math.random(); dPos[i*3]=(Math.random()-0.5)*12; dPos[i*3+1]=(Math.random()-0.5)*9; dPos[i*3+2]=(Math.random()-0.5)*9; }
  const dBase=dPos.slice(); const dustGeo=new THREE.BufferGeometry(); dustGeo.setAttribute('position', new THREE.BufferAttribute(dPos,3));
  const dustMat=new THREE.PointsMaterial({color:'#ffdca8', size:0.03, transparent:true, opacity:0.32, depthWrite:false, blending:THREE.AdditiveBlending});
  const dust=new THREE.Points(dustGeo,dustMat); dust.renderOrder=20; scene.add(dust);

  // Godray / shaft
  const shaftMat=new THREE.MeshBasicMaterial({color:'#ffe0a8', transparent:true, opacity:0.05, depthWrite:false, blending:THREE.AdditiveBlending, side:THREE.DoubleSide});
  const shaft=new THREE.Mesh(new THREE.ConeGeometry(3.2,10,40,1,true), shaftMat);
  shaft.position.set(3.8,4.5,1.8); shaft.rotation.x=Math.PI; shaft.rotation.z=-0.48; shaft.renderOrder=21; scene.add(shaft);

  // Rain streaks for shelter flashback
  const rainCount=180; const rainPos=new Float32Array(rainCount*3); const rainSeed=new Float32Array(rainCount);
  for(let i=0;i<rainCount;i++){ rainSeed[i]=Math.random(); rainPos[i*3]=(Math.random()-0.5)*8; rainPos[i*3+1]=Math.random()*6; rainPos[i*3+2]=(Math.random()-0.5)*6; }
  const rainBase=rainPos.slice(); const rainGeo=new THREE.BufferGeometry(); rainGeo.setAttribute('position', new THREE.BufferAttribute(rainPos,3));
  const rainMat=new THREE.PointsMaterial({color:'#9ec7ff', size:0.04, transparent:true, opacity:0, depthWrite:false});
  const rain=new THREE.Points(rainGeo,rainMat); rain.renderOrder=22; scene.add(rain);

  // Impact ring
  const ringMat=new THREE.MeshBasicMaterial({color:'#ff5a2a', transparent:true, opacity:0, depthWrite:false, blending:THREE.AdditiveBlending, side:THREE.DoubleSide});
  const ring=new THREE.Mesh(new THREE.RingGeometry(0.5,0.64,64), ringMat); ring.position.set(0,0.2,2.0); ring.renderOrder=23; scene.add(ring);

  // Fossil imprint plane for ending
  const fossilPlane=new THREE.Mesh(new THREE.PlaneGeometry(5.2,2.8), new THREE.MeshStandardMaterial({color:'#8a7e69', map:rockMap, normalMap:rockN, roughness:0.95, metalness:0.01, transparent:true, opacity:0}));
  fossilPlane.rotation.x=-Math.PI/2; fossilPlane.position.set(0,-0.58,0.2); fossilPlane.renderOrder=3; env.add(fossilPlane);
  const fossilImprint=new THREE.Mesh(new THREE.PlaneGeometry(4.2,2.1), new THREE.MeshBasicMaterial({color:'#2a241d', transparent:true, opacity:0, depthWrite:false}));
  fossilImprint.rotation.x=-Math.PI/2; fossilImprint.position.set(0,-0.575,0.2); fossilImprint.renderOrder=4; env.add(fossilImprint);

  // Optional GLB rock dressing
  const loader=new GLTFLoader();
  ['/tools/extinct-channel/projects/huayuan/assets/rock_07.glb','/tools/extinct-channel/projects/huayuan/assets/coast_rocks_01.glb'].forEach((url,i)=>{
    loader.load(url,(gltf)=>{
      const obj=gltf.scene; obj.traverse(o=>{ if(o.isMesh){ o.castShadow=true; o.receiveShadow=true; if(o.material){ o.material.roughness=1; o.material.metalness=0; o.material.needsUpdate=true; } } });
      const s=i===0?1.0:1.6; obj.scale.setScalar(s);
      obj.position.set(i===0?-5.2:5.4,-2.8,i===0?-2.8:-3.4); obj.rotation.y=i===0?0.4:-0.6;
      scene.add(obj);
    }, undefined, ()=>{});
  });

  const camPos=new THREE.Vector3(), camLook=new THREE.Vector3();
  let prevCamPos=new THREE.Vector3();
  function setCam(px,py,pz,lx,ly,lz,fov=38){
    camPos.set(px,py,pz); camLook.set(lx,ly,lz);
    camera.position.copy(camPos); camera.lookAt(camLook); camera.fov=fov;
    const d=camera.position.distanceTo(camLook);
    camera.near=clamp(d-7,0.05,0.8); camera.far=d+50; camera.updateProjectionMatrix();
  }
  function applyCamShake(t,amt=0){
    if(amt<=0) return;
    camera.position.x += (noise1(t*8.7)-0.5)*amt;
    camera.position.y += (noise1(t*9.3+10)-0.5)*amt*0.6;
    camera.position.z += (noise1(t*7.9+20)-0.5)*amt*0.4;
    camera.lookAt(camLook);
  }
  function updateShadows(){
    key.target.position.copy(camLook); key.target.updateMatrixWorld();
    const s=10; key.shadow.camera.left=-s; key.shadow.camera.right=s; key.shadow.camera.top=s; key.shadow.camera.bottom=-s;
    key.shadow.camera.updateProjectionMatrix();
  }
  function animateCreature(c, t, breathe=1, walk=0, sleep=0){
    const ud=c.userData;
    const by = 1 + Math.sin(t*1.6*(ud.amphibian?0.9:1.0))*0.012*breathe;
    c.scale.y = c.scale.y*0.9 + ( (ud.amphibian?1.05:1.0) * by )*0.1;
    ud.jaw.rotation.x = 0.02 + Math.sin(t*0.8)*0.015*breathe;
    ud.lids.forEach((lid,i)=>{ const blink = (Math.sin(t*0.7+i*1.3)>0.97)?0.9:0.35; lid.scale.y = lerp(lid.scale.y, blink + sleep*0.5, 0.15); });
    ud.tailSegs.forEach((seg,i)=>{ seg.position.y = -i*0.012 + Math.sin(t*1.2-i*0.5)*0.01*breathe; seg.position.z = Math.sin(t*1.1-i*0.45)*0.012*breathe; });
    ud.limbs.forEach((limb,i)=>{ const base=limb.userData.base; const ph=t*2.2 + i*1.7; limb.rotation.x = (base[2]>0?0.45:-0.45) + Math.sin(ph)*0.08*walk; limb.rotation.z = (i<2?0.65:-0.65) + Math.cos(ph)*0.06*walk; limb.position.y = base[1] + Math.sin(ph)*0.02*walk; });
    if(sleep>0){ c.rotation.z = lerp(c.rotation.z, (ud.amphibian?0.04:-0.08), 0.1); }
  }

  function resetScene(){
    waterMat.opacity=0; waterTop.material.opacity=0; sedMat.opacity=0; ringMat.opacity=0; rainMat.opacity=0;
    ribsGroup.children.forEach(c=>{ if(c.material) c.material.opacity=0; });
    xrayShell.material.opacity=0; healGlow.material.opacity=0;
    accent.intensity=0; key.intensity=8.8; rim.intensity=4.8; fill.intensity=4.2; coldFill.intensity=2.2; moon.intensity=0; burrowFill.intensity=2.8;
    shaftMat.opacity=0.07; dustMat.opacity=0.28; fossilPlane.material.opacity=0; fossilImprint.material.opacity=0;
    burrow.visible=true; env.visible=true; mammal.visible=true; amphib.visible=true;
    burrow.position.set(0,-0.1,0); burrow.rotation.set(0,0,0);
    env.rotation.set(0,0,0); env.position.set(0,0,0);
    mammal.position.set(-0.85,-0.18,0.35); mammal.rotation.set(0,0.12,-0.08); mammal.scale.set(1,1,1);
    amphib.position.set(1.0,-0.28,0.25); amphib.rotation.set(0,Math.PI-0.22,0.04); amphib.scale.set(1.05,1.05,1.05);
    water.position.y=-1.25; waterTop.position.y=-0.45; water.scale.set(1,1,1);
  }

  function updateDust(t,spd=1){
    const arr=dustGeo.attributes.position.array;
    for(let i=0;i<dustCount;i++){ const s=dSeed[i]; arr[i*3]=dBase[i*3]+0.18*Math.sin(t*0.28*spd+s*7.0); arr[i*3+1]=dBase[i*3+1]+0.12*Math.sin(t*0.38*spd+s*10.0); arr[i*3+2]=dBase[i*3+2]+0.08*Math.cos(t*0.22*spd+s*5.0); }
    dustGeo.attributes.position.needsUpdate=true;
  }

  function updateRain(t,opacity){
    rainMat.opacity=opacity;
    const arr=rainGeo.attributes.position.array;
    for(let i=0;i<rainCount;i++){ const s=rainSeed[i]; const y=(rainBase[i*3+1]-t*4.5*(0.6+s))%6; arr[i*3]=rainBase[i*3]+Math.sin(t*0.5+s)*0.05; arr[i*3+1]=y<0?y+6:y; arr[i*3+2]=rainBase[i*3+2]; }
    rainGeo.attributes.position.needsUpdate=true;
  }

  setCam(0.2,2.8,6.2,0,0.35,0,40); prevCamPos.copy(camera.position);

  function evaluateFrame(frame){
    frame=clamp(frame,0,TOTAL_FRAMES-1);
    if(frame>=TOTAL_FRAMES-5) return evaluateFrame(0); // loop lock
    const t=frame/FPS;
    resetScene();
    updateDust(t,1);

    let shot='hook'; let shake=0; let impact=0;
    // 1. Hook 0-2.5
    if(t<2.5){
      shot='hook_rock';
      const p=t/2.5; const punch=easeOut(p);
      setCam(lerp(0.8,0.25,punch), lerp(3.2,2.4,punch), lerp(7.2,5.2,punch), 0,0.45-0.1*p,0, 44-p*4);
      key.intensity=6.8; fill.intensity=2.8; shaftMat.opacity=0.08;
      impact = p<0.12?1-p/0.12:0; shake=impact*0.08;
    }
    // 2. Curled asleep 2.5-5.5
    else if(t<5.5){
      shot='asleep';
      const p=(t-2.5)/3.0;
      setCam(lerp(-1.8,-1.2,easeInOut(p)), lerp(0.85,0.55,easeInOut(p)), lerp(3.2,2.4,easeInOut(p)), -0.75,-0.22,0.32, 32);
      animateCreature(mammal,t,1.2,0,1); animateCreature(amphib,t,0.7,0,0.3);
      fill.intensity=5.2; burrowFill.intensity=6.5; moon.intensity=1.2; shaftMat.opacity=0.04; rim.intensity=5.5;
    }
    // 3. Two species identity 5.5-8.5
    else if(t<8.5){
      shot='two_species';
      const p=(t-5.5)/3.0;
      const ang=0.15+p*0.55;
      setCam(-1.5*Math.cos(ang)+0.2, 0.75+0.06*Math.sin(p*2.0), 2.8-0.2*p, 0.05,-0.22,0.28, 33);
      animateCreature(mammal,t,1.0,0,0.6); animateCreature(amphib,t,0.9,0,0.2);
      rim.intensity=6.0; fill.intensity=5.0; burrowFill.intensity=6.0; coldFill.intensity=2.8;
    }
    // 4. Wait not enemies 8.5-10.8
    else if(t<10.8){
      shot='not_enemies';
      const p=(t-8.5)/2.3; const punch=easeOut(clamp(p/0.22,0,1));
      setCam(lerp(-0.8,0.55,punch), lerp(0.7,0.45,punch), lerp(2.8,1.9,punch), 0.25,-0.2,0.3, lerp(32,27,punch));
      animateCreature(mammal,t,0.8,0,0.5); animateCreature(amphib,t,0.8,0,0.2);
      ringMat.opacity=p<0.4?0.85*(1-p/0.4):0; ring.scale.setScalar(1+p*11); ring.position.set(0.2,0.0,1.8);
      accent.intensity=p<0.4?8.0*(1-p/0.4):0; key.intensity=9.5; rim.intensity=6.0; burrowFill.intensity=6.5; fill.intensity=5.0; shaftMat.opacity=0.02;
      impact=p<0.18?1-p/0.18:0; shake=impact*0.12;
    }
    // 5. Healing ribs evidence 10.8-15.0
    else if(t<15.0){
      shot='healed_ribs';
      const p=(t-10.8)/4.2;
      setCam(lerp(0.8,1.15,easeInOut(p)), 0.45, lerp(2.1,1.55,easeInOut(p)), 1.0,-0.22,0.25, 28);
      animateCreature(mammal,t,0.7,0,0.6); animateCreature(amphib,t,0.6,0,0.2);
      const xr=smooth(clamp((p-0.06)/0.22,0,1));
      const xf=1-smooth(clamp((p-0.78)/0.22,0,1))*0.25;
      ribsGroup.children.forEach(c=>{ if(c.material && c.material.blending===THREE.AdditiveBlending && c!==healGlow) c.material.opacity=Math.min(1,1.4*xr*xf); });
      healGlow.material.opacity=0.95*xr*xf*(0.7+0.3*Math.sin(t*3.2));
      xrayShell.material.opacity=0.38*xr*xf;
      ribsGroup.position.copy(amphib.position); ribsGroup.rotation.copy(amphib.rotation); ribsGroup.scale.copy(amphib.scale);
      coldFill.intensity=3.8*xr; burrowFill.intensity=5.5; fill.intensity=4.5; key.intensity=8.0; shaftMat.opacity=0.02;
    }
    // 6. Not a hunt 15.0-17.2
    else if(t<17.2){
      shot='not_hunt';
      const p=(t-15.0)/2.2;
      setCam(lerp(1.2,-0.2,easeInOut(p)), lerp(0.7,1.15,easeInOut(p)), lerp(2.2,3.8,easeInOut(p)), 0.1,-0.18,0.28, 34);
      animateCreature(mammal,t,0.9,0,0.7); animateCreature(amphib,t,0.8,0,0.3);
      fill.intensity=2.8; rim.intensity=3.2;
    }
    // 7. Crawled in for shelter 17.2-21.0
    else if(t<21.0){
      shot='shelter';
      const p=(t-17.2)/3.8;
      if(p<0.5){
        const pp=p/0.5;
        setCam(lerp(2.2,1.4,easeInOut(pp)), lerp(0.9,0.7,easeInOut(pp)), lerp(3.6,2.6,easeInOut(pp)), 1.2-pp*0.4,-0.22,0.25, 33);
        amphib.position.x=lerp(2.8,1.0,easeOut(pp)); amphib.position.z=lerp(1.5,0.25,easeOut(pp));
        amphib.rotation.y=lerp(Math.PI-0.8,Math.PI-0.22,easeOut(pp));
        animateCreature(amphib,t,1.0,0.8,0); animateCreature(mammal,t,0.8,0,0.8);
        updateRain(t,0.35*(1-pp*0.6)); moon.intensity=0.6;
      } else {
        const pp=(p-0.5)/0.5;
        setCam(lerp(1.4,-1.8,easeInOut(pp)), lerp(0.7,1.2,easeInOut(pp)), lerp(2.6,3.4,easeInOut(pp)), -0.6+pp*0.5,-0.2,0.3, 32);
        animateCreature(amphib,t,0.8,0,0.4); animateCreature(mammal,t,0.9,0,0.9);
        fill.intensity=2.6;
      }
    }
    // 8. Aestivation 21.0-24.5
    else if(t<24.5){
      shot='aestivation';
      const p=(t-21.0)/3.5;
      setCam(lerp(-1.3,-0.85,easeInOut(p)), lerp(0.65,0.45,easeInOut(p)), lerp(2.6,2.0,easeInOut(p)), -0.85,-0.2,0.35, 29);
      animateCreature(mammal,t,0.5,0,1.0); animateCreature(amphib,t,0.6,0,0.5);
      dustMat.opacity=0.38; fill.intensity=5.0; burrowFill.intensity=6.0; rim.intensity=5.2; shaftMat.opacity=0.05;
    }
    // 9. Flood 24.5-30.5
    else if(t<30.5){
      shot='flood';
      const p=(t-24.5)/6.0;
      setCam(lerp(-0.6,0.2,easeInOut(p)), lerp(0.9,1.8,easeInOut(p)), lerp(2.8,4.2,easeInOut(p)), 0,-0.22,0.22, 38);
      animateCreature(mammal,t,0.4,0,0.8); animateCreature(amphib,t,0.4,0,0.4);
      const wp=smooth(clamp((p-0.08)/0.55,0,1));
      waterMat.opacity=0.72*wp; waterTop.material.opacity=0.55*wp;
      water.position.y=lerp(-1.25,0.0,wp); waterTop.position.y=lerp(-0.45,0.62,wp);
      const sp=clamp((p-0.18)/0.72,0,1);
      sedMat.opacity=0.9*sp*(1-smooth(clamp((p-0.92)/0.08,0,1)));
      const arr=sedGeo.attributes.position.array;
      for(let i=0;i<sedCount;i++){ const s=sedSeed[i]; const fall=sp*(2.0+s*1.4); arr[i*3+1]=lerp(1.8+s*3.0,-0.5+s*0.25,clamp(fall/2.2,0,1)); arr[i*3]=sedBase[i*3]+Math.sin(t*1.8+s*6)*0.05; }
      sedGeo.attributes.position.needsUpdate=true;
      if(p>0.55){ key.intensity=lerp(5.5,3.5,(p-0.55)/0.45); rim.intensity=lerp(3.0,1.5,(p-0.55)/0.45); }
      shake = p>0.1 && p<0.7 ? 0.03*(1-Math.abs(p-0.4)/0.3) : 0;
    }
    // 10. Payoff / fossil clue 30.5-35.0
    else {
      shot='clue';
      const p=(t-30.5)/4.5;
      setCam(lerp(0.2,0.3,easeInOut(p)), lerp(2.0,3.0,easeInOut(p)), lerp(4.6,6.8,easeInOut(p)), 0,lerp(0.15,0.4,easeInOut(p)),0, lerp(38,42,easeInOut(p)));
      const reveal=smooth(clamp((p-0.1)/0.35,0,1));
      burrow.visible = p < 0.45;
      fossilPlane.material.opacity=0.85*reveal; fossilImprint.material.opacity=0.55*reveal;
      env.rotation.y=lerp(0.04,0,easeInOut(p));
      key.intensity=lerp(4.5,6.5,easeInOut(p)); fill.intensity=2.8; shaftMat.opacity=0.07;
      // loop clean
      if(p>0.85){ const lp=(p-0.85)/0.15; setCam(lerp(0.3,0.2,lp), lerp(3.0,2.8,lp), lerp(6.8,6.2,lp), 0, lerp(0.4,0.35,lp), 0, lerp(42,40,lp)); }
    }

    animateCreature(mammal,t,1,0,0); animateCreature(amphib,t,1,0,0);
    updateDust(t, shot==='flood'?1.8:1.0);
    applyCamShake(t,shake);
    updateShadows();

    const mv=new THREE.Vector2((camPos.x-prevCamPos.x)*0.02, -(camPos.y-prevCamPos.y)*0.02);
    prevCamPos.copy(camPos);
    const focusDist=camera.position.distanceTo(camLook);
    const exposureMap = { hook_rock:1.65, asleep:1.55, two_species:1.55, not_enemies:1.7, healed_ribs:1.5, not_hunt:1.55, shelter:1.5, aestivation:1.5, flood:1.45, clue:1.6 };
    return {
      frame, time:t, shot, totalFrames: TOTAL_FRAMES,
      post: { focusDist, dofRange: shot==='healed_ribs'?16:28, maxBlur: shot==='not_enemies'?4.5:2.8, bloomAmt: shot==='not_enemies'?0.9:0.55, exposure: exposureMap[shot] || 1.55, time:t, motionVec:mv, impact }
    };
  }

  evaluateFrame(0);
  return { evaluateFrame, TOTAL_FRAMES, FPS, DUR };
}
