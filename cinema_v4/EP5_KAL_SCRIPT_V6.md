# EP5 v6 · "KAL AA JANA" · idea kept, script rebuilt on two rulesets

**Same idea.** Ustaad, parchi, teen din, chauthi gari. Nothing about the concept changed.

Two skills, cloned and each turned into an executable gate:

| source | vendored at | licence | what it added |
|---|---|---|---|
| `blader/humanizer` v4.0.0 | `cinema_v4/vendor/humanizer` | MIT | 26 patterns, voice override |
| `petergyang/no-ai-slop` | `cinema_v4/vendor/no-ai-slop` | MIT | editor's checklist, portability test, kicker ban |

Tools: `cinema_v4/tools/humanize_ur.py` · `cinema_v4/tools/noslop_ur.py` · `cinema_v4/tools/script_qc.py`
Voice sample: `cinema_v4/scripts/VOICE_TU_CUT_A.txt` (his Cut A)

---

## What each repo forced, in order

**1. humanizer** — killed my punctuation, not my idea.
`§1 Not X but Y` → deleted the "Sawaal yeh nahi… sawaal yeh hai" hinge. `§3 sayings that sound deep` → deleted "har cheez ke liye kal aata hai".

**2. no-ai-slop** — killed my closer, and made the idea pay off properly.
> *"Fake-profound kickers. Cut the final 'deep' line… Do not rewrite it into a better metaphor. Delete it, then end on the clearest concrete sentence already in the draft."*

Deleted: ~~"Woh do lafz nahi badlenge."~~ That is an aphorism.

Replaced with the thing already in the scene: **the ustaad's own words, now coming from the next man.** The film ends on the sentence it opened with, said by somebody else, about him.

**3. The rule both repos needed and neither has alone.** Both were run on his own script first.
humanizer scored it **73/100 FAIL**. no-ai-slop flagged `Main abhi bhi apni taraf hoon` as a **kicker**.
Both were wrong. His closer is not a claim about the world, it is a man saying something about himself. So the tools now read the voice sample and exempt any device the sample also uses — except the kicker rule, which stays hard, because no voice needs to end on an aphorism.

---

## FINAL

```
Ustaad ne bola: kal aa jana.

Ek parchi pe teen din likhe the. Woh parchi aaj bhi dashboard pe padi hai.

Teen din me chaar baar gaya. Chaar baar wohi kapda gari pe pada tha. Chaar baar wohi do lafz.

Paanchvi baar — chauthi? Ginti chhod. Paanchvi baar gari deewar se sati hui thi. Uski jagah kisi aur ki gari.

Ustaad ne chaabi teri taraf nahi ki. Chaabi jeb me daali. Bola: kaam ho gaya tha. Tu teen din baad aaya.

Aur woh teen din? Kis ne diye — usne nahi, tune. Phone pe, raat ko, kal se pakka likh ke. Woh raat yaad hai? Jab tune likha tha ke kal se sab badal jayega, aur agle teen din wohi gari, wohi kapda, wohi ustaad, aur tu bhi wohi, bas ek din aur kam?

Ab tu chauthi gari dhoond raha hai. Ustaad badal jayega. Gari badal jayegi.

Aur jab woh chauthi gari teen din baad khadi hogi, woh bhi kahega: kal aa jana.
```

**161 words · 23 sentences · 3.58 wps · 45.0 s**

---

## Three gates, all green — first version to do it

| script | qc | humanizer | no-ai-slop |
|---|---|---|---|
| v2 mask | PASS | FAIL | FAIL |
| v3 | FAIL | FAIL | FAIL |
| v4 | PASS | PASS | FAIL |
| v5 | PASS | PASS | FAIL |
| **v6** | **PASS** | **PASS** | **PASS** |
| film_v6 (rejected) | FAIL | — | FAIL |

Voice drift: **0 of 6 axes** (mean 7.13 vs 6.76, sd 5.61 vs 7.70, questions 17.4 % vs 19.1 %, longest 29 vs 35).

---

## The ending, in the cut

| B | in–out | picture |
|---|---|---|
| 1 | 0.0–2.4 | rag on bonnet. Frame 0 text: `KAL AA JANA` |
| 2 | 2.4–6.2 | the parchi taped to the dashboard, date in blue ink |
| 3 | 6.2–11.5 | four matched cuts, same corner, same cloth, four light passes |
| 4 | 11.5–15.0 | **"chauthi? Ginti chhod."** — he stops, hand over mouth, 8 frames |
| 5 | 15.0–19.0 | car pushed to the wall, another car in its place |
| 6 | 19.0–25.5 | the key. Fist closes. He does not look up |
| 7 | 25.5–33.0 | phone at night, the message still on the screen, thumb over it |
| 8 | 33.0–38.5 | the fourth car, different colour. He doesn't open the door |
| 9 | 38.5–40.0 | *"kal aa jana"* — said off-screen, to the next man. **He looks up.** |
| 10 | 40.0–45.0 | **[BALLOON POP]** · 800 ms nothing · the line again, whisper, over black |

**Sound** workshop tone · rag on metal · one spanner dropped at B6 · sub on each `chaar` ·
heart 62→96 · 6-frame riser 39.4→40.0 · **pop** · absolute silence · whisper. No music.

---

## Still his to give

Four objects are mine: `parchi` · `dashboard` · `gari deewar se sati hui` · `chaabi jeb me daalna`.
Everything else — the rhythm, the stumble, the loop, the silence before the pop — is locked.
