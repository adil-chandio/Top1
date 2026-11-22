#!/usr/bin/env python3
"""
Monarch Cam #03 — V4 Cinema Master Audio Engine
Builds:
  1. Monarch-Cam-03-Long-Video-Dry-Voiceover-Master-V4.wav (48 kHz, 24-bit, zero time-stretch)
  2. Monarch-Cam-03-Long-Video-Master-Mix-V4.wav (48 kHz, 24-bit, -14 LUFS, <= -1.5 dBTP)
  3. Monarch-Cam-03-Captions-V4.srt & Monarch-Cam-03-Captions-V4.vtt
  4. voice-lock-v4.json
"""
import json, math, os, subprocess, wave
import numpy as np
from scipy import signal
import soundfile as sf

SR = 48000
FPS = 30
FFMPEG = "/tmp/py/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2"
OUT_DIR = "/home/user/Top1/deliverables/monarch-cam-03-v4"
V4_DIR = "/home/user/Top1/tools/monarch-cockroach/v4"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(V4_DIR, exist_ok=True)

tl = json.load(open("/tmp/v4_audio/timeline_v4_aligned.json"))
TOTAL_FRAMES = tl["total_frames"]  # 10302
TOTAL_S = TOTAL_FRAMES / FPS       # 343.40s
N_SAMPLES = int(round(TOTAL_S * SR))

def load_wav_48k_stereo(path):
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    elif data.shape[1] > 2:
        data = data[:, :2]
    if sr != SR:
        g = math.gcd(sr, SR)
        up, down = SR // g, sr // g
        left = signal.resample_poly(data[:, 0], up, down)
        right = signal.resample_poly(data[:, 1], up, down)
        data = np.stack([left, right], axis=1).astype(np.float32)
    return data

def place(buf, clip, start_s, gain=1.0, pan=0.0):
    if clip.ndim == 1:
        clip = np.stack([clip, clip], axis=1)
    idx = int(round(start_s * SR))
    if idx >= N_SAMPLES or idx + len(clip) <= 0:
        return
    c0 = max(0, -idx)
    b0 = max(0, idx)
    L = min(len(clip) - c0, N_SAMPLES - b0)
    if L <= 0:
        return
    gl = gain * math.cos((pan + 1.0) * math.pi * 0.25) * 1.4142
    gr = gain * math.sin((pan + 1.0) * math.pi * 0.25) * 1.4142
    buf[b0:b0+L, 0] += clip[c0:c0+L, 0] * gl
    buf[b0:b0+L, 1] += clip[c0:c0+L, 1] * gr

