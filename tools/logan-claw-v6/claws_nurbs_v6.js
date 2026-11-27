import * as THREE from 'three';
import {
  GLM,
  assertSafeLatinGlyphs,
  buildLoftGeometry,
  buildNormalFromCanvas,
  mulberry32,
} from '/tools/monarch-v6-imax-sdk/index.js';

/**
 * Logan — Rig-to-Render VFX Breakdown (`V6.2 Hollywood IMAX`)
 *   1. High-Poly Lofted Curved Hollow-Ground Adamantium Claws (`9,984` tris across 3 blades)
 *   2. Bone-Attached 3D Maya/MetaHuman NURBS Spline Rig Controllers (torso, neck, face, wrist & 15 finger loops)
 *   3. Live-Animating 3D Golden MetaHuman "Expressions / Rig Logic" Facial Picker Schematic
 */

const RIG_GUI_LABELS = [
  'expressions',
  'rig logic',
  'GUI switch',
  'BROW_FURROW',
  'EYE_SACCADE',
  'SNIKT_RIG_v6',
];
assertSafeLatinGlyphs(RIG_GUI_LABELS, 'RigPickerGUI');

/**
 * Procedural 512x512 Anisotropic Brushed Surgical-Steel Micro-Grind Normal + Roughness + Subtle Knuckle Crimson Tint
 */
function buildBrushedSteelTextures(seed = 1974) {
  const S = 512;
  const heightCanvas = document.createElement('canvas');
  heightCanvas.width = S;
  heightCanvas.height = S;
  const hctx = heightCanvas.getContext('2d');
  const rng = mulberry32(seed);

  hctx.fillStyle = '#808080';
  hctx.fillRect(0, 0, S, S);

  // Fine longitudinal brushed steel grind lines along V (blade length)
  for (let i = 0; i < 950; i++) {
    const x = rng() * S;
    const w = 0.5 + rng() * 1.4;
    const lum = Math.round(105 + rng() * 50);
    hctx.fillStyle = `rgba(${lum},${lum},${lum},0.26)`;
    hctx.fillRect(x, 0, w, S);
  }
  // Micro-nicks along bevels
  for (let i = 0; i < 65; i++) {
    const x = rng() * S;
    const y = rng() * S;
    hctx.strokeStyle = 'rgba(40,40,40,0.32)';
    hctx.lineWidth = 0.9;
    hctx.beginPath();
    hctx.moveTo(x, y);
    hctx.lineTo(x + (rng() - 0.5) * 14, y + (rng() - 0.5) * 6);
    hctx.stroke();
  }
  const normalMap = buildNormalFromCanvas(heightCanvas, 1.45, S);

  // Albedo: bright cold surgical titanium-steel with subtle dark crimson/oil sheen near tang (v < 0.22)
  const colCanvas = document.createElement('canvas');
  colCanvas.width = S;
  colCanvas.height = S;
  const cctx = colCanvas.getContext('2d');
  const grad = cctx.createLinearGradient(0, 0, 0, S);
  grad.addColorStop(0.00, '#5e2320');
  grad.addColorStop(0.14, '#aeb6c2');
  grad.addColorStop(0.32, '#dfe7f2');
  grad.addColorStop(0.82, '#eef4fc');
  grad.addColorStop(1.00, '#ffffff');
  cctx.fillStyle = grad;
  cctx.fillRect(0, 0, S, S);

  // Subtle longitudinal streak modulation
  for (let i = 0; i < 420; i++) {
    const x = rng() * S;
    cctx.fillStyle = rng() > 0.5 ? 'rgba(255,255,255,0.06)' : 'rgba(90,105,125,0.07)';
    cctx.fillRect(x, 0, 1 + rng() * 1.6, S);
  }
  // Dried crimson micro-streaks near knuckle emergence (top 22% of V when v=0 at base)
  for (let i = 0; i < 38; i++) {
    const x = rng() * S;
    const len = S * (0.06 + rng() * 0.19);
    const cg = cctx.createLinearGradient(0, 0, 0, len);
    cg.addColorStop(0, 'rgba(72, 12, 10, 0.55)');
    cg.addColorStop(1, 'rgba(72, 12, 10, 0.0)');
    cctx.fillStyle = cg;
    cctx.fillRect(x, 0, 1.5 + rng() * 3.5, len);
  }

  const albedoMap = new THREE.CanvasTexture(colCanvas);
  albedoMap.colorSpace = THREE.SRGBColorSpace;
  albedoMap.flipY = false;

  const roughCanvas = document.createElement('canvas');
  roughCanvas.width = S;
  roughCanvas.height = S;
  const rctx = roughCanvas.getContext('2d');
  rctx.fillStyle = '#303030';
  rctx.fillRect(0, 0, S, S);
  for (let i = 0; i < 500; i++) {
    const x = rng() * S;
    const v = Math.round(28 + rng() * 38);
    rctx.fillStyle = `rgb(${v},${v},${v})`;
    rctx.fillRect(x, 0, 1.2, S);
  }
  const roughnessMap = new THREE.CanvasTexture(roughCanvas);
  roughnessMap.flipY = false;

  return { albedoMap, normalMap, roughnessMap };
}

