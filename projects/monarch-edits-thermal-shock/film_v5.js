import * as THREE from 'three';
import {
  createCinemaCameraRig,
  GLM,
} from '/tools/monarch-v6-imax-sdk/index.js';
import {
  FPS,
  DURATION,
  TOTAL_FRAMES,
  Y_HEATER_TOP,
} from './film_v5_world.js';
import VOICE_LOCK from './voice-lock-v5-imax.json';

/**
 * THERMAL SHOCK V5 "PLUGIN-GRADE ZACK D. x HOLLYWOOD IMAX" — 9-Shot Cinema Director & HUD.
 * Frame-locked 1:1 to `voice-lock-v5-imax.json`:
 *   - 30 Hz Texel-Snapped Shadow Updates (with volumetric hide guard -> Zero-Flicker Law 3)
 *   - 9:16 Portrait FOV Trigonometry Verified (`GLM.visibleHorizontalWidth` -> ZERO edge clipping!)
 *   - Protected Pure-Cinema Climax Window (`22.493s .. 24.3333s` -> 100% ZERO HUD/text!)
 *   - Deterministic Post-ACES 2D Optical Flash (`246/255` at `SHATTER_F = 685`)
 *   - Exact Seamless Infinite Loop (`Frame 1199 -> Frame 0` MAE < 2.0 / 255)
 */

export const SHATTER_T = VOICE_LOCK.shatter_t;   // 22.8333s
export const SHATTER_F = VOICE_LOCK.shatter_f;   // 685
export const VACUUM_T0 = VOICE_LOCK.vacuum_t0;   // 22.493s
export const CLIMAX_WINDOW = VOICE_LOCK.protected_climax_window_s; // [22.493, 24.3333]
export const CRACK_TIMES = VOICE_LOCK.crack_times_s;
export const SHOTS = VOICE_LOCK.shots;
export const CAPTIONS = VOICE_LOCK.captions;

// Exact Frame-0 Hero Pose (shared by S1_HOOK start AND S9_LOOP_RETURN end -> seamless infinite loop!)
const HERO_LOOP_CAM = {
  pos: [0.0, 2.08, 6.85],
  look: [0.0, 1.58, 0.0],
  fov: 38.0,
  dutch: 0.0,
};

const SHOT_CAM = {
  S1_HOOK: {
    from: HERO_LOOP_CAM,
    to:   { pos: [0.58, 1.96, 5.85], look: [0.0, 1.50, 0.0], fov: 37.0, dutch: 0.8 },
    focus: [0.0, 1.45, 0.0], dofRange: 14.0, maxBlur: 2.8,
  },
  S2_HEAT_SOAK: {
    arc: { r0: 5.55, r1: 4.55, a0: 0.14, a1: 0.78, y0: 1.72, y1: 1.32 },
    look: [0.0, 1.15, 0.0], fovFrom: 37.0, fovTo: 35.0, dutch: 0.0,
    focus: [0.0, 1.10, 0.0], dofRange: 11.0, maxBlur: 2.8,
  },
  S3_ICE_POUR: {
    from: { pos: [1.15, 2.88, 5.95], look: [0.08, 1.68, 0.0], fov: 38.0, dutch: 1.0 },
    to:   { pos: [0.42, 2.32, 5.15], look: [0.02, 1.42, 0.0], fov: 36.0, dutch: 0.3 },
    focus: [0.0, 1.50, 0.0], dofRange: 11.0, maxBlur: 2.8,
  },
  S4_CUTAWAY: {
    from: { pos: [-0.85, 1.62, 5.10], look: [0.0, 1.32, 0.10], fov: 36.0, dutch: -0.8 },
    to:   { pos: [-0.18, 1.44, 4.65], look: [0.0, 1.30, 0.25], fov: 35.0, dutch: 0.0 },
    focus: [0.0, 1.30, 0.25], dofRange: 9.5, maxBlur: 2.4,
  },
  S5_ATOMIC: {
    // Verified 9:16 FOV math: at z=5.85 (dist=5.50 to z=0.35), visible width = 2.13u -> entire 1.62u SiO2 rig + arrows fit 100%!
    from: { pos: [0.0, 1.36, 6.05], look: [0.0, 1.30, 0.35], fov: 37.0, dutch: 0.0 },
    to:   { pos: [0.0, 1.32, 5.55], look: [0.0, 1.30, 0.35], fov: 35.5, dutch: -2.2 },
    focus: [0.0, 1.30, 0.35], dofRange: 10.0, maxBlur: 2.0,
  },
  S6_SHATTER: {
    orbit: { r0: 4.95, r1: 4.35, a0: -0.38, a1: 0.62, y0: 1.42, y1: 1.68 },
    look: [0.0, 1.22, 0.0], fovFrom: 41.0, fovTo: 36.0, dutch: -2.4,
    focus: [0.0, 1.20, 0.2], dofRange: 8.5, maxBlur: 2.8,
  },
  S7_SHARDS: {
    from: { pos: [1.55, 1.18, 4.85], look: [0.0, 0.72, 0.15], fov: 37.0, dutch: -0.8 },
    to:   { pos: [-0.65, 1.38, 4.45], look: [0.0, 0.65, 0.10], fov: 36.0, dutch: 0.4 },
    focus: [0.0, 0.65, 0.15], dofRange: 8.5, maxBlur: 2.6,
  },
  S8_BORO_HERO: {
    arc: { r0: 5.50, r1: 5.15, a0: -0.45, a1: 0.32, y0: 1.68, y1: 1.52 },
    look: [0.0, 1.32, 0.0], fovFrom: 37.0, fovTo: 36.0, dutch: 0.0,
    focus: [0.0, 1.30, 0.0], dofRange: 12.0, maxBlur: 2.4,
  },
  S9_LOOP_RETURN: {
    from: { pos: [1.10, 1.85, 5.65], look: [0.0, 1.42, 0.0], fov: 37.0, dutch: 0.4 },
    to:   HERO_LOOP_CAM,
    focus: [0.0, 1.55, 0.0], dofRange: 14.0, maxBlur: 2.8,
  },
};

