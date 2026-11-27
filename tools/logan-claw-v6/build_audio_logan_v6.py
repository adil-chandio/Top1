#!/usr/bin/env python3
"""
Logan — Rig-to-Render VFX Breakdown (`V6.2 Hollywood IMAX`)
Dolby-Style Trailer Sound Design & Multi-Stem Master Mix (`48 kHz / 24-bit` WAV):
  - Loop-locked D1 (`36.71 Hz`) + A1 (`55.00 Hz`) dark cello/brass harmonic tension score
  - Tactile cloth rustle, leather/knuckle tendon clench & precision viewport rig ticks
  - `-180 dBFS` Pre-SNIKT Acoustic Vacuum Silence (`2.70s .. 2.87s`, frames `81..86`)
  - Custom 3-Blade Staggered Surgical-Steel `SNIKT!` Unsheathe + Singing Katana Overtones (`f=87`)
  - Match-cut `<190 Hz` Dolby Sub-Braaams (`f=87, 168, 252, 336`) + Reverse Sheath Lock (`f=393`)
  - Two-pass linear EBU R128 mastering (`-14.2 LUFS`, `-1.5 dBFS` ceiling) + `.srt`/`.vtt` export
"""
import json
import math
import os
import sys

ROOT = "/home/user/Top1"
sys.path.insert(0, "/tmp/py")
sys.path.insert(0, os.path.join(ROOT, "tools/monarch-v6-imax-sdk/python"))

import numpy as np
from scipy import signal
import soundfile as sf

from audio_imax_dsp import (
    SR,
    apply_vacuum_window,
    fade_io,
    master_ebu_r128_linear,
    place_clip,
    synth_chronometer_ticks,
    synth_imax_braam,
    synth_loop_locked_score,
    synth_modal_impact,
    synth_vacuum_suction,
    write_srt_vtt,
)

LOCK_PATH = os.path.join(ROOT, "tools/logan-claw-v6/audio-lock-logan-v6.json")
TMP_DIR = "/tmp/logan_v6"
EXPORT_DIR = os.path.join(ROOT, "exports/logan-claw-rig-v6-imax")


def synth_cloth_and_fist_foley(dur_s: float = 2.65) -> np.ndarray:
    """Tactile heavy cotton/chambray sleeve rustle (`0.1..1.5s`) + knuckle/tendon fist clench (`1.95..2.58s`)."""
    rng = np.random.default_rng(4207)
    n = int(round(dur_s * SR))
    t = np.arange(n, dtype=np.float32) / SR

    # 1. Filtered fabric friction whoosh as arm sweeps across chest
    noise = rng.standard_normal(n).astype(np.float32)
    b1, a1 = signal.butter(2, [380.0 / (SR * 0.5), 3400.0 / (SR * 0.5)], btype="bandpass")
    cloth = signal.lfilter(b1, a1, noise)
    env_arm = np.exp(-((t - 0.78) / 0.46) ** 2) * 0.55 + np.exp(-((t - 1.55) / 0.28) ** 2) * 0.35
    cloth *= env_arm

    # 2. Tight leather/knuckle bone-tendon clench micro-impacts (1.98s .. 2.55s)
    clench = np.zeros(n, dtype=np.float32)
    for tc, f_low, amp in [(2.02, 145.0, 0.55), (2.11, 168.0, 0.65), (2.21, 132.0, 0.80), (2.34, 118.0, 0.72)]:
        i0 = int(tc * SR)
        m = min(int(0.085 * SR), n - i0)
        if m <= 0:
            continue
        tt = np.arange(m, dtype=np.float32) / SR
        crk = amp * np.exp(-tt * 65.0) * (
            0.7 * np.sin(2 * np.pi * (f_low * np.exp(-tt * 14.0) + 52.0) * tt)
            + 0.45 * np.exp(-tt * 220.0) * rng.standard_normal(m).astype(np.float32)
        )
        clench[i0:i0 + m] += crk

    b2, a2 = signal.butter(2, 2600.0 / (SR * 0.5), btype="lowpass")
    clench = signal.lfilter(b2, a2, clench)
    s = (cloth * 0.65 + clench * 0.95).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s * 0.96, np.roll(s, 14) * 1.04], axis=1), 0.02, 0.03)


