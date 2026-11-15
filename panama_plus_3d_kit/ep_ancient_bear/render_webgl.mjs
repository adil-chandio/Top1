#!/usr/bin/env node
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execFileSync, spawnSync } from 'node:child_process';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const ROOT = path.resolve(HERE, '..', '..');
const TIMELINE = JSON.parse(fs.readFileSync(path.join(HERE, 'timeline.json'), 'utf8'));
const W = TIMELINE.width || 1920;
const H = TIMELINE.height || 1080;
const FPS = TIMELINE.fps || 24;
const TOTAL_FRAMES = TIMELINE.total_frames;
const FRAMES_DIR = path.join(HERE, '_frames');
const QC_DIR = path.join(HERE, 'qc');
const OUT_MP4 = path.join(ROOT, 'deliverables', 'MONARCH_AncientBear_EP01_3D_Cinema_1920x1080.mp4');
const AUDIO_M4A = path.join(HERE, 'master_audio.m4a');

const ENCODE_ONLY = process.argv.includes('--encode-only');
const RENDER_ONLY = process.argv.includes('--render-only');
const CHUNK_INDEX = parseInt(process.env.CHUNK_INDEX ?? '0', 10);
const CHUNK_COUNT = parseInt(process.env.CHUNK_COUNT ?? '1', 10);
const START_FRAME = Math.floor((CHUNK_INDEX * TOTAL_FRAMES) / CHUNK_COUNT);
const END_FRAME = Math.floor(((CHUNK_INDEX + 1) * TOTAL_FRAMES) / CHUNK_COUNT);
const CHUNK_TOTAL = END_FRAME - START_FRAME;

fs.mkdirSync(FRAMES_DIR, { recursive: true });
fs.mkdirSync(QC_DIR, { recursive: true });
fs.mkdirSync(path.dirname(OUT_MP4), { recursive: true });

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.glb': 'model/gltf-binary',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.wav': 'audio/wav',
};

if (!ENCODE_ONLY) {
  const { chromium } = await import('playwright');
  const server = http.createServer((req, res) => {
    const urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
    let filePath = path.join(HERE, urlPath === '/' ? 'scene.html' : urlPath);
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    fs.createReadStream(filePath).pipe(res);
  });

  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const PORT = server.address().port;
  const SCENE_URL = `http://127.0.0.1:${PORT}/scene.html`;
  console.log(
    `Serving ${HERE} at ${SCENE_URL} | Chunk ${CHUNK_INDEX + 1}/${CHUNK_COUNT}: frames ${START_FRAME}..${END_FRAME - 1} (${CHUNK_TOTAL} frames, ${W}x${H} @ ${FPS}fps)`
  );

  const WORKERS = Math.min(2, Math.max(1, os.cpus().length));
  let nextFrame = START_FRAME;
  let doneFrames = 0;
  const tStart = Date.now();

  async function workerLoop(wid) {
    const browser = await chromium.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--use-gl=angle',
        '--use-angle=swiftshader',
        '--enable-webgl',
        '--ignore-gpu-blocklist',
      ],
    });
    const context = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
    const page = await context.newPage();
    page.on('pageerror', (e) => console.error(`[W${wid} pageerror]`, e.message));
    page.on('console', (m) => { if (m.type() === 'error') console.error(`[W${wid} console]`, m.text()); });
    await page.goto(SCENE_URL, { waitUntil: 'domcontentloaded', timeout: 120000 });
    await page.waitForFunction(() => window.__PANAMA_READY__ === true, { timeout: 180000 });
    console.log(`Worker ${wid} WebGL + all GLB assets ready!`);

    while (true) {
      const f = nextFrame++;
      if (f >= END_FRAME) break;
      const outFile = path.join(FRAMES_DIR, `f_${String(f).padStart(5, '0')}.jpg`);
      await page.evaluate((idx) => window.__RENDER_FRAME__(idx), f);
      await page.screenshot({ path: outFile, type: 'jpeg', quality: 94 });
      doneFrames++;
      if (doneFrames % 25 === 0 || doneFrames === CHUNK_TOTAL) {
        const elapsed = (Date.now() - tStart) / 1000;
        const rate = doneFrames / Math.max(elapsed, 0.01);
        const eta = (CHUNK_TOTAL - doneFrames) / Math.max(rate, 0.01);
        console.log(
          `[Chunk ${CHUNK_INDEX}] Progress: ${doneFrames}/${CHUNK_TOTAL} (${((doneFrames / CHUNK_TOTAL) * 100).toFixed(1)}%) | ${rate.toFixed(2)} fps | ETA ${(eta / 60).toFixed(1)}m`
        );
      }
    }
    await browser.close();
  }

  await Promise.all(Array.from({ length: WORKERS }, (_, i) => workerLoop(i)));
  server.close();
}

