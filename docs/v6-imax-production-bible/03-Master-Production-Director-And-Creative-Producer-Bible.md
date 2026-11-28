# Volume 03 — Master Film Production Director & Creative Producer Bible (`V6.3`)

> **Companion to:**
> - `01-Monarch-Cam-03-Long-V6-Complete-Forensic-Case-Study.md` *(Forensic Execution Benchmark)*
> - `02-Universal-Any-Topic-V6.2-Hollywood-IMAX-Master-Playbook.md` *(WebGL2 / Shader / Audio / Render Engine Architecture)*
> - `tools/director-producer-os/` *(Executable Schemas, 24 World Archetypes, Anti-Clone Ledger, 32-Rule Linter & Three.js Optics SDK)*

---

## 1. Why Volume 03 Exists: Separation of *Engine* from *Direction*
Volumes `01` and `02` solved **rendering physics** — ACES Filmic grading, contact-hardening shadows, procedural SDF/FBM materials, custom GLSL fracture shaders, `-14 LUFS` EBU R128 mastering, and `6-Gate` media verification.

However, **an IMAX camera package does not direct a movie**. Without an explicit **Creative Producer & Film Director Operating System**, even the best 3D engine risks repeating one visual habit (`dark obsidian room + rotating specimen pedestal + cyan/amber rim + top-left telemetry badge + 2-act cutaway`) across wildly different stories.

Volume `03` installs the **Creative Brain** above the V6 engine so that:
1. **Every story births its own physical world, lighting ratio, lens psychology, color script, editorial grammar, acoustic atmosphere, and HUD philosophy.**
2. **Every camera placement, focal length, movement, cut, silence window, and reveal is mathematically and dramatically justified before a single line of scene code is written.**

---

## 2. The Five-Hat Studio Brain Hierarchy

```text
[RAW TOPIC / SCRIPT IDEA]
        │
        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ HAT 1: EXECUTIVE CREATIVE PRODUCER                                       │
│  • Interrogates emotional core ("Why should a stranger care in 1.5s?")   │
│  • Separates EV0 Observed Fact vs EV1 Inference vs EV2 Model Abstraction │
│  • Queries `production_fingerprints.json` -> Picks fresh `W01..W24` +    │
│    `H0..H5` achieving >= 65% Anti-Clone Divergence                       │
└──────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ HAT 2: NARRATIVE DRAMATURG                                               │
│  • Selects `SUSPENSE`, `MYSTERY`, or `SURPRISE_PIVOT`                    │
│  • Designs `See -> Hide -> Reveal` pairs (no reveal without prior hide)  │
│  • Routes abstract science across >= 2 of the 5 Concrete Visual Routes   │
│  • Plants early visual Motif -> returns at climax/end with shifted sense │
└──────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ HAT 3: PRODUCTION DESIGNER & GAFFER                                      │
│  • Plots Bruce Block 7-Component Contrast/Affinity against Beat Graph    │
│  • Locks 2-4 muted Base Hexes + 1 Reserved Accent Hex (5-10% area max)   │
│  • Sets physical Kelvin key/fill sources & Stop Ratio (1.5:1 .. 12:1)    │
└──────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ HAT 4: DIRECTOR OF PHOTOGRAPHY (DOP)                                     │
│  • Maps 3D `scene_geography`, Scale Ruler & `180°` Line of Action FIRST  │
│  • Blocks physical subject forces & persistent state changes SECOND      │
│  • Sets Camera Distance FIRST (perspective) -> Lens `mm` SECOND (crop)   │
│  • Verifies `visible_width_m >= 1.18 * subject_width_m` in `9:16`        │
│  • Enforces `30°` Sightline / Shot-Size Step, 3-Layer FG/MG/BG Parallax, │
│    Stillness Default (`<= 70%` moving), and 3 Rejected Alternatives      │
└──────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ HAT 5: LEAD EDITOR & SOUND DESIGNER                                      │
│  • Cuts by Walter Murch Rule of Six (`51%` Emotion > `23%` Story > ...)  │
│  • Escorts viewer gaze across cuts (`Eye-Trace delta <= 0.36`)           │
│  • Carves `-58 dBFS` Villeneuve Acoustic Vacuum before physical climax   │
│  • Protects `>= 1.8s` 100% HUD-free Pure Cinema Climax + Seamless Loop   │
└──────────────────────────────────────────────────────────────────────────┘
        │
        ▼
[HARD GATE 0.5: `director_linter.py` == 0 ERRORS] -> Cleared for V6 Build!
```

