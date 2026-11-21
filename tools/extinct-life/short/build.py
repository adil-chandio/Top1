#!/usr/bin/env python3
"""Stream genuine portrait renders through the editorial layers to H.264."""
from __future__ import annotations
import argparse
import contextlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from PIL import Image, ImageDraw
from mix import FF, MIX
from spec import CACHE, FIELDS, MATS, QA, HERE, OUT, FPS, W, H, FRAMES, NAME, TITLE, EVENTS, CUTS, digest, dump
from titles import Layout, FONTS

RENDER=CACHE/'bin/portrait'
STAGING=CACHE/'encode'
PROBES=(0,5,14,29,38,52,78,82,92,100,117,127,149,168,169,179,189,204,214,225,239,263,281,
         289,306,317,347,364,365,379,414,441,442,460,485,500,501,525,547,570,604,617,633,653,
         670,710,750,787,809,810,827,852,887,915,946,947,970,995,1018,1019)


def compile_scene():
    RENDER.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['g++','-std=c++17','-O3','-march=native','-fopenmp','-ffast-math','-Wall','-Wextra','-Werror',
                    str(HERE/'render.cpp'),'-o',str(RENDER)],check=True,timeout=45)


def fill_plan(frames,name):
    path=QA/f'{name}-frames.txt';path.write_text(''.join(f'{x}\n' for x in frames));return path


def audit_trace(records,full):
    d={int(n):v for n,*v in records}
    assert 0 in d and d[0][3]>d[5][3] and d[5][1]==0 and d[14][1]>.98, d[5]
    assert d[149][1]==1 and d[149][2]==0
    assert d[204][2]==0 and 0<d[214][2]<d[239][2]<.93
    assert .83<d[289][2]<d[317][2] and d[347][2]>.995
    assert d[1019][3]>d[0][3] and d[1019][3]-d[0][3]<.11
    if full:
        assert len(records)==FRAMES and sorted(d)==list(range(FRAMES))
        for a,b in ((CUTS[1],CUTS[2]),(CUTS[2],CUTS[3])):
            w=[v[1] for n,v in d.items() if a<=n<b];assert all(x<=y+1e-6 for x,y in zip(w,w[1:]))
        for k in ('hook','firm','soft'):
            n=EVENTS[k+'_impact'];assert d[n-1][3]>d[n][3]>d[n+1][3] and d[n][1]<=.0001<d[n+1][1]
    return dict(probes=len(d),original_frames=full,firm_final_slump=d[149][2],soft_first_slump=d[239][2],soft_final_slump=d[347][2],
                reverse_last_foot_height=d[1019][3],opening_foot_height=d[0][3])


def inputs():
    p=FIELDS/'world.json';m=json.loads(p.read_text());a=m['distance_km'];assert 6000<a['today']<6150 and 1100<a['past_model']<1250
    assert m['then_ma']==125 and m['then_age_is_not_a_footprint_date'] is True
    c=(HERE/'world.hpp').read_text(); start=c.index('static constexpr float p[2][2][2]='); end=c.index(';',start)
    k=[float(x) for x in re.findall(r'(-?\d+\.\d+)f',c[start:end])]
    assert all(abs(x-y)<1e-6 for x,y in zip(k,[q for kind in ('modern','past') for xy in m[kind] for q in xy],strict=True))
    return (p,[FIELDS/(n+'.field') for n in ('modern','ancient','brazil','koum')])


def encode_cmd(w,h):
    return [FF,'-hide_banner','-loglevel','warning','-nostdin','-y','-f','rawvideo','-pixel_format','rgb24',
            '-video_size',f'{w}x{h}','-framerate',str(FPS),'-i','pipe:0','-i',str(MIX/'program.wav'),'-map','0:v:0','-map','1:a:0',
            '-map_metadata','-1','-map_chapters','-1','-vf','scale=out_color_matrix=bt709:in_range=pc:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p',
            '-c:v','libx264','-profile:v','high','-level:v','4.1','-crf','16.75','-preset','medium','-tune','film','-maxrate','17700k','-bufsize','28100k',
            '-g','60','-keyint_min','16','-threads','2','-c:a','aac','-profile:a','aac_low','-ar','48000','-b:a','320k',
            '-color_range','tv','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-chroma_sample_location','left',
            '-metadata',f'title={TITLE}','-metadata:s:a:0','language=eng','-movflags','+faststart',str(STAGING/(NAME+'.pending.mp4'))]


def montage(p,items):
    for j in range(0,len(items),5):
        fs=items[j:j+5];canvas=Image.new('RGB',(216*len(fs),411),(12,22,27));d=ImageDraw.Draw(canvas)
        for i,n in enumerate(fs):
            with Image.open(p/f'f{n:04d}.jpg') as im:canvas.paste(im.resize((216,384),Image.Resampling.LANCZOS),(i*216,0))
            d.text((216*i+12,391),f'{n:04d} · {n/FPS:5.2f}s',fill=(234,232,221))
        canvas.save(p/f'sheet-{j//5:02d}.jpg',quality=93,subsampling=0)


