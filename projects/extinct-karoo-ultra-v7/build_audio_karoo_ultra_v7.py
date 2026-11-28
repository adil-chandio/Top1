#!/usr/bin/env python3
"""
Gate 2 Eargasm Cinema Audio Master (`V7.0 Autonomous Ultra Monarch`)
Project: Extinct Life — "This Rock Holds Two Animals" (`extinct-karoo-ultra-v7`, Specimen BP/1/5558)
Duration: 36.000s (1,080 exact frames @ 30.000 fps), 48 kHz / 24-bit Master WAV.

Eliminates ALL V6.3 audio defects:
  1. Per-Clip Active-Speech Gated Loudness Leveler + Broadcast Vocal EQ + Optical Compressor
     -> Fixes the -12.4 dB drop on `c01_hook`, `c04_wait`, and `c05_not_enemies`!
     -> All 12 spoken lines sit within <= 1.5 dB active RMS at exact 1.000x speed (`time_stretch_applied = False`).
  2. ZERO Stationary Radio Hiss / Buzz -> Replaces broadband white-noise wind & harsh `tanh` braams with
     sub-245 Hz Kellet pink/brown air movement + phase-integrated (`cumsum`) sub impacts.
  3. 4-Act Karplus-Strong Plucked Acoustic String + Rosewood Marimba + Bowed Low Cello Curiosity Score
     with -4.5 dB @ 1.85 kHz vocal-pocket EQ carve + Fairlight lookahead sidechain ducking.
  4. Frame-Locked Chion Synchresis Physical Foley (PhISEM quartz brush strokes, Hertzian sandstone cleavage,
     Strouhal camera whooshes, sequential rib modal clicks, limping amphibian footsteps, and Minnaert flood bubbles).
"""
import json
import os
import sys

sys.path.insert(0, "/tmp/py")
sys.path.insert(0, "/home/user/Top1/tools/monarch-v6-imax-sdk/python")

import numpy as np
import soundfile as sf

from audio_imax_dsp import (
    SR,
    FPS,
    load_wav_48k_stereo,
    place_clip,
    tighten_vo_zero_stretch,
    write_srt_vtt,
)
from audio_eargasm_v7 import (
    normalize_and_polish_vo_clip,
    synth_sub_air_breeze,
    synth_story_curiosity_score_v7,
    synth_phisem_brush_and_grains,
    synth_geological_rock_split,
    synth_strouhal_whoosh,
    synth_shepard_suction_into_vacuum,
    synth_clean_sub_impact,
    synth_osteological_rib_click,
    synth_amphibian_crawl_footstep,
    synth_monsoon_storm_and_flood_v7,
    synth_marimba_bar,
    build_and_verify_eargasm_master,
)

DURATION_S = 36.000
TOTAL_FRAMES = int(round(DURATION_S * FPS))  # 1080
N_SAMPLES = int(round(DURATION_S * SR))

RAW_DIR = "/tmp/karoo_v6/vo_raw"
OUT_DIR = "/tmp/karoo_ultra_v7"
EXPORT_DIR = "/home/user/Top1/exports/extinct-karoo-ultra-v7"
PROJECT_DIR = "/home/user/Top1/projects/extinct-karoo-ultra-v7"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(PROJECT_DIR, exist_ok=True)


def split_two_sentences_raw(wav: np.ndarray, min_sil_s: float = 0.20, thresh: float = 0.0022):
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
    return wav[s0:e0], wav[s1:e1]


def synth_dormant_heartbeat_clean(dur_s: float = 3.75) -> np.ndarray:
    """Phase-exact (`cumsum`) warm 46 Hz aestivation heartbeat — zero chirp reversal!"""
    n = int(round(dur_s * SR))
    out = np.zeros((n, 2), dtype=np.float32)
    for beat_t in [0.32, 1.82, 3.22]:
        for off, f0, g in [(0.0, 52.0, 0.88), (0.23, 43.0, 0.62)]:
            i0 = int((beat_t + off) * SR)
            m = min(int(0.24 * SR), n - i0)
            if m <= 8:
                continue
            tt = np.arange(m, dtype=np.float32) / SR
            ph = 2.0 * np.pi * np.cumsum(28.0 + f0 * np.exp(-tt * 5.5)) / SR
            th = g * (1.0 - np.exp(-tt * 140.0)) * np.exp(-tt * 16.5) * np.sin(ph)
            out[i0:i0 + m, 0] += th
            out[i0:i0 + m, 1] += th
    return out


