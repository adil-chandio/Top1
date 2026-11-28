import * as THREE from 'three';
import { mulberry32 } from '../core/pbr_shadow_sdk.js';
import { GLM } from '../core/sculpt_ik_rig_sdk.js';

/**
 * MONARCH V6 ULTRA — NEXT-GEN ZACK D. FILMS x CHRISTOPHER NOLAN CINEMA PLUGINS
 * (`thermal_ultra_v6_plugins.js`):
 *   1. `createThermodynamicsLabEnvironment` — Bokeh-depth 3D lab props + stainless vernier hazard bezel
 *   2. `createUltraSliceableCrystalGlass`   — Surgical 144° cross-section cutaway + chromatic Fresnel + floor caustics + 80 condensation beads
 *   3. `createUltraCryoPitcherAndIceRig`    — Titanium cryo-carafe + helical water stream + 7 3D ice cubes + sliceable water column
 *   4. `createUltraTetrahedralAtomicRig`    — True thermal-jitter SiO2 lattice + recoiling snapped bond stubs + Boron 3.3 spring shield
 *   5. `createUltraShatterAndWaterBurst`    — 128 dual-temp specular-glint crystal shards (zero fake wireframes) + bullet-time time-dilation + 140 3D water globules + expanding wet floor puddle
 */

// =============================================================================
// 1. BOKEH-DEPTH 3D THERMODYNAMICS LABORATORY ENVIRONMENT
// =============================================================================
export function createThermodynamicsLabEnvironment({ yFloor = 0.0 } = {}) {
  const group = new THREE.Group();

  // A. Precision Engraved Stainless-Steel Vernier Hazard Bezel around Heater Base
  const bezelCv = document.createElement('canvas');
  bezelCv.width = bezelCv.height = 512;
  const bctx = bezelCv.getContext('2d');
  bctx.clearRect(0, 0, 512, 512);
  const cx = 256, cy = 256;

  // Brushed dark gunmetal ring
  bctx.strokeStyle = 'rgba(130, 195, 220, 0.36)';
  bctx.lineWidth = 3;
  bctx.beginPath();
  bctx.arc(cx, cy, 236, 0, Math.PI * 2);
  bctx.stroke();

  bctx.strokeStyle = 'rgba(255, 130, 52, 0.42)';
  bctx.lineWidth = 2;
  bctx.beginPath();
  bctx.arc(cx, cy, 196, 0, Math.PI * 2);
  bctx.stroke();

  // 72 Vernier degree tick marks
  for (let i = 0; i < 72; i++) {
    const a = (i / 72) * Math.PI * 2;
    const major = i % 6 === 0;
    const r0 = major ? 206 : 216;
    const r1 = 230;
    bctx.strokeStyle = major ? 'rgba(190, 240, 255, 0.65)' : 'rgba(140, 190, 210, 0.28)';
    bctx.lineWidth = major ? 3 : 1.5;
    bctx.beginPath();
    bctx.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0);
    bctx.lineTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1);
    bctx.stroke();
  }

  const bezelTex = new THREE.CanvasTexture(bezelCv);
  bezelTex.colorSpace = THREE.SRGBColorSpace;
  const bezelMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(2.65, 2.65),
    new THREE.MeshBasicMaterial({
      map: bezelTex,
      transparent: true,
      opacity: 0.85,
      depthWrite: false,
      polygonOffset: true,
      polygonOffsetFactor: -2,
      polygonOffsetUnits: -2,
    })
  );
  bezelMesh.rotation.x = -Math.PI / 2;
  bezelMesh.position.y = yFloor + 0.008;
  group.add(bezelMesh);

  // B. Out-of-Focus Left Laboratory Retort Stand & Clamp Silhouette (Bokeh Depth Layer!)
  const standMat = new THREE.MeshStandardMaterial({
    color: '#1b2634',
    metalness: 0.85,
    roughness: 0.28,
  });
  const retortGrp = new THREE.Group();
  retortGrp.position.set(-2.05, yFloor, -4.2);
  const basePlate = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.06, 0.65), standMat);
  basePlate.position.y = 0.03;
  retortGrp.add(basePlate);
  const verticalRod = new THREE.Mesh(new THREE.CylinderGeometry(0.032, 0.032, 4.4, 14), standMat);
  verticalRod.position.y = 2.2;
  retortGrp.add(verticalRod);
  const crossArm = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 1.15, 12), standMat);
  crossArm.rotation.z = Math.PI / 2;
  crossArm.position.set(0.45, 2.85, 0);
  retortGrp.add(crossArm);
  // Subtle LED indicator on stand sensor
  const ledSensor = new THREE.Mesh(
    new THREE.SphereGeometry(0.045, 12, 12),
    new THREE.MeshBasicMaterial({ color: '#3cf0ff' })
  );
  ledSensor.position.set(0.95, 2.85, 0);
  retortGrp.add(ledSensor);
  group.add(retortGrp);

  // C. Out-of-Focus Right FLIR Thermal Telemetry Console Glow (Bokeh Depth Layer!)
  const monCv = document.createElement('canvas');
  monCv.width = 256;
  monCv.height = 160;
  const mctx = monCv.getContext('2d');
  mctx.fillStyle = '#07131e';
  mctx.fillRect(0, 0, 256, 160);
  mctx.strokeStyle = 'rgba(60, 240, 255, 0.35)';
  mctx.lineWidth = 2;
  mctx.strokeRect(8, 8, 240, 144);
  // Sine thermal trace
  mctx.strokeStyle = '#ff6a28';
  mctx.lineWidth = 4;
  mctx.beginPath();
  for (let x = 18; x < 238; x += 4) {
    const y = 85 - Math.sin(x * 0.06) * 32 - (x / 240) * 22;
    if (x === 18) mctx.moveTo(x, y);
    else mctx.lineTo(x, y);
  }
  mctx.stroke();
  mctx.fillStyle = '#3cf0ff';
  mctx.fillRect(24, 24, 70, 10);

  const monTex = new THREE.CanvasTexture(monCv);
  monTex.colorSpace = THREE.SRGBColorSpace;
  const monGrp = new THREE.Group();
  monGrp.position.set(2.15, 2.35, -5.1);
  monGrp.rotation.y = -0.35;
  const monFrame = new THREE.Mesh(new THREE.BoxGeometry(1.45, 0.92, 0.08), standMat);
  monGrp.add(monFrame);
  const monScreen = new THREE.Mesh(
    new THREE.PlaneGeometry(1.34, 0.82),
    new THREE.MeshBasicMaterial({ map: monTex, transparent: true, opacity: 0.72 })
  );
  monScreen.position.z = 0.045;
  monGrp.add(monScreen);
  const monPole = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.05, 2.35, 12), standMat);
  monPole.position.y = -1.2;
  monGrp.add(monPole);
  group.add(monGrp);

  // D. Overhead Softbox Studio Light-Bank Bars (subtle upper background bokeh bars)
  for (const sx of [-1.45, 1.45]) {
    const bar = new THREE.Mesh(
      new THREE.PlaneGeometry(1.35, 0.16),
      new THREE.MeshBasicMaterial({
        color: sx < 0 ? '#9ceeff' : '#ffd9a8',
        transparent: true,
        opacity: 0.26,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      })
    );
    bar.position.set(sx, 4.85, -6.2);
    bar.rotation.x = 0.35;
    group.add(bar);
  }

  return { group, bezelMesh, ledSensor };
}


