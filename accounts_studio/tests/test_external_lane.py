"""Tests for the external execution lane.

The lane's whole value is that a different machine produced the evidence. So
the tests here guard one property above all: **the client must never invent a
result that the runner did not produce.** A future edit that turns "runner has
not reported yet" into "green" must fail these tests.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accounts_studio import external_lane


class LaneArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def _write(self, rel, payload):
        path = self.base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding='utf-8')
        return path

    def test_missing_artifact_raises_instead_of_returning_a_guess(self):
        with self.assertRaises(FileNotFoundError):
            external_lane.load('asr', self.base)

    def test_unknown_artifact_kind_is_rejected(self):
        with self.assertRaises(KeyError):
            external_lane.load('not_a_real_capability', self.base)

    def test_load_returns_runner_payload_verbatim(self):
        payload = {'route': 'github_actions_runner', 'transcript': 'x', 'model': 'small'}
        self._write(external_lane.ARTIFACTS['asr'], payload)
        self.assertEqual(external_lane.load('asr', self.base), payload)


class LaneCapabilityReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def _write(self, rel, payload):
        path = self.base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding='utf-8')

    def test_absent_evidence_is_reported_missing_not_green(self):
        report = external_lane.capability_report(self.base)
        self.assertEqual(len(report), len(external_lane.ARTIFACTS))
        for name, entry in report.items():
            self.assertEqual(entry['status'], 'missing', name)
            self.assertFalse(entry['present'])
        self.assertNotIn('green', {e['status'] for e in report.values()})

    def test_artifact_without_runner_marker_is_not_green(self):
        self._write(external_lane.ARTIFACTS['vision'],
                    {'frames': [], 'note': 'local guess, no route marker'})
        report = external_lane.capability_report(self.base)
        self.assertEqual(report['vision']['status'], 'unverified')
        self.assertIn('route marker', report['vision']['reason'])

    def test_artifact_with_runner_marker_is_green(self):
        self._write(external_lane.ARTIFACTS['vision'],
                    {'route': 'github_actions_runner', 'frames': [{'caption': 'dark'}]})
        report = external_lane.capability_report(self.base)
        self.assertEqual(report['vision']['status'], 'green')

    def test_runner_error_is_reported_as_failure_not_success(self):
        self._write(external_lane.ARTIFACTS['audio'],
                    {'route': 'github_actions_runner',
                     'error': 'OSError: model download blocked'})
        report = external_lane.capability_report(self.base)
        self.assertEqual(report['audio']['status'], 'ran_but_failed')
        self.assertIn('blocked', report['audio']['error'])

    def test_unreadable_artifact_is_not_green(self):
        path = self.base / external_lane.ARTIFACTS['durable']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{not json', encoding='utf-8')
        report = external_lane.capability_report(self.base)
        self.assertEqual(report['durable']['status'], 'unreadable')


class LaneProvenanceTests(unittest.TestCase):
    def test_provenance_states_the_requesting_agent_did_not_author_it(self):
        prov = external_lane.provenance({'route': 'github_actions_runner',
                                         'model': 'Qwen/Qwen2.5-0.5B-Instruct',
                                         'source_sha256': 'a' * 64})
        self.assertTrue(prov['authored_by_requesting_agent'] is False)
        self.assertEqual(prov['produced_by'], 'github_actions_runner')
        self.assertEqual(prov['model'], 'Qwen/Qwen2.5-0.5B-Instruct')

    def test_honest_limits_never_claim_human_review_or_taste(self):
        limits = ' '.join(external_lane.honest_limits()).lower()
        self.assertIn('no human viewed or listened', limits)
        self.assertIn('not artistic judgement', limits)
        self.assertIn('youtube and instagram still refuse', limits)


class LaneTriggerTests(unittest.TestCase):
    def test_dry_run_does_not_touch_git(self):
        with patch('subprocess.run') as run:
            result = external_lane.trigger('test', dry_run=True)
        run.assert_not_called()
        self.assertTrue(result['dry_run'])
        self.assertEqual(result['reason'], 'test')
        self.assertEqual(result['commands'][-1][-1], f'HEAD:{external_lane.BRANCH}')

    def test_failed_push_raises_instead_of_pretending_the_lane_woke(self):
        class Fail:
            returncode = 1
            stdout = ''
            stderr = 'remote rejected'

        with patch('subprocess.run', return_value=Fail()):
            with self.assertRaises(RuntimeError) as ctx:
                external_lane.trigger('test')
        self.assertIn('remote rejected', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()


class DurableStoreTests(unittest.TestCase):
    """Durability is the easiest thing to fake, so it gets the strictest rules."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def _write(self, rel, payload):
        path = self.base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding='utf-8')

    def _upload(self, **over):
        payload = {'route': 'github_release', 'tag': 'accounts-durable-store',
                   'local_sha256': 'a' * 64, 'restored_sha256': 'a' * 64,
                   'verified_roundtrip': True}
        payload.update(over)
        self._write(external_lane.ARTIFACTS['durable'], payload)

    def _fresh(self, **over):
        payload = {'route': 'github_actions_runner',
                   'purpose': 'independent durability verification on a fresh runner',
                   'fetched_sha256': 'a' * 64, 'fetched_bytes': 10,
                   'matches_original_sha256': True}
        payload.update(over)
        self._write('durable/fresh_machine_verify.json', payload)

    def test_upload_alone_is_not_enough_to_be_green(self):
        self._upload()
        report = external_lane.capability_report(self.base)
        self.assertEqual(report['durable']['status'], 'unverified')
        self.assertIn('fresh-machine', report['durable']['reason'])

    def test_upload_plus_fresh_refetch_is_green(self):
        self._upload()
        self._fresh()
        report = external_lane.capability_report(self.base)
        self.assertEqual(report['durable']['status'], 'green')
        self.assertTrue(report['durable']['fresh_machine_verified'])
        self.assertEqual(report['durable']['fetched_bytes'], 10)

    def test_hash_mismatch_on_upload_is_a_failure(self):
        self._upload(restored_sha256='b' * 64, verified_roundtrip=False)
        self._fresh()
        report = external_lane.capability_report(self.base)
        self.assertEqual(report['durable']['status'], 'ran_but_failed')
        self.assertIn('hash mismatch', report['durable']['error'])

    def test_fresh_machine_seeing_different_bytes_is_not_green(self):
        self._upload()
        self._fresh(matches_original_sha256=False)
        report = external_lane.capability_report(self.base)
        self.assertEqual(report['durable']['status'], 'unverified')
        self.assertIn('different bytes', report['durable']['reason'])

    def test_unreadable_fresh_evidence_is_not_green(self):
        self._upload()
        bad = self.base / 'durable/fresh_machine_verify.json'
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text('<html>404</html>', encoding='utf-8')
        report = external_lane.capability_report(self.base)
        self.assertEqual(report['durable']['status'], 'unverified')


class RunnerRouteTests(unittest.TestCase):
    def test_only_runner_routes_count_as_provenance(self):
        self.assertIn('github_actions_runner', external_lane.RUNNER_ROUTES)
        self.assertIn('github_release', external_lane.RUNNER_ROUTES)
        self.assertNotIn('local_sandbox', external_lane.RUNNER_ROUTES)

    def test_a_local_route_cannot_claim_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for kind, rel in external_lane.ARTIFACTS.items():
                path = base / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({'route': 'local_sandbox'}), encoding='utf-8')
            report = external_lane.capability_report(base)
            self.assertEqual({e['status'] for e in report.values()}, {'unverified'})
