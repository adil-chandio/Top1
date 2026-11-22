#!/usr/bin/env python3
"""Biomechanical and geometric invariant tests for Monarch Cam Episode #03 rig."""

import math
import unittest

from rig import (
    CEILING_FRICTION_LEVELS,
    GROUND_FRICTION_LEVELS,
    PLATE_SPECS,
    crevice_trial_outcomes,
    load_resilience_profile,
    solve_confinement,
    solve_gate_stages,
    stick_slip_velocity_cm_s,
    tunnel_speed_profile,
)


class CockroachRigInvariantTests(unittest.TestCase):
    HEIGHTS = (12.52, 9.0, 6.0, 4.0, 3.2)

    def test_ceiling_and_floor_bounds_respected(self):
        for h in self.HEIGHTS:
            state = solve_confinement(h)
            self.assertLessEqual(state.dorsal_peak_mm, h, f"Dorsal plates pierced ceiling at {h} mm")
            self.assertGreaterEqual(state.ventral_clearance_mm, 0.0, f"Ventral body sank below floor at {h} mm")
            for p in state.plates:
                self.assertGreaterEqual(min(p.hinge_z_mm, p.tip_z_mm), 0.0)
                self.assertLessEqual(max(p.hinge_z_mm, p.tip_z_mm) + p.thickness_mm, h + 1e-6)

    def test_rigid_plate_chord_lengths_preserved(self):
        """Plates do not bend like rubber; chord lengths stay constant while arthrodial joints fold."""
        for h in self.HEIGHTS:
            state = solve_confinement(h)
            for p, (_, _, expected_chord, _) in zip(state.plates, PLATE_SPECS):
                actual_chord = math.hypot(p.tip_x_mm - p.hinge_x_mm, p.tip_z_mm - p.hinge_z_mm)
                self.assertAlmostEqual(actual_chord, expected_chord, places=2)

    def test_zero_tergite_shingle_interpenetration(self):
        """Adjacent overlapping plates maintain positive arthrodial clearance at every hinge."""
        for h in self.HEIGHTS:
            state = solve_confinement(h)
            for prev_p, curr_p in zip(state.plates, state.plates[1:]):
                self.assertLess(
                    curr_p.hinge_z_mm,
                    prev_p.tip_z_mm,
                    f"Plate {curr_p.name} interpenetrated {prev_p.name} at {h} mm",
                )

    def test_monotonic_sprawl_and_compression(self):
        states = [solve_confinement(h) for h in self.HEIGHTS]
        sprawls = [s.sprawl_angle_deg for s in states]
        comps = [s.body_compression_pct for s in states]
        for earlier, later in zip(sprawls, sprawls[1:]):
            self.assertLessEqual(earlier, later)
        for earlier, later in zip(comps, comps[1:]):
            self.assertLessEqual(earlier, later)
        self.assertGreaterEqual(states[-1].sprawl_angle_deg, 78.0)
        self.assertGreaterEqual(states[-1].body_compression_pct, 40.0)

    def test_tarsus_to_tibial_spine_gear_shift(self):
        """Freestanding & 6 mm use tarsal claws; 4.0 mm & 3.2 mm lift tarsi and plant tibial spines."""
        for h in (12.52, 9.0, 6.0):
            s = solve_confinement(h)
            self.assertEqual(s.contact_mode, "tarsal-claw")
            for leg in s.metathoracic_legs:
                self.assertEqual(leg.tarsus_tip_yz_mm[1], 0.0)
                self.assertEqual(len(leg.spine_contacts_yz_mm), 0)

        for h in (4.0, 3.2):
            s = solve_confinement(h)
            self.assertEqual(s.contact_mode, "tibial-spines")
            for leg in s.metathoracic_legs:
                self.assertEqual(leg.tibia_tip_yz_mm[1], 0.0)
                self.assertGreater(leg.tarsus_clearance_mm, 0.35)
                self.assertEqual(len(leg.spine_contacts_yz_mm), 3)
                for _, sz in leg.spine_contacts_yz_mm:
                    self.assertEqual(sz, 0.0)

    def test_ceiling_and_ground_friction_tradeoffs_match_pnas_fig3(self):
        """Higher ceiling friction monotonically slows crawling; ground friction peaks at intermediate grit."""
        mu_g_med, mu_leg_med = GROUND_FRICTION_LEVELS["med_40grit"]
        v_ceil_low = stick_slip_velocity_cm_s(
            CEILING_FRICTION_LEVELS["low_graphite_acrylic"], mu_g_med, mu_leg_med
        )["velocity_cm_s"]
        v_ceil_med = stick_slip_velocity_cm_s(
            CEILING_FRICTION_LEVELS["med_acrylic"], mu_g_med, mu_leg_med
        )["velocity_cm_s"]
        v_ceil_high = stick_slip_velocity_cm_s(
            CEILING_FRICTION_LEVELS["high_40grit"], mu_g_med, mu_leg_med
        )["velocity_cm_s"]
        self.assertGreater(v_ceil_low, v_ceil_med)
        self.assertGreater(v_ceil_med, v_ceil_high)

        mu_c = 0.16
        v_g_low = stick_slip_velocity_cm_s(mu_c, *GROUND_FRICTION_LEVELS["low_100grit"])["velocity_cm_s"]
        v_g_med = stick_slip_velocity_cm_s(mu_c, *GROUND_FRICTION_LEVELS["med_40grit"])["velocity_cm_s"]
        v_g_high = stick_slip_velocity_cm_s(mu_c, *GROUND_FRICTION_LEVELS["high_20grit"])["velocity_cm_s"]
        self.assertGreater(v_g_med, v_g_low)
        self.assertGreater(v_g_med, v_g_high)

    def test_five_stage_gate_traversal_monotonic_progress(self):
        stages = solve_gate_stages(3.2)
        self.assertEqual(len(stages), 5)
        fracs = [s.gate_x_progress_frac for s in stages]
        for a, b in zip(fracs, fracs[1:]):
            self.assertLess(a, b)
        self.assertTrue(all(s.hind_legs_outside for s in stages[:4]))
        self.assertFalse(stages[4].hind_legs_outside)
        self.assertGreaterEqual(stages[3].abdomen_compression_pct, 45.0)
        self.assertEqual(stages[4].abdomen_compression_pct, 0.0)

    def test_tunnel_speed_holds_until_4mm_drop(self):
        rows = tunnel_speed_profile()
        self.assertEqual([r["ceiling_mm"] for r in rows], [12.0, 9.0, 6.0, 4.0])
        for r in rows[:3]:
            self.assertAlmostEqual(r["velocity_cm_s"], 58.05, places=2)
            self.assertEqual(r["contact_mode"], "tarsal-claw")
        self.assertAlmostEqual(rows[3]["velocity_cm_s"], 14.52, places=2)
        self.assertEqual(rows[3]["contact_mode"], "tibial-spines")

    def test_crevice_trial_outcomes_sum_cleanly(self):
        outcomes = crevice_trial_outcomes()
        self.assertEqual(outcomes["total_trials"], 315)
        for g in outcomes["gates"]:
            self.assertAlmostEqual(g["pass_pct"] + g["wedged_pct"] + g["turn_back_pct"], 100.0, places=1)
        self.assertEqual(outcomes["gates"][-1]["pass_pct"], 17.0)
        self.assertEqual(outcomes["gates"][-1]["wedged_pct"], 9.0)

    def test_load_resilience_bounds_match_table_s1(self):
        prof = load_resilience_profile()
        self.assertEqual(len(prof["stations"]), 5)
        for st in prof["stations"]:
            self.assertGreaterEqual(st["compression_pct"], 40.0)
            self.assertLessEqual(st["compression_pct"], 58.0)
        self.assertEqual(prof["slit_3_2mm_body_weights"], 300)
        self.assertEqual(prof["cyclic_peak_body_weights"], 900)


if __name__ == "__main__":
    unittest.main()
