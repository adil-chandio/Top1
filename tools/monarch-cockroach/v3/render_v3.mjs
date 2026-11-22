#!/usr/bin/env node
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { createServer } from 'vite';
import { chromium } from 'playwright-core';

const ROOT = process.cwd();
const PLAN_PATH = path.join(ROOT, 'tools/monarch-cockroach/feature/feature.plan');
const OUT_DIR = path.join(ROOT, '.cache/monarch-cockroach/v3');
const CHROMIUM_EXEC = process.env.CHROMIUM_EXEC || '/tmp/chromium';
const FFMPEG_BIN = process.env.FFMPEG_BIN || path.join(ROOT, '.cache/runtime/py/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2');

function parseArgs(argv) {
  const opts = {
    stills: null,
    start: 0,
    end: 10461,
    workers: 1, // 1 Chromium uses vk_swiftshader's multi-threaded Vulkan worker pool across both cores at ~550 MB RSS!
    renderW: 960,
    renderH: 540,
    outDir: OUT_DIR,
    chunkSize: 300,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--stills') opts.stills = argv[++i].split(',').map(Number);
    else if (a === '--start') opts.start = Number(argv[++i]);
    else if (a === '--end') opts.end = Number(argv[++i]);
    else if (a === '--workers') opts.workers = Number(argv[++i]);
    else if (a === '--width') opts.renderW = Number(argv[++i]);
    else if (a === '--height') opts.renderH = Number(argv[++i]);
    else if (a === '--chunk') opts.chunkSize = Number(argv[++i]);
    else if (a === '--out') opts.outDir = path.resolve(argv[++i]);
  }
  return opts;
}

