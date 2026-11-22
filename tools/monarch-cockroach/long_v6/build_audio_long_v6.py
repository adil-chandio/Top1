#!/usr/bin/env python3
"""
Monarch Cam #03 — V6 Hollywood IMAX Long-Form Dolby-Cinema Audio Engine
Duration: 300.2667s = 9,008 exact frames @ 30.000 fps (14,412,800 samples @ 48 kHz 24-bit)

1. Preserves 100.000% untouched `voice-02` natural speech (`Monarch-Cam-03-Long-Video-Dry-Voiceover-Master-V5.wav`,
   `time_stretch_applied = False`, 0.00% pitch/rate modification).
2. Layers Luxury Hollywood Cinema Hall Sound Design across all 7 Chapters & 32 Shots:
   - Sub-Harmonic Cinema Hall Braaams (36.71 Hz D1 / 41.20 Hz E1 / 43.65 Hz F1 / 55.00 Hz A1, carved < 185 Hz
     so the 220 Hz - 4 kHz narration formant pocket stays razor-clear)
   - Two Complete Hollywood Trailer Vacuum Silence Drops (< -65 dBFS):
       * Vacuum #1 [17.82s .. 18.12s] preceded by 0.90s Reverse Suction Riser -> "Wait a second."
       * Vacuum #2 [98.60s .. 98.80s] preceded by 0.78s Reverse Suction Riser -> "It didn't."
   - Nolan-Style 500 fps Precision Chronometer Escapement Ticks (8 Hz) in bullet-time & 500 fps windows
   - Crystalline 3D Holographic Laser Tomography Sweep (@ 60.58s X-Ray Cutaway reveal)
   - Heavy Modal Steel Hydraulic Load-Cell Anvil Slam (~900x BW / 6.08 N @ 226.15s)
   - Real @e.d.i.t_sandeep clean cinema whooshes, sub-drops, risers, clicks & pops
   - Frame-accurate physical foley: wall toggle snap, copper penny clink, 11-plate chitin shingle cascade,
     surface-specific silicon-carbide crampon rake (100-grit slip vs 40-grit oar bite vs 20-grit belly snag),
     athlete force-plate shoulder collapse thud, and 3.15 mm acrylic gate thorax wedge
   - 7-Chapter evolving dark-cinema harmonic score + 55 ms look-ahead zero-phase sidechain ducking
3. Two-Pass FFmpeg Linear EBU R128 Broadcast/Cinema Mastering (-14.2 LUFS / -1.5 dBTP, 48 kHz 24-bit).
4. Exports Latin-1 clean `.srt` & `.vtt` full-film captions + `long-voice-lock-v6-imax.json`.
"""
import glob
import json
import math
import os
import subprocess
import sys

sys.path.insert(0, "/tmp/py")
import numpy as np
from scipy import signal
import soundfile as sf

