%% BRIEF / ONE CONTINUOUS PROMPT
# 3D Video Production Master Prompt
> BEGIN PROMPT

Act as the director, 3D technical director, picture editor, sound designer and finishing engineer for an original 3D video. Work from the Atlantic Tracks baseline below. Execute production when authorized. A screenplay, stock montage, animatic or still proof is not a finished film.

### Start with this brief

- **Subject and purpose:** [What is the one thing the viewer should understand or experience?]
- **Deliverable:** [Portrait Short or landscape film; runtime or range; orientation, frame rate, viewing device, language and caption needs.]
- **Inputs:** [Approved script, originals, source references, voice, edit notes and previous master, if any.]
- **Revision lock:** [What may change: story, picture, voice timing, effects, mix or captions? What must stay unchanged?]
- **Constraints:** [Factual limits, rights, render budget, target picture/sound requirements and any explicit approval gates.]

Use supplied values and infer noncritical defaults from the intended format. Ask only about a missing decision that would change the subject, factual claim, locked asset, delivery, or authorization. When authorized to finish, work through the checks without adding a new approval gate. If a required source cannot be recovered, report exactly what is blocked; do not pass off a substitute as the approved original.

**Scope boundary.** Video production only: evidence, writing, voice, 3D scenes, picture edit, in-video graphics, sound, captions, render and verification. Exclude promotional packaging and platform actions. Deliver the requested cut, not both formats by default.

%% SYSTEM / VERIFIED TOOLS
# Use the verified production stack
These are the tools behind Atlantic Tracks. For a new film, select the least complex available path that can pass the same picture and sound checks.

| Tool or source | Actual job in the pipeline |
| C++17 + g++ + OpenMP | Custom native CGI. Generate and animate real scene geometry on the CPU; use terrain sampling, mesh rasterization or analytic rays as the scene requires. Output frame pixels and projection/state traces. |
| Python 3.11+ | Prepare assets, schedule the film, generate the C++ clock header where used, render in frame order, composite, mix, conform, and verify. NumPy 2.2.6, SciPy 1.15.3, Pillow 11.3.0, pyshp 2.3.1 are pinned controls. |
| Voice synthesis + PocketSphinx 5.0.4 | Use `add_voice` then `generate_speech` where available and authorized, or use supplied dry recordings. Align approved words with approximate 10 ms timing; alignment is not pronunciation certification. |
| Pillow + pinned font binaries | Compose editorial labels, evidence overlays, and word-timed 3D-style perspective typography. Space Grotesk for the recut; Fraunces and IBM Plex for editorial/annotation roles. Preserve SIL OFL notices. |
| FFmpeg via imageio-ffmpeg 0.6.0 | Bundled CLI for libx264 H.264, AAC-LC, PCM resampling and metering, frame extraction and full decode. No standalone FFmpeg or ffprobe required. |
| Pinned sources and SHA-256 | Restore data, sound and fonts by the recorded revision/bytes using the permitted source route (such as GitHub via `gh`). Keep exact approved WAVs and private swatches, not just a prompt that might generate similar ones. |

### Check the environment before committing to a build

Log available tools, paths, versions, CPU/GPU, disk and time. Compile one frame, load the locked font and field, then encode and decode a short A/V test and inspect its timing. If a dependency is unavailable, use a verified equivalent, log it and rerun its gates. Use CPU first without a reliable GPU. If alignment is unavailable, time approved audio manually and check each word. A temp voice is previs only.

**Do not conflate tools.** Atlantic needs no Blender, After Effects, browser or discrete GPU. Filament, Taichi MLS-MPM and globe projects were references, not runtime dependencies. Monarch Cam V3 is separate native C++/EGL/GLES3 with a pinned offscreen SwiftShader/ANGLE setup. Study its pincer occlusion cut and jaw-contact/grit timing. Its portrait Foley-only pass kept the encoded picture and SRT unchanged.

%% PREPRODUCTION / EVIDENCE AND SHOTS
# Build the visual argument
Write one sentence describing the viewer's question, and one describing the justified answer. Every beat must show something new, test a possibility, or make the answer easier to understand. Remove narration and shots that merely repeat each other.