---

## 3. Synthesis of Global Cinema & Open-Source Benchmarks Built Into Top1

| Pillar | Source Tradition / Benchmark | How Top1 Enforces It Deterministically |
|---|---|---|
| **Visual Intensity Curve** | Bruce Block (*The Visual Story*, 7 Components: Space, Line, Shape, Tone, Color, Movement, Rhythm) | `bruce_block_visual_arc`: peak contrast (`>=65`) locked to `climax_beat_id`; resolution drops to visual affinity (`>=55`). |
| **Editing Priority & Gaze** | Walter Murch (*In the Blink of an Eye*, Rule of Six) | `murch_cut_driver` enum + Euclidean screen `eye_trace_end_xy -> eye_trace_start_xy <= 0.36` check. |
| **Scale, Light & Silence** | Denis Villeneuve & Roger Deakins | Mandatory `scale_reference_object` on `WS`/`EWS`; motivated Kelvin ratio (`parseContrastRatio()`); `silence_before_climax_window_s` + HUD-free climax. |
| **Suspense vs Surprise** | Alfred Hitchcock & 8-Step DOP Architecture (`cinematography-director`) | `dominant_mode`, `audience_knows_vs_hidden` per beat, temporal `see_hide_pairs`, 5 concrete `visual_route`s, `rejected_alternative`s, buzzword ban. |
| **Task-to-Move Discipline** | Mascelli (*Five C's*) & Shot-Director Cheat Sheets (`cinematic-skills` / `director-skills`) | 10 legal motivations (`HOLD_STILLNESS` default), sealed `start_frame_desc != end_frame_desc`, `hold_for_text` motion lock, `180°` & `30°` 3D vector checks. |
| **Style Orthogonality & Persistent Physics** | 60-Style Decoupled Grammar (`katil-skill` / `SceneForge`) | Genre/Channel decoupled from 24 physical `world_archetypes.json` + 6 `hud_philosophies` + `anti_clone_validator.py` (`>= 65%` divergence). |
| **Short-Form Scroll Survival** | Zack D. Films (`1.6s` visual paradox, `~2.5s` ASL) & Kurzgesagt (`~3.5s` ASL, color-coded systems) | Poster-grade Frame `0`, `hook_lands_within_s <= 2.5s`, `LOOP_SEAM_MATCH` (`<= 0.12` eye-trace delta), 1 held stillness beat before impact. |

---

## 4. Quick-Reference Command Suite

```bash
# 1. Validate any candidate Pre-Production Director Plan (32 Cinema + Anti-Clone Checks)
python3 tools/director-producer-os/validators/director_linter.py projects/<slug>/director-plan.json

# 2. Validate all reference exemplars & run full unit test suite
pytest tools/director-producer-os/tests/test_director_producer_os.py -v

# 3. After Gate 6 passes on a finished production, register its DNA into Anti-Clone memory
python3 tools/director-producer-os/validators/register_fingerprint.py projects/<slug>/director-plan.json
```

And inside Three.js (`director.js`):
```javascript
import {
  lensMmToThreeFovY,
  computeCinemaFraming,
  distanceForSubjectWidth,
  applyShotOpticsToCamera,
  kelvinToSrgb01,
  parseContrastRatio,
  check180AxisSide,
  compute30DegreeSeparation,
  projectNormalizedEyeTrace,
} from '/tools/monarch-v6-imax-sdk/index.js';
```
