// A corner-cube in local coordinates: x,y,z >= 0, x+y+z <= edge.
// The three back faces are the coordinate planes and the diagonal face is
// the air/plastic aperture. This traces a single geometrical-optics ray,
// not diffuse light, diffraction or the full manufactured reflector.
const EPS = 1e-8;
const sum = (v) => v[0] + v[1] + v[2];
export const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
export const scale3 = (v, factor) => v.map((c) => c * factor);
export const add3 = (v, w) => v.map((c, i) => c + w[i]);
export const unit3 = (v) => scale3(v, 1 / Math.hypot(...v));
const axis = (i) => [0, 1, 2].map((n) => Number(i === n));
export const reflect = (direction, normal) => add3(direction, scale3(normal, -2 * dot3(direction, normal)));

export function refract(direction, incidentSideNormal, from, to) {
  const cosine = -dot3(direction, incidentSideNormal);
  const ratio = from / to;
  const k = 1 - ratio * ratio * (1 - cosine * cosine);
  if (cosine <= 0 || k < 0) return null;
  return unit3(add3(scale3(direction, ratio), scale3(incidentSideNormal, ratio * cosine - Math.sqrt(k))));
}

export const CORNER_EDGE = 2.5;
export const PLASTIC_IOR = 1.49;
export const APERTURE_NORMAL = Object.freeze(unit3([1, 1, 1]));

export function traceCorner(entry, incident, edge = CORNER_EDGE, ior = PLASTIC_IOR) {
  if (Math.abs(sum(entry) - edge) > EPS || entry.some((c) => c <= EPS)) throw new RangeError('Entry must lie inside the triangular aperture.');
  let point = entry.slice();
  let direction = refract(unit3(incident), APERTURE_NORMAL, 1, ior);
  if (!direction) throw new RangeError('The ray must enter the aperture from air.');
  const events = [{ kind: 'entry', point, direction }];
  for (let n = 0; n < 10; n++) {
    let face = -1;
    let distance = sum(direction) > EPS ? (edge - sum(point)) / sum(direction) : Infinity;
    for (let i = 0; i < 3; i++) {
      if (direction[i] >= -EPS) continue;
      const toFace = -point[i] / direction[i];
      if (toFace >= -EPS && toFace < distance - EPS) { face = i; distance = Math.max(0, toFace); }
    }
    if (!Number.isFinite(distance) || distance < EPS) throw new RangeError('Ray hits a shared edge or does not meet a face.');
    point = add3(point, scale3(direction, distance));
    if (face === -1) {
      const outgoing = refract(direction, scale3(APERTURE_NORMAL, -1), ior, 1);
      return [...events, { kind: outgoing ? 'exit' : 'blocked', point, direction: outgoing }];
    }
    point[face] = 0;
    const normal = axis(face);
    const transmitted = refract(direction, normal, ior, 1);
    if (transmitted) return [...events, { kind: 'leak', face, point, direction: transmitted }];
    const cosine = -dot3(direction, normal);
    direction = reflect(direction, normal);
    events.push({ kind: 'bounce', face, point, direction, angle: Math.acos(Math.max(0, Math.min(1, cosine))) });
  }
  throw new RangeError('Ray traversal did not converge.');
}

// Select an off-centre ray: it strikes three different faces and exits at a
// different point. The external source/view alignment is a separate model.
export const RAY_IN = Object.freeze(unit3([-.66, -.58, -.47]));
export const OPTIC_PATH = Object.freeze(traceCorner([.40, .74, 1.36], RAY_IN));

// Put the aperture in a plane facing +Z. The rows form an orthonormal basis.
const benchX = unit3([1, -1, 0]);
const benchY = unit3([1, 1, -2]);
export function cornerToBench(value, direction = false, edge = CORNER_EDGE) {
  return [dot3(value, benchX), dot3(value, benchY), dot3(value, APERTURE_NORMAL) - (direction ? 0 : edge / Math.sqrt(3))];
}

const clamp01 = (x) => Math.min(1, Math.max(0, x));
const smooth01 = (x) => { const s = clamp01(x); return s * s * (3 - 2 * s); };

// A camera close to the illuminator sees the return lobe; a camera off axis
// sees little of it. This is an illustrative lobe, not a lux measurement.
export function returnPower(viewDirection, sourceDirection, lamp) {
  const cosine = Math.min(1, Math.max(-1, dot3(unit3(viewDirection), unit3(sourceDirection))));
  const angle = Math.acos(cosine);
  return clamp01(lamp) * Math.exp(-((angle / .186) ** 2));
}

export const fadeBetween = (time, start, end) => smooth01((time - start) / (end - start));

// Current segment distances are computed from exact bounce points. Only the
// presentation clock is stretched to match narration; it is not light speed.
export function pathProgress(t, anchors) {
  return anchors.slice(1).map((end, index) => clamp01((t - anchors[index]) / (end - anchors[index])));
}
