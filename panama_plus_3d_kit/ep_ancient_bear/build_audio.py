#!/usr/bin/env python3
"""
MONARCH Panama-Plus Cinema Audio Engine — EP01 Ancient Bear ("The Largest Bear That Ever Hunted Humans")
Combines:
  1. Arena Agent Neural Voiceover (voice-00, 8 frame-locked .wav clips from timeline.json)
  2. Real Bear Growl/Breath (Eduart-bear-3D/bear.mp3, sub-pitched -2.5 st)
  3. Earshot SFX Bank + audio/kit.json onset-aligned cues (drop, riser, hit, whoosh, bell, tick, land)
  4. Real Stone Scrape / Ice-Age Wind + Cave Room Tone, Long-Reverb Water Drips, Crackling Campfire & Heavy Footfalls
  5. 8-Section D-Minor Documentary Cello/Heartbeat Score with True-Silence Punch Drop & Vocal Sidechain Ducking
  6. Mastered cleanly to -14.0 LUFS / -1.5 dBTP @ 48kHz Stereo
"""
import json
import math
import os
import subprocess
import sys
import wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
SFX_DIR = os.path.join(HERE, "sfx")
OUT_WAV = os.path.join(HERE, "master_audio.wav")
OUT_M4A = os.path.join(HERE, "master_audio.m4a")
TIMELINE = json.load(open(os.path.join(HERE, "timeline.json"), "r", encoding="utf-8"))

SR = 48000
DUR = float(TIMELINE["total_sec"])
N = int(round(DUR * SR))


def run_ffmpeg(args):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True)


def load_audio_48k_mono(path, extra_af=None):
    tmp = path + ".tmp48m.wav"
    af = [extra_af] if extra_af else []
    cmd = ["-i", path]
    if af:
        cmd += ["-af", ",".join(af)]
    cmd += ["-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", tmp]
    run_ffmpeg(cmd)
    with wave.open(tmp, "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    os.remove(tmp)
    return x


def write_wav_stereo(path, st):
    st = np.clip(st, -0.99, 0.99)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767.0).astype("<i2").tobytes())


def bp(x, lo=None, hi=None, order=2):
    n = len(x)
    F = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1.0 / (1.0 + (lo / np.maximum(f, 1e-6)) ** (2 * order))
    if hi:
        m *= 1.0 / (1.0 + (f / hi) ** (2 * order))
    return np.fft.irfft(F * m, n).astype(np.float32)


def pink(n, rng):
    w = rng.normal(0.0, 1.0, n).astype(np.float32)
    F = np.fft.rfft(w)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    return np.fft.irfft(F / np.maximum(f, 18.0) ** 0.5, n).astype(np.float32)


def add_stereo(buf, seg_mono, t_sec, gain=1.0, pan=0.0):
    s = int(round(t_sec * SR))
    i0 = max(0, -s)
    j0 = max(0, s)
    m = min(len(seg_mono) - i0, len(buf) - j0)
    if m <= 0:
        return
    a = (np.clip(pan, -1.0, 1.0) + 1.0) * 0.25 * math.pi
    gl, gr = math.cos(a) * 1.4142 * gain, math.sin(a) * 1.4142 * gain
    seg = seg_mono[i0 : i0 + m]
    buf[j0 : j0 + m, 0] += seg * gl
    buf[j0 : j0 + m, 1] += seg * gr


def db_rms(x):
    r = float(np.sqrt(np.mean(np.square(np.maximum(np.abs(x), 1e-9)))))
    return 20.0 * math.log10(max(r, 1e-9))


