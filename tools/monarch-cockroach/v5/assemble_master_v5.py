#!/usr/bin/env python3
"""
Monarch Cam #03 — V5 Native 1920x1080 Master Compositor, QA Sheet Builder & EBU R128 Muxer!
1. Bakes all 32 Space Grotesk + IBM Plex Mono editorial cards, 3 comparison gauges,
   and 1 PNAS Primary Source card as lossless 1920x1080 RGBA PNG sprites via Chromium.
2. Streams /tmp/v5_build/beauty_plate_v5.mp4 (Lanczos + accurate_rnd + unsharp -> 1920x1080),
   composites ROI-cropped RGBA typography + 2x-supersampled 3D-tracked leader lines in numpy/PIL
   (enforcing 100% zero-overlay on all 4 Protected Climax Windows), and encodes + muxes
   exports/monarch-cam-03-v5/Monarch-Cam-03-Long-Video-V5.mp4 (< 85 MB decimal, bt709, +faststart).
3. Builds the 8-Panel Native Visual QA Sheet `Monarch-Cam-03-7-Chapter-QA-Sheet-V5.jpg`.
"""
import glob
import json
import math
import os
import subprocess
import time
import numpy as np
from PIL import Image, ImageDraw

ROOT = "/home/user/Top1"
BUILD_DIR = "/tmp/v5_build"
PLATES_DIR = os.path.join(BUILD_DIR, "plates")
SPRITES_DIR = os.path.join(BUILD_DIR, "overlay_sprites")
EXPORT_DIR = os.path.join(ROOT, "exports/monarch-cam-03-v5")
FFMPEG_BIN = glob.glob("/tmp/py/imageio_ffmpeg/binaries/ffmpeg*")[0]
RAW_PLATE = os.path.join(BUILD_DIR, "beauty_plate_v5.mp4")
AUDIO_WAV = os.path.join(BUILD_DIR, "Monarch-Cam-03-Long-Video-Master-Mix-V5.wav")
OUT_MP4 = os.path.join(EXPORT_DIR, "Monarch-Cam-03-Long-Video-V5.mp4")
OUT_QA_JPG = os.path.join(EXPORT_DIR, "Monarch-Cam-03-7-Chapter-QA-Sheet-V5.jpg")

W, H = 1920, 1080
TOTAL_FRAMES = 9008

PROTECTED_WINDOWS = [
    (330, 538),
    (4662, 4923),
    (8143, 8502),
    (8922, 8956),
]

TARGET_KEYS = ["head", "pronotum", "abdomen", "plate", "hinge", "r3Spine", "r3Claw", "pennies", "platen", "cram"]


def is_protected(f: int) -> bool:
    return any(a <= f < b for a, b in PROTECTED_WINDOWS)


def smooth(a: float, b: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - a) / max(1e-5, b - a)))
    return t * t * (3.0 - 2.0 * t)


def envelope(f: int, a: int, b: int, fade_in: int = 10, fade_out: int = 9) -> float:
    if f < a or f > b:
        return 0.0
    return smooth(a, a + fade_in, f) * (1.0 - smooth(b - fade_out, b, f))


def hex_to_rgb(hx: str):
    hx = hx.lstrip("#")
    return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16))


