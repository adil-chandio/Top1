#!/usr/bin/env node
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { spawn, execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';

const req = createRequire('/tmp/v6_runtime/package.json');
const { createServer } = req('vite');
const { chromium } = req('playwright-core');

const ROOT = '/home/user/Top1';
const BUILD_DIR = '/tmp/v6_short/build';
const PLATES_DIR = path.join(BUILD_DIR, 'plates');
const EXPORT_DIR = path.join(ROOT, 'exports/monarch-cam-03-short-v6-imax');
const AUDIO_WAV = '/tmp/v6_short/Monarch-Cam-03-Short-Master-Mix-V6-IMAX.wav';
const CHROMIUM_EXEC = '/tmp/chromium';
const FFMPEG_BIN = '/tmp/py/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2';

const W = 1080;
const H = 1920;
const TOTAL_FRAMES = 1050; // 35.000s @ 30.000 fps

const CHROMIUM_ENV = {
  ...process.env,
  LD_LIBRARY_PATH: '/tmp/sparticuz_libs/al2023/lib:/tmp/sparticuz_libs/swiftshader',
  VK_ICD_FILENAMES: '/tmp/sparticuz_libs/swiftshader/vk_swiftshader_icd.json',
  FONTCONFIG_PATH: '/tmp/sparticuz_libs/fonts',
};

function parseArgs(argv) {
  const opts = { mode: 'preflight', workers: 3, chunkSize: 175 };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--mode') opts.mode = argv[++i];
    else if (a === '--workers') opts.workers = Number(argv[++i]);
    else if (a === '--chunk') opts.chunkSize = Number(argv[++i]);
  }
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

function startRawFfmpegPipe(outMp4) {
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

function saveDataUrl(dataUrl, outPath) {
  const base64 = dataUrl.split(',')[1];
  fs.writeFileSync(outPath, Buffer.from(base64, 'base64'));
}

async function runPreflight(vitePort) {
  fs.mkdirSync(EXPORT_DIR, { recursive: true });
  const stillsDir = path.join(BUILD_DIR, 'qa_stills');
  fs.mkdirSync(stillsDir, { recursive: true });

  const browser = await launchBrowser();
  try {
    const page = await browser.newPage({ viewport: { width: W, height: H } });
    page.on('pageerror', (err) => console.error('[Browser PageError]', err));
    page.on('console', (msg) => {
      if (msg.type() === 'error') console.error('[Browser ConsoleError]', msg.text());
    });
    await page.goto(`http://127.0.0.1:${vitePort}/tools/monarch-cockroach/short_v6/short_page_v6.html?w=${W}&h=${H}`);
    await page.waitForFunction(() => window.__SHORT_V6_READY__ === true, null, { timeout: 45000 });

    // 1. Verify seamless loop continuity between Frame 1049 and Frame 0!
    const loopMae = await page.evaluate(() => window.measureLoopSeamMAE());
    console.log(`[Preflight] Loop-Seam RGB MAE (f=1049 -> f=0): ${loopMae.toFixed(3)} / 255`);

    // 2. Render 9:16 Cover PNG
    const coverUrl = await page.evaluate(() => window.renderCoverPNG());
    const coverPath = path.join(EXPORT_DIR, 'Monarch-Cam-03-Short-Cover-V6-IMAX.png');
    saveDataUrl(coverUrl, coverPath);
    console.log(`[Preflight] Saved Cover PNG -> ${coverPath}`);

    // 3. Render 12 Key Dramatic Beats across all 10 shots for visual gate inspection!
    const beatFrames = [
      { f:   14, label: '01_HOOK_PENNIES' },
      { f:   48, label: '02_SLOT_SQUEEZE' },
      { f:  118, label: '03_REWIND_ORBIT' },
      { f:  172, label: '04_LASER_SCAN' },
      { f:  246, label: '05_XRAY_HINGES' },
      { f:  324, label: '06_WAIT_DOLLY' },
      { f:  396, label: '07_COLLAPSE_80DEG' },
      { f:  458, label: '08_ZERO_FEET_LASER' },
      { f:  525, label: '09_SPINES_GRIT' },
      { f:  642, label: '10_PRESS_900X_SLAM' },
      { f:  776, label: '11_3LANE_RACE' },
      { f:  952, label: '12_GATE_FAIL_DUAL' },
    ];

    for (let i = 0; i < beatFrames.length; i++) {
      const bf = beatFrames[i];
      const pngUrl = await page.evaluate((fr) => window.renderFramePNG(fr), bf.f);
      const p = path.join(stillsDir, `beat_${String(i).padStart(2, '0')}.png`);
      saveDataUrl(pngUrl, p);
      console.log(`[Preflight] Beat ${i + 1}/12 (f=${bf.f} ${bf.label}) rendered`);
    }

    // Assemble 4x3 9:16 Contact Sheet via Python Pillow for sharp inspection!
    const sheetPath = path.join(EXPORT_DIR, 'Monarch-Cam-03-Short-12Beat-QA-Sheet-V6-IMAX.jpg');
    execFileSync('python3', ['-c', `
import sys
sys.path.insert(0, '/tmp/py')
from PIL import Image, ImageDraw
W_CELL, H_CELL = 360, 640
sheet = Image.new('RGB', (W_CELL * 4, H_CELL * 3), (8, 12, 16))
labels = ${JSON.stringify(beatFrames.map((b) => `f=${b.f} ${b.label}`))}
for idx in range(12):
    im = Image.open(f'${stillsDir}/beat_{idx:02d}.png').convert('RGB').resize((W_CELL, H_CELL), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im)
    draw.rectangle([8, 8, 250, 32], fill=(0, 0, 0))
    draw.text((14, 13), labels[idx], fill=(255, 215, 140))
    cx, cy = (idx % 4) * W_CELL, (idx // 4) * H_CELL
    sheet.paste(im, (cx, cy))
sheet.save('${sheetPath}', quality=92)
`], { stdio: 'inherit' });
    console.log(`[Preflight] Saved 12-Beat QA Sheet -> ${sheetPath}`);
  } finally {
    await browser.close();
  }
}

async function runFullRender(vitePort, opts) {
  fs.mkdirSync(PLATES_DIR, { recursive: true });
  fs.mkdirSync(EXPORT_DIR, { recursive: true });
  // Clean up only incomplete .pending.mp4 files so completed chunks resume cleanly!
  for (const old of fs.readdirSync(PLATES_DIR)) {
    if (old.endsWith('.pending.mp4')) {
      fs.unlinkSync(path.join(PLATES_DIR, old));
    }
  }

  const allChunks = [];
  for (let a = 0; a < TOTAL_FRAMES; a += opts.chunkSize) {
    const ci = allChunks.length;
    const outMp4 = path.join(PLATES_DIR, `plate_${String(ci).padStart(3, '0')}.mp4`);
    allChunks.push({ ci, a, b: Math.min(TOTAL_FRAMES, a + opts.chunkSize), outMp4 });
  }
  const pendingChunks = allChunks.filter((c) => !fs.existsSync(c.outMp4));
  console.log(`[Resume] ${allChunks.length - pendingChunks.length}/${allChunks.length} chunks already complete; rendering ${pendingChunks.length} remaining chunks...`);

  const activePipes = new Map();
  const wsServer = await startRawWSServer(W * H * 4, async (wid, frameBuf) => {
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
      const page = await browser.newPage({ viewport: { width: W, height: H } });
      await page.goto(`http://127.0.0.1:${vitePort}/tools/monarch-cockroach/short_v6/short_page_v6.html?w=${W}&h=${H}`);
      await page.waitForFunction(() => window.__SHORT_V6_READY__ === true, null, { timeout: 45000 });
      await page.evaluate(([p, w]) => window.connectRawWS(p, w), [wsPort, wid]);

      while (nextIdx < pendingChunks.length) {
        const job = pendingChunks[nextIdx++];
        const { ci, a, b, outMp4 } = job;
        const pendingMp4 = `${outMp4}.pending.mp4`;
        const ff = startRawFfmpegPipe(pendingMp4);
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
        const sec = (Date.now() - t0) / 1000;
        const fps = doneFrames / Math.max(0.1, sec);
        console.log(`[W${wid}] Chunk ${ci + 1}/${allChunks.length} [${a}..${b}) done | +${doneFrames}f | ${fps.toFixed(2)} fps`);
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

  // Concatenate lossless/CRF-15 video chunks and mux with Dolby-Cinema V6 Master WAV!
  const plateFiles = fs.readdirSync(PLATES_DIR).filter((f) => f.endsWith('.mp4')).sort();
  const concatList = path.join(BUILD_DIR, 'concat_v6.txt');
  fs.writeFileSync(concatList, plateFiles.map((f) => `file '${path.join(PLATES_DIR, f)}'`).join('\n') + '\n');

  const finalMp4 = path.join(EXPORT_DIR, 'Monarch-Cam-03-Viral-Short-V6-IMAX.mp4');
  execFileSync(FFMPEG_BIN, [
    '-y',
    '-f', 'concat', '-safe', '0', '-i', concatList,
    '-i', AUDIO_WAV,
    '-map', '0:v:0',
    '-map', '1:a:0',
    '-c:v', 'copy',
    '-c:a', 'aac',
    '-b:a', '320k',
    '-ar', '48000',
    '-movflags', '+faststart',
    '-shortest',
    finalMp4,
  ], { stdio: 'inherit' });

  console.log(`[V6 IMAX MASTER COMPLETE] -> ${finalMp4} (${(fs.statSync(finalMp4).size / (1024 * 1024)).toFixed(2)} MiB)`);
}

async function main() {
  const opts = parseArgs(process.argv);
  const vite = await createServer({
    configFile: false,
    root: ROOT,
    optimizeDeps: {
      noDiscovery: true,
      include: [],
    },
    resolve: {
      alias: {
        three: '/tmp/v6_runtime/node_modules/three',
      },
    },
    server: {
      port: 0,
      host: '127.0.0.1',
      fs: { allow: [ROOT, '/tmp/v6_runtime'] },
    },
    logLevel: 'error',
  });
  await vite.listen();
  const vitePort = vite.httpServer.address().port;

  try {
    if (opts.mode === 'preflight') {
      await runPreflight(vitePort);
    } else if (opts.mode === 'full') {
      await runFullRender(vitePort, opts);
    }
  } finally {
    await vite.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
