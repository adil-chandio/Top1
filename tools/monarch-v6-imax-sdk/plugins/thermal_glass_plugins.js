import * as THREE from 'three';
import { mulberry32 } from '../core/pbr_shadow_sdk.js';
import { GLM, createGroundContactAO } from '../core/sculpt_ik_rig_sdk.js';

/**
 * Monarch V6 Hollywood IMAX Cinema SDK — Reusable Photoreal Crystal Glass,
 * Physical Pitcher/Heater Props, Jagged Cleavage Fractures, Zack D. 3D Atomic Shear Cutaway
 * & NaN-Proof 96-Shard Voronoi Shatter Plugins (`plugins/thermal_glass_plugins.js`).
 */

/**
 * 1. Procedural 3-Strip Cinema Studio Softbox HDR Reflection Environment (`PMREMGenerator`).
 * Zero per-frame render cost on SwiftShader, gives curved glass & water real studio highlights!
 */
export function createStudioSoftboxEnvMap(renderer) {
  const W = 1024;
  const H = 512;
  const cv = document.createElement('canvas');
  cv.width = W;
  cv.height = H;
  const ctx = cv.getContext('2d');

  // Base dark obsidian studio gradient
  const bg = ctx.createLinearGradient(0, 0, 0, H);
  bg.addColorStop(0.0, '#101824');
  bg.addColorStop(0.46, '#070b11');
  bg.addColorStop(0.52, '#04060a');
  bg.addColorStop(1.0, '#090d14');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, W, H);

  // Overhead diffused skylight box
  const topBox = ctx.createRadialGradient(W * 0.5, H * 0.08, 10, W * 0.5, H * 0.08, 220);
  topBox.addColorStop(0.0, 'rgba(240, 248, 255, 0.95)');
  topBox.addColorStop(0.45, 'rgba(180, 220, 245, 0.38)');
  topBox.addColorStop(1.0, 'rgba(0, 0, 0, 0)');
  ctx.fillStyle = topBox;
  ctx.fillRect(0, 0, W, H * 0.45);

  // Crisp vertical studio softbox strips (creates authentic vertical glass reflections!)
  const strips = [
    { x: W * 0.16, w: 38, col0: 'rgba(110, 242, 255, 0.98)', col1: 'rgba(58, 212, 190, 0.0)' },
    { x: W * 0.38, w: 54, col0: 'rgba(255, 246, 230, 1.00)', col1: 'rgba(255, 220, 175, 0.0)' },
    { x: W * 0.64, w: 46, col0: 'rgba(255, 240, 218, 0.95)', col1: 'rgba(255, 180, 95, 0.0)' },
    { x: W * 0.84, w: 34, col0: 'rgba(255, 152, 72, 0.92)',  col1: 'rgba(255, 90, 30, 0.0)' },
  ];
  for (const st of strips) {
    const g = ctx.createLinearGradient(st.x - st.w, 0, st.x + st.w, 0);
    g.addColorStop(0.0, st.col1);
    g.addColorStop(0.35, st.col0);
    g.addColorStop(0.65, st.col0);
    g.addColorStop(1.0, st.col1);
    ctx.fillStyle = g;
    ctx.fillRect(st.x - st.w, H * 0.08, st.w * 2, H * 0.62);
  }

  // Horizon rim line
  const hor = ctx.createLinearGradient(0, H * 0.47, 0, H * 0.55);
  hor.addColorStop(0.0, 'rgba(70, 165, 195, 0.0)');
  hor.addColorStop(0.5, 'rgba(95, 205, 230, 0.34)');
  hor.addColorStop(1.0, 'rgba(20, 40, 55, 0.0)');
  ctx.fillStyle = hor;
  ctx.fillRect(0, H * 0.46, W, H * 0.10);

  const eqTex = new THREE.CanvasTexture(cv);
  eqTex.mapping = THREE.EquirectangularReflectionMapping;
  eqTex.colorSpace = THREE.SRGBColorSpace;

  const pmrem = new THREE.PMREMGenerator(renderer);
  pmrem.compileEquirectangularShader();
  const envRT = pmrem.fromEquirectangular(eqTex);
  eqTex.dispose();
  pmrem.dispose();
  return envRT.texture;
}

/**
 * 2. Double-Walled Sealed Crystal Glass Tumbler Plugin (with real wall thickness,
 * heavy optical base meniscus, Fresnel grazing rim & ground contact AO).
 */
