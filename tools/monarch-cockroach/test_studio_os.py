#!/usr/bin/env python3
"""End-to-end automated pytest suite for Studio OS + Monarch Cam Episode #03."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
OS_DIR = ROOT / "tools" / "monarch-studio-os"
EP_DIR = ROOT / "tools" / "monarch-cockroach"
MANIFEST_DIR = EP_DIR / "manifests"

sys.path.insert(0, str(OS_DIR))
sys.path.insert(0, str(EP_DIR))

from validators.claim_linter import (  # noqa: E402
    lint_script_against_claims,
    scan_zero_trust_privacy,
    validate_scorecard,
)
from validators.state_machine import (  # noqa: E402
    impacted_targets,
    validate_project_lifecycle,
)
import rig  # noqa: E402


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("manifest_file", "schema_file"),
    [
        ("project.json", "project.schema.json"),
        ("claims.json", "claims.schema.json"),
        ("scorecard.json", "scorecard.schema.json"),
        ("rights.json", "rights.schema.json"),
        ("shot-plan.json", "shot-plan.schema.json"),
        ("packaging.json", "packaging.schema.json"),
        ("proof-qa-report.json", "qa-report.schema.json"),
        ("feature-qa-report.json", "qa-report.schema.json"),
    ],
)
def test_manifest_validates_against_schema(manifest_file: str, schema_file: str) -> None:
    instance = _load_json(MANIFEST_DIR / manifest_file)
    schema = _load_json(OS_DIR / "schemas" / schema_file)
    jsonschema.validate(instance=instance, schema=schema)


def test_state_machine_blocks_automated_publish_and_tracks_dag() -> None:
    proj = _load_json(MANIFEST_DIR / "project.json")
    assert validate_project_lifecycle(proj) == []

    # Automated tool attempting to enter owner-accepted or published MUST fail
    bad_proj = json.loads(json.dumps(proj))
    bad_proj["status"] = "owner-accepted"
    bad_proj["status_history"].append(
        {"state": "owner-accepted", "timestamp_utc": "2026-11-21T00:00:00Z", "actor": "studio-os-bot", "note": "illegal"}
    )
    errs = validate_project_lifecycle(bad_proj)
    assert any("actor=='owner'" in e for e in errs)

    bad_pub = json.loads(json.dumps(proj))
    bad_pub["status"] = "published"
    bad_pub["status_history"].append(
        {"state": "published", "timestamp_utc": "2026-11-21T00:00:00Z", "actor": "ci-pipeline", "note": "illegal"}
    )
    errs_pub = validate_project_lifecycle(bad_pub)
    assert any("actor=='owner'" in e for e in errs_pub)

    # DAG invalidation: changing `voice` invalidates `feature_render`, `mix`, `audio_qa`, `video_qa`, NOT `claims` or `packaging`
    dirty = impacted_targets(["voice"])
    assert "feature_render" in dirty and "mix" in dirty
    assert "claims" not in dirty and "packaging" not in dirty


def test_claim_linter_and_scorecard_pass_and_catch_overclaims() -> None:
    claims_doc = _load_json(MANIFEST_DIR / "claims.json")
    scorecard_doc = _load_json(MANIFEST_DIR / "scorecard.json")
    narration = (EP_DIR / "feature" / "narration.txt").read_text(encoding="utf-8")
    script_md = (EP_DIR / "feature" / "script.md").read_text(encoding="utf-8")
    launch_txt = (EP_DIR / "feature" / "launch-copy-draft.txt").read_text(encoding="utf-8")

    assert lint_script_against_claims(narration, claims_doc, extra_texts=[script_md, launch_txt]) == []
    assert validate_scorecard(scorecard_doc) == []

    # Injecting a forbidden overclaim ("indestructible") must immediately fail the linter
    bad_errs = lint_script_against_claims(
        narration,
        claims_doc,
        extra_texts=["This cockroach is completely indestructible under any building."],
    )
    assert any("indestructible" in e.lower() for e in bad_errs)


def test_dependency_registry_sha256_integrity() -> None:
    deps = _load_json(OS_DIR / "manifests" / "dependencies.json")
    assert len(deps["dependencies"]) >= 15
    for d in deps["dependencies"]:
        assert len(d["sha256"]) == 64
        wheel_candidate = Path("/tmp/wheels") / d["commit_or_release"]
        if wheel_candidate.exists():
            actual_sha = hashlib.sha256(wheel_candidate.read_bytes()).hexdigest()
            assert actual_sha == d["sha256"], d["name"]


def test_moving_proof_csv_and_qa_invariants() -> None:
    qa = _load_json(MANIFEST_DIR / "proof-qa-report.json")
    assert qa["passed"] is True
    assert qa["video_qa"]["decoded_frames"] == 270
    assert qa["video_qa"]["black_frames"] == 0
    assert qa["audio_qa"]["clipped_samples"] == 0
    assert qa["mobile_qa"]["min_edge_contrast_ratio"] >= 3.5

    csv_path = ROOT / ".cache" / "monarch-cockroach" / "moving-proof" / "proof_trace.csv"
    if not csv_path.exists():
        pytest.skip("Gitignored .cache moving-proof CSV not present in fresh checkout")
    with csv_path.open("r", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 270
    for r in rows[178:]:
        assert int(r["spines_planted"]) == 1
        assert float(r["spine1_z_mm"]) == 0.0
        assert float(r["spine2_z_mm"]) == 0.0
        assert float(r["spine3_z_mm"]) == 0.0
        assert float(r["spine_slip_mm"]) == 0.0
        assert float(r["claw_z_mm"]) >= 0.45


def test_zero_trust_no_private_ids_or_binary_media_in_tools() -> None:
    assert scan_zero_trust_privacy([OS_DIR, EP_DIR]) == []

    # Also check against any Drive IDs recorded in `.cache/monarch-cockroach/drive-route-receipt.json`
    receipt_path = ROOT / ".cache" / "monarch-cockroach" / "drive-route-receipt.json"
    if receipt_path.exists():
        raw_receipt = receipt_path.read_text(encoding="utf-8")
        # Extract Drive IDs (excluding 32-char lowercase hex MD5 hashes) and verify none appear in `tools/`
        import re
        ids = {
            tok
            for tok in re.findall(r"\b1[A-Za-z0-9_-]{27,45}\b", raw_receipt)
            if not re.fullmatch(r"[0-9a-f]{32}", tok)
        }
        assert len(ids) >= 5
        for p in list(OS_DIR.rglob("*")) + list(EP_DIR.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                txt = p.read_text(encoding="utf-8", errors="ignore")
                for drive_id in ids:
                    assert drive_id not in txt, f"Leaked private Drive ID in {p}"


def test_biomechanical_rig_core_numbers() -> None:
    assert abs(rig.BODY_LENGTH_MM - 31.10) < 1e-6
    assert abs(rig.BODY_MASS_G - 0.76) < 1e-6
    assert abs(rig.FREESTANDING_HEIGHT_MM - 12.52) < 1e-6


def test_full_feature_master_qa_and_chapter_traces() -> None:
    proj = _load_json(MANIFEST_DIR / "project.json")
    assert proj["status"] == "qa-passed"
    assert proj["status"] not in ("owner-accepted", "published")

    vlock = _load_json(MANIFEST_DIR / "voice-lock.json")
    assert vlock["voice_id"] == "voice-01"
    assert vlock["time_stretch_applied"] is False
    assert vlock["total_frames"] == 10461

    fqa = _load_json(MANIFEST_DIR / "feature-qa-report.json")
    assert fqa["passed"] is True
    assert fqa["video_qa"]["decoded_frames"] == 10461
    assert fqa["video_qa"]["black_frames"] == 0
    assert fqa["video_qa"]["unintended_freeze_runs"] == 0
    assert fqa["audio_qa"]["clipped_samples"] == 0
    assert -18.0 <= fqa["audio_qa"]["integrated_lufs"] <= -13.0
    assert fqa["audio_qa"]["true_peak_dbtp"] <= -1.0

    shot_plan = _load_json(MANIFEST_DIR / "shot-plan.json")
    assert shot_plan["shots"][0]["first_frame"] == 0
    assert shot_plan["shots"][-1]["end_frame"] == 10461

    film_dir = ROOT / ".cache" / "monarch-cockroach" / "feature-film"
    if not (film_dir / "trace_ch01.csv").exists():
        pytest.skip("Gitignored .cache feature-film trace CSVs not present in fresh checkout")
    total_traced = 0
    for ch_idx in range(1, 8):
        tpath = film_dir / f"trace_ch{ch_idx:02d}.csv"
        assert tpath.exists()
        with tpath.open("r", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        total_traced += len(rows)
    assert total_traced == 10461


def test_v3_threejs_pyglm_master() -> None:
    v3_report_path = ROOT / ".cache" / "monarch-cockroach" / "v3" / "v3_verification_report.json"
    if not v3_report_path.exists():
        pytest.skip("Gitignored .cache v3 verification report not present in fresh checkout")
    rep = _load_json(v3_report_path)
    assert rep["pyglm"]["r3_sprawl_4mm_deg"] > 80.0
    assert rep["projection_csv"]["rows"] == 10461
    assert rep["master_mp4"]["frames"] == 10461
    assert rep["master_mp4"]["master_mb"] < 95.0
    assert -17.2 <= rep["master_mp4"]["lufs_i"] <= -14.8
    assert rep["master_mp4"]["dbtp"] <= -1.5
    assert rep["integrity"]["dry_vo_md5"] == "e4dfc0e4a332a35166e5c48ad16d63df"
    assert rep["integrity"]["locked_files_diff"] == 0


