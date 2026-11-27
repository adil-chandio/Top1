import * as THREE from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import {
  GLM,
  createBallisticParticleSystem,
  createCinemaCameraRig,
  createLoopLockedDustMotes,
  createVolumetricSpotlightCone,
} from '/tools/monarch-v6-imax-sdk/index.js';

/**
 * Logan — Rig-to-Render VFX Breakdown (`V6.2 Hollywood IMAX`)
 * Virtual Cinema Director (`420` frames = `14.000s` @ `30.000 fps`, seamless infinite loop):
 *   - 4 Iconic Viewport-Clay-Rig -> Final-Chiaroscuro-Render Match-Cut Pairs + Loop Reset
 *   - Analytical Quaternion-Verified Arm/Finger/Claw & 51-Blendshape Facial Choreography
 *   - Dual Studio Viewport / Rembrandt Chiaroscuro Lighting + Volumetric Haze & Ballistic Sparks
 */

export const TOTAL_FRAMES = 420;
export const FPS = 30;
export const SHOT_CUTS_LOGAN_V6 = new Set([0, 87, 132, 168, 210, 252, 294, 336, 393]);

// Solved exact FK bone deltas (verified in live Three.js on synchronized 3-skeleton `bruce.glb`):
const POSE_REST_R = {
  clavicle_r: [ 0.0018, -0.0079, -0.0610],
  upperarm_r: [ 0.2435, -0.1266, -0.4541],
  lowerarm_r: [-0.0162,  0.3924, -0.0943],
  hand_r:     [ 0.0000,  0.0000,  0.0000],
};

// Mid-arc lift across lower ribs so elbow sweeps naturally in front of torso (never clipping chest!)
const POSE_MID_R = {
  clavicle_r: [ 0.0000, -0.0360, -0.0880],
  upperarm_r: [ 0.3750, -0.3750, -0.2950],
  lowerarm_r: [-0.0350, -0.5800, -0.0920],
  hand_r:     [-0.5200,  0.2600, -0.0040],
};

// Hero chest pose (`hand_r` at `[-0.041, 1.437, +0.278]`, claws sweeping +46.5 deg up-right to `[+0.145, 1.631, +0.314]`!)
const POSE_CHEST_R = {
  clavicle_r: [-0.0011, -0.0589, -0.1051],
  upperarm_r: [ 0.4514, -0.5505, -0.1660],
  lowerarm_r: [-0.0479, -1.2976, -0.0884],
  hand_r:     [-1.0508,  0.4903, -0.0065],
};

const POSE_REST_L = {
  clavicle_l: [ 0.0018, -0.0074, -0.0638],
  upperarm_l: [ 0.2555, -0.1345, -0.4497],
  lowerarm_l: [-0.0188,  0.3945, -0.0893],
  hand_l:     [ 0.0000,  0.0000,  0.0000],
};

function lerp3(a, b, t) {
  return [
    GLM.mix(a[0], b[0], t),
    GLM.mix(a[1], b[1], t),
    GLM.mix(a[2], b[2], t),
  ];
}

