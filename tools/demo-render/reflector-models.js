import * as THREE from 'three';
import { bevel, box, mesh, pbr, ring, rng, texture, V } from './stage.js';
import { cornerToBench } from './reflector-optics.js';

const Y = V(0, 1, 0);
const temp = V(0, 0, 0);
const tmat = new THREE.Object3D();

export function setBar(object, a, b, radius = 1) {
  temp.copy(b).sub(a);
  object.position.copy(a).addScaledVector(temp, .5);
  object.scale.set(radius, temp.length(), radius);
  object.quaternion.setFromUnitVectors(Y, temp.normalize());
}

const rod = new THREE.CylinderGeometry(1, 1, 1, 12, 1);
const pin = new THREE.CylinderGeometry(1, 1, 1, 7, 1);
const mat = (color) => new THREE.MeshBasicMaterial({ color, toneMapped: false });
export function bar(parent, a, b, r, material, geometry = rod) {
  const item = mesh(parent, geometry, material);
  setBar(item, a, b, r);
  return item;
}

const rodBatch = (parent, list, material, geometry = pin) => {
  const result = new THREE.InstancedMesh(geometry, material, list.length);
  list.forEach(([a, b, r], i) => {
    setBar(tmat, a, b, r); tmat.updateMatrix(); result.setMatrixAt(i, tmat.matrix);
  });
  parent.add(result);
  return result;
};

export function ambientShadow(parent, glow, size, xyz, opacity = .7, stretch = 1) {
  const material = new THREE.MeshBasicMaterial({ color: '#000106', map: glow, opacity, transparent: true, depthWrite: false });
  const contact = mesh(parent, new THREE.PlaneGeometry(size * stretch, size), material, ...xyz);
  contact.rotation.x = -Math.PI / 2;
  return contact;
}

export function lampGlow(parent, glow, color, size, xyz) {
  const material = new THREE.SpriteMaterial({ map: glow, color, transparent: true, blending: THREE.AdditiveBlending, opacity: .24, depthWrite: false, toneMapped: false });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(size, size, 1); sprite.position.set(...xyz); parent.add(sprite);
  return sprite;
}

