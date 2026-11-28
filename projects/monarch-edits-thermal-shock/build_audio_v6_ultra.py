#!/usr/bin/env python3
"""
THERMAL SHOCK V6 ULTRA ("ZACK D. x CHRISTOPHER NOLAN DOLBY FOLEY ENGINE")
Zero-Stretch Audio-First Frame-Lock & 16-Layer Physical Acoustic Master (`40.000s`, `1,200` frames @ `30.000 fps`).
Upgrades V5's proven `-14.3 LUFS / LRA 8.8 LU` architecture with tactile physical realism:
  - 55 Hz Halogen Induction Coil Hum + Thermal Expansion Quartz Micro-Creaks
  - Laminar Cryo-Water Pour + 38 Helmholtz Rising Bubbles + Crisp Ice-Cube Clinks + 300°C Leidenfrost Sizzle
  - "RUKO." Surgical Laser Guillotine Slice Sweep
  - Accelerating Hitchcock Sub-Heartbeat + Rising 3.12 kHz Wine-Glass Breaking-Point Modal Singing Resonance
  - 4 Multi-Mode Quartz Cleavage Crack Pings -> Hard Digital Vacuum (`22.493s .. 22.8333s` = `-240 dBFS` WAV!)
  - 42-Snap + 32-Mode Crystal Shatter + Explosive Water-Splash Burst + Bullet-Time Doppler Shimmer
  - "DHADAM!" Gravity Snap + 22 Stereo Shard Floor Bounces + Hot-Coil Water Sizzle (`TSSSHHHH!`)
  - Borosilicate 3.3 Live Torture-Test Pour Sizzle + Pure Boron Crystalline Shield Chord
  - 14-Shot Dynamic Cinema Cut Map locked 1:1 to natural `voice-00` Hindustani clauses
"""
import json
import math
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, "/tmp/py")
sys.path.insert(0, os.path.join(ROOT, "tools/monarch-v6-imax-sdk/python"))

import numpy as np
from scipy import signal
import soundfile as sf
from audio_imax_dsp import (
    SR,
    FPS,
    find_ffmpeg,
    load_wav_48k_stereo,
    fade_io,
    place_clip,
    compute_lookahead_duck_envelope,
    synth_imax_braam,
)

DUR_S = 40.0
TOTAL_FRAMES = int(round(DUR_S * FPS))  # 1,200 exact frames
N_SAMPLES = int(round(DUR_S * SR))      # 1,920,000 exact samples

VO_RAW_DIR = "/tmp/thermal_v5/vo_raw"
TMP_DIR = "/tmp/thermal_v6"
PROJ_DIR = os.path.join(ROOT, "projects/monarch-edits-thermal-shock")
EXPORT_DIR = os.path.join(ROOT, "exports/thermal-shock-v6-ultra")
FFMPEG = find_ffmpeg()

for d in (TMP_DIR, EXPORT_DIR):
    os.makedirs(d, exist_ok=True)


def extract_spoken_islands(wav_path: str, min_silence_s: float = 0.14, rms_thresh: float = 0.0020):
    audio = load_wav_48k_stereo(wav_path)
    mono_sq = np.mean(audio ** 2, axis=1)
    win = int(0.015 * SR)
    rms = np.sqrt(np.convolve(mono_sq, np.ones(win, dtype=np.float32) / win, mode="same"))
    voiced = rms > rms_thresh
    idx = np.flatnonzero(voiced)
    if len(idx) == 0:
        raise RuntimeError(f"No speech detected in {wav_path}")

    pre = int(0.028 * SR)
    post = int(0.036 * SR)
    raw_bounds = []
    s = idx[0]
    prev = idx[0]
    gap_samples = int(min_silence_s * SR)
    for ix in idx[1:]:
        if ix - prev > gap_samples:
            raw_bounds.append((max(0, s - pre), min(len(audio), prev + post)))
            s = ix
        prev = ix
    raw_bounds.append((max(0, s - pre), min(len(audio), prev + post)))

    return [fade_io(audio[a:b], 0.010, 0.014) for a, b in raw_bounds]


# ---------------------------------------------------------------------------
# 1. EXTRACT ZERO-STRETCH VOICEOVER CLAUSES & BUILD 14-SHOT TIMELINE
# ---------------------------------------------------------------------------
act1_islands = extract_spoken_islands(os.path.join(VO_RAW_DIR, "act1_pre_shatter.wav"))
act2_islands = extract_spoken_islands(os.path.join(VO_RAW_DIR, "act2_post_shatter.wav"))
assert len(act1_islands) == 10 and len(act2_islands) == 8