# ------------------------------------------------------------------ 1. VO TRACK
def build_vo_track(rng):
    vo = np.zeros(N, dtype=np.float32)
    mask = np.zeros(N, dtype=np.float32)
    for b in TIMELINE["beats"]:
        p = os.path.join(HERE, b["vo_file"])
        # Warm documentary vocal polish: clean low-cut + subtle presence
        x = load_audio_48k_mono(p, extra_af="highpass=f=72,equalizer=f=320:t=q:w=1.1:g=-1.5,equalizer=f=3100:t=q:w=1.4:g=1.8")
        pk = float(np.max(np.abs(x))) + 1e-9
        x = x / pk * 0.88
        s = int(round(float(b["vo_start"]) * SR))
        e = min(N, s + len(x))
        m = e - s
        if m > 0:
            vo[s:e] += x[:m]
            mask[max(0, s - int(0.18 * SR)) : min(N, e + int(0.35 * SR))] = 1.0

    # Smooth ducking envelope (~220ms release)
    win = int(0.22 * SR)
    kernel = np.hanning(win * 2 + 1).astype(np.float32)
    kernel /= kernel.sum()
    duck_env = np.convolve(mask, kernel, mode="same")
    duck_env = np.clip(duck_env * 1.35, 0.0, 1.0)

    # Subtle dark limestone cave early-reflection tail (11% wet)
    ir_n = int(1.3 * SR)
    ir = rng.normal(0.0, 1.0, ir_n).astype(np.float32) * np.exp(-np.arange(ir_n) / (0.24 * SR))
    ir[: int(0.018 * SR)] = 0.0
    ir = bp(ir, 220, 4200, 1)
    ir /= np.sum(np.abs(ir)) + 1e-9
    wet = np.fft.irfft(np.fft.rfft(vo, N + ir_n) * np.fft.rfft(ir, N + ir_n), N + ir_n)[:N].astype(np.float32)
    vo_st = np.stack([vo * 0.96 + wet * 0.13, vo * 0.96 + np.roll(wet, 190) * 0.13], axis=1)
    return vo_st, duck_env


# ------------------------------------------------------------------ 2. SCORE
NOTE = {"C": 16.35, "C#": 17.32, "D": 18.35, "D#": 19.45, "E": 20.60, "F": 21.83,
        "F#": 23.12, "G": 24.50, "G#": 25.96, "A": 27.50, "A#": 29.14, "B": 30.87}


def hz(name):
    return NOTE[name[:-1]] * (2 ** int(name[-1]))


def pad_tone(f, n, amp, rng):
    t = np.arange(n, dtype=np.float32) / SR
    v = np.zeros(n, dtype=np.float32)
    for det in (-0.14, 0.0, 0.15):
        v += np.sin(2.0 * math.pi * f * (1.0 + det / 100.0) * t + float(rng.uniform(0, 6.28)))
    v += 0.28 * np.sin(2.0 * math.pi * f * 2.0 * t)
    v += 0.10 * np.sin(2.0 * math.pi * f * 3.0 * t)
    v /= 2.7
    fade = np.minimum(1.0, t / 0.55) * np.minimum(1.0, (n / SR - t) / 0.65)
    return v * fade * amp


def arp_tone(f, n, amp):
    t = np.arange(n, dtype=np.float32) / SR
    v = (
        np.sin(2.0 * math.pi * f * t)
        + 0.34 * np.sin(2.0 * math.pi * f * 2.005 * t)
        + 0.10 * np.sin(2.0 * math.pi * f * 3.98 * t)
    )
    return v * np.exp(-t * 3.6) * (1.0 - np.exp(-t * 420.0)) * amp


def build_score(rng):
    # (start, end, chord, intensity, pulse_sec, arp_notes)
    sections = [
        (0.00, 12.22, ["D2", "A2", "D3"],        0.38, 0.00, ["D4", "A4"]),         # Cold Open
        (12.22, 24.11, ["D2", "F2", "A2", "D3"], 0.65, 1.25, ["D4", "F4", "A4"]),   # 600 KG Doorway
        (24.11, 34.67, ["G1", "D2", "A#2"],      0.55, 1.50, ["D4", "G4"]),         # Forehead & Molars
        (34.67, 44.15, ["F1", "C2", "A2"],       0.42, 0.00, ["C4", "F4", "A4"]),   # It ate plants
        # 44.15 -> 45.93 TRUE SILENCE DROP ("It did the exact opposite.")
        (45.93, 58.19, ["A#1", "D2", "F2", "A2"],0.78, 0.78, ["D4", "F4", "A#4"]),  # Wolf vs No Calculation
        (58.19, 72.15, ["A1", "D2", "E2", "A2"], 0.90, 0.64, ["E4", "A4", "C5"]),   # Same Address / One Door
        (72.15, 86.43, ["C2", "G2", "D3"],       0.68, 0.95, ["G4", "D5"]),         # Bones & Chauvet
        (86.43, 98.20, ["D2", "A2", "F3"],       0.46, 0.00, ["D4", "A4", "F5"]),   # The Room
    ]
    st = np.zeros((N, 2), dtype=np.float32)
    for t0, t1, chord, inten, pulse, arp in sections:
        s0, s1 = int(round(t0 * SR)), min(N, int(round(t1 * SR)))
        m = s1 - s0
        if m <= 0:
            continue
        sec = np.zeros((m, 2), dtype=np.float32)
        for idx, note in enumerate(chord):
            p = pad_tone(hz(note), m, 0.14 * inten, rng)
            pan = 0.0 if idx == 0 else (-0.42 if idx % 2 else 0.42)
            a = (pan + 1.0) * 0.25 * math.pi
            sec[:, 0] += p * math.cos(a)
            sec[:, 1] += p * math.sin(a)
        if pulse > 0.0:
            step = int(round(pulse * SR))
            klen = int(0.32 * SR)
            tt = np.arange(klen, dtype=np.float32) / SR
            thump = np.sin(2.0 * math.pi * (52.0 + 36.0 * np.exp(-tt * 18.0)) * tt) * np.exp(-tt * 9.5) * 0.28 * inten
            pos = 0
            while pos + 100 < m:
                kk = min(klen, m - pos)
                sec[pos : pos + kk, 0] += thump[:kk]
                sec[pos : pos + kk, 1] += thump[:kk]
                pos += step
        if arp:
            step = int(round(0.625 * SR))
            alen = int(0.95 * SR)
            pos, ai = 0, 0
            while pos + 100 < m:
                note = arp[ai % len(arp)]
                at = arp_tone(hz(note), alen, 0.085 * inten)
                kk = min(alen, m - pos)
                pan = -0.35 if ai % 2 == 0 else 0.35
                a = (pan + 1.0) * 0.25 * math.pi
                sec[pos : pos + kk, 0] += at[:kk] * math.cos(a)
                sec[pos : pos + kk, 1] += at[:kk] * math.sin(a)
                pos += step
                ai += 1
        st[s0:s1] += sec

    # Keep pads warm away from 2-5kHz vocal presence band
    st[:, 0] = bp(st[:, 0], 24, 3400, 2)
    st[:, 1] = bp(st[:, 1], 24, 3400, 2)
    return st


