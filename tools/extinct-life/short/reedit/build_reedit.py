#!/usr/bin/env python3
"""Render the V2 timeline from scene geometry, then composite the word plates."""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
from contextlib import ExitStack
from time import monotonic

from PIL import Image, ImageDraw
from clock import CACHE, QA, MIX, HERE, FIELDS, MATS, W, H, FPS, PENDING, TITLE, header, dump, digest
from typography import Layout, SPACE
from mix import FF
from build import inputs

BIN=CACHE/'scene'


def compile_scene(t):
    (QA/'recut_clock.hpp').write_text(header(t))
    subprocess.run(['g++','-std=c++17','-O3','-march=native','-fopenmp','-ffast-math','-Wall','-Wextra','-Werror',
                    '-I',str(QA),str(HERE/'scene.cpp'),'-o',str(BIN)],check=True,timeout=45)


def source_inputs():
    world,fields=inputs();pin=json.loads((HERE.parent/'inputs.json').read_text())['geo8_and_world']
    assert all(digest(p)==pin[p.name] for p in (world,*fields))
    return [world,*fields]


def encode(target,size,phone):
    w,h=size
    return [FF,'-hide_banner','-loglevel','warning','-nostdin','-y','-f','rawvideo','-pixel_format','rgb24',
        '-video_size',f'{w}x{h}','-framerate',str(FPS),'-i','pipe:0','-i',str(MIX/'program.wav'),'-map','0:v:0','-map','1:a:0',
        '-map_metadata','-1','-map_chapters','-1','-vf','scale=out_color_matrix=bt709:in_range=pc:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p',
        '-c:v','libx264','-profile:v','high','-level:v','4.1','-crf','19' if phone else '16.4','-preset','veryfast' if phone else 'medium',
        '-tune','film','-maxrate','18900k','-bufsize','28400k','-g','60','-keyint_min','16','-threads','2',
        '-c:a','aac','-profile:a','aac_low','-ar','48000','-b:a','320k','-color_range','tv','-color_primaries','bt709',
        '-color_trc','bt709','-colorspace','bt709','-chroma_sample_location','left','-metadata',f'title={TITLE}',
        '-metadata:s:a:0','language=eng','-movflags','+faststart',str(target)]


