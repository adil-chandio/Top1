# Huayuan v3 — the one-minute script

**Status:** script and derived cut, gate-checked. No audio generated, no frame rendered.
**Tool:** `tools/v3_script.py` — run it, it prints the read, the silences and the cut, and exits
non-zero if any gate fails. Everything below is copied from its output, not remembered.

---

## 1. What was wrong with v2 (measured, not asserted)

| | v2 shipped | v3 script |
|---|---|---|
| Speech coverage | **41.0 %** (24.5 s voiced in 60 s) | **72.8 %** (43.7 s) |
| Silences ≥ 1.0 s | **5** | **2** |
| Longest silence | **2.98 s** | **1.80 s** (a declared hold) |
| Silent openings with no words on them | 3 shots | 0 |
| Cuts landing inside a spoken line | 7 measured (never checked before) | **0** |
| Captions claiming more speech than exists | 2 blocks (4.7 s claimed / 1.4 s real) | derived from measured times |

Three findings from this pass that the previous audit did not have:

1. **7 of the 17 v2 cuts fell inside a spoken line.** The film cut through words. This was never
   measured. The gate that catches it (`G1`) is now in the tool.
2. **v2's 14.3× shot-length spread was bought with 0.70 s shots** — the same shots the earlier
   audit called flicker. The number in `DIRECTOR-CUT-PLAN.md` was flattering the cut, not
   describing it. Coverage and spread trade against each other directly.
3. **The v2 line "the shallows had already passed" sat over a fossil close-up.** The words named
   something the frame did not show. v3 says "the extinction passed above them" over the water,
   because that is what the frame is.

---

## 2. The rate, and why the first model was wrong

The approved read measures **93 words in 34.8 s of voiced audio** (200–3500 Hz VAD, 23 segments,
gaps ≥ 0.35 s counted as silence).

The obvious model — 34.8/93 = 0.3742 s per word — treats that figure as if it were pure speech.
It is not: it already contains the pauses inside the read. Using it *and then* adding sentence
breaks double-counts them. That model predicted **38.74 s** for a read that measured **34.80 s**,
and every line after the first long one cascaded into overlap.

Corrected:

```
articulation   3.00 words/s   (0.333 s per word, pauses excluded)
comma          0.15 s
full stop      0.38 s

93/3.00 + 12×0.15 + 5×0.38 = 34.80 s     ← the measurement, to 0.01 s
```

`calibrate()` runs on every invocation and fails the whole script if the model drifts more than
0.55 s from the measured read. When the new read is synthesised, this model is replaced by
measured segment times.

---

## 3. The read

22 lines. `in`/`out` are model times; the text is final.

| # | in | out | shot | line |
|---|---|---|---|---|
| 1 | 0.60 | 3.66 | ECU 50 mm | This stone was the floor of a vanished sea. |
| 2 | 4.55 | 7.09 | WS 35 mm | Five hundred and twelve million years ago, |
| 3 | 7.95 | 10.39 | WS 35 mm | this seafloor was crawling with animals. |
| 4 | 11.25 | 12.64 | CU 85 mm | Nothing here had bones. |
| 5 | 13.50 | 15.38 | EWS 14 mm | Then the water went dark, |
| 6 | 16.10 | 18.21 | WS 28 mm | and the silt came down. |
| 7 | 18.62 | 21.01 | MS 50 mm | It buried them before they could rot. |
| 8 | 21.15 | 22.59 | CU 60 mm | Sealed. Still whole. |
| 9 | 22.75 | 24.52 | MCU 85 mm | No oxygen. No decay. |
| 10 | 24.60 | 26.33 | ECU 100 mm | Then the light goes out. |
| 11 | 27.05 | 28.11 | EWS 35 mm | The rock opens. |
| 12 | 28.95 | 30.68 | WS 24 mm | This is not a skeleton. |
| 13 | 31.20 | 34.08 | MS 35 mm | It is the animal itself, pressed into stone. |
| 14 | 34.60 | 36.66 | CU 50 mm | What survived is softer than bone: |
| 15 | 37.00 | 39.07 | MCU 85 mm | eye, gill, and nerve. |
| 16 | 39.20 | 41.08 | CU 50 mm | One hundred and fifty-three species, |
| 17 | 41.30 | 42.74 | ECU 100 mm | in sixteen groups. |
| 18 | 43.15 | 44.88 | WS 28 mm | The extinction passed above them. |
| 19 | 45.55 | 47.43 | WS 50 mm | Down here, life kept going. |
| 20 | 48.10 | 50.16 | MCU 85 mm | Was the deep water a refuge? |
| 21 | 50.80 | 53.24 | MS 35 mm | Perhaps. That is only a hypothesis. |
| 22 | 53.60 | 55.33 | CU 50 mm | The stone is still answering. |

116 words · 43.71 s of speech · 72.8 % of runtime.

**The two designed silences, and why they are allowed:**

| window | length | reason |
|---|---|---|
| 55.33 → 58.20 | **2.87 s** | the film lets go of the words; the third act plays out on picture |
| 58.20 → 60.00 | 1.80 s | final wide, picture only |

Every other silence is ≤ 0.90 s.

**Say the 2.87 s plainly:** it is the same length as the gap this whole pass exists to remove
(v2's worst was 2.98 s). The difference is *where* it is — v2's sat in the middle of the story,
between 20.10 and 23.08 s, where the audience is still waiting to be told something. This one is
after the last line, where there is nothing left to tell. The middle of the film is now the
tightest part of it (all gaps < 0.90 s), not the emptiest.

---

## 4. The cut

22 shots, ASL **2.73 s**, longest **6.70 s** (the seafloor wide, a moving setup), shortest **1.60 s**,
max/min **4.2×**. Told from the shot list, not the other way round: every cut is placed **0.08 s
before a line**, i.e. inside a silence, so no cut can fall inside a word.

The crisis falls: **2.60 → 2.52 → 2.53 → 1.60 → 1.85 → 2.45**. It is the only scene whose shots
shorten and then release, and the release is the cut to black at 26.3 s.

Lenses: 50/35/85/14/28/50/60/85/100/35/24/35/50/85/50/100/28/50/85/35/50/24 — 8 distinct
focal lengths, no two adjacent shots on the same lens.

---

## 5. What this script does **not** do

- **It does not generate the voice.** The approved read is a finished performance; this pass
  re-times *where the words sit*, not how they are spoken. Generating a new read needs the
  owner's authorisation and a registered voice.
- **It does not claim the model is the read.** Every time above is a prediction from a calibrated
  model. The first frame of every shot and every line onset has to be re-measured on the actual
  audio once it exists; `calibrate()` is the tripwire, not the proof.
- **The science is unchanged and still labelled.** "The extinction passed above them" is the
  Sinsk event (Myrow et al.); the deep-water refuge stays a hypothesis in words and on screen.
- **No picture has been rendered from this cut.** Shot sizes and lenses are the plan; the
  preflight eye-gate has not run on them.
