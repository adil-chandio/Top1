#!/usr/bin/env bash
# Headless bpy in this image: pip's bpy needs X/GL libs that aren't installed.
# Generate no-op stubs for exactly the symbols bpy's .so files reference.
set -euo pipefail
mkdir -p /tmp/xstub && cd /tmp/xstub
PY="${1:-/tmp/venv/bin/python}"
SITE=$("$PY" -c "import sysconfig;print(sysconfig.get_paths()['purelib'])")
"$PY" - "$SITE" <<'PY'
import subprocess, glob, sys
site = sys.argv[1]
libs = [f"{site}/bpy/__init__.so"] + glob.glob(f"{site}/bpy/lib/*.so*")
out = subprocess.run(["nm", "-D", "--undefined-only"] + libs,
                     capture_output=True, text=True).stdout
syms = {l.split()[-1].split("@")[0] for l in out.splitlines() if len(l.split()) >= 2}
pre = ("gl", "egl", "XRender", "XFixes", "XI", "xkb_", "Sm", "Ice", "Xt", "XESet",
       "XOpen", "XClose", "XQuery", "XGet", "XList", "XSelect", "XFree", "_Xi")
need = sorted({s for s in syms if s.startswith(pre)})
open("stubs.c", "w").write("\n".join(f"void* {n}(){{return 0;}}" for n in need) + "\n")
print(f"{len(need)} stub symbols")
PY
for n in libGL.so.1 libEGL.so.1 libXrender.so.1 libXi.so.6 libXfixes.so.3 \
         libxkbcommon.so.0 libSM.so.6 libICE.so.6 libXt.so.6; do
  gcc -shared -fPIC -Wl,-soname,$n -o "$n" stubs.c
done
LD_LIBRARY_PATH=/tmp/xstub "$PY" -c "import bpy;print('bpy', bpy.app.version_string, 'OK')"
