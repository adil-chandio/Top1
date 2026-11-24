import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../projects/huayuan/', import.meta.url));
const expected = {
  'coast_rocks_01.glb': '88167e72690e89b10b7a6108ab04dbc38adff7949b8b00f630007e8ef24a60ff',
  'coast_rocks_03.glb': '1c3e87e9c40c1745d116d82135b00fc399f9d8751d33eed18e0842277520fc13',
  'hallucigenia.glb': '2f1c725ab3410bc0b650ee442d7028555e63b51288fb8a6531997941dc8daa1e',
  'opabinia.glb': 'fb511c5c844507782e3a686ab0afedeb1b7792fd0b3301050e95d37a65ca0b62',
  'radiodont.glb': '147de95a18c771739f918e8ce0319c00fba560d6f415305f57fddc97b96f661a',
  'rock_07.glb': 'b4bbddfd12fcfe0fa9158a32a770d262780edb2bc0ebf787c87823b43b269910',
};
test('archived scene assets match recorded SHA-256 hashes', () => {
  for (const [name, hash] of Object.entries(expected)) {
    assert.equal(createHash('sha256').update(readFileSync(path.join(root, 'assets', name))).digest('hex'), hash, name);
  }
});
test('scene and history use the new section path and expected files exist', () => {
  for (const file of ['film.html', 'film.js', 'prototype.html', 'lookdev.js', 'PROJECT-STATUS.md', 'notes/SOURCE-AND-RECOVERY.md', 'notes/REVIEW-AND-TECHNICAL-PROOF.txt']) {
    assert.ok(existsSync(path.join(root, file)), file);
  }
  for (const file of ['film.js', 'lookdev.js']) {
    const text = readFileSync(path.join(root, file), 'utf8');
    assert.match(text, /\/tools\/extinct-channel\/projects\/huayuan\/assets\//);
    assert.doesNotMatch(text, /\/tools\/huayuan-production\/assets\//);
  }
});
