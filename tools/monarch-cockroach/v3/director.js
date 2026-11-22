import * as THREE from 'three';
import { GLM } from './cockroach3d.js';

/**
 * Parse tools/monarch-cockroach/feature/feature.plan into structured shot records.
 */
export function parseFeaturePlan(planText) {
  const shots = [];
  for (const raw of planText.split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const parts = line.split(/\s+/);
    shots.push({
      first: Number(parts[0]),
      end: Number(parts[1]),
      mode: Number(parts[2]),
      camId: Number(parts[3]),
      srcA: Number(parts[4]),
      srcB: Number(parts[5]),
      subject: parts[6],
    });
  }
  return shots;
}

export function findShot(shots, frame) {
  for (let i = 0; i < shots.length; i++) {
    const s = shots[i];
    if (frame >= s.first && frame < s.end) return s;
  }
  return shots[shots.length - 1];
}

/**
 * Direct the 3D scene, actors, lighting, camera, and optical focus for exact frame `frame` (0..10460).
 */
export function directFrame(world, camera, shots, frame) {
  const shot = findShot(shots, frame);
  const u = GLM.clamp((frame - shot.first) / Math.max(1, shot.end - shot.first), 0, 1);
  const uSmooth = GLM.smoothstep(0, 1, u);
  const srcT = GLM.mix(shot.srcA, shot.srcB, u);
  const filmSec = frame / 30.0;
  const { mode, camId } = shot;

  // Determine active stage
  const isThreshold = (mode >= 10 && mode <= 15) || (mode >= 70 && mode <= 74);
  const isCutaway = (mode === 23 || mode === 64);
  const isComparison = (mode === 32 || mode === 34 || mode === 52 || mode === 54);
  const isCorridor = !isThreshold && !isCutaway && !isComparison;

  world.stages.thresholdStage.visible = isThreshold;
  world.stages.corridorStage.visible = isCorridor;
  world.stages.cutawayStage.visible = isCutaway;
  world.stages.comparisonStage.visible = isComparison;
  world.heroActor.root.visible = isThreshold || isCorridor;
  world.contactShadow.visible = isThreshold || isCorridor;

  // Drift atmospheric dust gently
  world.dustPoints.position.set(
    Math.sin(filmSec * 0.25) * 3.0,
    Math.cos(filmSec * 0.19) * 1.2,
    Math.sin(filmSec * 0.17) * 2.5
  );
  world.dustPoints.visible = !isCutaway && !isComparison;

  // Lighting mood tuning per stage
  if (isThreshold) {
    world.scene.background.set('#071013');
    world.lights.keyLight.color.set('#ffd298');
    world.lights.keyLight.intensity = 3.05;
    world.lights.rimLight.color.set('#70bac8');
    world.lights.rimLight.intensity = 1.65;
    world.lights.hemi.intensity = 0.92;
  } else if (isCutaway || isComparison) {
    world.scene.background.set('#061114');
    world.lights.keyLight.color.set('#ffe2be');
    world.lights.keyLight.intensity = 3.15;
    world.lights.rimLight.color.set('#6fd0d8');
    world.lights.rimLight.intensity = 1.90;
    world.lights.hemi.intensity = 1.05;
  } else {
    world.scene.background.set('#091619');
    world.lights.keyLight.color.set('#ffdbb0');
    world.lights.keyLight.intensity = 2.95;
    world.lights.rimLight.color.set('#80cbd4');
    world.lights.rimLight.intensity = 1.75;
    world.lights.hemi.intensity = 1.02;
  }

  // Default actor & camera state
  let ceilingMm = 12.52;
  let worldX = 0, worldZ = 0, yaw = 0, bodyPitch = 0;
  let phase = filmSec * 9.5;
  let strideAmp = 1.0;
  let antennaProbe = 0.0, headPitch = 0.0, pronotumRoll = 0.0;
  let gateVisible = false, roofVisible = false, penniesInLab = false;
  let doorGapMm = 3.20;

  let eye = new THREE.Vector3(-28, 16, 42);
  let target = new THREE.Vector3(0, 4.5, 0);
  let fov = 34;
  let aperture = 4.2;
  let exposure = 1.16;
  let focusOverride = null;

  // =========================================================================
  // CHAPTER 1: Under the Door (Modes 10..15)
  // =========================================================================
  if (mode === 10) {
    // Open walnut floor approach toward closed door at X = +18 mm
    ceilingMm = 12.52;
    if (camId === 101) {
      worldX = GLM.mix(-48, -22, u);
      phase = srcT * 11.0;
      eye.set(worldX + 26, 11.5, 34 - u * 4);
      target.set(worldX + 4, 4.8, 2);
      fov = 34;
    } else if (camId === 102) {
      worldX = GLM.mix(-22, -6, u);
      phase = srcT * 11.0;
      eye.set(worldX + 12, 7.2, 26);
      target.set(worldX + 2, 4.2, 0);
      fov = 32;
    } else {
      // 111 hold into Ch2
      worldX = -10 + u * 5;
      phase = srcT * 4.0;
      strideAmp = 0.35;
      eye.set(worldX + 22, 13.5, 36);
      target.set(8, 3.5, 6);
      fov = 34;
    }
  } else if (mode === 11) {
    // Two stacked copper pennies beside 3.2 mm doorway slot + antennae probing
    ceilingMm = 12.52;
    if (camId === 103) {
      worldX = GLM.mix(-14, -6.5, uSmooth);
      strideAmp = 0.45 * (1 - uSmooth);
      phase = srcT * 6.0;
      eye.set(-16 + u * 3, 12.8, 48 - u * 4);
      target.set(5.5, 2.8, 11.5);
      fov = 31;
      aperture = 4.2;
    } else {
      // 104 antennae reach & sweep threshold
      worldX = GLM.mix(-6.5, -2.2, uSmooth);
      strideAmp = 0.15;
      antennaProbe = GLM.smoothstep(0.15, 0.9, u);
      headPitch = -0.18 * antennaProbe;
      eye.set(-12.5, 9.4, 34.5);
      target.set(6.5, 2.8, 6.0);
      fov = 30;
      aperture = 4.6;
    }
  } else if (mode === 12) {
    // PROTECTED CLIMAX: Sub-second head dip, shell flatten, and exit under 3.2 mm door!
    if (camId === 105) {
      worldX = GLM.mix(-2.0, 19.5, uSmooth);
      const sq = GLM.smoothstep(0.08, 0.68, u);
      ceilingMm = GLM.mix(11.8, 3.20, sq);
      headPitch = -0.25 * Math.sin(Math.PI * u);
      phase = srcT * 14.0;
      eye.set(-16 + u * 6, 6.8 - u * 1.4, 29 - u * 3);
      target.set(GLM.mix(6, 16, u), 2.3, 1.5);
      fov = 31;
      aperture = 4.8;
    } else {
      // 106 reverse side of door: emerges into warm hallway light and rebounds!
      worldX = GLM.mix(20.0, 52.0, u);
      const reb = GLM.smoothstep(0.22, 0.78, u);
      ceilingMm = GLM.mix(3.20, 12.52, reb);
      phase = srcT * 14.5;
      eye.set(58 + u * 8, 9.5, 31);
      target.set(GLM.mix(26, 46, u), 3.6, 0);
      fov = 33;
    }
  } else if (mode === 13) {
    // Freeze / quiet macro drift on empty 3.2 mm doorway slot + two copper pennies
    world.heroActor.root.visible = false;
    world.contactShadow.visible = false;
    eye.set(-12 + u * 4, 5.4, 35 - u * 3);
    target.set(11.0, 2.0, 13.0);
    fov = 28;
    aperture = 5.8;
  } else if (mode === 14) {
    // Standing height (12.52 mm) vs 3.2 mm doorway clearance paradox
    worldX = -4.5;
    ceilingMm = camId === 108 ? 12.52 : GLM.mix(12.52, 4.2, uSmooth);
    strideAmp = 0.08;
    eye.set(-6.0, 6.8, 38.0 - u * 3);
    target.set(3.5, 3.8, 4.0);
    fov = 30;
  } else if (mode === 15) {
    // Rear-lateral tease on splayed hind leg losing foot stance
    worldX = -1.0;
    ceilingMm = GLM.mix(6.2, 3.6, uSmooth);
    strideAmp = 0.25;
    phase = srcT * 5.0;
    eye.set(-22.5, 5.2, 19.5);
    target.set(-6.5, 1.6, 8.5);
    fov = 26;
    aperture = 6.2;
  }

  // =========================================================================
  // CHAPTER 2: Five Moves Through the Slot (Modes 20..24)
  // =========================================================================
  else if (mode === 20) {
    gateVisible = true;
    penniesInLab = true;
    ceilingMm = 12.52;
    worldX = GLM.mix(-24, -13, uSmooth);
    phase = srcT * 8.0;
    strideAmp = 0.65;
    eye.set(-34 + u * 5, 16.5, 42 - u * 4);
    target.set(2.0, 4.5, 0);
    fov = 34;
  } else if (mode === 21) {
    // 500 FPS Five Separate Moves through the 3.2 mm clear acrylic gate (at X = +16 mm)
    gateVisible = true;
    penniesInLab = true;
    if (camId === 202) {
      // Move 1: Antennal sweep probe
      worldX = GLM.mix(-8.0, -3.5, uSmooth);
      ceilingMm = 12.2;
      strideAmp = 0.2;
      antennaProbe = 0.35 + 0.65 * Math.sin(u * Math.PI);
      eye.set(-12, 7.5, 30);
      target.set(8.5, 3.2, 0);
      fov = 28;
    } else if (camId === 203) {
      // Move 2: Head pitch down & wedge into 3.2 mm gate
      worldX = GLM.mix(-3.5, 3.2, uSmooth);
      ceilingMm = GLM.mix(11.8, 6.8, uSmooth);
      headPitch = -0.34 * uSmooth;
      strideAmp = 0.35;
      phase = srcT * 4.5;
      eye.set(-8, 6.0, 26);
      target.set(10.5, 2.6, 0);
      fov = 27;
    } else if (camId === 204) {
      // Move 3: Pronotum shield rolls slightly (~9 deg) to slip inside
      worldX = GLM.mix(3.2, 10.5, uSmooth);
      ceilingMm = GLM.mix(6.8, 3.6, uSmooth);
      pronotumRoll = 0.17 * Math.sin(u * Math.PI);
      strideAmp = 0.55;
      phase = srcT * 5.2;
      eye.set(0, 6.8, 25);
      target.set(12.5, 2.4, 0);
      fov = 27;
    } else if (camId === 205) {
      // Move 4: Planted external hind legs shove thickest chest section through
      worldX = GLM.mix(10.5, 19.5, uSmooth);
      ceilingMm = 3.25;
      strideAmp = 0.95;
      phase = srcT * 6.8;
      eye.set(-10 + u * 6, 7.2, 27);
      target.set(11.5, 2.0, 4.0);
      fov = 28;
    } else {
      // Move 5 (206): Flattened abdomen pulls clear on far side
      worldX = GLM.mix(19.5, 31.0, uSmooth);
      ceilingMm = GLM.mix(3.25, 5.8, GLM.smoothstep(0.55, 1.0, u));
      strideAmp = 0.85;
      phase = srcT * 7.5;
      eye.set(38, 8.5, 29);
      target.set(23.0, 2.5, 0);
      fov = 29;
    }
  } else if (mode === 22) {
    // Dorsal close-up on overlapping rigid tergite plates during squeeze
    roofVisible = true;
    ceilingMm = GLM.mix(6.4, 3.4, uSmooth);
    worldX = GLM.mix(-6, 6, u);
    strideAmp = 0.65;
    phase = srcT * 7.0;
    eye.set(worldX - 14, 15.5, 20.5);
    target.set(worldX - 2, 2.5, 0);
    fov = 27;
  } else if (mode === 23) {
    // STAGE C: Dark Studio 3D Sagittal Cutaway — Rigid Chitin Plates + Folding Arthrodial Hinges!
    const comp = camId === 208
      ? GLM.mix(0.05, 0.45, uSmooth)
      : GLM.mix(0.45, 0.96, uSmooth);
    const cutInfo = world.props.sagittalRig.update({ compAlpha: comp, showPlaten: true, showLoadArrows: false });
    eye.set(-8.5 + u * 3.5, 8.6, 25.5 - u * 1.8);
    target.set(-1.5, 2.9, -2.0);
    fov = 29;
    aperture = 3.0;
    focusOverride = eye.distanceTo(target);
    return finalizeCamera(world, camera, eye, target, fov, focusOverride, aperture, exposure, filmSec, mode, cutInfo.landmarks);
  } else if (mode === 24) {
    // Viscoelastic hinge rebound back to standing height upon gate exit
    gateVisible = true;
    worldX = GLM.mix(21.0, 42.0, u);
    ceilingMm = camId === 210 ? 3.5 : GLM.mix(3.6, 12.52, uSmooth);
    phase = srcT * 10.0;
    eye.set(44, 10.5, 32);
    target.set(worldX, 3.8, 0);
    fov = 31;
  }

  // =========================================================================
  // CHAPTER 3: The Low-Ceiling Surprise (Modes 30..35)
  // =========================================================================
  else if (mode === 30) {
    // 15 cm confined corridor reveal
    roofVisible = true;
    ceilingMm = 12.0;
    worldX = GLM.mix(-52, -18, u);
    phase = srcT * 11.0;
    eye.set(-58 + u * 14, 20.0, 52 - u * 6);
    target.set(-12 + u * 10, 5.0, 0);
    fov = 35;
  } else if (mode === 31) {
    // 12 mm -> 9 mm -> 6 mm lateral tracking run at full ~58 cm/s!
    roofVisible = true;
    ceilingMm = camId === 302 ? 12.0 : camId === 303 ? GLM.mix(12.0, 9.0, uSmooth) : GLM.mix(9.0, 6.0, uSmooth);
    worldX = GLM.mix(-42, 38, u);
    phase = srcT * 15.5;
    eye.set(worldX + 8, 7.8, 35);
    target.set(worldX + 2, 3.4, 0);
    fov = 30;
  } else if (mode === 32 || mode === 34) {
    // STAGE D: 3-Lane Synchronized Speed Comparison (12 mm vs 6 mm vs 4 mm 4x cliff!)
    const heights = [12.0, 6.0, 4.0];
    const speeds = [58.05, 57.90, 14.52];
    const landmarks = {};
    for (let i = 0; i < 3; i++) {
      const lane = world.props.compLanes[i];
      lane.roof.position.y = heights[i] + 0.4;
      const dist = -44 + (speeds[i] / 58.05) * 84 * u;
      const st = lane.runner.update({
        ceilingMm: heights[i],
        worldX: dist,
        worldZ: 0,
        phase: srcT * (i === 2 ? 7.2 : 16.2),
        gaitMode: i === 2 ? 'oar' : 'tripod',
        time: filmSec,
      });
      if (i === 2) Object.assign(landmarks, st.landmarks);
    }
    eye.set(-6 + u * 6, 48.0, 72.0);
    target.set(-2.0, 2.0, 0.0);
    fov = 37;
    aperture = 2.4;
    focusOverride = eye.distanceTo(target);
    return finalizeCamera(world, camera, eye, target, fov, focusOverride, aperture, exposure, filmSec, mode, landmarks);
  } else if (mode === 33) {
    // High overhead dorsal tracking shot: legs splay 55 -> 75 deg while foot track stays 11.9 mm!
    roofVisible = true;
    ceilingMm = camId === 306 ? GLM.mix(12.0, 6.2, uSmooth) : 6.2;
    worldX = GLM.mix(-30, 30, u);
    phase = srcT * 14.5;
    eye.set(worldX - 3, 39.0, 6.0);
    target.set(worldX + 1, 2.0, 0.0);
    fov = 32;
    aperture = 2.8;
  } else if (mode === 35) {
    // 4 mm squeeze — alternating tripod breaks apart into synchronous oar shoves
    roofVisible = true;
    ceilingMm = 4.0;
    worldX = GLM.mix(-18, 18, u);
    phase = srcT * 7.8;
    eye.set(worldX + 14, 9.5, 28.0);
    target.set(worldX, 2.0, 0.0);
    fov = 29;
  }

  // =========================================================================
  // CHAPTER 4: When Shins Become Feet — Extreme Macro on Right Hind Leg (Modes 40..45)
  // =========================================================================
  else if (mode === 40) {
    roofVisible = true;
    ceilingMm = camId === 401 ? 12.0 : 4.0;
    worldX = GLM.mix(-10, 10, u);
    phase = srcT * 6.5;
    eye.set(worldX - 24, 6.8, 20.0);
    target.set(worldX - 6, 2.2, 8.5);
    fov = 27;
    aperture = 5.8;
  } else if (mode === 41) {
    // 12 mm upright tarsal-claw & soft pad stance macro
    roofVisible = true;
    ceilingMm = 12.0;
    worldX = GLM.mix(-8, 8, u);
    phase = srcT * 4.2; // slow-motion stride so every tarsomere & claw hook is crystal clear!
    eye.set(worldX - (camId === 403 ? 13.5 : 18.5), camId === 403 ? 3.8 : 5.4, camId === 403 ? 21.5 : 24.5);
    target.set(worldX - 8.5, 1.2, 11.2);
    fov = camId === 403 ? 22 : 25;
    aperture = 6.4;
  } else if (mode === 42) {
    // Roof presses 12 mm -> 4 mm: sprawl past 80 deg, foot claws tip sideways (+0.48 mm clear)!
    roofVisible = true;
    ceilingMm = camId === 404 ? GLM.mix(11.5, 4.0, uSmooth) : 4.0;
    worldX = GLM.mix(-6, 6, u);
    phase = srcT * 3.8;
    strideAmp = 0.55;
    eye.set(worldX - 16.5, 4.2, 22.0);
    target.set(worldX - 8.0, 1.3, 11.5);
    fov = 23;
    aperture = 6.2;
  } else if (mode === 43) {
    // PROTECTED CLIMAX (406 & 407) + Clean Picture Hold (412):
    // Uninterrupted extreme 85mm macro on backward-angled tibial spines planting at Y=0.00 mm & driving!
    roofVisible = true;
    ceilingMm = 4.0;
    worldX = GLM.mix(-8, 12, u);
    phase = srcT * 4.4;
    strideAmp = 0.95;
    eye.set(worldX - 13.5, 3.15, 20.8);
    target.set(worldX - 8.2, 0.95, 11.2);
    fov = 20.5;
    aperture = 6.8;
  } else if (mode === 44) {
    // Overhead view of synchronous middle legs (L2 & R2) shoving together like oars!
    roofVisible = true;
    ceilingMm = 4.0;
    worldX = GLM.mix(-14, 16, u);
    phase = srcT * 6.8;
    eye.set(worldX - 2, 32.5, 5.5);
    target.set(worldX, 1.8, 0.0);
    fov = 30;
    aperture = 3.0;
  } else if (mode === 45) {
    // Grazing side-ventral macro inside 4 mm tunnel: roof rub + belly rub + 5x BW spine thrust!
    roofVisible = true;
    ceilingMm = 4.0;
    worldX = GLM.mix(-12, 14, u);
    phase = srcT * 6.2;
    eye.set(worldX - 4, 2.35, 24.5);
    target.set(worldX - 1, 1.85, 4.0);
    fov = 25;
    aperture = 5.5;
  }

  // =========================================================================
  // CHAPTER 5: The Rough-Floor Trap (Modes 50..55)
  // =========================================================================
  else if (mode === 50 || mode === 51) {
    roofVisible = true;
    ceilingMm = 4.0;
    worldX = GLM.mix(-10, 12, u);
    phase = srcT * 5.2;
    eye.set(worldX - 15.0, 4.5, 23.0);
    target.set(worldX - 6.5, 1.2, 9.5);
    fov = mode === 51 ? 22 : 28;
    aperture = 5.6;
  } else if (mode === 52 || mode === 54) {
    // STAGE D: 638-Trial 4 mm Floor Grit Matrix (Slick 100-grit vs Medium 40-grit WINNER vs Coarse 20-grit belly snag)
    const speeds = [1.57, 5.26, 3.69]; // exact PNAS Table S2 / Fig. 3 speeds!
    const landmarks = {};
    for (let i = 0; i < 3; i++) {
      const lane = world.props.compLanes[i];
      lane.roof.position.y = 4.0 + 0.4;
      const dist = -36 + (speeds[i] / 5.26) * 68 * u;
      // Add slight lateral slip wobble on Slick lane 0!
      const slipZ = i === 0 ? Math.sin(srcT * 14.0) * 1.1 : 0.0;
      const st = lane.runner.update({
        ceilingMm: 4.0,
        worldX: dist,
        worldZ: slipZ,
        yaw: i === 0 ? Math.sin(srcT * 14.0) * 0.08 : 0.0,
        phase: srcT * (i === 0 ? 11.5 : i === 1 ? 8.0 : 5.8),
        gaitMode: 'oar',
        time: filmSec,
      });
      if (i === 1) Object.assign(landmarks, st.landmarks);
    }
    eye.set(-8 + u * 8, 48.0, 72.0);
    target.set(-2.0, 2.0, 0.0);
    fov = 37;
    aperture = 2.4;
    focusOverride = eye.distanceTo(target);
    return finalizeCamera(world, camera, eye, target, fov, focusOverride, aperture, exposure, filmSec, mode, landmarks);
  } else if (mode === 53) {
    // Ceiling roughness comparison inside 4 mm channel
    roofVisible = true;
    ceilingMm = 4.0;
    worldX = GLM.mix(-14, 10, u);
    phase = srcT * 6.0;
    eye.set(worldX + 10, 5.8, 26.5);
    target.set(worldX, 2.4, 0.0);
    fov = 27;
  } else if (mode === 55) {
    // 508: Slick floor spine slip vs 509: Coarse 20-grit belly snag
    roofVisible = true;
    ceilingMm = 4.0;
    if (camId === 508) {
      worldX = GLM.mix(-6, 2, u);
      worldZ = Math.sin(srcT * 16.0) * 1.2;
      yaw = Math.sin(srcT * 16.0) * 0.09;
      phase = srcT * 12.0;
    } else {
      worldX = GLM.mix(-6, 5, u);
      phase = srcT * 5.2;
    }
    eye.set(worldX - 14, 3.6, 22.5);
    target.set(worldX - 4, 1.2, 6.5);
    fov = 24;
  }

  // =========================================================================
  // CHAPTER 6: Tough Shell, Tight Limit (Modes 60..65)
  // =========================================================================
  else if (mode === 64) {
    // STAGE C: ~300x to ~900x Body-Weight Distributed Compression across ~3 cm2 Hinged Plates!
    const comp = camId === 601
      ? 0.35 + 0.58 * Math.sin(u * Math.PI * 0.85)
      : 0.82 + 0.10 * Math.sin(srcT * 5.0);
    const cutInfo = world.props.sagittalRig.update({ compAlpha: comp, showPlaten: true, showLoadArrows: true });
    eye.set(-6.5 + u * 4.5, 9.2, 27.5 - u * 2.0);
    target.set(-1.5, 3.1, -2.0);
    fov = 30;
    aperture = 3.0;
    focusOverride = eye.distanceTo(target);
    return finalizeCamera(world, camera, eye, target, fov, focusOverride, aperture, exposure, filmSec, mode, cutInfo.landmarks);
  } else if (mode === 65) {
    // Post-compression unimpaired 76.7 cm/s open-floor sprint!
    ceilingMm = 12.52;
    worldX = GLM.mix(-48, 48, u);
    phase = srcT * 18.0;
    eye.set(worldX + 18, 12.5, 36.0);
    target.set(worldX + 3, 4.5, 0.0);
    fov = 33;
  } else if (mode === 60 || mode === 61) {
    // Narrowing gate: 72% pass at 6.1/4.4 mm -> 17% pass at 3.2 mm beside two pennies!
    gateVisible = true;
    penniesInLab = true;
    const gateGap = (camId === 605) ? 5.2 : 3.20;
    doorGapMm = gateGap;
    if (camId === 605) {
      worldX = GLM.mix(-12, 32, u);
      ceilingMm = GLM.mix(11.5, 5.2, GLM.smoothstep(0.15, 0.48, u) * (1 - GLM.smoothstep(0.72, 0.98, u)));
      phase = srcT * 12.0;
    } else {
      worldX = GLM.mix(-16, -2, uSmooth);
      ceilingMm = 12.0;
      strideAmp = 0.45 * (1 - uSmooth);
      antennaProbe = uSmooth * 0.8;
      phase = srcT * 7.0;
    }
    eye.set(-22 + u * 6, 9.5, 35 - u * 3);
    target.set(11.0, 3.0, 5.0);
    fov = 31;
  } else if (mode === 62) {
    // 607: 74% antennal check & turn-back | 608: 9% thorax-wedged at thickest chest section!
    gateVisible = true;
    penniesInLab = true;
    doorGapMm = 3.15;
    if (camId === 607) {
      // Approaches, probes with antennae, then turns away cleanly
      const turnU = GLM.smoothstep(0.42, 0.92, u);
      worldX = GLM.mix(-6.5, -2.2, GLM.smoothstep(0, 0.42, u)) - turnU * 14.0;
      worldZ = -turnU * 8.5;
      yaw = turnU * 2.35;
      antennaProbe = (1 - turnU) * 0.95;
      ceilingMm = 12.0;
      phase = srcT * 8.5;
      eye.set(-20, 11.5, 34);
      target.set(2.0, 3.2, 0.0);
      fov = 31;
    } else {
      // 608: Head & anterior pronotum enter 3.15 mm gate, thickest pro/mesothorax wedges fast!
      worldX = GLM.mix(2.5, 9.2, GLM.smoothstep(0, 0.45, u)) + 0.18 * Math.sin(srcT * 18.0) * (u > 0.45 ? 1 : 0);
      ceilingMm = 3.25;
      strideAmp = 0.85;
      phase = srcT * 11.0; // hind legs push vigorously while thorax is held fast!
      eye.set(-8.5, 6.4, 25.5);
      target.set(10.5, 2.2, 2.0);
      fov = 27;
      aperture = 5.6;
    }
  } else if (mode === 63) {
    // 315 Lab Gate Attempts 3-Outcome Ledger over moody acrylic gate + penny stack
    gateVisible = true;
    penniesInLab = true;
    worldX = -9.0;
    ceilingMm = 12.2;
    strideAmp = 0.08;
    antennaProbe = 0.5;
    eye.set(-24 + u * 4, 13.5, 42);
    target.set(6.0, 1.5, 6.0);
    fov = 34;
  }

  // =========================================================================
  // CHAPTER 7: Hinges and Spines — Real-Speed Reprise & Quiet Hold (Modes 70..74)
  // =========================================================================
  else if (mode === 70) {
    // Real-speed 1x approach & sub-second doorway squeeze beside the two copper pennies!
    if (camId === 701) {
      worldX = GLM.mix(-38, -2.5, u);
      ceilingMm = 12.52;
      phase = srcT * 13.5;
      eye.set(-24 + u * 8, 8.8, 36 - u * 4);
      target.set(GLM.mix(-8, 10, u), 3.2, 6.0);
      fov = 32;
    } else {
      // 702 Protected Climax: 1x real-speed fold & shin drive under door!
      worldX = GLM.mix(-2.5, 24.0, uSmooth);
      ceilingMm = GLM.mix(12.0, 3.20, GLM.smoothstep(0.05, 0.55, u));
      phase = srcT * 15.0;
      eye.set(-14 + u * 8, 6.4, 29);
      target.set(12.0, 2.2, 4.0);
      fov = 30;
    }
  } else if (mode === 71) {
    // Far-side viscoelastic hinge rebound back to 12.52 mm + tarsal claws retake open floor!
    if (camId === 703) {
      worldX = GLM.mix(22.0, 44.0, u);
      ceilingMm = GLM.mix(3.20, 12.52, GLM.smoothstep(0.10, 0.72, u));
      phase = srcT * 14.0;
      eye.set(52, 8.2, 28);
      target.set(GLM.mix(26, 40, u), 3.6, 0.0);
      fov = 30;
    } else {
      worldX = GLM.mix(44.0, 82.0, u);
      ceilingMm = 12.52;
      phase = srcT * 15.5;
      eye.set(worldX - 22, 10.5, 32);
      target.set(worldX + 2, 4.2, 0.0);
      fov = 32;
    }
  } else if (mode === 72) {
    // Hero 3/4 portrait: Shells that fold · Shins that walk
    worldX = GLM.mix(-12, 6, u);
    ceilingMm = 12.52;
    phase = srcT * 10.0;
    eye.set(worldX + 20, 9.2, 28.0);
    target.set(worldX, 4.0, 0.0);
    fov = 29;
    aperture = 5.4;
  } else if (mode === 73 || mode === 74) {
    // 706: Cockroach clears frame -> 707: 8-second closing quiet hold on two-penny gap -> 708: Credits
    if (camId === 706) {
      worldX = GLM.mix(24.0, 95.0, u);
      ceilingMm = 12.52;
      phase = srcT * 15.0;
    } else {
      world.heroActor.root.visible = false;
      world.contactShadow.visible = false;
    }
    eye.set(-14 + u * 3.5, 5.8, 36.0 - u * 2.5);
    target.set(10.5, 2.1, 12.0);
    fov = 29;
    aperture = 5.4;
  }

  // Update Door / Corridor props
  world.props.doorSlab.position.set(18.0, 32.5 + doorGapMm, 0);
  world.props.acrylicRoof.visible = roofVisible;
  world.props.acrylicRoof.position.set(0, ceilingMm + 0.55, 0);
  world.props.gateAssembly.visible = gateVisible;
  world.props.gateAssembly.position.set(16.0, doorGapMm, 0);
  world.props.scalePost.visible = roofVisible || gateVisible;
  world.props.labPennyStack.visible = penniesInLab;

  // Update Hero Cockroach Actor
  let landmarks = {};
  if (world.heroActor.root.visible) {
    const actorInfo = world.heroActor.update({
      ceilingMm,
      worldX,
      worldZ,
      yaw,
      bodyPitch,
      phase,
      strideAmp,
      antennaProbe,
      headPitch,
      pronotumRoll,
      time: filmSec,
      floorY: 0.0,
    });
    landmarks = actorInfo.landmarks;
    // Dynamically lock Ch4/Ch5 extreme macro camera & target directly onto the live R3 distal tibia + tarsus/claw!
    if ((mode >= 41 && mode <= 43 || mode === 51) && landmarks.r3Spine && landmarks.r3Claw) {
      target.copy(landmarks.r3Spine).lerp(landmarks.r3Claw, mode === 41 ? 0.55 : 0.36);
      target.y = Math.max(1.0, target.y);
      if (mode === 41) {
        eye.copy(target).add(new THREE.Vector3(-9.2, 5.2, 17.5));
      } else if (mode === 42) {
        eye.copy(target).add(new THREE.Vector3(-8.4, 4.4, 16.0));
      } else {
        eye.copy(target).add(new THREE.Vector3(-7.2, 3.2, 14.2));
      }
    }
    world.contactShadow.position.set(worldX - 2.0 * Math.cos(yaw), 0.025, worldZ + 2.0 * Math.sin(yaw));
    world.contactShadow.rotation.z = -yaw;
    const flatScale = 1.0 + 0.22 * actorInfo.compAlpha;
    world.contactShadow.scale.set(1.05, flatScale, 1.0);
    world.contactShadow.material.opacity = 0.68 - 0.18 * (actorInfo.ventralClearance / 3.8);
  }
  landmarks.pennies = isThreshold
    ? new THREE.Vector3(8.5, 2.2, 21.5)
    : new THREE.Vector3(16.0, 2.2, 17.5);

  // Move key light shadow frustum with subject so 1024x1024 shadow map stays razor-sharp!
  world.lights.keyLight.position.set(target.x + 28, 62, target.z + 34);
  world.lights.keyLight.target.position.copy(target);
  world.lights.keyLight.target.updateMatrixWorld();
  world.lights.macroFill.position.set(target.x - 10, 12, target.z + 22);

  // Compute exact focal plane distance (locked onto hind spine/claw in Ch4/Ch5, pennies in 103, or camera target!)
  let focusPt = target;
  if (mode >= 41 && mode <= 43 && landmarks.r3Spine) focusPt = landmarks.r3Spine;
  else if (camId === 103 && landmarks.pennies) focusPt = landmarks.pennies;
  else if (landmarks.pronotum && world.heroActor.root.visible) focusPt = landmarks.pronotum;
  const focusDist = focusOverride ?? eye.distanceTo(focusPt);

  return finalizeCamera(world, camera, eye, target, fov, focusDist, aperture, exposure, filmSec, mode, landmarks);
}

function finalizeCamera(world, camera, eye, target, fov, focusDist, aperture, exposure, filmSec, mode, landmarks) {
  camera.fov = fov;
  camera.position.copy(eye);
  camera.lookAt(target);
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);
  return {
    mode,
    landmarks,
    lensParams: {
      focus: focusDist,
      aperture,
      exposure,
      bloom: 0.26,
      vignette: 0.32,
      time: filmSec,
    },
  };
}