if (!RENDER_ONLY) {
  for (let f = 0; f < TOTAL_FRAMES; f++) {
    const p = path.join(FRAMES_DIR, `f_${String(f).padStart(5, '0')}.jpg`);
    if (!fs.existsSync(p)) {
      throw new Error(`Missing frame ${p}`);
    }
  }
  console.log(`All ${TOTAL_FRAMES} frames verified. Encoding 1080p Full HD MP4...`);
  execFileSync('ffmpeg', [
    '-y', '-hide_banner', '-loglevel', 'error',
    '-framerate', String(FPS),
    '-i', path.join(FRAMES_DIR, 'f_%05d.jpg'),
    '-i', AUDIO_M4A,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-c:a', 'copy', '-movflags', '+faststart', '-shortest',
    OUT_MP4,
  ], { stdio: 'inherit' });

  // Build 16-frame Contact Sheet evenly spanning every beat (2% -> 98%)
  const sheetFrames = [];
  for (let i = 0; i < 16; i++) {
    const idx = Math.min(TOTAL_FRAMES - 1, Math.round((0.02 + (i / 15) * 0.96) * TOTAL_FRAMES));
    sheetFrames.push(path.join(FRAMES_DIR, `f_${String(idx).padStart(5, '0')}.jpg`));
  }
  const tileList = path.join(QC_DIR, '_tiles.txt');
  fs.writeFileSync(tileList, sheetFrames.map((p) => `file '${p}'`).join('\n'));
  execFileSync('ffmpeg', [
    '-y', '-hide_banner', '-loglevel', 'error',
    '-f', 'concat', '-safe', '0', '-i', tileList,
    '-vf', 'scale=480:270,tile=4x4',
    '-frames:v', '1',
    path.join(QC_DIR, 'contact_sheet.png'),
  ], { stdio: 'inherit' });

  // Run FFprobe + ebur128 QC
  const probe = JSON.parse(execFileSync('ffprobe', [
    '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', OUT_MP4,
  ], { encoding: 'utf8' }));
  const eb = spawnSync('ffmpeg', ['-i', OUT_MP4, '-af', 'ebur128=peak=true', '-f', 'null', '-'], { encoding: 'utf8' });
  const ebText = (eb.stderr || '') + (eb.stdout || '');
  const lufsM = ebText.match(/I:\s*(-?\d+\.\d+)\s*LUFS/);
  const tpM = ebText.match(/Peak:\s*(-?\d+\.\d+)\s*dBFS/);
  const vs = probe.streams.find((s) => s.codec_type === 'video') || {};
  const as = probe.streams.find((s) => s.codec_type === 'audio') || {};
  const stat = fs.statSync(OUT_MP4);
  const report = {
    file: path.relative(ROOT, OUT_MP4),
    size_bytes: stat.size,
    size_mb: +(stat.size / (1024 * 1024)).toFixed(2),
    width: vs.width,
    height: vs.height,
    r_frame_rate: vs.r_frame_rate,
    duration_sec: +parseFloat(probe.format.duration).toFixed(2),
    audio_codec: as.codec_name,
    audio_sample_rate: as.sample_rate,
    audio_lufs: lufsM ? parseFloat(lufsM[1]) : null,
    audio_true_peak_db: tpM ? parseFloat(tpM[1]) : null,
    total_frames: TOTAL_FRAMES,
    qc_pass: vs.width === W && vs.height === H && stat.size > 5_000_000,
  };
  fs.writeFileSync(path.join(QC_DIR, 'qc_report.json'), JSON.stringify(report, null, 2));
  console.log('QC REPORT:', report);

  // Clean temporary frames so git push stays clean & fast
  fs.rmSync(FRAMES_DIR, { recursive: true, force: true });
  if (!report.qc_pass) process.exit(1);
}
