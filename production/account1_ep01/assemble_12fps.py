#!/usr/bin/env python3
"""Assemble a film from a sub-sampled frame set.

The 12 fps pass writes only every 2.5th timeline frame. This script walks the
timeline in order, holds each rendered frame for the frames it covers, and
feeds ffmpeg a contiguous 30 fps image sequence — so the picture holds for two
or three frames instead of tweening. On motion-blurred volumetric shots a hold
reads as a deliberate cadence, not as a stutter, which is why it is preferable
to synthesising in-between frames that never existed.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default=str(BASE / "build" / "timeline_full.json"))
    ap.add_argument("--frames-dir", default=str(BASE / "frames12"))
    ap.add_argument("--out", default=str(BASE / "frames30"))
    args = ap.parse_args()

    tl = json.loads(Path(args.timeline).read_text())
    src = Path(args.frames_dir)
    dst = Path(args.out)
    dst.mkdir(parents=True, exist_ok=True)

    rendered = sorted(int(p.stem.split("_")[1]) for p in src.glob("f_*.png"))
    if not rendered:
        print("no rendered frames", file=sys.stderr)
        return 1
    have = set(rendered)
    total = max(s["f_end"] for s in tl["shots"])

    missing_rendered = 0
    written = 0
    prev = None
    for f in range(1, total + 1):
        if f in have:
            prev = f
        if prev is None:
            missing_rendered += 1
            continue
        link = dst / f"f_{f:06d}.png"
        if not link.exists():
            shutil.copyfile(src / f"f_{prev:06d}.png", link)
            written += 1

    print(f"rendered {len(rendered)} unique frames, expanded to {written + len(have)} "
          f"timeline frames, {missing_rendered} before the first rendered frame")
    if missing_rendered:
        print("WARNING: leading frames have no source image", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
