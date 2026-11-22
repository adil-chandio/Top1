import * as THREE from 'three';

/**
 * Monarch V6 Hollywood IMAX Cinema SDK — Reusable Volumetric God-Rays, Laser Tomography,
 * Loop-Locked Tyndall Dust Motes, Radial Shockwaves & Newtonian Ballistic VFX (`vfx_physics_sdk.js`).
 */

export function createVolumetricLightBlade({
  color = '#ffca7a',
  intensity = 0.24,
  length = 135,
  width = 190,
  originX = 2.0,
  renderOrder = 22,
} = {}) {
  const group = new THREE.Group();
  const baseMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    uniforms: {
      uColor: { value: new THREE.Color(color) },
      uIntensity: { value: intensity },
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
        float falloffX = pow(1.0 - vUv.x, 1.85) * smoothstep(0.0, 0.06, vUv.x);
        float falloffZ = sin(vUv.y * 3.14159265);
        float a = falloffX * falloffZ * falloffZ * uIntensity;
        gl_FragColor = vec4(uColor * a, a);
      }
    `,
  });

  for (const [angTilt, yOff, lenScale, op] of [
    [0.012, 0.55, 1.00, 1.00],
    [0.032, 1.35, 0.85, 0.75],
    [0.055, 2.25, 0.70, 0.50],
  ]) {
    const L = length * lenScale;
    const geo = new THREE.PlaneGeometry(L, width);
    geo.translate(-L * 0.5, 0, 0);
    const m = baseMat.clone();
    m.uniforms.uIntensity.value = intensity * op;
    const sheet = new THREE.Mesh(geo, m);
    sheet.rotation.x = -Math.PI / 2;
    sheet.rotation.y = angTilt;
    sheet.position.set(originX, yOff, 0);
    sheet.renderOrder = renderOrder;
    group.add(sheet);
  }
  return group;
}

export function createVolumetricSpotlightCone({
  color = '#9ce8f2',
  intensity = 0.13,
  topRadius = 8,
  bottomRadius = 48,
  height = 125,
  renderOrder = 21,
} = {}) {
  const mat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.FrontSide,
    uniforms: {
      uColor: { value: new THREE.Color(color) },
      uIntensity: { value: intensity },
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
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(topRadius, bottomRadius, height, 24, 1, true), mat);
  mesh.renderOrder = renderOrder;
  return mesh;
}

/**
 * Integer-cycle loop-locked 3D Tyndall floating dust motes (`f = N` matches `f = 0` to 0.000000!)
 */
export function createLoopLockedDustMotes({
  count = 110,
  radius = 0.16,
  color = '#ffe2ad',
  loopDurationS = 35.0,
  bounds = { x0: -82, xSpan: 78, y0: 0.65, ySpan: 13.5, z0: -36, zSpan: 72 },
  renderOrder = 24,
} = {}) {
  const mesh = new THREE.InstancedMesh(
    new THREE.SphereGeometry(radius, 8, 6),
    new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.62,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
    count
  );
  mesh.frustumCulled = false;
  mesh.renderOrder = renderOrder;

  const tmpM = new THREE.Matrix4();
  const tmpQ = new THREE.Quaternion();
  const tmpS = new THREE.Vector3();
  const tmpP = new THREE.Vector3();

  function update(timeS) {
    const w1 = (2 * Math.PI * 1.0) / loopDurationS;
    const w2 = (2 * Math.PI * 2.0) / loopDurationS;
    for (let i = 0; i < count; i++) {
      const s = i * 1.6180339887;
      const bx = bounds.x0 + ((i * 19.37) % bounds.xSpan);
      const by = bounds.y0 + ((i * 7.13) % bounds.ySpan);
      const bz = bounds.z0 + ((i * 23.41) % bounds.zSpan);
      const dx = 2.4 * Math.sin(w1 * timeS + s) + 1.1 * Math.cos(w2 * timeS + s * 1.7);
      const dy = 1.2 * Math.cos(w1 * timeS + s * 1.3) + 0.6 * Math.sin(w2 * timeS + s * 0.9);
      const dz = 1.8 * Math.sin(w1 * timeS - s * 0.8);
      tmpP.set(bx + dx, Math.max(0.25, by + dy), bz + dz);
      const sc = 0.55 + 0.45 * Math.sin(w2 * timeS + i);
      tmpS.setScalar(sc);
      tmpQ.identity();
      tmpM.compose(tmpP, tmpQ, tmpS);
      mesh.setMatrixAt(i, tmpM);
    }
    mesh.instanceMatrix.needsUpdate = true;
  }

  return { mesh, update };
}

export function createLaserTomographyScanner({ width = 24.0, height = 16.0, color = '#7efcf4' } = {}) {
  const group = new THREE.Group();
  group.visible = false;
  const colVec = new THREE.Color(color);
  const curtain = new THREE.Mesh(
    new THREE.PlaneGeometry(2.4, width),
    new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      uniforms: { uColor: { value: colVec }, uOpacity: { value: 0.85 } },
      vertexShader: `
        varying vec2 vUv;
        void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
      `,
      fragmentShader: `
        uniform vec3 uColor;
        uniform float uOpacity;
        varying vec2 vUv;
        void main() {
          float core = exp(-pow((vUv.x - 0.5) * 9.0, 2.0));
          float vy = sin(vUv.y * 3.14159265);
          float a = core * vy * uOpacity;
          gl_FragColor = vec4(uColor * a * 1.4, a);
        }
      `,
    })
  );
  curtain.rotation.y = Math.PI / 2;
  curtain.position.set(0, height * 0.42, 0);
  curtain.renderOrder = 25;

  const floorLine = new THREE.Mesh(
    new THREE.PlaneGeometry(0.65, width * 0.92),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false })
  );
  floorLine.rotation.x = -Math.PI / 2;
  floorLine.position.set(0, 0.14, 0);
  floorLine.renderOrder = 25;
  group.add(curtain, floorLine);
  return group;
}

export function createClearanceLaserGrid({ width = 46.0, depth = 34.0, floorY = 0.0 } = {}) {
  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(width, depth),
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
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = floorY + 0.09;
  mesh.renderOrder = 23;
  mesh.visible = false;
  return mesh;
}

export function createImpactShockwaveRing() {
  const mat = new THREE.ShaderMaterial({
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
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat);
  mesh.rotation.x = -Math.PI / 2;
  mesh.renderOrder = 26;
  mesh.visible = false;

  function trigger({ x = 0, y = 0.22, z = 0, size = 48.0, progress = -1, colorHex = '#ffd187' } = {}) {
    if (progress < 0.0 || progress >= 1.0) {
      mesh.visible = false;
      return;
    }
    mesh.visible = true;
    mesh.position.set(x, y, z);
    mesh.scale.set(size, size, 1);
    mat.uniforms.uProgress.value = progress;
    mat.uniforms.uColor.value.set(colorHex);
  }

  return { mesh, trigger };
}

/**
 * Newtonian Parabolic Ballistic Debris/Spark System (`y = v0*t - 0.5*g*t^2` + restitution floor bounce)
 */
export function createBallisticParticleSystem({
  count = 96,
  radius = 0.072,
  color = '#ffd99e',
  gravity = 11.8,
  restitution = 0.38,
  floorY = 0.0,
} = {}) {
  const mesh = new THREE.InstancedMesh(
    new THREE.DodecahedronGeometry(radius, 0),
    new THREE.MeshBasicMaterial({ color }),
    count
  );
  mesh.frustumCulled = false;
  mesh.visible = false;

  const tmpM = new THREE.Matrix4();
  const tmpQ = new THREE.Quaternion();
  const tmpS = new THREE.Vector3();
  const tmpP = new THREE.Vector3();
  const tmpE = new THREE.Euler();

  function update(origin, timeS, { intensity = 0.0, speedScale = 1.0, dirSign = -1.0 } = {}) {
    if (intensity <= 0.01) {
      mesh.visible = false;
      return;
    }
    mesh.visible = true;
    for (let i = 0; i < count; i++) {
      const seed = i * 2.39996323;
      const raw = timeS * 3.6 * speedScale + seed * 0.37;
      const tau = raw - Math.floor(raw);
      const vx = dirSign * (5.2 + (i % 7) * 1.35);
      const vy0 = 3.2 + (i % 5) * 0.85;
      const vz = Math.sin(seed * 11.3) * 3.1;

      const tHit = (2.0 * vy0) / gravity;
      let py;
      if (tau <= tHit) {
        py = vy0 * tau - 0.5 * gravity * tau * tau;
      } else {
        const tb = tau - tHit;
        const vyBounce = vy0 * restitution;
        py = Math.max(0.0, vyBounce * tb - 0.5 * gravity * tb * tb);
      }

      tmpP.set(
        origin.x + vx * tau,
        Math.max(floorY + 0.05, origin.y * 0.35 + py),
        origin.z + vz * tau
      );
      const sc = (1.0 - tau * 0.88) * (0.55 + 0.55 * ((i % 4) / 3)) * intensity;
      tmpS.setScalar(Math.max(0.001, sc));
      tmpE.set(tau * 14.0 + i, tau * 11.0, i);
      tmpQ.setFromEuler(tmpE);
      tmpM.compose(tmpP, tmpQ, tmpS);
      mesh.setMatrixAt(i, tmpM);
    }
    mesh.instanceMatrix.needsUpdate = true;
  }

  return { mesh, update };
}
