import json
import os
import re
import subprocess
import sys

sys.path.insert(0, "/tmp/py")
import numpy as np
import pytest

ROOT = "/home/user/Top1"
FFMPEG = "/tmp/py/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2"
EXPORT_DIR = os.path.join(ROOT, "exports/monarch-cam-03-short-v6-imax")
MP4_PATH = os.path.join(EXPORT_DIR, "Monarch-Cam-03-Viral-Short-V6-IMAX.mp4")
COVER_PNG = os.path.join(EXPORT_DIR, "Monarch-Cam-03-Short-Cover-V6-IMAX.png")
QA_JPG = os.path.join(EXPORT_DIR, "Monarch-Cam-03-Short-12Beat-QA-Sheet-V6-IMAX.jpg")
SRT_PATH = os.path.join(EXPORT_DIR, "Monarch-Cam-03-Short-Captions-V6-IMAX.srt")
VTT_PATH = os.path.join(EXPORT_DIR, "Monarch-Cam-03-Short-Captions-V6-IMAX.vtt")
LOCK_JSON = os.path.join(ROOT, "tools/monarch-cockroach/short_v6/short-voice-lock-v6-imax.json")

SHOT_CUTS = {0, 76, 161, 316, 425, 490, 611, 634, 682, 726, 912, 936, 995, 1031}


def _require_local_v6_exports():
    if not os.path.isfile(MP4_PATH):
        pytest.skip("Gitignored local exports/monarch-cam-03-short-v6-imax not present in fresh checkout")


def test_deliverables_exist_and_workspace_budget():
    assert os.path.isfile(LOCK_JSON)
    _require_local_v6_exports()
    for p in [MP4_PATH, COVER_PNG, QA_JPG, SRT_PATH, VTT_PATH, LOCK_JSON]:
        assert os.path.isfile(p), f"Missing deliverable: {p}"
        assert os.path.getsize(p) > 500, f"Empty deliverable: {p}"

    # Verify persistent untracked workspace footprint < 128.00 MiB
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True
    ).splitlines()
    total_bytes = sum(os.path.getsize(os.path.join(ROOT, f)) for f in untracked if os.path.isfile(os.path.join(ROOT, f)))
    total_mib = total_bytes / (1024 * 1024)
    print(f"[QA] Total untracked workspace size: {total_mib:.2f} MiB / 128.00 MiB")
    assert total_mib < 126.0, f"Workspace snapshot budget exceeded: {total_mib:.2f} MiB"


def test_voice_lock_and_captions_integrity():
    with open(LOCK_JSON, "r", encoding="utf-8") as f:
        lock = json.load(f)
    assert lock["total_frames"] == 1050
    assert lock["fps"] == 30
    assert abs(lock["duration_s"] - 35.0) < 1e-6
    assert lock["time_stretch_applied"] is False
    assert len(lock["cues"]) == 19

    if os.path.isfile(SRT_PATH) and os.path.isfile(VTT_PATH):
        srt_txt = open(SRT_PATH, encoding="utf-8").read()
        vtt_txt = open(VTT_PATH, encoding="utf-8").read()
        assert "under 2 pennies" in srt_txt
        assert "900" in srt_txt
        assert vtt_txt.startswith("WEBVTT")