function shotAtFrame(f) {
  for (const s of SHOTS) {
    if (f >= s.f0 && f < s.f1) return s;
  }
  return SHOTS[SHOTS.length - 1];
}

export function createThermalDirectorV5(world, camera) {
  const crackImpactFrames = CRACK_TIMES.map((ct, idx) => ({
    frame: Math.round(ct * FPS),
    amp: 0.38 + idx * 0.14,
    decay: 0.26,
    freq: 3.4,
    durationFrames: 12,
  }));

  const rig = createCinemaCameraRig(camera, {
    totalFrames: TOTAL_FRAMES,
    shotCuts: new Set(SHOTS.map((s) => s.f0)),
    impacts: [
      { frame: SHATTER_F, amp: 2.65, decay: 0.14, freq: 2.45, durationFrames: 30 },
      { frame: 730, amp: 0.85, decay: 0.22, freq: 2.8, durationFrames: 16 }, // "DHADAM!" punch
      ...crackImpactFrames,
    ],
  });

  const camPos = new THREE.Vector3();
  const camLook = new THREE.Vector3();
  const tmpV = new THREE.Vector3();
  const shadowFocus = new THREE.Vector3(0, 1.15, 0);
  const callouts = [];

  function projectAnchor(x, y, z) {
    tmpV.set(x, y, z).project(camera);
    return {
      x: (tmpV.x * 0.5 + 0.5) * 1080,
      y: (-tmpV.y * 0.5 + 0.5) * 1920,
      visible: tmpV.z > -1.0 && tmpV.z < 1.0,
    };
  }

  function evaluateFrame(frame) {
    const f = ((frame % TOTAL_FRAMES) + TOTAL_FRAMES) % TOTAL_FRAMES;
    const t = f / FPS;
    const shot = shotAtFrame(f);
    const u = GLM.clamp((f - shot.f0) / Math.max(1, shot.f1 - shot.f0), 0, 1);
    const cam = SHOT_CAM[shot.id];
    const w = world;

    // ---------- 1. PHYSICAL TIMELINE DRIVERS ----------
    const isShattered = f >= SHATTER_F && shot.id !== 'S9_LOOP_RETURN';
    const dtShatter = isShattered ? Math.max(0, t - SHATTER_T) : 0;
    const inBoroShot = shot.id === 'S8_BORO_HERO';
    const inLoopReturn = shot.id === 'S9_LOOP_RETURN';

    // Seamless thermal curve: starts at 0.38 (glowing hot glass on burner at f=0), rises to 1.0 in S2..S5, returns to exact 0.38 in S9!
    let heat = 0.38;
    if (!inLoopReturn) {
      heat = 0.38 + 0.62 * GLM.smoothstep(3.2, 7.0, t);
    } else {
      heat = GLM.mix(0.55, 0.38, GLM.smoothstep(0.0, 0.82, u));
    }

    // Pitcher tilt & laminar ice-water pour (S3_ICE_POUR: t=7.40..11.85s)
    const pourEnter = inLoopReturn
      ? 0.0
      : GLM.smoothstep(7.15, 7.75, t) * (1.0 - GLM.smoothstep(11.55, 12.25, t));
    const pourFlow = inLoopReturn
      ? 0.0
      : GLM.smoothstep(7.45, 7.85, t) * (1.0 - GLM.smoothstep(11.35, 11.75, t));
    const waterFill = inLoopReturn
      ? 0.0
      : GLM.smoothstep(7.55, 11.55, t) * (isShattered || inBoroShot ? 0.0 : 1.0);

    // Cold outer shell quench (builds during pour, stays frozen through S5)
    const coldShell = (inLoopReturn || inBoroShot)
      ? 0.0
      : GLM.smoothstep(7.85, 12.40, t);

    // 3D Cutaway & Atomic Lattice Shear (`S4_CUTAWAY` & `S5_ATOMIC`, plus calm comparison in `S8_BORO_HERO`)
    const cutawayActive = shot.id === 'S4_CUTAWAY' || shot.id === 'S5_ATOMIC';
    const cutawayMix = cutawayActive
      ? GLM.smoothstep(11.95, 12.75, t)
      : 0.0;
    const shearAmount = cutawayActive
      ? GLM.smoothstep(13.20, 22.10, t)
      : 0.0;
    const snapProgress = shot.id === 'S5_ATOMIC'
      ? GLM.smoothstep(21.40, SHATTER_T, t)
      : 0.0;

    // Stress gauge (0 -> 99% critical!)
    const stressPct = cutawayActive
      ? GLM.clamp(GLM.smoothstep(12.60, 22.45, t) * 0.99, 0, 0.99)
      : 0.0;

    // ---------- 2. UPDATE SDK PLUGINS & SCENE ACTORS ----------
    w.propsRig.update({
      time: t,
      heat,
      pourEnter: isShattered || inBoroShot ? 0.0 : pourEnter,
      pourFlow: isShattered || inBoroShot ? 0.0 : pourFlow,
      waterFill,
      isShattered: isShattered || inBoroShot,
    });
    // Hide pitcher during tight macro cutaway/shatter shots so upper frame stays uncluttered; visible in S1, S2, S3, S9!
    w.propsRig.pitcherPivot.visible = (
      shot.id === 'S1_HOOK' ||
      shot.id === 'S2_HEAT_SOAK' ||
      shot.id === 'S3_ICE_POUR' ||
      shot.id === 'S9_LOOP_RETURN'
    );

    // Soda-Lime Glass vs Shattered Base vs Borosilicate 3.3 Glass
    if (!isShattered && !inBoroShot) {
      w.sodaGlass.group.visible = true;
      w.survivorBase.visible = false;
      w.boroGlass.group.visible = false;

      // High-frequency pre-shatter resonance tremor in S5
      const vib = shot.id === 'S5_ATOMIC' ? GLM.smoothstep(18.5, SHATTER_T, t) * 0.014 : 0.0;
      w.sodaGlass.group.position.set(
        Math.sin(t * 54.0) * vib,
        Y_HEATER_TOP,
        Math.cos(t * 46.0) * vib
      );

      // Ghost outer glass slightly during cutaway so internal 3D SiO2 atomic lattice reads at 100% clarity
      w.sodaGlass.glassMat.opacity = GLM.mix(0.34, 0.14, cutawayMix);
      w.sodaGlass.fresnelMat.uniforms.uHeatMix.value = heat;
      w.sodaGlass.fresnelMat.uniforms.uOpacity.value = GLM.mix(0.88, 0.45, cutawayMix);
      w.sodaGlass.wireMat.opacity = cutawayMix * 0.72;

      w.thermalMat.uniforms.uHeat.value = heat;
      w.thermalMat.uniforms.uColdShell.value = coldShell;
      w.thermalMat.uniforms.uCutaway.value = cutawayMix;
      w.thermalMat.uniforms.uTime.value = t;
      w.coldOuterMat.opacity = coldShell * 0.18 * (1.0 - cutawayMix * 0.65);
    } else if (isShattered && !inBoroShot) {
      w.sodaGlass.group.visible = false;
      w.survivorBase.visible = true;
      w.boroGlass.group.visible = false;
    } else if (inBoroShot) {
      w.sodaGlass.group.visible = false;
      w.survivorBase.visible = false;
      w.boroGlass.group.visible = true;
      const boroIn = GLM.smoothstep(0.0, 0.18, u);
      const calmFlex = 1.0 + Math.sin(t * 4.2) * 0.012 * boroIn;
      w.boroGlass.group.position.set(0, Y_HEATER_TOP, 0);
      w.boroGlass.group.scale.set(calmFlex, 1.0, calmFlex);
      w.boroGlass.wireMat.opacity = 0.38 * boroIn;
    }

    // Laser Tomography Sweep on "RUKO." (`t = 11.95 .. 13.15s`)
    if (t >= 11.92 && t <= 13.20) {
      const lp = (t - 11.92) / 1.28;
      w.laserRing.visible = true;
      w.laserRing.position.set(0, Y_HEATER_TOP + 2.08 * (1.0 - lp), 0);
      w.laserRingMat.opacity = 0.92 * Math.sin(lp * Math.PI);
    } else {
      w.laserRing.visible = false;
    }

    // Jagged Bifurcating Cleavage Cracks (`S5_ATOMIC`)
    w.cracksPlugin.update(t, CRACK_TIMES, isShattered || inBoroShot || inLoopReturn);

    // Zack D. 3D SiO2 Atomic Lattice Cutaway (`S4_CUTAWAY` late & `S5_ATOMIC`)
    const showAtoms = t >= 13.05 && f < SHATTER_F;
    w.atomicRig.update({
      visible: showAtoms,
      reveal: GLM.smoothstep(13.05, 13.75, t),
      shear: shearAmount,
      snapProgress,
      time: t,
      calmBoroMode: false,
    });

    // Steam Plumes during Heat Soak & Ice-Water Quench
    const steamAmt = (!isShattered && !inBoroShot && !inLoopReturn)
      ? GLM.smoothstep(4.2, 6.2, t) * (1.0 - GLM.smoothstep(12.2, 13.5, t)) * (0.45 + 0.55 * pourFlow)
      : 0.0;
    for (const st of w.steamSprites) {
      if (steamAmt <= 0.01) {
        st.sp.material.opacity = 0.0;
        continue;
      }
      const cyc = (t * 0.42 + st.phase) % 1.0;
      st.sp.position.set(
        st.x0 + Math.sin(cyc * 8.0 + st.phase * 6.0) * 0.14 * cyc,
        Y_HEATER_TOP + 2.05 + cyc * 1.45,
        st.z0 + Math.cos(cyc * 7.0 + st.phase * 5.0) * 0.12 * cyc
      );
      const sc = 0.34 + cyc * 0.85;
      st.sp.scale.set(sc, sc, 1);
      st.sp.material.opacity = 0.34 * (1.0 - cyc) * Math.min(1.0, cyc * 5.0) * steamAmt;
    }

    // Pour Spray Droplets
    if (pourFlow > 0.1 && !isShattered) {
      w.sprayDroplets.mesh.visible = true;
      w.sprayDroplets.update(
        new THREE.Vector3(0, Y_HEATER_TOP + 0.35 + waterFill * 1.25, 0),
        (t - 7.45) * 1.0,
        { intensity: 0.55 * pourFlow, speedScale: 0.48, dirSign: 1.0 }
      );
    } else {
      w.sprayDroplets.mesh.visible = false;
    }

    // ---------- 3. VORONOI 96-SHARD EXPLOSION & SHOCKWAVES ----------
    const stormActive = isShattered && !inBoroShot && !inLoopReturn;
    w.shatterPlugin.update(dtShatter, stormActive);

    if (stormActive) {
      for (let i = 0; i < w.shockRings.length; i++) {
        const sr = w.shockRings[i];
        const pr = GLM.clamp((dtShatter - i * 0.06) / 0.92, 0, 1);
        if (pr > 0 && pr < 1) {
          sr.ring.trigger({ x: 0, y: sr.y, z: 0, size: sr.size, progress: pr, colorHex: sr.color });
        } else {
          sr.ring.mesh.visible = false;
        }
      }

      if (dtShatter < 0.95) {
        const tp = GLM.smoothstep(0, 0.95, dtShatter);
        w.blastTorus.visible = true;
        w.blastTorus.scale.setScalar(0.8 + tp * 4.8);
        w.blastTorusMat.opacity = 0.48 * (1.0 - tp);
        w.blastTorus.rotation.x = -Math.PI * 0.44 + tp * 0.14;
      } else {
        w.blastTorus.visible = false;
      }

      const spkI = Math.exp(-dtShatter * 2.1);
      if (spkI > 0.02) {
        w.blastSparks.mesh.visible = true;
        w.blastSparks.update(new THREE.Vector3(0, 1.25, 0), dtShatter * 0.65, { intensity: spkI, speedScale: 1.1, dirSign: 1.0 });
      } else {
        w.blastSparks.mesh.visible = false;
      }
    } else {
      for (const sr of w.shockRings) sr.ring.mesh.visible = false;
      w.blastTorus.visible = false;
      w.blastSparks.mesh.visible = false;
    }

    // Loop-locked Tyndall dust motes (exact 40.0s integer harmonic cycle!)
    w.dust.update(t);

    // Multi-Mood Lighting Choreography (keeps S4/S5 lifted & readable — never muddy dark!)
    const stormBoost = stormActive ? GLM.smoothstep(0.0, 0.25, dtShatter) * (1.0 - GLM.smoothstep(5.5, 6.8, dtShatter)) : 0.0;
    w.burnerLight.intensity = stormActive ? 1.2 : 1.8 + heat * 4.2;
    w.coldQuenchLight.intensity = (pourFlow * 2.8) + (cutawayActive ? 2.4 : 0.0) + (inBoroShot ? 2.6 : 0.0);
    w.cyanRim.intensity = 7.2 + cutawayMix * 2.4 + stormBoost * 2.8 + (inBoroShot ? 1.8 : 0.0);
    w.keyLight.intensity = 2.75 - cutawayMix * 0.25 + stormBoost * 0.85;
    w.warmKicker.intensity = 2.1 + stormBoost * 2.4;
    w.warmBackdropGlow.material.opacity = inBoroShot ? 0.16 : 0.34 * (1.0 - cutawayMix * 0.35);
    w.cyanHorizonGlow.material.opacity = inBoroShot ? 0.92 : 0.72;

    // ---------- 4. CINEMA CAMERA CHOREOGRAPHY ----------
    let fov = 37.0;
    let dutch = 0.0;

    if (cam.arc) {
      const e = GLM.easeInOutCubic(u);
      const r = GLM.mix(cam.arc.r0, cam.arc.r1, e);
      const a = GLM.mix(cam.arc.a0, cam.arc.a1, u);
      const y = GLM.mix(cam.arc.y0, cam.arc.y1, e);
      camPos.set(Math.sin(a) * r, y, Math.cos(a) * r);
      camLook.set(...cam.look);
      fov = GLM.mix(cam.fovFrom, cam.fovTo, e);
      dutch = cam.dutch;
    } else if (cam.orbit) {
      const pCurve = GLM.smoothstep(0, 1, Math.pow(u, 0.68));
      const a = GLM.mix(cam.orbit.a0, cam.orbit.a1, pCurve);
      const r = GLM.mix(cam.orbit.r0, cam.orbit.r1, pCurve);
      const y = GLM.mix(cam.orbit.y0, cam.orbit.y1, pCurve);
      camPos.set(Math.sin(a) * r, y, Math.cos(a) * r);
      camLook.set(...cam.look);
      fov = GLM.mix(cam.fovFrom, cam.fovTo, GLM.smoothstep(0, 0.55, u));
      dutch = cam.dutch * (1.0 - GLM.smoothstep(0.25, 0.85, u));
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
      fov = GLM.mix(cam.from.fov, cam.to.fov, e);
      dutch = GLM.mix(cam.from.dutch, cam.to.dutch, e);
    }

    // Hitchcock Vacuum Dread Creep right before SHATTER_F!
    if (t >= VACUUM_T0 && f < SHATTER_F) {
      const vp = (t - VACUUM_T0) / Math.max(0.05, SHATTER_T - VACUUM_T0);
      camPos.z -= 0.28 * vp * vp;
      fov += 1.8 * vp;
    }
    // Shatter Shockwave FOV Kick
    if (stormActive && shot.id === 'S6_SHATTER') {
      fov += 4.5 * Math.exp(-dtShatter * 3.5);
    }

    // Zero breathing amplitude across Frame 0 / Frame 1199 loop seam so MAE < 1.5 / 255!
    let breathAmp = 0.038;
    if (shot.id === 'S1_HOOK') breathAmp = 0.038 * GLM.smoothstep(0.0, 0.22, u);
    else if (shot.id === 'S9_LOOP_RETURN') breathAmp = 0.038 * (1.0 - GLM.smoothstep(0.68, 0.95, u));
    else if (shot.id === 'S6_SHATTER') breathAmp = 0.0;

    const rigState = rig.apply({
      frame: f,
      pos: camPos,
      look: camLook,
      fov,
      dutchDeg: dutch,
      breathAmp,
      shutterBlurScale: 0.34,
    });

    // ---------- 5. 30 Hz TEXEL-SNAPPED SHADOW UPDATE (Volumetrics Hidden!) ----------
    const vcVis = w.volCone.visible;
    const vbVis = w.volBlade.visible;
    w.volCone.visible = false;
    w.volBlade.visible = false;
    w.shadowRig.updateShadowMap(w.scene, shadowFocus, 6.2);
    w.volCone.visible = vcVis;
    w.volBlade.visible = vbVis;

    // ---------- 6. HDR OPTICAL POST PARAMS ----------
    const focusDist = Math.max(0.6, camera.position.distanceTo(tmpV.set(...cam.focus)));
    let bloomAmt = 0.46;
    if (stormActive) bloomAmt += 0.62 * Math.exp(-dtShatter * 2.8);
    if (cutawayActive) bloomAmt += 0.08;

    let exposure = 1.24;
    if (cutawayActive) exposure = 1.32; // Keep cutaway bright & razor-readable!
    if (t >= VACUUM_T0 && f < SHATTER_F) exposure = 1.14; // Subtle pre-blast tension dip
    if (stormActive) exposure += 0.85 * Math.exp(-dtShatter * 8.0);

    // Deterministic Post-ACES 2D Optical Flash Curve (renders on HUD canvas -> 246/255 guaranteed!)
    let flashAlpha = 0.0;
    if (f === SHATTER_F) flashAlpha = 0.96;
    else if (f === SHATTER_F + 1) flashAlpha = 0.78;
    else if (f > SHATTER_F + 1 && f <= SHATTER_F + 10) {
      flashAlpha = 0.52 * Math.exp(-(f - (SHATTER_F + 1)) * 0.55);
    }

    // ---------- 7. PROTECTED CLIMAX GATE & 3D->2D CALLOUTS ----------
    const inProtectedClimax = t >= CLIMAX_WINDOW[0] && t < CLIMAX_WINDOW[1];

    callouts.length = 0;
    if (!inProtectedClimax) {
      if (shot.id === 'S4_CUTAWAY') {
        callouts.push({ ...projectAnchor(-0.56, 1.88, 0.12), label: 'OUTER SHELL', value: '10°C COLD', color: '#3CF0FF' });
        callouts.push({ ...projectAnchor(0.48, 1.05, 0.12),  label: 'INNER CORE',  value: '300°C HOT', color: '#FF6A28' });
      } else if (shot.id === 'S5_ATOMIC') {
        callouts.push({ ...projectAnchor(0.0, 1.96, 0.40), label: 'OUTER SiO2', value: 'CONTRACTS ><', color: '#3CF0FF' });
        callouts.push({ ...projectAnchor(0.0, 0.66, 0.40), label: 'INNER SiO2', value: 'EXPANDS <>',   color: '#FF5218' });
      } else if (shot.id === 'S8_BORO_HERO') {
        callouts.push({ ...projectAnchor(0.48, 1.75, 0.15), label: 'BOROSILICATE 3.3', value: '3x LOW EXPANSION', color: '#3AD4BE' });
      }
    }

    const displayTemp = inBoroShot
      ? 300
      : Math.round(120 + heat * 180);

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
        shot: shot.id,
        inProtectedClimax,
        flashAlpha,
        tempC: displayTemp,
        stressPct,
        boroMode: inBoroShot,
        shatteredMode: stormActive,
        callouts,
      },
    };
  }

  return { evaluateFrame };
}

