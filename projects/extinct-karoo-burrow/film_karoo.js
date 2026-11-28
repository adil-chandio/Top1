import * as THREE from 'three';
import {
  createCinemaCameraRig,
  setImaxLightingPreset,
  GLM,
} from '/tools/monarch-v6-imax-sdk/index.js';
import {
  FPS,
  DURATION,
  TOTAL_FRAMES,
} from './film_karoo_world.js';
import VOICE_LOCK from './voice-lock-karoo-v6.json';

/**
 * EXTINCT LIFE V6 ULTRA — "This Rock Holds Two Animals" (`BP/1/5558`, ~250 Ma Karoo Burrow)
 * 12-Shot Cinema Director & Safe-Zone Scientific HUD (`film_karoo.js`).
 */

export const SHOTS = VOICE_LOCK.shots;
export const CAPTIONS = VOICE_LOCK.captions;
export const PROTECTED_WINDOWS = VOICE_LOCK.protected_climax_windows_s;
export const FLOOD_F = VOICE_LOCK.flood_surge_f; // 794

const HERO_LOOP_CAM = {
  pos: [0.0, 1.54, 5.15],
  look: [0.0, 0.56, 0.0],
  fov: 37.5,
  dutch: 0.0,
};

// 12-Shot Cinema Choreography (every shot verified with GLM.visibleHorizontalWidth for 9:16 portrait!)
const SHOT_CAM = {
  S01_LAB_HOOK: {
    from: HERO_LOOP_CAM,
    to:   { pos: [0.46, 1.44, 4.55], look: [0.0, 0.54, 0.0], fov: 36.5, dutch: 0.5 },
    focus: [0.0, 0.54, 0.0], dofRange: 10.5, maxBlur: 2.6,
  },
  S02_LASER_TOMOGRAPHY: {
    from: { pos: [-0.62, 1.88, 4.25], look: [0.0, 0.50, 0.0], fov: 36.5, dutch: -0.6 },
    to:   { pos: [ 0.28, 2.38, 3.65], look: [0.0, 0.48, 0.0], fov: 35.5, dutch: 0.3 },
    focus: [0.0, 0.50, 0.0], dofRange: 9.5, maxBlur: 2.4,
  },
  S03_DUAL_FOSSIL_ORBIT: {
    // High 48° museum overhead arc so BOTH skeletons (left-back curled Thrinaxodon + right-front Broomistega) are 100% separated!
    arc: { r0: 2.85, r1: 2.45, a0: -0.24, a1: 0.28, y0: 3.15, y1: 2.95 },
    look: [0.0, 0.46, 0.02], fovFrom: 36.5, fovTo: 35.0, dutch: 0.0,
    focus: [0.0, 0.46, 0.02], dofRange: 8.5, maxBlur: 2.3,
  },
  S04_WAIT_VERTIGO: {
    // Hitchcock VERTIGO Dolly-Zoom on "Wait. They were not enemies." (camera pulls back while FOV narrows 36->28.0°!)
    from: { pos: [0.18, 2.55, 2.75], look: [0.02, 0.46, 0.03], fov: 36.0, dutch: -0.8 },
    to:   { pos: [0.00, 3.25, 3.65], look: [0.02, 0.46, 0.03], fov: 28.0, dutch: -2.4 },
    focus: [0.02, 0.46, 0.03], dofRange: 8.5, maxBlur: 2.3,
  },
  S05_HEALING_RIBS_MACRO: {
    // Extreme Micro-CT Macro Dive directly onto Broomistega's 3 glowing golden healing rib calluses!
    from: { pos: [0.48, 1.56, 2.18], look: [0.26, 0.46, 0.18], fov: 34.0, dutch: 1.0 },
    to:   { pos: [0.32, 1.38, 1.85], look: [0.27, 0.46, 0.20], fov: 32.0, dutch: 0.3 },
    focus: [0.27, 0.46, 0.20], dofRange: 4.8, maxBlur: 2.6,
  },
  S06_NOT_A_HUNT: {
    // Forensic crane from flat amphibian skull back across intact healing ribcage & curled partner
    from: { pos: [0.68, 1.82, 2.45], look: [0.24, 0.46, 0.14], fov: 35.0, dutch: -0.5 },
    to:   { pos: [-0.18, 2.25, 2.95], look: [0.02, 0.46, 0.04], fov: 36.0, dutch: 0.0 },
    focus: [0.10, 0.46, 0.08], dofRange: 7.5, maxBlur: 2.4,
  },
  S07_TRIASSIC_SHELTER: {
    // 250M-Year Time Rewind: Cutaway of sun-lit Triassic burrow tunnel as injured amphibian crawls down!
    from: { pos: [-0.36, 1.54, 4.75], look: [-0.38, 0.82, -0.02], fov: 38.0, dutch: 0.8 },
    to:   { pos: [ 0.08, 1.38, 4.05], look: [-0.04, 0.54, -0.02], fov: 36.5, dutch: 0.0 },
    focus: [-0.20, 0.66, 0.0], dofRange: 10.0, maxBlur: 2.3,
  },
  S08_AESTIVATION_SLEEP: {
    // Elevated 32° cutaway into chamber so BOTH curled dormant Thrinaxodon (back-right) & nestled Broomistega (front-left) show clearly!
    from: { pos: [0.14, 1.48, 3.25], look: [0.12, 0.38, 0.00], fov: 35.5, dutch: -0.4 },
    to:   { pos: [0.28, 1.36, 2.88], look: [0.14, 0.36, 0.00], fov: 34.0, dutch: 0.2 },
    focus: [0.14, 0.38, 0.00], dofRange: 7.2, maxBlur: 2.4,
  },
  S09_FLOOD_INRUSH: {
    // Dramatic wide pullback as monsoon flash-flood muddy wave surges down the burrow tunnel!
    from: { pos: [-0.24, 1.38, 4.65], look: [-0.22, 0.72, 0.0], fov: 38.5, dutch: -1.8 },
    to:   { pos: [ 0.12, 1.24, 4.15], look: [ 0.04, 0.52, 0.0], fov: 37.0, dutch: 1.6 },
    focus: [-0.05, 0.60, 0.0], dofRange: 9.5, maxBlur: 2.6,
  },
  S10_CLIMAX_PETRIFY: {
    // Protected Pure-Cinema Climax (0% HUD): slow push into swirling flooded chamber as sediment compacts into stone!
    from: { pos: [0.14, 1.18, 3.85], look: [0.12, 0.48, 0.0], fov: 36.5, dutch: 1.2 },
    to:   { pos: [0.02, 1.34, 3.45], look: [0.10, 0.46, 0.0], fov: 35.0, dutch: 0.0 },
    focus: [0.10, 0.46, 0.0], dofRange: 8.0, maxBlur: 2.5,
  },
  S11_CLUE_KEPT: {
    // Match-cut back to Synchrotron Lab as translucent amber X-ray rock seals back into solid sandstone!
    from: { pos: [-0.38, 1.68, 3.95], look: [0.0, 0.54, 0.0], fov: 36.0, dutch: 0.0 },
    to:   { pos: [ 0.42, 1.58, 4.65], look: [0.0, 0.55, 0.0], fov: 37.0, dutch: 0.4 },
    focus: [0.0, 0.54, 0.0], dofRange: 9.5, maxBlur: 2.5,
  },
  S12_SEAMLESS_LOOP: {
    from: { pos: [0.42, 1.58, 4.65], look: [0.0, 0.55, 0.0], fov: 37.0, dutch: 0.4 },
    to:   HERO_LOOP_CAM,
    focus: [0.0, 0.56, 0.0], dofRange: 10.5, maxBlur: 2.6,
  },
};

