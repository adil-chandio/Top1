#!/usr/bin/env python3
import os, sys, math, json, glob, subprocess
sys.path.insert(0, '/tmp/py')
sys.path.insert(0, '/home/user/Top1/tools/monarch-v6-imax-sdk/python')
import numpy as np
from scipy import signal
import soundfile as sf
from audio_imax_dsp import (
    SR, find_ffmpeg, load_wav_48k_stereo, fade_io, place_clip,
    tighten_vo_zero_stretch, compute_lookahead_duck_envelope,
    synth_imax_braam, synth_vacuum_suction, synth_chronometer_ticks,
    synth_modal_impact, synth_laser_tomography_sweep, synth_loop_locked_score, apply_vacuum_window,
    master_ebu_r128_linear, write_srt_vtt
)

ROOT = '/home/user/Top1'
OUT_DIR = '/tmp/audio'
os.makedirs(OUT_DIR, exist_ok=True)
VO_RAW = '/tmp/audio/vo_raw.wav'
MASTER_WAV = '/tmp/audio/master_mix.wav'
MASTER_AAC = '/tmp/audio/master_mix.m4a'

TOTAL_DUR = 35.0  # 1050 frames @30fps, loop-friendly
N = int(TOTAL_DUR * SR)

# Load & tighten VO (zero stretch)
vo = load_wav_48k_stereo(VO_RAW)
vo = tighten_vo_zero_stretch(vo, rms_thresh=0.0015, pre_guard_s=0.020, post_guard_s=0.030, max_gap_s=0.18)
vo_dur = len(vo) / SR
print(f'VO tightened duration: {vo_dur:.3f}s')

# Build buses
music = np.zeros((N, 2), dtype=np.float32)
foley = np.zeros((N, 2), dtype=np.float32)
vo_bus = np.zeros((N, 2), dtype=np.float32)

# Place VO at 0.15s
VO_START = 0.15
place_clip(vo_bus, vo, VO_START, gain=1.0)

# Twist beat: "Wait. They were not enemies." ~8.8s in original; after tightening estimate proportionally
# Approx word position: "Wait" is 25th word of 88 => 28.4% into VO
twist_vo_t = VO_START + vo_dur * 0.284
vac_start = max(0.2, twist_vo_t - 0.20)
vac_end = vac_start + 0.18  # 180ms vacuum
print(f'Twist vacuum: {vac_start:.3f}-{vac_end:.3f}s, twist_vo_t={twist_vo_t:.3f}s')

# Music: loop-locked score
score = synth_loop_locked_score(TOTAL_DUR, base_hz=46.25)  # Bb1-ish dark pad
place_clip(music, score, 0.0, gain=0.34)

# Hook hit <1s: braam + impact
braam = synth_imax_braam(dur_s=1.6, root_hz=38.89)  # D#1
place_clip(music, braam, 0.20, gain=0.55)
impact = synth_modal_impact(dur_s=0.9, sub_hz=72.0)
place_clip(foley, impact, 0.35, gain=0.45)

# Twist impact/braam after vacuum
braam2 = synth_imax_braam(dur_s=1.2, root_hz=41.20)
place_clip(music, braam2, vac_end + 0.02, gain=0.40)
place_clip(foley, synth_modal_impact(dur_s=0.7, sub_hz=68.0), vac_end + 0.02, gain=0.30)

# 3s auditory pattern interrupts / foley hits
hit_times = [3.2, 6.0, 11.5, 14.5, 17.5, 20.5, 23.5, 26.5, 29.5]
for i, ht in enumerate(hit_times):
    if ht < TOTAL_DUR - 0.5:
        place_clip(foley, synth_modal_impact(dur_s=0.55, modes=((900+120*i, 40.0),(1800+80*i,55.0),(3200,70.0)), sub_hz=65.0+i), ht, gain=0.18, pan=(-0.25 if i%2==0 else 0.25))
        if i % 2 == 0:
            place_clip(foley, synth_laser_tomography_sweep(dur_s=0.6), ht+0.05, gain=0.10, pan=0.3)

