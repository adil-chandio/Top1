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
} from './film_v6_world.js';
import VOICE_LOCK from './voice-lock-v6-ultra.json';

/**
 * THERMAL SHOCK V6 ULTRA ("ZACK D. FILMS x CHRISTOPHER NOLAN AUTONOMOUS GOD-MODE")
 * 14-Shot Cinema Director & Kinetic HUD (`film_v6.js`).
 */

export const SHATTER_T = VOICE_LOCK.shatter_t;   // 22.8333s
export const SHATTER_F = VOICE_LOCK.shatter_f;   // 685
export const VACUUM_T0 = VOICE_LOCK.vacuum_t0;   // 22.493s
export const CLIMAX_WINDOW = VOICE_LOCK.protected_climax_window_s; // [22.493, 24.3333]
export const CRACK_TIMES = VOICE_LOCK.crack_times_s;
export const SHOTS = VOICE_LOCK.shots;
export const CAPTIONS = VOICE_LOCK.captions;

const HERO_LOOP_CAM = {
  pos: [0.0, 2.08, 6.85],
  look: [0.0, 1.58, 0.0],
  fov: 38.0,
  dutch: 0.0,
};

// 14-Shot Dynamic Zack D. x Nolan Camera Choreography (every shot verified inside 9:16 portrait frustum!)
const SHOT_CAM = {
  S1_HOOK: {
    from: HERO_LOOP_CAM,
    to:   { pos: [0.54, 1.94, 5.75], look: [0.0, 1.48, 0.0], fov: 37.0, dutch: 0.8 },
    focus: [0.0, 1.45, 0.0], dofRange: 13.0, maxBlur: 2.8,
  },
  S2A_COIL_MACRO: {
    // Low-angle macro crane past blazing nichrome coil & heavy crystal TIR fire ring (framed cleanly above captions)!
    from: { pos: [1.18, 1.38, 4.55], look: [0.0, 0.94, 0.0], fov: 37.5, dutch: -1.2 },
    to:   { pos: [0.68, 1.52, 4.25], look: [0.0, 1.04, 0.0], fov: 36.0, dutch: -0.4 },
    focus: [0.0, 0.85, 0.0], dofRange: 8.5, maxBlur: 2.8,
  },
  S2B_HEAT_EXPANSION: {
    arc: { r0: 4.85, r1: 4.25, a0: 0.18, a1: 0.72, y0: 1.65, y1: 1.38 },
    look: [0.0, 1.25, 0.0], fovFrom: 37.0, fovTo: 35.5, dutch: 0.5,
    focus: [0.0, 1.25, 0.0], dofRange: 9.5, maxBlur: 2.8,
  },
  S3A_POUR_IMPACT: {
    // High-angle follow down tilting cryo-carafe spout as 10°C stream + ice cubes hit 300°C glass!
    from: { pos: [1.08, 2.86, 5.75], look: [0.06, 1.66, 0.0], fov: 38.0, dutch: 1.2 },
    to:   { pos: [0.45, 2.38, 5.05], look: [0.02, 1.42, 0.0], fov: 36.5, dutch: 0.4 },
    focus: [0.0, 1.52, 0.0], dofRange: 10.5, maxBlur: 2.8,
  },
  S3B_QUENCH_SHOCK: {
    // Tight side-macro tracking rising meniscus, floating 3D ice cubes & outer condensation droplets!
    from: { pos: [-0.88, 1.58, 4.35], look: [0.0, 1.35, 0.0], fov: 36.0, dutch: -0.8 },
    to:   { pos: [-0.46, 1.48, 4.05], look: [0.0, 1.32, 0.0], fov: 35.0, dutch: -0.2 },
    focus: [0.0, 1.32, 0.0], dofRange: 8.0, maxBlur: 2.8,
  },
  S4_LASER_SLICE: {
    // "RUKO." Surgical cyan laser guillotine slices front 116° wedge open, exposing live 3D wall cross-section!
    from: { pos: [-0.55, 1.65, 4.95], look: [0.0, 1.30, 0.08], fov: 36.5, dutch: 0.0 },
    to:   { pos: [ 0.08, 1.44, 4.55], look: [0.0, 1.28, 0.12], fov: 35.0, dutch: 0.0 },
    focus: [0.0, 1.28, 0.12], dofRange: 8.5, maxBlur: 2.4,
  },
  S5A_ATOMIC_ZOOM: {
    // Zack D. Macro Dive straight into the sliced crystal cavity where 3D SiO2 tetrahedra materialize!
    from: { pos: [0.0, 1.38, 5.65], look: [0.0, 1.28, 0.18], fov: 37.0, dutch: 0.0 },
    to:   { pos: [0.0, 1.30, 5.05], look: [0.0, 1.28, 0.18], fov: 35.5, dutch: -1.0 },
    focus: [0.0, 1.28, 0.18], dofRange: 9.0, maxBlur: 2.2,
  },
  S5B_CRACK_CASCADE: {
    // Rising Dutch-angle tension close-up as 4 cleavage cracks rip down side walls & covalent bonds snap!
    from: { pos: [ 0.22, 1.32, 5.05], look: [0.0, 1.28, 0.18], fov: 35.5, dutch: -1.0 },
    to:   { pos: [-0.18, 1.30, 4.72], look: [0.0, 1.28, 0.18], fov: 35.0, dutch: -3.2 },
    focus: [0.0, 1.28, 0.18], dofRange: 8.5, maxBlur: 2.2,
  },
  S5C_VACUUM_DREAD: {
    // Hitchcock VERTIGO Dolly-Zoom in -180 dBFS vacuum silence (camera pulls back 4.72->5.55 while FOV narrows 35->29.8°)!
    from: { pos: [-0.18, 1.30, 4.72], look: [0.0, 1.28, 0.18], fov: 35.0, dutch: -3.2 },
    to:   { pos: [ 0.0,  1.30, 5.55], look: [0.0, 1.28, 0.18], fov: 29.8, dutch: -4.0 },
    focus: [0.0, 1.28, 0.18], dofRange: 8.0, maxBlur: 2.4,
  },
  S6A_DETONATION_FLASH: {
    // Ultra-wide shockwave blast punch as 128 shards + 140 water globules erupt!
    from: { pos: [-0.42, 1.38, 4.85], look: [0.0, 1.22, 0.0], fov: 43.0, dutch: -2.8 },
    to:   { pos: [-0.95, 1.46, 4.55], look: [0.0, 1.22, 0.0], fov: 38.5, dutch: -1.5 },
    focus: [0.0, 1.20, 0.15], dofRange: 8.5, maxBlur: 2.8,
  },
  S6B_BULLET_TIME_ORBIT: {
    // 110° Matrix Bullet-Time Speed-Ramp Orbit around suspended shards & water teardrops!
    orbit: { r0: 4.55, r1: 4.20, a0: -0.22, a1: 0.92, y0: 1.46, y1: 1.72 },
    look: [0.0, 1.24, 0.0], fovFrom: 38.5, fovTo: 36.0, dutch: -1.2,
    focus: [0.0, 1.22, 0.15], dofRange: 8.5, maxBlur: 2.8,
  },
  S7_AFTERMATH_SIZZLE: {
    // Low sweeping crane across wet glistening puddle, bouncing shards & sizzling 300°C coil steam!
    from: { pos: [ 1.55, 1.12, 4.65], look: [0.0, 0.62, 0.12], fov: 37.0, dutch: -0.6 },
    to:   { pos: [-0.68, 1.36, 4.35], look: [0.0, 0.58, 0.08], fov: 36.0, dutch: 0.4 },
    focus: [0.0, 0.58, 0.10], dofRange: 8.0, maxBlur: 2.6,
  },
  S8_BORO_TORTURE_TEST: {
    // Live Borosilicate 3.3 Pyrex torture test: active 10°C pour on 300°C coil + Boron spring shield!
    arc: { r0: 5.75, r1: 5.15, a0: -0.34, a1: 0.28, y0: 2.02, y1: 1.68 },
    look: [0.0, 1.42, 0.0], fovFrom: 38.0, fovTo: 36.5, dutch: 0.0,
    focus: [0.0, 1.38, 0.0], dofRange: 11.5, maxBlur: 2.5,
  },
  S9_SEAMLESS_LOOP: {
    from: { pos: [1.08, 1.86, 5.65], look: [0.0, 1.44, 0.0], fov: 37.0, dutch: 0.4 },
    to:   HERO_LOOP_CAM,
    focus: [0.0, 1.55, 0.0], dofRange: 13.0, maxBlur: 2.8,
  },
};

