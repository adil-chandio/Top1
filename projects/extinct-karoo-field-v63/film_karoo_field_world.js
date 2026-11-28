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
  createKarooRockAndDualFossilRig,
  createTriassicBurrowAndLivingPairRig,
  createFlashFloodAndPetrificationSystem,
} from '/tools/monarch-v6-imax-sdk/index.js';

/**
 * EXTINCT LIFE V6.3 DIRECTOR EDITION — "This Rock Holds Two Animals" (`BP/1/5558`)
 * Archetype: `W02_SCORCHED_FIELD_EXPEDITION` + `H1_DOCUMENTARY_LOWER_THIRD` (100% Anti-Clone Divergence!)
 *
 * ZERO dark sci-fi laboratory, ZERO spinning pedestal, ZERO cyan neon rings!
 *   - Set A (`trenchRoot`): Blazing 4300K South African Karoo Badlands Excavation Trench
 *       with distant Beaufort kopje mesas, desiccated mud-crack red desert floor, terraced rock pit,
 *       forged Estwing geological rock hammer, wooden bristle fossil brush, khaki field notebook
 *       (`BP/1/5558`), 10cm L-scale card, and warm sunlit calcite geological cross-section peel!
 *   - Set B (`triassicRoot`): 250-Ma Early Triassic Floodplain Surface + Underground Burrow Cutaway
 *       with above-ground Dicroidium drought scrub, open Triassic sky, gathering monsoon storm clouds,
 *       forked lightning, diagonal rain sheets, and churning terracotta-silt flash-flood burial!
 */

export const FPS = 30;
export const DURATION = 36.0;
export const TOTAL_FRAMES = 1080;

