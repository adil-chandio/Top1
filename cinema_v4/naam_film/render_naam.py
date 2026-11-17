"""NAAM LO — the film. 1080x1920, 30 fps, 55.0 s.
Plates -> camera move -> grade -> vignette -> grain -> code-alpha type -> x264.
Frames go straight into ffmpeg over a pipe; nothing is written to disk.
"""
import numpy as np, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance
import imageio_ffmpeg

W, H, FPS = 1080, 1920, 30
DUR = 55.0
NF = int(round(DUR * FPS))
P = "plates/"
MASK = "../reference/CHARACTER_MASKED_PORTRAIT.png"

F_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
F_MONOB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
F_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
F_SERIFB = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

CREAM = (243, 236, 226)
RED = (214, 48, 38)
DIM = (196, 188, 176)

# ----------------------------------------------------------------- timeline
# (t0, t1, plate, z0, z1, cx, cy, text, style, highlight, grade)
S = [
    (0.00, 2.20, "p01_cards.png",      1.00, 1.06, .50, .50, "TEEN SAU CARD.",                          "HOOK",  "",                        dict(bri=1.0)),
    (2.20, 5.90, "p02_doorway.png",    1.00, 1.09, .50, .54, "Beta ko paanch naam chahiye the, un logon ke jo sach me apne hain.", "LINE", "paanch naam", dict(bri=.97)),
    (5.90, 9.20, "p03_ledger.png",     1.00, 1.08, .46, .50, "Abbu ke paas teen sau card the, aur naam ek bhi nahi tha.", "LINE", "ek bhi nahi", dict(bri=.98)),
    (9.20, 10.30, "p03_ledger.png",   1.14, 1.18, .44, .46, "Beta ne poocha.",                        "LINE", "",                        dict(bri=.96)),
    (10.30, 11.20, "p03_ledger.png",  1.18, 1.23, .44, .46, "Kis ka naam likhun?",                     "LINE", "Kis ka naam",             dict(bri=.96)),
    (11.20, 14.20, "p04_mouth.png",    1.02, 1.10, .50, .50, "Abbu ne kaha ke log hain, aur logon ke naam nahi hote.", "LINE", "naam nahi hote", dict(bri=1.0)),
    (14.20, 18.90, "p05_pencil_air.png", 1.00, 1.12, .50, .52, "Abbu hanse, phir pencil uthai, aur woh teen sau card ke upar hawa me ruk gayi.", "LINE", "hawa me ruk gayi", dict(bri=1.02)),
    (18.90, 19.80, "p06_pencil_tip.png", 1.04, 1.14, .50, .50, "Ek naam.",                             "BIG",  "",                        dict(bri=1.0)),
    (19.80, 25.90, "p06_pencil_tip.png", 1.02, 1.14, .50, .52, "Do naam kaaghaz pe aaye, teesra aaya hi nahi, kyunki teesre naam ke saath ek purani ladaai yaad aa gayi, aur pencil neeche rakh di gayi.", "LINE", "teesra aaya hi nahi", dict(bri=.86)),
    (25.90, 31.00, "p08_night.png",     1.00, 1.07, .50, .50, "Raat bhar beta chup baitha, aur subah Abbu ne kaha ke sau log aayenge, aur sau plate lagengi.", "LINE", "sau plate", dict(bri=1.0)),
    (31.00, 35.10, "p09_plates.png",    1.00, 1.10, .50, .50, "Beta ne poocha ke jab tum bimaar the, tab kaun aaya tha, kaun plate laya tha?", "LINE", "kaun aaya tha", dict(bri=1.0)),
    (35.10, 39.10, "p10_finger_count.png", 1.00, 1.14, .50, .46, "Abbu ne jawab nahi diya, lekin unki ungli card ki ginti par wapas chali gayi.", "LINE", "jawab nahi diya", dict(bri=1.0)),
    (39.10, 41.00, "p03_ledger.png",   1.26, 1.34, .42, .40, "Phir aakhri lifafa uthaya.",             "LINE", "",                        dict(bri=.80)),
    (41.00, 42.50, "p06_pencil_tip.png", 1.46, 1.62, .46, .40, "Us pe likha tha, log nahi.",            "BIG",  "log nahi",                dict(bri=.60)),
    (42.50, 43.30, None,                1.00, 1.00, .50, .50, "",                                        "",     "",                        dict(bri=0)),
    (43.30, 47.10, "p01_cards.png",     1.62, 1.46, .50, .68, "Woh lifafa baaki lifafon ke neeche chala gaya, us almari me, jahan koi kabhi nahi dekhta.", "LINE", "koi kabhi nahi dekhta", dict(bri=.40)),
    (47.10, 50.60, "p01_cards.png",     1.04, 1.12, .50, .50, "Teen sau card, sau plate, aur ek aadmi ke paas paanch naam nahi.", "DATA", "paanch naam nahi", dict(bri=.90)),
    (50.60, 55.00, "MASK",              1.02, 1.14, .50, .46, "Jinke naam tum nahi le sakte, unke naam pe apni zindagi nahi de sakte.", "LINE", "apni zindagi", dict(bri=1.0)),
]

