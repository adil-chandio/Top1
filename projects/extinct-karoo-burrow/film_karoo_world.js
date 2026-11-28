import * as THREE from 'three';
import {
  buildOpticalBreadboardTexture,
  setImaxLightingPreset,
  makeImaxMaterial,
  createTexelSnappedShadowRig,
  createVolumetricSpotlightCone,
  createVolumetricLightBlade,
  createLoopLockedDustMotes,
  createLaserTomographyScanner,
  createStudioSoftboxEnvMap,
  createSynchrotronLabStage,
  createKarooRockAndDualFossilRig,
  createTriassicBurrowAndLivingPairRig,
  createFlashFloodAndPetrificationSystem,
} from '/tools/monarch-v6-imax-sdk/index.js';

/**
 * EXTINCT LIFE V6 ULTRA — "This Rock Holds Two Animals" (`BP/1/5558`, ~250 Ma Karoo Burrow)
 * Dual-Set World Builder (`film_karoo_world.js`):
 *   - Set A (`labRoot`): ESRF Synchrotron X-Ray Tomography Lab + Dual-Skeleton Karoo Sandstone Cast
 *   - Set B (`triassicRoot`): 250-Million-Year-Old Early Triassic Underground Burrow Cutaway + Flash Flood
 */

export const FPS = 30;
export const DURATION = 36.0;
export const TOTAL_FRAMES = 1080;