function shotAtFrame(f) {
  for (const s of SHOTS) {
    if (f >= s.f0 && f < s.f1) return s;
  }
  return SHOTS[SHOTS.length - 1];
}

export function createThermalDirectorV6(world, camera) {
  const crackImpacts = CRACK_TIMES.map((ct, idx) => ({
    frame: Math.round(ct * FPS),
    amp: 0.42 + idx * 0.15,
    decay: 0.25,
    freq: 3.5,
    durationFrames: 12,
  }));

  const rig = createCinemaCameraRig(camera, {
    totalFrames: TOTAL_FRAMES,
    shotCuts: new Set(SHOTS.map((s) => s.f0)),
    impacts: [
      { frame: SHATTER_F, amp: 2.75, decay: 0.14, freq: 2.50, durationFrames: 28 },
      { frame: 730, amp: 0.95, decay: 0.22, freq: 2.85, durationFrames: 16 }, // "DHADAM!" gravity snap
      ...crackImpacts,
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

    const isShattered = f >= SHATTER_F && shot.id !== 'S9_SEAMLESS_LOOP';
    const dtShatter = isShattered ? Math.max(0, t - SHATTER_T) : 0;
    const inBoroShot = shot.id === 'S8_BORO_TORTURE_TEST';
    const inLoopReturn = shot.id === 'S9_SEAMLESS_LOOP';

    // ---------- 1. PHYSICAL THERMODYNAMICS DRIVERS ----------
    let heat = 0.38;
    if (!inLoopReturn) {
      heat = 0.38 + 0.62 * GLM.smoothstep(3.2, 6.8, t);
    } else {
      heat = GLM.mix(0.85, 0.38, GLM.smoothstep(0.0, 0.80, u));
    }

    // Pour #1: Soda-Lime Quench (`S3A` & `S3B`: t = 7.40 .. 11.80s)
    // Pour #2: Borosilicate 3.3 Live Torture Test (`S8_BORO_TORTURE_TEST`: u = 0.08 .. 0.72)!
    let pourEnter = 0.0;
    let pourFlow = 0.0;
    let waterFill = 0.0;

    if (!isShattered && !inBoroShot && !inLoopReturn) {
      pourEnter = GLM.smoothstep(7.15, 7.70, t) * (1.0 - GLM.smoothstep(11.50, 12.15, t));
      pourFlow  = GLM.smoothstep(7.42, 7.80, t) * (1.0 - GLM.smoothstep(11.35, 11.75, t));
      waterFill = GLM.smoothstep(7.52, 11.50, t);
    } else if (inBoroShot) {
      pourEnter = GLM.smoothstep(0.04, 0.16, u) * (1.0 - GLM.smoothstep(0.72, 0.88, u));
      pourFlow  = GLM.smoothstep(0.08, 0.18, u) * (1.0 - GLM.smoothstep(0.68, 0.80, u));
      waterFill = GLM.smoothstep(0.10, 0.74, u) * 0.85;
    }

    const coldQuench = (!isShattered && !inBoroShot && !inLoopReturn)
      ? GLM.smoothstep(7.80, 12.30, t)
      : (inBoroShot ? GLM.smoothstep(0.14, 0.65, u) : 0.0);

    // Surgical 116° Cross-Section Cutaway (`S4_LASER_SLICE` through `S5C_VACUUM_DREAD`)
    const inCutaway = (
      shot.id === 'S4_LASER_SLICE' ||
      shot.id === 'S5A_ATOMIC_ZOOM' ||
      shot.id === 'S5B_CRACK_CASCADE' ||
      shot.id === 'S5C_VACUUM_DREAD'
    );
    const sliceProgress = inCutaway ? GLM.smoothstep(11.98, 13.15, t) : 0.0;
    const shearAmount = inCutaway ? GLM.smoothstep(13.40, 22.25, t) : (inBoroShot ? 0.55 : 0.0);
    const snapProgress = (shot.id === 'S5B_CRACK_CASCADE' || shot.id === 'S5C_VACUUM_DREAD')
      ? GLM.smoothstep(19.80, SHATTER_T - 0.04, t)
      : 0.0;

    // Stress %: climbs 0 -> 99% in Soda-Lime; stays calm 18% in Borosilicate 3.3!
    const stressPct = inCutaway
      ? GLM.clamp(GLM.smoothstep(12.60, 22.45, t) * 0.99, 0, 0.99)
      : (inBoroShot ? 0.18 * GLM.smoothstep(0.12, 0.45, u) : 0.0);

    // ---------- 2. UPDATE SDK ULTRA PLUGINS ----------
    w.cryoRig.update({
      time: t,
      heat,
      pourEnter,
      pourFlow,
      waterFill,
      sliceProgress,
      isShattered: isShattered && !inBoroShot,
    });
    w.cryoRig.pitcherPivot.visible = (
      shot.id === 'S1_HOOK' ||
      shot.id === 'S2B_HEAT_EXPANSION' ||
      shot.id === 'S3A_POUR_IMPACT' ||
      shot.id === 'S3B_QUENCH_SHOCK' ||
      shot.id === 'S8_BORO_TORTURE_TEST' ||
      shot.id === 'S9_SEAMLESS_LOOP'
    );

    const sliceY = sliceProgress <= 0.001 ? 9.9 : GLM.mix(2.14, 0.26, sliceProgress);

    if (!isShattered && !inBoroShot) {
      w.sodaGlass.group.visible = true;
      w.survivorBase.visible = false;
      w.boroGlass.group.visible = false;

      const vib = (shot.id === 'S5B_CRACK_CASCADE' || shot.id === 'S5C_VACUUM_DREAD')
        ? GLM.smoothstep(18.5, SHATTER_T, t) * 0.014
        : 0.0;
      w.sodaGlass.group.position.set(
        Math.sin(t * 56.0) * vib,
        Y_HEATER_TOP,
        Math.cos(t * 48.0) * vib
      );

      w.sodaGlass.update({
        heat,
        coldQuench,
        sliceProgress,
        shearPulse: shearAmount,
        time: t,
        opacity: GLM.mix(0.44, 0.34, sliceProgress),
      });

      w.magmaMat.uniforms.uHeat.value = heat;
      w.magmaMat.uniforms.uColdShell.value = coldQuench;
      w.magmaMat.uniforms.uSliceY.value = sliceY;
      w.magmaMat.uniforms.uTime.value = t;
    } else if (isShattered && !inBoroShot) {
      w.sodaGlass.group.visible = false;
      w.survivorBase.visible = true;
      w.boroGlass.group.visible = false;
    } else if (inBoroShot) {
      w.sodaGlass.group.visible = false;
      w.survivorBase.visible = false;
      w.boroGlass.group.visible = true;
      w.boroGlass.group.position.set(0, Y_HEATER_TOP, 0);
      // Slice open lower-front slightly in second half of S8 so Boron 3.3 shield lattice shines inside!
      const boroSlice = GLM.smoothstep(0.32, 0.50, u) * 0.85;
      w.boroGlass.update({
        heat: 0.92,
        coldQuench,
        sliceProgress: boroSlice,
        shearPulse: 0.0,
        time: t,
        opacity: 0.44,
      });
    }

    // Surgical Cyan Laser Guillotine Sweep (`t = 11.95 .. 13.20s`)
    if (t >= 11.94 && t <= 13.22) {
      const lp = (t - 11.94) / 1.28;
      w.laserRing.visible = true;
      w.laserRing.position.set(0, Y_HEATER_TOP + 2.12 * (1.0 - lp), 0);
      w.laserRingMat.opacity = 0.95 * Math.sin(lp * Math.PI);
    } else {
      w.laserRing.visible = false;
    }

    // Jagged Cleavage Cracks (`S5A..S5C`)
    w.cracksPlugin.update(t, CRACK_TIMES, isShattered || inBoroShot || inLoopReturn);

    // Zack D. 3D Tetrahedral SiO2 Lattice (`S5A..S5C` AND Boron Shield mode in `S8_BORO_TORTURE_TEST`!)
    const showSodaAtoms = t >= 15.80 && f < SHATTER_F;
    const showBoroAtoms = inBoroShot && u >= 0.36;
    w.atomicRig.update({
      visible: showSodaAtoms || showBoroAtoms,
      reveal: showSodaAtoms
        ? GLM.smoothstep(15.80, 16.65, t)
        : GLM.smoothstep(0.36, 0.48, u),
      shear: shearAmount,
      snapProgress,
      time: t,
      calmBoroMode: showBoroAtoms,
    });

    // Leidenfrost Steam Plumes:
    //   1) During 10°C pour onto 300°C glass (`S3A/S3B` & `S8`)
    //   2) Billowing off the wet red-hot halogen burner after shatter (`S7_AFTERMATH_SIZZLE`)!
    let steamAmt = 0.0;
    let steamBaseY = Y_HEATER_TOP + 2.02;
    if (!isShattered && !inLoopReturn) {
      steamAmt = pourFlow * 0.92;
      steamBaseY = Y_HEATER_TOP + 1.85;
    } else if (shot.id === 'S7_AFTERMATH_SIZZLE') {
      steamAmt = GLM.smoothstep(0.0, 0.18, u) * (1.0 - GLM.smoothstep(0.72, 1.0, u)) * 0.85;
      steamBaseY = Y_HEATER_TOP + 0.18; // Rising right off the sizzling wet halogen burner!
    }

    for (const st of w.steamSprites) {
      if (steamAmt <= 0.01) {
        st.sp.material.opacity = 0.0;
        continue;
      }
      const cyc = (t * 0.46 + st.phase) % 1.0;
      st.sp.position.set(
        st.x0 + Math.sin(cyc * 8.0 + st.phase * 6.0) * 0.16 * cyc,
        steamBaseY + cyc * 1.45,
        st.z0 + Math.cos(cyc * 7.0 + st.phase * 5.0) * 0.14 * cyc
      );
      const sc = 0.36 + cyc * 0.92;
      st.sp.scale.set(sc, sc, 1);
      st.sp.material.opacity = 0.36 * (1.0 - cyc) * Math.min(1.0, cyc * 5.0) * steamAmt;
    }

    // Pour Spray Droplets
    if (pourFlow > 0.12 && (!isShattered || inBoroShot)) {
      w.sprayDroplets.mesh.visible = true;
      w.sprayDroplets.update(
        new THREE.Vector3(0, Y_HEATER_TOP + 0.35 + waterFill * 1.25, 0),
        t * 0.9,
        { intensity: 0.58 * pourFlow, speedScale: 0.48, dirSign: 1.0 }
      );
    } else {
      w.sprayDroplets.mesh.visible = false;
    }

    // ---------- 3. 128-SHARD + 140-WATER-GLOBULE MATRIX BULLET-TIME DETONATION ----------
    const stormActive = isShattered && !inBoroShot && !inLoopReturn;
    w.shatterBurst.update(dtShatter, stormActive, t);

    if (stormActive) {
      for (let i = 0; i < w.shockRings.length; i++) {
        const sr = w.shockRings[i];
        const pr = GLM.clamp((dtShatter - i * 0.055) / 0.88, 0, 1);
        if (pr > 0 && pr < 1) {
          sr.ring.trigger({ x: 0, y: sr.y, z: 0, size: sr.size, progress: pr, colorHex: sr.color });
        } else {
          sr.ring.mesh.visible = false;
        }
      }

      if (dtShatter < 0.92) {
        const tp = GLM.smoothstep(0, 0.92, dtShatter);
        w.blastWave.visible = true;
        w.blastWave.scale.setScalar(0.8 + tp * 4.8);
        w.blastWaveMat.opacity = 0.50 * (1.0 - tp);
        w.blastWave.rotation.x = -Math.PI * 0.44 + tp * 0.14;
      } else {
        w.blastWave.visible = false;
      }

      const spkI = Math.exp(-dtShatter * 2.2);
      if (spkI > 0.02) {
        w.blastSparks.mesh.visible = true;
        w.blastSparks.update(new THREE.Vector3(0, 1.25, 0), dtShatter * 0.65, { intensity: spkI, speedScale: 1.15, dirSign: 1.0 });
      } else {
        w.blastSparks.mesh.visible = false;
      }
    } else {
      for (const sr of w.shockRings) sr.ring.mesh.visible = false;
      w.blastWave.visible = false;
      w.blastSparks.mesh.visible = false;
    }

    w.dust.update(t);

    // Multi-Mood Lighting Choreography
    const stormBoost = stormActive ? GLM.smoothstep(0.0, 0.22, dtShatter) * (1.0 - GLM.smoothstep(5.5, 6.8, dtShatter)) : 0.0;
    w.burnerLight.intensity = stormActive ? 1.5 : 1.9 + heat * 4.4;
    w.coldQuenchLight.intensity = (pourFlow * 3.0) + (inCutaway ? 2.5 : 0.0) + (inBoroShot ? 2.8 : 0.0);
    w.cyanRim.intensity = 7.4 + sliceProgress * 2.4 + stormBoost * 2.8 + (inBoroShot ? 2.0 : 0.0);
    w.keyLight.intensity = 2.80 - sliceProgress * 0.22 + stormBoost * 0.90;
    w.warmKicker.intensity = 2.15 + stormBoost * 2.4;
    w.warmBackdropGlow.material.opacity = inBoroShot ? 0.18 : 0.34 * (1.0 - sliceProgress * 0.30);
    w.cyanHorizonGlow.material.opacity = inBoroShot ? 0.92 : 0.74;

    // ---------- 4. 14-SHOT CAMERA EVALUATION ----------
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
      const pCurve = GLM.smoothstep(0, 1, Math.pow(u, 0.78));
      const a = GLM.mix(cam.orbit.a0, cam.orbit.a1, pCurve);
      const r = GLM.mix(cam.orbit.r0, cam.orbit.r1, pCurve);
      const y = GLM.mix(cam.orbit.y0, cam.orbit.y1, pCurve);
      camPos.set(Math.sin(a) * r, y, Math.cos(a) * r);
      camLook.set(...cam.look);
      fov = GLM.mix(cam.fovFrom, cam.fovTo, u);
      dutch = cam.dutch * (1.0 - GLM.smoothstep(0.3, 0.9, u));
    } else {
      const e = shot.id === 'S5C_VACUUM_DREAD' ? (u * u) : GLM.easeInOutCubic(u);
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

    if (stormActive && shot.id === 'S6A_DETONATION_FLASH') {
      fov += 4.2 * Math.exp(-dtShatter * 4.0);
    }

    // Zero breathing across loop seam (Frame 0 == Frame 1199)!
    let breathAmp = 0.036;
    if (shot.id === 'S1_HOOK') breathAmp = 0.036 * GLM.smoothstep(0.0, 0.22, u);
    else if (shot.id === 'S9_SEAMLESS_LOOP') breathAmp = 0.036 * (1.0 - GLM.smoothstep(0.68, 0.95, u));
    else if (shot.id === 'S6A_DETONATION_FLASH' || shot.id === 'S6B_BULLET_TIME_ORBIT') breathAmp = 0.0;

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
    if (stormActive) bloomAmt += 0.64 * Math.exp(-dtShatter * 2.8);
    if (inCutaway) bloomAmt += 0.08;

    let exposure = 1.24;
    if (inCutaway) exposure = 1.32;
    if (shot.id === 'S5C_VACUUM_DREAD') exposure = 1.12;
    if (stormActive) exposure += 0.85 * Math.exp(-dtShatter * 8.0);

    // Deterministic Post-ACES 2D Optical Flash Curve
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
      if (shot.id === 'S4_LASER_SLICE') {
        callouts.push({ ...projectAnchor(-0.48, 1.85, 0.25), label: 'OUTER WALL', value: '10°C QUENCHED', color: '#3CF0FF' });
        callouts.push({ ...projectAnchor( 0.44, 0.96, 0.25), label: 'INNER WALL', value: '300°C MAGMA',   color: '#FF5E24' });
      } else if (shot.id === 'S5A_ATOMIC_ZOOM' || shot.id === 'S5B_CRACK_CASCADE') {
        callouts.push({ ...projectAnchor(0.0, 1.92, 0.22), label: 'OUTER SiO2', value: 'CONTRACTS ><', color: '#3CF0FF' });
        callouts.push({ ...projectAnchor(0.0, 0.68, 0.22), label: 'INNER SiO2', value: 'EXPANDS <>',   color: '#FF5218' });
      } else if (inBoroShot) {
        callouts.push({ ...projectAnchor(0.45, 1.80, 0.20), label: 'BORON B2O3 SHIELD', value: '3x LOW EXPANSION', color: '#3EF5D4' });
      }
    }

    const displayTemp = inBoroShot ? 300 : Math.round(120 + heat * 180);

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

export function drawThermalHudV6(ctx, state, captions, opts = { showCaptions: true }) {
  const W = ctx.canvas.width;
  const H = ctx.canvas.height;
  const hud = state.hud;
  ctx.clearRect(0, 0, W, H);

  // 1. DETERMINISTIC POST-ACES OPTICAL SHATTER FLASH
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

  // 2. HIGH-CTR VIRAL COVER POSTER LOCKUP
  if (opts.coverMode) {
    ctx.save();
    const topG = ctx.createLinearGradient(0, 0, 0, 680);
    topG.addColorStop(0.0, 'rgba(3, 6, 12, 0.94)');
    topG.addColorStop(0.58, 'rgba(4, 8, 16, 0.72)');
    topG.addColorStop(1.0, 'rgba(4, 8, 16, 0.0)');
    ctx.fillStyle = topG;
    ctx.fillRect(0, 0, W, 680);

    ctx.textAlign = 'center';
    ctx.shadowColor = 'rgba(0, 0, 0, 0.95)';
    ctx.shadowBlur = 32;
    ctx.font = '700 94px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText('300°C GLASS', W / 2, 222);

    ctx.font = '700 72px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#3CF0FF';
    ctx.fillText('x 10°C PAANI!', W / 2, 318);

    roundRect(ctx, W / 2 - 245, 358, 490, 54, 27);
    ctx.fillStyle = 'rgba(255, 68, 24, 0.94)';
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.font = '700 26px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#FFFFFF';
    ctx.textBaseline = 'middle';
    ctx.fillText('THERMAL SHOCK V6 ULTRA', W / 2, 386);
    ctx.restore();
    return;
  }

  // 3. PROTECTED CLIMAX WINDOW -> 100% ZERO HUD/CAPTIONS!
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
  ctx.fillStyle = 'rgba(6, 11, 18, 0.76)';
  ctx.fill();
  ctx.lineWidth = 1.4;
  ctx.strokeStyle = hud.boroMode
    ? 'rgba(62, 245, 212, 0.48)'
    : hud.shatteredMode
      ? 'rgba(255, 82, 56, 0.55)'
      : 'rgba(255, 255, 255, 0.16)';
  ctx.stroke();

  const pulse = 0.65 + 0.35 * Math.sin(hud.time * Math.PI * 4.0);
  ctx.beginPath();
  ctx.arc(px + 24, py + ph / 2, 6, 0, Math.PI * 2);
  ctx.fillStyle = hud.boroMode
    ? `rgba(62, 245, 212, ${pulse})`
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

  // 5. Top-Left Docked Wall Shear Stress Bar (Active in S4/S5 AND shows calm 18% SAFE in S8 Borosilicate!)
  if (hud.stressPct > 0.02) {
    const gx = 52, gy = 206, gw = 330, gh = 16;
    const fillW = Math.max(14, gw * hud.stressPct);
    const barCol = hud.boroMode
      ? '#3EF5D4'
      : (hud.stressPct < 0.45 ? '#3CF0FF' : hud.stressPct < 0.78 ? '#FFB454' : '#FF3B1F');

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
    ctx.fillText(hud.boroMode ? 'BORON SHIELD STRESS (SAFE)' : 'WALL SHEAR STRESS', gx + 4, gy + 34);
    ctx.font = '700 24px "Space Grotesk", sans-serif';
    ctx.fillStyle = barCol;
    ctx.fillText(`${Math.round(hud.stressPct * 100)}%`, gx + gw + 14, gy + 8);
    ctx.restore();
  }

  // 6. 3D-Tracked Science Pointer Callouts
  for (const c of hud.callouts) {
    if (!c.visible) continue;
    ctx.save();
    const ax = GLM.clamp(c.x, 110, 820);
    const ay = GLM.clamp(c.y, 265, 1140);
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
    ctx.fillStyle = 'rgba(6, 12, 20, 0.85)';
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#F2FAFF';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    ctx.fillText(txt, boxX + 14, boxY + 22);
    ctx.restore();
  }

  // 7. Kinetic Read-Along Roman-Urdu Captions (Safe Zone y=1365 <= 1490)
  if (opts.showCaptions) {
    const t = hud.time;
    const cap = captions.find((c) => t >= c.t0 && t <= c.t1);
    if (cap) {
      const dtIn = (t - cap.t0) * FPS;
      const dtOut = (cap.t1 - t) * FPS;
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
      ctx.fillStyle = 'rgba(6, 11, 18, 0.76)';
      ctx.fill();
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
      ctx.stroke();

      ctx.fillStyle = cap.accent;
      roundRect(ctx, -Math.min(cardW * 0.36, 180), 66, Math.min(cardW * 0.72, 360) * uIn, 4, 2);
      ctx.fill();

      ctx.font = '700 58px "Space Grotesk", sans-serif';
      ctx.textBaseline = 'middle';
      ctx.shadowColor = 'rgba(0, 0, 0, 0.78)';
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

      ctx.font = '600 38px "Space Grotesk", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = 'rgba(212, 234, 248, 0.96)';
      ctx.fillText(cap.l2, 0, 38);
      ctx.restore();
    }
  }
}
