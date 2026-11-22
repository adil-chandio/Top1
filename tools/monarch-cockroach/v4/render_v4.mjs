#!/usr/bin/env node
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { spawn, execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';

const req = createRequire('/tmp/v4_runtime/package.json');
const { createServer } = req('vite');
const { chromium } = req('playwright-core');

const ROOT = '/home/user/Top1';
const BUILD_DIR = '/tmp/v4_build';
const PLATES_DIR = path.join(BUILD_DIR, 'plates');
const DELIV_DIR = path.join(ROOT, 'deliverables/monarch-cam-03-v4');
const AUDIO_WAV = path.join(BUILD_DIR, 'Monarch-Cam-03-Long-Video-Master-Mix-V4.wav');
const CHROMIUM_EXEC = '/tmp/chromium';
const FFMPEG_BIN = '/tmp/py/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2';

const TOTAL_FRAMES = 10302; // Exact 343.400s @ 30 fps (voice-lock-v4.json)

const CHROMIUM_ENV = {
  ...process.env,
  LD_LIBRARY_PATH: '/tmp/sparticuz_libs/al2023/lib:/tmp/sparticuz_libs/swiftshader',
  VK_ICD_FILENAMES: '/tmp/sparticuz_libs/swiftshader/vk_swiftshader_icd.json',
  FONTCONFIG_PATH: '/tmp/sparticuz_libs/fonts',
};

function parseArgs(argv) {
  const opts = {
    mode: 'all', // 'thumb' | 'plates' | 'assemble' | 'all'
    start: 0,
    end: TOTAL_FRAMES,
    renderW: 1280,
    renderH: 720,
    chunkSize: 300,
    crf: 18,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--mode') opts.mode = argv[++i];
    else if (a === '--start') opts.start = Number(argv[++i]);
    else if (a === '--end') opts.end = Number(argv[++i]);
    else if (a === '--width') opts.renderW = Number(argv[++i]);
    else if (a === '--height') opts.renderH = Number(argv[++i]);
    else if (a === '--chunk') opts.chunkSize = Number(argv[++i]);
    else if (a === '--crf') opts.crf = Number(argv[++i]);
  }
  return opts;
}

/**
 * Zero-copy RFC-6455 Binary WebSocket Receiver for Lossless Raw RGBA WebGL Readback!
 */
function startRawWSServer(expectedBytes, onFrame) {
  const srv = http.createServer();
  const ACK_FRAME = Buffer.from([0x81, 0x02, 0x6f, 0x6b]); // FIN text "ok"

  srv.on('upgrade', (req, socket) => {
    socket.setNoDelay(true);
    const wid = Number(new URL(req.url, 'http://127.0.0.1').searchParams.get('w') || '0');
    const key = req.headers['sec-websocket-key'];
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

async function launchBrowser(webgl = true) {
  const args = ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'];
  if (webgl) {
    args.push(
      '--enable-webgl',
      '--ignore-gpu-blocklist',
      '--use-gl=angle',
      '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader',
      '--js-flags=--max-old-space-size=1024'
    );
  }
  return chromium.launch({ executablePath: CHROMIUM_EXEC, headless: true, env: CHROMIUM_ENV, args });
}

function startRawFfmpegPipe(outMp4, w, h) {
  const args = [
    '-y',
    '-f', 'rawvideo',
    '-pix_fmt', 'rgba',
    '-s', `${w}x${h}`,
    '-r', '30',
    '-i', '-',
    '-vf', 'vflip',
    '-c:v', 'libx264',
    '-preset', 'veryfast',
    '-crf', '15',
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

async function renderThumbAndChapterSheet(vitePort) {
  fs.mkdirSync(DELIV_DIR, { recursive: true });
  fs.mkdirSync(path.join(BUILD_DIR, 'chapter_stills'), { recursive: true });

  const browser = await launchBrowser(true);
  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
    await page.goto(`http://127.0.0.1:${vitePort}/tools/monarch-cockroach/v4/page_v4.html?w=1920&h=1080`);
    await page.waitForFunction(() => window.__MONARCH_V4_READY__ === true, null, { timeout: 30000 });

    // 1. Native 1920x1080 Hero Thumbnail
    const thumbData = await page.evaluate(() => window.renderThumbnailPNG());
    const thumbOut = path.join(DELIV_DIR, 'Monarch-Cam-03-Thumbnail-V4.png');
    fs.writeFileSync(thumbOut, Buffer.from(thumbData.split(',')[1], 'base64'));
    console.log(`Wrote Thumbnail -> ${thumbOut} (${fs.statSync(thumbOut).size} bytes)`);

    // 2. Native 1920x1080 Stills across all 7 Chapters + Push-Up Metaphor for 8-Panel Cinema QA Sheet!
    const chapterFrames = [
      { f: 300,  label: 'CH01 · UNDER THE DOOR (3.2 MM · 2 PENNIES)' },
      { f: 2260, label: 'CH02 · 3D X-RAY SHINGLE & HINGE CUTAWAY' },
      { f: 3820, label: 'CH03 · 3-LANE HEIGHT RACE (12 vs 6 vs 4 MM)' },
      { f: 4940, label: 'CH04A · >80° WIDE-ARM SPLAYED PUSH-UP' },
      { f: 5320, label: 'CH04B · MACRO TIBIAL CRAMPON SPINE DRIVE' },
      { f: 7200, label: 'CH05 · FLOOR GRIT TRADE-OFF (40-GRIT WINS)' },
      { f: 7640, label: 'CH06 · ~900X BODY WEIGHT COMPRESSION PRESS' },
      { f: 9320, label: 'CH07 · 1X REAL-SPEED REBOUND & TARSAL SPRINT' },
    ];
    for (let i = 0; i < chapterFrames.length; i++) {
      const { f } = chapterFrames[i];
      const d = await page.evaluate((fr) => window.renderSingleFrameDataURL(fr, 0.96), f);
      fs.writeFileSync(path.join(BUILD_DIR, 'chapter_stills', `ch_${i}_${f}.jpg`), Buffer.from(d.split(',')[1], 'base64'));
    }
    console.log('Rendered all 8 native 1920x1080 chapter QA stills!');
  } finally {
    await browser.close();
  }
}

async function renderPlates(vitePort, opts) {
  fs.mkdirSync(PLATES_DIR, { recursive: true });

  const activePipes = new Map();
  const wsServer = await startRawWSServer(opts.renderW * opts.renderH * 4, async (wid, frameSlice) => {
    const pipe = activePipes.get(wid);
    if (!pipe) return;
    if (!pipe.stdin.write(frameSlice)) {
      await new Promise((r) => pipe.stdin.once('drain', r));
    }
  });
  const wsPort = wsServer.address().port;

  const chunks = [];
  for (let f = opts.start; f < opts.end; f += opts.chunkSize) {
    chunks.push([f, Math.min(opts.end, f + opts.chunkSize)]);
  }

  const browser = await launchBrowser(true);
  const t0 = Date.now();
  let doneFrames = 0;

  try {
    const page = await browser.newPage({ viewport: { width: opts.renderW, height: opts.renderH } });
    page.on('pageerror', (e) => console.error('[PAGE ERR]', e));
    await page.goto(`http://127.0.0.1:${vitePort}/tools/monarch-cockroach/v4/page_v4.html?w=${opts.renderW}&h=${opts.renderH}`);
    await page.waitForFunction(() => window.__MONARCH_V4_READY__ === true, null, { timeout: 30000 });
    await page.evaluate((url) => window.connectRawWS(url), `ws://127.0.0.1:${wsPort}/?w=0`);

    for (const [a, b] of chunks) {
      const tag = `${String(a).padStart(5, '0')}_${String(b).padStart(5, '0')}`;
      const chunkMp4 = path.join(PLATES_DIR, `plate_${tag}.mp4`);
      const chunkJson = path.join(PLATES_DIR, `plate_${tag}.json`);

      if (fs.existsSync(chunkMp4) && fs.existsSync(chunkJson) && fs.statSync(chunkMp4).size > 4096) {
        doneFrames += (b - a);
        console.log(`Cached chunk [${a}..${b})`);
        continue;
      }

      const tmpMp4 = chunkMp4 + '.pending.mp4';
      const ff = startRawFfmpegPipe(tmpMp4, opts.renderW, opts.renderH);
      activePipes.set(0, ff);

      const allRows = [];
      const SUB = 50;
      for (let f = a; f < b; f += SUB) {
        const subEnd = Math.min(b, f + SUB);
        const rows = await page.evaluate(([fa, fb]) => window.streamRawRangeWS(fa, fb), [f, subEnd]);
        for (const r of rows) allRows.push(r);
      }

      ff.stdin.end();
      await ff.done;
      activePipes.delete(0);

      fs.renameSync(tmpMp4, chunkMp4);
      fs.writeFileSync(chunkJson, JSON.stringify(allRows));
      doneFrames += (b - a);
      const elapsed = (Date.now() - t0) / 1000;
      const fps = doneFrames / Math.max(0.1, elapsed);
      const remSec = (opts.end - a - (b - a)) / Math.max(0.1, fps);
      console.log(`Chunk [${a}..${b}) complete | ${fps.toFixed(1)} fps | ~${Math.round(remSec)}s remaining`);
    }
  } finally {
    await browser.close();
    wsServer.close();
  }
}

async function assembleMaster(vitePort, opts) {
  fs.mkdirSync(DELIV_DIR, { recursive: true });

  // 1. Verify all chunks & landmark rows 0..10301
  const jsonFiles = fs.readdirSync(PLATES_DIR).filter((f) => f.endsWith('.json')).sort();
  const mp4Files = fs.readdirSync(PLATES_DIR).filter((f) => f.endsWith('.mp4') && !f.includes('.pending')).sort();

  const coordsByFrame = new Array(TOTAL_FRAMES);
  for (const jf of jsonFiles) {
    const rows = JSON.parse(fs.readFileSync(path.join(PLATES_DIR, jf), 'utf8'));
    for (const r of rows) {
      coordsByFrame[r[0]] = r.slice(1);
    }
  }
  for (let f = 0; f < TOTAL_FRAMES; f++) {
    if (!coordsByFrame[f]) throw new Error(`Missing landmark row for frame ${f}!`);
  }
  console.log(`Verified exact ${TOTAL_FRAMES} landmark rows [0..${TOTAL_FRAMES - 1}] across ${mp4Files.length} plate chunks.`);

  // 2. Concatenate 3D beauty plates losslessly if not already concatenated
  const concatTxt = path.join(BUILD_DIR, 'plates_concat_v4.txt');
  fs.writeFileSync(concatTxt, mp4Files.map((f) => `file '${path.join(PLATES_DIR, f)}'`).join('\n') + '\n');
  const rawConcatMp4 = path.join(BUILD_DIR, 'beauty_plate_v4.mp4');
  if (!fs.existsSync(rawConcatMp4) || fs.statSync(rawConcatMp4).size < 10_000_000) {
    execFileSync(FFMPEG_BIN, ['-y', '-f', 'concat', '-safe', '0', '-i', concatTxt, '-c', 'copy', rawConcatMp4], { stdio: 'inherit' });
  }

  // 3. Composite Native 1920x1080 RGBA Typography & 3D-Tracked Callout Leaders via Zero-Copy Unmasked HTTP Pipe!
  const browser = await launchBrowser(false);
  const outMp4 = path.join(DELIV_DIR, 'Monarch-Cam-03-Long-Video-V4.mp4');
  const EMPTY_RGBA = Buffer.alloc(1920 * 1080 * 4);

  let procStdin = null;
  const httpPipeServer = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }
    req.on('data', (chunk) => {
      if (!procStdin.write(chunk)) {
        req.pause();
        procStdin.once('drain', () => req.resume());
      }
    });
    req.on('end', () => { res.writeHead(200); res.end('ok'); });
  });
  await new Promise((r) => httpPipeServer.listen(0, '127.0.0.1', r));
  const ovPort = httpPipeServer.address().port;

  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
    await page.goto(`http://127.0.0.1:${vitePort}/tools/monarch-cockroach/v4/page_v4.html?titlesOnly=1`);
    await page.waitForFunction(() => window.__MONARCH_V4_READY__ === true, null, { timeout: 15000 });
    await page.evaluate((url) => window.setOverlayPostUrl(url), `http://127.0.0.1:${ovPort}/frame`);

    const hasOverlayArr = await page.evaluate((n) => {
      const out = new Array(n);
      for (let i = 0; i < n; i++) out[i] = window.hasOverlayForFrame(i);
      return out;
    }, TOTAL_FRAMES);

    const ffArgs = [
      '-y',
      '-i', rawConcatMp4,
      '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '1920x1080', '-r', '30', '-i', '-',
      '-i', AUDIO_WAV,
      '-filter_complex',
      '[0:v]scale=1920:1080:flags=lanczos+accurate_rnd,unsharp=3:3:0.32:3:3:0.0[bg];[bg][1:v]overlay=0:0:format=auto[vout];[2:a]volume=-0.4dB[aout]',
      '-map', '[vout]',
      '-map', '[aout]',
      '-c:v', 'libx264',
      '-preset', 'veryfast',
      '-crf', String(opts.crf),
      '-maxrate', '2150k',
      '-bufsize', '4300k',
      '-pix_fmt', 'yuv420p',
      '-colorspace', 'bt709',
      '-color_primaries', 'bt709',
      '-color_trc', 'bt709',
      '-c:a', 'aac',
      '-b:a', '320k',
      '-ar', '48000',
      '-movflags', '+faststart',
      '-frames:v', String(TOTAL_FRAMES),
      outMp4,
    ];

    const proc = spawn(FFMPEG_BIN, ffArgs, { stdio: ['pipe', 'ignore', 'pipe'] });
    procStdin = proc.stdin;
    let errLog = '';
    proc.stderr.on('data', (d) => { errLog += d.toString(); });
    const done = new Promise((res, rej) => {
      proc.on('close', (c) => (c === 0 ? res() : rej(new Error(`Master ffmpeg failed (${c}): ${errLog.slice(-800)}`))));
    });

    const t0 = Date.now();
    let f = 0;
    while (f < TOTAL_FRAMES) {
      if (!hasOverlayArr[f]) {
        if (!proc.stdin.write(EMPTY_RGBA)) {
          await new Promise((r) => proc.stdin.once('drain', r));
        }
        f++;
      } else {
        const batch = [];
        while (f < TOTAL_FRAMES && hasOverlayArr[f] && batch.length < 25) {
          batch.push([f, coordsByFrame[f]]);
          f++;
        }
        await page.evaluate((items) => window.postOverlayBatchHTTP(items), batch);
      }
      if (f % 1000 < 25 && f >= 1000) {
        console.log(`Composited ${f} / ${TOTAL_FRAMES} frames (${((Date.now() - t0) / 1000).toFixed(1)}s)...`);
      }
    }
    proc.stdin.end();
    await done;

    const sizeBytes = fs.statSync(outMp4).size;
    console.log(`MASTER V4 COMPLETE -> ${outMp4} (${sizeBytes} bytes = ${(sizeBytes / 1e6).toFixed(2)} MB decimal)`);
  } finally {
    httpPipeServer.close();
    await browser.close();
  }
}

async function main() {
  const opts = parseArgs(process.argv);
  const vite = await createServer({
    root: ROOT,
    server: { port: 0, host: '127.0.0.1', fs: { allow: [ROOT, '/tmp/v4_runtime'] } },
    logLevel: 'error',
  });
  await vite.listen();
  const vitePort = vite.httpServer.address().port;

  try {
    if (opts.mode === 'thumb' || opts.mode === 'all') {
      await renderThumbAndChapterSheet(vitePort);
    }
    if (opts.mode === 'plates' || opts.mode === 'all') {
      await renderPlates(vitePort, opts);
    }
    if (opts.mode === 'assemble' || opts.mode === 'all') {
      await assembleMaster(vitePort, opts);
    }
  } finally {
    await vite.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
