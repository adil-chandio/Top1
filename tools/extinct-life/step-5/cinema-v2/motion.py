#!/usr/bin/env python3
"""Lens finishing, world-tracked graphics, kinetic type, and shot encoding."""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import time

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from geometry import CACHE, FONTS, HERE, QA, compile_renderer, engine, geometry_key, raw_dir, sizes, base
from cues import CUTS, CUES, FPS, FRAMES, SR, bound, smooth, ease_out, end_envelope

FF=imageio_ffmpeg.get_ffmpeg_exe()
SIZE=(1920,1080)
CREAM=(254,242,214); MINT=(170,244,224); AMBER=(251,189,109); SKY=(163,219,222)
SOFT=(229,237,225); DARK=(5,13,20); DUST=(248,221,174)
ANCHOR_NAMES=('Sousa track','Koum track','Modern Atlantic','125 Ma','Title','Koum dive','Four horizons','Mayo Rey','Footprint count','Foot contact','Trackway count','Local sequence')


def rgba(c,a):return (*c,round(bound(a)*255))


def scale_point(a,r):return tuple(int(round(x*r)) for x in a)


def mix_pt(a,b,q):return tuple(x+(y-x)*q for x,y in zip(a,b,strict=True))


class Trace:
    def __init__(self,raw):
        if isinstance(raw,str): raw=list(map(float,raw.strip().split(',')))
        assert len(raw)==113,len(raw)
        self.f=int(raw[0]);self.k=int(raw[1]);self.cam=raw[2:5]
        self.sites=[]; self.arc=[]
        for k in range(2):
            b=raw[5+k*44:5+(k+1)*44]; self.sites.append([tuple(b[:5]),tuple(b[5:10])])
            self.arc.append([(b[i]*1920,b[i+1]*1080) for i in range(10,44,2)])
        self.steps=[(raw[i]*1920,raw[i+1]*1080) for i in range(93,105,2)]
        self.layers=[(raw[i]*1920,raw[i+1]*1080) for i in range(105,113,2)]


@lru_cache(maxsize=110)
def face(n,kind):
    file={'head':'Fraunces.ttf','mono':'PlexMono.ttf','sans':'PlexSans.ttf','bold':'PlexSans.ttf','light':'PlexSans.ttf','metric':'PlexSans.ttf'}[kind]
    f=ImageFont.truetype(str(FONTS/file),n)
    if kind=='head':f.set_variation_by_axes([min(112,max(25,n)),595,10,0])
    elif kind!='mono':
        f.set_variation_by_axes([{'sans':460,'bold':640,'light':385,'metric':605}[kind],95 if kind=='metric' else 100])
    return f


@lru_cache(maxsize=380)
def glyph(s,n,kind,tracking):
    f=face(n,kind); p=max(3,round(n*.09));
    if tracking>0:
        widths=[f.getlength(x)+tracking for x in s]; w=round(sum(widths))+p*2+3
    else:w=math.ceil(max(f.getlength(s),f.getbbox(s)[2]))+p*2+4
    h=round(n*1.30)+p*2
    a=Image.new('L',(w,h));d=ImageDraw.Draw(a)
    if tracking>0:
        u=p
        # A common baseline; draw tracking without turning each letter into its own bounce.
        for x,z in zip(s,widths,strict=True):
            d.text((round(u),p+round(n*.90)),x,font=f,fill=255,anchor='ls')
            u+=z
    else:d.text((p,p+round(n*.90)),s,font=f,fill=255,anchor='ls')
    return a,a.filter(ImageFilter.GaussianBlur(max(1,n*.015))),p


@lru_cache(maxsize=1300)
def shutter(size,key,phase):
    """Soft animated matte in the shape layer (not opacity-only subtitles)."""
    w,h=size
    q=bound(phase/48)
    if q>=.999:return Image.new('L',size,255)
    u=ease_out(q)
    y,x=np.ogrid[0:1:h*1j,0:1:w*1j]
    if key=='rise':
        edge=1.07*u-.035
        m=np.broadcast_to(np.clip((edge-y)/.23+.09,0,1),(h,w))
    elif key=='title-rise':
        # Lead with visible letterforms, not the empty top padding of the
        # font bitmap. Each main title line actually moves on its sound frame.
        edge=.243+.825*u
        m=np.broadcast_to(np.clip((edge-y)/.18+.09,0,1),(h,w))
    elif key=='count':
        edge=1.19*u-.09
        m=np.clip((edge-(x*.86+y*.14))/.19+.08,0,1)
    else:
        edge=1.22*u-.11
        m=np.clip((edge-(x*.92+y*.08))/.172,0,1)
    return Image.fromarray(np.uint8(255*m))


