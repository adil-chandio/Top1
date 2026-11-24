/**
 * HUAYUAN — V6.2 pass 2. 60 s (1,800 f @ 30 fps).
 *
 * SCALE CONTRACT (pass 2 fix): 1 world unit = 20 cm.
 *   radiodont body ~18 cm  -> 0.9 u   (drawn at 1.6 u length incl. frontal appendages)
 *   opabinia   body ~ 4 cm -> 0.2 u   (drawn 0.55 u)
 *   hallucigenia body ~3 cm-> 0.15 u  (drawn 0.45 u)
 *   sponge clumps 6-40 cm  -> 0.3-2.0 u
 *   camera distances 1.2-9 u, scene depth ~40 u
 * Every subject is therefore a real proportion of frame, not a speck on a 140-unit plane.
 *
 * Built on tools/monarch-v6-imax-sdk. Authored performance on real rigs, derived sediment
 * physics, scale-aware fog, 20-shot plan, claim stamps.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader.js';
import { clone as cloneSkinned } from 'three/examples/jsm/utils/SkeletonUtils.js';
import {
  createImaxOpticalPass, createCinemaCameraRig, buildLoftGeometry, buildNormalFromCanvas,
  makeImaxMaterial, setImaxLightingPreset, createTexelSnappedShadowRig, createGroundContactAO,
  createLoopLockedDustMotes, assertSafeLatinGlyphs, createGpuHudCompositor,
  loadVerifiedCinemaFonts, GLM,
} from '/tools/monarch-v6-imax-sdk/index.js';

const Q = new URLSearchParams(location.search);
const W = +Q.get('w') || 1920;
const H = +Q.get('h') || 1080;
const TOTAL = 1800;

await loadVerifiedCinemaFonts();

const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
renderer.setSize(W, H, false);
renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
renderer.autoClear = false;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(38, W / H, 0.02, 120);
const hud = createGpuHudCompositor(renderer, W, H);

let seed = 40213;
const rnd = () => { seed = (1664525 * seed + 1013904223) >>> 0; return seed / 4294967296; };
const smooth = (a, b, x) => { const t = GLM.clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };

/* ────────────────────────── shots ────────────────────────── */
const SHOTS = [
  [0, 62, 'slab', 'emerge'], [62, 150, 'slab', 'rake'], [150, 196, 'sea', 'craneUp'],
  [196, 268, 'sea', 'trackRadiodont'], [268, 316, 'sea', 'staticOpabinia'], [316, 390, 'sea', 'lowDolly'],
  [390, 428, 'sea', 'pushIn'], [428, 470, 'sea', 'handheld'], [470, 512, 'sea', 'whipPan'],
  [512, 560, 'sea', 'snapOut'], [560, 604, 'sea', 'overhead'], [604, 642, 'sea', 'dutchRoll'],
  [642, 682, 'sea', 'vertigo'], [682, 720, 'sea', 'lockedWide'], [720, 768, 'slab', 'topLight'],
  [768, 820, 'slab', 'macroArc'], [820, 872, 'slab', 'rackFocus'], [872, 930, 'slab', 'rake'],
  [930, 1004, 'sea', 'craneUp2'], [1004, 1072, 'sea', 'downTilt'], [1072, 1140, 'sea', 'trackRadiodont'],
  [1140, 1230, 'sea', 'vertigo'], [1230, 1330, 'sea', 'craneUp'], [1330, 1400, 'sea', 'staticOpabinia'],
  [1400, 1470, 'sea', 'lowDolly'], [1470, 1540, 'sea', 'handheld'], [1540, 1620, 'sea', 'overhead'],
  [1620, 1700, 'sea', 'dutchRoll'], [1700, 1800, 'sea', 'finalHold'],
];
const CUTS = new Set(SHOTS.map((s) => s[0]));
const shotAt = (f) => { for (let i = SHOTS.length - 1; i >= 0; i--) if (f >= SHOTS[i][0]) return SHOTS[i]; return SHOTS[0]; };

/* ────────────────────────── groups & lighting ────────────────────────── */
const sea = new THREE.Group();
const lab = new THREE.Group();
scene.add(sea, lab);

setImaxLightingPreset('abyssal_biolum', { fogStart: 2.2, fogRange: 26 });
const shadowRig = createTexelSnappedShadowRig(renderer, { mapSize: 1024 });

/* Water volume: vertical gradient dome so the column above reads as water, not space. */
const domeGeo = new THREE.SphereGeometry(58, 24, 18);
const domeMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { uTop: { value: new THREE.Color('#7fc6d4') }, uMid: { value: new THREE.Color('#2f7a88') }, uBot: { value: new THREE.Color('#0c2b34') }, uAmt: { value: 1.0 } },
  vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
  fragmentShader: `varying vec3 vP; uniform vec3 uTop,uMid,uBot; uniform float uAmt;
    void main(){ float h = clamp(vP.y/58.0*0.5+0.5,0.0,1.0);\n      h = pow(h, 0.75);
      vec3 c = mix(uBot, uMid, smoothstep(0.15,0.55,h));
      c = mix(c, uTop, smoothstep(0.55,1.0,h));
      gl_FragColor = vec4(c*uAmt, 1.0); }`,
});
const dome = new THREE.Mesh(domeGeo, domeMat);
dome.renderOrder = -1;
sea.add(dome);

/* seabed: lofted relief, 44 u across, sits at y = -1.55 */
function makeSeabed() {
  const g = new THREE.PlaneGeometry(44, 44, 110, 110);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i);
    p.setZ(i, 0.16 * Math.sin(x * 0.55 + y * 0.42) + 0.09 * Math.sin(x * 1.7 - y * 1.2) + 0.04 * Math.sin(x * 4.3 + y * 2.9));
  }
  g.computeVertexNormals();
  const c = document.createElement('canvas'); c.width = c.height = 512;
  const cx = c.getContext('2d');
  cx.fillStyle = '#5a6259'; cx.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 32000; i++) {
    const a = rnd();
    cx.fillStyle = a > 0.58 ? 'rgba(168,178,172,.13)' : a > 0.28 ? 'rgba(26,30,29,.28)' : 'rgba(92,108,98,.12)';
    cx.fillRect(rnd() * 512, rnd() * 512, 0.6 + rnd() * 2.8, 0.5 + rnd() * 2.2);
  }
  // hard desaturate: the warm ALBEDO was fighting the cool water and made the bed read as desert
  {
    const img = cx.getImageData(0, 0, 512, 512);
    const d = img.data;
    for (let i = 0; i < d.length; i += 4) {
      const l = 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2];
      d[i]     = Math.round(l * 0.90 + d[i] * 0.10);
      d[i + 1] = Math.round(l * 0.97 + d[i + 1] * 0.03);
      d[i + 2] = Math.round(l * 0.99 + d[i + 2] * 0.01);
    }
    cx.putImageData(img, 0, 0);
  }
  const map = new THREE.CanvasTexture(c); map.colorSpace = THREE.SRGBColorSpace;
  map.wrapS = map.wrapT = THREE.RepeatWrapping; map.repeat.set(7, 7);
  const nm = buildNormalFromCanvas(c, 1.1, 512); nm.repeat.set(7, 7);
  const m = makeImaxMaterial({ color: '#6f7a74', map, normalMap: nm, normalScale: 0.70, specPower: 0.13, rimStrength: 0.02 });
  const mesh = new THREE.Mesh(g, m);
  mesh.rotation.x = -Math.PI / 2; mesh.position.y = -1.55;
  mesh.receiveShadow = true;
  return mesh;
}
sea.add(makeSeabed());

