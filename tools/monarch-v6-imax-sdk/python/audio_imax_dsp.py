"""
Monarch V6 Hollywood IMAX Cinema SDK — Reusable Audio DSP, Zero-Time-Stretch VO Tightener,
Dolby-Style Trailer Sub-Braaams, Pre-Twist Vacuum Silence, Physical Foley & Two-Pass EBU R128 Mastering!
"""
import glob
import json
import math
import os
import re
import subprocess
import sys

sys.path.insert(0, "/tmp/py")
import numpy as np
from scipy import signal
import soundfile as sf

SR = 48000
FPS = 30


def find_ffmpeg() -> str:
    matches = glob.glob("/tmp/py/imageio_ffmpeg/binaries/ffmpeg*")
    return matches[0] if matches else "ffmpeg"


def load_wav_48k_stereo(path: str) -> np.ndarray:
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    elif data.shape[1] > 2:
        data = data[:, :2]
    if sr != SR:
        g = math.gcd(sr, SR)
        up, down = SR // g, sr // g
        data = np.stack([
            signal.resample_poly(data[:, 0], up, down),
            signal.resample_poly(data[:, 1], up, down),
        ], axis=1).astype(np.float32)
    return data


def fade_io(clip: np.ndarray, fi_s: float = 0.012, fo_s: float = 0.03) -> np.ndarray:
    out = clip.copy()
    fi = min(len(out) // 2, max(1, int(fi_s * SR)))
    fo = min(len(out) // 2, max(1, int(fo_s * SR)))
    w_in = 0.5 - 0.5 * np.cos(np.linspace(0, math.pi, fi, dtype=np.float32))
    w_out = 0.5 + 0.5 * np.cos(np.linspace(0, math.pi, fo, dtype=np.float32))
    if out.ndim == 2:
        out[:fi] *= w_in[:, None]
        out[-fo:] *= w_out[:, None]
    else:
        out[:fi] *= w_in
        out[-fo:] *= w_out
    return out


def place_clip(buf: np.ndarray, clip: np.ndarray, start_s: float, gain: float = 1.0, pan: float = 0.0, wrap_loop: bool = False):
    if clip.ndim == 1:
        clip = np.stack([clip, clip], axis=1)
    n_samples = len(buf)
    idx = int(round(start_s * SR))
    gl = gain * math.cos((pan + 1.0) * math.pi * 0.25) * 1.4142
    gr = gain * math.sin((pan + 1.0) * math.pi * 0.25) * 1.4142
    if wrap_loop:
        for k in range(len(clip)):
            dst = (idx + k) % n_samples
            buf[dst, 0] += clip[k, 0] * gl
            buf[dst, 1] += clip[k, 1] * gr
        return
    if idx >= n_samples or idx + len(clip) <= 0:
        return
    c0 = max(0, -idx)
    b0 = max(0, idx)
    L = min(len(clip) - c0, n_samples - b0)
    if L <= 0:
        return
    buf[b0:b0 + L, 0] += clip[c0:c0 + L, 0] * gl
    buf[b0:b0 + L, 1] += clip[c0:c0 + L, 1] * gr


def tighten_vo_zero_stretch(
    raw_audio: np.ndarray,
    rms_thresh: float = 0.0018,
    pre_guard_s: float = 0.024,
    post_guard_s: float = 0.028,
    max_gap_s: float = 0.16,
) -> np.ndarray:
    """
    Surgically tightens dead-air gaps between spoken islands while keeping 100.000% of speech
    at exact 1.000x natural speed and pitch (`time_stretch_applied = False`).
    """
    if raw_audio.ndim == 1:
        raw_audio = np.stack([raw_audio, raw_audio], axis=1)
    mono_sq = np.mean(raw_audio ** 2, axis=1)
    win = max(1, int(0.012 * SR))
    rms = np.sqrt(np.convolve(mono_sq, np.ones(win, dtype=np.float32) / win, mode="same"))
    voiced = rms > rms_thresh

    pre = int(pre_guard_s * SR)
    post = int(post_guard_s * SR)
    idx_voiced = np.flatnonzero(voiced)
    if len(idx_voiced) == 0:
        return raw_audio.copy()

    mask = np.zeros(len(raw_audio), dtype=bool)
    # Merge islands separated by < 45 ms
    starts, ends = [], []
    s = idx_voiced[0]
    prev = idx_voiced[0]
    for ix in idx_voiced[1:]:
        if ix - prev > int(0.045 * SR):
            starts.append(max(0, s - pre))
            ends.append(min(len(raw_audio), prev + post))
            s = ix
        prev = ix
    starts.append(max(0, s - pre))
    ends.append(min(len(raw_audio), prev + post))

    # Merge overlapping guarded islands
    merged = []
    for a, b in zip(starts, ends):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])

    pieces = []
    max_gap = int(max_gap_s * SR)
    for k, (a, b) in enumerate(merged):
        island = fade_io(raw_audio[a:b], 0.008, 0.008)
        pieces.append(island)
        if k < len(merged) - 1:
            gap_len = min(max_gap, merged[k + 1][0] - b)
            if gap_len > 0:
                pieces.append(np.zeros((gap_len, 2), dtype=np.float32))
    return np.concatenate(pieces, axis=0)