export function createDoubleWallCrystalGlass({
  baseRadius = 0.50,
  topRadius = 0.59,
  wallThickness = 0.068,
  baseThickness = 0.24,
  height = 2.08,
  radialSegs = 72,
  tintHex = '#d8f4fa',
  rimHex = '#8cf0ff',
  yFloor = 0.22,
} = {}) {
  const group = new THREE.Group();
  group.position.set(0, yFloor, 0);

  // Closed double-wall profile (outer base -> outer wall -> rounded lip -> inner wall -> solid meniscus)
  const pts = [
    new THREE.Vector2(0.001, 0.002),
    new THREE.Vector2(baseRadius * 0.93, 0.002),
    new THREE.Vector2(baseRadius, 0.045),
    new THREE.Vector2(baseRadius + (topRadius - baseRadius) * 0.45, height * 0.48),
    new THREE.Vector2(topRadius, height - 0.035),
    new THREE.Vector2(topRadius - wallThickness * 0.22, height + 0.012),
    new THREE.Vector2(topRadius - wallThickness * 0.78, height + 0.012),
    new THREE.Vector2(topRadius - wallThickness, height - 0.035),
    new THREE.Vector2(baseRadius - wallThickness + (topRadius - baseRadius) * 0.35, height * 0.45),
    new THREE.Vector2(baseRadius - wallThickness * 1.12, baseThickness + 0.05),
    new THREE.Vector2(baseRadius * 0.62, baseThickness),
    new THREE.Vector2(0.001, baseThickness - 0.012),
  ];
  const geo = new THREE.LatheGeometry(pts, radialSegs);
  geo.computeVertexNormals();

  const glassMat = new THREE.MeshPhysicalMaterial({
    color: tintHex,
    transparent: true,
    opacity: 0.34,
    roughness: 0.035,
    metalness: 0.04,
    reflectivity: 1.0,
    clearcoat: 1.0,
    clearcoatRoughness: 0.03,
    envMapIntensity: 2.5,
    side: THREE.DoubleSide,
    depthWrite: false,
  });

  const mesh = new THREE.Mesh(geo, glassMat);
  mesh.renderOrder = 12;
  group.add(mesh);

  // Grazing-angle Fresnel crystal edge highlight (makes silhouette pop on mobile!)
  const fresnelMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.FrontSide,
    blending: THREE.AdditiveBlending,
    uniforms: {
      uRimColor: { value: new THREE.Color(rimHex) },
      uWarmColor: { value: new THREE.Color('#ff8840') },
      uHeatMix: { value: 0.0 },
      uOpacity: { value: 0.85 },
    },
    vertexShader: `
      varying vec3 vWorldN;
      varying vec3 vWorldP;
      varying vec2 vUv;
      void main() {
        vUv = uv;
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorldP = wp.xyz;
        vWorldN = normalize(mat3(modelMatrix) * normal);
        gl_Position = projectionMatrix * viewMatrix * wp;
      }
    `,
    fragmentShader: `
      uniform vec3 uRimColor;
      uniform vec3 uWarmColor;
      uniform float uHeatMix;
      uniform float uOpacity;
      varying vec3 vWorldN;
      varying vec3 vWorldP;
      varying vec2 vUv;
      void main() {
        vec3 V = normalize(cameraPosition - vWorldP);
        float fres = pow(1.0 - clamp(abs(dot(vWorldN, V)), 0.0, 1.0), 3.1);
        float lipBoost = smoothstep(0.88, 1.0, vUv.y) * 0.45 + smoothstep(0.14, 0.0, vUv.y) * 0.35;
        vec3 col = mix(uRimColor, uWarmColor, uHeatMix * 0.55);
        float a = clamp((fres * 0.85 + lipBoost * 0.45) * uOpacity, 0.0, 0.95);
        gl_FragColor = vec4(col * a * 1.35, a);
      }
    `,
  });
  const outerRimGeo = new THREE.CylinderGeometry(topRadius * 1.003, baseRadius * 1.003, height, 64, 1, true);
  const fresnelShell = new THREE.Mesh(outerRimGeo, fresnelMat);
  fresnelShell.position.y = height * 0.5;
  fresnelShell.renderOrder = 13;
  group.add(fresnelShell);

  // X-ray structural wireframe edges
  const wireMat = new THREE.LineBasicMaterial({
    color: rimHex,
    transparent: true,
    opacity: 0.0,
    depthWrite: false,
  });
  const wire = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 24), wireMat);
  wire.renderOrder = 15;
  group.add(wire);

  // Ground contact AO under glass
  const ao = createGroundContactAO({ width: 2.3, depth: 2.3, opacity: 0.62, floorY: 0.0 });
  ao.position.y = -yFloor + 0.015;
  ao.renderOrder = 2;
  group.add(ao);

  return {
    group,
    mesh,
    glassMat,
    fresnelShell,
    fresnelMat,
    wire,
    wireMat,
    ao,
    dims: { baseRadius, topRadius, wallThickness, baseThickness, height, yFloor },
  };
}

/**
 * 3. Physical Halogen Heater Ring + Tilting Gooseneck Pitcher + Parabolic Water Stream Plugin.
 * Eliminates "floating sky water" — real props drive the thermal soak & cold quench!
 */
