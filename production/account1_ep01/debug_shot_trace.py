"""Build one shot's scene and report any traceback. No rendering.

    blender -b --factory-startup --python debug_shot_trace.py -- --shot S4_UNGUARDED_GATE
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpy  # noqa: E402


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", required=True)
    ap.add_argument("--timeline", default=str(HERE / "build" / "timeline_15s.json"))
    ap.add_argument("--assets", default=str(HERE / "assets"))
    args = ap.parse_args(argv)

    import render_scene as rs

    rs.ASSETS = Path(args.assets).resolve()
    rs.load_manifest()
    timeline = json.loads(Path(args.timeline).read_text())
    shot = next(s for s in timeline["shots"] if s["id"] == args.shot)
    s, e = int(shot["f_start"]), int(shot["f_end"])

    bpy.ops.wm.read_factory_settings(use_empty=True)
    rs.SCENE = bpy.context.scene
    rs.SCENE.render.engine = "CYCLES"
    rs.SCENE.render.resolution_x, rs.SCENE.render.resolution_y = rs.WIDTH, rs.HEIGHT

    mats = rs.build_material_library()
    try:
        rs.SHOT_BUILDERS[args.shot](mats, s, e)
        print(f"[TRACE] {args.shot}: scene built OK")
        return 0
    except Exception:
        print(f"[TRACE] {args.shot}: FAILED\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
