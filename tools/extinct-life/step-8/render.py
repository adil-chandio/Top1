#!/usr/bin/env python3
"""Render all 66 shot slots on the picture lock, then grade and encode each slot."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time

from PIL import Image

from common import CACHE, QA, F, FIELDS, S, FPS, HERE, STAGE, FF, BY, signature, sha, save_json
from cut import header, shot_of
from cues import native_marks
from film_picture import encoder
from editorial import MAPS, compose

PARTS=CACHE/'parts'; BUILD=CACHE/'compiler'; NATIVE=(1152,648)
SCENIC=(4,7,28,29,35,40,52,60,64)
MACRO=(0,1,8,9,10,11,17,18,19,20,21,22,25,26,33,37,43,55,62,63)
CORE=tuple(k for k in range(len(S)) if k not in MAPS)
ALL=tuple(range(len(S)))


def deps(maps=False):
    names=[*sorted((STAGE/'step-6').glob('*.hpp')),*sorted((STAGE/'step-7').glob('*.hpp')),
        STAGE/'step-5/cinema-v2/render_cinema.cpp', STAGE/'step-6/cut.py',STAGE/'step-6/film_picture.py',
        STAGE/'step-7/graphics.py', STAGE/'step-5/cinema-v2/cues.py',STAGE/'step-5/cinema-v2/motion.py',
        FIELDS/'manifest.json',HERE/'render_cinema.cpp', HERE/'look.hpp',HERE/'globe.hpp',HERE/'editorial.py',HERE/'render.py']
    if not maps:names+=sorted(p for p in HERE.glob('*.hpp') if p.name not in ('look.hpp','globe.hpp'))
    # cues.py may live in the original opening root; resolve the actual import.
    import cues
    names=[p for p in names if p.name!='cues.py']+[Path(cues.__file__)]
    return names


def build(maps=False):
    BUILD.mkdir(exist_ok=True,parents=True)
    marks=BUILD/'marks.hpp';ts=BUILD/'timeline.hpp'
    text=['#pragma once']
    for k,v in native_marks().items():text.append('constexpr int '+k+('[]={'+','.join(map(str,v))+'};' if isinstance(v,tuple) else '='+str(v)+';'))
    marks.write_text('\n'.join(text)+'\n');ts.write_text(header())
    target=BUILD/('globe' if maps else 'cinema')
    sig=signature(deps(maps)+[marks,ts]);tag=target.with_suffix('.sig')
    if target.is_file() and tag.is_file() and tag.read_text()==sig:return target,sig
    tmp=target.with_suffix('.working')
    cmd=['g++','-std=c++17','-O3','-march=native','-ffast-math','-fopenmp','-Wall','-Wextra','-Werror',
         *( ['-DATL_MAP_ONLY'] if maps else [] ),'-I',str(BUILD),str(HERE/'render_cinema.cpp'),'-o',str(tmp)]
    subprocess.run(cmd,check=True);tmp.replace(target);tag.write_text(sig)
    print('CINEMA_RENDERER_READY','globe' if maps else 'full',sig,flush=True)
    return target,sig


def marks(line,f):
    val=line.strip().split(',');k=shot_of(f)
    if len(val)!=38 or (int(val[0]),int(val[1]))!=(f,k):raise ValueError((f,line))
    a=list(map(float,val[2:])); return [(1920*a[j],1080*a[j+1],a[j+2]) for j in range(0,36,3)]


def native(program, size, frames, trace):
    return [str(program),str(FIELDS),*map(str,size),*map(str,frames),str(trace)]


def part(k):return PARTS/f'{k:02d}.mp4'


def enc(k,size,p):
    cmd=encoder(size,k,p);cmd[cmd.index('-preset')+1]='veryfast'
    # The same compression profile for every reel; more bits for moving water,
    # texture and skin. All output is 1080p24 with a shared Rec.709 container.
    rate=1100 if k in MAPS else 1775 if k in SCENIC else 1630 if k in MACRO else 1370
    if k in (42,45,65):rate=950
    for opt,n in (('-b:v',rate),('-maxrate',round(rate*1.48)),('-bufsize',round(rate*1.8))):cmd[cmd.index(opt)+1]=f'{n}k'
    return cmd


def sizefor(k):
    # Ground insets are all rendered on the same 16:9 native raster within a slot.
    return (1152,648) if k in MAPS or k in (0,1,18,43,62,65) else (960,540)


def staged(k,sig):
    dst=part(k);p=dst.with_suffix('.json')
    if not (dst.is_file() and p.is_file()):return False
    m=json.loads(p.read_text());return (m['signature'],m['frames'],m['bytes'],m['sha256'])==(sig,F[k+1]-F[k],dst.stat().st_size,sha(dst))


def render_group(keys,maps=False):
    program,sig=build(maps);PARTS.mkdir(exist_ok=True,parents=True);QA.mkdir(exist_ok=True,parents=True)
    need=[k for k in keys if not staged(k,sig)]
    print('SHOT_QUEUE',len(need),len(keys),'maps' if maps else 'picture',flush=True)
    for k in need:
        lo,hi=F[k:k+2];size=sizefor(k);w,h=size;stride=w*h*3
        dst=part(k);tmp=dst.with_suffix('.partial.mp4');trace=PARTS/f'{k:02d}.partial.csv';start=time.monotonic()
        want={lo+2,(lo+hi)//2,hi-3}|{max(lo,min(hi-1,v.f+6)) for v in BY.values() if lo<=v.f<hi}
        try:
            with subprocess.Popen(native(program,size,(lo,hi),trace),stdout=subprocess.PIPE) as source,subprocess.Popen(enc(k,size,tmp),stdin=subprocess.PIPE) as out:
                with trace_reader(source,trace) as proj:
                    for f in range(lo,hi):
                        raw=source.stdout.read(stride)
                        if len(raw)!=stride:raise RuntimeError(f'Incomplete native output at {f}')
                        tr=marks(proj.readline(),f)
                        im=compose(Image.frombytes('RGB',size,raw),k,f,tr)
                        if f in want:im.save(QA/f'frame-{f:05}.jpg',quality=94,subsampling=0)
                        out.stdin.write(im.tobytes())
                out.stdin.close();ret0=source.wait();ret1=out.wait()
                if ret0 or ret1:raise RuntimeError(f'Shot {k}: renderer {ret0}, encoder {ret1}')
            tmp.replace(dst);trace.replace(trace.with_name(f'{k:02d}.csv'))
            record={'shot':k,'key':S[k].key,'from_frame':lo,'to_frame_exclusive':hi,'frames':hi-lo,
                    'native':list(size),'bytes':dst.stat().st_size,'sha256':sha(dst),'signature':sig}
            save_json(dst.with_suffix('.json'),record)
            print(f"PICTURE {k:02} {S[k].key}  {hi-lo} frames  {time.monotonic()-start:.2f}s  {record['bytes']:,} B",flush=True)
        except BaseException:
            tmp.unlink(missing_ok=True);raise
    print('PICTURE_GROUP_READY',len(keys),flush=True)


class trace_reader:
    def __init__(self,child,path):self.child=child;self.path=path
    def __enter__(self):
        start=time.monotonic()
        while not self.path.is_file():
            if self.child.poll() is not None or time.monotonic()-start>45:raise RuntimeError('Renderer did not open its trace')
            time.sleep(.03)
        self.fd=self.path.open();return self.fd
    def __exit__(self,*_):self.fd.close()


def probes(frames,maps=False,size=NATIVE):
    prog,_=build(maps);QA.mkdir(exist_ok=True,parents=True);trace=QA/('sample-map.csv' if maps else 'sample-picture.csv')
    req=trace.with_suffix('.txt');req.write_text('\n'.join(map(str,frames))+'\n');w,h=size
    p=subprocess.run(native(prog,size,('--samples',req),trace),stdout=subprocess.PIPE,check=True,timeout=300)
    buf=p.stdout;stride=w*h*3
    if len(buf)!=len(frames)*stride:raise RuntimeError('Incomplete sample render')
    with trace.open() as q:
        for j,f in enumerate(frames):
            im=Image.frombytes('RGB',size,buf[j*stride:(j+1)*stride]);t=marks(q.readline(),f)
            compose(im,shot_of(f),f,t).save(QA/f'sample-{f:05}.jpg',quality=94,subsampling=0)
    print('INTERNAL_SAMPLES_READY',len(frames),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--group',choices=('maps','picture','all'),default='all');a.add_argument('--samples',nargs='+',type=int);a.add_argument('--shots',nargs='+',type=int,choices=ALL)
    args=a.parse_args()
    if args.samples:probes(sorted(set(args.samples)),args.group=='maps')
    else:
        for group,m in ((MAPS,True),(CORE,False)):
            if args.group==('picture' if m else 'maps'):continue
            selected=tuple(k for k in group if not args.shots or k in args.shots)
            if selected:render_group(selected,m)
