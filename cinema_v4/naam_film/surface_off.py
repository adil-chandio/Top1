"""NAAM LO — SURFACE-OFF build. Depth-sliced plate stage, moving key light,
x-ray dissolve, physical type, hidden cuts. 1080x1920 / 30 fps.
Devices: D1 photo-to-flesh · D2 surface-off · D3 word-matter · D4 one-take · D5 light-handshake
         D6 anamorphic · D9 silence punch · D10 shadow truth
"""
import numpy as np, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance
import imageio_ffmpeg
from collections import OrderedDict

W, H, FPS = 1080, 1920, 30
P = "plates/"
MASK = "../reference/CHARACTER_MASKED_PORTRAIT.png"
F_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
F_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

CREAM = (246, 240, 230)
RED = (226, 46, 34)
GOLD = (214, 168, 92)
CYAN = (96, 208, 230)
FOG = (9, 11, 15)

NS = 6          # depth slices
FEATHER = 0.19

# ---------------------------------------------------------------- shot map
# (t0, t1, plate, dolly, px, py, focus, light, device)
SHOTS = [
    (0.0, 1.6,  "p01",  0.16,   0,   0, 0.62, "sweepL", None),
    (1.6, 3.2,  "p01",  0.10, -46,  10, 0.55, "sweepR", None),
    (3.2, 4.8,  "p02",  0.14,   0,  22, 0.70, "top",    None),
    (4.8, 6.4,  "p03",  0.15,  30,   0, 0.60, "sweepL", None),
    (6.4, 8.0,  "p03",  0.20, -34,   0, 0.50, "sweepR", None),
    (8.0, 9.6,  "p04",  0.12,   0,  16, 0.60, "side",   None),
    (9.6, 11.2, "p05",  0.18, -52,   0, 0.45, "godray", None),
    (11.2, 12.8,"p05",  0.22,   0, -18, 0.55, "godray2",None),
    (12.8, 14.4,"p06",  0.16,  28,   0, 0.60, "sweepL", None),
    (14.4, 16.0,"p06",  0.20, -24,   0, 0.55, "sweepR", None),
    (16.0, 17.6,"p05",  0.14,   0,  14, 0.50, "side",   None),
    (17.6, 19.2,"p06",  0.24,   0, -24, 0.62, "top",    None),
    (19.2, 20.8,"p06",  0.12,   0,   0, 0.55, "sweepL", "soff"),
    (20.8, 22.4,"p05",  0.16,  26,   0, 0.60, "sweepR", None),
    (22.4, 24.0,"p08",  0.12,   0,  10, 0.55, "coldmoon",None),
    (24.0, 25.6,"p08",  0.10, -30,   0, 0.60, "coldmoon",None),
    (25.6, 27.2,"p09",  0.14,   0,   0, 0.62, "day",    None),
    (27.2, 28.8,"p09",  0.18,  34,   0, 0.55, "day",    None),
    (28.8, 30.4,"p10",  0.16,   0,  14, 0.58, "side",   None),
    (30.4, 32.0,"p10",  0.22, -26,   0, 0.52, "sweepL", None),
    (32.0, 33.6,"p03",  0.18,   0, -12, 0.55, "top",    None),
    (33.6, 35.2,"p05",  0.20,  30,   0, 0.60, "godray", None),
    (35.2, 36.8,"p06",  0.24,   0,  20, 0.55, "side",   None),
    (36.8, 38.4,"p06",  0.16,   0,  -8, 0.58, "sweepR", None),
    (38.4, 40.0,"p01",  0.20,  24,   0, 0.50, "sweepL", "soff"),
    (40.0, 41.6,"p01",  0.14, -20,  10, 0.55, "sweepR", None),
    (41.6, 43.2,"MASK", 0.16,   0,   0, 0.55, "red",    "xray"),
    (43.2, 44.8,"MASK", 0.10,  16,   0, 0.60, "red",    None),
    (44.8, 46.4,"MASK", 0.12,   0,  -8, 0.55, "red",    "xray2"),
    (46.4, 48.0,"MASK", 0.22,   0,  10, 0.62, "red",    None),
]

