#!/usr/bin/env python3
"""Parametric kinematic, tergite-fold, and stick-slip solver for Periplaneta americana.

Grounded in primary measurements and analytical model from:
Jayaram K, Full RJ (2016) "Cockroaches traverse crevices, crawl rapidly in
confined spaces, and inspire a soft, legged robot", PNAS 113(8):E950-E957
(PMCID: PMC4776529, DOI: 10.1073/pnas.1514591113).

All geometry is illustrative biomechanical reconstruction at true millimeter
scale (body length 31.10 mm, freestanding height 12.52 mm) with zero third-party
meshes or reused paper figures.
"""

from dataclasses import asdict, dataclass
import math
from typing import Dict, List, Tuple

# Primary morphometrics (Jayaram & Full 2016, Results & Table S1)
BODY_LENGTH_MM = 31.10
BODY_MASS_G = 0.76
FREESTANDING_HEIGHT_MM = 12.52
TARSUS_MIDLINE_MM = 11.89
STRIDE_PERIOD_MS = 61.05

# Table S1 sagittal cross-sections: (rostrocaudal_fraction, label, unloaded_mm, loaded_100g_mm)
CROSS_SECTIONS: Tuple[Tuple[float, str, float, float], ...] = (
    (0.10, "head-pronotum", 6.6, 3.1),
    (0.25, "prothorax-coxa", 8.8, 3.8),
    (0.37, "mesothorax-coxa", 8.4, 3.6),
    (0.50, "metathorax-coxa", 7.7, 3.5),
    (0.75, "mid-abdomen", 5.5, 3.0),
)

# Rigid dorsal plate (tergite) chord lengths in mm along the sagittal profile.
# Plates remain rigid (constant chord length & thickness); compression folds the
# soft arthrodial membranes at hinges between overlapping plates.
PLATE_SPECS: Tuple[Tuple[str, float, float, float], ...] = (
    ("pronotum", 0.03, 8.20, 0.36),
    ("mesonotum", 0.27, 4.40, 0.32),
    ("metanotum", 0.39, 4.30, 0.32),
    ("tergite-1", 0.51, 2.90, 0.26),
    ("tergite-2", 0.59, 2.85, 0.26),
    ("tergite-3", 0.67, 2.75, 0.25),
    ("tergite-4", 0.75, 2.60, 0.24),
    ("tergite-5", 0.83, 2.40, 0.23),
    ("tergite-6", 0.90, 2.10, 0.22),
)

# Table S2 friction benchmarks at 4-mm confinement
CEILING_FRICTION_LEVELS: Dict[str, float] = {
    "low_graphite_acrylic": 0.09,
    "med_acrylic": 0.14,
    "high_40grit": 0.46,
}
GROUND_FRICTION_LEVELS: Dict[str, Tuple[float, float]] = {
    # label -> (mu_body_kinetic, mu_leg_tibial_spines)
    "low_100grit": (0.37, 0.84),
    "med_40grit": (0.46, 1.73),
    "high_20grit": (0.76, 2.04),
}


@dataclass(frozen=True)
class PlatePose:
    name: str
    hinge_x_mm: float
    hinge_z_mm: float
    tip_x_mm: float
    tip_z_mm: float
    chord_mm: float
    thickness_mm: float
    pitch_deg: float
    arthrodial_fold_deg: float


@dataclass(frozen=True)
class LegPose:
    side: str  # "L" or "R"
    coxa_yz_mm: Tuple[float, float]
    femur_tip_yz_mm: Tuple[float, float]
    tibia_base_yz_mm: Tuple[float, float]
    tibia_tip_yz_mm: Tuple[float, float]
    tarsus_tip_yz_mm: Tuple[float, float]
    spine_contacts_yz_mm: List[Tuple[float, float]]
    sprawl_angle_deg: float
    contact_mode: str  # "tarsal-claw" | "tibial-spines"
    tarsus_clearance_mm: float


