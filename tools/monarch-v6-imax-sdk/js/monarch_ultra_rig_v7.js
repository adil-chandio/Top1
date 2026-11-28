/**
 * Monarch V7 Autonomous Ultra Cinema SDK — Procedural Biomechanics, Camera Physics & Volumetric Shader Rig!
 * Exposes `window.MONARCH_V7_RIG` for deterministic frame-indexed (`f` @ 30fps) cinema animation:
 *   1. Apple-Fluid Quintic / Cubic-Hermite Camera Momentum + Critically/Under-Damped Impact Recoil
 *   2. Analytical Law-of-Cosines 2-Bone Limb IK + Traveling S-Wave Spine Undulation + Injured-Flank Limp Gait
 *   3. Superposed Thoracic/Gular Breathing, Blinking Nictitating Eyelids & Muzzle/Whisker Micro-Expressions
 *   4. Wind-Driven Traveling-Wave Cloth / Survey-Ribbon Vertex Physics
 *   5. Volumetric Sun-Shaft (God-Ray) & Fresnel Subsurface-Silhouette Shader Helpers
 */
(function () {
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const lerp = (a, b, u) => a + (b - a) * u;

  // 1. NON-LINEAR CAMERA MOMENTUM & IMPACT RECOIL PHYSICS
  function smooth3(x) {
    const u = clamp01(x);
    return u * u * (3 - 2 * u);
  }

  function quintic5(x) {
    const u = clamp01(x);
    return u * u * u * (u * (u * 6 - 15) + 10);
  }

  /** Fast kinetic snap-in -> silky floating glide -> cushioned settle (Zack D. / Apple fluid feel) */
  function cinematicSnapGlide(x) {
    const u = clamp01(x);
    return 1 - Math.pow(1 - u, 2.8) * (1 + 1.8 * u * (1 - u));
  }

  /** Damped harmonic oscillator impulse (`t >= 0` seconds after impact) */
  function dampedImpactRecoil(dt, freqHz = 11.5, decay = 7.2) {
    if (dt <= 0 || dt > 1.6) return 0;
    return Math.exp(-decay * dt) * Math.sin(2 * Math.PI * freqHz * dt);
  }

  // 2. ANALYTICAL LAW-OF-COSINES 2-BONE LIMB IK + STRIDE ARC GENERATOR
  function solveTwoBoneIK(hipPos, footPos, L1, L2, bendOutSign = 1) {
    const dx = footPos.x - hipPos.x;
    const dy = footPos.y - hipPos.y;
    const dz = footPos.z - hipPos.z;
    const distRaw = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1e-5;
    const maxReach = (L1 + L2) * 0.985;
    const minReach = Math.abs(L1 - L2) * 1.05 + 0.004;
    const d = Math.max(minReach, Math.min(maxReach, distRaw));

    const cosA = Math.max(-1, Math.min(1, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)));
    const h = L1 * Math.sqrt(Math.max(0, 1 - cosA * cosA));
    const along = (L1 * cosA) / distRaw;

    // Outward/upward anatomical knee/elbow pole vector
    const horizLen = Math.sqrt(dx * dx + dz * dz) || 1e-4;
    const outX = (-dz / horizLen) * bendOutSign * 0.65;
    const outZ = (dx / horizLen) * bendOutSign * 0.65;
    const outY = 0.76;
    const oNorm = Math.sqrt(outX * outX + outY * outY + outZ * outZ);

    return {
      x: hipPos.x + dx * along + (outX / oNorm) * h,
      y: hipPos.y + dy * along + (outY / oNorm) * h,
      z: hipPos.z + dz * along + (outZ / oNorm) * h,
    };
  }

  /**
   * Computes quadruped crawling foot target with alternating diagonal gait + optional injured-side limp!
   * `phase01`: 0..0.55 = ground stance (pushes backward in world space -> zero foot sliding!),
   *            0.55..1.0 = swing arc (`sin(pi * s)` vertical clearance lift!).
   */
  function evalQuadrupedFootStep(cyclePhase, strideLen, liftHeight, isInjuredSide = false) {
    const p = ((cyclePhase % 1) + 1) % 1;
    const stanceEnd = isInjuredSide ? 0.66 : 0.54; // injured side guards ribs -> shorter, lower swing!
    const effStride = isInjuredSide ? strideLen * 0.68 : strideLen;
    const effLift = isInjuredSide ? liftHeight * 0.52 : liftHeight;

    if (p < stanceEnd) {
      const u = p / stanceEnd;
      return {
        fwdOffset: lerp(effStride * 0.5, -effStride * 0.5, u),
        liftY: 0,
        groundContact: 1 - Math.abs(u - 0.5) * 2,
      };
    }
    const s = (p - stanceEnd) / (1 - stanceEnd);
    return {
      fwdOffset: lerp(-effStride * 0.5, effStride * 0.5, smooth3(s)),
      liftY: Math.sin(Math.PI * s) * effLift,
      groundContact: 0,
    };
  }

  // 3. TRAVELING S-WAVE VERTEBRATE SPINE + SUPERPOSED BREATHING & BLINKING
  function evalTravelingSpineLateral(uAlongSpine, gaitCycle, amp = 0.045, injuredBias = 0) {
    // Head (`u=0`) stabilized somewhat for gaze; trunk & tail (`u -> 1`) propagate full traveling S-wave
    const env = 0.35 + 0.65 * Math.pow(clamp01(uAlongSpine), 0.85);
    const wave = Math.sin(uAlongSpine * Math.PI * 2.15 - gaitCycle * Math.PI * 2.0);
    return wave * amp * env + injuredBias * Math.sin(uAlongSpine * Math.PI) * 0.018;
  }

  /** Natural double-blink & sleepy half-lid schedule (returns eyelid closure 0 = open, 1 = shut) */
  function evalNaturalBlink(tSec, blinkCentersSec, halfSleepBase = 0) {
    let close = halfSleepBase;
    for (let i = 0; i < blinkCentersSec.length; i++) {
      const dt = Math.abs(tSec - blinkCentersSec[i]);
      if (dt < 0.13) {
        const b = Math.cos((dt / 0.13) * Math.PI * 0.5);
        close = Math.max(close, b * b);
      }
    }
    return clamp01(close);
  }

  // 4. TRAVELING-WAVE CLOTH & SURVEY RIBBON FLUTTER
  function displaceRibbonPoint(uAlong, tSec, gustAmp = 1.0, seedPhase = 0) {
    const pin = Math.pow(clamp01(uAlong), 1.35);
    const xWave = Math.sin(tSec * 5.8 - uAlong * 4.2 + seedPhase) * 0.032 * pin * gustAmp;
    const ySag = -Math.pow(uAlong, 1.5) * 0.045 + Math.cos(tSec * 7.4 - uAlong * 5.5 + seedPhase) * 0.014 * pin * gustAmp;
    const zWave = Math.cos(tSec * 4.3 - uAlong * 3.1 + seedPhase * 1.7) * 0.022 * pin * gustAmp;
    return { dx: xWave, dy: ySag, dz: zWave };
  }

  window.MONARCH_V7_RIG = {
    clamp01,
    lerp,
    smooth3,
    quintic5,
    cinematicSnapGlide,
    dampedImpactRecoil,
    solveTwoBoneIK,
    evalQuadrupedFootStep,
    evalTravelingSpineLateral,
    evalNaturalBlink,
    displaceRibbonPoint,
  };
})();
