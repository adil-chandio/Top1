// Desi 3D explainer — compositor for the Monarch Edit channel.
//
// One compositor, three pilots — P1 (ice on metal vs lakri), E1 (metal
// spoon feels cooler) and the long-form companion (16:9). A pilot is
// selected with the `pilot` query param (default p1). Loads the scene,
// applies the 2D caption layer, and publishes window.top1Frame(seconds) →
// JPEG base64. The render harness (render.mjs) drives it headless.

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

// The 9:16 layout is the hardcoded fallback so the P1/E1 outputs stay
// exactly as they were. The long-form pilot (16:9) supplies its own layout
// and camera in scenarios.js.
const L = view.layout ?? {
  headerX: 44, headerY: 52, headerRightPad: 44,
  headerTitleFont: '700 19px Copy', headerSubFont: '500 13px Copy', headerTagFont: '600 15px Copy',
  badgeX: 44, badgeY: 100, badgeFont: '600 13px Copy',
  blocksLeftX: 205, blocksRightX: 515, blocksY: 690, blocksSubY: 712,
  blocksFont: '700 22px Title', blocksSubFont: '500 13px Copy',
  clockY: 906, clockSubY: 930, clockFont: '750 24px Title', clockSubFont: '600 14px Copy',
  timelapseY: 908, timelapseFont: '700 22px Title',
  questionY: 1068, questionWrapFrac: 150, questionFont: '700 38px Title', questionLineHeight: 48,
  setupY: 1086, setupWrapFrac: 130, setupFont: '620 30px Copy', setupLineHeight: 38,
  timelapseCaptionY: 1086, timelapseWrapFrac: 150, timelapseFont: '600 27px Copy', timelapseLineHeight: 33,
  revealY: 1058, revealWrapFrac: 120, revealFont: '700 36px Title', revealLineHeight: 45,
  revealDisclaimerY: 1198, revealDisclaimerFont: '500 18px Copy',
  outroY: 1146, outroSubY: 1186, outroTitleFont: '750 34px Title', outroSubFont: '500 18px Copy',
  railLeft: 44, railY: 1252,
  disclaimerText: 'Yeh ek illustrative model hai — yeh koi tested result nahi hai.',
};

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

const cam = view.camera;
const camera = new THREE.PerspectiveCamera(cam?.fov ?? 38, W / H, 0.07, 90);
scene.update(0);
const defaultLookAt = new THREE.Vector3(0, 0.92, 0);
const lookAt = cam ? new THREE.Vector3(cam.lookAt[0], cam.lookAt[1], cam.lookAt[2]) : defaultLookAt;

