"""NAAM LO — 48.0 s mix for the SURFACE-OFF cut.
3-layer rule: transient + body + tail. Silence punch. -14 LUFS / -1 dBTP.
"""
import numpy as np, wave, sys

SR = 48000
DUR = 48.0
N = int(SR * DUR)
rng = np.random.default_rng(23)
L = np.zeros(N); R = np.zeros(N)
tt = np.arange(N) / SR

def _f(x, fc, hp=False):
    n = len(x)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1.0 / SR)
    r = 1.0 / np.sqrt(1.0 + (f / fc) ** 2)
    if hp: r = 1.0 - r
    return np.fft.irfft(X * r, n)

def env(n, a=0.004, d=0.2, curve=4.0):
    e = np.ones(n)
    na = max(1, min(n, int(a * SR))); nd = max(1, int(d * SR))
    e[:na] = np.linspace(0, 1, na)
    tail = min(nd, n - na)
    if tail > 0:
        e[na:na + tail] = np.exp(-curve * np.linspace(0, 1, tail))
        if na + tail < n: e[na + tail:] = 0
    return e

def add(sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i < 0: return
    s = sig[: max(0, N - i)]
    L[i:i + len(s)] += s * g * (1 - max(0, pan)) ** 0.5
    R[i:i + len(s)] += s * g * (1 + min(0, pan)) ** 0.5

# ---------- room ----------
room = _f(rng.standard_normal(N), 240) + 0.5 * _f(rng.standard_normal(N), 55)
room *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.11 * tt) 
room /= np.abs(room).max() + 1e-9
L += room * 0.020; R += room * 0.020

def rustle(dur=0.8, spikes=8, lo=900, hi=7000):
    n = int(dur * SR)
    x = _f(rng.standard_normal(n), hi, True); x = _f(x, lo)
    e = np.zeros(n)
    for _ in range(spikes):
        p = rng.integers(0, max(1, n - 2000)); w = rng.integers(300, 2400)
        seg = np.exp(-np.linspace(0, 6, min(w, n - p)))
        e[p:p + len(seg)] += seg * rng.uniform(0.3, 1.0)
    x *= e
    return x / (np.abs(x).max() + 1e-9)

def crack(hi=5200, dur=0.13):
    n = int(dur * SR)
    x = _f(rng.standard_normal(n), hi, True) * env(n, 0.0008, dur, 9)
    x += np.sin(2 * np.pi * 2600 * np.arange(n) / SR) * env(n, 0.0005, 0.05, 12) * 0.3
    return x / (np.abs(x).max() + 1e-9)

def whoosh(dur=0.34, up=True):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    x = _f(x, 1600 if up else 900)
    x *= np.sin(np.linspace(0, np.pi, n)) ** 1.4
    return x / (np.abs(x).max() + 1e-9)

def tap():
    n = int(0.09 * SR)
    x = rng.standard_normal(n) * env(n, 0.001, 0.07, 9)
    x += np.sin(2 * np.pi * 1150 * np.arange(n) / SR) * env(n, 0.001, 0.035, 10) * 0.35
    return x / (np.abs(x).max() + 1e-9)

def thump(f=52, dur=0.20):
    n = int(dur * SR)
    x = np.sin(2 * np.pi * f * np.arange(n) / SR) * env(n, 0.002, dur, 7)
    return x / (np.abs(x).max() + 1e-9)

# ---------- cut whooshes (every hidden cut, quiet) ----------
CUTS = [s * 1.6 for s in range(1, 30)]
for k, c in enumerate(CUTS):
    add(whoosh(0.26, up=(k % 2 == 0)), c - 0.13, 0.10, (-0.5 if k % 2 else 0.5))

# ---------- card shatters (D3) ----------
for t in (2.90, 9.30, 15.70, 25.30, 31.70, 38.10, 44.52):
    add(crack(5600), t, 0.34, rng.uniform(-.4, .4))
    add(crack(3200, 0.2), t + 0.03, 0.16, rng.uniform(-.5, .5))

# ---------- surface-off dissolves (D2) ----------
for t in (20.00, 39.15):
    add(whoosh(0.55), t, 0.24, 0.0)
    n = int(0.7 * SR)
    shimmer = np.sin(2 * np.pi * np.cumsum(np.linspace(900, 3400, n)) / SR) * env(n, 0.05, 0.62, 3)
    add(shimmer, t, 0.07, 0.0)