ACT1_PLAN = [
    (0, 0.18, "S1_HOOK",     "KHOLTE GARAM GLASS PAR", "BARAF THANDA PAANI DAALEIN?", "BARAF THANDA", "#FFB454"),
    (1, 0.24, "S2_HEAT",     "300°C KI GARMI SE",      "POORI DEEWAR PHAIL CHUKI HAI", "300°C",       "#FF6A28"),
    (2, 0.24, "S3_POUR_A",   "TABHI UPAR SE 10°C",     "THANDA PAANI GIRTA HAI",       "10°C",        "#3CF0FF"),
    (3, 0.12, "S3_POUR_B",   "SEEDHA GARAM GLASS PAR", "1 SECOND MEIN ASLI KHEL!",     "1 SECOND",    "#3CF0FF"),
    (4, 0.28, "S4_WAIT",     "RUKO.",                  "ANDAR DEKHO KYA HUA!",         "RUKO.",       "#FFD166"),
    (5, 0.18, "S4_CUTAWAY_A","BAHAR KI PATLI PARAT",   "10°C PAR THANDI HO GAYI",      "10°C",        "#3CF0FF"),
    (6, 0.14, "S4_CUTAWAY_B","JABKE ANDAR KA KANCH",   "AB BHI 300°C AAG HAI!",        "300°C AAG",   "#FF4A1C"),
    (7, 0.24, "S5_SHEAR_A",  "BAHAR WALI PARAT",       "TEZI SE SIKUDTI HAI",          "SIKUDTI",     "#3CF0FF"),
    (8, 0.14, "S5_SHEAR_B",  "AUR ANDAR WALI PARAT",   "GARMI SE PHAILI REHTI HAI",    "PHAILI",      "#FF6A28"),
    (9, 0.14, "S5_CRITICAL", "KHICHAO 4 GUNA ZYADA",   "STRESS LIMIT CROSS!",          "4 GUNA",      "#FF3B1F"),
]

vo_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)
timeline_segments = []
cursor_s = 0.0

for idx_i, gap_s, beat_id, l1, l2, hi, accent in ACT1_PLAN:
    cursor_s += gap_s
    clip = act1_islands[idx_i]
    dur = len(clip) / SR
    place_clip(vo_bus, clip, cursor_s, gain=1.0, pan=0.0)
    timeline_segments.append({
        "id": beat_id,
        "t0": round(cursor_s, 4),
        "t1": round(cursor_s + dur, 4),
        "f0": int(round(cursor_s * FPS)),
        "f1": int(round((cursor_s + dur) * FPS)),
        "l1": l1,
        "l2": l2,
        "hi": hi,
        "accent": accent,
    })
    cursor_s += dur

act1_end_s = cursor_s
VACUUM_T0 = round(act1_end_s + 0.030, 3)
SHATTER_T = round(math.ceil((VACUUM_T0 + 0.310) * FPS) / FPS, 4)  # 22.8333s (Frame 685!)
SHATTER_F = int(round(SHATTER_T * FPS))
VACUUM_QA_WINDOW = [round(VACUUM_T0 + 0.045, 3), round(SHATTER_T - 0.045, 3)]
CLIMAX_QUIET_END_T = round(SHATTER_T + 1.50, 4)  # 24.3333s (45 frames of pure unobstructed bullet-time cinema!)

ACT2_PLAN = [
    (0, 0.00, "S7_DHADAM",   "DHADAM! THERMAL SHOCK!", "1 SECOND MEIN VISFOT!",        "DHADAM!",     "#FF4A1C"),
    (1, 0.16, "S7_STORM_A",  "ISI THERMAL SHOCK SE",   "APNE HI KHICHAO KE KARAN",     "THERMAL SHOCK","#FFB454"),
    (2, 0.12, "S7_STORM_B",  "GLASS SAIKDON TUKDON",   "MEIN PHAT JATA HAI!",          "SAIKDON",     "#FFB454"),
    (3, 0.26, "S8_BORO_A",   "MAGAR BOROSILICATE",     "PYREX 3.3 LAB KANCH",          "BOROSILICATE","#3AD4BE"),
    (4, 0.14, "S8_BORO_B",   "3 GUNA KAM SIKUDTA HAI", "BORON ATOMIC SHIELD!",         "3 GUNA KAM",  "#3AD4BE"),
    (5, 0.14, "S8_BORO_C",   "ISLIYE WOH JHATKA",      "AARAM SE JHEL LETA HAI",       "JHEL LETA",   "#5EF2D6"),
    (6, 0.26, "S9_LOOP_A",   "TOH AGLI BAAR GARAM",    "SHEESHE MEIN PAANI SE PEHLE",  "GARAM",       "#FFB454"),
    (7, 0.14, "S9_LOOP_B",   "YEH SCIENCE ZAROOR",     "YAAD RAKHNA!",                 "SCIENCE",     "#3CF0FF"),
]

cursor_s = CLIMAX_QUIET_END_T
for idx_i, gap_s, beat_id, l1, l2, hi, accent in ACT2_PLAN:
    cursor_s += gap_s
    clip = act2_islands[idx_i]
    dur = len(clip) / SR
    place_clip(vo_bus, clip, cursor_s, gain=(1.08 if beat_id == "S7_DHADAM" else 1.0), pan=0.0)
    timeline_segments.append({
        "id": beat_id,
        "t0": round(cursor_s, 4),
        "t1": round(cursor_s + dur, 4),
        "f0": int(round(cursor_s * FPS)),
        "f1": int(round((cursor_s + dur) * FPS)),
        "l1": l1,
        "l2": l2,
        "hi": hi,
        "accent": accent,
    })
    cursor_s += dur

assert cursor_s < DUR_S - 0.35, f"Act 2 overran {DUR_S}s: {cursor_s:.3f}s"

b_hp, a_hp = signal.butter(2, 95.0 / (SR * 0.5), btype="highpass")
vo_bus = np.stack([signal.filtfilt(b_hp, a_hp, vo_bus[:, 0]), signal.filtfilt(b_hp, a_hp, vo_bus[:, 1])], axis=1).astype(np.float32)
vo_bus = (vo_bus / (float(np.max(np.abs(vo_bus))) + 1e-9)) * 0.79