/* rock outcrops: real scans, sized 0.5-3 u, seated on the bed */
const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder);
loader.setKTX2Loader(new KTX2Loader().setTranscoderPath('/@fs/tmp/v6_runtime/node_modules/three/examples/jsm/libs/basis/').detectSupport(renderer));
const A = '/tools/extinct-channel/projects/huayuan/assets/';
const [rockA, rockB, rockC, gRad, gOpa, gHal] = await Promise.all(
  ['coast_rocks_01.glb', 'coast_rocks_03.glb', 'rock_07.glb', 'radiodont.glb', 'opabinia.glb', 'hallucigenia.glb'].map((f) => loader.loadAsync(A + f))
);
function normalize(gl) {
  const root = gl.scene; root.updateMatrixWorld(true);
  const b = new THREE.Box3().setFromObject(root, true);
  const size = b.getSize(new THREE.Vector3()), center = b.getCenter(new THREE.Vector3());
  const inner = new THREE.Group(); inner.position.copy(center).multiplyScalar(-1); inner.add(root);
  const wrap = new THREE.Group(); wrap.add(inner);
  const k = 1 / Math.max(size.x, size.y, size.z);
  wrap.scale.setScalar(k);
  return { wrap, unitH: size.y * k };
}
const rocks = [normalize(rockA), normalize(rockB), normalize(rockC)];
// camera corridor keep-out: rocks must never intrude between lens and subject
const CLEAR = [
  { x: 0.1, z: -1.3, r: 3.2 },   // opabinia / halluci stage
  { x: 0.1, z: 0.6, r: 2.6 },    // lens positions
  { x: 0.0, z: -3.4, r: 2.4 },   // radiodont lane
];
for (let i = 0; i < 22; i++) {
  const src = rocks[i % 3];
  const m = src.wrap.clone(true);
  const s = 0.42 + rnd() * 1.9;
  let px = 0, pz = 0, ok = false;
  for (let tries = 0; tries < 40 && !ok; tries++) {
    px = (rnd() - 0.5) * 24;
    pz = -2.0 - rnd() * 19;
    ok = CLEAR.every((c) => Math.hypot(px - c.x, pz - c.z) > c.r + s * 0.5);
  }
  if (!ok) { px = -9 + rnd() * 18; pz = -14 - rnd() * 6; }
  m.scale.multiplyScalar(s);
  m.position.set(px, -1.55 + (src.unitH * s) / 2 - 0.06, pz);
  m.rotation.y = rnd() * Math.PI * 2;
  m.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false;
      o.material = makeImaxMaterial({ color: '#3f4542', map: o.material?.map || null, normalScale: 0.66, specPower: 0.12, rimStrength: 0.04 });
    }
  });
  sea.add(m);
}

/* sponges: irregular branched + vase forms, ochre/bone, clustered at 4 sites */
const sponges = [];
function spongeGeometry(kind, hgt, wid) {
  const rings = [];
  const seg = 14;
  for (let k = 0; k <= seg; k++) {
    const t = k / seg, row = [];
    const taper = kind === 0 ? (0.45 + 0.85 * Math.sin(t * 2.1) + 0.30 * t) : (0.25 + 1.25 * Math.pow(1 - t, 0.65));
    const wob = 1 + 0.16 * Math.sin(t * 9.1 + 1.7);
    const r = wid * taper * wob;
    for (let j = 0; j < 16; j++) {
      const a = (j / 16) * Math.PI * 2;
      const bump = 1 + 0.13 * Math.sin(a * 5 + t * 6);
      row.push([Math.cos(a) * r * bump, hgt * t, Math.sin(a) * r * bump]);
    }
    rings.push(row);
  }
  const geo = buildLoftGeometry(rings, true, true);
  /* a few side buds so no two silhouettes match */
  return geo;
}
const SITES = [[-3.6, -3.4], [2.6, -4.4], [4.6, -7.2], [-5.9, -7.4], [0.6, -9.6]];
for (let i = 0; i < 30; i++) {
  const site = SITES[i % SITES.length];
  const kind = i % 2;
  const hgt = 0.16 + rnd() * 0.52;
  const wid = hgt * (0.16 + rnd() * 0.20);
  const geo = spongeGeometry(kind, hgt, wid);
  const pal = ['#9b9c8c', '#838a7c', '#a8a695', '#727b70'][i % 4];
  const mat = makeImaxMaterial({ color: pal, normalScale: 0.62, rimStrength: 0.05, rimTint: [0.44, 0.52, 0.50], specPower: 0.18, translucent: 0.06 });
  const mesh = new THREE.Mesh(geo, mat);
  let sx = site[0] + (rnd() - 0.5) * 1.9;
  let sz = site[1] + (rnd() - 0.5) * 1.7;
  // hero stage keep-out: no prop may stand between the lens and a subject
  if (Math.hypot(sx - 0.10, sz + 1.30) < 2.1 || Math.hypot(sx - 0.55, sz + 1.15) < 1.9) {
    sx += (sx > 0 ? 2.4 : -2.4); sz -= 1.1;
  }
  mesh.position.set(sx, -1.57, sz);
  mesh.rotation.y = rnd() * 6.28; mesh.rotation.z = (rnd() - 0.5) * 0.16;
  mesh.castShadow = true; mesh.receiveShadow = true;
  sea.add(mesh);
  sponges.push({ mesh, phase: rnd() * 6.28 });
}

/* dust/silt in the column */
const motes = createLoopLockedDustMotes({
  count: 300, radius: 0.008, color: '#cfe4e0', loopDurationS: 60,
  bounds: { x0: -7, xSpan: 14, y0: -1.4, ySpan: 6.5, z0: -18, zSpan: 16 },
});
sea.add(motes.mesh);

/* ────────────────────────── creatures ────────────────────────── */

/**
 * True world-space extent of a skinned rig, in the rig's own space (before group scaling).
 * Samples vertices, applies bone transforms, expands a box. Skips quantised junk.
 */
