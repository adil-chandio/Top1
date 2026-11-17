#!/usr/bin/env python3
"""
MONARCH® PANAMA-PLUS EP4 — ORCA vs HUMPBACK (URDU VERSION)
Builds authentic Pakistani Urdu neural narration (edge-tts ur-PK-AsadNeural ->
ur-PK-UzmaNeural -> gTTS ur fallback), synchronized with Monarch.Overall.Work's
orca3d-audio-v3 ocean DSP (whale_moan, sonar_ping, krill_shimmer, bubble_rise,
surface_swell, carousel_rotation) + Leonxlnx/earshot cinematic hits, mastered to
-14.0 LUFS / -1.5 dBTP.
"""
from __future__ import annotations

import asyncio
import json
import math
import re
import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy import signal

KIT_DIR = Path(__file__).resolve().parent
OUT_DIR = KIT_DIR / "out"
VOICE_DIR = OUT_DIR / "voice_lines"
EARSHOT_DIR = KIT_DIR / "assets" / "earshot_takes"
SR = 48000
FPS = 30

SCRIPT_BEATS = [
    {
        "id": "hook_orcas",
        "tag": "SAMANDARI SHIKAARI",
        "headline": "",
        "subline": "",
        "tts_urdu": "اوَرکا سمندر کا سب سے خطرناک شکاری ہے۔ جب یہ آتا ہے تو گریٹ وائٹ شارک بھی بھاگ کھڑی ہوتی ہے۔",
        "text": "Orca samandar ka sab se khatarnak shikaari hai. Jab yeh aata hai toh Great White Shark bhi bhaag khadi hoti hai.",
        "sfx": [("earshot_sub", 0.10, 0.72), ("whoosh", 0.55, 0.45), ("bubble_rise", 1.2, 0.35)],
    },
    {
        "id": "scale_reveal",
        "tag": "40-TON DEO-QAMAT",
        "headline": "",
        "subline": "",
        "tts_urdu": "لیکن گہرے سمندر میں ایک دیو قامت مخلوق ایسی بھی ہے جو اس شکار کا رخ الٹ دیتی ہے: ہمپ بیک وہیل۔",
        "text": "Lekin gehray samandar mein ek deo-qamat makhlooq aisi bhi hai jo shikaar palat deti hai: Humpback Whale.",
        "sfx": [("earshot_riser", -0.85, 0.58), ("earshot_sub", 0.0, 0.85), ("whale_moan", 0.25, 0.52)],
    },
    {
        "id": "data_compare",
        "tag": "WAZAN KA MUQABLA",
        "headline": "6 TONNES  vs  40 TONNES",
        "subline": "ORCA (8M)  ·  HUMPBACK (15M)",
        "tts_urdu": "چالیس ٹن وزن اور پندرہ میٹر لمبائی کے ساتھ، ایک ہمپ بیک وہیل اوَرکا سے تقریباً سات گنا زیادہ بھاری ہوتی ہے۔",
        "text": "40 ton wazan aur 15 meter lambai ke sath, Humpback Whale Orca se taqreeban 7 guna zyada bhaari hoti hai.",
        "sfx": [("earshot_hit", 0.08, 0.52), ("earshot_hit", 0.45, 0.52)],
    },
    {
        "id": "weapon_fins",
        "tag": "QUDRATI HATHIYAR",
        "headline": "5M RAZOR-ARMORED FINS",
        "subline": "TEZ BARNACLES SE LAIS",
        "tts_urdu": "اس کے پانچ میٹر لمبے پنکھ تیز بارنیکلز سے لیس ہوتے ہیں، جو سمندر میں بھاری ہتھوڑے کی طرح وار کرتے ہیں۔",
        "text": "Iske 5 meter lambe pankh tez barnacles se lais hote hain, jo samandar mein bhaari hathode ki tarah waar karte hain.",
        "sfx": [("earshot_whoosh", 0.0, 0.56), ("earshot_sub", 0.22, 0.68), ("bubble_rise", 0.45, 0.48)],
    },
    {
        "id": "sonar_bait",
        "tag": "SONAR ALARM",
        "headline": "",
        "subline": "",
        "tts_urdu": "جب اوَرکا جھنڈ بنا کر حملے کی سونار کال دیتے ہیں، تو ہمپ بیک میلوں دور سے خطرے کی آواز سن لیتی ہے۔",
        "text": "Jab Orcas jhund bana kar hamlay ki sonar call dete hain, toh Humpback meelon door se aawaz sun leti hai.",
        "sfx": [("sonar_ping", 0.15, 0.60), ("krill_shimmer", 0.4, 0.35), ("sonar_ping", 2.0, 0.48)],
    },
    {
        "id": "intervention",
        "tag": "AZEEM MADADGAAR",
        "headline": "",
        "subline": "",
        "tts_urdu": "سائنسدانوں نے دیکھا ہے کہ ہمپ بیک سیلز اور دوسری وہیلز کو بچانے کے لیے سیدھا اوَرکا کے حملے میں کود پڑتی ہے۔",
        "text": "Scientists ne dekha hai ke Humpback seals aur doosri whales ko bachane ke liye seedha hamlay mein kood padti hai.",
        "sfx": [("earshot_riser", -0.75, 0.65), ("earshot_sub", 0.0, 0.90), ("whale_moan", 0.35, 0.55)],
    },
    {
        "id": "retreat",
        "tag": "85% RETREAT RATE",
        "headline": "ORCAS BREAK FORMATION",
        "subline": "DOCUMENTED INTERVENTIONS",
        "tts_urdu": "اپنی دیو ہیکل دُم اور پنکھوں کے طاقتور وار سے یہ پورے اوَرکا جھنڈ کو پیچھے ہٹنے پر مجبور کر دیتی ہے۔",
        "text": "Apni deo-haikal dum aur pankhon ke taaqatwar waar se yeh poore Orca jhund ko peechhe hatne par majboor kar deti hai.",
        "sfx": [("earshot_whoosh", 0.0, 0.60), ("bubble_rise", 0.25, 0.48), ("carousel", 0.5, 0.36)],
    },
    {
        "id": "closer",
        "tag": "MUHAFIZ-E-SAMANDAR",
        "headline": "EVEN KILLERS FEAR A GUARDIAN",
        "subline": "MONARCH® OCEAN ARCHIVE",
        "tts_urdu": "کیونکہ گہرے سمندر میں تیز رفتاری بھی ایک ناقابلِ شکست محافظ کے سامنے جھک جاتی ہے۔",
        "text": "Kyunki gehray samandar mein tez raftaari bhi ek na-qabil-e-shikast muhafiz ke samne jhuk jaati hai.",
        "sfx": [("earshot_sub", 0.0, 0.78), ("whale_moan", 0.30, 0.60)],
    },
]


