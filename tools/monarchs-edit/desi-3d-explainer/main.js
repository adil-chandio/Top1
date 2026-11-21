// Desi 3D explainer — compositor for the Monarch Edit channel.
//
// Loads the scene (scene.js), applies the 2D caption layer, and publishes
// window.top1Frame(seconds) → JPEG base64. The render harness (render.mjs)
// drives it headless.

import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import titleFont from '@fontsource-variable/space-grotesk/files/space-grotesk-latin-wght-normal.woff2?url';
import copyFont from '@fontsource-variable/dm-sans/files/dm-sans-latin-wght-normal.woff2?url';
import { createScene } from './scene.js';
import {
  DURATION, FRAME, ILLUSTRATION_BADGE, BEATS, CAPTIONS,
  clamp, beatAt, beatIndexAt, beatProgressAt, elapsedAt,
  clockRunningAt, questionProgress, revealProgress, outroProgress,
} from './timeline.js';

const W = FRAME.width;
const H = FRAME.height;
const params = new URLSearchParams(location.search);
const noOverlay = params.get('overlay') === '0';

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const generator = new THREE.PMREMGenerator(renderer);
const room = new RoomEnvironment();
const env = generator.fromScene(room, 0.065).texture;
room.dispose();
generator.dispose();

const { scene, update, refs } = createScene();
scene.environment = env;

const camera = new THREE.PerspectiveCamera(38, W / H, 0.07, 90);
scene.update(0);
const lookAt = new THREE.Vector3(0, 0.92, 0);

// Restrained drift from a slight top angle — steady, no jump cuts.
function applyCamera(t) {
  const camT = clamp(t / DURATION);
  camera.position.set(
    1.05 + 0.42 * (1 - camT),
    2.66 - 0.42 * camT,
    4.9 - 0.5 * camT,
  );
  camera.lookAt(lookAt);
}

const canvas = document.querySelector('canvas');
canvas.width = W;
canvas.height = H;
const ctx = canvas.getContext('2d', { alpha: false });
ctx.imageSmoothingQuality = 'high';

function text(value, x, y, font, color, maxWidth = 620) {
  ctx.font = font;
  ctx.fillStyle = color;
  ctx.textAlign = 'left';
  ctx.fillText(value, x, y, maxWidth);
}
function wrapText(value, x, y, maxWidth, font, color, lineHeight) {
  ctx.font = font;
  ctx.fillStyle = color;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  const words = value.split(' ');
  const lines = [];
  let line = '';
  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (ctx.measureText(candidate).width <= maxWidth || !line) line = candidate;
    else { lines.push(line); line = word; }
  }
  if (line) lines.push(line);
  for (const [i, l] of lines.entries()) ctx.fillText(l, x, y + i * lineHeight);
  ctx.textAlign = 'left';
  ctx.textBaseline = 'alphabetic';
  return lines.length;
}
function clockText(t) {
  if (!clockRunningAt(t)) return null;
  return { elapsed: elapsedAt(t), label: `T+${elapsedAt(t).toFixed(1)}s` };
}