// =============================================================================
// 2. SURGICAL 144° CROSS-SECTION SLICEABLE OPTICAL CRYSTAL GLASS + CAUSTICS
// =============================================================================
export function createUltraSliceableCrystalGlass({
  baseRadius = 0.50,
  topRadius = 0.585,
  wallThickness = 0.074,
  baseThickness = 0.25,
  height = 2.08,
  tintHex = '#d8f6ff',
  rimHex = '#7cf4ff',
  yFloor = 0.22,
} = {}) {
  const group = new THREE.Group();
  group.position.y = yFloor;

  // A. Custom Apple-Cinema Optical Crystal Shader:
  //    - Dual curved vertical softbox specular highlight ribbons
  //    - Chromatic RGB dispersion Fresnel rim (diamond-like edge fire!)
  //    - Live surgical cross-section clipping (`uSliceY`: clips front 144° wedge above uSliceY!)
  const crystalMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    uniforms: {
      uBaseTint: { value: new THREE.Color(tintHex) },
      uRimTint: { value: new THREE.Color(rimHex) },
      uHeatGlow: { value: 0.38 },
      uColdQuench: { value: 0.0 },
      uSliceY: { value: 9.9 }, // > height = intact; sweeps down 2.15 -> 0.24 during S4_LASER_SLICE!
      uOpacity: { value: 0.42 },
      uTime: { value: 0.0 },
    },
    vertexShader: `
      varying vec3 vWorldPos;
      varying vec3 vLocalPos;
      varying vec3 vWorldNormal;
      varying vec2 vUv;
      void main() {
        vUv = uv;
        vLocalPos = position;
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorldPos = wp.xyz;
        vWorldNormal = normalize(mat3(modelMatrix) * normal);
        gl_Position = projectionMatrix * viewMatrix * wp;
      }
    `,
    fragmentShader: `
      uniform vec3 uBaseTint;
      uniform vec3 uRimTint;
      uniform float uHeatGlow;
      uniform float uColdQuench;
      uniform float uSliceY;
      uniform float uOpacity;
      uniform float uTime;
      varying vec3 vWorldPos;
      varying vec3 vLocalPos;
      varying vec3 vWorldNormal;
      varying vec2 vUv;

      void main() {
        // Surgical 116° front wedge cutaway above uSliceY (keeps wide side crystal walls framing the 3D cutaway!)
        float ang = atan(vLocalPos.x, vLocalPos.z);
        if (vLocalPos.y > uSliceY && vLocalPos.z > 0.02 && abs(ang) < 1.02) {
          discard;
        }

        vec3 V = normalize(cameraPosition - vWorldPos);
        vec3 N = normalize(gl_FrontFacing ? vWorldNormal : -vWorldNormal);
        float ndv = abs(dot(N, V));

        // Chromatic RGB Fresnel dispersion (glass IOR split)
        float fresR = pow(1.0 - ndv, 2.55);
        float fresG = pow(1.0 - ndv, 3.00);
        float fresB = pow(1.0 - ndv, 3.55);
        vec3 dispRim = vec3(fresR * 1.08, fresG * 1.02, fresB * 1.18) * uRimTint;

        // Dual Studio Softbox Vertical Specular Ribbons!
        vec3 R = reflect(-V, N);
        vec3 softboxL = normalize(vec3(-0.68, 0.32, 0.66));
        vec3 softboxR = normalize(vec3( 0.72, 0.28, 0.63));
        vec3 topRimL  = normalize(vec3( 0.0,  0.92, -0.38));

        float specL = pow(max(0.0, dot(R, softboxL)), 72.0) * 1.55;
        float specR = pow(max(0.0, dot(R, softboxR)), 96.0) * 1.25;
        float specTop = pow(max(0.0, dot(R, topRimL)), 36.0) * 0.55;

        // Heavy crystal base internal refraction brightening (bottom 0.26u)
        float baseThickGlow = smoothstep(0.32, 0.02, vLocalPos.y) * 0.45;

        // Thermal bottom-up amber blackbody radiance vs top-down cryo cyan sheen
        float hotGrad = smoothstep(1.65, 0.05, vLocalPos.y) * uHeatGlow;
        vec3 hotCol = vec3(1.0, 0.38, 0.08) * hotGrad * 0.65;
        float coldGrad = smoothstep(0.55, 2.05, vLocalPos.y) * uColdQuench;
        vec3 coldCol = vec3(0.22, 0.90, 1.0) * coldGrad * 0.48;

        // Glowing cyan-white surgical cut edge highlight right along the slice boundary!
        float edgeDistY = abs(vLocalPos.y - uSliceY);
        float edgeDistA = abs(abs(ang) - 1.02);
        float cutGlow = 0.0;
        if (uSliceY < 2.06 && vLocalPos.z > 0.0) {
          float nearHoriz = smoothstep(0.045, 0.0, edgeDistY) * step(abs(ang), 1.04);
          float nearVert  = smoothstep(0.075, 0.0, edgeDistA) * step(uSliceY, vLocalPos.y);
          cutGlow = max(nearHoriz, nearVert);
        }

        vec3 glassCol = uBaseTint * (0.24 + baseThickGlow)
                      + dispRim * 1.28
                      + vec3(1.0, 0.98, 0.95) * (specL + specR + specTop)
                      + hotCol + coldCol
                      + vec3(0.45, 0.98, 1.0) * cutGlow * 1.85;

        float alpha = clamp(
          uOpacity * (0.28 + 0.72 * fresG) + baseThickGlow * 0.42 + (specL + specR) * 0.48 + cutGlow * 0.75,
          0.06, 0.96
        );
        gl_FragColor = vec4(glassCol, alpha);
      }
    `,
  });

  // Lathe Double-Wall Crystal Profile (64 radial segments for silky specular ribbons)
  const pts = [
    new THREE.Vector2(0.0, 0.0),
    new THREE.Vector2(baseRadius * 0.95, 0.0),
    new THREE.Vector2(baseRadius, 0.025),
    new THREE.Vector2(topRadius, height - 0.025),
    new THREE.Vector2(topRadius - wallThickness * 0.25, height),
    new THREE.Vector2(topRadius - wallThickness * 0.78, height),
    new THREE.Vector2(topRadius - wallThickness, height - 0.025),
    new THREE.Vector2(baseRadius - wallThickness, baseThickness + 0.04),
    new THREE.Vector2(baseRadius - wallThickness - 0.04, baseThickness),
    new THREE.Vector2(0.0, baseThickness),
  ];
  const latheGeo = new THREE.LatheGeometry(pts, 72);
  latheGeo.computeVertexNormals();

  const crystalMesh = new THREE.Mesh(latheGeo, crystalMat);
  crystalMesh.castShadow = true;
  crystalMesh.renderOrder = 14;
  group.add(crystalMesh);

  // Heavy Crystal Base Internal TIR Fire Ring
  const tirRingMat = new THREE.MeshBasicMaterial({
    color: '#ff9642',
    transparent: true,
    opacity: 0.52,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const tirRing = new THREE.Mesh(new THREE.TorusGeometry(baseRadius * 0.84, 0.016, 12, 64), tirRingMat);
  tirRing.rotation.x = Math.PI / 2;
  tirRing.position.y = baseThickness * 0.55;
  tirRing.renderOrder = 13;
  group.add(tirRing);

  // Top Lip Precision Specular Torus (clips in cutaway via visibility/shader)
  const lipMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    uniforms: {
      uColor: { value: new THREE.Color(rimHex) },
      uSliceY: { value: 9.9 },
      uOpacity: { value: 0.72 },
    },
    vertexShader: `
      varying vec3 vLocal;
      void main() {
        vLocal = position;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform vec3 uColor;
      uniform float uSliceY;
      uniform float uOpacity;
      varying vec3 vLocal;
      void main() {
        // Torus is rotated PI/2 in X, so world Z corresponds to vLocal.y!
        float ang = atan(vLocal.x, vLocal.y);
        if (uSliceY < 2.02 && vLocal.y > 0.0 && abs(ang) < 1.02) discard;
        gl_FragColor = vec4(uColor * 1.35, uOpacity);
      }
    `,
  });
  const lipTorus = new THREE.Mesh(
    new THREE.TorusGeometry(topRadius - wallThickness * 0.5, wallThickness * 0.42, 14, 72),
    lipMat
  );
  lipTorus.rotation.x = Math.PI / 2;
  lipTorus.position.y = height - 0.012;
  lipTorus.renderOrder = 16;
  group.add(lipTorus);

  // B. PHYSICAL 3D EXPOSED CROSS-SECTION WALL STRIPS (`leftCutWall` & `rightCutWall` at ±1.02 rad!)
  // Shows the EXACT live thermal battle across the glass wall thickness:
  // Outer edge = 10°C Electric Cyan | Center = White Shear Line | Inner edge = 300°C Magma Orange!
  const cutWallMat = new THREE.ShaderMaterial({
    transparent: true,
    side: THREE.DoubleSide,
    uniforms: {
      uColdAmt: { value: 1.0 },
      uHotAmt: { value: 1.0 },
      uShearPulse: { value: 0.0 },
      uSliceY: { value: 9.9 },
      uTime: { value: 0.0 },
    },
    vertexShader: `
      varying vec2 vUv;
      varying float vHeightY;
      void main() {
        vUv = uv;
        vHeightY = (modelMatrix * vec4(position, 1.0)).y - ${yFloor.toFixed(3)};
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uColdAmt;
      uniform float uHotAmt;
      uniform float uShearPulse;
      uniform float uSliceY;
      uniform float uTime;
      varying vec2 vUv;
      varying float vHeightY;
      void main() {
        if (vHeightY < uSliceY) discard;
        // vUv.x: 0.0 = inner 300°C wall, 1.0 = outer 10°C wall!
        vec3 hotCol = vec3(1.0, 0.32, 0.06) * (0.9 + 0.2 * sin(uTime * 10.0 + vUv.y * 12.0));
        vec3 coldCol = vec3(0.14, 0.92, 1.0);
        float shearZone = exp(-pow((vUv.x - 0.54) / 0.13, 2.0));
        vec3 col = mix(hotCol * uHotAmt, coldCol * uColdAmt, smoothstep(0.22, 0.82, vUv.x));
        col += vec3(1.0, 0.96, 0.88) * shearZone * (0.45 + 0.55 * uShearPulse);
        gl_FragColor = vec4(col * 1.25, 0.95);
      }
    `,
  });

  const wallH = height - baseThickness;
  const cutWallGeo = new THREE.PlaneGeometry(wallThickness * 1.35, wallH, 4, 24);
  const leftCutWall = new THREE.Mesh(cutWallGeo, cutWallMat);
  const rightCutWall = new THREE.Mesh(cutWallGeo, cutWallMat);

  const sliceAng = 1.02;
  const midR = (baseRadius + topRadius) * 0.5 - wallThickness * 0.5;
  leftCutWall.position.set(-Math.sin(sliceAng) * midR, baseThickness + wallH * 0.5, Math.cos(sliceAng) * midR);
  leftCutWall.rotation.y = -sliceAng + Math.PI * 0.5;
  rightCutWall.position.set(Math.sin(sliceAng) * midR, baseThickness + wallH * 0.5, Math.cos(sliceAng) * midR);
  rightCutWall.rotation.y = sliceAng - Math.PI * 0.5;

  leftCutWall.visible = false;
  rightCutWall.visible = false;
  leftCutWall.renderOrder = 17;
  rightCutWall.renderOrder = 17;
  group.add(leftCutWall, rightCutWall);

  // C. Projected Refractive Caustic Ring on Heater/Table Surface
  const caustCv = document.createElement('canvas');
  caustCv.width = caustCv.height = 256;
  const cctx = caustCv.getContext('2d');
  const cg = cctx.createRadialGradient(128, 128, 36, 128, 128, 124);
  cg.addColorStop(0.0, 'rgba(255, 160, 70, 0.0)');
  cg.addColorStop(0.52, 'rgba(255, 195, 110, 0.55)');
  cg.addColorStop(0.72, 'rgba(90, 240, 255, 0.65)');
  cg.addColorStop(1.0, 'rgba(0, 0, 0, 0.0)');
  cctx.fillStyle = cg;
  cctx.fillRect(0, 0, 256, 256);
  const caustTex = new THREE.CanvasTexture(caustCv);
  caustTex.colorSpace = THREE.SRGBColorSpace;

  const causticMat = new THREE.MeshBasicMaterial({
    map: caustTex,
    transparent: true,
    opacity: 0.48,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const causticMesh = new THREE.Mesh(new THREE.PlaneGeometry(1.55, 1.55), causticMat);
  causticMesh.rotation.x = -Math.PI / 2;
  causticMesh.position.y = 0.012;
  causticMesh.renderOrder = 9;
  group.add(causticMesh);

  // D. 80 Micro-Condensation Water Droplets on Cold Outer Crystal Shell (`InstancedMesh`)
  const rng = mulberry32(7711);
  const dropGeo = new THREE.SphereGeometry(0.014, 8, 8);
  const dropMat = new THREE.MeshStandardMaterial({
    color: '#aef6ff',
    emissive: '#104458',
    emissiveIntensity: 0.35,
    roughness: 0.04,
    metalness: 0.12,
    transparent: true,
    opacity: 0.0,
    depthWrite: false,
  });
  const COND_COUNT = 80;
  const condDrops = new THREE.InstancedMesh(dropGeo, dropMat, COND_COUNT);
  condDrops.visible = false;
  condDrops.renderOrder = 16;
  const condMeta = [];
  const dummy = new THREE.Object3D();
  for (let i = 0; i < COND_COUNT; i++) {
    const vy = baseThickness + 0.35 + rng() * (height - baseThickness - 0.45);
    const tH = vy / height;
    const radAtY = GLM.mix(baseRadius, topRadius, tH) + 0.004;
    const ang = (rng() - 0.5) * Math.PI * 1.85;
    const sc = 0.65 + rng() * 0.95;
    condMeta.push({ vy, radAtY, ang, sc });
    dummy.position.set(Math.sin(ang) * radAtY, vy, Math.cos(ang) * radAtY);
    dummy.scale.set(sc, sc * 1.25, sc * 0.55);
    dummy.lookAt(0, vy, 0);
    dummy.updateMatrix();
    condDrops.setMatrixAt(i, dummy.matrix);
  }
  condDrops.instanceMatrix.needsUpdate = true;
  group.add(condDrops);

  return {
    group,
    crystalMesh,
    crystalMat,
    tirRing,
    tirRingMat,
    lipTorus,
    lipMat,
    leftCutWall,
    rightCutWall,
    cutWallMat,
    causticMesh,
    causticMat,
    condDrops,
    condMeta,
    dropMat,
    update({ heat = 0.38, coldQuench = 0.0, sliceProgress = 0.0, shearPulse = 0.0, time = 0.0, opacity = 0.42 }) {
      const sliceY = sliceProgress <= 0.001
        ? 9.9
        : GLM.mix(height + 0.06, baseThickness + 0.02, GLM.clamp(sliceProgress, 0, 1));

      crystalMat.uniforms.uHeatGlow.value = heat;
      crystalMat.uniforms.uColdQuench.value = coldQuench;
      crystalMat.uniforms.uSliceY.value = sliceY;
      crystalMat.uniforms.uOpacity.value = opacity;
      crystalMat.uniforms.uTime.value = time;
      lipMat.uniforms.uSliceY.value = sliceY;

      const showCut = sliceProgress > 0.04;
      leftCutWall.visible = showCut;
      rightCutWall.visible = showCut;
      if (showCut) {
        cutWallMat.uniforms.uSliceY.value = sliceY;
        cutWallMat.uniforms.uColdAmt.value = Math.max(0.45, coldQuench);
        cutWallMat.uniforms.uHotAmt.value = Math.max(0.55, heat);
        cutWallMat.uniforms.uShearPulse.value = shearPulse;
        cutWallMat.uniforms.uTime.value = time;
      }

      tirRingMat.color.setRGB(
        GLM.mix(0.35, 1.0, heat),
        GLM.mix(0.85, 0.42, heat),
        GLM.mix(1.0, 0.12, heat)
      );
      tirRingMat.opacity = 0.36 + 0.32 * heat;

      causticMesh.rotation.z = time * 0.22;
      causticMat.opacity = 0.34 + 0.26 * coldQuench + 0.08 * Math.sin(time * 6.0);

      // Condensation beads appear on intact side walls during cold quench (hidden on sliced front wedge!)
      if (coldQuench > 0.08 && sliceProgress < 0.85) {
        condDrops.visible = true;
        dropMat.opacity = GLM.clamp(coldQuench * 0.78 * (1.0 - sliceProgress * 0.8), 0, 0.75);
      } else {
        condDrops.visible = false;
      }
    },
  };
}


// =============================================================================
// 3. TITANIUM CRYO-PITCHER + HELICAL STREAM + 3D ICE CUBES + SLICEABLE WATER
// =============================================================================
export function createUltraCryoPitcherAndIceRig({ yHeaterTop = 0.22 } = {}) {
  const root = new THREE.Group();
  const rng = mulberry32(31415);

  // --- A. Halogen Induction Heater Base with Glowing Spiral Nichrome Element ---
  const heaterGrp = new THREE.Group();
  root.add(heaterGrp);

  const chassisMat = new THREE.MeshStandardMaterial({
    color: '#121822',
    metalness: 0.88,
    roughness: 0.20,
    envMapIntensity: 1.8,
  });
  const baseBody = new THREE.Mesh(new THREE.CylinderGeometry(0.94, 1.06, yHeaterTop, 64), chassisMat);
  baseBody.position.y = yHeaterTop * 0.5;
  baseBody.castShadow = true;
  baseBody.receiveShadow = true;
  heaterGrp.add(baseBody);

  const chromeBezel = new THREE.Mesh(
    new THREE.TorusGeometry(0.945, 0.018, 12, 64),
    new THREE.MeshStandardMaterial({ color: '#9ad8ec', metalness: 0.95, roughness: 0.12 })
  );
  chromeBezel.rotation.x = Math.PI / 2;
  chromeBezel.position.y = yHeaterTop - 0.008;
  heaterGrp.add(chromeBezel);

  const ceramicPlate = new THREE.Mesh(
    new THREE.CylinderGeometry(0.88, 0.88, 0.012, 64),
    new THREE.MeshStandardMaterial({ color: '#070a10', metalness: 0.25, roughness: 0.08 })
  );
  ceramicPlate.position.y = yHeaterTop + 0.002;
  heaterGrp.add(ceramicPlate);

  // 4-Turn Blazing Nichrome Spiral Coil + Infrared Halo
  const spiralPts = [];
  const N_SP = 150;
  for (let i = 0; i <= N_SP; i++) {
    const u = i / N_SP;
    const r = 0.12 + u * 0.56;
    const a = u * Math.PI * 2.0 * 4.2;
    spiralPts.push(new THREE.Vector3(Math.cos(a) * r, yHeaterTop + 0.008, Math.sin(a) * r));
  }
  const coilGeo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(spiralPts), 160, 0.020, 8, false);
  const coilMat = new THREE.MeshBasicMaterial({ color: '#ff4e12' });
  const coilMesh = new THREE.Mesh(coilGeo, coilMat);
  heaterGrp.add(coilMesh);

  // --- B. Sculpted Titanium Cryo-Carafe with Frosty Sight-Glass Window ---
  const pitcherPivot = new THREE.Group();
  pitcherPivot.position.set(0.76, 3.18, 0.0);
  root.add(pitcherPivot);

  const pitcherBodyGrp = new THREE.Group();
  pitcherBodyGrp.position.set(0.24, 0.10, 0);
  pitcherPivot.add(pitcherBodyGrp);

  const titaniumMat = new THREE.MeshStandardMaterial({
    color: '#1a2432',
    metalness: 0.90,
    roughness: 0.18,
    envMapIntensity: 2.2,
  });
  const vessel = new THREE.Mesh(new THREE.CylinderGeometry(0.30, 0.36, 0.94, 40), titaniumMat);
  pitcherBodyGrp.add(vessel);

  // Frosty ice-cyan cooling band + vertical illuminated 10°C sight-glass strip
  const cryoBand = new THREE.Mesh(
    new THREE.CylinderGeometry(0.328, 0.338, 0.14, 40),
    new THREE.MeshBasicMaterial({ color: '#42f2ff' })
  );
  cryoBand.position.y = 0.12;
  pitcherBodyGrp.add(cryoBand);

  const sightGlass = new THREE.Mesh(
    new THREE.BoxGeometry(0.06, 0.52, 0.69),
    new THREE.MeshBasicMaterial({ color: '#56f4ff', transparent: true, opacity: 0.85 })
  );
  sightGlass.position.y = -0.05;
  pitcherBodyGrp.add(sightGlass);

  // Precision Gooseneck Pour Spout
  const spoutCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-0.24, -0.22, 0),
    new THREE.Vector3(-0.48, -0.02, 0),
    new THREE.Vector3(-0.62, 0.24, 0),
    new THREE.Vector3(-0.76, 0.30, 0),
  ]);
  const spoutMesh = new THREE.Mesh(new THREE.TubeGeometry(spoutCurve, 32, 0.044, 14, false), titaniumMat);
  pitcherBodyGrp.add(spoutMesh);

  // Spout Frost Tip Ring
  const spoutFrost = new THREE.Mesh(
    new THREE.TorusGeometry(0.046, 0.009, 10, 24),
    new THREE.MeshBasicMaterial({ color: '#aefaff' })
  );
  spoutFrost.position.set(-0.76, 0.30, 0);
  spoutFrost.rotation.y = Math.PI / 2;
  pitcherBodyGrp.add(spoutFrost);

  // Ergonomic Handle
  const handleCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0.30, 0.28, 0),
    new THREE.Vector3(0.54, 0.20, 0),
    new THREE.Vector3(0.52, -0.22, 0),
    new THREE.Vector3(0.33, -0.30, 0),
  ]);
  pitcherBodyGrp.add(new THREE.Mesh(new THREE.TubeGeometry(handleCurve, 24, 0.028, 10, false), titaniumMat));

  // --- C. Turbulent Helical Refracting Water Stream Shader ---
  const streamMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    uniforms: {
      uTime: { value: 0.0 },
      uFlow: { value: 0.0 },
    },
    vertexShader: `
      varying vec2 vUv;
      varying vec3 vNormal;
      void main() {
        vUv = uv;
        vNormal = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uTime;
      uniform float uFlow;
      varying vec2 vUv;
      varying vec3 vNormal;
      void main() {
        float streak1 = 0.5 + 0.5 * sin(vUv.x * 34.0 - uTime * 32.0 + vUv.y * 12.0);
        float streak2 = 0.5 + 0.5 * cos(vUv.x * 20.0 - uTime * 22.0 - vUv.y * 18.0);
        float foam = pow(streak1 * streak2, 1.5);
        vec3 baseWater = vec3(0.22, 0.88, 1.0);
        vec3 specWhite = vec3(0.95, 1.0, 1.0) * foam * 1.15;
        float rim = pow(1.0 - abs(vNormal.z), 1.6);
        float a = uFlow * (0.46 + 0.42 * foam + 0.25 * rim);
        gl_FragColor = vec4(baseWater + specWhite, clamp(a, 0.0, 0.92));
      }
    `,
  });
  let streamGeo = new THREE.BufferGeometry();
  const streamMesh = new THREE.Mesh(streamGeo, streamMat);
  streamMesh.visible = false;
  streamMesh.renderOrder = 18;
  root.add(streamMesh);

  // --- D. Sliceable Internal Water Column + Rippling Meniscus + Splash Crown ---
  const waterColMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    uniforms: {
      uSliceY: { value: 9.9 },
      uTime: { value: 0.0 },
      uOpacity: { value: 0.48 },
    },
    vertexShader: `
      varying vec3 vLocal;
      varying vec2 vUv;
      void main() {
        vLocal = position;
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uSliceY;
      uniform float uTime;
      uniform float uOpacity;
      varying vec3 vLocal;
      varying vec2 vUv;
      void main() {
        float ang = atan(vLocal.x, vLocal.z);
        // Slice front wedge of water column in sync with crystal glass so 3D SiO2 cutaway is 100% unobstructed!
        if (uSliceY < 2.05 && vLocal.z > 0.0 && abs(ang) < 1.04) {
          discard;
        }
        float caust = 0.5 + 0.5 * sin(vUv.x * 24.0 + uTime * 5.0) * cos(vUv.y * 16.0 - uTime * 4.0);
        vec3 deep = vec3(0.08, 0.58, 0.82);
        vec3 bright = vec3(0.32, 0.95, 1.0);
        vec3 col = mix(deep, bright, 0.35 + 0.45 * caust + 0.25 * vUv.y);
        gl_FragColor = vec4(col, uOpacity);
      }
    `,
  });
  const waterCyl = new THREE.Mesh(new THREE.CylinderGeometry(0.495, 0.425, 1.0, 56, 1, false), waterColMat);
  waterCyl.visible = false;
  waterCyl.renderOrder = 12;
  root.add(waterCyl);

  const meniscusMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    uniforms: {
      uTime: { value: 0.0 },
      uSliceY: { value: 9.9 },
      uSplash: { value: 0.0 },
    },
    vertexShader: `
      varying vec3 vLocal;
      varying vec2 vUv;
      void main() {
        vLocal = position;
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uTime;
      uniform float uSliceY;
      uniform float uSplash;
      varying vec3 vLocal;
      varying vec2 vUv;
      void main() {
        // CircleGeometry rotated -PI/2 around X -> world Z is -vLocal.y
        float wz = -vLocal.y;
        float ang = atan(vLocal.x, wz);
        if (uSliceY < 2.05 && wz > 0.0 && abs(ang) < 1.04) discard;
        float r = length(vUv - 0.5) * 2.0;
        float rings = 0.5 + 0.5 * sin(r * 26.0 - uTime * 16.0);
        vec3 col = mix(vec3(0.35, 0.94, 1.0), vec3(1.0, 1.0, 1.0), rings * (0.4 + 0.45 * uSplash));
        float a = (0.52 + 0.34 * rings) * smoothstep(1.02, 0.85, r);
        gl_FragColor = vec4(col, a);
      }
    `,
  });
  const meniscusDisc = new THREE.Mesh(new THREE.CircleGeometry(0.485, 56), meniscusMat);
  meniscusDisc.rotation.x = -Math.PI / 2;
  meniscusDisc.visible = false;
  meniscusDisc.renderOrder = 15;
  root.add(meniscusDisc);

  // --- E. 7 Floating/Tumbling 3D Translucent Beveled Ice Cubes! ---
  const iceShape = new THREE.Shape();
  const isz = 0.058;
  iceShape.moveTo(-isz, -isz);
  iceShape.lineTo(isz, -isz);
  iceShape.lineTo(isz, isz);
  iceShape.lineTo(-isz, isz);
  iceShape.closePath();
  const iceGeo = new THREE.ExtrudeGeometry(iceShape, {
    depth: 0.085,
    bevelEnabled: true,
    bevelThickness: 0.018,
    bevelSize: 0.016,
    bevelSegments: 2,
  });
  iceGeo.center();
  const iceMat = new THREE.MeshStandardMaterial({
    color: '#dffbff',
    emissive: '#1c6d8c',
    emissiveIntensity: 0.38,
    roughness: 0.06,
    metalness: 0.10,
    transparent: true,
    opacity: 0.78,
    envMapIntensity: 2.2,
  });
  const iceCubes = [];
  for (let i = 0; i < 7; i++) {
    const m = new THREE.Mesh(iceGeo, iceMat);
    m.visible = false;
    m.renderOrder = 15;
    root.add(m);
    const a = (i / 7) * Math.PI * 2 + 0.4;
    const rad = 0.14 + (i % 3) * 0.10;
    iceCubes.push({
      mesh: m,
      ang: a,
      rad,
      dropT0: 0.08 + i * 0.11,
      bobPhase: rng() * 6.28,
      rotSpd: [1.4 + rng(), 1.8 + rng(), 1.2 + rng()],
    });
  }

  return {
    root,
    heaterGrp,
    coilMat,
    pitcherPivot,
    streamMesh,
    waterCyl,
    meniscusDisc,
    iceCubes,
    update({
      time = 0.0,
      heat = 0.38,
      pourEnter = 0.0,
      pourFlow = 0.0,
      waterFill = 0.0,
      sliceProgress = 0.0,
      isShattered = false,
    }) {
      // 1. Heater spiral coil blackbody glow
      const pulse = 0.88 + 0.12 * Math.sin(time * 7.5);
      const h = GLM.clamp(heat, 0, 1) * pulse;
      coilMat.color.setRGB(
        GLM.mix(0.24, 1.0, h),
        GLM.mix(0.06, 0.38, Math.pow(h, 1.3)),
        GLM.mix(0.02, 0.08, Math.pow(h, 2.0))
      );

      // 2. Pitcher smooth tilt inside 9:16 portrait frame (rest pose matches Frame 0 == Frame 1200 -> exact loop!)
      pitcherPivot.position.set(
        GLM.mix(0.62, 0.50, pourEnter),
        GLM.mix(2.96, 2.74, pourEnter),
        0.0
      );
      pitcherPivot.rotation.z = GLM.mix(0.10, 0.48, pourEnter);

      const sliceY = sliceProgress <= 0.001 ? 9.9 : GLM.mix(2.14, 0.26, GLM.clamp(sliceProgress, 0, 1));

      // 3. Water fill & floating 3D ice cubes
      const maxFillH = 1.34;
      const curH = GLM.clamp(waterFill, 0, 1) * maxFillH;
      const surfaceY = yHeaterTop + 0.25 + curH;

      if (!isShattered && curH > 0.02) {
        waterCyl.visible = true;
        waterCyl.scale.set(1, curH, 1);
        waterCyl.position.set(0, yHeaterTop + 0.25 + curH * 0.5, 0);
        waterColMat.uniforms.uSliceY.value = sliceY;
        waterColMat.uniforms.uTime.value = time;
        waterColMat.uniforms.uOpacity.value = sliceProgress > 0.05 ? 0.36 : 0.48;

        meniscusDisc.visible = sliceProgress < 0.85;
        meniscusDisc.position.set(0, surfaceY, 0);
        const rScale = GLM.mix(0.86, 1.03, waterFill);
        meniscusDisc.scale.set(rScale, rScale, 1);
        meniscusMat.uniforms.uTime.value = time;
        meniscusMat.uniforms.uSliceY.value = sliceY;
        meniscusMat.uniforms.uSplash.value = pourFlow;

        // Animate 3D Ice Cubes dropping from stream & bobbing on meniscus!
        for (let i = 0; i < iceCubes.length; i++) {
          const ic = iceCubes[i];
          if (waterFill < ic.dropT0 || sliceProgress > 0.35) {
            ic.mesh.visible = false;
            continue;
          }
          ic.mesh.visible = true;
          const dropProg = GLM.clamp((waterFill - ic.dropT0) / 0.14, 0, 1);
          const bob = Math.sin(time * 5.2 + ic.bobPhase) * 0.025 * (1.0 + pourFlow * 0.8);
          const swirlA = ic.ang + time * 0.65;
          const ix = Math.sin(swirlA) * ic.rad * dropProg;
          const iz = Math.cos(swirlA) * ic.rad * dropProg;
          const iy = GLM.mix(yHeaterTop + 2.35, surfaceY - 0.03 + bob, GLM.easeOutCubic ? dropProg : (1 - Math.pow(1 - dropProg, 3)));
          ic.mesh.position.set(ix, iy, iz);
          ic.mesh.rotation.set(time * ic.rotSpd[0] * 0.35, time * ic.rotSpd[1] * 0.35, time * ic.rotSpd[2] * 0.25);
        }
      } else {
        waterCyl.visible = false;
        meniscusDisc.visible = false;
        for (const ic of iceCubes) ic.mesh.visible = false;
      }

      // 4. Parabolic Helical Pour Stream
      if (!isShattered && pourFlow > 0.02) {
        streamMesh.visible = true;
        pitcherPivot.updateMatrixWorld(true);
        const spoutWorld = new THREE.Vector3(-0.76, 0.30, 0).applyMatrix4(pitcherBodyGrp.matrixWorld);
        const targetY = Math.max(yHeaterTop + 0.28, surfaceY);
        const streamPts = [];
        for (let k = 0; k <= 20; k++) {
          const s = k / 20;
          const px = GLM.mix(spoutWorld.x, 0.03, Math.pow(s, 0.82)) + Math.sin(s * 12.0 - time * 18.0) * 0.008 * s;
          const py = GLM.mix(spoutWorld.y, targetY, s * s);
          const pz = Math.cos(s * 10.0 - time * 16.0) * 0.008 * s;
          streamPts.push(new THREE.Vector3(px, py, pz));
        }
        streamGeo.dispose();
        streamGeo = new THREE.TubeGeometry(
          new THREE.CatmullRomCurve3(streamPts),
          26,
          0.036 * (0.45 + 0.55 * pourFlow),
          12,
          false
        );
        streamMesh.geometry = streamGeo;
        streamMat.uniforms.uTime.value = time;
        streamMat.uniforms.uFlow.value = pourFlow;
      } else {
        streamMesh.visible = false;
      }
    },
  };
}


