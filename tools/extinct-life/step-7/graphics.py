"""Editorial type and evidence overlays for the investigation (1920-unit canvas).

Graphics clarify what's being tested; the separate locked captions carry speech.
All overlays leave the bottom subtitle lane clear. No track-to-track route is drawn.
"""
from __future__ import annotations

from functools import lru_cache
import math

import numpy as np
from PIL import Image

from cut import BY, F, FPS, inside
from film_picture import FilmType, pin, type_layer
from motion import AMBER, CREAM, DARK, MINT, SKY, smooth, ease_out, glyph, rgba

INK=(10,21,27); GREY=(155,180,177); FAINT=(112,150,148)


def cue(f,name,seconds=.40):
    return smooth((f-BY[name].f+1)/(FPS*seconds))


def step(t,lo,hi):return smooth((t-lo)/(hi-lo))


def rect(g,x0,y0,x1,y1,c,a=1):
    if a>.003:g.d.rectangle(g.xy((x0,y0,x1,y1)),fill=rgba(c,a))


def caps(g,x,y,text,c=GREY,a=1,n=23,align='l',tag=None):
    g.type(x,y,text,n,'mono',c,tag,a,align,track=1.02)


def txt(g,x,y,text,n=57,c=CREAM,a=1,align='l',tag=None,kind='head'):
    g.type(x,y,text,n,kind,c,tag,a,align,style='title-rise')


def centre(g,x,y,text,n,c=CREAM,a=1,kind='head'):
    mask,_,pad=glyph(text,max(8,round(n*g.s)),kind,0)
    txt(g,x-(mask.width-2*pad)/(2*g.s),y,text,n,c,a,kind=kind)


def eyebrow(g,head,detail=None,col=MINT,a=1,tag=None):
    g.bar(82,70,37,3.8,col,a)
    caps(g,132,55,head,col,a,24,tag=tag)
    if detail:caps(g,1838,55,detail,CREAM,a,20,'r')


def pair(g,names,colors=(AMBER,MINT),sub=('', ''),a=1,y=74):
    for i,(name,col,hint) in enumerate(zip(names,colors,sub,strict=True)):
        x=80+960*i
        g.bar(x,y+8,30,3.5,col,a)
        txt(g,x+48,y-11,name,49,CREAM,a)
        if hint:caps(g,x+50,y+57,hint,col,a,n=20)


def project_ok(p):return p[-1]>0 and 41<p[0]<1879 and 73<p[1]<964


def focus(g,p,col=AMBER,amount=1,r=26):
    if not project_ok(p):return
    x,y=p[:2]
    for sign in (-1,1):
        for ysgn in (-1,1):
            X,Y=x+r*sign,y+ysgn*r
            g.line(((X-10*sign,Y),(X,Y),(X,Y-10*ysgn)),col,amount,2.5)


def callout(g,p,x,y,text,col=MINT,a=1,align='l',leader_side=None):
    if not project_ok(p) or a<.008:return
    X,Y=p[:2]
    sign=leader_side if leader_side is not None else (1 if X>=x else -1)
    g.circle(X,Y,4,col,None,a*.91)
    e=(x,y+43);mid=(X-52*sign,Y-24 if Y>y+43 else Y+24)
    g.line(((X,Y),mid,(mid[0],y+43),e),col,a*.70,2.1)
    g.bar(x if align=='l' else x-34,y+44,34,2.6,col,a)
    caps(g,x,y,text,col,a,21,align)


def topo_label(g,p,name,col,i,a):
    if not project_ok(p):return
    x,y=p[:2];pin(g,p,col,a)
    # Put the two labels outward, clear of a short separation measurement.
    dx=(-39 if i==0 else 39);xx=min(1763,max(155,x+dx));yy=y+70 if y>265 else y+51
    g.line(((x,y+7),(x,y+42),(x+dx*.60,yy+13),(xx,yy+13)),col,a*.72,2.0)
    txt(g,xx+(7 if i else -7),yy-13,name,35,CREAM,a,'l' if i else 'r',kind='bold')


