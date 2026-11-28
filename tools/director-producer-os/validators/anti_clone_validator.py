#!/usr/bin/env python3
"""
Top1 Anti-Clone Creative Divergence Validator (`anti_clone_validator.py`).

Prevents single-template / single-vibe repetition across videos by comparing a candidate
`director-plan.json` against `catalog/world_archetypes.json` and `catalog/production_fingerprints.json`.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_DIR = os.path.abspath(os.path.join(HERE, "../catalog"))
ARCHETYPES_PATH = os.path.join(CATALOG_DIR, "world_archetypes.json")
FINGERPRINTS_PATH = os.path.join(CATALOG_DIR, "production_fingerprints.json")


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if len(t) >= 3}


def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def load_archetypes(path: str = ARCHETYPES_PATH) -> dict[str, dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {item["id"]: item for item in data.get("archetypes", [])}


def load_fingerprints(path: str = FINGERPRINTS_PATH) -> list[dict[str, Any]]:
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return list(data.get("productions", []))


def extract_fingerprint(plan: dict[str, Any]) -> dict[str, str]:
    ac = plan.get("anti_clone_declaration", {})
    pb = plan.get("producer_brief", {})
    return {
        "project_id": plan.get("project_id", "unknown"),
        "channel": plan.get("channel", "unknown"),
        "archetype_id": ac.get("selected_archetype_id", ""),
        "staging_topology": ac.get("staging_topology", ""),
        "primary_prop_anchor": ac.get("primary_prop_anchor", ""),
        "palette_family": ac.get("palette_family", ""),
        "opening_hook_grammar": pb.get("opening_hook_grammar", ""),
        "dominant_sequence_pattern": ac.get("dominant_sequence_pattern", ""),
        "hud_philosophy": ac.get("hud_philosophy", ""),
    }


def compute_divergence_score(cand: dict[str, str], prev: dict[str, str]) -> float:
    """Returns 0.0 (100% clone) to 100.0 (100% distinct) across 7 weighted directing dimensions."""
    weights = {
        "archetype_id": 22.0,
        "staging_topology": 18.0,
        "primary_prop_anchor": 16.0,
        "palette_family": 18.0,
        "opening_hook_grammar": 10.0,
        "dominant_sequence_pattern": 8.0,
        "hud_philosophy": 8.0,
    }
    score = 0.0
    for key, w in weights.items():
        va, vb = cand.get(key, ""), prev.get(key, "")
        if key in ("archetype_id", "staging_topology", "opening_hook_grammar", "hud_philosophy"):
            sim = 1.0 if va == vb and va != "" else 0.0
        else:
            sim = _jaccard(va, vb)
        score += w * (1.0 - sim)
    return round(score, 2)


def validate_anti_clone(
    plan: dict[str, Any],
    history: list[dict[str, Any]] | None = None,
    archetypes: dict[str, dict[str, Any]] | None = None,
    min_divergence_pct: float = 65.0,
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    arch_map = archetypes if archetypes is not None else load_archetypes()
    hist = history if history is not None else load_fingerprints()
    ac = plan.get("anti_clone_declaration", {})
    replaces_id = ac.get("replaces_project_id", "")
    # Exclude self (or superseded edition being remastered) when validating!
    excluded_ids = {plan.get("project_id"), replaces_id} - {"", None}
    hist = [h for h in hist if h.get("project_id") not in excluded_ids]
    aid = ac.get("selected_archetype_id", "")
    if aid not in arch_map:
        errors.append(
            f"Unknown selected_archetype_id '{aid}'. Choose one of the 24 studio archetypes: {sorted(arch_map.keys())}"
        )
    else:
        arch = arch_map[aid]
        if ac.get("staging_topology") != arch.get("topology"):
            warnings.append(
                f"Archetype {aid} canonical topology is '{arch.get('topology')}', "
                f"plan declared '{ac.get('staging_topology')}'."
            )

    cand = extract_fingerprint(plan)
    override = bool(ac.get("user_explicit_template_override", False))

    # If re-validating an already-registered project, evaluate against the history prior to its registration!
    if cand.get("project_id"):
        self_indices = [idx for idx, h in enumerate(hist) if h.get("project_id") == cand["project_id"]]
        if self_indices:
            hist = hist[: self_indices[0]]

    if not hist or override:
        return errors, warnings, {"divergence_vs_latest_pct": 100.0, "compared_against": len(hist)}

    latest = hist[-1]
    div_latest = compute_divergence_score(cand, latest)

    # 1. Consecutive Archetype Ban
    if cand["archetype_id"] == latest.get("archetype_id"):
        errors.append(
            f"ANTI-CLONE VIOLATION: Archetype '{cand['archetype_id']}' was just used in the immediately "
            f"preceding production ('{latest.get('project_id')}'). Pick a fresh world archetype!"
        )

    # 2. Same-channel consecutive archetype & hook ban
    same_ch = [h for h in hist if h.get("channel") == cand["channel"]]
    if same_ch:
        last_ch = same_ch[-1]
        if cand["archetype_id"] == last_ch.get("archetype_id"):
            errors.append(
                f"ANTI-CLONE VIOLATION: Channel '{cand['channel']}' already used archetype '{cand['archetype_id']}' "
                f"in its previous episode ('{last_ch.get('project_id')}')."
            )
        if cand["opening_hook_grammar"] == last_ch.get("opening_hook_grammar"):
            errors.append(
                f"ANTI-CLONE VIOLATION: Channel '{cand['channel']}' repeated opening_hook_grammar "
                f"'{cand['opening_hook_grammar']}' back-to-back with '{last_ch.get('project_id')}'."
            )

    # 3. Prop-Anchor Clone Ban (turntable / pedestal / breadboard fatigue)
    prop_sim = _jaccard(cand["primary_prop_anchor"], latest.get("primary_prop_anchor", ""))
    if prop_sim >= 0.5:
        errors.append(
            f"ANTI-CLONE VIOLATION: primary_prop_anchor '{cand['primary_prop_anchor']}' overlaps too closely "
            f"({prop_sim:.0%}) with latest production '{latest.get('primary_prop_anchor')}'."
        )

    # 4. Topology Saturation Guard (3x minimalist_sculptural_stage in a row!)
    recent3 = hist[-3:]
    if len(recent3) >= 3 and all(h.get("staging_topology") == "minimalist_sculptural_stage" for h in recent3):
        if cand["staging_topology"] == "minimalist_sculptural_stage":
            errors.append(
                "ANTI-CLONE SATURATION BLOCK: The last 3 studio productions ALL used 'minimalist_sculptural_stage' "
                "(isolated pedestals/tables). This production MUST stage inside a real environment topology "
                "('in_situ_natural_biome', 'lived_in_human_interior', 'field_expedition_site', "
                "'industrial_test_bay', 'microscopic_or_cosmic_diegetic', or 'split_reality_dual_timeline')."
            )

    # 5. Dark Obsidian-Teal-Amber Palette Fatigue Guard
    obsidian_teal_tokens = {"obsidian", "teal", "cyan", "amber"}
    recent_obsidian_count = sum(
        1 for h in recent3 if len(_tokens(h.get("palette_family", "")) & obsidian_teal_tokens) >= 2
    )
    if recent_obsidian_count >= 2 and len(_tokens(cand["palette_family"]) & obsidian_teal_tokens) >= 2:
        errors.append(
            f"ANTI-CLONE PALETTE BLOCK: {recent_obsidian_count}/3 recent productions already used the "
            f"obsidian/teal/cyan/amber palette family. Choose a fresh color script (e.g. warm daylight linen, "
            f"bleached desert ochre, high-key alabaster, molten foundry, canopy emerald, glacial blue-white, "
            f"monsoon sodium-asphalt, or silver-gelatin B&W)!"
        )

    # 6. HUD Philosophy Fatigue Guard
    recent_h3 = sum(1 for h in recent3 if h.get("hud_philosophy") == "H3_FORENSIC_BLUEPRINT")
    if recent_h3 >= 2 and cand["hud_philosophy"] == "H3_FORENSIC_BLUEPRINT":
        warnings.append(
            "HUD FATIGUE WARNING: 2+ of the last 3 productions used H3_FORENSIC_BLUEPRINT. Strongly consider "
            "H0_PURE_CINEMA, H1_DOCUMENTARY_LOWER_THIRD, H2_DIEGETIC_IN_WORLD, or H5_EDITORIAL_CHAPTER_CARDS."
        )

    # 7. Overall Divergence Score Threshold
    if div_latest < min_divergence_pct:
        errors.append(
            f"ANTI-CLONE DIVERGENCE TOO LOW: {div_latest:.1f}% vs '{latest.get('project_id')}' "
            f"(minimum required: {min_divergence_pct:.1f}%)."
        )

    report = {
        "divergence_vs_latest_pct": div_latest,
        "latest_project_id": latest.get("project_id"),
        "min_divergence_across_recent3_pct": round(
            min(compute_divergence_score(cand, h) for h in recent3), 2
        ),
        "compared_against": len(hist),
    }
    return errors, warnings, report
