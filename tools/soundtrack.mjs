import { FILE_TILES, fileDropCue } from './demo-render/motion.js';

// Score, mechanical details, and transitions are synthesized from scratch.
// The space short uses non-diegetic sound rather than sound traveling in vacuum.
const score = {
  'phone-storage': { notes: [55, 82.41, 130.81, 164.81], cues: [[.39, 'air'], [3.3, 'hit'], ...Array.from({ length: FILE_TILES }, (_, index) => [fileDropCue(index).impactAt, 'tick']), [7.1, 'hit'], [8.19, 'glass']] },
  'halo-desk-lamp': { notes: [49, 73.42, 110, 146.83], cues: [[.29, 'air'], [2.64, 'tick'], [2.81, 'hit'], [3.08, 'glass'], [6.8, 'air'], [7.14, 'glass']] },
  'last-signal': { notes: [41.20, 61.74, 103.83, 164.81], cues: [[.30, 'air'], [4, 'hit'], [4.37, 'signal'], [4.83, 'signal'], [5.29, 'signal'], [5.75, 'signal'], [8.03, 'hit'], [8.24, 'glass'], [9.3, 'signal']] },
};

export function soundtrack(film) {
  const rate = 48000;
  const frames = film.duration * rate;
  const wav = Buffer.alloc(44 + frames * 4);
  wav.write('RIFF', 0); wav.writeUInt32LE(wav.length - 8, 4); wav.write('WAVEfmt ', 8);
  wav.writeUInt32LE(16, 16); wav.writeUInt16LE(1, 20); wav.writeUInt16LE(2, 22);
  wav.writeUInt32LE(rate, 24); wav.writeUInt32LE(rate * 4, 28); wav.writeUInt16LE(4, 32); wav.writeUInt16LE(16, 34);
  wav.write('data', 36); wav.writeUInt32LE(frames * 4, 40);
  const { notes: [sub, alto, bloom, upper], cues } = score[film.id];
  const PI2 = Math.PI * 2;
  const sin = (frequency, t, phase = 0) => Math.sin(PI2 * t * frequency + phase);
  const final = film.shots.at(-1).at;
  let seed = 731 + film.duration;
  let filtered = 0;
  for (let i = 0; i < frames; i++) {
    const t = i / rate;
    const fade = Math.min(1, t / .42, (film.duration - t) / .70);
    const change = Math.min(1, Math.max(0, (t - final + .55) / 1.85));
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    const noise = seed / 2147483648 - 1;
    filtered += .082 * (noise - filtered);
    let low = sin(sub, t, .09 * sin(.3, t)) * .041 + sin(alto, t) * .029;
    let swells = .76 + .24 * sin(.22, t);
    const voicing = .023 * sin(bloom, t, .17 * sin(.2, t)) * swells + change * .025 * sin(upper, t) * swells;
    let center = 0, spread = 0;
    for (const [at, type] of cues) {
      const a = t - at;
      if (a < 0 || a > 1.85) continue;
      if (type === 'hit') {
        const phase = PI2 * (37 * a + 19 * (1 - Math.exp(-16 * a)) / 16);
        center += Math.sin(phase) * .22 * Math.min(1, a * 200) * Math.exp(-a * 6.2);
        center += filtered * .12 * Math.min(1, a * 110) * Math.exp(-a * 15);
      } else if (type === 'tick') {
        center += (filtered * .16 + sin(443, a) * .072 + sin(872, a) * .024) * Math.min(1, a * 270) * Math.exp(-a * 37);
      } else if (type === 'signal') {
        spread += sin(784, a, sin(191, a) * .21) * .062 * Math.min(1, a * 60) * Math.exp(-a * 7.3);
      } else if (type === 'glass') {
        const amp = Math.min(1, a * 34) * Math.exp(-a * 3.1);
        spread += amp * (sin(upper * 2, a) * .083 + sin(upper * 4.01, a) * .018);
      } else {
        spread += filtered * Math.sin(Math.PI * Math.min(.999, a / 1.2)) ** 6 * .085;
      }
    }
    low += filtered * .026 * swells;
    const left = Math.tanh((center + low + voicing + spread) * 1.23) * fade;
    const right = Math.tanh((center + low + voicing * .88 + spread * .83 + .014 * change * sin(upper * 1.004, t)) * 1.23) * fade;
    wav.writeInt16LE(Math.round(left * 32767), 44 + i * 4);
    wav.writeInt16LE(Math.round(right * 32767), 46 + i * 4);
  }
  return wav;
}
