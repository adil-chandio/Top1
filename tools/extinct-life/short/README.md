# Atlantic Tracks — Short 01

**Why Dinosaur Footprints Can Fool You** · 34.000 seconds · 1080 × 1920 · 30 fps · English · owner review, unpublished. This is one original portrait film. It does not crop or reuse frames, narration takes, titles, or an audio mix from Cinema Edition or Monarch Cam. It uses some of the same source geography, base rock data, typefaces and licensed raw sound library.

| Frame / time | What the picture shows |
| --- | --- |
| 0 / 0.00 s | The foot is already descending. The hook lands on frame 5 (0.167 s). Delayed toe release, damp edge fall and retained grains follow. |
| 82 / 2.73 s | Firm mud: same articulated limb and matched camera. The toe walls stay in place after lift. |
| 169 / 5.63 s | Softer mud: an initial impression and then progressively softer walls as the foot lifts. The camera and initial pose match the firm take. |
| 282 / 9.40 s | A closer angle on the failing left edge. It continues the soft-mud state, rather than resetting the stamp. |
| 365 / 12.17 s | Sousa Basin, Brazil: warm rock and a narrow, angled foot shape. Illustrated, not a specimen scan. |
| 442 / 14.73 s | Koum Basin, Cameroon: slate-toned rock and a broader, differently sculpted track. Illustrated, not a specimen scan. |
| 501 / 16.70 s | Present-day globe. Two independently anchored region markers, ≈6,000 km apart. |
| 574 / 19.13 s | Narration leads the same-view map rewind. Lighting and camera continue; the wipe reveals the separately sourced 125 Ma field. |
| 810 / 27.00 s | An illustrated rock face and sediment layers. Connected land is not a trail. |
| 947 / 31.57 s | Return to the same bank. The question carries over as the foot approaches; frame 1,019 leads into frame 0, not an end card. |

## Research and implementation

- Science follows the [Atlantic Tracks evidence ledger](../step-2/ATLANTIC-TRACKS-EVIDENCE.md): [Jacobs et al. (2024)](https://igeo.ufrj.br/inc/isc/3/03_139_Jacobs%20etal.pdf), [Menkem et al. (2026)](https://doi.org/10.1016/j.jop.2026.100416), and [Carvalho, Borghi & Leonardi (2013)](https://doi.org/10.1016/j.cretres.2013.04.004). The fossil plates are distinct original stand-ins, not photographs, identified specimens, or a claim of a shared animal/species. [Falkingham & Gatesy (2014)](https://doi.org/10.1073/pnas.1416252111) is a useful independent reference for how entry, sub-surface motion and withdrawal leave different features in a track. The demo is not a calibrated material experiment or a reconstruction of those authors' data.
- `portrait.hpp`, `sediment.hpp`, `world.hpp`, `render.cpp`: perspective/visibility, a welded 52,042-vertex foot, differential toe curl and heel roll, contact shadows, 3D grains and deformable heightfields. The two beds take the same pose. Soft relaxation is a pairwise, area-weighted flow on a non-uniform mesh, blended into the shot after loading; it is not a full fluid or particle solver. The [Taichi MLS-MPM example](https://github.com/taichi-dev/taichi/blob/215d6d13c1733cb297c4ffebc84f896c5a5576/examples/mpm88.py) informed the decision to keep mass transfer and material appearance separate, but no Taichi code runs here. [Filament](https://github.com/google/filament) is a reference for the bounded GGX/Schlick look; the renderer is local C++/OpenMP. Two generated diffuse swatches supply grain only; scene geometry, articulation, lighting, lens, and render pixels are computed in the renderer.
- Geography: [Kocsis–Scotese PaleoCoastlines](https://doi.org/10.1016/j.earscirev.2020.103463), [Scotese–Wright PaleoDEMs v2](https://doi.org/10.5281/zenodo.5460860) (CC BY 4.0, adapted), Natural Earth/NOAA ETOPO5 (public domain). Source pins in `world.json` are projected from two independently sourced epochs onto the same 3D sphere and continuous camera. The wipe is not a simulated motion of continents, and its label is not a footprint date. The model produces regional separations of ~6,085 km today and ~1,194 km in the snapshot, neither a route length. No line joins the two places. [Design-in-Product/globe](https://github.com/Design-in-Product/globe) was a camera/mapping reference, not an asset or runtime dependency.
- Editorial reference: [Monarch Cam portrait rebuild](../../monarch-ant-v3/short-v2/README.md), [Foley](../../monarch-ant-v3/short-foley/README.md) and [voice/launch](../../monarch-ant-v3/short-voice/README.md). Takeaways: action first, hard cause/effect comparison, tactile sync, mobile-size type and a motion seam. `mix.py` aligns the fresh takes without time-stretching, level-matches takes, and gives voice space over the shaped scene beds and Foley. The speaker and isolated English SRT are locked to the same edit clock. The paste sheet lists actual-use credits and the optional Studio Related Video setup once the long film is eligible.

## Review completed

- Ran a **4.03 s original matched-view proof** first, watching the footing, lift and edge slump in 540 × 960 contact sequences. Then checked framing, illustration labels and the replay at phone scale. The final source is supersampled from 1152 × 2048; all 1,020 output frames decoded, and 33 specific frames were extracted at 360 × 640. Opening visual and sound seam checked against nearby frames and audio samples. No logo, spoken CTA, blank intro, fabricated route or separate end card.
- 11 frame-pinned Foley accents, 14 word-aligned cues (zero added offset across decoded caption windows); 48 kHz stereo AAC-LC, −17.5 LUFS-I, −2.0 dBTP. The phone-band check led to additional voice-keyed attenuation in the bed; the final AAC passed with unchanged encoded picture packets. These are signal and visual checks, not a human pronunciation or audience sign-off. Check playback on the intended phone before release.

## Rebuild and output

Python 3.11+, `g++` with C++17 and OpenMP, `gh` for the pinned data sources, and the pinned requirements here. `prepare.py` reuses present locked inputs and rebuilds missing GEO8 inputs without replacing existing Cinema fields. Supply the private approved WAVs and diffuse swatches via `--originals` if not present in `deliverables/private-production-records/atlantic-tracks-short-01/`; `inputs.json` records the required digests, not links or media. No media or packages are checked into Git.

```sh
SHORT=tools/extinct-life/short
python3 -m pip install --target .cache/atlantic-short/python -r "$SHORT/requirements.txt"
export PYTHONPATH="$PWD/.cache/atlantic-short/python" PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python3 "$SHORT/prepare.py"
python3 "$SHORT/mix.py"
python3 "$SHORT/build.py" --proof
python3 "$SHORT/build.py"
python3 "$SHORT/verify.py"
```

The three release artifacts are `deliverables/extinct-life-short-01/Atlantic-Tracks-Short-01.mp4`, `Atlantic-Tracks-Short-01.en.srt` and `Atlantic-Tracks-Short-01-Studio.txt`. `verify.py --verify-only` checks completed artifacts; detailed transient, frame, science, layout and byte-lock results live in `.cache/atlantic-short/qa/verified.json`. `reconform.py` is only needed if replacing a mix in an unpromoted export; it requires the exact video packet hash to stay fixed. Drive delivery belongs in **Monarch Extinct Channel / Atlantic Tracks - Short 01**, separate from the Cinema Edition movie and its packaging. The build has no upload, permissions or publication code.
