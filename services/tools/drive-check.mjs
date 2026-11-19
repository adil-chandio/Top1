#!/usr/bin/env node
/**
 * Google Drive setup checker.
 *
 * Chalane ka tareeqa:  node services/tools/drive-check.mjs
 *
 * Ye script koi credential MANGE GI NAHI aur koi upload nahi karti.
 * Sirf batati hai ke kya chahiye, kya missing hai, aur kaunsa rasta
 * aapke account ke liye chalega.
 *
 * Asli upload aap khud test karo — 1 KB file se.
 */

import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('../..', import.meta.url)));

const envPath = resolve(root, '.env');
const envExample = resolve(root, '.env.example');

const readEnv = (path) => {
  if (!existsSync(path)) return {};
  const out = {};
  for (const line of readFileSync(path, 'utf8').split('\n')) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)$/);
    if (m && !line.trim().startsWith('#')) out[m[1]] = m[2].trim();
  }
  return out;
};

const env = readEnv(envPath);
const has = (k) => Boolean(env[k] && env[k].length > 0);

console.log('\n  GOOGLE DRIVE — SETUP CHECK');
console.log('  ' + '─'.repeat(58) + '\n');

if (!existsSync(envPath)) {
  console.log('  ✗ .env file nahi mili (repo root mein banao — already gitignored)\n');
} else {
  console.log('  ✓ .env file mili\n');
}

const paths = [
  {
    id: 'A',
    name: 'Workspace + Shared Drive (recommended)',
    needs: ['GOOGLE_SERVICE_ACCOUNT_JSON', 'GOOGLE_SHARED_DRIVE_ID'],
    explain: [
      'Business/Workspace account chahiye (free Gmail se nahi hoga)',
      'Shared Drive banao, service account ko Content Manager banao',
      'Service account JSON key server par rakho, repo mein NAHI',
      'GOOGLE_SERVICE_ACCOUNT_JSON = key file ka path',
      'GOOGLE_SHARED_DRIVE_ID = Shared Drive URL se',
    ],
  },
  {
    id: 'B',
    name: 'OAuth as user (normal Gmail)',
    needs: ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_REFRESH_TOKEN'],
    explain: [
      'Google Cloud project + OAuth consent screen',
      'Scope: drive.file (sirf app ki banayi files)',
      'Buyer ek baar consent deta hai',
      'Refresh token encrypted store karo',
    ],
  },
];

for (const p of paths) {
  const missing = p.needs.filter((k) => !has(k));
  const ready = missing.length === 0;
  console.log(`  ${ready ? '✓' : '✗'} Path ${p.id}: ${p.name}`);
  if (ready) {
    console.log('      Sab variables mil gaye.');
  } else {
    console.log(`      Missing: ${missing.join(', ')}`);
    for (const line of p.explain) console.log(`        · ${line}`);
  }
  console.log('');
}

// Trap warning
console.log('  ' + '─'.repeat(58));
console.log('  ⚠  TRAP: Service account ko PERSONAL My Drive mein upload mat');
console.log('     karwao. Service accounts ka apna storage quota nahi hota —');
console.log('     "Service Accounts do not have storage quota" error aayega.');
console.log('     Shared Drive (Workspace) ya OAuth (personal) — bas ye do.');
console.log('  ' + '─'.repeat(58) + '\n');

// Test checklist
console.log('  PEHLA TEST (aaj hi karo, 5 minute):\n');
console.log('    1. 1 KB text file banao: echo "test" > t.txt');
console.log('    2. Apne chosen path se upload karo');
console.log('    3. Drive UI mein dekho file dikhi');
console.log('    4. Delete karo');
console.log('    5. Agar ye fail ho → pipeline kabhi nahi chalega. Abhi pata karo.\n');

// .env.example snippet
if (!existsSync(envExample)) {
  console.log('  Tip: .env.example banao (ye commit ho sakti hai):\n');
  console.log('    # Drive — Path A');
  console.log('    GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/key.json');
  console.log('    GOOGLE_SHARED_DRIVE_ID=0Axxxxxxxx');
  console.log('    # Drive — Path B');
  console.log('    GOOGLE_CLIENT_ID=');
  console.log('    GOOGLE_CLIENT_SECRET=');
  console.log('    GOOGLE_REFRESH_TOKEN=\n');
}

console.log('  Detail: services/drive/STRUCTURE.md\n');
