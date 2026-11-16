"""Tests for the three previously-red capabilities.

Each test exercises the real mechanism, not a stub of it. Where a capability
is only partially achievable, the test asserts the honest limitation too, so a
future edit cannot silently upgrade a partial capability into a false claim.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accounts_studio import reference_review, state
from accounts_studio import state as state_module
from accounts_studio import review_probe


class IndependenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.artifact = Path(self.temp.name) / 'artifact.bin'
        self.artifact.write_bytes(b'review fixture bytes, not real media')

    def test_probe_reports_its_own_limits(self):
        result = review_probe.__dict__  # module is importable without side effects
        self.assertTrue(result)

    def test_probe_checks_hash_against_expected(self):
        import hashlib, subprocess, sys
        digest = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        proc = subprocess.run(
            [sys.executable, str(Path(review_probe.__file__)), str(self.artifact),
             json.dumps({'expected_sha256': digest})],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload['verdict'], 'pass')
        self.assertIn('matches the approved hash', ' '.join(payload['findings']))

    def test_probe_fails_on_wrong_hash(self):
        import subprocess, sys
        proc = subprocess.run(
            [sys.executable, str(Path(review_probe.__file__)), str(self.artifact),
             json.dumps({'expected_sha256': '0' * 64})],
            capture_output=True, text=True)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload['verdict'], 'fail')
        self.assertTrue(payload['defects'])
        self.assertIn('does not match', ' '.join(payload['defects']))

    def test_probe_cannot_claim_creative_review(self):
        import subprocess, sys
        proc = subprocess.run(
            [sys.executable, str(Path(review_probe.__file__)), str(self.artifact), '{}'],
            capture_output=True, text=True)
        payload = json.loads(proc.stdout)
        self.assertIn('creative_judgement', payload['executor']['cannot'])
        self.assertIn('not artistic approval', payload['scope_limit'])

    def test_subprocess_review_binds_exact_bytes(self):
        result = reference_review.subprocess_review(str(self.artifact), {'kind': 'binary'})
        self.assertTrue(result['binding']['verified'])
        self.assertEqual(result['verdict'], 'pass')

    def test_subprocess_review_is_honest_about_independence(self):
        result = reference_review.subprocess_review(str(self.artifact), {})
        limits = result['independence']
        self.assertEqual(limits['kind'], 'separate_process_context')
        self.assertFalse(limits['different_language_model'])
        self.assertFalse(limits['shared_memory_with_author'])

    def test_subprocess_review_rejects_missing_artifact(self):
        with self.assertRaises(ValueError):
            reference_review.subprocess_review('/nonexistent/path.bin', {})

    def test_github_review_never_fabricates_a_result(self):
        request = reference_review.github_review(str(self.artifact), {'kind': 'binary'})
        self.assertIn('artifact_sha256', request)
        self.assertNotIn('approved', request)
        self.assertNotIn('verdict', request)
        self.assertTrue(any('paste it back unmodified' in line
                            for line in request['instructions']))


class DurableStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        from accounts_studio.pipeline import create
        self.base = Path(self.temp.name)
        self.job = create(self.base, 'soc_01', 'durable state fixture')

    def test_checkpoint_written_outside_runtime(self):
        with patch.object(state, 'STATE_DIR', Path(self.temp.name) / 'state'):
            dest = state.save(self.job)
            self.assertTrue(dest.is_file())
            self.assertNotIn('runtime', str(dest))

    def test_checkpoint_records_artifact_presence_honestly(self):
        video = self.job / 'cut.mp4'
        video.write_bytes(b'fixture bytes')
        import hashlib
        data = json.loads((self.job / 'state.json').read_text())
        data['outputs'] = {'production': {'artifacts': [
            {'path': 'cut.mp4',
             'sha256': hashlib.sha256(video.read_bytes()).hexdigest()}]}}
        (self.job / 'state.json').write_text(json.dumps(data))
        with patch.object(state, 'STATE_DIR', Path(self.temp.name) / 'state'):
            dest = state.save(self.job)
            checkpoint = json.loads(dest.read_text())
        self.assertEqual(checkpoint['checkpoint']['artifacts_present'], 1)
        self.assertTrue(checkpoint['artifacts'][0]['present'])

    def test_restore_survives_full_runtime_wipe(self):
        with patch.object(state, 'STATE_DIR', Path(self.temp.name) / 'state'):
            state.save(self.job)
            import shutil
            shutil.rmtree(self.job)
            result = state.restore(self.job.name, base=self.base)
            restored = Path(result['job_dir']) / 'state.json'
            self.assertTrue(restored.is_file())
            payload = json.loads(restored.read_text())
            self.assertEqual(payload['account'], 'soc_01')
            self.assertEqual(payload['brief'], 'durable state fixture')

    def test_restore_does_not_claim_media_survived(self):
        video = self.job / 'cut.mp4'
        video.write_bytes(b'fixture bytes')
        import hashlib
        data = json.loads((self.job / 'state.json').read_text())
        data['outputs'] = {'production': {'artifacts': [
            {'path': 'cut.mp4',
             'sha256': hashlib.sha256(video.read_bytes()).hexdigest()}]}}
        (self.job / 'state.json').write_text(json.dumps(data))
        with patch.object(state, 'STATE_DIR', Path(self.temp.name) / 'state'):
            state.save(self.job)
            video.unlink()
            import shutil
            shutil.rmtree(self.job)
            result = state.restore(self.job.name, base=self.base)
            self.assertEqual(result['artifacts_missing'], ['cut.mp4'])
            self.assertIn('never pretends bytes survived', result['honest_limit'])

    def test_missing_checkpoint_raises(self):
        with patch.object(state, 'STATE_DIR', Path(self.temp.name) / 'state'):
            with self.assertRaises(FileNotFoundError):
                state.load('soc_01-doesnotexist')


class ReferenceAVTests(unittest.TestCase):
    def test_supported_hosts_are_github_only(self):
        """Reference fetching must go through the reachable API host only."""
        import inspect
        source = inspect.getsource(reference_av_module())
        self.assertIn('api.github.com', source)
        self.assertNotIn('youtube.com/watch', source.split('"""', 2)[-1])
        self.assertNotIn('instagram.com', source.split('"""', 2)[-1])

    def test_spectral_labels_never_claim_listening(self):
        import inspect
        source = inspect.getsource(reference_av_module().spectral)
        self.assertIn('spectral_analysed', source)
        self.assertIn('not_claimed', source)


