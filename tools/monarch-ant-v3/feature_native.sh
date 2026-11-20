#!/usr/bin/env bash
# Short restartable film blocks; only the native picture and internal matte are cached.
set -euo pipefail
cd "$(dirname "$0")/../.."
C=${MONARCH_V3_CACHE:-.cache/monarch-ant-v3}; K="$C/feature"; G=${MONARCH_EGL:?set MONARCH_EGL}
w=1280; h=720
mkdir -p "$K/work" "$K/qa"
bin="$K/work/studio-render"
if [[ ! -x "$bin" ]] || [[ -n $(find tools/monarch-ant{,-v2,-v3} \( -name '*.hpp' -o -name '*.cpp' \) -newer "$bin" -print -quit) ]]; then
  g++ -std=c++17 -O3 -Wall -Wextra -Werror -DNDEBUG tools/monarch-ant-v3/render.cpp -L"$G" -Wl,-rpath,"$G" -lEGL -lGLESv2 -o "$bin.new"
  mv "$bin.new" "$bin"
fi
export LD_LIBRARY_PATH="$G${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" VK_DRIVER_FILES="$G/vk_swiftshader_icd.json"
plan=${FEATURE_PLAN:-"$K/work/feature.plan"}
bounds=(0 708 2182 3700 5188 6658 8011 8994)
if [[ $# -eq 0 ]]; then set -- 2 3 4 5 6 7; fi
for ch in "$@"; do
  [[ "$ch" =~ ^[2-7]$ ]] || { echo "Invalid feature chapter $ch" >&2; exit 2; }
  lo=${bounds[ch-1]}; hi=${bounds[ch]}
  # Divide at extant edit points to preserve stable plate caching and enable targeted retakes.
  points=$(awk -v a="$lo" -v b="$hi" '$1>=a && $2<=b {print $1, $2}' "$plan")
  readarray -t blocks <<< "$points"
  for block in "${blocks[@]}"; do
    read -r a b <<< "$block"
    if [[ -n ${FEATURE_ONLY:-} && ",${FEATURE_ONLY}," != *",$a,"* ]]; then continue; fi
    p="$K/work/take-$a.plates"; csv="$K/qa/take-$a.csv"
    if [[ -s "$p" && -s "$csv" && ${FEATURE_FORCE:-0} != 1 ]]; then continue; fi
    "$bin" --width "$w" --height "$h" --feature 1 --cache "$C" --plan "$plan" --first "$a" --end "$b" --trace "$csv.pending" \
      | python3 -B tools/monarch-ant-v3/platepack.py "$p.pending" "$w" "$h" "$a" "$b"
    test "$(wc -l < "$csv.pending")" -eq "$((b-a+1))"
    mv "$p.pending" "$p"; mv "$csv.pending" "$csv"
  done
  printf 'FEATURE_NATIVE_CHAPTER_%d (%d..%d) READY\n' "$ch" "$lo" "$hi"
done
