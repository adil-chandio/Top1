import * as THREE from 'three';
import { AIR_TIMING } from '../../src/air-crush.js';
import { clamp, mix, smooth } from './motion.js';
import { BAND_DEPTH, BATH_Y, CAN_H, canRadius, deformCan, footPose, poseAt, vaporRemaining, waterEvent } from './air-crush-motion.js';
import { pressureMarks, putInstance, splashes, waterPlate } from './air-crush-vfx.js';
import { background, bevel, box, camera, cylinder, dust, frame, mesh, PI, pbr, ring, rng, strokeMaterial, TAU, texture, V } from './stage.js';

const HALF = CAN_H / 2;
const MOUTH = .32;
const WHITE = new THREE.Color('#d3eef2');
const WARM = new THREE.Color('#c19268');
const COOL = new THREE.Color('#80b6cb');

function wrapArt() {
  return texture(1536, 1024, (c, w, h) => {
    const ink = c.createLinearGradient(0, 0, 0, h);
    ink.addColorStop(0, '#7e311d'); ink.addColorStop(.14, '#b65a34');
    ink.addColorStop(.26, '#bb6138'); ink.addColorStop(.70, '#a44528');
    ink.addColorStop(.89, '#773523'); ink.addColorStop(1, '#532417');
    c.fillStyle = ink; c.fillRect(0, 0, w, h);
    c.fillStyle = '#e5a26b86'; c.fillRect(0, 142, w, 2); c.fillRect(0, 897, w, 2);
    c.fillStyle = '#421e17'; c.fillRect(0, 824, w, 52);
    c.fillStyle = '#d49972b3'; c.fillRect(0, 823, w, 1.4);
    const rand = rng(707);
    for (let i = 0; i < 7500; i++) {
      c.fillStyle = rand() > .49 ? '#fff3d318' : '#2d141013';
      c.fillRect(rand() * w, rand() * h, .7 + 7.5 * rand(), .38 + .91 * rand());
    }
    const face = w / 2;
    for (const [x, small] of [[face,false],[w*.16,true],[w*.84,true]]) {
      c.save(); c.translate(x, 0);
      c.textAlign = 'center'; c.fillStyle = '#f2dfb9';
      c.font = `800 ${small ? '70' : '122'}px sans-serif`;
      c.fillText('FIZZ', 0, 480);
      c.font = '600 23px monospace'; c.fillText('T O P 1   L A B', 0, 536);
      c.strokeStyle = '#edcbaa91'; c.lineWidth = 2;
      c.beginPath(); c.moveTo(-124, 557); c.lineTo(124, 557); c.stroke();
      c.font = '400 66px monospace'; c.fillText('01', 0, 693);
      c.font = '19px monospace'; c.fillText('PRESSURE STUDY', 0, 739);
      c.restore();
    }
  });
}

function skinGeo(from, to, reversed, inset) {
  const columns = 144, rows = 76, stride = columns + 1;
  const geometry = new THREE.BufferGeometry();
  const xyz = new Float32Array(stride * (rows + 1) * 3);
  const uv = new Float32Array(stride * (rows + 1) * 2);
  const index = [];
  const angles = Array.from({ length: stride }, (_, j) => mix(from, to, j / columns));
  for (let i = 0; i <= rows; i++) {
    for (let j = 0; j <= columns; j++) {
      const n = i * stride + j;
      uv[2 * n] = (angles[j] + PI) / TAU;
      uv[2 * n + 1] = i / rows;
      if (i !== rows && j !== columns) {
        if (!reversed) index.push(n, n + 1, n + stride, n + 1, n + stride + 1, n + stride);
        else index.push(n, n + stride, n + 1, n + 1, n + stride, n + stride + 1);
      }
    }
  }
  const coords = new THREE.BufferAttribute(xyz, 3).setUsage(THREE.DynamicDrawUsage);
  geometry.setAttribute('position', coords); geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  geometry.setIndex(index);
  const out = { x: 0, y: 0, z: 0 };
  function set(state) {
    for (let i = 0; i <= rows; i++) {
      for (let j = 0; j <= columns; j++) {
        deformCan(angles[j], i / rows, state, inset, out);
        coords.setXYZ(i * stride + j, out.x, out.y, out.z);
      }
    }
    coords.needsUpdate = true;
    geometry.computeVertexNormals();
    geometry.computeBoundingSphere();
  }
  set({ a: 0, b: 0, c: 0, shiver: 0 });
  return { geometry, set };
}

