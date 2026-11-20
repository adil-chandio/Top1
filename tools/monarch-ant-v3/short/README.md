# Monarch Cam 01A · Bite-to-jump Short

A separate 34.000-second promo, not a crop, re-encode, or revision of the V3
feature. Uses its trap-jaw and antlion rigs, contact solver and lab models.
The portrait optics, procedural materials, picture clock, narration edit,
score, Foley and small editorial cues are specific to this Short. The Short
shows the bite and a failed escape; it introduces the restraint experiment
without revealing its results or asking for a click.

## Build from the repo root

Dependencies: Python 3.11+, NumPy 2.2.6, Pillow 11.3.0, FFmpeg with libx264
(tested with imageio-ffmpeg 0.6.0), g++, and an EGL/GLES3 runtime. Put ANGLE's
SwiftShader files from `@sparticuz/chromium@131.0.1` (archive
`package/bin/swiftshader.tar.br`) in `$C/egl` or set `MONARCH_EGL`. `FFMPEG`
may point directly to the imageio binary. The native render needs about 4.8 GB
of scratch for 810×1440 RGBA plates. `native.sh` fingerprints the binary,
materials and plan and resumes complete takes. It accepts an optional list of
shot start frames for targeted checks or retakes.

```sh
D=tools/monarch-ant-v3/short
C=${MONARCH_SHORT_CACHE:-.cache/monarch-ant-short}
# Put original generated narrative WAVs in "$C/vo", using voice.json names.
# Put pinned SpaceGrotesk.ttf in .cache/monarch-ant-packaging/fonts, or point
# MONARCH_SHORT_FONT to it. Exact source and OFL are in ../packaging/README.md.
MONARCH_V2_CACHE="$C/v2" python3 -B tools/monarch-ant-v2/audio_sources.py --fetch
python3 -B "$D/materials.py" "$C/assets"
"$D/native.sh"
python3 -B "$D/sound.py"
python3 -B "$D/picture.py"
python3 -B "$D/verify.py"
```

`voice.json` includes the approved-session speaker, exact narration, per-take
trim and sample placements, plus an SRT cue list. Unlike the feature, the promo's
recorded words are newly generated rather than lifted from the earlier WAV.
Re-synthesizing may yield a different read and require re-spotting; don't time
stretch new readings to the old waveform. No title or caption is sourced from
an unverified transcript.

The verify step fully decodes the 30 fps Rec.709 MP4 and confirms the 1,020
CFR pictures, true peak and AAC clock, actual blade contact→lift, rim vs wall,
and the near-continuous loop seam. It writes inspection stills with *mock* UI
in `$C/qa` and promotes only the upload MP4, English SRT and Studio paste sheet
into `deliverables/monarch-cam-step-6-short/`. No CTA overlays, arrows or mock
buttons are in the rendered video. `upload.txt` explains Studio's actual
Related video field; nothing publishes or edits a YouTube upload.
