# Monarch Cam 01A · Short V2

The delivery revision is still 34.000 seconds. It replaces the listening
experience of the first promo, not the earlier file or the long film. The
voice is the same selected English speaker with newly written and generated
lines. Small cuts remove quiet gaps only; they do not stretch or pitch-shift
spoken words. Matched dry snaps, granular Foley and a moving score remain
under the narration. The last line asks the research question, not for a tap.

## Rebuild

Run from root. Restore the portrait build in [`../short`](../short) if its native
plates, font, audio banks or EGL runtime are missing. Point `MONARCH_SHORT_BASE`
to that cache if relocated. Install the same NumPy/Pillow/FFmpeg and
PocketSphinx 5.0.4 (for script alignment only; word list is in `story.json`).
Add the six original WAV takes under `.cache/monarch-ant-short-v2/vo/` and use
the old `FFMPEG` path or set your own. All new plates/mixes and caption receipts
use `MONARCH_SHORT_V2_CACHE`. No external binary files are checked into Git.

```bash
D=tools/monarch-ant-v3/short-v2
"$D/native.sh"       # 10 fresh takes, 8 contiguous reused V1 raw spans
python3 -B "$D/sound.py"
python3 -B "$D/finish.py"
python3 -B "$D/check.py"
```

`edit.plan` and `reuse.json` are the picture EDL. Deliberate frame pins put
contact at f5/439 followed immediately by lift; air snap at f328 has no such
lift; one clears the rim at f629, another touches the wall at f696. The model's
timing is illustrative. `sound.py` logs splice levels and measures both voice
and full-program gaps before committing the mix. `check.py` decodes a complete
1,020-frame export, checks sample/frame clocks and peak level, repeats the
full-mix floor test on AAC, and writes QA-only phone stills. Final MP4, SRT and
Studio copy go to `deliverables/monarch-cam-step-6-short-v2/`.
