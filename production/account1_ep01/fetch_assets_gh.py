#!/usr/bin/env python3
"""Fetch the CC0/MIT GLB assets through the GitHub contents API.

The sandbox can reach api.github.com but not raw.githubusercontent.com, so map
each raw URL onto the API form, which returns identical bytes. Idempotent: a
file already at its expected size is left alone.
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "assets" / "glb"

ASSETS = {
    "venice_mask.glb": ("mrdoob/three.js", "dev",
        "examples/models/gltf/venice_mask.glb", 4_282_264),
    "Soldier.glb": ("mrdoob/three.js", "dev",
        "examples/models/gltf/Soldier.glb", 2_160_468),
    "LeePerrySmith.glb": ("mrdoob/three.js", "dev",
        "examples/models/gltf/LeePerrySmith/LeePerrySmith.glb", 404_976),
    "DiffuseTransmissionPlant.glb": ("KhronosGroup/glTF-Sample-Assets", "main",
        "Models/DiffuseTransmissionPlant/glTF-Binary/DiffuseTransmissionPlant.glb", 5_759_100),
    "GlassHurricaneCandleHolder.glb": ("KhronosGroup/glTF-Sample-Assets", "main",
        "Models/GlassHurricaneCandleHolder/glTF-Binary/GlassHurricaneCandleHolder.glb", 2_705_400),
    "Lantern.glb": ("KhronosGroup/glTF-Sample-Assets", "main",
        "Models/Lantern/glTF-Binary/Lantern.glb", 9_564_264),
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ok = bad = 0
    for name, (repo, ref, path, want) in ASSETS.items():
        dest = OUT / name
        if dest.exists() and dest.stat().st_size == want:
            print(f"  [have] {name}")
            ok += 1
            continue
        url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={ref}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.raw",
            "User-Agent": "MonarchCinema3D/1.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            if len(data) != want:
                print(f"  [warn] {name}: {len(data):,} != {want:,}")
            dest.write_bytes(data)
            print(f"  [ok]   {name} ({len(data):,} B)")
            ok += 1
        except Exception as exc:
            print(f"  [fail] {name}: {exc}")
            bad += 1
    print(f"=== {ok} ready, {bad} failed ===")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