def measure_line(g,tr,a,col=CREAM):
    if a<.003 or not (project_ok(tr[0]) and project_ok(tr[1])):return
    x,y,_=tr[0];X,Y,_=tr[1]
    def Q(p):return ((1-p)*x+p*X,(1-p)*y+p*Y-36*math.sin(math.pi*p))
    for j in range(19):
        u0=(j+.15)/19;v=(j+.68)/19
        g.line((Q(u0),Q(v)),DARK,a*.67,5.0)
        g.line((Q(u0),Q(v)),col,a*.96,2.7)
    for p in (0,1):
        xx,yy=Q(p);g.line(((xx,yy-23),(xx,yy-43)),col,a*.86,2.2)


def map_view(g,k,f,tr,t):
    old=k in (3,46,48,51,53,56,59) and (k!=3 or f>=BY['old-lock'].f)
    edge=tr[4];far=tr[5]
    g.line(((edge[0],far[1]),edge[:2],(far[0],edge[1]),far[:2],(edge[0],far[1])),SKY,.30,1.4)
    for x in (edge[0],far[0]):
        for y in (edge[1],far[1]):
            sign=1 if x==edge[0] else -1
            g.line(((x+sign*23,y),(x,y),(x,y+(17 if y==edge[1] else -17))),SKY,.72,2.2)
    if k in (2,3,61):
        if k==3 and not old:
            eyebrow(g,'REWIND THE MAP','TWO GEOGRAPHIC SNAPSHOTS',MINT,1-step(t,.84,1.25))
            return
        a=1 if k!=3 else step(t,1.17,1.53)
        x=82;y=64
        new=old and k==3
        num='≈1,000 km' if new else '≈6,000 km'
        tag='then' if new else ('gap-returns' if k>=61 else 'now')
        n=(f>=BY[tag].f)*a
        head='125 MILLION YEARS AGO' if new else 'PRESENT DAY'
        detail='MODEL SNAPSHOT · NOT A FOOTPRINT DATE' if new else 'REGIONAL SEPARATION'
        caps(g,x+2,39,head,MINT if new else AMBER,a,21)
        txt(g,x,67,'Gondwana' if new else 'Atlantic Ocean',66,CREAM,a)
        caps(g,1842,28,detail,CREAM,a,19,'r')
        txt(g,1839,60,num,84,CREAM,n,'r',tag,'metric')
        if n>0:measure_line(g,tr,n*cue(f,tag),MINT if new else AMBER)
        for i,(p,name,c) in enumerate(zip(tr[:2],('Sousa','Koum region'),(AMBER,MINT),strict=True)):
            topo_label(g,p,name,c,i,a*(.80+.20*step(t,0,.31)))
        return
    if k in (5,34):
        i=int(k==5);c=MINT if i else AMBER;p=tr[i]
        a=step(t,.05,.51) if i else cue(f,'brazil',.33)
        eye='NORTHERN CAMEROON' if i else 'NORTHEAST BRAZIL'
        eyebrow(g,eye,'MODERN GEOGRAPHY',c,max(.65,a))
        if p[-1]>0:topo_label(g,p,'Koum Basin region' if i else 'Sousa Basin',c,i,a)
        return
    if k==56:
        eyebrow(g,'COMPARE THE DISTRIBUTIONS','NOT THE FOOTPRINT SITES',MINT,step(t,5.54,5.94))
    elif k==58:
        eyebrow(g,'WHAT WOULD TEST IT?','FUTURE EVIDENCE, NOT DISCOVERIES')
        a=cue(f,'more-sites',.36)
        if a>.01:
            for x,y,r in ((742,541,32),(910,611,41),(1071,509,30)):
                # Open question symbols, not new localities or an inferred route.
                g.circle(x,y,r,INK,MINT,.85*a,2.4)
                centre(g,x,y-23,'?',38,MINT,a,'bold')
            caps(g,118,870,'01    MORE SITES IN BETWEEN',AMBER,a,28)
    else:
        note={46:('RESTORE THE LAND','125 MA MODEL'),48:('BEDROCK AND FAULTS','2024 INTERPRETATION'),
           51:('CONNECTED LAND','125 MA MODEL'),53:('POSSIBLE DISPERSAL AREA','HYPOTHESIS · NOT A TRACED ROUTE'),
           59:('A POSSIBLE ROUTE','NOT AN INDIVIDUAL JOURNEY')}[k]
        eyebrow(g,*note,col=MINT)
        if k==46:
            a=cue(f,'restore-model');caps(g,96,911,'MODEL SNAPSHOT · NOT A FOOTPRINT DATE',CREAM,.91*a,22)
        if k in (46,48,51,53,59):
            for i,(p,name,c) in enumerate(zip(tr[:2],('Sousa region','Koum region'),(AMBER,MINT),strict=True)):
                topo_label(g,p,name,c,i,.89)
        if k==53:
            a=cue(f,'range',.46)
            caps(g,98,894,'POSSIBLE HABITAT CONNECTIONS',MINT,a,25)


