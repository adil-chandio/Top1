#!/usr/bin/env python3
"""
Stitches all 690 Blender Cycles PNG frames, Lanczos upscales to 1080x1920,
burns in bold Zack D. Films Roman Urdu kinetic captions, and muxes with master_audio.m4a!
"""
import json
import os
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

FRAMES_DIR = sys.argv[1]
OUT_MP4 = sys.argv[2]
LOCK_PATH = "tools/thermal-shock/voice-lock.json"
AUDIO_PATH = "tools/thermal-shock-blender/master_audio.m4a"
COMP_DIR = "/tmp/comp_frames"
os.makedirs(COMP_DIR, exist_ok=True)

with open(LOCK_PATH, "r", encoding="utf-8") as f:
    LOCK = json.load(f)

TOTAL_FRAMES = LOCK["total_frames"]
SHATTER_F = LOCK["shatter_frame"]
CAPTIONS = LOCK["captions"]

def find_font(size):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

FONT_STD = find_font(62)
FONT_HOT = find_font(72)

def active_caption(f):
    if SHATTER_F <= f < SHATTER_F + 16:
        return ""
    for c in CAPTIONS:
        if c["f0"] <= f <= c["f1"]:
            return c["text"]
    return ""

last_src = None
for f in range(TOTAL_FRAMES):
    src = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
    if not os.path.exists(src):
        if last_src is not None:
            src = last_src
        else:
            # Find first available frame
            for k in range(f + 1, TOTAL_FRAMES):
                cand = os.path.join(FRAMES_DIR, f"frame_{k:04d}.png")
                if os.path.exists(cand):
                    src = cand
                    break
    last_src = src
    img = Image.open(src).convert("RGB").resize((1080, 1920), Image.Resampling.LANCZOS)
    cap = active_caption(f)
    if cap:
        draw = ImageDraw.Draw(img)
        is_hot = ("THERMAL SHOCK" in cap) or ("PHAAD DETA" in cap)
        font = FONT_HOT if is_hot else FONT_STD
        bbox = draw.textbbox((0, 0), cap, font=font, stroke_width=8)
        tw = bbox[2] - bbox[0]
        x = (1080 - tw) // 2
        y = int(1920 * 0.75)
        draw.text(
            (x, y), cap, font=font,
            fill=(255, 224, 51) if is_hot else (255, 255, 255),
            stroke_width=8, stroke_fill=(0, 0, 0),
        )
    img.save(os.path.join(COMP_DIR, f"frame_{f:04d}.png"), compress_level=1)

subprocess.run([
    "ffmpeg", "-y",
    "-framerate", "30",
    "-i", os.path.join(COMP_DIR, "frame_%04d.png"),
    "-i", AUDIO_PATH,
    "-c:v", "libx264", "-preset", "medium", "-crf", "16",
    "-pix_fmt", "yuv420p", "-colorspace", "bt709",
    "-af", "alimiter=limit=0.708:level=false",
    "-c:a", "aac", "-b:a", "320k",
    "-movflags", "+faststart",
    "-shortest",
    OUT_MP4,
], check=True)
print(f"[Assemble] Master ready -> {OUT_MP4}")
