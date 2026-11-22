import * as THREE from 'three';

/**
 * Monarch V6 Hollywood IMAX Cinema SDK — Unified GLSL PBR, Procedural Sobel Normal
 * Textures & 30 Hz Light-Space Texel-Snapped Shadow Engine (`pbr_shadow_sdk.js`).
 *
 * Enforces Zero-Flicker Laws 1, 2 & 3 out-of-the-box:
 *   - Supports `#ifdef USE_SKINNING` (53-bone `.glb` humans) & `#ifdef USE_INSTANCING`
 *   - Enforces `depthWrite: false` and `uReceiveShadow: 0.0` automatically on transparent materials
 *   - Smooth shadow-frustum border fade + 5-tap rotated PCF shadow filter + 30 Hz light-space texel snap
 */

export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function buildNormalFromCanvas(srcCanvas, strength = 2.4, size = 512) {
  const work = document.createElement('canvas');
  work.width = size;
  work.height = size;
  const sctx = work.getContext('2d', { willReadFrequently: true });
  sctx.drawImage(srcCanvas, 0, 0, size, size);
  const src = sctx.getImageData(0, 0, size, size).data;

  const outCanvas = document.createElement('canvas');
  outCanvas.width = size;
  outCanvas.height = size;
  const octx = outCanvas.getContext('2d');
  const outImg = octx.createImageData(size, size);
  const dst = outImg.data;

  const lumAt = (x, y) => {
    const xi = (x + size) % size;
    const yi = (y + size) % size;
    const idx = (yi * size + xi) * 4;
    return (0.299 * src[idx] + 0.587 * src[idx + 1] + 0.114 * src[idx + 2]) / 255.0;
  };

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const tl = lumAt(x - 1, y - 1), t = lumAt(x, y - 1), tr = lumAt(x + 1, y - 1);
      const l  = lumAt(x - 1, y),                         r  = lumAt(x + 1, y);
      const bl = lumAt(x - 1, y + 1), b = lumAt(x, y + 1), br = lumAt(x + 1, y + 1);
      const dx = ((tr + 2 * r + br) - (tl + 2 * l + bl)) * strength;
      const dy = ((bl + 2 * b + br) - (tl + 2 * t + tr)) * strength;
      const inv = 1.0 / Math.hypot(dx, dy, 1.0);
      const idx = (y * size + x) * 4;
      dst[idx]     = Math.round(((-dx * inv) * 0.5 + 0.5) * 255);
      dst[idx + 1] = Math.round(((-dy * inv) * 0.5 + 0.5) * 255);
      dst[idx + 2] = Math.round(((1.0 * inv) * 0.5 + 0.5) * 255);
      dst[idx + 3] = 255;
    }
  }
  octx.putImageData(outImg, 0, 0);
  const tex = new THREE.CanvasTexture(outCanvas);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return tex;
}

export function buildOpticalBreadboardTexture(seed = 808) {
  const S = 512;
  const c = document.createElement('canvas');
  c.width = S;
  c.height = S;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#1b1e22';
  ctx.fillRect(0, 0, S, S);
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
  ctx.lineWidth = 1;
  for (let y = 0; y < S; y += 3) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(S, y); ctx.stroke();
  }
  const step = S / 8;
  for (let gy = 0; gy < 8; gy++) {
    for (let gx = 0; gx < 8; gx++) {
      const cx = (gx + 0.5) * step;
      const cy = (gy + 0.5) * step;
      ctx.fillStyle = '#343a40';
      ctx.beginPath(); ctx.arc(cx, cy, 7.2, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#090b0d';
      ctx.beginPath(); ctx.arc(cx, cy, 4.6, 0, Math.PI * 2); ctx.fill();
    }
  }
  const albedo = new THREE.CanvasTexture(c);
  albedo.wrapS = albedo.wrapT = THREE.RepeatWrapping;
  const normal = buildNormalFromCanvas(c, 2.2, 512);
  return { albedo, normal };
}