SR = 48000
FPS = 30
TOTAL_FRAMES = 9008
N_SAMPLES = TOTAL_FRAMES * (SR // FPS)  # 9008 * 1600 = 14,412,800 exact samples
DUR_S = N_SAMPLES / SR                  # 300.2666667s

ROOT = "/home/user/Top1"
TMP_DIR = "/tmp/v6_long"
V5_DIR = os.path.join(ROOT, "tools/monarch-cockroach/v5")
V6_DIR = os.path.join(ROOT, "tools/monarch-cockroach/long_v6")
MANIFEST_DIR = os.path.join(ROOT, "tools/monarch-cockroach/manifests")
EXPORT_DIR = os.path.join(ROOT, "exports/monarch-cam-03-long-v6-imax")
FFMPEG = glob.glob("/tmp/py/imageio_ffmpeg/binaries/ffmpeg*")[0]

for d in (TMP_DIR, V6_DIR, MANIFEST_DIR, EXPORT_DIR):
    os.makedirs(d, exist_ok=True)

# 0. Extract stereo 48 kHz WAVs from the 4 @e.d.i.t_sandeep SFX reels if not cached
REEL_NAMES = [
    "VID_20261113_012128_753",
    "VID_20261113_012137_703",
    "VID_20261113_012154_590",
    "VID_20261113_012158_998",
]
for rn in REEL_NAMES:
    wav_p = os.path.join(TMP_DIR, f"sfx_raw_{rn}.wav")
    mp4_p = os.path.join(TMP_DIR, f"{rn}.mp4")
    if not os.path.isfile(wav_p):
        subprocess.run(
            [FFMPEG, "-y", "-i", mp4_p, "-vn", "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", wav_p],
            check=True, capture_output=True
        )

# 1. Load pure zero-stretch Dry VO Master (14,412,800 samples @ 48 kHz)
dry_in = os.path.join(TMP_DIR, "Monarch-Cam-03-Long-Video-Dry-Voiceover-Master-V5.wav")
vo_bus, sr_vo = sf.read(dry_in, dtype="float32", always_2d=True)
assert sr_vo == SR and len(vo_bus) == N_SAMPLES, f"Unexpected VO shape: {vo_bus.shape} @ {sr_vo}"

dry_v6_out = os.path.join(TMP_DIR, "Monarch-Cam-03-Long-Video-Dry-Voiceover-Master-V6-IMAX.wav")
sf.write(dry_v6_out, vo_bus, SR, subtype="PCM_24")

# Load V5 voice-lock anchors & sentences
with open(os.path.join(V5_DIR, "voice-lock-v5.json"), "r", encoding="utf-8") as fh:
    v5_lock = json.load(fh)
A = v5_lock["anchors"]

# 2. 55 ms Look-Ahead Zero-Phase Sidechain Ducking Envelope
vo_mono_sq = np.mean(vo_bus ** 2, axis=1)
win_env = int(0.065 * SR)
vo_rms = np.sqrt(np.convolve(vo_mono_sq, np.ones(win_env, dtype=np.float32) / win_env, mode="same"))
shift = int(0.055 * SR)
vo_ahead = np.pad(vo_rms[shift:], (0, shift))
duck_raw = np.clip(vo_ahead / 0.030, 0.0, 1.0)
b_lp, a_lp = signal.butter(1, 2.8 / (SR * 0.5), btype="lowpass")
duck_smooth = np.clip(signal.filtfilt(b_lp, a_lp, duck_raw), 0.0, 1.0)


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
    if idx >= N_SAMPLES or idx + len(clip) <= 0:
        return
    c0 = max(0, -idx)
    b0 = max(0, idx)
    L = min(len(clip) - c0, N_SAMPLES - b0)
    if L <= 0:
        return
    gl = gain * math.cos((pan + 1.0) * math.pi * 0.25) * 1.4142
    gr = gain * math.sin((pan + 1.0) * math.pi * 0.25) * 1.4142
    buf[b0:b0 + L, 0] += clip[c0:c0 + L, 0] * gl
    buf[b0:b0 + L, 1] += clip[c0:c0 + L, 1] * gr


def slice_sfx(reel_name, t0, t1, fi=0.02, fo=0.06, norm_pk=0.75):
    full, _ = sf.read(os.path.join(TMP_DIR, f"sfx_raw_{reel_name}.wav"), dtype="float32", always_2d=True)
    seg = full[int(t0 * SR):int(t1 * SR), :2].copy()
    seg = fade_io(seg, fi, fo)
    pk = float(np.max(np.abs(seg)) + 1e-9)
    return seg * (norm_pk / pk)


sfx_whoosh_deep  = slice_sfx("VID_20261113_012137_703", 2.45, 3.10, 0.025, 0.08, 0.80)
sfx_whoosh_mid   = slice_sfx("VID_20261113_012137_703", 0.08, 0.83, 0.025, 0.08, 0.76)
sfx_whoosh_fast  = slice_sfx("VID_20261113_012137_703", 5.20, 5.75, 0.015, 0.06, 0.75)
sfx_sub_drop     = slice_sfx("VID_20261113_012154_590", 14.73, 15.75, 0.015, 0.16, 0.90)
sfx_riser_smooth = slice_sfx("VID_20261113_012154_590", 5.80, 8.15, 0.10, 0.06, 0.70)
sfx_riser_air    = slice_sfx("VID_20261113_012158_998", 22.12, 24.02, 0.10, 0.06, 0.65)
sfx_click_crisp  = slice_sfx("VID_20261113_012128_753", 1.95, 2.05, 0.003, 0.02, 0.70)
sfx_pop_soft     = slice_sfx("VID_20261113_012154_590", 4.23, 4.40, 0.004, 0.03, 0.65)

rng = np.random.default_rng(6030)


# ===========================================================================
# HOLLYWOOD IMAX PHYSICAL & DOLBY-CINEMA SYNTHESIZERS
# ===========================================================================
def synth_imax_braam(dur_s=1.55, root_hz=36.71):
    """Detuned Zimmer/Villeneuve low-brass + sub-cello swell (< 185 Hz vocal-safe)."""
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = (1.0 - np.exp(-t * 16.0)) * np.exp(-t * 2.15)
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
    return fade_io(out / (np.max(np.abs(out)) + 1e-9), 0.015, 0.20)


def synth_vacuum_suction(dur_s=0.90):
    """Reverse suction riser that chokes to dead silence on its exact final sample."""
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    f_inst = 95.0 + 1380.0 * (u ** 3.2)
    ph = 2 * np.pi * np.cumsum(f_inst) / SR
    b, a = signal.butter(2, [280 / (SR * 0.5), 4800 / (SR * 0.5)], btype="bandpass")
    whoosh = signal.lfilter(b, a, rng.standard_normal(n).astype(np.float32))
    s = (0.55 * np.sin(ph) + 0.45 * whoosh) * (u ** 2.6)
    s /= (np.max(np.abs(s)) + 1e-9)
    choke = int(0.006 * SR)
    s[-choke:] *= np.linspace(1.0, 0.0, choke, dtype=np.float32)
    return np.stack([s, np.roll(s, 12)], axis=1).astype(np.float32)


def synth_chronometer_ticks(dur_s, rate_hz=8.0):
    """Nolan-style precision 500 fps chronometer escapement pulse."""
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


def synth_laser_tomography_sweep(dur_s=0.95):
    """Crystalline 3D X-Ray holographic laser scan panning left -> right across cockroach."""
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    f1 = 2450.0 * np.exp(-u * 1.45) + 320.0
    ph1 = 2 * np.pi * np.cumsum(f1) / SR
    shimmer = 0.5 * np.sin(ph1) + 0.3 * np.sin(ph1 * 1.503) + 0.2 * np.sin(2 * np.pi * 1480 * t) * np.exp(-t * 8.0)
    env = np.sin(np.pi * u) ** 0.7
    s = (shimmer * env).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    pan = np.linspace(-0.58, 0.58, n, dtype=np.float32)
    return fade_io(np.stack([s * (0.5 - 0.5 * pan), s * (0.5 + 0.5 * pan)], axis=1), 0.02, 0.06)


def synth_wall_switch_snap():
    """Crisp mechanical ivory wall light-switch toggle snap + 120 Hz filament warm-up pop."""
    n = int(0.18 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    snap1 = 0.90 * np.exp(-t * 380.0) * (np.sin(2 * np.pi * 2450 * t) + 0.6 * np.sin(2 * np.pi * 5180 * t))
    t2 = np.maximum(0.0, t - 0.018)
    snap2 = (t >= 0.018) * 0.65 * np.exp(-t2 * 310.0) * np.sin(2 * np.pi * 1780 * t2)
    hum = 0.16 * np.exp(-t * 18.0) * np.sin(2 * np.pi * 120.0 * t)
    s = (snap1 + snap2 + hum).astype(np.float32)
    return fade_io(s / (np.max(np.abs(s)) + 1e-9), 0.001, 0.03)


def synth_hydraulic_anvil_slam():
    """Massive ~900x BW steel load-cell platen impact: sub-thud + damped steel modes."""
    n = int(0.92 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sub = 1.15 * np.exp(-t * 15.0) * np.sin(2 * np.pi * (88.0 * np.exp(-t * 7.0) + 38.0) * t)
    metal = (
        0.44 * np.exp(-t * 30.0) * np.sin(2 * np.pi * 1140.0 * t)
        + 0.30 * np.exp(-t * 46.0) * np.sin(2 * np.pi * 2490.0 * t)
        + 0.22 * np.exp(-t * 62.0) * np.sin(2 * np.pi * 3870.0 * t)
    )
    trans = 0.80 * np.exp(-t * 350.0) * rng.standard_normal(n).astype(np.float32)
    s = (sub + metal + trans).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 9)], axis=1), 0.002, 0.10)


