import * as THREE from 'three';
import { GLM, createCockroachActor } from '../v3/cockroach3d.js';

export { GLM };

/**
 * Monarch Cam #03 — V4 Enhanced Anatomical Periplaneta americana + Full-Body 3D X-Ray Cutaway Rig!
 * Upgrades V3 with:
 *   1. Sculpted chitinous joint condyles at every hip, knee, and tibio-tarsal joint (zero segment pinch/gap!).
 *   2. Curved thorn-profile crampon spines replacing primitive straight cones.
 *   3. Full-Body Zack-D Translucent 3D X-Ray Cockroach enclosing the rigid roof-tile tergites,
 *      accordion-pleated cyan arthrodial membranes, emerald ventral nerve cord + ganglia, and tracheae!
 *   4. Biomimetic CRAM (Compressible Robot with Articulated Mechanisms, Jayaram & Full 2016) lab prop!
 */
export function createCockroachActorV4(mats, opts = {}) {
  const actor = createCockroachActor(mats, opts);

  // Replace primitive straight-cone spines with curved, backward-hooked chitinous crampon thorns!
  const thornCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0.0, 0.0, 0.0),
    new THREE.Vector3(0.02, 0.36, 0.0),
    new THREE.Vector3(0.06, 0.72, 0.0),
    new THREE.Vector3(0.11, 1.00, 0.0),
  ]);
  const thornRings = [];
  for (let r = 0; r <= 7; r++) {
    const u = r / 7;
    const pt = thornCurve.getPoint(u);
    const rad = 0.145 * Math.pow(1.0 - u * 0.92, 0.78);
    const ring = [];
    for (let c = 0; c < 7; c++) {
      const a = (c / 7) * Math.PI * 2;
      ring.push(pt.x + Math.cos(a) * rad, pt.y, pt.z + Math.sin(a) * rad * 0.82);
    }
    thornRings.push(ring);
  }
  const pos = [], idx = [];
  for (let r = 0; r <= 7; r++) {
    for (let c = 0; c < 7; c++) {
      pos.push(thornRings[r][c * 3], thornRings[r][c * 3 + 1], thornRings[r][c * 3 + 2]);
    }
  }
  for (let r = 0; r < 7; r++) {
    for (let c = 0; c < 7; c++) {
      const a = r * 7 + c, b = r * 7 + ((c + 1) % 7);
      const d = (r + 1) * 7 + c, e = (r + 1) * 7 + ((c + 1) % 7);
      idx.push(a, d, b, b, d, e);
    }
  }
  const thornGeo = new THREE.BufferGeometry();
  thornGeo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  thornGeo.setIndex(idx);
  thornGeo.computeVertexNormals();

  // Swap InstancedMesh geometry on spines
  actor.root.children.forEach((ch) => {
    if (ch.isInstancedMesh && ch.count === 168) {
      ch.geometry.dispose();
      ch.geometry = thornGeo;
    }
  });

  // Add 18 sculpted arthrodial joint condyle capsules (hip, knee, ankle x 6 legs) so joints look 100% organic!
  const condyleGeo = new THREE.SphereGeometry(1.0, 12, 10);
  const condylesInst = new THREE.InstancedMesh(condyleGeo, mats.jointCondyleMat || mats.legMat, 18);
  condylesInst.castShadow = true;
  condylesInst.frustumCulled = false;
  actor.root.add(condylesInst);

  const tmpM = new THREE.Matrix4();
  const tmpQ = new THREE.Quaternion();
  const tmpS = new THREE.Vector3();
  const origUpdate = actor.update;

  actor.update = function updateV4(state) {
    const res = origUpdate(state);
    // Place organic joint condyles directly at hip (femur.position), knee (tibia.position), and ankle (tarsomeres[0].position)!
    let ci = 0;
    for (let li = 0; li < actor.legs.length; li++) {
      const leg = actor.legs[li];
      const scaleMul = leg.spec.pair === 2 ? 1.12 : 0.95;

      tmpS.set(0.46 * scaleMul, 0.42 * scaleMul, 0.46 * scaleMul);
      tmpM.compose(leg.femur.position, tmpQ, tmpS);
      condylesInst.setMatrixAt(ci++, tmpM);

      tmpS.set(0.38 * scaleMul, 0.36 * scaleMul, 0.38 * scaleMul);
      tmpM.compose(leg.tibia.position, tmpQ, tmpS);
      condylesInst.setMatrixAt(ci++, tmpM);

      tmpS.set(0.25 * scaleMul, 0.24 * scaleMul, 0.25 * scaleMul);
      tmpM.compose(leg.tarsomeres[0].position, tmpQ, tmpS);
      condylesInst.setMatrixAt(ci++, tmpM);
    }
    condylesInst.instanceMatrix.needsUpdate = true;
    return res;
  };

  return actor;
}

