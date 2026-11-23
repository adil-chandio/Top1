import * as THREE from 'three';
import { GLM, assertSafeLatinGlyphs } from '../../monarch-v6-imax-sdk/index.js';
import { ANCHORS, isProtectedFrame } from './director_long_v6.js';

const A = ANCHORS;

export const CALLOUTS_LONG_V6 = [
  // CHAPTER 1 [0..921]
  {
    id: 'c1_standing', start: 148, end: 210,
    eyebrow: 'CHAPTER 01 · PERIPLANETA AMERICANA',
    title: 'Half an Inch Tall',
    sub: '12.5 mm standing height · 31.1 mm body length',
    anchorKey: 'pronotum', boxX: 96, boxY: 104, boxW: 486, accent: '#ffd187',
  },
  {
    id: 'c1_pennies', start: 218, end: 325,
    eyebrow: 'SCALE REFERENCE · 3.04 MM',
    title: 'Two Stacked Pennies',
    sub: 'Closed oak doorway clearance: 3.20 mm',
    anchorKey: 'pennies', boxX: 96, boxY: 104, boxW: 486, accent: '#ffd187',
  },
  // [330..538] PROTECTED CLIMAX #1 -> 100% ZERO TEXT/HUD!
  {
    id: 'c1_paradox', start: 545, end: 766,
    eyebrow: 'THE MECHANICAL PARADOX',
    title: 'Stiff Armor, Folded in Half',
    sub: '47% vertical compression inside a 3.2 mm crevice',
    anchorKey: 'pronotum', boxX: 96, boxY: 104, boxW: 516, accent: '#ffd187',
  },
  {
    id: 'c1_hook', start: 780, end: 912,
    eyebrow: 'NO ROOM TO STAND',
    title: 'Running Without Its Feet',
    sub: 'Jayaram & Full · PNAS 2016 · UC Berkeley',
    anchorKey: 'r3Claw', boxX: 96, boxY: 104, boxW: 506, accent: '#88f4ee',
  },

  // CHAPTER 2 [921..2288]
  {
    id: 'c2_500fps', start: 1005, end: 1216,
    eyebrow: 'CHAPTER 02 · UC BERKELEY HIGH-SPEED RIG',
    title: '500 Frames / Second',
    sub: 'Five distinct biomechanical moves (288 - 821 ms)',
    anchorKey: 'head', boxX: 96, boxY: 104, boxW: 516, accent: '#88f4ee',
  },
  {
    id: 'c2_m1', start: 1232, end: 1356,
    eyebrow: '500 FPS SLOT SEQUENCE · 01 / 05',
    title: '1. Antennae Sweep Slot',
    sub: 'Sensory probe locates 3.2 mm crevice entry',
    anchorKey: 'head', boxX: 96, boxY: 104, boxW: 486, accent: '#ffd187',
  },
  {
    id: 'c2_m2', start: 1366, end: 1453,
    eyebrow: '500 FPS SLOT SEQUENCE · 02 / 05',
    title: '2. Head Tips & Wedges In',
    sub: 'Anterior capsule angles into tight opening',
    anchorKey: 'head', boxX: 96, boxY: 104, boxW: 496, accent: '#ffd187',
  },
  {
    id: 'c2_m3', start: 1463, end: 1577,
    eyebrow: '500 FPS SLOT SEQUENCE · 03 / 05',
    title: '3. Pronotum Rolls Inside',
    sub: 'Dorsal shield tilts ~11° to clear upper edge',
    anchorKey: 'pronotum', boxX: 96, boxY: 104, boxW: 496, accent: '#ffd187',
  },
  {
    id: 'c2_m4', start: 1587, end: 1720,
    eyebrow: '500 FPS SLOT SEQUENCE · 04 / 05',
    title: '4. Planted Hind Legs Shove',
    sub: 'External legs drive thickest thorax through',
    anchorKey: 'r3Spine', boxX: 96, boxY: 104, boxW: 506, accent: '#ffd187',
  },
  {
    id: 'c2_m5', start: 1730, end: 1813,
    eyebrow: '500 FPS SLOT SEQUENCE · 05 / 05',
    title: '5. Flattened Abdomen Clears',
    sub: 'Shell rebounds immediately on exit',
    anchorKey: 'abdomen', boxX: 96, boxY: 104, boxW: 506, accent: '#6ef29c',
  },
  {
    id: 'c2_xray_tiles', start: 1828, end: 2012,
    eyebrow: '3D X-RAY · DORSAL TERGITES',
    title: 'Rigid Roof-Tile Plates',
    sub: 'Constant plate chord length · zero rubbery bending',
    anchorKey: 'plate', boxX: 96, boxY: 104, boxW: 516, accent: '#ffd187',
  },
  {
    id: 'c2_xray_hinges', start: 2022, end: 2275,
    eyebrow: '3D X-RAY · ARTHRODIAL MEMBRANE',
    title: 'Soft Hinges Fold in Half',
    sub: 'Accordion folds absorb 41 - 57% compression',
    anchorKey: 'hinge', boxX: 96, boxY: 104, boxW: 516, accent: '#88f4ee',
  },

  // CHAPTER 3 [2288..3607]
  {
    id: 'c3_corridor', start: 2302, end: 2675,
    eyebrow: 'CHAPTER 03 · CONFINED CORRIDOR',
    title: 'Stepping Down the Roof',
    sub: '104 trials across controlled acrylic tunnel heights',
    anchorKey: 'pronotum', boxX: 96, boxY: 104, boxW: 516, accent: '#88f4ee',
  },
  {
    id: 'c3_fullspeed', start: 2810, end: 3085,
    eyebrow: '12 MM TO 9 MM TO 6 MM ROOF',
    title: 'Nearly Full Sprint: 58.1 cm/s',
    sub: 'Half standing height · 61.1 ms tripod beat holds',
    anchorKey: 'pronotum', boxX: 96, boxY: 104, boxW: 536, accent: '#6ef29c',
  },
  {
    id: 'c3_splay', start: 3098, end: 3278,
    eyebrow: 'DORSAL KINEMATICS',
    title: 'Legs Splay 55° to 75°',
    sub: 'Foot track stays ~11.9 mm from body midline',
    anchorKey: 'pronotum', boxX: 96, boxY: 104, boxW: 496, accent: '#88f4ee',
  },
  {
    id: 'c3_crash', start: 3294, end: 3595,
    eyebrow: 'BODY-COMPRESSION THRESHOLD · 4 MM',
    title: 'Speed Crashes 4x (14.5 cm/s)',
    sub: '2 mm lower squeezes shell · tripod gait collapses',
    anchorKey: 'pronotum', boxX: 96, boxY: 96, boxW: 526, accent: '#ffa84c',
  },

  // CHAPTER 4 [3607..5312]
  {
    id: 'c4_claws', start: 3768, end: 4128,
    eyebrow: 'CHAPTER 04 · OPEN STANCE (12 MM)',
    title: 'Hooked Claws & Soft Pads',
    sub: 'Distal ungues & arolium grip floor on every step',
    anchorKey: 'r3Claw', boxX: 96, boxY: 104, boxW: 506, accent: '#ffd187',
  },
  {
    id: 'c4_liftoff', start: 4144, end: 4342,
    eyebrow: 'SPLAYED PAST 80° · 4 MM ROOF',
    title: 'Foot Claws Tip Sideways',
    sub: 'Lifted +0.47 mm clear of normal floor engagement',
    anchorKey: 'r3Claw', boxX: 96, boxY: 104, boxW: 516, accent: '#88f4ee',
  },
  {
    id: 'c4_pushup', start: 4356, end: 4474,
    eyebrow: 'BIOMECHANICAL ANALOGY · >80° SPRAWL',
    title: 'Wide-Arm Splayed Push-Up',
    sub: 'Palms roll sideways · vertical leverage collapses',
    anchorKey: 'athleteHand', boxX: 96, boxY: 104, boxW: 526, accent: '#ffa84c',
  },
  {
    id: 'c4_shin_reveal', start: 4488, end: 4654,
    eyebrow: 'CONTACT HANDOFF · TIBIA',
    title: 'Shins Take Over From Feet',
    sub: 'Built-in passive crampon spines engage floor',
    anchorKey: 'r3Spine', boxX: 96, boxY: 104, boxW: 506, accent: '#ffd187',
  },
  // [4662..4923] PROTECTED CLIMAX #2 -> 100% ZERO TEXT/HUD!
  {
    id: 'c4_oars', start: 4930, end: 5088,
    eyebrow: 'SYNCHRONOUS OAR STROKE',
    title: 'Middle Legs Row Together',
    sub: 'Bilateral oar propulsion under 4 mm confinement',
    anchorKey: 'r3Spine', boxX: 96, boxY: 104, boxW: 516, accent: '#ffd187',
  },
  {
    id: 'c4_5x', start: 5102, end: 5298,
    eyebrow: 'PROPULSIVE THRUST · ~38 mN PER LEG',
    title: 'Five Times Body Weight',
    sub: 'Spiny shin push overcomes roof & ventral drag',
    anchorKey: 'r3Spine', boxX: 96, boxY: 104, boxW: 516, accent: '#ffd187',
  },

  // CHAPTER 5 [5312..6591]
  {
    id: 'c5_shear', start: 5385, end: 5795,
    eyebrow: 'CHAPTER 05 · FOOTLESS TRACTION TEST',
    title: 'Tibial Spines Lock In Alone',
    sub: 'Directional friction holds without feet (1.73 - 2.04)',
    anchorKey: 'r3Spine', boxX: 96, boxY: 104, boxW: 536, accent: '#6ef29c',
  },
  {
    id: 'c5_ceiling', start: 5870, end: 6214,
    eyebrow: '638 CONFINED RUNS · CEILING DRAG',
    title: 'Rougher Roofs Always Slow It',
    sub: '6.64 to 5.63 to 0.36 cm/s as overhead rub rises',
    anchorKey: 'pronotum', boxX: 96, boxY: 104, boxW: 526, accent: '#88f4ee',
  },
  {
    id: 'c5_floor', start: 6230, end: 6578,
    eyebrow: 'FLOOR GRIT TRADE-OFF · 4 MM',
    title: 'Medium 40-Grit Wins (5.26 cm/s)',
    sub: '100-grit slips (1.57) · 20-grit snags belly (3.69)',
    boxX: 96, boxY: 96, boxW: 542, accent: '#ffa84c',
  },

  // CHAPTER 6 [6591..8032]
  {
    id: 'c6_900x', start: 6602, end: 6868,
    eyebrow: 'CHAPTER 06 · DISTRIBUTED COMPRESSION',
    title: 'Up to ~900x Body Weight',
    sub: '6.08 N spread across ~3 cm² of hinged plates',
    anchorKey: 'platen', boxX: 96, boxY: 104, boxW: 526, accent: '#ffd187',
  },
  {
    id: 'c6_sprint', start: 6884, end: 7172,
    eyebrow: 'POST-LOAD RECOVERY',
    title: '76.7 cm/s Unimpaired Sprint',
    sub: 'Zero loss in open-floor velocity after compression',
    anchorKey: 'pronotum', boxX: 96, boxY: 104, boxW: 516, accent: '#6ef29c',
  },
  {
    id: 'c6_315', start: 7265, end: 7605,
    eyebrow: '315 GATE ATTEMPTS · THE LIMIT',
    title: '72% Pass Drops to 17% at 3.2 mm',
    sub: 'Over 4 out of 5 attempts fail at two-penny height',
    anchorKey: 'pronotum', boxX: 96, boxY: 104, boxW: 542, accent: '#ffd187',
  },
  {
    id: 'c6_limit', start: 7620, end: 8018,
    eyebrow: '3.2 MM CREVICE OUTCOMES',
    title: '74% Turn Back · 9% Chest-Wedged',
    sub: 'Antennal check rejects tight slots · thorax sets limit',
    anchorKey: 'pronotum', boxX: 96, boxY: 96, boxW: 546, accent: '#ff7a66',
  },

  // CHAPTER 7 [8032..9008]
  {
    id: 'c7_reprise', start: 8042, end: 8136,
    eyebrow: 'CHAPTER 07 · REAL-SPEED REPRISE',
    title: '1x Natural Speed',
    sub: 'Sub-second doorway vanish with full mechanics known',
    anchorKey: 'pronotum', boxX: 96, boxY: 104, boxW: 516, accent: '#ffd187',
  },
  // [8143..8502] PROTECTED CLIMAX #3 -> 100% ZERO TEXT/HUD!
  {
    id: 'c7_thesis', start: 8512, end: 8684,
    eyebrow: 'BIOMECHANICAL RESOLUTION',
    title: 'Solid Armor Jams · Feet Fail',
    sub: 'Folding hinges + tibial crampon spines solve both',
    anchorKey: 'pronotum', boxX: 96, boxY: 104, boxW: 526, accent: '#ffd187',
  },
  {
    id: 'c7_cram', start: 8700, end: 8914,
    eyebrow: 'BIO-INSPIRED CRAM ROBOT · UC BERKELEY',
    title: 'Shells That Fold · Shins That Walk',
    sub: 'Origami shell (75 to 35 mm) crawls at ~50% open speed',
    anchorKey: 'cram', boxX: 96, boxY: 104, boxW: 548, accent: '#6ef29c',
  },
];