export function createLoganLightingAndVfx(scene, renderer) {
  // Subtle neutral studio IBL for metallic blade reflections & eye catchlights
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envTex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environment = envTex;

  const hemiLight = new THREE.HemisphereLight('#9aa4b2', '#282c32', 0.65);
  scene.add(hemiLight);

  // Primary Key Light (`2048x2048` soft shadow map)
  const keyLight = new THREE.DirectionalLight('#ffd0a2', 3.4);
  keyLight.position.set(-1.15, 2.68, 1.42);
  keyLight.target.position.set(0.0, 1.55, 0.05);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(2048, 2048);
  keyLight.shadow.camera.near = 0.4;
  keyLight.shadow.camera.far = 6.5;
  keyLight.shadow.camera.left = -0.85;
  keyLight.shadow.camera.right = 0.85;
  keyLight.shadow.camera.top = 0.95;
  keyLight.shadow.camera.bottom = -0.85;
  keyLight.shadow.bias = -0.00045;
  keyLight.shadow.normalBias = 0.008;
  scene.add(keyLight, keyLight.target);

  // Fill Light
  const fillLight = new THREE.DirectionalLight('#9e4e34', 0.52);
  fillLight.position.set(1.15, 1.25, 1.55);
  fillLight.target.position.set(0.0, 1.55, 0.05);
  scene.add(fillLight, fillLight.target);

  // Cold Steel-Cyan Rim Kicker (grazing hair, shoulders, knuckles & Adamantium bevels!)
  const rimLight = new THREE.DirectionalLight('#74daff', 3.15);
  rimLight.position.set(1.32, 2.25, -1.28);
  rimLight.target.position.set(0.0, 1.55, 0.05);
  scene.add(rimLight, rimLight.target);

  // Dedicated Cold Blade & Eye Catchlight Kicker
  const bladeKicker = new THREE.DirectionalLight('#d6f0ff', 1.25);
  bladeKicker.position.set(0.52, 1.92, 1.35);
  bladeKicker.target.position.set(0.02, 1.52, 0.18);
  scene.add(bladeKicker, bladeKicker.target);

  // Subtle Dark Studio Backdrop Volumetric Cone (`visible = false` in Clay mode!)
  const studioVolCone = createVolumetricSpotlightCone({
    color: '#5ca8d6',
    intensity: 0.095,
    topRadius: 0.22,
    bottomRadius: 0.95,
    height: 2.35,
    renderOrder: 21,
  });
  studioVolCone.position.set(0.18, 1.55, -0.78);
  studioVolCone.rotation.z = -0.18;
  studioVolCone.castShadow = false;
  scene.add(studioVolCone);

  // Pinpoint Tyndall Dust Motes strictly behind character (`z = -0.65 .. -0.18` -> zero near-lens blobs!)
  const dustMotes = createLoopLockedDustMotes({
    count: 68,
    radius: 0.0014,
    color: '#b8dcf2',
    loopDurationS: TOTAL_FRAMES / FPS,
    bounds: { x0: -0.48, xSpan: 0.96, y0: 1.02, ySpan: 1.05, z0: -0.62, zSpan: 0.42 },
    renderOrder: 24,
  });
  // Override internal meter-scale drift amplitude cleanly via small group scale around backdrop
  dustMotes.mesh.scale.setScalar(0.08);
  dustMotes.mesh.position.set(0.0, 1.48, -0.36);
  scene.add(dustMotes.mesh);

  // Newtonian Metallic Micro-Sparks on `f=87` SNIKT! claw eruption
  const sniktSparks = createBallisticParticleSystem({
    count: 42,
    radius: 0.0018,
    color: '#e8f6ff',
    gravity: 6.8,
    restitution: 0.35,
    floorY: 0.65,
  });
  scene.add(sniktSparks.mesh);

  function applyLightingMode(mode, shotType = 'medium') {
    if (mode === 'viewport_clay') {
      scene.background = new THREE.Color('#23262b');
      scene.environmentIntensity = 0.50;
      hemiLight.color.set('#9ea6b2');
      hemiLight.groundColor.set('#383c42');
      hemiLight.intensity = 0.78;

      keyLight.color.set('#f2f5fa');
      keyLight.intensity = 1.85;
      keyLight.position.set(-1.05, 2.48, 2.25);

      fillLight.color.set('#c4cedc');
      fillLight.intensity = 0.72;
      fillLight.position.set(1.45, 1.68, 1.95);

      rimLight.color.set('#dce6f2');
      rimLight.intensity = 0.95;
      bladeKicker.intensity = 0.35;

      studioVolCone.visible = false;
      dustMotes.mesh.visible = false;
    } else {
      // Dark Obsidian Fincher / Mangold Chiaroscuro Final Render!
      scene.background = new THREE.Color('#05070a');
      scene.environmentIntensity = 0.16;
      hemiLight.color.set('#3a4858');
      hemiLight.groundColor.set('#1c100c');
      hemiLight.intensity = 0.15;

      // Near-neutral 4300K key: a heavily orange key stacks with the skin tint in linear light
      // and turns flesh into tomato plastic. Warmth now comes from the grade, not the lamp.
      keyLight.color.set('#fff3e8');
      keyLight.intensity = shotType === 'macro' ? 1.62 : 1.72;
      keyLight.position.set(-1.32, 2.72, 1.62);

      // Warm bounce is CUT hard so the shadow side falls to near-black (true first-node Rembrandt);
      // directional separation on the shadow cheek now comes from the cold cyan rim, not red fill.
      fillLight.color.set('#8a5a4c');
      fillLight.intensity = 0.26;
      fillLight.position.set(1.28, 1.30, 1.30);

      rimLight.color.set('#79d8ff');
      rimLight.intensity = shotType === 'macro' ? 2.30 : 1.95;

      bladeKicker.color.set('#d8f2ff');
      bladeKicker.intensity = shotType === 'macro' ? 0.72 : 0.48;

      studioVolCone.visible = shotType === 'medium';
      dustMotes.mesh.visible = shotType === 'medium';
    }
  }

  return {
    keyLight,
    studioVolCone,
    dustMotes,
    sniktSparks,
    applyLightingMode,
  };
}

