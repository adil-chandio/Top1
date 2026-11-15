#!/usr/bin/env python3
"""
MONARCH® STUDIO B2B 3D COMMERCIAL — CINEMA AUDIO MASTER (-14 LUFS)
Uses pre-generated Arena Agent voiceover (`vo/beat_01..06.wav`) + timeline.json,
layers Leonxlnx/earshot cinematic hits & risers + dark-luxury analog synth pulse,
sidechain-ducks under voice, and masters to -14.0 LUFS / -1.0 dBTP (`master_audio.m4a`).
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


def hpf(x: np.ndarray, hz: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, max(hz / (SR * 0.5), 0.0005), btype="high", output="sos")
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


def make_sfx(kind: str, seed: int = 21) -> np.ndarray:
    if kind == "sub_boom":
        es = try_earshot("sub_drop/punch.wav")
        if es is not None:
            return es
        n = int(1.4 * SR); t = np.arange(n) / SR
        f = 38.0 + 62.0 * np.exp(-t * 16.0)
        return lpf(hpf(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2), 26.0, 2), 180.0, 3)
    if kind == "whoosh":
        es = try_earshot("whoosh_fast/crisp.wav") or try_earshot("whoosh_big/thump.wav")
        if es is not None:
            return es
        n = int(0.5 * SR); t = np.arange(n) / SR
        rng = np.random.default_rng(seed)
        return bpf(rng.standard_normal(n), 320.0, 2200.0, 3) * (np.sin(np.pi * t / 0.5) ** 1.3)
    if kind == "riser":
        es = try_earshot("riser/dark.wav")
        if es is not None:
            return es
        n = int(0.75 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * np.cumsum(95.0 + 420.0 * (t / 0.75) ** 1.9) / SR) * ((t / 0.75) ** 2.0) * 0.5
    if kind == "impact_tick":
        es = try_earshot("pro_hover_tick/ping.wav") or try_earshot("cut_hit/punch.wav")
        if es is not None:
            return es
        n = int(0.14 * SR); t = np.linspace(0, 0.14, n, endpoint=False)
        return np.sin(2 * np.pi * 240.0 * t) * np.exp(-t * 65.0) * 0.7
    return np.zeros(int(0.1 * SR))


def build() -> None:
    tl = json.loads(TIMELINE_PATH.read_text())
    total_dur = float(tl["duration_sec"])
    n_samples = int(round(total_dur * SR))
    t_arr = np.arange(n_samples) / SR

    # Dark-Luxury Electronic Pulse + Sub Pad (116 BPM)
    beat_iv = 60.0 / 116.0
    pulse = np.zeros(n_samples)
    for bt in np.arange(0.0, total_dur, beat_iv):
        i0 = int(bt * SR)
        m = min(int(0.28 * SR), n_samples - i0)
        tt = np.arange(m) / SR
        f = 55.0 + 38.0 * np.exp(-tt * 28.0)
        pulse[i0 : i0 + m] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7.5) * 0.42

    pad = (
        0.55 * np.sin(2 * np.pi * 110.0 * t_arr)
        + 0.40 * np.sin(2 * np.pi * 164.81 * t_arr)
        + 0.30 * np.sin(2 * np.pi * 220.0 * t_arr)
        + 0.22 * np.sin(2 * np.pi * 261.63 * t_arr)
    )
    pad = lpf(pad, 620.0, 2) * (0.55 + 0.45 * np.sin(2 * np.pi * t_arr / 8.0))
    bed = pulse * 0.24 + pad * 0.14
    stereo_bed = np.stack([bed, bed], axis=1)

    voice_track = np.zeros(n_samples)
    duck_env = np.ones(n_samples)

    for b in tl["beats"]:
        v = load_wav_48k_mono(EP_DIR / b["wav"])
        v = v / (np.max(np.abs(v)) + 1e-9) * 0.88
        i0 = int(round(b["start"] * SR))
        i1 = min(n_samples, i0 + len(v))
        voice_track[i0:i1] += v[: i1 - i0]

        d0 = max(0, i0 - int(0.10 * SR))
        d1 = min(n_samples, i1 + int(0.15 * SR))
        duck_env[d0:d1] = np.minimum(duck_env[d0:d1], 0.40)

        for s_idx, (kind, offset, gain) in enumerate(b.get("sfx", [])):
            fx = make_sfx(kind, seed=31 + s_idx * 11) * gain * 0.56
            s0 = max(0, int((b["start"] + offset) * SR))
            s1 = min(n_samples, s0 + len(fx))
            pan = -0.25 if s_idx % 2 == 0 else 0.25
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
    print(f"EP2 B2B Audio mastered: {total_dur:.2f}s | I={lufs:.2f} LUFS | Peak={tp:.2f} dBFS")


if __name__ == "__main__":
    build()
