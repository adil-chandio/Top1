import * as THREE from 'three';
import woodURL from './textures/walnut.jpg?url';
import lunaURL from './textures/moon-albedo.jpg?url';
import { bevel, box, camera, cylinder, dust, frame, glowTexture, lightPool, mesh, PI, pbr, ring, rng, strokeMaterial, studio, TAU, texture, V } from './stage.js';
import { clamp, fallingBody, fileDropCue, hingeAngle, keplerPosition, LAMP_TRAVEL, MOON_ORBIT, smooth } from './motion.js';

async function load(url, repeat = [1, 1]) {
  const t = await new THREE.TextureLoader().loadAsync(url);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(...repeat);
  t.anisotropy = 4;
  return t;
}

function phoneInterface() {
  return texture(512, 1024, (c, w, h) => {
    const bg = c.createLinearGradient(0, 0, w, h);
    bg.addColorStop(0, '#101b2b'); bg.addColorStop(1, '#070d19');
    c.fillStyle = bg; c.fillRect(0, 0, w, h);
    c.fillStyle = '#4a6e88';
    for (let x = 22; x < w; x += 22) for (let y = 180; y < 975; y += 22) c.fillRect(x, y, 1, 1);
    c.fillStyle = '#95b3c9'; c.font = '22px monospace'; c.fillText('D E V I C E   /   0 1', 40, 125);
    c.fillStyle = '#f2f8fc'; c.font = 'bold 69px sans-serif'; c.fillText('Storage', 36, 211);
    c.fillStyle = '#7facc8'; c.font = '22px monospace'; c.fillText('CAPACITY', 39, 254);
    c.fillStyle = '#6b8193'; c.font = '19px monospace'; c.fillText('FILE VISUALIZATION', 40, 446);
    c.strokeStyle = '#34506a'; c.beginPath(); c.moveTo(39, 468); c.lineTo(473, 468); c.stroke();
    for (let y = 528; y < 920; y += 118) {
      c.strokeStyle = '#263b52'; c.beginPath(); c.moveTo(45, y); c.lineTo(469, y); c.stroke();
    }
    c.fillStyle = '#809bad'; c.font = '16px monospace'; c.fillText('REVIEW LARGE FILES FIRST', 40, 943);
  });
}

