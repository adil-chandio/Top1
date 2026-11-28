/**
 * Monarch V6.3 Director Optics, Spatial Continuity & Archetype Lighting SDK (`director_optics_sdk.js`)
 *
 * Runtime bridge between `tools/director-producer-os/` (`director-plan.json`, `world_archetypes.json`,
 * `director_linter.py`) and Three.js WebGL2 scenes:
 *   1. Full-frame 36mm cinema lens (`mm`) <-> Three.js `PerspectiveCamera.fov` (`deg`) for 9:16 & 16:9
 *   2. Distance-first physical framing calculator (visible width/height at distance + 18% safe margin)
 *   3. Planckian Kelvin-to-sRGB/Linear blackbody color & stop-ratio key:fill lighting calculator
 *   4. 180-degree Line-of-Action & 30-degree jump-cut vector verification
 *   5. Walter Murch / Bruce Block 9-Zone Eye-Trace screen-space projector
 */

export const CINEMA_GATES_MM = Object.freeze({
  '9:16_short': { widthMm: 20.25, heightMm: 36.00 },
  '16:9_long': { widthMm: 36.00, heightMm: 20.25 },
});

/**
 * Convert a full-frame cinema focal length (mm) to Three.js vertical FOV (degrees).
 * Matches `director_linter.py:compute_visible_dimensions_m` identically.
 */
export function lensMmToThreeFovY(lensMm, format = '9:16_short') {
  const gate = CINEMA_GATES_MM[format] || CINEMA_GATES_MM['9:16_short'];
  return (2.0 * Math.atan((gate.heightMm * 0.5) / lensMm) * 180.0) / Math.PI;
}

/**
 * Distance-first optical calculator: set physical camera-to-subject distance FIRST (controlling
 * perspective & spatial intimacy), then pick focal length `lensMm` to set framing.
 */
export function computeCinemaFraming(lensMm, distanceM, format = '9:16_short') {
  const gate = CINEMA_GATES_MM[format] || CINEMA_GATES_MM['9:16_short'];
  const visibleWidthM = (2.0 * distanceM * (gate.widthMm * 0.5)) / lensMm;
  const visibleHeightM = (2.0 * distanceM * (gate.heightMm * 0.5)) / lensMm;
  const fovYDeg = lensMmToThreeFovY(lensMm, format);
  const fovXDeg = (2.0 * Math.atan((gate.widthMm * 0.5) / lensMm) * 180.0) / Math.PI;
  return {
    lensMm,
    distanceM,
    format,
    fovYDeg,
    fovXDeg,
    visibleWidthM,
    visibleHeightM,
    maxSafeSubjectWidthM: visibleWidthM / 1.18,
  };
}

/**
 * Compute required camera distance (m) to frame `subjectWidthM` cleanly with a `marginFactor`
 * (default 1.24 -> ~19% breathing room across left/right edges in 9:16).
 */
export function distanceForSubjectWidth(subjectWidthM, lensMm, format = '9:16_short', marginFactor = 1.24) {
  const gate = CINEMA_GATES_MM[format] || CINEMA_GATES_MM['9:16_short'];
  const targetVisibleWidth = subjectWidthM * marginFactor;
  return (targetVisibleWidth * lensMm) / gate.widthMm;
}

/**
 * Apply a `director-plan.json` shot entry's optical & spatial pose directly to a `THREE.PerspectiveCamera`.
 */
export function applyShotOpticsToCamera(camera, shotSpec, format = '9:16_short') {
  const [cx, cy, cz] = shotSpec.camera_pos_xyz;
  const [lx, ly, lz] = shotSpec.look_at_xyz;
  camera.fov = lensMmToThreeFovY(shotSpec.lens_mm_equiv, format);
  camera.position.set(cx, cy, cz);
  camera.lookAt(lx, ly, lz);
  camera.updateProjectionMatrix();
  return camera;
}

/**
 * Physical Kelvin (1500K..15000K) -> normalized sRGB [r, g, b] (Tanner Helland Planckian locus fit).
 */
