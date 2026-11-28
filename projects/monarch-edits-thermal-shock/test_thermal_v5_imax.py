#!/usr/bin/env python3
"""
Gate 7 Forensic Verification Suite — Monarch Edits Thermal Shock V5 Plugin-Grade Hollywood IMAX.
Verifies the actual muxed H.264 + AAC deliverable (`exports/thermal-shock-v5-imax/Thermal-Shock-V5-Plugin-IMAX.mp4`)
against every Top1 V6 IMAX law plus all V3/V4 regression traps.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, '/tmp/py')
sys.path.insert(0, '/home/user/Top1/tools/monarch-v6-imax-sdk/python')

import numpy as np
from PIL import Image, ImageDraw
import forensic_qa_sdk as qa

ROOT = '/home/user/Top1'
MP4_PATH = os.path.join(ROOT, 'exports/thermal-shock-v5-imax/Thermal-Shock-V5-Plugin-IMAX.mp4')
LOCK_PATH = os.path.join(ROOT, 'projects/monarch-edits-thermal-shock/voice-lock-v5-imax.json')
SHEET_24_PATH = os.path.join(ROOT, 'exports/thermal-shock-v5-imax/24Frame-Forensic-MP4-Sheet-V5.jpg')
FFMPEG_BIN = qa.find_ffmpeg()


def decode_exact_mp4_frames(mp4_path: str, target_indices: list[int]) -> dict[int, np.ndarray]:
    """Stream-decode exact frame indices (0..1199) in a single O(1)-RAM pass with zero seek rounding."""
    wanted = set(target_indices)
    max_idx = max(wanted)
    frame_bytes = 1080 * 1920 * 3
    proc = subprocess.Popen(
        [
            FFMPEG_BIN, '-v', 'error', '-i', mp4_path,
            '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1',
        ],
        stdout=subprocess.PIPE,
    )
    out = {}
    idx = 0
    try:
        while idx <= max_idx:
            buf = proc.stdout.read(frame_bytes)
            if not buf or len(buf) < frame_bytes:
                break
            if idx in wanted:
                out[idx] = np.frombuffer(buf, dtype=np.uint8).reshape((1920, 1080, 3)).copy()
            idx += 1
    finally:
        proc.terminate()
        proc.wait()
    return out


def decode_mp4_audio_f32(mp4_path: str, sr: int = 48000) -> np.ndarray:
    raw = subprocess.check_output([
        FFMPEG_BIN, '-v', 'error', '-i', mp4_path,
        '-vn', '-f', 'f32le', '-ac', '2', '-ar', str(sr), 'pipe:1',
    ])
    return np.frombuffer(raw, dtype=np.float32).reshape((-1, 2))


def bt709_luma(rgb: np.ndarray) -> float:
    f = rgb.astype(np.float32)
    return float((0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]).mean())


def test_v6_imax_sdk_master_audit():
    assert os.path.exists(MP4_PATH), f'Missing final MP4: {MP4_PATH}'
    with open(LOCK_PATH) as f:
        lock = json.load(f)

    shot_cuts = {s['f0'] for s in lock['shots']} | {lock['shatter_f'], lock['shatter_f'] + 1}
    vac_w = tuple(lock['vacuum_qa_window'])

    report = qa.verify_imax_mp4(
        MP4_PATH,
        expected_frames=1200,
        shot_cuts=shot_cuts,
        check_seamless_loop=True,
        max_loop_mae=2.0,
        vacuum_window_s=vac_w,
        scale_w=180,
        scale_h=320,
    )
    print('\n[SDK STREAMING FORENSIC REPORT]:\n' + json.dumps(report, indent=2))
    assert report['decoded_frames'] == 1200
    assert report['aba_spikes'] == 0
    assert report['loop_mae'] < 2.0
    assert report['vacuum_rms_db'] < -85.0, f"Post-AAC vacuum noisy: {report['vacuum_rms_db']:.1f} dBFS"


def test_shatter_flash_cutaway_blast_and_24frame_sheet():
    with open(LOCK_PATH) as f:
        lock = json.load(f)

    shatter_f = lock['shatter_f']  # 685
    sample_frames = [
        0, 50, 120, 175, 240, 290,
        350, 385, 460, 565, 655, 682,
        685, 692, 695, 705, 730, 785,
        800, 920, 965, 1065, 1150, 1199,
    ]
    frames = decode_exact_mp4_frames(MP4_PATH, sample_frames)
    assert len(frames) == len(sample_frames), f'Missing decoded frames: {set(sample_frames) - set(frames)}'

    # 1. Verify post-ACES optical flash at exact Frame 685 (`Y >= 218 / 255` broadcast TV-range whiteout, 4x V3's 56/255!)
    f_flash = frames[shatter_f]
    flash_y = bt709_luma(f_flash)
    flash_rgb = float(f_flash.mean())
    flash_p95 = float(np.percentile(f_flash, 95))
    print(f'[Forensic] Exact Frame {shatter_f} Flash BT.709 Luma Y={flash_y:.1f}/255 | Mean RGB={flash_rgb:.1f}/255 | p95={flash_p95:.1f}/255')
    assert flash_y >= 218.0 and flash_rgb >= 215.0 and flash_p95 >= 242.0

    # 2. Verify full-res exact Frame 0 <-> Frame 1199 loop seam MAE (< 2.0 / 255!)
    full_loop_mae = float(np.abs(frames[0].astype(np.float32) - frames[1199].astype(np.float32)).mean())
    print(f'[Forensic] Full-Res 1080x1920 Decoded MP4 Loop MAE(f0, f1199) = {full_loop_mae:.3f} / 255')
    assert full_loop_mae < 2.0

    # 3. Verify middle-act cutaway & atomic lattice brightness (never muddy dark!)
    for cf in (385, 565, 655):
        arr = frames[cf]
        mean_l = bt709_luma(arr)
        p99_l = float(np.percentile(arr, 99))
        print(f'[Forensic] Cutaway/Atomic Frame {cf}: Y={mean_l:.1f}/255, p99={p99_l:.1f}/255')
        assert mean_l >= 32.0
        assert p99_l >= 200.0

    # 4. Verify 96-shard explosion motion & populated floor shards
    diff_ab = float(np.mean(np.abs(frames[695].astype(np.float32) - frames[705].astype(np.float32))))
    shard_p99 = float(np.percentile(frames[800], 99))
    print(f'[Forensic] Bullet-time motion MAE(695->705)={diff_ab:.2f}/255 | Floor Shards f=800 p99={shard_p99:.1f}/255')
    assert diff_ab >= 4.0
    assert shard_p99 >= 200.0

    # 5. Verify post-AAC explosion dynamic punch (`>= +8.5 dB` over build-up!)
    sr = 48000
    pcm = decode_mp4_audio_f32(MP4_PATH, sr=sr)
    build_seg = pcm[int(14.0 * sr):int(20.0 * sr)]
    blast_seg = pcm[int(22.833 * sr):int(24.133 * sr)]
    rms_build = 20.0 * np.log10(max(1e-12, float(np.sqrt(np.mean(build_seg ** 2)))))
    rms_blast = 20.0 * np.log10(max(1e-12, float(np.sqrt(np.mean(blast_seg ** 2)))))
    contrast_db = rms_blast - rms_build
    print(f'[Forensic] Post-AAC Build RMS={rms_build:.2f} dBFS | Blast RMS={rms_blast:.2f} dBFS | Contrast=+{contrast_db:.2f} dB')
    assert contrast_db >= 8.5

    # 6. Build 24-Frame Decoded MP4 Forensic Proof Sheet
    cols, rows = 6, 4
    cw, ch = 270, 480
    sheet = Image.new('RGB', (cols * cw, rows * ch), (6, 10, 16))
    for idx, fr in enumerate(sample_frames):
        im = Image.fromarray(frames[fr]).resize((cw, ch), Image.Resampling.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle([6, 6, 162, 28], fill=(0, 0, 0))
        d.text((12, 11), f'MP4 f={fr:04d} ({fr/30:.2f}s)', fill=(255, 218, 130))
        sheet.paste(im, ((idx % cols) * cw, (idx // cols) * ch))
    sheet.save(SHEET_24_PATH, quality=92)
    assert os.path.exists(SHEET_24_PATH)
    print(f'[Forensic] Saved 24-Frame Decoded MP4 Sheet -> {SHEET_24_PATH}')