def fade_io(clip, fi_s=0.015, fo_s=0.03):
    out = clip.copy()
    fi = min(len(out) // 2, max(1, int(fi_s * SR)))
    fo = min(len(out) // 2, max(1, int(fo_s * SR)))
    w_in = 0.5 - 0.5 * np.cos(np.linspace(0, math.pi, fi, dtype=np.float32))
    w_out = 0.5 + 0.5 * np.cos(np.linspace(0, math.pi, fo, dtype=np.float32))
    if out.ndim == 2:
        out[:fi] *= w_in[:, None]
        out[-fo:] *= w_out[:, None]
    else:
        out[:fi] *= w_in
        out[-fo:] *= w_out
    return out

# ---------------------------------------------------------------------------
# 1. BUILD DRY VOICEOVER STEM (ZERO TIME-STRETCH!)
# ---------------------------------------------------------------------------
vo_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)
b_hp, a_hp = signal.butter(2, 78.0 / (SR * 0.5), btype="highpass")
# Gentle air shelf boost around 5.5 kHz for crisp vocal intimacy
b_air, a_air = signal.iirpeak(5800.0 / (SR * 0.5), Q=1.2)

for ch in tl["chapters"]:
    raw_vo = load_wav_48k_stereo(ch["wav"])
    # High-pass rumble removal + subtle presence polish
    clean = np.zeros_like(raw_vo)
    for c in range(2):
        hp = signal.filtfilt(b_hp, a_hp, raw_vo[:, c])
        air = signal.lfilter(b_air, a_air, hp)
        clean[:, c] = hp + 0.14 * air
    clean = fade_io(clean, 0.012, 0.025)
    # Normalize chapter RMS gently so all 7 chapters match loudness within 0.2 dB
    rms = float(np.sqrt(np.mean(clean**2)) + 1e-9)
    clean *= (0.145 / rms)
    place(vo_bus, clean, ch["start_frame"] / FPS, gain=1.0, pan=0.0)

# Save pure Dry Voiceover Master V4 (24-bit 48kHz)
dry_vo_path = f"{OUT_DIR}/Monarch-Cam-03-Long-Video-Dry-Voiceover-Master-V4.wav"
sf.write(dry_vo_path, np.clip(vo_bus, -0.98, 0.98), SR, subtype="PCM_24")

# Compute smooth look-ahead voice activity envelope for sidechain ducking
vo_mono_sq = np.mean(vo_bus**2, axis=1)
win_env = int(0.08 * SR)
vo_rms_env = np.sqrt(np.convolve(vo_mono_sq, np.ones(win_env, dtype=np.float32) / win_env, mode="same"))
# Attack/release smoothing + 60ms look-ahead
shift = int(0.06 * SR)
vo_ahead = np.pad(vo_rms_env[shift:], (0, shift))
duck_amt = np.clip(vo_ahead / 0.035, 0.0, 1.0)
# Smooth release ~350ms
b_lp, a_lp = signal.butter(1, 2.6 / (SR * 0.5), btype="lowpass")
duck_smooth = np.clip(signal.filtfilt(b_lp, a_lp, duck_amt), 0.0, 1.0)

# ---------------------------------------------------------------------------
# 2. SLICE REAL @e.d.i.t_sandeep CLEAN SFX SAMPLES FROM /tmp/v4_audio/sfx_raw_*
# ---------------------------------------------------------------------------
def slice_sfx(reel_name, t0, t1, fi=0.02, fo=0.06, norm_pk=0.7):
    full = load_wav_48k_stereo(f"/tmp/v4_audio/sfx_raw_{reel_name}.wav")
    seg = full[int(t0 * SR):int(t1 * SR)].copy()
    seg = fade_io(seg, fi, fo)
    pk = float(np.max(np.abs(seg)) + 1e-9)
    return seg * (norm_pk / pk)

sfx_whoosh_deep  = slice_sfx("VID_20261113_012137_703", 2.45, 3.10, 0.03, 0.08, 0.75)  # 802 Hz silky cinema whoosh!
sfx_whoosh_mid   = slice_sfx("VID_20261113_012137_703", 0.08, 0.83, 0.03, 0.08, 0.72)  # 1188 Hz smooth transition whoosh!
sfx_sub_drop     = slice_sfx("VID_20261113_012154_590", 14.73, 15.75, 0.02, 0.14, 0.85) # 152 Hz deep sub-bass drop!
sfx_riser_smooth = slice_sfx("VID_20261113_012154_590", 5.80, 8.15, 0.12, 0.08, 0.65)   # 2.35s tension riser!
sfx_riser_air    = slice_sfx("VID_20261113_012158_998", 22.12, 24.02, 0.12, 0.08, 0.60) # 1.90s airy riser!
sfx_click_crisp  = slice_sfx("VID_20261113_012128_753", 1.95, 2.05, 0.004, 0.02, 0.65)  # crisp snap/click!
sfx_pop_soft     = slice_sfx("VID_20261113_012154_590", 4.23, 4.40, 0.005, 0.03, 0.60)  # tactile pop!

# ---------------------------------------------------------------------------
# 3. SYNTHESIZE BESPOKE PHYSICAL BIOMECHANICS FOLEY (48kHz STEREO)
# ---------------------------------------------------------------------------
rng = np.random.default_rng(4203)

def synth_wall_switch():
    """Mechanical ivory wall toggle SNAP + micro spring ring."""
    n = int(0.11 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    click1 = np.exp(-t * 280.0) * (0.8 * rng.standard_normal(n) + 0.9 * np.sin(2*np.pi*2350*t))
    t2 = np.maximum(0.0, t - 0.011)
    click2 = (t >= 0.011) * np.exp(-t2 * 190.0) * (0.6 * np.sin(2*np.pi*3420*t2) + 0.5 * np.sin(2*np.pi*1180*t2))
    body = np.exp(-t * 65.0) * 0.35 * np.sin(2*np.pi*210*t)
    s = (click1 + click2 + body).astype(np.float32)
    return fade_io(s / (np.max(np.abs(s)) + 1e-9), 0.001, 0.02)

def synth_coin_clink():
    """Two minted copper-zinc US pennies stacking onto oak threshold."""
    n = int(0.42 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    modes = [6180, 9420, 12850, 4120]
    decays = [24.0, 32.0, 45.0, 38.0]
    s = np.zeros(n, dtype=np.float32)
    for f, d in zip(modes, decays):
        s += np.exp(-t * d) * np.sin(2*np.pi*f*t)
    # Second micro-settle bounce 42ms later
    t2 = np.maximum(0.0, t - 0.042)
    for f, d in zip(modes, decays):
        s += 0.45 * (t >= 0.042) * np.exp(-t2 * (d * 1.3)) * np.sin(2*np.pi*(f*1.012)*t2)
    wood_tap = np.exp(-t * 140.0) * 0.5 * np.sin(2*np.pi*420*t)
    s += wood_tap
    return fade_io(s / (np.max(np.abs(s)) + 1e-9), 0.001, 0.06)

def synth_claw_skitter(dur_s, rate_hz=15.8, grit_freq=4200.0, pan_start=-0.55, pan_end=0.55):
    """Stereo-panned 6-legged cockroach tarsal skitter across hardwood or acrylic."""
    n = int(dur_s * SR)
    out = np.zeros((n, 2), dtype=np.float32)
    step_interval = 1.0 / (rate_hz * 3.0) # 3 claws per tripod half-stride
    t_cursor = 0.0
    b_bp, a_bp = signal.butter(2, [1400/(SR*0.5), min(0.92, grit_freq*1.8/(SR*0.5))], btype="bandpass")
    while t_cursor < dur_s - 0.03:
        m = int(0.024 * SR)
        tt = np.arange(m, dtype=np.float32) / SR
        burst = np.exp(-tt * 220.0) * signal.lfilter(b_bp, a_bp, rng.standard_normal(m).astype(np.float32))
        burst += 0.35 * np.exp(-tt * 310.0) * np.sin(2*np.pi*(grit_freq * rng.uniform(0.85, 1.15))*tt)
        idx = int(t_cursor * SR)
        u = t_cursor / max(1e-4, dur_s)
        pan = pan_start + (pan_end - pan_start) * u + rng.uniform(-0.08, 0.08)
        gl = math.cos((pan + 1.0) * math.pi * 0.25)
        gr = math.sin((pan + 1.0) * math.pi * 0.25)
        L = min(m, n - idx)
        gain = 0.65 + 0.35 * rng.random()
        out[idx:idx+L, 0] += burst[:L] * gl * gain
        out[idx:idx+L, 1] += burst[:L] * gr * gain
        t_cursor += step_interval * rng.uniform(0.82, 1.18)
    pk = float(np.max(np.abs(out)) + 1e-9)
    return fade_io(out / pk, 0.03, 0.05)

def synth_crampon_scrape(dur_s, coarseness=0.5):
    """Tactile tibial-spine crampon rake + silicon-carbide grain crunch."""
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    noise = rng.standard_normal(n).astype(np.float32)
    lo = 650.0 if coarseness > 0.7 else (1200.0 if coarseness > 0.35 else 2800.0)
    hi = 3400.0 if coarseness > 0.7 else (5800.0 if coarseness > 0.35 else 9200.0)
    b, a = signal.butter(2, [lo/(SR*0.5), hi/(SR*0.5)], btype="bandpass")
    shaped = signal.lfilter(b, a, noise)
    # Rhythmic oar-stroke modulation (~7 Hz under 4mm confinement)
    mod = 0.30 + 0.70 * np.maximum(0.0, np.sin(2*np.pi*6.8*t))**1.6
    # Add discrete spine micro-clicks on coarse/medium grit
    clicks = np.zeros(n, dtype=np.float32)
    if coarseness >= 0.35:
        for k in range(int(dur_s * 34)):
            ci = int(rng.uniform(0, n - 400))
            ct = np.arange(380, dtype=np.float32) / SR
            clicks[ci:ci+380] += rng.uniform(0.3, 0.9) * np.exp(-ct * 260.0) * np.sin(2*np.pi*rng.uniform(1800, 4400)*ct)
    s = shaped * mod + 0.55 * clicks
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s * 0.95, np.roll(s, 14) * 0.95], axis=1), 0.04, 0.06)

