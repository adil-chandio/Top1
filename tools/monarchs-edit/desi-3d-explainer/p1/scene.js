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
//
// 2026-11-21 next-level pass: ice with physical transmission, growing
// melted-puddle rings, rising steam wisps, softened contact shadows. All
// animation is still illustrative — no conduction, temperature or rate
// numbers are modelled, and the heat arrows stay a direction, not a rate.

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
const STEAM_COLOR = '#eef4fa';

// Procedural soft-disc sprite — DataTexture, no canvas, no DOM, so the
// scene stays importable in Node. Used for the steam wisps.
function softDotTexture() {
  const size = 64;
  const data = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const dx = (x + 0.5) / size - 0.5;
      const dy = (y + 0.5) / size - 0.5;
      const d = Math.sqrt(dx * dx + dy * dy);
      const a = Math.max(0, 1 - d * 2);
      const alpha = Math.pow(a, 2.6) * 255;
      const i = (y * size + x) * 4;
      data[i] = 255; data[i + 1] = 255; data[i + 2] = 255; data[i + 3] = alpha;
    }
  }
  const tex = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
  tex.needsUpdate = true;
  return tex;
}

export function createScene() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#14121d');

  const hemi = new THREE.HemisphereLight('#8e86b0', '#1c1826', 0.85);
  scene.add(hemi);

  const key = new THREE.DirectionalLight('#fff2df', 2.7);
  key.position.set(-3.4, 6.2, 3.3);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
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
    new THREE.MeshPhysicalMaterial({
      color: '#1d1928', roughness: 0.55, metalness: 0,
      clearcoat: 0.4, clearcoatRoughness: 0.6,
    }),
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
  const iceMat = new THREE.MeshPhysicalMaterial({
    color: ICE_COLOR, roughness: 0.12, metalness: 0.02,
    transparent: true, opacity: 0.96,
    transmission: 0.35, thickness: 0.5, ior: 1.31,
    emissive: '#9db8cc', emissiveIntensity: 0.1,
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

  // Melted-puddle rings that grow as the cubes shrink — illustrative only.
  const puddleMatLeft = new THREE.MeshStandardMaterial({
    color: '#d8ecff', roughness: 0.1, metalness: 0,
    transparent: true, opacity: 0,
  });
  const puddleMatRight = puddleMatLeft.clone();
  const puddleGeometry = new THREE.CircleGeometry(0.42, 48);

  const leftPuddle = new THREE.Mesh(puddleGeometry, puddleMatLeft);
  leftPuddle.rotation.x = -Math.PI / 2;
  leftPuddle.position.set(-WORLD.gap / 2, 0.012, 0);
  scene.add(leftPuddle);

  const rightPuddle = new THREE.Mesh(puddleGeometry, puddleMatRight);
  rightPuddle.rotation.x = -Math.PI / 2;
  rightPuddle.position.set(WORLD.gap / 2, 0.012, 0);
  scene.add(rightPuddle);

  // Steam wisps — soft points rising from each cube, opacity tied to melt.
  const dotTexture = softDotTexture();
  const steamMeta = [];
  const steam = (side, xCenter) => {
    const COUNT = 26;
    const positions = new Float32Array(COUNT * 3);
    const meta = [];
    for (let i = 0; i < COUNT; i++) {
      const ox = (Math.random() - 0.5) * 0.46;
      const oz = (Math.random() - 0.5) * 0.46;
      const phase = Math.random() * Math.PI * 2;
      const speed = 0.14 + Math.random() * 0.22;
      const rise = 0.95 + Math.random() * 0.75;
      positions[i * 3] = xCenter;
      positions[i * 3 + 1] = WORLD.blockTop + 0.3;
      positions[i * 3 + 2] = 0;
      meta.push({ ox, oz, phase, speed, rise });
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
      map: dotTexture, size: 0.34, sizeAttenuation: true,
      transparent: true, opacity: 0, depthWrite: false,
      color: STEAM_COLOR, blending: THREE.AdditiveBlending,
    });
    const points = new THREE.Points(geometry, material);
    points.position.set(0, 0, 0);
    points.frustumCulled = false;
    scene.add(points);
    steamMeta.push({ points, meta, xCenter, baseY: WORLD.blockTop + 0.35 });
    return points;
  };

  const leftSteam = steam('left', -WORLD.gap / 2);
  const rightSteam = steam('right', WORLD.gap / 2);

  // Heat-transfer arrows: block top → ice. Honest direction only, no rates.
  const arrowBase = WORLD.arrowBaseY;
  const arrowHeight = WORLD.arrowHeight;
  const makeArrow = (color, shaftRadius = 0.075) => {
    const group = new THREE.Group();
    group.position.set(0, arrowBase, 0);
    const shaft = new THREE.Mesh(
      new THREE.CylinderGeometry(shaftRadius, shaftRadius, arrowHeight, 20),
      new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 1.0, roughness: 0.4 }),
    );
    shaft.position.y = arrowHeight / 2 + 0.05;
    const tip = new THREE.Mesh(
      new THREE.ConeGeometry(0.17, 0.34, 24),
      new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 1.2, roughness: 0.4 }),
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
    // Subtle wobble — illustrative, not a measurement. Rotation only; scale
    // stays governed by the melt curves so the geometry stays honest.
    leftCube.rotation.y = Math.sin(time * 1.9) * 0.02 * metal;
    rightCube.rotation.y = Math.sin(time * 1.9 + 1.3) * 0.02 * wood;
    // Keep the cubes glued to the block top as they shrink.
    leftCube.position.y = WORLD.blockTop + (WORLD.cube * leftCube.scale.y) / 2;
    rightCube.position.y = WORLD.blockTop + (WORLD.cube * rightCube.scale.y) / 2;

    // Puddle spreads and darkens slightly as it melts.
    const leftPuddleScale = 0.35 + metal * 1.05;
    leftPuddle.scale.setScalar(Math.max(0.35, leftPuddleScale));
    leftPuddle.material.opacity = metal * 0.6;
    const rightPuddleScale = 0.35 + wood * 1.05;
    rightPuddle.scale.setScalar(Math.max(0.35, rightPuddleScale));
    rightPuddle.material.opacity = wood * 0.6;

    // Steam wisps rise and fade with the melt.
    const steamProgress = [metal, wood];
    for (const system of steamMeta) {
      const melt = system.xCenter < 0 ? steamProgress[0] : steamProgress[1];
      const material = system.points.material;
      material.opacity = Math.min(0.6, melt * 0.75);
      const attr = system.points.geometry.getAttribute('position');
      for (let i = 0; i < system.meta.length; i++) {
        const m = system.meta[i];
        const cycle = (time * m.speed + m.phase) % 1;
        const riseY = m.rise * cycle;
        attr.setXYZ(
          i,
          system.xCenter + m.ox + Math.sin(time * 1.4 + m.phase) * 0.14,
          system.baseY + riseY,
          Math.sin(time * 0.6 + m.phase) * 0.1 + m.oz * 0.4,
        );
      }
      attr.needsUpdate = true;
    }

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
      leftPuddle, rightPuddle,
      leftSteam, rightSteam,
      metalArrow, woodArrow,
    },
  };
}