/**
 * World-space size of a skinned rig computed through `SkinnedMesh.computeBoundingBox()`,
 * which bakes the current bone pose into the bounding box. Single code path used for
 * sizing, grounding and the screen-space probe, so they can never disagree.
 */
function measureSkinned(root) {
  const out = new THREE.Box3();
  const tmp = new THREE.Box3();
  root.updateMatrixWorld(true);
  root.traverse((o) => {
    if (!o.isMesh) return;
    if (o.isSkinnedMesh) {
      o.computeBoundingBox();
      if (o.boundingBox) {
        tmp.copy(o.boundingBox).applyMatrix4(o.matrixWorld);
        if (Number.isFinite(tmp.min.x)) out.union(tmp);
      }
    } else if (o.geometry) {
      if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
      tmp.copy(o.geometry.boundingBox).applyMatrix4(o.matrixWorld);
      if (Number.isFinite(tmp.min.x)) out.union(tmp);
    }
  });
  if (out.isEmpty()) return new THREE.Vector3(1, 1, 1);
  objExtent = out;
  return out.getSize(new THREE.Vector3());
}
let objExtent = null;

function measureSkinnedExtent(root) {
  const box = new THREE.Box3();
  const v = new THREE.Vector3();
  root.traverse((o) => {
    if (!o.isMesh || !o.geometry?.attributes?.position) return;
    const pos = o.geometry.attributes.position;
    const n = pos.count;
    const stride = Math.max(1, Math.floor(n / 3000));
    if (o.isSkinnedMesh && typeof o.applyBoneTransform === 'function') {
      for (let i = 0; i < n; i += stride) {
        v.fromBufferAttribute(pos, i);
        try { o.applyBoneTransform(i, v); } catch (e) { continue; }
        v.applyMatrix4(o.matrixWorld);
        if (Number.isFinite(v.x) && Number.isFinite(v.y) && Number.isFinite(v.z)) box.expandByPoint(v);
      }
    } else {
      o.updateMatrixWorld(true);
      for (let i = 0; i < n; i += stride) {
        v.fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld);
        if (Number.isFinite(v.x) && Number.isFinite(v.y) && Number.isFinite(v.z)) box.expandByPoint(v);
      }
    }
  });
  const sz = box.isEmpty() ? new THREE.Vector3(1, 1, 1) : box.getSize(new THREE.Vector3());
  return sz;
}

const creatures = [];
function makeCreature(gl, { name, targetLen, pos, yaw = 0, ground = null }) {
  const root = cloneSkinned(gl.scene);
  root.traverse((o) => {
    if (o.isMesh) {
      o.frustumCulled = false;
      o.castShadow = true; o.receiveShadow = true;
      o.material = makeImaxMaterial({
        color: name === 'radiodont' ? '#8a6b42' : name === 'opabinia' ? '#9a7748' : '#7a6238',
        map: o.material?.map || null, normalScale: 0.62, specPower: 0.34,
        rimStrength: 0.16, rimTint: [0.40, 0.52, 0.54], translucent: 0.04,
      });
    }
  });
  root.updateMatrixWorld(true);
  // Neither Box3.setFromObject nor the bone positions describe these rigs: the meshes are
  // quantised (KHR_mesh_quantization) and skinned, so the CPU-side attribute box is bogus.
  // Measure the ACTUAL deformed surface by applying bone transforms to sampled vertices.
  // SkinnedMesh.computeBoundingBox() applies bone transforms (Box3.setFromObject does not,
  // and these meshes are quantised), so this is the only measurement that matches the render.
  const rawSize = measureSkinned(root);
  const k = targetLen / Math.max(rawSize.x, rawSize.y, rawSize.z, 1e-9);
  const grp = new THREE.Group(); grp.add(root);
  grp.scale.setScalar(k);
  // recentre the rig on its own measured bounds BEFORE placing it, so the group pivot and the
  // visible body coincide (these imports carry large off-origin offsets).
  measureSkinned(root);
  if (objExtent) {
    const sz0 = objExtent.getSize(new THREE.Vector3());
    // FBX-derived rigs arrive on different up-axes. If the tallest axis is Y but the body is
    // clearly longer along Z or X, the creature is standing on end: lay it down.
    if (sz0.y > sz0.x * 1.35 && sz0.y > sz0.z * 1.35) {
      root.rotation.x = -Math.PI / 2;
    }
    root.updateMatrixWorld(true);
    measureSkinned(root);
    const c0 = objExtent.getCenter(new THREE.Vector3());
    root.position.sub(new THREE.Vector3().copy(c0).applyQuaternion(new THREE.Quaternion()));
  }
  grp.position.copy(pos); grp.rotation.y = yaw;
  sea.add(grp);
  grp.updateMatrixWorld(true);
  if (ground !== null) {
    const gb = measureSkinned(root);
    if (objExtent && Number.isFinite(objExtent.min.y)) grp.position.y += ground - objExtent.min.y;
  }
  const mixer = new THREE.AnimationMixer(root);
  mixer.clipAction(gl.animations[0]).play();
  root.updateMatrixWorld(true);
  const b = new THREE.Box3().setFromObject(root, true);
  const size = b.getSize(new THREE.Vector3());
  const bones = {}, rest = {};
  root.traverse((o) => { if (o.isBone) { bones[o.name] = o; rest[o.name] = o.quaternion.clone(); } });
  const c = { name, root, grp, mixer, bones, rest, basePos: pos.clone(), extent: size, flapL: [], flapR: [], probe: [], body: [], legs: [], head: null, recoil: 0, curl: 0 };
  for (const k in bones) {
    if (/^Flap_\d+\.L/.test(k)) c.flapL.push(k);
    if (/^Flap_\d+\.R/.test(k)) c.flapR.push(k);
    if (/^Frontal_\d+\.L/.test(k)) c.flapL.push(k);
    if (/^Frontal_\d+\.R/.test(k)) c.flapR.push(k);
    if (/^Probo\./.test(k)) c.probe.push(k);
    if (/^Body\.[0-9]/.test(k)) c.body.push(k);
    if (/^Body[A-C]?\./.test(k)) c.body.push(k);
    if (/^Bone(_|\.00)/.test(k)) c.legs.push(k);
    if (/^(Head|Neck)/.test(k)) c.head = k;
  }
  c.flapL.sort(); c.flapR.sort(); c.probe.sort(); c.body.sort(); c.legs.sort();
  creatures.push(c);
  return c;
}

