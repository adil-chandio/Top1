"""
Gate 6 Forensic Validator for 250-Ma Karoo Burrow Fossil (`Karoo-Burrow-V6-Ultra-IMAX.mp4`).
Runs streaming O(1)-RAM `verify_imax_mp4` across all 1,080 decoded H.264 frames + muxed AAC-LC audio,
verifies workspace `< 126 MiB`, and builds `Decoded-MP4-Proof-Sheet-Karoo-V6.jpg` directly from the MP4!
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, "/tmp/py")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../tools/monarch-v6-imax-sdk/python")))

from PIL import Image, ImageDraw
from forensic_qa_sdk import find_ffmpeg, verify_imax_mp4

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
LOCK_JSON = os.path.join(ROOT, "projects/extinct-karoo-burrow/voice-lock-karoo-v6.json")
EXPORT_DIR = os.path.join(ROOT, "exports/extinct-karoo-burrow")
_EXPORT_MP4 = os.path.join(EXPORT_DIR, "Karoo-Burrow-V6-Ultra-IMAX.mp4")
_TMP_MP4 = "/tmp/karoo_v6/Karoo-Burrow-V6-Ultra-IMAX.mp4"
MP4_PATH = _EXPORT_MP4 if os.path.isfile(_EXPORT_MP4) else _TMP_MP4
COVER_PATH = os.path.join(EXPORT_DIR, "Cover-Karoo-Burrow-V6-Ultra.png")
SRT_PATH = os.path.join(EXPORT_DIR, "Karoo-Burrow-V6-Ultra-Captions.srt")
VTT_PATH = os.path.join(EXPORT_DIR, "Karoo-Burrow-V6-Ultra-Captions.vtt")
PROOF_JPG = os.path.join(EXPORT_DIR, "Decoded-MP4-Proof-Sheet-Karoo-V6.jpg")


def test_karoo_v6_imax_master_and_proof_sheet():
    with open(LOCK_JSON, "r", encoding="utf-8") as fh:
        lock = json.load(fh)

    assert os.path.isfile(MP4_PATH), f"Missing master MP4: {MP4_PATH}"
    assert os.path.isfile(COVER_PATH), f"Missing cover PNG: {COVER_PATH}"
    assert os.path.isfile(SRT_PATH) and os.path.isfile(VTT_PATH), "Missing companion caption files"

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
    print("\n[KAROO V6 FORENSIC METRICS]", json.dumps(metrics, indent=2))
    assert metrics["true_peak_dbfs"] <= -1.0, f"Post-AAC True Peak exceeded -1.0 dBFS: {metrics['true_peak_dbfs']}"

    # Build 4x3 Decoded-MP4 Proof Contact Sheet directly from the H.264 bitstream!
    ffmpeg = find_ffmpeg()
    sample_frames = [18, 122, 255, 310, 355, 425, 570, 695, 788, 875, 912, 1079]
    select_expr = "+".join(f"eq(n\\,{f})" for f in sample_frames)
    tmp_dir = "/tmp/karoo_v6/decoded_proof"
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
    sheet = Image.new("RGB", (cols * tw, rows * th), (8, 12, 18))
    draw = ImageDraw.Draw(sheet)
    for idx, fnum in enumerate(sample_frames):
        im = Image.open(os.path.join(tmp_dir, f"f_{idx + 1:02d}.png")).convert("RGB")
        cx, cy = (idx % cols) * tw, (idx // cols) * th
        sheet.paste(im, (cx, cy))
        draw.rectangle([cx + 6, cy + 6, cx + 150, cy + 28], fill=(0, 0, 0))
        draw.text((cx + 12, cy + 10), f"MP4 f={fnum} ({fnum/30.0:.2f}s)", fill=(92, 240, 225))

    sheet.save(PROOF_JPG, quality=92)
    assert os.path.isfile(PROOF_JPG)

    # Verify total `/home/user/Top1` non-git workspace footprint < 126 MiB!
    total_bytes = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            if os.path.isfile(fp):
                total_bytes += os.path.getsize(fp)
    total_mib = total_bytes / (1024 * 1024)
    print(f"[WORKSPACE FOOTPRINT] {total_mib:.2f} MiB / 126.00 MiB cap")
    assert total_mib < 126.0, f"Workspace exceeded 126 MiB patchset cap: {total_mib:.2f} MiB"
