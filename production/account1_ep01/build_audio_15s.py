#!/usr/bin/env python3
"""Build frame-locked 15.000s (-14 LUFS) dark-cinema master soundtrack for EP01 PEHRA."""

import json
import math
import subprocess
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, resample_poly

BASE = Path(__file__).resolve().parent
VO_DIR = BASE / "vo"
OUT_DIR = BASE / "build"
SR = 48000
FPS = 30
DURATION = 15.0
TOTAL_SAMPLES = int(SR * DURATION)


def load_wav_48k(path: Path, t0: float = 0.0, t1: float | None = None) -> np.ndarray:
    sr, data = wavfile.read(str(path))
    if data.ndim > 1:
        data = data.mean(axis=1)
    if data.dtype == np.int16:
        x = data.astype(np.float64) / 32768.0
    elif data.dtype == np.int32:
        x = data.astype(np.float64) / 2147483648.0
    else:
        x = data.astype(np.float64)
    s0 = max(0, int(t0 * sr))
    s1 = len(x) if t1 is None else min(len(x), int(t1 * sr))
    x = x[s0:s1]
    if sr != SR:
        g = math.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g)
    # 18ms smooth fade in/out to eliminate clicks
    fade = min(int(0.018 * SR), len(x) // 4)
    if fade > 0:
        x[:fade] *= np.linspace(0.0, 1.0, fade)
        x[-fade:] *= np.linspace(1.0, 0.0, fade)
    return x


def filt(x: np.ndarray, kind: str, freq, order: int = 4) -> np.ndarray:
    sos = butter(order, freq, btype=kind, fs=SR, output="sos")
    return sosfilt(sos, x)


def place(buf: np.ndarray, sig: np.ndarray, start_s: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Place mono signal into stereo buffer [N, 2] with constant-power pan (-1..+1)."""
    idx = int(round(start_s * SR))
    if idx >= len(buf) or idx + len(sig) <= 0:
        return
    if idx < 0:
        sig = sig[-idx:]
        idx = 0
    end = min(len(buf), idx + len(sig))
    seg = sig[: end - idx] * gain
    angle = (pan + 1.0) * (math.pi / 4.0)
    buf[idx:end, 0] += seg * math.cos(angle)
    buf[idx:end, 1] += seg * math.sin(angle)


# -------------------- Physical Dark-Cinema Foley & Score Synthesis --------------------
def make_sub_impact(dur: float = 1.4, f_start: float = 92.0, f_end: float = 34.0, punch: float = 1.0) -> np.ndarray:
    rng = np.random.default_rng(101)
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Exponential pitch sweep sub boom
    phase = 2 * math.pi * (f_end * t + (f_start - f_end) * (1 - np.exp(-t * 9.0)) / 9.0)
    sub = np.sin(phase) * np.exp(-t * 2.8)
    sub2 = 0.35 * np.sin(2 * phase) * np.exp(-t * 5.5)
    # Transient thud body
    thud = filt(rng.standard_normal(len(t)), "lowpass", 220) * np.exp(-t * 24.0) * 0.55 * punch
    env = np.minimum(1.0, t / 0.004)
    return np.tanh((sub + sub2 + thud) * env * 1.3)


def make_dark_drone(dur: float = DURATION) -> tuple[np.ndarray, np.ndarray]:
    """Subtle Fincher/Fern dark bowed-cello atmospheric bed (never fights voice, ducks on silence)."""
    rng = np.random.default_rng(7)
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Deep D1 (36.7 Hz) + D2 (73.4 Hz) + A2 (110 Hz) slow dark tension harmonic bed
    lfo1 = 0.5 + 0.5 * np.sin(2 * math.pi * 0.14 * t)
    lfo2 = 0.5 + 0.5 * np.sin(2 * math.pi * 0.09 * t + 1.1)
    left = (
        0.48 * np.sin(2 * math.pi * 36.71 * t)
        + 0.34 * np.sin(2 * math.pi * 73.42 * t + 0.12 * np.sin(2 * math.pi * 0.3 * t))
        + 0.18 * lfo1 * np.sin(2 * math.pi * 110.0 * t)
        + 0.08 * lfo2 * np.sin(2 * math.pi * 174.61 * t)  # minor third F3 dark mystery
    )
    right = (
        0.48 * np.sin(2 * math.pi * 36.71 * t)
        + 0.34 * np.sin(2 * math.pi * 73.60 * t - 0.12 * np.sin(2 * math.pi * 0.27 * t))
        + 0.18 * lfo2 * np.sin(2 * math.pi * 110.25 * t)
        + 0.08 * lfo1 * np.sin(2 * math.pi * 174.45 * t)
    )
    # Cold night wind texture (only during outdoor shots 0..9.0s)
    wind_l = filt(rng.standard_normal(len(t)), "bandpass", [160, 620], order=3) * 0.14
    wind_r = filt(rng.standard_normal(len(t)), "bandpass", [180, 680], order=3) * 0.14
    outdoor_mask = np.clip((9.1 - t) / 0.6, 0.0, 1.0) * (0.65 + 0.35 * np.sin(2 * math.pi * 0.22 * t))
    left = filt(left, "lowpass", 340) + wind_l * outdoor_mask
    right = filt(right, "lowpass", 340) + wind_r * outdoor_mask

    # Deliberate silence notch right before padlock snap (6.65..6.90s) and before MONARCH (8.72..9.00s)
    duck = np.ones_like(t)
    duck *= 1.0 - 0.88 * np.exp(-((t - 6.78) / 0.14) ** 2)
    duck *= 1.0 - 0.82 * np.exp(-((t - 8.86) / 0.15) ** 2)
    # Smooth intro & resonant tail
    duck *= np.minimum(1.0, t / 0.25)
    duck *= np.clip((dur - t) / 0.55, 0.0, 1.0) ** 0.7
    return left * duck, right * duck


def make_metal_clack(seed: int = 12, bright: float = 1.0) -> np.ndarray:
    """Crisp mechanical rifle bolt / brass padlock snap."""
    rng = np.random.default_rng(seed)
    dur = 0.28
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Two-stage mechanical click-clack (38ms apart)
    hit1 = filt(rng.standard_normal(len(t)), "bandpass", [1400, 5200]) * np.exp(-t * 95.0)
    ring1 = (
        0.45 * np.sin(2 * math.pi * 1870 * t)
        + 0.32 * np.sin(2 * math.pi * 2940 * t)
        + 0.22 * np.sin(2 * math.pi * 4310 * t)
    ) * np.exp(-t * 42.0)
    t2 = np.maximum(0.0, t - 0.042)
    m2 = (t >= 0.042).astype(np.float64)
    hit2 = filt(rng.standard_normal(len(t)), "bandpass", [900, 4400]) * np.exp(-t2 * 70.0) * m2 * 1.25
    ring2 = (
        0.55 * np.sin(2 * math.pi * 1320 * t2)
        + 0.35 * np.sin(2 * math.pi * 2480 * t2)
        + 0.20 * np.sin(2 * math.pi * 3890 * t2)
    ) * np.exp(-t2 * 28.0) * m2 * bright
    body = filt(rng.standard_normal(len(t)), "bandpass", [220, 750]) * np.exp(-t2 * 55.0) * m2 * 0.6
    return np.tanh((hit1 + ring1 * 0.4 + hit2 + ring2 * 0.55 + body) * 1.4)


def make_iron_gate_creak(dur: float = 1.75) -> np.ndarray:
    """Eerie bowed wrought-iron hinge groan as gates swing open."""
    rng = np.random.default_rng(33)
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    f0 = 205 + 48 * np.sin(2 * math.pi * 0.75 * t) - 35 * (t / dur)
    phase = 2 * math.pi * np.cumsum(f0) / SR
    stick_slip = 0.65 + 0.35 * np.sin(2 * math.pi * 19.0 * t + 1.5 * np.sin(2 * math.pi * 3.1 * t))
    creak = (
        0.50 * np.sin(phase)
        + 0.32 * np.sin(2.01 * phase)
        + 0.20 * np.sin(3.47 * phase)
        + 0.14 * np.sin(5.12 * phase)
    ) * stick_slip
    scrape = filt(rng.standard_normal(len(t)), "bandpass", [400, 1800]) * 0.18
    env = np.sin(math.pi * np.clip(t / dur, 0, 1)) ** 0.75
    return filt((creak * 0.45 + scrape) * env, "bandpass", [150, 2600])


def make_boot_crunch(seed: int = 21) -> np.ndarray:
    """Heavy leather boot crunch on damp gravel/earth."""
    rng = np.random.default_rng(seed)
    dur = 0.26
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    heel = filt(rng.standard_normal(len(t)), "lowpass", 260) * np.exp(-t * 32.0) * 0.9
    grit = filt(rng.standard_normal(len(t)), "bandpass", [900, 3800]) * np.exp(-t * 22.0) * (
        0.5 + 0.5 * (rng.random(len(t)) > 0.72)
    )
    return (heel + grit * 0.65) * np.minimum(1.0, t / 0.005)


def make_reverse_riser(dur: float = 0.9) -> np.ndarray:
    rng = np.random.default_rng(55)
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    u = (t / dur) ** 2.6
    sweep = filt(rng.standard_normal(len(t)), "bandpass", [180, 2400]) * u * 0.55
    tone = np.sin(2 * math.pi * (110 + 210 * u) * t) * u * 0.35
    cut = np.clip((dur - t) / 0.015, 0.0, 1.0)
    return (sweep + tone) * cut


def make_whoosh(dur: float = 0.48, low: float = 120.0, high: float = 1600.0) -> np.ndarray:
    rng = np.random.default_rng(77)
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    env = np.sin(math.pi * t / dur) ** 1.8
    n = filt(rng.standard_normal(len(t)), "bandpass", [low, high], order=3)
    sub = np.sin(2 * math.pi * (95 - 40 * t / dur) * t) * env * 0.45
    return n * env * 0.85 + sub


def make_marble_chess_slam() -> np.ndarray:
    """Crisp polished stone-on-marble chess piece impact + pawn topple + cinema sub."""
    rng = np.random.default_rng(88)
    dur = 1.6
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Sharp stone click (solid marble modes)
    stone = (
        0.65 * np.sin(2 * math.pi * 920 * t) * np.exp(-t * 58.0)
        + 0.45 * np.sin(2 * math.pi * 1780 * t) * np.exp(-t * 75.0)
        + 0.30 * np.sin(2 * math.pi * 3120 * t) * np.exp(-t * 110.0)
        + filt(rng.standard_normal(len(t)), "bandpass", [600, 4200]) * np.exp(-t * 120.0) * 0.8
    )
    # Secondary pawn tip & two tiny marble bounces at +0.18s and +0.34s
    bounces = np.zeros_like(t)
    for bt, amp in [(0.19, 0.42), (0.35, 0.24), (0.46, 0.13)]:
        tb = np.maximum(0.0, t - bt)
        mb = (t >= bt).astype(np.float64)
        bounces += amp * mb * (
            np.sin(2 * math.pi * 1240 * tb) * np.exp(-tb * 70.0)
            + 0.5 * np.sin(2 * math.pi * 2380 * tb) * np.exp(-tb * 95.0)
        )
    sub = make_sub_impact(dur=dur, f_start=105.0, f_end=36.7, punch=1.15) * 0.82
    return np.tanh((stone * 0.9 + bounces + sub) * 1.2)


def make_clock_tick() -> np.ndarray:
    t = np.linspace(0, 0.08, int(SR * 0.08), endpoint=False)
    return (
        np.sin(2 * math.pi * 2150 * t) * np.exp(-t * 130.0) * 0.7
        + np.sin(2 * math.pi * 780 * t) * np.exp(-t * 90.0) * 0.4
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Voiceover placement (millisecond-aligned to natural internal phrase pauses)
    vo = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float64)
    b1 = load_wav_48k(VO_DIR / "beat_01.wav", 0.17, 5.08)  # 4.91s -> 0.10..5.01s
    b2 = load_wav_48k(VO_DIR / "beat_02.wav", 0.22, 3.63)  # 3.41s -> 5.30..8.71s
    b3 = load_wav_48k(VO_DIR / "beat_03.wav", 0.22, 5.13)  # 4.91s -> 9.15..14.06s

    # Normalize each VO line to uniform RMS so delivery feels rock-steady & authoritative
    for clip in (b1, b2, b3):
        rms = float(np.sqrt(np.mean(clip**2)) + 1e-9)
        clip *= 0.16 / rms

    place(vo, b1, 0.10, gain=1.0, pan=0.0)
    place(vo, b2, 5.30, gain=1.03, pan=0.0)
    place(vo, b3, 9.15, gain=1.02, pan=0.0)

    # 2. Dark atmospheric bed (stereo)
    sfx = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float64)
    dl, dr = make_dark_drone(DURATION)
    sfx[:, 0] += dl * 0.14
    sfx[:, 1] += dr * 0.14

    # 3. Frame-locked physical foley cues (every shot transition & physical action!)
    # S1 (0.00-2.40s): Frame-0 dark sub pulse + subtle lantern swing creak
    place(sfx, make_sub_impact(1.1, 82, 35, 0.8), 0.00, gain=0.28, pan=0.0)
    place(sfx, make_iron_gate_creak(0.65), 0.75, gain=0.045, pan=0.22)

    # S2 (2.40-5.20s): Cut to Royal Guards — deep transition + boots + crisp rifle lock
    place(sfx, make_whoosh(0.38, 110, 1200), 2.28, gain=0.18, pan=-0.12)
    place(sfx, make_boot_crunch(21), 2.42, gain=0.22, pan=-0.18)
    place(sfx, make_boot_crunch(22), 2.86, gain=0.17, pan=0.15)
    place(sfx, make_metal_clack(12, bright=1.0), 3.35, gain=0.24, pan=0.12)  # "bandook wale fauji"

    # S3 (5.20-6.90s): Close-up locked chain — tense ticks + reverse riser -> DEAD SILENCE -> SNAP!
    place(sfx, make_whoosh(0.32, 150, 1400), 5.08, gain=0.15, pan=0.0)
    place(sfx, make_clock_tick(), 5.55, gain=0.14, pan=-0.1)
    place(sfx, make_clock_tick(), 6.05, gain=0.16, pan=0.1)
    place(sfx, make_reverse_riser(0.62), 6.02, gain=0.16, pan=0.0)
    # 6.64..6.86s: CRISP DRAMATIC HUSH, then PADLOCK SNAPS OPEN AT Frame 206 (6.86s)!
    place(sfx, make_metal_clack(44, bright=1.35), 6.86, gain=0.36, pan=0.0)

    # S4 (6.90-9.00s): Iron Gates swing open into golden fog + guard walks away
    place(sfx, make_sub_impact(1.3, 88, 34, 0.9), 6.92, gain=0.28, pan=0.0)
    place(sfx, make_iron_gate_creak(1.65), 6.98, gain=0.14, pan=-0.15)
    place(sfx, make_boot_crunch(29), 7.95, gain=0.11, pan=0.35)
    place(sfx, make_boot_crunch(30), 8.52, gain=0.08, pan=0.45)

    # S5 (9.00-10.35s): Masked MONARCH reveal — dark velvet sub + crisp tick
    place(sfx, make_whoosh(0.42, 100, 1800), 8.88, gain=0.22, pan=0.0)
    place(sfx, make_sub_impact(1.1, 76, 33, 0.7), 9.00, gain=0.26, pan=0.0)

    # S6 (10.35-15.00s): Black Marble Chess Knight moves & SLAMS down at 12.00s (Frame 361)!
    place(sfx, make_whoosh(0.35, 160, 1500), 10.25, gain=0.16, pan=-0.1)
    place(sfx, make_reverse_riser(0.55), 11.42, gain=0.14, pan=0.0)
    place(sfx, make_marble_chess_slam(), 12.00, gain=0.40, pan=0.0)  # "is ek CHAAL ne"
    # Final resonant cliffhanger pulse at 14.15s fading cleanly to 15.00s
    place(sfx, make_sub_impact(0.85, 70, 32, 0.6), 14.12, gain=0.24, pan=0.0)

    # Sidechain-duck SFX slightly whenever voice speaks so Urdu narration is 100% razor-clear
    vo_env = np.abs(vo[:, 0])
    smooth_win = int(0.06 * SR)
    vo_env = np.convolve(vo_env, np.ones(smooth_win) / smooth_win, mode="same")
    duck_gain = 1.0 / (1.0 + 3.2 * vo_env)
    mix = vo * 1.15 + sfx * duck_gain[:, None]

    # Write clean 32-bit float raw WAVs then master through FFmpeg loudnorm (-14.0 LUFS, -1.0 dBTP)
    raw_wav = OUT_DIR / "mix_raw.wav"
    master_wav = OUT_DIR / "master_15s.wav"
    master_m4a = OUT_DIR / "master_15s.m4a"

    peak = float(np.max(np.abs(mix)) + 1e-9)
    mix_norm = (mix / max(peak, 1.0) * 0.88).astype(np.float32)
    wavfile.write(str(raw_wav), SR, mix_norm)

    # Warm broadcast voice EQ + EBU R128 loudness normalization to exact -14.0 LUFS / -1.0 dBTP
    af = (
        "highpass=f=28,"
        "equalizer=f=140:t=q:w=1.2:g=1.4,"
        "equalizer=f=3400:t=q:w=1.4:g=1.6,"
        "loudnorm=I=-14.0:TP=-1.0:LRA=9.0:linear=true,"
        f"apad=whole_dur={DURATION:.3f},atrim=0:{DURATION:.3f}"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw_wav), "-af", af, "-ar", "48000", "-ac", "2", str(master_wav)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(master_wav),
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
            "-t", f"{DURATION:.3f}", "-movflags", "+faststart",
            str(master_m4a),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    timeline = {
        "title": "MONARCH · EP01 — PEHRA (15s Dark 3D Cinema Preview)",
        "width": 1080,
        "height": 1920,
        "fps": FPS,
        "duration_sec": DURATION,
        "total_frames": int(DURATION * FPS),
        "shots": [
            {
                "id": "S1_MIDNIGHT_FURROW",
                "f_start": 1,
                "f_end": 72,
                "t_start": 0.00,
                "t_end": 2.40,
                "lookdev_frame": 38,
                "eyebrow": "PARIS · 1786",
                "caption": "Khet me sirf aaloo ugaye",
                "highlight": "aaloo",
            },
            {
                "id": "S2_ROYAL_GUARDS",
                "f_start": 73,
                "f_end": 156,
                "t_start": 2.40,
                "t_end": 5.20,
                "lookdev_frame": 116,
                "eyebrow": "SHAHI PEHRA",
                "caption": "Bahar bandook wale fauji",
                "highlight": "fauji",
            },
            {
                "id": "S3_LOCKED_IRON",
                "f_start": 157,
                "f_end": 207,
                "t_start": 5.20,
                "t_end": 6.90,
                "lookdev_frame": 196,
                "eyebrow": "ASLI WAJAH?",
                "caption": "Chori rokne ke liye nahi",
                "highlight": "nahi",
            },
            {
                "id": "S4_UNGUARDED_GATE",
                "f_start": 208,
                "f_end": 270,
                "t_start": 6.90,
                "t_end": 9.00,
                "lookdev_frame": 248,
                "eyebrow": "THE TWIST",
                "caption": "Taake log khud CHURA lein.",
                "highlight": "CHURA",
            },
            {
                "id": "S5_MASKED_MONARCH",
                "f_start": 271,
                "f_end": 310,
                "t_start": 9.00,
                "t_end": 10.35,
                "lookdev_frame": 292,
                "eyebrow": "MONARCH",
                "caption": "Ajeeb laga na?",
                "highlight": "Ajeeb",
            },
            {
                "id": "S6_MASTER_MOVE",
                "f_start": 311,
                "f_end": 450,
                "t_start": 10.35,
                "t_end": 15.00,
                "lookdev_frame": 372,
                "eyebrow": "EK CHAAL",
                "caption": "Poore mulk ki jaan bacha li.",
                "highlight": "jaan",
            },
        ],
    }
    tl_path = OUT_DIR / "timeline_15s.json"
    tl_path.write_text(json.dumps(timeline, indent=2))
    print(f"=== Audio mastered -> {master_m4a} ({DURATION:.3f}s, 450 frames) & {tl_path} ===")


if __name__ == "__main__":
    main()
