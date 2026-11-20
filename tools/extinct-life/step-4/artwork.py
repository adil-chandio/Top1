"""Original motion diagrams and art direction for the Atlantic Tracks animatic.

Coordinates below use a 1280x720 stage; the production canvas is 1920x1080.
Geographic polygons and markers are the only data geometry. Everything else
is explicitly schematic, including all relief and all rock/age sections.
"""
from __future__ import annotations

from functools import lru_cache
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
from scipy.ndimage import distance_transform_edt
import shapefile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / '.cache/monarch-extinct/atlantic-tracks'
sys.path.insert(0, str(HERE.parent / 'step-2'))
import build_opening_board as maps  # noqa: E402 — licensed map geometry and finite rotations

W, H, SCALE = 1280, 720, 1.5
SIZE = (1920, 1080)
INK = '#101d21'
PAPER = '#f2ecdc'
MUTED = '#b5c7c2'
PALE = '#d7dacf'
TEAL = '#9ce0cb'
RUST = '#f3b67b'
EDGE = '#375356'
DARK = '#0b171b'
SLATE = '#1d3335'
AMBER = '#e9c88d'
PHOTO_KEYS = {'mayo': 'mayo-rey.jpg', 'sousa': 'sousa-bank.jpg', 'valley': 'cretaceous-valley.jpg'}


def clamp(v):
    return min(1., max(0., v))


def ease(v):
    v = clamp(v)
    return v * v * (3 - 2 * v)


def interp(a, b, u):
    return a + (b - a) * u


def pt(x, y):
    return round(x * SCALE), round(y * SCALE)


def bx(x, y, x1, y1):
    return (*pt(x, y), *pt(x1, y1))


def rgb(value):
    return tuple(bytes.fromhex(value.removeprefix('#')))


@lru_cache(maxsize=150)
def font(path, size, face):
    file = {'serif': 'Fraunces.ttf', 'mono': 'PlexMono.ttf', 'sans': 'PlexSans.ttf', 'strong': 'PlexSans.ttf'}[face]
    f = ImageFont.truetype(str(path / file), round(size * SCALE))
    if face == 'serif':
        f.set_variation_by_axes([max(22, min(90, size)), 630, 14, 0])
    elif face in ('strong', 'sans'):
        f.set_variation_by_axes([650 if face == 'strong' else 435, 100])
    return f


class Canvas:
    def __init__(self, font_dir, base):
        self.f = font_dir
        self.im = base.copy()
        self.d = ImageDraw.Draw(self.im)

    def text(self, x, y, s, sz=22, c=PAPER, face='sans', anchor='lt'):
        if s:
            self.d.text(pt(x, y), s, font=font(self.f, sz, face), fill=c, anchor=anchor)

    def measure(self, s, sz, face):
        return font(self.f, sz, face).getlength(s) / SCALE

    def lines(self, x, y, s, sz, width, face, color, leading=1.12, nowrap=False):
        for para in s.split('\n'):
            if not para:
                y += sz * leading
                continue
            toks = para.split()
            current = ''
            for token in toks:
                candidate = f'{current} {token}'.strip()
                if not nowrap and current and self.measure(candidate, sz, face) > width:
                    self.text(x, y, current, sz, color, face)
                    current = token
                    y += sz * leading
                else:
                    current = candidate
            self.text(x, y, current, sz, color, face)
            y += sz * leading
        return y

    def box(self, a, fill, outline=None, radius=0, weight=1):
        if radius:
            self.d.rounded_rectangle(bx(*a), radius=round(radius * SCALE), fill=fill, outline=outline, width=max(1, round(weight * SCALE)))
        else:
            self.d.rectangle(bx(*a), fill=fill, outline=outline, width=max(1, round(weight * SCALE)))

    def line(self, coords, fill, weight=1):
        self.d.line([pt(*p) for p in coords], fill=fill, width=max(1, round(weight * SCALE)), joint='curve')

    def poly(self, coords, fill, outline=None, weight=1):
        self.d.polygon([pt(*p) for p in coords], fill=fill, outline=outline, width=max(1, round(weight * SCALE)))

    def ellipse(self, a, fill=None, outline=None, weight=1):
        self.d.ellipse(bx(*a), fill=fill, outline=outline, width=max(1, round(weight * SCALE)))

    def dot(self, x, y, r, fill, outline=None):
        self.ellipse((x-r, y-r, x+r, y+r), fill, outline, 1.7)

    def paste(self, image, x, y, mask=None):
        self.im.paste(image, pt(x, y), mask=mask)

    def pill(self, x, y, label, tone, back=DARK):
        length = self.measure(label, 15, 'mono') + 28
        self.box((x, y, x+length, y+29), back, EDGE, 3)
        self.text(x+14, y+7, label, 15, tone, 'mono')

    def pointer(self, a, b, tone=RUST):
        self.line([a, b], tone, 1.6)
        self.dot(*a, 3.5, tone)

    def arrow(self, a, b, tone=RUST):
        self.line([a, b], tone, 2)
        th = math.atan2(b[1] - a[1], b[0] - a[0])
        self.poly([b, (b[0]-12*math.cos(th-.4), b[1]-12*math.sin(th-.4)),
                   (b[0]-12*math.cos(th+.4), b[1]-12*math.sin(th+.4))], tone)

    def frame_ticks(self, x, y, w, h, tone=EDGE):
        self.box((x, y, x+w, y+h), None, tone)
        for xx in (x, x+w):
            for yy in (y, y+h):
                self.line([(xx, yy + (12 if yy == y else -12)), (xx, yy), (xx + (12 if xx == x else -12), yy)], PALE, 1.4)


@lru_cache(maxsize=32)
def grain(w, h, seed):
    rng = np.random.default_rng(seed)
    values = rng.normal(0, 0.065, (h, w)).astype('float32')
    for sw, sh, amp in ((7, 5, .65), (22, 17, .37), (65, 49, .22), (155, 106, .13)):
        lo = rng.normal(0, amp, (sh, sw)).astype('float32')
        values += np.asarray(Image.fromarray(lo).resize((w, h), Image.Resampling.BICUBIC))
    return values


@lru_cache(maxsize=2)
def background(warm=False):
    w, h = SIZE
    yy, xx = np.ogrid[0:1:h*1j, 0:1:w*1j]
    light = 13 * np.exp(-2.5 * ((xx-.73)**2 + (yy-.39)**2)) - 4 * yy + grain(w,h,503)*2.3
    base = np.asarray((13, 24, 27) if not warm else (23, 24, 24), dtype='float32')
    return Image.fromarray(np.uint8(np.clip(base + light[...,None] * np.array((.47,.9,.86)), 0, 255)))