export function buildWoodPlankTexture(seed = 7721) {
  const S = 1024;
  const c = document.createElement('canvas');
  c.width = S;
  c.height = S;
  const ctx = c.getContext('2d');
  const rng = mulberry32(seed);
  ctx.fillStyle = '#7c5130';
  ctx.fillRect(0, 0, S, S);
  const planks = 6;
  const ph = S / planks;
  for (let p = 0; p < planks; p++) {
    const y0 = p * ph;
    const tone = 0.88 + rng() * 0.24;
    ctx.fillStyle = `rgb(${Math.round(132 * tone)}, ${Math.round(86 * tone)}, ${Math.round(49 * tone)})`;
    ctx.fillRect(0, y0, S, ph);
    for (let g = 0; g < 95; g++) {
      const gy = y0 + rng() * ph;
      ctx.strokeStyle = rng() > 0.45 ? 'rgba(54, 30, 14, 0.18)' : 'rgba(186, 132, 80, 0.15)';
      ctx.lineWidth = 0.8 + rng() * 1.8;
      ctx.beginPath();
      ctx.moveTo(0, gy);
      ctx.bezierCurveTo(S * 0.33, gy + (rng() - 0.5) * 9, S * 0.66, gy + (rng() - 0.5) * 9, S, gy + (rng() - 0.5) * 4);
      ctx.stroke();
    }
    ctx.fillStyle = 'rgba(24, 12, 5, 0.72)';
    ctx.fillRect(0, y0, S, 3.0);
  }
  const albedo = new THREE.CanvasTexture(c);
  albedo.wrapS = albedo.wrapT = THREE.RepeatWrapping;
  const normal = buildNormalFromCanvas(c, 2.8, 512);
  return { albedo, normal };
}

export function buildStoneGritTexture({ grainCount = 3200, grainRadius = 2.3, baseHex = '#2f2a26', seed = 404 } = {}) {
  const S = 512;
  const c = document.createElement('canvas');
  c.width = S;
  c.height = S;
  const ctx = c.getContext('2d');
  const rng = mulberry32(seed);
  ctx.fillStyle = baseHex;
  ctx.fillRect(0, 0, S, S);
  for (let i = 0; i < grainCount; i++) {
    const x = rng() * S, y = rng() * S;
    const r = grainRadius * (0.55 + rng() * 0.95);
    ctx.fillStyle = rng() > 0.45 ? 'rgba(220, 212, 200, 0.26)' : 'rgba(12, 10, 9, 0.34)';
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
  }
  const albedo = new THREE.CanvasTexture(c);
  albedo.wrapS = albedo.wrapT = THREE.RepeatWrapping;
  const normal = buildNormalFromCanvas(c, 3.2, 512);
  return { albedo, normal };
}

