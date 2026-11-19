#!/usr/bin/env node
/**
 * Capacity + pricing reality check.
 *
 * Chalane ka tareeqa:
 *   node services/tools/render-budget.mjs
 *   node services/tools/render-budget.mjs --spf 2.5 --human 8 --hours 6
 *
 * DO cheezein alag hain, inhe mix mat karo:
 *   1. MACHINE time  — render (background mein chalta hai, aap so sakte ho)
 *   2. HUMAN time    — script, modelling, lighting, timing, revisions
 *
 * Aapki capacity HUMAN time se decide hoti hai, machine se nahi.
 * Yahan tak ke machine free ho, aap din mein 1 film se zyada theek se
 * nahi bana sakte — aur quality giraye baghair 2 bhi mushkil hai.
 *
 * Defaults conservative hain. Apna asli number daalo.
 */

const args = process.argv.slice(2);
const arg = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] !== undefined ? Number(args[i + 1]) : fallback;
};

const FPS = 24;
const SPF = arg('spf', 2.5);              // seconds per frame, software WebGL
const HUMAN_DAYS = arg('days', 5);        // productive days per week
const HUMAN_HOURS = arg('hours', 6);      // focused hours per day (not 8 — asli duniya)
const MACHINE_HOURS = arg('machine-hours', 14); // machine kitne ghante available

const product = [
  { name: '15s Short',    seconds: 15, humanHours: 4,  pkr: 25000, usd: 150 },
  { name: '30s Standard', seconds: 30, humanHours: 7,  pkr: 45000, usd: 280 },
  { name: '50s Deep',     seconds: 50, humanHours: 12, pkr: 70000, usd: 450 },
];

const machineHours = (s) => (s * FPS * SPF) / 3600;
const pad = (s, n) => String(s).padEnd(n);
const padS = (s, n) => String(s).padStart(n);

console.log('\n  CAPACITY — asli numbers');
console.log('  ' + '═'.repeat(64));
console.log(`  Machine:  ${SPF}s/frame @ ${FPS}fps, ${MACHINE_HOURS}h/day available`);
console.log(`  Human:    ${HUMAN_HOURS}h/day × ${HUMAN_DAYS} days = ${HUMAN_HOURS * HUMAN_DAYS}h/week`);
console.log('  ' + '═'.repeat(64) + '\n');

console.log('  ' + pad('Film', 14) + padS('Frames', 7) + padS('Machine', 10) + padS('Human', 8) + padS('/week', 8) + padS('/month', 8));
console.log('  ' + '─'.repeat(64));

const weeklyHuman = HUMAN_HOURS * HUMAN_DAYS;

for (const p of product) {
  const frames = p.seconds * FPS;
  const mh = machineHours(p.seconds);
  // Machine bottleneck: ek din mein kitni render ho sakti hain (background)
  const perDayByMachine = MACHINE_HOURS / mh;
  // Human bottleneck: poore hafte mein kitni bana sakte ho
  const perWeek = Math.floor(Math.min(weeklyHuman / p.humanHours, perDayByMachine * HUMAN_DAYS));
  const perMonth = perWeek * 4;
  console.log(
    '  ' + pad(p.name, 14) + padS(frames, 7) + padS(mh.toFixed(2) + 'h', 10) +
    padS(p.humanHours + 'h', 8) + padS(perWeek, 8) + padS(perMonth, 8)
  );
}

console.log('  ' + '─'.repeat(64));
console.log('\n  Bottleneck: HUMAN time. Machine aapka intezaar karega, aap machine ka nahi.\n');

// Revenue
console.log('  ' + '═'.repeat(64));
console.log('  MONTHLY REVENUE — realistic (quality giraye baghair)');
console.log('  ' + '═'.repeat(64) + '\n');

for (const p of product) {
  const mh = machineHours(p.seconds);
  const perWeek = Math.floor(Math.min(weeklyHuman / p.humanHours, (MACHINE_HOURS / mh) * HUMAN_DAYS));
  const perMonth = perWeek * 4;
  const pkrHour = p.pkr / p.humanHours;
  const usdHour = p.usd / p.humanHours;
  console.log(
    '  ' + pad(p.name, 14) +
    padS(perMonth + ' films/mo', 16) +
    padS('PKR ' + (perMonth * p.pkr).toLocaleString('en-PK'), 18) +
    padS('| $' + (perMonth * p.usd).toLocaleString('en-US'), 12)
  );
  console.log(
    '  ' + pad('', 14) +
    padS(`PKR ${Math.round(pkrHour).toLocaleString('en-PK')}/hr`, 16) +
    padS(`$${Math.round(usdHour)}/hr`, 18) +
    '   ← effective rate'
  );
}

console.log('\n  ' + '─'.repeat(64));
console.log('  ⚠  Effective rate PKR 1,500/hr se kam hai? Price badhao.');
console.log('     $25/hr se kam hai? International market undervaluing ho rahe ho.');
console.log('  ' + '─'.repeat(64));

// Actual films
console.log('\n  AAPKI MAUJOODA FILMS — machine time only\n');
const actual = [
  { name: 'air-crush (29s)',     seconds: 29, mb: 13.7 },
  { name: 'reflector (50s)',     seconds: 50, mb: 18.7 },
  { name: 'halo lamp (10s)',     seconds: 10, mb: 1.8 },
  { name: 'phone storage (11s)', seconds: 11, mb: 2.1 },
  { name: 'last signal (12s)',   seconds: 12, mb: 2.2 },
];

for (const f of actual) {
  const frames = f.seconds * FPS;
  console.log(
    '  ' + pad(f.name, 22) + padS(frames + ' frames', 12) +
    padS('~' + machineHours(f.seconds).toFixed(1) + 'h render', 16) +
    padS(f.mb + ' MB', 9)
  );
}

console.log('\n  ' + '═'.repeat(64));
console.log('  Ye ESTIMATE hai. Asli number ke liye ek film render karo,');
console.log('  waqt naapo, phir --spf ke saath dobara chalao:\n');
console.log('    CHROMIUM=... FFMPEG=... npm run render:demos -- halo-desk-lamp\n');
console.log('  Aur human hours track karo — har project ke baad likho ke');
console.log('  kitne ghante lage. 3 projects ke baad aapka asli rate pata chalega.\n');

// Sanity check
const thirty = product[1];
const r = (thirty.usd / thirty.humanHours);
if (r >= 45) {
  console.log('  ✓ Pricing healthy hai ($' + Math.round(r) + '/hr effective).');
} else if (r >= 30) {
  console.log('  ~ Pricing theek hai (' + Math.round(r) + '/hr). $45+/hr par le jao.');
} else {
  console.log('  ⚠ Pricing kam hai ($' + Math.round(r) + '/hr). Price badhao ya scope ghatao.');
}
console.log('');