// =============================================================================
// 4. ZACK D. TETRAHEDRAL SiO2 ATOMIC SHEAR + RECOILING SNAPPED BONDS + BORON SHIELD
// =============================================================================
export function createUltraTetrahedralAtomicRig({ yCenter = 1.28 } = {}) {
  const root = new THREE.Group();
  root.position.set(0, yCenter, 0.18);
  root.visible = false;

  // Soft feathered radial dark halo (NOT a boxy black slab — keeps sliced crystal glass framing visible!)
  const haloCv = document.createElement('canvas');
  haloCv.width = haloCv.height = 256;
  const hctx = haloCv.getContext('2d');
  const hg = hctx.createRadialGradient(128, 128, 28, 128, 128, 126);
  hg.addColorStop(0.0, 'rgba(4, 9, 16, 0.88)');
  hg.addColorStop(0.68, 'rgba(5, 11, 20, 0.72)');
  hg.addColorStop(1.0, 'rgba(5, 11, 20, 0.0)');
  hctx.fillStyle = hg;
  hctx.fillRect(0, 0, 256, 256);
  const haloTex = new THREE.CanvasTexture(haloCv);
  const haloPlane = new THREE.Mesh(
    new THREE.PlaneGeometry(1.75, 1.55),
    new THREE.MeshBasicMaterial({ map: haloTex, transparent: true, depthWrite: false })
  );
  haloPlane.position.z = -0.06;
  haloPlane.renderOrder = 20;
  root.add(haloPlane);

  const atomGeo = new THREE.SphereGeometry(0.056, 20, 16);
  const oxyGeo = new THREE.SphereGeometry(0.032, 12, 10);

  const coldAtomMat = new THREE.MeshStandardMaterial({
    color: '#2ef2ff',
    emissive: '#0c7a96',
    emissiveIntensity: 0.72,
    roughness: 0.14,
    metalness: 0.15,
  });
  const hotAtomMat = new THREE.MeshStandardMaterial({
    color: '#ff4e18',
    emissive: '#a82204',
    emissiveIntensity: 0.82,
    roughness: 0.16,
    metalness: 0.12,
  });
  const boroAtomMat = new THREE.MeshStandardMaterial({
    color: '#3cf5c8',
    emissive: '#0e785e',
    emissiveIntensity: 0.78,
    roughness: 0.14,
    metalness: 0.18,
  });
  const oxyMat = new THREE.MeshBasicMaterial({ color: '#eefaff' });

  // 5 columns x 4 rows + bridging Oxygen midpoints -> authentic SiO2 network framed cleanly inside sliced crystal glass!
  const COLS = 5;
  const ROWS = 4;
  const xStep = 0.195;
  const yStep = 0.235;
  const nodes = [];

  for (let r = 0; r < ROWS; r++) {
    const isCold = r >= 2;
    for (let c = 0; c < COLS; c++) {
      const bx = (c - (COLS - 1) / 2) * xStep + (r % 2 === 0 ? -0.025 : 0.025);
      const by = (r - (ROWS - 1) / 2) * yStep;
      const bz = ((c + r) % 2 === 0 ? 0.022 : -0.022);
      const mesh = new THREE.Mesh(atomGeo, isCold ? coldAtomMat : hotAtomMat);
      mesh.position.set(bx, by, bz);
      mesh.renderOrder = 22;
      root.add(mesh);
      nodes.push({ r, c, isCold, bx, by, bz, mesh, phase: c * 1.7 + r * 2.3 });
    }
  }

  function getNode(r, c) {
    return nodes[r * COLS + c];
  }

  // Covalent Bonds — shear-boundary bonds split into TWO stub halves + soft electric plasma flare sprite!
  const stubGeo = new THREE.CylinderGeometry(0.015, 0.015, 1.0, 8);
  const bonds = [];

  const sparkCv = document.createElement('canvas');
  sparkCv.width = sparkCv.height = 128;
  const sCtx = sparkCv.getContext('2d');
  const sg = sCtx.createRadialGradient(64, 64, 2, 64, 64, 62);
  sg.addColorStop(0.0, 'rgba(255, 255, 255, 1.0)');
  sg.addColorStop(0.18, 'rgba(155, 248, 255, 0.92)');
  sg.addColorStop(0.48, 'rgba(255, 130, 48, 0.42)');
  sg.addColorStop(1.0, 'rgba(0, 0, 0, 0.0)');
  sCtx.fillStyle = sg;
  sCtx.fillRect(0, 0, 128, 128);
  const sparkTex = new THREE.CanvasTexture(sparkCv);
  sparkTex.colorSpace = THREE.SRGBColorSpace;

  function addBond(nA, nB, isShear, diagIdx = 0) {
    const mat = new THREE.MeshBasicMaterial({
      color: isShear ? '#ffe49e' : (nA.isCold ? '#66f0ff' : '#ff7b3d'),
    });
    if (!isShear) {
      const mesh = new THREE.Mesh(stubGeo, mat);
      mesh.renderOrder = 21;
      root.add(mesh);
      const oxy = new THREE.Mesh(oxyGeo, oxyMat);
      oxy.renderOrder = 22;
      root.add(oxy);
      bonds.push({ a: nA, b: nB, isShear: false, mesh, oxy, mat });
    } else {
      // Two half-bond stubs + soft radial electric plasma flare sprite at midpoint!
      const stubA = new THREE.Mesh(stubGeo, mat);
      const stubB = new THREE.Mesh(stubGeo, mat);
      stubA.renderOrder = 21;
      stubB.renderOrder = 21;
      root.add(stubA, stubB);

      const fMat = new THREE.SpriteMaterial({
        map: sparkTex,
        transparent: true,
        opacity: 0.0,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const flashMesh = new THREE.Sprite(fMat);
      flashMesh.renderOrder = 25;
      root.add(flashMesh);

      bonds.push({
        a: nA, b: nB, isShear: true, stubA, stubB, flashMesh, fMat, mat,
        snapThresh: 0.22 + diagIdx * 0.14,
      });
    }
  }

  let shearCounter = 0;
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      if (c + 1 < COLS) addBond(getNode(r, c), getNode(r, c + 1), false);
      if (r + 1 < ROWS) {
        const isShear = (r === 1);
        // Outer columns experience highest shear -> snap first!
        const orderFromEdge = Math.abs(c - 2); // 2, 1, 0
        const snapRank = 2 - orderFromEdge;    // 0 (edges snap first!) -> 1 -> 2 (center snaps right before SHATTER_F!)
        addBond(getNode(r, c), getNode(r + 1, c), isShear, snapRank);
        shearCounter++;
        // Diagonal tetrahedral cross-link across shear boundary
        if (isShear && c + 1 < COLS) {
          addBond(getNode(r, c), getNode(r + 1, c + 1), true, snapRank + 0.5);
        }
      }
    }
  }

  // Bold 3D Force Vector Arrows (>< Contraction on top, <> Expansion on bottom)
  function makeForceArrow(hex, dirSign) {
    const g = new THREE.Group();
    const m = new THREE.MeshBasicMaterial({ color: hex });
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.24, 10), m);
    shaft.rotation.z = Math.PI / 2;
    g.add(shaft);
    const tip = new THREE.Mesh(new THREE.ConeGeometry(0.056, 0.12, 12), m);
    tip.rotation.z = dirSign > 0 ? -Math.PI / 2 : Math.PI / 2;
    tip.position.x = dirSign * 0.16;
    g.add(tip);
    g.renderOrder = 24;
    return g;
  }

  const coldArrL = makeForceArrow('#2ef2ff', +1);
  const coldArrR = makeForceArrow('#2ef2ff', -1);
  coldArrL.position.set(-0.62, 0.52, 0.06);
  coldArrR.position.set( 0.62, 0.52, 0.06);
  root.add(coldArrL, coldArrR);

  const hotArrL = makeForceArrow('#ff4e18', -1);
  const hotArrR = makeForceArrow('#ff4e18', +1);
  hotArrL.position.set(-0.42, -0.52, 0.06);
  hotArrR.position.set( 0.42, -0.52, 0.06);
  root.add(hotArrL, hotArrR);

  const upVec = new THREE.Vector3(0, 1, 0);
  const tmpDir = new THREE.Vector3();
  const midPt = new THREE.Vector3();

  return {
    root,
    update({ visible = false, reveal = 1.0, shear = 0.0, snapProgress = 0.0, time = 0.0, calmBoroMode = false }) {
      root.visible = visible && reveal > 0.01;
      if (!root.visible) return;

      const sc = GLM.mix(0.86, 1.0, GLM.clamp(reveal, 0, 1));
      root.scale.setScalar(sc);

      const effShear = calmBoroMode ? shear * 0.18 : shear;

      for (const nd of nodes) {
        if (calmBoroMode) {
          nd.mesh.material = (nd.c + nd.r) % 2 === 0 ? boroAtomMat : coldAtomMat;
          const gentle = Math.sin(time * 5.0 + nd.phase) * 0.006;
          nd.mesh.position.set(nd.bx * (1.0 + 0.04 * effShear) + gentle, nd.by, nd.bz);
        } else {
          nd.mesh.material = nd.isCold ? coldAtomMat : hotAtomMat;
          // True statistical-mechanics thermal vibration: 300°C inner atoms vibrate 5x more violently than 10°C cold atoms!
          const jAmp = nd.isCold ? 0.004 : (0.016 + 0.014 * effShear);
          const jx = Math.sin(time * 42.0 + nd.phase) * jAmp;
          const jy = Math.cos(time * 37.0 + nd.phase * 1.3) * jAmp;
          const scaleX = nd.isCold ? (1.0 - 0.30 * effShear) : (1.0 + 0.34 * effShear);
          const yPull = nd.isCold ? (0.045 * effShear) : (-0.045 * effShear);
          nd.mesh.position.set(nd.bx * scaleX + jx, nd.by + yPull + jy, nd.bz);
        }
      }

      for (let bi = 0; bi < bonds.length; bi++) {
        const bd = bonds[bi];
        const pA = bd.a.mesh.position;
        const pB = bd.b.mesh.position;
        tmpDir.subVectors(pB, pA);
        const dist = tmpDir.length();
        const unitDir = tmpDir.clone().normalize();

        if (!bd.isShear) {
          bd.mat.color.set(calmBoroMode ? '#3cf5c8' : (bd.a.isCold ? '#66f0ff' : '#ff7b3d'));
          bd.mesh.scale.set(1.0, dist, 1.0);
          bd.mesh.position.copy(pA).addScaledVector(unitDir, dist * 0.5);
          bd.mesh.quaternion.setFromUnitVectors(upVec, unitDir);
          bd.oxy.position.copy(bd.mesh.position);
        } else {
          const snapAmt = calmBoroMode ? 0.0 : GLM.clamp((snapProgress - bd.snapThresh) / 0.16, 0, 1);
          const crit = calmBoroMode ? 0.0 : GLM.clamp(effShear * 1.25, 0, 1);

          if (calmBoroMode) {
            bd.mat.color.set('#56fadc');
          } else {
            const pulse = 0.78 + 0.22 * Math.sin(time * 45.0 + bi);
            bd.mat.color.setRGB(1.0, GLM.mix(0.88, 0.16, crit) * pulse, GLM.mix(0.58, 0.08, crit));
          }

          // When snapAmt > 0, the bond splits in the middle and both broken stubs recoil back toward their atoms!
          const halfLen = dist * 0.5 * (1.0 - 0.68 * snapAmt);
          const thin = 1.0 - 0.42 * crit;
          bd.stubA.scale.set(thin, Math.max(0.01, halfLen), thin);
          bd.stubB.scale.set(thin, Math.max(0.01, halfLen), thin);
          bd.stubA.position.copy(pA).addScaledVector(unitDir, halfLen * 0.5);
          bd.stubB.position.copy(pB).addScaledVector(unitDir, -halfLen * 0.5);
          bd.stubA.quaternion.setFromUnitVectors(upVec, unitDir);
          bd.stubB.quaternion.setFromUnitVectors(upVec, unitDir);

          // Soft radial electric plasma flash right at the moment of bond rupture!
          if (snapAmt > 0.02 && snapAmt < 0.78) {
            const spk = Math.sin((snapAmt / 0.78) * Math.PI);
            bd.flashMesh.visible = true;
            midPt.copy(pA).addScaledVector(unitDir, dist * 0.5);
            bd.flashMesh.position.copy(midPt);
            bd.flashMesh.position.z += 0.04;
            const sc = 0.18 + 0.26 * spk;
            bd.flashMesh.scale.set(sc, sc, 1.0);
            bd.fMat.opacity = 0.92 * spk;
          } else {
            bd.flashMesh.visible = false;
          }
        }
      }

      // 3D Force Vectors (tucked cleanly inside/along sliced crystal rim!)
      const showArrows = !calmBoroMode;
      coldArrL.visible = coldArrR.visible = hotArrL.visible = hotArrR.visible = showArrows;
      if (showArrows) {
        const ap = 0.030 * Math.sin(time * 10.0);
        const asc = 0.82 + 0.26 * effShear;
        coldArrL.scale.setScalar(asc);
        coldArrR.scale.setScalar(asc);
        hotArrL.scale.setScalar(asc);
        hotArrR.scale.setScalar(asc);
        coldArrL.position.x = -0.52 + effShear * 0.10 + ap;
        coldArrR.position.x =  0.52 - effShear * 0.10 - ap;
        hotArrL.position.x  = -0.34 - effShear * 0.14 - ap;
        hotArrR.position.x  =  0.34 + effShear * 0.14 + ap;
      }
    },
  };
}


