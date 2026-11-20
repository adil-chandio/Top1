"""Film typography, tracked visual explanations, and lab comparison plates.

Drawing coordinates are a 1920x1080 design grid. Projected ticks describe this
illustration; none is a measured force vector or a trace from study footage.
"""
from dataclasses import dataclass
from functools import lru_cache
from math import cos, pi, sin
import csv
import numpy as np
from PIL import Image
from titles import Panel, CREAM, COOL, AMBER, SEA, rgba, ease, settle, glyphs
from feature_cut import WORK

INK = (11,19,18)
FADED = (187,198,185)

@dataclass(frozen=True)
class Call:
    a:int
    b:int
    pre:str
    title:str
    tail:str=''
    x:int=120
    y:int=160
    size:int=79
    color:tuple=AMBER
    target:str=''
    shade:bool=True

CALLS = (
 Call(731,799,'01  /  ILLUSTRATIVE CGI','A dent in the sand',x=121,y=147,size=67),
 Call(812,879,'SAME PIT  /  RIM VIEW','A funnel',x=122,y=212,size=90,target='pit'),
 Call(913,984,'THE HUNTER','Antlion larva','Mostly hidden below the surface',x=116,y=155,size=73,target='pit'),
 Call(1194,1275,'SAND IN MOTION','UP',x=130,y=180,size=129),
 Call(1280,1335,'SAND IN MOTION','DOWN',x=130,y=180,size=119),
 Call(1366,1444,'LEGS WORK UPHILL','BODY SLIDES DOWN',x=112,y=111,size=67),
 Call(1584,1679,'THE SECOND JOB','Clear the floor',x=116,y=165,size=71),
 Call(1701,1810,'KEEP THE WALLS','Steep & loose',x=118,y=137,size=78),
 Call(2001,2110,'THE WORKER','Trap-jaw ant','Odontomachus brunneus',x=118,y=145,size=82,color=CREAM),
 Call(2224,2317,'02  /  THE JAW','A controlled grip','Muscle moves the jaw slowly',x=118,y=326,size=67,color=COOL,shade=False),
 Call(2346,2411,'THE LATCH','Locked open',x=117,y=302,size=85,target='hinge',color=COOL,shade=False),
 Call(2412,2533,'CUTAWAY  /  SCHEMATIC','Load the spring system','The jaw stays open while tissue deforms',x=118,y=304,size=63,target='shell',color=COOL,shade=False),
 Call(2537,2591,'STORED ENERGY  /  01','Head capsule bends',x=972,y=261,size=72,target='shell',color=COOL,shade=False),
 Call(2612,2681,'STORED ENERGY  /  02','Attachment stretches',x=115,y=247,size=59,target='attach',color=AMBER,shade=False),
 Call(2705,2823,'CUTAWAY  /  SCHEMATIC','Latch releases','Two elastic structures recoil',x=1003,y=293,size=75,color=COOL,shade=False),
 Call(2869,2997,'01  /  HEAD CAPSULE','PUSH',x=115,y=399,size=129,target='shell',color=COOL,shade=False),
 Call(3025,3137,'02  /  MUSCLE–APODEME','PULL',x=1104,y=405,size=129,target='attach',color=AMBER,shade=False),
 Call(3507,3597,'CLOSURE TIME ≠ FLIGHT TIME','The snap is not the jump',x=1058,y=160,size=57,color=COOL,shade=False),
 Call(3873,3938,'03  /  GROUND CONTACT','Aim the jaws',x=110,y=152,size=76,target='tip'),
 Call(4012,4078,'OBSERVED IN SOME TRIALS','A leg lifts first',x=1036,y=161,size=66,target='toe'),
 Call(4099,4261,'THOUGHT EXPERIMENT  /  OPEN AIR','No surface','The jaws close; the body does not launch.',x=113,y=283,size=79,color=COOL,shade=False),
 Call(4461,4512,'EJECTED GRAINS','The sand gives',x=111,y=166,size=75),
 Call(4566,4641,'AFTER CONTACT','No feet on the slope',x=111,y=125,size=65,color=CREAM),
 Call(4675,4749,'ACROSS THE RIM','Crossing the rim',x=110,y=163,size=71),
 Call(4902,4992,'THE DIFFERENCE','An outside push',x=112,y=175,size=73),
 Call(5085,5186,'ONE BOWL  /  DIFFERENT ENDINGS','Where does she land?',x=118,y=111,size=74),
 Call(5539,5620,'04  /  A JUMP CAN FAIL','Airborne ≠ out',x=108,y=154,size=95),
 Call(5631,5741,'LARABEE & SUAREZ  /  2015','117 lab trials','O. brunneus with three Myrmeleon species',x=110,y=149,size=92),
 Call(5744,5806,'OF 117 LAB TRIALS','About half','Ran out on foot',x=1113,y=178,size=91),
 Call(5810,5902,'OF 117 LAB TRIALS','15%','Jumped clear via a jaw strike',x=110,y=151,size=136),
 Call(5910,6000,'OF 117 LAB TRIALS','About one-third','Caught: held under sand for ≥60 s',x=1010,y=161,size=76),
 Call(6283,6394,'A SPECTACULAR ESCAPE IS NOT A CONTROL','Does the snap help?',x=113,y=171,size=74),
 Call(6491,6559,'05  /  TEST THE SNAP','Legs can still work',x=111,y=124,size=68,shade=False,color=COOL),
 Call(6704,6785,'HANDLED  /  RESTRAINT','Jaw tips held shut',x=990,y=163,size=76,target='tip',shade=False),
 Call(7100,7237,'HANDLING CONFOUND','Fewer running escapes','In both handled groups vs untouched',x=112,y=138,size=72),
 Call(7658,7748,'MOCK VS RESTRAINED','More jump escapes','Not better running',x=113,y=146,size=70),
 Call(7873,7986,'WHAT THE LAB SHOWED','Another way out','Not a guarantee, and not a field rate',x=113,y=145,size=84),
)

