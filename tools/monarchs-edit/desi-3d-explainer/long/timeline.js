// Desi 3D explainer — long-form companion (first long video).
//
// Pure module: no clocks, no three.js, no DOM. Defines the beat sheet,
// the illustrative clock and melt curves for the long-form version of
// the first Desi 3D explainer pilot ("Baraf pehle kahan pighlegi — metal
// ya lakri?"). Same premise, expanded arc: promise → early proof →
// mechanism → evidence → honesty → reveal → outro.
//
// Everything about melting here is ILLUSTRATIVE. It is an explanatory model
// of the heat-transfer direction, not a measurement of a real test, and not
// a substitute for the physical run that the audit insists on (three paired
// runs, swapped sides, raw footage kept). 16:9 · 1280×720 · 92 s · 24 fps.

export const DURATION = 92;
export const FPS = 24;
export const FRAME = Object.freeze({ width: 1280, height: 720 });
export const ILLUSTRATION_BADGE = 'ILLUSTRATIVE 3D MODEL — NOT A TEST RESULT';

// Beat sheet — the long-form arc (opening promise → early proof →
// time-lapse mechanism → honest evidence context → what this is not →
// payoff → identity).
export const BEATS = Object.freeze([
  { id: 'opening',  start: 0,  end: 9  },
  { id: 'proof',    start: 9,  end: 24 },
  { id: 'timelapse', start: 24, end: 56 },
  { id: 'evidence', start: 56, end: 68 },
  { id: 'honesty',   start: 68, end: 76 },
  { id: 'reveal',    start: 76, end: 86 },
  { id: 'outro',     start: 86, end: 92 },
]);

// The shared clock: starts when the proof beat begins and runs through
// the time-lapse beat. Honest same-conditions frame — same room, same
// clock, both starting together.
export const CLOCK = Object.freeze({ start: 9, end: 56 });

// Illustrative melt windows (seconds). The metal cube is shown melting
// further than the wood cube — the direction the physics predicts — but
// the curves are authored, not measured. See ILLUSTRATION_BADGE.
export const MELT = Object.freeze({
  metal: [10.6, 51.6],
  wood:  [11.6, 52.6],
});

export const CAPTIONS = Object.freeze({
  opening:  'Baraf pehle kahan pighlegi — metal ya lakri?',
  proof:    'Dono blocks room temperature par — same room, same clock.',
  timelapse: 'TIME-LAPSE · same room · same clock',
  evidence: 'Ek real test ke liye bhi: three paired runs, swapped sides, raw footage.',
  honesty:  'Yeh ek illustrative model hai — yeh koi tested result nahi hai.',
  reveal:   'Metal se garmi ice tak jaldi pahunchaati hai',
  outro:    'MONARCHs Edit · Desi 3D explainer · long-form',
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
export function metalMeltAt(t) {
  return progress(t, MELT.metal[0], MELT.metal[1]);
}
export function woodMeltAt(t) {
  // Illustrative direction: same room, wood conducts less strongly, so the
  // wood cube is shown melting less far by the end of the window. Not a
  // measurement — see ILLUSTRATION_BADGE.
  return progress(t, MELT.wood[0], MELT.wood[1]) * 0.55;
}
export function clockLabelAt(t) {
  const elapsed = elapsedAt(t);
  return `T+${elapsed.toFixed(1)}s`;
}

// The opening beat fades the hook question in; the reveal fades in late in
// the payoff beat; the outro card fades in late in the identity beat.
export function questionProgress(t) {
  return progress(t, 0, 1.6);
}
export function revealProgress(t) {
  return progress(t, 76, 84);
}
export function outroProgress(t) {
  return progress(t, 86, 90.5);
}
