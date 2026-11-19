import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildBrief, buildPrompt, EXAMPLE } from '../src/prompts.js';

test('Roman Urdu sample has a script and shot plan prompt with three contiguous beats', () => {
  const { label, text } = buildPrompt(EXAMPLE);
  assert.equal(label, 'Roman Urdu · 25 sec · Explainer');
  assert.ok(text.includes(EXAMPLE.topic));
  assert.match(text, /Roman Urdu using Latin letters/);
  assert.deepEqual([...text.matchAll(/\((\d+–\d+)s\)/g)].map((match) => match[1]), ['0–4', '4–18', '18–25']);
  assert.match(text, /Exact voiceover.*On-screen caption.*Visual direction/);
});

test('the duration presets customize the running time and word budget', () => {
  for (const [duration, wordRange, beats] of [
    ['15', '25–33', ['0–3', '3–11', '11–15']],
    ['45', '80–100', ['0–5', '5–34', '34–45']],
  ]) {
    const { label, text } = buildPrompt({ ...EXAMPLE, duration });
    assert.match(label, new RegExp(`${duration} sec`));
    assert.ok(text.includes(`Aim for ${wordRange} spoken words`));
    assert.deepEqual([...text.matchAll(/\((\d+–\d+)s\)/g)].map((match) => match[1]), beats);
  }
});

test('product and story formats use different instructions and claims checks', () => {
  const promo = buildPrompt({ ...EXAMPLE, language: 'english', style: 'promo', topic: '  Desk   lamp  ' });
  assert.equal(promo.label, 'English · 25 sec · Product promo');
  assert.match(promo.text, /TOPIC\nDesk lamp\n/);
  assert.match(promo.text, /single product benefit/);
  assert.match(promo.text, /invent results, prices, ratings, or guarantees/);
  const story = buildPrompt({ ...EXAMPLE, style: 'story' });
  assert.match(story.text, /one visual payoff/);
  assert.match(story.text, /label fictional or composite scenes/);
});

test('prompt rejects blank and oversized topics or unknown options', () => {
  assert.throws(() => buildPrompt({ ...EXAMPLE, topic: ' \n ' }), /Enter a topic/);
  assert.throws(() => buildPrompt({ ...EXAMPLE, topic: 'a'.repeat(121) }), /characters/);
  assert.throws(() => buildPrompt({ ...EXAMPLE, duration: '90' }), /valid duration/);
  assert.throws(() => buildPrompt({ ...EXAMPLE, style: 'constructor' }), /valid format/);
  assert.throws(() => buildPrompt({ ...EXAMPLE, language: 'unknown' }), /valid language/);
});

test('custom brief captures scope and optionally preserves multi-line notes', () => {
  const values = { topic: 'Handmade lamp', audience: 'Small room renters', language: 'english', duration: '45' };
  const withoutNotes = buildBrief(values);
  assert.match(withoutNotes, /Audience: Small room renters/);
  assert.match(withoutNotes, /45 seconds, vertical/);
  assert.doesNotMatch(withoutNotes, /Tone, angle, or takeaway/);
  assert.match(withoutNotes, /not a rendered video/);
  assert.match(buildBrief({ ...values, notes: 'Calm tone\r\nShow the lamp switched on.' }), /Calm tone\nShow the lamp switched on/);
  assert.throws(() => buildBrief({ ...values, audience: ' ' }), /Enter an audience/);
});

test('an optional 3D direction is included only when supplied', () => {
  assert.doesNotMatch(buildPrompt(EXAMPLE).text, /VISUAL DIRECTION/);
  const { text } = buildPrompt({ ...EXAMPLE, visualDirection: '  Orbit a glossy violet phone.  ' });
  assert.match(text, /VISUAL DIRECTION\nOrbit a glossy violet phone\.\n/);
});
