import * as THREE from 'three';
import {
  mulberry32,
  buildNormalFromCanvas,
  buildMetricRulerTexture,
  buildWoodPlankTexture,
  setImaxLightingPreset,
  makeImaxMaterial,
  GLM,
  buildLoftGeometry,
  createGroundContactAO,
  createTexelSnappedShadowRig,
  createVolumetricLightBlade,
  createLoopLockedDustMotes,
  createStudioSoftboxEnvMap,
  buildKarooSandstoneTextures,
  buildOrganicCreatureTextures,
  createKarooRockAndDualFossilRig,
  createTriassicBurrowAndLivingPairRig,
  createFlashFloodAndPetrificationSystem,
} from '/tools/monarch-v6-imax-sdk/index.js';

/**
 * EXTINCT LIFE V7.0 AUTONOMOUS ULTRA MONARCH — "This Rock Holds Two Animals" (`BP/1/5558`)
 * Archetype: `W02_SCORCHED_FIELD_EXPEDITION` + `H1_DOCUMENTARY_LOWER_THIRD`
 *
 * Major V7 World, Physics, Prop, Shader & Biomechanical Upgrades:
 *   1. Living Paleontology Expedition Camp: Rugged 4x4 Safari Defender, wind-rippling canvas shade
 *      canopy, aluminum specimen crate, brass sieve, 3 fluttering survey ribbon stakes, 2 soaring
 *      Verreaux's black eagles, and distant swirling Karoo dust-devil thermal!
 *   2. Active S01 Excavation Action: Wooden camel-hair brush physically sweeps 3 rhythmic strokes across
 *      the boulder (`0.20s, 0.88s, 1.56s` — 1:1 Chion synchresis!), launching 64 sunlit quartz dust puffs
 *      before returning to its exact resting spot for `< 1.0 MAE` seamless loop closure!
 *   3. Physical Sandstone Cap Cleavage + High-Contrast Carved Stone Matrix + S03 Species Ghost-Silhouettes
 *      + Sequential 1-2-3 Rib Callus Illumination (`#4, #5, #6` synced to osteological modal clicks)!
 *   4. Biomechanically Alive Triassic Pair: Live vertex-deformed S-wave spine on `Broomistega`, gular
 *      throat-sac breathing, blinking eyelids, footstep sand puffs, AND `Thrinaxodon` ear-flick + sleepy
 *      eye-peek + whisker sniff + instinctive flash-flood huddle!
 */

export const FPS = 30;
export const DURATION = 36.0;
export const TOTAL_FRAMES = 1080;