# Dark studio inserts retain the same accent colours as the pit. The handful of
# designed interventions live around, never on top of, jaw-to-sand contact.
SPECIALS = (
 (3143,3284,'Dual actuation'),(3322,3462,'Measured duration'),(5334,5500,'Collision and fall'),
 (6068,6175,'Outcome ledger'),(6399,6478,'Study layout preview'),
 (6559,6658,'Same legs, different jaws'),(6795,6920,'Mock vs restrained'),
 (6920,7087,'Three treatments'),(7240,7347,'Confounded reference'),
 (7347,7619,'Matched comparison'),(8317,8449,'Sand goes up'),(8507,8578,'Ant goes up'),
)
PROTECTED = ((4261,4430),(5188,5334),(8179,8295),(8774,8994))


@lru_cache(maxsize=1)
def marks():
    with (WORK/'projection.csv').open() as p:
        return {int(a['frame']):{k:float(v) for k,v in a.items() if k!='frame'} for a in csv.DictReader(p)}


def pt(f, name):
    k=marks()[f]
    return k[name+'_x']*1920,k[name+'_y']*1080


def width(s,size,mono=False,spacing=0,weight=700):
    return glyphs(s,size,weight,mono,spacing).width-12


def fade(a,b,f,entry=10,exit=8):
    return ease(a,min(a+entry,b-1),f)*(1-ease(b-exit,b,f))


@lru_cache(maxsize=60)
def pool_tile(w,h,x,y,rx,ry):
    a=((np.arange(w)[None,:]-x)/rx)**2
    b=((np.arange(h)[:,None]-y)/ry)**2
    # Feather the pool to zero at its tile edges, even against bright quartz.
    ix=np.arange(w);iy=np.arange(h)
    xx=np.clip(np.minimum(ix,w-1-ix)/max(1.,w*.15),0,1);yy=np.clip(np.minimum(iy,h-1-iy)/max(1.,h*.24),0,1)
    return Image.fromarray(np.uint8(255*np.maximum(0.,1.-a-b)**2*(xx*xx*(3-2*xx))[None,:]*(yy*yy*(3-2*yy))[:,None]))


