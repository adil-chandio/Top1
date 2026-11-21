// E1 — Desi 3D explainer timeline (Monarch Edit channel · second pilot).
//
// "Metal Ka Chamach Zyada Thanda Kyun Lagta Hai?"
//
// This module is pure (no clocks, no three.js, no DOM). It defines the
// beat sheet, the shared clock, the illustrative warmth-drain curves and
// the paddle pose for a contrast explainer: the same paddle touches the
// metal block and the lakri/wood block at the same room temperature; the
// metal is shown draining warmth away faster — an illustrative direction,
// not a measurement.

export const DURATION = 38;           // P1 band: 34–40 s, vertical 9:16
export const FPS = 24;
export const FRAME = Object.freeze({ width: 720, height: 1280 });
export const ILLUSTRATION_BADGE = 'ILLUSTRATIVE 3D MODEL — NOT A TEST RESULT';

export const BEATS = Object.freeze([
  { id: 'question',  start: 0,  end: 4  },
  { id: 'setup',     start: 4,  end: 10 },
  { id: 'touch-metal', start: 10, end: 18 },
  { id: 'touch-wood',  start: 18, end: 26 },
  { id: 'reveal',    start: 26, end: 32 },
  { id: 'outro',     start: 32, end: 38 },
]);

// Shared clock: both touch phases run one clock from the first touch.
export const CLOCK = Object.freeze({ start: 10, end: 26 });

// Illustrative warmth-drain windows (seconds). Metal drains faster.
export const DRAINS = Object.freeze({
  metal: [12.5, 17.5],
  wood:  [20.5, 26],
});

// Paddle heights (center of the warm paddle).
export const PADDLE = Object.freeze({
  height: 0.55,
  restY: 1.62,        // idle hover height (center)
  touchY: 0.775,      // center when it touches a block top (0.5)
});

export const CAPTIONS = Object.freeze({
  question: 'Metal ka chamach zyada thanda kyun lagta hai?',
  setup: 'Dono blocks room temperature par — same paddle.',
  'touch-metal': 'TOUCH · METAL — garmi paddle se jaldi jaati hai.',
  'touch-wood': 'TOUCH · LAKRI — garmi jaldi nahi jaati.',
  reveal: 'Isparshan: metal garmi haath se jaldi jaldi laata hai',
  outro: 'MONARCHs Edit · Desi 3D explainer · test-first',
});

export const clamp = (v, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
export const clamp01 = (v) => clamp(v, 0, 1);
export const smooth = (v) => { const t = clamp01(v); return t * t * (3 - 2 * t); };
export const progress = (t, a, b) => smooth((clamp(t, a, b) - a) / Math.max(1e-9, b - a));

export function beatAt(t) {
  const time = clamp(t, 0, DURATION);
  return BEATS.find((beat) => time >= beat.start && time < beat.end) ?? BEATS[BEATS.length - 1];
}
export function beatIndexAt(t) {
  return BEATS.indexOf(beatAt(t));
}
export function beatCaptionAt(t) {
  return CAPTIONS[beatAt(t).id];
}
export function beatProgressAt(t) {
  const beat = beatAt(t);
  return progress(clamp(t, 0, DURATION), beat.start, beat.end);
}

export function elapsedAt(t) {
  return clamp(t, CLOCK.start, CLOCK.end) - CLOCK.start;
}
export function clockRunningAt(t) {
  return t >= CLOCK.start && t < CLOCK.end;
}
export function clockLabelAt(t) {
  const elapsed = elapsedAt(t);
  return `T+${elapsed.toFixed(1)}s`;
}

export function metalDrainAt(t) {
  return progress(t, DRAINS.metal[0], DRAINS.metal[1]);
}
export function woodDrainAt(t) {
  // Illustrative direction: same room, wood keeps the warmth closer.
  return progress(t, DRAINS.wood[0], DRAINS.wood[1]) * 0.55;
}

// Warmth-glow remaining on the paddle (1 = warm, 0 = cool). The paddle
// is one continuous proxy for the hand: it starts warm, drains fast on
// the metal block, holds cool mid-flight, and only marginally drains a
// second time on the wood block — wood stays cool for a held hand.
export function paddleWarmthAt(t) {
  if (t < DRAINS.metal[0]) return 1;             // not yet touched
  if (t < DRAINS.metal[1]) return 1 - metalDrainAt(t);   // metal: fast, visible drain
  if (t < DRAINS.wood[0]) return 0;              // mid-flight (held cool)
  return 0.06 * (1 - woodDrainAt(t));             // wood: marginal, slow, near-flat
}

// Paddle pose — { x, y }. Center x=0, touching blocks flip the side.
export function paddlePose(t) {
  const time = clamp(t, 0, DURATION);
  if (time < 9) return { x: 0, y: PADDLE.restY };
  if (time < DRAINS.metal[0]) {                     // 9 → 12.5: descend onto metal
    const a = smooth((time - 9) / (DRAINS.metal[0] - 9));
    return { x: -0.86 * a, y: PADDLE.restY + (PADDLE.touchY - PADDLE.restY) * a };
  }
  if (time < DRAINS.metal[1]) return { x: -0.86, y: PADDLE.touchY };   // touching metal
  if (time < DRAINS.wood[0]) {                       // arc to wood
    const a = smooth((time - DRAINS.metal[1]) / (DRAINS.wood[0] - DRAINS.metal[1]));
    return {
      x: -0.86 + 1.72 * a,
      y: PADDLE.touchY + (PADDLE.restY - PADDLE.touchY) * Math.sin(Math.PI * a),
    };
  }
  if (time < DRAINS.wood[1]) return { x: 0.86, y: PADDLE.touchY };     // touching wood
  if (time < 31) {                                  // return to center, lifted
    const a = smooth((time - DRAINS.wood[1]) / (31 - DRAINS.wood[1]));
    return { x: 0.86 - 0.86 * a, y: PADDLE.touchY + (PADDLE.restY - PADDLE.touchY) * a };
  }
  return { x: 0, y: PADDLE.restY };
}

export function metalTouchAt(t) {
  return t >= DRAINS.metal[0] && t < DRAINS.metal[1];
}
export function woodTouchAt(t) {
  return t >= DRAINS.wood[0] && t < DRAINS.wood[1];
}

export function revealProgress(t) {
  return progress(t, 26, 30);
}
export function questionProgress(t) {
  return progress(t, 0, 1.4);
}
export function outroProgress(t) {
  return progress(t, 32.4, 36);
}
