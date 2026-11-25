#!/usr/bin/env python3
"""
Measure how long each spoken line ACTUALLY takes.

A container duration is not a performance: every clip opens and closes with dead air, and
timing the film off container length is how v1 ended up with silence gaps. This decodes to
48 kHz mono float and finds the first and last 10 ms frame above -45 dBFS, which is the
speech body. Those numbers are what `v3_script.py` places lines with.

usage: measure_vo.py <dir-of-l01..lNN.mp3> [--json out.json]
"""
import glob
import json
import math
import os
import struct
import subprocess
import sys

FFMPEG = glob.glob("/tmp/py/imageio_ffmpeg/binaries/ffmpeg-*")[0]
SR = 48000
HOP = 480            # 10 ms
THRESH_DB = -45.0


def frames(path):
    pcm = subprocess.run(
        [FFMPEG, "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
        capture_output=True, check=True).stdout
    n = len(pcm) // 4
    return struct.unpack(f"{n}f", pcm[:n * 4])


def speech_span(s):
    thr = 10 ** (THRESH_DB / 20.0)
    first = last = None
    for i in range(0, len(s) - HOP, HOP):
        blk = s[i:i + HOP]
        rms = math.sqrt(sum(v * v for v in blk) / len(blk))
        if rms > thr:
            if first is None:
                first = i
            last = i + HOP
    if first is None:
        return 0.0, 0.0
    return first / SR, last / SR


def main():
    d = sys.argv[1]
    out = {}
    for f in sorted(glob.glob(os.path.join(d, "l*.mp3"))):
        name = os.path.splitext(os.path.basename(f))[0]
        s = frames(f)
        a, b = speech_span(s)
        out[name] = dict(container=round(len(s) / SR, 3), t_in=round(a, 3),
                         t_out=round(b, 3), speech=round(b - a, 3))
    print(json.dumps(out, indent=1))
    if "--json" in sys.argv:
        p = sys.argv[sys.argv.index("--json") + 1]
        json.dump(out, open(p, "w"), indent=1)
        print(f"\nwrote {p}")


if __name__ == "__main__":
    main()
