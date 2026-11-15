#!/usr/bin/env python3
"""storygate.py - is this a story, or is it a rant wearing a story's clothes?

Built from cinema_v4/vendor/screenwriting (jtydhr88/screenwriting-skills, MIT):
  sw-character-conflict  Egri 出击点 / McKee characterisation vs true character / Cron desire vs misbelief
  chekhov-dramaturgy     S4 open-close in one place, S5 answer said early and rejected, S8 three-layer ending
  sw-scene-craft         conflict lands on an actable action before it lands on an idea

A rant has: one voice, no want, no opposing voice, and it addresses the viewer.
A story has: someone who wants something, someone who won't give it, a choice that costs,
and a last action that is not the first action.

Usage:
  python3 storygate.py cinema_v4/scripts/kal_v7.txt
Exit 0 = it is a story.
"""
import re
import sys
from pathlib import Path

CONCRETE = {"gari", "gariyan", "darwaza", "darwaze", "chaabi", "parchi", "phone", "kapda",
            "dhool", "haath", "haathon", "aankh", "aankhein", "deewar", "ustaad", "plate",
            "paisa", "kamra", "kamre", "ghar", "kachra", "danda", "aag", "jeb", "bonnet",
            "shutter", "torch", "spanner", "gali", "dukaan", "raste", "chai", "chawal",
            "salan", "mayyat", "kandha", "abbu", "ammi", "biwi", "bachay", "beta", "beti",
            "dashboard", "workshop", "almari", "khana", "scooter", "bike", "tayar", "note", "screen",
            "kaaghaz", "kaagaz", "pencil", "lifafa", "card"}
WANT = r"\b(chahiye|chahiya|chahta|chahti|mangta|mangti|laana|lena hai|chahiye tha)\b"
SPEECH = r"\b(kaha|kahi|kahe|bola|boli|kehta|kehti|poocha|pooch|likha|likhi|jawab)\b"
REFUSAL = r"\b(nahi|nahin|mat|kal aa|baad me|abhi nahi|ruk|rehne do)\b"
ACTION = (r"\b(uthaya|uthai|khola|band|rakh|rakhi|rakha|badhaya|diya|di|uthi|gaya|gayi|"
          r"aaya|aayi|likh|phenka|kheencha|jhuka|sata|chalaya|bandh|tod|maine|mujhe)\b")
DECISION = r"\b(chahiye|karunga|jaunga|aaj|abhi|khud|se\b[^.!?]{0,12}\bkar)\b"
REVERSAL = r"\b(lekin|magar|par|phir bhi|haalaanke|jab ke)\b"
CHANGE_ACTION = (r"\b(rakh diya|rakhi|de diya|diya|badhaya|muskura|sar uthaya|uthaya|"
                 r"bola|kaha|likh)\b")


def sents(text):
    t = re.sub(r"\s+", " ", text).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+", t) if s.strip()]


def toks(s):
    return re.findall(r"[A-Za-z'’\-]+", s.lower())


def main():
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    ss = sents(text)
    low = text.lower()
    words = toks(text)
    n = len(words)
    head = " ".join(words[:40])
    tail = " ".join(words[-40:])
    rows = []

    def gate(name, ok, weight, detail):
        rows.append((name, ok, weight, detail))

    # 1. point of attack: the film opens on a decision, not on the cause
    gate("Point of attack on a decision", bool(re.search(DECISION, " ".join(words[:30]))),
         10, "first 30 words")

    # 2. someone wants something, out loud, early
    gate("A want is stated", bool(re.search(WANT, head)), 10, "first 40 words")

    # 3. an opposing voice that refuses
    gate("An opposing voice refuses", bool(re.search(REFUSAL, head)), 10, "first 40 words")

    # 4. characters speak
    speeches = len(re.findall(SPEECH, low))
    gate("Dialogue (>=2 speech acts)", speeches >= 2, 8, f"{speeches} speech acts")

    # 5. protagonist acts, not just observes
    acts = len(re.findall(ACTION, low))
    gate("Protagonist takes action", acts >= 4, 10, f"{acts} action verbs")

    # 6. a choice that costs something
    cost = re.search(r"\b(raat bhar|chup|chhod|phir bhi|khud|bina)\b", low)
    gate("A choice under pressure", bool(cost), 8, cost.group(0) if cost else "none")

    # 7. a reversal after the halfway mark
    half = int(len(words) * 0.5)
    gate("A turn after halfway", bool(re.search(REVERSAL, " ".join(words[half:]))),
         8, "second half")

    # 8. the ending is an act by the other person, not a saying
    close = " ".join(toks(" ".join(ss[-6:]))) if ss else ""
    hitc = re.search(CHANGE_ACTION, close)
    gate("Ends on an action", bool(hitc), 10, hitc.group(0) if hitc else "none")

    # 9. S4 - the film opens and closes on the same thing
    first_bg = set(zip(words[:18], words[1:19]))
    tail_words = words[int(len(words) * 0.7):]          # the callback can land before the moral
    last_bg = set(zip(tail_words, tail_words[1:]))
    loop = first_bg & last_bg
    gate("S4 opens and closes on one phrase", bool(loop), 8,
         " / ".join(" ".join(x) for x in list(loop)[:2]))

    # 10. C4 - one object, repeated
    counts = {c: words.count(c) for c in CONCRETE if words.count(c) >= 1}
    top = max(counts.values()) if counts else 0
    gate("C4 one object carries the film", top >= 3, 8, f"max repeat {top}")

    # 11. concrete density
    conc = sum(1 for s in ss if set(toks(s)) & CONCRETE)
    density = conc / max(1, len(ss))
    gate("Concrete noun in >=60% of lines", density >= 0.6, 6, f"{density*100:.0f}%")

    # 12. it is not a second-person lecture
    you = len(re.findall(r"\b(tu|tune|tera|teri|tujhe|tum|tumne|tumhara|tumhe)\b", low))
    gate("Not a second-person rant", you <= 3, 12, f"{you} x 'you'")

    # 13. a moral that is actually stated (the format he asked for: story + moral)
    tailw = " ".join(words[-30:])
    moral = re.search(r"\b(nahi karte|nahi karta|nahi de sakte|nahi de sakta|rukega|"
                      r"nahi rukta|intezaar nahi|mat do|mat karo|chhod do|sabak|lesson|"
                      r"moral|yaad rakh|seekh)\b", tailw)
    gate("A moral is stated at the end", bool(moral), 8, moral.group(0) if moral else "none")

    # 14. the moral names the object, so it can't float free of the story
    gate("The moral names the object", bool(set(words[-30:]) & CONCRETE), 8,
         ", ".join(sorted(set(words[-30:]) & CONCRETE))[:40])

    score = min(100, 100 - sum(w for _, ok, w, _ in rows if not ok))
    print(f"\nFILE {path.name}   {n} words   {len(ss)} sentences")
    print("=" * 74)
    for name, ok, w, detail in rows:
        if w == 0:
            continue
        print(f"{'PASS' if ok else 'FAIL'}  {name:38} {'-' + str(w) if not ok else '':4}  {detail}")
    print("=" * 74)
    verdict = "STORY" if score >= 80 else "NOT A STORY"
    print(f"SCORE {max(0, score)}/100  ->  {verdict}\n")
    return 0 if score >= 80 else 1


if __name__ == "__main__":
    sys.exit(main())