async function phone(env) {
  const floor = pbr('#161f31', .48, .25);
  const scene = studio(env, { bg: ['#090d17', '#253f5d', '#34638d45'], environment: .71, sky: '#bbd8ee', ground: '#1f2946', key: '#e2f4ff', rim: '#78a9ff', keyPower: 3.2, rimPower: 3.2 }, floor);
  const softKey = new THREE.DirectionalLight('#ffc395', 1.1);
  softKey.position.set(-3, 1.2, 4);
  scene.add(softKey);
  const brushed = strokeMaterial();
  const edges = pbr('#71859b', .31, .83, { roughnessMap: brushed });
  const milledDark = pbr('#243346', .29, .77, { roughnessMap: brushed });
  const rearGlass = pbr('#171f2d', .39, .38, { roughnessMap: brushed });
  lightPool(scene, '#5779a5', .25, 6.6, -.8, .37);
  const stage = cylinder(scene, 1.58, 1.56, .13, pbr('#263447', .37, .57), [0, .067, 0], true);
  stage.receiveShadow = true;
  ring(scene, 1.55, .009, edges, [0, .108, 0]).rotation.x = PI / 2;
  const body = new THREE.Group();
  scene.add(body);
  body.position.set(0, 1.902, 0);
  body.rotation.y = -.09;
  bevel(body, [1.8, 3.54, .28], .128, edges, [0, 0, 0], true);
  bevel(body, [1.767, 3.50, .109], .054, rearGlass, [0, 0, -.108]);
  bevel(body, [1.755, 3.49, .13], .063, pbr('#0b111d', .22, .52), [0, 0, .096]);
  const interfaceMat = new THREE.MeshBasicMaterial({ map: phoneInterface() });
  mesh(body, new THREE.PlaneGeometry(1.61, 3.34), interfaceMat, 0, 0, .163);
  bevel(body, [.34, .052, .026], .013, pbr('#06070b', .25, .55), [0, 1.57, .177]);
  bevel(body, [.035, .28, .086], .017, edges, [-.901, .719, .03]);
  bevel(body, [.035, .27, .086], .017, edges, [-.901, .345, .03]);
  bevel(body, [.035, .45, .088], .017, edges, [.903, .41, .03]);
  bevel(body, [.81, .82, .083], .038, milledDark, [-.345, 1.21, -.17]);
  const lensGlass = pbr('#172c3b', .11, .45, { emissive: '#163144', emissiveIntensity: .18 });
  for (const [x, y, r] of [[-.53, 1.39, .148], [-.22, 1.29, .142], [-.50, 1.066, .137]]) {
    cylinder(body, r * 1.13, r * 1.13, .067, edges, [x, y, -.228]).rotation.x = PI / 2;
    cylinder(body, r, r, .024, milledDark, [x, y, -.269]).rotation.x = PI / 2;
    const glass = mesh(body, new THREE.SphereGeometry(r * .81, 24, 12), lensGlass, x, y, -.279);
    glass.scale.z = .23;
    ring(body, r * .79, .005, pbr('#596083', .31, .74), [x, y, -.291]);
    ring(body, r * .42, .004, pbr('#2d6288', .28, .62), [x, y, -.303]);
  }
  cylinder(body, .055, .055, .016, pbr('#eed4a0', .55), [-.161, 1.51, -.219]).rotation.x = PI / 2;

  const trackWidth = 1.35;
  bevel(body, [trackWidth, .13, .027], .012, pbr('#334355', .53, .21), [0, .70, .18]);
  const meterMat = pbr('#80dbec', .32, .22, { emissive: '#8acaff', emissiveIntensity: .35 });
  const meter = bevel(body, [trackWidth - .03, .082, .02], .009, meterMat, [0, .70, .193]);
  // A thin highlight moving on the assembly is a studio softbox, not a UI filter.
  const strip = new THREE.PointLight('#8ae2ff', 5.6, 4.6, 2);
  scene.add(strip);
  const colors = ['#aecee4', '#7693be', '#db9170', '#557e93', '#a8a5c1', '#b88776'];
  const cells = colors.map((color, i) => {
    const cell = new THREE.Group(); body.add(cell);
    const matte = pbr(color, .26, .59, { roughnessMap: brushed });
    const metal = pbr('#35475b', .26, .73);
    bevel(cell, [.382, .239, .072], .026, metal);
    bevel(cell, [.358, .216, .038], .018, matte, [0, 0, .037]);
    bevel(cell, [.21, .016, .023], .006, pbr('#dfeaf4', .49, .11), [0, -.052, .061]);
    bevel(cell, [.095, .046, .020], .009, pbr('#bed0df', .37, .22), [-.052, .038, .057]);
    return cell;
  });
  const motes = dust(scene, 47, 88, [[-2.8, 2.8], [.2, 4.3], [-1.8, 1.2]], '#bbdbfa', .019);
  const cam = camera();
  const cyan = new THREE.Color('#78cbe3');
  const alert = new THREE.Color('#f96153');
  const grip = new THREE.Color('#f5ab70');
  return { scene, cam, update(t, cut) {
    const progress = smooth((t - 3.36) / 2.65);
    const selected = smooth((t - 7.39) / 1.08);
    const f = .46 + .5 * progress;
    meter.scale.x = f;
    meter.position.x = -(trackWidth - .03) * (1 - f) * .5;
    meterMat.color.copy(cyan).lerp(alert, progress).lerp(grip, selected * .22);
    meterMat.emissive.copy(meterMat.color);
    strip.position.set(-1.2 + smooth(t / 3.3) * 1.7, 3.04, -1.18);
    motes.position.y = .022 * t;
    for (const [i, cell] of cells.entries()) {
      const cue = fileDropCue(i);
      const age = t - cue.release;
      const fall = fallingBody(age, cue);
      const settling = smooth((age - .15) / .67);
      const lift = i === 5 ? selected : 0;
      const base = i < 3 ? -.93 : -.56;
      cell.visible = age >= 0;
      cell.position.set((i % 3 - 1) * .454 + lift * .21, base + fall.height + lift * .10, .231 + (1 - settling) * .60 + lift * .48);
      cell.rotation.set((1 - settling) * .42, (1 - settling) * .36 + lift * -.12, (1 - settling) * (i % 2 ? .38 : -.28));
    }
    if (cut.index === 0) {
      frame(cam, cut.progress, [V(-1.42, 3.56, -3.46), V(-1.86, 3.29, -3.86)], [V(-.40, 3.05, -.20), V(-.19, 2.68, -.11)], [V(-.54, 3.31, -.26), V(-.04, 2.70, -.09)], { mm: [76, 66], roll: [-.043, -.022], aperture: 19, smear: .48, bloom: .47 });
    } else if (cut.index === 1) {
      frame(cam, cut.progress, [V(2.73, 2.87, 6.2), V(1.14, 2.67, 6.38)], [V(.04, 1.96, .16), V(.03, 1.99, .27)], null, { mm: [36, 41], roll: [.026, .005], aperture: 9, smear: .66, bloom: .44 });
    } else {
      frame(cam, cut.progress, [V(.72, 2.67, 5.30), V(.29, 2.55, 6.54)], [V(.16, 2.21, .21), V(.02, 1.97, .17)], [V(.46, 1.36, .70), V(.07, 2.04, .20)], { mm: [44, 44], roll: [-.012, 0], aperture: 8, smear: .42, bloom: .55 });
    }
  } };
}