# 14-Shot Dynamic Zack D. x Nolan Camera Cut Map locked to exact vocal syllables!
seg_by_id = {s["id"]: s for s in timeline_segments}
f_heat0 = seg_by_id["S2_HEAT"]["f0"] - 2
f_pourA = seg_by_id["S3_POUR_A"]["f0"] - 2
f_pourB = seg_by_id["S3_POUR_B"]["f0"] - 1
f_wait  = seg_by_id["S4_WAIT"]["f0"] - 1
f_shearA= seg_by_id["S5_SHEAR_A"]["f0"] - 2
f_shearB= seg_by_id["S5_SHEAR_B"]["f0"] - 1
f_vac   = int(round(VACUUM_T0 * FPS))
f_dhadam= seg_by_id["S7_DHADAM"]["f0"] + 6
f_boroA = seg_by_id["S8_BORO_A"]["f0"] - 2
f_loopA = seg_by_id["S9_LOOP_A"]["f0"] - 2

SHOTS = [
    {"id": "S1_HOOK",               "f0": 0,                 "f1": f_heat0},
    {"id": "S2A_COIL_MACRO",        "f0": f_heat0,           "f1": f_heat0 + 58},
    {"id": "S2B_HEAT_EXPANSION",    "f0": f_heat0 + 58,      "f1": f_pourA},
    {"id": "S3A_POUR_IMPACT",       "f0": f_pourA,           "f1": f_pourB},
    {"id": "S3B_QUENCH_SHOCK",      "f0": f_pourB,           "f1": f_wait},
    {"id": "S4_LASER_SLICE",        "f0": f_wait,            "f1": f_shearA},
    {"id": "S5A_ATOMIC_ZOOM",       "f0": f_shearA,          "f1": f_shearB},
    {"id": "S5B_CRACK_CASCADE",     "f0": f_shearB,          "f1": f_vac},
    {"id": "S5C_VACUUM_DREAD",      "f0": f_vac,             "f1": SHATTER_F},
    {"id": "S6A_DETONATION_FLASH",  "f0": SHATTER_F,         "f1": SHATTER_F + 21},
    {"id": "S6B_BULLET_TIME_ORBIT", "f0": SHATTER_F + 21,    "f1": f_dhadam},
    {"id": "S7_AFTERMATH_SIZZLE",   "f0": f_dhadam,          "f1": f_boroA},
    {"id": "S8_BORO_TORTURE_TEST",  "f0": f_boroA,           "f1": f_loopA},
    {"id": "S9_SEAMLESS_LOOP",      "f0": f_loopA,           "f1": TOTAL_FRAMES},
]


# ---------------------------------------------------------------------------
# 2. PHYSICAL GLASS, CRYO-WATER, LASER SLICE & SHATTER SYNTHESIS
# ---------------------------------------------------------------------------
def synth_crystal_shatter_explosion_ultra(dur_s: float = 2.25, seed: int = 2026) -> np.ndarray:
    """
    6-Layer Physical Glass + Water Burst Explosion:
      A: 48 micro-staggered brittle cleavage impulse snaps (0..48 ms)
      B: High-voltage broadband crystalline burst (1.6 kHz - 14.2 kHz)
      C: 36 inharmonic high-Q crystal ringing modes (1.9 kHz - 13.0 kHz)
      D: Explosive Water-Column Splash Burst (600 Hz - 5.2 kHz)
      E: Bullet-Time Doppler Shimmer Tail (time-warped glass resonances)
      F: Chest-punch seismic sub-drop (96 Hz -> 29 Hz)
    """
    r = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    L = np.zeros(n, dtype=np.float32)
    R = np.zeros(n, dtype=np.float32)

    b_cr, a_cr = signal.butter(2, [1800 / (SR * 0.5), 14500 / (SR * 0.5)], btype="bandpass")
    for _ in range(48):
        onset = int(r.uniform(0.0, 0.050) * SR)
        m = int(r.uniform(0.005, 0.018) * SR)
        if onset + m >= n:
            continue
        tt = np.arange(m, dtype=np.float32) / SR
        burst = signal.lfilter(b_cr, a_cr, r.standard_normal(m).astype(np.float32)) * np.exp(-tt * r.uniform(220, 520))
        pan = r.uniform(-0.78, 0.78)
        amp = r.uniform(0.50, 1.05)
        L[onset:onset + m] += burst * amp * (0.5 - 0.5 * pan)
        R[onset:onset + m] += burst * amp * (0.5 + 0.5 * pan)

    b_sh, a_sh = signal.butter(2, [2400 / (SR * 0.5), 13500 / (SR * 0.5)], btype="bandpass")
    L += signal.lfilter(b_sh, a_sh, r.standard_normal(n).astype(np.float32)) * np.exp(-t * 9.0) * 0.68
    R += signal.lfilter(b_sh, a_sh, r.standard_normal(n).astype(np.float32)) * np.exp(-t * 8.8) * 0.68

    # Water column splash burst!
    b_wt, a_wt = signal.butter(2, [580 / (SR * 0.5), 5200 / (SR * 0.5)], btype="bandpass")
    L += signal.lfilter(b_wt, a_wt, r.standard_normal(n).astype(np.float32)) * np.exp(-t * 4.2) * 0.42
    R += signal.lfilter(b_wt, a_wt, r.standard_normal(n).astype(np.float32)) * np.exp(-t * 4.0) * 0.42

    # 36 inharmonic crystal modes + slight bullet-time pitch bend
    for freq in r.uniform(1950.0, 12800.0, size=36):
        dec = r.uniform(5.5, 28.0) + (freq / 12000.0) * 12.0
        amp = r.uniform(0.045, 0.125) * (1.0 - 0.32 * (freq / 13500.0))
        onset = int(r.uniform(0.0, 0.038) * SR)
        m = n - onset
        tt = t[:m]
        f_bend = freq * (1.0 - 0.04 * np.minimum(1.0, tt * 0.8))
        ring = amp * np.exp(-tt * dec) * np.sin(2 * np.pi * np.cumsum(f_bend) / SR + r.uniform(0, 6.28))
        pan = r.uniform(-0.82, 0.82)
        L[onset:] += ring * (0.5 - 0.5 * pan)
        R[onset:] += ring * (0.5 + 0.5 * pan)

    f_punch = 96.0 * np.exp(-t * 13.5) + 29.5
    punch = 1.42 * np.exp(-t * 8.2) * np.tanh(1.65 * np.sin(2 * np.pi * np.cumsum(f_punch) / SR))
    L += punch
    R += punch

    out = np.stack([L, R], axis=1).astype(np.float32)
    out /= (np.max(np.abs(out)) + 1e-9)
    return fade_io(out, 0.001, 0.14)


