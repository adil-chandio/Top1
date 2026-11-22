import * as THREE from 'three';
import { GLM, createCinemaCameraRig } from '../../monarch-v6-imax-sdk/index.js';
import { directFrameV5 } from '../v5/director_v5.js';
import voiceLock from './long-voice-lock-v6-imax.json';

export const FPS = voiceLock.fps; // 30
export const TOTAL_FRAMES = voiceLock.total_frames; // 9008
export const ANCHORS = voiceLock.anchors;
export const PROTECTED_WINDOWS = voiceLock.protected_windows;

// Exact hard camera-cut frames in `directFrameV5` (strictly zeroes 180°-shutter `uMotionVec` across cuts!)
export const SHOT_CUTS_LONG_V6 = new Set([
  0, 145, 214, 330, 538,
  921, 1224, 1819,
  2288, 2592, 2986, 3287,
  3607, 3883, 4138, 4350, 4481, 4923, 5097,
  5312, 5620, 5864, 6223,
  6591, 6877, 7183, 7519, 7891,
  8032, 8143, 8212, 8502, 8692, 8922, 8956,
]);

export const CAMERA_IMPACTS_LONG_V6 = [
  { frame: 29,   amp: 4.20, decay: 0.26, freq: 2.10, durationFrames: 18 }, // Ivory wall switch snap
  { frame: 374,  amp: 0.48, decay: 0.22, freq: 1.85, durationFrames: 20 }, // Climax #1 hind-leg doorway shove
  { frame: 1585, amp: 0.58, decay: 0.22, freq: 1.90, durationFrames: 20 }, // 500fps Move 4 shove
  { frame: 1821, amp: 0.36, decay: 0.26, freq: 2.00, durationFrames: 18 }, // 3D Laser tomography ignite
  { frame: 2694, amp: 0.85, decay: 0.24, freq: 1.95, durationFrames: 18 }, // Roof step 12 -> 9 mm
  { frame: 2819, amp: 0.95, decay: 0.24, freq: 1.95, durationFrames: 18 }, // Roof step 9 -> 6 mm
  { frame: 3294, amp: 1.35, decay: 0.22, freq: 1.80, durationFrames: 22 }, // 4 mm compression speed cliff
  { frame: 4418, amp: 26.0, decay: 0.22, freq: 1.75, durationFrames: 24 }, // Athlete shoulder collapse (mm studio!)
  { frame: 4664, amp: 0.42, decay: 0.25, freq: 2.05, durationFrames: 18 }, // Climax #2 crampon strike
  { frame: 6415, amp: 0.85, decay: 0.24, freq: 1.90, durationFrames: 20 }, // 20-grit belly snag
  { frame: 6785, amp: 1.55, decay: 0.20, freq: 1.75, durationFrames: 26 }, // ~900x BW hydraulic platen slam!
  { frame: 6879, amp: 0.82, decay: 0.24, freq: 1.95, durationFrames: 18 }, // 76.7 cm/s post-load launch
  { frame: 7948, amp: 1.08, decay: 0.22, freq: 1.90, durationFrames: 22 }, // 9% thorax wedge jam
  { frame: 8166, amp: 0.52, decay: 0.24, freq: 1.90, durationFrames: 18 }, // Climax #3 real-speed launch
];

export function isProtectedFrame(frame) {
  return PROTECTED_WINDOWS.some(([a, b]) => frame >= a && frame < b);
}

const subU = (f, f0, f1) => GLM.clamp((f - f0) / Math.max(1, f1 - f0), 0, 1);

let cachedCamRig = null;
let cachedCamRef = null;
function getCamRig(camera) {
  if (!cachedCamRig || cachedCamRef !== camera) {
    cachedCamRef = camera;
    cachedCamRig = createCinemaCameraRig(camera, {
      totalFrames: TOTAL_FRAMES,
      shotCuts: SHOT_CUTS_LONG_V6,
      impacts: CAMERA_IMPACTS_LONG_V6,
    });
  }
  return cachedCamRig;
}

const tmpDir = new THREE.Vector3();