def synth_chitin_shingle_fold(dur_s=1.8):
    """Delicate overlapping chitin plate micro-clicks + soft viscoelastic membrane crease."""
    n = int(dur_s * SR)
    s = np.zeros(n, dtype=np.float32)
    for k in range(11):
        t0 = 0.08 + k * (dur_s - 0.22) / 11.0
        idx = int(t0 * SR)
        m = int(0.045 * SR)
        tt = np.arange(m, dtype=np.float32) / SR
        f0 = 1650 + k * 140
        pulse = np.exp(-tt * 170.0) * (0.7 * np.sin(2*np.pi*f0*tt) + 0.4 * np.sin(2*np.pi*(f0*1.62)*tt))
        L = min(m, n - idx)
        s[idx:idx+L] += pulse[:L] * (0.55 + 0.35 * math.sin(k))
    s /= (np.max(np.abs(s)) + 1e-9)
    return fade_io(np.stack([s, np.roll(s, 18)], axis=1), 0.02, 0.05)

def synth_servo_press(dur_s=2.4):
    """Precision laboratory motorized compression stage whirr + 6.08N load lock."""
    n = int(dur_s * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f_sweep = 185.0 + 95.0 * np.sin(math.pi * np.clip(t / dur_s, 0, 1))
    phase = 2 * np.pi * np.cumsum(f_sweep) / SR
    whirr = 0.45 * np.sin(phase) + 0.22 * np.sin(2.0 * phase) + 0.12 * np.sin(3.0 * phase)
    env = np.sin(math.pi * np.clip(t / dur_s, 0, 1))**0.5
    s = (whirr * env).astype(np.float32)
    return fade_io(np.stack([s, s], axis=1), 0.08, 0.12)

foley_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)

