#!/usr/bin/env python3
"""Film typography, authenticated clean plates, and resumable per-shot encoding."""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
import math
import subprocess
import time

import numpy as np
from PIL import Image, ImageFilter

from assets import HERE, HOME, FIELDS
from cut import BY, F, FPS, S, inside, header
from motion import FF, Gfx, Trace, CREAM, MINT, SKY, AMBER, DARK, bound, smooth, ease_out

VIDEO=HOME/'picture'; QA=HOME/'proof'; V2=HOME/'opening'; FULL=HOME/'render-film'
MASTER=(1920,1080); NATIVE=(1024,576)


def build():
    from cues import native_marks
    HOME.mkdir(exist_ok=True,parents=True)
    data=['#pragma once']
    for k,v in native_marks().items():data.append('constexpr int '+k+('[]={'+','.join(map(str,v))+'};' if isinstance(v,tuple) else '='+str(v)+';'))
    (HOME/'marks.hpp').write_text('\n'.join(data)+'\n');(HOME/'timeline.hpp').write_text(header())
    for src,to in (('pilot.cpp','pilot'),('render_film.cpp','render-film')):
        p=HOME/(to+'.pending')
        subprocess.run(['g++','-O3','-std=c++17','-march=native','-fopenmp','-ffast-math','-Wall','-Wextra','-Werror', '-I',str(HOME),str(HERE/src),'-o',str(p)],check=True)
        p.replace(HOME/to)


def raster(k):
    if k<12:return (1152,648) if k in (2,3,5) else (960,540)
    return NATIVE


def opening_parts():
    V2.mkdir(exist_ok=True,parents=True)
    for k in range(12):
        w,h=raster(k);p=V2/f'{k:02d}.rgba';q=p.with_suffix('.csv')
        if p.is_file() and q.is_file() and p.stat().st_size==(F[k+1]-F[k])*w*h*4:continue
        tmp=p.with_suffix('.pending.rgba');trace=q.with_suffix('.partial.csv')
        with tmp.open('wb') as out:
            subprocess.run([str(HOME/'pilot'),str(FIELDS),str(w),str(h),str(F[k]),str(F[k+1]),str(trace)],stdout=out,check=True)
        trace.replace(q);tmp.replace(p);print('OPEN_PLATE',k,flush=True)


class FilmType(Gfx):
    def amt(self,key):
        if self.omit==key:return 0.
        a=BY.get(key)
        return 1. if a is None else bound((self.f-a.f+1)/12)


COL={'mint':MINT,'gold':AMBER,'cream':CREAM}


def span(k,f,key):
    sec=(f-BY[key].f)/FPS
    return (1-smooth((sec-BY[key].hold+.28)/.32))*smooth((F[k+1]-f)/9.)


def type_layer(g,k,q):
    a=span(k,g.f,q.key)
    if a<=.003:return
    s=q.place;c=COL[q.tint]
    if q.key=='firm-soft':
        for x,text,col in ((407,'Firm mud',MINT),(1236,'Soft mud',CREAM)):
            g.stroke(q.key,x+2,824,66,col,a)
            g.type(x,851,text,68,'head',col,q.key,a,style='title-rise')
        return
    if s.startswith('title-'):
        place={'title-a':365,'title-b':470,'title-c':575}[s]
        g.type(93,place,q.text,101,'head',c,q.key,a,style='title-rise')
        if s=='title-a':
            g.stroke(q.key,96,326,154,AMBER,a)
        return
    x,y={'low':(96,806),'left-low':(95,408),'left':(95,118)}[s]
    numeric=q.text[0] in '≈0123456789'
    n=91 if numeric else 72 if len(q.text)<17 else 64 if len(q.text)<24 else 58
    g.stroke(q.key,x+1,y-18,83 if not numeric else 115,c,a)
    g.type(x-1,y,q.text,n,'metric' if numeric else 'head',c,q.key,a,style='count' if numeric else 'title-rise')
    sub={
       'now':('REGIONAL SEPARATION TODAY',118),'old-lock':('MODEL SNAPSHOT · NOT FOOTPRINT DATES',84),
       'then':('APPROXIMATE STUDY ESTIMATE',107),'length':('ONE IMPRESSION · ILLUSTRATIVE OUTLINE',108),
       'count':('AT ONE KOUM SITE',101),'countways':('KOUM SURVEY',104),
       'restore-model':('NOT A FOOTPRINT DATE',113),'range':('HYPOTHESIS · NOT A TRACED ROUTE',74),
       'mawsonia':('COELACANTH ILLUSTRATION',82),
    }.get(q.key)
    if sub:g.type(x,y+sub[1],sub[0],21,'mono',CREAM,q.key,a*.92,track=1.14)
    if q.key=='mayo-type':g.type(x+2,y+82,'ILLUSTRATIVE RIVERBED',20,'mono',CREAM,q.key,a*.86,track=1.04)


