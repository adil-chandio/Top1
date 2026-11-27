import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
import {
  buildNormalFromCanvas,
  mulberry32,
} from '/tools/monarch-v6-imax-sdk/index.js';
import {
  createAdamantiumClawRig,
  createNurbsRigOverlay,
  createRigPickerBoard,
} from './claws_nurbs_v6.js';

/**
 * Logan — Rig-to-Render VFX Breakdown (`V6.2 Hollywood IMAX`)
 * Loads MIT-licensed Unreal MetaHuman 5.7 Bruce rig (`148,243` verts, 3 synchronized skins,
 * 51 ARKit blendshapes) and upgrades it with:
 *   1. Full Logan Chin-Beard Card Augmentation + Jawline Stubble Shader (connecting mutton-chops!)
 *   2. High-Frequency 4K-Equivalent Cellular Skin Pore Micro-Normal + Sweat Sheen + Dermal SSS + Knuckle Bruising
 *   3. Weathered Blood-Stained Dusty Linen/Chambray Workshirt Lookdev (`Bruce_Outfits`)
 *   4. Instant Dual-Mode Lookdev Switch (`viewport_clay` <-> `final_render`) for zero-latency Match-Cuts!
 */

const BRUCE_BASE = '/@fs/tmp/v6_runtime/assets/bruce';
const DRACO_PATH = '/@fs/tmp/v6_runtime/node_modules/three/examples/jsm/libs/draco/gltf/';

function buildMicroPoreNormalMap(seed = 3107) {
  const S = 512;
  const c = document.createElement('canvas');
  c.width = S;
  c.height = S;
  const ctx = c.getContext('2d');
  const rng = mulberry32(seed);
  ctx.fillStyle = '#888888';
  ctx.fillRect(0, 0, S, S);

  // Dense cellular skin pores + micro-creases
  for (let i = 0; i < 4800; i++) {
    const x = rng() * S;
    const y = rng() * S;
    const r = 0.7 + rng() * 1.65;
    ctx.fillStyle = rng() > 0.25 ? 'rgba(28,28,28,0.34)' : 'rgba(215,215,215,0.22)';
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }
  for (let i = 0; i < 360; i++) {
    const x = rng() * S;
    const y = rng() * S;
    const ang = rng() * Math.PI;
    const len = 4 + rng() * 10;
    ctx.strokeStyle = 'rgba(38,38,38,0.22)';
    ctx.lineWidth = 0.8;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + Math.cos(ang) * len, y + Math.sin(ang) * len);
    ctx.stroke();
  }
  const tex = buildNormalFromCanvas(c, 1.85, S);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return tex;
}

function buildWeatheredLinenTextures(seed = 8841) {
  const S = 512;
  const weave = document.createElement('canvas');
  weave.width = S;
  weave.height = S;
  const wctx = weave.getContext('2d');
  const rng = mulberry32(seed);

  wctx.fillStyle = '#808080';
  wctx.fillRect(0, 0, S, S);
  for (let y = 0; y < S; y += 2) {
    wctx.fillStyle = y % 4 === 0 ? 'rgba(215,215,215,0.32)' : 'rgba(45,45,45,0.32)';
    wctx.fillRect(0, y, S, 1);
  }
  for (let x = 0; x < S; x += 2) {
    wctx.fillStyle = x % 4 === 0 ? 'rgba(205,205,205,0.28)' : 'rgba(55,55,55,0.28)';
    wctx.fillRect(x, 0, 1, S);
  }
  const weaveNormal = buildNormalFromCanvas(weave, 2.1, S);
  weaveNormal.wrapS = weaveNormal.wrapT = THREE.RepeatWrapping;

  // Macro battle-grime & dried crimson stain map (512x512)
  const stain = document.createElement('canvas');
  stain.width = S;
  stain.height = S;
  const sctx = stain.getContext('2d');
  sctx.fillStyle = '#9e9590';
  sctx.fillRect(0, 0, S, S);

  // Sweat & dust blotches
  for (let i = 0; i < 140; i++) {
    const x = rng() * S;
    const y = rng() * S;
    const r = 18 + rng() * 58;
    const g = sctx.createRadialGradient(x, y, 2, x, y, r);
    const dark = rng() > 0.42;
    g.addColorStop(0, dark ? 'rgba(62, 54, 50, 0.34)' : 'rgba(182, 174, 168, 0.24)');
    g.addColorStop(1, 'rgba(128, 120, 115, 0.0)');
    sctx.fillStyle = g;
    sctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  // Dried crimson-rust battle splatters (matching weathered shirt in sheet1 f=094!)
  for (let i = 0; i < 85; i++) {
    const x = rng() * S;
    const y = rng() * S;
    const r = 6 + rng() * 34;
    const g = sctx.createRadialGradient(x, y, 1, x, y, r);
    g.addColorStop(0, 'rgba(78, 22, 19, 0.46)');
    g.addColorStop(0.55, 'rgba(92, 31, 26, 0.22)');
    g.addColorStop(1, 'rgba(92, 31, 26, 0.0)');
    sctx.fillStyle = g;
    sctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  const stainTex = new THREE.CanvasTexture(stain);
  stainTex.wrapS = stainTex.wrapT = THREE.RepeatWrapping;
  stainTex.colorSpace = THREE.SRGBColorSpace;
  return { weaveNormal, stainTex };
}

function buildEyeOcclusionAlphaMap() {
  const S = 256;
  const c = document.createElement('canvas');
  c.width = S;
  c.height = S;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, S, S);
  const g = ctx.createRadialGradient(S / 2, S / 2, S * 0.12, S / 2, S / 2, S * 0.54);
  g.addColorStop(0.0, '#000');
  g.addColorStop(0.58, '#444');
  g.addColorStop(1.0, '#fff');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, S, S);
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
  return tex;
}

