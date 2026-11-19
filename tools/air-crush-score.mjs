import { AIR_TIMING } from '../src/air-crush.js';
import { SNAP_SPEED, RIG } from './demo-render/air-crush-motion.js';
import { clamp, smooth } from './demo-render/motion.js';

// Original lab ambience, struck metal and water Foley, composed at 48 kHz.
// Amounts are chosen to leave space for the narration, especially on phones.
export function airCrushScore(duration) {
  const rate = 48000;
  const frames = Math.round(duration * rate);
  const wav = Buffer.alloc(44 + 4 * frames);
  wav.write('RIFF', 0); wav.writeUInt32LE(wav.length - 8, 4); wav.write('WAVEfmt ', 8);
  wav.writeUInt32LE(16, 16); wav.writeUInt16LE(1, 20); wav.writeUInt16LE(2, 22);
  wav.writeUInt32LE(rate, 24); wav.writeUInt32LE(rate * 4, 28); wav.writeUInt16LE(4, 32); wav.writeUInt16LE(16, 34);
  wav.write('data', 36); wav.writeUInt32LE(frames * 4, 40);
  const tau = Math.PI * 2;
  const sin = (f, t) => Math.sin(tau * f * t);
  const snaps = [[AIR_TIMING.hookSnap, SNAP_SPEED.hook], [AIR_TIMING.snap, SNAP_SPEED.replay]];
  const dips = [[AIR_TIMING.hookSnap + .055, .72], [AIR_TIMING.dip, 1.0], [AIR_TIMING.snap + .10, .81]];
  const lights = [1.625, 4.4167, 6.5, 11.5, 13.5833, 16.6667, 19.1667, 25.0833];
  let seed = 0xa78f531, slow = 0, medium = 0, wet = 0;
  for (let i = 0; i < frames; i++) {
    const t = i / rate;
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    const white = seed / 2147483648 - 1;
    slow += .021 * (white - slow);
    medium += .24 * (white - medium);
    const band = medium - slow;
    wet += .069 * (band - wet);
    const trem = .84 + .16 * sin(.27, t);
    let center = .031 * trem * sin(65.406, t) + .014 * trem * sin(130.812, t) + .024 * slow;
    const breath = .004 * sin(195.998, t) + .008 * Math.sin(tau * 196.28 * t + .24 * Math.sin(t * .61));
    let side = breath * (t > 17 ? .5 : 1);
    if (t > 2 && t < 8.9) center += .020 * band * Math.sin(Math.PI * (t - 2) / 6.9);
    // Increasingly quick low ticks before the second snap; a short gap makes
    // the audible crack read on small phone speakers too.
    if (t > 19.9 && t < 22.57) {
      const phase = (t - 19.9) * (2.1 + .54 * (t - 19.9));
      const pulse = Math.exp(-13 * (phase % 1));
      center += .026 * pulse * sin(176, t);
    }
    if (t > 22.65 && t < AIR_TIMING.snap) { center *= .29; side *= .29; }
    if (t >= RIG.flipFrom && t < RIG.lowerTo) {
      const age = t - RIG.flipFrom;
      const envelope = smooth(age / .24) * smooth((RIG.lowerTo - t) / .22);
      side += envelope * (.015 * sin(179 + 9 * Math.sin(age * 2.6), age) + .010 * band);
    }
    for (const [start, speed] of snaps) {
      const a = t - start;
      if (a >= 0 && a < 1.10) {
        const hit = clamp(a * 450);
        center += hit * .22 * Math.exp(-19 * a) * Math.sin(tau * (73 * a + 25 * (1 - Math.exp(-15 * a)) / 15));
        center += hit * Math.exp(-25 * a) * (.34 * band + .15 * (white - medium) + .113 * sin(481, a) + .10 * sin(1109, a) + .046 * sin(2317, a));
        center += hit * Math.exp(-12.6 * a) * (.034 * sin(337.2, a) + .023 * sin(682.2, a));
        const fold = a - .079 / speed;
        if (fold >= 0) center += clamp(fold * 410) * Math.exp(-18 * fold) * (.21 * band + .11 * sin(299, fold) + .067 * sin(751, fold));
        const room = Math.max(0, a - .040);
        side += clamp(room * 63) * Math.exp(-6.4 * room) * (.018 * sin(336.4, room) + .011 * band);
      }
    }
    for (const [start, energy] of dips) {
      const a = t - start;
      if (a >= 0 && a < 1.32) {
        const imp = energy * clamp(a * 76) * Math.exp(-6.3 * a);
        center += imp * (.151 * medium + .22 * wet + .068 * Math.sin(tau * (119 * a + 17 * (1 - Math.exp(-6 * a)) / 6)));
        side += imp * .067 * (white - slow) * sin(14, a);
        if (a > .18) side += clamp((a - .18) * 100) * Math.exp(-9 * (a - .18)) * band * .066;
      }
    }
    for (const start of lights) {
      const a = t - start;
      if (a >= 0 && a < .42) side += .056 * clamp(a * 45) * Math.exp(-10.5 * a) * (band + .45 * sin(189.5, a));
    }
    const fade = clamp((duration - t) / .42);
    wav.writeInt16LE(Math.round(32750 * Math.tanh((center + side) * 1.07) * fade), 44 + 4 * i);
    wav.writeInt16LE(Math.round(32750 * Math.tanh((center + .67 * side + .011 * slow) * 1.07) * fade), 46 + 4 * i);
  }
  return wav;
}