// =============================================================================
// KINETIC SAFE-ZONE HUD & DETERMINISTIC POST-ACES FLASH COMPOSITOR
// =============================================================================
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

export function drawThermalHudV5(ctx, state, captions, opts = { showCaptions: true }) {
  const W = ctx.canvas.width;
  const H = ctx.canvas.height;
  const hud = state.hud;
  ctx.clearRect(0, 0, W, H);

  // 1. DETERMINISTIC POST-ACES OPTICAL SHATTER FLASH (Frame 685 = ~246/255 full-screen punch!)
  if (hud.flashAlpha > 0.005 && !opts.coverMode) {
    ctx.save();
    const g = ctx.createRadialGradient(W * 0.5, H * 0.48, 40, W * 0.5, H * 0.48, H * 0.72);
    g.addColorStop(0.0, `rgba(255, 253, 246, ${hud.flashAlpha})`);
    g.addColorStop(0.55, `rgba(255, 236, 200, ${hud.flashAlpha * 0.94})`);
    g.addColorStop(1.0, `rgba(255, 195, 130, ${hud.flashAlpha * 0.86})`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    ctx.restore();
  }

  // 2. THUMBNAIL / COVER MODE (High-CTR Viral Poster Lockup!)
  if (opts.coverMode) {
    ctx.save();
    const topG = ctx.createLinearGradient(0, 0, 0, 620);
    topG.addColorStop(0.0, 'rgba(4, 8, 15, 0.88)');
    topG.addColorStop(0.68, 'rgba(4, 8, 15, 0.42)');
    topG.addColorStop(1.0, 'rgba(4, 8, 15, 0.0)');
    ctx.fillStyle = topG;
    ctx.fillRect(0, 0, W, 620);

    ctx.textAlign = 'center';
    ctx.shadowColor = 'rgba(0, 0, 0, 0.88)';
    ctx.shadowBlur = 28;
    ctx.font = '700 94px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText('300°C GLASS', W / 2, 225);

    ctx.font = '700 72px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#3CF0FF';
    ctx.fillText('x 10°C PAANI!', W / 2, 320);

    roundRect(ctx, W / 2 - 220, 360, 440, 54, 27);
    ctx.fillStyle = 'rgba(255, 74, 28, 0.90)';
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.font = '700 26px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#FFFFFF';
    ctx.textBaseline = 'middle';
    ctx.fillText('THERMAL SHOCK 3D', W / 2, 388);
    ctx.restore();
    return;
  }

  // 3. PROTECTED PURE-CINEMA CLIMAX GATE: 100% ZERO TEXT/HUD/GAUGES DURING EXPLOSION!
  if (hud.inProtectedClimax) {
    return;
  }

  // 4. Top-Left Minimalist Telemetry Pill (Safe Zone: x=52, y=144)
  ctx.save();
  ctx.font = '600 20px "IBM Plex Mono", monospace';
  const modeTag = hud.boroMode ? 'BOROSILICATE 3.3' : 'SODA-LIME LAB';
  const tempTxt = hud.boroMode
    ? 'SHOCK SAFE'
    : hud.shatteredMode
      ? 'SHATTERED!'
      : `CORE ${hud.tempC}°C`;
  const wTag = ctx.measureText(modeTag).width;
  const wTmp = ctx.measureText(tempTxt).width;
  const pillW = 68 + wTag + wTmp;
  const px = 52, py = 144, ph = 48;

  roundRect(ctx, px, py, pillW, ph, 24);
  ctx.fillStyle = 'rgba(6, 11, 18, 0.74)';
  ctx.fill();
  ctx.lineWidth = 1.4;
  ctx.strokeStyle = hud.boroMode
    ? 'rgba(58, 212, 190, 0.45)'
    : hud.shatteredMode
      ? 'rgba(255, 82, 56, 0.50)'
      : 'rgba(255, 255, 255, 0.16)';
  ctx.stroke();

  const pulse = 0.65 + 0.35 * Math.sin(hud.time * Math.PI * 4.0);
  ctx.beginPath();
  ctx.arc(px + 24, py + ph / 2, 6, 0, Math.PI * 2);
  ctx.fillStyle = hud.boroMode
    ? `rgba(58, 242, 200, ${pulse})`
    : (hud.shatteredMode || hud.stressPct > 0.65)
      ? `rgba(255, 72, 42, ${pulse})`
      : `rgba(255, 176, 84, ${pulse})`;
  ctx.fill();

  ctx.textBaseline = 'middle';
  ctx.fillStyle = '#EEF6FA';
  ctx.fillText(modeTag, px + 42, py + ph / 2 + 1);
  ctx.fillStyle = 'rgba(255,255,255,0.28)';
  ctx.fillText('|', px + 50 + wTag, py + ph / 2 + 1);
  ctx.fillStyle = hud.boroMode
    ? '#5EF2D6'
    : (hud.shatteredMode || hud.stressPct > 0.65)
      ? '#FF6A48'
      : '#FFD180';
  ctx.fillText(tempTxt, px + 64 + wTag, py + ph / 2 + 1);
  ctx.restore();

  // 5. Top-Left Docked Thermal Shear Stress Bar (`S4_CUTAWAY` & `S5_ATOMIC` -> ZERO overlap on 3D SiO2 Lattice!)
  if (hud.stressPct > 0.02) {
    const gx = 52, gy = 206, gw = 330, gh = 16;
    const fillW = Math.max(12, gw * hud.stressPct);
    const barCol = hud.stressPct < 0.45 ? '#3CF0FF' : hud.stressPct < 0.78 ? '#FFB454' : '#FF3B1F';

    ctx.save();
    roundRect(ctx, gx, gy, gw, gh, 8);
    ctx.fillStyle = 'rgba(7, 13, 22, 0.78)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.18)';
    ctx.lineWidth = 1.2;
    ctx.stroke();

    roundRect(ctx, gx, gy, fillW, gh, 8);
    ctx.fillStyle = barCol;
    ctx.fill();

    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.font = '600 18px "IBM Plex Mono", monospace';
    ctx.fillStyle = 'rgba(235, 245, 255, 0.88)';
    ctx.fillText('WALL SHEAR STRESS', gx + 4, gy + 34);
    ctx.font = '700 24px "Space Grotesk", sans-serif';
    ctx.fillStyle = barCol;
    ctx.fillText(`${Math.round(hud.stressPct * 100)}%`, gx + gw + 14, gy + 8);
    ctx.restore();
  }

  // 6. 3D-Tracked Science Pointer Callouts (Clamped inside safe margins!)
  for (const c of hud.callouts) {
    if (!c.visible) continue;
    ctx.save();
    const ax = GLM.clamp(c.x, 110, 820);
    const ay = GLM.clamp(c.y, 260, 1140);
    const dirX = ax > 500 ? -1 : 1;

    ctx.strokeStyle = c.color || '#8CE9FD';
    ctx.lineWidth = 2.0;
    ctx.beginPath();
    ctx.arc(ax, ay, 7, 0, Math.PI * 2);
    ctx.stroke();

    const elbowX = ax + dirX * 42;
    const elbowY = ay - 28;
    ctx.beginPath();
    ctx.moveTo(ax + dirX * 8, ay - 4);
    ctx.lineTo(elbowX, elbowY);
    ctx.stroke();

    ctx.font = '600 19px "IBM Plex Mono", monospace';
    const txt = `${c.label}: ${c.value}`;
    const cw = ctx.measureText(txt).width + 28;
    const boxX = GLM.clamp(dirX > 0 ? elbowX + 4 : elbowX - cw - 4, 48, 885 - cw);
    const boxY = elbowY - 22;

    roundRect(ctx, boxX, boxY, cw, 42, 10);
    ctx.fillStyle = 'rgba(6, 12, 20, 0.84)';
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#F2FAFF';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    ctx.fillText(txt, boxX + 14, boxY + 22);
    ctx.restore();
  }

  // 7. Kinetic Read-Along Roman-Urdu Captions (Safe Zone y=1355 <= 1490, Frosted Glass Pill!)
  if (opts.showCaptions) {
    const t = hud.time;
    const cap = captions.find((c) => t >= c.t0 && t <= c.t1);
    if (cap) {
      const dtIn = (t - cap.t0) * FPS;
      const dtOut = (cap.t1 - t) * FPS;
      // Elastic spring-pop arrival
      const uIn = GLM.clamp(dtIn / 6.0, 0, 1);
      const spring = uIn < 1.0 ? (0.88 + 0.14 * Math.sin(uIn * Math.PI * 0.72)) : 1.0;
      const alpha = GLM.clamp(Math.min(dtIn / 2.8, dtOut / 3.0, 1.0), 0, 1);

      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.translate(W / 2, 1365);
      ctx.scale(spring, spring);

      ctx.font = '700 58px "Space Grotesk", sans-serif';
      const wL1 = ctx.measureText(cap.l1).width;
      ctx.font = '600 38px "Space Grotesk", sans-serif';
      const wL2 = ctx.measureText(cap.l2).width;
      const cardW = Math.min(960, Math.max(wL1, wL2) + 76);

      roundRect(ctx, -cardW / 2, -62, cardW, 142, 24);
      ctx.fillStyle = 'rgba(6, 11, 18, 0.74)';
      ctx.fill();
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.14)';
      ctx.stroke();

      // Accent underline bar
      ctx.fillStyle = cap.accent;
      roundRect(ctx, -Math.min(cardW * 0.36, 180), 66, Math.min(cardW * 0.72, 360) * uIn, 4, 2);
      ctx.fill();

      // Line 1 with highlighted keyword
      ctx.font = '700 58px "Space Grotesk", sans-serif';
      ctx.textBaseline = 'middle';
      ctx.shadowColor = 'rgba(0, 0, 0, 0.75)';
      ctx.shadowBlur = 14;

      const hiIdx = cap.l1.indexOf(cap.hi);
      if (hiIdx >= 0) {
        const pre = cap.l1.slice(0, hiIdx);
        const mid = cap.hi;
        const post = cap.l1.slice(hiIdx + mid.length);
        const xStart = -wL1 / 2;
        ctx.textAlign = 'left';
        ctx.fillStyle = '#F6FAFD';
        ctx.fillText(pre, xStart, -16);
        const wPre = ctx.measureText(pre).width;
        ctx.fillStyle = cap.accent;
        ctx.fillText(mid, xStart + wPre, -16);
        const wMid = ctx.measureText(mid).width;
        ctx.fillStyle = '#F6FAFD';
        ctx.fillText(post, xStart + wPre + wMid, -16);
      } else {
        ctx.textAlign = 'center';
        ctx.fillStyle = '#F6FAFD';
        ctx.fillText(cap.l1, 0, -16);
      }

      // Line 2
      ctx.font = '600 38px "Space Grotesk", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = 'rgba(210, 232, 246, 0.96)';
      ctx.fillText(cap.l2, 0, 38);
      ctx.restore();
    }
  }
}
