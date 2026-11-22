import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { makeImaxMaterial } from './pbr_shadow_sdk.js';

/**
 * Monarch V6 Hollywood IMAX Cinema SDK — Parametric 3D Lofting, Analytical 2-Bone IK,
 * Skinned `.glb` Human Loader & Newtonian Cinema Camera Rig (`sculpt_ik_rig_sdk.js`).
 */

export const GLM = {
  vec3: (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z),
  clamp: (v, a, b) => Math.max(a, Math.min(b, v)),
  mix: (a, b, t) => a + (b - a) * t,
  smoothstep: (a, b, x) => {
    const t = Math.max(0, Math.min(1, (x - a) / (b - a)));
    return t * t * (3 - 2 * t);
  },
  easeInOutCubic: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  easeOutQuint: (t) => 1 - Math.pow(1 - Math.max(0, Math.min(1, t)), 5),

  /**
   * Analytical 3D 2-Bone Inverse Kinematics Solver (Cosine Law + Orthogonal Pole Vector)
   */
  solveTwoBoneIK(H, T, L1, L2, poleDir) {
    const dVec = new THREE.Vector3().subVectors(T, H);
    let dist = dVec.length();
    const minD = Math.abs(L1 - L2) + 0.08;
    const maxD = (L1 + L2) * 0.992;
    if (dist < 1e-5) dist = minD;
    const clamped = Math.max(minD, Math.min(maxD, dist));
    const forward = dVec.clone().divideScalar(dist);

    const cosA = Math.max(-1, Math.min(1, (L1 * L1 + clamped * clamped - L2 * L2) / (2 * L1 * clamped)));
    const sinA = Math.sqrt(Math.max(0, 1 - cosA * cosA));

    const ortho = poleDir.clone().addScaledVector(forward, -poleDir.dot(forward));
    if (ortho.lengthSq() < 1e-6) ortho.set(0, 1, 0).addScaledVector(forward, -forward.y);
    ortho.normalize();

    return H.clone()
      .addScaledVector(forward, L1 * cosA)
      .addScaledVector(ortho, L1 * sinA);
  },

  /**
   * Computes exact visible horizontal world width at distance `dist` for narrow 9:16 portrait framing!
   * Prevents 100% of left/right subject clipping in YouTube Shorts (`aspect = 9/16 = 0.5625`).
   */
  visibleHorizontalWidth(dist, fovYDeg, aspect = 9 / 16) {
    const fovYRad = THREE.MathUtils.degToRad(fovYDeg);
    const halfW = dist * Math.tan(fovYRad * 0.5) * aspect;
    return halfW * 2.0;
  },
};

/**
 * Build a smooth sealed parametric lofted BufferGeometry from cross-section rings `[row][col][x,y,z]`.
 */
export function buildLoftGeometry(rings, closedRing = true, capEnds = true) {
  const rows = rings.length;
  const cols = rings[0].length;
  const positions = [];
  const uvs = [];
  const indices = [];

  if (closedRing) {
    for (let r = 0; r < rows; r++) {
      const v = r / Math.max(1, rows - 1);
      for (let c = 0; c <= cols; c++) {
        const p = rings[r][c % cols];
        positions.push(p[0], p[1], p[2]);
        uvs.push(c / cols, v);
      }
    }
  } else {
    for (let r = 0; r < rows; r++) {
      const v = r / Math.max(1, rows - 1);
      for (let c = 0; c < cols; c++) {
        const p = rings[r][c];
        positions.push(p[0], p[1], p[2]);
        uvs.push(c / Math.max(1, cols - 1), v);
      }
    }
  }

  const ringCols = closedRing ? cols + 1 : cols;
  for (let r = 0; r < rows - 1; r++) {
    for (let c = 0; c < (closedRing ? cols : cols - 1); c++) {
      const a = r * ringCols + c;
      const b = a + 1;
      const d = (r + 1) * ringCols + c;
      const e = d + 1;
      indices.push(a, d, b, b, d, e);
    }
  }

  if (capEnds && closedRing) {
    const startCenterIdx = positions.length / 3;
    const c0 = rings[0].reduce((acc, p) => [acc[0] + p[0] / cols, acc[1] + p[1] / cols, acc[2] + p[2] / cols], [0, 0, 0]);
    positions.push(c0[0], c0[1], c0[2]);
    uvs.push(0.5, 0.0);
    for (let c = 0; c < cols; c++) indices.push(startCenterIdx, c, c + 1);

    const endCenterIdx = positions.length / 3;
    const cl = rings[rows - 1].reduce((acc, p) => [acc[0] + p[0] / cols, acc[1] + p[1] / cols, acc[2] + p[2] / cols], [0, 0, 0]);
    positions.push(cl[0], cl[1], cl[2]);
    uvs.push(0.5, 1.0);
    const base = (rows - 1) * ringCols;
    for (let c = 0; c < cols; c++) indices.push(endCenterIdx, base + c + 1, base + c);
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}

/**
 * Ground-Contact Ambient Occlusion Shadow Plane (strictly elevated +0.04 above `floorY` -> zero Z-fighting!)
 */
export function createGroundContactAO({ width = 36, depth = 22, opacity = 0.55, floorY = 0.0 } = {}) {
  const c = document.createElement('canvas');
  c.width = 128;
  c.height = 128;
  const ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 4, 64, 64, 62);
  g.addColorStop(0.0, `rgba(0, 0, 0, ${opacity})`);
  g.addColorStop(0.55, `rgba(0, 0, 0, ${opacity * 0.45})`);
  g.addColorStop(1.0, 'rgba(0, 0, 0, 0.0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(c);

  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(width, depth),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false })
  );
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = floorY + 0.04;
  mesh.renderOrder = 2;
  return mesh;
}

