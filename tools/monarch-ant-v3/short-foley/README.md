# Monarch Cam 01A · Short Foley Mix

This is an audio-only revision of the 34-second Short V2. `remix.py` verifies
and copies V2's H.264 video packets, uses the same VO edits and gain, and
conforms the long film's Foley recordings to the Short's existing picture
marks. It replaces the old effects bus, not the whole program with a piece
of feature audio. The original 25 caption cues are carried over verbatim.

| Short frame | Time | Effect |
|---:|---:|---|
| 5 | 0.167 s | Dry jaw contact, short body, and spreading grit |
| 194 | 6.467 s | Antlion flick and falling grains |
| 328 | 10.933 s | Air-only snap without the body or sand burst |
| 439 | 14.633 s | Jaw-to-sand contact; lift follows on the next frame |
| 644 | 21.467 s | Rim touchdown with a separate grit tail |
| 696 | 23.200 s | Dull wall hit, followed by sand sliding back down |

The effects are fit to the cut from the pinned banks in [`../pilot_mix.py`](../pilot_mix.py)
and [`../feature_mix.py`](../feature_mix.py). Short gain rides and score dips
clear the six main actions without bringing up the full mix or retiming
narration. The quiet closing experiment has sand/score underneath it but no
fake snap on the immobilized jaws, and no on-screen or narrated click prompt.

## Rebuild and verify

Use the same dependencies, voice takes, and banks as [`../short-v2`](../short-v2).
Have the verified V2 delivery MP4/SRT and the V2 cache's `qa/mix.json` and
`work/short-v2-mix.wav` available. Native plates and a feature MP4 are not
needed. No new speech, image generation, or network fetch is required.

```bash
# From the repository root, with the shared audio/Short V2 caches present.
O=.cache/monarch-ant-short
P=.cache/monarch-ant-short-v2
export PYTHONPATH="$O/python:$P/python" OPENBLAS_NUM_THREADS=1
export FFMPEG=$(realpath "$O"/python/imageio_ffmpeg/binaries/ffmpeg-linux-*)
python3 -B tools/monarch-ant-v3/short-foley/remix.py
```

The gate checks the V2 PCM reconstruction, VO timing, mono phone-band effect
levels versus V2, score and effects versus narration, limiter and AAC timing,
true peak/loudness, video packet identity, the decoded 1,020-frame PTS clock,
fast start, and the original subtitle checksum. `MONARCH_SHORT_FOLEY_CACHE`
redirects local-only stems and the QA `receipt.json`; use
`MONARCH_SHORT_FOLEY_DELIVERY` to redirect the MP4, SRT and Studio notes. The
default is `deliverables/monarch-cam-step-6-short-foley/`. No prior delivery
is overwritten. `upload.txt` describes the separate Studio Related video
step; this pipeline does not publish or link anything.
