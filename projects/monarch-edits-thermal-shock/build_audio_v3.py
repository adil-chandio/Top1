#!/usr/bin/env python3
"""
THERMAL SHOCK V3 "TABAHI" — Monarch Edits IMAX Sound Design Engine (36.000s = 1,080 frames @ 30fps).
Layers:
  1. Sub-braaams (D1 36.71 / D#2 43.65 / F1 41.20) on hook, pour, shatter, science, CTA
  2. Water pour foley: bandpass noise stream + bubble blips + splash modal impact
  3. Heat sizzle crackle, X-ray laser sweeps, Nolan chronometer ticks (accelerating)
  4. Pre-crack glass plinks (modal glass modes + sub), 190ms trailer VACUUM before SHATTER
  5. SHATTER: glass modal impact + braam + whiteout whoosh + 2.4s sub-drop + debris plinks
  6. Integer-cycle phase-locked dark-cinema score (drone + Zimmer ostinato), vacuum-masked
  7. Two-pass FFmpeg EBU R128 linear mastering (-14.2 LUFS / -1.5 dBTP, 48 kHz 24-bit) + SRT/VTT
"""
import glob
import json
import math
import os
import subprocess
import numpy as np
from scipy import signal

SR = 48000
FPS = 30
DUR_S = 36.0
N_SAMPLES = SR * 36  # 1,728,000 exact samples

ROOT = "/home/z/my-project/work/top1"
TMP_DIR = "/tmp/thermal_v3"
PROJ_DIR = os.path.join(ROOT, "projects/monarch-edits-thermal-shock")
EXPORT_DIR = os.path.join(ROOT, "exports/thermal-v3")
def _find_ffmpeg():
    for pat in (
        "/tmp/py/imageio_ffmpeg/binaries/ffmpeg*",
        "/home/z/.venv/lib/python3.12/site-packages/imageio_ffmpeg/binaries/ffmpeg*",
    ):
        m = glob.glob(pat)
        if m:
            return m[0]
    return "ffmpeg"

FFMPEG = _find_ffmpeg()

for d in (TMP_DIR, EXPORT_DIR):
    os.makedirs(d, exist_ok=True)

rng = np.random.default_rng(9137)

# ---------------------------------------------------------------- synth kit

def fade_io(clip, fi_s=0.012, fo_s=0.03):
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

def place(buf, clip, start_s, gain=1.0, pan=0.0):
    if clip.ndim == 1:
        clip = np.stack([clip, clip], axis=1)
    idx = int(round(start_s * SR))
    gl = gain * math.cos((pan + 1.0) * math.pi * 0.25) * 1.4142
    gr = gain * math.sin((pan + 1.0) * math.pi * 0.25) * 1.4142
    if idx >= N_SAMPLES or idx + len(clip) <= 0:
        return
    c0 = max(0, -idx)
    b0 = max(0, idx)
    L = min(len(clip) - c0, N_SAMPLES - b0)
    if L <= 0:
        return
    buf[b0:b0 + L, 0] += clip[c0:c0 + L, 0] * gl
    buf[b0:b0 + L, 1] += clip[c0:c0 + L, 1] * gr

def synth_imax_braam(dur_s=1.45, root_hz=36.71):
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

def synth_vacuum_suction(dur_s=0.92, seed=6003):
    r = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    f_inst = 95.0 + 1350.0 * (u ** 3.2)
    ph = 2 * np.pi * np.cumsum(f_inst) / SR
    b, a = signal.butter(2, [280 / (SR * 0.5), 4800 / (SR * 0.5)], btype="bandpass")
    whoosh = signal.lfilter(b, a, r.standard_normal(n).astype(np.float32))
    s = (0.55 * np.sin(ph) + 0.45 * whoosh) * (u ** 2.6)
    s /= (np.max(np.abs(s)) + 1e-9)
    choke = int(0.006 * SR)
    s[-choke:] *= np.linspace(1.0, 0.0, choke, dtype=np.float32)
    return np.stack([s, np.roll(s, 12)], axis=1).astype(np.float32)

def synth_whoosh(dur_s=0.55, f0=2200.0, f1=320.0, seed=11):
    r = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    f_inst = f0 * np.exp(-u * 3.0) + f1
    ph = 2 * np.pi * np.cumsum(f_inst) / SR
    b, a = signal.butter(2, [300 / (SR * 0.5), 5200 / (SR * 0.5)], btype="bandpass")
    nz = signal.lfilter(b, a, r.standard_normal(n).astype(np.float32))
    s = (0.45 * np.sin(ph) + 0.55 * nz) * np.sin(np.pi * u) ** 1.2
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 10)], axis=1), 0.02, 0.10)