function notebookMap() {
  return texture(512, 512, (c, w, h) => {
    const rand = rng(784);
    c.fillStyle = '#d7cbbb'; c.fillRect(0, 0, w, h);
    c.lineWidth = 1.3; c.strokeStyle = '#827964';
    for (let y = 78; y < h - 24; y += 29) { c.beginPath(); c.moveTo(27, y); c.lineTo(w - 27, y); c.stroke(); }
    c.fillStyle = '#342c25'; c.font = '20px serif'; c.fillText('STUDIO NOTES    /    01', 28, 56);
    for (let i = 0; i < 2890; i++) {
      c.fillStyle = rand() < .5 ? '#22190f13' : '#fff7e332'; c.fillRect(rand() * w, rand() * h, 1, 1);
    }
  });
}

async function halo(env) {
  const walnut = await load(woodURL, [3, 3]);
  const scene = studio(env, { bg: ['#100b10', '#443129', '#7d4e394b'], environment: .61, sky: '#eadac7', ground: '#57422e', key: '#ffe9c9', rim: '#8cacd1', keyPower: 2.55, rimPower: 2.4, keyAt: V(4.2, 6.4, 3.8), ambient: .72 }, pbr('#a5846b', .49, .14, { map: walnut, bumpMap: walnut, bumpScale: .095 }));
  const brushed = strokeMaterial();
  const copper = pbr('#a66d48', .28, .84, { roughnessMap: brushed });
  const bright = pbr('#e2ad81', .22, .82, { roughnessMap: brushed });
  const black = pbr('#202123', .32, .72, { roughnessMap: brushed });
  const inset = pbr('#4a3d37', .34, .55);
  const desk = new THREE.Group(); scene.add(desk);
  desk.rotation.y = .14;
  const base = bevel(desk, [2.07, .16, 1.30], .072, black, [-.23, .084, -.24], true);
  base.receiveShadow = true;
  bevel(desk, [2.02, .037, 1.25], .018, copper, [-.23, .175, -.24]);
  bevel(desk, [1.94, .017, 1.15], .008, inset, [-.23, .196, -.24]);
  const knob = new THREE.Group(); desk.add(knob);
  knob.position.set(-.83, .235, .147);
  cylinder(knob, .123, .131, .085, bright);
  cylinder(knob, .109, .109, .008, black, [0, .046, 0]);
  for (let i = 0; i < 18; i++) {
    const a = TAU * i / 18;
    box(knob, [.013, .057, .009], black, [Math.cos(a) * .128, -.003, Math.sin(a) * .128]).rotation.y = -a + PI / 2;
  }
  const lit = pbr('#aec89e', .43, .09, { emissive: '#aaffb1', emissiveIntensity: 0 });
  cylinder(desk, .019, .019, .011, lit, [-.83, .205, .335]);
  const pole = new THREE.CatmullRomCurve3([V(-.74, .18, -.58), V(-.79, 1.19, -.68), V(-.79, 2.69, -.69), V(-.67, 3.24, -.62), V(-.28, 3.51, -.44)]);
  mesh(desk, new THREE.TubeGeometry(pole, 43, .071, 10, false), black, 0, 0, 0, true);
  cylinder(desk, .113, .13, .12, copper, [-.74, .24, -.58], true);
  const pivot = new THREE.Group(); desk.add(pivot);
  pivot.position.set(-.27, 3.49, -.43);
  cylinder(pivot, .116, .123, .235, bright).rotation.z = PI / 2;
  const housing = new THREE.Group(); pivot.add(housing);
  housing.position.set(.54, .03, .30);
  const profile = [[.851, -.067], [.865, -.089], [1.093, -.089], [1.129, -.073], [1.147, -.038], [1.147, .055], [1.133, .081], [1.106, .093], [.87, .093], [.851, .07], [.851, -.067]];
  mesh(housing, new THREE.LatheGeometry(profile.map(([x, y]) => new THREE.Vector2(x, y)), 76), copper, 0, 0, 0, true);
  ring(housing, 1.133, .014, bright, [0, .049, 0]).rotation.x = PI / 2;
  ring(housing, 1.147, .010, black, [0, -.017, 0]).rotation.x = PI / 2;
  const diffuser = pbr('#fbc785', .36, .08, { emissive: '#ffd298', emissiveIntensity: .02 });
  mesh(housing, new THREE.RingGeometry(.884, 1.091, 76), diffuser, 0, -.093, 0).rotation.x = PI / 2;
  const lamp = new THREE.SpotLight('#ffd3a1', 0, 10, .47, .82, 2);
  lamp.position.set(.24, 3.37, -.13);
  const lampTarget = V(.55, .02, .27);
  scene.add(lamp, lamp.target);
  const pool = lightPool(scene, '#dc8535', 0, 5.9, .42, .4);
  const core = lightPool(scene, '#ffc96d', 0, 3.45, .58, .57, .013);
  const beam = mesh(scene, new THREE.CylinderGeometry(.67, 1.88, 1, 32, 1, true), new THREE.ShaderMaterial({
    transparent: true, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { power: { value: 0 } },
    vertexShader: `varying vec2 q; varying vec3 normalV, viewV;
      void main(){ q=uv; normalV=normalize(normalMatrix*normal); vec4 p=modelViewMatrix*vec4(position,1.);viewV=normalize(-p.xyz);gl_Position=projectionMatrix*p; }`,
    fragmentShader: `varying vec2 q; varying vec3 normalV, viewV; uniform float power;
      void main(){float edge=pow(abs(dot(normalize(normalV),normalize(viewV))),2.);float fade=sin(3.141593*q.y);
        gl_FragColor=vec4(1.,.52,.26,edge*fade*.035*power);}`,
  }));
  const up = V(0, 1, 0);
  const lightAxis = V(0, 0, 0);
  const motes = dust(scene, 3391, 136, [[-1.96, 2.21], [.31, 3.79], [-1.1, 1.32]], '#ffd595', .019);
  const notebook = new THREE.Group(); scene.add(notebook);
  notebook.position.set(.78, .018, .86); notebook.rotation.y = -.40;
  bevel(notebook, [1.36, .063, .92], .028, pbr('#c5ac90', .69, .06), [0, .049, 0], true);
  bevel(notebook, [1.40, .028, .958], .013, pbr('#3b2b26', .58), [0, .013, 0], true);
  const paper = mesh(notebook, new THREE.PlaneGeometry(1.31, .87), pbr('#d7c1a2', .74, .07, { map: notebookMap() }), 0, .083, 0);
  paper.rotation.x = -PI / 2; paper.receiveShadow = true;
  for (let i = 0; i < 5; i++) box(notebook, [1.31, .001, .003], pbr('#9e8064', .71), [0, .025 + i * .010, .461]);
  const pen = cylinder(notebook, .025, .026, .78, black, [.31, .109, -.11], true);
  pen.rotation.set(0, .2, PI / 2 - .13);
  cylinder(pen, .020, .006, .072, bright, [0, -.417, 0]);
  const cam = camera();
  return { scene, cam, update(t, cut) {
    const pressed = smooth((t - 2.51) / .14) * (1 - smooth((t - 2.72) / .27));
    const on = smooth((t - 2.77) / .72);
    const pivotAngle = hingeAngle(t - 2.76, LAMP_TRAVEL);
    knob.position.y = .235 - pressed * .039;
    pivot.rotation.z = .047 + pivotAngle * .41;
    pivot.rotation.x = pivotAngle;
    pivot.updateMatrixWorld(true);
    lightPlacing(housing, lamp, lampTarget, pivotAngle);
    lamp.intensity = 91 * on;
    beam.position.copy(lamp.position).lerp(lamp.target.position, .50);
    lightAxis.copy(lamp.position).sub(lamp.target.position);
    beam.scale.y = lightAxis.length();
    beam.quaternion.setFromUnitVectors(up, lightAxis.normalize());
    beam.material.uniforms.power.value = on;
    diffuser.emissiveIntensity = .028 + 2.42 * on;
    lit.emissiveIntensity = .78 * on;
    pool.material.opacity = .47 * on;
    pool.position.z = lamp.target.position.z;
    core.material.opacity = .49 * on;
    core.position.z = lamp.target.position.z;
    motes.material.opacity = .52 * on;
    motes.rotation.y = t * .065;
    motes.position.y = .023 * Math.sin(t * .77);
    if (cut.index === 0) {
      frame(cam, cut.progress, [V(-2.27, 1.46, 3.13), V(-1.86, 1.29, 2.73)], [V(-.51, .51, -.15), V(-.70, .35, .07)], [V(-.74, .48, -.58), V(-.79, .25, .16)], { mm: [63, 70], roll: [.032, .018], aperture: 18, smear: .41, bloom: .37 });
    } else if (cut.index === 1) {
      frame(cam, cut.progress, [V(1.93, 2.63, 7.14), V(1.42, 2.34, 7.44)], [V(.04, 2.05, -.02), V(.01, 2.08, -.05)], [V(.11, 2.08, -.11), V(.38, 1.41, .02)], { mm: [37, 41], roll: [.010, 0], aperture: 7, smear: .3, bloom: .98, exposure: 1.025 });
    } else {
      frame(cam, cut.progress, [V(1.15, 2.27, 7.55), V(-.62, 2.45, 7.49)], [V(.03, 2.0, -.03), V(.02, 1.96, -.13)], null, { mm: [43, 45], roll: [-.009, 0], aperture: 8, smear: .6, bloom: .89 });
    }
  } };
}

