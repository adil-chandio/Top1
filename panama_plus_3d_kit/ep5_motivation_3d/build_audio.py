#!/usr/bin/env python3
"""
MONARCH® PANAMA-PLUS EP5 V3 (TABAHI EDITION) — PRECISION AUDIO & TIMELINE ENGINE
- Trims leading/trailing digital silence on vo/beat_01..10.wav
- Applies crisp pitch-safe atempo=1.08 for urgent viral short cadence (~3.4 wps)
- Measures exact phrase-onset timestamps inside Beat 3 (3 monolith slams) and Beat 7 (phone flip, journal open, 10:00 ink)
- Emits `timeline_synced.json` so every 3D animation, camera kick, and SFX lands 0-2 frames on the exact spoken word
- Mixes voice (+9 dB over bed), felt piano + sub-drone + nocturnal rain + Earshot/procedural SFX, mastered to -14.0 LUFS / -1.0 dBTP
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy import signal

KIT_DIR = Path(__file__).resolve().parent
EARSHOT_DIR = KIT_DIR / "assets" / "earshot_takes"
TIMELINE_IN = KIT_DIR / "timeline.json"
TIMELINE_OUT = KIT_DIR / "timeline_synced.json"
OUT_WAV = KIT_DIR / "master_audio.wav"
OUT_M4A = KIT_DIR / "master_audio.m4a"
SR = 48000
FPS = 30
TEMPO = 1.08


def load_wav_48k_mono(path: Path) -> np.ndarray:
    tmp = KIT_DIR / f"_tmp_{path.stem}.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(path), "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", str(tmp),
        ],
        check=True,
    )
    with wave.open(str(tmp), "rb") as wf:
        arr = np.frombuffer(wf.readframes(wf.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
    tmp.unlink(missing_ok=True)
    return arr


def process_vo_clip(src: Path, tempo: float = TEMPO, head_pad: float = 0.02) -> np.ndarray:
    tmp_tempo = KIT_DIR / f"_tmp_atempo_{src.stem}.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(src),
            "-af", f"atempo={tempo:.3f},highpass=f=75,acompressor=threshold=-18dB:ratio=3:attack=5:release=60",
            "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", str(tmp_tempo),
        ],
        check=True,
    )
    with wave.open(str(tmp_tempo), "rb") as wf:
        arr = np.frombuffer(wf.readframes(wf.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
    tmp_tempo.unlink(missing_ok=True)

    # Trim dead silence using 15ms RMS window
    win = int(SR * 0.015)
    rms = np.array([
        math.sqrt(float(np.mean(arr[i : i + win] ** 2)))
        for i in range(0, len(arr), win)
    ])
    peak = float(np.max(rms)) if len(rms) else 0.0
    thr = max(0.008, peak * 0.045)
    active = np.where(rms > thr)[0]
    if len(active) > 0:
        s0 = max(0, int(active[0] * win - head_pad * SR))
        s1 = min(len(arr), int((active[-1] + 1) * win + 0.03 * SR))
        arr = arr[s0:s1]

    # Gentle fade in/out 8ms to prevent clicks
    fade_n = min(int(0.008 * SR), len(arr) // 4)
    if fade_n > 1:
        arr[:fade_n] *= np.linspace(0.0, 1.0, fade_n)
        arr[-fade_n:] *= np.linspace(1.0, 0.0, fade_n)

    # Peak normalize individual VO line to uniform presence
    mx = float(np.max(np.abs(arr))) + 1e-9
    return arr / mx * 0.88


def detect_phrase_onsets(arr: np.ndarray, min_gap_s: float = 0.14) -> list[float]:
    win = int(SR * 0.02)
    rms = [
        math.sqrt(float(np.mean(arr[i : i + win] ** 2)))
        for i in range(0, len(arr), win)
    ]
    peak = max(rms) if rms else 0.0
    thr = max(0.01, peak * 0.085)
    min_gap_w = int(min_gap_s / 0.02)
    onsets: list[float] = []
    in_speech = False
    gap = 0
    for idx, val in enumerate(rms):
        if val > thr:
            if not in_speech:
                onsets.append(round(idx * 0.02, 3))
                in_speech = True
            gap = 0
        else:
            if in_speech:
                gap += 1
                if gap >= min_gap_w:
                    in_speech = False
    return onsets


def load_earshot(rel: str) -> np.ndarray | None:
    p = EARSHOT_DIR / rel
    return load_wav_48k_mono(p) if p.exists() else None


def synth_sub_boom(dur_s: float = 0.75, f0: float = 92.0, f1: float = 34.0) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    freq = f1 + (f0 - f1) * np.exp(-t * 7.5)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    sig = np.sin(phase) * np.exp(-t * 4.2) + 0.35 * np.tanh(2.5 * np.sin(phase * 0.5)) * np.exp(-t * 6.0)
    return sig / (np.max(np.abs(sig)) + 1e-9)


def synth_glass_shatter(dur_s: float = 0.65) -> np.ndarray:
    rng = np.random.default_rng(77)
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    sos = signal.butter(3, [1800 / (SR * 0.5), 9500 / (SR * 0.5)], btype="bandpass", output="sos")
    sh = signal.sosfilt(sos, noise) * np.exp(-t * 8.5)
    for k in range(14):
        off = int((k * 0.018 + (k % 3) * 0.009) * SR)
        if off < n:
            m = n - off
            lt = np.arange(m) / SR
            f = 2200 + (k * 487) % 4200
            sh[off:] += np.sin(2 * np.pi * f * lt) * np.exp(-lt * 22.0) * 0.28
    return sh / (np.max(np.abs(sh)) + 1e-9)


def synth_whoosh(dur_s: float = 0.42) -> np.ndarray:
    rng = np.random.default_rng(31)
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    env = np.sin(np.pi * t / dur_s) ** 1.4
    noise = rng.standard_normal(n)
    sos = signal.butter(2, [240 / (SR * 0.5), 2800 / (SR * 0.5)], btype="bandpass", output="sos")
    w = signal.sosfilt(sos, noise) * env
    return w / (np.max(np.abs(w)) + 1e-9)


def synth_heartbeat_ignition(dur_s: float = 0.90) -> np.ndarray:
    n = int(dur_s * SR)
    out = np.zeros(n)
    for hit_t, f in [(0.0, 72.0), (0.24, 96.0)]:
        idx = int(hit_t * SR)
        m = min(int(0.32 * SR), n - idx)
        if m > 0:
            lt = np.arange(m) / SR
            out[idx : idx + m] += np.sin(2 * np.pi * f * np.exp(-lt * 4.5) * lt) * np.exp(-lt * 10.0)
    # Warm golden shimmer tail
    t = np.arange(n) / SR
    out += (np.sin(2 * np.pi * 440 * t) * 0.14 + np.sin(2 * np.pi * 659.25 * t) * 0.10) * np.exp(-t * 3.0)
    return out / (np.max(np.abs(out)) + 1e-9)


def synth_felt_piano_and_rain(total_dur: float) -> np.ndarray:
    n_total = int(round(total_dur * SR))
    # Emotional progression: D minor -> C major -> Bb major7 -> A minor -> D minor/A open resolve
    chords = [
        (0.00, 0.25, [146.83, 220.00, 261.63, 349.23]),
        (0.25, 0.50, [130.81, 196.00, 246.94, 329.63]),
        (0.50, 0.78, [116.54, 174.61, 220.00, 349.23]),
        (0.78, 1.00, [146.83, 220.00, 293.66, 440.00]),
    ]
    bed = np.zeros(n_total, dtype=np.float64)
    for f0, f1, freqs in chords:
        s = int(f0 * n_total)
        e = min(n_total, int(f1 * n_total))
        lt = np.arange(e - s) / SR
        dur_c = max(0.2, (e - s) / SR)
        env = np.sin(np.pi * np.clip(lt / dur_c, 0, 1)) ** 0.38
        seg = np.zeros(e - s)
        for idx, f in enumerate(freqs):
            seg += np.sin(2 * np.pi * f * lt) * 0.20 + np.sin(2 * np.pi * (f * 0.5) * lt) * 0.14
            for beat_off in np.arange(0.0, dur_c, 1.85):
                at = beat_off + idx * 0.28
                if at < dur_c:
                    a0 = int(at * SR)
                    m = min(int(1.6 * SR), (e - s) - a0)
                    if m > 0:
                        pt = np.arange(m) / SR
                        seg[a0 : a0 + m] += np.sin(2 * np.pi * f * pt) * np.exp(-pt * 3.1) * 0.16
        bed[s:e] += seg * env

    sos = signal.butter(2, 1150.0 / (SR * 0.5), btype="lowpass", output="sos")
    bed = signal.sosfilt(sos, bed)

    # Continuous nocturnal rain & subtle warm air room-tone (never digital zero)
    rng = np.random.default_rng(505)
    rain = rng.standard_normal(n_total)
    sos_r = signal.butter(2, [340 / (SR * 0.5), 2600 / (SR * 0.5)], btype="bandpass", output="sos")
    rain = signal.sosfilt(sos_r, rain)
    rain = rain / (np.max(np.abs(rain)) + 1e-9) * 0.11

    out = bed / (np.max(np.abs(bed)) + 1e-9) * 0.85 + rain
    return out


def main() -> None:
    raw_tl = json.loads(TIMELINE_IN.read_text(encoding="utf-8"))
    beats_out = []
    voice_chunks = []
    cue_events: list[tuple[float, str, float, float, str]] = []

    cursor_s = 0.0
    for idx, b in enumerate(raw_tl["beats"]):
        vo_path = KIT_DIR / b["vo_file"]
        arr = process_vo_clip(vo_path, tempo=TEMPO, head_pad=(0.015 if idx == 0 else 0.04))
        dur_s = len(arr) / SR
        pause_s = float(b.get("pause_after", 0.08))
        start_s = round(cursor_s, 3)
        end_s = round(cursor_s + dur_s + pause_s, 3)
        onsets = detect_phrase_onsets(arr)

        beat_rec = {
            "id": b["id"],
            "tag": b["tag"],
            "caption": b["caption"],
            "start": start_s,
            "end": end_s,
            "vo_end": round(cursor_s + dur_s, 3),
            "start_frame": int(round(start_s * FPS)),
            "end_frame": int(round(end_s * FPS)),
            "phrase_offsets_s": onsets,
            "phrase_frames": [int(round((start_s + o) * FPS)) for o in onsets],
        }
        beats_out.append(beat_rec)

        pad_n = int(round(pause_s * SR))
        voice_chunks.append(arr)
        if pad_n > 0:
            voice_chunks.append(np.zeros(pad_n, dtype=np.float64))
        cursor_s = end_s

        # Build beat-locked frame-exact SFX events
        if b["id"] == "hook_shatter":
            cue_events.append((0.02, "glass_shatter", 0.56, 0.0, "hook_glass"))
            cue_events.append((0.00, "sub_boom", 0.68, 0.0, "hook_sub"))
        elif b["id"] == "khwaab_fade":
            cue_events.append((start_s, "whoosh", 0.42, -0.18, "gallery_whoosh"))
        elif b["id"] == "excuse_monoliths":
            # Snap 3 slams to exact measured phrase onsets inside Beat 3!
            # Expected: phrase 0 (~0.02s), phrase 1 (~0.95s), phrase 2 (~2.05s), phrase 3+ (~4.4s)
            p_times = [start_s + o for o in onsets]
            slam_1 = p_times[1] if len(p_times) > 1 else start_s + 0.95
            slam_2 = p_times[2] if len(p_times) > 2 else start_s + 2.15
            slam_3 = p_times[-1] if len(p_times) > 3 else start_s + 4.55
            beat_rec["slam_frames"] = [
                int(round(slam_1 * FPS)),
                int(round(slam_2 * FPS)),
                int(round(slam_3 * FPS)),
            ]
            for st, pan, lbl in [(slam_1, -0.25, "kal_se"), (slam_2, 0.0, "bas_ka_nahi"), (slam_3, 0.25, "zikr_band")]:
                cue_events.append((st, "knock/wood.wav", 0.56, pan, lbl))
                cue_events.append((st, "sub_boom", 0.52, 0.0, f"{lbl}_sub"))
        elif b["id"] == "sukoon_trap":
            cue_events.append((start_s, "whoosh", 0.36, 0.15, "window_cut"))
        elif b["id"] == "xray_ignition":
            cue_events.append((start_s + 0.05, "heartbeat", 0.62, 0.0, "xray_heart"))
            cue_events.append((start_s + 1.65, "glass_shatter", 0.46, 0.0, "cage_break"))
        elif b["id"] == "micro_promise":
            cue_events.append((start_s, "swish/bright.wav", 0.36, 0.0, "lamp_on"))
            cue_events.append((start_s + 0.10, "knock/wood.wav", 0.38, -0.15, "lamp_click"))
        elif b["id"] == "desk_ten_min":
            p_times = [start_s + o for o in onsets]
            t_flip = p_times[0] + 0.35 if p_times else start_s + 0.45
            t_book = p_times[2] if len(p_times) > 2 else start_s + 1.75
            t_ink = p_times[3] if len(p_times) > 3 else start_s + 2.95
            beat_rec["desk_frames"] = [
                int(round(t_flip * FPS)),
                int(round(t_book * FPS)),
                int(round(t_ink * FPS)),
            ]
            cue_events.append((t_flip, "knock/wood.wav", 0.60, 0.22, "phone_ulta"))
            cue_events.append((t_book, "swish/bright.wav", 0.38, -0.15, "journal_open"))
            cue_events.append((t_ink, "pro_hover_tick/ping.wav", 0.36, 0.0, "ten_min_ink"))
        elif b["id"] == "stairs_ascent":
            for si in range(5):
                cue_events.append((start_s + 0.15 + si * 0.55, "mallet/glock.wav", 0.34 + si * 0.03, (si - 2) * 0.14, f"step_{si+1}"))
        elif b["id"] == "monarch_portrait":
            cue_events.append((start_s, "sub_boom", 0.66, 0.0, "portrait_drop"))
        elif b["id"] == "loop_question":
            cue_events.append((start_s, "pro_pop_in/round.wav", 0.38, 0.0, "question_pop"))

    voice_bus = np.concatenate(voice_chunks)
    total_dur = round(len(voice_bus) / SR, 3)
    total_frames = int(round(total_dur * FPS))
    # Align final beat end_frame cleanly to total_frames
    beats_out[-1]["end"] = total_dur
    beats_out[-1]["end_frame"] = total_frames

    synced_tl = {
        "title": raw_tl["title"],
        "width": raw_tl["width"],
        "height": raw_tl["height"],
        "fps": FPS,
        "duration_sec": total_dur,
        "total_frames": total_frames,
        "beats": beats_out,
    }
    TIMELINE_OUT.write_text(json.dumps(synced_tl, indent=2), encoding="utf-8")

    n_total = len(voice_bus)
    sfx_L = np.zeros(n_total, dtype=np.float64)
    sfx_R = np.zeros(n_total, dtype=np.float64)

    synth_bank = {
        "sub_boom": synth_sub_boom(),
        "glass_shatter": synth_glass_shatter(),
        "whoosh": synth_whoosh(),
        "heartbeat": synth_heartbeat_ignition(),
    }
    earshot_cache: dict[str, np.ndarray] = {}

    for t_cue, kind, gain, pan, _lbl in cue_events:
        if kind in synth_bank:
            clip = synth_bank[kind]
        else:
            if kind not in earshot_cache:
                arr = load_earshot(kind)
                earshot_cache[kind] = arr if arr is not None else synth_sub_boom(0.32, 110.0, 50.0)
            clip = earshot_cache[kind]

        s_idx = max(0, int(round(t_cue * SR)))
        e_idx = min(n_total, s_idx + len(clip))
        if e_idx <= s_idx:
            continue
        lg = math.sqrt(0.5 * (1.0 - pan))
        rg = math.sqrt(0.5 * (1.0 + pan))
        seg = clip[: e_idx - s_idx] * gain
        sfx_L[s_idx:e_idx] += seg * lg
        sfx_R[s_idx:e_idx] += seg * rg

    bed = synth_felt_piano_and_rain(total_dur)[:n_total] * 0.25
    voice_env = np.convolve(np.abs(voice_bus), np.ones(int(0.16 * SR)) / int(0.16 * SR), mode="same")
    duck = 1.0 - 0.56 * np.clip(voice_env / 0.11, 0.0, 1.0)

    mix_L = voice_bus * 1.05 + sfx_L + bed * duck
    mix_R = voice_bus * 1.05 + sfx_R + bed * duck
    stereo = np.stack([mix_L, mix_R], axis=1)
    peak = float(np.max(np.abs(stereo))) + 1e-9
    if peak > 0.90:
        stereo *= 0.90 / peak

    raw_wav = KIT_DIR / "_raw_mix.wav"
    data = (np.clip(stereo, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(str(raw_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(data.tobytes())

    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(raw_wav),
            "-af", "highpass=f=30,lowshelf=g=1.4:f=95,loudnorm=I=-14.0:TP=-1.0:LRA=6.5,aresample=48000",
            "-ar", "48000", "-ac", "2", "-sample_fmt", "s16",
            str(OUT_WAV),
        ],
        check=True,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(OUT_WAV), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(OUT_M4A),
        ],
        check=True,
    )
    raw_wav.unlink(missing_ok=True)

    eb = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(OUT_M4A), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    ).stderr
    summ = eb.split("Summary:")[-1]
    lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))
    print(f"Master EP5 V3 Audio: {total_dur:.2f}s ({total_frames}f) | I={lufs:.1f} LUFS | TP={tp:.1f} dBTP")


if __name__ == "__main__":
    main()
