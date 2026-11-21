// Desi 3D explainer — long-form scene graph for the Monarch Edit channel.
//
// The scene shows the two choices (metal vs lakri / wood) with matching ice
// cubes, the shared "same room" setup and the heat-transfer arrows in the
// payoff beat. It is an illustrative model of the mechanism — not a
// measurement, and not a substitute for the physical run the audit requires.
//
// This module creates no renderer and never touches the DOM: it is safe to
// import in Node for tests. The compositor (main.js) owns the renderer and
// the 2D caption layer. Composed for the 16:9 long-form frame (1280×720),
// distinct from the short-form P1 scene.

import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import {
  DURATION, clamp, metalMeltAt, woodMeltAt, revealProgress,
} from './timeline.js';

export const WORLD = Object.freeze({
  blockSize: [1.7, 0.55, 1.1],
  gap: 2.05,          // center-to-center distance between the two blocks
  blockCenterY: 0.275,
  blockTop: 0.55,
  cube: 0.66,
  floorRadius: 12,
  arrowBaseY: 0.55,     // arrows sit on the block top
  arrowHeight: 0.5,     // shaft height above the block top
});

const ICE_COLOR = '#e2f0ff';
const METAL_COLOR = '#d3d8e2';
const WOOD_COLOR = '#a1733f';

export function createScene() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#131118');

  const hemi = new THREE.HemisphereLight('#8e86b0', '#1c1826', 0.9);
  scene.add(hemi);

  const key = new THREE.DirectionalLight('#fff2df', 2.8);
  key.position.set(-3.6, 6.4, 3.4);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -5, right: 5, top: 5, bottom: -5, near: 0.1, far: 24 });
  key.shadow.camera.updateProjectionMatrix();
  key.shadow.normalBias = 0.02;
  key.shadow.bias = -0.00022;
  scene.add(key);

  const rim = new THREE.DirectionalLight('#79d6c5', 1.35);
  rim.position.set(4.6, 3.4, -2.6);
  scene.add(rim);

  const fill = new THREE.DirectionalLight('#5e83b8', 0.6);
  fill.position.set(0.4, 2.4, 4.6);
  scene.add(fill);

  const floor = new THREE.Mesh(
    new THREE.CircleGeometry(WORLD.floorRadius, 72),
    new THREE.MeshStandardMaterial({ color: '#1a1626', roughness: 0.94, metalness: 0 }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = 0;
  floor.receiveShadow = true;
  scene.add(floor);

  const metalMat = new THREE.MeshStandardMaterial({
    color: METAL_COLOR, roughness: 0.16, metalness: 1.0,
  });
  const woodMat = new THREE.MeshStandardMaterial({
    color: WOOD_COLOR, roughness: 0.76, metalness: 0.02,
  });
  const iceMat = new THREE.MeshStandardMaterial({
    color: ICE_COLOR, roughness: 0.14, metalness: 0.02,
    transparent: true, opacity: 0.94,
    emissive: '#9db8cc', emissiveIntensity: 0.12,
  });

  const blockGeometry = new RoundedBoxGeometry(WORLD.blockSize[0], WORLD.blockSize[1], WORLD.blockSize[2], 4, 0.12);

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

  const cubeGeometry = new RoundedBoxGeometry(WORLD.cube, WORLD.cube, WORLD.cube, 3, 0.13);

  const leftCube = new THREE.Mesh(cubeGeometry, iceMat.clone());
  leftCube.position.set(-WORLD.gap / 2, WORLD.blockTop + WORLD.cube / 2, 0);
  leftCube.castShadow = true;
  scene.add(leftCube);

  const rightCube = new THREE.Mesh(cubeGeometry, iceMat.clone());
  rightCube.position.set(WORLD.gap / 2, WORLD.blockTop + WORLD.cube / 2, 0);
  rightCube.castShadow = true;
  scene.add(rightCube);

  // Heat-transfer arrows: block top → ice. Honest direction only, no rates.
  const arrowBase = WORLD.arrowBaseY;
  const arrowHeight = WORLD.arrowHeight;
  const makeArrow = (color, shaftRadius, shaftEmissive, tipEmissive) => {
    const group = new THREE.Group();
    group.position.set(0, arrowBase, 0);
    const shaft = new THREE.Mesh(
      new THREE.CylinderGeometry(shaftRadius, shaftRadius, arrowHeight, 20),
      new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: shaftEmissive, roughness: 0.4 }),
    );
    shaft.position.y = arrowHeight / 2 + 0.05;
    const tip = new THREE.Mesh(
      new THREE.ConeGeometry(0.19, 0.38, 24),
      new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: tipEmissive, roughness: 0.4 }),
    );
    tip.position.y = arrowHeight + 0.05 + 0.19;
    group.add(shaft, tip);
    group.visible = false;
    return group;
  };

  const metalArrow = makeArrow('#ffb454', 0.085, 0.85, 1.15);
  metalArrow.position.x = -WORLD.gap / 2;
  scene.add(metalArrow);

  const woodArrow = makeArrow('#f2b986', 0.085, 0.75, 0.95);
  woodArrow.position.x = WORLD.gap / 2;
  woodArrow.visible = false;
  scene.add(woodArrow);

  function update(t) {
    const time = clamp(t, 0, DURATION);
    const metal = metalMeltAt(time);
    const wood = woodMeltAt(time);

    leftCube.scale.set(
      Math.max(0.28, 1 - 0.42 * metal),
      Math.max(0.06, 1 - metal),
      Math.max(0.28, 1 - 0.42 * metal),
    );
    rightCube.scale.set(
      Math.max(0.28, 1 - 0.42 * wood),
      Math.max(0.06, 1 - wood),
      Math.max(0.28, 1 - 0.42 * wood),
    );
    // Keep the cubes glued to the block top as they shrink.
    leftCube.position.y = WORLD.blockTop + (WORLD.cube * leftCube.scale.y) / 2;
    rightCube.position.y = WORLD.blockTop + (WORLD.cube * rightCube.scale.y) / 2;

    const reveal = revealProgress(time);
    const shimmer = 1 + 0.05 * Math.sin(time * 2.0);
    // The wood arrow never outgrows the metal arrow — illustrative direction.
    metalArrow.visible = reveal > 0.001;
    metalArrow.scale.setScalar(reveal * shimmer);
    woodArrow.visible = reveal > 0.001;
    woodArrow.scale.setScalar(reveal * shimmer * 0.5);

    return { metal, wood, reveal };
  }

  return {
    scene,
    update,
    world: WORLD,
    refs: {
      floor, hemi, key, rim, fill,
      leftBlock, rightBlock, leftCube, rightCube,
      metalArrow, woodArrow,
    },
  };
}
