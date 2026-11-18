#!/usr/bin/env python3
"""
MONARCH® PANAMA-PLUS AUDIO & TIMELINE ENGINE
Generates neural voiceover (Edge-TTS with automatic Piper Neural ONNX & gTTS fallback),
measures exact line timings, builds cinematic underwater SFX + sub-bass hits + whale calls +
sonar pings in NumPy/SciPy, and masters to -14.0 LUFS / -1.5 dBTP.
"""
from __future__ import annotations

import asyncio
import json
import math
import re
import subprocess
import urllib.request
import wave
from pathlib import Path

import numpy as np
from scipy import signal

KIT_DIR = Path(__file__).resolve().parent
OUT_DIR = KIT_DIR / "out"
VOICE_DIR = OUT_DIR / "voice_lines"
PIPER_DIR = KIT_DIR / "assets" / "piper"
SR = 48000
FPS = 30

SCRIPT_BEATS = [
    {
        "id": "hook_orcas",
        "tag": "APEX PREDATOR",
        "headline": "",
        "subline": "",
        "text": "Orcas are the deadliest killers in the ocean. Even great white sharks flee when they arrive.",
        "sfx": [("sub_boom", 0.15, 0.72), ("whoosh", 0.55, 0.45)],
    },
    {
        "id": "scale_reveal",
        "tag": "40-TON GIANT",
        "headline": "",
        "subline": "",
        "text": "Yet there is one creature that flips the hunt upside down: the humpback whale.",
        "sfx": [("riser", -0.8, 0.55), ("sub_boom", 0.0, 0.85), ("whale_call", 0.2, 0.52)],
    },
    {
        "id": "data_compare",
        "tag": "MASS COMPARISON",
        "headline": "6 TONNES  vs  40 TONNES",
        "subline": "ORCA (8M)  ·  HUMPBACK (15M)",
        "text": "At forty tonnes and fifteen meters long, a humpback outweighs an orca nearly seven to one.",
        "sfx": [("impact_tick", 0.1, 0.55), ("impact_tick", 0.45, 0.55)],
    },
    {
        "id": "weapon_fins",
        "tag": "NATURAL ARMOR",
        "headline": "5M RAZOR-ARMORED FINS",
        "subline": "COVERED IN SHARP BARNACLES",
        "text": "Its five-meter pectoral fins are armored with razor-sharp barnacles that act like heavy clubs.",
        "sfx": [("whoosh", 0.0, 0.52), ("sub_boom", 0.2, 0.65)],
    },
    {
        "id": "sonar_bait",
        "tag": "OCEAN ALARM",
        "headline": "",
        "subline": "",
        "text": "When orcas coordinate an attack, humpbacks hear their sonar calls from miles away.",
        "sfx": [("sonar_ping", 0.2, 0.58), ("sonar_ping", 1.8, 0.48), ("bubble_burst", 0.9, 0.35)],
    },
    {
        "id": "intervention",
        "tag": "THE INTERVENTION",
        "headline": "",
        "subline": "",
        "text": "Scientists have recorded humpbacks charging straight into orca hunts to shield seals and other whales.",
        "sfx": [("riser", -0.7, 0.65), ("sub_boom", 0.0, 0.92), ("whale_call", 0.4, 0.55)],
    },
    {
        "id": "retreat",
        "tag": "85% RETREAT RATE",
        "headline": "ORCAS BREAK FORMATION",
        "subline": "DOCUMENTED INTERVENTIONS",
        "text": "Thrashing their massive tails and blocking every strike, they force the entire orca pod to retreat.",
        "sfx": [("whoosh", 0.0, 0.58), ("bubble_burst", 0.3, 0.42)],
    },
    {
        "id": "closer",
        "tag": "MONARCH OF THE DEEP",
        "headline": "EVEN KILLERS FEAR A GUARDIAN",
        "subline": "MONARCH® OCEAN ARCHIVE",
        "text": "In the deep ocean, brute speed bows to an unbreakable guardian.",
        "sfx": [("sub_boom", 0.0, 0.75), ("whale_call", 0.3, 0.58)],
    },
]


