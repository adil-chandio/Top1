import * as THREE from 'three';
import {
  makeImaxMaterial,
  setImaxLightingPreset,
  createTexelSnappedShadowRig,
  buildOpticalBreadboardTexture,
  createImaxOpticalPass,
  createVolumetricLightBlade,
  createLoopLockedDustMotes,
  createImpactShockwaveRing,
  createBallisticParticleSystem,
  GLM,
  createGroundContactAO,
  createCinemaCameraRig,
  loadVerifiedCinemaFonts,
  createGpuHudCompositor,
  drawImaxShortHud,
} from '/tools/monarch-v6-imax-sdk/index.js';

const W = 1080;
const H = 1920;
const FPS = 30;
const DURATION = 23.36;
const TOTAL_FRAMES = Math.round(DURATION * FPS); // 701

const CAPTIONS = [
  [0.0, 2.8, 'GARAM SHEESHA', 'KYUN TOOT JATA HAI?'],
  [2.8, 6.2, 'THANDA PAANI', 'BAHAR SE SUKADTA HAI'],
  [6.2, 9.8, 'ANDAR KA HISSA', 'ABHI BHI PHAILA HAI'],
  [9.8, 13.5, 'THERMAL SHOCK', 'ZABARDAST KHICHAO!'],
  [13.5, 17.5, 'EK SECOND MEIN', 'ANDAR SE CRACK!'],
  [17.5, 23.36, 'AGLI BAAR', 'DO BAAR SOCHNA!'],
];

function buildGlassTumblerGeometry(outerR, innerR, height, radialSegs = 64) {
  const pts = [
    new THREE.Vector2(0.001, 0.0),
    new THREE.Vector2(outerR * 0.92, 0.0),
    new THREE.Vector2(outerR, 0.12),
    new THREE.Vector2(outerR * 1.04, height),
    new THREE.Vector2((outerR * 1.04 + innerR) * 0.5, height + 0.05),
    new THREE.Vector2(innerR, height),
    new THREE.Vector2(innerR * 0.94, 0.28),
    new THREE.Vector2(0.001, 0.26),
  ];
  return new THREE.LatheGeometry(pts, radialSegs);
}