export function buildMetricRulerTexture() {
  const W = 1024, H = 128;
  const c = document.createElement('canvas');
  c.width = W;
  c.height = H;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#161a1e';
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#d8c39e';
  for (let i = 0; i < 100; i++) {
    const x = (i / 100) * W;
    const isCm = (i % 10 === 0);
    const isHalf = (i % 5 === 0);
    const h = isCm ? 46 : (isHalf ? 30 : 18);
    ctx.fillRect(x, 0, isCm ? 3 : 1.5, h);
    if (isCm) {
      ctx.font = 'bold 22px monospace';
      ctx.fillText(`${i / 10}`, x + 6, 76);
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

const IMAX_PBR_VERT = `
  #include <common>
  #include <skinning_pars_vertex>

  uniform mat4 uShadowMatrix;
  varying vec3 vWorldPos;
  varying vec3 vWorldNormal;
  varying vec2 vUv;
  varying vec4 vShadowCoord;

  void main() {
    vUv = uv;
    vec3 objectNormal = normal;
    vec3 transformed = position;

    #ifdef USE_SKINNING
      mat4 boneMatX = getBoneMatrix( skinIndex.x );
      mat4 boneMatY = getBoneMatrix( skinIndex.y );
      mat4 boneMatZ = getBoneMatrix( skinIndex.z );
      mat4 boneMatW = getBoneMatrix( skinIndex.w );
      vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
      vec4 skinned = vec4( 0.0 );
      skinned += boneMatX * skinVertex * skinWeight.x;
      skinned += boneMatY * skinVertex * skinWeight.y;
      skinned += boneMatZ * skinVertex * skinWeight.z;
      skinned += boneMatW * skinVertex * skinWeight.w;
      transformed = ( bindMatrixInverse * skinned ).xyz;

      mat4 skinMatNorm = skinWeight.x * boneMatX + skinWeight.y * boneMatY + skinWeight.z * boneMatZ + skinWeight.w * boneMatW;
      objectNormal = mat3( bindMatrixInverse * skinMatNorm * bindMatrix ) * objectNormal;
    #endif

    vec4 localPos = vec4(transformed, 1.0);
    vec3 localNorm = objectNormal;
    #ifdef USE_INSTANCING
      localPos = instanceMatrix * localPos;
      localNorm = mat3(instanceMatrix) * localNorm;
    #endif

    vec4 wp = modelMatrix * localPos;
    vWorldPos = wp.xyz;
    vWorldNormal = normalize(mat3(modelMatrix) * localNorm);
    vShadowCoord = uShadowMatrix * wp;
    gl_Position = projectionMatrix * viewMatrix * wp;
  }
`;

const IMAX_PBR_FRAG = `
  #include <packing>

  uniform vec3 uBaseColor;
  uniform vec3 uEmissive;
  uniform vec3 uSpecColor;
  uniform vec3 uRimTint;
  uniform float uRimStrength;
  uniform float uTranslucent;
  uniform float uSpecPower;
  uniform float uNormalScale;
  uniform float uOpacity;
  uniform float uReceiveShadow;
  uniform vec2 uMapRepeat;
  uniform float uHasMap;
  uniform float uHasNormal;
  uniform sampler2D uMap;
  uniform sampler2D uNormalMap;

  uniform vec3 uKeyDir;
  uniform vec3 uKeyColor;
  uniform vec3 uFillDir;
  uniform vec3 uFillColor;
  uniform vec3 uRimDir;
  uniform vec3 uRimLightCol;
  uniform vec3 uSkyColor;
  uniform vec3 uGroundColor;
  uniform vec3 uFogColor;
  uniform float uFogStart;
  uniform float uFogRange;
  uniform sampler2D uShadowTex;
  uniform float uShadowStrength;

  varying vec3 vWorldPos;
  varying vec3 vWorldNormal;
  varying vec2 vUv;
  varying vec4 vShadowCoord;

  float fastLobe32(float x) {
    float x2 = x * x; float x4 = x2 * x2; float x8 = x4 * x4; float x16 = x8 * x8;
    return x16 * x16;
  }
  float fastLobe8(float x) {
    float x2 = x * x; float x4 = x2 * x2;
    return x4 * x4;
  }

  float sampleSoftShadow(vec4 sc, float ndl) {
    vec3 proj = sc.xyz / max(0.0001, sc.w);
    vec2 suv = proj.xy * 0.5 + 0.5;
    float curZ = proj.z * 0.5 + 0.5;
    float bx = smoothstep(0.02, 0.12, suv.x) * (1.0 - smoothstep(0.88, 0.98, suv.x));
    float by = smoothstep(0.02, 0.12, suv.y) * (1.0 - smoothstep(0.88, 0.98, suv.y));
    float bz = step(0.001, curZ) * (1.0 - smoothstep(0.95, 0.998, curZ));
    float borderMask = bx * by * bz;
    if (borderMask <= 0.001) return 1.0;

    float bias = mix(0.0042, 0.0015, clamp(ndl, 0.0, 1.0));
    float texel = 1.0 / 512.0;
    float lit = 0.0;
    lit += (curZ - bias <= unpackRGBAToDepth(texture2D(uShadowTex, suv))) ? 0.36 : 0.0;
    lit += (curZ - bias <= unpackRGBAToDepth(texture2D(uShadowTex, suv + vec2( 0.92 * texel,  0.38 * texel)))) ? 0.16 : 0.0;
    lit += (curZ - bias <= unpackRGBAToDepth(texture2D(uShadowTex, suv + vec2(-0.38 * texel,  0.92 * texel)))) ? 0.16 : 0.0;
    lit += (curZ - bias <= unpackRGBAToDepth(texture2D(uShadowTex, suv + vec2(-0.92 * texel, -0.38 * texel)))) ? 0.16 : 0.0;
    lit += (curZ - bias <= unpackRGBAToDepth(texture2D(uShadowTex, suv + vec2( 0.38 * texel, -0.92 * texel)))) ? 0.16 : 0.0;
    return mix(1.0, lit, uShadowStrength * borderMask);
  }

  void main() {
    vec2 uv = vUv * uMapRepeat;
    vec3 albedo = uBaseColor;
    if (uHasMap > 0.5) {
      vec3 tex = texture2D(uMap, uv).rgb;
      albedo *= (tex * tex * 1.04);
    }

    vec3 N = normalize(vWorldNormal);
    if (uHasNormal > 0.5) {
      vec3 nm = texture2D(uNormalMap, uv).xyz * 2.0 - 1.0;
      vec3 upRef = abs(N.y) < 0.92 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
      vec3 T = normalize(cross(upRef, N));
      vec3 B = cross(N, T);
      N = normalize(N + (T * nm.x + B * nm.y) * uNormalScale);
    }

    vec3 V = normalize(cameraPosition - vWorldPos);
    float ndlKey = max(dot(N, uKeyDir), 0.0);
    float shadow = (uReceiveShadow > 0.5) ? sampleSoftShadow(vShadowCoord, ndlKey) : 1.0;

    float hemiMix = N.y * 0.5 + 0.5;
    vec3 diff = mix(uGroundColor, uSkyColor, hemiMix);

    float wrapKey = max(dot(N, uKeyDir) * 0.62 + 0.38, 0.0);
    diff += uKeyColor * mix(ndlKey, wrapKey, uTranslucent * 0.62) * shadow;

    vec3 Hk = normalize(uKeyDir + V);
    float nhKey = max(dot(N, Hk), 0.0);
    float tightSpec = fastLobe32(nhKey);
    float broadSpec = fastLobe8(nhKey);
    vec3 spec = uSpecColor * uKeyColor * mix(broadSpec * 0.22, tightSpec * 0.98 + broadSpec * 0.24, uSpecPower) * shadow;

    float ndlFill = max(dot(N, uFillDir), 0.0);
    diff += uFillColor * ndlFill;
    vec3 Hf = normalize(uFillDir + V);
    spec += uSpecColor * uFillColor * (fastLobe8(max(dot(N, Hf), 0.0)) * 0.18 * uSpecPower);

    float ndlRim = max(dot(N, uRimDir), 0.0);
    diff += uRimLightCol * (ndlRim * 0.58);
    vec3 Hr = normalize(uRimDir + V);
    spec += uRimLightCol * (fastLobe32(max(dot(N, Hr), 0.0)) * 0.48 * uSpecPower);

    float ndv = max(dot(N, V), 0.0);
    float omv = 1.0 - ndv;
    float fres = omv * omv * omv;
    float backScatter = max(dot(-V, uKeyDir), 0.0) * uTranslucent * shadow;

    vec3 color = albedo * diff + spec + uEmissive;
    color += uRimTint * (fres * uRimStrength + backScatter * 0.34);

    float dist = length(cameraPosition - vWorldPos);
    float fogF = clamp((dist - uFogStart) / max(1.0, uFogRange), 0.0, 0.82);
    color = mix(color, uFogColor, fogF);

    gl_FragColor = vec4(sqrt(clamp(color, 0.0, 1.0)), uOpacity);
  }
`;

const dummyShadowTex = new THREE.DataTexture(new Uint8Array([255, 255, 255, 255]), 1, 1);
dummyShadowTex.needsUpdate = true;

export const SHARED_LIGHT_UNIFORMS = {
  uKeyDir:         { value: new THREE.Vector3(0.38, 0.82, 0.42).normalize() },
  uKeyColor:       { value: new THREE.Color('#ffd9ad').multiplyScalar(0.92) },
  uFillDir:        { value: new THREE.Vector3(-0.32, 0.48, 0.82).normalize() },
  uFillColor:      { value: new THREE.Color('#ffe0bd').multiplyScalar(0.34) },
  uRimDir:         { value: new THREE.Vector3(-0.56, 0.50, -0.66).normalize() },
  uRimLightCol:    { value: new THREE.Color('#7ee0ec').multiplyScalar(0.56) },
  uSkyColor:       { value: new THREE.Color('#425860').multiplyScalar(0.24) },
  uGroundColor:    { value: new THREE.Color('#382012').multiplyScalar(0.18) },
  uFogColor:       { value: new THREE.Color('#091115').multiplyScalar(0.12) },
  uFogStart:       { value: 950.0 },
  uFogRange:       { value: 2400.0 },
  uShadowMatrix:   { value: new THREE.Matrix4() },
  uShadowTex:      { value: dummyShadowTex },
  uShadowStrength: { value: 0.68 },
};

export function setImaxLightingPreset(preset = 'cinema_lab', overrides = {}) {
  if (preset === 'midnight_tungsten') {
    SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(0.26, 0.88, 0.39).normalize();
    SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#ffe0b8').multiplyScalar(0.98);
    SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#ffd4a6').multiplyScalar(0.38);
    SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#9ce0ea').multiplyScalar(0.48);
    SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#705a44').multiplyScalar(0.26);
    SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#482a15').multiplyScalar(0.20);
    SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.022, 0.018, 0.014);
    SHARED_LIGHT_UNIFORMS.uFogStart.value = 2100.0;
    SHARED_LIGHT_UNIFORMS.uFogRange.value = 4200.0;
    SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.70;
  } else if (preset === 'abyssal_biolum') {
    SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(-0.34, 0.78, 0.52).normalize();
    SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#86d8f6').multiplyScalar(0.86);
    SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#2e6284').multiplyScalar(0.36);
    SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#ffc478').multiplyScalar(0.58);
    SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#1e3b52').multiplyScalar(0.28);
    SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#101924').multiplyScalar(0.20);
    SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.008, 0.015, 0.026);
    SHARED_LIGHT_UNIFORMS.uFogStart.value = 1600.0;
    SHARED_LIGHT_UNIFORMS.uFogRange.value = 3400.0;
    SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.62;
  } else {
    // 'cinema_lab' — neutral-warm 5200K optical macro stage with cyan rim separation
    SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(0.36, 0.85, 0.38).normalize();
    SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#fff3e2').multiplyScalar(0.96);
    SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#e0ecee').multiplyScalar(0.36);
    SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#84e2ec').multiplyScalar(0.54);
    SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#48565c').multiplyScalar(0.26);
    SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#282522').multiplyScalar(0.20);
    SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.011, 0.017, 0.021);
    SHARED_LIGHT_UNIFORMS.uFogStart.value = 1850.0;
    SHARED_LIGHT_UNIFORMS.uFogRange.value = 3600.0;
    SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.66;
  }
  if (overrides.fogStart !== undefined) SHARED_LIGHT_UNIFORMS.uFogStart.value = overrides.fogStart;
  if (overrides.fogRange !== undefined) SHARED_LIGHT_UNIFORMS.uFogRange.value = overrides.fogRange;
}

