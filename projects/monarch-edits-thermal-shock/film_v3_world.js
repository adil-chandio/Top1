import * as THREE from 'three';
import {
  buildOpticalBreadboardTexture,
  setImaxLightingPreset,
  makeImaxMaterial,
  createTexelSnappedShadowRig,
  createVolumetricSpotlightCone,
  createVolumetricLightBlade,
  createLoopLockedDustMotes,
  createImpactShockwaveRing,
  createBallisticParticleSystem,
  mulberry32,
} from '/tools/monarch-v6-imax-sdk/index.js';

/**
 * THERMAL SHOCK V3 "TABAHI" — Premium 3D World Builder.
 * Glass-hero macro stage: borosilicate tumbler + thermal core shader + cold-front
 * shell + ballistic shard storm + SDK IMAX lighting (`cinema_lab`).
 * Perf-tuned for SwiftShader: NO transmission materials (opacity-fake glass),
 * 48 shards, 60 dust motes, 80 droplets, 50 sparks.
 */

export const FPS = 30;
export const DURATION = 36.0;
export const TOTAL_FRAMES = Math.round(DURATION * FPS); // 1080

// Studio geometry constants (director anchors match these!)
const GLASS_R = 0.52;
const GLASS_H = 1.85;
const GLASS_Y0 = 0.22; // sits on breadboard floor
const WATER_Y0 = 0.42;

function radialGlowTexture(innerHex, outerAlpha0 = 0.0, size = 256) {
  const cv = document.createElement('canvas');
  cv.width = cv.height = size;
  const ctx = cv.getContext('2d');
  const g = ctx.createRadialGradient(size / 2, size / 2, size * 0.04, size / 2, size / 2, size * 0.5);
  g.addColorStop(0, innerHex);
  g.addColorStop(0.45, innerHex.replace(/[\d.]+\)$/, '0.35)'));
  g.addColorStop(1, `rgba(0,0,0,${outerAlpha0})`);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function softDotTexture(hex = 'rgba(255,255,255,0.9)', size = 128) {
  const cv = document.createElement('canvas');
  cv.width = cv.height = size;
  const ctx = cv.getContext('2d');
  const g = ctx.createRadialGradient(size / 2, size / 2, 2, size / 2, size / 2, size * 0.5);
  g.addColorStop(0, hex);
  g.addColorStop(0.4, hex.replace(/[\d.]+\)$/, '0.30)'));
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

// ---------------- THERMAL CORE SHADER (the X-ray hero) ----------------
function buildCoreMaterial() {
  return new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    uniforms: {
      uHeat: { value: 0.0 },
      uXray: { value: 0.0 },
      uTime: { value: 0.0 },
    },
    vertexShader: `
      varying vec2 vUv;
      varying vec3 vPos;
      void main() {
        vUv = uv;
        vPos = position;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uHeat;
      uniform float uXray;
      uniform float uTime;
      varying vec2 vUv;
      varying vec3 vPos;
      float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float noise(vec2 p) {
        vec2 i = floor(p); vec2 f = fract(p);
        vec2 u2 = f * f * (3.0 - 2.0 * f);
        return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u2.x),
                   mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u2.x), u2.y);
      }
      float fbm(vec2 p) {
        float v = 0.0; float a = 0.5;
        for (int k = 0; k < 4; k++) { v += a * noise(p); p *= 2.03; a *= 0.5; }
        return v;
      }
      void main() {
        // cylindrical coordinate: vUv.x wraps the wall, vUv.y climbs it
        float wallY = vUv.y;
        float ang = vUv.x * 6.2831853;
        // slow convection churn
        float churn = fbm(vec2(vUv.x * 9.0 + uTime * 0.22, wallY * 5.0 - uTime * 0.35));
        float plume = fbm(vec2(ang * 2.2 + churn * 2.4, wallY * 3.4 - uTime * 0.55));
        // heat pool: hottest at bottom-center, rises with uHeat
        float pool = smoothstep(0.05, 0.85, wallY * (1.15 - 0.35 * uHeat));
        float hot = clamp(uHeat * (0.55 + 0.65 * plume) * (1.25 - pool * 0.55), 0.0, 1.4);
        // normal mode: magma glow
        vec3 deep   = vec3(0.42, 0.045, 0.008);
        vec3 mid    = vec3(1.00, 0.24, 0.03);
        vec3 bright = vec3(1.00, 0.62, 0.16);
        vec3 magma = mix(deep, mid, clamp(hot * 1.5, 0.0, 1.0));
        magma = mix(magma, bright, clamp(hot * hot * 0.9 - 0.15, 0.0, 1.0));
        float aNormal = (0.10 + 0.62 * clamp(hot, 0.0, 1.0)) * uHeat;
        // X-ray schematic mode: deep translucent red + hot contour line
        vec3 xcol = vec3(0.55, 0.055, 0.02);
        float coreLine = exp(-pow((wallY - 0.52) * 9.0, 2.0)) * (0.65 + 0.35 * plume);
        vec3 xrayCol = xcol * (0.42 + 0.58 * plume) + vec3(1.0, 0.45, 0.12) * coreLine * 0.9;
        float aXray = (0.34 + 0.30 * plume) * coreLine * 0.9 + 0.30;
        vec3 col = mix(magma, xrayCol, uXray);
        float alpha = mix(aNormal, aXray * uHeat * 0.95 + 0.10, uXray);
        alpha *= (0.35 + 0.65 * uHeat);
        gl_FragColor = vec4(col * alpha * 1.5, alpha);
      }
    `,
  });
}