# ---------- object foley ----------
for t, g, p in [(0.25, .34, -.25), (0.80, .24, .2), (1.55, .20, -.1), (2.55, .22, .25),
                (5.10, .16, -.2), (7.90, .14, .3), (13.10, .18, -.25), (19.90, .20, .2),
                (28.10, .16, -.3), (33.70, .18, .25), (40.10, .16, -.2), (44.90, .14, .2)]:
    add(rustle(), t, g * 1.7, p)

for t in [7.10, 8.30, 11.40, 12.90, 17.20, 18.40]:
    add(crack(6800, 0.07), t, 0.10, rng.uniform(-.4, .4))

for t in [29.30, 30.10, 30.90, 31.70, 32.50]:
    add(tap(), t, .42, rng.uniform(-.35, .35))

# ---------- sub drone ----------
drone = np.sin(2 * np.pi * (36 + 16 * np.clip((tt - 16) / 22, 0, 1)) * tt)
drone *= np.clip((tt - 15.5) / 6.0, 0, 1) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.2 * tt))
drone *= np.where(tt > 38.40, 0, 1)
drone /= np.abs(drone).max() + 1e-9
L += drone * 0.125; R += drone * 0.125

# ---------- heartbeat ----------
t = 28.80
while t < 38.2:
    bpm = 62 + 34 * ((t - 28.8) / 9.4)
    add(thump(50), t, .42, -0.10); add(thump(44), t + 0.15, .30, 0.10)
    t += 60.0 / bpm

# ---------- riser ----------
n = int(1.10 * SR)
x = _f(rng.standard_normal(n), 900, True) * np.linspace(0.02, 1, n) ** 2.2
sweep = np.sin(2 * np.pi * np.cumsum(np.linspace(180, 1900, n)) / SR) * np.linspace(0, 1, n) ** 3 * 0.25
add(x, 37.30, .20, 0.0); add(sweep, 37.30, .12, 0.0)

# ---------- THE POP (38.40) ----------
pn = int(0.42 * SR)
f = np.linspace(1300, 72, pn) ** 1.25
body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(pn, 0.0008, 0.38, 5.0)
click = rng.standard_normal(pn) * env(pn, 0.0004, 0.006, 30)
pop = body + click * 0.55
add(pop / (np.abs(pop).max() + 1e-9), 38.40, 1.0, 0.0)

# ---------- silence punch (D9) ----------
s0, s1 = int(38.86 * SR), int(39.42 * SR)
L[s0:s1] = 0; R[s0:s1] = 0

# ---------- x-ray ignite (D1) ----------
n = int(1.5 * SR)
ign = np.sin(2 * np.pi * 92 * np.arange(n) / SR) * env(n, 0.01, 1.4, 3.2)
add(ign, 42.30, 0.30, 0.0)
add(thump(38, 0.5), 42.30, 0.34, 0.0)

# ---------- final tone ----------
n = int(3.2 * SR)
tone = np.sin(2 * np.pi * 46 * np.arange(n) / SR) * env(n, 0.9, 2.4, 2.0)
add(tone / (np.abs(tone).max() + 1e-9), 44.80, 0.34, 0.0)

# ---------- master: -14 LUFS / -1 dBTP ----------
mix = np.stack([L, R], 1)
rms = np.sqrt((mix ** 2).mean())
gain = 10 ** ((-15.0 - 20 * np.log10(rms + 1e-12)) / 20)
mix *= gain
for _ in range(6):                       # soft limit toward -1 dBTP
    pk = np.abs(mix).max()
    if pk <= 0.891: break
    mix = np.tanh(mix * 1.15) / 1.15
    mix *= 0.891 / max(1e-9, np.abs(mix).max())
fade = int(0.30 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
pcm = (np.clip(mix, -1, 1) * 32767).astype('<i2')
with wave.open(sys.argv[1] if len(sys.argv) > 1 else 'audio/naam.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(f"{len(mix)/SR:.3f}s  peak {20*np.log10(np.abs(mix).max()):.2f} dBFS  rms {20*np.log10(np.sqrt((mix**2).mean())):.2f} dBFS")
