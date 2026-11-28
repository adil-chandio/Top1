#!/usr/bin/env python3
"""
Gate 2 Audio-First Frame-Lock & Open-Air Karoo Badlands / Monsoon Foley Master (`V6.3 Director Edition`)
Project: Extinct Life — "This Rock Holds Two Animals" (`W02_SCORCHED_FIELD_EXPEDITION`, Specimen BP/1/5558)
Duration: 36.000s (1,080 exact frames @ 30.000 fps), 48 kHz / 24-bit Master WAV.
Zero VO Time-Stretch (`time_stretch_applied = False`).
"""
import json
import math
import os
import sys

sys.path.insert(0, "/tmp/py")
sys.path.insert(0, "/home/user/Top1/tools/monarch-v6-imax-sdk/python")

import numpy as np
from scipy import signal
import soundfile as sf

from audio_imax_dsp import (
    SR,
    FPS,
    load_wav_48k_stereo,
    fade_io,
    place_clip,
    tighten_vo_zero_stretch,
    compute_lookahead_duck_envelope,
    synth_imax_braam,
    synth_vacuum_suction,
    synth_loop_locked_score,
    apply_vacuum_window,
    master_ebu_r128_linear,
    write_srt_vtt,
)

DURATION_S = 36.000
TOTAL_FRAMES = int(round(DURATION_S * FPS))  # 1080
N_SAMPLES = int(round(DURATION_S * SR))

RAW_DIR = "/tmp/karoo_v6/vo_raw"
OUT_DIR = "/tmp/karoo_field_v63"
EXPORT_DIR = "/home/user/Top1/exports/extinct-karoo-field-v63"
PROJECT_DIR = "/home/user/Top1/projects/extinct-karoo-field-v63"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(PROJECT_DIR, exist_ok=True)


def split_two_sentences(wav: np.ndarray, min_sil_s: float = 0.20, thresh: float = 0.0022):
    mono_sq = np.mean(wav ** 2, axis=1)
    win = int(0.015 * SR)
    rms = np.sqrt(np.convolve(mono_sq, np.ones(win, dtype=np.float32) / win, mode="same"))
    voiced = np.flatnonzero(rms > thresh)
    gaps = []
    prev = voiced[0]
    for ix in voiced[1:]:
        if ix - prev > int(min_sil_s * SR):
            gaps.append((ix - prev, prev, ix))
        prev = ix
    assert gaps, "Expected inter-sentence pause for clean split"
    _, end_a, start_b = max(gaps, key=lambda g: g[0])
    s0 = max(0, voiced[0] - int(0.025 * SR))
    e0 = min(len(wav), end_a + int(0.035 * SR))
    s1 = max(0, start_b - int(0.025 * SR))
    e1 = min(len(wav), voiced[-1] + int(0.035 * SR))
    return (
        tighten_vo_zero_stretch(wav[s0:e0], max_gap_s=0.14),
        tighten_vo_zero_stretch(wav[s1:e1], max_gap_s=0.14),
    )


