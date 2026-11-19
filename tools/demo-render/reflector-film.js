import * as THREE from 'three';
import { REFLECTOR_BEATS as B } from '../../src/reflector.js';
import { smooth } from './motion.js';
import { background, bevel, box, camera, dust, frame, glowTexture, lightPool, mesh, pbr, ring, strokeMaterial, V } from './stage.js';
import { ambientShadow, bar, bicycle, headlight, lampGlow, pavement, reflectorModule, setBar, softBeam } from './reflector-models.js';
import { CORNER_EDGE, OPTIC_PATH, RAY_IN, add3, cornerToBench, fadeBetween, pathProgress, reflect, returnPower, scale3 } from './reflector-optics.js';

const stage = (p, q, aim, to, mm, lens = {}) => ({
  path: [V(...p), V(...q)], aim: [V(...aim), V(...to)], lens: { mm, exposure: 1, ...lens },
});
const contact = [0,1.575,.463];
const cameras = [
  stage([-.115,1.636,1.497],[.092,1.640,1.198],contact,[.001,1.561,.463],[49,52],{aperture:10,bloom:.65,roll:[.034,-.012]}),
  stage([.97,1.835,1.57],[1.20,1.740,1.35],[0,1.569,.36],[0,1.561,.30],[51,57],{aperture:10,roll:[-.012,.004]}),
  stage([2.38,1.48,3.79],[1.42,1.57,3.59],[0,1.15,-.50],[0,1.18,-.30],[38,40]),
  stage([-.47,1.39,3.72],[-.225,1.566,2.72], [0,1.463,.25],[0,1.511,.36],[46,52],{aperture:7,bloom:.72}),
  stage([-.225,1.566,2.72],[2.51,1.713,1.44],[0,1.511,.36],[0,1.468,.27],[52,43],{roll:[0,-.027]}),
  stage([1.00,7.44,7.12],[.82,7.21,6.96],[-.33,.77,4.08],[-.33,.80,4.09],[27,27],{roll:[-.37,-.42]}),
  stage([1.40,3.12,5.70],[.77,3.63,5.88],[-.14,1.29,1.05],[-.14,1.27,1.06],[33,34]),
  stage([.31,4.20,6.24],[-.16,4.33,6.14],[-.04,1.23,1.23],[-.02,1.22,1.26],[33,34]),
  stage([2.16,2.19,3.09],[1.67,2.16,2.59],[0,1.67,.102],[0,1.65,.099],[50,53],{aperture:7}),
  stage([-.279,1.809,1.386],[.257,1.748,1.313],[.052,1.657,.626],[.075,1.659,.627],[47,53],{aperture:13,bloom:.75}),
  stage([2.92,3.30,7.86],[2.63,3.17,7.46],[0,2.28,-.37],[0,2.37,-.32],[43,45]),
  stage([2.63,3.17,7.46],[2.24,3.26,7.22],[0,2.37,-.32],[-.03,2.30,.03],[45,44]),
  stage([2.24,3.26,7.22],[1.57,3.46,7.11],[-.03,2.30,.03],[0,2.35,-.15],[44,46]),
  stage([1.57,3.46,7.11],[3.58,4.12,8.02],[0,2.35,-.15],[.01,2.54,.79],[46,39]),
  stage([5.28,5.44,8.12],[6.05,5.09,7.98],[.12,2.49,1.13],[.11,2.53,1.18],[39,37],{roll:[-.04,-.09]}),
  stage([-.73,1.13,6.49],[-.53,1.32,5.47],[.009,1.47,.21],[.025,1.46,.14],[56,59],{aperture:7,bloom:.65}),
  stage([.79,7.30,6.98],[.73,7.10,6.81],[-.33,.79,4.07],[-.31,.78,4.17],[27,26],{roll:[-.40,-.43]}),
  stage([-.22,1.53,3.40],[-.12,1.575,2.64],[0,1.484,.37],[0,1.546,.39],[41,48],{aperture:7,bloom:.68,roll:[.015,0]}),
];

const plain = (color) => new THREE.MeshBasicMaterial({ color, toneMapped:false });
const powerAt = (t, cut) => {
  if (cut < 2) return fadeBetween(t,B.hookOn,B.hookOn+.33);
  if (cut < 15) return fadeBetween(t,B.lampOn,B.lampOn+.28);
  return 1 - fadeBetween(t,B.lampOff,B.lampOff+.16) + fadeBetween(t,B.payoffOn,B.payoffOn+.25);
};
const warm = '#ffe7c7';
const escape = '#ff765e';

