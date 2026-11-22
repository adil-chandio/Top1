import * as THREE from 'three';
import { createCockroachActor, createSagittalCutawayRig, GLM } from './cockroach3d.js';
import { makeFastMaterial } from './materials.js';

/**
 * Create soft radial glow sprite texture for contact shadows, warm doorway spill, and floating dust bokeh.
 */
function makeGlowTexture(innerHex = '#ffffff', outerHex = '#00000000') {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 1, 64, 64, 62);
  g.addColorStop(0.0, innerHex);
  g.addColorStop(0.42, innerHex + '88');
  g.addColorStop(0.88, innerHex + '14');
  g.addColorStop(1.0, '#00000000');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  return t;
}

/**
 * Build realistic minted 3D US Penny (19.05 mm diameter x 1.52 mm thickness) with raised bevel rim.
 */
function createCopperPenny(mats) {
  const g = new THREE.Group();
  const R = 9.525, H = 1.52;
  const core = new THREE.Mesh(new THREE.CylinderGeometry(R - 0.18, R - 0.18, H, 48), mats.copperMat);
  core.castShadow = true;
  core.receiveShadow = true;
  g.add(core);
  // Raised obverse & reverse coin rims
  const rimGeo = new THREE.TorusGeometry(R - 0.22, 0.22, 10, 48);
  rimGeo.rotateX(Math.PI / 2);
  for (const s of [-1, 1]) {
    const rim = new THREE.Mesh(rimGeo, mats.copperMat);
    rim.position.y = s * (H * 0.5 - 0.06);
    rim.scale.set(1, 0.55, 1);
    g.add(rim);
  }
  return g;
}

/**
 * Dielectric Fresnel clear acrylic slab material (inspired by tools/gecko/premiere/window.js & bench.js).
 */
function createAcrylicMaterial(tint = [0.62, 0.88, 0.88], baseAlpha = 0.16) {
  return new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    uniforms: {
      uTint: { value: new THREE.Vector3(...tint) },
      uAlpha: { value: baseAlpha },
    },
    vertexShader: `
      varying vec3 vNormalW;
      varying vec3 vWorldPos;
      varying vec2 vUv;
      void main() {
        vUv = uv;
        vNormalW = normalize(mat3(modelMatrix) * normal);
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorldPos = wp.xyz;
        gl_Position = projectionMatrix * viewMatrix * wp;
      }
    `,
    fragmentShader: `
      varying vec3 vNormalW;
      varying vec3 vWorldPos;
      varying vec2 vUv;
      uniform vec3 uTint;
      uniform float uAlpha;
      void main() {
        vec3 V = normalize(cameraPosition - vWorldPos);
        float fresnel = pow(clamp(1.0 - abs(dot(normalize(vNormalW), V)), 0.0, 1.0), 3.0);
        // Subtle optical specular diagonal sheen across laboratory acrylic
        float streak1 = exp(-22.0 * abs(vUv.x - 0.34 - 0.18 * vUv.y));
        float streak2 = exp(-36.0 * abs(vUv.x - 0.72 + 0.22 * vUv.y));
        float edgeRule = smoothstep(0.46, 0.50, max(abs(vUv.x - 0.5), abs(vUv.y - 0.5)));
        vec3 col = mix(uTint, vec3(0.98, 0.94, 0.86), streak1 * 0.45) + vec3(0.45, 0.72, 0.74) * edgeRule * 0.55;
        float alpha = clamp(uAlpha + fresnel * 0.36 + (streak1 + streak2) * 0.11 + edgeRule * 0.32, 0.0, 0.78);
        gl_FragColor = vec4(col, alpha);
      }
    `,
  });
}

/**
 * Fast, studio-grade Optical Post-Processing Pass (Circle-of-Confusion Depth-of-Field +
 * Warm Specular Bloom + Vignette + ACES Filmic Tonemapping + Fine 35mm Cinema Grain).
 */
