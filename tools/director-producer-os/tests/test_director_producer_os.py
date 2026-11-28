from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OS_DIR = ROOT / "tools" / "director-producer-os"
VALIDATORS_DIR = OS_DIR / "validators"
EXAMPLES_DIR = OS_DIR / "examples"

if str(VALIDATORS_DIR) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_DIR))

from anti_clone_validator import (
    compute_divergence_score,
    extract_fingerprint,
    load_fingerprints,
    validate_anti_clone,
)
from director_linter import compute_visible_dimensions_m, lint_director_plan
from register_fingerprint import register_plan_fingerprint

CANONICAL_TOPOLOGIES = {
    "in_situ_natural_biome",
    "lived_in_human_interior",
    "field_expedition_site",
    "industrial_test_bay",
    "minimalist_sculptural_stage",
    "microscopic_or_cosmic_diegetic",
    "split_reality_dual_timeline",
}


def _load_example(name: str) -> dict:
    with open(EXAMPLES_DIR / name, "r", encoding="utf-8") as fh:
        return json.load(fh)


class TestDirectorProducerOS(unittest.TestCase):
    def test_catalog_has_24_valid_world_archetypes_and_6_huds(self):
        raw = json.loads((OS_DIR / "catalog" / "world_archetypes.json").read_text(encoding="utf-8"))
        archetypes = raw["archetypes"]
        huds = raw["hud_philosophies"]
        self.assertEqual(len(archetypes), 24)
        self.assertEqual(len(huds), 6)

        seen_ids = set()
        for arch in archetypes:
            aid = arch["id"]
            self.assertNotIn(aid, seen_ids)
            seen_ids.add(aid)
            self.assertIn(arch["topology"], CANONICAL_TOPOLOGIES, f"{aid} has non-canonical topology")
            cs = arch["color_script"]
            self.assertNotIn(cs["accent_hex"].upper(), {h.upper() for h in cs["base_hex"]})
            self.assertGreaterEqual(len(arch["lens_package_mm"]), 2)

    def test_schema_and_fingerprint_ledger_valid_json(self):
        schema = json.loads((OS_DIR / "schemas" / "director-plan.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["title"], "Top1DirectorProducerPlanV1")
        hist = load_fingerprints()
        self.assertGreaterEqual(len(hist), 3)

    def test_all_three_contrasting_exemplars_pass_zero_errors_zero_warnings(self):
        for example_file in (
            "01-sunlit-kitchen-pressure-cooker-plan.json",
            "02-rainforest-cordyceps-canopy-plan.json",
            "03-cretaceous-antarctic-polar-forest-plan.json",
        ):
            with self.subTest(example=example_file):
                plan = _load_example(example_file)
                errors, warnings, summary = lint_director_plan(plan, check_history=True)
                self.assertEqual(errors, [], f"Unexpected errors in {example_file}: {errors}")
                self.assertEqual(warnings, [], f"Unexpected warnings in {example_file}: {warnings}")
                self.assertGreaterEqual(summary["anti_clone"]["divergence_vs_latest_pct"], 85.0)

    def test_three_exemplars_mutually_diverge_strongly_from_each_other(self):
        p1 = _load_example("01-sunlit-kitchen-pressure-cooker-plan.json")
        p2 = _load_example("02-rainforest-cordyceps-canopy-plan.json")
        p3 = _load_example("03-cretaceous-antarctic-polar-forest-plan.json")
        f1, f2, f3 = extract_fingerprint(p1), extract_fingerprint(p2), extract_fingerprint(p3)
        self.assertGreaterEqual(compute_divergence_score(f1, f2), 85.0)
        self.assertGreaterEqual(compute_divergence_score(f2, f3), 80.0)
        self.assertGreaterEqual(compute_divergence_score(f1, f3), 85.0)

    def test_anti_clone_blocks_repeating_dark_pedestal_obsidian_teal_amber_template(self):
        clone = _load_example("03-cretaceous-antarctic-polar-forest-plan.json")
        clone["project_id"] = "bad-clone-attempt"
        clone["channel"] = "extinct-channel"
        clone["producer_brief"]["opening_hook_grammar"] = "FORENSIC_CRIME_SCENE_RESULT"
        clone["anti_clone_declaration"] = {
            "selected_archetype_id": "W19_SYNCHROTRON_TOMOGRAPHY_CHAMBER",
            "staging_topology": "minimalist_sculptural_stage",
            "primary_prop_anchor": "sandstone_block_specimen_pedestal",
            "palette_family": "obsidian_teal_cyan_amber_sandstone",
            "dominant_sequence_pattern": "forensic_peel_layer_by_layer",
            "hud_philosophy": "H3_FORENSIC_BLUEPRINT",
            "why_not_previous_template": "Trying to sneak the same dark pedestal template through again.",
            "user_explicit_template_override": False,
        }
        errors, _, report = validate_anti_clone(clone, history=load_fingerprints()[:3])
        joined = "\n".join(errors)
        self.assertIn("Archetype 'W19_SYNCHROTRON_TOMOGRAPHY_CHAMBER' was just used", joined)
        self.assertIn("ANTI-CLONE SATURATION BLOCK", joined)
        self.assertIn("ANTI-CLONE PALETTE BLOCK", joined)
        self.assertIn("ANTI-CLONE DIVERGENCE TOO LOW", joined)
        self.assertLess(report["divergence_vs_latest_pct"], 45.0)

    def test_linter_catches_vague_buzzwords_clipping_180_axis_30_deg_and_eye_trace(self):
        plan = _load_example("01-sunlit-kitchen-pressure-cooker-plan.json")

        bad_buzz = copy.deepcopy(plan)
        bad_buzz["shots"][0]["dramatic_purpose"] = "Make a super cinematic epic shot of the stove."
        errs, _, _ = lint_director_plan(bad_buzz, check_history=False)
        self.assertTrue(any("forbidden vague buzzword" in e for e in errs))

        bad_clip = copy.deepcopy(plan)
        bad_clip["shots"][0]["subject_width_m"] = 0.65
        errs, _, _ = lint_director_plan(bad_clip, check_history=False)
        self.assertTrue(any("HORIZONTAL CLIPPING RISK" in e for e in errs))

        bad_axis = copy.deepcopy(plan)
        bad_axis["shots"][1]["camera_pos_xyz"] = [0.24, 0.48, -0.35]
        errs, _, _ = lint_director_plan(bad_axis, check_history=False)
        self.assertTrue(any("180-DEGREE AXIS VIOLATION" in e for e in errs))

        bad_jump = copy.deepcopy(plan)
        bad_jump["shots"][1]["subject_id"] = bad_jump["shots"][0]["subject_id"]
        bad_jump["shots"][1]["shot_size"] = bad_jump["shots"][0]["shot_size"]
        bad_jump["shots"][1]["camera_pos_xyz"] = [0.03, 0.34, 0.68]
        bad_jump["shots"][1]["look_at_xyz"] = bad_jump["shots"][0]["look_at_xyz"]
        errs, _, _ = lint_director_plan(bad_jump, check_history=False)
        self.assertTrue(any("30-DEGREE JUMP-CUT VIOLATION" in e for e in errs))

        bad_eye = copy.deepcopy(plan)
        bad_eye["shots"][1]["eye_trace_start_xy"] = [0.95, 0.92]
        errs, _, _ = lint_director_plan(bad_eye, check_history=False)
        self.assertTrue(any("EYE-TRACE WHIPLASH" in e for e in errs))

    def test_linter_catches_bruce_block_color_accent_hold_for_text_see_hide_and_loop(self):
        plan = _load_example("01-sunlit-kitchen-pressure-cooker-plan.json")

        bad_col = copy.deepcopy(plan)
        bad_col["production_design"]["color_script"]["base_hex"].append("#C83E2B")
        errs, _, _ = lint_director_plan(bad_col, check_history=False)
        self.assertTrue(any("reserved_accent_hex" in e for e in errs))

        bad_bb = copy.deepcopy(plan)
        bad_bb["production_design"]["bruce_block_visual_arc"]["climax_beat_id"] = "B5_SAFE_KITCHEN_LOOP"
        errs, _, _ = lint_director_plan(bad_bb, check_history=False)
        self.assertTrue(any("Bruce Block mismatch" in e for e in errs))

        bad_txt = copy.deepcopy(plan)
        bad_txt["shots"][3]["move"] = "orbit_arc"
        bad_txt["shots"][3]["motivation"] = "RELATE"
        bad_txt["shots"][3]["ease"] = "easeInOutCubic"
        bad_txt["shots"][3]["end_frame_desc"] = "Orbited 90 degrees while viewer tries to read text."
        errs, _, _ = lint_director_plan(bad_txt, check_history=False)
        self.assertTrue(any("hold_for_text" in e for e in errs))

        bad_sh = copy.deepcopy(plan)
        bad_sh["dramaturgy"]["see_hide_pairs"][0]["hide_shot_id"] = "S06"
        bad_sh["dramaturgy"]["see_hide_pairs"][0]["reveal_shot_id"] = "S02"
        errs, _, _ = lint_director_plan(bad_sh, check_history=False)
        self.assertTrue(any("must precede reveal_shot" in e for e in errs))

        bad_loop = copy.deepcopy(plan)
        bad_loop["shots"][-1]["eye_trace_end_xy"] = [0.88, 0.85]
        errs, _, _ = lint_director_plan(bad_loop, check_history=False)
        self.assertTrue(any("seamless_loop=true eye-trace seam mismatch" in e for e in errs))

    def test_python_and_threejs_director_optics_sdk_exact_math_parity(self):
        node_bin = shutil.which("node")
        self.assertIsNotNone(node_bin)
        sdk_path = (ROOT / "tools" / "monarch-v6-imax-sdk" / "core" / "director_optics_sdk.js").as_posix()
        js_code = f"""
          import {{
            computeCinemaFraming,
            check180AxisSide,
            compute30DegreeSeparation,
            parseContrastRatio,
          }} from 'file://{sdk_path}';
          const f916 = computeCinemaFraming(35, 0.68, '9:16_short');
          const f169 = computeCinemaFraming(50, 2.40, '16:9_long');
          const side = check180AxisSide([-1, 0, 1, 0], [0.2, 0.4, 0.7]);
          const sep = compute30DegreeSeparation([0, 0, 1], [0, 0, 0], [1, 0, 0], [0, 0, 0]);
          const cr = parseContrastRatio('8:1', 3.2);
          console.log(JSON.stringify({{ f916, f169, side, sep, cr }}));
        """
        proc = subprocess.run(
            [node_bin, "--input-type=module", "-e", js_code],
            capture_output=True,
            text=True,
            check=True,
        )
        out = json.loads(proc.stdout.strip())

        py_w916, py_h916, py_fov916 = compute_visible_dimensions_m(35, 0.68, "9:16_short")
        py_w169, py_h169, py_fov169 = compute_visible_dimensions_m(50, 2.40, "16:9_long")

        self.assertAlmostEqual(out["f916"]["visibleWidthM"], py_w916, places=9)
        self.assertAlmostEqual(out["f916"]["visibleHeightM"], py_h916, places=9)
        self.assertAlmostEqual(out["f916"]["fovYDeg"], py_fov916, places=9)
        self.assertAlmostEqual(out["f169"]["visibleWidthM"], py_w169, places=9)
        self.assertAlmostEqual(out["f169"]["fovYDeg"], py_fov169, places=9)
        self.assertEqual(out["side"], 1)
        self.assertAlmostEqual(out["sep"], 90.0, places=9)
        self.assertAlmostEqual(out["cr"]["stopsDifference"], 3.0, places=9)
        self.assertAlmostEqual(out["cr"]["fillIntensity"], 0.4, places=9)

    def test_register_fingerprint_idempotent_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            temp_ledger = Path(td) / "production_fingerprints.json"
            shutil.copyfile(OS_DIR / "catalog" / "production_fingerprints.json", temp_ledger)
            plan_path = EXAMPLES_DIR / "01-sunlit-kitchen-pressure-cooker-plan.json"

            fp1 = register_plan_fingerprint(str(plan_path), str(temp_ledger), completed_date="2026-11-27")
            fp2 = register_plan_fingerprint(str(plan_path), str(temp_ledger), completed_date="2026-11-27")
            self.assertEqual(fp1, fp2)

            saved = json.loads(temp_ledger.read_text(encoding="utf-8"))["productions"]
            matches = [p for p in saved if p["project_id"] == "ref-01-sunlit-kitchen-pressure-cooker"]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["archetype_id"], "W01_SUNLIT_DOMESTIC_MORNING")


if __name__ == "__main__":
    unittest.main()