@dataclass(frozen=True)
class ConfinementState:
    ceiling_mm: float
    ventral_clearance_mm: float
    dorsal_peak_mm: float
    body_compression_pct: float
    sprawl_angle_deg: float
    contact_mode: str
    gait_mode: str
    expected_velocity_cm_s: float
    plates: List[PlatePose]
    metathoracic_legs: List[LegPose]


def clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def section_height_mm(frac: float, compression_alpha: float) -> float:
    """Interpolate sagittal body thickness between unloaded (alpha=0) and 100g-loaded (alpha=1)."""
    a = clamp(compression_alpha, 0.0, 1.0)
    pts = CROSS_SECTIONS
    if frac <= pts[0][0]:
        _, _, ul, ld = pts[0]
        return ul + a * (ld - ul)
    if frac >= pts[-1][0]:
        _, _, ul, ld = pts[-1]
        return ul + a * (ld - ul)
    for i in range(len(pts) - 1):
        f0, _, ul0, ld0 = pts[i]
        f1, _, ul1, ld1 = pts[i + 1]
        if f0 <= frac <= f1:
            t = (frac - f0) / (f1 - f0)
            h0 = ul0 + a * (ld0 - ul0)
            h1 = ul1 + a * (ld1 - ul1)
            return h0 + t * (h1 - h0)
    return 4.0


