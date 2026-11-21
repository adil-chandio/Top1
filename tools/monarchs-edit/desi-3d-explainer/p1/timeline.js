// Desi 3D explainer — timeline contract for the Monarch Edit channel.
//
// This module is pure (no clocks, no three.js, no DOM). It defines the
// beat sheet, the illustrative clock and melt curves, and the caption text
// for the first pilot, "Metal ya Lakri — Baraf Pehle Kahan Pighlegi?".
//
// Everything about melting here is ILLUSTRATIVE. It is an explanatory model
// of the heat-transfer direction, not a measurement of a real test, and not
// a substitute for the physical run that the audit insists on (three paired
// runs, swapped sides, raw footage kept).

export const DURATION = 38;            // P1 band: 34–40 s, vertical 9:16
export const FPS = 24;
export const FRAME = Object.freeze({ width: 720, height: 1280 });
export const ILLUSTRATION_BADGE = 'ILLUSTRATIVE 3D MODEL — NOT A TEST RESULT';

export const BEATS = Object.freeze([
  { id: 'question',  start: 0,  end: 5  },
  { id: 'setup',     start: 5,  end: 10 },
  { id: 'timelapse', start: 10, end: 22 },
  { id: 'reveal',    start: 22, end: 32 },
  { id: 'outro',     start: 32, end: 38 },
]);

// The shared clock: both blocks start counting at the same moment and the
// same seconds stay on screen.
export const CLOCK = Object.freeze({ start: 10, end: 22 });

// Illustrative melt windows (seconds). The metal cube is shown melting
// faster than the wood cube — the direction the physics predicts — but the
// curves are authored, not measured. See ILLUSTRATION_BADGE.
export const MELT = Object.freeze({
  metal: [10.6, 21.2],
  wood:  [11.0, 21.6],
});

export const CAPTIONS = Object.freeze({
  question: 'Baraf pehle kahan pighlegi — metal ya lakri?',
  setup: 'Dono blocks room temperature par — same clock, same contact.',
  timelapse: 'TIME-LAPSE · same room · same clock',
  reveal: 'Metal se garmi ice tak jaldi pahunchti hai',
  outro: 'MONARCHs Edit · Desi 3D explainer · test-first',
});

export const clamp = (v, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
export const clamp01 = (v) => clamp(v, 0, 1);
export const smooth = (v) => { const t = clamp01(v); return t * t * (3 - 2 * t); };
export const progress = (t, a, b) => smooth((clamp(t, a, b) - a) / Math.max(1e-9, b - a));
export const between = (t, a, b) => progress(t, a, b);

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
export function metalMeltAt(t) {
  return progress(t, MELT.metal[0], MELT.metal[1]);
}
export function woodMeltAt(t) {
  // Illustrative direction: same room, wood conducts less strongly, so the
  // wood cube is shown melting less far by the end of the window.
  return progress(t, MELT.wood[0], MELT.wood[1]) * 0.55;
}
export function clockLabelAt(t) {
  const elapsed = elapsedAt(t);
  return `T+${elapsed.toFixed(1)}s`;
}

// 2D overlay fades the reveal content in across 22–29 s.
export function revealProgress(t) {
  return progress(t, 22, 29);
}
// The question beat fades the prompt in from 0 s.
export function questionProgress(t) {
  return progress(t, 0, 1.4);
}
// The outro identity card fades in late.
export function outroProgress(t) {
  return progress(t, 32.4, 36);
}
