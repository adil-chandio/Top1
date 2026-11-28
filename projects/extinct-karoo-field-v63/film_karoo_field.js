import * as THREE from 'three';
import {
  createCinemaCameraRig,
  setImaxLightingPreset,
  lensMmToThreeFovY,
  GLM,
} from '/tools/monarch-v6-imax-sdk/index.js';
import {
  FPS,
  DURATION,
  TOTAL_FRAMES,
} from './film_karoo_field_world.js';
import VOICE_LOCK from './voice-lock-karoo-field-v63.json';

/**
 * EXTINCT LIFE V6.3 DIRECTOR EDITION — "This Rock Holds Two Animals" (`BP/1/5558`)
 * Archetype: `W02_SCORCHED_FIELD_EXPEDITION` + `H1_DOCUMENTARY_LOWER_THIRD`
 *
 * Powered by `director_optics_sdk.js` (`lensMmToThreeFovY` full-frame 36mm cinema lenses:
 * 28mm, 35mm, 50mm, 85mm, 100mm Macro) and locked 1:1 to `director-plan.json`.
 */

export const SHOTS = VOICE_LOCK.shots;
export const CAPTIONS = VOICE_LOCK.captions;
export const PROTECTED_WINDOWS = VOICE_LOCK.protected_climax_windows_s;
export const FLOOD_F = VOICE_LOCK.flood_surge_f; // 794

const FOV_28  = lensMmToThreeFovY(28,  '9:16_short'); // 65.5 deg
const FOV_35  = lensMmToThreeFovY(35,  '9:16_short'); // 54.4 deg
const FOV_50  = lensMmToThreeFovY(50,  '9:16_short'); // 39.6 deg
const FOV_85  = lensMmToThreeFovY(85,  '9:16_short'); // 23.9 deg
const FOV_100 = lensMmToThreeFovY(100, '9:16_short'); // 20.4 deg

const HERO_LOOP_CAM = {
  pos: [0.0, 0.96, 3.36],
  look: [0.0, 0.35, 0.16],
  fov: FOV_35,
  dutch: 0.0,
};

