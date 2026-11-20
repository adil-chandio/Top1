#!/usr/bin/env python3
"""Render the Investigation Cut into its own cache; never rewrite the baseline."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

HERE=Path(__file__).resolve().parent
STAGE=HERE.parent/'step-6'
sys.path.insert(0,str(STAGE))
from assets import FIELDS, HOME, base
from cut import F, FPS, S, header, inside, shot_of
from film_picture import encoder

CACHE=HOME/'investigation'
PARTS=CACHE/'parts'; PROG=CACHE/'render-investigation'; QA=CACHE/'qa'
OUT=base.ROOT/'deliverables/extinct-life-step-7'
NATIVE=(960,540)
RETAINED=(7,8,9,10,11,25,26,28,29,35)
EDITED=tuple(k for k in range(len(S)) if k not in RETAINED)
MAPS=(2,3,5,34,46,48,51,53,57,59,61,62)
SCENIC=(4,40,52,64)


def build():
    from cues import native_marks
    CACHE.mkdir(exist_ok=True,parents=True)
    lines=['#pragma once']
    for k,v in native_marks().items():
        rhs='[]={'+','.join(map(str,v))+'};' if isinstance(v,tuple) else '='+str(v)+';'
        lines.append('constexpr int '+k+rhs)
    (CACHE/'marks.hpp').write_text('\n'.join(lines)+'\n');(CACHE/'timeline.hpp').write_text(header())
    tmp=PROG.with_suffix('.pending')
    subprocess.run(['g++','-std=c++17','-O3','-march=native','-fopenmp','-ffast-math','-Wall','-Wextra','-Werror',
        '-I',str(CACHE),str(HERE/'render_investigation.cpp'),'-o',str(tmp)],check=True)
    tmp.replace(PROG)
    print('INVESTIGATION_RENDERER_READY',flush=True)


def parse_mark(line,f):
    vals=line.strip().split(',');k=shot_of(f)
    if len(vals)!=38 or int(vals[0])!=f or int(vals[1])!=k:raise RuntimeError(f'Invalid native trace at {f}: {line!r}')
    x=list(map(float,vals[2:]))
    if not all(math.isfinite(y) for y in x):raise RuntimeError(f'Nonfinite projection at {f}: {line!r}')
    return k,[(x[j]*1920,x[j+1]*1080,x[j+2]) for j in range(0,36,3)]


def native(first,last,size,trace):
    return [str(PROG),str(FIELDS),*map(str,size),str(first),str(last),str(trace)]


def encode_cmd(k,size,path):
    cmd=encoder(size,k,path);cmd[cmd.index('-preset')+1]='veryfast'
    # Keep detail where the evidence moves and save bits on still cartography.
    rate=1060 if k in MAPS else 1960 if k in SCENIC else 1780 if k in (0,1,20,21,30,32,55,60,63) else 975 if k==65 else 1370
    for opt,num in (('-b:v',rate),('-maxrate',round(rate*1.35)),('-bufsize',round(rate*1.88))):cmd[cmd.index(opt)+1]=f'{num}k'
    return cmd


def part(k):
    return PARTS/f'{k:02d}.mp4' if k in EDITED else HOME/'picture'/f'{k:02d}.mp4'


def stamp():
    files=[*HERE.glob('*.hpp'),HERE/'render_investigation.cpp',HERE/'render.py',HERE/'graphics.py',PROG,
        STAGE/'cut.py',STAGE/'film_picture.py',HERE.parent/'step-5/cinema-v2/motion.py',FIELDS/'manifest.json']
    return hashlib.sha256(b''.join(hashlib.sha256(f.read_bytes()).digest() for f in sorted(files))).hexdigest()


def one(k,source,trace,key):
    from graphics import compose
    lo,hi=F[k:k+2];w,h=NATIVE;fix=part(k);tmp=fix.with_suffix('.pending.mp4');runtime=time.monotonic()
    want={lo,hi-1,(lo+hi)//2}|{max(lo,min(hi-1,x.f+7)) for x in inside(k)}
    try:
        with subprocess.Popen(encode_cmd(k,(w,h),tmp),stdin=subprocess.PIPE) as p:
            try:
                for f in range(lo,hi):
                    raw=source.read(w*h*3)
                    if len(raw)!=w*h*3:raise RuntimeError(f'Native output ended at frame {f}')
                    _,tr=parse_mark(trace.readline(),f)
                    image=compose(Image.frombytes('RGB',(w,h),raw),k,f,tr)
                    if f in want:image.save(QA/f'frame-{f:05d}.jpg',quality=95,subsampling=0)
                    p.stdin.write(image.tobytes())
                p.stdin.close()
                if p.wait()!=0:raise RuntimeError(f'Encode failed: {k}')
            except BaseException:
                p.terminate();raise
    except BaseException:
        tmp.unlink(missing_ok=True);raise
    tmp.replace(fix)
    meta={'from_frame':lo,'to_frame_exclusive':hi,'frames':hi-lo,'rev':key,'bytes':fix.stat().st_size,'sha256':base.hashfile(fix)}
    fix.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(f'PICTURE {k:02d} {S[k].key} · {hi-lo} frames in {time.monotonic()-runtime:.1f}s · {fix.stat().st_size:,} B',flush=True)


def concat(key):
    manifest=CACHE/'investigation.ffconcat';lines=['ffconcat version 1.0']
    for k in range(len(S)):
        p=part(k)
        if not p.is_file():return False
        if k in EDITED:
            j=p.with_suffix('.json')
            if not j.is_file() or json.loads(j.read_text())['rev']!=key:return False
        # Absolute paths avoid accidentally resolving to the separate picture cache.
        spec=str(p.resolve()).replace("'","'\\''")
        lines += [f"file '{spec}'",f'duration {(F[k+1]-F[k])/FPS:.12f}']
    manifest.write_text('\n'.join(lines)+'\n');print('INVESTIGATION_PICTURE_READY',manifest,flush=True)
    return True


def encode(first,last,redo,only=None):
    PARTS.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    sig=stamp()
    def available(k):
        p=part(k);r=p.with_suffix('.json')
        return p.is_file() and r.is_file() and json.loads(r.read_text())['rev']==sig and not redo
    frames=[];shots=[]
    for k in EDITED:
        if first<=k<=last and (only is None or k in only) and not available(k):
            shots.append(k);frames.extend(range(F[k],F[k+1]))
    if frames:
        spec=CACHE/f'shots-{first:02d}-{last:02d}.txt';spec.write_text('\n'.join(map(str,frames))+'\n')
        csv=QA/f'trace-{first:02d}-{last:02d}.csv'
        print('RENDER_START',len(shots),'shots',len(frames),'frames',flush=True)
        with csv.open('w+') as trace, subprocess.Popen(native('--samples',spec,NATIVE,csv),stdout=subprocess.PIPE) as p:
            try:
                for k in shots:one(k,p.stdout,trace,sig)
                if p.stdout.read(1) or p.wait()!=0:raise RuntimeError('Native frame count mismatch')
            except BaseException:
                p.terminate();raise
    if not concat(sig):print('Selected span complete; full cache is not yet ready.',flush=True)


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--compile',action='store_true');a.add_argument('--tools-only',action='store_true')
    a.add_argument('--from',dest='first',type=int,default=0);a.add_argument('--to',dest='last',type=int,default=len(S)-1);a.add_argument('--redo',action='store_true')
    a.add_argument('--only',nargs='+',type=int,choices=EDITED,metavar='SHOT');x=a.parse_args()
    if not 0<=x.first<=x.last<len(S):a.error('invalid inclusive shot range')
    if x.compile or not PROG.is_file():build()
    if not x.tools_only:encode(x.first,x.last,x.redo,x.only)


if __name__=='__main__':main()
