import * as THREE from 'three';
import {
  mulberry32,
  buildNormalFromCanvas,
  buildMetricRulerTexture,
  makeImaxMaterial,
} from '../core/pbr_shadow_sdk.js';
import {
  GLM,
  buildLoftGeometry,
  createGroundContactAO,
} from '../core/sculpt_ik_rig_sdk.js';

/**
 * Monarch V6 Hollywood IMAX Cinema SDK — Extinct Life Paleontology & Triassic Burrow Plugin Suite
 * (`plugins/karoo_burrow_plugins.js`)
 *
 * Specimen: BP/1/5558 (Early Triassic ~250 Ma, Karoo Basin, South Africa — Fernandez et al., PLOS ONE 2013)
 *   1. Procedural Sedimentary Sandstone, Proto-Fur & Amphibian Skin Sobel Normal Textures
 *   2. ESRF Synchrotron X-Ray Tomography Rotary Gantry & Scale Stage
 *   3. Dual-Mode Karoo Sandstone Cast (`uScanX` Opaque Rock <-> Translucent Quartz-Amber X-Ray Shell)
 *      housing TWO Full 3D Articulated Vertebrate Skeletons (`Thrinaxodon` + `Broomistega` with 3 Healing Rib Calluses!)
 *   4. 250-Million-Year-Old Cutaway Underground Karoo Burrow + 2-Bone IK Crawling Amphibian + Breathing Dormant Cynodont
 *   5. Monsoon Flash-Flood Turbulent Surge Wave + 160 Swirling Silt/Bubble Particles + Sedimentary Petrification
 */

// =============================================================================
// 1. PROCEDURAL SEDIMENTARY STRATA, PROTO-FUR & WET AMPHIBIAN SKIN TEXTURES
// =============================================================================
export function buildKarooSandstoneTextures(seed = 2501) {
  const S = 512;
  const cv = document.createElement('canvas');
  cv.width = cv.height = S;
  const ctx = cv.getContext('2d');
  const rng = mulberry32(seed);

  ctx.fillStyle = '#7d4b34';
  ctx.fillRect(0, 0, S, S);

  // Fine Triassic sedimentary bedding laminae
  for (let y = 0; y < S; y += 3) {
    const wave = Math.sin(y * 0.045) * 6.0;
    const tone = 0.82 + 0.34 * (0.5 + 0.5 * Math.sin(y * 0.09 + rng() * 0.5));
    const r = Math.round(134 * tone);
    const g = Math.round(82 * tone);
    const b = Math.round(56 * tone);
    ctx.strokeStyle = `rgba(${r},${g},${b},0.55)`;
    ctx.lineWidth = 2.6;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.bezierCurveTo(S * 0.33, y + wave, S * 0.66, y - wave, S, y);
    ctx.stroke();
  }

  // Quartz & feldspar sand grains + dark ironstone speckles
  for (let i = 0; i < 3600; i++) {
    const x = rng() * S;
    const y = rng() * S;
    const rad = 0.6 + rng() * 1.9;
    ctx.fillStyle = rng() > 0.42 ? 'rgba(218,172,130,0.22)' : 'rgba(42,22,14,0.26)';
    ctx.beginPath();
    ctx.arc(x, y, rad, 0, Math.PI * 2);
    ctx.fill();
  }

  const albedo = new THREE.CanvasTexture(cv);
  albedo.colorSpace = THREE.SRGBColorSpace;
  albedo.wrapS = albedo.wrapT = THREE.RepeatWrapping;
  const normal = buildNormalFromCanvas(cv, 2.6, 512);
  return { albedo, normal };
}

export function buildOrganicCreatureTextures(seed = 8812, isFieldSun = false) {
  const S = 256;
  const rng = mulberry32(seed);

  // A. Cynodont Russet Proto-Fur Texture
  const furCv = document.createElement('canvas');
  furCv.width = furCv.height = S;
  const fctx = furCv.getContext('2d');
  fctx.fillStyle = '#8b5638';
  fctx.fillRect(0, 0, S, S);
  for (let i = 0; i < 2400; i++) {
    const x = rng() * S;
    const y = rng() * S;
    fctx.strokeStyle = rng() > 0.45 ? 'rgba(178,122,82,0.28)' : 'rgba(52,28,16,0.30)';
    fctx.lineWidth = 1.1;
    fctx.beginPath();
    fctx.moveTo(x, y);
    fctx.lineTo(x + 5 + rng() * 5, y + (rng() - 0.5) * 2.5);
    fctx.stroke();
  }
  const furAlbedo = new THREE.CanvasTexture(furCv);
  furAlbedo.colorSpace = THREE.SRGBColorSpace;
  furAlbedo.wrapS = furAlbedo.wrapT = THREE.RepeatWrapping;
  const furNormal = buildNormalFromCanvas(furCv, 1.8, 256);

  // B. Temnospondyl Mottled Olive-Ochre / Mud-Sienna Amphibian Skin Texture (Zero Teal in Field Mode!)
  const skinCv = document.createElement('canvas');
  skinCv.width = skinCv.height = S;
  const sctx = skinCv.getContext('2d');
  sctx.fillStyle = isFieldSun ? '#6d5e3f' : '#485c52';
  sctx.fillRect(0, 0, S, S);
  for (let i = 0; i < 420; i++) {
    const x = rng() * S;
    const y = rng() * S;
    const rad = 2.0 + rng() * 7.5;
    if (isFieldSun) {
      sctx.fillStyle = rng() > 0.5 ? 'rgba(154,126,78,0.28)' : 'rgba(58,42,26,0.32)';
    } else {
      sctx.fillStyle = rng() > 0.5 ? 'rgba(98,128,108,0.24)' : 'rgba(26,36,32,0.28)';
    }
    sctx.beginPath();
    sctx.arc(x, y, rad, 0, Math.PI * 2);
    sctx.fill();
  }
  const skinAlbedo = new THREE.CanvasTexture(skinCv);
  skinAlbedo.colorSpace = THREE.SRGBColorSpace;
  skinAlbedo.wrapS = skinAlbedo.wrapT = THREE.RepeatWrapping;
  const skinNormal = buildNormalFromCanvas(skinCv, 1.5, 256);

  return { furAlbedo, furNormal, skinAlbedo, skinNormal };
}


// =============================================================================
// 2. ESRF SYNCHROTRON TOMOGRAPHY LAB STAGE (`Set A`)
// =============================================================================
export function createSynchrotronLabStage({ yFloor = 0.0 } = {}) {
  const group = new THREE.Group();

  const ao = createGroundContactAO({ width: 5.8, depth: 5.8, opacity: 0.72, floorY: yFloor });
  group.add(ao);

  const darkMetal = makeImaxMaterial({
    color: '#141c26',
    specular: '#8cd8eb',
    specPower: 0.55,
    rimTint: [0.24, 0.72, 0.85],
    rimStrength: 0.24,
  });
  const brassMat = makeImaxMaterial({
    color: '#c89b4b',
    specular: '#fff0c2',
    specPower: 0.68,
    rimTint: [0.95, 0.78, 0.42],
    rimStrength: 0.28,
  });

  // Tiered Rotary Gantry Plinth
  const baseDisc = new THREE.Mesh(new THREE.CylinderGeometry(1.38, 1.52, 0.16, 72), darkMetal);
  baseDisc.position.y = yFloor + 0.08;
  baseDisc.castShadow = true;
  baseDisc.receiveShadow = true;
  group.add(baseDisc);

  const rotaryTurntable = new THREE.Group();
  rotaryTurntable.position.y = yFloor + 0.16;
  group.add(rotaryTurntable);

  const upperPlatter = new THREE.Mesh(new THREE.CylinderGeometry(1.16, 1.24, 0.14, 72), darkMetal);
  upperPlatter.position.y = 0.07;
  upperPlatter.castShadow = true;
  upperPlatter.receiveShadow = true;
  rotaryTurntable.add(upperPlatter);

  const brassRing = new THREE.Mesh(new THREE.TorusGeometry(1.20, 0.016, 12, 72), brassMat);
  brassRing.rotation.x = Math.PI / 2;
  brassRing.position.y = 0.135;
  rotaryTurntable.add(brassRing);

  // Cyan Telemetry Glow Ring around Turntable
  const cyanRingMat = new THREE.MeshBasicMaterial({ color: '#3ad4be' });
  const cyanRing = new THREE.Mesh(new THREE.TorusGeometry(1.39, 0.008, 8, 72), cyanRingMat);
  cyanRing.rotation.x = Math.PI / 2;
  cyanRing.position.y = yFloor + 0.162;
  group.add(cyanRing);

  // Physical Paleontology 10cm Metric Scale Bar resting on front of stage!
  const rulerTex = buildMetricRulerTexture();
  const scaleBlock = new THREE.Mesh(
    new THREE.BoxGeometry(0.56, 0.036, 0.075),
    makeImaxMaterial({ color: '#e8eef2', map: rulerTex, specPower: 0.35 })
  );
  scaleBlock.position.set(0.0, 0.158, 0.96);
  scaleBlock.rotation.x = -0.22;
  scaleBlock.castShadow = true;
  rotaryTurntable.add(scaleBlock);

  // Left & Right Synchrotron X-Ray Beamline Emitter / Detector Arms (placed wide so 9:16 center stays clean!)
  function buildBeamArm(sideSign) {
    const arm = new THREE.Group();
    const pillar = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.11, 1.55, 24), darkMetal);
    pillar.position.set(sideSign * 1.95, yFloor + 0.775, -0.35);
    arm.add(pillar);

    const head = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.19, 0.34, 28), darkMetal);
    head.rotation.z = Math.PI / 2;
    head.position.set(sideSign * 1.72, yFloor + 0.88, -0.15);
    arm.add(head);

    const lens = new THREE.Mesh(
      new THREE.CircleGeometry(0.13, 28),
      new THREE.MeshBasicMaterial({ color: sideSign < 0 ? '#3ad4be' : '#f7c35f' })
    );
    lens.rotation.y = sideSign < 0 ? Math.PI / 2 : -Math.PI / 2;
    lens.position.set(sideSign * 1.54, yFloor + 0.88, -0.15);
    arm.add(lens);
    return arm;
  }
  group.add(buildBeamArm(-1), buildBeamArm(+1));

  return { group, rotaryTurntable, cyanRingMat };
}


