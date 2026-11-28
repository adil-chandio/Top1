#!/usr/bin/env python3
"""
Gate 2 Audio-First Frame-Lock & 14-Layer Dolby Paleontology Foley Engine
Project: Extinct Life — "This Rock Holds Two Animals" (Karoo Burrow Specimen BP/1/5558, ~250 Ma)
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
    synth_chronometer_ticks,
    synth_laser_tomography_sweep,
    synth_loop_locked_score,
    apply_vacuum_window,
    master_ebu_r128_linear,
    write_srt_vtt,
)

DURATION_S = 36.000
TOTAL_FRAMES = int(round(DURATION_S * FPS))  # 1080
N_SAMPLES = int(round(DURATION_S * SR))

RAW_DIR = "/tmp/karoo_v6/vo_raw"
OUT_DIR = "/tmp/karoo_v6"
EXPORT_DIR = "/home/user/Top1/exports/extinct-karoo-burrow"
PROJECT_DIR = "/home/user/Top1/projects/extinct-karoo-burrow"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(PROJECT_DIR, exist_ok=True)


def split_two_sentences(wav: np.ndarray, min_sil_s: float = 0.20, thresh: float = 0.0022):
    """Splits a 2-sentence clip cleanly at the largest inter-sentence silence gap (0% stretch)."""
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


def synth_crystalline_ct_ping(freq_hz: float = 1560.0, dur_s: float = 0.55, pan: float = 0.0) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = (1.0 - np.exp(-t * 140.0)) * np.exp(-t * 7.2)
    tone = (
        0.68 * np.sin(2 * np.pi * freq_hz * t)
        + 0.24 * np.sin(2 * np.pi * (freq_hz * 2.003) * t) * np.exp(-t * 11.0)
        + 0.12 * np.sin(2 * np.pi * (freq_hz * 3.01) * t) * np.exp(-t * 18.0)
    ) * env
    l = tone * (0.5 - 0.35 * pan)
    r = np.roll(tone, 8) * (0.5 + 0.35 * pan)
    return fade_io(np.stack([l, r], axis=1).astype(np.float32), 0.004, 0.05)


def synth_time_rewind_whoosh(dur_s: float = 1.15, seed: int = 250) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    env = np.sin(np.pi * u) ** 1.4
    f_sweep = 160.0 + 1850.0 * np.sin(np.pi * u) ** 2
    ph = 2 * np.pi * np.cumsum(f_sweep) / SR
    b, a = signal.butter(2, [180 / (SR * 0.5), 3200 / (SR * 0.5)], btype="bandpass")
    wind = signal.lfilter(b, a, rng.standard_normal(n).astype(np.float32))
    sub = 0.65 * np.sin(2 * np.pi * (48.0 + 36.0 * u) * t)
    sig = (0.45 * wind + 0.30 * np.sin(ph) + sub) * env
    sig /= (np.max(np.abs(sig)) + 1e-9)
    pan = np.linspace(0.6, -0.6, n, dtype=np.float32)
    return fade_io(np.stack([sig * (0.5 - 0.4 * pan), sig * (0.5 + 0.4 * pan)], axis=1).astype(np.float32), 0.03, 0.08)


def synth_sandstone_crawl_step(seed: int = 11) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(0.16 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = np.exp(-t * 26.0) * (1.0 - np.exp(-t * 240.0))
    b, a = signal.butter(2, [650 / (SR * 0.5), 4600 / (SR * 0.5)], btype="bandpass")
    grit = signal.lfilter(b, a, rng.standard_normal(n).astype(np.float32)) * env
    thud = 0.35 * np.exp(-t * 48.0) * np.sin(2 * np.pi * 118.0 * t)
    s = (grit * 0.8 + thud).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 6)], axis=1), 0.003, 0.02)


def synth_dormant_heartbeat(dur_s: float = 3.8) -> np.ndarray:
    n = int(dur_s * SR)
    out = np.zeros((n, 2), dtype=np.float32)
    for beat_t in [0.35, 1.85, 3.25]:
        for off, f0, g in [(0.0, 52.0, 0.9), (0.21, 44.0, 0.65)]:
            i0 = int((beat_t + off) * SR)
            m = min(int(0.22 * SR), n - i0)
            if m <= 0:
                continue
            tt = np.arange(m, dtype=np.float32) / SR
            th = g * np.exp(-tt * 18.0) * np.sin(2 * np.pi * (f0 * np.exp(-tt * 4.0) + 28.0) * tt)
            out[i0:i0 + m, 0] += th
            out[i0:i0 + m, 1] += th
    return fade_io(out, 0.02, 0.08)


def synth_monsoon_flash_flood_climax(dur_s: float = 4.75, seed: int = 250000) -> np.ndarray:
    """
    Synthesizes the Protected Climax Flash-Flood Entombment (`t = 25.85s .. 30.60s`):
      1. Distant Triassic thunder crack (`+0.05s`)
      2. Violent rushing mud-water hydro-wall impact (`+0.62s` = exact `FLOOD_F = 795` / `26.500s`!)
      3. Churning Helmholtz water cavitation bubbles & swirling silt/pebbles (`+0.70..3.40s`)
      4. Underwater lowpass submersion + deep tectonic sandstone petrification seal (`+3.65s`)!
    """
    rng = np.random.default_rng(seed)
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    out_l = np.zeros(n, dtype=np.float32)
    out_r = np.zeros(n, dtype=np.float32)

    # 1. Distant Triassic storm thunder rumble at t=0.05s
    th_env = np.exp(-np.maximum(0.0, t - 0.05) * 2.8) * (t >= 0.05)
    b_th, a_th = signal.butter(2, [34 / (SR * 0.5), 240 / (SR * 0.5)], btype="bandpass")
    thunder = signal.lfilter(b_th, a_th, rng.standard_normal(n).astype(np.float32)) * th_env * 0.85
    out_l += thunder
    out_r += np.roll(thunder, 34)

    # 2. Flash-flood wall impact at dt = 0.65s (`26.500s` = Frame 795!)
    t_imp = np.maximum(0.0, t - 0.65)
    imp_gate = (t >= 0.65).astype(np.float32)
    sub_boom = 1.45 * np.exp(-t_imp * 3.8) * np.sin(2 * np.pi * (68.0 * np.exp(-t_imp * 3.0) + 33.0) * t_imp) * imp_gate

    # Sweeping lowpass underwater submersion: bright roaring splash -> deep submerged silt roar!
    rush_env = imp_gate * (1.0 - np.exp(-t_imp * 14.0)) * np.exp(-np.maximum(0.0, t_imp - 1.85) * 1.45)
    raw_l = rng.standard_normal(n).astype(np.float32)
    raw_r = rng.standard_normal(n).astype(np.float32)
    b_hi, a_hi = signal.butter(2, [220 / (SR * 0.5), 5400 / (SR * 0.5)], btype="bandpass")
    b_subm, a_subm = signal.butter(2, [55 / (SR * 0.5), 520 / (SR * 0.5)], btype="bandpass")
    roar_surface_l = signal.lfilter(b_hi, a_hi, raw_l)
    roar_surface_r = signal.lfilter(b_hi, a_hi, raw_r)
    roar_subm_l = signal.lfilter(b_subm, a_subm, raw_l)
    roar_subm_r = signal.lfilter(b_subm, a_subm, raw_r)

    submerge_mix = np.clip((t_imp - 0.55) / 1.65, 0.0, 1.0)
    water_l = ((1.0 - submerge_mix) * roar_surface_l * 1.1 + submerge_mix * roar_subm_l * 1.55) * rush_env
    water_r = ((1.0 - submerge_mix) * roar_surface_r * 1.1 + submerge_mix * roar_subm_r * 1.55) * rush_env
    out_l += sub_boom + water_l
    out_r += sub_boom + water_r

    # 3. 34 Helmholtz trapped-air burrow bubbles rising as flood fills the chamber!
    for b_idx in range(34):
        bt0 = 0.72 + (b_idx / 34.0) * 2.45 + rng.uniform(-0.02, 0.02)
        i0 = int(bt0 * SR)
        m = min(int(0.085 * SR), n - i0)
        if m <= 0:
            continue
        tt = np.arange(m, dtype=np.float32) / SR
        f0 = rng.uniform(340.0, 1180.0)
        f_chirp = f0 * (1.0 + 0.85 * (tt / 0.085) ** 1.6)
        bub = 0.28 * np.exp(-tt * 42.0) * np.sin(2 * np.pi * np.cumsum(f_chirp) / SR)
        pan = rng.uniform(-0.65, 0.65)
        out_l[i0:i0 + m] += bub * (0.5 - 0.4 * pan)
        out_r[i0:i0 + m] += bub * (0.5 + 0.4 * pan)

    # 4. Deep Tectonic Sandstone Compaction / Petrification Seal at dt = 3.65s (`29.50s`)
    t_seal = np.maximum(0.0, t - 3.65)
    seal_gate = (t >= 3.65).astype(np.float32)
    seal_thud = 1.15 * np.exp(-t_seal * 5.2) * np.sin(2 * np.pi * (56.0 * np.exp(-t_seal * 4.5) + 31.0) * t_seal) * seal_gate
    out_l += seal_thud
    out_r += seal_thud

    out = np.stack([out_l, out_r], axis=1).astype(np.float32)
    out /= (np.max(np.abs(out)) + 1e-9)
    return fade_io(out, 0.015, 0.16)


def main():
    # 1. Load & split all 11 exact spoken sentences at 1.000x natural speed (`0%` stretch!)
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

    # 2. Exact Cinema Placement Schedule across 36.000s (1,080 frames)
    schedule = [
        ("L01_HOOK",        0.180, c01,  "THIS ROCK HOLDS",         "TWO ANIMALS INSIDE",      "TWO ANIMALS",  "#F7C35F"),
        ("L02_ASLEEP",      2.540, c02,  "250 MILLION YEARS AGO",   "ONE CURLED UP ASLEEP",    "250 MILLION",  "#3AD4BE"),
        ("L03_PAIR",        6.980, c03,  "A MAMMAL RELATIVE",       "BESIDE AN AMPHIBIAN",     "MAMMAL",       "#F7C35F"),
        # --- PRE-TWIST VACUUM SILENCE: [10.220s .. 10.480s] (260ms -240 dBFS pure digital zero!) ---
        ("L04_WAIT",       10.500, c04,  "WAIT.",                   "LOOK CLOSER AT THE BONES","WAIT.",        "#FF6A48"),
        ("L05_NOT_ENEMIES",11.180, c05,  "THEY WERE NOT ENEMIES",   "ZERO PREDATOR STRUGGLE",  "NOT ENEMIES",  "#3AD4BE"),
        ("L06A_RIBS",      12.860, c06a, "AMPHIBIAN RIBS HEALING",  "WITH ZERO BITE MARKS",    "HEALING",      "#FFD166"),
        ("L06B_NO_HUNT",   16.240, c06b, "SO THIS WAS NOT A HUNT",  "FORENSIC X-RAY PROOF",    "NOT A HUNT",   "#3AD4BE"),
        ("L07_SHELTER",    18.180, c07,  "THE LIKELY STORY:",       "IT CRAWLED IN FOR SHELTER","SHELTER",     "#F7C35F"),
        ("L08_DORMANCY",   21.220, c08,  "DEEP AESTIVATION",        "SCORCHING DROUGHT SLEEP", "AESTIVATION",  "#3AD4BE"),
        ("L09_FLOOD",      25.540, c09,  "THEN A SUDDEN FLOOD",     "FILLED & SEALED THEM",    "FLOOD",        "#5CE1FF"),
        # --- PROTECTED PURE-CINEMA FLOOD & PETRIFICATION CLIMAX: [28.380s .. 30.850s] (100% ZERO HUD!) ---
        ("L10_CLUE",       30.920, c10a, "THAT IS THE CLUE",        "THE ROCK KEPT FOR 250M YRS","THE CLUE",   "#F7C35F"),
        ("L11_LOOP",       33.180, c10b, "THIS ROCK HOLDS",         "TWO ANIMALS.",            "TWO ANIMALS.", "#3AD4BE"),
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

    # Save isolated 1.000x dry VO stem
    dry_vo_path = f"{OUT_DIR}/dry_vo_karoo_v6.wav"
    sf.write(dry_vo_path, vo_bus, SR, subtype="PCM_24")

    # 3. Synthesize 14-Layer Dolby Physical Foley & Loop-Locked Harmonic Score
    score_bus = synth_loop_locked_score(dur_s=DURATION_S, base_hz=55.0) * 0.24
    duck_env = compute_lookahead_duck_envelope(vo_bus, lookahead_s=0.055)
    score_bus *= (1.0 - 0.64 * duck_env)[:, None]

    sfx_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)
    climax_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)

    # Opening cold-open sub-braaam (`0.05s`)
    place_clip(sfx_bus, synth_imax_braam(dur_s=1.65, root_hz=36.71), 0.05, gain=0.42)

    # Synchrotron X-Ray Tomography Laser Sweep (`2.60s` & reverse seal at `30.85s`)
    place_clip(sfx_bus, synth_laser_tomography_sweep(dur_s=1.45), 2.62, gain=0.28)
    place_clip(sfx_bus, synth_crystalline_ct_ping(1420.0, 0.55, pan=-0.25), 7.12, gain=0.20)
    place_clip(sfx_bus, synth_crystalline_ct_ping(1890.0, 0.55, pan=0.25),  8.52, gain=0.20)

    # Pre-Twist Vacuum Suction (`9.34s -> 10.21s`) -> Hard -240 dBFS Vacuum `[10.220s, 10.480s]`!
    VAC_T0, VAC_T1 = 10.220, 10.480
    place_clip(sfx_bus, synth_vacuum_suction(dur_s=0.86, seed=7701), VAC_T0 - 0.87, gain=0.38)

    # Post-Wait Twist Sub-Drop + Micro-CT Chronometer Ticks (`11.16s`)
    place_clip(sfx_bus, synth_imax_braam(dur_s=1.35, root_hz=41.20), 11.16, gain=0.40)
    place_clip(sfx_bus, synth_chronometer_ticks(dur_s=3.40, rate_hz=8.0), 12.85, gain=0.14)

    # 3 Healing Rib Callus Diagnostic Chimes (`13.45s, 14.15s, 14.85s`)
    for idx, rt in enumerate([13.45, 14.15, 14.85]):
        place_clip(sfx_bus, synth_crystalline_ct_ping(1640.0 + idx * 210.0, 0.48, pan=-0.15 + idx * 0.15), rt, gain=0.22)

    # 250-Million-Year Time-Rewind Transition (`17.95s`) + 6 Sandstone Crawl Steps (`18.55..20.85s`)
    place_clip(sfx_bus, synth_time_rewind_whoosh(dur_s=1.18, seed=250), 17.92, gain=0.36)
    for st_i, st_t in enumerate([18.65, 19.05, 19.48, 19.88, 20.32, 20.74]):
        place_clip(sfx_bus, synth_sandstone_crawl_step(seed=40 + st_i), st_t, gain=0.18, pan=-0.2 + 0.08 * st_i)

    # Dormant Aestivation Slow Heartbeat (`21.40s .. 25.20s`)
    place_clip(sfx_bus, synth_dormant_heartbeat(dur_s=3.80), 21.40, gain=0.34)

    # Monsoon Flash-Flood Surge & Petrification Climax (`25.85s .. 30.60s`, peak surge right in Pure-Cinema Climax `[28.38s..30.85s]`!)
    flood_sfx = synth_monsoon_flash_flood_climax(dur_s=5.00, seed=250000)
    place_clip(climax_bus, flood_sfx, 25.80, gain=0.88)
    place_clip(climax_bus, synth_imax_braam(dur_s=1.80, root_hz=32.70), 28.42, gain=0.72)

    # Synchrotron Lab Return Chime (`30.85s`)
    place_clip(sfx_bus, synth_laser_tomography_sweep(dur_s=1.05), 30.85, gain=0.24)

    # Duck non-climax SFX gently under VO while keeping Pure-Cinema Climax (`28.38..30.85s`) massive!
    sfx_bus *= (1.0 - 0.35 * duck_env)[:, None]

    pre_master = vo_bus * 1.08 + score_bus + sfx_bus + climax_bus

    # Carve strict -240 dBFS Pre-Twist Digital Vacuum `[10.220s, 10.480s]` across ALL buses!
    apply_vacuum_window(pre_master, VAC_T0, VAC_T1, taper_s=0.008)

    master_wav = f"{OUT_DIR}/master_mix_karoo_v6.wav"
    stats = master_ebu_r128_linear(pre_master, master_wav, target_i=-14.2, target_tp=-1.5)

    # Re-zero exact inner vacuum window post-loudnorm so WAV vacuum is pure 0.0 (-240 dBFS)!
    master_pcm, _ = sf.read(master_wav, dtype="float32", always_2d=True)
    apply_vacuum_window(master_pcm, VAC_T0 + 0.012, VAC_T1 - 0.012, taper_s=0.006)
    sf.write(master_wav, master_pcm, SR, subtype="PCM_24")

    vac_qa = [round(VAC_T0 + 0.025, 3), round(VAC_T1 - 0.025, 3)]  # [10.245, 10.455]
    vac_seg = master_pcm[int(vac_qa[0] * SR):int(vac_qa[1] * SR)]
    vac_db = 20.0 * math.log10(max(1e-12, float(np.sqrt(np.mean(vac_seg ** 2)))))
    peak_db = 20.0 * math.log10(max(1e-12, float(np.max(np.abs(master_pcm)))))
    print(f"[Audio Master] LUFS stats={stats['input_i']} -> -14.2 LUFS | Peak={peak_db:.2f} dBFS | Vacuum={vac_db:.1f} dBFS")

    # 4. Lock 12 Cinema Camera Shots (`0 .. 1080` exact frames @ 30fps)
    shots = [
        {"id": "S01_LAB_HOOK",          "f0":    0, "f1":   76, "set": "LAB",    "desc": "Hero Karoo sandstone burrow cast rotating on dark synchrotron stage"},
        {"id": "S02_LASER_TOMOGRAPHY",  "f0":   76, "f1":  209, "set": "LAB",    "desc": "Cyan-gold synchrotron laser curtain dissolves rock into X-ray amber, revealing curled mammal-relative skeleton"},
        {"id": "S03_DUAL_FOSSIL_ORBIT", "f0":  209, "f1":  307, "set": "LAB",    "desc": "Overhead-oblique orbital push showing Thrinaxodon & Broomistega skeletons side-by-side"},
        {"id": "S04_WAIT_VERTIGO",      "f0":  307, "f1":  385, "set": "LAB",    "desc": "Pre-twist -180 dBFS vacuum Hitchcock Vertigo dolly-zoom on 'Wait. They were not enemies.'"},
        {"id": "S05_HEALING_RIBS_MACRO","f0":  385, "f1":  487, "set": "LAB",    "desc": "Extreme micro-CT macro dive onto amphibian ribs #4-#6 glowing golden bone-callus fracture repairs"},
        {"id": "S06_NOT_A_HUNT",        "f0":  487, "f1":  545, "set": "LAB",    "desc": "Forensic skull-to-rib crane confirming zero predator tooth punctures"},
        {"id": "S07_TRIASSIC_SHELTER",  "f0":  545, "f1":  636, "set": "BURROW", "desc": "250M-year time rewind: injured amphibian crawls on 4 IK legs down sun-lit Triassic tunnel into cool shelter"},
        {"id": "S08_AESTIVATION_SLEEP", "f0":  636, "f1":  766, "set": "BURROW", "desc": "Close cutaway of dormant curled Thrinaxodon breathing slowly as amphibian settles peacefully beside it"},
        {"id": "S09_FLOOD_INRUSH",      "f0":  766, "f1":  852, "set": "BURROW", "desc": "Storm flashes outside; roaring muddy flash-flood surge crashes down burrow ramp"},
        {"id": "S10_CLIMAX_PETRIFY",    "f0":  852, "f1":  926, "set": "BURROW", "desc": "PROTECTED PURE-CINEMA CLIMAX (0% HUD): swirling sediment fills burrow & compacts into solid Karoo stone"},
        {"id": "S11_CLUE_KEPT",         "f0":  926, "f1":  995, "set": "LAB",    "desc": "Match-cut back to Synchrotron Lab as amber X-ray seals back into solid fossil rock"},
        {"id": "S12_SEAMLESS_LOOP",     "f0":  995, "f1": 1080, "set": "LAB",    "desc": "Smooth crane return to exact Frame 0 hero pose ('This rock holds two animals.')"},
    ]

    lock_data = {
        "project": "extinct-karoo-burrow-v6-ultra",
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
            [VAC_T0, 10.50],      # Pure silence vacuum beat before 'Wait.'
            [28.38, 30.86],       # Pure cinema flash-flood entombment & petrification climax!
        ],
        "lines": line_timings,
        "shots": shots,
        "captions": captions,
    }

    lock_path = f"{PROJECT_DIR}/voice-lock-karoo-v6.json"
    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump(lock_data, f, indent=2)

    write_srt_vtt(
        captions,
        f"{EXPORT_DIR}/Karoo-Burrow-V6-Ultra-Captions.srt",
        f"{EXPORT_DIR}/Karoo-Burrow-V6-Ultra-Captions.vtt",
    )
    print(f"[Gate 2 LOCKED] -> {lock_path} | 12 Shots | {TOTAL_FRAMES} Frames ({DURATION_S:.3f}s)")


if __name__ == "__main__":
    main()
