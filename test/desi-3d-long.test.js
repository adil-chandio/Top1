import test from 'node:test';
import assert from 'node:assert/strict';
import {
  DURATION, FPS, FRAME, BEATS, CAPTIONS, CLOCK, MELT, ILLUSTRATION_BADGE,
  clamp, progress,
  beatAt, beatIndexAt, beatCaptionAt, beatProgressAt,
  elapsedAt, clockRunningAt, clockLabelAt,
  metalMeltAt, woodMeltAt, questionProgress, revealProgress, outroProgress,
} from '../tools/monarchs-edit/desi-3d-explainer/long/timeline.js';
import { createScene, WORLD } from '../tools/monarchs-edit/desi-3d-explainer/long/scene.js';
import { PILOTS, getPilot } from '../tools/monarchs-edit/desi-3d-explainer/scenarios.js';

test('the long-form beat sheet covers the full 92-second run, contiguous and capped at DURATION', () => {
  assert.equal(DURATION, 92);
  assert.equal(FPS, 24);
  assert.equal(BEATS[0].start, 0);
  assert.equal(BEATS.at(-1).end, DURATION);
  for (let i = 0; i < BEATS.length - 1; i++) assert.equal(BEATS[i].end, BEATS[i + 1].start);
  for (let t = 0; t <= DURATION; t += 0.25) assert.ok(BEATS.includes(beatAt(t)), `uncovered time ${t}`);
  assert.equal(beatIndexAt(1.0), 0);
  assert.equal(beatIndexAt(92), BEATS.length - 1);
  assert.equal(FRAME.width, 1280, '16:9 long-form frame');
  assert.equal(FRAME.height, 720, '16:9 long-form frame');
  assert.equal(FRAME.width / FRAME.height, 16 / 9);
  assert.match(ILLUSTRATION_BADGE, /NOT A TEST RESULT/);
  assert.ok([...CAPTIONS.opening ? [CAPTIONS.opening] : []].length >= 1);
  for (const beat of BEATS) assert.ok(CAPTIONS[beat.id], `missing caption for beat '${beat.id}'`);
});

test('the long-form clock starts at 9s, runs to 56s, and holds still afterwards', () => {
  assert.equal(elapsedAt(9), 0);
  assert.equal(elapsedAt(24), 15);
  assert.equal(elapsedAt(56), 47);
  assert.equal(elapsedAt(92), 47);
  assert.equal(clockRunningAt(8.99), false);
  assert.equal(clockRunningAt(9), true);
  assert.equal(clockRunningAt(55.99), true);
  assert.equal(clockRunningAt(56), false);
  assert.equal(clockLabelAt(24), 'T+15.0s');
});

test('illustrative melts advance inside their windows; metal melts further than wood', () => {
  assert.equal(metalMeltAt(9), 0);
  assert.equal(metalMeltAt(51.6), 1);
  assert.equal(woodMeltAt(9), 0);
  assert.ok(Math.abs(woodMeltAt(52.6) - 0.55) < 1e-6);
  const mid = 30;
  assert.ok(metalMeltAt(mid) > woodMeltAt(mid), 'metal melts further than wood at 30s');
  assert.ok(woodMeltAt(mid) > 0, 'wood should already be melting by 30s');
  assert.ok(metalMeltAt(0) === 0, 'nothing melts before the window');
  assert.ok(woodMeltAt(92) === 0.55, 'wood holds at its asymptote after the window');
});

test('the shared clock drives both the elapsed label and the STEADY hold after its window', () => {
  assert.ok(progress(14, MELT.metal[0], MELT.metal[1]) > 0, 'metal is already melting at 14s');
  assert.equal(metalMeltAt(10.6), 0, 'metal melts from 10.6s, not before');
  assert.equal(clamp(1.5), 1, 'clamp is bounded to 0..1');
  assert.equal(clamp(-1), 0, 'clamp is bounded to 0..1');
});