function rayTrace(parent, points, colors, times, glow, radius = .017) {
  const tube = new THREE.CylinderGeometry(1, 1, 1, 10, 1);
  const groups = colors.map((color) => {
    const core = mesh(parent, tube, plain(color));
    const halo = mesh(parent,tube,new THREE.MeshBasicMaterial({
      color, transparent:true, depthWrite:false, opacity:.13, toneMapped:false, blending:THREE.AdditiveBlending,
    }));
    return [core, halo];
  });
  const spark = lampGlow(parent,glow,'#ffe2b3',radius*13,[0,0,0]);
  const arrow = (index, color) => {
    const vec = points[index+1].clone().sub(points[index]);
    const head = mesh(parent,new THREE.ConeGeometry(radius*3.4,radius*9,14),plain(color));
    head.position.copy(points[index]).addScaledVector(vec,.58);
    head.quaternion.setFromUnitVectors(V(0,1,0),vec.normalize()); head.visible=false;
    return head;
  };
  const ab = points[0].clone();
  return {
    arrow,
    update(t) {
      const progress = pathProgress(t,times);
      for (let i=0;i<groups.length;i++) {
        const [core, halo]=groups[i], p=progress[i];
        core.visible=halo.visible=p>0;
        if (p<=0) continue;
        ab.copy(points[i]).lerp(points[i+1],p);
        setBar(core,points[i],ab,radius);
        setBar(halo,points[i],ab,radius*2.2);
        spark.position.copy(ab);
      }
      spark.material.opacity = t < times[0] || t > times.at(-1) ? 0 : .87;
    },
  };
}

function standardMirror(parent, glow) {
  const trim=pbr('#607b86',.26,.78,{roughnessMap:strokeMaterial()});
  const glass=new THREE.MeshPhysicalMaterial({ color:'#a1c0ce', emissive:'#31516d', emissiveIntensity:.36, metalness:.93, roughness:.115, clearcoat:.93,clearcoatRoughness:.12 });
  const mount=pbr('#263642',.45,.54);
  bevel(parent,[1.59,.97,.10],.058,trim,[0,1.31,-.027]);
  bevel(parent,[1.47,.858,.027],.012,glass,[0,1.313,.038]);
  bevel(parent,[1.98,.145,1.02],.030,mount,[0,.685,.041]);
  for(const side of [-1,1]) bevel(parent,[.149,.216,.21],.019,mount,[side*.59,.826,-.16]);
  ambientShadow(parent,glow,2.6,[0,.592,.10],.8,1.34);
  const source=V(-1.04,1.66,2.44), hit=V(-.082,1.31,.052);
  const lamp=headlight(parent,glow,source,hit); lamp.fixture.scale.setScalar(.40);
  const incoming=hit.clone().sub(source).normalize();
  const out=V(...reflect(incoming.toArray(),[0,0,1]));
  const trace=rayTrace(parent,[source.clone().lerp(hit,.06),hit,hit.clone().addScaledVector(out,2.85)],[warm,'#a7eafb'],[B.mirrorIn,B.mirrorHit,B.mirrorOut],glow,.0138);
  const ping=lampGlow(parent,glow,'#ffe2bb',.49,[hit.x,hit.y,hit.z+.015]);
  const pointer=trace.arrow(1,'#bbf0ff');
  return (time) => {
    trace.update(time); lamp.power(fadeBetween(time,B.mirrorIn-.22,B.mirrorIn+.13));
    ping.material.opacity = time<B.mirrorHit ? 0 : .73*Math.exp(-7.4*(time-B.mirrorHit));
    pointer.visible=time>B.mirrorOut-.28;
  };
}

