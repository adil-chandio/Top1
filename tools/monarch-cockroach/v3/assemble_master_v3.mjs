#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawn, execFileSync } from 'node:child_process';
import { createServer } from 'vite';
import { chromium } from 'playwright-core';

const ROOT = process.cwd();
const PLAN_PATH = path.join(ROOT, 'tools/monarch-cockroach/feature/feature.plan');
const V3_DIR = path.join(ROOT, '.cache/monarch-cockroach/v3');
const PLATES_DIR = path.join(V3_DIR, 'plates');
const OUT_DIR = path.join(ROOT, '.cache/monarch-cockroach/out');
const AUDIO_WAV = path.join(ROOT, '.cache/monarch-cockroach/audio/Master-Mix-V2.wav');
const CHROMIUM_EXEC = process.env.CHROMIUM_EXEC || '/tmp/chromium';
const FFMPEG_BIN = process.env.FFMPEG_BIN || path.join(ROOT, '.cache/runtime/py/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2');

const TOTAL_FRAMES = 10461;

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });

  // 1. Merge & verify all 35 projection CSV chunks -> projection.csv (exact frames 0..10460)
  const csvFiles = fs.readdirSync(PLATES_DIR).filter((f) => f.endsWith('.csv')).sort();
  const mp4Files = fs.readdirSync(PLATES_DIR).filter((f) => f.endsWith('.mp4') && !f.includes('.pending')).sort();
  console.log(`Found ${mp4Files.length} video chunks and ${csvFiles.length} projection CSV chunks.`);

  let header = null;
  const rowsByFrame = new Array(TOTAL_FRAMES);
  const rawLines = [];
  for (const cf of csvFiles) {
    const lines = fs.readFileSync(path.join(PLATES_DIR, cf), 'utf8').trim().split('\n');
    if (!header) {
      header = lines[0];
      rawLines.push(header);
    }
    const cols = header.split(',');
    for (let i = 1; i < lines.length; i++) {
      const parts = lines[i].split(',');
      const f = Number(parts[0]);
      if (f >= 0 && f < TOTAL_FRAMES && !rowsByFrame[f]) {
        const obj = {};
        for (let c = 0; c < cols.length; c++) obj[cols[c]] = Number(parts[c]);
        rowsByFrame[f] = { line: lines[i], obj };
      }
    }
  }

  for (let f = 0; f < TOTAL_FRAMES; f++) {
    if (!rowsByFrame[f]) throw new Error(`Missing frame ${f} in projection CSV chunks!`);
    rawLines.push(rowsByFrame[f].line);
  }
  const projCsvPath = path.join(V3_DIR, 'projection.csv');
  fs.writeFileSync(projCsvPath, rawLines.join('\n') + '\n');
  console.log(`Verified & wrote ${projCsvPath} (${TOTAL_FRAMES} exact frames 0..${TOTAL_FRAMES - 1}).`);

  // 2. Losslessly concatenate 3D beauty plates -> beauty_plate_raw.mp4
  const concatListPath = path.join(V3_DIR, 'plates_concat.txt');
  fs.writeFileSync(
    concatListPath,
    mp4Files.map((f) => `file '${path.join(PLATES_DIR, f)}'`).join('\n') + '\n'
  );
  const rawConcatMp4 = path.join(V3_DIR, 'beauty_plate_raw.mp4');
  execFileSync(FFMPEG_BIN, [
    '-y', '-f', 'concat', '-safe', '0', '-i', concatListPath, '-c', 'copy', rawConcatMp4,
  ], { stdio: 'inherit' });
  console.log(`Concatenated 3D beauty plate -> ${rawConcatMp4}`);

  // 3. Launch lightweight titlesOnly Chromium tab to generate native 1920x1080 RGBA overlays
  const planText = fs.readFileSync(PLAN_PATH, 'utf8');
  const vite = await createServer({
    root: ROOT,
    server: { port: 0, host: '127.0.0.1', fs: { allow: [ROOT] } },
    logLevel: 'error',
  });
  await vite.listen();
  const vitePort = vite.httpServer.address().port;

  const browser = await chromium.launch({
    executablePath: CHROMIUM_EXEC,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    env: {
      ...process.env,
      LD_LIBRARY_PATH: '/tmp/al2023/lib:/tmp/al2023:/tmp' + (process.env.LD_LIBRARY_PATH ? ':' + process.env.LD_LIBRARY_PATH : ''),
    },
  });

  const masterOutMp4 = path.join(OUT_DIR, 'Monarch-Cam-03-Long-Video-16x9-Master-V3.mp4');

  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
    await page.goto(`http://127.0.0.1:${vitePort}/tools/monarch-cockroach/v3/page.html`, { waitUntil: 'networkidle' });
    await page.evaluate(async (p) => window.MONARCH_V3.init({ titlesOnly: true, planText: p }), planText);

    // Build 1 cached transparent 1920x1080 PNG for non-overlay frames
    const emptyB64 = await page.evaluate(() => {
      const c = document.createElement('canvas');
      c.width = 1920; c.height = 1080;
      return c.toDataURL('image/png');
    });
    const EMPTY_PNG = Buffer.from(emptyB64.slice(emptyB64.indexOf(',') + 1), 'base64');

    // Spawn single-pass Master FFmpeg compositor + locked Master-Mix-V2.wav (-0.9dB -> <= -1.5 dBTP AAC!)
    const ffArgs = [
      '-y',
      '-i', rawConcatMp4,
      '-f', 'image2pipe', '-vcodec', 'png', '-r', '30', '-i', '-',
      '-i', AUDIO_WAV,
      '-filter_complex',
      '[0:v]scale=1920:1080:flags=lanczos+accurate_rnd,unsharp=3:3:0.30:3:3:0.0[bg];[bg][1:v]overlay=0:0:format=auto[vout];[2:a]volume=-0.9dB[aout]',
      '-map', '[vout]',
      '-map', '[aout]',
      '-c:v', 'libx264',
      '-preset', 'medium',
      '-crf', '19',
      '-maxrate', '2050k',
      '-bufsize', '4100k',
      '-pix_fmt', 'yuv420p',
      '-colorspace', 'bt709',
      '-color_primaries', 'bt709',
      '-color_trc', 'bt709',
      '-r', '30',
      '-frames:v', String(TOTAL_FRAMES),
      '-c:a', 'aac',
      '-b:a', '320k',
      '-ar', '48000',
      '-movflags', '+faststart',
      masterOutMp4,
    ];

    console.log(`Compositing native 1920x1080 typography + 3D leaders + Master-Mix-V2.wav -> ${masterOutMp4}...`);
    const ff = spawn(FFMPEG_BIN, ffArgs, { stdio: ['pipe', 'ignore', 'pipe'] });
    let errTail = '';
    ff.stderr.on('data', (d) => { errTail = (errTail + d.toString()).slice(-1200); });
    const ffDone = new Promise((resolve, reject) => {
      ff.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg master mux failed (${code}): ${errTail}`))));
    });

    const t0 = Date.now();
    const BATCH = 30;
    for (let f = 0; f < TOTAL_FRAMES; f += BATCH) {
      const end = Math.min(TOTAL_FRAMES, f + BATCH);
      const reqBatch = [];
      for (let k = f; k < end; k++) reqBatch.push(rowsByFrame[k].obj);

      const pngUrls = await page.evaluate((items) => {
        return items.map((row) => window.MONARCH_V3.renderOverlayPNG(row.frame, row.mode, row));
      }, reqBatch);

      for (const dataUrl of pngUrls) {
        const buf = dataUrl
          ? Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64')
          : EMPTY_PNG;
        if (!ff.stdin.write(buf)) {
          await new Promise((r) => ff.stdin.once('drain', r));
        }
      }

      if (end % 1500 === 0 || end === TOTAL_FRAMES) {
        const elapsed = (Date.now() - t0) / 1000;
        console.log(`  Composited ${end}/${TOTAL_FRAMES} frames (${(end / elapsed).toFixed(1)} fps)...`);
      }
    }

    ff.stdin.end();
    await ffDone;
    const sizeMb = (fs.statSync(masterOutMp4).size / (1024 * 1024)).toFixed(2);
    console.log(`MASTER V3 COMPLETE: ${masterOutMp4} (${sizeMb} MB)`);

    // 4. Cut 60-second Opening Pilot (0..60.000s = 1,800 frames) & Moving Biomechanical Proof V3
    const pilotOutMp4 = path.join(OUT_DIR, 'Monarch-Cam-03-Opening-Pilot-60s-V3.mp4');
    execFileSync(FFMPEG_BIN, [
      '-y',
      '-i', masterOutMp4,
      '-t', '60.000',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
      '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
      '-c:a', 'aac', '-b:a', '320k', '-ar', '48000',
      '-movflags', '+faststart',
      pilotOutMp4,
    ], { stdio: 'inherit' });

    const proofOutMp4 = path.join(OUT_DIR, 'Monarch-Cam-03-Moving-Proof-V3.mp4');
    execFileSync(FFMPEG_BIN, [
      '-y',
      '-i', masterOutMp4,
      '-filter_complex',
      '[0:v]trim=start=8.0:end=16.0,setpts=PTS-STARTPTS[v1];' +
      '[0:v]trim=start=69.0:end=76.0,setpts=PTS-STARTPTS[v2];' +
      '[0:v]trim=start=162.5:end=172.5,setpts=PTS-STARTPTS[v3];' +
      '[v1][v2][v3]concat=n=3:v=1:a=0[vout]',
      '-map', '[vout]',
      '-an',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p',
      '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
      '-movflags', '+faststart',
      proofOutMp4,
    ], { stdio: 'inherit' });
    console.log(`Generated Opening-Pilot-60s-V3.mp4 and Moving-Proof-V3.mp4!`);
  } finally {
    await browser.close();
    await vite.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
