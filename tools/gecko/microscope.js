import * as THREE from 'three';
import { pbr, mesh, texture, rng, V, glowTexture, bevel } from '../demo-render/stage.js';
import { between, mix, clamp } from './motion.js';

function rod(points, radius, segments=12, taper=0) {
  const curve=new THREE.CatmullRomCurve3(points.map((v)=>V(...v)));
  const result=new THREE.TubeGeometry(curve,segments,radius,8,false);
  if(taper){
    const {position}=result.attributes;
    const temp=V(0,0,0);
    for(let j=0;j<=segments;j++){
      const u=j/segments,p=curve.getPointAt(u);
      for(let i=0;i<=8;i++){
        const a=j*9+i;
        temp.fromBufferAttribute(position,a).sub(p).multiplyScalar(1-taper*u*u).add(p);
        position.setXYZ(a,temp.x,temp.y,temp.z);
      }
    }
    result.computeVertexNormals();
  }
  return result;
}
const obj = new THREE.Object3D();
const plateShape = new THREE.SphereGeometry(1,12,7);

// Representative shafts and terminal paddles. The count, field spacing and
// proportions are simplified for visibility. No literal bonds/fluids or cups.
function shaftField(parent, pattern, seed, material, tipMaterial, hero=false, refined=false) {
  const d=1.58;
  const stem=rod([[0,0,d],[.05,0,1.27],[.12,0,.92],[.28,0,.46],[.46,0,.21]],hero?(refined?.042:.055):(refined?.031:.036),12,refined?.56:0);
  const shafts=new THREE.InstancedMesh(stem,material,pattern.length);parent.add(shafts);
  const rand=rng(seed);
  const branchCount=hero?7:5;
  const branches = Array.from({length:branchCount},(_,i)=>{
    const v=(i-(branchCount-1)/2)*.0755,x=.667+.056*Math.cos(i*1.23);
    const b=rod([[.45,0,.22],[.515,v*.28,.142],[x-.033,v*.84,.061],[x,v,.027]],hero?(refined?.0135:.016):.013,8,refined?.56:0);
    const m=new THREE.InstancedMesh(b,material,pattern.length);parent.add(m);
    return {v,x,m};
  });
  const tips=new THREE.InstancedMesh(plateShape,tipMaterial,pattern.length*branchCount);parent.add(tips);
  for(const [i,[x,y]] of pattern.entries()) {
    const at=V(x,y,0), angle=(rand()-.5)*.29,k=.83+.24*rand();
    const matrix=new THREE.Matrix4().compose(at,new THREE.Quaternion().setFromAxisAngle(V(0,0,1),angle),V(k,k,1));
    shafts.setMatrixAt(i,matrix);
    shafts.setColorAt(i,new THREE.Color().setHSL(.077+.035*rand(),.15+.2*rand(),.63+.21*rand()));
    for(const [j,{v,x:tip,m}] of branches.entries()) {
      m.setMatrixAt(i,matrix);
      obj.position.set(tip,v,.024).applyMatrix4(matrix);obj.quaternion.setFromAxisAngle(V(0,0,1),angle);
      obj.scale.set(hero?.073:.068,hero?(refined?.042:.038):.033,.013);obj.updateMatrix();
      tips.setMatrixAt(i*branchCount+j,obj.matrix);
    }
  }

}

function supportTexture() {
  return texture(640,384,(ctx,w,h)=>{
    const rng1=rng(31881);ctx.fillStyle='#3d2726';ctx.fillRect(0,0,w,h);
    for(let i=0;i<8300;i++) {
      const x=rng1()*w,y=rng1()*h,r=1+rng1()*4.2;
      ctx.fillStyle=i%2?'#61382e':'#644638';ctx.beginPath();ctx.ellipse(x,y,r*1.6,r,0,0,Math.PI*2);ctx.fill();
    }
    for(let i=0;i<720;i++) {
      const x=rng1()*w,y=rng1()*h,z=1+rng1()*2.8;ctx.fillStyle='#ad82702a';ctx.fillRect(x,y,z*3,z);
    }
  });
}

