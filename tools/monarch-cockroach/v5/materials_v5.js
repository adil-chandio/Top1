import * as THREE from 'three';

/**
 * Monarch Cam #03 — V5 Cinema Master Material, Procedural PBR & Flicker-Free Shadow Library!
 * Upgrades V4 with:
 *   1. Strict `depthWrite: false` + `uReceiveShadow: 0.0` on ALL transparent materials and
 *      `polygonOffset` support on ground base layers -> ZERO Z-fighting / blue flicker!
 *   2. Smooth frustum-border fade + 5-tap rotated PCF shadow sampling -> ZERO shadow pop/acne!
 *   3. Bespoke 1024px M6 Tapped Optical Breadboard + Laser-Etched Metric Scale Bar texture so
 *      continuous forward cockroach velocity is visually unmistakable without fake loops!
 */

export function buildNormalFromCanvas(srcCanvas, strength = 2.4, size = 512) {
  const work = document.createElement('canvas');
  work.width = size; work.height = size;
  const sctx = work.getContext('2d', { willReadFrequently: true });
  sctx.drawImage(srcCanvas, 0, 0, size, size);
  const src = sctx.getImageData(0, 0, size, size).data;

  const outCanvas = document.createElement('canvas');
  outCanvas.width = size; outCanvas.height = size;
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

function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function buildChitinBaseCanvas() {
  const S = 512;
  const c = document.createElement('canvas');
  c.width = S; c.height = S;
  const ctx = c.getContext('2d');
  const rng = mulberry32(1031);

  ctx.fillStyle = '#8e3e19';
  ctx.fillRect(0, 0, S, S);

  for (let i = 0; i < 2400; i++) {
    const x = rng() * S, y = rng() * S;
    const r = 3 + rng() * 9;
    ctx.fillStyle = rng() > 0.5 ? 'rgba(176, 92, 42, 0.13)' : 'rgba(46, 15, 4, 0.15)';
    ctx.beginPath();
    ctx.ellipse(x, y, r * 1.3, r * 0.85, rng() * Math.PI, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.strokeStyle = 'rgba(220, 138, 72, 0.08)';
  ctx.lineWidth = 1.0;
  for (let y = 0; y < S; y += 4) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.bezierCurveTo(S * 0.33, y + (rng() - 0.5) * 4, S * 0.66, y + (rng() - 0.5) * 4, S, y);
    ctx.stroke();
  }
  return c;
}

function buildPronotumTexture(chitinCanvas) {
  const S = 1024;
  const c = document.createElement('canvas');
  c.width = S; c.height = S;
  const ctx = c.getContext('2d');
  ctx.drawImage(chitinCanvas, 0, 0, S, S);

  const band = ctx.createRadialGradient(S * 0.5, S * 0.52, S * 0.14, S * 0.5, S * 0.5, S * 0.48);
  band.addColorStop(0.0, 'rgba(54, 16, 5, 0.82)');
  band.addColorStop(0.50, 'rgba(68, 22, 7, 0.74)');
  band.addColorStop(0.71, 'rgba(242, 178, 92, 0.80)');
  band.addColorStop(0.84, 'rgba(218, 142, 60, 0.64)');
  band.addColorStop(0.95, 'rgba(84, 30, 10, 0.84)');
  band.addColorStop(1.0, 'rgba(58, 18, 6, 0.90)');
  ctx.fillStyle = band;
  ctx.fillRect(0, 0, S, S);

  ctx.fillStyle = 'rgba(38, 10, 3, 0.60)';
  for (const sgn of [-1, 1]) {
    ctx.beginPath();
    ctx.ellipse(S * (0.5 + sgn * 0.125), S * 0.51, S * 0.115, S * 0.175, sgn * 0.20, 0, Math.PI * 2);
    ctx.fill();
  }

  const albedo = new THREE.CanvasTexture(c);
  albedo.colorSpace = THREE.SRGBColorSpace;
  const normal = buildNormalFromCanvas(c, 2.4, 512);
  return { albedo, normal };
}

function buildTegminaTexture(chitinCanvas) {
  const W = 1024, H = 512;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const ctx = c.getContext('2d');
  ctx.drawImage(chitinCanvas, 0, 0, W, H);

  const g = ctx.createLinearGradient(0, 0, W, 0);
  g.addColorStop(0.0, 'rgba(64, 20, 6, 0.56)');
  g.addColorStop(0.32, 'rgba(138, 58, 18, 0.20)');
  g.addColorStop(0.72, 'rgba(168, 82, 28, 0.28)');
  g.addColorStop(1.0, 'rgba(92, 38, 14, 0.48)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);

  ctx.lineCap = 'round';
  const drawVein = (x0, y0, x1, y1, cx, cy, w, alpha) => {
    ctx.strokeStyle = `rgba(34, 10, 3, ${alpha})`;
    ctx.lineWidth = w;
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.quadraticCurveTo(cx, cy, x1, y1); ctx.stroke();
    ctx.strokeStyle = `rgba(232, 150, 76, ${alpha * 0.52})`;
    ctx.lineWidth = Math.max(1.1, w * 0.42);
    ctx.beginPath(); ctx.moveTo(x0, y0 - 1.3); ctx.quadraticCurveTo(cx, cy - 1.3, x1, y1 - 1.3); ctx.stroke();
  };

  drawVein(18, H * 0.18, W * 0.64, H * 0.05, W * 0.30, H * 0.08, 7.0, 0.80);
  for (let i = 0; i < 12; i++) {
    const t = 0.10 + i * 0.074;
    const sx = W * (0.04 + t * 0.72), sy = H * (0.24 + t * 0.08);
    drawVein(sx, sy, Math.min(W * 0.98, sx + W * 0.24), H * (0.03 + i * 0.045), sx + W * 0.12, sy - H * 0.08, 3.6 - i * 0.14, 0.64);
  }
  drawVein(20, H * 0.34, W * 0.97, H * 0.56, W * 0.48, H * 0.42, 5.6, 0.74);
  for (let i = 0; i < 10; i++) {
    const sx = W * (0.16 + i * 0.080), sy = H * (0.38 + i * 0.02);
    drawVein(sx, sy, Math.min(W * 0.98, sx + W * 0.22), Math.min(H * 0.96, sy + H * 0.24), sx + W * 0.10, sy + H * 0.12, 3.0, 0.56);
  }
  drawVein(16, H * 0.46, W * 0.46, H * 0.94, W * 0.28, H * 0.62, 6.4, 0.82);

  const albedo = new THREE.CanvasTexture(c);
  albedo.colorSpace = THREE.SRGBColorSpace;
  const normal = buildNormalFromCanvas(c, 3.4, 512);
  return { albedo, normal };
}

function buildOakFloorTexture() {
  const S = 1024;
  const c = document.createElement('canvas');
  c.width = S; c.height = S;
  const ctx = c.getContext('2d');
  const rng = mulberry32(7721);

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
    const jx = ((p * 317 + 140) % (S - 120)) + 60;
    ctx.fillRect(jx, y0, 3.0, ph);
  }

  const albedo = new THREE.CanvasTexture(c);
  albedo.wrapS = albedo.wrapT = THREE.RepeatWrapping;
  const normal = buildNormalFromCanvas(c, 2.8, 512);
  return { albedo, normal };
}

function buildMintedPennyTexture() {
  const S = 512;
  const c = document.createElement('canvas');
  c.width = S; c.height = S;
  const ctx = c.getContext('2d');

  const bg = ctx.createRadialGradient(S * 0.45, S * 0.42, S * 0.05, S * 0.5, S * 0.5, S * 0.5);
  bg.addColorStop(0.0, '#e89660');
  bg.addColorStop(0.65, '#c66a36');
  bg.addColorStop(0.90, '#9e4c21');
  bg.addColorStop(0.95, '#f2b484');
  bg.addColorStop(1.0, '#7c3614');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, S, S);

  ctx.strokeStyle = '#ffd4aa';
  ctx.lineWidth = 14;
  ctx.beginPath();
  ctx.arc(S * 0.5, S * 0.5, S * 0.455, 0, Math.PI * 2);
  ctx.stroke();

  ctx.fillStyle = '#ecb284';
  ctx.beginPath();
  ctx.moveTo(S * 0.30, S * 0.80);
  ctx.quadraticCurveTo(S * 0.48, S * 0.64, S * 0.68, S * 0.78);
  ctx.lineTo(S * 0.62, S * 0.86);
  ctx.lineTo(S * 0.32, S * 0.86);
  ctx.closePath();
  ctx.fill();

  ctx.beginPath();
  ctx.ellipse(S * 0.49, S * 0.44, S * 0.115, S * 0.155, -0.08, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(S * 0.58, S * 0.38);
  ctx.lineTo(S * 0.65, S * 0.44);
  ctx.lineTo(S * 0.59, S * 0.47);
  ctx.lineTo(S * 0.61, S * 0.55);
  ctx.lineTo(S * 0.54, S * 0.58);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = 'rgba(255, 224, 192, 0.65)';
  ctx.font = 'bold 24px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('LIBERTY', S * 0.27, S * 0.54);
  ctx.fillText('2016', S * 0.74, S * 0.62);

  const albedo = new THREE.CanvasTexture(c);
  albedo.colorSpace = THREE.SRGBColorSpace;
  const normal = buildNormalFromCanvas(c, 3.6, 512);
  return { albedo, normal };
}

function buildGritTexture(grainCount, grainRadius, baseHex, seed) {
  const S = 512;
  const c = document.createElement('canvas');
  c.width = S; c.height = S;
  const ctx = c.getContext('2d');
  const rng = mulberry32(seed);

  ctx.fillStyle = baseHex;
  ctx.fillRect(0, 0, S, S);

  for (let i = 0; i < grainCount; i++) {
    const x = rng() * S, y = rng() * S;
    const r = grainRadius * (0.55 + rng() * 0.95);
    const bright = rng() > 0.45;
    ctx.fillStyle = bright ? 'rgba(220, 212, 200, 0.26)' : 'rgba(12, 10, 9, 0.34)';
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  const albedo = new THREE.CanvasTexture(c);
  albedo.wrapS = albedo.wrapT = THREE.RepeatWrapping;
  const normal = buildNormalFromCanvas(c, 3.2, 512);
  return { albedo, normal };
}

/**
 * V5 M6 Tapped Anodized Optical Breadboard Texture (Newport / Thorlabs style!)
 * Gives crisp real-world spatial motion cues during tracking shots with ZERO blue cast!
 */
function buildOpticalBreadboardTexture() {
  const S = 512;
  const c = document.createElement('canvas');
  c.width = S; c.height = S;
  const ctx = c.getContext('2d');

  // Deep neutral-charcoal anodized stainless top
  ctx.fillStyle = '#1b1e22';
  ctx.fillRect(0, 0, S, S);

  // Subtle brushed metal horizontal micro-lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
  ctx.lineWidth = 1;
  for (let y = 0; y < S; y += 3) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(S, y); ctx.stroke();
  }

  // 8x8 grid of countersunk M6 tapped mounting holes
  const step = S / 8;
  for (let gy = 0; gy < 8; gy++) {
    for (let gx = 0; gx < 8; gx++) {
      const cx = (gx + 0.5) * step;
      const cy = (gy + 0.5) * step;
      // Outer bright chamfer ring
      ctx.fillStyle = '#343a40';
      ctx.beginPath(); ctx.arc(cx, cy, 7.2, 0, Math.PI * 2); ctx.fill();
      // Inner dark threaded bore
      ctx.fillStyle = '#090b0d';
      ctx.beginPath(); ctx.arc(cx, cy, 4.6, 0, Math.PI * 2); ctx.fill();
    }
  }

  const albedo = new THREE.CanvasTexture(c);
  albedo.wrapS = albedo.wrapT = THREE.RepeatWrapping;
  const normal = buildNormalFromCanvas(c, 2.2, 512);
  return { albedo, normal };
}

/**
 * Laser-etched millimeter/centimeter ruler bar along corridor rail so forward velocity is unmistakable!
 */
function buildMetricRulerTexture() {
  const W = 1024, H = 128;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
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

function buildTelemetryScreenTexture() {
  const W = 512, H = 320;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const ctx = c.getContext('2d');

  ctx.fillStyle = '#071116';
  ctx.fillRect(0, 0, W, H);

  ctx.strokeStyle = 'rgba(110, 224, 232, 0.12)';
  ctx.lineWidth = 1;
  for (let x = 24; x < W; x += 36) { ctx.beginPath(); ctx.moveTo(x, 42); ctx.lineTo(x, H - 18); ctx.stroke(); }
  for (let y = 48; y < H; y += 36) { ctx.beginPath(); ctx.moveTo(18, y); ctx.lineTo(W - 18, y); ctx.stroke(); }

  ctx.fillStyle = '#8fe6de';
  ctx.font = 'bold 15px monospace';
  ctx.fillText('UC BERKELEY · POLY-PEDAL LAB · 500 FPS DAQ', 20, 26);
  ctx.fillStyle = '#ffd187';
  ctx.font = '12px monospace';
  ctx.fillText('CEILING: 12->4->3.2 MM | PEAK: 6.08 N (~900x BW)', 20, 44);

  // Force waveform
  ctx.strokeStyle = '#6ef2c8';
  ctx.lineWidth = 2.4;
  ctx.beginPath();
  for (let x = 20; x < W - 20; x += 4) {
    const u = (x - 20) / (W - 40);
    const y = 128 - Math.sin(u * Math.PI * 10) * 26 - Math.pow(Math.max(0, Math.sin(u * Math.PI * 5)), 3) * 22;
    if (x === 20) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Velocity cliff trace
  ctx.strokeStyle = '#ffb86c';
  ctx.lineWidth = 2.4;
  ctx.beginPath();
  for (let x = 20; x < W - 20; x += 4) {
    const u = (x - 20) / (W - 40);
    const step = u < 0.58 ? 0.0 : Math.min(1.0, (u - 0.58) * 6.0);
    const y = 212 + step * 52 + Math.sin(u * 38.0) * 5.0;
    if (x === 20) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.stroke();

  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

const V5_PBR_VERT = `
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

const V5_PBR_FRAG = `
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
    // Smooth border fade eliminates frustum-edge popping on background props/walls!
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

export function setLightingMood(mood, blend = 1.0) {
  if (mood === 'apartment_dark') {
    // Rich cinematic 2:14 AM moonlight contour + warm golden hallway rim spill!
    SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(-0.38, 0.68, 0.62).normalize();
    SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#7aa4dc').multiplyScalar(0.64);
    SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#38557c').multiplyScalar(0.34);
    SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#ffc478').multiplyScalar(0.58);
    SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#2a3f62').multiplyScalar(0.28);
    SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#1d202c').multiplyScalar(0.18);
    SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.010, 0.016, 0.030);
    SHARED_LIGHT_UNIFORMS.uFogStart.value = 2100.0;
    SHARED_LIGHT_UNIFORMS.uFogRange.value = 4000.0;
    SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.50;
  } else if (mood === 'apartment_lit') {
    SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(0.26, 0.88, 0.39).normalize();
    SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#ffe0b8').multiplyScalar(1.00 * blend + 0.55 * (1 - blend));
    SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#ffd4a6').multiplyScalar(0.40);
    SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#9ce0ea').multiplyScalar(0.46);
    SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#705a44').multiplyScalar(0.28);
    SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#482a15').multiplyScalar(0.22);
    SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.026, 0.020, 0.015);
    SHARED_LIGHT_UNIFORMS.uFogStart.value = 2200.0;
    SHARED_LIGHT_UNIFORMS.uFogRange.value = 4200.0;
    SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.70;
  } else if (mood === 'lab') {
    // Neutral-warm 5200K UC Berkeley fiber-optic cold-light macro illumination (ZERO blue floor cast!)
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
  } else if (mood === 'pushup') {
    SHARED_LIGHT_UNIFORMS.uKeyDir.value.set(0.32, 0.86, 0.40).normalize();
    SHARED_LIGHT_UNIFORMS.uKeyColor.value.set('#ffe8cc').multiplyScalar(0.98);
    SHARED_LIGHT_UNIFORMS.uFillColor.value.set('#96d8e4').multiplyScalar(0.38);
    SHARED_LIGHT_UNIFORMS.uRimLightCol.value.set('#ffbe72').multiplyScalar(0.62);
    SHARED_LIGHT_UNIFORMS.uSkyColor.value.set('#304e58').multiplyScalar(0.30);
    SHARED_LIGHT_UNIFORMS.uGroundColor.value.set('#18242a').multiplyScalar(0.20);
    SHARED_LIGHT_UNIFORMS.uFogColor.value.setRGB(0.009, 0.018, 0.024);
    SHARED_LIGHT_UNIFORMS.uFogStart.value = 2400.0;
    SHARED_LIGHT_UNIFORMS.uFogRange.value = 4400.0;
    SHARED_LIGHT_UNIFORMS.uShadowStrength.value = 0.68;
  }
}

export function makeV5Material({
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
}) {
  const c = new THREE.Color(color);
  const em = new THREE.Color(emissive);
  const sp = new THREE.Color(specular);
  return new THREE.ShaderMaterial({
    vertexShader: V5_PBR_VERT,
    fragmentShader: V5_PBR_FRAG,
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

export async function createV5MaterialLibrary() {
  const chitinCanvas = buildChitinBaseCanvas();
  const chitinAlbedo = new THREE.CanvasTexture(chitinCanvas);
  chitinAlbedo.wrapS = chitinAlbedo.wrapT = THREE.RepeatWrapping;
  const chitinNormal = buildNormalFromCanvas(chitinCanvas, 2.2, 512);

  const pronotumTex   = buildPronotumTexture(chitinCanvas);
  const tegminaTex    = buildTegminaTexture(chitinCanvas);
  const oakTex        = buildOakFloorTexture();
  const pennyTex      = buildMintedPennyTexture();
  const breadboardTex = buildOpticalBreadboardTexture();
  const rulerTex      = buildMetricRulerTexture();
  const grit100Tex    = buildGritTexture(5500, 1.1, '#3c3e42', 101);
  const grit40Tex     = buildGritTexture(3200, 2.3, '#2f2a26', 404);
  const grit20Tex     = buildGritTexture(1100, 4.8, '#251e19', 202);
  const screenTex     = buildTelemetryScreenTexture();

  return {
    textures: { chitinAlbedo, chitinNormal, oakTex, pennyTex, breadboardTex, rulerTex, grit100Tex, grit40Tex, grit20Tex, screenTex },

    pronotumMat: makeV5Material({
      color: '#c8642b', specular: '#ffdcaf', specPower: 0.96,
      map: pronotumTex.albedo, normalMap: pronotumTex.normal, normalScale: 0.38,
      rimTint: [1.0, 0.58, 0.22], rimStrength: 0.44, translucent: 0.22,
    }),
    tegminaMat: makeV5Material({
      color: '#b55523', specular: '#ffd29c', specPower: 0.88,
      map: tegminaTex.albedo, normalMap: tegminaTex.normal, normalScale: 0.58,
      rimTint: [0.98, 0.54, 0.18], rimStrength: 0.46, translucent: 0.36, side: THREE.DoubleSide,
    }),
    tergiteMat: makeV5Material({
      color: '#803215', specular: '#f4b880', specPower: 0.90,
      map: chitinAlbedo, normalMap: chitinNormal, mapRepeat: [2, 2], normalScale: 0.46,
      rimTint: [0.94, 0.44, 0.15], rimStrength: 0.38, translucent: 0.16, side: THREE.DoubleSide,
    }),
    headMat: makeV5Material({
      color: '#642510', specular: '#f4bc86', specPower: 0.92,
      map: chitinAlbedo, normalMap: chitinNormal, normalScale: 0.34,
      rimTint: [0.88, 0.40, 0.14], rimStrength: 0.34, translucent: 0.12,
    }),
    eyeMat: makeV5Material({
      color: '#121010', specular: '#def4fa', specPower: 1.0,
      normalMap: chitinNormal, normalScale: 0.92, mapRepeat: [10, 10],
      rimTint: [0.52, 0.82, 0.92], rimStrength: 0.48, translucent: 0.0,
    }),
    legMat: makeV5Material({
      color: '#943a18', specular: '#fac48c', specPower: 0.90,
      map: chitinAlbedo, normalMap: chitinNormal, mapRepeat: [2, 2], normalScale: 0.42,
      rimTint: [1.0, 0.50, 0.18], rimStrength: 0.44, translucent: 0.24,
    }),
    jointCondyleMat: makeV5Material({
      color: '#ba5c2a', specular: '#ffe0b5', specPower: 0.92,
      rimTint: [1.0, 0.65, 0.30], rimStrength: 0.40, translucent: 0.32,
    }),
    spineMat: makeV5Material({
      color: '#601e09', emissive: '#2c0b02', specular: '#ffe4bc', specPower: 0.98,
      rimTint: [1.0, 0.68, 0.28], rimStrength: 0.60, translucent: 0.20,
    }),
    aroliumMat: makeV5Material({
      color: '#eed6ac', emissive: '#3e2f18', specular: '#fff6e4', specPower: 0.58,
      rimTint: [1.0, 0.90, 0.70], rimStrength: 0.38, translucent: 0.42,
    }),
    pleuralNaturalMat: makeV5Material({
      color: '#7d3216', specular: '#e4b080', specPower: 0.80,
      map: chitinAlbedo, normalMap: chitinNormal, mapRepeat: [2, 2], normalScale: 0.42,
      rimTint: [0.86, 0.42, 0.14], rimStrength: 0.30, translucent: 0.12,
    }),

    // Flicker-Free FrontSide X-Ray Shell + Opaque Internal Sclerites/Hinges!
    xrayGlassShellMat: makeV5Material({
      color: '#cc7a42', emissive: '#241206', specular: '#ffffff', specPower: 0.96,
      rimTint: [1.0, 0.72, 0.38], rimStrength: 0.64, transparent: true, opacity: 0.19, side: THREE.FrontSide,
    }),
    cutFaceMat: makeV5Material({
      color: '#f59c4c', emissive: '#6e2e0a', specular: '#ffecd0', specPower: 0.82,
      rimTint: [1.0, 0.78, 0.42], rimStrength: 0.35, translucent: 0.26,
    }),
    arthrodialMat: makeV5Material({
      color: '#74f2ec', emissive: '#1e6e6e', specular: '#ecffff', specPower: 0.76,
      rimTint: [0.58, 0.98, 0.96], rimStrength: 0.55, translucent: 0.40, side: THREE.DoubleSide,
    }),
    nerveCordMat: makeV5Material({
      color: '#5ef29b', emissive: '#18683a', specular: '#e2ffee', specPower: 0.85,
      rimTint: [0.45, 1.0, 0.68], rimStrength: 0.52, translucent: 0.35,
    }),
    tracheaMat: makeV5Material({
      color: '#b8e4ee', emissive: '#1c3e48', specular: '#ffffff', specPower: 0.92,
      rimTint: [0.75, 0.95, 1.0], rimStrength: 0.45, translucent: 0.30,
    }),

    pennyFaceMat: makeV5Material({
      color: '#d87a42', emissive: '#1a0902', specular: '#ffe2c0', specPower: 0.95,
      map: pennyTex.albedo, normalMap: pennyTex.normal, normalScale: 0.92,
      rimTint: [1.0, 0.64, 0.34], rimStrength: 0.44, translucent: 0.04,
    }),
    pennyRimMat: makeV5Material({
      color: '#c26632', emissive: '#180802', specular: '#ffdcba', specPower: 0.95,
      rimTint: [1.0, 0.62, 0.32], rimStrength: 0.42,
    }),

    oakFloorMat: makeV5Material({
      color: '#7c502e', specular: '#cca27a', specPower: 0.68,
      map: oakTex.albedo, normalMap: oakTex.normal, mapRepeat: [5.0, 5.0], normalScale: 0.65,
      rimTint: [0.75, 0.48, 0.24], rimStrength: 0.10,
    }),
    oakDoorMat: makeV5Material({
      color: '#8e5c36', specular: '#d4aa82', specPower: 0.62,
      map: oakTex.albedo, normalMap: oakTex.normal, mapRepeat: [2.0, 3.0], normalScale: 0.48,
      rimTint: [0.78, 0.52, 0.28], rimStrength: 0.14,
    }),
    plasterWallMat: makeV5Material({
      color: '#d2c9bb', specular: '#eae4da', specPower: 0.20,
      rimTint: [0.60, 0.58, 0.54], rimStrength: 0.06,
    }),
    trimWhiteMat: makeV5Material({
      color: '#eae4da', specular: '#ffffff', specPower: 0.55,
      rimTint: [0.80, 0.78, 0.74], rimStrength: 0.10,
    }),
    switchPlateMat: makeV5Material({
      color: '#f2ecdf', specular: '#ffffff', specPower: 0.72,
      rimTint: [0.90, 0.86, 0.78], rimStrength: 0.16,
    }),
    brassMat: makeV5Material({
      color: '#d8ac52', emissive: '#1c1204', specular: '#fff0c4', specPower: 0.96,
      rimTint: [1.0, 0.82, 0.42], rimStrength: 0.44,
    }),
    rugMat: makeV5Material({
      color: '#2e4252', specular: '#486072', specPower: 0.18,
      normalMap: grit40Tex.normal, mapRepeat: [12, 12], normalScale: 0.45,
      rimTint: [0.32, 0.46, 0.58], rimStrength: 0.08,
    }),
    cabinetMat: makeV5Material({
      color: '#343c44', specular: '#788896', specPower: 0.55,
      rimTint: [0.45, 0.54, 0.62], rimStrength: 0.12,
    }),

    // Flicker-Free Neutral-Charcoal M6 Optical Breadboard (polygonOffset pushed behind all bench rails!)
    breadboardMat: makeV5Material({
      color: '#24272b', specular: '#5c6268', specPower: 0.48,
      map: breadboardTex.albedo, normalMap: breadboardTex.normal, mapRepeat: [12, 5], normalScale: 0.55,
      rimTint: [0.32, 0.35, 0.38], rimStrength: 0.10,
      polygonOffset: true, polygonOffsetFactor: 2, polygonOffsetUnits: 2,
    }),
    rulerMat: new THREE.MeshBasicMaterial({ map: rulerTex }),
    steelBrushedMat: makeV5Material({
      color: '#9eaab4', specular: '#f2f8ff', specPower: 0.90,
      rimTint: [0.72, 0.84, 0.92], rimStrength: 0.30,
    }),
    anodizedBlackMat: makeV5Material({
      color: '#191d21', specular: '#606c76', specPower: 0.76,
      rimTint: [0.34, 0.42, 0.48], rimStrength: 0.16,
    }),
    labWallMat: makeV5Material({
      color: '#283137', specular: '#46545e', specPower: 0.22,
      rimTint: [0.28, 0.36, 0.42], rimStrength: 0.06,
    }),

    // Flicker-Free Optical Crystal Acrylic (depthWrite=false, FrontSide, non-overlapping edges!)
    acrylicClearMat: makeV5Material({
      color: '#a8e4ec', emissive: '#06161b', specular: '#ffffff', specPower: 0.98,
      rimTint: [0.64, 0.92, 0.96], rimStrength: 0.46, transparent: true, opacity: 0.09, side: THREE.FrontSide,
    }),
    acrylicEdgeMat: makeV5Material({
      color: '#72e0ec', emissive: '#0c3038', specular: '#ffffff', specPower: 0.96,
      rimTint: [0.58, 0.94, 0.98], rimStrength: 0.56, transparent: true, opacity: 0.28, side: THREE.FrontSide,
    }),

    grit100Mat: makeV5Material({
      color: '#484c52', specular: '#9aa2ac', specPower: 0.66,
      map: grit100Tex.albedo, normalMap: grit100Tex.normal, mapRepeat: [24, 3], normalScale: 0.42,
      rimTint: [0.46, 0.50, 0.54], rimStrength: 0.10,
    }),
    grit40Mat: makeV5Material({
      color: '#36302b', specular: '#766c62', specPower: 0.34,
      map: grit40Tex.albedo, normalMap: grit40Tex.normal, mapRepeat: [20, 3], normalScale: 0.84,
      rimTint: [0.40, 0.36, 0.32], rimStrength: 0.08,
    }),
    grit20Mat: makeV5Material({
      color: '#2c231c', specular: '#645448', specPower: 0.24,
      map: grit20Tex.albedo, normalMap: grit20Tex.normal, mapRepeat: [14, 2.5], normalScale: 1.18,
      rimTint: [0.36, 0.28, 0.22], rimStrength: 0.08,
    }),
    screenGlowMat: new THREE.MeshBasicMaterial({ map: screenTex }),
  };
}
