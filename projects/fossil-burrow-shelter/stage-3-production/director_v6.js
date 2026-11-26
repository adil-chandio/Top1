import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

export function createDirector({ THREE, scene, camera, renderer, W, H }) {
  const FPS = 30, TOTAL_FRAMES = 1050, DUR = TOTAL_FRAMES / FPS;
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const lerp=(a,b,t)=>a+(b-a)*t;
  const smooth=(t)=>{t=clamp(t,0,1); return t*t*(3-2*t);};
  const easeOut=(t)=>1-Math.pow(1-clamp(t,0,1),4);
  const easeInOut=(t)=>{t=clamp(t,0,1); return t<0.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;};

  // --- Snyder look base ---
  scene.background = new THREE.Color(0x07090d);
  scene.fog = new THREE.FogExp2(0x07090d, 0.018);

  const amb = new THREE.AmbientLight(0x8aa4c8, 0.35); scene.add(amb);
  const key = new THREE.DirectionalLight(0xffe0b5, 5.8);
  key.position.set(7, 10, 6); key.castShadow = true;
  key.shadow.mapSize.set(2048,2048);
  key.shadow.camera.left=-10; key.shadow.camera.right=10; key.shadow.camera.top=10; key.shadow.camera.bottom=-10;
  key.shadow.camera.near=0.5; key.shadow.camera.far=40; key.shadow.bias=-0.00035; key.shadow.normalBias=0.03;
  scene.add(key); scene.add(key.target);
  const rim = new THREE.DirectionalLight(0x9fd0ff, 3.0); rim.position.set(-8,5,-7); scene.add(rim);
  const fill = new THREE.PointLight(0xff9a66, 2.2, 50); fill.position.set(0,3,5); scene.add(fill);
  const accent = new THREE.PointLight(0xff3b1f, 0, 25); accent.position.set(0,1.5,3); scene.add(accent);
  const coldFill = new THREE.PointLight(0x7fc0ff, 1.0, 35); coldFill.position.set(-3,1,-2); scene.add(coldFill);

  // --- Procedural texture helpers ---
  function makeCanvas(w,h,fn){ const c=document.createElement('canvas'); c.width=w; c.height=h; fn(c.getContext('2d'),w,h); return c; }
  function texFromCanvas(c, srgb=true){ const t=new THREE.CanvasTexture(c); t.wrapS=t.wrapT=THREE.RepeatWrapping; if(srgb) t.colorSpace=THREE.SRGBColorSpace; t.needsUpdate=true; return t; }
  function noiseTex(seed=1, c1='#5a5247', c2='#3f3830'){
    return texFromCanvas(makeCanvas(256,256,(g,w,h)=>{
      g.fillStyle=c1; g.fillRect(0,0,w,h);
      for(let i=0;i<5000;i++){ const x=Math.random()*w,y=Math.random()*h; const a=Math.random()*0.12; g.fillStyle=`rgba(0,0,0,${a})`; g.fillRect(x,y,2,2); }
      for(let i=0;i<2500;i++){ const x=Math.random()*w,y=Math.random()*h; const a=Math.random()*0.08; g.fillStyle=`rgba(255,255,255,${a})`; g.fillRect(x,y,1,1); }
      g.strokeStyle=c2; g.globalAlpha=0.15; for(let i=0;i<40;i++){ g.beginPath(); g.moveTo(Math.random()*w,Math.random()*h); g.lineTo(Math.random()*w,Math.random()*h); g.stroke(); }
    }));
  }
  function rockNormal(){
    return texFromCanvas(makeCanvas(256,256,(g,w,h)=>{
      g.fillStyle='#8080ff'; g.fillRect(0,0,w,h);
      for(let i=0;i<3000;i++){ const x=Math.random()*w,y=Math.random()*h; const r=1+Math.random()*3; const nx=128+(Math.random()-0.5)*40; const ny=128+(Math.random()-0.5)*40; g.fillStyle=`rgb(${nx|0},${ny|0},255)`; g.beginPath(); g.arc(x,y,r,0,Math.PI*2); g.fill(); }
    }), false);
  }

  const rockMap = noiseTex(1,'#6a6154','#3a332b'); rockMap.repeat.set(2,2);
  const rockN = rockNormal(); rockN.repeat.set(2,2);
  const soilMap = noiseTex(2,'#4a3a2b','#2a1f16'); soilMap.repeat.set(2,2);
  const boneMap = noiseTex(3,'#d8ccb4','#b8a88a');

  // --- Environment ---
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(80,80), new THREE.MeshStandardMaterial({color:'#1a1612', map:soilMap, roughness:1, metalness:0}));
  ground.rotation.x=-Math.PI/2; ground.position.y=-3.2; ground.receiveShadow=true; scene.add(ground);

  // Rock slab group
  const rockGroup = new THREE.Group(); scene.add(rockGroup);
  const rockMat = new THREE.MeshStandardMaterial({ color:'#7a7062', map:rockMap, normalMap:rockN, normalScale:new THREE.Vector2(0.8,0.8), roughness:0.96, metalness:0.02 });
  const rockDark = new THREE.MeshStandardMaterial({ color:'#4a4238', map:soilMap, roughness:1, metalness:0.01 });

  function addRockBox(w,h,d,x,y,z,rx=0,ry=0,rz=0,mat=rockMat){
    const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d), mat); m.position.set(x,y,z); m.rotation.set(rx,ry,rz); m.castShadow=true; m.receiveShadow=true; rockGroup.add(m); return m;
  }
  addRockBox(8.2,1.1,5.2,0,-0.55,0);
  addRockBox(7.4,0.55,4.6,0,0.28,0);
  addRockBox(6.2,0.3,3.8,0.2,0.68,0.1);
  // strata
  for(let i=0;i<7;i++){ addRockBox(7.8-i*0.2,0.08,4.8-i*0.15,(Math.random()-0.5)*0.2,-0.95+i*0.22,0.05,0,0,0, i%2?rockMat:rockDark); }
  // jagged rocks
  for(let i=0;i<28;i++){
    const s=0.2+Math.random()*0.9;
    const geo = Math.random()>0.5 ? new THREE.DodecahedronGeometry(s,0) : new THREE.BoxGeometry(s*1.4,s,s*1.1);
    const m=new THREE.Mesh(geo, i%3?rockMat:rockDark);
    m.position.set((Math.random()-0.5)*8.5, -0.3+Math.random()*1.4, (Math.random()-0.5)*5.2);
    m.rotation.set(Math.random()*2,Math.random()*2,Math.random()*2);
    m.castShadow=true; m.receiveShadow=true; rockGroup.add(m);
  }

  // Burrow cutaway
  const burrowGroup = new THREE.Group(); burrowGroup.position.set(0,-0.1,0); scene.add(burrowGroup);
  const burrowShell = new THREE.Mesh(new THREE.CylinderGeometry(3.2,3.4,5.6,48,1,true,Math.PI*0.12,Math.PI*1.76), new THREE.MeshStandardMaterial({color:'#3a3228', map:soilMap, roughness:1, metalness:0.01, transparent:true, opacity:0.55, side:THREE.DoubleSide}));
  burrowShell.rotation.z=Math.PI/2; burrowShell.rotation.y=Math.PI/2; burrowShell.position.set(0,-0.65,0.2);
  burrowShell.castShadow=true; burrowShell.receiveShadow=true; burrowGroup.add(burrowShell);
  const burrowFloor = new THREE.Mesh(new THREE.BoxGeometry(5.8,0.35,3.4), new THREE.MeshStandardMaterial({color:'#3b2f22', map:soilMap, roughness:1}));
  burrowFloor.position.set(0,-1.05,0.25); burrowFloor.receiveShadow=true; burrowGroup.add(burrowFloor);
  const burrowVoid = new THREE.Mesh(new THREE.SphereGeometry(2.3,32,20,0,Math.PI*2,0,Math.PI/2), new THREE.MeshStandardMaterial({color:'#050402', roughness:1, transparent:true, opacity:0.35}));
  burrowVoid.scale.set(1.35,0.62,1.1); burrowVoid.position.set(0,-0.62,0.28); burrowGroup.add(burrowVoid);

  // --- Creature builders (parametric, higher detail) ---
  function buildCreature({main='#7d6b58', belly='#b8a68a', dark='#4a3f34', amphibian=false}) {
    const g = new THREE.Group();
    const mat = new THREE.MeshStandardMaterial({color:main, roughness:0.72, metalness:0.03, map:noiseTex(4,main,dark), emissive:new THREE.Color(main), emissiveIntensity:0.08});
    const bMat = new THREE.MeshStandardMaterial({color:belly, roughness:0.85, metalness:0.01, emissive:new THREE.Color(belly), emissiveIntensity:0.05});
    const dMat = new THREE.MeshStandardMaterial({color:dark, roughness:0.85, metalness:0.02});
    // body segments
    const segs = amphibian ? 7 : 6;
    for(let i=0;i<segs;i++){
      const t=i/(segs-1);
      const r = (amphibian?0.42:0.46) * Math.sin(t*Math.PI)*0.7 + (amphibian?0.22:0.26);
      const s = new THREE.Mesh(new THREE.SphereGeometry(r,20,16), mat);
      s.position.set(lerp(-0.75,0.75,t), Math.sin(t*Math.PI)*0.08 - (amphibian?0.05:0), 0);
      s.scale.set(1.25, amphibian?0.72:0.85, 1.0);
      s.castShadow=true; s.receiveShadow=true; g.add(s);
    }
    // belly
    const bellyMesh = new THREE.Mesh(new THREE.SphereGeometry(0.38,20,16), bMat);
    bellyMesh.scale.set(1.6, amphibian?0.35:0.45, 0.8); bellyMesh.position.set(0,-0.18,0.12); g.add(bellyMesh);
    // head
    const head = new THREE.Group(); head.position.set(0.95,0.08,0); g.add(head);
    const skull = new THREE.Mesh(new THREE.BoxGeometry(0.42,0.28,0.34), mat); skull.castShadow=true; head.add(skull);
    const snout = new THREE.Mesh(new THREE.BoxGeometry(0.28,0.16,0.24), mat); snout.position.set(0.28,-0.03,0); snout.castShadow=true; head.add(snout);
    const jaw = new THREE.Mesh(new THREE.BoxGeometry(0.24,0.08,0.2), dMat); jaw.position.set(0.26,-0.12,0); head.add(jaw);
    // eyes
    const eyeMat = new THREE.MeshStandardMaterial({color:'#111', emissive: amphibian?'#1a3a2a':'#2a1a10', emissiveIntensity:0.6, roughness:0.2});
    for(const s of [-1,1]){ const e=new THREE.Mesh(new THREE.SphereGeometry(0.035,10,8), eyeMat); e.position.set(0.1,0.06,0.15*s); head.add(e); }
    // limbs
    const limbGeo = new THREE.CapsuleGeometry(amphibian?0.055:0.06, amphibian?0.32:0.26, 4, 8);
    const pawGeo = new THREE.SphereGeometry(amphibian?0.07:0.065,8,8);
    const positions = amphibian ? [[0.45,-0.22,0.38],[0.45,-0.22,-0.38],[-0.35,-0.22,0.42],[-0.35,-0.22,-0.42]] : [[0.45,-0.28,0.36],[0.45,-0.28,-0.36],[-0.4,-0.26,0.4],[-0.4,-0.26,-0.4]];
    positions.forEach((p,idx)=>{
      const limb = new THREE.Group(); limb.position.set(p[0],p[1],p[2]);
      const upper=new THREE.Mesh(limbGeo,mat); upper.castShadow=true; limb.add(upper);
      const paw=new THREE.Mesh(pawGeo,dMat); paw.position.y=-0.22; paw.scale.set(1.2,0.6,1.4); limb.add(paw);
      limb.rotation.z = idx<2?0.7:-0.7; limb.rotation.x = p[2]>0?0.5:-0.5;
      g.add(limb);
    });
    // tail
    const tail = new THREE.Group(); tail.position.set(-0.9,-0.02,0); g.add(tail);
    for(let i=0;i<5;i++){ const t=i/4; const r=lerp(amphibian?0.14:0.11,0.03,t); const seg=new THREE.Mesh(new THREE.SphereGeometry(r,10,8),mat); seg.position.x=-t*(amphibian?0.7:0.55); seg.position.y=-t*0.08; seg.castShadow=true; tail.add(seg); }
    // spine bumps
    for(let i=0;i<5;i++){ const t=i/4; const b=new THREE.Mesh(new THREE.SphereGeometry(0.04,6,6), dMat); b.position.set(lerp(-0.5,0.5,t), 0.28-(amphibian?0.04:0), 0); g.add(b); }
    return g;
  }

  const mammal = buildCreature({main:'#7a6854', belly:'#c2ae90', dark:'#4a3c30', amphibian:false});
  mammal.scale.setScalar(1.0); mammal.position.set(-0.85,-0.18,0.35); mammal.rotation.y=0.12; mammal.rotation.z=-0.08;
  burrowGroup.add(mammal);

  const amphib = buildCreature({main:'#5f7563', belly:'#98ad8c', dark:'#344238', amphibian:true});
  amphib.scale.setScalar(1.05); amphib.position.set(1.0,-0.28,0.25); amphib.rotation.y=Math.PI-0.22; amphib.rotation.z=0.04;
  burrowGroup.add(amphib);

  // Ribcage X-ray for amphibian
  const ribsGroup = new THREE.Group(); burrowGroup.add(ribsGroup);
  const ribMat = new THREE.MeshBasicMaterial({color:'#7fffd4', transparent:true, opacity:0, depthWrite:false, blending:THREE.AdditiveBlending});
  for(let i=0;i<8;i++){
    const rib = new THREE.Mesh(new THREE.TorusGeometry(0.24-i*0.012,0.013,8,28,Math.PI), ribMat.clone());
    rib.position.set(0.18-i*0.11, -0.02, 0); rib.rotation.y=Math.PI/2; rib.rotation.x=0.08;
    ribsGroup.add(rib);
  }
  const healMat = new THREE.MeshBasicMaterial({color:'#9fffe0', transparent:true, opacity:0, depthWrite:false, blending:THREE.AdditiveBlending});
  const healGlow = new THREE.Mesh(new THREE.SphereGeometry(0.38,24,18), healMat); healGlow.position.set(-0.1,0,0); ribsGroup.add(healGlow);
  const xrayShell = new THREE.Mesh(new THREE.SphereGeometry(0.75,28,22), new THREE.MeshBasicMaterial({color:'#7fffd4', transparent:true, opacity:0, wireframe:true, depthWrite:false, blending:THREE.AdditiveBlending}));
  xrayShell.scale.set(1.4,0.72,0.95); ribsGroup.add(xrayShell);

  // Water
  const waterMat = new THREE.MeshPhysicalMaterial({color:'#2a7ea8', transparent:true, opacity:0, roughness:0.08, metalness:0.05, transmission:0.0, depthWrite:false, thickness:0.5});
  const water = new THREE.Mesh(new THREE.BoxGeometry(5.8,1.4,3.6), waterMat); water.position.set(0,-1.2,0.25); water.renderOrder=10; burrowGroup.add(water);
  const waterTop = new THREE.Mesh(new THREE.PlaneGeometry(5.7,3.5), new THREE.MeshBasicMaterial({color:'#8fdcff', transparent:true, opacity:0, depthWrite:false, blending:THREE.AdditiveBlending, side:THREE.DoubleSide}));
  waterTop.rotation.x=-Math.PI/2; waterTop.position.set(0,-0.5,0.25); waterTop.renderOrder=11; burrowGroup.add(waterTop);

  // Sediment particles
  const sedCount=260; const sedPos=new Float32Array(sedCount*3); const sedSeed=new Float32Array(sedCount);
  for(let i=0;i<sedCount;i++){ sedSeed[i]=Math.random(); sedPos[i*3]=(Math.random()-0.5)*5.6; sedPos[i*3+1]=1.8+Math.random()*2.8; sedPos[i*3+2]=(Math.random()-0.5)*3.2; }
  const sedBase=sedPos.slice();
  const sedGeo=new THREE.BufferGeometry(); sedGeo.setAttribute('position', new THREE.BufferAttribute(sedPos,3));
  const sedMat=new THREE.PointsMaterial({color:'#c9b07a', size:0.05, transparent:true, opacity:0, depthWrite:false});
  const sediment=new THREE.Points(sedGeo,sedMat); sediment.renderOrder=12; burrowGroup.add(sediment);

  // Dust motes (global)
  const dustCount=180; const dPos=new Float32Array(dustCount*3); const dSeed=new Float32Array(dustCount);
  for(let i=0;i<dustCount;i++){ dSeed[i]=Math.random(); dPos[i*3]=(Math.random()-0.5)*10; dPos[i*3+1]=(Math.random()-0.5)*8; dPos[i*3+2]=(Math.random()-0.5)*8; }
  const dBase=dPos.slice();
  const dustGeo=new THREE.BufferGeometry(); dustGeo.setAttribute('position', new THREE.BufferAttribute(dPos,3));
  const dustMat=new THREE.PointsMaterial({color:'#ffdca8', size:0.035, transparent:true, opacity:0.35, depthWrite:false, blending:THREE.AdditiveBlending});
  const dust=new THREE.Points(dustGeo,dustMat); dust.renderOrder=20; scene.add(dust);

  // Volumetric light shaft
  const shaftMat = new THREE.MeshBasicMaterial({color:'#ffd89a', transparent:true, opacity:0.045, depthWrite:false, blending:THREE.AdditiveBlending, side:THREE.DoubleSide});
  const shaft = new THREE.Mesh(new THREE.ConeGeometry(2.8,9,32,1,true), shaftMat);
  shaft.position.set(3.5,4.0,1.5); shaft.rotation.x=Math.PI; shaft.rotation.z=-0.45; shaft.renderOrder=21; scene.add(shaft);

  // Shock ring
  const ringMat = new THREE.MeshBasicMaterial({color:'#ff5a2a', transparent:true, opacity:0, depthWrite:false, blending:THREE.AdditiveBlending, side:THREE.DoubleSide});
  const ring = new THREE.Mesh(new THREE.RingGeometry(0.5,0.62,64), ringMat); ring.position.set(0,0.2,2.0); ring.renderOrder=22; scene.add(ring);

  // Try load repo rock GLBs as set dressing (optional)
  const loader = new GLTFLoader();
  ['/tools/extinct-channel/projects/huayuan/assets/rock_07.glb','/tools/extinct-channel/projects/huayuan/assets/coast_rocks_01.glb'].forEach((url,i)=>{
    loader.load(url, (gltf)=>{
      const obj=gltf.scene; obj.traverse(o=>{ if(o.isMesh){ o.castShadow=true; o.receiveShadow=true; if(o.material){ o.material.roughness=1; o.material.metalness=0; } } });
      const s = i===0?0.9:1.4; obj.scale.setScalar(s);
      obj.position.set(i===0?-4.5:4.8, -2.6, i===0?-2.5:-3.2);
      obj.rotation.y = i===0?0.4:-0.6;
      scene.add(obj);
    }, undefined, ()=>{});
  });

  // Camera/state
  const camPos=new THREE.Vector3(), camLook=new THREE.Vector3();
  let prevCamPos=new THREE.Vector3(), prevCamLook=new THREE.Vector3();
  function setCam(px,py,pz,lx,ly,lz,fov=38){
    camPos.set(px,py,pz); camLook.set(lx,ly,lz);
    camera.position.copy(camPos); camera.lookAt(camLook); camera.fov=fov;
    const d=camera.position.distanceTo(camLook);
    camera.near=clamp(d-7,0.05,0.8); camera.far=d+45; camera.updateProjectionMatrix();
  }
  function updateShadows(){
    key.target.position.copy(camLook); key.target.updateMatrixWorld();
    const s=9; key.shadow.camera.left=-s; key.shadow.camera.right=s; key.shadow.camera.top=s; key.shadow.camera.bottom=-s;
    key.shadow.camera.updateProjectionMatrix();
  }

  setCam(0.2,2.8,6.2,0,0.35,0,40); prevCamPos.copy(camera.position); prevCamLook.copy(camLook);

  function evaluateFrame(frame){
    frame=clamp(frame,0,TOTAL_FRAMES-1);
    if(frame>=TOTAL_FRAMES-5) return evaluateFrame(0);
    const t=frame/FPS;

    // reset
    waterMat.opacity=0; waterTop.material.opacity=0; sedMat.opacity=0; ringMat.opacity=0;
    ribsGroup.children.forEach(c=>{ if(c.material) c.material.opacity=0; });
    xrayShell.material.opacity=0; healMat.opacity=0;
    accent.intensity=0; key.intensity=5.8; rim.intensity=3.0; fill.intensity=2.2; shaftMat.opacity=0.045;
    mammal.visible=true; amphib.visible=true; burrowGroup.visible=true; rockGroup.visible=true;
    rockGroup.position.set(0,0,0); rockGroup.rotation.set(0,0,0);
    burrowGroup.position.y=-0.1;

    let shot='hook';
    if(t<1.8){
      shot='hook';
      const p=t/1.8; const punch=1-easeOut(p);
      setCam(0.3+punch*0.8,2.9-p*0.5,6.8-p*1.8, 0,0.35,0, 42-p*3);
      key.intensity=6.5; fill.intensity=2.6;
      shaftMat.opacity=0.07;
    } else if(t<5.2){
      shot='setup';
      const p=(t-1.8)/3.4;
      setCam(lerp(1.0,-2.6,easeInOut(p)), lerp(2.4,1.5,easeInOut(p)), lerp(5.0,4.6,easeInOut(p)), lerp(0,-0.3,p), lerp(0.3,-0.15,p), 0.2, 36);
      rockGroup.position.y=lerp(0,-0.12,p);
      shaftMat.opacity=0.065;
    } else if(t<8.8){
      shot='two';
      const p=(t-5.2)/3.6;
      const ang=p*0.45;
      setCam(-1.8*Math.cos(ang)+0.2, 1.05+0.12*Math.sin(p*1.8), 3.4-0.4*p, 0.0,-0.20,0.28, 36);
      mammal.scale.y=0.78*(1+0.012*Math.sin(t*1.6));
      amphib.scale.y=0.84*(1+0.008*Math.sin(t*1.4+0.5));
      fill.intensity=2.4;
    } else if(t<11.2){
      shot='twist';
      const p=(t-8.8)/2.4;
      const punch=easeOut(clamp(p/0.25,0,1));
      setCam(lerp(-1.0,0.9,punch), lerp(1.0,0.65,punch), lerp(3.2,2.1,punch), 0.4,-0.18,0.3, lerp(34,30,punch));
      ringMat.opacity=p<0.45?0.9*(1-p/0.45):0; ring.scale.setScalar(1+p*10);
      accent.intensity=p<0.45?6.0*(1-p/0.45):0; key.intensity=7.0; rim.intensity=4.0; shaftMat.opacity=0.015;
    } else if(t<16.2){
      shot='evidence';
      const p=(t-11.2)/5.0;
      setCam(lerp(0.9,1.35,easeInOut(p)), 0.55, lerp(2.4,1.7,easeInOut(p)), 1.0,-0.20,0.25, 30);
      const xr=smooth(clamp((p-0.08)/0.25,0,1));
      const xf=1-smooth(clamp((p-0.75)/0.25,0,1))*0.3;
      ribsGroup.children.forEach(c=>{ if(c.material && c.material.blending===THREE.AdditiveBlending && c!==healGlow) c.material.opacity=Math.min(1,1.15*xr*xf); });
      healMat.opacity=0.65*xr*xf*(0.7+0.3*Math.sin(t*3.2));
      xrayShell.material.opacity=0.28*xr*xf;
      ribsGroup.position.copy(amphib.position); ribsGroup.rotation.copy(amphib.rotation); ribsGroup.scale.copy(amphib.scale);
      coldFill.intensity=2.2*xr;
    } else if(t<23.2){
      shot='reveal';
      const p=(t-16.2)/7.0;
      if(p<0.45){
        const pp=p/0.45;
        setCam(lerp(1.8,0.7,pp), 0.95, 3.4, lerp(0.9,0.2,pp), -0.2, 0.22, 32);
        amphib.position.x=lerp(2.5,1.1,easeOut(pp)); amphib.position.z=lerp(1.4,0.25,easeOut(pp));
        amphib.rotation.y=lerp(Math.PI-0.7,Math.PI-0.22,easeOut(pp));
      } else {
        const pp=(p-0.45)/0.55;
        setCam(lerp(0.7,-1.7,easeInOut(pp)), lerp(0.95,1.05,easeInOut(pp)), lerp(3.4,3.1,easeInOut(pp)), lerp(0.2,-0.9,pp), -0.22, 0.3, 30);
        fill.intensity=1.7+0.2*Math.sin(t*1.4);
      }
    } else if(t<27.5){
      shot='flood';
      const p=(t-23.2)/4.3;
      setCam(lerp(-0.6,0.2,easeInOut(p)), lerp(0.85,1.55,easeInOut(p)), lerp(2.8,3.8,easeInOut(p)), 0.05,-0.22,0.22, 36);
      const wp=smooth(clamp((p-0.12)/0.55,0,1));
      waterMat.opacity=0.72*wp; waterTop.material.opacity=0.55*wp;
      water.position.y=lerp(-1.2,-0.05,wp); waterTop.position.y=lerp(-0.5,0.55,wp);
      const sp=clamp((p-0.25)/0.7,0,1);
      sedMat.opacity=0.9*sp*(1-smooth(clamp((p-0.9)/0.1,0,1)));
      const arr=sedGeo.attributes.position.array;
      for(let i=0;i<sedCount;i++){ const seed=sedSeed[i]; const fall=sp*(1.9+seed*1.3); arr[i*3+1]=lerp(1.8+seed*2.8,-0.45+seed*0.25,clamp(fall/2.2,0,1)); arr[i*3]=sedBase[i*3]+Math.sin(t*1.5+seed*6)*0.04; }
      sedGeo.attributes.position.needsUpdate=true;
      shaftMat.opacity=0.03; rim.intensity=2.2; key.intensity=5.5;
      if(wp>0.6){ burrowGroup.visible=true; }
    } else if(t<32.2){
      shot='payoff';
      const p=(t-27.5)/4.7;
      setCam(lerp(0.0,0.5,easeInOut(p)), lerp(2.0,2.8,easeInOut(p)), lerp(5.0,6.4,easeInOut(p)), 0,0.25,0, 39);
      burrowGroup.visible = p < 0.35;
      if(p>=0.35){ waterMat.opacity=0; waterTop.material.opacity=0; sedMat.opacity=0; }
      rockGroup.rotation.y=lerp(0,0.06,easeInOut(p));
      key.intensity=6.0; shaftMat.opacity=0.055;
    } else {
      shot='loop';
      const p=(t-32.2)/(DUR-32.2);
      setCam(lerp(0.5,0.3,easeInOut(p)), lerp(2.8,2.9,easeInOut(p)), lerp(6.4,6.8,easeInOut(p)), 0,lerp(0.25,0.35,easeInOut(p)),0, lerp(39,42,easeInOut(p)));
      rockGroup.rotation.y=lerp(0.06,0,p);
      burrowGroup.visible=true; burrowGroup.position.y=-0.1;
      mammal.position.set(-0.95,-0.22,0.35); mammal.rotation.set(0,0.12,-0.12); mammal.scale.set(0.78,0.78,0.78);
      amphib.position.set(1.1,-0.30,0.25); amphib.rotation.set(0,Math.PI-0.22,0.04); amphib.scale.set(0.84,0.84,0.84);
      key.intensity=lerp(6.0,6.5,easeInOut(p)); fill.intensity=2.6; shaftMat.opacity=0.07;
    }

    // dust absolute
    const darr=dustGeo.attributes.position.array;
    for(let i=0;i<dustCount;i++){ const seed=dSeed[i]; darr[i*3]=dBase[i*3]+0.15*Math.sin(t*0.28+seed*7.0); darr[i*3+1]=dBase[i*3+1]+0.12*Math.sin(t*0.38+seed*10.0); darr[i*3+2]=dBase[i*3+2]+0.08*Math.cos(t*0.22+seed*5.0); }
    dustGeo.attributes.position.needsUpdate=true;

    updateShadows();

    // motion vector for postfx (approx from camera move)
    const mv = new THREE.Vector2((camPos.x-prevCamPos.x)*0.02, -(camPos.y-prevCamPos.y)*0.02);
    prevCamPos.copy(camPos); prevCamLook.copy(camLook);

    const focusDist = camera.position.distanceTo(camLook);
    const post = {
      focusDist, dofRange: shot==='evidence'?18:28, maxBlur: shot==='twist'?5.5:3.2,
      bloomAmt: shot==='twist'?0.75:0.48, exposure: shot==='twist'?1.35:1.28,
      time: t, motionVec: mv
    };

    return { frame, time:t, shot, totalFrames: TOTAL_FRAMES, post };
  }

  evaluateFrame(0);
  return { evaluateFrame, TOTAL_FRAMES, FPS, DUR };
}