# ------------------------------------------------------------------ 3. AMBIENCE & FOLEY
def build_ambience_and_foley(rng):
    amb = np.zeros((N, 2), dtype=np.float32)
    t = np.arange(N, dtype=np.float32) / SR

    # Subterranean cave room drone (38 Hz + 57 Hz) + airy cavern drift
    cave_sub = (np.sin(2.0 * math.pi * 38.0 * t) * 0.55 + np.sin(2.0 * math.pi * 57.0 * t) * 0.28)
    cave_sub = bp(cave_sub, 20, 105, 2) * 0.06
    cave_air = bp(pink(N, rng), 220, 3800, 1) * 0.028
    amb[:, 0] += cave_sub + cave_air
    amb[:, 1] += cave_sub + np.roll(cave_air, 620)

    # Real Ice-Age steppe wind (from blocky-stories amb/wind.wav if downloaded)
    wind_path = os.path.join(ASSETS, "wind.wav")
    if os.path.exists(wind_path):
        w_raw = load_audio_48k_mono(wind_path)
        w_loop = np.tile(w_raw, int(math.ceil(N / max(1, len(w_raw)))))[:N]
        w_loop = bp(w_loop, 95, 1100, 2)
    else:
        w_loop = bp(pink(N, rng), 90, 950, 2)
    # Wind swells loudest during outdoor winter Wolf & Cave Mouth shots (12..24s, 45..64s)
    w_env = np.full(N, 0.14, dtype=np.float32)
    for (s_t, e_t, amp) in [(12.0, 24.0, 0.42), (34.5, 44.0, 0.28), (45.8, 63.5, 0.55)]:
        s0, s1 = int(s_t * SR), min(N, int(e_t * SR))
        w_env[s0:s1] = amp
    w_env = np.convolve(w_env, np.hanning(int(1.2 * SR) | 1) / np.hanning(int(1.2 * SR) | 1).sum(), mode="same")
    amb[:, 0] += w_loop * w_env * 0.16
    amb[:, 1] += np.roll(w_loop, 1400) * w_env * 0.16

    # Roaring Hearth Fire + Crisp Crackles (Beats 1, 6, 7, 8 inside cave)
    fire_bed = bp(pink(N, rng), 140, 4500, 2) * 0.025
    crackle = np.zeros(N, dtype=np.float32)
    for _ in range(int(DUR * 14)):
        pos = int(rng.integers(0, max(1, N - 1500)))
        L = int(rng.integers(70, 520))
        burst = rng.normal(0.0, 1.0, L).astype(np.float32) * np.exp(-np.arange(L) / (L * 0.22))
        burst = bp(burst, 1200, 6800, 1) * float(rng.uniform(0.025, 0.14))
        crackle[pos : pos + L] += burst[: min(L, N - pos)]
    f_env = np.full(N, 0.15, dtype=np.float32)
    for (s_t, e_t, amp) in [(0.5, 12.2, 0.75), (58.2, 86.0, 0.90), (86.0, 97.5, 0.45)]:
        f_env[int(s_t * SR) : min(N, int(e_t * SR))] = amp
    f_env = np.convolve(f_env, np.hanning(int(0.8 * SR) | 1) / np.hanning(int(0.8 * SR) | 1).sum(), mode="same")
    add_stereo(amb, (fire_bed + crackle) * f_env, 0.0, gain=0.85, pan=-0.35)

    # Isolated Cavernous Water Drips (huge atmospheric realism, especially in silences!)
    for (td, pan) in [(1.4, -0.4), (7.6, 0.45), (11.6, -0.2), (44.85, 0.35), (71.5, -0.4), (99.15, 0.0)]:
        Ld = int(0.95 * SR)
        tt = np.arange(Ld, dtype=np.float32) / SR
        f0 = float(rng.uniform(1150.0, 1650.0))
        # Characteristic upward water-bubble pitch sweep + cavernous decay
        drip = np.sin(2.0 * math.pi * (f0 + 480.0 * (1.0 - np.exp(-tt * 65.0))) * tt)
        drip *= np.exp(-tt * 28.0) * (1.0 - np.exp(-tt * 600.0)) * 0.24
        # Echo bounce inside cave
        echo = np.pad(drip, (int(0.16 * SR), 0))[:Ld] * 0.32 + np.pad(drip, (int(0.35 * SR), 0))[:Ld] * 0.12
        add_stereo(amb, drip + echo, td, gain=0.95, pan=pan)

    # Real Stone Scrapes / Bone Impacts (Beat 7: Hohle Fels flint point + cut bones)
    for idx, t_st in enumerate([73.6, 75.8, 79.4, 82.1]):
        sp = os.path.join(ASSETS, f"stone_0{(idx % 4) + 1}.wav")
        if os.path.exists(sp):
            sx = load_audio_48k_mono(sp)
            sx = sx / (np.max(np.abs(sx)) + 1e-9) * 0.22
            add_stereo(amb, sx, t_st, gain=0.9, pan=0.25 if idx % 2 else -0.25)

    # Heavy 600kg Cave Bear Footsteps (Beats 2 & 6) + Hunter Gravel Steps (Beat 6)
    step_times = [
        (13.2, True, -0.2), (14.4, True, 0.2), (16.8, True, -0.25), (18.1, True, 0.25),
        (59.5, False, -0.3), (60.4, False, 0.3), (61.3, False, -0.3), (62.2, False, 0.3),
        (65.2, True, -0.2), (66.5, True, 0.2), (67.9, True, -0.15),
    ]
    for ts, heavy, pan in step_times:
        Ls = int((0.28 if heavy else 0.14) * SR)
        tt = np.arange(Ls, dtype=np.float32) / SR
        gravel = bp(rng.normal(0.0, 1.0, Ls).astype(np.float32) * np.exp(-tt * (26.0 if heavy else 52.0)), 140, 3200, 1)
        sub = np.sin(2.0 * math.pi * (56.0 if heavy else 95.0) * tt) * np.exp(-tt * (18.0 if heavy else 38.0))
        step_sig = gravel * (0.34 if heavy else 0.18) + sub * (0.42 if heavy else 0.10)
        add_stereo(amb, step_sig, ts, gain=1.0, pan=pan)

    # Real Bear Growls / Exhale (Eduart-bear-3D/bear.mp3 pitched -2.5 semitones for 600kg mass)
    bear_mp3 = os.path.join(ASSETS, "bear.mp3")
    if os.path.exists(bear_mp3):
        growl = load_audio_48k_mono(
            bear_mp3,
            extra_af="asetrate=44100*0.86,aresample=48000,lowpass=f=2800,afade=t=in:st=0:d=0.18,afade=t=out:st=1.8:d=0.6",
        )
        growl = growl[: int(2.5 * SR)]
        growl = growl / (np.max(np.abs(growl)) + 1e-9)
        add_stereo(amb, growl * 0.42, 15.2, gain=1.0, pan=0.05)
        add_stereo(amb, growl * 0.34, 52.2, gain=1.0, pan=-0.10)
        add_stereo(amb, growl * 0.46, 65.0, gain=1.0, pan=0.0)

    return amb


