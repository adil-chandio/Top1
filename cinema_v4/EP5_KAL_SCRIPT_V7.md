# EP5 v7 · "KAL AA JANA" — now a story, not a rant

**What was wrong with v6.** It had no character. It had a "tu" and a background ustaad, and it
spent 45 seconds accusing the viewer. Egri calls that a static conflict: one voice, no want,
nobody on the other side of the table. It reads as a lecture because it is one.

**Repo cloned:** `cinema_v4/vendor/screenwriting` — jtydhr88/screenwriting-skills, MIT, 4.7 MB.
The skill that mattered: `sw-character-conflict` (Egri + McKee + Cron + Lu Jun).

Three rules from it, applied literally:

> **出击点** — start at the moment of a **decision**, never at the cause.
> **人物真相 = 压力之下的选择** (McKee) — *he chooses, therefore he is.*
> **第一次冲突必须落在一个可演的动作上** — the first defeat must be a physical, filmable act.

So the film now opens on a decision (`aaj chahiye`), the first defeat is a **wrong spanner**
twice over, and the character is revealed by a choice made in silence at 2 a.m.

**New gate:** `cinema_v4/tools/storygate.py` — 12 checks from Egri/McKee/Chekhov.
Run on v6 it scores **60/100 NOT A STORY** (`6 x "you"`, no want, no turn, ends on a saying).
Run on v7 it scores **100/100 STORY**.

---

## FINAL

```
Ustaad ne kaha: kal aa jana.

Maine kaha: aaj chahiye.

Usne bonnet khola, band kiya. Phir wohi do lafz, kal aa jana.

Raat ko main wapas gaya. Kyun? Pata nahi. Shutter aadha khula tha, andar teen gariyan.

Meri gari deewar se sati hui thi, kapde ke neeche. Woh kisi aur ki gari pe jhuka tha, bina dekhe.

Main andar gaya, aur usne sar nahi uthaya. Aankhein gari pe thin. Usne mujhe dekha bhi tha?

Maine spanner uthaya, galat tha. Phir spanner uthaya, phir galat. Tisri baar usne bina dekhe haath badhaya, aur sahi spanner mere haath me rakha.

Usne spanner chheenna chahiye tha. Phir bhi spanner nahi chheena.

Hum dono raat bhar chup rahe, sirf spanner ki awaaz, aur torch ki roshni meri taraf aayi, aur woh roshni mujhe pehchanti hui lag rahi thi.

Kyun?

Aur phir woh torch hat gayi.

Subah gari theek thi. Kaise, mujhe ab bhi nahi pata.

Parchi pe likha tha kal aa jana. Usne woh parchi mere haath me rakhi, aur kaha: ab is pe aaj likh.
```

**172 words · 25 sentences · 3.58 wps · 48.0 s**

### Four gates, all green

| gate | score |
|---|---|
| `script_qc.py` | **100/100** |
| `storygate.py` | **100/100 STORY** |
| `humanize_ur.py` | **97/100**, voice drift **0 of 6** |
| `noslop_ur.py` | **PASS**, 0 hard patterns |

---

## The story, in the terms the skill uses

| element | what it is here |
|---|---|
| **Point of attack** | the decision, not the cause: `aaj chahiye` in frame 3 |
| **Want** (Cron) | the car today. Concrete, small, worth nothing to anyone but him |
| **Opposing voice** | the ustaad refuses with two words, and never argues again |
| **Misbelief** (Cron) | *"kal" is something the ustaad does to me* |
| **First defeat, actable** | the wrong spanner. Twice. You can film a man being wrong |
| **True character** (McKee) | he stays, and does not shout. That is the choice |
| **The turn** | `Usne spanner chheenna chahiye tha. Phir bhi spanner nahi chheena.` — the man who keeps saying "kal" gives away the tool instead |
| **S5** (Chekhov) | the right answer, `kal aa jana`, is said in act one and rejected |
| **S4** (Chekhov) | opens and closes on the same sentence, same counter |
| **C4** (Chekhov) | one object — the parchi — and one catchphrase |
| **Change** | the last action is the opposite of the first. He said `kal`; now he hands over the paper and says `aaj likh` |
| **No aphorism** | the film ends on a hand and a pen, not a lesson |

---

## Beats · 48.0 s · 26 cuts

| B | in–out | picture |
|---|---|---|
| 1 | 0.0–2.6 | counter. Ustaad doesn't look up. Frame 0 text `KAL AA JANA` |
| 2 | 2.6–4.4 | the boy: `aaj chahiye`. Jaw, not eyes |
| 3 | 4.4–8.0 | bonnet opens, he looks in, closes it. No words |
| 4 | 8.0–13.5 | night. Shutter aadha khula |
| 5 | 13.5–19.0 | his car under a cloth, pushed to the wall. The ustaad bent over somebody else's |
| 6 | 19.0–23.0 | `Usne mujhe dekha bhi tha?` — the boy's face in torch bounce |
| 7 | 23.0–30.0 | wrong spanner. wrong spanner. **then the hand, without looking** |
| 8 | 30.0–33.5 | `Phir bhi spanner nahi chheena.` — hold on the ustaad's shoulder |
| 9 | 33.5–38.5 | two men, one light, no dialogue. Real workshop sound only |
| 10 | 38.5–40.0 | `Kyun?` — torch swings away |
| 11 | 40.0–45.6 | morning. Car is clean. He is dirty |
| 12 | 45.6–48.0 | the parchi changes hands. `ab is pe aaj likh.` **[BALLOON POP]** at 46.4 · 800 ms nothing · pen scratch · out |

**Sound** workshop tone · spanner on concrete · the wrong-spanner clink (real, twice, identical) ·
torch click · heart 62→78 only under B9 · 6-frame riser 45.8→46.4 · **pop** · absolute silence ·
one pen scratch. No music.

---

## Files

`cinema_v4/scripts/kal_v7.txt` · `cinema_v4/tools/storygate.py`

Run all four:
```
python3 cinema_v4/tools/script_qc.py  cinema_v4/scripts/kal_v7.txt --duration 48 --register film
python3 cinema_v4/tools/storygate.py  cinema_v4/scripts/kal_v7.txt
python3 cinema_v4/tools/humanize_ur.py cinema_v4/scripts/kal_v7.txt --voice cinema_v4/scripts/VOICE_TU_CUT_A.txt
python3 cinema_v4/tools/noslop_ur.py   cinema_v4/scripts/kal_v7.txt --voice cinema_v4/scripts/VOICE_TU_CUT_A.txt
```

## Still his

The film is fiction now, so nothing here claims to be his memory. What only he can settle:
`parchi` ya kaam ka koi aur nishan · workshop kholi ya gali · aur kya woh aakhri lafz usne khud suna tha.
