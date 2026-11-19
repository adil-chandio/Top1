const TAU = 2 * Math.PI;
export const clamp = (value, min = 0, max = 1) => Math.max(min, Math.min(max, value));
export const smooth = (value) => { const t = clamp(value); return t * t * (3 - 2 * t); };
export const mix = (a, b, t) => a + (b - a) * t;

export const FILE_TILES = 6;
export const LAMP_TRAVEL = Object.freeze({ from: .044, to: -.34, frequency: 8, damping: .73, min: -.366, max: .048 });
export const MOON_ORBIT = Object.freeze({ a: 2.9, e: .185, period: 47, phase: .072 });

// The picture and Foley share these cue times rather than matching by ear.
export function fileDropCue(index) {
  const release = 3.35 + index * .31;
  const height = .69 + index * .075;
  const gravity = 10.8;
  return { release, height, gravity, restitution: .25, impactAt: release + Math.sqrt(2 * height / gravity) };
}

// Analytic free fall and a lossy, frictionless ground contact. Distances are in
// scene units; gravity is scaled for the visualization's slow-motion clock.
export function fallingBody(time, { height, gravity = 11.2, restitution = .26, bounces = 3 }) {
  if (time <= 0) return { height, velocity: 0, contacts: 0 };
  const impactSpeed = Math.sqrt(2 * gravity * height);
  const impactAt = impactSpeed / gravity;
  if (time < impactAt) return { height: height - gravity * time ** 2 / 2, velocity: -gravity * time, contacts: 0 };
  let age = time - impactAt;
  let speed = impactSpeed * restitution;
  for (let contacts = 1; contacts <= bounces; contacts++) {
    const airTime = 2 * speed / gravity;
    if (age < airTime) return { height: speed * age - gravity * age ** 2 / 2, velocity: speed - gravity * age, contacts };
    age -= airTime;
    speed *= restitution;
  }
  return { height: 0, velocity: 0, contacts: bounces + 1 };
}

// A viscously damped hinge, initially at rest. The damped overshoot is bounded
// by the housing limits rather than an infinite overshooting CSS ease.
export function hingeAngle(time, { from, to, frequency = 9, damping = .76, min = -Infinity, max = Infinity }) {
  const t = Math.max(0, time);
  const wd = frequency * Math.sqrt(1 - damping ** 2);
  const decay = Math.exp(-damping * frequency * t);
  const angle = to + (from - to) * decay * (Math.cos(wd * t) + (damping * frequency / wd) * Math.sin(wd * t));
  return clamp(angle, min, max);
}

// Elliptical two-body motion in its local plane. Mean anomaly advances in
// time, not true anomaly: the craft naturally speeds up near periapsis.
export function keplerPosition(time, { a, e, period, phase = 0 }) {
  const mean = ((phase + TAU * time / period) % TAU + TAU) % TAU;
  let anomaly = mean;
  for (let i = 0; i < 7; i++) anomaly -= (anomaly - e * Math.sin(anomaly) - mean) / (1 - e * Math.cos(anomaly));
  const b = a * Math.sqrt(1 - e ** 2);
  const x = a * (Math.cos(anomaly) - e);
  const z = b * Math.sin(anomaly);
  const dE = TAU / (period * (1 - e * Math.cos(anomaly)));
  return { x, z, radius: Math.hypot(x, z), speed: Math.hypot(a * Math.sin(anomaly) * dE, b * Math.cos(anomaly) * dE) };
}

export function cutAt(time, film) {
  const index = Math.max(0, film.shots.findLastIndex(({ at }) => at <= time));
  const shot = film.shots[index];
  const end = film.shots[index + 1]?.at ?? film.duration;
  const age = Math.max(0, time - shot.at);
  return { index, shot, age, progress: clamp(age / (end - shot.at)), remaining: Math.max(0, end - time) };
}