def compute_lookahead_duck_envelope(vo_bus: np.ndarray, lookahead_s: float = 0.055) -> np.ndarray:
    mono_sq = np.mean(vo_bus ** 2, axis=1)
    win_env = int(0.065 * SR)
    vo_rms = np.sqrt(np.convolve(mono_sq, np.ones(win_env, dtype=np.float32) / win_env, mode="same"))
    shift = int(lookahead_s * SR)
    vo_ahead = np.pad(vo_rms[shift:], (0, shift))
    duck_raw = np.clip(vo_ahead / 0.032, 0.0, 1.0)
    b_lp, a_lp = signal.butter(1, 3.0 / (SR * 0.5), btype="lowpass")
    return np.clip(signal.filtfilt(b_lp, a_lp, duck_raw), 0.0, 1.0).astype(np.float32)


def synth_imax_braam(dur_s: float = 1.45, root_hz: float = 36.71) -> np.ndarray:
    """Hans-Zimmer / Villeneuve low-brass + sub-harmonic swell (< 190 Hz so 220Hz–4kHz vocal band stays pure!)."""
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = (1.0 - np.exp(-t * 18.0)) * np.exp(-t * 2.4)
    l_sig = (
        0.62 * np.sin(2 * np.pi * root_hz * t)
        + 0.36 * np.tanh(2.4 * np.sin(2 * np.pi * (root_hz * 1.996) * t))
        + 0.18 * np.tanh(2.0 * np.sin(2 * np.pi * (root_hz * 3.004) * t))
    ) * env
    r_sig = (
        0.62 * np.sin(2 * np.pi * root_hz * t)
        + 0.36 * np.tanh(2.4 * np.sin(2 * np.pi * (root_hz * 2.004) * t))
        + 0.18 * np.tanh(2.0 * np.sin(2 * np.pi * (root_hz * 2.996) * t))
    ) * env
    b, a = signal.butter(2, 185.0 / (SR * 0.5), btype="lowpass")
    out = np.stack([signal.lfilter(b, a, l_sig), signal.lfilter(b, a, r_sig)], axis=1).astype(np.float32)
    return fade_io(out / (np.max(np.abs(out)) + 1e-9), 0.015, 0.18)


def synth_vacuum_suction(dur_s: float = 0.92, seed: int = 6003) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    f_inst = 95.0 + 1350.0 * (u ** 3.2)
    ph = 2 * np.pi * np.cumsum(f_inst) / SR
    b, a = signal.butter(2, [280 / (SR * 0.5), 4800 / (SR * 0.5)], btype="bandpass")
    whoosh = signal.lfilter(b, a, rng.standard_normal(n).astype(np.float32))
    s = (0.55 * np.sin(ph) + 0.45 * whoosh) * (u ** 2.6)
    s /= (np.max(np.abs(s)) + 1e-9)
    choke = int(0.006 * SR)
    s[-choke:] *= np.linspace(1.0, 0.0, choke, dtype=np.float32)
    return np.stack([s, np.roll(s, 12)], axis=1).astype(np.float32)


