import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import config from '../vite.config.js';
import { DEMOS, demoAssetName, findDemo } from '../src/demos.js';
import { REFLECTOR, REFLECTOR_BEATS, REFLECTOR_CAPTIONS, REFLECTOR_VO } from '../src/reflector.js';
import { buildPrompt } from '../src/prompts.js';
import { cutAt } from '../tools/demo-render/motion.js';
import {
  CORNER_EDGE, OPTIC_PATH, PLASTIC_IOR, RAY_IN, add3, cornerToBench, dot3,
  pathProgress, reflect, returnPower, scale3,
} from '../tools/demo-render/reflector-optics.js';

const read = (name, encoding) => readFile(new URL(`../${name}`, import.meta.url), encoding);
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-8, `${a} ≠ ${b}`);

test('the optic maintains geometry through exactly three TIR contacts and a separated return path', () => {
  const [entry, ...remainder] = OPTIC_PATH;
  const exit = remainder.pop();
  assert.equal(entry.kind, 'entry');
  assert.equal(exit.kind, 'exit');
  assert.deepEqual(remainder.map(({ face }) => face), [0, 1, 2]);
  for (const [i, hit] of remainder.entries()) {
    assert.equal(hit.kind, 'bounce');
    assert.equal(hit.point[hit.face], 0);
    assert.ok(hit.angle > Math.asin(1 / PLASTIC_IOR));
    const normal = [0, 1, 2].map((axis) => Number(axis === hit.face));
    const expected = reflect(OPTIC_PATH[i].direction, normal);
    hit.direction.forEach((component, j) => near(component, expected[j]));
  }
  for (const event of OPTIC_PATH) {
    assert.ok(event.point.every((coordinate) => coordinate >= 0));
    assert.ok(event.point.reduce((a, b) => a + b, 0) <= CORNER_EDGE + 1e-8);
    near(Math.hypot(...event.direction), 1);
  }
  near(cornerToBench(entry.point)[2], 0);
  near(cornerToBench(exit.point)[2], 0);
  near(dot3(cornerToBench(RAY_IN, true), cornerToBench(exit.direction, true)), -1);
  const displacement = add3(exit.point, scale3(entry.point, -1));
  const offset = add3(displacement, scale3(RAY_IN, -dot3(displacement, RAY_IN)));
  assert.ok(Math.hypot(...offset) > .1, 'opposite directions must not be drawn on the same line');
});

test('illustrative road return is aligned to the source and becomes dark with that source off', () => {
  const source = [0, 0, 1];
  near(returnPower(source, source, 1), 1);
  near(returnPower(source, source, 0), 0);
  assert.ok(returnPower([.5, 0, 1], source, 1) < .005);
  assert.ok(returnPower([.07, 0, 1], source, 1) > .85);
});

test('the ray trace never skips a segment and the sound cues land at each contact', () => {
  const { rayStart, rayEnter, hits, rayExit, returned } = REFLECTOR_BEATS;
  const anchors = [rayStart, rayEnter, ...hits, rayExit, returned];
  for (const [i, stamp] of anchors.entries()) {
    assert.deepEqual(pathProgress(stamp, anchors), Array.from({ length: 6 }, (_, n) => Number(n < i)));
    if (i > 0) assert.ok(stamp > anchors[i - 1]);
  }
  assert.equal(hits.length, 3);
  assert.deepEqual(hits.map((at) => cutAt(at, REFLECTOR).index), [12, 12, 12]);
  assert.equal(cutAt(REFLECTOR_BEATS.lampOff, REFLECTOR).index, 16);
  assert.equal(cutAt(REFLECTOR_BEATS.payoffOn, REFLECTOR).index, 17);
});

