# Huayuan v3 — where the film actually stands

Written 2026-11-25, after a preflight that looked fine and was not.
Every number here is copied from a tool run in this session.

---

## What is finished and verified

| | state | how it was checked |
|---|---|---|
| The lab set renders at all | fixed | it did not. `apply_timing.py` wrote the script's sequence name into the field that switches scene graphs, so both graphs went invisible and the shot was empty. Mapping is now explicit. |
| One palette (no orange third act) | fixed | pixel probe at f860: warm pixels 2.50 % → **0.00 %** on the slab, 0.02 % on the sea. Cause was `makeImaxMaterial`'s amber defaults on the 90-unit floor, not the texture (map measured 0.0 % warm). |
| Captions land on their own lines | fixed | `CUES`/`CLAIMS` now live in `v3_script.py`, resolve to the frames of the line that speaks them, and are injected by `tools/apply_timing.py`. A G7 gate fails the build if a cue outlives its line. |
| "Animal, whole" beat is not black | fixed | the 24 mm looked along a 12×8 plate at 17° depression; it is now high and oblique. |
| 20-shot cut, ASL 3.00 s | pass | longest 7.22 s, shortest 1.80 s, 4.0× spread; 96 words, 43.73 s speech (72.9 %). |
| Timing is derived, never typed | enforced | `apply_timing.py` is idempotent (ran twice, byte-identical), and the chain `v3_script.py → apply_timing.py → node --check` passes. |

## What is not finished

**Seventeen of twenty lines have no voice.** The ten clips in `audio/vo-voice01/` speak an
earlier 22-line draft; only three are word-identical to the current script (lines 5, 8, 9).
This is why the film cannot be released yet, and why no master is being rendered.

The consequence is worth stating plainly: **every frame number in the film is a model
prediction, including the ones that look right on the contact sheet.** `MEASURED` is
calibrated on the draft's ten lines at 2.436 w/s — the voice's true articulation rate, but
not this script's line lengths. When the real takes land, the whole cut shifts, and the HUD
and shot map shift with it in one command.

## The order that works

1. Record 10 lines. Record the remaining 7 in the next turn. (`notes/VO-SHEET.md`)
2. `measure_vo.py` → paste the twenty speech values into `MEASURED`/`MEASURED_WORDS`.
3. `v3_script.py` must PASS — then **read the per-scene table**, not just the verdict.
4. `apply_timing.py`, `node --check`, preflight, and look at the sheet at full size.
5. Only then: score, mix (−15 LUFS, ≥0.9 dB TP headroom), render 1800 f at 1920×1080
   with `--workers 2` (≈57 min), `verify_imax_mp4`, proof frames, upload, commit.

## Corrections I owe, on the record

- I blamed the slab texture for an orange frame. The texture was clean; the lights and the
  floor's default specular were the cause. Two preflights were spent before I measured
  instead of guessed.
- A handover note said six old clips could be reused. Only three can. The check compared
  the script against a remembered draft instead of the draft itself, which is in
  `SCRIPT-V3.md` §3.
- The rebase that brought this branch level with the remote silently kept the remote's
  superseded `v3_script.py`; the tool went back to reporting 116 words. Caught by re-running
  the tool, restored in `3ef2d5b`.
- This status file's earlier sibling said the film was renderable. It was not, twice: first
  because nothing rendered, then because the words on screen were one shot out of phase.
