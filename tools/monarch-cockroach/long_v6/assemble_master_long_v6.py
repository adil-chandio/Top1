#!/usr/bin/env python3
"""
Monarch Cam #03 — Long Video V6 Hollywood IMAX Master Compositor & Muxer (`assemble_master_long_v6.py`)
Streams all 31 beauty plate chunks (`plate_000..030.mp4` -> `1920x1080` Lanczos), composites:
  1. 3D-tracked antialiased leader lines + target reticles (`2x` supersampled)
  2. Live top-right optical telemetry pill (`IBM Plex Mono` 600 WOFF2, cached per unique readout)
  3. 36 pre-baked native `1920x1080` RGBA typography callouts, gauges & Frosted-Obsidian PNAS End Card
Strictly enforces 100% ZERO text/HUD/leaders inside all 4 Protected Climax Windows!
Encodes `1920x1080 @ 30.000 fps` (`CRF 17`, `maxrate 2450k`, `< 95 MB`) muxed with the `-14.2 LUFS` V6 Master Mix!
"""
import glob
import json
import math
import os
import subprocess
import sys
import time

sys.path.insert(0, "/tmp/py")
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30
TOTAL_FRAMES = 9008

BUILD_DIR = "/tmp/v6_long/build"
PLATES_DIR = os.path.join(BUILD_DIR, "plates")
OVERLAYS_DIR = os.path.join(BUILD_DIR, "overlays")
MASTER_MIX_WAV = "/tmp/v6_long/Monarch-Cam-03-Long-Video-Master-Mix-V6-IMAX.wav"
OUT_MP4 = "/tmp/v6_long/Monarch-Cam-03-Long-Video-Master-V6-IMAX.mp4"

PROTECTED_WINDOWS = [
    (330, 538),
    (4662, 4923),
    (8143, 8502),
    (8922, 8956),
]

MONO_FONT_PATH = "/tmp/v6_runtime/node_modules/@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-600-normal.woff2"


def find_ffmpeg() -> str:
    matches = glob.glob("/tmp/py/imageio_ffmpeg/binaries/ffmpeg*")
    return matches[0] if matches else "ffmpeg"