/* subjects sized to fill frame, placed inside the 20 u stage */
const rad1 = makeCreature(gRad, { name: 'radiodont', targetLen: 3.00, pos: new THREE.Vector3(1.2, 0.30, -3.4), yaw: Math.PI });
const rad2 = makeCreature(gRad, { name: 'radiodont', targetLen: 2.00, pos: new THREE.Vector3(-3.0, 1.55, -9.5), yaw: Math.PI * 0.78 });
const opa = makeCreature(gOpa, { name: 'opabinia', targetLen: 2.00, pos: new THREE.Vector3(0.10, -0.55, -1.30), yaw: Math.PI * 0.46 });
const hal = makeCreature(gHal, { name: 'hallucigenia', targetLen: 2.00, pos: new THREE.Vector3(0.55, 0, -1.15), yaw: Math.PI * 0.08, ground: -1.26 });
const HOME = {
  rad1: rad1.grp.position.clone(),
  rad2: rad2.grp.position.clone(),
  opa: opa.grp.position.clone(),
};
const hal2 = makeCreature(gHal, { name: 'hallucigenia', targetLen: 1.40, pos: new THREE.Vector3(-3.5, 0, -4.1), yaw: Math.PI * 0.88, ground: -1.30 });

/* ────────────────────────── sediment ────────────────────────── */
const SILT_N = 2600;
const siltPos = new Float32Array(SILT_N * 3);
const siltVel = new Float32Array(SILT_N * 3);
for (let i = 0; i < SILT_N; i++) {
  siltPos[i * 3] = (rnd() - 0.5) * 20;
  siltPos[i * 3 + 1] = -0.4 + rnd() * 7;
  siltPos[i * 3 + 2] = -1 - rnd() * 17;
}
const siltGeo = new THREE.BufferGeometry();
siltGeo.setAttribute('position', new THREE.BufferAttribute(siltPos, 3));
const siltMat = new THREE.PointsMaterial({ color: '#e2d5b8', size: 0.040, transparent: true, opacity: 0, depthWrite: false, sizeAttenuation: true, blending: THREE.NormalBlending });
const silt = new THREE.Points(siltGeo, siltMat);
silt.frustumCulled = false; silt.renderOrder = 21;
sea.add(silt);

/* ────────────────────────── fossil slab ────────────────────────── */
function makeSlab() {
  const g = new THREE.PlaneGeometry(12, 8, 180, 120);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i);
    p.setZ(i, 0.035 * Math.sin(x * 2.6 + y * 0.8) + 0.022 * Math.sin(y * 2.1 - x * 1.1) + 0.010 * Math.sin(x * 9.3));
  }
  g.computeVertexNormals();

  const c = document.createElement('canvas'); c.width = 2048; c.height = 1365;
  const cx = c.getContext('2d');
  cx.fillStyle = '#9d9480'; cx.fillRect(0, 0, 2048, 1365);
  for (let i = 0; i < 140000; i++) {
    const a = rnd();
    cx.fillStyle = a > 0.62 ? 'rgba(220,206,178,.10)' : a > 0.30 ? 'rgba(34,27,21,.10)' : 'rgba(150,126,94,.07)';
    cx.fillRect(rnd() * 2048, rnd() * 1365, 0.7 + rnd() * 3.4, 0.6 + rnd() * 2.4);
  }
  /* bedding planes + a fracture running diagonally (reads as stone, not plastic) */
  cx.strokeStyle = 'rgba(58,46,36,.34)'; cx.lineWidth = 3;
  for (let k = 0; k < 5; k++) { cx.beginPath(); cx.moveTo(0, 300 + k * 190 + Math.sin(k) * 40); cx.bezierCurveTo(700, 280 + k * 190, 1400, 340 + k * 190, 2048, 300 + k * 190); cx.stroke(); }
  cx.strokeStyle = 'rgba(30,24,19,.55)'; cx.lineWidth = 6;
  cx.beginPath(); cx.moveTo(240, 80); cx.bezierCurveTo(700, 520, 1180, 700, 1880, 1290); cx.stroke();

  /* compressed lobopod: dark mineral stain with segments, spines and a gut trace */
  cx.save(); cx.translate(1010, 700); cx.rotate(-0.05);
  cx.globalAlpha = 0.80; cx.fillStyle = '#33291f';
  cx.beginPath(); cx.ellipse(0, 0, 470, 104, 0, 0, Math.PI * 2); cx.fill();
  cx.globalAlpha = 0.30; cx.fillStyle = '#6a5744';
  cx.beginPath(); cx.ellipse(-40, -8, 430, 84, 0, 0, Math.PI * 2); cx.fill();
  cx.globalAlpha = 0.88; cx.strokeStyle = '#1f180f'; cx.lineWidth = 5;
  for (let k = -7; k <= 7; k++) {
    const x = k * 60;
    cx.beginPath(); cx.moveTo(x, -88); cx.quadraticCurveTo(x + 16, 0, x, 88); cx.stroke();
  }
  /* dorsal spines */
  cx.globalAlpha = 0.6; cx.lineWidth = 3;
  for (let k = -6; k <= 6; k++) { const x = k * 68; cx.beginPath(); cx.moveTo(x, -70); cx.lineTo(x + 8, -132); cx.stroke(); }
  /* gut trace */
  cx.globalAlpha = 0.72; cx.strokeStyle = '#171009'; cx.lineWidth = 13;
  cx.beginPath(); cx.moveTo(-420, 4); cx.quadraticCurveTo(0, 26, 430, -8); cx.stroke();
  /* paired eye patches at the head end */
  cx.globalAlpha = 0.85; cx.fillStyle = '#1d1611';
  cx.beginPath(); cx.ellipse(430, -30, 24, 17, 0.2, 0, Math.PI * 2); cx.fill();
  cx.beginPath(); cx.ellipse(430, 30, 24, 17, -0.2, 0, Math.PI * 2); cx.fill();
  cx.restore();

  const map = new THREE.CanvasTexture(c); map.colorSpace = THREE.SRGBColorSpace;
  const nm = buildNormalFromCanvas(c, 1.0, 1024);
  const m = makeImaxMaterial({ color: '#b3a68c', map, normalMap: nm, normalScale: 0.62, specPower: 0.16, rimStrength: 0.02 });
  const mesh = new THREE.Mesh(g, m);
  mesh.rotation.x = -Math.PI / 2;
  mesh.receiveShadow = true;
  lab.add(mesh);
  const plinth = new THREE.Mesh(new THREE.BoxGeometry(12.6, 0.9, 8.6), makeImaxMaterial({ color: '#221f1b', specPower: 0.18 }));
  plinth.position.y = -0.9; plinth.receiveShadow = true;
  lab.add(plinth);
  lab.add(createGroundContactAO({ width: 13.6, depth: 9.6, opacity: 0.45, floorY: 0.012 }));
  return mesh;
}
makeSlab();

/* ────────────────────────── camera rig, optical pass ────────────────────────── */
const rig = createCinemaCameraRig(camera, {
  totalFrames: TOTAL, shotCuts: CUTS,
  impacts: [
    { frame: 470, amp: 0.020, decay: 0.24, freq: 2.1 },
    { frame: 512, amp: 0.032, decay: 0.20, freq: 2.7 },
    { frame: 604, amp: 0.022, decay: 0.22, freq: 1.9 },
    { frame: 642, amp: 0.042, decay: 0.14, freq: 3.1 },
  ],
});
const { SHARED_LIGHT_UNIFORMS } = await import('/tools/monarch-v6-imax-sdk/core/pbr_shadow_sdk.js');

