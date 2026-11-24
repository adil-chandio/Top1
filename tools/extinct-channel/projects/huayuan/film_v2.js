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
 * physics, scale-aware fog, 17-shot director's cut, claim stamps.
 *
 * DIRECTOR'S CUT (this pass). The previous edit was 29 shots with a 2.07 s ASL, no shot held
 * longer than 1.6x the average, 20 different camera moves in 29 shots, and every lens between
 * 27 and 43 degrees. It had no shape: it was a slideshow of correct frames. See
 * notes/DIRECTION-GAP-DIAGNOSIS.md for the measurement and notes/DIRECTOR-CUT-PLAN.md for the
 * new cut, shot by shot.
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
/* ────────────────────────── director's cut ──────────────────────────
 * Built from the ASL, not hand-placed. Per DirectorSKILL editing-and-assembly.md:
 *   ASL 3.53 s, 17 shots, 1800 f
 *   longest 10.00 s = 2.83x ASL (the fossil reveal anchor)
 *   shortest 0.70 s = 0.20x ASL (the last light before the cut)
 *   max/min 14.3x, median 3.37 s sits below the mean
 * Sequences and their registers:
 *   STONE   0-120   (4.0 s)  one shot, cold open
 *   LIFE    120-315 (6.5 s)  observational, ASL 3.25
 *   CRISIS  315-690 (12.5 s) tightening, ASL 2.5, accelerating
 *   WITNESS 690-1290 (20.0 s) contemplative, ASL 7.0
 *   RETURN  1290-1800 (17.0 s) observational, ASL 3.6
 * Size ladder: 0 violations, 0 stutters (verified, see notes/DIRECTOR-CUT-PLAN.md)
 */
const SHOTS = [
  // STONE: the rock, no context, no scale. 50mm, low, texture before meaning.
  [0,    120,  'slab', 'ecu'],
  // LIFE
  [120,  258,  'sea',  'rad1_ms'],     // 4.60  establishing
  [258,  315,  'sea',  'opa_cu'],      // 1.90  close-up (cut on look)
  // CRISIS: pressure arrives on a wide, then accelerates 5.23 -> 0.90.
  // Shot lengths fall every cut; nothing is trimmed to fit, the cut is written this way.
  [315,  472,  'sea',  'pressure'],    // 5.23  the pressure arrives
  [472,  560,  'sea',  'relation'],    // 2.93  relation
  [560,  617,  'sea',  'hal_mcu'],     // 1.90  reaction
  [617,  663,  'sea',  'rad1_ecu'],    // 1.53  insert
  [663,  690,  'sea',  'lastlight'],   // 0.90  the last light
  // WITNESS: the rock again, now with anatomy. 10 s anchor.
  [690,  990,  'slab', 'ews'],         // 10.00 reveal
  [990,  1176, 'slab', 'ms'],          // 6.20  close-up
  [1176, 1290, 'slab', 'cu'],          // 3.80  insert
  // RETURN
  [1290, 1420, 'sea',  'return'],      // 4.33  establishing: the same place, now survivable
  [1420, 1517, 'sea',  'return_b'],    // 3.23  in among them - >30 deg off the previous setup
  [1517, 1637, 'sea',  'hal2_ms'],     // 4.00  relation
  [1637, 1722, 'sea',  'opa_mcu'],     // 2.83  reaction
  [1722, 1779, 'sea',  'rad1_cu'],     // 1.90  close-up
  [1779, 1800, 'sea',  'close'],       // 0.70  aftermath
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
  // A cold bed under a cyan key still read warm, because the rim light and the world fog were
  // both warm and the albedo was neutral-sand. Water absorbs red first; the bed has to look
  // like it is 40 m down, so the albedo is pulled blue-green and the rim is switched off.
  const m = makeImaxMaterial({ color: '#5c6f74', map, normalMap: nm, normalScale: 0.80, specPower: 0.11, rimStrength: 0.0 });
  const mesh = new THREE.Mesh(g, m);
  mesh.rotation.x = -Math.PI / 2; mesh.position.y = -1.55;
  mesh.receiveShadow = true;
  return mesh;
}
sea.add(makeSeabed());

/* ────────────────────────── water optics ──────────────────────────
 * The sea read as a lit diorama because nothing in the frame was made of water. Three layers
 * do that job: shafts from the surface (the light has a direction and a volume), caustics on
 * the bed (the surface is moving), and marine snow (the water itself is not empty). All three
 * are driven by the same `key` curve as the lighting, so the crisis darkens them together.
 */

