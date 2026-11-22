import * as THREE from 'three';
import { GLM } from './cockroach3d_v4.js';

/**
 * Monarch Cam #03 — V4 Cinema Master Director (10,302 frames = 343.40s @ 30 fps)
 * Frame-locked to fresh Arena voice-02 narration (voice-lock-v4.json).
 * Zero static holds: every shot features continuous damped camera choreography,
 * dynamic human/insect kinematics, real-time shadow focus tracking, and optical rack focus!
 */
const FPS = 30.0;

function uIn(f, a, b) {
  return GLM.clamp((f - a) / Math.max(1.0, b - a), 0.0, 1.0);
}
function sIn(f, a, b) {
  return GLM.smoothstep(a, b, f);
}

const tmpM = new THREE.Matrix4();
const tmpQ = new THREE.Quaternion();
const tmpS = new THREE.Vector3();
const tmpP = new THREE.Vector3();

function updateDustBurst(dustMesh, origin, time, intensity = 0.0) {
  if (intensity <= 0.01) {
    dustMesh.visible = false;
    return;
  }
  dustMesh.visible = true;
  for (let i = 0; i < 48; i++) {
    const seed = i * 1.6180339;
    const cyc = ((time * 4.2 + seed) % 1.0);
    const spreadZ = Math.sin(seed * 13.7) * 1.8;
    const backX = -cyc * (4.5 + (i % 5) * 1.1);
    const arcY = Math.sin(Math.PI * cyc) * (0.42 + (i % 4) * 0.16);
    tmpP.set(origin.x + backX, Math.max(0.03, origin.y + arcY), origin.z + spreadZ);
    const sc = (1.0 - cyc) * (0.55 + 0.45 * Math.sin(seed * 7.1)) * intensity;
    tmpS.set(sc, sc, sc);
    tmpQ.setFromEuler(new THREE.Euler(time * 8 + i, time * 6, i));
    tmpM.compose(tmpP, tmpQ, tmpS);
    dustMesh.setMatrixAt(i, tmpM);
  }
  dustMesh.instanceMatrix.needsUpdate = true;
}