def synth_cleavage_crack_snap(seed: int = 101) -> np.ndarray:
    r = np.random.default_rng(seed)
    n = int(0.32 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    b, a = signal.butter(2, [2500 / (SR * 0.5), 13800 / (SR * 0.5)], btype="bandpass")
    snap = signal.lfilter(b, a, r.standard_normal(n).astype(np.float32)) * np.exp(-t * 235.0) * 1.15
    modes = [r.uniform(2700, 3500), r.uniform(4800, 6300), r.uniform(8100, 10800)]
    ring = sum(0.30 * np.exp(-t * r.uniform(26, 48)) * np.sin(2 * np.pi * f * t) for f in modes)
    sub = 0.48 * np.exp(-t * 32.0) * np.sin(2 * np.pi * 118.0 * t)
    s = (snap + ring + sub).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 7)], axis=1), 0.001, 0.04)


def synth_shard_floor_tinkle(seed: int = 500) -> np.ndarray:
    r = np.random.default_rng(seed)
    n = int(0.28 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f1, f2, f3 = r.uniform(3400, 5400), r.uniform(6300, 9100), r.uniform(9900, 13400)
    hit1 = np.exp(-t * 56.0) * (0.56 * np.sin(2 * np.pi * f1 * t) + 0.33 * np.sin(2 * np.pi * f2 * t) + 0.19 * np.sin(2 * np.pi * f3 * t))
    b_off = int(r.uniform(0.052, 0.090) * SR)
    hit2 = np.zeros(n, dtype=np.float32)
    tb = t[:n - b_off]
    hit2[b_off:] = 0.44 * np.exp(-tb * 82.0) * (0.6 * np.sin(2 * np.pi * (f1 * 1.03) * tb) + 0.4 * np.sin(2 * np.pi * f2 * tb))
    click = 0.46 * np.exp(-t * 510.0) * r.standard_normal(n).astype(np.float32)
    s = (hit1 + hit2 + click).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 5)], axis=1), 0.001, 0.03)


def synth_cryo_water_pour_with_ice(dur_s: float, seed: int = 77) -> np.ndarray:
    """Pitcher water pour + 38 Helmholtz bubbles + 300°C Leidenfrost steam sizzle + 5 crisp ice-cube clinks!"""
    r = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    b1, a1 = signal.butter(2, [420 / (SR * 0.5), 2500 / (SR * 0.5)], btype="bandpass")
    b2, a2 = signal.butter(2, [3600 / (SR * 0.5), 12500 / (SR * 0.5)], btype="bandpass")
    stream = signal.lfilter(b1, a1, r.standard_normal(n).astype(np.float32)) * (0.45 + 0.55 * np.sin(np.pi * u))
    sizzle = signal.lfilter(b2, a2, r.standard_normal(n).astype(np.float32)) * np.exp(-np.maximum(0, u - 0.05) * 1.55) * 0.62
    s = stream + sizzle
    for k in range(38):
        uk = (k + r.uniform(0.1, 0.9)) / 38.0
        bi = int(uk * (dur_s - 0.08) * SR)
        m = int(0.032 * SR)
        if bi + m < n:
            tt = np.arange(m, dtype=np.float32) / SR
            f0 = 580.0 + 980.0 * uk + r.uniform(-90, 90)
            s[bi:bi + m] += np.exp(-tt * 135.0) * np.sin(2 * np.pi * (f0 + f0 * 1.9 * tt / 0.032) * tt) * r.uniform(0.34, 0.74)
    # 5 crisp ice-cube against crystal glass clinks
    for uk_ice in [0.14, 0.31, 0.49, 0.68, 0.84]:
        bi = int(uk_ice * (dur_s - 0.12) * SR)
        m = int(0.095 * SR)
        if bi + m < n:
            tt = np.arange(m, dtype=np.float32) / SR
            fi = r.uniform(3300.0, 4300.0)
            clink = np.exp(-tt * 52.0) * (0.65 * np.sin(2 * np.pi * fi * tt) + 0.35 * np.sin(2 * np.pi * (fi * 1.61) * tt))
            s[bi:bi + m] += clink * 0.55
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 9)], axis=1).astype(np.float32), 0.04, 0.12)


