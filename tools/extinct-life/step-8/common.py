"""Separate render and delivery roots; the preceding cuts are read-only inputs."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STAGE = HERE.parent
sys.path[:0] = [str(HERE), str(STAGE/'step-7'), str(STAGE/'step-6')]
from assets import HOME, FIELDS, SRT, VO, base, media_lock
from cut import BY, F, FPS, N, S, SPF, SR
from motion import FF

CACHE = HOME/'cinema-master'
QA = CACHE/'qa'
REF = CACHE/'inputs'/'Extinct-Life-Atlantic-Tracks-Investigation-Cut.mp4'
OUT = base.ROOT/'deliverables/extinct-life-step-8'
NAME = 'Atlantic-Tracks-Cinema-Edition'
MASTER = OUT/(NAME+'.mp4')
PREVIOUS = STAGE/'step-7'/'investigation-receipt.json'


def sha(p):
    return base.hashfile(p)


def signature(paths):
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode()+b'\0'+bytes.fromhex(sha(path)))
    return digest.hexdigest()


def save_json(path, data):
    path.parent.mkdir(exist_ok=True, parents=True)
    tmp = path.with_suffix(path.suffix+'.pending')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    tmp.replace(path)


def reference():
    r = json.loads(PREVIOUS.read_text())
    archive = r['files'][0]
    if not REF.is_file() or REF.stat().st_size != archive['bytes'] or sha(REF) != archive['sha256']:
        raise ValueError(f'Missing or changed Investigation Cut: {REF}')
    return r