// =============================================================================
// HELPER: PARAMETRIC VERTEBRATE SKULL & LIMB BUILDERS (`Zero Primitive Toys!`)
// =============================================================================
function buildCynodontSkullGeometry() {
  // Sculpted Thrinaxodon skull: narrow snout -> flared zygomatic cheekbones -> braincase!
  const profile = [
    // [zPos, widthHalf, heightTop, heightBot, yCenter]
    [ 0.24, 0.018,  0.022, -0.016,  0.00], // Nose tip
    [ 0.18, 0.036,  0.038, -0.026,  0.00], // Snout canine bulge
    [ 0.10, 0.044,  0.048, -0.030,  0.01], // Pre-orbital
    [ 0.01, 0.082,  0.056, -0.034,  0.01], // Wide zygomatic arches!
    [-0.08, 0.076,  0.062, -0.030,  0.02], // Sagittal crest & temporal fenestra
    [-0.15, 0.052,  0.048, -0.024,  0.01], // Occipital condyle
  ];
  const COLS = 20;
  const rings = profile.map(([z, rx, yt, yb, yc]) => {
    const ring = [];
    for (let c = 0; c < COLS; c++) {
      const a = (c / COLS) * Math.PI * 2;
      const ca = Math.cos(a);
      const sa = Math.sin(a);
      const wy = sa >= 0 ? yt : Math.abs(yb);
      // Cheekbone flare on horizontal sides
      const cheek = 1.0 + 0.16 * Math.pow(Math.abs(ca), 3.0) * (z < 0.05 && z > -0.11 ? 1.0 : 0.0);
      ring.push([ca * rx * cheek, yc + sa * wy, z]);
    }
    return ring;
  });
  return buildLoftGeometry(rings, true, true);
}

function buildTemnospondylSkullGeometry() {
  // Organic broad parabolic skull of Broomistega putterilli with domed cranial table & natural snout!
  const profile = [
    // [zPos, widthHalf, heightTop, heightBot]
    [ 0.19, 0.038, 0.022, -0.014], // Rounded snout tip
    [ 0.13, 0.078, 0.034, -0.018], // Parabolic widening
    [ 0.05, 0.108, 0.044, -0.022], // Mid-orbital cranial dome
    [-0.04, 0.126, 0.048, -0.024], // Broadest cheek/otic notch
    [-0.12, 0.108, 0.040, -0.020], // Posterior skull roof blending into neck
  ];
  const COLS = 22;
  const rings = profile.map(([z, rx, yt, yb]) => {
    const ring = [];
    for (let c = 0; c < COLS; c++) {
      const a = (c / COLS) * Math.PI * 2;
      const ca = Math.cos(a);
      const sa = Math.sin(a);
      const wy = sa >= 0 ? yt : Math.abs(yb);
      ring.push([ca * rx, sa * wy, z]);
    }
    return ring;
  });
  return buildLoftGeometry(rings, true, true);
}

function buildIKBoneLimb(hipPos, footPos, L1, L2, poleDir, boneMat, radius = 0.013) {
  const grp = new THREE.Group();
  const knee = GLM.solveTwoBoneIK(hipPos, footPos, L1, L2, poleDir);
  const up = new THREE.Vector3(0, 1, 0);

  function seg(pA, pB, rTop, rBot) {
    const dir = new THREE.Vector3().subVectors(pB, pA);
    const len = Math.max(0.01, dir.length());
    const m = new THREE.Mesh(new THREE.CylinderGeometry(rTop, rBot, len, 10), boneMat);
    m.position.copy(pA).addScaledVector(dir.normalize(), len * 0.5);
    m.quaternion.setFromUnitVectors(up, dir);
    m.renderOrder = 7;
    return m;
  }

  grp.add(seg(hipPos, knee, radius * 1.15, radius * 0.90));
  grp.add(seg(knee, footPos, radius * 0.88, radius * 0.68));
  const condyle = new THREE.Mesh(new THREE.SphereGeometry(radius * 1.18, 10, 8), boneMat);
  condyle.position.copy(knee);
  condyle.renderOrder = 7;
  grp.add(condyle);

  // 3 tiny toe phalanges at footPos
  for (let d = -1; d <= 1; d++) {
    const toeEnd = footPos.clone().add(new THREE.Vector3(d * 0.018, -0.004, 0.032));
    grp.add(seg(footPos, toeEnd, radius * 0.48, radius * 0.25));
  }
  return grp;
}


