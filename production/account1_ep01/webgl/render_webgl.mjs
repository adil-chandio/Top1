/**
 * PEHRA EP01 — WebGL frame renderer.
 *
 * Same proven recipe as the Panama-Plus episodes: serve the stage over a tiny
 * static HTTP server, drive a headless Chromium through Playwright with
 * SwiftShader WebGL, screenshot each frame, then encode with ffmpeg.
 *
 * The difference from the Cycles pass is that a frame costs a screenshot
 * rather than a path-trace, so the whole 137 s film is minutes, not hours.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '../../..');
const KIT = HERE;

const WIDTH = 1080, HEIGHT = 1920;

const arg = (name, dflt) => {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : dflt;
};
const TIMELINE_PATH = path.resolve(arg('timeline', path.join(ROOT, 'production/account1_ep01/build/timeline_full.json')));
const AUDIO_PATH = path.resolve(arg('audio', path.join(ROOT, 'production/account1_ep01/build/master_full.m4a')));
const OUT_MP4 = path.resolve(arg('out', path.join(ROOT, 'production/account1_ep01/renders/PEHRA_EP01_WEBGL_1080x1920.mp4')));
const FIRST_BEAT = arg('first-beat', null);
const LAST_BEAT = arg('last-beat', null);
const WORKERS = parseInt(arg('workers', '6'), 10);
const JPEG_Q = parseInt(arg('quality', '94'), 10);

const TIMELINE = JSON.parse(fs.readFileSync(TIMELINE_PATH, 'utf8'));
let shots = TIMELINE.shots;
if (FIRST_BEAT) {
  const a = shots.findIndex((s) => s.id === FIRST_BEAT);
  const b = LAST_BEAT ? shots.findIndex((s) => s.id === LAST_BEAT) : a;
  if (a < 0) throw new Error(`unknown --first-beat ${FIRST_BEAT}`);
  shots = shots.slice(a, b < 0 ? a + 1 : b + 1);
}
const F0 = shots[0].f_start;
const F1 = shots[shots.length - 1].f_end;
const TOTAL = F1 - F0 + 1;
const FPS = TIMELINE.fps || 30;

const FRAMES_DIR = arg('frames-dir', '/tmp/pehra_webgl_frames');
const QC_DIR = path.join(KIT, 'qc');
fs.rmSync(FRAMES_DIR, { recursive: true, force: true });
fs.mkdirSync(FRAMES_DIR, { recursive: true });
fs.mkdirSync(QC_DIR, { recursive: true });
fs.mkdirSync(path.dirname(OUT_MP4), { recursive: true });

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'application/javascript',
  '.mjs': 'application/javascript', '.json': 'application/json',
  '.glb': 'model/gltf-binary', '.css': 'text/css',
  '.wasm': 'application/wasm', '.js': 'application/javascript',
};

const server = http.createServer((req, res) => {
  const urlPath = (req.url || '/').split('?')[0];
  let filePath;
  if (urlPath === '/' || urlPath === '/scene.html') filePath = path.join(KIT, 'scene.html');
  else if (urlPath.startsWith('/vendor/three/'))
    filePath = path.join(ROOT, 'node_modules', 'three', urlPath.replace('/vendor/three/', ''));
  else if (urlPath.startsWith('/assets/'))
    filePath = path.join(ROOT, 'production/account1_ep01/assets/glb', path.basename(urlPath));
  else { res.writeHead(404); res.end('nope'); return; }
  if (!fs.existsSync(filePath)) { res.writeHead(404); res.end(`missing ${filePath}`); return; }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(filePath)] || 'application/octet-stream' });
  fs.createReadStream(filePath).pipe(res);
});

await new Promise((r) => server.listen(0, '127.0.0.1', r));
const baseUrl = `http://127.0.0.1:${server.address().port}`;
console.log(`PEHRA stage at ${baseUrl}  |  beats ${shots[0].id}..${shots[shots.length - 1].id}  |  ${TOTAL} frames`);

const logs = [];
const errors = [];

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
      '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox',
      '--disable-dev-shm-usage', '--disable-gpu-sandbox',
    ],
  });

  const tStart = Date.now();
  let completed = 0;

  async function runWorker(workerId, frames) {
    const ctx = await browser.newContext({
      viewport: { width: WIDTH, height: HEIGHT },
      deviceScaleFactor: 1,
    });
    const page = await ctx.newPage();
    page.on('pageerror', (e) => errors.push(`[W${workerId}] ${e.message}`));
    page.on('console', (m) => { if (m.type() === 'error') errors.push(`[W${workerId}] ${m.text()}`); });
    const tGoto = Date.now();
    await page.goto(`${baseUrl}/scene.html`, { waitUntil: 'networkidle' });
    console.log(`[W${workerId}] page loaded in ${((Date.now()-tGoto)/1000).toFixed(1)}s`);
    const tInit = Date.now();
    await page.evaluate(async (tl) => {
      window.__SET_TIMELINE__(tl);
      await window.__PEHRA_INIT__(tl);
    }, TIMELINE);
    console.log(`[W${workerId}] stage initialised in ${((Date.now()-tInit)/1000).toFixed(1)}s`);

    let n = 0;
    for (const f of frames) {
      const tF = Date.now();
      await page.evaluate((idx) => window.__PEHRA_FRAME__(idx), f);
      await page.screenshot({
        path: path.join(FRAMES_DIR, `frame_${String(f).padStart(5, '0')}.jpg`),
        type: 'jpeg', quality: JPEG_Q,
      });
      if (++n <= 3) console.log(`[W${workerId}] frame ${f} took ${((Date.now()-tF)/1000).toFixed(2)}s`);
      completed++;
      if (completed % 30 === 0 || completed === TOTAL) {
        const el = ((Date.now() - tStart) / 1000).toFixed(1);
        console.log(`  ${completed}/${TOTAL} frames (${el}s, ${(completed / el).toFixed(2)} fps)`);
      }
    }
    await ctx.close();
  }

  const buckets = Array.from({ length: WORKERS }, () => []);
  for (let f = F0; f <= F1; f++) buckets[(f - F0) % WORKERS].push(f);
  await Promise.all(buckets.map((b, i) => runWorker(i, b)));
  await browser.close();

  const got = fs.readdirSync(FRAMES_DIR).filter((f) => f.endsWith('.jpg')).length;
  console.log(`Rendered ${got}/${TOTAL} frames in ${((Date.now() - tStart) / 1000).toFixed(1)}s`);
  if (got !== TOTAL) throw new Error(`frame count mismatch: ${got}/${TOTAL}`);

  const audioArgs = fs.existsSync(AUDIO_PATH) ? ['-i', AUDIO_PATH] : [];
  const audioMap = fs.existsSync(AUDIO_PATH)
    ? ['-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest']
    : ['-an'];
  console.log('Encoding H.264 1080x1920 …');
  execFileSync('ffmpeg', [
    '-y', '-framerate', String(FPS),
    '-i', path.join(FRAMES_DIR, 'frame_%05d.jpg'),
    ...audioArgs,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-r', String(FPS),
    ...audioMap, '-movflags', '+faststart', OUT_MP4,
  ], { stdio: 'inherit' });

  const probe = JSON.parse(execFileSync('ffprobe',
    ['-v','quiet','-print_format','json','-show_format','-show_streams', OUT_MP4],
    { encoding: 'utf8' }));
  const v = probe.streams.find((s) => s.codec_type === 'video');
  const a = probe.streams.find((s) => s.codec_type === 'audio');
  const report = {
    file: path.relative(ROOT, OUT_MP4),
    size_mb: +(fs.statSync(OUT_MP4).size / 1048576).toFixed(2),
    width: v?.width, height: v?.height, fps: v?.r_frame_rate,
    duration_sec: +parseFloat(probe.format.duration).toFixed(2),
    frames: got, audio: a?.codec_name || null,
    beats: `${shots[0].id}..${shots[shots.length - 1].id}`,
    render_seconds: +((Date.now() - tStart) / 1000).toFixed(1),
    qc_pass: v?.width === WIDTH && v?.height === HEIGHT && got === TOTAL,
  };
  fs.writeFileSync(path.join(QC_DIR, 'webgl_qc.json'), JSON.stringify(report, null, 2));
  console.log('QC:', JSON.stringify(report, null, 2));
  if (!report.qc_pass) throw new Error('QC gate failed');
}

try {
  await main();
} catch (e) {
  fs.writeFileSync(path.join(QC_DIR, 'webgl_error.log'),
    [...logs, ...errors, String(e?.stack || e)].join('\n'));
  console.error(e);
  process.exitCode = 1;
} finally {
  server.close();
  if (!process.env.PEHRA_KEEP_FRAMES) fs.rmSync(FRAMES_DIR, { recursive: true, force: true });
}