// Tire, rim bead, alternating hub flanges, crossed spokes and spoke nipples.
// All spokes for both wheels use a single instanced draw call.
export function bicycle(parent, glow) {
  const bike = new THREE.Group(); parent.add(bike);
  const rubber = pbr('#171d27', .78, .02);
  const tread = pbr('#171a22', .61, .02);
  const rim = pbr('#192d37', .31, .65);
  const bright = pbr('#829199', .22, .83);
  const frame = new THREE.MeshPhysicalMaterial({ color: '#183c42', roughness: .28, metalness: .48, clearcoat: .65, clearcoatRoughness: .22 });
  const graphite = pbr('#1b2732', .45, .36);
  const wheelR = .654, hubY = .725;
  const spokes = [], nipples = [], tubeStruts = [], treadBars = [];
  const rear = V(0, hubY, 0), front = V(0, hubY, -2.17);
  for (const hub of [rear, front]) {
    const tire = ring(bike, wheelR, .068, rubber, hub.toArray()); tire.rotation.y = Math.PI / 2;
    const tireBead = ring(bike, wheelR - .050, .021, rim, hub.toArray()); tireBead.rotation.y = Math.PI / 2;
    for (const side of [-1, 1]) {
      const machined = ring(bike, wheelR - .060, .0085, bright, [side * .038, hub.y, hub.z]);
      machined.rotation.y = Math.PI / 2;
    }
    bar(bike, V(-.11, hub.y, hub.z), V(.11, hub.y, hub.z), .063, bright);
    bar(bike, V(-.136, hub.y, hub.z), V(.136, hub.y, hub.z), .024, graphite);
    for (let i = 0; i < 28; i++) {
      const a = i * Math.PI / 14, k = i % 2 ? 1 : -1;
      const atRadius = (r, angle, x) => V(x, hub.y + r * Math.cos(angle), hub.z + r * Math.sin(angle));
      const flange = atRadius(.052, a + (i % 4 < 2 ? .91 : -.91), k * .076);
      const inner = atRadius(wheelR - .079, a, k * .009);
      const outer = atRadius(wheelR - .047, a, k * .018);
      spokes.push([flange, inner, .0047]); nipples.push([inner, outer, .008]);
    }
    for (let i = 0; i < 64; i++) {
      const a = Math.PI * i / 32, k = i % 2 ? 1 : -1;
      const slot = (angle, x) => V(x, hub.y + .718 * Math.cos(angle), hub.z + .718 * Math.sin(angle));
      treadBars.push([slot(a - .014, k * .024), slot(a + .023, -k * .023), .006]);
    }
    ambientShadow(parent, glow, 1.04, [0, .005, hub.z], .80, .48);
  }
  rodBatch(bike, spokes, bright); rodBatch(bike, nipples, graphite); rodBatch(bike, treadBars, tread);
  const bb = V(0,.74,-.90), seat = V(0,1.67,-.58), head = V(0,1.65,-1.96), lowHead = V(0,1.37,-2.03);
  tubeStruts.push([bb, seat, .063], [seat, head, .061], [bb, lowHead, .086], [head, lowHead, .081]);
  for (const side of [-1, 1]) {
    tubeStruts.push([V(side*.11,rear.y,rear.z), V(side*.053,seat.y,seat.z), .026]);
    tubeStruts.push([V(side*.11,rear.y,rear.z), V(side*.073,bb.y,bb.z), .030]);
    tubeStruts.push([V(side*.096,front.y,front.z), V(side*.062,1.38,-2.01), .036]);
  }
  rodBatch(bike,tubeStruts,frame,rod);
  bar(bike, seat, V(0,1.91,-.55), .031, bright);
  bevel(bike,[.275,.079,.43],.034,graphite,[0,1.94,-.60]);
  bevel(bike,[.21,.036,.34],.016,rubber,[0,1.972,-.59]);
  bar(bike,head,V(0,1.81,-1.98),.030,bright);
  bar(bike,V(-.39,1.85,-1.99),V(.39,1.85,-1.99),.024,graphite);
  for (const side of [-1,1]) bar(bike,V(side*.25,1.85,-1.99),V(side*.42,1.85,-1.99),.032,rubber);
  const sprocket = ring(bike,.178,.019,bright,[.109,.74,-.90]); sprocket.rotation.y = Math.PI / 2;
  const rearGear = ring(bike,.075,.012,bright,[.109,rear.y,rear.z]); rearGear.rotation.y = Math.PI / 2;
  bar(bike,V(.114,.875,-.90),V(.114,.779,.0),.012,graphite);
  bar(bike,V(.112,.571,-.90),V(.112,.657,.0),.012,graphite);
  bar(bike,V(-.137,.74,-.90),V(.148,.74,-.90),.034,bright);
  bar(bike,V(.14,.74,-.90),V(.14,.57,-.78),.025,bright);
  bevel(bike,[.20,.037,.105],.012,graphite,[.21,.55,-.78]);
  bar(bike,V(-.14,.74,-.90),V(-.14,.89,-1.04),.025,bright);
  bevel(bike,[.20,.037,.105],.012,graphite,[-.21,.89,-1.04]);
  // Discrete rear mount, above the tire, not a dangling wire.
  bar(bike,V(0,1.77,-.52),V(0,1.57,.22),.031,graphite);
  bevel(bike,[.145,.19,.18],.023,graphite,[0,1.51,.29]);
  return bike;
}

function prismTileGeometry() {
  const side = 1 / Math.SQRT2;
  const verts = [[side,0,0],[0,side,0],[0,0,side],[0,0,0]].map((p) => cornerToBench(p,false,side));
  const geometry = new THREE.BufferGeometry();
  const positions = [];
  const colors = [];
  const facets = [[0,3,1],[1,3,2],[2,3,0]];
  for (let f = 0; f < 3; f++) for (const j of facets[f]) {
    const p = verts[j]; positions.push(p[0],p[1],p[2] * -.67);
    const value = [.67,.91,1][f]; colors.push(value,value,value);
  }
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors,3));
  geometry.computeVertexNormals();
  return geometry;
}

