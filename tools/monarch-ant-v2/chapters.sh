#!/usr/bin/env bash
# Render in restartable chapter segments. Every output frame is a new scene evaluation.
set -euo pipefail
cd "$(dirname "$0")/../.."
C=${MONARCH_V2_CACHE:-.cache/monarch-ant-v2}; FF=${FFMPEG:-ffmpeg}
mkdir -p "$C/work/chapter-renders" "$C/qa"
plan="$C/work/film-v2.plan"
frames="$C/work/chapter-renders/segments.txt"
python3 -B - "$C" > "$frames" <<'PY'
import json,sys
from pathlib import Path
j=json.loads((Path(sys.argv[1])/'work/film-v2.json').read_text());assert j['fps']==30
bounds=[f for f,_ in j['chapters']]+[j['frames']]
for k,(a,b) in enumerate(zip(bounds,bounds[1:]),1):print(k,a,b)
PY
export MONARCH_V2_FPS=30
while read -r id lo hi; do
 [[ $# -gt 0 && " $* " != *" $id "* ]] && continue
 clip="$C/work/chapter-renders/chapter-$id.mp4"; tr="$C/qa/native-$id.csv"
 tools/monarch-ant-v2/encode.sh 1280 720 "$plan" "$clip" --first "$lo" --end "$hi" --trace "$tr.tmp"
 mv -f "$tr.tmp" "$tr"
 echo "CHAPTER_${id}_READY · [$lo,$hi)"
done < "$frames"
for id in {1..7}; do [[ -s "$C/work/chapter-renders/chapter-$id.mp4" && -s "$C/qa/native-$id.csv" ]] || exit 0; done
clips="$C/work/chapter-renders/concat.ffconcat"
{
  echo 'ffconcat version 1.0'
  while read -r id lo hi; do
    printf "file 'chapter-%s.mp4'\n" "$id"
    awk -v n="$((hi-lo))" 'BEGIN{printf "duration %.9f\n",n/30}'
  done < "$frames"
} > "$clips"
"$FF" -nostdin -hide_banner -loglevel warning -xerror -f concat -safe 1 -i "$clips" -map 0:v:0 -c copy -map_metadata -1 -movie_timescale 48000 -movflags +faststart+write_colr -y "$C/work/v2-picture.concat.mp4"
mv -f "$C/work/v2-picture.concat.mp4" "$C/work/v2-picture.mp4"
head -n 1 "$C/qa/native-1.csv" > "$C/qa/v2-native-trace.csv"
for id in {1..7}; do tail -n +2 "$C/qa/native-$id.csv" >> "$C/qa/v2-native-trace.csv"; done
printf 'V2_PICTURE_READY\n'
