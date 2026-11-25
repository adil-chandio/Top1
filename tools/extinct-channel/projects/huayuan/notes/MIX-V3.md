# Huayuan v3 — the master that exists

**File:** `exports/extinct-channel-huayuan/Huayuan-60s-V3-VO-IMAX.mp4`
**Size:** 70,001,225 B · **SHA-256 (first 24):** `52390df6fd53f144d7eeb7e1`
**Video:** H.264 High, 1920×1080, 30 fps, 1800 frames, yuv420p, bt709, CRF 16, faststart
**Audio:** AAC-LC, 48 kHz mono, 320 kb/s

## Measured on the delivered file, not on the intent

| check | result |
|---|---|
| decoded frames | **1800** (60.00 s) |
| min luma | **23.96** / 255 — no black frame anywhere |
| A→B→A flicker spikes | **0** |
| integrated loudness | **−15.4 LUFS** |
| true peak | **−1.8 dBFS** |
| A/V sync, all 20 lines | **≤ 0.03 s** drift (worst 0.11 s, line 1's fade-in) |

## How the audio got there

The narration is **two generations** of `voice-01` (29.00 s + 31.16 s = 60.16 s of take for
a 60 s film). Lines were not re-synthesised one by one: the take's own silences were located
and assigned to line boundaries by a DP that matches each chunk to that line's word count.
That assignment was then checked against the three lines that also exist as individual
clips — agreement 0.12–0.16 s.

Speech: **96 words / 40.95 s / 2.344 w/s**. Coverage 68.2 % of runtime, gate minimum 62 %.

Loudness was not a gain move. The bed measured **−19.44 LUFS with a true peak of −0.98 dBTP**:
the headroom to raise it linearly to −15 LUFS simply was not there, and a +4.4 dB gain would
have clipped. It was normalised with `loudnorm` in dynamic mode to −14.6 LUFS / −1.8 dBTP,
verified at −15.45 LUFS / −1.78 dBTP in the WAV, then measured again **after** AAC at
−15.4 / −1.75.

## The mistake that shipped an audio-less file first

The render CLI takes `--audio` as a **filesystem path**. It was given the web path
`/tools/...`, `fs.existsSync` returned false, and the tool silently took its no-audio branch:
a perfectly good 1800-frame video with no sound. The track was then muxed from the cached
plates without re-rendering. The CLI should fail loudly instead of degrading quietly —
that is a fix owed to the tool, not to this film.

## What this master is not

There is no score. The bed is narration only. A music pass and a sound design pass are
separate work, and the loudness of this master leaves room for both.
