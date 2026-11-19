#!/usr/bin/env node
/**
 * Repo ka asli inventory — kya maujood hai, kya nahi.
 *
 * Chalane ka tareeqa:  node services/tools/inventory.mjs
 *
 * Ye script sirf PADHTI hai. Kuch change nahi karti.
 */

import { existsSync, statSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('../..', import.meta.url)));

const check = (label, path, note = '') => ({
  label,
  path,
  exists: existsSync(join(root, path)),
  note,
});

const groups = [
  {
    name: 'PORTFOLIO (Offer A ka proof)',
    items: [
      check('Can film — 29s Cinema Edition', 'public/demos/air-crush-cinema-edition.mp4'),
      check('Reflector film — 50s', 'public/demos/reflector-no-battery.mp4'),
      check('Halo lamp — 10s', 'public/demos/halo-desk-lamp-cinema-cut.mp4'),
      check('Phone storage — 11s', 'public/demos/phone-storage-cinema-cut.mp4'),
      check('Last signal — 12s', 'public/demos/last-signal-cinema-cut.mp4'),
      check('Posters (webp)', 'public/demos/air-crush-cinema-edition.webp'),
    ],
  },
  {
    name: 'RENDER ENGINE',
    items: [
      check('Render orchestrator', 'tools/render-demos.mjs'),
      check('3D scenes', 'tools/demo-render/scenes.js'),
      check('Blender pipeline (gecko)', 'tools/gecko/render.mjs'),
      check('Soundtrack synth', 'tools/soundtrack.mjs'),
    ],
  },
  {
    name: 'QA / VERIFICATION (aapka differentiator)',
    items: [
      check('Reflector verifier', 'tools/verify-reflector.mjs'),
      check('Gecko audit', 'tools/gecko/natural/audit.py'),
      check('Film motion tests', 'test/film-motion.test.js'),
    ],
  },
  {
    name: 'PRODUCTION DOCS',
    items: [
      check('Can production file', 'monarch-studio/PRODUCTION.md'),
      check('Can blueprint (free sample)', 'public/samples/air-crush-blueprint.md'),
      check('Reflector blueprint (free sample)', 'public/samples/reflector-blueprint.md'),
      check('25-second prompt sample', 'public/samples/25-second-short.md'),
    ],
  },
  {
    name: 'WEBSITE',
    items: [
      check('Homepage', 'index.html'),
      check('Kit page', 'kit.html'),
      check('Monarch Studio', 'monarch-studio/index.html'),
      check('Reflector screening', 'monarch-studio/reflector/index.html'),
    ],
  },
  {
    name: 'AGENTIC WORKFLOW (Offer C — banna hai)',
    items: [
      check('Shot plan schema', 'services/automation/shot-plan.schema.json', 'spec ready'),
      check('Moves library', 'automation/moves', 'BANANA HAI'),
      check('Model library', 'automation/models', 'BANANA HAI'),
      check('Pipeline orchestrator', 'automation/pipeline.mjs', 'BANANA HAI'),
      check('Drive delivery', 'automation/deliver.mjs', 'BANANA HAI'),
      check('QA report generator', 'automation/qa.mjs', 'BANANA HAI'),
    ],
  },
  {
    name: 'BUSINESS',
    items: [
      check('Offer A — 3D video', 'services/offers/OFFER-A-3D-VIDEO.md'),
      check('Offer B — process kit', 'services/offers/OFFER-B-PROCESS-KIT.md'),
      check('Offer C — agentic', 'services/offers/OFFER-C-AGENTIC-WORKFLOW.md'),
      check('Contract template', 'services/ops/CONTRACT-TEMPLATE.md'),
      check('Pricing', 'services/ops/PRICING.md'),
      check('Email/contact channel', 'CONTACT.md', 'GALAT — abhi maujood nahi'),
    ],
  },
];

console.log('\n  TOP1 — INVENTORY\n  ' + '─'.repeat(58) + '\n');

for (const group of groups) {
  console.log(`  ${group.name}`);
  for (const item of group.items) {
    const mark = item.exists ? '  ✓' : '  ✗';
    const pad = ' '.repeat(Math.max(0, 46 - item.label.length));
    const note = item.note ? `  ← ${item.note}` : '';
    console.log(`${mark} ${item.label}${pad}${note}`);
  }
  console.log('');
}

// Video sizes
const demos = join(root, 'public/demos');
if (existsSync(demos)) {
  const mp4s = readdirSync(demos).filter((f) => f.endsWith('.mp4'));
  const total = mp4s.reduce((sum, f) => sum + statSync(join(demos, f)).size, 0);
  console.log('  ' + '─'.repeat(58));
  console.log(`  ${mp4s.length} films, ${(total / 1024 / 1024).toFixed(1)} MB total\n`);
}

// Verdict
const ready = [
  'public/demos/air-crush-cinema-edition.mp4',
  'public/demos/reflector-no-battery.mp4',
  'tools/render-demos.mjs',
].every((p) => existsSync(join(root, p)));

console.log('  ' + '─'.repeat(58));
console.log(ready
  ? '  OFFER A: READY — do finished films + render engine maujood hain.'
  : '  OFFER A: portfolio ya engine missing hai.');
console.log('  OFFER B: SKELETON — outline hai, 8 files nahi.');
console.log('  OFFER C: NOT BUILT — architecture spec hai, code nahi.\n');
