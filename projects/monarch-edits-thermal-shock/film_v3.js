import * as THREE from 'three';
import {
  createCinemaCameraRig,
  GLM,
} from '/tools/monarch-v6-imax-sdk/index.js';
import {
  FPS, DURATION, TOTAL_FRAMES,
} from './film_v3_world.js';

/**
 * THERMAL SHOCK V3 "TABAHI" — 10-Shot Cinema Director + Kinetic HUD.
 * Shot list, speed ramps, impact shake, dutch rolls, DoF racks, bullet-time
 * shard choreography and projected 3D->2D science callouts.
 */

export const SHATTER_T = 15.2;
export const SHATTER_F = Math.round(SHATTER_T * FPS); // 456
export const VACUUM_T0 = 15.10;
export const VACUUM_T1 = 15.20;

export const SHOTS = [
  { id: 'S1_HOOK',    f0: 0,   f1: 66   },
  { id: 'S2_SETUP',   f0: 66,  f1: 132  },
  { id: 'S3_GARAM',   f0: 132, f1: 240  },
  { id: 'S4_POUR',    f0: 240, f1: 348  },
  { id: 'S5_STRESS',  f0: 348, f1: 456  },
  { id: 'S6_SHATTER', f0: 456, f1: 522  },
  { id: 'S7_DEBRIS',  f0: 522, f1: 636  },
  { id: 'S8_SCIENCE', f0: 636, f1: 810  },
  { id: 'S9_RULE',    f0: 810, f1: 930  },
  { id: 'S10_CTA',    f0: 930, f1: 1080 },
];

export const CAPTIONS = [
  { t0: 0.30,  t1: 2.20,  l1: 'GARAM SHEESHA',     l2: 'THANDA PAANI = TABAAHI?',      hi: 'TABAAHI',   accent: '#FFB454' },
  { t0: 2.30,  t1: 4.35,  l1: '36 SECOND MEIN',    l2: 'POORI SCIENCE - CHALO!',       hi: 'POORI SCIENCE', accent: '#3AD4BE' },
  { t0: 4.45,  t1: 7.95,  l1: '450 DEGREE GARAM',  l2: 'SHEESHA LOHE JITNA TEZ',       hi: '450',       accent: '#FFB454' },
  { t0: 8.05,  t1: 11.55, l1: 'THANDA PAANI GIRA', l2: 'SEEDHA GARAM SHEESHE PAR',     hi: 'THANDA',    accent: '#3AD4BE' },
  { t0: 11.65, t1: 13.55, l1: 'BAHAR THANDA',      l2: 'ANDAR ABHI 450!',              hi: 'ANDAR',     accent: '#FF4A1C' },
  { t0: 13.65, t1: 15.10, l1: 'STRESS 97%',        l2: 'SHEESHA AB SAHN nahi KARTA',   hi: '97%',       accent: '#FF4A1C' },
  { t0: 15.22, t1: 17.35, l1: 'THERMAL SHOCK!',    l2: '1 SECOND MEIN PHATA!',         hi: 'THERMAL SHOCK', accent: '#FF4A1C' },
  { t0: 17.45, t1: 21.15, l1: 'TIKONE KE TUKDE',   l2: 'HAWA MEIN UDD GAYE',           hi: 'UDD GAYE',  accent: '#FFB454' },
  { t0: 21.25, t1: 24.10, l1: 'BAHAR WALI DEEWAR', l2: 'TEZI SE SUKADTI HAI',          hi: 'TEZI SE',   accent: '#3AD4BE' },
  { t0: 24.20, t1: 26.95, l1: 'ANDAR ABHI BHI',    l2: 'PHAILA HUA HAI',               hi: 'PHAILA',    accent: '#FF4A1C' },
  { t0: 27.05, t1: 30.95, l1: 'BOROSILICATE',      l2: 'AARAM SE SIKUDTA - NAHI PHATA', hi: 'NAHI PHATA', accent: '#3AD4BE' },
  { t0: 31.05, t1: 35.80, l1: 'AGLA EXPERIMENT?',  l2: 'FOLLOW - MONARCH EDITS',       hi: 'FOLLOW',    accent: '#FFB454' },
];

function shotAtFrame(f) {
  for (const s of SHOTS) if (f >= s.f0 && f < s.f1) return s;
  return SHOTS[SHOTS.length - 1];
}

