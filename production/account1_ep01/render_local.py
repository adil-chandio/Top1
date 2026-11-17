#!/usr/bin/env python3
"""Render the whole PEHRA EP01 film locally, in parallel, resumable.

Uses the `bpy` wheel instead of a Blender binary, so no GitHub runner is
involved. Every worker is a separate process rendering a contiguous frame
block; finished frames are skipped on re-run, so an interrupted pass just
continues.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
PY = sys.executable


def build_env(extra_paths: list[str]) -> dict:
    env = dict(os.environ)
    libs = extra_paths + [
        os.environ.get("PEHRA_STUBS", "/tmp/stubs"),
        os.environ.get("PEHRA_BPY_LIB", "/tmp/bpy/bpy/lib"),
        str(BASE / "assets" / "lib"),
    ]
    env["LD_LIBRARY_PATH"] = ":".join(p for p in libs if Path(p).exists())
    env["PYTHONPATH"] = ":".join(
        p for p in [os.environ.get("PEHRA_BPY", "/tmp/bpy"),
                    os.environ.get("PEHRA_DEPS", "/tmp/pydeps")] if Path(p).exists())
    env.setdefault("OMP_NUM_THREADS", "1")
    return env


def frame_path(out: Path, f: int) -> Path:
    return out / f"f_{f:06d}.png"


def plan_shards(shots: list[dict], block: int, only: set[str] | None) -> list[dict]:
    rows = []
    for s in shots:
        if only and s["id"] not in only:
            continue
        lo, hi = int(s["f_start"]), int(s["f_end"])
        while lo <= hi:
            last = min(lo + block - 1, hi)
            rows.append({"id": s["id"], "f_start": lo, "f_end": last})
            lo = last + 1
    return rows


def sampled_frames(lo: int, hi: int, step: float) -> list[int]:
    """Timeline frames to actually render at the requested cadence."""
    if step <= 1.0:
        return list(range(lo, hi + 1))
    out, f = [], lo
    while f <= hi + 1e-9:
        out.append(int(round(f)))
        f += step
    return sorted(set(out))


def missing_in(row: dict, out: Path, step: float = 1.0) -> int:
    return sum(1 for f in sampled_frames(row["f_start"], row["f_end"], step)
               if not frame_path(out, f).exists())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default=str(BASE / "build" / "timeline_full.json"))
    ap.add_argument("--assets", default=str(BASE / "assets"))
    ap.add_argument("--out", default=str(BASE / "frames"))
    ap.add_argument("--block", type=int, default=40)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--samples", type=int, default=8)
    ap.add_argument("--res-pct", type=int, default=100)
    ap.add_argument("--only", default="", help="comma separated shot ids")
    ap.add_argument("--deadline-hours", type=float, default=0.0)
    ap.add_argument("--every", type=float, default=1.0,
                    help="render one frame every N timeline frames (12fps == 2.5)")
    args = ap.parse_args()

    timeline = json.loads(Path(args.timeline).read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    only = {x.strip() for x in args.only.split(",") if x.strip()} or None

    rows = plan_shards(timeline["shots"], args.block, only)
    todo = [r for r in rows if missing_in(r, out, args.every) > 0]
    total_frames = sum(len(sampled_frames(r["f_start"], r["f_end"], args.every))
                       for r in todo)
    done_frames = sum(r["f_end"] - r["f_start"] + 1 for r in rows) - total_frames
    print(f"=== {len(todo)} blocks, {total_frames} frames to render "
          f"({done_frames} already on disk) with {args.workers} workers ===")

    env = build_env([])
    runner = BASE / "run_bpy.py"
    started = time.time()
    deadline = started + args.deadline_hours * 3600 if args.deadline_hours else None
    queue = list(todo)
    running: list[tuple[subprocess.Popen, dict, float]] = []
    completed = 0

    def launch(row: dict) -> None:
        cmd = [PY, str(runner),
               "--shot", row["id"], "--mode", "final",
               "--samples", str(args.samples), "--res-pct", str(args.res_pct),
               "--frames", f"{row['f_start']}-{row['f_end']}",
               "--every", str(args.every),
               "--timeline", args.timeline, "--assets", args.assets,
               "--out", str(out)]
        log = open(BASE / "render_local.log", "a")
        log.write(f"\n=== {row['id']} {row['f_start']}-{row['f_end']} ===\n")
        log.flush()
        proc = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
        running.append((proc, row, time.time()))
        print(f"  [start] {row['id']} {row['f_start']}-{row['f_end']}")

    while queue or running:
        while queue and len(running) < args.workers:
            if deadline and time.time() > deadline:
                print("  [deadline] not launching more work")
                queue.clear()
                break
            launch(queue.pop(0))
        time.sleep(3)
        for item in list(running):
            proc, row, t0 = item
            if proc.poll() is None:
                continue
            running.remove(item)
            completed += 1
            got = sum(1 for f in sampled_frames(row["f_start"], row["f_end"], args.every)
                      if frame_path(out, f).exists())
            want = len(sampled_frames(row["f_start"], row["f_end"], args.every))
            elapsed = time.time() - t0
            rate = elapsed / max(got, 1)
            print(f"  [done] {row['id']} {row['f_start']}-{row['f_end']}: "
                  f"{got}/{want} frames, {elapsed/60:.1f} min, {rate:.0f}s/frame")
            if got < want:
                queue.append(row)          # resume the remainder next round
        if deadline and time.time() > deadline and not running:
            break

    have = len(list(out.glob("f_*.png")))
    total = max(s["f_end"] for s in timeline["shots"])
    print(f"=== frames on disk: {have}/{total} in {(time.time()-started)/60:.1f} min ===")
    return 0 if have == total else 1


if __name__ == "__main__":
    sys.exit(main())