def solve_confinement(ceiling_mm: float) -> ConfinementState:
    """Solve body posture, rigid tergite imbrication, and metathoracic limb contact for a ceiling height."""
    if not (3.0 <= ceiling_mm <= 15.0):
        raise ValueError(f"ceiling_mm={ceiling_mm} outside modeled [3.0, 15.0] mm window")

    # Above 9 mm: elevated running (ventral belly clear of floor).
    # 9 mm -> 6 mm: crouched posture drops ventral clearance to 0 before body compression starts at ~6 mm.
    # Below 6.2 mm: arthrodial membranes fold progressively up to maximum compression near 3.2 mm.
    if ceiling_mm >= 9.0:
        t_elev = clamp((ceiling_mm - 9.0) / (FREESTANDING_HEIGHT_MM - 9.0), 0.0, 1.0)
        ventral_z = 0.45 + t_elev * (3.72 - 0.45)
        comp_alpha = 0.0
    elif ceiling_mm > 6.2:
        t_crouch = (ceiling_mm - 6.2) / (9.0 - 6.2)
        ventral_z = 0.08 + t_crouch * (0.45 - 0.08)
        comp_alpha = (1.0 - t_crouch) * 0.34
    else:
        ventral_z = 0.0
        # Solve compression_alpha so thickest thoracic section + plate thickness fits cleanly under ceiling_mm.
        lo, hi = 0.34, 1.0
        for _ in range(32):
            mid = 0.5 * (lo + hi)
            peak = section_height_mm(0.25, mid) + 0.36
            if peak > ceiling_mm - 0.04:
                lo = mid
            else:
                hi = mid
        comp_alpha = hi
        # At extreme 3.2 mm gate, thorax experiences full membrane fold + slight lateral/longitudinal ovalization.
        if section_height_mm(0.25, comp_alpha) + 0.36 > ceiling_mm - 0.02:
            comp_alpha = 1.0

    # Longitudinal extension as soft intersegmental membranes telescope/flatten slightly under load.
    length_scale = 1.0 + 0.045 * comp_alpha
    plates: List[PlatePose] = []
    prev_bottom_at_next = None

    for idx, (name, frac, chord_mm, thick_mm) in enumerate(PLATE_SPECS):
        hx = frac * BODY_LENGTH_MM * length_scale
        raw_sec_h = section_height_mm(frac, comp_alpha)
        # Thoracic ovalization in the tightest 3.0-3.8 mm horizontal slit (constant hemocoel volume shifts laterally).
        max_allowed_top = ceiling_mm - 0.05
        sec_h = min(raw_sec_h, max_allowed_top - ventral_z - thick_mm)
        sec_h = max(sec_h, 2.15)

        hz = ventral_z + sec_h
        # Each overlapping tergite shingle-steps slightly above the next posterior plate's anterior hinge
        # while staying strictly below ceiling_mm and preserving exact rigid chord_mm.
        next_frac = PLATE_SPECS[idx + 1][1] if idx + 1 < len(PLATE_SPECS) else min(1.0, frac + 0.07)
        next_raw_h = section_height_mm(next_frac, comp_alpha)
        next_h = max(2.05, min(next_raw_h, max_allowed_top - ventral_z - thick_mm))
        # Anterior plate overlaps above posterior hinge by thickness + 0.04 mm arthrodial gap (zero clipping).
        target_tip_z = min(max_allowed_top - thick_mm, ventral_z + next_h + 0.04 + 0.06 * (1.0 - comp_alpha))
        dz = clamp(target_tip_z - hz, -0.85 * chord_mm, 0.85 * chord_mm)
        dx = math.sqrt(max(1e-6, chord_mm * chord_mm - dz * dz))
        tx = hx + dx
        tz = hz + dz
        pitch_deg = math.degrees(math.atan2(dz, dx))
        unloaded_dz = section_height_mm(next_frac, 0.0) - section_height_mm(frac, 0.0)
        unloaded_pitch = math.degrees(math.atan2(clamp(unloaded_dz, -0.8 * chord_mm, 0.8 * chord_mm), chord_mm))
        fold_deg = abs(pitch_deg - unloaded_pitch)

        if prev_bottom_at_next is not None:
            # Enforce non-interpenetration at shingle overlap: current hinge top <= previous tip bottom.
            hz = min(hz, prev_bottom_at_next - 0.02)
            dz = clamp(target_tip_z - hz, -0.85 * chord_mm, 0.85 * chord_mm)
            dx = math.sqrt(max(1e-6, chord_mm * chord_mm - dz * dz))
            tx = hx + dx
            tz = hz + dz
            pitch_deg = math.degrees(math.atan2(dz, dx))

        prev_bottom_at_next = tz
        plates.append(
            PlatePose(
                name=name,
                hinge_x_mm=round(hx, 4),
                hinge_z_mm=round(hz, 4),
                tip_x_mm=round(tx, 4),
                tip_z_mm=round(tz, 4),
                chord_mm=chord_mm,
                thickness_mm=thick_mm,
                pitch_deg=round(pitch_deg, 3),
                arthrodial_fold_deg=round(fold_deg, 3),
            )
        )

    dorsal_peak = max(max(p.hinge_z_mm, p.tip_z_mm) + p.thickness_mm for p in plates)
    unloaded_abdomen = section_height_mm(0.75, 0.0)
    current_abdomen = min(section_height_mm(0.75, comp_alpha), ceiling_mm - 0.30)
    compression_pct = clamp(100.0 * (1.0 - current_abdomen / unloaded_abdomen), 0.0, 60.0)

    # Transverse limb kinematics (front/rear view in Y-Z plane, midline Y=0, floor Z=0).
    # Tarsus midline distance remains ~11.89 mm across ceiling heights (Jayaram & Full 2016, Fig. 2C).
    com_z = ventral_z + 0.52 * (dorsal_peak - ventral_z)
    sprawl_rad = math.atan2(TARSUS_MIDLINE_MM, max(1.65, com_z))
    sprawl_deg = clamp(math.degrees(sprawl_rad), 48.0, 81.5)

    coxa_y = 2.35 + 0.55 * comp_alpha
    coxa_z = ventral_z + 0.32 * (dorsal_peak - ventral_z)

    # Switch between normal tarsal-claw stance (> 4.6 mm) and sprawled tibial-spine stance (<= 4.6 mm).
    if ceiling_mm > 4.6:
        contact_mode = "tarsal-claw"
        femur_y = coxa_y + 4.35
        femur_z = min(ceiling_mm - 0.32, coxa_z + 1.55 * clamp((ceiling_mm - 4.6) / 7.9, 0.15, 1.0))
        tibia_tip_y = TARSUS_MIDLINE_MM - 1.55
        tibia_tip_z = 0.58 + 0.42 * clamp((ceiling_mm - 4.6) / 7.9, 0.0, 1.0)
        tarsus_tip_y = TARSUS_MIDLINE_MM
        tarsus_tip_z = 0.0  # Claw/arolium engaged on ground
        tarsus_clearance = 0.0
        spine_contacts: List[Tuple[float, float]] = []
    else:
        contact_mode = "tibial-spines"
        # Femur splays nearly horizontal under low ceiling; distal tibia lies along floor so spines engage,
        # while distal tarsus flexes outward/upward clear of normal claw engagement.
        femur_y = coxa_y + 4.65
        femur_z = clamp(0.46 * ceiling_mm, 1.10, ceiling_mm - 0.35)
        tibia_base_contact_y = femur_y + 2.15
        tibia_tip_y = TARSUS_MIDLINE_MM - 0.55
        tibia_tip_z = 0.0  # Distal tibia/spines planted on ground
        # Distal tarsus/claws splayed sideways and lifted off the ground (lost claw engagement angle)
        tarsus_tip_y = TARSUS_MIDLINE_MM + 1.85
        tarsus_clearance = round(0.42 + 0.12 * clamp((4.6 - ceiling_mm) / 1.4, 0.0, 1.0), 4)
        tarsus_tip_z = tarsus_clearance
        spine_contacts = [
            (round(tibia_base_contact_y + k * (tibia_tip_y - tibia_base_contact_y) / 3.0, 4), 0.0)
            for k in range(1, 4)
        ]

    legs: List[LegPose] = []
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        legs.append(
            LegPose(
                side=side,
                coxa_yz_mm=(round(sgn * coxa_y, 4), round(coxa_z, 4)),
                femur_tip_yz_mm=(round(sgn * femur_y, 4), round(femur_z, 4)),
                tibia_base_yz_mm=(round(sgn * femur_y, 4), round(femur_z, 4)),
                tibia_tip_yz_mm=(round(sgn * tibia_tip_y, 4), round(tibia_tip_z, 4)),
                tarsus_tip_yz_mm=(round(sgn * tarsus_tip_y, 4), round(tarsus_tip_z, 4)),
                spine_contacts_yz_mm=[(round(sgn * y, 4), z) for y, z in spine_contacts],
                sprawl_angle_deg=round(sprawl_deg, 3),
                contact_mode=contact_mode,
                tarsus_clearance_mm=tarsus_clearance,
            )
        )

    if ceiling_mm >= 6.0:
        gait_mode = "alternating-tripod"
        vel = 58.05
    elif ceiling_mm >= 4.0:
        t_v = (ceiling_mm - 4.0) / 2.0
        gait_mode = "synchronous-mesothoracic-thrust" if ceiling_mm <= 4.3 else "transitional-sprawl"
        vel = 14.52 + t_v * (58.05 - 14.52)
    else:
        gait_mode = "crevice-gate-squeeze (72%->17% pass; 9% thorax-wedged)"
        vel = 6.5 + (ceiling_mm - 3.0) * 8.0

    return ConfinementState(
        ceiling_mm=round(ceiling_mm, 3),
        ventral_clearance_mm=round(ventral_z, 4),
        dorsal_peak_mm=round(dorsal_peak, 4),
        body_compression_pct=round(compression_pct, 2),
        sprawl_angle_deg=round(sprawl_deg, 2),
        contact_mode=contact_mode,
        gait_mode=gait_mode,
        expected_velocity_cm_s=round(vel, 2),
        plates=plates,
        metathoracic_legs=legs,
    )