def synth_chronometer_ticks(dur_s, rate_hz=8.0):
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

def synth_laser_sweep(dur_s=0.85):
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

def synth_modal_impact(dur_s=0.85, modes=((1140.0, 32.0), (2490.0, 48.0), (3870.0, 65.0)), sub_hz=84.0, seed=9001):
    r = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sub = 1.15 * np.exp(-t * 16.0) * np.sin(2 * np.pi * (sub_hz * np.exp(-t * 7.0) + 38.0) * t)
    metal = sum(0.35 * np.exp(-t * dec) * np.sin(2 * np.pi * freq * t) for freq, dec in modes)
    trans = 0.75 * np.exp(-t * 360.0) * r.standard_normal(n).astype(np.float32)
    s = (sub + metal + trans).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 9)], axis=1), 0.002, 0.10)

def synth_sub_drop(dur_s=2.4, f_start=72.0, f_end=24.0):
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    f_inst = f_start * np.exp(-u * 2.1) + f_end
    ph = 2 * np.pi * np.cumsum(f_inst) / SR
    s = np.sin(ph) * (0.35 + 0.65 * (1 - u)) * np.exp(-u * 1.15)
    s += 0.22 * np.sin(2 * np.pi * f_inst * 1.5 * t) * np.exp(-u * 2.2)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, s], axis=1).astype(np.float32), 0.01, 0.30)

def synth_water_pour(dur_s=3.4, seed=77):
    """Continuous pour: falling bandpass noise + resonant 'water' tone + bubble blips."""
    r = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    # hiss bed: lowpass noise ~1.2k with slight downward tilt
    b, a = signal.butter(2, [520 / (SR * 0.5), 2100 / (SR * 0.5)], btype="bandpass")
    hiss = signal.lfilter(b, a, r.standard_normal(n).astype(np.float32))
    hiss *= (0.55 + 0.45 * np.sin(np.pi * u)) * np.exp(-u * 0.35)
    # bubble blips: rising-pitch sine pings
    s = hiss.copy()
    for k in range(26):
        bi = int(r.uniform(0.04, dur_s - 0.10) * SR)
        m = int(0.035 * SR)
        tt = np.arange(m, dtype=np.float32) / SR
        f0 = r.uniform(700, 2300)
        blip = np.exp(-tt * 130.0) * np.sin(2 * np.pi * (f0 + f0 * 2.2 * tt / 0.035) * tt)
        L = min(m, n - bi)
        s[bi:bi + L] += blip[:L] * r.uniform(0.30, 0.75)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 8)], axis=1), 0.05, 0.16)

def synth_sizzle(dur_s, seed=411):
    """Heat sizzle crackle: sparse impulses + soft high band."""
    r = np.random.default_rng(seed)
    n = int(dur_s * SR)
    out = np.zeros(n, dtype=np.float32)
    b, a = signal.butter(2, [3000 / (SR * 0.5), 9000 / (SR * 0.5)], btype="bandpass")
    bed = signal.lfilter(b, a, r.standard_normal(n).astype(np.float32)) * 0.16
    out += bed
    for _ in range(int(dur_s * 46)):
        ci = int(r.uniform(0, n - 500))
        ct = np.arange(420, dtype=np.float32) / SR
        out[ci:ci + 420] += r.uniform(0.20, 0.80) * np.exp(-ct * 300.0) * r.standard_normal(420).astype(np.float32)
    out /= (np.max(np.abs(out)) + 1e-9)
    return fade_io(np.stack([out, np.roll(out, 11)], axis=1), 0.08, 0.14)

def synth_glass_tick(seed=31):
    r = np.random.default_rng(seed)
    n = int(0.12 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    s = np.exp(-t * 520.0) * (0.8 * np.sin(2 * np.pi * r.uniform(2800, 4200) * t) + 0.3 * np.sin(2 * np.pi * 8600 * t))
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, s], axis=1), 0.001, 0.02)

# ---------------------------------------------------------------- foley bus

foley_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)

# S1 HOOK [0.00..2.20]
place(foley_bus, synth_imax_braam(1.30, 36.71), 0.14, gain=0.34)
place(foley_bus, synth_glass_tick(31), 0.44, gain=0.30, pan=0.22)
place(foley_bus, synth_glass_tick(87), 1.30, gain=0.22, pan=-0.18)

