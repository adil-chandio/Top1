import * as THREE from 'three';
import {
  createVolumetricLightBlade,
  createVolumetricSpotlightCone,
  createLoopLockedDustMotes,
  createLaserTomographyScanner,
  createClearanceLaserGrid,
  createImpactShockwaveRing,
  createBallisticParticleSystem,
} from '../../monarch-v6-imax-sdk/index.js';
import { SHARED_LIGHT_UNIFORMS, setLightingMood } from '../v5/materials_v5.js';
import { createMonarchWorldV5 } from '../v5/world_v5.js';

/**
 * Monarch Cam #03 — Long Video V6 Hollywood IMAX 3D World & Volumetric VFX Suite!
 * Upgrades V5's 3 full-scale 3D sets with:
 *   1. 2:14 AM Silver-Blue Volumetric Moonlight Shafts (`[0..28]`, luma-safe > 18!)
 *   2. Instantaneous Warm Tungsten Volumetric Doorway Light-Blade + 130 Tyndall Dust Motes (`f >= 29`)
 *   3. 4 Overhead Surgical Volumetric Lab Spotlight Cones + 90 Floating Lab Dust Motes
 *   4. 2 Overhead Volumetric Force-Plate Studio Spotlight Cones (`pushupSet`)
 *   5. 3D Holographic Cyan Laser Tomography Curtain (`xrayScanner`)
 *   6. Emerald Floor-Clearance Optical Laser Grid (`clearanceLaser`, Y = +0.09 mm)
 *   7. Expanding Radial Impact Shockwave Ring (`shockwave`)
 *   8. 96-Particle Newtonian Parabolic Ballistic Grit & Spark Engine (`ballisticGrit`)
 *   9. Clean off-axis Phantom v2512 & scaled gooseneck tips so zero white circles photobomb macro shots!
 */