class Gfx:
    def __init__(self,size,f,omit=None):
        self.w,self.h=size;self.s=size[0]/1920;self.f=f;self.omit=omit
        self.paper=Image.new('RGBA',size);self.d=ImageDraw.Draw(self.paper);self.on=set()

    def xy(self,p):return scale_point(p,self.s)

    def amt(self,tag):
        if tag==self.omit:return 0.
        c=CUES[tag]
        return bound((self.f-c.frame+1)/c.move)

    def mark(self,tag):
        u=self.amt(tag)
        if u:self.on.add(tag)
        return u

    def line(self,ps,c,a=1,width=2.5):
        if a>.003:self.d.line([self.xy(x) for x in ps],fill=rgba(c,a),width=max(1,round(width*self.s)),joint='curve')

    def path(self,points,p,c,a=1,width=2.3):
        if p<.0001 or a<.003:return
        ps=[points[0]]; t=p*(len(points)-1)
        for j in range(len(points)-1):
            if t>=j+1:ps.append(points[j+1]);continue
            if t>j:ps.append(mix_pt(points[j],points[j+1],t-j))
            break
        if len(ps)>1:self.line(ps,c,a,width)

    def circle(self,x,y,r,fill=None,rim=None,a=1,width=2.):
        if r<.5 or a<.003:return
        self.d.ellipse(self.xy((x-r,y-r,x+r,y+r)),fill=rgba(fill,a) if fill else None,
                       outline=rgba(rim,a) if rim else None,width=max(1,round(width*self.s)))

    def bar(self,x,y,w,h,c,a=1):
        if w<.7 or h<.7 or a<.004:return
        self.d.rounded_rectangle(self.xy((x,y,x+w,y+h)),radius=max(1,round(h*.25*self.s)),fill=rgba(c,a))

    def type(self,x,y,text,n,kind='sans',c=CREAM,tag=None,a=1,align='l',track=0,style='shutter',phase=None):
        if a<=.003:return
        p=self.mark(tag) if tag is not None else 1.0
        if phase is not None:p*=phase
        if p<=0:return
        g,shadow,pad=glyph(text,max(8,round(n*self.s)),kind,round(track*self.s,2))
        E=ease_out(p)
        # Overshoot has no collision against the picture; settling is over a handful of frames.
        drift=0 if tag is None else (1-E)*min(30,5+n*.21)
        dx=(-.29*drift if style!='rise' else -.15*drift)
        scale=(.925+.075*E + .012*math.sin(math.pi*p)*p) if style=='count' else 1.0
        if scale!=1:
            extent=(max(2,round(g.width*scale)),max(2,round(g.height*scale)))
            g=g.resize(extent,Image.Resampling.BICUBIC);shadow=shadow.resize(extent,Image.Resampling.BILINEAR)
        if p<.9999:
            blade=shutter(g.size,style,max(1,round(p*48)));g=ImageChops.multiply(g,blade);shadow=ImageChops.multiply(shadow,blade)
        if align=='r':x-=g.width/self.s-2*pad/self.s
        xy=self.xy((x+dx,y+drift));box=(xy[0]-pad,xy[1]-pad)
        # Side shadows give a clean edge over changing geographic exposure.
        def paste(mask,color,amount,offset=(0,0)):
            b=(box[0]+offset[0],box[1]+offset[1],box[0]+offset[0]+mask.width,box[1]+offset[1]+mask.height)
            if amount<.999: mask=mask.point(lambda x:round(amount*x))
            carrier=Image.new('RGBA',mask.size,color)
            carrier.putalpha(mask)
            self.paper.alpha_composite(carrier,dest=b[:2])
        paste(shadow,DARK,a*.68,(max(1,round(self.s)),max(1,round(2.2*self.s))))
        paste(g,c,a)

    def eyebrow(self,x,y,text,c=SKY,tag=None,a=1):
        self.type(x,y,text,22,'mono',c,tag,a,track=2.05,style='shutter')

    def tech(self,text,tag=None,a=1,align='l'):
        self.type(92 if align=='l' else 1828,1008,text,18,'mono',SOFT,tag,a,align,track=.52,style='shutter')

    def stroke(self,tag,x,y,extent,col=AMBER,a=1):
        p=ease_out(self.mark(tag))
        self.bar(x,y,extent*p,3.2,col,a*.90)
        if p and p<.999:self.circle(x+extent*p,y+1.6,3.9,fill=CREAM,a=a*(1-p))

    def local_title(self,tag,name,region,accent,origin=(94,788),a=1):
        x,y=origin
        self.stroke(tag,x,y-16,114,accent,a)
        self.eyebrow(x,y,region,accent,tag,a)
        self.type(x-2,y+43,name,66,'head',CREAM,tag,a,style='rise')

    def metric(self,tag,n,sub,x,y,col=AMBER,context=None,a=1):
        self.stroke(tag,x,y-8,127,col,a)
        if context:
            self.eyebrow(x,y+10,context,col,tag,a)
            y+=42
        self.type(x-5,y+4,n,110,'metric',col,tag,a,style='count')
        self.eyebrow(x+1,y+116,sub,CREAM,tag,a)

    def world_pin(self,q,tag,main,small,col,a=1,side=-1,old=False):
        px,py,lx,ly,visible=q
        if not visible or not .018<px<.982 or not .022<py<.977 or a<.005:return
        u=self.mark(tag)
        if not u:return
        x,y=px*1920,py*1080;v,w=lx*1920,ly*1080
        dx=(176 if old else 158)*side
        rail=min(1735,max(178,v+dx))
        y1=min(822,max(549 if old and side<0 else 336,w-107-(25 if old else 0)))
        turn=(v+(rail-v)*.51,y1+14)
        ps=((x,y),(v,w),turn,(rail,y1+14))
        self.path(ps,ease_out(u),DARK,.81*a,7.)
        self.path(ps,ease_out(u),col,.96*a,2.4)
        pulse=(2.0+22*ease_out(u));self.circle(x,y,pulse,None,col,.75*a*(1-.67*u),2.4)
        self.circle(x,y,10.0,None,col,.82*a*ease_out(u),2.0)
        self.circle(x,y,4.9,col,None,a*ease_out(u))
        align='l' if side<0 else 'r'
        lx2=max(96,rail-181) if side<0 else min(1825,rail+199)
        self.type(lx2,y1-29,small,19,'mono',col,tag,.98*a,align,.72)
        self.type(lx2,y1+2,main,41,'bold',CREAM,tag,a,align,style='rise')

    def distance_bracket(self,nodes,tag,c,a=1):
        u=self.mark(tag)
        if not u:return
        # Equal-half build with no arrows: the curve depicts separation, not travel.
        n=len(nodes)-1
        for i in range(n):
            judge=abs((i+.5)/n-.5)*2
            beam=smooth((u-judge*.65)/.30)*a
            if beam<.004:continue
            q,r=nodes[i],nodes[i+1];b=mix_pt(q,r,.76 if n>10 else .70)
            self.line((q,b),DARK,.75*beam,7.)
            self.line((q,b),c,.98*beam,3.5)
            if .05<beam<.97:self.circle(*b,3.2,c,None,beam*.74)
        if len(nodes)>2:
            for q in (nodes[0],nodes[-1]):
                self.circle(*q,9.3,None,c,.64*a*ease_out(u),2.)


