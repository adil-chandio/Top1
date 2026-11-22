import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { makeV5Material } from './materials_v5.js';

/**
 * Monarch Cam #03 — V5 Rigged 3D Human Actors (53-Bone Mixamo Skeleton + Upgraded Kinematics & Materials)
 * Fixes V4 human-rig audit findings:
 *   1. Homeowner right arm reaches cleanly forward to ivory wall switch at Y = 1210 mm with natural
 *      elbow flexion & warm/moonlit rim definition (fixing V4 Frame 40's stiff high salute!).
 *   2. Researcher matte cotton lab coat (`specPower = 0.12`) eliminates shiny stripe banding!
 *   3. Athlete push-up rig exposes `getHandWorldPositions()` so Ground Reaction Force arrows lock
 *      onto the exact world-space palms on glowing force plates!
 */
export async function loadV5HumanActors(mats) {
  const loader = new GLTFLoader();
  const [homeGltf, resGltf, athGltf] = await Promise.all([
    loader.loadAsync('/tools/monarch-cockroach/v4/assets/homeowner.glb'),
    loader.loadAsync('/tools/monarch-cockroach/v4/assets/researcher.glb'),
    loader.loadAsync('/tools/monarch-cockroach/v4/assets/athlete.glb'),
  ]);

  function prepareRig(gltf, fallbackHex, rimTint = [0.75, 0.68, 0.58], rimStrength = 0.22) {
    const root = gltf.scene;
    const bones = {};
    const restQuats = {};
    const restPos = {};

    root.traverse((o) => {
      if (o.isBone) {
        const clean = o.name.replace(/^mixamorig:?/, '');
        bones[clean] = o;
        restQuats[clean] = o.quaternion.clone();
        restPos[clean] = o.position.clone();
      }
      if (o.isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
        o.frustumCulled = false;
        const oldMat = Array.isArray(o.material) ? o.material[0] : o.material;
        const tex = oldMat && oldMat.map ? oldMat.map : null;
        if (tex) {
          tex.colorSpace = THREE.SRGBColorSpace;
          o.material = makeV5Material({
            color: '#ffffff',
            specular: '#3e3834',
            specPower: 0.14,
            map: tex,
            rimTint,
            rimStrength,
            translucent: 0.10,
          });
        } else {
          o.material = makeV5Material({
            color: fallbackHex,
            specular: '#32363c',
            specPower: 0.12,
            rimTint,
            rimStrength: rimStrength * 0.8,
            translucent: 0.04,
          });
        }
      }
    });

    function setBoneDelta(name, rx = 0, ry = 0, rz = 0, order = 'XYZ') {
      const b = bones[name];
      if (!b) return;
      const dq = new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz, order));
      b.quaternion.copy(restQuats[name]).multiply(dq);
    }

    function resetAll() {
      for (const k of Object.keys(bones)) {
        bones[k].quaternion.copy(restQuats[k]);
        bones[k].position.copy(restPos[k]);
      }
    }

    return { root, bones, restQuats, restPos, setBoneDelta, resetAll };
  }

  const homeowner = prepareRig(homeGltf, '#263040', [0.85, 0.78, 0.68], 0.30);
  homeowner.root.scale.setScalar(1740);

  const researcher = prepareRig(resGltf, '#dde3e8', [0.65, 0.78, 0.84], 0.16);
  researcher.root.scale.setScalar(1750);

  if (researcher.bones.Head) {
    const glasses = new THREE.Group();
    const frameMat = mats.steelBrushedMat;
    const lensMat = mats.acrylicEdgeMat;
    for (const s of [-1, 1]) {
      const rim = new THREE.Mesh(new THREE.TorusGeometry(0.015, 0.0014, 8, 20), frameMat);
      rim.rotation.y = Math.PI / 2;
      rim.scale.set(1.22, 0.85, 1.0);
      rim.position.set(0.056, 0.048, s * 0.021);
      const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 0.0015, 16), lensMat);
      lens.rotation.z = Math.PI / 2;
      lens.scale.set(0.83, 1.0, 1.20);
      lens.position.set(0.056, 0.048, s * 0.021);
      lens.renderOrder = 14;
      glasses.add(rim, lens);
    }
    const bridge = new THREE.Mesh(new THREE.CylinderGeometry(0.0014, 0.0014, 0.014, 8), frameMat);
    bridge.rotation.x = Math.PI / 2;
    bridge.position.set(0.058, 0.050, 0);
    glasses.add(bridge);
    researcher.bones.Head.add(glasses);
  }

  const athlete = prepareRig(athGltf, '#1c222b', [0.95, 0.74, 0.48], 0.32);
  athlete.root.scale.setScalar(1740);

  /**
   * Natural ergonomic reach to wall light switch at chest/shoulder level (Y = 1210 mm):
   * From Mixamo T-pose, `RightArm` rz = -1.18 brings upper arm down along torso, and `RightForeArm`
   * bends forward cleanly so the index finger meets the toggle switch instead of saluting high!
   */
  function poseHomeowner(time, reachAmt = 0.0, lookDownAmt = 0.0) {
    homeowner.resetAll();
    const breath = 0.022 * Math.sin(time * 2.4);

    // Relaxed left arm at side
    homeowner.setBoneDelta('LeftShoulder', 0.0, 0.0, -0.08);
    homeowner.setBoneDelta('LeftArm', 0.10 + 0.16 * lookDownAmt, 0.0, 1.20 - 0.12 * lookDownAmt);
    homeowner.setBoneDelta('LeftForeArm', 0.0, -0.38 - 0.22 * lookDownAmt, 0.0);

    // Natural chest-level reach to wall switch: drop upper arm down along torso FIRST ('ZYX'),
    // then bend forearm forward cleanly so fingers touch the ivory wall toggle at Y = 1210 mm!
    const armDown = 1.22 - 0.14 * reachAmt;
    const armFwd = -0.34 * reachAmt;
    homeowner.setBoneDelta('RightShoulder', 0.0, -0.06 * reachAmt, 0.02);
    homeowner.setBoneDelta('RightArm', armFwd, -0.28 * reachAmt, -armDown, 'ZYX');
    homeowner.setBoneDelta('RightForeArm', 0.15 * reachAmt, 1.12 * reachAmt + 0.24 * (1 - reachAmt), 0.0);
    homeowner.setBoneDelta('RightHand', -0.18 * reachAmt, 0.0, 0.0);

    homeowner.setBoneDelta('Spine1', 0.18 * lookDownAmt + breath, 0.06 * (1 - lookDownAmt), 0);
    homeowner.setBoneDelta('Spine2', 0.20 * lookDownAmt, 0, 0);
    homeowner.setBoneDelta('Neck', 0.26 * lookDownAmt, -0.10 * reachAmt, 0);
    homeowner.setBoneDelta('Head', 0.34 * lookDownAmt, -0.08 * reachAmt + 0.04 * Math.sin(time * 3.1), 0);

    homeowner.setBoneDelta('LeftUpLeg', -0.06 * lookDownAmt, 0, -0.03);
    homeowner.setBoneDelta('RightUpLeg', -0.06 * lookDownAmt, 0, 0.03);
    homeowner.setBoneDelta('LeftLeg', 0.12 * lookDownAmt, 0, 0);
    homeowner.setBoneDelta('RightLeg', 0.12 * lookDownAmt, 0, 0);
  }

  function poseResearcher(time, dialReach = 0.5, inspectTilt = 0.5) {
    researcher.resetAll();
    const breath = 0.02 * Math.sin(time * 2.1);

    researcher.setBoneDelta('Spine1', 0.14 * inspectTilt + breath, 0, 0);
    researcher.setBoneDelta('Spine2', 0.16 * inspectTilt, 0, 0);
    researcher.setBoneDelta('Neck', 0.20 * inspectTilt, 0.06 * Math.sin(time * 0.9), 0);
    researcher.setBoneDelta('Head', 0.22 * inspectTilt, 0.05 * Math.cos(time * 1.1), 0);

    researcher.setBoneDelta('LeftArm', -0.35, 0.12, 1.05);
    researcher.setBoneDelta('LeftForeArm', 0.0, -0.60, 0.0);

    const wristSpin = 0.24 * Math.sin(time * 4.0) * dialReach;
    researcher.setBoneDelta('RightArm', -0.62 * dialReach - 0.20, -0.15, -0.92 + 0.22 * dialReach);
    researcher.setBoneDelta('RightForeArm', 0.0, 0.68 * dialReach + 0.28, wristSpin);
    researcher.setBoneDelta('RightHand', -0.15, wristSpin, 0);
  }

  function poseAthletePushup(time, splayAlpha = 0.0, repCycle = 0.0) {
    athlete.resetAll();
    const dip = 0.5 - 0.5 * Math.cos(repCycle * Math.PI * 2);

    const armSweepBack = (1.0 - splayAlpha) * 0.62;
    const armAbduct = (1.0 - splayAlpha) * (0.42 - 0.35 * dip) + splayAlpha * (-0.10 - 0.06 * Math.sin(time * 14.0));
    const elbowBend = (1.0 - splayAlpha) * (0.55 + 0.85 * dip) + splayAlpha * (0.18 + 0.12 * dip);
    const palmTipSideways = splayAlpha * 0.86;

    athlete.setBoneDelta('LeftArm', -0.35 * (1 - splayAlpha), -armSweepBack, armAbduct);
    athlete.setBoneDelta('RightArm', -0.35 * (1 - splayAlpha), armSweepBack, -armAbduct);
    athlete.setBoneDelta('LeftForeArm', 0, -elbowBend, 0);
    athlete.setBoneDelta('RightForeArm', 0, elbowBend, 0);
    athlete.setBoneDelta('LeftHand', -0.95 * (1 - splayAlpha), 0, palmTipSideways);
    athlete.setBoneDelta('RightHand', -0.95 * (1 - splayAlpha), 0, -palmTipSideways);

    const tremor = splayAlpha * 0.022 * Math.sin(time * 22.0);
    athlete.setBoneDelta('Neck', -0.46 + tremor, 0, 0);
    athlete.setBoneDelta('Head', -0.36, tremor * 1.4, 0);
    athlete.setBoneDelta('Spine1', 0.05 * splayAlpha, 0, 0);

    athlete.setBoneDelta('LeftFoot', -0.65, 0, 0);
    athlete.setBoneDelta('RightFoot', -0.65, 0, 0);
  }

  const tmpL = new THREE.Vector3();
  const tmpR = new THREE.Vector3();
  function getAthleteHandWorldPositions() {
    athlete.root.updateMatrixWorld(true);
    if (athlete.bones.LeftHand && athlete.bones.RightHand) {
      athlete.bones.LeftHand.getWorldPosition(tmpL);
      athlete.bones.RightHand.getWorldPosition(tmpR);
      return { left: tmpL.clone(), right: tmpR.clone() };
    }
    return { left: new THREE.Vector3(350, 0, -450), right: new THREE.Vector3(350, 0, 450) };
  }

  return {
    homeowner,
    researcher,
    athlete,
    poseHomeowner,
    poseResearcher,
    poseAthletePushup,
    getAthleteHandWorldPositions,
  };
}