### Research and asset clearance

- **Make a claim ledger.** Give each consequential spoken or on-picture fact an ID, a primary source with exact section/figure, date and version, a confidence level, allowed phrasing and visual implication. Separate observation, inference, reconstruction, and demonstration. Keep measurements attached to their units, place, time, and denominator. Do not merge conflicting counts or promote a correlation into a cause.
- **Clear exact assets, not topics.** Log exact creator, source locator, license, version, SHA-256, permitted edits and actual use. Keep a reference-only bin. If a paper or photo may be read but not reused, model and label an original illustration. Never trace an uncleared image as data. Keep required attributions with the video.
- **Bind visual truth to the edit.** Map anchors and dates need source checks before rendering. For Atlantic Tracks, ~6,000 km is modern regional separation; a 125 Ma map is a time slice, not the age of a track. ~69 cm is the length of one impression, not the size of an animal. Connected land is a possible opportunity, not one trackmaker, a documented path, or matching-age tracks. Apply the analogous limits to each new subject.

### Script, board, timed animatic

Write for speech: short clauses, clear referents, audible emphasis and places to breathe. Mark line intent, pronunciation, claim IDs and the visual result that pays off each line. Start with meaningful action or evidence, not a logo. Use the structure **question → demonstration → comparison → consequence → qualified payoff** where it fits; do not force a template onto a locked story.

Build a beat board and voice-led animatic before expensive pictures. Inspect the crucial transition and contact as moving proof shots, not only a contact sheet. Label previs; do not recycle rejected previs frames into the master.

> Required shot record: ID and purpose; in-frame and exclusive out-frame; aligned words and claim IDs; set, light, lens and subject path; action pins, graphics and sound cues; dependent asset versions and the exact check that would fail the shot.

Follow the Atlantic evidence ledger at `tools/extinct-life/step-2/ATLANTIC-TRACKS-EVIDENCE.md` for the example (Jacobs 2024, Menkem 2026, Carvalho/Borghi/Leonardi 2013). Falkingham & Gatesy 2014 informs the demonstration; it does not make it a replication.

%% CLOCK / NARRATION FIRST
# Lock words, performances and time
### Make editable, approved narration

For new speech, audition in the brief's language and accent using ~15 seconds of the actual copy, with numbers, place names and a turn in emphasis. Use the selected voice consistently. Record clauses or sections with handles as lossless WAV, not slices of an AAC mix. Keep originals, voice selection, text, pronunciation sheet, trims and hashes. Generating again is not byte-identical restoration.

Force-align the **approved words** (English baseline: 16 kHz mono input to the aligner, 100 ticks/s; keep the program at 48 kHz). Add dictionary entries and check ambiguous edges against waveform and playback. Keep spelling canonical even when the speech hint differs. Match active speech across takes; de-ess only as allowed. Preserve consonants, releases and useful breaths. Cut in verified low-energy handles with short cosine fades. Retake and re-align a revised line; do not pitch-shift or speed up speech to fix a hold.

### One clock drives the entire video

- **Timebase:** use integer frame indices and 48,000 Hz program samples. At 24 fps, a frame spans 2,000 samples; at 30 fps, 1,600. For these rates, `sample = frame × (48000 / FPS)`. Define rounding and use rational timestamps for other rates; never accumulate a rounded per-frame duration. Express ranges as [in, out) and derive the length from the final count.
- **Source of truth:** record each event as ID, frame/sample, object or word, and expected visual/audio result. Derive cuts, word highlights, map state, rig events, FX and subtitles from this lock. Generate renderer constants from the timeline rather than updating two lists by hand.
- **Gaps:** report aligned inter-phrase spacing, longest low-energy interval in the speech stem (band, window and threshold stated), and the quietest full-program interval as separate measures. Trim unearned holds in the edit; never pretend a louder music bed removes silence from the voice. Keep deliberate pauses only where they help the viewer see or think.
- **Locks:** distinguish original performance, locked PCM, locked encoded streams and locked timing grid. Freeze whichever the brief requires. An authorized recut rebuilds affected picture timing, cue sheet and SRT together. No silent timeline shifts.

