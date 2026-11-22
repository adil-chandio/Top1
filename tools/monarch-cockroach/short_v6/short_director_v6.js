import * as THREE from 'three';
import { GLM } from '../v5/cockroach3d_v5.js';
import { SHARED_LIGHT_UNIFORMS } from '../v5/materials_v5.js';

export const FPS = 30;
export const TOTAL_FRAMES = 1050; // Exact 35.000s seamless loop!

export const SHORT_SHOTS_V6 = [
  { id: 'S1_HOOK',      f0:    0, f1:   76, hudTag: 'LAOWA 24MM · 3.20 MM SLOT' },
  { id: 'S2_REWIND',    f0:   76, f1:  161, hudTag: 'PHANTOM 500 FPS · BULLET TIME' },
  { id: 'S3_XRAY',      f0:  161, f1:  316, hudTag: 'UC BERKELEY · X-RAY CUTAWAY' },
  { id: 'S4A_PUSHUP',   f0:  316, f1:  425, hudTag: 'BIOMECHANICS · >80° SPLAY' },
  { id: 'S4B_FEET_OFF', f0:  425, f1:  490, hudTag: '500 FPS MACRO · 0 FEET DOWN' },
  { id: 'S5_SPINES',    f0:  490, f1:  611, hudTag: 'TIBIAL SPINES · GRIP 2.04×' },
  { id: 'S6_PRESS_900X',f0:  611, f1:  726, hudTag: 'LOAD CELL · 6.08 N · 900× BW' },
  { id: 'S7A_GRIT_TRAP',f0:  726, f1:  912, hudTag: '3-SURFACE TRACTION RACE' },
  { id: 'S7B_GATE_FAIL',f0:  912, f1:  995, hudTag: '315 TRIALS · 83% FAIL AT 3.2 MM' },
  { id: 'S8_CTA_LOOP',  f0:  995, f1: 1050, hudTag: 'CRAM BIO-ROBOT · FULL BREAKDOWN' },
];

export function shotAtFrameV6(frame) {
  for (const s of SHORT_SHOTS_V6) {
    if (frame >= s.f0 && frame < s.f1) return s;
  }
  return SHORT_SHOTS_V6[SHORT_SHOTS_V6.length - 1];
}

function easeInOutCubic(x) {
  const t = GLM.clamp(x, 0, 1);
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function easeOutQuint(x) {
  const t = GLM.clamp(x, 0, 1);
  return 1 - Math.pow(1 - t, 5);
}

function dampedImpactShake(frame, triggerFrame, ampMm = 1.0, decay = 0.14) {
  const df = frame - triggerFrame;
  if (df < 0 || df > 36) return { x: 0, y: 0, roll: 0 };
  const env = Math.exp(-df * decay);
  return {
    x: ampMm * env * Math.sin(df * 1.85),
    y: ampMm * 1.25 * env * Math.cos(df * 2.35),
    roll: (ampMm * 0.008) * env * Math.sin(df * 2.10),
  };
}

/**
 * Custom Hollywood IMAX Lighting Palettes (sculpted architectural fill + golden/cyan rims)
 */
function applyImaxMood(mood) {
  if (mood === 'doorway_imax') {
    // Key from golden hallway + cool-amber moonlight fill illuminating the -X oak door panel!
    SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(0.45, 0.62, 0.64).normalize();
    SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#ffd294').multiplyScalar(1.06);
    SHARED_LIGHT_UNIFORMS.uFillDir.value.set(-0.78, 0.42, 0.46).normalize();
    SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#7aa6d8').multiplyScalar(0.52);
    SHARED_LIGHT_UNIFORMS.uRimDir.value.set(0.82, 0.28, -0.50).normalize();
    SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#ffbe6b').multiplyScalar(0.92);
    SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#344c72').multiplyScalar(0.34);
    SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#442812').multiplyScalar(0.28);
    SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.010, 0.015, 0.024);
    SHARED_LIGHT_UNIFORMS.uFogStart.value = 1800.0;
    SHARED_LIGHT_UNIFORMS.uFogRange.value = 3600.0;
    SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.64;
  } else if (mood === 'xray_imax') {
    SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(0.32, 0.84, 0.44).normalize();
    SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#eafbff').multiplyScalar(0.98);
    SHARED_LIGHT_UNIFORMS.uFillDir.value.set(-0.36, 0.48, 0.80).normalize();
    SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#7be6f2').multiplyScalar(0.38);
    SHARED_LIGHT_UNIFORMS.uRimDir.value.set(-0.52, 0.48, -0.70).normalize();
    SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#58f6e8').multiplyScalar(0.82);
    SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#26444e').multiplyScalar(0.26);
    SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#142026').multiplyScalar(0.18);
    SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.006, 0.014, 0.019);
    SHARED_LIGHT_UNIFORMS.uFogStart.value = 1400.0;
    SHARED_LIGHT_UNIFORMS.uFogRange.value = 3200.0;
    SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.64;
  } else if (mood === 'lab_imax') {
    SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(0.36, 0.84, 0.40).normalize();
    SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#fff0dc').multiplyScalar(1.02);
    SHARED_LIGHT_UNIFORMS.uFillDir.value.set(-0.36, 0.48, 0.80).normalize();
    SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#9adce8').multiplyScalar(0.38);
    SHARED_LIGHT_UNIFORMS.uRimDir.value.set(-0.56, 0.46, -0.68).normalize();
    SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#7ee8f4').multiplyScalar(0.70);
    SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#384a52').multiplyScalar(0.26);
    SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#26201c').multiplyScalar(0.20);
    SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.008, 0.013, 0.018);
    SHARED_LIGHT_UNIFORMS.uFogStart.value = 1650.0;
    SHARED_LIGHT_UNIFORMS.uFogRange.value = 3400.0;
    SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.68;
  } else if (mood === 'arena_imax') {
    SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(0.28, 0.88, 0.38).normalize();
    SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#ffe6c8').multiplyScalar(1.04);
    SHARED_LIGHT_UNIFORMS.uFillDir.value.set(-0.32, 0.45, 0.83).normalize();
    SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#78d0e0').multiplyScalar(0.40);
    SHARED_LIGHT_UNIFORMS.uRimDir.value.set(-0.48, 0.45, -0.75).normalize();
    SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#ffb464').multiplyScalar(0.78);
    SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#26424c').multiplyScalar(0.30);
    SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#121c22').multiplyScalar(0.22);
    SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.006, 0.012, 0.018);
    SHARED_LIGHT_UNIFORMS.uFogStart.value = 2400.0;
    SHARED_LIGHT_UNIFORMS.uFogRange.value = 4400.0;
    SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.70;
  }
}