// =============================================================================
// 1. PROCEDURAL DESERT TEXTURES & FIELD JOURNAL
// =============================================================================
function buildKarooDesertFloorTextures(seed = 7721) {
  const S = 512;
  const cv = document.createElement('canvas');
  cv.width = cv.height = S;
  const ctx = cv.getContext('2d');
  const rng = mulberry32(seed);

  ctx.fillStyle = '#9e5d3e';
  ctx.fillRect(0, 0, S, S);

  for (let i = 0; i < 180; i++) {
    const x = rng() * S;
    const y = rng() * S;
    const r = 18 + rng() * 64;
    const g = ctx.createRadialGradient(x, y, 2, x, y, r);
    const warm = rng() > 0.45;
    g.addColorStop(0.0, warm ? 'rgba(212,148,98,0.28)' : 'rgba(104,50,30,0.30)');
    g.addColorStop(1.0, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }

  const pts = [];
  const GRID = 7;
  for (let gy = 0; gy < GRID; gy++) {
    for (let gx = 0; gx < GRID; gx++) {
      pts.push([
        ((gx + 0.18 + rng() * 0.64) / GRID) * S,
        ((gy + 0.18 + rng() * 0.64) / GRID) * S,
      ]);
    }
  }
  ctx.strokeStyle = 'rgba(52, 22, 12, 0.65)';
  ctx.lineWidth = 2.3;
  for (let i = 0; i < pts.length; i++) {
    for (let j = i + 1; j < pts.length; j++) {
      const dx = pts[j][0] - pts[i][0];
      const dy = pts[j][1] - pts[i][1];
      if (Math.hypot(dx, dy) < (S / GRID) * 1.38) {
        const mx = (pts[i][0] + pts[j][0]) * 0.5 + (rng() - 0.5) * 8.0;
        const my = (pts[i][1] + pts[j][1]) * 0.5 + (rng() - 0.5) * 8.0;
        ctx.beginPath();
        ctx.moveTo(pts[i][0], pts[i][1]);
        ctx.quadraticCurveTo(mx, my, pts[j][0], pts[j][1]);
        ctx.stroke();
      }
    }
  }

  for (let i = 0; i < 4200; i++) {
    const x = rng() * S;
    const y = rng() * S;
    const rad = 0.6 + rng() * 2.1;
    ctx.fillStyle = rng() > 0.44 ? 'rgba(236,198,152,0.30)' : 'rgba(54,26,16,0.34)';
    ctx.beginPath();
    ctx.arc(x, y, rad, 0, Math.PI * 2);
    ctx.fill();
  }

  const albedo = new THREE.CanvasTexture(cv);
  albedo.colorSpace = THREE.SRGBColorSpace;
  albedo.wrapS = albedo.wrapT = THREE.RepeatWrapping;
  const normal = buildNormalFromCanvas(cv, 2.9, 512);
  return { albedo, normal };
}

function buildFieldNotebookPageTexture() {
  const cv = document.createElement('canvas');
  cv.width = 512;
  cv.height = 384;
  const ctx = cv.getContext('2d');

  ctx.fillStyle = '#efe4c8';
  ctx.fillRect(0, 0, 512, 384);

  ctx.strokeStyle = 'rgba(120, 138, 152, 0.34)';
  ctx.lineWidth = 1.5;
  for (let y = 56; y < 360; y += 24) {
    ctx.beginPath();
    ctx.moveTo(24, y);
    ctx.lineTo(488, y);
    ctx.stroke();
  }
  ctx.strokeStyle = 'rgba(92, 68, 42, 0.55)';
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(256, 0);
  ctx.lineTo(256, 384);
  ctx.stroke();

  ctx.fillStyle = '#2d2218';
  ctx.font = '700 22px monospace';
  ctx.fillText('KAROO BASIN · LOC 14', 32, 44);
  ctx.fillText('CAST BP/1/5558', 278, 44);
  ctx.font = '600 16px monospace';
  ctx.fillStyle = '#5c3c24';
  ctx.fillText('Lystrosaurus AZ (~250 Ma)', 32, 78);
  ctx.fillText('Beaufort Grp Siltstone', 32, 102);
  ctx.fillText('Dual vertebrate cast', 32, 126);

  ctx.strokeStyle = '#3b2e22';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.ellipse(372, 210, 84, 52, -0.15, 0, Math.PI * 2);
  ctx.stroke();
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(348, 212, 26, 0.4, Math.PI * 1.75);
  ctx.stroke();

  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function buildSubEarthStrataTexture(seed = 6612) {
  const W = 512;
  const H = 512;
  const rng = mulberry32(seed);
  const cv = document.createElement('canvas');
  cv.width = W;
  cv.height = H;
  const ctx = cv.getContext('2d');

  const bands = [
    [0.00, '#8d5336'],
    [0.14, '#734029'],
    [0.32, '#865238'],
    [0.48, '#613522'],
    [0.68, '#77452e'],
    [0.85, '#522c1c'],
    [1.00, '#442417'],
  ];
  const g = ctx.createLinearGradient(0, 0, 0, H);
  for (const [stop, col] of bands) g.addColorStop(stop, col);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);

  for (let y = 4; y < H; y += 5) {
    ctx.strokeStyle = (y % 15 === 0) ? 'rgba(232,188,138,0.18)' : 'rgba(38,18,10,0.24)';
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    for (let x = 0; x <= W; x += 16) {
      const wy = y + Math.sin(x * 0.035 + y * 0.11) * 2.6;
      if (x === 0) ctx.moveTo(x, wy);
      else ctx.lineTo(x, wy);
    }
    ctx.stroke();
  }

  for (let i = 0; i < 420; i++) {
    const x = rng() * W;
    const y = rng() * H;
    const r = 1.2 + rng() * 3.8;
    ctx.fillStyle = rng() > 0.38 ? 'rgba(218,178,132,0.18)' : 'rgba(42,20,12,0.22)';
    ctx.beginPath();
    ctx.ellipse(x, y, r * 1.5, r * 0.85, rng() * Math.PI, 0, Math.PI * 2);
    ctx.fill();
  }

  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return tex;
}

// =============================================================================
// 2. EXPEDITION CAMP, VEHICLE, CLOTH CANOPY, SURVEY RIBBONS & TOOLS
// =============================================================================
function buildEstwingRockHammer() {
  const grp = new THREE.Group();
  const steelMat = makeImaxMaterial({
    color: '#959fa8',
    specular: '#fff4e0',
    specPower: 0.80,
    rimTint: [0.96, 0.78, 0.52],
    rimStrength: 0.30,
  });
  const leatherMat = makeImaxMaterial({
    color: '#5a3219',
    specular: '#d89b68',
    specPower: 0.44,
    rimTint: [0.85, 0.55, 0.30],
    rimStrength: 0.18,
  });

  const shaftRings = [];
  for (let r = 0; r <= 12; r++) {
    const u = r / 12;
    const y = u * 0.30;
    const wx = 0.012 - 0.003 * Math.sin(u * Math.PI);
    const wz = 0.0055;
    const ring = [];
    for (let c = 0; c < 12; c++) {
      const a = (c / 12) * Math.PI * 2;
      ring.push([Math.cos(a) * wx, y, Math.sin(a) * wz]);
    }
    shaftRings.push(ring);
  }
  const shaft = new THREE.Mesh(buildLoftGeometry(shaftRings, true, true), steelMat);
  shaft.castShadow = true;
  grp.add(shaft);

  const gripRings = [];
  for (let r = 0; r <= 14; r++) {
    const u = r / 14;
    const y = 0.015 + u * 0.135;
    const swell = 1.0 + 0.18 * Math.sin(u * Math.PI) + 0.03 * Math.sin(u * Math.PI * 12.0);
    const ring = [];
    for (let c = 0; c < 14; c++) {
      const a = (c / 14) * Math.PI * 2;
      ring.push([Math.cos(a) * 0.0165 * swell, y, Math.sin(a) * 0.0125 * swell]);
    }
    gripRings.push(ring);
  }
  const grip = new THREE.Mesh(buildLoftGeometry(gripRings, true, true), leatherMat);
  grip.castShadow = true;
  grp.add(grip);

  const headRings = [];
  for (let r = 0; r <= 16; r++) {
    const u = r / 16;
    const x = GLM.mix(-0.085, 0.125, u);
    const pickTaper = u > 0.55 ? Math.max(0.08, 1.0 - (u - 0.55) / 0.45) : 1.0;
    const drop = u > 0.55 ? -0.026 * Math.pow((u - 0.55) / 0.45, 1.8) : 0.0;
    const rad = 0.016 * pickTaper;
    const ring = [];
    for (let c = 0; c < 12; c++) {
      const a = (c / 12) * Math.PI * 2;
      ring.push([x, 0.30 + drop + Math.sin(a) * rad, Math.cos(a) * rad * 0.88]);
    }
    headRings.push(ring);
  }
  const head = new THREE.Mesh(buildLoftGeometry(headRings, true, true), steelMat);
  head.castShadow = true;
  grp.add(head);

  return grp;
}

function buildAnimatedBrushAndStaticChisel() {
  const woodTex = buildWoodPlankTexture(404);
  const woodMat = makeImaxMaterial({
    color: '#bc864e',
    map: woodTex.albedo,
    normalMap: woodTex.normal,
    normalScale: 0.48,
    specPower: 0.38,
  });
  const ferruleMat = makeImaxMaterial({ color: '#cfa34e', specular: '#fff5d6', specPower: 0.76 });
  const bristleMat = makeImaxMaterial({ color: '#dec99e', specPower: 0.20 });

  const brushRig = new THREE.Group();
  const handleRings = [];
  for (let r = 0; r <= 12; r++) {
    const u = r / 12;
    const z = GLM.mix(-0.14, 0.05, u);
    const wx = 0.010 + 0.016 * GLM.smoothstep(0.45, 1.0, u);
    const wy = 0.007 + 0.003 * Math.sin(u * Math.PI);
    const ring = [];
    for (let c = 0; c < 12; c++) {
      const a = (c / 12) * Math.PI * 2;
      ring.push([Math.cos(a) * wx, Math.sin(a) * wy, z]);
    }
    handleRings.push(ring);
  }
  const handle = new THREE.Mesh(buildLoftGeometry(handleRings, true, true), woodMat);
  handle.castShadow = true;
  brushRig.add(handle);

  const ferrule = new THREE.Mesh(new THREE.BoxGeometry(0.058, 0.016, 0.026), ferruleMat);
  ferrule.position.set(0, 0, 0.062);
  ferrule.castShadow = true;
  brushRig.add(ferrule);

  const bristles = new THREE.Mesh(new THREE.BoxGeometry(0.060, 0.014, 0.056), bristleMat);
  bristles.position.set(0, 0, 0.102);
  bristles.castShadow = true;
  brushRig.add(bristles);

  const chiselGrp = new THREE.Group();
  const chiselMat = makeImaxMaterial({ color: '#6e7780', specular: '#e4ecf2', specPower: 0.68 });
  const chisel = new THREE.Mesh(new THREE.CylinderGeometry(0.0085, 0.0095, 0.22, 8), chiselMat);
  chisel.rotation.x = Math.PI * 0.5;
  chisel.rotation.z = 0.24;
  chisel.position.set(0.775, 0.146, 0.60);
  chisel.castShadow = true;
  chiselGrp.add(chisel);

  return { brushRig, bristles, chiselGrp };
}

function buildFieldNotebook() {
  const grp = new THREE.Group();
  const coverMat = makeImaxMaterial({ color: '#6b583e', specPower: 0.18 });
  const pageMat = makeImaxMaterial({
    color: '#f5ebd4',
    map: buildFieldNotebookPageTexture(),
    specPower: 0.14,
  });

  const cover = new THREE.Mesh(new THREE.BoxGeometry(0.29, 0.012, 0.21), coverMat);
  cover.castShadow = true;
  cover.receiveShadow = true;
  grp.add(cover);

  const pages = new THREE.Mesh(new THREE.BoxGeometry(0.276, 0.010, 0.196), pageMat);
  pages.position.y = 0.009;
  pages.receiveShadow = true;
  grp.add(pages);

  const flutterPage = new THREE.Mesh(
    new THREE.PlaneGeometry(0.132, 0.192, 8, 4),
    makeImaxMaterial({ color: '#f3e7cb', specPower: 0.12, side: THREE.DoubleSide })
  );
  flutterPage.rotation.x = -Math.PI / 2;
  flutterPage.position.set(0.068, 0.016, 0.0);
  grp.add(flutterPage);

  const pencil = new THREE.Mesh(
    new THREE.CylinderGeometry(0.0042, 0.0042, 0.165, 6),
    makeImaxMaterial({ color: '#d89b2b', specPower: 0.35 })
  );
  pencil.rotation.z = Math.PI * 0.5;
  pencil.rotation.y = 0.38;
  pencil.position.set(-0.04, 0.020, 0.04);
  pencil.castShadow = true;
  grp.add(pencil);

  return { grp, flutterPage };
}

function buildExpedition4x4Vehicle() {
  // Sculpted Paleontology Safari Field Tent (Catenary Canvas Ridge Tent) + Brass Surveyor Theodolite Tripod!
  const grp = new THREE.Group();
  const canvasMat = makeImaxMaterial({
    color: '#cbb48e',
    specular: '#f7e6c8',
    specPower: 0.14,
    rimTint: [0.98, 0.82, 0.56],
    rimStrength: 0.28,
    side: THREE.DoubleSide,
  });
  const woodMat = makeImaxMaterial({ color: '#6b492b', specPower: 0.22 });
  const brassMat = makeImaxMaterial({ color: '#c89b48', specular: '#fff4d4', specPower: 0.78 });

  const tentRings = [];
  for (let r = 0; r <= 16; r++) {
    const u = r / 16;
    const z = (u - 0.5) * 2.35;
    const ridgeSag = 0.06 * Math.sin(u * Math.PI);
    const topY = 1.42 - ridgeSag;
    const midSag = 0.08 * Math.sin(u * Math.PI);
    tentRings.push([
      [-1.08, 0.02, z],
      [-0.56, 0.68 - midSag, z],
      [ 0.00, topY, z],
      [ 0.56, 0.68 - midSag, z],
      [ 1.08, 0.02, z],
    ]);
  }
  const tentFly = new THREE.Mesh(buildLoftGeometry(tentRings, false, false), canvasMat);
  tentFly.castShadow = true;
  grp.add(tentFly);

  const innerShade = new THREE.Mesh(
    new THREE.ConeGeometry(0.76, 1.32, 3),
    makeImaxMaterial({ color: '#2b1a10', specPower: 0.05 })
  );
  innerShade.scale.set(1.1, 1.0, 1.8);
  innerShade.position.set(0, 0.64, 0);
  grp.add(innerShade);

  for (const pz of [-1.18, 1.18]) {
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.026, 1.48, 8), woodMat);
    pole.position.set(0, 0.74, pz);
    grp.add(pole);
  }

  const tripod = new THREE.Group();
  tripod.position.set(1.62, 0.0, 0.95);
  for (let l = 0; l < 3; l++) {
    const a = (l / 3) * Math.PI * 2 + 0.4;
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.010, 1.18, 6), woodMat);
    leg.position.set(Math.cos(a) * 0.18, 0.54, Math.sin(a) * 0.18);
    leg.rotation.z = Math.cos(a) * 0.28;
    leg.rotation.x = -Math.sin(a) * 0.28;
    tripod.add(leg);
  }
  const scopeBase = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.065, 0.08, 12), brassMat);
  scopeBase.position.y = 1.08;
  tripod.add(scopeBase);
  const scopeTube = new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.032, 0.24, 12), brassMat);
  scopeTube.rotation.z = Math.PI * 0.48;
  scopeTube.position.y = 1.16;
  tripod.add(scopeTube);
  grp.add(tripod);

  return grp;
}