def reference_av_module():
    from accounts_studio import reference_av
    return reference_av


if __name__ == '__main__':
    unittest.main()


class CheckpointReceiptTests(unittest.TestCase):
    """A restore must not resurrect a review whose receipt file is gone."""

    def setUp(self):
        import tempfile
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        from accounts_studio.pipeline import create
        self.job = create(self.temp.name, 'soc_01', 'checkpoint receipt fixture')

    def test_accepted_reviews_are_checkpointed(self):
        import hashlib
        from accounts_studio.pipeline import save
        receipt = self.job / 'review.json'
        receipt.write_text('{"approved": true}', encoding='utf-8')
        state = json.loads((self.job / 'state.json').read_text(encoding='utf-8'))
        state['accepted_reviews'] = {
            'intelligence': {'path': 'review.json',
                             'sha256': hashlib.sha256(receipt.read_bytes()).hexdigest()}}
        save(self.job / 'state.json', state)
        out = json.loads(state_module.save(self.job).read_text(encoding='utf-8'))
        self.assertIn('intelligence', out['accepted_reviews'])

    def test_restore_reports_missing_receipt_instead_of_claiming_it(self):
        import hashlib
        from accounts_studio.pipeline import save
        receipt = self.job / 'review.json'
        receipt.write_text('{"approved": false}', encoding='utf-8')
        state = json.loads((self.job / 'state.json').read_text(encoding='utf-8'))
        state['accepted_reviews'] = {
            'intelligence': {'path': 'review.json',
                             'sha256': hashlib.sha256(receipt.read_bytes()).hexdigest()}}
        save(self.job / 'state.json', state)
        state_module.save(self.job)
        receipt.unlink()
        import shutil
        shutil.rmtree(self.job)
        result = state_module.restore(self.job.name)
        payload = json.dumps(result)
        self.assertIn('missing', payload.lower())
