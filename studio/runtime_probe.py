"""Live challenge for configured unattended agents, not a creative/QC acceptance.
Commands are trusted operator configuration. No key values appear in reports.
"""
import argparse
import hashlib
import json
import os
import secrets
import shlex
import tempfile
from pathlib import Path
from studio.pipeline import CONFIG, ROOT, NOW, save
from studio.processes import run_command
from studio.supervisor import preflight


def validate_response(data, challenge, role):
    if data.get('challenge') != challenge or data.get('role') != role:
        raise ValueError('live challenge/role mismatch')
    if data.get('paid_spend') is not False:
        raise ValueError('no-paid-spend attestation required')
    identity = data.get('executor', {})
    if not isinstance(identity.get('id'), str) or not identity['id'].strip():
        raise ValueError('executor identity missing')
    if identity.get('unattended') is not True:
        raise ValueError('runtime is not unattended')
    capabilities = data.get('capabilities', {})
    for capability in ('research_tools', 'file_tools', 'execute_tools', 'moving_picture', 'audio_listening'):
        if capabilities.get(capability) is not True:
            raise ValueError('missing required capability: ' + capability)
    if role == 'reviewer' and identity.get('independent_context') is not True:
        raise ValueError('independent reviewer context required')
    # Values are worker attestations. A full media pilot is still required.
    return {'executor_id': identity['id'], 'capabilities': capabilities,
            'response_sha256': hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()}


def probe(output):
    report = {'checked_at': NOW().isoformat(), 'preflight': preflight(),
              'status': 'blocked_infrastructure', 'live_roles': {},
              'creative_pilot_passed': False, 'production_activated': False}
    if report['preflight']['ready_for_attempt']:
        report['status'] = 'probing'
        with tempfile.TemporaryDirectory(prefix='studio-probe-') as tmp:
            for role in ('worker', 'reviewer'):
                challenge = secrets.token_hex(24)
                request = Path(tmp) / (role + '-request.json')
                response = Path(tmp) / (role + '-response.json')
                save(request, {'operation': 'capability_probe', 'role': role,
                               'challenge': challenge, 'paid_spend_allowed': False,
                               'publishing_allowed': False, 'no_production_mutation': True,
                               'response_schema': 'studio/UNATTENDED_RUNTIME_CONTRACT.md'})
                try:
                    argv = shlex.split(os.environ[CONFIG[role + '_command_env']])
                    run_command(argv + ['--request', str(request), '--response', str(response)],
                                cwd=ROOT, timeout=60)
                    if not response.is_file() or response.stat().st_size > 65536:
                        raise ValueError('missing or oversized probe response')
                    report['live_roles'][role] = validate_response(json.loads(response.read_text()), challenge, role)
                except Exception as exc:
                    report['status'] = 'blocked_live_probe'
                    report['failure_type'] = type(exc).__name__
                    break
            else:
                ids = [v['executor_id'] for v in report['live_roles'].values()]
                report['status'] = 'needs_media_pilot' if len(set(ids)) == 2 else 'blocked_same_executor'
    save(output, report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'studio/runtime/live_probe.json')
    args = parser.parse_args()
    report = probe(args.output)
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'needs_media_pilot' else 2

if __name__ == '__main__':
    raise SystemExit(main())