/**
 * Builds a single high-poly curved hollow-ground hexagonal katana/Adamantium claw geometry (`52 x 16` loft).
 * Local coordinates inside claw group:
 *   - Base emerges at `[0, 0, 0]` and extends along `-X` (`0 -> -bladeLen`)
 *   - Cutting edge faces `-Y` (toward pinky/down-right when fist is across chest), dorsal spine faces `+Y`
 *   - Blade flats face `±Z` (dorsal/palmar faces catching camera & rim speculars!)
 */
function buildSingleCurvedClawGeometry(bladeLen = 0.278) {
  const ROWS = 52;
  const COLS = 16;
  const tangLen = 0.065;
  const rings = [];

  // 16-point symmetrical hollow-ground hexagonal blade cross-section in (y_profile, z_thickness):
  //   y in [-1..+1]: +1 = thick dorsal spine, -1 = razor cutting edge
  //   z in [-1..+1]: blade cheek thickness
  const baseProfile = [];
  for (let c = 0; c < COLS; c++) {
    const a = (c / COLS) * Math.PI * 2;
    // Map circle parameter into sharp-edged hollow-ground katana cross-section
    const sy = Math.cos(a); // +1 at spine (c=0), -1 at razor edge (c=8)
    const sz = Math.sin(a);
    let yNorm = sy;
    let zNorm = sz;
    if (sy < -0.35) {
      // Primary & secondary razor bevel converging to a surgical edge at y = -1
      const tEdge = (sy + 1.0) / 0.65; // 0 at edge, 1 at bevel ridge
      zNorm = Math.sign(sz) * Math.pow(Math.abs(sz), 0.75) * (0.04 + 0.96 * tEdge);
    } else if (Math.abs(sy - 0.18) < 0.36) {
      // Subtle fuller (blood-groove) concavity along mid-cheek
      const groove = Math.cos(((sy - 0.18) / 0.36) * Math.PI * 0.5);
      zNorm *= (1.0 - 0.24 * groove);
    } else if (sy > 0.55) {
      // Crisp chamfered dorsal spine
      zNorm *= 0.72;
    }
    baseProfile.push([yNorm, zNorm]);
  }

  for (let r = 0; r < ROWS; r++) {
    const u = r / (ROWS - 1); // 0 = internal tang, 0.19 = knuckle exit, 1.0 = needle point
    const x = tangLen * (1.0 - Math.min(1.0, u / 0.19)) - bladeLen * Math.max(0.0, (u - 0.19) / 0.81);
    const s = Math.max(0.0, (u - 0.19) / 0.81); // 0..1 along visible blade

    // Width (`halfH` in Y) & thickness (`halfT` in Z) taper smoothly to a lethal needle tip
    const tipTaper = s < 0.68
      ? (1.0 - 0.14 * (s / 0.68))
      : Math.max(0.012, 0.86 * Math.pow(1.0 - (s - 0.68) / 0.32, 1.28));
    const halfH = 0.0086 * tipTaper; // ~17.2 mm blade height at base -> needle point
    const halfT = 0.0024 * (s < 0.72 ? (1.0 - 0.18 * s) : Math.max(0.015, 0.82 * Math.pow(1.0 - (s - 0.72) / 0.28, 1.15)));

    // Graceful predatory downward/edge-ward curve (`-Y` arc, ~29 mm sweep at tip — matches reference sheet1 f=121/148!)
    const arcY = -0.029 * Math.pow(s, 1.85);

    const ring = [];
    for (let c = 0; c < COLS; c++) {
      const [py, pz] = baseProfile[c];
      ring.push([x, arcY + py * halfH, pz * halfT]);
    }
    rings.push(ring);
  }

  return buildLoftGeometry(rings, true, true);
}