def stick_slip_velocity_cm_s(
    mu_ceiling: float,
    mu_ground_body: float,
    mu_leg_spines: float,
    ceiling_mm: float = 4.0,
    f_max_n: float = 0.42,
    normal_body_n: float = 0.28,
    v_max_cm_s: float = 50.0,
) -> Dict[str, float]:
    """Analytical Coulomb stick-slip model from PMC4776529 SI Eqs. S4-S14 at 4-mm confinement."""
    c_h = normal_body_n / f_max_n
    theta_slip = math.atan2(1.0, mu_leg_spines)  # cot^-1(mu_f)
    denom_c = math.sqrt(1.0 + mu_ceiling * mu_ceiling)
    arg_max = c_h * (mu_ceiling + mu_ground_body) / denom_c
    if arg_max >= 0.995 or mu_leg_spines <= mu_ceiling + 1e-4:
        return {"stick_mm": 0.0, "slip_mm": 0.0, "stride_mm": 0.0, "velocity_cm_s": 0.0}

    theta_max = math.atan2(1.0, mu_ceiling) - math.asin(arg_max)
    arg_min = c_h * (mu_ceiling + mu_ground_body) / (mu_leg_spines - mu_ceiling)
    if arg_min >= 0.995:
        return {"stick_mm": 0.0, "slip_mm": 0.0, "stride_mm": 0.0, "velocity_cm_s": 0.0}

    leg_len_mm = 15.0
    kinematic_min = math.atan2(ceiling_mm, 2.0 * leg_len_mm)
    theta_min = max(math.asin(clamp(arg_min, 0.0, 0.995)), kinematic_min)

    stick_mm = 0.0
    if theta_max > theta_slip:
        stick_mm = 0.5 * ceiling_mm * ((1.0 / math.tan(theta_slip)) - (1.0 / math.tan(theta_max)))
        stick_mm = max(0.0, stick_mm)

    # Effective slip excursion attenuated by dorsal/ventral body drag ratio (Eqs. S11-S14).
    slip_mm = 0.0
    if min(theta_max, theta_slip) > theta_min:
        upper = min(theta_max, theta_slip)
        raw_excursion = 0.5 * ceiling_mm * ((1.0 / math.tan(theta_min)) - (1.0 / math.tan(upper)))
        mid_theta = 0.5 * (upper + theta_min)
        net_thrust_ratio = clamp(
            (mu_leg_spines * math.sin(mid_theta) - c_h * (mu_ceiling + mu_ground_body))
            / max(0.05, mu_leg_spines * math.sin(mid_theta)),
            0.0,
            1.0,
        )
        slip_mm = max(0.0, raw_excursion * net_thrust_ratio * 0.72)

    stride_mm = stick_mm + slip_mm
    # Constant stride period ~61.05 ms across ceiling & friction conditions (Jayaram & Full 2016, Figs. 2C & 3).
    vel_cm_s = min(v_max_cm_s, (stride_mm / 10.0) / (STRIDE_PERIOD_MS / 1000.0))
    return {
        "stick_mm": round(stick_mm, 4),
        "slip_mm": round(slip_mm, 4),
        "stride_mm": round(stride_mm, 4),
        "velocity_cm_s": round(vel_cm_s, 3),
    }


