"""Hand-keyed editorial graphics. Coordinates are on the 1920×1080 design grid.

Actor/particle mattes come from the renderer's alpha pass. For the studio
insert, the guide curves come from the projected mandible rig, not a stock HUD.
"""
from functools import lru_cache
from math import hypot
import csv
import json
from hashlib import sha256
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
import numpy as np

from pilot import ROOT, WORK

FONTS = ROOT / 'assets' / 'fonts'
CREAM = (251, 238, 213)
AMBER = (255, 209, 135)
COOL = (163, 220, 214)
SEA = (105, 176, 166)
SMOKE = (25, 29, 23)
KEYS = [
    (77, 123, 'COMING DOWN'),
    (154, 194, 'NO GRIP'),
    (524, 588, 'JAW ROTATION / INWARD'),
    (604, 708, 'HOW DOES SHE GO UP?'),
]


def verify_fonts():
    for row in json.loads((FONTS/'sources.json').read_text()):
        assert sha256((FONTS/row['name']).read_bytes()).hexdigest() == row['sha256'], row['name']


def ease(a, b, f):
    t = max(0., min(1., (f-a)/(b-a)))
    return t*t*(3.-2.*t)


def settle(a, b, f):
    t = max(0., min(1., (f-a)/(b-a)))
    return 1.-(1.-t)**3


def rgba(rgb, alpha):
    return (*rgb, round(255*max(0, min(1, alpha))))


@lru_cache(maxsize=64)
def font(size, weight, mono):
    ft = ImageFont.truetype(str(FONTS/('IBMPlexMono.ttf' if mono else 'SpaceGrotesk.ttf')), size)
    if not mono:
        ft.set_variation_by_axes([weight])
    return ft


@lru_cache(maxsize=180)
def glyphs(s, size, weight, mono, tracking):
    """One antialiased tile; baseline aligned even for individually spaced glyphs."""
    ft = font(size, weight, mono)
    asc = -ft.getbbox(s, anchor='ls')[1]
    chars = []
    offset = 0.
    for i, char in enumerate(s):
        if i:
            p = s[i-1]
            offset += ft.getlength(p+char)-ft.getlength(p)-ft.getlength(char)+tracking
        chars.append((char, offset))
        offset += ft.getlength(char)
    m = Image.new('L', (max(4, round(offset)+12), asc+18))
    draw = ImageDraw.Draw(m)
    for ch, x in chars:
        draw.text((6+x, asc+4), ch, anchor='ls', fill=255, font=ft)
    return m


