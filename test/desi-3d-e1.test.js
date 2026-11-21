import test from 'node:test';
import assert from 'node:assert/strict';
import {
  DURATION, FPS, FRAME, BEATS, CAPTIONS, ILLUSTRATION_BADGE, PADDLE,
  beatAt, beatIndexAt, beatProgressAt, beatCaptionAt,
  elapsedAt, clockRunningAt, clockLabelAt,
  metalDrainAt, woodDrainAt, paddleWarmthAt, paddlePose,
  metalTouchAt, woodTouchAt, revealProgress, questionProgress, outroProgress,
} from '../tools/monarchs-edit/desi-3d-explainer/e1/timeline.js';
import { createScene, WORLD } from '../tools/monarchs-edit/desi-3d-explainer/e1/scene.js';

test('the E1 beat sheet covers the full 38-second run, contiguous and capped at DURATION', () => {
  assert.equal(DURATION, 38);
  assert.equal(BEATS[0].start, 0);
  assert.equal(BEATS.at(-1).end, DURATION);
  for (let i = 0; i < BEATS.length - 1; i++) assert.equal(BEATS[i].end, BEATS[i + 1].start);
  for (let t = 0; t <= DURATION; t += 0.25) assert.ok(BEATS.includes(beatAt(t)), `uncovered time ${t}`);
  assert.equal(FRAME.width, 720);
  assert.equal(FRAME.height, 1280);
  assert.match(ILLUSTRATION_BADGE, /NOT A TEST RESULT/);
  assert.equal(beatIndexAt(1), 0);
  assert.equal(beatIndexAt(38), BEATS.length - 1);
});

test('shared clock starts at 10s, runs to 26s, and holds still afterwards', () => {
  assert.equal(elapsedAt(10), 0);
  assert.equal(elapsedAt(16), 6);
  assert.equal(elapsedAt(26), 16);
  assert.equal(elapsedAt(38), 16);
  assert.equal(clockRunningAt(9.99), false);
  assert.equal(clockRunningAt(10), true);
  assert.equal(clockRunningAt(25.99), true);
  assert.equal(clockRunningAt(26), false);
  assert.equal(clockLabelAt(16), 'T+6.0s');
});

test('illustrative drain curves advance inside their windows; wood lags metal', () => {
  assert.equal(metalDrainAt(10), 0);
  assert.equal(metalDrainAt(17.5), 1);
  assert.ok(Math.abs(woodDrainAt(26) - 0.55) < 1e-6);
  const mid = 15;
  assert.ok(metalDrainAt(mid) > woodDrainAt(mid), 'metal drains further');
  assert.ok(metalDrainAt(0) === 0, 'nothing drains before the window');
  assert.ok(paddleWarmthAt(10) === 1, 'paddle starts warm');
  assert.ok(paddleWarmthAt(14) < 1, 'paddle cools down during the metal touch');
  assert.ok(paddleWarmthAt(20) < paddleWarmthAt(14), 'mid-flight keeps the cool look');
  assert.equal(woodTouchAt(24) ? 1 : 0, 1);
});

test('touch beats: touch-metal and touch-wood never overlap; paddle tracks the side', () => {
  assert.equal(metalTouchAt(12.5), true);
  assert.equal(metalTouchAt(18), false);
  assert.equal(metalTouchAt(20), false);
  assert.equal(woodTouchAt(21), true);
  assert.equal(woodTouchAt(26), false);
  for (let t = 0; t < DURATION; t += 0.25) {
    assert.equal(metalTouchAt(t) && woodTouchAt(t), false, 'touches must not overlap');
  }
  const metal = paddlePose(14);
  const wood = paddlePose(23);
  assert.ok(Math.abs(metal.x - -0.86) < 1e-6, 'paddle rests over the metal block at 14s');
  assert.ok(Math.abs(wood.x - 0.86) < 1e-6, 'paddle rests over the wood block at 23s');
  assert.ok(metal.y < 1.62, 'paddle descends to touch');
});

test('paddle pose stays hovering before the touch and leaves the block top as it lifts', () => {
  const idle = paddlePose(5);
  assert.ok(Math.abs(idle.y - PADDLE.restY) < 1e-6, 'paddle hovers at rest before the touch');
  const midFlight = paddlePose(19.0);
  assert.ok(midFlight.y > PADDLE.touchY, 'paddle arcs up between the two touches');
  assert.ok(Math.abs(midFlight.x) < 1e-6, 'paddle crosses the middle mid-arc');
  const after = paddlePose(36);
  assert.ok(after.y >= PADDLE.touchY, 'paddle leaves the block top on the way out');
});

test('caption windows and reveal/outro fades advance progressively', () => {
  assert.equal(CAPTIONS.question, 'Metal ka chamach zyada thanda kyun lagta hai?');
  assert.equal(beatCaptionAt(2), CAPTIONS.question);
  assert.equal(questionProgress(0), 0);
  assert.equal(questionProgress(1.4), 1);
  assert.ok(revealProgress(28) > revealProgress(26));
  assert.equal(revealProgress(30), 1);
  assert.ok(outroProgress(36) > outroProgress(32.4));
  assert.equal(outroProgress(38), 1);
});

test('scene exposes the blocks, the paddle and the lights', () => {
  const { scene, refs } = createScene();
  assert.ok(scene, 'scene must exist');
  for (const object of Object.values(refs)) assert.ok(object, 'missing scene ref');
  assert.equal(refs.leftBlock.material.metalness, 1.0);
  assert.ok(refs.rightBlock.material.roughness > refs.leftBlock.material.roughness);
  assert.equal(refs.paddle.material.emissive.getHexString(), 'ffb35c');
  assert.ok(refs.paddle.castShadow === true);
  assert.equal(refs.leftBlock.geometry, refs.rightBlock.geometry);
});

test('update() pins the paddle touch line, cools it, and keeps the emissive bounded', () => {
  const { update, refs } = createScene();
  const state0 = update(0);
  assert.equal(state0.warmth, 1, 'paddle starts fully warm');
  assert.ok(Math.abs(refs.paddle.position.x - 0) < 1e-6, 'paddle hovers centred at t=0');
  const mid = update(14);
  assert.ok(mid.warmth < 1, 'paddle cools during the metal touch');
  assert.ok(Math.abs(refs.paddle.position.y - PADDLE.touchY) < 1e-3, 'paddle touches the block top');
  assert.ok(refs.paddle.position.y < WORLD.blockTop + WORLD.paddle.size[1] + 0.05, 'paddle sits on the block top');
  const metal = refs.paddle;
  const warmthBefore = metal.material.emissiveIntensity;
  const wood = update(23);
  assert.ok(wood.woodDrain > 0.2, 'wood drains by 23s');
  assert.ok(wood.warmth < 1, 'wood side keeps only partial warmth');
  assert.ok(metal.material.emissiveIntensity > 0.24, 'emissive never dies — paddle stays visible');
  const maxEmissive = 0.25 + 0.85 * 1;
  assert.ok(metal.material.emissiveIntensity <= maxEmissive + 1e-3, 'emissive stays bounded');
});

test('update() is safe at the ends of the window', () => {
  const { update, refs } = createScene();
  update(0);
  update(DURATION);
  assert.ok(refs.paddle.position.y >= WORLD.blockTop);
});
