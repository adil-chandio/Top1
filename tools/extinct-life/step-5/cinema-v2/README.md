# Atlantic Tracks — cinematic opening v2

This is the revised **first-minute approval cut**, not finished episode picture. The prior 3D review remains a separate export. No frames of the rejected Step 4 animatic or reference films are used. Same 1,457-frame edit, locked English narration and 18 canonical captions as the v1 3D review. The end follows “on that patch of ground.” Playback-check the pronunciation of Sousa before a release; automated timing is not pronunciation approval.

## Build order

Run from the repo root with Python 3.11+, NumPy, SciPy, Pillow (variable-font support), pyshp, imageio-ffmpeg 0.6.0, GCC with OpenMP, and about 9 GB of scratch space. See [the Step 5 setup](../README.md) for the workspace Python environment, three locked VO files, two generated albedos and fonts. The optional `--fetch` takes pinned geodata from GitHub. No GPU or graphics application required.

Place the four original RPG Audio gravel samples in `deliverables/extinct-life-step-5/source-materials/kenney-rpg/`; each is checksum-checked by `sound.py`. **Kenney Vleugels, CC0 1.0.** Source mirror: [`evanlin23/blocky-stories` at `328f356539d059f360175b66f3a88b2ba78e7c91`](https://github.com/evanlin23/blocky-stories/tree/328f356539d059f360175b66f3a88b2ba78e7c91/assets/audio/steps/gravel), `gravel_{02,05,07,08}.wav`. License in the same revision at `assets/licenses/kenney_rpg-audio_License.txt`. All score, tonal effects, wind and water layers are original synthesis; no mixed soundtrack or stock music reused.

```sh
C2=tools/extinct-life/step-5/cinema-v2
python3 "$C2/geometry.py" --prepare       # add --fetch to restore the pinned geodata
python3 "$C2/geometry.py" --proof         # optional native stills
python3 "$C2/geometry.py"                 # render 12 clean plates and projection traces
python3 "$C2/motion.py" --proof           # optional composited stills
python3 "$C2/motion.py"                   # grade, type, overlays and 12 encodes
python3 "$C2/review.py" --mix             # rebuild the mix, mux, and run final QA
```

Outputs in `deliverables/extinct-life-step-5/`: `Extinct-Life-Atlantic-Tracks-Opening-3D-v2.mp4`, `.en.srt` and `-Review-Notes.md`. Encodes, RGBA/depth mattes, traces, proof sheets and mix stems stay in `.cache/monarch-extinct/atlantic-tracks/pilot-3d/cinema-v2/`. `opening-3d-v2-receipt.json` is the lightweight audit.

## How to revise

- `cues.py` owns the 24 fps/48 kHz clock. `geometry.py` passes the rewind and contact/release frames to the native renderer. `motion.py` and `sound.py` both consume these event definitions. An offset in an anticipatory sound is not an offset in the matching text transient.
- `geometry.py` builds signed macro tracks, separate geological shelves, valley fields and relief maps. `render_cinema.cpp` lights and shades those sets, projects the pins/track markers, and depth-tests drifting dust, contact grit and riverbank details. The two globe snapshots use different source models and are editorially swept, not interpolated in time. Regional brackets depict separation. Only local sample steps use direction arrows. See [attribution and science boundaries](../README.md).
- `motion.py` tracks the in-scene marks. In screen space, separate masks build headlines, key numbers and their accompanying rules. `sound.py` spots a transient for those reveals and handles the independent score, atmosphere, transitions and physical effects. It automates only the non-narration buses, not the voice.
- `review.py` compares first-visible cue frames in the encoded MP4 against comp references with and without that layer. It timestamps the actual sound attacks against these frames on the same clock, validates the captions and AAC priming, and verifies exact dry-voice recovery before AAC. Full-frame tech checks are distinct from the owner's picture/mix approval.