export function directFrameV4(world, camera, frame) {
  const t = frame / FPS;

  // Reset per-frame visibility defaults cleanly
  world.apartmentSet.visible   = false;
  world.labSet.visible         = false;
  world.pushupSet.visible      = false;
  world.roachHero.root.visible = false;
  world.roachB.root.visible    = false;
  world.roachC.root.visible    = false;
  world.xrayRig.group.visible  = false;
  world.corridorGroup.visible  = true;
  world.labGateGroup.visible   = false;
  world.multiLaneGroup.visible = false;
  world.dustParticles.visible  = false;

  const camPos = new THREE.Vector3(0, 20, 60);
  const camLook = new THREE.Vector3(0, 5, 0);
  let fov = 34;
  let shadowCenter = new THREE.Vector3(0, 4, 0);
  let shadowSpan = 65.0;
  let dofRange = 45.0;
  let maxBlur = 2.6;
  let mode = 'cinema';
  let landmarks = {};
  let metrics = null;

  // Helper to place pennies landmark
  const penniesWorld = new THREE.Vector3(-22.0, 2.4, -16.5);

  // =========================================================================
  // CHAPTER 1 [0..1080]: UNDER THE DOOR (Midnight Apartment -> Switch -> Vanish)
  // =========================================================================
  if (frame < 1080) {
    world.apartmentSet.visible = true;
    world.roachHero.root.visible = true;
    world.penniesGroup.visible = frame >= 220;

    if (frame < 42) {
      // [0..42] Moody 2:14 AM midnight hallway; homeowner reaches right hand to wall switch!
      world.setLightingMood('apartment_dark', 1.0);
      world.switchToggle.rotation.z = 0.42;
      const reach = sIn(frame, 4, 41);
      world.humanActors.poseHomeowner(t, reach, 0.0);

      const u = uIn(frame, 0, 42);
      fov = GLM.mix(46, 42, u);
      camPos.set(GLM.mix(-1540, -1380, u), GLM.mix(1440, 1390, u), GLM.mix(-40, -110, u));
      camLook.set(GLM.mix(-310, -240, u), GLM.mix(1310, 1280, u), GLM.mix(-600, -575, u));
      shadowCenter.set(-380, 1180, -620);
      shadowSpan = 760.0;
      dofRange = 1100.0;
      maxBlur = 1.8;

      const r = world.roachHero.update({ ceilingMm: 12.52, worldX: -240, worldZ: 0, phase: 0, strideAmp: 0, time: t });
      landmarks = { ...r.landmarks, pennies: penniesWorld };
    }
    else if (frame < 172) {
      // [42..172] SNAP! Light switch flips UP -> warm 3000K kitchen light floods room -> WHIP-BOOM DIVE locked onto sprinting cockroach!
      const flash = sIn(frame, 42, 50);
      world.setLightingMood('apartment_lit', flash);
      world.switchToggle.rotation.z = GLM.mix(0.42, -0.42, sIn(frame, 41, 45));

      const lookDown = sIn(frame, 48, 86);
      const releaseReach = 1.0 - 0.55 * sIn(frame, 55, 105);
      world.humanActors.poseHomeowner(t, releaseReach, lookDown);

      const sprintU = sIn(frame, 48, 172);
      const rx = GLM.mix(-245, -72, sprintU);
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: 0,
        phase: (t - 1.4) * 16.2, strideAmp: 1.0, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      // Snap gaze onto the floor cockroach rapidly (f 46..72) while camera booms down smoothly (f 48..128)!
      const lookSnap = sIn(frame, 46, 72);
      const dive = sIn(frame, 48, 128);
      fov = GLM.mix(42, 34, dive);
      camPos.set(
        GLM.mix(-1380, rx - 58, dive),
        GLM.mix(1390, 22.0, Math.pow(dive, 0.72)),
        GLM.mix(-110, 62.0, dive)
      );
      camLook.set(
        GLM.mix(-240, rx + 6, lookSnap),
        GLM.mix(1280, 6.5, lookSnap),
        GLM.mix(-575, 0.0, lookSnap)
      );
      shadowCenter.set(rx, 6, 0);
      shadowSpan = GLM.mix(320.0, 72.0, dive);
      dofRange = GLM.mix(650.0, 48.0, dive);
      maxBlur = 2.6;
    }
    else if (frame < 251) {
      // [172..251] "Standing up, it's half an inch tall." — Heroic low-angle profile macro!
      world.setLightingMood('apartment_lit', 1.0);
      world.switchToggle.rotation.z = -0.42;
      world.humanActors.poseHomeowner(t, 0.35, 1.0);

      const u = sIn(frame, 172, 251);
      const rx = GLM.mix(-72, -52, u);
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: 0,
        phase: t * 3.2, strideAmp: 0.25, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      fov = 30;
      camPos.set(rx - 18 + u * 8, 10.5, 58.0);
      camLook.set(rx + 2, 6.2, 0);
      shadowCenter.set(rx, 5, 0);
      shadowSpan = 55.0;
      dofRange = 36.0;
    }
    else if (frame < 376) {
      // [251..376] "That gap ahead is barely as thick as two stacked pennies." — Rack focus onto embossed copper Lincoln pennies!
      world.setLightingMood('apartment_lit', 1.0);
      world.humanActors.poseHomeowner(t, 0.3, 1.0);
      const u = sIn(frame, 251, 376);
      const rx = GLM.mix(-52, -40, u);
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: 0,
        phase: t * 4.5, strideAmp: 0.35, antennaProbe: 0.45 * u, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      fov = 28;
      camPos.set(GLM.mix(-54, -50, u), GLM.mix(12.5, 9.5, u), GLM.mix(48, 28, u));
      camLook.set(GLM.mix(-20, -18, u), GLM.mix(4.2, 2.8, u), GLM.mix(-6, -12, u));
      shadowCenter.set(-18, 3, -10);
      shadowSpan = 48.0;
      dofRange = 36.0;
    }
    else if (frame < 596) {
      // [376..596] PROTECTED CLIMAX #1: Sub-second vanish under the closed oak door! (ZERO text overlays!)
      world.setLightingMood('apartment_lit', 1.0);
      world.humanActors.poseHomeowner(t, 0.25, 1.0);

      // Approach [-40 -> -10] during [376..430], explosive sub-second squeeze through X=0..44 during [430..495], vanish into hallway [495..596]!
      let rx, ceil, hPitch = 0, pRoll = 0, probe = 0;
      if (frame < 430) {
        const u = uIn(frame, 376, 430);
        rx = GLM.mix(-40, -11, u);
        ceil = 12.52;
        probe = sIn(frame, 400, 430);
      } else if (frame < 498) {
        const u = sIn(frame, 430, 498);
        rx = GLM.mix(-11, 66, u);
        // Smooth envelope compressing down to 3.2 mm under door X=[0..44]!
        const inSlot = GLM.smoothstep(-12, 2, rx) * (1.0 - GLM.smoothstep(42, 60, rx));
        ceil = GLM.mix(12.52, 3.22, inSlot);
        hPitch = -0.22 * GLM.smoothstep(-12, 0, rx) * (1 - GLM.smoothstep(6, 18, rx));
        pRoll = 0.16 * Math.sin(inSlot * Math.PI);
        probe = 1.0 - inSlot;
      } else {
        const u = uIn(frame, 498, 596);
        rx = 66 + u * 120;
        ceil = 12.52;
      }
      const r = world.roachHero.update({
        ceilingMm: ceil, worldX: rx, worldZ: 0,
        phase: t * 17.5, strideAmp: 1.0, antennaProbe: probe, headPitch: hPitch, pronotumRoll: pRoll, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      const camU = sIn(frame, 376, 560);
      fov = 31;
      camPos.set(GLM.mix(-54, -26, camU), GLM.mix(8.2, 5.2, camU), GLM.mix(48, 28, camU));
      camLook.set(GLM.mix(-8, 12, camU), GLM.mix(3.6, 2.2, camU), GLM.mix(4, 2, camU));
      shadowCenter.set(0, 3, 4);
      shadowSpan = 52.0;
      dofRange = 38.0;
    }
    else {
      // [596..1080] "Wait a second... An insect's shell is supposed to be stiff armor. Squashed that flat, its feet can't even stand underneath it."
      // Bullet-time paradox orbit right at the 3.2 mm door threshold!
      world.setLightingMood('apartment_lit', 1.0);
      const u = sIn(frame, 596, 1080);
      const squeezeU = sIn(frame, 596, 760);
      const rx = GLM.mix(-4.0, 5.5, squeezeU);
      const ceil = GLM.mix(6.2, 3.28, squeezeU);
      const r = world.roachHero.update({
        ceilingMm: ceil, worldX: rx, worldZ: 0,
        phase: 0.25 + t * 0.65, strideAmp: 0.35, headPitch: -0.14, pronotumRoll: 0.10, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      fov = 27;
      const ang = GLM.mix(0.95, 1.38, u);
      const dist = GLM.mix(48, 36, u);
      camPos.set(rx - Math.cos(ang) * dist, GLM.mix(9.5, 5.4, u), Math.sin(ang) * dist);
      camLook.set(rx - 3.0, GLM.mix(3.8, 2.1, u), 3.5 * u);
      shadowCenter.set(rx, 3, 0);
      shadowSpan = 45.0;
      dofRange = 30.0;
    }
  }

  // =========================================================================
  // CHAPTER 2 [1080..2586]: FIVE MOVES THROUGH THE SLOT + 3D X-RAY CUTAWAY
  // =========================================================================
  else if (frame < 2586) {
    world.labSet.visible = true;
    world.setLightingMood('lab', 1.0);

    if (frame < 1391) {
      // [1080..1391] Establish UC Berkeley Biomechanics Lab: Researcher in lab coat + Phantom 500 FPS camera + optical bench!
      world.roachHero.root.visible = true;
      world.labGateGroup.visible = true;
      world.ceilingSlab.visible = false;
      world.micrometerBridge.visible = false;
      world.labGateGroup.position.set(0, 3.2, 0);

      world.humanActors.poseResearcher(t, 0.65, 0.55);
      const u = sIn(frame, 1080, 1391);
      const rx = GLM.mix(-58, -18, u);
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: 0,
        phase: t * 4.2, strideAmp: 0.85, antennaProbe: sIn(frame, 1300, 1391) * 0.5, time: t,
      });
      landmarks = r.landmarks;

      // Smooth cinema push from medium lab shot (showing Researcher, Phantom 500fps cam & dual monitors!) down to optical gate!
      fov = GLM.mix(38, 30, u);
      camPos.set(GLM.mix(-165, -56, u), GLM.mix(135, 18, Math.pow(u, 0.75)), GLM.mix(295, 68, u));
      camLook.set(GLM.mix(-15, -10, u), GLM.mix(58, 6.5, Math.pow(u, 0.75)), GLM.mix(-95, -8, u));
      shadowCenter.set(-20, 12, -30);
      shadowSpan = GLM.mix(260.0, 75.0, u);
      dofRange = GLM.mix(340.0, 58.0, u);
    }
    else if (frame < 2007) {
      // [1391..2007] 500 FPS Five Separate Moves Through the 3.2 mm Acrylic Gate!
      world.roachHero.root.visible = true;
      world.labGateGroup.visible = true;
      world.ceilingSlab.visible = false;
      world.micrometerBridge.visible = false;
      world.labGateGroup.position.set(0, 3.2, 0);
      world.humanActors.poseResearcher(t, 0.5, 0.75);

      let rx = -16, ceil = 12.2, probe = 0, hPitch = 0, pRoll = 0, ph = t * 1.6;
      if (frame < 1538) {
        // Move 1 [1391..1538]: Antennae sweep the slot
        const u = sIn(frame, 1391, 1538);
        rx = GLM.mix(-18, -12.5, u);
        probe = 0.35 + 0.65 * Math.sin(u * Math.PI);
        ceil = 12.0;
      } else if (frame < 1638) {
        // Move 2 [1538..1638]: Head tips down and wedges in
        const u = sIn(frame, 1538, 1638);
        rx = GLM.mix(-12.5, -6.5, u);
        hPitch = -0.30 * u;
        ceil = GLM.mix(12.0, 7.8, u);
        probe = 0.7 * (1 - u);
      } else if (frame < 1767) {
        // Move 3 [1638..1767]: Pronotum shield rolls slightly (~11 deg) to slip inside
        const u = sIn(frame, 1638, 1767);
        rx = GLM.mix(-6.5, 2.5, u);
        hPitch = -0.30 * (1 - 0.5 * u);
        pRoll = 0.22 * Math.sin(u * Math.PI);
        ceil = GLM.mix(7.8, 3.55, u);
      } else if (frame < 1913) {
        // Move 4 [1767..1913]: Back legs stay planted outside and shove the thickest chest through!
        const u = sIn(frame, 1767, 1913);
        rx = GLM.mix(2.5, 16.5, u);
        ceil = 3.28;
        ph = 0.15 + u * 2.4;
      } else {
        // Move 5 [1913..2007]: Flattened belly pulls clear!
        const u = sIn(frame, 1913, 2007);
        rx = GLM.mix(16.5, 36.0, u);
        ceil = GLM.mix(3.28, 8.8, sIn(frame, 1955, 2007));
        ph = 2.55 + u * 2.2;
      }

      const r = world.roachHero.update({
        ceilingMm: ceil, worldX: rx, worldZ: 0,
        phase: ph, strideAmp: 0.85, antennaProbe: probe, headPitch: hPitch, pronotumRoll: pRoll, time: t,
      });
      landmarks = r.landmarks;

      const uAll = sIn(frame, 1391, 2007);
      fov = 28;
      camPos.set(GLM.mix(-46, 8, uAll), GLM.mix(14.5, 10.5, uAll), GLM.mix(58, 52, uAll));
      camLook.set(GLM.mix(-6, 12, uAll), 4.2, 0);
      shadowCenter.set(rx, 4, 0);
      shadowSpan = 56.0;
      dofRange = 42.0;
    }
    else {
      // [2007..2586] ZACK-D FULL-BODY 3D TRANSLUCENT X-RAY & ROOF-TILE HINGE CUTAWAY!
      world.xrayRig.group.visible = true;
      world.corridorGroup.visible = false;
      world.humanActors.poseResearcher(t, 0.4, 0.65);

      let comp = 0.0;
      if (frame < 2404) {
        comp = sIn(frame, 2045, 2345); // Smooth 47% vertical compression showing rigid amber plates + folding cyan hinges!
      } else {
        comp = 1.0 - sIn(frame, 2410, 2525); // Viscoelastic rebound!
      }

      const xr = world.xrayRig.update({
        compAlpha: comp,
        showPlaten: true,
        showLoadArrows: false,
        time: t,
        phase: t * 1.4,
      });
      landmarks = xr.landmarks;
      mode = 'cutaway';

      const u = sIn(frame, 2007, 2586);
      fov = 26;
      camPos.set(GLM.mix(-8, 6, u), GLM.mix(9.5, 7.2, u), GLM.mix(48, 39, u));
      camLook.set(-1.5, GLM.mix(4.2, 3.2, comp), 0);
      shadowCenter.set(-1.5, 4, 0);
      shadowSpan = 46.0;
      dofRange = 36.0;
    }
  }

  // =========================================================================
  // CHAPTER 3 [2586..4099]: THE LOW-CEILING SURPRISE (12 -> 9 -> 6 -> 4 MM)
  // =========================================================================
  else if (frame < 4099) {
    world.labSet.visible = true;
    world.setLightingMood('lab', 1.0);

    if (frame < 3662) {
      // [2586..3662] Researcher steps down micrometer roof (12 -> 9 -> 6 mm) while cockroach holds ~58 cm/s sprint!
      world.roachHero.root.visible = true;
      world.ceilingSlab.visible = true;
      world.micrometerBridge.visible = true;
      world.labFloorStrip.material = world.mats.grit40Mat;

      // Stepped ceiling height: 12 mm -> 9 mm (@3035) -> 6 mm (@3155)
      let ceil = 12.0;
      if (frame >= 3035 && frame < 3155) ceil = GLM.mix(12.0, 9.0, sIn(frame, 3035, 3075));
      else if (frame >= 3155) ceil = GLM.mix(9.0, 6.0, sIn(frame, 3155, 3205));

      world.ceilingSlab.position.y = ceil;
      world.micrometerDrum.rotation.y = (12.0 - ceil) * 1.25;
      world.humanActors.poseResearcher(t, sIn(frame, 2980, 3060) * (1.0 - 0.4 * sIn(frame, 3320, 3420)), 0.65);

      // Continuous looped treadmill/tracking sprint along corridor X = [-75..+75]
      const rx = -55 + ((t * 58.0) % 110.0);
      const r = world.roachHero.update({
        ceilingMm: ceil, worldX: rx, worldZ: 0,
        phase: t * 16.38, strideAmp: 1.0, gaitMode: 'tripod', time: t,
      });
      landmarks = r.landmarks;
      world.micrometerBridge.position.x = rx + 10;

      if (frame < 3280) {
        // Side-3/4 macro tracking camera showing Researcher + micrometer drum + lowering ceiling!
        const u = sIn(frame, 2586, 3280);
        fov = 32;
        camPos.set(rx - 42, GLM.mix(38, 18, u), GLM.mix(108, 72, u));
        camLook.set(rx + 4, GLM.mix(16, 6, u), GLM.mix(-24, -4, u));
      } else {
        // Elevated dorsal-3/4 kinematics cam showing 55° -> 75° wide leg splay with ZERO acrylic washout!
        const u = sIn(frame, 3280, 3662);
        fov = 30;
        camPos.set(rx - 22, GLM.mix(48, 42, u), GLM.mix(38, 28, u));
        camLook.set(rx + 2, 3.5, 0);
      }
      shadowCenter.set(rx, 5, 0);
      shadowSpan = 68.0;
      dofRange = 55.0;
      metrics = { gauge: 'speed_cliff', ceilingMm: ceil, speedCms: 58.1 };
    }
    else {
      // [3662..4099] 3-LANE SIMULTANEOUS HEIGHT COMPARISON RACE (12 mm vs 6 mm vs 4 mm)!
      // Visually proves the dramatic 4x speed crash (58.1 cm/s vs 14.5 cm/s) in one unforgettable shot!
      world.corridorGroup.visible = false;
      world.multiLaneGroup.visible = true;
      world.roachHero.root.visible = true;
      world.roachB.root.visible    = true;
      world.roachC.root.visible    = true;
      world.humanActors.poseResearcher(t, 0.45, 0.75);

      world.laneRoofs[0].position.y = 12.0; // Back lane: 12 mm open sprint (58.1 cm/s)
      world.laneRoofs[1].position.y = 6.0;  // Mid lane:  6 mm half-height sprint (57.8 cm/s)
      const drop4 = GLM.mix(6.0, 4.0, sIn(frame, 3662, 3720));
      world.laneRoofs[2].position.y = drop4; // Front hero lane: 4 mm body squeeze -> crashes to 14.5 cm/s!
      world.laneFloors.forEach((fl) => { fl.material = world.mats.grit40Mat; });

      const raceU = uIn(frame, 3662, 4099);
      const cycleU = (raceU * 2.2) % 1.0;
      const xFast12 = GLM.mix(-95, 95, Math.min(1.0, cycleU * 1.35));
      const xFast6  = GLM.mix(-95, 92, Math.min(1.0, cycleU * 1.32));
      const xSlow4  = GLM.mix(-95, -42, cycleU); // 4x slower!

      world.roachB.update({ ceilingMm: 12.0, worldX: xFast12, worldZ: -38, phase: t * 16.38, strideAmp: 1.0, gaitMode: 'tripod', time: t });
      world.roachC.update({ ceilingMm: 6.0,  worldX: xFast6,  worldZ: 0,   phase: t * 16.10, strideAmp: 1.0, gaitMode: 'tripod', time: t });
      const r4 = world.roachHero.update({ ceilingMm: drop4, worldX: xSlow4, worldZ: 38, phase: t * 6.8, strideAmp: 0.78, gaitMode: 'oar', time: t });
      landmarks = r4.landmarks;

      const u = sIn(frame, 3662, 4099);
      fov = 36;
      camPos.set(GLM.mix(-88, -48, u), GLM.mix(68, 52, u), GLM.mix(112, 92, u));
      camLook.set(GLM.mix(-15, 5, u), 3.0, -4.0);
      shadowCenter.set(-10, 5, 0);
      shadowSpan = 120.0;
      dofRange = 115.0;
      metrics = { gauge: 'speed_cliff', ceilingMm: drop4, speedCms: GLM.mix(58.1, 14.5, sIn(frame, 3680, 3840)) };
    }
  }

  // =========================================================================
  // CHAPTER 4 [4099..6012]: WHEN SHINS BECOME FEET (+ 3D HUMAN PUSH-UP STAGE!)
  // =========================================================================
  else if (frame < 6012) {
    if (frame >= 4869 && frame < 5008) {
      // [4869..5008] ZACK-D 3D HUMAN ATHLETE WIDE-ARM PUSH-UP BIOMECHANICS STAGE!
      // "Picture trying a push-up with your arms stretched straight out to the sides."
      world.pushupSet.visible = true;
      world.setLightingMood('pushup', 1.0);

      const splayAlpha = sIn(frame, 4898, 4952);
      const repCycle = (frame - 4869) / 46.0;
      world.humanActors.poseAthletePushup(t, splayAlpha, repCycle);

      // Height of torso off force plate drops from ~390 mm (upright push-up) down to ~145 mm (>82° wide-arm sprawl!)
      const dip = 0.5 - 0.5 * Math.cos(repCycle * Math.PI * 2);
      const chestH = GLM.mix(420 - 155 * dip, 155 - 28 * dip, splayAlpha);
      world.athletePivot.position.set(-820, chestH, 0);

      // Update glowing 3D ground-reaction arrows at hands (green vertical -> amber tilted outward!)
      world.handArrows.forEach(({ group, shaft, tip, side }) => {
        const handZ = side * GLM.mix(310, 815, splayAlpha);
        group.position.set(520, 0, handZ);
        group.rotation.x = side * splayAlpha * 0.58;
        const mat = splayAlpha > 0.5 ? world.vecMatAmber : world.vecMatGreen;
        shaft.material = mat;
        tip.material = mat;
      });

      const u = sIn(frame, 4869, 5008);
      fov = 34;
      // Front-3/4 low biomechanics camera framing face, straining shoulders, and splayed hands!
      camPos.set(GLM.mix(1850, 1620, u), GLM.mix(760, 480, u), GLM.mix(1120, 680, u));
      camLook.set(220, GLM.mix(240, 145, splayAlpha), 0);
      shadowCenter.set(120, 120, 0);
      shadowSpan = 1350.0;
      dofRange = 1400.0;
      maxBlur = 1.8;
      mode = 'pushup';
    }
    else {
      world.labSet.visible = true;
      world.setLightingMood('lab', 1.0);
      world.roachHero.root.visible = true;
      world.ceilingSlab.visible = true;
      world.micrometerBridge.visible = false;
      world.labFloorStrip.material = world.mats.grit40Mat;
      world.humanActors.poseResearcher(t, 0.35, 0.7);

      if (frame < 4649) {
        // [4099..4649] Open 12 mm stance: posterior-lateral macro tracking hooked tarsal claws & pale arolium pad!
        world.ceilingSlab.position.y = 12.5;
        const rx = -30 + ((t * 14.0) % 60.0);
        const r = world.roachHero.update({
          ceilingMm: 12.5, worldX: rx, worldZ: 0,
          phase: t * 3.2, strideAmp: 0.9, gaitMode: 'tripod', time: t,
        });
        landmarks = r.landmarks;

        const claw = r.landmarks.r3Claw;
        const u = sIn(frame, 4099, 4649);
        fov = 25;
        camPos.set(claw.x - GLM.mix(24, 15, u), GLM.mix(7.2, 4.2, u), claw.z + GLM.mix(22, 14, u));
        camLook.set(claw.x + 1.0, claw.y + 0.8, claw.z - 1.5);
        shadowCenter.copy(claw);
        shadowSpan = 34.0;
        dofRange = 18.0;
        maxBlur = 3.2;
      }
      else if (frame < 4869) {
        // [4649..4869] Press ceiling 12 mm -> 4 mm: leg splays past 80 deg, foot claws tip sideways +0.48 mm clear!
        const sq = sIn(frame, 4655, 4795);
        const ceil = GLM.mix(12.2, 4.0, sq);
        world.ceilingSlab.position.y = ceil;
        const r = world.roachHero.update({
          ceilingMm: ceil, worldX: 0, worldZ: 0,
          phase: 0.22 + t * 1.2, strideAmp: 0.55, time: t,
        });
        landmarks = r.landmarks;

        const claw = r.landmarks.r3Claw;
        fov = 24;
        camPos.set(claw.x - 15.5, GLM.mix(5.2, 3.1, sq), claw.z + 15.5);
        camLook.set(claw.x, claw.y + 0.4, claw.z - 2.0);
        shadowCenter.copy(claw);
        shadowSpan = 32.0;
        dofRange = 16.0;
      }
      else if (frame < 5469) {
        // [5008..5469] Match-cut from human wide-arm push-up back to cockroach tibia ->
        // [5197..5469] PROTECTED CLIMAX #2: UNINTERRUPTED EXTREME MACRO TIBIAL SPINE STRIKE & CRAMPON DRIVE!
        world.ceilingSlab.position.y = 4.0;
        const rx = -24 + ((t * 11.5) % 48.0);
        const r = world.roachHero.update({
          ceilingMm: 4.0, worldX: rx, worldZ: 0,
          phase: t * 2.8, strideAmp: 1.0, gaitMode: 'oar', time: t,
        });
        landmarks = r.landmarks;

        const sp = r.landmarks.r3Spine;
        const cl = r.landmarks.r3Claw;
        const panToSpine = sIn(frame, 5070, 5190);

        // Kick up micro-grit dust particles during the Protected Crampon Climax [5197..5469]!
        if (frame >= 5197) {
          updateDustBurst(world.dustParticles, sp, t, 1.0);
        }

        fov = 22;
        const focusPt = cl.clone().lerp(sp, panToSpine);
        camPos.set(focusPt.x - 13.5, GLM.mix(3.2, 2.25, panToSpine), focusPt.z + 12.8);
        camLook.set(focusPt.x + 1.2, focusPt.y + 0.45, focusPt.z - 1.2);
        shadowCenter.copy(focusPt);
        shadowSpan = 26.0;
        dofRange = 13.0;
        maxBlur = 3.4;
      }
      else {
        // [5469..6012] Synchronous middle-leg oar stroke + 5x body-weight (~38 mN) propulsive push!
        world.ceilingSlab.position.y = 4.0;
        const rx = -35 + ((t * 14.5) % 70.0);
        const r = world.roachHero.update({
          ceilingMm: 4.0, worldX: rx, worldZ: 0,
          phase: t * 4.4, strideAmp: 1.0, gaitMode: 'oar', time: t,
        });
        landmarks = r.landmarks;
        updateDustBurst(world.dustParticles, r.landmarks.r3Spine, t, 0.7);

        if (frame < 5665) {
          // Overhead-3/4 crystal-clear view showing L2 + R2 rowing synchronously like a pair of oars!
          const u = sIn(frame, 5469, 5665);
          fov = 29;
          camPos.set(rx - 18, GLM.mix(42, 36, u), GLM.mix(24, 16, u));
          camLook.set(rx + 1.5, 2.0, 0);
        } else {
          // Heroic low-angle front-3/4 power shot showing roof rub, belly rub, and 5x BW tibial crampon drive!
          const u = sIn(frame, 5665, 6012);
          fov = 27;
          camPos.set(rx + GLM.mix(34, 26, u), 3.4, GLM.mix(26, 20, u));
          camLook.set(rx - 2.0, 2.1, 2.0);
        }
        shadowCenter.set(rx, 2.5, 0);
        shadowSpan = 45.0;
        dofRange = 28.0;
      }
    }
  }

  // =========================================================================
  // CHAPTER 5 [6012..7456]: THE ROUGH-FLOOR TRAP (638 Runs · 100 / 40 / 20 Grit)
  // =========================================================================
  else if (frame < 7456) {
    world.labSet.visible = true;
    world.setLightingMood('lab', 1.0);
    world.humanActors.poseResearcher(t, 0.5, 0.65);

    if (frame < 6600) {
      // [6012..6600] Isolated tarsus-free spine grip test (mu = 1.73 - 2.04)!
      world.roachHero.root.visible = true;
      world.ceilingSlab.visible = true;
      world.ceilingSlab.position.y = 4.0;
      world.micrometerBridge.visible = false;
      world.labFloorStrip.material = world.mats.grit40Mat;

      const r = world.roachHero.update({
        ceilingMm: 4.0, worldX: 0, worldZ: 0,
        phase: t * 2.4, strideAmp: 0.85, gaitMode: 'oar', time: t,
      });
      landmarks = r.landmarks;
      const sp = r.landmarks.r3Spine;
      updateDustBurst(world.dustParticles, sp, t, 0.75);

      const u = sIn(frame, 6012, 6600);
      fov = 24;
      camPos.set(sp.x - GLM.mix(18, 12, u), GLM.mix(5.8, 3.0, u), sp.z + GLM.mix(18, 13, u));
      camLook.set(sp.x + 1.0, sp.y + 0.5, sp.z - 1.0);
      shadowCenter.copy(sp);
      shadowSpan = 30.0;
      dofRange = 16.0;
    }
    else if (frame < 6980) {
      // [6600..6980] 638 confined runs — rougher ceilings monotonically slow forward motion (6.64 -> 5.63 -> 0.36 cm/s)
      world.roachHero.root.visible = true;
      world.ceilingSlab.visible = true;
      world.ceilingSlab.position.y = 4.0;
      world.micrometerBridge.visible = true;
      world.labFloorStrip.material = world.mats.grit40Mat;

      const rx = -30 + ((t * 8.5) % 60.0);
      const r = world.roachHero.update({
        ceilingMm: 4.0, worldX: rx, worldZ: 0,
        phase: t * 3.5, strideAmp: 0.9, gaitMode: 'oar', time: t,
      });
      landmarks = r.landmarks;
      world.micrometerBridge.position.x = rx + 8;

      const u = sIn(frame, 6600, 6980);
      fov = 28;
      camPos.set(rx + GLM.mix(-36, 22, u), 4.6, 38.0);
      camLook.set(rx, 2.4, 0);
      shadowCenter.set(rx, 3, 0);
      shadowSpan = 52.0;
      dofRange = 36.0;
      metrics = { gauge: 'ceiling_rub' };
    }
    else {
      // [6980..7456] 3-LANE FLOOR GRIT TRADE-OFF ARENA (100-grit Slick vs 40-grit Medium Winner vs 20-grit Coarse Belly Snag)!
      world.corridorGroup.visible = false;
      world.multiLaneGroup.visible = true;
      world.roachHero.root.visible = true;
      world.roachB.root.visible    = true;
      world.roachC.root.visible    = true;

      world.laneFloors[0].material = world.mats.grit100Mat; // Back lane: 100-grit slick (1.57 cm/s — spines slip!)
      world.laneFloors[1].material = world.mats.grit40Mat;  // Center lane: 40-grit medium WINNER (5.26 cm/s!)
      world.laneFloors[2].material = world.mats.grit20Mat;  // Front lane: 20-grit coarse (3.69 cm/s — flattened belly snags!)
      world.laneRoofs.forEach((rg) => { rg.position.y = 4.0; });

      const u = uIn(frame, 6980, 7456);
      const x100 = GLM.mix(-65, -32, u); // 1.57 cm/s (slowest — slipping fast legs!)
      const x40  = GLM.mix(-65,  48, u); // 5.26 cm/s (leads cleanly!)
      const x20  = GLM.mix(-65,  12, u); // 3.69 cm/s (jerky belly snag!)

      world.roachB.update({ ceilingMm: 4.0, worldX: x100, worldZ: -38, phase: t * 9.5, strideAmp: 1.0, gaitMode: 'oar', time: t });
      const rWin = world.roachHero.update({ ceilingMm: 4.0, worldX: x40, worldZ: 0, phase: t * 5.8, strideAmp: 1.0, gaitMode: 'oar', time: t });
      // Add subtle snag stutter on coarse 20-grit lane!
      const snagX = x20 - 1.2 * Math.pow(Math.sin(t * 7.5), 4);
      world.roachC.update({ ceilingMm: 4.0, worldX: snagX, worldZ: 38, phase: t * 5.2, strideAmp: 0.9, gaitMode: 'oar', time: t });
      landmarks = rWin.landmarks;

      const cu = sIn(frame, 6980, 7456);
      fov = 35;
      camPos.set(GLM.mix(-78, -24, cu), GLM.mix(64, 48, cu), GLM.mix(106, 88, cu));
      camLook.set(GLM.mix(-22, 6, cu), 3.0, -4.0);
      shadowCenter.set(0, 3, 0);
      shadowSpan = 105.0;
      dofRange = 105.0;
      metrics = { gauge: 'floor_grit' };
    }
  }

  // =========================================================================
  // CHAPTER 6 [7456..9070]: TOUGH SHELL, TIGHT LIMIT (~900x BW & 315 Attempts)
  // =========================================================================
  else if (frame < 9070) {
    world.labSet.visible = true;
    world.setLightingMood('lab', 1.0);
    world.humanActors.poseResearcher(t, 0.55, 0.65);

    if (frame < 7775) {
      // [7456..7775] Full-Body 3D X-Ray Compression Load-Cell Press: ~300x -> ~900x Body Weight (6.08 N across 3 cm2, 2mm stop)!
      world.xrayRig.group.visible = true;
      world.corridorGroup.visible = false;

      const loadCurve = frame < 7710 ? sIn(frame, 7475, 7677) : (1.0 - sIn(frame, 7715, 7770));
      const xr = world.xrayRig.update({
        compAlpha: loadCurve * 0.96,
        showPlaten: true,
        showLoadArrows: loadCurve > 0.25,
        time: t,
        phase: t * 0.8,
      });
      landmarks = xr.landmarks;
      mode = 'cutaway';

      const u = sIn(frame, 7456, 7775);
      fov = 28;
      // Frame the X-ray cockroach + steel compression piston in foreground with CRAM soft-robot & Researcher softly visible in lab depth!
      camPos.set(GLM.mix(-28, 12, u), GLM.mix(14.5, 9.5, u), GLM.mix(58, 46, u));
      camLook.set(GLM.mix(4, -1, u), 4.5, -4.0);
      shadowCenter.set(0, 4, 0);
      shadowSpan = 55.0;
      dofRange = 55.0;
    }
    else if (frame < 8070) {
      // [7775..8070] Post-load unimpaired open sprint at 76.7 cm/s!
      world.roachHero.root.visible = true;
      world.ceilingSlab.visible = false;
      world.micrometerBridge.visible = false;
      world.labFloorStrip.material = world.mats.grit40Mat;

      const u = uIn(frame, 7775, 8070);
      const rx = -110 + ((u * 340) % 220);
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: 0,
        phase: t * 19.5, strideAmp: 1.0, gaitMode: 'tripod', time: t,
      });
      landmarks = r.landmarks;

      fov = 31;
      camPos.set(rx - 44, 16.5, 62.0);
      camLook.set(rx + 8, 6.0, -8.0);
      shadowCenter.set(rx, 5, 0);
      shadowSpan = 68.0;
      dofRange = 54.0;
    }
    else if (frame < 8426) {
      // [8070..8426] 315 Gate Attempts — wider 6.1 / 4.4 mm slots: 72% shoot straight through!
      world.roachHero.root.visible = true;
      world.labGateGroup.visible = true;
      world.ceilingSlab.visible = false;
      world.micrometerBridge.visible = false;
      world.labGateGroup.position.set(0, 5.8, 0);

      const u = uIn(frame, 8070, 8426);
      const cyc = (u * 2.0) % 1.0;
      const rx = GLM.mix(-65, 75, cyc);
      const inGate = GLM.smoothstep(-14, 0, rx) * (1 - GLM.smoothstep(18, 34, rx));
      const r = world.roachHero.update({
        ceilingMm: GLM.mix(12.52, 5.8, inGate), worldX: rx, worldZ: 0,
        phase: t * 16.0, strideAmp: 1.0, time: t,
      });
      landmarks = r.landmarks;

      fov = 30;
      camPos.set(-52, 22, 74);
      camLook.set(4, 6, 0);
      shadowCenter.set(0, 5, 0);
      shadowSpan = 68.0;
      dofRange = 58.0;
      metrics = { gauge: 'gate_315' };
    }
    else if (frame < 8842) {
      // [8426..8842] Gate narrows to 3.2 mm (17% pass; 74% sweep with antennae, feel the squeeze, and TURN BACK!)
      world.roachHero.root.visible = true;
      world.labGateGroup.visible = true;
      world.ceilingSlab.visible = false;
      world.micrometerBridge.visible = false;
      const gateH = GLM.mix(5.8, 3.2, sIn(frame, 8426, 8510));
      world.labGateGroup.position.set(0, gateH, 0);

      // Approach [-52 -> -15] during [8426..8660], probe slot [8660..8735], smooth 180° turn-around & retreat [8735..8842]!
      let rx = -15, rz = 0, yaw = 0, probe = 0, amp = 0.8;
      if (frame < 8660) {
        rx = GLM.mix(-54, -15, sIn(frame, 8426, 8660));
        probe = sIn(frame, 8580, 8660) * 0.8;
      } else if (frame < 8735) {
        rx = -15 + Math.sin((frame - 8660) * 0.12) * 1.5;
        probe = 1.0;
        amp = 0.25;
      } else {
        const tu = sIn(frame, 8735, 8800);
        const walkBack = uIn(frame, 8765, 8842);
        yaw = tu * Math.PI;
        rz = Math.sin(tu * Math.PI) * 6.5;
        rx = -15 - walkBack * 42.0;
        amp = 0.95;
      }
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: rz, yaw,
        phase: t * 9.5, strideAmp: amp, antennaProbe: probe, time: t,
      });
      landmarks = r.landmarks;

      const u = sIn(frame, 8426, 8842);
      fov = 29;
      camPos.set(GLM.mix(-58, -46, u), GLM.mix(18, 14, u), GLM.mix(68, 56, u));
      camLook.set(-10, 4.5, 0);
      shadowCenter.set(-14, 4, 0);
      shadowSpan = 62.0;
      dofRange = 48.0;
      metrics = { gauge: 'gate_315' };
    }
    else {
      // [8842..9070] "Nearly one in ten wedged fast at the thickest part of its chest." (9% thorax-wedged!)
      world.roachHero.root.visible = true;
      world.labGateGroup.visible = true;
      world.ceilingSlab.visible = false;
      world.micrometerBridge.visible = false;
      world.labGateGroup.position.set(0, 3.15, 0);

      const enterU = sIn(frame, 8842, 8915);
      // Wedges right at X = +3.2 mm (thickest pronotum/mesothorax jammed inside gate!) while hind legs churn!
      const rx = GLM.mix(-24, 3.2, enterU) + (frame >= 8915 ? 0.28 * Math.sin(t * 28.0) : 0.0);
      const r = world.roachHero.update({
        ceilingMm: GLM.mix(11.5, 3.35, enterU), worldX: rx, worldZ: 0,
        phase: t * 11.0, strideAmp: 0.95, headPitch: -0.15, pronotumRoll: 0.08, time: t,
      });
      landmarks = r.landmarks;
      updateDustBurst(world.dustParticles, r.landmarks.r3Spine, t, 0.55);

      fov = 26;
      camPos.set(-36, 11.5, 44);
      camLook.set(2.0, 3.4, 0);
      shadowCenter.set(0, 3, 0);
      shadowSpan = 45.0;
      dofRange = 32.0;
      metrics = { gauge: 'gate_315' };
    }
  }

  // =========================================================================
  // CHAPTER 7 [9070..10302]: HINGES AND SPINES (1x Real-Speed Reprise & Rebound)
  // =========================================================================
  else {
    world.apartmentSet.visible = true;
    world.setLightingMood('apartment_lit', 1.0);
    world.switchToggle.rotation.z = -0.42;
    world.penniesGroup.visible = true;
    world.humanActors.poseHomeowner(t, 0.2, 0.85);

    if (frame < 9182) {
      // [9070..9182] "Now watch that two-penny escape once more at real speed."
      world.roachHero.root.visible = true;
      const u = sIn(frame, 9070, 9182);
      const rx = GLM.mix(-95, -48, u);
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: 0,
        phase: t * 14.0, strideAmp: 1.0, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      fov = 31;
      camPos.set(GLM.mix(-88, -58, u), 12.5, 58.0);
      camLook.set(-8, 4.0, 8.0);
      shadowCenter.set(-25, 4, 5);
      shadowSpan = 65.0;
      dofRange = 48.0;
    }
    else if (frame < 9637) {
      // [9182..9637] PROTECTED CLIMAX #3: Real-speed 1x traversal [9215..9265], camera sweeps to far side (+X)
      // watching folded hinges viscoelastically spring shell back to 12.52 mm & feet resume full sprint!
      world.roachHero.root.visible = true;
      let rx, ceil = 12.52, pRoll = 0, hPitch = 0;
      if (frame < 9220) {
        rx = GLM.mix(-48, -10, uIn(frame, 9182, 9220));
      } else if (frame < 9268) {
        // True ~0.6s real-speed squeeze through X=[0..44]!
        const u = sIn(frame, 9220, 9268);
        rx = GLM.mix(-10, 56, u);
        const inDoor = GLM.smoothstep(-10, 2, rx) * (1 - GLM.smoothstep(40, 54, rx));
        ceil = GLM.mix(12.52, 3.22, inDoor);
        pRoll = 0.16 * Math.sin(inDoor * Math.PI);
        hPitch = -0.18 * (1 - u);
      } else {
        // Far-side hallway: viscoelastic shell rebound [9268..9420] & full tarsal sprint [9420..9637]!
        const u = uIn(frame, 9268, 9637);
        rx = 56 + u * 165;
        ceil = GLM.mix(4.2, 12.52, sIn(frame, 9268, 9385));
      }
      const r = world.roachHero.update({
        ceilingMm: ceil, worldX: rx, worldZ: 0,
        phase: t * 16.5, strideAmp: 1.0, headPitch: hPitch, pronotumRoll: pRoll, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      // Before frame 9260: kitchen-side threshold cam; Frame 9260+: match-cut to far-side hallway low tracking cam!
      if (frame < 9260) {
        const u = sIn(frame, 9182, 9260);
        fov = 30;
        camPos.set(-46 + u * 14, 7.5, 42);
        camLook.set(6, 2.8, 0);
        shadowCenter.set(0, 3, 0);
      } else {
        const u = sIn(frame, 9260, 9637);
        fov = 29;
        camPos.set(rx - GLM.mix(-28, 42, u), GLM.mix(8.5, 11.5, u), 48.0);
        camLook.set(rx + 4, 5.2, 0);
        shadowCenter.set(rx, 4, 0);
      }
      shadowSpan = 58.0;
      dofRange = 42.0;
    }
    else if (frame < 10017) {
      // [9637..10017] Final thesis synthesis: heroic macro tracking glide alongside sprinting cockroach!
      // "It gets through because its shell can fold, and its shins can walk."
      world.roachHero.root.visible = true;
      const u = sIn(frame, 9637, 10017);
      const rx = GLM.mix(65, 185, u);
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: 0,
        phase: t * 14.5, strideAmp: 1.0, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      fov = 28;
      camPos.set(rx + 28, 9.8, 44.0);
      camLook.set(rx - 2, 5.4, 0);
      shadowCenter.set(rx, 4, 0);
      shadowSpan = 55.0;
      dofRange = 38.0;
    }
    else {
      // [10017..10302] PROTECTED QUIET CLOSING HOLD on the empty 3.2 mm two-penny gap + warm hallway light spill
      // followed by clean PNAS Primary Source Card [10212..10302]!
      world.roachHero.root.visible = false;
      landmarks = { pennies: penniesWorld };

      const u = sIn(frame, 10017, 10302);
      fov = 28;
      camPos.set(GLM.mix(-56, -44, u), GLM.mix(10.5, 7.2, u), GLM.mix(42, 28, u));
      camLook.set(-14, 2.4, -8);
      shadowCenter.set(-18, 3, -10);
      shadowSpan = 48.0;
      dofRange = 36.0;
    }
  }

  // Apply camera & render real-time shadow map focused tightly on active subject!
  camera.fov = fov;
  camera.position.copy(camPos);
  camera.lookAt(camLook);
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);

  world.updateShadowMap(shadowCenter, shadowSpan);

  const focusDist = camPos.distanceTo(camLook);
  return {
    mode,
    landmarks,
    metrics,
    lensParams: {
      focusDist,
      dofRange,
      maxBlur,
      time: t,
    },
  };
}