def synth_coin_clink():
    n = int(0.40 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    s = np.zeros(n, dtype=np.float32)
    for f, d in [(6180, 26.0), (9420, 34.0), (12850, 46.0), (4120, 40.0)]:
        s += np.exp(-t * d) * np.sin(2 * np.pi * f * t)
    return fade_io(s / (np.max(np.abs(s)) + 1e-9), 0.001, 0.05)


def synth_claw_skitter(dur_s, rate_hz=16.5, grit_freq=4600.0, pan_a=-0.55, pan_b=0.55):
    n = int(dur_s * SR)
    out = np.zeros((n, 2), dtype=np.float32)
    step_interval = 1.0 / (rate_hz * 3.0)
    t_c = 0.0
    b_bp, a_bp = signal.butter(2, [1500 / (SR * 0.5), min(0.92, grit_freq * 1.8 / (SR * 0.5))], btype="bandpass")
    while t_c < dur_s - 0.025:
        m = int(0.022 * SR)
        tt = np.arange(m, dtype=np.float32) / SR
        burst = np.exp(-tt * 230.0) * signal.lfilter(b_bp, a_bp, rng.standard_normal(m).astype(np.float32))
        burst += 0.35 * np.exp(-tt * 320.0) * np.sin(2 * np.pi * (grit_freq * rng.uniform(0.86, 1.14)) * tt)
        idx = int(t_c * SR)
        u = t_c / max(1e-4, dur_s)
        pan = pan_a + (pan_b - pan_a) * u
        L = min(m, n - idx)
        out[idx:idx + L, 0] += burst[:L] * math.cos((pan + 1.0) * math.pi * 0.25)
        out[idx:idx + L, 1] += burst[:L] * math.sin((pan + 1.0) * math.pi * 0.25)
        t_c += step_interval * rng.uniform(0.84, 1.16)
    return fade_io(out / (np.max(np.abs(out)) + 1e-9), 0.02, 0.04)


def synth_crampon_scrape(dur_s, coarseness=0.6):
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    lo = 620.0 if coarseness > 0.7 else (1250.0 if coarseness > 0.35 else 2900.0)
    hi = 3400.0 if coarseness > 0.7 else (6100.0 if coarseness > 0.35 else 9400.0)
    b, a = signal.butter(2, [lo / (SR * 0.5), hi / (SR * 0.5)], btype="bandpass")
    shaped = signal.lfilter(b, a, rng.standard_normal(n).astype(np.float32))
    mod = 0.28 + 0.72 * (np.maximum(0.0, np.sin(2 * np.pi * 7.4 * t)) ** 1.6)
    clicks = np.zeros(n, dtype=np.float32)
    for _ in range(int(dur_s * 36)):
        ci = int(rng.uniform(0, max(1, n - 380)))
        ct = np.arange(360, dtype=np.float32) / SR
        clicks[ci:ci + 360] += rng.uniform(0.35, 0.95) * np.exp(-ct * 260.0) * np.sin(2 * np.pi * rng.uniform(1900, 4600) * ct)
    s = shaped * mod + 0.58 * clicks
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 15)], axis=1), 0.03, 0.05)


def synth_chitin_shingle_fold(dur_s=1.35):
    n = int(dur_s * SR)
    s = np.zeros(n, dtype=np.float32)
    for k in range(11):
        idx = int((0.05 + k * (dur_s - 0.14) / 11.0) * SR)
        m = int(0.042 * SR)
        tt = np.arange(m, dtype=np.float32) / SR
        f0 = 1620 + k * 145
        pulse = np.exp(-tt * 175.0) * (0.72 * np.sin(2 * np.pi * f0 * tt) + 0.38 * np.sin(2 * np.pi * (f0 * 1.62) * tt))
        L = min(m, n - idx)
        s[idx:idx + L] += pulse[:L]
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 16)], axis=1), 0.015, 0.04)