function rolledRim(parent, r, y, mat, section = TAU) {
  const torus = ring(parent, r, .026, mat, [0, y, 0], section);
  torus.rotation.x = -PI / 2;
  return torus;
}

function makeCan(root) {
  const wear = strokeMaterial();
  const label = wrapArt();
  label.wrapS = THREE.RepeatWrapping;
  label.anisotropy = 8;
  const enamel = pbr('#ffffff', .68, .61, { map: label, roughnessMap: wear, bumpMap: wear, bumpScale: .0046 });
  const silver = pbr('#a8b4bb', .60, .88, { roughnessMap: wear, bumpMap: wear, bumpScale: .005 });
  const cutMetal = pbr('#bbc5c9', .64, .80, { roughnessMap: wear, side: THREE.DoubleSide });
  const wallInterior = pbr('#697880', .63, .45, { roughnessMap: wear });
  const full = new THREE.Group(), slice = new THREE.Group();
  root.add(full, slice);
  const all = skinGeo(-PI, PI, false, 0);
  mesh(full, all.geometry, enamel);
  const sector = 1.11;
  const outer = skinGeo(sector, TAU - sector, false, 0);
  const inner = skinGeo(sector, TAU - sector, true, BAND_DEPTH);
  mesh(slice, outer.geometry, enamel);
  mesh(slice, inner.geometry, wallInterior);
  // Exposed cross-section with cut edges that read even at phone size.
  for (const theta of [sector, TAU - sector]) {
    const v = [], indices = [];
    for (let i = 0; i <= 56; i++) {
      for (const inset of [0, BAND_DEPTH]) {
        const a = deformCan(theta, i / 56, { a: 0, b: 0, c: 0, shiver: 0 }, inset);
        v.push(a.x, a.y, a.z);
      }
      const j = i * 2;
      if (i < 56) indices.push(j, j + 1, j + 2, j + 1, j + 3, j + 2);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3)); g.setIndex(indices); g.computeVertexNormals();
    mesh(slice, g, cutMetal);
    const path = Array.from({ length: 29 }, (_, j) => {
      const a = deformCan(theta, j / 28, { a: 0, b: 0, c: 0, shiver: 0 });
      return V(a.x, a.y, a.z);
    });
    mesh(slice, new THREE.TubeGeometry(new THREE.CatmullRomCurve3(path), 32, .008, 6, false), cutMetal);
  }
  const lid = new THREE.Group(), foot = new THREE.Group();
  root.add(lid, foot);
  lid.position.y = HALF; foot.position.y = -HALF;
  // An actual open drinking port, not a black decal. The flipped can uses
  // the same lid mesh, so the opening's position is consistent at the seal.
  const disk = new THREE.Shape().absarc(0, 0, .729, 0, TAU);
  const port = new THREE.Path().absellipse(0, -MOUTH, .175, .237, 0, TAU, true);
  disk.holes.push(port);
  const cap = mesh(lid, new THREE.ShapeGeometry(disk, 70), cutMetal, 0, -.036, 0);
  cap.rotation.x = -PI / 2;
  rolledRim(lid, .726, -.008, silver);
  rolledRim(lid, .653, -.035, silver).scale.z = .57;
  rolledRim(lid, .605, -.038, pbr('#748893', .49, .64)).scale.z = .25;
  rolledRim(lid, .687, -.012, silver).scale.z = .46;
  const mouthEdge = ring(lid, 1, .031, silver, [0, -.032, MOUTH]);
  mouthEdge.rotation.x = -PI / 2; mouthEdge.scale.set(.171, .233, .24);
  cylinder(lid, .077, .084, .027, silver, [0, .003, .019]);
  for (const [z, sx, sy] of [[-.205, .155, .163], [-.021, .101, .087]]) {
    const tab = ring(lid, 1, .22, silver, [0, .016, z]);
    tab.rotation.x = -PI / 2; tab.scale.set(sx, sy, .060);
  }
  bevel(lid, [.235, .025, .08], .012, silver, [0, .017, -.105]);
  rolledRim(foot, canRadius(0) - .012, .008, silver);
  const base = new THREE.LatheGeometry([[0, .12], [.29, .10], [.47, .053], [.62, .009], [.705, 0], [.748, .039]].map(([r, y]) => new THREE.Vector2(r, y)), 72);
  mesh(foot, base, cutMetal);
  rolledRim(foot, .479, .064, silver).scale.z = .5;
  const liquid = new THREE.Group();
  slice.add(liquid);
  const liquidSurface = pbr('#909b95', .21, .32, { transparent: true, opacity: .78, emissive: '#50250e', emissiveIntensity: .26 });
  cylinder(liquid, .761, .722, .156, liquidSurface, [0, -1.42, 0]);
  const hotMeniscus = rolledRim(liquid, .72, -1.344, pbr('#a9b8af', .42, .46));
  hotMeniscus.scale.z = .32;
  let last = '';
  function update(state) {
    full.visible = !state.cutaway;
    slice.visible = state.cutaway;
    liquid.visible = state.hot;
    const { a, b, c, shiver } = state.collapse;
    const key = `${a}:${b}:${c}:${shiver}`;
    if (last !== key) { all.set(state.collapse); last = key; }
    const cap = footPose(state.collapse);
    foot.position.set(cap.x, cap.y, 0);
    foot.rotation.z = cap.rotation;
  }
  return { update, lid };
}

