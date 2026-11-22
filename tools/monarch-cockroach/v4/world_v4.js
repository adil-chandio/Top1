import * as THREE from 'three';
import { SHARED_LIGHT_UNIFORMS, setLightingMood } from './materials_v4.js';
import { createCockroachActorV4, createXrayCutawayRigV4, createCramRobotProp } from './cockroach3d_v4.js';
import { loadV4HumanActors } from './humans3d_v4.js';

/**
 * Monarch Cam #03 — V4 Complete Multi-Set 3D Cinema World + Real-Time Shadow Engine!
 * Scale: 1 Three.js world unit = 1.0 mm everywhere.
 */
export async function createMonarchWorldV4(mats, renderer) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#091318');

  const humanActors = await loadV4HumanActors(mats);

  // =========================================================================
  // HERO & MULTI-LANE 3D COCKROACH ACTORS + FULL-BODY 3D X-RAY CUTAWAY RIG
  // =========================================================================
  const roachHero = createCockroachActorV4(mats, { includeWing: true });
  const roachB    = createCockroachActorV4(mats, { includeWing: true });
  const roachC    = createCockroachActorV4(mats, { includeWing: true });
  roachB.root.visible = false;
  roachC.root.visible = false;
  scene.add(roachHero.root, roachB.root, roachC.root);

  const xrayRig = createXrayCutawayRigV4(mats);
  xrayRig.group.visible = false;
  scene.add(xrayRig.group);

  // Micro grit/dust particle kick-up InstancedMesh for macro spine strikes!
  const dustGeo = new THREE.DodecahedronGeometry(0.068, 0);
  const dustParticles = new THREE.InstancedMesh(dustGeo, mats.pennyRimMat, 48);
  dustParticles.visible = false;
  dustParticles.frustumCulled = false;
  scene.add(dustParticles);

  // =========================================================================
  // SET 1: LIVED-IN MIDNIGHT APARTMENT HALLWAY & KITCHEN
  // =========================================================================
  const apartmentSet = new THREE.Group();
  scene.add(apartmentSet);

  // Hardwood oak floor spanning kitchen (-X) through doorway (X=0) into hallway (+X)
  const aptFloor = new THREE.Mesh(new THREE.BoxGeometry(3600, 16, 2600), mats.oakFloorMat);
  aptFloor.position.set(-200, -8, 0);
  apartmentSet.add(aptFloor);

  // Hallway dividing wall at X = 22 mm with doorway cutout (Z = -420..+420, Y = 0..2060)
  const wallLeft = new THREE.Mesh(new THREE.BoxGeometry(110, 2450, 920), mats.plasterWallMat);
  wallLeft.position.set(22, 1225, -880);
  const wallRight = new THREE.Mesh(new THREE.BoxGeometry(110, 2450, 920), mats.plasterWallMat);
  wallRight.position.set(22, 1225, 880);
  const wallHeader = new THREE.Mesh(new THREE.BoxGeometry(110, 390, 840), mats.plasterWallMat);
  wallHeader.position.set(22, 2255, 0);
  // Side & rear apartment walls so ZERO empty void is ever visible in wide human shots!
  const sideWallN = new THREE.Mesh(new THREE.BoxGeometry(3600, 2450, 80), mats.plasterWallMat);
  sideWallN.position.set(-200, 1225, -1280);
  const sideWallS = new THREE.Mesh(new THREE.BoxGeometry(3600, 2450, 80), mats.plasterWallMat);
  sideWallS.position.set(-200, 1225, 1280);
  const rearKitchenWall = new THREE.Mesh(new THREE.BoxGeometry(80, 2450, 2600), mats.plasterWallMat);
  rearKitchenWall.position.set(-1960, 1225, 0);
  const aptCeiling = new THREE.Mesh(new THREE.BoxGeometry(3600, 40, 2600), mats.trimWhiteMat);
  aptCeiling.position.set(-200, 2460, 0);
  apartmentSet.add(wallLeft, wallRight, wallHeader, sideWallN, sideWallS, rearKitchenWall, aptCeiling);

  // White baseboards & door casing trim
  const baseboardL = new THREE.Mesh(new THREE.BoxGeometry(126, 95, 920), mats.trimWhiteMat);
  baseboardL.position.set(22, 47.5, -880);
  const baseboardR = new THREE.Mesh(new THREE.BoxGeometry(126, 95, 920), mats.trimWhiteMat);
  baseboardR.position.set(22, 47.5, 880);
  const casingL = new THREE.Mesh(new THREE.BoxGeometry(132, 2100, 68), mats.trimWhiteMat);
  casingL.position.set(22, 1050, -445);
  const casingR = new THREE.Mesh(new THREE.BoxGeometry(132, 2100, 68), mats.trimWhiteMat);
  casingR.position.set(22, 1050, 445);
  apartmentSet.add(baseboardL, baseboardR, casingL, casingR);

  // Raised-Panel Solid Oak Hallway Door (exact 3.20 mm clearance above floor Y = 0!)
  const doorSlab = new THREE.Group();
  const doorCore = new THREE.Mesh(new THREE.BoxGeometry(44, 2050, 820), mats.oakDoorMat);
  doorCore.position.set(22, 3.2 + 1025, 0);
  doorSlab.add(doorCore);
  // Moulded bottom rail & decorative panels visible in low macro angles!
  const bottomRail = new THREE.Mesh(new THREE.BoxGeometry(48, 165, 760), mats.oakDoorMat);
  bottomRail.position.set(22, 3.2 + 95, 0);
  doorSlab.add(bottomRail);
  for (const pz of [-195, 195]) {
    const lowerPanel = new THREE.Mesh(new THREE.BoxGeometry(52, 620, 280), mats.oakDoorMat);
    lowerPanel.position.set(22, 3.2 + 520, pz);
    const upperPanel = new THREE.Mesh(new THREE.BoxGeometry(52, 720, 280), mats.oakDoorMat);
    upperPanel.position.set(22, 3.2 + 1340, pz);
    doorSlab.add(lowerPanel, upperPanel);
  }
  // Brass door handle & escutcheon at Y = 980 mm
  const handleRose = new THREE.Mesh(new THREE.CylinderGeometry(32, 32, 8, 20), mats.brassMat);
  handleRose.rotation.z = Math.PI / 2;
  handleRose.position.set(-4, 980, 330);
  const handleLever = new THREE.Mesh(new THREE.BoxGeometry(18, 16, 115), mats.brassMat);
  handleLever.position.set(-28, 980, 290);
  doorSlab.add(handleRose, handleLever);
  apartmentSet.add(doorSlab);

  // Warm hallway light spill strip on the far side (+X > 65 mm) glowing softly under the 3.2 mm gap!
  const hallwaySpillStrip = new THREE.Mesh(
    new THREE.PlaneGeometry(240, 820),
    new THREE.MeshBasicMaterial({ color: '#ffcf8a', transparent: true, opacity: 0.42 })
  );
  hallwaySpillStrip.rotation.x = -Math.PI / 2;
  hallwaySpillStrip.position.set(145, 0.2, 0);
  apartmentSet.add(hallwaySpillStrip);

  // Working 3D Wall Light Switch Plate + Animated Toggle Lever at (-38, 1210, -560)!
  const switchGroup = new THREE.Group();
  switchGroup.position.set(-38, 1210, -560);
  const switchPlate = new THREE.Mesh(new THREE.BoxGeometry(8, 115, 72), mats.switchPlateMat);
  switchGroup.add(switchPlate);
  const switchToggle = new THREE.Mesh(new THREE.BoxGeometry(22, 24, 10), mats.switchPlateMat);
  switchToggle.position.set(-10, 0, 0);
  switchToggle.rotation.z = 0.42; // Starts flipped DOWN (lights off!)
  switchGroup.add(switchToggle);
  apartmentSet.add(switchGroup);

  // Kitchen Background Furniture & Lived-In Props (gives gorgeous depth-of-field parallax!)
  const runnerRug = new THREE.Mesh(new THREE.BoxGeometry(1150, 4.5, 680), mats.rugMat);
  runnerRug.position.set(-980, 2.25, 180);
  const kitchenCounter = new THREE.Mesh(new THREE.BoxGeometry(620, 880, 1450), mats.cabinetMat);
  kitchenCounter.position.set(-1620, 440, -520);
  const counterTop = new THREE.Mesh(new THREE.BoxGeometry(650, 36, 1480), mats.oakDoorMat);
  counterTop.position.set(-1610, 898, -520);
  const fridge = new THREE.Mesh(new THREE.BoxGeometry(680, 1820, 760), mats.steelBrushedMat);
  fridge.position.set(-1600, 910, 620);
  // Glowing 2:14 AM digital microwave clock in dark kitchen background!
  const clockGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(78, 32),
    new THREE.MeshBasicMaterial({ color: '#6ef2e8' })
  );
  clockGlow.rotation.y = Math.PI / 2;
  clockGlow.position.set(-1282, 1040, -480);
  const microwaveBody = new THREE.Mesh(new THREE.BoxGeometry(360, 260, 520), mats.anodizedBlackMat);
  microwaveBody.position.set(-1465, 1045, -480);
  // Potted hallway plant
  const potMesh = new THREE.Mesh(new THREE.CylinderGeometry(135, 105, 260, 18), mats.tergiteMat);
  potMesh.position.set(-220, 130, 680);
  apartmentSet.add(runnerRug, kitchenCounter, counterTop, fridge, microwaveBody, clockGlow, potMesh);

  // Two Stacked Minted US Lincoln Pennies (19.05 mm diameter x 1.52 mm thick = 3.04 mm total!)
  const penniesGroup = new THREE.Group();
  const pennyCylGeo = new THREE.CylinderGeometry(9.525, 9.525, 1.52, 48);
  // CylinderGeometry material groups: [0 = side rim, 1 = top face (Lincoln!), 2 = bottom face]
  const pennyMats = [mats.pennyRimMat, mats.pennyFaceMat, mats.pennyRimMat];
  const pennyBottom = new THREE.Mesh(pennyCylGeo, pennyMats);
  pennyBottom.position.set(0, 0.76, 0);
  const pennyTop = new THREE.Mesh(pennyCylGeo, pennyMats);
  pennyTop.position.set(0.38, 2.28, -0.24);
  pennyTop.rotation.y = 0.65;
  penniesGroup.add(pennyBottom, pennyTop);
  penniesGroup.position.set(-22.0, 0.0, -16.5);
  apartmentSet.add(penniesGroup);

  // Place Rigged 3D Homeowner beside the wall light switch!
  humanActors.homeowner.root.position.set(-540, 0, -760);
  humanActors.homeowner.root.rotation.y = -0.38; // Facing toward switch (+X/+Z) & doorway!
  apartmentSet.add(humanActors.homeowner.root);

  // =========================================================================
  // SET 2: UC BERKELEY INTEGRATIVE BIOLOGY BIOMECHANICS LABORATORY
  // =========================================================================
  const labSet = new THREE.Group();
  labSet.visible = false;
  scene.add(labSet);

  // Optical Breadboard Table Surface at Y = 0 (spanning 900 mm x 560 mm)
  const breadboard = new THREE.Mesh(new THREE.BoxGeometry(920, 28, 560), mats.breadboardMat);
  breadboard.position.set(0, -14, 0);
  labSet.add(breadboard);

  // Anodized 80/20 aluminum extrusion rails framing the corridor
  for (const rz of [-185, 185]) {
    const rail = new THREE.Mesh(new THREE.BoxGeometry(860, 14, 18), mats.steelBrushedMat);
    rail.position.set(0, 7, rz);
    labSet.add(rail);
  }

  // Laboratory Rear & Side Walls + Shelving so every lab angle has grounded scientific depth!
  const labRearWall = new THREE.Mesh(new THREE.BoxGeometry(2800, 1800, 60), mats.labWallMat);
  labRearWall.position.set(0, 420, -760);
  const labLeftWall = new THREE.Mesh(new THREE.BoxGeometry(60, 1800, 2000), mats.labWallMat);
  labLeftWall.position.set(-1380, 420, 0);
  const labRightWall = new THREE.Mesh(new THREE.BoxGeometry(60, 1800, 2000), mats.labWallMat);
  labRightWall.position.set(1380, 420, 0);
  labSet.add(labRearWall, labLeftWall, labRightWall);

  // Dual Glowing UC Berkeley Telemetry LCD Monitors on articulated stand behind bench!
  for (const mx of [-260, 240]) {
    const monGroup = new THREE.Group();
    monGroup.position.set(mx, 145, -245);
    monGroup.rotation.y = mx < 0 ? 0.22 : -0.22;
    const bezel = new THREE.Mesh(new THREE.BoxGeometry(235, 150, 10), mats.anodizedBlackMat);
    const screen = new THREE.Mesh(new THREE.PlaneGeometry(218, 134), mats.screenGlowMat);
    screen.position.z = 5.5;
    const stand = new THREE.Mesh(new THREE.CylinderGeometry(8, 11, 150, 14), mats.steelBrushedMat);
    stand.position.set(0, -85, -4);
    monGroup.add(bezel, screen, stand);
    labSet.add(monGroup);
  }

  // Phantom 500 FPS High-Speed Cinema Camera on Geared Macro Rail!
  const phantomCam = new THREE.Group();
  const camBody = new THREE.Mesh(new THREE.BoxGeometry(64, 58, 86), mats.anodizedBlackMat);
  const lensBarrel = new THREE.Mesh(new THREE.CylinderGeometry(19, 22, 68, 24), mats.steelBrushedMat);
  lensBarrel.rotation.x = Math.PI / 2;
  lensBarrel.position.z = 68;
  const frontGlass = new THREE.Mesh(new THREE.CylinderGeometry(17, 17, 3, 24), mats.acrylicEdgeMat);
  frontGlass.rotation.x = Math.PI / 2;
  frontGlass.position.z = 102;
  const recLed = new THREE.Mesh(new THREE.SphereGeometry(2.8, 10, 10), new THREE.MeshBasicMaterial({ color: '#ff3b30' }));
  recLed.position.set(24, 21, 44);
  phantomCam.add(camBody, lensBarrel, frontGlass, recLed);
  phantomCam.position.set(-45, 36, -155);
  phantomCam.rotation.y = 0.24;
  labSet.add(phantomCam);

  // Biomimetic CRAM Soft-Shell Robot Prototype resting on right corner of optical bench!
  const cramProp = createCramRobotProp(mats);
  cramProp.position.set(175, 0, -135);
  cramProp.rotation.y = -0.45;
  labSet.add(cramProp);

  // UC Berkeley Researcher in White Lab Coat, Glasses & Cyan Nitrile Gloves behind bench!
  humanActors.researcher.root.position.set(30, -1085, -415);
  humanActors.researcher.root.rotation.y = -Math.PI / 2; // +X forward -> rotated -90 deg around Y faces +Z (toward bench & camera)!
  labSet.add(humanActors.researcher.root);

  // Precision Motorized Micrometer Ceiling Rig + Crystal-Clear Anti-Ghosting Acrylic Corridor!
  const corridorGroup = new THREE.Group();
  labSet.add(corridorGroup);

  // Active corridor floor strip (switches between clear acrylic, 100-grit, 40-grit, 20-grit!)
  const labFloorStrip = new THREE.Mesh(new THREE.BoxGeometry(380, 2.0, 96), mats.grit40Mat);
  labFloorStrip.position.set(0, -1.0, 0);
  corridorGroup.add(labFloorStrip);

  // Adjustable Crystal-Clear Acrylic Ceiling Slab (0.10 top opacity + crisp cyan edge bevel!)
  const ceilingSlab = new THREE.Group();
  const roofTopPane = new THREE.Mesh(new THREE.BoxGeometry(320, 1.4, 58), mats.acrylicClearMat);
  roofTopPane.position.y = 0.7;
  // Crisp polished front & back cyan glass edges so ceiling height is unmistakably readable without washing out the cockroach!
  const frontGlassEdge = new THREE.Mesh(new THREE.BoxGeometry(320, 1.5, 1.6), mats.acrylicEdgeMat);
  frontGlassEdge.position.set(0, 0.75, 29.0);
  const backGlassEdge = new THREE.Mesh(new THREE.BoxGeometry(320, 1.5, 1.6), mats.acrylicEdgeMat);
  backGlassEdge.position.set(0, 0.75, -29.0);
  ceilingSlab.add(roofTopPane, frontGlassEdge, backGlassEdge);
  corridorGroup.add(ceilingSlab);

  // Precision Micrometer Vernier Actuator Bridge straddling the corridor!
  const micrometerBridge = new THREE.Group();
  for (const pz of [-42, 42]) {
    const post = new THREE.Mesh(new THREE.CylinderGeometry(3.8, 3.8, 56, 16), mats.steelBrushedMat);
    post.position.set(0, 28, pz);
    micrometerBridge.add(post);
    // Engraved millimeter scale ticks (3.2, 4, 6, 9, 12 mm) on front post!
    if (pz > 0) {
      for (const hTick of [3.2, 4.0, 6.0, 9.0, 12.0]) {
        const tick = new THREE.Mesh(new THREE.BoxGeometry(4.5, 0.35, 1.2), mats.brassMat);
        tick.position.set(0, hTick, pz + 3.6);
        micrometerBridge.add(tick);
      }
    }
  }
  const crossBar = new THREE.Mesh(new THREE.BoxGeometry(16, 6, 98), mats.anodizedBlackMat);
  crossBar.position.set(0, 54, 0);
  const micrometerDrum = new THREE.Mesh(new THREE.CylinderGeometry(7.5, 7.5, 22, 24), mats.brassMat);
  micrometerDrum.position.set(0, 68, 0);
  micrometerBridge.add(crossBar, micrometerDrum);
  corridorGroup.add(micrometerBridge);

  // Narrowing Acrylic Crevice Gate (for Scene 02 500fps 5-move traversal & Scene 06 315-trial gate!)
  const labGateGroup = new THREE.Group();
  const gateBlade = new THREE.Mesh(new THREE.BoxGeometry(16.0, 48.0, 74.0), mats.acrylicEdgeMat);
  gateBlade.position.set(8.0, 24.0, 0);
  const gateSteelClamp = new THREE.Mesh(new THREE.BoxGeometry(20.0, 10.0, 78.0), mats.steelBrushedMat);
  gateSteelClamp.position.set(8.0, 49.0, 0);
  labGateGroup.add(gateBlade, gateSteelClamp);
  labGateGroup.visible = false;
  labSet.add(labGateGroup);

  // 3-Lane Simultaneous Comparison Arena (Height Race in Ch03 & Grit Trade-off Race in Ch05!)
  const multiLaneGroup = new THREE.Group();
  multiLaneGroup.visible = false;
  const laneOffsetsZ = [-38, 0, 38];
  const laneFloors = laneOffsetsZ.map((lz) => {
    const fl = new THREE.Mesh(new THREE.BoxGeometry(340, 2.0, 30), mats.grit40Mat);
    fl.position.set(0, -1.0, lz);
    multiLaneGroup.add(fl);
    return fl;
  });
  const laneRoofs = laneOffsetsZ.map((lz) => {
    const rg = new THREE.Group();
    const top = new THREE.Mesh(new THREE.BoxGeometry(320, 1.2, 30), mats.acrylicClearMat);
    top.position.y = 0.6;
    const edge = new THREE.Mesh(new THREE.BoxGeometry(320, 1.3, 1.4), mats.acrylicEdgeMat);
    edge.position.set(0, 0.65, 15.0);
    rg.add(top, edge);
    rg.position.set(0, 12.0, lz);
    multiLaneGroup.add(rg);
    return rg;
  });
  // Low 1.4mm anodized brass lane guide strips (never blocking view of adjacent cockroaches!)
  for (const dz of [-19, 19]) {
    const div = new THREE.Mesh(new THREE.BoxGeometry(320, 1.4, 1.2), mats.brassMat);
    div.position.set(0, 0.7, dz);
    multiLaneGroup.add(div);
  }
  labSet.add(multiLaneGroup);

  // =========================================================================
  // SET 3: ZACK-D HUMAN PUSH-UP BIOMECHANICS FORCE-PLATE STAGE (CH04)
  // =========================================================================
  const pushupSet = new THREE.Group();
  pushupSet.visible = false;
  scene.add(pushupSet);

  const gymFloor = new THREE.Mesh(new THREE.BoxGeometry(5200, 24, 4200), mats.breadboardMat);
  gymFloor.position.set(0, -12, 0);
  pushupSet.add(gymFloor);

  // Glowing cyan biomechanics metric grid on the force plate
  const gridHelper = new THREE.GridHelper(3600, 18, 0x5cd6de, 0x1c3d46);
  gridHelper.position.y = 1.5;
  pushupSet.add(gridHelper);

  // Place Rigged 3D Athlete in prone horizontal push-up plank (+X chest facing -Y floor!)
  const athletePivot = new THREE.Group();
  humanActors.athlete.root.rotation.set(0, 0, -Math.PI / 2);
  athletePivot.add(humanActors.athlete.root);
  pushupSet.add(athletePivot);

  // Glowing 3D Ground-Reaction Force Vectors at Left & Right Hands!
  const pushupVectors = new THREE.Group();
  const vecMatGreen = new THREE.MeshBasicMaterial({ color: '#6ef29c' });
  const vecMatAmber = new THREE.MeshBasicMaterial({ color: '#ffb454' });
  const handArrows = [-1, 1].map((s) => {
    const g = new THREE.Group();
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(14, 14, 340, 12), vecMatGreen);
    shaft.position.y = 170;
    const tip = new THREE.Mesh(new THREE.ConeGeometry(36, 90, 14), vecMatGreen);
    tip.position.y = 360;
    g.add(shaft, tip);
    g.position.set(420, 0, s * 320);
    pushupVectors.add(g);
    return { group: g, shaft, tip, side: s };
  });
  pushupSet.add(pushupVectors);

  // =========================================================================
  // REAL-TIME 512x512 ORTHOGRAPHIC 5-TAP PCF SHADOW MAP PASS (FAST SWIFTSHADER!)
  // =========================================================================
  const shadowRT = new THREE.WebGLRenderTarget(512, 512, {
    minFilter: THREE.NearestFilter,
    magFilter: THREE.NearestFilter,
    format: THREE.RGBAFormat,
    type: THREE.UnsignedByteType,
  });
  const shadowDepthMat = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  const shadowCam = new THREE.OrthographicCamera(-60, 60, 60, -60, 1.0, 4200.0);
  const biasMatrix = new THREE.Matrix4().set(
    0.5, 0.0, 0.0, 0.5,
    0.0, 0.5, 0.0, 0.5,
    0.0, 0.0, 0.5, 0.5,
    0.0, 0.0, 0.0, 1.0
  );

  let shadowCallCount = 0;
  function updateShadowMap(focusCenter, frustumHalf = 65.0) {
    shadowCallCount++;
    // At 30fps, refreshing the soft orthographic shadow map every 2nd frame (or on large span jumps) is 100% seamless!
    if ((shadowCallCount & 1) === 0 && Math.abs(shadowCam.right - frustumHalf) < 25.0) {
      return;
    }
    const keyDir = SHARED_LIGHT_UNIFORMS.uKeyDir.value;
    const dist = Math.max(160.0, frustumHalf * 3.2);
    shadowCam.left   = -frustumHalf;
    shadowCam.right  =  frustumHalf;
    shadowCam.top    =  frustumHalf;
    shadowCam.bottom = -frustumHalf;
    shadowCam.near   =  dist * 0.12;
    shadowCam.far    =  dist * 2.8;
    shadowCam.position.copy(focusCenter).addScaledVector(keyDir, dist);
    shadowCam.lookAt(focusCenter);
    shadowCam.updateProjectionMatrix();
    shadowCam.updateMatrixWorld(true);

    // Temporarily hide transparent glass slabs (and off-frustum 25k-tri human meshes on tight macro shots!) during depth pass!
    const prevCeil = ceilingSlab.visible;
    const prevMulti = laneRoofs[0].visible;
    const prevHome = humanActors.homeowner.root.visible;
    const prevRes  = humanActors.researcher.root.visible;
    ceilingSlab.visible = false;
    laneRoofs.forEach((r) => { r.visible = false; });
    if (frustumHalf < 180.0) {
      humanActors.homeowner.root.visible = false;
      humanActors.researcher.root.visible = false;
    }

    const prevOverride = scene.overrideMaterial;
    const prevTarget = renderer.getRenderTarget();
    scene.overrideMaterial = shadowDepthMat;
    renderer.setRenderTarget(shadowRT);
    renderer.clear();
    renderer.render(scene, shadowCam);
    renderer.setRenderTarget(prevTarget);
    scene.overrideMaterial = prevOverride;

    ceilingSlab.visible = prevCeil;
    laneRoofs.forEach((r) => { r.visible = prevMulti; });
    humanActors.homeowner.root.visible = prevHome;
    humanActors.researcher.root.visible = prevRes;

    SHARED_LIGHT_UNIFORMS.uShadowTex.value = shadowRT.texture;
    SHARED_LIGHT_UNIFORMS.uShadowMatrix.value
      .copy(shadowCam.projectionMatrix)
      .multiply(shadowCam.matrixWorldInverse);
  }

  return {
    scene,
    mats,
    humanActors,
    roachHero,
    roachB,
    roachC,
    xrayRig,
    dustParticles,
    apartmentSet,
    doorSlab,
    switchToggle,
    penniesGroup,
    labSet,
    corridorGroup,
    labFloorStrip,
    ceilingSlab,
    micrometerBridge,
    micrometerDrum,
    labGateGroup,
    multiLaneGroup,
    laneFloors,
    laneRoofs,
    phantomCam,
    cramProp,
    pushupSet,
    athletePivot,
    handArrows,
    vecMatGreen,
    vecMatAmber,
    setLightingMood,
    updateShadowMap,
  };
}

