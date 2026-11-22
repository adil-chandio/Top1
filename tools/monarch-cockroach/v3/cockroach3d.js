import * as THREE from 'three';

/**
 * GLM-style vector/matrix/quaternion kinematics & connected parametric mesh sculpt
 * for adult male Periplaneta americana at true millimeter scale (1 Three.js unit = 1.0 mm).
 *
 * Coordinate convention:
 *   +X = anterior (rostral, direction of forward sprint)
 *   +Y = dorsal (vertical height above floor; floor plane is Y = 0.00 mm)
 *   +Z = right lateral (+Z = right side, -Z = left side)
 *
 * Primary morphometrics (Jayaram & Full 2016, PNAS 113(8):E950-E957, PMC4776529):
 *   Body length = 31.10 mm, freestanding height = 12.52 mm, tarsus midline track = 11.89 mm.
 */
export const GLM = {
  vec3: (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z),
  clamp: (v, a, b) => Math.max(a, Math.min(b, v)),
  mix: (a, b, t) => a + (b - a) * t,
  smoothstep: (a, b, x) => {
    const t = Math.max(0, Math.min(1, (x - a) / (b - a)));
    return t * t * (3 - 2 * t);
  },
  /**
   * Analytical 2-bone IK solver in 3D using GLM vector algebra:
   * Given hip H, target T, bone lengths L1 (femur) & L2 (tibia), and preferred knee pole direction P,
   * returns exact knee joint world/local position K with smooth reach clamping.
   */
  solveTwoBoneIK(H, T, L1, L2, poleDir) {
    const dVec = new THREE.Vector3().subVectors(T, H);
    let dist = dVec.length();
    const minD = Math.abs(L1 - L2) + 0.08;
    const maxD = (L1 + L2) * 0.992;
    if (dist < 1e-5) dist = minD;
    const clamped = Math.max(minD, Math.min(maxD, dist));
    const forward = dVec.clone().divideScalar(dist);

    const cosA = Math.max(-1, Math.min(1, (L1 * L1 + clamped * clamped - L2 * L2) / (2 * L1 * clamped)));
    const sinA = Math.sqrt(Math.max(0, 1 - cosA * cosA));

    const ortho = poleDir.clone().addScaledVector(forward, -poleDir.dot(forward));
    if (ortho.lengthSq() < 1e-6) ortho.set(0, 1, 0).addScaledVector(forward, -forward.y);
    ortho.normalize();

    return H.clone()
      .addScaledVector(forward, L1 * cosA)
      .addScaledVector(ortho, L1 * sinA);
  },
};

/**
 * Build a smooth sealed parametric lofted BufferGeometry from cross-section rings.
 */
