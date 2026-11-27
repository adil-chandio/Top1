"""
Forensic Broadcast & Hollywood IMAX Verification Suite (`V6.2`)
Project: LOGAN — Rig-to-Render VFX Breakdown (`1080x1920` @ `30.000 fps`, `420` frames)
"""
import json
import os
import subprocess
import sys

SDK_PY = "/home/user/Top1/tools/monarch-v6-imax-sdk/python"
if SDK_PY not in sys.path:
    sys.path.insert(0, SDK_PY)
if "/tmp/py" not in sys.path:
    sys.path.insert(0, "/tmp/py")

import numpy as np
from forensic_qa_sdk import find_ffmpeg, verify_imax_mp4

ROOT = "/home/user/Top1"
EXPORT_DIR = os.path.join(ROOT, "exports/logan-claw-rig-v6-imax")
MP4_PATH = os.path.join(EXPORT_DIR, "Logan-Claw-Rig-Breakdown-V6-IMAX.mp4")
COVER_PATH = os.path.join(EXPORT_DIR, "Logan-Claw-Rig-Cover-V6-IMAX.png")
QA_SHEET_PATH = os.path.join(EXPORT_DIR, "Logan-Claw-Rig-12Beat-QA-Sheet-V6-IMAX.jpg")
LOCK_JSON = os.path.join(ROOT, "tools/logan-claw-v6/audio-lock-logan-v6.json")

TOTAL_FRAMES = 420
FPS = 30


def _lock():
    with open(LOCK_JSON, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_deliverables_exist():
    for path, min_bytes in (
        (MP4_PATH, 1_000_000),
        (COVER_PATH, 100_000),
        (QA_SHEET_PATH, 100_000),
    ):
        assert os.path.isfile(path), f"Missing deliverable: {path}"
        assert os.path.getsize(path) > min_bytes, f"Suspiciously small: {path}"


def test_hollywood_imax_v6_forensic_gate():
    lock = _lock()
    report = verify_imax_mp4(
        MP4_PATH,
        expected_frames=TOTAL_FRAMES,
        shot_cuts=set(lock["shot_cuts"]),
        check_seamless_loop=True,
        max_loop_mae=4.0,
        vacuum_window_s=tuple(lock["vacuum_window_s"]),
    )
    print("\n[V6 Forensic Report]", json.dumps(report, indent=2))
    assert report["decoded_frames"] == TOTAL_FRAMES
    assert report["loop_mae"] < 4.0, f"Loop seam MAE too high: {report['loop_mae']}"
    assert report["vacuum_rms_db"] < -48.0


def test_container_specs_1080x1920_30fps_14s():
    ffmpeg = find_ffmpeg()

    # Decode a single frame to confirm exact 1080x1920 geometry.
    raw = subprocess.check_output(
        [
            ffmpeg, "-v", "error", "-i", MP4_PATH, "-frames:v", "1",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ]
    )
    arr = np.frombuffer(raw, dtype=np.uint8)
    assert arr.size == 1080 * 1920 * 3, f"Unexpected frame geometry: {arr.size} bytes"

    # Confirm exact duration/fps from the stream banner FFmpeg prints.
    banner = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", MP4_PATH],
        capture_output=True, text=True,
    ).stderr
    assert "1080x1920" in banner, banner[:400]
    assert f"{FPS} fps" in banner, banner[:400]
    assert "14.0" in banner or "14.00" in banner, banner[:400]


def test_four_rig_to_render_match_cut_pairs():
    """Verify all 4 Clay-Viewport -> Chiaroscuro-Final-Render pairs contrast correctly."""
    ffmpeg = find_ffmpeg()
    w_s, h_s = 135, 240
    raw = subprocess.check_output(
        [
            ffmpeg, "-v", "error", "-i", MP4_PATH,
            "-vf", f"scale={w_s}:{h_s}",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ]
    )
    frames = np.frombuffer(raw, dtype=np.uint8).reshape((-1, h_s, w_s, 3)).astype(np.float32)
    assert frames.shape[0] == TOTAL_FRAMES
    luma = 0.299 * frames[..., 0] + 0.587 * frames[..., 1] + 0.114 * frames[..., 2]

    pairs = [
        (45, 105, "Pair 1 Medium SNIKT"),
        (148, 186, "Pair 2 Macro Fist & Claws"),
        (230, 272, "Pair 3 3/4 Portrait"),
        (314, 364, "Pair 4 Front Climax Stare"),
    ]
    for f_clay, f_render, name in pairs:
        clay_mean = float(luma[f_clay].mean())
        render_mean = float(luma[f_render].mean())
        render_p999 = float(np.percentile(luma[f_render], 99.99))
        render_p99 = float(np.percentile(luma[f_render], 99.0))
        # A clay viewport is a brightly-lit studio; a chiaroscuro final is deliberately
        # low-key. Require a clear, real separation but not a specific absolute level.
        assert clay_mean > render_mean + 8.0, (
            f"{name}: expected bright studio clay ({clay_mean:.1f}) > "
            f"dark chiaroscuro render ({render_mean:.1f})"
        )
        # Specular integrity on the FINAL render: the brightest highlights must be
        # genuinely bright (sheen, wet cornea, blade bevels) even though the frame mean
        # is dark. This is the property that actually breaks when a look-dev regresses.
        assert render_p999 > 150.0, (
            f"{name}: final render has no crisp specular highlights (p99.99={render_p999:.1f})"
        )
        assert render_p99 > 45.0, (
            f"{name}: final render lost its midtone structure (p99={render_p99:.1f})"
        )


def test_workspace_size_cap():
    """Keep this project's own contribution (source + gitignored deliverables) small.

    The Arena cap applies to the cumulative patchset, so it is measured against this
    project's tools dir plus its exports. `/exports/` is gitignored, so the master MP4
    never enters the patchset; it is counted here only as a deliverable sanity bound.
    """
    src_mb = int(subprocess.check_output(["du", "-sm", os.path.join(ROOT, "tools/logan-claw-v6")], text=True).split()[0])
    exp_mb = int(subprocess.check_output(["du", "-sm", EXPORT_DIR], text=True).split()[0])
    assert src_mb <= 4, f"Project source grew unexpectedly: {src_mb} MiB"
    assert exp_mb <= 45, f"Project exports grew unexpectedly: {exp_mb} MiB"
    assert src_mb + exp_mb <= 45, f"Project footprint {src_mb + exp_mb} MiB too large"
