import * as THREE from 'three';
import cut from '#gecko-cut';
import gpFont from '@fontsource-variable/dm-sans/files/dm-sans-latin-wght-normal.woff2?url';
import { lensStage } from '../demo-render/lens.js';
import { labEnvironment } from '../demo-render/air-crush.js';
import { kineticPhrases } from '../demo-render/air-crush-titles.js';
import { geckoFilm } from './film.js';
import { clamp, smooth } from './motion.js';

const W=1080,H=1920;
const raster=clamp(+(new URLSearchParams(location.search).get('raster')??.68),.36,1);
const w=Math.round(W*raster),h=Math.round(H*raster);
const canvas=document.querySelector('canvas'); canvas.width=W;canvas.height=H;
const ctx=canvas.getContext('2d',{alpha:false});ctx.imageSmoothingQuality='high';
const renderer=new THREE.WebGLRenderer({alpha:false,antialias:false,preserveDrawingBuffer:true,powerPreference:'high-performance'});
renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1;
const pmrem=new THREE.PMREMGenerator(renderer);const environment=labEnvironment(pmrem);pmrem.dispose();
const film=geckoFilm(environment,cut), optical=lensStage(renderer);
const font=new FontFace('Copy',`url(${gpFont})`,{weight:'100 1000'});document.fonts.add(await font.load());
const key=new Set(['wall','go','step','grip','controlled','tokay','toes','setae','branching','contact','suction','waals','adhere','direction','base','surface','curl','detach','hyperextension','microscopic','yank','loading','movement','gripping','possible']);
const captions=kineticPhrases(ctx,W,H,cut.captions,key,t=>t>=10.54&&t<48.89?'#b5e7d9':'#f7d1a3',()=>.837);
const shades=ctx.createRadialGradient(W*.52,H*.45,H*.14,W*.52,H*.45,H*.68);
shades.addColorStop(0,'#06090c00');shades.addColorStop(.70,'#05090e10');shades.addColorStop(1,'#0408138e');
const labelMap={ through:'THROUGH THE GLASS', foot:'TOKAY GECKO  /  GEKKO GECKO', lamella:'TOE PAD  /  ENLARGED', setae:'SETAE  /  ENLARGED SCHEMATIC', vanderwaals:'CLOSE CONTACT  /  SCHEMATIC', shear:'LOAD TOWARD TOE BASE', 'peel-wide':'DISTAL TIP RELEASE', replay:'DIGITAL HYPEREXTENSION  /  SLOW VIEW', angles:'SETAL SHAFT  /  MICRO VIEW' };
const choose=(t)=>{
  const i=Math.max(0,cut.shots.findLastIndex(s=>s.frame<=t*cut.fps+1e-7));
  const s=cut.shots[i],age=t-s.frame/cut.fps, span=((cut.shots[i+1]?.frame??cut.frames)-s.frame)/cut.fps;
  return {...s,age,remaining:span-age,progress:clamp(age/span),index:i};
};
function exposure(t,s){
  film.update(t,s);
  if (film.usesLens(s.kind)) optical(film.scene,film.cam,w,h,t);
  else {
    if(renderer.domElement.width!==w||renderer.domElement.height!==h)renderer.setSize(w,h,false);
    renderer.toneMappingExposure=film.cam.userData.lens.exposure;
    renderer.render(film.scene,film.cam);
  }
}
function render(t,artwork=false) {
  t=clamp(t,0,cut.duration-1/cut.fps);
  const s=choose(t);
  // One centered 24 fps sample per picture; no cross-cut blending. Author
  // camera and rig continuity in world space rather than by image morphing.
  exposure(t,s);
  ctx.globalAlpha=1;ctx.drawImage(renderer.domElement,0,0,W,H);
  ctx.fillStyle=shades;ctx.fillRect(0,0,W,H);
  if(!artwork) {
    captions(t);
    const label=labelMap[s.kind];
    if(label){
      const a=.78*smooth(s.age/.23)*smooth(s.remaining/.30);
      ctx.save();ctx.globalAlpha=a;ctx.font='720 23px Copy';ctx.fillStyle='#d5e7df';ctx.textAlign='left';ctx.shadowColor='#111519';ctx.shadowBlur=9;
      ctx.fillText(label,64,H*.075);ctx.restore();
    }
    const outro=smooth((t-61.43)/.565);
    if(outro>0){ctx.fillStyle=`rgba(4,7,9,${outro*.98})`;ctx.fillRect(0,0,W,H);}
  }
  return canvas.toDataURL('image/jpeg',.94).split(',')[1];
}
window.monarchGeckoFrame=render;
