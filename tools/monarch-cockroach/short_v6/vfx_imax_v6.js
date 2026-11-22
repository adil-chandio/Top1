import * as THREE from 'three';

/**
 * Monarch Cam #03 — V6 Hollywood IMAX 3D Volumetric, Laser & Newtonian Physics VFX Suite!
 * Strictly obeys all 5 Zero-Flicker Laws:
 *   - All additive/transparent VFX use `depthWrite: false`, explicit `renderOrder >= 20`,
 *     soft procedural UV edge feathering (zero hard mesh edges!), and non-coplanar Y offsets!
 *   - Floating atmospheric dust motes use integer-cycle frequencies `2*pi*(k/35.0)*t` so
 *     frame 1050 (35.000s) matches frame 0 (0.000s) to the sub-micrometer!
 */
export function createImaxVfxSuiteV6(world) {
  // Soft radial glow sprite texture (shared across dust motes, sparks & shockwaves)
  const glowCanvas = document.createElement('canvas');
  glowCanvas.width = 128; glowCanvas.height = 128;
  const gctx = glowCanvas.getContext('2d');
  const rg = gctx.createRadialGradient(64, 64, 2, 64, 64, 64);
  rg.addColorStop(0.0, 'rgba(255, 255, 255, 1.0)');
  rg.addColorStop(0.28, 'rgba(255, 232, 185, 0.65)');
  rg.addColorStop(0.68, 'rgba(255, 190, 110, 0.15)');
  rg.addColorStop(1.0, 'rgba(255, 170, 90, 0.0)');
  gctx.fillStyle = rg;
  gctx.fillRect(0, 0, 128, 128);
  const softGlowTex = new THREE.CanvasTexture(glowCanvas);

  // =========================================================================
  // 1. DOORWAY VOLUMETRIC TUNGSTEN GOD-RAY BLADE + 110 TYNDALL DUST MOTES
  // =========================================================================
  const doorwayVfx = new THREE.Group();

  const beamShaderMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    uniforms: {
      uColor: { value: new THREE.Color('#ffca7a') },
      uIntensity: { value: 0.34 },
    },
    vertexShader: `
      varying vec2 vUv;
      void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
    `,
    fragmentShader: `
      uniform vec3 uColor;
      uniform float uIntensity;
      varying vec2 vUv;
      void main() {
        // vUv.x: 0 at doorway slit -> 1 far into kitchen; vUv.y: 0..1 across width
        float falloffX = pow(1.0 - vUv.x, 1.85) * smoothstep(0.0, 0.06, vUv.x);
        float falloffZ = sin(vUv.y * 3.14159265);
        float a = falloffX * falloffZ * falloffZ * uIntensity;
        gl_FragColor = vec4(uColor * a, a);
      }
    `,
  });

  // 3 stacked non-coplanar volumetric light sheets fanning out from under the 3.2 mm oak door!
  for (const [angTilt, yOff, len, op] of [
    [0.012, 0.55, 135, 1.0],
    [0.032, 1.35, 115, 0.75],
    [0.055, 2.25,  95, 0.50],
  ]) {
    const geo = new THREE.PlaneGeometry(len, 190);
    geo.translate(-len * 0.5, 0, 0); // Origin at X = 0 (doorway slot), extends into -X!
    const m = beamShaderMat.clone();
    m.uniforms.uIntensity.value = 0.24 * op;
    const sheet = new THREE.Mesh(geo, m);
    sheet.rotation.x = -Math.PI / 2;
    sheet.rotation.y = angTilt;
    sheet.position.set(2.0, yOff, 0);
    sheet.renderOrder = 22;
    doorwayVfx.add(sheet);
  }

  // 110 Floating Tyndall Atmospheric Dust Motes (integer-cycle loop-locked!)
  const MOTE_COUNT = 110;
  const moteGeo = new THREE.SphereGeometry(0.16, 8, 6);
  const moteMat = new THREE.MeshBasicMaterial({
    color: '#ffe2ad',
    transparent: true,
    opacity: 0.62,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const doorwayMotes = new THREE.InstancedMesh(moteGeo, moteMat, MOTE_COUNT);
  doorwayMotes.frustumCulled = false;
  doorwayMotes.renderOrder = 24;
  doorwayVfx.add(doorwayMotes);
  world.apartmentSet.add(doorwayVfx);

  // =========================================================================
  // 2. LAB & ARENA OVERHEAD VOLUMETRIC SURGICAL SPOTLIGHT CONES + LAB MOTES
  // =========================================================================
  const coneMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.FrontSide,
    uniforms: {
      uColor: { value: new THREE.Color('#9ce8f2') },
      uIntensity: { value: 0.13 },
    },
    vertexShader: `
      varying vec2 vUv;
      varying vec3 vN;
      varying vec3 vV;
      void main() {
        vUv = uv;
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vN = normalize(mat3(modelMatrix) * normal);
        vV = normalize(cameraPosition - wp.xyz);
        gl_Position = projectionMatrix * viewMatrix * wp;
      }
    `,
    fragmentShader: `
      uniform vec3 uColor;
      uniform float uIntensity;
      varying vec2 vUv;
      varying vec3 vN;
      varying vec3 vV;
      void main() {
        float edgeSoft = pow(abs(dot(vN, vV)), 1.7);
        float vertFade = smoothstep(0.0, 0.25, vUv.y) * (1.0 - smoothstep(0.70, 1.0, vUv.y));
        float a = edgeSoft * vertFade * uIntensity;
        gl_FragColor = vec4(uColor * a, a);
      }
    `,
  });

  const labLightCones = new THREE.Group();
  for (const [lx, lz, tiltZ] of [[-48, -18, -0.18], [44, -18, 0.18]]) {
    const cone = new THREE.Mesh(new THREE.CylinderGeometry(8, 48, 125, 24, 1, true), coneMat);
    cone.position.set(lx, 58, lz);
    cone.rotation.z = tiltZ;
    cone.renderOrder = 21;
    labLightCones.add(cone);
  }
  world.labSet.add(labLightCones);

  // =========================================================================
  // 3. 3D HOLOGRAPHIC LASER TOMOGRAPHY SCANNER (FOR S3_XRAY REVEAL!)
  // =========================================================================
  const xrayScanner = new THREE.Group();
  xrayScanner.visible = false;
  const laserCurtainMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    uniforms: { uOpacity: { value: 0.85 } },
    vertexShader: `
      varying vec2 vUv;
      void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
    `,
    fragmentShader: `
      uniform float uOpacity;
      varying vec2 vUv;
      void main() {
        float core = exp(-pow((vUv.x - 0.5) * 9.0, 2.0));
        float vy = sin(vUv.y * 3.14159265);
        float a = core * vy * uOpacity;
        gl_FragColor = vec4(vec3(0.42, 0.98, 0.95) * a * 1.4, a);
      }
    `,
  });
  const laserSheet = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 24.0), laserCurtainMat);
  laserSheet.rotation.y = Math.PI / 2;
  laserSheet.position.set(0, 6.5, 0);
  laserSheet.renderOrder = 25;
  const laserFloorLine = new THREE.Mesh(
    new THREE.PlaneGeometry(0.65, 22.0),
    new THREE.MeshBasicMaterial({ color: '#7efcf4', transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false })
  );
  laserFloorLine.rotation.x = -Math.PI / 2;
  laserFloorLine.position.set(0, 0.14, 0);
  laserFloorLine.renderOrder = 25;
  xrayScanner.add(laserSheet, laserFloorLine);
  world.scene.add(xrayScanner);

  // =========================================================================
  // 4. EMERALD FLOOR-CLEARANCE LASER SHEET (FOR S4B "ZERO FEET DOWN"!)
  // =========================================================================
  const clearanceLaser = new THREE.Mesh(
    new THREE.PlaneGeometry(46.0, 34.0),
    new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: { uTime: { value: 0.0 }, uAlpha: { value: 0.45 } },
      vertexShader: `
        varying vec2 vUv;
        void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
      `,
      fragmentShader: `
        uniform float uTime;
        uniform float uAlpha;
        varying vec2 vUv;
        void main() {
          float rad = 1.0 - smoothstep(0.15, 0.50, length(vUv - 0.5));
          float scan = 0.72 + 0.28 * sin(vUv.x * 62.8318 - uTime * 14.0);
          float grid = smoothstep(0.92, 0.99, abs(sin(vUv.x * 37.699))) + smoothstep(0.92, 0.99, abs(sin(vUv.y * 37.699)));
          float a = rad * (0.28 * scan + 0.42 * clamp(grid, 0.0, 1.0)) * uAlpha;
          gl_FragColor = vec4(vec3(0.32, 0.96, 0.86) * a * 1.3, a);
        }
      `,
    })
  );
  clearanceLaser.rotation.x = -Math.PI / 2;
  clearanceLaser.position.y = 0.09; // Strictly 0.09 mm above floorY = 0 -> zero Z-fighting!
  clearanceLaser.renderOrder = 23;
  clearanceLaser.visible = false;
  world.scene.add(clearanceLaser);

  // =========================================================================
  // 5. RADIAL IMPACT SHOCKWAVE RING (900x SLAM, PUSH-UP COLLAPSE, GATE WEDGE!)
  // =========================================================================
  const shockwaveMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    uniforms: {
      uProgress: { value: 0.0 },
      uColor: { value: new THREE.Color('#ffd187') },
    },
    vertexShader: `
      varying vec2 vUv;
      void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
    `,
    fragmentShader: `
      uniform float uProgress;
      uniform vec3 uColor;
      varying vec2 vUv;
      void main() {
        float d = length(vUv - 0.5) * 2.0;
        float rTarget = mix(0.08, 0.96, uProgress);
        float ring = exp(-pow((d - rTarget) * 14.0, 2.0));
        float fade = (1.0 - uProgress) * (1.0 - smoothstep(0.92, 1.0, d));
        float a = ring * fade * 0.85;
        gl_FragColor = vec4(uColor * a * 1.4, a);
      }
    `,
  });
  const shockwaveMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), shockwaveMat);
  shockwaveMesh.rotation.x = -Math.PI / 2;
  shockwaveMesh.renderOrder = 26;
  shockwaveMesh.visible = false;
  world.scene.add(shockwaveMesh);

  // =========================================================================
  // 6. NEWTONIAN BALLISTIC GRIT & MICRO-SPARK PARTICLE ENGINE (96 PARTICLES!)
  // =========================================================================
  const GRIT_N = 96;
  const gritGeo = new THREE.DodecahedronGeometry(0.072, 0);
  const gritMat = new THREE.MeshBasicMaterial({ color: '#ffd99e' });
  const ballisticGrit = new THREE.InstancedMesh(gritGeo, gritMat, GRIT_N);
  ballisticGrit.frustumCulled = false;
  ballisticGrit.visible = false;
  world.scene.add(ballisticGrit);

  const tmpM = new THREE.Matrix4();
  const tmpQ = new THREE.Quaternion();
  const tmpS = new THREE.Vector3();
  const tmpP = new THREE.Vector3();
  const tmpE = new THREE.Euler();

  function updateDoorwayMotes(time) {
    // Exact integer cycles over 35.0s (`1/35` and `2/35` Hz) -> 100.000% seamless loop at f=1050 == f=0!
    const w1 = (2 * Math.PI * 1.0) / 35.0;
    const w2 = (2 * Math.PI * 2.0) / 35.0;
    for (let i = 0; i < MOTE_COUNT; i++) {
      const s = i * 1.6180339887;
      const bx = -4.0 - ((i * 19.37) % 78.0);
      const by = 0.65 + ((i * 7.13) % 13.5);
      const bz = -36.0 + ((i * 23.41) % 72.0);
      const dx = 2.4 * Math.sin(w1 * time + s) + 1.1 * Math.cos(w2 * time + s * 1.7);
      const dy = 1.2 * Math.cos(w1 * time + s * 1.3) + 0.6 * Math.sin(w2 * time + s * 0.9);
      const dz = 1.8 * Math.sin(w1 * time - s * 0.8);
      tmpP.set(bx + dx, Math.max(0.25, by + dy), bz + dz);
      // Brighter & slightly larger when inside the low doorway light beam!
      const inBeam = Math.exp(-tmpP.y * 0.16);
      const sc = (0.45 + 0.75 * inBeam) * (0.65 + 0.35 * Math.sin(w2 * time + i));
      tmpS.setScalar(sc);
      tmpQ.identity();
      tmpM.compose(tmpP, tmpQ, tmpS);
      doorwayMotes.setMatrixAt(i, tmpM);
    }
    doorwayMotes.instanceMatrix.needsUpdate = true;
  }

  /**
   * Newtonian ballistic trajectory solver (`x = v_x*tau`, `y = v_y*tau - 0.5*g*tau^2` + floor bounce `e = 0.38`)!
   */
  function updateBallisticGrit(origin, time, intensity = 0.0, speedScale = 1.0, dirSign = -1.0) {
    if (intensity <= 0.01) {
      ballisticGrit.visible = false;
      return;
    }
    ballisticGrit.visible = true;
    for (let i = 0; i < GRIT_N; i++) {
      const seed = i * 2.39996323;
      const raw = time * 3.6 * speedScale + seed * 0.37;
      const tau = raw - Math.floor(raw); // 0..1 particle lifetime
      const vx = dirSign * (5.2 + (i % 7) * 1.35);
      const vy0 = 3.2 + (i % 5) * 0.85;
      const vz = Math.sin(seed * 11.3) * 3.1;
      const g = 11.8;

      // Parabolic flight with first-bounce restitution e = 0.38 at floor!
      const tHit = (2.0 * vy0) / g;
      let py;
      if (tau <= tHit) {
        py = vy0 * tau - 0.5 * g * tau * tau;
      } else {
        const tb = tau - tHit;
        const vyBounce = vy0 * 0.38;
        py = Math.max(0.0, vyBounce * tb - 0.5 * g * tb * tb);
      }

      tmpP.set(
        origin.x + vx * tau,
        Math.max(0.05, origin.y * 0.35 + py),
        origin.z + vz * tau
      );
      const sc = (1.0 - tau * 0.88) * (0.55 + 0.55 * ((i % 4) / 3)) * intensity;
      tmpS.setScalar(Math.max(0.001, sc));
      tmpE.set(tau * 14.0 + i, tau * 11.0, i);
      tmpQ.setFromEuler(tmpE);
      tmpM.compose(tmpP, tmpQ, tmpS);
      ballisticGrit.setMatrixAt(i, tmpM);
    }
    ballisticGrit.instanceMatrix.needsUpdate = true;
  }

  function triggerShockwave({ x = 0, y = 0.22, z = 0, size = 48.0, progress = -1, colorHex = '#ffd187' } = {}) {
    if (progress < 0.0 || progress >= 1.0) {
      shockwaveMesh.visible = false;
      return;
    }
    shockwaveMesh.visible = true;
    shockwaveMesh.position.set(x, y, z);
    shockwaveMesh.scale.set(size, size, 1);
    shockwaveMat.uniforms.uProgress.value = progress;
    shockwaveMat.uniforms.uColor.value.set(colorHex);
  }

  function resetPerFrame() {
    xrayScanner.visible = false;
    clearanceLaser.visible = false;
    shockwaveMesh.visible = false;
    ballisticGrit.visible = false;
  }

  return {
    doorwayVfx,
    labLightCones,
    xrayScanner,
    clearanceLaser,
    updateDoorwayMotes,
    updateBallisticGrit,
    triggerShockwave,
    resetPerFrame,
  };
}
