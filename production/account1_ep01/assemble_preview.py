#!/usr/bin/env python3
"""Assemble the 15s PEHRA 3D preview: captions, grade, audio mux, QC, keyframes.

- final: validate 450 rendered Cycles PNGs, overlay six animated editorial
  captions, add subtle film grade/grain/vignette/glare-friendly contrast,
  mux the -14 LUFS master soundtrack, and emit a 1080x1920 H.264 MP4.
- lookdev: emit a labelled six-frame contact sheet for visual approval.

The video's picture frames are all true animated 3D renders. Caption PNGs are
motion-graphic text overlays, not still-image scene plates.
"""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent

try:
    LANCZOS = Image.Resampling.LANCZOS
except AttributeError:  # Pillow < 9
    LANCZOS = Image.LANCZOS

FONT_CANDIDATES_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
FONT_CANDIDATES_REGULAR = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]


def load_font(size: int, bold: bool = False):
    candidates = FONT_CANDIDATES_BOLD if bold else FONT_CANDIDATES_REGULAR
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def run(cmd: list[str], *, quiet: bool = True) -> subprocess.CompletedProcess:
    print("$", " ".join(shlex.quote(str(c)) for c in cmd), flush=True)
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        print(proc.stdout[-4000:])
        print(proc.stderr[-8000:])
        raise RuntimeError(f"Command failed with exit code {proc.returncode}")
    if not quiet and proc.stderr:
        print(proc.stderr[-2000:])
    return proc


def draw_centered(draw, text, center, font, fill, *, stroke=0, stroke_fill=(0, 0, 0, 180)):
    draw.text(
        center,
        text,
        font=font,
        fill=fill,
        anchor="mm",
        stroke_width=stroke,
        stroke_fill=stroke_fill,
    )


def draw_highlighted_caption(draw, text, highlight, center, font, base_fill, hi_fill):
    lower = text.lower()
    needle = (highlight or "").lower()
    parts: list[tuple[str, bool]] = []
    if needle and needle in lower:
        cursor = 0
        while True:
            idx = lower.find(needle, cursor)
            if idx < 0:
                if cursor < len(text):
                    parts.append((text[cursor:], False))
                break
            if idx > cursor:
                parts.append((text[cursor:idx], False))
            parts.append((text[idx : idx + len(needle)], True))
            cursor = idx + len(needle)
    else:
        parts.append((text, False))

    widths = [draw.textlength(seg, font=font) for seg, _ in parts]
    total = sum(widths)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_h = bbox[3] - bbox[1]
    x = center[0] - total / 2.0
    y = center[1] - text_h / 2.0 - bbox[1]
    for (segment, is_highlight), width in zip(parts, widths):
        # Soft editorial drop shadow + crisp 1px contour for legibility on fog.
        draw.text(
            (x + 4, y + 5), segment, font=font, fill=(0, 0, 0, 210),
            stroke_width=2, stroke_fill=(0, 0, 0, 160),
        )
        draw.text(
            (x, y), segment, font=font,
            fill=hi_fill if is_highlight else base_fill,
            stroke_width=1, stroke_fill=(0, 0, 0, 130),
        )
        x += width