const SHOT_CAM = {
  // S01 (35mm low-angle push_in): Sun-baked Karoo excavation trench + hammer + brush + scale card + solid red boulder
  S01: {
    from: HERO_LOOP_CAM,
    to:   { pos: [0.14, 0.92, 3.02], look: [0.0, 0.34, 0.12], fov: FOV_35, dutch: 0.0 },
    focus: [0.0, 0.35, 0.08], dofRange: 14.0, maxBlur: 1.8,
  },
  // S02 (35mm truck_lateral reveal): Warm sunlit calcite cross-section peels solid rock open
  S02: {
    from: { pos: [-0.46, 1.56, 2.72], look: [-0.02, 0.36, 0.08], fov: FOV_35, dutch: -0.4 },
    to:   { pos: [ 0.22, 1.76, 2.52], look: [ 0.02, 0.35, 0.06], fov: FOV_35, dutch:  0.2 },
    focus: [0.0, 0.36, 0.05], dofRange: 10.5, maxBlur: 2.0,
  },
  // S03 (35mm static HOLD_STILLNESS): High-angle field study separating curled Thrinaxodon & supine Broomistega
  S03: {
    from: { pos: [0.06, 2.38, 1.95], look: [0.02, 0.37, 0.02], fov: FOV_35, dutch: 0.0 },
    to:   { pos: [0.06, 2.38, 1.95], look: [0.02, 0.37, 0.02], fov: FOV_35, dutch: 0.0 },
    focus: [0.02, 0.37, 0.02], dofRange: 11.0, maxBlur: 1.8,
  },
  // S04 (Single earned Hitchcock Vertigo dolly_zoom on -240 dBFS vacuum & "Wait. They were not enemies.")
  S04: {
    from: { pos: [ 0.10, 1.92, 1.96], look: [0.04, 0.37, 0.03], fov: lensMmToThreeFovY(38, '9:16_short'), dutch: -0.4 },
    to:   { pos: [-0.06, 2.86, 3.05], look: [0.04, 0.37, 0.03], fov: lensMmToThreeFovY(62, '9:16_short'), dutch: -1.8 },
    focus: [0.04, 0.37, 0.03], dofRange: 9.0, maxBlur: 2.2,
  },
  // S05 (100mm Macro probe_macro_glide): Surgical dive onto Broomistega's 3 #E63926 vermilion healing rib calluses!
  S05: {
    from: { pos: [0.46, 1.18, 1.62], look: [0.27, 0.34, 0.18], fov: FOV_100, dutch: 0.6 },
    to:   { pos: [0.34, 1.02, 1.32], look: [0.27, 0.34, 0.20], fov: FOV_100, dutch: 0.2 },
    focus: [0.27, 0.34, 0.20], dofRange: 3.4, maxBlur: 2.6,
  },
  // S06 (85mm static HOLD_STILLNESS): Full unscarred triangular amphibian skull + anterior ribs centered cleanly!
  S06: {
    from: { pos: [0.44, 1.52, 2.28], look: [0.43, 0.26, 0.19], fov: FOV_85, dutch: 0.0 },
    to:   { pos: [0.44, 1.52, 2.28], look: [0.43, 0.26, 0.19], fov: FOV_85, dutch: 0.0 },
    focus: [0.43, 0.26, 0.19], dofRange: 4.5, maxBlur: 2.4,
  },
  // S07 (28mm tracking_follow): 250-Ma Early Triassic split-horizon drought surface + injured amphibian crawling down ramp
  S07: {
    from: { pos: [-0.36, 1.24, 2.76], look: [-0.30, 0.86, -0.02], fov: FOV_28, dutch: 0.4 },
    to:   { pos: [ 0.04, 1.10, 2.46], look: [-0.04, 0.58, -0.02], fov: FOV_28, dutch: 0.0 },
    focus: [-0.18, 0.68, 0.0], dofRange: 12.0, maxBlur: 1.9,
  },
  // S08 (50mm static HOLD_STILLNESS): Intimate aestivation portrait framed by hanging earthen rootlets
  S08: {
    from: { pos: [0.20, 1.14, 2.26], look: [0.12, 0.38, 0.0], fov: FOV_50, dutch: 0.0 },
    to:   { pos: [0.20, 1.14, 2.26], look: [0.12, 0.38, 0.0], fov: FOV_50, dutch: 0.0 },
    focus: [0.12, 0.38, 0.0], dofRange: 4.8, maxBlur: 2.3,
  },
  // S09 (28mm wide pull_out): Monsoon lightning splits storm clouds above as terracotta silt torrent slams down ramp!
  S09: {
    from: { pos: [-0.24, 1.16, 2.54], look: [-0.16, 0.78, 0.0], fov: FOV_28, dutch: -1.4 },
    to:   { pos: [ 0.06, 1.12, 2.88], look: [ 0.02, 0.58, 0.0], fov: FOV_28, dutch:  1.2 },
    focus: [-0.06, 0.64, 0.0], dofRange: 12.0, maxBlur: 2.1,
  },
  // S10 (35mm static HOLD_STILLNESS — 100% ZERO HUD): Villeneuve pure-cinema lithification compaction!
  S10: {
    from: { pos: [0.08, 1.06, 2.56], look: [0.08, 0.46, 0.0], fov: FOV_35, dutch: 0.0 },
    to:   { pos: [0.08, 1.06, 2.56], look: [0.08, 0.46, 0.0], fov: FOV_35, dutch: 0.0 },
    focus: [0.08, 0.46, 0.0], dofRange: 11.0, maxBlur: 1.9,
  },
  // S11 (35mm static geological seal): Match-cut back to Karoo dig trench as calcite glow seals into solid stone
  S11: {
    from: { pos: [-0.14, 1.24, 3.38], look: [0.0, 0.43, 0.04], fov: FOV_35, dutch: 0.0 },
    to:   HERO_LOOP_CAM,
    focus: [0.0, 0.43, 0.04], dofRange: 13.0, maxBlur: 1.9,
  },
  // S12 (35mm locked loop closure): Pixel-identical Frame-0 alignment ("This rock holds two animals.")
  S12: {
    from: HERO_LOOP_CAM,
    to:   HERO_LOOP_CAM,
    focus: [0.0, 0.44, 0.05], dofRange: 14.0, maxBlur: 1.8,
  },
};

