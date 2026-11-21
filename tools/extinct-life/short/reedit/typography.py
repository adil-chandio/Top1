"""Camera-projected, extruded word accents and a restrained documentary graphics system."""
from __future__ import annotations
from collections import defaultdict
from functools import lru_cache
from math import cos, sin, radians, exp, floor, ceil
from bisect import bisect_right

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from clock import W, H, FP, SR, FPS, ROOT, digest
from mix import WORD
from titles import Layer, BOX, ease

SPACE=ROOT/'.cache/atlantic-cover/fonts/SpaceGrotesk.ttf'
SPACE_SHA='acad6de1fc93436f5c0f1f4137751ef04f1aea3063e7036535970ffcfbd79f72'
F=(251,247,231); G=(255,210,139); A=(179,236,223); N=(7,16,21)
TINTS={'ivory':F,'sand':G,'aqua':A}
# Phrased captions, not a wall of unrelated one-word pop-ups. One focus per
# idea receives real depth, a restrained lean and a timed light/material hit.
SCORE=(
    (('Same foot.',(109,),('foot',)),),
    (('Two different|prints.',(80,128),('prints',)),),
    (('Firm mud|holds the shape.',(95,71),('firm','shape')),),
    (('In softer mud,',(85,),('softer',)),),
    (('the walls slump',(91,),('slump',)),('as the foot lifts.',(82,),('lifts',))),
    (('The toes can fool you.',(86,),('fool',)),),
    (('Three-toed|dinosaur tracks',(95,82),('three-toed',)),('in Brazil.',(109,),('brazil',))),
    (('More in|Cameroon,',(73,106),('cameroon',)),),
    (('roughly six thousand|kilometres away today.',(78,71),('thousand',)),),
    (('Rewind|the map.',(113,82),('rewind',)),),
    (('Before the Atlantic|opened here,',(76,86),('atlantic',)),),
    (('both places were on|the same landmass.',(68,82),('landmass',)),),
    (("But connected land|isn't a trail.",(76,97),('trail',)),),
    (('So what in|the rocks',(79,110),('rocks',)),('hints at|a route?',(84,110),('route',))),
)


@lru_cache(maxsize=196)
def font(px):
    f=ImageFont.truetype(str(SPACE),px);f.set_variation_by_axes([700]);return f


def clamp(x):return max(0.,min(1.,x))


def blend(a,b,k):return tuple(round(x+(y-x)*k) for x,y in zip(a,b,strict=True))


@lru_cache(maxsize=360)
def glyph(text,p,ss,tint):
    f=font(round(p*ss));l,t,r,b=f.getbbox(text,anchor='ls');pad=ceil(5.0*ss)
    w,h=r-l+2*pad,b-t+2*pad;l-=pad;t-=pad
    mask=Image.new('L',(w,h));ImageDraw.Draw(mask).text((-l,-t),text,font=f,anchor='ls',fill=255)
    # The bevel is lit top-left; the face stays mostly bright for phone-size
    # legibility. Edge shading follows the actual silhouette and counters.
    q=max(1,round(1.65*ss));h1=ImageChops.subtract(mask,ImageChops.offset(mask,q,q));l1=ImageChops.subtract(mask,ImageChops.offset(mask,-q,-q))
    c=TINTS[tint];bar=Image.new('RGB',(1,h));bar.putdata([blend(blend(c,(255,255,251),.43),blend(c,(185,157,118) if tint!='aqua' else (118,177,176),.34),j/max(1,h-1)) for j in range(h)])
    im=bar.resize(mask.size,Image.Resampling.BILINEAR)
    im.paste((255,254,243),(0,0,w,h),h1.point(lambda v:round(v*.50)))
    im.paste(blend(c,(23,38,45),.57),(0,0,w,h),l1.point(lambda v:round(v*.44)))
    im.putalpha(mask)
    outline=mask.filter(ImageFilter.MaxFilter(2*max(1,round(2.55*ss))+1))
    return im,mask,outline,(l/ss,t/ss),f.getlength(text)/ss