// =============================================================================
// 3. SPECIMEN BP/1/5558: KAROO SANDSTONE CAST + DUAL ARTICULATED 3D SKELETONS
// =============================================================================
export function createKarooRockAndDualFossilRig({ yBase = 0.30, paletteMode = 'synchrotron_lab' } = {}) {
  const isFieldSun = paletteMode === 'karoo_field_sun';
  const root = new THREE.Group();
  root.position.y = yBase;
  const rng = mulberry32(5558);

  const sandstoneTex = buildKarooSandstoneTextures(2501);

  // --- A. Sculpted Natural Burrow-Cast Sandstone Boulder (`buildLoftGeometry`, 34x40) ---
  const ROWS = 34;
  const COLS = 40;
  const rockRings = [];
  for (let r = 0; r < ROWS; r++) {
    const u = r / (ROWS - 1); // 0 -> 1 along X axis (-0.86 .. +0.86)
    const x = (u - 0.5) * 1.72;
    // Taper smoothly at both ends like a real natural sandstone burrow infill cast!
    const endProfile = Math.sin(Math.pow(u, 0.88) * Math.PI);
    const rxZ = (0.14 + 0.46 * Math.pow(endProfile, 0.68)) * (1.0 + 0.06 * Math.sin(u * 9.0));
    const ryY = (0.10 + 0.29 * Math.pow(endProfile, 0.62)) * (1.0 + 0.05 * Math.cos(u * 7.0));
    const zBend = Math.sin(u * Math.PI) * 0.08;

    const ring = [];
    for (let c = 0; c < COLS; c++) {
      const a = (c / COLS) * Math.PI * 2;
      const ca = Math.cos(a);
      const sa = Math.sin(a);
      // Flatten bottom slightly so rock sits naturally on pedestal + organic sedimentary facets!
      const flatBot = sa < 0 ? 0.62 : 1.05;
      const crag = 1.0
        + 0.055 * Math.sin(a * 3.0 + u * 8.0)
        + 0.035 * Math.cos(a * 5.0 - u * 11.0)
        + 0.020 * Math.sin(a * 9.0 + u * 15.0);
      const py = 0.24 + sa * ryY * flatBot * crag;
      const pz = zBend + ca * rxZ * crag;
      ring.push([x, Math.max(0.01, py), pz]);
    }
    rockRings.push(ring);
  }
  const rockGeo = buildLoftGeometry(rockRings, true, true);

  // Dual-Mode Synchrotron Tomography Shader:
  //   - Unscanned region (`vLocal.x > uScanX`): Tactile opaque Karoo sandstone (`alpha = 1.0`)
  //   - Laser plane (`|vLocal.x - uScanX| < 0.055`): Blazing Cyan-Gold Tomography Rim Slice
  //   - Scanned X-Ray region (`vLocal.x <= uScanX`): Translucent Quartz-Amber Hologram Shell (`alpha ~ 0.16 + fresnel`)!
  const rockXrayMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.FrontSide,
    uniforms: {
      tSand: { value: sandstoneTex.albedo },
      tNorm: { value: sandstoneTex.normal },
      uScanX: { value: -1.35 },
      uSolidBoost: { value: 1.0 },
      uTime: { value: 0.0 },
      uFieldMode: { value: isFieldSun ? 1.0 : 0.0 },
    },
    vertexShader: `
      varying vec3 vLocal;
      varying vec3 vWorldPos;
      varying vec3 vWorldNormal;
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
      uniform float uScanX;
      uniform float uSolidBoost;
      uniform float uTime;
      uniform float uFieldMode;
      varying vec3 vLocal;
      varying vec3 vWorldPos;
      varying vec3 vWorldNormal;
      varying vec2 vUv;

      void main() {
        vec3 nTex = texture2D(tNorm, vUv).xyz * 2.0 - 1.0;
        vec3 N = normalize(vWorldNormal + vec3(nTex.x, nTex.y, 0.0) * 0.32);
        vec3 V = normalize(cameraPosition - vWorldPos);
        float ndv = clamp(abs(dot(N, V)), 0.0, 1.0);
        float fresnel = pow(1.0 - ndv, 2.5);

        vec3 Lkey = normalize(vec3(0.52, 0.78, 0.36));
        vec3 Lrim = normalize(vec3(-0.68, 0.42, -0.58));
        float diff = max(dot(N, Lkey), 0.0);
        float rim  = pow(max(dot(N, Lrim), 0.0), 2.0);
        vec3 R = reflect(-V, N);
        float spec = pow(max(dot(R, Lkey), 0.0), 28.0);

        vec3 baseSand = texture2D(tSand, vUv).rgb;
        vec3 rimTint = mix(vec3(0.32, 0.86, 0.82), vec3(0.82, 0.64, 0.46), uFieldMode);
        vec3 solidCol = baseSand * (0.28 + 0.90 * diff)
                      + vec3(1.0, 0.82, 0.58) * spec * 0.24
                      + rimTint * rim * 0.28
                      + vec3(0.95, 0.70, 0.40) * fresnel * 0.22;

        float scanned = 1.0 - smoothstep(uScanX - 0.06, uScanX + 0.06, vLocal.x);
        float laserBand = exp(-pow((vLocal.x - uScanX) / 0.038, 2.0));

        vec3 xrayRimCol = mix(vec3(0.32, 0.90, 0.84), vec3(0.94, 0.72, 0.42), uFieldMode);
        vec3 xrayShell = mix(vec3(0.16, 0.09, 0.05), xrayRimCol, fresnel * 0.78)
                       + vec3(0.98, 0.78, 0.42) * pow(fresnel, 1.6) * 0.42;
        float xrayAlpha = clamp(0.11 + 0.42 * fresnel, 0.11, 0.58);

        float effScan = scanned * (1.0 - 0.0 * uSolidBoost);
        vec3 col = mix(solidCol, xrayShell, effScan);
        vec3 bandCol = mix(
          mix(vec3(0.30, 0.98, 0.90), vec3(1.0, 0.86, 0.42), 0.4),
          vec3(1.0, 0.82, 0.44),
          uFieldMode
        );
        col += bandCol * laserBand * 1.65;

        float alpha = mix(0.985, xrayAlpha, effScan);
        alpha = clamp(alpha + laserBand * 0.50, 0.10, 0.99);
        gl_FragColor = vec4(col, alpha);
      }
    `,
  });

  // Opaque inner shadow-caster rock core (only visible when unscanned so solid rock casts crisp shadow & hides bones 100%!)
  const solidCoreMat = new THREE.ShaderMaterial({
    uniforms: {
      tSand: { value: sandstoneTex.albedo },
      tNorm: { value: sandstoneTex.normal },
      uScanX: { value: -1.35 },
      uFieldMode: { value: isFieldSun ? 1.0 : 0.0 },
    },
    vertexShader: `
      varying vec3 vLocal;
      varying vec3 vWorldPos;
      varying vec3 vWorldNormal;
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
      uniform float uScanX;
      uniform float uFieldMode;
      varying vec3 vLocal;
      varying vec3 vWorldPos;
      varying vec3 vWorldNormal;
      varying vec2 vUv;
      void main() {
        if (vLocal.x <= uScanX + 0.02) discard;
        vec3 nTex = texture2D(tNorm, vUv).xyz * 2.0 - 1.0;
        vec3 N = normalize(vWorldNormal + vec3(nTex.x, nTex.y, 0.0) * 0.32);
        vec3 V = normalize(cameraPosition - vWorldPos);
        float fresnel = pow(1.0 - clamp(abs(dot(N, V)), 0.0, 1.0), 2.5);
        vec3 Lkey = normalize(vec3(0.52, 0.78, 0.36));
        vec3 Lrim = normalize(vec3(-0.68, 0.42, -0.58));
        float diff = max(dot(N, Lkey), 0.0);
        float rim  = pow(max(dot(N, Lrim), 0.0), 2.0);
        vec3 baseSand = texture2D(tSand, vUv).rgb;
        vec3 rimTint = mix(vec3(0.32, 0.86, 0.82), vec3(0.82, 0.64, 0.46), uFieldMode);
        vec3 col = baseSand * (0.30 + 0.88 * diff)
                 + rimTint * rim * 0.28
                 + vec3(0.95, 0.70, 0.40) * fresnel * 0.22;
        gl_FragColor = vec4(col, 1.0);
      }
    `,
  });

  const rockSolidCore = new THREE.Mesh(rockGeo, solidCoreMat);
  rockSolidCore.castShadow = true;
  rockSolidCore.receiveShadow = true;
  rockSolidCore.renderOrder = 9;
  root.add(rockSolidCore);

  const rockShell = new THREE.Mesh(rockGeo, rockXrayMat);
  rockShell.scale.setScalar(1.004);
  rockShell.renderOrder = 16;
  root.add(rockShell);

  // --- B. TWO HIGH-POLY ARTICULATED 3D FOSSIL SKELETONS INSIDE THE ROCK ---
  // Clearly separated spatially inside the burrow cast so BOTH skeletons read 100% distinctly!
  const fossilsGroup = new THREE.Group();
  fossilsGroup.position.set(0.0, 0.22, 0.0);
  root.add(fossilsGroup);

  const mammalBoneMat = new THREE.MeshStandardMaterial({
    color: isFieldSun ? '#f3dfc1' : '#f5cf7e',
    emissive: isFieldSun ? '#4a2b10' : '#52340c',
    emissiveIntensity: 0.20,
    roughness: 0.36,
    metalness: 0.04,
  });

  const amphibBoneMat = new THREE.MeshStandardMaterial({
    color: isFieldSun ? '#ded8cb' : '#7ef2e8',
    emissive: isFieldSun ? '#383028' : '#0c464e',
    emissiveIntensity: 0.20,
    roughness: 0.38,
    metalness: 0.04,
  });

  // 1) THRINAXODON (Curled Mammal-Relative Skeleton — Left-Back C-Coil!)
  const thrinaxGroup = new THREE.Group();
  thrinaxGroup.position.set(-0.20, 0.02, -0.10);
  fossilsGroup.add(thrinaxGroup);

  const thrinaxSkull = new THREE.Mesh(buildCynodontSkullGeometry(), mammalBoneMat);
  thrinaxSkull.position.set(-0.18, 0.06, 0.14);
  thrinaxSkull.rotation.set(0.12, 1.24, -0.16);
  thrinaxSkull.renderOrder = 6;
  thrinaxGroup.add(thrinaxSkull);

  // Differentiated Canine Fang Pair on Cynodont Snout!
  for (const sgn of [-1, 1]) {
    const fang = new THREE.Mesh(new THREE.ConeGeometry(0.008, 0.034, 8), mammalBoneMat);
    fang.rotation.x = Math.PI;
    fang.position.set(sgn * 0.026, -0.028, 0.17);
    thrinaxSkull.add(fang);
  }

  // Curled C-Coil Spine + Tail (`CatmullRomCurve3`)
  const thrinaxSpineCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-0.28, 0.06,  0.07), // Neck behind skull
    new THREE.Vector3(-0.40, 0.05, -0.07), // Anterior thorax
    new THREE.Vector3(-0.31, 0.04, -0.21), // Mid-thorax curl
    new THREE.Vector3(-0.10, 0.03, -0.22), // Lumbar curve
    new THREE.Vector3( 0.07, 0.02, -0.11), // Sacrum / pelvis
    new THREE.Vector3( 0.05, 0.01,  0.07), // Tail base curling around
    new THREE.Vector3(-0.08, 0.00,  0.17), // Tail tip near snout!
  ]);

  const vertGeo = new THREE.CylinderGeometry(0.017, 0.019, 0.024, 10);
  vertGeo.rotateZ(Math.PI / 2);
  const THRINAX_VERTS = 28;
  const thrinaxVerts = new THREE.InstancedMesh(vertGeo, mammalBoneMat, THRINAX_VERTS);
  thrinaxVerts.renderOrder = 6;
  thrinaxGroup.add(thrinaxVerts);

  const dummy = new THREE.Object3D();
  for (let i = 0; i < THRINAX_VERTS; i++) {
    const u = i / (THRINAX_VERTS - 1);
    const pt = thrinaxSpineCurve.getPoint(u);
    const tan = thrinaxSpineCurve.getTangent(u);
    dummy.position.copy(pt);
    dummy.lookAt(pt.clone().add(tan));
    const sc = u < 0.68 ? (1.05 - 0.25 * u) : (0.88 * (1.0 - (u - 0.68) * 2.2));
    dummy.scale.setScalar(Math.max(0.28, sc));
    dummy.updateMatrix();
    thrinaxVerts.setMatrixAt(i, dummy.matrix);

    // Thoracic & Lumbar Rib Pairs (`i = 2 .. 16`)
    if (i >= 2 && i <= 16) {
      const ribFrac = Math.sin(((i - 2) / 14) * Math.PI);
      const ribLen = 0.075 + 0.065 * ribFrac;
      const normalSide = new THREE.Vector3(-tan.z, 0, tan.x).normalize();
      for (const sgn of [-1, 1]) {
        const ribCurve = new THREE.CatmullRomCurve3([
          pt.clone(),
          pt.clone().addScaledVector(normalSide, sgn * ribLen * 0.65).add(new THREE.Vector3(0, 0.028, 0)),
          pt.clone().addScaledVector(normalSide, sgn * ribLen).add(new THREE.Vector3(0, -0.028, 0)),
        ]);
        const ribMesh = new THREE.Mesh(new THREE.TubeGeometry(ribCurve, 10, 0.0065, 6, false), mammalBoneMat);
        ribMesh.renderOrder = 6;
        thrinaxGroup.add(ribMesh);
      }
    }
  }

  // 4 Articulated IK Limbs tucked into sleeping coil
  thrinaxGroup.add(
    buildIKBoneLimb(new THREE.Vector3(-0.44, 0.05, -0.04), new THREE.Vector3(-0.30, 0.00, 0.11), 0.11, 0.10, new THREE.Vector3(-1, 0.4, 0), mammalBoneMat, 0.012),
    buildIKBoneLimb(new THREE.Vector3(-0.42, 0.04, -0.14), new THREE.Vector3(-0.26, 0.00, -0.04), 0.11, 0.10, new THREE.Vector3(0, 0.5, -1), mammalBoneMat, 0.012),
    buildIKBoneLimb(new THREE.Vector3( 0.02, 0.03, -0.16), new THREE.Vector3(-0.10, 0.00, -0.04), 0.12, 0.11, new THREE.Vector3(1, 0.5, 0), mammalBoneMat, 0.013),
    buildIKBoneLimb(new THREE.Vector3( 0.05, 0.02, -0.08), new THREE.Vector3(-0.06, 0.00,  0.08), 0.12, 0.11, new THREE.Vector3(1, 0.4, 0.5), mammalBoneMat, 0.013)
  );

  // 2) BROOMISTEGA (Supine/Stretched Amphibian Skeleton — Right-Front Side with 3 Healing Rib Calluses!)
  const broomGroup = new THREE.Group();
  broomGroup.position.set(0.16, 0.00, 0.14);
  fossilsGroup.add(broomGroup);

  const broomSkull = new THREE.Mesh(buildTemnospondylSkullGeometry(), amphibBoneMat);
  broomSkull.position.set(0.38, 0.08, 0.12);
  broomSkull.rotation.set(-0.08, -1.12, 0.08);
  broomSkull.renderOrder = 7;
  broomGroup.add(broomSkull);

  // Sculpted Dark Eye-Orbit Openings on Flat Temnospondyl Skull Roof!
  const orbitHoleMat = new THREE.MeshBasicMaterial({ color: '#091822' });
  for (const sgn of [-1, 1]) {
    const orb = new THREE.Mesh(new THREE.CylinderGeometry(0.024, 0.024, 0.014, 14), orbitHoleMat);
    orb.position.set(sgn * 0.046, 0.024, 0.04);
    broomSkull.add(orb);
  }

  const broomSpineCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3( 0.27, 0.07,  0.07), // Neck behind broad skull
    new THREE.Vector3( 0.14, 0.06,  0.02), // Anterior trunk (healing ribs zone!)
    new THREE.Vector3(-0.02, 0.05, -0.01), // Mid-trunk alongside Thrinaxodon
    new THREE.Vector3(-0.18, 0.04,  0.01), // Pelvic zone
    new THREE.Vector3(-0.34, 0.03,  0.08), // Tail base
    new THREE.Vector3(-0.48, 0.02,  0.17), // Tapered amphibian tail
  ]);

  const BROOM_VERTS = 24;
  const broomVerts = new THREE.InstancedMesh(vertGeo, amphibBoneMat, BROOM_VERTS);
  broomVerts.renderOrder = 7;
  broomGroup.add(broomVerts);

  // Diagnostic Callus Material for Healing Ribs #4, #5, #6 (#E63926 reserved vermilion in field mode when ribHighlight > 0!)
  const callusBoneRestCol = new THREE.Color('#ded8cb');
  const callusVermilionCol = new THREE.Color('#e63926');
  const callusEmissiveRest = new THREE.Color('#383028');
  const callusEmissiveHot = new THREE.Color('#b82012');
  const callusMat = new THREE.MeshStandardMaterial({
    color: isFieldSun ? '#ded8cb' : '#ffd466',
    emissive: isFieldSun ? '#383028' : '#ff9418',
    emissiveIntensity: isFieldSun ? 0.18 : 0.38,
    roughness: isFieldSun ? 0.34 : 0.24,
    metalness: 0.08,
  });
  const healingCallusAnchors = [];

  for (let i = 0; i < BROOM_VERTS; i++) {
    const u = i / (BROOM_VERTS - 1);
    const pt = broomSpineCurve.getPoint(u);
    const tan = broomSpineCurve.getTangent(u);
    dummy.position.copy(pt);
    dummy.lookAt(pt.clone().add(tan));
    const sc = u < 0.65 ? 0.96 : 0.92 * (1.0 - (u - 0.65) * 2.0);
    dummy.scale.setScalar(Math.max(0.25, sc));
    dummy.updateMatrix();
    broomVerts.setMatrixAt(i, dummy.matrix);

    if (i >= 2 && i <= 13) {
      const ribIdx = i - 1; // 1..12
      const ribFrac = Math.sin(((i - 2) / 11) * Math.PI);
      const ribLen = 0.082 + 0.062 * ribFrac;
      const normalSide = new THREE.Vector3(-tan.z, 0, tan.x).normalize();

      for (const sgn of [-1, 1]) {
        const midPt = pt.clone().addScaledVector(normalSide, sgn * ribLen * 0.62).add(new THREE.Vector3(0, 0.026, 0));
        const tipPt = pt.clone().addScaledVector(normalSide, sgn * ribLen).add(new THREE.Vector3(0, -0.018, 0));
        const ribCurve = new THREE.CatmullRomCurve3([pt.clone(), midPt, tipPt]);
        const ribMesh = new THREE.Mesh(new THREE.TubeGeometry(ribCurve, 10, 0.0068, 6, false), amphibBoneMat);
        ribMesh.renderOrder = 7;
        broomGroup.add(ribMesh);

        // RIBS #4, #5, #6 (sgn = +1, front/camera-facing flank): HEALING RIB FRACTURE CALLUSES!
        if (sgn === 1 && (ribIdx === 4 || ribIdx === 5 || ribIdx === 6)) {
          const callus = new THREE.Mesh(new THREE.SphereGeometry(0.016, 12, 10), callusMat);
          callus.scale.set(1.55, 1.05, 1.15);
          callus.position.copy(midPt);
          callus.lookAt(tipPt);
          callus.renderOrder = 8;
          broomGroup.add(callus);

          // Hairline healed fracture ring right at the center of the bone callus
          const fracRing = new THREE.Mesh(
            new THREE.TorusGeometry(0.0145, 0.0025, 8, 16),
            new THREE.MeshBasicMaterial({ color: '#4a2606' })
          );
          fracRing.position.copy(midPt);
          fracRing.lookAt(tipPt);
          fracRing.renderOrder = 8;
          broomGroup.add(fracRing);

          healingCallusAnchors.push(callus);
        }
      }
    }
  }

  // 4 Articulated Amphibian IK Limbs sprawled gently
  broomGroup.add(
    buildIKBoneLimb(new THREE.Vector3( 0.20, 0.06,  0.10), new THREE.Vector3( 0.28, 0.01,  0.25), 0.10, 0.09, new THREE.Vector3(0.4, 0.5, 1), amphibBoneMat, 0.011),
    buildIKBoneLimb(new THREE.Vector3( 0.18, 0.06, -0.04), new THREE.Vector3( 0.24, 0.01, -0.18), 0.10, 0.09, new THREE.Vector3(0.4, 0.5, -1), amphibBoneMat, 0.011),
    buildIKBoneLimb(new THREE.Vector3(-0.16, 0.04,  0.07), new THREE.Vector3(-0.12, 0.00,  0.22), 0.10, 0.09, new THREE.Vector3(-0.3, 0.5, 1), amphibBoneMat, 0.011),
    buildIKBoneLimb(new THREE.Vector3(-0.18, 0.04, -0.05), new THREE.Vector3(-0.16, 0.00, -0.19), 0.10, 0.09, new THREE.Vector3(-0.3, 0.5, -1), amphibBoneMat, 0.011)
  );

  // Subtle Diagnostic Callus Halo Ring (`S05_HEALING_RIBS_MACRO`)
  const diagHaloMat = new THREE.MeshBasicMaterial({
    color: isFieldSun ? '#e63926' : '#ffd166',
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const diagHalo = new THREE.Mesh(new THREE.RingGeometry(0.085, 0.102, 40), diagHaloMat);
  diagHalo.position.set(0.27, 0.09, 0.24);
  diagHalo.rotation.x = -0.55;
  diagHalo.renderOrder = 22;
  fossilsGroup.add(diagHalo);

  return {
    root,
    rockSolidCore,
    rockShell,
    rockXrayMat,
    solidCoreMat,
    fossilsGroup,
    thrinaxGroup,
    broomGroup,
    mammalBoneMat,
    amphibBoneMat,
    callusMat,
    healingCallusAnchors,
    diagHalo,
    diagHaloMat,
    update({ scanProgress = 0.0, ribHighlight = 0.0, speciesHighlight = 0.0, time = 0.0 }) {
      // scanProgress: 0 = 100% solid Karoo rock (Frame 0 & Frame 1079 -> exact loop!); 1 = 100% X-Ray tomography!
      const scanX = GLM.mix(-1.05, 1.05, GLM.clamp(scanProgress, 0, 1));
      rockXrayMat.uniforms.uScanX.value = scanX;
      solidCoreMat.uniforms.uScanX.value = scanX;
      rockXrayMat.uniforms.uTime.value = time;

      fossilsGroup.visible = scanProgress > 0.02;

      mammalBoneMat.emissiveIntensity = 0.18 + 0.18 * speciesHighlight;
      amphibBoneMat.emissiveIntensity = 0.20 + 0.20 * speciesHighlight;

      // Pulse the 3 fractured-rib bone calluses during forensic rib inspection!
      const pulse = 0.65 + 0.35 * Math.sin(time * 9.0);
      const rh = GLM.clamp(ribHighlight, 0, 1);
      if (isFieldSun) {
        callusMat.color.lerpColors(callusBoneRestCol, callusVermilionCol, rh);
        callusMat.emissive.lerpColors(callusEmissiveRest, callusEmissiveHot, rh);
        callusMat.emissiveIntensity = 0.18 + rh * 0.62 * pulse;
      } else {
        callusMat.emissiveIntensity = 0.25 + rh * 0.95 * pulse;
      }
      if (rh > 0.02) {
        diagHalo.visible = true;
        diagHaloMat.opacity = rh * (isFieldSun ? 0.55 : 0.78) * pulse;
        const sc = 0.92 + 0.12 * Math.sin(time * 6.0);
        diagHalo.scale.setScalar(sc);
      } else {
        diagHalo.visible = false;
      }
    },
  };
}


// =============================================================================
// 4. SET B: 250-MA EARLY TRIASSIC UNDERGROUND KAROO BURROW + LIVING ANIMALS
// =============================================================================
function buildLivingCynodontBody(furAlbedo, furNormal) {
  const grp = new THREE.Group();
  const bodyMat = makeImaxMaterial({
    color: '#9e623e',
    map: furAlbedo,
    normalMap: furNormal,
    normalScale: 0.65,
    specular: '#ffdcb8',
    specPower: 0.25,
    rimTint: [0.98, 0.72, 0.44],
    rimStrength: 0.32,
  });

  // Curled Sleeping Torso + Neck + Tail (`buildLoftGeometry` along C-coil!)
  const spine = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-0.22, 0.12,  0.14), // Neck
    new THREE.Vector3(-0.42, 0.14, -0.04), // Shoulder
    new THREE.Vector3(-0.34, 0.15, -0.24), // Ribcage (breathes!)
    new THREE.Vector3(-0.10, 0.14, -0.26), // Lower back
    new THREE.Vector3( 0.08, 0.11, -0.12), // Hip
    new THREE.Vector3( 0.05, 0.07,  0.10), // Curled tail mid
    new THREE.Vector3(-0.14, 0.05,  0.22), // Furry tail tip tucked by nose!
  ]);

  const RINGS = 32;
  const COLS = 20;
  const rings = [];
  for (let r = 0; r < RINGS; r++) {
    const u = r / (RINGS - 1);
    const pt = spine.getPoint(u);
    const tan = spine.getTangent(u).normalize();
    const side = new THREE.Vector3(-tan.z, 0, tan.x).normalize();
    const up = new THREE.Vector3().crossVectors(tan, side).normalize();

    // Plump mammal-relative torso tapering smoothly into furry tail
    const radProfile = u < 0.62
      ? (0.085 + 0.058 * Math.sin((u / 0.62) * Math.PI))
      : 0.085 * Math.max(0.18, 1.0 - (u - 0.62) / 0.38);

    const ring = [];
    for (let c = 0; c < COLS; c++) {
      const a = (c / COLS) * Math.PI * 2;
      const w = radProfile * 1.12;
      const h = radProfile * 0.88;
      const v = pt.clone()
        .addScaledVector(side, Math.cos(a) * w)
        .addScaledVector(up, Math.sin(a) * h);
      ring.push([v.x, Math.max(0.01, v.y), v.z]);
    }
    rings.push(ring);
  }
  const torsoMesh = new THREE.Mesh(buildLoftGeometry(rings, true, true), bodyMat);
  torsoMesh.castShadow = true;
  torsoMesh.receiveShadow = true;
  grp.add(torsoMesh);

  // Sculpted Sleeping Cynodont Head + Closed Eyelids + Wet Dark Nose
  const head = new THREE.Mesh(buildCynodontSkullGeometry(), bodyMat);
  head.scale.setScalar(1.22);
  head.position.set(-0.18, 0.12, 0.17);
  head.rotation.set(0.15, 1.25, -0.14);
  head.castShadow = true;
  grp.add(head);

  const nose = new THREE.Mesh(
    new THREE.SphereGeometry(0.022, 12, 10),
    makeImaxMaterial({ color: '#1c1210', specular: '#ffffff', specPower: 0.75 })
  );
  nose.position.set(0, 0.005, 0.245);
  head.add(nose);

  // Subtle small external pinnae/ear ridges
  for (const sgn of [-1, 1]) {
    const ear = new THREE.Mesh(new THREE.ConeGeometry(0.022, 0.038, 10), bodyMat);
    ear.position.set(sgn * 0.062, 0.052, -0.07);
    ear.rotation.set(-0.35, 0, -sgn * 0.45);
    head.add(ear);
  }

  return { grp, torsoMesh, head };
}

