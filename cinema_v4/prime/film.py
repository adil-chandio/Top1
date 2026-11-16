"""NAAM // PRIME — motion + comp engine (numpy, no GPU, no ffmpeg-filters).

Every shot is a genuine camera move, not a pan/zoom of a flat picture:
  * AI plates get a luminance-derived depth field and are re-projected per frame
    (dolly / pan / roll) with depth-correct parallax and edge-stretch hole fill.
  * Cycles shots use a REAL Z buffer (View-Z pass) for exact parallax.
  * 3D dust field with true perspective is layered in front of every shot.
  * Light sweep, DOF ramp, bloom, halation, grain, CA, vignette, type.

    /tmp/venv/bin/python film.py [--preview N] [--out path]
"""
import numpy as np, os, sys, subprocess, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 24
ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "..", "assets")
BUILD = os.path.join(ROOT, "build")
OUT = os.path.abspath(os.path.join(ROOT, "..", "..", "deliverables",
                                   "MONARCH_NAAM_PRIME_1080x1920.mp4"))
CREAM = (243, 236, 226)
RED = (214, 48, 38)
GOLD = (214, 168, 92)
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
MONOB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

rng = np.random.default_rng(11)


# ------------------------------------------------------------------ helpers
def ease(t):
    return t * t * (3 - 2 * t)


def ease_out(t):
    return 1 - (1 - t) ** 2.2


def load_rgb(path, w=W, h=H):
    im = Image.open(path).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, int(im.width * s + .5)), max(h, int(im.height * s + .5))),
                   Image.LANCZOS)
    x = (im.width - w) // 2
    y = (im.height - h) // 2
    im = im.crop((x, y, x + w, y + h))
    return np.asarray(im, np.float32) / 255.0


def load_depth(path, w=W, h=H, blur=9):
    im = Image.open(path).convert("L")
    im = im.resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur))
    d = 1.0 - np.asarray(im, np.float32) / 255.0     # 0 = far, 1 = near
    return d


def plate_depth(rgb, blur=26):
    """Pseudo-depth from luminance for black-background plates (subject = near)."""
    l = rgb.max(2)
    l = l / max(1e-6, np.percentile(l, 99.5))
    l = np.clip(l, 0, 1) ** 0.65
    im = Image.fromarray((l * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    d = np.asarray(im, np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.5) / (H * 0.62)) ** 2)
    near = np.clip(d * 0.65 + np.clip(1.0 - r, 0, 1) * 0.35, 0, 1)   # 1 = near subject
    d = 1.55 - 1.05 * near                                            # near=.50 far=1.55
    im = Image.fromarray(np.clip(d / 2.0 * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(14)), np.float32) / 255.0 * 2.0


def bilinear(img, xs, ys):
    xs = np.clip(xs, 0, img.shape[1] - 1.001)
    ys = np.clip(ys, 0, img.shape[0] - 1.001)
    x0 = xs.astype(np.int32); y0 = ys.astype(np.int32)
    fx = (xs - x0)[..., None]; fy = (ys - y0)[..., None]
    x1 = x0 + 1; y1 = y0 + 1
    a = img[y0, x0]; b = img[y0, x1]; c = img[y1, x0]
    d = img[y1, x1]
    return (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) +
            c * (1 - fx) * fy + d * fx * fy)


YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
CX, CY = W / 2.0, H * 0.5


def reproject(rgb, depth, c):
    """Camera move: c = dict(dolly, px, py, zoom, roll). dolly>0 = move closer."""
    d = np.clip(depth, 0.35, 3.0)
    p = 1.0 / d                                  # parallax weight
    # translation of the camera (fraction of frame at subject plane)
    tx = c.get("px", 0.0) * W
    ty = c.get("py", 0.0) * H
    zoom = max(1.002, c.get("zoom", 1.0) * (1.0 + c.get("dolly", 0.0)))
    rot = np.radians(c.get("roll", 0.0))
    ca, sa = np.cos(rot), np.sin(rot)
    x = XX - CX - tx * p
    y = YY - CY - ty * p
    xr = x * ca - y * sa
    yr = x * sa + y * ca
    xs = CX + xr / zoom
    ys = CY + yr / zoom
    out = bilinear(rgb, xs, ys)
    return out


