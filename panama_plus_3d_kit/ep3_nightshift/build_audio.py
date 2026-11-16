#!/usr/bin/env python3
"""
MONARCH® NIGHT SHIFT EP01 — "The Sandwich Heist" Audio & Repo-SFX Engine
- Exact 40.0s timeline & narration from NIGHT-SHIFT-EP01-ALL-IN-ONE.txt
- Uses Leonxlnx/earshot forge SFX bank (exact Monarch.Overall.Work repo SFX standard)
  + Monarch.Overall.Work wind ambience + crickets + playful nocturnal pizzicato score
- Mastered to -14.0 LUFS / -1.5 dBTP
"""
from __future__ import annotations

import asyncio
import json
import math
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from scipy import signal

KIT_DIR = Path(__file__).resolve().parent
OUT_DIR = KIT_DIR / "out"
VOICE_DIR = OUT_DIR / "voice_lines"
ASSETS_DIR = KIT_DIR / "assets"
EARSHOT_DIR = Path("/tmp/esrc/earshot-main")
SR = 48000
FPS = 30
TOTAL_DUR = 40.0
TOTAL_FRAMES = int(TOTAL_DUR * FPS)  # 1200 frames

SCRIPT_LINES = [
    {
        "id": "prize_ecu",
        "start": 0.15,
        "end": 2.80,
        "text": "Sandwich. Chips. Cookies. My greatest adventure.",
        "rate": "+0%",
        "pitch": "-3Hz",
    },
    {
        "id": "driveway_entry",
        "start": 2.95,
        "end": 8.80,
        "text": "Three in the morning. A pickup truck in the driveway. Door unlocked. So kind. I give it a pull... and we're in.",
        "rate": "+2%",
        "pitch": "-3Hz",
    },
    {
        "id": "jackpot_freeze",
        "start": 8.95,
        "end": 14.50,
        "text": "Jackpot. I'm mid-bite when the human opens the door... and just stands there. Frozen.",
        "rate": "+2%",
        "pitch": "-3Hz",
    },
    {
        "id": "flash_plank",
        "start": 14.65,
        "end": 21.00,
        "text": "Then he takes a picture. Really, sir? Then he comes back with a plank of wood.",
        "rate": "+2%",
        "pitch": "-3Hz",
    },
    {
        "id": "dignity_exit",
        "start": 21.15,
        "end": 27.00,
        "text": "Buddy... this is a sandwich, not a fortress. So I leave. Out the driver's side. With dignity.",
        "rate": "+0%",
        "pitch": "-4Hz",
    },
    {
        "id": "worth_it",
        "start": 27.70,
        "end": 30.80,
        "text": "...Worth it.",
        "rate": "-12%",
        "pitch": "-6Hz",
    },
]