def pin(g,p,col,amount=1.):
    if len(p)>2 and p[-1]<0.:return
    x,y=p[:2]
    if not 65<x<1855 or not 69<y<1009:return
    g.circle(x,y,15.3,None,DARK,amount*.72,5.2)
    g.circle(x,y,14.5,None,col,amount*.84,2.3)
    g.circle(x,y,4.4,CREAM,None,amount*.92)
    g.circle(x,y,27.1,None,col,amount*.23,1.7)


def sep(g,points,tag,c,hold=1.):
    if tag not in BY:return
    p=ease_out(g.amt(tag));n=len(points)-1
    if not p:return
    for i in range(n):
        a=1-float(abs((i+.5)/n-.5))*2; light=smooth((p-(1-a)*.69)/.27)*hold
        q,r=points[i],points[i+1]
        end=tuple(x+(y-x)*.71 for x,y in zip(q,r,strict=True))
        if light>.004:
            g.line((q,end),DARK,light*.76,6.1);g.line((q,end),c,light*.98,3.4)


def early_geo(g,k,tr):
    f=g.f
    if k==3 and f<BY['old-lock'].f:return
    epoch=k==3
    pins=tr.sites[epoch]
    c=(AMBER,MINT)
    if k==5:
        x,y,_,_,ok=pins[1]
        if ok:pin(g,(x*1920,y*1080,1),MINT,.58+.29*smooth((f-F[k])/24))
        return
    a=smooth((f-F[k])/10.)
    for i in range(2):
        p=pins[i]
        if p[-1]>0:pin(g,(p[0]*1920,p[1]*1080,1),c[i],a)
    tag='then' if epoch else 'now';sep(g,tr.arc[epoch],tag,MINT if epoch else AMBER,span(k,f,tag))
    if k==2:
        # Track two short place labels with the shared geographic entry – not an extra subtitle row.
        for i in range(2):
            p=pins[i];X,Y=p[0]*1920,p[1]*1080;gx=max(95,X-160) if i==0 else min(1779,X+127);gy=Y-69
            A=span(k,f,'now')*g.amt('now')
            g.line(((X,Y),(gx,gy+28)),c[i],A*.65,2.2)
            g.type(gx,gy,'Sousa' if i==0 else 'Koum',39,'bold',CREAM,'now',A,'r' if i==0 else 'l',style='title-rise')


def local_steps(g,tr):
    for i,(x,y) in enumerate(tr.steps):
        key=f'small-step-{i}';u=ease_out(g.amt(key));
        if not u:continue
        pin(g,(x,y),MINT,.93*u)
        if i and u>0:
            r=tr.steps[i-1];distance=math.dist(r,(x,y))
            if distance<80:continue
            dx,dy=(x-r[0])/distance,(y-r[1])/distance
            a=(r[0]+30*dx,r[1]+30*dy);b=(x-34*dx,y-34*dy)
            end=tuple(a0+(b0-a0)*u for a0,b0 in zip(a,b,strict=True));g.line((a,end),MINT,.46*u,2.8)
            if u>.5:g.line(((end[0]-14*dx+6*dy,end[1]-14*dy-6*dx),end,(end[0]-14*dx-6*dy,end[1]-14*dy+6*dx)),MINT,.81*u,2.5)