/**
 * Quaternion-verified Mixamo anatomical poses (`LeftShoulder`/`RightShoulder` rest basis):
 *   - `rx = +1.18..+1.26` drops both upper arms cleanly down along the ribcage (`world -Y`)
 *   - `LeftArm rz > 0` / `RightArm rz < 0` swings upper arms forward (`actor +X`)
 *   - `LeftForeArm rz > 0` / `RightForeArm rz < 0` bends elbows naturally forward!
 */
function poseHomeownerV6(actor, time, reachAmt = 0.0, lookDownAmt = 0.0) {
  actor.resetAll();
  const breath = 0.022 * Math.sin(time * 2.4);

  // Relaxed left arm hanging naturally beside torso
  actor.setBoneDelta('LeftArm', 1.26, 0.0, 0.08 + 0.14 * lookDownAmt);
  actor.setBoneDelta('LeftForeArm', 0.0, 0.0, 0.32 + 0.22 * lookDownAmt);

  // Ergonomic chest-height reach to ivory wall toggle switch (no horizontal T-pose salute!)
  actor.setBoneDelta('RightArm', 1.22 - 0.30 * reachAmt, 0.0, -0.10 - 0.48 * reachAmt);
  actor.setBoneDelta('RightForeArm', 0.0, 0.0, -0.28 - 0.62 * reachAmt);
  actor.setBoneDelta('RightHand', 0.0, 0.0, -0.16 * reachAmt);

  actor.setBoneDelta('Spine1', 0.16 * lookDownAmt + breath, 0.05 * (1 - lookDownAmt), 0);
  actor.setBoneDelta('Spine2', 0.18 * lookDownAmt, 0, 0);
  actor.setBoneDelta('Neck', 0.24 * lookDownAmt, -0.08 * reachAmt, 0);
  actor.setBoneDelta('Head', 0.30 * lookDownAmt, -0.06 * reachAmt + 0.03 * Math.sin(time * 3.1), 0);
}

function poseResearcherV6(actor, time, dialReach = 0.5, inspectTilt = 0.5) {
  actor.resetAll();
  const breath = 0.02 * Math.sin(time * 2.1);

  actor.setBoneDelta('Spine1', 0.14 * inspectTilt + breath, 0, 0);
  actor.setBoneDelta('Spine2', 0.16 * inspectTilt, 0, 0);
  actor.setBoneDelta('Neck', 0.20 * inspectTilt, 0.05 * Math.sin(time * 0.9), 0);
  actor.setBoneDelta('Head', 0.22 * inspectTilt, 0.04 * Math.cos(time * 1.1), 0);

  // Both upper arms dropped naturally down along ribcage, forearms poised over optical bench & dial!
  actor.setBoneDelta('LeftArm', 1.20, 0.0, 0.34);
  actor.setBoneDelta('LeftForeArm', 0.0, 0.0, 0.92);

  const wristMicro = 0.14 * Math.sin(time * 3.8) * dialReach;
  actor.setBoneDelta('RightArm', 1.16, 0.0, -0.34 - 0.16 * dialReach);
  actor.setBoneDelta('RightForeArm', 0.0, 0.0, -0.88 - 0.20 * dialReach);
  actor.setBoneDelta('RightHand', wristMicro, 0.0, -0.12);
}

/**
 * Monarch Cam #03 — V6 Hollywood IMAX Master Director (9,008 frames = 300.27s @ 30.000 fps)
 * Builds on V5's verified 32-shot blocking & zero-loop kinematics, elevating every frame with:
 *   - Volumetric Moonlight Shafts (`[0..28]`), Warm Tungsten Doorway Light-Blade + 130 Tyndall Dust Motes,
 *     and 4 Overhead Surgical Volumetric Lab Cones + 90 Floating Lab Dust Motes
 *   - 3D Holographic Cyan Laser Tomography Curtain (`[1819..1895]`) & Emerald Floor-Clearance Grid (`[4145..4350]`)
 *   - Newtonian Parabolic Ballistic Grit & Sparks (replacing simple sine-arc dust) + Radial Shockwave Rings
 *   - Newtonian Gravitational Athlete Collapse + Restitution Bounce (`[4404..4456]`)
 *   - Cinema Camera Dynamics: 14 Damped Impact Shakes, Dutch Banking, Vertigo Counter-Zooms & 180° Shutter Blur
 *   - Creamy 12-Tap Vogel Bokeh Backdrop on `[8956..9008]` behind the Frosted-Obsidian PNAS End Card!
 */
