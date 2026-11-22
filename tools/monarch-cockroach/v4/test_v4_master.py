import json
from pathlib import Path
from PIL import Image
import pytest

ROOT = Path("/home/user/Top1")
DELIV = ROOT / "deliverables" / "monarch-cam-03-v4"
V4_DIR = ROOT / "tools" / "monarch-cockroach" / "v4"
MANIFESTS = ROOT / "tools" / "monarch-cockroach" / "manifests"


def test_v4_voice_lock_integrity() -> None:
    vlock = json.loads((MANIFESTS / "voice-lock-v4.json").read_text())
    assert vlock["voice_id"] == "voice-02"
    assert vlock["time_stretch_applied"] is False
    assert vlock["fps"] == 30
    assert vlock["total_frames"] == 10302
    assert abs(vlock["total_duration_s"] - 343.4) < 1e-3
    assert len(vlock["chapters"]) == 7


def test_v4_deliverables_and_drive_size_cap() -> None:
    mp4 = DELIV / "Monarch-Cam-03-Long-Video-V4.mp4"
    if not mp4.exists():
        pytest.skip("Gitignored deliverables/monarch-cam-03-v4 not built in this checkout")
    thumb = DELIV / "Monarch-Cam-03-Thumbnail-V4.png"
    qa_sheet = DELIV / "Monarch-Cam-03-7-Chapter-QA-Sheet-V4.jpg"
    srt = DELIV / "Monarch-Cam-03-Captions-V4.srt"
    vtt = DELIV / "Monarch-Cam-03-Captions-V4.vtt"

    for p in (mp4, thumb, qa_sheet, srt, vtt):
        assert p.exists(), f"Missing deliverable: {p}"

    # Strict < 100 MB decimal cap for Google Drive connector upload
    mp4_bytes = mp4.stat().st_size
    assert 50_000_000 < mp4_bytes < 100_000_000

    with Image.open(thumb) as im_thumb:
        assert im_thumb.size == (1920, 1080)

    with Image.open(qa_sheet) as im_qa:
        assert im_qa.size == (2560, 2960)

    assert vtt.read_text().startswith("WEBVTT")
    assert "1\n00:00:" in srt.read_text()


def test_v4_rigged_human_glbs_and_modules_present() -> None:
    for glb in ("homeowner.glb", "researcher.glb", "athlete.glb"):
        p = V4_DIR / "assets" / glb
        assert p.exists() and p.stat().st_size > 1_000_000

    for mod in (
        "materials_v4.js",
        "cockroach3d_v4.js",
        "humans3d_v4.js",
        "world_v4.js",
        "director_v4.js",
        "titles_v4.js",
        "page_v4.html",
        "render_v4.mjs",
        "assemble_master_v4.py",
        "build_audio_v4.py",
    ):
        assert (V4_DIR / mod).exists(), f"Missing V4 module: {mod}"