function shotAtFrame(f) {
  for (const s of SHOTS) {
    if (f >= s.f0 && f < s.f1) return s;
  }
  return SHOTS[SHOTS.length - 1];
}

export function createKarooDirectorV6(world, camera) {
  const rig = createCinemaCameraRig(camera, {
    totalFrames: TOTAL_FRAMES,
    shotCuts: new Set(SHOTS.map((s) => s.f0)),
    impacts: [
      { frame: 335, amp: 0.65, decay: 0.22, freq: 2.8, durationFrames: 16 },     // "They were not enemies." drop
      { frame: FLOOD_F, amp: 1.85, decay: 0.14, freq: 2.4, durationFrames: 28 }, // Monsoon flash-flood surge slam!
      { frame: 885, amp: 0.95, decay: 0.18, freq: 2.2, durationFrames: 20 },     // Tectonic sandstone seal thud
    ],
  });

  const camPos = new THREE.Vector3();
  const camLook = new THREE.Vector3();
  const tmpV = new THREE.Vector3();
  const shadowFocus = new THREE.Vector3(0, 0.55, 0);
  const callouts = [];

  function projectWorldAnchor(x, y, z) {
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

    const inBurrowSet = shot.set === 'BURROW';
    w.labRoot.visible = !inBurrowSet;
    w.triassicRoot.visible = inBurrowSet;

    // ---------- 1. SET A (SYNCHROTRON LAB) CHOREOGRAPHY ----------
    let scanProgress = 0.0;
    let ribHighlight = 0.0;
    let speciesHighlight = 0.0;

    if (!inBurrowSet) {
      setImaxLightingPreset('cinema_lab', { fogStart: 18.0, fogRange: 45.0 });
      w.cycMat.color.set('#070c14');

      // Scan sweeps 0 -> 1 in S02 (`t = 2.60 .. 5.20s`), stays 1.0 in S03..S06, and seals 1 -> 0 in S11 (`t = 30.95 .. 32.85s`)!
      if (shot.id === 'S01_LAB_HOOK' || shot.id === 'S12_SEAMLESS_LOOP') {
        scanProgress = 0.0;
      } else if (shot.id === 'S02_LASER_TOMOGRAPHY') {
        scanProgress = GLM.smoothstep(2.60, 5.15, t);
      } else if (shot.id === 'S11_CLUE_KEPT') {
        scanProgress = 1.0 - GLM.smoothstep(30.95, 32.80, t);
      } else {
        scanProgress = 1.0;
      }

      speciesHighlight = (shot.id === 'S03_DUAL_FOSSIL_ORBIT' || shot.id === 'S04_WAIT_VERTIGO') ? 1.0 : 0.35;
      ribHighlight = (shot.id === 'S05_HEALING_RIBS_MACRO' || shot.id === 'S06_NOT_A_HUNT')
        ? GLM.smoothstep(12.90, 13.45, t) * (1.0 - 0.35 * GLM.smoothstep(16.8, 17.8, t))
        : 0.0;

      // Subtle turntable rotation that returns to exact 0.000 rad at Frame 0 & Frame 1079!
      let rotY = 0.0;
      if (shot.id === 'S01_LAB_HOOK') {
        rotY = 0.14 * GLM.smoothstep(0.0, 1.0, u);
      } else if (shot.id === 'S02_LASER_TOMOGRAPHY') {
        rotY = GLM.mix(0.14, 0.04, GLM.easeInOutCubic(u));
      } else if (shot.id === 'S11_CLUE_KEPT') {
        rotY = GLM.mix(-0.12, 0.08, GLM.easeInOutCubic(u));
      } else if (shot.id === 'S12_SEAMLESS_LOOP') {
        rotY = 0.08 * (1.0 - GLM.smoothstep(0.0, 0.85, u));
      }
      w.labStage.rotaryTurntable.rotation.y = rotY;

      w.fossilRockRig.update({ scanProgress, ribHighlight, speciesHighlight, time: t });

      // Active Synchrotron Laser Curtain during scan sweep (`S02` & `S11`)
      const showLaser = (scanProgress > 0.02 && scanProgress < 0.98);
      w.laserScanner.visible = showLaser;
      if (showLaser) {
        w.laserScanner.position.set(GLM.mix(-1.05, 1.05, scanProgress), 0.0, 0.0);
      }

      w.keyLight.color.set('#fff2dc');
      w.keyLight.intensity = 2.95 - 0.35 * scanProgress;
      w.rimLight.color.set('#4ef2e0');
      w.rimLight.intensity = 5.4 + 2.2 * scanProgress;
      w.warmFill.color.set('#ffb464');
      w.warmFill.intensity = 2.2;
      w.xrayCoreLight.intensity = 3.2 * scanProgress + 1.6 * ribHighlight;
      shadowFocus.set(0, 0.45, 0);
    } else {
      // ---------- 2. SET B (250-MA EARLY TRIASSIC BURROW + FLASH FLOOD) ----------
      w.laserScanner.visible = false;

      const isFlood = (shot.id === 'S09_FLOOD_INRUSH' || shot.id === 'S10_CLIMAX_PETRIFY');
      const crawlProgress = shot.id === 'S07_TRIASSIC_SHELTER'
        ? GLM.smoothstep(0.04, 0.94, u)
        : 1.0;
      const dormancyAura = shot.id === 'S08_AESTIVATION_SLEEP'
        ? Math.sin(u * Math.PI)
        : 0.0;

      const surgeFront = isFlood ? GLM.smoothstep(25.42, 26.85, t) : 0.0;
      const fillLevel  = isFlood ? GLM.smoothstep(26.15, 28.85, t) : 0.0;
      const petrify    = shot.id === 'S10_CLIMAX_PETRIFY' ? GLM.smoothstep(28.85, 30.65, t) : 0.0;

      w.burrowRig.update({
        crawlProgress,
        dormancyAura,
        floodSubmerge: fillLevel,
        time: t,
      });
      w.floodRig.update({
        active: isFlood,
        surgeFront,
        fillLevel,
        petrify,
        time: t,
      });

      // Shift lighting from scorching Triassic drought sun (S07/S08) -> Monsoon storm flash (S09/S10)!
      const stormMix = isFlood ? GLM.smoothstep(25.55, 26.40, t) : 0.0;
      const lightning = (isFlood && t > 25.75 && t < 26.65)
        ? Math.pow(Math.max(0, Math.sin(t * 29.0)), 8.0) * 2.2
        : 0.0;

      w.cycMat.color.setRGB(
        GLM.mix(0.14, 0.05, stormMix),
        GLM.mix(0.08, 0.09, stormMix),
        GLM.mix(0.05, 0.14, stormMix)
      );
      w.sunBlade.visible = stormMix < 0.85;
      w.triassicSkyGlow.material.opacity = 0.82 * (1.0 - stormMix * 0.72);

      w.keyLight.color.setRGB(
        GLM.mix(1.0, 0.68, stormMix),
        GLM.mix(0.84, 0.86, stormMix),
        GLM.mix(0.58, 1.0, stormMix)
      );
      w.keyLight.intensity = GLM.mix(3.4, 2.35, stormMix) + lightning;
      w.rimLight.color.set(isFlood ? '#68d8ff' : '#ffad58');
      w.rimLight.intensity = GLM.mix(3.8, 5.2, stormMix) + lightning;
      w.warmFill.color.set(isFlood ? '#4aa8d8' : '#ff9848');
      w.warmFill.intensity = GLM.mix(2.6, 1.8, stormMix);
      w.xrayCoreLight.intensity = 1.6 * (1.0 - petrify * 0.5);
      shadowFocus.set(0.0, 0.55, 0.0);
    }

    w.dust.update(t);

    // ---------- 3. 12-SHOT CAMERA EVALUATION ----------
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
    } else {
      const e = shot.id === 'S04_WAIT_VERTIGO' ? GLM.smoothstep(0.0, 0.65, u) : GLM.easeInOutCubic(u);
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

    // Taper breathing to exact 0.000 across loop seam (`Frame 0` & `Frame 1079`)!
    let breathAmp = 0.028;
    if (shot.id === 'S01_LAB_HOOK') breathAmp = 0.028 * GLM.smoothstep(0.0, 0.25, u);
    else if (shot.id === 'S12_SEAMLESS_LOOP') breathAmp = 0.028 * (1.0 - GLM.smoothstep(0.62, 0.94, u));
    else if (shot.id === 'S05_HEALING_RIBS_MACRO') breathAmp = 0.012;

    const rigState = rig.apply({
      frame: f,
      pos: camPos,
      look: camLook,
      fov,
      dutchDeg: dutch,
      breathAmp,
      shutterBlurScale: 0.30,
    });

    // ---------- 4. 30 Hz SHADOW PASS (Hide Volumetrics First — Zero-Flicker Law #3!) ----------
    const spotVis = w.labSpotCone.visible;
    const bladeVis = w.sunBlade.visible;
    w.labSpotCone.visible = false;
    w.sunBlade.visible = false;
    w.shadowRig.updateShadowMap(w.scene, shadowFocus, 5.2);
    w.labSpotCone.visible = spotVis;
    w.sunBlade.visible = bladeVis;

    // ---------- 5. OPTICAL POST-FX & PROTECTED CLIMAX GATES ----------
    const focusDist = Math.max(0.5, camera.position.distanceTo(tmpV.set(...cam.focus)));
    const inProtectedClimax = PROTECTED_WINDOWS.some(([w0, w1]) => t >= w0 && t < w1);

    let exposure = inBurrowSet ? 1.28 : 1.24;
    if (shot.id === 'S05_HEALING_RIBS_MACRO') exposure = 1.34;
    if (shot.id === 'S10_CLIMAX_PETRIFY') exposure = 1.26;

    let bloomAmt = 0.44;
    if (scanProgress > 0.05 && scanProgress < 0.95) bloomAmt = 0.56;
    if (shot.id === 'S05_HEALING_RIBS_MACRO') bloomAmt = 0.52;

    // 3D-Projected Scientific Pointer Callouts (non-overlapping top/bottom elbow vectors so bones stay 100% unobstructed!)
    callouts.length = 0;
    if (!inProtectedClimax) {
      if (shot.id === 'S03_DUAL_FOSSIL_ORBIT') {
        callouts.push({ ...projectWorldAnchor(-0.44, 0.48, -0.22), vDir: -1, hDir: -1, label: 'THRINAXODON', value: 'MAMMAL RELATIVE', color: '#F7C35F' });
        callouts.push({ ...projectWorldAnchor( 0.34, 0.45,  0.22), vDir: +1, hDir: +1, label: 'BROOMISTEGA', value: 'AMPHIBIAN',       color: '#3AD4BE' });
      } else if (shot.id === 'S05_HEALING_RIBS_MACRO' || shot.id === 'S06_NOT_A_HUNT') {
        callouts.push({ ...projectWorldAnchor(0.28, 0.48, 0.24), vDir: -1, vDist: 215, hDir: -1, label: 'RIBS #4-#6',   value: 'HEALING CALLUSES', color: '#FFD166' });
        callouts.push({ ...projectWorldAnchor(0.50, 0.48, 0.26), vDir: +1, vDist: 135, hDir: +1, label: 'SKULL & RIBS', value: '0 BITE MARKS',     color: '#3AD4BE' });
      } else if (shot.id === 'S07_TRIASSIC_SHELTER') {
        callouts.push({ ...projectWorldAnchor(-0.42, 0.86, 0.04), vDir: -1, hDir: +1, label: 'INFERENCE', value: 'SHELTER FROM HEAT', color: '#F7C35F' });
      } else if (shot.id === 'S08_AESTIVATION_SLEEP') {
        callouts.push({ ...projectWorldAnchor(0.28, 0.44, -0.14), vDir: -1, hDir: +1, label: 'AESTIVATION', value: 'DORMANT SLEEP', color: '#3AD4BE' });
      }
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
        shot: shot.id,
        inProtectedClimax,
        inBurrowSet,
        scanProgress,
        ribHighlight,
        callouts,
      },
    };
  }

  return { evaluateFrame };
}

