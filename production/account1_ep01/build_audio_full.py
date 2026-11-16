#!/usr/bin/env python3
"""Build the full-script Urdu soundtrack for EP01 PEHRA.

The 15-second master placed three hand-timed lines. This one is timeline
driven: every narration clip in ``vo_full/`` goes where ``timeline_full.json``
says it goes, and each beat gets its own foley cue.

Output is an EBU R128 master at exactly -14.0 LUFS / -1.0 dBTP, stereo 48 kHz,
frame-locked to the same timeline the renderer reads.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from build_audio_15s import (  # noqa: E402
    SR,
    filt,
    load_wav_48k,
    make_boot_crunch,
    make_clock_tick,
    make_dark_drone,
    make_iron_gate_creak,
    make_marble_chess_slam,
    make_metal_clack,
    make_reverse_riser,
    make_sub_impact,
    make_whoosh,
    place,
)

VO_DIR = BASE / "vo_full"
OUT_DIR = BASE / "build"


def load_timeline(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# Per-beat foley. Keys are shot ids; values are (builder, offset within beat, gain, pan).
# Offsets are relative to the beat start so a retimed timeline stays in sync.
CUE_MAP = {
    "B01_AERIAL_FIELD": [
        ("sub_swell", 0.05, 0.24, 0.0),
        ("creak", 1.20, 0.05, 0.24),
        ("boot", 2.10, 0.13, -0.20),
    ],
    "B02_GUARDED_FIELD": [
        ("whoosh", 0.02, 0.16, -0.14),
        ("boot", 0.35, 0.20, -0.22),
        ("metal", 1.05, 0.22, 0.14),
        ("boot", 1.70, 0.15, 0.20),
        ("metal", 2.35, 0.18, -0.10),
    ],
    "B03_MASKED_TITLE": [
        ("whoosh", 0.02, 0.22, 0.0),
        ("sub_swell", 0.10, 0.28, 0.0),
        ("gate_slam", 3.10, 0.30, 0.0),
    ],
    "B04_HUNGRY_PARIS": [
        ("whoosh", 0.02, 0.12, 0.10),
        ("sub_swell", 0.60, 0.16, 0.0),
    ],
    "B05_POTATO_PROMISE": [
        ("tick", 0.40, 0.13, -0.12),
        ("tick", 1.10, 0.11, 0.12),
        ("whoosh", 0.02, 0.12, 0.0),
    ],
    "B06_POISONED_MIND": [
        ("metal", 0.55, 0.16, -0.16),
        ("boot", 1.30, 0.16, 0.18),
        ("sub_swell", 0.10, 0.14, 0.0),
    ],
    "B07_FREE_BASKETS": [
        ("whoosh", 0.02, 0.12, -0.10),
        ("boot", 1.05, 0.14, -0.24),
        ("boot", 2.20, 0.12, 0.24),
    ],
    "B08_SILENT_PIVOT": [
        ("hush", 0.02, 0.20, 0.0),
        ("tick", 1.20, 0.18, -0.14),
        ("tick", 2.35, 0.16, 0.14),
    ],
    "B09_FORTY_ACRES": [
        ("whoosh", 0.02, 0.18, 0.0),
        ("metal", 0.70, 0.20, 0.0),
        ("sub_swell", 1.40, 0.20, 0.0),
    ],
    "B10_WHISPERS": [
        ("whoosh", 0.02, 0.12, 0.14),
        ("riser", 1.10, 0.13, 0.0),
        ("sub_swell", 2.20, 0.15, 0.0),
    ],
    "B11_LAST_ORDER": [
        ("tick", 0.30, 0.10, 0.0),
        ("tick", 0.95, 0.12, 0.0),
        ("sub_swell", 0.05, 0.16, 0.0),
    ],
    "B12_SUNSET_WITHDRAWAL": [
        ("whoosh", 0.02, 0.14, 0.0),
        ("boot", 0.55, 0.12, 0.26),
        ("boot", 1.30, 0.10, -0.30),
        ("creak", 2.30, 0.12, -0.18),
    ],
    "B13_NIGHT_THEFT": [
        ("whoosh", 0.02, 0.18, 0.0),
        ("boot", 0.40, 0.18, -0.22),
        ("boot", 0.95, 0.16, 0.20),
        ("riser", 1.85, 0.12, 0.0),
    ],
    "B14_EMPTY_FIELD_DAWN": [
        ("sub_swell", 0.05, 0.20, 0.0),
        ("whoosh", 2.10, 0.12, 0.0),
    ],
    "B15_GRAVE_200_YEARS": [
        ("whoosh", 0.02, 0.10, -0.10),
        ("sub_swell", 0.80, 0.14, 0.0),
    ],
    "B16_FINAL_MONARCH": [
        ("sub_swell", 0.05, 0.22, 0.0),
        ("gate_slam", 0.0, 0.34, 0.0),
        ("final_pulse", 0.0, 0.20, 0.0),
    ],
}


def build_cue(name: str, beat_dur: float, slam_at: float | None) -> tuple[np.ndarray, float]:
    """Return (signal, start_offset_within_beat)."""
    if name == "sub_swell":
        return make_sub_impact(1.4, 92, 34, 1.0), 0.0
    if name == "whoosh":
        return make_whoosh(0.42, 120, 1600), 0.0
    if name == "boot":
        return make_boot_crunch(21), 0.0
    if name == "metal":
        return make_metal_clack(12, bright=1.0), 0.0
    if name == "creak":
        return make_iron_gate_creak(1.55), 0.0
    if name == "tick":
        return make_clock_tick(), 0.0
    if name == "riser":
        return make_reverse_riser(0.85), 0.0
    if name == "gate_slam":
        # A full-size iron gate: marble-slam body plus a sub and a metal snap.
        body = make_marble_chess_slam() * 0.9
        sub = make_sub_impact(1.6, 68, 28, 1.3) * 0.85
        return np.tanh((body + sub) * 1.1), 0.0
    if name == "final_pulse":
        return make_sub_impact(1.6, 62, 26, 1.0), 0.0
    if name == "hush":
        # Deliberate near-silence: a thin high ring instead of a hit.
        t = np.linspace(0, 0.9, int(SR * 0.9), endpoint=False)
        return (np.sin(2 * math.pi * 3200 * t) * np.exp(-t * 6.0) * 0.25), 0.0
    raise KeyError(name)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default=str(BASE / "build" / "timeline_full.json"))
    ap.add_argument("--out", default=str(OUT_DIR / "master_full.m4a"))
    ap.add_argument("--vo-dir", default=str(VO_DIR))
    args = ap.parse_args()

    timeline = load_timeline(Path(args.timeline))
    shots = timeline["shots"]
    duration = float(timeline["duration_sec"])
    total_samples = int(round(SR * duration))
    vo_dir = Path(args.vo_dir)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- 1. narration -------------------------------------------------------
    vo = np.zeros((total_samples, 2), dtype=np.float64)
    placed = 0
    for shot in shots:
        clip_name = shot.get("vo")
        if not clip_name:
            continue
        path = vo_dir / f"{clip_name}.wav"
        if not path.exists():
            print(f"  [skip] {shot['id']}: {path.name} not generated yet")
            continue
        clip = load_wav_48k(path)
        rms = float(np.sqrt(np.mean(clip ** 2)) + 1e-9)
        clip *= 0.155 / rms          # uniform, authoritative delivery
        place(vo, clip, float(shot["vo_start"]), gain=1.0, pan=0.0)
        placed += 1
    print(f"=== narration placed: {placed}/{len(shots)} beats ===")

    # --- 2. atmospheric bed --------------------------------------------------
    sfx = np.zeros((total_samples, 2), dtype=np.float64)
    dl, dr = make_dark_drone(duration)
    sfx[:, 0] += dl * 0.13
    sfx[:, 1] += dr * 0.13

    # --- 3. per-beat foley ---------------------------------------------------
    for shot in shots:
        cues = CUE_MAP.get(shot["id"], [])
        t0 = float(shot["t_start"])
        beat_dur = float(shot["t_end"]) - t0
        for name, offset, gain, pan in cues:
            sig, extra = build_cue(name, beat_dur, None)
            if name == "gate_slam":
                if shot["id"] == "B16_FINAL_MONARCH":
                    # Land the slam on the frame the gate actually closes.
                    offset = max(0.0, beat_dur - 24 / 30.0)
                else:
                    offset = max(0.0, beat_dur - 8 / 30.0)
            if name == "final_pulse":
                offset = max(0.0, beat_dur - 4 / 30.0)
            place(sfx, sig, t0 + offset + extra, gain=gain, pan=pan)

    # --- 4. duck the bed under speech ---------------------------------------
    vo_env = np.abs(vo[:, 0])
    win = int(0.06 * SR)
    vo_env = np.convolve(vo_env, np.ones(win) / win, mode="same")
    duck = 1.0 / (1.0 + 3.4 * vo_env)
    mix = vo * 1.15 + sfx * duck[:, None]

    raw = OUT_DIR / "mix_full_raw.wav"
    peak = float(np.max(np.abs(mix)) + 1e-9)
    from scipy.io import wavfile

    wavfile.write(str(raw), SR, (mix / max(peak, 1.0) * 0.88).astype(np.float32))

    # --- 5. master to -14.0 LUFS / -1.0 dBTP ---------------------------------
    master_wav = OUT_DIR / "master_full.wav"
    out = Path(args.out)
    af = (
        "highpass=f=28,"
        "equalizer=f=180:t=q:w=1.0:g=1.4,"
        "equalizer=f=3200:t=q:w=1.1:g=1.8,"
        "equalizer=f=7600:t=q:w=1.0:g=0.9,"
        "acompressor=threshold=0.16:ratio=2.6:attack=16:release=190,"
        "loudnorm=I=-14.0:TP=-1.0:LRA=9:print_format=summary"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw),
         "-af", af, "-ar", "48000", "-ac", "2", str(master_wav)],
        check=True,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(master_wav),
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2", str(out)],
        check=True,
    )
    print(f"=== FULL MASTER -> {out} ({duration:.3f}s, "
          f"{timeline['total_frames']} frames, -14.0 LUFS) ===")


if __name__ == "__main__":
    main()
