import * as THREE from 'three';
import { SHARED_LIGHT_UNIFORMS, setLightingMood } from './materials_v5.js';
import {
  createCockroachActorV5,
  createXrayCutawayRigV5,
  createAnimatedCramRobotV5,
} from './cockroach3d_v5.js';
import { loadV5HumanActors } from './humans3d_v5.js';

/**
 * Monarch Cam #03 — V5 Next-Level Multi-Set 3D Cinema World + 30Hz Texel-Snapped Shadow Engine!
 * Scale: 1 Three.js world unit = 1.0 mm everywhere.
 * Eliminates 100% of V4 coplanar Z-fighting, transparent depth-sort flips, and 15Hz shadow jitter!
 */
export async function createMonarchWorldV5(mats, renderer) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#091115');

  const humanActors = await loadV5HumanActors(mats);

  // =========================================================================
  // HERO & MULTI-LANE 3D COCKROACH ACTORS + X-RAY RIG + ANIMATED CRAM ROBOT
  // =========================================================================
  const roachHero = createCockroachActorV5(mats, { includeWing: true });
  const roachB    = createCockroachActorV5(mats, { includeWing: true });
  const roachC    = createCockroachActorV5(mats, { includeWing: true });
  roachB.root.visible = false;
  roachC.root.visible = false;
  scene.add(roachHero.root, roachB.root, roachC.root);

  const xrayRig = createXrayCutawayRigV5(mats);
  xrayRig.group.visible = false;
  scene.add(xrayRig.group);

  const cramActor = createAnimatedCramRobotV5(mats);
  cramActor.root.visible = false;
  scene.add(cramActor.root);

  // Micro silicon-carbide grit/dust kick-up InstancedMesh for macro crampon strikes!
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

  const aptFloor = new THREE.Mesh(new THREE.BoxGeometry(3800, 18, 2600), mats.oakFloorMat);
  aptFloor.position.set(-200, -9.0, 0); // Top strictly at Y = 0.000
  apartmentSet.add(aptFloor);

  const wallLeft = new THREE.Mesh(new THREE.BoxGeometry(110, 2450, 920), mats.plasterWallMat);
  wallLeft.position.set(22, 1225, -880);
  const wallRight = new THREE.Mesh(new THREE.BoxGeometry(110, 2450, 920), mats.plasterWallMat);
  wallRight.position.set(22, 1225, 880);
  const wallHeader = new THREE.Mesh(new THREE.BoxGeometry(110, 390, 840), mats.plasterWallMat);
  wallHeader.position.set(22, 2255, 0);
  const sideWallN = new THREE.Mesh(new THREE.BoxGeometry(3800, 2450, 80), mats.plasterWallMat);
  sideWallN.position.set(-200, 1225, -1280);
  const sideWallS = new THREE.Mesh(new THREE.BoxGeometry(3800, 2450, 80), mats.plasterWallMat);
  sideWallS.position.set(-200, 1225, 1280);
  const rearKitchenWall = new THREE.Mesh(new THREE.BoxGeometry(80, 2450, 2600), mats.plasterWallMat);
  rearKitchenWall.position.set(-1980, 1225, 0);
  const farHallwayWall = new THREE.Mesh(new THREE.BoxGeometry(80, 2450, 2600), mats.plasterWallMat);
  farHallwayWall.position.set(1580, 1225, 0);
  const aptCeiling = new THREE.Mesh(new THREE.BoxGeometry(3800, 40, 2600), mats.trimWhiteMat);
  aptCeiling.position.set(-200, 2465, 0);
  apartmentSet.add(wallLeft, wallRight, wallHeader, sideWallN, sideWallS, rearKitchenWall, farHallwayWall, aptCeiling);

  const baseboardL = new THREE.Mesh(new THREE.BoxGeometry(126, 95, 916), mats.trimWhiteMat);
  baseboardL.position.set(22, 48.0, -880);
  const baseboardR = new THREE.Mesh(new THREE.BoxGeometry(126, 95, 916), mats.trimWhiteMat);
  baseboardR.position.set(22, 48.0, 880);
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
  const handleRose = new THREE.Mesh(new THREE.CylinderGeometry(32, 32, 8, 20), mats.brassMat);
  handleRose.rotation.z = Math.PI / 2;
  handleRose.position.set(-4, 980, 330);
  const handleLever = new THREE.Mesh(new THREE.BoxGeometry(18, 16, 115), mats.brassMat);
  handleLever.position.set(-28, 980, 290);
  doorSlab.add(handleRose, handleLever);
  apartmentSet.add(doorSlab);

  // Warm golden hallway light spill strip under & beyond the 3.2 mm door slot (depthWrite=false, Y = +0.18 mm!)
  const hallwaySpillStrip = new THREE.Mesh(
    new THREE.PlaneGeometry(320, 800),
    new THREE.MeshBasicMaterial({ color: '#ffd08e', transparent: true, opacity: 0.38, depthWrite: false })
  );
  hallwaySpillStrip.rotation.x = -Math.PI / 2;
  hallwaySpillStrip.position.set(130, 0.18, 0);
  hallwaySpillStrip.renderOrder = 1;
  apartmentSet.add(hallwaySpillStrip);

  // Working 3D Wall Light Switch Plate + Animated Toggle Lever at (-38, 1210, -560)!
  const switchGroup = new THREE.Group();
  switchGroup.position.set(-38, 1210, -560);
  const switchPlate = new THREE.Mesh(new THREE.BoxGeometry(8, 115, 72), mats.switchPlateMat);
  switchGroup.add(switchPlate);
  const switchToggle = new THREE.Mesh(new THREE.BoxGeometry(22, 24, 10), mats.switchPlateMat);
  switchToggle.position.set(-10, 0, 0);
  switchToggle.rotation.z = 0.42;
  switchGroup.add(switchToggle);
  apartmentSet.add(switchGroup);

  // Kitchen Background Furniture & Lived-In Props
  const runnerRug = new THREE.Mesh(new THREE.BoxGeometry(1150, 4.5, 680), mats.rugMat);
  runnerRug.position.set(-1020, 2.5, 220);
  const kitchenCounter = new THREE.Mesh(new THREE.BoxGeometry(620, 880, 1450), mats.cabinetMat);
  kitchenCounter.position.set(-1640, 440, -520);
  const counterTop = new THREE.Mesh(new THREE.BoxGeometry(650, 36, 1480), mats.oakDoorMat);
  counterTop.position.set(-1630, 898, -520);
  const fridge = new THREE.Mesh(new THREE.BoxGeometry(680, 1820, 760), mats.steelBrushedMat);
  fridge.position.set(-1620, 910, 620);
  const clockGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(78, 32),
    new THREE.MeshBasicMaterial({ color: '#6ef2e8' })
  );
  clockGlow.rotation.y = Math.PI / 2;
  clockGlow.position.set(-1298, 1040, -480);
  const microwaveBody = new THREE.Mesh(new THREE.BoxGeometry(360, 260, 520), mats.anodizedBlackMat);
  microwaveBody.position.set(-1482, 1045, -480);
  const potMesh = new THREE.Mesh(new THREE.CylinderGeometry(135, 105, 260, 18), mats.tergiteMat);
  potMesh.position.set(-260, 130, 690);
  apartmentSet.add(runnerRug, kitchenCounter, counterTop, fridge, microwaveBody, clockGlow, potMesh);

  // Two Stacked Minted US Lincoln Pennies (19.05 mm diameter x 1.52 mm thick = 3.04 mm total!)
  // Placed right beside the doorway approach path (-18, 0, 18) so BOTH pennies & squeezing cockroach frame together!
  const penniesGroup = new THREE.Group();
  const pennyCylGeo = new THREE.CylinderGeometry(9.525, 9.525, 1.52, 48);
  const pennyMats = [mats.pennyRimMat, mats.pennyFaceMat, mats.pennyRimMat];
  const pennyBottom = new THREE.Mesh(pennyCylGeo, pennyMats);
  pennyBottom.position.set(0, 0.77, 0);
  const pennyTop = new THREE.Mesh(pennyCylGeo, pennyMats);
  pennyTop.position.set(0.42, 2.30, -0.26);
  pennyTop.rotation.y = 0.65;
  pennyBottom.castShadow = true;
  pennyTop.castShadow = true;
  penniesGroup.add(pennyBottom, pennyTop);
  penniesGroup.position.set(-24.0, 0.0, -17.5);
  apartmentSet.add(penniesGroup);

  // Place Rigged 3D Homeowner ergonomically in front of wall switch (-38, 1210, -560)
  humanActors.homeowner.root.position.set(-360, 0, -650);
  humanActors.homeowner.root.rotation.y = -0.28;
  apartmentSet.add(humanActors.homeowner.root);

  // =========================================================================
  // SET 2: UC BERKELEY POLY-PEDAL BIOMECHANICS LABORATORY (1.88 M CONTINUOUS BENCH!)
  // =========================================================================
  const labSet = new THREE.Group();
  labSet.visible = false;
  scene.add(labSet);

  // STRICT PHYSICAL Y-HIERARCHY (ZERO COPLANAR SURFACES ANYWHERE!):
  //   1. Optical Breadboard Top       = -3.20 mm
  //   2. Aluminum Carrier Base Top    = -1.40 mm
  //   3. Active Grit Runway Strip Top =  0.00 mm
  const breadboard = new THREE.Mesh(new THREE.BoxGeometry(2400, 32, 980), mats.breadboardMat);
  breadboard.position.set(0, -19.2, 0); // Top strictly at Y = -3.20 mm!
  labSet.add(breadboard);

  // Anodized 80/20 aluminum extrusion side rails along optical table
  for (const rz of [-210, 210]) {
    const rail = new THREE.Mesh(new THREE.BoxGeometry(2100, 14, 20), mats.steelBrushedMat);
    rail.position.set(0, 3.8, rz); // Bottom at -3.20 mm (sits cleanly on breadboard!)
    labSet.add(rail);
  }

  // Laboratory Architectural Enclosure + Shelving
  const labRearWall = new THREE.Mesh(new THREE.BoxGeometry(3600, 2000, 60), mats.labWallMat);
  labRearWall.position.set(0, 480, -960);
  const labLeftWall = new THREE.Mesh(new THREE.BoxGeometry(60, 2000, 2400), mats.labWallMat);
  labLeftWall.position.set(-1780, 480, 0);
  const labRightWall = new THREE.Mesh(new THREE.BoxGeometry(60, 2000, 2400), mats.labWallMat);
  labRightWall.position.set(1780, 480, 0);
  labSet.add(labRearWall, labLeftWall, labRightWall);

  // Dual Glowing UC Berkeley DAQ Telemetry LCD Monitors on back instrumentation rack (Z = -420 mm)
  for (const mx of [-320, 300]) {
    const monGroup = new THREE.Group();
    monGroup.position.set(mx, 175, -420);
    monGroup.rotation.y = mx < 0 ? 0.20 : -0.20;
    const bezel = new THREE.Mesh(new THREE.BoxGeometry(280, 176, 12), mats.anodizedBlackMat);
    const screen = new THREE.Mesh(new THREE.PlaneGeometry(260, 156), mats.screenGlowMat);
    screen.position.z = 6.5;
    const stand = new THREE.Mesh(new THREE.CylinderGeometry(9, 13, 185, 14), mats.steelBrushedMat);
    stand.position.set(0, -102, -5);
    monGroup.add(bezel, screen, stand);
    labSet.add(monGroup);
  }

  // Phantom v2512 500 FPS High-Speed Camera on Geared Macro Rail!
  const phantomCam = new THREE.Group();
  const camBody = new THREE.Mesh(new THREE.BoxGeometry(68, 62, 92), mats.anodizedBlackMat);
  const lensBarrel = new THREE.Mesh(new THREE.CylinderGeometry(20, 23, 72, 24), mats.steelBrushedMat);
  lensBarrel.rotation.x = Math.PI / 2;
  lensBarrel.position.z = 72;
  const frontGlass = new THREE.Mesh(new THREE.CylinderGeometry(18, 18, 3, 24), mats.acrylicEdgeMat);
  frontGlass.rotation.x = Math.PI / 2;
  frontGlass.position.z = 109;
  frontGlass.renderOrder = 14;
  const recLed = new THREE.Mesh(new THREE.SphereGeometry(2.8, 10, 10), new THREE.MeshBasicMaterial({ color: '#ff3b30' }));
  recLed.position.set(25, 22, 47);
  phantomCam.add(camBody, lensBarrel, frontGlass, recLed);
  phantomCam.position.set(-55, 34, -225);
  phantomCam.rotation.y = 0.22;
  labSet.add(phantomCam);

  // Dual Fiber-Optic Gooseneck Cold-Light Macro Illuminators aimed at corridor!
  for (const gx of [-220, 220]) {
    const goose = new THREE.Group();
    const base = new THREE.Mesh(new THREE.CylinderGeometry(18, 20, 16, 16), mats.anodizedBlackMat);
    base.position.set(gx, 4.8, -175);
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(gx, 12, -175),
      new THREE.Vector3(gx * 0.92, 92, -145),
      new THREE.Vector3(gx * 0.78, 78, -75),
    ]);
    const neck = new THREE.Mesh(new THREE.TubeGeometry(curve, 18, 4.2, 10, false), mats.steelBrushedMat);
    const tip = new THREE.Mesh(
      new THREE.SphereGeometry(6.5, 12, 12),
      new THREE.MeshBasicMaterial({ color: '#fff5df' })
    );
    tip.position.set(gx * 0.78, 76, -72);
    goose.add(base, neck, tip);
    labSet.add(goose);
  }

  // Stereo Dissecting Microscope prop on left side of optical table
  const scopeGroup = new THREE.Group();
  scopeGroup.position.set(-480, -3.2, -165);
  const scopePillar = new THREE.Mesh(new THREE.CylinderGeometry(7, 7, 155, 14), mats.steelBrushedMat);
  scopePillar.position.y = 77.5;
  const scopeHead = new THREE.Mesh(new THREE.BoxGeometry(44, 52, 58), mats.trimWhiteMat);
  scopeHead.position.set(0, 118, 22);
  scopeHead.rotation.x = 0.35;
  scopeGroup.add(scopePillar, scopeHead);
  labSet.add(scopeGroup);

  // Static CRAM Soft-Robot bench prop on far right corner (hidden when animated cramActor is center-stage!)
  const cramBenchProp = createAnimatedCramRobotV5(mats);
  cramBenchProp.update({ worldX: 340, worldZ: -155, yaw: -0.45, compAlpha: 0.0 });
  cramBenchProp.root.position.y = -3.2;
  labSet.add(cramBenchProp.root);

  // UC Berkeley Researcher standing at realistic ergonomic distance behind optical bench (Z = -680 mm)!
  humanActors.researcher.root.position.set(-90, -1065, -680);
  humanActors.researcher.root.rotation.y = -Math.PI / 2;
  labSet.add(humanActors.researcher.root);

  // =========================================================================
  // 1.88 M CONTINUOUS CONFINED CORRIDOR RIG (ZERO LOOP RESETS REQUIRED!)
  // =========================================================================
  const corridorGroup = new THREE.Group();
  labSet.add(corridorGroup);

  // Aluminum sub-carrier base (Y = -3.20 mm -> -1.40 mm)
  const corridorBasePlate = new THREE.Mesh(new THREE.BoxGeometry(1920, 1.8, 128), mats.anodizedBlackMat);
  corridorBasePlate.position.set(0, -2.30, 0);
  corridorGroup.add(corridorBasePlate);

  // Laser-etched millimeter/centimeter ruler strip along front edge (Y = -1.34 mm, Z = +54 mm -> zero overlap!)
  const rulerStrip = new THREE.Mesh(new THREE.PlaneGeometry(1840, 14), mats.rulerMat);
  rulerStrip.rotation.x = -Math.PI / 2;
  rulerStrip.position.set(0, -1.34, 54.0);
  corridorGroup.add(rulerStrip);

  // Continuous 1,880 mm test runway strip (Y = -1.40 mm -> 0.000 mm!)
  const labFloorStrip = new THREE.Mesh(new THREE.BoxGeometry(1880, 1.4, 88), mats.grit40Mat);
  labFloorStrip.position.set(0, -0.70, 0);
  corridorGroup.add(labFloorStrip);

  // Flicker-Free Non-Overlapping Crystal-Clear Acrylic Ceiling Slab (1,840 mm long!)
  const ceilingSlab = new THREE.Group();
  const roofTopPane = new THREE.Mesh(new THREE.BoxGeometry(1840, 1.2, 54.0), mats.acrylicClearMat);
  roofTopPane.position.set(0, 0.60, 0.0);
  roofTopPane.renderOrder = 10;
  // Front & back polished cyan bevel strips separated by 0.3 mm air gap -> ZERO coplanar faces!
  const frontGlassEdge = new THREE.Mesh(new THREE.BoxGeometry(1840, 1.2, 1.4), mats.acrylicEdgeMat);
  frontGlassEdge.position.set(0, 0.60, 28.0);
  frontGlassEdge.renderOrder = 12;
  const backGlassEdge = new THREE.Mesh(new THREE.BoxGeometry(1840, 1.2, 1.4), mats.acrylicEdgeMat);
  backGlassEdge.position.set(0, 0.60, -28.0);
  backGlassEdge.renderOrder = 11;
  ceilingSlab.add(roofTopPane, frontGlassEdge, backGlassEdge);
  corridorGroup.add(ceilingSlab);

  // Precision Micrometer Vernier Actuator Towers spaced along the 1.8m corridor (X = -360, -120, +120, +360)
  // Gives gorgeous real-world parallax during continuous high-speed tracking shots!
  function makeMicrometerTower() {
    const g = new THREE.Group();
    for (const pz of [-46, 46]) {
      const post = new THREE.Mesh(new THREE.CylinderGeometry(3.6, 3.6, 58, 16), mats.steelBrushedMat);
      post.position.set(0, 27.6, pz);
      g.add(post);
      if (pz > 0) {
        for (const hTick of [3.2, 4.0, 6.0, 9.0, 12.0]) {
          const tick = new THREE.Mesh(new THREE.BoxGeometry(4.4, 0.35, 1.2), mats.brassMat);
          tick.position.set(0, hTick, pz + 3.5);
          g.add(tick);
        }
      }
    }
    const crossBar = new THREE.Mesh(new THREE.BoxGeometry(15, 6, 104), mats.anodizedBlackMat);
    crossBar.position.set(0, 55, 0);
    const drum = new THREE.Mesh(new THREE.CylinderGeometry(7.2, 7.2, 20, 24), mats.brassMat);
    drum.position.set(0, 68, 0);
    g.add(crossBar, drum);
    return { group: g, drum };
  }

  const micrometerBridge = new THREE.Group();
  const micrometerDrums = [];
  for (const tx of [-360, -120, 120, 360]) {
    const tw = makeMicrometerTower();
    tw.group.position.x = tx;
    micrometerBridge.add(tw.group);
    micrometerDrums.push(tw.drum);
  }
  corridorGroup.add(micrometerBridge);

  // Narrowing Acrylic Crevice Gate (Scene 02 500fps 5-move traversal & Scene 06 315-trial gate!)
  const labGateGroup = new THREE.Group();
  const gateBlade = new THREE.Mesh(new THREE.BoxGeometry(16.0, 48.0, 76.0), mats.acrylicEdgeMat);
  gateBlade.position.set(8.0, 24.0, 0);
  gateBlade.renderOrder = 14;
  const gateSteelClamp = new THREE.Mesh(new THREE.BoxGeometry(20.0, 10.0, 80.0), mats.steelBrushedMat);
  gateSteelClamp.position.set(8.0, 49.5, 0);
  labGateGroup.add(gateBlade, gateSteelClamp);
  labGateGroup.visible = false;
  labSet.add(labGateGroup);

  // Footless Traction Shear-Force Sensor Plate (Ch05 Shot 5A — mu = 1.73 - 2.04!)
  const tractionPlateGroup = new THREE.Group();
  tractionPlateGroup.visible = false;
  const sensorRim = new THREE.Mesh(new THREE.BoxGeometry(16, 0.32, 12), mats.steelBrushedMat);
  sensorRim.position.set(0, 0.16, 0);
  const sensorPad = new THREE.Mesh(new THREE.BoxGeometry(14, 0.38, 10), mats.anodizedBlackMat);
  sensorPad.position.set(0, 0.19, 0);
  const shearVecMat = new THREE.MeshBasicMaterial({ color: '#ffd187' });
  const shearShaft = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, 3.6, 10), shearVecMat);
  shearShaft.rotation.z = Math.PI / 2;
  shearShaft.position.set(-3.2, 0.65, 0);
  const shearTip = new THREE.Mesh(new THREE.ConeGeometry(0.28, 0.85, 12), shearVecMat);
  shearTip.rotation.z = Math.PI / 2;
  shearTip.position.set(-5.3, 0.65, 0);
  tractionPlateGroup.add(sensorRim, sensorPad, shearShaft, shearTip);
  labSet.add(tractionPlateGroup);

  // 3-Swatch Silicon-Carbide Grit Comparison Tray (Ch05 Shot 5B — Slick 100 vs Medium 40 vs Coarse 20!)
  const gritSwatchGroup = new THREE.Group();
  gritSwatchGroup.visible = false;
  const swatchSpecs = [
    { x: -38, mat: mats.grit100Mat },
    { x:   0, mat: mats.grit40Mat  },
    { x:  38, mat: mats.grit20Mat  },
  ];
  for (const sp of swatchSpecs) {
    const frame = new THREE.Mesh(new THREE.BoxGeometry(32, 1.6, 44), mats.steelBrushedMat);
    frame.position.set(sp.x, -2.2, 0);
    const pad = new THREE.Mesh(new THREE.BoxGeometry(29, 1.4, 41), sp.mat);
    pad.position.set(sp.x, -0.7, 0);
    gritSwatchGroup.add(frame, pad);
  }
  labSet.add(gritSwatchGroup);

  // 3-Lane Simultaneous Comparison Arena (920 mm long -> single-take races with ZERO modulo resets!)
  const multiLaneGroup = new THREE.Group();
  multiLaneGroup.visible = false;
  const multiBasePlate = new THREE.Mesh(new THREE.BoxGeometry(940, 1.8, 128), mats.anodizedBlackMat);
  multiBasePlate.position.set(0, -2.30, 0);
  multiLaneGroup.add(multiBasePlate);

  const laneOffsetsZ = [-38, 0, 38];
  const laneFloors = laneOffsetsZ.map((lz) => {
    const fl = new THREE.Mesh(new THREE.BoxGeometry(920, 1.4, 30), mats.grit40Mat);
    fl.position.set(0, -0.70, lz); // Top strictly at Y = 0.000 mm!
    multiLaneGroup.add(fl);
    return fl;
  });
  const laneRoofs = laneOffsetsZ.map((lz) => {
    const rg = new THREE.Group();
    const top = new THREE.Mesh(new THREE.BoxGeometry(900, 1.1, 26.0), mats.acrylicClearMat);
    top.position.set(0, 0.55, 0);
    top.renderOrder = 10;
    const edge = new THREE.Mesh(new THREE.BoxGeometry(900, 1.1, 1.3), mats.acrylicEdgeMat);
    edge.position.set(0, 0.55, 13.9); // Non-overlapping Z gap!
    edge.renderOrder = 12;
    rg.add(top, edge);
    rg.position.set(0, 12.0, lz);
    multiLaneGroup.add(rg);
    return rg;
  });
  for (const dz of [-19, 19]) {
    const div = new THREE.Mesh(new THREE.BoxGeometry(900, 1.4, 1.2), mats.brassMat);
    div.position.set(0, 0.70, dz);
    multiLaneGroup.add(div);
  }
  labSet.add(multiLaneGroup);

  // =========================================================================
  // SET 3: ZACK-D SPORTS BIOMECHANICS FORCE-PLATE STUDIO (CH04)
  // =========================================================================
  const pushupSet = new THREE.Group();
  pushupSet.visible = false;
  scene.add(pushupSet);

  const gymFloor = new THREE.Mesh(new THREE.BoxGeometry(5600, 28, 4600), mats.breadboardMat);
  gymFloor.position.set(0, -14.0, 0);
  pushupSet.add(gymFloor);

  const gridHelper = new THREE.GridHelper(3800, 20, 0x5cd6de, 0x1d3b44);
  gridHelper.position.y = 2.0;
  pushupSet.add(gridHelper);

  // Architectural biomechanics studio backdrop pillars so the stage looks grounded & cinematic!
  for (const px of [-1600, -550, 550, 1600]) {
    const col = new THREE.Mesh(new THREE.BoxGeometry(140, 2200, 140), mats.anodizedBlackMat);
    col.position.set(px, 1100, -1650);
    const strip = new THREE.Mesh(
      new THREE.PlaneGeometry(18, 1900),
      new THREE.MeshBasicMaterial({ color: '#5cd6de' })
    );
    strip.position.set(px, 1050, -1578);
    pushupSet.add(col, strip);
  }

  // Glowing cyan Force-Plate Sensor Pads that track under Left & Right Hands!
  const forcePads = [-1, 1].map(() => {
    const p = new THREE.Mesh(
      new THREE.BoxGeometry(320, 8, 320),
      new THREE.MeshBasicMaterial({ color: '#1b5560' })
    );
    p.position.y = 4.0;
    pushupSet.add(p);
    return p;
  });

  const athletePivot = new THREE.Group();
  humanActors.athlete.root.rotation.set(0, 0, -Math.PI / 2);
  athletePivot.add(humanActors.athlete.root);
  pushupSet.add(athletePivot);

  const pushupVectors = new THREE.Group();
  const vecMatGreen = new THREE.MeshBasicMaterial({ color: '#6ef29c' });
  const vecMatAmber = new THREE.MeshBasicMaterial({ color: '#ffa84c' });
  const handArrows = [-1, 1].map((s) => {
    const g = new THREE.Group();
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(13, 13, 280, 12), vecMatGreen);
    shaft.position.y = 140;
    const tip = new THREE.Mesh(new THREE.ConeGeometry(34, 82, 14), vecMatGreen);
    tip.position.y = 315;
    g.add(shaft, tip);
    pushupVectors.add(g);
    return { group: g, shaft, tip, side: s };
  });
  pushupSet.add(pushupVectors);

  // =========================================================================
  // 30 HZ EVERY-FRAME TEXEL-SNAPPED REAL-TIME SHADOW ENGINE (ZERO FLICKER!)
  // =========================================================================
  const shadowRT = new THREE.WebGLRenderTarget(512, 512, {
    minFilter: THREE.NearestFilter,
    magFilter: THREE.NearestFilter,
    format: THREE.RGBAFormat,
    type: THREE.UnsignedByteType,
  });
  const shadowDepthMat = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  const shadowCam = new THREE.OrthographicCamera(-60, 60, 60, -60, 1.0, 4200.0);

  const lightRight = new THREE.Vector3();
  const lightUp = new THREE.Vector3();
  const snappedFocus = new THREE.Vector3();

  function updateShadowMap(focusCenter, frustumHalf = 65.0) {
    // Runs EVERY SINGLE FRAME (30 Hz) with light-space texel snapping -> ZERO shadow swimming/flicker!
    const keyDir = SHARED_LIGHT_UNIFORMS.uKeyDir.value;
    lightRight.crossVectors(new THREE.Vector3(0, 1, 0), keyDir).normalize();
    lightUp.crossVectors(keyDir, lightRight).normalize();

    const texelWorld = (frustumHalf * 2.0) / 512.0;
    const rx = Math.round(focusCenter.dot(lightRight) / texelWorld) * texelWorld;
    const ry = Math.round(focusCenter.dot(lightUp) / texelWorld) * texelWorld;
    const rz = focusCenter.dot(keyDir);

    snappedFocus.set(0, 0, 0)
      .addScaledVector(lightRight, rx)
      .addScaledVector(lightUp, ry)
      .addScaledVector(keyDir, rz);

    const dist = Math.max(180.0, frustumHalf * 3.2);
    shadowCam.left   = -frustumHalf;
    shadowCam.right  =  frustumHalf;
    shadowCam.top    =  frustumHalf;
    shadowCam.bottom = -frustumHalf;
    shadowCam.near   =  dist * 0.12;
    shadowCam.far    =  dist * 2.8;
    shadowCam.position.copy(snappedFocus).addScaledVector(keyDir, dist);
    shadowCam.lookAt(snappedFocus);
    shadowCam.updateProjectionMatrix();
    shadowCam.updateMatrixWorld(true);

    // Hide transparent glass slabs & off-frustum high-poly human rigs during depth pass!
    const prevCeil = ceilingSlab.visible;
    const prevGate = labGateGroup.visible;
    const prevMulti = laneRoofs[0].visible;
    const prevHome = humanActors.homeowner.root.visible;
    const prevRes  = humanActors.researcher.root.visible;
    ceilingSlab.visible = false;
    labGateGroup.visible = false;
    laneRoofs.forEach((r) => { r.visible = false; });
    if (frustumHalf < 200.0) {
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
    labGateGroup.visible = prevGate;
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
    cramActor,
    cramBenchProp,
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
    micrometerDrums,
    labGateGroup,
    tractionPlateGroup,
    gritSwatchGroup,
    multiLaneGroup,
    laneFloors,
    laneRoofs,
    phantomCam,
    pushupSet,
    athletePivot,
    forcePads,
    handArrows,
    vecMatGreen,
    vecMatAmber,
    setLightingMood,
    updateShadowMap,
  };
}

export { createOpticalLensPassV4 as createOpticalLensPassV5 } from '../v4/world_v4.js';