export const MODULE_W = .611, MODULE_H = .289;
export const LENS_FRONT = .083;
export function reflectorModule(parent, glow, position) {
  const group = new THREE.Group(); group.position.copy(position); parent.add(group);
  const black = pbr('#20242c',.44,.26);
  const gasketMaterial = pbr('#222128',.79,.03);
  const fastener = pbr('#9aa6b3',.33,.79);
  const ruby = new THREE.MeshPhysicalMaterial({ color:'#8f0c1d', roughness:.20, metalness:.32, clearcoat:.76, clearcoatRoughness:.16 });
  const body = new THREE.Group(); const seal = new THREE.Group(); const lens = new THREE.Group();
  group.add(body,seal,lens);
  bevel(body,[MODULE_W+.036,MODULE_H+.040,.113],.025,black,[0,0,-.035]);
  for (const s of [-1,1]) {
    const screw = mesh(body, new THREE.CylinderGeometry(.017,.017,.011,16), fastener, s*.243,0,-.095);
    screw.rotation.x = Math.PI / 2;
    box(body,[.021,.0038,.005],black,[s*.243,0,-.101]);
  }
  bevel(seal,[MODULE_W+.008,MODULE_H+.022,.026],.012,gasketMaterial,[0,0,.027]);
  bevel(lens,[MODULE_W,MODULE_H,.036],.017,ruby,[0,0,.058]);
  const microMaterial = pbr('#dc2432',.245,.32,{ vertexColors:true, side:THREE.DoubleSide, emissive:'#f92319', emissiveIntensity:.035 });
  const tiles = [];
  for (let y = -3; y <= 3; y++) for (let x = -6; x <= 6; x++) {
    for (let row = 0; row < 2; row++) {
      const pitch = .0449, dx = (x + (row ? .50 : 0) + (y % 2 ? .50 : 0)) * pitch;
      const dy = y * pitch * .866 + (row ? -.0125 : .0005);
      if (Math.abs(dx) > .269 || Math.abs(dy) > .113) continue;
      tiles.push([dx,dy,row]);
    }
  }
  const prismTiles = new THREE.InstancedMesh(prismTileGeometry(), microMaterial, tiles.length);
  const random = rng(2203);
  tiles.forEach(([x,y,isUp],i) => {
    tmat.position.set(x,y,LENS_FRONT); tmat.rotation.set(0,0,isUp?Math.PI:0); tmat.scale.setScalar(.043);
    tmat.updateMatrix(); prismTiles.setMatrixAt(i,tmat.matrix);
    const gain = .73 + .26*random(); prismTiles.setColorAt(i,new THREE.Color(gain,gain,gain));
  });
  lens.add(prismTiles);
  // The molded mark is on the lens, and prism facets show through its skin.
  const clearSkin = new THREE.MeshPhysicalMaterial({
    color:'#a21624', roughness:.19, metalness:.03, clearcoat:1, clearcoatRoughness:.19,
    opacity:.205, transparent:true, depthWrite:false,
  });
  bevel(lens,[MODULE_W-.01,MODULE_H-.011,.012],.006,clearSkin,[0,0,.098]);
  const mold = texture(256,64,(ctx,w,h) => {
    ctx.clearRect(0,0,w,h);
    ctx.font='650 29px sans-serif'; ctx.textAlign='center'; ctx.fillStyle='#f0726d89';
    ctx.fillText('PRISM   02',w/2,40);
  });
  mesh(lens,new THREE.PlaneGeometry(.102,.0255),new THREE.MeshBasicMaterial({ map:mold, transparent:true, depthWrite:false }),.229,-.126,.087);
  const halo = lampGlow(lens,glow,'#ff352b',.82,[0,.02,.119]);
  const flare = lampGlow(lens,glow,'#ff9b75',.19,[-.175,.044,.116]);
  halo.material.opacity = flare.material.opacity = 0;
  return {
    group, body, seal, lens,
    brightness(power, t) {
      microMaterial.emissiveIntensity = .018 + 1.58*power;
      ruby.emissive.set('#ff151c'); ruby.emissiveIntensity = power*.34;
      halo.material.opacity = .23*power;
      flare.material.opacity = .51*power*(.7+.3*Math.sin(t*8.6+.52));
      flare.position.x = -.17 + .12*Math.sin(t*1.5);
    },
  };
}

