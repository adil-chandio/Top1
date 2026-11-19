import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import { AIR_CRUSH, AIR_CRUSH_CAPTIONS, AIR_TIMING } from '../src/air-crush.js';
import { BATH_Y, CAN_H, PORT_Y, RIG, buckle, canRadius, deformCan, eventClock, footPose, poseAt, pressureRatio, shutterTimes, splashHeight, vaporRemaining } from '../tools/demo-render/air-crush-motion.js';
import { cutAt } from '../tools/demo-render/motion.js';

const near = (a, b, eps = .00001) => assert.ok(Math.abs(a - b) < eps, `${a} is not near ${b}`);

function portHeight(t) {
  const { centerY, turn } = poseAt(t, 4);
  return centerY + Math.cos(Math.PI * turn) * PORT_Y;
}

test('the animated flip submerges the open port at the picture and Foley cue', () => {
  const t = AIR_TIMING.dip;
  assert.ok(portHeight(t - .04) > BATH_Y);
  near(portHeight(t), BATH_Y, .003);
  assert.ok(portHeight(t + .05) < BATH_Y);
  near(poseAt(11.5, 4).centerY, poseAt(11.5, 5).centerY);
  assert.equal(poseAt(t, 4).turn, 1);
});

test('the rim-driven flip stays clear of the bath and begins and ends at rest', () => {
  const end = RIG.flipTo;
  const dt = .001;
  near(poseAt(RIG.flipFrom + dt, 4).turn / dt, 0, .00002);
  near((1 - poseAt(end - dt, 4).turn) / dt, 0, .00002);
  assert.ok(RIG.flipTo < RIG.lowerFrom);
  for (let i = 0; i <= 120; i++) {
    const { centerY, turn } = poseAt(RIG.flipFrom + (end - RIG.flipFrom) * i / 120, 4);
    const angle = Math.PI * turn;
    for (let j = 0; j <= 120; j++) {
      const v = j / 120;
      const lowPoint = centerY + (v - .5) * CAN_H * Math.cos(angle) - canRadius(v) * Math.abs(Math.sin(angle));
      assert.ok(lowPoint > BATH_Y + .04, 'solid shell must clear the bath throughout the flip');
    }
  }
});

test('condensation starts after immersion and the inside pressure falls before the replay', () => {
  assert.ok(AIR_TIMING.dip < AIR_TIMING.condense);
  assert.ok(AIR_TIMING.condense <= AIR_TIMING.pressureStart);
  assert.ok(AIR_TIMING.pressureEnd < AIR_TIMING.snap);
  assert.equal(vaporRemaining(AIR_TIMING.condense), 1);
  assert.equal(pressureRatio(AIR_TIMING.pressureStart), 1);
  assert.ok(vaporRemaining(AIR_TIMING.pressureEnd) < .1);
  assert.ok(pressureRatio(AIR_TIMING.pressureEnd) < .25);
  for (let i = 0; i < 696; i++) assert.ok(pressureRatio((i + 1) / 24) <= pressureRatio(i / 24));
});

test('the deformation starts on impact, changes the side rather than shrinking the rim, and settles', () => {
  const start = buckle(-.01), snap = buckle(.09), final = buckle(2);
  assert.deepEqual(start, { a: 0, b: 0, c: 0, shiver: 0 });
  assert.ok(snap.a > snap.b && snap.c === 0, 'the primary buckle precedes the secondary folds');
  near(final.a, 1); near(final.b, 1); near(final.c, 1); near(final.shiver, 0);
  near(deformCan(0, 1, final).z, deformCan(0, 1, start).z);
  assert.ok(deformCan(0, .5, final).z < deformCan(0, .5, start).z - .23);
  assert.ok(deformCan(0, 0, final).y > deformCan(0, 0, start).y + .6);
});

test('the wall stays attached to the rigid ends as the base walks inward', () => {
  for (const w of [.09, .22, .36, .71, 1.5]) {
    const state = buckle(w);
    const foot = footPose(state);
    for (let j = 0; j < 32; j++) {
      const a = j / 32 * Math.PI * 2;
      const height = deformCan(a, 0, state);
      const r = canRadius(0);
      near(height.x, foot.x + Math.sin(a) * r * Math.cos(foot.rotation));
      near(height.y, foot.y + Math.sin(a) * r * Math.sin(foot.rotation));
      near(height.z, Math.cos(a) * r);
      near(deformCan(a, 1, state).y, CAN_H / 2);
    }
  }
  assert.ok(eventClock(AIR_TIMING.snap + .3, 9) < eventClock(AIR_TIMING.hookSnap + .3, 0));
});

test('motion shutter exposures stay within the current shot', () => {
  let inMotion = 0;
  for (let frame = 0; frame < AIR_CRUSH.duration * 24; frame++) {
    const t = frame / 24;
    const edit = cutAt(t, AIR_CRUSH);
    const samples = shutterTimes(t, edit);
    assert.ok(samples.length === 1 || samples.length === 2);
    if (samples.length === 2) inMotion++;
    for (const sample of samples) assert.equal(cutAt(sample, AIR_CRUSH).index, edit.index);
  }
  assert.ok(inMotion > 30 && inMotion < 85);
});

test('splash droplets burst out, fall under gravity, and do not continue below the surface', () => {
  const v = 3.11, g = 10.5;
  near(splashHeight(v / g, v, g), v * v / (2 * g));
  assert.equal(splashHeight(-.01, v, g), 0);
  assert.equal(splashHeight(2, v, g), 0);
});

test('the film has frame-aligned cuts, bounded captions and a downloadable production brief', async () => {
  for (const { at } of AIR_CRUSH.shots) near(at * 24, Math.round(at * 24));
  AIR_CRUSH_CAPTIONS.forEach(([start, end, ...lines], i) => {
    assert.ok(start >= (AIR_CRUSH_CAPTIONS[i - 1]?.[1] ?? 0) && start < end && end <= AIR_CRUSH.duration);
    assert.ok(lines.length <= 2 && lines.every((line) => line.length <= 30));
  });
  const script = await readFile(new URL(`../public${AIR_CRUSH.sample}`, import.meta.url), 'utf8');
  assert.ok(script.includes('Is can ko kisi ne dabaya nahi. Phir ye pichak kaise gaya?'));
  assert.ok(script.includes('Can ko hawa ne kuchla.'));
});