function buildWindCanopyAndCampGear() {
  const grp = new THREE.Group();
  const poleMat = makeImaxMaterial({ color: '#6e4e30', specPower: 0.20 });
  const crateMat = makeImaxMaterial({ color: '#a8afb5', specular: '#ffffff', specPower: 0.65 });
  const canteenMat = makeImaxMaterial({ color: '#687664', specPower: 0.38 });

  // 4 Angled Wooden Shade Poles (`x = 1.65..3.35, z = -2.2..-3.6`)
  const corners = [
    [-0.85, 1.48,  0.65],
    [ 0.85, 1.42,  0.65],
    [-0.85, 1.24, -0.65],
    [ 0.85, 1.18, -0.65],
  ];
  for (const [cx, ch, cz] of corners) {
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.026, ch, 8), poleMat);
    pole.position.set(cx, ch * 0.5, cz);
    pole.castShadow = true;
    grp.add(pole);
  }

  // Deformable Sun-Bleached Canvas Tarp (`16x12` grid updated in real time for wind ripple!)
  const tarpGeo = new THREE.PlaneGeometry(1.78, 1.38, 16, 12);
  tarpGeo.rotateX(-Math.PI * 0.5);
  const basePos = Float32Array.from(tarpGeo.attributes.position.array);
  const tarpMat = makeImaxMaterial({
    color: '#dfd0b0',
    specular: '#fff4dc',
    specPower: 0.14,
    rimTint: [0.98, 0.84, 0.58],
    rimStrength: 0.28,
    side: THREE.DoubleSide,
  });
  const tarpMesh = new THREE.Mesh(tarpGeo, tarpMat);
  tarpMesh.castShadow = true;
  grp.add(tarpMesh);

  // Aluminum Specimen Crate + Geological Sieve + Field Canteen under canopy
  const crate = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.34, 0.42), crateMat);
  crate.position.set(-0.25, 0.17, 0.15);
  crate.rotation.y = 0.28;
  crate.castShadow = true;
  grp.add(crate);

  const sieveRim = new THREE.Mesh(new THREE.TorusGeometry(0.18, 0.024, 8, 22), poleMat);
  sieveRim.rotation.x = Math.PI * 0.42;
  sieveRim.position.set(0.35, 0.08, 0.28);
  grp.add(sieveRim);

  const canteen = new THREE.Mesh(new THREE.SphereGeometry(0.085, 12, 10), canteenMat);
  canteen.scale.set(1.0, 1.25, 0.62);
  canteen.position.set(0.16, 0.09, 0.44);
  grp.add(canteen);

  function updateCloth(time) {
    const w0 = (Math.PI * 2.0) / DURATION;
    const pos = tarpGeo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const bx = basePos[i * 3 + 0];
      const bz = basePos[i * 3 + 2];
      const uX = (bx + 0.89) / 1.78;
      const uZ = (bz + 0.69) / 1.38;
      // Bilinear height across the 4 sloped corner poles + catenary sag + loop-locked wind wave!
      const hFront = GLM.mix(1.24, 1.18, uX);
      const hBack  = GLM.mix(1.48, 1.42, uX);
      const baseH = GLM.mix(hFront, hBack, uZ);
      const edgePin = Math.sin(uX * Math.PI) * Math.sin(uZ * Math.PI);
      const sag = -0.065 * edgePin;
      const wave = (0.026 * Math.sin(4.0 * w0 * time - uX * 4.5 + uZ * 2.2)
                  + 0.014 * Math.cos(8.0 * w0 * time - uZ * 5.5)) * (0.25 + 0.75 * edgePin);
      pos.setY(i, baseH + sag + wave);
    }
    pos.needsUpdate = true;
    tarpGeo.computeVertexNormals();
  }
  updateCloth(0);

  return { grp, updateCloth };
}

function buildSurveyStakeWithRibbon(seedPhase = 0.0) {
  const grp = new THREE.Group();
  const stake = new THREE.Mesh(
    new THREE.CylinderGeometry(0.011, 0.008, 0.42, 6),
    makeImaxMaterial({ color: '#8f6239', specPower: 0.16 })
  );
  stake.position.y = 0.19;
  stake.castShadow = true;
  grp.add(stake);

  const ribGeo = new THREE.PlaneGeometry(0.19, 0.024, 10, 1);
  ribGeo.translate(0.095, 0, 0);
  const baseRib = Float32Array.from(ribGeo.attributes.position.array);
  const ribMat = makeImaxMaterial({
    color: '#d9532f',
    specular: '#ffd6b8',
    specPower: 0.28,
    side: THREE.DoubleSide,
  });
  const ribbon = new THREE.Mesh(ribGeo, ribMat);
  ribbon.position.set(0, 0.36, 0);
  grp.add(ribbon);

  function updateRibbon(time) {
    const w0 = (Math.PI * 2.0) / DURATION;
    const pos = ribGeo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const bx = baseRib[i * 3 + 0];
      const by = baseRib[i * 3 + 1];
      const u = bx / 0.19;
      const pin = Math.pow(u, 1.3);
      const dy = -0.032 * pin + 0.022 * Math.sin(6.0 * w0 * time - u * 5.0 + seedPhase) * pin;
      const dz = 0.036 * Math.cos(5.0 * w0 * time - u * 4.2 + seedPhase * 1.4) * pin;
      pos.setXYZ(i, bx, by + dy, dz);
    }
    pos.needsUpdate = true;
  }
  updateRibbon(0);
  return { grp, updateRibbon };
}

function buildSoaringEaglesAndDustDevil() {
  const grp = new THREE.Group();
  const eagleMat = new THREE.MeshBasicMaterial({ color: '#2b1c14', side: THREE.DoubleSide });

  function makeEagle() {
    const eg = new THREE.Group();
    const wingL = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.11, 4, 1), eagleMat);
    wingL.position.set(-0.20, 0.02, 0);
    wingL.rotation.x = -Math.PI * 0.42;
    wingL.rotation.z = 0.16;
    const wingR = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.11, 4, 1), eagleMat);
    wingR.position.set(0.20, 0.02, 0);
    wingR.rotation.x = -Math.PI * 0.42;
    wingR.rotation.z = -0.16;
    const body = new THREE.Mesh(new THREE.ConeGeometry(0.032, 0.22, 5), eagleMat);
    body.rotation.x = Math.PI * 0.5;
    eg.add(wingL, wingR, body);
    return { eg, wingL, wingR };
  }

  const eagle1 = makeEagle();
  const eagle2 = makeEagle();
  grp.add(eagle1.eg, eagle2.eg);

  // Swirling Karoo Thermal Dust-Devil Column in distant badlands (`x = 5.4, z = -12.8`)
  const DEVIL_COUNT = 44;
  const devilGeo = new THREE.SphereGeometry(0.09, 6, 5);
  const devilMat = new THREE.MeshBasicMaterial({
    color: '#d9ad7c',
    transparent: true,
    opacity: 0.24,
    depthWrite: false,
  });
  const devilMesh = new THREE.InstancedMesh(devilGeo, devilMat, DEVIL_COUNT);
  devilMesh.frustumCulled = false;
  grp.add(devilMesh);

  const dummy = new THREE.Object3D();
  function updateSkyLife(time) {
    const w0 = (Math.PI * 2.0) / DURATION; // Exact 36.0s periodic loop!
    const a1 = w0 * time + 0.5;
    eagle1.eg.position.set(-3.2 + Math.cos(a1) * 4.2, 4.45 + 0.22 * Math.sin(2.0 * a1), -14.2 + Math.sin(a1) * 1.8);
    eagle1.eg.rotation.y = -a1 + Math.PI * 0.5;
    eagle1.eg.rotation.z = 0.22 * Math.cos(a1);
    const flap1 = 0.14 + 0.08 * Math.sin(9.0 * w0 * time);
    eagle1.wingL.rotation.z = flap1;
    eagle1.wingR.rotation.z = -flap1;

    const a2 = w0 * time + 2.8;
    eagle2.eg.position.set(4.1 + Math.cos(a2) * 3.6, 4.85 + 0.18 * Math.cos(2.0 * a2), -15.4 + Math.sin(a2) * 1.5);
    eagle2.eg.rotation.y = -a2 + Math.PI * 0.5;
    eagle2.eg.rotation.z = 0.18 * Math.cos(a2);

    for (let i = 0; i < DEVIL_COUNT; i++) {
      const u = i / DEVIL_COUNT;
      const spin = 5.0 * w0 * time + u * Math.PI * 8.0;
      const rad = 0.14 + u * 0.62;
      dummy.position.set(
        5.2 + Math.cos(spin) * rad,
        0.15 + u * 2.85,
        -12.5 + Math.sin(spin) * rad * 0.7
      );
      dummy.scale.setScalar((0.6 + u * 1.6) * (1.0 - 0.35 * u));
      dummy.updateMatrix();
      devilMesh.setMatrixAt(i, dummy.matrix);
    }
    devilMesh.instanceMatrix.needsUpdate = true;
  }
  updateSkyLife(0);
  return { grp, updateSkyLife };
}

function buildKarooMesaRange(sandTex) {
  const grp = new THREE.Group();
  const configs = [
    { x: -9.2, z: -16.8, w: 13.5, h: 2.55, d: 5.2, haze: 0.34, seed: 1.1 },
    { x:  1.2, z: -19.6, w: 16.4, h: 2.95, d: 5.8, haze: 0.46, seed: 2.7 },
    { x: 10.4, z: -17.2, w: 14.2, h: 2.68, d: 5.4, haze: 0.38, seed: 4.3 },
  ];
  for (const cfg of configs) {
    const mesaMat = makeImaxMaterial({
      color: new THREE.Color('#9c593a').lerp(new THREE.Color('#d4b18c'), cfg.haze),
      map: sandTex.albedo,
      normalMap: sandTex.normal,
      normalScale: 0.52,
      mapRepeat: [6, 2],
      specPower: 0.08,
      rimTint: [0.96, 0.80, 0.58],
      rimStrength: 0.14,
    });
    const rings = [];
    const profile = [
      [0.00, 1.00],
      [0.28, 0.84],
      [0.54, 0.72],
      [0.72, 0.66],
      [0.95, 0.64],
      [1.00, 0.61],
    ];
    for (let r = 0; r < profile.length; r++) {
      const [yf, sc] = profile[r];
      const ring = [];
      const N = 36;
      for (let c = 0; c < N; c++) {
        const a = (c / N) * Math.PI * 2;
        const crag = 1.0 + 0.11 * Math.sin(a * 3.0 + cfg.seed) + 0.07 * Math.cos(a * 7.0 - cfg.seed * 1.7) + 0.04 * Math.sin(a * 13.0 + yf * 4.0);
        const topJitter = yf > 0.9 ? 0.03 * Math.sin(a * 5.0 + cfg.seed) : 0.0;
        ring.push([
          cfg.x + Math.cos(a) * cfg.w * 0.5 * sc * crag,
          -0.22 + (yf + topJitter) * cfg.h,
          cfg.z + Math.sin(a) * cfg.d * 0.5 * sc * crag,
        ]);
      }
      rings.push(ring);
    }
    grp.add(new THREE.Mesh(buildLoftGeometry(rings, true, true), mesaMat));
  }
  return grp;
}

