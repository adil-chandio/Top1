#!/usr/bin/env python3
"""Full-length 16:9 editorial schedule for Monarch Cam Episode #03 (Cockroach Feature).

Builds the deterministic 88-shot, 7-chapter 16:9 schedule (`feature.plan`) on the
30 fps clock. Pre-VO nominal anchors span 9,180 frames (306.00 s); once Step 03
locks the selected narrator WAV, `conform_to_anchors(...)` scales each chapter's
takes proportionally onto exact sample-derived chapter boundaries without gaps.
"""

import json
from pathlib import Path
from typing import List, Sequence, Tuple

HERE = Path(__file__).resolve().parent
STORY_PATH = HERE / "story.json"
PLAN_PATH = HERE / "feature.plan"

FPS = 30
MASTER = (1920, 1080)
CONTINUATION_RASTER = (1280, 720)
NOMINAL_ANCHORS: Tuple[int, ...] = (0, 840, 2250, 3660, 5280, 6570, 7980, 9180)

# Chapter-by-chapter shot definitions:
# (relative_weight, mode, camera_id, src_a, src_b, subject, pin_fractions)
CHAPTER_SHOTS = {
    1: [
        (72, 10, 101, 0.00, 2.40, "open_tabletop_standing_scale", [(0.50, 1.20)]),
        (84, 10, 102, 2.40, 5.20, "six_legs_elevated_tripod_approach", []),
        (78, 11, 103, 0.00, 2.60, "two_stacked_pennies_beside_3_2mm_slit", [(0.45, 1.15)]),
        (66, 11, 104, 2.60, 4.80, "antennae_reach_slit_threshold", [(0.60, 3.92)]),
        (72, 12, 105, 0.00, 1.20, "cold_open_head_dip_and_shell_flatten", [(0.35, 0.42), (0.75, 0.90)]),
        (66, 12, 106, 1.20, 2.35, "subsecond_slit_exit_and_sprint", [(0.40, 1.66)]),
        (78, 13, 107, 0.00, 2.10, "freeze_on_empty_3_2mm_gap", []),
        (78, 14, 108, 0.00, 2.20, "standing_height_vs_slit_height_callout", []),
        (84, 14, 109, 2.20, 4.60, "underbody_clearance_disappears_question", []),
        (84, 15, 110, 0.00, 2.80, "splayed_foot_loses_stance_tease", []),
        (78, 10, 111, 5.20, 7.80, "cold_open_hold_into_chapter_two", []),
    ],
    2: [
        (110, 20, 201, 0.00, 3.10, "gate_rig_side_and_overhead_establish", []),
        (115, 21, 202, 0.00, 1.85, "stage_one_antennal_sweep_probe", [(0.45, 0.82)]),
        (120, 21, 203, 1.85, 3.70, "stage_two_head_pitch_down_and_wedge", [(0.50, 2.78)]),
        (125, 21, 204, 3.70, 5.80, "stage_three_pronotum_slight_roll_entry", [(0.55, 4.85)]),
        (135, 21, 205, 5.80, 8.20, "stage_four_planted_hind_legs_shove_thorax", [(0.48, 6.95)]),
        (115, 21, 206, 8.20, 10.10, "stage_five_flattened_abdomen_clears_gate", [(0.62, 9.35)]),
        (120, 22, 207, 0.00, 2.60, "not_soft_rubber_false_bend_contrast", []),
        (135, 23, 208, 0.00, 3.40, "sagittal_cutaway_rigid_tergite_plates", [(0.52, 1.76)]),
        (140, 23, 209, 3.40, 6.90, "arthrodial_hinge_membranes_fold_in_half", [(0.50, 5.15)]),
        (115, 24, 210, 0.00, 2.80, "overlapping_plates_spread_contact_patch", []),
        (90, 24, 211, 2.80, 5.10, "viscoelastic_hinge_rebound_on_exit", []),
        (90, 20, 212, 3.10, 5.60, "doorway_outside_leg_room_limitation", []),
    ],
    3: [
        (115, 30, 301, 0.00, 3.20, "fifteen_cm_low_ceiling_corridor_reveal", []),
        (120, 31, 302, 0.00, 3.40, "twelve_mm_unconstrained_run_58_cm_s", [(0.50, 1.70)]),
        (120, 31, 303, 3.40, 6.80, "nine_mm_crouched_run_no_roof_rub", []),
        (125, 31, 304, 6.80, 10.30, "six_mm_ceiling_skims_uncompressed_back", [(0.55, 8.70)]),
        (125, 32, 305, 0.00, 3.50, "three_height_speed_comparison_holds_58", []),
        (120, 33, 306, 0.00, 3.20, "overhead_sprawl_widens_55_to_75_deg", []),
        (120, 33, 307, 3.20, 6.40, "constant_11_9mm_foot_midline_track", []),
        (110, 33, 308, 6.40, 9.20, "constant_61ms_stride_beat_markers", []),
        (125, 34, 309, 0.00, 3.10, "ceiling_steps_down_to_four_mm_squeeze", [(0.45, 1.40)]),
        (125, 34, 310, 3.10, 6.40, "fourfold_speed_drop_to_14_5_cm_s", []),
        (110, 35, 311, 0.00, 2.90, "alternating_tripod_rhythm_breaks_apart", []),
        (95, 35, 312, 2.90, 5.40, "hold_on_four_mm_crawling_question", []),
    ],
    4: [
        (110, 40, 401, 0.00, 2.80, "rear_transverse_axis_align_on_hind_leg", []),
        (125, 41, 402, 0.00, 3.20, "upright_12mm_high_tarsal_tip_stance", [(0.50, 1.60)]),
        (125, 41, 403, 3.20, 6.40, "macro_hooked_claws_and_pads_catch_floor", [(0.48, 4.74)]),
        (135, 42, 404, 0.00, 3.40, "ceiling_presses_to_4mm_sprawl_past_80_deg", [(0.52, 1.77)]),
        (135, 42, 405, 3.40, 6.80, "tarsus_tips_sideways_claws_lose_angle", [(0.45, 4.93)]),
        (150, 43, 406, 0.00, 3.80, "uninterrupted_macro_shin_spines_plant_z0", [(0.38, 1.44), (0.72, 2.74)]),
        (140, 43, 407, 3.80, 7.20, "backward_angled_tibial_spines_drive_stroke", [(0.50, 5.50)]),
        (125, 44, 408, 0.00, 3.20, "overhead_paired_middle_legs_shove_together", [(0.55, 1.76)]),
        (125, 44, 409, 3.20, 6.40, "oar_like_mesothoracic_synchronous_thrust", []),
        (125, 45, 410, 0.00, 3.10, "dorsal_ceiling_and_ventral_belly_rub_vectors", []),
        (115, 45, 411, 3.10, 6.00, "five_body_weights_per_leg_thrust_balance", []),
        (105, 43, 412, 7.20, 9.80, "macro_spine_push_clean_picture_hold", []),
        (105, 40, 413, 2.80, 5.50, "pull_back_from_shin_to_full_tunnel_run", []),
    ],
    5: [
        (115, 50, 501, 0.00, 2.90, "question_are_splayed_feet_helping_hidden", []),
        (125, 51, 502, 0.00, 3.30, "schematic_spine_only_traction_test_setup", []),
        (120, 51, 503, 3.30, 6.40, "spiny_tibia_alone_holds_directional_grip", [(0.50, 4.85)]),
        (115, 52, 504, 0.00, 3.00, "six_hundred_confined_runs_surface_matrix", []),
        (120, 53, 505, 0.00, 3.10, "smooth_graphite_vs_rough_ceiling_comparison", []),
        (120, 53, 506, 3.10, 6.20, "rough_ceiling_monotonically_cuts_speed", [(0.52, 4.71)]),
        (120, 54, 507, 0.00, 3.10, "floor_roughness_curve_peaks_at_medium_grit", []),
        (115, 55, 508, 0.00, 2.90, "slick_100grit_floor_early_spine_slip", [(0.46, 1.33)]),
        (125, 55, 509, 2.90, 6.10, "coarse_20grit_floor_belly_snags_on_grit", [(0.54, 4.63)]),
        (110, 54, 510, 3.10, 5.90, "slipping_zigzag_path_at_4mm_limit", []),
        (105, 50, 511, 2.90, 5.50, "hold_on_friction_tradeoff_transition", []),
    ],
    6: [
        (125, 64, 601, 0.00, 3.30, "schematic_300x_to_900x_load_spread_plates", []),
        (120, 64, 602, 3.30, 6.40, "three_square_cm_patch_prevents_shell_crack", []),
        (120, 65, 603, 0.00, 3.10, "post_test_unimpaired_76_7_cm_s_sprint", [(0.50, 1.55)]),
        (115, 60, 604, 0.00, 3.00, "unstoppable_expectation_return_to_crevice_gate", []),
        (120, 61, 605, 0.00, 3.20, "six_mm_and_four_four_mm_72pct_pass", [(0.50, 1.60)]),
        (125, 61, 606, 3.20, 6.50, "three_two_mm_gate_drops_to_17pct_pass", [(0.52, 4.92)]),
        (120, 62, 607, 0.00, 3.10, "antennal_check_and_turn_back_majority", [(0.48, 1.49)]),
        (130, 62, 608, 3.10, 6.60, "nine_percent_wedged_at_thickest_thorax", [(0.55, 5.02)]),
        (120, 63, 609, 0.00, 3.10, "three_outcome_ledger_315_lab_attempts", []),
        (115, 60, 610, 3.00, 6.00, "tough_shell_vs_tight_gap_distinction", []),
        (100, 60, 611, 6.00, 8.60, "quiet_beat_before_real_speed_reprise", []),
    ],
    7: [
        (130, 70, 701, 0.00, 2.80, "reprise_approach_two_penny_slot_real_speed", []),
        (135, 70, 702, 2.80, 4.90, "real_speed_shingle_fold_and_shin_drive", [(0.45, 3.74)]),
        (135, 71, 703, 0.00, 2.90, "far_side_hinge_rebound_to_half_inch_height", [(0.42, 1.22)]),
        (130, 71, 704, 2.90, 5.80, "tarsal_claws_retake_open_floor_sprint", []),
        (140, 72, 705, 0.00, 3.40, "paired_callout_hinges_fold_spines_push", []),
        (145, 73, 706, 0.00, 3.60, "cockroach_clears_frame_leaving_pennies_and_slot", []),
        (195, 73, 707, 3.60, 8.20, "closing_quiet_hold_on_two_penny_gap_no_cta", []),
        (190, 74, 708, 0.00, 4.80, "readable_primary_source_and_science_credits", []),
    ],
}