export const GAUGES_LONG_V6 = [
  {
    id: 'g3_speed', start: 3310, end: 3596,
    title: 'CONFINED CORRIDOR SPEED (MEAN)',
    bars: [
      { label: '12 mm Open',   val: '58.1 cm/s', frac: 1.00, color: '#6ef29c' },
      { label: '6 mm Roof',    val: '57.9 cm/s', frac: 0.99, color: '#88f4ee' },
      { label: '4 mm Squeeze', val: '14.5 cm/s', frac: 0.25, color: '#ffa84c' },
    ],
  },
  {
    id: 'g5_grit', start: 6250, end: 6580,
    title: '4 MM FLOOR GRIT SPEED (MEAN)',
    bars: [
      { label: '100-Grit Slick',  val: '1.57 cm/s', frac: 0.30, color: '#88f4ee' },
      { label: '40-Grit Medium',  val: '5.26 cm/s', frac: 1.00, color: '#6ef29c' },
      { label: '20-Grit Coarse',  val: '3.69 cm/s', frac: 0.70, color: '#ffa84c' },
    ],
  },
  {
    id: 'g6_gate', start: 7630, end: 8020,
    title: '3.2 MM GATE (315 ATTEMPTS)',
    bars: [
      { label: 'Turn Back',       val: '74%', frac: 0.74, color: '#ffd187' },
      { label: 'Squeeze Through', val: '17%', frac: 0.17, color: '#6ef29c' },
      { label: 'Thorax Wedged',   val: '9%',  frac: 0.09, color: '#ff7a66' },
    ],
  },
];