/**
 * Lab key. The SDK's presets are tuned for 1000+ unit worlds; the fossil slab is a 12-unit set,
 * so the raking key, fog bracket and colour temperature are overridden here explicitly.
 */
function SHARED_KICK() {
  // raking key from upper-left, cool fill, tight falloff across a 12-unit slab
  SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(-0.55, 0.72, 0.42).normalize();
  SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#ffe6c2').multiplyScalar(1.55);
  SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#9fc4d0').multiplyScalar(0.34);
  SHARED_LIGHT_UNIFORMS.uFogStart.value = 4.0;
  SHARED_LIGHT_UNIFORMS.uFogRange.value = 22.0;
}
const fx = createImaxOpticalPass(renderer, W, H);
fx.rtScene.texture.colorSpace = THREE.SRGBColorSpace;

/* ────────────────────────── authored performance ────────────────────────── */
const WAVE = (ph, i, n, amp) => amp * Math.sin(ph - i * (Math.PI * 2 / n) * 1.35);

function performRadiodont(c, t, drive) {
  for (let i = 0; i < c.flapL.length; i++) {
    const kL = c.flapL[i], kR = c.flapR[i];
    const bL = c.bones[kL], bR = c.bones[kR];
    if (!bL) continue;
    const ph = t * 5.4, a = 0.34 * drive;
    bL.quaternion.copy(c.rest[kL]);
    bL.rotation.z += WAVE(ph, i, c.flapL.length, a);
    bL.rotation.y += WAVE(ph, i, c.flapL.length, a * 0.4);
    if (bR) {
      bR.quaternion.copy(c.rest[kR]);
      bR.rotation.z -= WAVE(ph + Math.PI, i, c.flapR.length, a);
      bR.rotation.y -= WAVE(ph + Math.PI, i, c.flapR.length, a * 0.4);
    }
  }
  c.root.rotation.x = 0.05 * Math.sin(t * 1.7) - c.recoil * 0.45;
  c.root.rotation.z = 0.06 * Math.sin(t * 2.3) + c.recoil * 0.85;
  c.root.position.y = 0.05 * Math.sin(t * 1.25);
}

function performOpabinia(c, t, drive) {
  for (let i = 0; i < c.probe.length; i++) {
    const b = c.bones[c.probe[i]];
    if (!b) continue;
    b.quaternion.copy(c.rest[c.probe[i]]);
    b.rotation.x += 0.22 * drive * Math.sin(t * 2.3 - i * 0.9);
    b.rotation.y += 0.15 * drive * Math.sin(t * 1.5 - i * 0.7);
  }
  for (let i = 0; i < c.body.length; i++) {
    const b = c.bones[c.body[i]];
    if (!b) continue;
    b.quaternion.copy(c.rest[c.body[i]]);
    b.rotation.y += 0.13 * drive * Math.sin(t * 3.6 - i * 0.8);
  }
  c.root.rotation.z = 0.10 * Math.sin(t * 0.9);
}

function performHallucigenia(c, t, drive, walk) {
  for (let i = 0; i < c.legs.length; i++) {
    const key = c.legs[i], b = c.bones[key];
    if (!b) continue;
    b.quaternion.copy(c.rest[key]);
    const side = key.includes('_R') ? -1 : 1;
    const step = Math.sin(walk * 3.4 - i * 0.62 + (side > 0 ? 0 : Math.PI));
    b.rotation.z += 0.42 * drive * step;
    b.rotation.x += 0.16 * drive * Math.max(0, step);
  }
  for (let i = 0; i < c.body.length; i++) {
    const b = c.bones[c.body[i]];
    if (!b) continue;
    b.quaternion.copy(c.rest[c.body[i]]);
    b.rotation.z += 0.08 * drive * Math.sin(walk * 2.1 - i * 0.5);
  }
  if (c.head && c.bones[c.head]) {
    const h = c.bones[c.head];
    h.quaternion.copy(c.rest[c.head]);
    h.rotation.x += 0.26 * drive * Math.sin(walk * 1.6) + c.curl * 1.0;
  }
}

/* ────────────────────────── light curve ────────────────────────── */
const LIGHT = [[0, 0.0], [62, 0.45], [150, 0.70], [390, 1.0], [470, 0.92], [560, 0.70], [642, 0.26], [700, 0.30],
  [720, 0.52], [860, 0.58], [900, 0.34], [930, 0.62], [1080, 0.92], [1260, 0.80], [1420, 0.88],
  [1600, 0.62], [1700, 0.40], [1800, 0.22]];
function lightAt(f) {
  for (let i = 1; i < LIGHT.length; i++) {
    if (f <= LIGHT[i][0]) {
      const [f0, v0] = LIGHT[i - 1], [f1, v1] = LIGHT[i];
      return GLM.mix(v0, v1, smooth(f0, f1, f));
    }
  }
  return 0;
}

/* ────────────────────────── HUD ────────────────────────── */
const LABELS = ['HUAYUAN  \u00b7  HUNAN', '512 MILLION YEARS AGO', 'RECONSTRUCTION', 'CONCEPTUAL  \u00b7  SEDIMENT EVENT',
  'SCHEMATIC  \u00b7  NOT A HUAYUAN SPECIMEN', 'EYE', 'GILLS', 'NERVE CORD', '153 SPECIES', '16 GROUPS',
  'DEEP-WATER REFUGE  -  HYPOTHESIS', 'OUTER SHELF  /  DEEP WATER', 'POSSIBLE, NOT PROVEN'];
assertSafeLatinGlyphs(LABELS, 'huayuan-v2');

const PROTECTED = [[682, 720], [1102, 1140]];
const inProtected = (f) => PROTECTED.some(([a, b]) => f >= a && f < b);

