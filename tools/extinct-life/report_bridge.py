#!/usr/bin/env python3
"""Prepare/collect a short-lived encrypted Actions artifact transfer over check annotations.

This is a workaround for environments that can reach GitHub's API but not its
artifact storage redirect. It never puts the private key or plaintext in Git.
"""
import argparse
import base64
import gzip
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / '.github/workflows/extinct-life-report-bridge.yml'
CACHE = ROOT / '.cache/extinct-life-report-bridge'
BRANCH = 'arena/6e66724e-top1'
REPO = 'adil-chandio/Top1'


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def gh_json(endpoint):
    return json.loads(run('gh', 'api', endpoint, capture_output=True, text=True).stdout)


def prepare(source_id):
    source = gh_json(f'repos/{REPO}/actions/runs/{source_id}')
    if source['head_branch'] != BRANCH or source['status'] != 'completed':
        raise ValueError('Source run must be a completed run on the research branch')
    artifacts = gh_json(f'repos/{REPO}/actions/runs/{source_id}/artifacts?per_page=100')['artifacts']
    if not any(a['name'] == 'extinct-life-research-report' and not a['expired'] for a in artifacts):
        raise ValueError('Unexpired research report artifact not found')
    folder = CACHE / str(source_id)
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    key, cert = folder / 'key.pem', folder / 'cert.pem'
    if key.exists() or cert.exists():
        raise ValueError('Transfer key already exists; keep it until its transfer is complete')
    run('openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-keyout', str(key),
        '-out', str(cert), '-nodes', '-days', '2', '-subj', '/CN=Extinct Life report transfer',
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    key.chmod(0o600)
    certificate = ''.join('          ' + line + '\n' for line in cert.read_text().splitlines())
    workflow = '''name: Extinct Life encrypted report bridge
on:
  push:
    branches: [arena/6e66724e-top1]
    paths: [.github/workflows/extinct-life-report-bridge.yml]
permissions:
  actions: read
  contents: read
jobs:
  transfer:
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    steps:
      - name: Download report from completed research run
        uses: actions/download-artifact@018cc2cf5baa6db3ef3c5f8a56943fffe632ef53 # v6
        with:
          name: extinct-life-research-report
          run-id: SOURCE_RUN_ID
          github-token: ${{ secrets.GITHUB_TOKEN }}
          path: /tmp/extinct-report
      - name: Encrypt report to temporary recipient and emit transport chunks
        shell: bash
        run: |
          set -euo pipefail
          cat > /tmp/recipient.pem <<'CERTIFICATE'
CERTIFICATE_BODY          CERTIFICATE
          test -f /tmp/extinct-report/REPORT.md
          gzip -n -c /tmp/extinct-report/REPORT.md > /tmp/report.md.gz
          openssl cms -encrypt -binary -aes256 -in /tmp/report.md.gz -outform DER -out /tmp/report.enc /tmp/recipient.pem
          python3 - <<'PYBRIDGE'
          import base64
          from pathlib import Path
          data = base64.b64encode(Path('/tmp/report.enc').read_bytes()).decode('ascii')
          chunks = [data[i:i+2500] for i in range(0, len(data), 2500)]
          if len(chunks) > 10:
              raise SystemExit('Encrypted report exceeds 10-annotation transfer limit; no report chunks emitted')
          for i, chunk in enumerate(chunks, 1):
              print(f'::notice title=ELREPORT-{i:02d}-OF-{len(chunks):02d}::{chunk}')
          PYBRIDGE
'''.replace('SOURCE_RUN_ID', str(source_id)).replace('CERTIFICATE_BODY', certificate)
    WORKFLOW.write_text(workflow)
    print(f'Prepared {WORKFLOW.relative_to(ROOT)} for source run {source_id}.')
    print('Commit and push ONLY the bridge workflow on the research branch; then collect the resulting bridge run.')
    print(f'Keep {key.relative_to(ROOT)} private and available until collection.')


def collect(source_id, bridge_id):
    bridge = gh_json(f'repos/{REPO}/actions/runs/{bridge_id}')
    if (bridge['head_branch'] != BRANCH or bridge['status'] != 'completed'
            or bridge['conclusion'] != 'success' or bridge['name'] != 'Extinct Life encrypted report bridge'):
        raise ValueError('Bridge run is not a successful transfer on the research branch')
    # Confirm the committed workflow targets this source, preventing accidental wrong-report retrieval.
    raw = run('gh', 'api', f'repos/{REPO}/contents/.github/workflows/extinct-life-report-bridge.yml?ref={bridge["head_sha"]}',
              capture_output=True, text=True).stdout
    committed = base64.b64decode(json.loads(raw)['content']).decode()
    if not re.search(r'^\s+run-id: ' + str(source_id) + r'\s*$', committed, re.M):
        raise ValueError('Bridge workflow targets a different source run')
    jobs = gh_json(f'repos/{REPO}/actions/runs/{bridge_id}/jobs?per_page=100')['jobs']
    selected = [j for j in jobs if j['name'] == 'transfer' and j['conclusion'] == 'success']
    if len(selected) != 1:
        raise ValueError('Expected exactly one successful transfer job')
    annotations = gh_json(f'repos/{REPO}/check-runs/{selected[0]["id"]}/annotations?per_page=100')
    chunks, count = {}, None
    for item in annotations:
        match = re.fullmatch(r'ELREPORT-(\d+)-OF-(\d+)', item.get('title') or '')
        if not match:
            continue
        index, total = map(int, match.groups())
        if count not in (None, total) or index in chunks or total > 10:
            raise ValueError('Conflicting encrypted chunks')
        chunks[index], count = item['message'], total
    if not count or set(chunks) != set(range(1, count + 1)):
        raise ValueError('Encrypted chunks are incomplete')
    folder = CACHE / str(source_id)
    key, cert = folder / 'key.pem', folder / 'cert.pem'
    encrypted, compressed, report = folder / 'report.enc', folder / 'report.md.gz', folder / 'REPORT.md'
    encrypted.write_bytes(base64.b64decode(''.join(chunks[i] for i in range(1, count + 1)), validate=True))
    run('openssl', 'cms', '-decrypt', '-binary', '-inform', 'DER', '-in', str(encrypted),
        '-recip', str(cert), '-inkey', str(key), '-out', str(compressed), stdout=subprocess.DEVNULL)
    report.write_bytes(gzip.decompress(compressed.read_bytes()))
    report.chmod(0o600)
    print(f'Retrieved {report.relative_to(ROOT)} ({report.stat().st_size} bytes).')
    print('Time-limited YouTube data: do not commit; delete/refresh under current policy.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('source_run', type=int)
    c = sub.add_parser('collect'); c.add_argument('source_run', type=int); c.add_argument('bridge_run', type=int)
    args = parser.parse_args()
    if args.source_run <= 0 or (args.command == 'collect' and args.bridge_run <= 0):
        parser.error('Run IDs must be positive integers')
    if args.command == 'prepare': prepare(args.source_run)
    else: collect(args.source_run, args.bridge_run)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'Bridge failed: {error}', file=sys.stderr)
        sys.exit(1)
