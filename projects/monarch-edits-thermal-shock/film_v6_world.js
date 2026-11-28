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
  createStudioSoftboxEnvMap,
  createBranchingCleavageCracks,
  createThermodynamicsLabEnvironment,
  createUltraSliceableCrystalGlass,
  createUltraCryoPitcherAndIceRig,
  createUltraTetrahedralAtomicRig,
  createUltraShatterAndWaterBurst,
} from '/tools/monarch-v6-imax-sdk/index.js';

/**
 * THERMAL SHOCK V6 ULTRA ("ZACK D. FILMS x CHRISTOPHER NOLAN AUTONOMOUS GOD-MODE")
 * World Builder (`film_v6_world.js`).
 */

export const FPS = 30;
export const DURATION = 40.0;
export const TOTAL_FRAMES = 1200;
export const Y_HEATER_TOP = 0.22;

function makeSoftRadialTex(innerRgba, midRgba, size = 256) {
  const cv = document.createElement('canvas');
  cv.width = cv.height = size;
  const ctx = cv.getContext('2d');
  const g = ctx.createRadialGradient(size / 2, size / 2, size * 0.03, size / 2, size / 2, size * 0.5);
  g.addColorStop(0.0, innerRgba);
  g.addColorStop(0.45, midRgba);
  g.addColorStop(1.0, 'rgba(0,0,0,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function buildInnerMagmaCoreShader() {
  return new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    uniforms: {
      uHeat: { value: 0.38 },
      uColdShell: { value: 0.0 },
      uSliceY: { value: 9.9 },
      uTime: { value: 0.0 },
    },
    vertexShader: `
      varying vec2 vUv;
      varying vec3 vLocal;
      void main() {
        vUv = uv;
        vLocal = position;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uHeat;
      uniform float uColdShell;
      uniform float uSliceY;
      uniform float uTime;
      varying vec2 vUv;
      varying vec3 vLocal;

      float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float noise(vec2 p) {
        vec2 i = floor(p); vec2 f = fract(p);
        vec2 u = f * f * (3.0 - 2.0 * f);
        return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
                   mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
      }

      void main() {
        // Slice open front 116° wedge in exact lockstep with outer crystal glass!
        float ang = atan(vLocal.x, vLocal.z);
        if ((vLocal.y + 1.14) > uSliceY && vLocal.z > 0.0 && abs(ang) < 1.04) {
          discard;
        }
        // Seamless cylindrical coordinates (eliminates any vertical UV wrap line!)
        float cx = sin(ang) * 2.6 + cos(ang) * 1.8;
        float n1 = noise(vec2(cx + uTime * 0.4, vUv.y * 6.0 - uTime * 0.75));
        float n2 = noise(vec2(cx * 1.9 - uTime * 0.3, vUv.y * 11.0 - uTime * 1.1));
        float conv = 0.55 * n1 + 0.45 * n2;

        float rise = smoothstep(1.08, 0.0, vUv.y * (1.28 - 0.44 * uHeat));
        float hotAmt = clamp(uHeat * (0.48 + 0.65 * conv) * (0.55 + 0.68 * rise), 0.0, 1.28);

        vec3 hotCol = mix(vec3(0.62, 0.08, 0.01), vec3(1.0, 0.48, 0.10), clamp(hotAmt * 1.15, 0.0, 1.0));
        float coldFront = 1.0 - uColdShell * 1.05;
        float coldBand = smoothstep(coldFront - 0.14, coldFront + 0.08, vUv.y) * step(0.02, uColdShell);
        vec3 coldCol = vec3(0.18, 0.88, 1.0) * (0.78 + 0.22 * sin(vUv.y * 42.0 - uTime * 9.0));

        vec3 finalCol = mix(hotCol, coldCol, coldBand * 0.64);
        float a = clamp(hotAmt * 0.44 + coldBand * 0.32, 0.0, 0.72);
        gl_FragColor = vec4(finalCol * a * 1.45, a);
      }
    `,
  });
}

