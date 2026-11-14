#!/usr/bin/env python3
"""
MONARCH® PANAMA-PLUS EP5 — MAIN ABHI BHI APNI TARAF HOON (40s 3D MOTIVATION)
Locks directly to the verified 40.000s Roman Urdu narration (`narration-urdu.mp3`),
builds a warm sidechain-ducked cinematic chord bed + frame-locked Leonxlnx/earshot
SFX (block slams at f279/f314/f363, stair unfold f546, 5 ascending tread chimes
f662..f712, notebook open f675, phone screen-down f844, pen f933, string release f963,
foot settles f1050/f1060), mastered to -14.0 LUFS / -1.5 dBTP.
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
EARSHOT_DIR = KIT_DIR / "assets" / "earshot_takes"
NARR_MP3 = KIT_DIR / "narration-urdu.mp3"
SR = 48000
FPS = 30
DUR = 40.0
TOTAL_FRAMES = int(DUR * FPS)
N_TOTAL = int(DUR * SR)

BEATS = [
    {"start": 0.00, "end": 8.90, "tag": "KHWAAB", "caption": "Sabse khaufnaak cheez haarna nahi. Khaufnaak woh din hai jab tum apne hi khwaab ko chhota sa khwaab keh kar us se nazar chura lete ho."},
    {"start": 9.30, "end": 13.20, "tag": "BAHAANAY", "caption": "Pehle kehte ho, kal se. Phir kehte ho, mere bas ka nahi. Phir us khwaab ka zikr hi band."},
    {"start": 13.28, "end": 17.90, "tag": "SUKOON YA RUKAWAT", "caption": "Aur duniya samajhti hai, tum theek ho. Haan, thakay ho to aaram karo."},
    {"start": 17.90, "end": 23.53, "tag": "PEHLA QADAM", "caption": "Magar apne khwaab ko dafan karke uska naam sukoon mat rakhna."},
    {"start": 23.53, "end": 27.76, "tag": "EK WAADA", "caption": "Aaj poori zindagi nahi badalni. Bas ek waada nibhana hai."},
    {"start": 27.76, "end": 31.10, "tag": "10 MINUTE", "caption": "Phone side par rakho, woh kaam kholo, das minute usay do."},
    {"start": 31.10, "end": 37.50, "tag": "APNI TARAF", "caption": "Kisi ko prove karne ke liye nahi. Khud ko yaad dilane ke liye: main abhi bhi apni taraf hoon."},
    {"start": 37.50, "end": 40.00, "tag": "AAJ KA WAADA", "caption": "Aaj ka waada kya hai?"},
]

FRAME_CUES = [
    (279, "knock/wood.wav", 0.52, -0.25, "block_1"),
    (279, "sub_drop/punch.wav", 0.45, 0.0, "block_1_sub"),
    (314, "knock/wood.wav", 0.50, 0.0, "block_2"),
    (314, "sub_drop/punch.wav", 0.42, 0.0, "block_2_sub"),
    (363, "knock/wood.wav", 0.55, 0.25, "block_3"),
    (363, "sub_drop/punch.wav", 0.52, 0.0, "block_3_sub"),
    (546, "whoosh_big/thump.wav", 0.42, 0.0, "stair_unfold"),
    (662, "mallet/glock.wav", 0.30, -0.30, "step_1"),
    (674, "mallet/glock.wav", 0.32, -0.15, "step_2"),
    (675, "swish/bright.wav", 0.28, 0.20, "notebook_open"),
    (687, "mallet/glock.wav", 0.34, 0.0, "step_3"),
    (700, "mallet/glock.wav", 0.36, 0.15, "step_4"),
    (712, "mallet/glock.wav", 0.38, 0.30, "step_5"),
    (844, "knock/wood.wav", 0.52, 0.18, "phone_down"),
    (933, "pro_hover_tick/ping.wav", 0.26, -0.12, "pen_start"),
    (963, "riser/dark.wav", 0.38, 0.0, "strings_release"),
    (1050, "cut_hit/punch.wav", 0.34, -0.10, "left_foot"),
    (1060, "cut_hit/punch.wav", 0.30, 0.10, "right_foot"),
    (1125, "pro_pop_in/round.wav", 0.35, 0.0, "cta_pop"),
]


def load_wav_mono(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wf:
        arr = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    return arr


def load_earshot(rel: str) -> np.ndarray | None:
    p = EARSHOT_DIR / rel
    if not p.exists():
        return None
    tmp = OUT_DIR / f"_tmp_{p.stem}_{p.parent.name}.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(p), "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", str(tmp)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    arr = load_wav_mono(tmp)
    tmp.unlink(missing_ok=True)
    return arr


def synth_ambient_bed(dur_s: float) -> np.ndarray:
    t = np.arange(N_TOTAL) / SR
    # Warm cinematic D-minor -> F-major -> C-major -> A-minor felt pad
    chords = [
        (0.0, 10.0, [146.83, 220.00, 261.63, 349.23]),
        (10.0, 20.0, [130.81, 196.00, 246.94, 329.63]),
        (20.0, 30.0, [174.61, 220.00, 261.63, 392.00]),
        (30.0, 40.0, [146.83, 220.00, 293.66, 440.00]),
    ]
    bed = np.zeros(N_TOTAL, dtype=np.float64)
    for t0, t1, freqs in chords:
        s = int(t0 * SR)
        e = min(N_TOTAL, int(t1 * SR))
        lt = np.arange(e - s) / SR
        env = np.sin(np.pi * np.clip(lt / (t1 - t0), 0, 1)) ** 0.45
        seg = np.zeros(e - s)
        for f in freqs:
            seg += np.sin(2 * np.pi * f * lt) * 0.25 + np.sin(2 * np.pi * (f * 0.5) * lt) * 0.14
        bed[s:e] += seg * env
    sos = signal.butter(2, 900.0 / (SR * 0.5), btype="lowpass", output="sos")
    bed = signal.sosfilt(sos, bed)
    return bed / (np.max(np.abs(bed)) + 1e-9)


def fallback_impact(dur_s: float = 0.35, f: float = 95.0) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * np.exp(-t * 4.0) * t) * np.exp(-t * 10.0)


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
    narr_wav = OUT_DIR / "narration_48k.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(NARR_MP3), "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", str(narr_wav)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    narr = load_wav_mono(narr_wav)
    voice_bus = np.zeros(N_TOTAL, dtype=np.float64)
    n_copy = min(N_TOTAL, len(narr))
    voice_bus[:n_copy] = narr[:n_copy]
    voice_bus /= (np.max(np.abs(voice_bus)) + 1e-9)

    sfx_L = np.zeros(N_TOTAL, dtype=np.float64)
    sfx_R = np.zeros(N_TOTAL, dtype=np.float64)
    cache: dict[str, np.ndarray] = {}

    for frame, rel, gain, pan, _name in FRAME_CUES:
        if rel not in cache:
            arr = load_earshot(rel)
            cache[rel] = arr if arr is not None else fallback_impact()
        clip = cache[rel]
        s_idx = int(round((frame / FPS) * SR))
        e_idx = min(N_TOTAL, s_idx + len(clip))
        if e_idx <= s_idx:
            continue
        lg = math.sqrt(0.5 * (1.0 - pan))
        rg = math.sqrt(0.5 * (1.0 + pan))
        seg = clip[: e_idx - s_idx] * gain
        sfx_L[s_idx:e_idx] += seg * lg
        sfx_R[s_idx:e_idx] += seg * rg

    bed = synth_ambient_bed(DUR) * 0.20
    voice_env = np.convolve(np.abs(voice_bus), np.ones(int(0.18 * SR)) / int(0.18 * SR), mode="same")
    duck = 1.0 - 0.62 * np.clip(voice_env / 0.10, 0.0, 1.0)

    mix_L = voice_bus * 1.08 + sfx_L + bed * duck
    mix_R = voice_bus * 1.08 + sfx_R + bed * duck
    stereo = np.stack([mix_L, mix_R], axis=1)
    peak = np.max(np.abs(stereo)) + 1e-9
    if peak > 0.90:
        stereo = stereo * (0.90 / peak)

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
            "-af", "highpass=f=30,lowshelf=g=1.2:f=95,loudnorm=I=-14.0:TP=-1.5:LRA=7,aresample=48000,alimiter=limit=0.84:level=false",
            "-ar", "48000", "-ac", "2", "-sample_fmt", "s16",
            str(master_wav),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    lufs, tp = measure_lufs(master_wav)
    print(f"Master EP5 Motivation Audio: {DUR:.2f}s ({TOTAL_FRAMES} frames) | I={lufs:.1f} LUFS | TP={tp:.1f} dBTP")

    timeline = {
        "title": "Main Abhi Bhi Apni Taraf Hoon — 3D",
        "fps": FPS,
        "duration_sec": DUR,
        "total_frames": TOTAL_FRAMES,
        "audio_lufs": lufs,
        "audio_tp_db": tp,
        "beats": BEATS,
    }
    (OUT_DIR / "timeline_synced.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