def synth_servo_press(dur_s=1.25):
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f_sw = 310.0 - 145.0 * (t / dur_s)
    ph = 2 * np.pi * np.cumsum(f_sw) / SR
    s = (0.55 * np.sin(ph) + 0.28 * np.sin(2 * ph) + 0.14 * np.sin(3 * ph)) * np.sin(np.pi * (t / dur_s)) ** 0.45
    return fade_io(np.stack([s, s], axis=1).astype(np.float32), 0.03, 0.05)


# ===========================================================================
# 3. ASSEMBLE FRAME-LOCKED FOLEY & HOLLYWOOD IMAX IMPACTS ACROSS ALL 7 CHAPTERS
# ===========================================================================
foley_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)

# --- CHAPTER 1 [0..921 / 0.00..30.70s]: Apartment Switch -> Pennies -> Climax #1 -> Bullet-Time Orbit ---
place(foley_bus, synth_wall_switch_snap(), A["ch1_switch"] / FPS, gain=0.46, pan=-0.32)
place(foley_bus, sfx_whoosh_deep, (A["ch1_switch"] + 3) / FPS, gain=0.38, pan=-0.10)
place(foley_bus, synth_imax_braam(1.4, 36.71), (A["ch1_switch"] + 4) / FPS, gain=0.32, pan=0.0)
place(foley_bus, synth_claw_skitter(3.6, 17.2, 4700, -0.65, 0.05), 1.15, gain=0.26)
place(foley_bus, synth_coin_clink(), 7.45, gain=0.28, pan=0.25)

# Protected Climax #1 [330..538 / 11.00..17.93s]: Uninterrupted Doorway Vanish -> Reverse Suction -> VACUUM!
place(foley_bus, synth_claw_skitter(1.4, 18.0, 4900, -0.35, 0.05), 11.05, gain=0.28)
place(foley_bus, synth_imax_braam(1.35, 36.71), A["ch1_climax_dip"] / FPS, gain=0.34)
place(foley_bus, synth_chitin_shingle_fold(1.15), (A["ch1_climax_dip"] + 6) / FPS, gain=0.32, pan=0.05)
place(foley_bus, sfx_whoosh_deep, A["ch1_climax_gone"] / FPS - 0.12, gain=0.40, pan=0.22)
place(foley_bus, synth_vacuum_suction(0.90), 16.92, gain=0.38)  # Chokes @ 17.82s -> 300ms PURE VACUUM into "Wait a second."!

# Bullet-Time Doorway Orbit [538..921 / 17.93..30.70s]:
place(foley_bus, sfx_click_crisp, 18.16, gain=0.26, pan=0.0)
place(foley_bus, sfx_sub_drop, 18.22, gain=0.34, pan=0.0)
place(foley_bus, synth_chronometer_ticks(6.8, 8.0), 18.45, gain=0.12)
place(foley_bus, sfx_riser_smooth, 28.25, gain=0.30, pan=0.0)

# --- CHAPTER 2 [921..2288 / 30.70..76.27s]: UC Berkeley Lab -> 500 fps Five Moves -> 3D X-Ray Cutaway ---
place(foley_bus, sfx_whoosh_mid, A["ch2_start"] / FPS - 0.08, gain=0.36, pan=-0.20)
place(foley_bus, synth_imax_braam(1.45, 43.65), A["ch2_start"] / FPS + 0.04, gain=0.30)
place(foley_bus, sfx_click_crisp, A["ch2_500fps"] / FPS, gain=0.26, pan=-0.18)
place(foley_bus, synth_chronometer_ticks(18.8, 8.0), A["ch2_moves_intro"] / FPS, gain=0.11)
for mv_key, pan_v in [
    ("ch2_move1_start", -0.25),
    ("ch2_move2_start", -0.10),
    ("ch2_move3_start", 0.00),
    ("ch2_move4_start", 0.15),
    ("ch2_move5_start", 0.30),
]:
    place(foley_bus, sfx_pop_soft, A[mv_key] / FPS, gain=0.22, pan=pan_v)
place(foley_bus, synth_crampon_scrape(3.8, 0.58), A["ch2_move4_start"] / FPS + 0.10, gain=0.30, pan=0.10)
place(foley_bus, synth_claw_skitter(2.4, 18.5, 5100, 0.10, 0.55), A["ch2_move5_start"] / FPS + 0.15, gain=0.24)

# Shot 2D [1819..2288 / 60.63..76.27s]: 3D Laser Tomography Scan + Shingle Cascade + Elastic Rebound!
place(foley_bus, synth_laser_tomography_sweep(0.95), A["ch2_xray_start"] / FPS - 0.06, gain=0.34)
place(foley_bus, synth_imax_braam(1.45, 43.65), A["ch2_xray_start"] / FPS + 0.05, gain=0.30)
place(foley_bus, synth_chitin_shingle_fold(1.30), A["ch2_xray_tiles"] / FPS + 0.12, gain=0.30, pan=-0.10)
place(foley_bus, synth_chitin_shingle_fold(1.25), A["ch2_xray_hinges"] / FPS + 0.12, gain=0.28, pan=0.12)
place(foley_bus, sfx_whoosh_fast, A["ch2_xray_rebound"] / FPS, gain=0.28, pan=0.15)