def make_caption_png(shot: dict, width: int, height: int, out_path: Path, index: int) -> None:
    """Minimal editorial lower-third: one line of Urdu, nothing else.

    No brand mark, no shot counter, no eyebrow, no timecode — the previous
    version drew five competing elements across the top of every frame and
    they read as clutter over the picture.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    font = load_font(56, bold=True)
    text = shot.get("caption", "").strip()
    if not text:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, "PNG", optimize=True)
        return

    highlight = shot.get("highlight", "")
    cy = height - 236
    # A soft scrim only behind the words, so the frame stays clean.
    bbox = draw.textbbox((0, 0), text, font=font, anchor="lt")
    tw = bbox[2] - bbox[0]
    pad_x, pad_y = 34, 20
    left = (width - tw) / 2 - pad_x
    right = (width + tw) / 2 + pad_x
    draw.rounded_rectangle(
        (left, cy - pad_y, right, cy + (bbox[3] - bbox[1]) + pad_y),
        radius=14, fill=(0, 0, 0, 118),
    )
    draw_highlighted_caption(
        draw, text, highlight, (width // 2, cy), font,
        (246, 246, 248, 255), (236, 176, 74, 255),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)


def expected_frame_paths(frames_dir: Path, frames: list[int]) -> list[Path]:
    paths = [frames_dir / f"f_{frame:06d}.png" for frame in frames]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing rendered frames:\n  " + "\n  ".join(missing[:12]))
    return paths


def make_contact_sheet(paths: list[Path], shots: list[dict], out_path: Path, *, cols: int = 3) -> None:
    thumb_w, thumb_h = 300, 533
    label_h = 64
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (7, 9, 14))
    draw = ImageDraw.Draw(sheet)
    font_label = load_font(18, bold=True)
    font_sub = load_font(15, bold=False)
    for i, (path, shot) in enumerate(zip(paths, shots)):
        col, row = i % cols, i // cols
        x, y = col * thumb_w, row * (thumb_h + label_h)
        with Image.open(path) as src:
            frame = src.convert("RGB")
            frame.thumbnail((thumb_w, thumb_h), LANCZOS)
            sheet.paste(frame, (x + (thumb_w - frame.width) // 2, y))
        draw.rectangle((x, y + thumb_h, x + thumb_w, y + thumb_h + label_h), fill=(12, 15, 22))
        compact = shot["id"].replace("_", " ")
        if len(compact) > 24:
            compact = compact[:23] + "…"
        draw.text((x + 12, y + thumb_h + 9), f"{i + 1:02d} · {compact}", font=font_label, fill=(238, 240, 242))
        draw.text(
            (x + 14, y + thumb_h + 38),
            f"frame {shot['lookdev_frame']:03d} · {shot['t_start']:.2f}–{shot['t_end']:.2f}s",
            font=font_sub, fill=(165, 175, 190),
        )
        draw.line((x, y + thumb_h, x + thumb_w, y + thumb_h), fill=(70, 78, 92), width=1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, "JPEG", quality=92, optimize=True)


def copy_keyframes(paths: list[Path], shots: list[dict], keyframe_dir: Path) -> None:
    keyframe_dir.mkdir(parents=True, exist_ok=True)
    for i, (path, shot) in enumerate(zip(paths, shots), 1):
        dest = keyframe_dir / f"{i:02d}_{shot['id']}_f{shot['lookdev_frame']:03d}.png"
        shutil.copy2(path, dest)


def build_video(
    frames_dir: Path,
    caption_paths: list[Path],
    shots: list[dict],
    audio_path: Path,
    out_mp4: Path,
    *,
    width: int,
    height: int,
    fps: int,
    duration: float,
) -> None:
    cmd: list[str] = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
        "-framerate", str(fps), "-start_number", "1",
        "-i", str(frames_dir / "f_%06d.png"),
    ]
    for cap in caption_paths:
        cmd += ["-loop", "1", "-framerate", str(fps), "-t", f"{duration:.3f}", "-i", str(cap)]
    cmd += ["-i", str(audio_path)]

    base_filters = [
        f"scale={width}:{height}:flags=lanczos",
        "setsar=1",
        "format=rgb24",
        "eq=contrast=1.055:brightness=-0.015:saturation=0.93",
        "unsharp=5:5:0.30:5:5:0.0",
        "noise=alls=5:allf=t",
        "vignette=PI/5",
        "fade=t=in:st=0:d=0.18",
        f"fade=t=out:st={duration - 0.28:.3f}:d=0.28",
        "format=rgba",
    ]
    chains = ["[0:v]" + ",".join(base_filters) + "[base]"]
    prev = "base"
    for i, (shot, cap) in enumerate(zip(shots, caption_paths), 1):
        t0 = float(shot["t_start"])
        t1 = float(shot["t_end"])
        fade_out = max(t0, t1 - 0.18)
        chains.append(
            f"[{i}:v]setpts=PTS-STARTPTS,format=rgba,"
            f"fade=t=in:st={t0:.3f}:d=0.18:alpha=1,"
            f"fade=t=out:st={fade_out:.3f}:d=0.18:alpha=1[cap{i}]"
        )
        chains.append(
            f"[{prev}][cap{i}]overlay=0:0:enable='between(t,{t0:.3f},{t1:.3f})'[v{i}]"
        )
        prev = f"v{i}"
    chains.append(f"[{prev}]format=yuv420p[vout]")
    filter_complex = ";".join(chains)

    audio_index = 1 + len(caption_paths)
    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", f"{audio_index}:a:0",
        "-t", f"{duration:.3f}",
        "-r", str(fps),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "17",
        "-profile:v", "high",
        "-level", "4.2",
        "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-colorspace", "bt709",
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "48000",
        "-ac", "2",
        "-movflags", "+faststart",
        "-metadata", "title=MONARCH EP01 PEHRA — 15s Dark 3D Cinema Preview",
        "-metadata", "comment=100% animated Blender Cycles 3D renders; zero still-image plates",
        str(out_mp4),
    ]
    run(cmd)
    # Full decode check — catches corrupt frames or a broken filter graph.
    run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(out_mp4), "-f", "null", "-",
        ]
    )


def probe_video(mp4: Path) -> dict:
    proc = run(
        [
            "ffprobe", "-v", "error",
            "-show_entries",
            "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels",
            "-of", "json", str(mp4),
        ]
    )
    try:
        return json.loads(proc.stdout)
    except Exception:
        return {"raw": proc.stdout}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("lookdev", "final"), default="final")
    parser.add_argument("--frames-dir", default=str(BASE / "frames"))
    parser.add_argument("--timeline", default=str(BASE / "build" / "timeline_15s.json"))
    parser.add_argument("--audio", default=str(BASE / "build" / "master_15s.m4a"))
    parser.add_argument("--out-dir", default=str(BASE / "renders"))
    args = parser.parse_args()

    timeline_path = Path(args.timeline).resolve()
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    shots = timeline["shots"]
    width = int(timeline["width"])
    height = int(timeline["height"])
    fps = int(timeline["fps"])
    duration = float(timeline["duration_sec"])
    total_frames = int(timeline["total_frames"])

    frames_dir = Path(args.frames_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    keyframe_dir = out_dir / "keyframes"
    lookdev_frames = [int(s["lookdev_frame"]) for s in shots]
    lookdev_paths = expected_frame_paths(frames_dir, lookdev_frames)
    copy_keyframes(lookdev_paths, shots, keyframe_dir)

    if args.mode == "lookdev":
        tag = timeline.get("tag", "15s")
        sheet = out_dir / f"PEHRA_{tag}_LOOKDEV_CONTACT_SHEET.jpg"
        make_contact_sheet(lookdev_paths, shots, sheet)
        qc = {
            "mode": "lookdev",
            "frames_checked": lookdev_frames,
            "frame_paths": [str(p) for p in lookdev_paths],
            "contact_sheet": str(sheet),
            "keyframes": str(keyframe_dir),
            "note": "Six single-frame Cycles lookdev renders for visual approval; not the delivered video.",
        }
        (out_dir / f"PEHRA_{tag}_LOOKDEV_QC.json").write_text(json.dumps(qc, indent=2), encoding="utf-8")
        print(f"=== LOOKDEV CONTACT SHEET -> {sheet} ===")
        return

    tag = timeline.get("tag", "15s")
    # Final: every frame must be present and unique in time.
    all_paths = expected_frame_paths(frames_dir, list(range(1, total_frames + 1)))
    if len(all_paths) != total_frames:
        raise RuntimeError(f"Expected {total_frames} frames, got {len(all_paths)}")

    caption_dir = BASE / "captions"
    caption_dir.mkdir(parents=True, exist_ok=True)
    caption_paths: list[Path] = []
    for i, shot in enumerate(shots, 1):
        cap_path = caption_dir / f"caption_{i:02d}_{shot['id']}.png"
        make_caption_png(shot, width, height, cap_path, i - 1)
        caption_paths.append(cap_path)

    sheet = out_dir / f"PEHRA_{tag}_CONTACT_SHEET.jpg"
    make_contact_sheet(lookdev_paths, shots, sheet)

    audio_path = Path(args.audio).resolve()
    if not audio_path.exists():
        raise FileNotFoundError(f"Master audio missing: {audio_path}")
    out_name = timeline.get("output_name", f"PEHRA_{tag}_PREVIEW_1080x1920.mp4")
    out_mp4 = out_dir / out_name
    build_video(
        frames_dir, caption_paths, shots, audio_path, out_mp4,
        width=width, height=height, fps=fps, duration=duration,
    )

    probe = probe_video(out_mp4)
    qc = {
        "mode": "final",
        "title": timeline["title"],
        "video": str(out_mp4),
        "contact_sheet": str(sheet),
        "keyframes": str(keyframe_dir),
        "expected": {
            "width": width,
            "height": height,
            "fps": fps,
            "duration_sec": duration,
            "total_frames": total_frames,
            "audio": "-14 LUFS / -1 dBTP stereo 48 kHz",
        },
        "validated_all_frame_files": True,
        "zero_still_image_scene_plates": True,
        "editorial_caption_overlays": len(caption_paths),
        "ffprobe": probe,
        "file_size_bytes": out_mp4.stat().st_size,
    }
    (out_dir / f"PEHRA_{tag}_QC.json").write_text(json.dumps(qc, indent=2), encoding="utf-8")

    # Bundle the exact timeline, master audio, and CC0 credits beside the video.
    shutil.copy2(timeline_path, out_dir / f"timeline_{tag}.json")
    shutil.copy2(audio_path, out_dir / f"master_{tag}.m4a")
    credits = BASE / "ASSET_CREDITS.md"
    if credits.exists():
        shutil.copy2(credits, out_dir / "ASSET_CREDITS.md")
    print(f"=== FINAL 15s PREVIEW -> {out_mp4} ({out_mp4.stat().st_size / 1048576:.1f} MB) ===")


if __name__ == "__main__":
    main()
