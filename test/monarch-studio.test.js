import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import config from '../vite.config.js';
import { AIR_CRUSH } from '../src/air-crush.js';

const read = (name) => readFile(new URL(`../${name}`, import.meta.url), 'utf8');
const studioEntry = new URL('..' + AIR_CRUSH.studio + 'index.html', import.meta.url);

test('Monarch Studio is a separate build entry linked from Top1 and uses the original master', async () => {
  assert.equal(config.build.rollupOptions.input.monarch, fileURLToPath(studioEntry));
  const [home, studio] = await Promise.all([read('index.html'), readFile(studioEntry, 'utf8')]);
  assert.ok(home.includes(`href=".${AIR_CRUSH.studio}"`));
  assert.match(studio, /<title>Monarch Studio/);
  assert.ok(studio.includes(`href="/demos/${AIR_CRUSH.asset}.mp4" download`));
  assert.ok(studio.includes(`poster="/demos/${AIR_CRUSH.asset}.webp"`));
  assert.ok(studio.includes(`href="${AIR_CRUSH.sample}" download`));
  assert.ok(studio.includes(`href="../?demo=${AIR_CRUSH.id}#builder"`));
  const videoTag = studio.match(/<video\b[^>]+>/)?.[0];
  assert.ok(videoTag?.includes('playsinline'));
  assert.ok(videoTag.includes('preload="none"'));
  assert.doesNotMatch(videoTag, /\bsrc=/, 'load no video bytes before a playback gesture');
});

test('standout shot links use the same in-shot cues as the renderer and gallery', async () => {
  const studio = await readFile(studioEntry, 'utf8');
  const links = [...studio.matchAll(/href="([^\"]+#t=([^\"]+))" data-studio-shot="(\d+)"/g)];
  assert.equal(links.length, 3);
  for (const [, href, time, index] of links) {
    assert.equal(Number(time), AIR_CRUSH.shots[index].jumpTo);
    assert.equal(href, `/demos/${AIR_CRUSH.asset}.mp4#t=${time}`);
  }
});
