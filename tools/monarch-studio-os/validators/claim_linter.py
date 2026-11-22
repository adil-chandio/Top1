#!/usr/bin/env python3
"""Automated Claim-to-Script & Caption Linter + Privacy/Scorecard Validators.

Implements Sections C, E, Z, 5, and 6 of Monarch Studio OS:
  - Verifies 1-to-1 paragraph alignment between `narration.txt` and `claims.json`.
  - Blocks unsupported/overstated phrases across narration, launch copy, and SRTs.
  - Verifies every source ID referenced by a paragraph exists in `claims.json["sources"]`.
  - Scans repository files for leaked Google Drive IDs, secrets, or auto-publish hooks.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import List, Sequence


PRIVATE_TOKEN_PATTERNS = (
    re.compile(r"drive\.google\.com/file/d/[A-Za-z0-9_-]{20,}"),
    re.compile(r"docs\.google\.com/document/d/[A-Za-z0-9_-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"GOCSPX-[0-9A-Za-z_-]{20,}"),
    re.compile(r"ya29\.[0-9A-Za-z_-]{30,}"),
    re.compile(r"googleapis\.com/upload/youtube/v3/videos"),
)

BINARY_MEDIA_EXTS = {".mp4", ".mov", ".mkv", ".wav", ".mp3", ".flac", ".aac", ".m4a"}


def split_paragraphs(text: str) -> List[str]:
    return [p.strip() for p in re.split(r"\n\n+", text.strip()) if p.strip()]


def lint_script_against_claims(
    narration_text: str,
    claims_doc: dict,
    extra_texts: Sequence[str] = (),
) -> List[str]:
    errors: List[str] = []
    paras = split_paragraphs(narration_text)
    p_claims = claims_doc.get("paragraph_claims", [])
    if len(paras) != len(p_claims):
        errors.append(
            f"Paragraph count mismatch: narration has {len(paras)}, claims.json has {len(p_claims)}"
        )

    known_sources = {s["source_id"] for s in claims_doc.get("sources", [])}
    seen_indices = set()
    for item in p_claims:
        idx = item["paragraph_index"]
        seen_indices.add(idx)
        for sid in item.get("source_ids", []):
            if sid not in known_sources:
                errors.append(f"Paragraph {idx} cites unknown source_id {sid!r}")

    if seen_indices != set(range(len(paras))):
        errors.append("paragraph_claims indices must cover 0..N-1 contiguously")

    corpus = [("narration", narration_text)] + [(f"extra[{i}]", t) for i, t in enumerate(extra_texts)]
    for rule in claims_doc.get("forbidden_phrases", []):
        pat = re.compile(rule["pattern"], re.IGNORECASE)
        for label, txt in corpus:
            m = pat.search(txt)
            if m:
                errors.append(
                    f"Forbidden claim pattern {rule['pattern']!r} matched {m.group(0)!r} in {label}: {rule['reason']}"
                )
    return errors


def validate_scorecard(scorecard_doc: dict, min_pass_score: float = 85.0) -> List[str]:
    errors: List[str] = []
    scores = scorecard_doc.get("scores", {})
    computed = round(sum(float(v) for v in scores.values()), 2)
    declared = round(float(scorecard_doc.get("total_score", -1)), 2)
    if computed != declared:
        errors.append(f"Scorecard total mismatch: sum={computed} vs total_score={declared}")
    gates = scorecard_doc.get("gate_checks", {})
    expected_pass = (computed >= min_pass_score) and all(bool(v) for v in gates.values())
    if bool(scorecard_doc.get("passed")) != expected_pass:
        errors.append(f"Scorecard passed={scorecard_doc.get('passed')} disagrees with computed={expected_pass}")
    return errors


def scan_zero_trust_privacy(scan_roots: Sequence[Path]) -> List[str]:
    violations: List[str] = []
    for root in scan_roots:
        for p in sorted(root.rglob("*")):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            if p.suffix.lower() in BINARY_MEDIA_EXTS:
                violations.append(f"Binary media forbidden in Git tree: {p}")
                continue
            txt = p.read_text(encoding="utf-8", errors="ignore")
            for rx in PRIVATE_TOKEN_PATTERNS:
                m = rx.search(txt)
                if m:
                    violations.append(f"Privacy/secret leak in {p}: {m.group(0)[:48]}")
    return violations
