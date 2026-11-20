# Monarch Cam 01A · Short Voice Match

Audio repair for the 34-second Foley Mix. The original Short cut was 4.30 LU
louder than the accepted long film and had stronger upper mids and sibilants.
This pass uses that film's approved dry speech master for timbre and its final
mix for loudness. It does not reuse a piece of the film or change the read.

The previous Short's narration was recovered at its original sample positions
by rebuilding its stereo accompaniment from the pinned banks. The original
stereo difference and the full-mix reconstruction are checked before processing.
A small broad upper-mid cut removes the old presence push. Dynamic attenuation
controls only the harsher moments in the speech, not the whole sound track.
The original Foley cues and background remain synced and are balanced at the
new reference level. No additional voice recording, time stretch or caption
edit is involved.

## Rebuild

Use Python 3.11+, NumPy 2.2.6, SciPy 1.15.3, Pillow 11.3.0, PocketSphinx 5.0.4,
and FFmpeg 7.0.2 (e.g. the imageio-ffmpeg 0.6.0 binary). Use the same shared
recordings and score banks as the [Foley Mix](../short-foley). Place the four
locked inputs listed in `voice_match.py` in the following cache's `reference/`
directory. The long review copy and WAV can be restored from Drive. No V2
renderer/cache or isolated Short voice takes are required.

```bash
# From repo root; dependencies must already be installed or on PYTHONPATH.
C=.cache/monarch-ant-short-voice
export MONARCH_SHORT_VOICE_CACHE="$C"
export MONARCH_V2_CACHE="$C/bank"
export FFMPEG=/path/to/ffmpeg
python3 -B tools/monarch-ant-v2/audio_sources.py --fetch  # only if not restored
python3 -B tools/monarch-ant-v3/short-voice/voice_match.py
```

`receipt.json` records SHA-256 checks, active dialogue-band comparisons, original
and new program loudness, AAC/sample-clock verification, effects marks, and
H.264 packet identity. The 1,020-frame file and its matching SRT/copy are promoted
only after these checks. `MONARCH_SHORT_VOICE_DELIVERY` can redirect output;
otherwise it's `deliverables/monarch-cam-step-6-short-voice/`. The separate Studio
Related video setup is in `upload.txt`; nothing is published by the script.