# -------------------------------------------------------------- dust in 3D
def make_dust(n=170, seed=3):
    r = np.random.default_rng(seed)
    return dict(
        x=r.uniform(-0.62, 0.62, n),
        y=r.uniform(-0.55, 0.55, n),
        z=r.uniform(0.35, 2.6, n),
        s=r.uniform(0.5, 1.9, n),
        b=r.uniform(0.25, 1.0, n),
        vx=r.uniform(-0.004, 0.004, n),
        vy=r.uniform(-0.006, -0.001, n),
        ph=r.uniform(0, 6.28, n),
    )


KER = {}
def kernel(r):
    r = int(max(1, min(11, round(r))))
    if r not in KER:
        r = max(1, r)
        g = np.mgrid[-r:r + 1, -r:r + 1].astype(np.float32)
        KER[r] = np.exp(-(g[0] ** 2 + g[1] ** 2) / (2 * (r * 0.55) ** 2))
    return KER[r]


def dust_layer(dust, c, t, gain=1.0, warm=(1.0, 0.90, 0.74)):
    layer = np.zeros((H, W, 3), np.float32)
    zoom = 1.0 + c.get("dolly", 0.0)
    for i in range(len(dust["x"])):
        z = dust["z"][i] - c.get("dolly", 0.0) * 0.35
        if z < 0.15:
            continue
        sx = CX + ((dust["x"][i] + dust["vx"][i] * t) - c.get("px", 0.0) * 1.6) * W * 0.55 / z
        sy = CY + ((dust["y"][i] + dust["vy"][i] * t) - c.get("py", 0.0) * 1.6) * H * 0.55 / z
        if not (-40 < sx < W + 40 and -40 < sy < H + 40):
            continue
        rad = min(3.6, dust["s"][i] * 1.35 / z * (1.0 + 0.5 * np.sin(dust["ph"][i] + t * 1.7)))
        k = kernel(rad)
        r = k.shape[0] // 2
        ix, iy = int(sx), int(sy)
        x0, x1 = max(0, ix - r), min(W, ix + r + 1)
        y0, y1 = max(0, iy - r), min(H, iy + r + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        kk = k[(y0 - iy + r):(y1 - iy + r), (x0 - ix + r):(x1 - ix + r)]
        amp = (0.16 / z ** 1.5) * dust["b"][i] * gain
        layer[y0:y1, x0:x1] += kk[..., None] * amp * np.array(warm, np.float32)
    return layer


# --------------------------------------------------------------- look / comp
def _pil(a):
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


def blur_fast(img, radius, down=2):
    """Gaussian blur at 1/down resolution, upsampled back (visually identical)."""
    im = _pil(img)
    h, w = im.height // down, im.width // down
    sm = im.resize((w, h), Image.BILINEAR).filter(
        ImageFilter.GaussianBlur(max(0.6, radius / down)))
    return np.asarray(sm.resize(im.size, Image.BILINEAR), np.float32) / 255.0


def bloom(img, thresh=0.62, radius=26, gain=0.55):
    l = img.max(2)
    m = np.clip((l - thresh) / (1 - thresh + 1e-5), 0, 1)
    hi = img * m[..., None]
    b = blur_fast(hi, radius, 2)
    b2 = blur_fast(hi, radius * 3.2, 4)
    add = b * 0.62 + b2 * 0.38
    return img + add * gain


def halation(img, radius=14, gain=0.16):
    l = np.clip((img.max(2) - 0.72) / 0.28, 0, 1)
    hi = img * l[..., None]
    a = blur_fast(hi, radius, 2)
    return img + a * np.array([1.0, 0.28, 0.18], np.float32) * gain


def grade(img, warm=0.05, contrast=1.12, lift=0.010):
    x = np.clip(img, 0, 1)
    # filmic S-curve (clip guards keep the power() finite)
    x = x * (1 - 0.18) + 0.18 * (x ** 1.0)          # gentle toe
    x = np.clip(x + contrast * (x - 0.5) * x * (1 - x) * 2.0, 0, 1)
    # split tone: warm highs, cool-ish shadows
    l = x.max(2, keepdims=True)
    x = x + np.clip(l, 0, 1) ** 1.4 * np.array([warm, warm * 0.45, -warm * 0.35], np.float32)
    x = x + (1 - l) ** 3 * np.array([-0.004, 0.0, 0.010], np.float32)
    return np.clip(x + lift, 0, 1)


def vignette(img, amt=0.42):
    r = np.sqrt(((XX - CX) / (W * 0.62)) ** 2 + ((YY - CY) / (H * 0.60)) ** 2)
    v = np.clip(1.0 - amt * np.clip(r - 0.42, 0, 2) ** 1.6, 0, 1)[..., None]
    return img * v


def chroma(img, amt=0.0016):
    im = _pil(img)
    hw, hh = W // 2, H // 2
    sm = im.resize((hw, hh), Image.BILINEAR)
    a = np.asarray(sm, np.float32) / 255.0
    def rz(ch, k):
        nw, nh = int(hw * k), int(hh * k)
        r = Image.fromarray(np.clip(ch * 255, 0, 255).astype(np.uint8)).resize((nw, nh),
                                                                              Image.BILINEAR)
        x = (nw - hw) // 2; y = (nh - hh) // 2
        return np.asarray(r.crop((x, y, x + hw, y + hh)), np.float32) / 255.0
    a[..., 0] = rz(a[..., 0], 1 + amt)
    a[..., 2] = rz(a[..., 2], 1 - amt)
    return np.asarray(_pil(a).resize((W, H), Image.BILINEAR), np.float32) / 255.0


_gstate = {"f": 0}
def grain(img, amount=0.030):
    _gstate["f"] += 1
    r = np.random.default_rng(_gstate["f"] * 7919)
    n = r.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)[:H, :W]
    l = img.mean(2, keepdims=True)
    a = amount * (0.55 + 0.75 * (1 - l))
    return np.clip(img + n[..., None] * a, 0, 1)