function buildLoftGeometry(rings, closedRing = true, capEnds = true) {
  const rows = rings.length;
  const cols = rings[0].length;
  const positions = [];
  const uvs = [];
  const indices = [];

  for (let r = 0; r < rows; r++) {
    const v = r / Math.max(1, rows - 1);
    for (let c = 0; c < cols; c++) {
      const u = c / (closedRing ? cols : Math.max(1, cols - 1));
      const p = rings[r][c];
      positions.push(p[0], p[1], p[2]);
      uvs.push(u, v);
    }
  }
  const stride = closedRing ? cols + 1 : cols;
  if (closedRing) {
    // Rebuild with seam duplicate column so UVs wrap cleanly without pinching
    positions.length = 0;
    uvs.length = 0;
    for (let r = 0; r < rows; r++) {
      const v = r / Math.max(1, rows - 1);
      for (let c = 0; c <= cols; c++) {
        const p = rings[r][c % cols];
        positions.push(p[0], p[1], p[2]);
        uvs.push(c / cols, v);
      }
    }
  }
  const ringCols = closedRing ? cols + 1 : cols;
  for (let r = 0; r < rows - 1; r++) {
    for (let c = 0; c < (closedRing ? cols : cols - 1); c++) {
      const a = r * ringCols + c;
      const b = a + 1;
      const d = (r + 1) * ringCols + c;
      const e = d + 1;
      indices.push(a, d, b, b, d, e);
    }
  }
  if (capEnds && closedRing) {
    const startCenterIdx = positions.length / 3;
    const c0 = rings[0].reduce((acc, p) => [acc[0] + p[0] / cols, acc[1] + p[1] / cols, acc[2] + p[2] / cols], [0, 0, 0]);
    positions.push(c0[0], c0[1], c0[2]);
    uvs.push(0.5, 0.0);
    for (let c = 0; c < cols; c++) {
      indices.push(startCenterIdx, c, c + 1);
    }
    const endCenterIdx = positions.length / 3;
    const cl = rings[rows - 1].reduce((acc, p) => [acc[0] + p[0] / cols, acc[1] + p[1] / cols, acc[2] + p[2] / cols], [0, 0, 0]);
    positions.push(cl[0], cl[1], cl[2]);
    uvs.push(0.5, 1.0);
    const base = (rows - 1) * ringCols;
    for (let c = 0; c < cols; c++) {
      indices.push(endCenterIdx, base + c + 1, base + c);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}

/**
 * Vaulted, rolled-margin Periplaneta americana pronotum shield (length ~8.6 mm, width ~10.4 mm).
 * Planar dorsal UV projection so pronotum-albedo.jpg maps symmetrically onto the dorsal shield.
 */
function buildPronotumGeometry() {
  const nu = 44, nv = 36;
  const pos = [], uv = [], idx = [];
  const L = 8.6, W = 5.35; // half-width 5.35 mm -> 10.7 mm wide shield

  for (let i = 0; i <= nu; i++) {
    const r = Math.pow(i / nu, 0.85); // denser near outer rolled rim
    for (let j = 0; j <= nv; j++) {
      const th = (j / nv) * Math.PI * 2;
      const ct = Math.cos(th), st = Math.sin(th);
      // Sub-elliptical blattodean shield: slightly narrower rostrally (+X), broader posteriorly (-X)
      const rostralTaper = ct > 0 ? (1.0 - 0.14 * ct) : (1.0 + 0.05 * (-ct));
      const x = ct * (L * 0.5) * r;
      const z = st * W * rostralTaper * r;
      // Arched dome with subtle flared marginal gutter and shallow central bilobed impression
      const dome = Math.sqrt(Math.max(0, 1.0 - r * r * 0.92)) * 2.15;
      const gutter = Math.exp(-Math.pow((r - 0.88) / 0.09, 2)) * 0.18;
      const bilobe = -0.14 * Math.exp(-Math.pow((x + 0.4) / 2.1, 2) - Math.pow((Math.abs(z) - 1.35) / 1.1, 2));
      const y = dome + gutter + bilobe - 0.35 * r * r;
      pos.push(x, y, z);
      uv.push(0.5 - (x / L) * 0.92, 0.5 + (z / (W * 2)) * 0.92);
    }
  }
  // Ventral tucked underside skirt so pronotum has realistic shell thickness from low macro angles
  const topVerts = (nu + 1) * (nv + 1);
  for (let j = 0; j <= nv; j++) {
    const rimIdx = (nu * (nv + 1) + j) * 3;
    pos.push(pos[rimIdx] * 0.94, pos[rimIdx + 1] - 0.28, pos[rimIdx + 2] * 0.94);
    uv.push(0.05, 0.05);
  }
  for (let i = 0; i < nu; i++) {
    for (let j = 0; j < nv; j++) {
      const a = i * (nv + 1) + j;
      const b = a + 1;
      const c = (i + 1) * (nv + 1) + j;
      const d = c + 1;
      idx.push(a, b, c, b, d, c);
    }
  }
  const outerBase = nu * (nv + 1);
  for (let j = 0; j < nv; j++) {
    const a = outerBase + j, b = a + 1;
    const c = topVerts + j, d = c + 1;
    idx.push(a, b, c, b, d, c);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  return geo;
}

/**
 * Asymmetric cambered leathery forewing (tegmen), length ~23.5 mm, overlapping across dorsal midline.
 */
function buildTegmenGeometry(sideSign = 1) {
  const nu = 42, nv = 22;
  const pos = [], uv = [], idx = [];
  const L = 23.8;
  for (let i = 0; i <= nu; i++) {
    const u = i / nu; // 0 = anterior humeral articulation, 1 = posterior wingtip beyond abdomen
    const x = -u * L;
    // Width profile: narrow humeral base -> broad mid-wing -> rounded elliptical apex
    const outerW = 5.65 * Math.pow(Math.sin(Math.PI * Math.min(0.98, 0.08 + 0.90 * u)), 0.58);
    // Medial overlap across midline: left tegmen (-1) overlaps deeper across Z=0 than right (+1)
    const innerZ = sideSign < 0 ? 1.85 * Math.sin(Math.PI * Math.min(1, u * 1.05)) : -1.10 * Math.sin(Math.PI * Math.min(1, u * 1.05));
    const outerZ = sideSign * outerW;

    for (let j = 0; j <= nv; j++) {
      const v = j / nv; // 0 = sutural/medial edge, 1 = costal/lateral edge
      const z = GLM.mix(innerZ, outerZ, v);
      // Cambered airfoil arch + subtle longitudinal vein flutes
      const arch = Math.sin(Math.PI * (0.18 + 0.76 * (1 - v))) * (1.55 * (1 - 0.52 * u));
      const costalDrop = -1.35 * Math.pow(v, 2.2) * (1 - 0.45 * u);
      const veinRipple = 0.045 * Math.sin(v * 26.0 + u * 6.0) * (1 - u * 0.5);
      // Left tegmen sits 0.14 mm above right tegmen along overlap zone so zero Z-fighting!
      const overlapLift = sideSign < 0 ? 0.15 * (1 - v) : 0.0;
      const y = arch + costalDrop + veinRipple + overlapLift - 0.45 * u;
      pos.push(x, y, z);
      uv.push(u, v);
    }
  }
  for (let i = 0; i < nu; i++) {
    for (let j = 0; j < nv; j++) {
      const a = i * (nv + 1) + j, b = a + 1;
      const c = (i + 1) * (nv + 1) + j, d = c + 1;
      if (sideSign > 0) idx.push(a, c, b, b, c, d);
      else idx.push(a, b, c, b, d, c);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  return geo;
}

/**
 * Single curved abdominal tergite / sternite ring shell so overlapping segments telescope realistically.
 */
function buildTergitePlateGeometry(widthHalf, chordLen, archHeight) {
  const nu = 10, nv = 24;
  const pos = [], uv = [], idx = [];
  for (let i = 0; i <= nu; i++) {
    const u = i / nu;
    const x = -u * chordLen;
    const w = widthHalf * (1.0 - 0.05 * u);
    for (let j = 0; j <= nv; j++) {
      const v = j / nv;
      const ang = (v - 0.5) * Math.PI; // -pi/2 .. +pi/2 lateral-to-lateral dorsal shell
      const z = Math.sin(ang) * w;
      const y = Math.cos(ang) * archHeight * (1.0 - 0.08 * u);
      pos.push(x, y, z);
      uv.push(u, v);
    }
  }
  for (let i = 0; i < nu; i++) {
    for (let j = 0; j < nv; j++) {
      const a = i * (nv + 1) + j, b = a + 1;
      const c = (i + 1) * (nv + 1) + j, d = c + 1;
      idx.push(a, c, b, b, c, d);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  return geo;
}

/**
 * Sculpted anatomical limb segment oriented along +Y from 0..1 (scaled & oriented per frame via GLM basis):
 * laterally flattened oval cross-section with organic proximal/distal condyle tapers.
 */
function buildLimbSegmentGeometry(profileFn, rows = 18, cols = 16) {
  const rings = [];
  for (let r = 0; r <= rows; r++) {
    const u = r / rows;
    const [rx, rz, xOff] = profileFn(u);
    const ring = [];
    for (let c = 0; c < cols; c++) {
      const a = (c / cols) * Math.PI * 2;
      ring.push([Math.cos(a) * rx + (xOff || 0), u, Math.sin(a) * rz]);
    }
    rings.push(ring);
  }
  return buildLoftGeometry(rings, true, true);
}

/**
 * Sculpted hypognathous blattodean head capsule (sub-triangular / heart-shaped).
 */
function buildHeadCapsuleGeometry() {
  const rows = 22, cols = 24;
  const rings = [];
  for (let r = 0; r <= rows; r++) {
    const u = r / rows; // 0 = vertex/occiput, 1 = labrum/mouthparts tip
    const y = 1.65 - u * 3.85;
    const width = 2.05 * Math.sin(Math.PI * Math.pow(Math.min(0.98, 0.12 + 0.84 * u), 0.72)) * (1 - 0.36 * u * u);
    const depth = 1.32 * Math.sin(Math.PI * Math.min(0.98, 0.15 + 0.80 * u)) * (1 - 0.28 * u);
    const xShift = 0.42 * Math.sin(u * Math.PI);
    const ring = [];
    for (let c = 0; c < cols; c++) {
      const a = (c / cols) * Math.PI * 2;
      ring.push([Math.cos(a) * depth + xShift, y, Math.sin(a) * width]);
    }
    rings.push(ring);
  }
  return buildLoftGeometry(rings, true, true);
}

/**
 * Create a complete, fully rigged 3D Periplaneta americana actor.
 */
export function createCockroachActor(mats, { includeWing = true } = {}) {
  const root = new THREE.Group();
  const body = new THREE.Group();
  root.add(body);

  // 1. Thoracic + ventral sternite core loft (warm translucent pleural membrane + dark sternites)
  const coreRings = [];
  const coreSpecs = [
    [11.5, 1.4, 1.1, 0.4],
    [9.2,  3.2, 1.9, 0.5],
    [5.5,  4.4, 2.3, 0.3],
    [0.5,  4.8, 2.4, 0.1],
    [-5.0, 4.9, 2.3, 0.0],
    [-10.5,4.6, 2.1, -0.1],
    [-15.2,3.8, 1.7, -0.1],
    [-18.6,2.3, 1.0, -0.1],
    [-20.2,0.8, 0.4, -0.1],
  ];
  for (const [x, rz, ry, y0] of coreSpecs) {
    const ring = [];
    for (let c = 0; c < 20; c++) {
      const a = (c / 20) * Math.PI * 2;
      ring.push([x, y0 + Math.sin(a) * ry, Math.cos(a) * rz]);
    }
    coreRings.push(ring);
  }
  const coreMesh = new THREE.Mesh(buildLoftGeometry(coreRings, true, true), mats.pleuralNaturalMat);
  coreMesh.castShadow = true;
  coreMesh.receiveShadow = true;
  body.add(coreMesh);

  // 2. Pronotum Shield Pivot (at x = +7.8 mm, overhanging head!)
  const pronotumPivot = new THREE.Group();
  pronotumPivot.position.set(7.8, 2.15, 0);
  const pronotumMesh = new THREE.Mesh(buildPronotumGeometry(), mats.pronotumMat);
  pronotumMesh.castShadow = true;
  pronotumMesh.receiveShadow = true;
  pronotumPivot.add(pronotumMesh);
  body.add(pronotumPivot);

  // 3. Hypognathous Head Capsule + Reniform Compound Eyes + Ocelli + Palps
  const headPivot = new THREE.Group();
  headPivot.position.set(10.6, 1.15, 0);
  headPivot.rotation.z = 0.32; // tucked downward-angled blattodean head
  const headMesh = new THREE.Mesh(buildHeadCapsuleGeometry(), mats.headMat);
  headMesh.castShadow = true;
  headPivot.add(headMesh);

  const eyeGeo = new THREE.SphereGeometry(0.88, 18, 14);
  eyeGeo.scale(0.76, 1.28, 0.62);
  const ocellusGeo = new THREE.SphereGeometry(0.20, 10, 8);
  for (const s of [-1, 1]) {
    const eye = new THREE.Mesh(eyeGeo, mats.eyeMat);
    eye.position.set(0.58, 0.45, s * 1.52);
    eye.rotation.x = s * 0.28;
    eye.rotation.z = -0.22;
    headPivot.add(eye);

    const ocellus = new THREE.Mesh(ocellusGeo, mats.aroliumMat);
    ocellus.position.set(1.12, 0.62, s * 0.78);
    headPivot.add(ocellus);

    // Segmented maxillary palp
    const palp = new THREE.Mesh(new THREE.CapsuleGeometry(0.11, 1.35, 4, 8), mats.legMat);
    palp.position.set(0.75, -2.05, s * 0.62);
    palp.rotation.z = -0.55;
    palp.rotation.x = s * 0.25;
    headPivot.add(palp);
  }
  body.add(headPivot);

  // 4. Sweeping 28-segment Tapering Filiform Antennae (34 mm long!)
  const ANT_SEGS = 28;
  const antTotalMeshCount = 2 * ANT_SEGS;
  const antSegGeo = new THREE.CylinderGeometry(0.68, 1.0, 1.0, 7, 1, false);
  antSegGeo.translate(0, 0.5, 0);
  const antennaeInst = new THREE.InstancedMesh(antSegGeo, mats.legMat, antTotalMeshCount);
  antennaeInst.castShadow = true;
  antennaeInst.frustumCulled = false;
  root.add(antennaeInst);

  // 5. Overlapping Segmented Abdominal Tergites + Posterior Cerci
  const tergitePivots = [];
  for (let i = 0; i < 8; i++) {
    const u = i / 7;
    const wHalf = 5.15 * Math.sin(Math.PI * (0.24 + 0.66 * (1 - u * 0.72)));
    const chord = 2.95 - 0.65 * u;
    const arch = 1.45 * (1 - 0.48 * u);
    const g = new THREE.Group();
    g.position.set(1.2 - i * 2.55, 1.35 - i * 0.11, 0);
    const m = new THREE.Mesh(buildTergitePlateGeometry(wHalf, chord, arch), mats.tergiteMat);
    m.castShadow = true;
    m.receiveShadow = true;
    g.add(m);
    body.add(g);
    tergitePivots.push(g);
  }

  // Paired 12-segment Posterior Sensory Cerci
  const cerciGroup = new THREE.Group();
  cerciGroup.position.set(-19.2, 0.35, 0);
  for (const s of [-1, 1]) {
    const cercus = new THREE.Group();
    cercus.rotation.y = -s * 0.42;
    cercus.rotation.z = -0.10;
    for (let k = 0; k < 10; k++) {
      const r0 = 0.36 * Math.pow(1 - k / 11, 0.85);
      const r1 = 0.36 * Math.pow(1 - (k + 1) / 11, 0.85);
      const seg = new THREE.Mesh(new THREE.CylinderGeometry(r1, r0, 0.48, 8), mats.legMat);
      seg.rotation.z = Math.PI / 2;
      seg.position.set(-k * 0.45, k * 0.03, s * (0.95 + k * 0.04));
      cercus.add(seg);
    }
    cerciGroup.add(cercus);
  }
  body.add(cerciGroup);

  // 6. Overlapping Veined Forewings (Left & Right Tegmina)
  const tegmenL = new THREE.Mesh(buildTegmenGeometry(-1), mats.tegminaMat);
  const tegmenR = new THREE.Mesh(buildTegmenGeometry(1), mats.tegminaMat);
  tegmenL.position.set(4.6, 2.35, 0);
  tegmenR.position.set(4.6, 2.35, 0);
  tegmenL.castShadow = tegmenR.castShadow = true;
  tegmenL.receiveShadow = tegmenR.receiveShadow = true;
  tegmenL.visible = tegmenR.visible = includeWing;
  body.add(tegmenL, tegmenR);

  // 7. Six Complete Articulated Arthropod Legs + 168 Instanced 3D Spines
  const coxaGeo = buildLimbSegmentGeometry((u) => [
    0.95 * (1 - 0.38 * u),
    0.52 * (1 - 0.25 * u),
    0.0,
  ]);
  const femurGeo = buildLimbSegmentGeometry((u) => {
    const swell = Math.sin(Math.PI * Math.pow(u, 0.68));
    return [0.36 + 0.58 * swell, 0.24 + 0.28 * swell, 0.0];
  });
  const tibiaGeo = buildLimbSegmentGeometry((u) => [
    0.34 - 0.08 * u + 0.06 * Math.pow(u, 3),
    0.26 - 0.06 * u,
    0.0,
  ]);
  const tarsomereGeo = buildLimbSegmentGeometry((u) => [
    0.20 * (1 - 0.15 * u) + 0.04,
    0.17 * (1 - 0.15 * u) + 0.03,
    0.0,
  ], 8, 10);

  // Curved keratin claw pair + soft pale arolium pad
  const clawRigProto = new THREE.Group();
  const arolium = new THREE.Mesh(new THREE.SphereGeometry(0.22, 10, 8), mats.aroliumMat);
  arolium.scale.set(1.25, 0.55, 1.05);
  arolium.position.set(0.18, 0.05, 0);
  clawRigProto.add(arolium);
  for (const cs of [-1, 1]) {
    const clawPts = [];
    for (let k = 0; k <= 8; k++) {
      const t = k / 8;
      clawPts.push(new THREE.Vector3(t * 0.68, 0.12 * Math.sin(t * 2.2) - 0.36 * t * t, cs * (0.14 + 0.18 * t)));
    }
    const curve = new THREE.CatmullRomCurve3(clawPts);
    const clawGeo = new THREE.TubeGeometry(curve, 8, 0.065, 6, false);
    const clawMesh = new THREE.Mesh(clawGeo, mats.spineMat);
    clawRigProto.add(clawMesh);
  }

  // Leg definitions: [pairIndex (0=pro, 1=meso, 2=meta), sideSign (-1=L, +1=R)]
  const LEG_SPECS = [
    { name: 'L1', pair: 0, side: -1, mount: [6.8,  0.55, -2.15], femurLen: 5.4,  tibiaLen: 4.8,  tarsusLen: 3.4, reachX:  5.6, trackZ:  8.4 },
    { name: 'R1', pair: 0, side:  1, mount: [6.8,  0.55,  2.15], femurLen: 5.4,  tibiaLen: 4.8,  tarsusLen: 3.4, reachX:  5.6, trackZ:  8.4 },
    { name: 'L2', pair: 1, side: -1, mount: [1.8,  0.48, -2.55], femurLen: 7.2,  tibiaLen: 7.4,  tarsusLen: 4.6, reachX: -1.4, trackZ: 10.8 },
    { name: 'R2', pair: 1, side:  1, mount: [1.8,  0.48,  2.55], femurLen: 7.2,  tibiaLen: 7.4,  tarsusLen: 4.6, reachX: -1.4, trackZ: 10.8 },
    { name: 'L3', pair: 2, side: -1, mount: [-3.4, 0.45, -2.75], femurLen: 8.6,  tibiaLen: 10.4, tarsusLen: 6.1, reachX: -9.8, trackZ: 11.89 },
    { name: 'R3', pair: 2, side:  1, mount: [-3.4, 0.45,  2.75], femurLen: 8.6,  tibiaLen: 10.4, tarsusLen: 6.1, reachX: -9.8, trackZ: 11.89 },
  ];

  const legs = LEG_SPECS.map((spec) => {
    const coxa = new THREE.Mesh(coxaGeo, mats.legMat);
    const femur = new THREE.Mesh(femurGeo, mats.legMat);
    const tibia = new THREE.Mesh(tibiaGeo, mats.legMat);
    const tarsomeres = Array.from({ length: 5 }, () => {
      const m = new THREE.Mesh(tarsomereGeo, mats.legMat);
      m.castShadow = true;
      root.add(m);
      return m;
    });
    const claws = clawRigProto.clone();
    coxa.castShadow = femur.castShadow = tibia.castShadow = true;
    root.add(coxa, femur, tibia, claws);
    return { spec, coxa, femur, tibia, tarsomeres, claws, worldLandmarks: {} };
  });

  // 168 Sharp Conical 3D Spines (24 tibial spines in 3 rows + 4 ventral femoral spines per leg)
  const SPINES_PER_LEG = 28;
  const spineGeo = new THREE.ConeGeometry(0.135, 1.0, 6);
  spineGeo.translate(0, 0.5, 0);
  const spinesInst = new THREE.InstancedMesh(spineGeo, mats.spineMat, legs.length * SPINES_PER_LEG);
  spinesInst.castShadow = true;
  spinesInst.frustumCulled = false;
  root.add(spinesInst);

  // Reusable scratch math objects
  const upY = new THREE.Vector3(0, 1, 0);
  const tmpDir = new THREE.Vector3();
  const tmpQ = new THREE.Quaternion();
  const tmpS = new THREE.Vector3();
  const tmpM = new THREE.Matrix4();

  function orientSegment(mesh, pA, pB, radiusScale = 1.0) {
    tmpDir.subVectors(pB, pA);
    const len = Math.max(1e-4, tmpDir.length());
    tmpDir.divideScalar(len);
    mesh.position.copy(pA);
    mesh.quaternion.setFromUnitVectors(upY, tmpDir);
    mesh.scale.set(radiusScale, len, radiusScale);
  }

  /**
   * Update complete 3D cockroach anatomy for the given biomechanical state:
   *   ceilingMm: effective confinement height [3.0 .. 15.0]
   *   worldX, worldZ, yaw: root world placement
   *   phase: continuous stride phase (1.0 = one full 61.05 ms stride cycle)
   *   gaitOverride: 'tripod' | 'oar' | 'stand' | 'wedge'
   *   antennaProbe: 0..1 slot-probing dip
   *   headPitch: extra head pitch (rad)
   *   pronotumRoll: slight roll for Stage 3 slot entry (rad)
   *   spineOnlyMode: if true, keep tarsi elevated softly for schematic traction beat
   */
  function update(state) {
    const {
      ceilingMm = 12.52,
      worldX = 0,
      worldZ = 0,
      yaw = 0,
      bodyPitch = 0,
      phase = 0,
      gaitMode = ceilingMm <= 4.3 ? 'oar' : 'tripod',
      strideAmp = 1.0,
      antennaProbe = 0.0,
      headPitch = 0.0,
      pronotumRoll = 0.0,
      time = 0.0,
      floorY = 0.0,
    } = state;

    // 1. Solve confinement body height & compression (matching rig.py Table S1!)
    let ventralClearance, compAlpha;
    if (ceilingMm >= 9.0) {
      const t = GLM.clamp((ceilingMm - 9.0) / (12.52 - 9.0), 0, 1);
      ventralClearance = 0.55 + t * (3.72 - 0.55);
      compAlpha = 0.0;
    } else if (ceilingMm > 6.0) {
      const t = (ceilingMm - 6.0) / 3.0;
      ventralClearance = 0.12 + t * 0.43;
      compAlpha = (1 - t) * 0.30;
    } else {
      ventralClearance = 0.05;
      compAlpha = GLM.clamp(0.30 + 0.70 * ((6.0 - ceilingMm) / 2.8), 0.30, 1.0);
    }

    // Body height scale & Poisson-like lateral expansion under confinement
    const vertScale = 1.0 - 0.54 * compAlpha;
    const latScale = 1.0 + 0.24 * compAlpha;
    const lenScale = 1.0 + 0.045 * compAlpha;

    const bodyBaseY = floorY + ventralClearance + 1.55 * vertScale;
    body.position.set(worldX, bodyBaseY, worldZ);
    body.rotation.set(pronotumRoll * 0.45, yaw, bodyPitch);
    body.scale.set(lenScale, vertScale, latScale);

    // Pronotum & Head subtle articulation
    pronotumPivot.rotation.set(pronotumRoll * 0.65, 0, -0.08 * compAlpha + 0.05 * Math.sin(phase * Math.PI * 2));
    headPivot.rotation.set(0, 0.06 * Math.sin(time * 4.1), 0.32 - 0.26 * compAlpha + headPitch);

    // Telescoping abdominal tergite shingle fold
    for (let i = 0; i < tergitePivots.length; i++) {
      const g = tergitePivots[i];
      g.position.x = 1.2 - i * (2.55 - 0.14 * compAlpha);
      g.rotation.z = -0.04 * (1 - compAlpha);
    }
    tegmenL.rotation.x = -0.05 * compAlpha;
    tegmenR.rotation.x = 0.05 * compAlpha;

    body.updateMatrixWorld(true);

    // 2. Update 28-segment sweeping filiform antennae via GLM damped traveling wave
    let antIdx = 0;
    for (const s of [-1, 1]) {
      const socketLocal = new THREE.Vector3(1.15, 0.35, s * 0.92);
      const prevPt = socketLocal.applyMatrix4(headPivot.matrixWorld);
      const baseYaw = yaw + s * (0.34 + 0.16 * compAlpha + 0.09 * Math.sin(time * 5.7 + s));
      const baseElev = (0.22 * (1 - compAlpha) - 0.34 * antennaProbe);

      for (let k = 0; k < ANT_SEGS; k++) {
        const u = (k + 1) / ANT_SEGS;
        const segLen = 1.24 * (1 - 0.18 * u);
        const sweep = baseYaw + s * (0.48 * u * u + 0.11 * Math.sin(time * 9.5 - u * 4.8 + s * 1.2));
        const whipY = baseElev * (1 - 0.7 * u) - 0.28 * u * u * (0.4 + antennaProbe) + 0.06 * Math.sin(time * 11.2 - u * 5.5);
        const nextPt = new THREE.Vector3(
          prevPt.x + Math.cos(sweep) * segLen,
          Math.max(floorY + 0.08, prevPt.y + whipY * segLen),
          prevPt.z - Math.sin(sweep) * segLen
        );
        tmpDir.subVectors(nextPt, prevPt);
        const l = Math.max(1e-4, tmpDir.length());
        tmpQ.setFromUnitVectors(upY, tmpDir.divideScalar(l));
        const rad = 0.22 * Math.pow(1 - u * 0.86, 0.9);
        tmpS.set(rad, l, rad);
        tmpM.compose(prevPt, tmpQ, tmpS);
        antennaeInst.setMatrixAt(antIdx++, tmpM);
        prevPt.copy(nextPt);
      }
    }
    antennaeInst.instanceMatrix.needsUpdate = true;

    // 3. Solve all 6 Arthropod Legs + 5-Segment Tarsi + 168 Individual 3D Spines!
    const tibialSpineMode = ceilingMm <= 4.65;
    const cosY = Math.cos(yaw), sinY = Math.sin(yaw);
    const toWorld = (lx, ly, lz) => new THREE.Vector3(
      worldX + lx * cosY + lz * sinY,
      floorY + ly,
      worldZ - lx * sinY + lz * cosY
    );

    let spineIdx = 0;
    const landmarks = {};

    for (let li = 0; li < legs.length; li++) {
      const leg = legs[li];
      const { pair, side, mount, femurLen, tibiaLen, tarsusLen, reachX, trackZ } = leg.spec;

      // Gait phase: alternating tripod (L1,R2,L3 vs R1,L2,R3) OR synchronous mesothoracic oar push at 4 mm!
      let legPhase = phase;
      if (gaitMode === 'oar') {
        if (pair === 1) legPhase = phase; // Both middle legs row synchronously like oars!
        else legPhase = phase + (side > 0 ? 0.35 : 0.72) + pair * 0.18;
      } else {
        const tripodGroup = (pair + (side > 0 ? 1 : 0)) % 2;
        legPhase = phase + tripodGroup * 0.5;
      }
      const cyc = ((legPhase % 1) + 1) % 1;
      // Stance occupies 68% of cycle (0..0.68), swing 32% (0.68..1.0)
      const inStance = strideAmp < 0.02 ? true : cyc < 0.68;
      const swingU = inStance ? 0 : (cyc - 0.68) / 0.32;
      const stanceU = inStance ? (cyc / 0.68) : 0;
      const strideLen = (pair === 2 ? 5.6 : pair === 1 ? 4.8 : 3.8) * strideAmp * (tibialSpineMode ? 0.72 : 1.0);
      const strideOffsetX = strideAmp < 0.02
        ? 0
        : inStance
          ? GLM.mix(0.5 * strideLen, -0.5 * strideLen, stanceU)
          : GLM.mix(-0.5 * strideLen, 0.5 * strideLen, GLM.smoothstep(0, 1, swingU));
      const swingLiftY = (!inStance && strideAmp >= 0.02)
        ? Math.sin(Math.PI * swingU) * Math.min(1.65, Math.max(0.28, (ceilingMm - 2.6) * 0.25))
        : 0.0;

      // Coxa body mount -> trochanter hip joint
      const mountWorld = new THREE.Vector3(...mount).applyMatrix4(body.matrixWorld);
      const hipLocalX = mount[0] * lenScale - 0.55;
      const hipLocalZ = side * (Math.abs(mount[2]) * latScale + 0.85);
      const hipLocalY = Math.max(0.42, (bodyBaseY - floorY) - 0.45 * vertScale);
      const hipWorld = toWorld(hipLocalX, hipLocalY, hipLocalZ);
      orientSegment(leg.coxa, mountWorld, hipWorld, 1.0);

      // Determine distal tibia tip & tarsus/claw posture:
      // Mode A (ceilingMm > 4.65): Upright tarsal-claw stance -> distal tibia elevated (~0.85 mm), 5-segment tarsus curves down to plant claws at Y=0.00 mm!
      // Mode B (ceilingMm <= 4.65): Sprawled tibial-spine stance (>80 deg sprawl) -> distal tibia plants flat at Y=0.14 mm so backward-angled spines touch floor Y=0.00 mm, while 5-segment tarsus tips sideways & lifts claws (+0.48 mm clear of floor)!
      const sprawlTransition = GLM.smoothstep(5.4, 4.15, ceilingMm);
      const footTrackZ = side * (trackZ + 0.55 * sprawlTransition);
      const anchorX = reachX + strideOffsetX;

      const tibiaTipHeight = GLM.mix(0.95 + 0.35 * ((ceilingMm - 4.65) / 8.0), 0.18, sprawlTransition) + swingLiftY;
      const tibiaTipWorld = toWorld(anchorX - (pair === 2 ? 0.8 : 0.3), Math.max(0.16, tibiaTipHeight), footTrackZ * GLM.mix(0.86, 0.96, sprawlTransition));

      // Preferred knee pole: arched dorsolaterally when upright, splayed almost horizontally below ceiling when confined!
      const poleLocal = new THREE.Vector3(
        pair === 0 ? 0.55 : pair === 1 ? 0.10 : -0.20,
        GLM.mix(1.35, 0.22, sprawlTransition),
        side * GLM.mix(0.85, 1.85, sprawlTransition)
      );
      const poleWorld = new THREE.Vector3(
        poleLocal.x * cosY + poleLocal.z * sinY,
        poleLocal.y,
        -poleLocal.x * sinY + poleLocal.z * cosY
      ).normalize();

      const kneeWorld = GLM.solveTwoBoneIK(hipWorld, tibiaTipWorld, femurLen, tibiaLen, poleWorld);
      // Strictly clamp knee below ceilingMm - 0.28 mm so femur/tibia NEVER clip the ceiling!
      const maxKneeY = floorY + ceilingMm - 0.28;
      if (kneeWorld.y > maxKneeY) kneeWorld.y = maxKneeY;

      orientSegment(leg.femur, hipWorld, kneeWorld, pair === 2 ? 1.12 : 0.96);
      orientSegment(leg.tibia, kneeWorld, tibiaTipWorld, pair === 2 ? 1.05 : 0.92);

      // Build 5-tarsomere curved chain from tibiaTipWorld -> clawWorld
      const tarsusDirX = pair === 0 ? 0.72 : pair === 1 ? 0.18 : -0.58;
      const tarsusOutZ = side * GLM.mix(0.68, 0.96, sprawlTransition);
      const clawClearanceY = GLM.mix(0.03, 0.50, sprawlTransition) + swingLiftY * 1.12;
      const tarsusEndWorld = toWorld(
        anchorX + tarsusDirX * tarsusLen * 0.62,
        clawClearanceY,
        footTrackZ + tarsusOutZ * tarsusLen * 0.52
      );

      let prevT = tibiaTipWorld.clone();
      for (let ti = 0; ti < 5; ti++) {
        const u1 = (ti + 1) / 5;
        // Upright: tarsus arches gently down onto plantar pad/claw; Confined: tarsus tips sideways/upward off floor!
        const archCurve = GLM.mix(-0.22 * Math.sin(Math.PI * u1), 0.18 * Math.pow(u1, 1.3), sprawlTransition);
        const nextT = prevT.clone().lerp(tarsusEndWorld, 1 / (5 - ti));
        nextT.y = Math.max(floorY + 0.02, GLM.mix(tibiaTipWorld.y, tarsusEndWorld.y, u1) + archCurve);
        orientSegment(leg.tarsomeres[ti], prevT, nextT, 1.0 - ti * 0.08);
        prevT.copy(nextT);
      }

      // Position & orient paired claws + arolium at distal 5th tarsomere
      leg.claws.position.copy(tarsusEndWorld);
      const clawHeading = Math.atan2(-(tarsusEndWorld.z - tibiaTipWorld.z), tarsusEndWorld.x - tibiaTipWorld.x);
      leg.claws.rotation.set(
        side * sprawlTransition * 1.18, // claws tip sideways past 80 deg sprawl!
        clawHeading,
        sprawlTransition * 0.42
      );

      // Populate 4 ventral femoral spines + 24 backward-angled tibial spines in 3 rows!
      const femurAxis = new THREE.Vector3().subVectors(kneeWorld, hipWorld).normalize();
      for (let fs = 0; fs < 4; fs++) {
        const fu = 0.30 + 0.55 * (fs / 3);
        const baseP = hipWorld.clone().lerp(kneeWorld, fu);
        baseP.y -= 0.18;
        const sDir = new THREE.Vector3(0, -0.85, side * 0.25).addScaledVector(femurAxis, 0.35).normalize();
        tmpQ.setFromUnitVectors(upY, sDir);
        tmpS.set(0.78, 0.62, 0.78);
        tmpM.compose(baseP, tmpQ, tmpS);
        spinesInst.setMatrixAt(spineIdx++, tmpM);
      }

      const tibiaAxis = new THREE.Vector3().subVectors(tibiaTipWorld, kneeWorld).normalize();
      // Orthogonal radial basis around tibia for 3 distinct anatomical spine rows
      const tibSide = new THREE.Vector3().crossVectors(tibiaAxis, new THREE.Vector3(0, 1, 0));
      if (tibSide.lengthSq() < 1e-5) tibSide.set(0, 0, 1);
      tibSide.normalize();
      const tibDown = new THREE.Vector3().crossVectors(tibSide, tibiaAxis).normalize();
      if (tibDown.y > 0) tibDown.negate();

      let sampleSpineContact = null;
      for (let ts = 0; ts < 24; ts++) {
        const row = ts % 3; // 3 rows along tibia: ventro-medial, ventral, ventro-lateral
        const rowStep = Math.floor(ts / 3) / 7; // 8 spines per row
        const tu = 0.16 + 0.80 * rowStep;
        const rowAngle = (row - 1) * 0.58;
        const radial = tibDown.clone().multiplyScalar(Math.cos(rowAngle)).addScaledVector(tibSide, Math.sin(rowAngle));
        const baseP = kneeWorld.clone().lerp(tibiaTipWorld, tu).addScaledVector(radial, 0.20);
        // Backward/distally raked at ~38 deg along tibiaAxis + downward radial bite into floor!
        const spineDir = tibiaAxis.clone().multiplyScalar(0.76).addScaledVector(radial, 0.65).normalize();
        const spineLen = (pair === 2 ? 1.05 : 0.82) * (0.72 + 0.42 * tu);
        // Ensure spine tip kisses floor cleanly at Y = floorY without stabbing deep underground
        if (baseP.y + spineDir.y * spineLen < floorY) {
          spineDir.y = (floorY - baseP.y) / Math.max(0.25, spineLen);
          spineDir.normalize();
        }
        tmpQ.setFromUnitVectors(upY, spineDir);
        tmpS.set(0.95, spineLen, 0.95);
        tmpM.compose(baseP, tmpQ, tmpS);
        spinesInst.setMatrixAt(spineIdx++, tmpM);
        if (li === 5 && ts === 19) {
          sampleSpineContact = baseP.clone().addScaledVector(spineDir, spineLen);
        }
      }

      if (li === 5) {
        // Right metathoracic hind leg landmarks for Scene 04 macro focus & callout tracking!
        landmarks.r3Knee = kneeWorld.clone();
        landmarks.r3TibiaTip = tibiaTipWorld.clone();
        landmarks.r3Spine = sampleSpineContact || tibiaTipWorld.clone();
        landmarks.r3Claw = tarsusEndWorld.clone();
      }
    }
    spinesInst.instanceMatrix.needsUpdate = true;

    landmarks.head = new THREE.Vector3(1.2, 0, 0).applyMatrix4(headPivot.matrixWorld);
    landmarks.pronotum = new THREE.Vector3(0, 1.8, 0).applyMatrix4(pronotumPivot.matrixWorld);
    landmarks.abdomen = new THREE.Vector3(-10.0, 1.4, 0).applyMatrix4(body.matrixWorld);
    landmarks.hinge = new THREE.Vector3(-4.0, 1.8, 0).applyMatrix4(body.matrixWorld);

    return {
      compAlpha,
      ventralClearance,
      sprawlDeg: GLM.mix(52, 81.5, GLM.smoothstep(8.5, 4.0, ceilingMm)),
      tibialSpineMode,
      landmarks,
    };
  }

  return { root, body, pronotumPivot, headPivot, tegmenL, tegmenR, legs, update };
}

/**
 * Create the 3D Sagittal Exoskeleton Shingle & Arthrodial Hinge Cutaway Rig
 * (for Scene 02 frames 1963..2260 and Scene 06 load-distribution cutaway frames 7617..7928).
 * Rigid curved chitin tergite plates maintain constant chord length while translucent
 * pleated arthrodial hinge membranes fold between them!
 */
export function createSagittalCutawayRig(mats) {
  const group = new THREE.Group();

  // 7 Rigid curved dorsal sclerite plates (constant chord length, zero rubbery bending!)
  const plateSpecs = [
    { label: 'pronotum', chord: 7.4, arch: 0.55, thick: 0.42, w: 6.8 },
    { label: 'mesonotum', chord: 4.3, arch: 0.32, thick: 0.36, w: 6.6 },
    { label: 'metanotum', chord: 4.2, arch: 0.30, thick: 0.36, w: 6.5 },
    { label: 'tergite1', chord: 3.1, arch: 0.24, thick: 0.30, w: 6.1 },
    { label: 'tergite2', chord: 3.0, arch: 0.22, thick: 0.29, w: 5.8 },
    { label: 'tergite3', chord: 2.9, arch: 0.20, thick: 0.28, w: 5.3 },
    { label: 'tergite4', chord: 2.7, arch: 0.18, thick: 0.26, w: 4.7 },
  ];

  const plates = plateSpecs.map((s) => {
    // Extruded curved sclerite slab with crisp cross-section cut face on +Z camera side
    const shape = new THREE.Shape();
    const N = 16;
    for (let i = 0; i <= N; i++) {
      const u = i / N;
      const x = -u * s.chord;
      const y = Math.sin(Math.PI * u) * s.arch;
      if (i === 0) shape.moveTo(x, y);
      else shape.lineTo(x, y);
    }
    for (let i = N; i >= 0; i--) {
      const u = i / N;
      const x = -u * s.chord;
      const y = Math.sin(Math.PI * u) * s.arch - s.thick;
      shape.lineTo(x, y);
    }
    shape.closePath();
    const geo = new THREE.ExtrudeGeometry(shape, { depth: s.w, bevelEnabled: true, bevelThickness: 0.06, bevelSize: 0.05, bevelSegments: 2 });
    geo.translate(0, 0, -s.w); // Front cut plane sits cleanly at Z = 0!
    // ExtrudeGeometry group 0 = front/back cut caps (bright amber chitin cross-section), group 1 = extruded dorsal/ventral shell!
    const m = new THREE.Mesh(geo, [mats.cutFaceMat || mats.tergiteMat, mats.tergiteMat]);
    m.castShadow = true;
    m.receiveShadow = true;
    group.add(m);
    return { spec: s, mesh: m };
  });

  // Soft pleated cyan-teal arthrodial membrane hinges connecting posterior underside of plate i to anterior lip of plate i+1
  const hinges = [];
  for (let i = 0; i < plates.length - 1; i++) {
    // Accordion-pleated membrane ribbon visible clearly on the Z = 0 sagittal cut plane
    const hGroup = new THREE.Group();
    for (let p = 0; p < 3; p++) {
    const cyl = new THREE.Mesh(
        new THREE.CylinderGeometry(0.24, 0.24, plates[i + 1].spec.w * 0.96, 14),
        mats.arthrodialMat
      );
      cyl.rotation.x = Math.PI / 2;
      cyl.position.set((p - 1) * 0.26, (p % 2 === 0 ? 0.08 : -0.08), -plates[i + 1].spec.w * 0.48);
      hGroup.add(cyl);
    }
    group.add(hGroup);
    hinges.push(hGroup);
  }

  // Ventral sternite floor plates + curved anatomical internal cavity (never a flat rectangle!) + silvery tracheal tubes
  const ventralBar = new THREE.Mesh(new THREE.BoxGeometry(24.5, 0.42, 6.0), mats.cutFaceMat || mats.headMat);
  ventralBar.position.set(-1.5, 0.21, -3.0);
  group.add(ventralBar);

  // Curved anatomical sagittal tissue cross-section matching arched exoskeleton contour
  const cavityShape = new THREE.Shape();
  cavityShape.moveTo(-13.4, 0.35);
  cavityShape.lineTo(10.2, 0.35);
  cavityShape.quadraticCurveTo(9.5, 3.8, 2.5, 4.85);
  cavityShape.quadraticCurveTo(-6.2, 4.6, -13.4, 1.45);
  cavityShape.closePath();
  const cavityGeo = new THREE.ExtrudeGeometry(cavityShape, { depth: 5.5, bevelEnabled: false });
  cavityGeo.translate(0, 0, -5.55);
  const hemocoel = new THREE.Mesh(cavityGeo, mats.pleuralNaturalMat);
  group.add(hemocoel);

  // Silvery-cyan compressible tracheal tubes with bright cut-ring walls visible in the sagittal cut plane (Z = 0)
  const tracheae = Array.from({ length: 6 }, (_, i) => {
    const tMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.46, 0.46, 5.5, 18), mats.arthrodialMat);
    tMesh.rotation.x = Math.PI / 2;
    tMesh.position.set(6.5 - i * 3.5, 2.5, -2.7);
    group.add(tMesh);
    return tMesh;
  });

  // Descending crystal compression platen (for compression & 300x/900x load scenes)
  const platen = new THREE.Mesh(new THREE.BoxGeometry(28.5, 0.55, 8.8), mats.acrylicMat);
  const platenRim = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(28.5, 0.55, 8.8)),
    new THREE.LineBasicMaterial({ color: '#a8ece6', transparent: true, opacity: 0.65 })
  );
  platen.add(platenRim);
  group.add(platen);

  // Distributed load arrows (shown only during Scene 06 300x-900x load spread beat)
  const loadArrows = new THREE.Group();
  const arrowMat = new THREE.MeshBasicMaterial({ color: '#ffd187', transparent: true, opacity: 0.9 });
  for (let i = 0; i < 7; i++) {
    const ax = 8.4 - i * 3.1;
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, 1.8, 8), arrowMat);
    shaft.position.set(ax, 1.35, -1.2);
    const cone = new THREE.Mesh(new THREE.ConeGeometry(0.28, 0.62, 10), arrowMat);
    cone.rotation.z = Math.PI;
    cone.position.set(ax, 0.35, -1.2);
    loadArrows.add(shaft, cone);
  }
  group.add(loadArrows);

  function update({ compAlpha = 0.0, showPlaten = true, showLoadArrows = false } = {}) {
    const unloadedHeights = [6.4, 6.8, 6.6, 5.9, 5.4, 4.9, 4.3];
    const loadedHeights   = [3.1, 3.3, 3.2, 2.9, 2.7, 2.5, 2.3];
    let curX = 11.2;
    let peakY = 0;
    const landmarks = {};

    for (let i = 0; i < plates.length; i++) {
      const p = plates[i];
      const h0 = GLM.mix(unloadedHeights[i], loadedHeights[i], compAlpha);
      const h1 = GLM.mix(
        unloadedHeights[Math.min(plates.length - 1, i + 1)],
        loadedHeights[Math.min(plates.length - 1, i + 1)],
        compAlpha
      );
      // Rigid plate tilts on its soft hinge so its chord length NEVER changes!
      const dy = GLM.clamp((h1 + 0.34 * (1 - 0.55 * compAlpha)) - h0, -p.spec.chord * 0.5, p.spec.chord * 0.5);
      const pitch = Math.asin(dy / p.spec.chord);
      p.mesh.position.set(curX, h0, 0);
      p.mesh.rotation.set(0, 0, -pitch);
      peakY = Math.max(peakY, h0 + p.spec.arch);

      const tipX = curX - Math.cos(pitch) * p.spec.chord;
      const tipY = h0 + Math.sin(pitch) * p.spec.chord;
      if (i < hinges.length) {
        // Pleated arthrodial hinge folds into the pocket between overlapping plates!
        hinges[i].position.set(tipX + 0.55, tipY - 0.32, 0.04);
        hinges[i].scale.set(1.0 + 0.45 * compAlpha, 1.0 - 0.48 * compAlpha, 1.0);
        if (i === 2) landmarks.hinge = new THREE.Vector3(tipX + 0.55, tipY - 0.25, 0.1).applyMatrix4(group.matrixWorld);
      }
      if (i === 1) landmarks.plate = new THREE.Vector3(curX - 2.0, h0 + 0.25, 0.1).applyMatrix4(group.matrixWorld);
      // Overlapping roof-tile step
      curX = tipX + (0.95 + 0.38 * compAlpha);
    }

    const innerH = Math.max(1.6, peakY - 0.75);
    hemocoel.scale.y = innerH / 4.85;
    hemocoel.position.y = 0.04;
    for (let i = 0; i < tracheae.length; i++) {
      tracheae[i].position.y = 0.65 + innerH * (0.44 - i * 0.03);
      tracheae[i].scale.set(1.0 + 0.38 * compAlpha, 1.0, 1.0 - 0.52 * compAlpha); // elliptical tracheal compression!
    }

    platen.visible = showPlaten;
    platen.position.set(-1.5, peakY + 0.34, -2.8);
    loadArrows.visible = showLoadArrows;
    loadArrows.position.set(-1.5, peakY + 0.65, 0);
    landmarks.platen = new THREE.Vector3(-1.5, peakY + 0.34, 0).applyMatrix4(group.matrixWorld);
    return { peakY, landmarks };
  }

  return { group, update };
}
