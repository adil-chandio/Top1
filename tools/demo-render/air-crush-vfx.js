import * as THREE from 'three';
import { BATH_Y, pressureRatio, splashHeight } from './air-crush-motion.js';
import { clamp, smooth } from './motion.js';
import { mesh, pbr, rng, TAU } from './stage.js';

// The surface uses the same analytic wave in mesh displacement and normals.
// Broad softbox reflections sit on top of a dark transmission colour.
export function waterPlate(parent) {
  const uniforms = { age: { value: -2 }, time: { value: 0 }, strength: { value: 1 } };
  const waves = `
    void wave(vec2 p, out float z, out vec2 slope) {
      float r=max(length(p),.001);
      float a=time*2.1+dot(p,vec2(4.4,5.1));
      float b=time*1.23+dot(p,vec2(-6.7,3.25));
      z=.0047*sin(a)+.0031*sin(b);
      slope=.0047*cos(a)*vec2(4.4,5.1)+.0031*cos(b)*vec2(-6.7,3.25);
      if(age<0. || age>2.3) return;
      float ripple=r-(.745+1.57*age);
      float env=exp(-6.3*ripple*ripple-1.85*age)*(.057*strength);
      float k=19.0*ripple;
      z+=env*sin(k);
      slope+=(env*(19.0*cos(k)-12.6*ripple*sin(k)))*p/r;
      float edge=1.-smoothstep(2.18,2.59,r);
      z*=edge; slope*=edge;
    }
  `;
  const material = new THREE.ShaderMaterial({
    uniforms, transparent: true, depthWrite: false,
    vertexShader: `
      uniform float age,time,strength;
      varying vec3 world; varying vec2 xy;
      ${waves}
      void main(){
        xy=position.xy; float z; vec2 slope;
        wave(xy,z,slope);
        vec4 p=modelMatrix*vec4(xy,z,1.);
        world=p.xyz; gl_Position=projectionMatrix*viewMatrix*p;
      }`,
    fragmentShader: `
      uniform float age,time,strength;
      varying vec3 world; varying vec2 xy;
      ${waves}
      void main(){
        float r=length(xy); if(r>2.65) discard;
        float z; vec2 slope; wave(xy,z,slope);
        vec3 n=normalize(vec3(-slope.x,1.,slope.y));
        vec3 eye=normalize(cameraPosition-world), refl=reflect(-eye,n);
        float m=1.-clamp(dot(n,eye),0.,1.);
        float f=.026+.974*m*m*m*m*m;
        float a=max(0.,dot(refl,normalize(vec3(-.36,1.,.58))));
        float b=max(0.,dot(refl,normalize(vec3(.74,.40,-.33))));
        float strip=(1.-smoothstep(.05,.22,abs(refl.x+.27)))*smoothstep(.13,.66,refl.y);
        vec3 blue=vec3(.011,.038,.052)*(1.+.67*(1.-smoothstep(.3,2.61,r)));
        vec3 card=vec3(.25,.51,.62)*a*a*a*a*a*a*a*a*.19;
        float bb=b*b; bb*=bb; bb*=bb; bb*=bb;
        vec3 back=vec3(.41,.77,1.0)*bb*.14;
        float brass=(1.-smoothstep(.025,.3,abs(world.x+refl.x*.68))) * smoothstep(.01,.72,refl.y) * (1.-smoothstep(.35,1.4,abs(world.z-.74)));
        vec3 pigment=vec3(.32,.104,.037)*brass*.36;
        vec3 tint=blue+(f+.26)*(card+back+pigment+vec3(.17,.32,.42)*strip*.32);
        gl_FragColor=vec4(tint,clamp(.49+f*.45+strip*.11,0.,.93));
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  const sheet = mesh(parent, new THREE.PlaneGeometry(5.34, 5.34, 68, 68), material, 0, BATH_Y, 0);
  sheet.rotation.x = -Math.PI / 2;
  sheet.renderOrder = 3;
  return uniforms;
}

const proxy = new THREE.Object3D();
export function putInstance(objects, i, x, y, z, scale, sy = scale, sz = scale) {
  proxy.position.set(x, y, z);
  proxy.scale.set(scale, sy, sz);
  proxy.updateMatrix();
  objects.setMatrixAt(i, proxy.matrix);
}

export function splashes(parent) {
  const wet = pbr('#92b5c6', .17, .25, { emissive: '#102232', emissiveIntensity: .37 });
  const count = 89;
  const drops = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), wet, count);
  drops.frustumCulled = false;
  parent.add(drops);
  const random = rng(91);
  const queue = Array.from({ length: count }, (_, i) => [TAU * i / count + random() * .36, random(), random(), random(), random()]);
  // This translucent sheet stretches into a crown before the individual
  // ballistic drops separate. The rim and every drop share the entry clock.
  const n = 70;
  const p = new THREE.BufferAttribute(new Float32Array((n + 1) * 2 * 3), 3).setUsage(THREE.DynamicDrawUsage);
  const indices = [];
  for (let i = 0; i < n; i++) indices.push(i * 2, i * 2 + 2, i * 2 + 1, i * 2 + 1, i * 2 + 2, i * 2 + 3);
  const shell = new THREE.BufferGeometry(); shell.setAttribute('position', p); shell.setIndex(indices);
  const lace = pbr('#91b4bd', .19, .18, { side: THREE.DoubleSide, transparent: true, opacity: 0, depthWrite: false });
  const crown = mesh(parent, shell, lace);
  crown.frustumCulled = false;
  crown.renderOrder = 4;

  return (age, energy) => {
    drops.visible = age >= 0 && age < 1.22;
    crown.visible = age >= 0 && age < .385;
    if (crown.visible) {
      for (let i = 0; i <= n; i++) {
        const a = i / n * TAU;
        const drag = .81 + .18 * Math.sin(3 * a + .9);
        const rag = .76 + .17 * Math.sin(7 * a + age * 8.1) + .07 * Math.sin(13 * a + 2.1);
        const top = BATH_Y + splashHeight(age, 2.12 * energy * drag, 10.5) * rag;
        const base = .73 + .88 * age;
        const edge = .74 + age * (1.72 + .68 * rag) * energy;
        p.setXYZ(i * 2, Math.sin(a) * base, BATH_Y -.015, Math.cos(a) * base);
        p.setXYZ(i * 2 + 1, Math.sin(a) * edge, top, Math.cos(a) * edge);
      }
      p.needsUpdate = true;
      shell.computeVertexNormals();
      lace.opacity = .56 * smooth(age / .033) * (1 - smooth((age - .15) / .22));
    }
    if (!drops.visible) return;
    for (let i = 0; i < count; i++) {
      const [a, r, h, s, release] = queue[i];
      const f = age - .022 - release * .147;
      const v = (1.17 + h * 3.53) * energy;
      const height = splashHeight(f, v, 10.5);
      const speed = (.67 + r * 2.07) * energy;
      const dist = .77 + r * .15 + f * speed - .13 * f * f;
      const radius = height < .005 ? 0 : (.009 + s ** 2.5 * .028) * (1 - clamp(f) * .43);
      const stretch = 1 + Math.min(.91, Math.abs(v - 10.5 * f) * .16);
      putInstance(drops, i, Math.sin(a) * dist, BATH_Y + height, Math.cos(a) * dist, radius, radius * stretch);
    }
    drops.instanceMatrix.needsUpdate = true;
  };
}

// Deliberately schematic: constant outside vectors plus a shortening inside
// push. Thin on purpose so the stage stays legible; not moving air jets.
export function pressureMarks(parent) {
  const container = new THREE.Group(); parent.add(container);
  const shader = (color) => new THREE.MeshBasicMaterial({ color, opacity: 0, transparent: true, depthWrite: false });
  const cool = shader('#a0d7de'), warm = shader('#f5bc82');
  function arrowGroup(mat) {
    const g = new THREE.Group();
    const len = .33, w = .012;
    const v = [0,0,0, -len,w,0, -len,-w,0, 0,0,0, -.11,.06,0, -.11,-.06,0];
    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
    mat.side = THREE.DoubleSide;
    mesh(g, geom, mat);
    container.add(g);
    return g;
  }
  const ext = [], inside = [];
  for (const s of [-1, 1]) {
    for (let i = 0; i < 3; i++) {
      const g = arrowGroup(cool);
      g.rotation.z = s < 0 ? 0 : Math.PI;
      g.position.set(s * (.992 + .055 * (i === 1 ? -1 : 0)), 1.68 + i * .46, .70);
      ext.push(g);
    }
    const g = arrowGroup(warm);
    g.rotation.z = s < 0 ? Math.PI : 0;
    g.position.set(s * .51, 2.39, .14);
    inside.push({ g, s });
  }
  return (t, cut) => {
    const comparison = cut.index === 7;
    const active = comparison || cut.index === 8;
    container.visible = active;
    if (!active) return;
    const env = smooth((cut.age - .26) / .34) * smooth(cut.remaining / .42);
    cool.opacity = env * (comparison ? .48 : .69);
    warm.opacity = env * .57;
    for (const { g, s } of inside) {
      g.visible = comparison;
      const q = pressureRatio(t);
      g.scale.x = q;
      g.scale.y = .78 + q * .22;
      g.position.x = s * (.19 + q * .32);
    }
    for (const g of ext) g.visible = !comparison || Math.abs(g.position.y - 2.14) < .02;
  };
}
