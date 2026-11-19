import assert from 'node:assert/strict';
import { test } from 'node:test';
import { cutAt, fallingBody, FILE_TILES, fileDropCue, hingeAngle, keplerPosition, LAMP_TRAVEL, MOON_ORBIT } from '../tools/demo-render/motion.js';
import { DEMOS } from '../src/demos.js';

const close = (value, expected, tolerance = 1e-6) => assert.ok(Math.abs(value - expected) < tolerance, `${value} ≠ ${expected}`);

test('file motion follows free fall, loses impact energy, and never crosses the contact plane', () => {
  const setup = { height: .81, gravity: 10.8, restitution: .25 };
  const at = Math.sqrt(2 * setup.height / setup.gravity);
  const before = fallingBody(at - 1e-7, setup);
  const after = fallingBody(at + 1e-7, setup);
  assert.equal(before.contacts, 0);
  assert.equal(after.contacts, 1);
  close(after.velocity / -before.velocity, setup.restitution, 1e-4);
  const bouncePeak = fallingBody(at + after.velocity / setup.gravity, setup);
  close(bouncePeak.height, setup.height * setup.restitution ** 2, 1e-4);
  for (let i = 0; i < 300; i++) assert.ok(fallingBody(i / 144, setup).height >= 0);
  assert.deepEqual(fallingBody(5, setup), { height: 0, velocity: 0, contacts: 4 });
});

test('each storage impact cue matches the position used by the shot', () => {
  for (let index = 0; index < FILE_TILES; index++) {
    const cue = fileDropCue(index);
    const age = cue.impactAt - cue.release;
    close(fallingBody(age, cue).height, 0);
  }
});

test('lamp reaches its resting angle within the authored mechanical travel', () => {
  const design = LAMP_TRAVEL;
  close(hingeAngle(0, design), design.from);
  close(hingeAngle(4, design), design.to);
  for (let i = 0; i < 240; i++) {
    const angle = hingeAngle(i / 96, design);
    assert.ok(angle >= design.min && angle <= design.max);
  }
});

test('elliptical orbit clears the moon and moves faster near periapsis', () => {
  const shape = { ...MOON_ORBIT, phase: 0 };
  const near = keplerPosition(0, shape);
  const far = keplerPosition(shape.period / 2, shape);
  const lap = keplerPosition(shape.period, shape);
  close(near.radius, shape.a * (1 - shape.e));
  close(far.radius, shape.a * (1 + shape.e));
  close(lap.x, near.x);
  close(lap.z, near.z);
  close(near.speed / far.speed, (1 + shape.e) / (1 - shape.e));
  for (let i = 0; i <= 120; i++) {
    const advance = keplerPosition(i * shape.period / 120, shape);
    assert.ok(advance.radius - .82 > 1.47, 'craft hull bound must not intersect moon');
  }
});

test('the cinematography cuts exactly on the editorial cue boundaries', () => {
  for (const film of DEMOS) {
    assert.equal(cutAt(0, film).index, 0);
    for (let i = 1; i < film.shots.length; i++) {
      const stamp = film.shots[i].at;
      assert.equal(cutAt(stamp - 1e-4, film).index, i - 1);
      const cut = cutAt(stamp, film);
      assert.equal(cut.index, i);
      assert.equal(cut.progress, 0);
      assert.equal(cut.age, 0);
    }
    assert.equal(cutAt(film.duration, film).progress, 1);
  }
});
