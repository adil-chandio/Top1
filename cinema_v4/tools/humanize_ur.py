#!/usr/bin/env python3
"""humanize_ur.py - blader/humanizer's 26 patterns, ported to Roman Urdu, plus voice match.

The skill (cinema_v4/vendor/humanizer, MIT v4.0.0) is prose for a model to read. This is the
same rule set as something that can fail a build.

Two modes:
  default        mark every tell, strongest first, and score the script
  --voice FILE   a voice sample overrides the pattern list (SKILL.md "Voice"): the
                 script must sit inside the sample's rhythm, not inside a house style.

Usage:
  python3 humanize_ur.py cinema_v4/scripts/kal_v4.txt --voice cinema_v4/scripts/VOICE_TU_CUT_A.txt

Exit 0 = clean, 1 = a hard pattern fired.
"""
import re
import sys
import statistics
from pathlib import Path

# --------------------------------------------------------------------------- lexicons
# §1 - the hinge. "Sawaal yeh nahi ke X. Sawaal yeh hai ke Y." is the Urdu form.
P1 = [
    (r"sawaal yeh nahi", "sawaal yeh nahi ... sawaal yeh hai"),
    (r"baat yeh nahi", "baat yeh nahi ... baat yeh hai"),
    (r"masla yeh nahi", "masla yeh nahi ... masla yeh hai"),
    (r"\bsirf\b[^.!?]{0,30}\bnahi\b", "sirf X nahi"),
    (r"\bnahi\b[^.!?]{0,24}\bbalki\b", "nahi X, balki Y"),
    (r"\bnahi\b[^.!?]{0,24}\bbalke\b", "nahi X, balke Y"),
    (r"\byeh\b[^.!?]{0,16}\bnahi\b[^.!?]{0,12}\byeh\b", "yeh X nahi, yeh Y"),
    (r"\bnahi\s+(ke|keh)\b", "nahi ke ... balke"),
    (r"\bisme\s+shak\s+nahi\b", "isme shak nahi"),
]
# §3 - sayings that sound deep. True of everyone, so it lands on no one.
P3 = [
    (r"\bzindagi\b", "zindagi"),
    (r"\bhar\s+(cheez|banda|aadmi|roz|waqt|din)\b", "har cheez / har banda"),
    (r"\bsab\s+log\b", "sab log"),
    (r"\bsach\s+yeh\s+(hai|ha)\b", "sach yeh hai"),
    (r"\basli\s+baat\b", "asli baat"),
    (r"\bkoi\s+din\b", "koi din"),
    (r"\bwaqt\s+(ka|ki)\s+", "waqt ka ..."),
    (r"\bkabhi\s+nahi\s+(aata|aayega|badalta|milti)\b", "kabhi nahi aata"),
    (r"\bkhud\s+se\s+(jeet|haar)\b", "khud se jeet"),
]
# §4 - staged run-up before the point.
P4 = [
    (r"^dekho[,!.]?\s", "dekho,"),
    (r"^suno[,!.]?\s", "suno,"),
    (r"\bchalo\s+(shuru|ab)\b", "chalo shuru"),
    (r"\baaj\s+(main|hum)\s+(aapko|tumhe|tujhe)\b", "aaj main aapko batata hoon"),
    (r"\bpehle\s+yeh\s+samajh\b", "pehle yeh samajh lo"),
    (r"\bseedhi\s+si\s+baat\s+hai\b", "seedhi si baat hai"),
]
# §5 - arguing with no one.
P5 = [
    (r"\bkoi\s+kahe\s+(to|ke)\b", "koi kahe to"),
    (r"\blog\s+kehte\s+hain\b", "log kehte hain"),
    (r"\baksar\s+log\b", "aksar log"),
    (r"\bmain\s+yeh\s+nahi\s+keh\s+raha\b", "main yeh nahi keh raha"),
    (r"\baap\s+poochhenge\b", "aap poochhenge"),
    (r"\bkoi\s+yeh\s+nahi\s+kehta\b", "koi yeh nahi kehta"),
]
# §12 - overused AI words, Roman Urdu equivalents of "delve/leverage/robust".
P12 = ["maqsad", "aham", "manzil", "safar", "kamyabi", "kamyab", "jazba", "hausla",
       "khudi", "shaksiat", "taraqqi", "badlaav", "asliyat", "zaroorat", "ehmiyat",
       "koshish", "musalman", "positive", "energy", "journey", "growth", "mindset",
       "transform", "impact", "vision", "mission"]