function vessel(parent) {
  const brushed = strokeMaterial();
  const metal = pbr('#26353d', .64, .76, { roughnessMap: brushed });
  const rim = pbr('#78919d', .52, .83, { roughnessMap: brushed });
  const base = pbr('#141c24', .48, .56);
  cylinder(parent, 2.75, 2.64, .17, base, [0,.10,0]);
  const shell = [[0,.195],[2.23,.197],[2.44,.218],[2.63,.381],[2.75,.677],[2.77,.800],[2.74,.816],[2.68,.819],[2.645,.74],[2.58,.57],[2.43,.374],[2.23,.30],[0,.3]];
  const bowl = new THREE.LatheGeometry(shell.map(([r,y]) => new THREE.Vector2(r,y)), 120);
  mesh(parent, bowl, metal);
  rolledRim(parent, 2.728, .797, rim);
  rolledRim(parent, 2.578, .331, metal);
  cylinder(parent, 2.51, 2.36, .096, pbr('#142a35', .58, .51), [0,.26,0]);
  return waterPlate(parent);
}

function machine(parent, lid) {
  const dark = pbr('#263846', .51, .67, { roughnessMap: strokeMaterial() });
  const railMetal = pbr('#98afbb', .42, .85);
  const brushed = pbr('#657d89', .55, .79, { roughnessMap: strokeMaterial() });
  const black = pbr('#14222a', .54, .41);
  const gasket = pbr('#4d3a27', .67, .30);
  const shoe = new THREE.Group(); lid.add(shoe);
  // Rear yoke touches the rolled lid only, leaving the opening and wall free.
  for (const x of [-.51,.51]) {
    bevel(shoe, [.166,.122,.20], .027, gasket, [x,-.105,-.54]);
    bevel(shoe, [.157,.108,.294], .025, brushed, [x,-.079,-.684]);
    const bolt = cylinder(shoe,.038,.038,.030,railMetal,[x,-.008,-.73]);
    bolt.rotation.z = .20;
  }
  bevel(shoe, [1.15,.095,.16], .028, dark, [0,-.072,-.80]);
  const eye = cylinder(shoe,.125,.125,.119,brushed,[0,-.032,-.874]);
  eye.rotation.x = PI / 2;
  const frame = new THREE.Group(); parent.add(frame);
  const stand = V(1.86, 0, -1.49);
  bevel(frame, [.86,.23,.72], .092, black, [stand.x,.105,stand.z]);
  bevel(frame, [.42,4.51,.377], .075, dark, [stand.x,2.36,stand.z]);
  for (const x of [-.119,.119]) {
    cylinder(frame,.032,.032,4.16,railMetal,[stand.x+x,2.35,stand.z+.225]);
  }
  bevel(frame, [.52,.14,.46], .045, brushed, [stand.x,4.61,stand.z]);
  const carriage = bevel(frame, [.49,.365,.282], .063, brushed, [stand.x,2.64,stand.z+.20]);
  const boom = new THREE.Group(); frame.add(boom);
  const sleeve = bevel(boom, [.22,1,.22], .034, dark, [0,0,0]);
  const ram = bevel(boom, [.118,1,.118], .028, railMetal, [0,0,0]);
  const swivel = cylinder(frame,.113,.113,.110,brushed,[0,0,0]); swivel.rotation.x = PI / 2;
  const axis = V(0,1,0), anchor = V(0,0,0), delta = V(0,0,0), joint = V(0,0,0);
  return (active, framing) => {
    frame.visible = active && framing;
    shoe.visible = active;
    if (!frame.visible) return;
    joint.set(0,-.032,-.885);
    lid.localToWorld(joint);
    carriage.position.y = joint.y + .163;
    anchor.set(stand.x, carriage.position.y, stand.z+.39);
    delta.copy(joint).sub(anchor);
    const distance = delta.length();
    boom.position.copy(anchor);
    boom.quaternion.setFromUnitVectors(axis, delta.normalize());
    sleeve.scale.y = distance * .65; sleeve.position.y = distance * .325;
    ram.scale.y = distance * .46; ram.position.y = distance * .77;
    swivel.position.copy(joint);
  };
}

