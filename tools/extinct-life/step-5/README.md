# Atlantic Tracks — first-minute 3D approval cut

**Current review:** [Cinematic v2 build and verification](cinema-v2/README.md). This page also documents the preserved original 3D approval cut and its source inputs.

**Scope:** an authored 60.708 s 3D sequence for *Why These Dinosaur Footprints Are an Ocean Apart*. No later picture work, release or picture lock. The rejected Step 4 animatic is not a picture source. The locked Step 3 English v2 audio (audition `02`) and first 18 canonical English cues begin at zero. The edit stops just after “on that patch of ground,” before the next sentence. It does not trim or stretch any spoken phrase. The mixed dry track is sample-identical through the cut at unity after subtracting the stereo bed.

## What is rendered

- `prepare_terrain.py` turns pinned height/coast data into two different georeferenced fields. The Earth has the same radius and camera optics through the rewind. An animated plane sweeps through the curved model, with a projected graticule at the seam. These are separate present and **125 Ma model snapshots**, not a purported view of the age of either set of prints or a modeled history between those dates. The paths of the two site pins use the checked regional coordinates. The two dashed brackets show approximate **regional separation** (~6,000/~1,000 km in the study), not a proposed path on a map.
- `render3d.cpp` ray-casts the relief, terrain, local depressions, four rock horizons, reflective water plane and articulated contact rig. Surface lighting and shadows use world normals and the actual terrain. Cameras and printed marks are in the same coordinates as the set. Local geometry is explanatory and not traced from field or journal figures. The contrasting material textures are generated albedo, not photo backplates.
- `picture.py` composites titles, tracked dimensional pins, projected bracket annotations, depth mattes and typography over the render. Per-shot native sizes are 1920×1080 for maps, 1536×864 for the opening close views and 1280×720 for the other local scenes, composited into the 1080p review. No Adobe project is needed; the tracked overlays and edit live with the geometry here. Proof boards are for QA, not the requested deliverable.
- `finish.py` adds the original procedural score/FX under the unchanged dry VO, preserves whole captions, and muxes the exact 24 fps packet clock with English CC. `verify_opening.py` inspects the MP4 boxes, decodes the full cut, checks sync and captions, and records the receipt while making encoded-playback stills to inspect.

## Re-create in the workspace

Use Python 3.11+, Pillow with variable-font support, NumPy, SciPy, pyshp and imageio-ffmpeg 0.6.0, and a C++17 compiler with OpenMP (tested with GCC 12.2). No graphics device, browser or app service. In this sandbox the Python packages are available from `.cache/monarch-ant-short-voice/python` and `.cache/monarch-extinct/atlantic-tracks/python` on `PYTHONPATH`. Use `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=2` on this two-vCPU sandbox.

1. Restore the two albedo JPGs under `deliverables/extinct-life-step-5/source-materials/` (checksums in `pilot-assets.json`). Preserve the original three v2 VO deliveries in `deliverables/extinct-life-step-3/` (hashes in `../step-3/vo-v2-receipt.json`). A new synthesis is not a substitute.
2. For the picture data, `prepare_terrain.py --fetch` uses `gh api` raw blobs if the three pinned geodata sources and two map-lock inputs are absent. With them already in cache, omit `--fetch`. To restore the exact Fraunces/Plex Sans/Plex Mono binaries, use `../step-4/asset-lock.json` and its `google/fonts` ref; put the binaries in `.cache/monarch-extinct/atlantic-tracks/animatic/fonts/` with their OFL notices.

```sh
python3 tools/extinct-life/step-5/prepare_terrain.py
python3 tools/extinct-life/step-5/picture.py --proof  # optional still QA
python3 tools/extinct-life/step-5/picture.py          # all 12 shots; several minutes
python3 tools/extinct-life/step-5/finish.py
python3 tools/extinct-life/step-5/verify_opening.py
```

Delivery: `deliverables/extinct-life-step-5/Extinct-Life-Atlantic-Tracks-Opening-3D.mp4`, its English `.srt` sidecar and review notes. Packed grids, raw encodes, synth mix stems, projected traces and proofs stay in the cache. No generated datasets or exports in Git.

## Attribution

- **Ancient coastline and rotations:** Ádám T. Kocsis and Christopher R. Scotese, *Mapping paleocoastlines and continental flooding during the Phanerozoic* (2021), [doi:10.1016/j.earscirev.2020.103463](https://doi.org/10.1016/j.earscirev.2020.103463). PaleoCoastlines v7.1 125 Ma coastline, v19o_r1c plate rotations. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Resampled, recoloured, projected and annotated. Details / pin sources: `../step-2/map-sources.json` and `../step-2/ATLANTIC-TRACKS-EVIDENCE.md`.
- **Ancient height:** Christopher R. Scotese and Nicky Wright (2018), [PALEOMAP PaleoDEMs v2](https://doi.org/10.5281/zenodo.5460860), 125 Ma, CC BY 4.0. Sampled from the pinned `serroba/histeclipse` 8-bit mirror, resampled, lit and vertically exaggerated.
- **Modern:** 1:50m [Natural Earth v5.1.2](https://www.naturalearthdata.com/about/terms-of-use/) land polygons and NOAA NGDC [ETOPO5 (1988)](https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO5/TOPO/ETOPO5/ETOPO5.DAT) from the pinned `voxiverse/voxiverse` repacked version. Public domain. Relief vertically exaggerated.
- **Fonts:** Fraunces and IBM Plex, SIL OFL 1.1. **Other:** generated rock albedo; original geometry, pictures and synthesized audio. No prior-film footage, licensed journal imagery, media-release stills or stock music are used.
