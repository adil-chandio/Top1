import { AIR_TIMING } from '../../src/air-crush.js';
import { clamp, smooth } from './motion.js';

export const CAN_H = 3.08;
export const CAN_R = .857;
export const BATH_Y = .77;
export const IMMERSE = .145;
export const BAND_DEPTH = .022;
export const PORT_Y = CAN_H / 2 - .036;
const CLEARANCE = .218;
const LOWER_SECONDS = .385;
const FOOT_SHORTENING = .835;
const FOOT_SHEAR = .225;
const FOOT_TILT = .14;

function ease(n) {
  const t = clamp(n);
  return t ** 3 * (t * (t * 6 - 15) + 10);
}

function unEase(y) {
  let a = 0, b = 1;
  for (let i = 0; i < 32; i++) {
    const m = (a + b) / 2;
    if (ease(m) < y) a = m;
    else b = m;
  }
  return (a + b) / 2;
}

const lowerFrom = AIR_TIMING.dip - unEase(CLEARANCE / (CLEARANCE + IMMERSE)) * LOWER_SECONDS;
export const RIG = Object.freeze({ flipFrom: 8.93, flipTo: 10.021, lowerFrom, lowerTo: lowerFrom + LOWER_SECONDS });
export const SNAP_SPEED = Object.freeze({ hook: 1.62, replay: .63 });

// Illustration levels; not measured pressure data.
export function pressureRatio(t) {
  return 1 - .84 * smooth((t - AIR_TIMING.pressureStart) / (AIR_TIMING.pressureEnd - AIR_TIMING.pressureStart));
}

export function buckle(t) {
  if (t <= 0) return { a: 0, b: 0, c: 0, shiver: 0 };
  const a = smooth(t / .138);
  const b = smooth((t - .061) / .23);
  const c = smooth((t - .208) / .43);
  // Damped motion rides on a plastic (non-rebounding) shape change.
  const shiver = t < .10 ? 0 : .012 * Math.sin(57 * (t - .10)) * Math.exp(-9.4 * (t - .10));
  return { a, b, c, shiver };
}

export function eventClock(t, shot) {
  return shot === 0 ? (t - AIR_TIMING.hookSnap) * SNAP_SPEED.hook : (t - AIR_TIMING.snap) * SNAP_SPEED.replay;
}

export function poseAt(t, shot) {
  const hook = shot === 0;
  const hot = shot > 0 && shot < 4;
  const turn = hot ? 0 : shot > 4 || hook ? 1 : ease((t - RIG.flipFrom) / (RIG.flipTo - RIG.flipFrom));
  const hold = BATH_Y + PORT_Y - IMMERSE;
  const descend = ease((t - RIG.lowerFrom) / LOWER_SECONDS);
  const lift = .31 * Math.sin(Math.PI * turn) ** 2;
  // The fixture translates during the flip so the skirt clears the water.
  const centerY = hot ? 1.88 : shot === 4 ? hold + lift + (IMMERSE + CLEARANCE) * (1 - descend) : hold;
  const collapse = buckle(eventClock(t, shot));
  return { hot, turn, centerY, collapse, cutaway: shot === 2 || (shot >= 5 && shot <= 7) };
}

export function canRadius(v) {
  const heel = smooth(v / .078);
  const neck = smooth((v - .88) / .105);
  return CAN_R - .107 * (1 - heel) - .118 * neck;
}

const angleDiff = (x) => Math.atan2(Math.sin(x), Math.cos(x));
const crease = (theta, v, heading, level, length, width, slope) => {
  const a = Math.abs(angleDiff(theta - heading - (v - level) * slope)) / width;
  const h = (v - level) / length;
  const envelope = Math.exp(-h * h * 1.4);
  // An angular crease with shoulders and a narrower ridge, not a rubber dent.
  const fold = Math.max(0, 1 - a);
  return envelope * (.52 * fold + .48 * Math.pow(fold, .44));
};
const amount = ({ a, b, c }) => .29 * a + .50 * b + .21 * c;

export function footPose(state) {
  const s = amount(state);
  return { x: FOOT_SHEAR * s, y: -CAN_H / 2 + FOOT_SHORTENING * s, rotation: FOOT_TILT * s };
}

// Diamond/diagonal buckling is authored, not an FEA prediction. The stable
// lid and the moving base are rigid rings; wall vertices meet both rims.
export function deformCan(theta, v, state, inset = 0, out = { x: 0, y: 0, z: 0 }) {
  const { a, b, c, shiver } = state;
  const s = amount(state);
  const wall = Math.sin(Math.PI * v);
  let r = canRadius(v) - inset;
  if (s > 0) {
    const first = crease(theta, v, -.34, .57, .245, .90, 5.9);
    const second = crease(theta, v, 2.93, .46, .268, .95, -5.2);
    const lower = crease(theta, v, 1.14, .32, .149, .80, -7.8);
    const signedEdge = .072 * Math.sin(theta * 3 + v * 15.6) - .039 * Math.sin(theta * 6 - 10.9 * v);
    r = Math.max(.19, r + wall ** 1.28 * (-a * .59 * first - b * .56 * second - c * .44 * lower + signedEdge * s - .157 * s) + shiver * wall);
  }
  const tilt = FOOT_TILT * s * (1 - smooth(v / .235));
  const rimX = Math.sin(theta) * r;
  out.y = (v - .5) * CAN_H + FOOT_SHORTENING * s * (1 - smooth(v)) + rimX * Math.sin(tilt) + .178 * s * wall ** 2.8 * Math.sin(2 * theta + 12.9 * v);
  out.x = rimX * Math.cos(tilt) + FOOT_SHEAR * s * (1 - v) ** 2;
  out.z = Math.cos(theta) * r - .068 * s * wall;
  return out;
}

export function splashHeight(age, upward, gravity = 10.5) {
  return age < 0 ? 0 : Math.max(0, age * upward - .5 * gravity * age * age);
}

export function vaporRemaining(t) {
  return 1 - .948 * smooth((t - AIR_TIMING.condense) / 3.94);
}

export function waterEvent(t, shot) {
  return shot === 0 || shot >= 9 ? eventClock(t, shot) : t - AIR_TIMING.dip;
}

export function shutterTimes(t, cut) {
  const moving = cut.index === 0 && Math.abs(t - AIR_TIMING.hookSnap - .091) < .175
    || cut.index === 4 && t >= RIG.flipFrom && t <= RIG.lowerTo + .135
    || cut.index === 9 && t >= AIR_TIMING.snap - .05 && t <= AIR_TIMING.snap + .79;
  if (!moving) return [t];
  // Two sub-exposures on fast action, kept within the edited shot. 24 fps
  // with a 180-degree shutter interval; no dissolve across a hard cut.
  const lo = t - cut.age;
  const hi = t + cut.remaining - 1e-6;
  return [clamp(t - 1 / 192, lo, hi), clamp(t + 1 / 192, lo, hi)];
}