def conform_to_anchors(anchors: Sequence[int] = NOMINAL_ANCHORS) -> List[dict]:
    """Scale chapter shot weights cleanly onto exact integer chapter frame anchors."""
    if len(anchors) != 8 or anchors[0] != 0 or any(a >= b for a, b in zip(anchors, anchors[1:])):
        raise ValueError(f"Invalid 8-point chapter anchors: {anchors}")

    shots: List[dict] = []
    for ch in range(1, 8):
        ch_lo, ch_hi = anchors[ch - 1], anchors[ch]
        span = ch_hi - ch_lo
        specs = CHAPTER_SHOTS[ch]
        total_w = sum(w for w, *_ in specs)
        acc = 0
        cursor = ch_lo
        for idx, (w, mode, cam, sa, sb, subj, pin_fracs) in enumerate(specs):
            acc += w
            end = ch_hi if idx == len(specs) - 1 else ch_lo + round(span * acc / total_w)
            if end <= cursor + 12:
                end = cursor + 12
            pins: List[List[float]] = []
            for pf, pt in pin_fracs:
                pf_frame = cursor + max(1, min(end - cursor - 2, round((end - cursor) * pf)))
                pins.append([int(pf_frame), round(float(pt), 6)])
            shots.append(
                {
                    "first": int(cursor),
                    "end": int(end),
                    "mode": int(mode),
                    "camera": int(cam),
                    "src": [round(float(sa), 6), round(float(sb), 6)],
                    "subject": subj,
                    "chapter": ch,
                    "pins": pins,
                }
            )
            cursor = end

    assert shots[0]["first"] == 0 and shots[-1]["end"] == anchors[-1]
    assert all(a["end"] == b["first"] for a, b in zip(shots, shots[1:]))
    assert len({s["subject"] for s in shots}) == len(shots)
    for r in shots:
        pts = [(r["first"], r["src"][0]), *[(p[0], p[1]) for p in r["pins"]], (r["end"] - 1, r["src"][1])]
        assert all(f0 < f1 and t0 < t1 for (f0, t0), (f1, t1) in zip(pts, pts[1:])), r
    return shots


