"""Cinematic titles and pin labels, kept separate from the locked subtitle track."""
from functools import lru_cache
import math

import numpy as np
from PIL import Image

import graphics as ic
from common import F, FPS, BY
from film_picture import FilmType, pin
from motion import AMBER, CREAM, MINT, DARK

MAPS = (2,3,5,34,46,48,51,53,59,61)
MAP_SEQS={46:('RESTORE THE LAND','Gondwana','125 MA MODEL  ·  NOT A FOOTPRINT DATE'),
          48:('BEDROCK & FAULTS','Linked geology','2024 INTERPRETATION'),
          51:('CONNECTED LAND','Before the ocean','125 MA MODEL'),
          53:('A POSSIBLE DISPERSAL AREA','Habitat, not a trail','HYPOTHESIS  ·  NOT A TRACED ROUTE'),
          59:('THE LIMIT OF THE EVIDENCE','A possible route','NOT AN INDIVIDUAL JOURNEY')}


def ismap(k,f):return k in MAPS or (k==56 and f>=F[k]+133) or (k==58 and f<BY['better-dates'].f)


@lru_cache(maxsize=16)
def mask(size,mode):
    w,h=size
    y,x=np.ogrid[0:1:h*1j,0:1:w*1j]
    if mode=='globe':
        a=.62*np.exp(-((x+.13)/.52)**2-((y-.135)/.33)**2)+.36*np.exp(-((y+.06)/.245)**2)
    elif mode=='title':
        a=.68*np.exp(-((x+.09)/.65)**2-((y-.39)/.59)**2)+.09*np.exp(-((y+.08)/.23)**2)
    elif mode=='field':
        a=.31*np.exp(-((y+.045)/.24)**2)+.14*np.exp(-((y-1.04)/.18)**2)
    else:
        a=.31*np.exp(-((y+.10)/.30)**2)+.09*np.exp(-((y-1.04)/.20)**2)
        a=np.broadcast_to(a,(h,w))
    a=np.broadcast_to(a,(h,w))
    return Image.fromarray(np.rint(np.clip(a,0,.88)*255).astype(np.uint8))


def map_pin(g,p,label,tone,side,a=1):
    if not (p[2]>0 and 75<p[0]<1840 and 86<p[1]<892) or a<.01:return
    x,y=p[:2]
    pin(g,p,tone,a)
    if x<390:side=1
    if x>1510:side=-1
    down=-1 if y>779 else 1
    yy=y+down*62
    xx=x+side*72
    g.line(((x,y+down*17),(x,y+down*32),(x+side*35,yy),(xx,yy)),tone,a*.68,2.1)
    shift=11 if side>0 else -11
    ic.txt(g,xx+shift,yy-20,label,34,CREAM,a,'l' if side>0 else 'r',kind='bold')


def dist(g,tr,col,a):
    if any(p[2]<=0 for p in tr[:2]) or a<.015:return
    a0=np.asarray(tr[2:],np.float32)[:,:2];u0=np.linspace(0,1,len(a0))
    def p(t):return (float(np.interp(t,u0,a0[:,0])),float(np.interp(t,u0,a0[:,1])))
    n=15 if math.dist(a0[0],a0[-1])>220 else 8
    for i in range(n):
        x,y=(i+.19)/n,(i+.73)/n
        g.line((p(x),p(y)),DARK,a*.74,6.2);g.line((p(x),p(y)),col,a*.94,2.65)


