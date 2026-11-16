#!/usr/bin/env python3
"""Rebuild production/account1_ep01/vo_full/*.wav from the base64 blob.

The voice clips are gzipped+base64'd inside narration_b64.json so CI has the
performance without the binary WAVs living in git.
"""
from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
BLOB = BASE / "narration_b64.json"
OUT = BASE / "vo_full"


def main() -> None:
    data = json.loads(BLOB.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    wrote = 0
    for name, payload in sorted(data["clips"].items()):
        path = OUT / f"{name}.wav"
        if path.exists():
            continue
        path.write_bytes(gzip.decompress(base64.b64decode(payload)))
        wrote += 1
    total = len(list(OUT.glob("b*.wav")))
    print(f"restored {wrote} clip(s); {total}/{len(data['clips'])} narration files present")
    missing = sorted(set(data["clips"]) - {p.stem for p in OUT.glob("b*.wav")})
    if missing:
        raise SystemExit(f"missing after restore: {missing}")


if __name__ == "__main__":
    main()