def age_chart(g,k,f,t):
    # Range positions and widths are illustrative, not absolute ages. The two
    # broad bands deliberately share a pale region without a common date pin.
    final=k==45
    a=cue(f,'age',.41) if final else step(t,.16,.70)
    if a<.005:return
    h=1 if final else cue(f,'window-low',.52)
    xl,xr=492,1777;y1,y2=443,636
    rect(g,81,137,1839,894,INK,.94*a)
    g.line(((81,190),(81,137),(140,137)),AMBER,a*.68,2)
    g.line(((1776,894),(1839,894),(1839,841)),MINT,a*.68,2)
    txt(g,127,190,'Early Cretaceous' if final else 'An age window, not a date',78,CREAM,a,tag='age' if final else None)
    caps(g,129,287,'BROAD ASSIGNMENT  /  EXACT RELATIONSHIP UNKNOWN' if final else 'SCHEMATIC AGE RANGES  /  NOT MEASURED ENDPOINTS',GREY,a,23)
    caps(g,xl,365,'OLDER',GREY,a,19);caps(g,xr,365,'YOUNGER',GREY,a,19,'r')
    for i in range(11):
        x=xl+(xr-xl)*i/10
        g.line(((x,401),(x,738)),FAINT,a*(.31 if i%5==0 else .14),1.4)
    for y,nm,col,ends in ((y1,'Sousa region',AMBER,(.10,.89) if final else (.08,.70)),
                           (y2,'Koum region',MINT,(.10,.89) if final else (.29,.93))):
        g.line(((xl,y+37),(xr,y+37)),FAINT,a*.48,1.8)
        txt(g,127,y+8,nm,48,col,a,kind='bold')
        L=xl+(xr-xl)*ends[0];R=xl+(xr-xl)*ends[1];u=ease_out(h)
        R=L+(R-L)*u
        # Fuzzy, explicitly provisional ends instead of falsely precise bars.
        for j in range(58):
            q=(j+.5)/58;opacity=(.08+.69*step(q,0,.15)*(1-step(q,.84,1)))*a
            x0=L+(R-L)*j/58;x1=L+(R-L)*(j+1)/58
            g.bar(x0,y+17,(x1-x0)+.9,40,col,opacity)
            if j%3==0 and .04<q<.96:g.line(((x0-5,y+59),(x0+13,y+15)),CREAM,a*.22,1.5)
    if final:
        gap=step(t,.72,2.10)
        g.line(((844,391),(844,381),(1190,381),(1190,391)),CREAM,a*gap*.47,2.4)
        g.line(((844,744),(844,754),(1190,754),(1190,744)),CREAM,a*gap*.47,2.4)
        caps(g,128,794,'OVERLAP DOES NOT ESTABLISH THE SAME MOMENT',CREAM,a*gap,29)
    else:
        caps(g,128,794,'A RANGE IS NOT A TIMESTAMP',CREAM,a*h,26)


