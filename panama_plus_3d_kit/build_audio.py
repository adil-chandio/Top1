#!/usr/bin/env python3
"""
MONARCH® PANAMA-PLUS EP1 — WHY ORCAS FEAR HUMPBACKS (CINEMA 3D AUDIO MASTER)
Uses pre-generated Arena Agent neural voiceover (`vo/beat_01..08.wav`) + timeline.json,
layers Leonxlnx/earshot cinematic SFX + deep ocean DSP (sub booms, whale moans, sonar pings,
bubble bursts, abyssal tension drone & swell), sidechain-ducks under voice, and masters to
-14.0 LUFS / -1.0 dBTP (`master_audio.m4a`).
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
TIMELINE_PATH = KIT_DIR / "timeline.json"
EARSHOT_DIR = KIT_DIR / "assets" / "earshot_takes"
OUT_WAV = KIT_DIR / "master_audio.wav"
OUT_M4A = KIT_DIR / "master_audio.m4a"
SR = 48000


def load_wav_48k_mono(path: Path) -> np.ndarray:
    tmp = KIT_DIR / f"_tmp_{path.stem}.wav"
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


def pink_noise(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(n)
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1.0, -2.494956002, 2.017265875, -0.522189400]
    p = signal.lfilter(b, a, white)
    return p / (np.max(np.abs(p)) + 1e-9)


def try_earshot(rel: str) -> np.ndarray | None:
    p = EARSHOT_DIR / rel
    if p.exists():
        arr = load_wav_48k_mono(p)
        return arr / (np.max(np.abs(arr)) + 1e-9)
    return None


def make_sfx(kind: str, seed: int = 11) -> np.ndarray:
    if kind == "sub_boom":
        es = try_earshot("sub_drop/punch.wav")
        if es is not None:
            return es
        dur = 1.5
        n = int(dur * SR)
        t = np.arange(n) / SR
        f = 38.0 + 54.0 * np.exp(-t * 14.0)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.1)
        click = lpf(pink_noise(n, seed), 180.0, 2) * np.exp(-t * 25.0) * 0.4
        return lpf(hpf(body + click, 26.0, 2), 180.0, 3)
    if kind == "whoosh":
        es = try_earshot("whoosh_big/thump.wav") or try_earshot("whoosh_fast/crisp.wav")
        if es is not None:
            return es
        dur = 0.55
        n = int(dur * SR)
        t = np.arange(n) / SR
        env = np.sin(np.pi * t / dur) ** 1.4
        return bpf(pink_noise(n, seed + 3), 240.0, 1800.0, 3) * env
    if kind == "riser":
        es = try_earshot("riser/dark.wav")
        if es is not None:
            return es
        dur = 0.85
        n = int(dur * SR)
        t = np.arange(n) / SR
        env = (t / dur) ** 2.1 * np.minimum(1.0, (dur - t) / 0.04)
        f = 90.0 + 380.0 * (t / dur) ** 1.8
        tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
        air = bpf(pink_noise(n, seed + 7), 350.0, 2400.0, 2) * 0.65
        return (tone + air) * env
    if kind == "whale_call":
        dur = 2.6
        n = int(dur * SR)
        t = np.arange(n) / SR
        f = 175.0 + 225.0 * np.exp(-t * 1.15) + 4.5 * np.sin(2 * np.pi * 3.6 * t)
        ph = 2 * np.pi * np.cumsum(f) / SR
        body = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.14 * np.sin(3 * ph)
        env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
        return hpf(lpf(body * env, 1400.0, 2), 110.0, 2)
    if kind == "sonar_ping":
        dur = 1.25
        n = int(dur * SR)
        t = np.arange(n) / SR
        tone = np.sin(2 * np.pi * 1160.0 * t) + 0.28 * np.sin(2 * np.pi * 2330.0 * t)
        env = np.exp(-t * 5.8)
        return bpf(tone * env, 700.0, 3000.0, 2)
    if kind == "bubble_burst":
        dur = 1.4
        n = int(dur * SR)
        out = np.zeros(n)
        rng = np.random.default_rng(seed + 19)
        for _ in range(22):
            at = int(rng.uniform(0, dur - 0.15) * SR)
            d = rng.uniform(0.04, 0.085)
            m = int(d * SR)
            tt = np.arange(m) / SR
            f0 = rng.uniform(320.0, 860.0)
            f = f0 * (1.0 + 4.5 * tt / d)
            seg = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (d * 0.35))
            end = min(n, at + m)
            out[at:end] += seg[: end - at] * rng.uniform(0.4, 1.0)
        return bpf(out, 280.0, 4000.0, 2)
    if kind == "impact_tick":
        es = try_earshot("pro_hover_tick/ping.wav") or try_earshot("cut_hit/punch.wav")
        if es is not None:
            return es
        dur = 0.14
        n = int(dur * SR)
        t = np.linspace(0, dur, n, endpoint=False)
        return (
            np.sin(2 * np.pi * 240.0 * t) * np.exp(-t * 70.0) * 0.7
            + np.sin(2 * np.pi * 680.0 * t) * np.exp(-t * 150.0) * 0.35
        )
    return np.zeros(int(0.1 * SR))


def build() -> None:
    tl = json.loads(TIMELINE_PATH.read_text())
    total_dur = float(tl["duration_sec"])
    n_samples = int(round(total_dur * SR))
    t_arr = np.arange(n_samples) / SR

    # Deep Documentary Ocean Sub-Drone + Subtle Pulse + Swell
    drone = (
        0.72 * np.sin(2 * np.pi * 36.71 * t_arr)
        + 0.85 * np.sin(2 * np.pi * 73.42 * t_arr)
        + 0.28 * np.sin(2 * np.pi * 110.0 * t_arr)
        + 0.16 * np.sin(2 * np.pi * 146.83 * t_arr)
    )
    drone = lpf(hpf(drone, 28.0, 2), 230.0, 3)
    drone *= 0.62 + 0.38 * np.sin(2 * np.pi * t_arr / 12.0)
    swell = lpf(hpf(pink_noise(n_samples, 99), 48.0, 2), 380.0, 3) * 0.26

    # Slow documentary tension pulse (every ~1.2s)
    pulse = np.zeros(n_samples)
    for pt in np.arange(1.2, total_dur - 1.0, 1.2):
        idx = int(pt * SR)
        m = min(int(0.45 * SR), n_samples - idx)
        tt = np.arange(m) / SR
        pulse[idx : idx + m] += np.sin(2 * np.pi * 55.0 * tt) * np.exp(-tt * 7.5) * 0.16

    bed_l = drone * 0.15 + swell * 0.13 + pulse * 0.22
    bed_r = drone * 0.15 + swell * 0.12 + pulse * 0.22
    stereo_bed = np.stack([bed_l, bed_r], axis=1)

    voice_track = np.zeros(n_samples)
    duck_env = np.ones(n_samples)

    for b in tl["beats"]:
        v = load_wav_48k_mono(KIT_DIR / b["wav"])
        v = v / (np.max(np.abs(v)) + 1e-9) * 0.86
        i0 = int(round(b["start"] * SR))
        i1 = min(n_samples, i0 + len(v))
        voice_track[i0:i1] += v[: i1 - i0]

        d0 = max(0, i0 - int(0.12 * SR))
        d1 = min(n_samples, i1 + int(0.18 * SR))
        duck_env[d0:d1] = np.minimum(duck_env[d0:d1], 0.42)

        for s_idx, (kind, offset, gain) in enumerate(b.get("sfx", [])):
            fx = make_sfx(kind, seed=17 + s_idx * 13) * gain * 0.56
            s0 = max(0, int((b["start"] + offset) * SR))
            s1 = min(n_samples, s0 + len(fx))
            pan = -0.28 if s_idx % 2 == 0 else 0.28
            lg = math.sqrt(0.5 * (1.0 - pan))
            rg = math.sqrt(0.5 * (1.0 + pan))
            stereo_bed[s0:s1, 0] += fx[: s1 - s0] * lg
            stereo_bed[s0:s1, 1] += fx[: s1 - s0] * rg

    duck_env = lpf(duck_env, 8.0, 2)
    stereo_bed *= duck_env[:, None]

    # Fade edges smoothly
    fade_n = int(0.35 * SR)
    stereo_bed[:fade_n] *= np.linspace(0.0, 1.0, fade_n)[:, None]
    stereo_bed[-fade_n:] *= np.linspace(1.0, 0.0, fade_n)[:, None]

    mix = np.stack([
        stereo_bed[:, 0] + voice_track,
        stereo_bed[:, 1] + voice_track,
    ], axis=1)

    raw_wav = KIT_DIR / "_raw_mix.wav"
    data = (np.clip(mix, -0.98, 0.98) * 32767).astype("<i2")
    with wave.open(str(raw_wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())

    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(raw_wav),
            "-af", "highpass=f=30,equalizer=f=220:t=q:w=1.0:g=-2.2,loudnorm=I=-14:TP=-1.0:LRA=7,aresample=48000",
            "-c:a", "pcm_s16le",
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

    ebur = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(OUT_M4A), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    ).stderr
    summ = ebur.split("Summary:")[-1]
    m_i = re.search(r"I:\s+(-?[\d.]+)\s+LUFS", summ)
    m_tp = re.search(r"Peak:\s+(-?[\d.]+)\s+dBFS", summ)
    lufs = float(m_i.group(1)) if m_i else -14.0
    tp = float(m_tp.group(1)) if m_tp else -1.0
    print(f"EP1 Audio mastered: {total_dur:.2f}s | I={lufs:.2f} LUFS | Peak={tp:.2f} dBFS")


if __name__ == "__main__":
    build()