def screens(g,k,tr):
    if S[k].rig=='world':
        if S[k].var==0:
            pin(g,tr[0],AMBER,.9)
        else:
            for p,c in zip(tr[:2],(AMBER,MINT),strict=True):pin(g,p,c,.86)
        if S[k].var==6:sep(g,[x[:2] for x in tr[2:]],'gap-returns',AMBER,span(k,g.f,'gap-returns'))
        if S[k].var>=7:
            for i,(p,c) in enumerate(zip(tr[:2],(AMBER,MINT),strict=True)):
                x,y,_=p;smooth_pin=smooth((g.f-F[k])/13)
                g.circle(x,y,41,None,c,.23*smooth_pin,2.)
    if S[k].rig=='strata':
        p=smooth((g.f-F[k])/29.)
        for j in range(2):
            x,y,z=tr[j];a=x-160;b=x+126
            col=AMBER if j==0 else MINT
            if 350<x<1590 and S[k].var!=2:
                for i in range(26):
                    z=i/26;v=(.56+.44*math.sin(math.pi*z))*math.sin(math.pi*z)
                    xpos=a+(b-a)*z;g.bar(xpos,865+20*j,(b-a)/26+.8,4.0,col,.82*p*v)
                g.line(((a-21,867+20*j),(b+20,867+20*j)),col,.15*p,1.)
    if S[k].rig=='credits':
        A=smooth((g.f-BY['credits-on'].f+1)/13.)*smooth((F[k+1]-g.f)/9.)
        g.bar(113,192,119,4,AMBER,A)
        g.type(110,218,'Sources & maps',89,'head',CREAM,None,A)
        g.type(113,408,'FOOTPRINTS & GEOLOGY',22,'mono',AMBER,None,A,track=2.6)
        g.type(113,465,'Jacobs et al. (2024) · corridor hypothesis',30,'sans',CREAM,None,A)
        g.type(113,523,'Menkem et al. (2026) · Koum survey',30,'sans',CREAM,None,A)
        g.type(113,581,'Carvalho et al. (2013) · Sousa preservation',30,'sans',CREAM,None,A)
        g.type(1005,408,'CARTOGRAPHY',22,'mono',MINT,None,A,track=2.6)
        g.type(1005,465,'Kocsis & Scotese · PaleoCoastlines & rotations',29,'sans',CREAM,None,A)
        g.type(1005,523,'Scotese & Wright · PaleoDEMs v2',29,'sans',CREAM,None,A)
        g.type(1005,581,'CC BY 4.0 · adapted / shaded / annotated',27,'sans',CREAM,None,A)
        g.type(1005,632,'Natural Earth & NOAA ETOPO5 · public domain',27,'sans',CREAM,None,A)
        g.line(((113,777),(1772,777)),SKY,A*.29,1.7)
        g.type(113,811,'EXTINCT LIFE   /   ORIGINAL CGI AND SCORE',22,'mono',CREAM,None,A,track=1.6)
        g.type(113,862,'Kenney gravel Foley · CC0 1.0',23,'sans',CREAM,None,A)


@lru_cache(maxsize=50)
def scrim(w,h,k):
    ys,xs=np.ogrid[0:1:h*1j,0:1:w*1j]; a=np.zeros((h,w),np.float32)
    for q in inside(k):
        if not q.text:continue
        v=.82 if q.place=='low' else .46 if q.place.startswith('title-') else .255 if q.place=='left' else .397
        m=(.39 if q.place.startswith('title-') else .46)*np.exp(-((xs+.09)/.55)**2-((ys-v)/.31)**2)
        np.maximum(a,m,out=a)
    return Image.fromarray(np.uint8(a*255))