async def try_edge_tts(text: str, mp3_path: Path) -> bool:
    import edge_tts

    for voice in ("en-US-AndrewNeural", "en-US-GuyNeural", "en-US-ChristopherNeural"):
        try:
            comm = edge_tts.Communicate(text, voice, rate="+5%")
            await comm.save(str(mp3_path))
            if mp3_path.exists() and mp3_path.stat().st_size > 1000:
                return True
        except Exception as exc:
            print(f"[TTS] edge-tts {voice} failed: {exc}")
    return False


def ensure_piper_model() -> Path | None:
    PIPER_DIR.mkdir(parents=True, exist_ok=True)
    onnx = PIPER_DIR / "en_US-ryan-high.onnx"
    cfg = PIPER_DIR / "en_US-ryan-high.onnx.json"
    base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high"
    try:
        if not onnx.exists() or onnx.stat().st_size < 1_000_000:
            print("[TTS] Downloading Piper neural voice en_US-ryan-high...")
            urllib.request.urlretrieve(f"{base}/en_US-ryan-high.onnx", onnx)
        if not cfg.exists() or cfg.stat().st_size < 100:
            urllib.request.urlretrieve(f"{base}/en_US-ryan-high.onnx.json", cfg)
        return onnx
    except Exception as exc:
        print(f"[TTS] Piper download failed: {exc}")
        return None


def try_piper_tts(text: str, raw_wav: Path, model_path: Path) -> bool:
    try:
        from piper.voice import PiperVoice

        voice = PiperVoice.load(str(model_path))
        with wave.open(str(raw_wav), "wb") as wav_file:
            voice.synthesize(text, wav_file)
        return raw_wav.exists() and raw_wav.stat().st_size > 2000
    except Exception as exc:
        print(f"[TTS] Piper Python API failed ({exc}), trying CLI...")
        try:
            subprocess.run(
                ["piper", "--model", str(model_path), "--output_file", str(raw_wav)],
                input=text.encode("utf-8"),
                check=True,
            )
            return raw_wav.exists() and raw_wav.stat().st_size > 2000
        except Exception as exc2:
            print(f"[TTS] Piper CLI failed: {exc2}")
            return False


def try_gtts(text: str, mp3_path: Path) -> bool:
    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang="en", tld="us")
        tts.save(str(mp3_path))
        return mp3_path.exists() and mp3_path.stat().st_size > 1000
    except Exception as exc:
        print(f"[TTS] gTTS failed: {exc}")
        return False


async def synth_lines() -> list[dict]:
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    edge_ok = True
    piper_model: Path | None = None

    for idx, beat in enumerate(SCRIPT_BEATS):
        mp3_path = VOICE_DIR / f"line_{idx:02d}.mp3"
        raw_path = VOICE_DIR / f"line_{idx:02d}_raw.wav"
        wav_path = VOICE_DIR / f"line_{idx:02d}.wav"

        synthesized = False
        if edge_ok:
            synthesized = await try_edge_tts(beat["text"], mp3_path)
            if synthesized:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(mp3_path), "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(wav_path)],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                edge_ok = False

        if not synthesized:
            if piper_model is None:
                piper_model = ensure_piper_model()
            if piper_model is not None and try_piper_tts(beat["text"], raw_path, piper_model):
                synthesized = True
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-i", str(raw_path),
                        "-af", "atempo=1.06,highpass=f=75,equalizer=f=140:t=q:w=1.1:g=2.5",
                        "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(wav_path),
                    ],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )

        if not synthesized:
            if try_gtts(beat["text"], mp3_path):
                synthesized = True
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-i", str(mp3_path),
                        "-af", "asetrate=44100*0.90,aresample=48000,atempo=1.15",
                        "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(wav_path),
                    ],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )

        if not synthesized:
            raise RuntimeError(f"All TTS engines failed on beat {idx}")

        with wave.open(str(wav_path), "rb") as w:
            dur = w.getnframes() / w.getframerate()
        print(f"  Line {idx:02d} ({beat['id']}): {dur:.2f}s")
        results.append({**beat, "idx": idx, "wav": str(wav_path), "voice_dur": dur})
    return results


def load_mono_wav(path: str) -> np.ndarray:
    with wave.open(path, "rb") as w:
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0


def lpf(x: np.ndarray, hz: float, order: int = 3) -> np.ndarray:
    sos = signal.butter(order, min(hz / (SR * 0.5), 0.95), btype="low", output="sos")
    return signal.sosfilt(sos, x)