def synth_karoo_desert_wind_bed(dur_s: float = 36.0, seed: int = 5558) -> np.ndarray:
    """Loop-locked open-air South African Karoo desert wind + fine blowing quartz sand grains."""
    rng = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    # Periodic gust envelope so t=0.000s and t=36.000s match cleanly across the loop seam
    w0 = 2.0 * np.pi / dur_s
    gust = 0.58 + 0.26 * np.sin(3.0 * w0 * t + 0.4) + 0.16 * np.cos(7.0 * w0 * t)

    b_air, a_air = signal.butter(2, [210 / (SR * 0.5), 1450 / (SR * 0.5)], btype="bandpass")
    b_sand, a_sand = signal.butter(2, [2400 / (SR * 0.5), 6200 / (SR * 0.5)], btype="bandpass")

    air_l = signal.lfilter(b_air, a_air, rng.standard_normal(n).astype(np.float32))
    air_r = signal.lfilter(b_air, a_air, rng.standard_normal(n).astype(np.float32))
    sand_l = signal.lfilter(b_sand, a_sand, rng.standard_normal(n).astype(np.float32)) * 0.22
    sand_r = signal.lfilter(b_sand, a_sand, rng.standard_normal(n).astype(np.float32)) * 0.22

    # Attenuate surface desert wind while underground inside burrow (18.2s .. 30.8s)
    e1 = np.clip(-(t - 18.2) * 5.0, -40.0, 40.0)
    e2 = np.clip((t - 30.9) * 5.0, -40.0, 40.0)
    burrow_shade = 1.0 - 0.65 * ((1.0 / (1.0 + np.exp(e1))) * (1.0 / (1.0 + np.exp(e2))))
    out = np.stack([(air_l + sand_l) * gust * burrow_shade, (air_r + sand_r) * gust * burrow_shade], axis=1)
    out /= (np.max(np.abs(out)) + 1e-9)
    # Cross-blend final 120ms with opening 120ms for seamless loop continuity
    xf = int(0.12 * SR)
    alpha = np.linspace(0.0, 1.0, xf, dtype=np.float32)[:, None]
    out[-xf:] = out[-xf:] * (1.0 - alpha) + out[:xf] * alpha
    return out.astype(np.float32)


def synth_fossil_brush_stroke(dur_s: float = 0.42, seed: int = 71) -> np.ndarray:
    """Dry hog-bristle paleontologist brush sweeping red quartz dust off sandstone."""
    rng = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = np.sin(np.pi * (t / dur_s)) ** 1.5
    b, a = signal.butter(2, [1400 / (SR * 0.5), 7400 / (SR * 0.5)], btype="bandpass")
    swish = signal.lfilter(b, a, rng.standard_normal(n).astype(np.float32)) * env
    swish /= (np.max(np.abs(swish)) + 1e-9)
    return fade_io(np.stack([swish * 0.85, np.roll(swish, 14) * 0.95], axis=1).astype(np.float32), 0.01, 0.04)


def synth_calcite_mineral_peel(dur_s: float = 1.85, reverse: bool = False, seed: int = 303) -> np.ndarray:
    """Warm natural sandstone-calcite geological cross-section shimmer (zero sci-fi laser!)."""
    rng = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = (1.0 - t / dur_s) if reverse else (t / dur_s)
    env = np.sin(np.pi * (t / dur_s)) ** 1.25
    b, a = signal.butter(2, [380 / (SR * 0.5), 2400 / (SR * 0.5)], btype="bandpass")
    stone_rub = signal.lfilter(b, a, rng.standard_normal(n).astype(np.float32)) * 0.48
    # Warm earthy fifth harmonic (D3=146.83 Hz, A3=220 Hz, F#4=369.99 Hz)
    chord = (
        0.45 * np.sin(2 * np.pi * (146.83 + 18.0 * u) * t)
        + 0.32 * np.sin(2 * np.pi * (220.0 + 24.0 * u) * t)
        + 0.18 * np.sin(2 * np.pi * (369.99 + 30.0 * u) * t)
    )
    sig = (stone_rub + chord * 0.55) * env
    sig /= (np.max(np.abs(sig)) + 1e-9)
    pan = np.linspace(-0.45, 0.45, n, dtype=np.float32) if not reverse else np.linspace(0.45, -0.45, n, dtype=np.float32)
    return fade_io(np.stack([sig * (0.5 - 0.35 * pan), sig * (0.5 + 0.35 * pan)], axis=1).astype(np.float32), 0.03, 0.08)