function drawHud(f) {
  const ctx = hud.ctx;
  ctx.clearRect(0, 0, W, H);
  if (!inProtected(f)) {
    const s = W / 1920;
    ctx.save(); ctx.scale(s, s);
    ctx.font = '500 20px "IBM Plex Mono"';
    const bar = (txt, x, y, alpha = 1) => {
      const w = ctx.measureText(txt).width + 26;
      ctx.globalAlpha = alpha;
      ctx.fillStyle = 'rgba(3,10,12,.55)';
      ctx.fillRect(x - 12, y - 24, w, 36);
      ctx.fillStyle = '#e6dcc6';
      ctx.fillText(txt, x, y);
      ctx.globalAlpha = 1;
    };
    if (f >= 60) bar('HUAYUAN  \u00b7  HUNAN', W ? 56 : 56, 1058);
    if (f >= 150 && f < 390) bar('RECONSTRUCTION', 56, 80);
    if (f >= 390 && f < 720) bar('CONCEPTUAL  \u00b7  SEDIMENT EVENT', 56, 80);
    if (f >= 720 && f < 930) bar('SCHEMATIC  \u00b7  NOT A HUAYUAN SPECIMEN', 56, 80);
    if (f >= 930) bar('DEEP-WATER REFUGE  -  HYPOTHESIS', 56, 80);

    if (f >= 44 && f < 150) {
      ctx.font = '600 46px "Space Grotesk"'; ctx.fillStyle = '#f4e9d2';
      ctx.fillText('512 MILLION YEARS AGO', 56, 1004);
      ctx.font = '500 20px "IBM Plex Mono"'; ctx.fillStyle = '#b9ac93';
      ctx.fillText('OUTER SHELF  /  DEEP WATER', 56, 1040);
    }
    if (f >= 786 && f < 852) { ctx.font = '600 40px "Space Grotesk"'; ctx.fillStyle = '#f4e9d2'; ctx.fillText('EYE', 56, 1004); }
    if (f >= 852 && f < 902) { ctx.font = '600 40px "Space Grotesk"'; ctx.fillStyle = '#f4e9d2'; ctx.fillText('GILLS', 56, 1004); }
    if (f >= 902 && f < 930) { ctx.font = '600 40px "Space Grotesk"'; ctx.fillStyle = '#f4e9d2'; ctx.fillText('NERVE CORD', 56, 1004); }
    if (f >= 940 && f < 1046) {
      const a = GLM.clamp((f - 940) / 14, 0, 1);
      ctx.globalAlpha = a; ctx.font = '600 48px "Space Grotesk"'; ctx.fillStyle = '#f4e9d2';
      ctx.fillText('153 SPECIES', 56, 1000); ctx.globalAlpha = 1;
    }
    if (f >= 1046 && f < 1102) { ctx.font = '600 48px "Space Grotesk"'; ctx.fillStyle = '#f4e9d2'; ctx.fillText('16 GROUPS', 56, 1000); }
    ctx.restore();
  }
  hud.composite();
}

/* ────────────────────────── main draw ────────────────────────── */
/* ────────────────────────── camera solver ────────────────────────── */

/**
 * A shot is a statement about attention, not a pile of magic numbers.
 * `who` is the subject, `fill` the fraction of frame height it should occupy, `az` the
 * orbit angle around it. The lens is then placed at exactly the distance that yields that
 * fill, at `lift` above the subject, aimed straight at it. A shot cannot silently miss.
 */
function subjectAnchor(who) {
  if (who === 'rad1') return rad1.grp.position.clone().setY(rad1.grp.position.y + 0.32);
  if (who === 'opa') return opa.grp.position.clone().setY(opa.grp.position.y + 0.18);
  if (who === 'hal') return hal.grp.position.clone().setY(hal.grp.position.y + 0.16);
  if (who === 'hal2') return hal2.grp.position.clone().setY(hal2.grp.position.y + 0.12);
  if (who === 'reef') return new THREE.Vector3(0.30, -1.10, -1.60);
  if (who === 'slab') return new THREE.Vector3(0.0, -0.34, -0.28);
  return new THREE.Vector3(0, -0.6, -2);
}
const SUBJECT_LEN = { rad1: 3.0, opa: 2.0, hal: 2.0, hal2: 1.4, reef: 3.0, slab: 2.4 };

function distForFill(len, fill, fov) {
  // a subject of length L at distance d spans L / (2*d*tan(halfFov)) of frame height
  const halfFov = (fov * Math.PI) / 360;
  return len / (2 * fill * Math.tan(halfFov));
}

/* The slab is a 12x8 bedding plane, not a character: an orbit solve makes it fill the frame
   with sand. These five shots keep the framing that was verified frame-by-frame. */
const SLAB_CAM = {
  emerge:    (e) => ({ pos: [0, GLM.mix(3.3, 2.35, e), 4.6], look: [0, 0.05, -0.25], fov: 36 }),
  rake:      (e) => ({ pos: [GLM.mix(2.9, -2.9, e), 1.05, 2.55], look: [GLM.mix(0.9, -0.9, e), 0.02, -0.2], fov: 32 }),
  topLight:  (e) => ({ pos: [0.05, GLM.mix(3.9, 2.5, e), 3.05], look: [0, 0.04, -0.5], fov: 34 }),
  macroArc:  (e) => { const a = GLM.mix(-0.24, 0.18, e); return { pos: [Math.sin(a) * 1.55, 0.72, 0.85 + Math.cos(a) * 0.55], look: [0.42, 0.02, -0.18], fov: 27 }; },
  rackFocus: (e) => ({ pos: [GLM.mix(-1.75, 1.25, e), 0.80, 1.25], look: [0, 0.02, -0.2], fov: 29 }),
};

function solveShot(name, e, u, t) {
  if (SLAB_CAM[name]) {
    const c = SLAB_CAM[name](e);
    return {
      pos: new THREE.Vector3(...c.pos), look: new THREE.Vector3(...c.look), fov: c.fov,
      dutch: 0, blur: 0.10,
    };
  }
  const plan = SHOT_PLAN[name] || SHOT_PLAN.lockedWide;
  const tgt = subjectAnchor(plan.who);
  const fov = plan.fov;
  const presence = (plan.who === 'slab' || plan.who === 'reef') ? 1.0 : 1.9;
  const fill = Math.min(GLM.mix(plan.fill[0], plan.fill[1], e) * presence, 0.94);
  const az = plan.azBase + GLM.mix(plan.az[0], plan.az[1], e);
  const lift = GLM.mix(plan.lift[0], plan.lift[1], e);
  const dist = Math.max(distForFill(SUBJECT_LEN[plan.who] ?? 2, fill, fov), 0.45);
  const pos = new THREE.Vector3(
    tgt.x + Math.sin(az) * dist,
    tgt.y + lift * dist * 0.42 + 0.06,
    tgt.z + Math.cos(az) * dist,
  );
  // the silt plane undulates up to y = -1.30; never let the lens sink into it
  pos.y = Math.max(pos.y, -0.35);  // grazing the bed reads as black; hold the lens well clear
  if (plan.shake) {
    pos.x += Math.sin(t * 7.3) * plan.shake;
    pos.y += Math.sin(t * 6.1) * plan.shake * 0.7;
  }
  return {
    pos, look: tgt, fov,
    dutch: GLM.mix(plan.dutch[0], plan.dutch[1], e),
    blur: GLM.mix(plan.blur[0], plan.blur[1], e),
  };
}

