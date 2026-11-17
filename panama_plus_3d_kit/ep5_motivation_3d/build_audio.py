#!/usr/bin/env python3
"""
MONARCH® PANAMA-PLUS EP5 — MAIN ABHI BHI APNI TARAF HOON (40s CINEMA 3D AUDIO MASTER)
Locks directly to `narration-urdu.mp3` (40.000s), builds a warm felt-piano + chord bed +
nocturnal rain outside window + frame-locked Leonxlnx/earshot SFX, mastered to -14.0 LUFS / -1.0 dBTP.
"""
from __future__ import annotations

import math
import re
import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy import signal

KIT_DIR = Path(__file__).resolve().parent
EARSHOT_DIR = KIT_DIR / "assets" / "earshot_takes"
NARR_MP3 = KIT_DIR / "narration-urdu.mp3"
OUT_WAV = KIT_DIR / "master_audio.wav"
OUT_M4A = KIT_DIR / "master_audio.m4a"
SR = 48000
FPS = 30
DUR = 40.0
N_TOTAL = int(DUR * SR)

FRAME_CUES = [
    (279, "knock/wood.wav", 0.54, -0.22, "block_1"),
    (279, "sub_drop/punch.wav", 0.46, 0.0, "block_1_sub"),
    (314, "knock/wood.wav", 0.52, 0.0, "block_2"),
    (314, "sub_drop/punch.wav", 0.44, 0.0, "block_2_sub"),
    (363, "knock/wood.wav", 0.56, 0.22, "block_3"),
    (363, "sub_drop/punch.wav", 0.54, 0.0, "block_3_sub"),
    (546, "whoosh_big/thump.wav", 0.44, 0.0, "stair_unfold"),
    (662, "mallet/glock.wav", 0.32, -0.28, "step_1"),
    (674, "mallet/glock.wav", 0.34, -0.14, "step_2"),
    (675, "swish/bright.wav", 0.30, 0.18, "notebook_open"),
    (687, "mallet/glock.wav", 0.36, 0.0, "step_3"),
    (700, "mallet/glock.wav", 0.38, 0.14, "step_4"),
    (712, "mallet/glock.wav", 0.40, 0.28, "step_5"),
    (844, "knock/wood.wav", 0.54, 0.18, "phone_down"),
    (933, "pro_hover_tick/ping.wav", 0.28, -0.12, "pen_start"),
    (963, "riser/dark.wav", 0.42, 0.0, "rise_up"),
    (1050, "cut_hit/punch.wav", 0.36, -0.10, "left_foot"),
    (1060, "cut_hit/punch.wav", 0.32, 0.10, "right_foot"),
    (1125, "pro_pop_in/round.wav", 0.38, 0.0, "cta_pop"),
]


def load_wav_48k_mono(path: Path) -> np.ndarray:
    tmp = KIT_DIR / f"_tmp_{path.stem}.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", str(tmp)],
        check=True,
    )
    with wave.open(str(tmp), "rb") as wf:
        arr = np.frombuffer(wf.readframes(wf.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
    tmp.unlink(missing_ok=True)
    return arr


def load_earshot(rel: str) -> np.ndarray | None:
    p = EARSHOT_DIR / rel
    return load_wav_48k_mono(p) if p.exists() else None


def synth_felt_piano_bed() -> np.ndarray:
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
        for idx, f in enumerate(freqs):
            seg += np.sin(2 * np.pi * f * lt) * 0.24 + np.sin(2 * np.pi * (f * 0.5) * lt) * 0.14
            # Gentle arpeggio pluck every 2.5s
            for beat_off in (0.0, 2.5, 5.0, 7.5):
                at = beat_off + idx * 0.38
                if at < (t1 - t0):
                    a0 = int(at * SR)
                    m = min(int(1.8 * SR), (e - s) - a0)
                    if m > 0:
                        pt = np.arange(m) / SR
                        seg[a0 : a0 + m] += np.sin(2 * np.pi * f * pt) * np.exp(-pt * 3.2) * 0.14
        bed[s:e] += seg * env
    sos = signal.butter(2, 1050.0 / (SR * 0.5), btype="lowpass", output="sos")
    bed = signal.sosfilt(sos, bed)

    # Subtle distant window rain hush
    rng = np.random.default_rng(505)
    rain = rng.standard_normal(N_TOTAL)
    sos_r = signal.butter(2, [350 / (SR * 0.5), 2400 / (SR * 0.5)], btype="bandpass", output="sos")
    rain = signal.sosfilt(sos_r, rain)
    rain = rain / (np.max(np.abs(rain)) + 1e-9) * 0.08
    return bed / (np.max(np.abs(bed)) + 1e-9) + rain


def fallback_impact(dur_s: float = 0.35, f: float = 95.0) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * np.exp(-t * 4.0) * t) * np.exp(-t * 10.0)


def main() -> None:
    narr = load_wav_48k_mono(NARR_MP3)
    voice_bus = np.zeros(N_TOTAL, dtype=np.float64)
    n_copy = min(N_TOTAL, len(narr))
    voice_bus[:n_copy] = narr[:n_copy]
    voice_bus /= np.max(np.abs(voice_bus)) + 1e-9

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

    bed = synth_felt_piano_bed() * 0.24
    voice_env = np.convolve(np.abs(voice_bus), np.ones(int(0.18 * SR)) / int(0.18 * SR), mode="same")
    duck = 1.0 - 0.58 * np.clip(voice_env / 0.10, 0.0, 1.0)

    mix_L = voice_bus * 1.06 + sfx_L + bed * duck
    mix_R = voice_bus * 1.06 + sfx_R + bed * duck
    stereo = np.stack([mix_L, mix_R], axis=1)
    peak = np.max(np.abs(stereo)) + 1e-9
    if peak > 0.90:
        stereo = stereo * (0.90 / peak)

    raw_wav = KIT_DIR / "_raw_mix.wav"
    data = (np.clip(stereo, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(str(raw_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(data.tobytes())

    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(raw_wav),
            "-af", "highpass=f=30,lowshelf=g=1.2:f=95,loudnorm=I=-14.0:TP=-1.0:LRA=7,aresample=48000",
            "-ar", "48000", "-ac", "2", "-sample_fmt", "s16",
            str(OUT_WAV),
        ],
        check=True,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(OUT_WAV), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(OUT_M4A),
        ],
        check=True,
    )
    raw_wav.unlink(missing_ok=True)

    eb = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(OUT_M4A), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    ).stderr
    summ = eb.split("Summary:")[-1]
    lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))
    print(f"Master EP5 Audio: {DUR:.2f}s | I={lufs:.1f} LUFS | TP={tp:.1f} dBTP")


if __name__ == "__main__":
    main()