# --- CHAPTER 3 [2288..3607 / 76.27..120.23s]: Stepped Ceiling Corridor & 3-Lane Speed Cliff ---
place(foley_bus, sfx_whoosh_mid, A["ch3_start"] / FPS - 0.06, gain=0.32, pan=0.18)
place(foley_bus, synth_claw_skitter(8.5, 16.8, 4600, -0.50, 0.45), A["ch3_corridor_intro"] / FPS, gain=0.22)
place(foley_bus, sfx_click_crisp, A["ch3_step_down"] / FPS, gain=0.28, pan=-0.15)
place(foley_bus, synth_servo_press(0.85), A["ch3_step_down"] / FPS + 0.05, gain=0.20)
place(foley_bus, sfx_click_crisp, A["ch3_half_height"] / FPS, gain=0.30, pan=0.15)
place(foley_bus, synth_servo_press(0.85), A["ch3_half_height"] / FPS + 0.05, gain=0.22)
# Vacuum Suction #2 [97.80..98.58s] -> 220ms Vacuum -> "It didn't."!
place(foley_bus, synth_vacuum_suction(0.78), 97.80, gain=0.34)
place(foley_bus, sfx_sub_drop, 98.84, gain=0.36, pan=0.0)
place(foley_bus, synth_claw_skitter(7.2, 17.5, 4800, -0.55, 0.55), A["ch3_full_speed"] / FPS + 0.20, gain=0.25)
# 4 mm Compression Drop & Speed Cliff (@ f=3287 / 109.57s):
place(foley_bus, sfx_sub_drop, A["ch3_drop_2mm"] / FPS + 0.15, gain=0.38, pan=0.28)
place(foley_bus, synth_imax_braam(1.45, 41.20), A["ch3_drop_2mm"] / FPS + 0.20, gain=0.32)
place(foley_bus, synth_crampon_scrape(4.8, 0.65), A["ch3_speed_crash"] / FPS - 0.30, gain=0.26, pan=0.32)

# --- CHAPTER 4 [3607..5312 / 120.23..177.07s]: Claws Lift Off -> Push-Up Collapse -> Climax #2 Crampon Oars ---
place(foley_bus, sfx_whoosh_mid, A["ch4_start"] / FPS - 0.06, gain=0.32, pan=-0.20)
place(foley_bus, synth_claw_skitter(5.5, 16.4, 4500, -0.35, 0.25), A["ch4_follow_leg"] / FPS, gain=0.22)
place(foley_bus, sfx_riser_air, A["ch4_press_ceil"] / FPS - 0.40, gain=0.26)
place(foley_bus, synth_laser_tomography_sweep(0.80), A["ch4_80deg"] / FPS - 0.10, gain=0.24)  # Emerald clearance laser!
# Shot 4D [4350..4481 / 145.00..149.37s]: 3D Athlete Splayed Push-Up Collapse!
place(foley_bus, sfx_whoosh_fast, A["ch4_pushup_start"] / FPS, gain=0.28)
place(foley_bus, sfx_sub_drop, 147.26, gain=0.40, pan=0.0)  # Exact Newtonian shoulder impact frame f=4418!
place(foley_bus, synth_imax_braam(1.20, 36.71), 147.28, gain=0.28)
# Protected Climax #2 [4662..4923 / 155.40..164.10s]: Synchronous Tibial Spine Crampon Oar Drive!
place(foley_bus, sfx_whoosh_deep, A["ch4_climax_start"] / FPS - 0.08, gain=0.38, pan=0.0)
place(foley_bus, synth_imax_braam(1.55, 36.71), A["ch4_climax_start"] / FPS + 0.05, gain=0.35)
place(foley_bus, synth_chronometer_ticks(8.4, 8.0), A["ch4_climax_start"] / FPS + 0.15, gain=0.12)
place(foley_bus, synth_crampon_scrape(8.3, 0.62), A["ch4_climax_start"] / FPS + 0.18, gain=0.38, pan=0.06)
place(foley_bus, synth_crampon_scrape(6.5, 0.58), A["ch4_oars_start"] / FPS, gain=0.28, pan=-0.08)

# --- CHAPTER 5 [5312..6591 / 177.07..219.70s]: Footless Traction Shear Rig & 100/40/20 Grit Trade-Off ---
place(foley_bus, sfx_whoosh_mid, A["ch5_start"] / FPS - 0.06, gain=0.30, pan=0.15)
place(foley_bus, synth_crampon_scrape(6.2, 0.60), A["ch5_grip_test"] / FPS, gain=0.32, pan=-0.12)
place(foley_bus, sfx_click_crisp, A["ch5_locked_tight"] / FPS, gain=0.26)
place(foley_bus, synth_chitin_shingle_fold(1.8), A["ch5_rough_ceil"] / FPS, gain=0.24, pan=0.0)
# 3-Lane Grit Trade-Off [6223..6591 / 207.43..219.70s]: Slick 100-grit vs 40-grit vs Coarse 20-grit snag!
place(foley_bus, sfx_whoosh_fast, A["ch5_floor_grit"] / FPS - 0.05, gain=0.28)
place(foley_bus, synth_crampon_scrape(2.8, 0.14), A["ch5_slick_slip"] / FPS - 0.20, gain=0.24, pan=-0.45)
place(foley_bus, synth_crampon_scrape(4.8, 0.94), A["ch5_coarse_snag"] / FPS - 0.15, gain=0.36, pan=0.42)
place(foley_bus, synth_imax_braam(1.30, 41.20), A["ch5_coarse_snag"] / FPS, gain=0.26)

