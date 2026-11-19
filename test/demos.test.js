import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { DEMOS, demoAssetName, findDemo } from '../src/demos.js';
import { buildPrompt } from '../src/prompts.js';

test('planned film cues are ordered, and every demo has a matching builder preset', () => {
  assert.equal(new Set(DEMOS.map(({ id }) => id)).size, DEMOS.length);
  for (const film of DEMOS) {
    assert.equal(findDemo(film.id), film);
    assert.equal(film.shots[0].at, 0);
    assert.ok(film.posterAt > 0 && film.posterAt < film.duration);
    film.shots.forEach(({ at, jumpTo, shotNote }, i) => {
      const end = film.shots[i + 1]?.at ?? film.duration;
      assert.ok(at < film.duration && (!i || at > film.shots[i - 1].at));
      assert.ok(at < jumpTo && jumpTo < end, 'the player shortcut must land inside its shot');
      assert.ok(shotNote.length > 0);
    });
    assert.ok(buildPrompt(film.preset).text.includes(film.preset.visualDirection));
  }
  assert.equal(findDemo('no-such-film'), undefined);
});

test('each gallery card links a locally served MP4 and its poster', async () => {
  const index = await readFile(new URL('../index.html', import.meta.url), 'utf8');
  for (const { id } of DEMOS) {
    const videoName = demoAssetName(id, 'mp4');
    const posterName = demoAssetName(id, 'webp');
    const movie = await readFile(new URL(`../public/demos/${videoName}`, import.meta.url));
    const cover = await readFile(new URL(`../public/demos/${posterName}`, import.meta.url));
    assert.equal(movie.toString('ascii', 4, 8), 'ftyp');
    assert.equal(cover.toString('ascii', 8, 12), 'WEBP');
    assert.ok(index.includes(`data-demo="${id}" href="/demos/${videoName}"`));
    assert.ok(index.includes(`src="/demos/${posterName}"`));
    assert.ok(index.includes(`data-demo-preset="${id}"`));
  }
});


test('the featured film in the hero is the same published cut as the gallery', async () => {
  const index = await readFile(new URL('../index.html', import.meta.url), 'utf8');
  assert.ok(index.includes(`data-demo="air-crush" href="/demos/${demoAssetName('air-crush', 'mp4')}" aria-label="Play Who Crushed the Can?"`));
  assert.match(index, /<details class="viewer-shots" id="demo-shot-guide">/);
});