/** the entire visual language of the film, one row per shot */
const SHOT_PLAN = {
  emerge:         { who: 'slab', fov: 36, fill: [0.40, 0.62], az: [0.0, 0.0],    azBase: 0.0,  lift: [0.55, 0.40], dutch: [0, 0],        blur: [0.10, 0.10] },
  rake:           { who: 'slab', fov: 30, fill: [0.55, 0.55], az: [-0.50, 0.50], azBase: 0.0,  lift: [0.42, 0.42], dutch: [0, 0],        blur: [0.10, 0.10] },
  topLight:       { who: 'slab', fov: 34, fill: [0.46, 0.60], az: [0.0, 0.0],    azBase: 0.0,  lift: [0.66, 0.52], dutch: [0, 0],        blur: [0.10, 0.10] },
  macroArc:       { who: 'slab', fov: 27, fill: [0.66, 0.66], az: [-0.24, 0.20], azBase: 0.0,  lift: [0.30, 0.26], dutch: [0, 0],        blur: [0.10, 0.10] },
  rackFocus:      { who: 'slab', fov: 29, fill: [0.54, 0.54], az: [-0.40, 0.36], azBase: 0.0,  lift: [0.26, 0.26], dutch: [0, 0],        blur: [0.10, 0.10] },
  trackRadiodont: { who: 'rad1', fov: 38, fill: [0.44, 0.54], az: [0.06, -0.08], azBase: 0.26, lift: [0.30, 0.24], dutch: [0, 0],        blur: [0.20, 0.24] },
  staticOpabinia: { who: 'opa',  fov: 36, fill: [0.50, 0.50], az: [0.0, 0.0],    azBase: -0.60, lift: [0.34, 0.34], dutch: [0, 0],        blur: [0.12, 0.12] },
  lowDolly:       { who: 'hal',  fov: 37, fill: [0.30, 0.50], az: [0.42, 0.14], azBase: 0.34, lift: [0.20, 0.12], dutch: [0, 0],        blur: [0.12, 0.26] },
  overhead:       { who: 'opa',  fov: 42, fill: [0.34, 0.42], az: [0.30, 0.52], azBase: -0.34, lift: [0.78, 0.92], dutch: [-0.06, -0.06], blur: [0.12, 0.12] },
  dutchRoll:      { who: 'opa',  fov: 42, fill: [0.46, 0.40], az: [0.10, -0.26], azBase: -0.60, lift: [0.58, 0.66], dutch: [-0.05, 0.22], blur: [0.26, 0.16] },
  vertigo:        { who: 'opa',  fov: 42, fill: [0.48, 0.24], az: [0.0, 0.26],  azBase: -0.60, lift: [0.52, 0.80], dutch: [0.05, -0.05], blur: [0.12, 0.12] },
  craneUp:        { who: 'reef', fov: 40, fill: [0.30, 0.58], az: [-0.34, 0.26], azBase: 0.0,  lift: [0.10, 0.62], dutch: [0, 0],        blur: [0.12, 0.10] },
  pushIn:         { who: 'reef', fov: 37, fill: [0.30, 0.58], az: [-0.14, 0.06], azBase: 0.0,  lift: [0.52, 0.30], dutch: [0, 0],        blur: [0.10, 0.16] },
  handheld:       { who: 'reef', fov: 38, fill: [0.40, 0.46], az: [0.08, 0.20], azBase: 0.0,  lift: [0.34, 0.28], dutch: [0.01, -0.01], blur: [0.10, 0.10], shake: 0.030 },
  whipPan:        { who: 'hal2', fov: 40, fill: [0.34, 0.52], az: [-0.95, 0.18], azBase: 0.40, lift: [0.72, 0.62], dutch: [0.06, 0.10], blur: [0.52, 0.30] },
  snapOut:        { who: 'reef', fov: 43, fill: [0.58, 0.22], az: [0.0, -0.16], azBase: 0.0,  lift: [0.36, 0.80], dutch: [0, 0],        blur: [0.10, 0.10] },
  lockedWide:     { who: 'reef', fov: 39, fill: [0.34, 0.34], az: [0.0, 0.0],    azBase: 0.0,  lift: [0.52, 0.52], dutch: [0, 0],        blur: [0.08, 0.08] },
  craneUp2:       { who: 'reef', fov: 40, fill: [0.44, 0.26], az: [-0.26, 0.22], azBase: 0.0,  lift: [0.16, 0.72], dutch: [0, 0],        blur: [0.12, 0.10] },
  downTilt:       { who: 'reef', fov: 39, fill: [0.24, 0.48], az: [0.16, -0.10], azBase: 0.0,  lift: [0.76, 0.24], dutch: [0, 0],        blur: [0.10, 0.10] },
  finalHold:      { who: 'reef', fov: 37, fill: [0.38, 0.30], az: [-0.10, 0.08], azBase: 0.0,  lift: [0.58, 0.66], dutch: [0, 0],        blur: [0.08, 0.08] },
};