def sweep(img, t, strength=0.10, pos=None):
    """A soft raking light band drifting across the frame (light handshake)."""
    p = (pos if pos is not None else (t * 1.15 - 0.10)) * 1.6 - 0.3
    band = np.exp(-(((XX / W - p) - (YY / H - 0.5) * 0.35) ** 2) / (2 * 0.20 ** 2))
    l = img.max(2)[..., None]
    return img + band[..., None] * l * strength * 0.6


def dof(img, depth, focus, amount=1.0):
    """Depth-driven blur: bucket depths and blend three blur levels."""
    if amount <= 0.001:
        return img
    b1 = blur_fast(img, 2.4, 2)
    b2 = blur_fast(img, 7.0, 2)
    coc = np.clip(np.abs(depth - focus) / 0.42, 0, 1)[..., None] * amount
    out = img * (1 - coc) + b1 * coc * (1 - coc) * 2 + b2 * np.clip(coc - 0.5, 0, 1) * 2
    return np.clip(out, 0, 1)


# --------------------------------------------------------------------- type
_fc = {}


def font(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]


def text_layer(w, h, items):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for it in items:
        f = font(it.get("font", MONOB), it["size"])
        txt = it["text"]
        if it.get("tracking"):
            d2 = ImageDraw.Draw(im)
            tw = sum(d2.textlength(ch, font=f) + it["tracking"] for ch in txt) - it["tracking"]
            x = it["x"] - tw / 2 if it.get("center") else it["x"]
            for ch in txt:
                d.text((int(round(x)), int(it["y"])), ch, font=f,
                       fill=it.get("color", CREAM) + (it.get("alpha", 255),))
                x += d2.textlength(ch, font=f) + it["tracking"]
        else:
            x = it["x"] - d.textlength(txt, font=f) / 2 if it.get("center") else it["x"]
            d.text((x, it["y"]), txt, font=f, fill=it.get("color", CREAM) + (it.get("alpha", 255),))
    return np.asarray(im, np.float32) / 255.0