function buildLivingAmphibianRig(skinAlbedo, skinNormal, isFieldSun = false) {
  const root = new THREE.Group();
  const skinMat = makeImaxMaterial({
    color: isFieldSun ? '#7c6a48' : '#526b5c',
    map: skinAlbedo,
    normalMap: skinNormal,
    normalScale: 0.58,
    specular: isFieldSun ? '#f0d2a8' : '#c8f4ec',
    specPower: isFieldSun ? 0.58 : 0.72, // Wet glistening amphibian skin sheen!
    rimTint: isFieldSun ? [0.92, 0.68, 0.42] : [0.42, 0.90, 0.82],
    rimStrength: isFieldSun ? 0.28 : 0.36,
  });

  // Torso + Tail (`buildLoftGeometry`)
  const RINGS = 26;
  const COLS = 18;
  const rings = [];
  for (let r = 0; r < RINGS; r++) {
    const u = r / (RINGS - 1); // 0 = neck (+0.26) -> 1 = tail tip (-0.52)
    const z = GLM.mix(0.24, -0.54, u);
    const bodyEnv = u < 0.58
      ? (0.078 + 0.048 * Math.sin((u / 0.58) * Math.PI))
      : 0.078 * Math.max(0.14, 1.0 - (u - 0.58) / 0.42);
    const widthScale = u < 0.62 ? 1.28 : 0.55; // Flat wide trunk -> laterally compressed amphibian tail!
    const heightScale = u < 0.62 ? 0.74 : 0.95;

    const ring = [];
    for (let c = 0; c < COLS; c++) {
      const a = (c / COLS) * Math.PI * 2;
      ring.push([
        Math.cos(a) * bodyEnv * widthScale,
        0.085 + Math.sin(a) * bodyEnv * heightScale,
        z,
      ]);
    }
    rings.push(ring);
  }
  const bodyMesh = new THREE.Mesh(buildLoftGeometry(rings, true, true), skinMat);
  bodyMesh.castShadow = true;
  bodyMesh.receiveShadow = true;
  root.add(bodyMesh);

  // Subtle reddish-ochre bruised/healing scar patch over right ribs!
  const bruisePatch = new THREE.Mesh(
    new THREE.SphereGeometry(0.055, 14, 10),
    makeImaxMaterial({ color: '#8a4c3e', specular: '#ffd8c2', specPower: 0.55 })
  );
  bruisePatch.scale.set(0.45, 0.72, 1.45);
  bruisePatch.position.set(0.115, 0.095, 0.06);
  root.add(bruisePatch);

  // Broad Organic Temnospondyl Head + Subtle Recessed Dark-Amber Amphibian Eyes!
  const head = new THREE.Mesh(buildTemnospondylSkullGeometry(), skinMat);
  head.scale.setScalar(1.08);
  head.position.set(0, 0.088, 0.28);
  head.castShadow = true;
  root.add(head);

  const socketRimMat = makeImaxMaterial({ color: '#2b3a32', specPower: 0.45 });
  const eyeAmberMat = makeImaxMaterial({ color: '#9e6b24', specular: '#ffffff', specPower: 0.92 });
  const pupilMat = new THREE.MeshBasicMaterial({ color: '#06090b' });
  for (const sgn of [-1, 1]) {
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.015, 0.004, 8, 16), socketRimMat);
    rim.rotation.x = Math.PI / 2;
    rim.position.set(sgn * 0.042, 0.036, 0.045);
    head.add(rim);

    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.013, 12, 10), eyeAmberMat);
    eye.position.set(sgn * 0.042, 0.037, 0.045);
    head.add(eye);

    const pup = new THREE.Mesh(new THREE.SphereGeometry(0.0075, 10, 8), pupilMat);
    pup.position.set(sgn * 0.045, 0.041, 0.051);
    head.add(pup);
  }

  // 4 Dynamic 2-Bone IK Walking Legs (`solveTwoBoneIK` updated live every frame!)
  const legDefs = [
    { side: -1, zHip:  0.16, phase: 0.00 }, // Front-Left
    { side: +1, zHip:  0.16, phase: 0.50 }, // Front-Right (slightly guarded step near healing ribs!)
    { side: -1, zHip: -0.14, phase: 0.50 }, // Hind-Left
    { side: +1, zHip: -0.14, phase: 0.00 }, // Hind-Right
  ];
  const upAxis = new THREE.Vector3(0, 1, 0);
  const legs = legDefs.map((ld) => {
    const upper = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.018, 1.0, 10), skinMat);
    const lower = new THREE.Mesh(new THREE.CylinderGeometry(0.017, 0.013, 1.0, 10), skinMat);
    const foot  = new THREE.Mesh(new THREE.SphereGeometry(0.020, 10, 8), skinMat);
    foot.scale.set(1.2, 0.5, 1.5);
    upper.castShadow = lower.castShadow = true;
    root.add(upper, lower, foot);
    return { ...ld, upper, lower, foot };
  });

  const hipLocal = new THREE.Vector3();
  const footLocal = new THREE.Vector3();
  const poleLocal = new THREE.Vector3();
  const dirTmp = new THREE.Vector3();

  function updateLegs(walkCycle = 0.0, strideAmp = 1.0) {
    for (const lg of legs) {
      const cyc = (walkCycle + lg.phase) % 1.0;
      const swing = Math.sin(cyc * Math.PI * 2.0);
      const lift = Math.max(0, Math.cos(cyc * Math.PI * 2.0)) * 0.042 * strideAmp;
      hipLocal.set(lg.side * 0.11, 0.075, lg.zHip);
      footLocal.set(
        lg.side * 0.195,
        0.012 + lift,
        lg.zHip + swing * 0.068 * strideAmp
      );
      poleLocal.set(lg.side * 0.85, 0.65, 0.15);
      const knee = GLM.solveTwoBoneIK(hipLocal, footLocal, 0.088, 0.084, poleLocal);

      dirTmp.subVectors(knee, hipLocal);
      const len1 = dirTmp.length();
      lg.upper.scale.set(1, len1, 1);
      lg.upper.position.copy(hipLocal).addScaledVector(dirTmp.normalize(), len1 * 0.5);
      lg.upper.quaternion.setFromUnitVectors(upAxis, dirTmp);

      dirTmp.subVectors(footLocal, knee);
      const len2 = dirTmp.length();
      lg.lower.scale.set(1, len2, 1);
      lg.lower.position.copy(knee).addScaledVector(dirTmp.normalize(), len2 * 0.5);
      lg.lower.quaternion.setFromUnitVectors(upAxis, dirTmp);

      lg.foot.position.copy(footLocal);
    }
  }
  updateLegs(0, 0);

  return { root, bodyMesh, head, updateLegs };
}

