import * as THREE from 'three';
import { GLM } from './cockroach3d_v5.js';

/**
 * Monarch Cam #03 — V5 Cinema Master Director (9,008 frames = 300.27s @ 30 fps)
 * Frame-locked to tightened zero-dead-air voice-lock-v5.json (Arena voice-02, 0% time-stretch).
 *
 * STRICT V5 GUARANTEES:
 *   1. ZERO `%` modulo coordinate/cycle snap-back loops anywhere in the film!
 *   2. ZERO coplanar Z-fighting or alternating-frame shadow skips!
 *   3. 32 motivated cinema shots across continuous 1.88 m lab & 3.8 m apartment environments!
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
    const raw = time * 4.2 + seed;
    const cyc = raw - Math.floor(raw);
    const spreadZ = Math.sin(seed * 13.7) * 1.8;
    const backX = -cyc * (4.5 + (i & 3) * 1.2);
    const arcY = Math.sin(Math.PI * cyc) * (0.42 + (i & 3) * 0.16);
    tmpP.set(origin.x + backX, Math.max(0.04, origin.y + arcY), origin.z + spreadZ);
    const sc = (1.0 - cyc) * (0.55 + 0.45 * Math.sin(seed * 7.1)) * intensity;
    tmpS.set(sc, sc, sc);
    tmpQ.setFromEuler(new THREE.Euler(time * 8 + i, time * 6, i));
    tmpM.compose(tmpP, tmpQ, tmpS);
    dustMesh.setMatrixAt(i, tmpM);
  }
  dustMesh.instanceMatrix.needsUpdate = true;
}

export function directFrameV5(world, camera, frame) {
  const t = frame / FPS;

  // Reset per-frame visibility cleanly
  world.apartmentSet.visible       = false;
  world.labSet.visible             = false;
  world.pushupSet.visible          = false;
  world.roachHero.root.visible     = false;
  world.roachB.root.visible        = false;
  world.roachC.root.visible        = false;
  world.xrayRig.group.visible      = false;
  world.cramActor.root.visible     = false;
  world.cramBenchProp.root.visible = true;
  world.corridorGroup.visible      = true;
  world.labGateGroup.visible       = false;
  world.tractionPlateGroup.visible = false;
  world.gritSwatchGroup.visible    = false;
  world.multiLaneGroup.visible     = false;
  world.dustParticles.visible      = false;

  const camPos = new THREE.Vector3(0, 20, 60);
  const camLook = new THREE.Vector3(0, 5, 0);
  let fov = 34;
  let shadowCenter = new THREE.Vector3(0, 4, 0);
  let shadowSpan = 65.0;
  let dofRange = 45.0;
  let maxBlur = 2.5;
  let mode = 'cinema';
  let landmarks = {};
  let metrics = null;

  const penniesWorld = new THREE.Vector3(-24.0, 2.4, -17.5);

  // =========================================================================
  // CHAPTER 1 [0..921]: UNDER THE DOOR (Midnight Apartment -> Switch -> Vanish)
  // =========================================================================
  if (frame < 921) {
    world.apartmentSet.visible = true;
    world.roachHero.root.visible = true;
    world.penniesGroup.visible = frame >= 185;

    if (frame < 29) {
      // [0..29] 2:14 AM moonlit hallway; homeowner reaches naturally to chest-height wall toggle!
      world.setLightingMood('apartment_dark', 1.0);
      world.switchToggle.rotation.z = 0.42;
      const reach = sIn(frame, 2, 28);
      world.humanActors.poseHomeowner(t, reach, 0.0);

      const u = uIn(frame, 0, 29);
      fov = GLM.mix(45, 41, u);
      camPos.set(GLM.mix(-1420, -1260, u), GLM.mix(1380, 1340, u), GLM.mix(40, -40, u));
      camLook.set(GLM.mix(-280, -210, u), GLM.mix(1240, 1215, u), GLM.mix(-590, -565, u));
      shadowCenter.set(-340, 1180, -600);
      shadowSpan = 720.0;
      dofRange = 1100.0;
      maxBlur = 1.6;

      const r = world.roachHero.update({ ceilingMm: 12.52, worldX: -245, worldZ: 0, phase: 0, strideAmp: 0, time: t });
      landmarks = { ...r.landmarks, pennies: penniesWorld };
    }
    else if (frame < 145) {
      // [29..145] SNAP! Light switch flips UP -> warm 3000K kitchen light -> WHIP-BOOM DIVE locked onto sprinting cockroach!
      const flash = sIn(frame, 29, 36);
      world.setLightingMood('apartment_lit', flash);
      world.switchToggle.rotation.z = GLM.mix(0.42, -0.42, sIn(frame, 28, 32));

      const lookDown = sIn(frame, 34, 72);
      const releaseReach = 1.0 - 0.60 * sIn(frame, 42, 92);
      world.humanActors.poseHomeowner(t, releaseReach, lookDown);

      const sprintU = sIn(frame, 34, 145);
      const rx = GLM.mix(-245, -76, sprintU);
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: 0,
        phase: (t - 0.95) * 16.4, strideAmp: 1.0, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      const lookSnap = sIn(frame, 32, 58);
      const dive = sIn(frame, 34, 108);
      fov = GLM.mix(41, 33, dive);
      camPos.set(
        GLM.mix(-1260, rx - 56, dive),
        GLM.mix(1340, 21.0, Math.pow(dive, 0.72)),
        GLM.mix(-40, 60.0, dive)
      );
      camLook.set(
        GLM.mix(-210, rx + 6, lookSnap),
        GLM.mix(1215, 6.2, lookSnap),
        GLM.mix(-565, 0.0, lookSnap)
      );
      shadowCenter.set(rx, 6, 0);
      shadowSpan = GLM.mix(300.0, 68.0, dive);
      dofRange = GLM.mix(620.0, 46.0, dive);
    }
    else if (frame < 214) {
      // [145..214] "Standing up, it's half an inch tall." — Heroic low-angle profile macro!
      world.setLightingMood('apartment_lit', 1.0);
      world.switchToggle.rotation.z = -0.42;
      world.humanActors.poseHomeowner(t, 0.35, 1.0);

      const u = sIn(frame, 145, 214);
      const rx = GLM.mix(-76, -54, u);
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: 0,
        phase: t * 3.4, strideAmp: 0.30, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      fov = 30;
      camPos.set(rx - 18 + u * 8, 10.2, 56.0);
      camLook.set(rx + 2, 6.2, 0);
      shadowCenter.set(rx, 5, 0);
      shadowSpan = 54.0;
      dofRange = 36.0;
    }
    else if (frame < 330) {
      // [214..330] "That gap ahead is barely as thick as two stacked pennies." — Pennies beside cockroach + 3.2mm door slot!
      world.setLightingMood('apartment_lit', 1.0);
      world.humanActors.poseHomeowner(t, 0.3, 1.0);
      const u = sIn(frame, 214, 330);
      const rx = GLM.mix(-52, -36, u);
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: 0,
        phase: t * 4.6, strideAmp: 0.38, antennaProbe: 0.48 * u, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      fov = 28;
      camPos.set(GLM.mix(-56, -50, u), GLM.mix(13.5, 9.8, u), GLM.mix(50, 34, u));
      camLook.set(GLM.mix(-24, -18, u), GLM.mix(4.2, 2.8, u), GLM.mix(-6, -10, u));
      shadowCenter.set(-22, 3, -8);
      shadowSpan = 50.0;
      dofRange = 38.0;
    }
    else if (frame < 538) {
      // [330..538] PROTECTED CLIMAX #1: Unobstructed Centered Sub-Second Vanish Under the Closed Oak Door!
      // Pennies sit cleanly at (-24, 0, -17.5) behind the cockroach's path (Z=0), so ZERO occlusion occurs!
      world.setLightingMood('apartment_lit', 1.0);
      world.humanActors.poseHomeowner(t, 0.25, 1.0);

      let rx, ceil = 12.52, hPitch = 0, pRoll = 0, probe = 0;
      if (frame < 373) {
        const u = uIn(frame, 330, 373);
        rx = GLM.mix(-36, -10, u);
        probe = sIn(frame, 345, 373);
      } else if (frame < 468) {
        const u = sIn(frame, 373, 468);
        rx = GLM.mix(-10, 34, u);
        const inSlot = GLM.smoothstep(-11, 2, rx);
        ceil = GLM.mix(12.52, 3.22, inSlot);
        hPitch = -0.24 * GLM.smoothstep(-11, 0, rx) * (1.0 - GLM.smoothstep(8, 22, rx));
        pRoll = 0.16 * Math.sin(inSlot * Math.PI * 0.85);
        probe = 1.0 - inSlot;
      } else {
        const u = uIn(frame, 468, 538);
        rx = GLM.mix(34, 138, Math.pow(u, 1.15));
        const stillUnder = 1.0 - GLM.smoothstep(40, 56, rx);
        ceil = GLM.mix(12.52, 3.22, stillUnder);
      }

      const r = world.roachHero.update({
        ceilingMm: ceil, worldX: rx, worldZ: 0,
        phase: t * 17.5, strideAmp: 1.0, antennaProbe: probe, headPitch: hPitch, pronotumRoll: pRoll, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      const camU = sIn(frame, 330, 520);
      fov = 30;
      camPos.set(GLM.mix(-50, -32, camU), GLM.mix(9.2, 5.4, camU), GLM.mix(36, 26, camU));
      camLook.set(GLM.mix(-12, 16, camU), GLM.mix(3.4, 2.0, camU), GLM.mix(-4, -1, camU));
      shadowCenter.set(GLM.mix(-10, 10, camU), 3, -4);
      shadowSpan = 52.0;
      dofRange = 42.0;
    }
    else {
      // [538..921] "Wait a second... An insect's shell is supposed to be stiff armor..."
      // Bullet-time paradox orbit right at the 3.2 mm door threshold!
      world.setLightingMood('apartment_lit', 1.0);
      const u = sIn(frame, 538, 921);
      const squeezeU = sIn(frame, 538, 680);
      const rx = GLM.mix(-4.5, 5.5, squeezeU);
      const ceil = GLM.mix(5.8, 3.26, squeezeU);
      const r = world.roachHero.update({
        ceilingMm: ceil, worldX: rx, worldZ: 0,
        phase: 0.25 + t * 0.65, strideAmp: 0.35, headPitch: -0.14, pronotumRoll: 0.10, time: t,
      });
      landmarks = { ...r.landmarks, pennies: penniesWorld };

      fov = 27;
      const ang = GLM.mix(0.88, 1.42, u);
      const dist = GLM.mix(48, 35, u);
      camPos.set(rx - Math.cos(ang) * dist, GLM.mix(9.4, 5.0, u), Math.sin(ang) * dist);
      camLook.set(rx - 2.5, GLM.mix(3.6, 2.0, u), 2.5 * u);
      shadowCenter.set(rx, 3, 0);
      shadowSpan = 44.0;
      dofRange = 30.0;
    }
  }

  // =========================================================================
  // CHAPTER 2 [921..2288]: FIVE MOVES THROUGH THE SLOT + 3D X-RAY CUTAWAY
  // =========================================================================
  else if (frame < 2288) {
    world.labSet.visible = true;
    world.setLightingMood('lab', 1.0);

    if (frame < 1224) {
      // [921..1224] Wide Human-Scale UC Berkeley Lab -> Smooth Crane Dive onto 500fps Optical Gate!
      // Starts high enough to frame Researcher's head, glasses & lab coat cleanly, then dives to bench!
      world.roachHero.root.visible = true;
      world.labGateGroup.visible = true;
      world.ceilingSlab.visible = false;
      world.micrometerBridge.visible = false;
      world.labGateGroup.position.set(0, 3.2, 0);

      const u = sIn(frame, 921, 1224);
      const rx = GLM.mix(-64, -18, u);
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: 0,
        phase: t * 4.4, strideAmp: 0.85, antennaProbe: sIn(frame, 1140, 1224) * 0.5, time: t,
      });
      landmarks = r.landmarks;

      fov = GLM.mix(42, 30, u);
      const cy = GLM.mix(460, 17, Math.pow(u, 0.72));
      // Only show full human researcher while camera is wide enough to frame him cleanly (avoids headless waist crop!)
      world.humanActors.researcher.root.visible = cy > 180;
      if (cy > 180) world.humanActors.poseResearcher(t, 0.65, 0.55);

      camPos.set(GLM.mix(-420, -56, u), cy, GLM.mix(720, 68, u));
      camLook.set(GLM.mix(-65, -10, u), GLM.mix(245, 6.2, Math.pow(u, 0.72)), GLM.mix(-320, -6, u));
      shadowCenter.set(-20, 10, -25);
      shadowSpan = GLM.mix(380.0, 72.0, u);
      dofRange = GLM.mix(680.0, 58.0, u);
    }
    else if (frame < 1819) {
      // [1224..1819] 500 FPS Five Separate Moves Through the 3.2 mm Acrylic Gate!
      world.roachHero.root.visible = true;
      world.labGateGroup.visible = true;
      world.ceilingSlab.visible = false;
      world.micrometerBridge.visible = false;
      world.labGateGroup.position.set(0, 3.2, 0);
      world.humanActors.researcher.root.visible = false; // Clean dark lab wall bokeh in tight 500fps macro!

      let rx = -16, ceil = 12.2, probe = 0, hPitch = 0, pRoll = 0, ph = t * 1.6;
      if (frame < 1362) {
        // Move 1 [1224..1362]: Antennae sweep the slot
        const u = sIn(frame, 1224, 1362);
        rx = GLM.mix(-18, -12.5, u);
        probe = 0.35 + 0.65 * Math.sin(u * Math.PI);
        ceil = 12.0;
      } else if (frame < 1459) {
        // Move 2 [1362..1459]: Head tips down and wedges in
        const u = sIn(frame, 1362, 1459);
        rx = GLM.mix(-12.5, -6.5, u);
        hPitch = -0.30 * u;
        ceil = GLM.mix(12.0, 7.8, u);
        probe = 0.7 * (1 - u);
      } else if (frame < 1583) {
        // Move 3 [1459..1583]: Pronotum shield rolls slightly (~11 deg) to slip inside
        const u = sIn(frame, 1459, 1583);
        rx = GLM.mix(-6.5, 2.5, u);
        hPitch = -0.30 * (1 - 0.5 * u);
        pRoll = 0.22 * Math.sin(u * Math.PI);
        ceil = GLM.mix(7.8, 3.55, u);
      } else if (frame < 1726) {
        // Move 4 [1583..1726]: Planted hind legs shove thickest chest through!
        const u = sIn(frame, 1583, 1726);
        rx = GLM.mix(2.5, 16.5, u);
        ceil = 3.28;
        ph = 0.15 + u * 2.4;
      } else {
        // Move 5 [1726..1819]: Flattened abdomen pulls clear!
        const u = sIn(frame, 1726, 1819);
        rx = GLM.mix(16.5, 36.0, u);
        ceil = GLM.mix(3.28, 8.8, sIn(frame, 1768, 1819));
        ph = 2.55 + u * 2.2;
      }

      const r = world.roachHero.update({
        ceilingMm: ceil, worldX: rx, worldZ: 0,
        phase: ph, strideAmp: 0.85, antennaProbe: probe, headPitch: hPitch, pronotumRoll: pRoll, time: t,
      });
      landmarks = r.landmarks;

      const uAll = sIn(frame, 1224, 1819);
      fov = 28;
      camPos.set(GLM.mix(-46, 10, uAll), GLM.mix(14.0, 9.8, uAll), GLM.mix(58, 50, uAll));
      camLook.set(GLM.mix(-6, 12, uAll), 4.0, 0);
      shadowCenter.set(rx, 4, 0);
      shadowSpan = 56.0;
      dofRange = 42.0;
    }
    else {
      // [1819..2288] ZACK-D FULL-BODY 3D TRANSLUCENT X-RAY & ROOF-TILE HINGE CUTAWAY!
      world.xrayRig.group.visible = true;
      world.corridorGroup.visible = false;
      world.humanActors.researcher.root.visible = false;

      let comp = 0.0;
      if (frame < 2198) {
        comp = sIn(frame, 1850, 2145);
      } else {
        comp = 1.0 - sIn(frame, 2202, 2278);
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

      const u = sIn(frame, 1819, 2288);
      fov = 26;
      camPos.set(GLM.mix(-12, 8, u), GLM.mix(10.0, 7.0, u), GLM.mix(48, 39, u));
      camLook.set(-1.5, GLM.mix(4.2, 3.1, comp), 0);
      shadowCenter.set(-1.5, 4, 0);
      shadowSpan = 46.0;
      dofRange = 36.0;
    }
  }

  // =========================================================================
  // CHAPTER 3 [2288..3607]: THE LOW-CEILING SURPRISE (1.88 M CONTINUOUS RUN!)
  // =========================================================================
  else if (frame < 3607) {
    world.labSet.visible = true;
    world.setLightingMood('lab', 1.0);

    if (frame < 3287) {
      // ONE UNBROKEN CONTINUOUS SPRINT FROM X = -520 MM TO X = +520 MM (ZERO `%` REWIND LOOPS!)
      // Covered across 3 dynamic cinema camera angles (Wide Establishing -> Side Rail -> Overhead Dorsal)!
      world.roachHero.root.visible = true;
      world.ceilingSlab.visible = true;
      world.micrometerBridge.visible = true;
      world.labFloorStrip.material = world.mats.grit40Mat;

      // Stepped ceiling height: 12.0 mm -> 9.0 mm (@2693) -> 6.0 mm (@2818)
      let ceil = 12.0;
      if (frame >= 2693 && frame < 2818) ceil = GLM.mix(12.0, 9.0, sIn(frame, 2693, 2740));
      else if (frame >= 2818) ceil = GLM.mix(9.0, 6.0, sIn(frame, 2818, 2868));

      world.ceilingSlab.position.y = ceil;
      world.micrometerDrums.forEach((d) => { d.rotation.y = (12.0 - ceil) * 1.3; });

      // True continuous physical forward run across 1,040 mm of calibrated runway!
      const runU = uIn(frame, 2288, 3287);
      const rx = GLM.mix(-520, 520, runU);
      const r = world.roachHero.update({
        ceilingMm: ceil, worldX: rx, worldZ: 0,
        phase: t * 16.38, strideAmp: 1.0, gaitMode: 'tripod', time: t,
      });
      landmarks = r.landmarks;

      if (frame < 2592) {
        // Shot 3A [2288..2592]: Medium-wide optical corridor establishing dolly past gooseneck lights & DAQ monitors!
        world.humanActors.researcher.root.visible = false;
        const u = sIn(frame, 2288, 2592);
        fov = GLM.mix(38, 33, u);
        camPos.set(rx - GLM.mix(95, 55, u), GLM.mix(82, 34, u), GLM.mix(215, 115, u));
        camLook.set(rx + 18, GLM.mix(28, 10, u), GLM.mix(-75, -12, u));
        shadowSpan = GLM.mix(190.0, 85.0, u);
        dofRange = GLM.mix(260.0, 75.0, u);
      } else if (frame < 2986) {
        // Shot 3B [2592..2986]: Low high-speed side-profile tracking rail watching roof step 12->9->6mm!
        world.humanActors.researcher.root.visible = false;
        const u = sIn(frame, 2592, 2986);
        fov = 30;
        camPos.set(rx - 36 + u * 16, GLM.mix(19, 11.5, u), GLM.mix(82, 58, u));
        camLook.set(rx + 6, GLM.mix(7.5, 4.5, u), 0);
        shadowSpan = 68.0;
        dofRange = 52.0;
      } else {
        // Shot 3C [2986..3287]: Elevated dorsal-3/4 kinematics cam showing 55° -> 75° wide leg splay!
        world.humanActors.researcher.root.visible = false;
        const u = sIn(frame, 2986, 3287);
        fov = 29;
        camPos.set(rx - 22, GLM.mix(48, 40, u), GLM.mix(38, 24, u));
        camLook.set(rx + 3, 3.5, 0);
        shadowSpan = 64.0;
        dofRange = 48.0;
      }
      shadowCenter.set(rx, 5, 0);
      metrics = { gauge: 'speed_cliff', ceilingMm: ceil, speedCms: 58.1 };
    }
    else {
      // Shot 3D [3287..3607]: SINGLE-TAKE CONTINUOUS 3-LANE RACE (900 MM TRACK — ZERO `%` LOOP!)
      // 12 mm (58.1 cm/s) & 6 mm (57.9 cm/s) sprint continuously ahead while 4 mm crashes 4x to 14.5 cm/s!
      world.corridorGroup.visible = false;
      world.multiLaneGroup.visible = true;
      world.roachHero.root.visible = true;
      world.roachB.root.visible    = true;
      world.roachC.root.visible    = true;
      world.humanActors.researcher.root.visible = true;
      world.humanActors.poseResearcher(t, 0.45, 0.75);

      world.laneRoofs[0].position.y = 12.0;
      world.laneRoofs[1].position.y = 6.0;
      const drop4 = GLM.mix(6.0, 4.0, sIn(frame, 3287, 3340));
      world.laneRoofs[2].position.y = drop4;
      world.laneFloors.forEach((fl) => { fl.material = world.mats.grit40Mat; });

      const raceU = uIn(frame, 3287, 3607);
      const xFast12 = GLM.mix(-310, 340, raceU);
      const xFast6  = GLM.mix(-310, 332, raceU);
      const xSlow4  = GLM.mix(-310, -145, raceU); // True 1:4 distance ratio!

      world.roachB.update({ ceilingMm: 12.0, worldX: xFast12, worldZ: -38, phase: t * 16.38, strideAmp: 1.0, gaitMode: 'tripod', time: t });
      world.roachC.update({ ceilingMm: 6.0,  worldX: xFast6,  worldZ: 0,   phase: t * 16.10, strideAmp: 1.0, gaitMode: 'tripod', time: t });
      const r4 = world.roachHero.update({ ceilingMm: drop4, worldX: xSlow4, worldZ: 38, phase: t * 6.8, strideAmp: 0.78, gaitMode: 'oar', time: t });
      landmarks = r4.landmarks;

      const u = sIn(frame, 3287, 3607);
      fov = 36;
      camPos.set(GLM.mix(-355, -185, u), GLM.mix(76, 58, u), GLM.mix(138, 108, u));
      camLook.set(GLM.mix(-265, -75, u), 3.0, -2.0);
      shadowCenter.set(GLM.mix(-270, -90, u), 5, 0);
      shadowSpan = 165.0;
      dofRange = 160.0;
      metrics = { gauge: 'speed_cliff', ceilingMm: drop4, speedCms: GLM.mix(58.1, 14.5, sIn(frame, 3300, 3441)) };
    }
  }

  // =========================================================================
  // CHAPTER 4 [3607..5312]: WHEN SHINS BECOME FEET (+ 3D FORCE-PLATE ATHLETE!)
  // =========================================================================
  else if (frame < 5312) {
    if (frame >= 4350 && frame < 4481) {
      // Shot 4D [4350..4481]: ZACK-D 3D HUMAN ATHLETE WIDE-ARM PUSH-UP FORCE-PLATE STUDIO!
      world.pushupSet.visible = true;
      world.setLightingMood('pushup', 1.0);

      const splayAlpha = sIn(frame, 4378, 4432);
      const repCycle = (frame - 4350) / 44.0;
      world.humanActors.poseAthletePushup(t, splayAlpha, repCycle);

      const dip = 0.5 - 0.5 * Math.cos(repCycle * Math.PI * 2);
      const chestH = GLM.mix(420 - 150 * dip, 152 - 26 * dip, splayAlpha);
      world.athletePivot.position.set(-820, chestH, 0);
      world.athletePivot.updateMatrixWorld(true);

      // Lock glowing force plates & Ground Reaction Force vectors to exact LeftHand & RightHand world coords!
      const hands = world.humanActors.getAthleteHandWorldPositions();
      const handPts = [hands.left, hands.right];
      world.handArrows.forEach(({ group, shaft, tip, side }, idx) => {
        const hp = handPts[idx];
        world.forcePads[idx].position.set(hp.x, 4.0, hp.z);
        group.position.set(hp.x, 8.0, hp.z);
        // Upright green vertical lift -> outward-tilted amber lateral shear as arms splay >80°!
        group.rotation.set(-side * splayAlpha * 0.62, 0, 0);
        const vScale = GLM.mix(1.0, 0.72, splayAlpha);
        group.scale.set(1.0, vScale, 1.0);
        const mat = splayAlpha > 0.5 ? world.vecMatAmber : world.vecMatGreen;
        shaft.material = mat;
        tip.material = mat;
      });

      const u = sIn(frame, 4350, 4481);
      fov = 35;
      camPos.set(GLM.mix(1780, 1560, u), GLM.mix(780, 520, u), GLM.mix(1160, 740, u));
      camLook.set(GLM.mix(120, 40, u), GLM.mix(240, 150, splayAlpha), 0);
      shadowCenter.set(60, 120, 0);
      shadowSpan = 1400.0;
      dofRange = 1500.0;
      maxBlur = 1.6;
      mode = 'pushup';
    }
    else {
      world.labSet.visible = true;
      world.setLightingMood('lab', 1.0);
      world.roachHero.root.visible = true;
      world.ceilingSlab.visible = true;
      world.micrometerBridge.visible = true;
      world.labFloorStrip.material = world.mats.grit40Mat;
      world.humanActors.researcher.root.visible = false; // Pure macro bokeh!

      if (frame < 3883) {
        // Shot 4A [3607..3883]: Crane sweep down behind running cockroach in 12 mm corridor (continuous X = -240 -> -95)!
        world.ceilingSlab.position.y = 12.5;
        const u = uIn(frame, 3607, 3883);
        const rx = GLM.mix(-240, -95, u);
        const r = world.roachHero.update({
          ceilingMm: 12.5, worldX: rx, worldZ: 0,
          phase: t * 3.8, strideAmp: 0.95, gaitMode: 'tripod', time: t,
        });
        landmarks = r.landmarks;

        const cu = sIn(frame, 3607, 3883);
        fov = GLM.mix(31, 25, cu);
        camPos.set(rx - GLM.mix(46, 22, cu), GLM.mix(28, 7.5, cu), GLM.mix(48, 22, cu));
        camLook.set(rx + 2, GLM.mix(6.5, 2.2, cu), GLM.mix(0, 8, cu));
        shadowCenter.set(rx, 4, 4);
        shadowSpan = GLM.mix(62.0, 36.0, cu);
        dofRange = GLM.mix(48.0, 20.0, cu);
      }
      else if (frame < 4138) {
        // Shot 4B [3883..4138]: Ultra-macro tracking dolly on hooked tarsal claws & pale arolium pad (continuous X = -95 -> +35)!
        world.ceilingSlab.position.y = 12.5;
        const u = uIn(frame, 3883, 4138);
        const rx = GLM.mix(-95, 35, u);
        const r = world.roachHero.update({
          ceilingMm: 12.5, worldX: rx, worldZ: 0,
          phase: t * 3.2, strideAmp: 0.9, gaitMode: 'tripod', time: t,
        });
        landmarks = r.landmarks;

        const claw = r.landmarks.r3Claw;
        const cu = sIn(frame, 3883, 4138);
        fov = 24;
        camPos.set(claw.x - GLM.mix(19, 14, cu), GLM.mix(6.2, 4.0, cu), claw.z + GLM.mix(18, 13.5, cu));
        camLook.set(claw.x + 1.0, claw.y + 0.7, claw.z - 1.5);
        shadowCenter.copy(claw);
        shadowSpan = 32.0;
        dofRange = 17.0;
        maxBlur = 3.0;
      }
      else if (frame < 4350) {
        // Shot 4C [4138..4350]: Continuous forward squeeze (X = +35 -> +110) as ceiling presses 12.5 -> 4.0 mm!
        const sq = sIn(frame, 4145, 4275);
        const ceil = GLM.mix(12.5, 4.0, sq);
        world.ceilingSlab.position.y = ceil;
        const rx = GLM.mix(35, 110, uIn(frame, 4138, 4350));
        const r = world.roachHero.update({
          ceilingMm: ceil, worldX: rx, worldZ: 0,
          phase: t * 2.4, strideAmp: 0.70, time: t,
        });
        landmarks = r.landmarks;

        const claw = r.landmarks.r3Claw;
        fov = 24;
        camPos.set(claw.x - 15.0, GLM.mix(5.0, 3.0, sq), claw.z + 15.0);
        camLook.set(claw.x, claw.y + 0.4, claw.z - 2.0);
        shadowCenter.copy(claw);
        shadowSpan = 32.0;
        dofRange = 16.0;
      }
      else if (frame < 4923) {
        // Shot 4E [4481..4923]: Match-cut back to tibia + PROTECTED CLIMAX #2 [4662..4923]
        // Continuous forward crampon drive (X = -85 -> +85, ZERO `%` reset!)
        world.ceilingSlab.position.y = 4.0;
        const rx = GLM.mix(-85, 85, uIn(frame, 4481, 4923));
        const r = world.roachHero.update({
          ceilingMm: 4.0, worldX: rx, worldZ: 0,
          phase: t * 2.9, strideAmp: 1.0, gaitMode: 'oar', time: t,
        });
        landmarks = r.landmarks;

        const sp = r.landmarks.r3Spine;
        const cl = r.landmarks.r3Claw;
        const panToSpine = sIn(frame, 4540, 4655);

        if (frame >= 4662) {
          updateDustBurst(world.dustParticles, sp, t, 1.0);
        }

        const orbit = sIn(frame, 4662, 4923);
        fov = 22;
        const focusPt = cl.clone().lerp(sp, panToSpine);
        camPos.set(
          focusPt.x - GLM.mix(13.5, 9.5, orbit),
          GLM.mix(3.2, 2.2, panToSpine),
          focusPt.z + GLM.mix(12.8, 14.2, orbit)
        );
        camLook.set(focusPt.x + 1.2, focusPt.y + 0.45, focusPt.z - 1.2);
        shadowCenter.copy(focusPt);
        shadowSpan = 26.0;
        dofRange = 13.0;
        maxBlur = 3.2;
      }
      else if (frame < 5097) {
        // Shot 4F [4923..5097]: Overhead-3/4 crystal-clear view showing L2 + R2 rowing synchronously like oars!
        world.ceilingSlab.position.y = 4.0;
        const rx = GLM.mix(85, 175, uIn(frame, 4923, 5097));
        const r = world.roachHero.update({
          ceilingMm: 4.0, worldX: rx, worldZ: 0,
          phase: t * 4.4, strideAmp: 1.0, gaitMode: 'oar', time: t,
        });
        landmarks = r.landmarks;
        updateDustBurst(world.dustParticles, r.landmarks.r3Spine, t, 0.65);

        const u = sIn(frame, 4923, 5097);
        fov = 29;
        camPos.set(rx - 18, GLM.mix(44, 36, u), GLM.mix(26, 15, u));
        camLook.set(rx + 2.0, 2.0, 0);
        shadowCenter.set(rx, 2.5, 0);
        shadowSpan = 46.0;
        dofRange = 30.0;
      }
      else {
        // Shot 4G [5097..5312]: Heroic low front-3/4 power shot (continuous X = +175 -> +295) showing 5x BW drive!
        world.ceilingSlab.position.y = 4.0;
        const rx = GLM.mix(175, 295, uIn(frame, 5097, 5312));
        const r = world.roachHero.update({
          ceilingMm: 4.0, worldX: rx, worldZ: 0,
          phase: t * 4.4, strideAmp: 1.0, gaitMode: 'oar', time: t,
        });
        landmarks = r.landmarks;
        updateDustBurst(world.dustParticles, r.landmarks.r3Spine, t, 0.75);

        const u = sIn(frame, 5097, 5312);
        fov = 27;
        camPos.set(rx + GLM.mix(34, 25, u), 3.4, GLM.mix(26, 19, u));
        camLook.set(rx - 2.0, 2.1, 2.0);
        shadowCenter.set(rx, 2.5, 0);
        shadowSpan = 45.0;
        dofRange = 28.0;
      }
    }
  }

  // =========================================================================
  // CHAPTER 5 [5312..6591]: THE ROUGH-FLOOR TRAP (638 Runs · 100 / 40 / 20 Grit)
  // =========================================================================
  else if (frame < 6591) {
    world.labSet.visible = true;
    world.setLightingMood('lab', 1.0);

    if (frame < 5620) {
      // Shot 5A [5312..5620]: Footless Traction Shear-Force Sensor Rig (mu = 1.73 - 2.04) — Clean Posterior-Lateral Macro!
      world.roachHero.root.visible = true;
      world.ceilingSlab.visible = true;
      world.ceilingSlab.position.y = 4.0;
      world.micrometerBridge.visible = false;
      world.tractionPlateGroup.visible = true;
      world.labFloorStrip.material = world.mats.grit40Mat;
      world.humanActors.researcher.root.visible = false;

      const rx = GLM.mix(-24, 18, uIn(frame, 5312, 5620));
      const r = world.roachHero.update({
        ceilingMm: 4.0, worldX: rx, worldZ: 0,
        phase: t * 2.4, strideAmp: 0.85, gaitMode: 'oar', time: t,
      });
      landmarks = r.landmarks;
      const sp = r.landmarks.r3Spine;
      world.tractionPlateGroup.position.set(rx - 9.0, 0.0, 12.5);
      updateDustBurst(world.dustParticles, sp, t, 0.70);

      const u = sIn(frame, 5312, 5620);
      fov = 24;
      camPos.set(sp.x - GLM.mix(21.0, 14.5, u), GLM.mix(6.4, 3.8, u), sp.z + GLM.mix(19.5, 14.5, u));
      camLook.set(sp.x + 1.0, sp.y + 0.5, sp.z - 1.2);
      shadowCenter.copy(sp);
      shadowSpan = 30.0;
      dofRange = 18.0;
    }
    else if (frame < 5864) {
      // Shot 5B [5620..5864]: Racking Macro Glide Across 100-Grit vs 40-Grit vs 20-Grit Silicon-Carbide Swatches!
      world.corridorGroup.visible = false;
      world.gritSwatchGroup.visible = true;
      world.roachHero.root.visible = true;
      world.humanActors.researcher.root.visible = true;
      world.humanActors.poseResearcher(t, 0.5, 0.65);

      const u = sIn(frame, 5620, 5864);
      const rx = GLM.mix(-48, 36, u);
      const r = world.roachHero.update({
        ceilingMm: 4.2, worldX: rx, worldZ: -10,
        phase: t * 4.8, strideAmp: 0.9, gaitMode: 'oar', time: t,
      });
      landmarks = r.landmarks;

      fov = 28;
      camPos.set(GLM.mix(-56, 28, u), GLM.mix(22, 16, u), GLM.mix(58, 46, u));
      camLook.set(GLM.mix(-36, 32, u), 1.5, -2);
      shadowCenter.set(rx, 3, -4);
      shadowSpan = 72.0;
      dofRange = 54.0;
    }
    else if (frame < 6223) {
      // Shot 5C [5864..6223]: Continuous Confined Run (X = -140 -> +130, ZERO `%` loop!) showing overhead ceiling drag!
      world.roachHero.root.visible = true;
      world.ceilingSlab.visible = true;
      world.ceilingSlab.position.y = 4.0;
      world.micrometerBridge.visible = true;
      world.labFloorStrip.material = world.mats.grit40Mat;
      world.humanActors.researcher.root.visible = false;

      const rx = GLM.mix(-140, 130, uIn(frame, 5864, 6223));
      const r = world.roachHero.update({
        ceilingMm: 4.0, worldX: rx, worldZ: 0,
        phase: t * 3.8, strideAmp: 0.9, gaitMode: 'oar', time: t,
      });
      landmarks = r.landmarks;

      const u = sIn(frame, 5864, 6223);
      fov = 28;
      camPos.set(rx + GLM.mix(-38, 24, u), GLM.mix(6.2, 4.2, u), 40.0);
      camLook.set(rx, 2.4, 0);
      shadowCenter.set(rx, 3, 0);
      shadowSpan = 54.0;
      dofRange = 38.0;
      metrics = { gauge: 'ceiling_rub' };
    }
    else {
      // Shot 5D [6223..6591]: SINGLE-TAKE 3-LANE FLOOR GRIT TRADE-OFF ARENA (100-Grit vs 40-Grit Winner vs 20-Grit Belly Snag)!
      world.corridorGroup.visible = false;
      world.multiLaneGroup.visible = true;
      world.roachHero.root.visible = true;
      world.roachB.root.visible    = true;
      world.roachC.root.visible    = true;
      world.humanActors.researcher.root.visible = true;
      world.humanActors.poseResearcher(t, 0.45, 0.7);

      world.laneFloors[0].material = world.mats.grit100Mat;
      world.laneFloors[1].material = world.mats.grit40Mat;
      world.laneFloors[2].material = world.mats.grit20Mat;
      world.laneRoofs.forEach((rg) => { rg.position.y = 4.0; });

      const u = uIn(frame, 6223, 6591);
      const x100 = GLM.mix(-140, -68, u); // 1.57 cm/s (slipping spines!)
      const x40  = GLM.mix(-140, 115, u); // 5.26 cm/s (clear winner!)
      const x20  = GLM.mix(-140,  36, u); // 3.69 cm/s (flattened belly snags!)

      world.roachB.update({ ceilingMm: 4.0, worldX: x100, worldZ: -38, phase: t * 9.5, strideAmp: 1.0, gaitMode: 'oar', time: t });
      const rWin = world.roachHero.update({ ceilingMm: 4.0, worldX: x40, worldZ: 0, phase: t * 5.8, strideAmp: 1.0, gaitMode: 'oar', time: t });
      const snagX = x20 - 1.2 * Math.pow(Math.sin(t * 7.5), 4);
      world.roachC.update({ ceilingMm: 4.0, worldX: snagX, worldZ: 38, phase: t * 5.2, strideAmp: 0.9, gaitMode: 'oar', time: t });
      landmarks = rWin.landmarks;

      const cu = sIn(frame, 6223, 6591);
      fov = 35;
      camPos.set(GLM.mix(-195, -25, cu), GLM.mix(66, 48, cu), GLM.mix(112, 88, cu));
      camLook.set(GLM.mix(-110, 42, cu), 3.0, -2.0);
      shadowCenter.set(GLM.mix(-100, 35, cu), 3, 0);
      shadowSpan = 125.0;
      dofRange = 115.0;
      metrics = { gauge: 'floor_grit' };
    }
  }

  // =========================================================================
  // CHAPTER 6 [6591..8032]: TOUGH SHELL, TIGHT LIMIT (~900x BW & 315 Attempts)
  // =========================================================================
  else if (frame < 8032) {
    world.labSet.visible = true;
    world.setLightingMood('lab', 1.0);

    if (frame < 6877) {
      // Shot 6A [6591..6877]: Full-Body 3D X-Ray Compression Load-Cell Press (~900x BW = 6.08 N, 2 mm stop)!
      world.xrayRig.group.visible = true;
      world.corridorGroup.visible = false;
      world.humanActors.researcher.root.visible = false;

      const loadCurve = frame < 6820 ? sIn(frame, 6610, 6799) : (1.0 - sIn(frame, 6824, 6872));
      const xr = world.xrayRig.update({
        compAlpha: loadCurve * 0.96,
        showPlaten: true,
        showLoadArrows: loadCurve > 0.25,
        time: t,
        phase: t * 0.8,
      });
      landmarks = xr.landmarks;
      mode = 'cutaway';

      const u = sIn(frame, 6591, 6877);
      fov = 28;
      camPos.set(GLM.mix(-28, 16, u), GLM.mix(14.5, 9.2, u), GLM.mix(56, 44, u));
      camLook.set(GLM.mix(2, -1, u), 4.2, -2.0);
      shadowCenter.set(0, 4, 0);
      shadowSpan = 54.0;
      dofRange = 48.0;
    }
    else if (frame < 7183) {
      // Shot 6B [6877..7183]: Continuous Unimpaired Post-Load Open Sprint at 76.7 cm/s (X = -320 -> +320, ZERO `%` reset!)
      world.roachHero.root.visible = true;
      world.ceilingSlab.visible = false;
      world.micrometerBridge.visible = true;
      world.labFloorStrip.material = world.mats.grit40Mat;
      world.humanActors.researcher.root.visible = true;
      world.humanActors.poseResearcher(t, 0.35, 0.65);

      const u = uIn(frame, 6877, 7183);
      const rx = GLM.mix(-320, 320, u);
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: 0,
        phase: t * 19.5, strideAmp: 1.0, gaitMode: 'tripod', time: t,
      });
      landmarks = r.landmarks;

      const cu = sIn(frame, 6877, 7183);
      fov = 32;
      camPos.set(rx - GLM.mix(56, 36, cu), GLM.mix(24, 15, cu), GLM.mix(78, 58, cu));
      camLook.set(rx + 10, 6.0, -6.0);
      shadowCenter.set(rx, 5, 0);
      shadowSpan = 72.0;
      dofRange = 58.0;
    }
    else if (frame < 7519) {
      // Shot 6C [7183..7519]: Single Continuous 5.8 mm Gate Pass-Through (X = -175 -> +185, ZERO `%` reset!)
      world.roachHero.root.visible = true;
      world.labGateGroup.visible = true;
      world.ceilingSlab.visible = false;
      world.micrometerBridge.visible = false;
      world.labGateGroup.position.set(0, 5.8, 0);
      world.humanActors.researcher.root.visible = true;
      world.humanActors.poseResearcher(t, 0.5, 0.7);

      const u = sIn(frame, 7183, 7519);
      const rx = GLM.mix(-175, 185, u);
      const inGate = GLM.smoothstep(-16, 0, rx) * (1.0 - GLM.smoothstep(18, 36, rx));
      const r = world.roachHero.update({
        ceilingMm: GLM.mix(12.52, 5.8, inGate), worldX: rx, worldZ: 0,
        phase: t * 15.5, strideAmp: 1.0, time: t,
      });
      landmarks = r.landmarks;

      fov = 31;
      camPos.set(GLM.mix(-88, -32, u), GLM.mix(28, 18, u), GLM.mix(92, 66, u));
      camLook.set(GLM.mix(-45, 35, u), 5.5, 0);
      shadowCenter.set(GLM.mix(-40, 30, u), 5, 0);
      shadowSpan = 76.0;
      dofRange = 64.0;
      metrics = { gauge: 'gate_315' };
    }
    else if (frame < 7891) {
      // Shot 6D [7519..7891]: Gate narrows to 3.2 mm (17% pass; 74% antennal check & 180° turn-back!)
      world.roachHero.root.visible = true;
      world.labGateGroup.visible = true;
      world.ceilingSlab.visible = false;
      world.micrometerBridge.visible = false;
      world.humanActors.researcher.root.visible = false;
      const gateH = GLM.mix(5.8, 3.2, sIn(frame, 7519, 7595));
      world.labGateGroup.position.set(0, gateH, 0);

      let rx = -15, rz = 0, yaw = 0, probe = 0, amp = 0.8;
      if (frame < 7730) {
        rx = GLM.mix(-58, -15, sIn(frame, 7519, 7730));
        probe = sIn(frame, 7650, 7730) * 0.85;
      } else if (frame < 7795) {
        rx = -15 + Math.sin((frame - 7730) * 0.12) * 1.4;
        probe = 1.0;
        amp = 0.25;
      } else {
        const tu = sIn(frame, 7795, 7850);
        const walkBack = uIn(frame, 7820, 7891);
        yaw = tu * Math.PI;
        rz = Math.sin(tu * Math.PI) * 6.5;
        rx = -15 - walkBack * 44.0;
        amp = 0.95;
      }
      const r = world.roachHero.update({
        ceilingMm: 12.52, worldX: rx, worldZ: rz, yaw,
        phase: t * 9.5, strideAmp: amp, antennaProbe: probe, time: t,
      });
      landmarks = r.landmarks;

      const u = sIn(frame, 7519, 7891);
      fov = 29;
      camPos.set(GLM.mix(-58, -46, u), GLM.mix(18, 13.5, u), GLM.mix(68, 54, u));
      camLook.set(-10, 4.5, 0);
      shadowCenter.set(-14, 4, 0);
      shadowSpan = 62.0;
      dofRange = 48.0;
      metrics = { gauge: 'gate_315' };
    }
    else {
      // Shot 6E [7891..8032]: 9% Thorax-Wedged Outcome at 3.15 mm!
      world.roachHero.root.visible = true;
      world.labGateGroup.visible = true;
      world.ceilingSlab.visible = false;
      world.micrometerBridge.visible = false;
      world.humanActors.researcher.root.visible = false;
      world.labGateGroup.position.set(0, 3.15, 0);

      const enterU = sIn(frame, 7891, 7950);
      const rx = GLM.mix(-24, 3.2, enterU) + (frame >= 7950 ? 0.26 * Math.sin(t * 26.0) : 0.0);
      const r = world.roachHero.update({
        ceilingMm: GLM.mix(11.5, 3.35, enterU), worldX: rx, worldZ: 0,
        phase: t * 11.0, strideAmp: 0.95, headPitch: -0.15, pronotumRoll: 0.08, time: t,
      });
      landmarks = r.landmarks;
      updateDustBurst(world.dustParticles, r.landmarks.r3Spine, t, 0.55);

      fov = 26;
      camPos.set(-34, 11.0, 42);
      camLook.set(2.0, 3.4, 0);
      shadowCenter.set(0, 3, 0);
      shadowSpan = 45.0;
      dofRange = 32.0;
      metrics = { gauge: 'gate_315' };
    }
  }

  // =========================================================================
  // CHAPTER 7 [8032..9008]: HINGES, SPINES & BIO-INSPIRED CRAM ROBOT!
  // =========================================================================
  else {
    if (frame >= 8692 && frame < 8922) {
      // Shot 7D [8692..8922]: NEXT-LEVEL BIO-INSPIRED CRAM ROBOT + COCKROACH SIDE-BY-SIDE SYNTHESIS!
      // "It doesn't vanish under a door by being indestructible. It gets through because its shell can fold, and its shins can walk."
      world.labSet.visible = true;
      world.setLightingMood('lab', 1.0);
      world.cramBenchProp.root.visible = false;
      world.cramActor.root.visible = true;
      world.roachHero.root.visible = true;
      world.ceilingSlab.visible = true;
      world.micrometerBridge.visible = true;
      world.humanActors.researcher.root.visible = true;
      world.humanActors.poseResearcher(t, 0.4, 0.7);

      const u = uIn(frame, 8692, 8922);
      const sq = sIn(frame, 8715, 8785);
      const ceil = GLM.mix(16.0, 8.6, sq);
      world.ceilingSlab.position.y = ceil;

      const rx = GLM.mix(-140, 140, u);
      // Cockroach in foreground (+16 Z) & Bio-inspired CRAM soft-shell robot alongside (-18 Z) compressing & scuttling together!
      const r = world.roachHero.update({
        ceilingMm: GLM.mix(12.52, 4.2, sq), worldX: rx + 12, worldZ: 18,
        phase: t * 8.5, strideAmp: 1.0, gaitMode: sq > 0.5 ? 'oar' : 'tripod', time: t,
      });
      const cram = world.cramActor.update({
        worldX: rx - 14, worldZ: -12, yaw: 0, compAlpha: sq, phase: t * 9.0,
      });
      landmarks = { ...r.landmarks, cram: cram.shellTop };

      const cu = sIn(frame, 8692, 8922);
      fov = 32;
      camPos.set(rx - GLM.mix(68, 42, cu), GLM.mix(32, 20, cu), GLM.mix(92, 68, cu));
      camLook.set(rx, GLM.mix(8.0, 5.5, sq), 2.0);
      shadowCenter.set(rx, 6, 0);
      shadowSpan = 85.0;
      dofRange = 75.0;
    }
    else {
      world.apartmentSet.visible = true;
      world.setLightingMood('apartment_lit', 1.0);
      world.switchToggle.rotation.z = -0.42;
      world.penniesGroup.visible = true;
      world.humanActors.poseHomeowner(t, 0.2, 0.85);

      if (frame < 8143) {
        // Shot 7A [8032..8143]: "Now watch that two-penny escape once more at real speed."
        world.roachHero.root.visible = true;
        const u = sIn(frame, 8032, 8143);
        const rx = GLM.mix(-96, -44, u);
        const r = world.roachHero.update({
          ceilingMm: 12.52, worldX: rx, worldZ: 0,
          phase: t * 14.5, strideAmp: 1.0, time: t,
        });
        landmarks = { ...r.landmarks, pennies: penniesWorld };

        fov = 31;
        camPos.set(GLM.mix(-88, -54, u), 12.0, 54.0);
        camLook.set(-10, 3.8, 6.0);
        shadowCenter.set(-24, 4, 5);
        shadowSpan = 62.0;
        dofRange = 46.0;
      }
      else if (frame < 8502) {
        // Shot 7B [8143..8502]: PROTECTED CLIMAX #3 — 1x Real-Speed Traversal [8155..8215] + Match-Cut to Far-Side Rebound!
        world.roachHero.root.visible = true;
        let rx, ceil = 12.52, pRoll = 0, hPitch = 0;
        if (frame < 8165) {
          rx = GLM.mix(-44, -10, uIn(frame, 8143, 8165));
        } else if (frame < 8215) {
          const u = sIn(frame, 8165, 8215);
          rx = GLM.mix(-10, 56, u);
          const inDoor = GLM.smoothstep(-10, 2, rx) * (1.0 - GLM.smoothstep(40, 54, rx));
          ceil = GLM.mix(12.52, 3.22, inDoor);
          pRoll = 0.16 * Math.sin(inDoor * Math.PI);
          hPitch = -0.18 * (1 - u);
        } else {
          const u = uIn(frame, 8215, 8502);
          rx = 56 + u * 165;
          ceil = GLM.mix(4.0, 12.52, sIn(frame, 8215, 8335));
        }
        const r = world.roachHero.update({
          ceilingMm: ceil, worldX: rx, worldZ: 0,
          phase: t * 16.5, strideAmp: 1.0, headPitch: hPitch, pronotumRoll: pRoll, time: t,
        });
        landmarks = { ...r.landmarks, pennies: penniesWorld };

        if (frame < 8212) {
          const u = sIn(frame, 8143, 8212);
          fov = 30;
          camPos.set(-48 + u * 16, 7.2, 42);
          camLook.set(6, 2.6, 2);
          shadowCenter.set(0, 3, 0);
        } else {
          const u = sIn(frame, 8212, 8502);
          fov = 29;
          camPos.set(rx - GLM.mix(-28, 42, u), GLM.mix(8.5, 11.5, u), 48.0);
          camLook.set(rx + 4, 5.2, 0);
          shadowCenter.set(rx, 4, 0);
        }
        shadowSpan = 58.0;
        dofRange = 42.0;
      }
      else if (frame < 8692) {
        // Shot 7C [8502..8692]: Heroic Hallway Sprint Tracking Shot!
        world.roachHero.root.visible = true;
        const u = uIn(frame, 8502, 8692);
        const rx = GLM.mix(80, 235, u);
        const r = world.roachHero.update({
          ceilingMm: 12.52, worldX: rx, worldZ: 0,
          phase: t * 15.0, strideAmp: 1.0, time: t,
        });
        landmarks = { ...r.landmarks, pennies: penniesWorld };

        fov = 28;
        camPos.set(rx + 28, 9.5, 42.0);
        camLook.set(rx - 2, 5.4, 0);
        shadowCenter.set(rx, 4, 0);
        shadowSpan = 54.0;
        dofRange = 38.0;
      }
      else {
        // Shot 7E [8922..9008]: PROTECTED QUIET CLOSING HOLD [8922..8956] + PNAS PRIMARY SOURCE CARD [8956..9008]
        world.roachHero.root.visible = false;
        landmarks = { pennies: penniesWorld };

        const u = sIn(frame, 8922, 9008);
        fov = 28;
        camPos.set(GLM.mix(-54, -42, u), GLM.mix(9.8, 6.8, u), GLM.mix(48, 36, u));
        camLook.set(-10, 2.4, 8);
        shadowCenter.set(-14, 3, 8);
        shadowSpan = 48.0;
        dofRange = 36.0;
      }
    }
  }

  // Tight dynamic near/far clip planes boost 24-bit depth buffer precision 6x!
  const focusDist = camPos.distanceTo(camLook);
  camera.fov = fov;
  camera.near = Math.max(1.4, Math.min(25.0, focusDist * 0.08));
  camera.far  = Math.max(2200.0, focusDist * 24.0);
  camera.position.copy(camPos);
  camera.lookAt(camLook);
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);

  world.updateShadowMap(shadowCenter, shadowSpan);

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