async def try_edge_tts_urdu(text: str, mp3_path: Path) -> bool:
    import edge_tts

    for voice in ("ur-PK-AsadNeural", "ur-PK-UzmaNeural", "ur-IN-SalmanNeural"):
        try:
            comm = edge_tts.Communicate(text, voice, rate="+4%")
            await comm.save(str(mp3_path))
            if mp3_path.exists() and mp3_path.stat().st_size > 1000:
                return True
        except Exception as exc:
            print(f"[TTS] edge-tts {voice} failed: {exc}")
    return False


def try_gtts_urdu(text: str, mp3_path: Path) -> bool:
    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang="ur")
        tts.save(str(mp3_path))
        return mp3_path.exists() and mp3_path.stat().st_size > 1000
    except Exception as exc:
        print(f"[TTS] gTTS Urdu failed: {exc}")
        return False


def decode_to_wav_48k_mono(src: Path, dst_wav: Path) -> np.ndarray:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", str(dst_wav)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    with wave.open(str(dst_wav), "rb") as wf:
        raw = wf.readframes(wf.getnframes())
    arr = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    nz = np.flatnonzero(np.abs(arr) > 0.008)
    if len(nz) > 0:
        s = max(0, int(nz[0]) - int(0.03 * SR))
        e = min(len(arr), int(nz[-1]) + int(0.06 * SR))
        arr = arr[s:e]
    return arr


