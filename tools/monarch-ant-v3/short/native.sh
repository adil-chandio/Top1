#!/usr/bin/env bash
# Restartable native portrait plates. These are not inputs to the V3 feature.
set -euo pipefail
cd "$(dirname "$0")/../../.."
D=tools/monarch-ant-v3/short
C=${MONARCH_SHORT_CACHE:-.cache/monarch-ant-short}
G=$(realpath "${MONARCH_EGL:-$C/egl}")
W=810 H=1440
mkdir -p "$C/plates" "$C/trace"
bin="$C/portrait-render"
if [[ ! -x "$bin" ]] || [[ -n $(find tools/monarch-ant{,-v2,-v3} \( -name '*.cpp' -o -name '*.hpp' \) -newer "$bin" -print -quit) ]]; then
  g++ -std=c++17 -O3 -Wall -Wextra -Werror -DNDEBUG tools/monarch-ant-v3/render.cpp -L"$G" -Wl,-rpath,"$G" -lEGL -lGLESv2 -o "$bin.new"
  mv "$bin.new" "$bin"
fi
export LD_LIBRARY_PATH="$G${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" VK_DRIVER_FILES="$G/vk_swiftshader_icd.json"
for mat in quartz cuticle canopy; do test -s "$C/assets/$mat.rgba"; done
fingerprint=$(sha256sum "$bin" "$D/edit.plan" "$C"/assets/{quartz,cuticle,canopy}.rgba | cut -d ' ' -f 1 | sha256sum | cut -d ' ' -f 1)
while read -r a b _; do
  [[ "$a" =~ ^[0-9]+$ ]] || continue
  if [[ $# -ne 0 && " $* " != *" $a "* ]]; then continue; fi
  f="$C/plates/$a.rgba"; tr="$C/trace/$a.csv"; rev="$C/trace/$a.build"
  bytes=$((W*H*4*(b-a)))
  if [[ -s "$f" && -s "$tr" && -s "$rev" && $(<"$rev") == "$fingerprint" && $(stat -c %s "$f") -eq "$bytes" ]]; then continue; fi
  "$bin" --width "$W" --height "$H" --portrait 1 --feature 1 --cache "$C" --plan "$D/edit.plan" --first "$a" --end "$b" --trace "$tr.pending" > "$f.pending"
  test "$(stat -c %s "$f.pending")" -eq "$bytes"
  test "$(wc -l < "$tr.pending")" -eq "$((b-a+1))"
  mv "$f.pending" "$f"; mv "$tr.pending" "$tr"; printf '%s\n' "$fingerprint" > "$rev"
  printf 'PORTRAIT_PLATE_READY %d..%d\n' "$a" "$((b-1))"
done < "$D/edit.plan"
printf 'PORTRAIT_NATIVE_DONE\n'