export function makeImaxMaterial({
  color = '#5b220d',
  emissive = '#000000',
  specular = '#e8aa6e',
  specPower = 0.85,
  map = null,
  normalMap = null,
  normalScale = 0.45,
  mapRepeat = [1, 1],
  rimTint = [0.92, 0.44, 0.14],
  rimStrength = 0.36,
  translucent = 0.15,
  transparent = false,
  opacity = 1.0,
  receiveShadow = true,
  side = THREE.FrontSide,
  polygonOffset = false,
  polygonOffsetFactor = 0,
  polygonOffsetUnits = 0,
} = {}) {
  const c = new THREE.Color(color);
  const em = new THREE.Color(emissive);
  const sp = new THREE.Color(specular);
  return new THREE.ShaderMaterial({
    vertexShader: IMAX_PBR_VERT,
    fragmentShader: IMAX_PBR_FRAG,
    transparent,
    depthWrite: !transparent,
    side,
    polygonOffset,
    polygonOffsetFactor,
    polygonOffsetUnits,
    uniforms: {
      ...SHARED_LIGHT_UNIFORMS,
      uBaseColor:     { value: new THREE.Vector3(c.r, c.g, c.b) },
      uEmissive:      { value: new THREE.Vector3(em.r, em.g, em.b).multiplyScalar(0.48) },
      uSpecColor:     { value: new THREE.Vector3(sp.r, sp.g, sp.b) },
      uRimTint:       { value: new THREE.Vector3(...rimTint) },
      uRimStrength:   { value: rimStrength },
      uTranslucent:   { value: translucent },
      uSpecPower:     { value: specPower },
      uNormalScale:   { value: normalScale },
      uOpacity:       { value: opacity },
      uReceiveShadow: { value: receiveShadow && !transparent ? 1.0 : 0.0 },
      uMapRepeat:     { value: new THREE.Vector2(mapRepeat[0], mapRepeat[1]) },
      uHasMap:        { value: map ? 1.0 : 0.0 },
      uHasNormal:     { value: normalMap ? 1.0 : 0.0 },
      uMap:           { value: map },
      uNormalMap:     { value: normalMap },
    },
  });
}