export function createTriassicBurrowAndLivingPairRig({ paletteMode = 'synchrotron_lab' } = {}) {
  const isFieldSun = paletteMode === 'karoo_field_sun';
  const group = new THREE.Group();
  group.visible = false;

  const sandTex = buildKarooSandstoneTextures(3310);
  const orgTex = buildOrganicCreatureTextures(8812, isFieldSun);

  const burrowRockMat = makeImaxMaterial({
    color: isFieldSun ? '#8f5236' : '#8c5338',
    map: sandTex.albedo,
    normalMap: sandTex.normal,
    normalScale: 0.88,
    mapRepeat: [3, 2],
    specular: isFieldSun ? '#c9936a' : '#e6b48a',
    specPower: isFieldSun ? 0.14 : 0.22,
    rimTint: [0.94, 0.62, 0.36],
    rimStrength: isFieldSun ? 0.14 : 0.22,
    polygonOffset: true,
    polygonOffsetFactor: 1,
    polygonOffsetUnits: 1,
  });

  // Cutaway Half-Pipe Underground Burrow Tunnel + Terminal Sleeping Chamber (`buildLoftGeometry` open C-arch!)
  // Path descends from upper-left Triassic desert entrance (-1.55, 1.52) down 24° ramp into sheltered chamber (+0.15, 0.24)!
  const tunnelSpine = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-1.68, 1.52, -0.05), // Sun-lit burrow mouth
    new THREE.Vector3(-1.05, 1.02, -0.04), // Upper inclined sandstone ramp
    new THREE.Vector3(-0.45, 0.54, -0.02), // Lower tunnel throat
    new THREE.Vector3( 0.08, 0.28,  0.00), // Terminal sleeping chamber center!
    new THREE.Vector3( 0.68, 0.28,  0.02), // Rounded back chamber wall
  ]);

  const T_ROWS = 36;
  const T_COLS = 24;
  const tunnelRings = [];
  for (let r = 0; r < T_ROWS; r++) {
    const u = r / (T_ROWS - 1);
    const pt = tunnelSpine.getPoint(u);
    const chamberExpand = GLM.smoothstep(0.45, 0.82, u);
    const endClose = 1.0 - 0.72 * Math.pow(GLM.smoothstep(0.84, 1.0, u), 2.0);
    const radW = (0.48 + 0.34 * chamberExpand) * endClose;
    const radH = (0.42 + 0.28 * chamberExpand) * endClose;

    const ring = [];
    for (let c = 0; c < T_COLS; c++) {
      // Open front cutaway (`a` spans from -0.30*PI floor-front -> back wall -> +0.72*PI ceiling-lip!)
      const frac = c / (T_COLS - 1);
      const a = GLM.mix(-0.22 * Math.PI, 1.18 * Math.PI, frac);
      // Map angle so floor is flat/cradled, back wall curves behind (z < 0), roof arches overhead!
      const localY = -Math.cos(a) * radH + radH * 0.55;
      const localZ = -Math.sin(a) * radW;
      const crag = 1.0 + 0.05 * Math.sin(u * 14.0 + frac * 9.0);
      ring.push([
        pt.x,
        pt.y + localY * crag,
        pt.z + localZ * crag,
      ]);
    }
    tunnelRings.push(ring);
  }
  const burrowChamberGeo = buildLoftGeometry(tunnelRings, false, false);
  burrowRockMat.side = THREE.DoubleSide;
  const burrowChamber = new THREE.Mesh(burrowChamberGeo, burrowRockMat);
  burrowChamber.receiveShadow = true;
  burrowChamber.castShadow = true;
  group.add(burrowChamber);

  // Sandy Burrow Floor Bed inside Chamber + Sloped Ramp Floor
  const floorPts = [];
  for (let r = 0; r < T_ROWS; r++) {
    const u = r / (T_ROWS - 1);
    const pt = tunnelSpine.getPoint(u);
    const w = 0.44 + 0.30 * GLM.smoothstep(0.45, 0.80, u);
    floorPts.push([
      [pt.x, pt.y - 0.02, -w * 0.92],
      [pt.x, pt.y - 0.03,  0.0],
      [pt.x, pt.y - 0.01,  w * 0.68],
    ]);
  }
  const rampFloorMat = isFieldSun
    ? makeImaxMaterial({
        color: '#6b3e28',
        map: sandTex.albedo,
        normalMap: sandTex.normal,
        normalScale: 0.92,
        mapRepeat: [4, 2],
        specular: '#a67452',
        specPower: 0.06,
        rimTint: [0.78, 0.48, 0.28],
        rimStrength: 0.06,
      })
    : burrowRockMat;
  const rampFloor = new THREE.Mesh(buildLoftGeometry(floorPts, false, false), rampFloorMat);
  rampFloor.receiveShadow = true;
  group.add(rampFloor);

  // Cross-Section Earth Strata Framing Block surrounding the underground burrow cutaway
  const strataBackdrop = new THREE.Mesh(
    new THREE.PlaneGeometry(6.8, 4.4),
    makeImaxMaterial({
      color: '#3a2218',
      map: sandTex.albedo,
      normalMap: sandTex.normal,
      normalScale: 0.7,
      mapRepeat: [5, 3],
      specPower: 0.12,
    })
  );
  strataBackdrop.position.set(0.0, 1.35, -0.88);
  group.add(strataBackdrop);

  // Living Curled Thrinaxodon (Dormant in Back-Right of Terminal Chamber so both animals are clearly visible!)
  const livingCynodont = buildLivingCynodontBody(orgTex.furAlbedo, orgTex.furNormal);
  livingCynodont.grp.position.set(0.28, 0.26, -0.14);
  group.add(livingCynodont.grp);

  // Living Crawling Broomistega (Crawls down the sloped ramp and nestles beside Thrinaxodon!)
  const livingAmphib = buildLivingAmphRigWrapper(orgTex.skinAlbedo, orgTex.skinNormal, isFieldSun);
  group.add(livingAmphib.root);

  // Subtle Cyan Aestivation Metabolic Aura Ring (`S08_AESTIVATION_SLEEP`)
  const dormRingMat = new THREE.MeshBasicMaterial({
    color: '#3ad4be',
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const dormRing = new THREE.Mesh(new THREE.RingGeometry(0.36, 0.41, 48), dormRingMat);
  dormRing.rotation.x = -Math.PI / 2;
  dormRing.position.set(0.08, 0.28, -0.02);
  dormRing.renderOrder = 20;
  group.add(dormRing);

  return {
    group,
    tunnelSpine,
    livingCynodont,
    livingAmphib,
    dormRing,
    dormRingMat,
    update({ crawlProgress = 1.0, dormancyAura = 0.0, floodSubmerge = 0.0, time = 0.0 }) {
      // 1. Slow 0.26 Hz Aestivation Dormancy Breathing on Curled Thrinaxodon
      const breathRate = floodSubmerge > 0.2 ? 0.0 : 1.0;
      const breath = Math.sin(time * Math.PI * 2.0 * 0.28) * breathRate;
      livingCynodont.torsoMesh.scale.set(1.0 + 0.026 * breath, 1.0 + 0.038 * breath, 1.0 + 0.026 * breath);
      livingCynodont.head.rotation.x = 0.15 + 0.025 * breath;

      // 2. Injured Broomistega 2-Bone IK Crawl down the 24° Burrow Ramp -> Settled Resting Pose beside Thrinaxodon!
      const cp = GLM.clamp(crawlProgress, 0, 1);
      const pathU = GLM.mix(0.14, 0.64, GLM.easeInOutCubic(cp));
      const pos = tunnelSpine.getPoint(pathU);
      const tan = tunnelSpine.getTangent(pathU).normalize();

      // Settle cleanly on left-front of chamber so sleeping Thrinaxodon behind-right stays 100% visible!
      const settleZ = GLM.smoothstep(0.60, 1.0, cp) * 0.16;
      const settleX = GLM.smoothstep(0.60, 1.0, cp) * 0.04;
      // Subtle protective limp bob while crawling, settling still at cp = 1
      const walkActive = 1.0 - GLM.smoothstep(0.86, 1.0, cp);
      const limpBob = Math.abs(Math.sin(cp * Math.PI * 6.0)) * 0.016 * walkActive;

      livingAmphib.root.position.set(pos.x + settleX, pos.y + 0.01 + limpBob, pos.z + settleZ);
      const slopePitch = Math.atan2(-tan.y, tan.x);
      livingAmphib.root.rotation.set(
        0.04 * Math.sin(cp * 18.0) * walkActive,
        Math.PI * 0.5 - 0.18 * GLM.smoothstep(0.7, 1.0, cp),
        0.0
      );
      livingAmphib.bodyMesh.rotation.x = slopePitch * (1.0 - GLM.smoothstep(0.75, 1.0, cp));
      livingAmphib.head.rotation.x = livingAmphib.bodyMesh.rotation.x - 0.08;
      livingAmphib.head.rotation.y = Math.sin(cp * 12.0) * 0.10 * walkActive;
      livingAmphib.updateLegs(cp * 3.2, walkActive);

      // 3. Dormancy Aura
      if (dormancyAura > 0.02) {
        dormRing.visible = true;
        const p = 0.55 + 0.45 * Math.sin(time * 2.4);
        dormRingMat.opacity = dormancyAura * 0.45 * p;
        dormRing.scale.setScalar(0.94 + 0.12 * p);
      } else {
        dormRing.visible = false;
      }
    },
  };
}

function buildLivingAmphRigWrapper(skinAlbedo, skinNormal, isFieldSun = false) {
  return buildLivingAmphibianRig(skinAlbedo, skinNormal, isFieldSun);
}


// =============================================================================
// 5. MONSOON FLASH-FLOOD SURGE WAVE + 160 SILT PARTICLES + PETRIFICATION SEAL
// =============================================================================
export function createFlashFloodAndPetrificationSystem(tunnelSpine, { paletteMode = 'synchrotron_lab' } = {}) {
  const isFieldSun = paletteMode === 'karoo_field_sun';
  const group = new THREE.Group();
  group.visible = false;
  const rng = mulberry32(25099);
  const sandTex = buildKarooSandstoneTextures(9911);

  // A. Rushing Turbulent Mud-Water Surge Tongue descending the burrow tunnel!
  const surgeMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    uniforms: {
      uTime: { value: 0.0 },
      uFrontU: { value: 0.0 },
      uOpacity: { value: 0.88 },
      uFieldMode: { value: isFieldSun ? 1.0 : 0.0 },
    },
    vertexShader: `
      varying vec2 vUv;
      varying vec3 vNormal;
      void main() {
        vUv = uv;
        vNormal = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uTime;
      uniform float uFrontU;
      uniform float uOpacity;
      uniform float uFieldMode;
      varying vec2 vUv;
      varying vec3 vNormal;
      void main() {
        if (vUv.y > uFrontU) discard;
        float frontFoam = smoothstep(uFrontU - 0.22, uFrontU, vUv.y);
        float churn1 = 0.5 + 0.5 * sin(vUv.x * 26.0 + uTime * 18.0 - vUv.y * 22.0);
        float churn2 = 0.5 + 0.5 * cos(vUv.x * 19.0 - uTime * 15.0 + vUv.y * 28.0);
        float turb = churn1 * churn2;

        vec3 mudDeep = vec3(0.28, 0.16, 0.10);
        vec3 siltMid = vec3(0.58, 0.37, 0.23);
        vec3 foamCrest = mix(vec3(0.84, 0.90, 0.92), vec3(0.88, 0.76, 0.62), uFieldMode);

        vec3 col = mix(mudDeep, siltMid, turb);
        col = mix(col, foamCrest, frontFoam * (0.45 + 0.55 * turb));
        float rim = pow(1.0 - abs(vNormal.z), 1.8);
        vec3 rimCol = mix(vec3(0.45, 0.78, 0.88), vec3(0.78, 0.56, 0.38), uFieldMode);
        col += rimCol * rim * 0.32;

        float a = uOpacity * smoothstep(uFrontU + 0.01, uFrontU - 0.05, vUv.y);
        gl_FragColor = vec4(col, clamp(a, 0.0, 0.92));
      }
    `,
  });

  const S_ROWS = 32;
  const S_COLS = 16;
  const surgeRings = [];
  for (let r = 0; r < S_ROWS; r++) {
    const u = r / (S_ROWS - 1);
    const pt = tunnelSpine.getPoint(u);
    const w = 0.38 + 0.28 * GLM.smoothstep(0.45, 0.85, u);
    const h = 0.22 + 0.16 * Math.sin(u * Math.PI);
    const ring = [];
    for (let c = 0; c < S_COLS; c++) {
      const a = (c / S_COLS) * Math.PI * 2;
      ring.push([
        pt.x,
        pt.y + 0.08 + Math.sin(a) * h,
        pt.z + Math.cos(a) * w * 0.78,
      ]);
    }
    surgeRings.push(ring);
  }
  const surgeMesh = new THREE.Mesh(buildLoftGeometry(surgeRings, true, true), surgeMat);
  surgeMesh.renderOrder = 14;
  group.add(surgeMesh);

  // B. Rising Interior Burrow Floodwater & Sedimentary Compaction Volume
  //    Lofted strictly INSIDE tunnelSpine (`radW * 0.88`, `radH * 0.82`) so it NEVER spills outside the curved burrow walls!
  const chamberFillMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    uniforms: {
      tSand: { value: sandTex.albedo },
      uTime: { value: 0.0 },
      uFillLevel: { value: 0.0 },
      uPetrify: { value: 0.0 },
      uFieldMode: { value: isFieldSun ? 1.0 : 0.0 },
    },
    vertexShader: `
      varying vec3 vWorldPos;
      varying vec2 vUv;
      varying vec3 vWorldNormal;
      void main() {
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorldPos = wp.xyz;
        vUv = uv * vec2(3.0, 2.0);
        vWorldNormal = normalize(mat3(modelMatrix) * normal);
        gl_Position = projectionMatrix * viewMatrix * wp;
      }
    `,
    fragmentShader: `
      uniform sampler2D tSand;
      uniform float uTime;
      uniform float uFillLevel;
      uniform float uPetrify;
      uniform float uFieldMode;
      varying vec3 vWorldPos;
      varying vec2 vUv;
      varying vec3 vWorldNormal;
      void main() {
        float yMax = mix(0.22, 1.24, uFillLevel);
        float wave = 0.026 * sin(vWorldPos.x * 8.0 - uTime * 11.0) * (1.0 - uPetrify);
        if (vWorldPos.y > yMax + wave) discard;

        float swirl = 0.5 + 0.5 * sin(vUv.x * 18.0 + uTime * (9.0 * (1.0 - uPetrify))) * cos(vUv.y * 14.0 - uTime * 6.0);
        vec3 deepSilt = mix(vec3(0.18, 0.24, 0.27), vec3(0.26, 0.15, 0.10), uFieldMode);
        vec3 floodWater = mix(deepSilt, vec3(0.56, 0.37, 0.24), swirl);
        float meniscus = smoothstep(yMax - 0.055, yMax + wave, vWorldPos.y) * (1.0 - uPetrify);
        vec3 menCol = mix(vec3(0.68, 0.88, 0.94), vec3(0.86, 0.72, 0.56), uFieldMode);
        floodWater += menCol * meniscus * 0.55;

        // Compacted Karoo Sandstone state (uPetrify -> 1, semi-translucent amber matrix so entombed pair stays visible!)
        vec3 L = normalize(vec3(0.45, 0.80, 0.40));
        float diff = 0.38 + 0.72 * max(abs(dot(vWorldNormal, L)), 0.0);
        vec3 stoneCol = texture2D(tSand, vUv).rgb * diff + vec3(0.28, 0.16, 0.06) * uPetrify;

        vec3 col = mix(floodWater, stoneCol, uPetrify);
        float alpha = mix(0.54, 0.78, uPetrify);
        gl_FragColor = vec4(col, alpha);
      }
    `,
  });

  const F_ROWS = 30;
  const F_COLS = 20;
  const fillRings = [];
  for (let r = 0; r < F_ROWS; r++) {
    const u = GLM.mix(0.28, 0.98, r / (F_ROWS - 1));
    const pt = tunnelSpine.getPoint(u);
    const chamberExpand = GLM.smoothstep(0.45, 0.82, u);
    const endClose = 1.0 - 0.72 * Math.pow(GLM.smoothstep(0.84, 1.0, u), 2.0);
    const radW = (0.48 + 0.34 * chamberExpand) * endClose * 0.86;
    const radH = (0.42 + 0.28 * chamberExpand) * endClose * 0.80;
    const ring = [];
    for (let c = 0; c < F_COLS; c++) {
      const a = (c / F_COLS) * Math.PI * 2;
      ring.push([
        pt.x,
        pt.y + 0.20 + Math.sin(a) * radH * 0.72,
        pt.z - 0.04 + Math.cos(a) * radW * 0.75,
      ]);
    }
    fillRings.push(ring);
  }
  const chamberFillMesh = new THREE.Mesh(buildLoftGeometry(fillRings, true, true), chamberFillMat);
  chamberFillMesh.renderOrder = 15;
  group.add(chamberFillMesh);

  // C. 160 Fine Swirling 3D Silt Grains & Rising Trapped-Air Micro-Bubbles (`InstancedMesh`)
  const PART_COUNT = 160;
  const partGeo = new THREE.SphereGeometry(0.0085, 8, 6);
  const partMat = new THREE.MeshBasicMaterial({
    color: isFieldSun ? '#d9b58c' : '#d8eefa',
    transparent: true,
    opacity: 0.72,
    depthWrite: false,
  });
  const partMesh = new THREE.InstancedMesh(partGeo, partMat, PART_COUNT);
  partMesh.frustumCulled = false;
  partMesh.renderOrder = 18;
  group.add(partMesh);

  const parts = [];
  for (let i = 0; i < PART_COUNT; i++) {
    parts.push({
      ang: rng() * Math.PI * 2,
      rad: 0.08 + rng() * 0.58,
      yOff: rng() * 0.72,
      spd: 1.6 + rng() * 2.8,
      sc: 0.45 + rng() * 1.15,
    });
  }
  const dummy = new THREE.Object3D();

  return {
    group,
    surgeMesh,
    chamberFillMesh,
    partMesh,
    update({ active = false, surgeFront = 0.0, fillLevel = 0.0, petrify = 0.0, time = 0.0 }) {
      group.visible = active;
      if (!active) return;

      surgeMesh.visible = surgeFront > 0.01 && petrify < 0.85;
      surgeMat.uniforms.uTime.value = time;
      surgeMat.uniforms.uFrontU.value = GLM.clamp(surgeFront, 0, 1);
      surgeMat.uniforms.uOpacity.value = 0.86 * (1.0 - petrify * 0.9);

      chamberFillMesh.visible = fillLevel > 0.02;
      chamberFillMat.uniforms.uTime.value = time;
      chamberFillMat.uniforms.uFillLevel.value = GLM.clamp(fillLevel, 0, 1);
      chamberFillMat.uniforms.uPetrify.value = GLM.clamp(petrify, 0, 1);

      const swirlGain = GLM.clamp(fillLevel * 1.4, 0, 1) * (1.0 - petrify);
      partMesh.visible = swirlGain > 0.03;
      if (partMesh.visible) {
        partMat.opacity = 0.76 * swirlGain;
        for (let i = 0; i < PART_COUNT; i++) {
          const p = parts[i];
          const a = p.ang + time * p.spd * (1.0 - 0.8 * petrify);
          const wy = 0.24 + ((p.yOff + time * 0.42 * (i % 2 === 0 ? 1 : -0.5)) % 0.78);
          dummy.position.set(
            0.10 + Math.cos(a) * p.rad,
            Math.min(0.22 + fillLevel * 0.82, Math.max(0.24, wy)),
            -0.02 + Math.sin(a) * p.rad * 0.55
          );
          dummy.scale.setScalar(p.sc * swirlGain);
          dummy.updateMatrix();
          partMesh.setMatrixAt(i, dummy.matrix);
        }
        partMesh.instanceMatrix.needsUpdate = true;
      }
    },
  };
}