# An original generic three-toed silhouette. Never mapped to a fossil outline.
FOOT = ((.50,.95),(.43,.92),(.38,.84),(.38,.75),(.32,.68),(.24,.59),(.13,.50),(.07,.43),(.06,.37),(.10,.32),(.15,.33),(.24,.41),(.37,.52),(.42,.51),(.41,.42),(.41,.30),(.43,.16),(.47,.055),(.51,.019),(.55,.037),(.58,.135),(.59,.27),(.57,.43),(.58,.50),(.64,.51),(.73,.41),(.82,.32),(.88,.29),(.93,.31),(.94,.36),(.89,.44),(.80,.53),(.72,.61),(.65,.70),(.63,.77),(.62,.86),(.57,.93))


def smooth_ring(p):
    pts = list(p)
    out = []
    for i in range(len(pts)):
        a, b, c, d = [pts[j % len(pts)] for j in range(i-1,i+3)]
        for t in (0.,.25,.5,.75):
            out.append(tuple(.5*((2*y)+(-x+z)*t+(2*x-5*y+4*z-q)*t*t+(-x+3*y-3*z+q)*t*t*t) for x,y,z,q in zip(a,b,c,d)))
    return out


FOOT_RING = smooth_ring(FOOT)


def foot_points(x, y, w, h, degrees=0):
    a = math.radians(degrees)
    co, si = math.cos(a), math.sin(a)
    return [(x + (u-.5)*w*co-(v-.5)*h*si, y+(u-.5)*w*si+(v-.5)*h*co) for u,v in FOOT_RING]


@lru_cache(maxsize=42)
def terrain(width, height, style):
    """Procedural shaded sediment, no source photos or traced geometry."""
    w,h = pt(width,height)
    idx = ['crisp','soft','rim','empty','trail','varied','ripples','cracks','scan','other','hero'].index(style)
    n = grain(w,h,19 if idx < 4 else 19+idx)
    y,x = np.ogrid[:h, :w]
    phase = y / 19 + .37*np.sin(x/85.) + .18*np.sin((x+y)/63.)
    height_map = n*3.0 + 2.4*np.sin(x/34.+n+y/44) + .5*np.sin(y/5+x/13)
    darkness = np.zeros((h,w), dtype='float32')
    palette = {'crisp': (128,102,72), 'soft': (119,96,72), 'rim': (150,105,71),
               'scan': (91,132,124), 'trail': (117,111,82), 'varied': (126,112,84),
               'ripples': (102,128,120), 'cracks': (144,114,78), 'hero': (135,110,83),
               'other': (132,103,76)}.get(style, (121,101,74))
    if style in ('crisp','rim','soft','scan','other','hero','trail','varied'):
        multi = style in ('trail','varied')
        stamps = [(w*.48,h*.50,min(w*.42,h*.80),h*.82,-13 if style == 'other' else 9)]
        if style=='hero':
            stamps = [(w*.67,h*.46,h*.67,h*.81,11)]
        if style in ('rim','scan'):
            stamps = [(w*.5,h*.50,min(w*.41,h*.72),h*.81,7)]
        if multi:
            stamps = [(w*(.17+i*.163),h*(.69-i*.088+(.068 if i % 2 else -.039)),h*.224,h*.285,48+(i%2)*7) for i in range(5)]
        for i,(cx,cy,fw,fh,rot) in enumerate(stamps):
            m = Image.new('L',(w,h))
            ImageDraw.Draw(m).polygon(foot_points(cx,cy,fw,fh,rot),fill=1)
            mask = np.asarray(m, dtype=bool)
            sd = distance_transform_edt(mask) - distance_transform_edt(~mask)
            soft = style == 'soft' or (style=='varied' and i >= 2)
            sd = sd + n*(5 if soft else 1.6)
            sharpness = (11. if soft else 2.8) if not multi else (5.5 if soft else 2.5)
            depression = np.clip(.5 + sd / (3.6*sharpness), 0., 1.)
            height_map -= (9.5 if soft or multi else 15.2) * depression
            height_map += (5.2 if style=='rim' else 1.65) * np.exp(-((sd+2.8)/(5.5 if style=='rim' else 3.2))**2)
            darkness += (19. if soft else 22.)*depression
    if style == 'ripples':
        height_map += 4.8 * np.sin(phase * 3.22 + .27*n)
    if style == 'cracks':
        rng = np.random.default_rng(33)
        first = np.full((h,w), np.inf, dtype='float32'); second = first.copy()
        for cy in np.linspace(-.12*h, 1.13*h, 6):
            for cx in np.linspace(-.09*w,1.09*w,9):
                d = np.hypot(x-cx-rng.uniform(-.058,.058)*w,y-cy-rng.uniform(-.08,.08)*h).astype('float32')
                second = np.minimum(np.maximum(first, d),second)
                first = np.minimum(first,d)
        seam = np.exp(-((second-first+.7*n)/3.8)**2)
        height_map -= 3.5*seam
        darkness += 40*seam
    gy,gx = np.gradient(height_map)
    sun = .81 + .32*np.exp(-((x/w-.33)**2+(y/h-.28)**2)*2.35)
    value = sun[...,None]*np.array(palette) + (gx*31+gy*34+n*14. - darkness)[...,None]
    return Image.fromarray(np.uint8(np.clip(value, 17, 247)))