# S2 SETUP [2.20..4.40]
place(foley_bus, synth_whoosh(0.6, 1800, 280, 21), 2.24, gain=0.30, pan=-0.12)
place(foley_bus, synth_laser_sweep(0.8), 2.62, gain=0.22)
place(foley_bus, synth_imax_braam(1.15, 43.65), 2.70, gain=0.24)

# S3 GARAM [4.40..8.00]
place(foley_bus, synth_whoosh(0.5, 900, 2400, 33), 4.42, gain=0.24, pan=0.15)
place(foley_bus, synth_sizzle(3.5, 411), 4.60, gain=0.20)
place(foley_bus, synth_glass_tick(53), 6.10, gain=0.20, pan=0.10)
place(foley_bus, synth_imax_braam(1.05, 49.00), 6.30, gain=0.20)

# S4 POUR [8.00..11.60]
place(foley_bus, synth_whoosh(0.5, 2400, 500, 44), 7.98, gain=0.22, pan=0.0)
place(foley_bus, synth_water_pour(3.45, 77), 8.00, gain=0.42)
place(foley_bus, synth_modal_impact(0.5, modes=((980.0, 40.0), (2100.0, 55.0)), sub_hz=95.0, seed=771), 8.14, gain=0.30)
place(foley_bus, synth_glass_tick(91), 9.40, gain=0.16, pan=-0.22)
place(foley_bus, synth_glass_tick(17), 10.60, gain=0.16, pan=0.22)

# S5 STRESS [11.60..15.20]
place(foley_bus, synth_laser_sweep(0.9), 11.62, gain=0.28)
place(foley_bus, synth_imax_braam(1.20, 36.71), 11.70, gain=0.26)
place(foley_bus, synth_chronometer_ticks(2.10, 8.0), 11.90, gain=0.13)
place(foley_bus, synth_chronometer_ticks(1.00, 12.0), 14.05, gain=0.15)  # ends 15.05, before vacuum
place(foley_bus, synth_modal_impact(0.42, seed=3131), 13.18, gain=0.26, pan=-0.14)
place(foley_bus, synth_modal_impact(0.46, seed=3232), 14.00, gain=0.34, pan=0.10)
place(foley_bus, synth_modal_impact(0.24, seed=3333), 14.84, gain=0.44, pan=0.0)  # tail ends 15.08
place(foley_bus, synth_vacuum_suction(3.40, 6003), 11.80, gain=0.40)  # ends exactly 15.20 -> SHATTER

# S6 SHATTER [15.20..17.40]
place(foley_bus, synth_modal_impact(1.15, modes=((1140.0, 26.0), (2490.0, 38.0), (3870.0, 52.0)), sub_hz=62.0, seed=9137), 15.20, gain=0.62)
place(foley_bus, synth_imax_braam(1.45, 36.71), 15.21, gain=0.40)
place(foley_bus, synth_whoosh(0.7, 5200, 300, 55), 15.20, gain=0.46)
place(foley_bus, synth_sub_drop(2.4, 72, 24), 15.24, gain=0.52)

# S7 DEBRIS [17.40..21.20]
for i, (ts, g, p) in enumerate([
    (15.92, 0.20, -0.30), (16.30, 0.16, 0.26), (16.72, 0.14, -0.10), (17.30, 0.13, 0.18),
    (17.85, 0.12, -0.24), (18.40, 0.10, 0.10), (19.05, 0.09, -0.16),
]):
    place(foley_bus, synth_modal_impact(0.28, modes=((1350.0, 55.0), (2700.0, 70.0)), sub_hz=120.0, seed=4000 + i), ts, gain=g, pan=p)
place(foley_bus, synth_imax_braam(1.10, 43.65), 19.60, gain=0.20)

# S8 SCIENCE [21.20..27.00]
place(foley_bus, synth_whoosh(0.6, 2000, 320, 66), 21.22, gain=0.26, pan=0.0)
place(foley_bus, synth_laser_sweep(0.9), 21.50, gain=0.24)
place(foley_bus, synth_imax_braam(1.15, 41.20), 21.60, gain=0.24)
place(foley_bus, synth_chronometer_ticks(2.2, 6.5), 22.60, gain=0.10)
place(foley_bus, synth_glass_tick(71), 24.30, gain=0.18, pan=0.15)

