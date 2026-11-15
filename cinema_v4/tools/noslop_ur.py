#!/usr/bin/env python3
"""noslop_ur.py - petergyang/no-ai-slop's rules as an executable gate, Roman Urdu.

The skill is prose for an editor. This is the same checklist as something that can fail a build,
plus the one thing the skill cannot do by itself: it reads a voice sample first, because the
skill's own first principle is "preserve the writer's voice" and "leave strong human sentences
alone". A rule the writer's own work breaks is that writer's device, not slop.

One rule stays hard even then: the fake-profound kicker. A writer can end on a question or on a
thing. Nobody's voice needs to end on an aphorism.

Usage:
  python3 noslop_ur.py cinema_v4/scripts/kal_v6.txt --voice cinema_v4/scripts/VOICE_TU_CUT_A.txt
Exit 0 = clean, 1 = a hard pattern fired.
"""
import re
import sys
from pathlib import Path

# things a camera can point at - the portability test needs something to stand on
CONCRETE = {
    "gari", "gariyan", "darwaza", "darwaze", "chaabi", "parchi", "phone", "kapda",
    "dhool", "haath", "haathon", "aankh", "aankhein", "aankhon", "deewar", "ustaad",
    "plate", "paisa", "paisay", "kamra", "kamre", "ghar", "kachra", "danda", "aag",
    "jeb", "dashboard", "bonnet", "gali", "dukaan", "raste", "seat", "chai", "chawal",
    "salan", "mayyat", "kandha", "tasbeeh", "abbu", "ammi", "biwi", "bachay", "beta",
    "beti", "scooter", "bike", "tayar", "spanner", "rag", "note", "likha", "screen",
}
ABSTRACT_HINT = {"baat", "sach", "zindagi", "waqt", "lafz", "din", "kal", "haal", "safar",
                 "manzil", "kamyabi", "himmat", "himmat", "jazba", "soch", "yaqeen"}

P_BINARY = [(r"yeh\b[^.!?]{0,24}\bnahi\b[^.!?]{0,16}\b(yahi|yeh)\b[^.!?]{0,16}\bhai\b", "yeh X nahi, yeh Y hai"),
            (r"sawaal yeh nahi", "sawaal yeh nahi"),
            (r"baat yeh nahi", "baat yeh nahi"),
            (r"\bnahi\b[^.!?]{0,22}\bbalki\b", "nahi X balki Y"),
            (r"\bsirf\b[^.!?]{0,24}\bnahi\b", "sirf X nahi")]
P_THROAT = [(r"^dekho\b", "dekho,"), (r"^suno\b", "suno,"),
            (r"\bsach\s+bataun\b", "sach bataun"),
            (r"\bseedhi\s+si\s+baat\b", "seedhi si baat"),
            (r"\bmain\s+aapko\s+bata\b", "main aapko batata hoon")]
P_FAUX = [(r"\bjo\s+koi\s+nahi\s+batata\b", "jo koi nahi batata"),
          (r"\baksar\s+log\s+yahi\b", "aksar log yahi ghalati karte hain"),
          (r"\bpart\s+everyone\s+skips\b", "the part everyone skips"),
          (r"\byahi\s+woh\s+cheez\s+hai\s+jo\b", "yahi woh cheez hai jo")]
P_PUFF = [(r"\bsab\s+se\s+(ahem|bada)\b", "sab se ahem"),
          (r"\bnaya\s+daur\b", "naya daur"),
          (r"\bek\s+nayi\s+shuruaat\b", "ek nayi shuruaat"),
          (r"\bsabit\s+karta\s+hai\b", "sabit karta hai"),
          (r"\bhistory\s+badal\b", "history badal di")]
P_META = [(r"\byeh\s+baat\s+(ahem|zaroori)\s+hai\b", "yeh baat ahem hai"),
          (r"\bdhayan\s+do\b", "dhayan do"),
          (r"\bsamajh\s+lo\b", "samajh lo"),
          (r"\bas\s+you\s+can\s+see\b", "as you can see"),
          (r"\bkey\s+point\b", "key point"),
          (r"\bnote\s+karo\b", "note karo")]
P_WEASEL = [(r"\bresearch\s+(kehti|kehta)\b", "research kehti hai"),
            (r"\bstud(y|ies)\b", "studies"),
            (r"\bexperts?\b", "experts"),
            (r"\bbade\s+log\s+kehte\b", "bade log kehte hain"),
            (r"\bdata\s+batata\b", "data batata hai")]
P_RHET = [(r"\bsocho\s+zara\b", "socho zara"),
          (r"\bkya\s+aap\s+jante\b", "kya aap jante hain"),
          (r"\bkya\s+hua\s+agar\s+main\s+kahun\b", "what if I told you"),
          (r"\bplot\s+twist\b", "plot twist"),
          (r"\bimagine\s+kar\b", "imagine kar")]
P_RECAP = [(r"\baakhir\s+me\b", "aakhir me"), (r"\bkhulasa\b", "khulasa"),
           (r"\bto\s+yahi\b", "to yahi"), (r"\boverall\b", "overall"),
           (r"\bultimately\b", "ultimately"), (r"\bin\s+short\b", "in short")]
BANNED_WORDS = ["delve", "leverage", "utilize", "robust", "seamless", "holistic",
                "paradigm", "game changer", "transformative", "elevate", "harness",
                "tapestry", "realm", "beacon", "meticulous", "intricate", "paramount",
                "litreally", "basically", "truly", "fundamentally", "essentially"]


