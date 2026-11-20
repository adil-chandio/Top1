#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
C=${MONARCH_V2_CACHE:-.cache/monarch-ant-v2}
G=${MONARCH_EGL:?set MONARCH_EGL to the directory with ANGLE and SwiftShader libraries}
FF=${FFMPEG:-ffmpeg}
w=$1; h=$2; plan=$3; out=$4; shift 4
mkdir -p "$C/work"
exe="$C/work/cinema-render"
if [ ! -x "$exe" ] || find tools/monarch-ant{,-v2} -maxdepth 1 \( -name '*.hpp' -o -name 'render.cpp' \) -newer "$exe" | grep -q .; then
  g++ -std=c++17 -O3 -DNDEBUG -Wall -Wextra -Werror tools/monarch-ant-v2/render.cpp -L"$G" -Wl,-rpath,"$G" -lEGL -lGLESv2 -o "$exe.new"
  mv -f "$exe.new" "$exe"
fi
speed=${MONARCH_V2_FPS:-30}
tmp="${out%.mp4}.encoding.mp4"
trap 'rm -f "$tmp"' EXIT
export LD_LIBRARY_PATH="$G${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" VK_DRIVER_FILES="$G/vk_swiftshader_icd.json"
"$exe" --cache "$C" --width "$w" --height "$h" --plan "$plan" "$@" | \
 "$FF" -nostdin -hide_banner -loglevel warning -xerror -f rawvideo -pixel_format rgba -video_size "$w"x"$h" -framerate "$speed" -i pipe:0 \
 -filter_threads 1 -vf 'vflip,scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p' -an \
 -c:v libx264 -threads 1 -preset "${X264_PRESET:-veryfast}" -crf "${VIDEO_CRF:-17}" -maxrate "${VIDEO_MAXRATE:-2300k}" -bufsize "${VIDEO_BUFSIZE:-4650k}" -g "$((speed*2))" \
 -bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0 \
 -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv -movie_timescale 48000 -movflags +faststart+write_colr -y "$tmp"
mv "$tmp" "$out"
