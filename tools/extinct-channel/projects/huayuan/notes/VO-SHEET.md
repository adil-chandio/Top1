# Huayuan v3 — voice sheet

**Voice:** `voice-01` (registered by the user on the second audition).
**Engine:** `generate_speech`, one file per line, `audio/vo-voice01/nNN.mp3`.
**Rule:** the text below is copied from `tools/v3_script.py`, not retyped. If a line changes
there, this sheet is stale and must be regenerated before another file is cut.

Why one file per line: a single long take cannot be placed. The packing solver in
`v3_script.py` needs each line's own measured body length (`tools/measure_vo.py`), and a line
whose duration is guessed is a line the picture will eventually have to cut through.

---

## Lines that exist (3 of 20)

| line | file | text | speech |
|---|---|---|---|
| 5 | `l05.mp3` | Then the water went dark, | 1.79 s |
| 8 | `l09.mp3` | No oxygen. No decay. | 2.23 s |
| 9 | `l10.mp3` | Then the light goes out. | 1.48 s |

Copy these to `n05.mp3`, `n08.mp3`, `n09.mp3` — byte-identical, not re-synthesised. A
different take of the same words is a different performance and will not match the others.

## Lines that must be spoken (17)

Speak exactly these, no added words, no dropped articles. Punctuation is direction: a comma
is a breath, a full stop is a fall.

| line | file | text | words |
|---|---|---|---|
| 1 | `n01.mp3` | A stone from a dead seafloor. | 6 |
| 2 | `n02.mp3` | Five hundred and twelve million years ago. | 7 |
| 3 | `n03.mp3` | It was crawling with animals. | 5 |
| 4 | `n04.mp3` | None of them had bones. | 5 |
| 6 | `n06.mp3` | and the silt came. | 4 |
| 7 | `n07.mp3` | Buried before they could rot. | 5 |
| 10 | `n10.mp3` | The rock opens. | 3 |
| 11 | `n11.mp3` | Not a skeleton. | 3 |
| 12 | `n12.mp3` | The animal itself, pressed into stone. | 6 |
| 13 | `n13.mp3` | Softer than bone: eye, gill, nerve. | 6 |
| 14 | `n14.mp3` | One hundred and fifty-three species, | 5 |
| 15 | `n15.mp3` | in sixteen groups. | 3 |
| 16 | `n16.mp3` | The extinction passed above. | 4 |
| 17 | `n17.mp3` | Down here, life kept going. | 5 |
| 18 | `n18.mp3` | Was the deep a refuge? | 5 |
| 19 | `n19.mp3` | A hypothesis, not a fact. | 5 |
| 20 | `n20.mp3` | The stone is still answering. | 5 |

82 words. At the voice's measured 2.436 w/s plus punctuation that is roughly **38 s of
new speech**, which lands the finished read near 47 s in a 60 s film — about 78 % coverage,
comfortably above the 62 % gate.

⚠ Lines 1–10 are the remaining budget of the *current* ten-per-turn allowance. The tool
refuses an eleventh call in the same turn, and the refusal is not a failure of the film —
it is a rate limit. Two turns finish the set: 10 now, 7 next.

## After the last file lands

```bash
cd tools/extinct-channel/projects/huayuan
python3 tools/measure_vo.py audio/vo-voice01 --json /tmp/vo.json   # per-line bodies
# paste the 20 speech values into MEASURED in v3_script.py, and the word counts into
# MEASURED_WORDS, then:
python3 tools/v3_script.py           # must print PASS; read the per-scene numbers, not just PASS
python3 tools/apply_timing.py        # injects cues, claims, shot frames into film_v3.js
node --check film_v3.js
```

Then re-preflight. Every frame number moves when the real durations land — that is expected,
and it is exactly why none of them are typed by hand any more.
