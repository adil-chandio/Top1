"""The approved first movement only. All edits live on the locked V2 clock."""
import csv
import json
import os
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parent
sys.path.append(str(TOOLS.parent / 'monarch-ant-v2'))
from mix import SR, W as V2_WORK, LEVEL, native_vo  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(os.environ.get('MONARCH_V3_CACHE', '.cache/monarch-ant-v3'))
WORK = ROOT / 'work'
QA = ROOT / 'qa'
DELIVERY = Path(os.environ.get('MONARCH_V3_DELIVERY', 'deliverables/monarch-cam-step-4-v3'))
TITLE = 'Monarch-Cam-Ant-V3-Opening-Pilot'
PLAN = TOOLS / 'opening.plan'
FPS = 30
FRAMES = 708
ENDS = (0, 194, 333, 484, 708)
SPF = SR // FPS
SAMPLES = FRAMES * SPF
CONTACT = 441
LANDING = 519


def make_dirs():
    for p in (WORK, QA):
        p.mkdir(parents=True, exist_ok=True)


def dims():
    w, h = map(int, (WORK / 'native-size.txt').read_text().split())
    assert w * 9 == h * 16
    return w, h


def plate_range(i, w, h):
    lo, hi = ENDS[i:i + 2]
    p = WORK / f'native-{i}.rgba'
    assert p.stat().st_size == (hi - lo) * w * h * 4, p
    return p, lo, hi


def picture_trace():
    rows = []
    for i in range(len(ENDS) - 1):
        with (QA / f'native-{i}.csv').open() as src:
            rows.extend(csv.DictReader(src))
    assert [int(x['frame']) for x in rows] == list(range(FRAMES))
    return rows


def voice_plate():
    m = json.loads((V2_WORK / 'film-v2.json').read_text())
    assert m['fps'] == FPS and m['chapters'][1][0] == FRAMES
    words = native_vo()
    v = np.zeros(SAMPLES, dtype=np.float32)
    placements = []
    for lo, hi, dst in m['vo_ranges']:
        size = min(hi - lo, SAMPLES - dst)
        if size <= 0:
            continue
        assert lo >= 0 and dst >= 0
        v[dst:dst+size] = words[lo:lo+size] * LEVEL
        placements.append(dict(from_sample=lo, to_sample=lo+size, dest_sample=dst))
    return v, placements
