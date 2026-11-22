import * as THREE from 'three';

/**
 * Monarch Cam #03 — V4 Native 1920x1080 Cinema Typography & 3D-Tracked Callout Compositor!
 * Frame-locked to Arena voice-02 timeline (10,302 frames = 343.40s @ 30 fps).
 *
 * Strict Monarch Studio rules:
 *   - ZERO rectangular HUD boxes.
 *   - ZERO forced burned-in bottom subtitles (.srt/.vtt sidecars carry captions).
 *   - Protected pure-cinema climax windows stay 100% free of text overlays.
 *   - Space Grotesk (display) + IBM Plex Mono (kickers, metrics, 3D-tracked callouts).
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

function envelope(f, a, b, fadeIn = 12, fadeOut = 10) {
  if (f < a || f > b) return 0;
  return smooth(a, a + fadeIn, f) * (1 - smooth(b - fadeOut, b, f));
}

// Protected pure-cinema climax windows (locked to voice-lock-v4.json): ZERO text overlays!
export const PROTECTED_WINDOWS_V4 = [
  [376, 596],     // Ch01 Cold-open sub-second vanish under the closed oak door
  [5197, 5469],   // Ch04 Uninterrupted macro tibial-spine strike & crampon drive
  [9182, 9572],   // Ch07 Real-speed 1x doorway traversal & viscoelastic shell rebound
  [10017, 10212], // Ch07 Closing quiet atmospheric hold on illuminated two-penny gap
];

export function isProtectedV4(f) {
  return PROTECTED_WINDOWS_V4.some(([a, b]) => f >= a && f < b);
}

export const EDITORIAL_CALLS_V4 = [
  // CHAPTER 1 [0..1080]: Under the Door
  { a: 145,  b: 246,  pre: '01  /  PERIPLANETA AMERICANA', title: 'Half an inch tall', tail: '12.5 mm standing height · 31.1 mm body length', x: 118, y: 152, size: 72, col: COLORS.CREAM, shade: true },
  { a: 254,  b: 372,  pre: 'SCALE REFERENCE  /  3.04 MM', title: 'Two stacked pennies', tail: 'Closed doorway clearance: 3.2 mm', x: 118, y: 152, size: 70, col: COLORS.AMBER, target: 'pennies', shade: true },
  // [376..596] PROTECTED CLIMAX #1
  { a: 604,  b: 842,  pre: 'THE MECHANICAL PARADOX', title: 'Stiff armor, folded in half', tail: '47% vertical compression inside a 3.2 mm crevice', x: 118, y: 152, size: 68, col: COLORS.AMBER, target: 'pronotum', shade: true },
  { a: 856,  b: 1035, pre: 'NO ROOM TO STAND', title: 'How This Cockroach Runs Without Its Feet', tail: 'Jayaram & Full · PNAS 2016 · UC Berkeley', x: 118, y: 156, size: 60, col: COLORS.COOL, target: 'r3Claw', shade: true },

  // CHAPTER 2 [1080..2586]: Five Moves Through the Slot
  { a: 1168, b: 1384, pre: '02  /  UC BERKELEY HIGH-SPEED RIG', title: '500 frames per second', tail: 'Resolving five distinct biomechanical moves (288–821 ms)', x: 118, y: 152, size: 70, col: COLORS.AMBER, shade: true },
  { a: 1400, b: 1534, pre: 'MOVE 01  /  SENSORY PROBE', title: 'Antennae sweep the slot', x: 118, y: 152, size: 68, col: COLORS.CREAM, target: 'head', shade: true },
  { a: 1542, b: 1634, pre: 'MOVE 02  /  ENTRY WEDGE', title: 'Head tips down and wedges in', x: 118, y: 152, size: 66, col: COLORS.CREAM, target: 'head', shade: true },
  { a: 1642, b: 1763, pre: 'MOVE 03  /  PRONOTUM SHIELD', title: 'Rolls slightly to slip inside', x: 118, y: 152, size: 66, col: COLORS.AMBER, target: 'pronotum', shade: true },
  { a: 1771, b: 1909, pre: 'MOVE 04  /  EXTERNAL THRUST', title: 'Planted hind legs shove', tail: 'Driving the thickest thoracic section through', x: 118, y: 152, size: 68, col: COLORS.AMBER, target: 'r3Spine', shade: true },
  { a: 1916, b: 2003, pre: 'MOVE 05  /  CLEARANCE', title: 'Flattened abdomen pulls free', x: 118, y: 152, size: 66, col: COLORS.CREAM, target: 'abdomen', shade: true },
  { a: 2016, b: 2215, pre: '3D X-RAY  /  DORSAL TERGITES', title: 'Rigid plates overlap like roof tiles', tail: 'Constant plate chord length — zero rubbery bending', x: 118, y: 152, size: 64, col: COLORS.AMBER, target: 'plate', shade: true },
  { a: 2224, b: 2498, pre: '3D X-RAY  /  ARTHRODIAL MEMBRANE', title: 'Soft hinges fold in half', tail: 'Accordion intersegmental folds absorb 41–57% compression', x: 118, y: 152, size: 66, col: COLORS.COOL, target: 'hinge', shade: true },

  // CHAPTER 3 [2586..4099]: The Low-Ceiling Surprise
  { a: 2600, b: 2980, pre: '03  /  15 CM CONFINED CORRIDOR', title: 'Stepping down the ceiling', tail: '104 trials across controlled acrylic tunnel heights', x: 118, y: 152, size: 68, col: COLORS.CREAM, shade: true },
  { a: 3150, b: 3440, pre: '12 MM  ->  9 MM  ->  6 MM', title: 'Nearly full sprint: 58.1 cm/s', tail: 'Half standing height · 61.1 ms tripod stride beat holds', x: 118, y: 152, size: 66, col: COLORS.AMBER, shade: true },
  { a: 3452, b: 3655, pre: 'DORSAL KINEMATICS', title: 'Legs splay 55° to 75°', tail: 'Foot track stays ~11.9 mm from body midline', x: 118, y: 152, size: 68, col: COLORS.COOL, shade: true },
  { a: 3668, b: 4015, pre: 'BODY COMPRESSION THRESHOLD  /  4 MM', title: 'Speed crashes 4x to 14.5 cm/s', tail: '2 mm lower squeezes the shell · Alternating tripod collapses', x: 118, y: 152, size: 64, col: COLORS.AMBER, shade: true },

  // CHAPTER 4 [4099..6012]: When Shins Become Feet
  { a: 4240, b: 4638, pre: '04  /  OPEN STANCE (12 MM)', title: 'High on hooked claws & soft pads', tail: 'Distal ungues & arolium catch the ground on every step', x: 118, y: 152, size: 64, col: COLORS.CREAM, target: 'r3Claw', shade: true },
  { a: 4655, b: 4862, pre: 'SPLAYED PAST 80°  /  4 MM', title: 'Foot claws tip sideways', tail: 'Lifted +0.47 mm off normal floor engagement', x: 118, y: 152, size: 68, col: COLORS.COOL, target: 'r3Claw', shade: true },
  { a: 4874, b: 5002, pre: 'BIOMECHANICAL ANALOGY  /  >80° SPRAWL', title: 'Wide-arm splayed push-up', tail: 'Palms roll sideways · Vertical leverage collapses', x: 118, y: 152, size: 68, col: COLORS.AMBER, shade: true },
  { a: 5016, b: 5188, pre: 'CONTACT HANDOFF  /  TIBIA', title: 'Shins take over from the feet', x: 118, y: 152, size: 68, col: COLORS.CREAM, target: 'r3Spine', shade: true },
  // [5197..5469] PROTECTED CLIMAX #2: Macro tibial crampon spine strike!
  { a: 5476, b: 5660, pre: 'SYNCHRONOUS OAR STROKE', title: 'Middle legs shove together', tail: 'Rowing in unison like oars under 4 mm confinement', x: 118, y: 152, size: 66, col: COLORS.AMBER, shade: true },
  { a: 5672, b: 5940, pre: 'PROPULSIVE THRUST  /  ~38 mN PER LEG', title: 'Five times body weight', tail: 'Each spiny shin push overcomes roof & ventral drag', x: 118, y: 152, size: 68, col: COLORS.AMBER, target: 'r3Spine', shade: true },

  // CHAPTER 5 [6012..7456]: The Rough-Floor Trap
  { a: 6095, b: 6490, pre: '05  /  FOOTLESS TRACTION TEST', title: 'Tibial spines lock in alone', tail: 'Directional friction holds without feet (mu = 1.73 – 2.04)', x: 118, y: 152, size: 64, col: COLORS.COOL, target: 'r3Spine', shade: true },
  { a: 6608, b: 6970, pre: '638 CONFINED RUNS  /  CEILING DRAG', title: 'Rougher roofs always slow it', tail: '6.64 -> 5.63 -> 0.36 cm/s as overhead rub rises', x: 118, y: 152, size: 66, col: COLORS.CREAM, shade: true },
  { a: 6988, b: 7385, pre: 'FLOOR GRIT TRADE-OFF  /  4 MM', title: 'Medium 40-grit wins (5.26 cm/s)', tail: '100-grit slips (1.57 cm/s) · 20-grit snags flattened belly (3.69 cm/s)', x: 118, y: 152, size: 62, col: COLORS.AMBER, shade: true },

  // CHAPTER 6 [7456..9070]: Tough Shell, Tight Limit
  { a: 7468, b: 7768, pre: '06  /  DISTRIBUTED COMPRESSION', title: 'Up to ~900x body weight', tail: '6.08 N spread across ~3 cm² of hinged plates (2 mm stop)', x: 118, y: 152, size: 68, col: COLORS.AMBER, target: 'platen', shade: true },
  { a: 7782, b: 8058, pre: 'POST-LOAD RECOVERY', title: '76.7 cm/s — unimpaired sprint', tail: 'Zero loss in open-floor velocity after compression', x: 118, y: 152, size: 66, col: COLORS.CREAM, shade: true },
  { a: 8165, b: 8535, pre: '315 GATE ATTEMPTS  /  THE LIMIT', title: '72% pass -> 17% at 3.2 mm', tail: 'Over four out of five attempts fail at two-penny height', x: 118, y: 152, size: 66, col: COLORS.AMBER, shade: true },
  { a: 8550, b: 8995, pre: '3.2 MM OUTCOMES', title: '74% turn back · 9% chest-wedged', tail: 'Antennal sweep rejects tight slots; thickest thorax sets limit', x: 118, y: 152, size: 62, col: COLORS.COOL, target: 'pronotum', shade: true },

  // CHAPTER 7 [9070..10302]: Hinges and Spines
  { a: 9080, b: 9176, pre: '07  /  REAL-SPEED REPRISE', title: '1x natural speed', x: 118, y: 152, size: 72, col: COLORS.CREAM, shade: true },
  // [9182..9572] PROTECTED CLIMAX #3: Real-speed fold, push, and rebound!
  { a: 9645, b: 9995, pre: 'TWO MECHANISMS WORKING TOGETHER', title: 'Shells that fold · Shins that walk', tail: 'Compliant arthrodial hinges + tibial crampon spines', x: 118, y: 152, size: 66, col: COLORS.AMBER, shade: true },
  // [10017..10212] PROTECTED CLOSING HOLD!
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

export function createEditorialCompositorV4() {
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  const projVec = new THREE.Vector3();

  // Pre-bake feathered pool sprite ONCE at startup (avoids slow per-frame CPU elliptical radialGradient!)
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
    const o = envelope(frame, call.a, call.b, 12, 10);
    if (o <= 0.005) return;
    const settle = smooth(call.a, call.a + 16, frame);
    const dy = (1 - settle) * 14;

    if (call.shade) {
      drawFeatheredPool(call.x + 360, call.y + 34, 610, 215, o);
    }

    ctx.save();
    // 1. Monarch Studio hairline rule + origin dot
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

    // 2. Pre-kicker in IBM Plex Mono
    ctx.globalAlpha = o * 0.92;
    ctx.font = '500 24px "IBM Plex Mono", monospace';
    ctx.letterSpacing = '2.2px';
    ctx.fillStyle = call.col === COLORS.COOL ? COLORS.COOL : COLORS.CREAM;
    ctx.fillText(call.pre, call.x, call.y - 36 + dy * 0.5);

    // 3. Main editorial headline in Space Grotesk
    ctx.globalAlpha = o;
    ctx.font = `700 ${call.size}px "Space Grotesk", sans-serif`;
    ctx.letterSpacing = '-1.4px';
    ctx.fillStyle = call.col;
    ctx.fillText(call.title, call.x, call.y + call.size * 0.52 + dy);

    // 4. Optional crisp scientific sub-line
    if (call.tail) {
      const tailAlpha = o * smooth(call.a + 4, call.a + 18, frame);
      ctx.globalAlpha = tailAlpha * 0.92;
      ctx.font = '500 28px "Space Grotesk", sans-serif';
      ctx.letterSpacing = '0px';
      ctx.fillStyle = COLORS.CREAM;
      ctx.fillText(call.tail, call.x, call.y + call.size * 0.52 + 44 + dy);
    }

    // 5. 3D-Tracked Leader Line stopping 18px short of landmark!
    if (call.target && landmarks && landmarks[call.target]) {
      const lm = landmarks[call.target];
      const pt = lm.isScreen ? lm : projectWorldPoint(lm, camera, projVec);
      if (pt && pt.x > 80 && pt.x < W - 80 && pt.y > 230 && pt.y < H - 80) {
        const startX = call.x + 260;
        const startY = call.y + call.size * 0.52 + (call.tail ? 62 : 22) + dy;
        const dist = Math.hypot(pt.x - startX, pt.y - startY);
        if (dist > 75 && dist < 960) {
          const grow = smooth(call.a + 6, call.a + 22, frame);
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
    // 1. Chapter 3 3-Lane Height Race Legend [3675..4040]
    if (frame >= 3675 && frame <= 4040) {
      const o = envelope(frame, 3675, 4040, 12, 12);
      drawFeatheredPool(960, 975, 860, 115, o);
      ctx.save();
      ctx.globalAlpha = o;
      ctx.textAlign = 'center';
      const cols = [
        { x: 420,  k: '12 MM CEILING', v: '58.1 cm/s · Tripod holds' },
        { x: 960,  k: '6 MM CEILING',  v: '57.9 cm/s · Tripod holds' },
        { x: 1500, k: '4 MM SQUEEZE',  v: '14.5 cm/s · 4x speed cliff', hi: true },
      ];
      for (const item of cols) {
        ctx.font = '600 22px "IBM Plex Mono", monospace';
        ctx.fillStyle = item.hi ? COLORS.AMBER : COLORS.COOL;
        ctx.fillText(item.k, item.x, 962);
        ctx.font = '500 26px "Space Grotesk", sans-serif';
        ctx.fillStyle = COLORS.CREAM;
        ctx.fillText(item.v, item.x, 998);
      }
      ctx.restore();
    }

    // 2. Chapter 5 3-Lane Grit Trade-off Legend [6995..7415]
    if (frame >= 6995 && frame <= 7415) {
      const o = envelope(frame, 6995, 7415, 12, 12);
      drawFeatheredPool(960, 975, 860, 115, o);
      ctx.save();
      ctx.globalAlpha = o;
      ctx.textAlign = 'center';
      const cols = [
        { x: 420,  k: 'SLICK (100-GRIT)',  v: '1.57 cm/s · Spines slip' },
        { x: 960,  k: 'MEDIUM (40-GRIT)',  v: '5.26 cm/s · Peak traction', hi: true },
        { x: 1500, k: 'COARSE (20-GRIT)',  v: '3.69 cm/s · Belly snags' },
      ];
      for (const item of cols) {
        ctx.font = '600 22px "IBM Plex Mono", monospace';
        ctx.fillStyle = item.hi ? COLORS.AMBER : COLORS.MUTED;
        ctx.fillText(item.k, item.x, 962);
        ctx.font = '500 26px "Space Grotesk", sans-serif';
        ctx.fillStyle = COLORS.CREAM;
        ctx.fillText(item.v, item.x, 998);
      }
      ctx.restore();
    }

    // 3. Chapter 6 315 Lab Gate Attempts Ledger [8640..9020]
    if (frame >= 8640 && frame <= 9020) {
      const o = envelope(frame, 8640, 9020, 12, 12);
      drawFeatheredPool(960, 915, 840, 155, o);
      ctx.save();
      ctx.globalAlpha = o;
      ctx.textAlign = 'center';
      const items = [
        { x: 430,  big: '74%', k: 'TURNED BACK', sub: 'Rejected after antennal check', col: COLORS.CREAM },
        { x: 960,  big: '17%', k: 'PASSED 3.2 MM', sub: 'Cleared two-penny slot (< 1 s)', col: COLORS.AMBER },
        { x: 1490, big: '9%',  k: 'CHEST-WEDGED', sub: 'Held at thickest thorax section', col: COLORS.COOL },
      ];
      for (const it of items) {
        ctx.font = '700 76px "Space Grotesk", sans-serif';
        ctx.fillStyle = it.col;
        ctx.fillText(it.big, it.x, 895);
        ctx.font = '600 21px "IBM Plex Mono", monospace';
        ctx.fillStyle = COLORS.CREAM;
        ctx.fillText(it.k, it.x, 936);
        ctx.font = '400 22px "Space Grotesk", sans-serif';
        ctx.fillStyle = COLORS.MUTED;
        ctx.fillText(it.sub, it.x, 968);
      }
      ctx.restore();
    }

    // 4. Closing Primary Research Source Card [10212..10302]
    if (frame >= 10212) {
      const o = smooth(10212, 10234, frame) * (1 - smooth(10288, 10301, frame));
      if (o > 0.01) {
        ctx.save();
        ctx.fillStyle = `rgba(7, 15, 18, ${(0.86 * o).toFixed(3)})`;
        ctx.fillRect(0, 0, W, H);
        ctx.globalAlpha = o;
        ctx.font = '500 23px "IBM Plex Mono", monospace';
        ctx.fillStyle = COLORS.COOL;
        ctx.fillText('PRIMARY RESEARCH  /  ILLUSTRATIVE 3D BIOMECHANICS RECONSTRUCTION', 160, 360);

        ctx.font = '700 56px "Space Grotesk", sans-serif';
        ctx.fillStyle = COLORS.CREAM;
        ctx.fillText('Jayaram & Full (2016)', 160, 444);

        ctx.font = '400 32px "Space Grotesk", sans-serif';
        ctx.fillStyle = COLORS.AMBER;
        ctx.fillText('“Cockroaches traverse crevices, crawl rapidly in confined spaces,', 160, 506);
        ctx.fillText('and inspire a soft, legged robot.”', 160, 550);

        ctx.font = '500 25px "IBM Plex Mono", monospace';
        ctx.fillStyle = COLORS.MUTED;
        ctx.fillText('Proceedings of the National Academy of Sciences · 113(8): E950–E957 · PMC4776529', 160, 624);
        ctx.fillText('University of California, Berkeley · Illustrative CGI reconstruction.', 160, 670);
        ctx.restore();
      }
    }
  }

  function compositeFrame(webglCanvas, frame, camera, landmarks) {
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(webglCanvas, 0, 0, W, H);

    if (!isProtectedV4(frame)) {
      for (const call of EDITORIAL_CALLS_V4) {
        if (frame >= call.a && frame <= call.b) {
          drawCall(call, frame, camera, landmarks);
        }
      }
      drawComparisonGauges(frame);
    }
    return canvas;
  }

  function hasOverlay(frame) {
    if (isProtectedV4(frame)) return false;
    if (frame >= 10212) return true;
    if ((frame >= 3675 && frame <= 4040) || (frame >= 6995 && frame <= 7415) || (frame >= 8640 && frame <= 9020)) return true;
    for (const call of EDITORIAL_CALLS_V4) {
      if (frame >= call.a && frame <= call.b) return true;
    }
    return false;
  }

  function renderOverlayTransparent(frame, screenLandmarks) {
    ctx.clearRect(0, 0, W, H);
    if (!hasOverlay(frame)) return false;
    for (const call of EDITORIAL_CALLS_V4) {
      if (frame >= call.a && frame <= call.b) {
        drawCall(call, frame, null, screenLandmarks);
      }
    }
    drawComparisonGauges(frame);
    return true;
  }

  return { canvas, ctx, compositeFrame, hasOverlay, renderOverlayTransparent };
}