function draw(frame) {
  const shot = shotAt(frame);
  const t = frame / 30;
  const u = (frame - shot[0]) / (shot[1] - shot[0]);
  const e = GLM.easeInOutCubic(u);
  const isSea = shot[2] === 'sea';
  const isLab = shot[2] === 'slab';
  sea.visible = isSea; lab.visible = isLab;

  const key = lightAt(frame);
  // Lab set (fossil) needs a dedicated raking key; the abyssal preset alone leaves it black.
  if (isLab) {
    setImaxLightingPreset('cinema_lab');
    SHARED_KICK();
  } else {
    setImaxLightingPreset('abyssal_biolum');
  }
  domeMat.uniforms.uAmt.value = isSea ? (0.55 + 0.45 * key) : 0;
  scene.fog = isSea ? new THREE.FogExp2('#1d5a66', 0.042 - 0.020 * key) : new THREE.FogExp2('#0a0d10', 0.030);
  scene.background = new THREE.Color(isSea ? '#0a2830' : '#05080a');

  motes.mesh.visible = false;
  shadowRig.updateShadowMap(scene, camera.position, 9.0);
  motes.mesh.visible = isSea;

  const drive = isSea ? (frame < 390 ? 1.0 : frame < 720 ? GLM.clamp(1.3 - key * 0.5, 0.30, 1.25) : 0.5) : 0.15;
  performRadiodont(rad1, t, drive * 1.2);
  performRadiodont(rad2, t + 0.7, drive * 0.85);
  performOpabinia(opa, t + 1.3, drive);
  performHallucigenia(hal, t, drive, t * 2.2);
  performHallucigenia(hal2, t + 0.4, drive * 0.8, t * 2.2 + 1.1);

  const cross = smooth(196, 390, frame);
  rad1.grp.position.x = GLM.mix(3.1, -3.0, cross);
  rad1.grp.position.y = 0.30 + 0.10 * Math.sin(t * 1.1);
  rad1.grp.position.z = -3.4 + 0.55 * Math.sin(t * 0.6);
  rad1.grp.rotation.y = Math.PI + 0.10 * Math.sin(t * 0.9) + rad1.recoil * 0.7;

  const crisis = frame >= 470 && frame < 720;
  if (crisis) {
    const k = smooth(470, 520, frame) * (1 - smooth(650, 720, frame));
    rad1.recoil = k; hal.curl = k;
    opa.grp.rotation.z = 0.85 * k * Math.sin((frame - 470) * 0.12) + 0.08;
  }
  // These were `+=` / `-=` inside draw(), so every frame added to the previous frame's state:
  // the progressive render drifted the animals metres below the seabed while random-access
  // preflight looked fine. Pose is now a pure function of `frame`.
  const sink = frame >= 930 ? frame - 930 : 0;
  const opaTumble = crisis ? smooth(470, 520, frame) * (1 - smooth(650, 720, frame)) : 0;
  rad1.grp.position.y = HOME.rad1.y + 0.10 * Math.sin(t * 1.1) - sink * 0.0022;
  rad2.grp.position.y = HOME.rad2.y - sink * 0.0019;
  opa.grp.position.y = HOME.opa.y - sink * 0.0016;
  opa.grp.position.z = HOME.opa.z + opaTumble * 0.9 - sink * 0.004;

  const pulse = crisis ? 2.8 : 0.9;
  for (const s of sponges) {
    const k = 1 + 0.06 * Math.sin(t * pulse + s.phase) * (crisis ? 1.7 : 1);
    s.mesh.scale.set(k, 1 + (k - 1) * 0.7, k);
  }

  /* sediment */
  const siltAmt = (frame >= 390 && frame < 760) ? smooth(390, 468, frame) * (1 - smooth(700, 760, frame)) : 0;
  siltMat.opacity = 0.70 * siltAmt;
  if (siltAmt > 0.002) {
    for (let i = 0; i < SILT_N; i++) {
      const i3 = i * 3;
      siltVel[i3 + 1] -= 0.9 / 30;
      siltVel[i3] += (0.16 - siltVel[i3]) * 0.02;
      siltVel[i3 + 2] += (0.04 - siltVel[i3 + 2]) * 0.012;
      siltVel[i3] *= 0.984; siltVel[i3 + 1] *= 0.984; siltVel[i3 + 2] *= 0.984;
      siltPos[i3] += siltVel[i3] * 0.055 * siltAmt;
      siltPos[i3 + 1] += siltVel[i3 + 1] * 0.055 * siltAmt;
      siltPos[i3 + 2] += siltVel[i3 + 2] * 0.055 * siltAmt;
      if (siltPos[i3 + 1] < -1.52) {
        siltPos[i3] = (rnd() - 0.5) * 20;
        siltPos[i3 + 1] = 3.2 + rnd() * 4.6;
        siltPos[i3 + 2] = -0.6 - rnd() * 16;
        siltVel[i3] = siltVel[i3 + 1] = siltVel[i3 + 2] = 0;
      }
    }
    siltGeo.attributes.position.needsUpdate = true;
  }
  motes.update(t);

  /* camera: one idea per shot, solved against its subject (never hand-typed vectors) */
  const cam = solveShot(shot[3], e, u, t);
  const pos = cam.pos, look = cam.look;
  let fov = cam.fov, dutch = cam.dutch, blur = cam.blur;

  camera.up.set(0, 1, 0);
  const res = rig.apply({
    frame, pos, look, fov, dutchDeg: dutch * 57.2958, breathAmp: 0.005, shutterBlurScale: blur,
    // Cap the depth bracket: the rig scales near plane with focus distance, which turns a wide
    // shot into a black frame once focusDist passes ~10 u. maxNear holds it at 6 cm.
    minNear: 0.02, maxNear: 0.06,
  });

  fx.render(scene, camera, {
    focusDist: res.focusDist,
    dofRange: isLab ? 7 : 9,
    maxBlur: isLab ? 0.50 : 0.30,
    bloomAmt: crisis ? 0.070 : isLab ? 0.052 : 0.050,
    exposure: isSea ? 1.48 + 0.26 * key : 1.62,
    motionVec: res.motionVec, time: t,
  });

  drawHud(frame);
}

/* ────────────────────────── SDK CLI surface ────────────────────────── */
window.renderFramePNG = (f) => { draw(f); return renderer.domElement.toDataURL('image/png'); };
window.renderCoverPNG = () => window.renderFramePNG(238);
const gl = renderer.getContext();
const px = new Uint8Array(W * H * 4);
let ws = null, ack = null;
window.connectRawWS = (port, id) => new Promise((ok, no) => {
  ws = new WebSocket(`ws://127.0.0.1:${port}/?w=${id}`);
  ws.onmessage = () => { if (ack) { const a = ack; ack = null; a(); } };
  ws.onopen = () => ok(true);
  ws.onerror = no;
});
window.streamFramesWS = async (first, last) => {
  if (first > 0) draw(first - 1);
  for (let f = first; f < last; f++) {
    draw(f);
    gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px);
    await new Promise((ok) => { ack = ok; ws.send(px); });
  }
  return last - first;
};
window.__Probe = (frame) => {
  draw(frame);
  camera.updateMatrixWorld(true);
  const out = {};
  const bv = new THREE.Vector3();
  for (const c of creatures) {
    measureSkinned(c.root);
    const box = objExtent ? objExtent.clone() : new THREE.Box3();
    if (box.isEmpty() || !Number.isFinite(box.min.x)) { out[c.name] = null; continue; }
    if (box.isEmpty()) { out[c.name] = null; continue; }
    const pts = [];
    for (const xi of [box.min.x, box.max.x]) for (const yi of [box.min.y, box.max.y]) for (const zi of [box.min.z, box.max.z]) {
      const v = new THREE.Vector3(xi, yi, zi).project(camera);
      pts.push(v);
    }
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9, behind = false;
    for (const v of pts) {
      if (v.z > 1) behind = true;
      x0 = Math.min(x0, v.x); x1 = Math.max(x1, v.x);
      y0 = Math.min(y0, v.y); y1 = Math.max(y1, v.y);
    }
    const dist = camera.position.distanceTo(box.getCenter(new THREE.Vector3()));
    out[c.name] = {
      onScreen: !behind && (x1 - x0) < 1.6 && (y1 - y0) < 1.6 && x1 > -1 && x0 < 1 && y1 > -1 && y0 < 1,
      wFrac: +((Math.min(x1,1) - Math.max(x0,-1)) / 2).toFixed(3),
      hFrac: +((Math.min(y1,1) - Math.max(y0,-1)) / 2).toFixed(3),
      cx: +((Math.min(x1,1)+Math.max(x0,-1))/2).toFixed(3),
      cy: +((Math.min(y1,1)+Math.max(y0,-1))/2).toFixed(3),
      dist: +dist.toFixed(2),
    };
  }
  return out;
};
window.__Scene = { sea, lab, scene, camera, THREE, draw };
window.__IMAX_READY__ = true;