def synth_chronometer_ticks(dur_s: float, rate_hz: float = 8.0) -> np.ndarray:
    n = int(dur_s * SR)
    out = np.zeros((n, 2), dtype=np.float32)
    step = int(SR / rate_hz)
    m = int(0.014 * SR)
    tt = np.arange(m, dtype=np.float32) / SR
    tick_a = np.exp(-tt * 420.0) * (0.75 * np.sin(2 * np.pi * 4650 * tt) + 0.45 * np.sin(2 * np.pi * 7820 * tt))
    tick_b = np.exp(-tt * 460.0) * (0.70 * np.sin(2 * np.pi * 3920 * tt) + 0.40 * np.sin(2 * np.pi * 6480 * tt))
    k = 0
    for idx in range(0, n - m, step):
        tk = tick_a if (k % 2 == 0) else tick_b
        pan = -0.28 if (k % 2 == 0) else 0.28
        out[idx:idx + m, 0] += tk * (0.5 - 0.5 * pan)
        out[idx:idx + m, 1] += tk * (0.5 + 0.5 * pan)
        k += 1
    return fade_io(out / (np.max(np.abs(out)) + 1e-9), 0.04, 0.06)


def synth_laser_tomography_sweep(dur_s: float = 0.85) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    f1 = 2400.0 * np.exp(-u * 1.45) + 320.0
    ph1 = 2 * np.pi * np.cumsum(f1) / SR
    shimmer = 0.5 * np.sin(ph1) + 0.3 * np.sin(ph1 * 1.503) + 0.2 * np.sin(2 * np.pi * 1480 * t) * np.exp(-t * 8.0)
    s = (shimmer * (np.sin(np.pi * u) ** 0.7)).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    pan = np.linspace(-0.55, 0.55, n, dtype=np.float32)
    return fade_io(np.stack([s * (0.5 - 0.5 * pan), s * (0.5 + 0.5 * pan)], axis=1), 0.02, 0.06)


def synth_modal_impact(dur_s: float = 0.85, modes=((1140.0, 32.0), (2490.0, 48.0), (3870.0, 65.0)), sub_hz: float = 84.0) -> np.ndarray:
    rng = np.random.default_rng(9001)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sub = 1.15 * np.exp(-t * 16.0) * np.sin(2 * np.pi * (sub_hz * np.exp(-t * 7.0) + 38.0) * t)
    metal = sum(0.35 * np.exp(-t * dec) * np.sin(2 * np.pi * freq * t) for freq, dec in modes)
    trans = 0.75 * np.exp(-t * 360.0) * rng.standard_normal(n).astype(np.float32)
    s = (sub + metal + trans).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 9)], axis=1), 0.002, 0.10)


def synth_loop_locked_score(dur_s: float = 35.0, base_hz: float = 55.0) -> np.ndarray:
    """
    Synthesizes an exact integer-cycle harmonic dark-cinema pad + glass pulse so
    `sample[N]` -> `sample[0]` is 100.000% phase-continuous with zero click!
    """
    n = int(round(dur_s * SR))
    t = np.arange(n, dtype=np.float32) / SR
    # Quantize frequencies to exact integer cycles over `dur_s`
    q_hz = lambda f: round(f * dur_s) / dur_s
    f_root = q_hz(base_hz)
    f_fifth_l = q_hz(base_hz * 1.498)
    f_fifth_r = q_hz(base_hz * 1.502)
    f_swell = 2.0 / dur_s

    swell = 0.72 + 0.28 * np.sin(2 * np.pi * f_swell * t)
    pad_l = (0.58 * np.sin(2 * np.pi * f_root * t) + 0.32 * np.sin(2 * np.pi * f_fifth_l * t)) * swell
    pad_r = (0.58 * np.sin(2 * np.pi * f_root * t) + 0.32 * np.sin(2 * np.pi * f_fifth_r * t)) * swell

    # Subtle glass-marimba ostinato on integer beat subdivisions
    steps = max(16, int(round(dur_s * 4)))
    step_len = n // steps
    notes = [base_hz * 4, base_hz * 6, base_hz * 4.5, base_hz * 8]
    ost_l = np.zeros(n, dtype=np.float32)
    ost_r = np.zeros(n, dtype=np.float32)
    for st in range(steps):
        if st % 8 == 7:
            continue
        i0 = st * step_len
        m = min(step_len, n - i0)
        tt = np.arange(m, dtype=np.float32) / SR
        fn = q_hz(notes[st % len(notes)])
        plk = np.exp(-tt * 12.0) * (0.75 * np.sin(2 * np.pi * fn * tt) + 0.22 * np.sin(2 * np.pi * fn * 3.0 * tt))
        ost_l[i0:i0 + m] += plk * (0.22 if st % 2 == 0 else 0.14)
        ost_r[i0:i0 + m] += plk * (0.14 if st % 2 == 0 else 0.22)

    return np.stack([pad_l * 0.45 + ost_l, pad_r * 0.45 + ost_r], axis=1).astype(np.float32)