function lightPlacing(housing, lamp, target, angle) {
  lamp.position.copy(housing.getWorldPosition(V(0, 0, 0)));
  lamp.position.y -= .11;
  lamp.target.position.copy(target);
  lamp.target.position.z -= angle * 2.1;
}

function solarCells() {
  return texture(384, 224, (c, w, h) => {
    const rand = rng(370);
    const deep = c.createLinearGradient(0, 0, w, h);
    deep.addColorStop(0, '#0c1833'); deep.addColorStop(.48, '#344c76'); deep.addColorStop(1, '#142344');
    c.fillStyle = deep; c.fillRect(0, 0, w, h);
    c.strokeStyle = '#8297b973'; c.lineWidth = .55;
    for (let x = 4; x < w; x += 7) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, h); c.stroke(); }
    for (let y = 8; y < h; y += 26) { c.beginPath(); c.moveTo(0, y); c.lineTo(w, y); c.stroke(); }
    c.fillStyle = '#303b53';
    for (let x = 0; x < w; x += 64) c.fillRect(x, 0, 2.5, h);
    c.fillRect(0, h / 2, w, 2.5);
    for (let i = 0; i < 640; i++) { c.fillStyle = '#c4dbff1e'; c.fillRect(rand() * w, rand() * h, 1, .7); }
  });
}