def legend(p,pre,title,tail,x,y,o,e,size,col=AMBER,dy=14):
    p.word(pre,x,y-61,29,COOL if col==COOL else CREAM,mono=True,spacing=1.3,alpha=o*.9,show=min(1.,e*1.38))
    p.word(title,x,y+dy*(1-e),size,col,weight=680,spacing=-1.65,alpha=o,show=e,slant=.021)
    if tail:p.word(tail,x,y+size+23,32,CREAM,weight=500,alpha=o*ease(.24,.91,e),show=ease(.20,.93,e))
    def ink(line,dot):
        line([(x,y-80),(x+33*e,y-80)],rgba(col,.87*o),2.2)
        dot((x,y-80),3.3,rgba(col,.94*o))
    p.vector(ink)


def leader(p, f, target, x,y, e,o, col):
    px,py=pt(f,target)
    if not (26<px<1894 and 26<py<1054):return
    d=-1 if x>px else 1
    ax,ay=x,y
    bx,by=ax+min(83,abs(px-ax)*.52)*d,ay
    end = (px+(bx-px)*(1-e),py+(by-py)*(1-e))
    def v(line,dot):
        line([(ax,ay),(bx,by),end],rgba(INK,o*.40),6.0)
        line([(ax,ay),(bx,by),end],rgba(col,o*.79),2.35)
        if e>.87:
            dot((px,py),4.5,rgba(col,o*.94))
            dot((px,py),11.1,rgba(col,o*.73),outline=True)
    p.vector(v)


def callout(im,f,c,matte):
    opacity=fade(c.a,c.b,f);reveal=settle(c.a+2,c.a+18,f)
    if opacity<=.002:return
    w=max(width(c.title,c.size),width(c.pre,29,True,1.3),width(c.tail,32) if c.tail else 0)+62
    box=(max(0,c.x-95),max(0,c.y-107),min(1920,c.x+w+105),min(1080,c.y+c.size+183))
    p=Panel(im,box,matte if c.shade else None)
    if c.shade:
        px,py=p.pos(c.x+w*.31,c.y+c.size*.13)
        mask=pool_tile(p.layer.width,p.layer.height,round(px/p.r),round(py/p.r),int(max(440,w*.95)*p.r),int((220+c.size*.18)*p.r))
        # Cached half-tonal pools cannot cover the worker or its airborne grit.
        mask=mask.point(lambda n:round(n*.60*opacity));p.over(mask,INK,(0,0))
    legend(p,c.pre,c.title,c.tail,c.x,c.y,opacity,reveal,c.size,c.color)
    p.finish()
    if c.target:
        to=pt(f,c.target);right=to[0]>c.x+w*.5
        x=c.x+min(w-44,width(c.title,c.size)+26) if right else c.x-24
        y=c.y+c.size*.48
        if abs(to[0]-x)>43 and abs(to[1]-y)>13 and 26<to[0]<1894 and 26<to[1]<1054:
            p=Panel(im,(max(0,min(x,to[0])-26),max(0,min(y,to[1])-26),min(1920,max(x,to[0])+26),min(1080,max(y,to[1])+26)),None)
            leader(p,f,c.target,x,y,settle(c.a+11,c.a+30,f),opacity*.86,c.color);p.finish()
    if c.title in ('UP','DOWN'):
        p=Panel(im,(375,102,740,470),None);y=238
        v=settle(c.a+7,c.a+23,f);x=575 if c.title=='DOWN' else 397
        d=-1 if c.title=='UP' else 1
        def draw(l,dot):
            l([(x,y-28*d),(x,y+74*d*v)],rgba(c.color,opacity*.94),3.8)
            if v>.55:l([(x-16,y+(74*v-20)*d),(x,y+74*v*d),(x+16,y+(74*v-20)*d)],rgba(c.color,opacity*.94),3.8)
        p.vector(draw);p.finish()


def topology(im,f):
    if f<748 or f>=799:return
    o=fade(747,799,f,13,9);t=settle(750,778,f)
    x,y=pt(f,'pit'); p=Panel(im,(436,64,1571,1030),None)
    def layer(line,dot):
        for k,(a,b) in enumerate(((401,338),(295,244),(155,125))):
            N=int(t*61); phases=[1.3+k*.32+i/61*(pi*2) for i in range(N)]
            line([(x+a*cos(j)+30*sin(j),y+b*sin(j)) for j in phases],rgba(CREAM,o*(.42-k*.029)),2.3)
        dot((x,y),5,rgba(AMBER,.92*o));dot((x,y),15,rgba(AMBER,.73*o),True)
    p.vector(layer);p.finish()


