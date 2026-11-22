import * as THREE from 'three';

/**
 * Monarch Cam #03 — V5 Native 1920x1080 Cinema Typography & 3D-Tracked Callout Compositor!
 * Frame-locked to tightened zero-dead-air voice-lock-v5.json (9,008 frames = 300.27s @ 30 fps).
 */
const W = 1920;
const H = 1080;

const COLORS = {
  CREAM: '#fbeed5',
  AMBER: '#ffd187',
  COOL: '#8fe6de',
  MUTED: '#b6c7c4',
  INK: '#081113',
};

function smooth(a, b, x) {
  const t = Math.max(0, Math.min(1, (x - a) / Math.max(1e-5, b - a)));
  return t * t * (3 - 2 * t);
}

function envelope(f, a, b, fadeIn = 10, fadeOut = 9) {
  if (f < a || f > b) return 0;
  return smooth(a, a + fadeIn, f) * (1 - smooth(b - fadeOut, b, f));
}

// Protected pure-cinema climax windows (locked to voice-lock-v5.json): 100% ZERO text overlays!
export const PROTECTED_WINDOWS_V5 = [
  [330, 538],   // Ch01 Cold-open sub-second vanish under the closed oak door
  [4662, 4923], // Ch04 Uninterrupted macro tibial-spine strike & crampon drive
  [8143, 8502], // Ch07 Real-speed 1x doorway traversal & viscoelastic shell rebound
  [8922, 8956], // Ch07 Closing quiet atmospheric hold on illuminated two-penny gap
];

export function isProtectedV5(f) {
  return PROTECTED_WINDOWS_V5.some(([a, b]) => f >= a && f < b);
}

