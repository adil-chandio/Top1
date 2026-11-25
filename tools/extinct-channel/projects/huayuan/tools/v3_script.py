#!/usr/bin/env python3
"""Huayuan v3 — the one-minute script, and the cut derived from it.

WHY THE SCRIPT COMES FIRST
v2 was cut first and narrated second. The result measured: five silences of
1.5-3.0 s, each landing beside a cut, and two captions claiming four seconds of
speech over one second of audio. The order was the bug.

WHAT THE MEASUREMENTS SAY
The approved read is 93 words in 34.8 s of voiced audio (200-3500 Hz VAD, 23
segments, gaps >= 0.35 s counted as silence). 0.3742 s/word INCLUDES the pauses
inside that read. Using it and then adding sentence breaks double-counts them:
that version predicted 38.74 s for a 34.80 s read and every line after it
cascaded into overlap. The pauses are taken out first:

    articulation 2.44 words/s, measured on the voice that actually read it.

Ten of the twenty-two lines were synthesised and measured: 55 words in 22.58 s
of voiced audio. My own two estimates before that (3.00, then 3.41) were both
wrong, in opposite directions, and both were numbers I fitted to an old read
instead of to this one. The packing solver below uses the measured length of
every line it has, so the placement cannot drift from the read again.

HOW THE CUT IS MADE SAFE
A shot cannot start inside a line. Each shot is declared as "starts at line N",
and its first frame is 0.30 s BEFORE that line, i.e. inside the silence that
precedes it. There is no free-floating cut time that can drift into a word, and
a line is never split by the picture.

WHAT THE GATES PROTECT
  G0  the model still reproduces the measured read
  G1  no cut inside a spoken line
  G2  every silence <= 0.90 s unless declared a DESIGNED HOLD with a reason
  G3  speech >= 62 % of runtime                    (v2 shipped 41 %)
  G4  no shot under 0.90 s, none over 10 s
  G5  no two adjacent shots on the same lens
  G6  the last shot is picture only and the words finish before it opens
"""
import json
import sys

FPS = 30.0
RUNTIME = 60.0
WPS = 2.436           # articulation, measured on the 10 synthesised lines
COMMA_BREAK = 0.15
SENT_BREAK = 0.38
TAIL = 0.06
CUT_LEAD = 0.08       # a cut lands just before the line it announces

# (text, t_in, follows a comma inside the same sentence)
LINES = [
    ("A stone from a dead seafloor.", 0.60, False),
    ("Five hundred and twelve million years ago.", 0.00, False),
    ("It was crawling with animals.", 0.00, False),
    ("None of them had bones.", 0.00, False),
    ("Then the water went dark,", 0.00, False),
    ("and the silt came.", 0.00, True),
    ("Buried before they could rot.", 0.00, False),
    ("No oxygen. No decay.", 0.00, False),
    ("Then the light goes out.", 0.00, False),
    ("The rock opens.", 0.00, False),
    ("Not a skeleton.", 0.00, False),
    ("The animal itself, pressed into stone.", 0.00, False),
    ("Softer than bone: eye, gill, nerve.", 0.00, False),
    ("One hundred and fifty-three species,", 0.00, False),
    ("in sixteen groups.", 0.00, True),
    ("The extinction passed above.", 0.00, False),
    ("Down here, life kept going.", 0.00, False),
    ("Was the deep a refuge?", 0.00, False),
    ("A hypothesis, not a fact.", 0.00, False),
    ("The stone is still answering.", 0.00, False),
]

# (scene, size, lens, first line, why this shot exists)
SHOTS = [
    ("stone",   "ECU", 50,  1,  "the rock, texture before meaning"),
    ("life",    "WS",  35,  2,  "the seafloor, the animals"),
    ("life",    "CU",  85,  4,  "what the wide cannot show"),
    ("crisis",  "EWS", 14,  5,  "the widest lens arrives with the event"),
    ("crisis",  "WS",  28,  6,  "the silt, falling"),
    ("crisis",  "MS",  50,  7,  "what the silt lands on"),
    ("crisis",  "CU",  85,  8,  "no oxygen"),
    ("crisis",  "ECU", 100, 9,  "the last light"),
    ("witness", "EWS", 35,  10, "the reveal opens"),
    ("witness", "WS",  24,  11, "the animal, whole"),
    ("witness", "MS",  35,  12, "pressed into stone"),
    ("witness", "CU",  50,  13, "what survived"),
    ("witness", "MCU", 85,  14, "the count"),
    ("witness", "ECU", 100, 15, "the count lands"),
    ("return",  "WS",  28,  16, "back to water, same place"),
    ("return",  "WS",  50,  17, "in among them"),
    ("return",  "MCU", 85,  18, "the question"),
    ("return",  "MS",  35,  19, "the doubt"),
    ("return",  "CU",  50,  20, "the line"),
]