// Per-shot camera choreography: eased keyframes inside each shot.
// pos/look given as [x,y,z]; fov in degrees; dutch in degrees.
const SHOT_CAM = {
  S1_HOOK: {
    from: { pos: [1.35, 2.70, 2.60], look: [0.0, 2.10, 0.0], fov: 40, dutch: 1.2 },
    to:   { pos: [0.75, 2.50, 2.00], look: [0.0, 2.08, 0.0], fov: 39, dutch: 0.6 },
    focus: [0.0, 2.12, 0.0], dofRange: 3.2, maxBlur: 4.2,
  },
  S2_SETUP: {
    from: { pos: [0.75, 2.50, 2.00], look: [0.0, 2.08, 0.0], fov: 39, dutch: 0.6 },
    to:   { pos: [-0.55, 1.85, 7.1], look: [0.0, 1.30, 0.0],  fov: 38, dutch: 0.0 },
    focus: [0, 1.25, 0], dofRange: 16.0, maxBlur: 3.4,
  },
  S3_GARAM: {
    arc: { r0: 6.6, r1: 5.3, a0: 0.42, a1: 1.05, y0: 2.0, y1: 1.62 },
    look: [0, 1.30, 0], fovFrom: 38, fovTo: 36, dutch: 0.0,
    focus: [0, 1.25, 0], dofRange: 12.0, maxBlur: 3.4,
  },
  S4_POUR: {
    from: { pos: [1.7, 3.7, 4.9], look: [0.0, 1.05, 0.0], fov: 36, dutch: 1.5 },
    to:   { pos: [0.9, 3.0, 4.3], look: [0.0, 1.30, 0.0], fov: 36, dutch: 0.6 },
    focus: [0, 1.10, 0], dofRange: 9.0, maxBlur: 3.8,
  },
  S5_STRESS: {
    from: { pos: [-1.9, 2.10, 4.2], look: [0.0, 1.95, 0.0], fov: 34, dutch: 0.0 },
    to:   { pos: [-0.9, 2.30, 3.1], look: [0.0, 1.95, 0.0], fov: 31, dutch: -4.0 },
    focus: [0, 1.95, 0], dofRange: 7.0, maxBlur: 4.2,
  },
  S6_SHATTER: {
    orbit: { r: 4.7, a0: -0.55, a1: 2.0, y0: 1.45, y1: 1.75 },
    look: [0, 1.20, 0], fovFrom: 40, fovTo: 34, dutch: -2.0,
    focus: [0, 1.20, 0], dofRange: 7.0, maxBlur: 4.4,
  },
  S7_DEBRIS: {
    from: { pos: [2.1, 1.15, 3.9], look: [0.0, 0.60, 0.0], fov: 36, dutch: -1.0 },
    to:   { pos: [0.7, 1.25, 3.0], look: [0.0, 0.55, 0.0], fov: 36, dutch: -0.4 },
    focus: [0, 0.45, 0], dofRange: 5.5, maxBlur: 4.0,
  },
  S8_SCIENCE: {
    from: { pos: [0.0, 1.55, 6.3], look: [0.0, 1.30, 0.0], fov: 37, dutch: 0.0 },
    to:   { pos: [0.0, 1.42, 5.5], look: [0.0, 1.28, 0.0], fov: 37, dutch: 0.0 },
    focus: [0, 1.25, 0], dofRange: 18.0, maxBlur: 3.2,
  },
  S9_RULE: {
    arc: { r0: 5.9, r1: 5.6, a0: 2.7, a1: 3.4, y0: 1.65, y1: 1.45 },
    look: [0, 1.05, 0], fovFrom: 36, fovTo: 36, dutch: 0.0,
    focus: [0, 1.00, 0], dofRange: 12.0, maxBlur: 3.4,
  },
  S10_CTA: {
    from: { pos: [2.5, 2.7, 5.3], look: [0.0, 1.10, 0.0], fov: 34, dutch: 0.0 },
    to:   { pos: [0.0, 4.8, 8.8], look: [0.0, 1.60, 0.0], fov: 40, dutch: 0.0 },
    focus: [0, 1.30, 0], dofRange: 22.0, maxBlur: 3.2,
  },
};

// Speed-ramped simulated shatter time (bullet-time -> realtime, C1-continuous)
function shatterSimT(dt) {
  if (dt <= 0) return 0;
  if (dt < 1.4) return 0.30 * dt;
  return 0.42 + (dt - 1.4) * (0.30 + 0.70 * GLM.smoothstep(0, 1.0, (dt - 1.4) / 1.9));
}