function heater(parent) {
  const base = pbr('#231c1c', .52, .67);
  const rim = pbr('#48382c', .50, .74);
  const warm = pbr('#633019', .48, .39, { emissive: '#c45123', emissiveIntensity: .65 });
  cylinder(parent, 1.93, 1.82, .255, base, [0, .17, 0]);
  cylinder(parent, 1.44, 1.74, .105, rim, [0, .295, 0]);
  cylinder(parent, 1.37, 1.39, .042, base, [0, .32, 0]);
  for (const r of [1.16, 1.28, 1.397]) rolledRim(parent, r, .322, r === 1.28 ? warm : rim);
  for (let i = 0; i < 20; i++) {
    const a = i / 20 * TAU;
    const slot = bevel(parent, [.126, .045, .04], .013, pbr('#090d0f', .69, .35), [Math.sin(a) * 1.884, .175, Math.cos(a) * 1.884]);
    slot.rotation.y = a;
  }
}

function softSteam(root) {
  const items = [];
  const spriteMap = texture(96, 96, (c) => {
    const random = rng(64);
    for (let i = 0; i < 31; i++) {
      const a = random() * TAU, r = Math.sqrt(random()) * 25;
      const x = 48 + Math.sin(a) * r, y = 48 + Math.cos(a) * r, size = 10 + random() * 15;
      const g = c.createRadialGradient(x, y, 0, x, y, size);
      g.addColorStop(0, 'rgba(255,255,255,.21)'); g.addColorStop(.5, 'rgba(255,255,255,.085)'); g.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = g; c.fillRect(0, 0, 96, 96);
    }
  });
  const random = rng(221);
  for (let i = 0; i < 17; i++) {
    const material = new THREE.SpriteMaterial({ map: spriteMap, color: '#e0e5df', depthWrite: false, transparent: true });
    const sprite = new THREE.Sprite(material);
    root.add(sprite);
    items.push({ sprite, phase: random(), speed: .54 + .32 * random(), spread: .5 + random() * .8 });
  }
  return (time, amount, sourceY) => {
    for (const { sprite, phase, speed, spread } of items) {
      const t = (time * speed + phase) % 1;
      const spreadNow = t ** 1.3 * spread;
      sprite.visible = amount > .008;
      sprite.position.set(Math.cos(phase * TAU + t * 5) * spreadNow * .37 - t * .22, sourceY + t * 1.65, MOUTH + Math.sin(phase * TAU + t * 3) * spreadNow * .3);
      sprite.scale.set(.17 + t * .92 * spread, .28 + t * .89 * spread, 1);
      sprite.material.opacity = amount * (.08 + .29 * Math.sin(PI * t)) * (1 - t * .71);
      sprite.material.rotation = phase * TAU + t;
    }
  };
}

