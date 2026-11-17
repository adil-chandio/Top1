"""Structural checks only: never a scientific, visual, hearing or craft pass."""
import importlib.util
import json
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('preproduction', HERE / 'build_preproduction_map.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PreproductionMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((HERE / 'ENGLISH_RESEARCH_DERIVED_EDIT_MAP.json').read_text())
        cls.cues = json.loads((ROOT / 'research/monarch_cam_gecko_batch3/ENGLISH_CAPTION_CUES.json').read_text())['cues']

    def test_reproducible_and_existing_audio_hash_bound(self):
        self.assertEqual(self.plan, module.build())

    def test_all_cues_exactly_once(self):
        indices = [i for shot in self.plan['shots'] for i in shot['cue_indices']]
        self.assertEqual(indices, list(range(len(self.cues))))
        for shot in self.plan['shots']:
            for i in shot['cue_indices']:
                self.assertGreaterEqual(self.cues[i]['start'], shot['start'])
                self.assertLessEqual(self.cues[i]['end'], shot['end'])

    def test_no_timeline_gap_overlap_or_zero_length(self):
        shots = self.plan['shots']
        self.assertEqual(shots[0]['start'], 0)
        self.assertEqual(shots[-1]['end'], 70)
        for index, shot in enumerate(shots):
            self.assertGreater(shot['end'], shot['start'])
            if index:
                self.assertEqual(shots[index-1]['end'], shot['start'])

    def test_release_has_no_hidden_picture_cut(self):
        release = [s for s in self.plan['shots'] if s['continuous_group'] == 'R01']
        self.assertEqual([s['id'] for s in release], ['S08', 'S09'])
        self.assertEqual(release[0]['start'], 33.2)
        self.assertEqual(release[-1]['end'], 44.02)
        self.assertFalse(release[1]['cut_at_start_allowed'])

    def test_script_text_not_silently_rewritten(self):
        script = (ROOT / 'research/monarch_cam_gecko_batch3/SCRIPT_AND_FILM_BLUEPRINT_ENGLISH.md').read_text()
        narration = script.split('## Narration — recording text\n', 1)[1].split('\n## Packaging', 1)[0]
        normalize = lambda text: re.findall('[a-z0-9]+', text.lower())
        self.assertEqual(normalize(narration), normalize(' '.join(s['narration'] for s in self.plan['shots'])))

    def test_ending_is_unvoiced_proposal(self):
        last = self.plan['shots'][-1]
        self.assertEqual(last['start'], self.plan['audio']['seconds'])
        self.assertEqual(last['cue_indices'], [])
        self.assertIn('proposal', self.plan['timing_evidence']['picture_end_70s'])

    def test_no_implicit_production_or_quality_pass(self):
        self.assertEqual(self.plan['status'], 'DESIGN_ONLY_PRODUCTION_HELD')
        for key in ('production_authorized', 'audio_qc_passed', 'anatomy_qc_passed', 'rights_qc_passed', 'native_av_qc_passed', 'whole_animal_walk_cycle_required'):
            self.assertIs(self.plan[key], False)
        self.assertFalse(self.plan['audio']['listened'])
        self.assertEqual(self.plan['language'], 'English')
        self.assertEqual(self.plan['voice_id'], 'voice-09')
        self.assertIn('not ear-verified', self.plan['timing_evidence']['internal_boundaries'])


if __name__ == '__main__':
    unittest.main()
