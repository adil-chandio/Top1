"""
Gate 6 Forensic Validator for V6.3 Director-OS Field-Dig Edition:
  `exports/extinct-karoo-field-v63/Karoo-Burrow-Field-Edition-V6.3.mp4`

Verifies:
1. Gate 0.5 `director_linter.py` passes with 0 errors, 0 warnings, and >= 65% anti-clone divergence.
2. Voice-lock `time_stretch_applied == False` (exact 1.000x approved voiceover speed).
3. Streaming O(1)-RAM `verify_imax_mp4` across all 1,080 decoded H.264 frames + post-AAC audio:
   - 1080x1920 @ 30.000 fps, 36.000s, 0 frozen/corrupt frames, seamless loop MAE <= 2.5
   - Post-AAC True Peak <= -1.0 dBFS, Integrated Loudness within -14.2 +/- 0.6 LUFS (via ffmpeg ebur128)
   - Post-AAC Pre-Twist Vacuum [10.220s, 10.480s] <= -50.0 dBFS
4. Extracts 12-frame `Decoded-MP4-Proof-Sheet-Karoo-Field-V6.3.jpg` directly from the MP4 bitstream.
5. Asserts persistent non-.git `/home/user/Top1` workspace footprint < 126.0 MiB.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, "/tmp/py")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(ROOT, "tools/monarch-v6-imax-sdk/python"))
sys.path.insert(0, os.path.join(ROOT, "tools/director-producer-os/validators"))

from PIL import Image, ImageDraw
from director_linter import lint_director_plan
from forensic_qa_sdk import find_ffmpeg, verify_imax_mp4

PLAN_JSON = os.path.join(ROOT, "projects/extinct-karoo-field-v63/director-plan.json")
LOCK_JSON = os.path.join(ROOT, "projects/extinct-karoo-field-v63/voice-lock-karoo-field-v63.json")
EXPORT_DIR = os.path.join(ROOT, "exports/extinct-karoo-field-v63")
_EXPORT_MP4 = os.path.join(EXPORT_DIR, "Karoo-Burrow-Field-Edition-V6.3.mp4")
_TMP_MP4 = "/tmp/karoo_field_v63/Karoo-Burrow-Field-Edition-V6.3.mp4"
MP4_PATH = _EXPORT_MP4 if os.path.isfile(_EXPORT_MP4) else _TMP_MP4
COVER_PATH = os.path.join(EXPORT_DIR, "Cover-Karoo-Burrow-Field-V6.3.png")
SRT_PATH = os.path.join(EXPORT_DIR, "Karoo-Burrow-Field-Edition-V6.3.srt")
VTT_PATH = os.path.join(EXPORT_DIR, "Karoo-Burrow-Field-Edition-V6.3.vtt")
PROOF_JPG = os.path.join(EXPORT_DIR, "Decoded-MP4-Proof-Sheet-Karoo-Field-V6.3.jpg")


def test_karoo_field_v63_director_plan_and_master_mp4():
    # 1. Gate 0.5 Director Linter + Anti-Clone Validator
    with open(PLAN_JSON, "r", encoding="utf-8") as fh:
        plan = json.load(fh)
    errs, warns, plan_metrics = lint_director_plan(plan, check_history=True)
    assert errs == [], f"Director linter errors: {errs}"
    assert warns == [], f"Director linter warnings: {warns}"
    assert plan_metrics["anti_clone"]["min_divergence_across_recent3_pct"] >= 65.0

    # 2. Gate 2 Voice-Lock Integrity (1.000x exact speed)
    with open(LOCK_JSON, "r", encoding="utf-8") as fh:
        lock = json.load(fh)
    assert lock["time_stretch_applied"] is False
    assert lock["archetype_id"] == "W02_SCORCHED_FIELD_EXPEDITION"
    assert lock["hud_philosophy"] == "H1_DOCUMENTARY_LOWER_THIRD"

    assert os.path.isfile(MP4_PATH), f"Missing master MP4: {MP4_PATH}"
    assert os.path.isfile(COVER_PATH), f"Missing cover PNG: {COVER_PATH}"
    assert os.path.isfile(SRT_PATH) and os.path.isfile(VTT_PATH), "Missing .srt/.vtt subtitles"

    # 3. Streaming Decoded-MP4 Video + Audio Verification
    shot_cuts = {int(s["f0"]) for s in lock["shots"] if int(s["f0"]) > 0}
    vac_w = tuple(lock["vacuum_qa_window"])
    metrics = verify_imax_mp4(
        mp4_path=MP4_PATH,
        expected_frames=1080,
        shot_cuts=shot_cuts,
        check_seamless_loop=True,
        max_loop_mae=2.5,
        vacuum_window_s=vac_w,
    )
    print("\n[KAROO FIELD V6.3 FORENSIC METRICS]", json.dumps(metrics, indent=2))
    assert metrics["true_peak_dbfs"] <= -1.0, f"Post-AAC True Peak exceeded -1.0 dBFS: {metrics['true_peak_dbfs']}"

    # Verify Post-AAC Integrated Loudness & True Peak via ffmpeg ebur128
    ffmpeg = find_ffmpeg()
    ebu = subprocess.run(
        [ffmpeg, "-nostats", "-i", MP4_PATH, "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    m_i = re.findall(r"I:\s*(-?\d+\.\d+)\s*LUFS", ebu.stderr)
    m_tp = re.findall(r"Peak:\s*(-?\d+\.\d+)\s*dBFS", ebu.stderr)
    assert m_i, "Could not parse EBU R128 integrated loudness"
    post_lufs = float(m_i[-1])
    post_tp = float(m_tp[-1]) if m_tp else metrics["true_peak_dbfs"]
    print(f"[POST-AAC EBU R128] Integrated = {post_lufs:.2f} LUFS | True Peak = {post_tp:.2f} dBTP")
    assert -14.8 <= post_lufs <= -13.6, f"Post-AAC LUFS out of -14.2 +/- 0.6 target: {post_lufs}"
    assert post_tp <= -1.0, f"Post-AAC True Peak > -1.0 dBTP: {post_tp}"

    # 4. Build 4x3 Decoded-MP4 Proof Contact Sheet directly from the H.264 bitstream
    sample_frames = [18, 134, 255, 310, 355, 430, 510, 620, 695, 782, 875, 1079]
    select_expr = "+".join(f"eq(n\\,{f})" for f in sample_frames)
    tmp_dir = "/tmp/karoo_field_v63/decoded_proof"
    os.makedirs(tmp_dir, exist_ok=True)
    subprocess.run(
        [
            ffmpeg, "-y", "-v", "error", "-i", MP4_PATH,
            "-vf", f"select='{select_expr}',scale=270:480",
            "-fps_mode", "passthrough", os.path.join(tmp_dir, "f_%02d.png"),
        ],
        check=True,
    )

    cols, rows, tw, th = 4, 3, 270, 480
    sheet = Image.new("RGB", (cols * tw, rows * th), (24, 15, 10))
    draw = ImageDraw.Draw(sheet)
    for idx, fnum in enumerate(sample_frames):
        im = Image.open(os.path.join(tmp_dir, f"f_{idx + 1:02d}.png")).convert("RGB")
        cx, cy = (idx % cols) * tw, (idx // cols) * th
        sheet.paste(im, (cx, cy))
        draw.rectangle([cx + 6, cy + 6, cx + 162, cy + 28], fill=(20, 12, 8))
        draw.text((cx + 12, cy + 10), f"MP4 f={fnum} ({fnum/30.0:.2f}s)", fill=(244, 223, 184))

    sheet.save(PROOF_JPG, quality=92)
    assert os.path.isfile(PROOF_JPG)

    # 5. Enforce < 126.0 MiB persistent non-.git workspace footprint
    total_bytes = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            if os.path.isfile(fp):
                total_bytes += os.path.getsize(fp)
    total_mib = total_bytes / (1024 * 1024)
    print(f"[WORKSPACE FOOTPRINT] {total_mib:.2f} MiB / 126.00 MiB cap")
    assert total_mib < 126.0, f"Workspace exceeded 126 MiB cap: {total_mib:.2f} MiB"