test('caption windows and fades advance progressively', () => {
  assert.equal(beatCaptionAt(2), CAPTIONS.opening);
  assert.equal(beatCaptionAt(30), CAPTIONS.timelapse);
  assert.equal(beatCaptionAt(60), CAPTIONS.evidence);
  assert.equal(beatCaptionAt(72), CAPTIONS.honesty);
  assert.equal(questionProgress(0), 0);
  assert.equal(questionProgress(1.6), 1);
  assert.ok(revealProgress(80) > revealProgress(76));
  assert.equal(revealProgress(84), 1);
  assert.ok(outroProgress(89) > outroProgress(86));
  assert.equal(outroProgress(92), 1);
});

test('scene exposes the two blocks, the two ice cubes, and the heat arrows', () => {
  const { scene, refs } = createScene();
  assert.ok(scene, 'scene must exist');
  for (const object of Object.values(refs)) assert.ok(object, 'missing scene ref');
  assert.equal(refs.leftBlock.material.metalness, 1.0);
  assert.ok(refs.rightBlock.material.roughness > refs.leftBlock.material.roughness);
  assert.equal(refs.leftBlock.geometry, refs.rightBlock.geometry);
  assert.equal(refs.floor.geometry.parameters.radius, WORLD.floorRadius);
  assert.equal(refs.leftCube.material.opacity, 0.94);
  assert.equal(refs.leftBlock.position.x, -WORLD.gap / 2);
  assert.equal(refs.rightBlock.position.x, WORLD.gap / 2);
});

test('update() shrinks the cubes, gluing them to the block top, and holds the arrows back until the reveal', () => {
  const { update, refs } = createScene();
  const state0 = update(0);
  assert.equal(state0.metal, 0);
  assert.equal(state0.wood, 0);
  assert.equal(state0.reveal, 0);
  assert.equal(refs.leftCube.scale.y, 1, 'ice is full before the melt window');
  assert.ok(Math.abs(refs.leftCube.position.y - (WORLD.blockTop + WORLD.cube / 2)) < 1e-6, 'cubes start on the block top');
  assert.equal(refs.metalArrow.visible, false, 'no arrows before reveal');
  const mid = update(30);
  assert.ok(mid.metal > 0, 'metal has melted by 30s');
  assert.ok(mid.wood > 0, 'wood has melted by 30s');
  assert.ok(mid.metal > mid.wood, 'metal melts further by 30s');
  assert.equal(refs.leftCube.visible, true);
  const reveal = update(80);
  assert.ok(reveal.reveal > 0, 'reveal is in progress at 80s');
  assert.ok(refs.metalArrow.visible, 'metal arrow is shown during the reveal');
  assert.ok(refs.metalArrow.scale.x > refs.woodArrow.scale.x, 'metal arrow is larger than the wood arrow (illustrative)');
});

test('update() is safe at the ends of the window', () => {
  const { update, refs } = createScene();
  update(0);
  update(92);
  assert.ok(refs.leftCube.scale.y >= 0.06);
});

test('the long pilot is registered with its own view, layout and camera', () => {
  assert.ok(PILOTS.long, 'long pilot is registered');
  assert.ok(PILOTS.p1);
  assert.ok(PILOTS.e1);
  const pilot = getPilot('long');
  assert.equal(pilot.id, 'long');
  assert.equal(pilot.view.window, '92s · 16:9');
  assert.equal(pilot.imageWidth, undefined, 'no image manifest — video art is not fabricated');
  assert.equal(pilot.view.stillTimes.length, 8);
  assert.equal(pilot.view.layout.blocksLeftX, 359);
  assert.equal(pilot.view.layout.blocksRightX, 922);
  assert.equal(pilot.view.layout.railLeft, 56);
  assert.ok(pilot.view.camera.from.length === 3);
  assert.ok(pilot.view.camera.to.length === 3);
  assert.equal(pilot.view.camera.fov, 38);
  assert.ok(pilot.view.camera.lookAt.length === 3);
  assert.equal(pilot.view.camera.from[2] > pilot.view.camera.to[2], true, 'camera drifts toward the scene as the timeline advances');
  // The long pilot renders through its own frame and FPS, not P1/E1's
  assert.equal(pilot.timeline.DURATION, 92);
  assert.equal(pilot.timeline.FPS, 24);
  assert.equal(pilot.timeline.FRAME.width, 1280);
  assert.equal(pilot.timeline.FRAME.height, 720);
  assert.throws(() => getPilot('long-form'));
});