export function createOpticalLensPass(renderer, width, height) {
  const rt = new THREE.WebGLRenderTarget(width, height, {
    type: THREE.UnsignedByteType,
    depthBuffer: true,
    depthTexture: new THREE.DepthTexture(width, height, THREE.UnsignedIntType),
  });
  const postScene = new THREE.Scene();
  const postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  const uniforms = {
    tColor: { value: rt.texture },
    tDepth: { value: rt.depthTexture },
    uStep: { value: new THREE.Vector2(1 / width, 1 / height) },
    uNear: { value: 1.0 },
    uFar: { value: 450.0 },
    uFocus: { value: 38.0 },
    uAperture: { value: 5.5 },
    uExposure: { value: 1.12 },
    uBloom: { value: 0.28 },
    uVignette: { value: 0.34 },
    uTime: { value: 0.0 },
  };

  const mat = new THREE.ShaderMaterial({
    uniforms,
    depthTest: false,
    depthWrite: false,
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
    fragmentShader: `
      varying vec2 vUv;
      uniform sampler2D tColor, tDepth;
      uniform vec2 uStep;
      uniform float uNear, uFar, uFocus, uAperture, uExposure, uBloom, uVignette, uTime;

      vec3 fetchLin(vec2 uv) {
        vec3 s = texture2D(tColor, clamp(uv, vec2(0.001), vec2(0.999))).rgb;
        return s * s; // Exact gamma-2.0 linearize with ZERO pow()/exp2()/log2()!
      }

      void main() {
        float z = texture2D(tDepth, vUv).r;
        float viewZ = (uNear * uFar) / max(0.0001, (uFar - z * (uFar - uNear)));
        float coc = min(3.6, uAperture * abs(viewZ - uFocus) / max(8.0, viewZ) * 3.8);

        vec3 c0 = fetchLin(vUv);
        vec2 rad = uStep * max(coc, 1.8);
        vec3 s1 = fetchLin(vUv + vec2( rad.x,  rad.y * 0.4));
        vec3 s2 = fetchLin(vUv + vec2(-rad.x, -rad.y * 0.4));
        vec3 s3 = fetchLin(vUv + vec2(-rad.x * 0.4,  rad.y));
        vec3 s4 = fetchLin(vUv + vec2( rad.x * 0.4, -rad.y));
        vec3 ring = (s1 + s2 + s3 + s4) * 0.25;

        float dofMix = clamp((coc - 0.22) * 0.48, 0.0, 0.78);
        vec3 col = mix(c0, ring, dofMix);

        // Fused warm highlight halation from the same 4 ring taps (zero extra texture fetches!)
        vec3 bSample = max(ring - vec3(0.52), 0.0);
        col += bSample * uBloom * vec3(1.15, 0.92, 0.75);

        // Optical exposure + gentle natural lens vignette
        vec2 vd = (vUv - 0.5) * vec2(1.14, 0.84);
        col *= uExposure * 0.94 * (1.0 - dot(vd, vd) * uVignette * 0.85);

        // Filmic curve + fast hardware sqrt gamma!
        col = (col * (2.42 * col + 0.08)) / (col * (2.35 * col + 0.54) + 0.13);
        vec3 srgb = sqrt(clamp(col, 0.0, 1.0));

        // Clean spatial anti-banding dither (prevents 8-bit gradient banding without temporal H.264 noise bloat!)
        float dither = (fract(dot(gl_FragCoord.xy, vec2(0.46711056, 0.00583715)) * 52.9829189) - 0.5) * (1.5 / 255.0);
        srgb += dither;

        gl_FragColor = vec4(clamp(srgb, 0.0, 1.0), 1.0);
      }
    `,
  });
  postScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat));

  return {
    rt,
    render(scene, camera, lensParams = {}) {
      uniforms.uNear.value = camera.near;
      uniforms.uFar.value = camera.far;
      uniforms.uFocus.value = lensParams.focus ?? 42.0;
      uniforms.uAperture.value = lensParams.aperture ?? 4.8;
      uniforms.uExposure.value = lensParams.exposure ?? 1.15;
      uniforms.uBloom.value = lensParams.bloom ?? 0.28;
      uniforms.uVignette.value = lensParams.vignette ?? 0.34;
      uniforms.uTime.value = lensParams.time ?? 0.0;

      renderer.setRenderTarget(rt);
      renderer.render(scene, camera);
      renderer.setRenderTarget(null);
      renderer.render(postScene, postCam);
    },
  };
}

