# Atlantic Tracks: voice-led animatic

This is the first review cut for **Why These Dinosaur Footprints Are an Ocean Apart**. It uses the byte-pinned v2 voiceover and English SRT from Step 3 at timeline zero. It is not final CGI, picture lock, or a release file. No sound effects or score were added. For edit notes and attributions, see `Extinct-Life-Atlantic-Tracks-Animatic-v1-Shot-Handoff.md` next to the MP4.

- `timeline.py`: picture beats from the measured v2 voice and its word-aligned cue sheet. Cut positions round to the nearest frame at 24 fps. Within-shot reveals (contrast, numbers, labels) are keyed in `render_animatic.py` and `artwork.py`.
- `artwork.py`: original illustration and schematic renderer. The two geographical plates use the same equirectangular scale and pinned, licensed sources. Unlike the cartography, the schematic rocks, prints, fish, habitat and time diagrams are not specimen data.
- `asset-lock.json`: hashes for the three original generated landscape plates and three SIL OFL font binaries. Fonts can be restored from the pinned `google/fonts` commit using GitHub contents or raw blobs. No generated art is in Git. The chosen illustration bytes are stored under `deliverables/extinct-life-step-4/illustration-sources/` (not on Drive as extra files). The geography is pinned in `../step-2/map-sources.json`.
- `verify_animatic.py`: verifies the actual MP4—exact 24 fps packet clock, seekable shot starts, frame decode, AAC alignment to PCM, and complete SRT round trip. `animatic-v1-receipt.json` records export outputs and checksums.

## Build

With Python 3.11+, Pillow, numpy, scipy, pyshp and imageio-ffmpeg installed, use:

```sh
python3 tools/extinct-life/step-4/render_animatic.py --proof
python3 tools/extinct-life/step-4/render_animatic.py
python3 tools/extinct-life/step-4/verify_animatic.py
```

In the working sandbox the dependencies are cached in `.cache/monarch-ant-short-voice/python` and `.cache/monarch-extinct/atlantic-tracks/python` (both on `PYTHONPATH`). Map files and fonts are, by default, under `.cache/monarch-extinct/atlantic-tracks/sources` and `.cache/monarch-extinct/atlantic-tracks/animatic/fonts`. If the sandbox cache is gone, restore the SHA-pinned inputs and pass `--sources`, `--art` or `--fonts`. Copy the original v2 WAV and SRT under `deliverables/extinct-life-step-3/` if not already there. New TTS or newly generated art will not produce the same bytes.

`--proof` stores sample sheets under the animatic cache; these are for QA only. Intermediate shot encodes also live in the cache. Keep screenshots, raw clips and final media out of Git. File only the checked review MP4 and its shot handoff in the existing animation folder. The older VO versions and other channel assets remain untouched.