// Restrained drift — steady, no jump cuts.
function applyCamera(t) {
  const camT = tl.clamp(t / tl.DURATION);
  if (cam) {
    camera.position.set(
      cam.from[0] + (cam.to[0] - cam.from[0]) * camT,
      cam.from[1] + (cam.to[1] - cam.from[1]) * camT,
      cam.from[2] + (cam.to[2] - cam.from[2]) * camT,
    );
  } else {
    camera.position.set(
      1.05 + 0.42 * (1 - camT),
      2.66 - 0.42 * camT,
      4.9 - 0.5 * camT,
    );
  }
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
  text(view.captionTitle, L.headerX, L.headerY, L.headerTitleFont, '#f4f1fc');
  text('DESI 3D EXPLAINER', L.headerX, L.headerY + 22, L.headerSubFont, '#dcd6ee');
  ctx.textAlign = 'right';
  text(view.tag, W - L.headerRightPad, L.headerY, L.headerTagFont, '#ffdfa6');
  text(view.window, W - L.headerRightPad, L.headerY + 22, L.headerSubFont, '#eee5c8');
  ctx.textAlign = 'left';

  // Persistent honest badge.
  text(tl.ILLUSTRATION_BADGE, L.badgeX, L.badgeY, L.badgeFont, '#ffd98a');

  // Block labels
  ctx.textAlign = 'center';
  ctx.font = L.blocksFont;
  ctx.fillStyle = '#ffffff';
  ctx.fillText(view.labels.left, L.blocksLeftX, L.blocksY);
  ctx.fillText(view.labels.right, L.blocksRightX, L.blocksY);
  ctx.font = L.blocksSubFont;
  ctx.fillStyle = '#e3def0';
  ctx.fillText(view.labelSub.left, L.blocksLeftX, L.blocksSubY);
  ctx.fillText(view.labelSub.right, L.blocksRightX, L.blocksSubY);
  ctx.textAlign = 'left';

  // Shared clock + TIME-LAPSE marker
  const clock = clockText(t);
  if (clock) {
    ctx.textAlign = 'center';
    ctx.font = L.clockFont;
    ctx.fillStyle = '#ffffff';
    ctx.shadowColor = 'rgba(0,0,0,.5)';
    ctx.shadowBlur = 10;
    ctx.fillText(clock.label, centerX, L.clockY);
    ctx.shadowBlur = 0;
    ctx.font = L.clockSubFont;
    ctx.fillStyle = '#dcd6ef';
    ctx.fillText('CLOCK · SAME CONDITIONS', centerX, L.clockSubY);
    ctx.textAlign = 'left';
  } else if (beat.id === 'timelapse' || beat.id === 'touch-metal') {
    ctx.textAlign = 'center';
    ctx.font = L.timelapseFont;
    ctx.fillStyle = '#fdfdfd';
    ctx.fillText('TIME-LAPSE', centerX, L.timelapseY);
    ctx.textAlign = 'left';
  }

  // Beat caption
  ctx.save();
  ctx.shadowColor = 'rgba(0,0,0,.42)';
  ctx.shadowBlur = 12;
  ctx.shadowOffsetY = 4;

  if ((beat.id === 'question' || beat.id === 'opening') && question > 0) {
    ctx.globalAlpha = 0.25 + 0.75 * question;
    wrapText(tl.CAPTIONS[beat.id], centerX, L.questionY, W - L.questionWrapFrac, L.questionFont, '#fffdfd', L.questionLineHeight);
    ctx.globalAlpha = 1;
  } else if (beat.id === 'setup' || beat.id === 'proof' || beat.id === 'evidence' || beat.id === 'honesty') {
    wrapText(tl.CAPTIONS[beat.id], centerX, L.setupY, W - L.setupWrapFrac, L.setupFont, '#ffffff', L.setupLineHeight);
  } else if (beat.id === 'timelapse' || beat.id === 'touch-metal' || beat.id === 'touch-wood') {
    wrapText(tl.CAPTIONS[beat.id], centerX, L.timelapseCaptionY, W - L.timelapseWrapFrac, L.timelapseFont, '#fdfdfd', L.timelapseLineHeight);
  } else if (beat.id === 'reveal') {
    ctx.globalAlpha = reveal;
    wrapText(tl.CAPTIONS.reveal, centerX, L.revealY, W - L.revealWrapFrac, L.revealFont, '#fff3d6', L.revealLineHeight);
    ctx.font = L.revealDisclaimerFont;
    ctx.textAlign = 'center';
    ctx.fillStyle = '#e9e2f4';
    ctx.fillText(L.disclaimerText, centerX, L.revealDisclaimerY);
    ctx.textAlign = 'left';
    ctx.globalAlpha = 1;
  } else if (beat.id === 'outro' && outro > 0) {
    ctx.globalAlpha = outro;
    ctx.textAlign = 'center';
    ctx.font = L.outroTitleFont;
    ctx.fillStyle = '#ffffff';
    ctx.fillText(view.captionTitle, centerX, L.outroY);
    ctx.font = L.outroSubFont;
    ctx.fillStyle = '#e9e3f4';
    ctx.fillText(view.captionLine, centerX, L.outroSubY);
    ctx.textAlign = 'left';
    ctx.globalAlpha = 1;
  }
  ctx.restore();

  // Beat progress rail
  const index = tl.beatIndexAt(t);
  const railW = (W - L.railLeft * 2 - (tl.BEATS.length - 1) * 11) / tl.BEATS.length;
  for (let i = 0; i < tl.BEATS.length; i++) {
    const x = L.railLeft + i * (railW + 11);
    ctx.fillStyle = 'rgba(240,233,255,.24)';
    ctx.fillRect(x, L.railY, railW - 7, 3);
    if (i === index) {
      const fraction = tl.beatProgressAt(t);
      ctx.fillStyle = '#ffb454';
      ctx.fillRect(x, L.railY, (railW - 7) * fraction, 3);
    } else if (i < index) {
      ctx.fillStyle = 'rgba(240,233,255,.62)';
      ctx.fillRect(x, L.railY, railW - 7, 3);
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