# ---------------------------------------------------------------- caption cards (2-5 words)
CARDS = [
    (0.0,  3.2,  "TEEN SAU CARD.",                 "CARD"),
    (3.2,  6.4,  "PAANCH NAAM.",                   None),
    (6.4,  9.6,  "NAAM EK BHI NAHI.",              "NAHI"),
    (9.6,  12.8, "LOG HAIN.",                      None),
    (12.8, 16.0, "LOGON KE NAAM NAHI HOTE.",       "NAAM"),
    (16.0, 19.2, "PENCIL RUK GAYI.",               "RUK"),
    (19.2, 22.4, "EK NAAM.",                       None),
    (22.4, 25.6, "TEESRA — NAHI.",                 "NAHI"),
    (25.6, 28.8, "PURANI LADAAI.",                 None),
    (28.8, 32.0, "SAU PLATE.",                     None),
    (32.0, 35.2, "KAUN AAYAA THA?",                "KAUN"),
    (35.2, 38.4, "UNGLI GINTI PAR.",               None),
    (38.4, 41.6, "LOG NAHI.",                      "NAHI"),
    (41.6, 44.8, "JINKE NAAM TUM NAHI LE SAKTE,",  "NAAM"),
    (44.8, 48.0, "UNKE NAAM PE APNI ZINDAGI NAHI.","ZINDAGI"),
]

CUTS = [s[0] for s in SHOTS[1:]]

# ---------------------------------------------------------------- assets
_pc = OrderedDict()
def plate(name):
    if name in _pc:
        _pc.move_to_end(name); return _pc[name]
    if name == "MASK":
        im = Image.open(MASK).convert("RGB")
    else:
        import glob
        f = glob.glob(P + name + "_*.png")[0]
        im = Image.open(f).convert("RGB")
    im = im.resize((768, int(768 * im.size[1] / im.size[0])), Image.LANCZOS)
    _pc[name] = im
    if len(_pc) > 4: _pc.popitem(last=False)
    return im

def fit(im):
    """cover-crop to 1080x1920 exactly"""
    pw, ph = im.size
    s = max(W / pw, H / ph)
    im2 = im.resize((int(pw * s + 0.5), int(ph * s + 0.5)), Image.LANCZOS)
    x = (im2.size[0] - W) // 2; y = (im2.size[1] - H) // 2
    return im2.crop((x, y, x + W, y + H))

def depth_of(im):
    g = im.convert("L").filter(ImageFilter.GaussianBlur(7))
    a = np.asarray(g, np.float32) / 255.0
    lo, hi = np.percentile(a, 4), np.percentile(a, 96)
    a = np.clip((a - lo) / (hi - lo + 1e-6), 0, 1) ** 0.9
    a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)), np.float32) / 255
    return a

def make_slices(im):
    dep = depth_of(im)
    out = []
    for i in range(NS):
        d0, d1 = i / NS, (i + 1) / NS
        lo, hi = d0 - FEATHER, d1 + FEATHER
        a = np.clip((dep - lo) / (2 * FEATHER), 0, 1) * np.clip((hi - dep) / (2 * FEATHER), 0, 1)
        dm = (d0 + d1) / 2
        # bake atmospheric perspective: far = darker, hazier, softer
        far = 1 - dm
        rgb = Image.blend(im, Image.new("RGB", im.size, FOG), 0.30 * far)
        rgb = ImageEnhance.Brightness(rgb).enhance(1.06 - 0.18 * far)
        if far > 0.62: rgb = rgb.filter(ImageFilter.GaussianBlur(2.6))
        elif far > 0.38: rgb = rgb.filter(ImageFilter.GaussianBlur(1.3))
        lay = rgb.convert("RGBA")
        lay.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
        out.append((lay, dm))
    return out

