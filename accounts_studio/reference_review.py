"""Independent review vehicles that actually exist in this workspace.

Two real routes, both with honest limits:

1. `subprocess` — a separate OS process with its own argv/env/stdin, given only
   the artifact bytes and the acceptance criteria. It has no access to the
   authoring conversation, so it is genuinely a different execution context.
   It is NOT a different language model: independence is of context, not of
   judgement.

2. `github_actions` — a fresh ephemeral runner executing a committed review
   script against the exact artifact hash. Different machine, different
   process tree, no shared memory with the author. This is the strongest
   independence available here, and its output is public/auditable.

Neither route may be described as an independent *human* or independent
*creative* review. Both produce mechanical/structural findings only.
"""
import hashlib,json,os,subprocess,sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / 'accounts_studio' / 'review_probe.py'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def subprocess_review(artifact, criteria, executor_id='reviewer-subprocess-v1'):
    """Run the probe as a separate process: real distinct execution context."""
    artifact = Path(artifact).resolve()
    if not artifact.is_file() or not artifact.stat().st_size:
        raise ValueError('artifact missing or empty')
    proc = subprocess.run(
        [sys.executable, str(PROBE), str(artifact), json.dumps(criteria)],
        capture_output=True, text=True, timeout=300,
        cwd='/tmp',                    # deliberately NOT the repo working dir
        env={'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
             'PYTHONPATH': '/tmp/pydeps', 'HOME': '/tmp'},
        stdin=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        raise RuntimeError('reviewer subprocess failed: ' + proc.stderr[-800:])
    result = json.loads(proc.stdout)
    expected = sha256(artifact)
    if result.get('sha256') != expected:
        raise ValueError('reviewer inspected different bytes')
    result['binding'] = {'artifact_sha256': expected, 'verified': True}
    result['independence'] = {
        'kind': 'separate_process_context',
        'different_cwd': True, 'different_env': True, 'stdin_closed': True,
        'shared_memory_with_author': False,
        'different_language_model': False,
        'limit': 'mechanical checks only; not a creative or human review',
    }
    return result


def github_review(artifact, criteria, repo='adil-chandio/Top1',
                  workflow='accounts-review.yml'):
    """Dispatch the ephemeral-runner review workflow for this exact artifact.

    The caller must pass the artifact into the workflow (via a committed
    manifest) and then read back the run output. This function only prepares
    the request; it never fabricates the runner's answer.
    """
    artifact = Path(artifact).resolve()
    request = {
        'artifact_name': artifact.name,
        'artifact_sha256': sha256(artifact),
        'artifact_bytes': artifact.stat().st_size,
        'criteria': criteria,
        'workflow': workflow,
        'repo': repo,
        'instructions': [
            f'gh workflow run {workflow} --ref <branch> '
            f'-f sha={sha256(artifact)}',
            'read the run output and paste it back unmodified',
            'if the runner cannot obtain the artifact, record the failure; '
            'do not substitute a local check',
        ],
    }
    return request


def record(job_dir, vehicle, result):
    """Persist review evidence next to the job, never inside deliverables."""
    job_dir = Path(job_dir); job_dir.mkdir(parents=True, exist_ok=True)
    dest = job_dir / f'independent_review_{vehicle}_{result["binding"]["artifact_sha256"][:12]}.json'
    dest.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return dest
