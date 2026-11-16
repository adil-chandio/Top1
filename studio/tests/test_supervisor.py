import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from studio.supervisor import preflight, run


class SupervisorTests(unittest.TestCase):
    def test_missing_infrastructure_not_ready(self):
        self.assertFalse(preflight({})['ready_for_attempt'])

    def test_session_mailboxes_are_not_autonomous_workers(self):
        report = preflight({'STUDIO_WORKER_COMMAND': 'arena-session-worker',
                            'STUDIO_REVIEWER_COMMAND': 'arena-session-reviewer'})
        self.assertFalse(report['checks']['worker_unattended_transport'])
        self.assertFalse(report['checks']['reviewer_unattended_transport'])

    def test_blocked_preflight_does_not_tick_or_change_job(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ', {}, clear=True), patch('studio.supervisor.tick') as tick:
            result = run(tmp)
            self.assertEqual(result['status'], 'blocked_infrastructure')
            tick.assert_not_called()
            self.assertEqual(json.loads((Path(tmp)/'supervisor_status.json').read_text())['ticks'], 0)

    def test_queued_stages_continue_without_user_go_ahead(self):
        with tempfile.TemporaryDirectory() as tmp, patch('studio.supervisor.preflight', return_value={'ready_for_attempt': True}), patch('studio.supervisor.select_job', return_value=Path(tmp)/'job'), patch('studio.supervisor.tick', side_effect=['queued', 'awaiting_user_evaluation']) as tick, patch('studio.supervisor.time.sleep'):
            result = run(tmp, max_ticks=4)
            self.assertEqual(result['status'], 'awaiting_user_evaluation')
            self.assertEqual(tick.call_count, 2)

    def test_pending_reviewer_not_polled_as_if_working(self):
        with tempfile.TemporaryDirectory() as tmp, patch('studio.supervisor.preflight', return_value={'ready_for_attempt': True}), patch('studio.supervisor.select_job', return_value=Path(tmp)/'job'), patch('studio.supervisor.tick', return_value='awaiting_reviewer') as tick:
            self.assertEqual(run(tmp)['status'], 'awaiting_reviewer')
            self.assertEqual(tick.call_count, 1)

    def test_invalid_budget_rejected(self):
        with self.assertRaises(ValueError):
            run('/unused', max_ticks=0)
