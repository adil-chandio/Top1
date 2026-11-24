# Huayuan — current project handoff

## Status

A complete 60-second **experimental review** was rendered and uploaded, not accepted as a finished cinematic film. Multiple animals were restored to view and the approved mixed audio was stream-copied; however preflight and decoded stills showed a sparse synthetic seabed, schematic fossil/evidence, repetitive coverage and a weak crisis. It has not passed a creative review, expert science review, continuous subjective listening or frame-by-frame visual inspection. Do not market it as final, IMAX-certified, expert-validated or a wholly new sound mix.

- [Review video](https://drive.google.com/file/d/1J9fiEEg3XG2dF63BtniG_1MNwX9H_28X/view?usp=drivesdk)
- [Technical proof](https://drive.google.com/file/d/1Dm80wJLryDEF1GV05AHQfqJqnaIabl2Q/view?usp=drivesdk) and [source credits](https://docs.google.com/document/d/1enyAh54POjm22dE5AL9g_FpFf8HGbuae/edit?usp=drivesdk&ouid=101198042089865187058&rtpof=true&sd=true).
- [Project Drive folder](https://drive.google.com/drive/folders/16miPGSr27SfHyV84KThUUh2AhcfZzvP7); access depends on permissions.
- The file's SHA-256, decoded frame count, audio identity and loudness are recorded in `notes/REVIEW-AND-TECHNICAL-PROOF.txt`. Preflight critiques and complete model links are in `notes/`.

## Audio / delivery boundary

The accepted story-review narration was recovered **only as part of an existing stereo mix** with music and sound effects already baked in. Its decoded PCM SHA-256 is `6bb74d9c8645b6e4ea1438ade1a7738d7d69865b013b1b5c2c581f2e30ab9348`; the final file's audio matches it. There is no verified matching dry voice stem. Do not substitute the older dry candidate, retime, stretch, or regenerate the voice without appropriate user approval. A truly independent score/SFX remix cannot be claimed from this combined track. Private audio, video and customer captions are not committed; recover authorized media from Drive if available, and verify hashes. The earlier accepted-voice story source is [here](https://drive.google.com/file/d/1r_CORPZ7Qe0mxkvTPRx9FqC_pSYV-vQM/view?usp=drivesdk).

## Science and rights

[Huayuan study](https://www.nature.com/articles/s41586-025-10030-0) reports a ~512-million-year-old biota, 153 animal species across 16 major groups. A deeper-water refuge is a suggestion, not a proven cause or locally observed event. [Myrow et al.](https://par.nsf.gov/servlets/purl/10520526) discuss possible Cambrian environmental changes; precise causes and local timing are uncertain. Generic Anomalocaris, Opabinia and Hallucigenia models are illustrative and should not be identified as Huayuan fossil specimens. Check all claims and current primary sources before release. Model attributions and licensing are in `notes/SOURCE-AND-RECOVERY.md`; reuse requires following those terms.

## Run the archived scene (not a new approved final)

From the repository root on a suitably provisioned Linux runtime:

```bash
bash tools/monarch-v6-imax-sdk/bootstrap_v6_runtime.sh
node tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs \
  --page /tools/extinct-channel/projects/huayuan/film.html --mode preflight \
  --w 1280 --h 720 --frames 1800 --build-dir /tmp/huayuan-channel-build \
  --export-dir exports/extinct-channel-huayuan/preflight
node --test tools/extinct-channel/tests/project.test.mjs
```

The SDK and scene reference `/tmp/v6_runtime`, `/tmp/chromium`, and `/tmp/sparticuz_libs`; a fresh environment needs the bootstrap. It uses SwiftShader where hardware is unavailable and a full render can be slow; timing is hardware-dependent. The preflight generates stills only and does not include the mixed audio. The old `prototype.html` and `lookdev.js` are retained as failed look-development history, not a recommended final pipeline.

If a new audiovisual task is authorized, investigate the critique first; do not silently treat this old scene as the required creative standard. Follow the repository's production process, preserve voice identity, inspect the actual decoded result and disclose any unfinished quality gate.