async function init() {
  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    preserveDrawingBuffer: true,
    powerPreference: 'high-performance',
  });
  renderer.setSize(W, H, false);
  renderer.setPixelRatio(1);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.18;
  document.body.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#090D14');
  scene.fog = new THREE.FogExp2('#090D14', 0.042);

  const camera = new THREE.PerspectiveCamera(38, W / H, 0.2, 60);
  const rig = createCinemaCameraRig(camera, { aspect: W / H });

  setImaxLightingPreset(scene, 'obsidian_lab');
  scene.add(new THREE.AmbientLight('#b8d4ff', 1.05));

  const keyLight = new THREE.DirectionalLight('#fff2dc', 3.0);
  keyLight.position.set(4.5, 7.5, 5.0);
  scene.add(keyLight);

  const cyanRim = new THREE.PointLight('#3AD4BE', 5.0, 20);
  cyanRim.position.set(-3.2, 3.2, -2.2);
  scene.add(cyanRim);

  const heatLight = new THREE.PointLight('#FF4A1C', 0.0, 14);
  heatLight.position.set(0, 1.4, 0.2);
  scene.add(heatLight);

  const shadowRig = createTexelSnappedShadowRig(renderer, { mapSize: 1024 });

  // Optical lab table
  const tableTex = buildOpticalBreadboardTexture(512);
  const tableMat = makeImaxMaterial({
    color: '#121A26',
    roughness: 0.42,
    metalness: 0.68,
    map: tableTex,
    polygonOffset: true,
    polygonOffsetFactor: 2,
    polygonOffsetUnits: 2,
  });
  const table = new THREE.Mesh(new THREE.BoxGeometry(16, 0.4, 12), tableMat);
  table.position.set(0, -0.2, 0);
  table.receiveShadow = true;
  scene.add(table);

  // Volumetric light blade + dust motes
  const blade = createVolumetricLightBlade({ color: '#3AD4BE', opacity: 0.16, width: 6.5, height: 11 });
  blade.position.set(0, 4.0, -3.6);
  blade.renderOrder = 22;
  scene.add(blade);

  const dust = createLoopLockedDustMotes({ count: 90, radius: 5.5, height: 6.0, color: '#8BE9FD' });
  dust.renderOrder = 23;
  scene.add(dust);

  // Contact AO under glass
  const ao = createGroundContactAO(2.2);
  ao.position.set(0, 0.01, 0);
  ao.renderOrder = 2;
  scene.add(ao);

  // Hero Glass Tumbler (outer + inner thermal cutaway)
  const glassGroup = new THREE.Group();
  scene.add(glassGroup);

  const outerGeo = buildGlassTumblerGeometry(0.95, 0.80, 2.4, 64);
  const outerMat = new THREE.MeshPhysicalMaterial({
    color: '#d8f3ff',
    roughness: 0.07,
    metalness: 0.05,
    transmission: 0.88,
    thickness: 0.45,
    ior: 1.52,
    clearcoat: 1.0,
    clearcoatRoughness: 0.05,
    transparent: true,
    opacity: 0.72,
    depthWrite: false,
  });
  const outerGlass = new THREE.Mesh(outerGeo, outerMat);
  outerGlass.renderOrder = 10;
  glassGroup.add(outerGlass);

  // Inner thermal core (glows molten amber-red as heat builds)
  const innerCoreGeo = new THREE.CylinderGeometry(0.76, 0.70, 1.95, 48, 1, true);
  const innerCoreMat = new THREE.MeshStandardMaterial({
    color: '#FF4A1C',
    emissive: '#FF3300',
    emissiveIntensity: 0.0,
    roughness: 0.25,
    metalness: 0.1,
    transparent: true,
    opacity: 0.0,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const innerCore = new THREE.Mesh(innerCoreGeo, innerCoreMat);
  innerCore.position.y = 1.25;
  innerCore.renderOrder = 6;
  glassGroup.add(innerCore);

  // Cold water pour stream
  const streamGeo = new THREE.CylinderGeometry(0.08, 0.12, 3.8, 24);
  const streamMat = new THREE.MeshPhysicalMaterial({
    color: '#4CE8FF',
    emissive: '#1488AA',
    emissiveIntensity: 0.45,
    roughness: 0.05,
    transparent: true,
    opacity: 0.0,
    depthWrite: false,
  });
  const waterStream = new THREE.Mesh(streamGeo, streamMat);
  waterStream.position.set(0, 3.6, 0);
  waterStream.renderOrder = 12;
  scene.add(waterStream);

  // Shear-stress shockwave rings
  const shockRing1 = createImpactShockwaveRing({ color: '#FF4A1C', maxRadius: 2.8 });
  const shockMesh1 = shockRing1.mesh || shockRing1;
  shockMesh1.position.set(0, 1.2, 0);
  shockMesh1.renderOrder = 24;
  scene.add(shockMesh1);

  const shockRing2 = createImpactShockwaveRing({ color: '#3AD4BE', maxRadius: 3.4 });
  const shockMesh2 = shockRing2.mesh || shockRing2;
  shockMesh2.position.set(0, 1.2, 0);
  shockMesh2.renderOrder = 25;
  scene.add(shockMesh2);

  // 3D Glass Shards for shatter explosion
  const shards = [];
  const shardMat = new THREE.MeshPhysicalMaterial({
    color: '#e6f9ff',
    emissive: '#3AD4BE',
    emissiveIntensity: 0.25,
    roughness: 0.08,
    metalness: 0.15,
    transparent: true,
    opacity: 0.9,
    side: THREE.DoubleSide,
  });
  for (let i = 0; i < 28; i++) {
    const angle = (i / 28) * Math.PI * 2;
    const y0 = 0.4 + ((i * 7) % 19) * 0.1;
    const shardGeo = new THREE.ConeGeometry(0.14 + (i % 3) * 0.06, 0.38 + (i % 4) * 0.08, 4);
    const mesh = new THREE.Mesh(shardGeo, shardMat);
    mesh.visible = false;
    mesh.renderOrder = 14;
    scene.add(mesh);
    shards.push({
      mesh,
      x0: Math.cos(angle) * 0.85,
      y0,
      z0: Math.sin(angle) * 0.85,
      vx: Math.cos(angle) * (2.6 + (i % 5) * 0.7),
      vy: 1.4 + (i % 4) * 0.9,
      vz: Math.sin(angle) * (2.6 + (i % 5) * 0.7),
      rx: (i % 3 + 1) * 3.2,
      ry: (i % 4 + 1) * 2.5,
    });
  }

  // Ballistic spark/droplet particles
  const particles = createBallisticParticleSystem({ count: 140, color: '#6BF0FF', size: 0.065 });
  particles.renderOrder = 26;
  scene.add(particles);

  // Post-FX & HUD
  const opticalPass = createImaxOpticalPass(renderer, scene, camera, {
    bloomStrength: 0.65,
    bloomRadius: 0.45,
    bloomThreshold: 0.72,
  });

  await loadVerifiedCinemaFonts();
  const hud = createGpuHudCompositor(renderer, W, H);

  window.__duration = DURATION;
  window.__totalFrames = TOTAL_FRAMES;
  window.__ready = true;
  window.__SHORT_V6_READY__ = true;

  window.evaluateFrame = (frameIdx) => {
    const t = Math.max(0, Math.min(DURATION, frameIdx / FPS));
    const loopT = t / DURATION;

    // 1. Thermal & Shatter Choreography
    const pourStart = 2.5;
    const shatterT = 13.8;
    const isShattered = t >= shatterT;

    // Inner heat glow builds from 0 to 13.8s
    const heatProgress = GLM.clamp((t - 0.5) / 10.0, 0, 1);
    innerCoreMat.opacity = isShattered ? 0.0 : heatProgress * 0.62;
    innerCoreMat.emissiveIntensity = isShattered ? 0.0 : heatProgress * 2.4;
    heatLight.intensity = isShattered ? Math.max(0, 4.5 - (t - shatterT) * 2.5) : heatProgress * 4.5;

    // Cold water pour stream (2.5s -> 8.5s)
    if (t >= pourStart && t < 8.5) {
      streamMat.opacity = 0.75;
      waterStream.position.y = 3.5 - Math.sin(t * 12) * 0.04;
    } else {
      streamMat.opacity = 0.0;
    }

    // Outer glass visibility & stress vibration
    outerGlass.visible = !isShattered;
    if (!isShattered && t > 9.5) {
      const vib = (t - 9.5) / (shatterT - 9.5);
      glassGroup.position.x = Math.sin(t * 42) * 0.025 * vib;
      glassGroup.position.z = Math.cos(t * 37) * 0.025 * vib;
    } else {
      glassGroup.position.set(0, 0, 0);
    }

    // Shockwave rings
    if (t >= 10.0 && t < 13.8) {
      if (shockRing1.update) shockRing1.update((t - 10.0) * 0.65);
      else { const s = 1 + (t - 10.0) * 0.8; shockMesh1.scale.set(s, s, s); }
      shockMesh1.visible = true;
    } else {
      shockMesh1.visible = false;
    }
    if (t >= shatterT) {
      const dt = t - shatterT;
      // Bullet-time slow-mo for first 2.5s after shatter
      const simDt = dt < 2.5 ? dt * 0.28 : 2.5 * 0.28 + (dt - 2.5) * 1.1;
      if (shockRing2.update) shockRing2.update(dt * 0.85);
      else { const s = 1 + dt * 1.5; shockMesh2.scale.set(s, s, s); }
      shockMesh2.visible = dt < 2.0;

      for (const s of shards) {
        s.mesh.visible = true;
        s.mesh.position.set(
          s.x0 + s.vx * simDt,
          Math.max(0.08, s.y0 + s.vy * simDt - 4.9 * simDt * simDt),
          s.z0 + s.vz * simDt
        );
        s.mesh.rotation.set(s.rx * simDt, s.ry * simDt, 0);
      }
      if (particles.update) particles.update(simDt);
      particles.visible = true;
    } else {
      shockMesh2.visible = false;
      for (const s of shards) s.mesh.visible = false;
      particles.visible = false;
    }

    // Dust motes
    dust.update(loopT);

    // 2. Cinema Camera Rig (9:16 portrait framing + bullet-time orbit + seamless loop)
    let camPos, camTarget;
    if (t < 3.0) {
      const p = GLM.easeOutQuint(t / 3.0);
      camPos = [THREE.MathUtils.lerp(0, 1.4, p), THREE.MathUtils.lerp(2.2, 1.8, p), THREE.MathUtils.lerp(6.8, 5.2, p)];
      camTarget = [0, 1.25, 0];
    } else if (t < 9.5) {
      const p = (t - 3.0) / 6.5;
      camPos = [THREE.MathUtils.lerp(1.4, -1.8, p), THREE.MathUtils.lerp(1.8, 1.5, p), THREE.MathUtils.lerp(5.2, 4.6, p)];
      camTarget = [0, 1.2, 0];
    } else if (t < shatterT) {
      const p = (t - 9.5) / (shatterT - 9.5);
      camPos = [THREE.MathUtils.lerp(-1.8, 0.2, p), THREE.MathUtils.lerp(1.5, 1.35, p), THREE.MathUtils.lerp(4.6, 3.9, p)];
      camTarget = [0, 1.2, 0];
    } else if (t < 21.5) {
      const p = (t - shatterT) / (21.5 - shatterT);
      const angle = p * Math.PI * 0.85;
      camPos = [Math.sin(angle) * 4.8, 1.6 + Math.sin(p * Math.PI) * 0.6, Math.cos(angle) * 4.8];
      camTarget = [0, 1.15, 0];
    } else {
      const p = GLM.easeOutQuint((t - 21.5) / (DURATION - 21.5));
      camPos = [THREE.MathUtils.lerp(2.1, 0, p), THREE.MathUtils.lerp(1.6, 2.2, p), THREE.MathUtils.lerp(4.3, 6.8, p)];
      camTarget = [0, 1.25, 0];
    }

    camera.position.set(...camPos);
    camera.lookAt(...camTarget);

    shadowRig.updateShadowMap(scene, new THREE.Vector3(0, 1.2, 0), 4.5);
    renderer.setRenderTarget(null);
    renderer.render(scene, camera);

    // 3. Kinetic Roman Urdu HUD Captions
    let line1 = '';
    let line2 = '';
    for (const [s, e, l1, l2] of CAPTIONS) {
      if (t >= s && t < e) {
        line1 = l1;
        line2 = l2;
        break;
      }
    }
    hud.ctx.clearRect(0, 0, W, H);
    if (line1) {
      drawImaxShortHud(hud.ctx, W, H, {
        line1,
        line2,
        accentColor: t >= shatterT ? '#FF4A1C' : '#3AD4BE',
        progress: loopT,
      });
    }
    // hud.composite();
  };

  window.renderFrame = window.evaluateFrame;
  window.renderFramePNG = (frameIdx) => {
    window.evaluateFrame(frameIdx);
  };
  window.renderCoverPNG = () => window.renderFramePNG(Math.round(14.5 * FPS));
}

init();