def bake_chromium_sprites():
    os.makedirs(SPRITES_DIR, exist_ok=True)
    manifest_path = os.path.join(SPRITES_DIR, "sprites_manifest.json")
    print("Baking 36 native 1920x1080 Space Grotesk + IBM Plex Mono V5 sprites via Chromium...")
    js_code = r"""
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const req = createRequire('/tmp/v4_runtime/package.json');
const { createServer } = req('vite');
const { chromium } = req('playwright-core');

const vite = await createServer({
  root: '/home/user/Top1',
  server: { port: 0, host: '127.0.0.1', fs: { allow: ['/home/user/Top1', '/tmp/v4_runtime'] } },
  logLevel: 'error',
});
await vite.listen();
const vp = vite.httpServer.address().port;

const browser = await chromium.launch({
  executablePath: '/tmp/chromium',
  headless: true,
  env: {
    ...process.env,
    LD_LIBRARY_PATH: '/tmp/sparticuz_libs/al2023/lib:/tmp/sparticuz_libs/swiftshader',
    FONTCONFIG_PATH: '/tmp/sparticuz_libs/fonts',
  },
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});

const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(`http://127.0.0.1:${vp}/tools/monarch-cockroach/v5/page_v5.html?titlesOnly=1`);
await page.waitForFunction(() => window.__MONARCH_V5_READY__ === true);

const data = await page.evaluate(async () => {
  const mod = await import('/tools/monarch-cockroach/v5/titles_v5.js');
  const comp = mod.createEditorialCompositorV5();
  const calls = mod.EDITORIAL_CALLS_V5;
  const outCalls = [];

  for (let i = 0; i < calls.length; i++) {
    const c = calls[i];
    const midFrame = Math.min(c.b - 10, c.a + 20);
    comp.renderOverlayTransparent(midFrame, null, null);
    outCalls.push({
      idx: i,
      a: c.a, b: c.b, x: c.x, y: c.y, size: c.size,
      col: c.col, tail: Boolean(c.tail), target: c.target || null,
      png: comp.canvas.toDataURL('image/png'),
    });
  }

  comp.renderOverlayTransparent(3450, null, null);
  const gaugeHeightPng = comp.canvas.toDataURL('image/png');

  comp.renderOverlayTransparent(6400, null, null);
  const gaugeGritPng = comp.canvas.toDataURL('image/png');

  comp.renderOverlayTransparent(7800, null, null);
  const gaugeGatePng = comp.canvas.toDataURL('image/png');

  comp.renderOverlayTransparent(8990, null, null);
  const endCardPng = comp.canvas.toDataURL('image/png');

  return { outCalls, gaugeHeightPng, gaugeGritPng, gaugeGatePng, endCardPng };
});

const dir = '/tmp/v5_build/overlay_sprites';
const manifest = { calls: [], gauges: {} };
for (const c of data.outCalls) {
  const p = path.join(dir, `call_${String(c.idx).padStart(2, '0')}.png`);
  fs.writeFileSync(p, Buffer.from(c.png.split(',')[1], 'base64'));
  delete c.png;
  c.path = p;
  manifest.calls.push(c);
}
for (const [k, b64] of [['height', data.gaugeHeightPng], ['grit', data.gaugeGritPng], ['gate', data.gaugeGatePng], ['end', data.endCardPng]]) {
  const p = path.join(dir, `gauge_${k}.png`);
  fs.writeFileSync(p, Buffer.from(b64.split(',')[1], 'base64'));
  manifest.gauges[k] = p;
}
fs.writeFileSync(path.join(dir, 'sprites_manifest.json'), JSON.stringify(manifest, null, 2));
await browser.close();
await vite.close();
"""
    subprocess.run(["node", "--input-type=module", "-e", js_code], check=True)
    with open(manifest_path, "r") as fh:
        return json.load(fh)


def load_sprite_roi(png_path: str, y_min: int = 0, y_max: int = H):
    im = Image.open(png_path).convert("RGBA")
    arr = np.array(im, dtype=np.uint8)
    if y_min > 0:
        arr[:y_min, :, 3] = 0
    if y_max < H:
        arr[y_max:, :, 3] = 0
    ys, xs = np.where(arr[:, :, 3] > 0)
    if len(xs) == 0:
        return None
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    crop = arr[y0:y1, x0:x1]
    return {
        "x0": x0, "y0": y0, "w": x1 - x0, "h": y1 - y0,
        "rgb": crop[:, :, :3].astype(np.float32),
        "alpha": (crop[:, :, 3:4].astype(np.float32) / 255.0),
    }


def blend_roi(frame_rgb: np.ndarray, sprite, opacity: float, dy: int = 0):
    if sprite is None or opacity <= 0.004:
        return
    x0 = sprite["x0"]
    y0 = sprite["y0"] + dy
    h, w = sprite["h"], sprite["w"]
    if y0 < 0 or y0 + h > H:
        return
    dst = frame_rgb[y0:y0 + h, x0:x0 + w].astype(np.float32)
    a = sprite["alpha"] * opacity
    blended = dst * (1.0 - a) + sprite["rgb"] * a
    frame_rgb[y0:y0 + h, x0:x0 + w] = np.clip(blended, 0, 255).astype(np.uint8)


