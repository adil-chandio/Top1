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
const BUILD_DIR = '/tmp/v6_long/build';
const PLATES_DIR = path.join(BUILD_DIR, 'plates');
const OVERLAYS_DIR = path.join(BUILD_DIR, 'overlays');
const STILLS_DIR = path.join(BUILD_DIR, 'qa_stills');
const EXPORT_DIR = path.join(ROOT, 'exports/monarch-cam-03-long-v6-imax');
const CHROMIUM_EXEC = '/tmp/chromium';

const ffBinDir = '/tmp/py/imageio_ffmpeg/binaries';
const FFMPEG_BIN = path.join(
  ffBinDir,
  fs.readdirSync(ffBinDir).find((f) => f.startsWith('ffmpeg'))
);

const TOTAL_FRAMES = 9008; // 300.267s @ 30.000 fps

const CHROMIUM_ENV = {
  ...process.env,
  LD_LIBRARY_PATH: '/tmp/sparticuz_libs/al2023/lib:/tmp/sparticuz_libs/swiftshader',
  VK_ICD_FILENAMES: '/tmp/sparticuz_libs/swiftshader/vk_swiftshader_icd.json',
  FONTCONFIG_PATH: '/tmp/sparticuz_libs/fonts',
};

function parseArgs(argv) {
  const opts = { mode: 'preflight', workers: 2, chunkSize: 300, width: 1280, height: 720, maxChunks: 999 };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--mode') opts.mode = argv[++i];
    else if (a === '--workers') opts.workers = Number(argv[++i]);
    else if (a === '--chunk') opts.chunkSize = Number(argv[++i]);
    else if (a === '--width') opts.width = Number(argv[++i]);
    else if (a === '--height') opts.height = Number(argv[++i]);
    else if (a === '--max-chunks') opts.maxChunks = Number(argv[++i]);
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

function startRawFfmpegPipe(outMp4, width, height) {
  const args = [
    '-y',
    '-f', 'rawvideo',
    '-pix_fmt', 'rgba',
    '-s', `${width}x${height}`,
    '-r', '30',
    '-i', '-',
    '-vf', 'vflip',
    '-c:v', 'libx264',
    '-preset', 'veryfast',
    '-crf', '12',
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

async function exportOverlaysIfNeeded(page) {
  fs.mkdirSync(OVERLAYS_DIR, { recursive: true });
  const items = await page.evaluate(() => window.exportOverlayAssetsV6());
  const manifest = [];
  for (const it of items) {
    const fn = `${it.id}.png`;
    saveDataUrl(it.dataUrl, path.join(OVERLAYS_DIR, fn));
    manifest.push({ id: it.id, kind: it.kind, start: it.start, end: it.end, fadeFrames: it.fadeFrames, file: fn });
  }
  fs.writeFileSync(path.join(OVERLAYS_DIR, 'overlays_manifest_v6.json'), JSON.stringify(manifest, null, 2));
  console.log(`[Overlays] Exported ${manifest.length} native 1920x1080 RGBA overlay cards -> ${OVERLAYS_DIR}`);
}

async function runPreflight(vitePort) {
  fs.mkdirSync(EXPORT_DIR, { recursive: true });
  fs.mkdirSync(STILLS_DIR, { recursive: true });

  const browser = await launchBrowser();
  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
    page.on('pageerror', (err) => console.error('[Browser PageError]', err));
    page.on('console', (msg) => {
      if (msg.type() === 'error') console.error('[Browser ConsoleError]', msg.text());
    });
    await page.goto(`http://127.0.0.1:${vitePort}/tools/monarch-cockroach/long_v6/page_long_v6.html?w=1920&h=1080`);
    await page.waitForFunction(() => window.__LONG_V6_READY__ === true, null, { timeout: 60000 });

    // 1. Export pre-baked 1920x1080 RGBA typography cards for Python compositor
    await exportOverlaysIfNeeded(page);

    // 2. Render Hero 1920x1080 YouTube Thumbnail V6 IMAX (Doorway Light-Blade + Pennies + Squeezing Cockroach)
    const thumbUrl = await page.evaluate(() => window.renderFramePNG(364, { thumbnailMode: true }));
    const thumbPath = path.join(EXPORT_DIR, 'Monarch-Cam-03-Long-Video-Thumbnail-V6-IMAX.png');
    saveDataUrl(thumbUrl, thumbPath);
    console.log(`[Preflight] Saved Hero 1920x1080 Thumbnail -> ${thumbPath}`);

    // 3. Render 16 Key Dramatic Beats across all 7 Chapters (including dark moonlight & end card!)
    const beatFrames = [
      { f:   18, label: '01_CH1_MOONLIGHT_SWITCH' },
      { f:   68, label: '02_CH1_WHIP_DIVE_BOLT' },
      { f:  280, label: '03_CH1_TWO_PENNIES' },
      { f:  386, label: '04_CH1_CLIMAX1_PURE' },
      { f:  640, label: '05_CH1_BULLET_ORBIT' },
      { f:  965, label: '06_CH2_LAB_VOLUMETRIC' },
      { f: 1852, label: '07_CH2_LASER_SCAN' },
      { f: 2110, label: '08_CH2_XRAY_HINGES' },
      { f: 3440, label: '09_CH3_3LANE_CLIFF' },
      { f: 4260, label: '10_CH4_LASER_CLAWS_OFF' },
      { f: 4422, label: '11_CH4_PUSHUP_SHOCKWAVE' },
      { f: 4780, label: '12_CH4_CLIMAX2_SPARKS' },
      { f: 6440, label: '13_CH5_GRIT_TRADEOFF' },
      { f: 6790, label: '14_CH6_900X_SLAM' },
      { f: 7952, label: '15_CH6_GATE_FAIL_83' },
      { f: 8984, label: '16_CH7_PNAS_BOKEH_CARD' },
    ];

    for (let i = 0; i < beatFrames.length; i++) {
      const bf = beatFrames[i];
      const pngUrl = await page.evaluate((fr) => window.renderFramePNG(fr, { showHud: true }), bf.f);
      const p = path.join(STILLS_DIR, `beat_${String(i).padStart(2, '0')}.png`);
      saveDataUrl(pngUrl, p);
      console.log(`[Preflight] Beat ${i + 1}/16 (f=${bf.f} ${bf.label}) rendered`);
    }

    // Assemble 4x4 16:9 Contact Sheet (2560x1440) + print per-beat mean_luma!
    const sheetPath = path.join(EXPORT_DIR, 'Monarch-Cam-03-Long-Video-16Beat-QA-Sheet-V6-IMAX.jpg');
    execFileSync('python3', ['-c', `
import sys
sys.path.insert(0, '/tmp/py')
import numpy as np
from PIL import Image, ImageDraw
W_CELL, H_CELL = 640, 360
sheet = Image.new('RGB', (W_CELL * 4, H_CELL * 4), (8, 12, 16))
labels = ${JSON.stringify(beatFrames.map((b) => `f=${b.f} ${b.label}`))}
for idx in range(16):
    im_full = Image.open(f'${STILLS_DIR}/beat_{idx:02d}.png').convert('RGB')
    luma = float(np.asarray(im_full, dtype=np.float32).mean())
    print(f'  [LumaCheck] {labels[idx]}: mean_luma = {luma:.2f}')
    im = im_full.resize((W_CELL, H_CELL), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im)
    draw.rectangle([8, H_CELL - 30, 310, H_CELL - 6], fill=(0, 0, 0))
    draw.text((14, H_CELL - 24), f"{labels[idx]} (L={luma:.0f})", fill=(255, 215, 140))
    cx, cy = (idx % 4) * W_CELL, (idx // 4) * H_CELL
    sheet.paste(im, (cx, cy))
sheet.save('${sheetPath}', quality=92)
`], { stdio: 'inherit' });
    console.log(`[Preflight] Saved 16-Beat Multi-Chapter QA Sheet -> ${sheetPath}`);
  } finally {
    await browser.close();
  }
}

async function runFullRender(vitePort, opts) {
  fs.mkdirSync(PLATES_DIR, { recursive: true });
  fs.mkdirSync(EXPORT_DIR, { recursive: true });

  // Clean up any incomplete .pending.mp4 files so completed chunks resume cleanly!
  for (const old of fs.readdirSync(PLATES_DIR)) {
    if (old.endsWith('.pending.mp4')) {
      fs.unlinkSync(path.join(PLATES_DIR, old));
    }
  }

  const { width, height, chunkSize, workers } = opts;
  const allChunks = [];
  for (let a = 0; a < TOTAL_FRAMES; a += chunkSize) {
    const ci = allChunks.length;
    const base = path.join(PLATES_DIR, `plate_${String(ci).padStart(3, '0')}`);
    allChunks.push({ ci, a, b: Math.min(TOTAL_FRAMES, a + chunkSize), outMp4: `${base}.mp4`, outJson: `${base}.json` });
  }
  const allPending = allChunks.filter((c) => !(fs.existsSync(c.outMp4) && fs.existsSync(c.outJson)));
  const pendingChunks = allPending.slice(0, opts.maxChunks);
  console.log(`[Resume] ${allChunks.length - allPending.length}/${allChunks.length} chunks complete; rendering batch of ${pendingChunks.length}/${allPending.length} remaining chunks (${width}x${height}, ${workers} workers)...`);

  if (pendingChunks.length === 0) return;

  const activePipes = new Map();
  const wsServer = await startRawWSServer(width * height * 4, async (wid, frameBuf) => {
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
      const page = await browser.newPage({ viewport: { width, height } });
      await page.goto(`http://127.0.0.1:${vitePort}/tools/monarch-cockroach/long_v6/page_long_v6.html?w=${width}&h=${height}`);
      await page.waitForFunction(() => window.__LONG_V6_READY__ === true, null, { timeout: 60000 });

      if (wid === 0 && !fs.existsSync(path.join(OVERLAYS_DIR, 'overlays_manifest_v6.json'))) {
        await exportOverlaysIfNeeded(page);
      }

      await page.evaluate(([p, w]) => window.connectRawWS(p, w), [wsPort, wid]);

      while (nextIdx < pendingChunks.length) {
        const job = pendingChunks[nextIdx++];
        const { ci, a, b, outMp4, outJson } = job;
        const pendingMp4 = `${outMp4}.pending.mp4`;
        const ff = startRawFfmpegPipe(pendingMp4, width, height);
        activePipes.set(wid, ff);

        const chunkMeta = [];
        const SUB = 50;
        for (let f = a; f < b; f += SUB) {
          const part = await page.evaluate(
            ([fa, fb]) => window.streamBeautyFramesWS(fa, fb),
            [f, Math.min(b, f + SUB)]
          );
          chunkMeta.push(...part);
        }

        ff.stdin.end();
        await ff.done;
        activePipes.delete(wid);
        fs.writeFileSync(outJson, JSON.stringify(chunkMeta));
        fs.renameSync(pendingMp4, outMp4);

        doneFrames += (b - a);
        const sec = (Date.now() - t0) / 1000;
        const fps = doneFrames / Math.max(0.1, sec);
        const remS = ((pendingChunks.reduce((s, c) => s + (c.b - c.a), 0) - doneFrames) / Math.max(0.1, fps));
        console.log(`[W${wid}] Chunk ${ci + 1}/${allChunks.length} [${a}..${b}) done | +${doneFrames}f | ${fps.toFixed(2)} fps | ETA ${remS.toFixed(0)}s`);
      }
    } finally {
      await browser.close();
    }
  }

  try {
    await Promise.all(Array.from({ length: workers }, (_, w) => runWorker(w)));
  } finally {
    wsServer.close();
  }
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
    if (opts.mode === 'thumb') {
      const browser = await launchBrowser();
      try {
        const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
        await page.goto(`http://127.0.0.1:${vitePort}/tools/monarch-cockroach/long_v6/page_long_v6.html?w=1920&h=1080`);
        await page.waitForFunction(() => window.__LONG_V6_READY__ === true, null, { timeout: 60000 });
        const thumbUrl = await page.evaluate(() => window.renderFramePNG(352, { thumbnailMode: true }));
        const thumbPath = path.join(EXPORT_DIR, 'Monarch-Cam-03-Long-Video-Thumbnail-V6-IMAX.png');
        saveDataUrl(thumbUrl, thumbPath);
        console.log(`[Thumb] Saved Hero 1920x1080 Thumbnail -> ${thumbPath}`);
      } finally {
        await browser.close();
      }
    } else if (opts.mode === 'preflight') {
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