def geographic(g,k,f,tr,t):
    old=k not in (2,5,34,61) and (k!=3 or f>=BY['old-lock'].f)
    if k==3 and not old:
        a=ic.step(t,0,.18)*(1-ic.step(t,.87,1.25))
        ic.caps(g,92,68,'PRESENT DAY → 125 MILLION YEARS AGO',MINT,a,25)
        ic.txt(g,90,110,'Rewind the map',72,CREAM,a)
        ic.caps(g,94,214,'TWO GEOGRAPHIC SNAPSHOTS',CREAM,a,23)
        return
    if k in (2,3,61):
        a=ic.step(t,1.25,1.68) if k==3 else ic.step(t,0,.29)
        head='125 MILLION YEARS AGO' if old else 'PRESENT DAY'
        title='Gondwana' if old else 'Atlantic Ocean'
        c=MINT if old else AMBER
        ic.caps(g,92,64,head,c,a,25)
        ic.txt(g,87,107,title,78,CREAM,a)
        ic.caps(g,94,208,'MODEL SNAPSHOT  ·  NOT A FOOTPRINT DATE' if old else 'TWO REGIONS. ONE OCEAN BETWEEN THEM.',CREAM,a*.84,20)
        key='then' if old else 'gap-returns' if k==61 else 'now'
        b=ic.cue(f,key,.38)
        x=1828;y=111
        ic.caps(g,x,y-40,'APPROX. REGIONAL SEPARATION',CREAM,b*.88,21,'r')
        ic.txt(g,x,y,'≈1,000 km' if old else '≈6,000 km',81,c,b,'r',kind='metric')
        dist(g,tr,c,b*.94)
        for i,(p,label,col) in enumerate(zip(tr[:2],('Sousa','Koum region'),(AMBER,MINT))):map_pin(g,p,label,col,1 if i else -1,a)
    elif k in (5,34):
        i=int(k==5);c=MINT if i else AMBER;a=ic.step(t,.04,.42)
        ic.caps(g,92,61,'MODERN GEOGRAPHY  /  LOCATOR',c,a,23)
        ic.txt(g,87,105,'Northern Cameroon' if i else 'Northeast Brazil',72,CREAM,a)
        map_pin(g,tr[i],'Koum Basin region' if i else 'Sousa Basin',c,1 if i else -1,(ic.step(t,.20,.88) if i else ic.cue(f,'brazil',.38)))
    elif k in MAP_SEQS:
        head,title,foot=MAP_SEQS[k];a=ic.step(t,0,.42)
        ic.caps(g,92,62,head,MINT,a,23)
        ic.txt(g,88,110,title,71,CREAM,a)
        ic.caps(g,94,213,foot,CREAM,a*.9,20)
        for i,(p,label,col) in enumerate(zip(tr[:2],('Sousa region','Koum region'),(AMBER,MINT))):map_pin(g,p,label,col,1 if i else -1,a*.96)
    elif k==56:
        a=ic.step(t,5.54,5.98)
        ic.caps(g,92,68,'COMPARE THE DISTRIBUTIONS',MINT,a,24)
        ic.txt(g,89,110,'Other basins',76,CREAM,a)
        ic.caps(g,93,218,'NOT THE FOOTPRINT SITES  ·  NO ROUTE SHOWN',CREAM,a,22)
    elif k==58:
        ic.caps(g,92,68,'WHAT WOULD TEST IT?   /   01',MINT,1,24)
        a=ic.cue(f,'more-sites',.41)
        ic.txt(g,88,113,'More sites',79,CREAM,a)
        ic.caps(g,93,220,'FUTURE EVIDENCE, NOT DISCOVERIES',CREAM,1,22)
        a0=tr[0];b=tr[1]
        if a>0 and a0[2]>0 and b[2]>0:
            x,y=((a0[0]+b[0])*.5,(a0[1]+b[1])*.5-62)
            g.circle(x,y,34,ic.INK,MINT,a*.87,2.4);ic.centre(g,x,y-25,'?',38,MINT,a,'bold')


def title(g,f,t):
    a=ic.step(t,.04,.47)*(1-ic.step(t,4.38,5.64));x=90
    g.line(((x+3,327),(x+140,327)),AMBER,.9*a,3.5)
    ic.caps(g,x+5,278,'EXTINCT LIFE   /   A FOSSIL INVESTIGATION',AMBER,.97*a,22)
    ic.txt(g,x-3,362,'Atlantic Tracks',145,CREAM,a)
    ic.txt(g,x+4,521,'Why These Dinosaur Footprints',54,CREAM,a)
    ic.txt(g,x+4,603,'Are an Ocean Apart',54,CREAM,a)
    ic.caps(g,x+4,859,'ILLUSTRATIVE ANCIENT FLOODPLAIN',CREAM,ic.step(t,4.59,5.18)*.96,21)