def credits(g,f):
    a=cue(f,'credits-on',.37)*(1-step((f-F[65])/FPS,6.00,6.5));
    if a<.005:return
    eyebrow(g,'EXTINCT LIFE','INVESTIGATION CUT',AMBER,a)
    txt(g,97,164,'Sources & maps',105,CREAM,a)
    g.line(((98,322),(1823,322)),FAINT,a*.40,2)
    caps(g,98,371,'FOOTPRINTS & GEOLOGY',AMBER,a,25)
    caps(g,1012,371,'GEOGRAPHY & AUDIO',MINT,a,25)
    for i,s in enumerate(('Jacobs et al. (2024) · corridor hypothesis','Menkem et al. (2026) · Koum survey','Carvalho et al. (2013) · Sousa preservation')):
        txt(g,98,431+61*i,s,31,CREAM,a,kind='sans')
    for i,s in enumerate(('Kocsis & Scotese · PaleoCoastlines / rotations','Scotese & Wright · PaleoDEMs v2  •  CC BY 4.0','Natural Earth / NOAA ETOPO5 · public domain','Sound recording credits & licenses in the handoff')):
        txt(g,1012,431+61*i,s,30,CREAM,a,kind='sans')
    g.line(((98,768),(1823,768)),FAINT,a*.40,2)
    caps(g,98,812,'ORIGINAL CGI ILLUSTRATIONS  /  MAPS ADAPTED',GREY,a,23)


@lru_cache(maxsize=34)
def scrim(size,mode):
    w,h=size;v,u=np.ogrid[0:1:h*1j,0:1:w*1j]
    if mode=='full':
        m=.62*np.exp(-((u+.01)/.68)**2-((v-.31)/.53)**2)
    elif mode=='sides':
        m=.65*np.exp(-((v-.006)/.20)**2)*(.80+.20*np.cos(np.pi*u*4)**2)+.40*np.exp(-((v-1.05)/.18)**2)
    else:m=.54*np.exp(-((v-.01)/.24)**2)*(.75+.25*np.cos(np.pi*u*.64)**2)+.25*np.exp(-((v-1.05)/.19)**2)
    return Image.fromarray(np.clip(m*255,0,255).astype(np.uint8))