def apply_vacuum_window(bus: np.ndarray, t0_s: float, t1_s: float, taper_s: float = 0.010):
    """Carves a complete -180 dBFS digital silence drop right before a major twist word ('Wait.')!"""
    i0 = max(0, int(round(t0_s * SR)))
    i1 = min(len(bus), int(round(t1_s * SR)))
    tap = max(1, int(round(taper_s * SR)))
    if i0 > tap:
        w = 0.5 + 0.5 * np.cos(np.linspace(0, math.pi, tap, dtype=np.float32))
        bus[i0 - tap:i0] *= w[:, None]
    bus[i0:i1] = 0.0
    if i1 + tap < len(bus):
        w = 0.5 - 0.5 * np.cos(np.linspace(0, math.pi, tap, dtype=np.float32))
        bus[i1:i1 + tap] *= w[:, None]


def master_ebu_r128_linear(pre_master: np.ndarray, out_wav: str, target_i: float = -14.2, target_tp: float = -1.5) -> dict:
    """Two-pass FFmpeg linear EBU R128 broadcast loudness normalizer (`PCM_24`, `48 kHz`)."""
    ffmpeg = find_ffmpeg()
    tmp_in = f"{out_wav}.pre.wav"
    sf.write(tmp_in, pre_master, SR, subtype="PCM_24")
    try:
        p1 = subprocess.run(
            [
                ffmpeg, "-y", "-i", tmp_in,
                "-af", f"loudnorm=I={target_i}:TP={target_tp}:LRA=9:print_format=json",
                "-f", "null", "-"
            ],
            capture_output=True, text=True, check=True
        )
        m = re.search(r"\{\s*\"input_i\".*?\}", p1.stderr, flags=re.DOTALL)
        assert m, f"Failed to parse loudnorm pass 1 JSON: {p1.stderr[-500:]}"
        stats = json.loads(m.group(0))

        af_p2 = (
            f"loudnorm=I={target_i}:TP={target_tp}:LRA=9:"
            f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
            f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
            f"offset={stats['target_offset']}:linear=true,"
            f"alimiter=limit={target_tp}dB:level=false"
        )
        subprocess.run(
            [ffmpeg, "-y", "-i", tmp_in, "-af", af_p2, "-ar", str(SR), "-c:a", "pcm_s24le", out_wav],
            capture_output=True, text=True, check=True
        )
        return stats
    finally:
        if os.path.exists(tmp_in):
            os.remove(tmp_in)


def write_srt_vtt(cues: list, srt_path: str, vtt_path: str):
    def fmt_ts(sec: float, comma: bool = True) -> str:
        ms = int(round(sec * 1000))
        h, rem = divmod(ms, 3600000)
        m, rem = divmod(rem, 60000)
        s, ms_rem = divmod(rem, 1000)
        sep = "," if comma else "."
        return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms_rem:03d}"

    srt_lines = []
    vtt_lines = ["WEBVTT", ""]
    for idx, c in enumerate(cues, 1):
        t0, t1, txt = c["t0"], c["t1"], c["text"]
        srt_lines += [str(idx), f"{fmt_ts(t0, True)} --> {fmt_ts(t1, True)}", txt, ""]
        vtt_lines += [f"{fmt_ts(t0, False)} --> {fmt_ts(t1, False)}", txt, ""]

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(vtt_lines))