def geo(g,tr):
    f,k=tr.f,tr.k
    if k==2:
        a=end_envelope(f,FRAMES[3],8)
        g.stroke('orbit',93,91,91,SKY,a)
        g.eyebrow(93,108,'PRESENT DAY',MINT,'orbit',a)
        g.type(90,154,'Atlantic Ocean',76,'head',CREAM,'orbit',a,style='rise')
        g.metric('distance-now','≈6,000 km','APART TODAY',92,352,AMBER,a=a)
        g.distance_bracket(tr.arc[0],'distance-now',AMBER,a)
        g.world_pin(tr.sites[0][0],'sousa-pin','Sousa Basin','BRAZIL',AMBER,a,-1)
        g.world_pin(tr.sites[0][1],'koum-pin','Koum Basin','CAMEROON',MINT,a,1)
        g.tech('REGIONAL SEPARATION  /  RELIEF EXAGGERATED','orbit',a,'r')
    elif k==3:
        a=end_envelope(f,CUES['model-lock'].frame+2,6)
        g.eyebrow(94,111,'GEOLOGIC REWIND',MINT,'rewind',a)
        m=ease_out(g.amt('rewind'))
        raw=(0. if g.omit=='rewind' else
             bound((f-CUES['rewind'].frame+1)/float(CUES['model-lock'].frame-CUES['rewind'].frame)))
        g.line([(96,157),(96+268*m,157)],MINT,a*.49,2)
        g.bar(96,155,268*raw,3.7,MINT,a*.98)
        for i in range(7): g.line([(96+44.6*i,167),(96+44.6*i,177)],MINT,a*.48*m,1.8)
        ah=end_envelope(f,FRAMES[4]+5,10)
        g.stroke('model-lock',93,91,105,MINT,ah)
        g.eyebrow(93,108,'EARLY CRETACEOUS',MINT,'model-lock',ah)
        g.type(91,149,'125 million',73,'head',CREAM,'model-lock',ah,style='rise')
        g.type(91,229,'years ago',73,'head',CREAM,'model-lock',ah,style='rise')
        g.type(95,319,'Model snapshot, not footprint dates',29,'light',SOFT,'model-lock',ah)
        g.metric('distance-then','≈1,000 km','THEN  /  STUDY ESTIMATE',94,373,MINT,a=ah)
        g.distance_bracket(tr.arc[1],'distance-then',MINT,ah)
        g.world_pin(tr.sites[1][0],'sousa-past','Sousa region','FUTURE BRAZIL',AMBER,ah,-1,True)
        g.world_pin(tr.sites[1][1],'koum-past','Koum region','FUTURE CAMEROON',MINT,ah,1,True)
        g.tech('PALEOMAP COASTS + PALEODEMS · CC BY 4.0','model-lock',ah,'r')
    else:
        ao=end_envelope(f,FRAMES[6],10)
        g.local_title('approach','Koum Basin','NORTHERN CAMEROON',MINT,(94,116),ao)
        g.tech('PRESENT DAY  /  REGIONAL LOCATION','approach',ao,'r')
        x,y,_,_,visible=tr.sites[0][1];x*=1920;y*=1080;u=g.mark('local-fix');a=ao*ease_out(u)
        if visible and a>0:
            entry=ao*(.20+.80*ease_out(u))
            g.circle(x,y,6.6,CREAM,None,entry)
            g.circle(x,y,20.5,None,DARK,entry*.78,5.8)
            g.circle(x,y,20.5,None,MINT,entry*.91,2.8)
            g.circle(x,y,29+41*ease_out(u),None,MINT,a*(1-.79*u),2.2)
            paths=[[(x-47,y),(x-31,y)],[(x+31,y),(x+47,y)],[(x,y-46),(x,y-30)],[(x,y+31),(x,y+47)]]
            for r in paths:g.path(r,ease_out(u),MINT,a*.78)


