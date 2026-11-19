import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, mkdtemp, stat, copyFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { extname, isAbsolute, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { build } from 'vite';
import { DEMOS, demoAssetName, findDemo } from '../src/demos.js';
import { soundtrack } from './soundtrack.mjs';
import { airCrushScore } from './air-crush-score.mjs';
import { reflectorMix, reflectorScore } from './reflector-score.mjs';
import { REFLECTOR } from '../src/reflector.js';

const FPS = 24;
const ffmpeg = process.env.FFMPEG || 'ffmpeg';
const staging = process.env.TOP1_STILLS === '1';
const output = resolve(process.env.TOP1_RENDER_OUT ?? (staging ? '.cache/render-stills' : fileURLToPath(new URL('../public/demos', import.meta.url))));
const ORIGIN = 'http://top1-render.local';
const root = fileURLToPath(new URL('..', import.meta.url));
const entry = fileURLToPath(new URL('./demo-render/index.html', import.meta.url));
const IDs = process.argv.slice(2);
const films = IDs.length ? IDs.map(findDemo) : [...DEMOS, REFLECTOR];
if (films.some((film) => !film)) throw new Error(`Unknown demo ID. Use one of: ${[...DEMOS, REFLECTOR].map((film) => film.id).join(', ')}.`);

function processResult(child) {
  return new Promise((resolve, reject) => {
    child.on('error', reject);
    child.on('close', (code, signal) => code === 0 ? resolve() : reject(new Error(`FFmpeg exited with ${code ?? signal}`)));
  });
}

async function encode(page, film, temp) {
  const audio = join(temp, `${film.id}.wav`);
  const lab = film.id === 'air-crush';
  const optical = film.id === REFLECTOR.id;
  const narrated = lab || optical;
  const voice = fileURLToPath(new URL(`./demo-render/audio/${film.id}-vo.m4a`, import.meta.url));
  await writeFile(audio, lab ? airCrushScore(film.duration) : optical ? reflectorScore(film.duration) : soundtrack(film));
  const file = join(temp, `${film.id}.mp4`);
  const child = spawn(ffmpeg, [
    '-hide_banner', '-loglevel', 'error', '-y', '-filter_threads', '1',
    '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', 'pipe:0', '-i', audio,
    ...(narrated ? [
      '-i', voice, '-filter_complex', optical ? reflectorMix() : '[1:a]volume=0.88[fx];[2:a]pan=stereo|FL=c0|FR=c0,volume=0.90[vo];[fx][vo]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:latency=1[mix]', '-map', '0:v', '-map', '[mix]',
    ] : ['-af', 'volume=5dB']),
    '-vf', 'scale=in_range=full:in_color_matrix=bt601:out_range=tv:out_color_matrix=bt709,format=yuv420p',
    '-c:v', 'libx264', '-profile:v', 'high', '-level:v', narrated ? '4.0' : '3.1', '-crf', '19', '-preset', lab ? 'fast' : 'veryfast', '-threads', '2',
    ...(narrated ? ['-g', '48', '-maxrate', optical ? '6M' : '7M', '-bufsize', optical ? '12M' : '14M'] : []),
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-bsf:v', 'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0',
    '-c:a', 'aac', '-b:a', narrated ? '128k' : '96k', '-movflags', '+faststart+write_colr', '-shortest', file,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = processResult(child);
  let failure;
  done.catch((error) => { failure = error; });
  child.stdin.on('error', (error) => { failure ||= error; });
  try {
    const total = film.duration * FPS;
    for (let i = 0; i < total; i += 4) {
      if (failure) throw failure;
      const jpegs = await page.evaluate(({ start, end, fps }) => {
        const frames = [];
        for (let frame = start; frame < end; frame++) frames.push(window.top1Frame(frame / fps));
        return frames;
      }, { start: i, end: Math.min(total, i + 4), fps: FPS });
      for (const jpeg of jpegs) {
        if (!child.stdin.write(Buffer.from(jpeg, 'base64'))) {
          await Promise.race([once(child.stdin, 'drain'), done]);
        }
      }
      if (i % (FPS * 3) === 0) console.log(`  ${film.title}: ${i / FPS}s / ${film.duration}s`);
    }
    child.stdin.end();
    await done;
  } catch (error) {
    child.stdin.destroy();
    if (child.exitCode === null) child.kill();
    await done.catch(() => {});
    throw error;
  }
}

async function poster(page, film, temp) {
  const jpeg = await page.evaluate((t) => window.top1Frame(t, true), film.posterAt);
  const original = join(temp, `${film.id}-art.jpg`);
  await writeFile(original, Buffer.from(jpeg, 'base64'));
  await processResult(spawn(ffmpeg, [
    '-hide_banner', '-loglevel', 'error', '-y', '-i', original,
    '-frames:v', '1', '-c:v', 'libwebp', '-quality', '85', join(temp, `${film.id}.webp`),
  ], { stdio: 'inherit' }));
}

const args = ['--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--no-zygote'];
const temp = await mkdtemp(join(tmpdir(), 'top1-films-'));
let browser;
try {
  await mkdir(output, { recursive: true });
  // Build only the renderer into scratch space. Chromium loads it through
  // intercepted file requests: no public server, HMR, or external network.
  const compositor = join(temp, 'compositor');
  await build({ configFile: false, root, base: './', publicDir: false, logLevel: 'error', build: {
    outDir: compositor, emptyOutDir: true, target: 'esnext', rollupOptions: { input: entry },
  } });
  const types = { '.html': 'text/html', '.js': 'text/javascript', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };
  browser = await chromium.launch({ args, executablePath: process.env.CHROMIUM || undefined });
  for (const film of films) {
    const page = await browser.newPage({ viewport: { width: 720, height: 1280 } });
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
    const url = new URL('/tools/demo-render/index.html', ORIGIN);
    url.searchParams.set('film', film.id);
    if (process.env.TOP1_FULL_QUALITY === '1') url.searchParams.set('quality', 'full');
    await page.goto(url.href);
    try {
      await page.waitForFunction(() => typeof window.top1Frame === 'function', { timeout: 15_000 });
    } catch (error) {
      throw new Error(`${film.title} render did not initialize: ${errors.join('; ') || error.message}`);
    }
    await poster(page, film, temp);
    if (staging) {
      const requested = process.env.TOP1_STILL_TIMES?.split(',').map(Number);
      if (requested?.some((at) => !Number.isFinite(at) || at < 0 || at > film.duration)) throw new Error('Invalid TOP1_STILL_TIMES.');
      const reviewTimes = requested ?? (IDs.length ? film.shots.map(({ jumpTo }) => jumpTo) : [1.1, film.shots[1].at + 1.1, film.duration - 1.4]);
      for (const at of new Set([...reviewTimes, film.posterAt])) {
        const prefix = `${film.id}-${at.toFixed(2)}`;
        const still = await page.evaluate((t) => window.top1Frame(t), at);
        await writeFile(join(output, `${prefix}.jpg`), Buffer.from(still, 'base64'));
      }
    } else {
      await encode(page, film, temp);
    }
    if (errors.length) throw new Error(`${film.title} compositor: ${errors.join('; ')}`);
    await page.close();
    for (const ext of staging ? ['webp'] : ['webp', 'mp4']) {
      const source = `${film.id}.${ext}`;
      const name = staging ? source : demoAssetName(film.id, ext);
      await copyFile(join(temp, source), join(output, name));
      console.log(`${name}: ${(await stat(join(output, name))).size} bytes`);
    }
  }
} finally {
  await browser?.close();
  await rm(temp, { recursive: true, force: true });
}