def transform(src,corners,rect,scale):
    l,t,r,b=rect;w,h=src.size
    # Map the projected quadrilateral back to its source pixel plane.
    a=[];q=[]
    for (x,y),(u,v) in zip(corners,((0,0),(w,0),(w,h),(0,h)),strict=True):
        x=x*scale-l;y=y*scale-t
        a.extend(((x,y,1,0,0,0,-u*x,-u*y),(0,0,0,x,y,1,-v*x,-v*y)));q.extend((u,v))
    m=np.linalg.solve(a,q)
    return src.transform((r-l,b-t),Image.Transform.PERSPECTIVE,m,Image.Resampling.BILINEAR)


class Words:
    def __init__(self,scale,checks):self.s=scale;self.ss=round(scale*1.55,4);self.bounds=checks;self.faces=0;self.extrusions=0

    def stamp(self,im,text,px,x,y,alpha,bob=0,tilt=0,yaw=0,roll=0,boost=1.,depth=0.,tint='ivory',tag='captions'):
        if alpha<.022:return
        g,m,o,(l,t),advance=glyph(text,px,self.ss,tint)
        w,h=g.width/self.ss,g.height/self.ss;u=l-advance/2;v=t+px*.35
        x+=advance/2;y+=bob-px*.35
        a,b,c=map(radians,(tilt,yaw,roll));X=cos(a);Y=sin(a);L=cos(b);J=sin(b);R=cos(c);S=sin(c)
        def project(z):
            k=[]
            for i,j in ((u,v),(u+w,v),(u+w,v+h),(u,v+h)):
                i*=boost;j*=boost
                y1=X*j-Y*z;z1=Y*j+X*z
                x1=L*i+J*z1;z2=-J*i+L*z1
                f=680/(680-z2)
                k.append((x+f*(R*x1-S*y1),y+f*(S*x1+R*y1)))
            return k
        z=project(0);bake=project(-depth) if depth>0 else z
        xx,yy=zip(*(z+bake),strict=True)
        assert BOX[0]-2<=min(xx)<max(xx)<=BOX[2]+2 and BOX[1]-2<=min(yy)<max(yy)<=BOX[3]+2,(tag,text,tuple(round(v,1) for v in (min(xx),min(yy),max(xx),max(yy))))
        self.bounds[tag][text]=[round(v,2) for v in (min(xx),min(yy),max(xx),max(yy))]
        s=self.s;rect=(floor((min(xx)-8)*s),floor((min(yy)-8)*s),ceil((max(xx)+8)*s),ceil((max(yy)+12)*s))
        cord=rect[:2];shape=rect[2]-rect[0],rect[3]-rect[1]
        # Local cast shadow follows the face, not an opaque static subtitle bar.
        st=transform(o,z,rect,s);shadow=Image.new('L',shape);shadow.paste(st,(round(1.5*s),round(5.0*s)))
        shadow=shadow.filter(ImageFilter.GaussianBlur(max(1,3.1*s)))
        im.paste((3,10,13),rect,shadow.point(lambda v:round(v*alpha*.73)))
        im.paste(N,rect,st.point(lambda v:round(v*alpha*.89)))
        if depth>0:
            self.extrusions+=1
            tone=TINTS[tint]
            for j in range(7,0,-1):
                d=j/7;mask=transform(m,project(-d*depth),rect,s)
                im.paste(blend((24,32,35),tone,.40*(1-d)+.28),rect,mask if alpha>.995 else mask.point(lambda v:round(v*alpha)))
        face=transform(g,z,rect,s);mask=face.getchannel('A')
        im.paste(face,cord,mask if alpha>.995 else mask.point(lambda v:round(v*alpha)))
        self.faces+=1

    def len(self,text,p):return font(round(p*self.ss)).getlength(text)/self.ss