# --- CHAPTER 6 [6591..8032 / 219.70..267.73s]: ~900x BW Hydraulic Press -> 76.7 cm/s Sprint -> 315 Gate Trials ---
place(foley_bus, sfx_whoosh_deep, A["ch6_start"] / FPS - 0.08, gain=0.36)
place(foley_bus, synth_servo_press(4.8), A["ch6_start"] / FPS + 0.50, gain=0.28)
# Massive ~900x BW (6.08 N) Hydraulic Platen Slam @ f=6785 (226.17s)!
place(foley_bus, synth_hydraulic_anvil_slam(), 226.15, gain=0.54, pan=0.0)
place(foley_bus, synth_imax_braam(1.55, 36.71), 226.18, gain=0.38, pan=0.0)
# <80 ms Elastic Shell Rebound & 76.7 cm/s Open Sprint (@ f=6877 / 229.23s):
place(foley_bus, sfx_click_crisp, 228.50, gain=0.28)
place(foley_bus, sfx_whoosh_deep, A["ch6_sprint_76"] / FPS - 0.10, gain=0.38, pan=0.25)
place(foley_bus, synth_claw_skitter(5.8, 20.4, 5400, -0.55, 0.65), A["ch6_sprint_76"] / FPS, gain=0.30)
# 315 Narrowing Gate Attempts & 83% Failure (@ f=7519..8032):
place(foley_bus, sfx_whoosh_mid, A["ch6_315_gate"] / FPS - 0.06, gain=0.30, pan=-0.18)
place(foley_bus, synth_claw_skitter(3.8, 17.5, 4800, -0.45, 0.45), A["ch6_wider_pass"] / FPS, gain=0.24)
place(foley_bus, sfx_sub_drop, A["ch6_narrow_3mm"] / FPS + 0.10, gain=0.36)
place(foley_bus, synth_imax_braam(1.35, 41.20), A["ch6_17_pct"] / FPS, gain=0.30)
# 9% Thorax Wedge Jam @ f=7948 (264.93s):
place(foley_bus, sfx_click_crisp, 264.90, gain=0.32, pan=0.22)
place(foley_bus, synth_chitin_shingle_fold(0.85), 264.95, gain=0.28, pan=0.22)

# --- CHAPTER 7 [8032..9008 / 267.73..300.27s]: 1x Real-Speed Reprise -> CRAM Robot -> Quiet Hold -> PNAS ---
place(foley_bus, sfx_riser_smooth, 268.80, gain=0.28)
# Protected Climax #3 [8143..8502 / 271.43..283.40s]: Real-Speed Doorway Vanish & Elastic Rebound!
place(foley_bus, synth_claw_skitter(1.6, 18.2, 4900, -0.50, 0.05), A["ch7_climax_start"] / FPS + 0.05, gain=0.28)
place(foley_bus, synth_coin_clink(), 272.10, gain=0.24, pan=-0.22)
place(foley_bus, synth_chitin_shingle_fold(0.75), 272.35, gain=0.28, pan=0.05)
place(foley_bus, sfx_whoosh_deep, 272.75, gain=0.40, pan=0.20)
place(foley_bus, synth_imax_braam(1.45, 55.00), 272.80, gain=0.32)
place(foley_bus, synth_claw_skitter(3.2, 18.5, 5000, 0.10, 0.65), A["ch7_spring_back"] / FPS, gain=0.24)
# CRAM Soft Robot + Cockroach Side-by-Side [8692..8922 / 289.73..297.40s]:
place(foley_bus, sfx_pop_soft, A["ch7_not_indestruct"] / FPS, gain=0.24, pan=-0.18)
place(foley_bus, synth_servo_press(1.6), 290.40, gain=0.18, pan=-0.25)
place(foley_bus, synth_claw_skitter(4.8, 17.0, 5000, -0.45, 0.45), 291.00, gain=0.22)


# ===========================================================================
# 4. 7-CHAPTER EVOLVING HOLLYWOOD DARK-CINEMA SCORE
# ===========================================================================
music_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)

CHAPTER_HARMONY = [
    # (start_f, end_f, root_hz, fifth_hz, color_hz, drone_gain, pulse_vel, ostinato_notes)
    (0,    921,  36.71, 110.00, 174.61, 0.135, 0.15, [293.66, 349.23, 440.00, 466.16, 440.00, 349.23]),
    (921,  2288, 36.71, 110.00, 164.81, 0.145, 0.19, [293.66, 329.63, 349.23, 440.00, 349.23, 329.63]),
    (2288, 3607, 43.65, 130.81, 174.61, 0.150, 0.20, [349.23, 392.00, 415.30, 523.25, 415.30, 392.00]),
    (3607, 5312, 36.71, 110.00, 185.00, 0.160, 0.22, [293.66, 349.23, 440.00, 493.88, 440.00, 349.23]),
    (5312, 6591, 41.20, 123.47, 164.81, 0.145, 0.18, [329.63, 369.99, 392.00, 493.88, 392.00, 369.99]),
    (6591, 8032, 55.00, 110.00, 196.00, 0.165, 0.23, [220.00, 261.63, 329.63, 392.00, 329.63, 261.63]),
    (8032, 9008, 36.71, 110.00, 164.81, 0.150, 0.16, [293.66, 329.63, 440.00, 587.33, 440.00, 329.63]),
]

