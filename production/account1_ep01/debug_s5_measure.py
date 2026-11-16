"""Print real world-space bounds for the S5 monarch so we stop guessing.

Run inside Blender:
    blender -b --factory-startup --python debug_s5_measure.py -- \
        --timeline build/timeline_15s.json --assets assets
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpy  # noqa: E402


def parse(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default=str(HERE / "build" / "timeline_15s.json"))
    ap.add_argument("--assets", default=str(HERE / "assets"))
    return ap.parse_args(argv)


def main(argv=None):
    args = parse(argv if argv is not None else sys.argv[sys.argv.index("--") + 1:])
    import render_scene as rs

    rs.ASSETS = Path(args.assets)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rs.SCENE = bpy.context.scene
    mats = rs.build_material_library()
    head, bust, shoulders, neck, mask, eye_light = rs.make_monarch_setup(mats)
    bpy.context.view_layer.update()

    def report(label, group):
        if group is None:
            print(f"[MEASURE] {label}: MISSING")
            return
        lo, hi = rs.bbox_group(group)
        print(f"[MEASURE] {label}: x {lo.x:+.3f}..{hi.x:+.3f} "
              f"(w {hi.x - lo.x:.3f})  y {lo.y:+.3f}..{hi.y:+.3f} "
              f"(d {hi.y - lo.y:.3f})  z {lo.z:+.3f}..{hi.z:+.3f} (h {hi.z - lo.z:.3f})")

    report("BUST", bust)
    report("MASK", mask)
    report("SHOULDERS", shoulders)
    if mask:
        for obj in mask.children_recursive[:12]:
            print(f"[MASK-CHILD] {obj.name} type={obj.type} scale={tuple(round(v, 3) for v in obj.scale)}")

    # Render one frame from the S5 camera so the numbers can be checked visually.
    rs.SCENE.render.engine = "CYCLES"
    rs.SCENE.cycles.device = "CPU"
    rs.SCENE.render.resolution_x = rs.WIDTH
    rs.SCENE.render.resolution_y = rs.HEIGHT
    rs.SCENE.render.image_settings.file_format = "PNG"
    cam = rs.shot_s5(mats, 269, 315)
    rs.SCENE.camera = cam
    rs.SCENE.frame_set(292)
    out = HERE / "frames_debug"
    out.mkdir(parents=True, exist_ok=True)
    rs.SCENE.render.resolution_percentage = 45
    rs.SCENE.cycles.samples = 10
    rs.SCENE.render.filepath = str(out / "s5_debug_")
    bpy.ops.render.render(write_still=True)
    print("[MEASURE] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