def load_earshot_take(take_rel: str, target_sr: int = SR) -> np.ndarray | None:
    p = EARSHOT_DIR / take_rel
    if not p.exists():
        return None
    tmp = OUT_DIR / f"_tmp_{p.stem}.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(p), "-ac", "1", "-ar", str(target_sr), "-sample_fmt", "s16", str(tmp)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    with wave.open(str(tmp), "rb") as wf:
        arr = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    tmp.unlink(missing_ok=True)
    return arr


def bpf(x: np.ndarray, lo: float, hi: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, [lo / (SR * 0.5), min(hi, SR * 0.45) / (SR * 0.5)], btype="bandpass", output="sos")
    return signal.sosfilt(sos, x)


def lpf(x: np.ndarray, hi: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, min(hi, SR * 0.45) / (SR * 0.5), btype="lowpass", output="sos")
    return signal.sosfilt(sos, x)


def hpf(x: np.ndarray, lo: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, lo / (SR * 0.5), btype="highpass", output="sos")
    return signal.sosfilt(sos, x)


def pink_noise(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    w = rng.standard_normal(n)
    b, a = signal.butter(1, 0.04)
    y = signal.lfilter(b, a, w)
    return y / (np.max(np.abs(y)) + 1e-9)


# --- Repo orca3d-audio-v3.py Ocean DSP Instruments ---
def synth_whale_moan(dur_s: float = 2.8, f0: float = 470.0, f1: float = 196.0) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 1.35) + 4.5 * np.sin(2 * np.pi * 4.1 * t)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) + 0.34 * np.sin(2 * phase) + 0.13 * np.sin(3 * phase)
    breath = bpf(pink_noise(n, 11), 240.0, 1400.0, order=2) * 0.22
    shape = np.sin(np.pi * np.clip(t / dur_s, 0, 1)) ** 0.65
    out = hpf((body + breath) * shape, 140.0, order=3)
    return out / (np.max(np.abs(out)) + 1e-9)


def synth_sonar_ping(dur_s: float = 1.25, f: float = 1180.0) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * f * t) + 0.32 * np.sin(2 * np.pi * f * 2.01 * t)
    env = np.exp(-t * 7.2)
    lag = int(0.085 * SR)
    tail = np.concatenate([np.zeros(lag), (tone * env)[:-lag] * 0.30])
    out = bpf(tone * env + tail, 700.0, 3200.0, order=2)
    return out / (np.max(np.abs(out)) + 1e-9)


def synth_krill_shimmer(dur_s: float = 3.0) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    shimmer = bpf(pink_noise(n, 23), 900.0, 3200.0, order=3)
    rng = np.random.default_rng(23)
    grain = lpf(np.abs(rng.standard_normal(n)), 22.0, order=2)
    env = 0.25 + 0.75 * grain / (np.max(grain) + 1e-9)
    shape = np.sin(np.pi * np.clip(t / dur_s, 0, 1)) ** 1.3
    out = shimmer * env * shape
    return out / (np.max(np.abs(out)) + 1e-9)


def synth_bubble_rise(dur_s: float = 1.6) -> np.ndarray:
    n = int(dur_s * SR)
    out = np.zeros(n)
    rng = np.random.default_rng(31)
    for _ in range(24):
        at = int(rng.uniform(0, dur_s - 0.2) * SR)
        d = 0.05 + rng.uniform(0, 0.05)
        m = int(d * SR)
        tt = np.arange(m) / SR
        f0 = rng.uniform(320.0, 880.0)
        f = f0 * (1.0 + 5.2 * tt / d)
        tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (d * 0.32))
        end = min(n, at + m)
        out[at:end] += (tone * rng.uniform(0.35, 1.0))[: end - at]
    out = bpf(out, 280.0, 5200.0, order=2)
    return out / (np.max(np.abs(out)) + 1e-9)