function visualPrism(parent,glow) {
  const center=V(0,2.47,0);
  const toWorld=(p)=>V(...cornerToBench(p)).add(center);
  const edge=CORNER_EDGE;
  const v=[toWorld([edge,0,0]),toWorld([0,edge,0]),toWorld([0,0,edge]),toWorld([0,0,0])];
  const sideColors=['#675968','#414c66','#905b64'];
  const border=pbr('#91acc1',.22,.64);
  const faces=[];
  for(let i=0;i<3;i++) {
    const a=(i+1)%3,b=(i+2)%3;
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute([...v[a].toArray(),...v[b].toArray(),...v[3].toArray()],3));
    g.computeVertexNormals();
    const m = new THREE.MeshPhysicalMaterial({
      color:sideColors[i], metalness:.32, roughness:.22, clearcoat:.77, clearcoatRoughness:.19,
      emissive:'#ffa178',emissiveIntensity:0,transparent:true,opacity:.58, depthWrite:false, side:THREE.DoubleSide,
    });
    faces.push(mesh(parent,g,m));
    bar(parent,v[a],v[b],.016,border);
    bar(parent,v[i],v[3],.016,border);
  }
  // Tiny square angle markers at the three back corners' common vertex.
  const brackets=new THREE.Group();parent.add(brackets);
  const mark=plain('#f7c2a0');
  const w=.23;
  for (const [a,b] of [[0,1],[1,2],[2,0]]) {
    const p=[0,0,0],m=[0,0,0],n=[0,0,0];p[a]=w;m[a]=m[b]=w;n[b]=w;
    bar(brackets,toWorld(p),toWorld(m),.012,mark);bar(brackets,toWorld(m),toWorld(n),.012,mark);
  }
  const base=pbr('#415061',.36,.68);
  bevel(parent,[3.27,.18,2.42],.058,base,[0,.135,-.401]);
  bevel(parent,[.35,.40,.48],.065,base,[0,.407,-.56]);
  bar(parent,V(0,.44,-.57),v[2].clone(),.053,base);
  ambientShadow(parent,glow,3.8,[0,.014,-.50],.77,1.33);
  const entry=OPTIC_PATH[0],exit=OPTIC_PATH.at(-1);
  const from=toWorld(add3(entry.point,scale3(RAY_IN,-3.20)));
  const returned=toWorld(add3(exit.point,scale3(exit.direction,3.20)));
  const path=[from,...OPTIC_PATH.map((e)=>toWorld(e.point)),returned];
  const trace=rayTrace(parent,path,[warm,'#ffac7e','#ffab7a','#ff9c72','#ff9477',escape],
    [B.rayStart,B.rayEnter,...B.hits,B.rayExit,B.returned],glow,.018);
  const pulses=OPTIC_PATH.slice(1,4).map((e)=>lampGlow(parent,glow,'#ffc199',.64,toWorld(e.point).toArray()));
  const inArrow=trace.arrow(0,warm), outArrow=trace.arrow(5,'#ff8877');
  const srcRing=ring(parent,.15,.011,border,from.toArray());
  srcRing.quaternion.setFromUnitVectors(V(0,0,1),from.clone().sub(path[1]).normalize());
  return (time,index) => {
    trace.update(time);
    brackets.visible=index===10;
    inArrow.visible=outArrow.visible=index===14;
    srcRing.visible=index>=11;
    for (let i=0;i<3;i++) {
      const age=time-B.hits[i];
      const pulse=age>=0?.88*Math.exp(-7.6*age):0;
      pulses[i].material.opacity=pulse;
      faces[OPTIC_PATH[i+1].face].material.emissiveIntensity=pulse*.67;
    }
  };
}