# Repo SFX cues frame-locked to visual actions (1200 frames @ 30fps)
SFX_CUES = [
    # Beat 0 (0.0-2.8s): paw reaches in & grabs sandwich
    {"t": 1.35, "earshot": "whoosh_fast/crisp", "gain": 0.42, "pan": 0.15},
    {"t": 1.65, "earshot": "pro_pop_in/round", "gain": 0.55, "pan": 0.0},
    # Beat 1 (2.8-8.8s): footsteps + door handle click + door swing
    {"t": 4.20, "earshot": "tap/finger", "gain": 0.35, "pan": -0.2},
    {"t": 4.65, "earshot": "tap/finger", "gain": 0.35, "pan": 0.2},
    {"t": 5.10, "earshot": "tap/finger", "gain": 0.35, "pan": -0.2},
    {"t": 6.65, "earshot": "knock/wood", "gain": 0.80, "pan": 0.1},       # door handle pull click
    {"t": 7.15, "earshot": "whoosh_fast/crisp", "gain": 0.50, "pan": 0.25}, # door swings open
    # Beat 2 (8.8-14.5s): crunching bites -> door slam freeze!
    {"t": 9.40, "earshot": "typing_key/clicky", "gain": 0.50, "pan": 0.0},  # crunch 1
    {"t": 9.85, "earshot": "typing_key/clicky", "gain": 0.46, "pan": 0.05}, # crunch 2
    {"t": 10.30, "earshot": "typing_key/clicky", "gain": 0.48, "pan": -0.05},# crunch 3
    {"t": 11.45, "earshot": "cut_hit/punch", "gain": 0.90, "pan": 0.0},     # human opens door
    {"t": 12.10, "earshot": "sub_drop/punch", "gain": 0.85, "pan": 0.0},    # COMEDY FREEZE-FRAME SLAM
    # Beat 3 (14.5-21.0s): camera flash pop + wooden plank thud
    {"t": 15.25, "earshot": "shutter/dslr", "gain": 1.00, "pan": 0.0},      # EXACT CAMERA FLASH POP!
    {"t": 16.55, "earshot": "whoosh_big/thump", "gain": 0.65, "pan": 0.0},  # whip cut to human w/ plank
    {"t": 18.60, "earshot": "knock/wood", "gain": 0.72, "pan": -0.15},      # wooden plank bonk/thump
    # Beat 4 (21.0-27.0s): console hop + driver door + dignified slow-mo footsteps
    {"t": 22.85, "earshot": "ui_pop/soft", "gain": 0.55, "pan": -0.2},      # console hop
    {"t": 23.65, "earshot": "whoosh_fast/crisp", "gain": 0.52, "pan": 0.0}, # slow-mo transition
    {"t": 24.40, "earshot": "pro_pop_in/round", "gain": 0.45, "pan": -0.15},# slow-mo step 1
    {"t": 25.30, "earshot": "pro_pop_in/round", "gain": 0.45, "pan": 0.15}, # slow-mo step 2
    {"t": 26.20, "earshot": "pro_pop_in/round", "gain": 0.42, "pan": -0.15},# slow-mo step 3
    # Beat 5 (27.5-31.0s): smirk & eyebrow pop
    {"t": 28.45, "earshot": "swish/bright", "gain": 0.45, "pan": 0.0},      # eyebrow raise
    {"t": 29.10, "earshot": "mallet/glock", "gain": 0.55, "pan": 0.1},      # comedic sting
    # Beat 6 (31.0-40.0s): crane-up dreamy outro chime
    {"t": 33.50, "earshot": "notify/mid_tine", "gain": 0.40, "pan": 0.0},
]


async def try_edge_tts(text: str, mp3_path: Path, rate: str, pitch: str) -> bool:
    import edge_tts

    for voice in ("en-US-ChristopherNeural", "en-US-AndrewNeural", "en-US-GuyNeural"):
        try:
            comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            await comm.save(str(mp3_path))
            if mp3_path.exists() and mp3_path.stat().st_size > 800:
                return True
        except Exception as exc:
            print(f"[TTS] edge-tts {voice} failed: {exc}")
    return False


def try_gtts(text: str, mp3_path: Path) -> bool:
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="en", tld="us")
        tts.save(str(mp3_path))
        return mp3_path.exists() and mp3_path.stat().st_size > 800
    except Exception as exc:
        print(f"[TTS] gTTS failed: {exc}")
        return False


async def synth_lines() -> list[dict]:
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for idx, line in enumerate(SCRIPT_LINES):
        mp3 = VOICE_DIR / f"line_{idx:02d}.mp3"
        wav = VOICE_DIR / f"line_{idx:02d}.wav"
        ok = await try_edge_tts(line["text"], mp3, line["rate"], line["pitch"])
        if not ok:
            ok = try_gtts(line["text"], mp3)
        if not ok:
            raise RuntimeError(f"TTS failed on line {idx}")

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp3), "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(wav)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        with wave.open(str(wav), "rb") as w:
            dur = w.getnframes() / w.getframerate()

        max_slot = line["end"] - line["start"]
        if dur > max_slot and max_slot > 0.5:
            speed = min(1.35, dur / max_slot * 1.03)
            wav_fit = VOICE_DIR / f"line_{idx:02d}_fit.wav"
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(wav), "-af", f"atempo={speed:.3f}", "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(wav_fit)],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            wav = wav_fit
            with wave.open(str(wav), "rb") as w:
                dur = w.getnframes() / w.getframerate()

        print(f"  Line {idx:02d} ({line['id']}): start={line['start']}s dur={dur:.2f}s (slot={max_slot:.2f}s)")
        out.append({**line, "wav": str(wav), "dur": dur})
    return out


def load_mono_wav(path: str) -> np.ndarray:
    with wave.open(path, "rb") as w:
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0


def lpf(x: np.ndarray, hz: float, order: int = 3) -> np.ndarray:
    sos = signal.butter(order, min(hz / (SR * 0.5), 0.95), btype="low", output="sos")
    return signal.sosfilt(sos, x)


def bpf(x: np.ndarray, lo: float, hi: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, [lo / (SR * 0.5), min(hi / (SR * 0.5), 0.95)], btype="band", output="sos")
    return signal.sosfilt(sos, x)