export async function createMonarchWorldLongV6(mats, renderer) {
  const world = await createMonarchWorldV5(mats, renderer);

  // Clean off-axis Phantom v2512 & scaled fiber-optic gooseneck tips (prevents bright white circle bokeh blobs!)
  world.phantomCam.position.set(-178, 36, -248);
  world.phantomCam.rotation.y = 0.34;
  world.labSet.traverse((o) => {
    if (o.isMesh && o.geometry?.type === 'SphereGeometry' && o.position.y > 60) {
      o.scale.setScalar(0.35);
    }
  });

  // 1. 2:14 AM Cool Silver-Blue Moonlight Volumetric Shaft (active before light switch f < 29)
  const moonlightGroup = new THREE.Group();
  for (const [mx, mz, tiltZ] of [[-190, -120, 0.28], [-60, 80, 0.24]]) {
    const mCone = createVolumetricSpotlightCone({
      color: '#7ab8ee',
      intensity: 0.16,
      topRadius: 65,
      bottomRadius: 290,
      height: 1450,
      renderOrder: 21,
    });
    mCone.position.set(mx, 680, mz);
    mCone.rotation.z = tiltZ;
    moonlightGroup.add(mCone);
  }
  const moonFloorPool = new THREE.Mesh(
    new THREE.PlaneGeometry(980, 920),
    new THREE.MeshBasicMaterial({
      color: '#5c92c4',
      transparent: true,
      opacity: 0.18,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })
  );
  moonFloorPool.rotation.x = -Math.PI / 2;
  moonFloorPool.position.set(-180, 0.12, -20);
  moonFloorPool.renderOrder = 2;
  moonlightGroup.add(moonFloorPool);
  world.apartmentSet.add(moonlightGroup);

  // 2. Warm Tungsten Volumetric Doorway Light-Blade + 130 Tyndall Dust Motes (active f >= 29)
  const doorwayVfx = new THREE.Group();
  const doorwayBlade = createVolumetricLightBlade({
    color: '#ffca7a',
    intensity: 0.26,
    length: 148,
    width: 210,
    originX: 2.0,
    renderOrder: 22,
  });
  const doorwayMotes = createLoopLockedDustMotes({
    count: 130,
    radius: 0.046,
    color: '#ffe3b0',
    loopDurationS: 30.0,
    bounds: { x0: -92, xSpan: 94, y0: 0.65, ySpan: 15.0, z0: -46, zSpan: 40 },
    renderOrder: 24,
  });
  doorwayVfx.add(doorwayBlade, doorwayMotes.mesh);
  world.apartmentSet.add(doorwayVfx);

  // 3. UC Berkeley Lab Surgical Overhead Volumetric Cones + 90 Floating Lab Motes
  const labLightCones = new THREE.Group();
  for (const [lx, lz, tiltZ] of [
    [-310, -28, -0.14],
    [-95,  -26, -0.10],
    [ 95,  -26,  0.10],
    [ 310, -28,  0.14],
  ]) {
    const cone = createVolumetricSpotlightCone({
      color: '#9ce8f2',
      intensity: 0.10,
      topRadius: 10,
      bottomRadius: 58,
      height: 145,
      renderOrder: 21,
    });
    cone.position.set(lx, 68, lz);
    cone.rotation.z = tiltZ;
    labLightCones.add(cone);
  }
  const labMotes = createLoopLockedDustMotes({
    count: 90,
    radius: 0.075,
    color: '#b8f4fa',
    loopDurationS: 25.0,
    bounds: { x0: -380, xSpan: 760, y0: 1.4, ySpan: 24.0, z0: -52, zSpan: 42 },
    renderOrder: 24,
  });
  labLightCones.add(labMotes.mesh);
  world.labSet.add(labLightCones);

  // 4. Push-Up Biomechanics Studio Overhead Volumetric Cones
  const studioCones = new THREE.Group();
  for (const [sx, sz, col] of [[-260, -180, '#6ee8f2'], [320, 180, '#ffc478']]) {
    const sc = createVolumetricSpotlightCone({
      color: col,
      intensity: 0.13,
      topRadius: 110,
      bottomRadius: 680,
      height: 1850,
      renderOrder: 21,
    });
    sc.position.set(sx, 920, sz);
    studioCones.add(sc);
  }
  world.pushupSet.add(studioCones);

  // 5. 3D Holographic Cyan Laser Tomography Curtain + Emerald Floor-Clearance Grid + Shockwave + Ballistic Grit
  const xrayScanner = createLaserTomographyScanner({ width: 26.0, height: 17.0, color: '#7efcf4' });
  const clearanceLaser = createClearanceLaserGrid({ width: 48.0, depth: 36.0, floorY: 0.0 });
  const shockwave = createImpactShockwaveRing();
  const ballisticGrit = createBallisticParticleSystem({
    count: 96,
    radius: 0.074,
    color: '#ffd99e',
    gravity: 11.8,
    restitution: 0.38,
    floorY: 0.0,
  });
  world.scene.add(xrayScanner, clearanceLaser, shockwave.mesh, ballisticGrit.mesh);

  // Upgraded V6 Hollywood IMAX 6-Mood Cinema Lighting Controller!
  function setLightingMoodV6(mood) {
    if (mood === 'midnight_dark') {
      SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(-0.38, 0.68, 0.62).normalize();
      SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#86b6ee').multiplyScalar(0.76);
      SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#446894').multiplyScalar(0.42);
      SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#ffc87c').multiplyScalar(0.64);
      SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#344e76').multiplyScalar(0.34);
      SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#242a3a').multiplyScalar(0.24);
      SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.012, 0.020, 0.036);
      SHARED_LIGHT_UNIFORMS.uFogStart.value = 2100.0;
      SHARED_LIGHT_UNIFORMS.uFogRange.value = 4000.0;
      SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.52;
      world.scene.background.set('#0e1926');
    } else if (mood === 'apartment_warm') {
      setLightingMood('apartment_lit', 1.06);
      world.scene.background.set('#14100d');
    } else if (mood === 'xray_surgical') {
      SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(0.32, 0.86, 0.40).normalize();
      SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#eefaff').multiplyScalar(0.96);
      SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#a8e4ee').multiplyScalar(0.34);
      SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#6cf4ee').multiplyScalar(0.72);
      SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#2e4852').multiplyScalar(0.26);
      SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#1a2226').multiplyScalar(0.18);
      SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.008, 0.015, 0.020);
      SHARED_LIGHT_UNIFORMS.uFogStart.value = 1800.0;
      SHARED_LIGHT_UNIFORMS.uFogRange.value = 3500.0;
      SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.68;
      world.scene.background.set('#081116');
    } else if (mood === 'macro_warm') {
      SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(0.38, 0.84, 0.38).normalize();
      SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#ffe8c6').multiplyScalar(1.04);
      SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#dcecee').multiplyScalar(0.38);
      SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#7ef2e2').multiplyScalar(0.60);
      SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#4c5458').multiplyScalar(0.28);
      SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#2c251f').multiplyScalar(0.22);
      SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.012, 0.016, 0.020);
      SHARED_LIGHT_UNIFORMS.uFogStart.value = 1850.0;
      SHARED_LIGHT_UNIFORMS.uFogRange.value = 3600.0;
      SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.68;
      world.scene.background.set('#0b1216');
    } else if (mood === 'zackd_studio') {
      setLightingMood('pushup');
      world.scene.background.set('#091319');
    } else {
      setLightingMood('lab');
      world.scene.background.set('#0a1217');
    }
  }

  function resetVfxPerFrame() {
    xrayScanner.visible = false;
    clearanceLaser.visible = false;
    shockwave.trigger({ progress: -1 });
    ballisticGrit.update(new THREE.Vector3(), 0, { intensity: 0.0 });
  }

  return {
    ...world,
    moonlightGroup,
    doorwayVfx,
    doorwayMotes,
    labLightCones,
    labMotes,
    studioCones,
    xrayScanner,
    clearanceLaser,
    shockwave,
    ballisticGrit,
    setLightingMoodV6,
    resetVfxPerFrame,
  };
}