# --- CH01: Midnight apartment light switch, bolt across oak floor, pennies, sub-second vanish, paradox stop ---
place(foley_bus, synth_wall_switch(), 42 / FPS, gain=0.42, pan=-0.28)
place(foley_bus, sfx_whoosh_deep,     45 / FPS, gain=0.26, pan=-0.15) # Camera whip-dive from switch to floor!
place(foley_bus, synth_claw_skitter(3.8, 16.2, 4400, -0.6, 0.3), 50 / FPS, gain=0.19)
place(foley_bus, synth_coin_clink(),  255 / FPS, gain=0.30, pan=0.22)  # Two stacked pennies!
place(foley_bus, sfx_riser_air,       318 / FPS, gain=0.20, pan=0.0)   # Riser into protected vanish climax!
place(foley_bus, synth_claw_skitter(1.6, 17.5, 4800, -0.35, 0.15), 376 / FPS, gain=0.24)
place(foley_bus, sfx_whoosh_mid,      468 / FPS, gain=0.34, pan=0.10)  # Sub-second vanish under the door!
place(foley_bus, synth_chitin_shingle_fold(0.75), 470 / FPS, gain=0.24)
place(foley_bus, sfx_sub_drop,        595 / FPS, gain=0.40, pan=0.0)   # "Wait a second." visceral sub-drop!
place(foley_bus, sfx_click_crisp,     738 / FPS, gain=0.16, pan=-0.1)

# --- CH02: 500 FPS camera trigger, 5 distinct biomechanical moves, X-ray chitin roof-tile fold ---
place(foley_bus, sfx_whoosh_deep,     1080 / FPS, gain=0.28, pan=0.0)  # Ch02 transition into UC Berkeley lab
place(foley_bus, sfx_sub_drop,        1173 / FPS, gain=0.30, pan=0.0)  # 500 FPS bullet-time engage!
place(foley_bus, sfx_click_crisp,     1175 / FPS, gain=0.22, pan=0.25) # Phantom 500fps shutter click
# 5 moves tactile cues
place(foley_bus, sfx_pop_soft,        1474 / FPS, gain=0.20, pan=-0.2) # Move 1: Antennae sweep
place(foley_bus, sfx_click_crisp,     1542 / FPS, gain=0.22, pan=-0.1) # Move 2: Head tips down & wedges
place(foley_bus, synth_chitin_shingle_fold(0.9), 1642 / FPS, gain=0.22, pan=0.0) # Move 3: Pronotum shield rolls
place(foley_bus, synth_crampon_scrape(1.1, 0.55), 1770 / FPS, gain=0.22, pan=0.15) # Move 4: Hind legs shove chest
place(foley_bus, sfx_whoosh_mid,      1916 / FPS, gain=0.24, pan=0.25) # Move 5: Flattened abdomen clears!
# X-ray cutaway shingle & arthrodial hinge fold
place(foley_bus, sfx_whoosh_deep,     2007 / FPS, gain=0.22, pan=0.0)  # Dissolve to 3D X-ray cutaway!
place(foley_bus, synth_chitin_shingle_fold(2.4), 2160 / FPS, gain=0.28, pan=0.0)