export function kelvinToSrgb01(kelvin) {
  const temp = Math.max(1500, Math.min(15000, kelvin)) / 100.0;
  let r;
  let g;
  let b;

  if (temp <= 66.0) {
    r = 255.0;
    g = 99.4708025861 * Math.log(temp) - 161.1195681661;
    b = temp <= 19.0 ? 0.0 : 138.5177312231 * Math.log(temp - 10.0) - 305.0447927307;
  } else {
    r = 329.698727446 * Math.pow(temp - 60.0, -0.1332047592);
    g = 288.1221695283 * Math.pow(temp - 60.0, -0.0755148492);
    b = 255.0;
  }

  return [
    Math.max(0.0, Math.min(1.0, r / 255.0)),
    Math.max(0.0, Math.min(1.0, g / 255.0)),
    Math.max(0.0, Math.min(1.0, b / 255.0)),
  ];
}

/**
 * Convert cinematographic key:fill ratio string ('2:1', '4:1', '8:1', '12:1') into exact fill multiplier
 * and stop difference so high-key vs low-key chiaroscuro worlds NEVER look identically lit.
 */
export function parseContrastRatio(ratioStr = '4:1', keyIntensity = 2.4) {
  const parts = String(ratioStr).split(':').map(Number);
  const ratio = parts.length === 2 && parts[1] > 0 ? parts[0] / parts[1] : 4.0;
  const fillIntensity = keyIntensity / Math.max(1.0, ratio);
  const stopsDifference = Math.log2(Math.max(1.0, ratio));
  return {
    ratio,
    stopsDifference,
    keyIntensity,
    fillIntensity,
    rimIntensity: keyIntensity * (ratio >= 8.0 ? 0.65 : 0.35),
  };
}

/**
 * 180-degree Line-of-Action XZ side sign (+1, -1, or 0 on-axis).
 */
export function check180AxisSide(lineOfActionXZ, camPosXYZ) {
  const [x1, z1, x2, z2] = lineOfActionXZ;
  const [cx, , cz] = camPosXYZ;
  const cross = (x2 - x1) * (cz - z1) - (z2 - z1) * (cx - x1);
  if (Math.abs(cross) < 1e-6) return 0;
  return cross > 0 ? 1 : -1;
}

/**
 * 3D angular separation (degrees) between Shot A and Shot B sightlines (`>= 30 deg` avoids jump cuts).
 */
export function compute30DegreeSeparation(camA, lookA, camB, lookB) {
  const va = [camA[0] - lookA[0], camA[1] - lookA[1], camA[2] - lookA[2]];
  const vb = [camB[0] - lookB[0], camB[1] - lookB[1], camB[2] - lookB[2]];
  const na = Math.hypot(va[0], va[1], va[2]);
  const nb = Math.hypot(vb[0], vb[1], vb[2]);
  if (na < 1e-8 || nb < 1e-8) return 0.0;
  const cosT = Math.max(-1.0, Math.min(1.0, (va[0] * vb[0] + va[1] * vb[1] + va[2] * vb[2]) / (na * nb)));
  return (Math.acos(cosT) * 180.0) / Math.PI;
}

/**
 * Project a `THREE.Vector3` focal point into normalized `[0..1, 0..1]` top-left-origin screen coordinates
 * and return its Bruce Block / Walter Murch 9-Zone Continuum Grid sector.
 */
export function projectNormalizedEyeTrace(worldPointVec3, camera) {
  const ndc = worldPointVec3.clone().project(camera);
  const x = Math.max(0.0, Math.min(1.0, (ndc.x + 1.0) * 0.5));
  const y = Math.max(0.0, Math.min(1.0, (1.0 - ndc.y) * 0.5));
  const col = x < 1 / 3 ? 'LEFT' : x < 2 / 3 ? 'CENTER' : 'RIGHT';
  const row = y < 1 / 3 ? 'TOP' : y < 2 / 3 ? 'MID' : 'BOTTOM';
  return {
    xy: [Number(x.toFixed(3)), Number(y.toFixed(3))],
    zone: `${row}_${col}`,
  };
}