function buildDicroidiumScrubCluster(seed = 91) {
  const grp = new THREE.Group();
  const rng = mulberry32(seed);
  const frondMat = makeImaxMaterial({
    color: '#6e6a3c',
    specular: '#d8cc98',
    specPower: 0.22,
    rimTint: [0.92, 0.78, 0.46],
    rimStrength: 0.25,
    side: THREE.DoubleSide,
  });
  for (let f = 0; f < 7; f++) {
    const yaw = (f / 7) * Math.PI * 2 + rng() * 0.3;
    const len = 0.24 + rng() * 0.16;
    const arch = 0.28 + rng() * 0.25;
    const rings = [];
    for (let r = 0; r <= 8; r++) {
      const u = r / 8;
      const rad = u * len;
      const y = Math.sin(u * Math.PI * 0.78) * len * arch;
      const w = 0.026 * Math.sin(Math.pow(u, 0.7) * Math.PI);
      rings.push([
        [Math.cos(yaw) * rad - Math.sin(yaw) * w, y, Math.sin(yaw) * rad + Math.cos(yaw) * w],
        [Math.cos(yaw) * rad, y + 0.006, Math.sin(yaw) * rad],
        [Math.cos(yaw) * rad + Math.sin(yaw) * w, y, Math.sin(yaw) * rad - Math.cos(yaw) * w],
      ]);
    }
    const frond = new THREE.Mesh(buildLoftGeometry(rings, false, false), frondMat);
    frond.castShadow = true;
    grp.add(frond);
  }
  return grp;
}

// =============================================================================
// 3. V7 PHYSICAL ROCK-CAP CLEAVAGE + CARVED MATRIX BOWL + SPECIES SILHOUETTES
// =============================================================================
function buildCleavingRockCapAndMatrixBowl(sandTex, fossilRockRig) {
  // 1. Dark-terracotta chiseled lower fossil matrix bed under the skeletons so bone-ivory POPS with 10x contrast!
  const bowlGeo = new THREE.SphereGeometry(0.84, 36, 20);
  bowlGeo.scale(1.02, 0.22, 0.56);
  const bPos = bowlGeo.attributes.position;
  for (let i = 0; i < bPos.count; i++) {
    const px = bPos.getX(i);
    const py = bPos.getY(i);
    const pz = bPos.getZ(i);
    // Depress the top face into a carved natural stone hollow cradling the two skeletons!
    if (py > 0) {
      const rIn = Math.hypot(px / 0.76, pz / 0.42);
      const scoop = (1.0 - GLM.smoothstep(0.45, 1.0, rIn)) * 0.16;
      bPos.setY(i, py * 0.35 - scoop + 0.012 * Math.sin(px * 14.0 + pz * 11.0));
    }
  }
  bowlGeo.computeVertexNormals();
  const bowlMat = makeImaxMaterial({
    color: '#522c1b',
    map: sandTex.albedo,
    normalMap: sandTex.normal,
    normalScale: 0.95,
    mapRepeat: [3, 2],
    specular: '#b8825a',
    specPower: 0.10,
    rimTint: [0.92, 0.64, 0.38],
    rimStrength: 0.16,
  });
  const matrixBowl = new THREE.Mesh(bowlGeo, bowlMat);
  matrixBowl.position.set(0.0, 0.25, 0.02);
  matrixBowl.receiveShadow = true;
  matrixBowl.visible = false;
  fossilRockRig.root.add(matrixBowl);

  // 2. Physical Cleaving Upper Sandstone Cap (`upperCapMesh`) that cracks & lifts upward in S02 (and seals in S11)!
  const ROWS = 28;
  const COLS = 24;
  const capRings = [];
  for (let r = 0; r < ROWS; r++) {
    const u = r / (ROWS - 1);
    const x = (u - 0.5) * 1.68;
    const endProfile = Math.sin(Math.pow(u, 0.88) * Math.PI);
    const rxZ = 0.13 + 0.44 * Math.pow(endProfile, 0.68);
    const ryY = 0.08 + 0.24 * Math.pow(endProfile, 0.62);
    const zBend = Math.sin(u * Math.PI) * 0.07;
    const ring = [];
    for (let c = 0; c < COLS; c++) {
      // Dome upper half (`a` in [0 .. PI]) + flat fractured underside
      const a = (c / COLS) * Math.PI * 2;
      const ca = Math.cos(a);
      const sa = Math.sin(a);
      const crag = 1.0 + 0.05 * Math.sin(a * 4.0 + u * 9.0) + 0.03 * Math.cos(a * 7.0 - u * 12.0);
      const py = sa >= 0 ? (0.26 + sa * ryY * crag) : (0.25 + sa * 0.025 * crag);
      ring.push([x, py, zBend + ca * rxZ * crag]);
    }
    capRings.push(ring);
  }
  const capMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: true,
    uniforms: {
      tSand: { value: sandTex.albedo },
      tNorm: { value: sandTex.normal },
      uOpacity: { value: 1.0 },
      uSeamGlow: { value: 0.0 },
    },
    vertexShader: `
      varying vec3 vLocal;
      varying vec3 vWorldNormal;
      varying vec3 vWorldPos;
      varying vec2 vUv;
      void main() {
        vLocal = position;
        vUv = uv * vec2(3.0, 2.0);
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorldPos = wp.xyz;
        vWorldNormal = normalize(mat3(modelMatrix) * normal);
        gl_Position = projectionMatrix * viewMatrix * wp;
      }
    `,
    fragmentShader: `
      uniform sampler2D tSand;
      uniform sampler2D tNorm;
      uniform float uOpacity;
      uniform float uSeamGlow;
      varying vec3 vLocal;
      varying vec3 vWorldNormal;
      varying vec3 vWorldPos;
      varying vec2 vUv;
      void main() {
        vec3 nTex = texture2D(tNorm, vUv).xyz * 2.0 - 1.0;
        vec3 N = normalize(vWorldNormal + vec3(nTex.x, nTex.y, 0.0) * 0.35);
        vec3 L = normalize(vec3(0.55, 0.76, 0.36));
        float diff = max(dot(N, L), 0.0);
        vec3 col = texture2D(tSand, vUv).rgb * (0.30 + 0.88 * diff);
        float seam = exp(-pow((vLocal.y - 0.25) / 0.035, 2.0));
        col += vec3(1.0, 0.80, 0.40) * seam * uSeamGlow * 1.45;
        gl_FragColor = vec4(col, uOpacity);
      }
    `,
  });
  const upperCapMesh = new THREE.Mesh(buildLoftGeometry(capRings, true, true), capMat);
  upperCapMesh.visible = false;
  upperCapMesh.renderOrder = 17;
  fossilRockRig.root.add(upperCapMesh);

  // 3. Individual Callus Clones on Ribs #4, #5, #6 so each lights up sequentially 1 -> 2 -> 3 on its exact osteological click!
  const indivCallusMats = fossilRockRig.healingCallusAnchors.map((mesh) => {
    const m = mesh.material.clone();
    mesh.material = m;
    return m;
  });

  // Boost skeleton contrast & crispness!
  fossilRockRig.mammalBoneMat.color.set('#f9e9ce');
  fossilRockRig.mammalBoneMat.roughness = 0.30;
  fossilRockRig.amphibBoneMat.color.set('#e2d7c3');
  fossilRockRig.amphibBoneMat.roughness = 0.32;

  // 4. Translucent Fresnel Anatomical Life-Silhouettes for S03 ("A mammal relative beside an amphibian")!
  function makeGhostMat(hexCol) {
    return new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uColor: { value: new THREE.Color(hexCol) },
        uStrength: { value: 0.0 },
      },
      vertexShader: `
        varying vec3 vNormalW;
        varying vec3 vPosW;
        void main() {
          vec4 wp = modelMatrix * vec4(position, 1.0);
          vPosW = wp.xyz;
          vNormalW = normalize(mat3(modelMatrix) * normal);
          gl_Position = projectionMatrix * viewMatrix * wp;
        }
      `,
      fragmentShader: `
        uniform vec3 uColor;
        uniform float uStrength;
        varying vec3 vNormalW;
        varying vec3 vPosW;
        void main() {
          vec3 V = normalize(cameraPosition - vPosW);
          float fres = pow(1.0 - clamp(abs(dot(vNormalW, V)), 0.0, 1.0), 1.85);
          float a = uStrength * (0.14 + 0.72 * fres);
          gl_FragColor = vec4(uColor * (0.8 + 0.6 * fres), clamp(a, 0.0, 0.85));
        }
      `,
    });
  }

  const mammalGhostMat = makeGhostMat('#f5b352');
  const amphibGhostMat = makeGhostMat('#c9d47a');

  // Coiled mammal-relative silhouette volume around Thrinaxodon
  const mCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-0.38, 0.30,  0.04),
    new THREE.Vector3(-0.60, 0.29, -0.17),
    new THREE.Vector3(-0.51, 0.28, -0.31),
    new THREE.Vector3(-0.30, 0.27, -0.32),
    new THREE.Vector3(-0.13, 0.26, -0.21),
    new THREE.Vector3(-0.15, 0.25, -0.03),
    new THREE.Vector3(-0.28, 0.24,  0.07),
  ]);
  const mammalGhost = new THREE.Mesh(new THREE.TubeGeometry(mCurve, 28, 0.088, 12, false), mammalGhostMat);
  mammalGhost.renderOrder = 21;
  mammalGhost.visible = false;
  fossilRockRig.root.add(mammalGhost);

  // Stretched amphibian silhouette volume around Broomistega
  const aCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3( 0.54, 0.30, 0.26),
    new THREE.Vector3( 0.30, 0.28, 0.16),
    new THREE.Vector3( 0.14, 0.27, 0.13),
    new THREE.Vector3(-0.02, 0.26, 0.15),
    new THREE.Vector3(-0.22, 0.25, 0.24),
  ]);
  const amphibGhost = new THREE.Mesh(new THREE.TubeGeometry(aCurve, 24, 0.082, 12, false), amphibGhostMat);
  amphibGhost.scale.set(1.0, 0.72, 1.15);
  amphibGhost.renderOrder = 21;
  amphibGhost.visible = false;
  fossilRockRig.root.add(amphibGhost);

  return {
    matrixBowl,
    upperCapMesh,
    capMat,
    indivCallusMats,
    mammalGhost,
    mammalGhostMat,
    amphibGhost,
    amphibGhostMat,
  };
}