function fillTracers(root) {
  const material = pbr('#c3d0d0', .26, .34, { emissive: '#626763', emissiveIntensity: .25 });
  const n = 64;
  const particles = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 8, 6), material, n);
  const bubbleMat = pbr('#bcc7b8', .19, .22, { transparent: true, opacity: .65, depthWrite: false });
  const boil = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), bubbleMat, 19);
  boil.frustumCulled = false;
  boil.renderOrder = 2;
  root.add(boil);
  particles.frustumCulled = false;
  root.add(particles);
  const random = rng(5);
  const seeds = Array.from({ length: n }, () => [random(), random(), random(), random(), random()]);
  function update(t, pose, shot) {
    particles.visible = pose.cutaway || shot === 3;
    boil.visible = shot === 2;
    if (boil.visible) {
      for (let i = 0; i < boil.count; i++) {
        const [a, phase, speed, disk] = seeds[i];
        const rise = (t * (.85 + speed * 1.58) + phase) % 1;
        const r = .57 * Math.sqrt(disk);
        const radius = (.011 + phase * .034) * smooth(rise / .22) * (1 - smooth((rise - .67) / .33));
        putInstance(boil, i, r * Math.sin(a * TAU), -1.4 + rise * .117, r * Math.cos(a * TAU), radius, radius * .72);
      }
      boil.instanceMatrix.needsUpdate = true;
    }
    if (!particles.visible) return;
    const c = new THREE.Color();
    for (let i = 0; i < n; i++) {
      const [angle, phase, s, edge, motion] = seeds[i];
      const clock = t * (.24 + .34 * motion) + phase;
      const a = angle * TAU + .25 * Math.sin(t * (1.3 + s) + phase * TAU);
      const f = clock % 1;
      const gas = .0079 + .013 * s;
      if (shot === 3) {
        const amp = Math.sin(PI * f);
        const air = i < 24;
        const width = .08 + f * .42;
        putInstance(particles, i, Math.sin(a) * width * edge - f * f * .28, HALF + f * (1.18 + s * .64) + .011, MOUTH + Math.cos(a) * width * edge, amp * gas * (air ? 1.06 : .56));
        c.copy(air ? COOL : WARM);
      } else if (pose.hot) {
        const r = .652 * Math.sqrt(edge);
        const radius = gas * Math.sin(PI * f) ** .35;
        putInstance(particles, i, Math.sin(a) * r, -1.37 + f * 2.79, Math.cos(a) * r, radius, radius * (1.10 + phase * .25));
        c.copy(WARM).lerp(COOL, s > .80 ? .95 : 0);
      } else {
        const remains = vaporRemaining(t);
        const bead = smooth((t - AIR_TIMING.condense - phase * 2.74) / .74);
        const section = clamp(.08 + edge * .76, 0, 1);
        const r = mix(.12 + .55 * Math.sqrt(edge), canRadius(section) - .075, bead);
        const height = mix(-1.35 + 2.65 * ((phase + .06 * Math.sin(t * 4.1 + motion * TAU)) % 1), (section - .5) * CAN_H, bead);
        const slideAge = Math.max(0, t - 15.22 - motion * 2.64);
        const drift = Math.min(.47, .23 * slideAge ** 2);
        const size = mix(gas * (i / n < remains ? 1 : .34), (.009 + s * .023) * (i % 4 === 0 ? 1.18 : .66), bead);
        putInstance(particles, i, Math.sin(a) * r, Math.min(1.39, height + bead * drift), Math.cos(a) * r, size, size * (1 + bead * .50));
        c.copy(WARM).lerp(WHITE, bead);
      }
      particles.setColorAt(i, c);
    }
    particles.instanceMatrix.needsUpdate = true;
    particles.instanceColor.needsUpdate = true;
  }
  return update;
}

function surfaceBeads(can) {
  const n = 56;
  const material = pbr('#adc6cc', .19, .32, { emissive: '#26323a', emissiveIntensity: .11 });
  const water = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), material, n);
  water.frustumCulled = false;
  can.add(water);
  const random = rng(139);
  const queue = Array.from({ length: n }, () => [random() * TAU, mix(.12,.902,random()), random(), random()]);
  const p = V(0, 0, 0);
  return (t, state, age, shot) => {
    water.visible = !state.hot && !state.cutaway && shot !== 8;
    if (!water.visible) return;
    const wet = shot === 4 ? smooth(age / .46) : 1;
    for (let i = 0; i < n; i++) {
      const [theta, level, size, phase] = queue[i];
      const falling = clamp(t - 23.78 - 2.17 * phase);
      const v = Math.min(.935, level + (i % 6 === 0 ? falling * falling * .089 : .0));
      deformCan(theta, v, state.collapse, -.011, p);
      const scale = wet * (.008 + .023 * size ** 1.75);
      putInstance(water, i, p.x,p.y,p.z,scale,scale*(1.14 + phase*.58));
    }
    water.instanceMatrix.needsUpdate = true;
  };
}