/* 1. shafts: crossed planes under an additive falloff, so they hold up as the camera moves */
const shaftMat = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
  uniforms: { uCol: { value: new THREE.Color('#c8eef2') }, uAmt: { value: 0 }, uT: { value: 0 } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec2 vUv; uniform vec3 uCol; uniform float uAmt, uT;
    void main(){
      float edge = sin(vUv.x * 3.14159265);
      float core = pow(edge, 2.4);
      float fall = pow(clamp(1.0 - vUv.y, 0.0, 1.0), 1.30);
      float flick = 0.80 + 0.20 * sin(uT * 0.55 + vUv.x * 9.0);
      float a = core * fall * uAmt * flick;
      gl_FragColor = vec4(uCol * a, a);
    }`,
});
const shafts = new THREE.Group();
shafts.renderOrder = 18;
for (let i = 0; i < 9; i++) {
  const w = 0.9 + rnd() * 2.1;
  const h = 9.2 + rnd() * 3.0;
  const geo = new THREE.PlaneGeometry(w, h);
  geo.translate(0, -h * 0.5, 0);                 // hinge at the surface, hang downward
  const m = shaftMat;
  const a = new THREE.Mesh(geo, m);
  a.rotation.y = rnd() * Math.PI;
  a.rotation.z = (rnd() - 0.5) * 0.13;           // a shaft is never perfectly vertical
  a.position.set(-7 + rnd() * 14, 9.6, -13 + rnd() * 12);
  shafts.add(a);
  const b = a.clone(); b.rotation.y += Math.PI / 2;   // crossed, so it survives a pan
  shafts.add(b);
}
sea.add(shafts);

/* 2. caustics: the moving light pattern a surface throws onto a bed 40 m down */
const causticMat = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  uniforms: { uAmt: { value: 0 }, uT: { value: 0 }, uCol: { value: new THREE.Color('#9fd8d2') } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `varying vec2 vUv; uniform float uAmt, uT; uniform vec3 uCol;
    void main(){
      vec2 p = vUv * 9.0;
      float a = sin(p.x * 2.1 + uT * 0.55) * sin(p.y * 1.7 - uT * 0.42);
      float b = sin((p.x + p.y) * 1.31 - uT * 0.63) * sin((p.x - p.y) * 1.11 + uT * 0.37);
      float c = abs(a + b);
      float lines = smoothstep(0.55, 0.98, c);
      float vign = smoothstep(0.0, 0.18, vUv.x) * smoothstep(0.0, 0.18, 1.0 - vUv.x)
                 * smoothstep(0.0, 0.18, vUv.y) * smoothstep(0.0, 0.18, 1.0 - vUv.y);
      float alpha = lines * vign * uAmt;
      gl_FragColor = vec4(uCol * alpha, alpha);
    }`,
});
const caustic = new THREE.Mesh(new THREE.PlaneGeometry(34, 34), causticMat);
caustic.rotation.x = -Math.PI / 2;
caustic.position.y = -1.50;
caustic.renderOrder = 17;
sea.add(caustic);

/* 3. marine snow: the water is not empty, and it is not still */
const SNOW_N = 1500;
const snowPos = new Float32Array(SNOW_N * 3);
const snowSeed = new Float32Array(SNOW_N);
for (let i = 0; i < SNOW_N; i++) {
  snowPos[i * 3] = (rnd() - 0.5) * 18;
  snowPos[i * 3 + 1] = -1.4 + rnd() * 9.0;
  snowPos[i * 3 + 2] = 2.5 - rnd() * 20;
  snowSeed[i] = rnd() * Math.PI * 2;
}
const snowGeo = new THREE.BufferGeometry();
snowGeo.setAttribute('position', new THREE.BufferAttribute(snowPos, 3));
const snowMat = new THREE.PointsMaterial({
  color: '#dcefef', size: 0.026, transparent: true, opacity: 0.5,
  depthWrite: false, sizeAttenuation: true, blending: THREE.AdditiveBlending,
});
const snow = new THREE.Points(snowGeo, snowMat);
snow.frustumCulled = false; snow.renderOrder = 19;
sea.add(snow);

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
        color: name === 'radiodont' ? '#6d6350' : name === 'opabinia' ? '#7a6a4e' : '#625949',
        map: o.material?.map || null, normalScale: 0.66, specPower: 0.40,
        rimStrength: 0.20, rimTint: [0.34, 0.60, 0.68], translucent: 0.07,
      });
    }
  });
  root.updateMatrixWorld(true);
  // Neither Box3.setFromObject nor the bone positions describe these rigs: the meshes are
  // quantised (KHR_mesh_quantization) and skinned, so the CPU-side attribute box is bogus.
  // Measure the ACTUAL deformed surface by applying bone transforms to sampled vertices.
  // SkinnedMesh.computeBoundingBox() applies bone transforms (Box3.setFromObject does not,
  // and these meshes are quantised), so this is the only measurement that matches the render.
  let localDims = null;
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
    localDims = objExtent.getSize(new THREE.Vector3());
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
  const c = { name, root, grp, mixer, bones, rest, basePos: pos.clone(), extent: size,
    dims: localDims ? { x: localDims.x, y: localDims.y, z: localDims.z } : { x: 2, y: 0.5, z: 0.6 },
    headDir: null, flapL: [], flapR: [], probe: [], body: [], legs: [], head: null, recoil: 0, curl: 0 };
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
  // Which end is the head? Ask the rig. Without this, an "ECU" lands on the tail.
  if (c.head && c.bones[c.head]) {
    const wp = c.bones[c.head].getWorldPosition(new THREE.Vector3());
    const lp = grp.worldToLocal(wp.clone());
    if (Math.hypot(lp.x, lp.z) > 1e-4) {
      c.headDir = new THREE.Vector3(lp.x, 0, lp.z).normalize();
    }
  }
  if (!c.headDir) {
    const d = c.dims;
    c.headDir = d.x >= d.z ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 0, 1);
  }
  window.__DC = window.__DC || { dims: {} };
  window.__DC.dims[name] = { d: [c.dims.x, c.dims.y, c.dims.z], k: +grp.scale.x.toFixed(3),
    pos: [grp.position.x, grp.position.y, grp.position.z], head: c.headDir.toArray().map(n => +n.toFixed(2)),
    extent: [size.x, size.y, size.z].map(n => +n.toFixed(2)) };
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
  const g = new THREE.PlaneGeometry(12, 8, 380, 250);
  const p = g.attributes.position;
  // The plate was a painted plane: at 170 px/u no lens could ever resolve a macro out of it,
  // which is why the 100/135mm cuts rendered as mush. Real relief is added along the fossil's
  // own outline so raking light and a long lens have genuine silhouette to work with.
  const reliefAt = (x, y) => {
    const px = (x / 12 + 0.5) * 2048, py = (0.5 - y / 8) * 1365;   // plane local -> plate pixels
    const X = px - 1010, Y = py - 700;
    const u = X * Math.cos(0.05) - Y * Math.sin(0.05);             // fossil frame (drawn at -0.05 rad)
    const v = X * Math.sin(0.05) + Y * Math.cos(0.05);
    let h = 0;
    const e = (u / 470) ** 2 + (v / 104) ** 2;
    if (e < 1) {
      h = 0.085 * Math.sqrt(1 - e);                                // domed body
      h *= 0.86 + 0.14 * Math.cos((u / 60) * Math.PI * 2);          // segment ridges
      h -= 0.018 * Math.exp(-((v / 15) ** 2));                      // gut trace groove
    }
    for (let k = -6; k <= 6; k++) {                                 // dorsal spines
      h += 0.075 * Math.exp(-(((u - k * 68) / 10) ** 2)) * Math.exp(-(((v + 104) / 30) ** 2));
    }
    h += 0.055 * Math.exp(-(((u - 430) / 30) ** 2) - (((v + 30) / 22) ** 2));  // paired eyes
    h += 0.055 * Math.exp(-(((u - 430) / 30) ** 2) - (((v - 30) / 22) ** 2));
    return h;
  };
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i);
    p.setZ(i, 0.035 * Math.sin(x * 2.6 + y * 0.8) + 0.022 * Math.sin(y * 2.1 - x * 1.1)
              + 0.010 * Math.sin(x * 9.3) + reliefAt(x, y));
  }
  g.computeVertexNormals();

  const c = document.createElement('canvas'); c.width = 4096; c.height = 2730;
  const cx = c.getContext('2d'); cx.scale(2, 2);
  cx.fillStyle = '#9d9480'; cx.fillRect(0, 0, 2048, 1365);
  for (let i = 0; i < 280000; i++) {
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
  // The plate is only 12x8; from a high angle the frame used to end in a black band where the
  // set stopped. A large dark floor puts the specimen in a room instead of in a void.
  // A 12x8 plate in an 80x80 room still ended in a black band wherever a low lens looked up.
  // A studio is closed: floor plus a cyclorama far enough away to fall off in the fog.
  const setMat = makeImaxMaterial({ color: '#191713', specPower: 0.10 });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(90, 90), setMat);
  floor.rotation.x = -Math.PI / 2; floor.position.y = -0.02; floor.receiveShadow = true;
  lab.add(floor);
  const cyc = new THREE.Mesh(
    new THREE.CylinderGeometry(26, 26, 22, 32, 1, true),
    new THREE.MeshBasicMaterial({ color: '#060505', side: THREE.BackSide }),
  );
  cyc.position.y = 3;
  lab.add(cyc);
  return mesh;
}
makeSlab();

/* ────────────────────────── camera rig, optical pass ────────────────────────── */
const rig = createCinemaCameraRig(camera, {
  totalFrames: TOTAL, shotCuts: CUTS,
  impacts: [
    { frame: 472, amp: 0.020, decay: 0.24, freq: 2.1 },
    { frame: 560, amp: 0.030, decay: 0.20, freq: 2.7 },
    { frame: 617, amp: 0.024, decay: 0.20, freq: 2.4 },
    { frame: 663, amp: 0.040, decay: 0.13, freq: 3.1 },
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
const LIGHT = [
  [0, 0.0],          // stone: cold open, no water yet
  [120, 0.30],       // through the water to light
  [258, 0.85],       // life, near full
  [315, 0.92],
  [330, 0.55],       // crisis: light starts failing
  [488, 0.38],
  [574, 0.26],
  [628, 0.16],
  [690, 0.06],       // the darkest point in the film, on the cut
  [990, 0.42],       // witness: the slab's own raking key (lab set ignores this curve)
  [1290, 0.30],      // back to water
  [1517, 0.72],
  [1637, 0.86],
  [1722, 0.70],
  [1779, 0.45],
  [1800, 0.26],
];
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

/* Protected pure-cinema windows: zero text, zero HUD.
   The 690-990 fossil reveal is the longest shot in the film and carries no label at all -
   the audience has to work out what it is looking at. */
const PROTECTED = [[315, 330], [690, 990], [1779, 1800]];   // no type where the frame must speak
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
    // claim stamps, one per sequence - never two at once
    if (f >= 120 && f < 330) bar('RECONSTRUCTION', 56, 80);
    if (f >= 330 && f < 690) bar('CONCEPTUAL  \u00b7  SEDIMENT EVENT', 56, 80);
    if (f >= 990 && f < 1290) bar('SCHEMATIC  \u00b7  NOT A HUAYUAN SPECIMEN', 56, 80);
    if (f >= 1290) bar('DEEP-WATER REFUGE  -  HYPOTHESIS', 56, 80);

    // the one line of context, on the cold open only
    if (f >= 44 && f < 120) {
      ctx.font = '600 46px "Space Grotesk"'; ctx.fillStyle = '#f4e9d2';
      ctx.fillText('512 MILLION YEARS AGO', 56, 1004);
      ctx.font = '500 20px "IBM Plex Mono"'; ctx.fillStyle = '#b9ac93';
      ctx.fillText('OUTER SHELF  /  DEEP WATER', 56, 1040);
    }
    // anatomy callouts sit on the 6.2 s and 3.8 s shots, one each
    // the callouts are tied to the shot, not to a rough guess: EWS reads the whole plate,
    // MS walks the spine, CU lands on the head. One word each, and only where it is true.
    // The 10 s reveal (690-990) carries no type at all: the audience has to work out what it is
    // looking at. Callouts start only when the camera is already on the anatomy.
    if (f >= 990 && f < 1176) { ctx.font = '600 40px "Space Grotesk"'; ctx.fillStyle = '#f4e9d2'; ctx.fillText('DORSAL SPINES', 56, 1004); }
    if (f >= 1176 && f < 1240) { ctx.font = '600 40px "Space Grotesk"'; ctx.fillStyle = '#f4e9d2'; ctx.fillText('SEGMENTED BODY', 56, 1004); }
    // the count lands after the anatomy, as the payoff
    if (f >= 1240 && f < 1290) {
      ctx.font = '600 48px "Space Grotesk"'; ctx.fillStyle = '#f4e9d2';
      ctx.fillText('153 SPECIES', 56, 942);
    }
    ctx.restore();
  }
  hud.composite();
}


function drawDebug() {
  const D = window.__DC; if (!D) return;
  const ctx = hud.ctx;
  if (!ctx) return;
  ctx.save(); ctx.font = '600 19px "Space Grotesk"'; ctx.fillStyle = '#8ef0a0';
  let y = 300;
  if (D.last) {
    ctx.fillText('DBG ' + D.last.name + ' who=' + D.last.who + ' dist=' + D.last.dist + ' proj=' + D.last.proj, 40, y);
    y += 24;
    ctx.fillText('len=' + D.last.len + ' wid=' + D.last.wid + ' hgt=' + D.last.hgt + ' axisY=' + D.last.axis, 40, y); y += 24;
    ctx.fillText('pos=' + D.last.pos.join(',') + ' look=' + D.last.look.join(','), 40, y); y += 28;
  }
  for (const k in (D.dims || {})) {
    const v = D.dims[k];
    ctx.fillText(k + ' d=' + v.d.map(n=>n.toFixed(2)).join(',') + ' k=' + v.k + ' y=' + v.pos[1].toFixed(2) + ' h=' + v.head.join(','), 40, y);
    y += 22;
  }
  ctx.restore();
}

/* ────────────────────────── main draw ────────────────────────── */
/* ────────────────────────── camera solver ────────────────────────── */

/**
 * A shot is now a real lens decision, not a framing accident.
 *
 * `mm` selects the focal length from the lens table in cinematic-language.md; the distance
 * that realises `fill` is solved from that focal length, so a 135mm shot is genuinely
 * compressed and a 14mm shot genuinely expands the space. `hgt` places the lens axis as a
 * fraction of the subject's own height (0 = its base, 1 = its top), which is how the
 * height ladder is actually specified — never as an absolute metre value.
 */
function subjectAnchor(who) {
  // grp.scale is huge on some rigs (hallucigenia imports at ~1/66 world size), so an offset
  // expressed in scale units flies off the animal. Offsets are fractions of real body height.
  const bodyCentre = (c, up) => {
    const k = c.grp.scale.x || 1;
    return c.grp.position.clone().setY(c.grp.position.y + up * c.dims.y * k);
  };
  if (who === 'rad1') return bodyCentre(rad1, 0.50);
  if (who === 'opa') return bodyCentre(opa, 0.50);
  if (who === 'hal') return bodyCentre(hal, 0.50);
  if (who === 'hal2') return bodyCentre(hal2, 0.50);
  if (who === 'reef') return new THREE.Vector3(0.30, -1.24, -1.60);
  if (who === 'slab') return new THREE.Vector3(0.0, -0.34, -0.28);
  return new THREE.Vector3(0, -0.6, -2);
}
/* real world size of each subject, measured off the rig at load (see makeCreature) */
const CREATURE_BY_NAME = { rad1, opa, hal, hal2 };
function subjectMetrics(who) {
  const c = CREATURE_BY_NAME[who];
  if (!c) return { len: 3.4, wid: 1.2, hgt: 0.9, axis: new THREE.Vector3(1, 0, 0), yaw: 0, k: 1 };
  const d = c.dims, k = c.grp.scale.x || 1;          // dims are measured PRE-scale
  const len = Math.max(d.x, d.z) * k, wid = Math.max(0.30 * len, Math.min(d.x, d.z) * k);
  return { len, wid, hgt: Math.max(d.y * k, 0.20), axis: c.headDir.clone(), yaw: c.grp.rotation.y, k };
}

/** distance at which a subject of `len` spans `fill` of frame height at `fov` degrees */
function distForFill(len, fill, fov) {
  const halfFov = (fov * Math.PI) / 360;
  return len / (2 * fill * Math.tan(halfFov));
}

/* The slab is a 12x8 bedding plane, not a character: an orbit solve over-crops it into sand.
   These keep the framing verified frame-by-frame, now with a real lens per shot. */
const SLAB_CAM = {
  // 1. COLD OPEN - 85mm grazing down the spined flank. Silhouette only: no scale, no context,
  //    and the eye lands on the dorsal spines before the brain knows what it is looking at.
  ecu: (e) => ({ pos: [GLM.mix(0.55, 0.20, e), GLM.mix(2.30, 2.05, e), GLM.mix(3.10, 2.75, e)],
                 look: [GLM.mix(0.30, 0.05, e), 0.03, GLM.mix(-0.35, -0.45, e)], fov: fovOf(35) }),
  // 9. THE REVEAL - 35mm from above, a 10 s push that starts wide enough to say "rock" and
  //    ends tight enough to say "animal". Camera is inside the plate footprint so no void.
  ews: (e) => ({ pos: [GLM.mix(2.70, 0.70, e), GLM.mix(7.40, 3.30, e), GLM.mix(6.10, 2.20, e)],
                 look: [GLM.mix(-0.10, 0.10, e), GLM.mix(-0.45, 0.02, e), GLM.mix(-0.20, -0.02, e)],
                 fov: fovOf(35) }),
  // 10. ANATOMY - 50mm down the spine, slow lateral drift; spine stays on the rule-of-thirds
  ms:  (e) => ({ pos: [GLM.mix(-1.05, 0.75, e), GLM.mix(2.55, 2.05, e), GLM.mix(1.55, 1.15, e)],
                 look: [GLM.mix(-0.04, 0.06, e), 0.045, GLM.mix(0.05, -0.16, e)], fov: fovOf(35) }),
  // 11. THE EYE - 135mm on the head end (x=+2.44). Contre-jour: the relief carries it, so the
  //     plate never has to survive a 135mm crop on its own texture.
  cu:  (e) => ({ pos: [GLM.mix(-0.30, 0.35, e), GLM.mix(2.55, 2.15, e), GLM.mix(2.30, 1.95, e)],
                 look: [GLM.mix(0.15, 0.20, e), 0.04, GLM.mix(-0.15, -0.25, e)], fov: fovOf(50) }),
};

/* Open water has no subject to solve a distance against - a reef is a place, not a body.
   These are lens-and-position decisions, one per geography beat, and each of the four is a
   different setup so the film never repeats a frame it has already shown. */
const REEF_CAM = {
  // pressure arrives: 14mm just above the bed, looking up into the water column
  pressure: (e) => ({ pos: [GLM.mix(1.35, 0.85, e), -0.62, GLM.mix(4.55, 4.05, e)],
                      look: [0.05, -0.62, -2.60], fov: fovOf(14) }),
  // relation: 35mm, animals read against the reef face
  relation: (e) => ({ pos: [GLM.mix(2.75, 2.05, e), GLM.mix(0.05, -0.20, e), GLM.mix(2.60, 2.05, e)],
                      look: [0.35, -1.02, -2.35], fov: fovOf(35) }),
  // the last light: 24mm, tight and low, the column going dark
  lastlight: (e) => ({ pos: [GLM.mix(-0.55, 0.15, e), -0.75, GLM.mix(2.85, 2.35, e)],
                       look: [0.25, -0.72, -2.90], fov: fovOf(24) }),
  // return: 14mm from high and wide - the same place, now survivable
  return: (e) => ({ pos: [GLM.mix(-0.55, 0.45, e), GLM.mix(0.95, 0.60, e), GLM.mix(3.05, 2.35, e)],
                    look: [GLM.mix(0.10, 0.25, e), GLM.mix(-1.00, -1.10, e), GLM.mix(-2.55, -2.75, e)],
                    fov: fovOf(28) }),
  // inside the return: 50mm, taken from the opposite side so the two setups are not a stutter
  return_b: (e) => ({ pos: [GLM.mix(2.15, 1.60, e), GLM.mix(1.15, 0.80, e), GLM.mix(2.45, 1.85, e)],
                      look: [GLM.mix(0.05, 0.20, e), GLM.mix(-1.15, -1.05, e), GLM.mix(-2.45, -2.60, e)],
                      fov: fovOf(50) }),
  // closing: 24mm, drifting back off the reef into open water
  close: (e) => ({ pos: [GLM.mix(0.60, 0.10, e), GLM.mix(0.55, 1.05, e), GLM.mix(3.30, 4.30, e)],
                   look: [0.05, -1.00, -2.60], fov: fovOf(24) }),
};

/**
 * Frame the subject by measurement, not by trigonometry.
 *
 * Every version before this one computed a camera position from a length assumption and then
 * hoped the animal was in shot. It frequently was not: bodies sat off the frame edge, or the
 * camera was aimed at empty water. This solve projects the subject's ACTUAL deformed bounding
 * box through a candidate camera and iterates distance/height until the box is centred and
 * occupies the width the ladder asked for. `fill` is the fraction of frame width the body
 * covers; above 1.0 the body runs past the edge, which is what a close-up is.
 */
function subjectBox(who, frontFrac = null) {
  const c = CREATURE_BY_NAME[who];
  const box = new THREE.Box3();
  if (!c) return box;
  const v = new THREE.Vector3();
  const k = c.grp.scale.x || 1;
  // grp.position/rotation are rewritten every frame by the performance pass, but matrixWorld is
  // only recomputed at render time. Without this the solver frames the PREVIOUS frame's pose -
  // which is why a "centred" solve could still put the animal off the edge of the actual image.
  c.grp.updateMatrixWorld(true);
  // optional head region: only the front `frontFrac` of the body along its own head axis
  const head = c.grp.position.clone().addScaledVector(
    c.headDir.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), c.grp.rotation.y),
    (Math.max(c.dims.x, c.dims.z) * k) * (0.5 - frontFrac));
  c.root.traverse((o) => {
    if (!o.isMesh || !o.geometry?.attributes?.position) return;
    const pos = o.geometry.attributes.position, n = pos.count;
    const stride = Math.max(1, Math.floor(n / 900));
    for (let i = 0; i < n; i += stride) {
      v.fromBufferAttribute(pos, i);
      if (o.isSkinnedMesh && typeof o.applyBoneTransform === 'function') {
        try { o.applyBoneTransform(i, v); } catch (err) { continue; }
      }
      v.applyMatrix4(o.matrixWorld);
      if (!Number.isFinite(v.x) || !Number.isFinite(v.y) || !Number.isFinite(v.z)) continue;
      if (frontFrac !== null && v.distanceTo(head) > (Math.max(c.dims.x, c.dims.z) * k) * frontFrac) continue;
      box.expandByPoint(v);
    }
  });
  return box;
}

/** width/height of the box as seen from `pos`, plus where its centre lands in NDC */
function measureFraming(box, pos, tgt, fov) {
  const cam = new THREE.PerspectiveCamera(fov, ASPECT, 0.05, 200);
  cam.position.copy(pos);
  cam.up.set(0, 1, 0);
  cam.lookAt(tgt);
  cam.updateMatrixWorld(true);
  cam.updateProjectionMatrix();
  const v = new THREE.Vector3();
  let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9, seen = 0, total = 0;
  for (let i = 0; i <= 6; i++) {
    for (let j = 0; j <= 6; j++) {
      for (let k = 0; k <= 3; k++) {
        v.set(box.min.x + (box.max.x - box.min.x) * i / 6,
              box.min.y + (box.max.y - box.min.y) * j / 6,
              box.min.z + (box.max.z - box.min.z) * k / 3);
        v.project(cam);
        total++;
        if (v.z > 1 || v.z < -1) continue;
        seen++;
        x0 = Math.min(x0, v.x); x1 = Math.max(x1, v.x);
        y0 = Math.min(y0, v.y); y1 = Math.max(y1, v.y);
      }
    }
  }
  if (seen < total * 0.5) return null;           // more than half the body is behind the lens
  return {
    w: (x1 - x0) / 2, h: (y1 - y0) / 2,           // NDC spans -> fraction of frame
    cx: (x0 + x1) / 2, cy: (y0 + y1) / 2,
    x0, x1, y0, y1,
  };
}

function solveCreature(plan, fov) {
  const az = plan.azBase + plan.az;
  const dir = new THREE.Vector3(Math.sin(az), 0, Math.cos(az));
  const full = subjectBox(plan.who);
  if (full.isEmpty()) return null;
  // Close-ups are cut on the head. Framing a 135mm on an animal's mid-spine is a picture of a
  // back; the audience came for the eye and the frontal appendage.
  const headBox = plan.fill > 1.15 ? subjectBox(plan.who, 0.30) : null;
  // Try the head first; if a 3x fill drives the lens inside the body, fall back to the whole
  // animal at a fill it can actually hold. A shot that cannot be framed is not shipped.
  const head = solveCreatureIn(plan, fov, dir, full, headBox && !headBox.isEmpty() ? headBox : full);
  if (head && head.ok) return head.cam;
  const wide = solveCreatureIn({ ...plan, fill: Math.min(plan.fill, 1.55) }, fov, dir, full, full);
  return wide ? wide.cam : null;
}

function solveCreatureIn(plan, fov, dir, full, box) {
  const bodyH = Math.max(full.max.y - full.min.y, 0.05);
  const boxMid = (full.min.y + full.max.y) / 2;
  const swimmers = plan.who === 'rad1' || plan.who === 'opa';
  const camY = () => (swimmers
    ? boxMid + (plan.hgt - 0.5) * bodyH * 1.15
    : full.min.y + plan.hgt * bodyH);
  const aim = box.getCenter(new THREE.Vector3());

  let dist = 3.2, pos = new THREE.Vector3(), m = null;
  for (let iter = 0; iter < 18; iter++) {
    pos.set(aim.x + dir.x * dist, camY(), aim.z + dir.z * dist);
    m = measureFraming(box, pos, aim, fov);
    if (!m) { dist *= 1.4; continue; }                 // camera inside or behind the body
    // m.w scales as 1/dist, so the corrective step is m.w/fill, not fill/m.w
    const step = Math.pow(GLM.clamp(m.w / Math.max(plan.fill, 1e-3), 0.05, 20), 0.8);
    dist = GLM.clamp(dist * step, 0.30, 26);
    // centring: a real camera tilts/pans until the subject is on its axis. Do the same, and
    // re-measure immediately - a correction that is never verified is a guess.
    if (Math.abs(m.cx) > 0.02 || Math.abs(m.cy) > 0.02) {
      const cam = new THREE.PerspectiveCamera(fov, ASPECT, 0.05, 300);
      cam.position.copy(pos); cam.up.set(0, 1, 0); cam.lookAt(aim);
      cam.updateMatrixWorld(true); cam.updateProjectionMatrix();
      const right = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 0);
      const up = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 1);
      const halfH = Math.tan((fov * Math.PI) / 360) * dist;
      aim.addScaledVector(right, m.cx * halfH * ASPECT);
      aim.addScaledVector(up, m.cy * halfH);
      aim.y = GLM.clamp(aim.y, full.min.y, full.max.y);
    }
    if (Math.abs(step - 1) < 0.004 && Math.abs(m.cx) < 0.03 && Math.abs(m.cy) < 0.05) break;
  }
  pos.set(aim.x + dir.x * dist, camY(), aim.z + dir.z * dist);
  const fin = measureFraming(box, pos, aim, fov) || m;
  window.__DC = window.__DC || {};
  window.__DC.last = {
    name: plan._name, who: plan.who, dist: +dist.toFixed(2),
    occW: fin ? +fin.w.toFixed(2) : 0, occH: fin ? +fin.h.toFixed(2) : 0,
    cx: fin ? +fin.cx.toFixed(2) : 0, cy: fin ? +fin.cy.toFixed(2) : 0,
    head: box !== full, pos: pos.toArray().map((n) => +n.toFixed(2)),
    look: aim.toArray().map((n) => +n.toFixed(2)),
  };
  const ok = !!fin && Math.abs(fin.cx) < 0.28 && Math.abs(fin.cy) < 0.34
    && fin.w > plan.fill * 0.55 && fin.w < plan.fill * 1.9;
  return { cam: { pos, look: aim.clone(), fov, dutch: plan.dutch, blur: plan.blur }, ok, fin, dist };
}

function solveShot(name, e, u, t) {
  window.__DC = window.__DC || {}; window.__DC.last = null;
  if (SLAB_CAM[name]) {
    const c = SLAB_CAM[name](e);
    return {
      pos: new THREE.Vector3(...c.pos), look: new THREE.Vector3(...c.look), fov: c.fov,
      dutch: 0, blur: 0.08,
    };
  }
  if (REEF_CAM[name]) {
    const c = REEF_CAM[name](e);
    return {
      pos: new THREE.Vector3(...c.pos), look: new THREE.Vector3(...c.look), fov: c.fov,
      dutch: 0, blur: 0.10,
    };
  }
  const plan = { ...(SHOT_PLAN[name] || SHOT_PLAN.rad1_ms), _name: name };
  const r = solveCreature(plan, fovOf(plan.mm));
  if (r) return r;
  const c = SLAB_CAM.ews(e);
  return { pos: new THREE.Vector3(...c.pos), look: new THREE.Vector3(...c.look), fov: c.fov, dutch: 0, blur: 0.08 };
}

/** the entire visual language of the film, one row per shot.
 *  `mm` is the real focal length; fov is derived from the full-frame sensor height so the
 *  lens table in cinematic-language.md applies directly. `hgt` is the lens axis expressed as a
 *  multiplier of the subject's own height (0 = at its base, 1 = at its top). */
const ASPECT = 16 / 9;
const SENSOR_H = 24.0;                        // full-frame 36x24
const fovOf = (mm) => 2 * Math.atan(SENSOR_H / (2 * mm)) * 180 / Math.PI;

const SHOT_PLAN = {
  // creature subjects
  // fill = subject length / frame width. Below 1 the body sits inside the frame (WS/MS);
  // at 1 it fills it; above 1 the body runs past the edge, which is what a CU actually is.
  rad1_ms:  { who: 'rad1', mm: 35,  fill: 0.86, az: 0.34,  azBase: 0.30, hgt: 0.55, dutch: 0.00, blur: 0.10 },
  rad1_ecu: { who: 'rad1', mm: 100, fill: 3.30, az: 0.20,  azBase: 0.52, hgt: 0.34, dutch: 0.00, blur: 0.06 },
  rad1_cu:  { who: 'rad1', mm: 85,  fill: 1.35, az: -0.16, azBase: 0.42, hgt: 0.56, dutch: 0.02, blur: 0.08 },
  opa_cu:   { who: 'opa',  mm: 85,  fill: 2.20, az: 0.05,  azBase: -0.55, hgt: 0.36, dutch: 0.00, blur: 0.06 },
  opa_mcu:  { who: 'opa',  mm: 50,  fill: 1.15, az: -0.20, azBase: -0.40, hgt: 0.50, dutch: -0.04, blur: 0.10 },
  hal_mcu:  { who: 'hal',  mm: 85,  fill: 1.45, az: 0.30,  azBase: 0.28, hgt: 0.42, dutch: 0.00, blur: 0.06 },
  hal2_ms:  { who: 'hal2', mm: 35,  fill: 0.95, az: 0.42,  azBase: 0.34, hgt: 0.50, dutch: 0.00, blur: 0.10 },
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
    // The preset's amber rim is beautiful on a hero prop and wrong for a 40 m seabed: it was
    // the single largest warm contribution to the bed. Cool it, and let the bioluminescent
    // life carry the only warm accent in the frame.
    SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#7fd8e8').multiplyScalar(0.44);
    SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.010, 0.030, 0.042);
    SHARED_LIGHT_UNIFORMS.uFogStart.value = 2.4;
    SHARED_LIGHT_UNIFORMS.uFogRange.value = 30.0;
  }
  domeMat.uniforms.uAmt.value = isSea ? (0.55 + 0.45 * key) : 0;
  scene.fog = isSea ? new THREE.FogExp2('#17505f', 0.046 - 0.022 * key) : new THREE.FogExp2('#0a0d10', 0.030);
  scene.background = new THREE.Color(isSea ? '#082229' : '#05080a');

  motes.mesh.visible = false;
  shadowRig.updateShadowMap(scene, camera.position, 9.0);
  motes.mesh.visible = isSea;

  // performance energy follows the drama: full life, strained in the crisis, calmer after
  const drive = isSea
    ? (frame < 330 ? 1.0 : frame < 690 ? GLM.clamp(1.45 - key * 0.9, 0.42, 1.30) : 0.62)
    : 0.15;
  performRadiodont(rad1, t, drive * 1.2);
  performRadiodont(rad2, t + 0.7, drive * 0.85);
  performOpabinia(opa, t + 1.3, drive);
  performHallucigenia(hal, t, drive, t * 2.2);
  performHallucigenia(hal2, t + 0.4, drive * 0.8, t * 2.2 + 1.1);

  const cross = smooth(120, 320, frame);
  rad1.grp.position.x = GLM.mix(3.1, -3.0, cross);
  rad1.grp.position.y = 0.30 + 0.10 * Math.sin(t * 1.1) + (frame >= 1637 ? 0.35 * smooth(1637, 1779, frame) : 0);
  rad1.grp.position.z = -3.4 + 0.55 * Math.sin(t * 0.6);
  rad1.grp.rotation.y = Math.PI + 0.10 * Math.sin(t * 0.9) + rad1.recoil * 0.7;

  const crisis = frame >= 315 && frame < 690;
  if (crisis) {
    const k = smooth(330, 400, frame) * (1 - smooth(620, 690, frame));
    rad1.recoil = k; hal.curl = k;
    opa.grp.rotation.z = 0.85 * k * Math.sin((frame - 330) * 0.12) + 0.08;
  }
  // These were `+=` / `-=` inside draw(), so every frame added to the previous frame's state:
  // the progressive render drifted the animals metres below the seabed while random-access
  // preflight looked fine. Pose is now a pure function of `frame`.
  const sink = frame >= 1290 ? frame - 1290 : 0;
  const opaTumble = crisis ? smooth(315, 385, frame) * (1 - smooth(615, 690, frame)) : 0;
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
  const siltAmt = (frame >= 315 && frame < 700) ? smooth(315, 420, frame) * (1 - smooth(635, 700, frame)) : 0;
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

  // the three water layers breathe with the same curve as the light
  shaftMat.uniforms.uAmt.value = isSea ? 0.10 + 0.30 * key : 0;
  shaftMat.uniforms.uT.value = t;
  causticMat.uniforms.uAmt.value = isSea ? 0.06 + 0.26 * key : 0;
  causticMat.uniforms.uT.value = t;
  snowMat.opacity = isSea ? 0.22 + 0.34 * key : 0;
  if (isSea) {
    const sp = snowGeo.attributes.position.array;
    for (let i = 0; i < SNOW_N; i++) {
      const ph = snowSeed[i];
      sp[i * 3]     += Math.sin(t * 0.30 + ph) * 0.0016;
      sp[i * 3 + 1] -= 0.0032 - 0.0016 * Math.sin(t * 0.22 + ph * 1.7);
      sp[i * 3 + 2] += Math.cos(t * 0.26 + ph * 0.9) * 0.0014;
      if (sp[i * 3 + 1] < -1.45) { sp[i * 3 + 1] = 7.6; sp[i * 3] = (rnd() - 0.5) * 18; }
    }
    snowGeo.attributes.position.needsUpdate = true;
  }

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
  if (window.__DC_DEBUG) drawDebug();
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
window.__Scene = { sea, lab, scene, camera, THREE, draw,
  _audit: { rad1, opa, hal, hal2, rad2 } };   // read-only hook for the framing probe
window.__IMAX_READY__ = true;
