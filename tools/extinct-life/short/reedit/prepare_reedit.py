#!/usr/bin/env python3
"""Restore the original Short's pinned input set and the V2 typeface."""
from __future__ import annotations
import argparse
from pathlib import Path

# Import pins and paths without importing the renderer or starting an encode.
from clock import ROOT, digest
from prepare import DEFAULT, prepare

REF='5bd87dfc525c8a0d1d8529d3684716e00c3fc59a'
DIRECTORY=ROOT/'.cache/atlantic-cover/fonts'
LOCK=(('SpaceGrotesk.ttf','SpaceGrotesk%5Bwght%5D.ttf','acad6de1fc93436f5c0f1f4137751ef04f1aea3063e7036535970ffcfbd79f72'),
      ('SpaceGrotesk-OFL.txt','OFL.txt','564ce565c371c5e5bbf286006565a7c9aa55a9f56e7ca58d56e05d649dd61a72'))


def setup(originals):
    prepare(originals)
    from assets import download
    for file,path,h in LOCK:
        p=DIRECTORY/file;download(p,'google/fonts',REF,f'ofl/spacegrotesk/{path}',h);assert digest(p)==h
    print('RECUT_SOURCE_INPUTS_READY',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--originals',type=Path,default=DEFAULT);setup(p.parse_args().originals)