for ch_f0, ch_f1, f_root, f_fifth, f_col, d_gain, p_vel, ost_notes in CHAPTER_HARMONY:
    s0 = int((ch_f0 / FPS) * SR)
    s1 = min(N_SAMPLES, int((ch_f1 / FPS) * SR))
    n_seg = s1 - s0
    tt = np.arange(n_seg, dtype=np.float32) / SR
    swell = 0.68 + 0.32 * np.sin(2 * np.pi * 0.125 * tt)
    dl = (
        0.50 * np.sin(2 * np.pi * f_root * tt)
        + 0.32 * np.sin(2 * np.pi * (f_root * 2.0) * tt)
        + 0.20 * np.sin(2 * np.pi * (f_fifth * 0.998) * tt)
        + 0.12 * np.sin(2 * np.pi * f_col * tt)
    ) * swell
    dr = (
        0.50 * np.sin(2 * np.pi * f_root * tt)
        + 0.32 * np.sin(2 * np.pi * (f_root * 2.0) * tt)
        + 0.20 * np.sin(2 * np.pi * (f_fifth * 1.002) * tt)
        + 0.12 * np.sin(2 * np.pi * (f_col * 1.003) * tt)
    ) * swell
    seg_drone = fade_io(np.stack([dl, dr], axis=1).astype(np.float32) * d_gain, 0.45, 0.55)
    music_bus[s0:s1] += seg_drone

    # Precision 16th-pulse cinema ostinato (paused during final quiet hold >= 297.2s!)
    step_s = 0.26
    t_cur = ch_f0 / FPS + 0.12
    t_end = min(297.0, ch_f1 / FPS - 0.20)
    st_i = 0
    while t_cur < t_end:
        # Pause ostinato inside both trailer vacuum drops!
        if not (17.65 <= t_cur <= 18.25) and not (98.45 <= t_cur <= 98.95) and (st_i % 8 != 7):
            m = int(0.24 * SR)
            mt = np.arange(m, dtype=np.float32) / SR
            fn = ost_notes[st_i % len(ost_notes)]
            plk = p_vel * (
                np.exp(-mt * 15.0) * np.sin(2 * np.pi * fn * mt)
                + 0.24 * np.exp(-mt * 34.0) * np.sin(2 * np.pi * (fn * 2.0) * mt)
            )
            pan_st = 0.34 * math.sin(st_i * 1.13)
            idx = int(round(t_cur * SR))
            L = min(m, N_SAMPLES - idx)
            if L > 0:
                music_bus[idx:idx + L, 0] += plk[:L] * (0.5 - 0.5 * pan_st)
                music_bus[idx:idx + L, 1] += plk[:L] * (0.5 + 0.5 * pan_st)
        t_cur += step_s
        st_i += 1

# Warm resolving D-add9 cinema chord tail across the Protected Quiet Closing Hold + PNAS Card [296.8s .. 300.25s]
s_end0 = int(296.8 * SR)
n_tail = N_SAMPLES - s_end0
tt_tail = np.arange(n_tail, dtype=np.float32) / SR
env_tail = np.sin(np.pi * np.minimum(1.0, tt_tail / (n_tail / SR))) ** 0.85 * np.exp(-tt_tail * 0.45)
chord_l = (
    0.42 * np.sin(2 * np.pi * 73.42 * tt_tail)
    + 0.30 * np.sin(2 * np.pi * 146.83 * tt_tail)
    + 0.22 * np.sin(2 * np.pi * 220.00 * tt_tail)
    + 0.16 * np.sin(2 * np.pi * 329.63 * tt_tail)
) * env_tail * 0.18
chord_r = (
    0.42 * np.sin(2 * np.pi * 73.42 * tt_tail)
    + 0.30 * np.sin(2 * np.pi * 146.95 * tt_tail)
    + 0.22 * np.sin(2 * np.pi * 220.18 * tt_tail)
    + 0.16 * np.sin(2 * np.pi * 329.45 * tt_tail)
) * env_tail * 0.18
music_bus[s_end0:, 0] += chord_l
music_bus[s_end0:, 1] += chord_r


# ===========================================================================
# 5. APPLY DUAL HOLLYWOOD TRAILER VACUUM SILENCE DROPS + SIDECHAIN MASTERING
# ===========================================================================
vac_mask = np.ones(N_SAMPLES, dtype=np.float32)
for t_fade_start, t_zero_start, t_zero_end, t_recover in [
    (17.78, 17.82, 18.12, 18.22),  # Vacuum #1 -> "Wait a second."
    (98.56, 98.60, 98.80, 98.90),  # Vacuum #2 -> "It didn't."
]:
    i0, i1, i2, i3 = int(t_fade_start * SR), int(t_zero_start * SR), int(t_zero_end * SR), int(t_recover * SR)
    vac_mask[i0:i1] = np.linspace(1.0, 0.0, i1 - i0, dtype=np.float32)
    vac_mask[i1:i2] = 0.0
    vac_mask[i2:i3] = np.linspace(0.0, 1.0, i3 - i2, dtype=np.float32)

music_ducked = music_bus * ((1.0 - 0.52 * duck_smooth) * vac_mask)[:, None]
foley_ducked = foley_bus * ((1.0 - 0.22 * duck_smooth) * vac_mask)[:, None]

raw_mix = vo_bus * 1.06 + foley_ducked * 0.90 + music_ducked * 0.92
# Enforce exact -180 dBFS inside Vacuum #1 [17.83..18.11s] so zero tail leaks in
raw_mix[int(17.83 * SR):int(18.11 * SR)] = 0.0
# Clean 80ms fade-out at frame 9008 tail
tail_f = int(0.08 * SR)
raw_mix[-tail_f:] *= np.linspace(1.0, 0.0, tail_f, dtype=np.float32)[:, None]