function makeSoftGlowTex(innerRgba, midRgba, size = 256) {
  const cv = document.createElement('canvas');
  cv.width = cv.height = size;
  const ctx = cv.getContext('2d');
  const g = ctx.createRadialGradient(size / 2, size / 2, size * 0.04, size / 2, size / 2, size * 0.5);
  g.addColorStop(0.0, innerRgba);
  g.addColorStop(0.48, midRgba);
  g.addColorStop(1.0, 'rgba(0,0,0,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

export async function createKarooWorldV6(renderer) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#070b12');

  const studioEnv = createStudioSoftboxEnvMap(renderer);
  scene.environment = studioEnv;
  setImaxLightingPreset('cinema_lab', { fogStart: 18.0, fogRange: 45.0 });

  // Fast dark cyclorama backdrop (`depthWrite: false`)
  const cycMat = new THREE.MeshBasicMaterial({ color: '#070c14', side: THREE.BackSide, depthWrite: false });
  const cyc = new THREE.Mesh(new THREE.CylinderGeometry(15.0, 15.0, 11.0, 40, 1, true), cycMat);
  cyc.position.y = 4.8;
  cyc.renderOrder = -10;
  scene.add(cyc);

  // =========================================================================
  // SET A: ESRF SYNCHROTRON X-RAY PALEONTOLOGY LAB
  // =========================================================================
  const labRoot = new THREE.Group();
  scene.add(labRoot);

  const bread = buildOpticalBreadboardTexture(909);
  const labFloor = new THREE.Mesh(
    new THREE.PlaneGeometry(36, 36),
    makeImaxMaterial({
      color: '#1b2430',
      map: bread.albedo,
      normalMap: bread.normal,
      normalScale: 0.55,
      mapRepeat: [6, 6],
      specular: '#8cd8e8',
      specPower: 0.42,
      rimTint: [0.24, 0.72, 0.78],
      rimStrength: 0.18,
      polygonOffset: true,
      polygonOffsetFactor: 2,
      polygonOffsetUnits: 2,
    })
  );
  labFloor.rotation.x = -Math.PI / 2;
  labFloor.receiveShadow = true;
  labRoot.add(labFloor);

  const labStage = createSynchrotronLabStage({ yFloor: 0.0 });
  labRoot.add(labStage.group);

  const fossilRockRig = createKarooRockAndDualFossilRig({ yBase: 0.14 });
  labStage.rotaryTurntable.add(fossilRockRig.root);

  const laserScanner = createLaserTomographyScanner({ width: 2.6, height: 2.4, color: '#5cf8e4' });
  labRoot.add(laserScanner);

  const labBackGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(14, 9),
    new THREE.MeshBasicMaterial({
      map: makeSoftGlowTex('rgba(58, 212, 190, 0.52)', 'rgba(24, 92, 112, 0.16)'),
      transparent: true,
      opacity: 0.65,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  );
  labBackGlow.position.set(0, 1.8, -7.2);
  labRoot.add(labBackGlow);

  const labSpotCone = createVolumetricSpotlightCone({
    color: '#bceff6',
    intensity: 0.10,
    topRadius: 0.45,
    bottomRadius: 2.25,
    height: 5.8,
    renderOrder: 21,
  });
  labSpotCone.position.set(0, 4.4, 0);
  labRoot.add(labSpotCone);

  // =========================================================================
  // SET B: 250-MILLION-YEAR-OLD EARLY TRIASSIC KAROO BURROW CUTAWAY
  // =========================================================================
  const triassicRoot = new THREE.Group();
  triassicRoot.visible = false;
  scene.add(triassicRoot);

  const burrowRig = createTriassicBurrowAndLivingPairRig();
  burrowRig.group.visible = true;
  triassicRoot.add(burrowRig.group);

  const floodRig = createFlashFloodAndPetrificationSystem(burrowRig.tunnelSpine);
  triassicRoot.add(floodRig.group);

  // Scorching Early Triassic Drought Sun Shafts pouring down the inclined burrow entrance!
  const sunBlade = createVolumetricLightBlade({
    color: '#ffbe68',
    intensity: 0.22,
    length: 3.4,
    width: 1.15,
    originX: -1.75,
    renderOrder: 22,
  });
  sunBlade.position.set(-0.25, 1.58, 0.05);
  sunBlade.rotation.z = -0.44;
  triassicRoot.add(sunBlade);

  const triassicSkyGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(8.5, 5.5),
    new THREE.MeshBasicMaterial({
      map: makeSoftGlowTex('rgba(255, 174, 82, 0.85)', 'rgba(196, 88, 34, 0.28)'),
      transparent: true,
      opacity: 0.78,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  );
  triassicSkyGlow.position.set(-2.2, 2.35, -0.72);
  triassicRoot.add(triassicSkyGlow);

  // =========================================================================
  // SHARED MULTI-MOOD CINEMA LIGHTS, TYNDALL DUST & 30 Hz SHADOW RIG
  // =========================================================================
  const ambientLight = new THREE.AmbientLight('#b8d4ea', 0.62);
  scene.add(ambientLight);

  const keyLight = new THREE.DirectionalLight('#fff2dc', 2.95);
  keyLight.position.set(3.4, 6.8, 4.2);
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight('#4ef2e0', 5.4);
  rimLight.position.set(-4.2, 3.6, -3.2);
  scene.add(rimLight);

  const warmFill = new THREE.PointLight('#ffb464', 2.4, 12.0, 1.6);
  warmFill.position.set(1.8, 1.6, 2.5);
  scene.add(warmFill);

  const xrayCoreLight = new THREE.PointLight('#ffd878', 0.0, 5.5, 1.8);
  xrayCoreLight.position.set(0.0, 0.65, 0.35);
  scene.add(xrayCoreLight);

  const dust = createLoopLockedDustMotes({
    count: 54,
    radius: 0.010,
    color: '#ffe4b4',
    loopDurationS: DURATION,
    bounds: { x0: -2.4, xSpan: 4.8, y0: 0.38, ySpan: 2.6, z0: -2.5, zSpan: 2.5 },
    renderOrder: 24,
  });
  scene.add(dust.mesh);

  const shadowRig = createTexelSnappedShadowRig(renderer, { mapSize: 512 });

  return {
    scene,
    cycMat,
    labRoot,
    labStage,
    fossilRockRig,
    laserScanner,
    labBackGlow,
    labSpotCone,
    triassicRoot,
    burrowRig,
    floodRig,
    sunBlade,
    triassicSkyGlow,
    ambientLight,
    keyLight,
    rimLight,
    warmFill,
    xrayCoreLight,
    dust,
    shadowRig,
  };
}