# §13 - inflated significance.
P13 = [
    (r"\bsab\s+se\s+(aham|bada)\b", "sab se aham"),
    (r"\bnaya\s+daur\b", "naya daur"),
    (r"\bsirf\s+shuruaat\b", "sirf shuruaat hai"),
    (r"\bhistory\s+badal\b", "history badal"),
    (r"\byeh\s+ek\s+turning\s+point\b", "turning point"),
    (r"\bdaur\s+badal\s+raha\b", "daur badal raha hai"),
]
# §15 - shallow -ing phrases ("karte hue").
P15 = [(r"\b\w+te\s+hue\b", "karte hue"), (r"\b\w+ti\s+hue\b", "karti hui")]
# §16 - sales language.
P16 = [(r"\bmuft\b", "muft"), (r"\bfree\b", "free"), (r"\baaj\s+hi\b", "aaj hi"),
       (r"\blimited\b", "limited"), (r"\boffer\b", "offer"), (r"\bdiscount\b", "discount"),
       (r"\bab\s+available\b", "ab available"), (r"\bjaldi\s+karo\b", "jaldi karo")]
# §17 - borrowed authority with no citation.
P17 = [(r"\bresearch\s+(kehti|kehta|se\s+pata)\b", "research kehti hai"),
       (r"\bstud(y|ies)\s+show", "studies show"),
       (r"\bexperts?\s+kehte\b", "experts kehte hain"),
       (r"\bscience\s+kehti\b", "science kehti hai"),
       (r"\bdata\s+batata\b", "data batata hai"),
       (r"\bproven\b", "proven")]
# §22 - chatbot residue.
P22 = [(r"\bbilkul\b", "bilkul"), (r"\bumeed\s+hai\b", "umeed hai"),
       (r"\bzaroor\s+(madad|help)\b", "zaroor madad karega"),
       (r"\bagar\s+aapko\s+koi\b", "agar aapko koi sawaal ho"),
       (r"\bmain\s+yahan\s+hoon\b", "main yahan hoon"),
       (r"\bmadad\s+karega\b", "madad karega")]
# §23 - knowledge-limit disclaimers.
P23 = [(r"\bmere\s+paas\s+(data|maloomat)\s+nahi\b", "mere paas data nahi"),
       (r"\bmujhe\s+yaqeen\s+nahi\b", "mujhe yaqeen nahi"),
       (r"\bmain\s+guess\b", "main guess")]
# §25 - writing about the document.
P25 = [(r"\bis\s+script\s+me\b", "is script me"),
       (r"\bneeche\s+diya\b", "neeche diya gaya"),
       (r"\bupar\s+likha\b", "upar likha"),
       (r"\bjaise\s+ke\s+hum\s+ne\s+dekha\b", "jaise ke hum ne dekha")]

HARD = {1, 2, 3, 6, 12, 13, 16, 22}
NAMES = {
    1: "Not X but Y", 2: "One-line closer / dramatic fragment", 3: "Sayings that sound deep",
    4: "Staged run-up", 5: "Arguing with no one", 6: "Forced triads",
    7: "Repeated sentence openings", 8: "Dashes as universal connector",
    9: "Stacked qualifiers", 10: "Hyphenated pairs", 11: "Passive / missing subject",
    12: "Overused AI words", 13: "Inflated significance", 14: "Vague connection",
    15: "Shallow -ing phrases", 16: "Sales language", 17: "Borrowed authority",
    18: "Avoiding is/are/has", 19: "Bold as decoration", 20: "Decorative headings",
    21: "Curly quotation marks", 22: "Chatbot residue", 23: "Knowledge disclaimers",
    24: "Heading repeated in first line", 25: "Writing about the document",
    26: "Re-explaining what the reader knows",
}


def sents(text):
    t = re.sub(r"\s+", " ", text).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+", t) if s.strip()]


def words(s):
    return re.findall(r"[A-Za-z'’\-]+", s.lower())


def hit(pats, raw):
    out = []
    for p, label in pats:
        if re.search(p, raw, re.M):
            out.append(label)
    return out


def stats(sents_):
    lens = [len(words(s)) for s in sents_] or [0]
    w = [x for s in sents_ for x in words(s)] or [""]
    return {
        "n": len(sents_),
        "mean": statistics.mean(lens),
        "sd": statistics.pstdev(lens) if len(lens) > 1 else 0.0,
        "short%": 100.0 * sum(1 for x in lens if x <= 4) / len(lens),
        "longest": max(lens),
        "q%": 100.0 * sum(1 for s in sents_ if s.rstrip().endswith("?")) / max(1, len(sents_)),
        "ttr": len(set(w)) / max(1, len(w)),
        "wps_voice": 2.9,
    }