def state_dict(state: ConfinementState) -> Dict[str, object]:
    return asdict(state)


@dataclass(frozen=True)
class GateStage:
    stage_index: int
    stage_id: str
    label: str
    gate_x_progress_frac: float
    head_pitch_deg: float
    pronotum_roll_deg: float
    hind_legs_outside: bool
    abdomen_compression_pct: float
    clearance_margin_mm: float


def solve_gate_stages(gate_mm: float = 3.2) -> List[GateStage]:
    """Five horizontal crevice traversal stages (Jayaram & Full 2016, Fig. 1B-E)."""
    if not (3.0 <= gate_mm <= 7.0):
        raise ValueError(f"gate_mm={gate_mm} outside modeled [3.0, 7.0] mm window")
    confined = solve_confinement(gate_mm)
    abd_comp = confined.body_compression_pct
    margin = round(max(0.03, gate_mm - confined.dorsal_peak_mm), 4)
    return [
        GateStage(1, "antennal_probe", "Antennae probe slit", 0.06, -4.0, 0.0, True, 0.0, round(gate_mm, 3)),
        GateStage(2, "head_pitch_ram", "Head pitches down & wedges in", 0.22, -19.5, 0.0, True, 8.5, margin),
        GateStage(3, "pronotum_side_roll", "Pronotum rolls slightly to enter", 0.42, -11.0, 12.5, True, 24.0, margin),
        GateStage(4, "hind_leg_thorax_push", "Hind legs outside shove thorax", 0.68, -3.5, 3.0, True, abd_comp, margin),
        GateStage(5, "abdomen_exit_rebound", "Flattened abdomen clears & rebounds", 1.00, 0.0, 0.0, False, 0.0, round(FREESTANDING_HEIGHT_MM - gate_mm, 3)),
    ]


