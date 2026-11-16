# EP5 v4 · "KAL AA JANA" · humanizer pass, voice-matched to HIS script

**Method** `blader/humanizer` (MIT, ★69k) — AGENTS.md + README + SKILL.md, all read.
The step I had been skipping is in the README:

> **Match your voice** — "include a sample of your own writing... Humanizer follows the
> sample's rhythm, word choice, punctuation, and deliberate quirks."

**Voice sample** = his own script (Cut A): short declaratives, `tu`, a stumble before a
correction, questions used as the knife, and *no* lesson ever spoken.

---

## 1. AUDIT of v3 — what he was calling robot writing

| humanizer # | Tell | v3 line |
|---|---|---|
| 1 | Not X but Y | *"Sawaal yeh nahi ke gari kab ready hogi. Sawaal yeh hai ke tu kab ready hoga?"* |
| 2 | One-line closer / dramatic fragment | *"Ek kal."* |
| 3 | Sayings that sound deep | *"Kyunki tu har cheez ke liye kal aata hai."* / *"Woh kal kabhi nahi aata."* |
| 6 | Forced list | *"Kaam kal. Call kal. Maafi kal. Ghar jaana kal."* — four abstractions, zero scene |

v3 scores **76/100 FAIL** under the two new gates.

## 2. FIRST REWRITE (draft)

Scene instead of sermon: a parchi with a date, a cloth on the car, a key that never
changes hands. Lesson deleted. Only the accountant line survived, because the scene earns it.

## 3. CRITIQUE of the draft — what still sounded written

- *"Teen din kis ne diye? Usne nahi. Tune."* — still a hinge, one notch softer than the one I cut.
- *"Woh do lafz nahi badlenge."* — an aphorism. Kept only because the parchi is on screen.
- The narrator never stumbled. A man telling this story loses count, because it shames him.
  **Fix:** `Paanchvi baar — chauthi? Ginti chhod.`
- Too clean for a workshop. The dust and the thumbprint carry the abandonment; nothing else needed.

## 4. FINAL

```
Ustaad ne bola: kal aa jana.

Ek parchi pe teen din likhe the. Woh parchi aaj bhi dashboard pe padi hai.

Teen din me chaar baar gaya. Chaar baar wohi kapda gari pe pada tha. Chaar baar wohi do lafz.

Paanchvi baar — chauthi? Ginti chhod. Paanchvi baar gari side pe khiski hui thi, deewar se sati hui, aur uski jagah kisi aur ki gari khadi thi. Darwaze ki dhool pe angoothe ka nishan hai. Tune pehli baar lagaya tha.

Ustaad ne chaabi teri taraf nahi ki. Usne chaabi jeb me daali. Bola: kaam ho gaya tha. Tu teen din baad aaya.

Teen din kis ne diye? Usne nahi. Tune. Phone pe, raat ko, kal se pakka likh ke.

Ab tu chauthi gari dhoond raha hai. Ustaad badal jayega. Gari badal jayegi. Woh do lafz nahi badlenge.
```

**136 words · 23 sentences · 3.02 wps · 14/14 gates · 100/100 PASS**

```
python3 cinema_v4/tools/script_qc.py cinema_v4/scripts/kal_v4.txt --duration 45 --register film
```

---

## Gate history (the tool now catches what he caught)

| script | score | verdict |
|---|---|---|
| `film_v6.txt` | 66 | FAIL — desk words, emotion label, fortune-cookie |
| `kal_v3.txt` | 76 | FAIL — not-X-but-Y hinge, fortune-cookie |
| `kal_v2.txt` | 86 | PASS (but topic dead — concept, no people) |
| **`kal_v4.txt`** | **100** | **PASS — 14/14** |

---

## Beat map · 45.0 s · 26 cuts, none over 2.2 s

| B | in–out | picture |
|---|---|---|
| 1 | 0.0–2.4 | ustaad's hand, dirty rag, drags across a bonnet. Frame 0 text: **`KAL AA JANA`** |
| 2 | 2.4–6.0 | the parchi, taped to the dashboard, date in blue ink, dust on the tape |
| 3 | 6.0–11.0 | four matched cuts: same corner, same car, cloth, different light. On each `chaar`, one more dust layer |
| 4 | 11.0–15.0 | **the stumble.** He stops. Looks away off-axis. Hand over mouth for 8 frames |
| 5 | 15.0–21.0 | car pushed to the wall, other car in its place. His thumbprint in the dust — insert 6 frames |
| 6 | 21.0–27.5 | the key. Ustaad's fist closes around it. He does not look up. *"Kaam ho gaya tha."* |
| 7 | 27.5–33.0 | phone, night, sent message on screen, thumb over it. No reply needed — it's his own message |
| 8 | 33.0–38.0 | the fourth car: a different colour, same problem. He does not open the door |
| 9 | 38.0–40.0 | extreme close, eyes, cloth falling out of frame |
| 10 | 40.0–45.0 | **[BALLOON POP]** 40.0 · 800 ms nothing · *"Woh do lafz nahi badlenge."* whispered over black |

**Sound** workshop tone · rag on metal · spanner dropped once (beat 6) · one sub per `chaar` ·
heart 62→96 · 6-frame riser 39.4→40.0 · **pop** · absolute silence · whisper. No music.

---

## Open, and I will not guess it

`parchi`, `dashboard`, `angoothe ka nishan`, `kapda` — these are the **four details that are mine**.
If your workshop doesn't look like this, name the four and they get replaced. Everything else in
the script is structure, and structure doesn't lie.