def title(g,f):
    a=end_envelope(f,FRAMES[5],16)
    g.stroke('title-one',95,341,170,AMBER,a)
    g.eyebrow(95,291,'E X T I N C T   L I F E',AMBER,'title-one',a)
    g.type(94,376,'Why These Dinosaur',102,'head',CREAM,'title-one',a,style='title-rise')
    g.type(94,481,'Footprints Are',102,'head',CREAM,'title-two',a,style='title-rise')
    g.type(94,586,'an Ocean Apart',102,'head',DUST,'title-three',a,style='title-rise')
    g.tech('ILLUSTRATIVE ANCIENT FLOODPLAIN','title-three',a*.95)


def grow_step(g,tr,i,x,y):
    name=f'step-{i+1}';u=g.mark(name)
    if u<=0:return
    light=ease_out(u);a=.80
    if 39<x<1881 and 125<y<1053:
        # The small number stays adjacent to the actual recessed step, never above it as a card.
        g.circle(x,y,15.5,None,DARK,light*.79,5.5)
        g.circle(x,y,15.5,None,MINT,light*.91,2.9)
        g.circle(x,y,24+11*light,None,MINT,a*light*(.73-.62*u),2.7)
        g.circle(x,y,4.9,CREAM,None,light*.96)
        g.line(((x+18,y-6),(x+36,y-14)),DARK,.72*light,4.0)
        g.line(((x+18,y-6),(x+36,y-14)),MINT,.69*light,2.0)
        g.type(x+43,y-28,f'{i+1:02}',23,'mono',CREAM,name,.95)
    if i>0:
        src=np.array(tr.steps[i-1]);dst=np.array((x,y));d=dst-src
        if np.linalg.norm(d)>58:
            v=d/np.linalg.norm(d);a1=src+34*v;b1=dst-36*v
            end=a1+(b1-a1)*light
            g.line((a1,end),MINT,.40*light,2.1)
            if light>.38:
                q=end-12*v;q1=q+6*np.array((v[1],-v[0]));q2=q-6*np.array((v[1],-v[0]))
                g.line((q1,end,q2),MINT,.90*light,2.5)


