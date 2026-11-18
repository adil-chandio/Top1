#!/usr/bin/env python3
"""Capture target thumbnails from YouTube CDN; never substitutes a proxy.

Run in an environment that can reach i.ytimg.com. Downloads are staged and
validated before replacing local files. A successful capture still needs human
visual review and packaging reconciliation before the research gate changes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.error
import urllib.request

TARGETS = {
    'jU3nOWkZCCQ': 'https://i.ytimg.com/vi/jU3nOWkZCCQ/default.jpg',
    'LjC0BgCMjG0': 'https://i.ytimg.com/vi/LjC0BgCMjG0/default.jpg',
}
MAX_BYTES = 2_000_000


def capture(url, target, timeout=15, skip_decoder=False):
    request = urllib.request.Request(url, headers={'User-Agent': 'MonarchCamThumbnailVerification/1.0'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.geturl() != url:
            raise ValueError('Unexpected redirect; refusing unverified source')
        if response.headers.get_content_type() != 'image/jpeg':
            raise ValueError('Response is not image/jpeg')
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES or not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'):
        raise ValueError('Invalid, incomplete, or oversized JPEG')
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix='.jpg', delete=False) as f:
            temp = Path(f.name)
            f.write(data)
        if not skip_decoder:
            proc = subprocess.run(['identify', '-regard-warnings', str(temp)], capture_output=True, text=True)
            if proc.returncode:
                raise ValueError('JPEG decoder rejected image: ' + proc.stderr.strip())
        os.replace(temp, target)
        temp = None
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
    return {'url': url, 'path': str(target), 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'decoder_checked': not skip_decoder, 'visual_review': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('thumbnail-captures'))
    parser.add_argument('--skip-decoder', action='store_true', help='Capture only; decoder check is required separately before use')
    args = parser.parse_args()
    results = {}
    for video_id, url in TARGETS.items():
        try:
            results[video_id] = capture(url, args.output / (video_id + '-default.jpg'), skip_decoder=args.skip_decoder)
        except (OSError, ValueError, urllib.error.URLError) as exc:
            results[video_id] = {'url': url, 'error': str(exc), 'visual_review': False}
    print(json.dumps(results, indent=2))
    return int(any('error' in result for result in results.values()))


if __name__ == '__main__':
    raise SystemExit(main())
