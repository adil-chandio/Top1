# Monarch Cam #1A · YouTube packaging

This builds the upload kit for the accepted 299.80-second V3 film. It does not
upload, schedule, publish or run a title test. `copy-spec.json` stores the
editorial decisions and source references. The chapter times are derived from
the V3 frame anchors, including a split at the 117-trial discussion. The upload
text attributes the film's research, original score samples, Foley and type.

## Rebuild with the selected art

Use Python 3.11+ and Pillow 11.3.0. Put the selected nearly-16:9 art in
`.cache/monarch-ant-packaging/selected-cover-art.png`. This is an external art
input, not committed to Git. Restore `SpaceGrotesk.ttf` and
`SpaceGrotesk-OFL.txt` to `.cache/monarch-ant-packaging/fonts/` from
`google/fonts@5bd87dfc525c8a0d1d8529d3684716e00c3fc59a`,
`ofl/spacegrotesk/SpaceGrotesk[wght].ttf` and `ofl/spacegrotesk/OFL.txt`.
The builder verifies both file hashes. Use `--art`, `--fonts`, `--out` and
`--qa` to point to alternate paths if the deliverable has moved.

```sh
python3 -B tools/monarch-ant-v3/packaging/build.py
```

It makes the final sRGB 16:9 JPEG below 2 MB, the plain-text Studio paste
sheet, JSON metadata, launch guide and ZIP in
`deliverables/monarch-cam-step-5-packaging/`. Inspect the JPEG and its 480, 320,
176 and 120-pixel visual mockups in `.cache/monarch-ant-packaging/qa/`. The
mocked runtime badges are QA-only, not baked into the real thumbnail. The
receipt records the source raster and the output raster separately. Contrast
numbers are pixel-based checks, not audience or predicted CTR measurements.