function shotAtFrame(f) {
  for (const s of SHOTS) {
    if (f >= s.f0 && f < s.f1) return s;
  }
  return SHOTS[SHOTS.length - 1];
}

export function createKarooFieldDirectorV63(world, camera) {
  const rig = createCinemaCameraRig(camera, {
    totalFrames: TOTAL_FRAMES,
    shotCuts: new Set(SHOTS.map((s) => s.f0)),
    impacts: [
      { frame: 335, amp: 0.55, decay: 0.22, freq: 2.7, durationFrames: 15 },     // "They were not enemies." drop
      { frame: FLOOD_F, amp: 1.75, decay: 0.14, freq: 2.4, durationFrames: 28 }, // Terracotta flash-flood wall slam!
      { frame: 884, amp: 0.88, decay: 0.18, freq: 2.1, durationFrames: 20 },     // Tectonic Beaufort sandstone seal
    ],
  });

  const camPos = new THREE.Vector3();
  const camLook = new THREE.Vector3();
  const tmpV = new THREE.Vector3();
  const shadowFocus = new THREE.Vector3(0, 0.45, 0);
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
    w.trenchRoot.visible = !inBurrowSet;
    w.triassicRoot.visible = inBurrowSet;

    let scanProgress = 0.0;
    let ribHighlight = 0.0;
    let speciesHighlight = 0.0;
    let isStorm = false;
    let stormMix = 0.0;

    if (!inBurrowSet) {
      // ---------- 1. SET A: SUN-BAKED KAROO EXCAVATION TRENCH ----------
      setImaxLightingPreset('karoo_desert_sun', { fogStart: 13.0, fogRange: 34.0 });
      w.skyMat.uniforms.uStormMix.value = 0.0;
      w.skyMat.uniforms.uLightning.value = 0.0;
      w.lightningBolt.visible = false;

      if (shot.id === 'S01' || shot.id === 'S12') {
        scanProgress = 0.0;
      } else if (shot.id === 'S02') {
        scanProgress = GLM.smoothstep(2.60, 5.20, t);
      } else if (shot.id === 'S11') {
        scanProgress = 1.0 - GLM.smoothstep(30.92, 32.75, t);
      } else {
        scanProgress = 1.0;
      }

      speciesHighlight = (shot.id === 'S03' || shot.id === 'S04') ? 0.90 : 0.30;
      ribHighlight = (shot.id === 'S05' || shot.id === 'S06')
        ? GLM.smoothstep(12.82, 13.38, t) * (1.0 - 0.18 * GLM.smoothstep(17.2, 18.0, t))
        : 0.0;

      // Move diagnostic ring from ribs #4-#6 (`S05`) to intact skull (`S06`)!
      if (shot.id === 'S06') {
        w.fossilRockRig.diagHalo.position.set(0.52, 0.09, 0.25);
        w.fossilRockRig.diagHaloMat.color.set('#e8b059');
      } else {
        w.fossilRockRig.diagHalo.position.set(0.27, 0.09, 0.24);
        w.fossilRockRig.diagHaloMat.color.set('#e63926');
      }

      // In-situ sandstone cast never spins like a turntable — stays physically embedded in the rock cradle!
      w.fossilRockRig.update({ scanProgress, ribHighlight, speciesHighlight, time: t });

      const showSlice = scanProgress > 0.02 && scanProgress < 0.98;
      w.sunSliceCurtain.visible = showSlice;
      if (showSlice) {
        w.sunSliceCurtain.position.set(GLM.mix(-1.02, 1.02, scanProgress), 1.32, 0.0);
      }

      // Warm golden sun flare bridge right at end of S06 (`17.85..18.16s`) into 250-Ma Triassic world
      const timeBridgeFlare = shot.id === 'S06' ? GLM.smoothstep(17.75, 18.16, t) * 1.4 : 0.0;

      w.ambientLight.color.set('#8fb4d4');
      w.ambientLight.groundColor.set('#b87248');
      w.ambientLight.intensity = 0.90;
      w.keyLight.color.set('#ffe6be');
      w.keyLight.intensity = 3.35 + timeBridgeFlare;
      w.skyRimLight.color.set('#f2d4a4');
      w.skyRimLight.intensity = 2.45 + 0.85 * scanProgress;
      w.trenchBounceLight.color.set('#e89458');
      w.trenchBounceLight.intensity = 1.85;
      w.fossilCoreLight.color.set(ribHighlight > 0.2 ? '#ff8866' : '#ffcf7c');
      w.fossilCoreLight.intensity = 2.6 * scanProgress + 1.4 * ribHighlight;
      shadowFocus.set(0.0, 0.38, 0.15);
    } else {
      // ---------- 2. SET B: 250-MA EARLY TRIASSIC FLOODPLAIN & BURROW ----------
      w.sunSliceCurtain.visible = false;

      isStorm = (shot.id === 'S09' || shot.id === 'S10');
      // Storm clouds begin gathering late in S08 (`24.6..25.5s`) to match the 25.15s thunder J-cut!
      stormMix = shot.id === 'S08'
        ? 0.42 * GLM.smoothstep(24.55, 25.53, t)
        : (isStorm ? GLM.smoothstep(25.40, 26.25, t) : 0.0);

      if (stormMix > 0.55) {
        setImaxLightingPreset('monsoon_storm', { fogStart: 12.0, fogRange: 32.0 });
      } else {
        setImaxLightingPreset('karoo_desert_sun', { fogStart: 13.0, fogRange: 34.0 });
      }

      const crawlProgress = shot.id === 'S07' ? GLM.smoothstep(0.04, 0.94, u) : 1.0;
      const surgeFront = isStorm ? GLM.smoothstep(25.45, 26.85, t) : 0.0;
      const fillLevel  = isStorm ? GLM.smoothstep(26.15, 28.85, t) : 0.0;
      const petrify    = shot.id === 'S10' ? GLM.smoothstep(28.75, 30.65, t) : 0.0;

      // Zero artificial glowing ring under living animals (`dormancyAura = 0.0` pure naturalism!)
      w.burrowRig.update({
        crawlProgress,
        dormancyAura: 0.0,
        floodSubmerge: fillLevel,
        time: t,
      });
      w.floodRig.update({
        active: isStorm,
        surgeFront,
        fillLevel,
        petrify,
        time: t,
      });

      // Dual-strike monsoon lightning forks across the storm sky (`25.80..26.55s`, peaking around f=782 & f=792!)
      const boltEnv1 = Math.exp(-Math.pow((t - 26.06) / 0.085, 2.0));
      const boltEnv2 = Math.exp(-Math.pow((t - 26.40) / 0.075, 2.0));
      const lightning = isStorm ? Math.max(boltEnv1, boltEnv2) * 2.6 : 0.0;

      w.skyMat.uniforms.uStormMix.value = stormMix;
      w.skyMat.uniforms.uLightning.value = lightning * 0.45;
      w.lightningBolt.visible = lightning > 0.22;
      w.lightningMat.opacity = GLM.clamp(lightning * 0.62, 0.0, 0.96);
      w.lightningHaloMat.opacity = GLM.clamp(lightning * 0.26, 0.0, 0.48);

      w.sunBlade.visible = stormMix < 0.75;
      w.ambientLight.intensity = GLM.mix(0.88, 0.55, stormMix);
      w.keyLight.color.setRGB(
        GLM.mix(1.0, 0.72, stormMix),
        GLM.mix(0.86, 0.80, stormMix),
        GLM.mix(0.62, 0.94, stormMix)
      );
      w.keyLight.intensity = GLM.mix(3.45, 2.05, stormMix) + lightning;
      w.skyRimLight.color.set(isStorm ? '#c8d6e6' : '#f2be78');
      w.skyRimLight.intensity = GLM.mix(2.6, 3.4, stormMix) + lightning * 0.8;
      w.trenchBounceLight.color.set(isStorm ? '#8c5a3c' : '#eb9452');
      w.trenchBounceLight.intensity = GLM.mix(2.2, 1.5, stormMix);
      w.fossilCoreLight.color.set('#ffd28c');
      w.fossilCoreLight.intensity = 1.35 * (1.0 - petrify * 0.45);
      shadowFocus.set(0.0, 0.55, 0.0);
    }

    w.updateRainAndNotebook(t, isStorm, stormMix);
    w.dust.update(t);

    // ---------- 3. DIRECTOR-OS 12-SHOT CAMERA EVALUATION ----------
    const e = shot.id === 'S04' ? GLM.smoothstep(0.0, 0.68, u) : GLM.easeInOutCubic(u);
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
    const fov = GLM.mix(cam.from.fov, cam.to.fov, e);
    const dutch = GLM.mix(cam.from.dutch, cam.to.dutch, e);

    // Respect Stillness Default (`breathAmp = 0.0` on locked tripod static beats & loop seam!)
    const isStaticBeat = shot.move === 'static';
    let breathAmp = isStaticBeat ? 0.004 : 0.018;
    if (shot.id === 'S01') breathAmp = 0.018 * GLM.smoothstep(0.0, 0.30, u);
    if (shot.id === 'S12') breathAmp = 0.0;
    if (shot.id === 'S05') breathAmp = 0.008;

    const rigState = rig.apply({
      frame: f,
      pos: camPos,
      look: camLook,
      fov,
      dutchDeg: dutch,
      breathAmp,
      shutterBlurScale: 0.28,
    });

    // ---------- 4. 30 Hz SHADOW PASS (Hide Volumetrics First — Zero-Flicker Law #3!) ----------
    const sliceVis = w.sunSliceCurtain.visible;
    const bladeVis = w.sunBlade.visible;
    const rainVis = w.rainMesh.visible;
    const boltVis = w.lightningBolt.visible;
    w.sunSliceCurtain.visible = false;
    w.sunBlade.visible = false;
    w.rainMesh.visible = false;
    w.lightningBolt.visible = false;
    w.shadowRig.updateShadowMap(w.scene, shadowFocus, 5.4);
    w.sunSliceCurtain.visible = sliceVis;
    w.sunBlade.visible = bladeVis;
    w.rainMesh.visible = rainVis;
    w.lightningBolt.visible = boltVis;

    // ---------- 5. OPTICAL POST-FX & ARCHIVAL DOCUMENTARY CALLOUTS ----------
    const focusDist = Math.max(0.5, camera.position.distanceTo(tmpV.set(...cam.focus)));
    const inProtectedClimax = PROTECTED_WINDOWS.some(([w0, w1]) => t >= w0 && t < w1);

    let exposure = inBurrowSet ? 1.18 : 1.14;
    if (shot.id === 'S05') exposure = 1.24;
    if (shot.id === 'S09' || shot.id === 'S10') exposure = 1.22;

    let bloomAmt = 0.30;
    if (scanProgress > 0.05 && scanProgress < 0.95) bloomAmt = 0.38;
    if (shot.id === 'S05') bloomAmt = 0.36;

    // Archival Natural-History Specimen Pointers (warm parchment + #E63926 vermilion pathology only!)
    callouts.length = 0;
    if (!inProtectedClimax) {
      if (shot.id === 'S03') {
        callouts.push({ ...projectWorldAnchor(-0.42, 0.42, -0.18), vDir: -1, vDist: 175, hDir: -1, label: 'THRINAXODON', value: 'MAMMAL RELATIVE', accent: '#E8B059' });
        callouts.push({ ...projectWorldAnchor( 0.34, 0.39,  0.20), vDir: +1, vDist: 155, hDir: +1, label: 'BROOMISTEGA', value: 'AMPHIBIAN',       accent: '#F4DFB8' });
      } else if (shot.id === 'S05') {
        callouts.push({ ...projectWorldAnchor(0.28, 0.42, 0.22), vDir: -1, vDist: 205, hDir: -1, label: 'RIBS #4–#6', value: 'HEALING CALLUSES', accent: '#E63926' });
      } else if (shot.id === 'S06') {
        callouts.push({ ...projectWorldAnchor(0.50, 0.23, 0.25), vDir: -1, vDist: 175, hDir: -1, label: 'SKULL & RIBS', value: '0 BITE MARKS', accent: '#E8B059' });
      } else if (shot.id === 'S07') {
        callouts.push({ ...projectWorldAnchor(-0.45, 0.88, 0.04), vDir: +1, vDist: 140, hDir: +1, label: '250 MA KAROO', value: 'DROUGHT REFUGE', accent: '#F4DFB8' });
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
        time: f >= TOTAL_FRAMES - 1 ? 0.0 : t,
      },
      hud: {
        time: t,
        frame: f,
        shot: shot.id,
        inProtectedClimax,
        inBurrowSet,
        callouts,
      },
    };
  }

  return { evaluateFrame };
}