function drawOverlay(t) {
  const beat = beatAt(t);
  const reveal = revealProgress(t);
  const outro = outroProgress(t);
  const question = questionProgress(t);
  const centerX = W / 2;

  // Legibility shading only.
  const mask = ctx.createLinearGradient(0, 0, 0, H);
  mask.addColorStop(0, 'rgba(6,5,11,.84)');
  mask.addColorStop(0.14, 'rgba(6,5,11,.28)');
  mask.addColorStop(0.62, 'rgba(6,5,11,0)');
  mask.addColorStop(0.82, 'rgba(6,5,11,.58)');
  mask.addColorStop(1, 'rgba(4,4,9,.96)');
  ctx.fillStyle = mask;
  ctx.fillRect(0, 0, W, H);

  // Header
  text('MONARCHs Edit', 44, 52, '700 19px Copy', '#f4f1fc');
  text('DESI 3D EXPLAINER', 44, 74, '500 13px Copy', '#dcd6ee');
  ctx.textAlign = 'right';
  text('P1 · 3D EDIT', W - 44, 52, '600 15px Copy', '#ffdfa6');
  text(`${DURATION}s · 9:16`, W - 44, 74, '500 13px Copy', '#eee5c8');
  ctx.textAlign = 'left';

  // Persistent honest badge.
  text(ILLUSTRATION_BADGE, 44, 100, '600 13px Copy', '#ffd98a');

  // Block labels (positions tuned to the render — see scene camera).
  ctx.textAlign = 'center';
  ctx.font = '700 22px Title';
  ctx.fillStyle = '#ffffff';
  ctx.fillText('METAL', 205, 690);
  ctx.fillText('LAKRI', 515, 690);
  ctx.font = '500 13px Copy';
  ctx.fillStyle = '#e3def0';
  ctx.fillText('LEFT · LOW-MASS ICE', 205, 712);
  ctx.fillText('RIGHT · LOW-MASS ICE', 515, 712);
  ctx.textAlign = 'left';

  // Shared clock + TIME-LAPSE marker
  const clock = clockText(t);
  if (clock) {
    ctx.textAlign = 'center';
    ctx.font = '750 24px Title';
    ctx.fillStyle = '#ffffff';
    ctx.shadowColor = 'rgba(0,0,0,.5)';
    ctx.shadowBlur = 10;
    ctx.fillText(clock.label, centerX, 906);
    ctx.shadowBlur = 0;
    ctx.font = '600 14px Copy';
    ctx.fillStyle = '#dcd6ef';
    ctx.fillText('CLOCK · SAME ROOM', centerX, 930);
    ctx.textAlign = 'left';
  } else if (beat.id === 'timelapse') {
    ctx.textAlign = 'center';
    ctx.font = '700 22px Title';
    ctx.fillStyle = '#fdfdfd';
    ctx.fillText('TIME-LAPSE', centerX, 908);
    ctx.textAlign = 'left';
  }

  // Beat caption
  ctx.save();
  ctx.shadowColor = 'rgba(0,0,0,.42)';
  ctx.shadowBlur = 12;
  ctx.shadowOffsetY = 4;

  if (beat.id === 'question' && question > 0) {
    ctx.globalAlpha = 0.25 + 0.75 * question;
    wrapText(CAPTIONS.question, centerX, 1068, W - 150, '700 40px Title', '#fffdfd', 50);
    ctx.globalAlpha = 1;
  } else if (beat.id === 'setup') {
    wrapText(CAPTIONS.setup, centerX, 1086, W - 130, '620 30px Copy', '#ffffff', 38);
  } else if (beat.id === 'timelapse') {
    wrapText(CAPTIONS.timelapse, centerX, 1086, W - 150, '620 26px Copy', '#fdfdfd', 32);
  } else if (beat.id === 'reveal') {
    ctx.globalAlpha = reveal;
    wrapText(CAPTIONS.reveal, centerX, 1058, W - 120, '700 38px Title', '#fff3d6', 47);
    ctx.font = '500 18px Copy';
    ctx.textAlign = 'center';
    ctx.fillStyle = '#e9e2f4';
    ctx.fillText('Yeh ek illustrative model hai — yeh koi tested result nahi hai.', centerX, 1198);
    ctx.textAlign = 'left';
    ctx.globalAlpha = 1;
  } else if (beat.id === 'outro' && outro > 0) {
    ctx.globalAlpha = outro;
    ctx.textAlign = 'center';
    ctx.font = '750 34px Title';
    ctx.fillStyle = '#ffffff';
    ctx.fillText('MONARCHs Edit', centerX, 1146);
    ctx.font = '500 18px Copy';
    ctx.fillStyle = '#e9e3f4';
    ctx.fillText('Desi 3D explainer · everyday science, test-first', centerX, 1186);
    ctx.textAlign = 'left';
    ctx.globalAlpha = 1;
  }
  ctx.restore();

  // Beat progress rail
  const index = beatIndexAt(t);
  const railW = (W - 88 - (BEATS.length - 1) * 11) / BEATS.length;
  for (let i = 0; i < BEATS.length; i++) {
    const x = 44 + i * (railW + 11);
    ctx.fillStyle = 'rgba(240,233,255,.24)';
    ctx.fillRect(x, 1252, railW - 7, 3);
    if (i === index) {
      const fraction = beatProgressAt(t);
      ctx.fillStyle = '#ffb454';
      ctx.fillRect(x, 1252, (railW - 7) * fraction, 3);
    } else if (i < index) {
      ctx.fillStyle = 'rgba(240,233,255,.62)';
      ctx.fillRect(x, 1252, railW - 7, 3);
    }
  }

  // Fade in/out edges
  const fade = Math.min(1, Math.max(clamp(t / 0.5), clamp((DURATION - t) / 0.6)));
  if (fade < 1) {
    ctx.fillStyle = `rgba(3,3,8,${0.92 * (1 - fade)})`;
    ctx.fillRect(0, 0, W, H);
  }
}

function render(t) {
  const time = clamp(t, 0, DURATION);
  applyCamera(time);
  update(time);
  renderer.setSize(W, H, false);
  renderer.render(scene, camera);
  ctx.globalAlpha = 1;
  ctx.drawImage(renderer.domElement, 0, 0, W, H);
  if (!noOverlay) drawOverlay(time);
  return canvas.toDataURL('image/jpeg', 0.94).split(',')[1];
}

window.top1Frame = render;
