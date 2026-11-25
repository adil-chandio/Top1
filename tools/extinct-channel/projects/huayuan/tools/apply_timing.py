#!/usr/bin/env python3
"""
Inject the script's timing into the film.

`v3_script.py` decides WHEN everything happens; `film_v3.js` must not decide it a second
time. This reads the dump and rewrites exactly two things in place:

  * SCRIPT_CUES / SCRIPT_CLAIMS   (HUD windows, already resolved to frames)
  * the SHOTS frame map           ([f0, f1, scene, cam, mm] rows)

Re-run after any change to MEASURED audio, then re-preflight. If you find yourself typing a
frame number into film_v3.js by hand, this file is the thing you actually wanted.
"""
import json
import re
import sys

DUMP = "/tmp/huayuan_v3_script.json"
FILM = "film_v3.js"

SCENE_CAM = {
    # (scene, size) -> (film shot name, focal length)
    ("stone", "ECU"): ("ecu", 50),
    ("life", "WS"): ("rad1_ms", 35),
    ("life", "CU"): ("opa_cu", 85),
    ("life", "MS"): ("hal_mcu", 50),
    ("crisis", "EWS"): ("pressure", 14),
    ("crisis", "WS"): ("relation", 28),
    ("crisis", "MS"): ("hal_mcu", 50),
    ("crisis", "CU"): ("rad1_ecu", 85),
    ("crisis", "ECU"): ("lastlight", 100),
    ("witness", "EWS"): ("ews", 35),
    ("witness", "WS"): ("wide", 24),
    ("witness", "MS"): ("ms", 35),
    ("witness", "CU"): ("cu", 50),
    ("witness", "MCU"): ("mcu", 85),
    ("witness", "ECU"): ("ecu2", 100),
    ("return", "WS"): ("return", 28),
    ("return", "MS"): ("doubt", 35),
    ("return", "CU"): ("rad1_cu", 50),
    ("return", "ECU"): ("lastlight", 100),
}
# the return sequence walks a lens ladder of its own; index by shot order within the scene
RETURN_LADDER = [("return", 28), ("return_b", 50), ("opa_mcu", 85), ("doubt", 35), ("rad1_cu", 50)]
CLOSE_CAM = ("close", 24)


def main() -> int:
    d = json.load(open(DUMP))
    src = open(FILM).read()

    cues = json.dumps(d["cues"], ensure_ascii=False, separators=(",", ":"))
    claims = json.dumps(d["claims"], ensure_ascii=False, separators=(",", ":"))
    src, n1 = re.subn(r"const SCRIPT_CUES = .*?;", f"const SCRIPT_CUES = {cues};", src, count=1, flags=re.S)
    src, n2 = re.subn(r"const SCRIPT_CLAIMS = .*?;", f"const SCRIPT_CLAIMS = {claims};", src, count=1, flags=re.S)

    # `draw()` switches two scene GRAPHS (`sea`, `lab`); the script names five SEQUENCES.
    # Writing the sequence name into the set field blanked both graphs and rendered an empty
    # frame — the exact class of bug the contact sheet cannot see.
    SET_OF = {"stone": "slab", "witness": "slab", "life": "sea", "crisis": "sea", "return": "sea"}
    rows, ret_i = [], 0
    for s in d["shots"]:
        if s.get("note", "").startswith("the last shot"):
            cam, mm = CLOSE_CAM
        elif s["scene"] == "return":
            cam, mm = RETURN_LADDER[min(ret_i, len(RETURN_LADDER) - 1)]
            ret_i += 1
        else:
            cam, mm = SCENE_CAM[(s["scene"], s["size"])]
        rows.append(f"  [{s['f0']:>4},{s['f1']:>4}, '{SET_OF[s['scene']]}', '{cam}', {mm}],")
    body = "const SHOTS = [\n" + "\n".join(rows) + "\n];"
    src, n3 = re.subn(r"const SHOTS = \[.*?\n\];", body, src, count=1, flags=re.S)

    open(FILM, "w").write(src)
    print(f"cues {'OK' if n1 else 'MISS'} · claims {'OK' if n2 else 'MISS'} · shots {'OK' if n3 else 'MISS'} "
          f"({len(d['shots'])} shots, {len(d['cues'])} cues, {len(d['claims'])} claims)")
    return 0 if (n1 and n2 and n3) else 1


if __name__ == "__main__":
    sys.exit(main())
