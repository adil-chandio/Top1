# Huayuan — mix v2 (the silence fix)

## The complaint, measured

The approved mix had **no music bed at all** — only the voice and a room tone sitting near
−36 dB. So every pause between paragraphs was literal silence:

| gap | length |
|---|---|
| 5.75 → 7.25 s | 1.50 s |
| 11.75 → 13.00 s | 1.25 s |
| **20.00 → 23.00 s** | **3.00 s** |
| 30.00 → 32.00 s | 2.00 s |
| 45.25 → 48.00 s | 2.75 s |

**10.5 s of dead air in a 60 s film.** On top of that the approved master also **clipped**: 795
samples above 1.0, decoded peak **1.1679**. Both are fixed here.

## What was built

A score, synthesised (no library, no licence question), that follows the cut rather than sitting
under it:

- **Harmony** — a slow low bed under a four-chord arc. The third chord (B♭) lands on the
  extinction at 23 s, i.e. the floor falls away exactly where the film does.
- **Glass** — a high beating tone that arrives at 20.2 s and leaves at 47 s: the fossil's
  presence, not a melody.
- **Pulse** — a 46 Hz throb through the crisis only (10.5 → 23 s), rising from 0.85 to 1.9 Hz.
  Deliberately not a beat — water has no tempo, it has pressure.
- **Riser + sub drop** into the 23.0 s cut.
- **Water** — filtered noise, present for the whole 60 s, so the floor never drops to zero.

Then the mix:

1. Voice peak-normalised to 0.92 (it was clipping before anything was added).
2. Bed set 13 dB under the voice **before** ducking.
3. **Sidechain from measured voice activity** (10 ms RMS, gated 7 dB over the noise floor,
   30 ms attack / 300 ms release): bed drops 62% under speech, returns to full in the gaps.
   This is the actual fix — the bed can be loud where the voice is absent without ever
   fighting it where the voice is present.
4. Look-ahead peak limiter (4 ms, 90 ms release) — touches only what would clip.
5. Gentle 2:1 program compression at −24 dB so the quiet passages lift without the loud ones
   moving.

## Result

| metric | before | after |
|---|---|---|
| silent runs ≥ 0.20 s | 5 | **0** (only the last 0.3 s tail) |
| quietest 50 ms window | −47.0 dB | −49 → now bed-covered throughout |
| integrated loudness | −15.2 LUFS | **−14.5 LUFS** |
| loudness range | — | **3.3 LU** |
| true peak | **−1.5 dBFS** (source clipped at 1.168) | **−0.3 dBFS**, no samples over 1.0 |

Old gap 3 (the 3-second hole at 21–23 s) now measures **−25.9 dB** instead of −36.7 dB: there is
music there, and it is quiet because the film is quiet, not because the file is empty.

## Honest limits

- The bed is **synthesised**, not composed. It is harmonically simple on purpose and it is
  designed to be felt more than heard; it is not a substitute for a real score.
- The voice is the same read, same timing, same performance. Nothing about the narration was
  re-recorded or retimed — only its level staging and the space around it changed.
- The ducking is measured, not by ear: I have not listened to this mix, I have measured it.
  The numbers above say what the file does; they do not say it sounds good, and that judgement
  is still the user's.
