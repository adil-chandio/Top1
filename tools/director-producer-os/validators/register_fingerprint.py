#!/usr/bin/env python3
"""
Register a completed production's `director-plan.json` into `catalog/production_fingerprints.json`
so future episodes automatically diverge from its world, staging, prop anchor, palette, hook, and HUD.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from anti_clone_validator import FINGERPRINTS_PATH, extract_fingerprint


def register_plan_fingerprint(
    plan_path: str,
    fingerprints_path: str = FINGERPRINTS_PATH,
    completed_date: str | None = None,
) -> dict[str, str]:
    with open(plan_path, "r", encoding="utf-8") as fh:
        plan = json.load(fh)
    fp = extract_fingerprint(plan)
    fp["format"] = plan.get("format", "9:16_short")
    fp["completed_date"] = completed_date or dt.date.today().isoformat()

    with open(fingerprints_path, "r", encoding="utf-8") as fh:
        ledger = json.load(fh)

    prods = [p for p in ledger.get("productions", []) if p.get("project_id") != fp["project_id"]]
    prods.append(fp)
    ledger["productions"] = prods

    with open(fingerprints_path, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, indent=2)
        fh.write("\n")
    return fp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register completed director-plan.json fingerprint")
    parser.add_argument("plan_json", help="Path to validated director-plan.json")
    args = parser.parse_args(argv)
    fp = register_plan_fingerprint(args.plan_json)
    print("[REGISTERED FINGERPRINT]", json.dumps(fp, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