class Layout:
    def __init__(self,size,t,m):
        assert digest(SPACE)==SPACE_SHA
        self.s=size[0]/W;self.size=size;self.t=t;self.cuts=t['cuts'];self.ar=t['art'];self.report=defaultdict(dict)
        self.type=Words(self.s,self.report);self.map_frames={'today':0,'past':0,'rewind':0};self.word_frames=0;self.subject_cuts=[self.cuts[i]*FP for i in (1,2,5,6,7,8,9)];self.cues=m['cues']
        self.groups=[]
        for ci,(caps,cue) in enumerate(zip(SCORE,self.cues,strict=True)):
            wpos=0
            for text,sizes,focus in caps:
                lines=text.split('|');words=[]
                for line in lines:
                    local=[]
                    for word in line.split():
                        tokens=WORD.findall(word.lower().replace('’',"'"));m=cue['words'][wpos:wpos+len(tokens)];wpos+=len(tokens)
                        assert [x['token'] for x in m]==tokens
                        local.append((word,m[0]['start'],m[-1]['end'],word.lower().strip(',.?') in focus))
                    words.append(local)
                start=words[0][0][1];end=words[-1][-1][2];self.groups.append((ci,start,end,words,sizes))
            assert wpos==len(cue['words'])
        self.start=[row[1]-int(SR*.024) for row in self.groups]
        self.mask=[self.mat(k) for k in range(11)];self.colors=[self.grade(k) for k in range(11)]

    def roi(self,b,k):return Layer(self.s,b,self.report,k)

    def mat(self,k):
        dim=174 if k in (3,4,9) else 143 if k<7 or k==10 else 148
        mask=Image.new('L',(1,self.size[1]));alpha=[]
        for j in range(self.size[1]):
            y=j/self.s
            top=(.28 if k in (3,5,6,9) else .16)*ease(475,174,y) if k<7 or k>8 else 0
            b=dim*ease(1170 if k!=4 else 1420,1559,y)
            alpha.append(round(255*top+b*.91))
        mask.putdata(alpha);return mask.resize(self.size,Image.Resampling.NEAREST)

    @staticmethod
    def grade(k):
        # A mild scene-referred printing curve with lifted small detail and
        # subtle warm/blue separation; no full-screen flash or filter preset.
        warm=k in (0,1,5,9,10);ans=[]
        for tint in ((6,3,-3) if warm else (-4,2,8) if k in (2,3,4,6) else (0,1,2)):
            ans.extend(round(clamp((a/255)**.92+(tint/255)*sin(a/255*3.14159))*255) for a in range(256))
        return ans

    @lru_cache(maxsize=20)
    def slates(self,key):
        # This is a small live label, never a slate separating the viewer from action.
        sh=self.roi((78,224,933,464),key);x=90; y=242
        meta={
            'demo':(G,'CGI DEMO',''),
            'firm':(G,'01 / MATCHED VIEW','Firm mud'),
            'soft':(A,'02 / MATCHED VIEW','Soft mud'),
            'lip':(A,'DETAIL / SOFT MUD','The failing edge'),
            'brazil':(G,'SOUSA BASIN','Brazil'),
            'cameroon':(A,'KOUM BASIN','Cameroon'),
            'layers':(G,'SEDIMENT LAYERS',''),
        }
        tone,small,big=meta[key]
        sh.rect((x,y+2,x+25,y+6),(*tone,255));sh.text(x+43,y-10,small,32,(*tone,255),'mono',stroke=1,tracking=1.3)
        if big:sh.text(x-1,y+44,big,79 if key in ('brazil','cameroon') else 61,(*F,255),'serif',stroke=2)
        if key in ('brazil','cameroon'):sh.text(x,y+141,'ILLUSTRATIVE TRACK SURFACE',29,(*F,249),'mono',stroke=1,tracking=.86)
        if key in ('firm','soft','lip','layers'):sh.text(x,386 if big else y+43,'CGI DEMO' if key!='layers' else 'ILLUSTRATED ROCK FACE',27,(*F,220),'mono',stroke=1,tracking=1.)
        return sh

    def split(self,im,u):
        sh=self.roi((69,221,932,1124),'comparison');k=H*.43
        for top,y,color,txt in ((True,243,G,'01  /  FIRM'),(False,k+41,A,'02  /  SOFT')):
            w=146 if top else 151
            sh.draw.rounded_rectangle(sh.box((85,y-13,85+w+70,y+38)),radius=round(9*self.s),fill=(*N,213))
            sh.rect((93,y-3,98,y+27),(*color,255))
            sh.text(109,y-3,txt,28,(*color,255),'mono',tracking=1)
        sh.text(92,305,'SAME FOOT · SAME SCALE · CGI',26,(*F,250),'mono',stroke=1,tracking=.75)
        sh.put(im,.8+.2*ease(0,5,u))
        # A short amber/teal rule animates along the cut, not over the prints.
        y=round(k*self.s);d=ImageDraw.Draw(im)
        d.rectangle((0,y-2,self.size[0],y+2),fill=N)
        x=round(self.size[0]*ease(-1,11,u));d.line((0,y,x,y),fill=blend(G,A,.46),width=max(1,round(1.8*self.s)))

    @lru_cache(maxsize=4)
    def era_box(self,past):
        sh=self.roi((72,222,931,485),'past' if past else 'today')
        col=G if past else A
        sh.rect((89,255,122,259),(*col,255))
        sh.text(139,243,'125 MILLION YEARS AGO' if past else 'PRESENT DAY',35,(*col,252),'mono',tracking=1.45)
        sh.text(91,420 if past else 427,'MAP SNAPSHOT · NOT A TRACK DATE' if past else 'BETWEEN THE TWO REGIONS',29,(*F,224),'mono',tracking=1.08)
        return sh

    def era(self,im,n,past,alpha):
        if alpha<.02:return
        self.era_box(past).put(im,alpha)
        start=self.ar['wipe_end']-7 if past else self.ar['today'];u=ease(start,start+9,n)
        self.type.stamp(im,'Connected land' if past else '≈6,000 km',87 if past else 113,91,402 if past else 405,alpha,
                        bob=10*(1-u),tilt=9+13*(1-u),yaw=-6-12*(1-u),roll=-.45,depth=13 if past else 19,
                        tint='sand' if past else 'aqua',tag='atlas header')

    @lru_cache(maxsize=1)
    def rewind_tag(self):
        sh=self.roi((72,222,930,483),'rewind')
        sh.text(91,248,'‹‹   MAP REWIND',35,(*A,255),'mono',tracking=1.25)
        return sh

    def maps(self,im,n,r):
        p=r[4];d=self.ar
        modern=(.55+.45*ease(d['today'],d['today']+9,n))*(1-ease(-.006,.17,p));past=ease(.916,.999,p)
        self.era(im,n,False,modern);self.era(im,n,True,past)
        a=ease(.016,.22,p)*(1-ease(.79,.97,p))
        if a>.02:
            self.rewind_tag().put(im,a);ribbon=self.roi((78,312,928,418),'atlas motion');x=89
            for i in range(20):
                q=1.-i/19
                c=G if q<=p else A
                ribbon.rect((x+i*35,348,x+i*35+2,348+(15 if i%4==0 else 8)),(*c,round((.74 if q<=p else .37)*255)))
            at=x+(19*35)*(1-p);ribbon.rect((at-1,340,at+2,380),(*F,255));ribbon.put(im,a);self.map_frames['rewind']+=1
        pins=list(zip(r[5::3],r[6::3],r[7::3],strict=True))
        for old,amount,group in ((False,modern,pins[:2]),(True,past,pins[2:])):
            if amount<.05:continue
            self.map_frames['past' if old else 'today']+=1
            sh=self.roi((70,564,935,1355),'past pins' if old else 'today pins')
            for i,(u,v,z) in enumerate(group):
                x,y=W*u,H*v;assert z>0 and 152<x<924 and 689<y<1280,(n,i,old,x,y)
                color=G if i==0 else A
                lx=90 if i==0 else 913
                label=('Brazil' if i==0 else 'Cameroon')+(' region' if old else '')
                bw=({(False,0):143,(False,1):214,(True,0):240,(True,1):321})[(old,i)]
                ly=(y+99 if old else y-143) if i==0 else y-191
                bend=(x+(-28 if i==0 else 26),ly+53);end=(min(lx+bw-21,x-27) if i==0 else max(lx-bw+16,x+30),ly+53)
                lead=[(x,y),bend,end]
                sh.poly(lead,(*N,224),5.0);sh.poly(lead,(*color,235),2.5)
                hit=(1-ease(0,14,n-(d['wipe_end']-5 if old else d['today'])-i*3));sh.disk(x,y,16+9*hit,(*N,148),(*color,245),2.8)
                sh.disk(x,y,7,(*color,255))
                a1,a2=(lx,lx+bw) if i==0 else (lx-bw,lx)
                sh.draw.rounded_rectangle(sh.box((a1,ly-1,a2,ly+56)),radius=round(8*self.s),fill=(*N,232))
                sh.text(lx+(13 if i==0 else -13),ly+11,label,36,(*F,255),'map','lt' if i==0 else 'rt')
            sh.put(im,amount)

    def captions(self,im,n,k):
        t=(n+.5)*FP;i=bisect_right(self.start,t)-1
        if i<0:return
        j,first,last,lines,pxs=self.groups[i];last_cue=self.cues[j];following=self.start[i+1] if i+1<len(self.start) else self.t['samples']
        end=min(following,last_cue['end_sample'] if last==last_cue['speech_end'] else following)
        end=min([end,*[start for start in self.subject_cuts if last<=start<end]])
        if t>=end:return
        intro=(t-first)/SR;u=ease(-.025,.132,intro)
        alpha=.48+.52*u
        if end+int(SR*.027)<following:alpha*=1-.94*ease(end-SR*.061,end,t)
        shade='sand' if k in (0,1,5,9,10) else 'aqua'
        last_y=1490 if k==4 else 1475
        for i,(words,px) in enumerate(zip(lines,pxs,strict=True)):
            row=last_y-(len(lines)-1-i)*max(83,pxs[-1]*.84)
            ws=tuple(w[0] for w in words);space=self.type.len(' ',px)*.87
            widths=[self.type.len(x,px) for x in ws];length=sum(widths)+space*(len(ws)-1)
            if length>746:
                px=round(px*746/length);space=self.type.len(' ',px)*.87
                widths=[self.type.len(x,px) for x in ws];length=sum(widths)+space*(len(ws)-1)
            assert px>=58,(words,px,length)
            x=493-length/2
            for (word,a,b,is_focus),w in zip(words,widths,strict=True):
                dt=(t-a)/SR
                # Word entrance eases ahead of the acoustic attack so the text
                # can be read in phrases. The focal relief moves on the word.
                accent=ease(-.031,.048,dt)*(1-.64*ease(.076,.30,dt))
                pop=accent*(.80+.20*exp(-max(0,dt)*6))
                strength=alpha*(.81+.19*ease(-.022,.072,dt))
                key=word.lower().strip(',.?')
                weight=1. if key in ('foot','prints','slump','fool','rewind','trail','route') else .75
                amount=weight*(18+17*pop) if is_focus else 0
                dip=9*ease(.048,.32,dt) if key=='slump' else 0
                self.type.stamp(im,word,px,x,row,strength,bob=13*(1-u)-9*pop*(1 if is_focus else .36)+dip,
                            tilt=(17+16*pop) if is_focus else 2.8*(1-u),yaw=(-9-14*pop) if is_focus else 0,
                            roll=(-1.4+1.8*pop) if is_focus else 0,boost=1+(.072 if is_focus else .014)*pop,
                            depth=amount,tint=shade if is_focus else 'ivory')
                x+=w+space
        self.word_frames+=1

    def paint(self,im,n,row):
        k=int(row[0]);assert k==bisect_right(self.cuts,n)-1
        im=im.point(self.colors[k]);im.paste(N,(0,0,*im.size),self.mask[k]);local=n-self.cuts[k]
        if k==4:self.split(im,local)
        elif k in (7,8):self.maps(im,n,row)
        else:
            key={0:'demo',1:'firm',2:'soft',3:'lip',5:'brazil',6:'cameroon',9:'layers',10:'demo'}[k]
            self.slates(key).put(im,1 if k in (0,10) else (.54+.46*ease(0,7,local)))
        self.captions(im,n,k)
        return im

    def measurement(self):
        return dict(text_bounds=self.report,pin_frames=self.map_frames,captioned_frames=self.word_frames,
                    total_word_plates=self.type.faces,perspective_extrusion_plates=self.type.extrusions)
