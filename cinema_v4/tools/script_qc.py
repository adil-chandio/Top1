#!/usr/bin/env python3
"""MONARCH script QC — checks a Roman-Urdu script for AI-slop tells + retention gates.

Built from:
  refs/humanizer_26_tells.md   (blader/humanizer, MIT)  -> structural tells
  refs/slop_lexicon.json       (instagram-agent-skill, MIT) -> stock words
  refs/three_layer_hook.md     (vyralcontent, MIT) -> hook layers

Usage:  python3 script_qc.py script.txt --duration 45
Exit code 0 = pass, 1 = fail (any hard gate).
"""
import json, re, sys, statistics
from pathlib import Path

HARD_CLICHES = ["sapne dekho", "mehnat karo", "manzil", "safar", "kamyabi",
                "positive soch", "never give up", "khud par bharosa",
                "zindagi ek test", "kamyab hona hai"]
CTA_PATTERNS = [r"\bcomment\s+(karo|karein|karo na)\b", r"\bfollow\s+(karo|karein)\b",
                r"\bshare\s+(karo|karein)\b", r"\btag\s+(karo|karein)\b",
                r"\blike\s+(karo|karein)\b", r"link\s+bio"]
DISFLUENCY = ["main—", "yaar", "matlab", "dekho", "hmm", "uh", "arey", "bas—", " na,", "chalo", "toh ", "haan"]
ABSTRACT = ["kamyabi", "manzil", "safar", "koshish", "jazba", "himmat",
            "khudi", "shaksiat", "taraqqi", "positive", "energy"]
# English desk-words that stand in for a real prop. His bar: gari, ghar, snaps,
# khana, danda, kachra, aag, phone - objects you can point a camera at.
JARGON = ["doc", "document", "line", "my project", "mindset", "journey",
          "concept", "content", "my brand", "my goals", "growth", "hustle", "vibe"]
# "Main darta hoon" = the writer telling you the feeling. Behaviour, not label.
EMOTION_LABELS = [r"\bmain\b[^.!?]{0,24}\b(darta|dar\s+lagta|udaas|khush|pareshan|akela)\b",
                  r"\bmujhe\b[^.!?]{0,20}\b(dar|khushi|ghussa|afsos)\b",
                  r"\bmain\b[^.!?]{0,20}\b(thak|bor|khali)\b\s*(hua)?\s*(hoon|tha)\b"]


def sentences(text: str):
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?…])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def words(s: str):
    return [w for w in re.findall(r"[A-Za-z'’\-]+", s) if w]


def main():
    p = Path(sys.argv[1])
    dur = 45.0
    if "--duration" in sys.argv:
        dur = float(sys.argv[sys.argv.index("--duration") + 1])
    register = "film"
    if "--register" in sys.argv:
        register = sys.argv[sys.argv.index("--register") + 1]
    text = p.read_text(encoding="utf-8")
    raw = text.lower()

    sents = sentences(text)
    wc = len(words(text))
    lens = [len(words(s)) for s in sents] or [0]
    paceeya = wc / dur

    # --- tells -------------------------------------------------------------
    triads = []
    for i in range(len(sents) - 2):
        chunk = sents[i:i + 3]
        if not all(len(words(s)) <= 4 for s in chunk):
            continue
        # anaphora (same opening word 3x) is a device, a slop triad is not
        # anaphora = the same word repeated at the head of neighbouring lines.
        # A slop triad needs three *different* parallel items; a run where any two
        # lines open on the same word is anaphora, which is a device, not a tell.
        # anaphora repeats the head word, epiphora repeats the tail ("Kaam kal.
        # Call kal. Maafi kal."). Both are devices. A slop triad has neither.
        firsts = [words(s.lower())[0] if words(s) else "" for s in chunk]
        lasts = [words(s.lower())[-1] if words(s) else "" for s in chunk]
        if len(set(firsts)) < 3 or len(set(lasts)) < 3:
            continue
        triads.append(" / ".join(chunk))

    # A short fragment is HIS device (see SCRIPT_TU_STYLE: "Ammi. Biwi. Bachay. Andar.").
    # It only reads as slop when the *final* line is a bare fragment - the fake-artistic
    # closer (humanizer tell #2). So gate the closer, not the device.
    fragments = [sents[-1]] if sents and len(words(sents[-1])) <= 2 else []
    cliches = [c for c in HARD_CLICHES if c in raw]
    ctas = [pat for pat in CTA_PATTERNS if re.search(pat, raw)]
    abstract = [a for a in ABSTRACT if re.search(rf"\b{a}\b", raw)]
    has_disfluency = any(d in raw for d in DISFLUENCY)
    NUMBER_WORDS = ["ek", "do", "teen", "chaar", "paanch", "che", "saat", "aath",
                    "nau", "das", "bees", "sau", "hazaar", "saal", "minute", "baarah"]
    numbers = sorted({*re.findall(r"\b\d+\b", text),
                      *(w for w in NUMBER_WORDS if re.search(rf"\b{w}\b", raw))})
    hooks = len(words(sents[0])) if sents else 0
    variance = statistics.pstdev(lens) if len(lens) > 1 else 0
    shouts = re.findall(r"\b[A-Z]{4,}\b", text)
    jargon = [j for j in JARGON if re.search(rf"\b{re.escape(j)}\b", raw)]
    emotion = [e for e in EMOTION_LABELS if re.search(e, raw)]

    # --- score -------------------------------------------------------------
    score = 100
    rows = []

    def gate(name, ok, weight, detail):
        nonlocal score
        if not ok:
            score -= weight
        rows.append((name, "PASS" if ok else "FAIL", f"-{weight}" if not ok else "", detail))

    gate("Hook <= 6 words", hooks <= 6, 8, f"{hooks} words")
    gate("No forced triads", not triads, 12, triads[0] if triads else "")
    frag_ok = (not fragments) or (len(fragments) == 1 and sents and fragments[0] == sents[0])
    gate("No fragment closer", frag_ok, 8, fragments[0] if fragments else "")
    gate("No banned cliches", not cliches, 12, ", ".join(cliches))
    gate("No CTA bait", not ctas, 10, ", ".join(ctas))
    if register == "voice-note":
        gate("Disfluency present", has_disfluency, 8, "insaan ki zubaan")
    gate(">=2 concrete numbers", len(numbers) >= 2, 8, f"{len(numbers)} numbers")
    gate("Sentence variance >= 3", variance >= 3, 6, f"{variance:.1f}")
    gate("Abstract nouns <= 1", len(abstract) <= 1, 8, ", ".join(abstract))
    gate("Pace 2.6-3.6 wps", 2.6 <= paceeya <= 3.6, 6, f"{paceeya:.2f} wps")
    gate("Word count 120-175", 120 <= wc <= 175, 6, f"{wc} words")
    gate("No desk-word props", len(jargon) <= 1, 12, ", ".join(jargon))
    gate("Behaviour, not emotion", not emotion, 12, f"{len(emotion)} label(s)")

    print(f"\nFILE: {p.name}   duration target: {dur}s   words: {wc}   sentences: {len(sents)}")
    print("-" * 74)
    for name, st, w, detail in rows:
        print(f"{st:4}  {name:24} {w:4}  {detail[:40]}")
    print("-" * 74)
    verdict = "PASS" if score >= 80 else "FAIL"
    print(f"SCORE {score}/100  ->  {verdict}\n")
    if shouts:
        print("note: shouted words:", ", ".join(shouts))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