def synth_adamantium_snikt(dur_s: float = 1.48) -> np.ndarray:
    """
    Iconic 3-Blade Staggered Adamantium `SNIKT!` Unsheathe:
      - Punchy flesh/knuckle sheath transient + sub impact
      - 3 staggered (`0 ms`, `11 ms`, `23 ms`) high-velocity dispersive steel-on-steel blade scrapes
      - Long crystalline surgical-steel modal katana resonance (`1.84..11.2 kHz`)
    """
    rng = np.random.default_rng(1974)
    n = int(round(dur_s * SR))
    t = np.arange(n, dtype=np.float32) / SR
    left = np.zeros(n, dtype=np.float32)
    right = np.zeros(n, dtype=np.float32)

    # 1. Sub-chest + knuckle burst thud
    thud = 1.15 * np.exp(-t * 24.0) * np.sin(2 * np.pi * (112.0 * np.exp(-t * 16.0) + 41.0) * t)
    left += thud
    right += thud

    # 2. Three staggered metallic blade ejections
    blade_offsets_s = [0.000, 0.011, 0.023]
    blade_pans = [-0.18, 0.04, 0.24]
    for bi, (off_s, pan) in enumerate(zip(blade_offsets_s, blade_pans)):
        i0 = int(round(off_s * SR))
        m = n - i0
        tt = np.arange(m, dtype=np.float32) / SR

        # Fast upward metallic scrape chirp (0..95 ms)
        scrape_env = np.exp(-tt * 28.0) * (1.0 - np.exp(-tt * 380.0))
        f_chirp = 1450.0 + 5200.0 * np.clip(tt / 0.085, 0.0, 1.0) ** 0.72 + bi * 210.0
        ph = 2 * np.pi * np.cumsum(f_chirp) / SR
        raw_n = rng.standard_normal(m).astype(np.float32)
        bp_b, bp_a = signal.butter(2, [2100.0 / (SR * 0.5), 11500.0 / (SR * 0.5)], btype="bandpass")
        hiss = signal.lfilter(bp_b, bp_a, raw_n) * np.exp(-tt * 34.0)

        # Steel lock click at ~58 ms when blade hits full mechanical stop
        lock_t = np.maximum(0.0, tt - 0.056)
        lock_click = (tt >= 0.056).astype(np.float32) * np.exp(-lock_t * 290.0) * (
            0.9 * np.sin(2 * np.pi * (3420.0 + bi * 180.0) * lock_t)
            + 0.65 * np.sin(2 * np.pi * (6890.0 + bi * 240.0) * lock_t)
        )

        # Singing hollow-ground steel blade modes
        modes = [
            (1842.0 + bi * 34.0, 3.8, 0.30),
            (3196.0 + bi * 52.0, 4.6, 0.26),
            (4980.0 + bi * 75.0, 5.8, 0.20),
            (7460.0 + bi * 110.0, 7.5, 0.14),
            (10850.0 + bi * 140.0, 10.5, 0.09),
        ]
        ring = np.zeros(m, dtype=np.float32)
        for freq, dec, amp in modes:
            ring += amp * (1.0 - np.exp(-tt * 120.0)) * np.exp(-tt * dec) * np.sin(2 * np.pi * freq * tt)

        sig = 0.52 * np.sin(ph) * scrape_env + 0.48 * hiss + 0.75 * lock_click + 0.85 * ring
        gl = math.cos((pan + 1.0) * math.pi * 0.25) * 1.4142
        gr = math.sin((pan + 1.0) * math.pi * 0.25) * 1.4142
        left[i0:] += sig * gl
        right[i0:] += sig * gr

    out = np.stack([left, right], axis=1).astype(np.float32)
    out /= (np.max(np.abs(out)) + 1e-9)
    return fade_io(out, 0.001, 0.14)


def synth_blade_edge_glint(dur_s: float = 1.25) -> np.ndarray:
    """Cold crystalline steel-edge light sweep for Shot 02B Macro Adamantium Reveal (`f=168`)."""
    n = int(round(dur_s * SR))
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    env = (1.0 - np.exp(-t * 32.0)) * np.exp(-t * 2.9)
    f_sweep = 2650.0 + 3800.0 * (u ** 0.85)
    ph = 2 * np.pi * np.cumsum(f_sweep) / SR
    s = env * (
        0.48 * np.sin(2 * np.pi * 2217.0 * t)
        + 0.36 * np.sin(2 * np.pi * 4435.0 * t * 1.001)
        + 0.24 * np.sin(ph) * np.exp(-t * 4.5)
    )
    s /= (np.max(np.abs(s)) + 1e-9)
    pan = np.linspace(-0.42, 0.48, n, dtype=np.float32)
    return fade_io(np.stack([s * (0.5 - 0.5 * pan), s * (0.5 + 0.5 * pan)], axis=1).astype(np.float32), 0.004, 0.16)


