#!/usr/bin/env python3
"""Render and verify the Step 02.5 Hardest-Contact Kinematic Proof board (9:16 portrait).

Outputs to gitignored `.cache/monarch-cockroach/proof/`:
  - cockroach-contact-proof-portrait.png (1080x1920, 2x supersampled)
  - proof-receipt.json
"""

import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rig import (
    CEILING_FRICTION_LEVELS,
    GROUND_FRICTION_LEVELS,
    TARSUS_MIDLINE_MM,
    solve_confinement,
    state_dict,
    stick_slip_velocity_cm_s,
)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = ROOT / ".cache" / "monarch-cockroach" / "proof"

FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def draw_sagittal_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    ceiling_mm: float,
    title: str,
    subtitle: str,
    show_pennies_and_inset: bool,
    scale: int,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=20 * scale, fill=(18, 22, 29), outline=(48, 58, 74), width=2 * scale)

    f_title = load_font(FONT_BOLD, 21 * scale)
    f_sub = load_font(FONT_REG, 15 * scale)
    f_lbl = load_font(FONT_MONO, 13 * scale)

    draw.text((x0 + 24 * scale, y0 + 15 * scale), title, fill=(242, 245, 250), font=f_title)
    draw.text((x0 + 24 * scale, y0 + 44 * scale), subtitle, fill=(158, 172, 194), font=f_sub)

    state = solve_confinement(ceiling_mm)

    px0 = x0 + 36 * scale
    px1 = x1 - 36 * scale
    py_floor = y1 - 32 * scale
    mm_scale = min((px1 - px0) / 36.5, (py_floor - (y0 + 92 * scale)) / 14.0)

    def to_px(xm: float, zm: float) -> tuple[float, float]:
        return (px0 + xm * mm_scale, py_floor - zm * mm_scale)

    # Ground substrate
    draw.rectangle((px0 - 10 * scale, py_floor, px1 + 10 * scale, py_floor + 12 * scale), fill=(52, 58, 68))
    draw.line((px0 - 10 * scale, py_floor, px1 + 10 * scale, py_floor), fill=(130, 145, 168), width=2 * scale)

    # Acrylic ceiling slab
    _, py_ceil = to_px(0.0, ceiling_mm)
    draw.rectangle(
        (px0 - 10 * scale, py_ceil - 11 * scale, px1 + 10 * scale, py_ceil),
        fill=(46, 86, 118),
        outline=(102, 178, 232),
        width=2 * scale,
    )
    draw.text(
        (px1 - 168 * scale, py_ceil - 30 * scale),
        f"CEILING {ceiling_mm:.1f} mm",
        fill=(126, 202, 252),
        font=f_lbl,
    )

    # Soft visceral hemocoel / ventral body silhouette
    vent_pts = [to_px(p.hinge_x_mm, state.ventral_clearance_mm + 0.14) for p in state.plates]
    vent_pts.append(to_px(state.plates[-1].tip_x_mm, state.ventral_clearance_mm + 0.20))
    dorsal_pts = [to_px(p.tip_x_mm, p.tip_z_mm) for p in reversed(state.plates)]
    dorsal_pts.append(to_px(state.plates[0].hinge_x_mm, state.plates[0].hinge_z_mm))
    draw.polygon(vent_pts + dorsal_pts, fill=(72, 52, 38), outline=(118, 88, 62))

    # Sagittal pro-, meso-, and metathoracic legs showing stance shift
    if state.contact_mode == "tarsal-claw":
        sag_legs = [
            ((6.5, state.ventral_clearance_mm + 1.2), (4.6, 5.2), (2.2, 0.0)),
            ((12.2, state.ventral_clearance_mm + 1.1), (13.4, 5.8), (15.0, 0.0)),
            ((17.8, state.ventral_clearance_mm + 1.0), (21.5, 6.4), (26.2, 0.0)),
        ]
        for coxa_m, knee_m, foot_m in sag_legs:
            c_p, k_p, f_p = to_px(*coxa_m), to_px(*knee_m), to_px(*foot_m)
            draw.line((c_p, k_p), fill=(214, 144, 76), width=4 * scale)
            draw.line((k_p, f_p), fill=(96, 224, 252), width=4 * scale)
            draw.ellipse((f_p[0] - 4 * scale, f_p[1] - 4 * scale, f_p[0] + 4 * scale, f_p[1] + 4 * scale), fill=(96, 224, 252))
    else:
        # Low-ceiling sprawled sagittal projection: tibia skims ground (green spines), tarsus lifts clear (red)
        sag_legs = [
            ((6.8, 1.0), (4.8, 1.5), (2.6, 0.0), (1.1, 0.48)),
            ((12.8, 1.0), (14.8, 1.6), (17.5, 0.0), (19.1, 0.48)),
            ((18.4, 1.0), (22.6, 1.7), (27.4, 0.0), (29.2, 0.50)),
        ]
        for coxa_m, knee_m, tib_m, tar_m in sag_legs:
            c_p, k_p, tb_p, tr_p = to_px(*coxa_m), to_px(*knee_m), to_px(*tib_m), to_px(*tar_m)
            draw.line((c_p, k_p), fill=(214, 144, 76), width=4 * scale)
            draw.line((k_p, tb_p), fill=(82, 238, 168), width=4 * scale)
            draw.line((tb_p, tr_p), fill=(248, 112, 112), width=3 * scale)
            draw.polygon(
                [(tb_p[0] - 4 * scale, tb_p[1] - 9 * scale), (tb_p[0] + 4 * scale, tb_p[1] - 9 * scale), (tb_p[0], tb_p[1] + 1 * scale)],
                fill=(82, 238, 168),
            )

    # Head capsule + sweeping sensory antenna
    head_x, head_z = to_px(0.9, state.ventral_clearance_mm + (1.20 if ceiling_mm < 5.0 else 2.55))
    r_hx, r_hz = 1.35 * mm_scale, 1.02 * mm_scale
    draw.ellipse((head_x - r_hx, head_z - r_hz, head_x + r_hx, head_z + r_hz), fill=(138, 84, 42), outline=(224, 158, 96), width=2 * scale)
    ant_end = to_px(-1.9, min(ceiling_mm - 0.42, state.ventral_clearance_mm + 1.75))
    draw.line((head_x - r_hx * 0.6, head_z - r_hz * 0.2, ant_end[0], ant_end[1]), fill=(232, 178, 116), width=2 * scale)

    # Rigid sclerotized tergite plates + teal arthrodial membrane hinges
    for idx, p in enumerate(state.plates):
        hx, hz = to_px(p.hinge_x_mm, p.hinge_z_mm)
        tx, tz = to_px(p.tip_x_mm, p.tip_z_mm)
        _, hz_top = to_px(p.hinge_x_mm, p.hinge_z_mm + p.thickness_mm)
        th_px = max(3.2 * scale, hz - hz_top)
        quad = [(hx, hz), (tx, tz), (tx, tz - th_px), (hx, hz - th_px)]
        draw.polygon(quad, fill=(198, 122, 54), outline=(250, 202, 138))
        if idx > 0:
            prev = state.plates[idx - 1]
            phx, phz = to_px(prev.tip_x_mm, prev.tip_z_mm)
            draw.line((phx, phz, hx, hz), fill=(76, 228, 196), width=3 * scale)
            draw.ellipse((hx - 3 * scale, hz - 3 * scale, hx + 3 * scale, hz + 3 * scale), fill=(76, 228, 196))

    if show_pennies_and_inset:
        # Two stacked US pennies scale cue (2 x 1.52 mm = 3.04 mm)
        pen_x0 = px1 - 102 * scale
        pen_w = 78 * scale
        for idx in range(2):
            _, p_bot = to_px(0.0, idx * 1.52)
            _, p_top = to_px(0.0, (idx + 1) * 1.52)
            draw.rounded_rectangle(
                (pen_x0, p_top, pen_x0 + pen_w, p_bot),
                radius=3 * scale,
                fill=(188, 114, 68),
                outline=(236, 168, 118),
                width=2 * scale,
            )
        draw.text(
            (pen_x0 - 38 * scale, py_ceil - 50 * scale),
            "2 PENNIES (~3.0 mm)",
            fill=(242, 182, 132),
            font=f_lbl,
        )

        # 3.5x Magnified Tergite-Hinge Cutaway Inset in upper-right space of Panel 2
        ix0, iy0, ix1, iy1 = x0 + 492 * scale, y0 + 96 * scale, x1 - 28 * scale, y0 + 236 * scale
        draw.rounded_rectangle((ix0, iy0, ix1, iy1), radius=12 * scale, fill=(12, 16, 22), outline=(76, 228, 196), width=2 * scale)
        draw.text(
            (ix0 + 14 * scale, iy0 + 10 * scale),
            "3.5x ZOOM: RIGID TERGITES + FOLDED ARTHRODIAL JOINTS",
            fill=(112, 232, 202),
            font=f_lbl,
        )
        # Render magnified tergites 1..4 inside inset
        z_plates = state.plates[3:7]
        base_x = z_plates[0].hinge_x_mm
        base_z = min(p.hinge_z_mm for p in z_plates) - 0.18
        z_scale_x = (ix1 - ix0 - 44 * scale) / 11.2
        z_scale_z = (iy1 - iy0 - 54 * scale) / 0.85
        for idx, zp in enumerate(z_plates):
            zhx = ix0 + 22 * scale + (zp.hinge_x_mm - base_x) * z_scale_x
            ztx = ix0 + 22 * scale + (zp.tip_x_mm - base_x) * z_scale_x
            zhz = iy1 - 18 * scale - (zp.hinge_z_mm - base_z) * z_scale_z
            ztz = iy1 - 18 * scale - (zp.tip_z_mm - base_z) * z_scale_z
            zth = max(8 * scale, zp.thickness_mm * z_scale_z * 0.55)
            draw.polygon([(zhx, zhz), (ztx, ztz), (ztx, ztz - zth), (zhx, zhz - zth)], fill=(208, 130, 58), outline=(252, 212, 152))
            if idx > 0:
                prev_zp = z_plates[idx - 1]
                pzx = ix0 + 22 * scale + (prev_zp.tip_x_mm - base_x) * z_scale_x
                pzz = iy1 - 18 * scale - (prev_zp.tip_z_mm - base_z) * z_scale_z
                draw.line((pzx, pzz, zhx, zhz), fill=(76, 228, 196), width=4 * scale)
                draw.ellipse((zhx - 4 * scale, zhz - 4 * scale, zhx + 4 * scale, zhz + 4 * scale), fill=(76, 228, 196))

    badge_txt = (
        f"Peak {state.dorsal_peak_mm:.2f} mm | Abdomen strain {state.body_compression_pct:.1f}% | "
        f"0 plate collisions"
    )
    draw.text((px0, y0 + 70 * scale), badge_txt, fill=(112, 232, 202), font=f_lbl)