def dual(im,f):
    e=settle(3145,3167,f);o=fade(3143,3284,f);p=Panel(im,(0,0,1920,1080),None)
    p.word('TWO ACTIONS',117,218,31,CREAM,mono=True,spacing=2.4,show=e,alpha=o)
    p.word('PUSH',112,299,100,COOL,show=e,alpha=o,slant=.027)
    p.word('+',407,325,64,CREAM,show=e,alpha=o*.75)
    p.word('PULL',478,299,100,AMBER,show=ease(3164,3189,f),alpha=o,slant=.029)
    p.word('Same jaw rotation',119,441,48,CREAM,show=settle(3204,3228,f),alpha=o)
    p.word('TWO CONTACTS  /  NOT TWO STRIKES',118,927,27,FADED,mono=True,spacing=1.25,show=e,alpha=o*.86)
    leader(p,f,'shell',650,267,settle(3151,3188,f),o*.88,COOL)
    leader(p,f,'attach',645,557,settle(3178,3203,f),o*.93,AMBER)
    p.finish()


def time_mark(im,f):
    o=fade(3322,3462,f,15,9);t=settle(3355,3384,f);p=Panel(im,(66,102,861,816),None)
    p.word('MEASURED CLOSURE TIME',114,214,28,COOL,mono=True,spacing=1.5,alpha=o,show=settle(3325,3342,f))
    p.word('77',103,289+(1-t)*15,161,CREAM,weight=700,slant=.021,show=t,alpha=o)
    p.word('µs',309,344,106,COOL,weight=600,show=settle(3375,3395,f),alpha=o)
    p.word('Mean, 0° to 90° jaw rotation',117,496,37,CREAM,show=settle(3394,3418,f),alpha=o)
    p.word('O. BRUNNEUS   /   SUTTON ET AL. 2022',119,624,25,FADED,mono=True,spacing=1.,show=settle(3411,3431,f),alpha=o)
    p.word('Illustration slowed for clarity',119,666,30,FADED,show=t,alpha=o)
    def rule(l,d):
        l([(118,581),(118+476*t,581)],rgba(COOL,o*.6),2.1)
        for j in range(5):
            if t*4>=j:l([(118+j*119,575),(118+j*119,587)],rgba(COOL,o*.57),2.0)
    p.vector(rule);p.finish()


def collision(im,f):
    if f<5417:
        c=Call(5334,5417,'FAILURE CASE  /  CGI','Wall hit',x=113,y=148,size=86)
        callout(im,f,c,None)
        p=Panel(im,(547,135,1710,939),None)
        v=settle(5334,5370,f);o=fade(5334,5417,f)
        ids=list(range(5301,min(f,5416)+1,3))
        def path(l,d):
            for j in range(0,len(ids)-1):
                a,b=ids[j:j+2];c=AMBER if a<5325 else COOL
                if j%3==1:continue
                l([pt(a,'body'),pt(b,'body')],rgba(c,o*.48),3.4)
            x=pt(5325,'toe');d(x,13+14*(1-v),rgba(AMBER,o*.78),True)
        p.vector(path);p.finish()
    else:
        callout(im,f,Call(5417,5500,'BACK INSIDE THE PIT','3 wall collisions','In the observed lab trials',x=112,y=169,size=89),None)


def results(im,f):
    t=settle(6068,6086,f);o=fade(6068,6175,f)
    p=Panel(im,(56,711,1864,1035),None)
    p.over(Image.new('L',p.layer.size,round(232*o)),INK,(0,0))
    p.word('117 LAB TRIALS   /   OBSERVED OUTCOMES',115,767,28,CREAM,mono=True,spacing=1.5,show=t,alpha=o)
    for i,(n,k,c) in enumerate((('~1/2','RAN OUT',CREAM),('15%','JUMPED CLEAR',COOL),('~1/3','CAUGHT',AMBER))):
        x=112+i*568;v=settle(6072+i*5,6090+i*5,f)
        p.word(n,x,832,79,c,weight=690,show=v,alpha=o)
        p.word(k,x,940,30,CREAM,mono=True,spacing=1.2,show=v,alpha=o*.9)
    p.finish()


