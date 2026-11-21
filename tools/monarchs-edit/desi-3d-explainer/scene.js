// Desi 3D explainer — scene graph for the Monarch Edit channel pilot.
//
// The scene shows the two choices (metal vs wood/lakri) with matching ice
// cubes, the shared "same room" setup and the heat-transfer arrows in the
// reveal beat. It is an illustrative model of the mechanism — not a
// measurement, and not a substitute for the physical run the audit requires.
//
// This module creates no renderer and never touches the DOM: it is safe to
// import in Node for tests. The compositor (main.js) owns the renderer,
// the environment map and the 2D caption layer.

import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import {
  DURATION, clamp, metalMeltAt, woodMeltAt, revealProgress,
} from './timeline.js';

export const WORLD = Object.freeze({
  blockSize: [1.55, 0.5, 1.05],
  gap: 1.72,          // center-to-center distance between the two blocks
  blockCenterY: 0.25,
  blockTop: 0.5,
  cube: 0.62,
  floorRadius: 9,
  arrowBaseY: 0.5,     // arrows sit on the block top
  arrowHeight: 0.42,   // shaft height above the block top
});

const ICE_COLOR = '#dfeeff';
const METAL_COLOR = '#c9ced8';
const WOOD_COLOR = '#9e6b39';

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

  const metalMat = new THREE.MeshStandardMaterial({
    color: METAL_COLOR, roughness: 0.18, metalness: 1.0,
  });
  const woodMat = new THREE.MeshStandardMaterial({
    color: WOOD_COLOR, roughness: 0.78, metalness: 0.02,
  });
  const iceMat = new THREE.MeshStandardMaterial({
    color: ICE_COLOR, roughness: 0.14, metalness: 0.02,
    transparent: true, opacity: 0.94,
    emissive: '#9db8cc', emissiveIntensity: 0.12,
  });

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

  const cubeGeometry = new RoundedBoxGeometry(WORLD.cube, WORLD.cube, WORLD.cube, 2, 0.12);

  const leftCube = new THREE.Mesh(cubeGeometry, iceMat.clone());
  leftCube.position.set(-WORLD.gap / 2, WORLD.blockTop + WORLD.cube / 2, 0);
  leftCube.castShadow = true;
  scene.add(leftCube);

  const rightCube = new THREE.Mesh(cubeGeometry, iceMat.clone());
  rightCube.position.set(WORLD.gap / 2, WORLD.blockTop + WORLD.cube / 2, 0);
  rightCube.castShadow = true;
  scene.add(rightCube);

  // Heat-transfer arrows: block top → ice. Honest direction only, no rates.
  const arrowBase = WORLD.blockTop;
  const arrowHeight = WORLD.arrowHeight;
  const makeArrow = (color) => {
    const group = new THREE.Group();
    group.position.set(0, arrowBase, 0);
    const shaft = new THREE.Mesh(
      new THREE.CylinderGeometry(0.075, 0.075, arrowHeight, 20),
      new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.8, roughness: 0.4 }),
    );
    shaft.position.y = arrowHeight / 2 + 0.05;
    const tip = new THREE.Mesh(
      new THREE.ConeGeometry(0.17, 0.34, 24),
      new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 1.1, roughness: 0.4 }),
    );
    tip.position.y = arrowHeight + 0.05 + 0.17;
    group.add(shaft, tip);
    group.visible = false;
    return group;
  };

  const metalArrow = makeArrow('#ffb454');
  metalArrow.position.x = -WORLD.gap / 2;
  scene.add(metalArrow);

  const woodArrow = makeArrow('#f2b986');
  woodArrow.position.x = WORLD.gap / 2;
  woodArrow.visible = false;
  scene.add(woodArrow);

  function update(t) {
    const time = clamp(t, 0, DURATION);
    const metal = metalMeltAt(time);
    const wood = woodMeltAt(time);

    leftCube.scale.set(
      Math.max(0.3, 1 - 0.4 * metal),
      Math.max(0.06, 1 - metal),
      Math.max(0.3, 1 - 0.4 * metal),
    );
    rightCube.scale.set(
      Math.max(0.3, 1 - 0.4 * wood),
      Math.max(0.06, 1 - wood),
      Math.max(0.3, 1 - 0.4 * wood),
    );
    // Keep the cubes glued to the block top as they shrink.
    leftCube.position.y = WORLD.blockTop + (WORLD.cube * leftCube.scale.y) / 2;
    rightCube.position.y = WORLD.blockTop + (WORLD.cube * rightCube.scale.y) / 2;

    const reveal = revealProgress(time);
    const shimmer = 1 + 0.05 * Math.sin(time * 2.2);
    // The wood arrow never outgrows the metal arrow — illustrative direction.
    metalArrow.visible = reveal > 0.001;
    metalArrow.scale.setScalar(reveal * shimmer);
    woodArrow.visible = reveal > 0.001;
    woodArrow.scale.setScalar(reveal * shimmer * 0.55);

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