export function createPhysicalHeaterAndPitcherRig({ yHeaterTop = 0.22 } = {}) {
  const root = new THREE.Group();

  // --- A. Ceramic Halogen Induction Heater Unit ---
  const heaterGroup = new THREE.Group();
  root.add(heaterGroup);

  const housingGeo = new THREE.CylinderGeometry(0.92, 1.04, yHeaterTop - 0.01, 56);
  const housingMat = new THREE.MeshStandardMaterial({
    color: '#19202a',
    roughness: 0.34,
    metalness: 0.82,
    envMapIntensity: 1.4,
  });
  const housing = new THREE.Mesh(housingGeo, housingMat);
  housing.position.y = (yHeaterTop - 0.01) * 0.5;
  housing.castShadow = true;
  housing.receiveShadow = true;
  heaterGroup.add(housing);

  // Beveled chrome trim ring
  const trim = new THREE.Mesh(
    new THREE.TorusGeometry(0.91, 0.022, 14, 64),
    new THREE.MeshStandardMaterial({ color: '#7b90a6', roughness: 0.18, metalness: 0.92 })
  );
  trim.rotation.x = Math.PI / 2;
  trim.position.y = yHeaterTop - 0.012;
  heaterGroup.add(trim);

  // Dark translucent glass-ceramic cooktop plate
  const plate = new THREE.Mesh(
    new THREE.CylinderGeometry(0.88, 0.88, 0.014, 56),
    new THREE.MeshPhysicalMaterial({
      color: '#0c1017',
      roughness: 0.08,
      metalness: 0.1,
      clearcoat: 1.0,
      transparent: true,
      opacity: 0.82,
      depthWrite: false,
    })
  );
  plate.position.y = yHeaterTop - 0.004;
  plate.renderOrder = 4;
  heaterGroup.add(plate);

  // 3.5-turn glowing spiral tungsten-halogen coil underneath ceramic top
  const coilPts = [];
  const turns = 3.5;
  for (let i = 0; i <= 96; i++) {
    const u = i / 96;
    const ang = u * Math.PI * 2 * turns;
    const r = 0.14 + u * 0.56;
    coilPts.push(new THREE.Vector3(Math.cos(ang) * r, yHeaterTop - 0.022, Math.sin(ang) * r));
  }
  const coilGeo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(coilPts), 96, 0.020, 8, false);
  const coilMat = new THREE.MeshBasicMaterial({
    color: '#ff5214',
    transparent: true,
    opacity: 0.25,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const coil = new THREE.Mesh(coilGeo, coilMat);
  coil.renderOrder = 5;
  heaterGroup.add(coil);

  // --- B. Sculpted Brushed-Titanium Gooseneck Pitcher (Pivots around spout-aim!) ---
  const pitcherPivot = new THREE.Group();
  // Rest position visible in upper-right frame on wide shots (Frame 0 == Frame 1200 seamless!)
  pitcherPivot.position.set(1.22, 3.35, 0.0);
  root.add(pitcherPivot);

  const metalMat = new THREE.MeshStandardMaterial({
    color: '#283646',
    roughness: 0.22,
    metalness: 0.88,
    envMapIntensity: 1.9,
  });
  const frostBandMat = new THREE.MeshPhysicalMaterial({
    color: '#88ecff',
    emissive: '#197896',
    emissiveIntensity: 0.55,
    roughness: 0.18,
    metalness: 0.2,
  });

  // Pitcher body offset from pivot so it frames cleanly inside 9:16 portrait view!
  const pitcherBodyGrp = new THREE.Group();
  pitcherBodyGrp.position.set(0.24, 0.10, 0);
  pitcherPivot.add(pitcherBodyGrp);

  const pPts = [
    new THREE.Vector2(0.001, -0.45),
    new THREE.Vector2(0.36, -0.45),
    new THREE.Vector2(0.38, -0.38),
    new THREE.Vector2(0.31, 0.36),
    new THREE.Vector2(0.33, 0.42),
    new THREE.Vector2(0.28, 0.42),
    new THREE.Vector2(0.26, -0.36),
    new THREE.Vector2(0.001, -0.36),
  ];
  const pBody = new THREE.Mesh(new THREE.LatheGeometry(pPts, 40), metalMat);
  pBody.castShadow = true;
  pitcherBodyGrp.add(pBody);

  // Frost indicator band ("10°C ICE QUENCH")
  const frostRing = new THREE.Mesh(new THREE.CylinderGeometry(0.355, 0.368, 0.11, 40, 1, true), frostBandMat);
  frostRing.position.y = -0.10;
  pitcherBodyGrp.add(frostRing);

  // Curved gooseneck pouring spout reaching from body (-x) to nozzle at (-0.78, 0.22, 0) in pitcherBodyGrp
  const spoutCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-0.30, -0.22, 0),
    new THREE.Vector3(-0.56, -0.05, 0),
    new THREE.Vector3(-0.72, 0.24, 0),
    new THREE.Vector3(-0.88, 0.26, 0),
  ]);
  const spout = new THREE.Mesh(new THREE.TubeGeometry(spoutCurve, 32, 0.044, 12, false), metalMat);
  spout.castShadow = true;
  pitcherBodyGrp.add(spout);

  // Spout nozzle world-tracking marker
  const spoutTipMarker = new THREE.Object3D();
  spoutTipMarker.position.set(-0.89, 0.25, 0);
  pitcherBodyGrp.add(spoutTipMarker);

  // Handle on +x side
  const handleCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0.31, 0.28, 0),
    new THREE.Vector3(0.58, 0.22, 0),
    new THREE.Vector3(0.56, -0.20, 0),
    new THREE.Vector3(0.35, -0.26, 0),
  ]);
  const handle = new THREE.Mesh(new THREE.TubeGeometry(handleCurve, 24, 0.028, 10, false), metalMat);
  pitcherBodyGrp.add(handle);

  // --- C. Parabolic Laminar Water Stream + Rising Water Volume + Splash Crown ---
  const streamMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    uniforms: {
      uTime: { value: 0.0 },
      uFlow: { value: 0.0 },
    },
    vertexShader: `
      varying vec2 vUv;
      varying vec3 vN;
      varying vec3 vP;
      void main() {
        vUv = uv;
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vP = wp.xyz;
        vN = normalize(mat3(modelMatrix) * normal);
        gl_Position = projectionMatrix * viewMatrix * wp;
      }
    `,
    fragmentShader: `
      uniform float uTime;
      uniform float uFlow;
      varying vec2 vUv;
      varying vec3 vN;
      varying vec3 vP;
      void main() {
        vec3 V = normalize(cameraPosition - vP);
        float fres = pow(1.0 - clamp(abs(dot(vN, V)), 0.0, 1.0), 2.0);
        float scroll = fract(vUv.x * 4.5 - uTime * 3.8);
        float streak = 0.62 + 0.38 * sin(vUv.y * 28.0 + uTime * 26.0 - vUv.x * 16.0);
        float headMask = smoothstep(0.0, 0.06, uFlow - vUv.x * 0.35);
        vec3 core = mix(vec3(0.32, 0.82, 0.98), vec3(0.88, 0.98, 1.0), fres * 0.8 + streak * 0.25);
        float a = clamp(uFlow * headMask * (0.48 + 0.42 * streak * (0.5 + 0.5 * scroll) + 0.28 * fres), 0.0, 0.92);
        gl_FragColor = vec4(core * (1.0 + 0.35 * fres), a);
      }
    `,
  });

  // Pre-built parabolic stream curve from tilted spout nozzle ~(0.34, 3.06, 0) into glass center (0.0, 0.65, 0)
  const paraPts = [];
  for (let i = 0; i <= 28; i++) {
    const s = i / 28;
    const x = 0.33 * (1.0 - s) * (1.0 - 0.55 * s);
    const y = 3.04 - 0.25 * s - 2.15 * s * s;
    paraPts.push(new THREE.Vector3(x, y, 0));
  }
  const streamGeo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(paraPts), 36, 0.042, 12, false);
  const streamMesh = new THREE.Mesh(streamGeo, streamMat);
  streamMesh.visible = false;
  streamMesh.renderOrder = 16;
  root.add(streamMesh);

  // Rising water column inside glass (volume + meniscus top)
  const waterGroup = new THREE.Group();
  waterGroup.position.set(0, yHeaterTop + 0.24, 0);
  waterGroup.visible = false;
  root.add(waterGroup);

  const waterBodyMat = new THREE.MeshPhysicalMaterial({
    color: '#2998c8',
    transparent: true,
    opacity: 0.44,
    roughness: 0.06,
    metalness: 0.05,
    envMapIntensity: 2.0,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const waterCol = new THREE.Mesh(new THREE.CylinderGeometry(0.485, 0.435, 1.0, 48, 1, true), waterBodyMat);
  waterCol.position.y = 0.5;
  waterCol.renderOrder = 11;
  waterGroup.add(waterCol);

  const meniscus = new THREE.Mesh(
    new THREE.CircleGeometry(0.485, 48),
    new THREE.MeshPhysicalMaterial({
      color: '#6ce2ff',
      transparent: true,
      opacity: 0.68,
      roughness: 0.04,
      envMapIntensity: 2.4,
      side: THREE.DoubleSide,
      depthWrite: false,
    })
  );
  meniscus.rotation.x = -Math.PI / 2;
  meniscus.position.y = 1.0;
  meniscus.renderOrder = 13;
  waterGroup.add(meniscus);

  // Splash crown torus
  const splashMat = new THREE.MeshBasicMaterial({
    color: '#b8f4ff',
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const splashCrown = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.032, 10, 44), splashMat);
  splashCrown.rotation.x = Math.PI / 2;
  splashCrown.visible = false;
  splashCrown.renderOrder = 17;
  root.add(splashCrown);

  return {
    root,
    heaterGroup,
    coil,
    coilMat,
    pitcherPivot,
    spoutTipMarker,
    streamMesh,
    streamMat,
    waterGroup,
    waterCol,
    meniscus,
    splashCrown,
    splashMat,
    update({ time, heat, pourEnter, pourFlow, waterFill, isShattered }) {
      // Heater coil molten glow (0..1)
      const hGlow = isShattered ? Math.max(0.08, heat * 0.25) : 0.22 + heat * 0.78;
      coilMat.opacity = GLM.clamp(hGlow, 0, 1);
      coilMat.color.setRGB(1.0, 0.24 + 0.42 * heat, 0.05 + 0.18 * heat);

      // Pitcher smooth entry & tilt (pourEnter = 0 at Frame 0 AND Frame 1200 -> exact loop match!)
      pitcherPivot.position.set(
        GLM.mix(0.76, 0.64, pourEnter),
        GLM.mix(3.18, 2.96, pourEnter),
        0.0
      );
      pitcherPivot.rotation.z = GLM.mix(0.08, 0.44, pourEnter);

      // Parabolic stream
      streamMat.uniforms.uTime.value = time;
      streamMat.uniforms.uFlow.value = pourFlow;
      streamMesh.visible = pourFlow > 0.02 && !isShattered;

      // Rising water volume inside glass
      if (waterFill > 0.01 && !isShattered) {
        waterGroup.visible = true;
        const hW = 0.06 + waterFill * 1.28;
        waterCol.scale.set(1, hW, 1);
        waterCol.position.y = hW * 0.5;
        const rip = 1.0 + 0.035 * Math.sin(time * 14.0) * pourFlow;
        meniscus.position.y = hW;
        meniscus.scale.set(rip, rip, 1);
      } else {
        waterGroup.visible = false;
      }

      // Splash crown at impact surface
      if (pourFlow > 0.15 && !isShattered) {
        const surfY = yHeaterTop + 0.24 + 0.06 + waterFill * 1.28;
        const cyc = (time * 3.6) % 1.0;
        splashCrown.visible = true;
        splashCrown.position.set(0.05, surfY + 0.02, 0);
        splashCrown.scale.setScalar(0.55 + cyc * 1.15);
        splashMat.opacity = 0.72 * (1.0 - cyc) * pourFlow;
      } else {
        splashCrown.visible = false;
      }
    },
  };
}

/**
 * 4. Jagged Bifurcating Internal Cleavage Cracks Plugin (NOT smooth macaroni tubes!).
 * Builds razor-sharp angular lightning fracture trees inside the glass wall.
 */
export function createBranchingCleavageCracks({
  radius = 0.545,
  height = 2.05,
  yFloor = 0.22,
  seed = 4040,
} = {}) {
  const group = new THREE.Group();
  group.position.set(0, yFloor, 0);
  const rng = mulberry32(seed);
  const networks = [];

  const rootAngles = [0.18, -0.72, 1.15, -1.65];

  function buildSharpSegmentRibbon(pts3D, halfWidth = 0.0085) {
    const positions = [];
    const uvs = [];
    const indices = [];
    const n = pts3D.length;
    for (let i = 0; i < n; i++) {
      const p = pts3D[i];
      const u = i / Math.max(1, n - 1);
      // Radial normal so ribbon faces outward + tangential bevel
      const radial = new THREE.Vector3(p.x, 0, p.z).normalize();
      const tang = new THREE.Vector3(-radial.z, 0.25, radial.x).normalize();
      const w = halfWidth * (1.15 - 0.65 * u);
      const pA = p.clone().addScaledVector(tang, -w).addScaledVector(radial, 0.006);
      const pB = p.clone().addScaledVector(tang, +w).addScaledVector(radial, -0.006);
      positions.push(pA.x, pA.y, pA.z, pB.x, pB.y, pB.z);
      uvs.push(u, 0, u, 1);
      if (i < n - 1) {
        const b = i * 2;
        indices.push(b, b + 1, b + 2, b + 1, b + 3, b + 2);
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    geo.setIndex(indices);
    geo.computeVertexNormals();
    return geo;
  }

  for (let ni = 0; ni < rootAngles.length; ni++) {
    const netGrp = new THREE.Group();
    netGrp.visible = false;
    group.add(netGrp);

    const mat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uGrowth: { value: 0.0 },
        uTime: { value: 0.0 },
      },
      vertexShader: `
        varying vec2 vUv;
        void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
      `,
      fragmentShader: `
        uniform float uGrowth;
        uniform float uTime;
        varying vec2 vUv;
        void main() {
          if (vUv.x > uGrowth) discard;
          float tipDist = clamp(uGrowth - vUv.x, 0.0, 1.0);
          float tipFlash = exp(-tipDist * 16.0);
          float core = 1.0 - abs(vUv.y - 0.5) * 1.75;
          vec3 coldEdge = vec3(0.65, 0.96, 1.0);
          vec3 hotCore  = vec3(1.0, 0.82, 0.42);
          vec3 col = mix(hotCore, coldEdge, tipFlash * 0.75 + 0.25);
          float flick = 0.88 + 0.12 * sin(uTime * 55.0 + vUv.x * 25.0);
          float a = clamp(core * 1.35, 0.0, 1.0) * flick;
          gl_FragColor = vec4(col * (1.35 + tipFlash * 1.4) * a, a);
        }
      `,
    });

    // Main jagged trunk (12 sharp zig-zag steps down the glass wall)
    let ang = rootAngles[ni];
    let y = height - 0.06;
    const trunk = [new THREE.Vector3(Math.cos(ang) * radius, y, Math.sin(ang) * radius)];
    for (let s = 1; s <= 12; s++) {
      y -= (height * 0.76) / 12;
      ang += (s % 2 === 0 ? 1 : -1) * (0.06 + rng() * 0.11);
      const rNow = radius * (0.94 + 0.06 * (y / height));
      trunk.push(new THREE.Vector3(Math.cos(ang) * rNow, y, Math.sin(ang) * rNow));
    }
    const trunkMesh = new THREE.Mesh(buildSharpSegmentRibbon(trunk, 0.010), mat);
    trunkMesh.renderOrder = 19;
    netGrp.add(trunkMesh);

    // 4 sharp bifurcating sub-branches per crack
    for (const forkIdx of [3, 5, 7, 9]) {
      const startP = trunk[forkIdx].clone();
      let bAng = Math.atan2(startP.z, startP.x);
      let bY = startP.y;
      const dir = forkIdx % 2 === 0 ? 1 : -1;
      const branchPts = [startP];
      for (let k = 1; k <= 5; k++) {
        bY -= 0.09 + rng() * 0.06;
        bAng += dir * (0.09 + rng() * 0.09);
        const rB = radius * (0.94 + 0.06 * (bY / height));
        branchPts.push(new THREE.Vector3(Math.cos(bAng) * rB, bY, Math.sin(bAng) * rB));
      }
      const bMesh = new THREE.Mesh(buildSharpSegmentRibbon(branchPts, 0.0062), mat);
      bMesh.renderOrder = 19;
      netGrp.add(bMesh);
    }

    networks.push({ group: netGrp, mat });
  }

  return {
    group,
    networks,
    update(time, crackTimes, isShattered) {
      if (isShattered) {
        group.visible = false;
        return;
      }
      group.visible = true;
      for (let i = 0; i < networks.length; i++) {
        const t0 = crackTimes[i] ?? 999;
        if (time < t0) {
          networks[i].group.visible = false;
        } else {
          networks[i].group.visible = true;
          const g = GLM.clamp((time - t0) / 0.34, 0, 1);
          networks[i].mat.uniforms.uGrowth.value = g;
          networks[i].mat.uniforms.uTime.value = time;
        }
      }
    },
  };
}

