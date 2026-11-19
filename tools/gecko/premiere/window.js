import * as THREE from 'three';
import { bevel, glowTexture, mesh, rng, texture, V } from '../../demo-render/stage.js';
import { clamp, digitSamples, mix } from '../motion.js';
import { softSurface } from './look.js';

function leafGeometry() {
  const pos=[],uv=[],ix=[],n=24;
  for(let i=0;i<=n;i++){
    const u=i/n,w=Math.sin(Math.PI*u)**.69*.37;
    for(let j=0;j<3;j++){
      const v=j-1;
      pos.push(v*w+.059*Math.sin(u*4.4),u, .17*Math.sin(u*Math.PI)-.16*v*v*w);
      uv.push(j*.5,u);
      if(i<n&&j<2){const k=i*3+j;ix.push(k,k+1,k+3,k+1,k+4,k+3);}
    }
  }
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ix);g.computeVertexNormals();return g;
}

function contactOcclusion(group) {
  const canvas=document.createElement('canvas'),w=288,h=336,sx=6.0,sy=7.0;
  canvas.width=w;canvas.height=h;const c=canvas.getContext('2d');
  const stamp=document.createElement('canvas');stamp.width=stamp.height=64;
  const stampCtx=stamp.getContext('2d'),g=stampCtx.createRadialGradient(32,32,1,32,32,32);
  g.addColorStop(0,'#08100aef');g.addColorStop(.49,'#080c0b96');g.addColorStop(.82,'#1c22152a');g.addColorStop(1,'#1c221500');
  stampCtx.fillStyle=g;stampCtx.fillRect(0,0,64,64);
  const map=new THREE.CanvasTexture(canvas);map.colorSpace=THREE.SRGBColorSpace;
  const surface=mesh(group,new THREE.PlaneGeometry(sx,sy),new THREE.MeshBasicMaterial({map,transparent:true,depthWrite:false,opacity:.82}),0,0,-.002);
  surface.renderOrder=5;
  const pcoord=(x,y)=>[(x/sx+.5)*w,(-y/sy+.5)*h];
  const shadow=(x,y,width,height,angle,opacity)=>{
    const [ac,bc]=pcoord(x,y);c.save();c.translate(ac,bc);c.rotate(angle);c.globalAlpha=opacity;
    const a=width*w/sx,b=height*h/sy;c.drawImage(stamp,-a/2,-b/2,a,b);c.restore();
  };
  const splay=[-.96,-.49,-.071,.391,.920], len=[.276,.418,.514,.475,.344];
  return (p,through)=>{
    surface.visible=!through;if(through)return;
    surface.position.set(p.x,p.y-.03,-.002);
    c.clearRect(0,0,w,h);
    shadow(-.10,-.06,2.10,4.81,.06,.33);
    shadow(.20,1.31,1.40,1.46,.05,.22);
    for(const l of p.limb) {
      const z=l.at[2],amt=1-.80*clamp(z/.295);
      const x=l.at[0]-p.x,y=l.at[1]-p.y+.03;
      shadow(x,y,.47+.42*z,.45+.42*z,l.yaw,.53*amt);
      for(let i=0;i<len.length;i++){
        const angle=l.yaw+splay[i]*l.side, d=(i-2)*.046*l.side,forward=.083-.015*Math.abs(i-2);
        const u=x+Math.sin(l.yaw)*forward+Math.cos(l.yaw)*d;
        const v=y+Math.cos(l.yaw)*forward-Math.sin(l.yaw)*d;
        const foot=digitSamples(len[i],clamp(l.curl*(.914+.043*i)),1,20).filter(n=>n.contact);
        const s=foot.at(-1)?.x??.18,e=foot[0]?.x??.095,along=(s+e)*.5;
        shadow(u+Math.sin(angle)*along,v+Math.cos(angle)*along,.189+z*.5,.139+(s-e)*1.26+z*.32,angle,.38*amt);
      }
    }
    map.needsUpdate=true;
  };
}