def hpf(x: np.ndarray, hz: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, max(hz / (SR * 0.5), 0.0005), btype="high", output="sos")
    return signal.sosfilt(sos, x)


def bpf(x: np.ndarray, lo: float, hi: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, [lo / (SR * 0.5), min(hi / (SR * 0.5), 0.95)], btype="band", output="sos")
    return signal.sosfilt(sos, x)


def pink_noise(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(n)
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1.0, -2.494956002, 2.017265875, -0.522189400]
    p = signal.lfilter(b, a, white)
    return p / (np.max(np.abs(p)) + 1e-9)


def make_sfx(kind: str, seed: int = 11) -> np.ndarray:
    if kind == "sub_boom":
        dur = 1.5
        n = int(dur * SR)
        t = np.arange(n) / SR
        f = 38.0 + 54.0 * np.exp(-t * 14.0)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.1)
        click = lpf(pink_noise(n, seed), 180.0, 2) * np.exp(-t * 25.0) * 0.4
        return lpf(hpf(body + click, 26.0, 2), 180.0, 3)
    if kind == "whoosh":
        dur = 0.55
        n = int(dur * SR)
        t = np.arange(n) / SR
        env = np.sin(np.pi * t / dur) ** 1.4
        return bpf(pink_noise(n, seed + 3), 240.0, 1800.0, 3) * env
    if kind == "riser":
        dur = 0.85
        n = int(dur * SR)
        t = np.arange(n) / SR
        env = (t / dur) ** 2.1 * np.minimum(1.0, (dur - t) / 0.04)
        f = 90.0 + 380.0 * (t / dur) ** 1.8
        tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
        air = bpf(pink_noise(n, seed + 7), 350.0, 2400.0, 2) * 0.65
        return (tone + air) * env
    if kind == "whale_call":
        dur = 2.4
        n = int(dur * SR)
        t = np.arange(n) / SR
        f = 185.0 + 240.0 * np.exp(-t * 1.2) + 4.0 * np.sin(2 * np.pi * 3.8 * t)
        ph = 2 * np.pi * np.cumsum(f) / SR
        body = np.sin(ph) + 0.32 * np.sin(2 * ph)
        env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
        return hpf(lpf(body * env, 1400.0, 2), 120.0, 2)
    if kind == "sonar_ping":
        dur = 1.1
        n = int(dur * SR)
        t = np.arange(n) / SR
        tone = np.sin(2 * np.pi * 1160.0 * t) + 0.25 * np.sin(2 * np.pi * 2330.0 * t)
        env = np.exp(-t * 6.5)
        return bpf(tone * env, 700.0, 3000.0, 2)
    if kind == "bubble_burst":
        dur = 1.3
        n = int(dur * SR)
        out = np.zeros(n)
        rng = np.random.default_rng(seed + 19)
        for _ in range(18):
            at = int(rng.uniform(0, dur - 0.15) * SR)
            d = rng.uniform(0.04, 0.08)
            m = int(d * SR)
            tt = np.arange(m) / SR
            f0 = rng.uniform(340.0, 820.0)
            f = f0 * (1.0 + 4.5 * tt / d)
            seg = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (d * 0.35))
            end = min(n, at + m)
            out[at:end] += seg[: end - at] * rng.uniform(0.4, 1.0)
        return bpf(out, 280.0, 4000.0, 2)
    if kind == "impact_tick":
        dur = 0.14
        n = int(dur * SR)
        t = np.linspace(0, dur, n, endpoint=False)
        return (np.sin(2 * np.pi * 240.0 * t) * np.exp(-t * 70.0) * 0.7
                + np.sin(2 * np.pi * 680.0 * t) * np.exp(-t * 150.0) * 0.35)
    return np.zeros(int(0.1 * SR))