def draw_tracked_leader(frame_rgb: np.ndarray, call: dict, frame: int, opacity: float, dy: float, coords):
    t_key = call.get("target")
    if not t_key or coords is None:
        return
    idx = TARGET_KEYS.index(t_key)
    nx, ny = coords[idx * 2], coords[idx * 2 + 1]
    if nx < 0 or ny < 0:
        return
    pt_x, pt_y = nx * W, ny * H
    if not (80 < pt_x < W - 80 and 230 < pt_y < H - 80):
        return

    start_x = call["x"] + 260.0
    start_y = call["y"] + call["size"] * 0.52 + (62.0 if call["tail"] else 22.0) + dy
    dist = math.hypot(pt_x - start_x, pt_y - start_y)
    if not (75.0 < dist < 960.0):
        return

    grow = smooth(call["a"] + 5, call["a"] + 20, frame)
    ux = (pt_x - start_x) / dist
    uy = (pt_y - start_y) / dist
    end_x = start_x + (dist - 18.0) * grow * ux
    end_y = start_y + (dist - 18.0) * grow * uy
    knee_x = start_x + (end_x - start_x) * 0.42

    bx0 = max(0, int(min(start_x, pt_x)) - 18)
    by0 = max(0, int(min(start_y, pt_y)) - 18)
    bx1 = min(W, int(max(start_x, pt_x)) + 18)
    by1 = min(H, int(max(start_y, pt_y)) + 18)
    bw, bh = bx1 - bx0, by1 - by0
    if bw <= 4 or bh <= 4:
        return

    ss = Image.new("RGBA", (bw * 2, bh * 2), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ss)
    r, g, b = hex_to_rgb(call["col"])
    a_byte = int(max(0, min(255, round(opacity * 0.80 * 255))))
    pts = [
        ((start_x - bx0) * 2, (start_y - by0) * 2),
        ((knee_x - bx0) * 2,  (start_y - by0) * 2),
        ((end_x - bx0) * 2,   (end_y - by0) * 2),
    ]
    dr.line(pts, fill=(r, g, b, a_byte), width=4)
    cx, cy = (pt_x - bx0) * 2, (pt_y - by0) * 2
    dr.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], outline=(r, g, b, a_byte), width=4)

    down = np.array(ss.resize((bw, bh), Image.Resampling.BILINEAR), dtype=np.float32)
    la = down[:, :, 3:4] / 255.0
    dst = frame_rgb[by0:by1, bx0:bx1].astype(np.float32)
    frame_rgb[by0:by1, bx0:bx1] = np.clip(dst * (1.0 - la) + down[:, :, :3] * la, 0, 255).astype(np.uint8)


