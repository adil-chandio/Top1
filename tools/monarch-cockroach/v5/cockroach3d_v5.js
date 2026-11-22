import * as THREE from 'three';
import { GLM, createCockroachActorV4, createXrayCutawayRigV4 } from '../v4/cockroach3d_v4.js';

export { GLM };

/**
 * Soft radial ground-contact AO shadow texture so every cockroach & robot feels physically weighted!
 */
let cachedContactTex = null;
function getContactShadowTexture() {
  if (cachedContactTex) return cachedContactTex;
  const S = 128;
  const c = document.createElement('canvas');
  c.width = S; c.height = S;
  const ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(S * 0.5, S * 0.5, 4, S * 0.5, S * 0.5, S * 0.5);
  g.addColorStop(0.0, 'rgba(0, 0, 0, 0.62)');
  g.addColorStop(0.55, 'rgba(0, 0, 0, 0.28)');
  g.addColorStop(1.0, 'rgba(0, 0, 0, 0.0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, S, S);
  cachedContactTex = new THREE.CanvasTexture(c);
  return cachedContactTex;
}

/**
 * V5 Cockroach Actor:
 * Adds grounded soft contact-occlusion shadow under thorax/abdomen + deterministic renderOrder!
 */
export function createCockroachActorV5(mats, opts = {}) {
  const actor = createCockroachActorV4(mats, opts);

  const shadowPlane = new THREE.Mesh(
    new THREE.PlaneGeometry(36.0, 17.0),
    new THREE.MeshBasicMaterial({
      map: getContactShadowTexture(),
      transparent: true,
      opacity: 0.52,
      depthWrite: false,
    })
  );
  shadowPlane.rotation.x = -Math.PI / 2;
  shadowPlane.renderOrder = 2;
  actor.root.add(shadowPlane);

  const origUpdate = actor.update;
  actor.update = function updateV5(state = {}) {
    const res = origUpdate(state);
    const ceil = state.ceilingMm ?? 12.52;
    const floorY = state.floorY ?? 0.0;
    const sq = GLM.clamp((12.52 - ceil) / (12.52 - 3.2), 0.0, 1.0);
    // Keep contact AO blob strictly 0.04 mm above floorY (depthWrite=false -> zero Z-fighting!)
    shadowPlane.position.set(
      state.worldX ?? 0.0,
      floorY + 0.04,
      state.worldZ ?? 0.0
    );
    shadowPlane.rotation.z = -(state.yaw ?? 0.0);
    shadowPlane.scale.set(1.0 + 0.08 * sq, 1.0 + 0.32 * sq, 1.0);
    shadowPlane.material.opacity = opts.isGhost ? 0.0 : GLM.mix(0.46, 0.72, sq);
    return res;
  };

  return actor;
}

/**
 * V5 Flicker-Free Full-Body 3D X-Ray & Sagittal Cutaway Rig:
 * Enforces deterministic renderOrder (internal opaque sclerites/hinges first, FrontSide outer glass shell last!)
 */
export function createXrayCutawayRigV5(mats) {
  const rig = createXrayCutawayRigV4(mats);
  rig.group.traverse((o) => {
    if (!o.isMesh) return;
    const mat = Array.isArray(o.material) ? o.material[0] : o.material;
    if (mat === mats.xrayGlassShellMat) {
      o.renderOrder = 16;
      o.castShadow = false;
    } else if (mat === mats.acrylicEdgeMat) {
      o.renderOrder = 18;
      o.castShadow = false;
    } else {
      o.renderOrder = 5;
    }
  });
  return rig;
}

/**
 * V5 Articulated Bio-Inspired CRAM Robot (Compressible Robot with Articulated Mechanisms,
 * Jayaram & Full 2016, PNAS — 75 mm uncompressed -> 35 mm compressed at ~50% open speed!)
 * Actively compresses its laser-cut origami dorsal shell and scuttles with splayed spiny legs!
 */
export function createAnimatedCramRobotV5(mats) {
  const root = new THREE.Group();

  // Base flexible PET/fabric chassis
  const chassis = new THREE.Mesh(new THREE.BoxGeometry(58, 2.8, 34), mats.anodizedBlackMat);
  chassis.position.y = 3.2;
  chassis.castShadow = true;
  root.add(chassis);

  // Micro PCB + glowing status LED inside chassis
  const led = new THREE.Mesh(
    new THREE.SphereGeometry(1.1, 10, 10),
    new THREE.MeshBasicMaterial({ color: '#5ef29b' })
  );
  led.position.set(22, 5.2, 0);
  root.add(led);

  // 6 Articulated overlapping compliant amber-polymer origami dorsal shell plates!
  const shellTiles = [];
  for (let i = 0; i < 6; i++) {
    const pivot = new THREE.Group();
    const w = 36 - i * 1.6;
    const plate = new THREE.Mesh(new THREE.BoxGeometry(12.5, 1.0, w), mats.cutFaceMat);
    const hingeStrip = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.55, w * 0.94), mats.arthrodialMat);
    hingeStrip.position.set(-6.2, -0.2, 0);
    plate.castShadow = true;
    pivot.add(plate, hingeStrip);
    root.add(pivot);
    shellTiles.push(pivot);
  }

  // 4 Articulated splayed compliant robot legs with micro-spines!
  const legs = [];
  for (const [li, sx] of [[-16, 0], [16, 1]].map(([x, idx]) => [idx, x])) {
    for (const sz of [-1, 1]) {
      const hip = new THREE.Group();
      const thigh = new THREE.Mesh(new THREE.BoxGeometry(4.2, 1.2, 16), mats.steelBrushedMat);
      thigh.position.z = sz * 8.0;
      const shin = new THREE.Mesh(new THREE.BoxGeometry(3.4, 1.0, 14), mats.brassMat);
      shin.position.set(0, -1.2, sz * 18.0);
      shin.rotation.x = sz * 0.22;
      thigh.castShadow = true;
      shin.castShadow = true;
      hip.add(thigh, shin);
      hip.position.set(sx, 3.4, sz * 15.0);
      root.add(hip);
      legs.push({ hip, sx, sz, idx: li });
    }
  }

  const shadowBlob = new THREE.Mesh(
    new THREE.PlaneGeometry(72, 48),
    new THREE.MeshBasicMaterial({
      map: getContactShadowTexture(),
      transparent: true,
      opacity: 0.50,
      depthWrite: false,
    })
  );
  shadowBlob.rotation.x = -Math.PI / 2;
  shadowBlob.position.y = 0.05;
  shadowBlob.renderOrder = 2;
  root.add(shadowBlob);

  function update({ worldX = 0, worldZ = 0, yaw = 0, compAlpha = 0.0, phase = 0.0 } = {}) {
    root.position.set(worldX, 0, worldZ);
    root.rotation.y = yaw;

    // Uncompressed arch height ~18.5 mm (scaled representation alongside 31mm roach / 75->35mm ratio = 53% squeeze!)
    const archH = GLM.mix(17.5, 8.2, compAlpha);
    chassis.position.y = GLM.mix(4.2, 2.2, compAlpha);

    for (let i = 0; i < shellTiles.length; i++) {
      const u = i / (shellTiles.length - 1);
      const archCurve = Math.sin(Math.PI * (0.15 + 0.72 * u));
      const tx = 21.0 - i * 8.4;
      const ty = chassis.position.y + 1.8 + archCurve * (archH - 4.0);
      shellTiles[i].position.set(tx, ty, 0);
      shellTiles[i].rotation.z = GLM.mix(0.20 - u * 0.34, 0.05 - u * 0.08, compAlpha);
    }

    for (const lg of legs) {
      const diagPhase = phase + (lg.sx > 0 ? 0.0 : Math.PI) + (lg.sz > 0 ? 0.0 : Math.PI);
      const swing = Math.sin(diagPhase) * 0.28;
      const splayDown = GLM.mix(0.24, 0.05, compAlpha);
      lg.hip.position.y = chassis.position.y;
      lg.hip.rotation.y = swing * lg.sz;
      lg.hip.rotation.x = lg.sz * splayDown;
    }

    return {
      shellTop: new THREE.Vector3(worldX, archH + 1.0, worldZ),
    };
  }

  update({ compAlpha: 0.0 });
  return { root, update };
}
