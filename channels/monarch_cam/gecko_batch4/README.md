# Batch 4 — production started, not complete

Batch 2 was skipped by user, not passed; Batch 3 narration listening and caption synchronization are pending. This folder starts Batch 4 with an original sound-bed and narration mix, not a complete film. The existing cartoon-like gecko tests were rejected as reference-quality and have not been repackaged as the full production. No slides/still-image animation substitution is used.

## Sound draft

`create_sound_bed.py` synthesizes original tones, interpolated noise and swells; no external music or Dailymotion sound is used. Requires Python with NumPy. The mixed WAV includes the selected v2 narration (`../gecko_batch3/audio/gecko-narration-v2.wav`) and original score.

```sh
python create_sound_bed.py
ffmpeg -i ../gecko_batch3/audio/gecko-narration-v2.wav -i audio/original-bed.wav \
  -filter_complex '[0:a]volume=0.80,pan=stereo|c0=c0|c1=c0[voice];[voice][1:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[mix]' \
  -map '[mix]' -c:a pcm_s16le audio/gecko-audio-mix-draft.wav
```

60.8 s stereo PCM, 24 kHz; decoded completely, mean −19.8 dBFS and maximum −2.0 dBFS (sample peak). Mix SHA-256 `971fc074790eb8197a17113a125f28b65d73d952cce5e1fdaa33a59a5e90277f`; score `a545a758b5bc57bb671accd1c3cd4ad36b9ac9acab66845d5b98ce24cce903f5`. Mix saved to the existing production folder: https://drive.google.com/file/d/1fz50jYO5v5mIDrdnTLGsI70UsuIvJ8rq/view ; Drive reported matching hash and 5,836,878 bytes. Folder permissions inherited and unchanged; not a publication. No actual listening was done, so quality, balance, intelligibility, technical-term pronunciation and seam checks remain unverified; earlier recognition flagged potential can/can't and aren't ambiguity. This mix is draft, not approved for final use. WAVs are ignored by Git per repo convention; Drive hosts the mixed WAV and previous narration, while the score is reproducible from the script.

## Visual benchmark to production

Previously inspected half-second frame samples from [CGMeetup Gecko Animation](https://www.dailymotion.com/video/x6i0u21) suggest low-angle environmental framing, separation via light background, foreground vegetation and alternating wide and close views. They do not establish exact motion, edit cadence or audio, nor permission to reuse. Transfer only those general composition principles to original shots; make toe contact and the scientific graphics brighter and legible. Source notes: `../gecko_batch2/GECKO_DENSE_VISUAL_REVIEW_2026-11-18.md`. The source is not confirmed a viral animal explainer; wider relevant 3D-video comparison remains incomplete.

## Remaining critical work

Build a credible original/cleared animated gecko, environment and readable foot/contact action, followed by original microstructure shots. Assemble all shots against the 60.80-second voice, synchronized captions and sound; inspect and correct full output against the benchmark. Rights checks for any new third-party assets remain mandatory. Batch 4 has not produced the complete picture film or passed the gate; Batch 5 has not started. No public publication or paid purchase is authorized.