/**
 * Zack-D-Style Full-Body Translucent 3D X-Ray & Sagittal Cutaway Cockroach!
 * Replaces V3's abstract floating block with an unmistakable translucent 3D cockroach
 * whose internal dorsal shingle plates, cyan pleated arthrodial hinges, emerald ventral
 * nerve cord + ganglia, and silver tracheal tubes fold & rebound in real time!
 */
export function createXrayCutawayRigV4(mats) {
  const group = new THREE.Group();

  // 1. Complete translucent ghost/glass cockroach outer body + articulated legs & antennae!
  const glassMaterials = {
    ...mats,
    pronotumMat: mats.xrayGlassShellMat,
    tegminaMat: mats.xrayGlassShellMat,
    tergiteMat: mats.xrayGlassShellMat,
    pleuralNaturalMat: mats.xrayGlassShellMat,
  };
  const ghostRoach = createCockroachActorV4(glassMaterials, { includeWing: false });
  // Offset slightly into -Z so the sagittal cut plane at Z = +0.4 mm slices cleanly down the midline!
  ghostRoach.root.position.set(0, 0, -0.8);
  group.add(ghostRoach.root);

  // 2. Seven Rigid Curved Amber Chitin Dorsal Sclerites (constant chord length, zero rubbery bending!)
  const plateSpecs = [
    { chord: 7.2, arch: 0.58, thick: 0.46, w: 5.2 },
    { chord: 4.3, arch: 0.35, thick: 0.40, w: 5.4 },
    { chord: 4.1, arch: 0.32, thick: 0.38, w: 5.4 },
    { chord: 3.1, arch: 0.26, thick: 0.34, w: 5.0 },
    { chord: 3.0, arch: 0.24, thick: 0.32, w: 4.7 },
    { chord: 2.8, arch: 0.22, thick: 0.30, w: 4.2 },
    { chord: 2.6, arch: 0.18, thick: 0.28, w: 3.6 },
  ];

  const plates = plateSpecs.map((s) => {
    const shape = new THREE.Shape();
    const N = 18;
    for (let i = 0; i <= N; i++) {
      const u = i / N;
      const x = -u * s.chord;
      const y = Math.sin(Math.PI * u) * s.arch;
      if (i === 0) shape.moveTo(x, y); else shape.lineTo(x, y);
    }
    for (let i = N; i >= 0; i--) {
      const u = i / N;
      const x = -u * s.chord;
      const y = Math.sin(Math.PI * u) * s.arch - s.thick;
      shape.lineTo(x, y);
    }
    shape.closePath();
    const geo = new THREE.ExtrudeGeometry(shape, {
      depth: s.w, bevelEnabled: true, bevelThickness: 0.06, bevelSize: 0.05, bevelSegments: 2,
    });
    geo.translate(0, 0, -s.w + 0.8);
    const m = new THREE.Mesh(geo, [mats.cutFaceMat, mats.tergiteMat]);
    m.castShadow = true;
    m.receiveShadow = true;
    group.add(m);
    return { spec: s, mesh: m };
  });

  // 3. Six Glowing Cyan Accordion-Pleated Arthrodial Intersegmental Hinges!
  const hinges = [];
  for (let i = 0; i < plates.length - 1; i++) {
    const hGroup = new THREE.Group();
    // V-shaped folding bellows ribbon + glowing joint core
    const upperLeaf = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.14, plates[i + 1].spec.w * 0.92), mats.arthrodialMat);
    const lowerLeaf = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.14, plates[i + 1].spec.w * 0.92), mats.arthrodialMat);
    const creaseCyl = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, plates[i + 1].spec.w * 0.95, 14), mats.arthrodialMat);
    creaseCyl.rotation.x = Math.PI / 2;
    const zCenter = -plates[i + 1].spec.w * 0.45 + 0.8;
    upperLeaf.position.set(0.28, 0.18, zCenter);
    lowerLeaf.position.set(0.28, -0.18, zCenter);
    creaseCyl.position.set(-0.14, 0.0, zCenter);
    hGroup.add(upperLeaf, lowerLeaf, creaseCyl);
    group.add(hGroup);
    hinges.push({ hGroup, upperLeaf, lowerLeaf });
  }

  // 4. Anatomical Ventral Nerve Cord + 6 Segmental Ganglia (Emerald Bioluminescent Highlight!)
  const nerveGroup = new THREE.Group();
  const cordCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(10.2, 1.35, 0.2),
    new THREE.Vector3(5.8,  0.85, 0.2),
    new THREE.Vector3(0.4,  0.75, 0.2),
    new THREE.Vector3(-6.2, 0.72, 0.2),
    new THREE.Vector3(-13.8,0.78, 0.2),
  ]);
  const cordMesh = new THREE.Mesh(new THREE.TubeGeometry(cordCurve, 32, 0.16, 8, false), mats.nerveCordMat);
  nerveGroup.add(cordMesh);
  for (const gx of [9.4, 6.2, 2.2, -1.8, -6.2, -10.4]) {
    const g = new THREE.Mesh(new THREE.SphereGeometry(0.38, 12, 10), mats.nerveCordMat);
    g.scale.set(1.45, 0.75, 0.95);
    g.position.set(gx, gx > 7 ? 1.25 : 0.78, 0.22);
    nerveGroup.add(g);
  }
  group.add(nerveGroup);

  // 5. Branching Silver-Cyan Compressible Tracheal Air Tubes (instead of plain circles!)
  const tracheae = Array.from({ length: 5 }, (_, i) => {
    const tx = 6.2 - i * 4.1;
    const branch = new THREE.Group();
    const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.42, 3.8, 16), mats.tracheaMat);
    trunk.rotation.x = Math.PI / 2;
    trunk.position.set(0, 0, -1.2);
    const ramusA = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.24, 2.2, 10), mats.tracheaMat);
    ramusA.rotation.z = 0.62;
    ramusA.position.set(0.65, 0.55, 0.35);
    const ramusB = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.24, 2.0, 10), mats.tracheaMat);
    ramusB.rotation.z = -0.58;
    ramusB.position.set(-0.62, 0.48, 0.35);
    branch.add(trunk, ramusA, ramusB);
    branch.position.set(tx, 2.6, 0);
    group.add(branch);
    return branch;
  });

  // 6. Brushed-Steel + Optical Crystal Laboratory Compression Platen + Load-Cell Piston!
  const platenGroup = new THREE.Group();
  const glassPlate = new THREE.Mesh(new THREE.BoxGeometry(34.0, 0.75, 16.0), mats.acrylicEdgeMat);
  const steelCollar = new THREE.Mesh(new THREE.CylinderGeometry(3.4, 4.0, 2.6, 24), mats.steelBrushedMat);
  steelCollar.position.set(0, 1.7, -1.0);
  const pistonShaft = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 1.5, 18.0, 18), mats.steelBrushedMat);
  pistonShaft.position.set(0, 11.5, -1.0);
  platenGroup.add(glassPlate, steelCollar, pistonShaft);
  group.add(platenGroup);

  // 7. Distributed Golden Force Vectors across all 7 Hinged Plates (for Scene 06 900x BW!)
  const loadArrows = new THREE.Group();
  const arrowMat = new THREE.MeshBasicMaterial({ color: '#ffd187' });
  for (let i = 0; i < 7; i++) {
    const ax = 8.4 - i * 3.1;
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 2.0, 8), arrowMat);
    shaft.position.set(ax, 1.55, 0.6);
    const cone = new THREE.Mesh(new THREE.ConeGeometry(0.32, 0.68, 12), arrowMat);
    cone.rotation.z = Math.PI;
    cone.position.set(ax, 0.42, 0.6);
    loadArrows.add(shaft, cone);
  }
  group.add(loadArrows);

  function update({ compAlpha = 0.0, showPlaten = true, showLoadArrows = false, time = 0.0, phase = 0.0 } = {}) {
    const ceilingEquiv = GLM.mix(11.8, 3.35, compAlpha);
    ghostRoach.update({
      ceilingMm: ceilingEquiv,
      worldX: 0,
      worldZ: -0.8,
      phase,
      strideAmp: 0.18,
      time,
      floorY: 0,
    });

    const unloadedHeights = [6.4, 6.8, 6.6, 5.9, 5.4, 4.9, 4.3];
    const loadedHeights   = [3.05, 3.25, 3.18, 2.90, 2.70, 2.50, 2.30];
    let curX = 9.8;
    let peakY = 0;
    const landmarks = {};

    for (let i = 0; i < plates.length; i++) {
      const p = plates[i];
      const h0 = GLM.mix(unloadedHeights[i], loadedHeights[i], compAlpha);
      const h1 = GLM.mix(
        unloadedHeights[Math.min(plates.length - 1, i + 1)],
        loadedHeights[Math.min(plates.length - 1, i + 1)],
        compAlpha
      );
      const dy = GLM.clamp((h1 + 0.34 * (1 - 0.55 * compAlpha)) - h0, -p.spec.chord * 0.5, p.spec.chord * 0.5);
      const pitch = Math.asin(dy / p.spec.chord);
      p.mesh.position.set(curX, h0, 0);
      p.mesh.rotation.set(0, 0, -pitch);
      peakY = Math.max(peakY, h0 + p.spec.arch);

      const tipX = curX - Math.cos(pitch) * p.spec.chord;
      const tipY = h0 + Math.sin(pitch) * p.spec.chord;
      if (i < hinges.length) {
        const h = hinges[i];
        h.hGroup.position.set(tipX + 0.52, tipY - 0.30, 0);
        // True origami V-fold as compAlpha increases from 0 -> 1!
        const foldAngle = GLM.mix(0.48, 0.08, compAlpha);
        h.upperLeaf.rotation.z = foldAngle;
        h.lowerLeaf.rotation.z = -foldAngle;
        h.upperLeaf.position.y = Math.sin(foldAngle) * 0.38;
        h.lowerLeaf.position.y = -Math.sin(foldAngle) * 0.38;
        if (i === 2) landmarks.hinge = new THREE.Vector3(tipX + 0.52, tipY - 0.25, 0.8).applyMatrix4(group.matrixWorld);
      }
      if (i === 1) landmarks.plate = new THREE.Vector3(curX - 2.0, h0 + 0.25, 0.8).applyMatrix4(group.matrixWorld);
      curX = tipX + (0.98 + 0.42 * compAlpha);
    }

    const innerH = Math.max(1.55, peakY - 0.72);
    nerveGroup.scale.y = GLM.mix(1.0, 0.62, compAlpha);
    for (let i = 0; i < tracheae.length; i++) {
      tracheae[i].position.y = 0.75 + innerH * (0.44 - i * 0.03);
      // Elliptical lateral flattening of tracheae without rupturing!
      tracheae[i].scale.set(1.0 + 0.35 * compAlpha, 1.0 - 0.50 * compAlpha, 1.0);
    }

    platenGroup.visible = showPlaten;
    platenGroup.position.set(-1.2, peakY + 0.42, 0);
    loadArrows.visible = showLoadArrows;
    loadArrows.position.set(-1.2, peakY + 0.85, 0);
    landmarks.platen = new THREE.Vector3(-1.2, peakY + 0.42, 0.8).applyMatrix4(group.matrixWorld);
    return { peakY, landmarks };
  }

  return { group, update };
}

