#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
D=tools/monarch-ant-v3/short-v2
S=${MONARCH_SHORT_BASE:-.cache/monarch-ant-short}
C=${MONARCH_SHORT_V2_CACHE:-.cache/monarch-ant-short-v2}
G=$(realpath "${MONARCH_EGL:-$S/egl}")
W=${SHORT_NATIVE_W:-810}; H=$((W*16/9)); bin="$C/portrait-render"
mkdir -p "$C/plates" "$C/trace"
if [[ ! -x "$bin" ]] || [[ -n $(find tools/monarch-ant{,-v2,-v3} \( -name '*.cpp' -o -name '*.hpp' \) -newer "$bin" -print -quit) ]]; then
  g++ -std=c++17 -O3 -Werror -Wall -Wextra -DNDEBUG tools/monarch-ant-v3/render.cpp -L"$G" -Wl,-rpath,"$G" -lEGL -lGLESv2 -o "$bin.new"
  mv "$bin.new" "$bin"
fi
# The short's human-facing EDL keeps the tag before the native clock.
awk 'NF>0 && $1!~/^#/ {printf "%s %s %s %s %s %s %s",$1,$2,$3,$4,$6,$7,$5;for(i=8;i<=NF;i++)printf " %s",$i;printf "\n"}' "$D/edit.plan" > "$C/render.plan"
export LD_LIBRARY_PATH="$G${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" VK_DRIVER_FILES="$G/vk_swiftshader_icd.json"
base=(--width "$W" --height "$H" --portrait 1 --feature 1 --cache "$S" --plan "$C/render.plan")
if [[ -n ${SHORT_STILLS:-} ]]; then "$bin" "${base[@]}" --ppm "$C/probe" --trace "$C/probe.csv" --stills "$SHORT_STILLS"; exit; fi
[[ "$W" == 810 && "$H" == 1440 ]]
sig=$(sha256sum "$bin" "$C/render.plan" "$S"/assets/{quartz,cuticle,canopy}.rgba | awk '{print $1}' | sha256sum | awk '{print $1}')
while read -r a b _; do
  [[ "$a" =~ ^[0-9]+$ ]] || continue
  if grep -q "\"$a\":" "$D/reuse.json"; then continue; fi
  if [[ $# -gt 0 && " $* " != *" $a "* ]]; then continue; fi
  f="$C/plates/$a.rgba"; tr="$C/trace/$a.csv"; rev="$C/trace/$a.build"; bytes=$((W*H*4*(b-a)))
  if [[ -s "$f" && -s "$tr" && -s "$rev" && $(<"$rev") == "$sig" && $(stat -c %s "$f") -eq "$bytes" ]]; then continue; fi
  "$bin" "${base[@]}" --first "$a" --end "$b" --trace "$tr.pending" > "$f.pending"
  test "$(stat -c %s "$f.pending")" -eq "$bytes" && test "$(wc -l < "$tr.pending")" -eq "$((b-a+1))"
  mv "$f.pending" "$f"; mv "$tr.pending" "$tr"; printf '%s\n' "$sig" > "$rev"
  printf 'SHORT_V2_PLATE_READY %d..%d\n' "$a" "$((b-1))"
done < "$C/render.plan"
printf 'SHORT_V2_NATIVE_READY\n'