def overlays(g,k,f,tr,t):
    if k in (2,3,5,34,46,48,51,53,59,61) or (k==56 and t>=5.54) or (k==58 and f<BY['better-dates'].f):
        map_view(g,k,f,tr,t);return
    if k==0:
        a=cue(f,'sousa-open',.35)
        caps(g,89,91,'BRAZIL  /  01',AMBER,a,25)
        txt(g,86,130,'Sousa Basin',65,CREAM,a,tag='sousa-open')
    elif k in (1,62):
        g.line(((960,0),(960,1080)),INK,.94,6)
        a=max(.20,cue(f,'koum-open',.34)) if k==1 else 1
        pair(g,('Sousa Basin','Koum region'),(AMBER,MINT),('BRAZIL','CAMEROON'),a,y=85)
        if k==62:
            a=step(t,.58,1.12)
            rect(g,486,782,1434,911,INK,.91*a)
            centre(g,960,798,'No trail across the gap',58,CREAM,a)
    elif k==4:
        a=1-step(t,2.32,2.96)
        caps(g,90,135,'EXTINCT LIFE  /  A FOSSIL INVESTIGATION',AMBER,a*step(t,0,.25),22)
        for i,name in enumerate(('title-a','title-b','title-c')):
            txt(g,86,195+109*i,BY[name].text,103,CREAM if i<2 else AMBER,a,tag=name)
        if t>=3.0:caps(g,88,862,'ILLUSTRATIVE ANCIENT FLOODPLAIN',CREAM,.88*step(t,3.0,3.32),21)
    elif k in (6,13):
        a=cue(f,'surfaces',.40) if k==6 else step(t,.04,.42)
        eyebrow(g,'KOUM  /  FOUR WALKED SURFACES','SEPARATE EXPOSURES',MINT,a)
        for i,p in enumerate(tr[:4]):
            b=a*step(t,.48+.38*i,1.08+.38*i)
            if project_ok(p):
                x,y=p[:2];g.circle(x,y,21,INK,MINT,b*.86,2);centre(g,x,y-15,str(i+1),25,CREAM,b,'mono')
    elif k==12:
        eyebrow(g,'FOLLOW THE PRINTS','THE RECORD STOPS AT THE BREAK',MINT,step(t,.55,1.55))
    elif k==14:
        eyebrow(g,'EROSION  /  THE CLUE CHANGES','ILLUSTRATIVE SURFACE')
        a=cue(f,'erosion-pop',.48)
        callout(g,tr[0],145,205,'EDGE LOST',AMBER,a)
    elif k==15:
        a=cue(f,'photos',.44)
        eyebrow(g,'PHOTOGRAMMETRY','SIMULATED CAMERA VIEWS',MINT,step(t,.08,.54))
        txt(g,91,170,'2,000+',96,CREAM,a,tag='photos',kind='metric')
        caps(g,95,274,'OVERLAPPING PHOTOS',MINT,a,22)
    elif k==16:
        eyebrow(g,'SAME RELIEF, DIGITAL MODEL','ILLUSTRATIVE MESH')
        a=cue(f,'reconstruction',.49)
        caps(g,95,855,'SHAPE SURVIVES IN THE RECORD',MINT,a,24)
    elif k==18:
        a=cue(f,'length',.45)
        txt(g,84,140,'≈69 cm',100,CREAM,a,tag='length',kind='metric')
        caps(g,89,250,'LENGTH OF ONE IMPRESSION',AMBER,a,23)
        caps(g,89,287,'NOT THE ANIMAL’S HEIGHT',CREAM,a*.86,20)
        for j,label in ((1,'HEEL'),(2,'TOE')):
            if project_ok(tr[j]) and a>.6:
                x,y=tr[j][:2];caps(g,x+20,y-19,label,CREAM,a,19)
    elif k==19:
        a=cue(f,'soft-outline',.47)
        eyebrow(g,'THE MARGIN IS LESS DISTINCT','INTERPRETIVE OUTLINE',AMBER,a)
        if t>=4.1:caps(g,85,877,'SOFTER SEDIMENT CAN DEFORM',CREAM,step(t,4.10,4.62),24)
    elif k in (20,21):
        a=max(.62,step(t,0,.37))
        if k==20:
            label='SAME STAMP / TWO SUBSTRATES'
            if f>=BY['test-down'].f:label='01   CONTACT'
            if f>=BY['test-up'].f:label='02   RELEASE'
            if f>=BY['slump'].f:label='03   SOFT WALL SLUMPS'
            eyebrow(g,label,'CONTROLLED CGI DEMONSTRATION',MINT,a)
            b=cue(f,'two-muds',.32)
        else:
            eyebrow(g,'SAME STAMP. DIFFERENT PRINTS.','CONTROLLED CGI DEMONSTRATION',MINT,a)
            b=cue(f,'firm-soft',.36)
        pair(g,('Firm mud','Soft mud'),(AMBER,MINT),a=b,y=164)
        if k==21:
            rect(g,88,866,1830,926,INK,.91*b)
            caps(g,120,879,'RIM HOLDS',AMBER,b,28)
            caps(g,1080,879,'WALLS SLUMP INWARD',MINT,b,28)
    elif k==22:
        eyebrow(g,'ONE TRACKWAY, CHANGING GROUND','ILLUSTRATIVE SEQUENCE')
        a=cue(f,'less-clear',.44)
        caps(g,87,120,'CLEARER     /     LESS DISTINCT',CREAM,a,25)
    elif k==23:
        eyebrow(g,'LOOKALIKE IMPRESSIONS','SHAPE ALONE DOES NOT IDENTIFY THE MAKER')
    elif k==24:
        eyebrow(g,'LOOK BELOW THE FOOT','THE SEDIMENT IS PART OF THE EVIDENCE')
    elif k==27:
        pair(g,('Rippled','Cracked'),(MINT,AMBER),('WATER MOVED','GROUND DRIED'),y=106)
        caps(g,87,881,'DIFFERENT EXPOSED SURFACES',CREAM,step(t,.34,.78),23)
    elif k==30:
        eyebrow(g,'GRAIN CONTACTS','ILLUSTRATIVE MICROVIEW')
        a=cue(f,'cement',.34)
        txt(g,84,147,'Mineral cement',82,CREAM,a,tag='cement')
        if a>.02:callout(g,tr[0],1047,316,'BOND BETWEEN GRAINS',AMBER,a)
    elif k in (31,36):
        a=cue(f,'mat' if k==31 else 'sousa-fibres',.39)
        eyebrow(g,'KOUM  /  BINDING' if k==31 else 'SOUSA  /  PRESERVATION','ILLUSTRATIVE MICROVIEW')
        txt(g,85,151,'Possible microbial mat',75,CREAM,a,tag='mat' if k==31 else None)
        if a>.02:callout(g,tr[0],1119,330,'POSSIBLE BINDING',MINT,a)
    elif k==32:
        a=cue(f,'bury',.47);seal=cue(f,'seal',.37)
        eyebrow(g,'BURIAL','PRESERVATION MECHANISM',AMBER)
        txt(g,82,148,'Fresh sediment',80,CREAM,a*(1-seal))
        txt(g,82,148,'Surface sealed',80,CREAM,seal)
        if seal>.08:callout(g,tr[0],1410,621,'BURIED TRACK BED',MINT,seal,'r')
    elif k==33:
        eyebrow(g,'WHAT SURVIVED','ILLUSTRATIVE PRESERVED IMPRESSION',a=step(t,1.20,1.77))
    elif k==37:
        a=cue(f,'rim',.36)
        eyebrow(g,'A RAISED RIM','ILLUSTRATIVE SOUSA SURFACE',AMBER,a,tag='rim')
        callout(g,tr[1],140,199,'DISPLACED SEDIMENT',AMBER,a)
    elif k==38:
        eyebrow(g,'COHESIVE SURFACE','PROPOSED PRESERVATION AT SOUSA',AMBER)
    elif k==39:
        eyebrow(g,'COMPARE THE CONDITIONS','NOT JUST THE TOES')
        a=cue(f,'both',.49)
        pair(g,('Koum region','Sousa Basin'),(MINT,AMBER),a=a,y=153)
        caps(g,97,887,'DAMP SEDIMENT  /  POTENTIAL FOR PRESERVATION',CREAM,a,23)
    elif k==40:
        g.line(((960,0),(960,1080)),INK,.94,6)
        pair(g,('Bank A','Bank B'),(AMBER,MINT),('ILLUSTRATION','ILLUSTRATION'),y=82)
        a=step(t,4.87,5.33)
        rect(g,410,759,1510,888,INK,.83*a)
        centre(g,960,782,'Similar banks ≠ one river',58,CREAM,a)
    elif k==41:
        eyebrow(g,'TURN THE COMPARISON SIDEWAYS','SCHEMATIC SECTIONS · NOT TO SCALE')
        a=step(t,.40,1.12)
        pair(g,('Sousa region','Koum region'),a=a,y=161)
        b=step(t,2.48,3.23)
        for p,c in zip(tr[:2],(AMBER,MINT),strict=True):focus(g,p,c,b,28)
        caps(g,97,875,'SIMILAR PRINTS. TIME RELATIONSHIP UNKNOWN.',CREAM,b,26)
    elif k in (42,45):
        age_chart(g,k,f,t)
    elif k==43:
        a=cue(f,'pollen',.39)
        eyebrow(g,'LOOK FOR AGE CLUES','ILLUSTRATIVE POLLEN GRAIN',AMBER)
        txt(g,89,388,'Fossil pollen',101,CREAM,a,tag='pollen')
        caps(g,93,498,'CORRELATES ROCK LAYERS',AMBER,a,25)
    elif k==44:
        eyebrow(g,'CONTEXT IS NOT A DATE STAMP','SEPARATE DEPOSITS · SCHEMATIC')
        a=step(t,.16,.52);b=step(t,2.44,3.16)
        pair(g,('Track-bearing rock','Other deposits'),(AMBER,MINT),a=a,y=161)
        callout(g,tr[0],148,314,'FOOTPRINT BED',AMBER,a)
        callout(g,tr[3],1703,631,'REGIONAL POLLEN CLUE',MINT,b,'r')
        caps(g,91,880,'THE CLUE DOES NOT DIRECTLY DATE THE TRACK BED',CREAM,b,23)
    elif k in (47,49,50,60):
        if k==60:
            second=cue(f,'rift-late',.43)
            eyebrow(g,'ATLANTIC OPENING  /  IN STAGES','TECTONIC SCHEMATIC')
            if second>.03:caps(g,91,879,'SEA ENTERS THE WIDENING BASIN',MINT,second,25)
            else:caps(g,91,879,'CRUST STRETCHES',AMBER,cue(f,'rift-early',.43),25)
        else:
            label={47:'FAULTS IN OLDER BEDROCK',49:'THE BASIN DROPS',50:'SEDIMENT COLLECTS IN THE BASIN'}[k]
            a=cue(f,{47:'fault-light',49:'rift-down',50:'rift-fill'}[k])
            eyebrow(g,label,'TECTONIC SCHEMATIC',AMBER,max(a,.36))
    elif k==52:
        eyebrow(g,'RIVERS & LAKES','ILLUSTRATIVE LANDSCAPE',a=.88)
    elif k==54:
        eyebrow(g,'OVER GENERATIONS','SEPARATE HABITATS · NOT AN INDIVIDUAL TRACK')
        for i,p in enumerate(tr[:3]):
            q=cue(f,('habitat-first','habitat-next','habitat-last')[i])
            if project_ok(p):
                x,y=p[:2];x-=35;y+=113
                caps(g,x,y,str(i+1).zfill(2),MINT,q,23)
    elif k==55:
        a=cue(f,'mawsonia',.37)
        txt(g,86,133,'Mawsonia',91,CREAM,a,tag='mawsonia')
        caps(g,92,238,'COELACANTH ILLUSTRATION' if t<8.5 else 'ILLUSTRATIVE FOSSIL MATCH CUT',MINT,a,23)
    elif k==56:
        a=cue(f,'other-basins',.37)
        eyebrow(g,'FOSSIL FRAGMENTS','ILLUSTRATIONS, NOT SPECIMEN PHOTOS')
        pair(g,('South American basins','African basins'),a=a,y=143)
        caps(g,94,877,'OTHER BASINS, NOT THE TRACK SITES',CREAM,a,24)
    elif k==57:
        a=step(t,.14,.65)
        eyebrow(g,'INDEPENDENT LINES OF EVIDENCE','ILLUSTRATIONS · NO RIVER COURSE SHOWN')
        g.line(((960,160),(960,904)),GREY,.30*a,2)
        pair(g,('Footprints','Fish fossils'),(AMBER,MINT),('TRACK-BEARING ROCKS','OTHER BASINS'),a,y=149)
        centre(g,960,852,'Two patterns to test against the geography',48,CREAM,a)
    elif k==58:
        # Distinct tests replace the earlier continuous hold. No new 'finds'.
        better=f>=BY['better-fossils'].f;tag='better-fossils' if better else 'better-dates';a=cue(f,tag,.33)
        eyebrow(g,'WHAT WOULD TEST IT?','FUTURE EVIDENCE, NOT DISCOVERIES')
        txt(g,84,133,'Identifiable fossils' if better else 'Narrower dates',77,CREAM,a,tag=tag)
    elif k==63:
        a=cue(f,'rocks-answer',.32)
        txt(g,84,90,'The rocks.',108,CREAM,a,tag='rocks-answer')
        caps(g,91,220,'THE PRINTS STAY IN THEIR BEDS',MINT,a,26)
        caps(g,1830,66,'PLATE MOTION · SCHEMATIC',CREAM,a,20,'r')
        for p,c in zip(tr[:2],(AMBER,MINT),strict=True):
            focus(g,p,c,.76*a,52)
    elif k==64:
        a=step(t,6.58,7.38)*(1-step(t,8.75,9.33))
        caps(g,95,879,'ILLUSTRATIVE ANCIENT LANDSCAPE',CREAM,a,22)
    elif k==65:
        credits(g,f)
    else:
        for b in inside(k):
            if b.text and b.f<=f<=b.f+round(b.hold*FPS):type_layer(g,k,b)


def compose(im,k,f,tr,omit=None):
    t=(f-F[k])/FPS
    maps=k in (2,3,5,34,46,48,51,53,59,61) or (k==56 and t>=5.54) or (k==58 and f<BY['better-dates'].f)
    if not maps:
        mode='full' if k in (0,4,18,19,43) else 'sides' if k in (1,20,21,39,40,41,62) else 'stage'
        fade=(1-step(t,2.36,3.0)) if k==4 else 1
        m=scrim(im.size,mode)
        if fade<.996:m=m.point(lambda a:int(a*fade))
        im.paste(INK,None,m)
    g=FilmType(im.size,f,omit)
    overlays(g,k,f,tr,t)
    return Image.alpha_composite(im.convert('RGBA'),g.paper).convert('RGB')