# --- CH03: 15cm confined corridor, researcher micrometer roof steps (12->9->6->4mm), 4x speed crash ---
place(foley_bus, sfx_whoosh_mid,      2586 / FPS, gain=0.26, pan=0.0)
place(foley_bus, synth_claw_skitter(3.2, 16.4, 5200, -0.5, 0.5), 2925 / FPS, gain=0.18)
for mf in [3035, 3095, 3155]:
    place(foley_bus, sfx_click_crisp, mf / FPS, gain=0.22, pan=0.28)   # Micrometer Vernier clicks (12->9->6mm)
place(foley_bus, synth_claw_skitter(4.5, 16.1, 5400, -0.45, 0.45), 3344 / FPS, gain=0.20) # Full 58 cm/s sprint holds!
place(foley_bus, sfx_riser_smooth,    3605 / FPS, gain=0.22, pan=0.0)  # Riser into 4mm squeeze!
place(foley_bus, sfx_click_crisp,     3666 / FPS, gain=0.26, pan=0.28) # Final 4mm roof drop!
place(foley_bus, sfx_sub_drop,        3832 / FPS, gain=0.38, pan=0.0)  # Speed crashes 4x to 14.5 cm/s!
place(foley_bus, synth_crampon_scrape(2.2, 0.45), 3845 / FPS, gain=0.18)

# --- CH04: Tarsal claw engagement -> >80° sprawl -> 3D Human wide-arm push-up -> Macro Crampon Climax! ---
place(foley_bus, sfx_whoosh_deep,     4099 / FPS, gain=0.26, pan=0.0)
place(foley_bus, synth_claw_skitter(2.6, 14.5, 5000, -0.2, 0.2), 4385 / FPS, gain=0.17)
place(foley_bus, sfx_click_crisp,     4652 / FPS, gain=0.22, pan=0.0)  # Ceiling presses down!
place(foley_bus, sfx_whoosh_mid,      4868 / FPS, gain=0.28, pan=-0.2) # Cut to 3D Human Athlete push-up stage!
place(foley_bus, sfx_pop_soft,        4925 / FPS, gain=0.20, pan=0.0)  # Arms slide past 80 degrees!
place(foley_bus, sfx_whoosh_deep,     5006 / FPS, gain=0.28, pan=0.2)  # Match-cut back to splayed cockroach tibia!
place(foley_bus, sfx_riser_smooth,    5125 / FPS, gain=0.25, pan=0.0)  # Build into Protected Macro Spine Climax!
# [5197..5469] PROTECTED MACRO TIBIAL SPINE CLIMAX!
place(foley_bus, sfx_sub_drop,        5198 / FPS, gain=0.34, pan=0.0)
place(foley_bus, synth_crampon_scrape(4.6, 0.60), 5202 / FPS, gain=0.34, pan=0.05) # Rich tactile crampon bite!
place(foley_bus, synth_crampon_scrape(3.2, 0.55), 5548 / FPS, gain=0.22, pan=0.0)  # Synchronous middle-leg oar stroke!

# --- CH05: Friction isolation & 638-run grit trade-off (100-grit slip vs 40-grit win vs 20-grit belly snag) ---
place(foley_bus, sfx_whoosh_mid,      6012 / FPS, gain=0.26, pan=0.0)
place(foley_bus, synth_crampon_scrape(1.8, 0.60), 6244 / FPS, gain=0.22, pan=-0.15)
place(foley_bus, sfx_pop_soft,        6585 / FPS, gain=0.24, pan=0.0)  # "Right?" curiosity beat!
place(foley_bus, synth_crampon_scrape(1.5, 0.15), 7084 / FPS, gain=0.20, pan=-0.35) # 100-grit slick slip!
place(foley_bus, synth_crampon_scrape(2.2, 0.92), 7185 / FPS, gain=0.28, pan=0.35)  # 20-grit coarse belly snag!