export function rainWindow(group,canopy) {
  const back=mesh(group,new THREE.PlaneGeometry(11.80,21.25),new THREE.MeshBasicMaterial({map:canopy,color:0x899e97,fog:false}),1.00,1.13,-5.18);
  const reverse=mesh(group,new THREE.PlaneGeometry(12.30,22.15),new THREE.MeshBasicMaterial({map:canopy,color:0x607f79,fog:false,side:THREE.BackSide}),-.18,1.39,6.76);
  reverse.scale.x=-1;
  // At the shallow side angle the camera sees across the pane. A second
  // diffuse depth card is perpendicular to the canopy rather than screen-space.
  const side=mesh(group,new THREE.PlaneGeometry(15.20,18.90),new THREE.MeshBasicMaterial({map:canopy,color:0x455f5c,fog:false}),-8.54,1.28,-.74);
  side.rotation.y=Math.PI/2;

  const metal=softSurface('#2a3838',{shininess:52,specular:0x546865});
  const edge=softSurface('#5f7472',{shininess:76,specular:0x7c9189});
  const black=softSurface('#162626',{shininess:18});
  for(const s of [-1,1]) {
    bevel(group,[.265,18.60,.30],.034,metal,[s*2.37,1.29,-.127]);
    bevel(group,[.033,18.60,.033],.006,edge,[s*2.235,1.29,.029]);
    bevel(group,[.078,18.60,.064],.011,black,[s*2.171,1.29,-.031]);
    for(let j=0;j<5;j++)bevel(group,[.108,.129,.082],.019,metal,[s*2.389,j*3.6-5.1,.069]);
  }
  const wipe=texture(512,512,(ctx,w,h)=>{
    const rr=rng(255086);
    for(let i=0;i<150;i++){
      const x=rr()*w,y=rr()*h,len=5+rr()*51;
      ctx.strokeStyle=i%7===0?'#c9efe536':'#bdd9bd11';ctx.lineWidth=.24+rr()*.85;
      ctx.beginPath();ctx.moveTo(x,y);ctx.quadraticCurveTo(x+len*.12,y+len*.44,x+len*.14,y+len);ctx.stroke();
    }
  });
  const pane=mesh(group,new THREE.PlaneGeometry(4.40,18.83),new THREE.ShaderMaterial({
    transparent:true,depthWrite:false,side:THREE.DoubleSide,blending:THREE.NormalBlending,toneMapped:false,
    uniforms:{clock:{value:0},fine:{value:wipe}},
    vertexShader:`varying vec2 aperture; varying vec3 eye; void main(){aperture=uv; vec4 p=modelViewMatrix*vec4(position,1.);eye=p.xyz;gl_Position=projectionMatrix*p;}`,
    fragmentShader:`
      varying vec2 aperture; varying vec3 eye; uniform float clock; uniform sampler2D fine;
      void main(){
        vec2 w=aperture;
        float f=pow(1.-abs(normalize(eye).z),3.4);
        float a=exp(-8.*abs(w.x-.17-.217*w.y-.013*sin(clock*.31)));
        float b=exp(-28.*abs(w.x-.79+.25*w.y));
        float c=exp(-40.*abs(w.x-.045-.076*w.y));
        float lace=texture2D(fine,w*vec2(1.,2.)).a;
        float light=.027+(a*.16+b*.153+c*.102)*(.39+.61*f)+lace*.29;
        vec3 cool=vec3(.30,.60,.55),warm=vec3(.90,.60,.35);
        vec3 ink=mix(cool,warm,min(1.,b*.74));
        gl_FragColor=vec4(ink,light);
      }`
  }),0,1.50,-.006);
  pane.renderOrder=1;
  const dryGlow=glowTexture();
  const fog=new THREE.Group();group.add(fog);
  const seeds=rng(5914),pos=[];
  for(let i=0;i<128;i++)pos.push((seeds()-.5)*15,(seeds()-.5)*22,(-4+seeds()*8));
  const fg=new THREE.BufferGeometry();fg.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
  const dots=new THREE.Points(fg,new THREE.PointsMaterial({map:dryGlow,color:'#e2cd9e',transparent:true,depthWrite:false,opacity:.38,size:.118,blending:THREE.AdditiveBlending}));
  fog.add(dots);
  const leaf=leafGeometry(),fronds=[];
  for(let i=0;i<20;i++){
    const side=i%2 ? -1:1, isHigh=i%4===0;
    const m=mesh(group,leaf,softSurface(i%3===0?'#1d3534':'#162e2a',{side:THREE.DoubleSide,specular:0x254133,shininess:13}),side*(4.05+seeds()*1.45),1.3+(seeds()-.5)*12,-4.76+seeds()*2.5);
    const k=.93+seeds()*1.26;
    m.scale.set(k*(isHigh?1.36:1),k,1);m.rotation.y=(seeds()-.5)*.87;
    const roll=(.48+seeds()*.95)*side;m.rotation.z=roll;
    fronds.push({m,roll,i});
  }
  const paint=contactOcclusion(group);
  return (t,p,through)=>{
    back.visible=!through;reverse.visible=through;side.visible=!through;
    back.position.y=1.16+p.y*.29;reverse.position.y=1.14+p.y*.25;
    back.position.x=.49+.16*Math.sin(t*.135);
    pane.material.uniforms.clock.value=t;
    fog.position.set(.09*Math.sin(t*.54),.13*Math.sin(t*.34),.124*Math.sin(t*.23));
    dots.material.opacity=through?.24:.32;
    for(const {m,roll,i} of fronds){m.visible=!through;m.rotation.z=roll+.047*Math.sin(t*.77+i*.84);}
    paint(p,through);
  };
}
