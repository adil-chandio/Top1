#!/usr/bin/env bash
# Restartable, lossless native picture + matte renders (scratch only).
set -euo pipefail
cd "$(dirname "$0")/../.."
C=${MONARCH_V3_CACHE:-.cache/monarch-ant-v3}
G=${MONARCH_EGL:?set MONARCH_EGL to ANGLE/SwiftShader runtime directory}
mkdir -p "$C/work" "$C/qa"
w=${V3_WIDTH:-1920}; h=${V3_HEIGHT:-1080}
exe="$C/work/render-v3"
if [[ ! -x "$exe" ]] || [[ -n $(find tools/monarch-ant{,-v2,-v3} \( -name '*.hpp' -o -name '*.cpp' \) -newer "$exe" -print -quit) ]]; then
  g++ -std=c++17 -O3 -Wall -Wextra -Werror -DNDEBUG tools/monarch-ant-v3/render.cpp -L"$G" -Wl,-rpath,"$G" -lEGL -lGLESv2 -o "$exe.new"
  mv -f "$exe.new" "$exe"
fi
export LD_LIBRARY_PATH="$G${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" VK_DRIVER_FILES="$G/vk_swiftshader_icd.json"
lo=(0 194 333 484); hi=(194 333 484 708)
if [[ $# -gt 0 ]]; then
  for id in "$@"; do
    [[ "$id" =~ ^[0-3]$ ]] || { echo "Unknown render piece: $id" >&2; exit 2; }
  done
  if [[ -s "$C/work/native-size.txt" && $(cat "$C/work/native-size.txt") != "$w $h" ]]; then
    echo "A partial retake needs the same dimensions as existing plates" >&2
    exit 2
  fi
fi
for i in 0 1 2 3; do
  [[ $# -eq 0 || " $* " == *" $i "* ]] || continue
  a=${lo[i]}; b=${hi[i]}; p="$C/work/native-$i.rgba"; csv="$C/qa/native-$i.csv"
  "$exe" --cache "$C" --width "$w" --height "$h" --first "$a" --end "$b" --trace "$csv.pending" > "$p.pending"
  size=$(( (b-a)*w*h*4 ))
  [[ $(stat -c %s "$p.pending") -eq $size ]]
  mv -f "$p.pending" "$p"; mv -f "$csv.pending" "$csv"
  printf 'V3_NATIVE_%s_READY (%s to %s)\n' "$i" "$a" "$b"
done
printf '%s %s\n' "$w" "$h" > "$C/work/native-size.txt"
for i in 0 1 2 3; do
  [[ -s "$C/work/native-$i.rgba" ]] || exit 0
  [[ $(stat -c %s "$C/work/native-$i.rgba") -eq $(( (hi[i]-lo[i])*w*h*4 )) ]]
done
"$exe" --cache "$C" --width "$w" --height "$h" --guides "$C/work/jaw-guide.csv"
echo V3_NATIVE_PICTURE_READY
