#!/bin/bash
# Rebuild the local render environment from scratch.
#
# Why this exists: the sandbox cannot reach Debian mirrors, and GitHub's hosted
# runners were unavailable, so Blender is installed as a PyPI wheel (`bpy`) and
# the seven missing X11/GL libraries are compiled from the shims in ./shims as
# no-op stubs — a background Cycles render never opens a display, so those entry
# points are unreachable by construction.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STUBS=/tmp/stubs

echo "== 1/4 python deps =="
pip install --quiet --target /tmp/bpy bpy
pip install --quiet --target /tmp/pydeps numpy scipy pillow imageio-ffmpeg

echo "== 2/4 GUI-only library shims =="
mkdir -p "$STUBS"
gcc -shared -fPIC -Wl,-soname,libGL.so.1        -o "$STUBS/libGL.so.1"        "$HERE/shims/gl_all.c"
gcc -shared -fPIC -Wl,-soname,libXfixes.so.3    -o "$STUBS/libXfixes.so.3"    "$HERE/shims/x_all.c"
gcc -shared -fPIC -Wl,-soname,libXrender.so.1   -o "$STUBS/libXrender.so.1"   "$HERE/shims/x_all.c"
gcc -shared -fPIC -Wl,-soname,libXi.so.6        -o "$STUBS/libXi.so.6"        "$HERE/shims/x_all.c"
gcc -shared -fPIC -Wl,-soname,libSM.so.6        -o "$STUBS/libSM.so.6"        "$HERE/shims/sm_all.c"
gcc -shared -fPIC -Wl,-soname,libICE.so.6       -o "$STUBS/libICE.so.6"       "$HERE/shims/sm_all.c"
gcc -shared -fPIC -Wl,-soname,libxkbcommon.so.0 \
    -Wl,--version-script,"$HERE/shims/xkb0.map" -o "$STUBS/libxkbcommon.so.0" "$HERE/shims/xkb_all.c"

echo "== 3/4 ffmpeg =="
FF=$(ls /tmp/pydeps/imageio_ffmpeg/binaries/ffmpeg-* 2>/dev/null | head -1)
mkdir -p /tmp/pydeps/bin && chmod +x "$FF" && ln -sf "$FF" /tmp/pydeps/bin/ffmpeg

echo "== 4/4 verify =="
LD_LIBRARY_PATH=$STUBS:/tmp/bpy/bpy/lib PYTHONPATH=/tmp/bpy python3 -c \
  "import bpy; print('bpy', bpy.app.version_string, 'ready')"