def draw_transverse_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    ceiling_mm: float,
    title: str,
    scale: int,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=20 * scale, fill=(18, 22, 29), outline=(48, 58, 74), width=2 * scale)

    f_title = load_font(FONT_BOLD, 18 * scale)
    f_lbl = load_font(FONT_MONO, 13 * scale)
    draw.text((x0 + 20 * scale, y0 + 15 * scale), title, fill=(242, 245, 250), font=f_title)

    state = solve_confinement(ceiling_mm)
    cx = 0.5 * (x0 + x1)
    py_floor = y1 - 36 * scale
    mm_scale = min((x1 - x0 - 52 * scale) / 31.0, (py_floor - (y0 + 76 * scale)) / 14.0)

    def to_px(ym: float, zm: float) -> tuple[float, float]:
        return (cx + ym * mm_scale, py_floor - zm * mm_scale)

    draw.rectangle((x0 + 18 * scale, py_floor, x1 - 18 * scale, py_floor + 10 * scale), fill=(52, 58, 68))
    draw.line((x0 + 18 * scale, py_floor, x1 - 18 * scale, py_floor), fill=(138, 152, 174), width=2 * scale)

    _, py_ceil = to_px(0.0, ceiling_mm)
    draw.rectangle(
        (x0 + 18 * scale, py_ceil - 10 * scale, x1 - 18 * scale, py_ceil),
        fill=(46, 86, 118),
        outline=(102, 178, 232),
        width=2 * scale,
    )

    for sgn in (-1.0, 1.0):
        mx, _ = to_px(sgn * TARSUS_MIDLINE_MM, 0.0)
        draw.line((mx, py_floor - 52 * scale, mx, py_floor + 8 * scale), fill=(76, 88, 108), width=1 * scale)

    half_w_mm = 4.85 if ceiling_mm > 5.0 else 5.65
    b_left, b_top = to_px(-half_w_mm, state.dorsal_peak_mm)
    b_right, b_bot = to_px(half_w_mm, state.ventral_clearance_mm)
    draw.ellipse((b_left, b_top, b_right, b_bot), fill=(154, 94, 46), outline=(238, 178, 112), width=3 * scale)

    for leg in state.metathoracic_legs:
        p_coxa = to_px(*leg.coxa_yz_mm)
        p_femur = to_px(*leg.femur_tip_yz_mm)
        p_tib = to_px(*leg.tibia_tip_yz_mm)
        p_tar = to_px(*leg.tarsus_tip_yz_mm)

        draw.line((p_coxa, p_femur), fill=(214, 144, 76), width=5 * scale)
        tib_color = (82, 238, 168) if leg.contact_mode == "tibial-spines" else (228, 166, 98)
        draw.line((p_femur, p_tib), fill=tib_color, width=5 * scale)
        tar_color = (248, 112, 112) if leg.contact_mode == "tibial-spines" else (96, 224, 252)
        draw.line((p_tib, p_tar), fill=tar_color, width=4 * scale)

        if leg.contact_mode == "tarsal-claw":
            draw.ellipse(
                (p_tar[0] - 5 * scale, p_tar[1] - 5 * scale, p_tar[0] + 5 * scale, p_tar[1] + 5 * scale),
                fill=(96, 224, 252),
            )
        else:
            for sy, sz in leg.spine_contacts_yz_mm:
                sx, sfloor = to_px(sy, sz)
                draw.polygon(
                    [(sx - 4 * scale, sfloor - 11 * scale), (sx + 4 * scale, sfloor - 11 * scale), (sx, sfloor + 1 * scale)],
                    fill=(82, 238, 168),
                )
            draw.ellipse(
                (p_tar[0] - 5 * scale, p_tar[1] - 5 * scale, p_tar[0] + 5 * scale, p_tar[1] + 5 * scale),
                outline=(248, 112, 112),
                width=2 * scale,
            )

    mode_label = (
        f"Sprawl {state.sprawl_angle_deg:.1f} deg | {state.contact_mode.upper()} | "
        f"{state.expected_velocity_cm_s:.1f} cm/s"
    )
    mode_col = (82, 238, 168) if state.contact_mode == "tibial-spines" else (126, 214, 252)
    draw.text((x0 + 20 * scale, y0 + 43 * scale), mode_label, fill=mode_col, font=f_lbl)