class Art:
    def __init__(self, sources, art, font_dir):
        self.font_dir = font_dir
        self.art_dir = art
        spec = json.loads((HERE.parent/'step-2/map-sources.json').read_text())
        for item in spec['inputs']:
            assert maps.digest(sources/item['name']) == item['sha256'], item['name']
        geo = json.loads((sources/'ne_110m_land.geojson').read_text())
        self.world = [g for f in geo['features'] for g in maps.polygons(f['geometry'])]
        with (sources/'125Ma_CS_v7.shp').open('rb') as shp:
            self.past = [g for shape in shapefile.Reader(shp=shp).iterShapes() for g in maps.polygons(shape.__geo_interface__)]
        r = maps.get_rotations(sources/'m06c9h_3id_forPgeog_19o_r1c.rot')
        self.early = tuple(maps.rotated(s, maps.reconstruction(p, 125., r)) for s,p in zip(maps.SITES,maps.PLATES))
        a,b = [maps.land_ids(p,self.world) for p in maps.SITES]
        c,d = [maps.land_ids(p,self.past) for p in self.early]
        assert a and b and a.isdisjoint(b) and c & d
        self.chart = {past: self.map_plate(past) for past in (False,True)}
        self.photos = {key: self.photo_plate(art/name) for key,name in PHOTO_KEYS.items()}

    @staticmethod
    def photo_plate(file):
        w, h = 2094, 1178
        photo = ImageOps.fit(Image.open(file).convert('RGB'), (w,h), Image.Resampling.LANCZOS)
        yy, xx = np.ogrid[0:1:h*1j,0:1:w*1j]
        dark = np.clip(.64/(1+np.exp((xx-.39)*19))+.72*np.maximum(0,(yy-.66))+.13*np.exp(-yy*10),.05,.81)
        value = np.asarray(photo)*(1-dark[...,None])+dark[...,None]*np.array((12,22,25))
        return Image.fromarray(np.uint8(np.clip(value, 0, 255)))

    @staticmethod
    def map_xy(latlon):
        lat,lon = latlon
        return (lon+76)*6.68,(32-lat)*6.68

    def map_plate(self, past):
        w,h = pt(775,454)
        mask = Image.new('L',(w,h))
        line = Image.new('L',(w,h))
        md, ld = ImageDraw.Draw(mask), ImageDraw.Draw(line)
        for outer,*holes in (self.past if past else self.world):
            if max(p[0] for p in outer)<-76 or min(p[0] for p in outer)>40 or max(p[1] for p in outer)<-36 or min(p[1] for p in outer)>32:
                continue
            for i,ring in enumerate((outer,*holes)):
                ring = [pt(*self.map_xy((y,x))) for x,y in ring]
                md.polygon(ring,fill=0 if i else 255)
                ld.line([*ring,ring[0]],fill=255,width=2)
        y,x = np.ogrid[0:1:h*1j,0:1:w*1j]
        relief = grain(w,h,233 if past else 241)
        sea = np.array((17.,41.,49.)) + (7*np.sin(x*1.7)+12*y+relief*5)[...,None]
        land = np.array((81.,105.,83.) if past else (71.,106.,103.))+(relief*18+10*np.sin(x*4))[...,None]
        base = np.where(np.asarray(mask)[...,None] > 0,land,sea)
        base = Image.fromarray(np.uint8(np.clip(base,0,255)))
        base.paste('#adbe9c' if past else '#8db5a8',(0,0,w,h),line)
        d = ImageDraw.Draw(base)
        for lon in range(-60,40,20):
            px=pt(*self.map_xy((0,lon)))[0]; d.line([(px,0),(px,h)],fill='#516c64',width=1)
        for lat in range(-20,21,20):
            py=pt(*self.map_xy((lat,0)))[1]; d.line([(0,py),(w,py)],fill='#4a6866',width=1)
        bloom = None
        if past:
            coords = [self.map_xy(p) for p in self.early]
            cx,cy = np.mean(np.array(coords),axis=0)*SCALE
            yy,xx = np.ogrid[:h,:w]
            # Broad conceptual area, land-limited and without a boundary or vector.
            v = .71 * np.exp(-(((xx-cx)/(133*SCALE))**2+((yy-cy)/(76*SCALE))**2)*2.2)
            v *= np.asarray(mask)/255.
            glow = np.asarray(base)*(1-v[...,None])+v[...,None]*np.array((241,185,102))
            bloom = Image.fromarray(np.uint8(glow))
        return base,bloom

    def chrome(self, c, shot, section, *, footer=True):
        tone = RUST if ('HYPOTHESIS' in shot.tag or 'LIMIT' in shot.tag) else TEAL
        c.box((64,49,78,58), RUST)
        c.text(91,45,'EXTINCT LIFE', 17, PAPER,'mono')
        if shot.style=='photo' or shot.variant=='end':
            width=c.measure(shot.tag,17,'mono')
            c.box((1201-width,34,1228,69),DARK,EDGE,4)
        c.text(1216,45,shot.tag, 17,tone,'mono','rt')
        if footer:
            c.line([(64,636),(1216,636)],EDGE)
            c.text(64,652,f'{section:02d}  /  ATLANTIC TRACKS',15,MUTED,'mono')
            for i in range(8):
                c.box((1055+i*21,653,1071+i*21,656),TEAL if i+1==section else EDGE)

    def header(self, c, shot, size=53, y=135, width=337):
        while max(c.measure(line,size,'serif') for line in shot.heading.split('\n')) > width and size>37:
            size -= 1
        yy = c.lines(64,y,shot.heading,size,width,'serif',PAPER,1.09)
        c.line([(65,yy+14),(108,yy+14)],RUST,2.5)
        c.lines(64,yy+39,shot.deck,25,width-14,'sans',MUTED,1.27)
        return yy+39

    def wide(self,c,shot):
        h = shot.heading.replace('\n',' ')
        c.text(64,94,h,50,PAPER,'serif')
        c.text(66,161,shot.deck,22,MUTED)

    def panel(self,c,w=752,h=430,tag='ORIGINAL SCHEMATIC'):
        c.box((464,129,464+w,129+h),SLATE,EDGE,4)
        c.text(464,581,tag,15,MUTED,'mono')

    def map_view(self,c,s,t):
        mode=s.variant
        past = mode not in ('open','focus','sousa','back','question','rocks')
        map_x,map_y = 442,110
        bloom = mode=='possible-end' or (mode=='possible' and t>=345.829)
        c.paste(self.chart[past][1 if bloom else 0],map_x,map_y)
        c.frame_ticks(map_x,map_y,775,454)
        points = [(map_x+x,map_y+y) for x,y in map(self.map_xy,self.early if past else maps.SITES)]
        active = (mode!='focus', mode!='sousa' and not (mode=='open' and t<2.645))
        color = (RUST,TEAL)
        for i,(px,py) in enumerate(points):
            if not active[i]:
                continue
            col = color[i]
            if past:
                ax,ay=(px-60,py-61) if not i else (px+59,py+54)
            else:
                ax,ay=(px-44,py+42) if not i else (px+47,py-47)
            if mode=='focus': ax,ay=px-68,py+70
            c.line([(px,py),(ax,ay)],col,1.5)
            c.dot(px,py,12,DARK, None)
            c.dot(px,py,7,col, PAPER)
            align = 'rt' if ax<px else 'lt'
            xx = ax+(-8 if ax<px else 8)
            c.text(xx,ay-9,('Sousa region' if not i else 'Koum region') if past else ('Sousa Basin' if not i else 'Koum Basin'),23,col,'strong',align)
            c.text(xx,ay+20,('Future Brazil' if not i else 'Future Cameroon') if past else ('Brazil' if not i else 'Cameroon'),17,PAPER,'sans',align)
        if past:
            c.text(461,527,'WESTERN GONDWANA',17,PALE,'mono')
            c.text(1216,580,'125 Ma MODEL SNAPSHOT  /  NOT A FOOTPRINT DATE',16,MUTED,'mono','rt')
        else:
            c.text(878,392,'ATLANTIC',19,'#b3cbcd','mono','mt')
            c.text(1216,580,'APPROXIMATE BASIN LOCATIONS',16,MUTED,'mono','rt')
        if bloom:
            c.pill(925,148,'ILLUSTRATIVE AREA',AMBER)
        if mode=='open':
            y = self.header(c,s,52,137)
            if t < 6.225:
                pts=foot_points(194,440,133,142,-11)
                c.poly(pts,'#546c60',RUST,1.5)
                c.text(65,535,'THREE-TOED TRACK • SCHEMATIC',14,PALE,'mono')
            else:
                self.metric(c,64,390,'≈6,000','KM APART TODAY',RUST)
        elif mode=='rewind':
            self.header(c,s,53,137)
            if t>=15.395: self.metric(c,64,388,'≈1,000','KM THEN  /  STUDY ESTIMATE',TEAL)
            else: self.metric(c,64,388,'125 Ma','ANCIENT MAP MODEL',TEAL)
        elif mode=='back':
            self.header(c,s,53,137)
            if t>=415.1: self.metric(c,64,388,'≈6,000','KM APART TODAY',RUST)
        elif mode=='rocks':
            self.header(c,s,63,201)
        else:
            self.header(c,s,53,149)

    def metric(self,c,x,y,value,label,tone=RUST):
        c.text(x,y,value,71,tone,'strong')
        c.text(x+2,y+83,label,17,PAPER,'mono')

    def title(self,c,s,t,u):
        chart=self.chart[True][0].resize(pt(1150,675),Image.Resampling.BICUBIC)
        alpha=np.empty(pt(1150,675)[::-1],dtype='uint8')
        alpha[:]=np.minimum(182,np.linspace(0,230,alpha.shape[1],dtype='uint8'))
        c.paste(chart,220,5,Image.fromarray(alpha))
        c.line([(67,190),(132,190)],RUST,3)
        c.text(65,137,'01   /   ATLANTIC TRACKS',19,TEAL,'mono')
        c.lines(63,222,s.heading,76,760,'serif',PAPER,1.01,nowrap=True)
        if t>=24.485:
            c.text(69,492,'A land connection is not a trail.',25,PALE)
        c.text(1216,573,'125 Ma RECONSTRUCTION  /  NOT A TRACK DATE',15,PALE,'mono','rt')

    def photo(self,c,s,t,u):
        photo=self.photos[s.variant]
        # A restrained 4% dolly; left and vertical scrims are in the photo plate.
        zoom=1.013+.047*ease(u)
        w,h=photo.size
        ww,hh=SIZE[0]/zoom,SIZE[1]/zoom
        x=(w-ww)*interp(.37,.64,ease(u)); y=(h-hh)*.57
        p=photo.transform(SIZE, Image.Transform.AFFINE, (ww/SIZE[0],0,x,0,hh/SIZE[1],y),Image.Resampling.BILINEAR)
        c.paste(p,0,0)
        self.header(c,s,62,231,434)

    def relief_panel(self,c,style,x=464,y=119,w=752,h=442):
        c.paste(terrain(w,h,style),x,y)
        c.frame_ticks(x,y,w,h)

    @lru_cache(maxsize=1)
    def hero_relief(self):
        y,x=np.ogrid[0:1:SIZE[1]*1j,0:1:SIZE[0]*1j]
        dark=np.clip(.14+.78/(1+np.exp((x-.47)*18))+.28*y**5,.1,.92)
        relief=np.asarray(terrain(W,H,'hero'))
        return Image.fromarray(np.uint8(relief*(1-dark[...,None])+dark[...,None]*np.array((11,24,26))))

    def imprint(self,c,s,t,u):
        v=s.variant
        if v=='end':
            c.paste(self.hero_relief(),0,0)
            self.header(c,s,59,173,425)
            if t>=433.419:
                c.lines(66,381,'Where could life\nhave gone next?',28,325,'sans',PAPER,1.25)
            c.text(1216,599,'ORIGINAL RELIEF STUDY',15,PAPER,'mono','rt')
            return
        style={'diffuse':'soft','rim':'rim'}.get(v,'crisp')
        self.relief_panel(c,style)
        if v=='fade':
            fading=clamp((t-177.458)/3.15)
            if fading>0:
                c.paste(Image.blend(terrain(752,442,'crisp'),terrain(752,442,'empty'),ease(fading)),464,119)
                c.frame_ticks(464,119,752,442)
        c.text(464,580,'ILLUSTRATIVE RELIEF  /  NOT A SPECIMEN IMAGE',15,MUTED,'mono')
        if v=='ruler':
            if t>=102.107:
                self.metric(c,64,163,'≈69','CENTIMETRES',TEAL)
                c.lines(66,287,s.deck,27,333,'sans',PAPER,1.20)
                c.text(66,390,'TK-034 · MEAN HIND-PRINT LENGTH',15,MUTED,'mono')
                x=1089; y=167; h=351
                c.box((x-17,y-10,x+70,y+h+18),'#242c29',PALE,3)
                c.line([(x,y),(x,y+h)],PAPER,2)
                for i in range(0,70):
                    yy=y+i*h/69
                    c.line([(x,yy),(x+(23 if i%10==0 or i==69 else 8),yy)],PAPER)
                    if i%10==0 or i==69:
                        label='69' if i==69 else str(i)
                        c.text(x+30,yy-8,label,14,PALE,'mono')
                c.text(1168,523,'cm',14,PALE,'mono','rt')
            else:
                c.text(65,211,'The impression',46,PAPER,'serif')
        else:
            self.header(c,s,54,147)
        if v=='count' and t>=45.538:
            self.metric(c,64,383,'283','FOOTPRINTS EXAMINED',TEAL)
        if v=='diffuse':
            c.pointer((864,264),(1018,218),PAPER)
            c.pill(1008,179,'DIFFUSE MARGIN',PAPER)
        if v=='rim' and t>=230.718:
            c.pointer((832,246),(1029,181))
            c.pill(1003,150,'RAISED RIM',RUST)

    def tracks(self,c,s,t,u):
        v=s.variant
        self.header(c,s,53,147)
        x,y,w,h=464,129,752,430
        self.relief_panel(c,'varied' if v=='changes' else 'trail',x,y,w,h)
        stamps=[(x+w*(.17+i*.163),y+h*(.69-i*.088+(.068 if i%2 else -.039))) for i in range(5)]
        if v=='way':
            for i,(px,py) in enumerate(stamps):
                if t>=s.at+i*.70:
                    c.ellipse((px-46,py-46,px+46,py+46),None,TEAL,1.7)
                    c.dot(px-32,py+55,14,DARK,TEAL)
                    c.text(px-32,py+49,str(i+1),15,PAPER,'mono','mt')
            if t>=52.778:
                self.metric(c,64,392,'34','TRACKWAYS DOCUMENTED',TEAL)
        if v=='stop':
            c.arrow((669,488),(1030,366),PAPER)
            c.text(667,503,'DIRECTION ON THIS SLAB',17,PAPER,'mono')
            if t>=60.728:
                c.line([(1154,157),(1154,513)],RUST,2)
                c.pill(917,482,'NO FURTHER PRINTS',RUST)
        if v=='changes':
            c.pill(501,158,'CLEARER',TEAL)
            c.pill(1033,158,'LESS DISTINCT',RUST)
        c.text(465,580,'SINGLE SCHEMATIC TRACKWAY  /  NOT A REGIONAL ROUTE',15,MUTED,'mono')

    def stack(self,c,s,t,u):
        v=s.variant
        self.header(c,s,54,147)
        spread = 52 if v=='preview' else (42+45*ease((t-65.3)/3.1) if v=='four' else 82)
        top0 = 192 if v=='preview' else 139
        erosion = ease((t-77.718)/2.1) if v=='erosion' else 0.
        tops = ('#638e81','#6b7460','#9a8568','#b38b63')
        sides = ('#304e47','#495449','#605543','#715944')
        for i in (3,2,1,0):
            y = top0+i*spread
            chipped = erosion*(29 if i in (0,2) else 0)
            a=(560,y); b=(1093-chipped,y+35); cc=(1002-chipped,y+133); d=(481,y+100)
            c.poly([d,cc,(cc[0],cc[1]+23),(d[0],d[1]+23)],sides[i],EDGE)
            c.poly([b,cc,(cc[0],cc[1]+23),(b[0],b[1]+23)],sides[i],EDGE)
            tip = (b[0]-chipped*.49,b[1]+chipped*.87)
            c.poly([a,b,tip,cc,d],tops[i],'#bac0a0',1.3)
            for k in range(2):
                r = 7 + k*8
                c.line([(d[0]+26,d[1]+r+2),(d[0]+210,d[1]+r+14),(cc[0],cc[1]+r-3)], '#8a8270',.8)
            for k in range(3):
                px=621+k*134+(i%2)*10; py=y+51+k*6+(i%2)*11
                c.poly(foot_points(px,py,43,26,-8+i*10),sides[i])
            if v!='preview' and (v=='erosion' or t>=65.6+i*.6):
                c.line([(b[0]+9,b[1]+20),(1133,b[1]+20)],TEAL if i==0 else MUTED,1.3)
                c.text(1143,b[1]+10,f'{i+1:02d}',21,TEAL if i==0 else MUTED,'mono')
            if chipped:
                c.poly([(1090+chipped*.6,y+41+chipped*.78),(1125+chipped*.7,y+53+chipped),
                        (1102+chipped*.71,y+82+chipped*1.25),(1080+chipped*.58,y+72+chipped*1.18)],tops[i],PAPER)
        c.text(480,581,'SCHEMATIC LAYER STACK  /  SEPARATION NOT TO TIME SCALE',15,MUTED,'mono')

    def scan(self,c,s,t,u):
        self.header(c,s,54,145)
        if s.variant=='views':
            for i,(px,py) in enumerate(((499,230),(712,173),(910,221))):
                if t<s.at+i*.84:
                    continue
                c.box((px-9,py-30,px+240,py+211),DARK,'#729792',5)
                c.paste(terrain(231,169,'crisp'),px,py)
                c.text(px+2,py-22,f'VIEW {i+1:02d}',15,TEAL,'mono')
                c.box((px+59+i*9,py+44,px+168+i*9,py+135),None,TEAL,0,2)
                c.line([(px+120,py+170),(835+(i-1)*33,476)],TEAL,1.4)
            c.box((754,462,922,511),DARK,EDGE,4)
            c.text(838,473,'SAME SLAB',18,PAPER,'mono','mt')
            if t>=87.838:
                self.metric(c,64,384,'2,000+','OVERLAPPING IMAGES',TEAL)
        else:
            self.relief_panel(c,'scan')
            sweep = ease((t-s.at)/2.4)
            if sweep<1:
                x=464+752*sweep
                for i in range(12):
                    y=132+i*34
                    c.line([(x,y),(1214,y)],'#a1c7bd',1)
                for i in range(22):
                    xx=round(x+(1215-x)*i/22)
                    c.line([(xx,131),(xx,559)],'#a1c7bd',1)
                c.line([(x,121),(x,560)],TEAL,2.6)
            c.pill(975,144,'SHADED RELIEF',TEAL)
        c.text(464,582,'ORIGINAL METHOD DIAGRAM  /  NOT SURVEY IMAGERY',15,MUTED,'mono')

    def stamp(self,c,s,t,u):
        self.wide(c,s)
        for i,(x,label) in enumerate(((64,'FIRMER MUD'),(664,'SOFTER MUD'))):
            v=s.variant
            if v=='other': label=('ILLUSTRATIVE SHAPE A','ILLUSTRATIVE SHAPE B')[i]
            if v=='press':
                p=ease((t-122.257)/2.86)
                release=126.077 if not i else 128.147
                shown=t>=release
                height=284
                style=('soft' if i else 'crisp') if shown else 'empty'
            else:
                p=1.; shown=True; height=284
                style=('other' if v=='other' else 'soft') if i else 'crisp'
            self.relief_panel(c,style,x,216,551,height)
            if not shown and t>=122.257:
                factor=1.15-.15*p
                sx=x+551*.48 + (1-p)*16; sy=216+height*.50-(1-p)*22
                c.poly(foot_points(sx+14,sy+17,201*factor,220*factor,9),'#594532')
                c.poly(foot_points(sx,sy,201*factor,220*factor,9),'#bba783',PAPER,1.9)
                c.pill(x+19,230,'SAME STAMP',PAPER)
            c.text(x,522,label,17,TEAL if not i else RUST,'mono')
            if v!='other':
                state = ('Holds the edge' if not i else 'Edges slump') if shown else 'One stamp, same scale'
                c.text(x,550,state,24,PAPER,'strong')
            else:
                c.text(x,550,'Not a species diagnosis',24,PAPER)

    def textures(self,c,s,t,u):
        self.header(c,s,57,146)
        for i,(x,style,lab,idea,when) in enumerate(((464,'ripples','Ripple marks','Moving water',157.688),
                                                    (850,'cracks','Mud cracks','Surface dried',160.828))):
            if t<when:
                c.box((x,154,x+366,502),SLATE,EDGE,4)
                c.text(x+183,320,f'CLUE {i+1:02}',19,MUTED,'mono','mt')
                continue
            self.relief_panel(c,style,x,154,366,358)
            c.text(x,529,lab,26,PAPER,'strong')
            c.text(x,569,idea,20,TEAL if i==0 else RUST)

    def bed(self,c,s,t,u):
        v=s.variant
        self.header(c,s,52,144)
        self.panel(c,tag='CONCEPTUAL CROSS-SECTION  /  NOT TO STRATIGRAPHIC SCALE')
        left,right=496,1184
        mid=852
        y0=290
        def ybase(x):
            und = 6*math.sin((x-491)/92)+3*math.cos(x/31)
            mark=(33+24*(v=='rim'))*math.exp(-((x-mid)/64)**2)
            edge = (13 if v=='rim' else 3)*(math.exp(-((x-mid-90)/17)**2)+math.exp(-((x-mid+90)/17)**2))
            return y0 + und + (mark-edge if v in ('bury','rim','sections') or (v=='drain' and t>=172.778) else 0)
        xs=np.linspace(left,right,106)
        profile=[(x,ybase(x)) for x in xs]
        bands=[profile]
        for i,depth in enumerate((69,107,149,187)):
            bands.append([(x,y0+depth+(5-i*.75)*math.sin(x/(54+i*17))+4*math.cos(x/(41+i*7))) for x in xs])
        bands.append([(x,520) for x in xs])
        for i,(a,b,fill) in enumerate(zip(bands,bands[1:],('#b58b60','#765e48','#9b7b56','#55645b','#494e42'))):
            c.poly([*a,*reversed(b)],fill,EDGE)
            c.line(a,'#d7b685' if i==0 else '#b29166',1.1)
            for q in (.25,.52,.82):
                lamina=[(x,interp(y,yy,q)+1.1*math.sin(x/16.+q*2)) for (x,y),(_,yy) in zip(a,b)]
                c.line(lamina,'#cda978' if i in (0,2) else '#8a856c',.7)
        if v=='clues':
            c.pointer((861,ybase(861)),(962,244),TEAL); c.pill(947,206,'RIPPLED BED',TEAL)
            c.pointer((931,426),(1019,465),RUST); c.pill(1010,470,'DRIED SURFACE',RUST)
        if v=='drain':
            p=ease((t-168.9)/3.7)
            air=interp(222,318,p)
            wet=[(x,y) for x,y in profile if y>air]
            if wet:
                c.poly([(wet[0][0],air),(wet[-1][0],air),*reversed(wet)], '#4f8e87',TEAL)
            c.pill(514,162,'WATER COVER' if t<172.6 else 'EXPOSED GROUND',TEAL)
            if t>=172.778:
                c.pointer((852,321),(934,242),RUST); c.pill(945,212,'A STEP CAN REGISTER',RUST)
        if v=='bury':
            p=ease((t-s.at)/3.0)
            seal=[(x,y-((y-224)*p)) for x,y in profile]
            c.poly([*seal,*reversed(profile)], '#d1a272',PALE)
            c.line(profile,'#43382e',2)
            c.pill(917,163,'NEW SEDIMENT',RUST)
            c.pointer((853,318),(986,365),PAPER); c.pill(974,371,'BURIED SURFACE',PAPER)
        if v=='rim':
            c.pointer((763,279),(650,219),RUST); c.pill(509,185,'DISPLACED EDGE',RUST)
            c.pointer((940,278),(1064,211),RUST); c.pill(1014,176,'RAISED RIM',RUST)

    @lru_cache(maxsize=8)
    def mineral_plate(self,variant):
        w,h=pt(500,398)
        out=Image.new('RGB',(w,h),'#4a8080' if variant=='cement' else '#995e43')
        d=ImageDraw.Draw(out)
        rng=np.random.default_rng({'cement':776,'mat':417,'sousa':421}[variant])
        for y in np.linspace(-10,h+10,12):
            for x in np.linspace(-25,w+20,15):
                cx=x+rng.uniform(-12,12); cy=y+rng.uniform(-11,11)
                a=rng.uniform(18,29); b=rng.uniform(16,28)
                r=rng.uniform(0,2*math.pi)
                shape=[(round(cx+math.cos(r+i*math.pi/4)*a*rng.uniform(.76,1.22)),
                        round(cy+math.sin(r+i*math.pi/4)*b*rng.uniform(.73,1.08))) for i in range(8)]
                shade=rng.uniform(.66,1.13)
                col=tuple(round(v*shade) for v in ((152,135,101) if variant!='sousa' else (181,121,79)))
                d.polygon(shape, fill=col, outline='#655440', width=1)
                d.line(shape[:4], fill='#bfa77a', width=1)
        return out

    def micro(self,c,s,t,u):
        v=s.variant
        self.header(c,s,53,145)
        self.panel(c,tag='SCHEMATIC DETAIL  /  NOT A MICROGRAPH')
        if v=='pollen':
            cx,cy,r=829,338,155
            rads=np.linspace(0,2*math.pi,153,endpoint=False)
            shape=[(cx+math.cos(a)*(r+4*math.sin(5*a)),cy+math.sin(a)*(r+5*math.cos(7*a))) for a in rads]
            c.poly(shape,'#3d5b54',AMBER,1.6)
            for j in range(35,0,-1):
                a=r*j/36
                curve=j/35
                x0=cx-22*(1-curve); y0=cy-33*(1-curve)
                col=tuple(round(interp(lo,hi,1-curve)) for lo,hi in zip((62,89,77),(174,159,108)))
                c.ellipse((x0-a,y0-a,x0+a,y0+a),col)
            rng=np.random.default_rng(538)
            for a in np.arange(0,2*math.pi,.104):
                d=rng.uniform(10,21)
                c.line([(cx+(r-8)*math.cos(a),cy+(r-8)*math.sin(a)),(cx+(r+d)*math.cos(a),cy+(r+d)*math.sin(a))],AMBER,1.9)
            for _ in range(365):
                dx,dy=rng.uniform(-1,1,2)*r
                if dx*dx+dy*dy<.89*r*r:
                    c.dot(cx+dx,cy+dy,rng.uniform(1,3.2),'#5d7560',None)
            c.line([(cx-82,cy-71),(cx-52,cy-40),(cx-36,cy-10),(cx-32,cy+18)],'#bdd7ab',2)
            c.pill(958,171,'GENERIC GRAIN',TEAL)
            return
        # An illustrated microscope field with grained outlines and a thin mat.
        width,height=500,398
        plate=self.mineral_plate(v)
        mask=Image.new('L',plate.size)
        ImageDraw.Draw(mask).ellipse((2,2,plate.width-2,plate.height-2),fill=255)
        x,y=562,145
        c.paste(plate,x,y,mask)
        c.ellipse((x,y,x+width,y+height),None,'#9ebbb2',1.5)
        if v=='cement':
            c.pointer((730,260),(535,192),AMBER); c.pill(485,156,'GRAIN',AMBER)
            c.pointer((946,313),(1072,244),TEAL); c.pill(1010,207,'CEMENT',TEAL)
            if t>=189.858:
                c.text(814,495,'EVIDENCE OF EARLY CEMENTATION',16,PAPER,'mono','mt')
        else:
            xy=[(xx,226+5.4*math.sin(xx/23)+2.*math.cos(xx/4.4)) for xx in np.linspace(610,1014,135)]
            c.line(xy,'#2a4941',11)
            c.line(xy,TEAL,5)
            c.pointer((914,229),(1040,177),TEAL); c.pill(940,147,'POSSIBLE MAT',TEAL)
            c.text(814,495,'ILLUSTRATED SURFACE LAYER',16,PAPER,'mono','mt')

    def compare(self,c,s,t,u):
        self.wide(c,s)
        for i,(x,place,sub,style,tone,key) in enumerate((
            (64,'Koum Basin','Sediment stabilization','ripples',TEAL,'mayo'),
            (665,'Sousa Basin','Cohesion and raised rims','cracks',RUST,'sousa'),
        )):
            if s.variant=='banks':
                photo=ImageOps.fit(self.photos[key],pt(551,266),Image.Resampling.BICUBIC,centering=(.74,.58))
                c.paste(photo,x,216)
                c.frame_ticks(x,216,551,266)
                sub = 'Landscape illustration'
            else:
                self.relief_panel(c,style,x,216,551,266)
            c.text(x,501,place,26,tone,'strong')
            c.text(x,544,sub,24,PAPER)
        c.text(64,599,'SEPARATE BASINS  /  NO SPECIMEN MATCH',15,MUTED,'mono')

    def age(self,c,s,t,u):
        v=s.variant
        self.header(c,s,53,146)
        self.panel(c,tag='QUALITATIVE AGE COMPARISON  /  NO DATED GAP IMPLIED')
        if v in ('regional','unmatched'):
            for i,(x,label,col) in enumerate(((515,'KOUM BASIN',TEAL),(873,'SOUSA BASIN',RUST))):
                c.text(x,166,label,17,col,'mono')
                for k,color in enumerate(('#716854','#a68662','#434f47','#967356','#655f53')):
                    y=213+k*51
                    c.box((x,y,x+290,y+49),color,EDGE,2)
                    for j in range(4):
                        yy=y+9+8*j
                        c.line([(x+5,yy),(x+136,yy+(-3 if j%2 else 3)),(x+286,yy+2)],'#b19c77',.8)
                tr_y=264 if i else 315
                c.box((x,tr_y,x+290,tr_y+49),None,col,1,2)
                c.text(x+16,tr_y+16,'TRACK BED',18,PAPER,'mono')
                if v=='regional':
                    yy=233 if i else 452
                    c.dot(x+258,yy,7,AMBER,DARK)
                    c.text(x+240,yy-9,'REGIONAL CLUE',16,PAPER,'mono','rt')
            c.text(838,494,'COLUMNS NOT CORRELATED',18,PAPER,'mono','mt')
        else:
            c.box((508,171,1178,241),'#345c56',TEAL,3,1.5)
            c.text(843,191,'EARLY CRETACEOUS',24,PAPER,'mono','mt')
            for i,(y,col,place) in enumerate(((279,TEAL,'KOUM'),(368,RUST,'SOUSA'))):
                c.box((508,y,1178,y+65),DARK,EDGE,4)
                c.text(525,y+22,place,18,col,'mono')
                for x in range(666,1156,19):
                    c.line([(x,y+47),(x+14,y+19)],EDGE,1.2)
                c.pill(843,y+19,'EXACT TRACK AGE UNRESOLVED',col)
            c.text(842,483,'A BROAD PERIOD IS NOT A SHARED DATE',18,PAPER,'mono','mt')

    def fault(self,c,s,t,u):
        v=s.variant
        self.header(c,s,51,144)
        self.panel(c,tag='TECTONIC SCHEMATIC  /  NOT TO SCALE OR TIME')
        if v=='stages':
            for i,(y,phase) in enumerate(((164,'CONNECTED LAND'),(278,'CRUST STRETCHES'),(392,'OCEAN WIDENS'))):
                if i and t < (402.879,405.759,408.28)[i]:
                    continue
                left,right,mid=507,1174,840
                h=72
                gap=(0,54,155)[i]
                c.box((left,y,right,y+h),'#0e262e',EDGE,4)
                c.poly([(left,y+24),(mid-gap,y+24),(mid-gap+10,y+49),(mid-gap-3,y+h),(left,y+h)],'#839380',EDGE)
                c.poly([(mid+gap,y+24),(right,y+24),(right,y+h),(mid+gap-9,y+h),(mid+gap-11,y+49)],'#849582',EDGE)
                c.line([(left,y+49),(mid-gap+6,y+49)],AMBER,1.6)
                c.line([(mid+gap-8,y+49),(right,y+49)],TEAL,1.6)
                if gap:
                    c.line([(mid-gap,y+48),(mid+gap,y+48)],'#78bbbc',1)
                c.text(left,y-18,phase,15,PAPER,'mono')
            return
        sink=0.38 if v=='structures' else (ease((t-312.463)/3.1) if v=='sink' else 1.)
        fill=(ease((t-316.363)/2.8) if v=='sink' else (1. if v=='fill' else 0.))
        y=246
        bed=y+25+89*sink
        lx=693-26*sink; rx=991+30*sink
        bottom=510
        bands=[]
        for depth in (0,44,91,155,300):
            q = [(497,y+depth),(lx,y+depth),(lx+53,bed+depth),(rx-55,bed+depth),(rx,y+depth),(1183,y+depth)]
            bands.append([(px,min(py,bottom)) for px,py in q])
        for a,b,color in zip(bands,bands[1:],('#9d8769','#54685e','#776d57','#594e47')):
            c.poly([*a,*reversed(b)],color,EDGE)
            c.line(a,'#bfaa81',1.6)
            c.line([(x,interp(y,yy,.45)) for (x,y),(_,yy) in zip(a,b)],'#958a70',1)
        c.line([(lx,y),(lx+73,bottom)],RUST,1.8)
        c.line([(rx,y),(rx-75,bottom)],RUST,1.8)
        if fill:
            for i in range(6):
                k=fill*(i+1)/6
                a=bed-k*64; b=a+fill*64/6+1
                el=lx+53-(bed-a)/(bed-y)*53
                er=rx-55+(bed-a)/(bed-y)*55
                c.poly([(el,a),(er,a),(er-5,b),(el+5,b)],'#be9b69' if i%2 else '#d2b680',EDGE)
            c.pill(747,180,'RIVER + LAKE DEPOSITS',TEAL)
        else:
            c.pointer((lx+36,bed+12),(611,384),RUST); c.pill(517,388,'FAULT',RUST)
            c.pointer((rx-28,bed-7),(1106,383),RUST); c.pill(1080,394,'FAULT',RUST)
            if v=='sink':
                c.arrow((695,183),(566,183),TEAL)
                c.arrow((984,183),(1112,183),TEAL)

    def network(self,c,s,t,u):
        v=s.variant
        self.header(c,s,53,146)
        self.panel(c,tag='CONCEPT DIAGRAM  /  NOT A MAPPED ROUTE')
        if v=='generations':
            c.text(514,172,'HABITAT PATCHES',20,TEAL,'mono')
            for i,(cx,cy,when) in enumerate(((603,311,349.1),(838,375,351.25),(1075,297,353.4))):
                c.ellipse((cx-91,cy-53,cx+91,cy+53),'#304e47',EDGE,2)
                live=t>=when
                tone=TEAL if live else '#52766b'
                for a in (1,.76,.53):
                    c.ellipse((cx-75*a,cy-34*a,cx+75*a,cy+34*a),None,tone,1.5)
                if live: c.dot(cx,cy,6,TEAL)
                c.text(cx,cy+72,f'PATCH {i+1:02}',17,PAPER,'mono','mt')
            c.text(839,498,'A POSSIBILITY, NOT ONE ANIMAL’S JOURNEY',16,MUTED,'mono','mt')
        else:
            cards = [('REGIONAL ROCK','Tracks near rivers and lakes',TEAL,s.at),
                     ('OTHER BASINS','A separate fish-fossil pattern',RUST,s.at+.65),
                     ('GEOGRAPHY','Do these fit an old river system?',TEAL,s.at+1.2)] if v=='test' else [
                     ('MORE SITES','Find evidence between regions',TEAL,384.019),
                     ('NARROWER DATES','Reduce uncertainty in time',RUST,386.15),
                     ('IDENTIFIABLE FOSSILS','Distinguish more of the animals',TEAL,387.7)]
            for i,(name,body,tone,when) in enumerate(cards):
                y=164+i*111
                c.box((507,y,1172,y+91),DARK,EDGE,4)
                c.box((507,y+6,513,y+85),tone if t>=when else EDGE)
                if t>=when:
                    c.text(536,y+14,name,16,tone,'mono')
                    c.text(535,y+44,body,26,PAPER,'strong')

    @lru_cache(maxsize=2)
    def fish_engraving(self):
        w,h=pt(721,352)
        surface=Image.new('RGBA',(w,h))
        d=ImageDraw.Draw(surface)
        # General lobe-finned fish anatomy, without claiming a particular fossil.
        body=smooth_ring(((45,163),(59,122),(113,106),(201,85),(307,90),(405,117),(487,149),
                           (529,151),(554,120),(600,75),(623,82),(604,132),(623,145),(673,158),
                           (678,177),(634,188),(602,186),(611,212),(632,253),(610,262),(554,221),
                           (526,198),(458,200),(383,234),(291,248),(214,247),(94,213),(52,187)))
        region=[pt(x,y) for x,y in body]
        scale_mask=Image.new('L',(w,h)); ImageDraw.Draw(scale_mask).polygon(region,fill=255)
        finpaths=[[(153,114),(185,73),(243,26),(283,92)],[(376,120),(413,97),(468,99),(485,142)],
                  [(175,202),(202,231),(221,267),(195,301),(171,294),(165,251),(152,225)],
                  [(320,230),(355,253),(384,299),(348,321),(320,303),(315,272),(303,242)],
                  [(427,216),(458,236),(505,250),(472,203)]]
        for f in finpaths:
            fp=smooth_ring(f)
            d.polygon([pt(x,y) for x,y in fp],fill='#537e72',outline='#d2ca9e',width=2)
            for x,y in fp[4:][::4]:
                d.line([pt(*f[0]),pt(x,y)],fill='#95af95',width=1)
        d.polygon(region,fill='#6d8e79',outline='#e2d9ae',width=3)
        hatches=Image.new('RGBA',(w,h)); hd=ImageDraw.Draw(hatches)
        for j,y in enumerate(range(93,251,14)):
            for x in range(157+(j%2)*9,529,19):
                hd.arc(bx(x-11,y-10,x+12,y+11),-76,80,fill='#b4b598',width=1)
        for i in range(10):
            y=135+i*6
            hd.line([pt(501,y),pt(621,y+((i-4)*5))],fill='#a6b69a',width=1)
        surface.paste(hatches,(0,0),ImageChops.multiply(hatches.getchannel('A'),scale_mask))
        d.arc(bx(67,123,151,212),-62,87,fill='#d9cfa7',width=2)
        d.line([pt(53,177),pt(109,181)],fill=DARK,width=3)
        d.ellipse(bx(89,131,116,158),fill='#d0b77f',outline=PAPER,width=2)
        d.ellipse(bx(98,138,109,149),fill=DARK)
        return surface

    def fish(self,c,s,t,u):
        self.header(c,s,52,148)
        self.panel(c,tag='COELACANTH ILLUSTRATION  /  NOT A SPECIMEN IMAGE')
        art=self.fish_engraving()
        if s.variant=='intro':
            c.paste(art,478,161,art.getchannel('A'))
            if t>=362.5:
                c.text(832,493,'Mawsonia',38,TEAL,'serif','mt')
        else:
            art=art.resize(pt(618,302),Image.Resampling.LANCZOS)
            c.paste(art,527,135,art.getchannel('A'))
            for i,(x,label,tone) in enumerate(((495,'SOUTH AMERICAN BASINS',RUST),(848,'AFRICAN BASINS',TEAL))):
                c.box((x,449,x+328,518),DARK,EDGE,4)
                c.text(x+15,465,label,16,tone,'mono')
                c.text(x+15,489,'Fish fossils in other basins',18,PAPER)

    def credits(self,c,s,t,u):
        c.text(65,120,'Sources & maps',64,PAPER,'serif')
        c.line([(65,209),(1216,209)],EDGE,1.2)
        c.text(66,244,'THE TRACK SCIENCE',17,TEAL,'mono')
        for i,line in enumerate(('Jacobs et al. • Bulletin 95 (2024)',
                                  'Menkem et al. • J. Palaeogeography (2026)',
                                  'Carvalho et al. • Cretaceous Research (2013)')):
            c.text(66,284+i*48,line,24,PAPER)
        c.text(691,244,'MAP DATA',17,RUST,'mono')
        for i,line in enumerate(('Natural Earth • public domain',
                                 'Kocsis & Scotese • PaleoCoastlines v7.1',
                                 'CC BY 4.0 • cropped, recoloured, annotated')):
            c.text(691,284+i*48,line,24,PAPER)
        c.text(691,423,'creativecommons.org/licenses/by/4.0',18,MUTED)
        c.line([(66,479),(1216,479)],EDGE,1.2)
        c.text(66,507,'Drawn diagrams and AI landscape illustrations. No field photography or published specimen panels.',22,MUTED)
        c.text(66,554,'ATLANTIC TRACKS   /   NARRATION v2   /   ROUGH PICTURE',16,TEAL,'mono')

    def frame(self,shot,seconds,section,end):
        u=clamp((seconds-shot.at)/(end-shot.at))
        c=Canvas(self.font_dir,background(shot.variant in ('sousa','rim','mat')))
        if shot.style=='photo':
            self.photo(c,shot,seconds,u)
        elif shot.style=='map':
            self.map_view(c,shot,seconds)
        else:
            getattr(self,shot.style)(c,shot,seconds,u)
        self.chrome(c,shot,section,footer=shot.style!='credits')
        return c.im