def synth_bone_callus_tap(freq_hz: float = 920.0, pan: float = 0.0) -> np.ndarray:
    """Tactile dry fossil-bone osteological resonance focus cue (replaces lab CT ping)."""
    n = int(0.32 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = (1.0 - np.exp(-t * 320.0)) * np.exp(-t * 16.5)
    body = (
        0.72 * np.sin(2 * np.pi * freq_hz * t)
        + 0.34 * np.sin(2 * np.pi * (freq_hz * 1.58) * t) * np.exp(-t * 28.0)
        + 0.18 * np.sin(2 * np.pi * 240.0 * t) * np.exp(-t * 42.0)
    ) * env
    body /= (np.max(np.abs(body)) + 1e-9)
    return fade_io(
        np.stack([body * (0.5 - 0.35 * pan), np.roll(body, 6) * (0.5 + 0.35 * pan)], axis=1).astype(np.float32),
        0.002,
        0.03,
    )


def synth_time_wind_passage(dur_s: float = 1.20, seed: int = 250) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    env = np.sin(np.pi * u) ** 1.35
    b, a = signal.butter(2, [140 / (SR * 0.5), 2600 / (SR * 0.5)], btype="bandpass")
    wind = signal.lfilter(b, a, rng.standard_normal(n).astype(np.float32))
    sub = 0.68 * np.sin(2 * np.pi * (44.0 + 32.0 * u) * t)
    sig = (0.52 * wind + sub) * env
    sig /= (np.max(np.abs(sig)) + 1e-9)
    pan = np.linspace(0.55, -0.55, n, dtype=np.float32)
    return fade_io(np.stack([sig * (0.5 - 0.4 * pan), sig * (0.5 + 0.4 * pan)], axis=1).astype(np.float32), 0.03, 0.08)


def synth_sandstone_crawl_step(seed: int = 11) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(0.16 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = np.exp(-t * 26.0) * (1.0 - np.exp(-t * 240.0))
    b, a = signal.butter(2, [650 / (SR * 0.5), 4600 / (SR * 0.5)], btype="bandpass")
    grit = signal.lfilter(b, a, rng.standard_normal(n).astype(np.float32)) * env
    thud = 0.38 * np.exp(-t * 48.0) * np.sin(2 * np.pi * 112.0 * t)
    s = (grit * 0.8 + thud).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 6)], axis=1), 0.003, 0.02)


def synth_dormant_heartbeat(dur_s: float = 3.8) -> np.ndarray:
    n = int(dur_s * SR)
    out = np.zeros((n, 2), dtype=np.float32)
    for beat_t in [0.35, 1.85, 3.25]:
        for off, f0, g in [(0.0, 50.0, 0.9), (0.22, 42.0, 0.65)]:
            i0 = int((beat_t + off) * SR)
            m = min(int(0.22 * SR), n - i0)
            if m <= 0:
                continue
            tt = np.arange(m, dtype=np.float32) / SR
            th = g * np.exp(-tt * 18.0) * np.sin(2 * np.pi * (f0 * np.exp(-tt * 4.0) + 28.0) * tt)
            out[i0:i0 + m, 0] += th
            out[i0:i0 + m, 1] += th
    return fade_io(out, 0.02, 0.08)