// Startup Latin-1 Tofu Guard across 100% of callouts, gauges, and PNAS citation strings!
assertSafeLatinGlyphs(
  [
    ...CALLOUTS_LONG_V6.flatMap((c) => [c.eyebrow, c.title, c.sub]),
    ...GAUGES_LONG_V6.flatMap((g) => [g.title, ...g.bars.flatMap((b) => [b.label, b.val])]),
    'PRIMARY SOURCE · BIOMECHANICS & ROBOTICS',
    'Cockroaches traverse crevices, squeeze rapidly through confined spaces, and inspire soft, legged robots',
    'Kaushik Jayaram & Robert J. Full · University of California, Berkeley',
    'Proceedings of the National Academy of Sciences (PNAS), 2016 · 113(8): E950-E957 · PMC4776529',
  ],
  'LongV6Titles'
);

const projTmp = new THREE.Vector3();
function projectWorldToScreen(worldVec, camera, W, H) {
  if (!worldVec) return null;
  projTmp.copy(worldVec).project(camera);
  if (projTmp.z < -1 || projTmp.z > 1) return null;
  return {
    x: (projTmp.x * 0.5 + 0.5) * W,
    y: (-projTmp.y * 0.5 + 0.5) * H,
  };
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

export function getActiveLeaderProjectionV6(state, camera, W = 1920, H = 1080) {
  const f = state.frame;
  if (isProtectedFrame(f) || f >= A.ch7_pnas_start) return null;

  for (const c of CALLOUTS_LONG_V6) {
    if (f >= c.start && f <= c.end) {
      let target3D = null;
      if (c.worldTarget) {
        target3D = new THREE.Vector3(...c.worldTarget);
      } else if (c.anchorKey && state.anchors && state.anchors[c.anchorKey]) {
        target3D = state.anchors[c.anchorKey];
      }
      if (!target3D) return null;
      const pt = projectWorldToScreen(target3D, camera, W, H);
      if (!pt) return null;

      const fadeIn  = GLM.smoothstep(c.start, c.start + 12, f);
      const fadeOut = 1.0 - GLM.smoothstep(c.end - 12, c.end, f);
      return {
        id: c.id,
        alpha: fadeIn * fadeOut,
        accent: c.accent || '#ffd187',
        boxX: c.boxX,
        boxY: c.boxY,
        boxW: c.boxW,
        boxH: 132,
        tx: Math.round(pt.x * 10) / 10,
        ty: Math.round(pt.y * 10) / 10,
      };
    }
  }
  return null;
}

export function renderEditorialOverlayLongV6(ctx, W, H, state, camera, opts = {}) {
  ctx.clearRect(0, 0, W, H);
  const f = state.frame;

  // 1. ABSOLUTE ZERO OVERLAYS INSIDE ALL 4 PROTECTED CLIMAX WINDOWS!
  if (isProtectedFrame(f)) return;

  // 2. LUXURY FROSTED-OBSIDIAN PRIMARY SOURCE END CARD [8956..9008]
  if (f >= A.ch7_pnas_start) {
    const fade = GLM.smoothstep(A.ch7_pnas_start, A.ch7_pnas_start + 14, f);
    ctx.save();
    ctx.globalAlpha = fade;

    ctx.fillStyle = 'rgba(5, 10, 15, 0.54)';
    ctx.fillRect(0, 0, W, H);

    const cardW = 1360, cardH = 380;
    const cx = (W - cardW) * 0.5, cy = (H - cardH) * 0.5;
    ctx.shadowColor = 'rgba(0, 0, 0, 0.65)';
    ctx.shadowBlur = 36;
    ctx.shadowOffsetY = 14;
    roundRect(ctx, cx, cy, cardW, cardH, 22);
    ctx.fillStyle = 'rgba(8, 15, 22, 0.86)';
    ctx.fill();

    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;
    ctx.strokeStyle = 'rgba(255, 209, 135, 0.38)';
    ctx.lineWidth = 1.6;
    ctx.stroke();

    ctx.fillStyle = '#ffd187';
    roundRect(ctx, W * 0.5 - 54, cy + 48, 108, 4, 2);
    ctx.fill();

    ctx.textAlign = 'center';
    ctx.font = '600 18px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#88f4ee';
    ctx.fillText('PRIMARY SOURCE · BIOMECHANICS & ROBOTICS', W * 0.5, cy + 92);

    ctx.font = '700 35px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#f5f8fa';
    ctx.fillText('Cockroaches traverse crevices, squeeze rapidly through', W * 0.5, cy + 158);
    ctx.fillText('confined spaces, and inspire soft, legged robots', W * 0.5, cy + 204);

    ctx.font = '500 24px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#ffd187';
    ctx.fillText('Kaushik Jayaram & Robert J. Full · University of California, Berkeley', W * 0.5, cy + 266);

    ctx.font = '500 18px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(218, 232, 240, 0.84)';
    ctx.fillText('Proceedings of the National Academy of Sciences (PNAS), 2016 · 113(8): E950-E957 · PMC4776529', W * 0.5, cy + 318);
    ctx.restore();
    return;
  }

  // 3. TOP-RIGHT LIVE OPTICAL TELEMETRY PILL
  if (!opts.skipDynamicLeaders && state.hudTag) {
    ctx.save();
    ctx.font = '600 16px "IBM Plex Mono", monospace';
    const w1 = ctx.measureText(state.hudTag).width;
    const w2 = state.hudMetric ? ctx.measureText(state.hudMetric).width + 28 : 0;
    const pillW = 48 + w1 + w2;
    const pillH = 40;
    const pillX = W - 84 - pillW;
    const pillY = 48;

    roundRect(ctx, pillX, pillY, pillW, pillH, 20);
    ctx.fillStyle = 'rgba(7, 13, 19, 0.72)';
    ctx.fill();
    ctx.strokeStyle = state.hudAlert ? 'rgba(255, 122, 102, 0.45)' : 'rgba(255, 255, 255, 0.16)';
    ctx.lineWidth = 1.2;
    ctx.stroke();

    const pulse = 0.65 + 0.35 * Math.sin(state.time * Math.PI * 4.0);
    ctx.beginPath();
    ctx.arc(pillX + 21, pillY + pillH * 0.5, 4.8, 0, Math.PI * 2);
    ctx.fillStyle = state.hudAlert ? `rgba(255, 112, 82, ${pulse})` : `rgba(110, 246, 208, ${pulse})`;
    ctx.fill();

    ctx.textBaseline = 'middle';
    ctx.fillStyle = 'rgba(236, 244, 248, 0.90)';
    ctx.fillText(state.hudTag, pillX + 36, pillY + pillH * 0.5 + 1);
    if (state.hudMetric) {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.28)';
      ctx.fillText('·', pillX + 44 + w1, pillY + pillH * 0.5 + 1);
      ctx.fillStyle = state.hudAlert ? '#ffa84c' : '#ffd187';
      ctx.fillText(state.hudMetric, pillX + 58 + w1, pillY + pillH * 0.5 + 1);
    }
    ctx.restore();
  }

  // 4. EDITORIAL CALLOUT CARDS + 3D-TRACKED LEADER LINES
  for (const c of CALLOUTS_LONG_V6) {
    if (f >= c.start && f <= c.end) {
      const fadeIn  = GLM.smoothstep(c.start, c.start + 12, f);
      const fadeOut = 1.0 - GLM.smoothstep(c.end - 12, c.end, f);
      const alpha = opts.forceFullAlpha ? 1.0 : fadeIn * fadeOut;
      const slideDx = opts.forceFullAlpha ? 0.0 : (1.0 - GLM.easeOutQuint(GLM.clamp((f - c.start) / 14, 0, 1))) * -16.0;

      ctx.save();
      ctx.globalAlpha = alpha;
      const bx = c.boxX + slideDx, by = c.boxY, bw = c.boxW, bh = 132;

      if (!opts.skipDynamicLeaders) {
        let target3D = null;
        if (c.worldTarget) target3D = new THREE.Vector3(...c.worldTarget);
        else if (c.anchorKey && state.anchors && state.anchors[c.anchorKey]) target3D = state.anchors[c.anchorKey];
        const pt = projectWorldToScreen(target3D, camera, W, H);
        if (pt && pt.x > 60 && pt.x < W - 60 && pt.y > 60 && pt.y < H - 60) {
          const sx = bx + bw * 0.60;
          const sy = by + bh;
          const elbowY = Math.min(pt.y - 18, sy + 42);

          ctx.strokeStyle = c.accent || '#ffd187';
          ctx.lineWidth = 2.1;
          ctx.beginPath();
          ctx.moveTo(sx, sy);
          ctx.lineTo(sx, elbowY);
          ctx.lineTo(pt.x, pt.y);
          ctx.stroke();

          ctx.fillStyle = c.accent || '#ffd187';
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 4.6, 0, Math.PI * 2);
          ctx.fill();
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.86)';
          ctx.lineWidth = 1.4;
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 9.6, 0, Math.PI * 2);
          ctx.stroke();
        }
      }

      ctx.shadowColor = 'rgba(0, 0, 0, 0.52)';
      ctx.shadowBlur = 22;
      ctx.shadowOffsetY = 8;
      roundRect(ctx, bx, by, bw, bh, 14);
      ctx.fillStyle = 'rgba(7, 13, 19, 0.84)';
      ctx.fill();

      ctx.shadowBlur = 0;
      ctx.shadowOffsetY = 0;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.14)';
      ctx.lineWidth = 1.3;
      ctx.stroke();

      roundRect(ctx, bx + 12, by + 18, 4.5, bh - 36, 2.2);
      ctx.fillStyle = c.accent || '#ffd187';
      ctx.fill();

      ctx.textAlign = 'left';
      ctx.font = '600 14.5px "IBM Plex Mono", monospace';
      ctx.fillStyle = c.accent || '#ffd187';
      ctx.fillText(c.eyebrow, bx + 28, by + 35);

      ctx.font = '700 29.5px "Space Grotesk", sans-serif';
      ctx.fillStyle = '#f6f9fb';
      ctx.fillText(c.title, bx + 28, by + 75);

      ctx.font = '500 18px "Space Grotesk", sans-serif';
      ctx.fillStyle = 'rgba(218, 232, 240, 0.88)';
      ctx.fillText(c.sub, bx + 28, by + 108);
      ctx.restore();
    }
  }

  // 5. LIVE ANIMATED COMPARISON GAUGES
  for (const g of GAUGES_LONG_V6) {
    if (f >= g.start && f <= g.end) {
      const fadeIn  = GLM.smoothstep(g.start, g.start + 14, f);
      const fadeOut = 1.0 - GLM.smoothstep(g.end - 14, g.end, f);
      const alpha = opts.forceFullAlpha ? 1.0 : fadeIn * fadeOut;
      const barGrow = opts.forceFullAlpha ? 1.0 : GLM.easeOutQuint(GLM.clamp((f - g.start) / 28, 0, 1));

      ctx.save();
      ctx.globalAlpha = alpha;
      const gw = 536, gh = 192;
      const gx = W - gw - 84, gy = H - gh - 72;

      ctx.shadowColor = 'rgba(0, 0, 0, 0.55)';
      ctx.shadowBlur = 24;
      ctx.shadowOffsetY = 8;
      roundRect(ctx, gx, gy, gw, gh, 14);
      ctx.fillStyle = 'rgba(7, 13, 19, 0.86)';
      ctx.fill();

      ctx.shadowBlur = 0;
      ctx.shadowOffsetY = 0;
      ctx.strokeStyle = 'rgba(136, 244, 238, 0.30)';
      ctx.lineWidth = 1.4;
      ctx.stroke();

      ctx.textAlign = 'left';
      ctx.font = '600 15px "IBM Plex Mono", monospace';
      ctx.fillStyle = '#88f4ee';
      ctx.fillText(g.title, gx + 24, gy + 34);

      g.bars.forEach((b, i) => {
        const ry = gy + 64 + i * 40;
        ctx.font = '500 17px "Space Grotesk", sans-serif';
        ctx.fillStyle = '#e8f1f5';
        ctx.fillText(b.label, gx + 24, ry + 13);

        const barX = gx + 190, barW = 196, barH = 14;
        roundRect(ctx, barX, ry + 1, barW, barH, 7);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.10)';
        ctx.fill();

        roundRect(ctx, barX, ry + 1, Math.max(8, barW * b.frac * barGrow), barH, 7);
        ctx.fillStyle = b.color;
        ctx.fill();

        ctx.font = '600 15px "IBM Plex Mono", monospace';
        ctx.fillStyle = b.color;
        ctx.fillText(b.val, barX + barW + 14, ry + 13);
      });
      ctx.restore();
    }
  }
}