export function createThermalDirectorV3(world, camera) {
  const rig = createCinemaCameraRig(camera, {
    totalFrames: TOTAL_FRAMES,
    shotCuts: new Set(SHOTS.map((s) => s.f0)),
    impacts: [
      { frame: SHATTER_F, amp: 2.4, decay: 0.15, freq: 2.35, durationFrames: 26 },
      { frame: 432, amp: 0.5, decay: 0.26, freq: 3.1, durationFrames: 12 },
      { frame: 408, amp: 0.42, decay: 0.28, freq: 3.3, durationFrames: 12 },
      { frame: 387, amp: 0.34, decay: 0.30, freq: 3.5, durationFrames: 12 },
      { frame: 247, amp: 0.5, decay: 0.30, freq: 2.9, durationFrames: 14 },
    ],
  });

  const camPos = new THREE.Vector3();
  const camLook = new THREE.Vector3();
  const tmpA = new THREE.Vector3();
  const anchorScreen = [];

  function projectAnchor(v3) {
    tmpA.copy(v3).project(camera);
    return {
      x: (tmpA.x * 0.5 + 0.5) * 1080,
      y: (-tmpA.y * 0.5 + 0.5) * 1920,
      visible: tmpA.z < 1.0,
    };
  }

  function evaluateFrame(frame) {
    const f = ((frame % TOTAL_FRAMES) + TOTAL_FRAMES) % TOTAL_FRAMES;
    const t = f / FPS;
    const shot = shotAtFrame(f);
    const u = GLM.clamp((f - shot.f0) / Math.max(1, shot.f1 - shot.f0), 0, 1);
    const cam = SHOT_CAM[shot.id];

    // ---------- 1. EVENT STATE ----------
    const heat = GLM.smoothstep(4.4, 7.6, t);
    const pourU = GLM.smoothstep(8.0, 11.4, t);
    const pourOn = t >= 8.0 && t < 11.4;
    const coldFront = GLM.clamp(GLM.smoothstep(8.7, 12.8, t) * 1.18, 0, 1.18);
    const xray = GLM.smoothstep(11.6, 12.5, t);
    const stress = t < 12.0 ? 0 : GLM.clamp((t - 12.0) / 3.14, 0, 0.97);
    const isShattered = t >= SHATTER_T;
    const dtS = isShattered ? t - SHATTER_T : 0;
    const simT = isShattered ? shatterSimT(dtS) : 0;
    const scienceOn = t >= 21.2 && t < 27.0;
    const boroOn = t >= 26.6;

    // ---------- 2. ANIMATION ----------
    const w = world;

    w.coreMat.uniforms.uHeat.value = isShattered ? 0 : heat;
    w.coreMat.uniforms.uXray.value = xray;
    w.coreMat.uniforms.uTime.value = t;
    w.coldMat.uniforms.uColdFront.value = isShattered || scienceOn ? 1.05 : coldFront;
    w.coldMat.uniforms.uTime.value = t;
    // Shot-driven light choreography
    const s7Light = GLM.smoothstep(17.4, 18.2, t) * (1 - GLM.smoothstep(21.0, 21.8, t));
    w.debrisLight.intensity = 3.6 * s7Light;
    w.warmFill.intensity = 1.6 + s7Light * 2.2;
    w.cyanRim.intensity = (t < 4.4 ? 9.0 : 6.5) - heat * 1.4 + xray * 2.2 + s7Light * 1.5;
    w.coldLight.intensity = (t < 4.4 ? 1.2 : 0) + (t > 8.7 && !isShattered ? 2.6 * GLM.smoothstep(8.7, 9.6, t) : 0);
    w.keyLight.intensity = (2.6 - heat * 0.5) * (1 - xray * 0.42) + s7Light * 0.3;
    w.halo.material.opacity = 0.34 * (1 - xray * 0.78) * (1 - s7Light * 0.35);
    w.horizon.material.opacity = 0.85 * (1 - xray * 0.72);
    // X-ray schematic: single-sided core (kills additive double-stack wash)
    const wantSide = xray > 0.5 ? THREE.FrontSide : THREE.DoubleSide;
    if (w.coreMat.side !== wantSide) w.coreMat.side = wantSide;

    w.heatLight.intensity = isShattered ? 0 : heat * 5.2 * (1 - 0.35 * coldFront);

    // Glass visibility states
    if (!isShattered && !boroOn) {
      w.glassGroup.visible = true;
      w.outerGlass.visible = true;
      w.baseRing.visible = false;
      w.boroGroup.visible = false;
      // pre-shatter vibration
      const vib = GLM.smoothstep(12.6, SHATTER_T, t) * 0.014;
      w.glassGroup.position.x = Math.sin(t * 47.0) * vib;
      w.glassGroup.position.z = Math.cos(t * 39.0) * vib;
      // X-ray ghosting (no transmission pass — pure opacity glass)
      w.glassMat.opacity = 0.30 - xray * 0.24;
      w.ghostEdges.material.opacity = xray * 0.85;
      w.ghostEdges.visible = xray > 0.01;
    } else if (isShattered && !scienceOn && !boroOn) {
      w.glassGroup.visible = false;
      w.baseRing.visible = true;
    }

    // Science schematic (S8)
    if (scienceOn) {
      w.glassGroup.visible = true;
      w.outerGlass.visible = false;
      w.baseRing.visible = true;
      w.ghostEdges.visible = true;
      w.ghostEdges.material.opacity = 0.9;
      w.coreMat.uniforms.uHeat.value = 0.72;
      w.coreMat.uniforms.uXray.value = 1.0;
      w.glassGroup.position.set(0, 0, 0);
    }
    // Borosilicate comparison (S9/S10)
    if (boroOn) {
      const boroIn = GLM.smoothstep(26.6, 27.4, t);
      w.glassGroup.visible = false;
      w.baseRing.visible = true;
      w.boroGroup.visible = true;
      const flex = 1.0 + Math.sin(t * 3.1) * 0.028 * boroIn;
      w.boroGroup.scale.set(flex, 1.0 / flex * 0.5 + 0.5, flex);
      w.boroEdges.material.opacity = 0.55 * boroIn;
    }

    // Water pour
    w.streamMat.uniforms.uTime.value = t;
    w.streamMat.uniforms.uOpacity.value = pourOn ? 0.9 * GLM.smoothstep(8.0, 8.35, t) * (1 - GLM.smoothstep(11.15, 11.4, t)) : 0.0;
    w.stream.visible = w.streamMat.uniforms.uOpacity.value > 0.01;
    const waterLevel = 0.42 + pourU * 1.05;
    w.waterSurf.position.y = waterLevel;
    w.waterSurf.material.opacity = t > 8.2 && !isShattered ? 0.55 : 0.0;
    // ripple pulse
    const ripple = Math.sin(t * 9.0) * 0.05 + 1.0;
    w.waterSurf.scale.setScalar(t > 8.2 && !isShattered && !scienceOn ? ripple : 1.0);

    // Splash crown at first contact (8.15s)
    if (t >= 8.12 && t < 9.0) {
      const sp = (t - 8.12) / 0.88;
      w.splash.visible = true;
      w.splash.scale.setScalar(1 + sp * 3.4);
      w.splashMat.opacity = 0.85 * (1 - sp);
    } else {
      w.splash.visible = false;
    }

    // Pour spray droplets
    if (pourOn) {
      w.droplets.mesh.visible = true;
      w.droplets.update(new THREE.Vector3(0, waterLevel + 0.05, 0), (t - 8.1) * 1.0, { intensity: 0.5, speedScale: 0.4, dirSign: 1.0 });
    } else if (!isShattered) {
      w.droplets.mesh.visible = false;
    }

    // Steam wisps
    const steamOn = t > 4.7 && t < 12.8 && !isShattered;
    for (const s of w.steam) {
      if (!steamOn) { s.sp.material.opacity = 0; continue; }
      const cyc = ((t / 2.6) + s.phase) % 1.0;
      s.sp.position.set(
        s.x0 + Math.sin(cyc * 9.0 + s.phase * 7) * 0.16 * cyc,
        2.35 + cyc * 1.5,
        s.z0 + Math.cos(cyc * 7.0 + s.phase * 5) * 0.13 * cyc
      );
      const sc = 0.30 + cyc * 0.85;
      s.sp.scale.set(sc, sc, 1);
      s.sp.material.opacity = 0.30 * (1 - cyc) * Math.min(1, cyc * 6.0) * heat;
    }

    // Crack growth (three staggered cracks)
    const crackWins = [
      [12.9, 13.35],
      [13.6, 14.05],
      [14.4, 14.85],
    ];
    for (let i = 0; i < w.cracks.length; i++) {
      const c = w.cracks[i];
      const [t0, t1] = crackWins[i];
      if (isShattered || scienceOn) { c.mesh.visible = false; continue; }
      if (t >= t0 && t <= t1) {
        c.mesh.visible = true;
        const g = (t - t0) / (t1 - t0);
        c.mesh.geometry.setDrawRange(0, Math.floor(c.totalVerts * g));
        c.mat.opacity = 0.9;
        const flick = 0.8 + 0.2 * Math.sin(t * 60 + i * 2);
        c.mat.color.set('#FFB454').multiplyScalar(flick);
      } else if (t > t1) {
        c.mesh.visible = true;
        c.mesh.geometry.setDrawRange(0, c.totalVerts);
        c.mat.opacity = 0.75;
        c.mat.color.set('#FFB454');
      } else {
        c.mesh.visible = false;
      }
    }

    // ---------- SHATTER SYSTEM ----------
    if (isShattered) {
      w.glassGroup.visible = scienceOn;
      w.outerGlass.visible = false;
      w.coldShell.visible = scienceOn;
      for (const c of w.cracks) c.mesh.visible = false;
      w.baseRing.visible = true;
      w.boroGroup.visible = boroOn;

      // Whiteout flash (2-frame peak, exp decay)
      const wOp = dtS < 0.028 ? 1.0 : Math.exp(-(dtS - 0.028) * 16.0);
      w.whiteout.visible = dtS < 0.5 && wOp > 0.02;
      w.whiteoutMat.opacity = wOp * 0.92;

      // Shockwave floor rings (staggered)
      for (let i = 0; i < w.rings.length; i++) {
        const r = w.rings[i];
        const pr = GLM.clamp((dtS - i * 0.07) / 0.95, 0, 1);
        if (pr > 0 && pr < 1) {
          r.ring.trigger({ x: 0, y: r.y, z: 0, size: r.size, progress: pr, colorHex: r.color });
        } else {
          r.ring.mesh.visible = false;
        }
      }

      // Vertical torus shockwave
      if (dtS < 1.25) {
        const tp = GLM.smoothstep(0, 1.2, dtS);
        w.torus.visible = true;
        w.torus.scale.setScalar(1 + tp * 6.2);
        w.torusMat.opacity = 0.85 * (1 - tp);
        w.torus.rotation.z = tp * 0.4;
      } else {
        w.torus.visible = false;
      }

      // 64 shards: ballistic + drag + floor bounce
      const g = 9.8 * 1.35;
      for (const s of w.shards) {
        s.mesh.visible = simT > 0.005;
        if (!s.mesh.visible) continue;
        const k = s.drag;
        const dx = s.vx * (1 - Math.exp(-k * simT)) / k;
        const dz = s.vz * (1 - Math.exp(-k * simT)) / k;
        // vertical: analytic parabola with 1 bounce
        const yRaw = s.y0 + s.vy * simT - 0.5 * g * simT * simT;
        let y = yRaw;
        if (yRaw < 0.07) {
          const tHit = (s.vy + Math.sqrt(Math.max(0, s.vy * s.vy + 2 * g * Math.max(0, s.y0 - 0.07)))) / g;
          if (simT > tHit) {
            const tb = simT - tHit;
            const vyB = Math.abs(s.vy) * 0.30;
            y = Math.max(0.06, 0.07 + vyB * tb - 0.5 * g * tb * tb * 0.60);
          }
        }
        s.mesh.position.set(s.x0 + dx, y, s.z0 + dz);
        s.mesh.rotation.set(s.ax * simT, s.ay * simT, s.az * simT);
        const fade = 1.0 - GLM.smoothstep(3.6, 5.6, simT) * 0.35;
        s.mesh.scale.setScalar(s.scale * fade);
      }

      // Sparks
      const sparkI = Math.exp(-dtS * 2.4);
      if (sparkI > 0.02) {
        w.sparks.mesh.visible = true;
        w.sparks.update(new THREE.Vector3(0, 1.25, 0), simT, { intensity: sparkI, speedScale: 1.0, dirSign: 1.0 });
      } else {
        w.sparks.mesh.visible = false;
      }
      // Dust motes keep drifting
      w.dust.update(t);
    } else {
      w.whiteout.visible = false;
      w.torus.visible = false;
      for (const r of w.rings) r.ring.mesh.visible = false;
      for (const s of w.shards) s.mesh.visible = false;
      w.sparks.mesh.visible = false;
      w.dust.update(t);
    }

    // ---------- 3. CINEMA CAMERA ----------
    if (cam.arc) {
      const r = GLM.mix(cam.arc.r0, cam.arc.r1, GLM.easeInOutCubic(u));
      const a = GLM.mix(cam.arc.a0, cam.arc.a1, u);
      const y = GLM.mix(cam.arc.y0, cam.arc.y1, u);
      camPos.set(Math.sin(a) * r, y, Math.cos(a) * r);
      camLook.set(...cam.look);
      var fov = GLM.mix(cam.fovFrom, cam.fovTo, u);
      var dutch = cam.dutch;
    } else if (cam.orbit) {
      // Bullet-time orbit around the shatter epicenter, eased hard at start
      const a = GLM.mix(cam.orbit.a0, cam.orbit.a1, GLM.smoothstep(0, 1, Math.pow(u, 0.72)));
      const r = cam.orbit.r;
      const y = GLM.mix(cam.orbit.y0, cam.orbit.y1, u);
      camPos.set(Math.sin(a) * r, y, Math.cos(a) * r);
      camLook.set(...cam.look);
      var fov = GLM.mix(cam.fovFrom, cam.fovTo, GLM.smoothstep(0, 0.55, u));
      var dutch = cam.dutch * (1 - GLM.smoothstep(0.3, 0.8, u));
    } else {
      const e = GLM.easeInOutCubic(u);
      camPos.set(
        GLM.mix(cam.from.pos[0], cam.to.pos[0], e),
        GLM.mix(cam.from.pos[1], cam.to.pos[1], e),
        GLM.mix(cam.from.pos[2], cam.to.pos[2], e)
      );
      camLook.set(
        GLM.mix(cam.from.look[0], cam.to.look[0], e),
        GLM.mix(cam.from.look[1], cam.to.look[1], e),
        GLM.mix(cam.from.look[2], cam.to.look[2], e)
      );
      var fov = GLM.mix(cam.from.fov, cam.to.fov, e);
      var dutch = GLM.mix(cam.from.dutch, cam.to.dutch, e);
    }
    // Bullet-time extra: FOV punch at impact
    if (isShattered && shot.id === 'S6_SHATTER') {
      fov += 5.0 * Math.exp(-dtS * 3.2);
    }
    // Vacuum creep: micro push-in during dead silence
    if (t >= VACUUM_T0 && t < SHATTER_T) {
      camPos.multiplyScalar(1 - 0.012 * ((t - VACUUM_T0) / 0.1));
    }

    const rigState = rig.apply({
      frame: f,
      pos: camPos,
      look: camLook,
      fov,
      dutchDeg: dutch,
      breathAmp: shot.id === 'S6_SHATTER' ? 0.0 : 0.045,
      shutterBlurScale: 0.38,
    });

    // Whiteout billboard follows the camera exactly (post-apply, zero lag)
    if (w.whiteout.visible) {
      const fwd = tmpA.set(0, 0, -1).applyQuaternion(camera.quaternion);
      w.whiteout.position.copy(camera.position).addScaledVector(fwd, 1.0);
      w.whiteout.quaternion.copy(camera.quaternion);
    }

    // ---------- 4. POST PARAMS ----------
    const focusPoint = tmpA.set(...cam.focus);
    const focusDist = Math.max(0.5, camera.position.distanceTo(focusPoint));
    let bloomAmt = 0.5;
    if (isShattered) bloomAmt += 0.55 * Math.exp(-dtS * 3.4);
    if (pourOn) bloomAmt += 0.14;
    if (t >= 12.9 && t < SHATTER_T) bloomAmt += 0.10 * Math.exp(-(t - 14.85) * (t - 14.85) * 30.0) * 2.2;
    let exposure = 1.18;
    if (isShattered) exposure += 1.0 * Math.exp(-dtS * 11.0);
    if (heat > 0 && !isShattered) exposure += 0.07 * heat;

    // ---------- 5. HUD STATE (3D -> 2D callouts) ----------
    anchorScreen.length = 0;
    const calloutOn = (xray > 0.3 && t < SHATTER_T) || scienceOn;
    if (calloutOn) {
      anchorScreen.push({ ...projectAnchor(new THREE.Vector3(0, 2.32, 0)), label: 'RIM STRESS', value: 'MAX' });
      anchorScreen.push({ ...projectAnchor(new THREE.Vector3(0.98, 1.30, 0.15)), label: 'CORE', value: '450 C' });
      anchorScreen.push({ ...projectAnchor(new THREE.Vector3(-0.9, 0.62, 0.35)), label: 'SHELL', value: '15 C' });
    }

    return {
      time: t,
      frame: f,
      shot: shot.id,
      postParams: {
        focusDist,
        dofRange: cam.dofRange,
        maxBlur: cam.maxBlur,
        bloomAmt,
        exposure,
        motionVec: rigState.motionVec,
        time: t,
      },
      hud: {
        time: t,
        frame: f,
        temp: Math.round(20 + heat * 430),
        stress,
        xray,
        alert: stress > 0.55 || isShattered,
        callouts: anchorScreen,
        scienceOn,
        shatterT: SHATTER_T,
        coverTitle: 'GARAM SHEESHA',
        coverSubtitle: 'x THANDA PAANI',
      },
    };
  }

  return { evaluateFrame };
}