> V2 cut the voice first: six original dry takes, 14 aligned phrases at original speed and a 2.603 s → 0.170 s reduction in the longest inter-phrase gap. Keep the intent, not that exact number, on a different script.

%% SCENE / NATIVE GEOMETRY AND MOVEMENT
# Build the action in 3D
### Geometry and contact, before polish

Work in a defined world scale and coordinate system. Build original sets, rigs, terrain, props and mechanisms; keep motion, camera, annotations and contact in that space. Use clean silhouettes, welded deforming forms and stable bind-pose material coordinates. Model foreground, mid-ground and distant layers for parallax. Separate loose pieces where occlusion matters. Check load-bearing joints and intersections throughout motion.

For an interaction, block **approach → initial contact → load/dwell → release → aftermath**. Make the surface react where force is applied and retain the altered state after the limb leaves. Use believable inertia, differential toe curl or heel roll when relevant, and avoid floating, sliding, penetration, ground reset or particles firing before impact. Log exact frame pins and geometry traces; pair the first picture action with the sound attack, then let secondary fragments land at motivated offsets.

**Reference implementation.** The Short uses a welded 52,042-vertex, 104,080-triangle foot. One generic rig and matched action/camera compare firm and soft beds. A close-up continues the soft state. The heightfield stamps an indent and rim with compaction, then area-weighted pairwise transfer relaxes the wet edge. The run logged ~0.000000012 relative transfer error, not mass conservation for the entire stamp or physics validation. It is illustrative CGI, not full MPM or a specimen-calibrated simulation.

### Light, material and optics

Keep albedo, relief/normals, roughness and wetness distinct. Build directional key, fill, contact shadows and occlusion cues in scene. Bounded GGX/Schlick shapes the Short’s wet/dry highlights; it is not offline path tracing. Two generated diffuse swatches provide grain only. Geometry, motion, camera and final pixels are rendered in code, not generated with a video model. Keep detail stable in object space. For water, use directional flow, depth/attenuation and Fresnel response; check moving highlights for shimmer.

Use perspective-correct interpolation, depth testing and projected anchors. Set lens, near/far, focus plane and key direction per shot. Make the focus pull reveal detail; don’t blur the contact the viewer must read. Match exposures across cuts, then composite and grade with a restrained highlight roll-off and readable cavities. Recheck moving detail after encoding.

%% PICTURE / DATA AND TYPOGRAPHY
# Make the picture explain itself
### Geography and evidence layers

For geography, build data-derived coast/relief fields from approved, pinned sources. Record period, projection, orbit, rotation convention and marker coordinates. Atlantic uses eight-channel float GEO8 fields: 2048 × 1024 for globe snapshots and 1280 × 1280 for local beds. Modern inputs are Natural Earth and NOAA ETOPO5 (public domain); ancient inputs are Kocsis–Scotese coastlines/rotations and Scotese–Wright PaleoDEMs (CC BY 4.0, adapted). Credit layers actually used.

Render a sphere with relief lighting, atmospheric falloff and a continuous camera. Reveal the separately sourced epoch on the sphere; don’t morph modern outlines into an invented plate history. Project each world-space marker and hide it at the limb, behind geometry or when its epoch is not legible. Route leaders to their own anchors. In the Short, modeled regional separation is ~6,085 km today and ~1,194 km in the 125 Ma snapshot. Neither measures a trail. Label reconstructions and illustrated tracks/strata long enough to read.

### Typography and accessibility are distinct layers