/**
 * 5. Zack D. Films 3D Atomic Shear & Sagittal Wall Cutaway Plugin (`S4_CUTAWAY` & `S5_ATOMIC`).
 * Shows unmistakable 3D physics:
 *   - Outer 10°C Cyan SiO2 Lattice pulling INWARD (with bold 3D Cyan Compression Arrows)
 *   - Inner 300°C Molten SiO2 Lattice pushing OUTWARD (with bold 3D Orange-Red Tension Arrows)
 *   - Covalent Bond Cylinders stretching white-hot & SNAPPING at critical shear!
 */
export function createZackDAtomicCutawayRig({ yCenter = 1.32 } = {}) {
  const root = new THREE.Group();
  root.position.set(0, yCenter, 0.35);
  root.visible = false;

  // Translucent dark lab cross-section slab backing so atoms pop at 100% contrast
  const slab = new THREE.Mesh(
    new THREE.BoxGeometry(1.62, 1.38, 0.08),
    new THREE.MeshPhysicalMaterial({
      color: '#071019',
      transparent: true,
      opacity: 0.78,
      roughness: 0.25,
      metalness: 0.2,
      depthWrite: false,
    })
  );
  slab.position.set(0, 0, -0.09);
  slab.renderOrder = 14;
  root.add(slab);

  const slabBorder = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(1.64, 1.40, 0.085)),
    new THREE.LineBasicMaterial({ color: '#4ddbf0', transparent: true, opacity: 0.55, depthWrite: false })
  );
  slabBorder.position.copy(slab.position);
  slabBorder.renderOrder = 15;
  root.add(slabBorder);

  // Outer cold zone glow strip (top/left = Outer Wall 10°C) & Inner hot zone glow strip (bottom/right = Inner Wall 300°C)
  const coldZone = new THREE.Mesh(
    new THREE.PlaneGeometry(1.52, 0.54),
    new THREE.MeshBasicMaterial({ color: '#147896', transparent: true, opacity: 0.28, blending: THREE.AdditiveBlending, depthWrite: false })
  );
  coldZone.position.set(0, 0.32, -0.03);
  coldZone.renderOrder = 15;
  root.add(coldZone);

  const hotZone = new THREE.Mesh(
    new THREE.PlaneGeometry(1.52, 0.54),
    new THREE.MeshBasicMaterial({ color: '#a82608', transparent: true, opacity: 0.34, blending: THREE.AdditiveBlending, depthWrite: false })
  );
  hotZone.position.set(0, -0.32, -0.03);
  hotZone.renderOrder = 15;
  root.add(hotZone);

  // Glossy 3D Atoms: 2 rows of Cold Outer Atoms (y > 0) + 2 rows of Hot Inner Atoms (y < 0), 5 cols each
  const atomGeo = new THREE.SphereGeometry(0.068, 24, 18);
  const coldAtomMat = new THREE.MeshPhysicalMaterial({
    color: '#3cf0ff',
    emissive: '#0c6882',
    emissiveIntensity: 0.75,
    roughness: 0.08,
    metalness: 0.15,
    clearcoat: 1.0,
    envMapIntensity: 2.2,
  });
  const hotAtomMat = new THREE.MeshPhysicalMaterial({
    color: '#ff5218',
    emissive: '#d92800',
    emissiveIntensity: 1.15,
    roughness: 0.12,
    metalness: 0.10,
    clearcoat: 1.0,
    envMapIntensity: 2.0,
  });

  const COLS = 5;
  const ROWS = 4; // rows 0,1 = Outer Cold (10°C); rows 2,3 = Inner Hot (300°C)
  const atoms = [];
  for (let r = 0; r < ROWS; r++) {
    const isCold = r < 2;
    const baseY = 0.44 - r * 0.295;
    const rowArr = [];
    for (let c = 0; c < COLS; c++) {
      const baseX = (c - (COLS - 1) * 0.5) * 0.29;
      const m = new THREE.Mesh(atomGeo, isCold ? coldAtomMat : hotAtomMat);
      m.position.set(baseX, baseY, 0.04);
      m.renderOrder = 17;
      root.add(m);
      rowArr.push({ mesh: m, baseX, baseY, isCold, col: c, row: r });
    }
    atoms.push(rowArr);
  }

  // Covalent SiO2 Bond Struts connecting horizontal & vertical neighbors (shear interface = between row 1 & row 2!)
  const bondGeo = new THREE.CylinderGeometry(0.016, 0.016, 1.0, 10);
  const bonds = [];
  const upVec = new THREE.Vector3(0, 1, 0);
  const tmpDir = new THREE.Vector3();

  function addBond(a, b, isShearInterface) {
    const mat = new THREE.MeshBasicMaterial({
      color: isShearInterface ? '#ffd180' : a.isCold ? '#66e8ff' : '#ff7b3d',
      transparent: true,
      opacity: 0.92,
    });
    const mesh = new THREE.Mesh(bondGeo, mat);
    mesh.renderOrder = 16;
    root.add(mesh);
    bonds.push({ mesh, mat, a, b, isShearInterface });
  }

  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      if (c < COLS - 1) addBond(atoms[r][c], atoms[r][c + 1], false);
      if (r < ROWS - 1) addBond(atoms[r][c], atoms[r + 1][c], r === 1);
    }
  }

  // Bold 3D Force Vector Arrows:
  //   Top Cyan Arrows pointing INWARD (>< Contraction!)
  //   Bottom Red-Orange Arrows pointing OUTWARD (<> Thermal Expansion!)
  function make3DArrow(colorHex) {
    const g = new THREE.Group();
    const m = new THREE.MeshStandardMaterial({
      color: colorHex,
      emissive: colorHex,
      emissiveIntensity: 0.85,
      roughness: 0.2,
      metalness: 0.2,
    });
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.24, 14), m);
    shaft.rotation.z = -Math.PI / 2;
    shaft.position.x = -0.12;
    const head = new THREE.Mesh(new THREE.ConeGeometry(0.058, 0.13, 16), m);
    head.rotation.z = -Math.PI / 2;
    head.position.x = 0.04;
    g.add(shaft, head);
    g.renderOrder = 18;
    return g;
  }

  // Top INWARD contraction arrows (left points +X, right points -X)
  const coldArrowL = make3DArrow('#3cf0ff');
  coldArrowL.position.set(-0.62, 0.61, 0.06);
  root.add(coldArrowL);

  const coldArrowR = make3DArrow('#3cf0ff');
  coldArrowR.rotation.z = Math.PI;
  coldArrowR.position.set(0.62, 0.61, 0.06);
  root.add(coldArrowR);

  // Bottom OUTWARD expansion arrows (left points -X, right points +X)
  const hotArrowL = make3DArrow('#ff4a1c');
  hotArrowL.rotation.z = Math.PI;
  hotArrowL.position.set(-0.42, -0.61, 0.06);
  root.add(hotArrowL);

  const hotArrowR = make3DArrow('#ff4a1c');
  hotArrowR.position.set(0.42, -0.61, 0.06);
  root.add(hotArrowR);

  return {
    root,
    update({ visible, reveal, shear, snapProgress, time, calmBoroMode = false }) {
      root.visible = visible;
      if (!visible) return;

      const sc = 0.82 + 0.18 * GLM.easeOutQuint(reveal);
      root.scale.setScalar(sc);

      const effShear = calmBoroMode ? shear * 0.24 : shear;
      // Update atom positions: Cold contracts inward (-32% X), Hot expands outward (+34% X + thermal vibration!)
      for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
          const at = atoms[r][c];
          if (at.isCold) {
            const contract = 1.0 - effShear * (r === 0 ? 0.34 : 0.24);
            const snapLift = !calmBoroMode && snapProgress > 0 ? snapProgress * 0.09 * (r === 0 ? 1.3 : 1.0) : 0;
            at.mesh.position.set(
              at.baseX * contract,
              at.baseY + snapLift,
              0.04
            );
          } else {
            const expand = 1.0 + effShear * (r === 3 ? 0.34 : 0.25);
            const vib = (calmBoroMode ? 0.003 : 0.011 * effShear) * Math.sin(time * 52.0 + c * 2.1 + r);
            const snapDrop = !calmBoroMode && snapProgress > 0 ? -snapProgress * 0.09 : 0;
            at.mesh.position.set(
              at.baseX * expand + vib,
              at.baseY + snapDrop + vib * 0.5,
              0.04
            );
          }
        }
      }

      // Update covalent bonds (interface bonds stretch, glow critical white-red, and SNAP!)
      for (let bi = 0; bi < bonds.length; bi++) {
        const bd = bonds[bi];
        const pA = bd.a.mesh.position;
        const pB = bd.b.mesh.position;
        tmpDir.subVectors(pB, pA);
        const dist = tmpDir.length();

        if (bd.isShearInterface && !calmBoroMode) {
          // Outer-most columns snap first as shear crosses 4x limit!
          const edgeFactor = Math.abs(bd.a.col - 2) / 2.0; // 1.0 at outer cols, 0 at center
          const snapThresh = 0.35 + (1.0 - edgeFactor) * 0.45;
          if (snapProgress > snapThresh) {
            bd.mesh.visible = false;
            continue;
          }
          bd.mesh.visible = true;
          const crit = GLM.clamp(effShear * 1.25, 0, 1);
          const pulse = 0.75 + 0.25 * Math.sin(time * 48.0 + bi);
          bd.mat.color.setRGB(1.0, GLM.mix(0.85, 0.18, crit) * pulse, GLM.mix(0.55, 0.08, crit));
          bd.mesh.scale.set(1.0 - 0.45 * crit, dist, 1.0 - 0.45 * crit);
        } else {
          bd.mesh.visible = true;
          bd.mat.color.set(calmBoroMode ? '#4ef2d2' : bd.a.isCold ? '#66e8ff' : '#ff7b3d');
          bd.mesh.scale.set(1.0, dist, 1.0);
        }

        bd.mesh.position.copy(pA).addScaledVector(tmpDir, 0.5);
        bd.mesh.quaternion.setFromUnitVectors(upVec, tmpDir.normalize());
      }

      // Animate 3D Force Vector Arrows
      const arrowPulse = 0.04 * Math.sin(time * 9.0);
      const arrowScale = calmBoroMode ? 0.55 : 0.85 + 0.35 * effShear;
      coldArrowL.scale.setScalar(arrowScale);
      coldArrowR.scale.setScalar(arrowScale);
      hotArrowL.scale.setScalar(arrowScale);
      hotArrowR.scale.setScalar(arrowScale);
      coldArrowL.position.x = -0.66 + effShear * 0.14 + arrowPulse;
      coldArrowR.position.x = 0.66 - effShear * 0.14 - arrowPulse;
      hotArrowL.position.x = -0.36 - effShear * 0.18 - arrowPulse;
      hotArrowR.position.x = 0.36 + effShear * 0.18 + arrowPulse;
    },
  };
}