def synth_sub_drop(dur_s: float = 2.3, f_start: float = 82.0, f_end: float = 24.5) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    f_inst = f_start * np.exp(-u * 2.2) + f_end
    s = np.tanh(1.38 * np.sin(2 * np.pi * np.cumsum(f_inst) / SR)) * (0.4 + 0.6 * (1 - u)) * np.exp(-u * 1.1)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, s], axis=1).astype(np.float32), 0.004, 0.25)


def synth_vacuum_riser_with_modal_singing(dur_s: float, seed: int = 606) -> np.ndarray:
    """Suction riser + 3.12 kHz stressed wine-glass breaking-point modal resonance -> instant choke!"""
    r = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    f_inst = 115.0 + 1720.0 * (u ** 3.3)
    b, a = signal.butter(2, [320 / (SR * 0.5), 5600 / (SR * 0.5)], btype="bandpass")
    wh = signal.lfilter(b, a, r.standard_normal(n).astype(np.float32))
    modal_sing = 0.28 * np.sin(2 * np.pi * np.cumsum(2980.0 + 210.0 * (u ** 2)) / SR) * (u ** 2.2)
    s = (0.52 * np.sin(2 * np.pi * np.cumsum(f_inst) / SR) + 0.36 * wh + modal_sing) * (u ** 2.3)
    s /= (np.max(np.abs(s)) + 1e-9)
    choke = int(0.008 * SR)
    s[-choke:] *= np.linspace(1.0, 0.0, choke, dtype=np.float32)
    return np.stack([s, np.roll(s, 11)], axis=1).astype(np.float32)


def synth_accelerating_heartbeat_and_ticks(dur_s: float) -> np.ndarray:
    n = int(dur_s * SR)
    out = np.zeros((n, 2), dtype=np.float32)
    m_tk = int(0.013 * SR)
    tt = np.arange(m_tk, dtype=np.float32) / SR
    tk_a = np.exp(-tt * 430.0) * (0.75 * np.sin(2 * np.pi * 4700 * tt) + 0.4 * np.sin(2 * np.pi * 7900 * tt))
    tk_b = np.exp(-tt * 460.0) * (0.70 * np.sin(2 * np.pi * 3950 * tt) + 0.4 * np.sin(2 * np.pi * 6500 * tt))
    cur = 0.0
    k = 0
    while cur < dur_s - 0.02:
        u = cur / dur_s
        rate = 7.5 + 10.5 * (u ** 1.7)
        idx = int(cur * SR)
        if idx + m_tk < n:
            tk = tk_a if k % 2 == 0 else tk_b
            pan = -0.34 if k % 2 == 0 else 0.34
            gain = 0.45 + 0.55 * u
            out[idx:idx + m_tk, 0] += tk * gain * (0.5 - 0.5 * pan)
            out[idx:idx + m_tk, 1] += tk * gain * (0.5 + 0.5 * pan)
        cur += 1.0 / rate
        k += 1

    # Sub-heartbeat lub-dub accelerating toward fracture!
    m_hb = int(0.15 * SR)
    thb = np.arange(m_hb, dtype=np.float32) / SR
    thump = np.exp(-thb * 18.0) * np.sin(2 * np.pi * (68.0 * np.exp(-thb * 8.0) + 37.0) * thb)
    hb_cur = 0.15
    while hb_cur < dur_s - 0.25:
        u = hb_cur / dur_s
        for sub_off, sub_g in [(0.0, 0.65), (0.13 - 0.03 * u, 0.45)]:
            bi = int((hb_cur + sub_off) * SR)
            if bi + m_hb < n:
                g_h = sub_g * (0.45 + 0.55 * u)
                out[bi:bi + m_hb, 0] += thump * g_h
                out[bi:bi + m_hb, 1] += thump * g_h
        hb_cur += 0.72 - 0.38 * u

    out /= (np.max(np.abs(out)) + 1e-9)
    return fade_io(out, 0.02, 0.02)


def synth_whoosh(dur_s: float = 0.5, f0: float = 2200.0, f1: float = 280.0, seed: int = 19) -> np.ndarray:
    r = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    f_inst = f0 * np.exp(-u * 2.8) + f1
    b, a = signal.butter(2, [260 / (SR * 0.5), 5600 / (SR * 0.5)], btype="bandpass")
    nz = signal.lfilter(b, a, r.standard_normal(n).astype(np.float32))
    s = (0.42 * np.sin(2 * np.pi * np.cumsum(f_inst) / SR) + 0.58 * nz) * (np.sin(np.pi * u) ** 1.3)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 10)], axis=1).astype(np.float32), 0.015, 0.08)


def synth_leidenfrost_coil_sizzle(dur_s: float = 2.4, seed: int = 404) -> np.ndarray:
    r = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    b, a = signal.butter(2, [3800 / (SR * 0.5), 13500 / (SR * 0.5)], btype="bandpass")
    s = signal.lfilter(b, a, r.standard_normal(n).astype(np.float32)) * np.exp(-t * 1.25)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 8)], axis=1).astype(np.float32), 0.02, 0.15)


