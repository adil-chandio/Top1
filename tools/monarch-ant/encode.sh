#!/usr/bin/env bash
# Offline frame pipe. No intermediate uncompressed frames and no publishing.
set -euo pipefail
cd "$(dirname "$0")/../.."
C=${MONARCH_ANT_CACHE:-.cache/monarch-cam-ant-film}
G=${MONARCH_EGL:?Set MONARCH_EGL to the ANGLE / SwiftShader library directory.}
FF=${FFMPEG:-ffmpeg}
W=$1 H=$2 PLAN=$3 OUTPUT=$4
shift 4
[ -s "$PLAN" ]
mkdir -p "$C/work"
if [ ! -x "$C/work/ant-render" ] || find tools/monarch-ant -maxdepth 1 \( -name '*.hpp' -o -name 'render.cpp' \) -newer "$C/work/ant-render" | grep -q .; then
    g++ -std=c++17 -O3 -DNDEBUG tools/monarch-ant/render.cpp -L"$G" -lEGL -lGLESv2 -Wl,-rpath,"$G" -o "$C/work/ant-render"
fi
vbv=()
if [ -n "${VIDEO_MAXRATE:-}" ]; then vbv=(-maxrate "$VIDEO_MAXRATE" -bufsize "${VIDEO_BUFSIZE:-$VIDEO_MAXRATE}"); fi
part="${OUTPUT%.mp4}.rendering.mp4"
trap 'rm -f "$part"' EXIT
LD_LIBRARY_PATH="$G${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" VK_DRIVER_FILES="$G/vk_swiftshader_icd.json" \
 "$C/work/ant-render" --dir "$C" --plan "$PLAN" --width "$W" --height "$H" "$@" | \
 "$FF" -nostdin -hide_banner -loglevel warning -xerror -f rawvideo -pixel_format rgba -video_size "$W"x"$H" -framerate "${RENDER_FPS:-24}" -i pipe:0 \
 -filter_threads 1 -vf 'vflip,scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p' -an \
 -c:v libx264 -threads 1 -preset "${X264_PRESET:-fast}" -crf "${VIDEO_CRF:-18}" -g "${GOP:-48}" -pix_fmt yuv420p \
 "${vbv[@]}" -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv -movflags +faststart -y "$part"
mv -f "$part" "$OUTPUT"
