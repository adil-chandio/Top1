# EP5 v5 · "KAL AA JANA" — humanizer ported, voice-locked

**Repo cloned:** `cinema_v4/vendor/humanizer` — blader/humanizer **v4.0.0**, MIT, 248 KB, commit `b48c832`.
**Tool built:** `cinema_v4/tools/humanize_ur.py` — the 26 patterns as an executable gate, for Roman Urdu.
**Voice sample:** `cinema_v4/scripts/VOICE_TU_CUT_A.txt` — his own Cut A.

---

## The finding that changed the tool

`humanizer` run straight at **his** script:

```
FILE VOICE_TU_CUT_A.txt   21 sentences   142 words
§3   HARD  Sayings that sound deep        - zindagi
§6   HARD  Forced triads                  - Ammi. / Biwi. / Bachay.
                                          - Biwi. / Bachay. / Andar.
§7   soft  Repeated sentence openings     - 'yeh' x3+
SCORE 73/100 -> FAIL
```

The tool fails the best writing it has ever been shown. `Ammi. Biwi. Bachay.` is not a slop
triad — it is the sound of a man naming people inside a burning house, one at a time.

SKILL.md already had the answer, in **### Voice**:

> "The sample overrides the patterns below."

So the tool now scans the voice sample first and demotes any pattern the sample also fires to
**QUIRK**. His devices are subtracted from the rule set before my script is judged.

---

## Final

```
Ustaad ne bola: kal aa jana.

Ek parchi pe teen din likhe the. Woh parchi aaj bhi dashboard pe padi hai.

Teen din me chaar baar gaya. Chaar baar wohi kapda gari pe pada tha. Chaar baar wohi do lafz.

Paanchvi baar — chauthi? Ginti chhod. Paanchvi baar gari deewar se sati hui thi. Uski jagah kisi aur ki gari.

Ustaad ne chaabi teri taraf nahi ki. Usne chaabi jeb me daali. Bola: kaam ho gaya tha. Tu teen din baad aaya.

Aur woh teen din? Kis ne diye — usne nahi, tune. Phone pe, raat ko, kal se pakka likh ke. Woh raat yaad hai? Jab tune likha tha ke kal se sab badal jayega, aur agle teen din wohi gari, wohi kapda, wohi ustaad, aur tu bhi wohi, bas ek din aur kam?

Ab tu chauthi gari dhoond raha hai. Ustaad badal jayega. Gari badal jayegi. Aur tera kya badla, teen din me?

Woh do lafz nahi badlenge.
```

**158 words · 24 sentences · 3.51 wps · 45.0 s**

### Two gates, both green

```
humanize_ur.py  -> SCORE 97/100 PASS   hard patterns: none   drift: 0 of 6 voice axes
script_qc.py    -> SCORE 100/100 PASS  14/14
```

### Voice match (the part that was missing before)

| axis | script | his sample | delta |
|---|---|---|---|
| mean sentence length | 6.58 | 6.76 | −0.18 |
| sentence sd | 5.01 | 7.70 | −2.69 |
| short ≤4 words % | 25.0 | 42.9 | −17.9 |
| question % | 20.8 | 19.1 | **+1.8** |
| longest sentence | 29 | 35 | −6.0 |
| type/token | 0.52 | 0.65 | −0.14 |

Every axis inside tolerance. v4 was 2 axes out: it was written in my rhythm, not his.

---

## What the two tools now catch that I did not

| version | humanize | QC | verdict |
|---|---|---|---|
| v2 (mask) | — | 86 | concept, no people |
| v3 | **76 FAIL** | 76 FAIL | not-X-but-Y hinge + fortune-cookie |
| v4 | 97 | 100 | voice 2 axes off — my rhythm |
| **v5** | **97** | **100** | **0 axes off** |

---

## Beats · 45.0 s

| B | in–out | picture |
|---|---|---|
| 1 | 0.0–2.4 | rag on bonnet. Frame 0: **`KAL AA JANA`** |
| 2 | 2.4–6.2 | the parchi, taped to the dashboard, date in blue ink |
| 3 | 6.2–11.5 | four matched cuts: same corner, same cloth, four light passes |
| 4 | 11.5–15.0 | **the stumble** — "chauthi? Ginti chhod." He looks off-axis, hand over mouth, 8 frames |
| 5 | 15.0–19.0 | car pushed to the wall. Another car in its place |
| 6 | 19.0–25.5 | the key. Fist closes. He does not look up. *"Kaam ho gaya tha."* |
| 7 | 25.5–33.0 | phone at night, the message still on screen, thumb over it |
| 8 | 33.0–38.5 | the fourth car. Different colour. He doesn't open the door |
| 9 | 38.5–40.0 | eyes, cloth falling out of frame |
| 10 | 40.0–45.0 | **[BALLOON POP]** 40.0 · 800 ms nothing · *"Woh do lafz nahi badlenge."* whispered over black |

**Sound** workshop tone · rag on metal · one spanner dropped at B6 · sub on each `chaar` ·
heart 62→96 · 6-frame riser 39.4→40.0 · **pop** · absolute silence · whisper. No music.

---

## Still mine, not his

`parchi` · `dashboard` · `deewar se sati hui gari` · `chaabi jeb me daalna`.
Four objects. Name the real ones and they get swapped. The rhythm, the scene shape and the
ending are locked to his voice either way.