def local(g,tr):
    f,k=tr.f,tr.k
    if k in (0,1):
        a=end_envelope(f,FRAMES[k+1]+2,6); key='brazil' if k==0 else 'cameroon'; col=AMBER if k==0 else MINT
        g.local_title(key,'Sousa Basin' if not k else 'Koum Basin',key.upper(),col,(95,802),a)
        g.tech('CGI ILLUSTRATION  /  NOT SPECIMEN IMAGERY',key,a*.86)
    elif k==4:title(g,f)
    elif k==6:
        g.metric('four-surfaces','4','TRACK-BEARING SURFACES',95,162,AMBER)
        for j,(x,y) in enumerate(tr.layers,1):
            tag=f'layer-{j}';u=g.mark(tag)
            if 100<y<974 and u:
                q=ease_out(u);edge=(x+109,y-23)
                g.circle(x,y,6.1,AMBER,None,q)
                g.circle(x,y,12+15*q,None,AMBER,.53*q*(1-u*.68),1.9)
                g.path(((x,y),(x+39,y-23),edge),q,AMBER,.92,2.6)
                g.type(x+117,y-35,f'{j:02}',21,'mono',CREAM,tag,.94)
        g.tech('SCHEMATIC GEOLOGY  /  FOUR SEPARATE SURFACES','four-surfaces',.92)
    elif k==7:
        a=end_envelope(f,FRAMES[8]+6,14)
        g.local_title('mayo-rey','Mayo Rey River','KOUM BASIN  /  CAMEROON',MINT,(96,800),a)
        g.tech('ILLUSTRATIVE RIVERBED  /  NOT FIELD FOOTAGE','mayo-rey',a*.91)
    elif k==8:
        g.metric('footprint-count','283','FOOTPRINTS STUDIED',93,163,MINT,context='AT ONE SITE')
        g.tech('2026 KOUM BASIN SURVEY  /  ILLUSTRATIVE TRACKS','footprint-count',.89)
    elif k==9:
        a=end_envelope(f,FRAMES[10]+5,10)
        g.local_title('footfall-type','One footfall','ONE ANIMAL',AMBER,(94,120),a)
        g.tech('ILLUSTRATIVE CONTACT  /  NO SPECIES IDENTIFICATION','footfall-type',a*.86)
    elif k==10:
        g.metric('trackway-count','34','DOCUMENTED TRACKWAYS',93,172,MINT)
        g.tech('KOUM SURVEY  /  ILLUSTRATIVE TRACKWAY','trackway-count',.94)
    else:
        g.local_title('sequence','Read the sequence','ON ONE PATCH OF GROUND',MINT,(94,124),1)
        for i,(x,y) in enumerate(tr.steps):grow_step(g,tr,i,x,y)
        g.tech('LOCAL DIRECTION  /  NOT A MIGRATION ROUTE','sequence',.90)