/**
 * 30 Hz Every-Frame Light-Space Texel-Snapped Shadow Rig (Zero-Flicker Law #3!)
 */
export function createTexelSnappedShadowRig(renderer, { mapSize = 512, excludeObjects = [] } = {}) {
  const shadowRT = new THREE.WebGLRenderTarget(mapSize, mapSize, {
    minFilter: THREE.NearestFilter,
    magFilter: THREE.NearestFilter,
    format: THREE.RGBAFormat,
  });
  const shadowDepthMat = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  const shadowCam = new THREE.OrthographicCamera(-60, 60, 60, -60, 1.0, 4200.0);
  const lightRight = new THREE.Vector3();
  const lightUp = new THREE.Vector3();
  const snappedFocus = new THREE.Vector3();

  function updateShadowMap(scene, focusCenter, frustumHalf = 65.0) {
    const keyDir = SHARED_LIGHT_UNIFORMS.uKeyDir.value;
    lightRight.crossVectors(new THREE.Vector3(0, 1, 0), keyDir).normalize();
    lightUp.crossVectors(keyDir, lightRight).normalize();

    const texelWorld = (frustumHalf * 2.0) / mapSize;
    const rx = Math.round(focusCenter.dot(lightRight) / texelWorld) * texelWorld;
    const ry = Math.round(focusCenter.dot(lightUp) / texelWorld) * texelWorld;
    const rz = focusCenter.dot(keyDir);

    snappedFocus.set(0, 0, 0)
      .addScaledVector(lightRight, rx)
      .addScaledVector(lightUp, ry)
      .addScaledVector(keyDir, rz);

    const dist = Math.max(180.0, frustumHalf * 3.2);
    shadowCam.left = -frustumHalf;
    shadowCam.right = frustumHalf;
    shadowCam.top = frustumHalf;
    shadowCam.bottom = -frustumHalf;
    shadowCam.near = dist * 0.12;
    shadowCam.far = dist * 2.8;
    shadowCam.position.copy(snappedFocus).addScaledVector(keyDir, dist);
    shadowCam.lookAt(snappedFocus);
    shadowCam.updateProjectionMatrix();
    shadowCam.updateMatrixWorld(true);

    const savedVis = excludeObjects.map((o) => {
      const v = o.visible;
      o.visible = false;
      return v;
    });

    const prevOverride = scene.overrideMaterial;
    const prevTarget = renderer.getRenderTarget();
    scene.overrideMaterial = shadowDepthMat;
    renderer.setRenderTarget(shadowRT);
    renderer.clear();
    renderer.render(scene, shadowCam);
    renderer.setRenderTarget(prevTarget);
    scene.overrideMaterial = prevOverride;

    excludeObjects.forEach((o, idx) => { o.visible = savedVis[idx]; });

    SHARED_LIGHT_UNIFORMS.uShadowTex.value = shadowRT.texture;
    SHARED_LIGHT_UNIFORMS.uShadowMatrix.value
      .copy(shadowCam.projectionMatrix)
      .multiply(shadowCam.matrixWorldInverse);
  }

  return { updateShadowMap, shadowRT, shadowCam };
}
