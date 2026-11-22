#!/usr/bin/env node
/**
 * Monarch V6 Hollywood IMAX Cinema SDK — Universal Parallel Raw-RGBA WebSocket Renderer,
 * 12-Beat Pre-Flight Contact-Sheet Generator & Unified Single-SPS/PPS Master Encoder!
 *
 * Usage:
 *   node tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs \
 *     --page /tools/my-film/page.html \
 *     --mode preflight \
 *     --w 1080 --h 1920 --frames 1050 \
 *     --beats '[{"f":10,"label":"01_HOOK"}, ...]' \
 *     --export-dir exports/my-film \
 *     --build-dir /tmp/my_film_build \
 *     --audio /tmp/my_film/master_mix.wav \
 *     --out-name My-Film-V6-IMAX.mp4
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { spawn, execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';

const req = createRequire('/tmp/v6_runtime/package.json');
const { createServer } = req('vite');
const { chromium } = req('playwright-core');

const ROOT = '/home/user/Top1';
const CHROMIUM_EXEC = '/tmp/chromium';

function findFfmpeg() {
  const pyDir = '/tmp/py/imageio_ffmpeg/binaries';
  if (fs.existsSync(pyDir)) {
    const f = fs.readdirSync(pyDir).find((n) => n.startsWith('ffmpeg'));
    if (f) return path.join(pyDir, f);
  }
  return 'ffmpeg';
}

const FFMPEG_BIN = findFfmpeg();
const CHROMIUM_ENV = {
  ...process.env,
  LD_LIBRARY_PATH: '/tmp/sparticuz_libs/al2023/lib:/tmp/sparticuz_libs/swiftshader',
  VK_ICD_FILENAMES: '/tmp/sparticuz_libs/swiftshader/vk_swiftshader_icd.json',
  FONTCONFIG_PATH: '/tmp/sparticuz_libs/fonts',
};

function parseArgs(argv) {
  const cpuCap = Math.max(1, Math.min(3, os.cpus().length));
  const opts = {
    page: '',
    mode: 'preflight',
    w: 1080,
    h: 1920,
    frames: 1050,
    workers: cpuCap,
    chunkSize: 175,
    buildDir: '/tmp/imax_v6_build',
    exportDir: path.join(ROOT, 'exports/imax-v6-run'),
    audio: '',
    outName: 'Master-V6-IMAX.mp4',
    coverName: 'Cover-V6-IMAX.png',
    qaName: '12Beat-QA-Sheet-V6-IMAX.jpg',
    readyFlag: '__IMAX_READY__',
    beatsJson: '',
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--page') opts.page = argv[++i];
    else if (a === '--mode') opts.mode = argv[++i];
    else if (a === '--w') opts.w = Number(argv[++i]);
    else if (a === '--h') opts.h = Number(argv[++i]);
    else if (a === '--frames') opts.frames = Number(argv[++i]);
    else if (a === '--workers') opts.workers = Math.min(os.cpus().length, Number(argv[++i]));
    else if (a === '--chunk') opts.chunkSize = Number(argv[++i]);
    else if (a === '--build-dir') opts.buildDir = argv[++i];
    else if (a === '--export-dir') opts.exportDir = path.resolve(ROOT, argv[++i]);
    else if (a === '--audio') opts.audio = argv[++i];
    else if (a === '--out-name') opts.outName = argv[++i];
    else if (a === '--cover-name') opts.coverName = argv[++i];
    else if (a === '--qa-name') opts.qaName = argv[++i];
    else if (a === '--ready-flag') opts.readyFlag = argv[++i];
    else if (a === '--beats') opts.beatsJson = argv[++i];
  }
  if (!opts.page) throw new Error('Missing required --page /tools/.../page.html');
  return opts;
}

async function launchBrowser() {
  const args = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--enable-webgl',
    '--ignore-gpu-blocklist',
    '--use-gl=angle',
    '--use-angle=swiftshader',
    '--enable-unsafe-swiftshader',
    '--js-flags=--max-old-space-size=1536',
  ];
  return chromium.launch({ executablePath: CHROMIUM_EXEC, headless: true, env: CHROMIUM_ENV, args });
}

function startRawWSServer(expectedBytes, onFrame) {
  const srv = http.createServer();
  const ACK_FRAME = Buffer.from([0x81, 0x02, 0x6f, 0x6b]);

  srv.on('upgrade', (reqSocket, socket) => {
    socket.setNoDelay(true);
    const wid = Number(new URL(reqSocket.url, 'http://127.0.0.1').searchParams.get('w') || '0');
    const key = reqSocket.headers['sec-websocket-key'];
    const accept = crypto.createHash('sha1').update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');
    socket.write(
      'HTTP/1.1 101 Switching Protocols\r\n' +
      'Upgrade: websocket\r\n' +
      'Connection: Upgrade\r\n' +
      `Sec-WebSocket-Accept: ${accept}\r\n\r\n`
    );

    const msgOut = Buffer.allocUnsafe(expectedBytes);
    let msgOffset = 0;
    let recvBuf = Buffer.alloc(0);

    socket.on('data', async (chunk) => {
      recvBuf = recvBuf.length === 0 ? chunk : Buffer.concat([recvBuf, chunk]);
      while (recvBuf.length >= 2) {
        const b0 = recvBuf[0];
        const b1 = recvBuf[1];
        const fin = (b0 & 0x80) !== 0;
        const opcode = b0 & 0x0f;
        const masked = (b1 & 0x80) !== 0;
        let len = b1 & 0x7f;
        let hdr = 2;
        if (len === 126) {
          if (recvBuf.length < 4) return;
          len = recvBuf.readUInt16BE(2);
          hdr = 4;
        } else if (len === 127) {
          if (recvBuf.length < 10) return;
          len = Number(recvBuf.readBigUInt64BE(2));
          hdr = 10;
        }
        const maskOffset = hdr;
        if (masked) hdr += 4;
        if (recvBuf.length < hdr + len) return;
        if (opcode === 0x08) { socket.end(); return; }

        if (masked) {
          const m0 = recvBuf[maskOffset], m1 = recvBuf[maskOffset + 1], m2 = recvBuf[maskOffset + 2], m3 = recvBuf[maskOffset + 3];
          for (let i = 0; i < len; i++) {
            const m = (i & 3) === 0 ? m0 : (i & 3) === 1 ? m1 : (i & 3) === 2 ? m2 : m3;
            msgOut[msgOffset + i] = recvBuf[hdr + i] ^ m;
          }
        } else {
          recvBuf.copy(msgOut, msgOffset, hdr, hdr + len);
        }
        msgOffset += len;
        recvBuf = recvBuf.subarray(hdr + len);

        if (fin && (opcode === 0x02 || opcode === 0x00)) {
          socket.pause();
          await onFrame(wid, msgOut.subarray(0, msgOffset));
          msgOffset = 0;
          socket.write(ACK_FRAME);
          socket.resume();
        }
      }
    });
  });

  return new Promise((resolve) => srv.listen(0, '127.0.0.1', () => resolve(srv)));
}

function startRawFfmpegPipe(outMp4, W, H) {
  const args = [
    '-y',
    '-f', 'rawvideo',
    '-pix_fmt', 'rgba',
    '-s', `${W}x${H}`,
    '-r', '30',
    '-i', '-',
    '-vf', 'vflip',
    '-c:v', 'libx264',
    '-preset', 'veryfast',
    '-crf', '14',
    '-pix_fmt', 'yuv420p',
    '-colorspace', 'bt709',
    '-color_primaries', 'bt709',
    '-color_trc', 'bt709',
    outMp4,
  ];
  const proc = spawn(FFMPEG_BIN, args, { stdio: ['pipe', 'ignore', 'pipe'] });
  let errLog = '';
  proc.stderr.on('data', (d) => { errLog += d.toString(); });
  const done = new Promise((resolve, reject) => {
    proc.on('close', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`ffmpeg exited ${code}: ${errLog.slice(-600)}`));
    });
  });
  return { stdin: proc.stdin, done };
}

function saveDataUrl(dataUrl, outPath) {
  fs.writeFileSync(outPath, Buffer.from(dataUrl.split(',')[1], 'base64'));
}

async function runPreflight(vitePort, opts) {
  fs.mkdirSync(opts.exportDir, { recursive: true });
  const stillsDir = path.join(opts.buildDir, 'qa_stills');
  fs.mkdirSync(stillsDir, { recursive: true });

  const browser = await launchBrowser();
  try {
    const page = await browser.newPage({ viewport: { width: opts.w, height: opts.h } });
    page.on('pageerror', (err) => console.error('[Browser PageError]', err));
    page.on('console', (msg) => {
      if (msg.type() === 'error') console.error('[Browser ConsoleError]', msg.text());
    });
    await page.goto(`http://127.0.0.1:${vitePort}${opts.page}?w=${opts.w}&h=${opts.h}`);
    await page.waitForFunction((rf) => window[rf] === true || window.__SHORT_V6_READY__ === true, opts.readyFlag, { timeout: 45000 });

    const loopMae = await page.evaluate(() => (typeof window.measureLoopSeamMAE === 'function' ? window.measureLoopSeamMAE() : -1));
    if (loopMae >= 0) {
      console.log(`[Preflight] Loop-Seam RGB MAE: ${loopMae.toFixed(3)} / 255`);
    }

    if (await page.evaluate(() => typeof window.renderCoverPNG === 'function')) {
      const coverUrl = await page.evaluate(() => window.renderCoverPNG());
      const coverPath = path.join(opts.exportDir, opts.coverName);
      saveDataUrl(coverUrl, coverPath);
      console.log(`[Preflight] Saved Cover -> ${coverPath}`);
    }

    let beatFrames;
    if (opts.beatsJson) {
      beatFrames = JSON.parse(opts.beatsJson);
    } else {
      beatFrames = Array.from({ length: 12 }, (_, i) => {
        const f = Math.min(opts.frames - 2, Math.round(((i + 0.4) / 12) * opts.frames));
        return { f, label: `BEAT_${String(i + 1).padStart(2, '0')}` };
      });
    }

    for (let i = 0; i < beatFrames.length; i++) {
      const bf = beatFrames[i];
      const pngUrl = await page.evaluate((fr) => window.renderFramePNG(fr), bf.f);
      saveDataUrl(pngUrl, path.join(stillsDir, `beat_${String(i).padStart(2, '0')}.png`));
      console.log(`[Preflight] Beat ${i + 1}/${beatFrames.length} (f=${bf.f} ${bf.label}) rendered`);
    }

    const isPortrait = opts.h >= opts.w;
    const cellW = isPortrait ? 360 : 480;
    const cellH = isPortrait ? 640 : 270;
    const sheetPath = path.join(opts.exportDir, opts.qaName);
    execFileSync('python3', ['-c', `
import sys
sys.path.insert(0, '/tmp/py')
from PIL import Image, ImageDraw
n = ${beatFrames.length}
cols = 4
rows = (n + cols - 1) // cols
W_CELL, H_CELL = ${cellW}, ${cellH}
sheet = Image.new('RGB', (W_CELL * cols, H_CELL * rows), (8, 12, 16))
labels = ${JSON.stringify(beatFrames.map((b) => `f=${b.f} ${b.label}`))}
for idx in range(n):
    im = Image.open(f'${stillsDir}/beat_{idx:02d}.png').convert('RGB').resize((W_CELL, H_CELL), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im)
    draw.rectangle([8, 8, 255, 32], fill=(0, 0, 0))
    draw.text((14, 13), labels[idx], fill=(255, 215, 140))
    sheet.paste(im, ((idx % cols) * W_CELL, (idx // cols) * H_CELL))
sheet.save('${sheetPath}', quality=92)
`], { stdio: 'inherit' });
    console.log(`[Preflight] Saved QA Sheet -> ${sheetPath}`);
  } finally {
    await browser.close();
  }
}

async function runFullRender(vitePort, opts) {
  const platesDir = path.join(opts.buildDir, 'plates');
  fs.mkdirSync(platesDir, { recursive: true });
  fs.mkdirSync(opts.exportDir, { recursive: true });

  for (const old of fs.readdirSync(platesDir)) {
    if (old.endsWith('.pending.mp4')) fs.unlinkSync(path.join(platesDir, old));
  }

  const allChunks = [];
  for (let a = 0; a < opts.frames; a += opts.chunkSize) {
    const ci = allChunks.length;
    const outMp4 = path.join(platesDir, `plate_${String(ci).padStart(3, '0')}.mp4`);
    allChunks.push({ ci, a, b: Math.min(opts.frames, a + opts.chunkSize), outMp4 });
  }
  const pendingChunks = allChunks.filter((c) => !fs.existsSync(c.outMp4));
  console.log(`[Resume] ${allChunks.length - pendingChunks.length}/${allChunks.length} chunks ready; rendering ${pendingChunks.length} chunks (${opts.workers} workers)...`);

  const activePipes = new Map();
  const wsServer = await startRawWSServer(opts.w * opts.h * 4, async (wid, frameBuf) => {
    const pipe = activePipes.get(wid);
    if (!pipe) return;
    if (!pipe.stdin.write(frameBuf)) {
      await new Promise((r) => pipe.stdin.once('drain', r));
    }
  });
  const wsPort = wsServer.address().port;

  let nextIdx = 0;
  let doneFrames = 0;
  const t0 = Date.now();

  async function runWorker(wid) {
    const browser = await launchBrowser();
    try {
      const page = await browser.newPage({ viewport: { width: opts.w, height: opts.h } });
      await page.goto(`http://127.0.0.1:${vitePort}${opts.page}?w=${opts.w}&h=${opts.h}`);
      await page.waitForFunction((rf) => window[rf] === true || window.__SHORT_V6_READY__ === true, opts.readyFlag, { timeout: 45000 });
      await page.evaluate(([p, w]) => window.connectRawWS(p, w), [wsPort, wid]);

      while (nextIdx < pendingChunks.length) {
        const { ci, a, b, outMp4 } = pendingChunks[nextIdx++];
        const pendingMp4 = `${outMp4}.pending.mp4`;
        const ff = startRawFfmpegPipe(pendingMp4, opts.w, opts.h);
        activePipes.set(wid, ff);

        const SUB = 35;
        for (let f = a; f < b; f += SUB) {
          await page.evaluate(([fa, fb]) => window.streamFramesWS(fa, fb), [f, Math.min(b, f + SUB)]);
        }

        ff.stdin.end();
        await ff.done;
        activePipes.delete(wid);
        fs.renameSync(pendingMp4, outMp4);

        doneFrames += (b - a);
        const fps = doneFrames / Math.max(0.1, (Date.now() - t0) / 1000);
        console.log(`[W${wid}] Chunk ${ci + 1}/${allChunks.length} [${a}..${b}) done | ${fps.toFixed(2)} fps`);
      }
    } finally {
      await browser.close();
    }
  }

  try {
    await Promise.all(Array.from({ length: opts.workers }, (_, w) => runWorker(w)));
  } finally {
    wsServer.close();
  }

  const plateFiles = fs.readdirSync(platesDir).filter((f) => f.endsWith('.mp4')).sort();
  const concatList = path.join(opts.buildDir, 'concat_v6.txt');
  fs.writeFileSync(concatList, plateFiles.map((f) => `file '${path.join(platesDir, f)}'`).join('\n') + '\n');

  const finalMp4 = path.join(opts.exportDir, opts.outName);
  // Unified single-SPS/PPS broadcast H.264 High@L4.0 master pass!
  const ffArgs = ['-y', '-f', 'concat', '-safe', '0', '-i', concatList];
  if (opts.audio && fs.existsSync(opts.audio)) {
    ffArgs.push(
      '-i', opts.audio,
      '-map', '0:v:0', '-map', '1:a:0',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-g', '30', '-bf', '2',
      '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
      '-c:a', 'aac', '-b:a', '320k', '-ar', '48000',
      '-movflags', '+faststart', '-shortest', finalMp4
    );
  } else {
    ffArgs.push(
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-g', '30', '-bf', '2',
      '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
      '-movflags', '+faststart', finalMp4
    );
  }
  execFileSync(FFMPEG_BIN, ffArgs, { stdio: 'inherit' });
  console.log(`[V6 IMAX MASTER READY] -> ${finalMp4} (${(fs.statSync(finalMp4).size / (1024 * 1024)).toFixed(2)} MiB)`);
}

async function main() {
  const opts = parseArgs(process.argv);
  const vite = await createServer({
    configFile: false,
    root: ROOT,
    optimizeDeps: { noDiscovery: true, include: [] },
    resolve: { alias: { three: '/tmp/v6_runtime/node_modules/three' } },
    server: { port: 0, host: '127.0.0.1', fs: { allow: [ROOT, '/tmp/v6_runtime'] } },
    logLevel: 'error',
  });
  await vite.listen();
  const vitePort = vite.httpServer.address().port;

  try {
    if (opts.mode === 'preflight') await runPreflight(vitePort, opts);
    else await runFullRender(vitePort, opts);
  } finally {
    await vite.close();
  }
}

main().catch((err) => {
  console.error('[FATAL RENDER ERROR]', err);
  process.exit(1);
});
