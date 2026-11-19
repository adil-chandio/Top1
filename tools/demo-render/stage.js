import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { clamp, mix, smooth } from './motion.js';

export const PI = Math.PI;
export const TAU = 2 * PI;
export const V = (x, y, z) => new THREE.Vector3(x, y, z);
export const rng = (seed) => () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };

export function texture(w, h, painter, colorSpace = THREE.SRGBColorSpace) {
  const canvas = document.createElement('canvas');
  canvas.width = w; canvas.height = h;
  painter(canvas.getContext('2d'), w, h);
  const map = new THREE.CanvasTexture(canvas);
  map.colorSpace = colorSpace;
  return map;
}

export function pbr(color, roughness = .35, metalness = .12, extra = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness, metalness, ...extra });
}

export function mesh(parent, geometry, material, x = 0, y = 0, z = 0, cast = false) {
  const item = new THREE.Mesh(geometry, material);
  item.position.set(x, y, z);
  item.castShadow = cast;
  parent.add(item);
  return item;
}

export const bevel = (parent, size, radius, material, xyz = [0, 0, 0], cast = false) =>
  mesh(parent, new RoundedBoxGeometry(...size, 2, radius), material, ...xyz, cast);
export const box = (parent, size, material, xyz = [0, 0, 0], cast = false) =>
  mesh(parent, new THREE.BoxGeometry(...size), material, ...xyz, cast);
export const ring = (parent, r, thickness, material, xyz = [0, 0, 0], arc = TAU) =>
  mesh(parent, new THREE.TorusGeometry(r, thickness, 8, 64, arc), material, ...xyz);
export const cylinder = (parent, rTop, rBottom, h, material, xyz = [0, 0, 0], cast = false) =>
  mesh(parent, new THREE.CylinderGeometry(rTop, rBottom, h, 48), material, ...xyz, cast);

export function strokeMaterial() {
  return texture(128, 128, (c, w, h) => {
    const rand = rng(1913);
    c.fillStyle = '#777'; c.fillRect(0, 0, w, h);
    for (let i = 0; i < 680; i++) {
      c.fillStyle = rand() < .45 ? `rgba(250,250,250,${rand() * .24})` : `rgba(20,20,20,${rand() * .27})`;
      c.fillRect(rand() * w, rand() * h, 4 + rand() * w, .2 + rand() * .85);
    }
  }, THREE.NoColorSpace);
}

function radialMask() {
  return texture(128, 128, (c) => {
    const g = c.createRadialGradient(64, 64, 18, 64, 64, 63);
    g.addColorStop(0, '#fff'); g.addColorStop(.36, '#fff'); g.addColorStop(1, '#000');
    c.fillStyle = g; c.fillRect(0, 0, 128, 128);
  }, THREE.NoColorSpace);
}

export function background(colors) {
  return texture(256, 452, (c, w, h) => {
    const g = c.createLinearGradient(0, 0, w * .16, h);
    g.addColorStop(0, colors[0]); g.addColorStop(.64, colors[1]); g.addColorStop(1, colors[0]);
    c.fillStyle = g; c.fillRect(0, 0, w, h);
    const haze = c.createRadialGradient(w * .3, h * .4, 6, w * .3, h * .4, w * .8);
    haze.addColorStop(0, colors[2]); haze.addColorStop(1, '#00000000');
    c.fillStyle = haze; c.fillRect(0, 0, w, h);
  });
}

export function studio(env, mood, floorMaterial) {
  const scene = new THREE.Scene();
  scene.background = background(mood.bg);
  scene.environment = env;
  scene.environmentIntensity = mood.environment ?? .5;
  scene.add(new THREE.HemisphereLight(mood.sky, mood.ground, mood.ambient ?? .65));
  const key = new THREE.DirectionalLight(mood.key, mood.keyPower ?? 3);
  key.position.copy(mood.keyAt || V(3.6, 6.4, 3.2));
  scene.add(key);
  const rim = new THREE.DirectionalLight(mood.rim, mood.rimPower ?? 2.8);
  rim.position.set(-3.3, 3.15, -2.8);
  scene.add(rim);
  if (floorMaterial) {
    key.castShadow = true;
    key.shadow.mapSize.set(512, 512);
    Object.assign(key.shadow.camera, { left: -3.8, right: 3.8, top: 3.8, bottom: -3.8, near: .1, far: 14 });
    key.shadow.camera.updateProjectionMatrix();
    key.shadow.normalBias = .018;
    key.shadow.bias = -.00022;
    key.shadow.autoUpdate = false;
    key.shadow.needsUpdate = true;
    const floor = mesh(scene, new THREE.PlaneGeometry(24, 24), floorMaterial);
    floor.rotation.x = -PI / 2;
    floor.receiveShadow = true;
    floorMaterial.alphaMap = radialMask();
    floorMaterial.transparent = true;
    floorMaterial.alphaTest = .016;
    floor.renderOrder = -5;
  }
  return scene;
}

export function glowTexture() {
  return texture(96, 96, (c) => {
    const g = c.createRadialGradient(48, 48, 0, 48, 48, 47);
    g.addColorStop(0, '#fff'); g.addColorStop(.14, '#fff9'); g.addColorStop(.45, '#fff2'); g.addColorStop(1, '#fff0');
    c.fillStyle = g; c.fillRect(0, 0, 96, 96);
  });
}

export function lightPool(scene, color, opacity, size, x, z, altitude = .008) {
  const m = new THREE.MeshBasicMaterial({ color, map: glowTexture(), transparent: true, depthWrite: false, opacity, blending: THREE.AdditiveBlending });
  const plane = mesh(scene, new THREE.PlaneGeometry(size, size), m, x, altitude, z);
  plane.rotation.x = -PI / 2;
  plane.renderOrder = 1;
  return plane;
}

export function dust(scene, seed, count, bounds, color, size) {
  const rand = rng(seed);
  const vertices = new Float32Array(count * 3);
  for (let i = 0; i < vertices.length; i++) {
    const pair = bounds[i % 3];
    vertices[i] = mix(pair[0], pair[1], rand());
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
  const material = new THREE.PointsMaterial({ size, color, opacity: .48, transparent: true, depthWrite: false, map: glowTexture(), blending: THREE.AdditiveBlending });
  const cloud = new THREE.Points(geometry, material);
  scene.add(cloud);
  return cloud;
}

export const camera = () => new THREE.PerspectiveCamera(38, 9 / 16, .07, 90);
const axis = V(0, 0, 0);
const delta = V(0, 0, 0);

export function frame(cam, at, position, target, focus, optics) {
  const n = smooth(at);
  cam.position.copy(position[0]).lerp(position[1], n);
  const aim = target[0].clone().lerp(target[1], n);
  cam.lookAt(aim);
  cam.rotateZ(mix(optics.roll?.[0] ?? 0, optics.roll?.[1] ?? 0, n));
  cam.setFocalLength(mix(optics.mm[0], optics.mm[1], n));
  cam.getWorldDirection(axis);
  const focalPlane = focus ? focus[0].clone().lerp(focus[1], smooth(clamp(at * 1.35))) : aim;
  cam.userData.lens = {
    focus: Math.max(cam.near + .01, delta.copy(focalPlane).sub(cam.position).dot(axis)),
    aperture: optics.aperture ?? 8,
    bloom: optics.bloom ?? .45,
    exposure: optics.exposure ?? 1,
    // A restrained camera-velocity smear; hard edits never blend two shots.
    smear: (optics.smear ?? 0) * 4 * at * (1 - at),
  };
}