@lru_cache(maxsize=12)
def curves(kind):
    # Densify the colour mids without crushing relief. No synthetic grain in the upload encode.
    x=np.arange(256)/255.0;a=[]
    for c in range(3):
        new=np.clip(.004+x**(1.035 if kind in ('v2','floor','valley') else 1.022)*(1.018 if c==0 else 1.003)+.012*x**3,0,1)
        a.extend(np.around(new*255).astype(int).tolist())
    return a


def make(image,k,f,tr,omit=None,return_g=False):
    q=S[k];kind=q.rig; w,h=image.size
    pic=image.convert('RGB').point(curves(kind))
    if image.mode=='RGBA' and k not in (2,3,5):
        matte=image.getchannel('A').point(lambda a:round(a*.72))
        pic=Image.composite(pic.filter(ImageFilter.GaussianBlur(1.65 if k in (0,1,9) else 1.21)),pic,matte)
    pic.paste(DARK,None,scrim(w,h,k))
    g=FilmType((w,h),f,omit)
    if k in (2,3,5):early_geo(g,k,tr)
    if k==11:local_steps(g,tr)
    if k>=12:screens(g,k,tr)
    for b in inside(k):
        if b.text and b.f<=f<=b.f+round((b.hold+.03)*FPS):type_layer(g,k,b)
    result=Image.alpha_composite(pic.convert('RGBA'),g.paper).convert('RGB')
    return (result,g.paper) if return_g else result


def trace(k,line):
    if k<12:return Trace(line)
    p=list(map(float,line.strip().split(',')));assert len(p)==38,(k,len(p));assert int(p[1])==k
    return [(p[j]*1920,p[j+1]*1080,p[j+2]) for j in range(2,38,3)]


def read_exact(stream,n):
    data=stream.read(n)
    if len(data)!=n:raise RuntimeError(f'Short frame: {len(data)} vs {n} bytes')
    return data


def bitrate(k):
    return {'v2':1470,'world':1135,'floor':1510,'valley':1550,'slabs':1350,'scan':1360,'grain':1320,'strata':1250,'fault':1350,'habitat':1280,'fish':1520,'credits':820}[S[k].rig]


def encoder(sz,k,dst):
    W,H=MASTER;rate=bitrate(k)
    return [FF,'-hide_banner','-loglevel','error','-y','-nostdin','-f','rawvideo','-pixel_format','rgb24','-framerate',str(FPS),'-video_size',f'{sz[0]}x{sz[1]}','-i','-',
       '-an','-filter_threads','1','-vf',f'scale={W}:{H}:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p',
       '-c:v','libx264','-threads','1','-preset','faster','-profile:v','high','-b:v',f'{rate}k','-maxrate',f'{round(rate*1.36)}k','-bufsize',f'{round(rate*1.82)}k',
       '-g','72','-keyint_min','24','-sc_threshold','0','-bf','3','-b_strategy','1','-x264-params','b-pyramid=normal:force-cfr=1:open-gop=0',
       '-color_range','tv','-colorspace','bt709','-color_trc','bt709','-color_primaries','bt709','-video_track_timescale','24','-movie_timescale','48000',str(dst)]


def path(k):return VIDEO/f'{k:02d}.mp4'