// =============================================================================
// H1_DOCUMENTARY_LOWER_THIRD — ARCHIVAL NATURAL-HISTORY TYPOGRAPHY (ZERO SCI-FI!)
// =============================================================================
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

export function drawKarooFieldHudV63(ctx, state, captions, opts = { showCaptions: true }) {
  const W = ctx.canvas.width;
  const H = ctx.canvas.height;
  const hud = state.hud;
  ctx.clearRect(0, 0, W, H);

  // 1. HIGH-CTR OUTDOOR EXPEDITION COVER POSTER (`coverMode`)
  if (opts.coverMode) {
    ctx.save();
    const topG = ctx.createLinearGradient(0, 0, 0, 620);
    topG.addColorStop(0.0, 'rgba(32, 18, 10, 0.88)');
    topG.addColorStop(0.58, 'rgba(32, 18, 10, 0.46)');
    topG.addColorStop(1.0, 'rgba(32, 18, 10, 0.0)');
    ctx.fillStyle = topG;
    ctx.fillRect(0, 0, W, 620);

    ctx.textAlign = 'center';
    ctx.shadowColor = 'rgba(18, 9, 4, 0.92)';
    ctx.shadowBlur = 28;
    ctx.font = '700 88px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#FFF8EC';
    ctx.fillText('2 ANIMALS IN', W / 2, 205);

    ctx.font = '700 96px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#F2B857';
    ctx.fillText('ONE ROCK', W / 2, 310);

    // Clean warm archival stamp bar (zero cyan telemetry!)
    roundRect(ctx, W / 2 - 270, 348, 540, 50, 8);
    ctx.fillStyle = 'rgba(34, 20, 12, 0.86)';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgba(242, 184, 87, 0.78)';
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.font = '700 23px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#F4E3C1';
    ctx.textBaseline = 'middle';
    ctx.fillText('KAROO BASIN DIG · 250 MILLION YRS', W / 2, 374);
    ctx.restore();
    return;
  }

  if (hud.inProtectedClimax) return;

  // 2. SUBTLE DOCUMENTARY LOCATION STAMP (Only in opening trench establishing shots S01-S02)
  if (hud.shot === 'S01' || hud.shot === 'S02') {
    ctx.save();
    ctx.font = '700 22px "IBM Plex Mono", monospace';
    ctx.textAlign = 'left';
    ctx.fillStyle = 'rgba(34, 20, 12, 0.68)';
    roundRect(ctx, 64, 108, 535, 44, 6);
    ctx.fill();
    ctx.fillStyle = '#E8B059';
    ctx.fillRect(64, 108, 5, 44);
    ctx.fillStyle = '#F7EBD2';
    ctx.textBaseline = 'middle';
    ctx.fillText('KAROO BASIN, SOUTH AFRICA · BP/1/5558', 84, 131);
    ctx.restore();
  }

  // 3. ARCHIVAL SPECIMEN POINTER CALLOUTS (Warm Parchment + #E63926 Pathology Highlight)
  for (const c of hud.callouts) {
    if (!c.visible) continue;
    ctx.save();
    const ax = GLM.clamp(c.x, 150, W - 150);
    const ay = GLM.clamp(c.y, 320, H - 540);
    const vd = c.vDist || 155;
    const ex = GLM.clamp(ax + c.hDir * 95, 220, W - 220);
    const ey = GLM.clamp(ay + c.vDir * vd, 250, H - 500);

    // Anchor dot & hairline rule
    ctx.beginPath();
    ctx.arc(ax, ay, 6.5, 0, Math.PI * 2);
    ctx.fillStyle = c.accent;
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(ax, ay);
    ctx.lineTo(ex, ey);
    ctx.lineTo(ex + c.hDir * 44, ey);
    ctx.strokeStyle = 'rgba(247, 235, 210, 0.88)';
    ctx.lineWidth = 2.4;
    ctx.stroke();

    const boxW = 310;
    const boxH = 74;
    const bx = c.hDir > 0 ? Math.min(W - boxW - 48, ex + 44) : Math.max(48, ex - 44 - boxW);
    const by = ey - boxH * 0.5;

    roundRect(ctx, bx, by, boxW, boxH, 8);
    ctx.fillStyle = 'rgba(28, 17, 11, 0.86)';
    ctx.fill();
    ctx.fillStyle = c.accent;
    ctx.fillRect(bx, by, 6, boxH);

    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
    ctx.font = '700 20px "IBM Plex Mono", monospace';
    ctx.fillStyle = c.accent;
    ctx.fillText(c.label, bx + 20, by + 30);

    ctx.font = '700 24px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#FFF8EC';
    ctx.fillText(c.value, bx + 20, by + 58);
    ctx.restore();
  }

  // 4. H1_DOCUMENTARY_LOWER_THIRD CAPTIONS (Warm Charcoal-Sepia Card in Safe Zone y=1485..1645)
  if (!opts.showCaptions) return;
  const active = captions.find((cp) => hud.time >= cp.t0 && hud.time <= cp.t1 + 0.08);
  if (!active) return;

  ctx.save();
  const cardW = 880;
  const cardH = 148;
  const cx = (W - cardW) * 0.5;
  const cy = 1495;

  roundRect(ctx, cx, cy, cardW, cardH, 12);
  ctx.fillStyle = 'rgba(24, 15, 10, 0.82)';
  ctx.fill();
  ctx.strokeStyle = 'rgba(232, 176, 89, 0.36)';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Left editorial accent bar
  ctx.fillStyle = active.accent;
  roundRect(ctx, cx, cy, 8, cardH, [12, 0, 0, 12]);
  ctx.fill();

  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  ctx.shadowColor = 'rgba(0, 0, 0, 0.65)';
  ctx.shadowBlur = 10;

  // Line 1 & Line 2 with targeted single-phrase color highlight
  const drawHighlightedLine = (lineText, yPos, fontSize) => {
    ctx.font = `700 ${fontSize}px "Space Grotesk", sans-serif`;
    if (active.hi && lineText.includes(active.hi)) {
      const idx = lineText.indexOf(active.hi);
      const pre = lineText.slice(0, idx);
      const mid = active.hi;
      const post = lineText.slice(idx + mid.length);
      const totalW = ctx.measureText(lineText).width;
      let curX = W * 0.5 - totalW * 0.5;
      ctx.textAlign = 'left';
      if (pre) {
        ctx.fillStyle = '#FFF7EA';
        ctx.fillText(pre, curX, yPos);
        curX += ctx.measureText(pre).width;
      }
      ctx.fillStyle = active.accent;
      ctx.fillText(mid, curX, yPos);
      curX += ctx.measureText(mid).width;
      if (post) {
        ctx.fillStyle = '#FFF7EA';
        ctx.fillText(post, curX, yPos);
      }
    } else {
      ctx.textAlign = 'center';
      ctx.fillStyle = '#FFF7EA';
      ctx.fillText(lineText, W * 0.5, yPos);
    }
  };

  drawHighlightedLine(active.l1, cy + 62, 42);
  drawHighlightedLine(active.l2, cy + 118, 44);
  ctx.restore();
}
