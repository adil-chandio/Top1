"""Build a DESIGN-ONLY map from existing approximate acoustic cues; no media generation."""
import hashlib
import json
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

def build():
    alignment_path = ROOT / 'research/monarch_cam_gecko_batch3/ENGLISH_WORD_ALIGNMENT.json'
    cues_path = ROOT / 'research/monarch_cam_gecko_batch3/ENGLISH_CAPTION_CUES.json'
    timing = json.loads((ROOT / 'research/monarch_cam_gecko_batch3/NARRATION_TIMING_RECEIPT.json').read_text())
    alignment = json.loads(alignment_path.read_text())
    cues = json.loads(cues_path.read_text())['cues']
    audio = ROOT / 'studio/runtime/gecko/narration/english-narration-v1.wav'
    # Existing draft voice only; a technical identity check is not listening approval.
    with wave.open(str(audio)) as stream:
        duration = stream.getnframes() / stream.getframerate()
    audio_hash = hashlib.sha256(audio.read_bytes()).hexdigest()
    assert audio_hash == timing['combined_sha256'] == alignment['audio_sha256']
    assert duration == timing['total_seconds'] == alignment['duration'] == 63.68
    # Boundaries selected from existing cue starts. Exact join and file tail are separate anchors.
    specs = [
        ('S01', 0, 5.71, 'Question', 'Context-to-foot approach; only a restrained tip-lift preview, not a complete cycle.', 'same foot, wall and marked digit established', 'support or anatomy invented; bar on empty field'),
        ('S02', 5.71, 11.08, 'Control', 'Hold the located foot and pad; subtle loaded versus beginning-to-lift contrast.', 'one location through contrast', 'contact highlight alone changes while geometry remains unrelated'),
        ('S03', 11.08, 16.14, 'Hierarchy', 'Match the marked pad region into an explicitly simplified lamella/seta hierarchy.', 'locator persists; scale change declared schematic', 'hair forest disconnected from toe; layer width treated as adhesive boundary'),
        ('S04', 16.14, 20.27, 'Close contact', 'Branching schematic tips approach the same surface plane; avoid literal molecular-scale realism.', 'tip/surface relation readable', 'liquid bridge, suction cavity or literal spring bonds'),
        ('S05', 20.27, 26.59, 'Not suction', 'Keep branching tips and surface; a short English label supplies terminology, no negative-example detour.', 'same scale; absence of suction not a new mechanism', 'vacuum-like contact or unsupported force graph'),
        ('S06', 26.59, 28.41, 'Orientation', 'Return to matched toe side-oblique view; locate BASE and TIP before directional cue.', 'base screen-left; tip screen-right; wall below in local view', 'unannounced mirroring or oblique arrow read as pulling away'),
        ('S07', 28.41, 33.20, 'Loading', 'One proximal arrow parallel to surface; contact region explicitly qualitative, no visible sliding required.', 'wall normal and digit identity retained', 'arrow points into wall, is mislabeled muscle force, or implies solved adhesion'),
        ('S08', 33.20, 37.50, 'Release onset', 'Continuous macro shot: establish contact, then active distal tip lift produces a visible small gap.', 'release group R01: no picture cut/reset', 'whole pad disappears; tip penetrates surface; no geometric gap'),
        ('S09', 37.50, 44.02, 'Progressive release', 'Continue same shot; release front progresses toward base; clear gap and settled detached state.', 'R01 camera/surface identity preserved throughout', 'cut hides continuity; contact proxy relabeled measured setal area'),
        ('S10', 44.02, 47.95, 'Name the toe motion', 'Use the settled macro toe and restrained outline cue; name DIGITAL HYPEREXTENSION.', 'same toe; no second inconsistent release', 'text overwhelms toe or schematic is sold as measured skeletal motion'),
        ('S11', 47.95, 52.19, 'Separate scales', 'Show clearly bounded microscopic inset while toe remains main image; no numeric angles.', 'inset is different scale, not an X-ray view', 'array angle becomes a toe-joint instruction'),
        ('S12', 52.19, 55.82, 'Return', 'Match back to located foot/context and visible toe clearance; no full walk-cycle requirement.', 'solid physical gap before text summary', 'teleporting replant or full natural gait asserted'),
        ('S13', 55.82, 63.68, 'Causal payoff', 'Local original action/context remains; introduce contact, load direction, toe movement sequentially.', 'three cues tied to visible anatomy rather than recap cards', 'three simultaneous panels, generic bar, unsupported strength/energy claim'),
        ('S14', 63.68, 70.00, 'Unvoiced hold / compact sources', 'Provisional readable end hold on settled original scene; short source card plus companion full credits.', 'no voice retiming; final readability and credit text still pending', 'end card treated as full asset-rights clearance or unreadably dense credits'),
    ]
    shots = []
    for sid, start, end, purpose, action, continuity, reject in specs:
        indices = [i for i, c in enumerate(cues) if c['start'] < end and c['end'] > start]
        shots.append(dict(id=sid, start=start, end=end, purpose=purpose, action=action,
                          continuity=continuity, reject_if=reject, cue_indices=indices,
                          narration=' '.join(cues[i]['text'] for i in indices),
                          cut_at_start_allowed=sid != 'S09',
                          continuous_group='R01' if sid in ('S08', 'S09') else None))
    return {
        'status': 'DESIGN_ONLY_PRODUCTION_HELD', 'language': 'English', 'voice_id': 'voice-09',
        'voice_selection': 'user selected English audition09; no new synthesis',
        'audio': {'path': str(audio.relative_to(ROOT)), 'sha256': audio_hash, 'seconds': duration,
                  'listened': False, 'speed_processing_this_plan': 'none'},
        'timing_evidence': {'cues': str(cues_path.relative_to(ROOT)),
                            'alignment': str(alignment_path.relative_to(ROOT)),
                            'internal_boundaries': 'approximate transcript-constrained acoustic cues; not ear-verified cuts',
                            'exact_assembly_anchors': [0, 33.2, 63.68],
                            'picture_end_70s': 'editorial proposal, not generated export or biological timing'},
        'rig_decision': 'HYBRID_PROPOSED_NOT_ASSET_APPROVED',
        'context_required': 'source-grounded exterior foot/contact context; no schematic-bar-only final substitute',
        'mechanism_insert': 'explicitly qualitative single-digit motion; no measured skeletal/tendon or natural gait claim',
        'whole_animal_walk_cycle_required': False,
        'production_authorized': False, 'audio_qc_passed': False, 'anatomy_qc_passed': False,
        'rights_qc_passed': False, 'native_av_qc_passed': False, 'shots': shots,
    }

if __name__ == '__main__':
    data = build()
    dest = HERE / 'ENGLISH_RESEARCH_DERIVED_EDIT_MAP.json'
    dest.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'map': str(dest.relative_to(ROOT)), 'shots': len(data['shots']),
                      'audio_identity_verified': True, 'production_authorized': False}))
