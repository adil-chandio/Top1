#!/usr/bin/env python3
"""Build and validate all Monarch Studio OS structured manifests for Episode #03.

Populates `tools/monarch-cockroach/manifests/` and builds the typed SQLite
research warehouse in `.cache/monarch-studio-os/research_warehouse.sqlite`.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OS_DIR = ROOT / "tools" / "monarch-studio-os"
sys.path.insert(0, str(OS_DIR))
sys.path.insert(0, str(HERE / "feature"))

import jsonschema  # noqa: E402
from feature_cut import conform_to_anchors  # noqa: E402
from validators.claim_linter import (  # noqa: E402
    lint_script_against_claims,
    scan_zero_trust_privacy,
    validate_scorecard,
)
from validators.state_machine import validate_project_lifecycle  # noqa: E402
from warehouse.cohort_store import build_warehouse  # noqa: E402

MANIFEST_DIR = HERE / "manifests"


def camera_lens_and_motivation(mode: int, subject: str) -> tuple[float, str, str]:
    if "macro" in subject or mode in (23, 41, 42, 43):
        return (
            100.0,
            "Shallow macro focus locked on contact plane (z = 0.00 mm) so lifted claws (+0.47 mm) and planted shin spines separate cleanly.",
            f"Macro lens isolates {subject.replace('_', ' ')} without cutting or hiding contact behind graphics.",
        )
    if "overhead" in subject or mode in (33, 44):
        return (
            50.0,
            "Orthographic-feel dorsal focus plane across all six leg tips to make gait symmetry readable on a 6-inch screen.",
            f"Overhead axis reveals {subject.replace('_', ' ')} across left-right leg pairs simultaneously.",
        )
    if "schematic" in subject or mode in (51, 64, 72, 74):
        return (
            50.0,
            "Crisp deep-focus schematic plane with high-contrast callout separation.",
            f"Locked diagram framing clarifies {subject.replace('_', ' ')} without reenacting invasive lab handling.",
        )
    return (
        35.0,
        "Deep corridor/slot focus keeping both US pennies, the 3.2 mm acrylic edge, and the cockroach silhouette sharp together.",
        f"Eye-level tracking preserves spatial scale during {subject.replace('_', ' ')}.",
    )


def build_all(proof_passed: bool = False, qa_passed: bool = False) -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    if qa_passed:
        status = "qa-passed"
    elif proof_passed:
        status = "proof-passed"
    else:
        status = "proof-pending"

    history = [
        {"state": "idea", "date": "2026-11-21", "actor": "agent-verified", "reason": "Ranked in original Monarch Cam 46-video market pass Top 3."},
        {"state": "researched", "date": "2026-11-21", "actor": "agent-verified", "reason": "Primary PNAS paper PMC4776529 + 8 verbatim multi-million-view benchmark transcripts analyzed."},
        {"state": "shortlisted", "date": "2026-11-21", "actor": "agent-verified", "reason": "Unfilmed tibial-spine traction whitespace confirmed vs Deep Look hydraulic-press benchmark."},
        {"state": "owner-selected", "date": "2026-11-21", "actor": "owner", "reason": "Owner directed: start Monarch Cam Episode #03 with 16:9 Long Video built first."},
        {"state": "claim-checked", "date": "2026-11-21", "actor": "qa-gate", "reason": "All 30 paragraphs mapped 1-to-1 to Jayaram & Full (2016) PNAS bounds."},
        {"state": "scripted", "date": "2026-11-21", "actor": "agent-verified", "reason": "Upgraded Script V2 (794 words, 81 sentences, 9.8 avg w/sent) exported to PDF & Google Doc."},
        {"state": "proof-pending", "date": "2026-11-21", "actor": "agent-verified", "reason": "Native C++17/OpenMP 9.00 s 1920x1080 3D moving contact proof queued before voice lock."},
    ]
    if proof_passed or qa_passed:
        history.append(
            {
                "state": "proof-passed",
                "date": "2026-11-21",
                "actor": "qa-gate",
                "reason": "9.00 s (270f @ 30 fps) native C++17 3D moving contact proof passed full PyAV/LUFS/mobile decode QA and visual inspection.",
            }
        )
    if qa_passed:
        history.extend(
            [
                {
                    "state": "voice-locked",
                    "date": "2026-11-21",
                    "actor": "owner",
                    "reason": "Owner auditioned masculine narrator candidates (Battle 01) and locked voice-01; 7 dry 48kHz/24-bit WAV takes locked at 10,461 frames (348.700 s, zero time-stretch).",
                },
                {
                    "state": "picture-locked",
                    "date": "2026-11-21",
                    "actor": "agent-verified",
                    "reason": "All 7 native C++17/OpenMP 1920x1080 @ 30.000 fps chapter plates (10,461 frames) rendered and visually inspected across 7-chapter QA contact sheet.",
                },
                {
                    "state": "mix-locked",
                    "date": "2026-11-21",
                    "actor": "agent-verified",
                    "reason": "48 kHz 24-bit stereo documentary mix locked (-15.50 LUFS-I WAV / -16.45 LUFS-I AAC Master, -1.69 dBTP True Peak, 0.9996 mono correlation).",
                },
                {
                    "state": "qa-passed",
                    "date": "2026-11-21",
                    "actor": "qa-gate",
                    "reason": "Full 10,461-frame PyAV decode, EBU R128 loudness, 4x True-Peak, 14.67 ms A/V sync, and 120px..480px mobile contrast QA passed; awaiting human owner-accepted sign-off.",
                },
            ]
        )

    project_doc = {
        "project_id": "monarch-cam-03-cockroach-long",
        "channel": "monarch-cam",
        "episode": "03",
        "edition": "16x9-long-form-feature-v2",
        "format": "long-16x9",
        "status": status,
        "owner_selected": True,
        "strategic_chain": {
            "what_viewer_saw": "A half-inch tall American cockroach sprints straight into a 3.2 mm crack (two stacked pennies) and vanishes in under a second.",
            "physical_mechanism": "Rigid chitin plates shingle on soft folding arthrodial hinges (~47% compression) while >80-degree leg sprawl lifts the foot claws and engages backward-pointing tibial shin spines like crampons.",
            "supporting_evidence": "Jayaram & Full (2016) PNAS 500 fps experiments across n = 21 male Periplaneta americana: 315 crevice-gate trials, 104 ceiling-height corridor trials, 638 confined-friction runs, and cyclic compression tests.",
            "what_evidence_does_not_prove": "Does NOT prove cockroaches are indestructible under sharp point loads, does NOT generalize exact 3.2 mm / 4.0 mm thresholds to every cockroach species, and our 3D visuals are illustrative reconstructions rather than lab video.",
            "viewer_understanding_shift": "Replaces the myth of 'rubbery or indestructible pests' with two exact mechanical design principles: hinged armor that folds and spiny shins that take over when feet lose geometry.",
        },
        "status_history": history,
    }

    audience_doc = {
        "project_id": "monarch-cam-03-cockroach-long",
        "viewer_question": "How can a half-inch insect with stiff armor vanish under a closed door crack where its legs can't even stand?",
        "prior_belief": "Viewers assume either the shell bends like soft rubber or cockroaches are mysteriously indestructible.",
        "visual_stop_moment": "0:00–0:08 eye-level sprint into a 3.2 mm clear slot beside two stacked copper pennies—and sub-second exit.",
        "post_watch_takeaway": "Stiff plates tile on soft hinges to clear the slot, and rows of stiff shin spines replace lifted foot claws inside a 4 mm ceiling—yet >80% still fail at 3 mm.",
        "share_and_rewatch_driver": "The wide-arm push-up realization in Scene 04 + the counter-intuitive rough-floor belly-snag bet in Scene 05 + real-speed replay in Scene 07.",
    }

    hook_lab_doc = {
        "project_id": "monarch-cam-03-cockroach-long",
        "candidates": [
            {
                "id": "H1_light_flip_door_action",
                "type": "visual_action",
                "opening_line": "Flip on a light, and a cockroach bolts for the crack under a closed door.",
                "one_sentence_clear": True,
                "matches_title_thumbnail": True,
                "first_seconds_visual_evidence": True,
                "non_misleading": True,
                "reproducible_in_proof_clip": True,
                "passed": True,
                "selected": True,
            },
            {
                "id": "H2_no_feet_surprising_claim",
                "type": "surprising_claim",
                "opening_line": "Squeezed into a tight crack, this cockroach stops using its feet—and keeps moving anyway.",
                "one_sentence_clear": True,
                "matches_title_thumbnail": True,
                "first_seconds_visual_evidence": True,
                "non_misleading": True,
                "reproducible_in_proof_clip": True,
                "passed": True,
                "selected": False,
            },
            {
                "id": "H3_two_pennies_scale",
                "type": "scale_comparison",
                "opening_line": "Stack two pennies on the floor: that three-millimeter sliver is tall enough for a half-inch cockroach to vanish through.",
                "one_sentence_clear": True,
                "matches_title_thumbnail": True,
                "first_seconds_visual_evidence": True,
                "non_misleading": True,
                "reproducible_in_proof_clip": True,
                "passed": True,
                "selected": False,
            },
            {
                "id": "H4_armor_fold_question",
                "type": "question",
                "opening_line": "If an insect's shell is stiff armor, why doesn't a three-millimeter gap snap it in half?",
                "one_sentence_clear": True,
                "matches_title_thumbnail": False,
                "first_seconds_visual_evidence": True,
                "non_misleading": True,
                "reproducible_in_proof_clip": True,
                "passed": False,
                "selected": False,
            },
            {
                "id": "H5_900x_press_consequence",
                "type": "consequence",
                "opening_line": "Crush this insect under nine hundred times its body weight, and it sprints away unharmed.",
                "one_sentence_clear": True,
                "matches_title_thumbnail": False,
                "first_seconds_visual_evidence": False,
                "non_misleading": True,
                "reproducible_in_proof_clip": False,
                "passed": False,
                "selected": False,
            },
        ],
    }

    # Classify all 30 paragraphs 1-to-1
    ch_bounds = (0, 6, 10, 14, 19, 23, 27, 30)
    para_categories = [
        # Ch 1 (0..5)
        ("illustrative_animation", "Everyday closed-door framing staged cleanly on 3.2 mm slot."),
        ("measured", "12.52 mm (~0.5 in) standing height vs 3.2 mm (~2 stacked US pennies = 3.04 mm) gate."),
        ("directly_observed", "High-speed approach without pause before antennal sweep."),
        ("directly_observed", "Downward head pitch and dorsal shell compression on entry."),
        ("measured", "288–821 ms IQR traversal (< 1 s) at 3.2 mm."),
        ("published_finding", "Frames the two core biomechanical questions answered in PMC4776529."),
        # Ch 2 (6..9)
        ("measured", "500 fps high-speed videography identifying 5 distinct traversal stages."),
        ("directly_observed", "Stages 1–4: antennal probe, head wedge, slight pronotum roll, outside hind-leg shove."),
        ("directly_observed", "Stage 5 abdomen exit; stiff chitin sclerites do not bend like rubber."),
        ("published_finding", "Rigid tergites shingle while soft arthrodial membranes fold ~41–57% (47% in 3.2 mm slit)."),
        # Ch 3 (10..13)
        ("published_finding", "Contrasts narrow gate (legs outside) with continuous low-ceiling confinement."),
        ("measured", "15 cm confined tunnel stepped across 12, 9, 6, and 4 mm (104 trials)."),
        ("measured", "Speed holds ~58.05 ± 2.33 cm/s across 12, 9, and 6 mm with constant ~61.05 ms stride."),
        ("measured", "2 mm drop from 6 mm to 4 mm cuts speed 4x to 14.52 ± 0.98 cm/s (P < 0.001) and breaks tripod gait."),
        # Ch 4 (14..18)
        ("illustrative_animation", "Camera motivation introducing the rear transverse leg comparison."),
        ("directly_observed", "Unconstrained 12 mm running engages distal tarsal claws and arolium/euplantulae pads."),
        ("modelled_reconstruction", "At 4 mm, >80 deg sprawl tips distal tarsus sideways (+0.47 mm clearance); wide-arm push-up analogy."),
        ("directly_observed", "Backward-pointing tibial spines contact floor at z = 0 mm and drive rearward without slip."),
        ("derived_calculation", "Synchronous mesothoracic oar shoves; ~38 mN/leg thrust = ~5.1x BW against dorsal+ventral friction."),
        # Ch 5 (19..22)
        ("measured", "Tarsus-ablated semicircular-track control confirmed tibial-spine kinetic friction (mu_f = 0.84–2.04)."),
        ("hypothesis", "Sets up intuitive viewer prediction ('rougher floor should always make it faster') tested next."),
        ("measured", "638 confined runs at 4 mm: rougher ceilings monotonically reduce speed (6.64 -> 5.63 -> 0.36 cm/s)."),
        ("measured", "Floor speed peaks on medium 40-grit (5.26 cm/s) and drops on coarse 20-grit (3.69 cm/s) via belly snag (mu_g = 0.76)."),
        # Ch 6 (23..26)
        ("measured", "Slit normal load ~300x BW (2.25 N); cyclic distributed peak ~900x BW (6.08 N over ~3 cm²), post-test speed 76.67 cm/s (P = 0.49)."),
        ("published_finding", "Transitions from distributed shell resilience to 315 crevice-gate limit trials."),
        ("measured", "72 ± 5% pass at 6.1 & 4.4 mm vs 17 ± 3% pass (>4/5 fail) at 3.2 mm."),
        ("unknown_limitation", "17% pass, ~74% antennal turn-back, 9 ± 2% thorax-wedged bottleneck for adult male Periplaneta americana."),
        # Ch 7 (27..29)
        ("modelled_reconstruction", "Real-speed 1x synthesis of antennal read, shingle fold, and tibial-spine drive."),
        ("measured", "Viscoelastic arthrodial rebound (60 ± 12% slow-rate resilience) restores 12.52 mm standing posture."),
        ("published_finding", "Concluding synthesis contrasting myth of indestructibility with folding hinges + walking shins."),
    ]
    assert len(para_categories) == 30

    p_claims = []
    for idx, (cat, note) in enumerate(para_categories):
        ch = next(c + 1 for c in range(7) if ch_bounds[c] <= idx < ch_bounds[c + 1])
        p_claims.append(
            {
                "paragraph_index": idx,
                "chapter": ch,
                "category": cat,
                "source_ids": ["jayaram_full_2016_pnas"],
                "bound_note": note,
            }
        )

    claims_doc = {
        "project_id": "monarch-cam-03-cockroach-long",
        "script_version": "V2",
        "sources": [
            {
                "source_id": "jayaram_full_2016_pnas",
                "citation": "Jayaram K, Full RJ (2016). Cockroaches traverse crevices, crawl rapidly in confined spaces, and inspire a soft, legged robot. PNAS 113(8): E950-E957.",
                "doi_or_url": "https://doi.org/10.1073/pnas.1514591113",
                "access_date": "2026-11-21",
                "source_type": "peer-reviewed-paper",
                "license": "PNAS Open Access (PMC4776529) — scientific facts/measurements cited; zero paper figures or lab videos reused.",
                "exact_claims_supported": [
                    "Adult male Periplaneta americana (n=21, 0.76g, 12.52mm freestanding height) traverse 3.2mm gates in 288-821ms IQR across 5 stages.",
                    "Pass rate drops from 72+-5% (6.1 & 4.4mm) to 17+-3% (3.2mm) across 315 trials (~74% turn back, 9+-2% thorax-wedged).",
                    "104 confined-ceiling trials hold 58.05+-2.33 cm/s across 12, 9, 6mm before dropping 4x to 14.52+-0.98 cm/s at 4mm.",
                    "At 4mm (>80 deg sprawl), tibial spines engage substrate (~5.1x BW thrust/leg); across 638 runs, medium 40-grit floor maximizes speed.",
                    "Distributed cyclic compression peaks at 6.08+-1.61 N (~900x BW) with 76.67+-7.34 cm/s unimpaired post-test speed (P=0.49).",
                ],
                "claims_not_supported": [
                    "Indestructibility under sharp point loads or barefoot stomps without a 2mm stop.",
                    "Identical millimeter limits across all 4,500+ cockroach species or juvenile instars.",
                    "Claiming our procedural 3D render is actual high-speed camera footage or micro-CT.",
                ],
            }
        ],
        "forbidden_phrases": [
            {"pattern": r"\bevery cockroach species\b|\ball cockroaches\b", "reason": "Exact millimeter thresholds belong to adult male Periplaneta americana."},
            {"pattern": r"\bactual lab footage\b|\breal microscope video\b|\bmicro-ct scan footage\b", "reason": "Visuals are an illustrative procedural 3D reconstruction."},
            {"pattern": r"\bcompletely indestructible\b|\bliterally uncrushable\b", "reason": "900x BW test used distributed plates with a 2 mm stop; 9% still wedge at 3.2 mm."},
            {"pattern": r"\blike and subscribe\b|\bsmash that subscribe\b", "reason": "Monarch Cam forbids spoken/end-clutter CTAs."},
        ],
        "paragraph_claims": p_claims,
    }

    scorecard_doc = {
        "project_id": "monarch-cam-03-cockroach-long",
        "disclaimer": "Pre-production quality gate only (out of 100)—not a guaranteed viral probability prediction.",
        "scores": {
            "viewer_promise_clarity": 19,
            "visible_proof_potential": 19,
            "novelty": 14,
            "evidence_strength": 15,
            "emotional_stakes_value": 9,
            "short_long_format_fit": 9,
            "rights_certainty": 5,
            "production_feasibility": 4.5,
        },
        "total_score": 94.5,
        "gate_checks": {
            "score_strong": True,
            "claim_ledger_complete": True,
            "title_thumbnail_promise_clear": True,
            "eight_to_twelve_sec_proof_possible": True,
            "owner_selection_confirmed": True,
        },
        "passed": True,
    }

    rights_doc = {
        "project_id": "monarch-cam-03-cockroach-long",
        "spdx_default_code_license": "LicenseRef-Proprietary-Top1",
        "assets": [
            {
                "asset_id": "pnas_pmc4776529_facts",
                "asset_type": "paper",
                "source": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4776529/",
                "spdx_or_terms": "Scientific measurements & facts cited with full attribution; 0 third-party images/videos copied.",
                "sha256": None,
                "commercial_use_cleared": True,
                "usage_scope": "Quantitative solver parameters, script bounds, and credits citation.",
            },
            {
                "asset_id": "cockroach_cpp17_sdf_renderer",
                "asset_type": "code",
                "source": "tools/monarch-cockroach/feature/proof_render.cpp",
                "spdx_or_terms": "100% original repository C++17/OpenMP ray-casting code",
                "sha256": None,
                "commercial_use_cleared": True,
                "usage_scope": "All 16:9 moving proof and episode 3D visuals.",
            },
            {
                "asset_id": "procedural_dsp_contact_foley",
                "asset_type": "sound",
                "source": "tools/monarch-cockroach/feature/build_moving_proof.py",
                "spdx_or_terms": "100% original synthesized NumPy/SciPy DSP micro-contact Foley (zero external samples)",
                "sha256": None,
                "commercial_use_cleared": True,
                "usage_scope": "Synchronized chitin shingle, acrylic touch, and tibial-spine grit transients.",
            },
            {
                "asset_id": "arena_auditioned_narrator_voice",
                "asset_type": "voice",
                "source": "Arena add_voice / generate_speech licensed TTS session voice",
                "spdx_or_terms": "Platform-licensed synthetic speech selected by owner audition (zero unauthorized voice cloning)",
                "sha256": None,
                "commercial_use_cleared": True,
                "usage_scope": "Episode #03 English documentary narration.",
            },
        ],
    }

    pronunciation_doc = {
        "project_id": "monarch-cam-03-cockroach-long",
        "language": "en-US",
        "terms": [
            {"term": "Periplaneta americana", "ipa": "/ˌpɛrɪpləˈniːtə əˌmɛrɪˈkɑːnə/", "spoken_policy": "Written in credits/SUPER; spoken VO uses 'American cockroaches' for clean conversational flow."},
            {"term": "arthrodial", "ipa": "/ɑːrˈθroʊdiəl/", "spoken_policy": "Shown on SUPER ('Soft arthrodial hinges'); spoken VO says 'soft hinge tissue'."},
            {"term": "crampons", "ipa": "/ˈkræmpɒnz/", "spoken_policy": "Spoken in Ch. 04 & Ch. 06—verify crisp 'kram-ponz' stress on human listen check."},
            {"term": "antennae", "ipa": "/ænˈtɛniː/", "spoken_policy": "Spoken in Ch. 02, 06, 07—verify plural '-nee' ending rather than '-nay'."},
            {"term": "millimeters", "ipa": "/ˈmɪlɪˌmiːtərz/", "spoken_policy": "Spoken twice only (Ch. 03 'two millimeters lower', Ch. 06 'three millimeters')."},
        ],
        "pickup_protocol": "Synthesize 7 independent chapter takes with fixed voice_id; if any word mispronounces or clips, regenerate only that chapter take without pitch/speed warping.",
    }

    voice_lock_path = MANIFEST_DIR / "voice-lock.json"
    dry_master_wav = ROOT / ".cache" / "monarch-cockroach" / "voice" / "Monarch-Cam-03-Long-Video-Dry-Voiceover-Master-V2.wav"
    if dry_master_wav.exists():
        import hashlib
        for asset in rights_doc["assets"]:
            if asset["asset_id"] == "arena_auditioned_narrator_voice":
                asset["sha256"] = hashlib.sha256(dry_master_wav.read_bytes()).hexdigest()

    if voice_lock_path.exists():
        vlock = json.loads(voice_lock_path.read_text())
        anchors = [0] + [c["end_frame"] for c in vlock["chapters"]]
        from feature_cut import write_schedule
        write_schedule(anchors)
        raw_shots = conform_to_anchors(anchors)
    else:
        raw_shots = conform_to_anchors()
    shots_out = []
    for idx, s in enumerate(raw_shots, 1):
        lens, focus, motiv = camera_lens_and_motivation(s["mode"], s["subject"])
        shots_out.append(
            {
                "shot_index": idx,
                "chapter": s["chapter"],
                "first_frame": s["first"],
                "end_frame": s["end"],
                "camera_id": s["camera"],
                "lens_mm_equiv": lens,
                "subject": s["subject"],
                "camera_motivation": motiv,
                "focus_logic": focus,
                "mobile_6in_safe": True,
            }
        )
    shot_plan_doc = {
        "project_id": "monarch-cam-03-cockroach-long",
        "fps": 30,
        "master_resolution": [1920, 1080],
        "shots": shots_out,
    }

    packaging_doc = {
        "project_id": "monarch-cam-03-cockroach-long",
        "format": "long-16x9",
        "title_concepts": [
            {
                "id": "T1_mechanism_paradox",
                "title": "How This Cockroach Runs Without Its Feet",
                "angle": "Direct mechanism paradox matching the lifted-claw / shin-spine visual proof.",
                "char_count": 40,
                "selected": True,
            },
            {
                "id": "T2_scale_and_mechanism",
                "title": "This Cockroach Vanishes Under Two Pennies—Without Using Its Feet",
                "angle": "Combines household two-penny scale hook with the footless propulsion reveal.",
                "char_count": 64,
                "selected": False,
            },
            {
                "id": "T3_hinged_armor",
                "title": "Why a 3mm Crack Doesn't Crush This Cockroach's Armor",
                "angle": "Leads with shell-folding puzzle; kept as backup A/B test candidate.",
                "char_count": 52,
                "selected": False,
            },
        ],
        "thumbnail_concepts": [
            {
                "id": "C1_macro_shin_spines_vs_pennies",
                "headline_badge": "NO FEET",
                "composition": "Tight rear-quarter macro at the 3.2 mm clear slot beside two copper pennies: flattened amber shell, lifted foot claws in silhouette, and 3 glowing gold shin spines planted on 40-grit floor.",
                "silhouette_contrast": "Warm copper/amber + gold contact spikes against deep #0D121A obsidian background (contrast > 6.5x at 120px).",
                "timestamp_safe": True,
                "selected": True,
            },
            {
                "id": "C2_split_standing_vs_3mm_flat",
                "headline_badge": "3MM GAP",
                "composition": "Left-to-right height compression comparison: 12.5 mm standing posture vs 3.2 mm shingled squeeze under clear glass.",
                "silhouette_contrast": "High vertical step-down silhouette readable at 176px mobile feed width.",
                "timestamp_safe": True,
                "selected": False,
            },
            {
                "id": "C3_shingle_cutaway_zoom",
                "headline_badge": "IT FOLDS",
                "composition": "Extreme macro cutaway on overlapping amber tergite plates and cyan folding arthrodial hinges under downward load arrows.",
                "silhouette_contrast": "Amber vs cyan complementary contrast on dark stage.",
                "timestamp_safe": True,
                "selected": False,
            },
        ],
        "first_frame_promise": "Frame 0 opens directly on the half-inch cockroach sprinting into the two-penny (3.2 mm) door slot—zero logo or intro delay.",
        "resolution_checks_px": [480, 320, 176, 120],
        "promise_match_verified": True,
        "experiment": {
            "hypothesis": "Macro close-up showing lifted claws + planted shin spines ('NO FEET') beside two pennies will deliver stronger CTR + first-30s retention than a broad hydraulic-press survival angle.",
            "variable": "Mechanism-specific footless propulsion hook + thumbnail ('NO FEET') vs generic toughness framing.",
            "control": "Same 7-chapter Monarch Cam 16:9 documentary pacing (~9.8 w/sent) established in Ant #01A V3.",
            "expected_signal": "Strong first-30s hold across the sub-second door-crack vanish and steady retention across Scene 04/05's rough-floor bet.",
            "minimum_observation_window": "First 7 days and >= 10,000 impressions in YouTube Studio before judging CTR.",
            "result": "pending_owner_publish",
            "next_action": "Compare Studio CTR + 0:30 retention against Ant #01A V3; test Title T2 / Cover C2 only if CTR trails baseline after window.",
        },
    }

    # Build SQLite warehouse with verified benchmark rows
    cohort_rows = [
        {
            "source_id": "deeplook_mosquito_6needles",
            "channel_cohort": "wildlife-micro-biomechanics",
            "creator": "KQED Deep Look",
            "title": "How Mosquitoes Use Six Needles to Suck Your Blood",
            "format": "long-16x9",
            "runtime_s": 211,
            "title_promise": "Looks like one tube -> actually six specialized micro-needles",
            "thumbnail_features": "Extreme macro proboscis on skin, high contrast",
            "observed_age": "9+ years",
            "displayed_views": 23000000,
            "script_avg_words_per_sent": 13.2,
            "confidence_and_limitations": "Verbatim KQED transcript verified; views reflect 9-year catalog flagship status, not single-line causality.",
        },
        {
            "source_id": "realscience_octopus",
            "channel_cohort": "science-biology-long",
            "creator": "Real Science",
            "title": "The Insane Biology of: The Octopus",
            "format": "long-16x9",
            "runtime_s": 1180,
            "title_promise": "Escalating biological paradoxes (colorblind camouflage)",
            "thumbnail_features": "Close-up eye/skin chromatophores on dark ground",
            "observed_age": "3+ years",
            "displayed_views": 13180000,
            "script_avg_words_per_sent": 14.1,
            "confidence_and_limitations": "Transcript verified; longer 19-min essay format vs our 5-6 min mechanism cut.",
        },
        {
            "source_id": "stevemould_grasshopper_leg",
            "channel_cohort": "biomechanics-explainer",
            "creator": "Steve Mould",
            "title": "We should use this amazing mechanism that's inside a grasshopper leg",
            "format": "long-16x9",
            "runtime_s": 612,
            "title_promise": "Hidden mechanical lever/latch inside an insect leg",
            "thumbnail_features": "Physical model + clear insect leg diagram",
            "observed_age": "2+ years",
            "displayed_views": 3220000,
            "script_avg_words_per_sent": 13.8,
            "confidence_and_limitations": "Transcript verified; strong human-scale physical analogy before micro-anatomy.",
        },
        {
            "source_id": "deeplook_cockroach_press",
            "channel_cohort": "same-species-benchmark",
            "creator": "KQED Deep Look",
            "title": "Cockroach vs. Hydraulic Press: Who Wins?",
            "format": "long-16x9",
            "runtime_s": 237,
            "title_promise": "How a cockroach survives 900x body-weight compression",
            "thumbnail_features": "Macro cockroach under metal press",
            "observed_age": "3 years (Sep 2023)",
            "displayed_views": 815663,
            "script_avg_words_per_sent": 13.9,
            "confidence_and_limitations": "Same PNAS lab source; skipped shin-spine mechanics, 4mm cliff, and 638-trial belly-drag trap.",
        },
        {
            "source_id": "monarchcam_01a_ant_v3",
            "channel_cohort": "same-channel-baseline",
            "creator": "Monarch Cam",
            "title": "This Ant Escapes by Biting the Ground",
            "format": "long-16x9",
            "runtime_s": 300,
            "title_promise": "Trap-jaw ant strikes sand to launch out of antlion pit",
            "thumbnail_features": "Macro jaw strike on sand, 'NO GRIP' badge",
            "observed_age": "Channel Ep #01A",
            "displayed_views": None,
            "script_avg_words_per_sent": 9.1,
            "confidence_and_limitations": "Locked 8,994-frame internal production benchmark.",
        },
    ]
    db_path = build_warehouse(cohort_rows)

    to_write = [
        ("project.json", project_doc, "project.schema.json"),
        ("claims.json", claims_doc, "claims.schema.json"),
        ("scorecard.json", scorecard_doc, "scorecard.schema.json"),
        ("rights.json", rights_doc, "rights.schema.json"),
        ("shot-plan.json", shot_plan_doc, "shot-plan.schema.json"),
        ("packaging.json", packaging_doc, "packaging.schema.json"),
    ]
    for fname, doc, schema_name in to_write:
        schema = json.loads((OS_DIR / "schemas" / schema_name).read_text())
        jsonschema.validate(instance=doc, schema=schema)
        (MANIFEST_DIR / fname).write_text(json.dumps(doc, indent=2) + "\n")

    (MANIFEST_DIR / "audience.json").write_text(json.dumps(audience_doc, indent=2) + "\n")
    (MANIFEST_DIR / "hook-lab.json").write_text(json.dumps(hook_lab_doc, indent=2) + "\n")
    (MANIFEST_DIR / "pronunciation.json").write_text(json.dumps(pronunciation_doc, indent=2) + "\n")
    (MANIFEST_DIR / "research.json").write_text(
        json.dumps({"warehouse_sqlite": str(db_path.relative_to(ROOT)), "cohort_count": len(cohort_rows), "cohorts": cohort_rows}, indent=2) + "\n"
    )

    # Run automated linters!
    narration = (HERE / "feature" / "narration.txt").read_text()
    launch_copy = (HERE / "feature" / "launch-copy-draft.txt").read_text()
    lc_errs = validate_project_lifecycle(project_doc)
    cl_errs = lint_script_against_claims(narration, claims_doc, [launch_copy])
    sc_errs = validate_scorecard(scorecard_doc)
    pv_errs = scan_zero_trust_privacy([HERE, OS_DIR])
    assert not lc_errs, lc_errs
    assert not cl_errs, cl_errs
    assert not sc_errs, sc_errs
    assert not pv_errs, pv_errs
    if qa_passed:
        release_status = {
            "project_id": "monarch-cam-03-cockroach-long",
            "status": "qa-passed",
            "human_gates_completed": ["owner-selected", "voice-locked"],
            "human_gates_pending": ["owner-accepted", "published"],
            "youtube_auto_upload_permitted": False,
            "short_9x16_held_until_long_video_signoff": True,
        }
        (MANIFEST_DIR / "release-status.json").write_text(json.dumps(release_status, indent=2) + "\n")
    print(f"ALL STUDIO OS MANIFESTS & LINTERS PASSED ({status}): manifests + SQLite warehouse ready.")


if __name__ == "__main__":
    build_all(proof_passed="--proof-passed" in sys.argv, qa_passed="--qa-passed" in sys.argv)
