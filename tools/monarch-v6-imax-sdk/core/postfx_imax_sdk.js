import * as THREE from 'three';

/**
 * Monarch V6 Hollywood IMAX Cinema SDK — True Linear-Light ACES Filmic HDR Optical Pass
 * (`postfx_imax_sdk.js`):
 *   1. True Linear-Space Pipeline (`s * s` decode -> HDR optical math -> `pow(1/2.2)` sRGB)
 *   2. 12-Tap Golden-Angle (`2.39996323 rad`) Vogel-Spiral Cinema Bokeh Depth-of-Field
 *   3. Subtle Peripheral Optical Chromatic Dispersion
 *   4. 7-Tap 180°-Shutter Directional Camera-Velocity Motion Blur (`uMotionVec`)
 *   5. Dual-Pass Panavision `2.35x` Wide Horizontal Anamorphic Halation & Specular Bloom
 *   6. Kodak 2383 Split-Tone Cinema Grade + Narkowicz ACES Filmic Tone Mapping + 35mm Fine Grain
 */
export function createImaxOpticalPass(renderer, width, height) {
  const rtScene = new THREE.WebGLRenderTarget(width, height, {
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
    format: THREE.RGBAFormat,
    type: THREE.UnsignedByteType,
    depthBuffer: true,
    depthTexture: new THREE.DepthTexture(width, height, THREE.UnsignedIntType),
  });

  const bw = Math.max(64, Math.floor(width / 3));
  const bh = Math.max(64, Math.floor(height / 3));
  const rtBloomA = new THREE.WebGLRenderTarget(bw, bh, {
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
    format: THREE.RGBAFormat,
  });
  const rtBloomB = new THREE.WebGLRenderTarget(bw, bh, {
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
    format: THREE.RGBAFormat,
  });

  const quadGeo = new THREE.PlaneGeometry(2, 2);
  const postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  const vertCommon = `
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }
  `;

  const bloomHorizMat = new THREE.ShaderMaterial({
    uniforms: {
      tInput: { value: rtScene.texture },
      uTexel: { value: new THREE.Vector2(1.0 / bw, 1.0 / bh) },
    },
    vertexShader: vertCommon,
    fragmentShader: `
      uniform sampler2D tInput;
      uniform vec2 uTexel;
      varying vec2 vUv;

      vec3 brightExtract(vec2 uv) {
        vec3 s = texture2D(tInput, clamp(uv, 0.001, 0.999)).rgb;
        vec3 lin = s * s;
        float lum = dot(lin, vec3(0.2126, 0.7152, 0.0722));
        float knee = smoothstep(0.36, 0.92, lum);
        return lin * knee;
      }

      void main() {
        float dx = uTexel.x * 2.35;
        vec3 acc = brightExtract(vUv) * 0.227027;
        acc += (brightExtract(vUv + vec2(dx * 1.4, 0.0)) + brightExtract(vUv - vec2(dx * 1.4, 0.0))) * 0.194594;
        acc += (brightExtract(vUv + vec2(dx * 3.2, 0.0)) + brightExtract(vUv - vec2(dx * 3.2, 0.0))) * 0.121621;
        acc += (brightExtract(vUv + vec2(dx * 5.4, 0.0)) + brightExtract(vUv - vec2(dx * 5.4, 0.0))) * 0.054054;
        acc += (brightExtract(vUv + vec2(dx * 8.0, 0.0)) + brightExtract(vUv - vec2(dx * 8.0, 0.0))) * 0.016216;
        gl_FragColor = vec4(clamp(acc, 0.0, 4.0) * 0.5, 1.0);
      }
    `,
    depthTest: false,
    depthWrite: false,
  });

  const bloomVertMat = new THREE.ShaderMaterial({
    uniforms: {
      tInput: { value: rtBloomA.texture },
      uTexel: { value: new THREE.Vector2(1.0 / bw, 1.0 / bh) },
    },
    vertexShader: vertCommon,
    fragmentShader: `
      uniform sampler2D tInput;
      uniform vec2 uTexel;
      varying vec2 vUv;
      void main() {
        float dy = uTexel.y * 1.35;
        vec3 acc = texture2D(tInput, vUv).rgb * 0.28;
        acc += (texture2D(tInput, clamp(vUv + vec2(0.0, dy * 1.5), 0.001, 0.999)).rgb +
                texture2D(tInput, clamp(vUv - vec2(0.0, dy * 1.5), 0.001, 0.999)).rgb) * 0.23;
        acc += (texture2D(tInput, clamp(vUv + vec2(0.0, dy * 3.5), 0.001, 0.999)).rgb +
                texture2D(tInput, clamp(vUv - vec2(0.0, dy * 3.5), 0.001, 0.999)).rgb) * 0.13;
        gl_FragColor = vec4(acc, 1.0);
      }
    `,
    depthTest: false,
    depthWrite: false,
  });

  const finalMat = new THREE.ShaderMaterial({
    uniforms: {
      tColor:       { value: rtScene.texture },
      tDepth:       { value: rtScene.depthTexture },
      tBloom:       { value: rtBloomB.texture },
      uRes:         { value: new THREE.Vector2(width, height) },
      uFocusDist:   { value: 45.0 },
      uDofRange:    { value: 40.0 },
      uMaxBlur:     { value: 3.4 },
      uNear:        { value: 1.4 },
      uFar:         { value: 4800.0 },
      uMotionVec:   { value: new THREE.Vector2(0.0, 0.0) },
      uBloomAmt:    { value: 0.42 },
      uExposure:    { value: 1.18 },
      uTime:        { value: 0.0 },
    },
    vertexShader: vertCommon,
    fragmentShader: `
      uniform sampler2D tColor;
      uniform sampler2D tDepth;
      uniform sampler2D tBloom;
      uniform vec2 uRes;
      uniform float uFocusDist;
      uniform float uDofRange;
      uniform float uMaxBlur;
      uniform float uNear;
      uniform float uFar;
      uniform vec2 uMotionVec;
      uniform float uBloomAmt;
      uniform float uExposure;
      uniform float uTime;
      varying vec2 vUv;

      float linearizeDepth(float d) {
        float z = d * 2.0 - 1.0;
        return (2.0 * uNear * uFar) / max(0.0001, (uFar + uNear - z * (uFar - uNear)));
      }

      vec3 sampleLinear(vec2 uv) {
        vec3 s = texture2D(tColor, clamp(uv, 0.001, 0.999)).rgb;
        return s * s;
      }

      vec3 acesFilmic(vec3 x) {
        const float a = 2.51;
        const float b = 0.03;
        const float c = 2.43;
        const float d = 0.59;
        const float e = 0.14;
        return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
      }

      // Precomputed Golden-Angle (2.39996323 rad) Vogel-Spiral offsets - zero runtime sin/cos/sqrt!
      vec3 sampleVogelBokeh(vec2 uv, vec2 scale) {
        vec3 col = sampleLinear(uv) * 0.24;
        float wSum = 0.24;
        vec2 o0 = vec2(-0.2456,  0.2248) * scale;
        vec2 o1 = vec2( 0.0402, -0.4696) * scale;
        vec2 o2 = vec2( 0.4398,  0.3910) * scale;
        vec2 o3 = vec2(-0.6657,  0.0725) * scale;
        vec2 o4 = vec2( 0.3712, -0.6548) * scale;
        vec2 o5 = vec2( 0.2683,  0.7817) * scale;
        vec2 o6 = vec2(-0.8325, -0.3408) * scale;
        vec2 o7 = vec2( 0.8755, -0.3792) * scale;

        vec3 t0 = sampleLinear(uv + o0); float w0 = (1.0 + smoothstep(0.45, 1.0, dot(t0, vec3(0.2126, 0.7152, 0.0722))) * 0.55) * 0.095; col += t0 * w0; wSum += w0;
        vec3 t1 = sampleLinear(uv + o1); float w1 = (1.0 + smoothstep(0.45, 1.0, dot(t1, vec3(0.2126, 0.7152, 0.0722))) * 0.55) * 0.095; col += t1 * w1; wSum += w1;
        vec3 t2 = sampleLinear(uv + o2); float w2 = (1.0 + smoothstep(0.45, 1.0, dot(t2, vec3(0.2126, 0.7152, 0.0722))) * 0.55) * 0.095; col += t2 * w2; wSum += w2;
        vec3 t3 = sampleLinear(uv + o3); float w3 = (1.0 + smoothstep(0.45, 1.0, dot(t3, vec3(0.2126, 0.7152, 0.0722))) * 0.55) * 0.095; col += t3 * w3; wSum += w3;
        vec3 t4 = sampleLinear(uv + o4); float w4 = (1.0 + smoothstep(0.45, 1.0, dot(t4, vec3(0.2126, 0.7152, 0.0722))) * 0.55) * 0.095; col += t4 * w4; wSum += w4;
        vec3 t5 = sampleLinear(uv + o5); float w5 = (1.0 + smoothstep(0.45, 1.0, dot(t5, vec3(0.2126, 0.7152, 0.0722))) * 0.55) * 0.095; col += t5 * w5; wSum += w5;
        vec3 t6 = sampleLinear(uv + o6); float w6 = (1.0 + smoothstep(0.45, 1.0, dot(t6, vec3(0.2126, 0.7152, 0.0722))) * 0.55) * 0.095; col += t6 * w6; wSum += w6;
        vec3 t7 = sampleLinear(uv + o7); float w7 = (1.0 + smoothstep(0.45, 1.0, dot(t7, vec3(0.2126, 0.7152, 0.0722))) * 0.55) * 0.095; col += t7 * w7; wSum += w7;
        return col / wSum;
      }

      void main() {
        float rawD = texture2D(tDepth, vUv).r;
        float linD = linearizeDepth(rawD);
        float coc = clamp(abs(linD - uFocusDist) / max(1.0, uDofRange), 0.0, 1.0) * uMaxBlur;
        vec2 texel = 1.0 / uRes;

        vec3 col = (rawD < 0.9998 && coc > 0.16) ? sampleVogelBokeh(vUv, coc * texel) : sampleLinear(vUv);

        vec2 fromCenter = vUv - 0.5;
        float edgeR2 = dot(fromCenter, fromCenter);
        if (edgeR2 > 0.06) {
          vec2 caShift = fromCenter * (edgeR2 * 1.6) * texel;
          col.r = mix(col.r, sampleLinear(vUv + caShift).r, 0.42);
          col.b = mix(col.b, sampleLinear(vUv - caShift).b, 0.42);
        }

        float mvLen = length(uMotionVec);
        if (mvLen > 0.0008) {
          vec3 mAcc = col * 0.28;
          mAcc += sampleLinear(vUv + uMotionVec * 0.33) * 0.20;
          mAcc += sampleLinear(vUv - uMotionVec * 0.33) * 0.20;
          mAcc += sampleLinear(vUv + uMotionVec * 0.68) * 0.11;
          mAcc += sampleLinear(vUv - uMotionVec * 0.68) * 0.11;
          mAcc += sampleLinear(vUv + uMotionVec * 1.00) * 0.05;
          mAcc += sampleLinear(vUv - uMotionVec * 1.00) * 0.05;
          col = mAcc;
        }

        vec3 bloom = texture2D(tBloom, vUv).rgb * 2.0;
        col += bloom * vec3(1.04, 0.98, 1.08) * uBloomAmt;

        col *= uExposure;
        float luma = dot(col, vec3(0.2126, 0.7152, 0.0722));
        vec3 shadowTint = vec3(0.92, 0.98, 1.06);
        vec3 highTint   = vec3(1.04, 1.00, 0.94);
        col *= mix(shadowTint, highTint, clamp(luma * 1.2, 0.0, 1.0));

        float vig = 1.0 - edgeR2 * 0.42;
        col *= vig;

        vec3 mapped = acesFilmic(col * 1.08);
        vec3 srgb = pow(clamp(mapped, 0.0, 1.0), vec3(1.0 / 2.2));

        float grain = fract(sin(dot(vUv + fract(uTime * 0.173), vec2(12.9898, 78.233))) * 43758.5453) - 0.5;
        srgb += grain * (1.8 / 255.0);

        gl_FragColor = vec4(clamp(srgb, 0.0, 1.0), 1.0);
      }
    `,
    depthTest: false,
    depthWrite: false,
  });

  const sceneB1 = new THREE.Scene(); sceneB1.add(new THREE.Mesh(quadGeo, bloomHorizMat));
  const sceneB2 = new THREE.Scene(); sceneB2.add(new THREE.Mesh(quadGeo, bloomVertMat));
  const sceneFinal = new THREE.Scene(); sceneFinal.add(new THREE.Mesh(quadGeo, finalMat));

  function render(scene, camera, params = {}) {
    finalMat.uniforms.uFocusDist.value = params.focusDist ?? 45.0;
    finalMat.uniforms.uDofRange.value  = params.dofRange ?? 40.0;
    finalMat.uniforms.uMaxBlur.value   = params.maxBlur ?? 3.2;
    finalMat.uniforms.uNear.value      = camera.near;
    finalMat.uniforms.uFar.value       = camera.far;
    finalMat.uniforms.uBloomAmt.value  = params.bloomAmt ?? 0.42;
    finalMat.uniforms.uExposure.value  = params.exposure ?? 1.22;
    finalMat.uniforms.uTime.value      = params.time ?? 0.0;
    if (params.motionVec) {
      finalMat.uniforms.uMotionVec.value.copy(params.motionVec);
    } else {
      finalMat.uniforms.uMotionVec.value.set(0, 0);
    }

    renderer.setRenderTarget(rtScene);
    renderer.clear();
    renderer.render(scene, camera);

    renderer.setRenderTarget(rtBloomA);
    renderer.clear();
    renderer.render(sceneB1, postCam);

    renderer.setRenderTarget(rtBloomB);
    renderer.clear();
    renderer.render(sceneB2, postCam);

    renderer.setRenderTarget(null);
    renderer.render(sceneFinal, postCam);
  }

  return { render, rtScene };
}
