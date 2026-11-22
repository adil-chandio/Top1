import * as THREE from 'three';

/**
 * Monarch Studio Native 1920x1080 Cinema Typography, 3D-Tracked Callout Leaders,
 * and Scientific Comparison Gauges — modeled directly on tools/monarch-ant-v3/feature_titles.py
 * and tools/gecko/premiere/titles.js.
 *
 * Strict channel rules:
 *   - ZERO rectangular HUD boxes.
 *   - ZERO forced burned-in bottom subtitles on the 16:9 Long Video (.srt/.vtt sidecars carry captions).
 *   - Protected climax windows stay 100% free of text overlays.
 *   - Space Grotesk (display) + IBM Plex Mono (kickers, metrics, tracked callouts).
 */
const W = 1920;
const H = 1080;

const COLORS = {
  CREAM: '#fbeed5',
  AMBER: '#ffd187',
  COOL: '#a3dcd6',
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

// Protected pure-cinema action climax windows: ZERO text overlays allowed!
const PROTECTED_WINDOWS = [
  [377, 551],     // Scene 01 Cold-open sub-second vanish under the closed door
  [4889, 5236],   // Scene 04 Uninterrupted macro tibial-spine strike & drive stroke
  [9410, 9675],   // Scene 07 Real-speed 1x shingle fold & far-side rebound
  [10083, 10274], // Scene 07 8-second closing quiet hold on empty two-penny gap
];

function isProtected(f) {
  return PROTECTED_WINDOWS.some(([a, b]) => f >= a && f < b);
}

/**
 * Editorial Calls across the 7 chapters (frame-locked to feature.plan & voice-lock.json).
 */
export const EDITORIAL_CALLS = [
  // CHAPTER 1: Under the Door (0..1056)
  { a: 48,   b: 182,  pre: '01  /  ILLUSTRATIVE CGI', title: 'Half an inch tall', tail: 'Adult male Periplaneta americana · 12.5 mm standing', x: 118, y: 156, size: 74, col: COLORS.CREAM, shade: true },
  { a: 202,  b: 358,  pre: 'SCALE REFERENCE  /  3.04 MM', title: 'Two stacked pennies', tail: 'Doorway clearance: 3.2 mm', x: 118, y: 156, size: 72, col: COLORS.AMBER, target: 'pennies', shade: true },
  { a: 562,  b: 645,  pre: 'UNDER ONE SECOND', title: 'How This Cockroach Runs Without Its Feet', tail: 'Jayaram & Full · PNAS 2016', x: 118, y: 162, size: 62, col: COLORS.AMBER, shade: true },
  { a: 660,  b: 842,  pre: 'THE MECHANICAL PARADOX', title: 'Stiff armor, folded in half', tail: '12.5 mm standing height -> 3.2 mm slot', x: 118, y: 156, size: 68, col: COLORS.CREAM, target: 'pronotum', shade: true },
  { a: 860,  b: 1025, pre: 'NO ROOM TO STAND', title: 'Feet lose their stance', tail: 'What pushes the body through?', x: 118, y: 156, size: 72, col: COLORS.COOL, target: 'r3Claw', shade: true },

  // CHAPTER 2: Five Moves Through the Slot (1056..2578)
  { a: 1072, b: 1168, pre: '02  /  HIGH-SPEED RECONSTRUCTION', title: '500 frames per second', tail: 'Five distinct moves through a 3.2 mm gate', x: 118, y: 152, size: 72, col: COLORS.AMBER, shade: true },
  { a: 1182, b: 1292, pre: 'MOVE 01  /  SENSORY PROBE', title: 'Antennae sweep the slot', x: 118, y: 152, size: 68, col: COLORS.CREAM, target: 'head', shade: true },
  { a: 1306, b: 1420, pre: 'MOVE 02  /  ENTRY WEDGE', title: 'Head tips down', x: 118, y: 152, size: 72, col: COLORS.CREAM, target: 'head', shade: true },
  { a: 1435, b: 1555, pre: 'MOVE 03  /  PRONOTUM SHIELD', title: 'Slight roll into the gap', x: 118, y: 152, size: 68, col: COLORS.AMBER, target: 'pronotum', shade: true },
  { a: 1570, b: 1700, pre: 'MOVE 04  /  EXTERNAL THRUST', title: 'Planted hind legs shove', tail: 'Pushing the thickest chest section inside', x: 118, y: 152, size: 68, col: COLORS.AMBER, target: 'r3Spine', shade: true },
  { a: 1716, b: 1826, pre: 'MOVE 05  /  EXIT', title: 'Flattened abdomen clears', x: 118, y: 152, size: 68, col: COLORS.CREAM, target: 'abdomen', shade: true },
  { a: 1972, b: 2102, pre: 'CUTAWAY  /  SAGITTAL SCHEMATIC', title: 'Rigid chitin plates', tail: 'Overlapping like roof tiles · Constant plate length', x: 118, y: 154, size: 72, col: COLORS.AMBER, target: 'plate', shade: false },
  { a: 2114, b: 2254, pre: 'CUTAWAY  /  ARTHRODIAL MEMBRANE', title: 'Soft hinges fold in half', tail: '47% vertical compression without cracking a plate', x: 118, y: 154, size: 68, col: COLORS.COOL, target: 'hinge', shade: false },
  { a: 2390, b: 2510, pre: 'VISCOELASTIC REBOUND', title: 'Springs back on exit', x: 118, y: 154, size: 70, col: COLORS.CREAM, shade: true },

  // CHAPTER 3: The Low-Ceiling Surprise (2578..4135)
  { a: 2595, b: 2700, pre: '03  /  15 CM CONFINED CORRIDOR', title: 'When the whole roof stays low', tail: '104 laboratory trials across ceiling heights', x: 118, y: 152, size: 66, col: COLORS.CREAM, shade: true },
  { a: 2715, b: 3095, pre: '12 MM  ->  9 MM  ->  6 MM', title: 'Nearly full sprint: ~58 cm/s', tail: 'Down to half standing height · 61 ms stride beat holds', x: 118, y: 152, size: 66, col: COLORS.AMBER, shade: true },
  { a: 3255, b: 3505, pre: 'OVERHEAD KINEMATICS', title: 'Legs splay 55° to 75°', tail: 'Foot track stays near 11.9 mm from midline', x: 118, y: 152, size: 70, col: COLORS.COOL, shade: true },
  { a: 3642, b: 3902, pre: 'TWO MILLIMETERS LOWER  /  4 MM', title: 'Speed crashes to 14.5 cm/s', tail: 'A fourfold drop once the ceiling squeezes the shell', x: 118, y: 152, size: 68, col: COLORS.AMBER, shade: false },
  { a: 3916, b: 4075, pre: 'GAIT BREAKDOWN', title: 'Tripod rhythm falls apart', x: 118, y: 152, size: 70, col: COLORS.CREAM, shade: true },

  // CHAPTER 4: When Shins Become Feet (4135..6074)
  { a: 4274, b: 4558, pre: '04  /  OPEN STANCE (12 MM)', title: 'High on tarsal claws & pads', tail: 'Distal foot hooks catch the floor on every step', x: 118, y: 152, size: 66, col: COLORS.CREAM, target: 'r3Claw', shade: true },
  { a: 4574, b: 4880, pre: 'SPLAYED PAST 80°  /  4 MM', title: 'Foot claws tip sideways', tail: 'Lifted +0.48 mm off normal engagement angle', x: 118, y: 152, size: 68, col: COLORS.COOL, target: 'r3Claw', shade: true },
  // [4889..5236] PROTECTED CLIMAX: Uninterrupted macro tibial-spine plant & drive stroke!
  { a: 5244, b: 5525, pre: 'SYNCHRONOUS OAR STROKE', title: 'Middle legs shove together', tail: 'Rowing like a pair of oars under 4 mm confinement', x: 118, y: 152, size: 66, col: COLORS.AMBER, shade: true },
  { a: 5542, b: 5818, pre: 'PROPULSIVE FORCE  /  ~38 mN PER LEG', title: 'Five times body weight', tail: 'Overcoming roof & belly drag on each spiny shin push', x: 118, y: 152, size: 70, col: COLORS.AMBER, target: 'r3Spine', shade: true },

  // CHAPTER 5: The Rough-Floor Trap (6074..7617)
  { a: 6218, b: 6498, pre: '05  /  FRICTION ISOLATION', title: 'Tibial spines lock in alone', tail: 'Directional grip holds without tarsal foot contact (mu = 1.73 - 2.04)', x: 118, y: 152, size: 64, col: COLORS.COOL, target: 'r3Spine', shade: false },
  { a: 6650, b: 6922, pre: '638 CONFINED RUNS  /  CEILING RUB', title: 'Rougher roofs always slow it', tail: '6.64 -> 5.63 -> 0.36 cm/s as ceiling friction rises', x: 118, y: 152, size: 66, col: COLORS.CREAM, shade: false },
  { a: 6936, b: 7352, pre: 'FLOOR GRIT TRADE-OFF  /  4 MM', title: 'Medium grit wins (5.26 cm/s)', tail: 'Slick 100-grit slips (1.57) · Coarse 20-grit snags the belly (3.69)', x: 118, y: 152, size: 64, col: COLORS.AMBER, shade: false },

  // CHAPTER 6: Tough Shell, Tight Limit (7617..9282)
  { a: 7625, b: 7922, pre: '06  /  DISTRIBUTED COMPRESSION', title: 'Up to ~900x body weight', tail: 'Spread across ~3 cm2 of hinged plates (2 mm safety stop)', x: 118, y: 152, size: 70, col: COLORS.AMBER, target: 'platen', shade: false },
  { a: 7935, b: 8075, pre: 'POST-LOAD SPRINT', title: '76.7 cm/s — unimpaired', tail: 'No loss in open-floor running speed afterward', x: 118, y: 152, size: 68, col: COLORS.CREAM, shade: true },
  { a: 8234, b: 8532, pre: '315 GATE ATTEMPTS  /  THE LIMIT', title: '72% pass -> 17% at 3.2 mm', tail: 'More than four out of five attempts fail at two-penny height', x: 118, y: 152, size: 66, col: COLORS.AMBER, shade: true },
  { a: 8545, b: 8850, pre: '3.2 MM OUTCOMES', title: '74% turn back · 9% chest-wedged', tail: 'Antennae reject most narrow slots; thickest thorax sets the limit', x: 118, y: 152, size: 62, col: COLORS.COOL, target: 'pronotum', shade: true },

  // CHAPTER 7: Hinges and Spines (9282..10461)
  { a: 9292, b: 9404, pre: '07  /  REAL-SPEED REPRISE', title: '1x natural speed', x: 118, y: 152, size: 72, col: COLORS.CREAM, shade: true },
  // [9410..9675] PROTECTED CLIMAX: Real-speed fold, push, and rebound!
  { a: 9808, b: 9936, pre: 'TWO MECHANISMS WORKING TOGETHER', title: 'Shells that fold · Shins that walk', x: 118, y: 152, size: 68, col: COLORS.AMBER, shade: true },
];

export function projectWorldPoint(worldPt, camera, projVec = new THREE.Vector3()) {
  if (!worldPt) return null;
  projVec.copy(worldPt).project(camera);
  if (projVec.z < -1 || projVec.z > 1) return null;
  return {
    x: (projVec.x * 0.5 + 0.5) * W,
    y: (-projVec.y * 0.5 + 0.5) * H,
    ndcX: (projVec.x * 0.5 + 0.5),
    ndcY: (-projVec.y * 0.5 + 0.5),
  };
}

export function createEditorialCompositor() {
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  const projVec = new THREE.Vector3();

  function projectToScreen(worldPt, camera) {
    if (!worldPt) return null;
    if (worldPt.isScreen) return worldPt;
    return projectWorldPoint(worldPt, camera, projVec);
  }

  function drawFeatheredPool(x, y, rx, ry, alpha) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(rx, ry);
    const g = ctx.createRadialGradient(0, 0, 0.05, 0, 0, 1.0);
    g.addColorStop(0.0, `rgba(6, 13, 15, ${(0.58 * alpha).toFixed(3)})`);
    g.addColorStop(0.55, `rgba(6, 13, 15, ${(0.32 * alpha).toFixed(3)})`);
    g.addColorStop(1.0, 'rgba(6, 13, 15, 0)');
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(0, 0, 1.0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawCall(call, frame, camera, landmarks) {
    const o = envelope(frame, call.a, call.b, 12, 10);
    if (o <= 0.005) return;
    const settle = smooth(call.a, call.a + 16, frame);
    const dy = (1 - settle) * 14;

    if (call.shade) {
      drawFeatheredPool(call.x + 340, call.y + 34, 560, 210, o);
    }

    ctx.save();
    // 1. Hairline rule + origin dot (Monarch Cam signature)
    ctx.globalAlpha = o * 0.92;
    ctx.strokeStyle = call.col;
    ctx.fillStyle = call.col;
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.moveTo(call.x, call.y - 68);
    ctx.lineTo(call.x + 36 * settle, call.y - 68);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(call.x, call.y - 68, 3.4, 0, Math.PI * 2);
    ctx.fill();

    // 2. Pre-kicker in IBM Plex Mono
    ctx.globalAlpha = o * 0.90;
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
      ctx.font = '500 29px "Space Grotesk", sans-serif';
      ctx.letterSpacing = '0px';
      ctx.fillStyle = COLORS.CREAM;
      ctx.fillText(call.tail, call.x, call.y + call.size * 0.52 + 44 + dy);
    }

    // 5. 3D-Tracked Leader Line to exact projected anatomical / prop landmark!
    if (call.target && landmarks[call.target]) {
      const pt = projectToScreen(landmarks[call.target], camera);
      if (pt && pt.x > 80 && pt.x < W - 80 && pt.y > 120 && pt.y < H - 70) {
        const startX = call.x + 260;
        const startY = call.y + call.size * 0.52 + (call.tail ? 62 : 22) + dy;
        const dist = Math.hypot(pt.x - startX, pt.y - startY);
        if (dist > 70 && dist < 980) {
          const grow = smooth(call.a + 6, call.a + 22, frame);
          // Stop 18px short of landmark so we NEVER obscure the anatomy/spine contact itself!
          const ux = (pt.x - startX) / dist;
          const uy = (pt.y - startY) / dist;
          const endX = startX + (dist - 18) * grow * ux;
          const endY = startY + (dist - 18) * grow * uy;
          const kneeX = startX + (endX - startX) * 0.42;

          ctx.globalAlpha = o * 0.78;
          ctx.strokeStyle = call.col;
          ctx.lineWidth = 1.85;
          ctx.beginPath();
          ctx.moveTo(startX, startY);
          ctx.lineTo(kneeX, startY);
          ctx.lineTo(endX, endY);
          ctx.stroke();

          // Delicate target ring around landmark
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 7.5, 0, Math.PI * 2);
          ctx.stroke();
        }
      }
    }
    ctx.restore();
  }

  /**
   * Clean bottom-aligned comparison lane labels during multi-lane studio shots
   * (matching Monarch-Cam-Ant-V3 "MOCK vs RESTRAINED" plate!).
   */
  function drawComparisonLegend(frame, mode) {
    if (mode === 32 || mode === 34) {
      const o = envelope(frame, mode === 32 ? 3112 : 3638, mode === 32 ? 3242 : 3904, 10, 10);
      if (o <= 0.01) return;
      ctx.save();
      ctx.globalAlpha = o;
      ctx.textAlign = 'center';
      const cols = [
        { x: 420,  k: '12 MM CEILING', v: '58.1 cm/s · Tripod' },
        { x: 960,  k: '6 MM CEILING',  v: '57.9 cm/s · Tripod holds' },
        { x: 1500, k: '4 MM SQUEEZE',  v: '14.5 cm/s · 4x cliff', hi: true },
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
    } else if (mode === 52 || mode === 54) {
      const o = envelope(frame, mode === 52 ? 6510 : 6932, mode === 52 ? 6638 : 7070, 10, 10);
      if (o <= 0.01) return;
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
    } else if (mode === 63) {
      // 315 Lab Gate Attempts Ledger (8856..9009)
      const o = envelope(frame, 8860, 9005, 12, 10);
      if (o <= 0.01) return;
      drawFeatheredPool(960, 860, 820, 190, o);
      ctx.save();
      ctx.globalAlpha = o;
      ctx.textAlign = 'center';
      const items = [
        { x: 430,  big: '74%', k: 'TURNED BACK', sub: 'Rejected after antennal check', col: COLORS.CREAM },
        { x: 960,  big: '17%', k: 'TRAVERSED 3.2 MM', sub: 'Cleared two-penny slot (< 1 s)', col: COLORS.AMBER },
        { x: 1490, big: '9%',  k: 'THORAX-WEDGED', sub: 'Held at thickest chest section', col: COLORS.COOL },
      ];
      for (const it of items) {
        ctx.font = '700 84px "Space Grotesk", sans-serif';
        ctx.fillStyle = it.col;
        ctx.fillText(it.big, it.x, 865);
        ctx.font = '600 22px "IBM Plex Mono", monospace';
        ctx.fillStyle = COLORS.CREAM;
        ctx.fillText(it.k, it.x, 908);
        ctx.font = '400 23px "Space Grotesk", sans-serif';
        ctx.fillStyle = COLORS.MUTED;
        ctx.fillText(it.sub, it.x, 942);
      }
      ctx.restore();
    } else if (mode === 74) {
      // Closing readable Primary Science Credits (10274..10461)
      const o = envelope(frame, 10282, 10452, 18, 18);
      if (o <= 0.01) return;
      ctx.save();
      ctx.fillStyle = `rgba(7, 15, 18, ${(0.82 * o).toFixed(3)})`;
      ctx.fillRect(0, 0, W, H);
      ctx.globalAlpha = o;
      ctx.font = '500 23px "IBM Plex Mono", monospace';
      ctx.fillStyle = COLORS.COOL;
      ctx.fillText('PRIMARY RESEARCH  /  ILLUSTRATIVE 3D RECONSTRUCTION', 160, 360);

      ctx.font = '700 54px "Space Grotesk", sans-serif';
      ctx.fillStyle = COLORS.CREAM;
      ctx.fillText('Jayaram & Full (2016)', 160, 442);

      ctx.font = '400 32px "Space Grotesk", sans-serif';
      ctx.fillStyle = COLORS.AMBER;
      ctx.fillText('“Cockroaches traverse crevices, crawl rapidly in confined spaces,', 160, 504);
      ctx.fillText('and inspire a soft, legged robot.”', 160, 548);

      ctx.font = '500 25px "IBM Plex Mono", monospace';
      ctx.fillStyle = COLORS.MUTED;
      ctx.fillText('Proceedings of the National Academy of Sciences · 113(8): E950–E957 · PMC4776529', 160, 622);
      ctx.fillText('All visuals are illustrative biomechanical CGI, not study high-speed footage.', 160, 668);
      ctx.restore();
    }
  }

  /**
   * Composite WebGL canvas onto 1920x1080 master canvas + editorial layer,
   * and return projected landmarks row for projection.csv.
   */
  function compositeFrame(webglCanvas, frame, mode, camera, landmarks) {
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(webglCanvas, 0, 0, W, H);

    if (!isProtected(frame)) {
      for (const call of EDITORIAL_CALLS) {
        if (frame >= call.a && frame <= call.b) {
          drawCall(call, frame, camera, landmarks);
        }
      }
      drawComparisonLegend(frame, mode);
    }

    // Export normalized [0..1] screen projections for projection.csv audit!
    const trace = {};
    for (const key of ['head', 'pronotum', 'hinge', 'r3Spine', 'r3Claw', 'pennies', 'platen']) {
      const p = projectToScreen(landmarks[key], camera);
      trace[key + '_x'] = p ? +p.ndcX.toFixed(4) : -1;
      trace[key + '_y'] = p ? +p.ndcY.toFixed(4) : -1;
    }
    return { canvas, ctx, trace };
  }

  function hasActiveOverlay(frame, mode) {
    if (isProtected(frame)) return false;
    for (const call of EDITORIAL_CALLS) {
      if (frame >= call.a && frame <= call.b) return true;
    }
    if (mode === 32 || mode === 34 || mode === 52 || mode === 54 || mode === 63 || mode === 74) return true;
    return false;
  }

  function renderOverlayPNG(frame, mode, normRow) {
    if (!hasActiveOverlay(frame, mode)) return null;
    ctx.clearRect(0, 0, W, H);
    const screenLandmarks = {};
    if (normRow) {
      for (const key of ['head', 'pronotum', 'hinge', 'r3Spine', 'r3Claw', 'pennies', 'platen']) {
        const nx = normRow[key + '_x'];
        const ny = normRow[key + '_y'];
        if (nx !== undefined && nx >= 0 && ny >= 0) {
          screenLandmarks[key] = { isScreen: true, x: nx * W, y: ny * H, ndcX: nx, ndcY: ny };
        }
      }
    }
    for (const call of EDITORIAL_CALLS) {
      if (frame >= call.a && frame <= call.b) {
        drawCall(call, frame, null, screenLandmarks);
      }
    }
    drawComparisonLegend(frame, mode);
    return canvas.toDataURL('image/png');
  }

  return { canvas, ctx, compositeFrame, hasActiveOverlay, renderOverlayPNG };
}