def build_qa_sheet():
    stills = sorted(glob.glob(os.path.join(BUILD_DIR, "chapter_stills", "ch_*.jpg")))
    if len(stills) < 8:
        return
    sheet = Image.new("RGB", (3840, 2160), (8, 15, 19))
    for i, sp in enumerate(stills[:8]):
        im = Image.open(sp).convert("RGB").resize((960, 540), Image.Resampling.LANCZOS)
        # 2 cols x 4 rows at 1920x540? Wait: 2x4 or 4x2: 4 cols x 2 rows = 3840x1080! Let's make crisp 2 cols x 4 rows (3840x4320 -> 2560x2880)!
    # Crisp 2x4 UHD grid (2560 x 2880, each panel 1280x720!)
    sheet = Image.new("RGB", (2560, 2880), (8, 15, 19))
    for i, sp in enumerate(stills[:8]):
        im = Image.open(sp).convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS)
        x = (i % 2) * 1280
        y = (i // 2) * 720
        sheet.paste(im, (x, y))
    sheet.save(OUT_QA_JPG, quality=93)
    print(f"Saved 8-Panel Visual QA Sheet V5 -> {OUT_QA_JPG} ({os.path.getsize(OUT_QA_JPG):,} bytes)")


def main():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    build_qa_sheet()
    manifest = bake_chromium_sprites()

    call_sprites = [load_sprite_roi(c["path"], 0, 520) for c in manifest["calls"]]
    gauge_height = load_sprite_roi(manifest["gauges"]["height"], 780, H)
    gauge_grit   = load_sprite_roi(manifest["gauges"]["grit"],   780, H)
    gauge_gate   = load_sprite_roi(manifest["gauges"]["gate"],   740, H)
    end_card     = load_sprite_roi(manifest["gauges"]["end"],    0,   H)

    coords_by_frame = [None] * TOTAL_FRAMES
    for jf in sorted(glob.glob(os.path.join(PLATES_DIR, "*.json"))):
        with open(jf, "r") as fh:
            for row in json.load(fh):
                coords_by_frame[row[0]] = row[1:]
    assert all(c is not None for c in coords_by_frame), "Missing landmark frame!"
    print(f"Loaded all {TOTAL_FRAMES} 3D landmark rows.")

    dec_cmd = [
        FFMPEG_BIN, "-v", "error",
        "-i", RAW_PLATE,
        "-vf", "scale=1920:1080:flags=lanczos+accurate_rnd,unsharp=3:3:0.32:3:3:0.0",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
    ]
    enc_cmd = [
        FFMPEG_BIN, "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", "30", "-i", "-",
        "-i", AUDIO_WAV,
        "-filter_complex", "[1:a]volume=-0.4dB[aout]",
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-maxrate", "2250k", "-bufsize", "4500k",
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
        "-movflags", "+faststart",
        "-frames:v", str(TOTAL_FRAMES),
        OUT_MP4,
    ]

    dec = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)
    enc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE, bufsize=W * H * 3 * 2)

    frame_bytes = W * H * 3
    t0 = time.time()
    calls = manifest["calls"]

    for f in range(TOTAL_FRAMES):
        raw = dec.stdout.read(frame_bytes)
        if len(raw) != frame_bytes:
            raise RuntimeError(f"Short read at frame {f}: got {len(raw)} bytes")

        if is_protected(f):
            enc.stdin.write(raw)
        else:
            active_calls = [c for c in calls if c["a"] <= f <= c["b"]]
            has_gauge = (3300 <= f <= 3595) or (6235 <= f <= 6578) or (7625 <= f <= 8018) or (f >= 8956)
            if not active_calls and not has_gauge:
                enc.stdin.write(raw)
            else:
                arr = np.frombuffer(raw, dtype=np.uint8).reshape((H, W, 3)).copy()
                for c in active_calls:
                    op = envelope(f, c["a"], c["b"], 10, 9)
                    settle = smooth(c["a"], c["a"] + 14, f)
                    dy = int(round((1.0 - settle) * 14.0))
                    blend_roi(arr, call_sprites[c["idx"]], op, dy)
                    draw_tracked_leader(arr, c, f, op, dy, coords_by_frame[f])

                if 3300 <= f <= 3595:
                    blend_roi(arr, gauge_height, envelope(f, 3300, 3595, 10, 10), 0)
                if 6235 <= f <= 6578:
                    blend_roi(arr, gauge_grit, envelope(f, 6235, 6578, 10, 10), 0)
                if 7625 <= f <= 8018:
                    blend_roi(arr, gauge_gate, envelope(f, 7625, 8018, 10, 10), 0)
                if f >= 8956:
                    op_end = smooth(8956, 8970, f) * (1.0 - smooth(8996, 9007, f))
                    blend_roi(arr, end_card, op_end, 0)

                enc.stdin.write(arr.tobytes())

        if f > 0 and f % 1500 == 0:
            dt = time.time() - t0
            print(f"Composited & encoded {f}/{TOTAL_FRAMES} frames ({f / dt:.1f} fps, {dt:.1f}s elapsed)...")

    enc.stdin.close()
    dec.stdout.close()
    dec.wait()
    rc = enc.wait()
    if rc != 0:
        raise RuntimeError(f"Encoder exited with {rc}")

    sz = os.path.getsize(OUT_MP4)
    print(f"DONE in {time.time() - t0:.1f}s! Master V5 -> {OUT_MP4} ({sz:,} bytes = {sz / 1e6:.2f} MB decimal)")


if __name__ == "__main__":
    main()