// =============================================================================
// 4. V7 CREATURE BIOMECHANICS UPGRADES (S-Wave Spine, Eyelids, Whiskers, Puffs!)
// =============================================================================
function attachExpressiveBiomechanicsToBurrow(burrowRig, orgTex) {
  const cyn = burrowRig.livingCynodont;
  const amp = burrowRig.livingAmphib;

  // --- A. THRINAXODON EXPRESSIVE EYES, EYELIDS, EARS & SNOUT WHISKERS ---
  const furLidMat = makeImaxMaterial({
    color: '#844e30',
    map: orgTex.furAlbedo,
    normalMap: orgTex.furNormal,
    normalScale: 0.45,
    specPower: 0.22,
  });
  const warmEyeMat = makeImaxMaterial({ color: '#3b200c', specular: '#ffffff', specPower: 0.96 });
  const catchlightMat = new THREE.MeshBasicMaterial({ color: '#fff8ea' });
  const whiskerMat = new THREE.MeshBasicMaterial({ color: '#e8d8be', transparent: true, opacity: 0.78 });

  const cynEyes = [];
  for (const sgn of [-1, 1]) {
    const eyeBall = new THREE.Mesh(new THREE.SphereGeometry(0.0135, 12, 10), warmEyeMat);
    eyeBall.position.set(sgn * 0.040, 0.026, 0.092);
    cyn.head.add(eyeBall);

    const catchDot = new THREE.Mesh(new THREE.SphereGeometry(0.0038, 6, 6), catchlightMat);
    catchDot.position.set(sgn * 0.045, 0.031, 0.102);
    cyn.head.add(catchDot);

    // Upper furry eyelid rotating open/shut smoothly!
    const upperLid = new THREE.Mesh(
      new THREE.SphereGeometry(0.0152, 12, 8, 0, Math.PI * 2, 0, Math.PI * 0.56),
      furLidMat
    );
    upperLid.position.set(sgn * 0.040, 0.026, 0.092);
    cyn.head.add(upperLid);
    cynEyes.push({ eyeBall, upperLid });

    // 3 Delicate Mammalian Tactile Whiskers (Vibrissae) per snout side!
    for (let w = 0; w < 3; w++) {
      const wh = new THREE.Mesh(new THREE.CylinderGeometry(0.0008, 0.0003, 0.068, 4), whiskerMat);
      wh.position.set(sgn * 0.036, -0.004 + w * 0.006, 0.195 - w * 0.012);
      wh.rotation.z = -sgn * (1.28 + w * 0.12);
      wh.rotation.y = sgn * (0.25 - w * 0.15);
      cyn.head.add(wh);
    }
  }

  // --- B. BROOMISTEGA TRAVELING S-WAVE SPINE DEFORMATION + GULAR THROAT SAC + EYELID BLINKS ---
  const ampGeo = amp.bodyMesh.geometry;
  const ampBasePos = Float32Array.from(ampGeo.attributes.position.array);

  const skinLidMat = makeImaxMaterial({ color: '#5f5036', specPower: 0.45 });
  const ampLids = [];
  for (const sgn of [-1, 1]) {
    const lid = new THREE.Mesh(
      new THREE.SphereGeometry(0.0145, 10, 8, 0, Math.PI * 2, 0, Math.PI * 0.55),
      skinLidMat
    );
    lid.position.set(sgn * 0.042, 0.037, 0.045);
    amp.head.add(lid);
    ampLids.push(lid);
  }

  // Amphibian gular throat pouch under lower jaw (oscillates visibly as Broomistega breathes!)
  const gularSac = new THREE.Mesh(
    new THREE.SphereGeometry(0.056, 12, 10),
    makeImaxMaterial({ color: '#9c865b', specular: '#f5dec0', specPower: 0.52 })
  );
  gularSac.scale.set(1.25, 0.42, 1.35);
  gularSac.position.set(0, -0.016, 0.045);
  amp.head.add(gularSac);

  // --- C. FOOTSTEP SAND PUFFS (`S07`) + FLASH-FLOOD MUD SPLASH DROPLETS (`S09`) ---
  const PUFF_COUNT = 36;
  const puffGeo = new THREE.SphereGeometry(0.016, 7, 6);
  const puffMat = new THREE.MeshBasicMaterial({
    color: '#d8a474',
    transparent: true,
    opacity: 0.55,
    depthWrite: false,
  });
  const puffMesh = new THREE.InstancedMesh(puffGeo, puffMat, PUFF_COUNT);
  puffMesh.frustumCulled = false;
  puffMesh.renderOrder = 20;
  burrowRig.group.add(puffMesh);

  const SPLASH_COUNT = 72;
  const splashGeo = new THREE.SphereGeometry(0.013, 6, 5);
  const splashMat = new THREE.MeshBasicMaterial({
    color: '#c99364',
    transparent: true,
    opacity: 0.82,
    depthWrite: false,
  });
  const splashMesh = new THREE.InstancedMesh(splashGeo, splashMat, SPLASH_COUNT);
  splashMesh.frustumCulled = false;
  splashMesh.renderOrder = 19;
  burrowRig.group.add(splashMesh);

  const dummy = new THREE.Object3D();
  const stepTimes = [18.58, 18.98, 19.40, 19.82, 20.24, 20.68];

  function updateBiomechanics({ time, crawlProgress, isStorm, surgeFront, fillLevel }) {
    // 1. Live S-Wave Spinal Undulation on Broomistega's 26-ring body!
    const walkAct = 1.0 - GLM.smoothstep(0.85, 1.0, crawlProgress);
    const posAttr = ampGeo.attributes.position;
    const breathAmp = fillLevel > 0.25 ? 0.0 : 1.0;
    const gularRate = walkAct > 0.1 ? 0.95 : 0.30;
    const gularBeat = 0.5 + 0.5 * Math.sin(time * Math.PI * 2.0 * gularRate) * breathAmp;

    for (let i = 0; i < posAttr.count; i++) {
      const bx = ampBasePos[i * 3 + 0];
      const by = ampBasePos[i * 3 + 1];
      const bz = ampBasePos[i * 3 + 2]; // +0.24 (neck) -> -0.54 (tail tip)
      const uAlong = GLM.clamp((0.24 - bz) / 0.78, 0.0, 1.0);
      const sWave = Math.sin(uAlong * 6.2 - crawlProgress * 20.0) * 0.042 * (0.30 + 0.70 * uAlong) * walkAct;
      // Gentle tail curl & rib breathing when resting in S08
      const restCurl = (1.0 - walkAct) * Math.pow(Math.max(0, uAlong - 0.45) / 0.55, 1.8) * 0.065;
      const ribBreath = (uAlong > 0.08 && uAlong < 0.52) ? (1.0 + 0.032 * (gularBeat - 0.5) * breathAmp) : 1.0;
      posAttr.setXYZ(i, bx * ribBreath + sWave + restCurl, by * ribBreath, bz);
    }
    posAttr.needsUpdate = true;
    ampGeo.computeVertexNormals();

    // Gular throat pump + natural amphibian blinks (`19.15s, 22.35s, 24.65s`)
    gularSac.scale.set(1.25, 0.36 + 0.26 * gularBeat, 1.35);
    let ampBlink = fillLevel > 0.15 ? 1.0 : 0.08;
    for (const bt of [19.15, 22.35, 24.65]) {
      const dt = Math.abs(time - bt);
      if (dt < 0.14) ampBlink = Math.max(ampBlink, Math.pow(Math.cos((dt / 0.14) * Math.PI * 0.5), 2));
    }
    for (const lid of ampLids) {
      lid.rotation.x = GLM.mix(-0.92, 0.18, ampBlink);
    }

    // 2. Thrinaxodon Sleepy Eye-Peek (`21.45s..22.85s`), Snout Sniff, & Flash-Flood Huddle (`26.05s+`)!
    // Sleepy eye cracks half-open when Broomistega settles nearby, checks friend peacefully, then closes!
    const peekWindow = GLM.smoothstep(21.40, 21.80, time) * (1.0 - GLM.smoothstep(22.45, 22.95, time));
    const startlePeek = isStorm ? GLM.smoothstep(25.95, 26.12, time) * (1.0 - GLM.smoothstep(26.35, 26.60, time)) : 0.0;
    const eyeOpen = Math.max(peekWindow * 0.62, startlePeek * 0.85) * (1.0 - GLM.smoothstep(0.15, 0.35, fillLevel));
    for (const ce of cynEyes) {
      // Closed = +0.22 rad (covers eyeball); Open = -0.78 rad!
      ce.upperLid.rotation.x = GLM.mix(0.22, -0.78, eyeOpen);
    }

    // Sniff micro-nod during peekWindow + instinctive huddle closer together on flood impact!
    const sniff = peekWindow * Math.sin(time * 22.0) * 0.035;
    const huddle = isStorm ? GLM.smoothstep(26.02, 26.55, time) : 0.0;
    cyn.grp.position.set(0.28 - 0.045 * huddle, 0.26, -0.14 + 0.035 * huddle);
    cyn.head.rotation.y = 1.25 - 0.12 * peekWindow + 0.08 * huddle;
    cyn.head.rotation.z = -0.14 + sniff;
    if (huddle > 0.01) {
      amp.root.position.x += 0.045 * huddle;
      amp.root.position.z -= 0.035 * huddle;
    }

    // 3. Footstep Sand Puffs in S07 (`18.58..21.15s`)
    let anyPuff = false;
    for (let p = 0; p < PUFF_COUNT; p++) {
      const stepIdx = Math.floor(p / 6);
      const subIdx = p % 6;
      const dt = time - stepTimes[stepIdx];
      if (dt > 0.0 && dt < 0.48 && !isStorm) {
        anyPuff = true;
        const life = dt / 0.48;
        const uPath = GLM.mix(0.18, 0.60, stepIdx / 5.0);
        const sPt = burrowRig.tunnelSpine.getPoint(uPath);
        const side = (stepIdx % 2 === 0 ? -1 : 1) * 0.16;
        const ang = (subIdx / 6) * Math.PI * 2 + stepIdx;
        dummy.position.set(
          sPt.x + Math.cos(ang) * 0.08 * life,
          sPt.y + 0.02 + 0.07 * Math.sin(life * Math.PI),
          sPt.z + side + Math.sin(ang) * 0.08 * life
        );
        dummy.scale.setScalar((1.0 - life) * 1.15);
      } else {
        dummy.scale.setScalar(0.0001);
      }
      dummy.updateMatrix();
      puffMesh.setMatrixAt(p, dummy.matrix);
    }
    puffMesh.visible = anyPuff;
    if (anyPuff) puffMesh.instanceMatrix.needsUpdate = true;

    // 4. 3D Terracotta Mud/Foam Splash Droplets ahead of the Flood Surge Crest (`S09`)!
    const showSplash = isStorm && surgeFront > 0.04 && fillLevel < 0.92;
    splashMesh.visible = showSplash;
    if (showSplash) {
      const crestPt = burrowRig.tunnelSpine.getPoint(GLM.clamp(surgeFront, 0.05, 0.95));
      for (let s = 0; s < SPLASH_COUNT; s++) {
        const cyc = ((time * (2.6 + (s % 5) * 0.35) + s * 0.17) % 1.0);
        const ang = s * 2.39996;
        const spread = 0.08 + (s % 7) * 0.045;
        dummy.position.set(
          crestPt.x + 0.18 * cyc + Math.cos(ang) * spread * cyc,
          crestPt.y + 0.10 + Math.sin(cyc * Math.PI) * (0.18 + (s % 4) * 0.06),
          crestPt.z + Math.sin(ang) * spread * cyc
        );
        dummy.scale.setScalar((1.0 - cyc) * (0.7 + (s % 3) * 0.35));
        dummy.updateMatrix();
        splashMesh.setMatrixAt(s, dummy.matrix);
      }
      splashMesh.instanceMatrix.needsUpdate = true;
    }
  }

  return { updateBiomechanics };
}

