import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const KIT_DIR = path.join(ROOT, 'panama_plus_3d_kit', 'ep6_mafia_temple');
const OUT_DIR = path.join(KIT_DIR, 'out');
const QC_DIR = path.join(KIT_DIR, 'qc');
const DELIVERABLES_DIR = path.join(ROOT, 'deliverables');

const TIMELINE = JSON.parse(fs.readFileSync(path.join(OUT_DIR, 'timeline_synced.json'), 'utf8'));
const AUDIO_WAV = path.join(OUT_DIR, 'audio_master.wav');
const OUT_MP4 = path.join(
  DELIVERABLES_DIR,
  'MONARCH_MafiaTemple_3D_PanamaPlus_1920x1080.mp4'
);
const CONTACT_SHEET = path.join(QC_DIR, 'contact_sheet.png');
const QC_REPORT = path.join(QC_DIR, 'qc_report.json');
const ERROR_LOG = path.join(QC_DIR, 'render_error.log');

const WIDTH = 1920;
const HEIGHT = 1080;
const FPS = TIMELINE.fps || 24;
const TOTAL_FRAMES = TIMELINE.total_frames;
const WORKERS = 3;
const FRAMES_DIR = '/tmp/ep6_mafia_temple_frames';

fs.rmSync(FRAMES_DIR, { recursive: true, force: true });
fs.mkdirSync(FRAMES_DIR, { recursive: true });
fs.mkdirSync(QC_DIR, { recursive: true });
fs.mkdirSync(DELIVERABLES_DIR, { recursive: true });

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript',
  '.mjs': 'application/javascript',
  '.json': 'application/json',
  '.glb': 'model/gltf-binary',
  '.jpg': 'image/jpeg',
};

const server = http.createServer((req, res) => {
  const urlPath = (req.url || '/').split('?')[0];
  let filePath;
  if (urlPath === '/' || urlPath === '/scene.html') {
    filePath = path.join(KIT_DIR, 'scene.html');
  } else if (urlPath.startsWith('/vendor/three/')) {
    filePath = path.join(ROOT, 'node_modules', 'three', urlPath.replace('/vendor/three/', ''));
  } else if (urlPath.startsWith('/assets/')) {
    filePath = path.join(KIT_DIR, urlPath.slice(1));
  } else {
    res.writeHead(404);
    res.end('Not found');
    return;
  }
  if (!fs.existsSync(filePath)) {
    res.writeHead(404);
    res.end(`Missing: ${filePath}`);
    return;
  }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(filePath)] || 'application/octet-stream' });
  fs.createReadStream(filePath).pipe(res);
});

await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const port = server.address().port;
const baseUrl = `http://127.0.0.1:${port}`;
const logs = [];

try {
  const browser = await chromium.launch({
    headless: true,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox'],
  });
  const tStart = Date.now();
  let completed = 0;

  async function runWorker(workerId, frameIndices) {
    const context = await browser.newContext({ viewport: { width: WIDTH, height: HEIGHT }, deviceScaleFactor: 1 });
    const page = await context.newPage();
    page.on('pageerror', (err) => logs.push(`[W${workerId} pageerror] ${err.message}`));
    await page.goto(`${baseUrl}/scene.html`, { waitUntil: 'networkidle' });
    await page.evaluate(async (tl) => { await window.__MONARCH_INIT__(tl); }, TIMELINE);

    for (const f of frameIndices) {
      await page.evaluate((idx) => { window.__MONARCH_FRAME__(idx); }, f);
      await page.screenshot({ path: path.join(FRAMES_DIR, `frame_${String(f).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 96 });
      completed++;
      if (completed % 60 === 0 || completed === TOTAL_FRAMES) {
        console.log(`Rendered ${completed}/${TOTAL_FRAMES} frames (${((Date.now() - tStart) / 1000).toFixed(1)}s)`);
      }
    }
    await context.close();
  }

  const buckets = Array.from({ length: WORKERS }, () => []);
  for (let f = 0; f < TOTAL_FRAMES; f++) buckets[f % WORKERS].push(f);
  await Promise.all(buckets.map((b, i) => runWorker(i, b)));
  await browser.close();

  execFileSync('ffmpeg', [
    '-y', '-framerate', String(FPS), '-i', path.join(FRAMES_DIR, 'frame_%05d.jpg'), '-i', AUDIO_WAV,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(FPS),
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', OUT_MP4,
  ], { stdio: 'inherit' });

  const step = Math.max(1, Math.floor(TOTAL_FRAMES / 16));
  execFileSync('ffmpeg', [
    '-y', '-i', OUT_MP4, '-vf', `select='not(mod(n,${step}))',scale=480:270,tile=4x4`, '-frames:v', '1', CONTACT_SHEET,
  ], { stdio: 'inherit' });

  const probe = JSON.parse(execFileSync('ffprobe', ['-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', OUT_MP4], { encoding: 'utf8' }));
  const vStream = probe.streams.find((s) => s.codec_type === 'video');
  const aStream = probe.streams.find((s) => s.codec_type === 'audio');
  const sizeBytes = fs.statSync(OUT_MP4).size;
  const ebuErr = execFileSync('ffmpeg', ['-hide_banner', '-nostats', '-i', OUT_MP4, '-af', 'ebur128=peak=true', '-f', 'null', '-'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  const summ = (ebuErr || '').split('Summary:').pop() || '';
  const lufsMatch = summ.match(/I:\s+(-?[\d.]+) LUFS/);
  const tpMatch = summ.match(/Peak:\s+(-?[\d.]+) dBFS/);

  const report = {
    file: path.relative(ROOT, OUT_MP4),
    size_bytes: sizeBytes,
    size_mb: +(sizeBytes / (1024 * 1024)).toFixed(2),
    width: vStream?.width,
    height: vStream?.height,
    r_frame_rate: vStream?.r_frame_rate,
    duration_sec: +parseFloat(probe.format.duration).toFixed(2),
    audio_codec: aStream?.codec_name,
    audio_sample_rate: aStream?.sample_rate,
    audio_lufs: lufsMatch ? parseFloat(lufsMatch[1]) : TIMELINE.audio_lufs,
    audio_true_peak_db: tpMatch ? parseFloat(tpMatch[1]) : TIMELINE.audio_tp_db,
    total_frames: TOTAL_FRAMES,
    qc_pass: vStream?.width === WIDTH && vStream?.height === HEIGHT && Boolean(aStream) && sizeBytes > 500_000,
  };
  fs.writeFileSync(QC_REPORT, JSON.stringify(report, null, 2));
  console.log('QC REPORT:', JSON.stringify(report, null, 2));
  if (!report.qc_pass) throw new Error('QC gate failed!');
} catch (err) {
  logs.push(`FATAL: ${err?.stack || err}`);
  fs.writeFileSync(ERROR_LOG, logs.join('\n'), 'utf8');
  console.error(err);
  process.exitCode = 1;
} finally {
  server.close();
  fs.rmSync(FRAMES_DIR, { recursive: true, force: true });
}
