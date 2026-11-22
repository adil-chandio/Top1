#!/usr/bin/env python3
"""Formal 15-state lifecycle validator & workflow dependency DAG for Monarch Studio OS.

Enforces:
  1. Ordered state progression (`idea` .. `published`) with explicit audit reasons.
  2. Hard rule (Section V & Z): NO automated tool can ever promote a project to
     `owner-accepted` or `published` without an explicit human-actor sign-off record.
  3. Content-addressed Workflow DAG (Section W): hashes upstream artifacts so
     downstream targets invalidate selectively instead of blind `run-all.sh` rebuilds.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Sequence

STATES: Sequence[str] = (
    "idea",
    "researched",
    "shortlisted",
    "owner-selected",
    "claim-checked",
    "scripted",
    "proof-pending",
    "proof-passed",
    "voice-locked",
    "picture-locked",
    "mix-locked",
    "qa-passed",
    "owner-accepted",
    "private-uploaded",
    "published",
)

HUMAN_ONLY_STATES = {"owner-selected", "owner-accepted", "published"}

# Dependency graph (Section W): key -> upstream nodes it depends on
DAG_UPSTREAMS: Dict[str, List[str]] = {
    "claims": [],
    "script": ["claims"],
    "voice": ["script"],
    "shot_plan": ["script"],
    "proof_render": ["claims", "shot_plan"],
    "feature_render": ["voice", "shot_plan", "assets"],
    "assets": [],
    "mix": ["voice", "feature_render"],
    "audio_qa": ["mix"],
    "video_qa": ["feature_render", "mix"],
    "packaging": ["claims", "script"],
}


def validate_project_lifecycle(project_doc: dict) -> List[str]:
    errors: List[str] = []
    cur = project_doc.get("status")
    if cur not in STATES:
        errors.append(f"Unknown status: {cur!r}")
        return errors

    history = project_doc.get("status_history", [])
    if not history:
        errors.append("status_history cannot be empty")
        return errors

    if history[-1].get("state") != cur:
        errors.append(f"Current status {cur!r} does not match latest history entry {history[-1].get('state')!r}")

    prev_idx = -1
    for entry in history:
        st = entry.get("state")
        actor = entry.get("actor")
        if st not in STATES:
            errors.append(f"Invalid history state: {st!r}")
            continue
        idx = STATES.index(st)
        if idx < prev_idx:
            errors.append(f"Backward state regression without reset receipt: {STATES[prev_idx]} -> {st}")
        prev_idx = idx
        if st in HUMAN_ONLY_STATES and actor != "owner":
            errors.append(f"State {st!r} requires actor=='owner', got {actor!r}")

    return errors


def impacted_targets(changed_nodes: Sequence[str]) -> List[str]:
    """Return ordered list of DAG targets invalidated by `changed_nodes`."""
    dirty = set(changed_nodes)
    added = True
    while added:
        added = False
        for node, ups in DAG_UPSTREAMS.items():
            if node not in dirty and any(u in dirty for u in ups):
                dirty.add(node)
                added = True
    order = [
        "claims",
        "script",
        "assets",
        "voice",
        "shot_plan",
        "proof_render",
        "feature_render",
        "mix",
        "audio_qa",
        "video_qa",
        "packaging",
    ]
    return [n for n in order if n in dirty]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_project_fingerprints(file_map: Dict[str, Sequence[Path]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for node, paths in file_map.items():
        h = hashlib.sha256()
        for p in sorted(paths):
            h.update(p.name.encode("utf-8"))
            h.update(b"\0")
            if p.exists():
                h.update(p.read_bytes())
        out[node] = h.hexdigest()
    return out