def dating(g,k,f,t):
    final=k==45
    a=ic.cue(f,'age',.45) if final else ic.step(t,.04,.46)
    ic.eyebrow(g,'DATING THE BEDS  /  '+('02' if final else '01'),'SCHEMATIC  ·  NO MEASURED ENDPOINTS',MINT,ic.step(t,0,.4))
    if a<.005:return
    panel=(26,51,58) if final else (39,55,62)
    ic.rect(g,825,132,1839,837,panel,a*.98)
    g.line(((826,837),(826,132),(884,132)),MINT if final else AMBER,a*.88,2.4)
    g.line(((1797,837),(1839,837),(1839,802)),CREAM,a*.46,2.4)
    ic.txt(g,875,175,'Early Cretaceous' if final else 'A window, not a date',72,CREAM,a)
    ic.caps(g,879,273,'THE TWO BEDS ARE BROADLY DATED' if final else 'A PROVISIONAL RANGE FOR EACH BED',CREAM,a*.77,22)
    x0,x1=883,1774
    reveal=ic.step(t,.72,1.42) if final else ic.cue(f,'window-low',.74)
    if not final:
        ic.caps(g,x0,342,'OLDER',ic.GREY,a,19);ic.caps(g,x1,342,'YOUNGER',ic.GREY,a,19,'r')
    else:
        ic.caps(g,x0,342,'BROAD EARLY CRETACEOUS ASSIGNMENT',ic.GREY,a,18)
    for i,(y,name,c) in enumerate(((402,'Sousa region',AMBER),(534,'Koum region',MINT))):
        ic.txt(g,x0,y,name,35,CREAM,a,kind='bold')
        Y=y+65
        g.line(((x0,Y),(x1,Y)),CREAM,a*.22,1.6)
        aa=reveal if i==0 else ic.step(reveal,.10,.92)
        # Soft, independently unresolved ends; no date pins or numerical scale.
        B,E=((.031,.91) if i==0 else (.10,.979)) if final else ((.031,.73) if i==0 else (.27,.964))
        p0=x0+(x1-x0)*B; r=(x1-x0)*(E-B)
        for j in range(40):
            u=j/40; v=(j+1)/40
            opacity=(.92*ic.step(u,0,.20)*(1-ic.step(v,.80,1))+.07)*a*ic.step(aa,u,min(1.,u+.17))
            if opacity>.003:
                col=tuple(round(b+(d-b)*(opacity/max(a,.005))) for b,d in zip(panel,c,strict=True))
                ic.rect(g,p0+u*r,Y-12,p0+v*r+.7,Y+12,col,.98*a)
    ic.caps(g,x0,705,'OVERLAP DOES NOT MEAN THE SAME MOMENT' if final else 'A RANGE IS NOT A TIMESTAMP',CREAM,a*reveal,24)
    # The label and actual CG strata sit outside the chart and subtitle lane.
    ic.caps(g,104,355,'ILLUSTRATIVE ROCK SECTIONS',CREAM,a*.82,19)


def compose(im,k,f,tr):
    t=(f-F[k])/FPS
    m=ismap(k,f)
    mode='globe' if m else 'title' if k==4 else 'field' if k in (0,1,7,8,9,10,11,17,18,19,22,25,26,28,29,33,35,37,40,52,55,62,64) else 'stage'
    z=mask(im.size,mode)
    if k==4 and t>4.5:z=z.point(lambda v:int(v*(1-ic.step(t,4.5,5.88)*.70)))
    im.paste((10,17,23),None,z)
    g=FilmType(im.size,f)
    if m:geographic(g,k,f,tr,t)
    elif k==4:title(g,f,t)
    elif k in (42,45):dating(g,k,f,t)
    elif k==9:
        a=ic.step(t,.04,.36)*(1-ic.step(t,3.88,4.44))
        ic.eyebrow(g,'HOW A TRACK FORMS','ILLUSTRATIVE STEP  ·  NOT AN IDENTIFICATION',MINT,a)
    elif k==0:
        a=ic.cue(f,'sousa-open',.40)
        ic.caps(g,92,68,'01  /  NORTHEAST BRAZIL',AMBER,a,25)
        ic.txt(g,88,104,'Sousa Basin',70,CREAM,a)
        ic.caps(g,94,193,'RECONSTRUCTED FOOTPRINT SURFACE',CREAM,a*.9,20)
    elif k==65:
        ic.credits(g,f)
        # Replace the prior edition name with an accurate label.
        a=ic.cue(f,'credits-on',.37)*(1-ic.step(t,6.0,6.5))
        ic.rect(g,1370,38,1855,90,(14,25,31),a)
        ic.caps(g,1838,55,'CINEMA EDITION',CREAM,a,n=20,align='r')
    else:ic.overlays(g,k,f,tr,t)
    return Image.alpha_composite(im.convert('RGBA'),g.paper).convert('RGB')
