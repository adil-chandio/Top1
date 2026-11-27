#!/usr/bin/env bash
# ==============================================================================
# Logan Claw-Pop VFX Rig Breakdown (V6.2 Hollywood IMAX)
# Idempotent /tmp Asset Stager (keeps persistent Git workspace lean < 128 MiB!)
# Uses MIT-licensed Unreal MetaHuman 5.7 Bruce rig (`creategamecharacters/metahuman-to-glb`)
# ==============================================================================
set -euo pipefail

DEST="/tmp/v6_runtime/assets/bruce"
if [ -f "$DEST/bruce.glb" ] && [ -f "$DEST/mh_materials.json" ] && [ -d "$DEST/textures" ]; then
  echo "[Logan-V6] MetaHuman rig assets already staged at $DEST"
  exit 0
fi

echo "[Logan-V6] Staging MIT-licensed MetaHuman 5.7 rig into $DEST..."
TMP_REPO="/tmp/mh_bruce_sparse"
rm -rf "$TMP_REPO"
git clone --depth 1 --filter=blob:none --sparse https://github.com/creategamecharacters/metahuman-to-glb.git "$TMP_REPO"
(
  cd "$TMP_REPO"
  git sparse-checkout set docs/5.7/characters/bruce
)
mkdir -p "/tmp/v6_runtime/assets"
rm -rf "$DEST"
cp -r "$TMP_REPO/docs/5.7/characters/bruce" "$DEST"
cp "$TMP_REPO/LICENSE" "$DEST/LICENSE.txt"
rm -rf "$TMP_REPO"
echo "[Logan-V6] Staged bruce.glb + hair/beard/brow/mustache atlases at $DEST"
