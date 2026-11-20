#!/usr/bin/env python3
"""Original geometry and clean plates for the cinematic revision.

Writes signed-depth, linear albedo and slope fields and renders perspective RGB
plus a circle-of-confusion matte. Typography can be rebuilt without rerendering
geometry. No earlier movie pixels are an input.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import prepare_terrain as base
from cues import FRAMES, native_marks

CACHE=base.CACHE/'cinema-v2'
PACK=CACHE/'packed'
QA=CACHE/'qa'
OUT=base.OUT
MATS=base.MATERIALS
NATIVE=CACHE/'render-cinema'
ROOT=base.ROOT
FONTS=base.ATL/'animatic/fonts'


def sizes(k):
    if k in (2,3,5):return 1920,1080
    if k in (0,1,9):return 1536,864
    return 1408,792


def patch(dst,mask,color,mix=.72):
    dst[:]=base.mix(dst,base.rgb(color),np.float32(mask*mix))


def scatter_macro(x,z,alt,albedo,seed,kind):
    n,d=alt.shape[0],x[0,1]-x[0,0]
    rng=np.random.default_rng(seed+187)
    low=base.gray_noise((n,n),(31,206,711),(.55,.18,.10),seed+90)
    for j in range(620):
        iz,ix=rng.integers(52,n-52,size=2)
        X,Z=x[iz,ix],z[iz,ix]
        tight=kind in ('brazil','koum','stamp')
        if (tight and math.hypot(X,Z)<(.97 if j<140 else .50)) or (not tight and abs(X)<.93):continue
        r=rng.uniform(1.35,6.9) if j>=140 else rng.uniform(4.8,18.8)
        rr=int(r*2.2)+1
        S=np.s_[iz-rr:iz+rr+1,ix-rr:ix+rr+1]
        V,U=np.ogrid[-rr:rr+1,-rr:rr+1];ang=rng.uniform(-3.14,3.14)
        a,b=np.cos(ang),np.sin(ang);u=(U*a-V*b)/r;v=(U*b+V*a)/(r*rng.uniform(.66,1.50))
        w=base.smooth((1.12-(abs(u)**1.5+abs(v)**1.53+.18*low[S]))*1.33)
        w*=np.clip(1.13-.23*u+.16*v+.19*low[S],.61,1.47)
        alt[S]+=w*np.float32(r*d*rng.uniform(.39,.94))
        if kind=='brazil': colors=((.30,.155,.077),(.16,.108,.071),(.42,.284,.137),(.108,.071,.050))
        else: colors=((.116,.150,.127),(.211,.216,.170),(.33,.33,.241),(.096,.104,.089))
        patch(albedo[S],np.clip(w*.97,0,1),colors[j%4],.70)


def macro_v2(name):
    n,span=1280,9.6; x,z=base.field_coords(n,span); df=span/n
    k='warm' if name=='brazil' else 'cool'; seed={'brazil':41,'koum':52,'steps':77,'stamp':77}[name]
    broad,grain,alb=base.base_rock(n,seed,k)
    rng=np.random.default_rng(seed+3170)
    centres=np.stack(np.meshgrid(np.arange(-5.2,5.4,.68),np.arange(-5.2,5.4,.65)),axis=2).reshape(-1,2)
    centres+=rng.uniform(-.24,.24,centres.shape)
    query=np.stack((x+.097*grain,z+.111*np.roll(grain,19,axis=0)),axis=-1)
    sd=cKDTree(centres).query(query.reshape(-1,2),k=2,workers=1)[0].reshape(n,n,2).astype(np.float32)
    crease=(sd[:,:,1]-sd[:,:,0])
    clay=np.exp(-np.abs(crease)/(.0135+.010*np.maximum(0,grain)))*base.smooth(.56+broad*.89)
    grain2=base.gray_noise((n,n),(14,71,201,560,n),(.41,.24,.16,.12,.06),seed+164)
    groove=np.sin(31*(z-.29*x)+1.9*broad); tiny=base.smooth((grain2-.10)*1.37)
    alt=gaussian_filter(.082*broad+.013*grain+.011*grain2+.005*groove,1.17)-.0155*clay
    alt+=.050*np.sin(.66*x+.55*z)+.013*np.sin(x*1.95-z*2.8)
    pigment=(.89+.19*base.smooth(.48+broad*.56)+.13*tiny-.36*clay+.014*groove).astype(np.float32)
    alb*=pigment[...,None]
    pool=base.smooth(.12+.80*broad)
    patch(alb,pool,(.168,.069,.035) if k=='warm' else (.064,.097,.090),.35)
    scatter_macro(x,z,alt,alb,seed,name)
    coords={'brazil':[(.10,.16,1.38,1.56,13.,.15)],'koum':[(.14,.024,1.33,1.5,-22.,.43),(-1.46,1.54,1.01,1.35,-9.,.92)],
            'steps':[(-.32,-2.58,1.,1.31,-12.,.15),(.29,-1.30,1.02,1.33,7.,.11),(-.25,-.05,.997,1.3,-10.,.08),(.29,1.19,1.,1.28,6.,.22),(-.23,2.44,1.08,1.42,-8.,.29),(.26,3.67,1.01,1.31,9.,.39)],
            'stamp':[(.06,.20,1.26,1.51,0.,.20)]}[name]
    depth=np.zeros_like(alt); lip=depth.copy()
    for px,pz,w,h,angle,soft in coords:
        d,e=base.imprint(x,z,df,px,pz,w,h,angle,grain*.54,soft)
        depth=np.maximum(depth,d);lip=np.maximum(lip,e)
    # Smooth the cavity sidewalls, keep displaced grains and the soft rim.
    depth=gaussian_filter(depth,1.75)
    lip=gaussian_filter(lip,.76)
    depth*=1.-.07*base.smooth((grain2+.05)*1.75)
    alt=alt-.146*depth+.022*lip
    # Material details stay subtle in an unpressed stamp set. Darkness mainly
    # comes from the actual signed depression and ray-shadow, not a black decal.
    if name!='stamp':alb*=((1.-.14*depth)+.11*lip)[...,None]
    base.write_local(name,span,alt,alb,depth,lip)


def valley_v2(name):
    n,span=896,96.; x,z=base.field_coords(n,span); dawn=name=='floodplain'
    p,d,tex=base.base_rock(n,660+int(dawn)*17,'cool' if dawn else 'warm')
    smooth=base.smooth
    long=gaussian_filter(p,5.0)
    mid=(7.9 if dawn else 6.85)*np.sin(z*(.080 if dawn else .093)+(1.03 if dawn else .78))+1.62*np.sin(z*.165-1.4)
    # Broader and lower ground levels: an illustrative floodplain and riverbed,
    # not measured modern bathymetry or an exact view of the Cretaceous site.
    width=(4.5 if dawn else 3.56)+.83*np.sin(.108*z+.67)+.35*np.cos(.282*z+.46)+.31*long
    dist=x-mid; gap=abs(dist)-width+.49*long+.235*np.sin(z*.49+x*.23)
    lip=smooth((gap+.87)/2.26)
    h=-.63+.89*lip
    h+=(.33 if dawn else .69)*smooth((gap-2.42+.74*long)/1.54)
    h+=(.62 if dawn else 1.15)*smooth((gap-6.63+1.7*long)/1.70)
    h+=(.94 if dawn else 1.47)*smooth((gap-11.2+1.6*long)/2.6)
    h+=(2.32 if dawn else 2.94)*smooth((gap-17.4+4.4*long)/6.9)
    h+=1.96*smooth((z-19.0)/20.)+1.55*long*smooth((gap-9)/10)
    h+=.060*p+.011*np.sin(20.7*h+1.8*p)*lip
    bar1=np.exp(-((dist-1.57)/1.58)**2-((z-(-6.4 if dawn else 5.8))/7.2)**2)
    bar2=np.exp(-((dist+2.00)/1.32)**2-((z+14.1)/4.25)**2)
    h+=.75*bar1+.62*bar2
    scrub=smooth((p-.16+.20*d)*1.82)*smooth((gap-2.8)/8)
    h+=.58*scrub
    stone=tex*.57+base.rgb((.106,.127,.085) if dawn else (.193,.096,.051))*.81
    lamina=.90+.12*np.sin(h*17+.33*p)+.15*np.cos(h*7.86+x*.36+.78*long)
    stone*=np.clip(lamina,.62,1.22)[...,None]
    patch(stone,smooth((long+.19)*1.36)*lip,(.095,.155,.098) if dawn else (.257,.107,.049),.52)
    patch(stone,scrub,(.032,.087,.047) if dawn else (.047,.084,.043),.79)
    patch(stone,smooth((.07-h)/.25),(.074,.103,.067),.70)
    rng=np.random.default_rng(3812 if dawn else 8331)
    for j in range(1700):
        I,J=rng.integers(42,n-42,size=2)
        if gap[I,J]<.96 or gap[I,J]>32 or z[I,J]<-33:continue
        rock=j%4==0; r=rng.uniform(2.9,13) if rock else rng.uniform(2.3,8.2)
        rr=int(2.52*r); vy,ux=np.ogrid[-rr:rr+1,-rr:rr+1]; S=np.s_[I-rr:I+rr+1,J-rr:J+rr+1]
        rot=rng.uniform(-1.4,1.4);u=(ux*np.cos(rot)+vy*np.sin(rot))/r
        v=(-ux*np.sin(rot)+vy*np.cos(rot))/(r*rng.uniform(.64,1.36))
        mass=smooth(1.25-((abs(u)**1.67+abs(v)**1.6)*(1.+.25*d[S]+.13*np.sin(vy*.90+ux*.51))))
        tint=(.296,.185,.097) if rock and not dawn else (.189,.190,.113) if rock else (.036,.090,.042) if dawn else (.048,.084,.028)
        h[S]+=mass*rng.uniform(.21,.83)*(.88 if dawn else 1.0)
        patch(stone[S],mass,tint,.83)
    base.write_local(name,span,h,stone,np.zeros_like(h),np.zeros_like(h))


def geology_v2():
    n,span=1056,14.; x,z=base.field_coords(n,span)
    p,k,alb=base.base_rock(n,799,'cool'); medium=gaussian_filter(p,2)
    wob=.45*np.sin(.62*x)+.21*medium+.12*np.sin(x*2.05-.2*z)
    cuts=(-3.,-1.19,.75,2.84)
    alt=.345+.058*medium+.017*k
    for z0,dy in zip(cuts,(.54,.60,.67,.57),strict=True):
        alt+=dy*base.smooth((z-z0+wob)/.29)
    al=alb*.71+base.rgb((.211,.131,.072))*.57
    stripe=.80+.17*np.sin(alt*49+.8*medium)+.095*np.cos(alt*109+1.29*k)
    al*=stripe[...,None]
    marks=np.zeros_like(p); lips=marks.copy()
    for i,cz in enumerate((-1.91,-.17,1.89,4.05)):
        for cx in ((-1.17,.81) if i%2==0 else (-.91,1.30)):
            h,l=base.imprint(x,z,span/n,cx,cz,.82,1.16,-9+7*i,k*.49,.40)
            marks=np.maximum(marks,h); lips=np.maximum(lips,l)
    base.write_local('shelves',span,alt-.107*marks+.019*lips,al,marks,lips)


def prep(fetch=False):
    PACK.mkdir(parents=True,exist_ok=True)
    base.check_inputs(fetch)
    base.PACK=PACK
    base.build_globes()
    for nm in ('brazil','koum','stamp','steps'):macro_v2(nm)
    for nm in ('river','floodplain'):valley_v2(nm)
    geology_v2()


def compile_renderer():
    CACHE.mkdir(parents=True,exist_ok=True)
    mk=native_marks(); header=CACHE/'marks.hpp'; tmp=NATIVE.with_suffix('.pending')
    lines=['#pragma once']
    for k,v in mk.items():
        if isinstance(v,tuple):lines.append('constexpr int '+k+'[]={'+','.join(map(str,v))+'};')
        else:lines.append(f'constexpr int {k}={v};')
    header.write_text('\n'.join(lines)+'\n')
    subprocess.run(['g++','-std=c++17','-O3','-ffast-math','-march=native','-fopenmp','-Wall','-Wextra','-Werror','-I',str(CACHE),str(HERE/'render_cinema.cpp'),'-o',str(tmp)],check=True)
    tmp.replace(NATIVE)


def geometry_key():
    h=sha256()
    for f in (HERE/'geometry.py',HERE/'render_cinema.cpp',HERE.parent/'prepare_terrain.py',HERE.parent/'pilot-assets.json'):
        h.update(f.read_bytes())
    h.update(json.dumps(native_marks(),sort_keys=True).encode())
    for f in sorted(PACK.glob('*.field')):h.update(base.hashfile(f).encode())
    assert len(list(PACK.glob('*.field')))==9
    return h.hexdigest()[:14]


def raw_dir(key=None):return CACHE/f'clean-{key or geometry_key()}'


def engine(size,first,last,tr):
    return [str(NATIVE),str(PACK),*map(str,size),str(first),str(last),str(tr)]


def proof():
    QA.mkdir(parents=True,exist_ok=True)
    moments=(1.02,3.50,5.6,8.8,10.78,12.45,17.1,22.1,29.4,34.4,39.2,45.4,49.46,50.33,54.4,59.2)
    for t in moments:
        f=round(t*24); trace=QA/f'new-{f:04d}.csv';size=(832,468)
        a=subprocess.check_output(engine(size,f,f+1,trace))
        assert len(a)==math.prod(size)*4
        Image.frombytes('RGBA',size,a).convert('RGB').save(QA/f'new-{f:04d}.jpg',quality=94)


def plates(only):
    work=raw_dir();work.mkdir(parents=True,exist_ok=True)
    print('CLEAN_SET',work,flush=True)
    for k,(lo,hi) in enumerate(zip(FRAMES,FRAMES[1:]),1):
        if only and k not in only:continue
        w,h=sizes(k-1); n=(hi-lo)*w*h*4
        dst=work/f'{k:02d}.rgba';tr=work/f'{k:02d}.csv'
        if dst.is_file() and dst.stat().st_size==n and tr.is_file():continue
        s=time.monotonic(); tmp=dst.with_suffix('.pending.rgba');tp=tr.with_suffix('.pending.csv')
        with tmp.open('wb') as stream:
            subprocess.run(engine((w,h),lo,hi,tp),stdout=stream,check=True)
        assert tmp.stat().st_size==n
        tp.replace(tr);tmp.replace(dst)
        print(f'CLEAN_SHOT {k:02d} {lo:04d}-{hi:04d} {time.monotonic()-s:.1f}s',flush=True)
    print('CLEAN_READY',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepare',action='store_true');p.add_argument('--fetch',action='store_true')
    p.add_argument('--proof',action='store_true');p.add_argument('--only',nargs='+',type=int)
    a=p.parse_args()
    if a.prepare:prep(a.fetch)
    else:
        compile_renderer()
        if a.proof:proof()
        else:plates(a.only)


if __name__=='__main__':main()