/**
 * Built-in Repo Rigged 53-Bone Human `.glb` Asset Paths (ready to load in any new film!)
 */
export const BUILTIN_HUMAN_GLBS = {
  homeowner: '/tools/monarch-cockroach/v4/assets/homeowner.glb',
  researcher: '/tools/monarch-cockroach/v4/assets/researcher.glb',
  athlete: '/tools/monarch-cockroach/v4/assets/athlete.glb',
};

export async function loadRiggedHumanActor(
  glbUrl = BUILTIN_HUMAN_GLBS.researcher,
  { scale = 1750, fallbackColor = '#dde3e8', rimTint = [0.65, 0.78, 0.84], rimStrength = 0.18 } = {}
) {
  const loader = new GLTFLoader();
  const gltf = await loader.loadAsync(glbUrl);
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
        o.material = makeImaxMaterial({
          color: '#ffffff',
          specular: '#3e3834',
          specPower: 0.14,
          map: tex,
          rimTint,
          rimStrength,
          translucent: 0.10,
        });
      } else {
        o.material = makeImaxMaterial({
          color: fallbackColor,
          specular: '#32363c',
          specPower: 0.12,
          rimTint,
          rimStrength: rimStrength * 0.8,
          translucent: 0.04,
        });
      }
    }
  });

  root.scale.setScalar(scale);

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

/**
 * Newtonian Cinema Camera Rig:
 *   - Critically-damped spring impact shake (`impacts: [{ frame, amp, decay, freq }]`)
 *   - Integer-cycle loop-locked organic probe breathing
 *   - Dutch roll (`dutchDeg`)
 *   - Dynamic Z-buffer near/far precision clamping (Zero-Flicker Law #4)
 *   - Screen-space shutter velocity `motionVec` with automatic zeroing across `shotCuts`!
 */
export function createCinemaCameraRig(camera, { totalFrames = 1050, shotCuts = new Set([0]), impacts = [] } = {}) {
  let prevFrame = -999;
  const prevCamPos = new THREE.Vector3();
  const prevLookAt = new THREE.Vector3();
  const motionVec = new THREE.Vector2();
  const camRight = new THREE.Vector3();
  const camUp = new THREE.Vector3();

  function apply({
    frame,
    pos,
    look,
    fov = 44,
    dutchDeg = 0.0,
    breathAmp = 0.16,
    shutterBlurScale = 0.35,
    extraMotionX = 0.0,
    extraMotionY = 0.0,
    minNear = 1.4,
    maxNear = 25.0,
  }) {
    const finalPos = pos.clone();
    const finalLook = look.clone();

    // 1. Integer-cycle loop-locked probe breathing (matches f=totalFrames and f=0 identically!)
    if (breathAmp > 0) {
      const ph = (2 * Math.PI * frame) / Math.max(1, totalFrames);
      finalPos.y += breathAmp * Math.sin(ph * 4.0);
      finalPos.z += breathAmp * 0.75 * Math.cos(ph * 3.0);
    }

    // 2. Critically-damped spring impact shake
    for (const imp of impacts) {
      const df = frame - imp.frame;
      const maxDur = imp.durationFrames ?? 22;
      if (df >= 0 && df <= maxDur) {
        const env = (imp.amp ?? 1.2) * Math.exp(-df * (imp.decay ?? 0.24));
        const freq = imp.freq ?? 1.85;
        finalPos.y += env * Math.sin(df * freq);
        finalPos.z += env * 0.55 * Math.cos(df * (freq * 1.24));
      }
    }

    // 3. Dynamic near/far depth precision bracket (Zero-Flicker Law #4)
    const focusDist = Math.max(5.0, finalPos.distanceTo(finalLook));
    camera.fov = fov;
    camera.near = GLM.clamp(focusDist * 0.08, minNear, maxNear);
    camera.far = Math.max(2400.0, focusDist * 26.0);

    // 4. Dutch roll angle
    const dRad = THREE.MathUtils.degToRad(dutchDeg);
    camera.up.set(0, Math.cos(dRad), Math.sin(dRad)).normalize();
    camera.position.copy(finalPos);
    camera.lookAt(finalLook);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld(true);

    // 5. Screen-space 180°-shutter velocity blur vector (strictly zeroed across hard cuts!)
    // Uses angular lens pan `(dLook - dPos) / focusDist` so a pure tracking dolly (`dPos == dLook`)
    // keeps the locked hero subject razor-sharp while genuine whip-pans produce natural cinema blur!
    if (prevFrame === frame - 1 && !shotCuts.has(frame)) {
      const dPos = finalPos.clone().sub(prevCamPos);
      const dLook = finalLook.clone().sub(prevLookAt);
      const angularPan = dLook.sub(dPos);
      camera.matrixWorld.extractBasis(camRight, camUp, new THREE.Vector3());
      const denom = Math.max(14.0, focusDist);
      const vx = -angularPan.dot(camRight) / denom;
      const vy = -angularPan.dot(camUp) / denom;
      motionVec.set(
        GLM.clamp(vx * shutterBlurScale + extraMotionX, -0.018, 0.018),
        GLM.clamp(vy * shutterBlurScale + extraMotionY, -0.016, 0.016)
      );
    } else {
      motionVec.set(extraMotionX, extraMotionY);
    }

    prevFrame = frame;
    prevCamPos.copy(finalPos);
    prevLookAt.copy(finalLook);

    return { focusDist, motionVec: motionVec.clone() };
  }

  return { apply };
}
