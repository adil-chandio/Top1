#!/usr/bin/env python3
"""Recover this Short's inputs without building or overwriting other editions."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from shutil import copyfile
import sys
from urllib.parse import quote

from spec import CACHE, FIELDS, ROOT, HERE, digest
from materials import make

DEFAULT=ROOT/'deliverables/private-production-records/atlantic-tracks-short-01'
LOCK=json.loads((HERE/'inputs.json').read_text())


def ready(p,h):return p.is_file() and digest(p)==h


def prepare(originals: Path):
    for n,h in LOCK['private_vo_and_diffuse_detail'].items():
        dst=CACHE/n
        if ready(dst,h):continue
        source=originals/n
        if not ready(source,h):raise ValueError(f'Missing or different approved original: {source}')
        dst.parent.mkdir(parents=True,exist_ok=True);copyfile(source,dst)
    make(CACHE/'materials')
    sys.path.insert(0,str(HERE.parent/'step-6'))
    from assets import FONTS, download
    import assets
    from sound_v2 import sources
    # GEO8 files are immutable inputs from the data build. Build in a temporary
    # sibling directory so the established Cinema fields are never overwritten.
    stage4=json.loads((HERE.parent/'step-4/asset-lock.json').read_text())
    for f in stage4['fonts']:
        download(FONTS/f['file'],stage4['font_source'],stage4['font_ref'],quote(f['path']),f['sha256'])
        download(FONTS/(Path(f['file']).stem+'-OFL.txt'),stage4['font_source'],stage4['font_ref'],f['license_path'])
    files=LOCK['geo8_and_world'];bad=[n for n,h in files.items() if not ready(FIELDS/n,h)]
    if bad:
        from tempfile import TemporaryDirectory
        assets.fetch();assets.base.material=assets.material;FIELDS.mkdir(parents=True,exist_ok=True)
        with TemporaryDirectory(prefix='atl-short-geo-',dir=CACHE) as d:
            assets.base.PACK=Path(d)
            if any(n in bad for n in ('modern.field','ancient.field','world.json')):assets.base.build_globes()
            for n in ('brazil','koum'):
                if n+'.field' in bad:assets.pilot.macro_v2(n)
            for n in bad:
                p=Path(d)/n
                if not ready(p,files[n]):raise ValueError(f'Field checksum changed: supply locked {n}')
                if (FIELDS/n).exists():raise ValueError(f'Existing field changed; keep separate: {FIELDS/n}')
                p.replace(FIELDS/n)
    print('ATLANTIC_SHORT_INPUTS_READY',len(files),len(sources()),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--originals',type=Path,default=DEFAULT);args=p.parse_args();prepare(args.originals)
