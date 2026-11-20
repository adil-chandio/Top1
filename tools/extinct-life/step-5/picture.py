#!/usr/bin/env python3
"""Composite world-space callouts over the native 3D opening and encode plates.

Proof renders never change the cut inputs. The only picture source is render3d.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from prepare_terrain import HERE, CACHE, PACK, ATL, hashfile

FPS=24
CLOCK=48_000
FRAMES=(0,63,99,245,470,629,765,869,1040,1154,1267,1353,1457)
SHOT_NAMES=('Sousa relief','Koum relief','Present-day orbit','Deep-time reveal','Title / concept valley',
            'Koum approach','Exposed rock horizons','Mayo Rey river concept','Survey surface','Track contact',
            'Trackways','One sequence')
END=FRAMES[-1]/FPS
SIZE=(1920,1080)
FONTS=ATL/'animatic/fonts'
FF=imageio_ffmpeg.get_ffmpeg_exe()
NATIVE=CACHE/'render3d'
NEAR=(1536,864)
GEOSIZE=(1920,1080)
LOCAL=(1280,720)
INK=(8,17,22)
CREAM=(252,241,218)
GOLD=(246,186,111)
TEAL=(165,234,216)
FAINT=(214,223,215)


def smooth(x):
    v=max(0,min(1,x)); return v*v*(3-2*v)


def appear(t,a,r=.38):
    return smooth((t-a)/r)


def envelope(t,enter,fade_in,leave=None,fade_out=.3):
    return appear(t,enter,fade_in)*(1-appear(t,leave,fade_out) if leave is not None else 1)


@lru_cache(maxsize=140)
def font(s,face):
    name={'head':'Fraunces.ttf','tag':'PlexMono.ttf','sans':'PlexSans.ttf','bold':'PlexSans.ttf'}[face]
    ft=ImageFont.truetype(str(FONTS/name),s)
    if face=='head': ft.set_variation_by_axes([min(103,max(26,s)),602,13,0])
    elif face in ('sans','bold'):ft.set_variation_by_axes([445 if face=='sans' else 615,100])
    return ft


def tone(rgb,alpha):
    return (*rgb,round(max(min(alpha,1),0)*255))


@lru_cache(maxsize=30)
def scrim(size,tag):
    w,h=size
    y,x=np.ogrid[0:1:h*1j,0:1:w*1j]
    if tag=='title':
        m=.72*np.exp(-((x+.15)/.64)**2-((y-.51)/.55)**2)+.16*y**5
    elif tag=='map':
        m=.72*np.exp(-((x+.17)/.48)**2-((y-.18)/.30)**2)+.30*y**8
    elif tag=='lower':
        m=.57*np.exp(-((x+.11)/.58)**2-((y-.89)/.33)**2)+.22*y**7
    elif tag=='upper':
        m=.63*np.exp(-((x+.10)/.56)**2-((y-.19)/.31)**2)+.21*y**9
    else:
        m=.29*y**8
    return Image.fromarray(np.uint8(np.minimum(1,m)*255))


class Overlay:
    def __init__(self,size):
        self.w,self.h=size
        self.scale=self.w/1920
        self.layer=Image.new('RGBA',size)
        self.d=ImageDraw.Draw(self.layer)

    def p(self,xy):return tuple(round(v*self.scale) for v in xy)
    def coord(self,xy):return xy[0]*1920,xy[1]*1080

    def text(self,x,y,text,size,color=CREAM,face='sans',a=1,anchor='lt',shadow=0):
        if a<.004 or not text:return
        xy=self.p((x,y)); f=font(round(size*self.scale),face)
        if shadow>0:
            self.d.text((xy[0]+1,xy[1]+max(1,round(2*self.scale))),text,font=f,anchor=anchor,
                        fill=tone(INK,a*shadow),stroke_width=round(1.25*self.scale),stroke_fill=tone(INK,a*shadow))
        self.d.text(xy,text,font=f,anchor=anchor,fill=tone(color,a))

    def tracking(self,x,y,text,size,space,color=CREAM,a=1):
        f=font(round(size*self.scale),'tag')
        for char in text:
            self.text(x,y,char,size,color,'tag',a)
            x+=f.getlength(char)/self.scale+space

    def line(self,ps,col,a=.9,w=2):
        if a>.008:
            self.d.line([self.p(x) for x in ps],fill=tone(col,a),width=max(1,round(w*self.scale)),joint='curve')

    def dot(self,x,y,r,col,a=1,edge=None,lw=1):
        self.d.ellipse(self.p((x-r,y-r,x+r,y+r)),fill=tone(col,a) if col is not None else None,
                       outline=tone(edge,a) if edge is not None else None,width=max(1,round(lw*self.scale)))

    def label(self,x,y,s,kicker,a,col=GOLD,right=False):
        al='rt' if right else 'lt'
        self.text(x,y,kicker,19,col,'tag',a,al,shadow=.92)
        self.text(x,y+34,s,36,CREAM,'bold',a,al,shadow=.84)

    def little(self,txt,a=1,right=False):
        self.text(1821 if right else 95,1008,txt,18,FAINT,'tag',a,'rt' if right else 'lt',shadow=.85)


# Projection values produced by the same camera and the same frame as the pixels.
# Two groups: 2 pins and 17 arc samples each, then 5 step points and 4 rock layers.
class Trace:
    def __init__(self,values):
        assert len(values)==111, len(values)
        self.frame=int(values[0]); self.shot=int(values[1]); self.camera=tuple(values[2:5])
        self.pins=[];self.arc=[]
        for i in range(2):
            row=values[5+i*44:5+(i+1)*44]
            self.pins.append([tuple(row[j:j+5]) for j in (0,5)])
            self.arc.append([(row[j]*1920,row[j+1]*1080) for j in range(10,44,2)])
        self.steps=[(values[j]*1920,values[j+1]*1080) for j in range(93,103,2)]
        self.layers=[(values[j]*1920,values[j+1]*1080) for j in range(103,111,2)]

    @classmethod
    def read(cls,f):return cls([float(a) for a in f.readline().strip().split(',')])


def draw_pin(g,p,t,tag,kicker,color,a,region=False,right=False,past=False):
    px,py,lx,ly,visible=p
    if not visible or not .012<px<.988 or not .026<py<.971 or a<=.004:return
    x,y=g.coord((px,py)); mx,my=g.coord((lx,ly))
    # Leader begins at the raised world's projection, not a fixed screen label.
    ma=138 if not region else 177
    off_y=-130 if not region else -117
    ax=max(96,min(1816,mx + (ma if right else -ma)))
    ay=max(175,min(901,my+off_y*a-(38 if past else 0)))
    joint=(mx+(ax-mx)*.65,ay+67)
    tail=(ax+(-13 if not right else 13),ay+67)
    g.line([(x,y),(mx,my),joint,tail],INK,a*.52,6)
    g.line([(x,y),(mx,my),joint,tail],color,a*.91,2)
    g.dot(x,y,19,None,a*.30,color,2)
    g.dot(x,y,8.4,INK,a*.87)
    g.dot(x,y,5.6,color,a,CREAM,1.1)
    g.dot(*tail,3.3,color,a)
    if not right:
        tx=max(94,ax-202)
        g.label(tx,ay,kicker,tag,a,color)
    else:
        tx=min(1824,ax+238)
        g.label(tx,ay,kicker,tag,a,color,right=True)


def segments(g,points,age,a):
    for i in range(len(points)-1):
        # Show equal halves of a distance bracket; its stroke has no direction.
        used=len(points)-1
        j=abs((i+.5)/used-.5)*2
        step=smooth((age-j*.72)/.22)*a
        if step<.002:continue
        v,b=points[i],points[i+1]
        s=.67
        tail=(v[0]+(b[0]-v[0])*s,v[1]+(b[1]-v[1])*s)
        g.line((v,tail),INK,.72*step,7)
        g.line((v,tail),GOLD,.98*step,3)


def metric(g,number,lab,x,y,a,tone_=GOLD):
    if a<=.002: return
    offset=18*(1-a)
    g.text(x,y+offset,number,91,tone_,'bold',a,shadow=.81)
    g.tracking(x+4,y+105+offset,lab,19,1.05,CREAM,a)


def geographic(g,tr,t):
    k=tr.shot
    if k==5:
        a=appear(t,26.22,.39)
        g.tracking(95,87,'NORTHERN CAMEROON',22,1.7,TEAL,a)
        g.text(95,128,'Koum Basin',63,CREAM,'head',a,shadow=.72)
        g.little('REGIONAL LOCATION  /  ELEVATION EXAGGERATED',a,True)
        p=tr.pins[0][1]; pin=appear(t,28.56,.36)
        x,y=g.coord(p[:2]); q=(max(12,min(114,59+39*math.sin(t*4.3))))
        if p[-1]:
            g.dot(x,y,q,None,.25*pin,TEAL,1.8);g.dot(x,y,16,None,.85*pin,TEAL,2.1);g.dot(x,y,5.6,TEAL,pin)
            g.line(((x-33,y),(x-18,y)),TEAL,pin*.7);g.line(((x+18,y),(x+33,y)),TEAL,pin*.7)
        return
    old=k==3
    if old:
        a=appear(t,11.06,.53)
        g.tracking(95,85,'EARLY CRETACEOUS',21,1.7,TEAL,a)
        g.text(95,129,'125 million',71,CREAM,'head',a,shadow=.82)
        g.text(95,210,'years ago',71,CREAM,'head',a,shadow=.82)
        g.text(100,304,'Model snapshot, not footprint dates',26,FAINT,'sans',a,shadow=.9)
        rewind=envelope(t,10.208,.21,11.07,.28)
        g.tracking(96,89,'REWIND  /  DEEP TIME',21,1.8,TEAL,rewind)
        g.line([(97,132),(97+242*min(1,(t-10.208)/1.16),132)],TEAL,.88*rewind,2)
        g.little('PALEOMAP COASTS + PALEODEMS  /  CC BY 4.0  /  RELIEF EXAGGERATED',a,True)
        p=appear(t,11.6,.62)
        draw_pin(g,tr.pins[1][0],t,'FUTURE BRAZIL','Sousa region',GOLD,p,past=True)
        draw_pin(g,tr.pins[1][1],t,'FUTURE CAMEROON','Koum region',TEAL,p,right=True,past=True)
        m=appear(t,15.395,.48)
        segments(g,tr.arc[1],(t-15.395)/.90,m)
        metric(g,'≈1,000 km','THEN  /  STUDY ESTIMATE',96,363,m,TEAL)
    else:
        a=appear(t,4.135,.41)
        g.tracking(95,85,'PRESENT DAY',23,1.8,TEAL,a)
        g.text(95,125,'Atlantic Ocean',62,CREAM,'head',a,shadow=.84)
        g.little('NATURAL EARTH + NOAA ETOPO5  /  RELIEF EXAGGERATED',a,True)
        draw_pin(g,tr.pins[0][0],t,'BRAZIL','Sousa Basin',GOLD,appear(t,4.34,.43))
        draw_pin(g,tr.pins[0][1],t,'CAMEROON','Koum Basin',TEAL,appear(t,4.74,.47),right=True)
        m=appear(t,6.225,.46)
        segments(g,tr.arc[0],(t-6.225)/.87,m)
        metric(g,'≈6,000 km','APART TODAY',94,308,m)


def composition(rgba,tr):
    assert rgba.mode=='RGBA'
    t=tr.frame/FPS;k=tr.shot;size=rgba.size
    im=rgba.convert('RGB')
    if k in (0,1,4,9,10):
        depth=rgba.getchannel('A')
        radius=5 if k in (0,1,9) else 3.6
        soft=im.filter(ImageFilter.GaussianBlur(radius*size[0]/1920))
        im=Image.composite(soft,im,depth)
    tag='map' if k in (2,3,5) else 'title' if k==4 else 'upper' if k in (6,8,9,10,11) else 'lower'
    if k in (0,1):tag='lower'
    im.paste(INK,(0,0,*size),scrim(size,tag))
    g=Overlay(size)
    if k in (2,3,5):
        geographic(g,tr,t)
    elif k in (0,1):
        ka=FRAMES[k]/FPS
        a=appear(t,ka+.10,.28)
        g.tracking(96,797,'BRAZIL' if k==0 else 'CAMEROON',20,1.8,GOLD if k==0 else TEAL,a)
        g.text(94,831,'Sousa Basin' if k==0 else 'Koum Basin',62,CREAM,'head',a,shadow=.91)
        g.little('CGI ILLUSTRATION  /  NOT SPECIMEN IMAGERY',a)
    elif k==4:
        a=envelope(t,19.58,.69,25.78,.41)
        g.tracking(101,270,'E X T I N C T   L I F E',20,.75,GOLD,a)
        g.line([(99,326),(99+106*a,326)],GOLD,a,3)
        for i,s in enumerate(('Why These Dinosaur','Footprints Are','an Ocean Apart')):
            u=envelope(t,19.60+i*.13,.67,25.77,.40)
            y=375+i*107+(1-u)*17
            g.text(93,y,s,104,CREAM,'head',u,shadow=.68)
        g.little('CONCEPT LANDSCAPE  /  NOT A RECONSTRUCTED TRACK SITE',a)
    elif k==6:
        a=appear(t,32.625,.47)
        metric(g,'4','TRACK-BEARING SURFACES',94,161,a)
        for j,(x,y) in enumerate(tr.layers):
            q=appear(t,32.63+j*.29,.43)
            if x<1380 and 112<y<976 and q>.005:
                g.dot(x,y,6.6,GOLD,q,CREAM,1)
                g.line(((x,y),(x+43,y-32),(x+88,y-32)),GOLD,q*.82)
                g.text(x+97,y-42,f'{j+1:02}',20,GOLD,'tag',q,shadow=.88)
        g.little('SCHEMATIC GEOLOGY  /  SEPARATE SURFACES, NOT ONE EVENT',max(.65,a))
    elif k==7:
        a=appear(t,36.25,.51)
        g.tracking(97,782,'KOUM BASIN  /  CAMEROON',21,1.6,TEAL,a)
        g.text(93,825,'Mayo Rey River',69,CREAM,'head',a,shadow=.89)
        g.little('CGI LANDSCAPE  /  NOT FIELD FOOTAGE',a)
    elif k==8:
        a=appear(t,45.538,.43)
        metric(g,'283','FOOTPRINTS STUDIED',94,168,a,TEAL)
        g.little('ONE SITE IN THE 2026 SURVEY  /  ILLUSTRATIVE TRACKS',.82)
    elif k==9:
        a=envelope(t,48.15,.41,51.89,.38)
        g.tracking(95,113,'ONE ANIMAL',20,1.5,TEAL,a)
        g.text(94,150,'One footfall',64,CREAM,'head',a,shadow=.94)
        g.little('CGI DEMONSTRATION  /  NOT AN IDENTIFIED TRACKMAKER',.95)
    else:
        if k==10:
            a=appear(t,52.792,.43)
            metric(g,'34','DOCUMENTED TRACKWAYS',94,146,a,TEAL)
        else:
            a=appear(t,56.53,.36)
            g.tracking(96,124,'ON ONE PATCH OF GROUND',21,1.4,GOLD,a)
            g.text(94,172,'Read the sequence',60,CREAM,'head',a,shadow=.87)
            for j,(x,y) in enumerate(tr.steps):
                q=appear(t,56.55+j*.34,.30)
                if 62<x<1849 and 145<y<996 and q>.004:
                    g.dot(x,y,27,None,q*.73,TEAL,2.2)
                    g.dot(x,y,4.0,TEAL,q)
                if j==0 or q<.005:continue
                x0,y0=tr.steps[j-1]
                dx,dy=x-x0,y-y0
                length=math.hypot(dx,dy)
                if length<53 or y0>1040 or y<135:continue
                dx,dy=dx/length,dy/length
                u=appear(t,56.64+j*.34,.52)
                g.line(((x0+31*dx,y0+31*dy),(x-35*dx,y-35*dy)),TEAL,u*.36,1.9)
                x1,y1=x-35*dx,y-35*dy
                g.line(((x1-11*dx-6*dy,y1-11*dy+6*dx),(x1,y1),(x1-11*dx+6*dy,y1-11*dy-6*dx)),TEAL,u*.82,2.2)
        g.little('SINGLE TRACKWAY • CGI EXAMPLE',.90)
    return Image.alpha_composite(im.convert('RGBA'),g.layer).convert('RGB')


def compile_native():
    CACHE.mkdir(parents=True,exist_ok=True)
    p=NATIVE.with_suffix('.new')
    subprocess.run(['g++','-std=c++17','-O3','-ffast-math','-march=native','-fopenmp','-Wall','-Wextra','-Werror',str(HERE/'render3d.cpp'),'-o',str(p)],check=True)
    p.replace(NATIVE)


def part_dir():
    h=hashlib.sha256()
    sources=['picture.py','render3d.cpp','prepare_terrain.py','pilot-assets.json']
    for f in sources:
        h.update((HERE/f).read_bytes())
    for n in ('modern','ancient','brazil','koum','shelves','river','floodplain','steps','stamp'):
        h.update(hashfile(PACK/f'{n}.field').encode())
    for n in ('Fraunces.ttf','PlexSans.ttf','PlexMono.ttf'):
        h.update(hashfile(FONTS/n).encode())
    return CACHE/f'picture-{h.hexdigest()[:14]}'


def engine(size,lo,hi,trace):
    return [str(NATIVE),str(PACK),*map(str,size),str(lo),str(hi),str(trace)]


def proof():
    q=CACHE/'qa';q.mkdir(parents=True,exist_ok=True)
    poses=(0,1.23,3.16,4.92,7.92,9.88,10.84,11.79,16.83,18.96,21.98,25.24,28.98,31.43,34.59,38.73,42.28,
           46.27,49.45,51.60,54.12,57.87,60.52)
    for n in range(3):
        batch=poses[n*9:n*9+9]; canvas=Image.new('RGB',(1320,271*((len(batch)+2)//3)),INK);d=ImageDraw.Draw(canvas)
        for i,t in enumerate(batch):
            f=round(t*FPS); tr=q/f'comp-{f:04d}.csv';sz=(864,486)
            px=subprocess.check_output(engine(sz,f,f+1,tr))
            with tr.open() as src: view=composition(Image.frombytes('RGBA',sz,px),Trace.read(src))
            view.save(q/f'comp-{f:04d}.jpg',quality=93)
            xy=(i%3*440,i//3*271);canvas.paste(view.resize((440,248),Image.Resampling.LANCZOS),xy)
            d.text((xy[0]+10,xy[1]+250),f'{t:.2f}s',fill=CREAM)
        canvas.save(q/f'comp-board-{n+1}.jpg',quality=91)


def native_size(k):
    return GEOSIZE if k in (2,3,5) else NEAR if k in (0,1) else LOCAL


def part(path,k,lo,hi):
    trace=path.with_suffix('.csv'); tr=path.with_suffix('.pending.csv');tmp=path.with_suffix('.pending.mp4')
    size=native_size(k); n=4*math.prod(size)
    cmd=[FF,'-hide_banner','-loglevel','error','-nostdin','-y','-f','rawvideo','-pixel_format','rgb24','-framerate',str(FPS),
         '-video_size',f'{size[0]}x{size[1]}','-i','-','-an','-filter_threads','1',
         '-vf','scale=1920:1080:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p',
         '-c:v','libx264','-threads','1','-preset','fast','-crf','17.8','-maxrate','8700k','-bufsize','11500k',
         '-profile:v','high','-bf','0','-g','48','-keyint_min','24','-color_range','tv','-colorspace','bt709',
         '-color_trc','bt709','-color_primaries','bt709','-video_track_timescale',str(CLOCK),'-movie_timescale',str(CLOCK),str(tmp)]
    env={**os.environ,'OMP_NUM_THREADS':os.environ.get('OMP_NUM_THREADS','2')}
    with subprocess.Popen(engine(size,lo,hi,tr),stdout=subprocess.PIPE,env=env) as native, \
         subprocess.Popen(cmd,stdin=subprocess.PIPE) as encoder:
        assert native.stdout and encoder.stdin
        first=native.stdout.read(n)
        if len(first)!=n:raise RuntimeError(f'render engine ended before shot {k+1}')
        with tr.open('r') as reader:
            raw=first
            for frame in range(lo,hi):
                assert len(raw)==n,(frame,len(raw),n)
                view=Trace.read(reader)
                assert view.frame==frame and view.shot==k
                im=composition(Image.frombytes('RGBA',size,raw),view)
                encoder.stdin.write(im.tobytes())
                if frame+1<hi: raw=native.stdout.read(n)
            assert not native.stdout.read(1)
        encoder.stdin.close()
        assert native.wait()==0 and encoder.wait()==0
    tr.replace(trace);tmp.replace(path)


def render(only):
    base=part_dir();base.mkdir(parents=True,exist_ok=True)
    print(f'3D plates: {base}',flush=True)
    for k,(lo,hi) in enumerate(zip(FRAMES,FRAMES[1:])):
        if only and (k+1) not in only:continue
        p=base/f'{k+1:02d}.mp4'
        if p.exists() and p.with_suffix('.csv').exists():continue
        s=time.monotonic(); part(p,k,lo,hi)
        print(f'{k+1:02d} / {len(SHOT_NAMES)}  {lo/FPS:.3f}–{hi/FPS:.3f}  {SHOT_NAMES[k]}  {time.monotonic()-s:.1f}s',flush=True)
    if all((base/f'{k+1:02d}.mp4').exists() for k in range(len(SHOT_NAMES))):
        v=['ffconcat version 1.0']
        for i,(lo,hi) in enumerate(zip(FRAMES,FRAMES[1:]),1):
            v += [f"file '{i:02d}.mp4'",f'duration {(hi-lo)/FPS:.9f}']
        p=base/'concat.ffconcat'; p.write_text('\n'.join(v)+'\n')
        print('PICTURE_READY',p,flush=True)


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--proof',action='store_true');cli.add_argument('--only',nargs='+',type=int)
    a=cli.parse_args()
    assert not a.only or all(1<=s<=len(SHOT_NAMES) for s in a.only)
    compile_native()
    if a.proof:proof()
    else:render(a.only)


if __name__=='__main__':main()