def build(proof=False,compile=True):
    QA.mkdir(parents=True,exist_ok=True);STAGING.mkdir(parents=True,exist_ok=True)
    world,fields=inputs();clip=MIX/'program.wav';mix=json.loads((QA/'mix.json').read_text())
    assert digest(clip)==mix['sha256']
    if compile:compile_scene()
    size=(540,960) if proof else (W,H);w,h=size
    render_w,render_h=size if proof else (1152,2048);data=render_w*render_h*3
    frames=PROBES if proof else range(FRAMES)
    target=QA/('phone-proof' if proof else 'native-proof');target.mkdir(exist_ok=True)
    layout=Layout(size,mix['cues']);tag='proof' if proof else 'render'; trace=QA/f'{tag}-trace.csv'
    fmt=['--frames',str(fill_plan(frames,tag))] if proof else ['0',str(FRAMES)]
    prog=[str(RENDER),str(FIELDS),str(render_w),str(render_h),*fmt,str(trace),str(MATS)]
    t0=time.monotonic();k=-1;record=[]
    with contextlib.ExitStack() as stack:
        err=stack.enter_context((QA/f'{tag}-renderer.log').open('wb'))
        renderer=stack.enter_context(subprocess.Popen(prog,stdout=subprocess.PIPE,stderr=err,
                                    env={**os.environ,'OMP_NUM_THREADS':'2','OMP_DYNAMIC':'FALSE'}))
        writer=None
        if not proof:
            log=stack.enter_context((QA/'encode.log').open('wb'))
            writer=stack.enter_context(subprocess.Popen(encode_cmd(w,h),stdin=subprocess.PIPE,stderr=log))
        try:
            for n in frames:
                raw=renderer.stdout.read(data)
                if len(raw)!=data:raise RuntimeError(f'short RGB frame {n}: {len(raw)} bytes; {err.name}')
                if k<0:src=stack.enter_context(trace.open());k=0
                row=tuple(float(x) for x in src.readline().rstrip().split(','));assert len(row)==17 and row[0]==n,row
                record.append(row)
                im=Image.frombytes('RGB',(render_w,render_h),raw)
                if not proof:im=im.resize(size,Image.Resampling.LANCZOS)
                im=layout.paint(im,n,row[1:])
                if writer:writer.stdin.write(im.tobytes())
                if n in PROBES:
                    im.save(target/f'f{n:04d}.jpg',quality=94,subsampling=0)
                if n in CUTS[:-1] or n%120==0:print(f'{tag.upper()} {n:04d}/{FRAMES} {time.monotonic()-t0:6.1f}s',flush=True)
            assert not renderer.stdout.read(1)
            if renderer.wait(timeout=12)!=0:raise RuntimeError(err.name)
            if writer:
                writer.stdin.close()
                if writer.wait(timeout=70)!=0:raise RuntimeError(log.name)
        except BaseException:
            for p in (renderer,writer):
                if p and p.poll() is None:p.kill()
            raise
    print((QA/f'{tag}-renderer.log').read_text().strip(),flush=True)
    stats=audit_trace(record,not proof)
    montage(target,PROBES)
    dump(QA/f'{tag}-layout.json',dict(size=size,source='native geometry',safe_text_bounds=dict(layout.report),map_annotated_frames=layout.map_frames,
         frame_audit=stats))
    if not proof:
        materials=[MATS/'silt.u8',MATS/'scales.u8']; fonts=sorted(FONTS.glob('*.ttf')); code=sorted(p for p in HERE.iterdir() if p.suffix in ('.py','.cpp','.hpp'))
        dump(QA/'build.json',dict(frames=FRAMES,size=size,render_size=(render_w,render_h),fps=FPS,duration=FRAMES/FPS,cuts=CUTS,
             retired_media_inputs=[],project_sources={p.name:digest(p) for p in code},
             field_inputs={p.name:digest(p) for p in [world,*fields]},brand_fonts={p.name:digest(p) for p in fonts},
             detail_tiles={p.name:digest(p) for p in materials},render_log=(QA/'render-renderer.log').read_text().strip(),
             seconds=round(time.monotonic()-t0,3),program_audio=mix['sha256'],encode_sha256=digest(STAGING/(NAME+'.pending.mp4'))))
    print('EDITORIAL_PROOF_READY' if proof else 'SHORT_NATIVE_ENCODE_READY',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--proof',action='store_true');p.add_argument('--skip-compile',action='store_true')
    a=p.parse_args();build(a.proof,not a.skip_compile)