def write_schedule(anchors: Sequence[int] = NOMINAL_ANCHORS) -> dict:
    shots = conform_to_anchors(anchors)
    lines = [
        "# Monarch Cam Episode #03 · 16:9 Feature Editorial Schedule (30 fps)\n",
        "# Columns: first_frame end_frame mode camera_id src_start_s src_end_s subject [pin_frame pin_src_s ...]\n",
    ]
    for r in shots:
        pin_str = "".join(f" {p[0]} {p[1]:.6f}" for p in r["pins"])
        lines.append(
            f"{r['first']} {r['end']} {r['mode']} {r['camera']} "
            f"{r['src'][0]:.6f} {r['src'][1]:.6f} {r['subject']}{pin_str}\n"
        )
    PLAN_PATH.write_text("".join(lines), encoding="utf-8")
    summary = {
        "fps": FPS,
        "frames": anchors[-1],
        "duration_s": round(anchors[-1] / FPS, 2),
        "delivery_resolution": list(MASTER),
        "continuation_resolution": list(CONTINUATION_RASTER),
        "anchors": list(anchors),
        "shot_count": len(shots),
    }
    print(
        f"{len(shots)} takes; 7 chapters; {summary['frames']} frames / "
        f"{summary['duration_s']:.2f} s @ {FPS} fps (1920x1080 master)"
    )
    return summary


if __name__ == "__main__":
    write_schedule()