function foilMap() {
  return texture(192, 192, (c, w, h) => {
    const rand = rng(552);
    c.fillStyle = '#ad8758'; c.fillRect(0, 0, w, h);
    for (let i = 0; i < 400; i++) {
      const x = rand() * w; const y = rand() * h; const size = 2 + rand() * 30;
      const g = c.createLinearGradient(x, y, x + size, y + size * .9);
      g.addColorStop(0, '#e6be8278'); g.addColorStop(.52, '#ab835e17'); g.addColorStop(1, '#452b1d5c');
      c.fillStyle = g; c.fillRect(x, y, size, size * .82);
    }
  });
}

async function signal(env) {
  const moonMap = await load(lunaURL);
  const scene = studio(env, { bg: ['#040811', '#111d31', '#142f5840'], sky: '#697eaa', ground: '#152132', key: '#ffebd3', keyAt: V(-2, 4, 4), rim: '#6d9ede', environment: .36, ambient: .31, keyPower: 3.45, rimPower: 2.05 });
  const stars = dust(scene, 133981, 610, [[-36, 36], [-39, 32], [-51, -11]], '#b9cdea', .057);
  stars.material.opacity = .64;
  const closeStars = dust(scene, 21, 93, [[-13, 13], [-13, 10], [-17, -8]], '#ffe1c3', .024);
  closeStars.material.opacity = .56;
  const center = V(-.42, -.28, -.29);
  const moon = mesh(scene, new THREE.SphereGeometry(1.47, 72, 48), pbr('#b4c8db', .86, .06, { map: moonMap, bumpMap: moonMap, bumpScale: .079, envMapIntensity: .20 }), ...center);
  moon.rotation.z = -.18;
  const satellite = new THREE.Group(); scene.add(satellite);
  const graphite = pbr('#212936', .33, .68);
  const titanium = pbr('#a8b5be', .28, .82, { roughnessMap: strokeMaterial() });
  const foil = foilMap();
  const wrapped = pbr('#ffd89e', .43, .67, { map: foil, bumpMap: foil, bumpScale: .018 });
  const bakedCells = solarCells();
  const cellMat = pbr('#a0bbed', .34, .53, { map: bakedCells, bumpMap: bakedCells, bumpScale: .007 });
  bevel(satellite, [.568, .658, .445], .055, wrapped);
  for (const y of [-.31, .32]) bevel(satellite, [.597, .062, .471], .019, titanium, [0, y, 0]);
  bevel(satellite, [.441, .52, .071], .017, graphite, [0, .01, .224]);
  bevel(satellite, [.369, .258, .031], .013, titanium, [0, -.047, .265]);
  for (const x of [-.184, .184]) {
    for (const y of [-.154, .106]) cylinder(satellite, .023, .023, .015, graphite, [x, y, .289]).rotation.x = PI / 2;
  }
  const lens = cylinder(satellite, .073, .073, .075, pbr('#3493bb', .21, .47), [.003, -.027, .296]);
  lens.rotation.x = PI / 2;
  ring(satellite, .079, .012, titanium, [0, -.026, .33]);
  for (const s of [-1, 1]) {
    const wing = new THREE.Group(); satellite.add(wing);
    wing.position.set(s * .246, .058, .011); wing.rotation.y = s * .09;
    bevel(wing, [.243, .074, .071], .021, titanium, [s * .137, 0, 0]);
    cylinder(wing, .052, .052, .19, graphite, [s * .213, 0, 0]).rotation.z = PI / 2;
    bevel(wing, [.802, .482, .044], .016, graphite, [s * .663, .02, 0]);
    mesh(wing, new THREE.PlaneGeometry(.747, .424), cellMat, s * .663, .02, .024);
    for (const yy of [-.22, .265]) box(wing, [.81, .02, .024], titanium, [s * .668, yy, .027]);
    for (const x of [.278, 1.053]) box(wing, [.019, .50, .024], titanium, [s * x, .022, .026]);
  }
  const antenna = new THREE.Group(); satellite.add(antenna);
  antenna.position.set(-.022, .356, -.08); antenna.rotation.set(-.33, 0, -.27);
  cylinder(antenna, .071, .103, .112, graphite, [0, .03, 0]);
  const dishProfile = [new THREE.Vector2(0, .07), ...Array.from({ length: 16 }, (_, i) => {
    const r = (i + 1) * .0215; return new THREE.Vector2(r, .07 + r ** 2 * .86);
  })];
  const dishMaterial = pbr('#c0c4c5', .37, .74, { side: THREE.DoubleSide });
  mesh(antenna, new THREE.LatheGeometry(dishProfile, 52), dishMaterial);
  ring(antenna, .345, .007, titanium, [0, .174, 0]).rotation.x = PI / 2;
  const emitter = cylinder(antenna, .016, .024, .216, graphite, [0, .188, 0]);
  mesh(emitter, new THREE.SphereGeometry(.039, 16, 12), titanium, 0, .122, 0);
  const probeLight = pbr('#fa9959', .41, .19, { emissive: '#ff7b32', emissiveIntensity: .3 });
  bevel(satellite, [.08, .024, .023], .007, probeLight, [-.15, .228, .27]);

  const beacon = center.clone().add(V(.65, .43, 1.18).normalize().multiplyScalar(1.51));
  const haloSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), color: '#ffbe73', opacity: 0, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
  haloSprite.position.copy(beacon); scene.add(haloSprite);
  const surfaceLight = new THREE.PointLight('#ffc075', 0, 1.2, 1.9);
  surfaceLight.position.copy(beacon).add(V(.039, .036, .13)); scene.add(surfaceLight);
  const rings = Array.from({ length: 4 }, () => {
    const glow = new THREE.MeshBasicMaterial({ color: '#f3af70', transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending });
    return ring(scene, .23, .012, glow, [0, 0, 0]);
  });
  const trajectory = new THREE.BufferGeometry();
  trajectory.setAttribute('position', new THREE.BufferAttribute(new Float32Array(6), 3));
  const ray = new THREE.Line(trajectory, new THREE.LineBasicMaterial({ color: '#ffc78d', transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
  ray.frustumCulled = false; scene.add(ray);
  const cam = camera();
  const inclination = .49;
  const zAxis = V(0, 0, 1);
  const aim = V(0, 0, 0);
  return { scene, cam, update(t, cut) {
    moon.rotation.y = -.35 + t * .022;
    const p = keplerPosition(t, MOON_ORBIT);
    satellite.position.set(center.x + p.x, center.y + p.z * Math.sin(inclination), center.z + p.z * Math.cos(inclination));
    satellite.rotation.set(.21 + t * -.016, -.44 + t * .038, -.08 + t * .029);
    satellite.scale.setScalar(.66);
    const sent = smooth((t - 4.14) / .27) * (1 - smooth((t - 7.15) / .33));
    const answered = smooth((t - 8.08) / .55) * (.64 + .36 * Math.sin(t * 6.5) ** 2);
    probeLight.emissiveIntensity = .21 + sent * 2.1;
    aim.copy(satellite.position).sub(beacon).normalize();
    rings.forEach((pulse, i) => {
      const q = (t - 4.3 - .46 * i) / 1.44;
      pulse.visible = q > 0 && q < 1;
      pulse.position.copy(satellite.position).lerp(beacon, clamp(q));
      pulse.quaternion.setFromUnitVectors(zAxis, aim);
      pulse.scale.setScalar(.40 + .98 * clamp(q));
      pulse.material.opacity = Math.sin(PI * clamp(q)) * .7;
    });
    trajectory.attributes.position.setXYZ(0, satellite.position.x, satellite.position.y, satellite.position.z);
    trajectory.attributes.position.setXYZ(1, beacon.x, beacon.y, beacon.z);
    trajectory.attributes.position.needsUpdate = true;
    ray.material.opacity = .34 * sent;
    haloSprite.material.opacity = answered * .95;
    haloSprite.scale.setScalar(.33 + .41 * answered);
    surfaceLight.intensity = 1.8 * answered;
    if (cut.index === 0) {
      const rig = satellite.position;
      frame(cam, cut.progress, [rig.clone().add(V(1.12, .90, 3.83)), rig.clone().add(V(.66, .55, 4.31))], [rig.clone().add(V(-.29, -.10, 0)), rig.clone().add(V(-.42, -.11, 0))], [rig, rig], { mm: [60, 56], roll: [-.035, -.012], aperture: 18, smear: .43, bloom: .54 });
    } else if (cut.index === 1) {
      frame(cam, cut.progress, [V(1.29, 1.32, 7.55), V(.96, 1.13, 8.20)], [V(.29, .10, .04), V(.20, .17, .04)], [V(.94, .57, 1.17), V(.21, .19, 1.15)], { mm: [41, 43], roll: [.036, .018], aperture: 7, smear: .5, bloom: .73 });
    } else {
      frame(cam, cut.progress, [V(-.69, 1.42, 7.4), V(-1.68, 1.60, 8.92)], [V(.01, -.05, .09), V(-.15, -.04, .01)], [beacon, V(-.26, -.14, .71)], { mm: [47, 44], roll: [.01, 0], aperture: 10, smear: .57, bloom: .84 });
    }
  } };
}

export const SCENES = { 'phone-storage': phone, 'halo-desk-lamp': halo, 'last-signal': signal };