# ------------------------------------------------------------------ 4. EARSHOT KIT SFX
def build_earshot_sfx():
    sfx = np.zeros((N, 2), dtype=np.float32)
    kit_path = os.path.join(SFX_DIR, "kit.json")
    meta_path = os.path.join(SFX_DIR, "takes", "meta.json")
    if not (os.path.exists(kit_path) and os.path.exists(meta_path)):
        print("WARN: earshot kit/takes missing, skipping earshot layer")
        return sfx

    kit = json.load(open(kit_path, "r", encoding="utf-8"))["kit"]["roles"]
    meta = json.load(open(meta_path, "r", encoding="utf-8"))
    cache = {}
    BED_DB = -23.0

    def cue(role, t, gain_db=0.0, pan=0.0):
        r = kit.get(role)
        if not r:
            return
        name = r["sound"].replace("/", "_")
        wav_p = os.path.join(SFX_DIR, "takes", name + ".wav")
        if not os.path.exists(wav_p):
            return
        if name not in cache:
            cache[name] = load_audio_48k_mono(wav_p)
        x = cache[name]
        onset = float(meta.get(name, {}).get("onset_s", 0.0))
        off = float(r.get("offset_ms", 0) or 0) / 1000.0
        start = t + off - onset
        target_db = BED_DB + float(r.get("bed_db", 0.0)) + gain_db
        cur = db_rms(x)
        g = 10.0 ** ((target_db - cur) / 20.0)
        p_use = 0.0 if role in ("drop", "land", "hit", "tock") else pan
        add_stereo(sfx, x * min(g, 2.5), start, gain=1.0, pan=p_use)

    # Frame-locked psychological cues matching timeline.json beats!
    cue("drop", 0.50, -1.0)
    cue("bell", 8.40, 0.5, 0.20)          # "PLACED."
    cue("riser", 11.10, -1.5, 0.0)
    cue("whoosh.long", 12.22, -2.0, -0.25)
    cue("hit", 12.22, -1.0)               # 600 KG Cave Mouth Reveal
    cue("drop", 15.60, -2.5)
    cue("whoosh.short", 24.11, -2.5, 0.25)
    cue("tick.crisp", 25.40, 1.0, -0.3)   # Steep forehead HUD
    cue("tick.crisp", 30.00, 1.0, 0.3)    # Flat molars HUD
    cue("whoosh.short", 34.67, -2.5, -0.25)
    cue("tick", 37.80, 0.5, 0.0)          # Mostly plants
    cue("drop", 42.60, -1.5)              # "THE OPPOSITE."
    cue("riser", 44.85, -1.0, 0.0)        # Swell out of dead silence into Wolf!
    cue("hit", 45.93, -1.0)
    cue("whoosh.long", 45.93, -2.0, 0.25)
    cue("drop", 52.80, -3.0)              # "Furniture in the way"
    cue("riser", 57.10, -1.5, 0.0)
    cue("whoosh.long", 58.19, -2.0, -0.25)
    cue("hit", 58.19, -1.0)               # Same address
    cue("drop", 65.80, -1.0)              # "ONE DOOR"
    cue("whoosh.short", 72.15, -2.0, 0.25)
    cue("tock", 73.80, 0.5, -0.2)         # Flint in vertebra
    cue("tick.crisp", 78.60, 0.5, 0.2)    # 1,700+ cut bones
    cue("riser", 85.30, -2.0, 0.0)
    cue("whoosh.long", 86.43, -2.5, -0.2)
    cue("bell", 95.80, 1.0, 0.0)          # "NOT A BEAR'S ANYMORE."
    return sfx