export function microscope(parent,refined=false) {
  const phong=(color,more)=>new THREE.MeshPhongMaterial({color,shininess:23,specular:0x645247,...more});
  const fiber = refined?phong('#dcc29b',{emissive:0x493424,emissiveIntensity:.21}):pbr('#dbc6a0',.40,.07,{emissive:'#553a25',emissiveIntensity:.075});
  const spatula = refined?phong('#fae2b7',{shininess:41}):pbr('#f2d8ae',.39,.11);
  const tissueMap=supportTexture();
  const tissue = refined?phong('#ecd3b8',{map:tissueMap,bumpMap:tissueMap,bumpScale:.026,shininess:17}):pbr('#d5aca0',.60,.02,{map:tissueMap,bumpMap:tissueMap,bumpScale:.022});
  const glass=refined?phong('#34534d',{emissive:0x102520,emissiveIntensity:.40,shininess:68}):pbr('#335352',.36,.60,{emissive:'#091a19',emissiveIntensity:.38});
  const trim=pbr('#719994',.25,.72);
  mesh(parent,new THREE.BoxGeometry(12,7,.21),glass,0,0,-.107);
  const chip=bevel(parent,[6.74,3.2,.13],.031,trim,[0,0,-.105]);
  chip.material=pbr('#3b5a59',.28,.49,{emissive:'#091c19',emissiveIntensity:.24});
  const edge=pbr('#64958b',.26,.67);bevel(parent,[6.76,.020,.055],.006,edge,[0,-1.627,-.039]);
  const padRoot=new THREE.Group();padRoot.matrixAutoUpdate=false;parent.add(padRoot);
  const sparseRoot=new THREE.Group();sparseRoot.matrixAutoUpdate=false;parent.add(sparseRoot);
  const pattern=[];
  const s=rng(67236), rows=[-2.42,-1.47,-.52,.43,1.38,2.31];
  for(let i=0;i<rows.length;i++) {
    const pad=mesh(padRoot,new THREE.SphereGeometry(1,38,18),tissue,rows[i],0,1.75);
    pad.scale.set(.483,1.73,.207);
    for(let j=0;j<14;j++) for(let k=0;k<2;k++) pattern.push([rows[i]+(k-.5)*.277+(s()-.5)*.10,(j-6.5)*.222+(s()-.5)*.09]);
  }
  const scuteBed=mesh(padRoot,new THREE.SphereGeometry(1,48,20),tissue,-.03,.02,1.86);
  scuteBed.scale.set(2.89,1.77,.217);
  shaftField(padRoot,pattern,846131,fiber,spatula,false,refined);
  shaftField(sparseRoot,[[-1.33,-.64],[-.72,.68],[-.34,-.46],[.12,.26],[.61,-.13],[1.18,.57],[1.75,-.86]],252,fiber,spatula,true,refined);
  const part=mesh(sparseRoot,new THREE.SphereGeometry(1,36,18),tissue,.28,.02,1.75);part.scale.set(2.17,1.46,.197);
  const glow=glowTexture();
  const gleam=new THREE.Mesh(new THREE.PlaneGeometry(2.17,.95),new THREE.MeshBasicMaterial({ map:glow,color:'#5bcebd',blending:THREE.AdditiveBlending,depthWrite:false,transparent:true,opacity:.22 }));
  gleam.position.set(.65,-.12,.002);parent.add(gleam);
    return (t,index,marks)=>{
    const sparseView = ['branched','contact-ground','vanderwaals','vd-detail','angles','angle-detail','recap-contact'].includes(index);
    const recap=index==='recap-contact', compare=index==='angles'||index==='angle-detail';
    padRoot.visible=!sparseView;sparseRoot.visible=sparseView;
    const attach = recap?between(t,52.38,53.59):compare?1-between(t,46.63,48.10):between(t,17.12,marks.microContact);
    const shear=(compare?.82:between(t,marks.shear,marks.shear+1.08)) * (compare?1-between(t,46.15,48.35):1);
    const z=compare ? -.0109*attach+.333*(1-attach) : .13*(1-attach)-.0109*attach, shift=.36*shear;
    // A shear illustration anchors the terminal end and flexes the higher shaft.
    padRoot.matrix.set(1,0,-shift/1.58,0, 0,1,0,0, 0,0,1-.065*attach,z, 0,0,0,1);
    sparseRoot.matrix.copy(padRoot.matrix);padRoot.matrixWorldNeedsUpdate=sparseRoot.matrixWorldNeedsUpdate=true;
    const active = recap ? attach>.965 : compare ? attach>.969 && t>45.12 : t>=marks.microContact;
    // Highlight one near-contact region; not a depiction of photons or a measured force map.
    gleam.visible=active && sparseView;
    gleam.material.opacity=refined ? .065+.08*between(t,24.14,25.42) : .09+.09*between(t,24.14,25.42);
    return {attach};
  };
}
