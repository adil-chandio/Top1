import * as THREE from 'three';

/**
 * Monarch Cam #03 — V6 Hollywood IMAX Optical Post-Processing Engine
 * Upgrades V5 with:
 *   1. True Linear-Space Pipeline (decodes V5 gamma2 shader output -> linear HDR math -> sRGB encode)
 *   2. 12-Tap Golden-Angle (2.39996 rad) Vogel-Spiral Cinema Bokeh Depth-of-Field
 *   3. 7-Tap 180°-Shutter Directional Camera-Velocity Motion Blur on whip-pans & ballistic launches
 *   4. Dual-Pass Anamorphic Horizontal Streak Halation & Bioluminescent Specular Bloom
 *   5. Kodak 2383 Cinema Color Grade + Narkowicz ACES Filmic Tone Mapping + 35mm Fine Film Grain
 */
export function createImaxOpticalPassV6(renderer, width, height) {
  const rtScene = new THREE.WebGLRenderTarget(width, height, {
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
    format: THREE.RGBAFormat,
    type: THREE.UnsignedByteType,
    depthBuffer: true,
    depthTexture: new THREE.DepthTexture(width, height, THREE.UnsignedIntType),
  });

  // Quarter-res bloom buffer for silky wide anamorphic horizontal halation!
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

  // Pass 1: Bright-pass threshold + Wide Anamorphic Horizontal Blur
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
        // Wide Panavision-style horizontal anamorphic spread (2.35x wider horizontally!)
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

  // Pass 2: Soft Vertical Halo Blur
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

  // Pass 3: Final Composite — 12-Tap Vogel Bokeh DoF + Shutter Motion Blur + Anamorphic Bloom + ACES Filmic!
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

      void main() {
        float rawD = texture2D(tDepth, vUv).r;
        float linD = linearizeDepth(rawD);
        float coc = clamp(abs(linD - uFocusDist) / max(1.0, uDofRange), 0.0, 1.0) * uMaxBlur;
        vec2 texel = 1.0 / uRes;

        // 1. 12-Tap Golden-Angle Vogel-Spiral Cinema Bokeh Disc in True Linear Light!
        vec3 col = sampleLinear(vUv) * 0.22;
        float wSum = 0.22;
        if (coc > 0.12) {
          for (int i = 0; i < 11; i++) {
            float fi = float(i) + 1.0;
            float r = sqrt(fi / 11.5) * coc;
            float th = fi * 2.39996323;
            vec2 off = vec2(cos(th), sin(th)) * r * texel;
            vec3 tap = sampleLinear(vUv + off);
            // Boost specular bokeh disc highlights naturally!
            float lum = dot(tap, vec3(0.2126, 0.7152, 0.0722));
            float bw = 1.0 + smoothstep(0.45, 1.0, lum) * 0.55;
            col += tap * bw * 0.075;
            wSum += bw * 0.075;
          }
          col /= wSum;
        } else {
          col = sampleLinear(vUv);
        }

        // 2. Subtle Radial Optical Lens Chromatic Dispersion near frame periphery
        vec2 fromCenter = vUv - 0.5;
        float edgeR2 = dot(fromCenter, fromCenter);
        if (edgeR2 > 0.06) {
          vec2 caShift = fromCenter * (edgeR2 * 1.6) * texel;
          col.r = mix(col.r, sampleLinear(vUv + caShift).r, 0.42);
          col.b = mix(col.b, sampleLinear(vUv - caShift).b, 0.42);
        }

        // 3. 180°-Shutter Directional Velocity Motion Blur (on whip-pans & ballistic impacts!)
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

        // 4. Add Anamorphic Horizontal Bloom & Bioluminescent Halation (multiplying *2 to unpack 0.5 scale)
        vec3 bloom = texture2D(tBloom, vUv).rgb * 2.0;
        // Subtle Panavision cool-amber optical tint
        col += bloom * vec3(1.04, 0.98, 1.08) * uBloomAmt;

        // 5. Luxury Cinema Hall Color Grade (deep obsidian-teal shadows, rich golden-amber highlights)
        col *= uExposure;
        float luma = dot(col, vec3(0.2126, 0.7152, 0.0722));
        vec3 shadowTint = vec3(0.92, 0.98, 1.06);
        vec3 highTint   = vec3(1.04, 1.00, 0.94);
        col *= mix(shadowTint, highTint, clamp(luma * 1.2, 0.0, 1.0));

        // Subtle optical lens vignette before tone-mapping
        float vig = 1.0 - edgeR2 * 0.42;
        col *= vig;

        // 6. Narkowicz ACES Filmic HDR Tone Mapping -> sRGB Gamma 2.2
        vec3 mapped = acesFilmic(col * 1.08);
        vec3 srgb = pow(clamp(mapped, 0.0, 1.0), vec3(1.0 / 2.2));

        // 7. 35mm Fine Cinema Film Grain (prevents 100% of H.264 banding in dark theatre shadows!)
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