- **Kinetic captions:** use actually spoken words, grouped in natural 1–2-line phrases. Reserve emphasis for the words that carry the idea. V2 maps bevel-lit glyph masks and seven depth slices through a moving perspective plane with a short settle; it is composited lettering, not solid text mesh footage. Update when the word arrives; use tint/depth/pose to direct the eye, not incessant bouncing, all-caps or large opaque blocks. Give the audience time to read the complete phrase.
- **Anchored editorial graphics:** track a rim, location or label from the same geometry and CSV projection, not manual screen guesses. Use restrained contrast, scale and motion hierarchy. Keep qualifications at the same time as the relevant image. Do not add a sound to every type move.
- **Readability and captions:** check projected bounds and overshoot at final resolution and phone size. V2 used (68, 214)–(932, 1538) on 1080 × 1920; test the intended interface separately. Keep hero contact and map anchors clear. Generate full SRT cues from the alignment, with readable line breaks, no overlaps and no premature reveals. Preserve relevant non-speech information when accessibility requires it. The feature has selectable captions plus SRT; portrait burned-in groups do not replace the sidecar.

%% EDIT / PACE AND CONTINUITY
# Direct the cut for the viewer's eye
### Cut with purpose

Open on a leg already descending, a moving jaw, a visibly puzzling object, or another image that pays off the hook. Establish where the action is; move closer only when there is a new detail to read. A controlled dolly, focus pull or gentle impact impulse is more readable than arbitrary punch zooms or constant shake. Ease cameras into and out of significant movement, match screen direction and cut on action, on an occluding foreground object, or at a change of idea. Use J/L cuts only when the following sound or line clarifies the change.

For an A/B demonstration, hold viewpoint, scale, stimulus and main timing constant while changing the tested variable. Follow the action, then show the outcome at rest. Keep the compared feature intact and out from behind captions. If a split is too small, show matched takes in succession. Preserve screen direction and light relationships or clearly establish a new viewpoint. A 9:16 rebuild needs new camera staging and graphics, not a center crop of the long film.

### Apply the right rhythm to the requested format

- **Portrait:** fast first payoff, no extra opening or ending block and no needless dead air. Give the viewer one visual idea per beat. Preserve contact, lift, consequence and reaction; tighten holds around them, not the event itself. Reserve vertical space for motion, balanced negative space, and the UI-safe caption lane. If designed as a loop, end on a brief return that physically leads into frame zero. Compare pose, lens, position, shadows, material continuity, relative motion and the sound approach across the seam.
- **Landscape:** maintain long-form proof and placement between sections. Use orientation wides, tactility in macros, matched diagrams and quieter stretches only where earned. Keep the approved sequence grid, dialogue clock and chapter markers during a scoped refinement. Give evidence labels enough hold to be understood and reset the wide view after the detail if necessary. Do not force a looping outro.

**Review the complete proof at speed.** Watch with sound, on mute and at phone size. Find stretches where picture, speech and sound stop giving new information. Remove the wait, not by adding filler, and recompute dependent cues. In V2, the hook contacts at frame 5, the soft lip drops a chip at 190, the globe reveal spans 442–496 and the return starts at 696 of 735. Use exact event pins like these, not these timings for unrelated subjects.

%% SOUND / MATERIAL AND INTELLIGIBILITY
# Make the action audible
### Separate the buses and spot them precisely

Maintain dry narration, isolated timed Foley, scene ambience, music/tonal bed, and a lossless 48 kHz working master with reference stems. Use 24-bit PCM for the locked wave delivery/mix in this pipeline. Spot sound from **observed picture events**, not from an evenly spaced beat grid. Layer a short body, a real material attack and a little textured tail only when motivated. Trim each source around first audible attack after EQ or pitch treatment; verify it has not drifted a frame. The contact, release, later crumble, rock chip, map rewind, and sea entry are different events; give each a distinct sound and attack.

Use material-specific recordings from the cleared bank. In V2, real wet release, dry grit and stone combine with circular wind/water beds and a ~122 BPM pulse scored with pinned recordings. Change bandwidth, stereo width and room with scale, overlap ambience and make score space for tactile beats. Avoid fake snaps, constant risers or sounds attached to every word. Essential effects must read in mono without sub-bass. Log the actual sources and transformations.

### Mix around speech, then check the encode

