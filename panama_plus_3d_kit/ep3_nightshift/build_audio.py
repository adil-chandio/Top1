#!/usr/bin/env python3
"""
MONARCH NIGHT SHIFT EP01: THE SANDWICH HEIST — CINEMA AUDIO MASTER (-14 LUFS)
Uses pre-generated Arena Agent comedic bear voiceover (`vo/line_01..06.wav`) + timeline.json,
adds 3:00 AM suburban cricket/wind ambience, camera shutter flash, wooden plank clack,
sneaky upright-bass heist groove, and masters to -14.0 LUFS / -1.0 dBTP (`master_audio.m4a`).
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

EP_DIR = Path(__file__).resolve().parent
TIMELINE_PATH = EP_DIR / "timeline.json"
EARSHOT_DIR = EP_DIR / "assets" / "earshot_takes"
OUT_WAV = EP_DIR / "master_audio.wav"
OUT_M4A = EP_DIR / "master_audio.m4a"
SR = 48000


def load_wav_48k_mono(path: Path) -> np.ndarray:
    tmp = EP_DIR / f"_tmp_{path.stem}.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", str(tmp)],
        check=True,
    )
    with wave.open(str(tmp), "rb") as w:
        raw = w.readframes(w.getnframes())
    tmp.unlink(missing_ok=True)
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0


def lpf(x: np.ndarray, hz: float, order: int = 3) -> np.ndarray:
    sos = signal.butter(order, min(hz / (SR * 0.5), 0.95), btype="low", output="sos")
    return signal.sosfilt(sos, x)


def bpf(x: np.ndarray, lo: float, hi: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, [lo / (SR * 0.5), min(hi / (SR * 0.5), 0.95)], btype="band", output="sos")
    return signal.sosfilt(sos, x)


def try_earshot(rel: str) -> np.ndarray | None:
    p = EARSHOT_DIR / rel
    if p.exists():
        arr = load_wav_48k_mono(p)
        return arr / (np.max(np.abs(arr)) + 1e-9)
    return None


def make_sfx(kind: str, seed: int = 44) -> np.ndarray:
    if kind == "shutter":
        es = try_earshot("cut_hit/punch.wav")
        n = int(0.18 * SR); t = np.arange(n) / SR
        rng = np.random.default_rng(seed)
        click = bpf(rng.standard_normal(n), 1800.0, 6200.0, 2) * np.exp(-t * 48.0)
        return click * 0.8 + (es[:n] * 0.4 if es is not None and len(es) >= n else 0.0)
    if kind == "door_creak":
        n = int(0.65 * SR); t = np.arange(n) / SR
        return bpf(np.sin(2 * np.pi * (170.0 + 35.0 * np.sin(t * 28.0)) * t), 140.0, 950.0, 2) * np.sin(np.pi * t / 0.65) * 0.45
    if kind == "wood_thud":
        es = try_earshot("sub_drop/punch.wav")
        if es is not None:
            return es
        n = int(0.45 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * (92.0 + 50.0 * np.exp(-t * 22.0)) * t) * np.exp(-t * 8.0) * 0.8
    if kind == "whoosh":
        es = try_earshot("whoosh_fast/crisp.wav")
        if es is not None:
            return es
        n = int(0.42 * SR); t = np.arange(n) / SR
        return bpf(np.random.default_rng(seed).standard_normal(n), 300.0, 2200.0, 2) * np.sin(np.pi * t / 0.42) * 0.55
    return np.zeros(int(0.1 * SR))


def build() -> None:
    tl = json.loads(TIMELINE_PATH.read_text())
    total_dur = float(tl["duration_sec"])
    n_samples = int(round(total_dur * SR))
    t_arr = np.arange(n_samples) / SR
    rng = np.random.default_rng(77)

    # 3:00 AM Suburban Night Air + Soft Crickets + Sneaky Upright Bass Pizzicato
    night_air = lpf(rng.standard_normal(n_samples), 320.0, 2) * 0.032
    crickets = np.zeros(n_samples)
    for ct in np.arange(0.6, total_dur - 0.5, 2.3):
        i0 = int(ct * SR)
        m = min(int(0.35 * SR), n_samples - i0)
        tt = np.arange(m) / SR
        pulse = (0.5 + 0.5 * np.sin(2 * np.pi * 24.0 * tt)) ** 2
        crickets[i0 : i0 + m] += np.sin(2 * np.pi * 4320.0 * tt) * pulse * np.sin(np.pi * tt / 0.35) * 0.014

    # Sneaky noir-comedy pizzicato walking bassline (E minor: E2, G2, A2, B2, Bb2, A2, G2, F#2)
    bass_notes = [82.41, 98.00, 110.00, 123.47, 116.54, 110.00, 98.00, 92.50]
    bass_bed = np.zeros(n_samples)
    step_s = 0.58
    for idx, bt in enumerate(np.arange(0.4, total_dur - 1.2, step_s)):
        f0 = bass_notes[idx % len(bass_notes)]
        i0 = int(bt * SR)
        m = min(int(0.45 * SR), n_samples - i0)
        tt = np.arange(m) / SR
        pluck = (np.sin(2 * np.pi * f0 * tt) + 0.45 * np.sin(4 * np.pi * f0 * tt) * np.exp(-tt * 9.0)) * np.exp(-tt * 5.8)
        bass_bed[i0 : i0 + m] += pluck * 0.14

    bed = night_air + crickets + bass_bed
    stereo_bed = np.stack([bed, bed], axis=1)

    # Story-beat SFX cues
    beat_sfx = {
        "driveway_entry": [("door_creak", 4.5, 0.55)],
        "jackpot_freeze": [("whoosh", 0.2, 0.45), ("door_creak", 4.2, 0.50)],
        "flash_plank": [("shutter", 1.15, 0.85), ("wood_thud", 4.6, 0.65)],
        "dignity_exit": [("whoosh", 3.6, 0.55)],
        "outro_crane": [("whoosh", 0.2, 0.40)],
    }

    voice_track = np.zeros(n_samples)
    duck_env = np.ones(n_samples)

    for b in tl["beats"]:
        if b.get("wav"):
            v = load_wav_48k_mono(EP_DIR / b["wav"])
            v = v / (np.max(np.abs(v)) + 1e-9) * 0.88
            i0 = int(round(b["start"] * SR))
            i1 = min(n_samples, i0 + len(v))
            voice_track[i0:i1] += v[: i1 - i0]

            d0 = max(0, i0 - int(0.10 * SR))
            d1 = min(n_samples, i1 + int(0.15 * SR))
            duck_env[d0:d1] = np.minimum(duck_env[d0:d1], 0.42)

        for s_idx, (kind, offset, gain) in enumerate(beat_sfx.get(b["id"], [])):
            fx = make_sfx(kind, seed=81 + s_idx * 7) * gain
            s0 = max(0, int((b["start"] + offset) * SR))
            s1 = min(n_samples, s0 + len(fx))
            pan = -0.22 if s_idx % 2 == 0 else 0.22
            stereo_bed[s0:s1, 0] += fx[: s1 - s0] * math.sqrt(0.5 * (1.0 - pan))
            stereo_bed[s0:s1, 1] += fx[: s1 - s0] * math.sqrt(0.5 * (1.0 + pan))

    duck_env = lpf(duck_env, 10.0, 2)
    stereo_bed *= duck_env[:, None]

    mix = np.stack([stereo_bed[:, 0] + voice_track, stereo_bed[:, 1] + voice_track], axis=1)
    raw_wav = EP_DIR / "_raw_mix.wav"
    data = (np.clip(mix, -0.98, 0.98) * 32767).astype("<i2")
    with wave.open(str(raw_wav), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())

    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw_wav),
            "-af", "highpass=f=30,equalizer=f=240:t=q:w=1.0:g=-2.0,loudnorm=I=-14:TP=-1.0:LRA=7,aresample=48000",
            "-c:a", "pcm_s16le", str(OUT_WAV),
        ],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(OUT_WAV), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(OUT_M4A)],
        check=True,
    )
    raw_wav.unlink(missing_ok=True)

    eb = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(OUT_M4A), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    ).stderr
    summ = eb.split("Summary:")[-1]
    lufs = float(re.search(r"I:\s+(-?[\d.]+)\s+LUFS", summ).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+)\s+dBFS", summ).group(1))
    print(f"EP3 NightShift Audio mastered: {total_dur:.2f}s | I={lufs:.2f} LUFS | Peak={tp:.2f} dBFS")


if __name__ == "__main__":
    build()