// ---------------- COLD-FRONT SHELL SHADER ----------------
function buildColdMaterial() {
  return new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.FrontSide,
    uniforms: {
      uColdFront: { value: 0.0 },
      uTime: { value: 0.0 },
    },
    vertexShader: `
      varying vec2 vUv;
      void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
    `,
    fragmentShader: `
      uniform float uColdFront;
      uniform float uTime;
      varying vec2 vUv;
      void main() {
        float front = uColdFront * 1.08;
        float d = front - vUv.y;
        float band = exp(-d * d * 42.0) * step(-0.16, d);
        float wet = exp(-max(d, 0.0) * 7.0) * 0.5 * step(0.0, d);
        float shimmer = 0.75 + 0.25 * sin(vUv.x * 40.0 + uTime * 3.0 + d * 14.0);
        vec3 col = vec3(0.30, 0.83, 0.86) * band * shimmer + vec3(0.62, 0.92, 1.0) * wet * 0.5;
        float a = clamp(band * 0.55 + wet * 0.22, 0.0, 0.8);
        gl_FragColor = vec4(col * a, a);
      }
    `,
  });
}

// ---------------- WATER STREAM SHADER ----------------
function buildStreamMaterial() {
  return new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    uniforms: {
      uTime: { value: 0.0 },
      uOpacity: { value: 0.0 },
    },
    vertexShader: `
      varying vec2 vUv;
      void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
    `,
    fragmentShader: `
      uniform float uTime;
      uniform float uOpacity;
      varying vec2 vUv;
      void main() {
        float streak = 0.55 + 0.45 * sin(vUv.x * 34.0 + uTime * 22.0);
        float scroll = fract(vUv.y * 3.0 - uTime * 2.4);
        float body = smoothstep(0.0, 0.18, vUv.x) * (1.0 - smoothstep(0.82, 1.0, vUv.x));
        float a = uOpacity * body * (0.42 + 0.58 * streak * scroll);
        vec3 col = mix(vec3(0.72, 0.92, 1.0), vec3(0.45, 0.78, 0.95), vUv.x);
        gl_FragColor = vec4(col * a, a);
      }
    `,
  });
}

