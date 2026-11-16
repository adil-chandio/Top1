"""Bounded acquisition of one attributed CC BY reference; not a hero-rig approval."""
import base64
import hashlib
import json
import os
import urllib.request

URL = 'https://upload.wikimedia.org/wikipedia/commons/5/5e/Alpheus_heterochaelis_%28I0651%29_%2813048410675%29.jpg'
LIMIT = 2_000_000

def acquire():
    req = urllib.request.Request(URL, headers={'User-Agent': 'MonarchCamAnatomyResearch/1.0 (bounded CC BY source inspection)'})
    with urllib.request.urlopen(req, timeout=45) as response:
        data = response.read(LIMIT + 1)
    if len(data) > LIMIT or not data.startswith(b'\xff\xd8'):
        raise ValueError('Not a bounded JPEG')
    return data

def main():
    data = acquire()
    receipt = {'url': URL, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
               'credit': 'Robert Aguilar / Smithsonian Environmental Research Center',
               'license': 'CC BY 2.0', 'visual_inspection': False}
    encoded = base64.b64encode(data).decode()
    chunks = [encoded[i:i+48000] for i in range(0, len(encoded), 48000)]
    for i, chunk in enumerate(chunks):
        body = {'name': f'species-photo-{i:02d}', 'head_sha': os.environ['GITHUB_SHA'],
                'status': 'completed', 'conclusion': 'success',
                'output': {'title': 'Bounded CC BY species reference', 'summary': json.dumps(receipt), 'text': chunk}}
        req = urllib.request.Request(f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/check-runs",
            data=json.dumps(body).encode(), headers={'Authorization': 'Bearer '+os.environ['GH_TOKEN'],
            'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as response:
            json.load(response)
    print(json.dumps(receipt))

if __name__ == '__main__':
    main()