class Panel:
    def __init__(self, img, box, matte):
        self.img, self.r, self.matte = img, img.width/1920, matte
        self.box = tuple(round(t*self.r) for t in box)
        w = self.box[2]-self.box[0]; h = self.box[3]-self.box[1]
        self.layer = Image.new('RGBA', (w,h))

    def pos(self, x, y):
        return x*self.r-self.box[0], y*self.r-self.box[1]

    def over(self, mask, color, xy):
        im = Image.new('RGBA', mask.size, (*color, 0)); im.putalpha(mask)
        self.layer.alpha_composite(im, xy)

    def word(self, text, x, y, size, color, *, weight=650, mono=False, spacing=0, show=1, alpha=1,
             slant=.0, bottom=False, shadow=True):
        if show <= .002 or alpha <= .002:
            return
        size = max(1, round(size*self.r))
        tile = glyphs(text, size, weight, mono, round(spacing*self.r, 1))
        if show < .999 or alpha < .999:
            m = np.asarray(tile, dtype=np.float32)
            if show < .999:
                xx = np.arange(m.shape[1], dtype=np.float32)[None,:]
                yy = np.arange(m.shape[0], dtype=np.float32)[:,None]
                if bottom:
                    yy = m.shape[0]-1.-yy
                front = show*(m.shape[0]+abs(slant)*m.shape[1]+7)-5.
                m *= np.clip((front-yy-xx*slant+max(0.,-slant*m.shape[1]))/3.5+.5, 0, 1)
            tile = Image.fromarray(np.uint8(np.clip(m*alpha+.5, 0, 255)))
        px, py = self.pos(x, y)
        xy = round(px)-6, round(py)-4
        if shadow:
            s = tile.filter(ImageFilter.GaussianBlur(max(.8, 2.4*self.r)))
            self.over(s.point(lambda u:round(.51*u)), (26,18,11), (xy[0],xy[1]+round(2.8*self.r)))
        self.over(tile, color, xy)

    def pool(self, x, y, rx, ry, amount, color=(24, 20, 18)):
        """Local photographic falloff, with no hard rectangle or text strip."""
        if amount < .003: return
        X,Y = self.pos(x,y)
        a = ((np.arange(self.layer.width)[None,:]-X)/(self.r*rx))**2
        b = ((np.arange(self.layer.height)[:,None]-Y)/(self.r*ry))**2
        d = np.maximum(0.,1.-a-b)
        self.over(Image.fromarray(np.uint8(255*amount*d*d)), color, (0,0))

    def vector(self, fn):
        # Strokes and nodal markers are supersampled independently of FreeType.
        ratio = 2
        art = Image.new('RGBA', (self.layer.width*ratio,self.layer.height*ratio))
        draw = ImageDraw.Draw(art)
        scale = ratio*self.r
        def p(a):
            x,y = self.pos(*a);return round(x*ratio), round(y*ratio)
        def line(points, color, width=2.3):
            if len(points)>1:
                draw.line([p(t) for t in points], fill=color, width=max(1,round(width*scale)), joint='curve')
        def dot(point, rad, color, outline=False):
            x,y=p(point);r=rad*scale;box=(x-r,y-r,x+r,y+r)
            if outline:draw.ellipse(box,outline=color,width=max(1,round(1.8*scale)))
            else:draw.ellipse(box,fill=color)
        fn(line,dot)
        self.layer.alpha_composite(art.resize(self.layer.size,Image.Resampling.LANCZOS))

    def finish(self):
        if self.matte is not None:
            front = self.matte.crop(self.box)
            self.layer.putalpha(ImageChops.multiply(self.layer.getchannel('A'), ImageChops.invert(front)))
        self.img.alpha_composite(self.layer, (self.box[0],self.box[1]))


@lru_cache(maxsize=1)
def curves():
    a = {}
    with (WORK/'jaw-guide.csv').open() as f:
        for row in csv.DictReader(f):
            fr, side = int(row['frame']), int(row['side'])
            entry = a.setdefault(fr, dict(sweep=float(row['sweep']), curves={-1:[], 1:[]}))
            entry['curves'][side].append((float(row['x'])*1920,float(row['y'])*1080))
    assert set(a)==set(range(524,588)) and all(len(c)==37 for x in a.values() for c in x['curves'].values())
    return a


def down(img, f, matte):
    p = Panel(img, (0, 120, 930, 830), matte)
    op = ease(77, 87, f)*(1-ease(115,122,f))
    t = settle(92,104,f)
    tail = ease(113,123,f)
    y = 411+26*t+12*tail
    p.pool(274,454,635,307,.54*op)
    p.word('COMING', 136, 365-29*(1-settle(77,88,f)), 63, CREAM, weight=560, spacing=1.25,
           show=settle(78,91,f), alpha=op, slant=.045)
    p.word('DOWN', 130-14*tail, y, 133, AMBER, weight=700, spacing=-3.4,
           show=t, alpha=op, slant=.043)
    def trace(line,dot):
        w = ease(88,107,f)
        if w<=0:return
        a=(601,y-2);b=(601-21*w,y+76*w)
        line([a,b],rgba(CREAM,.71*op),2.7)
        if w>.68:
            v=ease(102,109,f)
            line([(b[0]-14*v,b[1]-18*v),b,(b[0]+21*v,b[1]-6*v)],rgba(AMBER,op*v),3.7)
        dot(a,3.1,rgba(AMBER,.90*op))
    p.vector(trace);p.finish()


def grip(img, f, matte):
    p = Panel(img, (0, 0, 825, 543), matte)
    t=settle(159,174,f);v=ease(184,194,f);o=1-ease(188,194,f)
    p.pool(221,230,560,282,.57*ease(154,166,f)*o)
    p.word('NO', 139-12*v, 156, 56, CREAM, weight=560, spacing=3.8,
           show=ease(154,162,f),alpha=o,slant=.078)
    p.word('GRIP', 133+30*(1-t)-31*v, 224+12*v, 117, AMBER, weight=700, spacing=-2.8,
           show=t, alpha=o, slant=.060)
    def shear(line,dot):
        z = ease(162,177,f)
        if z<=0:return
        left=141-32*v;y=343+5*v;break_at=left+91*z
        line([(left,y),(break_at,y)],rgba(CREAM,.62*z*o),2.8)
        x=break_at+8+19*v
        line([(x,y+3),(x+145*z*(1-v*.39),y+3)],rgba(AMBER,.78*z*o),2.8)
        dot((left,y),3.4,rgba(AMBER,.8*z*o))
    p.vector(shear);p.finish()