def over(base, layer):
    a = layer[..., 3:4]
    return base * (1 - a) + layer[..., :3] * a


# ------------------------------------------------------------------- shots
def shot_defs():
    P = lambda n: os.path.join(ASSETS, n)
    B = lambda n: os.path.join(BUILD, n)
    S = []

    S.append(dict(name="eyes", dur=6.0, src=P("plate_eyes.png"), kind="plate",
                  cam=[dict(dolly=0.0, px=0.010, py=0.004, zoom=1.02),
                       dict(dolly=0.085, px=-0.020, py=0.014, zoom=1.05)],
                  focus=0.62, sweep=0.16, dust=0.55, dof=0.85,
                  type=[dict(text="NAAM", size=30, x=90, y=1730, tracking=9,
                             color=CREAM, alpha=105, font=MONOB),
                        dict(text="01", size=30, x=990, y=1730, color=RED, alpha=180, font=MONOB)]))

    S.append(dict(name="edge", dur=6.0, src=B("edge_beauty.png"), z=B("edge_z.png"),
                  kind="cg", cam=[dict(dolly=0.0, px=0.0, py=0.0, zoom=1.00),
                                  dict(dolly=0.075, px=0.028, py=-0.014, zoom=1.03)],
                  focus=0.55, sweep=0.10, dust=0.70, dof=0.9, expo=0.62, bloom=0.26,
                  type=[dict(text="44 NAMES. ONE PRICE.", size=27, x=90, y=1738,
                             tracking=4, color=(226, 214, 198), alpha=120, font=MONOB)]))

    S.append(dict(name="hands", dur=6.0, src=P("plate_hands.png"), kind="plate",
                  cam=[dict(dolly=0.0, px=-0.012, py=0.012, zoom=1.03),
                       dict(dolly=0.075, px=0.014, py=-0.018, zoom=1.04)],
                  focus=0.66, sweep=0.13, dust=1.0, dof=0.8,
                  type=[dict(text="", size=1, x=0, y=0)]))

    S.append(dict(name="writing", dur=6.0, src=P("plate_writing.png"), kind="plate",
                  cam=[dict(dolly=0.0, px=0.022, py=0.0, zoom=1.05),
                       dict(dolly=0.055, px=-0.020, py=0.010, zoom=1.06)],
                  focus=0.60, sweep=0.11, dust=0.65, dof=1.0,
                  type=[dict(text="5 NAMES", size=31, x=90, y=300, tracking=7,
                             color=(226, 214, 198), alpha=110, font=MONOB)]))

    S.append(dict(name="shards", dur=6.0, src=B("shards_beauty.png"), z=B("shards_z.png"),
                  kind="cg", cam=[dict(dolly=0.10, px=-0.020, py=0.010, zoom=1.10, roll=1.2),
                                  dict(dolly=-0.02, px=0.020, py=-0.010, zoom=1.00, roll=-0.6)],
                  focus=0.50, sweep=0.08, dust=0.9, dof=1.0, flash=True, expo=0.90, bloom=0.42,
                  type=[dict(text="", size=1, x=0, y=0)]))

    S.append(dict(name="mask", dur=6.0, src=P("plate_mask.png"), kind="plate",
                  cam=[dict(dolly=0.075, px=0.0, py=0.008, zoom=1.06),
                       dict(dolly=0.0, px=0.0, py=-0.004, zoom=1.00)],
                  focus=0.70, sweep=0.20, dust=0.45, dof=0.7,
                  type=[dict(text="NOBODY WRITES FIVE.", size=27, x=90, y=1740,
                             tracking=4, color=(226, 214, 198), alpha=135, font=MONOB)]))

    S.append(dict(name="page", dur=6.0, src=P("plate_page.png"), kind="plate",
                  cam=[dict(dolly=0.02, px=-0.018, py=0.016, zoom=1.03),
                       dict(dolly=0.09, px=0.016, py=-0.020, zoom=1.06)],
                  focus=0.58, sweep=0.14, dust=0.8, dof=1.0, embers=True,
                  type=[dict(text="", size=1, x=0, y=0)]))

    S.append(dict(name="type", dur=6.0, src=B("type_beauty.png"), z=B("type_z.png"),
                  kind="cg", cam=[dict(dolly=0.0, px=0.0, py=0.0, zoom=1.00),
                                  dict(dolly=0.05, px=0.0, py=0.0, zoom=1.02)],
                  focus=0.55, sweep=0.09, dust=0.55, dof=0.6, expo=0.72, bloom=0.24,
                  type=[dict(text="JINKE NAAM TUM NAHI LE SAKTE", size=27, x=W / 2, y=1560,
                             center=True, tracking=4, color=(226, 216, 202), alpha=210,
                             delay=1.50, font=MONOB),
                        dict(text="UNKE NAAM PE APNI ZINDAGI", size=27, x=W / 2, y=1632,
                             center=True, tracking=4, color=(226, 216, 202), alpha=205,
                             delay=2.30, font=MONOB),
                        dict(text="NAHI DE SAKTE.", size=27, x=W / 2, y=1704,
                             center=True, tracking=4, color=RED, alpha=235,
                             delay=3.05, font=MONOB)]))
    return S


