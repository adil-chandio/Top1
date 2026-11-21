# Third-party tool intake

The production system should gain capability deliberately, not by copying random
GitHub repositories or downloading unlicensed media. The current candidates below
are **not installed by this foundation**. Repository metadata and pins were
observed on 2026-11-21 UTC. They are reviewed options, pinned to the
observed commit, and must be rechecked before adoption because upstream code and
licenses can change.

| Candidate | Intended role | License | Observed pin | Decision |
| --- | --- | --- | --- | --- |
| [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO) | exchangeable editorial timelines | Apache-2.0 | `f101411e11968d3255488f4aaccf041d965a2148` | evaluate for EDL interchange |
| [OpenImageIO](https://github.com/AcademySoftwareFoundation/OpenImageIO) | image sequence inspection and metadata | Apache-2.0 | `8a21cac9fbab4713b72076f0eaf9fdb0831a72b6` | evaluate for QA only |
| [OpenColorIO](https://github.com/AcademySoftwareFoundation/OpenColorIO) | explicit color-management configuration | BSD-3-Clause | `22dd9c4faa0d1b7cfb3d64d1a6e9cb454acc6cfd` | evaluate before renderer integration |
| [Snakemake](https://github.com/snakemake/snakemake) | resumable project DAGs | MIT | `6d007cf012b0d4dfb80d3a7a21c2cd39bec8f7c8` | evaluate against the existing scripts |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | offline draft transcription/alignment aid | MIT | `5eaee0cc9024eb9e9a99469199920c8b7f5cb9ec` | optional, never final fact source |
| [WhisperX](https://github.com/m-bain/whisperX) | word-level alignment candidate | BSD-2-Clause | `b904f02b7e1f26fd10fb04840d655ff27e88e464` | license/model audit required |
| [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | encoded scene-change QA | BSD-3-Clause | `e51a306ce0d951ca2f2a1e8384c19fc3536f83c4` | evaluate for delivery QA |

## Adoption checklist

Before adding one:

1. Re-fetch the repository metadata and confirm license, commit and security state.
2. Record the exact commit, transitive dependencies, Python/Node/compiler impact,
   and a local hash in a machine-readable manifest.
3. Run it in a sandbox against a tiny synthetic proof, never private media first.
4. Add a test that catches output drift and a removal path if it becomes stale.
5. Keep license notices and model licenses with the delivery record.
6. Do not import clips, music, voices, thumbnails, or other media just because a
   repository links to them. Media rights are a separate gate.

The current native renderer, FFmpeg checks, Pillow/NumPy tools and existing
receipts remain the baseline until a candidate demonstrably fixes a measured
failure.
