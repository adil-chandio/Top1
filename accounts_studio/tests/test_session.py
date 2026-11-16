"""Session transport tests.

The transport exists so a queued job can actually advance without pretending a
subprocess worker exists. Its whole safety value is that it loosens nothing:
a submission is only a result, never an approval, and the reviewer must be a
different executor with declared independent context.

These tests are ported from the three-channel system's suite, with the same
assertions, so the two systems cannot silently diverge in strictness.
"""
import datetime as dt
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from accounts_studio.pipeline import create, save
from accounts_studio.session import step, submit


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.job = create(self.base, 'soc_01', 'Session fixture only')

    def state(self):
        return json.loads((self.job / 'state.json').read_text(encoding='utf-8'))

    def candidate(self):
        p = self.job / 'fixture.txt'
        p.write_text('Test evidence, not actual research', encoding='utf-8')
        return {
            'status': 'complete',
            'paid_spend': False,
            'research': {
                'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                'question': 'Test?',
                'decision': 'Fixture decision',
                'sources': [{'url': 'https://example.org',
                             'finding': 'Synthetic fixture only'}],
            },
            'artifacts': [{'path': p.name,
                           'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}],
        }

    def worker(self):
        self.assertEqual(step(self.job), 'awaiting_worker')
        result = self.candidate()
        submit(self.job, result, 'test-author', ['synthetic-test-data'])
        self.assertEqual(step(self.job), 'awaiting_reviewer')
        return result

    def test_missing_runtime_replaced_by_real_pending_task(self):
        self.assertEqual(step(self.job), 'awaiting_worker')
        state = self.state()
        self.assertTrue(Path(state['pending_task']['request']).is_file())
        self.assertEqual(state['stage'], 0)

    def test_waiting_does_not_consume_retry_budget(self):
        for _ in range(5):
            step(self.job)
        state = self.state()
        self.assertEqual(state['attempts']['intelligence'], 1)
        self.assertEqual(state['revision_attempts']['intelligence'], 1)

    def test_distinct_review_advances(self):
        r = self.worker()
        submit(self.job, {
            'approved': True,
            'inspected_artifacts': [r['artifacts'][0]['sha256']],
            'findings': 'Synthetic fixture bytes checked'}, 'test-reviewer',
            ['byte-inspection'], True)
        self.assertEqual(step(self.job), 'queued')
        state = self.state()
        self.assertEqual(state['stage'], 1)
        self.assertNotIn('pending_task', state)
        self.assertIn('intelligence', state['accepted_reviews'])

    def test_same_executor_cannot_approve(self):
        self.worker()
        submit(self.job, {'approved': True}, 'test-author', ['test'], True)
        self.assertEqual(step(self.job), 'queued')
        self.assertEqual(self.state()['stage'], 0)
        self.assertIn('same executor', self.state()['blocker'])

    def test_no_independent_context_blocks(self):
        self.worker()
        submit(self.job, {'approved': True}, 'test-reviewer', ['test'])
        step(self.job)
        self.assertIn('independent context', self.state()['blocker'])

    def test_bad_artifact_not_accepted(self):
        step(self.job)
        r = self.candidate()
        r['artifacts'][0]['sha256'] = 'bad'
        submit(self.job, r, 'test-author', ['test'])
        step(self.job)
        self.assertEqual(self.state()['stage'], 0)
        self.assertIn('hash mismatch', self.state()['blocker'])

    def test_request_tamper_rejected(self):
        step(self.job)
        task = self.state()['pending_task']
        Path(task['request']).write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError):
            submit(self.job, self.candidate(), 'test-author', ['test'])

    def test_no_overwrite_of_submission(self):
        step(self.job)
        r = self.candidate()
        submit(self.job, r, 'test-author', ['test'])
        with self.assertRaises(ValueError):
            submit(self.job, r, 'test-author', ['test'])

    def test_submission_requires_declared_capability(self):
        step(self.job)
        with self.assertRaises(ValueError):
            submit(self.job, self.candidate(), 'test-author', [])

    def test_submit_without_pending_task_is_rejected(self):
        with self.assertRaises(ValueError):
            submit(self.job, self.candidate(), 'test-author', ['test'])

    def test_failing_review_new_attempt_folder(self):
        self.worker()
        submit(self.job, {'approved': False, 'findings': 'Need correction'},
               'test-reviewer', ['test'], True)
        step(self.job)
        step(self.job)
        self.assertTrue((self.job / 'intelligence-2/request.json').is_file())
        self.assertTrue((self.job / 'intelligence-1/result.json').is_file())

    def test_pending_task_never_claims_approval(self):
        """A parked task must not carry a verdict or approved flag."""
        step(self.job)
        task = self.state()['pending_task']
        self.assertEqual(set(task), {'role', 'request', 'response',
                                     'request_sha256'})
        self.assertEqual(task['role'], 'worker')


class AttachTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.job = create(self.tmp.name, 'soc_01', 'Attach fixture')

    def test_attach_refuses_job_that_already_ran(self):
        from accounts_studio.session import attach
        state = json.loads((self.job / 'state.json').read_text(encoding='utf-8'))
        state['stage'] = 2
        save(self.job / 'state.json', state)
        with self.assertRaises(ValueError):
            attach(self.job)

    def test_attach_refuses_already_bound_brief(self):
        from accounts_studio.session import attach
        state = json.loads((self.job / 'state.json').read_text(encoding='utf-8'))
        state['creative_brief_sha256'] = 'a' * 64
        save(self.job / 'state.json', state)
        with self.assertRaises(ValueError) as ctx:
            attach(self.job)
        self.assertIn('already bound', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