def plate_for(s):
    if s["kind"] == "plate":
        rgb = load_rgb(s["src"])
        return rgb, plate_depth(rgb)
    rgb = load_rgb(s["src"])
    z = load_depth(s["z"])
    return rgb, z


def ember_layer(t, gain=1.0):
    r = np.random.default_rng(5)
    n = 90
    x = r.uniform(0.25, 0.85, n) * W
    y0 = r.uniform(0.15, 0.95, n) * H
    s = r.uniform(0.8, 2.6, n)
    sp = r.uniform(40, 150, n)
    layer = np.zeros((H, W, 3), np.float32)
    for i in range(n):
        y = (y0[i] - sp[i] * t / 6.0) % H
        x2 = x[i] + 26 * np.sin(t * 1.3 + i)
        k = kernel(s[i]); rad = k.shape[0] // 2
        ix, iy = int(x2), int(y)
        x0, x1 = max(0, ix - rad), min(W, ix + rad + 1)
        y0_, y1_ = max(0, iy - rad), min(H, iy + rad + 1)
        if x1 <= x0 or y1_ <= y0_:
            continue
        kk = k[(y0_ - iy + rad):(y1_ - iy + rad), (x0 - ix + rad):(x1 - ix + rad)]
        layer[y0_:y1_, x0:x1] += kk[..., None] * 1.4 * gain * np.array([1.0, 0.45, 0.12])
    return layer


def flash(img, t, dur=0.22):
    if t < dur:
        k = (1 - t / dur) ** 2
        img = img + k * np.array([0.85, 0.30, 0.20], np.float32)
    return img