def test_decoded_video_frames_flicker_and_seamless_loop():
    _require_local_v6_exports()
    # Decode all 1,050 frames at quarter-res (270x480 RGB24) directly from the final MP4 to verify:
    #   1. Exact 1,050 decoded frames (35.000s @ 30.000 fps) and 0 decode errors
    #   2. Zero black/dropped frames
    #   3. Zero A->B->A single-frame flicker spikes inside shots
    #   4. Seamless loop RGB MAE between frame 1049 and frame 0
    w, h = 270, 480
    cmd = [
        FFMPEG, "-v", "error",
        "-i", MP4_PATH,
        "-vf", f"scale={w}:{h}",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
    ]
    proc = subprocess.run(cmd, capture_output=True, check=True)
    assert proc.stderr == b"", f"FFmpeg decode errors: {proc.stderr.decode()}"

    frame_bytes = w * h * 3
    assert len(proc.stdout) % frame_bytes == 0
    n_frames = len(proc.stdout) // frame_bytes
    assert n_frames == 1050, f"Expected 1050 decoded frames, got {n_frames}"

    frames = np.frombuffer(proc.stdout, dtype=np.uint8).reshape((n_frames, h, w, 3)).astype(np.float32)

    # Check non-black luma on every single frame
    means = frames.mean(axis=(1, 2, 3))
    assert float(means.min()) > 8.0, f"Dark/black frame detected! min mean={means.min():.2f}"

    # Check seamless loop continuity between final frame 1049 and first frame 0 (excluding HUD top/caption zones)
    roi_1049 = frames[1049, int(h * 0.14):int(h * 0.62), :, :]
    roi_0000 = frames[0, int(h * 0.14):int(h * 0.62), :, :]
    loop_mae = float(np.abs(roi_1049 - roi_0000).mean())
    print(f"[QA] Decoded MP4 Loop-Seam ROI MAE (f=1049 -> f=0): {loop_mae:.3f} / 255")
    assert loop_mae < 9.5, f"Loop seam discontinuity too high: {loop_mae:.3f}"

    # Check zero A->B->A single-frame flicker spikes away from intentional cut/impact frames!
    aba_spikes = []
    for i in range(1, n_frames - 1):
        if any(abs(i - c) <= 2 for c in SHOT_CUTS):
            continue
        d_prev = float(np.abs(frames[i] - frames[i - 1]).mean())
        d_next = float(np.abs(frames[i + 1] - frames[i]).mean())
        d_bridge = float(np.abs(frames[i + 1] - frames[i - 1]).mean())
        # True single-frame A->B->A glitch jumps wildly from both neighbors while i-1 and i+1 remain close!
        if d_prev > 14.0 and d_next > 14.0 and d_bridge < 4.5:
            aba_spikes.append((i, d_prev, d_next, d_bridge))
    assert len(aba_spikes) == 0, f"Detected A->B->A flicker spikes: {aba_spikes}"


def test_muxed_audio_loudness_and_wait_silence_drop():
    _require_local_v6_exports()
    # Measure EBU R128 loudness directly on the muxed AAC stream inside the final MP4!
    res = subprocess.run(
        [FFMPEG, "-nostats", "-i", MP4_PATH, "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, check=True
    )
    m_i = re.findall(r"I:\s*(-?\d+\.\d+)\s*LUFS", res.stderr)
    m_tp = re.findall(r"Peak:\s*(-?\d+\.\d+)\s*dBFS", res.stderr)
    assert m_i and m_tp, "Failed to parse EBU R128 summary from MP4"
    lufs = float(m_i[-1])
    tp = float(m_tp[-1])
    print(f"[QA] Muxed MP4 Audio: I={lufs:.2f} LUFS, TruePeak={tp:.2f} dBFS")
    assert -15.4 <= lufs <= -13.4, f"Integrated loudness out of target (-14 +- 1 LUFS): {lufs}"
    assert tp <= -0.9, f"True peak too hot: {tp} dBFS"

    # Decode stereo float32 PCM from MP4 and verify the 190ms trailer vacuum silence right before "Wait." (10.39..10.52s)
    pcm = subprocess.run(
        [FFMPEG, "-v", "error", "-i", MP4_PATH, "-vn", "-f", "f32le", "-ac", "2", "-ar", "48000", "-"],
        capture_output=True, check=True
    ).stdout
    audio = np.frombuffer(pcm, dtype=np.float32).reshape((-1, 2))
    dur_s = len(audio) / 48000.0
    assert abs(dur_s - 35.0) < 0.06, f"Unexpected audio duration: {dur_s:.3f}s"

    s0, s1 = int(10.40 * 48000), int(10.52 * 48000)
    vac_rms_db = 20.0 * np.log10(np.sqrt(np.mean(audio[s0:s1] ** 2)) + 1e-9)
    print(f"[QA] Pre-'Wait.' Trailer Vacuum RMS (10.40-10.52s): {vac_rms_db:.1f} dBFS")
    assert vac_rms_db < -48.0, f"Trailer silence drop before 'Wait.' not clean enough: {vac_rms_db:.1f} dBFS"
