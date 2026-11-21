"""Phone-safe editorial typography and independently anchored map markers."""
from __future__ import annotations
from functools import lru_cache
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
from spec import ROOT, W, H, FPS, SR, CUTS

FONTS=ROOT/'.cache/monarch-extinct/atlantic-tracks/animatic/fonts'
IVORY=(250,243,224)
GLACIER=(185,234,219)
OCHRE=(253,203,137)
INK=(10,19,23)
BOX=(68,214,932,1538)  # portrait UI exclusion, 1080×1920 reference pixels


def ease(a,b,t):
    u=max(0.,min(1.,(t-a)/(b-a)))
    return u*u*(3-2*u)


@lru_cache(maxsize=72)
def face(kind,px):
    if kind=='serif':
        f=ImageFont.truetype(str(FONTS/'Fraunces.ttf'),px)
        f.set_variation_by_axes([62,570,12,0]);return f
    if kind in ('sans','caption','map'):
        f=ImageFont.truetype(str(FONTS/'PlexSans.ttf'),px)
        f.set_variation_by_axes([640 if kind=='caption' else 565 if kind=='map' else 540,100]);return f
    return ImageFont.truetype(str(FONTS/'PlexMono.ttf'),px)


WRAPS={
    'the walls slump as the foot lifts.':('the walls slump','as the foot lifts.'),
    'Three-toed dinosaur tracks in Brazil.':('Three-toed dinosaur','tracks in Brazil.'),
    'roughly six thousand kilometres away today.':('roughly six thousand','kilometres away today.'),
    'Before the Atlantic opened here,':('Before the Atlantic','opened here,'),
    'both places were on the same landmass.':('both places were on','the same landmass.'),
    "But connected land isn't a trail.":('But connected land',"isn't a trail."),
    'So what in the rocks hints at a route?':('So what in the rocks','hints at a route?'),
}


class Layer:
    """Small alpha ROI; box measurements live in reference no matter proof size."""
    def __init__(self,s,b,report,scene,logical=''):
        self.s=s;self.b=b;self.origin=(round(s*b[0]),round(s*b[1]));self.report=report;self.scene=scene;self.logical=logical
        self.im=Image.new('RGBA',(round(s*b[2])-self.origin[0],round(s*b[3])-self.origin[1]));self.draw=ImageDraw.Draw(self.im)
    def pt(self,x,y):return (round(self.s*x)-self.origin[0],round(self.s*y)-self.origin[1])
    def box(self,a):return self.pt(*a[:2])+self.pt(*a[2:])
    def rect(self,a,c):self.draw.rectangle(self.box(a),fill=c)
    def poly(self,points,fill,stroke=0):self.draw.line([self.pt(*p) for p in points],fill=fill,width=max(1,round(stroke*self.s)),joint='curve')
    def disk(self,x,y,r,fill,outline=None,width=0):self.draw.ellipse(self.box((x-r,y-r,x+r,y+r)),fill=fill,outline=outline,width=max(1,round(width*self.s)))
    def text(self,x,y,t,px,c,kind='sans',anchor='lt',stroke=0,tracking=0):
        font=face(kind,round(self.s*px));X,Y=self.pt(x,y);w=round(stroke*self.s)
        opts=dict(font=font,anchor=anchor,stroke_width=w)
        if tracking:
            # Optical typewriter tracking. For caps don't inherit per-word
            # tracking from the expressive display/caption family.
            assert anchor=='lt'
            poses=[];dx=0.
            for k in t:
                poses.append((k,(X+round(dx),Y)));dx+=font.getlength(k)+tracking*self.s
            a,b,r,d=self.draw.textbbox((X,Y),t,**opts);r=max(r,X+round(dx))
        else:a,b,r,d=self.draw.textbbox((X,Y),t,**opts)
        if (X<0 or Y<0 or a<0 or b<0 or r>self.im.width+1 or d>self.im.height+1):raise ValueError((t,self.b,[a,b,r,d]))
        A,B,R,D=tuple(round((q+o)/self.s,3) for q,o in zip((a,b,r,d),self.origin*2,strict=True))
        if not(BOX[0]-2<=A<R<=BOX[2]+2 and BOX[1]-2<=B<D<=BOX[3]+2):raise ValueError((t,self.scene,[A,B,R,D]))
        self.report[self.scene][t]=[A,B,R,D]
        if tracking:
            # Use one common baseline; per-letter top anchors would float
            # punctuation independently, so calculate it from the whole run.
            base=font.getbbox(t,anchor='ls')[1]
            for ch,(X1,Y1) in poses:self.draw.text((X1,Y1-base),ch,font=font,anchor='ls',fill=c,stroke_width=w,stroke_fill=(*INK,226))
        else:self.draw.text((X,Y),t,fill=c,stroke_fill=(*INK,226),**opts)
    def put(self,im,a=1.):
        if a<.006:return
        mask=self.im.getchannel('A')
        if a<.999:mask=mask.point([round(a*x) for x in range(256)])
        im.paste(self.im,self.origin,mask)