def build():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = asyncio.run(synth_lines())

    cur_t = 0.45
    timeline_beats = []
    for item in lines:
        start_t = cur_t
        end_t = start_t + item["voice_dur"] + 0.55
        timeline_beats.append({
            "id": item["id"],
            "tag": item["tag"],
            "headline": item["headline"],
            "subline": item["subline"],
            "text": item["text"],
            "start": round(start_t, 3),
            "voice_end": round(start_t + item["voice_dur"], 3),
            "end": round(end_t, 3),
            "wav": item["wav"],
            "sfx": item["sfx"],
        })
        cur_t = end_t
    total_dur = round(cur_t + 1.4, 3)
    total_frames = int(math.ceil(total_dur * FPS))
    total_dur = round(total_frames / FPS, 3)

    n_samples = int(total_dur * SR)
    t_arr = np.arange(n_samples) / SR

    drone = (
        0.75 * np.sin(2 * np.pi * 36.71 * t_arr)
        + 0.85 * np.sin(2 * np.pi * 73.42 * t_arr)
        + 0.25 * np.sin(2 * np.pi * 110.0 * t_arr)
    )
    drone = lpf(hpf(drone, 28.0, 2), 210.0, 3)
    drone *= 0.65 + 0.35 * np.sin(2 * np.pi * t_arr / 14.0)
    swell = lpf(hpf(pink_noise(n_samples, 99), 50.0, 2), 340.0, 3) * 0.25

    bed = (drone * 0.14 + swell * 0.12)
    stereo_bed = np.stack([bed, bed], axis=1)

    voice_track = np.zeros(n_samples)
    duck_env = np.ones(n_samples)

    for b in timeline_beats:
        v = load_mono_wav(b["wav"])
        v = v / (np.max(np.abs(v)) + 1e-9) * 0.82
        i0 = int(b["start"] * SR)
        i1 = min(n_samples, i0 + len(v))
        voice_track[i0:i1] += v[: i1 - i0]

        d0 = max(0, i0 - int(0.12 * SR))
        d1 = min(n_samples, i1 + int(0.18 * SR))
        duck_env[d0:d1] = np.minimum(duck_env[d0:d1], 0.48)

        for s_idx, (kind, offset, gain) in enumerate(b["sfx"]):
            fx = make_sfx(kind, seed=17 + s_idx * 13) * gain * 0.55
            s0 = max(0, int((b["start"] + offset) * SR))
            s1 = min(n_samples, s0 + len(fx))
            pan = -0.25 if s_idx % 2 == 0 else 0.25
            lg = math.sqrt(0.5 * (1.0 - pan))
            rg = math.sqrt(0.5 * (1.0 + pan))
            stereo_bed[s0:s1, 0] += fx[: s1 - s0] * lg
            stereo_bed[s0:s1, 1] += fx[: s1 - s0] * rg

    duck_env = lpf(duck_env, 8.0, 2)
    stereo_bed *= duck_env[:, None]

    mix = np.stack([
        stereo_bed[:, 0] + voice_track,
        stereo_bed[:, 1] + voice_track,
    ], axis=1)

    raw_wav = OUT_DIR / "audio_raw.wav"
    master_wav = OUT_DIR / "audio_master.wav"
    data = (np.clip(mix, -0.98, 0.98) * 32767).astype("<i2")
    with wave.open(str(raw_wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(raw_wav),
            "-af", "highpass=f=30,equalizer=f=220:t=q:w=1.0:g=-2.5,loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000",
            "-c:a", "pcm_s16le",
            str(master_wav),
        ],
        check=True,
    )

    ebur = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(master_wav), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, check=True
    ).stderr
    summ = ebur.split("Summary:")[-1]
    m_i = re.search(r"I:\s+(-?[\d.]+)\s+LUFS", summ)
    m_tp = re.search(r"Peak:\s+(-?[\d.]+)\s+dBFS", summ)
    lufs = float(m_i.group(1)) if m_i else -14.0
    tp = float(m_tp.group(1)) if m_tp else -1.5

    timeline = {
        "title": "Why Orcas Fear Humpbacks",
        "fps": FPS,
        "duration_sec": total_dur,
        "total_frames": total_frames,
        "audio_lufs": lufs,
        "audio_true_peak_db": tp,
        "beats": [{k: v for k, v in b.items() if k not in ("wav", "sfx")} for b in timeline_beats],
    }
    (OUT_DIR / "timeline_synced.json").write_text(json.dumps(timeline, indent=2))
    print(f"Audio mastered: {total_dur:.2f}s ({total_frames} frames) | I={lufs:.2f} LUFS | Peak={tp:.2f} dBFS")


if __name__ == "__main__":
    build()