export function directFrameLongV6(world, camera, frame) {
  const time = frame / FPS;
  const camRig = getCamRig(camera);

  // Reset V6 VFX cleanly before base V5 blocking (so volumetric cones never cast opaque shadows!)
  world.moonlightGroup.visible = false;
  world.doorwayVfx.visible = false;
  world.labLightCones.visible = false;
  if (world.studioCones) world.studioCones.visible = false;
  world.penniesGroup.position.set(-24.0, 0.0, -17.5);
  world.penniesGroup.rotation.set(0, 0, 0);
  world.resetVfxPerFrame();

  // 1. Evaluate verified 32-shot V5 kinematics, world visibility, shadow map & base camera pose
  const v5 = directFrameV5(world, camera, frame);
  const landmarks = { ...v5.landmarks };

  // Replace V5's old 48-particle sine-arc dust with our 96-particle Newtonian Parabolic Ballistic Grit!
  const hadV5Dust = world.dustParticles.visible;
  world.dustParticles.visible = false;

  // Recover base camera position, lookAt target, and lens parameters from V5
  const camPos = camera.position.clone();
  camera.getWorldDirection(tmpDir);
  const baseFocusDist = v5.lensParams.focusDist;
  const camLook = camPos.clone().addScaledVector(tmpDir, baseFocusDist);

  let fov = camera.fov;
  let dofRange = v5.lensParams.dofRange;
  let maxBlur = Math.max(2.6, v5.lensParams.maxBlur * 1.32); // Richer 12-tap Vogel cinema bokeh!
  let bloomAmt = 0.42;
  let exposure = 1.22;
  let dutchDeg = 0.0;
  let shutterBlurScale = 0.36;
  let extraMotionX = 0.0;
  let hudTag = '';
  let hudMetric = '';
  let hudAlert = false;

  // Subtle ~0.34 Hz organic cinema Steadicam / macro-probe breathing (scaled safely to focus distance)
  const breathScale = GLM.clamp(baseFocusDist * 0.0022, 0.04, 1.4);
  camPos.y += breathScale * Math.sin(time * 2.15);
  camPos.z += breathScale * 0.7 * Math.cos(time * 1.65);

  // =========================================================================
  // LAYER V6 VOLUMETRIC LIGHTING, LASER VFX, NEWTONIAN PHYSICS & TELEMETRY
  // =========================================================================
  if (frame < 921) {
    if (frame < 62) {
      const reach = frame < 29
        ? GLM.smoothstep(2, 24, frame) * (1 - 0.15 * GLM.smoothstep(24, 29, frame))
        : (1 - GLM.smoothstep(29, 54, frame)) * 0.85;
      const lookDown = frame < 29 ? GLM.smoothstep(22, 29, frame) * 0.22 : 0.22 + 0.78 * GLM.smoothstep(29, 60, frame);
      poseHomeownerV6(world.humanActors.homeowner, time, reach, lookDown);
      world.humanActors.homeowner.root.updateMatrixWorld(true);
    }
    if (frame < 29) {
      // [0..29] 2:14 AM Silver-Blue Volumetric Moonlight Shafts (luma-safe > 20!)
      world.setLightingMoodV6('midnight_dark');
      world.moonlightGroup.visible = true;
      exposure = 1.42;
      bloomAmt = 0.48;
      hudTag = 'CH 01 · 02:14 AM HALLWAY';
      hudMetric = 'DOOR CLEARANCE 3.20 MM';
    } else {
      world.setLightingMoodV6('apartment_warm');
      world.doorwayVfx.visible = true;
      world.doorwayMotes.update(time);
      bloomAmt = 0.48;

      if (frame < 145) {
        // Whip-boom dive from wall switch to sprinting cockroach: Dutch banking + 180° shutter blur!
        const diveU = subU(frame, 29, 112);
        dutchDeg = -3.4 * Math.sin(Math.PI * diveU);
        shutterBlurScale = 0.52;
        hudTag = 'CH 01 · ESCAPE SPRINT';
        hudMetric = 'STANDING 12.5 MM';
      } else if (frame < 214) {
        hudTag = 'CH 01 · FREE-STANDING PROFILE';
        hudMetric = '12.5 MM (~0.5 INCH)';
      } else if (frame < 330) {
        hudTag = 'CH 01 · SCALE CALIBRATION';
        hudMetric = '2 US PENNIES = 3.04 MM';
      } else if (frame < 538) {
        // PROTECTED CLIMAX #1 [330..538]: Sympathetic penny micro-tremor + Newtonian oak-dust burst!
        bloomAmt = 0.52;
        const shoveEnv = Math.sin(Math.PI * subU(frame, 373, 462));
        if (shoveEnv > 0.02 && landmarks.r3Spine) {
          world.penniesGroup.position.y = 0.06 * shoveEnv * Math.abs(Math.sin(time * 50.0));
          world.penniesGroup.rotation.z = 0.012 * shoveEnv * Math.sin(time * 44.0);
          world.ballisticGrit.update(landmarks.r3Spine, time, {
            intensity: shoveEnv * 0.92,
            speedScale: 1.15,
            dirSign: -1.0,
          });
        }
      } else {
        // [538..921] "Wait a second..." Hitchcock Vertigo Counter-Zoom + Bullet-Time Orbit!
        const vertU = GLM.easeOutQuint(subU(frame, 538, 615));
        fov = fov + 4.2 * Math.sin(vertU * Math.PI * 0.5);
        dutchDeg = 1.6 * Math.sin(subU(frame, 538, 921) * Math.PI);
        bloomAmt = 0.50;
        hudTag = 'CH 01 · PARADOX FREEZE';
        hudMetric = '47% SHELL COMPRESSION';
      }
    }
  } else if (frame < 2288) {
    world.labLightCones.visible = true;
    world.labMotes.update(time);

    if (frame < 1224) {
      world.setLightingMoodV6('berkeley_lab');
      const dialReach = GLM.smoothstep(990, 1135, frame) * (1 - 0.35 * GLM.smoothstep(1155, 1218, frame));
      poseResearcherV6(world.humanActors.researcher, time, dialReach, 0.38 + 0.32 * GLM.smoothstep(960, 1170, frame));
      world.humanActors.researcher.root.updateMatrixWorld(true);
      hudTag = 'CH 02 · UC BERKELEY POLY-PEDAL LAB';
      hudMetric = '500 FPS · 3.20 MM GATE';
    } else if (frame < 1819) {
      world.setLightingMoodV6('berkeley_lab');
      // Move 4 [1583..1726]: Planted hind legs fire Newtonian ballistic silicon-carbide grit!
      if (frame >= 1583 && frame <= 1726 && landmarks.r3Spine) {
        const shoveAmt = Math.sin(Math.PI * subU(frame, 1583, 1726));
        world.ballisticGrit.update(landmarks.r3Spine, time, {
          intensity: shoveAmt * 0.90,
          speedScale: 0.78,
          dirSign: -1.0,
        });
      }
      hudTag = 'CH 02 · 500 FPS SLOT KINEMATICS';
      hudMetric = 'TRAVERSAL 288 - 821 MS';
    } else {
      // [1819..2288] 3D Holographic Cyan Laser Tomography Curtain + Surgical X-Ray Cutaway!
      world.setLightingMoodV6('xray_surgical');
      world.labLightCones.visible = false;
      exposure = 1.26;
      bloomAmt = 0.52;

      // Hide steel hydraulic press shaft in Ch 02D (saved for Ch 06A ~900x press!) and show clean acrylic roof!
      let comp = 0.0;
      if (frame < 2198) comp = GLM.smoothstep(1850, 2145, frame);
      else comp = 1.0 - GLM.smoothstep(2202, 2278, frame);
      const xr = world.xrayRig.update({
        compAlpha: comp,
        showPlaten: false,
        showLoadArrows: false,
        time,
        phase: time * 1.4,
      });
      world.corridorGroup.visible = true;
      world.ceilingSlab.visible = true;
      world.ceilingSlab.position.y = Math.max(3.35, xr.peakY + 0.36);
      world.micrometerBridge.visible = false;
      Object.assign(landmarks, xr.landmarks);

      if (frame < 1898) {
        const scanU = subU(frame, 1819, 1898);
        world.xrayScanner.visible = true;
        world.xrayScanner.position.set(GLM.mix(18.0, -20.0, scanU), 0.0, 0.0);
      }
      hudTag = 'CH 02 · 3D X-RAY CUTAWAY';
      hudMetric = frame < 2198 ? 'ARTHRODIAL HINGE FOLD' : 'VISCOELASTIC REBOUND';
    }
  } else if (frame < 3607) {
    world.setLightingMoodV6('berkeley_lab');
    world.labLightCones.visible = true;
    world.labMotes.update(time);

    if (frame < 3287) {
      let ceil = 12.0;
      if (frame >= 2693 && frame < 2818) ceil = 9.0;
      else if (frame >= 2818) ceil = 6.0;
      if (frame >= 2961 && frame <= 3020) {
        // "It didn't." subtle Vertigo punch-in!
        fov += 2.6 * Math.sin(subU(frame, 2961, 3020) * Math.PI);
      }
      shutterBlurScale = 0.44;
      hudTag = 'CH 03 · CONFINED CORRIDOR';
      hudMetric = `ROOF ${ceil.toFixed(1)} MM · ~58 CM/S`;
    } else {
      // [3287..3607] 3-Lane Speed Cliff: Radial cyan shockwave when Lane 3 drops to 4.0 mm!
      if (frame >= 3294 && frame <= 3328) {
        world.shockwave.trigger({
          x: -290, y: 0.22, z: 38, size: 62.0,
          progress: subU(frame, 3294, 3328), colorHex: '#7efcf4',
        });
      }
      hudTag = 'CH 03 · BODY-COMPRESSION CLIFF';
      hudMetric = '4.0 MM = 14.5 CM/S (-75%)';
      hudAlert = true;
    }
  } else if (frame < 5312) {
    if (frame >= 4350 && frame < 4481) {
      // Shot 4D [4350..4481]: 3D Athlete Splayed Push-Up + Newtonian Restitution Bounce & Shockwave!
      world.setLightingMoodV6('zackd_studio');
      if (world.studioCones) world.studioCones.visible = true;
      exposure = 1.24;
      bloomAmt = 0.46;
      if (frame >= 4418 && frame <= 4456) {
        const bT = (frame - 4418) / FPS;
        const bounceMm = 44.0 * Math.exp(-bT * 8.5) * Math.abs(Math.sin(bT * 18.0));
        world.athletePivot.position.y += bounceMm;
        world.athletePivot.updateMatrixWorld(true);
        world.shockwave.trigger({
          x: 60, y: 10.0, z: 0, size: 1250.0,
          progress: subU(frame, 4418, 4456), colorHex: '#ffa84c',
        });
      }
      const hands = world.humanActors.getAthleteHandWorldPositions();
      landmarks.athleteHand = hands.right.clone().add(new THREE.Vector3(0, 75, 0));
      hudTag = 'CH 04 · FORCE-PLATE BIOMECHANICS';
      hudMetric = frame >= 4405 ? 'SPLAY > 80° · GRIP FAILS' : 'VERTICAL PALM LEVERAGE';
      hudAlert = frame >= 4405;
    } else {
      world.setLightingMoodV6('macro_warm');
      world.labLightCones.visible = true;
      world.labMotes.update(time);
      bloomAmt = 0.46;

      if (frame < 4138) {
        hudTag = 'CH 04 · OPEN-SPACE FOOTWORK';
        hudMetric = 'HOOKED CLAWS + AROLIUM PAD';
      } else if (frame < 4350) {
        // Shot 4C [4138..4350]: Emerald Floor-Clearance Optical Laser Grid under lifted claws!
        const sq = GLM.smoothstep(4145, 4275, frame);
        if (sq > 0.35 && landmarks.r3Claw) {
          world.clearanceLaser.visible = true;
          world.clearanceLaser.position.set(landmarks.r3Claw.x, 0.09, landmarks.r3Claw.z * 0.7);
          world.clearanceLaser.material.uniforms.uTime.value = time;
          world.clearanceLaser.material.uniforms.uAlpha.value = GLM.smoothstep(0.35, 0.92, sq) * 0.62;
        }
        hudTag = 'CH 04 · >80° FEMUR SPLAY';
        hudMetric = sq > 0.6 ? 'CLAWS +0.47 MM OFF FLOOR' : 'PRESSING TO 4.0 MM';
        hudAlert = sq > 0.6;
      } else if (frame < 4662) {
        hudTag = 'CH 04 · CONTACT HANDOFF';
        hudMetric = 'TIBIAL CRAMPON SPINES';
      } else if (frame < 4923) {
        // PROTECTED CLIMAX #2 [4662..4923]: Newtonian Parabolic Silicon-Carbide Grit & Spark Engine!
        bloomAmt = 0.50;
        if (landmarks.r3Spine) {
          world.ballisticGrit.update(landmarks.r3Spine, time, {
            intensity: 0.96,
            speedScale: 1.12,
            dirSign: -1.0,
          });
        }
      } else {
        if (hadV5Dust && landmarks.r3Spine) {
          world.ballisticGrit.update(landmarks.r3Spine, time, {
            intensity: 0.72,
            speedScale: 1.25,
            dirSign: -1.0,
          });
        }
        hudTag = 'CH 04 · SYNCHRONOUS OAR DRIVE';
        hudMetric = 'THRUST ~5x BODY WEIGHT';
      }
    }
  } else if (frame < 6591) {
    world.setLightingMoodV6('berkeley_lab');
    world.labLightCones.visible = true;
    world.labMotes.update(time);

    if (hadV5Dust && landmarks.r3Spine) {
      world.ballisticGrit.update(landmarks.r3Spine, time, {
        intensity: 0.68,
        speedScale: 0.95,
        dirSign: -1.0,
      });
    }
    if (frame < 5620) {
      hudTag = 'CH 05 · FOOTLESS TRACTION RIG';
      hudMetric = 'FRICTION COEFF 1.73 - 2.04';
    } else if (frame < 5864) {
      hudTag = 'CH 05 · SUBSTRATE ARRAYS';
      hudMetric = '100 · 40 · 20 GRIT SILICON CARBIDE';
    } else if (frame < 6223) {
      hudTag = 'CH 05 · 638 CONFINED RUNS';
      hudMetric = 'ROUGHER ROOF SLOWS SPEED';
    } else {
      hudTag = 'CH 05 · FLOOR GRIT TRADE-OFF';
      hudMetric = '40-GRIT WINS (5.26 CM/S)';
      hudAlert = frame >= 6413;
    }
  } else if (frame < 8032) {
    if (frame < 6877) {
      // Shot 6A [6591..6877]: ~900x Body-Weight Hydraulic Load-Cell Press + Golden Platen Shockwave!
      world.setLightingMoodV6('xray_surgical');
      exposure = 1.26;
      bloomAmt = 0.52;
      const loadCurve = frame < 6820 ? GLM.smoothstep(6610, 6799, frame) : (1.0 - GLM.smoothstep(6824, 6872, frame));
      if (frame >= 6784 && frame <= 6818) {
        world.shockwave.trigger({
          x: -1.2, y: 0.22, z: 0, size: 68.0,
          progress: subU(frame, 6784, 6818), colorHex: '#ffd187',
        });
      }
      const bwMult = Math.round(loadCurve * 896);
      hudTag = 'CH 06 · COMPRESSION LOAD CELL';
      hudMetric = loadCurve > 0.12 ? `${(loadCurve * 6.08).toFixed(2)} N (~${bwMult}x BW)` : 'SHELL RECOVERY < 80 MS';
      hudAlert = bwMult > 700;
    } else {
      world.setLightingMoodV6('berkeley_lab');
      world.labLightCones.visible = true;
      world.labMotes.update(time);
      if (frame < 7183) {
        dutchDeg = -1.6;
        shutterBlurScale = 0.54;
        extraMotionX = -0.0045;
        hudTag = 'CH 06 · POST-LOAD SPRINT';
        hudMetric = '76.7 CM/S UNIMPAIRED';
      } else if (frame < 7519) {
        hudTag = 'CH 06 · 315 GATE TRIALS';
        hudMetric = '5.8 MM GAP · 72% PASS';
      } else {
        if (hadV5Dust && landmarks.r3Spine) {
          world.ballisticGrit.update(landmarks.r3Spine, time, {
            intensity: 0.55,
            speedScale: 1.0,
            dirSign: -1.0,
          });
        }
        if (frame >= 7946 && frame <= 7980) {
          world.shockwave.trigger({
            x: 2.0, y: 0.20, z: 0, size: 46.0,
            progress: subU(frame, 7946, 7980), colorHex: '#ff7a66',
          });
        }
        hudTag = 'CH 06 · 3.15 MM HARD LIMIT';
        hudMetric = '83% FAIL (74% TURN · 9% WEDGED)';
        hudAlert = true;
      }
    }
  } else {
    if (frame >= 8692 && frame < 8922) {
      // Shot 7D [8692..8922]: Bio-Inspired CRAM Robot + Cockroach Side-by-Side!
      world.setLightingMoodV6('berkeley_lab');
      world.labLightCones.visible = true;
      world.labMotes.update(time);
      hudTag = 'CH 07 · BIO-INSPIRED CRAM ROBOT';
      hudMetric = '75 TO 35 MM ORIGAMI SHELL';
    } else {
      world.setLightingMoodV6('apartment_warm');
      world.doorwayVfx.visible = true;
      world.doorwayMotes.update(time);
      bloomAmt = 0.50;

      if (frame < 8143) {
        hudTag = 'CH 07 · REAL-SPEED REPRISE';
        hudMetric = '1.0X NATURAL SPEED';
      } else if (frame >= 8502 && frame < 8692) {
        shutterBlurScale = 0.44;
        hudTag = 'CH 07 · BIOMECHANICAL SYNTHESIS';
        hudMetric = 'FOLDING PLATES + TIBIAL SPINES';
      } else if (frame >= 8956) {
        // Creamy 12-tap Vogel Bokeh golden doorway backdrop behind Frosted-Obsidian PNAS End Card!
        dofRange = 8.0;
        maxBlur = 5.4;
        bloomAmt = 0.54;
        exposure = 1.08;
      }
    }
  }

  // Strictly enforce 100% zero HUD telemetry inside all 4 Protected Windows & PNAS End Card!
  if (isProtectedFrame(frame) || frame >= ANCHORS.ch7_pnas_start) {
    hudTag = '';
    hudMetric = '';
    hudAlert = false;
  }

  // Apply Newtonian Cinema Camera Rig (impact shakes, Dutch banking, 180°-shutter velocity blur!)
  const rigOut = camRig.apply({
    frame,
    pos: camPos,
    look: camLook,
    fov,
    dutchDeg,
    breathAmp: 0.0,
    shutterBlurScale,
    extraMotionX,
  });

  return {
    frame,
    time,
    protectedWindow: isProtectedFrame(frame),
    focusDist: rigOut.focusDist,
    dofRange,
    maxBlur,
    bloomAmt,
    exposure,
    motionVec: rigOut.motionVec,
    hudTag,
    hudMetric,
    hudAlert,
    anchors: landmarks,
  };
}