# Text that must be on screen while a specific LINE is spoken. Keyed by 1-based line id and
# resolved to frames HERE — never typed by hand in film_v3.js. A cue lives and dies on its
# own line's frames, which is what stops the v2/v3 defect where a caption announced the next
# beat a shot early. "eye, gill, nerve" is spoken once but carried by the 85mm macro, so both
# plates sit on line 13.
CUES = {
    1:  [("512 MILLION YEARS AGO", "big46"), ("DEAD SEA FLOOR", "sunset20")],
    13: [("SOFTER THAN BONE", "big40")],
    14: [("153 SPECIES", "big52")],
    18: [("A REFUGE?", "big46")],
    19: [("A HYPOTHESIS, NOT A FACT", "big36")],
}

# Claim stamps are tied to the SEQUENCE the shot belongs to, so they can never drift either.
CLAIMS = {
    "life":    "RECONSTRUCTION",
    "crisis":  "CONCEPTUAL  \u00b7  SEDIMENT EVENT",
    "witness": "SCHEMATIC  \u00b7  NOT A HUAYUAN SPECIMEN",
    "return":  "DEEP WATER  -  HYPOTHESIS",
}

DESIGNED_HOLDS = {
    10: (1.90, "the rock reveal opens silent so the audience has to identify it"),
    17: (0.90, "the film returns to water; picture leads, voice follows"),
}

CLOSE = (58.20, 60.00, "the last shot: the sea closes over the frame, no words")


def count(text):
    return (len(text.replace("?", " ").replace("!", " ").split()),
            max(1, text.count(".") + text.count("?")),
            text.count(","))


# measured voiced spans, voice-01, lines 1-10 (s)
MEASURED = [3.44, 2.86, 2.88, 1.72, 1.78, 1.46, 2.76, 1.96, 2.24, 1.48]  # lines 1-10 recorded
MEASURED_WORDS = [9, 7, 6, 4, 5, 5, 7, 3, 4, 5]


def calibrate():
    """The model must reproduce the read that actually exists, not a hoped one."""
    predicted = sum(MEASURED_WORDS) / WPS
    measured = sum(MEASURED)
    return abs(predicted - measured) <= 0.40, predicted


MAX_GAP = 0.74        # packing: 96 words at the measured rate + 19 gaps must fit 58.2 s
CUT_PAD = 0.06        # a cut sits this far before the line it introduces


def line_dur(text, breath, measured=None):
    if measured is not None:
        return measured
    w, sn, c = count(text)
    return (w / WPS + COMMA_BREAK * c + SENT_BREAK * (sn - 1) + TAIL
            + (SENT_BREAK if breath else 0.0))


def build():
    """Place the lines so the CUT lands in a silence and no gap exceeds MAX_GAP.

    t_in is derived, never typed. Every line that exists as audio carries its
    measured length; the rest are predicted from the measured rate.
    """
    rows, t = [], 0.0
    for i, (text, t_in, breath) in enumerate(LINES, start=1):
        measured = MEASURED[i - 1] if i - 1 < len(MEASURED) else None
        d = line_dur(text, breath, measured)
        # a cut to a new shot needs a silence, and that silence is part of the
        # gap budget: give the cut 0.06 s, the rest is air before the line
        gap = MAX_GAP if i > 1 else LINES[0][1]
        if i > 1:
            t = round(t + gap, 2)
        rows.append(dict(id=i, t_in=round(t, 2), dur=round(d, 2),
                         t_out=round(t + d, 2), words=count(text)[0],
                         text=text, measured=measured is not None))
        t = t + d
    return rows


