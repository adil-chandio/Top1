import test from 'node:test';
import assert from 'node:assert/strict';
import {
  DURATION, FPS, FRAME, BEATS, CAPTIONS, ILLUSTRATION_BADGE,
  beatAt, beatIndexAt, beatCaptionAt, beatProgressAt,
  elapsedAt, clockRunningAt, clockLabelAt,
  metalMeltAt, woodMeltAt, revealProgress, questionProgress, outroProgress,
} from '../tools/monarchs-edit/desi-3d-explainer/p1/timeline.js';
import { createScene, WORLD } from '../tools/monarchs-edit/desi-3d-explainer/p1/scene.js';

test('the P1 beat sheet covers the full 38-second run, contiguous and capped at DURATION', () => {
  assert.equal(DURATION, 38);
  assert.equal(BEATS[0].start, 0);
  assert.equal(BEATS[BEATS.length - 1].end, DURATION);
  for (let i = 0; i < BEATS.length - 1; i++) assert.equal(BEATS[i].end, BEATS[i + 1].start);
  for (let t = 0; t <= DURATION; t += 0.25) assert.ok(BEATS.includes(beatAt(t)), `uncovered time ${t}`);
  assert.equal(beatIndexAt(1.0), 0);
  assert.equal(beatIndexAt(38), BEATS.length - 1);
  assert.equal(FRAME.width, 720);
  assert.equal(FRAME.height, 1280);
  assert.match(ILLUSTRATION_BADGE, /NOT A TEST RESULT/);
});

test('shared clock starts at 10s, runs to 22s, and holds still afterwards', () => {
  assert.equal(elapsedAt(10), 0);
  assert.equal(elapsedAt(16), 6);
  assert.equal(elapsedAt(22), 12);
  assert.equal(elapsedAt(38), 12);
  assert.equal(clockRunningAt(9.99), false);
  assert.equal(clockRunningAt(10), true);
  assert.equal(clockRunningAt(21.99), true);
  assert.equal(clockRunningAt(22), false);
  assert.equal(clockLabelAt(16), 'T+6.0s');
});

test('illustrative melts advance over the timelapse window; metal melts further than wood', () => {
  assert.equal(metalMeltAt(10), 0);
  assert.equal(metalMeltAt(21.2), 1);
  assert.equal(woodMeltAt(10), 0);
  assert.ok(Math.abs(woodMeltAt(21.6) - 0.55) < 1e-6);
  assert.ok(metalMeltAt(15.5) > woodMeltAt(15.5));
  assert.ok(woodMeltAt(15.5) > 0, 'wood should already be melting by 15.5s');
  assert.ok(metalMeltAt(0) === 0, 'nothing melts before the window');
});

test('caption windows and reveal/outro fades advance progressively', () => {
  assert.equal(CAPTIONS.question, 'Baraf pehle kahan pighlegi — metal ya lakri?');
  assert.equal(beatCaptionAt(2), CAPTIONS.question);
  assert.equal(questionProgress(0), 0);
  assert.equal(questionProgress(1.4), 1);
  assert.ok(revealProgress(27) > revealProgress(22));
  assert.equal(revealProgress(29), 1);
  assert.ok(outroProgress(36) > outroProgress(32.4));
  assert.equal(outroProgress(38), 1);
});

test('scene exposes the two blocks, the two ice cubes, and the heat arrows', () => {
  const { scene, update, refs } = createScene();
  assert.ok(scene, 'scene must exist');
  for (const object of Object.values(refs)) assert.ok(object, 'missing scene ref');
  assert.equal(refs.leftBlock.material.metalness, 1.0);
  assert.ok(refs.rightBlock.material.roughness > refs.leftBlock.material.roughness);
  assert.equal(refs.leftCube.material.transparent, true);
  assert.equal(refs.rightCube.material.transparent, true);
  assert.equal(refs.metalArrow.visible, false);   // arrows appear in the reveal beat only
  assert.equal(refs.leftCube.geometry, refs.rightCube.geometry, 'cubes share one geometry');
  const arrowObjects = [refs.metalArrow, refs.woodArrow];
  for (const arrow of arrowObjects) {
    assert.equal(arrow.children.length, 2, 'arrow = shaft + tip');
  }
});

