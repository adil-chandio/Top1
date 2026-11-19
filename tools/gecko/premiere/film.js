import * as THREE from 'three';
import { background, camera, frame, V } from '../../demo-render/stage.js';
import { between, mix } from '../motion.js';
import { gecko } from '../model.js';
import { microscope } from '../microscope.js';
import { rainWindow } from './window.js';
import { padBench } from './bench.js';
import { setups,liveKinds,microKinds,lensKinds } from './camera.js';

export function premiereFilm(look,cut) {
  const scene=new THREE.Scene();
  const cam=camera();cam.near=.030;cam.updateProjectionMatrix();
  const environment={
    night:background(['#0a191e','#152e2b','#30595050']),
    macro:background(['#080f18','#254138','#31564c6b']),
    micro:background(['#111922','#304b44','#9c634451']),
  };
  const key=new THREE.DirectionalLight('#ffe2bd',2.71);scene.add(key);
  const rim=new THREE.DirectionalLight('#a3ede7',1.43);scene.add(rim);
  const floor=new THREE.HemisphereLight('#87a7ae','#4c3a2a',1.13);scene.add(floor);
  const outside=new THREE.Group(), macro=new THREE.Group(), micro=new THREE.Group();scene.add(outside,macro,micro);
  const window=rainWindow(outside,look.canopy), reptile=gecko(outside,look.palette);
  const foot=padBench(macro,look.palette), shaft=microscope(micro,true);
  const followPad=new Set(['step','grip-anchor','no-yank']);
  function update(t,shot) {
    const {kind,progress}=shot;
    const isLive=liveKinds.has(kind), isMicro=microKinds.has(kind), beneath=['through','foot','lamella'].includes(kind);
    outside.visible=isLive;micro.visible=isMicro;macro.visible=!isLive&&!isMicro;
    scene.background=isLive?environment.night:isMicro?environment.micro:environment.macro;
    const eye=kind==='eye'||kind==='hero-eye';
    const frontRim=isLive?1.53:isMicro?1.25:1.15;
    key.intensity=eye?2.35:isLive?2.31:isMicro?2.58:2.42;
    key.color.set(isLive?'#ffdcaa':beneath?'#ffdbb7':'#ffe9c9');
    key.position.set(eye?3.30:isLive?3.31:2.35,eye?5.20:isLive?5.70:4.38,beneath?-5.1:eye?2.97:4.79);
    rim.intensity=beneath?1.44:frontRim;
    rim.color.set(isLive?'#a1d6e4':isMicro?'#b1e6ca':'#aadac9');
    rim.position.set(-5.24,isLive?3.07:2.83,beneath?-2.84:1.59);
    floor.intensity=beneath?1.23:(isMicro?.96:1.06);
    const origin=V(0,0,0);
    let physics={};
    if(isLive){
      const pose=reptile.update(t);
      origin.set(pose.x,pose.y,0);
      if(followPad.has(kind)){
        const active=pose.limb[0];
        // Camera follows the general foot, not its exact toe tips; the background
        // and footprint stay in view so its motion is apparent.
        origin.set(mix(active.at[0],pose.x+active.side*1.05,.22),mix(active.at[1],pose.y+.62,.25),active.at[2]*.20);
        if(kind==='no-yank')origin.set(mix(pose.limb[0].at[0],pose.x-1.10,.36),mix(pose.limb[0].at[1],pose.y+.57,.25),pose.limb[0].at[2]*.21);
      } else if (eye) {
        origin.x+=.46*(pose.eyePoints[1].x-pose.x-.58);origin.z+=.25*(pose.eyePoints[1].z-.78);
      }
      window(t,pose,beneath);
    } else if(isMicro){physics=shaft(t,kind,cut.marks);} else {physics=foot(t,kind,cut);}
    const st=setups[kind];
    cam.up.set(...st.up);
    const {p,q,a,b,mm,roll,aperture}=st;
    const cameraLead=isLive?.011:.006;
    const drift=V(cameraLead*Math.sin(t*1.36)+cameraLead*.44*Math.sin(t*3.9),cameraLead*.8*Math.sin(t*1.18+.41),0);
    frame(cam,progress,[V(...p).add(origin).add(drift),V(...q).add(origin).add(drift)],[V(...a).add(origin),V(...b).add(origin)],null,
      {mm,roll,aperture,bloom:eye?.83:.50,exposure:eye?1.03:isMicro?.96:1.00,smear:kind==='step'?.51:0});
    cam.updateMatrixWorld();
    if(physics.world){
      const pixels={};
      for(const [name,p] of Object.entries(physics.world)){
        const v=V(...p).project(cam);pixels[name]=[.5+.5*v.x,.5-.5*v.y];
      }
      physics={...physics,pixels};
    }
    return physics;
  }
  return {scene,cam,update,lens:(kind)=>lensKinds.has(kind)};
}