def synth_heartbeat_pulse(dur_s: float = 0.75) -> np.ndarray:
    """Deep visceral double heartbeat (`lub-dub` at `52 Hz` / `44 Hz`) for close-up portrait tension."""
    n = int(round(dur_s * SR))
    t = np.arange(n, dtype=np.float32) / SR
    lub = np.exp(-t * 18.0) * np.sin(2 * np.pi * (68.0 * np.exp(-t * 9.0) + 38.0) * t)
    t2 = np.maximum(0.0, t - 0.24)
    dub = (t >= 0.24).astype(np.float32) * 0.82 * np.exp(-t2 * 21.0) * np.sin(2 * np.pi * (58.0 * np.exp(-t2 * 9.0) + 34.0) * t2)
    s = (lub + dub).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, s], axis=1), 0.005, 0.10)


def synth_sheath_retract(dur_s: float = 0.52) -> np.ndarray:
    """Reverse metallic slide + mechanical lock click (`SHHK-CHK!`) at `f=393` loop reset."""
    rng = np.random.default_rng(993)
    n = int(round(dur_s * SR))
    t = np.arange(n, dtype=np.float32) / SR
    u = t / dur_s
    f_down = 5400.0 * np.exp(-u * 1.8) + 920.0
    ph = 2 * np.pi * np.cumsum(f_down) / SR
    bp_b, bp_a = signal.butter(2, [1200.0 / (SR * 0.5), 7600.0 / (SR * 0.5)], btype="bandpass")
    slide = signal.lfilter(bp_b, bp_a, rng.standard_normal(n).astype(np.float32)) * np.exp(-t * 9.5)
    lock_t = np.maximum(0.0, t - 0.18)
    lock = (t >= 0.18).astype(np.float32) * np.exp(-lock_t * 42.0) * np.sin(2 * np.pi * 135.0 * lock_t)
    s = (0.38 * np.sin(ph) * np.exp(-t * 10.0) + 0.45 * slide + 0.65 * lock).astype(np.float32)
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s * 1.02, np.roll(s, 8) * 0.98], axis=1), 0.003, 0.08)


