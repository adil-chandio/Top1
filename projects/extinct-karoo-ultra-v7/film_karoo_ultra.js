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
} from './film_karoo_ultra_world.js';
import VOICE_LOCK from './voice-lock-karoo-ultra-v7.json';

/**
 * EXTINCT LIFE V7.0 AUTONOMOUS ULTRA MONARCH — Master Director & Camera Choreography
 * Locked 1:1 to `director-plan.json` & `voice-lock-karoo-ultra-v7.json` (`1,080` exact frames @ 30fps).
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
  pos: [0.0, 0.94, 3.34],
  look: [0.0, 0.36, 0.14],
  fov: FOV_35,
  dutch: 0.0,
};

const SHOT_CAM = {
  // S01 (35mm low-angle push_in): Active bristle brush sweeps sunlit dust off boulder with camp 4x4 & canopy behind!
  S01: {
    from: HERO_LOOP_CAM,
    to:   { pos: [0.16, 0.88, 2.86], look: [0.02, 0.37, 0.10], fov: FOV_35, dutch: -0.4 },
    focus: [0.0, 0.36, 0.08], dofRange: 14.5, maxBlur: 1.7,
  },
  // S02 (35mm truck_lateral + arc reveal): Upper sandstone cap physically cracks & lifts off in golden sunbeams!
  S02: {
    from: { pos: [-0.54, 1.48, 2.68], look: [-0.04, 0.38, 0.06], fov: FOV_35, dutch: -0.6 },
    to:   { pos: [ 0.28, 1.82, 2.38], look: [ 0.02, 0.34, 0.04], fov: FOV_35, dutch:  0.4 },
    focus: [0.0, 0.35, 0.04], dofRange: 10.5, maxBlur: 2.0,
  },
  // S03 (35mm overhead two-shot): Unobstructed ivory skeletons + sequential warm anatomical species silhouettes!
  S03: {
    from: { pos: [0.04, 2.32, 1.88], look: [0.01, 0.32, 0.02], fov: FOV_35, dutch: 0.0 },
    to:   { pos: [0.05, 2.26, 1.84], look: [0.01, 0.32, 0.02], fov: FOV_35, dutch: 0.0 },
    focus: [0.01, 0.32, 0.02], dofRange: 11.0, maxBlur: 1.8,
  },
  // S04 (Earned Hitchcock Vertigo contra-zoom across -240 dBFS vacuum & "Wait. They were not enemies.")
  S04: {
    from: { pos: [ 0.10, 1.88, 1.92], look: [0.03, 0.33, 0.03], fov: lensMmToThreeFovY(38, '9:16_short'), dutch: -0.4 },
    to:   { pos: [-0.08, 2.84, 3.02], look: [0.03, 0.33, 0.03], fov: lensMmToThreeFovY(62, '9:16_short'), dutch: -1.9 },
    focus: [0.03, 0.33, 0.03], dofRange: 9.0, maxBlur: 2.2,
  },
  // S05 (100mm Macro surgical fly-along): Sequential 1-2-3 #E63926 callus ignition on Ribs #4, #5, #6!
  S05: {
    from: { pos: [0.48, 1.24, 1.62], look: [0.30, 0.34, 0.19], fov: FOV_100, dutch: 0.6 },
    to:   { pos: [0.32, 1.20, 1.36], look: [0.26, 0.34, 0.19], fov: FOV_100, dutch: 0.1 },
    focus: [0.27, 0.34, 0.19], dofRange: 3.4, maxBlur: 2.6,
  },
  // S06 (85mm close-up): Intact unbitten triangular amphibian skull -> blazing golden 250-Ma sun-flare portal!
  S06: {
    from: { pos: [0.44, 1.48, 2.22], look: [0.43, 0.27, 0.19], fov: FOV_85, dutch: 0.0 },
    to:   { pos: [0.44, 1.45, 2.18], look: [0.43, 0.27, 0.19], fov: FOV_85, dutch: 0.0 },
    focus: [0.43, 0.27, 0.19], dofRange: 4.4, maxBlur: 2.4,
  },
  // S07 (28mm tracking_follow): Split-horizon drought surface + S-wave undulating Broomistega limping down ramp!
  S07: {
    from: { pos: [-0.42, 1.26, 2.78], look: [-0.32, 0.86, -0.02], fov: FOV_28, dutch: 0.5 },
    to:   { pos: [ 0.06, 1.08, 2.42], look: [-0.02, 0.54, -0.02], fov: FOV_28, dutch: 0.0 },
    focus: [-0.16, 0.66, 0.0], dofRange: 12.0, maxBlur: 1.9,
  },
  // S08 (50mm sanctuary portrait through swaying rootlets): Thrinaxodon sleepy eye-peek + sniff + gular breath!
  S08: {
    from: { pos: [0.20, 1.12, 2.22], look: [0.12, 0.37, 0.0], fov: FOV_50, dutch: 0.0 },
    to:   { pos: [0.18, 1.10, 2.19], look: [0.12, 0.37, 0.0], fov: FOV_50, dutch: 0.0 },
    focus: [0.12, 0.37, 0.0], dofRange: 4.6, maxBlur: 2.4,
  },
  // S09 (28mm wide pull_out + Frame-794 shock): Twin lightning + splashing mud wall slamming down over huddling pair!
  S09: {
    from: { pos: [-0.24, 1.16, 2.52], look: [-0.16, 0.78, 0.0], fov: FOV_28, dutch: -1.5 },
    to:   { pos: [ 0.08, 1.12, 2.88], look: [ 0.02, 0.56, 0.0], fov: FOV_28, dutch:  1.2 },
    focus: [-0.06, 0.64, 0.0], dofRange: 12.0, maxBlur: 2.1,
  },
  // S10 (35mm 0%-HUD monument frame): Rising Minnaert bubbles + churning terracotta silt compacting into stone!
  S10: {
    from: { pos: [0.08, 1.05, 2.54], look: [0.08, 0.46, 0.0], fov: FOV_35, dutch: 0.0 },
    to:   { pos: [0.08, 1.04, 2.50], look: [0.08, 0.46, 0.0], fov: FOV_35, dutch: 0.0 },
    focus: [0.08, 0.46, 0.0], dofRange: 11.0, maxBlur: 1.9,
  },
  // S11 (35mm geological re-seal): Upper sandstone cap descends and locks seamlessly over BP/1/5558!
  S11: {
    from: { pos: [-0.12, 1.18, 3.38], look: [0.0, 0.40, 0.08], fov: FOV_35, dutch: 0.0 },
    to:   HERO_LOOP_CAM,
    focus: [0.0, 0.38, 0.10], dofRange: 13.5, maxBlur: 1.8,
  },
  // S12 (35mm pixel-locked loop return): Exact Frame-0 alignment ("This rock holds two animals.")
  S12: {
    from: HERO_LOOP_CAM,
    to:   HERO_LOOP_CAM,
    focus: [0.0, 0.36, 0.08], dofRange: 14.5, maxBlur: 1.7,
  },
};

function shotAtFrame(f) {
  for (const s of SHOTS) {
    if (f >= s.f0 && f < s.f1) return s;
  }
  return SHOTS[SHOTS.length - 1];
}

function appleFluidEase(u) {
  const x = GLM.clamp(u, 0, 1);
  return x * x * x * (x * (x * 6 - 15) + 10);
}

export function createKarooUltraDirectorV7(world, camera) {
  const rig = createCinemaCameraRig(camera, {
    totalFrames: TOTAL_FRAMES,
    shotCuts: new Set(SHOTS.map((s) => s.f0)),
    impacts: [
      { frame:  78, amp: 0.38, decay: 0.24, freq: 3.1, durationFrames: 14 },     // S02 Hertzian sandstone cleavage crack!
      { frame: 335, amp: 0.58, decay: 0.22, freq: 2.7, durationFrames: 16 },     // "They were not enemies." sub-drop
      { frame: FLOOD_F, amp: 1.80, decay: 0.14, freq: 2.4, durationFrames: 28 }, // Frame 794 Terracotta mud-wall slam!
      { frame: 882, amp: 0.85, decay: 0.18, freq: 2.1, durationFrames: 20 },     // Tectonic sandstone lithification seal
    ],
  });

  const camPos = new THREE.Vector3();
  const camLook = new THREE.Vector3();
  const tmpV = new THREE.Vector3();
  const shadowFocus = new THREE.Vector3(0, 0.45, 0);
  const callouts = [];

  const boneRestCol = new THREE.Color('#e2d7c3');
  const boneHotCol  = new THREE.Color('#e63926');
  const emRestCol   = new THREE.Color('#383028');
  const emHotCol    = new THREE.Color('#c81e10');
  const ribClickTimes = VOICE_LOCK.rib_click_times_s; // [13.40, 14.12, 14.84]

  function projectWorldAnchor(x, y, z) {
    tmpV.set(x, y, z).project(camera);
    return {
      x: (tmpV.x * 0.5 + 0.5) * 1080,
      y: (-tmpV.y * 0.5 + 0.5) * 1920,
      visible: tmpV.z > -1.0 && tmpV.z < 1.0,
    };
  }

  function evaluateFrame(frame, opts = {}) {
    const f = ((frame % TOTAL_FRAMES) + TOTAL_FRAMES) % TOTAL_FRAMES;
    const t = f / FPS;
    const shot = shotAtFrame(f);
    const u = GLM.clamp((f - shot.f0) / Math.max(1, shot.f1 - shot.f0), 0, 1);
    const cam = SHOT_CAM[shot.id];
    const w = world;
    const cv = w.cleavageRig;

    const inBurrowSet = shot.set === 'BURROW';
    w.trenchRoot.visible = !inBurrowSet;
    w.triassicRoot.visible = inBurrowSet;

    let scanProgress = 0.0;
    let ribHighlight = 0.0;
    let isStorm = false;
    let stormMix = 0.0;

    if (!inBurrowSet) {
      // ---------- 1. SET A: KAROO EXPEDITION CAMP & PHYSICAL ROCK CLEAVAGE ----------
      setImaxLightingPreset('karoo_desert_sun', { fogStart: 13.5, fogRange: 35.0 });
      w.skyMat.uniforms.uStormMix.value = 0.0;
      w.skyMat.uniforms.uLightning.value = 0.0;
      w.lightningBolt.visible = false;

      let capLift = 0.0; // 0 = solid closed rock, 1 = upper cap cleaved & lifted clear!
      if (shot.id === 'S01' || shot.id === 'S12') {
        scanProgress = 0.0;
        capLift = 0.0;
      } else if (shot.id === 'S02') {
        scanProgress = GLM.smoothstep(2.56, 4.45, t);
        capLift = appleFluidEase(GLM.clamp((t - 2.68) / 2.65, 0.0, 1.0));
      } else if (shot.id === 'S11') {
        const sealProg = appleFluidEase(GLM.clamp((t - 30.88) / 1.85, 0.0, 1.0));
        scanProgress = 1.0 - sealProg;
        capLift = 1.0 - sealProg;
      } else {
        scanProgress = 1.0;
        capLift = 1.0;
      }

      const speciesHighlight = (shot.id === 'S03' || shot.id === 'S04') ? 0.95 : 0.38;
      ribHighlight = (shot.id === 'S05' || shot.id === 'S06')
        ? GLM.smoothstep(12.85, 13.38, t) * (1.0 - 0.15 * GLM.smoothstep(17.3, 18.0, t))
        : 0.0;

      w.fossilRockRig.update({ scanProgress, ribHighlight, speciesHighlight, time: t });

      // V7 Breakthrough: Once cleaved open (`capLift > 0.85`), hide murky `rockShell` completely and cradle
      // skeletons inside crisp carved `matrixBowl` so BOTH 3D skeletons read with 100% razor-sharp relief!
      cv.matrixBowl.visible = scanProgress > 0.08;
      w.fossilRockRig.rockShell.visible = scanProgress < 0.96;

      if (capLift > 0.01 && capLift < 0.99) {
        cv.upperCapMesh.visible = true;
        cv.upperCapMesh.position.set(0.08 * capLift, 0.62 * capLift, -0.22 * capLift);
        cv.upperCapMesh.rotation.set(-0.42 * capLift, 0.08 * capLift, 0.12 * capLift);
        cv.capMat.uniforms.uOpacity.value = 1.0 - GLM.smoothstep(0.58, 0.96, capLift);
        cv.capMat.uniforms.uSeamGlow.value = Math.sin(capLift * Math.PI);
      } else {
        cv.upperCapMesh.visible = false;
      }

      // Sequential 1 -> 2 -> 3 Rib Callus Ignition in S05 (1:1 locked to osteological clicks!)
      for (let idx = 0; idx < cv.indivCallusMats.length; idx++) {
        const m = cv.indivCallusMats[idx];
        const anchor = w.fossilRockRig.healingCallusAnchors[idx];
        let cAct = 0.0;
        if (shot.id === 'S05' || shot.id === 'S06') {
          const trig = ribClickTimes[idx] || 13.40;
          cAct = GLM.smoothstep(trig - 0.08, trig + 0.16, t);
          const pop = Math.exp(-Math.max(0, t - trig) * 4.5) * GLM.smoothstep(trig - 0.04, trig + 0.05, t);
          anchor.scale.set(1.55 + 0.42 * pop, 1.05 + 0.32 * pop, 1.15 + 0.32 * pop);
        } else {
          anchor.scale.set(1.55, 1.05, 1.15);
        }
        m.color.lerpColors(boneRestCol, boneHotCol, cAct);
        m.emissive.lerpColors(emRestCol, emHotCol, cAct);
        m.emissiveIntensity = 0.18 + cAct * 0.72 * (0.72 + 0.28 * Math.sin(t * 8.0 + idx));
      }

      // S03 Sequential Fresnel Anatomical Life-Silhouettes ("A mammal relative beside an amphibian")!
      const mamSil = shot.id === 'S03'
        ? GLM.smoothstep(7.06, 7.42, t) * (1.0 - GLM.smoothstep(8.25, 8.65, t))
        : 0.0;
      const ampSil = shot.id === 'S03'
        ? GLM.smoothstep(8.42, 8.78, t) * (1.0 - GLM.smoothstep(9.65, 10.05, t))
        : 0.0;
      cv.mammalGhost.visible = mamSil > 0.01;
      cv.mammalGhostMat.uniforms.uStrength.value = mamSil * 0.78;
      cv.amphibGhost.visible = ampSil > 0.01;
      cv.amphibGhostMat.uniforms.uStrength.value = ampSil * 0.78;

      if (shot.id === 'S06') {
        w.fossilRockRig.diagHalo.position.set(0.52, 0.09, 0.25);
        w.fossilRockRig.diagHaloMat.color.set('#e8b059');
      } else {
        w.fossilRockRig.diagHalo.position.set(0.27, 0.09, 0.24);
        w.fossilRockRig.diagHaloMat.color.set('#e63926');
      }

      const showSlice = scanProgress > 0.02 && scanProgress < 0.98;
      w.sunSliceCurtain.visible = showSlice;
      if (showSlice) {
        w.sunSliceCurtain.position.set(GLM.mix(-1.02, 1.02, scanProgress), 1.32, 0.0);
      }

      const timeBridgeFlare = shot.id === 'S06' ? GLM.smoothstep(17.65, 18.16, t) * 1.65 : 0.0;
      w.ambientLight.color.set('#8fb4d4');
      w.ambientLight.groundColor.set('#b87248');
      w.ambientLight.intensity = 0.92;
      w.keyLight.color.set('#ffe6be');
      w.keyLight.intensity = 3.40 + timeBridgeFlare;
      w.skyRimLight.color.set('#f2d4a4');
      w.skyRimLight.intensity = 2.50 + 0.90 * scanProgress;
      w.trenchBounceLight.color.set('#e89458');
      w.trenchBounceLight.intensity = 1.90;
      w.fossilCoreLight.color.set(ribHighlight > 0.2 ? '#ff8866' : '#ffcf7c');
      w.fossilCoreLight.intensity = 1.25 * scanProgress + 0.85 * ribHighlight;
      shadowFocus.set(0.0, 0.38, 0.15);
    } else {
      // ---------- 2. SET B: 250-MA EARLY TRIASSIC BURROW & LIVING BIOMECHANICS ----------
      w.sunSliceCurtain.visible = false;

      isStorm = (shot.id === 'S09' || shot.id === 'S10');
      stormMix = shot.id === 'S08'
        ? 0.44 * GLM.smoothstep(24.50, 25.53, t)
        : (isStorm ? GLM.smoothstep(25.40, 26.25, t) : 0.0);

      if (stormMix > 0.55) {
        setImaxLightingPreset('monsoon_storm', { fogStart: 12.0, fogRange: 32.0 });
      } else {
        setImaxLightingPreset('karoo_desert_sun', { fogStart: 13.5, fogRange: 35.0 });
      }

      const crawlProgress = shot.id === 'S07' ? GLM.smoothstep(0.03, 0.95, u) : 1.0;
      const surgeFront = isStorm ? GLM.smoothstep(25.45, 26.85, t) : 0.0;
      const fillLevel  = isStorm ? GLM.smoothstep(26.15, 28.85, t) : 0.0;
      const petrify    = shot.id === 'S10' ? GLM.smoothstep(28.72, 30.65, t) : 0.0;

      w.burrowRig.update({
        crawlProgress,
        dormancyAura: 0.0,
        floodSubmerge: fillLevel,
        time: t,
      });
      w.biomech.updateBiomechanics({
        time: t,
        crawlProgress,
        isStorm,
        surgeFront,
        fillLevel,
      });
      w.floodRig.update({
        active: isStorm,
        surgeFront,
        fillLevel,
        petrify,
        time: t,
      });

      const boltEnv1 = Math.exp(-Math.pow((t - 26.05) / 0.085, 2.0));
      const boltEnv2 = Math.exp(-Math.pow((t - 26.41) / 0.075, 2.0));
      const lightning = isStorm ? Math.max(boltEnv1, boltEnv2) * 2.75 : 0.0;

      w.skyMat.uniforms.uStormMix.value = stormMix;
      w.skyMat.uniforms.uLightning.value = lightning * 0.45;
      w.lightningBolt.visible = lightning > 0.22;
      w.lightningMat.opacity = GLM.clamp(lightning * 0.65, 0.0, 0.96);
      w.lightningHaloMat.opacity = GLM.clamp(lightning * 0.28, 0.0, 0.50);

      w.sunBlade.visible = stormMix < 0.75;
      w.ambientLight.intensity = GLM.mix(0.90, 0.56, stormMix);
      w.keyLight.color.setRGB(
        GLM.mix(1.0, 0.72, stormMix),
        GLM.mix(0.86, 0.80, stormMix),
        GLM.mix(0.62, 0.94, stormMix)
      );
      w.keyLight.intensity = GLM.mix(3.50, 2.10, stormMix) + lightning;
      w.skyRimLight.color.set(isStorm ? '#c8d6e6' : '#f2be78');
      w.skyRimLight.intensity = GLM.mix(2.65, 3.45, stormMix) + lightning * 0.85;
      w.trenchBounceLight.color.set(isStorm ? '#8c5a3c' : '#eb9452');
      w.trenchBounceLight.intensity = GLM.mix(2.25, 1.55, stormMix);
      w.fossilCoreLight.color.set('#ffd28c');
      w.fossilCoreLight.intensity = 1.45 * (1.0 - petrify * 0.45);
      shadowFocus.set(0.0, 0.55, 0.0);
    }

    w.updateWorldDynamics(t, isStorm, stormMix);
    w.dust.update(t);

    // ---------- 3. APPLE-FLUID NON-LINEAR CAMERA MOMENTUM ----------
    const e = shot.id === 'S04' ? GLM.smoothstep(0.0, 0.68, u) : appleFluidEase(u);
    if (opts.coverMode) {
      // Hero IMAX Poster Angle: shows Karoo sky + Tafelberg mesas + 4x4 + canopy + lifting rock cap + both skeletons + tools!
      camPos.set(0.02, 1.06, 3.16);
      camLook.set(0.0, 0.44, 0.04);
      world.fossilRockRig.rockShell.visible = false;
    } else {
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
    }
    const fov = GLM.mix(cam.from.fov, cam.to.fov, e);
    const dutch = GLM.mix(cam.from.dutch, cam.to.dutch, e);

    let breathAmp = shot.move === 'static' ? 0.008 : 0.018;
    if (shot.id === 'S01') breathAmp = 0.018 * GLM.smoothstep(0.0, 0.28, u);
    if (shot.id === 'S12') breathAmp = 0.0; // Exact Frame-0 lock!
    if (shot.id === 'S05') breathAmp = 0.007;

    const rigState = rig.apply({
      frame: f,
      pos: camPos,
      look: camLook,
      fov,
      dutchDeg: dutch,
      breathAmp,
      shutterBlurScale: 0.28,
    });

    // ---------- 4. 30 Hz SHADOW PASS (Zero-Flicker Law #3: Hide Volumetrics & Dust Puffs First!) ----------
    const sliceVis = w.sunSliceCurtain.visible;
    const bladeVis = w.sunBlade.visible;
    const rainVis = w.rainMesh.visible;
    const boltVis = w.lightningBolt.visible;
    const bdustVis = w.brushDustMesh.visible;
    const mgVis = cv.mammalGhost.visible;
    const agVis = cv.amphibGhost.visible;
    w.sunSliceCurtain.visible = false;
    w.sunBlade.visible = false;
    w.rainMesh.visible = false;
    w.lightningBolt.visible = false;
    w.brushDustMesh.visible = false;
    cv.mammalGhost.visible = false;
    cv.amphibGhost.visible = false;
    w.shadowRig.updateShadowMap(w.scene, shadowFocus, 5.4);
    w.sunSliceCurtain.visible = sliceVis;
    w.sunBlade.visible = bladeVis;
    w.rainMesh.visible = rainVis;
    w.lightningBolt.visible = boltVis;
    w.brushDustMesh.visible = bdustVis;
    cv.mammalGhost.visible = mgVis;
    cv.amphibGhost.visible = agVis;

    // ---------- 5. OPTICAL POST-FX & ARCHIVAL DOCUMENTARY CALLOUTS ----------
    const focusDist = Math.max(0.5, camera.position.distanceTo(tmpV.set(...cam.focus)));
    const inProtectedClimax = PROTECTED_WINDOWS.some(([w0, w1]) => t >= w0 && t < w1);

    let exposure = inBurrowSet ? 1.19 : 1.15;
    if (shot.id === 'S05') exposure = 1.25;
    if (shot.id === 'S09' || shot.id === 'S10') exposure = 1.23;

    let bloomAmt = 0.30;
    if (scanProgress > 0.05 && scanProgress < 0.95) bloomAmt = 0.40;
    if (shot.id === 'S05') bloomAmt = 0.36;

    callouts.length = 0;
    if (!inProtectedClimax) {
      if (shot.id === 'S03') {
        callouts.push({ ...projectWorldAnchor(-0.42, 0.40, -0.18), vDir: -1, vDist: 175, hDir: -1, label: 'THRINAXODON', value: 'MAMMAL RELATIVE', accent: '#E8B059' });
        callouts.push({ ...projectWorldAnchor( 0.34, 0.38,  0.20), vDir: +1, vDist: 155, hDir: +1, label: 'BROOMISTEGA', value: 'AMPHIBIAN',       accent: '#F4DFB8' });
      } else if (shot.id === 'S05') {
        callouts.push({ ...projectWorldAnchor(0.28, 0.41, 0.22), vDir: -1, vDist: 205, hDir: -1, label: 'RIBS #4–#6', value: 'HEALING CALLUSES', accent: '#E63926' });
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

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

export function drawKarooUltraHudV7(ctx, state, captions, opts = { showCaptions: true }) {
  const W = ctx.canvas.width;
  const H = ctx.canvas.height;
  const hud = state.hud;
  ctx.clearRect(0, 0, W, H);

  if (opts.coverMode) {
    ctx.save();
    const topG = ctx.createLinearGradient(0, 0, 0, 620);
    topG.addColorStop(0.0, 'rgba(30, 16, 9, 0.90)');
    topG.addColorStop(0.58, 'rgba(30, 16, 9, 0.48)');
    topG.addColorStop(1.0, 'rgba(30, 16, 9, 0.0)');
    ctx.fillStyle = topG;
    ctx.fillRect(0, 0, W, 620);

    ctx.textAlign = 'center';
    ctx.shadowColor = 'rgba(16, 8, 3, 0.94)';
    ctx.shadowBlur = 28;
    ctx.font = '700 88px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#FFF8EC';
    ctx.fillText('2 ANIMALS IN', W / 2, 205);

    ctx.font = '700 96px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#F2B857';
    ctx.fillText('ONE ROCK', W / 2, 310);

    roundRect(ctx, W / 2 - 280, 348, 560, 52, 8);
    ctx.fillStyle = 'rgba(32, 18, 10, 0.88)';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgba(242, 184, 87, 0.82)';
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.font = '700 23px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#F4E3C1';
    ctx.textBaseline = 'middle';
    ctx.fillText('KAROO EXPEDITION · 250 MILLION YRS', W / 2, 375);
    ctx.restore();
    return;
  }

  if (hud.inProtectedClimax) return;

  if (hud.shot === 'S01' || hud.shot === 'S02') {
    ctx.save();
    ctx.font = '700 22px "IBM Plex Mono", monospace';
    ctx.textAlign = 'left';
    ctx.fillStyle = 'rgba(34, 20, 12, 0.72)';
    roundRect(ctx, 64, 108, 535, 44, 6);
    ctx.fill();
    ctx.fillStyle = '#E8B059';
    ctx.fillRect(64, 108, 5, 44);
    ctx.fillStyle = '#F7EBD2';
    ctx.textBaseline = 'middle';
    ctx.fillText('KAROO BASIN, SOUTH AFRICA · BP/1/5558', 84, 131);
    ctx.restore();
  }

  for (const c of hud.callouts) {
    if (!c.visible) continue;
    ctx.save();
    const ax = GLM.clamp(c.x, 150, W - 150);
    const ay = GLM.clamp(c.y, 320, H - 540);
    const vd = c.vDist || 155;
    const ex = GLM.clamp(ax + c.hDir * 95, 220, W - 220);
    const ey = GLM.clamp(ay + c.vDir * vd, 250, H - 500);

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

  if (!opts.showCaptions) return;
  const active = captions.find((cp) => hud.time >= cp.t0 && hud.time <= cp.t1 + 0.08);
  if (!active) return;

  ctx.save();
  const cardW = 880;
  const cardH = 148;
  const cx = (W - cardW) * 0.5;
  const cy = 1495;

  roundRect(ctx, cx, cy, cardW, cardH, 12);
  ctx.fillStyle = 'rgba(24, 15, 10, 0.84)';
  ctx.fill();
  ctx.strokeStyle = 'rgba(232, 176, 89, 0.38)';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  ctx.fillStyle = active.accent;
  roundRect(ctx, cx, cy, 8, cardH, [12, 0, 0, 12]);
  ctx.fill();

  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  ctx.shadowColor = 'rgba(0, 0, 0, 0.68)';
  ctx.shadowBlur = 10;

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