export function createAdamantiumClawRig(handBones = []) {
  const tex = buildBrushedSteelTextures(1974);

  const clayBladeMat = new THREE.MeshStandardMaterial({
    color: new THREE.Color('#dfe4ec'),
    roughness: 0.42,
    metalness: 0.10,
    normalMap: tex.normalMap,
    normalScale: new THREE.Vector2(0.18, 0.18),
    side: THREE.DoubleSide,
  });

  const glintUniforms = {
    uGlintSweep: { value: -1.0 },
  };

  const renderBladeMat = new THREE.MeshPhysicalMaterial({
    color: new THREE.Color('#6a7f96'),
    map: tex.albedoMap,
    normalMap: tex.normalMap,
    normalScale: new THREE.Vector2(0.55, 0.55),
    roughnessMap: tex.roughnessMap,
    roughness: 0.29,
    metalness: 0.92,
    clearcoat: 0.42,
    clearcoatRoughness: 0.11,
    anisotropy: 0.78,
    anisotropyRotation: 0.0,
    envMapIntensity: 0.88,
    side: THREE.DoubleSide,
  });

  renderBladeMat.onBeforeCompile = (shader) => {
    shader.uniforms.uGlintSweep = glintUniforms.uGlintSweep;
    shader.fragmentShader = `uniform float uGlintSweep;\n` + shader.fragmentShader;
    shader.fragmentShader = shader.fragmentShader.replace(
      '#include <map_fragment>',
      `
      #include <map_fragment>
      #ifdef USE_MAP
        // Dark brushed-gunmetal fuller spine + razor-bright surgical bevel edge!
        float edgeDist = abs(fract(vMapUv.x * 2.0) - 0.5) * 2.0;
        float bevelProfile = mix(0.32, 1.18, smoothstep(0.18, 0.86, edgeDist));
        diffuseColor.rgb *= bevelProfile;
      #endif
      `
    );
    shader.fragmentShader = shader.fragmentShader.replace(
      '#include <emissivemap_fragment>',
      `
      #include <emissivemap_fragment>
      #ifdef USE_MAP
        if (uGlintSweep >= 0.0 && uGlintSweep <= 1.2) {
          float band = exp(-pow((vMapUv.y - uGlintSweep) * 11.0, 2.0));
          float edgeMask = smoothstep(0.35, 0.92, abs(fract(vMapUv.x * 2.0) - 0.5) * 2.0);
          totalEmissiveRadiance += vec3(0.42, 0.78, 1.08) * band * (0.35 + 0.65 * edgeMask) * 0.68;
        }
      #endif
      `
    );
  };

  const weltClayMat = new THREE.MeshStandardMaterial({
    color: new THREE.Color('#8e9299'),
    roughness: 0.78,
    metalness: 0.0,
  });
  const weltRenderMat = new THREE.MeshStandardMaterial({
    color: new THREE.Color('#3c0e0c'),
    roughness: 0.32,
    metalness: 0.05,
  });

  const root = new THREE.Group();
  root.name = 'AdamantiumClawRig';

  // Mount directly onto BodyMesh `hand_r` bone!
  const hostBone = handBones[handBones.length - 1] || handBones[0];
  if (hostBone) hostBone.add(root);

  // Three anatomical inter-metacarpal slots in `hand_r` local coordinates (1 unit = 1m):
  //   Slot 0: Index–Middle valley  (`y = +0.0175`)
  //   Slot 1: Middle–Ring valley   (`y = -0.0068`) — slightly longest center claw (`28.4 cm`)
  //   Slot 2: Ring–Pinky valley    (`y = -0.0290`)
  const slotSpecs = [
    { y: +0.0176, z: -0.0078, x: -0.084, len: 0.270, fanZ: -0.044, fanY: +0.018 },
    { y: -0.0068, z: -0.0086, x: -0.086, len: 0.284, fanZ:  0.000, fanY:  0.000 },
    { y: -0.0292, z: -0.0058, x: -0.076, len: 0.266, fanZ: +0.046, fanY: -0.018 },
  ];

  const blades = [];
  const welts = [];
  const weltGeo = new THREE.TorusGeometry(0.0058, 0.0019, 8, 18);
  weltGeo.scale(0.65, 1.35, 0.85);

  for (let i = 0; i < slotSpecs.length; i++) {
    const sp = slotSpecs[i];
    const slotHolder = new THREE.Group();
    slotHolder.position.set(sp.x, sp.y, sp.z);
    slotHolder.rotation.set(0, sp.fanY, sp.fanZ);

    const bladeGeo = buildSingleCurvedClawGeometry(sp.len);
    const bladeMesh = new THREE.Mesh(bladeGeo, renderBladeMat);
    bladeMesh.castShadow = true;
    bladeMesh.receiveShadow = true;
    bladeMesh.frustumCulled = false;
    slotHolder.add(bladeMesh);

    const weltMesh = new THREE.Mesh(weltGeo, weltRenderMat);
    weltMesh.rotation.y = Math.PI / 2;
    weltMesh.position.set(-0.002, 0, 0);
    weltMesh.frustumCulled = false;
    slotHolder.add(weltMesh);

    root.add(slotHolder);
    blades.push({ mesh: bladeMesh, slotHolder, len: sp.len, baseFanZ: sp.fanZ });
    welts.push(weltMesh);
  }

  function setRenderMode(mode) {
    const isClay = mode === 'viewport_clay';
    for (const b of blades) b.mesh.material = isClay ? clayBladeMat : renderBladeMat;
    for (const w of welts) w.material = isClay ? weltClayMat : weltRenderMat;
  }

  function setState({ extension = 0.0, tremor = 0.0, glintSweep = -1.0 } = {}) {
    glintUniforms.uGlintSweep.value = glintSweep;
    if (extension <= 0.015) {
      root.visible = false;
      return;
    }
    root.visible = true;
    for (let i = 0; i < blades.length; i++) {
      // Staggered 3-blade ballistic extension
      const localExt = GLM.clamp((extension - i * 0.05) / 0.90, 0.0, 1.0);
      const eased = 1.0 - Math.pow(1.0 - localExt, 3.0);
      const b = blades[i];
      b.mesh.visible = localExt > 0.02;
      // Slide out along -X from +len (inside forearm) to 0.0 (locked at knuckle)
      b.mesh.position.x = (1.0 - eased) * (b.len * 0.92);
      b.mesh.scale.set(Math.max(0.15, eased), 1.0, 1.0);
      b.slotHolder.rotation.z = b.baseFanZ + tremor * (i - 1) * 0.012;
      welts[i].visible = localExt > 0.15;
    }
  }

  return { root, setRenderMode, setState };
}

