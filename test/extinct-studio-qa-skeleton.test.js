import test from 'node:test';
import assert from 'node:assert/strict';
import {
  VIDEO_QA_ITEMS, AUDIO_QA_ITEMS, ALL_QA_ITEMS,
  runSkeleton, toGateReceipt,
} from '../tools/extinct-studio/qa-skeleton.js';

test('the check lists cover the doc\'s Q — Quality assurance list', () => {
  const videoIds = VIDEO_QA_ITEMS.map((i) => i.id);
  for (const id of ['frame-count', 'fps', 'black-frames', 'duplicate-frames', 'freeze-frames', 'dropped-frames', 'color-range', 'duration-audio-video', 'clipping', 'caption-overflow', 'safe-area', 'ocr-readability', 'scene-change-continuity', 'visual-diff', 'phone-size-playback']) {
    assert.ok(videoIds.includes(id), `missing video qa item '${id}'`);
  }
  const audioIds = AUDIO_QA_ITEMS.map((i) => i.id);
  for (const id of ['lufs', 'true-peak', 'aac-re-encode', 'mono-compatibility', 'phone-speaker-review']) {
    assert.ok(audioIds.includes(id), `missing audio qa item '${id}'`);
  }
  assert.equal(ALL_QA_ITEMS.length, VIDEO_QA_ITEMS.length + AUDIO_QA_ITEMS.length);
});

test('the skeleton reports every check as unavailable in this environment — no fake pass', () => {
  const report = runSkeleton({ projectId: 'demo-project', generatedAt: '2026-11-21T10:00:00.000Z' });
  assert.equal(report.honestyNote.length > 20, true);
  assert.equal(report.video.every((c) => c.status === 'unavailable'), true);
  assert.equal(report.audio.every((c) => c.status === 'unavailable'), true);
  assert.equal(report.overall.ok, 0);
  assert.equal(report.qaPasses, false);
  const receipt = toGateReceipt(report);
  assert.equal(receipt.videoOk, false);
  assert.equal(receipt.audioOk, false);
  // honest note must not read as a pass
  assert.match(report.honestyNote, /No render/);
});

test('real probe results are injected via probeOverrides and honored', () => {
  const overrides = {
    'frame-count': { status: 'ok', observed: 912 },
    'fps': { status: 'ok', observed: 24 },
    'black-frames': { status: 'fail', reason: '2 black frames found' },
    'fps': { status: 'ok', observed: 24 },
  };
  const report = runSkeleton({ probeOverrides: overrides });
  const frameCount = report.video.find((c) => c.id === 'frame-count');
  assert.equal(frameCount.status, 'ok');
  assert.equal(frameCount.observed, 912);
  const black = report.video.find((c) => c.id === 'black-frames');
  assert.equal(black.status, 'fail');
  assert.equal(report.qaPasses, false);
});

test('a bogus probeOverride is not honored — it falls back to unavailable', () => {
  const report = runSkeleton({ probeOverrides: { 'frame-count': { status: 'invented' } } });
  assert.equal(report.video.find((c) => c.id === 'frame-count').status, 'unavailable');
});