def synth_monsoon_flash_flood_climax(dur_s: float = 5.65, seed: int = 250001) -> np.ndarray:
    """
    J-Cuts in at t = 25.15s (0.38s BEFORE S09 cut at 25.533s!) and spans through 30.80s:
      1. Distant rolling Early Triassic dry thunder J-cut (`+0.00..0.75s`) + slashing monsoon rain
      2. Sharp lightning crack (`+0.88s` = `26.03s`)
      3. Heavy silt-choked terracotta mud-wall slam (`+1.30s` = `26.45s` / Frame 794!)
      4. Churning trapped-air burrow bubbles & dense earthen submersion (`+1.40..4.10s`)
      5. Deep tectonic Beaufort sandstone compaction seal (`+4.30s` = `29.45s`)
    """
    rng = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    out_l = np.zeros(n, dtype=np.float32)
    out_r = np.zeros(n, dtype=np.float32)

    # 1. J-Cut Rolling Thunder + Slashing Rain Curtain
    th_env = (1.0 - np.exp(-t * 8.0)) * np.exp(-t * 1.65)
    b_th, a_th = signal.butter(2, [32 / (SR * 0.5), 210 / (SR * 0.5)], btype="bandpass")
    thunder = signal.lfilter(b_th, a_th, rng.standard_normal(n).astype(np.float32)) * th_env * 0.95
    out_l += thunder
    out_r += np.roll(thunder, 42)

    rain_env = np.clip((t - 0.25) / 0.6, 0.0, 1.0) * np.exp(-np.maximum(0.0, t - 2.2) * 1.2)
    b_rn, a_rn = signal.butter(2, [1200 / (SR * 0.5), 6800 / (SR * 0.5)], btype="bandpass")
    out_l += signal.lfilter(b_rn, a_rn, rng.standard_normal(n).astype(np.float32)) * rain_env * 0.35
    out_r += signal.lfilter(b_rn, a_rn, rng.standard_normal(n).astype(np.float32)) * rain_env * 0.35

    # 2. Sharp Lightning Crack at dt = 0.88s (`26.03s`)
    t_cr = np.maximum(0.0, t - 0.88)
    cr_gate = (t >= 0.88).astype(np.float32)
    b_cr, a_cr = signal.butter(2, [450 / (SR * 0.5), 5200 / (SR * 0.5)], btype="bandpass")
    crack = signal.lfilter(b_cr, a_cr, rng.standard_normal(n).astype(np.float32)) * np.exp(-t_cr * 14.0) * cr_gate * 0.72
    out_l += crack
    out_r += np.roll(crack, 18)

    # 3. Heavy Silt-Choked Flash-Flood Wall Slam at dt = 1.30s (`26.45s` = Frame 794!)
    t_imp = np.maximum(0.0, t - 1.30)
    imp_gate = (t >= 1.30).astype(np.float32)
    sub_boom = 1.55 * np.exp(-t_imp * 3.6) * np.sin(2 * np.pi * (64.0 * np.exp(-t_imp * 3.0) + 31.0) * t_imp) * imp_gate

    rush_env = imp_gate * (1.0 - np.exp(-t_imp * 14.0)) * np.exp(-np.maximum(0.0, t_imp - 1.90) * 1.45)
    raw_l = rng.standard_normal(n).astype(np.float32)
    raw_r = rng.standard_normal(n).astype(np.float32)
    b_hi, a_hi = signal.butter(2, [190 / (SR * 0.5), 4400 / (SR * 0.5)], btype="bandpass")
    b_subm, a_subm = signal.butter(2, [48 / (SR * 0.5), 460 / (SR * 0.5)], btype="bandpass")
    roar_surface_l = signal.lfilter(b_hi, a_hi, raw_l)
    roar_surface_r = signal.lfilter(b_hi, a_hi, raw_r)
    roar_subm_l = signal.lfilter(b_subm, a_subm, raw_l)
    roar_subm_r = signal.lfilter(b_subm, a_subm, raw_r)

    submerge_mix = np.clip((t_imp - 0.50) / 1.60, 0.0, 1.0)
    water_l = ((1.0 - submerge_mix) * roar_surface_l * 1.05 + submerge_mix * roar_subm_l * 1.65) * rush_env
    water_r = ((1.0 - submerge_mix) * roar_surface_r * 1.05 + submerge_mix * roar_subm_r * 1.65) * rush_env
    out_l += sub_boom + water_l
    out_r += sub_boom + water_r

    # 4. Trapped-air bubbles escaping earthen chamber
    for b_idx in range(30):
        bt0 = 1.38 + (b_idx / 30.0) * 2.35 + rng.uniform(-0.02, 0.02)
        i0 = int(bt0 * SR)
        m = min(int(0.085 * SR), n - i0)
        if m <= 0:
            continue
        tt = np.arange(m, dtype=np.float32) / SR
        f0 = rng.uniform(300.0, 980.0)
        f_chirp = f0 * (1.0 + 0.78 * (tt / 0.085) ** 1.6)
        bub = 0.25 * np.exp(-tt * 42.0) * np.sin(2 * np.pi * np.cumsum(f_chirp) / SR)
        pan = rng.uniform(-0.6, 0.6)
        out_l[i0:i0 + m] += bub * (0.5 - 0.4 * pan)
        out_r[i0:i0 + m] += bub * (0.5 + 0.4 * pan)

    # 5. Deep Tectonic Sandstone Compaction Seal at dt = 4.30s (`29.45s`)
    t_seal = np.maximum(0.0, t - 4.30)
    seal_gate = (t >= 4.30).astype(np.float32)
    seal_thud = 1.25 * np.exp(-t_seal * 5.0) * np.sin(2 * np.pi * (54.0 * np.exp(-t_seal * 4.5) + 29.0) * t_seal) * seal_gate
    out_l += seal_thud
    out_r += seal_thud

    out = np.stack([out_l, out_r], axis=1).astype(np.float32)
    out /= (np.max(np.abs(out)) + 1e-9)
    return fade_io(out, 0.02, 0.18)