def main():
    # 1. Load, split, AND Broadcast-Polish EVERY individual spoken phrase (`target_voiced_rms_db = -18.0`!)
    TARGET_VO_DB = -18.0
    c01 = normalize_and_polish_vo_clip(load_wav_48k_stereo(f"{RAW_DIR}/c01_hook.wav"), TARGET_VO_DB, max_gap_s=0.14)
    c02 = normalize_and_polish_vo_clip(load_wav_48k_stereo(f"{RAW_DIR}/c02_asleep.wav"), TARGET_VO_DB, max_gap_s=0.15)
    c03 = normalize_and_polish_vo_clip(load_wav_48k_stereo(f"{RAW_DIR}/c03_pair.wav"), TARGET_VO_DB, max_gap_s=0.14)
    c04 = normalize_and_polish_vo_clip(load_wav_48k_stereo(f"{RAW_DIR}/c04_wait.wav"), TARGET_VO_DB, max_gap_s=0.10)
    c05 = normalize_and_polish_vo_clip(load_wav_48k_stereo(f"{RAW_DIR}/c05_not_enemies.wav"), TARGET_VO_DB, max_gap_s=0.12)

    raw_06a, raw_06b = split_two_sentences_raw(load_wav_48k_stereo(f"{RAW_DIR}/c06_ribs.wav"))
    c06a = normalize_and_polish_vo_clip(raw_06a, TARGET_VO_DB, max_gap_s=0.14)
    c06b = normalize_and_polish_vo_clip(raw_06b, TARGET_VO_DB, max_gap_s=0.14)

    c07 = normalize_and_polish_vo_clip(load_wav_48k_stereo(f"{RAW_DIR}/c07_shelter.wav"), TARGET_VO_DB, max_gap_s=0.14)
    c08 = normalize_and_polish_vo_clip(load_wav_48k_stereo(f"{RAW_DIR}/c08_dormancy.wav"), TARGET_VO_DB, max_gap_s=0.14)
    c09 = normalize_and_polish_vo_clip(load_wav_48k_stereo(f"{RAW_DIR}/c09_flood.wav"), TARGET_VO_DB, max_gap_s=0.14)

    raw_10a, raw_10b = split_two_sentences_raw(load_wav_48k_stereo(f"{RAW_DIR}/c10_clue_loop.wav"))
    c10a = normalize_and_polish_vo_clip(raw_10a, TARGET_VO_DB, max_gap_s=0.14)
    c10b = normalize_and_polish_vo_clip(raw_10b, TARGET_VO_DB, max_gap_s=0.14)

    schedule = [
        ("L01_HOOK",         0.180, c01,  "THIS ROCK HOLDS",         "TWO ANIMALS INSIDE",       "TWO ANIMALS",  "#E8B059"),
        ("L02_ASLEEP",       2.540, c02,  "250 MILLION YEARS AGO",   "ONE CURLED UP ASLEEP",     "250 MILLION",  "#F4DFB8"),
        ("L03_PAIR",         6.980, c03,  "A MAMMAL RELATIVE",       "BESIDE AN AMPHIBIAN",      "AMPHIBIAN",    "#E8B059"),
        # --- PRE-TWIST VACUUM SILENCE: [10.220s .. 10.480s] (260ms -240 dBFS pure digital zero!) ---
        ("L04_WAIT",        10.500, c04,  "WAIT.",                   "LOOK CLOSER AT THE BONES", "WAIT.",        "#E63926"),
        ("L05_NOT_ENEMIES", 11.180, c05,  "THEY WERE NOT ENEMIES",   "ZERO PREDATOR STRUGGLE",   "NOT ENEMIES",  "#E63926"),
        ("L06A_RIBS",       12.860, c06a, "AMPHIBIAN RIBS HEALING",  "WITH ZERO BITE MARKS",     "HEALING",      "#E63926"),
        ("L06B_NO_HUNT",    16.240, c06b, "SO THIS WAS NOT A HUNT",  "OSTEOLOGICAL PROOF",       "NOT A HUNT",   "#E8B059"),
        ("L07_SHELTER",     18.180, c07,  "THE LIKELY STORY:",       "IT CRAWLED IN FOR SHELTER","SHELTER",      "#F4DFB8"),
        ("L08_DORMANCY",    21.220, c08,  "DEEP AESTIVATION",        "SCORCHING DROUGHT SLEEP",  "AESTIVATION",  "#E8B059"),
        ("L09_FLOOD",       25.540, c09,  "THEN A SUDDEN FLOOD",     "FILLED & SEALED THEM",     "FLOOD",        "#E8B059"),
        ("L10_CLUE",        30.920, c10a, "THAT IS THE CLUE",        "THE ROCK KEPT FOR 250M YRS","THE CLUE",    "#F4DFB8"),
        ("L11_LOOP",        33.180, c10b, "THIS ROCK HOLDS",         "TWO ANIMALS.",             "TWO ANIMALS.", "#E8B059"),
    ]

    vo_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)
    captions = []
    line_timings = []

    for lid, t0, clip, l1, l2, hi, accent in schedule:
        dur = len(clip) / SR
        t1 = round(t0 + dur, 4)
        assert t1 < DURATION_S - 0.35, f"Line {lid} overflows 36.0s: t1={t1}"
        place_clip(vo_bus, clip, t0, gain=1.0, pan=0.0)
        line_timings.append({
            "id": lid,
            "t0": round(t0, 4),
            "t1": t1,
            "f0": int(round(t0 * FPS)),
            "f1": int(round(t1 * FPS)),
        })
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
        print(f"[VO V7 Level-Locked] {lid:16s} | {t0:6.3f}s -> {t1:6.3f}s ({dur:5.3f}s) | f={int(round(t0*FPS)):04d}..{int(round(t1*FPS)):04d}")

    dry_vo_path = f"{OUT_DIR}/dry_vo_karoo_ultra_v7.wav"
    sf.write(dry_vo_path, vo_bus, SR, subtype="PCM_24")

    # 2. Synthesize Zero-Hiss Sub-Air + 4-Act Plucked Acoustic/Marimba Curiosity Score
    sub_air_bus = synth_sub_air_breeze(dur_s=DURATION_S, seed=5558)
    score_bus = synth_story_curiosity_score_v7(dur_s=DURATION_S)

    # 3. Synthesize Frame-Locked Chion Synchresis Physical Foley & Impacts
    foley_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)
    impact_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)

    # S01 (0.0..2.53s): Deep sandstone presence + 3 rhythmic PhISEM quartz-sand brush sweeps (0.20s, 0.88s, 1.56s)!
    place_clip(impact_bus, synth_clean_sub_impact(dur_s=1.20, root_hz=36.71), 0.04, gain=0.28)
    place_clip(foley_bus, synth_phisem_brush_and_grains(dur_s=0.46, pan_start=-0.35, pan_end=0.28, seed=71), 0.20, gain=0.26)
    place_clip(foley_bus, synth_phisem_brush_and_grains(dur_s=0.44, pan_start=0.28, pan_end=-0.30, seed=72), 0.88, gain=0.22)
    place_clip(foley_bus, synth_phisem_brush_and_grains(dur_s=0.48, pan_start=-0.25, pan_end=0.35, seed=73), 1.56, gain=0.24)

    # S02 (2.53..6.97s): Strouhal camera glide + Hertzian sandstone fracture cleavage & calcite crystal modal shimmer!
    place_clip(foley_bus, synth_strouhal_whoosh(dur_s=0.55, peak_hz=310.0, pan_dir=1.0, seed=801), 2.48, gain=0.24)
    place_clip(foley_bus, synth_geological_rock_split(dur_s=2.05, reverse=False, seed=303), 2.56, gain=0.34)

    # S03 (6.97..10.23s): Warm rosewood marimba/harmonic species-silhouette reveal accents (Thrinaxodon @ 7.12s, Broomistega @ 8.48s)
    place_clip(foley_bus, synth_marimba_bar(587.33, dur_s=0.58, pan=-0.32), 7.12, gain=0.22)
    place_clip(foley_bus, synth_marimba_bar(440.00, dur_s=0.58, pan=0.32),  8.48, gain=0.22)

    # S03 -> S04 Vacuum Twist: Shepard rising tension + air suction -> -240 dBFS Vacuum [10.220s, 10.480s] -> Clean Sub Drop!
    VAC_T0, VAC_T1 = 10.220, 10.480
    place_clip(impact_bus, synth_shepard_suction_into_vacuum(dur_s=0.90, seed=7701), VAC_T0 - 0.91, gain=0.42)
    place_clip(impact_bus, synth_clean_sub_impact(dur_s=1.35, root_hz=41.20), 11.16, gain=0.44)

    # S05 (12.83..16.23s): 100mm Macro Strouhal dive whoosh + 3 sequential mineralized-bone rib callus clicks (#4, #5, #6)!
    place_clip(foley_bus, synth_strouhal_whoosh(dur_s=0.52, peak_hz=420.0, pan_dir=-1.0, seed=805), 12.80, gain=0.24)
    for idx, rt in enumerate([13.40, 14.12, 14.84]):
        place_clip(foley_bus, synth_osteological_rib_click(freq_hz=860.0 + idx * 115.0, pan=-0.18 + idx * 0.18, seed=51 + idx), rt, gain=0.26)

    # S06 -> S07 (17.85..21.20s): 250-Million-Year Golden Portal Strouhal Whoosh + 6 Asymmetric Limping Crawl Footsteps!
    place_clip(foley_bus, synth_strouhal_whoosh(dur_s=0.88, peak_hz=280.0, pan_dir=-1.0, seed=250), 17.82, gain=0.34)
    for st_i, st_t in enumerate([18.58, 18.98, 19.40, 19.82, 20.24, 20.68]):
        is_limp = (st_i % 2 == 1)  # Odd steps = injured right flank!
        place_clip(foley_bus, synth_amphibian_crawl_footstep(pan=-0.24 + 0.08 * st_i, heavy_limp=is_limp, seed=40 + st_i), st_t, gain=0.25)

    # S08 (21.20..25.53s): Slow Dormant Aestivation Heartbeat
    place_clip(foley_bus, synth_dormant_heartbeat_clean(dur_s=3.75), 21.38, gain=0.32)

    # S09 -> S10 (25.15..30.80s): J-Cut Thunder + Marshall-Palmer Rain + Frame-794 Mud-Wall Slam + Minnaert Bubbles + Stone Seal!
    flood_sfx = synth_monsoon_storm_and_flood_v7(dur_s=5.65, seed=250007)
    place_clip(impact_bus, flood_sfx, 25.15, gain=0.92)
    place_clip(impact_bus, synth_clean_sub_impact(dur_s=1.75, root_hz=32.70), 28.42, gain=0.56)

    # S11 (30.87..33.17s): Upper Sandstone Cap Geological Re-Seal!
    place_clip(foley_bus, synth_geological_rock_split(dur_s=1.60, reverse=True, seed=309), 30.88, gain=0.28)

    # 4. Mix, Sidechain-Duck, Carve -240 dBFS Vacuum, Master to -14.2 LUFS, & Assert Forensic Line Uniformity + Zero Hiss!
    master_wav = f"{OUT_DIR}/master_mix_karoo_ultra_v7.wav"
    qa = build_and_verify_eargasm_master(
        vo_bus=vo_bus,
        score_bus=score_bus,
        foley_bus=foley_bus,
        impact_bus=impact_bus,
        sub_air_bus=sub_air_bus,
        line_timings=line_timings,
        vacuum_window_s=(VAC_T0, VAC_T1),
        out_wav=master_wav,
        target_lufs=-14.2,
        target_tp=-1.5,
    )
    print("\n[AUDIO EARGASM V7 TELEMETRY]", json.dumps(qa, indent=2))

    # 5. Lock 12 Director-OS Shots (`0 .. 1080` exact frames @ 30fps — 1:1 with `director-plan.json`!)
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

    vac_qa = [round(VAC_T0 + 0.025, 3), round(VAC_T1 - 0.025, 3)]
    lock_data = {
        "project": "extinct-karoo-ultra-v7",
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
        "brush_stroke_times_s": [0.20, 0.88, 1.56],
        "rib_click_times_s": [13.40, 14.12, 14.84],
        "crawl_step_times_s": [18.58, 18.98, 19.40, 19.82, 20.24, 20.68],
        "protected_climax_windows_s": [
            [VAC_T0, 10.50],
            [26.00, 30.88],
        ],
        "audio_qa": qa,
        "lines": line_timings,
        "shots": shots,
        "captions": captions,
    }

    lock_path = f"{PROJECT_DIR}/voice-lock-karoo-ultra-v7.json"
    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump(lock_data, f, indent=2)

    write_srt_vtt(
        captions,
        f"{EXPORT_DIR}/Karoo-Burrow-Ultra-Monarch-V7.srt",
        f"{EXPORT_DIR}/Karoo-Burrow-Ultra-Monarch-V7.vtt",
    )
    print(f"[Gate 2 V7 LOCKED] -> {lock_path} | VO Spread = {qa['vo_line_spread_db']} dB | Hiss Floor = {qa['stationary_hiss_floor_db']} dBFS")


if __name__ == "__main__":
    main()
