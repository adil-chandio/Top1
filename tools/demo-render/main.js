import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import titleFont from '@fontsource-variable/space-grotesk/files/space-grotesk-latin-wght-normal.woff2?url';
import copyFont from '@fontsource-variable/dm-sans/files/dm-sans-latin-wght-normal.woff2?url';
import { findDemo } from '../../src/demos.js';
import { SCENES } from './scenes.js';
import { clamp, cutAt, smooth } from './motion.js';
import { lensStage } from './lens.js';
import { airCrush, labEnvironment } from './air-crush.js';
import { shutterTimes } from './air-crush-motion.js';
import { airCrushTitles } from './air-crush-titles.js';
import { reflectorFilm } from './reflector-film.js';
import { reflectorTitles } from './reflector-titles.js';

const params = new URLSearchParams(location.search);
const film = findDemo(params.get('film') || 'phone-storage');
if (!film) throw new Error('Unknown film.');
const full = params.get('quality') === 'full';
const lab = film.id === 'air-crush';
const optical = film.id === 'reflector';
const custom = lab || optical;
const W = film.width ?? 720;
const H = film.height ?? 1280;
const raster = full ? 1 : optical ? 2 / 3 : lab ? .64 : .55;
const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: false, preserveDrawingBuffer: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1;
renderer.shadowMap.enabled = !custom;
renderer.shadowMap.type = THREE.PCFShadowMap;
const generator = new THREE.PMREMGenerator(renderer);
const room = custom ? null : new RoomEnvironment();
const env = custom ? labEnvironment(generator) : generator.fromScene(room, .065).texture;
room?.dispose(); generator.dispose();
const scene = await (lab ? airCrush : optical ? reflectorFilm : SCENES[film.id])(env);
const expose = lensStage(renderer);
const canvas = document.querySelector('canvas');
canvas.width = W; canvas.height = H;
const ctx = canvas.getContext('2d', { alpha: false });
ctx.imageSmoothingQuality = 'high';
const customTitles = lab ? airCrushTitles(ctx, W, H) : optical ? reflectorTitles(ctx, W, H) : null;
const fonts = [
  new FontFace('Title', `url(${titleFont})`, { weight: '300 700' }),
  new FontFace('Copy', `url(${copyFont})`, { weight: '100 1000' }),
];
await Promise.all(fonts.map(async (font) => document.fonts.add(await font.load())));

const mask = ctx.createLinearGradient(0, 0, 0, H);
mask.addColorStop(0, '#05040be5');
mask.addColorStop(.16, '#05040b13');
mask.addColorStop(.58, '#05040b00');
mask.addColorStop(.86, '#05040bab');
mask.addColorStop(1, '#040309f4');

function text(value, x, y, font, color, maxWidth = 628) {
  ctx.font = font;
  ctx.fillStyle = color;
  ctx.fillText(value, x, y, maxWidth);
}
function rect(x, y, w, h, color) {
  ctx.fillStyle = color; ctx.fillRect(x, y, w, h);
}
function titles(t, cut) {
  ctx.fillStyle = mask; ctx.fillRect(0, 0, W, H);
  rect(43, 48, 26, 2, film.color);
  text('TOP1 KITS  /  SCREENING ROOM', 43, 78, '700 17px Copy', '#f1edfa');
  ctx.textAlign = 'right';
  text(`FILM ${film.number}   ·   9:16`, W - 43, 78, '650 16px Copy', '#eee9f6c5');
  ctx.textAlign = 'left';
  const fade = .60 + .40 * smooth(cut.age / .25);
  ctx.save();
  ctx.globalAlpha = fade;
  rect(43, 958, 33, 2, film.color);
  text(cut.shot.tag, 43, 986, '720 16px Copy', film.color);
  text(cut.shot.lines.join(' '), 40, 1048, '650 63px Title', '#fffdfd');
  text(cut.shot.caption, 43, 1095, '620 28px Copy', '#f1ecf9');
  ctx.restore();
  const rail = (W - 86 - 14) / film.shots.length;
  for (let i = 0; i < film.shots.length; i++) {
    const x = 43 + i * (rail + 7);
    const fraction = i < cut.index ? 1 : i === cut.index ? cut.progress : 0;
    rect(x, 1151, rail, 2, '#f0e9ff46');
    if (fraction > 0) rect(x, 1151, rail * fraction, 2, film.color);
  }
  const fadeOut = clamp((t - film.duration + .53) / .53);
  const fadeIn = clamp((.27 - t) / .27);
  if (fadeIn + fadeOut > 0) rect(0, 0, W, H, `rgba(3, 3, 8, ${.94 * (fadeIn + fadeOut)})`);
}

function render(time, artworkOnly = false) {
  const t = clamp(time, 0, film.duration);
  const cut = cutAt(t, film);
  const scale = artworkOnly ? .84 : raster;
  const width = Math.round(W * scale), height = Math.round(H * scale);
  const samples = lab && !artworkOnly ? shutterTimes(t, cut) : [t];
  for (let i = 0; i < samples.length; i++) {
    const at = samples[i];
    scene.update(at, cutAt(at, film));
    if (custom && (artworkOnly || !(optical ? [0, 1, 9, 17] : [3, 5, 9]).includes(cut.index))) {
      // Deep-focus coverage goes straight through Three's ACES curve. Only
      // the macro shots need a depth render target and focus compositor.
      if (renderer.domElement.width !== width || renderer.domElement.height !== height) renderer.setSize(width, height, false);
      renderer.toneMappingExposure = scene.cam.userData.lens.exposure;
      renderer.render(scene.scene, scene.cam);
    } else {
      renderer.toneMappingExposure = 1;
      expose(scene.scene, scene.cam, width, height, at);
    }
    ctx.globalAlpha = 1 / (i + 1);
    ctx.drawImage(renderer.domElement, 0, 0, W, H);
  }
  ctx.globalAlpha = 1;
  if (!artworkOnly) {
    if (customTitles) customTitles(t, cut);
    else titles(t, cut);
  }
  return canvas.toDataURL('image/jpeg', .94).split(',')[1];
}

window.top1Frame = render;
