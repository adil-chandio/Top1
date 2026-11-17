#!/usr/bin/env python3
"""Execute render_scene.py under the `bpy` Python module."""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.argv = [str(HERE / "render_scene.py")] + sys.argv[1:]
runpy.run_path(str(HERE / "render_scene.py"), run_name="__main__")