def synth_whoosh(dur_s: float = 0.75) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(t / dur_s, 0, 1)) ** 1.6
    out = bpf(pink_noise(n, 77), 160.0, 1800.0, order=2) * env
    return out / (np.max(np.abs(out)) + 1e-9)


def synth_sub_boom(dur_s: float = 1.5) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    f = 42.0 + 78.0 * np.exp(-t * 14.0)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5)
    return np.tanh(tone * 1.4) / 1.2


def synth_riser(dur_s: float = 1.3) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    f = 95.0 * (4.2 ** (t / dur_s))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.35 * bpf(pink_noise(n, 99), 300.0, 3200.0)
    out = body * ((t / dur_s) ** 2.2) * np.exp(-np.maximum(0, t - dur_s + 0.08) * 30.0)
    return out / (np.max(np.abs(out)) + 1e-9)


def synth_surface_swell(dur_s: float) -> np.ndarray:
    n = int(dur_s * SR)
    t = np.arange(n) / SR
    low = hpf(lpf(pink_noise(n, 411), 220.0, order=3), 45.0, order=2)
    env = (0.45 + 0.55 * (0.5 - 0.5 * np.cos(2 * np.pi * t * 0.21)) ** 1.3)
    deep_drone = (np.sin(2 * np.pi * 54.0 * t) * 0.30 + np.sin(2 * np.pi * 81.0 * t) * 0.14)
    return (low * env * 0.65 + deep_drone * 0.35)