# Chronometer ticks around evidence/reveal section
ticks = synth_chronometer_ticks(dur_s=4.0, rate_hz=8.0)
place_clip(foley, ticks, 9.5, gain=0.06)
place_clip(foley, synth_chronometer_ticks(dur_s=3.0, rate_hz=8.0), 18.0, gain=0.04)

# Flood whoosh near payoff
whoosh = synth_vacuum_suction(dur_s=1.2, seed=4242)
# reverse-ish swell by fading in
whoosh_env = np.linspace(0,1,len(whoosh))[:,None]**1.5
place_clip(foley, whoosh * whoosh_env, 24.5, gain=0.22)

# Final settle impact
place_clip(foley, synth_modal_impact(dur_s=1.0, sub_hz=55.0), 30.8, gain=0.20)

# Ducking
duck = compute_lookahead_duck_envelope(vo_bus, lookahead_s=0.055)
bed = (music + foley)
for ch in range(2):
    bed[:, ch] *= (1.0 - 0.38 * duck)

# Apply vacuum window to full bed (and lightly to VO tail-in is not needed; VO has no speech there)
apply_vacuum_window(bed, vac_start, vac_end, taper_s=0.010)
# Ensure VO also silent in vacuum (should already be between words)
apply_vacuum_window(vo_bus, vac_start, vac_end, taper_s=0.008)

mix = bed + vo_bus * 1.0
# gentle safety clip
mix = np.tanh(mix * 1.1) / 1.1
mix = mix.astype(np.float32)

# Write pre-master then EBU R128
pre = '/tmp/audio/pre_master.wav'
sf.write(pre, mix, SR, subtype='PCM_24')
stats = master_ebu_r128_linear(mix, MASTER_WAV, target_i=-14.2, target_tp=-1.5)
print('Loudnorm stats:', stats)

# AAC mux-friendly copy with limiter for true peak guard
ffmpeg = find_ffmpeg()
subprocess.run([
    ffmpeg, '-y', '-i', MASTER_WAV,
    '-af', 'alimiter=limit=0.708:level=false',
    '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-ac', '2',
    MASTER_AAC
], check=True, capture_output=True, text=True)

# Captions SRT/VTT (simple timed cues)
cues = [
    {"t0": 0.15, "t1": 1.80, "text": "THIS ROCK HOLDS\nTWO ANIMALS"},
    {"t0": 1.90, "t1": 5.20, "text": "250 MILLION YEARS AGO\nONE CURLED UP ASLEEP"},
    {"t0": 5.30, "t1": 8.60, "text": "A MAMMAL RELATIVE\nBESIDE AN AMPHIBIAN"},
    {"t0": 8.95, "t1": 10.80, "text": "WAIT.\nNOT ENEMIES."},
    {"t0": 10.90, "t1": 14.20, "text": "HEALING RIBS\nNO BITE MARKS"},
    {"t0": 14.30, "t1": 16.00, "text": "NOT A HUNT"},
    {"t0": 16.10, "t1": 19.20, "text": "IT CRAWLED IN\nFOR SHELTER"},
    {"t0": 19.30, "t1": 23.00, "text": "THE OTHER IN\nAESTIVATION"},
    {"t0": 23.10, "t1": 26.60, "text": "A FLOOD FILLED\nTHE BURROW"},
    {"t0": 26.70, "t1": 29.60, "text": "THE CLUE\nTHE ROCK KEPT"},
    {"t0": 29.70, "t1": 32.20, "text": "TWO ANIMALS\nONE ROCK"},
]
write_srt_vtt(cues, '/tmp/audio/captions.srt', '/tmp/audio/captions.vtt')

# Write audio qa json
qa = {
    "vo_raw": VO_RAW,
    "vo_tightened_duration_s": vo_dur,
    "total_duration_s": TOTAL_DUR,
    "twist_vacuum_s": [vac_start, vac_end],
    "time_stretch_applied": False,
    "loudnorm_pass1": stats,
    "master_wav": MASTER_WAV,
    "master_aac": MASTER_AAC,
}
with open('/tmp/audio/audio_qa_build.json','w') as f: json.dump(qa, f, indent=2)
print(json.dumps({"ok": True, "vo_dur": vo_dur, "total": TOTAL_DUR, "twist": [vac_start, vac_end]}))
