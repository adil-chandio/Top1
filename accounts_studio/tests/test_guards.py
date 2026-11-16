"""Delivery barrier tests.

The barrier's job is to make it impossible to hand over a file that QC did not
review, or to deliver the same rejected film twice. These tests attack it.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from accounts_studio import guards
from accounts_studio.pipeline import create, save


class ArtifactIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.job = create(self.temp.name, 'soc_01', 'guard fixture')
        self.file = self.job / 'out.txt'
        self.file.write_text('bytes under test', encoding='utf-8')
        self.result = {'artifacts': [
            {'path': 'out.txt',
             'sha256': hashlib.sha256(self.file.read_bytes()).hexdigest()}]}

    def test_unchanged_artifact_passes(self):
        guards.artifact_integrity(self.job, self.result)

    def test_changed_artifact_raises(self):
        self.file.write_text('tampered', encoding='utf-8')
        with self.assertRaises(ValueError) as ctx:
            guards.artifact_integrity(self.job, self.result)
        self.assertIn('missing or changed', str(ctx.exception))

    def test_deleted_artifact_raises(self):
        self.file.unlink()
        with self.assertRaises(ValueError):
            guards.artifact_integrity(self.job, self.result)

    def test_path_escape_raises(self):
        with self.assertRaises(ValueError):
            guards.artifact_integrity(
                self.job, {'artifacts': [{'path': '../escape', 'sha256': 'x'}]})


class DeliveryPreflightTests(unittest.TestCase):
    """No receipt, no delivery. A review that reviewed different bytes is worthless."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.job = create(self.temp.name, 'soc_01', 'delivery fixture')
        (self.job / 'active_release.json')
        self.video = self.job / 'final.mp4'
        self.video.write_bytes(b'\x00\x00\x00 ftypisom fake but hashed')
        self.vsha = hashlib.sha256(self.video.read_bytes()).hexdigest()
        # Each stage gets its OWN receipt, because the barrier checks that each
        # review inspected exactly that stage's artifact hashes.
        self.stage_hashes = {
            'production': [self.vsha],
            'qc': [hashlib.sha256(b'qc-evidence').hexdigest()],
            'packaging': [hashlib.sha256(b'packaging-evidence').hexdigest()],
        }
        self.receipts = {}
        self.state = {'outputs': {}, 'accepted_reviews': {}}
        for stage, hashes in self.stage_hashes.items():
            receipt = self.job / f'{stage}-review.json'
            receipt.write_text(json.dumps(
                {'approved': True, 'inspected_artifacts': hashes,
                 'findings': 'fixture'}), encoding='utf-8')
            self.receipts[stage] = receipt
            self.state['accepted_reviews'][stage] = {
                'path': receipt.name,
                'sha256': hashlib.sha256(receipt.read_bytes()).hexdigest()}
            if stage == 'production':
                arts = [{'path': 'final.mp4', 'sha256': self.vsha}]
            else:
                # QC and packaging each cite their own evidence file.
                ev = self.job / f'{stage}-evidence.bin'
                ev.write_bytes(stage.encode() + b'-evidence')
                arts = [{'path': ev.name,
                         'sha256': hashlib.sha256(ev.read_bytes()).hexdigest()}]
                self.stage_hashes[stage] = [arts[0]['sha256']]
                self.receipts[stage].write_text(json.dumps(
                    {'approved': True,
                     'inspected_artifacts': self.stage_hashes[stage],
                     'findings': 'fixture'}), encoding='utf-8')
                self.state['accepted_reviews'][stage] = {
                    'path': self.receipts[stage].name,
                    'sha256': hashlib.sha256(
                        self.receipts[stage].read_bytes()).hexdigest()}
            self.state['outputs'][stage] = {'artifacts': arts}
        self.state['outputs']['qc']['reviewed_production_sha256'] = self.vsha

    def _preflight(self):
        # production_preflight is exercised separately; here we test the checks
        # that do not need an on-disk release manifest.
        saved = guards.production_preflight
        guards.production_preflight = lambda: True
        try:
            return guards.delivery_preflight(self.job, self.state)
        finally:
            guards.production_preflight = saved

    def test_complete_evidence_passes(self):
        self.assertTrue(self._preflight())

    def test_missing_review_receipt_raises(self):
        del self.state['accepted_reviews']['qc']
        with self.assertRaises(ValueError) as ctx:
            self._preflight()
        self.assertIn('missing independent qc review', str(ctx.exception))

    def test_receipt_pointing_at_changed_file_raises(self):
        self.receipts['qc'].write_text('{"approved": false}', encoding='utf-8')
        with self.assertRaises(ValueError) as ctx:
            self._preflight()
        self.assertIn('review receipt changed', str(ctx.exception))

    def test_review_that_inspected_other_bytes_raises(self):
        self.receipts['qc'].write_text(json.dumps(
            {'approved': True, 'inspected_artifacts': ['a' * 64],
             'findings': 'fixture'}), encoding='utf-8')
        self.state['accepted_reviews']['qc']['sha256'] = hashlib.sha256(
            self.receipts['qc'].read_bytes()).hexdigest()
        with self.assertRaises(ValueError) as ctx:
            self._preflight()
        self.assertIn('binding mismatch', str(ctx.exception))

    def test_two_final_videos_rejected(self):
        """A second video must never slip through, by any check order.

        Rebuilding the production review to cover both files is the only way to
        reach the one-video rule; a lazier forgery is caught earlier by the
        binding check. Both outcomes are a refusal, and that is the point.
        """
        other = self.job / 'second.mp4'
        other.write_bytes(b'other')
        other_sha = hashlib.sha256(other.read_bytes()).hexdigest()
        self.state['outputs']['production']['artifacts'].append(
            {'path': 'second.mp4', 'sha256': other_sha})
        # attempt 1: leave the review untouched -> binding mismatch
        with self.assertRaises(ValueError) as ctx:
            self._preflight()
        self.assertIn('binding mismatch', str(ctx.exception))
        # attempt 2: forge a review covering both -> the one-video rule fires
        self.receipts['production'].write_text(json.dumps(
            {'approved': True, 'inspected_artifacts': [self.vsha, other_sha],
             'findings': 'fixture'}), encoding='utf-8')
        self.state['accepted_reviews']['production']['sha256'] = hashlib.sha256(
            self.receipts['production'].read_bytes()).hexdigest()
        with self.assertRaises(ValueError) as ctx:
            self._preflight()
        self.assertIn('exactly one final video', str(ctx.exception))

    def test_rejected_hash_cannot_be_redelivered(self):
        self.state['rejected_video_hashes'] = [self.vsha]
        with self.assertRaises(ValueError) as ctx:
            self._preflight()
        self.assertIn('cannot be redelivered', str(ctx.exception))

    def test_user_rejected_flag_blocks(self):
        self.state['user_rejected'] = True
        with self.assertRaises(ValueError) as ctx:
            self._preflight()
        self.assertIn('user-rejected', str(ctx.exception))

    def test_qc_bound_to_a_different_video_raises(self):
        self.state['outputs']['qc']['reviewed_production_sha256'] = 'b' * 64
        with self.assertRaises(ValueError) as ctx:
            self._preflight()
        self.assertIn('QC belongs to different video', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