function makeCircleLoop(radiusX, radiusZ, segments = 44, color = '#dcd046', axis = 'XZ', offset = [0, 0, 0], tubeR = 0.00165) {
  const pts = [];
  for (let i = 0; i < segments; i++) {
    const a = (i / segments) * Math.PI * 2;
    const c = Math.cos(a) * radiusX;
    const s = Math.sin(a) * radiusZ;
    if (axis === 'XZ') pts.push(new THREE.Vector3(c + offset[0], offset[1], s + offset[2]));
    else if (axis === 'YZ') pts.push(new THREE.Vector3(offset[0], c + offset[1], s + offset[2]));
    else pts.push(new THREE.Vector3(c + offset[0], s + offset[1], offset[2]));
  }
  const curve = new THREE.CatmullRomCurve3(pts, true);
  const geo = new THREE.TubeGeometry(curve, segments, tubeR, 5, true);
  const mat = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.90,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow = false;
  mesh.receiveShadow = false;
  mesh.renderOrder = 19;
  mesh.frustumCulled = false;
  return mesh;
}

function makePolyline(points3D, color = '#df423a', opacity = 0.88, tubeR = 0.00125) {
  const pts = points3D.map((p) => new THREE.Vector3(...p));
  const curve = new THREE.CatmullRomCurve3(pts, false);
  const geo = new THREE.TubeGeometry(curve, Math.max(16, pts.length * 4), tubeR, 5, false);
  const mat = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow = false;
  mesh.receiveShadow = false;
  mesh.renderOrder = 19;
  mesh.frustumCulled = false;
  return mesh;
}