# --- CH06: 900x Body Weight Compression Press -> 76.7 cm/s sprint -> 315 Gate Attempts (17% pass) ---
place(foley_bus, sfx_whoosh_deep,     7456 / FPS, gain=0.28, pan=0.0)
place(foley_bus, synth_servo_press(3.0), 7490 / FPS, gain=0.24, pan=0.0)
place(foley_bus, sfx_sub_drop,        7677 / FPS, gain=0.42, pan=0.0)  # 900x BODY WEIGHT PEAK!
place(foley_bus, synth_chitin_shingle_fold(1.2), 7680 / FPS, gain=0.24)
place(foley_bus, synth_claw_skitter(2.4, 19.5, 5200, -0.5, 0.65), 7780 / FPS, gain=0.26) # 76.7 cm/s unimpaired sprint!
place(foley_bus, sfx_riser_air,       8370 / FPS, gain=0.24, pan=0.0)
place(foley_bus, sfx_sub_drop,        8608 / FPS, gain=0.36, pan=0.0)  # "Only seventeen percent made it through."
place(foley_bus, sfx_pop_soft,        8710 / FPS, gain=0.20, pan=-0.25) # Antennal rejection & turn-back
place(foley_bus, sfx_click_crisp,     8865 / FPS, gain=0.24, pan=0.25)  # 9% chest-wedged stop!

# --- CH07: Real-Speed 1x Reprise, Viscoelastic Rebound, Closing Quiet Hold ---
place(foley_bus, sfx_whoosh_deep,     9070 / FPS, gain=0.28, pan=0.0)
# [9182..9572] PROTECTED REAL-SPEED REPRISE CLIMAX!
place(foley_bus, synth_claw_skitter(1.3, 17.2, 4500, -0.55, 0.0), 9185 / FPS, gain=0.25)
place(foley_bus, sfx_whoosh_mid,      9235 / FPS, gain=0.34, pan=0.08) # Real-speed 1x zip under door!
place(foley_bus, synth_chitin_shingle_fold(1.1), 9375 / FPS, gain=0.26, pan=0.15) # Hinges spring shell back!
place(foley_bus, synth_claw_skitter(1.8, 17.5, 4500, 0.1, 0.65), 9555 / FPS, gain=0.24) # Feet take over sprint!
place(foley_bus, sfx_sub_drop,        9881 / FPS, gain=0.28, pan=0.0)  # Final thesis resolution pulse!

# ---------------------------------------------------------------------------
# 4. HYPNOTIC DARK-SCIENCE CINEMA SCORE (EVOLVING 7-CHAPTER OSTINATO + SUB-PULSE)
# ---------------------------------------------------------------------------
music_bus = np.zeros((N_SAMPLES, 2), dtype=np.float32)
t_full = np.arange(N_SAMPLES, dtype=np.float32) / SR

# Chapter harmonic roots (Hz): D2 (73.42), A1 (55.0), G1 (49.0), Bb1 (58.27), F1 (43.65)
ch_progression = [
    (0.8,   36.0,  [73.42, 65.41, 58.27, 55.00], [293.66, 349.23, 440.00, 466.16, 440.00, 349.23]), # Ch1: D minor midnight tension
    (36.0,  86.2,  [55.00, 58.27, 73.42, 65.41], [440.00, 523.25, 659.25, 587.33, 523.25, 440.00]), # Ch2: 500fps glass precision
    (86.2,  136.6, [73.42, 87.31, 65.41, 58.27], [293.66, 440.00, 587.33, 523.25, 440.00, 392.00]), # Ch3: Fast corridor sprint beat
    (136.6, 200.4, [55.00, 58.27, 55.00, 49.00], [329.63, 349.23, 440.00, 523.25, 466.16, 349.23]), # Ch4: A Phrygian crampon revelation
    (200.4, 248.5, [65.41, 58.27, 73.42, 55.00], [392.00, 440.00, 523.25, 587.33, 440.00, 349.23]), # Ch5: Scientific puzzle / bet
    (248.5, 302.3, [49.00, 58.27, 65.41, 73.42], [293.66, 392.00, 466.16, 587.33, 523.25, 392.00]), # Ch6: Heavy load & 17% stakes
    (302.3, 343.4, [73.42, 58.27, 65.41, 73.42], [293.66, 440.00, 523.25, 659.25, 587.33, 440.00]), # Ch7: Lucid synthesis & wonder
]