export async function reflectorFilm(environment) {
  const scene=new THREE.Scene();
  scene.environment=environment;
  scene.environmentIntensity=.59;
  const streetBg=background(['#080f1b','#213747','#3c526064']);
  const labBg=background(['#101522','#2b3c50','#4a5e715f']);
  scene.background=streetBg;
  const rim=new THREE.DirectionalLight('#a0d6ff',2.26); rim.position.set(-3.3,4.2,-1.7); scene.add(rim);
  const key=new THREE.DirectionalLight('#ffdfc3',2.07); key.position.set(4.6,5.3,4.5); scene.add(key);
  const hemi=new THREE.HemisphereLight('#b6d3ee','#2c263b',.72);scene.add(hemi);
  const nightFog=new THREE.FogExp2('#101a2b',.045);
  const labFog=new THREE.FogExp2('#202c3d',.032);
  const glow=glowTexture();
  const street=new THREE.Group();scene.add(street);
  pavement(street); bicycle(street,glow);
  const face=V(0,1.575,.463);
  const real=reflectorModule(street,glow,V(0,1.575,.363));
  const source=V(-.94,1.02,6.81);
  const lamp=headlight(street,glow,source,face);
  const beam=softBeam(street,source.clone().lerp(face,.027),face);
  const splash=lightPool(street,'#e5d5c4',.18,5.5,-.33,1.04,.014);
  splash.scale.set(.69,1.3,1);
  const actual=new THREE.SpotLight('#ffedce',22,13,.19,.7,1.25);
  actual.position.copy(source);actual.target.position.copy(face);street.add(actual,actual.target);
  const motes=dust(street,712,52,[[-1.65,.84],[.4,2.1],[.41,6.45]],'#c5d6e2',.024);
  const comparison=new THREE.Group();scene.add(comparison);
  const mount=new THREE.Group();scene.add(mount);
  const optic=new THREE.Group();scene.add(optic);
  const bench=new THREE.Group();scene.add(bench);
  const rubberDeck=pbr('#364658',.55,.48), aluminum=pbr('#57687a',.37,.65);
  const fullFloor=mesh(bench,new THREE.PlaneGeometry(76,76),pbr('#283647',.67,.19),0,-.009,2);
  fullFloor.rotation.x=-Math.PI/2;
  for(let i=-5;i<=5;i++) box(bench,[.009,.007,13.8],pbr('#455568',.68,.24),[i*.67,.001,1.8]);
  bevel(comparison,[3.75,.23,4.93],.065,rubberDeck,[0,.46,1.46]);
  bevel(mount,[2.68,.20,1.66],.052,rubberDeck,[0,.70,-.12]);
  bevel(mount,[.13,1.0,.18],.039,aluminum,[0,1.14,-.24]);
  ambientShadow(mount,glow,1.62,[0,.802,-.038],.68,1.39);
  const mock=reflectorModule(mount,glow,V(0,1.65,0));
  const updateMirror=standardMirror(comparison,glow);
  const updatePrism=visualPrism(optic,glow);
  const cam=camera(); cam.near=.031; cam.updateProjectionMatrix();
  // Orthographic proof view: depth perspective must not make the two parallel
  // external directions seem to converge. This is a deliberate edit at 35s.
  const plan=new THREE.OrthographicCamera(-2.37,2.37,2.37*16/9,-2.37*16/9,.031,90);
  plan.userData.lens={exposure:1};
  let activeCam=cam;
  const view=V(0,0,0), lightDir=source.clone().sub(face).normalize().toArray();

  function update(t, cut) {
    const i=cut.index;
    const road=i<6||i>14;
    street.visible=road; bench.visible=!road;
    comparison.visible=i===6||i===7;
    mount.visible=i===8||i===9;
    optic.visible=i>=10&&i<=14;
    scene.background=road?streetBg:labBg;
    scene.fog=road?nightFog:labFog;
    scene.environmentIntensity=road?.43:.65;
    key.intensity=road?1.98:2.60;
    hemi.intensity=road?.58:.71;
    rim.intensity=road?2.35:2.08;
    const track=cameras[i];
    // Adjacent microscope views share endpoint/aim and maintain the optical ray's picture position.
    activeCam=i===14?plan:cam;
    if (i===14) {
      const u=smooth(cut.progress);
      plan.position.copy(track.path[0]).lerp(track.path[1],u);
      plan.lookAt(track.aim[0].clone().lerp(track.aim[1],u));
      plan.rotateZ(-.04-.05*u);
    } else frame(cam,cut.progress,track.path,track.aim,null,track.lens);
    if (road) {
      const p=powerAt(t,i);
      view.copy(cam.position).sub(face).normalize();
      const bright=returnPower(view.toArray(),lightDir,p);
      real.brightness(bright,t);lamp.power(p);beam.value=p;
      actual.intensity=p*26;splash.material.opacity=p*.285;
      motes.material.opacity=.21*p;motes.position.x=.043*Math.sin(t*.72);motes.position.y=.036*Math.cos(t*.63);
    } else if (mount.visible) {
      const apart=fadeBetween(t,19.63,21.61);
      mock.body.position.z=-.325*apart;
      mock.seal.position.z=-.057*apart;
      mock.lens.position.z=.519*apart;
      mock.group.rotation.y=i===8 ? -.09*smooth(cut.progress) : -.09;
      mock.brightness(.055,t);
    } else if (comparison.visible) updateMirror(t);
    else if (optic.visible) updatePrism(t,i);
  }
  return {scene,get cam(){return activeCam;},update};
}
