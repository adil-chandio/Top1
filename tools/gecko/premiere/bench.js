import * as THREE from 'three';
import { bevel, glowTexture, mesh, rng, texture, V } from '../../demo-render/stage.js';
import { digit, foot } from '../model.js';
import { clamp, between, digitSamples, mix, release } from '../motion.js';
import { softSurface } from './look.js';

const dlen=.614, breadth=1.19, meshScale=5.95, root=-.291;
export function padBench(group,palette) {
  const glow=glowTexture();
  const brushed=texture(768,384,(ctx,w,h)=>{
    const rand=rng(95289);ctx.fillStyle='#899491';ctx.fillRect(0,0,w,h);
    for(let i=0;i<3710;i++){
      const g=i%3===0?'#ddd9bf36':'#0d151a19';ctx.fillStyle=g;ctx.fillRect(rand()*w,rand()*h,1+rand()*w*.137,.45+rand()*.55);
    }
  });
  const alloy=softSurface('#566960',{map:brushed,shininess:53,specular:0x76998a});
  const edge=softSurface('#85a99b',{shininess:68,specular:0xa0b5a4});
  const p=mesh(group,new THREE.PlaneGeometry(7.58,4.65),softSurface('#344b45',{
    transparent:true,depthWrite:false,opacity:.79,shininess:91,specular:0xa6bdad,emissive:0x18211f,emissiveIntensity:.41,
  }),0,0,0);
  p.renderOrder=3;
  const base=mesh(group,new THREE.PlaneGeometry(10.2,8.07),new THREE.MeshBasicMaterial({color:'#142727'}),0,0,-2.65);
  const frm=new THREE.Group();group.add(frm);
  for(const j of [-1,1]) {
    bevel(frm,[7.64,.050,.227],.013,alloy,[0,j*2.352,-.131]);
    bevel(frm,[.068,4.78,.211],.013,alloy,[j*3.811,0,-.131]);
    bevel(frm,[7.65,.016,.022],.005,edge,[0,j*2.367,-.029]);
    bevel(frm,[.017,4.76,.019],.005,edge,[j*3.815,0,-.023]);
  }
  const track=texture(768,384,(ctx,w,h)=>{
    ctx.clearRect(0,0,w,h);const r=rng(45965);
    for(let i=0;i<783;i++){
      ctx.fillStyle=i%5===0?'#d3f5d833':'#cee6d216';ctx.fillRect(r()*w,r()*h,1+r()*7,.3+r()*.7);
    }
  });
  const sheen=mesh(group,new THREE.PlaneGeometry(7.28,4.6),new THREE.MeshBasicMaterial({map:track,color:'#cbe7d6',transparent:true,opacity:.36,depthWrite:false}),0,0,.001);
  sheen.renderOrder=4;
  const soft=mesh(group,new THREE.PlaneGeometry(4.74,1.40),new THREE.MeshBasicMaterial({map:glow,color:'#080e0c',transparent:true,depthWrite:false,opacity:.59}),-.49,-.08,.0018);
  soft.renderOrder=6;
  const caustic=mesh(group,new THREE.PlaneGeometry(6.64,1.87),new THREE.MeshBasicMaterial({map:glow,color:'#6d9282',transparent:true,blending:THREE.AdditiveBlending,depthWrite:false,opacity:.38}),.72,-.62,.0012);
  caustic.rotation.z=.09;caustic.renderOrder=5;
  const tile=new THREE.Group();group.add(tile);tile.scale.setScalar(meshScale);
  const toe=digit(tile,palette,dlen,breadth,true,60,15);
  const heel=mesh(tile,new THREE.SphereGeometry(1,26,16),palette.leg,root-.10,0,.063);heel.scale.set(.261,.111,.062);
  const ghostGroup=new THREE.Group();group.add(ghostGroup);ghostGroup.scale.set(meshScale,meshScale,-meshScale);
  const dark=(material)=>{
    const m=material.clone();m.color.multiplyScalar(.39);m.specular?.multiplyScalar(.19);
    // A planar reflection is visible only on rays passing through the finite
    // top face of the glass. Never let the virtual geometry leak below its rim.
    m.customProgramCacheKey=()=> 'finite-glass-reflection-aperture';
    m.onBeforeCompile=(shader)=>{
      shader.vertexShader='varying vec3 reflectWorld;\n'+shader.vertexShader.replace('#include <project_vertex>',`#include <project_vertex>
        vec4 aperturePoint=vec4(transformed,1.0);
        #ifdef USE_INSTANCING
          aperturePoint=instanceMatrix*aperturePoint;
        #endif
        reflectWorld=(modelMatrix*aperturePoint).xyz;`);
      shader.fragmentShader='varying vec3 reflectWorld;\n'+shader.fragmentShader.replace('#include <clipping_planes_fragment>',`#include <clipping_planes_fragment>
        float crossAt=cameraPosition.z/max(.00001,cameraPosition.z-reflectWorld.z);
        vec2 panePoint=mix(cameraPosition.xy,reflectWorld.xy,crossAt);
        if(abs(panePoint.x)>3.788||abs(panePoint.y)>2.324) discard;`);
    };
    return m;
  };
  const ghost={...palette,pad:dark(palette.pad),claw:dark(palette.claw),lamella:dark(palette.lamella),leg:dark(palette.leg)};
  const mirror=digit(ghostGroup,ghost,dlen,breadth,true,31,15);
  const reflectHeel=mesh(ghostGroup,new THREE.SphereGeometry(1,18,10),ghost.leg,root-.10,0,.063);reflectHeel.scale.copy(heel.scale);
  const unit=new THREE.Group();group.add(unit);unit.scale.setScalar(4.20);
  const palm=foot(unit,palette,1,true);
  const arm=mesh(unit,new THREE.CapsuleGeometry(.094,.44,7,18),palette.leg,-.031,-.26,.112);arm.rotation.x=-.28;
  const load=new THREE.Group();group.add(load);
  const emissive=new THREE.MeshBasicMaterial({color:'#9de9c7',transparent:true,depthWrite:false,toneMapped:false});
  const needle=mesh(load,new THREE.ConeGeometry(.086,.241,3),emissive);needle.rotation.z=Math.PI/2;
  const vector=mesh(load,new THREE.BoxGeometry(1,.027,.015),emissive);
  needle.renderOrder=8;vector.renderOrder=8;
  const legend=mesh(load,new THREE.PlaneGeometry(3.43,.009),new THREE.MeshBasicMaterial({color:'#7e9b8c',transparent:true,opacity:.32,depthWrite:false}),-.10,-1.03,.024);
  legend.renderOrder=7;
  const lines=Array.from({length:13},()=>mesh(group,new THREE.PlaneGeometry(.177,.020),new THREE.MeshBasicMaterial({
    color:'#adddc6',transparent:true,opacity:.65,depthWrite:false,toneMapped:false,
  })));
  lines.forEach(m=>{m.renderOrder=8;});
  return (t,kind,cut)=>{
    const ventral=kind==='foot'||kind==='lamella';
    const wide=kind==='foot'||kind==='peeled';
    const replay=kind==='replay',recap=kind==='recap-peel';
    const steady=kind==='shear'||kind==='shear-locked'||kind==='recap-shear';
    const recapShear=kind==='recap-shear';
    const local=replay?mix(35.44,38.83,clamp((t-41.125)/3.54)):recap?mix(35.37,39.20,clamp((t-55.458)/2.38)):t;
    const action=release(local,cut.marks.curlStart,cut.marks.digitRelease);
    const curl=ventral||steady?0:action.curl;
    const lift=ventral||steady||replay?0:action.palmLift;
    p.visible=base.visible=sheen.visible=soft.visible=caustic.visible=!ventral;
    tile.visible=!wide;unit.visible=wide;ghostGroup.visible=!wide&&!ventral;
    const loadingAt=recapShear?54.22:cut.marks.shear;
    const force=steady?between(t,loadingAt,loadingAt+(recapShear?.80:1.28)):0;
    const padAge=release(local,cut.marks.curlStart,cut.marks.digitRelease);
    let contact=[];
    if(wide){
      palm.update([-.038,-.106,lift],.093+.059*between(t,39.04,40.47),curl,ventral);
      arm.position.set(-.031,-.303,lift+.111);
    } else {
      const z=lift*.68;
      toe.update([root,0,z],Math.PI/2,curl,ventral||steady);
      heel.position.set(root-.104-.009*force,0,z+.063);
      if(ghostGroup.visible){mirror.update([root,0,z],Math.PI/2,curl,false);reflectHeel.position.copy(heel.position);}
      contact=digitSamples(dlen,curl,breadth,104);
    }
    soft.position.set(wide?-.16:-.39,wide?.52:-.015,.0027);soft.rotation.z=wide?Math.PI/2:.034;
    soft.scale.set(1+.20*lift/.22,1+.39*lift/.22,1);soft.material.opacity=.60*(1-.82*lift/.22);
    caustic.position.set(.80+.12*Math.sin(t*.77),-.56+.045*Math.sin(t),.002);caustic.material.opacity=.40+.085*force;
    for(const [i,m] of lines.entries()){
      const at=mix(.291,.907,i/(lines.length-1));
      const dot=contact[Math.round(at*104)];
      const peeling=kind==='peel-wide'||kind==='peel-side'||recap||replay;
      m.visible=!!dot?.contact&&!wide&&!ventral&&(steady||peeling)&&lift<.009;
      m.position.set((root+dlen*at)*meshScale,replay?.675:-.603,.014);
      const rise=steady?between(t,loadingAt+.09,loadingAt+.58):between(local,35.13,36.01);
      m.material.opacity=.55*rise*(1-.31*(padAge.curl));
    }
    load.visible=steady;
    if(steady){
      const start=1.41,end=start-(.14+force*2.24),y=-.904;
      needle.position.set(end,y,.043);vector.position.set((start+end)*.5+.039,y,.045);vector.scale.x=Math.max(.077,start-end-.101);
      emissive.opacity=.10+.77*between(t,loadingAt-.026,loadingAt+.42);
    }
    const world=contact.length?{
      tip:[(root+contact.at(-2).x)*meshScale,0,(contact.at(-2).z+lift*.68)*meshScale],
      base:[(root+contact[24].x)*meshScale,0,(contact[24].z+lift*.68)*meshScale],
    }:{};
    return {contact:!wide ? contact.filter(s=>s.contact).length : undefined,load:force,lift,world};
  };
}