def encode_one(k,source,project,pending_source):
    # One decoder and consistent resolution/codec parameters for the concat.
    sz=raster(k);lo,hi=F[k],F[k+1];mask=k<12;stride=math.prod(sz)*(4 if mask else 3)
    dst=path(k);tmp=dst.with_suffix('.pending.mp4');proof={}
    cue=[q for q in inside(k) if q.text];fx={q.f:q for q in cue}
    want={lo,round(lo+(hi-lo)*.54),hi-1}|{q.f for q in cue}
    if pending_source:want={x for x in want if lo<=x<hi}
    with subprocess.Popen(encoder(sz,k,tmp),stdin=subprocess.PIPE) as p:
        assert p.stdin
        for f in range(lo,hi):
            raw=read_exact(source,stride);line=project.readline()
            assert int(line.split(',',1)[0])==f,(k,f,line)
            scene=trace(k,line);im=Image.frombytes('RGBA' if mask else 'RGB',sz,raw);out=make(im,k,f,scene)
            if f in want:
                out.save(QA/f'f{f:05d}.jpg',quality=94)
                if f in fx:
                    key=fx[f].key; without=make(im,k,f,scene,omit=key)
                    d=np.max(np.abs(np.asarray(out,dtype='int16')-np.asarray(without,dtype='int16')),axis=-1)>22
                    if key.startswith('title-'):
                        y=round((365+105*('title-a','title-b','title-c').index(key))*sz[0]/1920)
                        d[:y]=False;d[y+round(97*sz[0]/1920):]=False
                    n=int(d.sum());assert n>=20,(key,f,n)
                    proof[key]={'frame':f,'native_onset_changed_pixels':n}
                    np.savez_compressed(QA/f'type-{f:05d}.npz',delta=d,with_type=np.asarray(out)[d],without_type=np.asarray(without)[d],size=sz)
            p.stdin.write(out.tobytes())
        p.stdin.close();assert p.wait()==0
    assert set(proof)=={q.key for q in cue}
    dst.with_suffix('.json').write_text(json.dumps(proof,indent=2)+'\n');tmp.replace(dst)
    print('PICTURE_PART',f'{k+1:02d}/{len(S):02d}',S[k].key,hi-lo,dst.stat().st_size,flush=True)


def encode(first,last,redo=False):
    def available(k):
        return path(k).is_file() and path(k).with_suffix('.json').is_file() and not redo

    VIDEO.mkdir(exist_ok=True,parents=True);QA.mkdir(exist_ok=True,parents=True)
    for k in range(first,min(12,last)):
        if available(k):continue
        p=V2/f'{k:02d}.rgba'
        with p.open('rb') as source, p.with_suffix('.csv').open() as tr:encode_one(k,source,tr,False)
    k=max(12,first)
    while k<last:
        if available(k):k+=1;continue
        end=k+1
        while end<last and not available(end):end+=1
        native_csv=QA/f'trace-{k}-{end}.csv';native_csv.touch();w,h=NATIVE
        start=time.monotonic()
        with open(native_csv) as tf, subprocess.Popen([str(FULL),str(FIELDS),str(w),str(h),str(F[k]),str(F[end]),str(native_csv)],stdout=subprocess.PIPE) as proc:
            assert proc.stdout
            try:
                for i in range(k,end):encode_one(i,proc.stdout,tf,True)
            except BaseException:
                proc.terminate();raise
            assert proc.wait()==0
        print('PICTURE_GROUP',k,end,round(time.monotonic()-start,2),flush=True);k=end
    if all(path(j).exists() for j in range(len(S))):
        x=['ffconcat version 1.0']
        for j in range(len(S)):x += [f"file '{path(j).name}'",f'duration {(F[j+1]-F[j])/FPS:.12f}']
        (VIDEO/'concat.ffconcat').write_text('\n'.join(x)+'\n');print('PICTURE_READY',flush=True)


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--compile',action='store_true');a.add_argument('--open-plates',action='store_true');a.add_argument('--from',dest='first',type=int,default=0);a.add_argument('--to',dest='last',type=int,default=len(S)-1);a.add_argument('--tools-only',action='store_true');a.add_argument('--redo',action='store_true',help='replace the selected shot range');args=a.parse_args()
    if not 0<=args.first<=args.last<len(S):a.error('invalid inclusive shot range')
    if args.compile:build()
    if args.open_plates:opening_parts()
    if not args.tools_only:encode(args.first,args.last+1,args.redo)


if __name__=='__main__':main()
