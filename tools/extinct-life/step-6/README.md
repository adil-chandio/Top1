# Atlantic Tracks — full cinematic cut

**Why These Dinosaur Footprints Are an Ocean Apart** uses the locked eight-section English narration and all 127 of its original cues. The owner replaced the first-minute limit with a full-film brief. This cut does not use the rejected Step 4 pictures, nor does it change either Step 5 opening review. The complete timeline is **10,696 frames (07:25.667 at 24 fps)**, including a 6.5 s end credit after the **07:19.138** WAV. No publicity or sharing changes are part of the build.

## Sound redesign (current review)

The first full delivery passed technical checks, but the owner rejected the soundtrack because the effects were barely perceptible. The new full-duration mix uses recorded water, wind, and contact Foley, distinct dry and wet impacts and releases, a layered rock slide and fault drop, and moving map transitions. A quieter, selectively ducked score leaves room for those actions. It is a sound-only review revision, not a rerelease or a replacement of the archived exports.

Restore the locked Step 3 WAV, SRT and timing sheet, plus the **original** `deliverables/extinct-life-step-6/Extinct-Life-Atlantic-Tracks-Cinematic-Full.mp4` from the Drive receipt below. With the Python environment in the original build section set up, run:

```sh
stage=tools/extinct-life/step-6
python3 "$stage/sound_v2.py"
python3 "$stage/finish_sound_v2.py"
```

- `sound_v2.py` fetches and checks the recordings and credit documents in [`sound-v2-sources.json`](sound-v2-sources.json). The lined-up integer stereo overlay is the only signal added to the unchanged dry VO. Intermediate audio and QA live under `film/sound-v2/` in the cache. The original `film/mix/`, if present, is read only for comparison.
- `finish_sound_v2.py` uses the original MP4 as the picture lock. It copies AVC and timed text and retains the chapter marks. It checks the actual sample data, B-frame offsets and keyframes, full decode, subtitle round-trip, exact dry VO recovery, narration lag after AAC, and a bandwidth-limited mono comparison of the two actual delivered soundtracks. No render plates or shot rebuilds are needed. `--verify-only` repeats these checks without remuxing.
- The separate review package is `Extinct-Life-Atlantic-Tracks-Cinematic-Full-Sound-Redesign{.mp4,.en.srt,-Handoff.md}` in `deliverables/extinct-life-step-6/`. The handoff has timecodes for listening and names each recordist and license, also embedded as credits in the MP4. [Redesign verification](sound-v2-receipt.json). Numerical checks are not an owner listening signoff.

## Original cut inputs and rebuild

Restore the WAV, SRT and timing sheet from the [locked Step 3 handoff](../step-3/vo-v2-receipt.json) under `deliverables/extinct-life-step-3/`. `assets.py` checks sizes/hashes before preparing any assets. It retrieves only pinned open map, font and gravel foley sources; every local fossil/rock shape and material is generated for the film. It does not use the image-rights research as an image library. Builds require Python 3.11+, `g++` with OpenMP and `gh` for fetching pinned sources. From the repository root:

```sh
python3 -m pip install --target .cache/film-python \
  numpy==2.2.6 scipy==1.15.3 Pillow==11.3.0 imageio-ffmpeg==0.6.0 pyshp==2.3.1
export PYTHONPATH="$PWD/.cache/film-python" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
stage=tools/extinct-life/step-6
python3 "$stage/assets.py"
python3 "$stage/film_picture.py" --compile --open-plates --tools-only
python3 "$stage/film_picture.py"
python3 "$stage/film_audio.py"
python3 "$stage/finish_film.py"
```

- `cut.py` specifies all shots, markers and spots. A picture frame is exactly 2,000 PCM samples at 48 kHz. `film_picture.py --from 20 --to 21 --redo` replaces just those zero-indexed shots; normal runs skip complete parts and regenerate the concat manifest when all 66 are present. Re-run with `--redo` (or a fresh picture cache) when changing shots/materials; do not combine revisions by relying on cache presence.
- `pilot.cpp` generates new clean plates from the opening CGI renderer and Step 6 materials, not from either prior export. Body rasterizer/rigs are `render_film.cpp`, `raster.hpp`, `sets.hpp`, `feature.hpp`. Body shots are rendered at 1024×576 with native depth, then Lanczos-scaled for a 1920×1080 limited-Rec.709 encode. Opening plates range from 960×540 to 1152×648. The visual approach distinguishes terrain from evidence cutaways and avoids using a mapped path to suggest that any one dinosaur travelled between the two sites.
- Only 33 kinetic editorial entries (title, place names, counts and selected terms) are composited into pixels. The exact English SRT is embedded as a **separate** track and delivered as a sidecar. Many players have a subtitle menu; for those which do not read MP4 text tracks, use the sidecar.
- `film_audio.py` builds an original continuous stereo motif, separate location ambience with lead/tail overlaps, and 77 timed spots. It uses four pinned CC0 Kenney gravel cues, original procedural water/soil/stone layers and gentle stereo crossfeed. The dry mono channel is duplicated at unity, unchanged, and a 24-bit quantized bed is added. No pitch changes, time stretch, intermediate AAC or mix-wide limiting. Foley is illustrative; spatial placement is stereo, not a binaural measurement.
- `finish_film.py` joins the H.264 parts without recompression, adds the stereo mix, explicit chapter markers and selectable EN subtitles, and verifies the **actual** MP4. It inspects exact clocks and composition offsets, tests full decode, checks all cues against the original script and against the demuxed track, proves dry-voice identity before AAC and zero-lag windows after, and compares each first-visible text event to its omission reference. `--verify-only` repeats QA on the delivered file. The [receipt](full-film-receipt.json) is the record of numeric results; it is not a claim of creative approval or a human pronunciation check.

Render plates, decoded proofs, mix stems and field data are under `.cache/monarch-extinct/atlantic-tracks/film/`. Shareable `Extinct-Life-Atlantic-Tracks-Cinematic-Full.mp4`, `.en.srt` and `-Handoff.md` are in `deliverables/extinct-life-step-6/`. Do not commit generated media. Use the handoff and receipt for source attribution. The **125 Ma** slice is not a footprint age, the **~69 cm** value is one print not an animal measurement, and the Mawsonia scene does not place that fish at the footprint sites. Listen to **Sousa** in the passage at 03:34–03:39 before release.

## Delivered files

**Current picture review:** [Investigation Cut](../step-7/README.md#delivered-review) is the separate full-film picture recut. It stream-copies the Sound Redesign AAC, English timed text and chapters; it does not overwrite either Step 6 file.

**Sound Redesign / audio lock:** Full Sound Redesign MP4 · identical English SRT. The MP4 is verified in the existing `3d animation` folder. The revised notes and separately named SRT are also in the local deliverables; their extra Drive uploads were rate-limited. See the [redesign Drive receipt](sound-v2-drive-handoff.json).

**Archived original (use as the picture lock, not as the latest mix):** Full MP4 · Original handoff · [original Drive receipt](drive-handoff.json).
