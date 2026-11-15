#!/usr/bin/env bash
# Blender-in-sandbox: bpy needs X/GL libs that this image doesn't ship.
# Build no-op stubs for exactly the symbols bpy's .so files reference, then LD_LIBRARY_PATH them.
set -e
mkdir -p /tmp/xstub && cd /tmp/xstub
python3 - <<'PY'
import subprocess, glob
libs = ["/usr/local/lib/python3.11/dist-packages/bpy/__init__.so"] + \
       glob.glob("/usr/local/lib/python3.11/dist-packages/bpy/lib/*.so*")
out = subprocess.run(["nm", "-D", "--undefined-only"] + libs, capture_output=True, text=True).stdout
syms = {l.split()[-1].split("@")[0] for l in out.splitlines() if l.strip()}
pre = ("gl", "egl", "XRender", "XFixes", "XI", "xkb_", "Sm", "Ice", "Xt", "XESet")
extra = ("XOpenDevice","XCloseDevice","XFreeDeviceList","XQueryDeviceState","XFreeDeviceState",
         "XGetExtensionVersion","XListInputDevices","_XiGetDevicePresenceNotifyEvent","XSelectExtensionEvent")
need = sorted({s for s in syms if s.startswith(pre) or s in extra})
open("stubs.c", "w").write("\n".join(f"void* {n}(){{return 0;}}" for n in need) + "\n")
PY
for n in libGL.so.1 libXrender.so.1 libXi.so.6 libXfixes.so.3 libxkbcommon.so.0 libSM.so.6 libICE.so.6 libXt.so.6; do
  gcc -shared -fPIC -Wl,-soname,$n -o "$n" stubs.c
done
echo "stubs ready: LD_LIBRARY_PATH=/tmp/xstub python3 scene3d.py <shot> <out.png>"