Preserve a stable voice centre, intelligible consonants, headroom and natural breathing. Use local gain rides, gentle voice-keyed attenuation and selective upper-mid cuts on competing water/score/effects; if an accent is inaudible, correct the layer and timing, not the entire master gain. For the locked Cinema approach, add the stereo overlay to unchanged dry mono in both channels without clipping; subtract that overlay in integer PCM to prove exact narration identity before AAC. A recut may use its authorized gain/EQ/de-ess edits and keeps the original WAVs separately.

Measure EBU R128 integrated loudness (LUFS-I), true peak (dBTP), range and local dynamics both in PCM and decoded AAC. Compare aligned cue windows against the reference mix, inspect narration-minus-background in phone-mono bands (e.g. 185–4,800 Hz for V2; 250–4,800 Hz and 2.5–5 kHz spot checks for Cinema), listen for water masking or pumping, and report actual onset lags and floor windows. Use the reference loudness near −17 LUFS-I with headroom near −2 dBTP as a starting point, not as a universal standard or a reason to ignore a delivery specification.

For a loop, crossfade circular bed samples, shape and wrap tails, and inspect the decoded frame/sample junction. If AAC introduces a click, resolve it locally (V2 used a 6 ms taper on the bed only). Do not fade the dialogue to hide a gap or lose the first impact. Human headphone and phone-speaker checks are separate from signal statistics.

%% EXECUTION / PROVE BEFORE EXPENSIVE RENDERS
# Prove and render in stages
### Work in this order

1. **Inventory and prepare:** verify rights, exact hashes and locks. Use versioned scratch, staged and final locations. Restore original WAVs, sound bank, fonts and fields by their pins. Budget runtime, CPU and disk from a timed sample of the hardest shot. Keep deliverables and sources out of volatile scratch; generated plates and large media out of Git.
2. **Block and test risk:** test hard contact, material change, labels and loop in motion (Atlantic began with a ~4 s matched-view proof). Probe impact, lift, slump, chip, pin reveal and seam. Run a complete scored phone proof when pacing or typography changes; a still proof does not test the cut.
3. **Lock and stage:** compile the native renderer and stream ordered RGB frames plus one matching projection/state row per frame to Python. Fail on missing frames, stale traces, bad order or nonzero child exit. Check representative native probes as well as the phone proof before the long pass.
4. **Render and recover:** record frame spans, dimensions, compiler/libs, seeds, assets, scene/comp/clock fingerprints, traces and part hashes. Resume only matching parts. Re-render affected spans for scene changes; reuse clean plates for typography only if geometry and clock match. Stage incomplete work separately. Limit resources (baseline: two OpenMP threads for picture and one BLAS thread). Expect byte identity only with compatible tools; verify after an environment change.

### Existing repo routes (from the repository root)

| Mode | Use the relevant video stages |
| Portrait V2 | `tools/extinct-life/short/reedit/`: `prepare_reedit.py` → `mix_edit.py` → `build_reedit.py --phone-cut` → `verify_reedit.py --phone` → `build_reedit.py` → `verify_reedit.py`. `--proof` is stills only. Restore the six WAVs and two swatches via the checksum lock. |
| Cinema | `tools/extinct-life/step-8/`: restore Step 3 WAV/SRT/timing, the archived Investigation Cut and Step 6 `assets.py` and `sound_v2.py` outputs; `audit.py` → `render.py --group all` → `mix_cinema.py` → `conform.py --audio-preflight` → `conform.py`. `render.py --samples` / `--shots` for probes or repairs. |

The Cinema chain was evidence → voice lock → animatic → 3D opening proof → full film → Investigation Cut → Cinema Edition. Use each route’s README for paths and dependency pins. Previs example: `step-4/timeline.py`; fields: `step-5/prepare_terrain.py`. Use `--verify-only` to recheck a promoted master. Stop on lock mismatch, and never overwrite an archive.

%% FINISH / ENCODE AND MEASURE
# Conform and verify the actual master
### Correct output, not just the right dimensions

