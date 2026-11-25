#!/usr/bin/env python3
"""
Assemble the narration bed at the script's frame-exact timings.

The script says where a line starts and ends; this puts the line's audio exactly there, on
the sample, so picture and voice cannot drift apart. Placement is on the clip's measured
speech onset, not on sample 0 — a clip that opens with 90 ms of room tone and is placed at
sample 0 is a line that arrives late.

usage: build_vo_bed.py [--out audio/vo-voice01/vo-bed.wav]
"""
import glob
import json
import math
import struct
import subprocess
import sys
import wave

FF = glob.glob("/tmp/py/imageio_ffmpeg/binaries/ffmpeg-*")[0]
SR = 48000
TOTAL = 60
OPEN_PAD = 0.10          # the first word needs an onset, not a trim
HEADROOM_DB = -1.0


def pcm(path):
    b = subprocess.run([FF, "-v", "error", "-i", path, "-f", "f32le", "-ac", "1",
                        "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    n = len(b) // 4
    return list(struct.unpack(f"{n}f", b[:n * 4]))


def main():
    out_path = "audio/vo-voice01/vo-bed.wav"
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]

    d = json.load(open("/tmp/huayuan_v3_script.json"))
    meas = json.load(open("tools/measurements/vo-lines.json"))
    total = TOTAL * SR
    bed = [0.0] * total

    placed = 0
    for r in d["rows"]:
        k = f"n{r['id']:02d}"
        clip = pcm(f"audio/vo-voice01/lines/{k}.wav")
        off = int(round((r["t_in"] - meas[k]["t_in"]) * SR))
        if r["id"] == 1:
            off = int(round(OPEN_PAD * SR))
        if off < 0:
            clip, off = clip[-off:], 0
        end = min(off + len(clip), total)
        for i, v in enumerate(clip[:end - off]):
            bed[off + i] += v
        placed += 1

    peak = max(abs(v) for v in bed)
    g = (10 ** (HEADROOM_DB / 20.0)) / peak if peak else 1.0
    scaled = [v * g for v in bed]

    w = wave.open(out_path, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", max(-32768, min(32767, int(v * 32767))))
                           for v in scaled))
    w.close()
    print(f"{placed} lines -> {out_path} · {TOTAL}s · peak {20*math.log10(peak):.2f} dBFS "
          f"-> {HEADROOM_DB:.1f} dBFS (gain {20*math.log10(g):+.2f} dB)")


if __name__ == "__main__":
    main()
