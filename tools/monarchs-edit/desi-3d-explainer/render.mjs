// Desi 3D explainer — render harness for the Monarch Edit channel (P1).
//
// Two modes:
//   - default: full MP4 encode through an external ffmpeg (libx264 + AAC \
//     optional audio). Requires ffmpeg on PATH or $FFMPEG.
//   - TOP1_DESI3D_STILLS=1: still JPEGs only, no ffmpeg needed.
//
// Point TOP1_DESI3D_OUT at a directory to place the result. The default is
// .cache/monarch-desi-3d-explainer/ so channel assets never land in the
// public storefront folder (public/demos/) by accident.

import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, mkdtemp, stat, copyFile, readdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { extname, isAbsolute, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { build } from 'vite';
import { PILOTS } from './scenarios.js';

const pilotName = process.env.TOP1_DESI3D_PILOT || 'p1';
const pilot = PILOTS[pilotName];
if (!pilot) throw new Error(`Unknown pilot '${pilotName}' — use one of: ${Object.keys(PILOTS).join(', ')}`);
const DURATION = pilot.timeline.DURATION;
const FPS = pilot.timeline.FPS;
const FRAME = pilot.timeline.FRAME;

const staging = process.env.TOP1_DESI3D_STILLS === '1';
const output = resolve(process.env.TOP1_DESI3D_OUT ?? '.cache/monarch-desi-3d-explainer');
const OUT_ROOT = process.cwd();
const entry = fileURLToPath(new URL('./index.html', import.meta.url));
const ORIGIN = 'http://top1-desi-3d.local';
const ffmpeg = process.env.FFMPEG || 'ffmpeg';

const root = fileURLToPath(new URL('../../..', import.meta.url));

function processResult(child) {
  return new Promise((resolve, reject) => {
    child.on('error', reject);
    child.on('close', (code, signal) => code === 0 ? resolve() : reject(new Error(`FFmpeg exited with ${code ?? signal}`)));
  });
}

async function encode(page, temp) {
  const file = join(temp, `desi-3d-explainer-${pilotName}.mp4`);
  const total = Math.ceil(DURATION * FPS);
  const audio = process.env.TOP1_DESI3D_AUDIO || null;
  const child = spawn(ffmpeg, [
    '-hide_banner', '-loglevel', 'error', '-y', '-filter_threads', '1',
    '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', 'pipe:0',
    ...(audio ? ['-i', audio, '-shortest'] : []),
    '-vf', 'scale=in_range=full:in_color_matrix=bt601:out_range=tv:out_color_matrix=bt709,format=yuv420p',
    '-c:v', 'libx264', '-profile:v', 'high', '-level:v', '3.1', '-crf', '19',
    '-preset', 'veryfast', '-threads', '2',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-bsf:v', 'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0',
    ...(audio ? ['-c:a', 'aac', '-b:a', '128k'] : ['-an']),
    '-movflags', '+faststart', file,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = processResult(child);
  let failure;
  done.catch((error) => { failure = error; });
  child.stdin.on('error', (error) => { failure ||= error; });
  try {
    for (let i = 0; i < total; i += 4) {
      if (failure) throw failure;
      const jpegs = await page.evaluate(({ start, end }) => {
        const frames = [];
        for (let frame = start; frame < end; frame++) frames.push(window.top1Frame(frame / FPS));
        return frames;
      }, { start: i, end: Math.min(total, i + 4) });
      for (const jpeg of jpegs) {
        if (!child.stdin.write(Buffer.from(jpeg, 'base64'))) {
          await Promise.race([once(child.stdin, 'drain'), done]);
        }
      }
      if (i % (FPS * 3) === 0) console.log(`  ${(i / FPS).toFixed(0)}s / ${DURATION}s`);
    }
    child.stdin.end();
    await done;
  } catch (error) {
    child.stdin.destroy();
    if (child.exitCode === null) child.kill();
    await done.catch(() => {});
    throw error;
  }
  return file;
}

async function stills(page, temp, times) {
  for (const [i, at] of times.entries()) {
    const still = await page.evaluate((at) => window.top1Frame(at), at);
    const file = join(temp, `still-${String(i).padStart(2, '0')}.jpg`);
    await writeFile(file, Buffer.from(still, 'base64'));
    console.log(`  still: ${at}s → ${file}`);
  }
}

async function main() {
  const temp = await mkdtemp(join(tmpdir(), 'top1-desi-3d-'));
  let browser;
  try {
    await mkdir(output, { recursive: true });
    const compositor = join(temp, 'compositor');
    await build({ configFile: false, root, base: './', publicDir: false, logLevel: 'error', build: {
      outDir: compositor, emptyOutDir: true, target: 'esnext', rollupOptions: { input: entry },
    } });
    const types = { '.html': 'text/html', '.js': 'text/javascript', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };
    browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--no-zygote'], executablePath: process.env.CHROMIUM || undefined });
    const page = await browser.newPage({ viewport: { width: FRAME.width, height: FRAME.height } });
    await page.route('**/*', async (route) => {
      const url = new URL(route.request().url());
      if (url.origin !== ORIGIN) return route.abort();
      const file = resolve(compositor, `.${decodeURIComponent(url.pathname)}`);
      const subpath = relative(compositor, file);
      const contentType = types[extname(file)];
      if (!contentType || subpath.startsWith('..') || isAbsolute(subpath)) return route.abort();
      try { await route.fulfill({ path: file, contentType }); }
      catch { await route.fulfill({ status: 404, body: 'Render resource not available.' }); }
    });
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(`${ORIGIN}/tools/monarchs-edit/desi-3d-explainer/index.html?pilot=${pilotName}`);
    try {
      await page.waitForFunction(() => typeof window.top1Frame === 'function', { timeout: 20_000 });
    } catch (error) {
      throw new Error(`Desi 3D explainer did not initialize: ${errors.join('; ') || error.message}`);
    }
    if (staging) {
      const stillTimes = pilot.view.stillTimes ?? [2.5, 7.0, 9.5, 13.5, 23.0, 28.0, 36.0];
      await stills(page, temp, stillTimes);
      for (const name of await readdir(temp).then((files) => files.filter((f) => f.startsWith('still-')))) {
        await copyFile(join(temp, name), join(output, name));
        console.log(`  still → ${join(output, name)}`);
      }
    } else {
      const file = await encode(page, temp);
      await copyFile(file, join(output, `desi-3d-explainer-${pilotName}.mp4`));
      const size = (await stat(join(output, `desi-3d-explainer-${pilotName}.mp4`))).size;
      console.log(`desi-3d-explainer-${pilotName}.mp4: ${size} bytes`);
    }
    if (errors.length) throw new Error(`Desi 3D explainer compositor: ${errors.join('; ')}`);
    await page.close();
  } finally {
    await browser?.close();
    await rm(temp, { recursive: true, force: true });
  }
}

main().catch((error) => { console.error(error.message); process.exit(1); });