export function createLoganDirectorV6(logan, lights, camera) {
  const camRig = createCinemaCameraRig(camera, {
    totalFrames: TOTAL_FRAMES,
    shotCuts: SHOT_CUTS_LOGAN_V6,
    impacts: [
      { frame:  87, amp: 0.0085, decay: 0.26, freq: 2.15, durationFrames: 18 }, // SNIKT! eruption
      { frame: 168, amp: 0.0032, decay: 0.30, freq: 2.05, durationFrames: 12 }, // Macro render cut
      { frame: 252, amp: 0.0024, decay: 0.32, freq: 1.85, durationFrames: 10 }, // 3/4 portrait cut
      { frame: 336, amp: 0.0042, decay: 0.25, freq: 1.90, durationFrames: 14 }, // Climax stare cut
    ],
  });

  // Fist curl budget. A full anatomical fist folds the proximal + middle + distal
  // phalanges to roughly 1.9 rad TOTAL per digit. The previous table summed to ~4.2 rad
  // (242 deg), which drove the fingertips straight through the palm and erupted the
  // hand as inverted backfaces / hard black shards. `FIST_CURL` scales the whole table.
  const FIST_CURL = 0.62;
  // Distal phalanges fold the tightest and are what punch through the palm; damp them harder.
  const DISTAL_CURL = 0.42;
  const RIGHT_FINGERS = [
    ['index_01_r', 1.42 * FIST_CURL, 0.06],  ['index_02_r', 1.62 * FIST_CURL, 0.0],  ['index_03_r', 1.18 * FIST_CURL * DISTAL_CURL, 0.0],
    ['middle_01_r', 1.48 * FIST_CURL, 0.0],  ['middle_02_r', 1.68 * FIST_CURL, 0.0], ['middle_03_r', 1.22 * FIST_CURL * DISTAL_CURL, 0.0],
    ['ring_01_r', 1.52 * FIST_CURL, -0.05],  ['ring_02_r', 1.68 * FIST_CURL, 0.0],   ['ring_03_r', 1.24 * FIST_CURL * DISTAL_CURL, 0.0],
    ['pinky_01_r', 1.56 * FIST_CURL, -0.10], ['pinky_02_r', 1.68 * FIST_CURL, 0.0],  ['pinky_03_r', 1.25 * FIST_CURL * DISTAL_CURL, 0.0],
  ];
  const LEFT_FIST_CURL = 0.66;

  const LEFT_FINGERS = [
    'index_01_l', 'index_02_l', 'index_03_l',
    'middle_01_l', 'middle_02_l', 'middle_03_l',
    'ring_01_l', 'ring_02_l', 'ring_03_l',
    'pinky_01_l', 'pinky_02_l', 'pinky_03_l',
  ];

  const fistWorldTmp = new THREE.Vector3();

  function applyRightArmBlend(tArm) {
    // Two-segment smooth spline through POSE_REST_R -> POSE_MID_R -> POSE_CHEST_R
    for (const boneName of ['clavicle_r', 'upperarm_r', 'lowerarm_r', 'hand_r']) {
      let rot;
      if (tArm <= 0.5) {
        rot = lerp3(POSE_REST_R[boneName], POSE_MID_R[boneName], tArm * 2.0);
      } else {
        rot = lerp3(POSE_MID_R[boneName], POSE_CHEST_R[boneName], (tArm - 0.5) * 2.0);
      }
      logan.setBoneDelta(boneName, rot[0], rot[1], rot[2]);
    }
  }

  function applyRightHandFingers(clench, splayOpen = 0.0) {
    // `clench` in [0..1] (+ry curls into palm!), `splayOpen` in [0..1] fans fingers wide before fist snap!
    for (const [bName, maxCurl, fanSign] of RIGHT_FINGERS) {
      const curl = clench * maxCurl - splayOpen * 0.16;
      const fanZ = splayOpen * fanSign * 1.65;
      logan.setBoneDelta(bName, 0.0, curl, fanZ);
    }
    // Thumb locks tightly over curled index/middle phalanges on fist clench
    logan.setBoneDelta('thumb_01_r', 0.20 * clench - 0.12 * splayOpen, 0.42 * clench - 0.18 * splayOpen, -0.28 * clench);
    logan.setBoneDelta('thumb_02_r', 0.0, 0.62 * clench - 0.10 * splayOpen, 0.0);
    logan.setBoneDelta('thumb_03_r', 0.0, 0.50 * clench, 0.0);
  }

  function applyLeftHandFist(clench = 0.88) {
    for (const nm of ['clavicle_l', 'upperarm_l', 'lowerarm_l', 'hand_l']) {
      const r = POSE_REST_L[nm];
      logan.setBoneDelta(nm, r[0], r[1], r[2]);
    }
    for (const fName of LEFT_FINGERS) {
      logan.setBoneDelta(fName, 0.0, 1.45 * LEFT_FIST_CURL * clench, 0.0);
    }
    logan.setBoneDelta('thumb_01_l', -0.22 * clench, 0.48 * clench, 0.30 * clench);
    logan.setBoneDelta('thumb_02_l', 0.0, 0.82 * clench, 0.0);
  }

  function evaluateFrame(frame) {
    const f = ((frame % TOTAL_FRAMES) + TOTAL_FRAMES) % TOTAL_FRAMES;
    const timeS = f / FPS;
    // Integer-cycle breathing locked to 420 frames (`f=420` === `f=0` to 0.000000!)
    const loopPhase = (2.0 * Math.PI * f) / TOTAL_FRAMES;
    const breath = Math.sin(loopPhase * 3.0);

    logan.resetAllPose();

    let mode = 'viewport_clay';
    let shotType = 'medium';
    let tArm = 0.0;
    let splayOpen = 0.0;
    let fistClench = 0.18;
    let clawExt = 0.0;
    let clawTremor = 0.0;
    let glintSweep = -1.0;

    // Facial & Head parameters
    let browDown = 0.42;
    let eyeSquint = 0.16;
    let eyeWide = 0.0;
    let noseSneer = 0.08;
    let mouthFrown = 0.24;
    let jawClench = 0.10;
    let headPitch = -0.04; // negative ry = chin down (Kubrick stare!)
    let headYaw = 0.0;     // rx = yaw
    let gazeX = 0.0;
    let gazeY = 0.04;
    let blink = 0.0;

    let camPos = new THREE.Vector3(0.0, 1.48, 2.24);
    let camLook = new THREE.Vector3(0.0, 1.47, 0.04);
    let camFov = 31.0;
    let dutchDeg = 0.0;
    let exposure = 1.12;
    let bloomAmt = 0.22;
    let maxBlur = 1.6;

    // Subtle organic blink only in early viewport raise (`f=22..27`)
    if (f >= 21 && f <= 27) {
      blink = Math.sin(((f - 21) / 6.0) * Math.PI) * 0.92;
    }

    // =========================================================================
    // PAIR 1 (f = 0 .. 131): Medium-Close Viewport Raise -> SNIKT! Final Render
    // =========================================================================
    if (f < 132) {
      const uShot = f / 131.0;
      camPos.set(0.0, GLM.mix(1.48, 1.505, uShot), GLM.mix(2.24, 2.02, GLM.smoothstep(0, 1, uShot)));
      camLook.set(0.0, GLM.mix(1.47, 1.495, uShot), 0.04);
      camFov = 31.0;

      if (f < 87) {
        mode = 'viewport_clay';
        shotType = 'medium';
        // Arm rises smoothly across chest (`f=0..44`), fingers fan open (`f=36..60`), clenches fist (`f=61..80`)
        tArm = GLM.easeInOutCubic(GLM.clamp(f / 44.0, 0.0, 1.0));
        if (f >= 32 && f <= 66) {
          splayOpen = Math.sin(GLM.clamp((f - 32) / 34.0, 0.0, 1.0) * Math.PI) * 0.95;
        }
        if (f < 58) {
          fistClench = 0.18 * (1.0 - splayOpen);
        } else {
          fistClench = GLM.easeInOutCubic(GLM.clamp((f - 58) / 20.0, 0.0, 1.0));
        }
        const rageRamp = GLM.smoothstep(48, 85, f);
        browDown = GLM.mix(0.34, 0.56, rageRamp);
        eyeSquint = GLM.mix(0.08, 0.16, rageRamp);
        eyeWide = GLM.mix(0.10, 0.22, rageRamp);
        noseSneer = GLM.mix(0.05, 0.30, rageRamp);
        mouthFrown = GLM.mix(0.20, 0.45, rageRamp);
        jawClench = rageRamp * 0.55;
        headPitch = GLM.mix(-0.03, -0.10, rageRamp);
        gazeY = GLM.mix(0.03, 0.18, rageRamp);

        // Position Golden Rig-Logic Picker cleanly in upper-right viewport (`sheet1 f=000..081`)
        logan.pickerBoard.mesh.position.set(0.235, 1.805, -0.06);
        logan.pickerBoard.mesh.rotation.set(0, 0, 0);
        logan.pickerBoard.mesh.scale.setScalar(1.0);
        exposure = 1.04;
        bloomAmt = 0.12;
      } else {
        // f = 87 .. 131: HARD MATCH-CUT -> FINAL CHIAROSCURO RENDER (`SNIKT!`)
        mode = 'final_render';
        shotType = 'medium';
        tArm = 1.0;
        fistClench = 1.0;
        // Explosive Adamantium claw ejection. At `f=87` the claws are ALREADY 45% out:
        // landing on a fully-sheathed fist produced a near-black silhouette frame
        // (`min_luma 5.81`) that failed the zero-black-frame gate.
        clawExt = GLM.clamp(0.45 + (f - 87) / 3.0, 0.0, 1.0);
        const df = f - 87;
        clawTremor = Math.exp(-df * 0.24) * Math.sin(df * 2.4) * 1.2;
        glintSweep = GLM.clamp((f - 88) / 28.0, 0.0, 1.2);

        browDown = 0.58;
        eyeSquint = 0.04;
        eyeWide = 0.32;
        noseSneer = 0.34;
        mouthFrown = 0.48;
        jawClench = 0.65;
        headPitch = -0.105;
        gazeY = 0.20;
        dutchDeg = -0.65 * Math.exp(-df * 0.12);
        // Tighter SNIKT coverage: the medium-wide framing left ~2/3 of the 9:16 frame
        // empty black, which read as an underexposed silhouette on the cut frame.
        camFov = 25.5;
        camPos.set(0.0, 1.535, 1.72);
        camLook.set(0.0, 1.512, 0.04);
        // Extra key energy fading over ~1.5 s only across the SNIKT eruption, so the
        // cut frame never reads as an empty silhouette. Deep chiaroscuro is unchanged
        // later in the shot once `sniktPower` has decayed.
        const sniktPower = Math.exp(-Math.max(0, df) * 0.055);
        exposure = 1.14 + 0.22 * sniktPower;
        bloomAmt = 0.38;
      }
    }
    // =========================================================================
    // PAIR 2 (f = 132 .. 209): Extreme 100mm Macro Knuckles & 3 Curved Blades
    // =========================================================================
    else if (f < 210) {
      const uMacro = (f - 132) / 77.0;
      tArm = 1.0;
      fistClench = 0.96 + 0.04 * Math.sin(uMacro * Math.PI * 2.0);
      clawExt = 1.0;
      browDown = 0.56;
      eyeSquint = 0.04;
      eyeWide = 0.28;
      mouthFrown = 0.44;
      headPitch = -0.06;

      // Tight macro framing: bearded jaw edge top-left, clenched fist (`[-0.041, 1.437, 0.278]`) bottom-left,
      // 3 curved blades sweeping diagonally up-right to `[+0.145, 1.631, 0.314]`!
      camPos.set(GLM.mix(0.066, 0.052, uMacro), GLM.mix(1.535, 1.546, uMacro), GLM.mix(1.42, 1.32, uMacro));
      camLook.set(0.052, 1.538, 0.285);
      camFov = 23.4;
      shotType = 'macro';

      if (f < 168) {
        mode = 'viewport_clay';
        clawTremor = 0.15 * Math.sin((f - 132) * 0.45);
        // Place Golden Rig-Logic Picker cleanly behind the 3 blades (`sheet1 f=121..135`!)
        logan.pickerBoard.mesh.position.set(0.082, 1.608, 0.02);
        logan.pickerBoard.mesh.scale.setScalar(1.06);
        exposure = 1.05;
        bloomAmt = 0.14;
        maxBlur = 1.2;
      } else {
        mode = 'final_render';
        // Sweeping cold-cyan specular glint along all 3 hollow-ground Adamantium bevels!
        glintSweep = GLM.clamp((f - 169) / 30.0, 0.0, 1.18);
        exposure = 1.20;
        bloomAmt = 0.40;
        maxBlur = 2.2;
      }
    }
    // =========================================================================
    // PAIR 3 (f = 210 .. 293): Intimate 3/4 Facial Micro-Expression Portrait
    // =========================================================================
    else if (f < 294) {
      const u34 = (f - 210) / 83.0;
      tArm = 0.0;
      fistClench = 0.65;
      clawExt = 0.0;
      shotType = 'closeup';

      // Camera angled 26 deg to viewer's left (`sheet2 f=176..216` 3/4 profile!)
      camPos.set(GLM.mix(-0.43, -0.39, u34), GLM.mix(1.822, 1.818, u34), GLM.mix(0.94, 0.88, u34));
      camLook.set(-0.008, 1.802, 0.068);
      camFov = 21.5;

      // Subtle living micro-acting: brow corrugator flex, eye dart, nostril sneer
      const act = GLM.smoothstep(0.08, 0.72, u34);
      browDown = GLM.mix(0.42, 0.58, act);
      eyeSquint = GLM.mix(0.03, 0.07, act);
      eyeWide = GLM.mix(0.24, 0.40, act);
      noseSneer = GLM.mix(0.12, 0.38, act);
      mouthFrown = GLM.mix(0.28, 0.50, act);
      jawClench = GLM.mix(0.20, 0.60, act);
      headPitch = GLM.mix(-0.05, -0.09, act);
      headYaw = GLM.mix(-0.04, 0.03, act);
      // Sharp intense eye look toward camera-left -> locking onto lens
      gazeX = GLM.mix(-0.34, -0.18, GLM.smoothstep(0.35, 0.62, u34));
      gazeY = 0.12;

      if (f < 252) {
        mode = 'viewport_clay';
        logan.pickerBoard.mesh.visible = false; // clean clay head portrait just like sheet2 f=176!
        exposure = 1.04;
        bloomAmt = 0.10;
      } else {
        mode = 'final_render';
        exposure = 1.22;
        bloomAmt = 0.30;
      }
      maxBlur = 1.8;
    }
    // =========================================================================
    // PAIR 4 (f = 294 .. 392): Dead-Center Front Kubrick-Stare Climax
    // =========================================================================
    else if (f < 393) {
      const uFront = (f - 294) / 98.0;
      tArm = 0.0;
      fistClench = 0.75;
      clawExt = 0.0;
      shotType = 'closeup';

      camPos.set(0.0, GLM.mix(1.820, 1.814, uFront), GLM.mix(1.08, 0.98, GLM.smoothstep(0, 1, uFront)));
      camLook.set(0.0, 1.810, 0.068);
      camFov = 23.2;

      const intensity = GLM.smoothstep(0.0, 0.58, uFront);
      browDown = GLM.mix(0.50, 0.58, intensity);
      // Kubrick stare needs a genuinely OPEN eye: heavy squint drops the upper lid
      // over the pupil and kills the catchlight. Menace comes from the brow, not the lid.
      eyeSquint = GLM.mix(0.02, 0.05, intensity);
      eyeWide = GLM.mix(0.40, 0.62, intensity);
      noseSneer = GLM.mix(0.22, 0.42, intensity);
      mouthFrown = GLM.mix(0.38, 0.54, intensity);
      jawClench = GLM.mix(0.35, 0.75, intensity);
      // Iconic Logan Kubrick tilt: chin down (`-0.118 rad`), eyes locked straight up into the lens!
      headPitch = GLM.mix(-0.088, -0.118, intensity);
      gazeX = 0.0;
      gazeY = GLM.mix(0.18, 0.28, intensity);

      if (f < 336) {
        mode = 'viewport_clay';
        logan.pickerBoard.mesh.visible = false; // clean front clay portrait just like sheet2 f=230!
        exposure = 1.04;
        bloomAmt = 0.10;
      } else {
        mode = 'final_render';
        exposure = 1.22;
        bloomAmt = 0.32;
      }
      maxBlur = 1.8;
    }
    // =========================================================================
    // SHOT 5 (f = 393 .. 419): Seamless Infinite-Loop Viewport Reset -> f = 0!
    // =========================================================================
    else {
      const uLoop = (f - 393) / 27.0; // at f=419, uLoop = 26/27 = 0.963 -> smoothly meets f=0 (0.0)!
      const easeBack = 1.0 - GLM.easeInOutCubic(GLM.clamp((f - 393) / 26.0, 0.0, 1.0));
      mode = 'viewport_clay';
      shotType = 'medium';

      tArm = easeBack * 0.42;
      fistClench = GLM.mix(0.18, 0.85, easeBack);
      clawExt = GLM.clamp(1.0 - (f - 393) / 5.5, 0.0, 1.0); // crisp reverse sheath in first 6 frames!

      browDown = GLM.mix(0.34, 0.52, easeBack);
      eyeSquint = GLM.mix(0.06, 0.14, easeBack);
      eyeWide = GLM.mix(0.06, 0.16, easeBack);
      noseSneer = GLM.mix(0.05, 0.24, easeBack);
      mouthFrown = GLM.mix(0.20, 0.38, easeBack);
      headPitch = GLM.mix(-0.03, -0.09, easeBack);
      gazeY = GLM.mix(0.03, 0.16, easeBack);

      camPos.set(0.0, GLM.mix(1.48, 1.495, easeBack), GLM.mix(2.24, 2.12, easeBack));
      camLook.set(0.0, GLM.mix(1.47, 1.485, easeBack), 0.04);
      camFov = 31.0;

      logan.pickerBoard.mesh.position.set(0.235, 1.805, -0.06);
      logan.pickerBoard.mesh.rotation.set(0, 0, 0);
      logan.pickerBoard.mesh.scale.setScalar(1.0);
      exposure = 1.04;
      bloomAmt = 0.12;
      maxBlur = 1.6;
    }

    // 1. Apply Mode & Studio/Chiaroscuro Lighting
    logan.setRenderMode(mode);
    if (mode === 'viewport_clay' && (f >= 210 && f < 393)) {
      // Keep 3/4 & Front close-up clay portraits clean of background picker board (matching sheet2!)
      logan.pickerBoard.mesh.visible = false;
    }
    lights.applyLightingMode(mode, shotType);

    // 2. Apply Torso Breathing, Head Orientation, Arms, Hands & Claws
    logan.setBoneDelta('spine_02', 0.0, -0.012 * breath, 0.0);
    logan.setBoneDelta('spine_04', 0.0, -0.016 * breath, 0.0);
    logan.setBoneDelta('neck_01', headYaw * 0.35, headPitch * 0.42, 0.0);
    logan.setBoneDelta('head',    headYaw * 0.65, headPitch * 0.58 - 0.008 * breath, 0.0);

    applyRightArmBlend(tArm);
    applyRightHandFingers(fistClench, splayOpen);
    applyLeftHandFist(0.86);

    logan.clawRig.setState({
      extension: clawExt,
      tremor: clawTremor,
      glintSweep,
    });

    // 3. Apply 51-Blendshape Facial Micro-Acting across Face + Beard + Eyebrows + Mustache!
    logan.setMorph('browDownLeft', browDown);
    logan.setMorph('browDownRight', browDown);
    logan.setMorph('eyeSquintLeft', eyeSquint);
    logan.setMorph('eyeSquintRight', eyeSquint);
    logan.setMorph('cheekSquintLeft', eyeSquint * 0.55);
    logan.setMorph('cheekSquintRight', eyeSquint * 0.55);
    logan.setMorph('noseSneerLeft', noseSneer);
    logan.setMorph('noseSneerRight', noseSneer * 0.88);
    logan.setMorph('mouthFrownLeft', mouthFrown);
    logan.setMorph('mouthFrownRight', mouthFrown);
    logan.setMorph('mouthPressLeft', jawClench * 0.68);
    logan.setMorph('mouthPressRight', jawClench * 0.68);
    logan.setMorph('eyeWideLeft', eyeWide);
    logan.setMorph('eyeWideRight', eyeWide);
    logan.setMorph('eyeBlinkLeft', blink);
    logan.setMorph('eyeBlinkRight', blink);

    if (gazeY >= 0) {
      logan.setMorph('eyeLookUpLeft', gazeY * 0.55);
      logan.setMorph('eyeLookUpRight', gazeY * 0.55);
    } else {
      logan.setMorph('eyeLookDownLeft', -gazeY * 0.55);
      logan.setMorph('eyeLookDownRight', -gazeY * 0.55);
    }
    if (gazeX < 0) {
      logan.setMorph('eyeLookOutRight', -gazeX * 0.75);
      logan.setMorph('eyeLookInLeft', -gazeX * 0.75);
    } else if (gazeX > 0) {
      logan.setMorph('eyeLookInRight', gazeX * 0.75);
      logan.setMorph('eyeLookOutLeft', gazeX * 0.75);
    }

    // 4. Update Live Golden Rig-Logic Picker Schematic
    if (logan.pickerBoard.mesh.visible) {
      logan.pickerBoard.draw({
        brow: browDown,
        squint: eyeSquint,
        sneer: noseSneer,
        clench: fistClench,
        gazeX,
        gazeY,
      });
    }

    logan.actorRoot.updateMatrixWorld(true);

    // 5. Update Atmospheric Dust & Ballistic SNIKT! Micro-Sparks
    lights.dustMotes.update(timeS);
    if (f >= 87 && f <= 99) {
      logan.getBoneWorldPos('index_01_r', fistWorldTmp);
      const sparkAlpha = 1.0 - (f - 87) / 12.0;
      lights.sniktSparks.update(fistWorldTmp, (f - 87) / 30.0, {
        intensity: sparkAlpha * 0.85,
        speedScale: 0.28,
        dirSign: 0.35,
      });
    } else {
      lights.sniktSparks.mesh.visible = false;
    }

    // 6. Apply Newtonian Cinema Camera Rig + Meter-Precision Z-Buffer Bracket
    const rigOut = camRig.apply({
      frame: f,
      pos: camPos,
      look: camLook,
      fov: camFov,
      dutchDeg,
      breathAmp: shotType === 'medium' ? 0.0028 : 0.0012,
      shutterBlurScale: 0.28,
      minNear: 0.08,
      maxNear: 0.32,
    });

    const trueFocusDist = camera.position.distanceTo(camLook);
    camera.near = GLM.clamp(trueFocusDist * 0.16, 0.08, 0.35);
    camera.far = 22.0;
    camera.updateProjectionMatrix();

    return {
      frame: f,
      time: timeS,
      mode,
      shotType,
      postParams: {
        focusDist: trueFocusDist,
        dofRange: 1.0,
        maxBlur,
        bloomAmt,
        exposure,
        time: timeS,
        motionVec: rigOut.motionVec,
      },
    };
  }

  return { evaluateFrame };
}