_sc = OrderedDict()
HW_, HH_ = W // 2, H // 2
MG = 1.18

def plates(name):
    """half-res source array + smoothed depth, both with margin for the warp"""
    if name in _sc:
        _sc.move_to_end(name); return _sc[name]
    base = fit(plate(name))
    dep = depth_of(base)
    WS, HS = int(HW_ * MG), int(HH_ * MG)
    src = np.asarray(base.resize((WS, HS), Image.BICUBIC), np.float32)
    di = Image.fromarray((dep * 255).astype(np.uint8)).resize((HW_, HH_), Image.BILINEAR)
    di = di.filter(ImageFilter.GaussianBlur(max(6, HW_ // 38)))  # smooth: a luma-depth must not bend rigid props
    dsrc = np.asarray(di, np.float32) / 255.0
    _sc[name] = (src, dsrc)
    if len(_sc) > 4: _sc.popitem(last=False)
    return _sc[name]

YY, XX = np.mgrid[0:HH_, 0:HW_]
YY = YY.astype(np.float32); XX = XX.astype(np.float32)

def warp(src, dep, k, px, py, focus):
    """continuous 2.5D warp: src coordinate = centre + (p-centre)/z(p) + shift(p)"""
    zn = 1.0 + k * (dep - focus) * 0.85
    ox = px * (dep - focus) * 1.8
    oy = py * (dep - focus) * 1.8
    gx = px * 260.0 / MG      # whole-camera pan (no bending)
    gy = py * 260.0 / MG
    xs = src.shape[1] / 2.0 + (XX - HW_ / 2.0) / zn + ox + gx
    ys = src.shape[0] / 2.0 + (YY - HH_ / 2.0) / zn + oy + gy
    x0 = np.clip(xs.astype(np.int32), 0, src.shape[1] - 2)
    y0 = np.clip(ys.astype(np.int32), 0, src.shape[0] - 2)
    fx = (xs - x0)[..., None]; fy = (ys - y0)[..., None]
    c00 = src[y0, x0]; c10 = src[y0, x0 + 1]
    c01 = src[y0 + 1, x0]; c11 = src[y0 + 1, x0 + 1]
    top = c00 + (c10 - c00) * fx
    bot = c01 + (c11 - c01) * fx
    out = top + (bot - top) * fy
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)

# ---------------------------------------------------------------- light (D5)
def radial(size, power=2.0):
    n = size
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.sqrt((x - n / 2) ** 2 + (y - n / 2) ** 2) / (n / 2)
    v = np.clip(1 - r, 0, 1) ** power
    return v

RAD = Image.fromarray((radial(320, 2.2) * 255).astype(np.uint8))
def light_blob(pos, scale, col, amt):
    s = max(2, int(320 * scale))
    b = RAD.resize((s // 2, s // 2), Image.BILINEAR)
    lay = Image.new("RGB", (W // 2, H // 2), col)
    m = Image.new("L", (W // 2, H // 2), 0)
    m.paste(b, (int(pos[0] / 2 - s / 4), int(pos[1] / 2 - s / 4)))
    lay = lay.resize((W, H), Image.BILINEAR)
    m = m.resize((W, H), Image.BILINEAR)
    lay.putalpha(m.point(lambda v: int(v * amt)))
    return lay

def godray(t, phase, n=3):
    """soft diagonal streaks"""
    lay = Image.new("RGBA", (W // 3, H // 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for k in range(n):
        x = ((t * 46 + k * 300 + phase * 90) % (W + 900)) - 450
        w = 120 + 40 * k
        d.polygon([(x, -40), (x + w, -40), (x + w * 2.4, H // 3 + 40), (x + w * 1.4, H // 3 + 40)],
                  fill=(255, 226, 190, 16 + 8 * k))
    return lay.filter(ImageFilter.GaussianBlur(8)).resize((W, H), Image.BILINEAR)

# ---------------------------------------------------------------- D2 surface-off
def blueprint(im):
    """plate -> wireframe / contour / grid"""
    g = np.asarray(im.convert("L").filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    gx = np.abs(np.diff(g, axis=1, prepend=g[:, :1]))
    gy = np.abs(np.diff(g, axis=0, prepend=g[:1, :]))
    e = np.clip((gx + gy) * 6.0, 0, 1)
    dep = depth_of(im)
    contours = np.zeros_like(dep)
    for lv in (0.25, 0.4, 0.55, 0.7, 0.85):
        contours = np.maximum(contours, np.clip(1 - np.abs(dep - lv) / 0.006, 0, 1))
    base = np.zeros((H, W, 3), np.float32)
    base[:] = (10, 16, 24)
    canvas = Image.fromarray(base.astype(np.uint8))
    d = ImageDraw.Draw(canvas)
    for x in range(0, W, 60): d.line([(x, 0), (x, H)], fill=(16, 26, 38), width=1)
    for y in range(0, H, 60): d.line([(0, y), (W, y)], fill=(16, 26, 38), width=1)
    a = np.asarray(canvas, np.float32)
    a += e[:, :, None] * np.array(CYAN, np.float32) * 1.15
    a += contours[:, :, None] * np.array((60, 150, 190), np.float32) * 0.9
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

BLP = {}
def blp(name):
    if name not in BLP:
        BLP[name] = blueprint(fit(plate(name)))
    return BLP[name]

def dust_layer(t, amt):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(int(t * 30) % 977)
    for _ in range(int(160 * amt)):
        x = rng.integers(0, W); y = rng.integers(0, H)
        r = rng.integers(1, 4)
        v = rng.integers(90, 220)
        d.ellipse([x, y, x + r, y + r], fill=(v, v - 20, v - 50, rng.integers(40, 150)))
    return lay.filter(ImageFilter.GaussianBlur(1.1))

# ---------------------------------------------------------------- D1 x-ray
def ribcage():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx = W * 0.50
    # cranium
    d.arc([cx - 222, H * 0.175, cx + 222, H * 0.575], 152, 388, fill=CYAN + (200,), width=8)
    d.arc([cx - 208, H * 0.195, cx + 208, H * 0.560], 152, 388, fill=CYAN + (90,), width=4)
    # brow ridge
    d.arc([cx - 190, H * 0.30, cx + 190, H * 0.40], 190, 350, fill=CYAN + (170,), width=6)
    # eye sockets
    for sx in (-1, 1):
        d.ellipse([cx + sx * 118 - 78, H * 0.335, cx + sx * 118 + 78, H * 0.415],
                  outline=CYAN + (215,), width=7)
        d.ellipse([cx + sx * 118 - 60, H * 0.345, cx + sx * 118 + 60, H * 0.405],
                  outline=CYAN + (80,), width=3)
    # nasal cavity
    d.polygon([(cx - 34, H * 0.435), (cx + 34, H * 0.435), (cx, H * 0.505)],
              outline=CYAN + (190,), width=6)
    # cheek + maxilla
    d.arc([cx - 200, H * 0.40, cx + 200, H * 0.56], 200, 340, fill=CYAN + (110,), width=5)
    # teeth
    for k in range(9):
        x = cx - 108 + k * 27
        d.line([(x, H * 0.535), (x, H * 0.575)], fill=CYAN + (150,), width=4)
    d.line([(cx - 120, H * 0.535), (cx + 120, H * 0.535)], fill=CYAN + (170,), width=4)
    # mandible
    d.arc([cx - 196, H * 0.47, cx + 196, H * 0.70], 20, 160, fill=CYAN + (185,), width=8)
    d.line([(cx, H * 0.13), (cx, H * 0.545)], fill=CYAN + (55,), width=3)
    lay = lay.filter(ImageFilter.GaussianBlur(1.3))
    glow = lay.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.85))
    lay = Image.alpha_composite(lay, glow)
    return lay

RIBS = ribcage()  # skull, aligned to the mask

def xray_comp(img, u):
    """u 0..1 : plate -> flesh-to-bone"""
    k = max(1e-3, u)
    dark = ImageEnhance.Brightness(img).enhance(1 - 0.24 * k)
    cool = ImageChops.screen(dark, Image.merge("RGB", [Image.new("L", (W, H), 0)] * 2 +
                                              [Image.new("L", (W, H), int(40 * k))]))
    gl = RIBS.copy()
    a = gl.getchannel("A").point(lambda v: int(v * k))
    gl.putalpha(a)
    out = Image.new("RGB", (W, H)); out.paste(cool, (0, 0)); out.paste(gl, (0, 0), gl)
    # heart: scene key light
    hx, hy = W * 0.50, H * 0.775
    beat = 1 + 0.16 * math.sin(u * 22)
    heart = light_blob((hx, hy), 1.30 * beat, (255, 44, 30), 0.50 * k)
    out = Image.alpha_composite(out.convert("RGBA"), heart).convert("RGB")
    # heart re-lights the jaw (D5)
    re = light_blob((hx, hy - 330), 2.0, (255, 66, 44), 0.22 * k)
    out = Image.alpha_composite(out.convert("RGBA"), re).convert("RGB")
    return out

# ---------------------------------------------------------------- D3 word matter
F_HOOK = ImageFont.truetype(F_MONO, 92)
F_CARD = ImageFont.truetype(F_MONO, 74)

_cards = {}
def card_layer(text, hot, size=74, col=CREAM):
    f = ImageFont.truetype(F_MONO, size)
    ls = 5
    words = text.split()
    lines, cur, cw = [], [], 0.0
    maxw = W - 150
    for w_ in words:
        ww = sum(f.getlength(c) for c in w_) + ls * (len(w_) - 1)
        sp = f.getlength(" ") + ls
        if cur and cw + sp + ww > maxw:
            lines.append(cur); cur, cw = [], 0.0
        cur.append((w_, ww)); cw += (sp if cur[:-1] else 0) + ww
    if cur: lines.append(cur)
    lh = int((f.getmetrics()[0] + f.getmetrics()[1]) * 1.30)
    im = Image.new("RGBA", (W, lh * len(lines) + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for li, idxs in enumerate(lines):
        sp = f.getlength(" ") + ls
        total = sum(w for _, w in idxs) + sp * (len(idxs) - 1)
        x = (W - total) / 2; y = li * lh
        for word, ww in idxs:
            c = RED if (hot and hot in word) else col
            for ch in word:
                d.text((x, y), ch, font=f, fill=c + (255,))
                x += f.getlength(ch) + ls
            x += sp
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").point(lambda v: int(v * 0.9)))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    out = Image.new("RGBA", (im.width, im.height + 8), (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 6)); out.alpha_composite(im, (0, 0))
    return out

def shards(text, hot):
    """split the card into physical pieces"""
    lay = card_layer(text, hot, 84)
    bbox = lay.getbbox()
    if not bbox: return []
    lay = lay.crop(bbox)
    w, h = lay.size
    gx, gy = 10, 5
    out = []
    rng = np.random.default_rng(7)
    for j in range(gy):
        for i in range(gx):
            x0, y0 = int(i * w / gx), int(j * h / gy)
            x1, y1 = int((i + 1) * w / gx), int((j + 1) * h / gy)
            pc = lay.crop((x0, y0, x1, y1))
            if not pc.getbbox(): continue
            out.append(dict(img=pc, x=bbox[0] + x0, y=bbox[1] + y0,
                            vx=rng.uniform(-9, 9), vy=rng.uniform(-13, -3),
                            rot=rng.uniform(-70, 70), dl=rng.uniform(0, 3.5)))
    return out

CARDS_C = {}
for (c0, c1, txt, hot) in CARDS:
    CARDS_C[(c0, c1)] = (card_layer(txt, hot), shards(txt, hot) if hot else None)

CARD_Y = 1178

# ---------------------------------------------------------------- post
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 1.32
VIG = Image.fromarray((np.clip(1 - 0.58 * np.clip(r, 0, 1.6) ** 2.0, 0.12, 1) * 255).astype(np.uint8)).convert("RGB")

sc = np.zeros((H, W), np.uint8)
sc[:] = (np.clip((np.arange(H) - 1000) / (H - 1000), 0, 1) ** 1.6 * 120)[:, None].astype(np.uint8)
SCRIM = Image.merge("RGBA", [Image.new("L", (W, H), 0)] * 3 + [Image.fromarray(sc)])

GR = []
for k in range(14):
    g = np.random.default_rng(300 + k).normal(128, 8.6, (H // 2, W // 2)).clip(0, 255).astype(np.uint8)
    GR.append(Image.fromarray(g).resize((W, H), Image.BILINEAR).convert("RGB"))

def whip(img, k):
    """directional motion blur for hidden cuts (D4)"""
    out = img.copy()
    for j in range(1, 5):
        dx = int(k * j * 7)
        sh = ImageChops.offset(img, dx, 0)
        out = Image.blend(out, sh, 0.16)
    return out

def shot_at(t):
    for s in SHOTS:
        if s[0] <= t < s[1]: return s
    return SHOTS[-1]

# ---------------------------------------------------------------- frame
def frame(i):
    t = i / FPS
    t0, t1, name, dolly, px, py, focus, light, dev = shot_at(t)
    u = min(max((t - t0) / (t1 - t0), 0), 1)
    e = u * u * (3 - 2 * u)

    # --- D4: hidden cuts, whip at every cut
    dist = min(abs(t - c) for c in CUTS) if CUTS else 9
    wk = max(0.0, 1 - dist / 0.13)

    src, dep = plates(name)
    img = warp(src, dep, dolly * e, px * e * 0.5, py * e * 0.5, focus)

    # --- D2 surface-off
    if dev == "soff":
        k = min(1.0, max(0.0, (u - 0.45) / 0.40))
        if k > 0:
            b = blp(name)
            img = Image.blend(img, b, k * k)
            if k > 0.75:
                img = Image.alpha_composite(img.convert("RGBA"),
                                            dust_layer(t, (k - 0.75) * 4)).convert("RGB")

    # --- D1 x-ray
    if dev in ("xray", "xray2"):
        if dev == "xray":
            k = min(1.0, max(0.0, (u - 0.25) / 0.45))
        else:
            k = 1.0 - min(1.0, max(0.0, (u - 0.15) / 0.7))
        img = xray_comp(img, k)

    # --- D5 light-handshake
    fl = 1.0 + 0.014 * math.sin(2 * math.pi * 1.1 * t)
    img = ImageEnhance.Brightness(img).enhance(fl)
    if light:
        ph = (u + (0.3 if "2" in light else 0)) % 1.0
        if light.startswith("sweep"):
            x = (-260 + ph * (W + 520)) if light.endswith("L") else (W + 260 - ph * (W + 520))
            blob = light_blob((x, H * 0.42), 2.6, (255, 208, 150), 0.26)
        elif light == "top":
            blob = light_blob((W * (0.35 + 0.3 * ph), -80), 3.0, (255, 220, 170), 0.30)
        elif light.startswith("godray"):
            blob = light_blob((W * (0.2 + 0.6 * ph), H * 0.16), 2.4, (255, 232, 196), 0.22)
            img = Image.alpha_composite(img.convert("RGBA"), godray(t, ph)).convert("RGB")
        elif light == "coldmoon":
            blob = light_blob((W * (0.15 + 0.5 * ph), H * 0.3), 2.8, (120, 170, 230), 0.16)
        elif light == "day":
            blob = light_blob((W * 0.5, H * (0.1 + 0.2 * ph)), 3.4, (235, 240, 255), 0.22)
        elif light == "red":
            blob = light_blob((W * 0.5, H * 0.44), 2.2, (255, 40, 30), 0.13 + 0.05 * math.sin(t * 3.4))
        else:
            blob = light_blob((W * (0.15 + 0.7 * ph), H * 0.45), 2.6, (255, 210, 160), 0.22)
        img = Image.alpha_composite(img.convert("RGBA"), blob).convert("RGB")

    # --- typography
    for (c0, c1, txt, hot) in CARDS:
        if c0 <= t < c1:
            lay, sh = CARDS_C[(c0, c1)]
            a = min(1.0, (t - c0) / (3.5 / FPS))
            end = c1 - t
            img = img.convert("RGBA"); img.alpha_composite(SCRIM)
            if sh and end < 0.30:
                # D3 word-matter: the word breaks into pieces
                kk = (0.30 - end) / 0.30
                for s in sh:
                    dx = s["vx"] * kk * 42; dy = s["vy"] * kk * 42 + 260 * kk * kk
                    ang = s["rot"] * kk
                    p = s["img"].rotate(ang, expand=True, resample=Image.BICUBIC)
                    al = max(0.0, 1 - kk * 1.15)
                    p.putalpha(p.getchannel("A").point(lambda v: int(v * al * a)))
                    img.alpha_composite(p, (int(s["x"] + dx), int(CARD_Y + s["y"] + dy)))
            else:
                tmp = lay
                if a < 1:
                    tmp = lay.copy(); tmp.putalpha(tmp.getchannel("A").point(lambda v: int(v * a)))
                rise = int((1 - a) * 14)
                img.alpha_composite(tmp, (0, CARD_Y + rise))
            img = img.convert("RGB")
            break

    # --- grade / post
    if wk > 0.02:
        img = whip(img, wk)
    # halation: blur the bright bits back over the frame
    small = img.resize((W // 6, H // 6), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    small = ImageEnhance.Brightness(small).enhance(1.35).resize((W, H), Image.BILINEAR)
    img = Image.blend(img, ImageChops.screen(img, small), 0.10)
    img = ImageChops.multiply(img, VIG)
    img = ImageEnhance.Contrast(img).enhance(1.10)
    img = ImageEnhance.Color(img).enhance(0.94)
    g = GR[i % len(GR)]
    img = ImageChops.add(img, ImageChops.offset(g, (i * 37) % W, (i * 91) % H), 1.0, -128)

    # --- D6 anamorphic flare (3 shots only)
    if name == "MASK" and 41.6 <= t < 43.2:
        fl_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(fl_img)
        y = int(H * 0.42)
        for k2, al in ((0, 90), (1, 50), (2, 26)):
            d.rectangle([0, y - 2 - k2, W, y + 2 + k2], fill=(255, 70, 50, al))
        fl_img = fl_img.filter(ImageFilter.GaussianBlur(6))
        img = Image.alpha_composite(img.convert("RGBA"), fl_img).convert("RGB")

    return img

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "so.mp4"
    a, b = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (0.0, 48.0)
    only = sys.argv[4] if len(sys.argv) > 4 else None
    if only == "stills":
        for tt in [a, b]:
            frame(int(tt * FPS)).save(f"/tmp/so_{tt:.1f}.png")
        print("stills"); sys.exit()
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", "audio/naam.wav"]
    if a > 0:
        cmd += ["-ss", str(a), "-t", str(b - a), "-i", "audio/naam.wav"]
    cmd += ["-map", "0:v", "-map", "1:a", "-ss", str(a), "-t", str(b - a),
            "-c:v", "libx264", "-preset", "medium", "-crf", "25", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    n0, n1 = int(a * FPS), int(b * FPS)
    for i in range(n0, n1):
        p.stdin.write(frame(i).tobytes())
        if (i - n0) % 120 == 0: print(f"  {i}/{n1}", flush=True)
    p.stdin.close(); p.wait()
    print("done", out, p.returncode)
