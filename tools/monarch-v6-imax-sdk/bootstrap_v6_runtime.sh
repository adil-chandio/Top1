#!/usr/bin/env bash
# ==============================================================================
# Monarch V6 Hollywood IMAX Cinema SDK — Idempotent Headless Vulkan/WebGL2 & DSP
# Runtime Bootstrapper (runs in /tmp so persistent repo stays lean < 128 MiB!)
# ==============================================================================
set -euo pipefail

echo "[V6-IMAX-SDK] Checking /tmp/v6_runtime, /tmp/chromium, /tmp/sparticuz_libs & /tmp/py..."

mkdir -p /tmp/v6_runtime /tmp/sparticuz_libs /tmp/py

# 1. Node / Three.js / Vite / Playwright / Fonts / Sparticuz Chromium
if [ ! -d "/tmp/v6_runtime/node_modules/three" ] || [ ! -d "/tmp/v6_runtime/node_modules/@sparticuz/chromium" ]; then
  echo "[V6-IMAX-SDK] Installing Node runtime packages into /tmp/v6_runtime..."
  cat > /tmp/v6_runtime/package.json <<'EOF'
{
  "name": "monarch-v6-imax-runtime",
  "private": true,
  "dependencies": {
    "@fontsource-variable/space-grotesk": "^5.2.0",
    "@fontsource/ibm-plex-mono": "^5.2.0",
    "@sparticuz/chromium": "^133.0.0",
    "playwright-core": "^1.51.0",
    "three": "^0.174.0",
    "vite": "^6.2.0"
  }
}
EOF
  npm install --prefix /tmp/v6_runtime --no-audit --no-fund --silent
fi

# 2. Extract @sparticuz/chromium + SwiftShader Vulkan + AL2023 shared libs + absolute ICD symlinks
if [ ! -x "/tmp/chromium" ] || [ ! -f "/tmp/sparticuz_libs/swiftshader/libvk_swiftshader.so" ]; then
  echo "[V6-IMAX-SDK] Extracting @sparticuz/chromium & SwiftShader Vulkan libraries..."
  node -e '
    const fs = require("node:fs");
    const path = require("node:path");
    const { createRequire } = require("node:module");
    const req = createRequire("/tmp/v6_runtime/package.json");
    const chromium = req("@sparticuz/chromium");
    (async () => {
      const binDir = path.join("/tmp/v6_runtime/node_modules/@sparticuz/chromium/bin");
      const execPath = await chromium.executablePath(binDir);
      if (execPath !== "/tmp/chromium" && fs.existsSync(execPath)) {
        fs.copyFileSync(execPath, "/tmp/chromium");
      }
      fs.chmodSync("/tmp/chromium", 0o755);
      console.log("[V6-IMAX-SDK] Chromium binary ready at:", execPath);
    })().catch((e) => { console.error(e); process.exit(1); });
  '

  # Ensure al2023, swiftshader, and fonts archives are unpacked into /tmp/sparticuz_libs
  python3 - <<'PY'
import glob, json, os, shutil, tarfile

bin_dir = "/tmp/v6_runtime/node_modules/@sparticuz/chromium/bin"
out_root = "/tmp/sparticuz_libs"
os.makedirs(out_root, exist_ok=True)

for name in ("al2023", "swiftshader", "fonts"):
    matches = glob.glob(os.path.join(bin_dir, f"{name}.tar*"))
    target = os.path.join(out_root, name)
    os.makedirs(target, exist_ok=True)
    for m in matches:
        if m.endswith(".br"):
            # Already extracted by @sparticuz/chromium into /tmp; copy if present
            tmp_src = os.path.join("/tmp", name)
            if os.path.isdir(tmp_src):
                shutil.copytree(tmp_src, target, dirs_exist_ok=True)
        elif tarfile.is_tarfile(m):
            with tarfile.open(m) as tf:
                tf.extractall(target)

# Also sync /tmp/al2023, /tmp/swiftshader, /tmp/fonts if @sparticuz unpacked there
for name, sub in [("al2023", "al2023"), ("swiftshader", "swiftshader"), ("fonts", "fonts")]:
    for cand in [f"/tmp/{name}", f"/tmp/{name}/lib"]:
        if os.path.isdir(cand) and cand != os.path.join(out_root, sub):
            shutil.copytree(f"/tmp/{name}", os.path.join(out_root, sub), dirs_exist_ok=True)
            break

# Locate libvk_swiftshader.so and write ABSOLUTE vk_swiftshader_icd.json
vk_so = None
for root, _, files in os.walk(out_root):
    if "libvk_swiftshader.so" in files:
        vk_so = os.path.join(root, "libvk_swiftshader.so")
        break
if vk_so is None and os.path.isfile("/tmp/libvk_swiftshader.so"):
    os.makedirs(os.path.join(out_root, "swiftshader"), exist_ok=True)
    vk_so = os.path.join(out_root, "swiftshader/libvk_swiftshader.so")
    shutil.copy2("/tmp/libvk_swiftshader.so", vk_so)

assert vk_so and os.path.isfile(vk_so), "libvk_swiftshader.so not found!"
ss_dir = os.path.dirname(vk_so)
icd_path = os.path.join(ss_dir, "vk_swiftshader_icd.json")
with open(icd_path, "w", encoding="utf-8") as f:
    json.dump({"file_format_version": "1.0.0", "ICD": {"library_path": vk_so, "api_version": "1.0.5"}}, f)

# Symlink EGL/GLESv2/SwiftShader/Vulkan directly into /tmp alongside /tmp/chromium
for fname in ("libEGL.so", "libGLESv2.so", "libvk_swiftshader.so", "vk_swiftshader_icd.json"):
    src = os.path.join(ss_dir, fname)
    dst = os.path.join("/tmp", fname)
    if os.path.isfile(src):
        if os.path.lexists(dst):
            os.remove(dst)
        os.symlink(src, dst)

for root, _, files in os.walk(out_root):
    if "libvulkan.so.1" in files:
        src = os.path.join(root, "libvulkan.so.1")
        dst = "/tmp/libvulkan.so.1"
        if os.path.lexists(dst):
            os.remove(dst)
        os.symlink(src, dst)
        break
PY
fi

# 3. Python Audio DSP & Video/FFmpeg Stack
if ! PYTHONPATH=/tmp/py python3 -c "import numpy, scipy, soundfile, PIL, pytest, imageio_ffmpeg, jsonschema" >/dev/null 2>&1; then
  echo "[V6-IMAX-SDK] Installing Python DSP & FFmpeg packages into /tmp/py..."
  pip install --quiet --target /tmp/py numpy scipy soundfile Pillow pytest imageio-ffmpeg jsonschema
fi

echo "[V6-IMAX-SDK] Bootstrap 100% READY (WebGL2 SwiftShader + Fonts + Audio DSP + FFmpeg)!"