for t0, t1, bass_roots, mallet_notes in ch_progression:
    i0, i1 = int(t0 * SR), min(N_SAMPLES, int(t1 * SR))
    seg_len = i1 - i0
    tt = np.arange(seg_len, dtype=np.float32) / SR

    # Warm analog sub-pad changing bar every 6.0s
    bar_len = 6.0
    pad_l = np.zeros(seg_len, dtype=np.float32)
    pad_r = np.zeros(seg_len, dtype=np.float32)
    n_bars = int(math.ceil((t1 - t0) / bar_len))
    for b in range(n_bars):
        bs0 = int(b * bar_len * SR)
        bs1 = min(seg_len, int((b + 1.15) * bar_len * SR))
        if bs1 <= bs0:
            continue
        bt = np.arange(bs1 - bs0, dtype=np.float32) / SR
        f_root = bass_roots[b % len(bass_roots)]
        w = np.sin(math.pi * np.clip(bt / ((bs1 - bs0)/SR), 0, 1))**0.75
        # Sub fundamental + warm fifth + gentle detuned shimmer
        tone_l = 0.55 * np.sin(2*np.pi*f_root*bt) + 0.25 * np.sin(2*np.pi*(f_root*1.498)*bt) + 0.14 * np.sin(2*np.pi*(f_root*2.003)*bt)
        tone_r = 0.55 * np.sin(2*np.pi*f_root*bt) + 0.25 * np.sin(2*np.pi*(f_root*1.502)*bt) + 0.14 * np.sin(2*np.pi*(f_root*1.997)*bt)
        pad_l[bs0:bs1] += tone_l * w
        pad_r[bs0:bs1] += tone_r * w

    # Delicate glass-marimba / kalimba stereo pulse (KQED Deep Look / Veritasium texture!)
    step_s = 0.375 # 160 BPM eighth-note pulse
    n_steps = int((t1 - t0) / step_s)
    for st in range(n_steps):
        # Leave subtle breathing space on every 8th beat
        if st % 8 == 7:
            continue
        ms0 = int(st * step_s * SR)
        mlen = min(int(0.42 * SR), seg_len - ms0)
        if mlen <= 64:
            continue
        mt = np.arange(mlen, dtype=np.float32) / SR
        fn = mallet_notes[st % len(mallet_notes)]
        mallet = np.exp(-mt * 11.5) * np.sin(2*np.pi*fn*mt) + 0.22 * np.exp(-mt * 28.0) * np.sin(2*np.pi*(fn*3.0)*mt)
        pan_m = 0.38 * math.sin(st * 0.9)
        pad_l[ms0:ms0+mlen] += 0.22 * mallet * (0.5 - 0.5 * pan_m)
        pad_r[ms0:ms0+mlen] += 0.22 * mallet * (0.5 + 0.5 * pan_m)

    seg_stereo = fade_io(np.stack([pad_l, pad_r], axis=1), 0.35, 0.55)
    music_bus[i0:i1] += seg_stereo * 0.14

# Dramatic silence pocket right at "Wait a second." [594..636] so the sub-drop & hook hit 10x harder!
s_hush0, s_hush1 = int(590 / FPS * SR), int(642 / FPS * SR)
hush_env = np.ones(N_SAMPLES, dtype=np.float32)
hush_env[s_hush0:s_hush1] = np.linspace(0.15, 0.15, s_hush1 - s_hush0)
# Gentle fade out over final 4 seconds [10180..10302]
f_end0 = int(10160 / FPS * SR)
hush_env[f_end0:] *= np.linspace(1.0, 0.0, N_SAMPLES - f_end0, dtype=np.float32)

