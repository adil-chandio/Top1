// E1 — Desi 3D explainer scene (Monarch Edit channel · second pilot).
//
// "Metal Ka Chamach Zyada Thanda Kyun Lagta Hai?" — the same warm paddle
// touches the metal block and the lakri/wood block at the same room
// temperature. The metal is shown draining warmth away faster — a
// direction, not a measurement.
//
// This module creates no renderer and never touches the DOM: it is safe
// to import in Node for tests. The compositor (main.js) owns the renderer,
// the environment map and the 2D caption layer.

import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import {
  DURATION, clamp, metalDrainAt, woodDrainAt, paddleWarmthAt, revealProgress, paddlePose,
} from './timeline.js';

export const WORLD = Object.freeze({
  blockSize: [1.55, 0.5, 1.05],
  gap: 1.72,          // center-to-center distance between the two blocks
  blockCenterY: 0.25,
  blockTop: 0.5,
  paddle: { size: [0.62, 0.55, 0.62], radius: 0.2 },
  floorRadius: 9,
});

const METAL_COLOR = '#c9ced8';
const WOOD_COLOR = '#9e6b39';
const PADDLE_COLOR = '#FFB35C';

export function createScene() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#14121d');

  const hemi = new THREE.HemisphereLight('#8e86b0', '#1c1826', 0.85);
  scene.add(hemi);

  const key = new THREE.DirectionalLight('#fff2df', 2.7);
  key.position.set(-3.4, 6.2, 3.3);
  key.castShadow = true;
  key.shadow.mapSize.set(512, 512);
  Object.assign(key.shadow.camera, { left: -4, right: 4, top: 4, bottom: -4, near: 0.1, far: 20 });
  key.shadow.camera.updateProjectionMatrix();
  key.shadow.normalBias = 0.02;
  key.shadow.bias = -0.00022;
  scene.add(key);

  const rim = new THREE.DirectionalLight('#7fd6c9', 1.35);
  rim.position.set(4.4, 3.4, -2.7);
  scene.add(rim);

  const fill = new THREE.DirectionalLight('#5e83b8', 0.55);
  fill.position.set(0.4, 2.2, 4.5);
  scene.add(fill);

  const floor = new THREE.Mesh(
    new THREE.CircleGeometry(WORLD.floorRadius, 64),
    new THREE.MeshStandardMaterial({ color: '#1d1928', roughness: 0.92, metalness: 0 }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = 0;
  floor.receiveShadow = true;
  scene.add(floor);

  const metalMat = new THREE.MeshStandardMaterial({ color: METAL_COLOR, roughness: 0.18, metalness: 1.0 });
  const woodMat = new THREE.MeshStandardMaterial({ color: WOOD_COLOR, roughness: 0.78, metalness: 0.02 });

  const blockGeometry = new RoundedBoxGeometry(WORLD.blockSize[0], WORLD.blockSize[1], WORLD.blockSize[2], 3, 0.1);

  const leftBlock = new THREE.Mesh(blockGeometry, metalMat);
  leftBlock.position.set(-WORLD.gap / 2, WORLD.blockCenterY, 0);
  leftBlock.castShadow = true;
  leftBlock.receiveShadow = true;
  scene.add(leftBlock);

  const rightBlock = new THREE.Mesh(blockGeometry, woodMat);
  rightBlock.position.set(WORLD.gap / 2, WORLD.blockCenterY, 0);
  rightBlock.castShadow = true;
  rightBlock.receiveShadow = true;
  scene.add(rightBlock);

  // Warm paddle — an illustrative proxy for the spoon/hand. Its emissive
  // warmth drains as it sits on each block: metal drains faster.
  const paddleMat = new THREE.MeshStandardMaterial({
    color: PADDLE_COLOR,
    emissive: PADDLE_COLOR,
    emissiveIntensity: 1.1,
    roughness: 0.42,
    metalness: 0.12,
  });
  const paddle = new THREE.Mesh(
    new RoundedBoxGeometry(WORLD.paddle.size[0], WORLD.paddle.size[1], WORLD.paddle.size[2], 3, WORLD.paddle.radius),
    paddleMat,
  );
  paddle.castShadow = true;
  scene.add(paddle);

  function update(t) {
    const time = clamp(t, 0, DURATION);
    const { x, y } = paddlePose(time);
    paddle.position.set(x, y, 0);

    // Warmth remaining — metal drains faster (illustrative).
    const warmth = paddleWarmthAt(time);
    paddleMat.emissiveIntensity = 0.25 + 0.85 * warmth;
    // Slight breathing so the paddle does not sit dead-steady.
    const shimmer = 1 + 0.03 * Math.sin(time * 2.3);
    paddle.scale.setScalar(shimmer);

    return {
      warmth,
      metalDrain: metalDrainAt(time),
      woodDrain: woodDrainAt(time),
      reveal: revealProgress(time),
      x, y,
    };
  }

  return {
    scene,
    update,
    world: WORLD,
    refs: {
      floor, hemi, key, rim, fill,
      leftBlock, rightBlock, paddle,
    },
  };
}
