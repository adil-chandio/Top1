import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from studio.processes import run_command
from studio.runtime_probe import probe, validate_response


class RuntimeProbeTests(unittest.TestCase):
    def response(self):
        return {'challenge': 'nonce', 'role': 'reviewer', 'paid_spend': False,
                'executor': {'id': 'test-reviewer', 'unattended': True, 'independent_context': True},
                'capabilities': {k: True for k in ('research_tools', 'file_tools', 'execute_tools', 'moving_picture', 'audio_listening')}}

    def test_valid_live_contract_not_creative_acceptance(self):
        self.assertEqual(validate_response(self.response(), 'nonce', 'reviewer')['executor_id'], 'test-reviewer')

    def test_stale_nonce_rejected(self):
        with self.assertRaises(ValueError):
            validate_response(self.response(), 'new', 'reviewer')

    def test_text_only_reviewer_rejected(self):
        data = self.response(); data['capabilities']['audio_listening'] = False
        with self.assertRaises(ValueError):
            validate_response(data, 'nonce', 'reviewer')

    def test_same_context_rejected(self):
        data = self.response(); data['executor']['independent_context'] = False
        with self.assertRaises(ValueError):
            validate_response(data, 'nonce', 'reviewer')

    def test_missing_infra_does_not_launch_command(self):
        with tempfile.TemporaryDirectory() as tmp, patch('studio.runtime_probe.preflight', return_value={'ready_for_attempt': False}), patch('studio.runtime_probe.run_command') as command:
            report = probe(Path(tmp)/'report.json')
            command.assert_not_called()
            self.assertFalse(report['production_activated'])

    def test_actual_command_success_and_nonzero(self):
        run_command([sys.executable, '-c', 'pass'], cwd='.', timeout=5)
        with self.assertRaises(subprocess.CalledProcessError):
            run_command([sys.executable, '-c', 'raise SystemExit(3)'], cwd='.', timeout=5)

    def test_actual_timeout(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            run_command([sys.executable, '-c', 'import time; time.sleep(60)'], cwd='.', timeout=.1)