function makeRigDot(color = '#e03c32', radius = 0.0048, pos = [0, 0, 0]) {
  const m = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 10, 8),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.88, depthWrite: false })
  );
  m.position.set(...pos);
  m.renderOrder = 20;
  m.frustumCulled = false;
  return m;
}

/**
 * Bone-Parented 3D Maya / MetaHuman NURBS Controller Rig:
 *   Note that on MetaHuman spine/neck/head bones, local `X` points UP along spine,
 *   local `Y` points RIGHT (`-worldX`), and local `Z` points FORWARD (`+worldZ`),
 *   so horizontal torso/neck hoops lie in the bone's local **`YZ` plane**!
 */
export function createNurbsRigOverlay(bonesByName) {
  const rigObjects = [];
  const addOnBone = (boneName, obj) => {
    const list = bonesByName.get(boneName);
    const b = list ? list[list.length - 1] : null;
    if (!b) return;
    b.add(obj);
    rigObjects.push(obj);
  };

  // 1. Torso FK/IK Rings (local YZ plane around X-up spine!)
  addOnBone('pelvis',   makeCircleLoop(0.205, 0.148, 56, '#df3b32', 'YZ', [0.00, 0, 0.01]));
  addOnBone('pelvis',   makeRigDot('#df3b32', 0.0055, [0.00, +0.208, 0.03]));
  addOnBone('pelvis',   makeRigDot('#df3b32', 0.0055, [0.00, -0.208, 0.03]));
  addOnBone('spine_01', makeCircleLoop(0.192, 0.142, 56, '#dcd046', 'YZ', [0.03, 0, 0.01]));
  addOnBone('spine_02', makeCircleLoop(0.196, 0.146, 56, '#48c858', 'YZ', [0.02, 0, 0.01]));
  addOnBone('spine_03', makeCircleLoop(0.208, 0.156, 56, '#dcd046', 'YZ', [0.02, 0, 0.01]));
  addOnBone('spine_03', makeRigDot('#df3b32', 0.0052, [0.04, +0.085, 0.155]));
  addOnBone('spine_03', makeRigDot('#df3b32', 0.0052, [0.04, -0.085, 0.155]));
  addOnBone('spine_05', makeCircleLoop(0.214, 0.152, 56, '#dcd046', 'YZ', [-0.02, 0, 0.02]));
  addOnBone('spine_05', makePolyline([[-0.24, 0, 0.155], [0.16, 0, 0.155]], '#dcd046', 0.72));

  // 2. Collar / Neck Ring & Sagittal Facial Symmetry Spline (`head` local X=up, Y=-worldX, Z=+worldZ!)
  addOnBone('neck_01', makeCircleLoop(0.088, 0.086, 48, '#dcd046', 'YZ', [0.01, 0, 0.015]));
  addOnBone('head', makePolyline([
    [0.185, 0.0, 0.098],
    [0.145, 0.0, 0.112],
    [0.105, 0.0, 0.115],
    [0.084, 0.0, 0.118],
    [0.052, 0.0, 0.136],
    [0.036, 0.0, 0.122],
    [0.016, 0.0, 0.120],
    [-0.008, 0.0, 0.116],
    [-0.034, 0.0, 0.108],
    [-0.052, 0.0, 0.075],
  ], '#df423a', 0.76));

  // Subtle golden brow/cheek/jaw facial rig micro-locators on `head`
  for (const pt of [
    [0.098, +0.032, 0.112], [0.098, -0.032, 0.112],
    [0.056, +0.054, 0.096], [0.056, -0.054, 0.096],
    [0.006, +0.028, 0.112], [0.006, -0.028, 0.112],
  ]) {
    addOnBone('head', makeRigDot('#e6b832', 0.0022, pt));
  }

  // 3. Blue Elbow Pole-Vector Guides (`lowerarm_r` & `lowerarm_l`)
  addOnBone('lowerarm_r', makeCircleLoop(0.058, 0.058, 36, '#3b82e6', 'YZ', [0.0, 0, 0]));
  addOnBone('lowerarm_l', makeCircleLoop(0.058, 0.058, 36, '#3b82e6', 'YZ', [0.0, 0, 0]));

  // 4. Right Hand Wrist + 15 Finger Phalanx Orange FK Loops (`hand_r` local -X = along fingers!)
  addOnBone('hand_r', makeCircleLoop(0.052, 0.034, 42, '#ee7b24', 'YZ', [-0.012, 0, 0.0]));
  addOnBone('hand_r', makeCircleLoop(0.056, 0.032, 42, '#dcd046', 'YZ', [-0.055, 0, 0.0]));

  const fingerRings = [
    ['index_01_r',  0.0155, '#ee7b24'], ['index_02_r',  0.0132, '#48c858'], ['index_03_r',  0.0112, '#dcd046'],
    ['middle_01_r', 0.0160, '#ee7b24'], ['middle_02_r', 0.0136, '#48c858'], ['middle_03_r', 0.0115, '#dcd046'],
    ['ring_01_r',   0.0150, '#ee7b24'], ['ring_02_r',   0.0128, '#48c858'], ['ring_03_r',   0.0108, '#dcd046'],
    ['pinky_01_r',  0.0135, '#ee7b24'], ['pinky_02_r',  0.0115, '#48c858'], ['pinky_03_r',  0.0098, '#dcd046'],
    ['thumb_01_r',  0.0175, '#ee7b24'], ['thumb_02_r',  0.0148, '#48c858'], ['thumb_03_r',  0.0124, '#dcd046'],
  ];
  for (const [bName, rad, col] of fingerRings) {
    addOnBone(bName, makeCircleLoop(rad, rad * 0.94, 24, col, 'YZ', [-0.012, 0, 0], 0.00105));
  }

  // Left hand red IK/FK tab handle (matching lower-right of sheet1 f=000..081!)
  addOnBone('hand_l', makePolyline([
    [0.01, -0.042, 0.02], [0.07, -0.048, 0.02], [0.07, -0.030, 0.02], [0.01, -0.026, 0.02], [0.01, -0.042, 0.02],
  ], '#df3b32', 0.88));

  function setVisible(vis) {
    for (const o of rigObjects) o.visible = vis;
  }

  return { setVisible, rigObjects };
}