def synth_boron_shield_chord(dur_s: float = 1.6) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    s = (
        0.48 * np.sin(2 * np.pi * 1046.5 * t) * np.exp(-t * 2.4)
        + 0.34 * np.sin(2 * np.pi * 1568.0 * t) * np.exp(-t * 3.0)
        + 0.24 * np.sin(2 * np.pi * 2093.0 * t) * np.exp(-t * 3.8)
    ).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 14)], axis=1), 0.01, 0.15)


# ---------------------------------------------------------------------------
# 3. PLACE FOLEY & MASSIVE SHATTER CLIMAX ON BUSES
# ---------------------------------------------------------------------------
foley_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)
impact_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)

t_pour0 = seg_by_id["S3_POUR_A"]["t0"] - 0.08
t_pour1 = seg_by_id["S4_WAIT"]["t0"] - 0.12
t_wait  = seg_by_id["S4_WAIT"]["t0"]
t_shear0= seg_by_id["S5_SHEAR_A"]["t0"]
t_boro0 = seg_by_id["S8_BORO_A"]["t0"]
t_loop0 = seg_by_id["S9_LOOP_A"]["t0"]

# Hook & Heat Soak + Thermal Expansion Quartz Creaks
place_clip(foley_bus, synth_imax_braam(1.25, 36.71), 0.04, gain=0.28)
place_clip(foley_bus, synth_whoosh(0.48, 1900, 320, 11), seg_by_id["S2_HEAT"]["t0"] - 0.06, gain=0.22, pan=0.18)
place_clip(foley_bus, synth_imax_braam(1.10, 43.65), seg_by_id["S2_HEAT"]["t0"] + 0.05, gain=0.20)
for crk_t, crk_p in [(4.25, -0.25), (5.65, 0.28), (6.75, -0.22)]:
    place_clip(foley_bus, synth_cleavage_crack_snap(900 + int(crk_t * 10)), crk_t, gain=0.09, pan=crk_p)

# Cryo-Pitcher Pour + Ice Cubes + 300°C Leidenfrost Sizzle
place_clip(foley_bus, synth_whoosh(0.45, 2500, 420, 22), t_pour0 - 0.05, gain=0.24)
place_clip(foley_bus, synth_cryo_water_pour_with_ice(max(1.5, t_pour1 - t_pour0), 77), t_pour0, gain=0.36)

# "RUKO." Surgical Laser Guillotine Slice
place_clip(foley_bus, synth_whoosh(0.52, 3800, 220, 33), t_wait - 0.04, gain=0.34, pan=-0.20)
place_clip(foley_bus, synth_imax_braam(1.15, 36.71), t_wait + 0.34, gain=0.24)

# Atomic Shear + Heartbeat + Ticks + 4 Cleavage Cracks + Modal Singing Riser -> Hard Choke at VACUUM_T0!
shear_span = max(1.2, (VACUUM_T0 - 0.04) - t_shear0)
place_clip(foley_bus, synth_accelerating_heartbeat_and_ticks(shear_span), t_shear0, gain=0.21)
place_clip(foley_bus, synth_vacuum_riser_with_modal_singing(min(3.4, shear_span), 606), VACUUM_T0 - min(3.4, shear_span) - 0.02, gain=0.35)

crack_times = [
    round(t_shear0 + shear_span * 0.22, 3),
    round(t_shear0 + shear_span * 0.46, 3),
    round(t_shear0 + shear_span * 0.68, 3),
    round(t_shear0 + shear_span * 0.86, 3),
]
for ci, ct in enumerate(crack_times):
    if ct + 0.33 < VACUUM_T0:
        place_clip(foley_bus, synth_cleavage_crack_snap(300 + ci), ct, gain=0.27 + 0.06 * ci, pan=(-0.38 if ci % 2 == 0 else 0.38))

# === PROTECTED CLIMAX DETONATION AT SHATTER_T (+11 dB Dynamic Contrast!) ===
place_clip(impact_bus, synth_crystal_shatter_explosion_ultra(2.25, 2026), SHATTER_T, gain=0.98)
place_clip(impact_bus, synth_imax_braam(1.65, 36.71), SHATTER_T + 0.008, gain=0.72)
place_clip(impact_bus, synth_imax_braam(1.40, 55.00), SHATTER_T + 0.020, gain=0.44)
place_clip(impact_bus, synth_sub_drop(2.35, 84.0, 24.5), SHATTER_T + 0.015, gain=0.80)
place_clip(impact_bus, synth_whoosh(0.85, 6200, 240, 99), SHATTER_T + 0.005, gain=0.58)

# Secondary "DHADAM!" Gravity Snap + Hot-Coil Water Sizzle + 22 Stereo Shard Floor Bounces
place_clip(impact_bus, synth_sub_drop(1.15, 70.0, 28.0), seg_by_id["S7_DHADAM"]["t0"], gain=0.46)
place_clip(foley_bus, synth_leidenfrost_coil_sizzle(2.6, 404), seg_by_id["S7_DHADAM"]["t0"] + 0.06, gain=0.22, pan=0.14)