def main():
    rng = np.random.default_rng(42)
    print("Building Arena Agent VO track...")
    vo_st, duck = build_vo_track(rng)
    print("Building 8-section D-minor documentary score...")
    score = build_score(rng)
    print("Building cave ambience, fire crackles, steppe wind, footsteps & bear roar...")
    amb = build_ambience_and_foley(rng)
    print("Building earshot SFX cue bus...")
    sfx = build_earshot_sfx()

    # Smooth vocal sidechain ducking: music/amb step down ~5.5 dB under voice
    bed_duck = (1.0 - 0.48 * duck)[:, None]
    mix = vo_st * 1.02 + (score * 0.72 + amb * 0.85) * bed_duck + sfx * 0.78
    mix = np.tanh(mix * 1.05) * 0.94

    raw_tmp = OUT_WAV + ".raw.wav"
    write_wav_stereo(raw_tmp, mix)
    run_ffmpeg([
        "-i", raw_tmp,
        "-af", "highpass=f=26,loudnorm=I=-14:TP=-1.5:LRA=8",
        "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", OUT_WAV,
    ])
    run_ffmpeg([
        "-i", OUT_WAV, "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2", OUT_M4A,
    ])
    os.remove(raw_tmp)
    print(f"DONE -> {OUT_WAV} & {OUT_M4A} ({DUR:.3f}s)")


if __name__ == "__main__":
    main()