/**
 * 3D Floating Golden MetaHuman "Rig Logic / Expressions" Facial Picker Schematic
 * Live-updates active control sliders & gaze crosshairs every frame in Viewport mode!
 */
export function createRigPickerBoard() {
  const W = 768;
  const H = 960;
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d');
  const tex = new THREE.CanvasTexture(canvas);
  tex.minFilter = THREE.LinearFilter;
  tex.magFilter = THREE.LinearFilter;
  tex.colorSpace = THREE.SRGBColorSpace;

  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(0.28, 0.35),
    new THREE.MeshBasicMaterial({
      map: tex,
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
    })
  );
  mesh.renderOrder = 15;
  mesh.frustumCulled = false;

  function draw({ brow = 0.5, squint = 0.3, sneer = 0.2, clench = 0.0, gazeX = 0.0, gazeY = 0.0 } = {}) {
    ctx.clearRect(0, 0, W, H);

    const goldDim = 'rgba(226, 182, 52, 0.38)';
    const goldMid = 'rgba(236, 192, 58, 0.72)';
    const goldHot = '#ffd24a';

    // Outer picker frame
    ctx.strokeStyle = goldDim;
    ctx.lineWidth = 2.0;
    ctx.strokeRect(26, 24, W - 52, H - 96);

    // Cranium + Jaw Wireframe Contour
    const cx = W * 0.5;
    const cy = H * 0.42;
    ctx.strokeStyle = goldMid;
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.ellipse(cx, cy - 30, 198, 248, 0, Math.PI, Math.PI * 2);
    ctx.bezierCurveTo(cx + 198, cy + 95, cx + 148, cy + 218, cx, cy + 258);
    ctx.bezierCurveTo(cx - 148, cy + 218, cx - 198, cy + 95, cx - 198, cy - 30);
    ctx.stroke();

    // Vertical & Horizontal Symmetry Guides
    ctx.strokeStyle = 'rgba(226, 182, 52, 0.20)';
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(cx, 54); ctx.lineTo(cx, cy + 270);
    ctx.moveTo(cx - 210, cy - 42); ctx.lineTo(cx + 210, cy - 42);
    ctx.stroke();

    // Brow Arch Sliders (live-driven by `brow`!)
    for (const sgn of [-1, 1]) {
      for (let k = 0; k < 4; k++) {
        const bx = cx + sgn * (42 + k * 34);
        const byTop = cy - 118 + k * 5;
        const byBot = byTop + 36;
        ctx.strokeStyle = goldDim;
        ctx.lineWidth = 2.0;
        ctx.beginPath(); ctx.moveTo(bx, byTop); ctx.lineTo(bx, byBot); ctx.stroke();

        const dotY = byTop + (0.25 + 0.65 * brow) * 36;
        ctx.fillStyle = goldHot;
        ctx.beginPath(); ctx.arc(bx, dotY, 6.2, 0, Math.PI * 2); ctx.fill();
      }
    }

    // Eye Gaze Joysticks + Squint Rings
    for (const sgn of [-1, 1]) {
      const ex = cx + sgn * 84;
      const ey = cy - 42;
      ctx.strokeStyle = goldMid;
      ctx.lineWidth = 2.2;
      ctx.beginPath(); ctx.ellipse(ex, ey, 44, 28 * (1.0 - 0.35 * squint), 0, 0, Math.PI * 2); ctx.stroke();
      ctx.strokeRect(ex - 52, ey - 38, 104, 76);

      ctx.fillStyle = goldHot;
      ctx.beginPath();
      ctx.arc(ex + gazeX * 22, ey - gazeY * 16, 7.5, 0, Math.PI * 2);
      ctx.fill();
    }

    // Nasal Bridge & Sneer Triangles
    ctx.strokeStyle = goldMid;
    ctx.beginPath();
    ctx.moveTo(cx, cy - 58);
    ctx.lineTo(cx - 32, cy + 44);
    ctx.lineTo(cx + 32, cy + 44);
    ctx.closePath();
    ctx.stroke();
    for (const sgn of [-1, 1]) {
      const nx = cx + sgn * 48;
      const ny = cy + 36 - sneer * 16;
      ctx.fillStyle = goldHot;
      ctx.beginPath(); ctx.arc(nx, ny, 5.8, 0, Math.PI * 2); ctx.fill();
    }

    // Mouth / Jaw Controller Matrix
    ctx.strokeStyle = goldMid;
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.ellipse(cx, cy + 118, 78, 28, 0, 0, Math.PI * 2);
    ctx.stroke();
    for (let m = -3; m <= 3; m++) {
      const mx = cx + m * 24;
      const my = cy + 118 + Math.abs(m) * 3 * clench;
      ctx.fillStyle = m === 0 ? goldHot : goldMid;
      ctx.beginPath(); ctx.arc(mx, my, 5.2, 0, Math.PI * 2); ctx.fill();
    }

    // Side Aux Slider Banks (matching dense rig-logic dots seen in macro f=121..135!)
    for (const bankX of [56, W - 134]) {
      ctx.strokeStyle = goldDim;
      ctx.strokeRect(bankX, cy + 150, 78, 210);
      for (let r = 0; r < 6; r++) {
        const ry = cy + 172 + r * 30;
        ctx.beginPath(); ctx.moveTo(bankX + 12, ry); ctx.lineTo(bankX + 66, ry); ctx.stroke();
        const v = ((r % 2 === 0 ? brow : clench) * 0.7 + 0.18);
        ctx.fillStyle = goldHot;
        ctx.beginPath(); ctx.arc(bankX + 12 + v * 54, ry, 5.0, 0, Math.PI * 2); ctx.fill();
      }
    }

    // Crisp Bottom Rig-Logic Labels (identical layout to reference viewport!)
    ctx.font = '600 22px "IBM Plex Mono", monospace';
    ctx.fillStyle = goldHot;
    ctx.fillText('expressions', 36, H - 46);
    ctx.fillStyle = goldMid;
    ctx.fillText('rig logic', 36, H - 18);
    ctx.fillText('GUI switch', W * 0.44, H - 18);

    tex.needsUpdate = true;
  }

  draw({});
  return { mesh, draw };
}