// =============================================================================
// 5. MASTER V7 WORLD BUILDER (`createKarooUltraWorldV7`)
// =============================================================================
export async function createKarooUltraWorldV7(renderer) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#d8b88c');

  scene.environment = createStudioSoftboxEnvMap(renderer);
  setImaxLightingPreset('karoo_desert_sun', { fogStart: 13.5, fogRange: 35.0 });

  const sandTex = buildKarooSandstoneTextures(2501);
  const floorTex = buildKarooDesertFloorTextures(7721);
  const orgTex = buildOrganicCreatureTextures(8812, true);

  // --- ATMOSPHERIC KAROO SKY & MONSOON DOME ---
  const skyMat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    uniforms: {
      uStormMix: { value: 0.0 },
      uLightning: { value: 0.0 },
      uSunDir: { value: new THREE.Vector3(0.58, 0.44, -0.68).normalize() },
    },
    vertexShader: `
      varying vec3 vDir;
      void main() {
        vDir = normalize(position);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uStormMix;
      uniform float uLightning;
      uniform vec3 uSunDir;
      varying vec3 vDir;
      void main() {
        float h = clamp(vDir.y * 1.35 + 0.08, 0.0, 1.0);
        vec3 dayHorizon = vec3(0.93, 0.78, 0.58);
        vec3 dayMid     = vec3(0.63, 0.76, 0.86);
        vec3 dayZenith  = vec3(0.30, 0.49, 0.67);
        vec3 dayCol = mix(dayHorizon, dayMid, smoothstep(0.0, 0.38, h));
        dayCol = mix(dayCol, dayZenith, smoothstep(0.35, 0.92, h));

        float sunDot = max(dot(normalize(vDir), uSunDir), 0.0);
        dayCol += vec3(1.0, 0.85, 0.55) * pow(sunDot, 10.0) * 0.46;

        vec3 stormHorizon = vec3(0.23, 0.18, 0.20);
        vec3 stormZenith  = vec3(0.07, 0.09, 0.14);
        vec3 stormCol = mix(stormHorizon, stormZenith, smoothstep(0.0, 0.75, h));
        stormCol += vec3(0.86, 0.90, 0.98) * uLightning * 0.58;

        gl_FragColor = vec4(mix(dayCol, stormCol, uStormMix), 1.0);
      }
    `,
  });
  const skyDome = new THREE.Mesh(new THREE.SphereGeometry(38.0, 40, 24), skyMat);
  skyDome.renderOrder = -10;
  scene.add(skyDome);

  // ===========================================================================
  // SET A: LIVING KAROO PALEONTOLOGY EXPEDITION TRENCH (`trenchRoot`)
  // ===========================================================================
  const trenchRoot = new THREE.Group();
  scene.add(trenchRoot);

  const desertFloor = new THREE.Mesh(
    new THREE.PlaneGeometry(56, 56),
    makeImaxMaterial({
      color: '#b4714c',
      map: floorTex.albedo,
      normalMap: floorTex.normal,
      normalScale: 0.74,
      mapRepeat: [11, 11],
      specular: '#f0cfa8',
      specPower: 0.16,
      rimTint: [0.94, 0.72, 0.48],
      rimStrength: 0.14,
      polygonOffset: true,
      polygonOffsetFactor: 3,
      polygonOffsetUnits: 3,
    })
  );
  desertFloor.rotation.x = -Math.PI / 2;
  desertFloor.receiveShadow = true;
  trenchRoot.add(desertFloor);

  trenchRoot.add(createGroundContactAO({ width: 2.6, depth: 1.9, opacity: 0.68, floorY: 0.0 }));

  const trenchStoneMat = makeImaxMaterial({
    color: '#a45e3d',
    map: sandTex.albedo,
    normalMap: sandTex.normal,
    normalScale: 0.85,
    mapRepeat: [5, 4],
    specular: '#ecc298',
    specPower: 0.16,
    rimTint: [0.95, 0.72, 0.46],
    rimStrength: 0.16,
  });

  const benchGeo = new THREE.PlaneGeometry(7.2, 5.2, 96, 96);
  benchGeo.rotateX(-Math.PI / 2);
  const bPos = benchGeo.attributes.position;
  for (let i = 0; i < bPos.count; i++) {
    const px = bPos.getX(i);
    const pz = bPos.getZ(i);
    const ellipR = Math.hypot(px / 1.65, (pz - 0.12) / 1.18);
    const shelf = 1.0 - GLM.smoothstep(0.68, 1.48, ellipR);
    const terrace = Math.floor(shelf * 3.6) / 3.6 * 0.35 + shelf * 0.65;
    const socket = (1.0 - GLM.smoothstep(0.45, 0.95, Math.hypot(px / 0.88, pz / 0.44))) * 0.028;
    const microCrag = (0.012 * Math.sin(px * 5.2 + pz * 4.1) + 0.008 * Math.cos(px * 9.4 - pz * 7.8)) * shelf;
    bPos.setY(i, Math.max(0.003, terrace * 0.135 - socket + microCrag));
  }
  benchGeo.computeVertexNormals();
  const rockCradle = new THREE.Mesh(benchGeo, trenchStoneMat);
  rockCradle.castShadow = true;
  rockCradle.receiveShadow = true;
  trenchRoot.add(rockCradle);

  const wallRings = [];
  for (let r = 0; r <= 32; r++) {
    const u = r / 32;
    const x = (u - 0.5) * 10.6;
    const sideRise = GLM.smoothstep(0.8, 3.6, Math.abs(x));
    const crag1 = 0.09 * Math.sin(u * 13.0) + 0.05 * Math.cos(u * 23.0);
    const h1 = 0.22 + 0.34 * sideRise + crag1;
    const h2 = 0.42 + 0.58 * sideRise + crag1 * 1.3;
    wallRings.push([
      [x, -0.04, -2.05 + 0.22 * Math.sin(u * 9.0)],
      [x,  h1,   -2.42 + 0.18 * Math.cos(u * 11.0)],
      [x,  h1 + 0.04, -2.88],
      [x,  h2,   -3.25 + 0.24 * Math.sin(u * 15.0)],
      [x,  h2 + 0.05, -3.95],
      [x, -0.05, -4.40],
    ]);
  }
  const trenchBackWall = new THREE.Mesh(buildLoftGeometry(wallRings, false, true), trenchStoneMat);
  trenchBackWall.castShadow = true;
  trenchBackWall.receiveShadow = true;
  trenchRoot.add(trenchBackWall);

  trenchRoot.add(buildKarooMesaRange(sandTex));

  // Expedition 4x4 Vehicle + Wind-Rippling Canvas Canopy + Survey Ribbon Stakes + Soaring Eagles!
  const defender4x4 = buildExpedition4x4Vehicle();
  defender4x4.position.set(-2.95, 0.44, -6.95);
  defender4x4.rotation.y = 0.52;
  trenchRoot.add(defender4x4);

  const campCanopy = buildWindCanopyAndCampGear();
  campCanopy.grp.position.set(2.35, 0.22, -3.55);
  campCanopy.grp.rotation.y = -0.36;
  trenchRoot.add(campCanopy.grp);

  const surveyStakes = [
    { pos: [-1.18, 0.11,  0.46], rotY:  0.35, phase: 0.2 },
    { pos: [ 1.15, 0.11,  0.38], rotY: -0.25, phase: 1.9 },
    { pos: [-1.62, 0.18, -1.55], rotY:  0.15, phase: 3.4 },
  ].map((cfg) => {
    const st = buildSurveyStakeWithRibbon(cfg.phase);
    st.grp.position.set(...cfg.pos);
    st.grp.rotation.y = cfg.rotY;
    trenchRoot.add(st.grp);
    return st;
  });

  const skyLife = buildSoaringEaglesAndDustDevil();
  trenchRoot.add(skyLife.grp);

  // Scattered Sandstone Excavation Chips
  const chipMesh = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(0.036, 0), trenchStoneMat, 56);
  chipMesh.castShadow = true;
  chipMesh.receiveShadow = true;
  const rng = mulberry32(55581);
  const dummy = new THREE.Object3D();
  for (let i = 0; i < 56; i++) {
    const ang = rng() * Math.PI * 2;
    const rad = 0.95 + rng() * 2.4;
    dummy.position.set(Math.cos(ang) * rad * 1.25, 0.016, Math.sin(ang) * rad * 0.85);
    dummy.rotation.set(rng() * 3, rng() * 3, rng() * 3);
    dummy.scale.set(0.6 + rng() * 1.5, 0.35 + rng() * 0.55, 0.6 + rng() * 1.3);
    dummy.updateMatrix();
    chipMesh.setMatrixAt(i, dummy.matrix);
  }
  trenchRoot.add(chipMesh);

  for (const [sx, sz, sd] of [[-1.85, -1.18, 101], [1.92, -1.24, 102], [-2.55, 0.45, 103], [2.45, 0.35, 104]]) {
    const scrub = buildDicroidiumScrubCluster(sd);
    scrub.position.set(sx, 0.01, sz);
    trenchRoot.add(scrub);
  }

  // HERO SPECIMEN BP/1/5558 + V7 PHYSICAL ROCK-CAP CLEAVAGE & SPECIES SILHOUETTES!
  const fossilRockRig = createKarooRockAndDualFossilRig({
    yBase: 0.11,
    paletteMode: 'karoo_field_sun',
  });
  trenchRoot.add(fossilRockRig.root);

  const cleavageRig = buildCleavingRockCapAndMatrixBowl(sandTex, fossilRockRig);

  const sunSliceCurtain = createVolumetricLightBlade({
    color: '#ffd27a',
    intensity: 0.28,
    length: 1.95,
    width: 1.05,
    originX: 0.0,
    renderOrder: 22,
  });
  sunSliceCurtain.rotation.z = -Math.PI * 0.5;
  sunSliceCurtain.position.set(0, 1.35, 0.0);
  sunSliceCurtain.visible = false;
  trenchRoot.add(sunSliceCurtain);

  // Foreground Paleontologist Tools + Animated Bristle Brush + 64 Sunlit Quartz Dust Puffs!
  const rockHammer = buildEstwingRockHammer();
  rockHammer.position.set(-0.84, 0.148, 0.62);
  rockHammer.rotation.set(1.44, 0.48, -0.52);
  trenchRoot.add(rockHammer);

  const brushTools = buildAnimatedBrushAndStaticChisel();
  brushTools.brushRig.position.set(0.68, 0.142, 0.62);
  brushTools.brushRig.rotation.set(0, -0.62, 0);
  trenchRoot.add(brushTools.brushRig, brushTools.chiselGrp);

  const BRUSH_DUST_N = 64;
  const brushDustMesh = new THREE.InstancedMesh(
    new THREE.SphereGeometry(0.015, 7, 6),
    new THREE.MeshBasicMaterial({ color: '#e8b684', transparent: true, opacity: 0.52, depthWrite: false }),
    BRUSH_DUST_N
  );
  brushDustMesh.frustumCulled = false;
  brushDustMesh.renderOrder = 23;
  brushDustMesh.visible = false;
  trenchRoot.add(brushDustMesh);

  const notebook = buildFieldNotebook();
  notebook.grp.position.set(-0.56, 0.132, 0.88);
  notebook.grp.rotation.y = 0.26;
  trenchRoot.add(notebook.grp);

  const rulerTex = buildMetricRulerTexture();
  const scaleSideMat = makeImaxMaterial({ color: '#dfd8c8', specPower: 0.15 });
  const scaleTopMat = makeImaxMaterial({
    color: '#fffaf0',
    map: rulerTex,
    specular: '#fff5dc',
    specPower: 0.22,
    rimTint: [0.96, 0.84, 0.66],
    rimStrength: 0.20,
  });
  const scaleCard = new THREE.Mesh(
    new THREE.BoxGeometry(0.46, 0.014, 0.072),
    [scaleSideMat, scaleSideMat, scaleTopMat, scaleSideMat, scaleSideMat, scaleSideMat]
  );
  scaleCard.position.set(0.10, 0.140, 0.72);
  scaleCard.rotation.y = -0.05;
  scaleCard.castShadow = true;
  trenchRoot.add(scaleCard);

  // ===========================================================================
  // SET B: 250-MA EARLY TRIASSIC FLOODPLAIN + EXPRESSIVE LIVING BURROW PAIR
  // ===========================================================================
  const triassicRoot = new THREE.Group();
  triassicRoot.visible = false;
  scene.add(triassicRoot);

  const burrowRig = createTriassicBurrowAndLivingPairRig({ paletteMode: 'karoo_field_sun' });
  burrowRig.group.visible = true;
  for (const child of burrowRig.group.children) {
    if (child.geometry && child.geometry.type === 'PlaneGeometry') {
      child.visible = false;
    }
  }
  triassicRoot.add(burrowRig.group);

  const biomech = attachExpressiveBiomechanicsToBurrow(burrowRig, orgTex);

  const subEarthWall = new THREE.Mesh(
    new THREE.PlaneGeometry(16.0, 4.92),
    makeImaxMaterial({
      color: '#a86644',
      map: buildSubEarthStrataTexture(6612),
      normalMap: sandTex.normal,
      normalScale: 0.55,
      mapRepeat: [4, 2],
      specular: '#cfa07c',
      specPower: 0.08,
      rimTint: [0.88, 0.58, 0.36],
      rimStrength: 0.24,
    })
  );
  subEarthWall.position.set(0.0, -0.94, -0.68);
  triassicRoot.add(subEarthWall);

  const triassicSurface = new THREE.Mesh(
    new THREE.PlaneGeometry(36.0, 22.0),
    makeImaxMaterial({
      color: '#a86442',
      map: floorTex.albedo,
      normalMap: floorTex.normal,
      normalScale: 0.72,
      mapRepeat: [9, 6],
      specPower: 0.14,
      polygonOffset: true,
      polygonOffsetFactor: 2,
      polygonOffsetUnits: 2,
    })
  );
  triassicSurface.rotation.x = -Math.PI / 2;
  triassicSurface.position.set(0.0, 1.52, -11.88);
  triassicSurface.receiveShadow = true;
  triassicRoot.add(triassicSurface);

  const triassicMesas = buildKarooMesaRange(sandTex);
  triassicMesas.position.y = 1.52;
  triassicRoot.add(triassicMesas);

  const triassicFerns = [];
  for (const [fx, fz, sd] of [[-2.05, -0.95, 201], [-0.95, -0.98, 202], [0.85, -0.96, 203], [2.15, -1.02, 204]]) {
    const fn = buildDicroidiumScrubCluster(sd);
    fn.position.set(fx, 1.52, fz);
    triassicRoot.add(fn);
    triassicFerns.push(fn);
  }

  // Swaying Earthen Rootlets inside Burrow Ceiling (`fg` bokeh parallax for S08!)
  const rootletMat = makeImaxMaterial({ color: '#5c3c24', specPower: 0.12 });
  const rootlets = [];
  for (let i = 0; i < 11; i++) {
    const rx = -0.42 + i * 0.105;
    const rlen = 0.11 + (i % 3) * 0.048;
    const rootlet = new THREE.Mesh(new THREE.ConeGeometry(0.006, rlen, 6), rootletMat);
    rootlet.rotation.x = Math.PI;
    const baseRotZ = (i % 2 === 0 ? 1 : -1) * 0.14;
    rootlet.rotation.z = baseRotZ;
    rootlet.position.set(rx, 0.86 - Math.abs(rx - 0.10) * 0.18, 0.12 + (i % 2) * 0.09);
    triassicRoot.add(rootlet);
    rootlets.push({ mesh: rootlet, baseRotZ, phase: i * 0.9 });
  }

  const floodRig = createFlashFloodAndPetrificationSystem(burrowRig.tunnelSpine, {
    paletteMode: 'karoo_field_sun',
  });
  triassicRoot.add(floodRig.group);

  const sunBlade = createVolumetricLightBlade({
    color: '#ffbe68',
    intensity: 0.25,
    length: 3.2,
    width: 1.08,
    originX: -1.72,
    renderOrder: 22,
  });
  sunBlade.position.set(-0.28, 1.54, 0.04);
  sunBlade.rotation.z = -0.44;
  triassicRoot.add(sunBlade);

  const RAIN_COUNT = 150;
  const rainMesh = new THREE.InstancedMesh(
    new THREE.CylinderGeometry(0.003, 0.003, 0.44, 4),
    new THREE.MeshBasicMaterial({ color: '#dcd2bc', transparent: true, opacity: 0.44, depthWrite: false }),
    RAIN_COUNT
  );
  rainMesh.frustumCulled = false;
  rainMesh.renderOrder = 23;
  rainMesh.visible = false;
  triassicRoot.add(rainMesh);
  const rainSeeds = Array.from({ length: RAIN_COUNT }, (_, i) => ({
    x0: -3.2 + ((i * 0.618034) % 1.0) * 6.4,
    y0: 1.55 + ((i * 0.381966) % 1.0) * 2.6,
    z0: -2.4 + ((i * 0.754877) % 1.0) * 2.2,
    spd: 6.6 + (i % 5) * 1.1,
  }));

  const lightningBolt = new THREE.Group();
  const boltCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-0.95, 3.65, -4.8),
    new THREE.Vector3(-0.74, 3.05, -4.8),
    new THREE.Vector3(-0.88, 2.58, -4.8),
    new THREE.Vector3(-0.62, 2.04, -4.8),
    new THREE.Vector3(-0.72, 1.52, -4.8),
  ]);
  const forkCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-0.88, 2.58, -4.8),
    new THREE.Vector3(-1.16, 2.12, -4.8),
    new THREE.Vector3(-1.28, 1.72, -4.8),
  ]);
  const lightningMat = new THREE.MeshBasicMaterial({
    color: '#fff6e4',
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const lightningHaloMat = new THREE.MeshBasicMaterial({
    color: '#d8b48a',
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  lightningBolt.add(
    new THREE.Mesh(new THREE.TubeGeometry(boltCurve, 18, 0.026, 6, false), lightningMat),
    new THREE.Mesh(new THREE.TubeGeometry(forkCurve, 10, 0.016, 6, false), lightningMat),
    new THREE.Mesh(new THREE.TubeGeometry(boltCurve, 18, 0.095, 6, false), lightningHaloMat)
  );
  lightningBolt.renderOrder = 21;
  lightningBolt.visible = false;
  triassicRoot.add(lightningBolt);

  // ===========================================================================
  // LIGHTING + LOOP-LOCKED DUST MOTES + 30 Hz TEXEL-SNAPPED SHADOWS
  // ===========================================================================
  const ambientLight = new THREE.HemisphereLight('#8fb4d4', '#b87248', 0.88);
  scene.add(ambientLight);

  const keyLight = new THREE.DirectionalLight('#ffe8c2', 3.35);
  keyLight.position.set(4.8, 5.6, 4.4);
  scene.add(keyLight);

  const skyRimLight = new THREE.DirectionalLight('#ebd2a8', 2.45);
  skyRimLight.position.set(-4.4, 3.8, -3.6);
  scene.add(skyRimLight);

  const trenchBounceLight = new THREE.PointLight('#e89458', 1.85, 11.0, 1.6);
  trenchBounceLight.position.set(1.4, 1.2, 2.4);
  scene.add(trenchBounceLight);

  const fossilCoreLight = new THREE.PointLight('#ffcf7c', 0.0, 5.2, 1.8);
  fossilCoreLight.position.set(0.0, 0.58, 0.34);
  scene.add(fossilCoreLight);

  const dust = createLoopLockedDustMotes({
    count: 58,
    radius: 0.009,
    color: '#ffe4b4',
    loopDurationS: DURATION,
    bounds: { x0: -2.5, xSpan: 5.0, y0: 0.24, ySpan: 2.3, z0: -2.0, zSpan: 2.6 },
    renderOrder: 24,
  });
  scene.add(dust.mesh);

  const shadowRig = createTexelSnappedShadowRig(renderer, { mapSize: 512 });

  // ===========================================================================
  // LIVE FRAME UPDATE HELPERS (Brush Sweeps, Cloth, Ribbons, Eagles, Rain!)
  // ===========================================================================
  const strokeTimes = [0.20, 0.88, 1.56];
  function updateWorldDynamics(time, isStorm, stormStrength) {
    const w0 = (Math.PI * 2.0) / DURATION;

    // 1. Notebook flutter, canopy cloth ripple, survey ribbons & soaring eagles (100% loop-locked at 36.0s!)
    notebook.flutterPage.rotation.y = 0.035 + 0.034 * Math.sin(3.0 * w0 * time) + 0.016 * Math.cos(6.0 * w0 * time);
    campCanopy.updateCloth(time);
    for (const st of surveyStakes) st.updateRibbon(time);
    skyLife.updateSkyLife(time);

    // 2. Active S01 Bristle Brush Sweeping Action (`0.10s .. 2.34s` -> handle angled UPWARD above rock crest!)
    const activeBrush = GLM.smoothstep(0.09, 0.22, time) * (1.0 - GLM.smoothstep(2.04, 2.34, time));
    if (activeBrush > 0.001) {
      const sweepX = 0.44 * Math.sin((time - 0.16) * 4.6);
      const sweepZ = 0.10 * Math.cos((time - 0.16) * 9.2);
      // Negative X rotation (-0.82 rad) tilts bristles (z=+0.114) down onto boulder crest while handle (z=-0.22) rises prominently into the sunlit sky!
      const liftY = 0.69 + 0.035 * Math.abs(Math.cos((time - 0.16) * 4.6));
      brushTools.brushRig.position.set(
        GLM.mix(0.68, sweepX, activeBrush),
        GLM.mix(0.142, liftY, activeBrush),
        GLM.mix(0.62, sweepZ + 0.10, activeBrush)
      );
      brushTools.brushRig.rotation.set(
        GLM.mix(0.0, -0.82, activeBrush),
        GLM.mix(-0.62, 0.38 * Math.cos((time - 0.16) * 4.6), activeBrush),
        GLM.mix(0.0, 0.24 * Math.sin((time - 0.16) * 4.6), activeBrush)
      );
    } else {
      brushTools.brushRig.position.set(0.68, 0.142, 0.62);
      brushTools.brushRig.rotation.set(0, -0.62, 0);
    }

    // 64 Sunlit Red-Quartz Dust Puffs kicked up by the 3 S01 Brush Strokes!
    let anyBrushDust = false;
    for (let i = 0; i < BRUSH_DUST_N; i++) {
      const sIdx = i % 3;
      const dt = time - strokeTimes[sIdx];
      if (dt > 0.0 && dt < 0.78) {
        anyBrushDust = true;
        const life = dt / 0.78;
        const ang = i * 2.39996;
        const dirSign = sIdx === 1 ? -1 : 1;
        dummy.position.set(
          dirSign * 0.26 * life + Math.cos(ang) * 0.32 * life,
          0.62 + 0.28 * life - 0.08 * life * life,
          0.14 + Math.sin(ang) * 0.22 * life
        );
        dummy.scale.setScalar((1.0 - life) * (0.85 + (i % 4) * 0.35));
      } else {
        dummy.scale.setScalar(0.0001);
      }
      dummy.updateMatrix();
      brushDustMesh.setMatrixAt(i, dummy.matrix);
    }
    brushDustMesh.visible = anyBrushDust;
    if (anyBrushDust) brushDustMesh.instanceMatrix.needsUpdate = true;

    // 3. Triassic Ferns & Burrow Ceiling Rootlet Sway
    for (let i = 0; i < triassicFerns.length; i++) {
      const sway = isStorm
        ? 0.24 * stormStrength + 0.13 * Math.sin(time * 16.0 + i)
        : 0.038 * Math.sin(4.0 * w0 * time + i * 1.4);
      triassicFerns[i].rotation.z = -sway;
    }
    for (const rl of rootlets) {
      const rSway = isStorm
        ? 0.16 * Math.sin(time * 14.0 + rl.phase) * stormStrength
        : 0.032 * Math.sin(3.0 * w0 * time + rl.phase);
      rl.mesh.rotation.z = rl.baseRotZ + rSway;
    }

    // 4. Monsoon Diagonal Rain Curtain (`S09-S10`)
    rainMesh.visible = isStorm && stormStrength > 0.08;
    if (rainMesh.visible) {
      rainMesh.material.opacity = 0.44 * stormStrength;
      for (let i = 0; i < RAIN_COUNT; i++) {
        const rs = rainSeeds[i];
        const fall = (time * rs.spd) % 2.55;
        dummy.position.set(rs.x0 + fall * 0.34, rs.y0 + 1.1 - fall, rs.z0);
        dummy.rotation.set(0, 0, 0.32);
        dummy.scale.setScalar(1.0);
        dummy.updateMatrix();
        rainMesh.setMatrixAt(i, dummy.matrix);
      }
      rainMesh.instanceMatrix.needsUpdate = true;
    }
  }

  return {
    scene,
    skyMat,
    trenchRoot,
    fossilRockRig,
    cleavageRig,
    sunSliceCurtain,
    brushDustMesh,
    notebook,
    triassicRoot,
    burrowRig,
    biomech,
    floodRig,
    sunBlade,
    rainMesh,
    lightningBolt,
    lightningMat,
    lightningHaloMat,
    ambientLight,
    keyLight,
    skyRimLight,
    trenchBounceLight,
    fossilCoreLight,
    dust,
    shadowRig,
    updateWorldDynamics,
  };
}
