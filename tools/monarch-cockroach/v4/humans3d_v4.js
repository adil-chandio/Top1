import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { makeV4Material } from './materials_v4.js';

/**
 * Monarch Cam #03 — V4 Rigged 3D Human Actors (53-Bone Mixamo Skeleton + Bespoke PBR Clothing)
 *   1. Homeowner (Midnight apartment light-switch opener & startled look-down)
 *   2. UC Berkeley Biomechanics Researcher (White lab coat, nitrile gloves, rimless glasses, micrometer control)
 *   3. Biomechanics Athlete (Normal shoulder-width push-up vs >80° wide-arm splayed push-up metaphor!)
 */
export async function loadV4HumanActors(mats) {
  const loader = new GLTFLoader();
  const [homeGltf, resGltf, athGltf] = await Promise.all([
    loader.loadAsync('/tools/monarch-cockroach/v4/assets/homeowner.glb'),
    loader.loadAsync('/tools/monarch-cockroach/v4/assets/researcher.glb'),
    loader.loadAsync('/tools/monarch-cockroach/v4/assets/athlete.glb'),
  ]);

  function prepareRig(gltf, pelvisHex) {
    const root = gltf.scene;
    const bones = {};
    const restQuats = {};
    const restPos = {};

    root.traverse((o) => {
      if (o.isBone) {
        // Normalize bone key whether exported as "mixamorig:RightArm" or "mixamorigRightArm"
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
          o.material = makeV4Material({
            color: '#ffffff',
            specular: '#584e46',
            specPower: 0.25,
            map: tex,
            rimTint: [0.85, 0.72, 0.58],
            rimStrength: 0.16,
            translucent: 0.08,
          });
        } else {
          o.material = makeV4Material({
            color: pelvisHex,
            specular: '#383c42',
            specPower: 0.18,
            rimTint: [0.45, 0.50, 0.56],
            rimStrength: 0.10,
            translucent: 0.02,
          });
        }
      }
    });

    function setBoneDelta(name, rx = 0, ry = 0, rz = 0) {
      const b = bones[name];
      if (!b) return;
      const dq = new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz, 'XYZ'));
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

  // Note: 1 Three.js world unit = 1.0 mm! Adult human height = 1740 mm!
  const homeowner = prepareRig(homeGltf, '#1b1e25');
  homeowner.root.scale.setScalar(1740);

  const researcher = prepareRig(resGltf, '#e3e9ef');
  researcher.root.scale.setScalar(1750);

  // Attach sleek 3D rimless lab glasses onto researcher's Head bone!
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
      glasses.add(rim, lens);
    }
    const bridge = new THREE.Mesh(new THREE.CylinderGeometry(0.0014, 0.0014, 0.014, 8), frameMat);
    bridge.rotation.x = Math.PI / 2;
    bridge.position.set(0.058, 0.050, 0);
    glasses.add(bridge);
    researcher.bones.Head.add(glasses);
  }

  const athlete = prepareRig(athGltf, '#12151a');
  athlete.root.scale.setScalar(1740);

  /**
   * Animate Homeowner in Scene 01:
   *   reachAmt: 0..1 right hand reaching to wall light switch & flicking UP
   *   lookDownAmt: 0..1 startled head/torso pitch downward watching the cockroach bolt!
   */
  function poseHomeowner(time, reachAmt = 0.0, lookDownAmt = 0.0) {
    homeowner.resetAll();
    const breath = 0.025 * Math.sin(time * 2.4);
    // Natural relaxed left arm down at side (from T-pose: LeftArm rz ~ -1.22, RightArm rz ~ +1.22)
    homeowner.setBoneDelta('LeftShoulder', 0.0, 0.0, -0.10);
    homeowner.setBoneDelta('LeftArm', 0.12 + 0.18 * lookDownAmt, 0.0, 1.18 - 0.15 * lookDownAmt);
    homeowner.setBoneDelta('LeftForeArm', 0.0, -0.35 - 0.25 * lookDownAmt, 0.0);

    // Right arm reaches forward at chest/switch height (~1210 mm) to wall toggle switch!
    const armDown = 1.15 * (1.0 - reachAmt) + 0.52 * reachAmt;
    const armFwd = -0.62 * reachAmt;
    homeowner.setBoneDelta('RightShoulder', 0.0, -0.06 * reachAmt, 0.05);
    homeowner.setBoneDelta('RightArm', armFwd, -0.18 * reachAmt, -armDown);
    homeowner.setBoneDelta('RightForeArm', 0.0, 0.62 * reachAmt + 0.22 * (1 - reachAmt), 0.0);
    homeowner.setBoneDelta('RightHand', -0.18 * reachAmt, 0.0, 0.0);
    homeowner.setBoneDelta('RightHandIndex1', 0.35 * (1 - reachAmt), 0, 0);

    // Spine & head look toward switch first, then snap downward toward floor cockroach!
    homeowner.setBoneDelta('Spine1', 0.18 * lookDownAmt + breath, 0.08 * (1 - lookDownAmt), 0);
    homeowner.setBoneDelta('Spine2', 0.22 * lookDownAmt, 0, 0);
    homeowner.setBoneDelta('Neck', 0.28 * lookDownAmt - 0.06 * reachAmt, -0.15 * reachAmt, 0);
    homeowner.setBoneDelta('Head', 0.36 * lookDownAmt, -0.12 * reachAmt + 0.05 * Math.sin(time * 3.1), 0);

    // Slight athletic knee bend on surprise
    homeowner.setBoneDelta('LeftUpLeg', -0.08 * lookDownAmt, 0, -0.03);
    homeowner.setBoneDelta('RightUpLeg', -0.08 * lookDownAmt, 0, 0.03);
    homeowner.setBoneDelta('LeftLeg', 0.15 * lookDownAmt, 0, 0);
    homeowner.setBoneDelta('RightLeg', 0.15 * lookDownAmt, 0, 0);
  }

  /**
   * Animate UC Berkeley Researcher in Lab Scenes:
   *   dialReach: 0..1 right gloved hand extended forward turning micrometer knob
   *   inspectTilt: 0..1 leaning forward & peering down at acrylic tunnel / high-speed rig
   */
  function poseResearcher(time, dialReach = 0.5, inspectTilt = 0.5) {
    researcher.resetAll();
    const breath = 0.02 * Math.sin(time * 2.1);

    researcher.setBoneDelta('Spine1', 0.16 * inspectTilt + breath, 0, 0);
    researcher.setBoneDelta('Spine2', 0.18 * inspectTilt, 0, 0);
    researcher.setBoneDelta('Neck', 0.22 * inspectTilt, 0.08 * Math.sin(time * 0.9), 0);
    researcher.setBoneDelta('Head', 0.24 * inspectTilt, 0.06 * Math.cos(time * 1.1), 0);

    // Left gloved hand resting near optical breadboard edge
    researcher.setBoneDelta('LeftArm', -0.45, 0.15, 0.95);
    researcher.setBoneDelta('LeftForeArm', 0.0, -0.65, 0.0);

    // Right gloved hand reaching to precision micrometer Vernier knob & rotating gently!
    const wristSpin = 0.28 * Math.sin(time * 4.2) * dialReach;
    researcher.setBoneDelta('RightArm', -0.78 * dialReach - 0.25, -0.18, -0.82 + 0.30 * dialReach);
    researcher.setBoneDelta('RightForeArm', 0.0, 0.72 * dialReach + 0.30, wristSpin);
    researcher.setBoneDelta('RightHand', -0.18, wristSpin, 0);
  }

  /**
   * Animate Biomechanics Athlete on Force-Plate Stage (Scene 04 [4869..5008]):
   *   splayAlpha: 0.0 = crisp standard shoulder-width push-up (~38° arm angle)
   *               1.0 = arms stretched straight out to the sides (>82° sprawl — mechanical collapse!)
   *   repCycle: continuous push-up phase
   */
  function poseAthletePushup(time, splayAlpha = 0.0, repCycle = 0.0) {
    athlete.resetAll();
    // Rotate whole character horizontal (prone plank facing floor -Y!) via root transform in world_v4.js;
    // here we articulate shoulder sprawl, elbow flexion, wrist roll, and head/neck strain!
    const dip = 0.5 - 0.5 * Math.cos(repCycle * Math.PI * 2);

    // Standard push-up (splayAlpha=0): arms tucked back ~45 deg, elbows bend cleanly, body rises high.
    // Wide-arm >80° splayed push-up (splayAlpha=1): arms straight out laterally in T-sprawl, elbows barely leverage, palms tip onto outer edge!
    const armSweepBack = (1.0 - splayAlpha) * 0.62;
    const armAbduct = (1.0 - splayAlpha) * (0.42 - 0.35 * dip) + splayAlpha * (-0.12 - 0.08 * Math.sin(time * 14.0));
    const elbowBend = (1.0 - splayAlpha) * (0.55 + 0.85 * dip) + splayAlpha * (0.18 + 0.12 * dip);
    const palmTipSideways = splayAlpha * 0.88; // Exact human analogue of cockroach tarsal claws tipping off floor!

    athlete.setBoneDelta('LeftArm', -0.35 * (1 - splayAlpha), -armSweepBack, armAbduct);
    athlete.setBoneDelta('RightArm', -0.35 * (1 - splayAlpha), armSweepBack, -armAbduct);
    athlete.setBoneDelta('LeftForeArm', 0, -elbowBend, 0);
    athlete.setBoneDelta('RightForeArm', 0, elbowBend, 0);
    athlete.setBoneDelta('LeftHand', -0.95 * (1 - splayAlpha), 0, palmTipSideways);
    athlete.setBoneDelta('RightHand', -0.95 * (1 - splayAlpha), 0, -palmTipSideways);

    // Head lifted slightly looking forward, straining as splayAlpha -> 1!
    const tremor = splayAlpha * 0.025 * Math.sin(time * 22.0);
    athlete.setBoneDelta('Neck', -0.48 + tremor, 0, 0);
    athlete.setBoneDelta('Head', -0.38, tremor * 1.5, 0);
    athlete.setBoneDelta('Spine1', 0.06 * splayAlpha, 0, 0);

    // Feet planted on toes
    athlete.setBoneDelta('LeftFoot', -0.65, 0, 0);
    athlete.setBoneDelta('RightFoot', -0.65, 0, 0);
  }

  return { homeowner, researcher, athlete, poseHomeowner, poseResearcher, poseAthletePushup };
}