/**
 * Minimal zero-dependency RFC-6455 binary WebSocket frame receiver (reassembles fragmented frames + unmasks into preallocated Buffer!).
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

        if (opcode === 0x08) { socket.end(); return; } // close

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

async function launchWorkerBrowser() {
  return chromium.launch({
    executablePath: CHROMIUM_EXEC,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--use-gl=angle',
      '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader',
      '--ignore-gpu-blocklist',
      '--js-flags=--max-old-space-size=512',
    ],
    env: {
      ...process.env,
      LD_LIBRARY_PATH: '/tmp/al2023/lib:/tmp/al2023:/tmp' + (process.env.LD_LIBRARY_PATH ? ':' + process.env.LD_LIBRARY_PATH : ''),
      VK_ICD_FILENAMES: '/tmp/al2023/vk_swiftshader_icd.json',
    },
  });
}

async function createWorkerPage(browser, port, renderW, renderH, planText) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('pageerror', (err) => console.error('[PAGE ERROR]', err));
  await page.goto(`http://127.0.0.1:${port}/tools/monarch-cockroach/v3/page.html`, { waitUntil: 'networkidle' });
  await page.evaluate(
    async ({ renderW, renderH, planText }) => window.MONARCH_V3.init({ renderW, renderH, planText }),
    { renderW, renderH, planText }
  );
  return page;
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

async function main() {
  const opts = parseArgs(process.argv);
  fs.mkdirSync(path.join(opts.outDir, 'stills'), { recursive: true });
  fs.mkdirSync(path.join(opts.outDir, 'plates'), { recursive: true });

  const planText = fs.readFileSync(PLAN_PATH, 'utf8');
  const vite = await createServer({
    root: ROOT,
    server: { port: 0, host: '127.0.0.1', fs: { allow: [ROOT] } },
    logLevel: 'error',
  });
  await vite.listen();
  const vitePort = vite.httpServer.address().port;

  const activePipes = new Map();
  const wsServer = await startRawWSServer(opts.renderW * opts.renderH * 4, async (wid, frameSlice) => {
    const pipe = activePipes.get(wid);
    if (!pipe) return;
    if (!pipe.stdin.write(frameSlice)) {
      await new Promise((r) => pipe.stdin.once('drain', r));
    }
  });
  const wsPort = wsServer.address().port;

  try {
    if (opts.stills) {
      const browser = await launchWorkerBrowser();
      try {
        const page = await createWorkerPage(browser, vitePort, 1280, 720, planText);
        for (const f of opts.stills) {
          const { dataUrl, trace } = await page.evaluate((frame) => window.MONARCH_V3.renderJPEGDataURL(frame, 0.95), f);
          const b64 = dataUrl.slice(dataUrl.indexOf(',') + 1);
          const outPath = path.join(opts.outDir, 'stills', `frame_${String(f).padStart(5, '0')}.jpg`);
          fs.writeFileSync(outPath, Buffer.from(b64, 'base64'));
          console.log(`STILL frame=${f} -> ${outPath}`, JSON.stringify(trace));
        }
      } finally {
        await browser.close();
      }
      return;
    }

    const chunks = [];
    for (let f = opts.start; f < opts.end; f += opts.chunkSize) {
      chunks.push([f, Math.min(opts.end, f + opts.chunkSize)]);
    }

    console.log(`Rendering 3D Beauty Plates [${opts.start}..${opts.end}) in ${chunks.length} chunks across ${opts.workers} worker(s) (${opts.renderW}x${opts.renderH})...`);
    const t0 = Date.now();
    let completedFrames = 0;
    let cursor = 0;

    async function workerLoop(workerId) {
      const browser = await launchWorkerBrowser();
      try {
        const page = await createWorkerPage(browser, vitePort, opts.renderW, opts.renderH, planText);
        await page.evaluate((url) => window.MONARCH_V3.connectWS(url), `ws://127.0.0.1:${wsPort}/?w=${workerId}`);

        while (cursor < chunks.length) {
          const idx = cursor++;
          const [a, b] = chunks[idx];
          const chunkMp4 = path.join(opts.outDir, 'plates', `plate_${String(a).padStart(5, '0')}_${String(b).padStart(5, '0')}.mp4`);
          const chunkCsv = path.join(opts.outDir, 'plates', `plate_${String(a).padStart(5, '0')}_${String(b).padStart(5, '0')}.csv`);
          if (fs.existsSync(chunkMp4) && fs.existsSync(chunkCsv) && fs.statSync(chunkMp4).size > 4096) {
            completedFrames += (b - a);
            console.log(`[W${workerId}] Cached [${a}..${b})`);
            continue;
          }

          const tmpMp4 = chunkMp4 + '.pending.mp4';
          const tmpCsv = chunkCsv + '.pending.csv';
          const ff = startRawFfmpegPipe(tmpMp4, opts.renderW, opts.renderH);
          activePipes.set(workerId, ff);

          const csvLines = ['frame,mode,head_x,head_y,pronotum_x,pronotum_y,hinge_x,hinge_y,r3Spine_x,r3Spine_y,r3Claw_x,r3Claw_y,pennies_x,pennies_y,platen_x,platen_y'];

          const SUB = 50;
          for (let f = a; f < b; f += SUB) {
            const subEnd = Math.min(b, f + SUB);
            const traces = await page.evaluate(
              ([fa, fb]) => window.MONARCH_V3.streamRangeWS(fa, fb),
              [f, subEnd]
            );
            for (const tr of traces) {
              csvLines.push([
                tr.frame, tr.mode,
                tr.head_x, tr.head_y,
                tr.pronotum_x, tr.pronotum_y,
                tr.hinge_x, tr.hinge_y,
                tr.r3Spine_x, tr.r3Spine_y,
                tr.r3Claw_x, tr.r3Claw_y,
                tr.pennies_x, tr.pennies_y,
                tr.platen_x, tr.platen_y,
              ].join(','));
            }
            completedFrames += (subEnd - f);
          }

          activePipes.delete(workerId);
          ff.stdin.end();
          await ff.done;
          fs.writeFileSync(tmpCsv, csvLines.join('\n') + '\n');
          fs.renameSync(tmpMp4, chunkMp4);
          fs.renameSync(tmpCsv, chunkCsv);

          const rssMb = Math.round(process.memoryUsage().rss / (1024 * 1024));
          const elapsed = (Date.now() - t0) / 1000;
          const fps = completedFrames / Math.max(0.1, elapsed);
          const remSec = ((opts.end - opts.start) - completedFrames) / Math.max(0.1, fps);
          console.log(`[W${workerId}] Done [${a}..${b}) | ${completedFrames}/${opts.end - opts.start} frames | ${fps.toFixed(2)} fps | nodeRSS=${rssMb}MB | ETA ${(remSec / 60).toFixed(1)} min`);
        }
      } finally {
        await browser.close();
      }
    }

    await Promise.all(Array.from({ length: opts.workers }, (_, w) => workerLoop(w)));
    console.log(`ALL 3D PLATES COMPLETE in ${((Date.now() - t0) / 1000).toFixed(1)}s!`);
  } finally {
    wsServer.close();
    await vite.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