// ================= KINETIC TABAHI HUD =================

function roundRectPath(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

export function drawTabahiHud(ctx, state, captions, opts = { showCaptions: true }) {
  const W = ctx.canvas.width;
  const H = ctx.canvas.height;
  const t = state.hud.time;
  ctx.clearRect(0, 0, W, H);

  if (opts.coverMode) {
    ctx.save();
    ctx.textAlign = 'center';
    ctx.fillStyle = 'rgba(4, 8, 14, 0.55)';
    ctx.fillRect(0, 0, W, 620);
    ctx.font = '700 96px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.shadowColor = 'rgba(0,0,0,0.8)';
    ctx.shadowBlur = 26;
    ctx.fillText(state.hud.coverTitle, W / 2, 240);
    ctx.font = '700 62px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#FFB454';
    ctx.fillText(state.hud.coverSubtitle, W / 2, 330);
    ctx.font = '600 30px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(140, 220, 230, 0.9)';
    ctx.fillText('MONARCH EDITS - 3D SCIENCE', W / 2, 410);
    ctx.restore();
    return;
  }

  const hud = state.hud;

  // ---- 1. Top telemetry pill ----
  ctx.save();
  ctx.font = '600 21px "IBM Plex Mono", monospace';
  const tag = 'THERMAL LAB';
  const metric = `SURFACE ${hud.temp} C`;
  const w1 = ctx.measureText(tag).width;
  const w2 = ctx.measureText(metric).width + 30;
  const pillW = Math.min(700, 56 + w1 + w2);
  const pillX = 52, pillY = 142, pillH = 50;
  roundRectPath(ctx, pillX, pillY, pillW, pillH, 25);
  ctx.fillStyle = 'rgba(7, 12, 18, 0.72)';
  ctx.fill();
  ctx.lineWidth = 1.4;
  ctx.strokeStyle = 'rgba(255,255,255,0.16)';
  ctx.stroke();
  const pulse = 0.6 + 0.4 * Math.sin(t * Math.PI * 4.0);
  ctx.beginPath();
  ctx.arc(pillX + 26, pillY + pillH / 2, 6.0, 0, Math.PI * 2);
  ctx.fillStyle = hud.alert ? `rgba(255, 84, 60, ${pulse})` : `rgba(110, 246, 208, ${pulse})`;
  ctx.fill();
  ctx.textBaseline = 'middle';
  ctx.fillStyle = 'rgba(238, 246, 250, 0.92)';
  ctx.fillText(tag, pillX + 44, pillY + pillH / 2 + 1);
  ctx.fillStyle = 'rgba(255,255,255,0.28)';
  ctx.fillText('|', pillX + 54 + w1, pillY + pillH / 2 + 1);
  ctx.fillStyle = hud.alert ? '#FF7A5C' : '#FFD187';
  ctx.fillText(metric, pillX + 74 + w1, pillY + pillH / 2 + 1);
  ctx.restore();

  // ---- 2. Stress meter (vertical, right side inside safe zone) ----
  if (hud.stress > 0.02 && t < 15.25) {
    const mx = 862, my0 = 560, my1 = 1150;
    const hgt = (my1 - my0) * hud.stress;
    ctx.save();
    roundRectPath(ctx, mx, my0, 26, my1 - my0, 13);
    ctx.fillStyle = 'rgba(10, 16, 24, 0.66)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.14)';
    ctx.lineWidth = 1.2;
    ctx.stroke();
    const sc = hud.stress < 0.5 ? '#3AD4BE' : hud.stress < 0.8 ? '#FFB454' : '#FF4A1C';
    roundRectPath(ctx, mx, my1 - hgt, 26, hgt, 13);
    ctx.fillStyle = sc;
    ctx.globalAlpha = 0.9;
    ctx.fill();
    ctx.globalAlpha = 1.0;
    ctx.font = '700 30px "Space Grotesk", sans-serif';
    ctx.fillStyle = sc;
    ctx.textAlign = 'center';
    ctx.fillText(`${Math.round(hud.stress * 100)}%`, mx + 13, my1 + 44);
    ctx.font = '600 16px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(255,255,255,0.55)';
    ctx.fillText('STRESS', mx + 13, my0 - 18);
    ctx.restore();
  }

  // ---- 3. 3D-projected science callouts ----
  for (const c of hud.callouts) {
    if (!c.visible) continue;
    ctx.save();
    const flick = 0.85 + 0.15 * Math.sin(t * 6 + c.x);
    ctx.strokeStyle = 'rgba(140, 233, 253, 0.85)';
    ctx.fillStyle = 'rgba(8, 14, 20, 0.8)';
    ctx.lineWidth = 1.6;
    // clamp anchor inside frame
    const ax = GLM.clamp(c.x, 90, 990);
    const ay = GLM.clamp(c.y, 210, 1240);
    ctx.beginPath();
    ctx.arc(ax, ay, 7, 0, Math.PI * 2);
    ctx.stroke();
    const dirX = ax > 540 ? 1 : -1;
    ctx.beginPath();
    ctx.moveTo(ax + dirX * 9, ay);
    ctx.lineTo(ax + dirX * 56, ay - 34);
    ctx.stroke();
    ctx.font = '600 19px "IBM Plex Mono", monospace';
    const lbl = `${c.label} ${c.value}`;
    const tw = ctx.measureText(lbl).width + 26;
    let chipX = ax + dirX * 62;
    chipX = dirX > 0 ? Math.min(chipX, W - tw - 28) : Math.max(chipX, tw + 28);
    roundRectPath(ctx, dirX > 0 ? chipX : chipX - tw, ay - 60, tw, 42, 10);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = `rgba(190, 240, 250, ${flick})`;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    ctx.fillText(lbl, (dirX > 0 ? chipX : chipX - tw) + 13, ay - 39);
    ctx.restore();
  }

  // ---- 4. Kinetic two-line captions (safe zone: above y=1490) ----
  if (opts.showCaptions) {
    const cap = captions.find((c) => t >= c.t0 && t <= c.t1);
    if (cap) {
      const dtIn = (t - cap.t0) * 30.0;
      const dtOut = (cap.t1 - t) * 30.0;
      const pop = dtIn < 6.0 ? 0.90 + 0.10 * (1 - Math.pow(1 - dtIn / 6.0, 3)) : 1.0;
      const alpha = Math.min(1.0, dtIn / 3.0, dtOut / 3.0);
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.translate(W / 2, 1395);
      ctx.scale(pop, pop);
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      // line1 with keyword highlight
      ctx.font = '700 74px "Space Grotesk", sans-serif';
      ctx.shadowColor = 'rgba(0,0,0,0.7)';
      ctx.shadowBlur = 18;
      ctx.shadowOffsetY = 5;
      const hiIdx = cap.l1.indexOf(cap.hi);
      const wFull = ctx.measureText(cap.l1).width;
      let x = -wFull / 2;
      if (hiIdx >= 0) {
        const pre = cap.l1.slice(0, hiIdx);
        const mid = cap.hi;
        const post = cap.l1.slice(hiIdx + mid.length);
        ctx.textAlign = 'left';
        ctx.fillStyle = '#F4F8FB';
        ctx.fillText(pre, x, 0);
        ctx.fillStyle = cap.accent;
        ctx.fillText(mid, x + ctx.measureText(pre).width, 0);
        ctx.fillStyle = '#F4F8FB';
        ctx.fillText(post, x + ctx.measureText(pre).width + ctx.measureText(mid).width, 0);
      } else {
        ctx.fillStyle = '#F4F8FB';
        ctx.fillText(cap.l1, 0, 0);
      }
      // line2
      ctx.font = '600 42px "Space Grotesk", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = 'rgba(200, 224, 238, 0.94)';
      ctx.fillText(cap.l2, 0, 62);
      ctx.restore();
    }
  }

  // ---- 5. Progress bar + brand ----
  ctx.save();
  const p = state.frame / 1080;
  ctx.fillStyle = 'rgba(255,255,255,0.10)';
  ctx.fillRect(90, 1874, W - 180, 4);
  const grad = ctx.createLinearGradient(90, 0, W - 90, 0);
  grad.addColorStop(0, '#3AD4BE');
  grad.addColorStop(1, '#FF4A1C');
  ctx.fillStyle = grad;
  ctx.fillRect(90, 1874, (W - 180) * p, 4);
  ctx.font = '600 19px "IBM Plex Mono", monospace';
  ctx.fillStyle = 'rgba(230, 240, 246, 0.62)';
  ctx.textAlign = 'left';
  ctx.fillText('MONARCH EDITS', 90, 1848);
  ctx.textAlign = 'right';
  ctx.fillText(`${Math.round(state.hud.temp)} C`, W - 90, 1848);
  ctx.restore();
}