export function pavement(parent) {
  const groundMap = texture(512,512,(ctx,w,h) => {
    const rand=rng(8239); ctx.fillStyle='#252d34'; ctx.fillRect(0,0,w,h);
    for (let i=0;i<22000;i++) {
      const v=rand()<.5?'10,17,24':'155,165,173';
      ctx.fillStyle=`rgba(${v},${.05+rand()*.34})`;
      ctx.fillRect(rand()*w,rand()*h,.6+rand()*3.2,.45+rand()*2.1);
    }
    for(let i=0;i<26;i++) {
      ctx.strokeStyle=`rgba(7,11,17,${.06+rand()*.2})`;
      ctx.lineWidth=.8+rand()*1.1;
      const x=rand()*w,y=rand()*h;
      ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+rand()*70,y+rand()*12);ctx.stroke();
    }
  });
  groundMap.wrapS=groundMap.wrapT=THREE.RepeatWrapping; groundMap.repeat.set(10,14); groundMap.anisotropy=4;
  const asphalt = pbr('#6e7381',.72,.14,{map:groundMap});
  const floor=mesh(parent,new THREE.PlaneGeometry(22,30),asphalt,0,0,3);
  floor.rotation.x=-Math.PI/2;
  const concrete=pbr('#1d2a39',.77,.08), steel=pbr('#2b3442',.39,.56), mortar=pbr('#253849',.82,.09);
  box(parent,[.32,5.8,19],concrete,[-3.17,2.89,3.7]);
  box(parent,[10,5.8,.28],concrete,[1.8,2.89,-5.50]);
  box(parent,[.61,.19,19],mortar,[-3.0,.10,3.73]);
  for (const z of [-4.5,-1.25,2,5.25,8.5,11.75]) {
    box(parent,[.36,5.8,.13],steel,[-2.95,2.88,z]);
    box(parent,[.083,.046,1.04],pbr('#b8a68b',.74,.05),[2.0,.008,z+.54]);
  }
  box(parent,[.023,.019,18],pbr('#9a846a',.56,.12),[-2.66,.008,4.2]);
  const warm=mat('#ffdec2'), cool=mat('#a0d6e7');
  for (const z of [-3.3,1.3,5.9,10.5]) {
    box(parent,[.11,.071,.8],cool,[-2.84,3.13,z]);
    box(parent,[.018,.29,.070],warm,[-2.79,.66,z+1.05]);
  }
}

export function headlight(parent, glow, from, aim) {
  const fixture = new THREE.Group(); parent.add(fixture); fixture.position.copy(from); fixture.lookAt(aim);
  const metal=pbr('#435363',.29,.67), dark=pbr('#252b33',.5,.44);
  const emitter=pbr('#56606d',.23,.21,{emissive:'#fff2cf',emissiveIntensity:0});
  bevel(fixture,[.94,.38,.31],.068,metal,[0,0,-.144]);
  bevel(fixture,[.79,.30,.095],.043,dark,[0,0,.021]);
  for (let j=-2;j<=2;j++) box(fixture,[.68,.016,.11],dark,[0,j*.06,-.34]);
  for (const x of [-.244,.00,.244]) {
    const recess = mesh(fixture,new THREE.CylinderGeometry(.111,.111,.053,24),metal,x,0,.062);
    recess.rotation.x=Math.PI/2;
    const source=mesh(fixture,new THREE.CylinderGeometry(.09,.09,.034,24),emitter,x,0,.088);
    source.rotation.x=Math.PI/2;
    ring(fixture,.104,.008,metal,[x,0,.093]);
  }
  const lensGlow=lampGlow(fixture,glow,'#ffe2b8',1.05,[0,0,.18]);
  const feet=pbr('#29343b',.43,.67);
  bar(parent,from.clone().add(V(0,-.13,0)),V(from.x,.19,from.z+.1),.053,feet);
  bevel(parent,[.70,.16,.58],.030,feet,[from.x,.09,from.z+.1]);
  ambientShadow(parent,glow,1.2,[from.x,.009,from.z+.10],.83,.82);
  return {
    fixture, power(p) { emitter.emissiveIntensity = p*2.5; lensGlow.material.opacity = p*.37; },
  };
}

export function softBeam(parent, from, to) {
  const direction=to.clone().sub(from), distance=direction.length();
  const material=new THREE.ShaderMaterial({
    uniforms:{ power:{value:0} }, transparent:true, depthWrite:false, side:THREE.DoubleSide,
    blending:THREE.AdditiveBlending,
    vertexShader:`varying vec2 st; varying vec3 vn, eye; void main(){ st=uv; vec4 view=modelViewMatrix*vec4(position,1.); vn=normalize(normalMatrix*normal); eye=-view.xyz; gl_Position=projectionMatrix*view; }`,
    fragmentShader:`varying vec2 st; varying vec3 vn, eye; uniform float power;
      void main(){ float contour=pow(clamp(abs(dot(normalize(vn),normalize(eye))),0.,1.),1.9);
      float longitudinal=smoothstep(0.,.20,st.y)*smoothstep(0.,.16,1.-st.y);
      gl_FragColor=vec4(.72,.78,.83,.073*contour*longitudinal*power); }`,
  });
  const cone=mesh(parent,new THREE.CylinderGeometry(.69,.081,distance,40,1,true),material);
  cone.position.copy(from).lerp(to,.5); cone.quaternion.setFromUnitVectors(Y,direction.normalize());
  return material.uniforms.power;
}
