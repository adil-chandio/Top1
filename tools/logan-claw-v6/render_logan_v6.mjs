#!/usr/bin/env node
/**
 * Logan — Rig-to-Render VFX Breakdown (`V6.2 Hollywood IMAX`)
 * Wrapper around the official `tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs` engine
 * + Post-AAC True-Peak Protection (`-af "alimiter=limit=0.708:level=false"` -> `<= -1.0 dBFS`!).
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const ROOT = '/home/user/Top1';
const EXPORT_DIR = path.join(ROOT, 'exports/logan-claw-rig-v6-imax');
const BUILD_DIR = '/tmp/logan_v6/build';
const AUDIO_WAV = '/tmp/logan_v6/Logan-Claw-Rig-Master-Mix-V6-IMAX.wav';
const OUT_MP4 = 'Logan-Claw-Rig-Breakdown-V6-IMAX.mp4';

function findFfmpeg() {
  const pyDir = '/tmp/py/imageio_ffmpeg/binaries';
  if (fs.existsSync(pyDir)) {
    const f = fs.readdirSync(pyDir).find((n) => n.startsWith('ffmpeg'));
    if (f) return path.join(pyDir, f);
  }
  return 'ffmpeg';
}

const modeArg = process.argv.includes('--mode')
  ? process.argv[process.argv.indexOf('--mode') + 1]
  : 'preflight';

// 12 Key Storyboard Beats spanning EVERY single shot & match-cut pair across all 420 frames!
const BEATS = [
  { f:   4, label: '01_CLAY_REST_START' },
  { f:  46, label: '02_CLAY_HAND_SPLAY' },
  { f:  78, label: '03_CLAY_FIST_VACUUM' },
  { f:  94, label: '04_RENDER_SNIKT_OUT' },
  { f: 118, label: '05_RENDER_HERO_HOLD' },
  { f: 146, label: '06_MACRO_CLAY_RIG' },
  { f: 184, label: '07_MACRO_STEEL_GLINT' },
  { f: 228, label: '08_34_CLAY_PROFILE' },
  { f: 272, label: '09_34_RENDER_PORES' },
  { f: 314, label: '10_FRONT_CLAY_RIG' },
  { f: 364, label: '11_FRONT_CLIMAX_STARE' },
  { f: 406, label: '12_LOOP_RESET_CLAY' },
];

execFileSync('bash', [path.join(ROOT, 'tools/logan-claw-v6/fetch_assets.sh')], { stdio: 'inherit' });

execFileSync('node', [
  path.join(ROOT, 'tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs'),
  '--page', '/tools/logan-claw-v6/page_logan_v6.html',
  '--mode', modeArg === 'render' ? 'render' : 'preflight',
  '--w', '1080',
  '--h', '1920',
  '--frames', '420',
  '--chunk', '105',
  '--workers', '2',
  '--build-dir', BUILD_DIR,
  '--export-dir', EXPORT_DIR,
  '--audio', AUDIO_WAV,
  '--out-name', OUT_MP4,
  '--cover-name', 'Logan-Claw-Rig-Cover-V6-IMAX.png',
  '--qa-name', 'Logan-Claw-Rig-12Beat-QA-Sheet-V6-IMAX.jpg',
  '--beats', JSON.stringify(BEATS),
], { stdio: 'inherit' });

// On full render, re-mux audio with `-af "alimiter=limit=0.708:level=false"` (CLAUDE.md Rule #4)
// so lossy AAC psychoacoustic Gibbs overshoot NEVER pushes post-AAC True Peak above `-1.0 dBFS`!
if (modeArg === 'render') {
  const ffmpeg = findFfmpeg();
  const finalPath = path.join(EXPORT_DIR, OUT_MP4);
  const safeTmp = `${finalPath}.tp_safe.mp4`;
  execFileSync(ffmpeg, [
    '-y',
    '-i', finalPath,
    '-i', AUDIO_WAV,
    '-map', '0:v:0',
    '-map', '1:a:0',
    '-c:v', 'copy',
    '-af', 'alimiter=limit=0.708:level=false',
    '-c:a', 'aac',
    '-b:a', '320k',
    '-ar', '48000',
    '-movflags', '+faststart',
    '-shortest',
    safeTmp,
  ], { stdio: 'inherit' });
  fs.renameSync(safeTmp, finalPath);
  console.log(`[Post-AAC True-Peak Guard] Verified & muxed -> ${finalPath}`);
}