Match the intended aspect and scan. Baseline delivery: 1080 × 1920/30 for portrait, 1920 × 1080/24 for landscape; progressive CFR, MP4 fast-start, H.264 High, limited SDR BT.709 `yuv420p`, stereo 48 kHz AAC-LC. Use actual matrix/range conversion and matching tags, not tags alone. Use high-quality resampling and enough bits for moving relief, grain and type. Verify colour and range on decoded picture. Keep PCM until the final AAC encode.

Conform matching segments without recompression where possible. Check seekable shot joins, decode and presentation timestamps, edit lists, AAC priming and tail padding against logical duration. A sound-only revision must prove encoded video packet/timing identity. A picture-only revision must prove identity of locked encoded audio, captions and chapters (as in Investigation Cut). Cinema remixed beneath unchanged dry narration; it did not copy the old AAC. A recut gets a new clock, captions and version.

| Gate | Required proof before promotion |
| Picture | Decode every frame. Confirm cadence, expected start/end and format; flag unintended blacks, freezes or duplicates. Inspect decoded native and phone views around risky events, joins and the replay seam if applicable. |
| Scene and graphics | Compare traces and actual frames for contact/release order, material change, pose continuity, projection, depth/occlusion, label bounds and legibility. Confirm intended match cuts and absent false data. |
| Audio | Check logical duration/sample count, clip/true peak, LUFS-I, loudness balance, audible event attacks, intentional quiet and realistic seam. Correlate decoded AAC to program PCM in speech windows; measure error/SNR and compare mono phone band. Exact dry-voice proof is pre-AAC, not a claim of bit-perfect lossy encode. |
| Captions and locks | Validate language, text, order, hold/read time, bounds, SRT round-trip for selectable `mov_text`, chapters and required stream fingerprints. Check payloads and timestamps, not the container hash alone. |

Render to a pending file, fail on a gate, fix the source problem, rerun affected work and check the final mux again. Promote only the verified file and its matching caption. Record results for the actual file you hand over, not from a pre-encode WAV, still-only proof or a different version.

%% STANDARD / HISTORICAL RESULTS
# Use measured quality references
These are measured delivery results from the two Atlantic Tracks cuts, not universal thresholds or a guarantee of photorealism.

| Measure | Cinema Edition / landscape | V2 Kinetic Recut / portrait |
| Finished stream | 07:25.667; 10,696 frames; 66 shots; 1920 × 1080 / 24 fps | 24.500 s; 735 frames; 1080 × 1920 / 30 fps; 1,176,000 program samples |
| Working picture | 1152 × 648 or 960 × 540 scene plates by shot; composited and scaled to 1080p | 1152 × 2048 → 1080 × 1920; 540 × 960 full phone proof |
| Mix and encode | −17.2 LUFS-I, −2.0 dBTP; AAC 288 kb/s target; measured decoded AAC vs PCM SNR 35.647 dB | −16.9 LUFS-I, −2.1 dBTP; AAC 320 kb/s target; CRF 16.4 production encode; SNR 39.364 dB |
| Speech and text | 21,078,604 dry samples unchanged before AAC; 127 zero-offset decoded speech windows; 127 selectable EN cues and matching SRT; nine chapters | 14 zero-offset decoded speech windows; 14 full EN SRT cues; 722 frames with type and 984 extruded word plates (not unique frames) |
| Verification | All frames decoded; 263 sampled picture probes. “Sousa” needs human listening. | All frames decoded; 19 decoded phone probes (360 × 640). 19 pinned Foley attacks under 12 ms in the stem. |

### Know what caused the fixes

- **Dead gap:** V1 ran 34 s. V2’s 170 ms maximum aligned gap is not its 300 ms low-RMS limit (−43 dBFS in 10 ms speech-band bins). First word ~56 ms; aligned gap over replay ~235 ms. Performance beats matter more than any one number.
- **Codec and clarity:** Cinema’s 224 kb/s trial missed its >30 dB SNR gate; 288 kb/s passed. V2’s decoded phone-mono voice-to-bed separation was 12.13–18.55 dB across its cues. Set bands, windows and tolerances for each film; don’t just turn up the whole mix.
- **Replay:** V2 measured −60.64 dBFS decoded stereo seam delta and 3.3104 mean absolute RGB code-value difference at 72 × 128, last frame vs first. Neither metric replaces listening and watching the seam at speed.

