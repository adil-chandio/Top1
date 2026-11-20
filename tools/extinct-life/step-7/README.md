# Atlantic Tracks — Investigation Cut

Picture revision of **Why These Dinosaur Footprints Are an Ocean Apart**. It uses the sound-redesigned full film as the comparison baseline and **copies its AAC, English timed-text and chapters**. No synthesized performance, captions, gain, audio edit, chapter, or running time changes. This is a separate review file, not a master replacement or publication.

## The edit

A clue is introduced, tested and then either kept or qualified. The paired print framing opens the film and comes back before the answer. Both map endpoints use the same Atlantic crop; the wipe compares two independent model states, not an invented coastline animation. The title is integrated into the landscape rather than given the full original hold.

| Start | Sequence | What changes on screen |
|---|---|---|
| 00:00 | The match | Two close prints; cartographic measure at the same scale, today vs. the 125 Ma model. |
| 01:01 | Preserve a clue | Peel apart walked surfaces, lose part of a rock edge, reconstruct the remaining relief from illustrative overlapping views. |
| 02:01 | Same-stamp test | Identical carved stamps with a shared descent, dwell and release clock. Firm mud holds the rim; wetter mud is modeled to deform and slump. Close and overhead readouts. |
| 02:49 | Why a print lasts | Retain the water retreat and erosion actions. Enlarge grain bonds and possible mat binding, then show younger sediment cover the print. |
| 04:01 | Break the false match | Similar banks, different sections, schematic age windows and a distinct regional pollen deposit rather than a date pin on either track bed. |
| 05:57 | Another kind of evidence | Swim toward camera, cut on the fish's orientation to an illustrative fossil, then compare fragments from other basins. The three future tests have separate visual beats. |
| 06:45 | It was the rocks | Tectonic cutaway and rising waterline; return to today's gap and the print pair. Each impression is locked to its own moving geological block. Match-cut to the opening print. |

The camera can move inside a shot slot, but all 66 original shot starts are on the locked 24 fps grid. In particular the mud impact, lift, slump, fault drop, staged sea entry and answer are storyboarded against the original audio anchors. Strong existing evidence beats (including field survey, initial foot plant/peel, small steps and water retreat) are retained rather than remade to inflate the change count.

All local terrain/print/grain/pollen/fossil renders are explanatory models, not survey images. Published rounded regional distances are used; **125 Ma is not a footprint date**. The **~69 cm** measure is one impression, not body size. Dates on the chart are broad assignments with no quantified endpoints or assumed contemporaneity. Regional pollen clues do not directly date the track beds. Fish finds are from **other basins**, not those beds; a plausible dispersal area is not a river trace or individual journey. The handoff and in-file metadata credit the original research, CC BY maps, and retained audio recordings.

## Rebuild / verify

Use the same Python dependencies and prepared fields/fonts as [Step 6](../step-6/README.md). Get the locked SRT/timing materials from [Step 3](../step-3/vo-v2-receipt.json). Restore the [Sound Redesign MP4](../step-6/sound-v2-drive-handoff.json) and its bit-identical `.en.srt` to `deliverables/extinct-life-step-6/` with the names in [its receipt](../step-6/sound-v2-receipt.json). The 10 retained original shot encodes are read from `film/picture/`; if a cache was lost, regenerate the original clean plates and the necessary ranges (`07–11`, `25–26`, `28–29`, `35`) using Step 6's readme, pinned inputs and build commands. Do not mix a regenerated picture with a different narration lock.

```sh
export PYTHONPATH="$PWD/.cache/film-python" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
s=tools/extinct-life/step-7
python3 "$s/sample_frames.py" --compile   # local visual probes, not an export
python3 "$s/render.py"
python3 "$s/finish_investigation.py"
```

`render.py --compile --tools-only` just builds the native executable. The inclusive zero-based `--from` / `--to`, or `--only` with a list of edited shots, are convenient for look approval and targeted repairs. Each new shot has a frame-bound receipt and a SHA-256; a normal build accepts only the same render revision for every new shot. A selective refinement pass can be conformed by explicitly naming its original fingerprint and the exact amended shot numbers. No cache-presence-based mixing. All intermediate files (including decoded proof sheets) are under `film/investigation/`, separate from the original plates and mix. With two CPU cores, the wide ray-cast landscapes cost materially more render time than the lab sets and atlas.

`finish_investigation.py` checks the RED source hash, sample clock and chapter grid; conformed AAC packet payloads and timestamps **and decoded stereo output**; exact subtitle and chapter samples; SRT round-trip; all 10,696 decoded pictures and retained-vs-replaced shot probes. `--verify-only` repeats those checks on the delivered MP4 without changing media. The [receipt](investigation-receipt.json) records the result. Frame and waveform matching are not human approval or audience-retention information. Listen to **Sousa** at 03:34–03:39 before release.

The MP4, `.en.srt` and `-Handoff.md` are in `deliverables/extinct-life-step-7/`. Keep generated media out of Git. The original, opening approvals, and Sound Redesign remain separate.

## Delivered review

Investigation Cut MP4 · unchanged English SRT · [Drive verification](investigation-drive-handoff.json). The 93,022,469-byte MP4 was relisted with matching checksums in the existing `3d animation` folder. The identical SRT is already present there; no duplicate was needed. The local handoff includes the cue review, science boundaries and source credits.
