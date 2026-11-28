# 06 — Sound Dramaturgy, Villeneuve Silence Law & Multi-Channel Creative Identity

## 1. Sound Is 50% of the Image
A 3D render feels weightless when wall-to-wall narration and constant drone music smother every second. Great directors score **dynamic range in time**:
1. **Acoustic Bed Identity (`acoustic_world_bed`):** Every world archetype carries its own authentic room-tone/air signature — *morning kitchen kettle simmer & distant courtyard sparrow (`W01`)*, *humid canopy drip & insect chorus (`W05`)*, *katabatic polar wind over creaking firn ice (`W07`)*, *60 Hz transformer hum (`W23`)*. Never reuse a generic sci-fi dark sub-drone in a sunlit or natural world!
2. **The Villeneuve Silence-Before-Impact Window (`silence_before_climax_window_s`):**
   - Pull sub-bass and ambient bed down (`-55` to `-60 dBFS` acoustic vacuum) for **`0.35–1.20s`** immediately preceding the physical rupture/revelation.
   - When the physical transient (`alloy pop`, `chitin snap`, `sandstone fracture`, `glacial core shear`) hits out of near-silence, its perceived visceral punch triples without clipping `-1.0 dBTP`.
3. **Protected Pure-Cinema Climax Windows (`protected_hud_free_climax_windows_s`):**
   - At least **`1.80s` minimum** (`2.5–4.5s` recommended) during the emotional/physical climax MUST strip away **100% of HUD overlays, callout brackets, and captions** (`Gate 5` + `director_linter.py` enforced) so the viewer experiences unobstructed cinema.

---

## 2. Channel Spines WITHOUT Single-Template Monotony
Per `CHANNELS.md`, our studio runs distinct channels — and **even within a single channel, consecutive episodes MUST inhabit fresh worlds from `world_archetypes.json`**:

### A. `monarch-edits` (Desi Urdu/Hindi 3D Science, Everyday Engineering & Curiosity)
- **Voice & Soul:** High-clarity conversational Roman-script/Urdu-Hindi storytelling (`~155–170 WPM`), tactile curiosity, relatable real-world stakes.
- **World Rotation Pool (Never Locked to Dark Pedestals!):**
  - Household/Kitchen/Workshop -> `W01_SUNLIT_DOMESTIC_MORNING`, `W22_DESI_ROOFTOP_COURTYARD_DUSK`, `W13_TERRACOTTA_CARPENTER_WORKSHOP`
  - Street/Grid/Coastal -> `W09_MONSOON_ASPHALT_NIGHT_STREET`, `W21_TIDAL_COASTAL_BASALT_WAVE_TANK`
  - Heavy Machines/Aero/Electricity -> `W04_BRUTALIST_FOUNDRY_HIGH_HEAT`, `W15_AERODYNAMIC_WIND_TUNNEL_BAY`, `W23_HIGH_VOLTAGE_FARADAY_DARKROOM`, `W12_HARD_VACUUM_ORBITAL_SUNLIGHT`
  - Medical/Clean Tech/Micro -> `W06_HIGH_KEY_SCULPTURAL_ATELIER`, `W10_SURGICAL_OPERATING_THEATER`, `W11_CELLULAR_INNER_CATHEDRAL`
- **HUD Rotation:** `H1_DOCUMENTARY_LOWER_THIRD`, `H2_DIEGETIC_IN_WORLD`, `H4_HIGH_CONTRAST_SWISS_GRID`, `H0_PURE_CINEMA`.

### B. `monarch-cam` (Wildlife, Biomechanics & Biological Mysteries)
- **Voice & Soul:** Investigative natural-history awe, anatomical precision, sensory immersion.
- **World Rotation Pool:**
  - Living Biomes -> `W05_RAINFOREST_CANOPY_UNDERSTORY`, `W16_GOLDEN_HOUR_SAVANNA_GRASSLAND`, `W03_ABYSSAL_HYDROTHERMAL_DARK`, `W17_SUBTERRANEAN_KARST_LIMESTONE_CAVE`, `W21_TIDAL_COASTAL_BASALT_WAVE_TANK`
  - Internal Physiology -> `W11_CELLULAR_INNER_CATHEDRAL`, `W19_SYNCHROTRON_TOMOGRAPHY_CHAMBER`
  - Museum/Comparative Anatomy -> `W08_CANDLELIT_NATURALIST_ARCHIVE`, `W06_HIGH_KEY_SCULPTURAL_ATELIER`
- **HUD Rotation:** `H0_PURE_CINEMA` (BBC Earth flagship!), `H1_DOCUMENTARY_LOWER_THIRD`, `H3_FORENSIC_BLUEPRINT` (sparingly, max 1 in 3 episodes).

### C. `extinct-channel` (`Extinct Life` — Paleontology, Deep Time & Earth Cataclysms)
- **Voice & Soul:** Deep-time detective gravity, specimen provenance (`BP/1/5558`, core IDs, formation strata), vanished worlds brought back with scientific restraint.
- **World Rotation Pool:**
  - Field Dig & Strata -> `W02_SCORCHED_FIELD_EXPEDITION`, `W07_CRYOGENIC_GLACIAL_WHITEOUT`, `W17_SUBTERRANEAN_KARST_LIMESTONE_CAVE`
  - Extinction Cataclysms -> `W14_VOLCANIC_BASALT_EXTINCTION`, `W03_ABYSSAL_HYDROTHERMAL_DARK`
  - Archive & Dual-Time -> `W08_CANDLELIT_NATURALIST_ARCHIVE`, `W24_DUAL_STRAND_OPPENHEIMER_CONTRAST`
- **HUD Rotation:** `H5_EDITORIAL_CHAPTER_CARDS`, `H1_DOCUMENTARY_LOWER_THIRD`, `H2_DIEGETIC_IN_WORLD` (field notebook / rock core markings), `H0_PURE_CINEMA`.