Check `step-8/cinema-receipt.json` under `tools/extinct-life/` and V2’s `qa/verified.json` in `.cache/atlantic-short/reedit/` if restored. Code shows gates; receipts show results.

%% NEXT PASS / UPGRADE WITH PROOF
# Raise the quality with a matched test

### Make upgrades earn their cost

These are conditional upgrades, not features claimed for both historical files. Declare the problem and pass condition first. Compare the same event span and output spec before and after; keep resolution, encode, playback level and evaluation window comparable. Log the quality change, render cost and regressions. Revert changes that do not improve the intended shot.

- **First: causality and pace.** If the hook is late, remove the wait without clipping a consonant or the contact. For muddy comparison, reframe and match projection before adding effects. For weak sound, retime or rebalance its isolated stem; judge on phone-mono and at full playback. Verify result and intent at normal speed.
- **Then: optics and finish.** If movement stutters or textures crawl, test temporal or spatial supersampling on the worst motion. Avoid blurring the contact; composite sharp graphics after optical blur. Test softer grounded shadows, light separation and stable filtering for improved shape. For a higher-bit/scene-referred comp, test a grey ramp and highlights through the SDR export before switching. Fit complex simulation only with calibration and a visible gain.
- **Spend render budget where it reads.** Compare plates to the resized delivery for a macro, a wide and any motion-heavy shot. Allocate more samples/pixels to fine evidence, less to distant or off-screen detail. Don’t trade readable typography or the reaction shot for bigger resolution numbers. Switch backend only when available and a comparable proof wins; rerun its gates and don’t imply it was used historically.
- **Make checks repeatable.** Keep a shared event schema, dependency-aware rebuilds, intermediate/reference comparisons and automated timing, geometry and type-bounds checks. Distinguish exact identity where locked from tolerance-based comparisons for new renders. A statistical pass is not the viewer’s experience.

> Example acceptance: a closer mud-edge shot must carry the same lip state across the cut, show the chip after lift and keep captions clear of both. Its encode must keep the sound pin and readable detail at phone size. If not, fix staging and sync before increasing shading quality.

%% HANDOFF / REVIEW AND DELIVERY
# Review the file you will hand over

### Watch and listen at speed

Use the exact verified MP4 intended for delivery, not the stems or preview. For portrait, watch on a phone with intended interface margins and listen in mono on its speaker. For landscape, watch at display scale with selectable captions off and on. In both, listen on headphones too. Watch muted for motion and graphic clarity, then watch with sound without stopping. Diagnose unclear moments with frame, waveform and cue probes. For a loop, play three repeats and check the join for image jumps, clipped releases, silence or clicks.

Check pronunciations and factual labels with a qualified reviewer when available. Cinema’s pending example is **Sousa at 03:34–03:39**: the hint was *Sohza*, but forced alignment is not human approval. If a device, listener or test is unavailable, say what is unverified. Do not invent an owner gate; hold final delivery if a required review has not passed.

### Hand off the film, not the workshop

Deliver one versioned verified MP4 and its matching SRT in the brief’s language. Include a concise technical receipt or handoff note. Keep exact inputs, dry takes, timeline, clean plates when practical, project, stems, proof logs, traces and hashes recoverable under the agreed storage policy. Share internal working files only when asked. Never overwrite the previous delivery.

In the receipt distinguish **rendered**, **fully decoded**, **visually sampled**, **instrumented audio verified** and **human reviewed**. Record names and SHA-256, format, working vs delivery resolution, frame/sample counts, locks exercised, results with tolerances, changes and unresolved limitations with timecodes. State who did what kind of review only if it happened.

**Final rule.** Correct anything material that fails. If an input or required check is unavailable, report what was completed and what is blocked. Never deliver a proof as a master. Present only the requested video and its matching in-video production deliverables.

> END OF PROMPT