@lru_cache(maxsize=30)
def scrims(size,k):
    w,h=size; y,x=np.ogrid[0:1:h*1j,0:1:w*1j]
    if k in (0,1,7):
        m=.63*np.exp(-((x+.10)/.53)**2-((y-.88)/.30)**2)+.21*y**11
    elif k==4:
        m=.77*np.exp(-((x+.068)/.61)**2-((y-.476)/.54)**2)+.16*y**11
    elif k in (2,3,5):
        m=.725*np.exp(-((x+.072)/.47)**2-((y-.27)/.46)**2)+.17*y**11
    else:
        m=.70*np.exp(-((x+.076)/.48)**2-((y-.13)/.37)**2)+.22*y**12
    return Image.fromarray(np.uint8(np.minimum(1,m)*255))


@lru_cache(maxsize=20)
def lut(k):
    tables=[];x=np.linspace(0,1,256)
    shadow=(1-x)**3.81; glow=np.clip((x-.2)/.82,0,1)**1.72
    mul=(1.011,1.006,.976) if k in (0,4,7) else (1.006,1.026,1.012)
    if k in (2,3,5):mul=(1.023,1.025,1.010)
    for i,m in enumerate(mul):
        effect=np.clip(x**(1.06 if k in (4,7) else 1.035)*m + ([-.004,.007,.013][i])*shadow + ([.021,.009,-.007][i])*glow,0,1)
        tables.extend(np.around(effect*255).astype(int).tolist())
    return tables