// =============================================================================
// 5. 128 DUAL-TEMP FACETED CRYSTAL SHARDS + MATRIX BULLET-TIME + 140 WATER GLOBULES + WET PUDDLE
// =============================================================================
export function createUltraShatterAndWaterBurst({
  yOrigin = 0.22,
  glassRadius = 0.55,
  glassHeight = 2.06,
  seed = 90210,
} = {}) {
  const group = new THREE.Group();
  const rng = mulberry32(seed);

  // A. Custom Dual-Temperature Optical Crystal Shard Shader (ZERO fake Tron wireframes!):
  //    - Inner shard face glows with residual 300°C warm amber heat that cools over time!
  //    - Outer shard face reflects crisp 10°C ice-cyan studio light!
  //    - Beveled facets fire blinding diamond specular star-glints dynamically as each shard spins!
  const shardCrystalMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    uniforms: {
      uCoolDecay: { value: 1.0 },
      uTime: { value: 0.0 },
    },
    vertexShader: `
      varying vec3 vWorldPos;
      varying vec3 vWorldNormal;
      void main() {
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorldPos = wp.xyz;
        vWorldNormal = normalize(mat3(modelMatrix) * normal);
        gl_Position = projectionMatrix * viewMatrix * wp;
      }
    `,
    fragmentShader: `
      uniform float uCoolDecay;
      uniform float uTime;
      varying vec3 vWorldPos;
      varying vec3 vWorldNormal;
      void main() {
        vec3 V = normalize(cameraPosition - vWorldPos);
        vec3 N = normalize(gl_FrontFacing ? vWorldNormal : -vWorldNormal);
        float ndv = abs(dot(N, V));
        float fres = pow(1.0 - ndv, 2.4);

        vec3 R = reflect(-V, N);
        vec3 keyDir1 = normalize(vec3( 0.58, 0.68, 0.45));
        vec3 keyDir2 = normalize(vec3(-0.65, 0.42, 0.62));
        vec3 rimDir  = normalize(vec3( 0.0,  0.85, -0.52));

        // Razor-sharp dynamic diamond facet specular glints as shards tumble!
        float glint1 = pow(max(0.0, dot(R, keyDir1)), 64.0) * 2.6;
        float glint2 = pow(max(0.0, dot(R, keyDir2)), 48.0) * 1.9;
        float broad  = pow(max(0.0, dot(R, rimDir)),  12.0) * 0.65;

        // Dual-temp memory: back/inner face carries warm 300°C orange glow right after shatter!
        vec3 coldGlass = vec3(0.68, 0.94, 1.0);
        vec3 hotInner  = vec3(1.0, 0.44, 0.10) * uCoolDecay;
        vec3 bodyCol = gl_FrontFacing
          ? mix(vec3(0.16, 0.48, 0.62), coldGlass, fres)
          : mix(vec3(0.32, 0.22, 0.16), hotInner, 0.65);

        vec3 finalCol = bodyCol
                      + coldGlass * (fres * 0.95 + broad)
                      + vec3(1.0, 0.99, 0.96) * (glint1 + glint2);

        float alpha = clamp(0.34 + 0.52 * fres + (glint1 + glint2) * 0.45, 0.28, 0.95);
        gl_FragColor = vec4(finalCol, alpha);
      }
    `,
  });

  const TOTAL_SHARDS = 128;
  const shards = [];

  for (let i = 0; i < TOTAL_SHARDS; i++) {
    const isNeedle = i >= 84;
    const sides = i % 3 === 0 ? 3 : (i % 4 === 0 ? 5 : 4);
    const poly = new THREE.Shape();
    const baseSize = isNeedle ? (0.036 + rng() * 0.062) : (0.072 + rng() * 0.145);
    const stretchY = isNeedle ? (1.8 + rng() * 1.4) : (1.15 + rng() * 0.95);

    for (let v = 0; v < sides; v++) {
      const a = (v / sides) * Math.PI * 2 + (rng() - 0.5) * 0.55;
      const radV = baseSize * (v === 0 ? 1.38 : (0.48 + rng() * 0.56));
      const px = Math.cos(a) * radV * 0.78;
      const py = Math.sin(a) * radV * stretchY;
      if (v === 0) poly.moveTo(px, py);
      else poly.lineTo(px, py);
    }
    poly.closePath();

    const geo = new THREE.ExtrudeGeometry(poly, {
      depth: isNeedle ? 0.014 : (0.026 + rng() * 0.030),
      bevelEnabled: true,
      bevelThickness: isNeedle ? 0.004 : 0.008,
      bevelSize: isNeedle ? 0.004 : 0.007,
      bevelSegments: 1,
    });
    geo.computeVertexNormals();

    const mesh = new THREE.Mesh(geo, shardCrystalMat);
    mesh.castShadow = !isNeedle && (i % 2 === 0);
    mesh.visible = false;
    mesh.renderOrder = 17;
    group.add(mesh);

    const rawAng = (i / TOTAL_SHARDS) * Math.PI * 2 + (rng() - 0.5) * 0.32;
    const rSpawn = glassRadius * (0.78 + rng() * 0.26);
    const x0 = Math.cos(rawAng) * rSpawn;
    const z0 = Math.sin(rawAng) * rSpawn; // EXPLICITLY DEFINED -> NaN IMPOSSIBLE!
    const y0 = yOrigin + 0.26 + rng() * (glassHeight - 0.30);

    const speedRadial = isNeedle ? (0.85 + rng() * 1.65) : (0.95 + rng() * 1.95);
    const vx = Math.cos(rawAng) * speedRadial * 0.82;
    const vz = Math.sin(rawAng) * speedRadial + (z0 > 0 ? 0.52 : 0.0);
    const vy = 0.55 + (y0 - yOrigin) * 0.85 + rng() * 1.45;

    shards.push({
      mesh,
      x0, y0, z0,
      vx, vy, vz,
      rx0: rng() * 6.28, ry0: rng() * 6.28, rz0: rng() * 6.28,
      rvx: (rng() - 0.5) * 15.0,
      rvy: (rng() - 0.5) * 15.0,
      rvz: (rng() - 0.5) * 15.0,
      restY: 0.025 + rng() * 0.032,
      bounce: 0.30 + rng() * 0.16,
    });
  }

  // B. 140 Photoreal Refractive Liquid Water Globules & Splash Mist (`InstancedMesh` Fresnel Shader!)
  const globGeo = new THREE.SphereGeometry(0.028, 12, 10);
  const globMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    vertexShader: `
      varying vec3 vNormalW;
      varying vec3 vViewDir;
      void main() {
        vec4 wPos = modelMatrix * instanceMatrix * vec4(position, 1.0);
        vNormalW = normalize(mat3(modelMatrix) * mat3(instanceMatrix) * normal);
        vViewDir = normalize(cameraPosition - wPos.xyz);
        gl_Position = projectionMatrix * viewMatrix * wPos;
      }
    `,
    fragmentShader: `
      varying vec3 vNormalW;
      varying vec3 vViewDir;
      void main() {
        vec3 N = normalize(vNormalW);
        vec3 V = normalize(vViewDir);
        float ndv = clamp(abs(dot(N, V)), 0.0, 1.0);
        // Crystal-clear transparent water interior + icy silver-cyan Fresnel rim + razor-sharp studio pinpoint glint!
        float fresnel = pow(1.0 - ndv, 2.75);
        vec3 R = reflect(-V, N);
        float keySpec = pow(max(dot(R, normalize(vec3(0.52, 0.76, 0.40))), 0.0), 56.0);
        float rimSpec = pow(max(dot(R, normalize(vec3(-0.62, 0.44, 0.55))), 0.0), 28.0);
        float softStrip = smoothstep(0.84, 0.97, abs(R.x * 0.78 + R.y * 0.28)) * smoothstep(-0.15, 0.75, R.y);

        vec3 coreCol = vec3(0.07, 0.28, 0.40);
        vec3 rimCol  = vec3(0.62, 0.95, 1.00);
        vec3 col = mix(coreCol, rimCol, fresnel)
                 + vec3(1.0, 0.99, 0.96) * (keySpec * 2.6 + softStrip * 0.78)
                 + vec3(0.45, 0.95, 1.0) * rimSpec * 1.15;

        float alpha = clamp(0.16 + fresnel * 0.68 + keySpec * 0.88 + softStrip * 0.34, 0.16, 0.95);
        gl_FragColor = vec4(col, alpha);
      }
    `,
  });
  const WATER_COUNT = 140;
  const waterGlobs = new THREE.InstancedMesh(globGeo, globMat, WATER_COUNT);
  waterGlobs.visible = false;
  waterGlobs.renderOrder = 16;
  group.add(waterGlobs);

  const globData = [];
  for (let i = 0; i < WATER_COUNT; i++) {
    const a = (i / WATER_COUNT) * Math.PI * 2 + (rng() - 0.5) * 0.4;
    const r0 = rng() * 0.44;
    const x0 = Math.cos(a) * r0;
    const z0 = Math.sin(a) * r0;
    const y0 = yOrigin + 0.28 + rng() * 1.28;
    const spd = 0.75 + rng() * 2.15;
    const szRoll = rng();
    const baseSc = szRoll < 0.45 ? (0.38 + rng() * 0.28) : szRoll < 0.85 ? (0.70 + rng() * 0.38) : (1.12 + rng() * 0.36);
    globData.push({
      x0, y0, z0,
      vx: Math.cos(a) * spd * 0.85,
      vy: 0.45 + rng() * 1.95,
      vz: Math.sin(a) * spd + (z0 > 0 ? 0.38 : 0.0),
      sc: baseSc,
    });
  }

  // C. Expanding Wet Specular Water Puddle on Optical Breadboard (`S7_AFTERMATH_SIZZLE`)
  const pudCv = document.createElement('canvas');
  pudCv.width = pudCv.height = 256;
  const pctx = pudCv.getContext('2d');
  const pg = pctx.createRadialGradient(128, 128, 18, 128, 128, 122);
  pg.addColorStop(0.0, 'rgba(65, 215, 245, 0.42)');
  pg.addColorStop(0.68, 'rgba(45, 180, 220, 0.32)');
  pg.addColorStop(0.88, 'rgba(180, 250, 255, 0.48)');
  pg.addColorStop(1.0, 'rgba(0, 0, 0, 0.0)');
  pctx.fillStyle = pg;
  pctx.fillRect(0, 0, 256, 256);
  const pudTex = new THREE.CanvasTexture(pudCv);
  const puddleMat = new THREE.MeshBasicMaterial({
    map: pudTex,
    transparent: true,
    opacity: 0.0,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const puddleMesh = new THREE.Mesh(new THREE.PlaneGeometry(3.8, 3.8), puddleMat);
  puddleMesh.rotation.x = -Math.PI / 2;
  puddleMesh.position.y = 0.010;
  puddleMesh.visible = false;
  puddleMesh.renderOrder = 8;
  group.add(puddleMesh);

  // True Matrix Bullet-Time Piecewise Physics Time Mapper!
  //   dtReal 0.00..0.10s -> fast explosive expansion (0.00..0.14s sim)
  //   dtReal 0.10..1.48s -> slow-motion Matrix bullet-time orbit (0.14..0.38s sim = 0.17x speed!)
  //   dtReal 1.48s+      -> "DHADAM!" gravity snaps back to 1.0x real-time fall & floor bounces!
  function mapBulletTime(dtReal) {
    if (dtReal <= 0) return 0;
    if (dtReal < 0.10) return dtReal * 1.40;
    if (dtReal < 1.48) return 0.14 + (dtReal - 0.10) * 0.174;
    return 0.38 + (dtReal - 1.48) * 1.08;
  }

  function assertFinitePositions() {
    for (let i = 0; i < shards.length; i++) {
      const p = shards[i].mesh.position;
      if (!Number.isFinite(p.x) || !Number.isFinite(p.y) || !Number.isFinite(p.z)) {
        throw new Error(`[V6 ULTRA NaN GUARD] Shard ${i} non-finite position: (${p.x}, ${p.y}, ${p.z})`);
      }
    }
  }

  const dummy = new THREE.Object3D();
  const dirVec = new THREE.Vector3();
  const upAxis = new THREE.Vector3(0, 1, 0);
  const GRAV = 9.6;

  return {
    group,
    shards,
    waterGlobs,
    puddleMesh,
    mapBulletTime,
    update(dtReal, active = false, realTime = 0.0) {
      if (!active || dtReal < 0) {
        group.visible = false;
        return;
      }
      group.visible = true;

      const tSim = mapBulletTime(dtReal);
      shardCrystalMat.uniforms.uCoolDecay.value = Math.exp(-dtReal * 0.45);
      shardCrystalMat.uniforms.uTime.value = realTime;

      // 1. Update all 128 faceted dual-temp crystal shards
      for (let i = 0; i < shards.length; i++) {
        const s = shards[i];
        s.mesh.visible = true;

        let y = s.y0 + s.vy * tSim - 0.5 * GRAV * tSim * tSim;
        let groundSpinDamp = 1.0;
        let slideFriction = 1.0;

        if (y < s.restY) {
          const disc = s.vy * s.vy + 2.0 * GRAV * (s.y0 - s.restY);
          const tImpact1 = (s.vy + Math.sqrt(Math.max(0.0001, disc))) / GRAV;
          const vImpact1 = Math.sqrt(Math.max(0.0, disc));
          const dt1 = Math.max(0, tSim - tImpact1);
          const vB1 = vImpact1 * s.bounce;
          const durB1 = (2.0 * vB1) / GRAV;

          if (dt1 < durB1) {
            y = s.restY + vB1 * dt1 - 0.5 * GRAV * dt1 * dt1;
            groundSpinDamp = 0.48;
            slideFriction = 0.80;
          } else {
            const dt2 = dt1 - durB1;
            const vB2 = vB1 * s.bounce * 0.55;
            const durB2 = (2.0 * vB2) / GRAV;
            if (dt2 < durB2) {
              y = s.restY + vB2 * dt2 - 0.5 * GRAV * dt2 * dt2;
              groundSpinDamp = 0.20;
              slideFriction = 0.64;
            } else {
              y = s.restY;
              groundSpinDamp = 0.0;
              slideFriction = 0.56;
            }
          }
        }

        const effT = slideFriction < 1.0 ? tSim * slideFriction + 0.16 * (1.0 - slideFriction) : tSim;
        s.mesh.position.set(s.x0 + s.vx * effT, y, s.z0 + s.vz * effT);

        if (groundSpinDamp > 0.0) {
          const rotT = tSim * (0.45 + 0.55 * groundSpinDamp);
          s.mesh.rotation.set(s.rx0 + s.rvx * rotT, s.ry0 + s.rvy * rotT, s.rz0 + s.rvz * rotT);
        } else {
          s.mesh.rotation.set(Math.PI * 0.5, s.ry0 + 0.7, 0.08 * ((i % 3) - 1));
        }
      }

      assertFinitePositions();

      // 2. Update 140 3D Water Globules (stretch into teardrops along velocity vector!)
      waterGlobs.visible = dtReal < 4.8;
      if (waterGlobs.visible) {
        globMat.opacity = 0.80 * (1.0 - GLM.smoothstep(3.2, 4.8, dtReal));
        for (let i = 0; i < WATER_COUNT; i++) {
          const g = globData[i];
          const gx = g.x0 + g.vx * tSim;
          const gz = g.z0 + g.vz * tSim;
          let gy = g.y0 + g.vy * tSim - 0.5 * (GRAV * 1.05) * tSim * tSim;
          const curVy = g.vy - (GRAV * 1.05) * tSim;

          if (gy <= 0.02) {
            // Splashed flat into floor puddle!
            dummy.position.set(gx, 0.015, gz);
            dummy.rotation.set(0, 0, 0);
            dummy.scale.set(g.sc * 1.8, 0.12, g.sc * 1.8);
          } else {
            dummy.position.set(gx, gy, gz);
            dirVec.set(g.vx, curVy, g.vz);
            const spd = dirVec.length();
            if (spd > 0.01) {
              dummy.quaternion.setFromUnitVectors(upAxis, dirVec.normalize());
            }
            const stretch = 1.0 + Math.min(1.8, spd * 0.38);
            dummy.scale.set(g.sc * 0.78, g.sc * stretch, g.sc * 0.78);
          }
          dummy.updateMatrix();
          waterGlobs.setMatrixAt(i, dummy.matrix);
        }
        waterGlobs.instanceMatrix.needsUpdate = true;
      }

      // 3. Expanding Wet Specular Puddle on Table after Gravity Snap (`dtReal > 1.45s`)
      if (dtReal > 1.35) {
        puddleMesh.visible = true;
        const pGrow = GLM.smoothstep(1.35, 3.6, dtReal);
        puddleMesh.scale.setScalar(0.35 + 0.85 * pGrow);
        puddleMat.opacity = 0.62 * pGrow;
      } else {
        puddleMesh.visible = false;
      }
    },
  };
}