STYLE = {
    "HOOK": dict(font=F_MONO,  size=88, ls=9,  y=1330, col=CREAM, lh=1.26),
    "LINE": dict(font=F_SERIF, size=51, ls=0.8, y=1318, col=CREAM, lh=1.38),
    "BIG":  dict(font=F_SERIFB, size=66, ls=2.0, y=1300, col=CREAM, lh=1.32),
    "DATA": dict(font=F_MONO,  size=56, ls=3.5, y=1280, col=CREAM, lh=1.36),
}

# ----------------------------------------------------------------- helpers
def plate(name):
    if name == "MASK":
        return Image.open(MASK).convert("RGB")
    return Image.open(P + name).convert("RGB")

_cache = {}
def get(name):
    if name not in _cache:
        _cache[name] = plate(name)
    return _cache[name]

def cover(img, z, cx, cy):
    pw, ph = img.size
    vh0 = min(ph, pw / (W / H)); vw0 = vh0 * (W / H)
    vw, vh = min(vw0 / z, pw), min(vh0 / z, ph)
    x0 = cx * pw - vw / 2; y0 = cy * ph - vh / 2
    x0 = min(max(x0, 0.0), pw - vw); y0 = min(max(y0, 0.0), ph - vh)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + vw, y0 + vh))

def ease(u):  # smoothstep
    return u * u * (3 - 2 * u)

# vignette
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 1.32
vig = np.clip(1.0 - 0.62 * np.clip(r, 0, 1.6) ** 2.1, 0.10, 1.0)
VIG = Image.fromarray((vig * 255).astype(np.uint8)).convert("RGB")

# scrim under type
sc = np.zeros((H, W), np.uint8)
grad = np.clip((np.arange(H) - 980) / (H - 980), 0, 1) ** 1.55 * 178
sc[:] = grad[:, None].astype(np.uint8)
SCRIM = Image.merge("RGBA", [Image.new("L", (W, H), 0)] * 3 + [Image.fromarray(sc)])