test('update() keeps the cubes glued to the block top as they shrink', () => {
  const { update, refs } = createScene();
  const state0 = update(0);
  assert.equal(state0.reveal, 0, 'reveal content starts hidden');
  assert.equal(state0.metal, 0);
  assert.equal(state0.wood, 0);

  for (const cube of [refs.leftCube, refs.rightCube]) {
    const base = cube.position.y - (WORLD.cube * cube.scale.y) / 2;
    assert.ok(Math.abs(base - WORLD.blockTop) < 1e-3, `cube base ${base} vs block top`);
  }

  const at = update(18);   // past the melt window but before reveal
  assert.ok(at.metal > 0.3, `metal melt progressed to ${at.metal}`);
  assert.ok(at.wood < at.metal, 'wood melts less than metal');
  assert.equal(at.reveal, 0, 'reveal content waits until the reveal beat');
  const metalScaled = refs.leftCube.scale.y;
  const woodScaled = refs.rightCube.scale.y;
  assert.ok(metalScaled < woodScaled, `metal cube (${metalScaled}) should be smaller than wood (${woodScaled})`);
  assert.ok(metalScaled >= 0.06 && woodScaled >= 0.06, 'cubes never vanish');

  const reveal = update(27);   // inside the reveal window
  assert.ok(reveal.reveal > 0.5, `reveal advanced to ${reveal.reveal}`);
  assert.ok(refs.metalArrow.visible && refs.woodArrow.visible, 'arrows appear in the reveal beat');
  const metalArrowScale = refs.metalArrow.scale.x;
  const woodArrowScale = refs.woodArrow.scale.x;
  assert.ok(metalArrowScale > woodArrowScale, 'metal arrow is brighter than the wood arrow');
});

test('update() is safe at the ends of the window', () => {
  const { update, refs } = createScene();
  update(0);
  update(DURATION);
  assert.ok(refs.leftCube.scale.y >= 0.06);
  assert.ok(refs.rightCube.scale.y >= 0.06);
});

test('scene exposes the melt puddles and the steam wisps', () => {
  const { scene, refs, update, world } = createScene();
  for (const ref of [refs.leftPuddle, refs.rightPuddle, refs.leftSteam, refs.rightSteam]) {
    assert.ok(ref, 'missing new scene ref');
  }
  assert.equal(refs.leftSteam.geometry.getAttribute('position').count, 26);
  assert.equal(refs.rightSteam.geometry.getAttribute('position').count, 26);
  assert.ok(refs.leftSteam.geometry.getAttribute('position').array.length === 26 * 3);
  assert.equal(refs.leftSteam.visible, true);
  const state = update(0);
  assert.ok(Math.abs(refs.leftPuddle.material.opacity - 0) < 1e-6, 'puddles start invisible');
  assert.ok(Math.abs(refs.leftSteam.material.opacity - 0) < 1e-6, 'steam starts invisible');
});

test('update() grows the puddles and lifts the steam with the melt, wood still slower', () => {
  const { update, refs, world } = createScene();
  update(0);
  const at = update(18);
  assert.ok(at.metal > 0.3, 'metal has melted by 18s');
  assert.ok(refs.leftPuddle.scale.x > 0.5, 'puddle grows with the melt');
  assert.ok(refs.leftPuddle.material.opacity > 0.1, 'puddle becomes visible');
  assert.ok(refs.rightPuddle.material.opacity < refs.leftPuddle.material.opacity, 'wood puddle is weaker — illustrative direction');
  assert.ok(refs.leftSteam.material.opacity > 0, 'metal steam is visible');
  assert.ok(refs.leftSteam.material.opacity > refs.rightSteam.material.opacity, 'metal steam is stronger than wood steam');
  // Steam must actually rise — y positions change over time
  const pos = refs.leftSteam.geometry.getAttribute('position');
  const y0 = pos.getY(0);
  const _ = update(24);
  const y1 = refs.leftSteam.geometry.getAttribute('position').getY(0);
  assert.notEqual(y1, y0, 'steam rises with the clock');
});

test('cubes stay glued to the block top and never vanish as the melt advances', () => {
  const { update, refs, world } = createScene();
  update(18);
  for (const cube of [refs.leftCube, refs.rightCube]) {
    const base = cube.position.y - (world.cube * cube.scale.y) / 2;
    assert.ok(Math.abs(base - world.blockTop) < 1e-3, `cube base ${base} vs block top`);
    assert.ok(cube.scale.y >= 0.06, 'cubes never vanish');
  }
  // Rotation wobbles but never flips past small angles
  assert.ok(Math.abs(refs.leftCube.rotation.y) <= 0.05, 'cube wobble is small');
});

test('the arrows remain illustrative direction — metal arrow always larger than wood', () => {
  const { update, refs } = createScene();
  const at = update(22);
  assert.equal(refs.metalArrow.children.length, 2, 'arrow = shaft + tip');
  assert.equal(refs.woodArrow.children.length, 2, 'arrow = shaft + tip');
  const reveal = update(27);
  assert.ok(reveal.reveal > 0.5, 'reveal has advanced');
  assert.ok(refs.metalArrow.visible && refs.woodArrow.visible, 'both arrows appear during the reveal');
  assert.ok(refs.metalArrow.scale.x > refs.woodArrow.scale.x, 'metal arrow stays larger');
});