def main():
    # 1. Load & split all 12 exact spoken clauses at 1.000x natural speed (`0%` stretch!)
    c01 = tighten_vo_zero_stretch(load_wav_48k_stereo(f"{RAW_DIR}/c01_hook.wav"), max_gap_s=0.14)
    c02 = tighten_vo_zero_stretch(load_wav_48k_stereo(f"{RAW_DIR}/c02_asleep.wav"), max_gap_s=0.15)
    c03 = tighten_vo_zero_stretch(load_wav_48k_stereo(f"{RAW_DIR}/c03_pair.wav"), max_gap_s=0.14)
    c04 = tighten_vo_zero_stretch(load_wav_48k_stereo(f"{RAW_DIR}/c04_wait.wav"), max_gap_s=0.10)
    c05 = tighten_vo_zero_stretch(load_wav_48k_stereo(f"{RAW_DIR}/c05_not_enemies.wav"), max_gap_s=0.12)
    c06a, c06b = split_two_sentences(load_wav_48k_stereo(f"{RAW_DIR}/c06_ribs.wav"))
    c07 = tighten_vo_zero_stretch(load_wav_48k_stereo(f"{RAW_DIR}/c07_shelter.wav"), max_gap_s=0.14)
    c08 = tighten_vo_zero_stretch(load_wav_48k_stereo(f"{RAW_DIR}/c08_dormancy.wav"), max_gap_s=0.14)
    c09 = tighten_vo_zero_stretch(load_wav_48k_stereo(f"{RAW_DIR}/c09_flood.wav"), max_gap_s=0.14)
    c10a, c10b = split_two_sentences(load_wav_48k_stereo(f"{RAW_DIR}/c10_clue_loop.wav"))

    # 2. Documentary Parchment / Ochre Typography + Single Reserved #E63926 Vermilion Forensic Accent!
    schedule = [
        ("L01_HOOK",        0.180, c01,  "THIS ROCK HOLDS",         "TWO ANIMALS INSIDE",      "TWO ANIMALS",  "#E8B059"),
        ("L02_ASLEEP",      2.540, c02,  "250 MILLION YEARS AGO",   "ONE CURLED UP ASLEEP",    "250 MILLION",  "#F4DFB8"),
        ("L03_PAIR",        6.980, c03,  "A MAMMAL RELATIVE",       "BESIDE AN AMPHIBIAN",     "AMPHIBIAN",    "#E8B059"),
        # --- PRE-TWIST VACUUM SILENCE: [10.220s .. 10.480s] (260ms -240 dBFS pure digital zero!) ---
        ("L04_WAIT",       10.500, c04,  "WAIT.",                   "LOOK CLOSER AT THE BONES","WAIT.",        "#E63926"),
        ("L05_NOT_ENEMIES",11.180, c05,  "THEY WERE NOT ENEMIES",   "ZERO PREDATOR STRUGGLE",  "NOT ENEMIES",  "#E63926"),
        ("L06A_RIBS",      12.860, c06a, "AMPHIBIAN RIBS HEALING",  "WITH ZERO BITE MARKS",    "HEALING",      "#E63926"),
        ("L06B_NO_HUNT",   16.240, c06b, "SO THIS WAS NOT A HUNT",  "OSTEOLOGICAL PROOF",      "NOT A HUNT",   "#E8B059"),
        ("L07_SHELTER",    18.180, c07,  "THE LIKELY STORY:",       "IT CRAWLED IN FOR SHELTER","SHELTER",     "#F4DFB8"),
        ("L08_DORMANCY",   21.220, c08,  "DEEP AESTIVATION",        "SCORCHING DROUGHT SLEEP", "AESTIVATION",  "#E8B059"),
        # Note: L09_FLOOD finishes at ~28.34s; HUD strips away 100% across [26.00s .. 30.88s] pure cinema climax!
        ("L09_FLOOD",      25.540, c09,  "THEN A SUDDEN FLOOD",     "FILLED & SEALED THEM",    "FLOOD",        "#E8B059"),
        ("L10_CLUE",       30.920, c10a, "THAT IS THE CLUE",        "THE ROCK KEPT FOR 250M YRS","THE CLUE",   "#F4DFB8"),
        ("L11_LOOP",       33.180, c10b, "THIS ROCK HOLDS",         "TWO ANIMALS.",            "TWO ANIMALS.", "#E8B059"),
    ]

    vo_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)
    captions = []
    line_timings = []

    for lid, t0, clip, l1, l2, hi, accent in schedule:
        dur = len(clip) / SR
        t1 = round(t0 + dur, 4)
        assert t1 < DURATION_S - 0.35, f"Line {lid} overflows 36.0s: t1={t1}"
        place_clip(vo_bus, clip, t0, gain=1.0, pan=0.0)
        line_timings.append({"id": lid, "t0": round(t0, 4), "t1": t1, "f0": int(round(t0 * FPS)), "f1": int(round(t1 * FPS))})
        captions.append({
            "id": lid,
            "t0": round(t0, 4),
            "t1": t1,
            "l1": l1,
            "l2": l2,
            "hi": hi,
            "accent": accent,
            "text": f"{l1} — {l2}",
        })
        print(f"[VO Lock] {lid:16s} | {t0:6.3f}s -> {t1:6.3f}s ({dur:5.3f}s) | f={int(round(t0*FPS)):04d}..{int(round(t1*FPS)):04d}")

    dry_vo_path = f"{OUT_DIR}/dry_vo_karoo_field_v63.wav"
    sf.write(dry_vo_path, vo_bus, SR, subtype="PCM_24")

    # 3. Synthesize Authentic Open-Air Karoo Wind + Earthen Score + Foley + Monsoon Flood Climax
    duck_env = compute_lookahead_duck_envelope(vo_bus, lookahead_s=0.055)

    desert_wind = synth_karoo_desert_wind_bed(dur_s=DURATION_S, seed=5558) * 0.13
    desert_wind *= (1.0 - 0.48 * duck_env)[:, None]

    # Warm earthen cello-drone fifths (`49.0 Hz` G1) instead of cold lab drone
    score_bus = synth_loop_locked_score(dur_s=DURATION_S, base_hz=49.0) * 0.21
    score_bus *= (1.0 - 0.66 * duck_env)[:, None]

    sfx_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)
    climax_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)

    # Opening earthen sandstone resonance + paleontologist bristle brush sweep (`0.08s`, `1.55s`)
    place_clip(sfx_bus, synth_imax_braam(dur_s=1.55, root_hz=36.71), 0.05, gain=0.38)
    place_clip(sfx_bus, synth_fossil_brush_stroke(dur_s=0.44, seed=71), 0.14, gain=0.16, pan=-0.28)
    place_clip(sfx_bus, synth_fossil_brush_stroke(dur_s=0.38, seed=72), 1.62, gain=0.14, pan=0.22)

    # Sunlit calcite cross-section geological peel (`2.58s`)
    place_clip(sfx_bus, synth_calcite_mineral_peel(dur_s=2.10, reverse=False, seed=303), 2.58, gain=0.26)

    # Subtle bone-orientation taps in S03 (`7.15s`, `8.55s`)
    place_clip(sfx_bus, synth_bone_callus_tap(760.0, pan=-0.25), 7.15, gain=0.18)
    place_clip(sfx_bus, synth_bone_callus_tap(640.0, pan=0.25),  8.55, gain=0.18)

    # Pre-Twist Vacuum Suction (`9.34s -> 10.21s`) -> Hard -240 dBFS Vacuum `[10.220s, 10.480s]`!
    VAC_T0, VAC_T1 = 10.220, 10.480
    place_clip(sfx_bus, synth_vacuum_suction(dur_s=0.86, seed=7701), VAC_T0 - 0.87, gain=0.36)

    # Post-Wait Earthen Sub-Drop (`11.16s`)
    place_clip(sfx_bus, synth_imax_braam(dur_s=1.30, root_hz=41.20), 11.16, gain=0.38)

    # 3 Tactile Osteological Focus Taps on Healing Ribs #4, #5, #6 (`13.45s, 14.15s, 14.85s`)
    for idx, rt in enumerate([13.45, 14.15, 14.85]):
        place_clip(sfx_bus, synth_bone_callus_tap(880.0 + idx * 110.0, pan=-0.15 + idx * 0.15), rt, gain=0.22)

    # 250-Million-Year Desert-Wind Passage (`17.92s`) + 6 Sandstone Crawl Steps (`18.65..20.74s`)
    place_clip(sfx_bus, synth_time_wind_passage(dur_s=1.18, seed=250), 17.92, gain=0.36)
    for st_i, st_t in enumerate([18.65, 19.05, 19.48, 19.88, 20.32, 20.74]):
        place_clip(sfx_bus, synth_sandstone_crawl_step(seed=40 + st_i), st_t, gain=0.19, pan=-0.2 + 0.08 * st_i)

    # Dormant Aestivation Slow Heartbeat (`21.40s .. 25.20s`)
    place_clip(sfx_bus, synth_dormant_heartbeat(dur_s=3.80), 21.40, gain=0.34)

    # Walter Murch J-Cut Monsoon Thunder (`25.15s` — 0.38s BEFORE S09 cut!) + Flash-Flood Wall Slam (`26.45s`) + Lithification!
    flood_sfx = synth_monsoon_flash_flood_climax(dur_s=5.65, seed=250001)
    place_clip(climax_bus, flood_sfx, 25.15, gain=0.90)
    place_clip(climax_bus, synth_imax_braam(dur_s=1.85, root_hz=32.70), 28.42, gain=0.72)

    # Geological Seal Back to Modern Karoo Dig Trench (`30.86s`) + Final Brush Whisper (`33.55s`)
    place_clip(sfx_bus, synth_calcite_mineral_peel(dur_s=1.55, reverse=True, seed=309), 30.86, gain=0.22)
    place_clip(sfx_bus, synth_fossil_brush_stroke(dur_s=0.36, seed=79), 33.55, gain=0.12, pan=-0.18)

    sfx_bus *= (1.0 - 0.36 * duck_env)[:, None]

    pre_master = vo_bus * 1.08 + desert_wind + score_bus + sfx_bus + climax_bus

    # Carve strict -240 dBFS Pre-Twist Digital Vacuum `[10.220s, 10.480s]` across ALL buses!
    apply_vacuum_window(pre_master, VAC_T0, VAC_T1, taper_s=0.008)

    master_wav = f"{OUT_DIR}/master_mix_karoo_field_v63.wav"
    stats = master_ebu_r128_linear(pre_master, master_wav, target_i=-14.2, target_tp=-1.5)

    # Re-zero exact inner vacuum window post-loudnorm so WAV vacuum is pure 0.0 (-240 dBFS)!
    master_pcm, _ = sf.read(master_wav, dtype="float32", always_2d=True)
    apply_vacuum_window(master_pcm, VAC_T0 + 0.012, VAC_T1 - 0.012, taper_s=0.006)
    sf.write(master_wav, master_pcm, SR, subtype="PCM_24")

    vac_qa = [round(VAC_T0 + 0.025, 3), round(VAC_T1 - 0.025, 3)]  # [10.245, 10.455]
    vac_seg = master_pcm[int(vac_qa[0] * SR):int(vac_qa[1] * SR)]
    vac_db = 20.0 * math.log10(max(1e-12, float(np.sqrt(np.mean(vac_seg ** 2)))))
    peak_db = 20.0 * math.log10(max(1e-12, float(np.max(np.abs(master_pcm)))))
    print(f"[Audio Master V6.3] LUFS={stats['input_i']} -> -14.2 LUFS | Peak={peak_db:.2f} dBFS | Vacuum={vac_db:.1f} dBFS")

    # 4. Lock 12 Director-OS Shots (`0 .. 1080` exact frames @ 30fps — 1:1 with `director-plan.json`!)
    shots = [
        {"id": "S01", "f0":    0, "f1":   76, "set": "TRENCH", "lens_mm": 35,  "move": "push_in"},
        {"id": "S02", "f0":   76, "f1":  209, "set": "TRENCH", "lens_mm": 35,  "move": "truck_lateral"},
        {"id": "S03", "f0":  209, "f1":  307, "set": "TRENCH", "lens_mm": 35,  "move": "static"},
        {"id": "S04", "f0":  307, "f1":  385, "set": "TRENCH", "lens_mm": 50,  "move": "dolly_zoom"},
        {"id": "S05", "f0":  385, "f1":  487, "set": "TRENCH", "lens_mm": 100, "move": "probe_macro_glide"},
        {"id": "S06", "f0":  487, "f1":  545, "set": "TRENCH", "lens_mm": 85,  "move": "static"},
        {"id": "S07", "f0":  545, "f1":  636, "set": "BURROW", "lens_mm": 28,  "move": "tracking_follow"},
        {"id": "S08", "f0":  636, "f1":  766, "set": "BURROW", "lens_mm": 50,  "move": "static"},
        {"id": "S09", "f0":  766, "f1":  852, "set": "BURROW", "lens_mm": 28,  "move": "pull_out"},
        {"id": "S10", "f0":  852, "f1":  926, "set": "BURROW", "lens_mm": 35,  "move": "static"},
        {"id": "S11", "f0":  926, "f1":  995, "set": "TRENCH", "lens_mm": 35,  "move": "static"},
        {"id": "S12", "f0":  995, "f1": 1080, "set": "TRENCH", "lens_mm": 35,  "move": "static"},
    ]

    lock_data = {
        "project": "extinct-karoo-field-v63",
        "archetype_id": "W02_SCORCHED_FIELD_EXPEDITION",
        "hud_philosophy": "H1_DOCUMENTARY_LOWER_THIRD",
        "specimen": "BP/1/5558 (Thrinaxodon liorhinus + Broomistega putterilli, ~250 Ma Early Triassic Karoo)",
        "voice_id": "voice-01",
        "time_stretch_applied": False,
        "fps": FPS,
        "duration_s": DURATION_S,
        "total_frames": TOTAL_FRAMES,
        "vacuum_window_s": [VAC_T0, VAC_T1],
        "vacuum_qa_window": vac_qa,
        "flood_surge_t": 26.45,
        "flood_surge_f": 794,
        "protected_climax_windows_s": [
            [VAC_T0, 10.50],
            [26.00, 30.88],
        ],
        "lines": line_timings,
        "shots": shots,
        "captions": captions,
    }

    lock_path = f"{PROJECT_DIR}/voice-lock-karoo-field-v63.json"
    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump(lock_data, f, indent=2)

    write_srt_vtt(
        captions,
        f"{EXPORT_DIR}/Karoo-Burrow-Field-Edition-V6.3.srt",
        f"{EXPORT_DIR}/Karoo-Burrow-Field-Edition-V6.3.vtt",
    )
    print(f"[Gate 2 LOCKED] -> {lock_path} | 12 Director-OS Shots | {TOTAL_FRAMES} Frames ({DURATION_S:.3f}s)")


if __name__ == "__main__":
    main()