/**
 * V4 Optical Cinema Post-Processing Pass:
 * Macro Depth-of-Field Bokeh + Subtle Chromatic Edge Polish + Cinema Vignette + Film Grain!
 */
export function createOpticalLensPassV4(renderer, width, height) {
  const rt = new THREE.WebGLRenderTarget(width, height, {
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
    format: THREE.RGBAFormat,
    depthBuffer: true,
    depthTexture: new THREE.DepthTexture(width, height, THREE.UnsignedIntType),
  });

  const postScene = new THREE.Scene();
  const postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  const postMat = new THREE.ShaderMaterial({
    uniforms: {
      tColor:    { value: rt.texture },
      tDepth:    { value: rt.depthTexture },
      uRes:      { value: new THREE.Vector2(width, height) },
      uFocusDist:{ value: 42.0 },
      uDofRange: { value: 36.0 },
      uMaxBlur:  { value: 3.2 },
      uNear:     { value: 1.0 },
      uFar:      { value: 6500.0 },
      uTime:     { value: 0.0 },
    },
    vertexShader: `
      varying vec2 vUv;
      void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }
    `,
    fragmentShader: `
      uniform sampler2D tColor;
      uniform sampler2D tDepth;
      uniform vec2 uRes;
      uniform float uFocusDist;
      uniform float uDofRange;
      uniform float uMaxBlur;
      uniform float uNear;
      uniform float uFar;
      uniform float uTime;
      varying vec2 vUv;

      float linearizeDepth(float d) {
        float z = d * 2.0 - 1.0;
        return (2.0 * uNear * uFar) / max(0.0001, (uFar + uNear - z * (uFar - uNear)));
      }

      void main() {
        float rawD = texture2D(tDepth, vUv).r;
        float linD = linearizeDepth(rawD);
        float coc = clamp(abs(linD - uFocusDist) / max(1.0, uDofRange), 0.0, 1.0) * uMaxBlur;
        vec2 texel = coc / uRes;

        // Fast 5-tap Golden-Cross Bokeh disc kernel
        vec3 col = texture2D(tColor, vUv).rgb * 0.36;
        col += texture2D(tColor, vUv + vec2( 0.85,  0.52) * texel).rgb * 0.16;
        col += texture2D(tColor, vUv + vec2(-0.74,  0.67) * texel).rgb * 0.16;
        col += texture2D(tColor, vUv + vec2(-0.52, -0.84) * texel).rgb * 0.16;
        col += texture2D(tColor, vUv + vec2( 0.64, -0.44) * texel).rgb * 0.16;

        // Subtle cinema S-curve contrast + delicate optical vignette
        vec2 centered = vUv - 0.5;
        float vig = 1.0 - dot(centered, centered) * 0.34;
        col *= vig;
        col = clamp(col * (1.04 - 0.04 * col), 0.0, 1.0);

        // Fast sin-free cinema grain so dark gradients never band in H.264!
        float grain = fract(dot(vUv + fract(uTime * 0.13), vec2(129.898, 782.33))) - 0.5;
        col += grain * (1.6 / 255.0);

        gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
      }
    `,
    depthWrite: false,
    depthTest: false,
  });

  postScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), postMat));

  function render(scene, camera, params = {}) {
    postMat.uniforms.uFocusDist.value = params.focusDist ?? 45.0;
    postMat.uniforms.uDofRange.value  = params.dofRange ?? 40.0;
    postMat.uniforms.uMaxBlur.value   = params.maxBlur ?? 2.8;
    postMat.uniforms.uNear.value      = camera.near;
    postMat.uniforms.uFar.value       = camera.far;
    postMat.uniforms.uTime.value      = params.time ?? 0.0;

    renderer.setRenderTarget(rt);
    renderer.clear();
    renderer.render(scene, camera);
    renderer.setRenderTarget(null);
    renderer.render(postScene, postCam);
  }

  return { render, rt };
}