function contact(parent) {
  const shade = texture(144, 144, (c, w) => {
    const gradient = c.createRadialGradient(w/2,w/2,w*.18,w/2,w/2,w*.493);
    gradient.addColorStop(0,'#040912d9'); gradient.addColorStop(.62,'#0509108a'); gradient.addColorStop(1,'#04070e00');
    c.fillStyle=gradient; c.fillRect(0,0,w,w);
  });
  const patch = mesh(parent,new THREE.PlaneGeometry(7.7,7.7),new THREE.MeshBasicMaterial({ map: shade, transparent:true, depthWrite:false }),0,.006,0);
  patch.rotation.x=-PI/2;
  patch.renderOrder=1;
}

export function labEnvironment(generator) {
  const room = new THREE.Scene(); room.background = new THREE.Color('#18232e');
  const banks = [
    [[-4.1,3.1,2.9],[3.0,5.9],'#ffe3cb',2.6],
    [[3.46,2.44,-3.66],[1.22,5.4],'#acf4ff',3.2],
    [[.28,5.86,.07],[4.1,2.1],'#f4fbfa',1.18],
    [[4.7,1.05,2.8],[3.1,4.4],'#ccddf2',.48],
  ];
  const feather = texture(96, 128, (c,w,h) => {
    const a=c.createLinearGradient(0,0,w,0); a.addColorStop(0,'#171717'); a.addColorStop(.12,'#f4f4f4'); a.addColorStop(.79,'#fff'); a.addColorStop(1,'#4a4a4a');
    c.fillStyle=a; c.fillRect(0,0,w,h);
  });
  for (const [pos,[w,h],color,brightness] of banks) {
    const m = new THREE.MeshBasicMaterial({ map: feather, color: new THREE.Color(color).multiplyScalar(brightness), side:THREE.DoubleSide, toneMapped:false });
    const card=mesh(room,new THREE.PlaneGeometry(w,h),m,...pos);
    card.lookAt(0,.55,0);
  }
  const target=generator.fromScene(room,.047);
  room.traverse((o)=> { o.geometry?.dispose(); o.material?.dispose(); }); feather.dispose();
  return target.texture;
}

// Dolly tracks, not dependent on frame-rate. Off-axis arc and distinct focal
// lengths keep this feeling like photographed coverage of one practical set.
const cine = [
  [[[1.94,2.64,5.19],[1.22,2.49,4.98]], [[-.04,2.12,.0],[.05,2.07,0]], [50,52], 6],
  [[[-2.94,3.34,5.38],[-1.68,2.77,5.10]], [[.0,2.06,0],[.0,2.09,0]], [45,47], 5],
  [[[-.55,2.64,4.99],[.13,2.46,4.63]], [[-.02,2.04,0],[.0,2.04,0]], [46,46], 3],
  [[[1.33,4.73,2.65],[.48,4.58,2.13]], [[.04,3.57,.27],[-.01,3.64,.22]], [37,36], 12],
  [[[-2.28,3.57,7.07],[-1.05,2.94,6.46]], [[.12,2.27,.04],[.17,2.24,0]], [38,39], 4],
  [[[.32,1.33,3.51],[.48,1.19,3.29]], [[.0,1.18,.12],[.025,1.12,.11]], [41,43], 10],
  [[[.38,2.82,4.77],[.02,2.42,4.43]], [[.0,2.29,0],[.0,2.23,0]], [46,47], 4],
  [[[.18,2.66,6.02],[.10,2.48,5.76]], [[.02,2.17,.06],[.02,2.12,0]], [42,42], 3],
  [[[-.72,3.03,6.74],[-.14,2.67,6.36]], [[.02,2.11,0],[.02,2.13,0]], [40,40], 4],
  [[[-1.27,2.74,4.27],[-1.70,2.26,4.33]], [[-.03,2.15,.07],[-.05,1.95,.12]], [51,49], 11],
  [[[2.94,2.78,5.34],[1.98,2.43,5.49]], [[-.02,1.91,0],[.03,1.94,0]], [49,49], 4],
];