class Layout:
    def __init__(self,size,cues):
        self.size=size;self.s=size[0]/W;assert round(H*self.s)==size[1]
        self.report=defaultdict(dict);self.active={};self.cues=cues;self.map_frames=0
        for n in range(CUTS[-1]):
            for i,c in enumerate(cues):
                a,b=c['start_sample'],c['end_sample'];f=(n+.5)*SR/FPS
                if a<=f<b:
                    assert n not in self.active
                    self.active[n]=(i,ease(a-1350,a+1440,f)*(1-.16*ease(b-960,b,f)))
        self.shades={i:self.veil(i) for i in range(10)}
    def roi(self,b,k,n=''):return Layer(self.s,b,self.report,k,n)
    def veil(self,k):
        h=self.size[1];a=[]
        for y in range(h):
            v=y/self.s
            if k in (1,2,3,4,5,8):
                hi=42 if k<=3 else 91
                u=hi*(1-ease(264,624,v))
            elif k in (0,9):u=28*(1-ease(259,420,v))
            else:u=0
            lo=(151 if k in (4,5,8) else 114 if k in (1,2,3) else 89)*(ease(1169,1635,v) if k not in (6,7) else ease(1287,1620,v))
            a.append(round(u+lo))
        s=Image.new('L',(1,h));s.putdata(a);return s.resize(self.size,Image.Resampling.NEAREST)
    @lru_cache(maxsize=20)
    def static(self,key):
        if key in ('formation','firm','soft','slump','layers'):
            y=260;scene=self.roi((69,231,916,438),key)
            if key in ('formation','layers'):
                ink=OCHRE if key=='formation' else GLACIER;word='CGI DEMO' if key=='formation' else 'SEDIMENT LAYERS  /  CGI'
                scene.rect((88,y+1,116,y+4),(*ink,255));scene.text(131,y-10,word,33,(*IVORY,236),'mono',stroke=2,tracking=1.05)
            else:
                ink=OCHRE if key=='firm' else GLACIER
                scene.rect((87,y,122,y+4),(*ink,250))
                scene.text(88,y+24,{'firm':'Firm mud','soft':'Soft mud','slump':'The wall gives way'}[key],63,(*IVORY,255),'serif',stroke=2)
                scene.text(91,y+108,'SAME FOOT · SAME VIEW' if key!='slump' else 'CLOSER VIEW · CGI',29,(*ink,237),'mono',stroke=2,tracking=1)
            return scene
        if key in ('brazil','cameroon'):
            br=key=='brazil';ink=OCHRE if br else GLACIER
            scene=self.roi((70,228,919,515),key)
            scene.rect((89,258,124,262),(*ink,255))
            scene.text(143,246,'SOUSA BASIN' if br else 'KOUM BASIN',34,(*ink,255),'mono',stroke=2,tracking=1.82)
            scene.text(85,300,'Brazil' if br else 'Cameroon',106,(*IVORY,255),'serif',stroke=1)
            scene.text(92,436,'ILLUSTRATIVE TRACK SURFACE',32,(*IVORY,239),'mono',stroke=2,tracking=1.60)
            return scene
        if key in ('today','past'):
            now=key=='today';ink=GLACIER if now else OCHRE
            scene=self.roi((69,231,919,493),key)
            scene.rect((90,259,129,263),(*ink,255))
            scene.text(149,247,'PRESENT DAY' if now else '125 MILLION YEARS AGO',36,(*ink,255),'mono',tracking=1.18)
            scene.text(85,311,'≈6,000 km' if now else 'Connected land',83,(*IVORY,255),'serif')
            scene.text(91,414,'BETWEEN THE TWO REGIONS' if now else 'MAP SNAPSHOT · NOT A TRACK DATE',30,(*IVORY,216),'mono',tracking=1.18)
            return scene
        raise KeyError(key)
    @lru_cache(maxsize=24)
    def caption(self,k):
        cue=self.cues[k]['text'];lines=WRAPS.get(cue,(cue,));px=57;h=66
        scene=self.roi((67,1340,930,1542),'captions')
        w=face('caption',round(self.s*px));longest=max(w.getlength(x)/self.s for x in lines)
        assert longest<798,cue
        x=492;top=1435-(len(lines)-1)*h
        # A narrow matte anchors the lettering over wet highlights without
        # occupying the animal's centre of action or the platform's right rail.
        bx=(x-longest/2-31,top-15,x+longest/2+31,1516)
        scene.draw.rounded_rectangle(scene.box(bx),radius=round(20*self.s),fill=(*INK,206))
        for i,text in enumerate(lines):scene.text(x,top+i*h,text,px,(*IVORY,255),'caption','mt',stroke=1)
        return scene
    def pins(self,im,pins,now,a):
        if a<.006:return
        # The label leaders end at their own anchors. There is intentionally
        # no connector or travelling dot from one fossil site to the other.
        coords=pins[:2] if now else pins[2:4]
        self.map_frames+=1
        r=self.roi((66,585,935,1335),'present pins' if now else 'ancient pins')
        for i,(u,v,z) in enumerate(coords):
            x,y=u*W,v*H
            if z<=0 or not(110<x<920 and 732<y<1250):raise ValueError((i,now,x,y,z))
            c=OCHRE if i==0 else GLACIER
            bx=88 if i==0 else 920
            by=(y-127 if now else y+104) if i==0 else (y-170 if now else y-188)
            tag=('Brazil' if i==0 else 'Cameroon')+('' if now else ' region')
            font=face('map',round(self.s*36));w=font.getlength(tag)/self.s
            right=bx+w+28 if i==0 else bx
            left=bx if i==0 else bx-w-28
            bend=x+(-24 if i==0 else 24)
            dst=(min(right,x-35),by+52) if i==0 else (max(left,x+34),by+52)
            line=[(x,y),(bend,by+52),dst]
            r.poly(line,(*INK,221),5.5);r.poly(line,(*c,210),2.5)
            r.disk(x,y,15,(*INK,162),(*c,247),2.6);r.disk(x,y,7,(*c,255))
            r.draw.rounded_rectangle(r.box((left,by-7,right,by+51)),radius=round(self.s*10),fill=(*INK,227))
            r.text(bx+(14 if i==0 else -14),by+4,tag,36,(*IVORY,255),'map',anchor='lt' if i==0 else 'rt')
        r.put(im,a)
    def paint(self,im,n,t):
        k=int(t[0]);expected=next(j for j in range(len(CUTS)-1) if CUTS[j]<=n<CUTS[j+1]);assert k==expected,(n,k,expected)
        im.paste(INK,(0,0,self.size[0],self.size[1]),self.shades[k]);q=n-CUTS[k]
        if k in (0,9):self.static('formation').put(im)
        elif k in (1,2,3,4,5,8):
            key={1:'firm',2:'soft',3:'slump',4:'brazil',5:'cameroon',8:'layers'}[k]
            self.static(key).put(im,1 if k<=2 else ease(-1,8,q))
        elif k in (6,7):
            f=n/FPS
            # Only display contemporary or paleogeographic pins within the
            # corresponding completed snapshot, never half-coastline states.
            today=1-ease(20.32,20.72,f);then=ease(21.63,22.05,f)
            poses=list(zip(t[4::3],t[5::3],t[6::3],strict=True));assert len(poses)==4
            self.static('today').put(im,today);self.static('past').put(im,then)
            self.pins(im,poses,True,today);self.pins(im,poses,False,then)
        if n in self.active:
            j,a=self.active[n];self.caption(j).put(im,a)
        return im