# S9 RULE [27.00..31.00]
place(foley_bus, synth_whoosh(0.6, 1600, 260, 77), 27.02, gain=0.24, pan=-0.10)
place(foley_bus, synth_imax_braam(1.10, 36.71), 27.10, gain=0.22)
place(foley_bus, synth_glass_tick(37), 28.40, gain=0.16, pan=0.12)

# S10 CTA [31.00..36.00]
place(foley_bus, synth_whoosh(0.9, 1200, 200, 88), 31.02, gain=0.30, pan=0.0)
place(foley_bus, synth_imax_braam(1.30, 32.70), 31.20, gain=0.28)
place(foley_bus, synth_sub_drop(1.8, 60, 26), 34.30, gain=0.30)

# ---------------------------------------------------------------- score bus

music_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)
t_full = np.arange(N_SAMPLES, dtype=np.float32) / SR

def int_freq(target_hz):
    return round(target_hz * DUR_S) / DUR_S

f_d1 = int_freq(36.71)
f_d2 = int_freq(73.42)
f_a2 = int_freq(110.00)
f_f3 = int_freq(174.61)

swell = 0.65 + 0.35 * np.cos(2 * np.pi * (5.0 / DUR_S) * t_full)
drone_l = (
    0.48 * np.sin(2 * np.pi * f_d1 * t_full)
    + 0.34 * np.sin(2 * np.pi * f_d2 * t_full)
    + 0.20 * np.sin(2 * np.pi * int_freq(109.85) * t_full)
    + 0.11 * np.sin(2 * np.pi * f_f3 * t_full)
) * swell
drone_r = (
    0.48 * np.sin(2 * np.pi * f_d1 * t_full)
    + 0.34 * np.sin(2 * np.pi * f_d2 * t_full)
    + 0.20 * np.sin(2 * np.pi * int_freq(110.15) * t_full)
    + 0.11 * np.sin(2 * np.pi * int_freq(174.80) * t_full)
) * swell
music_bus[:, 0] += drone_l * 0.150
music_bus[:, 1] += drone_r * 0.150

# Zimmer ostinato: 0.25s steps = 144 integer steps over 36.000s
notes_ost = [293.66, 349.23, 440.00, 466.16, 440.00, 349.23, 329.63, 293.66]
step_s = 0.25
for st in range(int(DUR_S / step_s)):
    if st % 8 == 7:
        continue
    t0_st = st * step_s
    # silence inside the trailer vacuum (15.10..15.28) and final resolve tail (34.6+)
    if 15.02 <= t0_st <= 15.30:
        continue
    if t0_st >= 34.60:
        continue
    m = int(0.24 * SR)
    mt = np.arange(m, dtype=np.float32) / SR
    fn = notes_ost[st % len(notes_ost)]
    if t0_st < 8.0:
        vel = 0.14
    elif t0_st < 15.2:
        vel = 0.20
    elif t0_st < 21.2:
        vel = 0.16
    else:
        vel = 0.21
    plk = vel * (np.exp(-mt * 15.0) * np.sin(2 * np.pi * fn * mt) + 0.25 * np.exp(-mt * 34.0) * np.sin(2 * np.pi * (fn * 2.0) * mt))
    pan_st = 0.36 * math.sin(st * 1.1)
    idx = int(round(t0_st * SR))
    L = min(m, N_SAMPLES - idx)
    music_bus[idx:idx + L, 0] += plk[:L] * (0.5 - 0.5 * pan_st)
    music_bus[idx:idx + L, 1] += plk[:L] * (0.5 + 0.5 * pan_st)

# ---------------------------------------------------------------- vacuum window

vac_mask = np.ones(N_SAMPLES, dtype=np.float32)
v0, v1, v2, v3 = int(15.055 * SR), int(15.095 * SR), int(15.205 * SR), int(15.255 * SR)
vac_mask[v0:v1] = np.linspace(1.0, 0.0, v1 - v0, dtype=np.float32)
vac_mask[v1:v2] = 0.0
vac_mask[v2:v3] = np.linspace(0.0, 1.0, v3 - v2, dtype=np.float32)

music_vac = music_bus * vac_mask[:, None]
foley_vac = foley_bus * vac_mask[:, None]

raw_mix = foley_vac * 1.0 + music_vac * 0.96
raw_mix = np.clip(raw_mix, -0.99, 0.99)

# ---------------------------------------------------------------- mastering