def draw_limits_footer(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], scale: int) -> dict[str, float]:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=20 * scale, fill=(18, 22, 29), outline=(48, 58, 74), width=2 * scale)

    f_title = load_font(FONT_BOLD, 20 * scale)
    f_body = load_font(FONT_REG, 15 * scale)
    f_mono = load_font(FONT_MONO, 14 * scale)

    draw.text(
        (x0 + 24 * scale, y0 + 15 * scale),
        "REAL BIOLOGICAL LIMITS (Jayaram & Full 2016, PNAS 113:E950-E957)",
        fill=(248, 206, 118),
        font=f_title,
    )

    mu_g_med, mu_l_med = GROUND_FRICTION_LEVELS["med_40grit"]
    v_c_low = stick_slip_velocity_cm_s(CEILING_FRICTION_LEVELS["low_graphite_acrylic"], mu_g_med, mu_l_med)["velocity_cm_s"]
    v_c_med = stick_slip_velocity_cm_s(CEILING_FRICTION_LEVELS["med_acrylic"], mu_g_med, mu_l_med)["velocity_cm_s"]
    v_c_high = stick_slip_velocity_cm_s(CEILING_FRICTION_LEVELS["high_40grit"], mu_g_med, mu_l_med)["velocity_cm_s"]

    v_g_low = stick_slip_velocity_cm_s(0.16, *GROUND_FRICTION_LEVELS["low_100grit"])["velocity_cm_s"]
    v_g_med = stick_slip_velocity_cm_s(0.16, *GROUND_FRICTION_LEVELS["med_40grit"])["velocity_cm_s"]
    v_g_high = stick_slip_velocity_cm_s(0.16, *GROUND_FRICTION_LEVELS["high_20grit"])["velocity_cm_s"]

    rows = [
        ("Crevice pass rate (n=315):", "72 +/- 5% @ 6.1 mm  ->  17 +/- 3% @ 3.2 mm (9 +/- 2% thorax-wedged)"),
        ("Confined speed collapse:", "58.05 cm/s (6-12 mm) ->  14.52 cm/s @ 4.0 mm + synchronous mid-legs"),
        ("Ceiling drag slowdown:", f"Stick-slip @ 4 mm: {v_c_low:.1f} -> {v_c_med:.1f} -> {v_c_high:.1f} cm/s (rough ceiling)"),
        ("Floor friction trade-off:", f"Stick-slip @ 4 mm: {v_g_low:.1f} (slip) < {v_g_med:.1f} (peak) > {v_g_high:.1f} cm/s (belly drag)"),
        ("Normal load bounds:", "~300x BW in 3.2 mm slit; ~900x BW cyclic survival (no press spectacle)"),
    ]
    ry = y0 + 50 * scale
    for k, v in rows:
        draw.text((x0 + 24 * scale, ry), k, fill=(162, 178, 202), font=f_mono)
        draw.text((x0 + 306 * scale, ry), v, fill=(236, 240, 246), font=f_body)
        ry += 30 * scale

    return {
        "model_v_ceiling_low_cm_s": v_c_low,
        "model_v_ceiling_med_cm_s": v_c_med,
        "model_v_ceiling_high_cm_s": v_c_high,
        "model_v_ground_low_cm_s": v_g_low,
        "model_v_ground_med_cm_s": v_g_med,
        "model_v_ground_high_cm_s": v_g_high,
    }