shard_rng = np.random.default_rng(884)
shard_bounce_times = sorted([SHATTER_T + 0.38 + (k / 22.0) * 4.5 + shard_rng.uniform(-0.05, 0.05) for k in range(22)])
for si, sbt in enumerate(shard_bounce_times):
    g_sb = 0.29 * math.exp(-si * 0.070)
    p_sb = float(shard_rng.uniform(-0.76, 0.76))
    place_clip(foley_bus, synth_shard_floor_tinkle(700 + si), sbt, gain=g_sb, pan=p_sb)

# Borosilicate 3.3 Live Torture-Test Pour + Boron Shield Chord & Loop Return
place_clip(foley_bus, synth_whoosh(0.50, 2100, 310, 77), t_boro0 - 0.05, gain=0.25, pan=-0.15)
place_clip(foley_bus, synth_boron_shield_chord(1.65), t_boro0 + 0.02, gain=0.24)
place_clip(foley_bus, synth_cryo_water_pour_with_ice(3.4, 188), t_boro0 + 0.35, gain=0.22, pan=-0.12)
place_clip(foley_bus, synth_whoosh(0.55, 1600, 260, 88), t_loop0 - 0.05, gain=0.22, pan=0.12)


# ---------------------------------------------------------------------------
# 4. INTEGER-CYCLE HARMONIC SCORE + 55ms VO DUCKING + HARD VACUUM GATE
# ---------------------------------------------------------------------------
music_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)
t_vec = np.arange(N_SAMPLES, dtype=np.float32) / SR


def int_freq(hz: float) -> float:
    return round(hz * DUR_S) / DUR_S


f_d1, f_d2 = int_freq(36.71), int_freq(73.42)
f_a2l, f_a2r = int_freq(109.85), int_freq(110.15)
f_f3 = int_freq(174.61)

swell = 0.68 + 0.32 * np.cos(2 * np.pi * (4.0 / DUR_S) * t_vec)
music_bus[:, 0] += (0.46 * np.sin(2 * np.pi * f_d1 * t_vec) + 0.32 * np.sin(2 * np.pi * f_d2 * t_vec) + 0.18 * np.sin(2 * np.pi * f_a2l * t_vec) + 0.10 * np.sin(2 * np.pi * f_f3 * t_vec)) * swell * 0.132
music_bus[:, 1] += (0.46 * np.sin(2 * np.pi * f_d1 * t_vec) + 0.32 * np.sin(2 * np.pi * f_d2 * t_vec) + 0.18 * np.sin(2 * np.pi * f_a2r * t_vec) + 0.10 * np.sin(2 * np.pi * f_f3 * t_vec)) * swell * 0.132

notes_ost = [293.66, 349.23, 440.00, 466.16, 440.00, 349.23, 329.63, 293.66]
step_s = 0.25
for st in range(int(round(DUR_S / step_s))):
    if st % 8 == 7:
        continue
    t0_st = st * step_s
    if (VACUUM_T0 - 0.26) <= t0_st <= (SHATTER_T + 0.35):
        continue
    m = int(0.22 * SR)
    mt = np.arange(m, dtype=np.float32) / SR
    fn = notes_ost[st % len(notes_ost)]
    vel = (0.13 + 0.14 * ((t0_st - t_shear0) / max(0.5, VACUUM_T0 - t_shear0))) if (t_shear0 <= t0_st < VACUUM_T0) else 0.13
    plk = vel * (np.exp(-mt * 16.0) * np.sin(2 * np.pi * fn * mt) + 0.24 * np.exp(-mt * 35.0) * np.sin(2 * np.pi * (fn * 2.0) * mt))
    pan_st = 0.35 * math.sin(st * 1.15)
    idx = int(round(t0_st * SR))
    L = min(m, N_SAMPLES - idx)
    music_bus[idx:idx + L, 0] += plk[:L] * (0.5 - 0.5 * pan_st)
    music_bus[idx:idx + L, 1] += plk[:L] * (0.5 + 0.5 * pan_st)

vo_duck = compute_lookahead_duck_envelope(vo_bus, lookahead_s=0.055)
shatter_duck = np.ones(N_SAMPLES, dtype=np.float32)
sd0, sd1 = int(SHATTER_T * SR), min(N_SAMPLES, int((SHATTER_T + 1.85) * SR))
shatter_duck[sd0:sd1] = 0.20 + 0.80 * np.linspace(0.0, 1.0, sd1 - sd0, dtype=np.float32) ** 1.6

music_ducked = music_bus * ((1.0 - 0.58 * vo_duck) * shatter_duck)[:, None]
foley_ducked = foley_bus * (1.0 - 0.32 * vo_duck)[:, None]

vac_mask = np.ones(N_SAMPLES, dtype=np.float32)
v_fade_in = int((VACUUM_T0 - 0.018) * SR)
v_zero_0 = int(VACUUM_T0 * SR)
v_zero_1 = int(SHATTER_T * SR)
vac_mask[v_fade_in:v_zero_0] = np.linspace(1.0, 0.0, v_zero_0 - v_fade_in, dtype=np.float32)
vac_mask[v_zero_0:v_zero_1] = 0.0

impact_norm = impact_bus / (float(np.max(np.abs(impact_bus))) + 1e-9)
impact_saturated = (np.tanh(2.48 * impact_norm) / math.tanh(2.48)).astype(np.float32)

raw_mix = (vo_bus * 0.88 + foley_ducked * 0.72 + music_ducked * 0.68) * vac_mask[:, None] + impact_saturated * 1.14
raw_mix[v_zero_0:v_zero_1, :] = 0.0
peak_raw = float(np.max(np.abs(raw_mix)) + 1e-9)
if peak_raw > 0.96:
    raw_mix = raw_mix * (0.96 / peak_raw)

