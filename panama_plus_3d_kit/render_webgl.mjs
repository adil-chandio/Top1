import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const KIT_DIR = path.join(ROOT, 'panama_plus_3d_kit');
const JOB = JSON.parse(fs.readFileSync(path.join(KIT_DIR, 'job.json'), 'utf8'));

const WIDTH = JOB.width || 1080;
const HEIGHT = JOB.height || 1920;
const FPS = JOB.fps || 30;
const DURATION = JOB.duration_sec || 5;
const TOTAL_FRAMES = Math.round(FPS * DURATION);
const FRAMES_DIR = '/tmp/panama_plus_frames';
const OUT_MP4 = path.join(KIT_DIR, 'out', 'panama_plus_hero_1080p.mp4');

fs.rmSync(FRAMES_DIR, { recursive: true, force: true });
fs.mkdirSync(FRAMES_DIR, { recursive: true });
fs.mkdirSync(path.dirname(OUT_MP4), { recursive: true });

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
    if (!full.startsWith(threeDir)) {
      res.writeHead(403);
      res.end('Forbidden');
      return;
    }
  } else {
    const rel = reqPath === '/' ? 'scene.html' : reqPath.replace(/^\/+/, '');
    full = path.join(KIT_DIR, rel);
    if (!full.startsWith(KIT_DIR)) {
      res.writeHead(403);
      res.end('Forbidden');
      return;
    }
  }
  if (!fs.existsSync(full) || fs.statSync(full).isDirectory()) {
    res.writeHead(404);
    res.end('Not found');
    return;
  }
  const ext = path.extname(full).toLowerCase();
  res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
  fs.createReadStream(full).pipe(res);
});

await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const { port } = server.address();
const baseUrl = `http://127.0.0.1:${port}`;

const browser = await chromium.launch({
  headless: true,
  args: [
    '--use-gl=angle',
    '--use-angle=swiftshader',
    '--enable-webgl',
    '--ignore-gpu-blocklist',
    '--no-sandbox',
  ],
});

const page = await browser.newPage({ viewport: { width: WIDTH, height: HEIGHT } });
page.on('pageerror', (err) => console.error('PAGEERROR:', err));
page.on('console', (msg) => {
  if (msg.type() === 'error') console.error('CONSOLE:', msg.text());
});
await page.goto(baseUrl, { waitUntil: 'networkidle' });

const localModel = path.join(KIT_DIR, JOB.model_local || 'assets/model.glb');
const payload = {
  ...JOB,
  model_served_path: fs.existsSync(localModel) ? `/${JOB.model_local}` : null,
};

await page.evaluate((job) => window.__MONARCH_INIT__(job), payload);

for (let i = 0; i < TOTAL_FRAMES; i += 1) {
  await page.evaluate(([idx, tot]) => window.__MONARCH_FRAME__(idx, tot), [i, TOTAL_FRAMES]);
  const framePath = path.join(FRAMES_DIR, `frame_${String(i).padStart(5, '0')}.png`);
  await page.screenshot({ path: framePath, type: 'png' });
}

await browser.close();
server.close();

execFileSync(
  'ffmpeg',
  [
    '-y',
    '-framerate',
    String(FPS),
    '-i',
    path.join(FRAMES_DIR, 'frame_%05d.png'),
    '-c:v',
    'libx264',
    '-preset',
    'medium',
    '-crf',
    '17',
    '-pix_fmt',
    'yuv420p',
    '-movflags',
    '+faststart',
    OUT_MP4,
  ],
  { stdio: 'inherit' }
);

console.log(`Rendered ${TOTAL_FRAMES} frames -> ${OUT_MP4}`);