def measure_lufs(wav_path: Path) -> tuple[float, float]:
    res = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(wav_path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    summ = res.stderr.split("Summary:")[-1]
    lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))
    return lufs, tp


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    VOICE_DIR.mkdir(parents=True, exist_ok=True)

    beats_out = []
    voice_clips = []
    t_cursor = 0.40

    for idx, beat in enumerate(SCRIPT_BEATS):
        mp3 = VOICE_DIR / f"{idx:02d}_{beat['id']}.mp3"
        wav = VOICE_DIR / f"{idx:02d}_{beat['id']}.wav"

        ok = await try_edge_tts_urdu(beat["tts_urdu"], mp3)
        if not ok:
            ok = try_gtts_urdu(beat["tts_urdu"], mp3)
        if not ok:
            raise RuntimeError(f"All Urdu TTS backends failed on beat {beat['id']}")

        samples = decode_to_wav_48k_mono(mp3, wav)
        dur = len(samples) / SR
        start_t = round(t_cursor, 3)
        voice_end = round(start_t + dur, 3)
        pause = 0.90 if idx in (1, 5, 7) else 0.65
        end_t = round(voice_end + pause, 3)

        beats_out.append({
            "id": beat["id"],
            "tag": beat["tag"],
            "headline": beat["headline"],
            "subline": beat["subline"],
            "text": beat["text"],
            "start": start_t,
            "voice_end": voice_end,
            "end": end_t,
            "sfx": beat["sfx"],
        })
        voice_clips.append((start_t, samples))
        t_cursor = end_t
        print(f"Beat {idx+1}: {beat['id']} [{start_t:.2f}s -> {voice_end:.2f}s] (cut {end_t:.2f}s)")

    total_dur = math.ceil((t_cursor + 1.0) * FPS) / FPS
    total_frames = int(round(total_dur * FPS))
    n_total = int(total_dur * SR)

    voice_bus = np.zeros(n_total, dtype=np.float64)
    for start_t, samples in voice_clips:
        s_idx = int(round(start_t * SR))
        e_idx = min(n_total, s_idx + len(samples))
        voice_bus[s_idx:e_idx] += samples[: e_idx - s_idx]

    # Preload repo Earshot takes with procedural DSP fallbacks
    earshot_sub = load_earshot_take("sub_drop/punch.wav")
    if earshot_sub is None:
        earshot_sub = synth_sub_boom()
    earshot_riser = load_earshot_take("riser/dark.wav")
    if earshot_riser is None:
        earshot_riser = synth_riser()
    earshot_whoosh = load_earshot_take("whoosh_big/thump.wav")
    if earshot_whoosh is None:
        earshot_whoosh = synth_whoosh()
    earshot_hit = load_earshot_take("cut_hit/punch.wav")
    if earshot_hit is None:
        earshot_hit = synth_sub_boom(0.45)

    sfx_bank = {
        "earshot_sub": earshot_sub,
        "earshot_riser": earshot_riser,
        "earshot_whoosh": earshot_whoosh,
        "earshot_hit": earshot_hit,
        "whoosh": synth_whoosh(),
        "whale_moan": synth_whale_moan(),
        "sonar_ping": synth_sonar_ping(),
        "krill_shimmer": synth_krill_shimmer(),
        "bubble_rise": synth_bubble_rise(),
        "carousel": synth_whoosh(1.2),
    }

    sfx_L = np.zeros(n_total, dtype=np.float64)
    sfx_R = np.zeros(n_total, dtype=np.float64)
    pan_cycle = [-0.30, 0.28, 0.0, -0.22, 0.32]
    p_i = 0
    for b in beats_out:
        for name, rel_t, gain in b["sfx"]:
            clip = sfx_bank[name]
            t_pos = max(0.0, b["start"] + rel_t)
            s_idx = int(round(t_pos * SR))
            e_idx = min(n_total, s_idx + len(clip))
            if e_idx <= s_idx:
                continue
            pan = 0.0 if "sub" in name else pan_cycle[p_i % len(pan_cycle)]
            p_i += 1
            lg = math.sqrt(0.5 * (1.0 - pan))
            rg = math.sqrt(0.5 * (1.0 + pan))
            seg = clip[: e_idx - s_idx] * gain
            sfx_L[s_idx:e_idx] += seg * lg
            sfx_R[s_idx:e_idx] += seg * rg

    # Ocean bed + surface swell (ducked gently under Urdu speech)
    bed = synth_surface_swell(total_dur) * 0.14
    voice_env = np.convolve(np.abs(voice_bus), np.ones(int(0.16 * SR)) / int(0.16 * SR), mode="same")
    duck = 1.0 - 0.58 * np.clip(voice_env / 0.10, 0.0, 1.0)

    mix_L = voice_bus * 1.10 + (sfx_L + bed) * duck
    mix_R = voice_bus * 1.10 + (sfx_R + bed) * duck
    stereo = np.stack([mix_L, mix_R], axis=1)
    peak = np.max(np.abs(stereo)) + 1e-9
    if peak > 0.90:
        stereo = stereo * (0.90 / peak)

    raw_wav = OUT_DIR / "audio_raw.wav"
    master_wav = OUT_DIR / "audio_master.wav"
    data = (np.clip(stereo, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(str(raw_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(data.tobytes())

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(raw_wav),
            "-af", "highpass=f=30,lowshelf=g=1.5:f=90,loudnorm=I=-14.0:TP=-1.5:LRA=7,aresample=48000,alimiter=limit=0.84:level=false",
            "-ar", "48000", "-ac", "2", "-sample_fmt", "s16",
            str(master_wav),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    lufs, tp = measure_lufs(master_wav)
    print(f"Master Urdu Audio: {total_dur:.2f}s ({total_frames} frames) | I={lufs:.1f} LUFS | TP={tp:.1f} dBTP")

    timeline = {
        "title": "Why Orcas Fear Humpbacks — Urdu 3D",
        "fps": FPS,
        "duration_sec": total_dur,
        "total_frames": total_frames,
        "audio_lufs": lufs,
        "audio_tp_db": tp,
        "beats": beats_out,
    }
    (OUT_DIR / "timeline_synced.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