export async function createThermalWorldV6(renderer) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#04070d');
  const rng = mulberry32(20261128);

  // 1. Studio Softbox HDR Environment Map (applied selectively to reflective studio actors!)
  const studioEnv = createStudioSoftboxEnvMap(renderer);
  scene.environment = studioEnv;
  setImaxLightingPreset('cinema_lab', { fogStart: 24.0, fogRange: 55.0 });

  // 2. Optical Breadboard Table + Bokeh-Depth 3D Thermodynamics Lab Environment
  const bread = buildOpticalBreadboardTexture(808);
  const floorMat = makeImaxMaterial({
    color: '#222b35',
    map: bread.albedo,
    normalMap: bread.normal,
    normalScale: 0.62,
    mapRepeat: [6, 6],
    specular: '#a8d8e6',
    specPower: 0.44,
    rimTint: [0.32, 0.58, 0.68],
    rimStrength: 0.18,
    polygonOffset: true,
    polygonOffsetFactor: 2,
    polygonOffsetUnits: 2,
  });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(44, 44), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);

  const labEnv = createThermodynamicsLabEnvironment({ yFloor: 0.0 });
  scene.add(labEnv.group);

  // Fast dark cyclorama (`MeshBasicMaterial` + `depthWrite:false` -> zero wasted PBR/Bokeh on sky!)
  const cyc = new THREE.Mesh(
    new THREE.CylinderGeometry(16.0, 16.0, 11.0, 44, 1, true),
    new THREE.MeshBasicMaterial({ color: '#060b13', side: THREE.BackSide, depthWrite: false })
  );
  cyc.position.y = 5.0;
  cyc.renderOrder = -10;
  scene.add(cyc);

  const warmBackdropGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(14, 14),
    new THREE.MeshBasicMaterial({
      map: makeSoftRadialTex('rgba(255, 128, 44, 0.78)', 'rgba(255, 78, 20, 0.20)'),
      transparent: true,
      opacity: 0.34,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  );
  warmBackdropGlow.position.set(0, 2.2, -7.8);
  scene.add(warmBackdropGlow);

  const cyanHorizonGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(26, 5.2),
    new THREE.MeshBasicMaterial({
      map: makeSoftRadialTex('rgba(58, 218, 232, 0.60)', 'rgba(28, 108, 140, 0.18)'),
      transparent: true,
      opacity: 0.74,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  );
  cyanHorizonGlow.position.set(0, 0.65, -11.5);
  scene.add(cyanHorizonGlow);

  // 3. Multi-Mood Cinema Lighting Rig
  scene.add(new THREE.AmbientLight('#b8d6ec', 0.56));

  const keyLight = new THREE.DirectionalLight('#fff5e6', 2.85);
  keyLight.position.set(3.6, 7.8, 4.2);
  scene.add(keyLight);

  const cyanRim = new THREE.DirectionalLight('#66f2ff', 7.6);
  cyanRim.position.set(-4.8, 3.8, -3.0);
  scene.add(cyanRim);

  const warmKicker = new THREE.PointLight('#ffaa58', 2.2, 16.0, 1.6);
  warmKicker.position.set(2.8, 1.6, 2.6);
  scene.add(warmKicker);

  const burnerLight = new THREE.PointLight('#ff5016', 2.5, 7.8, 1.8);
  burnerLight.position.set(0, 0.85, 0);
  scene.add(burnerLight);

  const coldQuenchLight = new THREE.PointLight('#6ceeff', 0.0, 8.8, 1.7);
  coldQuenchLight.position.set(0, 3.1, 0.7);
  scene.add(coldQuenchLight);

  // 4. Titanium Cryo-Pitcher + Helical Stream + 7 Floating 3D Ice Cubes + Halogen Burner
  const cryoRig = createUltraCryoPitcherAndIceRig({ yHeaterTop: Y_HEATER_TOP });
  scene.add(cryoRig.root);

  // 5. Hero Soda-Lime Sliceable Refractive Crystal Glass + Inner Magma Core
  const sodaGlass = createUltraSliceableCrystalGlass({
    baseRadius: 0.50,
    topRadius: 0.585,
    wallThickness: 0.074,
    baseThickness: 0.25,
    height: 2.08,
    tintHex: '#d8f6ff',
    rimHex: '#7ef4ff',
    yFloor: Y_HEATER_TOP,
  });
  scene.add(sodaGlass.group);

  const magmaMat = buildInnerMagmaCoreShader();
  const magmaCore = new THREE.Mesh(
    new THREE.CylinderGeometry(0.50, 0.42, 1.80, 56, 12, true),
    magmaMat
  );
  magmaCore.position.y = 0.25 + 0.90;
  magmaCore.renderOrder = 11;
  sodaGlass.group.add(magmaCore);

  // Surgical Cyan Laser Guillotine Ring + Light Sheet (`S4_LASER_SLICE`)
  const laserRingMat = new THREE.MeshBasicMaterial({
    color: '#6cf9ff',
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const laserRing = new THREE.Mesh(new THREE.RingGeometry(0.38, 0.86, 64), laserRingMat);
  laserRing.rotation.x = -Math.PI / 2;
  laserRing.visible = false;
  laserRing.renderOrder = 24;
  scene.add(laserRing);

  // 6. Multi-Branch Jagged Cleavage Cracks (placed on side walls so they frame the sliced cross-section!)
  const cracksPlugin = createBranchingCleavageCracks({
    radius: 0.568,
    height: 2.05,
    yFloor: Y_HEATER_TOP,
    seed: 4040,
  });
  scene.add(cracksPlugin.group);

  // 7. Zack D. Tetrahedral SiO2 + Recoiling Snapped Bonds + Boron 3.3 Shield Rig
  const atomicRig = createUltraTetrahedralAtomicRig({ yCenter: 1.30 });
  scene.add(atomicRig.root);

  // 8. Post-Shatter Broken Crystal Base + Irregular Translucent Fracture Daggers
  const survivorBase = new THREE.Group();
  survivorBase.position.set(0, Y_HEATER_TOP, 0);
  survivorBase.visible = false;

  const basePuck = new THREE.Mesh(
    new THREE.CylinderGeometry(0.505, 0.495, 0.23, 56),
    new THREE.MeshStandardMaterial({
      color: '#bfeef8',
      emissive: '#0c2838',
      emissiveIntensity: 0.26,
      transparent: true,
      opacity: 0.58,
      roughness: 0.05,
      metalness: 0.12,
      envMapIntensity: 2.4,
      depthWrite: false,
    })
  );
  basePuck.position.y = 0.115;
  basePuck.renderOrder = 10;
  survivorBase.add(basePuck);

  const jagMat = new THREE.MeshStandardMaterial({
    color: '#c4f2fc',
    emissive: '#0d2e40',
    emissiveIntensity: 0.28,
    transparent: true,
    opacity: 0.48,
    roughness: 0.04,
    metalness: 0.14,
    envMapIntensity: 2.4,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  for (let k = 0; k < 12; k++) {
    if (k === 2 || k === 7 || k === 10) continue;
    const a = (k / 12) * Math.PI * 2 + (rng() - 0.5) * 0.28;
    const spH = 0.06 + rng() * 0.18;
    const spW = 0.032 + rng() * 0.046;
    const sp = new THREE.Mesh(new THREE.ConeGeometry(spW, spH, 3), jagMat);
    sp.scale.set(1.0, 1.0, 0.34);
    sp.position.set(Math.cos(a) * 0.475, 0.22 + spH * 0.36, Math.sin(a) * 0.475);
    sp.rotation.set((rng() - 0.5) * 0.2, a + Math.PI * 0.5, (rng() - 0.5) * 0.16);
    sp.renderOrder = 12;
    survivorBase.add(sp);
  }
  scene.add(survivorBase);

  // 9. Hero Borosilicate 3.3 Pyrex Lab Beaker (`S8_BORO_TORTURE_TEST` — receives live ice-water pour on 300°C coil!)
  const boroGlass = createUltraSliceableCrystalGlass({
    baseRadius: 0.54,
    topRadius: 0.565,
    wallThickness: 0.056,
    baseThickness: 0.21,
    height: 2.14,
    tintHex: '#ccfcf0',
    rimHex: '#3ef5d4',
    yFloor: Y_HEATER_TOP,
  });
  // Precision green-cyan lab beaker graduation rings & vertical measurement ticks
  const gradMat = new THREE.MeshBasicMaterial({
    color: '#68fae0',
    transparent: true,
    opacity: 0.65,
    depthWrite: false,
  });
  for (const gy of [0.62, 0.98, 1.34, 1.70]) {
    const gr = new THREE.Mesh(new THREE.TorusGeometry(0.558, 0.0045, 6, 56), gradMat);
    gr.rotation.x = Math.PI / 2;
    gr.position.y = gy;
    gr.renderOrder = 16;
    boroGlass.group.add(gr);
  }
  boroGlass.group.visible = false;
  scene.add(boroGlass.group);

  // 10. 128 Dual-Temp Specular-Glint Crystal Shards + 140 Water Splash Globules + Expanding Wet Puddle
  const shatterBurst = createUltraShatterAndWaterBurst({
    yOrigin: Y_HEATER_TOP,
    glassRadius: 0.55,
    glassHeight: 2.06,
    seed: 90210,
  });
  scene.add(shatterBurst.group);

  const shockRings = [
    { ring: createImpactShockwaveRing(), y: 0.04, size: 8.2, color: '#ffe2a2' },
    { ring: createImpactShockwaveRing(), y: 0.24, size: 6.0, color: '#66f4ff' },
    { ring: createImpactShockwaveRing(), y: 1.18, size: 4.8, color: '#ff6424' },
  ];
  for (const sr of shockRings) scene.add(sr.ring.mesh);

  const blastWaveMat = new THREE.MeshBasicMaterial({
    color: '#9cf8ff',
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const blastWave = new THREE.Mesh(new THREE.RingGeometry(0.86, 0.91, 72), blastWaveMat);
  blastWave.position.set(0, 1.25, 0);
  blastWave.visible = false;
  blastWave.renderOrder = 26;
  scene.add(blastWave);

  // 11. Volumetric Leidenfrost Steam Plumes (12 sprites for both S3 Pour & S7 Hot-Coil Sizzle!)
  const steamTex = makeSoftRadialTex('rgba(235, 248, 255, 0.80)', 'rgba(170, 225, 245, 0.24)', 128);
  const steamSprites = [];
  for (let i = 0; i < 12; i++) {
    const sp = new THREE.Sprite(
      new THREE.SpriteMaterial({
        map: steamTex,
        transparent: true,
        opacity: 0.0,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      })
    );
    sp.renderOrder = 19;
    scene.add(sp);
    steamSprites.push({
      sp,
      phase: i / 12 + rng() * 0.07,
      x0: (rng() - 0.5) * 0.58,
      z0: (rng() - 0.5) * 0.58,
    });
  }

  const sprayDroplets = createBallisticParticleSystem({
    count: 95,
    radius: 0.022,
    color: '#b4f6ff',
    gravity: 9.2,
    restitution: 0.34,
    floorY: 0.03,
  });
  scene.add(sprayDroplets.mesh);

  const blastSparks = createBallisticParticleSystem({
    count: 80,
    radius: 0.028,
    color: '#ffe2a6',
    gravity: 11.2,
    restitution: 0.42,
    floorY: 0.03,
  });
  scene.add(blastSparks.mesh);

  const dust = createLoopLockedDustMotes({
    count: 56,
    radius: 0.024,
    color: '#ffe6b8',
    loopDurationS: DURATION,
    bounds: { x0: -3.2, xSpan: 6.4, y0: 0.45, ySpan: 3.6, z0: -3.4, zSpan: 5.2 },
    renderOrder: 24,
  });
  scene.add(dust.mesh);

  // 12. Volumetrics (hidden during 30 Hz shadow depth pass!)
  const volCone = createVolumetricSpotlightCone({
    color: '#c2f0fa',
    intensity: 0.09,
    topRadius: 0.65,
    bottomRadius: 2.6,
    height: 6.6,
    renderOrder: 21,
  });
  volCone.position.set(0, 5.1, 0);
  scene.add(volCone);

  const volBlade = createVolumetricLightBlade({
    color: '#ffc87a',
    intensity: 0.13,
    length: 6.2,
    width: 5.0,
    originX: 1.8,
    renderOrder: 22,
  });
  volBlade.position.set(0, 0.04, -0.8);
  scene.add(volBlade);

  // 13. 30 Hz Texel-Snapped Shadow Rig (512x512 fast soft contact shadows)
  const shadowRig = createTexelSnappedShadowRig(renderer, { mapSize: 512 });

  return {
    scene,
    floor,
    labEnv,
    warmBackdropGlow,
    cyanHorizonGlow,
    keyLight,
    cyanRim,
    warmKicker,
    burnerLight,
    coldQuenchLight,
    cryoRig,
    sodaGlass,
    magmaMat,
    magmaCore,
    laserRing,
    laserRingMat,
    cracksPlugin,
    atomicRig,
    survivorBase,
    boroGlass,
    shatterBurst,
    shockRings,
    blastWave,
    blastWaveMat,
    steamSprites,
    sprayDroplets,
    blastSparks,
    dust,
    volCone,
    volBlade,
    shadowRig,
  };
}
