import * as THREE from 'three';
import cut from '#gecko-cut';
import dm from '@fontsource-variable/dm-sans/files/dm-sans-latin-wght-normal.woff2?url';
import sg from '@fontsource-variable/space-grotesk/files/space-grotesk-latin-wght-normal.woff2?url';
import { lensStage } from '../../demo-render/lens.js';
import { between, clamp } from '../motion.js';
import { createPremiereLook } from './look.js';
import { premiereFilm } from './film.js';
import { premiereTitles } from './titles.js';

const W=1080,H=1920,opts=new URLSearchParams(location.search);
const raster=clamp(+(opts.get('raster')??.72),.40,1);
const w=Math.round(W*raster),h=Math.round(H*raster);
const canvas=document.querySelector('canvas');canvas.width=W;canvas.height=H;
const ctx=canvas.getContext('2d',{alpha:false});ctx.imageSmoothingQuality='high';
const renderer=new THREE.WebGLRenderer({alpha:false,antialias:false,precision:'highp',preserveDrawingBuffer:false,powerPreference:'high-performance'});
renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;
const look=await createPremiereLook();
const film=premiereFilm(look,cut), optical=lensStage(renderer);
for(const [name,url] of [['Copy',dm],['Display',sg]])document.fonts.add(await new FontFace(name,`url(${url})`,{weight:'100 1000'}).load());
const drawTitles=premiereTitles(ctx,cut);
const vignette=ctx.createRadialGradient(W*.52,H*.487,H*.174,W*.51,H*.493,H*.715);
vignette.addColorStop(0,'#09091000');vignette.addColorStop(.72,'#080a130d');vignette.addColorStop(1,'#06142279');
const kind=(t)=>{
  const index=Math.max(0,cut.shots.findLastIndex(s=>s.frame<=t*cut.fps+1e-7));
  const s=cut.shots[index],a=s.frame/cut.fps,b=(cut.shots[index+1]?.frame??cut.frames)/cut.fps;
  return {...s,index,age:t-a,remaining:b-t,progress:clamp((t-a)/(b-a))};
};
window.monarchGeckoFrame=(t)=>{
  t=clamp(t,0,cut.duration-1/cut.fps);
  const s=kind(t),physics=film.update(t,s);
  if(film.lens(s.kind)&&opts.get('optics')!=='direct'){
    renderer.toneMappingExposure=1;
    optical(film.scene,film.cam,w,h,t);
  }else{
    if(renderer.domElement.width!==w||renderer.domElement.height!==h)renderer.setSize(w,h,false);
    renderer.toneMappingExposure=film.cam.userData.lens.exposure;
    renderer.render(film.scene,film.cam);
  }
  ctx.globalAlpha=1;ctx.drawImage(renderer.domElement,0,0,W,H);
  ctx.fillStyle=vignette;ctx.fillRect(0,0,W,H);
  drawTitles(t,s,physics);
  const fade=between(t,61.38,61.995);
  if(fade){ctx.fillStyle=`rgba(4,7,9,${fade})`;ctx.fillRect(0,0,W,H);}
  return canvas.toDataURL('image/jpeg',.947).split(',')[1];
};