export const EDITORIAL_CALLS_V5 = [
  // CHAPTER 1 [0..921]: Under the Door
  { a: 122,  b: 208,  pre: '01  /  PERIPLANETA AMERICANA', title: 'Half an inch tall', tail: '12.5 mm standing height · 31.1 mm body length', x: 118, y: 152, size: 72, col: COLORS.CREAM, shade: true },
  { a: 218,  b: 325,  pre: 'SCALE REFERENCE  /  3.04 MM', title: 'Two stacked pennies', tail: 'Closed doorway clearance: 3.2 mm', x: 118, y: 152, size: 70, col: COLORS.AMBER, target: 'pennies', shade: true },
  // [330..538] PROTECTED CLIMAX #1
  { a: 545,  b: 765,  pre: 'THE MECHANICAL PARADOX', title: 'Stiff armor, folded in half', tail: '47% vertical compression inside a 3.2 mm crevice', x: 118, y: 152, size: 68, col: COLORS.AMBER, target: 'pronotum', shade: true },
  { a: 780,  b: 912,  pre: 'NO ROOM TO STAND', title: 'How This Cockroach Runs Without Its Feet', tail: 'Jayaram & Full · PNAS 2016 · UC Berkeley', x: 118, y: 156, size: 60, col: COLORS.COOL, target: 'r3Claw', shade: true },

  // CHAPTER 2 [921..2288]: Five Moves Through the Slot
  { a: 1005, b: 1216, pre: '02  /  UC BERKELEY HIGH-SPEED RIG', title: '500 frames per second', tail: 'Resolving five distinct biomechanical moves (288–821 ms)', x: 118, y: 152, size: 70, col: COLORS.AMBER, shade: true },
  { a: 1232, b: 1356, pre: 'MOVE 01  /  SENSORY PROBE', title: 'Antennae sweep the slot', x: 118, y: 152, size: 68, col: COLORS.CREAM, target: 'head', shade: true },
  { a: 1366, b: 1453, pre: 'MOVE 02  /  ENTRY WEDGE', title: 'Head tips down and wedges in', x: 118, y: 152, size: 66, col: COLORS.CREAM, target: 'head', shade: true },
  { a: 1463, b: 1577, pre: 'MOVE 03  /  PRONOTUM SHIELD', title: 'Rolls slightly to slip inside', x: 118, y: 152, size: 66, col: COLORS.AMBER, target: 'pronotum', shade: true },
  { a: 1587, b: 1720, pre: 'MOVE 04  /  EXTERNAL THRUST', title: 'Planted hind legs shove', tail: 'Driving the thickest thoracic section through', x: 118, y: 152, size: 68, col: COLORS.AMBER, target: 'r3Spine', shade: true },
  { a: 1730, b: 1813, pre: 'MOVE 05  /  CLEARANCE', title: 'Flattened abdomen pulls free', x: 118, y: 152, size: 66, col: COLORS.CREAM, target: 'abdomen', shade: true },
  { a: 1826, b: 2010, pre: '3D X-RAY  /  DORSAL TERGITES', title: 'Rigid plates overlap like roof tiles', tail: 'Constant plate chord length — zero rubbery bending', x: 118, y: 152, size: 64, col: COLORS.AMBER, target: 'plate', shade: true },
  { a: 2020, b: 2275, pre: '3D X-RAY  /  ARTHRODIAL MEMBRANE', title: 'Soft hinges fold in half', tail: 'Accordion intersegmental folds absorb 41–57% compression', x: 118, y: 152, size: 66, col: COLORS.COOL, target: 'hinge', shade: true },

  // CHAPTER 3 [2288..3607]: The Low-Ceiling Surprise
  { a: 2302, b: 2675, pre: '03  /  15 CM CONFINED CORRIDOR', title: 'Stepping down the ceiling', tail: '104 trials across controlled acrylic tunnel heights', x: 118, y: 152, size: 68, col: COLORS.CREAM, shade: true },
  { a: 2810, b: 3085, pre: '12 MM  ->  9 MM  ->  6 MM', title: 'Nearly full sprint: 58.1 cm/s', tail: 'Half standing height · 61.1 ms tripod stride beat holds', x: 118, y: 152, size: 66, col: COLORS.AMBER, shade: true },
  { a: 3098, b: 3278, pre: 'DORSAL KINEMATICS', title: 'Legs splay 55° to 75°', tail: 'Foot track stays ~11.9 mm from body midline', x: 118, y: 152, size: 68, col: COLORS.COOL, shade: true },
  { a: 3294, b: 3595, pre: 'BODY COMPRESSION THRESHOLD  /  4 MM', title: 'Speed crashes 4x to 14.5 cm/s', tail: '2 mm lower squeezes the shell · Alternating tripod collapses', x: 118, y: 152, size: 64, col: COLORS.AMBER, shade: true },

  // CHAPTER 4 [3607..5312]: When Shins Become Feet
  { a: 3768, b: 4128, pre: '04  /  OPEN STANCE (12 MM)', title: 'High on hooked claws & soft pads', tail: 'Distal ungues & arolium catch the ground on every step', x: 118, y: 152, size: 64, col: COLORS.CREAM, target: 'r3Claw', shade: true },
  { a: 4144, b: 4342, pre: 'SPLAYED PAST 80°  /  4 MM', title: 'Foot claws tip sideways', tail: 'Lifted +0.47 mm off normal floor engagement', x: 118, y: 152, size: 68, col: COLORS.COOL, target: 'r3Claw', shade: true },
  { a: 4356, b: 4474, pre: 'BIOMECHANICAL ANALOGY  /  >80° SPRAWL', title: 'Wide-arm splayed push-up', tail: 'Palms roll sideways · Vertical leverage collapses', x: 118, y: 152, size: 68, col: COLORS.AMBER, shade: true },
  { a: 4488, b: 4654, pre: 'CONTACT HANDOFF  /  TIBIA', title: 'Shins take over from the feet', x: 118, y: 152, size: 68, col: COLORS.CREAM, target: 'r3Spine', shade: true },
  // [4662..4923] PROTECTED CLIMAX #2: Macro tibial crampon spine strike!
  { a: 4930, b: 5088, pre: 'SYNCHRONOUS OAR STROKE', title: 'Middle legs shove together', tail: 'Rowing in unison like oars under 4 mm confinement', x: 118, y: 152, size: 66, col: COLORS.AMBER, shade: true },
  { a: 5102, b: 5298, pre: 'PROPULSIVE THRUST  /  ~38 mN PER LEG', title: 'Five times body weight', tail: 'Each spiny shin push overcomes roof & ventral drag', x: 118, y: 152, size: 68, col: COLORS.AMBER, target: 'r3Spine', shade: true },

  // CHAPTER 5 [5312..6591]: The Rough-Floor Trap
  { a: 5385, b: 5795, pre: '05  /  FOOTLESS TRACTION TEST', title: 'Tibial spines lock in alone', tail: 'Directional friction holds without feet (mu = 1.73 – 2.04)', x: 118, y: 152, size: 64, col: COLORS.COOL, target: 'r3Spine', shade: true },
  { a: 5870, b: 6214, pre: '638 CONFINED RUNS  /  CEILING DRAG', title: 'Rougher roofs always slow it', tail: '6.64 -> 5.63 -> 0.36 cm/s as overhead rub rises', x: 118, y: 152, size: 66, col: COLORS.CREAM, shade: true },
  { a: 6230, b: 6578, pre: 'FLOOR GRIT TRADE-OFF  /  4 MM', title: 'Medium 40-grit wins (5.26 cm/s)', tail: '100-grit slips (1.57 cm/s) · 20-grit snags flattened belly (3.69 cm/s)', x: 118, y: 152, size: 62, col: COLORS.AMBER, shade: true },

  // CHAPTER 6 [6591..8032]: Tough Shell, Tight Limit
  { a: 6602, b: 6868, pre: '06  /  DISTRIBUTED COMPRESSION', title: 'Up to ~900x body weight', tail: '6.08 N spread across ~3 cm² of hinged plates (2 mm stop)', x: 118, y: 152, size: 68, col: COLORS.AMBER, target: 'platen', shade: true },
  { a: 6884, b: 7172, pre: 'POST-LOAD RECOVERY', title: '76.7 cm/s — unimpaired sprint', tail: 'Zero loss in open-floor velocity after compression', x: 118, y: 152, size: 66, col: COLORS.CREAM, shade: true },
  { a: 7265, b: 7605, pre: '315 GATE ATTEMPTS  /  THE LIMIT', title: '72% pass -> 17% at 3.2 mm', tail: 'Over four out of five attempts fail at two-penny height', x: 118, y: 152, size: 66, col: COLORS.AMBER, shade: true },
  { a: 7620, b: 8018, pre: '3.2 MM OUTCOMES', title: '74% turn back · 9% chest-wedged', tail: 'Antennal sweep rejects tight slots; thickest thorax sets limit', x: 118, y: 152, size: 62, col: COLORS.COOL, target: 'pronotum', shade: true },

  // CHAPTER 7 [8032..9008]: Hinges, Spines & Bio-Inspired CRAM Robot
  { a: 8042, b: 8136, pre: '07  /  REAL-SPEED REPRISE', title: '1x natural speed', x: 118, y: 152, size: 72, col: COLORS.CREAM, shade: true },
  // [8143..8502] PROTECTED CLIMAX #3
  { a: 8512, b: 8684, pre: 'BIOMECHANICAL RESOLUTION', title: 'Solid armor jams · Feet fail inside', tail: 'Compliant arthrodial hinges + tibial crampon spines solve both', x: 118, y: 152, size: 62, col: COLORS.CREAM, shade: true },
  { a: 8700, b: 8914, pre: 'BIO-INSPIRED CRAM ROBOT  /  UC BERKELEY', title: 'Shells that fold · Shins that walk', tail: 'Compressible origami shell (75 -> 35 mm) crawls at ~50% open speed', x: 118, y: 152, size: 64, col: COLORS.AMBER, target: 'cram', shade: true },
  // [8922..8956] PROTECTED CLOSING HOLD!
];