def scan(text, voice_stats=None):
    """Return [(pattern_no, labels)] for the text, strongest first."""
    raw = text.lower()
    ss = sents(text)
    found = []
    for num, res in [
        (1, hit(P1, raw)), (3, hit(P3, raw)), (4, hit(P4, raw)), (5, hit(P5, raw)),
        (12, [w for w in P12 if re.search(rf"\b{w}\b", raw)]),
        (13, hit(P13, raw)), (15, hit(P15, raw)), (16, hit(P16, raw)),
        (17, hit(P17, raw)), (22, hit(P22, raw)), (23, hit(P23, raw)), (25, hit(P25, raw)),
    ]:
        if res:
            found.append((num, res))
    if ss and len(words(ss[-1])) <= 3:
        found.append((2, [f"closer: \"{ss[-1]}\""]))
    triads = []
    for i in range(len(ss) - 2):
        c = ss[i:i + 3]
        if not all(len(words(x)) <= 4 for x in c):
            continue
        f = [words(x)[0] if words(x) else "" for x in c]
        l = [words(x)[-1] if words(x) else "" for x in c]
        if len(set(f)) < 3 or len(set(l)) < 3:
            continue
        triads.append(" / ".join(c))
    if triads:
        found.append((6, triads))
    opens = [words(x)[0] for x in ss if words(x)]
    rep = [opens[i] for i in range(2, len(opens)) if opens[i] == opens[i-1] == opens[i-2]]
    if rep:
        found.append((7, [f"'{w}' x3+" for w in dict.fromkeys(rep)]))
    dashes = len(re.findall(r"[—–]", text))
    if ss and dashes > max(2, len(ss) // 4):
        found.append((8, [f"{dashes} em-dashes in {len(ss)} sentences"]))
    if re.search(r"\b(shayad|mumkin)\b[^.!?]{0,15}\b(shayad|mumkin)\b", raw) or \
       re.search(r"\bthoda\s+sa\b|\bkuch\s+had\s+tak\b", raw):
        found.append((9, ["shayad ... mumkin"]))
    if text.count("**") >= 2:
        found.append((19, [f"{text.count('**')//2} bold spans"]))
    if re.search(r"[“”‘’]", text):
        found.append((21, ["curly quotes"]))
    bigrams = {}
    for x in ss:
        w = words(x)
        for i in range(len(w) - 1):
            bg = w[i] + " " + w[i+1]
            bigrams[bg] = bigrams.get(bg, 0) + 1
    reps = [b for b, n in bigrams.items() if n >= 3 and b.split()[0] not in
            {"ke", "ki", "ko", "se", "me", "mein", "hai", "tha", "aur", "woh"}]
    if reps:
        found.append((26, reps[:3]))
    found.sort(key=lambda x: x[0])
    return found


def main():
    path = Path(sys.argv[1])
    voice = None
    if "--voice" in sys.argv:
        voice = Path(sys.argv[sys.argv.index("--voice") + 1])
    text = path.read_text(encoding="utf-8")
    ss = sents(text)
    st = stats(ss)

    exempt = set()
    if voice:
        exempt = {n for n, _ in scan(voice.read_text(encoding="utf-8"))}

    found = [(n, lab) for n, lab in scan(text)]
    for n, lab in found:
        mark = "HARD" if n in HARD else "soft"
        if n in exempt:
            mark = "QUIRK"
    print(f"\nFILE {path.name}   {len(ss)} sentences   {sum(len(words(x)) for x in ss)} words")
    print("=" * 78)
    if not found:
        print("no tells found")
    for n, lab in found:
        if n in exempt:
            mark = "QUIRK"
        elif n in HARD:
            mark = "HARD"
        else:
            mark = "soft"
        print(f"§{n:<3} {mark:5} {NAMES[n]}")
        for l in lab[:4]:
            print(f"        - {l}")

    fired = [n for n, _ in found if n in HARD and n not in exempt]
    soft = [n for n, _ in found if n not in HARD or n in exempt]

    if voice:
        vs = stats(sents(voice.read_text(encoding="utf-8")))
        print("\nVOICE MATCH  (sample = %s)" % voice.name)
        print(f"{'':16}{'script':>10}{'sample':>10}{'delta':>10}")
        rows = [("mean sent len", st["mean"], vs["mean"]),
                ("sentence sd", st["sd"], vs["sd"]),
                ("short <=4w %", st["short%"], vs["short%"]),
                ("question %", st["q%"], vs["q%"]),
                ("longest sent", st["longest"], vs["longest"]),
                ("type/token", st["ttr"], vs["ttr"])]
        drift = 0
        for name, a, b in rows:
            d = a - b
            tol = max(1.0, abs(b) * 0.45)
            off = "  <-- off voice" if abs(d) > tol else ""
            if off:
                drift += 1
            print(f"{name:16}{a:>10.2f}{b:>10.2f}{d:>+10.2f}{off}")
        print(f"drift: {drift} of {len(rows)} voice axes")

    score = 100 - 12 * len(fired) - 3 * len(soft)
    score = max(0, score)
    print("=" * 78)
    if exempt:
        print(f"exempt (your own voice sample does it too): {sorted(exempt)}")
    print(f"hard patterns fired: {fired if fired else 'none'}")
    print(f"soft patterns: {soft if soft else 'none'}")
    print(f"SCORE {score}/100 -> {'PASS' if not fired else 'FAIL'}\n")
    return 0 if not fired else 1


if __name__ == "__main__":
    sys.exit(main())