// =============================================================================
// EXTINCT LIFE DOCUMENTARY HUD & VIRAL COVER COMPOSITOR
// =============================================================================
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

export function drawKarooHudV6(ctx, state, captions, opts = { showCaptions: true }) {
  const W = ctx.canvas.width;
  const H = ctx.canvas.height;
  const hud = state.hud;
  ctx.clearRect(0, 0, W, H);

  // 1. HIGH-CTR VIRAL COVER POSTER LOCKUP
  if (opts.coverMode) {
    ctx.save();
    const topG = ctx.createLinearGradient(0, 0, 0, 680);
    topG.addColorStop(0.0, 'rgba(5, 9, 15, 0.94)');
    topG.addColorStop(0.58, 'rgba(5, 9, 15, 0.68)');
    topG.addColorStop(1.0, 'rgba(5, 9, 15, 0.0)');
    ctx.fillStyle = topG;
    ctx.fillRect(0, 0, W, 680);

    ctx.textAlign = 'center';
    ctx.shadowColor = 'rgba(0, 0, 0, 0.95)';
    ctx.shadowBlur = 32;
    ctx.font = '700 88px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText('2 ANIMALS IN', W / 2, 215);

    ctx.font = '700 92px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#F7C35F';
    ctx.fillText('ONE ROCK!', W / 2, 318);

    roundRect(ctx, W / 2 - 265, 358, 530, 54, 27);
    ctx.fillStyle = 'rgba(16, 46, 54, 0.92)';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#3AD4BE';
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.font = '700 24px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#3AD4BE';
    ctx.textBaseline = 'middle';
    ctx.fillText('250 MILLION YRS · X-RAY SCAN', W / 2, 386);
    ctx.restore();
    return;
  }

  // 2. PROTECTED CLIMAX WINDOWS -> 100% ZERO HUD / CAPTIONS!
  if (hud.inProtectedClimax) {
    return;
  }

  // 3. Top-Left Scientific Provenance Telemetry Pill (strictly distinguishes Evidence vs Reconstruction!)
  ctx.save();
  ctx.font = '600 20px "IBM Plex Mono", monospace';
  const leftTag = hud.inBurrowSet ? 'KAROO ~250 MA' : 'SYNCHROTRON CT';
  const rightTag = hud.inBurrowSet
    ? 'RECONSTRUCTION'
    : (hud.ribHighlight > 0.2 ? 'EVIDENCE: RIB CALLUS' : 'BP/1/5558 FOSSIL');

  const wL = ctx.measureText(leftTag).width;
  const wR = ctx.measureText(rightTag).width;
  const pillW = 70 + wL + wR;
  const px = 52, py = 144, ph = 48;

  roundRect(ctx, px, py, pillW, ph, 24);
  ctx.fillStyle = 'rgba(7, 12, 19, 0.78)';
  ctx.fill();
  ctx.lineWidth = 1.4;
  ctx.strokeStyle = hud.inBurrowSet ? 'rgba(247, 195, 95, 0.42)' : 'rgba(58, 212, 190, 0.45)';
  ctx.stroke();

  const pulse = 0.65 + 0.35 * Math.sin(hud.time * Math.PI * 3.0);
  ctx.beginPath();
  ctx.arc(px + 24, py + ph / 2, 6, 0, Math.PI * 2);
  ctx.fillStyle = hud.inBurrowSet ? `rgba(247, 195, 95, ${pulse})` : `rgba(58, 212, 190, ${pulse})`;
  ctx.fill();

  ctx.textBaseline = 'middle';
  ctx.fillStyle = '#EEF4FA';
  ctx.fillText(leftTag, px + 42, py + ph / 2 + 1);
  ctx.fillStyle = 'rgba(255,255,255,0.28)';
  ctx.fillText('|', px + 50 + wL, py + ph / 2 + 1);
  ctx.fillStyle = hud.inBurrowSet ? '#F7C35F' : '#3AD4BE';
  ctx.fillText(rightTag, px + 64 + wL, py + ph / 2 + 1);
  ctx.restore();

  // 4. 3D-Projected Anatomy & Burrow Pointer Callouts (Non-overlapping vertical + horizontal offsets!)
  for (const c of hud.callouts) {
    if (!c.visible) continue;
    ctx.save();
    const ax = GLM.clamp(c.x, 120, 840);
    const ay = GLM.clamp(c.y, 340, 1080);
    const dirX = c.hDir || (ax > 520 ? -1 : 1);
    const dirY = c.vDir || -1;

    ctx.strokeStyle = c.color || '#3AD4BE';
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.arc(ax, ay, 7, 0, Math.PI * 2);
    ctx.stroke();

    const spanY = c.vDist || 115;
    const elbowX = GLM.clamp(ax + dirX * 56, 80, 880);
    const elbowY = GLM.clamp(ay + dirY * spanY, 245, 1210);
    ctx.beginPath();
    ctx.moveTo(ax + dirX * 6, ay + dirY * 6);
    ctx.lineTo(elbowX, elbowY);
    ctx.stroke();

    ctx.font = '600 19px "IBM Plex Mono", monospace';
    const txt = `${c.label}: ${c.value}`;
    const cw = ctx.measureText(txt).width + 28;
    const boxX = GLM.clamp(dirX > 0 ? elbowX - 18 : elbowX - cw + 18, 48, 895 - cw);
    const boxY = dirY < 0 ? elbowY - 44 : elbowY + 4;

    roundRect(ctx, boxX, boxY, cw, 42, 10);
    ctx.fillStyle = 'rgba(7, 13, 21, 0.88)';
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#F2F8FC';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    ctx.fillText(txt, boxX + 14, boxY + 22);
    ctx.restore();
  }

  // 5. Kinetic Read-Along Documentary Captions (`Safe Zone y=1368 <= 1490`)
  if (opts.showCaptions) {
    const t = hud.time;
    const cap = captions.find((c) => t >= c.t0 && t <= c.t1);
    if (cap) {
      const dtIn = (t - cap.t0) * FPS;
      const dtOut = (cap.t1 - t) * FPS;
      const uIn = GLM.clamp(dtIn / 6.0, 0, 1);
      const spring = uIn < 1.0 ? (0.90 + 0.12 * Math.sin(uIn * Math.PI * 0.72)) : 1.0;
      const alpha = GLM.clamp(Math.min(dtIn / 2.8, dtOut / 3.0, 1.0), 0, 1);

      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.translate(W / 2, 1368);
      ctx.scale(spring, spring);

      ctx.font = '700 56px "Space Grotesk", sans-serif';
      const wL1 = ctx.measureText(cap.l1).width;
      ctx.font = '600 36px "Space Grotesk", sans-serif';
      const wL2 = ctx.measureText(cap.l2).width;
      const cardW = Math.min(960, Math.max(wL1, wL2) + 76);

      roundRect(ctx, -cardW / 2, -62, cardW, 140, 24);
      ctx.fillStyle = 'rgba(7, 12, 20, 0.78)';
      ctx.fill();
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
      ctx.stroke();

      ctx.fillStyle = cap.accent;
      roundRect(ctx, -Math.min(cardW * 0.36, 180), 64, Math.min(cardW * 0.72, 360) * uIn, 4, 2);
      ctx.fill();

      ctx.font = '700 56px "Space Grotesk", sans-serif';
      ctx.textBaseline = 'middle';
      ctx.shadowColor = 'rgba(0, 0, 0, 0.80)';
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

      ctx.font = '600 36px "Space Grotesk", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = 'rgba(214, 232, 246, 0.96)';
      ctx.fillText(cap.l2, 0, 36);
      ctx.restore();
    }
  }
}