def render_frame(s, lt, idx):
    """lt = local time in seconds inside the shot."""
    u = ease(lt / s["dur"])
    c0, c1 = s["cam"]
    c = {k: c0.get(k, 0.0) + (c1.get(k, 0.0) - c0.get(k, 0.0)) * u for k in
         ("dolly", "px", "py", "zoom", "roll")}
    c["zoom"] = c0.get("zoom", 1.0) + (c1.get("zoom", 1.0) - c0.get("zoom", 1.0)) * u
    rgb, depth = s["_rgb"], s["_depth"]
    img = reproject(rgb, depth, c)
    # depth of field: rack slightly through the move
    f = s["focus"] + 0.06 * (u - 0.5)
    img = dof(img, depth, f, s.get("dof", 1.0))
    # light handshake
    if s.get("sweep"):
        img = sweep(img, u, s["sweep"])
    # atmosphere
    if s.get("dust"):
        img = img + dust_layer(s["_dust"], c, lt * 1.0, s["dust"])
    if s.get("embers"):
        img = img + ember_layer(lt, 0.9)
    img = bloom(img, gain=s.get("bloom", 0.52))
    img = halation(img)
    img = grade(img, warm=0.055)
    img = np.clip(img * s.get("expo", 1.16), 0, 1)
    img = vignette(img, 0.34)
    if s.get("flash"):
        img = flash(img, lt)
    img = chroma(img, 0.0014)
    img = grain(img, 0.026)
    img = np.clip(img, 0, 1)
    # type
    items = []
    for it in s.get("type", []):
        if not it["text"]:
            continue
        a = it.get("alpha", 255)
        dly = it.get("delay", 0.45)
        tt = min(1.0, max(0.0, (lt - dly) / 0.55))
        items.append({**it, "alpha": int(a * tt)})
    if items:
        img = over(img, text_layer(W, H, items))
    # fades
    if lt < 0.30:
        img = img * ease(lt / 0.30)
    if s["dur"] - lt < 0.26:
        img = img * ease((s["dur"] - lt) / 0.26)
    return img


SHOTS = None


def build_shots():
    global SHOTS
    SHOTS = shot_defs()
    for i, s in enumerate(SHOTS):
        s["_rgb"], s["_depth"] = plate_for(s)
        s["_dust"] = make_dust(150, seed=10 + i)


# ------------------------------------------------------------------- audio
SR = 48000


def synth_audio(total, cuts, path):
    n = int(total * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)

    def env(a, d, length, at):
        i0 = int(at * SR); ln = int(length * SR)
        if i0 >= n:
            return None
        seg = np.arange(min(ln, n - i0)) / SR
        e = np.minimum(seg / max(a, 1e-3), 1.0) * np.exp(-seg / max(d, 1e-3))
        return i0, e

    # sub drone bed
    drone = 0.16 * np.sin(2 * np.pi * 43 * t) + 0.07 * np.sin(2 * np.pi * 64.5 * t + 1.1)
    drone *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.06 * t)
    out += drone.astype(np.float32)

    # impact at each cut
    r = np.random.default_rng(21)
    for i, ct in enumerate(cuts):
        g = env(0.002, 0.30, 1.6, ct)
        if g:
            i0, e = g
            k = len(e)
            thump = np.sin(2 * np.pi * (72 * np.exp(-np.arange(k) / SR * 6)) * np.arange(k) / SR)
            noise = r.normal(0, 1, k) * np.exp(-np.arange(k) / SR * 22)
            out[i0:i0 + k] += (0.55 * thump * e + 0.18 * noise * e).astype(np.float32)
        # metallic tick
        g2 = env(0.0005, 0.05, 0.3, ct)
        if g2:
            i0, e = g2
            k = len(e)
            hi = np.sin(2 * np.pi * 3100 * np.arange(k) / SR) * e * 0.05
            out[i0:i0 + k] += hi.astype(np.float32)

    # heartbeat 60 -> 96 bpm from 28s
    bt = 28.0
    bpm = 60.0
    while bt < total - 1.0:
        g = env(0.004, 0.13, 0.5, bt)
        if g:
            i0, e = g
            k = len(e)
            th = np.sin(2 * np.pi * 52 * np.arange(k) / SR) * e * 0.42
            out[i0:i0 + k] += th.astype(np.float32)
        g = env(0.004, 0.10, 0.4, bt + 0.22)
        if g:
            i0, e = g
            k = len(e)
            out[i0:i0 + k] += (np.sin(2 * np.pi * 46 * np.arange(k) / SR) * e * 0.26).astype(np.float32)
        bpm = min(96, bpm + 3.0)
        bt += 60.0 / bpm

    # riser into the end card
    i0 = int(43.2 * SR)
    k = int(4.4 * SR)
    if i0 + k < n:
        seg = np.arange(k) / SR
        nz = r.normal(0, 1, k)
        # cheap lowpass
        b = np.convolve(nz, np.ones(24) / 24, mode="same")
        out[i0:i0 + k] += (b * (seg / seg.max()) ** 2.4 * 0.30).astype(np.float32)

    # the silence punch
    s0, s1 = int(47.30 * SR), int(47.80 * SR)
    out[s0:s1] *= 0.02

    # final hit
    g = env(0.002, 0.55, 2.2, 47.80)
    if g:
        i0, e = g
        k = len(e)
        out[i0:i0 + k] += (np.sin(2 * np.pi * 38 * np.arange(k) / SR) * e * 0.75).astype(np.float32)

    # gentle top-end tuck + normalise
    out = np.tanh(out * 1.25) * 0.92
    out /= max(1e-6, np.abs(out).max())
    out *= 0.89
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes(pcm.tobytes())
    return path