export function projectWorldPoint(worldPt, camera, projVec = new THREE.Vector3()) {
  if (!worldPt || !camera) return null;
  projVec.copy(worldPt).project(camera);
  if (projVec.z < -1 || projVec.z > 1) return null;
  return {
    x: (projVec.x * 0.5 + 0.5) * W,
    y: (-projVec.y * 0.5 + 0.5) * H,
    ndcX: (projVec.x * 0.5 + 0.5),
    ndcY: (-projVec.y * 0.5 + 0.5),
  };
}

export function createEditorialCompositorV5() {
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  const projVec = new THREE.Vector3();

  const poolSprite = document.createElement('canvas');
  poolSprite.width = 256;
  poolSprite.height = 256;
  const pCtx = poolSprite.getContext('2d');
  const pg = pCtx.createRadialGradient(128, 128, 6, 128, 128, 128);
  pg.addColorStop(0.0, 'rgba(6, 13, 16, 0.62)');
  pg.addColorStop(0.55, 'rgba(6, 13, 16, 0.34)');
  pg.addColorStop(1.0, 'rgba(6, 13, 16, 0)');
  pCtx.fillStyle = pg;
  pCtx.fillRect(0, 0, 256, 256);

  function drawFeatheredPool(x, y, rx, ry, alpha) {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.drawImage(poolSprite, x - rx, y - ry, rx * 2, ry * 2);
    ctx.restore();
  }

  function drawCall(call, frame, camera, landmarks) {
    const o = envelope(frame, call.a, call.b, 10, 9);
    if (o <= 0.005) return;
    const settle = smooth(call.a, call.a + 14, frame);
    const dy = (1 - settle) * 14;

    if (call.shade) {
      drawFeatheredPool(call.x + 360, call.y + 34, 610, 215, o);
    }

    ctx.save();
    ctx.globalAlpha = o * 0.94;
    ctx.strokeStyle = call.col;
    ctx.fillStyle = call.col;
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.moveTo(call.x, call.y - 68);
    ctx.lineTo(call.x + 38 * settle, call.y - 68);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(call.x, call.y - 68, 3.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.globalAlpha = o * 0.92;
    ctx.font = '500 24px "IBM Plex Mono", monospace';
    ctx.letterSpacing = '2.2px';
    ctx.fillStyle = call.col === COLORS.COOL ? COLORS.COOL : COLORS.CREAM;
    ctx.fillText(call.pre, call.x, call.y - 36 + dy * 0.5);

    ctx.globalAlpha = o;
    ctx.font = `700 ${call.size}px "Space Grotesk", sans-serif`;
    ctx.letterSpacing = '-1.4px';
    ctx.fillStyle = call.col;
    ctx.fillText(call.title, call.x, call.y + call.size * 0.52 + dy);

    if (call.tail) {
      const tailAlpha = o * smooth(call.a + 4, call.a + 16, frame);
      ctx.globalAlpha = tailAlpha * 0.92;
      ctx.font = '500 28px "Space Grotesk", sans-serif';
      ctx.letterSpacing = '0px';
      ctx.fillStyle = COLORS.CREAM;
      ctx.fillText(call.tail, call.x, call.y + call.size * 0.52 + 44 + dy);
    }

    if (call.target && landmarks && landmarks[call.target]) {
      const lm = landmarks[call.target];
      const pt = lm.isScreen ? lm : projectWorldPoint(lm, camera, projVec);
      if (pt && pt.x > 80 && pt.x < W - 80 && pt.y > 230 && pt.y < H - 80) {
        const startX = call.x + 260;
        const startY = call.y + call.size * 0.52 + (call.tail ? 62 : 22) + dy;
        const dist = Math.hypot(pt.x - startX, pt.y - startY);
        if (dist > 75 && dist < 960) {
          const grow = smooth(call.a + 5, call.a + 20, frame);
          const ux = (pt.x - startX) / dist;
          const uy = (pt.y - startY) / dist;
          const endX = startX + (dist - 18) * grow * ux;
          const endY = startY + (dist - 18) * grow * uy;
          const kneeX = startX + (endX - startX) * 0.42;

          ctx.globalAlpha = o * 0.80;
          ctx.strokeStyle = call.col;
          ctx.lineWidth = 1.85;
          ctx.beginPath();
          ctx.moveTo(startX, startY);
          ctx.lineTo(kneeX, startY);
          ctx.lineTo(endX, endY);
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 7.5, 0, Math.PI * 2);
          ctx.stroke();
        }
      }
    }
    ctx.restore();
  }

  function drawComparisonGauges(frame) {
    // 1. Chapter 3 3-Lane Height Race Legend [3300..3595]
    if (frame >= 3300 && frame <= 3595) {
      const o = envelope(frame, 3300, 3595, 10, 10);
      drawFeatheredPool(960, 965, 680, 95, o * 0.85);
      ctx.save();
      ctx.globalAlpha = o;
      const items = [
        { x: 430, k: '12 MM CEILING', v: '58.1 cm/s · Tripod holds', c: COLORS.CREAM },
        { x: 840, k: '6 MM CEILING',  v: '57.9 cm/s · Tripod holds', c: COLORS.COOL },
        { x: 1260, k: '4 MM SQUEEZE', v: '14.5 cm/s · 4x speed cliff', c: COLORS.AMBER },
      ];
      for (const it of items) {
        ctx.font = '600 20px "IBM Plex Mono", monospace';
        ctx.fillStyle = it.c;
        ctx.fillText(it.k, it.x, 956);
        ctx.font = '500 23px "Space Grotesk", sans-serif';
        ctx.fillStyle = COLORS.CREAM;
        ctx.fillText(it.v, it.x, 986);
      }
      ctx.restore();
    }

    // 2. Chapter 5 3-Lane Grit Trade-off Legend [6235..6578]
    if (frame >= 6235 && frame <= 6578) {
      const o = envelope(frame, 6235, 6578, 10, 10);
      drawFeatheredPool(960, 965, 720, 95, o * 0.85);
      ctx.save();
      ctx.globalAlpha = o;
      const items = [
        { x: 390, k: 'SLICK (100-GRIT)',  v: '1.57 cm/s · Spines slip', c: COLORS.MUTED },
        { x: 830, k: 'MEDIUM (40-GRIT)',  v: '5.26 cm/s · Peak traction', c: COLORS.AMBER },
        { x: 1280, k: 'COARSE (20-GRIT)', v: '3.69 cm/s · Belly snags', c: COLORS.COOL },
      ];
      for (const it of items) {
        ctx.font = '600 20px "IBM Plex Mono", monospace';
        ctx.fillStyle = it.c;
        ctx.fillText(it.k, it.x, 956);
        ctx.font = '500 23px "Space Grotesk", sans-serif';
        ctx.fillStyle = COLORS.CREAM;
        ctx.fillText(it.v, it.x, 986);
      }
      ctx.restore();
    }

    // 3. Chapter 6 3.2 mm Gate Outcome Breakdown [7625..8018]
    if (frame >= 7625 && frame <= 8018) {
      const o = envelope(frame, 7625, 8018, 10, 10);
      drawFeatheredPool(960, 955, 680, 105, o * 0.88);
      ctx.save();
      ctx.globalAlpha = o;
      const stats = [
        { x: 460, pct: '74%', lbl: 'TURNED BACK', sub: 'Rejected after antennal check', c: COLORS.CREAM },
        { x: 880, pct: '17%', lbl: 'PASSED 3.2 MM', sub: 'Cleared two-penny slot (< 1 s)', c: COLORS.AMBER },
        { x: 1300, pct: '9%', lbl: 'CHEST-WEDGED', sub: 'Held at thickest thorax section', c: COLORS.COOL },
      ];
      for (const st of stats) {
        ctx.font = '700 44px "Space Grotesk", sans-serif';
        ctx.fillStyle = st.c;
        ctx.fillText(st.pct, st.x, 938);
        ctx.font = '600 18px "IBM Plex Mono", monospace';
        ctx.fillText(st.lbl, st.x, 964);
        ctx.font = '400 19px "Space Grotesk", sans-serif';
        ctx.fillStyle = COLORS.MUTED;
        ctx.fillText(st.sub, st.x, 990);
      }
      ctx.restore();
    }
  }

  function drawPrimarySourceEndCard(frame) {
    // [8956..9008] Clean PNAS Primary Source Credit Card!
    if (frame < 8956) return;
    const o = smooth(8956, 8970, frame);
    drawFeatheredPool(620, 825, 620, 185, o * 0.92);
    ctx.save();
    ctx.globalAlpha = o * 0.94;
    ctx.strokeStyle = COLORS.AMBER;
    ctx.lineWidth = 2.2;
    ctx.beginPath(); ctx.moveTo(118, 726); ctx.lineTo(162, 726); ctx.stroke();

    ctx.font = '500 22px "IBM Plex Mono", monospace';
    ctx.letterSpacing = '2px';
    ctx.fillStyle = COLORS.AMBER;
    ctx.fillText('PRIMARY RESEARCH  /  ILLUSTRATIVE 3D BIOMECHANICS RECONSTRUCTION', 118, 756);

    ctx.font = '700 42px "Space Grotesk", sans-serif';
    ctx.letterSpacing = '-0.8px';
    ctx.fillStyle = COLORS.CREAM;
    ctx.fillText('Jayaram & Full (2016)', 118, 808);

    ctx.font = '500 26px "Space Grotesk", sans-serif';
    ctx.letterSpacing = '0px';
    ctx.fillStyle = COLORS.COOL;
    ctx.fillText('“Cockroaches traverse crevices, crawl rapidly in confined spaces,', 118, 848);
    ctx.fillText('and inspire a soft, legged robot.”', 118, 882);

    ctx.font = '400 21px "IBM Plex Mono", monospace';
    ctx.fillStyle = COLORS.MUTED;
    ctx.fillText('Proceedings of the National Academy of Sciences · 113(8): E950–E957 · PMC4776529', 118, 922);
    ctx.fillText('University of California, Berkeley · Illustrative CGI reconstruction', 118, 952);
    ctx.restore();
  }

  function renderOverlayTransparent(frame, camera = null, landmarks = null) {
    ctx.clearRect(0, 0, W, H);
    if (isProtectedV5(frame)) return canvas;
    for (const c of EDITORIAL_CALLS_V5) {
      if (frame >= c.a && frame <= c.b) drawCall(c, frame, camera, landmarks);
    }
    drawComparisonGauges(frame);
    drawPrimarySourceEndCard(frame);
    return canvas;
  }

  function renderThumbnailOverlay(webglCanvas) {
    ctx.clearRect(0, 0, W, H);
    ctx.drawImage(webglCanvas, 0, 0, W, H);

    drawFeatheredPool(510, 225, 590, 235, 0.88);
    ctx.save();
    ctx.fillStyle = COLORS.AMBER;
    ctx.font = '600 25px "IBM Plex Mono", monospace';
    ctx.letterSpacing = '2.8px';
    ctx.fillText('3.2 MM CREVICE  ·  NO FEET REQUIRED', 108, 134);

    ctx.fillStyle = COLORS.CREAM;
    ctx.font = '700 90px "Space Grotesk", sans-serif';
    ctx.letterSpacing = '-2.4px';
    ctx.fillText('FOLDED IN HALF', 104, 232);

    ctx.fillStyle = COLORS.AMBER;
    ctx.font = '700 54px "Space Grotesk", sans-serif';
    ctx.letterSpacing = '-1.2px';
    ctx.fillText('Running on Spiny Shins', 108, 304);
    ctx.restore();

    return canvas.toDataURL('image/png');
  }

  const outCanvas = document.createElement('canvas');
  outCanvas.width = W;
  outCanvas.height = H;
  const outCtx = outCanvas.getContext('2d');

  function compositeFrame(webglCanvas, frame, camera = null, landmarks = null) {
    outCtx.clearRect(0, 0, W, H);
    outCtx.drawImage(webglCanvas, 0, 0, W, H);
    renderOverlayTransparent(frame, camera, landmarks);
    outCtx.drawImage(canvas, 0, 0, W, H);
    return outCanvas;
  }

  return { canvas, ctx, renderOverlayTransparent, renderThumbnailOverlay, compositeFrame };
}
