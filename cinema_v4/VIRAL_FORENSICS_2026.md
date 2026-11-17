# TABAHI · Viral forensics, 2026
### What million-view short-form scripts actually do — measured, not guessed

**Sources**
- `thecontentlabs.app` — *"What 1M-View Scripts Actually Say: A Linguistic Teardown of 165 Viral Videos"*.
  9,326 hooks for the first-word study, **3,633 full transcripts** for the script study, tiered
  under 100K / 100K–1M / **1M+ (165 videos)**.
- Berger & Milkman (Wharton) — 7,000 NYT articles, emotional arousal and sharing.
- Berger, *Contagious* — STEPPS.
- NYU — moral-outrage language and retweet rate.
- Islamic funeral practice (ghusl, kafan, janazah, 24-hour burial, hidad 3 days) — documented,
  not invented. See `idea` below for why that matters.

---

## 1. The three numbers that break my last six drafts

| metric | under 100K | **1M+** | my v8 |
|---|---|---|---|
| words per sentence | 10.2 | **14.0** | **6.9** |
| questions per script | 1.16 | **1.84** | 4 (ok) |
| profanity | 12.2 % | **6.7 %** | 0 |
| you ÷ I ratio | 2.40 | **1.91** | **0.18** |

**Reading it honestly:** mega-viral scripts are *longer-sentenced, more curious, cleaner, and less
"you"-heavy* than small ones. My scripts are the exact inverse: staccato fragments, almost no
"you", very few questions. That is not a style choice, it is **long-tail DNA**. The gate now
enforces this — `script_qc.py --tier viral`:

```
FAIL  Viral: 11-15 words/sentence   -10   6.9 (long-tail 10.2, viral 14.0)
FAIL  Viral: you/I ratio 1.4-2.4     -8   0.18 (viral 1.91)
```

"Punchy = viral" is the myth. It is true *below* 100K and false above 1M. Complete thoughts travel.

---

## 2. The emotion that decides reach (share rate vs average)

| emotion | share rate | | emotion | share rate |
|---|---|---|---|---|
| **Awe** | **5.3×** | | Pride | 2.5× |
| **Anger** | **4.8×** | | Hope | 2.1× |
| Anxiety | 3.7× | | Nostalgia | 1.8× |
| Excitement | 3.4× | | **Sadness** | **0.7×** |
| Amusement | 3.1× | | Contentment | 0.4× |
| Surprise | 2.9× | | | |

**This is the whole problem.** v6, v7 and v8 are beautiful and they are **sad**. Sadness shares at
**0.7×**. A masterpiece in the sadness column is mathematically capped.

Worse: **his own script was anger** — *"duniya tujhe lectures degi"*, *"wohi apne aate hain aur mayyat
par khane ka intezam karte hain"*. He put the world on trial. That is the 4.8× quadrant. I took his
anger and converted it into my melancholy. **I drifted off his bar, not toward it.**

---

## 3. What actually moves people to press share

Not "good content". Four mechanisms, all measurable:

1. **Identity signalling.** Sharing is a sentence about yourself. 73 % say they share to define
   themselves. The test: *what would someone say about themselves by sharing this?* If the answer is
   flattering, it spreads. If neutral, it dies.
2. **High-arousal emotion.** Intensity, not positivity. Anger and awe both work; sadness does not.
3. **Moral outrage, quantified.** NYU: each outrage-expressing word raised retweet rate **+17 %**.
   Outrage is not a tone, it is a metric.
4. **Practical value + the curiosity gap.** Practical content is shared by **DM** more than any other
   type — and DM shares are the strongest ranking signal on Instagram in 2026.

What people actually want underneath all of it: **status, certainty, permission, and to be seen as
someone who sees clearly.** They feel anxiety about a life they suspect they are wasting, and they
cannot say it out loud. The content they share says it for them.

---

## 4. The five moves a 1M+ script makes, in order

1. A **question** in the first two lines (1.84 per script vs 1.16).
2. The subject, **not the relationship** — it teaches you something, it doesn't scold you
   (you/I 1.91, not 2.4).
3. **Awe through scale or mechanism**, delivered as fact, not as feeling.
4. **Anger through a named hypocrisy** — someone gains while someone else pays.
5. Ends on a **thing**, not a lesson. The lesson is what the viewer says in the comments.

That last one is why the moral has to be *inside* the story, spoken by whoever paid the price.

---

## 5. What this kills, and what survives

**Killed:** the "tu/tum" accusation format. Staccato fragment stacking as a default. Sadness as the
emotional engine. Ending on a soft image.

**Survives and gets stronger:** his own devices — duniya ko mulzim banao (anger), the cost ledger
(anger + practical value), the parable with a kicker (awe), zero abstraction.

**The correction is one line:** stop writing sad films about a good man. Write **angry** films about
a system, with **awe** as the texture.