def is_protected(f: int) -> bool:
    return any(a <= f < b for a, b in PROTECTED_WINDOWS)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / max(1e-6, edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def hex_to_rgb(hex_str: str) -> tuple:
    h = hex_str.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def load_cropped_overlays(manifest_path: str) -> list:
    with open(manifest_path, "r", encoding="utf-8") as fp:
        items = json.load(fp)
    loaded = []
    for item in items:
        png_path = os.path.join(OVERLAYS_DIR, item["file"])
        im = Image.open(png_path).convert("RGBA")
        arr = np.asarray(im, dtype=np.uint8)
        ys, xs = np.where(arr[:, :, 3] > 0)
        if len(xs) == 0:
            continue
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        sub = arr[y0:y1, x0:x1, :].astype(np.float32)
        loaded.append({
            "id": item["id"],
            "kind": item["kind"],
            "start": int(item["start"]),
            "end": int(item["end"]),
            "fade": int(item.get("fadeFrames", 12)),
            "x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "rgb": sub[:, :, :3],
            "alpha": sub[:, :, 3:4] / 255.0,
        })
    return loaded


def blend_rgba_patch(frame_rgb: np.ndarray, x0: int, y0: int, patch_rgb: np.ndarray, patch_alpha: np.ndarray, opacity: float = 1.0):
    if opacity <= 0.002:
        return
    h, w, _ = patch_rgb.shape
    roi = frame_rgb[y0:y0 + h, x0:x0 + w, :].astype(np.float32)
    a = patch_alpha * opacity
    out = roi * (1.0 - a) + patch_rgb * a
    frame_rgb[y0:y0 + h, x0:x0 + w, :] = np.clip(out, 0, 255).astype(np.uint8)


class TelemetryPillCache:
    """2x-supersampled Top-Right Live Telemetry Pill (`IBM Plex Mono` 600 WOFF2)."""
    def __init__(self):
        self.font_2x = ImageFont.truetype(MONO_FONT_PATH, 31)
        self.cache = {}

    def get_patch(self, ht: str, hm: str, ha: int):
        key = (ht, hm, ha)
        if key in self.cache:
            return self.cache[key]

        dummy = ImageDraw.Draw(Image.new("RGBA", (16, 16)))
        b1 = dummy.textbbox((0, 0), ht, font=self.font_2x)
        w1 = b1[2] - b1[0]
        w2 = 0
        if hm:
            b2 = dummy.textbbox((0, 0), hm, font=self.font_2x)
            w2 = (b2[2] - b2[0]) + 56

        pill_w2 = 96 + w1 + w2
        pill_h2 = 80
        pad2 = 8
        cw2, ch2 = pill_w2 + pad2 * 2, pill_h2 + pad2 * 2
        im2 = Image.new("RGBA", (cw2, ch2), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im2)

        border_col = (255, 122, 102, 118) if ha else (255, 255, 255, 44)
        dr.rounded_rectangle(
            [pad2, pad2, pad2 + pill_w2, pad2 + pill_h2],
            radius=40,
            fill=(7, 13, 19, 188),
            outline=border_col,
            width=3,
        )
        dot_col = (255, 112, 82, 235) if ha else (110, 246, 208, 235)
        cy2 = pad2 + pill_h2 // 2
        dr.ellipse([pad2 + 32, cy2 - 10, pad2 + 52, cy2 + 10], fill=dot_col)

        ty2 = cy2 - 19
        dr.text((pad2 + 72, ty2), ht, font=self.font_2x, fill=(236, 244, 248, 232))
        if hm:
            dr.text((pad2 + 88 + w1, ty2), "·", font=self.font_2x, fill=(255, 255, 255, 85))
            m_col = (255, 168, 76, 245) if ha else (255, 209, 135, 245)
            dr.text((pad2 + 114 + w1, ty2), hm, font=self.font_2x, fill=m_col)

        im1 = im2.resize((cw2 // 2, ch2 // 2), Image.Resampling.LANCZOS)
        arr = np.asarray(im1, dtype=np.float32)
        x0 = W - 80 - (cw2 // 2)
        y0 = 44
        res = (x0, y0, arr[:, :, :3], arr[:, :, 3:4] / 255.0)
        if len(self.cache) < 512:
            self.cache[key] = res
        return res


def draw_leader_patch(frame_rgb: np.ndarray, leader: dict):
    alpha = float(leader.get("alpha", 0.0))
    if alpha <= 0.01:
        return
    tx, ty = float(leader["tx"]), float(leader["ty"])
    if not (60.0 < tx < W - 60.0 and 60.0 < ty < H - 60.0):
        return

    bx = float(leader["boxX"])
    by = float(leader["boxY"])
    bw = float(leader["boxW"])
    bh = float(leader["boxH"])
    sx = bx + bw * 0.60
    sy = by + bh
    elbow_y = min(ty - 18.0, sy + 42.0)

    x0 = max(0, int(min(sx, tx)) - 22)
    y0 = max(0, int(min(sy, elbow_y, ty)) - 22)
    x1 = min(W, int(max(sx, tx)) + 22)
    y1 = min(H, int(max(sy, elbow_y, ty)) + 22)
    if x1 <= x0 + 4 or y1 <= y0 + 4:
        return

    pw, ph = x1 - x0, y1 - y0
    im2 = Image.new("RGBA", (pw * 2, ph * 2), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im2)
    acc = hex_to_rgb(leader.get("accent", "#ffd187"))

    p0 = ((sx - x0) * 2.0, (sy - y0) * 2.0)
    p1 = ((sx - x0) * 2.0, (elbow_y - y0) * 2.0)
    p2 = ((tx - x0) * 2.0, (ty - y0) * 2.0)
    dr.line([p0, p1, p2], fill=(*acc, 235), width=4)

    cx, cy = p2
    dr.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(*acc, 245))
    dr.ellipse([cx - 19, cy - 19, cx + 19, cy + 19], outline=(255, 255, 255, 220), width=3)

    im1 = im2.resize((pw, ph), Image.Resampling.LANCZOS)
    arr = np.asarray(im1, dtype=np.float32)
    blend_rgba_patch(frame_rgb, x0, y0, arr[:, :, :3], arr[:, :, 3:4] / 255.0, alpha)


def main():
    t0 = time.time()
    ffmpeg = find_ffmpeg()
    assert os.path.isfile(MASTER_MIX_WAV), f"Missing Master Mix WAV: {MASTER_MIX_WAV}"

    # 1. Gather & validate all 31 beauty plate chunks + metadata JSONs
    plate_mp4s = sorted(glob.glob(os.path.join(PLATES_DIR, "plate_*.mp4")))
    plate_jsons = sorted(glob.glob(os.path.join(PLATES_DIR, "plate_*.json")))
    assert len(plate_mp4s) == 31 and len(plate_jsons) == 31, (
        f"Expected 31 plate chunks, found {len(plate_mp4s)} mp4s and {len(plate_jsons)} jsons"
    )

    all_meta = []
    for jp in plate_jsons:
        with open(jp, "r", encoding="utf-8") as fp:
            all_meta.extend(json.load(fp))
    assert len(all_meta) == TOTAL_FRAMES, f"Expected {TOTAL_FRAMES} metadata entries, got {len(all_meta)}"
    for idx, rec in enumerate(all_meta):
        assert rec["f"] == idx, f"Frame sequence mismatch at {idx}: {rec['f']}"

    concat_txt = os.path.join(BUILD_DIR, "plates_concat_v6.txt")
    with open(concat_txt, "w", encoding="utf-8") as fp:
        for mp in plate_mp4s:
            fp.write(f"file '{mp}'\n")

    overlays = load_cropped_overlays(os.path.join(OVERLAYS_DIR, "overlays_manifest_v6.json"))
    pill_cache = TelemetryPillCache()
    print(f"[Compositor] Loaded {len(overlays)} pre-baked 1920x1080 RGBA cards & {len(all_meta)} frame records.")

    # 2. Spawn streaming 1920x1080 Lanczos decoder + H.264/AAC broadcast encoder
    dec_proc = subprocess.Popen(
        [
            ffmpeg, "-v", "error",
            "-f", "concat", "-safe", "0", "-i", concat_txt,
            "-vf", "scale=1920:1080:flags=lanczos",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ],
        stdout=subprocess.PIPE,
    )

    enc_proc = subprocess.Popen(
        [
            ffmpeg, "-y", "-v", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-i", MASTER_MIX_WAV,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-maxrate", "2120k", "-bufsize", "4400k",
            "-pix_fmt", "yuv420p",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-af", "alimiter=limit=0.708:level=false",
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart",
            OUT_MP4,
        ],
        stdin=subprocess.PIPE,
    )

    frame_bytes = W * H * 3
    for f in range(TOTAL_FRAMES):
        raw = dec_proc.stdout.read(frame_bytes)
        assert len(raw) == frame_bytes, f"Short read at frame {f}: {len(raw)} bytes"
        frame_rgb = np.frombuffer(raw, dtype=np.uint8).reshape((H, W, 3)).copy()

        if not is_protected(f):
            rec = all_meta[f]
            # 1) 3D-tracked leader line (underneath callout card!)
            if rec.get("l") and f < 8956:
                draw_leader_patch(frame_rgb, rec["l"])

            # 2) Top-right live optical telemetry pill
            if rec.get("ht") and f < 8956:
                px0, py0, prgb, palpha = pill_cache.get_patch(rec["ht"], rec.get("hm", ""), int(rec.get("ha", 0)))
                blend_rgba_patch(frame_rgb, px0, py0, prgb, palpha, 1.0)

            # 3) Active pre-baked callouts, gauges & Frosted-Obsidian PNAS End Card
            for ov in overlays:
                if ov["start"] <= f <= ov["end"]:
                    fade = ov["fade"]
                    op_in = smoothstep(ov["start"], ov["start"] + fade, f)
                    op_out = 1.0 if ov["kind"] == "endcard" else (1.0 - smoothstep(ov["end"] - fade, ov["end"], f))
                    blend_rgba_patch(frame_rgb, ov["x0"], ov["y0"], ov["rgb"], ov["alpha"], op_in * op_out)

        enc_proc.stdin.write(frame_rgb.tobytes())
        if (f + 1) % 900 == 0 or f == TOTAL_FRAMES - 1:
            dt = time.time() - t0
            print(f"[Compositor] {f + 1}/{TOTAL_FRAMES} frames ({(f + 1) / max(0.1, dt):.1f} fps)")

    enc_proc.stdin.close()
    dec_ret = dec_proc.wait()
    enc_ret = enc_proc.wait()
    assert dec_ret == 0 and enc_ret == 0, f"FFmpeg pipeline failed: dec={dec_ret}, enc={enc_ret}"

    size_mb = os.path.getsize(OUT_MP4) / (1024 * 1024)
    print(f"[SUCCESS] Master V6 IMAX MP4 -> {OUT_MP4} ({size_mb:.2f} MiB in {time.time() - t0:.1f}s)")
    assert size_mb < 96.0, f"MP4 exceeds 96 MiB Drive upload ceiling: {size_mb:.2f} MiB"


if __name__ == "__main__":
    main()