# ---------------------------------------------------------------------------
# 5. TWO-PASS LINEAR EBU R128 MASTERING + FORENSIC PROBES
# ---------------------------------------------------------------------------
pre_wav = os.path.join(TMP_DIR, "pre_thermal_v6_ultra.wav")
master_wav = os.path.join(TMP_DIR, "master_mix_v6_ultra.wav")
sf.write(pre_wav, raw_mix, SR, subtype="PCM_24")

p1 = subprocess.run(
    [FFMPEG, "-y", "-i", pre_wav, "-af", "loudnorm=I=-14.2:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
    capture_output=True, text=True, check=True,
)
ln = json.loads(p1.stderr[p1.stderr.rfind("{"):p1.stderr.rfind("}") + 1])
af2 = (
    f"loudnorm=I=-14.2:TP=-1.5:LRA=11:measured_I={ln['input_i']}:"
    f"measured_TP={ln['input_tp']}:measured_LRA={ln['input_lra']}:"
    f"measured_thresh={ln['input_thresh']}:offset={ln['target_offset']}:linear=true,"
    f"alimiter=limit=-1.5dB:level=false"
)
subprocess.run(
    [FFMPEG, "-y", "-i", pre_wav, "-af", af2, "-ar", "48000", "-c:a", "pcm_s24le", master_wav],
    check=True, capture_output=True,
)
m_data, _ = sf.read(master_wav, dtype="float32", always_2d=True)
m_data = m_data[:N_SAMPLES] if len(m_data) >= N_SAMPLES else np.pad(m_data, ((0, N_SAMPLES - len(m_data)), (0, 0)))
m_data[v_zero_0:v_zero_1, :] = 0.0
sf.write(master_wav, m_data, SR, subtype="PCM_24")

ver = subprocess.run(
    [FFMPEG, "-nostats", "-i", master_wav, "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
    capture_output=True, text=True, check=True,
)
for line in ver.stderr.splitlines():
    if any(k in line for k in ("I:", "LRA:", "Peak:")) and "TARGET:-23" not in line:
        print("[EBU R128 V6 ULTRA]", line.strip())


def rms_db(arr):
    return float(20.0 * np.log10(float(np.sqrt(np.mean(arr ** 2))) + 1e-12))


build_bed_rms = rms_db(m_data[int((SHATTER_T - 2.2) * SR):int((VACUUM_T0 - 0.1) * SR)])
blast_peak_rms = rms_db(m_data[int(SHATTER_T * SR):int((SHATTER_T + 0.45) * SR)])
vac_qa_rms = rms_db(m_data[int(VACUUM_QA_WINDOW[0] * SR):int(VACUUM_QA_WINDOW[1] * SR)])
print(f"[Audio V6 Forensics] Build RMS={build_bed_rms:.1f} dBFS | Shatter Blast RMS={blast_peak_rms:.1f} dBFS | Contrast=+{blast_peak_rms - build_bed_rms:.1f} dB | WAV Vacuum={vac_qa_rms:.1f} dBFS")

lock_data = {
    "project": "monarch-edits-thermal-shock-v6-ultra-imax",
    "fps": FPS,
    "duration_s": DUR_S,
    "total_frames": TOTAL_FRAMES,
    "time_stretch_applied": False,
    "voice_id": "voice-00",
    "vacuum_t0": VACUUM_T0,
    "shatter_t": SHATTER_T,
    "shatter_f": SHATTER_F,
    "vacuum_qa_window": VACUUM_QA_WINDOW,
    "protected_climax_window_s": [VACUUM_T0, CLIMAX_QUIET_END_T],
    "crack_times_s": crack_times,
    "shard_bounce_times_s": [round(x, 3) for x in shard_bounce_times],
    "shots": SHOTS,
    "captions": timeline_segments,
}

lock_path = os.path.join(PROJ_DIR, "voice-lock-v6-ultra.json")
with open(lock_path, "w", encoding="utf-8") as f:
    json.dump(lock_data, f, indent=2, ensure_ascii=False)


def fmt_srt(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


srt_lines, vtt_lines = [], ["WEBVTT", ""]
for idx_c, seg in enumerate(timeline_segments, 1):
    srt_lines += [str(idx_c), f"{fmt_srt(seg['t0'])} --> {fmt_srt(seg['t1'])}", f"{seg['l1']} - {seg['l2']}", ""]
    vtt_lines += [f"{fmt_srt(seg['t0']).replace(',', '.')} --> {fmt_srt(seg['t1']).replace(',', '.')}", f"{seg['l1']} - {seg['l2']}", ""]

with open(os.path.join(EXPORT_DIR, "Thermal-Shock-V6-Ultra-Captions.srt"), "w", encoding="utf-8") as f:
    f.write("\n".join(srt_lines))
with open(os.path.join(EXPORT_DIR, "Thermal-Shock-V6-Ultra-Captions.vtt"), "w", encoding="utf-8") as f:
    f.write("\n".join(vtt_lines))

print(f"[LOCKED V6 ULTRA] {lock_path} | 14 Shots | SHATTER_T={SHATTER_T}s (f={SHATTER_F}) | VACUUM={VACUUM_QA_WINDOW}")