export async function createThermalWorldV3(renderer) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#04060B');
  const rng = mulberry32(90210);

  // SDK IMAX lighting preset (neutral-warm lab + cyan rim separation)
  setImaxLightingPreset('cinema_lab', { fogStart: 26.0, fogRange: 60.0 });

  // ============ FLOOR (optical breadboard, SDK PBR) ============
  const bread = buildOpticalBreadboardTexture(808);
  const floorMat = makeImaxMaterial({
    color: '#2b3238',
    map: bread.albedo,
    normalMap: bread.normal,
    normalScale: 0.5,
    mapRepeat: [5, 5],
    specular: '#9fc4cc',
    specPower: 0.35,
    rimTint: [0.35, 0.55, 0.62],
    rimStrength: 0.16,
  });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(46, 46), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);

  // ============ STUDIO BACKDROP + HALO + HORIZON ============
  const backdrop = new THREE.Mesh(
    new THREE.CylinderGeometry(15.5, 15.5, 9.5, 40, 1, true),
    new THREE.MeshStandardMaterial({ color: '#0a1016', roughness: 1.0, metalness: 0.0, side: THREE.BackSide })
  );
  backdrop.position.y = 4.4;
  scene.add(backdrop);

  const haloMat = new THREE.MeshBasicMaterial({
    map: radialGlowTexture('rgba(255,150,60,0.85)'),
    transparent: true,
    opacity: 0.34,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const halo = new THREE.Mesh(new THREE.PlaneGeometry(16, 16), haloMat);
  halo.position.set(0, 2.4, -7.2);
  scene.add(halo);

  const horizonMat = new THREE.MeshBasicMaterial({
    map: radialGlowTexture('rgba(60,140,170,0.55)'),
    transparent: true,
    opacity: 0.85,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const horizon = new THREE.Mesh(new THREE.PlaneGeometry(30, 4.2), horizonMat);
  horizon.position.set(0, 0.35, -12.4);
  scene.add(horizon);

  // ============ REAL LIGHTS (hybrid: MeshPhysical surfaces + mood) ============
  const keyLight = new THREE.DirectionalLight('#fff3e2', 2.6);
  keyLight.position.set(3.2, 7.4, 3.4);
  scene.add(keyLight);

  const cyanRim = new THREE.DirectionalLight('#7ee0ec', 9.0);
  cyanRim.position.set(-4.6, 3.6, -3.2);
  scene.add(cyanRim);

  const warmFill = new THREE.PointLight('#ffd9ad', 1.6, 18.0, 1.7);
  warmFill.position.set(2.4, 0.9, 2.8);
  scene.add(warmFill);

  const heatLight = new THREE.PointLight('#ff5a1e', 0.0, 6.5, 1.9);
  heatLight.position.set(0, 1.05, 0);
  scene.add(heatLight);

  const coldLight = new THREE.PointLight('#8fd8f2', 0.0, 7.5, 1.8);
  coldLight.position.set(0, 3.4, 0.8);
  scene.add(coldLight);

  const debrisLight = new THREE.PointLight('#ffe2b0', 0.0, 9.0, 1.6);
  debrisLight.position.set(0, 1.5, 0);
  scene.add(debrisLight);

  // ============ HERO GLASS TUMBLER (LatheGeometry, opacity-fake glass) ============
  const glassGroup = new THREE.Group();
  glassGroup.position.set(0, GLASS_Y0, 0);
  scene.add(glassGroup);

  const glassPts = [];
  for (let i = 0; i <= 22; i++) {
    const v = i / 22;
    const y = v * GLASS_H;
    // subtle wall bulge + rounded rim
    const r = GLASS_R * (0.86 + 0.14 * Math.sin(v * Math.PI * 0.86) + 0.05 * v);
    glassPts.push(new THREE.Vector2(Math.max(0.30, r), y));
  }
  glassPts.push(new THREE.Vector2(GLASS_R * 0.86, GLASS_H + 0.02));
  const latheGeo = new THREE.LatheGeometry(glassPts, 64);
  const glassMat = new THREE.MeshPhysicalMaterial({
    color: '#cfeef2',
    transparent: true,
    opacity: 0.30,
    roughness: 0.06,
    metalness: 0.0,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const outerGlass = new THREE.Mesh(latheGeo, glassMat);
  outerGlass.renderOrder = 12;
  glassGroup.add(outerGlass);

  // thermal core (inner cylinder wall with magma shader)
  const coreMat = buildCoreMaterial();
  const core = new THREE.Mesh(
    new THREE.CylinderGeometry(GLASS_R * 0.90, GLASS_R * 0.90, GLASS_H * 0.96, 48, 8, true),
    coreMat
  );
  core.position.y = GLASS_H * 0.5;
  core.renderOrder = 11;
  glassGroup.add(core);

  // cold-front shell (slightly outside the glass)
  const coldMat = buildColdMaterial();
  const coldShell = new THREE.Mesh(
    new THREE.CylinderGeometry(GLASS_R * 1.045, GLASS_R * 1.045, GLASS_H, 48, 10, true),
    coldMat
  );
  coldShell.position.y = GLASS_H * 0.5;
  coldShell.renderOrder = 14;
  glassGroup.add(coldShell);

  // X-ray ghost wireframe
  const ghostEdges = new THREE.LineSegments(
    new THREE.EdgesGeometry(latheGeo, 28),
    new THREE.LineBasicMaterial({ color: '#bfeaf6', transparent: true, opacity: 0.0, depthWrite: false })
  );
  ghostEdges.position.y = 0;
  ghostEdges.renderOrder = 15;
  glassGroup.add(ghostEdges);

  // water surface inside glass
  const waterSurf = new THREE.Mesh(
    new THREE.CircleGeometry(GLASS_R * 0.88, 40),
    new THREE.MeshPhysicalMaterial({
      color: '#2e7fa8',
      transparent: true,
      opacity: 0.0,
      roughness: 0.15,
      metalness: 0.1,
      side: THREE.DoubleSide,
      depthWrite: false,
    })
  );
  waterSurf.rotation.x = -Math.PI / 2;
  waterSurf.position.y = WATER_Y0;
  waterSurf.renderOrder = 13;
  glassGroup.add(waterSurf);

  // pour stream (from above)
  const streamMat = buildStreamMaterial();
  const stream = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.062, 3.1, 14, 20, true), streamMat);
  stream.position.set(0, WATER_Y0 + 1.55, 0);
  stream.renderOrder = 16;
  glassGroup.add(stream);

  // splash crown at first contact
  const splashMat = new THREE.MeshBasicMaterial({
    color: '#bfeaf6',
    transparent: true,
    opacity: 0.0,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const splash = new THREE.Mesh(new THREE.TorusGeometry(0.30, 0.045, 8, 42), splashMat);
  splash.rotation.x = -Math.PI / 2;
  splash.position.y = WATER_Y0 + 0.05;
  splash.visible = false;
  splash.renderOrder = 17;
  glassGroup.add(splash);

  // steam wisps (6 soft sprites)
  const steamTex = softDotTexture('rgba(235,245,250,0.85)');
  const steam = [];
  for (let i = 0; i < 6; i++) {
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({
      map: steamTex,
      transparent: true,
      opacity: 0,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    }));
    sp.renderOrder = 18;
    glassGroup.add(sp);
    steam.push({ sp, phase: rng(), x0: (rng() - 0.5) * 0.5, z0: (rng() - 0.5) * 0.5 });
  }

  // ============ CRACKS (3 staggered tubes, drawRange growth) ============
  const cracks = [];
  const crackSeeds = [
    [[0.02, 1.62, 0.50], [0.30, 1.30, 0.44], [0.47, 0.92, 0.24], [0.40, 0.55, -0.30]],
    [[-0.40, 1.72, 0.30], [-0.52, 1.34, -0.10], [-0.36, 0.98, -0.38], [-0.10, 0.60, -0.50]],
    [[-0.10, 1.80, -0.48], [0.24, 1.52, -0.46], [0.46, 1.10, -0.28], [0.30, 0.72, 0.34]],
  ];
  for (const pts of crackSeeds) {
    const curve = new THREE.CatmullRomCurve3(pts.map((p) => new THREE.Vector3(...p)));
    const geo = new THREE.TubeGeometry(curve, 24, 0.014, 6, false);
    const mat = new THREE.MeshBasicMaterial({
      color: '#FFB454',
      transparent: true,
      opacity: 0.9,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.visible = false;
    mesh.renderOrder = 19;
    glassGroup.add(mesh);
    cracks.push({ mesh, mat, totalVerts: geo.index ? geo.index.count : geo.attributes.position.count });
  }

  // ============ BASE RING (post-shatter survivor) ============
  const baseRing = new THREE.Group();
  const ringBottom = new THREE.Mesh(
    new THREE.CylinderGeometry(GLASS_R * 0.92, GLASS_R * 0.96, 0.10, 48, 1, true),
    new THREE.MeshPhysicalMaterial({ color: '#9fc8d2', transparent: true, opacity: 0.42, roughness: 0.12, side: THREE.DoubleSide, depthWrite: false })
  );
  ringBottom.position.y = 0.06;
  ringBottom.renderOrder = 10;
  baseRing.add(ringBottom);
  const scorch = new THREE.Mesh(
    new THREE.RingGeometry(GLASS_R * 1.02, GLASS_R * 1.45, 48),
    new THREE.MeshBasicMaterial({ color: '#ff6a28', transparent: true, opacity: 0.10, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide })
  );
  scorch.rotation.x = -Math.PI / 2;
  scorch.position.y = 0.012;
  baseRing.add(scorch);
  baseRing.visible = false;
  baseRing.position.y = GLASS_Y0;
  scene.add(baseRing);

  // ============ BOROSILICATE COMPARISON TUMBLER (S9/S10 hero) ============
  const boroGroup = new THREE.Group();
  boroGroup.position.set(0, GLASS_Y0, 0);
  const boroPts = [];
  for (let i = 0; i <= 20; i++) {
    const v = i / 20;
    const y = v * 2.35;
    const r = 0.56 * (0.9 + 0.1 * Math.sin(v * Math.PI));
    boroPts.push(new THREE.Vector2(Math.max(0.34, r), y));
  }
  boroPts.push(new THREE.Vector2(0.48, 2.37));
  const boroGeo = new THREE.LatheGeometry(boroPts, 56);
  const boroGlass = new THREE.Mesh(
    boroGeo,
    new THREE.MeshPhysicalMaterial({
      color: '#bff0ea',
      transparent: true,
      opacity: 0.34,
      roughness: 0.05,
      metalness: 0.0,
      side: THREE.DoubleSide,
      depthWrite: false,
    })
  );
  boroGlass.renderOrder = 12;
  boroGroup.add(boroGlass);
  const boroEdges = new THREE.LineSegments(
    new THREE.EdgesGeometry(boroGeo, 30),
    new THREE.LineBasicMaterial({ color: '#3AD4BE', transparent: true, opacity: 0.0, depthWrite: false })
  );
  boroEdges.renderOrder = 15;
  boroGroup.add(boroEdges);
  const boroWater = new THREE.Mesh(
    new THREE.CircleGeometry(0.5, 40),
    new THREE.MeshPhysicalMaterial({ color: '#2e7fa8', transparent: true, opacity: 0.5, roughness: 0.15, side: THREE.DoubleSide, depthWrite: false })
  );
  boroWater.rotation.x = -Math.PI / 2;
  boroWater.position.y = 0.5;
  boroGroup.add(boroWater);
  boroGroup.visible = false;
  scene.add(boroGroup);

  // ============ SHATTER SYSTEM ============
  // whiteout billboard (camera-attached; director positions it every frame)
  const whiteoutMat = new THREE.MeshBasicMaterial({
    color: '#ffffff',
    transparent: true,
    opacity: 0.0,
    depthTest: false,
    depthWrite: false,
  });
  const whiteout = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 5.6), whiteoutMat);
  whiteout.visible = false;
  whiteout.renderOrder = 40;
  whiteout.frustumCulled = false;
  scene.add(whiteout);

  // 3 floor shockwave rings (staggered) + vertical torus
  const ringSpecs = [
    { y: 0.06, size: 7.5, color: '#ffd187' },
    { y: 0.10, size: 5.6, color: '#ffb454' },
    { y: 0.16, size: 4.2, color: '#ff6a28' },
  ];
  const rings = ringSpecs.map((s) => ({
    ring: createImpactShockwaveRing(),
    y: s.y,
    size: s.size,
    color: s.color,
  }));
  for (const r of rings) scene.add(r.ring.mesh);

  const torusMat = new THREE.MeshBasicMaterial({
    color: '#ffd9a8',
    transparent: true,
    opacity: 0.85,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const torus = new THREE.Mesh(new THREE.TorusGeometry(1.0, 0.05, 8, 60), torusMat);
  torus.rotation.x = Math.PI / 2;
  torus.position.y = 1.15;
  torus.visible = false;
  torus.renderOrder = 28;
  scene.add(torus);

  // 48 extruded glass shards (ballistic + drag + 1 bounce, director-integrated)
  const shardMat = new THREE.MeshPhysicalMaterial({
    color: '#d6f0f4',
    transparent: true,
    opacity: 0.86,
    roughness: 0.07,
    metalness: 0.0,
    side: THREE.DoubleSide,
    depthWrite: true,
  });
  const shards = [];
  for (let i = 0; i < 48; i++) {
    const tri = new THREE.Shape();
    const s0 = 0.06 + rng() * 0.16;
    tri.moveTo(-s0 * 0.7, -s0 * 0.55);
    tri.lineTo(s0, -s0 * 0.25);
    tri.lineTo(-s0 * 0.25, s0 * 0.85);
    tri.closePath();
    const geo = new THREE.ExtrudeGeometry(tri, { depth: 0.016 + rng() * 0.03, bevelEnabled: false });
    const mesh = new THREE.Mesh(geo, shardMat);
    mesh.visible = false;
    scene.add(mesh);
    const ang = rng() * Math.PI * 2;
    const rad = 0.30 + rng() * 0.34;
    shards.push({
      mesh,
      x0: Math.cos(ang) * rad,
      y0: 0.55 + rng() * 1.75,
      vx: Math.cos(ang) * (1.3 + rng() * 2.6),
      vy: 1.0 + rng() * 2.8,
      vz: Math.sin(ang) * (1.3 + rng() * 2.6),
      drag: 0.55 + rng() * 0.85,
      scale: 0.6 + rng() * 1.1,
      ax: (rng() - 0.5) * 11.0,
      ay: (rng() - 0.5) * 11.0,
      az: (rng() - 0.5) * 9.0,
    });
  }

  // SDK particle systems: pour droplets + shatter sparks + loop-locked dust
  const droplets = createBallisticParticleSystem({
    count: 80, radius: 0.02, color: '#bfeaf6', gravity: 9.0, restitution: 0.25, floorY: WATER_Y0,
  });
  scene.add(droplets.mesh);

  const sparks = createBallisticParticleSystem({
    count: 50, radius: 0.032, color: '#ffd99e', gravity: 11.8, restitution: 0.38, floorY: 0.0,
  });
  scene.add(sparks.mesh);

  const dust = createLoopLockedDustMotes({
    count: 60, radius: 0.035, color: '#ffe2ad', loopDurationS: 36.0,
    bounds: { x0: -4.2, xSpan: 8.4, y0: 0.35, ySpan: 3.4, z0: -2.8, zSpan: 6.4 },
    renderOrder: 24,
  });
  scene.add(dust.mesh);

  // ============ VOLUMETRICS (perf-shrunk for SwiftShader) ============
  const volCone = createVolumetricSpotlightCone({
    color: '#cfeaf2', intensity: 0.10, topRadius: 0.55, bottomRadius: 2.4, height: 6.4, renderOrder: 21,
  });
  volCone.position.set(0, 4.9, 0);
  scene.add(volCone);

  const volBlade = createVolumetricLightBlade({
    color: '#ffca7a', intensity: 0.16, length: 6.0, width: 5.2, originX: 1.6, renderOrder: 22,
  });
  volBlade.position.set(0, 0.02, 1.2);
  scene.add(volBlade);

  // ============ SHADOW RIG (baked once; zero-flicker law) ============
  const shadowRig = createTexelSnappedShadowRig(renderer, { mapSize: 1024 });
  shadowRig.updateShadowMap(scene, new THREE.Vector3(0, 1.1, 0), 7.5);

  return {
    scene,
    // hero glass
    glassGroup, outerGlass, glassMat, ghostEdges,
    coreMat, coldMat, coldShell,
    // props
    baseRing, boroGroup, boroEdges, boroWater,
    streamMat, stream, waterSurf, splash, splashMat,
    droplets, sparks, dust, steam,
    cracks, shards,
    // shatter
    whiteout, whiteoutMat, rings, torus, torusMat,
    // lights & backdrop
    keyLight, cyanRim, warmFill, heatLight, coldLight, debrisLight,
    halo, horizon, backdrop, floor,
    shadowRig,
  };
}