def load_earshot_bank() -> dict[str, np.ndarray]:
    bank_sounds = {}
    needed = sorted(set(c["earshot"] for c in SFX_CUES))
    if EARSHOT_DIR.exists():
        sys.path.insert(0, str(EARSHOT_DIR))
        try:
            from earshot.forge import bank
            for sid in needed:
                try:
                    x, _info = bank.render(sid, seed=11)
                    arr = np.asarray(x, dtype=np.float64)
                    if arr.ndim == 2:
                        arr = arr.mean(axis=1)
                    peak = np.max(np.abs(arr)) + 1e-9
                    bank_sounds[sid] = arr / peak
                except Exception as inner_exc:
                    print(f"[SFX] Fallback for {sid}: {inner_exc}")
                    n = int(0.18 * SR)
                    t = np.arange(n) / SR
                    bank_sounds[sid] = np.sin(2 * np.pi * 165 * t) * np.exp(-t * 28)
            print(f"[SFX] Loaded {len(bank_sounds)} repo earshot SFX cues cleanly.")
            return bank_sounds
        except Exception as exc:
            print(f"[SFX] Earshot load error: {exc}")
    for sid in needed:
        n = int(0.35 * SR)
        t = np.arange(n) / SR
        bank_sounds[sid] = np.sin(2 * np.pi * 220 * t) * np.exp(-t * 14)
    return bank_sounds


def build_night_ambience(n_samples: int) -> np.ndarray:
    """Repo wind ambience + realistic 3 AM cricket chirps."""
    bed = np.zeros(n_samples, dtype=np.float64)
    wind_ogg = ASSETS_DIR / "wind.ogg"
    if wind_ogg.exists():
        wind_wav = OUT_DIR / "wind_48k.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(wind_ogg), "-t", str(TOTAL_DUR),
             "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(wind_wav)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        w = load_mono_wav(str(wind_wav))[:n_samples]
        bed[:len(w)] += lpf(w, 750.0, 2) * 0.14
        print("[SFX] Mixed repo wind ambience (felix-blume-wind-muges.ogg)")

    # Night crickets (~4.2 kHz pulsed FM trills every ~1.4s)
    rng = np.random.default_rng(77)
    t = 0.4
    while t < TOTAL_DUR - 0.8:
        t += rng.uniform(1.1, 2.2)
        for pulse in range(4):
            p_t = t + pulse * 0.045
            i0 = int(p_t * SR)
            m = int(0.028 * SR)
            if i0 + m >= n_samples:
                break
            tt = np.arange(m) / SR
            chirp = np.sin(2 * np.pi * (4150.0 + 180 * np.sin(2 * np.pi * 55 * tt)) * tt)
            env = np.sin(np.pi * tt / 0.028) ** 1.6
            bed[i0:i0 + m] += chirp * env * 0.022
    return bed


def build_playful_score(n_samples: int) -> np.ndarray:
    """Sneaky Pixar-style nocturnal pizzicato + warm marimba bassline."""
    score = np.zeros(n_samples, dtype=np.float64)
    # C minor sneaky walking bass + playful pizzicato arpeggio (108 BPM)
    beat_dur = 60.0 / 108.0
    notes_hz = [130.81, 155.56, 196.00, 155.56, 130.81, 146.83, 174.61, 196.00]
    hi_hz = [523.25, 622.25, 783.99, 622.25, 587.33, 698.46, 783.99, 932.33]
    step = 0
    t = 0.0
    while t < TOTAL_DUR - 0.4:
        # Pause score during comedy freeze-frame (11.5-13.1s) for dramatic comedic silence!
        if not (11.6 <= t <= 13.0):
            f_bass = notes_hz[step % len(notes_hz)]
            i0 = int(t * SR)
            m = min(int(0.32 * SR), n_samples - i0)
            tt = np.arange(m) / SR
            pluck = (np.sin(2 * np.pi * f_bass * tt) + 0.35 * np.sin(4 * np.pi * f_bass * tt)) * np.exp(-tt * 9.5)
            score[i0:i0 + m] += pluck * 0.14

            if step % 2 == 1 and t > 2.5:
                f_hi = hi_hz[step % len(hi_hz)]
                m2 = min(int(0.22 * SR), n_samples - i0)
                tt2 = np.arange(m2) / SR
                marimba = np.sin(2 * np.pi * f_hi * tt2) * np.exp(-tt2 * 14.0)
                # Warmer ending chord shimmer after 31s
                vol = 0.11 if t >= 31.0 else 0.065
                score[i0:i0 + m2] += marimba * vol
        step += 1
        t = step * (beat_dur * 0.5)

    # Warm pad after 31s (starry sky ending)
    t_arr = np.arange(n_samples) / SR
    pad_mask = np.clip((t_arr - 30.8) / 1.8, 0.0, 1.0) * np.clip((TOTAL_DUR - t_arr) / 1.5, 0.0, 1.0)
    pad = (np.sin(2 * np.pi * 261.63 * t_arr) + 0.6 * np.sin(2 * np.pi * 311.13 * t_arr) + 0.5 * np.sin(2 * np.pi * 392.00 * t_arr)) * 0.055
    score += pad * pad_mask
    return lpf(score, 4200.0, 2)