/**
 * 6. NaN-Proof 96-Shard Multi-Faceted 3D Voronoi Crystal Shatter Plugin.
 *   - 64 beveled polygonal primary wall/rim shards + 32 glittering prism splinters
 *   - Refractive cyan-white edge wireframes on hero shards + radial blast streaks
 *   - Built-in `assertFiniteShardPositions()` guard (guarantees ZERO NaN vertices!)
 *   - Portrait 9:16 frustum-calibrated ballistics + 2-bounce floor restitution
 */
export function createVoronoiShatterPlugin({
  yOrigin = 0.22,
  glassRadius = 0.55,
  glassHeight = 2.05,
  seed = 90210,
} = {}) {
  const group = new THREE.Group();
  const rng = mulberry32(seed);

  const shardGlassMat = new THREE.MeshStandardMaterial({
    color: '#a6ecfa',
    emissive: '#0c2d40',
    emissiveIntensity: 0.34,
    transparent: true,
    opacity: 0.52,
    roughness: 0.04,
    metalness: 0.12,
    envMapIntensity: 2.25,
    side: THREE.DoubleSide,
    depthWrite: false,
  });

  const shardEdgeMat = new THREE.LineBasicMaterial({
    color: '#d6fcff',
    transparent: true,
    opacity: 0.92,
    blending: THREE.AdditiveBlending,
  });

  const shards = [];
  const TOTAL_SHARDS = 96;

  for (let i = 0; i < TOTAL_SHARDS; i++) {
    const isWave2 = i >= 64;
    // Acute razor-sharp 3-to-5 vertex glass splinter/dagger polygon (never boxy!)
    const sides = i % 2 === 0 ? 3 : (i % 5 === 0 ? 5 : 4);
    const poly = new THREE.Shape();
    const baseSize = isWave2 ? (0.045 + rng() * 0.072) : (0.078 + rng() * 0.145);
    const stretchY = 1.25 + rng() * 0.95;
    for (let v = 0; v < sides; v++) {
      const a = (v / sides) * Math.PI * 2 + (rng() - 0.5) * 0.54;
      const radV = baseSize * (v === 0 ? 1.35 : (0.52 + rng() * 0.54));
      const px = Math.cos(a) * radV * 0.78;
      const py = Math.sin(a) * radV * stretchY;
      if (v === 0) poly.moveTo(px, py);
      else poly.lineTo(px, py);
    }
    poly.closePath();

    const geo = new THREE.ExtrudeGeometry(poly, {
      depth: isWave2 ? 0.014 : (0.022 + rng() * 0.024),
      bevelEnabled: !isWave2,
      bevelThickness: 0.005,
      bevelSize: 0.004,
      bevelSegments: 1,
    });
    geo.computeVertexNormals();

    const mesh = new THREE.Mesh(geo, shardGlassMat);
    mesh.castShadow = !isWave2;
    mesh.visible = false;

    // Crisp cyan-white cleavage edge glint on hero shards
    if (!isWave2) {
      const edgeLines = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 32), shardEdgeMat);
      mesh.add(edgeLines);
    }
    group.add(mesh);

    // Bias angular distribution slightly toward camera (+Z) while still 360° so 9:16 portrait frame is PACKED!
    const rawAng = (i / TOTAL_SHARDS) * Math.PI * 2 + (rng() - 0.5) * 0.35;
    const rSpawn = glassRadius * (0.78 + rng() * 0.28);
    const x0 = Math.cos(rawAng) * rSpawn;
    const z0 = Math.sin(rawAng) * rSpawn; // <-- EXPLICITLY DEFINED & VERIFIED!
    const y0 = yOrigin + 0.28 + rng() * (glassHeight - 0.32);

    // Portrait-calibrated radial velocity (keeps storm dense inside ±1.45 world X while flying toward camera!)
    const speedRadial = isWave2 ? (0.65 + rng() * 1.45) : (0.85 + rng() * 1.85);
    const vx = Math.cos(rawAng) * speedRadial * 0.78;
    const vz = Math.sin(rawAng) * speedRadial + (z0 > 0 ? 0.55 : 0.0);
    const vy = isWave2 ? (1.65 + rng() * 2.75) : (0.95 + rng() * 2.35);

    shards.push({
      mesh,
      isWave2,
      delay: isWave2 ? (0.04 + rng() * 0.14) : 0.0,
      x0,
      y0,
      z0,
      vx,
      vy,
      vz,
      drag: isWave2 ? (0.95 + rng() * 0.75) : (0.62 + rng() * 0.65),
      gravityScale: isWave2 ? 0.68 : 1.0,
      scale: 0.82 + rng() * 0.45,
      rx0: rng() * 6.28,
      ry0: rng() * 6.28,
      rz0: rng() * 6.28,
      ax: (rng() - 0.5) * 14.0,
      ay: (rng() - 0.5) * 14.0,
      az: (rng() - 0.5) * 12.0,
    });
  }

  // 36 High-Velocity Radial Blast Streak Lines (first 0.45s of detonation)
  const streakGroup = new THREE.Group();
  streakGroup.position.set(0, yOrigin + glassHeight * 0.52, 0);
  streakGroup.visible = false;
  group.add(streakGroup);

  const streakMat = new THREE.MeshBasicMaterial({
    color: '#ffe4ad',
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const streakGeo = new THREE.PlaneGeometry(0.018, 0.85);
  const streaks = [];
  const upAxis = new THREE.Vector3(0, 1, 0);
  for (let k = 0; k < 36; k++) {
    const theta = (k / 36) * Math.PI * 2 + rng() * 0.15;
    const phi = (rng() - 0.42) * 1.15;
    const dir = new THREE.Vector3(
      Math.cos(phi) * Math.cos(theta),
      Math.sin(phi),
      Math.cos(phi) * Math.sin(theta)
    ).normalize();
    const m = new THREE.Mesh(streakGeo, streakMat);
    m.quaternion.setFromUnitVectors(upAxis, dir);
    m.renderOrder = 27;
    streakGroup.add(m);
    streaks.push({ mesh: m, dir, speed: 3.2 + rng() * 3.8, r0: 0.35 + rng() * 0.25 });
  }

  // C1-continuous Bullet-Time Curve: ultra-slow 0.22x during first 1.65s explosion, smoothly ramping to 1.0x!
  function mapSimTime(dtReal) {
    if (dtReal <= 0) return 0;
    const slowWindow = 1.65;
    const slowRate = 0.22;
    if (dtReal <= slowWindow) return slowRate * dtReal;
    const rem = dtReal - slowWindow;
    const ramp = GLM.smoothstep(0.0, 2.2, rem);
    return slowRate * slowWindow + rem * (slowRate + (1.0 - slowRate) * ramp);
  }

  function assertFiniteShardPositions() {
    for (let i = 0; i < shards.length; i++) {
      const p = shards[i].mesh.position;
      if (!Number.isFinite(p.x) || !Number.isFinite(p.y) || !Number.isFinite(p.z)) {
        throw new Error(`[VoronoiShatterPlugin] NaN/Infinite position detected on shard #${i}: (${p.x}, ${p.y}, ${p.z})`);
      }
    }
  }

  return {
    group,
    shards,
    update(dtReal, active) {
      if (!active || dtReal <= 0) {
        group.visible = false;
        streakGroup.visible = false;
        return;
      }
      group.visible = true;

      // Radial blast velocity streaks (first 0.48s)
      if (dtReal < 0.48) {
        streakGroup.visible = true;
        const sp = dtReal / 0.48;
        streakMat.opacity = 0.88 * (1.0 - sp) * (1.0 - sp);
        for (const st of streaks) {
          const dist = st.r0 + st.speed * dtReal * 0.65;
          st.mesh.position.copy(st.dir).multiplyScalar(dist);
          st.mesh.scale.set(1.0, 0.45 + sp * 1.35, 1.0);
        }
      } else {
        streakGroup.visible = false;
      }

      const simBase = mapSimTime(dtReal);
      const G = 9.81;
      const floorY = 0.035;

      for (let i = 0; i < shards.length; i++) {
        const s = shards[i];
        const t = simBase - s.delay;
        if (t <= 0.001) {
          s.mesh.visible = false;
          continue;
        }
        s.mesh.visible = true;
        const k = s.drag;
        const expDrag = (1.0 - Math.exp(-k * t)) / k;
        const x = s.x0 + s.vx * expDrag;
        const z = s.z0 + s.vz * expDrag;

        const gEff = G * s.gravityScale;
        let y = s.y0 + s.vy * t - 0.5 * gEff * t * t;
        let spinDamp = 1.0;

        // Analytic 2-bounce floor restitution (e1 = 0.42, e2 = 0.26)
        if (y < floorY) {
          const disc = Math.max(0, s.vy * s.vy + 2.0 * gEff * Math.max(0, s.y0 - floorY));
          const tHit1 = (s.vy + Math.sqrt(disc)) / gEff;
          const tb1 = Math.max(0, t - tHit1);
          const vy1 = Math.sqrt(disc) * 0.42;
          const y1 = floorY + vy1 * tb1 - 0.5 * gEff * tb1 * tb1;
          if (y1 >= floorY) {
            y = y1;
            spinDamp = 0.65;
          } else {
            const tDur1 = (2.0 * vy1) / gEff;
            const tb2 = Math.max(0, tb1 - tDur1);
            const vy2 = vy1 * 0.48;
            const y2 = floorY + vy2 * tb2 - 0.5 * gEff * tb2 * tb2;
            y = Math.max(floorY, y2);
            spinDamp = y2 > floorY + 0.002 ? 0.35 : 0.0;
          }
        }

        s.mesh.position.set(x, y, z);
        if (spinDamp > 0) {
          s.mesh.rotation.set(
            s.rx0 + s.ax * t * (0.5 + 0.5 * spinDamp),
            s.ry0 + s.ay * t * (0.5 + 0.5 * spinDamp),
            s.rz0 + s.az * t * (0.5 + 0.5 * spinDamp)
          );
        }
        s.mesh.scale.setScalar(s.scale);
      }

      assertFiniteShardPositions();
    },
  };
}