# -------------------------------------------------------------------- main
def main():
    args = sys.argv[1:]
    preview = None
    out = OUT
    if "--preview" in args:
        preview = float(args[args.index("--preview") + 1])
    if "--out" in args:
        out = args[args.index("--out") + 1]
    only = None
    if "--shots" in args:
        only = {int(x) for x in args[args.index("--shots") + 1].split(",")}
    build_shots()
    total = sum(s["dur"] for s in SHOTS)
    print(f"shots {len(SHOTS)} total {total:.2f}s frames {int(total * FPS)}")

    if preview is not None:
        # write one still per shot for inspection
        acc = 0.0
        for i, s in enumerate(SHOTS):
            img = render_frame(s, s["dur"] * preview, i)
            p = os.path.join(BUILD, f"prev_{i}_{s['name']}.png")
            Image.fromarray((img * 255).astype(np.uint8)).save(p)
            print("PREV", p)
        return

    if only is not None:
        from imageio_ffmpeg import get_ffmpeg_exe
        ff = get_ffmpeg_exe()
        sel = [s for i, s in enumerate(SHOTS) if i in only]
        tot = sum(s["dur"] for s in sel)
        cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
               "-crf", "19", "-pix_fmt", "yuv420p", "-profile:v", "high",
               "-level", "4.2", "-an", out]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for s in sel:
            nf = int(round(s["dur"] * FPS))
            for f in range(nf):
                pr.stdin.write((render_frame(s, f / FPS, 0) * 255).astype(np.uint8).tobytes())
            print("  done", s["name"], flush=True)
        pr.stdin.close(); pr.wait()
        print("WROTE", out, f"{tot:.2f}s")
        return

    from imageio_ffmpeg import get_ffmpeg_exe
    ff = get_ffmpeg_exe()
    wav = os.path.join(BUILD, "naam_prime_audio.wav")
    cuts = []
    acc = 0.0
    for s in SHOTS:
        acc += s["dur"]; cuts.append(round(acc, 3))
    synth_audio(total, cuts, wav)
    print("AUDIO", wav)

    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "slow", "-crf", "19",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    idx = 0
    for s in SHOTS:
        nf = int(round(s["dur"] * FPS))
        for f in range(nf):
            lt = f / FPS
            img = render_frame(s, lt, idx)
            pr.stdin.write((img * 255).astype(np.uint8).tobytes())
            idx += 1
            if idx % 120 == 0:
                print(f"  frame {idx}/{int(total * FPS)}", flush=True)
    pr.stdin.close()
    pr.wait()
    print("WROTE", out)


if __name__ == "__main__":
    main()
