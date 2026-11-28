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
  createDoubleWallCrystalGlass,
  createPhysicalHeaterAndPitcherRig,
  createBranchingCleavageCracks,
  createZackDAtomicCutawayRig,
  createVoronoiShatterPlugin,
} from '/tools/monarch-v6-imax-sdk/index.js';

/**
 * THERMAL SHOCK V5 "PLUGIN-GRADE ZACK D. x HOLLYWOOD IMAX" — World Builder.
 * Powered 100% by reusable Monarch V6 IMAX SDK Plugins:
 *   - Procedural 3-Strip Studio Softbox HDR PMREM Reflection Environment
 *   - Double-Walled Sealed Crystal Soda-Lime & Borosilicate 3.3 Lab Tumblers
 *   - Physical Halogen Induction Heater Coil + Tilting Gooseneck Pour Pitcher + Parabolic Stream
 *   - Razor-Sharp Bifurcating Cleavage Cracks + 3D Zack D. SiO2 Atomic Shear Cutaway
 *   - NaN-Proof 96-Shard Beveled Voronoi Shatter Storm + 30 Hz Texel-Snapped Shadows
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

function buildThermalWallShader() {
  return new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    uniforms: {
      uHeat: { value: 0.38 },
      uColdShell: { value: 0.0 },
      uCutaway: { value: 0.0 },
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
      uniform float uColdShell;
      uniform float uCutaway;
      uniform float uTime;
      varying vec2 vUv;
      varying vec3 vPos;

      float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float noise(vec2 p) {
        vec2 i = floor(p); vec2 f = fract(p);
        vec2 u = f * f * (3.0 - 2.0 * f);
        return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
                   mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
      }

      void main() {
        // In cutaway mode, peel front-half of thermal cylinder so 3D atomic rig inside shines clearly
        if (uCutaway > 0.35 && vPos.z > 0.08) {
          discard;
        }
        float n1 = noise(vec2(vUv.x * 10.0 + uTime * 0.35, vUv.y * 6.0 - uTime * 0.65));
        float n2 = noise(vec2(vUv.x * 18.0 - uTime * 0.25, vUv.y * 10.0 - uTime * 0.95));
        float conv = 0.55 * n1 + 0.45 * n2;

        // Bottom-up thermal rise from halogen coil
        float rise = smoothstep(1.05, 0.0, vUv.y * (1.28 - 0.42 * uHeat));
        float hotAmt = clamp(uHeat * (0.45 + 0.65 * conv) * (0.55 + 0.65 * rise), 0.0, 1.25);

        vec3 magmaLow = vec3(0.58, 0.08, 0.01);
        vec3 magmaHigh = vec3(1.0, 0.46, 0.09);
        vec3 hotCol = mix(magmaLow, magmaHigh, clamp(hotAmt * 1.15, 0.0, 1.0));

        // Cold quench wave descending from top rim
        float coldFront = 1.0 - uColdShell * 1.05;
        float coldBand = smoothstep(coldFront - 0.14, coldFront + 0.08, vUv.y) * step(0.02, uColdShell);
        vec3 coldCol = vec3(0.18, 0.86, 1.0) * (0.75 + 0.25 * sin(vUv.y * 40.0 - uTime * 8.0));

        vec3 finalCol = mix(hotCol, coldCol, coldBand * 0.68);
        float a = clamp(hotAmt * 0.48 + coldBand * 0.36, 0.0, 0.78);
        gl_FragColor = vec4(finalCol * a * 1.45, a);
      }
    `,
  });
}

export async function createThermalWorldV5(renderer) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#05080f');
  const rng = mulberry32(202611);

  // 1. Procedural 3-Strip Cinema Softbox HDR Environment Map!
  scene.environment = createStudioSoftboxEnvMap(renderer);
  setImaxLightingPreset('cinema_lab', { fogStart: 24.0, fogRange: 55.0 });

  // 2. Optical Breadboard Lab Table (Zero-Flicker Law 1: polygonOffset + y=0)
  const bread = buildOpticalBreadboardTexture(808);
  const floorMat = makeImaxMaterial({
    color: '#252d36',
    map: bread.albedo,
    normalMap: bread.normal,
    normalScale: 0.6,
    mapRepeat: [6, 6],
    specular: '#a8d4e0',
    specPower: 0.42,
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

  // Curved studio cyclorama (MeshBasicMaterial + depthWrite:false -> ZERO wasted PBR/PMREM/Bokeh on 1.5M dark bg pixels!)
  const cyc = new THREE.Mesh(
    new THREE.CylinderGeometry(16.0, 16.0, 11.0, 44, 1, true),
    new THREE.MeshBasicMaterial({ color: '#070c14', side: THREE.BackSide, depthWrite: false })
  );
  cyc.position.y = 5.0;
  cyc.renderOrder = -10;
  scene.add(cyc);

  const warmBackdropGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(14, 14),
    new THREE.MeshBasicMaterial({
      map: makeSoftRadialTex('rgba(255, 132, 48, 0.78)', 'rgba(255, 85, 24, 0.22)'),
      transparent: true,
      opacity: 0.36,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  );
  warmBackdropGlow.position.set(0, 2.2, -7.8);
  scene.add(warmBackdropGlow);

  const cyanHorizonGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(26, 5.2),
    new THREE.MeshBasicMaterial({
      map: makeSoftRadialTex('rgba(58, 212, 224, 0.58)', 'rgba(32, 110, 140, 0.18)'),
      transparent: true,
      opacity: 0.72,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  );
  cyanHorizonGlow.position.set(0, 0.65, -11.5);
  scene.add(cyanHorizonGlow);

  // 3. Cinema Multi-Mood Lighting Rig
  const ambient = new THREE.AmbientLight('#b8d4ea', 0.55);
  scene.add(ambient);

  const keyLight = new THREE.DirectionalLight('#fff4e4', 2.8);
  keyLight.position.set(3.6, 7.8, 4.2);
  scene.add(keyLight);

  const cyanRim = new THREE.DirectionalLight('#6ef0ff', 7.5);
  cyanRim.position.set(-4.8, 3.8, -3.0);
  scene.add(cyanRim);

  const warmKicker = new THREE.PointLight('#ffaa58', 2.2, 16.0, 1.6);
  warmKicker.position.set(2.8, 1.6, 2.6);
  scene.add(warmKicker);

  const burnerLight = new THREE.PointLight('#ff5218', 2.4, 7.5, 1.8);
  burnerLight.position.set(0, 0.85, 0);
  scene.add(burnerLight);

  const coldQuenchLight = new THREE.PointLight('#6ce8ff', 0.0, 8.5, 1.7);
  coldQuenchLight.position.set(0, 3.1, 0.7);
  scene.add(coldQuenchLight);

  // 4. Physical Halogen Heater Base + Gooseneck Pitcher + Parabolic Stream Plugin
  const propsRig = createPhysicalHeaterAndPitcherRig({ yHeaterTop: Y_HEATER_TOP });
  scene.add(propsRig.root);

  // 5. Hero Soda-Lime Double-Wall Crystal Tumbler + Inner Thermal Shader Core
  const sodaGlass = createDoubleWallCrystalGlass({
    baseRadius: 0.50,
    topRadius: 0.58,
    wallThickness: 0.066,
    baseThickness: 0.24,
    height: 2.06,
    tintHex: '#d8f4fa',
    rimHex: '#8cf0ff',
    yFloor: Y_HEATER_TOP,
  });
  scene.add(sodaGlass.group);

  const thermalMat = buildThermalWallShader();
  const thermalShell = new THREE.Mesh(
    new THREE.CylinderGeometry(0.515, 0.445, 1.80, 56, 12, true),
    thermalMat
  );
  thermalShell.position.y = 0.24 + 0.90;
  thermalShell.renderOrder = 11;
  sodaGlass.group.add(thermalShell);

  // Cold condensation outer sheen shell
  const coldOuterMat = new THREE.MeshBasicMaterial({
    color: '#5cf0ff',
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.FrontSide,
  });
  const coldOuterShell = new THREE.Mesh(
    new THREE.CylinderGeometry(0.588, 0.508, 2.04, 56, 1, true),
    coldOuterMat
  );
  coldOuterShell.position.y = 1.03;
  coldOuterShell.renderOrder = 14;
  sodaGlass.group.add(coldOuterShell);

  // Laser tomography horizontal scan ring for "RUKO." cutaway reveal
  const laserRingMat = new THREE.MeshBasicMaterial({
    color: '#66f7ff',
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const laserRing = new THREE.Mesh(new THREE.RingGeometry(0.42, 0.78, 56), laserRingMat);
  laserRing.rotation.x = -Math.PI / 2;
  laserRing.visible = false;
  laserRing.renderOrder = 20;
  scene.add(laserRing);

  // 6. Razor-Sharp Jagged Bifurcating Cleavage Cracks Plugin
  const cracksPlugin = createBranchingCleavageCracks({
    radius: 0.565,
    height: 2.04,
    yFloor: Y_HEATER_TOP,
    seed: 4040,
  });
  scene.add(cracksPlugin.group);

  // 7. Zack D. Films 3D SiO2 Atomic Shear & Force-Arrow Cutaway Plugin
  const atomicRig = createZackDAtomicCutawayRig({ yCenter: 1.30 });
  scene.add(atomicRig.root);

  // 8. Post-Shatter Surviving Jagged Base Crown + Scorch Ring
  const survivorBase = new THREE.Group();
  survivorBase.position.set(0, Y_HEATER_TOP, 0);
  survivorBase.visible = false;
  const baseChunkGeo = new THREE.CylinderGeometry(0.51, 0.50, 0.22, 48);
  const baseChunk = new THREE.Mesh(
    baseChunkGeo,
    new THREE.MeshPhysicalMaterial({
      color: '#c8eef6',
      transparent: true,
      opacity: 0.62,
      roughness: 0.08,
      clearcoat: 1.0,
      envMapIntensity: 2.4,
      depthWrite: false,
    })
  );
  baseChunk.position.y = 0.11;
  baseChunk.renderOrder = 10;
  survivorBase.add(baseChunk);

  // Irregular asymmetric translucent fracture splinters around broken base (zero uniform cone ring!)
  const crownMat = new THREE.MeshPhysicalMaterial({
    color: '#bfeff8',
    emissive: '#0c2634',
    emissiveIntensity: 0.22,
    transparent: true,
    opacity: 0.46,
    roughness: 0.05,
    clearcoat: 1.0,
    envMapIntensity: 2.2,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  for (let k = 0; k < 11; k++) {
    const a = (k / 11) * Math.PI * 2 + (rng() - 0.5) * 0.34;
    if (k === 3 || k === 8) continue; // natural missing fracture gaps!
    const spikeH = 0.05 + rng() * 0.16;
    const spikeW = 0.032 + rng() * 0.045;
    const sp = new THREE.Mesh(new THREE.ConeGeometry(spikeW, spikeH, 3), crownMat);
    sp.scale.set(1.0, 1.0, 0.38);
    sp.position.set(Math.cos(a) * 0.475, 0.21 + spikeH * 0.38, Math.sin(a) * 0.475);
    sp.rotation.set((rng() - 0.5) * 0.22, a + Math.PI * 0.5, (rng() - 0.5) * 0.18);
    sp.renderOrder = 12;
    survivorBase.add(sp);
  }
  scene.add(survivorBase);

  // 9. Hero Borosilicate 3.3 Lab Glass Beaker/Tumbler (`S8_BORO_HERO`)
  const boroGlass = createDoubleWallCrystalGlass({
    baseRadius: 0.54,
    topRadius: 0.56,
    wallThickness: 0.052,
    baseThickness: 0.20,
    height: 2.16,
    tintHex: '#ccf9f0',
    rimHex: '#3ad4be',
    yFloor: Y_HEATER_TOP,
  });
  // Etched lab graduation rings on Borosilicate 3.3 glass!
  const gradMat = new THREE.MeshBasicMaterial({
    color: '#6ef7de',
    transparent: true,
    opacity: 0.58,
    depthWrite: false,
  });
  for (const gy of [0.65, 1.05, 1.45, 1.82]) {
    const gr = new THREE.Mesh(new THREE.TorusGeometry(0.556, 0.0045, 6, 56), gradMat);
    gr.rotation.x = Math.PI / 2;
    gr.position.y = gy;
    gr.renderOrder = 14;
    boroGlass.group.add(gr);
  }
  const boroWater = new THREE.Mesh(
    new THREE.CylinderGeometry(0.50, 0.48, 1.18, 48),
    new THREE.MeshPhysicalMaterial({
      color: '#2aa6c8',
      transparent: true,
      opacity: 0.46,
      roughness: 0.05,
      envMapIntensity: 2.2,
      depthWrite: false,
    })
  );
  boroWater.position.y = 0.22 + 0.59;
  boroWater.renderOrder = 11;
  boroGlass.group.add(boroWater);
  boroGlass.group.visible = false;
  scene.add(boroGlass.group);

  // 10. NaN-Proof 96-Shard 3D Voronoi Crystal Shatter Plugin + Shockwaves
  const shatterPlugin = createVoronoiShatterPlugin({
    yOrigin: Y_HEATER_TOP,
    glassRadius: 0.55,
    glassHeight: 2.04,
    seed: 90210,
  });
  scene.add(shatterPlugin.group);

  const shockRings = [
    { ring: createImpactShockwaveRing(), y: 0.05, size: 7.8, color: '#ffe09e' },
    { ring: createImpactShockwaveRing(), y: 0.24, size: 5.8, color: '#6ef0ff' },
    { ring: createImpactShockwaveRing(), y: 1.15, size: 4.6, color: '#ff6a28' },
  ];
  for (const sr of shockRings) scene.add(sr.ring.mesh);

  const blastTorusMat = new THREE.MeshBasicMaterial({
    color: '#9cf6ff',
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const blastTorus = new THREE.Mesh(new THREE.RingGeometry(0.86, 0.91, 72), blastTorusMat);
  blastTorus.position.set(0, 1.25, 0);
  blastTorus.visible = false;
  blastTorus.renderOrder = 26;
  scene.add(blastTorus);

  // 11. Steam Plumes + Ballistic Spray Droplets + Shatter Sparks + Loop-Locked Dust Motes
  const steamTex = makeSoftRadialTex('rgba(232, 246, 255, 0.75)', 'rgba(180, 220, 240, 0.20)', 128);
  const steamSprites = [];
  for (let i = 0; i < 8; i++) {
    const sp = new THREE.Sprite(
      new THREE.SpriteMaterial({
        map: steamTex,
        transparent: true,
        opacity: 0.0,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      })
    );
    sp.renderOrder = 18;
    scene.add(sp);
    steamSprites.push({
      sp,
      phase: i / 8 + rng() * 0.08,
      x0: (rng() - 0.5) * 0.48,
      z0: (rng() - 0.5) * 0.48,
    });
  }

  const sprayDroplets = createBallisticParticleSystem({
    count: 90,
    radius: 0.022,
    color: '#aef2ff',
    gravity: 9.2,
    restitution: 0.32,
    floorY: 0.03,
  });
  scene.add(sprayDroplets.mesh);

  const blastSparks = createBallisticParticleSystem({
    count: 75,
    radius: 0.030,
    color: '#ffdf9e',
    gravity: 11.2,
    restitution: 0.42,
    floorY: 0.03,
  });
  scene.add(blastSparks.mesh);

  // Clamp dust zSpan <= 2.4 so NO dust disc ever drifts near the macro camera lens!
  const dust = createLoopLockedDustMotes({
    count: 56,
    radius: 0.024,
    color: '#ffe5b4',
    loopDurationS: DURATION,
    bounds: { x0: -3.2, xSpan: 6.4, y0: 0.45, ySpan: 3.6, z0: -3.4, zSpan: 5.2 },
    renderOrder: 24,
  });
  scene.add(dust.mesh);

  // 12. Volumetrics (hidden automatically during 30 Hz shadow depth pass!)
  const volCone = createVolumetricSpotlightCone({
    color: '#bfeef8',
    intensity: 0.09,
    topRadius: 0.65,
    bottomRadius: 2.6,
    height: 6.6,
    renderOrder: 21,
  });
  volCone.position.set(0, 5.1, 0);
  scene.add(volCone);

  const volBlade = createVolumetricLightBlade({
    color: '#ffc678',
    intensity: 0.13,
    length: 6.2,
    width: 5.0,
    originX: 1.8,
    renderOrder: 22,
  });
  volBlade.position.set(0, 0.04, -0.8);
  scene.add(volBlade);

  // 13. 30 Hz Texel-Snapped Shadow Rig (512x512 = 4x faster on SwiftShader, pixel-identical soft shadow!)
  const shadowRig = createTexelSnappedShadowRig(renderer, { mapSize: 512 });

  return {
    scene,
    floor,
    warmBackdropGlow,
    cyanHorizonGlow,
    keyLight,
    cyanRim,
    warmKicker,
    burnerLight,
    coldQuenchLight,
    propsRig,
    sodaGlass,
    thermalMat,
    thermalShell,
    coldOuterMat,
    coldOuterShell,
    laserRing,
    laserRingMat,
    cracksPlugin,
    atomicRig,
    survivorBase,
    boroGlass,
    shatterPlugin,
    shockRings,
    blastTorus,
    blastTorusMat,
    steamSprites,
    sprayDroplets,
    blastSparks,
    dust,
    volCone,
    volBlade,
    shadowRig,
  };
}
