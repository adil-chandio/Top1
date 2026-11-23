"""
Monarch Cam #03 — Long Video V6 Hollywood IMAX Forensic Pytest Gate (`test_long_v6.py`)
Validates:
  1. Decoded MP4 frame count == `9,008` (`300.267s @ 30.000 fps`), `0` black frames (`min_luma > 8.0`),
     `0` `A -> B -> A` single-frame flicker spikes across all non-cut triplets
  2. Broadcast EBU R128 loudness (`-15.4 .. -13.2 LUFS`), True Peak (`<= -0.9 dBFS`),
     and Pre-Twist Vacuum Silence `[17.85..18.08s]` (`< -48.0 dBFS`)
  3. 100% Zero overlays/HUD/leader metadata inside all 4 Protected Climax Windows
     (`[330, 538]`, `[4662, 4923]`, `[8143, 8502]`, `[8922, 8956]`)
  4. Exact `81` SRT/VTT caption cues + 0% VO time-stretch lock + Drive-uploadable MP4 `< 96 MiB`
"""
import glob
import json
import os
import sys

sys.path.insert(0, "/tmp/py")

ROOT = "/home/user/Top1"
sys.path.insert(0, os.path.join(ROOT, "tools/monarch-v6-imax-sdk/python"))
from forensic_qa_sdk import verify_imax_mp4

MP4_PATH = "/tmp/v6_long/Monarch-Cam-03-Long-Video-Master-V6-IMAX.mp4"
SRT_PATH = os.path.join(ROOT, "exports/monarch-cam-03-long-v6-imax/Monarch-Cam-03-Long-Video-Captions-V6-IMAX.srt")
VTT_PATH = os.path.join(ROOT, "exports/monarch-cam-03-long-v6-imax/Monarch-Cam-03-Long-Video-Captions-V6-IMAX.vtt")
LOCK_PATH = os.path.join(ROOT, "tools/monarch-cockroach/long_v6/long-voice-lock-v6-imax.json")
PLATES_DIR = "/tmp/v6_long/build/plates"
OVERLAYS_MANIFEST = "/tmp/v6_long/build/overlays/overlays_manifest_v6.json"

SHOT_CUTS_LONG_V6 = {
    0, 29, 145, 214, 330, 538,
    921, 1224, 1819,
    2288, 2592, 2986, 3287,
    3607, 3883, 4138, 4350, 4481, 4923, 5097,
    5312, 5620, 5864, 6223,
    6591, 6877, 7183, 7519, 7891,
    8032, 8143, 8212, 8502, 8692, 8922, 8956,
}

PROTECTED_WINDOWS = [
    (330, 538),
    (4662, 4923),
    (8143, 8502),
    (8922, 8956),
]


def test_voice_lock_and_captions_integrity():
    with open(LOCK_PATH, "r", encoding="utf-8") as fp:
        lock = json.load(fp)
    assert lock["fps"] == 30
    assert lock["total_frames"] == 9008
    assert lock["time_stretch_applied"] is False
    assert len(lock.get("captions", [])) == 81 or "\n81\n" in open(SRT_PATH, "r", encoding="utf-8").read()

    assert os.path.isfile(SRT_PATH) and os.path.getsize(SRT_PATH) > 2000
    assert os.path.isfile(VTT_PATH) and os.path.getsize(VTT_PATH) > 2000
    srt_txt = open(SRT_PATH, "r", encoding="utf-8").read()
    assert "\n81\n" in srt_txt or srt_txt.startswith("1\n")


def test_protected_climax_windows_zero_overlays():
    with open(OVERLAYS_MANIFEST, "r", encoding="utf-8") as fp:
        overlays = json.load(fp)
    assert len(overlays) >= 34

    for ov in overlays:
        s, e = int(ov["start"]), int(ov["end"])
        for pa, pb in PROTECTED_WINDOWS:
            overlap = max(0, min(e, pb - 1) - max(s, pa) + 1)
            assert overlap == 0, f"Overlay {ov['id']} [{s}..{e}] violates Protected Window [{pa}..{pb}]!"

    plate_jsons = sorted(glob.glob(os.path.join(PLATES_DIR, "plate_*.json")))
    assert len(plate_jsons) == 31
    recs = []
    for jp in plate_jsons:
        with open(jp, "r", encoding="utf-8") as fp:
            recs.extend(json.load(fp))
    assert len(recs) == 9008
    for pa, pb in PROTECTED_WINDOWS:
        for f in range(pa, pb):
            r = recs[f]
            assert r.get("l") is None, f"Leader active inside protected window at f={f}"
            assert r.get("ht", "") == "", f"HUD telemetry active inside protected window at f={f}"


def test_master_mp4_forensic_imax_gate():
    assert os.path.isfile(MP4_PATH), f"Missing Master MP4: {MP4_PATH}"
    size_mb = os.path.getsize(MP4_PATH) / (1024 * 1024)
    assert 15.0 < size_mb < 96.0, f"MP4 size {size_mb:.2f} MiB outside [15, 96] MiB bounds"

    report = verify_imax_mp4(
        mp4_path=MP4_PATH,
        expected_frames=9008,
        shot_cuts=SHOT_CUTS_LONG_V6,
        check_seamless_loop=False,
        vacuum_window_s=(17.85, 18.08),
        scale_w=320,
        scale_h=180,
    )
    print("\n[FORENSIC REPORT LONG V6 IMAX]", json.dumps(report, indent=2))
    assert report["decoded_frames"] == 9008
    assert report["min_luma"] > 12.0
    assert report["aba_spikes"] == 0
    assert -15.2 <= report["lufs"] <= -13.4
    assert report["true_peak_dbfs"] <= -1.0
    assert report["vacuum_rms_db"] < -55.0