test('50-second edit has 18 frame-aligned setups, with readable captions and a separate prompt preset', () => {
  assert.equal(REFLECTOR.duration * 24, 1200);
  assert.equal(REFLECTOR.shots.length, 18);
  assert.equal(REFLECTOR.shots[0].at, 0);
  REFLECTOR.shots.forEach(({ at, jumpTo }, i) => {
    near(at * 24, Math.round(at * 24));
    assert.equal(cutAt(at, REFLECTOR).index, i);
    assert.equal(cutAt(jumpTo, REFLECTOR).index, i);
    assert.ok(jumpTo > at && jumpTo < REFLECTOR.duration);
  });
  REFLECTOR_CAPTIONS.forEach(([start, end, ...lines], i) => {
    assert.ok(start >= (REFLECTOR_CAPTIONS[i - 1]?.[1] ?? 0) && end > start && end < REFLECTOR.duration);
    assert.ok(lines.length <= 2 && lines.every((line) => line.length <= 29));
  });
  assert.equal(findDemo(REFLECTOR.id), REFLECTOR);
  assert.ok(!DEMOS.includes(REFLECTOR), 'Project 002 is a showcase, not a change to the store gallery');
  assert.match(buildPrompt(REFLECTOR.preset).text, /corner cube/);
});

test('Project 002 is discoverable from both sites with real local files and chapter links', async () => {
  const entry = new URL(`..${REFLECTOR.studio}index.html`, import.meta.url);
  const [page, studio, home, sample, movie, poster] = await Promise.all([
    readFile(entry, 'utf8'), read('monarch-studio/index.html', 'utf8'), read('index.html', 'utf8'),
    read(`public${REFLECTOR.sample}`, 'utf8'), read(`public/demos/${demoAssetName(REFLECTOR.id, 'mp4')}`),
    read(`public/demos/${demoAssetName(REFLECTOR.id, 'webp')}`),
  ]);
  assert.equal(config.build.rollupOptions.input.reflector, fileURLToPath(entry));
  assert.ok(home.includes(`href=".${REFLECTOR.studio}"`) && studio.includes('href="./reflector/"'));
  const video = page.match(/<video\b[^>]+>/)?.[0];
  assert.ok(video?.includes('playsinline') && video.includes('preload="none"'));
  assert.doesNotMatch(video, /\bsrc=/);
  assert.equal(movie.toString('ascii', 4, 8), 'ftyp');
  assert.equal(poster.toString('ascii', 8, 12), 'WEBP');
  assert.ok(page.includes(`href="/demos/${REFLECTOR.asset}.mp4" download`));
  assert.ok(page.includes(`href="${REFLECTOR.sample}" download`));
  assert.ok(page.includes('href="../../?demo=reflector#builder"'));
  const chapterLinks = [...page.matchAll(/#t=([\d.]+)" data-studio-shot="(\d+)"/g)];
  assert.equal(chapterLinks.length, 3);
  for (const [, t, i] of chapterLinks) assert.equal(Number(t), REFLECTOR.shots[i].jumpTo);
  for (const [, script] of REFLECTOR_VO) assert.ok(page.includes(script) && sample.includes(script));
});

test('the frame audit indexes the full native-rate reference, not a sparse sample', async () => {
  const [md, csv] = await Promise.all([
    read('public/samples/reflector-reference-audit.md', 'utf8'),
    read('public/samples/reflector-reference-frames.csv', 'utf8'),
  ]);
  const [header, ...rows] = csv.trim().split(/\r?\n/);
  assert.match(header, /^frame,seconds,luma,contrast,saturation,edges,delta,hist_diff/);
  assert.equal(rows.length, 1200);
  rows.forEach((line, i) => {
    const [frame, time] = line.split(',').map(Number);
    assert.equal(frame, i);
    assert.ok(Math.abs(time - i / 29.97) < .000002);
  });
  const ranges = [...md.matchAll(/^\| \d{2}(?:\.00–40\.04)? \| f(\d+)(?:–(\d+))? \|/gm)];
  assert.equal(ranges.length, 41);
  let next = 0;
  for (const [, first, last] of ranges) {
    assert.equal(Number(first), next);
    next = Number(last ?? first) + 1;
  }
  assert.equal(next, 1200);
});