/**
 * Construct the complete Multi-Stage Monarch Cam Episode #03 3D Studio World.
 */
export function createMonarchWorld(mats) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#071215');
  scene.fog = new THREE.FogExp2('#071215', 0.0022);

  // Studio + Macro Naturalistic Lighting Rig (lush midtone & shadow readability like Ant V3 & Gecko Premiere!)
  const ambient = new THREE.AmbientLight('#5e7278', 1.15);
  scene.add(ambient);

  const hemi = new THREE.HemisphereLight('#a4dce6', '#5c3c24', 1.55);
  scene.add(hemi);

  const keyLight = new THREE.DirectionalLight('#ffdcaf', 3.15);
  keyLight.position.set(32, 68, 38);
  keyLight.castShadow = false;
  scene.add(keyLight);
  scene.add(keyLight.target);

  const frontFill = new THREE.DirectionalLight('#ffd6ae', 1.55);
  frontFill.position.set(-18, 32, 58);
  scene.add(frontFill);

  const rimLight = new THREE.DirectionalLight('#86d8e2', 1.85);
  rimLight.position.set(-45, 36, -42);
  scene.add(rimLight);

  const macroFill = new THREE.PointLight('#ffcc88', 2.2, 160, 1.1);
  macroFill.position.set(14, 14, 24);
  scene.add(macroFill);

  // Soft elliptical contact-shadow decal right beneath hero cockroach so it is 100% grounded even under shallow grazing light
  const shadowGlow = makeGlowTexture('#050809', '#05080900');
  const contactShadow = new THREE.Mesh(
    new THREE.PlaneGeometry(38, 24),
    new THREE.MeshBasicMaterial({ map: shadowGlow, transparent: true, opacity: 0.62, depthWrite: false })
  );
  contactShadow.rotation.x = -Math.PI / 2;
  contactShadow.position.y = 0.025;
  scene.add(contactShadow);

  // Floating macro atmospheric dust motes (inspired by tools/gecko/premiere/window.js)
  const dustCount = 180;
  const dustPos = new Float32Array(dustCount * 3);
  for (let i = 0; i < dustCount; i++) {
    const s1 = Math.sin(i * 12.9898) * 43758.5453;
    const s2 = Math.sin(i * 78.233 + 1.7) * 29431.113;
    const s3 = Math.sin(i * 41.137 + 3.3) * 19173.731;
    dustPos[i * 3]     = ((s1 - Math.floor(s1)) - 0.5) * 160;
    dustPos[i * 3 + 1] = 1.5 + (s2 - Math.floor(s2)) * 38;
    dustPos[i * 3 + 2] = ((s3 - Math.floor(s3)) - 0.5) * 120;
  }
  const dustGeo = new THREE.BufferGeometry();
  dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
  const dustPoints = new THREE.Points(
    dustGeo,
    new THREE.PointsMaterial({
      map: makeGlowTexture('#ffe2b5', '#ffe2b500'),
      size: 0.95,
      transparent: true,
      opacity: 0.34,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  );
  scene.add(dustPoints);

  // =========================================================================
  // STAGE A: Nocturnal Oak Doorway Threshold + Two Stacked Copper Pennies
  // =========================================================================
  const thresholdStage = new THREE.Group();
  scene.add(thresholdStage);

  const oakFloor = new THREE.Mesh(new THREE.PlaneGeometry(340, 260), mats.oakMat);
  oakFloor.rotation.x = -Math.PI / 2;
  oakFloor.receiveShadow = true;
  thresholdStage.add(oakFloor);

  // Nocturnal bokeh far depth backdrop
  const bokehBackdrop = new THREE.Mesh(
    new THREE.PlaneGeometry(420, 210),
    new THREE.MeshBasicMaterial({ map: mats.textures.bokehTex, color: '#8ca8ad', fog: false })
  );
  bokehBackdrop.position.set(30, 62, -118);
  thresholdStage.add(bokehBackdrop);

  // Stained dark-walnut closed door leaf
  const doorMat = makeFastMaterial({
    color: '#523826',
    specular: '#9e7a5e',
    specPower: 0.48,
    map: mats.textures.oakAlbedo,
    normalMap: mats.textures.oakNormal,
    normalScale: 0.45,
    rimTint: [0.85, 0.58, 0.34],
    rimStrength: 0.18,
  });
  const doorSlab = new THREE.Mesh(new THREE.BoxGeometry(24, 48, 98), doorMat);
  const doorLip = new THREE.Mesh(
    new THREE.BoxGeometry(24.6, 1.1, 98.4),
    makeFastMaterial({ color: '#b48a56', specular: '#ffe6be', specPower: 0.94, rimTint: [1.0, 0.78, 0.45], rimStrength: 0.35 })
  );
  doorLip.position.y = -24.0 + 0.55;
  doorSlab.add(doorLip);
  thresholdStage.add(doorSlab);

  // Warm hallway light spilling from BEYOND the closed door (+X > 30 mm) through the 3.2 mm crack!
  const spillPlane = new THREE.Mesh(
    new THREE.PlaneGeometry(110, 130),
    new THREE.MeshBasicMaterial({
      map: makeGlowTexture('#ffae52', '#ffae5200'),
      transparent: true,
      opacity: 0.26,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
  );
  spillPlane.rotation.x = -Math.PI / 2;
  spillPlane.position.set(24, 0.04, -22);
  thresholdStage.add(spillPlane);

  // Two stacked US copper pennies (1.52 mm + 1.52 mm = 3.04 mm) in open light right beside the 3.2 mm door corner!
  const pennyStack = new THREE.Group();
  const pennyShadow = new THREE.Mesh(
    new THREE.PlaneGeometry(25.5, 25.5),
    new THREE.MeshBasicMaterial({ map: makeGlowTexture('#000000', '#00000000'), transparent: true, opacity: 0.62, depthWrite: false })
  );
  pennyShadow.rotation.x = -Math.PI / 2;
  pennyShadow.position.set(0.2, 0.03, -0.1);
  pennyStack.add(pennyShadow);
  const pennyBottom = createCopperPenny(mats);
  pennyBottom.position.set(0, 0.76, 0);
  const pennyTop = createCopperPenny(mats);
  pennyTop.position.set(0.45, 1.52 + 0.76, -0.28);
  pennyTop.rotation.y = 1.1;
  pennyStack.add(pennyBottom, pennyTop);
  pennyStack.position.set(11.5, 0, 23.5);
  thresholdStage.add(pennyStack);

  // =========================================================================
  // STAGE B: High-Speed 500fps Acrylic & Brushed-Alloy Lab Tunnel / Gate Rig
  // =========================================================================
  const corridorStage = new THREE.Group();
  scene.add(corridorStage);

  const gritFloor = new THREE.Mesh(new THREE.PlaneGeometry(320, 220), mats.gritMat);
  gritFloor.rotation.x = -Math.PI / 2;
  gritFloor.receiveShadow = true;
  corridorStage.add(gritFloor);

  // 160 Instanced 3D Mineral Grit Grains concentrated in the active macro corridor for real geometric floor micro-relief!
  const grainGeo = new THREE.DodecahedronGeometry(0.16, 0);
  const grainMat = makeFastMaterial({ color: '#3b3632', specular: '#786e64', specPower: 0.25, rimTint: [0.4, 0.38, 0.35], rimStrength: 0.08 });
  const grainsInst = new THREE.InstancedMesh(grainGeo, grainMat, 160);
  {
    const m = new THREE.Matrix4(), p = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3(), e = new THREE.Euler();
    for (let i = 0; i < 160; i++) {
      const r1 = fract(Math.sin(i * 91.7 + 0.3) * 43758.5);
      const r2 = fract(Math.sin(i * 37.3 + 1.9) * 19283.7);
      const r3 = fract(Math.sin(i * 63.1 + 4.2) * 31847.2);
      p.set((r1 - 0.5) * 96, 0.05 + r3 * 0.08, (r2 - 0.5) * 38);
      e.set(r1 * 6, r2 * 6, r3 * 6);
      q.setFromEuler(e);
      const sc = 0.55 + r3 * 1.25;
      s.set(sc * 1.2, sc * 0.55, sc);
      m.compose(p, q, s);
      grainsInst.setMatrixAt(i, m);
    }
    grainsInst.instanceMatrix.needsUpdate = true;
  }
  corridorStage.add(grainsInst);

  // Precision brushed dark-alloy side rails + adjustable clear dielectric acrylic ceiling!
  const alloyMat = makeFastMaterial({ color: '#2f3e42', specular: '#9bc0c6', specPower: 0.85, rimTint: [0.55, 0.78, 0.82], rimStrength: 0.28 });
  const trimMat = makeFastMaterial({ color: '#789aa0', specular: '#dcf2f6', specPower: 0.95, rimTint: [0.75, 0.92, 0.96], rimStrength: 0.35 });
  for (const zs of [-1, 1]) {
    const rail = new THREE.Mesh(new THREE.BoxGeometry(170, 1.4, 2.2), alloyMat);
    rail.position.set(0, 0.7, zs * 22.5);
    rail.castShadow = true;
    corridorStage.add(rail);
    const bevelStrip = new THREE.Mesh(new THREE.BoxGeometry(170, 0.25, 0.45), trimMat);
    bevelStrip.position.set(0, 1.45, zs * 21.6);
    corridorStage.add(bevelStrip);
  }

  // Adjustable clear acrylic corridor roof (150 mm long x 43 mm wide x 1.2 mm thick)
  const acrylicRoofMat = createAcrylicMaterial([0.64, 0.90, 0.90], 0.17);
  const acrylicRoof = new THREE.Mesh(new THREE.BoxGeometry(155, 1.1, 43), acrylicRoofMat);
  const roofEdges = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(155, 1.1, 43)),
    new THREE.LineBasicMaterial({ color: '#9de4df', transparent: true, opacity: 0.55 })
  );
  acrylicRoof.add(roofEdges);
  corridorStage.add(acrylicRoof);

  // Gate mode vertical acrylic barrier (for 5-move slot traversal & 315-attempt narrowing gate in Ch2 & Ch6!)
  const gateAssembly = new THREE.Group();
  const gateWallMat = createAcrylicMaterial([0.58, 0.84, 0.88], 0.24);
  const gateSlab = new THREE.Mesh(new THREE.BoxGeometry(8.5, 36.0, 43.0), gateWallMat);
  gateSlab.position.y = 18.0;
  const gateLipMetal = new THREE.Mesh(new THREE.BoxGeometry(8.8, 0.65, 43.2), trimMat);
  gateLipMetal.position.y = 0.32;
  gateAssembly.add(gateSlab, gateLipMetal);
  corridorStage.add(gateAssembly);

  // Etched vertical millimeter scale post on far rail (-Z = -21 mm)
  const scalePost = new THREE.Group();
  const postBody = new THREE.Mesh(new THREE.BoxGeometry(2.4, 18.0, 0.9), alloyMat);
  postBody.position.y = 9.0;
  scalePost.add(postBody);
  const tickMat = new THREE.MeshBasicMaterial({ color: '#cfeae8' });
  for (let mm = 1; mm <= 15; mm++) {
    const isMajor = (mm === 3 || mm === 4 || mm === 6 || mm === 9 || mm === 12 || mm === 15);
    const tick = new THREE.Mesh(new THREE.BoxGeometry(isMajor ? 1.5 : 0.8, 0.14, 0.96), tickMat);
    tick.position.set(0.3, mm, 0);
    scalePost.add(tick);
  }
  scalePost.position.set(16.0, 0, -21.2);
  corridorStage.add(scalePost);

  // Penny stack duplicate inside corridor rig when comparing 3.2 mm lab gate vs two pennies
  const labPennyStack = pennyStack.clone();
  labPennyStack.position.set(16.0, 0, 17.5);
  corridorStage.add(labPennyStack);

  // =========================================================================
  // STAGE C: Deep Petrol-Teal (#08181c) 3D Sagittal Exoskeleton Cutaway Stage
  // =========================================================================
  const cutawayStage = new THREE.Group();
  const studioPedestal = new THREE.Mesh(
    new THREE.CylinderGeometry(36, 38, 1.2, 64),
    makeFastMaterial({ color: '#09181d', specular: '#2c545c', specPower: 0.62, rimTint: [0.22, 0.48, 0.54], rimStrength: 0.14 })
  );
  studioPedestal.position.y = -0.6;
  studioPedestal.receiveShadow = true;
  cutawayStage.add(studioPedestal);

  const studioBackdropGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(110, 62),
    new THREE.MeshBasicMaterial({
      map: makeGlowTexture('#1a464f', '#06111400'),
      transparent: true,
      opacity: 0.75,
      depthWrite: false,
    })
  );
  studioBackdropGlow.position.set(-1.5, 8.0, -14.0);
  cutawayStage.add(studioBackdropGlow);

  const sagittalRig = createSagittalCutawayRig(mats);
  cutawayStage.add(sagittalRig.group);
  scene.add(cutawayStage);

  // =========================================================================
  // STAGE D: Multi-Lane 3D Experimental Comparison Stage (Ch3 Height Cliff & Ch5 Grit Matrix)
  // =========================================================================
  const comparisonStage = new THREE.Group();
  scene.add(comparisonStage);

  const laneSpecs = [-21.5, 0.0, 21.5];
  const compLanes = laneSpecs.map((zCenter, idx) => {
    const g = new THREE.Group();
    g.position.z = zCenter;
    const baseMat = idx === 0
      ? new THREE.MeshPhongMaterial({ color: '#263438', specular: '#9ac2c8', shininess: 95 }) // Slick 100-grit / high-ceiling lane
      : idx === 1
        ? mats.gritMat // Medium 40-grit optimal lane
        : new THREE.MeshPhongMaterial({
            color: '#5b5248',
            specular: '#484039',
            shininess: 14,
            map: mats.textures.rubbleAlbedo,
            normalMap: mats.textures.rubbleNormal,
            normalScale: new THREE.Vector2(1.5, 1.5),
          }); // Coarse 20-grit snag lane
    const track = new THREE.Mesh(new THREE.BoxGeometry(130, 1.2, 18.5), baseMat);
    track.position.y = -0.6;
    track.receiveShadow = true;
    const roof = new THREE.Mesh(new THREE.BoxGeometry(130, 0.8, 18.5), createAcrylicMaterial([0.62, 0.88, 0.88], 0.18));
    const rim = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(130, 0.8, 18.5)),
      new THREE.LineBasicMaterial({ color: idx === 1 ? '#ffd187' : '#80b8be', transparent: true, opacity: 0.55 })
    );
    roof.add(rim);
    g.add(track, roof);
    comparisonStage.add(g);
    const runner = createCockroachActor(mats);
    g.add(runner.root);
    return { group: g, track, roof, runner };
  });

  // Primary Hero Cockroach Actor (used in Threshold, Corridor, and Macro Leg stages)
  const heroActor = createCockroachActor(mats);
  scene.add(heroActor.root);

  return {
    scene,
    lights: { hemi, keyLight, rimLight, macroFill },
    contactShadow,
    dustPoints,
    stages: {
      thresholdStage,
      corridorStage,
      cutawayStage,
      comparisonStage,
    },
    props: {
      doorSlab,
      spillPlane,
      pennyStack,
      acrylicRoof,
      gateAssembly,
      scalePost,
      labPennyStack,
      sagittalRig,
      compLanes,
    },
    heroActor,
  };
}

function fract(x) {
  return x - Math.floor(x);
}
