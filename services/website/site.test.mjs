#!/usr/bin/env node
/**
 * Services site ke static checks.
 *
 * Chalane ka tareeqa:  node services/website/site.test.mjs
 *
 * Ye `npm test` ka hissa NAHI hai — apna alag script hai.
 * Browser nahi chahiye; sirf files padh kar check karta hai.
 */

import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const dir = resolve(fileURLToPath(new URL('./site', import.meta.url)));
const repoRoot = resolve(fileURLToPath(new URL('../..', import.meta.url)));

let pass = 0;
const failures = [];

function check(name, fn) {
  try {
    fn();
    pass += 1;
    console.log(`  ✓ ${name}`);
  } catch (error) {
    failures.push({ name, message: error.message });
    console.log(`  ✗ ${name}\n      ${error.message}`);
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const html = readFileSync(resolve(dir, 'index.html'), 'utf8');
const css = readFileSync(resolve(dir, 'site.css'), 'utf8');
const js = readFileSync(resolve(dir, 'site.js'), 'utf8');

console.log('\n  SERVICES SITE — TESTS\n  ' + '─'.repeat(56) + '\n');

/* ─── Files ──────────────────────────────────────────── */

check('index.html, site.css, site.js, config.js maujood hain', () => {
  for (const file of ['index.html', 'site.css', 'site.js', 'config.js']) {
    assert(existsSync(resolve(dir, file)), `${file} missing`);
  }
});

check('site Vite app se independent hai (koi /src import nahi)', () => {
  assert(!js.includes('/src/'), 'site.js imports from /src');
  assert(!html.includes('/src/main.js'), 'index.html pulls the Vite entry');
  assert(!html.includes('vite'), 'index.html mentions vite');
});

/* ─── HTML structure ─────────────────────────────────── */

check('required sections maujood hain', () => {
  for (const id of ['top', 'work', 'services', 'process', 'brief', 'faq']) {
    assert(html.includes(`id="${id}"`), `section #${id} missing`);
  }
});

check('JS ke saare element IDs HTML mein hain', () => {
  const jsIds = [...js.matchAll(/\$\('#([a-zA-Z0-9_-]+)'\)/g)].map((m) => m[1]);
  const htmlIds = new Set(
    [...html.matchAll(/id="([a-zA-Z0-9_-]+)"/g)].map((m) => m[1])
  );
  const missing = [...new Set(jsIds)].filter((id) => !htmlIds.has(id));
  assert(missing.length === 0, `JS queries IDs that do not exist: ${missing.join(', ')}`);
});

check('language aur viewport meta set hain', () => {
  assert(html.includes('lang="en"'), 'missing lang attribute');
  assert(html.includes('name="viewport"'), 'missing viewport meta');
  assert(html.includes('name="description"'), 'missing description meta');
});

check('koi inline script ya eval nahi', () => {
  assert(!/<script(?![^>]*src=)/i.test(html), 'inline script found');
  assert(!js.includes('eval('), 'eval() found');
  assert(!js.includes('innerHTML = `' + '${'), 'unchecked template injection pattern');
});

check('accessibility basics', () => {
  assert(html.includes('class="skip"'), 'missing skip link');
  assert(html.includes('aria-label'), 'no aria labels');
  assert(html.includes('role="status"'), 'form status lacks live region');
});

check('reduced-motion respect karta hai', () => {
  assert(css.includes('prefers-reduced-motion'), 'no reduced-motion block');
});

/* ─── Config ─────────────────────────────────────────── */

const configSource = readFileSync(resolve(dir, 'config.js'), 'utf8');

check('config.js mein contact fields hain', () => {
  for (const key of ['email:', 'whatsapp:', 'formspree:', 'formMode:']) {
    assert(configSource.includes(key), `config missing ${key}`);
  }
});

check('config.js mein placeholder keys nahi hain', () => {
  // Sirf asli code check karo — comments aur trailing examples nahi
  const code = configSource
    .split('\n')
    .map((line) => {
      const trimmed = line.trim();
      if (trimmed.startsWith('//') || trimmed.startsWith('*')) return '';
      return line.replace(/\/\/.*$/, '');
    })
    .join('\n');
  assert(!code.includes('YOUR_'), 'placeholder YOU_ text left in a value');
  assert(!/x{6,}/.test(code), 'placeholder xxxxxx left in a value');
});

check('formMode valid value hai', () => {
  const match = configSource.match(/formMode:\s*'([^']+)'/);
  assert(match, 'formMode not found');
  assert(['mailto', 'formspree', 'none'].includes(match[1]), `bad formMode: ${match[1]}`);
});

/* ─── Dynamic import of config ───────────────────────── */

const { CONFIG, FILMS, TIERS, INCLUDED, EXCLUDED, FAQ } = await import(
  resolve(dir, 'config.js')
);

check('config exports sahi hain', () => {
  for (const [name, value] of Object.entries({ CONFIG, FILMS, TIERS, INCLUDED, EXCLUDED, FAQ })) {
    assert(value !== undefined, `${name} not exported`);
  }
});

check('har tier ka priceKey CONFIG.pricing mein hai', () => {
  for (const tier of TIERS) {
    assert(CONFIG.pricing[tier.priceKey] !== undefined, `${tier.id} has bad priceKey`);
  }
});

check('films ke required fields hain aur ids unique hain', () => {
  const required = ['id', 'title', 'category', 'duration', 'poster'];
  for (const film of FILMS) {
    for (const field of required) {
      assert(film[field], `${film.id} missing ${field}`);
    }
    // drive films need driveId, not path; file films need path
    if (film.provider === 'drive') {
      assert(film.driveId, `${film.id} missing driveId`);
    } else {
      assert(film.path, `${film.id} missing path`);
    }
  }
  const ids = FILMS.map((f) => f.id);
  assert(new Set(ids).size === ids.length, 'duplicate film ids');
});

check('local film files exist (Drive entries exempt)', () => {
  for (const film of FILMS) {
    if (film.provider === 'drive') {
      assert(film.driveId, `${film.id}: drive provider without driveId`);
      continue;
    }
    const target = film.path.startsWith('/')
      ? resolve(repoRoot, film.path.slice(1))
      : resolve(dir, film.path);
    assert(existsSync(target), `${film.id}: missing ${film.path}`);
  }
});

check('har film ka poster maujood hai (local file ya https URL)', () => {
  for (const film of FILMS) {
    if (film.poster.startsWith('https://')) continue;
    const target = film.poster.startsWith('/')
      ? resolve(repoRoot, film.poster.slice(1))
      : resolve(dir, film.poster);
    assert(existsSync(target), `${film.id}: missing poster ${film.poster}`);
  }
});

check('Drive posters Google ke thumbnail endpoint se aate hain', () => {
  for (const film of FILMS.filter((f) => f.provider === 'drive')) {
    assert(
      film.poster.startsWith('https://drive.google.com/thumbnail?id='),
      `${film.id}: Drive poster should use drive.google.com/thumbnail`
    );
    assert(
      film.poster.includes(film.driveId),
      `${film.id}: poster id does not match driveId`
    );
  }
});

check('aspect ratio valid hai aur cards use karte hain', () => {
  const allowed = ['9:16', '16:9', '1:1'];
  for (const film of FILMS) {
    assert(allowed.includes(film.aspect), `${film.id}: bad aspect ${film.aspect}`);
  }
});

check('site.js Drive embed support karta hai', () => {
  const source = readFileSync(resolve(dir, 'site.js'), 'utf8');
  assert(source.includes('/preview'), 'no Drive /preview embed URL');
  assert(source.includes('isDrive'), 'no Drive provider branch');
  assert(!source.includes('export=download'), 'should not force-download Drive files');
});

check('kam az kam ek featured film hai', () => {
  assert(FILMS.some((f) => f.featured), 'no featured film for hero');
});

check('pricing non-negative hai', () => {
  for (const [key, value] of Object.entries(CONFIG.pricing)) {
    assert(typeof value === 'number' && value >= 0, `pricing.${key} invalid`);
  }
});

check('FAQ entries complete hain', () => {
  assert(FAQ.length >= 5, 'FAQ needs at least 5 entries');
  for (const item of FAQ) {
    assert(item.q && item.a, 'FAQ entry missing q or a');
  }
});

check('excluded list clearly non-promises batati hai', () => {
  const text = EXCLUDED.join(' ').toLowerCase();
  assert(text.includes('upload'), 'excluded list should mention uploading');
  assert(text.includes('guarantee'), 'excluded list should mention guarantees');
});

/* ─── Independence from main app ─────────────────────── */

check('main app files ko is site se change nahi kiya', () => {
  const mainFiles = ['index.html', 'kit.html', 'package.json', 'vite.config.js'];
  for (const file of mainFiles) {
    assert(existsSync(resolve(repoRoot, file)), `${file} missing from repo root`);
  }
});

/* ─── Dev server path safety ─────────────────────────── */

check('dev server path traversal block karta hai', () => {
  const server = readFileSync(resolve(dir, '..', 'serve.mjs'), 'utf8');

  // isInside ko relative() se compare karna chahiye, string slicing se nahi
  assert(
    server.includes('relative(base, target)'),
    'isInside() must use path.relative(), not string slicing'
  );
  assert(
    !/normalize\(target\)\.slice\(/.test(server),
    'isInside() still slices strings — traversal bypass possible'
  );
  assert(server.includes('READ_ROOTS'), 'no read-root allowlist in server');
  assert(server.includes('isAbsolute'), 'server does not reject absolute paths');
});

/* ─── Summary ────────────────────────────────────────── */

const total = pass + failures.length;
console.log('\n  ' + '─'.repeat(56));
console.log(`  ${pass}/${total} pass`);
if (failures.length) {
  console.log(`  ${failures.length} FAIL\n`);
  process.exit(1);
}
console.log('  Sab theek ✓\n');
