// Desi 3D explainer — compositor for the Monarch Edit channel.
//
// One compositor, two pilots — P1 (ice on metal vs lakri) and E1 (metal
// spoon feels cooler). A pilot is selected with the `pilot` query param
// (default p1). Loads the scene, applies the 2D caption layer, and publishes
// window.top1Frame(seconds) → JPEG base64. The render harness (render.mjs)
// drives it headless.

import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import titleFont from '@fontsource-variable/space-grotesk/files/space-grotesk-latin-wght-normal.woff2?url';
import copyFont from '@fontsource-variable/dm-sans/files/dm-sans-latin-wght-normal.woff2?url';
import { PILOTS } from './scenarios.js';

// Register the variable title/copy fonts before the first paint so the
// caption layer uses the channel's type system instead of fallback faces.
const titleFace = new FontFace('Title', `url(${titleFont})`, { weight: '100 900', style: 'normal' });
const copyFace = new FontFace('Copy', `url(${copyFont})`, { weight: '100 900', style: 'normal' });
const fontsReady = Promise.all([titleFace.load(), copyFace.load()])
  .then(([t, c]) => { document.fonts.add(t); document.fonts.add(c); })
  .catch(() => {});

const params = new URLSearchParams(location.search);
const pilotName = params.get('pilot') || 'p1';
const pilot = PILOTS[pilotName];
if (!pilot) throw new Error(`Unknown pilot '${pilotName}' — use one of: ${Object.keys(PILOTS).join(', ')}`);
const tl = pilot.timeline;
const view = pilot.view;
const noOverlay = params.get('overlay') === '0';

const W = tl.FRAME.width;
const H = tl.FRAME.height;
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

const { scene, update, refs } = pilot.createScene();
scene.environment = env;

const camera = new THREE.PerspectiveCamera(38, W / H, 0.07, 90);
scene.update(0);
const lookAt = new THREE.Vector3(0, 0.92, 0);

// Restrained drift from a slight top angle — steady, no jump cuts.
function applyCamera(t) {
  const camT = tl.clamp(t / tl.DURATION);
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
  if (!tl.clockRunningAt(t)) return null;
  return { elapsed: tl.elapsedAt(t), label: tl.clockLabelAt(t) };
}

function drawOverlay(t) {
  const beat = tl.beatAt(t);
  const reveal = tl.revealProgress(t);
  const outro = tl.outroProgress(t);
  const question = tl.questionProgress(t);
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
  text(view.captionTitle, 44, 52, '700 19px Copy', '#f4f1fc');
  text('DESI 3D EXPLAINER', 44, 74, '500 13px Copy', '#dcd6ee');
  ctx.textAlign = 'right';
  text(view.tag, W - 44, 52, '600 15px Copy', '#ffdfa6');
  text(view.window, W - 44, 74, '500 13px Copy', '#eee5c8');
  ctx.textAlign = 'left';

  // Persistent honest badge.
  text(tl.ILLUSTRATION_BADGE, 44, 100, '600 13px Copy', '#ffd98a');

  // Block labels
  ctx.textAlign = 'center';
  ctx.font = '700 22px Title';
  ctx.fillStyle = '#ffffff';
  ctx.fillText(view.labels.left, 205, 690);
  ctx.fillText(view.labels.right, 515, 690);
  ctx.font = '500 13px Copy';
  ctx.fillStyle = '#e3def0';
  ctx.fillText(view.labelSub.left, 205, 712);
  ctx.fillText(view.labelSub.right, 515, 712);
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
    ctx.fillText('CLOCK · SAME CONDITIONS', centerX, 930);
    ctx.textAlign = 'left';
  } else if (beat.id === 'timelapse' || beat.id === 'touch-metal') {
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
    wrapText(tl.CAPTIONS.question, centerX, 1068, W - 150, '700 38px Title', '#fffdfd', 48);
    ctx.globalAlpha = 1;
  } else if (beat.id === 'setup') {
    wrapText(tl.CAPTIONS.setup, centerX, 1086, W - 130, '620 30px Copy', '#ffffff', 38);
  } else if (beat.id === 'timelapse' || beat.id === 'touch-metal' || beat.id === 'touch-wood') {
    wrapText(tl.CAPTIONS[beat.id], centerX, 1086, W - 150, '600 27px Copy', '#fdfdfd', 33);
  } else if (beat.id === 'reveal') {
    ctx.globalAlpha = reveal;
    wrapText(tl.CAPTIONS.reveal, centerX, 1058, W - 120, '700 36px Title', '#fff3d6', 45);
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
    ctx.fillText(view.captionTitle, centerX, 1146);
    ctx.font = '500 18px Copy';
    ctx.fillStyle = '#e9e3f4';
    ctx.fillText(view.captionLine, centerX, 1186);
    ctx.textAlign = 'left';
    ctx.globalAlpha = 1;
  }
  ctx.restore();

  // Beat progress rail
  const index = tl.beatIndexAt(t);
  const railW = (W - 88 - (tl.BEATS.length - 1) * 11) / tl.BEATS.length;
  for (let i = 0; i < tl.BEATS.length; i++) {
    const x = 44 + i * (railW + 11);
    ctx.fillStyle = 'rgba(240,233,255,.24)';
    ctx.fillRect(x, 1252, railW - 7, 3);
    if (i === index) {
      const fraction = tl.beatProgressAt(t);
      ctx.fillStyle = '#ffb454';
      ctx.fillRect(x, 1252, (railW - 7) * fraction, 3);
    } else if (i < index) {
      ctx.fillStyle = 'rgba(240,233,255,.62)';
      ctx.fillRect(x, 1252, railW - 7, 3);
    }
  }

  // Fade in/out edges
  const fade = Math.min(1, Math.max(tl.clamp(t / 0.5), tl.clamp((tl.DURATION - t) / 0.6)));
  if (fade < 1) {
    ctx.fillStyle = `rgba(3,3,8,${0.92 * (1 - fade)})`;
    ctx.fillRect(0, 0, W, H);
  }
}

async function render(t) {
  // Wait once for the variable fonts before drawing the first frame so the
  // caption layer uses the channel type system, not fallback faces.
  await fontsReady;
  const time = tl.clamp(t, 0, tl.DURATION);
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