pre_path = os.path.join(TMP_DIR, "pre_thermal_v3.wav")
sf_ok = True
try:
    import soundfile as sf
    sf.write(pre_path, raw_mix, SR, subtype="PCM_24")
except Exception as e:
    print("soundfile missing:", e)
    sf_ok = False

master_out = os.path.join(TMP_DIR, "master_mix.wav")

def master():
    p1 = subprocess.run(
        [FFMPEG, "-y", "-i", pre_path, "-af", "loudnorm=I=-14.2:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    j_txt = p1.stderr[p1.stderr.rfind("{"):p1.stderr.rfind("}") + 1]
    ln = json.loads(j_txt)
    af2 = (
        f"loudnorm=I=-14.2:TP=-1.5:LRA=9:measured_I={ln['input_i']}:"
        f"measured_TP={ln['input_tp']}:measured_LRA={ln['input_lra']}:"
        f"measured_thresh={ln['input_thresh']}:offset={ln['target_offset']}:linear=true,"
        f"alimiter=limit=-1.5dB:level=false"
    )
    subprocess.run(
        [FFMPEG, "-y", "-i", pre_path, "-af", af2, "-ar", "48000", "-c:a", "pcm_s24le", master_out],
        check=True, capture_output=True,
    )
    ver = subprocess.run(
        [FFMPEG, "-i", master_out, "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    tail = [l.strip() for l in ver.stderr.splitlines() if any(k in l for k in ("I:", "LRA:", "Peak:")) and "TARGET:-23" not in l]
    print("=== THERMAL V3 TABAHI MASTER EBU R128 ===")
    for l in tail[-5:]:
        print(" ", l)

master()

# vacuum silence QA
import numpy as _np
pcm = subprocess.run(
    [FFMPEG, "-v", "error", "-ss", "15.10", "-to", "15.20", "-i", master_out,
     "-vn", "-f", "f32le", "-ac", "2", "-ar", "48000", "-"],
    capture_output=True, check=True,
).stdout
audio = _np.frombuffer(pcm, dtype=np.float32).reshape((-1, 2))
vac_db = float(20.0 * _np.log10(float(_np.sqrt(_np.mean(audio ** 2))) + 1e-9))
print(f"Vacuum window RMS: {vac_db:.1f} dBFS (target < -48)")

# ---------------------------------------------------------------- captions

CAPS = [
    (0.30, 2.20, "GARAM SHEESHA - THANDA PAANI = TABAAHI?"),
    (2.30, 4.35, "36 SECOND MEIN POORI SCIENCE - CHALO!"),
    (4.45, 7.95, "450 DEGREE GARAM - SHEESHA LOHE JITNA TEZ"),
    (8.05, 11.55, "THANDA PAANI GIRA - SEEDHA GARAM SHEESHE PAR"),
    (11.65, 13.55, "BAHAR THANDA - ANDAR ABHI 450!"),
    (13.65, 15.10, "STRESS 97% - SHEESHA AB SAHN nahi KARTA"),
    (15.22, 17.35, "THERMAL SHOCK! - 1 SECOND MEIN PHATA!"),
    (17.45, 21.15, "TIKONE KE TUKDE - HAWA MEIN UDD GAYE"),
    (21.25, 24.10, "BAHAR WALI DEEWAR TEZI SE SUKADTI HAI"),
    (24.20, 26.95, "ANDAR ABHI BHI PHAILA HUA HAI"),
    (27.05, 30.95, "BOROSILICATE AARAM SE SIKUDTA - NAHI PHATA"),
    (31.05, 35.80, "AGLA EXPERIMENT? FOLLOW - MONARCH EDITS"),
]

def fmt_srt(sec):
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

srt_out, vtt_out = [], ["WEBVTT", ""]
for i, (t0, t1, txt) in enumerate(CAPS, 1):
    srt_out += [str(i), f"{fmt_srt(t0)} --> {fmt_srt(t1)}", txt, ""]
    vtt_out += [f"{fmt_srt(t0).replace(',', '.')} --> {fmt_srt(t1).replace(',', '.')}", txt, ""]

open(os.path.join(EXPORT_DIR, "Thermal-Shock-V3-Captions.srt"), "w").write("\n".join(srt_out))
open(os.path.join(EXPORT_DIR, "Thermal-Shock-V3-Captions.vtt"), "w").write("\n".join(vtt_out))

print(f"WROTE: {master_out}")
print(f"WROTE: {EXPORT_DIR}/Thermal-Shock-V3-Captions.srt/.vtt")