export async function airCrush(env) {
  const scene = new THREE.Scene();
  scene.environment = env; scene.environmentIntensity = .95;
  const teal = background(['#050c15', '#122b3d', '#496e7536']);
  const gold = background(['#0d0c11', '#30201d', '#bc784f42']);
  scene.add(new THREE.HemisphereLight('#d9e6eb','#171a28',.29));
  const key = new THREE.DirectionalLight('#fff0e1', 2.05);
  key.position.set(-3.7,5.2,3.42); scene.add(key);
  const edge = new THREE.DirectionalLight('#8dd9ff', 2.63);
  edge.position.set(3.1,3.66,-3.77); scene.add(edge);
  const matte = texture(144, 144, (c, w) => {
    const g = c.createRadialGradient(w / 2, w / 2, w * .12, w / 2, w / 2, w * .49);
    g.addColorStop(0, '#fff'); g.addColorStop(.33, '#fff');
    g.addColorStop(.70, '#3f3f3f'); g.addColorStop(1, '#000');
    c.fillStyle = g; c.fillRect(0, 0, w, w);
  }, THREE.NoColorSpace);
  const floor = mesh(scene, new THREE.PlaneGeometry(14, 14), pbr('#17212b', .48, .53, { alphaMap: matte, transparent: true, depthWrite: false }));
  floor.rotation.x = -PI / 2;
  floor.renderOrder = -6;
  contact(scene);
  const cam = camera();
  const cold = new THREE.Group(), hot = new THREE.Group(), can = new THREE.Group();
  scene.add(cold, hot, can);
  const bath = vessel(cold);
  heater(hot);
  const { update, lid } = makeCan(can);
  const stageRig = machine(cold, lid);
  const steam = softSteam(can);
  const gas = fillTracers(can);
  const droplets = surfaceBeads(can);
  const waterFX = splashes(cold);
  const graphics = pressureMarks(cold);
  const amber = new THREE.PointLight('#fe8d4f', 9.2, 4.1, 1.55);
  amber.position.set(-1.05, .7, .95); hot.add(amber);
  const fixture = pbr('#242d37', .57, .53), dark = pbr('#18232d',.55,.48);
  for (const x of [-4.1,3.94]) {
    bevel(scene, [.32,5.65,.26], .105, fixture,[x,2.52,-5.72]);
    box(scene,[.85,3.76,.09],dark,[x,2.68,-5.87]);
  }
  const bounce = new THREE.DirectionalLight('#bcd3e1', .29);
  bounce.position.set(2.2, 1.32, 4.5);
  scene.add(bounce);
  const motes = dust(scene,174,30,[[-3.4,3.6],[.4,5.3],[-3.65,2.8]],'#b8d6dd',.019);
  motes.material.opacity=.30;
  return { scene, cam, update(t, cut) {
    const idx=cut.index;
    const state=poseAt(t,idx);
    cold.visible=!state.hot; hot.visible=state.hot;
    scene.background=state.hot?gold:teal;
    key.color.set(state.hot?'#ffe1c7':'#fff4ea');
    edge.color.set(state.hot?'#f4ae76':'#81c8ff');
    edge.intensity=state.hot?2.2:2.6;
    can.rotation.set(0,-.12-.13*Math.sin(PI*state.turn),-PI*state.turn);
    can.position.set(0,state.centerY,0);
    update(state);
    stageRig(!state.hot,idx===4||idx===8||idx===10);
    steam(t,state.hot&&idx!==2?(idx===3?1.45:.98):0,HALF+.05);
    gas(t,state,idx);
    const impulse=waterEvent(t,idx);
    droplets(t,state,impulse,idx);
    bath.age.value=impulse;
    bath.time.value=t;
    bath.strength.value=idx===0||idx>=9?.85:1.04;
    waterFX(impulse,idx===0||idx>=9?.84:1.03);
    graphics(t,cut);
    motes.rotation.y=.018*t;
    const [pos,aim,mm,aperture]=cine[idx];
    const keyT=idx===4?Math.max(0,cut.progress*.96):cut.progress;
    const onset=idx===0?AIR_TIMING.hookSnap:AIR_TIMING.snap;
    const kick=(idx===0||idx===9)&&t>onset?Math.sin((t-onset)*29.0)*Math.exp(-10.5*(t-onset))*.034:0;
    const tracks=pos.map(([x,y,z])=>V(x+kick,y+kick*.32,z));
    const target=aim.map((v)=>V(...v));
    const focus = idx===3 ? [V(.02,3.43,.33), V(.04,3.64,.24)] : idx===5 ? [V(.05,.91,.3),V(.05,.71,.29)] : aim.map(([x,y,z])=>V(x,y,z+.57));
    frame(cam,keyT,tracks,target,focus,{mm,aperture, exposure:idx===2||idx===6?.99:1.08,bloom:.23,smear:0});
  } };
}