def main():
    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(EXPORT_DIR, exist_ok=True)

    with open(LOCK_PATH, "r", encoding="utf-8") as f:
        lock = json.load(f)

    dur_s = float(lock["duration_s"])
    n_samples = int(round(dur_s * SR))
    vac_t0, vac_t1 = lock["vacuum_window_s"]

    # 1. Integer-cycle loop-locked dark cinema score (D1 = 36.71 Hz / A1 = 55.0 Hz)
    score_bus = synth_loop_locked_score(dur_s=dur_s, base_hz=36.71) * 0.44
    cello_sub = synth_loop_locked_score(dur_s=dur_s, base_hz=55.00) * 0.24
    music_bus = score_bus + cello_sub

    # 2. Viewport precision ticks & tactile foley stem
    sfx_bus = np.zeros((n_samples, 2), dtype=np.float32)
    place_clip(sfx_bus, synth_cloth_and_fist_foley(2.65), start_s=0.04, gain=0.42)
    place_clip(sfx_bus, synth_chronometer_ticks(2.55, rate_hz=10.0), start_s=0.10, gain=0.14)
    place_clip(sfx_bus, synth_vacuum_suction(0.88), start_s=1.81, gain=0.52)

    # Viewport inspection ticks during clay rig segments
    place_clip(sfx_bus, synth_chronometer_ticks(1.12, rate_hz=12.0), start_s=4.42, gain=0.15)
    place_clip(sfx_bus, synth_chronometer_ticks(1.32, rate_hz=10.0), start_s=7.02, gain=0.13)
    place_clip(sfx_bus, synth_chronometer_ticks(1.32, rate_hz=10.0), start_s=9.82, gain=0.14)

    # 3. Hero Match-Cut Transients & Dolby <190 Hz Sub-Braaams!
    # Shot 01B (f=87 -> 2.900s): EXPLOSIVE ADAMANTIUM SNIKT! + D1 Sub-Braaam
    place_clip(sfx_bus, synth_adamantium_snikt(1.48), start_s=2.900, gain=0.98)
    place_clip(sfx_bus, synth_imax_braam(1.55, root_hz=36.71), start_s=2.900, gain=0.86)

    # Shot 02B (f=168 -> 5.600s): Macro Blade Render Cut + Steel Glint + F1 Sub-Braaam
    place_clip(sfx_bus, synth_modal_impact(0.75, sub_hz=72.0), start_s=5.600, gain=0.56)
    place_clip(sfx_bus, synth_blade_edge_glint(1.25), start_s=5.600, gain=0.52)
    place_clip(sfx_bus, synth_imax_braam(1.25, root_hz=43.65), start_s=5.600, gain=0.68)

    # Shot 03B (f=252 -> 8.400s): 3/4 Profile Render Cut + Heartbeat + A1 Sub-Swell
    place_clip(sfx_bus, synth_heartbeat_pulse(0.82), start_s=8.400, gain=0.62)
    place_clip(sfx_bus, synth_imax_braam(1.30, root_hz=41.20), start_s=8.400, gain=0.64)

    # Shot 04B (f=336 -> 11.200s): Front Kubrick-Stare Climax Cut + Full D1 Dolby Braaam
    place_clip(sfx_bus, synth_modal_impact(0.95, modes=((920.0, 18.0), (1840.0, 24.0), (3680.0, 34.0)), sub_hz=64.0), start_s=11.200, gain=0.66)
    place_clip(sfx_bus, synth_imax_braam(1.75, root_hz=36.71), start_s=11.200, gain=0.94)
    place_clip(sfx_bus, synth_heartbeat_pulse(0.85), start_s=11.950, gain=0.48)

    # Shot 05 (f=393 -> 13.100s): Loop-Reset Sheath Retraction -> seamless bridge to f=0
    place_clip(sfx_bus, synth_sheath_retract(0.54), start_s=13.100, gain=0.48)

    # Combine stems & carve complete -180 dBFS Pre-SNIKT Vacuum Window [2.70s .. 2.87s]!
    pre_master = music_bus + sfx_bus
    apply_vacuum_window(pre_master, vac_t0, vac_t1, taper_s=0.012)

    # AAC pre-echo guard: the SNIKT transient at 2.900s is only 30ms after the vacuum
    # window closes. Lossy AAC's transform window smears that attack backwards into the
    # silence, lifting a measured -50.5 dBFS source to -38.9 dBFS in the muxed MP4 and
    # tripping the broadcast vacuum gate. Widen the digital black and soften the attack.
    pre_master[int(round((vac_t0 - 0.010) * SR)):int(round((vac_t1 + 0.010) * SR))] = 0.0
    attack_tap = int(round(0.022 * SR))
    a0 = int(round((vac_t1 + 0.010) * SR))
    pre_master[a0:a0 + attack_tap] *= np.linspace(0.0, 1.0, attack_tap, dtype=np.float32)[:, None]

    # Cross-fade tiny 12ms loop boundary on sfx_bus so sample[N-1] -> sample[0] never clicks
    loop_tap = int(0.015 * SR)
    w_end = np.linspace(1.0, 0.42, loop_tap, dtype=np.float32)[:, None]
    pre_master[-loop_tap:] *= w_end

    peak = float(np.max(np.abs(pre_master)))
    if peak > 0.92:
        pre_master *= (0.92 / peak)

    out_wav = os.path.join(TMP_DIR, "Logan-Claw-Rig-Master-Mix-V6-IMAX.wav")
    stats = master_ebu_r128_linear(pre_master, out_wav, target_i=-14.2, target_tp=-1.5)

    # Re-enforce exact digital zero inside inner [2.715s .. 2.855s] post-loudnorm filter tail!
    mastered, sr_out = sf.read(out_wav, dtype="float32", always_2d=True)
    assert len(mastered) == n_samples, f"Expected {n_samples} samples, got {len(mastered)}"
    apply_vacuum_window(mastered, vac_t0 + 0.002, vac_t1 - 0.002, taper_s=0.006)
    # Re-apply the AAC pre-echo guard after the loudnorm gain stage too, so the digital
    # black survives mastering and the leading edge cannot smear back into the window.
    mastered[int(round((vac_t0 - 0.006) * SR)):int(round((vac_t1 + 0.006) * SR))] = 0.0
    m0 = int(round((vac_t1 + 0.006) * SR))
    mtap = int(round(0.020 * SR))
    mastered[m0:m0 + mtap] *= np.linspace(0.0, 1.0, mtap, dtype=np.float32)[:, None]
    sf.write(out_wav, mastered, SR, subtype="PCM_24")

    i0, i1 = int(2.73 * SR), int(2.84 * SR)
    vac_rms = 20.0 * np.log10(np.sqrt(np.mean(mastered[i0:i1] ** 2)) + 1e-12)

    srt_path = os.path.join(EXPORT_DIR, "Logan-Claw-Rig-Captions-V6-IMAX.srt")
    vtt_path = os.path.join(EXPORT_DIR, "Logan-Claw-Rig-Captions-V6-IMAX.vtt")
    write_srt_vtt(lock["cues"], srt_path, vtt_path)

    print(f"[Audio V6 READY] {out_wav} | dur={len(mastered)/SR:.3f}s | loudnorm_in={stats['input_i']} LUFS | vac_rms={vac_rms:.1f} dBFS")


if __name__ == "__main__":
    main()
