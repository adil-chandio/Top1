#!/usr/bin/env python3
"""
Top1 Master Film Director & Executive Producer Pre-Production Linter (`director_linter.py`).

Usage:
  python3 tools/director-producer-os/validators/director_linter.py <director-plan.json> [--no-history]

Enforces 32 deterministic cinema, optical, staging, blocking, Walter Murch editing,
Bruce Block visual-intensity, acoustic dramaturgy, and Anti-Clone divergence laws BEFORE
writing a single line of Three.js scene code or rendering any media.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from anti_clone_validator import validate_anti_clone

SHOT_SIZE_ORDER = ["EWS", "WS", "MWS", "MS", "MCU", "CU", "BCU", "ECU", "MACRO"]
ACTIVE_MOVES = {
    "push_in", "pull_out", "truck_lateral", "pedestal_vertical", "crane_arc",
    "orbit_arc", "pan", "tilt", "whip_pan", "dolly_zoom", "rack_focus_locked",
    "tracking_follow", "vehicle_or_body_mount", "probe_macro_glide",
}
PARALLAX_MOVES = {
    "push_in", "pull_out", "truck_lateral", "pedestal_vertical",
    "crane_arc", "orbit_arc", "tracking_follow", "probe_macro_glide",
}
TRANSLATIONAL_TEXT_CONFLICT_MOVES = {
    "whip_pan", "orbit_arc", "crane_arc", "truck_lateral", "dolly_zoom",
}
ACTIVE_MOTIVATIONS = {
    "FOLLOW", "REVEAL", "APPROACH", "WITHDRAW", "RELATE",
    "ORIENT", "SUBJECTIVE", "RHYTHM", "EXPRESSIVE",
}
VAGUE_RE = re.compile(
    r"\b(cinematic|epic|dynamic|cool|awesome|stunning|beautiful shot|looks nice|add energy)\b",
    re.IGNORECASE,
)


def _vec_sub(a: list[float], b: list[float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vec_norm(v: tuple[float, float, float]) -> float:
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def _angle_between_deg(v1: tuple[float, float, float], v2: tuple[float, float, float]) -> float:
    n1, n2 = _vec_norm(v1), _vec_norm(v2)
    if n1 < 1e-8 or n2 < 1e-8:
        return 0.0
    cos_t = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]) / (n1 * n2)))
    return math.degrees(math.acos(cos_t))


def _line_side_xz(line_xz: list[float], cam_xyz: list[float]) -> int:
    x1, z1, x2, z2 = line_xz
    cx, cz = cam_xyz[0], cam_xyz[2]
    cross = (x2 - x1) * (cz - z1) - (z2 - z1) * (cx - x1)
    if abs(cross) < 1e-6:
        return 0
    return 1 if cross > 0 else -1


def compute_visible_dimensions_m(lens_mm: float, dist_m: float, fmt: str) -> tuple[float, float, float]:
    """
    Full-frame 36mm cinema sensor equivalence:
      - 16:9_long  -> 36.00mm x 20.25mm active gate
      - 9:16_short -> 20.25mm x 36.00mm vertical portrait cinema gate
    Returns (visible_width_m, visible_height_m, threejs_fov_y_deg).
    """
    if fmt == "9:16_short":
        sensor_w_mm, sensor_h_mm = 20.25, 36.00
    else:
        sensor_w_mm, sensor_h_mm = 36.00, 20.25
    vis_w = 2.0 * dist_m * (sensor_w_mm * 0.5) / lens_mm
    vis_h = 2.0 * dist_m * (sensor_h_mm * 0.5) / lens_mm
    fov_y_deg = math.degrees(2.0 * math.atan((sensor_h_mm * 0.5) / lens_mm))
    return vis_w, vis_h, fov_y_deg


def lint_director_plan(
    plan: dict[str, Any],
    check_history: bool = True,
    history_override: list[dict[str, Any]] | None = None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    required_top = (
        "schema_version", "project_id", "channel", "format", "fps", "duration_s",
        "producer_brief", "anti_clone_declaration", "dramaturgy",
        "production_design", "scene_geography", "shots", "sound_dramaturgy",
    )
    for k in required_top:
        if k not in plan:
            errors.append(f"Missing required top-level section '{k}'.")
    if errors:
        return errors, warnings, {}

    fmt = plan["format"]
    fps = int(plan["fps"])
    dur = float(plan["duration_s"])
    tol = (1.0 / fps) + 1e-4

    # 1. Anti-Clone Creative Divergence Gate
    ac_report: dict[str, Any] = {}
    if check_history:
        ac_err, ac_warn, ac_report = validate_anti_clone(plan, history=history_override)
        errors.extend(ac_err)
        warnings.extend(ac_warn)

    # 2. Executive Producer Brief & Hook Speed
    pb = plan["producer_brief"]
    hook_s = float(pb.get("hook_lands_within_s", 99.0))
    if fmt == "9:16_short" and hook_s > 2.5:
        errors.append(f"9:16_short hook_lands_within_s={hook_s:.2f}s exceeds 2.50s scroll-survival threshold.")
    elif fmt == "16:9_long" and hook_s > 15.0:
        errors.append(f"16:9_long hook_lands_within_s={hook_s:.2f}s exceeds 15.0s cold-open threshold.")

    ep = pb.get("epistemic_ledger", {})
    total_ep = (
        len(ep.get("observed_evidence", []))
        + len(ep.get("scientific_inferences", []))
        + len(ep.get("illustrative_abstractions", []))
    )
    if total_ep == 0:
        errors.append("epistemic_ledger is empty: explicitly separate observed_evidence, scientific_inferences, and illustrative_abstractions.")

    why_not = plan["anti_clone_declaration"].get("why_not_previous_template", "")
    if len(why_not.strip()) < 25:
        errors.append("anti_clone_declaration.why_not_previous_template must explain in >=25 chars why this world/staging differs from past episodes.")

    # 3. Dramaturgy: Beat Map, Visual Routes, See/Hide Pairs, Motifs
    dram = plan["dramaturgy"]
    beats = dram.get("beats", [])
    if len(beats) < 3:
        errors.append("dramaturgy.beats must contain at least 3 narrative beats.")
    else:
        if abs(float(beats[0]["t0"])) > tol:
            errors.append(f"First beat '{beats[0]['beat_id']}' must start at t0=0.0.")
        for b1, b2 in zip(beats, beats[1:]):
            if abs(float(b1["t1"]) - float(b2["t0"])) > tol:
                errors.append(f"Beat gap/overlap between '{b1['beat_id']}' ({b1['t1']}) and '{b2['beat_id']}' ({b2['t0']}).")
        if abs(float(beats[-1]["t1"]) - dur) > tol:
            errors.append(f"Final beat '{beats[-1]['beat_id']}' ends at {beats[-1]['t1']} != duration_s {dur}.")

    routes_used = {b.get("visual_route") for b in beats if b.get("visual_route")}
    if len(routes_used) < 2:
        errors.append(
            f"Monotone visual routing: only {sorted(routes_used)} used across all beats. "
            "Combine at least 2 distinct routes (LITERAL_SPECIMEN, PROCESS_MECHANISM, PHYSICAL_ANALOGY, CONSEQUENCE_AFTERMATH, HUMAN_OR_CREATURE_WITNESS)."
        )

    # 4. Production Design: Color Script & Bruce Block 7-Component Climax Sync
    pd = plan["production_design"]
    cs = pd.get("color_script", {})
    base_hexes = {h.upper() for h in cs.get("base_hex", [])}
    accent_hex = cs.get("reserved_accent_hex", "").upper()
    if accent_hex in base_hexes:
        errors.append(
            f"Color script violation: reserved_accent_hex {accent_hex} is also in base_hex! "
            "Reserve the accent color strictly for the core focal mechanism/clue."
        )

    bb = pd.get("bruce_block_visual_arc", {})
    if beats:
        peak_intensity = max(float(b["intensity_0_to_100"]) for b in beats)
        beat_by_id = {b["beat_id"]: b for b in beats}
        climax_bid = bb.get("climax_beat_id", "")
        if climax_bid not in beat_by_id:
            errors.append(f"bruce_block_visual_arc.climax_beat_id '{climax_bid}' does not match any beat_id.")
        elif float(beat_by_id[climax_bid]["intensity_0_to_100"]) < peak_intensity - 5.0:
            errors.append(
                f"Bruce Block mismatch: climax_beat_id '{climax_bid}' has story intensity "
                f"{beat_by_id[climax_bid]['intensity_0_to_100']}, below peak story beat ({peak_intensity})."
            )
    if float(bb.get("climax_visual_contrast_0_to_100", 0)) < 65.0:
        errors.append("bruce_block_visual_arc.climax_visual_contrast_0_to_100 must be >= 65.0 at the climax.")
    if float(bb.get("resolution_visual_affinity_0_to_100", 0)) < 55.0:
        errors.append("bruce_block_visual_arc.resolution_visual_affinity_0_to_100 must be >= 55.0 so the ending visually resolves.")

    # 5. Scene Geography Map
    geo_map = {g["scene_id"]: g for g in plan.get("scene_geography", [])}
    if not geo_map:
        errors.append("scene_geography must define at least 1 physical scene map.")

    # 6. Shot-by-Shot Cinematography, Blocking, Optics, 180/30 Geometry & Eye-Trace
    shots = plan.get("shots", [])
    shot_map = {s["id"]: s for s in shots}
    beat_ids = {b["beat_id"] for b in beats}

    if abs(float(shots[0]["t0"])) > tol:
        errors.append(f"First shot '{shots[0]['id']}' must start at t0=0.0.")
    for s1, s2 in zip(shots, shots[1:]):
        if abs(float(s1["t1"]) - float(s2["t0"])) > tol:
            errors.append(f"Shot timeline gap/overlap: {s1['id']} ({s1['t1']}) -> {s2['id']} ({s2['t0']}).")
    if abs(float(shots[-1]["t1"]) - dur) > tol:
        errors.append(f"Last shot '{shots[-1]['id']}' ends at {shots[-1]['t1']} != duration_s {dur}.")

    moving_count = 0
    shallow_count = 0
    dolly_zoom_count = 0
    stillness_beats = 0
    rejected_alt_count = 0

    for idx, s in enumerate(shots):
        sid = s["id"]
        st0, st1 = float(s["t0"]), float(s["t1"])
        sdur = st1 - st0
        if sdur <= 0.0:
            errors.append(f"{sid}: shot duration must be positive ({st0}..{st1}).")
        elif sdur < 0.65:
            warnings.append(f"{sid}: very short shot ({sdur:.2f}s) — verify content curve is readable.")

        if s["beat_id"] not in beat_ids:
            errors.append(f"{sid}: unknown beat_id '{s['beat_id']}'.")
        if s["scene_id"] not in geo_map:
            errors.append(f"{sid}: unknown scene_id '{s['scene_id']}'.")

        # Vague buzzword guard
        for field_name in ("dramatic_purpose", "reason", "start_frame_desc", "end_frame_desc"):
            val = s.get(field_name, "")
            m = VAGUE_RE.search(val)
            if m:
                errors.append(
                    f"{sid}.{field_name}: forbidden vague buzzword '{m.group(0)}' — state exact story/spatial/optical purpose."
                )

        # Motivation & move discipline
        mv = s["move"]
        mot = s["motivation"]
        if mv == "static":
            stillness_beats += 1
        else:
            moving_count += 1
            if mot not in ACTIVE_MOTIVATIONS:
                errors.append(f"{sid}: active move '{mv}' requires an active motivation in {sorted(ACTIVE_MOTIVATIONS)}, got '{mot}'.")
            if not s.get("ease"):
                errors.append(f"{sid}: active move '{mv}' must specify an explicit 'ease' curve (e.g. 'easeInOutCubic', 'easeOutQuart').")
            if s.get("start_frame_desc", "").strip() == s.get("end_frame_desc", "").strip():
                errors.append(f"{sid}: active move '{mv}' has identical start_frame_desc and end_frame_desc — seal where the move starts and stops!")

        if s.get("held_stillness_beat"):
            stillness_beats += 1
        if mv == "dolly_zoom":
            dolly_zoom_count += 1
        if s.get("dof_mode") == "shallow":
            shallow_count += 1
        if s.get("rejected_alternative", "").strip():
            rejected_alt_count += 1

        # Hold-for-text vs distracting camera move
        for hw in s.get("hold_for_text", []) or []:
            if mv in TRANSLATIONAL_TEXT_CONFLICT_MOVES and hw[0] < st1 - tol and hw[1] > st0 + tol:
                errors.append(f"{sid}: camera move '{mv}' conflicts with hold_for_text reading window {hw}.")

        # Distance-First Optical Math & Horizontal Clipping Guard
        cam_pos = s["camera_pos_xyz"]
        look_at = s["look_at_xyz"]
        dist_m = _vec_norm(_vec_sub(cam_pos, look_at))
        if dist_m < 1e-4:
            errors.append(f"{sid}: camera_pos_xyz equals look_at_xyz (zero camera distance)!")
        else:
            lens_mm = float(s["lens_mm_equiv"])
            vis_w, vis_h, fov_y = compute_visible_dimensions_m(lens_mm, dist_m, fmt)
            subj_w = float(s["subject_width_m"])
            if s["shot_size"] in ("EWS", "WS", "MWS", "MS") and vis_w < subj_w * 1.18:
                errors.append(
                    f"{sid}: HORIZONTAL CLIPPING RISK in {fmt}! At dist={dist_m:.2f}m & lens={lens_mm:.0f}mm "
                    f"(Three.js fovY={fov_y:.1f} deg), visible width is {vis_w:.3f}m < 1.18 x subject_width_m ({subj_w * 1.18:.3f}m)."
                )

        # Wide-shot scale ruler check & 3-layer depth check
        layers = s.get("layers_fg_mg_bg", {})
        if mv in PARALLAX_MOVES:
            for lk in ("fg", "mg", "bg"):
                if len(layers.get(lk, "").strip()) < 3 or layers.get(lk, "").strip().lower() == "none":
                    errors.append(f"{sid}: parallax move '{mv}' requires explicit 3-layer depth staging (missing '{lk}' in layers_fg_mg_bg).")
        if s["shot_size"] in ("EWS", "WS"):
            geo = geo_map.get(s["scene_id"], {})
            if not geo.get("scale_reference_object"):
                errors.append(f"{sid}: wide shot requires scale_reference_object in scene_geography.")

        # 180-Degree Line of Action Check
        if s["scene_id"] in geo_map and not s.get("deliberate_axis_cross", False):
            geo = geo_map[s["scene_id"]]
            actual_side = _line_side_xz(geo["line_of_action_xz"], cam_pos)
            if actual_side not in (0, int(geo["allowed_camera_side"])):
                errors.append(
                    f"{sid}: 180-DEGREE AXIS VIOLATION in scene '{s['scene_id']}'! "
                    f"Camera {cam_pos} is on side {actual_side}, expected {geo['allowed_camera_side']} "
                    "(set deliberate_axis_cross=true ONLY if crossing on-camera or for intentional disorientation)."
                )

        # Sequence Continuity vs Previous Shot (30-Degree Rule + Eye-Trace Continuum + Anti-Monotony)
        if idx > 0:
            prev = shots[idx - 1]
            if prev["scene_id"] == s["scene_id"] and prev["subject_id"] == s["subject_id"]:
                v_prev = _vec_sub(prev["camera_pos_xyz"], prev["look_at_xyz"])
                v_curr = _vec_sub(cam_pos, look_at)
                ang_deg = _angle_between_deg(v_prev, v_curr)
                sz_step = abs(SHOT_SIZE_ORDER.index(prev["shot_size"]) - SHOT_SIZE_ORDER.index(s["shot_size"]))
                if ang_deg < 30.0 and sz_step == 0 and not s.get("deliberate_jump_cut", False):
                    errors.append(
                        f"{prev['id']} -> {sid}: 30-DEGREE JUMP-CUT VIOLATION on '{s['subject_id']}'! "
                        f"Camera moved only {ang_deg:.1f} deg (<30 deg) with 0 shot-size change ({s['shot_size']})."
                    )

            # Walter Murch Eye-Trace Quadrant Continuity
            ex0, ey0 = prev["eye_trace_end_xy"]
            ex1, ey1 = s["eye_trace_start_xy"]
            eye_jump = math.hypot(ex1 - ex0, ey1 - ey0)
            if eye_jump > 0.36 and not s.get("deliberate_eye_trace_shock", False):
                errors.append(
                    f"{prev['id']} -> {sid}: EYE-TRACE WHIPLASH! Viewer focus jumped {eye_jump:.2f} screen units "
                    f"({prev['eye_trace_end_xy']} -> {s['eye_trace_start_xy']}) > 0.36 limit without deliberate_eye_trace_shock=true."
                )

        if idx >= 2:
            p1, p2 = shots[idx - 2], shots[idx - 1]
            if (p1["shot_size"], p1["camera_angle"]) == (p2["shot_size"], p2["camera_angle"]) == (s["shot_size"], s["camera_angle"]):
                errors.append(
                    f"{p1['id']}->{p2['id']}->{sid}: 3 consecutive shots repeat identical framing ({s['shot_size']}, {s['camera_angle']})!"
                )

    # 7. See/Hide & Motif Temporal Ordering
    for sh in dram.get("see_hide_pairs", []):
        hid, rid = sh.get("hide_shot_id"), sh.get("reveal_shot_id")
        if hid not in shot_map or rid not in shot_map:
            errors.append(f"see_hide_pair '{sh.get('hidden_element')}' references missing shot_id ({hid} -> {rid}).")
        elif float(shot_map[hid]["t0"]) >= float(shot_map[rid]["t0"]):
            errors.append(
                f"see_hide_pair '{sh.get('hidden_element')}': hide_shot '{hid}' ({shot_map[hid]['t0']}s) "
                f"must precede reveal_shot '{rid}' ({shot_map[rid]['t0']}s)!"
            )

    for mf in dram.get("motifs", []):
        pid, cid = mf.get("planted_shot_id"), mf.get("callback_shot_id")
        if pid not in shot_map or cid not in shot_map:
            errors.append(f"motif '{mf.get('motif_name')}' references missing shot_id ({pid} -> {cid}).")
        elif float(shot_map[pid]["t0"]) >= float(shot_map[cid]["t0"]):
            errors.append(f"motif '{mf.get('motif_name')}': planted_shot '{pid}' must precede callback_shot '{cid}'.")

    # 8. Global Restraint & Pacing Budgets
    n_shots = len(shots)
    moving_ratio = moving_count / n_shots
    shallow_ratio = shallow_count / n_shots
    max_dz = 1 if fmt == "9:16_short" else 2

    if dolly_zoom_count > max_dz:
        errors.append(f"Dolly-zoom overuse: {dolly_zoom_count} used (maximum {max_dz} per {fmt}).")
    if stillness_beats == 0:
        errors.append("Zero stillness beats in the entire film! Place at least 1 static or held_stillness_beat shot so motion has contrast.")
    if moving_ratio > 0.70:
        errors.append(f"Camera restlessness: {moving_count}/{n_shots} ({moving_ratio:.0%}) moving shots exceeds 70% ceiling.")
    elif moving_ratio > 0.55:
        warnings.append(f"Moving-shot share is {moving_ratio:.0%} — check if 1-2 explanatory shots would hit harder static.")
    if shallow_ratio > 0.45:
        errors.append(f"Shallow-DoF overuse: {shallow_count}/{n_shots} ({shallow_ratio:.0%}) exceeds 45% budget.")
    if rejected_alt_count < min(3, n_shots):
        errors.append(
            f"Record a non-empty 'rejected_alternative' on at least the 3 key beats (found {rejected_alt_count})."
        )

    # 9. Sound Dramaturgy & Protected Climax Windows
    sd = plan["sound_dramaturgy"]
    pw_list = sd.get("protected_hud_free_climax_windows_s", [])
    total_pw = 0.0
    for w0, w1 in pw_list:
        if not (0.0 <= w0 < w1 <= dur + tol):
            errors.append(f"Invalid protected_hud_free_climax_window [{w0}, {w1}] outside [0, {dur}].")
        total_pw += (w1 - w0)
    if total_pw < 1.8:
        errors.append(f"Protected HUD-free pure-cinema climax duration ({total_pw:.2f}s) must be >= 1.80s.")

    # 10. Seamless Loop Closure Verification
    if pb.get("seamless_loop"):
        s_first, s_last = shots[0], shots[-1]
        if s_first["scene_id"] != s_last["scene_id"]:
            errors.append(
                f"seamless_loop=true requires final shot '{s_last['id']}' ({s_last['scene_id']}) "
                f"to return to opening scene '{s_first['scene_id']}'."
            )
        loop_eye = math.hypot(
            s_last["eye_trace_end_xy"][0] - s_first["eye_trace_start_xy"][0],
            s_last["eye_trace_end_xy"][1] - s_first["eye_trace_start_xy"][1],
        )
        if loop_eye > 0.12:
            errors.append(
                f"seamless_loop=true eye-trace seam mismatch: {loop_eye:.3f} > 0.12 "
                f"({s_last['eye_trace_end_xy']} -> {s_first['eye_trace_start_xy']})."
            )

    summary = {
        "project_id": plan["project_id"],
        "format": fmt,
        "duration_s": dur,
        "shots_count": n_shots,
        "beats_count": len(beats),
        "visual_routes_used": sorted(routes_used),
        "moving_shot_ratio": round(moving_ratio, 3),
        "shallow_dof_ratio": round(shallow_ratio, 3),
        "stillness_beats": stillness_beats,
        "protected_climax_total_s": round(total_pw, 2),
        "anti_clone": ac_report,
    }
    return errors, warnings, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Top1 Pre-Production director-plan.json")
    parser.add_argument("plan_json", help="Path to director-plan.json")
    parser.add_argument("--no-history", action="store_true", help="Skip historical anti-clone check")
    args = parser.parse_args(argv)

    with open(args.plan_json, "r", encoding="utf-8") as fh:
        plan = json.load(fh)

    errors, warnings, summary = lint_director_plan(plan, check_history=not args.no_history)
    for w in warnings:
        print(f"[WARN]  {w}")
    for e in errors:
        print(f"[ERROR] {e}")
    print("[DIRECTOR PLAN SUMMARY]", json.dumps(summary, indent=2))
    if errors:
        print(f"\nFAILED: {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    print(f"\nPASSED: 0 errors, {len(warnings)} warning(s). Cleared for Gate 2/3/4 Production!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