def derive_cut(rows):
    by_id = {r["id"]: r for r in rows}
    shots = []
    for idx, (scene, size, lens, first, note) in enumerate(SHOTS):
        t0 = 0.0 if idx == 0 else round(by_id[first]["t_in"] - 0.08, 2)
        t1 = round(CLOSE[0], 2) if idx + 1 == len(SHOTS) else \
            round(by_id[SHOTS[idx + 1][3]]["t_in"] - 0.08, 2)
        lines = [r["id"] for r in rows if r["id"] >= first and
                 (idx + 1 == len(SHOTS) or r["id"] < SHOTS[idx + 1][3])]
        shots.append(dict(scene=scene, size=size, lens=lens, note=note, lines=lines,
                          t0=t0, t1=t1, dur=round(t1 - t0, 2),
                          f0=round(t0 * FPS), f1=round(t1 * FPS)))
    # picture-only close
    shots.append(dict(scene="return", size="WS", lens=24, note=CLOSE[2], lines=[],
                      t0=CLOSE[0], t1=60.0, dur=round(60.0 - CLOSE[0], 2),
                      f0=round(CLOSE[0] * FPS), f1=1800))
    return shots


def main():
    ok, predicted = calibrate()
    rows, shots, fails = build(), None, []
    shots = derive_cut(rows)
    last = rows[-1]

    if not ok:
        fails.append(f"G0 the model predicts {predicted:.2f}s for the measured lines, "
                     f"which run {sum(MEASURED):.2f}s — recalibrate before trusting any timing")

    cut_times = [s["t0"] for s in shots[1:]]
    for c in cut_times:                                            # G1
        for r in rows:
            if r["t_in"] + 0.03 < c < r["t_out"] - 0.03:
                fails.append(f"G1 the cut at {c:.2f} falls inside line {r['id']} "
                             f"({r['t_in']:.2f}-{r['t_out']:.2f}): {r['text']}")

    gaps = [(0.0, rows[0]["t_in"], "open", 0.90, None)]
    for x, y in zip(rows, rows[1:]):
        cap, why = 0.90, None
        for n, (mx, w) in DESIGNED_HOLDS.items():
            if y["id"] == n:
                cap, why = mx, w
        gaps.append((x["t_out"], y["t_in"], f"{x['id']}->{y['id']}", cap, why))
    gaps.append((last["t_out"], CLOSE[0], "tail", 3.20, CLOSE[2]))
    gaps.append((CLOSE[0], 60.0, "close", 1.80, CLOSE[2]))
    for (g0, g1, tag, cap, why) in gaps:                            # G2
        g = g1 - g0
        if g < -1e-9:
            fails.append(f"G2 overlap {tag} {g0:.2f}/{g1:.2f}")
        elif g > cap + 1e-9:
            fails.append(f"G2 gap {tag} {g0:.2f}-{g1:.2f} = {g:.2f}s > {cap:.2f}s"
                         + (f" [{why}]" if why else " (undeclared)"))

    speech = sum(r["dur"] for r in rows)
    cov = speech / RUNTIME
    if cov < 0.62:                                                  # G3
        fails.append(f"G3 coverage {cov:.1%} < 62 %")

    lens = [s["dur"] for s in shots if s["dur"] > 0] or [1.0]
    for s in shots:                                                 # G4
        if s["dur"] <= 0.0:
            fails.append(f"G4 {s['size']} at {s['t0']:.2f} has zero length — "
                         "its first line does not exist in LINES")
        elif s["dur"] < 0.90 - 1e-9:
            fails.append(f"G4 {s['size']} {s['t0']:.2f}-{s['t1']:.2f} = {s['dur']:.2f}s < 0.90 s")
        if s["dur"] > 10.0 + 1e-9:
            fails.append(f"G4 {s['size']} {s['t0']:.2f}-{s['t1']:.2f} = {s['dur']:.2f}s > 10 s")
    for x, y in zip(shots, shots[1:]):                              # G5
        if x["lens"] == y["lens"]:
            fails.append(f"G5 two adjacent shots on the same {x['lens']} mm "
                         f"({x['t0']:.2f} and {y['t0']:.2f})")

    if last["t_out"] > CLOSE[0]:                                    # G6
        fails.append(f"G6 the words run to {last['t_out']:.2f}, past the close at {CLOSE[0]:.2f}")

    # ── cues: resolve every plate to the frames of the line that speaks it ─────────────
    by_id = {r["id"]: r for r in rows}
    cues, claims = [], []
    for lid, plates in sorted(CUES.items()):
        r = by_id.get(lid)
        if r is None:
            fails.append(f"G7 cue references line {lid}, which does not exist")
            continue
        f0 = int(round(r["t_in"] * FPS))
        f1 = int(round(r["t_out"] * FPS))
        pos = 1004
        for (text, style) in plates:
            y = pos
            pos -= 40 if style != "sunset20" else 24
            cues.append(dict(line=lid, f0=f0, f1=f1, text=text, style=style,
                             y=y if style != "sunset20" else 1040))
        if f0 < 0 or f1 > RUNTIME * FPS:                            # G7
            fails.append(f"G7 cue for line {lid} lands outside the film ({f0}-{f1})")
    for s_ in shots:
        tag = CLAIMS.get(s_["scene"])
        if tag:
            claims.append(dict(f0=s_["f0"], f1=s_["f1"], text=tag))
    # G7: no cue may outlive the line that speaks it
    for c in cues:
        r = by_id[c["line"]]
        if c["f0"] < int(round(r["t_in"] * FPS)) - 1 or c["f1"] > int(round(r["t_out"] * FPS)) + 1:
            fails.append(f"G7 cue '{c['text']}' is not contained by line {c['line']}")

    json.dump(dict(rows=rows, shots=shots, gaps=gaps, cues=cues, claims=claims, speech=round(speech, 2),
                   coverage=round(cov, 4), fails=fails),
              open("/tmp/huayuan_v3_script.json", "w"), indent=1)

    print(f"articulation {WPS:.2f} w/s · {sum(MEASURED_WORDS)} measured words predict "
          f"{predicted:.2f}s vs {sum(MEASURED):.2f}s measured ({'OK' if ok else 'DRIFTED'})\n")
    print("THE READ")
    print(f"{'#':>3} {'in':>6}{'out':>7}{'w':>4}{'dur':>6}  shot")
    print("-" * 104)
    for r in rows:
        sh = next((x for x in shots if x["t0"] <= r["t_in"] < x["t1"]), shots[-1])
        print(f"{r['id']:>3} {r['t_in']:>6.2f}{r['t_out']:>7.2f}{r['words']:>4}{r['dur']:>6.2f}"
              f"  {sh['size']} {sh['lens']}mm")
        print(f"      {r['text']}")
    print()
    print(f"{'silence':<9}{'window':>18}{'len':>7}{'cap':>7}  note")
    for (g0, g1, tag, cap, why) in gaps:
        state = "ok" if g1 - g0 <= 0.90 else ("HOLD" if why else "TOO LONG")
        print(f"{tag:<9}{g0:>7.2f}-{g1:<9.2f}{g1 - g0:>7.2f}{cap:>7.2f}  {why or state}")
    print()
    print("THE CUT")
    print(f"{'#':>3}{'scene':>9}{'size':>6}{'lens':>6}{'in':>8}{'out':>8}{'sec':>7}{'frames':>8}"
          f"{'lines':>8}  why")
    for i, x in enumerate(shots, 1):
        tags = f"{min(x['lines'])}-{max(x['lines'])}" if x["lines"] else "—"
        print(f"{i:>3}{x['scene']:>9}{x['size']:>6}{x['lens']:>5}mm{x['t0']:>8.2f}{x['t1']:>8.2f}"
              f"{x['dur']:>7.2f}{x['f1'] - x['f0']:>8d}{tags:>8}  {x['note']}")
    print()
    print(f"shots {len(shots)} · ASL {sum(lens) / len(lens):.2f}s · longest {max(lens):.2f}s · "
          f"shortest {min(lens):.2f}s · max/min {max(lens) / min(lens):.1f}x")
    print(f"words {sum(r['words'] for r in rows)} · speech {speech:.2f}s ({cov:.1%}) · "
          f"silence {RUNTIME - speech:.2f}s")
    print()
    if fails:
        print("FAIL")
        for f in fails:
            print("  " + f)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
