# Historical production restart, provenance, and audio recovery

**Historical note:** this document records the state before the later full 60-second review was rendered. For the current status and decoded verification, see `REVIEW-AND-TECHNICAL-PROOF.txt` and `../PROJECT-STATUS.md`.

The prior turn's untracked working files (including the most recent dry voice WAV and full scene code) were absent when this workspace started. The accepted 60-second narration was recovered only **inside the prior story-review MP4**, downloaded from the user's Drive folder. Its MP4 SHA-256 is `bd641006ed2515807b46ba7e8f3aee7b6042dc97193f95412e119247a7d56a97`.

`tools/huayuan-recovery/approved-voice-with-old-mix.m4a` is a lossless stream copy of that MP4's stereo AAC track (60 s, 48 kHz). Decoded PCM SHA-256 for both tracks: `6bb74d9c8645b6e4ea1438ade1a7738d7d69865b013b1b5c2c581f2e30ab9348`. **It is not an isolated narration stem:** old music and sound effects are baked in. The recovered separate `Huayuan-dry-voice-locked.wav` belongs to an older, different narration script, not the subsequently accepted narration; never substitute it without approval. No time-stretch was applied during recovery, but the original dry WAV/sample-level test source is missing and cannot be verified from the mixed track. To create a genuinely new sound mix, recover the correct dry voice if available, or clearly disclose the limitation before using a separation process. The old full video is not reused as a production visual template.

The preflight is a **look-development experiment only**, and has failed creative review twice as recorded in LOOKDEV-CRITIQUE.md. The full film, 2–3-second crisis sequence, film edit, new sound mix, continuous watch/listening and decoded-film QA have not been produced. V6 SDK was restored from the fetched `origin/main` commit `64749ac4a5e3c3f80fe0d9e93b5077b58e8a126f` without merging over the branch, and its README was not modified.

## Assets in the experimental lookdev

- `radiodont.glb`: modified Anomalocaris 3D Model by Skache, CC BY 4.0, https://sketchfab.com/3d-models/anomalocaris-3d-model-dad76e60589a41e18a42db1e979f81f8 ; rigged derivative from https://github.com/chengong201/prehistoric-animal-museum ; SHA-256 `147de95a18c771739f918e8ce0319c00fba560d6f415305f57fddc97b96f661a`. This is a generic Cambrian reconstruction, not a Huayuan specimen. Already used in rejected cuts.
- `coast_rocks_01.glb` and `coast_rocks_03.glb`: Coast Rocks 01 and 03, Rob Tuytel and Rico Cilliers, CC0, https://polyhaven.com/a/coast_rocks_01 and https://polyhaven.com/a/coast_rocks_03 ; compressed derivatives from https://github.com/2600th/web-ocean-3d, per its ASSET_LICENSES.md. Modern geology is used only as visual material, not Huayuan evidence.
- `rock_07.glb`: Rock 07, Jenelle van Heerden, CC0, https://polyhaven.com/a/rock_07 ; optimized derivative from the same source repository.
- No endorsement by any original creator is implied. Final-specific credits must be reviewed for actual assets used.

## Additional models in full-scene prototype

- `opabinia.glb`: Opabinia by billionlioe, CC BY 4.0, https://sketchfab.com/models/d2111e360cdc4243aac23871836c49f5 ; modified rigged derivative from https://github.com/chengong201/prehistoric-animal-museum ; SHA-256 `fb511c5c844507782e3a686ab0afedeb1b7792fd0b3301050e95d37a65ca0b62`.
- `hallucigenia.glb`: Hallucigenia Cambrian Animal by huykhoi2407, CC BY 4.0, https://sketchfab.com/3d-models/hallucigenia-cambrian-animal-fad8306e863a4960b48e49c16c3806cf ; modified rigged derivative from the same repository; SHA-256 `2f1c725ab3410bc0b650ee442d7028555e63b51288fb8a6531997941dc8daa1e`.
- These generic animals are illustrative, not identifications of Huayuan fossil species.  https://creativecommons.org/licenses/by/4.0/