def compose(src,tr,trace=False,omit=None):
    k=tr.k; size=src.size; scale=size[0]/1920
    pic=src.convert('RGB')
    if k not in (2,3,5):
        c=src.getchannel('A')
        m=c.point(lambda x:min(230,round(x*.86)))
        small=pic.filter(ImageFilter.GaussianBlur((3.4 if k in (0,1,9) else 2.9)*scale))
        pic=Image.composite(small,pic,m)
        if k in (0,1,9):
            m=c.point(lambda x: max(0,round((x-84)*.86)))
            pic=Image.composite(small.filter(ImageFilter.GaussianBlur(5.1*scale)),pic,m)
    pic=pic.point(lut(k))
    # Only lens-addressed highlights bloom: not a flash over the subtitles or an effect covering the geography.
    glow=k in (0,1,3,4,7,9)
    if glow:
        p=pic.convert('L').resize((size[0]//3,size[1]//3),Image.Resampling.BILINEAR)
        a=(.50 if (k==3 and tr.f<CUES['model-lock'].frame) else .31 if k==4 else .21)
        m=p.point(lambda x:round(max(0,x-147)*a)).filter(ImageFilter.GaussianBlur(8.2*scale)).resize(size,Image.Resampling.BILINEAR)
        pic.paste((226,246,240) if k==3 else (255,232,183),None,m)
    pic.paste(DARK,(0,0,*size),scrims(size,k))
    g=Gfx(size,tr.f,omit)
    if k in (2,3,5):geo(g,tr)
    else:local(g,tr)
    result=Image.alpha_composite(pic.convert('RGBA'),g.paper).convert('RGB')
    return (result,g.on) if trace else result


def enc_dir():
    h=sha256(geometry_key().encode())
    for p in (HERE/'motion.py', HERE/'cues.py', FONTS/'PlexSans.ttf',FONTS/'PlexMono.ttf',FONTS/'Fraunces.ttf'):
        h.update(base.hashfile(p).encode())
    return CACHE/f'encoded-{h.hexdigest()[:14]}'


def ffconcat(out):
    paths=sorted(out.glob('[0-9][0-9].mp4'));a=['ffconcat version 1.0']
    if len(paths)!=len(FRAMES)-1:return False
    for i,path in enumerate(paths):
        a+=[f"file '{path.name}'",f'duration {(FRAMES[i+1]-FRAMES[i])/FPS:.9f}']
    p=out/'concat.ffconcat';p.write_text('\n'.join(a)+'\n');print('PICTURE_READY',p,flush=True)
    return True


def encode(only=None,available=False):
    raw=raw_dir();out=enc_dir();out.mkdir(parents=True,exist_ok=True)
    print('FINISHING_SET',out,flush=True)
    for i,(lo,hi) in enumerate(zip(FRAMES,FRAMES[1:]),1):
        if only and i not in only:continue
        dst=out/f'{i:02d}.mp4';tn=out/f'{i:02d}-events.json';path=raw/f'{i:02d}.rgba';tr=raw/f'{i:02d}.csv'
        if dst.is_file() and tn.is_file():continue
        if not path.is_file() or not tr.is_file():
            if available:continue
            raise FileNotFoundError(f'clean shot {i} is not ready')
        w,h=sizes(i-1); b4=w*h*4; assert path.stat().st_size==(hi-lo)*b4
        s=time.monotonic();tmp=dst.with_suffix('.pending.mp4')
        cmd=[FF,'-hide_banner','-loglevel','error','-y','-nostdin','-f','rawvideo','-pixel_format','rgb24','-framerate',str(FPS),
             '-video_size',f'{w}x{h}','-i','-','-an','-filter_threads','1','-vf','scale=1920:1080:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p',
             '-c:v','libx264','-threads','1','-profile:v','high','-preset','fast','-crf','16.7','-maxrate','9300k','-bufsize','13200k',
             '-g','48','-keyint_min','24','-bf','0','-color_range','tv','-colorspace','bt709','-color_trc','bt709','-color_primaries','bt709',
             '-video_track_timescale',str(SR),'-movie_timescale',str(SR),str(tmp)]
        starts={}
        with path.open('rb') as rgba_file, tr.open('r') as trace, subprocess.Popen(cmd,stdin=subprocess.PIPE) as p:
            assert p.stdin
            for f in range(lo,hi):
                B=rgba_file.read(b4);j=Trace(trace.readline());assert len(B)==b4 and j.f==f and j.k==i-1
                im,events=compose(Image.frombytes('RGBA',(w,h),B),j,True)
                for key in events:starts.setdefault(key,f)
                p.stdin.write(im.tobytes())
            p.stdin.close();assert p.wait()==0 and not rgba_file.read(1) and not trace.read(1)
        expected={c.id:c.frame for c in CUTS if c.show and lo<=c.frame<hi}
        assert starts==expected,(i,expected,starts)
        tn.write_text(json.dumps(starts,indent=2)+'\n')
        tmp.replace(dst)
        print(f'ENCODED_SHOT {i:02d} {ANCHOR_NAMES[i-1]} {time.monotonic()-s:.1f}s',flush=True)
    ffconcat(out)


def proofs():
    QA.mkdir(exist_ok=True,parents=True)
    sec=(0.61,1.33,3.10,5.6,6.38,8.83,10.77,11.74,13.33,15.79,18.83,19.92,21.18,23.17,
         29.33,32.57,34.91,37.83,40.21,46.21,49.46,50.75,54.30,56.97,58.69,60.54)
    for i in range(3):
        tests=sec[i*9:i*9+9]; sheet=Image.new('RGB',(1320,271*((len(tests)+2)//3)),DARK);pen=ImageDraw.Draw(sheet)
        for j,t in enumerate(tests):
            f=round(t*FPS);tr=QA/f'comp2-{f:04d}.csv';size=(864,486)
            raw=subprocess.check_output(engine(size,f,f+1,tr)); r=compose(Image.frombytes('RGBA',size,raw),Trace(tr.read_text()));r.save(QA/f'comp2-{f:04d}.jpg',quality=93)
            p=(j%3*440,j//3*271);sheet.paste(r.resize((440,248),Image.Resampling.LANCZOS),p)
            pen.text((p[0]+9,p[1]+251),f'{f/FPS:06.3f}s · frame {f}',fill=CREAM)
        sheet.save(QA/f'motion-proof-{i+1}.jpg',quality=92)


def main():
    c=argparse.ArgumentParser(description=__doc__);c.add_argument('--proof',action='store_true');c.add_argument('--available',action='store_true');c.add_argument('--only',nargs='+',type=int);a=c.parse_args()
    if a.proof:
        if not (CACHE/'render-cinema').exists():compile_renderer()
        proofs()
    else:encode(a.only,a.available)


if __name__=='__main__':main()