/**
 * Biomimetic CRAM Soft-Shell Robot Prototype Prop (Jayaram & Full 2016, UC Berkeley)
 * Overlapping laser-cut compliant dorsal shell plates + splayed spiny legs sitting on lab bench!
 */
export function createCramRobotProp(mats) {
  const g = new THREE.Group();
  const baseChassis = new THREE.Mesh(new THREE.BoxGeometry(46, 3.2, 28), mats.anodizedBlackMat);
  baseChassis.position.y = 3.2;
  g.add(baseChassis);

  // 5 Overlapping compliant amber-polymer shell tiles inspired by cockroach tergites!
  for (let i = 0; i < 5; i++) {
    const tile = new THREE.Mesh(new THREE.BoxGeometry(11.5, 0.9, 30 - i * 1.4), mats.cutFaceMat);
    tile.position.set(16 - i * 8.2, 6.8 - i * 0.35, 0);
    tile.rotation.z = 0.11;
    tile.castShadow = true;
    g.add(tile);
  }
  // 4 Splayed compliant robot legs
  for (const sx of [-12, 12]) {
    for (const sz of [-1, 1]) {
      const leg = new THREE.Mesh(new THREE.BoxGeometry(3.2, 0.8, 12), mats.steelBrushedMat);
      leg.position.set(sx, 2.2, sz * 18);
      leg.rotation.x = sz * 0.24;
      leg.castShadow = true;
      g.add(leg);
    }
  }
  return g;
}
