# Batch 3 — narration and handoff checkpoint

## Completed this continuation

- Generated revised English voice with the voice selected in the current audition; 3 segments, total 60.80 s. User selection of the audition is not approval of the complete narration. WAV SHA and per-clip measured durations are in `NARRATION_V2_RECEIPT.json`. Audio source stored in the existing Drive production folder: https://drive.google.com/file/d/11MW2AqMDrAoSPoBQcg-S7XYFPTjf_lAu/view . Upload SHA matched local SHA.
- Produced `CAPTIONS_V2_ALIGNED_DRAFT.srt` and `ALIGNMENT_V2.json` using PocketSphinx transcript-constrained alignment independently for each of the three generated clips, 16 kHz analysis copies, and manual pronunciation dictionary entries for Tokay, setae, van der Waals, hyperextension and possessive gecko's. The script is `align_narration.py`; install `pocketsphinx` separately and supply FFmpeg. Input is the expected transcript: this does **not** prove what was spoken or whether the pronunciations are correct. Word and cue times remain estimates, not verified playback sync; listening against the audio is necessary before publishing. `CAPTIONS_V2_ESTIMATED.srt` remains an earlier character-weighted draft.
- Signal checks: FFmpeg decoded the 60.80 s mono 24 kHz WAV; mean −19.0 dBFS and peak −1.5 dBFS (sample peak). The 20.32 s and 41.04 s joins fall inside detected silence using −45 dB / 0.12 s settings. Signal analysis does not replace listening; neither prosody nor seam quality was heard.

## Approximate edit anchors from alignment

Use as editing guidance, not exact phonetic timing: hook 0.26–4.97, control 5.48–10.11, setae/contact 10.79–19.97, no suction and forces 20.56–27.42, direction 27.42–33.97, toe release 34.40–40.70, hyperextension/angle distinction 41.32–48.68, final payoff 49.26–60.50. Total file duration 60.80 s. The alignment may drift, especially around technical words and the transition at 27.42 s; retime after listening.

## Gate and carry-forward

The script, source map, shot plan and initial selected-voice recording are available; Batch 3 remains **not fully passed** because actual pronunciation, wording and natural joined delivery have not been independently heard/verified, nor have captions been checked against playback. Batch 2 was skipped at the user's direction, not passed: believable animated animal/foot, contact depiction, the actual viral reference benchmark and commercial rights remain open for Batch 4. Existing cartoon concepts do not meet the reference. Batch 4 production and Batch 5 final audiovisual checks are not complete. No publication or paid expenditure is authorized.

## Independent recognition diagnostic

Default PocketSphinx language-model decoding was also run on a 16 kHz conversion of the complete narration. It made many clear recognition errors (for example “Tokay gecko's toes” became “okay gecko stones”; “setae” became “seem to”). It rendered the opening as “a gecko can't hold on to a wall” instead of scripted “can,” and the suction sentence as “the arts suction cups” instead of “they aren't suction cups.” These are **ASR flags, not evidence that the synthesized voice actually says the wrong words**. They make the can/can't and aren't negations particularly important in the pending human/audio listening check. Transcript-constrained alignment cannot clear these flags because it assumes the text.