# Apply smooth sidechain ducking (-6.0 dB under voice, full bloom during pauses & protected climaxes!)
sidechain_gain = (1.0 - 0.52 * duck_smooth) * hush_env
music_bus *= sidechain_gain[:, None]
# Also gently duck foley 2.2 dB under active syllables so speech consonants stay razor-clear!
foley_ducked = foley_bus * (1.0 - 0.24 * duck_smooth)[:, None]

# ---------------------------------------------------------------------------
# 5. MASTER SUMMING & EBU R128 / -14.2 LUFS + -1.5 dBTP TRUE-PEAK LIMITING
# ---------------------------------------------------------------------------
raw_mix = vo_bus * 1.05 + foley_ducked * 0.88 + music_bus * 0.92
tmp_raw_path = "/tmp/v4_audio/pre_master_v4.wav"
sf.write(tmp_raw_path, np.clip(raw_mix, -0.99, 0.99), SR, subtype="PCM_24")

master_mix_path = f"{OUT_DIR}/Monarch-Cam-03-Long-Video-Master-Mix-V4.wav"
# Two-pass loudnorm to exact -14.2 LUFS, TP=-1.5 dBTP, LRA=9
p1 = subprocess.run(
    [FFMPEG, "-y", "-i", tmp_raw_path, "-af", "loudnorm=I=-14.2:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"],
    capture_output=True, text=True, check=True
)
j_txt = p1.stderr[p1.stderr.rfind("{"):p1.stderr.rfind("}")+1]
ln = json.loads(j_txt)
af_pass2 = (
    f"loudnorm=I=-14.2:TP=-1.5:LRA=9:measured_I={ln['input_i']}:"
    f"measured_TP={ln['input_tp']}:measured_LRA={ln['input_lra']}:"
    f"measured_thresh={ln['input_thresh']}:offset={ln['target_offset']}:linear=true:print_format=summary,"
    f"alimiter=limit=-1.5dB:level=false"
)
subprocess.run(
    [FFMPEG, "-y", "-i", tmp_raw_path, "-af", af_pass2, "-ar", "48000", "-c:a", "pcm_s24le", master_mix_path],
    check=True, capture_output=True
)

# Verify final LUFS & True Peak!
verify = subprocess.run(
    [FFMPEG, "-i", master_mix_path, "-af", "ebur128=peak=true", "-f", "null", "-"],
    capture_output=True, text=True, check=True
)
tail_lines = [l for l in verify.stderr.splitlines() if any(k in l for k in ["I:", "LRA:", "Peak:"])][-6:]
print("MASTER MIX V4 EBU R128:", "\n  ".join(tail_lines))

# ---------------------------------------------------------------------------
# 6. EXPORT EXACT .SRT & .VTT CAPTIONS + VOICE-LOCK-V4.JSON
# ---------------------------------------------------------------------------
def fmt_srt(sec):
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def fmt_vtt(sec):
    return fmt_srt(sec).replace(",", ".")

srt_lines = []
vtt_lines = ["WEBVTT", ""]
cue_idx = 1
for ch in tl["chapters"]:
    for s in ch["sentences"]:
        t0 = s["abs_start_f"] / FPS
        t1 = max(t0 + 0.45, s["abs_end_f"] / FPS - 0.04)
        srt_lines += [str(cue_idx), f"{fmt_srt(t0)} --> {fmt_srt(t1)}", s["text"], ""]
        vtt_lines += [f"{fmt_vtt(t0)} --> {fmt_vtt(t1)}", s["text"], ""]
        cue_idx += 1

open(f"{OUT_DIR}/Monarch-Cam-03-Captions-V4.srt", "w").write("\n".join(srt_lines))
open(f"{OUT_DIR}/Monarch-Cam-03-Captions-V4.vtt", "w").write("\n".join(vtt_lines))

tl["voice_id"] = "voice-02"
tl["selection_provenance"] = "Synthesized via Arena generate_speech (voice-02, masculine en-US narration; battle_id '02' auto-assigned after owner skipped prompt)"
tl["time_stretch_applied"] = False
tl["sample_rate_hz"] = 48000
tl["bit_depth"] = 24
tl["master_mix_wav"] = master_mix_path
tl["dry_vo_wav"] = dry_vo_path
json.dump(tl, open(f"{V4_DIR}/voice-lock-v4.json", "w"), indent=2)
print("Saved V4 Audio Master, Dry VO, SRT, VTT, and voice-lock-v4.json successfully!")