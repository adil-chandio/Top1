"""Standalone review probe. Runs in its own process with its own cwd/env.

Receives ONLY an artifact path and acceptance criteria on argv. It has no
access to the authoring conversation, brief, or reasoning. It performs real
mechanical checks and reports them honestly, including what it cannot judge.

Exit code 0 always when the artifact is readable; findings carry the verdict.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

MEDIA_VIDEO = {'.mp4', '.mov', '.mkv', '.webm'}
MEDIA_IMAGE = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
MEDIA_AUDIO = {'.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus'}


def ffmpeg():
    import os
    for extra in ('/tmp/pydeps',):
        if extra not in sys.path:
            sys.path.insert(0, extra)
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def probe_media(path):
    exe = ffmpeg()
    if not exe:
        return {'error': 'no ffmpeg available in reviewer context'}
    out = subprocess.run([exe, '-hide_banner', '-i', str(path)],
                         capture_output=True, text=True)
    found = {'duration': None, 'streams': []}
    for line in out.stderr.splitlines():
        line = line.strip()
        if line.startswith('Duration:'):
            found['duration'] = line.split('Duration:')[1].split(',')[0].strip()
        elif line.startswith('Stream #'):
            found['streams'].append(line)
    return found


def main():
    artifact = Path(sys.argv[1])
    criteria = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    findings, defects = [], []

    if not artifact.is_file():
        defects.append('artifact does not exist')
        exists = False
        digest = None
        size = 0
    else:
        data = artifact.read_bytes()
        exists, size = True, len(data)
        digest = hashlib.sha256(data).hexdigest()
        findings.append(f'artifact exists, {size} bytes, sha256 {digest[:16]}...')
        if size == 0:
            defects.append('artifact is empty')

    suffix = artifact.suffix.lower()
    media = None
    if exists and size and suffix in MEDIA_VIDEO | MEDIA_AUDIO | MEDIA_IMAGE:
        media = probe_media(artifact)
        if media.get('error'):
            defects.append(media['error'])
        else:
            if media.get('duration'):
                findings.append('container duration ' + media['duration'])
            for stream in media.get('streams', []):
                findings.append(stream)
            if suffix in MEDIA_VIDEO:
                if not any('Video:' in s for s in media.get('streams', [])):
                    defects.append('video container has no video stream')
                if not any('Audio:' in s for s in media.get('streams', [])):
                    findings.append('no audio stream present')
    elif exists:
        findings.append(f'non-media artifact type {suffix}; structural checks only')

    expected_sha = criteria.get('expected_sha256')
    if expected_sha:
        if digest != expected_sha:
            defects.append('artifact sha256 does not match the approved hash')
        else:
            findings.append('artifact hash matches the approved hash')

    result = {
        'executor': {
            'id': 'review-probe-v1',
            'capabilities': ['artifact_read', 'hash_verify', 'container_probe'],
            'cannot': ['creative_judgement', 'human_viewing', 'listening',
                       'factual_verification'],
        },
        'independent_context': True,
        'artifact': str(artifact),
        'sha256': digest,
        'bytes': size,
        'criteria_received': criteria,
        'findings': findings,
        'defects': defects,
        'verdict': 'pass' if not defects else 'fail',
        'scope_limit': ('Mechanical checks only. This reviewer did not view the '
                        'content creatively, did not listen to it, and cannot '
                        'verify claims. A pass here is not artistic approval.'),
    }
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