def inward(img, f, matte):
    p = Panel(img, (54,234,826,722), matte)
    entry = settle(530,548,f);out=1-ease(578,588,f)
    p.word('JAW ROTATION', 135, 412, 32, COOL, mono=True, spacing=4.1,
           show=ease(527,541,f),alpha=out*.91,shadow=False)
    p.word('INWARD', 132, 474, 105, CREAM, weight=690, spacing=7.7-8.9*entry,
           show=entry,alpha=out,slant=.032,shadow=False)
    def underline(line,dot):
        v=ease(528,550,f)*out
        if v>0:
            line([(135,388),(135+48*entry,388)],rgba(COOL,.90*v),2.7)
            dot((135,388),3.9,rgba(COOL,v))
    p.vector(underline);p.finish()
    c=curves()[f]
    p=Panel(img,(914,254,1916,975), matte)
    def jaw_vectors(line,dot):
        on=ease(528,541,f)*out
        s=min(1.,max(0.,c['sweep']))
        for side in (-1,1):
            k=c['curves'][side];col=COOL if side==1 else SEA
            for i in range(0,36,3):
                line(k[i:i+2],rgba(col,on*.42),1.75)
            active=s*35+1.
            n=int(active)
            at=tuple(a+(b-a)*(active-n) for a,b in zip(k[n],k[min(n+1,36)]))
            # Short leading arc, not an accumulating persistent trail over the head.
            if n>0:
                line([*k[max(0,n-8):n+1],at],rgba(col,on*(.58+.41*s)),2.35)
            dot(at,4.1,rgba(col,.96*on))
            dot(at,8.6,rgba(col,.61*on),outline=True)
            if s>.61 and n>=2:
                x,y=at; dx,dy=x-k[n-2][0],y-k[n-2][1];v=max(.01,hypot(dx,dy))
                dx,dy=dx/v,dy/v
                tip=(x+5*dx,y+5*dy)
                line([(tip[0]-15*dx-7*dy,tip[1]-15*dy+7*dx),tip,
                      (tip[0]-15*dx+7*dy,tip[1]-15*dy-7*dx)],rgba(col,on*.81),2.25)
    p.vector(jaw_vectors);p.finish()


def question(img, f, matte):
    p=Panel(img, (0,0,1072,594), matte)
    look=ease(604,621,f);leave=1-ease(700,708,f)
    rise=settle(650,671,f)
    o=look*leave
    p.pool(279,283,655,310,(.43 if f<673 else .62)*o,SMOKE)
    p.word('HOW DOES SHE',135,216,41,CREAM,weight=560,spacing=2.1,
           show=look,alpha=leave,slant=.06)
    p.word('GO',129,285+16*(1-rise),120,CREAM,weight=680,spacing=-2.5,
           show=settle(633,649,f),alpha=leave,slant=.018,bottom=True)
    p.word('UP?',336,285+51*(1-rise),120,AMBER,weight=700,spacing=-2.5,
           show=rise,alpha=leave,slant=-.016,bottom=True)
    def mark(line,dot):
        col=rgba(AMBER,o*.81)
        line([(137,186),(137+45*look,186)],col,2.5)
        if rise>.2:
            e=ease(657,671,f)
            a=(594,377);b=(594,377-72*e)
            line([a,b],rgba(AMBER,o*e*.84),3.1)
            if e>.7:line([(b[0]-12,b[1]+14),b,(b[0]+12,b[1]+14)],rgba(AMBER,o*e*.84),3.1)
    p.vector(mark);p.finish()


def composite(img, f):
    for (lo,hi,_), fn in zip(KEYS,(down,grip,inward,question)):
        if lo<=f<hi:
            # Source RGB is a complete plate, even where the actor mask is zero.
            # Compositing onto that non-opaque alpha would paint an opaque oval.
            matte = img.getchannel('A')
            img.putalpha(255)
            fn(img,f,matte)
            break
    return img
