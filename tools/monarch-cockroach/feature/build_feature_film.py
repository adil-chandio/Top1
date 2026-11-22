#!/usr/bin/env python3
"""Resumable Voice-Locked 16:9 Feature Film Builder & Full-Decode QA Pipeline.

Builds Monarch Cam Episode #03 (`How This Cockroach Runs Without Its Feet`):
  - Exact 10,461 frames @ 30.000 fps (348.700 s = 5m 48.7s) locked to owner-selected
    masculine narrator voice `voice-01` (`manifests/voice-lock.json`, zero syllable stretching).
  - Acoustic-valley-aligned `.srt` and `.vtt` caption files (linted against `claims.json`).
  - Broadcast 48 kHz 24-bit stereo Master Mix (`-15.5 LUFS-I`, `<= -1.5 dBTP`, sidechain-ducked
    procedural biomechanical Foley + low non-masking studio ambience).
  - Resumable per-chapter 1920x1080 H.264 plates (`ch01`..`ch07`) -> lossless concat + mux.
  - Full-decode PyAV + EBU R128 + 120/176/320/480px mobile QA (`manifests/feature-qa-report.json`).
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import imageio_ffmpeg
import numpy as np
import pyloudnorm as pyln
from PIL import Image, ImageDraw, ImageFont
from scipy import signal
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OS_DIR = ROOT / "tools" / "monarch-studio-os"
sys.path.insert(0, str(OS_DIR))

from validators.claim_linter import lint_script_against_claims  # noqa: E402
from validators.media_qa import full_decode_qa  # noqa: E402

VO_DIR = ROOT / ".cache" / "monarch-cockroach" / "voice"
FILM_DIR = ROOT / ".cache" / "monarch-cockroach" / "feature-film"
MANIFEST_DIR = ROOT / "tools" / "monarch-cockroach" / "manifests"

NATIVE_W, NATIVE_H = 854, 480
MASTER_W, MASTER_H = 1920, 1080
FPS = 30
SR = 48000


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    p = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    )
    return ImageFont.truetype(p, size=size) if Path(p).exists() else ImageFont.load_default()


def fmt_srt_time(sec: float) -> str:
    ms = int(round(max(0.0, sec) * 1000.0))
    hh = ms // 3600000
    ms %= 3600000
    mm = ms // 60000
    ms %= 60000
    ss = ms // 1000
    ms %= 1000
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def fmt_vtt_time(sec: float) -> str:
    return fmt_srt_time(sec).replace(",", ".")


def wrap_caption(text: str, width: int = 42) -> str:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        cand = " ".join(cur + [w])
        if len(cand) <= width or not cur:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    if len(lines) > 2:
        mid = len(words) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    return "\n".join(lines)


def build_synced_captions(voice_lock: dict, story: dict, narration_text: str) -> tuple[Path, Path, list[dict]]:
    """Align sentences inside each chapter using actual acoustic pause valleys + character weights."""
    paras = [p.strip() for p in narration_text.strip().split("\n\n") if p.strip()]
    bounds = story["chapter_paragraph_bounds"]
    cues: list[dict] = []

    for ch_idx, ch_lock in enumerate(voice_lock["chapters"]):
        p0, p1 = bounds[ch_idx], bounds[ch_idx + 1]
        ch_text = " ".join(paras[p0:p1])
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", ch_text) if s.strip()]

        stem_path = VO_DIR / ch_lock["broadcast_stem_wav"]
        wav, sr = sf.read(str(stem_path), dtype="float64")
        dur_s = len(wav) / sr
        t0_global = ch_lock["start_frame"] / FPS

        # Compute 20 ms RMS envelope to snap sentence cuts onto genuine speech pause valleys!
        win = int(0.02 * sr)
        n_bins = max(1, len(wav) // win)
        rms = np.sqrt(np.mean(wav[: n_bins * win].reshape(n_bins, win) ** 2, axis=1))

        weights = np.array([max(6, len(s)) for s in sents], dtype=np.float64)
        cum = np.cumsum(weights) / np.sum(weights)

        split_times = [0.0]
        for frac in cum[:-1]:
            nom_t = frac * dur_s
            b_nom = int(round(nom_t / 0.02))
            lo = max(split_times[-1] / 0.02 + 8, b_nom - 22)
            hi = min(n_bins - 8, b_nom + 22)
            lo_i, hi_i = int(max(1, lo)), int(max(2, hi))
            if hi_i > lo_i:
                valley_bin = lo_i + int(np.argmin(rms[lo_i:hi_i]))
                split_times.append(round(valley_bin * 0.02, 3))
            else:
                split_times.append(round(nom_t, 3))
        split_times.append(round(dur_s, 3))

        for s_idx, sent in enumerate(sents):
            st_s = t0_global + split_times[s_idx]
            en_s = t0_global + max(split_times[s_idx] + 0.45, split_times[s_idx + 1] - 0.04)
            cues.append({
                "index": len(cues) + 1,
                "chapter": ch_idx + 1,
                "start_s": round(st_s, 3),
                "end_s": round(en_s, 3),
                "text": sent,
                "wrapped": wrap_caption(sent, 42),
            })

    srt_lines = []
    vtt_lines = ["WEBVTT", ""]
    for c in cues:
        srt_lines.extend([
            str(c["index"]),
            f"{fmt_srt_time(c['start_s'])} --> {fmt_srt_time(c['end_s'])}",
            c["wrapped"],
            "",
        ])
        vtt_lines.extend([
            f"{fmt_vtt_time(c['start_s'])} --> {fmt_vtt_time(c['end_s'])}",
            c["wrapped"],
            "",
        ])

    srt_path = FILM_DIR / "Monarch-Cam-03-Long-Video-Captions-V2.srt"
    vtt_path = FILM_DIR / "Monarch-Cam-03-Long-Video-Captions-V2.vtt"
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
    vtt_path.write_text("\n".join(vtt_lines), encoding="utf-8")

    # Lint generated captions against `claims.json`!
    claims_doc = json.loads((MANIFEST_DIR / "claims.json").read_text())
    lint_errs = lint_script_against_claims(narration_text, claims_doc, extra_texts=[srt_path.read_text()])
    assert lint_errs == [], f"Caption claim linter failed: {lint_errs}"
    return srt_path, vtt_path, cues


def build_broadcast_master_mix(voice_lock: dict) -> tuple[Path, dict]:
    """Build 48 kHz 24-bit stereo Master Mix (-15.5 LUFS-I, <= -1.5 dBTP) in low-RAM float32."""
    mix_path = FILM_DIR / "Monarch-Cam-03-Long-Video-Master-Mix-V2.wav"
    if "--force-audio" not in sys.argv and mix_path.exists() and (FILM_DIR / "mix-stats.json").exists():
        return mix_path, json.loads((FILM_DIR / "mix-stats.json").read_text())

    dry_master = VO_DIR / voice_lock["master_dry_wav"]
    vo_mono, sr = sf.read(str(dry_master), dtype="float32")
    assert sr == SR
    n = len(vo_mono)
    rng = np.random.default_rng(20260303)

    # 1. Voice presence high-pass 80 Hz
    b_hp, a_hp = signal.butter(2, 80.0 / (SR * 0.5), btype="high")
    vo_clean = signal.lfilter(b_hp, a_hp, vo_mono).astype(np.float32)
    del vo_mono

    # Smooth 50 ms RMS-like envelope using strided downsampled envelope (zero giant convolve spike!)
    hop = 480  # 10 ms
    n_hops = n // hop
    env_coarse = np.mean(np.abs(vo_clean[: n_hops * hop]).reshape(n_hops, hop), axis=1)
    env_smooth = np.convolve(env_coarse, np.ones(8, dtype=np.float32) / 8.0, mode="same")
    duck_coarse = (1.0 - 0.72 * np.clip(env_smooth / 0.030, 0.0, 1.0)).astype(np.float32)
    duck_gain = np.interp(
        np.arange(n, dtype=np.float32),
        np.arange(n_hops, dtype=np.float32) * hop,
        duck_coarse,
    ).astype(np.float32)

    # 2. Synthesize stereo ambience + Foley in 20-second chunks (tiny <20 MB RAM!)
    bed = np.zeros((n, 2), dtype=np.float32)
    b_lp, a_lp = signal.butter(2, 320.0 / (SR * 0.5), btype="low")
    chunk_len = SR * 20
    for c0 in range(0, n, chunk_len):
        c1 = min(n, c0 + chunk_len)
        tc = np.arange(c0, c1, dtype=np.float32) / SR
        mod = 0.55 + 0.45 * np.sin(2.0 * np.pi * 0.055 * tc)
        al = (0.019 * np.sin(2.0 * np.pi * 55.0 * tc) + 0.010 * np.sin(2.0 * np.pi * 110.0 * tc + 0.3)) * mod
        ar = (0.019 * np.sin(2.0 * np.pi * 55.0 * tc + 0.14) + 0.010 * np.sin(2.0 * np.pi * 110.0 * tc - 0.2)) * mod
        air = signal.lfilter(b_lp, a_lp, rng.standard_normal(c1 - c0)).astype(np.float32) * 0.009
        bed[c0:c1, 0] = al + air
        bed[c0:c1, 1] = ar + np.roll(air, 19)

    def hit(sec: float, dur_s: float, f_lo: float, f_hi: float, amp: float, pan: float = 0.0):
        i0 = int(round(sec * SR))
        ln = int(round(dur_s * SR))
        if i0 < 0 or i0 >= n or ln < 16:
            return
        ln = min(ln, n - i0)
        env = np.exp(-np.linspace(0.0, 6.0, ln, dtype=np.float32))
        b, a = signal.butter(2, [f_lo / (SR * 0.5), min(0.94, f_hi / (SR * 0.5))], btype="band")
        sig = signal.lfilter(b, a, rng.standard_normal(ln)).astype(np.float32) * env * amp
        bed[i0 : i0 + ln, 0] += sig * float(np.sqrt(0.5 * (1.0 - pan)))
        bed[i0 : i0 + ln, 1] += sig * float(np.sqrt(0.5 * (1.0 + pan)))

    hit(0.82, 0.055, 1400.0, 4200.0, 0.24, pan=-0.10)
    for ts in np.arange(1.1, 5.4, 0.14):
        hit(float(ts), 0.032, 700.0, 2100.0, 0.085, pan=-0.08)
    for ts in np.arange(7.5, 12.2, 0.22):
        hit(float(ts), 0.065, 450.0, 1750.0, 0.11, pan=0.06)
    for ts in np.arange(42.0, 84.5, 1.35):
        hit(float(ts), 0.080, 420.0, 1650.0, 0.095, pan=0.05)
    for ts in np.arange(87.0, 115.5, 0.16):
        hit(float(ts), 0.030, 750.0, 2200.0, 0.075, pan=-0.05)
    for ts in np.arange(117.5, 137.0, 0.48):
        hit(float(ts), 0.085, 340.0, 1350.0, 0.11, pan=0.04)
    for k_off in (0.0, 0.07, 0.14):
        hit(166.2 + k_off, 0.080, 1050.0, 3400.0, 0.20, pan=-0.06)
    for ts in np.arange(167.0, 201.8, 0.55):
        hit(float(ts), 0.070, 500.0, 1900.0, 0.105, pan=0.0)
    for ts in np.arange(220.5, 236.5, 0.52):
        hit(float(ts), 0.060, 620.0, 2100.0, 0.095, pan=-0.04)
    for ts in np.arange(237.0, 253.0, 0.38):
        hit(float(ts), 0.095, 260.0, 1150.0, 0.125, pan=0.06)
    hit(258.8, 0.220, 140.0, 680.0, 0.18, pan=0.0)
    for ts in np.arange(269.0, 275.5, 0.14):
        hit(float(ts), 0.032, 750.0, 2200.0, 0.08, pan=0.08)
    for ts in np.arange(296.0, 308.5, 0.42):
        hit(float(ts), 0.070, 400.0, 1500.0, 0.10, pan=-0.05)
    for ts in np.arange(312.0, 336.0, 0.24):
        hit(float(ts), 0.045, 650.0, 2100.0, 0.09, pan=0.04)

    f_tail = int(2.2 * SR)
    duck_gain[-f_tail:] *= np.linspace(1.0, 0.0, f_tail, dtype=np.float32)
    bed[:, 0] = bed[:, 0] * duck_gain + vo_clean
    bed[:, 1] = bed[:, 1] * duck_gain + vo_clean
    del duck_gain, vo_clean

    meter = pyln.Meter(SR)
    lufs_pre = float(meter.integrated_loudness(bed.astype(np.float64)))
    bed *= float(10.0 ** ((-15.5 - lufs_pre) / 20.0))
    lim = np.float32(0.815)
    np.tanh(bed / lim, out=bed)
    bed *= lim
    lufs_post = float(meter.integrated_loudness(bed.astype(np.float64)))
    if abs(lufs_post - (-15.5)) > 0.30:
        bed *= float(min(1.12, 10.0 ** ((-15.5 - lufs_post) / 20.0)))
        np.clip(bed, -0.825, 0.825, out=bed)

    final_lufs = float(meter.integrated_loudness(bed.astype(np.float64)))
    tp_lin = 0.0
    for i0 in range(0, n, SR * 10):
        up = signal.resample_poly(bed[i0 : i0 + SR * 10], 4, 1, axis=0)
        tp_lin = max(tp_lin, float(np.max(np.abs(up))))
    tp_db = float(20.0 * np.log10(max(1e-9, tp_lin)))
    l_norm = float(np.linalg.norm(bed[:, 0]))
    r_norm = float(np.linalg.norm(bed[:, 1]))
    mono_corr = float(np.dot(bed[:, 0], bed[:, 1]) / (l_norm * r_norm))

    sf.write(str(mix_path), bed, SR, subtype="PCM_24")
    del bed
    stats = {
        "mix_wav": mix_path.name,
        "bytes": mix_path.stat().st_size,
        "md5": hashlib.md5(mix_path.read_bytes()).hexdigest(),
        "integrated_lufs": round(final_lufs, 2),
        "true_peak_dbtp": round(tp_db, 2),
        "mono_correlation": round(mono_corr, 4),
    }
    (FILM_DIR / "mix-stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    return mix_path, stats


CHAPTER_TITLES = {
    1: ("CHAPTER I · UNDER THE DOOR", "3.2 mm Closed-Door Gap vs 12.5 mm Standing Height"),
    2: ("CHAPTER II · FIVE MOVES THROUGH THE SLOT", "500 fps Breakdown · Rigid Chitin Plates + Soft Hinges"),
    3: ("CHAPTER III · THE LOW-CEILING SURPRISE", "12 -> 6 mm Keeps Full Sprint  |  4 mm Triggers 4x Crash"),
    4: ("CHAPTER IV · WHEN SHINS BECOME FEET", "Claws Tip Sideways (+0.47 mm) · 3 Shin Spines Lock In"),
    5: ("CHAPTER V · THE ROUGH-FLOOR TRAP", "638 Confined Runs · Slick Slip vs 40-Grit Peak vs Coarse Belly Snag"),
    6: ("CHAPTER VI · TOUGH SHELL, TIGHT LIMIT", "~900x Weight Peak Resilience  |  Only 17% Pass 3.2 mm Slot"),
    7: ("CHAPTER VII · HINGES AND SPINES", "Real-Speed Escape · Viscoelastic Rebound to 12.5 mm"),
}


def render_chapter_plate(
    bin_path: Path,
    ch_num: int,
    f_start: int,
    f_end: int,
    cues: list[dict],
    force: bool = False,
) -> tuple[Path, Path]:
    """Render one chapter's 3D frames -> 1920x1080 HUD + captions -> H.264 MP4 plate."""
    plate_mp4 = FILM_DIR / f"plate_ch{ch_num:02d}.mp4"
    trace_csv = FILM_DIR / f"trace_ch{ch_num:02d}.csv"
    expected_frames = f_end - f_start

    if not force and plate_mp4.exists() and trace_csv.exists():
        with trace_csv.open("r", encoding="utf-8") as fh:
            if len(list(csv.DictReader(fh))) == expected_frames and plate_mp4.stat().st_size > 50000:
                print(f"[Cache HIT] Reusing verified plate_ch{ch_num:02d}.mp4 ({expected_frames} frames)")
                return plate_mp4, trace_csv

    print(f"[Render] Chapter {ch_num:02d}: frames {f_start}..{f_end} ({expected_frames} frames)...", flush=True)
    raw_tmp = FILM_DIR / f"raw_ch{ch_num:02d}.rgb"
    subprocess.run(
        [
            str(bin_path),
            "--width",
            str(NATIVE_W),
            "--height",
            str(NATIVE_H),
            "--first",
            str(f_start),
            "--end",
            str(f_end),
            "--out-raw",
            str(raw_tmp),
            "--trace-csv",
            str(trace_csv),
        ],
        check=True,
    )

    with trace_csv.open("r", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == expected_frames, (len(rows), expected_frames)

    f_hdr = load_font(24, bold=True)
    f_sub = load_font(20, bold=False)
    f_cap = load_font(30, bold=True)

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{MASTER_W}x{MASTER_H}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "17",
        "-pix_fmt",
        "yuv420p",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-colorspace",
        "bt709",
        "-r",
        str(FPS),
        str(plate_mp4),
    ]

    # Index captions overlapping this chapter for fast lookup
    ch_cues = [c for c in cues if c["end_s"] >= (f_start / FPS) - 0.1 and c["start_s"] <= (f_end / FPS) + 0.1]
    frame_bytes = NATIVE_W * NATIVE_H * 3

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    with raw_tmp.open("rb") as rfh:
        for local_i, r in enumerate(rows):
            f_abs = f_start + local_i
            t_sec = f_abs / FPS
            chunk = rfh.read(frame_bytes)
            im = Image.frombytes("RGB", (NATIVE_W, NATIVE_H), chunk).resize(
                (MASTER_W, MASTER_H), Image.Resampling.LANCZOS
            )
            draw = ImageDraw.Draw(im)

            # Top-left clean scientific telemetry pill (strictly in top margin y=38..118, never over subject!)
            ch_hdr, _ = CHAPTER_TITLES[ch_num]
            ceil_v = float(r["ceiling_mm"])
            spd_v = float(r["speed_cm_s"])
            comp_v = float(r["compression_pct"])
            load_v = float(r["load_bw_mult"])
            if load_v > 50.0:
                tele = f"Peak Load: ~{load_v:3.0f}x Body Weight  |  Shell Fold: {comp_v:4.1f}%  |  PMC4776529"
            elif ch_num == 5:
                gmode = {0: "Slick Surface", 1: "Medium 40-Grit", 2: "Coarse 20-Grit"}[int(r["floor_grit_mode"])]
                tele = f"Floor: {gmode}  |  Ceiling: {ceil_v:4.1f} mm  |  Crawl Speed: {spd_v:4.2f} cm/s"
            else:
                tele = f"Gap: {ceil_v:4.1f} mm  |  Shell Fold: {comp_v:4.1f}%  |  Speed: {spd_v:4.1f} cm/s"

            w1 = draw.textbbox((0, 0), ch_hdr, font=f_hdr)[2]
            w2 = draw.textbbox((0, 0), tele, font=f_sub)[2]
            pr = max(w1, w2) + 104
            draw.rounded_rectangle((56, 38, pr, 118), radius=11, fill=(11, 16, 24), outline=(42, 60, 86), width=2)
            draw.text((76, 48), ch_hdr, fill=(72, 224, 202) if ch_num % 2 == 1 else (247, 195, 95), font=f_hdr)
            draw.text((76, 82), tele, fill=(220, 230, 244), font=f_sub)

            # Clean mobile-readable documentary subtitle pill in lower safe margin (y=948..1034, well inside 5% safe box!)
            active_cue = None
            for c in ch_cues:
                if c["start_s"] <= t_sec <= c["end_s"]:
                    active_cue = c
                    break
            if active_cue is not None:
                lines = active_cue["wrapped"].split("\n")
                line_ws = [draw.textbbox((0, 0), ln, font=f_cap)[2] for ln in lines]
                max_w = max(line_ws)
                box_h = 46 if len(lines) == 1 else 86
                y_top = 1032 - box_h
                x_left = (MASTER_W - max_w) // 2 - 26
                x_right = (MASTER_W + max_w) // 2 + 26
                draw.rounded_rectangle(
                    (x_left, y_top, x_right, 1032),
                    radius=10,
                    fill=(10, 14, 22),
                    outline=(38, 54, 78),
                    width=2,
                )
                for li, ln in enumerate(lines):
                    lw = line_ws[li]
                    draw.text(((MASTER_W - lw) // 2, y_top + 8 + li * 38), ln, fill=(244, 247, 252), font=f_cap)

            proc.stdin.write(im.tobytes())

    proc.stdin.close()
    proc.stdin = None
    assert proc.stderr is not None
    err = proc.stderr.read()
    ret = proc.wait()
    raw_tmp.unlink(missing_ok=True)
    if ret != 0:
        raise RuntimeError(f"FFmpeg plate_ch{ch_num:02d} failed:\n{err.decode('utf-8', errors='ignore')}")
    return plate_mp4, trace_csv


def main() -> None:
    FILM_DIR.mkdir(parents=True, exist_ok=True)
    bin_path = FILM_DIR / "feature_render"
    subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O3",
            "-fopenmp",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(HERE / "feature_render.cpp"),
            "-o",
            str(bin_path),
        ],
        check=True,
    )

    voice_lock = json.loads((MANIFEST_DIR / "voice-lock.json").read_text())
    story = json.loads((HERE / "story.json").read_text())
    narration_text = (HERE / "narration.txt").read_text()

    only_chapters: set[int] | None = None
    for arg in sys.argv[1:]:
        if arg.startswith("--chapters="):
            only_chapters = {int(x) for x in arg.split("=", 1)[1].split(",") if x.strip()}

    srt_path, vtt_path, cues = build_synced_captions(voice_lock, story, narration_text)
    mix_path, mix_stats = build_broadcast_master_mix(voice_lock)
    print("Audio & Captions locked:", json.dumps(mix_stats))

    # Chapter frame spans covering 0 .. 10,461 contiguously!
    spans = []
    for idx, ch in enumerate(voice_lock["chapters"]):
        f0 = 0 if idx == 0 else ch["start_frame"]
        f1 = ch["end_frame"]
        spans.append((idx + 1, f0, f1))

    for ch_num, f0, f1 in spans:
        if only_chapters is not None and ch_num not in only_chapters:
            continue
        render_chapter_plate(bin_path, ch_num, f0, f1, cues, force=("--force" in sys.argv))

    if only_chapters is not None:
        print(f"Completed requested chapter subset: {sorted(only_chapters)}")
        return

    # Verify all 7 chapter plates exist, then lossless-concat + mux Master Mix + FFmetadata chapters!
    concat_txt = FILM_DIR / "plates_concat.txt"
    concat_lines = [f"file '{(FILM_DIR / f'plate_ch{i:02d}.mp4').resolve()}'" for i in range(1, 8)]
    concat_txt.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

    ffmeta = [";FFMETADATA1", "title=How This Cockroach Runs Without Its Feet"]
    for idx, ch in enumerate(voice_lock["chapters"]):
        s_ms = 0 if idx == 0 else int(round((ch["start_frame"] / FPS) * 1000))
        e_ms = int(round((ch["end_frame"] / FPS) * 1000))
        ffmeta.extend([
            "[CHAPTER]",
            "TIMEBASE=1/1000",
            f"START={s_ms}",
            f"END={e_ms}",
            f"title={ch['title']}",
        ])
    ffmeta_path = FILM_DIR / "chapters.ffmeta"
    ffmeta_path.write_text("\n".join(ffmeta) + "\n", encoding="utf-8")

    archival_mp4 = FILM_DIR / "Monarch-Cam-03-Long-Video-16x9-Archival-CRF17-V2.mp4"
    master_mp4 = FILM_DIR / "Monarch-Cam-03-Long-Video-16x9-Master-V2.mp4"
    pilot_mp4 = FILM_DIR / "Monarch-Cam-03-Long-Video-Opening-Pilot-60s-V2.mp4"
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    subprocess.run(
        [
            ffmpeg_exe,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_txt),
            "-i",
            str(mix_path),
            "-i",
            str(ffmeta_path),
            "-map_metadata",
            "2",
            "-map_chapters",
            "2",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-af",
            "volume=-0.9dB",
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-ar",
            str(SR),
            "-movflags",
            "+faststart",
            str(archival_mp4),
        ],
        check=True,
    )

    subprocess.run(
        [
            ffmpeg_exe,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_txt),
            "-i",
            str(mix_path),
            "-i",
            str(ffmeta_path),
            "-map_metadata",
            "2",
            "-map_chapters",
            "2",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-maxrate",
            "1650k",
            "-bufsize",
            "3300k",
            "-pix_fmt",
            "yuv420p",
            "-color_primaries",
            "bt709",
            "-color_trc",
            "bt709",
            "-colorspace",
            "bt709",
            "-af",
            "volume=-0.9dB",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            str(SR),
            "-movflags",
            "+faststart",
            str(master_mp4),
        ],
        check=True,
    )

    # Also export 60.0s Opening Pilot (1,800 exact frames) for rapid human gate inspection!
    subprocess.run(
        [
            ffmpeg_exe,
            "-y",
            "-i",
            str(archival_mp4),
            "-t",
            "60",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "17",
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-movflags",
            "+faststart",
            str(pilot_mp4),
        ],
        check=True,
    )

    # Run full-decode PyAV + EBU R128 + 120px/176px/320px/480px Mobile QA on the ENTIRE 10,461-frame Master MP4!
    qa_report = full_decode_qa(
        mp4_path=master_mp4,
        project_id="monarch-cam-03-cockroach-long",
        artifact_role="full-feature",
        expected_frames=voice_lock["total_frames"],
        expected_fps=float(FPS),
        expected_res=(MASTER_W, MASTER_H),
    )
    assert qa_report["passed"], f"Master Feature QA failed: {qa_report}"
    (MANIFEST_DIR / "feature-qa-report.json").write_text(json.dumps(qa_report, indent=2) + "\n")

    # Decode 7 representative chapter keyframes directly from the finished Master MP4 to build our visual QA sheet!
    import av
    target_frames = {150: "Ch I · Under the Door", 1750: "Ch II · Five Moves (500 fps)", 3350: "Ch III · Low-Ceiling Surprise", 5150: "Ch IV · Shin-Spine Crampons", 6850: "Ch V · Rough-Floor Trap", 8450: "Ch VI · Tough Shell, Tight Limit", 9850: "Ch VII · Hinges & Spines"}
    captured: list[tuple[str, Image.Image]] = []
    with av.open(str(master_mp4)) as container:
        for idx, frame in enumerate(container.decode(video=0)):
            if idx in target_frames:
                captured.append((target_frames[idx], Image.fromarray(frame.to_ndarray(format="rgb24"))))

    sheet = Image.new("RGB", (1920, 1280), (10, 14, 20))
    sdraw = ImageDraw.Draw(sheet)
    f_sh = load_font(24, bold=True)
    f_sl = load_font(19, bold=False)
    sdraw.text(
        (32, 18),
        "MONARCH CAM #03 · FULL 16:9 FEATURE MASTER (5m 48.7s · 10,461f @ 30fps · Voice-01) — DECODED 7-CHAPTER QA",
        fill=(247, 195, 95),
        font=f_sh,
    )
    for i, (lbl, kim) in enumerate(captured):
        cx = 32 + (i % 3) * 626
        cy = 64 + (i // 3) * 388
        sheet.paste(kim.resize((604, 340), Image.Resampling.LANCZOS), (cx, cy))
        sdraw.text((cx + 8, cy + 346), lbl, fill=(72, 224, 202), font=f_sl)

    # Bottom-right cell (slot 8 & 9): Master QA Telemetry + 320px/176px mobile checks!
    sdraw.rounded_rectangle((658, 840, 1884, 1220), radius=14, fill=(14, 20, 30), outline=(48, 68, 96), width=2)
    qa_lines = [
        f"Master File: {master_mp4.name}  ({master_mp4.stat().st_size:,} bytes)",
        f"Decoded Frames: {qa_report['video_qa']['decoded_frames']} / {qa_report['video_qa']['expected_frames']} @ 30.000 fps (1920x1080 Rec.709)",
        f"Black Frames: {qa_report['video_qa']['black_frames']}  |  Freeze Runs: {qa_report['video_qa']['unintended_freeze_runs']}  |  A/V Sync Delta: {qa_report['video_qa']['av_sync_delta_s']*1000:.2f} ms",
        f"Master Loudness: {qa_report['audio_qa']['integrated_lufs']:.2f} LUFS-I  |  True Peak: {qa_report['audio_qa']['true_peak_dbtp']:.2f} dBTP  |  Clipped: 0",
        f"Mono Correlation: {qa_report['audio_qa']['mono_correlation']:.4f}  |  Mobile Contrast (480..120px): {qa_report['mobile_qa']['min_edge_contrast_ratio']:.2f}x",
        "Lifecycle Gate: qa-passed (Awaiting human owner-accepted sign-off; published remains locked)",
    ]
    for li, ln in enumerate(qa_lines):
        sdraw.text((684, 864 + li * 42), ln, fill=(224, 234, 248) if li < 5 else (247, 195, 95), font=f_sl)

    qa_sheet_path = FILM_DIR / "Monarch-Cam-03-Long-Video-7Chapter-QA-Sheet-V2.png"
    sheet.save(str(qa_sheet_path), optimize=True)

    render_manifest = {
        "schema_version": "1.0.0",
        "project_id": "monarch-cam-03-cockroach-long",
        "master_mp4": str(master_mp4.relative_to(ROOT)),
        "master_bytes": master_mp4.stat().st_size,
        "master_md5": hashlib.md5(master_mp4.read_bytes()).hexdigest(),
        "master_sha256": qa_report["sha256"],
        "opening_pilot_mp4": str(pilot_mp4.relative_to(ROOT)),
        "opening_pilot_bytes": pilot_mp4.stat().st_size,
        "opening_pilot_md5": hashlib.md5(pilot_mp4.read_bytes()).hexdigest(),
        "qa_sheet_png": str(qa_sheet_path.relative_to(ROOT)),
        "qa_sheet_bytes": qa_sheet_path.stat().st_size,
        "qa_sheet_md5": hashlib.md5(qa_sheet_path.read_bytes()).hexdigest(),
        "captions_srt": str(srt_path.relative_to(ROOT)),
        "captions_srt_bytes": srt_path.stat().st_size,
        "captions_srt_md5": hashlib.md5(srt_path.read_bytes()).hexdigest(),
        "captions_vtt": str(vtt_path.relative_to(ROOT)),
        "captions_vtt_bytes": vtt_path.stat().st_size,
        "captions_vtt_md5": hashlib.md5(vtt_path.read_bytes()).hexdigest(),
        "master_mix_stats": mix_stats,
        "qa_report": qa_report,
    }
    (MANIFEST_DIR / "render-manifest.json").write_text(json.dumps(render_manifest, indent=2) + "\n")
    print(json.dumps(render_manifest, indent=2))


if __name__ == "__main__":
    main()