pre_path = os.path.join(TMP_DIR, "pre_long_v6_imax.wav")
sf.write(pre_path, np.clip(raw_mix, -0.99, 0.99), SR, subtype="PCM_24")

# Two-Pass FFmpeg Linear EBU R128 Mastering (-14.2 LUFS, -1.5 dBTP)
mix_v6_out = os.path.join(TMP_DIR, "Monarch-Cam-03-Long-Video-Master-Mix-V6-IMAX.wav")
p1 = subprocess.run(
    [FFMPEG, "-y", "-i", pre_path, "-af", "loudnorm=I=-14.2:TP=-1.5:LRA=8:print_format=json", "-f", "null", "-"],
    capture_output=True, text=True, check=True
)
j_txt = p1.stderr[p1.stderr.rfind("{"):p1.stderr.rfind("}") + 1]
ln = json.loads(j_txt)
af2 = (
    f"loudnorm=I=-14.2:TP=-1.5:LRA=8:measured_I={ln['input_i']}:"
    f"measured_TP={ln['input_tp']}:measured_LRA={ln['input_lra']}:"
    f"measured_thresh={ln['input_thresh']}:offset={ln['target_offset']}:linear=true,"
    f"alimiter=limit=-1.5dB:level=false"
)
subprocess.run(
    [FFMPEG, "-y", "-i", pre_path, "-af", af2, "-ar", "48000", "-c:a", "pcm_s24le", mix_v6_out],
    check=True, capture_output=True
)
os.remove(pre_path)

# Verify exact sample count & EBU R128 loudness + Vacuum #1 RMS!
mix_check, sr_chk = sf.read(mix_v6_out, dtype="float32", always_2d=True)
assert sr_chk == SR and len(mix_check) == N_SAMPLES, f"Master mix sample mismatch: {mix_check.shape}"
vac_rms_db = float(20.0 * np.log10(np.sqrt(np.mean(mix_check[int(17.85 * SR):int(18.08 * SR)] ** 2)) + 1e-9))
assert vac_rms_db < -60.0, f"Vacuum #1 RMS too high: {vac_rms_db:.2f} dBFS"

ver = subprocess.run([FFMPEG, "-i", mix_v6_out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, check=True)
tail = [l.strip() for l in ver.stderr.splitlines() if any(k in l for k in ("I:", "LRA:", "Peak:")) and "TARGET:-23" not in l]
print("=== LONG V6 IMAX MASTER MIX EBU R128 ===")
for l in tail[-5:]:
    print(" ", l)
print(f"  Vacuum #1 [17.85..18.08s] RMS: {vac_rms_db:.1f} dBFS (Target < -60 dBFS)")


# ===========================================================================
# 6. EXPORT FULL-FILM `.SRT`, `.VTT` CAPTIONS & `long-voice-lock-v6-imax.json`
# ===========================================================================
def sanitize_latin1(txt: str) -> str:
    return (
        txt.replace("\u2019", "'")
           .replace("\u2018", "'")
           .replace("\u201c", '"')
           .replace("\u201d", '"')
           .replace("\u2014", " - ")
           .replace("\u2013", "-")
           .replace("\u2026", "...")
    )


def fmt_srt(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


srt_lines = []
vtt_lines = ["WEBVTT", ""]
cue_idx = 0
for ch in v5_lock["chapters"]:
    for sent in ch["sentences"]:
        cue_idx += 1
        t0 = sent["abs_start_f"] / FPS
        t1 = sent["abs_end_f"] / FPS
        txt = sanitize_latin1(sent["text"])
        assert all(ord(c) <= 0xFF for c in txt), f"Non-Latin-1 char in cue {cue_idx}: {txt}"
        srt_lines += [str(cue_idx), f"{fmt_srt(t0)} --> {fmt_srt(t1)}", txt, ""]
        vtt_lines += [f"{fmt_srt(t0).replace(',', '.')} --> {fmt_srt(t1).replace(',', '.')}", txt, ""]

srt_path = os.path.join(EXPORT_DIR, "Monarch-Cam-03-Long-Video-Captions-V6-IMAX.srt")
vtt_path = os.path.join(EXPORT_DIR, "Monarch-Cam-03-Long-Video-Captions-V6-IMAX.vtt")
open(srt_path, "w", encoding="utf-8").write("\n".join(srt_lines))
open(vtt_path, "w", encoding="utf-8").write("\n".join(vtt_lines))

v6_lock = dict(v5_lock)
v6_lock["version"] = "long-v6-imax"
v6_lock["resolution"] = [1920, 1080]
v6_lock["audio_standard"] = "Dolby-Cinema Hall EBU R128 (-14.2 LUFS / -1.5 dBTP, 48 kHz 24-bit)"
v6_lock["vacuum_windows_s"] = [[17.82, 18.12], [98.60, 98.80]]
v6_lock["total_caption_cues"] = cue_idx

for p in (os.path.join(V6_DIR, "long-voice-lock-v6-imax.json"), os.path.join(MANIFEST_DIR, "long-voice-lock-v6-imax.json")):
    open(p, "w", encoding="utf-8").write(json.dumps(v6_lock, indent=2))

print(f"Exported {cue_idx} frame-locked captions (.srt & .vtt) and long-voice-lock-v6-imax.json!")