def tunnel_speed_profile() -> List[Dict[str, float]]:
    """Confined 15-cm tunnel crawling profile across 12, 9, 6, and 4 mm (104 trials, Fig. 2C)."""
    rows: List[Dict[str, float]] = []
    for h in (12.0, 9.0, 6.0, 4.0):
        s = solve_confinement(h)
        rows.append(
            {
                "ceiling_mm": h,
                "velocity_cm_s": s.expected_velocity_cm_s,
                "stride_period_ms": STRIDE_PERIOD_MS,
                "tarsus_midline_mm": TARSUS_MIDLINE_MM,
                "sprawl_deg": s.sprawl_angle_deg,
                "compression_pct": s.body_compression_pct,
                "contact_mode": s.contact_mode,
                "gait_mode": s.gait_mode,
            }
        )
    return rows


def crevice_trial_outcomes() -> Dict[str, object]:
    """Empirical 315-trial horizontal crevice gate outcomes (Jayaram & Full 2016, Fig. 1F)."""
    return {
        "total_trials": 315,
        "animals_n": 21,
        "gates": [
            {"gate_mm": 6.1, "pass_pct": 72.0, "sem_pct": 5.0, "abdomen_compression_pct": 0.0, "wedged_pct": 0.0, "turn_back_pct": 28.0},
            {"gate_mm": 4.4, "pass_pct": 72.0, "sem_pct": 5.0, "abdomen_compression_pct": 27.0, "wedged_pct": 1.0, "turn_back_pct": 27.0},
            {"gate_mm": 3.2, "pass_pct": 17.0, "sem_pct": 3.0, "abdomen_compression_pct": 47.0, "wedged_pct": 9.0, "turn_back_pct": 74.0},
        ],
    }


def load_resilience_profile() -> Dict[str, object]:
    """Exoskeletal compression, resilience, and load-tolerance bounds (Table S1 & Fig. 5)."""
    station_strains = []
    for frac, label, ul, ld in CROSS_SECTIONS:
        strain_pct = round(100.0 * (1.0 - ld / ul), 1)
        station_strains.append(
            {"fraction": frac, "station": label, "unloaded_mm": ul, "loaded_100g_mm": ld, "compression_pct": strain_pct}
        )
    return {
        "stations": station_strains,
        "resilience_slow_0_5_mm_s_pct": 60.0,
        "resilience_fast_4_0_mm_s_pct": 44.0,
        "contact_patch_cm2": 3.0,
        "slit_3_2mm_normal_force_n": 2.25,
        "slit_3_2mm_body_weights": 300,
        "cyclic_peak_force_n": 6.08,
        "cyclic_peak_body_weights": 900,
        "post_compression_run_cm_s": 76.67,
        "unpressed_control_p_value": 0.49,
    }


if __name__ == "__main__":
    import json

    summary = {
        f"{h:.1f}mm": {
            "dorsal_peak_mm": s.dorsal_peak_mm,
            "ventral_clearance_mm": s.ventral_clearance_mm,
            "compression_pct": s.body_compression_pct,
            "sprawl_deg": s.sprawl_angle_deg,
            "contact_mode": s.contact_mode,
            "gait_mode": s.gait_mode,
            "velocity_cm_s": s.expected_velocity_cm_s,
        }
        for h in (12.5, 9.0, 6.0, 4.0, 3.2)
        for s in (solve_confinement(h),)
    }
    print(json.dumps(summary, indent=2))