def cohort(im,f,a,b):
    # In native receiver coordinates: left mock, right restrained for the paired
    # view; left untouched, middle mock, right restrained in the baseline view.
    o=fade(a,b,f,11,7);e=settle(a+2,a+23,f)
    if a in (6399,6920,7240):
        labels=[('UNTOUCHED','No manipulation',FADED),('MOCK','Glue outside jaws',COOL),('RESTRAINED','Jaw tips glued shut',AMBER)]
        centers=[554,938,1322]
        title='Three treatment groups' if a!=7240 else 'Different handling, different test'
        subtitle='76 ants in each group'
    else:
        labels=[('MOCK','Can still snap',COOL),('RESTRAINED','Cannot snap',AMBER)]
        centers=[640,1247]
        title='Same handling. Different jaws.' if a<7347 else 'Compare the two handled groups'
        subtitle='Both chilled & glued   /   76 per group'
    p=Panel(im,(0,0,1920,1080),None)
    p.word('LARABEE & SUAREZ  /  RESTRAINT EXPERIMENT',112,110,28,COOL,mono=True,spacing=1.75,show=e,alpha=o*.93)
    p.word(title,109,160,65,CREAM,weight=680,spacing=-1.32,show=e,alpha=o)
    distinct=ease(6950,6973,f) if a==6920 else 0.
    for i,(one,two,col) in enumerate(labels):
        x=centers[i];v=settle(a+5+i*3,a+19+i*3,f)
        depth=o*(1. if i==0 else (1.-.39*distinct if a!=7240 else .75))
        p.word(one,x-width(one,35,True,1.5,650)*.5,755 if len(labels)==3 else 815,35,col,mono=True,spacing=1.5,show=v,alpha=depth)
        p.word(two,x-width(two,30,False,0,650)*.5,805 if len(labels)==3 else 865,30,CREAM,show=v,alpha=depth*.91)
    p.word(subtitle,112,985,28,FADED,mono=True,spacing=1.2,show=e,alpha=o*.85)
    def v(l,d):
        if len(labels)==2:
            x,y=centers;h=944
            l([(x,h-17),(x,h),(x+(y-x)*e,h)],rgba(COOL,.65*o),2.5)
            if e>.96:l([(y,h),(y,h-17)],rgba(COOL,.65*o),2.5)
        elif distinct>0.002:
            x=centers[0];y=735
            l([(x-60*distinct,y),(x+60*distinct,y)],rgba(COOL,o*.77*distinct),2.6)
            d((x,y),3.0,rgba(COOL,o*.85*distinct))
        elif a==7240:
            x=748;h=579
            l([(x,h-228*e),(x,h+228*e)],rgba(FADED,.38*o),2.5)
    p.vector(v);p.finish()


def compose(im,f):
    c=next((x for x in CALLS if x.a<=f<x.b),None)
    g=next((x for x in SPECIALS if x[0]<=f<x[1]),None)
    if c is None and g is None and not 748<=f<799:return im
    matte=im.getchannel('A')
    im.putalpha(255)
    if c:callout(im,f,c,matte)
    if 748<=f<799:topology(im,f)
    if g:
        a,b,k=g
        if a==3143:dual(im,f)
        elif a==3322:time_mark(im,f)
        elif a==5334:collision(im,f)
        elif a==6068:results(im,f)
        elif a in (8317,8507):
            c=Call(a,b,'SAME SAND  /  DIFFERENT PUSH','Sand goes up' if a==8317 else 'Ant goes up',x=112,y=158,size=84)
            callout(im,f,c,matte)
        else:cohort(im,f,a,b)
    return im


def plan():
    intervals=[dict(first=x.a,end=x.b,label=x.title) for x in CALLS]+[dict(first=a,end=b,label=k) for a,b,k in SPECIALS]
    for i in intervals:
        assert not any(a<i['end'] and b>i['first'] for a,b in PROTECTED), i
        assert i['end']-i['first']>34
    return sorted(intervals,key=lambda i:i['first'])