// =============================================================================
// 1. PROCEDURAL DESICCATED KAROO MUD-CRACK FLOOR & FIELD NOTEBOOK TEXTURES
// =============================================================================
function buildKarooDesertFloorTextures(seed = 7721) {
  const S = 512;
  const cv = document.createElement('canvas');
  cv.width = cv.height = S;
  const ctx = cv.getContext('2d');
  const rng = mulberry32(seed);

  ctx.fillStyle = '#9c5c3d';
  ctx.fillRect(0, 0, S, S);

  // Sun-baked ochre/terracotta tonal patches
  for (let i = 0; i < 180; i++) {
    const x = rng() * S;
    const y = rng() * S;
    const r = 18 + rng() * 64;
    const g = ctx.createRadialGradient(x, y, 2, x, y, r);
    const warm = rng() > 0.45;
    g.addColorStop(0.0, warm ? 'rgba(206,144,96,0.26)' : 'rgba(108,54,34,0.28)');
    g.addColorStop(1.0, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }

  // Polygonal desiccated mud-crack network (Voronoi cell edges)
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
  ctx.strokeStyle = 'rgba(54, 24, 14, 0.62)';
  ctx.lineWidth = 2.2;
  for (let i = 0; i < pts.length; i++) {
    for (let j = i + 1; j < pts.length; j++) {
      const dx = pts[j][0] - pts[i][0];
      const dy = pts[j][1] - pts[i][1];
      const d = Math.hypot(dx, dy);
      if (d < S / GRID * 1.38) {
        const mx = (pts[i][0] + pts[j][0]) * 0.5 + (rng() - 0.5) * 8.0;
        const my = (pts[i][1] + pts[j][1]) * 0.5 + (rng() - 0.5) * 8.0;
        ctx.beginPath();
        ctx.moveTo(pts[i][0], pts[i][1]);
        ctx.quadraticCurveTo(mx, my, pts[j][0], pts[j][1]);
        ctx.stroke();
      }
    }
  }

  // Fine quartz & dark ironstone gravel speckles
  for (let i = 0; i < 4200; i++) {
    const x = rng() * S;
    const y = rng() * S;
    const rad = 0.6 + rng() * 2.1;
    ctx.fillStyle = rng() > 0.44 ? 'rgba(232,194,148,0.28)' : 'rgba(56,28,18,0.32)';
    ctx.beginPath();
    ctx.arc(x, y, rad, 0, Math.PI * 2);
    ctx.fill();
  }

  const albedo = new THREE.CanvasTexture(cv);
  albedo.colorSpace = THREE.SRGBColorSpace;
  albedo.wrapS = albedo.wrapT = THREE.RepeatWrapping;
  const normal = buildNormalFromCanvas(cv, 2.8, 512);
  return { albedo, normal };
}

function buildFieldNotebookPageTexture() {
  const cv = document.createElement('canvas');
  cv.width = 512;
  cv.height = 384;
  const ctx = cv.getContext('2d');

  ctx.fillStyle = '#efe4c8';
  ctx.fillRect(0, 0, 512, 384);

  // Subtle ruled field-journal lines
  ctx.strokeStyle = 'rgba(120, 138, 152, 0.34)';
  ctx.lineWidth = 1.5;
  for (let y = 56; y < 360; y += 24) {
    ctx.beginPath();
    ctx.moveTo(24, y);
    ctx.lineTo(488, y);
    ctx.stroke();
  }
  // Center spine crease
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
  ctx.fillText('In-situ burrow infill', 32, 126);

  // Graphite sketch of burrow oval on right page
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

// =============================================================================
// 2. BESPOKE PALEONTOLOGY FIELD PROPS (Rock Hammer, Brush, Notebook, Mesas)
// =============================================================================
function buildEstwingRockHammer() {
  const grp = new THREE.Group();
  const steelMat = makeImaxMaterial({
    color: '#8f98a0',
    specular: '#fff4e0',
    specPower: 0.78,
    rimTint: [0.96, 0.78, 0.52],
    rimStrength: 0.28,
  });
  const leatherMat = makeImaxMaterial({
    color: '#5a3219',
    specular: '#d89b68',
    specPower: 0.42,
    rimTint: [0.85, 0.55, 0.30],
    rimStrength: 0.18,
  });

  // Lofted forged steel shaft (`y = 0 .. 0.31m`)
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

  // Stacked varnished leather grip (`y = 0.015 .. 0.145m`)
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

  // Forged head + curved geological pick spike (`x = -0.095 .. +0.115m` at `y = 0.30m`)
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

function buildFossilBrushAndChisel() {
  const grp = new THREE.Group();
  const woodTex = buildWoodPlankTexture(404);
  const woodMat = makeImaxMaterial({
    color: '#b8834c',
    map: woodTex.albedo,
    normalMap: woodTex.normal,
    normalScale: 0.45,
    specPower: 0.35,
  });
  const ferruleMat = makeImaxMaterial({ color: '#c49a48', specular: '#fff5d6', specPower: 0.72 });
  const bristleMat = makeImaxMaterial({ color: '#d8c298', specPower: 0.18 });

  // Turned wooden handle (`z = -0.14 .. +0.06m`)
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
  grp.add(handle);

  const ferrule = new THREE.Mesh(new THREE.BoxGeometry(0.056, 0.015, 0.026), ferruleMat);
  ferrule.position.set(0, 0, 0.062);
  ferrule.castShadow = true;
  grp.add(ferrule);

  const bristles = new THREE.Mesh(new THREE.BoxGeometry(0.058, 0.013, 0.054), bristleMat);
  bristles.position.set(0, 0, 0.100);
  bristles.castShadow = true;
  grp.add(bristles);

  // Forged cold chisel beside brush
  const chiselMat = makeImaxMaterial({ color: '#6b737b', specular: '#e4ecf2', specPower: 0.65 });
  const chisel = new THREE.Mesh(new THREE.CylinderGeometry(0.0085, 0.0095, 0.21, 8), chiselMat);
  chisel.rotation.x = Math.PI * 0.5;
  chisel.rotation.z = 0.24;
  chisel.position.set(0.095, 0.004, -0.02);
  chisel.castShadow = true;
  grp.add(chisel);

  return grp;
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

  // Fluttering top sheet corner driven deterministically in evaluateFrame (`loop-locked`)
  const flutterPage = new THREE.Mesh(
    new THREE.PlaneGeometry(0.132, 0.192, 8, 4),
    makeImaxMaterial({ color: '#f3e7cb', specPower: 0.12, side: THREE.DoubleSide })
  );
  flutterPage.rotation.x = -Math.PI / 2;
  flutterPage.position.set(0.068, 0.016, 0.0);
  grp.add(flutterPage);

  // Wooden field pencil resting diagonally across notebook
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

function buildSubEarthStrataTexture(seed = 6612) {
  const W = 512;
  const H = 512;
  const rng = mulberry32(seed);
  const cv = document.createElement('canvas');
  cv.width = W;
  cv.height = H;
  const ctx = cv.getContext('2d');

  // Rich Beaufort Group Early Triassic Floodplain Soil & Siltstone Horizons
  const bands = [
    [0.00, '#8d5336'], // Sun-baked upper floodplain crust
    [0.14, '#734029'], // Reddish-brown desiccated mudstone
    [0.32, '#865238'], // Buff-ochre crevasse-splay sandstone lens
    [0.48, '#613522'], // Deep terracotta paleosol horizon
    [0.68, '#77452e'], // Caliche-nodule siltstone bed
    [0.85, '#522c1c'], // Compacted basal mudstone
    [1.00, '#442417'],
  ];
  const g = ctx.createLinearGradient(0, 0, 0, H);
  for (const [stop, col] of bands) g.addColorStop(stop, col);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);

  // Fine wavy sedimentary bedding laminae
  for (let y = 4; y < H; y += 5) {
    ctx.strokeStyle = (y % 15 === 0) ? 'rgba(232,188,138,0.16)' : 'rgba(38,18,10,0.22)';
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    for (let x = 0; x <= W; x += 16) {
      const wy = y + Math.sin(x * 0.035 + y * 0.11) * 2.6;
      if (x === 0) ctx.moveTo(x, wy);
      else ctx.lineTo(x, wy);
    }
    ctx.stroke();
  }

  // Pale carbonate caliche nodules & root-trace mottles
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

function buildKarooMesaRange(sandTex) {
  const grp = new THREE.Group();
  // Authentic wide flat-topped Karoo Tafelberg / Dolerite-Capped Mesas (broad silhouettes, stepped cliffs!)
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
      [0.00, 1.00], // Broad talus apron skirt
      [0.28, 0.84],
      [0.54, 0.72],
      [0.72, 0.66], // Base of vertical dolerite caprock sill!
      [0.95, 0.64], // Steep near-vertical Karoo table cliff!
      [1.00, 0.61], // Flat table summit
    ];
    for (let r = 0; r < profile.length; r++) {
      const [yf, sc] = profile[r];
      const ring = [];
      const N = 36;
      for (let c = 0; c < N; c++) {
        const a = (c / N) * Math.PI * 2;
        // Elongated rocky spurs & gullies so silhouette reads as eroded geology, never a smooth cone
        const crag = 1.0
          + 0.11 * Math.sin(a * 3.0 + cfg.seed)
          + 0.07 * Math.cos(a * 7.0 - cfg.seed * 1.7)
          + 0.04 * Math.sin(a * 13.0 + yf * 4.0);
        const topJitter = yf > 0.9 ? 0.03 * Math.sin(a * 5.0 + cfg.seed) : 0.0;
        ring.push([
          cfg.x + Math.cos(a) * cfg.w * 0.5 * sc * crag,
          -0.22 + (yf + topJitter) * cfg.h,
          cfg.z + Math.sin(a) * cfg.d * 0.5 * sc * crag,
        ]);
      }
      rings.push(ring);
    }
    const mesa = new THREE.Mesh(buildLoftGeometry(rings, true, true), mesaMat);
    grp.add(mesa);
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
// 3. MASTER WORLD BUILDER (`createKarooFieldWorldV63`)
// =============================================================================
export async function createKarooFieldWorldV63(renderer) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#d8b88c');

  const studioEnv = createStudioSoftboxEnvMap(renderer);
  scene.environment = studioEnv;
  setImaxLightingPreset('karoo_desert_sun', { fogStart: 13.0, fogRange: 34.0 });

  const sandTex = buildKarooSandstoneTextures(2501);
  const floorTex = buildKarooDesertFloorTextures(7721);

  // --- ATMOSPHERIC KAROO SKY & STORM DOME (`depthWrite: false`, `renderOrder: -10`) ---
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
        // Blazing South African Karoo afternoon sky: warm dust horizon -> arid cerulean zenith
        vec3 dayHorizon = vec3(0.92, 0.77, 0.58);
        vec3 dayMid     = vec3(0.64, 0.76, 0.85);
        vec3 dayZenith  = vec3(0.32, 0.50, 0.67);
        vec3 dayCol = mix(dayHorizon, dayMid, smoothstep(0.0, 0.38, h));
        dayCol = mix(dayCol, dayZenith, smoothstep(0.35, 0.92, h));

        float sunDot = max(dot(normalize(vDir), uSunDir), 0.0);
        dayCol += vec3(1.0, 0.84, 0.54) * pow(sunDot, 12.0) * 0.42;

        // Monsoon storm sky (S09-S10): bruised slate-indigo clouds + warm lightning scatter
        vec3 stormHorizon = vec3(0.24, 0.19, 0.21);
        vec3 stormZenith  = vec3(0.08, 0.10, 0.15);
        vec3 stormCol = mix(stormHorizon, stormZenith, smoothstep(0.0, 0.75, h));
        stormCol += vec3(0.82, 0.86, 0.95) * uLightning * 0.55;

        vec3 col = mix(dayCol, stormCol, uStormMix);
        gl_FragColor = vec4(col, 1.0);
      }
    `,
  });
  const skyDome = new THREE.Mesh(new THREE.SphereGeometry(38.0, 40, 24), skyMat);
  skyDome.renderOrder = -10;
  scene.add(skyDome);

  // ===========================================================================
  // SET A: SOUTH AFRICAN KAROO BADLANDS EXCAVATION TRENCH (`trenchRoot`)
  // ===========================================================================
  const trenchRoot = new THREE.Group();
  scene.add(trenchRoot);

  // 1. Desiccated Mud-Crack Desert Floor (`polygonOffset` -> Zero-Flicker Law #1)
  const desertFloor = new THREE.Mesh(
    new THREE.PlaneGeometry(54, 54),
    makeImaxMaterial({
      color: '#b4714c',
      map: floorTex.albedo,
      normalMap: floorTex.normal,
      normalScale: 0.72,
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

  const rockAO = createGroundContactAO({ width: 2.6, depth: 1.9, opacity: 0.68, floorY: 0.0 });
  trenchRoot.add(rockAO);

  // 2. Continuous Sculpted Beaufort Sandstone Excavation Outcrop Bench (`96x96` terrain -> ZERO floating gap!)
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
    // Broad flat-topped chiseled sandstone shelf under specimen + tools, terraced smoothly into desert floor!
    const ellipR = Math.hypot(px / 1.65, (pz - 0.12) / 1.18);
    const shelf = 1.0 - GLM.smoothstep(0.68, 1.48, ellipR);
    // Stepped sedimentary rock terraces
    const terrace = Math.floor(shelf * 3.6) / 3.6 * 0.35 + shelf * 0.65;
    // Slight chiseled socket depression right under the fossil nodule (`|px| < 0.78, |pz| < 0.38`)
    const socket = (1.0 - GLM.smoothstep(0.45, 0.95, Math.hypot(px / 0.88, pz / 0.44))) * 0.028;
    const microCrag = (0.012 * Math.sin(px * 5.2 + pz * 4.1) + 0.008 * Math.cos(px * 9.4 - pz * 7.8)) * shelf;
    bPos.setY(i, Math.max(0.003, terrace * 0.135 - socket + microCrag));
  }
  benchGeo.computeVertexNormals();
  const rockCradle = new THREE.Mesh(benchGeo, trenchStoneMat);
  rockCradle.castShadow = true;
  rockCradle.receiveShadow = true;
  trenchRoot.add(rockCradle);

  // Eroded Low Beaufort Sandstone Outcrop Ridges behind Trench (`z = -2.35 .. -4.2m`, craggy natural ledges!)
  const wallRings = [];
  for (let r = 0; r <= 32; r++) {
    const u = r / 32;
    const x = (u - 0.5) * 10.6;
    // Dip lower in center (`|x| < 1.8`) so distant Karoo sky & Tafelberg mesas breathe heroically behind title!
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

  // Distant Beaufort Kopje Mesas (`z = -15m .. -21m`)
  const mesaRange = buildKarooMesaRange(sandTex);
  trenchRoot.add(mesaRange);

  // Scattered Natural Red Sandstone Excavation Chips & Pebbles (`InstancedMesh`)
  const chipGeo = new THREE.DodecahedronGeometry(0.036, 0);
  const chipMesh = new THREE.InstancedMesh(chipGeo, trenchStoneMat, 56);
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

  // Sparse Dry Karoo Scrub Tufts in Trench Background
  for (const [sx, sz, sd] of [[-1.85, -1.18, 101], [1.92, -1.24, 102], [-2.55, 0.45, 103], [2.45, 0.35, 104]]) {
    const scrub = buildDicroidiumScrubCluster(sd);
    scrub.position.set(sx, 0.01, sz);
    trenchRoot.add(scrub);
  }

  // 3. HERO IN-SITU FOSSIL BURROW CAST (`BP/1/5558` in `karoo_field_sun` Natural Mode!)
  const fossilRockRig = createKarooRockAndDualFossilRig({
    yBase: 0.11,
    paletteMode: 'karoo_field_sun',
  });
  trenchRoot.add(fossilRockRig.root);

  // Warm Sunlit Calcite Geological Peel Curtain (replaces cyan synchrotron laser!)
  const sunSliceCurtain = createVolumetricLightBlade({
    color: '#ffd27a',
    intensity: 0.24,
    length: 1.85,
    width: 0.95,
    originX: 0.0,
    renderOrder: 22,
  });
  sunSliceCurtain.rotation.z = -Math.PI * 0.5;
  sunSliceCurtain.position.set(0, 1.35, 0.0);
  sunSliceCurtain.visible = false;
  trenchRoot.add(sunSliceCurtain);

  // 4. FOREGROUND PALEONTOLOGIST FIELD TOOLS RESTING ON THE SANDSTONE EXCAVATION SHELF!
  const rockHammer = buildEstwingRockHammer();
  rockHammer.position.set(-0.84, 0.148, 0.62);
  rockHammer.rotation.set(1.44, 0.48, -0.52);
  trenchRoot.add(rockHammer);

  const brushAndChisel = buildFossilBrushAndChisel();
  brushAndChisel.position.set(0.68, 0.142, 0.62);
  brushAndChisel.rotation.y = -0.62;
  trenchRoot.add(brushAndChisel);

  const notebook = buildFieldNotebook();
  notebook.grp.position.set(-0.56, 0.132, 0.88);
  notebook.grp.rotation.y = 0.26;
  trenchRoot.add(notebook.grp);

  // Authentic 10cm Metric Photographic Field Scale Card (`y = 0.138m` right in front of specimen!)
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
  scaleCard.receiveShadow = false;
  trenchRoot.add(scaleCard);

  // ===========================================================================
  // SET B: 250-MA EARLY TRIASSIC FLOODPLAIN SURFACE + UNDERGROUND BURROW
  // ===========================================================================
  const triassicRoot = new THREE.Group();
  triassicRoot.visible = false;
  scene.add(triassicRoot);

  const burrowRig = createTriassicBurrowAndLivingPairRig({ paletteMode: 'karoo_field_sun' });
  burrowRig.group.visible = true;
  // Hide the small 4.4m flat strataBackdrop inside burrowRig and replace with true split-horizon earth + surface!
  for (const child of burrowRig.group.children) {
    if (child.geometry && child.geometry.type === 'PlaneGeometry') {
      child.visible = false;
    }
  }
  burrowRig.dormRingMat.color.set('#e8b059');
  triassicRoot.add(burrowRig.group);

  // Deep Subterranean Stratified Beaufort Sedimentary Cross-Section strictly BELOW surface (`y = -3.4 .. +1.52m`)
  const subEarthStrataTex = buildSubEarthStrataTexture(6612);
  const subEarthWall = new THREE.Mesh(
    new THREE.PlaneGeometry(16.0, 4.92),
    makeImaxMaterial({
      color: '#a86644',
      map: subEarthStrataTex,
      normalMap: sandTex.normal,
      normalScale: 0.55,
      mapRepeat: [4, 2],
      specular: '#cfa07c',
      specPower: 0.08,
      rimTint: [0.88, 0.58, 0.36],
      rimStrength: 0.24,
    })
  );
  subEarthWall.receiveShadow = false;
  subEarthWall.position.set(0.0, -0.94, -0.68);
  triassicRoot.add(subEarthWall);

  // Above-Ground Desiccated Triassic Floodplain Surface Crust (`y = 1.52m`, `z = -0.88 .. -18m`)
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

  // Dicroidium Drought Scrub Tufts along the Burrow Entrance Lip (`y = 1.52m`)
  const triassicFerns = [];
  for (const [fx, fz, sd] of [[-2.05, -0.95, 201], [-0.95, -0.98, 202], [0.85, -0.96, 203], [2.15, -1.02, 204]]) {
    const fn = buildDicroidiumScrubCluster(sd);
    fn.position.set(fx, 1.52, fz);
    triassicRoot.add(fn);
    triassicFerns.push(fn);
  }

  // Hanging Earthen Rootlets inside Burrow Ceiling (`fg` depth framing for S08!)
  const rootletMat = makeImaxMaterial({ color: '#5c3c24', specPower: 0.12 });
  for (let i = 0; i < 9; i++) {
    const rx = -0.35 + i * 0.12;
    const rlen = 0.11 + (i % 3) * 0.045;
    const rootlet = new THREE.Mesh(new THREE.ConeGeometry(0.006, rlen, 6), rootletMat);
    rootlet.rotation.x = Math.PI;
    rootlet.rotation.z = (i % 2 === 0 ? 1 : -1) * 0.14;
    rootlet.position.set(rx, 0.86 - Math.abs(rx - 0.12) * 0.18, 0.12 + (i % 2) * 0.08);
    triassicRoot.add(rootlet);
  }

  // Terracotta-Ochre Flash-Flood & Lithification System (`karoo_field_sun` mode!)
  const floodRig = createFlashFloodAndPetrificationSystem(burrowRig.tunnelSpine, {
    paletteMode: 'karoo_field_sun',
  });
  triassicRoot.add(floodRig.group);

  // Scorching 4100K Drought Sun Shaft pouring down the inclined burrow entrance!
  const sunBlade = createVolumetricLightBlade({
    color: '#ffbe68',
    intensity: 0.24,
    length: 3.2,
    width: 1.05,
    originX: -1.72,
    renderOrder: 22,
  });
  sunBlade.position.set(-0.28, 1.54, 0.04);
  sunBlade.rotation.z = -0.44;
  triassicRoot.add(sunBlade);

  // Diagonal Monsoon Rain Curtain (`InstancedMesh`, visible only during S09-S10 storm!)
  const RAIN_COUNT = 140;
  const rainGeo = new THREE.CylinderGeometry(0.003, 0.003, 0.42, 4);
  const rainMat = new THREE.MeshBasicMaterial({
    color: '#d8cfb8',
    transparent: true,
    opacity: 0.42,
    depthWrite: false,
  });
  const rainMesh = new THREE.InstancedMesh(rainGeo, rainMat, RAIN_COUNT);
  rainMesh.frustumCulled = false;
  rainMesh.renderOrder = 23;
  rainMesh.visible = false;
  triassicRoot.add(rainMesh);
  const rainSeeds = Array.from({ length: RAIN_COUNT }, (_, i) => ({
    x0: -3.2 + ((i * 0.618034) % 1.0) * 6.4,
    y0: 1.55 + ((i * 0.381966) % 1.0) * 2.6,
    z0: -2.4 + ((i * 0.754877) % 1.0) * 2.2,
    spd: 6.5 + (i % 5) * 1.1,
  }));

  // Forked Monsoon Lightning Bolt + Plasma Halo in Distant Triassic Sky (`S09`)
  const lightningBolt = new THREE.Group();
  const boltPts = [
    new THREE.Vector3(-0.95, 3.65, -4.8),
    new THREE.Vector3(-0.74, 3.05, -4.8),
    new THREE.Vector3(-0.88, 2.58, -4.8),
    new THREE.Vector3(-0.62, 2.04, -4.8),
    new THREE.Vector3(-0.72, 1.52, -4.8),
  ];
  const forkPts = [
    new THREE.Vector3(-0.88, 2.58, -4.8),
    new THREE.Vector3(-1.16, 2.12, -4.8),
    new THREE.Vector3(-1.28, 1.72, -4.8),
  ];
  const boltCurve = new THREE.CatmullRomCurve3(boltPts);
  const forkCurve = new THREE.CatmullRomCurve3(forkPts);
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
  // SHARED ROGER DEAKINS DESERT SUN + SKY FILL + WARM BOUNCE + 30 Hz SHADOWS
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
  fossilCoreLight.position.set(0.0, 0.55, 0.32);
  scene.add(fossilCoreLight);

  // Wind-blown golden Karoo quartz dust motes (`loopDurationS: 36.0` -> zero seam jump!)
  const dust = createLoopLockedDustMotes({
    count: 52,
    radius: 0.009,
    color: '#ffe4b4',
    loopDurationS: DURATION,
    bounds: { x0: -2.5, xSpan: 5.0, y0: 0.24, ySpan: 2.3, z0: -2.0, zSpan: 2.6 },
    renderOrder: 24,
  });
  scene.add(dust.mesh);

  const shadowRig = createTexelSnappedShadowRig(renderer, { mapSize: 512 });

  function updateRainAndNotebook(time, isStorm, stormStrength) {
    // Gentle loop-locked Karoo breeze on field notebook corner (`3 * 2pi / 36s`)
    const w0 = (Math.PI * 2.0) / DURATION;
    notebook.flutterPage.rotation.y = 0.035 + 0.032 * Math.sin(3.0 * w0 * time) + 0.015 * Math.cos(6.0 * w0 * time);

    // Wind sway on Triassic surface ferns
    for (let i = 0; i < triassicFerns.length; i++) {
      const sway = isStorm
        ? 0.22 * stormStrength + 0.12 * Math.sin(time * 16.0 + i)
        : 0.035 * Math.sin(4.0 * w0 * time + i * 1.4);
      triassicFerns[i].rotation.z = -sway;
    }

    // Monsoon diagonal rain sheets (`S09-S10`)
    rainMesh.visible = isStorm && stormStrength > 0.08;
    if (rainMesh.visible) {
      rainMat.opacity = 0.42 * stormStrength;
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
    sunSliceCurtain,
    notebook,
    triassicRoot,
    burrowRig,
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
    updateRainAndNotebook,
  };
}