def audit_trace(r,t,full):
    d={int(row[0]):row for row in r};e=t['events'];c=t['cuts'];end=t['frames']
    assert d[0][4]>d[5][4] and d[5][2]<.0003 and d[12][2]>.90
    assert d[c[2]-1][2]>.998 and d[c[2]-1][3]==0
    assert 0<d[c[3]-1][3]<d[e['lip_chip']][3]<d[c[4]-1][3]<=1.0
    assert d[c[4]][2]==1 and d[c[4]][3]>.995
    assert d[end-1][4]>d[0][4] and d[end-1][4]-d[0][4]<.13
    assert d[e['map_land']][5]==1 and d[c[8]][5]==0 and 0<d[(t["art"]["wipe_begin"]+t["art"]["wipe_end"])//2][5]<1
    if full:
        assert list(d)==list(range(end))
        marks=[x[5] for x in r[c[7]:c[9]]];assert marks==sorted(marks)
        for k in ('hook','firm','soft'):
            i=e[k+'_impact'];j=e[k+'_lift'];assert d[i-1][4]>d[i][4]>d[i+1][4] and d[i][2]<.001<d[i+1][2]
            assert d[j+3][4]-d[j-1][4]>.014,(k,d[j-1][:6],d[j+3][:6])
        assert max(abs(d[c[1]+i][4]-d[c[2]+i][4]) for i in range(36))<=.034
    return dict(frame_rows=len(r),firm_slump=d[c[2]-1][3],initial_soft_slump=d[c[3]-1][3],
                chip_soft_slump=d[e['lip_chip']][3],final_soft_slump=d[c[4]-1][3],
                loop_ankle_delta=round(d[end-1][4]-d[0][4],8))


def sheet(p,groups):
    for k,nums in enumerate(groups,1):
        panel=Image.new('RGB',(216*len(nums),410),(9,19,25));d=ImageDraw.Draw(panel)
        for i,n in enumerate(nums):
            with Image.open(p/f'f{n:04d}.jpg') as im:panel.paste(im.resize((216,384),Image.Resampling.LANCZOS),(216*i,0))
            d.text((i*216+14,391),f'{n:04d}   {n/FPS:.3f}s',fill=(239,231,212))
        panel.save(p/f'sequence-{k:02d}.jpg',quality=93,subsampling=0)


def build(proof=False,phone=False):
    t0=monotonic();QA.mkdir(parents=True,exist_ok=True);PENDING.parent.mkdir(parents=True,exist_ok=True)
    fields=source_inputs()
    mix=json.loads((QA/'mix.json').read_text());t=mix['timeline'];assert mix['sha256']==digest(MIX/'program.wav')
    compile_scene(t)
    size=(540,960) if proof or phone else (W,H);render_size=(576,1024) if proof or phone else (1152,2048)
    tag='proof' if proof else 'phone' if phone else 'native';views=QA/f'{tag}-views';views.mkdir(exist_ok=True)
    frames=t['probes'] if proof else list(range(t['frames'])); wanted=set(t['probes']);r=[]
    order=QA/f'{tag}-frames.txt';order.write_text('\n'.join(map(str,frames))+'\n');trace=QA/f'{tag}-trace.csv'
    prog=[str(BIN),str(FIELDS),str(MATS),*map(str,render_size),str(order),str(trace)]
    output=PENDING.parent/(PENDING.stem.replace('.pending','-Phone-Proof')+'.mp4') if phone else PENDING
    expected=render_size[0]*render_size[1]*3;layout=Layout(size,t,mix)
    with ExitStack() as st:
        err=st.enter_context((QA/f'{tag}-renderer.log').open('wb'))
        sim=st.enter_context(subprocess.Popen(prog,stdout=subprocess.PIPE,stderr=err,
                    env={**os.environ,'OMP_NUM_THREADS':'2','OMP_DYNAMIC':'FALSE'}))
        encoder=None;p=None
        if not proof:
            enc=st.enter_context((QA/f'{tag}-encode.log').open('wb'))
            encoder=st.enter_context(subprocess.Popen(encode(output,size,phone),stdin=subprocess.PIPE,stderr=enc))
        try:
            for n in frames:
                raw=sim.stdout.read(expected)
                if len(raw)!=expected:raise RuntimeError(f'Geometry frame {n}: {len(raw)} bytes; see {err.name}')
                if p is None:p=st.enter_context(trace.open())
                row=tuple(map(float,p.readline().rstrip().split(',')));assert len(row)==18 and row[0]==n,row
                r.append(row);im=Image.frombytes('RGB',render_size,raw).resize(size,Image.Resampling.LANCZOS)
                im=layout.paint(im,n,row[1:])
                if encoder:encoder.stdin.write(im.tobytes())
                if n in wanted:im.save(views/f'f{n:04d}.jpg',quality=93,subsampling=0)
                if n in t['cuts'] or n%120==0:print(f'{tag.upper()} {n:03d}/{t["frames"]}  {monotonic()-t0:.1f}s',flush=True)
            assert not sim.stdout.read(1)
            if sim.wait(timeout=15):raise RuntimeError(err.name)
            if encoder:
                encoder.stdin.close()
                if encoder.wait(timeout=45):raise RuntimeError(enc.name)
        except BaseException:
            for p in (sim,encoder):
                if p and p.poll() is None:p.kill()
            raise
    log=(QA/f'{tag}-renderer.log').read_text().strip();assert re.search(r'mass delta 0\.00000',log),log
    m=layout.measurement();checks=audit_trace(r,t,not proof)
    groups=[t['probes'][j:j+5] for j in range(0,len(t['probes']),5)];sheet(views,groups)
    artifact=dict(timeline=t,size=size,source_size=render_size,trace=checks,graphics=m,scene=log,
        source_digests={p.name:digest(p) for p in fields+[SPACE,MATS/'silt.u8',MATS/'scales.u8']},
        project_digests={str(p.relative_to(HERE.parent)):digest(p) for p in sorted([*HERE.glob('*.py'),*HERE.glob('*.cpp'),*HERE.parent.glob('*.hpp')])},
        seconds_to_build=round(monotonic()-t0,2),program_audio=mix['sha256'])
    if not proof:artifact['encode_sha256']=digest(output)
    dump(QA/f'{tag}-build.json',artifact)
    print('RECUT_GEOMETRY_READY',log,checks,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--proof',action='store_true');g.add_argument('--phone-cut',action='store_true')
    a=p.parse_args();build(a.proof,a.phone_cut)