def sents(text):
    t = re.sub(r"\s+", " ", text).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+", t) if s.strip()]


def words(s):
    return re.findall(r"[A-Za-z'’\-]+", s.lower())


def hit(pats, raw):
    return [lbl for p, lbl in pats if re.search(p, raw, re.M)]


def scan(text):
    raw = text.lower()
    ss = sents(text)
    found = []

    for num, labels in [
        (1, hit(P_BINARY, raw) + hit(P_RHET, raw)),
        (2, hit(P_THROAT, raw) + hit(P_FAUX, raw)),
        (3, hit(P_PUFF, raw) + hit(P_WEASEL, raw)),
        (4, hit(P_META, raw)),
        (6, hit(P_RECAP, raw)),
        (7, [w for w in BANNED_WORDS if re.search(rf"\b{re.escape(w)}\b", raw)]),
    ]:
        if labels:
            found.append((num, labels))

    # dramatic fragmentation / robotic rhythm: 3+ consecutive sentences of <=3 words
    run, runs = 0, []
    for s in ss:
        run = run + 1 if len(words(s)) <= 3 else 0
        if run >= 3:
            runs.append(run)
    if runs:
        found.append((5, [f"{len(runs)} run(s) of 3+ short sentences"]))

    # colon reveal: a colon followed by a <=4 word tail
    col = []
    for m in re.finditer(r"([^.!?:]{0,40}):\s*([A-Za-z' ]{1,40})", text):
        head, tail = m.group(1), m.group(2)
        if re.search(r"\b(bola|boli|kaha|kahi|kehta|kehti|keh|kahe|kahega|kahegi|kahunga|poocha|pooch|likha|likhi|sawaal)\s*$", head.lower().strip()):
            continue          # dialogue: "Ustaad ne bola: kal aa jana."
        if 0 < len(tail.split()) <= 4:
            col.append(tail.strip())
    if col:
        found.append((8, [f"colon reveal: '{c}'" for c in col[:2]]))

    # em dashes
    dashes = len(re.findall(r"[—–]", text))
    if dashes > 2:
        found.append((9, [f"{dashes} em dashes"]))

    # the kicker: final sentence, short, no camera-pointable noun, an abstraction or aphorism
    if ss:
        last = ss[-1]
        lw = set(words(last))
        has_concrete = bool(lw & CONCRETE)
        has_abstract = bool(lw & ABSTRACT_HINT)
        is_question = last.rstrip().endswith("?")
        third_person = bool(re.search(r"\b(woh|wo|yeh|ye|log|duniya|kal|waqt|har)\b", last.lower()))
        first_person = bool(re.search(r"\b(main|hum|mujhe|maine|mujh)\b", last.lower()))
        timeless = bool(re.search(r"\b(hai|hain|hoga|hogi|hota|hoti|nahi|badle|badlenge)\b",
                                  last.lower()))
        if (len(words(last)) <= 10 and not has_concrete and not is_question
                and (has_abstract or third_person) and timeless and not first_person):
            found.append((10, [f'kicker: "{last}"']))

    # portability: a mid-script sentence with no concrete noun and no action verb
    portable = []
    for s in ss[:-1]:
        lw = set(words(s))
        if lw & CONCRETE:
            continue
        if re.search(r"\b(hai|hain|tha|thi|hota|hoti|hoga)\b", s.lower()) and \
                not re.search(r"\b(gaya|gayi|aaya|aayi|likha|diya|kiya|bola|uthaya|phenka|"
                              r"khola|band|rakha|daala|uthi|gira|padi)\b", s.lower()):
            portable.append(s)
    if portable:
        found.append((11, portable[:3]))

    found.sort(key=lambda x: x[0])
    return found


NAMES = {1: "Binary contrast / rhetorical setup", 2: "Throat-clearing / faux-insight setup",
         3: "Importance puffery / weasel attribution", 4: "Interpretive metadiscourse",
         5: "Dramatic fragmentation", 6: "Summary-recap ending", 7: "Banned words",
         8: "Colon reveal", 9: "Em dashes", 10: "Fake-profound kicker",
         11: "Portability test (no concrete noun, no action)"}
# a writer's own voice can own 5 and 11. nobody's voice owns 1, 2, 3, 6, 7, 10.
SOFT = {5, 9, 11}


def main():
    path = Path(sys.argv[1])
    voice = Path(sys.argv[sys.argv.index("--voice") + 1]) if "--voice" in sys.argv else None
    text = path.read_text(encoding="utf-8")
    exempt = {n for n, _ in scan(voice.read_text(encoding="utf-8"))} if voice else set()
    found = scan(text)

    print(f"\nFILE {path.name}   {len(sents(text))} sentences   "
          f"{len(words(text))} words   [{Path(__file__).parent.parent.parent.name}]")
    print("=" * 78)
    if not found:
        print("no patterns found")
    hard = []
    for n, labels in found:
        tag = "QUIRK" if n in exempt else ("soft " if n in SOFT else "HARD ")
        print(f"§{n:<3} {tag} {NAMES[n]}")
        for l in labels[:3]:
            print(f"        - {l}")
        if n not in SOFT and n not in exempt:
            hard.append(n)
    print("=" * 78)
    if exempt:
        print(f"exempt (the writer does it too): {sorted(exempt)}")
    print(f"hard: {hard if hard else 'none'}")
    print(f"RESULT {'PASS' if not hard else 'FAIL'}   ({len(hard)} hard pattern(s))\n")
    return 0 if not hard else 1


if __name__ == "__main__":
    sys.exit(main())
