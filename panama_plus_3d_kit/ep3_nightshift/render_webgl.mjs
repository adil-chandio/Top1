import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const KIT_DIR = path.join(ROOT, 'panama_plus_3d_kit', 'ep3_nightshift');
const OUT_DIR = path.join(KIT_DIR, 'out');
const QC_DIR = path.join(KIT_DIR, 'qc');
const DELIVERABLES_DIR = path.join(ROOT, 'deliverables');

const TIMELINE = JSON.parse(fs.readFileSync(path.join(OUT_DIR, 'timeline_synced.json'), 'utf8'));
const AUDIO_WAV = path.join(OUT_DIR, 'audio_master.wav');
const OUT_MP4 = path.join(
  DELIVERABLES_DIR,
  'MONARCH_NightShift_EP01_SandwichHeist_PanamaPlus_1080x1920.mp4'
);
const CONTACT_SHEET = path.join(QC_DIR, 'contact_sheet.png');
const QC_REPORT = path.join(QC_DIR, 'qc_report.json');

const WIDTH = 1080;
const HEIGHT = 1920;
const FPS = TIMELINE.fps || 30;
const TOTAL_FRAMES = TIMELINE.total_frames;
const WORKERS = 2;
const FRAMES_DIR = '/tmp/ep3_nightshift_frames';
const ERROR_LOG = path.join(QC_DIR, 'render_error.log');
const logs = [];
const logMsg = (m) => {
  console.log(m);
  logs.push(m);
};

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
  '.gltf': 'model/gltf+json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
};

const server = http.createServer((req, res) => {
  const reqPath = (req.url || '/').split('?')[0];
  let full;
  if (reqPath.startsWith('/vendor/three/')) {
    const relVendor = reqPath.slice('/vendor/three/'.length);
    const threeDir = path.join(ROOT, 'node_modules', 'three');
    full = path.join(threeDir, relVendor);
    if (!full.startsWith(threeDir)) { res.writeHead(403); res.end('Forbidden'); return; }
  } else {
    const rel = reqPath === '/' ? 'scene.html' : reqPath.replace(/^\/+/, '');
    full = path.join(KIT_DIR, rel);
    if (!full.startsWith(KIT_DIR)) { res.writeHead(403); res.end('Forbidden'); return; }
  }
  if (!fs.existsSync(full) || fs.statSync(full).isDirectory()) {
    res.writeHead(404); res.end('Not found'); return;
  }
  const ext = path.extname(full).toLowerCase();
  res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
  fs.createReadStream(full).pipe(res);
});

await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const { port } = server.address();
const baseUrl = `http://127.0.0.1:${port}`;

logMsg(`Rendering NIGHT SHIFT EP01: ${TOTAL_FRAMES} frames (${TIMELINE.duration_sec}s @ ${FPS}fps) across ${WORKERS} workers...`);

async function renderWorker(workerIdx) {
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--use-gl=angle',
      '--use-angle=swiftshader',
      '--enable-webgl',
      '--ignore-gpu-blocklist',
      '--no-sandbox',
      '--disable-dev-shm-usage',
    ],
  });
  const page = await browser.newPage({ viewport: { width: WIDTH, height: HEIGHT } });
  page.setDefaultTimeout(180000);
  page.on('pageerror', (err) => logMsg(`[W${workerIdx}] PAGEERROR: ${err.stack || err.message}`));
  page.on('console', (msg) => {
    if (msg.type() === 'error' || msg.text().startsWith('MODEL ')) {
      logMsg(`[W${workerIdx}] ${msg.type().toUpperCase()}: ${msg.text()}`);
    }
  });
  await page.goto(baseUrl, { waitUntil: 'networkidle', timeout: 120000 });
  await page.evaluate((tl) => window.__MONARCH_INIT__(tl), TIMELINE);

  for (let i = workerIdx; i < TOTAL_FRAMES; i += WORKERS) {
    await page.evaluate((idx) => window.__MONARCH_FRAME__(idx), i);
    const framePath = path.join(FRAMES_DIR, `frame_${String(i).padStart(5, '0')}.png`);
    await page.screenshot({ path: framePath, type: 'png' });
    if (i % 150 === 0) logMsg(`  [W${workerIdx}] frame ${i}/${TOTAL_FRAMES}`);
  }
  await browser.close();
}

try {
  await Promise.all(Array.from({ length: WORKERS }, (_, idx) => renderWorker(idx)));
} catch (err) {
  logMsg(`FATAL RENDER ERROR: ${err.stack || err.message}`);
  fs.writeFileSync(ERROR_LOG, logs.join('\n') + '\n');
  server.close();
  throw err;
}
server.close();
if (fs.existsSync(ERROR_LOG)) fs.unlinkSync(ERROR_LOG);

execFileSync(
  'ffmpeg',
  [
    '-y',
    '-framerate', String(FPS),
    '-i', path.join(FRAMES_DIR, 'frame_%05d.png'),
    '-i', AUDIO_WAV,
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '19',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-ar', '48000',
    '-shortest',
    '-movflags', '+faststart',
    OUT_MP4,
  ],
  { stdio: 'inherit' }
);

const step = Math.max(1, Math.floor(TOTAL_FRAMES / 16));
execFileSync(
  'ffmpeg',
  [
    '-y', '-i', OUT_MP4,
    '-vf', `select='not(mod(n\\,${step}))',scale=270:480,tile=4x4`,
    '-frames:v', '1', CONTACT_SHEET,
  ],
  { stdio: 'inherit' }
);

const probeJson = execFileSync(
  'ffprobe',
  ['-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', OUT_MP4],
  { encoding: 'utf8' }
);
const probe = JSON.parse(probeJson);
const vStream = probe.streams.find((s) => s.codec_type === 'video');
const aStream = probe.streams.find((s) => s.codec_type === 'audio');
const stats = fs.statSync(OUT_MP4);

const report = {
  file: path.relative(ROOT, OUT_MP4),
  size_bytes: stats.size,
  size_mb: Number((stats.size / (1024 * 1024)).toFixed(2)),
  width: vStream?.width,
  height: vStream?.height,
  r_frame_rate: vStream?.r_frame_rate,
  duration_sec: Number(Number(probe.format.duration).toFixed(2)),
  audio_codec: aStream?.codec_name,
  audio_sample_rate: aStream?.sample_rate,
  audio_lufs: TIMELINE.audio_lufs,
  audio_true_peak_db: TIMELINE.audio_true_peak_db,
  total_frames: TOTAL_FRAMES,
  qc_pass:
    vStream?.width === 1080 &&
    vStream?.height === 1920 &&
    stats.size > 1_000_000 &&
    Math.abs(TIMELINE.audio_lufs - -14.0) <= 1.2,
};

fs.writeFileSync(QC_REPORT, JSON.stringify(report, null, 2));
console.log('QC REPORT:', JSON.stringify(report, null, 2));
if (!report.qc_pass) throw new Error('QC gate failed!');