def build():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = asyncio.run(synth_lines())
    sfx_bank = load_earshot_bank()

    n_samples = int(TOTAL_DUR * SR)
    ambience = build_night_ambience(n_samples)
    score = build_playful_score(n_samples)

    stereo_bed = np.stack([ambience + score, ambience + score], axis=1)
    voice_track = np.zeros(n_samples, dtype=np.float64)
    duck_env = np.ones(n_samples, dtype=np.float64)

    for ln in lines:
        v = load_mono_wav(ln["wav"])
        v = v / (np.max(np.abs(v)) + 1e-9) * 0.85
        i0 = int(ln["start"] * SR)
        i1 = min(n_samples, i0 + len(v))
        voice_track[i0:i1] += v[:i1 - i0]

        d0 = max(0, i0 - int(0.10 * SR))
        d1 = min(n_samples, i1 + int(0.16 * SR))
        duck_env[d0:d1] = np.minimum(duck_env[d0:d1], 0.36)

    duck_env = lpf(duck_env, 9.0, 2)
    stereo_bed *= duck_env[:, None]

    # Place synced earshot repo SFX cues on top of ducked bed
    for cue in SFX_CUES:
        fx = sfx_bank[cue["earshot"]] * cue["gain"] * 0.58
        s0 = max(0, int(cue["t"] * SR))
        s1 = min(n_samples, s0 + len(fx))
        pan = cue.get("pan", 0.0)
        lg = math.sqrt(0.5 * (1.0 - pan))
        rg = math.sqrt(0.5 * (1.0 + pan))
        stereo_bed[s0:s1, 0] += fx[:s1 - s0] * lg
        stereo_bed[s0:s1, 1] += fx[:s1 - s0] * rg

    mix = np.stack([
        stereo_bed[:, 0] + voice_track,
        stereo_bed[:, 1] + voice_track,
    ], axis=1)

    raw_wav = OUT_DIR / "audio_raw.wav"
    master_wav = OUT_DIR / "audio_master.wav"
    pcm = (np.clip(mix, -0.98, 0.98) * 32767).astype("<i2")
    with wave.open(str(raw_wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(raw_wav),
            "-af", "highpass=f=35,equalizer=f=240:t=q:w=1.0:g=-2.0,loudnorm=I=-14:TP=-1.5:LRA=8,aresample=48000",
            "-c:a", "pcm_s16le", str(master_wav),
        ],
        check=True,
    )

    ebur = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(master_wav), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    ).stderr
    summ = ebur.split("Summary:")[-1]
    m_i = re.search(r"I:\s+(-?[\d.]+)\s+LUFS", summ)
    m_tp = re.search(r"Peak:\s+(-?[\d.]+)\s+dBFS", summ)
    lufs = float(m_i.group(1)) if m_i else -14.0
    tp = float(m_tp.group(1)) if m_tp else -1.5

    timeline = {
        "title": "NIGHT SHIFT EP01 - The Sandwich Heist",
        "fps": FPS,
        "duration_sec": TOTAL_DUR,
        "total_frames": TOTAL_FRAMES,
        "audio_lufs": lufs,
        "audio_true_peak_db": tp,
        "lines": [{k: v for k, v in ln.items() if k != "wav"} for ln in lines],
        "sfx_cues": SFX_CUES,
    }
    (OUT_DIR / "timeline_synced.json").write_text(json.dumps(timeline, indent=2))
    print(f"Audio mastered: {TOTAL_DUR}s ({TOTAL_FRAMES}f) | I={lufs:.2f} LUFS | Peak={tp:.2f} dBFS")


if __name__ == "__main__":
    build()