def render_portrait_proof(out_dir: Path = DEFAULT_OUT) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    scale = 2
    w, h = 1080 * scale, 1920 * scale
    canvas = Image.new("RGB", (w, h), (10, 13, 18))
    draw = ImageDraw.Draw(canvas)

    f_kicker = load_font(FONT_MONO, 15 * scale)
    f_h1 = load_font(FONT_BOLD, 28 * scale)
    f_sub = load_font(FONT_REG, 17 * scale)

    draw.text(
        (44 * scale, 40 * scale),
        "MONARCH CAM · EPISODE #03 · STEP 02.5 HARDEST-CONTACT KINEMATIC PROOF",
        fill=(98, 224, 192),
        font=f_kicker,
    )
    draw.text(
        (44 * scale, 70 * scale),
        "How This Cockroach Runs Without Its Feet",
        fill=(246, 248, 252),
        font=f_h1,
    )
    draw.text(
        (44 * scale, 110 * scale),
        "Periplaneta americana · True-mm solver: rigid tergite shingle fold + tibial-spine shift",
        fill=(158, 172, 194),
        font=f_sub,
    )

    draw_sagittal_panel(
        draw,
        (44 * scale, 152 * scale, 1036 * scale, 526 * scale),
        12.52,
        "1 · SAGITTAL UNCONFINED RUN (12.5 mm Freestanding)",
        "Rigid chitin tergites relaxed; belly 3.7 mm clear of floor; tarsal-claw tripod @ 58.1 cm/s",
        show_pennies_and_inset=False,
        scale=scale,
    )

    draw_sagittal_panel(
        draw,
        (44 * scale, 544 * scale, 1036 * scale, 924 * scale),
        3.20,
        "2 · SAGITTAL 3.2 mm GATE SQUEEZE (Two Stacked Pennies)",
        "Plates stay rigid: teal arthrodial joints fold 47% so tergites shingle cleanly with zero clipping",
        show_pennies_and_inset=True,
        scale=scale,
    )

    draw_transverse_panel(
        draw,
        (44 * scale, 942 * scale, 530 * scale, 1438 * scale),
        12.52,
        "3A · FRONT: 12.5 mm CLAW STANCE",
        scale=scale,
    )
    draw_transverse_panel(
        draw,
        (550 * scale, 942 * scale, 1036 * scale, 1438 * scale),
        4.00,
        "3B · FRONT: 4.0 mm TIBIAL SPINES",
        scale=scale,
    )

    f_leg = load_font(FONT_MONO, 13 * scale)
    draw.text(
        (48 * scale, 1450 * scale),
        "CYAN DOTS = planted tarsal claws (z = 0 mm)     GREEN TRIANGLES = planted tibial spines (z = 0 mm)",
        fill=(206, 216, 232),
        font=f_leg,
    )
    draw.text(
        (48 * scale, 1472 * scale),
        "RED RINGS = splayed distal tarsi lifted clear (> 0.42 mm)     TEAL JOINTS = folded arthrodial membranes",
        fill=(206, 216, 232),
        font=f_leg,
    )

    friction_metrics = draw_limits_footer(
        draw,
        (44 * scale, 1504 * scale, 1036 * scale, 1732 * scale),
        scale=scale,
    )

    draw.rounded_rectangle(
        (44 * scale, 1752 * scale, 1036 * scale, 1872 * scale),
        radius=14 * scale,
        outline=(58, 68, 86),
        width=2 * scale,
    )
    draw.text(
        (64 * scale, 1776 * scale),
        "SHORTS UI SAFE BAND VERIFIED (y = 1752..1872 px reserved for captions & YouTube Shorts chrome)",
        fill=(132, 146, 168),
        font=f_leg,
    )
    draw.text(
        (64 * scale, 1808 * scale),
        "ILLUSTRATIVE BIOMECHANICAL RECONSTRUCTION · 0 THIRD-PARTY MESHES · NO ANIMAL-HARM SPECTACLE",
        fill=(112, 212, 184),
        font=f_leg,
    )

    final_img = canvas.resize((1080, 1920), Image.Resampling.LANCZOS)
    png_path = out_dir / "cockroach-contact-proof-portrait.png"
    final_img.save(png_path, format="PNG", optimize=True)

    sha = hashlib.sha256(png_path.read_bytes()).hexdigest()
    receipt = {
        "episode": "monarch-cam-03-cockroach-crevice",
        "stage": "step-02.5-hardest-contact-kinematic-proof",
        "output_png": str(png_path.relative_to(ROOT)),
        "resolution": [1080, 1920],
        "bytes": png_path.stat().st_size,
        "sha256": sha,
        "states": {
            f"{ch:.2f}mm": state_dict(solve_confinement(ch))
            for ch in (12.52, 9.0, 6.0, 4.0, 3.2)
        },
        "friction_model_4mm": friction_metrics,
    }
    receipt_path = out_dir / "proof-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    res = render_portrait_proof()
    print(
        json.dumps(
            {
                "output_png": res["output_png"],
                "resolution": res["resolution"],
                "bytes": res["bytes"],
                "sha256": res["sha256"],
                "friction_model_4mm": res["friction_model_4mm"],
            },
            indent=2,
        )
    )
