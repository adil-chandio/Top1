# Monarch Cam · V3 opening and full feature

The first **23.60 s** of *This Ant Bites the Ground to Escape*. 11 native takes on the locked V2 opening clock. This pilot is a separate review artifact, not a whole-film export. No V2 files are inputs to the picture encoder; the existing 3D primitives/character assets, V2 VO placements and audio banks are reused. Source is a native renderer/custom comp, not an After Effects project.

## Build

From the repo root, use the environment in [V2's README](../monarch-ant-v2/README.md) for Python (NumPy, Pillow), an EGL/GLES3 runtime and FFmpeg (`FFMPEG`). Set `MONARCH_EGL` to the pinned SwiftShader/ANGLE runtime directory. Set `MONARCH_V3_CACHE` (default `.cache/monarch-ant-v3`) if you want a separate scratch tree; full HD RGBA plates take ~5.9 GB of disk, plus space for temporarily replacing a render piece. No cached animated plates ship in Git.

V3's `assets/` needs `dune-quartz.png` and `forest-bokeh.png` (from the pilot's `source-assets`), and the two TTFs and OFL notices in `assets/fonts/`. See the pinned paths and SHA-256 fingerprints in `source-assets/sources.json`. Get the two font files from those revisions of `google/fonts`, save each as its `name`, and retain the original notices. `titles.py` verifies bytes before compositing. The assets packer also reads V2's `chitin-micro.png` in its existing asset cache. Recover the original V2 audio banks with `tools/monarch-ant-v2/audio_sources.py --fetch` as needed (see V2 notes). Keep `MONARCH_VO_WAV` pointing to the locked full VO master and V2 `work/film-v2.json` intact.

```sh
python3 -B tools/monarch-ant-v3/assets.py
# Full native render. Optional args 0..3 regenerate only those pieces.
tools/monarch-ant-v3/native.sh
python3 -B tools/monarch-ant-v3/pilot_mix.py
python3 -B tools/monarch-ant-v3/finish.py
python3 -B tools/monarch-ant-v3/delivery.py
```

`finish.py --board 109,173,233,234,441,442,509,551,682` checks stills without an encode; `--clean` skips titles. `delivery.py` does a complete decode, CFR/sample count verification, active VO comparison, first-strike check and exact geometry/optical constraints before staging the MP4 plus notes and optional English SRT. Caption word timings are tied to the selected voice, not inferred from the edited typography. Default delivery is `deliverables/monarch-cam-step-4-v3/`.

## Editorial marks (30 fps)

- 0–193: leg effort then sand shear, fixed reference marker, directional typographic accents. At 194, camera drops with the rolling grain.
- 227–240: physical foreground pincer passes across the lens; cut at frame 234 under the occlusion. A sand tail, not a loud transition effect, crosses it.
- 383–483: planted legs, head aim, jaws sweep; contact at f441 then first lift at f442. No graphic between the moving jaws and the ground.
- 484–523: land/air geography of the pit, rim clearing and the touchdown f519. The shot remains wide to show where the ant ends up.
- 524–587: projection-driven jaw sweep guides and the word INWARD. The trajectory annotation is a motion guide, not a force arrow.
- 588–707: question from the rim to the overhead bowl. Last clean frame can carry directly into the next chapter.

This uses staging and a retimed illustrative model, not field or lab footage, a CT reconstruction or a trajectory measurement. Credits and review points are in the delivery's TXT.

## Full V3 · 04:59.80

`feature_cut.py` keeps the seven narration placements and the approved first 708
pictures. It makes a 90-entry editorial plan for the full 8,994-frame edit.
Every continuation frame is evaluated in the V3 world, with no V2 footage or
frame interpolation. Macro contact views use the rich shader and moving shadows;
wide coverage uses a lower-cost soft contact pass with the same palette and lens
positions. The post-opening native raster is 1280×720; the MP4 is 1920×1080.

The separate V3 delivery folder is `deliverables/monarch-cam-step-4-v3-full/`
(`MONARCH_FEATURE_DELIVERY` overrides it). Set `MONARCH_V3_DELIVERY` to the
folder holding the approved opener if relocated. Its MP4 is pinned by SHA-256,
and its PCM mix is consumed from the pilot's work cache. Also required:
`liblz4` (system shared library), V2's `work/film-v2.json`, the locked WAV and
Step 2 script, and the Step 3 timing receipts (`MONARCH_VO_EDIT_DIR`, default
`.cache/monarch-cam-ant-vo-v1`). The SRT is optional and separate from the video.

```sh
# Start with the verified opening build and V2 audio/texture banks in place.
python3 -B tools/monarch-ant-v3/feature_cut.py
# Takes are restartable. Optional positionals are chapter numbers from 2 to 7.
tools/monarch-ant-v3/feature_native.sh
C=${MONARCH_V3_CACHE:-.cache/monarch-ant-v3}/feature
"$C/work/studio-render" --feature 1 --width 1280 --height 720 \
  --plan "$C/work/feature.plan" --first 708 --marks "$C/work/projection.csv"
python3 -B tools/monarch-ant-v3/feature_words.py
python3 -B tools/monarch-ant-v3/feature_mix.py
python3 -B tools/monarch-ant-v3/feature_finish.py 2 3 4 5 6 7 --mux
python3 -B tools/monarch-ant-v3/feature_delivery.py
# Inspect the encoded boards in "$C/qa" before promotion.
python3 -B tools/monarch-ant-v3/feature_delivery.py --promote
# Optional: create a lighter full-length Drive review when the master exceeds 100 MB.
python3 -B tools/monarch-ant-v3/feature_review.py
```

The `.plates` scratch packets are lossless RGBA with a matte used for selective
occlusion, not ordinary footage. Expect several GB of scratch rather than a full
raw sequence. For a geometry retake regenerate affected `take-*.plates` with
`FEATURE_FORCE=1 FEATURE_ONLY=3462,6478` (matching take starts and chapter args),
then rebuild projection and re-run the chapter compositor. For an asset or shader
change regenerate all affected native takes; `feature_native.sh` won't silently
replace a finished plate. The composite fingerprints include the scene list,
projection, compositor and plate metadata; they reject stale mux inputs. Get
pre-encode inspection boards with `feature_finish.py --board 4297,4298,5325`.

The finalized QA checks the locked PCM at the join, decoded opener equality,
complete Rec.709 CFR clocks, dialogue correlation, selected onset positions, and
frame-level rig traces. The extra cuts distinguish a jaw's closure time from
body flight and report observed trial outcomes separately from the handled-cohort
experiment. Model motion, its time scale, and the cutaway are illustrative; use
the feature's credits/science TXT for the cited study denominators.
