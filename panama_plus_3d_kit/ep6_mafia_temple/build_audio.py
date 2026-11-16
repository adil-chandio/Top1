#!/usr/bin/env python3
"""
MONARCH® PANAMA-PLUS EP6 — MAFIA TEMPLE 3D (20.0s, 24fps, 1920x1080)
Uses real CC0/Repo audio assets per production/mafia-temple/audio/SOURCES.md:
- powerbassist/World-simulator searching.ogg (dark ambient score)
- evanlin23/blocky-stories stone_01..04.wav (frame-locked heel-strike footsteps)
- evanlin23/blocky-stories rain.wav + wind.wav (nocturnal shrine atmosphere)
- Leonxlnx/earshot sub_drop/punch.wav + riser/dark.wav + cut_hit/punch.wav
- Deep bronze Tibetan temple bowl resonance on exact 6-shot cut frames (96, 216, 312, 384, 432)
Mastered to -14.0 LUFS / -1.5 dBTP.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy import signal

KIT_DIR = Path(__file__).resolve().parent
OUT_DIR = KIT_DIR / "out"
ASSETS_DIR = KIT_DIR / "assets"
EARSHOT_DIR = ASSETS_DIR / "earshot_takes"
SR = 48000
FPS = 24
DUR = 20.0
TOTAL_FRAMES = 480
N_TOTAL = int(DUR * SR)


def decode_audio_48k(src: Path, mono: bool = True) -> np.ndarray | None:
    if not src.exists():
        return None
    tmp = OUT_DIR / f"_tmp_{src.stem}.wav"
    ch = "1" if mono else "2"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-ac", ch, "-ar", str(SR), "-sample_fmt", "s16", str(tmp)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    with wave.open(str(tmp), "rb") as wf:
        arr = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    tmp.unlink(missing_ok=True)
    if not mono:
        arr = arr.reshape(-1, 2)
    return arr


def loop_to_len(arr: np.ndarray, target_n: int) -> np.ndarray:
    if len(arr) == 0:
        return np.zeros(target_n, dtype=np.float64)
    reps = math.ceil(target_n / len(arr))
    return np.tile(arr, reps)[:target_n] if arr.ndim == 1 else np.tile(arr, (reps, 1))[:target_n]


def synth_temple_bowl(dur_s: float = 3.2, f0: float = 112.0) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    partials = [(1.0, 1.0, 1.4), (2.756, 0.35, 2.2), (5.404, 0.14, 3.8)]
    sig = np.zeros(n)
    for ratio, amp, decay in partials:
        sig += amp * np.sin(2 * np.pi * (f0 * ratio) * t) * np.exp(-t * decay)
    return sig / (np.max(np.abs(sig)) + 1e-9)


def synth_rain_fallback(dur_s: float) -> np.ndarray:
    rng = np.random.default_rng(108)
    w = rng.standard_normal(int(dur_s * SR))
    sos = signal.butter(2, [450 / (SR * 0.5), 4200 / (SR * 0.5)], btype="bandpass", output="sos")
    y = signal.sosfilt(sos, w)
    return y / (np.max(np.abs(y)) + 1e-9)


def place_mono(L: np.ndarray, R: np.ndarray, clip: np.ndarray, t_sec: float, gain: float, pan: float = 0.0) -> None:
    s = int(round(t_sec * SR))
    e = min(N_TOTAL, s + len(clip))
    if e <= s:
        return
    lg = math.sqrt(0.5 * (1.0 - pan))
    rg = math.sqrt(0.5 * (1.0 + pan))
    seg = clip[: e - s] * gain
    L[s:e] += seg * lg
    R[s:e] += seg * rg


def measure_lufs(wav_path: Path) -> tuple[float, float]:
    res = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(wav_path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    summ = res.stderr.split("Summary:")[-1]
    lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))
    return lufs, tp


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    L = np.zeros(N_TOTAL, dtype=np.float64)
    R = np.zeros(N_TOTAL, dtype=np.float64)

    # 1. Music score: searching.ogg
    music = decode_audio_48k(ASSETS_DIR / "searching.ogg", mono=False)
    if music is not None:
        m = loop_to_len(music, N_TOTAL)
        L += m[:, 0] * 0.42
        R += m[:, 1] * 0.42
    else:
        t = np.arange(N_TOTAL) / SR
        drone = np.sin(2 * np.pi * 55 * t) * 0.32 + np.sin(2 * np.pi * 82.5 * t) * 0.16
        L += drone
        R += drone

    # 2. Night rain & wind atmosphere
    rain = decode_audio_48k(ASSETS_DIR / "rain.wav", mono=True)
    wind = decode_audio_48k(ASSETS_DIR / "wind.wav", mono=True)
    rain_bed = loop_to_len(rain, N_TOTAL) if rain is not None else synth_rain_fallback(DUR)
    wind_bed = loop_to_len(wind, N_TOTAL) if wind is not None else synth_rain_fallback(DUR) * 0.5
    L += rain_bed * 0.14 + wind_bed * 0.12
    R += rain_bed * 0.14 + wind_bed * 0.12

    # 3. Real CC0 Stone Footsteps synced to visible walks/runs:
    # Shot 1 (0..4s): steady deliberate walk every 0.58s
    # Shot 3 (9..13s): courtyard walk every 0.55s
    # Shot 4 (13..16s): fast lateral run every 0.34s
    steps = [decode_audio_48k(ASSETS_DIR / f"stone_0{i}.wav", mono=True) for i in range(1, 5)]
    steps = [s for s in steps if s is not None]
    if steps:
        step_times = [0.40, 0.98, 1.56, 2.14, 2.72, 3.30, 9.25, 9.80, 10.35, 10.90, 11.45, 12.00, 12.55,
                      13.20, 13.54, 13.88, 14.22, 14.56, 14.90, 15.24, 15.58]
        for idx, st in enumerate(step_times):
            clip = steps[idx % len(steps)]
            pan = -0.18 if idx % 2 == 0 else 0.18
            gain = 0.52 if st >= 13.0 else 0.36
            place_mono(L, R, clip, st, gain, pan=pan)

    # 4. Earshot Sub Drops, Dark Risers & Temple Bowls locked to the 6 cuts (frames 96, 216, 312, 384, 432)
    sub_drop = decode_audio_48k(EARSHOT_DIR / "sub_drop" / "punch.wav", mono=True)
    riser = decode_audio_48k(EARSHOT_DIR / "riser" / "dark.wav", mono=True)
    cut_hit = decode_audio_48k(EARSHOT_DIR / "cut_hit" / "punch.wav", mono=True)
    bowl_deep = synth_temple_bowl(3.6, 110.0)
    bowl_high = synth_temple_bowl(2.8, 164.8)

    place_mono(L, R, bowl_deep, 0.05, 0.55, 0.0)
    for cut_frame in (96, 216, 312, 384, 432):
        ct = cut_frame / FPS
        if sub_drop is not None:
            place_mono(L, R, sub_drop, ct, 0.72, 0.0)
        if cut_hit is not None:
            place_mono(L, R, cut_hit, ct, 0.44, 0.0)
        place_mono(L, R, bowl_high if cut_frame in (216, 432) else bowl_deep, ct + 0.04, 0.45, 0.0)

    if riser is not None:
        place_mono(L, R, riser, 16.6, 0.58, 0.0)
        place_mono(L, R, riser, 18.0 - 0.8, 0.72, 0.0)

    stereo = np.stack([L, R], axis=1)
    # Clean fade-in / tail fade
    fi = int(0.25 * SR)
    fo = int(0.45 * SR)
    stereo[:fi] *= np.linspace(0, 1, fi)[:, None]
    stereo[-fo:] *= np.linspace(1, 0, fo)[:, None]
    peak = np.max(np.abs(stereo)) + 1e-9
    if peak > 0.90:
        stereo *= 0.90 / peak

    raw_wav = OUT_DIR / "audio_raw.wav"
    master_wav = OUT_DIR / "audio_master.wav"
    data = (np.clip(stereo, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(str(raw_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(data.tobytes())

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(raw_wav),
            "-af", "highpass=f=28,lowshelf=g=2.0:f=80,loudnorm=I=-14.0:TP=-1.5:LRA=8,aresample=48000,alimiter=limit=0.84:level=false",
            "-ar", "48000", "-ac", "2", "-sample_fmt", "s16",
            str(master_wav),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    lufs, tp = measure_lufs(master_wav)
    print(f"Master EP6 Mafia Temple Audio: {DUR:.2f}s ({TOTAL_FRAMES} frames @ {FPS}fps) | I={lufs:.1f} LUFS | TP={tp:.1f} dBTP")

    timeline = {
        "title": "MONARCH Mafia Temple 3D — 20s Cut",
        "fps": FPS,
        "duration_sec": DUR,
        "total_frames": TOTAL_FRAMES,
        "audio_lufs": lufs,
        "audio_tp_db": tp,
        "cuts": [0, 96, 216, 312, 384, 432, 480],
    }
    (OUT_DIR / "timeline_synced.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