/**
 * Builds dense 3D Chin-Beard Strand Cards attached to `FACIAL_C_Jaw` so Bruce's mutton-chops +
 * horseshoe mustache connect seamlessly into Logan's rugged full chin & under-jaw beard!
 */
function buildChinBeardCards(beardMatRender, beardMatClay, jawBones) {
  const host = jawBones[0];
  if (!host) return { setMode: () => {} };

  // Note: `FACIAL_C_Jaw` rest position is `[-0.002, 1.777, 0.037]`, local axes:
  //   X = `[+1, 0, 0]` (world +X),
  //   Y = `[0, -0.64, +0.77]` (down-forward toward chin tip!),
  //   Z = `[0, -0.77, -0.64]` (down-back under chin!).
  // Chin tip in world is ~ `[0, 1.735, 0.106]` -> delta from jaw `[0, -0.042, +0.069]`
  // In jaw local coords: `y_loc = (-0.042)*(-0.64) + 0.069*(0.77) = +0.080`, `z_loc = (-0.042)*(-0.77) + 0.069*(-0.64) = -0.012`!
  const rng = mulberry32(7719);
  const positions = [];
  const normals = [];
  const uvs = [];
  const indices = [];

  const CARD_COUNT = 210;
  for (let i = 0; i < CARD_COUNT; i++) {
    const uSpread = (rng() - 0.5) * 2.0; // -1..+1 across chin width (bridging mutton chops at ±0.046m)
    const vLayer = rng(); // 0 = soul-patch/upper chin, 1 = under-chin/jawline
    const xBase = uSpread * (0.036 + 0.012 * vLayer);
    const arch = Math.cos(uSpread * 1.15);
    const yBase = 0.096 + 0.018 * arch - 0.016 * vLayer;
    const zBase = -0.020 + 0.008 * arch - 0.020 * vLayer;

    const cardW = 0.013 + rng() * 0.008;
    const cardL = 0.022 + rng() * 0.014;
    // Grow downward-forward in jaw local (+0.32 Y, +0.92 Z = world down!)
    const dirX = uSpread * 0.16 + (rng() - 0.5) * 0.08;
    const dirY = 0.42 + (rng() - 0.5) * 0.12;
    const dirZ = 0.88 + (rng() - 0.5) * 0.10;
    const dLen = Math.hypot(dirX, dirY, dirZ);
    const dx = (dirX / dLen) * cardL;
    const dy = (dirY / dLen) * cardL;
    const dz = (dirZ / dLen) * cardL;

    // Tangent across card width
    const tx = cardW * 0.5;
    const ty = -uSpread * cardW * 0.18;
    const tz = 0.0;

    const baseIdx = positions.length / 3;
    // Quad with slight outward bow
    positions.push(
      xBase - tx, yBase - ty, zBase - tz,
      xBase + tx, yBase + ty, zBase + tz,
      xBase - tx * 0.82 + dx, yBase - ty + dy, zBase - tz + dz,
      xBase + tx * 0.82 + dx, yBase + ty + dy, zBase + tz + dz
    );

    const nx = uSpread * 0.45, ny = 0.82, nz = -0.35;
    const nl = Math.hypot(nx, ny, nz);
    for (let k = 0; k < 4; k++) normals.push(nx / nl, ny / nl, nz / nl);

    // Sample rich dense strand region of Beard_M_MuttonChops_CardsAtlas_Attribute
    const u0 = 0.08 + (i % 5) * 0.16;
    const u1 = u0 + 0.14;
    uvs.push(u0, 0.08, u1, 0.08, u0, 0.94, u1, 0.94);
    indices.push(baseIdx, baseIdx + 2, baseIdx + 1, baseIdx + 1, baseIdx + 2, baseIdx + 3);
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geo.setIndex(indices);

  // Two-pass (opaque core + soft fringe) matching Bruce's mutton-chops!
  const coreRender = beardMatRender.inner.clone();
  const fringeRender = beardMatRender.outer.clone();
  const coreMesh = new THREE.Mesh(geo, coreRender);
  const fringeMesh = new THREE.Mesh(geo, fringeRender);
  coreMesh.castShadow = true;
  coreMesh.frustumCulled = false;
  fringeMesh.frustumCulled = false;
  fringeMesh.renderOrder = 8;

  host.add(coreMesh);
  host.add(fringeMesh);

  return {
    setMode(mode) {
      const isClay = mode === 'viewport_clay';
      coreMesh.material = isClay ? beardMatClay.inner : coreRender;
      fringeMesh.material = isClay ? beardMatClay.outer : fringeRender;
    },
  };
}

function createHairMaterialPair(atlasTex, colorHex, density = 1.8, roughFloor = 0.52, isClay = false, innerAlphaTest = 0.38) {
  const buildPass = (isInner) => {
    const mat = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color(isClay ? '#6c6a67' : colorHex),
      roughness: isClay ? 0.80 : roughFloor,
      metalness: 0.0,
      anisotropy: isClay ? 0.0 : 0.32,
      anisotropyRotation: -0.66,
      alphaMap: atlasTex,
      transparent: !isInner,
      depthWrite: isInner,
      alphaTest: isInner ? innerAlphaTest : 0.0,
      opacity: isInner ? 1.0 : (isClay ? 0.88 : 0.90),
      side: THREE.DoubleSide,
      // CRITICAL: the inner opaque "core" pass and the outer strand pass share geometry.
      // Applying the SAME polygon offset to both cancels out and the two passes z-fight,
      // shredding the groom into hard-edged black scribbles. Push the inner core AWAY
      // from camera, and pull the outer strand pass TOWARD it.
      polygonOffset: true,
      polygonOffsetFactor: isInner ? 1.5 : -3.0,
      polygonOffsetUnits: isInner ? 8.0 : -14.0,
    });
    mat.customProgramCacheKey = () => `logan_hair_v3_${colorHex}_${isInner}_${isClay}_${density}_${innerAlphaTest}`;
    mat.onBeforeCompile = (shader) => {
      shader.uniforms.uHairDensity = { value: isInner ? Math.max(1.20, density * 0.45) : density };
      shader.uniforms.uSeedAmp = { value: isClay ? 0.12 : 0.34 };
      shader.fragmentShader = `
        uniform float uHairDensity;
        uniform float uSeedAmp;
      ` + shader.fragmentShader;
      shader.fragmentShader = shader.fragmentShader.replace(
        '#include <map_fragment>',
        `
        #include <map_fragment>
        #ifdef USE_ALPHAMAP
          vec4 hAt = texture2D(alphaMap, vAlphaMapUv);
          float strandMul = 1.0 + (hAt.b - 0.5) * 2.0 * uSeedAmp;
          float ndv = abs(dot(normalize(vNormal), normalize(vViewPosition)));
          float hAO = mix(0.32, 1.0, smoothstep(0.05, 0.55, ndv));
          diffuseColor.rgb *= strandMul * hAO;
        #endif
        `
      );
      shader.fragmentShader = shader.fragmentShader.replace(
        '#include <alphamap_fragment>',
        `
        #ifdef USE_ALPHAMAP
          float hCov = texture2D(alphaMap, vAlphaMapUv).r;
          diffuseColor.a *= clamp(hCov * uHairDensity, 0.0, 1.0);
        #endif
        `
      );
    };
    return mat;
  };
  return { inner: buildPass(true), outer: buildPass(false) };
}