# grain bank
GR = []
for k in range(16):
    g = np.random.default_rng(700 + k).normal(128, 9.4, (H // 2, W // 2)).clip(0, 255).astype(np.uint8)
    GR.append(Image.fromarray(g).resize((W, H), Image.BILINEAR).convert("RGB"))

def text_layer(text, style, hi):
    st = STYLE[style]
    f = ImageFont.truetype(st["font"], st["size"])
    ls, lh = st["ls"], st["lh"]
    asc, desc = f.getmetrics()
    lh_px = int((asc + desc) * lh)
    margin = 74
    maxw = W - 2 * margin
    words = text.split()
    lo = text.lower()
    hits = set()
    if hi:
        p = lo.find(hi.lower())
        if p >= 0:
            q = p + len(hi)
            pos = 0
            for i, wd in enumerate(words):
                ws = lo.find(wd, pos); pos = ws + len(wd)
                if ws < q and pos > p: hits.add(i)
    def wd_width(wd):
        return (sum(f.getlength(c) for c in wd) + ls * (len(wd) - 1)) if wd else 0
    space = f.getlength(" ") + ls
    lines, cur, cw = [], [], 0.0
    for i, wd in enumerate(words):
        ww = wd_width(wd)
        if cur and cw + space + ww > maxw:
            lines.append(cur); cur, cw = [], 0.0
        cur.append(i); cw += (space if cur[:-1] else 0) + ww
    if cur: lines.append(cur)
    img = Image.new("RGBA", (W, lh_px * len(lines) + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for li, idxs in enumerate(lines):
        total = sum(wd_width(words[i]) for i in idxs) + space * (len(idxs) - 1)
        x = (W - total) / 2
        yb = li * lh_px
        for i in idxs:
            col = RED if i in hits else st["col"]
            for c in words[i]:
                d.text((x, yb), c, font=f, fill=col + (255,))
                x += f.getlength(c) + ls
            x += space
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.putalpha(img.getchannel("A").point(lambda v: int(v * 0.82)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    out = Image.new("RGBA", (img.width, img.height + 6), (0, 0, 0, 0))
    out.alpha_composite(shadow, (0, 5))
    out.alpha_composite(img, (0, 0))
    return out

LAYER = {}
for sh in S:
    if sh[7]:
        LAYER[id(sh)] = (text_layer(sh[7], sh[8], sh[9]), STYLE[sh[8]]["y"])

BRAND = Image.open  # placeholder to keep linters calm

def shot_at(t):
    for sh in S:
        if sh[0] <= t < sh[1]:
            return sh
    return S[-1]

# ----------------------------------------------------------------- render
def frame(i):
    t = i / FPS
    sh = shot_at(t)
    t0, t1, name, z0, z1, cx, cy, text, style, hi, gr = sh
    u = min(max((t - t0) / max(1e-6, t1 - t0), 0), 1)
    z = z0 + (z1 - z0) * ease(u)
    z += 0.006 * math.sin(2 * math.pi * 0.31 * t + hash(name) % 7)
    dx = 0.008 * math.sin(2 * math.pi * 0.21 * t + 1.3)
    dy = 0.006 * math.sin(2 * math.pi * 0.17 * t + 2.7)

    if name is None:
        img = Image.new("RGB", (W, H), (3, 3, 3))
    else:
        img = cover(get(name), z, cx + dx, cy + dy)
        b = gr.get("bri", 1.0)
        img = ImageEnhance.Brightness(img).enhance(b)
        img = ImageEnhance.Contrast(img).enhance(gr.get("con", 1.06))
        img = ImageEnhance.Color(img).enhance(gr.get("sat", 0.96))
        img = ImageChops.multiply(img, VIG)

    # light flicker
    fl = 1.0 + 0.016 * math.sin(2 * math.pi * 0.9 * t + 0.7) + 0.010 * math.sin(2 * math.pi * 7.3 * t)
    img = ImageEnhance.Brightness(img).enhance(fl)

    # mask pulse
    if name == "MASK":
        p = 0.5 + 0.5 * math.sin(2 * math.pi * 0.55 * t)
        redl = Image.new("RGB", (W, H), (255, 26, 18))
        img = Image.blend(img, ImageChops.screen(img, redl), 0.045 + 0.05 * p)

    if text:
        lay, ypos = LAYER[id(sh)]
        a = min(1.0, (t - t0) / (4.0 / FPS))
        rise = int((1 - a) * 8)
        img = img.convert("RGBA")
        img.alpha_composite(SCRIM)
        if a < 1:
            tmp = lay.copy(); tmp.putalpha(tmp.getchannel("A").point(lambda v: int(v * a)))
        else:
            tmp = lay
        img.alpha_composite(tmp, (0, ypos + rise))
        img = img.convert("RGB")

    # grain
    if name is not None:
        g = GR[i % len(GR)]
        goff = ImageChops.offset(g, (i * 37) % W, (i * 91) % H)
        if name == "MASK":
            img = img.filter(ImageFilter.GaussianBlur(0.6))
            g = GR[(i + 5) % len(GR)]
            goff = ImageChops.offset(g, (i * 53) % W, (i * 71) % H)
            goff = ImageChops.blend(Image.new("RGB", (W, H), (128, 128, 128)), goff, 0.72)
        img = ImageChops.add(img, goff, scale=1.0, offset=-128)

    # brand
    if name == "MASK" and t > 53.15:
        bl = BRAND_LAYER
        a = min(1.0, (t - 53.15) / 0.35)
        tmp = bl.copy()
        tmp.putalpha(tmp.getchannel("A").point(lambda v: int(v * a)))
        img = img.convert("RGBA"); img.alpha_composite(tmp, (0, 1770)); img = img.convert("RGB")
    return img

def brand():
    f = ImageFont.truetype(F_MONO, 30)
    txt = "T A B A H I"
    tw = f.getlength(txt)
    im = Image.new("RGBA", (W, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text(((W - tw) / 2, 8), txt, font=f, fill=DIM + (215,))
    lw = 44
    d.line([(W / 2 - tw / 2 - 26, 24), (W / 2 - tw / 2 - 26 + lw, 24)], fill=(150, 40, 34, 200), width=2)
    d.line([(W / 2 + tw / 2 + 26 - lw, 24), (W / 2 + tw / 2 + 26, 24)], fill=(150, 40, 34, 200), width=2)
    return im

BRAND_LAYER = brand()

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "naam_lo.mp4"
    only = [int(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else None
    if only:
        for i in only:
            frame(i).save(f"/tmp/test_{i:05d}.png")
        print("test frames written"); sys.exit()
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", "audio/naam.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "26", "-maxrate", "8M", "-bufsize", "16M",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(NF):
        p.stdin.write(frame(i).tobytes())
        if i % 150 == 0:
            print(f"  {i}/{NF}  t={i/FPS:.1f}s", flush=True)
    p.stdin.close(); p.wait()
    print("done", out, "exit", p.returncode)