export function createShortDirectorV6(world, vfx, camera) {
  const camPos = new THREE.Vector3();
  const lookAt = new THREE.Vector3();
  const prevCamPos = new THREE.Vector3();
  const prevLookAt = new THREE.Vector3();
  const shadowFocus = new THREE.Vector3();
  const motionVec = new THREE.Vector2();
  const upVec = new THREE.Vector3(0, 1, 0);
  let lastFrameRendered = -999;

  // Add a crisp golden 3.2mm doorway bevel highlight strip right at X = -0.25mm, Y = 1.6mm so the
  // 3.20 mm oak door gap blazes unmistakably like a cinema light slit!
  const doorSlotGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(520, 2.8),
    new THREE.MeshBasicMaterial({
      color: '#ffd89a',
      transparent: true,
      opacity: 0.78,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })
  );
  doorSlotGlow.rotation.y = -Math.PI / 2;
  doorSlotGlow.position.set(-0.2, 1.55, 0);
  doorSlotGlow.renderOrder = 21;
  world.apartmentSet.add(doorSlotGlow);

  // Canonical Frame-0 State (23.5 mm Z clearance between penny center Z=+19.5 and roach Z=-4.0 -> ZERO leg overlap!)
  const HOOK_PENNY_POS   = new THREE.Vector3(-21.0, 0.0, 19.5);
  const HOOK_CAM_START   = new THREE.Vector3(-82.0, 20.5, 48.0);
  const HOOK_LOOK_START  = new THREE.Vector3(-12.0, 3.8, 5.5);
  const HOOK_FOV_START   = 50.0;
  const HOOK_ROACH_X0    = -31.0;
  const HOOK_ROACH_Z0    = -4.0;

  function resetSceneActors() {
    world.apartmentSet.visible = false;
    world.labSet.visible = false;
    world.pushupSet.visible = false;
    world.corridorGroup.visible = true;
    world.ceilingSlab.visible = true;
    world.labGateGroup.visible = false;
    world.tractionPlateGroup.visible = false;
    world.gritSwatchGroup.visible = false;
    world.multiLaneGroup.visible = false;
    world.cramBenchProp.root.visible = true;

    world.roachHero.root.visible = false;
    world.roachB.root.visible = false;
    world.roachC.root.visible = false;
    world.xrayRig.group.visible = false;
    world.cramActor.root.visible = false;
    world.dustParticles.visible = false;

    world.humanActors.homeowner.root.visible = false;
    world.humanActors.researcher.root.visible = false;
    vfx.resetPerFrame();
  }

  function evaluateFrame(frame) {
    const f = ((frame % TOTAL_FRAMES) + TOTAL_FRAMES) % TOTAL_FRAMES;
    const time = f / FPS;
    const shot = shotAtFrameV6(f);
    const u = (f - shot.f0) / Math.max(1, shot.f1 - shot.f0);

    resetSceneActors();
    vfx.updateDoorwayMotes(time);

    let fov = 46.0;
    let camRoll = 0.0;
    let focusDist = 56.0;
    let dofRange = 46.0;
    let maxBlur = 3.0;
    let bloomAmt = 0.44;
    let exposure = 1.24;
    let shadowHalf = 68.0;
    let explicitMotionX = 0.0;
    let explicitMotionY = 0.0;
    let telemetryMetric = '';

    // =======================================================================
    // SHOT 1 [0..76]: HOOK — "Under 2 pennies — at 50x body length per second."
    // =======================================================================
    if (shot.id === 'S1_HOOK') {
      world.apartmentSet.visible = true;
      world.roachHero.root.visible = true;
      applyImaxMood('doorway_imax');
      world.penniesGroup.position.copy(HOOK_PENNY_POS);

      // Newtonian deceleration to probe slot (u=0..0.32), then explosive C-spine launch (u=0.32..1.0)!
      let rx, ceil, probe, pitch, roll, phase;
      if (u < 0.32) {
        const k = easeOutQuint(u / 0.32);
        rx = GLM.mix(HOOK_ROACH_X0, -14.5, k);
        ceil = GLM.mix(12.2, 8.4, k);
        probe = Math.sin(k * Math.PI * 0.9);
        pitch = -0.22 * k;
        roll = 0.16 * k;
        phase = u * 7.5;
      } else {
        const k = easeInOutCubic((u - 0.32) / 0.68);
        rx = GLM.mix(-14.5, 29.0, Math.pow(k, 1.35));
        ceil = GLM.mix(8.4, 3.20, GLM.smoothstep(0.0, 0.38, k));
        probe = 1.0 - GLM.smoothstep(0.0, 0.45, k);
        pitch = -0.22 * (1.0 - GLM.smoothstep(0.15, 0.65, k));
        roll = 0.18 * Math.sin(Math.PI * GLM.clamp(k * 1.4, 0, 1));
        phase = 2.4 + k * 11.2;
      }

      const pennyJolt = dampedImpactShake(f, 25, 0.16, 0.22);
      world.penniesGroup.children[1].position.y = 2.30 + Math.abs(pennyJolt.y) * 0.5;

      const rState = world.roachHero.update({
        ceilingMm: ceil,
        worldX: rx,
        worldZ: HOOK_ROACH_Z0,
        yaw: 0.04 * Math.sin(u * 6.0) * GLM.smoothstep(0.0, 0.15, u),
        phase,
        antennaProbe: probe,
        headPitch: pitch,
        pronotumRoll: roll,
        time,
      });

      if (u > 0.30 && u < 0.88) {
        vfx.updateBallisticGrit(rState.landmarks.r3Spine, time, 0.95, 1.35, -1.0);
      }

      // Camera tracks cleanly behind & left of the pennies so pennies sit in lower-right foreground
      // while the full cockroach compresses & shoots under the blazing 3.2mm oak door in center-frame!
      const camEase = easeInOutCubic(u);
      camPos.set(
        GLM.mix(HOOK_CAM_START.x, -44.0, camEase),
        GLM.mix(HOOK_CAM_START.y, 8.8, camEase),
        GLM.mix(HOOK_CAM_START.z, 29.0, camEase)
      );
      lookAt.set(
        GLM.mix(HOOK_LOOK_START.x, 2.0, camEase),
        GLM.mix(HOOK_LOOK_START.y, 2.6, camEase),
        GLM.mix(HOOK_LOOK_START.z, 2.5, camEase)
      );
      fov = GLM.mix(HOOK_FOV_START, 46.0, camEase);
      camRoll = 0.035 * Math.sin(u * Math.PI);
      const launchShake = dampedImpactShake(f, 26, 0.42, 0.18);
      camPos.x += launchShake.x;
      camPos.y += launchShake.y;
      camRoll += launchShake.roll;

      shadowFocus.set(rx * 0.5 - 8.0, 2.0, 6.0);
      shadowHalf = 68.0;
      focusDist = camPos.distanceTo(lookAt);
      dofRange = 48.0;
      bloomAmt = 0.48;
      telemetryMetric = `GAP ${ceil.toFixed(2)} MM`;
    }

    // =======================================================================
    // SHOT 2 [76..161]: BULLET-TIME REWIND — "12.5 mm tall... through a 3.2 mm gap."
    // =======================================================================
    else if (shot.id === 'S2_REWIND') {
      world.apartmentSet.visible = true;
      world.roachHero.root.visible = true;
      applyImaxMood('doorway_imax');
      world.penniesGroup.position.copy(HOOK_PENNY_POS);

      let rx, ceil, phase;
      if (u < 0.42) {
        const k = easeOutQuint(u / 0.42);
        rx = GLM.mix(14.0, -17.5, k);
        ceil = GLM.mix(3.20, 12.52, easeInOutCubic(k));
        phase = 13.6 - k * 5.2;
      } else if (u < 0.74) {
        const k = (u - 0.42) / 0.32;
        rx = GLM.mix(-17.5, -14.0, k);
        ceil = 12.52 - 0.35 * Math.sin(k * Math.PI);
        phase = 8.4 + k * 0.9;
      } else {
        const k = easeInOutCubic((u - 0.74) / 0.26);
        rx = GLM.mix(-14.0, -4.5, k);
        ceil = GLM.mix(12.52, 3.30, k);
        phase = 9.3 + k * 2.1;
      }

      world.roachHero.update({
        ceilingMm: ceil,
        worldX: rx,
        worldZ: HOOK_ROACH_Z0,
        yaw: 0.02,
        phase,
        antennaProbe: GLM.smoothstep(0.65, 0.95, u) * 0.7,
        headPitch: -0.14 * GLM.smoothstep(0.70, 1.0, u),
        time,
      });

      // Sweeping 105-deg Bullet-Time Orbit across the golden doorway light blade (full body + pennies visible!)
      const orb = easeInOutCubic(u);
      const ang = GLM.mix(0.62, -0.52, orb);
      const rad = GLM.mix(64.0, 58.0, Math.sin(orb * Math.PI));
      camPos.set(
        rx - Math.cos(ang) * rad,
        GLM.mix(10.5, 14.5, Math.sin(orb * Math.PI)),
        2.0 + Math.sin(ang) * rad
      );
      lookAt.set(rx + 3.0, GLM.mix(3.0, 5.0, 1.0 - Math.abs(u - 0.55) * 2.0), 2.0);
      fov = 47.0;
      camRoll = -0.042 * Math.sin(orb * Math.PI);
      explicitMotionX = u < 0.14 ? (1.0 - u / 0.14) * 0.012 : 0.0;

      shadowFocus.set(rx, 2.0, 4.0);
      shadowHalf = 68.0;
      focusDist = camPos.distanceTo(lookAt);
      dofRange = 46.0;
      bloomAmt = 0.50;
      telemetryMetric = `HEIGHT ${ceil.toFixed(1)} TO 3.2 MM`;
    }

    // =======================================================================
    // SHOT 3 [161..316]: LASER TOMOGRAPHY X-RAY — "Rigid roof-shingle plates..."
    // =======================================================================
    else if (shot.id === 'S3_XRAY') {
      world.labSet.visible = true;
      world.ceilingSlab.visible = false;
      world.humanActors.researcher.root.visible = true;
      world.humanActors.poseResearcher(time, 0.65, 0.55);
      applyImaxMood('xray_imax');

      const compWave = 0.5 - 0.5 * Math.cos(GLM.clamp((u - 0.10) / 0.90, 0, 1) * Math.PI * 3.0);
      const compAlpha = GLM.clamp(0.08 + 0.92 * compWave, 0.0, 1.0);

      if (u < 0.18) {
        const scanU = u / 0.18;
        vfx.xrayScanner.visible = true;
        vfx.xrayScanner.position.set(GLM.mix(18.0, -20.0, scanU), 0.0, 0.0);
      }

      if (u < 0.09) {
        world.roachHero.root.visible = true;
        world.roachHero.update({
          ceilingMm: GLM.mix(11.8, 9.2, u / 0.09),
          worldX: 0,
          worldZ: 0,
          phase: time * 4.2,
          time,
        });
      } else {
        world.xrayRig.group.visible = true;
        world.xrayRig.update({
          compAlpha,
          showPlaten: true,
          showLoadArrows: false,
          time,
          phase: time * 3.4,
        });
      }

      // Full-Body 9:16 Portrait Macro Parallax Arc (entire 31mm X-ray cockroach + 7 plates + 6 hinges in frame!)
      const arc = easeInOutCubic(u);
      camPos.set(
        GLM.mix(22.0, -18.0, arc),
        GLM.mix(17.5, 11.5, arc),
        GLM.mix(72.0, 62.0, Math.sin(arc * Math.PI))
      );
      lookAt.set(GLM.mix(-1.5, -2.5, arc), GLM.mix(4.6, 3.2, compAlpha), 0.0);
      fov = 46.0;
      camRoll = 0.022 * Math.sin(arc * Math.PI * 2.0);
      shadowFocus.set(-1.5, 3.0, 0.0);
      shadowHalf = 58.0;
      focusDist = camPos.distanceTo(lookAt);
      dofRange = 42.0;
      bloomAmt = 0.46;
      telemetryMetric = `COMPRESSION ${Math.round(compAlpha * 60)}%`;
    }

    // =======================================================================
    // SHOT 4A [316..425]: TRAILER DROP "WAIT." + DOLLY-ZOOM PUSH-UP COLLAPSE
    // =======================================================================
    else if (shot.id === 'S4A_PUSHUP') {
      world.pushupSet.visible = true;
      applyImaxMood('arena_imax');

      const splayAlpha = GLM.smoothstep(0.16, 0.62, u);
      const collapseU = GLM.clamp((u - 0.63) / 0.37, 0.0, 1.0);
      const repCycle = u < 0.63 ? u * 1.4 : 0.88 + 0.12 * collapseU;
      world.humanActors.poseAthletePushup(time, splayAlpha, repCycle);

      let chestDrop = 0.0;
      if (collapseU > 0.0) {
        const gDrop = Math.min(1.0, collapseU * 2.8);
        const bounce = collapseU > 0.35 ? Math.exp(-(collapseU - 0.35) * 9.0) * Math.abs(Math.sin((collapseU - 0.35) * 14.0)) * 0.18 : 0.0;
        chestDrop = (gDrop * gDrop - bounce) * 245.0;
      }
      const baseChestY = GLM.mix(490.0, 395.0, splayAlpha) - chestDrop;
      world.athletePivot.position.set(-420.0, Math.max(155.0, baseChestY), 0.0);

      const hands = world.humanActors.getAthleteHandWorldPositions();
      const handArr = [hands.left, hands.right];
      const warnCollapse = collapseU > 0.05;
      for (let i = 0; i < 2; i++) {
        const hp = handArr[i];
        world.forcePads[i].position.set(hp.x, 4.0, hp.z);
        world.forcePads[i].material.color.set(warnCollapse ? '#ff4d2e' : (splayAlpha > 0.5 ? '#ff9f42' : '#268c9e'));
        const ha = world.handArrows[i];
        ha.group.position.set(hp.x, 8.0, hp.z);
        const tiltZ = ha.side * splayAlpha * 0.68;
        ha.group.rotation.set(tiltZ, 0, 0);
        const vScale = warnCollapse ? 0.55 : (1.0 - 0.25 * splayAlpha);
        ha.group.scale.set(1.0, vScale, 1.0);
        ha.shaft.material = splayAlpha > 0.45 ? world.vecMatAmber : world.vecMatGreen;
        ha.tip.material = ha.shaft.material;
      }

      if (f >= 385 && f < 418) {
        vfx.triggerShockwave({
          x: 240.0, y: 6.0, z: 0.0,
          size: 1950.0,
          progress: (f - 385) / 33.0,
          colorHex: '#ff6a3d',
        });
      }

      // Full-Span 9:16 Arena Framing (both hands, force pads, GRF arrows, and athlete 100% inside frame!)
      const dz = GLM.smoothstep(0.0, 0.24, u);
      fov = GLM.mix(53.0, 44.0, dz) + collapseU * 2.0;
      const dist = GLM.mix(3150.0, 3680.0, dz) - collapseU * 240.0;
      const azim = GLM.mix(0.32, -0.22, easeInOutCubic(u));
      camPos.set(
        100.0 + Math.cos(azim) * dist,
        GLM.mix(1120.0, 740.0, easeInOutCubic(u)),
        Math.sin(azim) * dist
      );
      lookAt.set(80.0, Math.max(240.0, baseChestY - 20.0), 0.0);

      const colShake = dampedImpactShake(f, 385, 26.0, 0.16);
      camPos.x += colShake.x;
      camPos.y += colShake.y;
      camRoll = colShake.roll * 0.08;

      shadowFocus.set(80.0, 220.0, 0.0);
      shadowHalf = 1350.0;
      focusDist = camPos.distanceTo(lookAt);
      dofRange = 1800.0;
      bloomAmt = 0.46;
      telemetryMetric = `ARM SPLAY ${Math.round(GLM.mix(38, 86, splayAlpha))}°`;
    }

    // =======================================================================
    // SHOT 4B [425..490]: ULTRA-MACRO — "Every foot lifts off. Zero feet down."
    // =======================================================================
    else if (shot.id === 'S4B_FEET_OFF') {
      world.labSet.visible = true;
      world.ceilingSlab.position.y = 3.25;
      applyImaxMood('lab_imax');

      const rx = GLM.mix(-14.0, 14.0, u);
      world.roachHero.root.visible = true;
      const rState = world.roachHero.update({
        ceilingMm: 3.25,
        worldX: rx,
        worldZ: 0.0,
        phase: 2.15 + u * 1.35,
        gaitMode: 'oar',
        floorY: 0.38,
        time,
      });

      vfx.clearanceLaser.visible = true;
      vfx.clearanceLaser.position.set(rState.landmarks.r3Claw.x, 0.08, rState.landmarks.r3Claw.z);
      vfx.clearanceLaser.material.uniforms.uTime.value = time;

      const claw = rState.landmarks.r3Claw;
      camPos.set(
        claw.x + GLM.mix(9.5, 5.5, u),
        GLM.mix(3.6, 2.6, u),
        claw.z + 23.0
      );
      lookAt.set(claw.x - 1.5, 1.15, claw.z - 0.5);
      fov = 38.0;
      camRoll = -0.018;
      shadowFocus.copy(claw);
      shadowHalf = 32.0;
      focusDist = camPos.distanceTo(lookAt);
      dofRange = 18.0;
      maxBlur = 3.6;
      bloomAmt = 0.46;
      telemetryMetric = 'TARSAL CONTACT: 0.0 N';
    }

    // =======================================================================
    // SHOT 5 [490..611]: CRAMPON SPINES + WHIP-CRANE TO TWIN-OAR ROWING!
    // =======================================================================
    else if (shot.id === 'S5_SPINES') {
      world.labSet.visible = true;
      world.ceilingSlab.position.y = 3.30;
      applyImaxMood('lab_imax');
      world.roachHero.root.visible = true;

      const rx = GLM.mix(-24.0, 52.0, Math.pow(u, 1.15));
      const phase = u < 0.60 ? (3.5 + u * 4.8) : (6.38 + (u - 0.60) * 14.5);
      const rState = world.roachHero.update({
        ceilingMm: 3.30,
        worldX: rx,
        worldZ: 0.0,
        phase,
        gaitMode: 'oar',
        strideAmp: 1.12,
        time,
      });

      const sp = rState.landmarks.r3Spine;
      world.tractionPlateGroup.visible = u < 0.66;
      world.tractionPlateGroup.position.set(sp.x, 0.0, sp.z);
      vfx.updateBallisticGrit(sp, time, 1.0, u < 0.60 ? 1.1 : 2.2, -1.0);

      const crane = easeInOutCubic(GLM.clamp((u - 0.54) / 0.30, 0.0, 1.0));
      const macroCam = new THREE.Vector3(sp.x - 8.5, 4.4, sp.z + 24.5);
      const macroLook = new THREE.Vector3(sp.x + 0.5, 1.1, sp.z);

      const topCam = new THREE.Vector3(rx - 10.0, 66.0, 18.0);
      const topLook = new THREE.Vector3(rx + 2.0, 1.5, 0.0);

      camPos.lerpVectors(macroCam, topCam, crane);
      lookAt.lerpVectors(macroLook, topLook, crane);
      fov = GLM.mix(39.0, 45.0, crane);
      camRoll = 0.045 * Math.sin(crane * Math.PI);
      if (u > 0.54 && u < 0.80) {
        explicitMotionY = 0.011 * Math.sin(((u - 0.54) / 0.26) * Math.PI);
      }

      shadowFocus.set(rx, 1.5, 0.0);
      shadowHalf = GLM.mix(34.0, 58.0, crane);
      focusDist = camPos.distanceTo(lookAt);
      dofRange = GLM.mix(20.0, 48.0, crane);
      bloomAmt = 0.44;
      telemetryMetric = crane < 0.5 ? 'SPINE SHEAR 2.04×' : 'L2 + R2 TWIN-OAR GAIT';
    }

    // =======================================================================
    // SHOT 6 [611..726]: 900x HYDRAULIC ANVIL SLAM -> <80MS REBOUND & LAUNCH!
    // =======================================================================
    else if (shot.id === 'S6_PRESS_900X') {
      world.labSet.visible = true;
      world.ceilingSlab.visible = false;
      applyImaxMood('lab_imax');

      if (f < 682) {
        world.xrayRig.group.visible = true;
        let compAlpha;
        if (f < 620) {
          compAlpha = 0.06;
        } else if (f <= 634) {
          const slamK = Math.pow((f - 620) / 14.0, 2.4);
          compAlpha = GLM.mix(0.06, 1.00, slamK);
        } else {
          compAlpha = 1.00 - 0.025 * Math.exp(-(f - 634) * 0.25) * Math.cos((f - 634) * 1.8);
        }
        world.xrayRig.update({
          compAlpha: GLM.clamp(compAlpha, 0, 1),
          showPlaten: true,
          showLoadArrows: f >= 634,
          time,
          phase: 1.2 + time * 1.5,
        });

        if (f >= 634 && f < 664) {
          vfx.triggerShockwave({
            x: -1.2, y: 0.20, z: 0.0,
            size: 64.0,
            progress: (f - 634) / 30.0,
            colorHex: '#ffd280',
          });
        }

        const pShake = dampedImpactShake(f, 634, 1.85, 0.17);
        camPos.set(14.0 + pShake.x, 12.5 + pShake.y, 66.0);
        lookAt.set(-1.5, 3.8, 0.0);
        fov = 45.0;
        camRoll = pShake.roll;
        shadowFocus.set(-1.5, 2.5, 0.0);
        shadowHalf = 58.0;
        const loadN = f < 620 ? 0.0 : (f < 634 ? ((f - 620) / 14.0) * 6.08 : 6.08);
        telemetryMetric = `LOAD ${loadN.toFixed(2)} N · ${Math.round((loadN / 6.08) * 896)}× BW`;
      } else {
        world.roachHero.root.visible = true;
        const kRun = (f - 682) / 44.0;
        const reboundCeil = GLM.mix(3.35, 12.20, GLM.smoothstep(0.0, 0.08, kRun));
        const rx = Math.pow(kRun, 1.45) * 128.0;
        const rState = world.roachHero.update({
          ceilingMm: reboundCeil,
          worldX: rx,
          worldZ: 0.0,
          phase: 4.0 + kRun * 13.8,
          gaitMode: 'tripod',
          strideAmp: 1.18,
          time,
        });
        vfx.updateBallisticGrit(rState.landmarks.r3Spine, time, 1.0, 2.4, -1.0);

        camPos.set(GLM.mix(14.0, 68.0, easeOutQuint(kRun)), GLM.mix(12.5, 16.0, kRun), GLM.mix(66.0, 52.0, kRun));
        lookAt.set(GLM.mix(-1.5, rx + 6.0, easeOutQuint(kRun)), 4.0, 0.0);
        fov = GLM.mix(45.0, 48.0, kRun);
        camRoll = -0.032 * Math.sin(kRun * Math.PI);
        explicitMotionX = -0.014 * Math.sin(kRun * Math.PI);
        shadowFocus.set(rx, 3.0, 0.0);
        shadowHalf = 64.0;
        telemetryMetric = 'REBOUND <80 MS · 76.7 CM/S';
      }
      focusDist = camPos.distanceTo(lookAt);
      dofRange = 46.0;
      bloomAmt = 0.48;
    }

    // =======================================================================
    // SHOT 7A [726..912]: 3-LANE GRIT RACE -> COARSE 20-GRIT BELLY-SNAG MACRO
    // =======================================================================
    else if (shot.id === 'S7A_GRIT_TRAP') {
      world.labSet.visible = true;
      world.corridorGroup.visible = false;
      world.multiLaneGroup.visible = true;
      world.laneFloors[0].material = world.mats.grit100Mat;
      world.laneFloors[1].material = world.mats.grit40Mat;
      world.laneFloors[2].material = world.mats.grit20Mat;
      world.laneRoofs.forEach((r) => { r.position.y = 4.0; });
      applyImaxMood('lab_imax');

      world.roachB.root.visible = true;
      world.roachHero.root.visible = true;
      world.roachC.root.visible = true;

      const xSlick = -70.0 + u * 52.0 - 1.6 * Math.sin(u * 38.0);
      world.roachB.update({
        ceilingMm: 4.0,
        worldX: xSlick,
        worldZ: -38.0,
        yaw: 0.07 * Math.sin(u * 34.0),
        phase: u * 26.0,
        gaitMode: 'oar',
        time,
      });

      const xMed = -70.0 + u * 168.0;
      const heroRes = world.roachHero.update({
        ceilingMm: 4.0,
        worldX: xMed,
        worldZ: 0.0,
        yaw: 0.0,
        phase: u * 21.0,
        gaitMode: 'oar',
        time,
      });

      const snagCycle = u * 15.0;
      const snagStall = Math.pow(Math.sin(snagCycle * Math.PI), 4) * 2.8;
      const xCoarse = -70.0 + u * 68.0 - snagStall;
      const snagYaw = 0.11 * Math.sin(snagCycle * Math.PI * 2.0);
      const snagPitch = 0.06 * Math.abs(Math.sin(snagCycle * Math.PI));
      world.roachC.update({
        ceilingMm: 4.0,
        worldX: xCoarse,
        worldZ: 38.0,
        yaw: snagYaw,
        bodyPitch: snagPitch,
        pronotumRoll: -snagYaw * 0.8,
        phase: u * 18.5,
        gaitMode: 'oar',
        time,
      });

      // Wide 9:16 3-lane stadium view (all 3 lanes clearly inside frame!) -> Rack down to Coarse 20 belly snag!
      const rack = easeInOutCubic(GLM.clamp((u - 0.46) / 0.22, 0.0, 1.0));
      const wideCam = new THREE.Vector3(xMed * 0.42 + 88.0, 86.0, 146.0);
      const wideLook = new THREE.Vector3(xMed * 0.42 - 14.0, 2.0, 2.0);

      const snagCam = new THREE.Vector3(xCoarse + 38.0, 7.5, 68.0);
      const snagLook = new THREE.Vector3(xCoarse - 3.0, 1.6, 37.5);

      camPos.lerpVectors(wideCam, snagCam, rack);
      lookAt.lerpVectors(wideLook, snagLook, rack);
      fov = GLM.mix(50.0, 40.0, rack);
      camRoll = rack * 0.025 * Math.sin(snagCycle * Math.PI * 2.0);

      if (rack < 0.6) {
        vfx.updateBallisticGrit(heroRes.landmarks.r3Spine, time, 0.85, 2.0, -1.0);
      }

      shadowFocus.lerpVectors(wideLook, snagLook, rack);
      shadowHalf = GLM.mix(105.0, 44.0, rack);
      focusDist = camPos.distanceTo(lookAt);
      dofRange = GLM.mix(90.0, 26.0, rack);
      bloomAmt = 0.44;
      telemetryMetric = rack < 0.5 ? '40-GRIT OPTIMAL GRIP' : '20-GRIT BELLY SNAG';
    }

    // =======================================================================
    // SHOT 7B [912..995]: DUAL-ROACH 3.2MM GATE FAILURE — "4 in 5 fail (83%)"
    // =======================================================================
    else if (shot.id === 'S7B_GATE_FAIL') {
      world.labSet.visible = true;
      world.ceilingSlab.visible = false;
      world.labGateGroup.visible = true;
      world.labGateGroup.position.set(0.0, 3.15, 0.0);
      applyImaxMood('lab_imax');

      world.roachHero.root.visible = true;
      world.roachB.root.visible = true;

      let xWedge, wedgeCeil, wedgePhase;
      if (f < 936) {
        const k = easeOutQuint((f - 912) / 24.0);
        xWedge = GLM.mix(-36.0, 1.6, k);
        wedgeCeil = GLM.mix(11.2, 3.25, k);
        wedgePhase = (f - 912) * 0.42;
      } else {
        const dt = f - 936;
        xWedge = 1.6 + 0.28 * Math.sin(dt * 1.9) * Math.exp(-dt * 0.02);
        wedgeCeil = 3.22;
        wedgePhase = 10.08 + dt * 0.52;
      }
      const wRes = world.roachHero.update({
        ceilingMm: wedgeCeil,
        worldX: xWedge,
        worldZ: 10.5,
        yaw: 0.04 * Math.sin(f * 0.9),
        pronotumRoll: 0.14,
        phase: wedgePhase,
        gaitMode: 'oar',
        time,
      });

      if (f >= 936) {
        vfx.updateBallisticGrit(wRes.landmarks.r3Spine, time, 0.95, 2.3, -1.0);
        if (f < 962) {
          vfx.triggerShockwave({
            x: 2.0, y: 0.22, z: 10.5,
            size: 38.0,
            progress: (f - 936) / 26.0,
            colorHex: '#6ef8f2',
          });
        }
      }

      let xTurn, zTurn, yawTurn, probeTurn;
      if (u < 0.36) {
        const k = easeOutQuint(u / 0.36);
        xTurn = GLM.mix(-42.0, -14.5, k);
        zTurn = -14.5;
        yawTurn = 0.0;
        probeTurn = Math.sin(k * Math.PI);
      } else if (u < 0.66) {
        const k = easeInOutCubic((u - 0.36) / 0.30);
        xTurn = -14.5 - 6.0 * Math.sin(k * Math.PI * 0.5);
        zTurn = -14.5 - 7.5 * Math.sin(k * Math.PI);
        yawTurn = k * Math.PI;
        probeTurn = 1.0 - k;
      } else {
        const k = (u - 0.66) / 0.34;
        xTurn = -20.5 - k * 34.0;
        zTurn = -14.5;
        yawTurn = Math.PI;
        probeTurn = 0.0;
      }
      world.roachB.update({
        ceilingMm: 11.8,
        worldX: xTurn,
        worldZ: zTurn,
        yaw: yawTurn,
        antennaProbe: probeTurn,
        phase: u * 16.0,
        gaitMode: 'tripod',
        time,
      });

      // Elevated 3/4 gate master showing BOTH the cyan 3.2mm acrylic gate, wedged roach, AND turning roach!
      const wShake = dampedImpactShake(f, 936, 1.15, 0.19);
      camPos.set(
        GLM.mix(-74.0, -56.0, easeInOutCubic(u)) + wShake.x,
        GLM.mix(32.0, 24.0, easeInOutCubic(u)) + wShake.y,
        GLM.mix(68.0, 56.0, easeInOutCubic(u))
      );
      lookAt.set(-8.0, 5.0, -1.5);
      fov = 48.0;
      camRoll = wShake.roll;
      shadowFocus.set(-10.0, 3.0, 0.0);
      shadowHalf = 68.0;
      focusDist = camPos.distanceTo(lookAt);
      dofRange = 54.0;
      bloomAmt = 0.46;
      telemetryMetric = '3.2 MM GATE · 83% FAIL';
    }

    // =======================================================================
    // SHOT 8 [995..1050]: CRAM BIO-ROBOT SPRINT -> SEAMLESS WHIP-LOOP TO F=0!
    // =======================================================================
    else {
      if (f < 1031) {
        const k = (f - 995) / 36.0;
        world.labSet.visible = true;
        world.ceilingSlab.visible = false;
        world.cramBenchProp.root.visible = false;
        world.roachHero.root.visible = true;
        world.cramActor.root.visible = true;
        applyImaxMood('lab_imax');

        const rx = -45.0 + k * 96.0;
        world.roachHero.update({
          ceilingMm: 9.5,
          worldX: rx,
          worldZ: 20.0,
          phase: k * 11.5,
          gaitMode: 'tripod',
          time,
        });
        world.cramActor.update({
          worldX: -48.0 + k * 78.0,
          worldZ: -16.0,
          yaw: 0.0,
          compAlpha: 0.82,
          phase: k * 24.0,
        });

        const whipAccel = GLM.smoothstep(0.68, 1.0, k);
        camPos.set(
          GLM.mix(58.0, 96.0, k) + whipAccel * 45.0,
          GLM.mix(38.0, 28.0, k),
          GLM.mix(92.0, 68.0, k)
        );
        lookAt.set(GLM.mix(-8.0, rx - 4.0, k) + whipAccel * 55.0, 6.0, 2.0);
        fov = GLM.mix(48.0, 50.0, k);
        camRoll = -0.055 * whipAccel;
        explicitMotionX = 0.024 * whipAccel;

        shadowFocus.set(rx * 0.5, 4.0, 0.0);
        shadowHalf = 86.0;
        focusDist = camPos.distanceTo(lookAt);
        dofRange = 68.0;
        bloomAmt = 0.46;
        telemetryMetric = 'UC BERKELEY CRAM ROBOT';
      } else {
        const w = (f - 1031) / (1050 - 1031);
        const e = easeOutQuint(w);

        world.apartmentSet.visible = true;
        world.roachHero.root.visible = true;
        applyImaxMood('doorway_imax');
        world.penniesGroup.position.copy(HOOK_PENNY_POS);
        world.penniesGroup.children[1].position.y = 2.30;

        const preX = GLM.mix(-54.0, HOOK_ROACH_X0, e);
        world.roachHero.update({
          ceilingMm: 12.2,
          worldX: preX,
          worldZ: HOOK_ROACH_Z0,
          yaw: 0.0,
          phase: (w - 1.0) * 4.8,
          antennaProbe: 0.0,
          headPitch: 0.0,
          pronotumRoll: 0.0,
          time,
        });

        camPos.set(
          GLM.mix(-128.0, HOOK_CAM_START.x, e),
          GLM.mix(28.0, HOOK_CAM_START.y, e),
          GLM.mix(72.0, HOOK_CAM_START.z, e)
        );
        lookAt.set(
          GLM.mix(-38.0, HOOK_LOOK_START.x, e),
          GLM.mix(5.2, HOOK_LOOK_START.y, e),
          GLM.mix(10.0, HOOK_LOOK_START.z, e)
        );
        fov = HOOK_FOV_START;
        camRoll = 0.055 * (1.0 - e);
        explicitMotionX = 0.024 * (1.0 - e);

        shadowFocus.set(preX * 0.5 - 8.0, 2.0, 6.0);
        shadowHalf = 68.0;
        focusDist = camPos.distanceTo(lookAt);
        dofRange = 48.0;
        bloomAmt = 0.48;
        telemetryMetric = 'GAP 3.20 MM';
      }
    }

    const loopHarmonic1 = (2.0 * Math.PI * 3.0 * f) / TOTAL_FRAMES;
    const loopHarmonic2 = (2.0 * Math.PI * 7.0 * f) / TOTAL_FRAMES;
    const breathAmp = shot.id === 'S4A_PUSHUP' ? 6.5 : 0.20;
    camPos.x += Math.sin(loopHarmonic1) * breathAmp;
    camPos.y += Math.sin(loopHarmonic2) * breathAmp * 0.75;

    camera.fov = fov;
    camera.position.copy(camPos);
    upVec.set(Math.sin(camRoll), Math.cos(camRoll), 0).normalize();
    camera.up.copy(upVec);
    camera.lookAt(lookAt);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld(true);

    const isHardCut = (
      f === 76 || f === 161 || f === 316 || f === 425 ||
      f === 490 || f === 611 || f === 726 || f === 912 ||
      f === 995 || f === 1031 || lastFrameRendered !== f - 1
    );
    if (isHardCut) {
      motionVec.set(explicitMotionX, explicitMotionY);
    } else {
      const dLook = lookAt.distanceTo(prevLookAt);
      const dCam = camPos.distanceTo(prevCamPos);
      const autoBlur = GLM.clamp((dCam + dLook) / Math.max(20.0, focusDist) * 0.055, 0.0, 0.016);
      const dxSign = Math.sign((lookAt.x - prevLookAt.x) + (camPos.x - prevCamPos.x)) || 1.0;
      motionVec.set(
        GLM.clamp(explicitMotionX + dxSign * autoBlur * 0.65, -0.026, 0.026),
        GLM.clamp(explicitMotionY, -0.018, 0.018)
      );
    }
    prevCamPos.copy(camPos);
    prevLookAt.copy(lookAt);
    lastFrameRendered = f;

    world.updateShadowMap(shadowFocus, shadowHalf);

    return {
      frame: f,
      time,
      shot,
      u,
      telemetryMetric,
      postParams: {
        focusDist,
        dofRange,
        maxBlur,
        bloomAmt,
        exposure,
        time,
        motionVec,
      },
    };
  }

  return { evaluateFrame };
}
