import * as THREE from 'three';
import skinURL from './assets/dorsal-albedo.jpg?url';
import irisURL from './assets/iris-albedo.jpg?url';
import canopyURL from './assets/night-canopy.jpg?url';
import { between, clamp, mix } from '../motion.js';

const TAU=2*Math.PI;
const mirror=(n)=>1-Math.abs(1-((n%2+2)%2));
const load = (url)=>new Promise((ok,bad)=>{const img=new Image();img.onload=()=>ok(img);img.onerror=()=>bad(new Error(`Missing look-dev plate ${url}`));img.src=url;});
const srgb=(im)=>{const t=new THREE.Texture(im);t.colorSpace=THREE.SRGBColorSpace;t.needsUpdate=true;t.anisotropy=4;return t;};
function toCanvas(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;return c;}
function painter(img) {
  const c=toCanvas(img.width,img.height),ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(img,0,0);
  const {data:src}=ctx.getImageData(0,0,c.width,c.height), w=c.width,h=c.height;
  return function make(kind){
    const body=kind==='body', head=kind==='rim', digit=kind==='toe';
    const [W,H]=body?[2450,1152]:digit?[650,480]:head?[448,448]:[872,604];
    const color=toCanvas(W,H), bump=toCanvas(W,H), co=color.getContext('2d'), bu=bump.getContext('2d');
    const pixels=co.createImageData(W,H), relief=bu.createImageData(W,H);
    for(let j=0;j<H;j++) {
      const v=1-j/(H-1), a=v*TAU, vent=(1-between(Math.sin(a),-.77,.15))*(head?.35:1);
      const bend=.061*Math.sin(a*2.01)+.027*Math.sin(a*3.58+.8);
      for(let i=0;i<W;i++) {
        const u=i/(W-1);
        const long=body?u*3.55+bend+.09*Math.sin(u*21.3+a*.87):u*(digit?.72:head?.51:1.13)+bend+(digit?.65:head?.21:1.29);
        const cross=body ? v*1.87+.104*Math.sin(u*15+2.2*v)+.042*Math.sin(u*29.7-v*3) : v*(digit?.77:.95)+.19+.106*Math.sin(u*6.1+a*.45);
        const X=Math.min(w-1,Math.round((w-1)*mirror(long))),Y=Math.min(h-1,Math.round((h-1)*mirror(cross)));
        const k=4*(Y*w+X), q=4*(j*W+i);
        const red=src[k],green=src[k+1],blue=src[k+2];
        // Milder luminosity variation on the ventral half, preserve the grooves.
        const orange=between(red-green,15,72), L=.23*red+.53*green+.24*blue;
        const grained=L+23*orange;
        const grain=clamp((grained-98)*.66,-37,58);
        const striation=(body?1-between(u,.18,.39):0)*(.5+.5*Math.cos(u*112+2.6*Math.sin(a)))*.22;
        const whiten=vent*(.79-.13*between(-Math.sin(a),.5,1));
        pixels.data[q]=mix(red*.99+11-striation*red,167+grain,whiten);
        pixels.data[q+1]=mix(green*1.032+4-striation*green,153+grain*.93,whiten);
        pixels.data[q+2]=mix(blue*1.09+7-striation*blue,126+grain*.89,whiten);
        pixels.data[q+3]=255;
        const res=clamp(128+(grained-118)*1.55,33,235);
        relief.data[q]=relief.data[q+1]=relief.data[q+2]=res;relief.data[q+3]=255;
      }
    }
    co.putImageData(pixels,0,0);bu.putImageData(relief,0,0);
    if(body) {
      // UV coordinates track the closed labial crease in the same 3D head.
      const y0=-3.18,y1=2.213,u0=1.112,u1=2.177;
      for(const sign of [1,-1]) for(const [offset,width,hue] of [[-.0061,4.2,'#af9b8ac4'],[0,3.0,'#161612e9']]){
        for(let k=0;k<124;k++){
          const v=k/124,z=(k+1)/124;
          const coords=(t)=>{const angle=Math.asin(mix(-.193,-.363,between(t,0,1)));const ring=sign>0?1+angle/TAU:.5-angle/TAU;
            return [(mix(u0,u1,t)-y0)/(y1-y0)*W,(1-ring+offset)*H];};
          co.strokeStyle=hue;co.lineWidth=width*between(v,0,.11)*(1-between(v,.93,1))+.10;co.lineCap='round';
          co.beginPath();co.moveTo(...coords(v));co.lineTo(...coords(z));co.stroke();
        }
      }
    }
    const map=srgb(color), bumpMap=new THREE.CanvasTexture(bump);bumpMap.anisotropy=4;
    return {map,bumpMap,reliefAt:(u,v)=>relief.data[4*(Math.round((1-clamp(v))*(H-1))*W+Math.round(clamp(u)*(W-1)))]/255};
  };
}

export const softSurface=(color,mapOptions={})=>new THREE.MeshPhongMaterial({color,shininess:23,specular:0x43443a,...mapOptions});
export async function createPremiereLook(){
  const [skin,iris,canopy]=await Promise.all([load(skinURL),load(irisURL),load(canopyURL)]);
  const atlas=painter(skin);
  const maps=atlas('body');
  const material=(tiles,shine,bump,glint)=>{
    const {map,bumpMap}=tiles;
    return softSurface(0xffffff,{map,bumpMap,shininess:shine,bumpScale:bump,specular:new THREE.Color(glint)});
  };
  const body=material(maps,36,.0168,'#494746');
  const leg=material(atlas('limb'),26,.0154,'#42423d');
  const pad=material(atlas('toe'),23,.0148,'#46403a');
  const lid=material(atlas('rim'),31,.011,'#454038');
  const lamella=softSurface('#e1c9af',{specular:0x423a31,shininess:26});
  const claw=softSurface('#b6a183',{specular:0x85755f,shininess:48});
  const irisMat=softSurface('#ffedae',{map:srgb(iris),specular:0xcde0f4,shininess:130,emissive:0x1e1007,emissiveIntensity:.13});
  return {palette:{body,leg,pad,lid,lamella,claw,iris:irisMat,refined:true,reliefAt:maps.reliefAt},canopy:srgb(canopy)};
}