export async function loadLoganActor(scene) {
  const draco = new DRACOLoader();
  draco.setDecoderPath(DRACO_PATH);
  const gltfLoader = new GLTFLoader();
  gltfLoader.setDRACOLoader(draco);

  const texLoader = new THREE.TextureLoader();
  const loadPng = (file, srgb = false) => new Promise((resolve, reject) => {
    texLoader.load(
      `${BRUCE_BASE}/textures/${file}`,
      (t) => {
        t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
        t.flipY = false;
        t.wrapS = t.wrapT = THREE.RepeatWrapping;
        resolve(t);
      },
      undefined,
      reject
    );
  });

  const [
    gltf,
    beardAtlas,
    browAtlas,
    hairAtlas,
    mustacheAtlas,
    lashAtlas,
  ] = await Promise.all([
    gltfLoader.loadAsync(`${BRUCE_BASE}/bruce.glb`),
    loadPng('Beard_M_MuttonChops_CardsAtlas_Attribute.png', false),
    loadPng('Eyebrows_M_FlatThick_CardsAtlas_Attribute.png', false),
    loadPng('Hair_S_Casual_CardsAtlas_Attribute.png', false),
    loadPng('Mustache_S_Horseshoe_CardsAtlas_Attribute.png', false),
    loadPng('T_Eyelashes_S_Sparse_Coverage.png', false),
  ]);

  const actorRoot = gltf.scene;
  scene.add(actorRoot);

  // 1. Collect all bones grouped by canonical name across all 3 synchronized skins!
  //    (Three.js GLTFLoader renames duplicate bones in Skin 1 & Skin 2 with `_1` / `_2`,
  //     whereas native MetaHuman numbered bones are zero-padded `_01`, `_02`, `_03`!)
  const canonicalBoneName = (rawName) => rawName.replace(/_[1-9]\d*$/, '');
  const bonesByName = new Map();
  const restQuats = new Map();
  actorRoot.traverse((o) => {
    if (o.isBone) {
      const canon = canonicalBoneName(o.name);
      if (!bonesByName.has(canon)) bonesByName.set(canon, []);
      bonesByName.get(canon).push(o);
      restQuats.set(o, o.quaternion.clone());
    }
  });

  // 2. Collect all synchronized ARKit morph-target meshes (`FaceMesh`, `Beard`, `Eyebrows`, `Mustache`)!
  const morphMeshes = [];
  actorRoot.traverse((o) => {
    if (o.isMesh && o.morphTargetDictionary && o.morphTargetInfluences) {
      morphMeshes.push(o);
    }
  });

  // 3. Build high-frequency 4K-equivalent pore normal + weathered linen textures
  const poreNormal = buildMicroPoreNormalMap(3107);
  const { weaveNormal, stainTex } = buildWeatheredLinenTextures(8841);
  const eyeOccAlpha = buildEyeOcclusionAlphaMap();

  // Mode swap registry: `[{ mesh, slotIdx, clayMat, renderMat }]`
  const matSwaps = [];
  const registerSwap = (mesh, slotIdx, clayMat, renderMat) => {
    matSwaps.push({ mesh, slotIdx, clayMat, renderMat });
  };

  // Shared sculpted Maya/ZBrush clay generator (retains baked normal map + micro-pores!)
  const makeClayMat = (normalMap = null, normalScale = 0.75, baseHex = '#9fa3aa', rough = 0.76) => {
    const m = new THREE.MeshStandardMaterial({
      color: new THREE.Color(baseHex),
      roughness: rough,
      metalness: 0.02,
      normalMap: normalMap || null,
      normalScale: new THREE.Vector2(normalScale, normalScale),
      side: THREE.DoubleSide,
    });
    return m;
  };

  // Hair / Beard / Brow / Mustache two-pass pairs (Render + Clay)
  // Keep `0.42` inner alphaTest on facial grooms (zero card corners!) and `0.22` on scalp hair for dense bangs!
  const hairPairs = {
    Beard_M_MuttonChops_CardMesh_Group0_LOD0_CardMat: {
      render: createHairMaterialPair(beardAtlas, '#16110d', 2.05, 0.50, false, 0.42),
      clay:   createHairMaterialPair(beardAtlas, '#73716e', 1.95, 0.82, true,  0.42),
    },
    Eyebrows_M_FlatThick_CardsMesh_Group0_LOD0_CardMat: {
      render: createHairMaterialPair(browAtlas, '#0d0906', 2.60, 0.52, false, 0.34),
      clay:   createHairMaterialPair(browAtlas, '#6c6a67', 2.50, 0.82, true,  0.34),
    },
    Hair_S_Casual_CardsMesh_Group0_LOD0_CardMat: {
      render: createHairMaterialPair(hairAtlas, '#110b07', 5.10, 0.48, false, 0.22),
      clay:   createHairMaterialPair(hairAtlas, '#767471', 4.80, 0.80, true,  0.22),
    },
    Mustache_S_Horseshoe_CardMesh_Group0_LOD0_CardMat: {
      render: createHairMaterialPair(mustacheAtlas, '#1a140f', 1.75, 0.50, false, 0.42),
      clay:   createHairMaterialPair(mustacheAtlas, '#72706d', 1.65, 0.82, true,  0.42),
    },
  };

  const pendingHairCoreClones = [];

  actorRoot.traverse((obj) => {
    if (!obj.isMesh) return;
    obj.frustumCulled = false;
    obj.castShadow = true;
    obj.receiveShadow = true;

    const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
    mats.forEach((mat, slotIdx) => {
      if (!mat) return;
      const mName = mat.name || '';

      // A. Hair / Beard / Brow / Mustache Cards
      if (hairPairs[mName]) {
        const pair = hairPairs[mName];
        if (Array.isArray(obj.material)) obj.material[slotIdx] = pair.render.outer;
        else obj.material = pair.render.outer;
        obj.renderOrder = 8;
        registerSwap(obj, Array.isArray(obj.material) ? slotIdx : -1, pair.clay.outer, pair.render.outer);
        pendingHairCoreClones.push({ srcMesh: obj, pair });
        return;
      }

      // B. Hidden / EyeShell / Lacrimal helper slots -> clean wet corneal clearcoat or hidden mask
      if (mName === 'M_Hide' || mName === 'MI_Face_LacrimalFluid') {
        const hidden = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false, colorWrite: false });
        if (Array.isArray(obj.material)) obj.material[slotIdx] = hidden;
        else obj.material = hidden;
        return;
      }
      if (mName === 'MI_Face_EyeShell') {
        // Subtle socket ambient-occlusion rim + wet tear sheen
        const shellRender = new THREE.MeshPhysicalMaterial({
          color: new THREE.Color('#050303'),
          alphaMap: eyeOccAlpha,
          transparent: true,
          opacity: 0.55,
          depthWrite: false,
          roughness: 0.08,
          clearcoat: 1.0,
          clearcoatRoughness: 0.03,
        });
        const shellClay = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false, colorWrite: false });
        if (Array.isArray(obj.material)) obj.material[slotIdx] = shellRender;
        else obj.material = shellRender;
        registerSwap(obj, Array.isArray(obj.material) ? slotIdx : -1, shellClay, shellRender);
        return;
      }

      // C. Eyelashes
      if (mName.includes('LashMat')) {
        const lashRender = new THREE.MeshStandardMaterial({
          color: new THREE.Color('#0c0806'),
          alphaMap: lashAtlas,
          transparent: true,
          depthWrite: false,
          roughness: 0.55,
          side: THREE.DoubleSide,
        });
        lashRender.onBeforeCompile = (sh) => {
          sh.fragmentShader = sh.fragmentShader.replace(
            '#include <alphamap_fragment>',
            `#ifdef USE_ALPHAMAP\n diffuseColor.a *= clamp(texture2D(alphaMap, vAlphaMapUv).g * 1.6, 0.0, 1.0);\n#endif`
          );
        };
        const lashClay = lashRender.clone();
        lashClay.color.set('#686664');
        if (Array.isArray(obj.material)) obj.material[slotIdx] = lashRender;
        else obj.material = lashRender;
        registerSwap(obj, Array.isArray(obj.material) ? slotIdx : -1, lashClay, lashRender);
        return;
      }

      // D. Eyeballs (`MI_EyeL_Baked`, `MI_EyeR_Baked`) — razor-sharp wet cornea clearcoat + sculpted clay iris!
      if (mName.includes('MI_Eye')) {
        const eyeRender = new THREE.MeshPhysicalMaterial({
          map: mat.map,
          normalMap: mat.normalMap,
          normalScale: new THREE.Vector2(0.20, 0.20),
          roughness: 0.14,
          metalness: 0.0,
          clearcoat: 0.55,
          clearcoatRoughness: 0.06,
          ior: 1.42,
          specularIntensity: 1.05,
          envMapIntensity: 0.55,
        });
        const eyeClay = new THREE.MeshStandardMaterial({
          map: mat.map,
          roughness: 0.56,
          metalness: 0.0,
        });
        eyeClay.customProgramCacheKey = () => 'logan_eye_clay';
        eyeClay.onBeforeCompile = (sh) => {
          sh.fragmentShader = sh.fragmentShader.replace(
            '#include <map_fragment>',
            `
            vec4 eTex = texture2D(map, vMapUv);
            float eLum = dot(eTex.rgb, vec3(0.299, 0.587, 0.114));
            // Subtle ZBrush/Maya greyscale corneal iris & pupil ring so clay gaze is razor-focused!
            float clayShade = mix(0.46, 0.76, smoothstep(0.08, 0.62, eLum));
            diffuseColor.rgb = vec3(clayShade * 0.98, clayShade, clayShade * 1.03);
            `
          );
        };
        if (Array.isArray(obj.material)) obj.material[slotIdx] = eyeRender;
        else obj.material = eyeRender;
        registerSwap(obj, Array.isArray(obj.material) ? slotIdx : -1, eyeClay, eyeRender);
        return;
      }

      // E. Face & Body Skin (`MI_Face_Skin_Baked` & `MI_Body_Baked`) — Dermal SSS + 4K Micro-Pores + Sweat + Bruising + Chin Stubble!
      if (mName.includes('Skin_Baked') || mName.includes('Body_Baked')) {
        const isFace = mName.includes('Face_Skin');
        const skinRender = new THREE.MeshPhysicalMaterial({
          map: mat.map,
          normalMap: mat.normalMap,
          normalScale: new THREE.Vector2(isFace ? 1.15 : 1.05, isFace ? 1.15 : 1.05),
          roughnessMap: mat.roughnessMap,
          aoMap: mat.aoMap,
          roughness: 1.0,
          metalness: 0.0,
          specularIntensity: 0.88,
          specularColor: new THREE.Color('#ffefe4'),
          sheen: 0.10,
          sheenRoughness: 0.72,
          sheenColor: new THREE.Color('#9e4432'),
          clearcoat: isFace ? 0.24 : 0.18, // subtle sweat film sheen!
          clearcoatRoughness: 0.28,
          side: THREE.DoubleSide,
        });
        skinRender.customProgramCacheKey = () => `logan_skin_${isFace}`;
        skinRender.onBeforeCompile = (shader) => {
          shader.uniforms.uPoreNormal = { value: poreNormal };
          shader.uniforms.uIsFace = { value: isFace ? 1.0 : 0.0 };
          shader.vertexShader = `varying vec3 vObjPos;\n` + shader.vertexShader.replace(
            '#include <begin_vertex>',
            `#include <begin_vertex>\n vObjPos = position;`
          );
          shader.fragmentShader = `
            uniform sampler2D uPoreNormal;
            uniform float uIsFace;
            varying vec3 vObjPos;
          ` + shader.fragmentShader;

          shader.fragmentShader = shader.fragmentShader.replace(
            '#include <map_fragment>',
            `
            #include <map_fragment>
            // Deep weathered Logan tan + dermal blood warmth + battle bruising!
            diffuseColor.rgb *= vec3(0.96, 0.92, 0.89);
            if (uIsFace > 0.5) {
              // Subtle battle bruising on right brow ridge & cheekbone (matching sheet2 f=203/257!)
              float browBruise = exp(-pow((vObjPos.x + 0.034) * 28.0, 2.0) - pow((vObjPos.y - 1.855) * 38.0, 2.0)) * smoothstep(0.06, 0.11, vObjPos.z);
              float leftBrowBruise = exp(-pow((vObjPos.x - 0.038) * 30.0, 2.0) - pow((vObjPos.y - 1.858) * 42.0, 2.0)) * smoothstep(0.06, 0.11, vObjPos.z);
              diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.62, 0.30, 0.26), clamp(browBruise * 0.62 + leftBrowBruise * 0.42, 0.0, 0.72));
            } else {
              // Weathered bruised/blood-flushed dorsal right knuckles (x < -0.50 in rest body mesh!)
              // Localised raw knuckle. Both axes MUST be closed bands — an open-ended smoothstep
              // ramps to 1.0 over the entire hand and turns the fist into a red mitten.
              float kx = smoothstep(-0.500, -0.542, vObjPos.x) * (1.0 - smoothstep(-0.588, -0.612, vObjPos.x));
              float ky = smoothstep(1.092, 1.128, vObjPos.y) * (1.0 - smoothstep(1.172, 1.205, vObjPos.y));
              float kz = smoothstep(0.120, 0.170, vObjPos.z);
              float knuckleZone = clamp(kx * ky * kz, 0.0, 1.0);
              diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.86, 0.55, 0.48), knuckleZone * 0.34);
            }
            `
          );

          shader.fragmentShader = shader.fragmentShader.replace(
            '#include <normal_fragment_maps>',
            `
            #include <normal_fragment_maps>
            #ifdef USE_NORMALMAP_TANGENTSPACE
              vec3 poreN = texture2D(uPoreNormal, vNormalMapUv * (uIsFace > 0.5 ? 22.0 : 34.0)).xyz * 2.0 - 1.0;
              normal = normalize(normal + tbn * (poreN * (uIsFace > 0.5 ? 0.28 : 0.32)));
            #endif
            `
          );

          shader.fragmentShader = shader.fragmentShader.replace(
            '#include <roughnessmap_fragment>',
            `
            float roughnessFactor = roughness;
            #ifdef USE_ROUGHNESSMAP
              roughnessFactor *= texture2D(roughnessMap, vRoughnessMapUv).g;
            #endif
            // Sweat-slicked forehead/brow/cheek/knuckle specular micro-highlights!
            roughnessFactor = clamp(max(roughnessFactor * 0.82, 0.28), 0.26, 0.72);
            `
          );
        };

        const skinClay = makeClayMat(mat.normalMap, 0.88, '#a0a4ab', 0.75);
        if (Array.isArray(obj.material)) obj.material[slotIdx] = skinRender;
        else obj.material = skinRender;
        registerSwap(obj, Array.isArray(obj.material) ? slotIdx : -1, skinClay, skinRender);
        return;
      }

      // F. Outfit (`MID_M_techwear_bodyShapeG_MH_Jacket_66` & Pants) -> Gritty Weathered Blood-Stained Linen/Chambray Workshirt!
      if (mName.includes('Jacket') || mName.includes('Pants') || mName.includes('Shoes')) {
        const isJacket = mName.includes('Jacket');
        const clothRender = new THREE.MeshPhysicalMaterial({
          map: mat.map,
          normalMap: mat.normalMap,
          normalScale: new THREE.Vector2(1.25, 1.25),
          aoMap: mat.aoMap,
          roughness: isJacket ? 0.86 : 0.90,
          metalness: 0.02,
          sheen: isJacket ? 0.35 : 0.15,
          sheenRoughness: 0.82,
          sheenColor: new THREE.Color('#cfc6be'),
          side: THREE.DoubleSide,
        });
        if (isJacket) {
          clothRender.customProgramCacheKey = () => 'logan_weathered_workshirt';
          clothRender.onBeforeCompile = (shader) => {
            shader.uniforms.uStainTex = { value: stainTex };
            shader.uniforms.uWeaveNorm = { value: weaveNormal };
            shader.fragmentShader = `
              uniform sampler2D uStainTex;
              uniform sampler2D uWeaveNorm;
            ` + shader.fragmentShader;
            shader.fragmentShader = shader.fragmentShader.replace(
              '#include <map_fragment>',
              `
              vec4 origTex = texture2D(map, vMapUv);
              // Remap techwear into deep low-key charcoal-slate / dark umber work-jacket
              // so chiaroscuro low-key contrast pops 100% on skin, knuckles & Adamantium blades!
              float origLuma = dot(origTex.rgb, vec3(0.299, 0.587, 0.114));
              float weaveVar = texture2D(uWeaveNorm, vMapUv * 36.0).x * 0.14 + 0.93;
              vec3 darkCanvas = mix(vec3(0.011, 0.013, 0.017), vec3(0.042, 0.040, 0.038), smoothstep(0.05, 0.65, origLuma));
              diffuseColor.rgb = darkCanvas * weaveVar;
              `
            );
            shader.fragmentShader = shader.fragmentShader.replace(
              '#include <normal_fragment_maps>',
              `
              #include <normal_fragment_maps>
              #ifdef USE_NORMALMAP_TANGENTSPACE
                vec3 wv = texture2D(uWeaveNorm, vNormalMapUv * 58.0).xyz * 2.0 - 1.0;
                normal = normalize(normal + tbn * (wv * 0.34));
              #endif
              `
            );
          };
        }
        const clothClay = makeClayMat(mat.normalMap, 1.0, isJacket ? '#989ca3' : '#787c82', 0.80);
        if (Array.isArray(obj.material)) obj.material[slotIdx] = clothRender;
        else obj.material = clothRender;
        registerSwap(obj, Array.isArray(obj.material) ? slotIdx : -1, clothClay, clothRender);
        return;
      }

      // G. Teeth / fallback
      const clayFallback = makeClayMat(mat.normalMap, 0.5, '#a8acb2', 0.75);
      registerSwap(obj, Array.isArray(obj.material) ? slotIdx : -1, clayFallback, mat);
    });
  });

  // Add inner opaque-alpha-clip passes for hair, beard, brows & mustache so volume is lush & shadow-casting!
  const nonSkinnedGroomMeshes = [];
  for (const { srcMesh, pair } of pendingHairCoreClones) {
    const coreClone = srcMesh.isSkinnedMesh ? srcMesh.clone() : new THREE.Mesh(srcMesh.geometry, pair.render.inner);
    if (srcMesh.isSkinnedMesh) {
      coreClone.bind(srcMesh.skeleton, srcMesh.bindMatrix);
    }
    coreClone.material = pair.render.inner;
    // Sit the opaque core just inside the strand shell so its silhouette never
    // pokes past the alpha-tested outer cards as a hard black wedge.
    coreClone.scale.multiplyScalar(0.988);
    coreClone.castShadow = true;
    coreClone.receiveShadow = true;
    coreClone.frustumCulled = false;
    coreClone.renderOrder = 4;
    srcMesh.parent.add(coreClone);
    if (coreClone.morphTargetDictionary && coreClone.morphTargetInfluences) {
      morphMeshes.push(coreClone);
    }
    registerSwap(coreClone, -1, pair.clay.inner, pair.render.inner);
    if (!srcMesh.isSkinnedMesh) {
      nonSkinnedGroomMeshes.push(srcMesh, coreClone);
    }
  }

  // Lock all non-skinned groom meshes (`Hair_S_Casual`, `Beard`, `Eyebrows`, `Mustache`) directly onto `head` bone
  // at rest pose so head pitch/yaw/breathing never lets the forehead or brow ridge clip through hair cards!
  actorRoot.updateMatrixWorld(true);
  const headList = bonesByName.get('head') || [];
  const faceHeadBone = headList[0];
  if (faceHeadBone) {
    for (const gm of nonSkinnedGroomMeshes) {
      faceHeadBone.attach(gm);
    }
  }

  // ---------------------------------------------------------------------------
  // Corneal catchlights: parented to the `head` bone so they track every head
  // pitch/yaw and the breathing bob. Positions are HEAD-BONE LOCAL, sampled at
  // rest from `FACIAL_L_Eye`/`FACIAL_R_Eye` joint centres (+0.0132 protruding
  // along the head's -Y axis, which maps to world +Z at rest).
  // MeshPhysicalMaterial nulls the specular lobe for camera-facing normals, so a
  // real key specular on a corneal sphere is structurally impossible -> emit them.
  // ---------------------------------------------------------------------------
  const catchlightSpecs = [
    { x: 0.0804, y: -0.0328, z: 0.0910 },
    { x: 0.0791, y: 0.0343, z: 0.0910 },
  ];
  const catchlightGeo = new THREE.CircleGeometry(0.0042, 16);
  const catchlightMat = new THREE.MeshBasicMaterial({
    color: new THREE.Color('#eaf6ff'),
    transparent: true,
    opacity: 0.92,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    toneMapped: false,
  });
  const catchlightMatClay = new THREE.MeshBasicMaterial({
    color: new THREE.Color('#5d6167'),
    transparent: true,
    opacity: 0.40,
    depthWrite: false,
    side: THREE.DoubleSide,
    toneMapped: false,
  });
  const catchlights = [];
  if (faceHeadBone) {
    for (const spec of catchlightSpecs) {
      const m = new THREE.Mesh(catchlightGeo, catchlightMat);
      m.position.set(spec.x, spec.y, spec.z);
      // `CircleGeometry`'s normal is +Z, and head-local +Z is world +Z (toward the lens)
      // at rest — so NO rotation. Any rotation here turns the disc edge-on and it vanishes.
      m.renderOrder = 12;
      m.frustumCulled = false;
      faceHeadBone.add(m);
      catchlights.push(m);
    }
  }

  // Repair Draco-scrambled `JOINTS_0` on `Bruce_Outfits` using exact analytical 18-bone capsule skinning
  // bound directly to `SKM_Bruce_BodyMesh001`'s clean 342-bone skeleton, AND retract covered inner-torso
  // `BodyMesh` vertices by 2.0 cm so skin never pokes through the jacket!
  let bodySkinnedMesh = null;
  const outfitSkinnedMeshes = [];
  actorRoot.traverse((o) => {
    if (!o.isSkinnedMesh) return;
    if (o.name.includes('BodyMesh')) bodySkinnedMesh = o;
    else if (o.name.includes('Outfits')) outfitSkinnedMeshes.push(o);
  });

  if (bodySkinnedMesh) {
    // 1. Retract covered inner torso/upper-sleeve skin (`y < 1.545 && |x| < 0.43`) while preserving bare neck & wrists/hands!
    const bPos = bodySkinnedMesh.geometry.attributes.position;
    const bNrm = bodySkinnedMesh.geometry.attributes.normal;
    for (let i = 0; i < bPos.count; i++) {
      const vx = bPos.getX(i);
      const vy = bPos.getY(i);
      if (vy < 1.565 && vy > 1.285 && Math.abs(vx) < 0.514) {
        bPos.setXYZ(
          i,
          vx - bNrm.getX(i) * 0.025,
          vy - bNrm.getY(i) * 0.025,
          bPos.getZ(i) - bNrm.getZ(i) * 0.025
        );
      }
    }
    bPos.needsUpdate = true;

    // 2. Build clean 18-bone rest-pose capsule segments on `bodySkinnedMesh.skeleton`
    const skel = bodySkinnedMesh.skeleton;
    const findIdx = (canon) => skel.bones.findIndex((b) => canonicalBoneName(b.name) === canon);
    const segSpecs = [
      ['pelvis', 'pelvis', 'spine_01'],
      ['spine_01', 'spine_01', 'spine_02'],
      ['spine_02', 'spine_02', 'spine_03'],
      ['spine_03', 'spine_03', 'spine_04'],
      ['spine_04', 'spine_04', 'spine_05'],
      ['spine_05', 'spine_05', 'neck_01'],
      ['neck_01',  'neck_01',  'head'],
      ['clavicle_l', 'spine_05', 'upperarm_l'],
      ['upperarm_l', 'upperarm_l', 'lowerarm_l'],
      ['lowerarm_l', 'lowerarm_l', 'hand_l'],
      ['hand_l',     'hand_l',     'middle_01_l'],
      ['clavicle_r', 'spine_05', 'upperarm_r'],
      ['upperarm_r', 'upperarm_r', 'lowerarm_r'],
      ['lowerarm_r', 'lowerarm_r', 'hand_r'],
      ['hand_r',     'hand_r',     'middle_01_r'],
      ['thigh_l',    'thigh_l',    'calf_l'],
      ['calf_l',     'calf_l',     'foot_l'],
      ['thigh_r',    'thigh_r',    'calf_r'],
      ['calf_r',     'calf_r',     'foot_r'],
    ];
    const capsules = [];
    for (const [jointCanon, aCanon, bCanon] of segSpecs) {
      const jIdx = findIdx(jointCanon);
      const aIdx = findIdx(aCanon);
      const bIdx = findIdx(bCanon);
      if (jIdx < 0 || aIdx < 0 || bIdx < 0) continue;
      const pA = skel.bones[aIdx].getWorldPosition(new THREE.Vector3());
      const pB = skel.bones[bIdx].getWorldPosition(new THREE.Vector3());
      capsules.push({ jIdx, pA, pB, ab: pB.clone().sub(pA), abLenSq: Math.max(1e-6, pB.distanceToSquared(pA)) });
    }

    const ptSegDistSq = (px, py, pz, cap) => {
      const apx = px - cap.pA.x;
      const apy = py - cap.pA.y;
      const apz = pz - cap.pA.z;
      const t = Math.max(0.0, Math.min(1.0, (apx * cap.ab.x + apy * cap.ab.y + apz * cap.ab.z) / cap.abLenSq));
      const dx = apx - cap.ab.x * t;
      const dy = apy - cap.ab.y * t;
      const dz = apz - cap.ab.z * t;
      return dx * dx + dy * dy + dz * dz;
    };

    const reweightedGeos = new Set();
    for (const om of outfitSkinnedMeshes) {
      const geo = om.geometry;
      if (!reweightedGeos.has(geo)) {
        reweightedGeos.add(geo);
        const pos = geo.attributes.position;
        const n = pos.count;
        const newIdx = new Uint16Array(n * 4);
        const newWgt = new Float32Array(n * 4);
        const dists = new Array(capsules.length);
        for (let i = 0; i < n; i++) {
          const px = pos.getX(i);
          const py = pos.getY(i);
          const pz = pos.getZ(i);
          for (let c = 0; c < capsules.length; c++) {
            dists[c] = { jIdx: capsules[c].jIdx, d2: ptSegDistSq(px, py, pz, capsules[c]) };
          }
          dists.sort((a, b) => a.d2 - b.d2);
          let wSum = 0.0;
          const w4 = [0, 0, 0, 0];
          for (let k = 0; k < 4; k++) {
            const w = 1.0 / Math.pow(dists[k].d2 + 0.040 * 0.040, 2.35);
            w4[k] = w;
            wSum += w;
          }
          for (let k = 0; k < 4; k++) {
            newIdx[i * 4 + k] = dists[k].jIdx;
            newWgt[i * 4 + k] = w4[k] / wSum;
          }
        }
        geo.setAttribute('skinIndex', new THREE.BufferAttribute(newIdx, 4));
        geo.setAttribute('skinWeight', new THREE.BufferAttribute(newWgt, 4));
      }
      om.bind(skel, bodySkinnedMesh.bindMatrix);
    }
  }

  // Native MetaHuman `Beard_M_MuttonChops` + `Mustache_S_Horseshoe` provides 100% clean classic Wolverine chops!
  const chinBeard = { setMode: () => {} };

  // 5. Attach 3 Curved Lofted Adamantium Claws + 3D NURBS Spline Rig + Golden Facial Rig Picker Board!
  const clawRig = createAdamantiumClawRig(bonesByName.get('hand_r') || []);
  const nurbsRig = createNurbsRigOverlay(bonesByName);
  const pickerBoard = createRigPickerBoard();
  scene.add(pickerBoard.mesh);

  const tmpEuler = new THREE.Euler();
  const tmpQuat = new THREE.Quaternion();

  function resetAllPose() {
    for (const [b, q0] of restQuats.entries()) {
      b.quaternion.copy(q0);
    }
    for (const m of morphMeshes) {
      m.morphTargetInfluences.fill(0);
    }
  }

  function setBoneDelta(name, rx = 0, ry = 0, rz = 0, order = 'XYZ') {
    const list = bonesByName.get(name);
    if (!list) return;
    tmpEuler.set(rx, ry, rz, order);
    tmpQuat.setFromEuler(tmpEuler);
    for (const b of list) {
      const q0 = restQuats.get(b);
      if (q0) b.quaternion.copy(q0).multiply(tmpQuat);
    }
  }

  function setMorph(name, value) {
    for (const m of morphMeshes) {
      const idx = m.morphTargetDictionary[name];
      if (idx !== undefined) {
        m.morphTargetInfluences[idx] = value;
      }
    }
  }

  let currentMode = '';
  function setRenderMode(mode) {
    if (mode !== currentMode) {
      const isClay = mode === 'viewport_clay';
      for (const sw of matSwaps) {
        const target = isClay ? sw.clayMat : sw.renderMat;
        if (sw.slotIdx >= 0) sw.mesh.material[sw.slotIdx] = target;
        else sw.mesh.material = target;
      }
      chinBeard.setMode(mode);
      for (const c of catchlights) c.material = isClay ? catchlightMatClay : catchlightMat;
      clawRig.setRenderMode(mode);
      nurbsRig.setVisible(isClay);
      pickerBoard.mesh.visible = isClay;
      currentMode = mode;
    }
  }

  function getBoneWorldPos(name, targetVec = new THREE.Vector3()) {
    const list = bonesByName.get(name);
    if (!list || list.length === 0) return targetVec.set(0, 1.5, 0);
    const b = list[list.length - 1];
    b.updateWorldMatrix(true, false);
    return b.getWorldPosition(targetVec);
  }

  return {
    actorRoot,
    bonesByName,
    catchlights,
    clawRig,
    nurbsRig,
    pickerBoard,
    resetAllPose,
    setBoneDelta,
    setMorph,
    setRenderMode,
    getBoneWorldPos,
  };
}
