"""NAAM LO — sound design. 55.0 s, 48 kHz stereo. No music. Only objects, and one pop."""
import numpy as np, wave, sys

SR = 48000
DUR = 55.0
N = int(SR * DUR)
rng = np.random.default_rng(11)
L = np.zeros(N); R = np.zeros(N)

def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i < 0: return
    s = sig[: max(0, N - i)]
    gl = gain * (1 - max(0, pan)) ** 0.5
    gr = gain * (1 + min(0, pan)) ** 0.5
    L[i:i + len(s)] += s * gl
    R[i:i + len(s)] += s * gr

def env(n, a=0.004, d=0.2, curve=4.0):
    e = np.ones(n)
    na = max(1, int(a * SR)); nd = max(1, int(d * SR))
    na = min(na, n)
    e[:na] = np.linspace(0, 1, na)
    tail = min(nd, n - na)
    if tail > 0:
        e[na:na + tail] = np.exp(-curve * np.linspace(0, 1, tail))
        if na + tail < n: e[na + tail:] = 0
    return e

def _filt(x, fc, hp=False):
    n = len(x)
    if n < 4: return x
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    resp = 1.0 / np.sqrt(1.0 + (f / fc) ** 2)
    if hp: resp = 1.0 - resp
    return np.fft.irfft(X * resp, n)

def lp(x, fc): return _filt(x, fc, False)
def hp(x, fc): return _filt(x, fc, True)

def noise(n):
    return rng.standard_normal(n)

# ---------- 1. room tone ----------
room = lp(noise(N), 260) * 0.9 + lp(noise(N), 60) * 0.5
room *= (0.85 + 0.15 * np.sin(2 * np.pi * 0.13 * np.arange(N) / SR))
room /= (np.max(np.abs(room)) + 1e-9)
L += room * 0.024
R += room * 0.024

# ---------- 2. card rustle ----------
def rustle(dur=0.9, spikes=9, lo=900, hi=7000):
    n = int(dur * SR)
    x = hp(lp(noise(n), hi), lo)
    e = np.zeros(n)
    for _ in range(spikes):
        p = rng.integers(0, max(1, n - 2000))
        w = rng.integers(300, 2600)
        seg = np.exp(-np.linspace(0, 6, min(w, n - p)))
        e[p:p + len(seg)] += seg * rng.uniform(0.3, 1.0)
    x *= e
    return x / (np.max(np.abs(x)) + 1e-9)

for t, g, p in [(0.25, .30, -.25), (0.75, .22, .2), (1.45, .18, -.1),
                (2.45, .20, .25), (6.05, .16, -.2), (19.95, .26, -.3),
                (20.55, .12, .2), (41.05, .20, .1), (43.45, .26, -.2),
                (44.10, .20, .25), (45.20, .16, -.15), (46.30, .12, .2)]:
    add(rustle(), t, g * 1.75, p)

# ---------- 3. pencil ----------
def scratch(dur=0.18):
    n = int(dur * SR)
    x = hp(noise(n), 1800)
    e = np.exp(-np.linspace(0, 3.5, n)) * (0.6 + 0.4 * np.abs(np.sin(np.linspace(0, 18, n))))
    return (x * e) / (np.max(np.abs(x * e)) + 1e-9)
add(scratch(0.30), 19.05, .46, -.15)
for k in range(14):
    add(scratch(rng.uniform(0.05, 0.16)), 20.6 + k * 0.32 + rng.uniform(-0.05, 0.05),
        rng.uniform(.10, .20), rng.uniform(-.4, .4))
add(scratch(0.10), 35.25, .28, .1)
add(scratch(0.10), 36.25, .28, .1)
add(scratch(0.10), 37.30, .28, .1)

# ---------- 4. finger taps on card edges (counting) ----------
def tap():
    n = int(0.09 * SR)
    x = noise(n) * env(n, 0.001, 0.07, 9)
    x += np.sin(2 * np.pi * 1150 * np.arange(n) / SR) * env(n, 0.001, 0.035, 10) * 0.35
    return x / (np.max(np.abs(x)) + 1e-9)
for t in [9.25, 10.35, 35.15, 35.95, 36.75, 37.55, 38.35]:
    add(tap(), t, .46, rng.uniform(-.35, .35))

# ---------- 5. sub drone ----------
tt = np.arange(N) / SR
drone = np.sin(2 * np.pi * (38 + 14 * np.clip((tt - 20) / 22, 0, 1)) * tt)
drone *= np.clip((tt - 19.0) / 6.0, 0, 1) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.22 * tt))
drone *= np.where(tt > 42.18, 0, 1)
drone /= (np.max(np.abs(drone)) + 1e-9)
L += drone * 0.135; R += drone * 0.135

# ---------- 6. heartbeat 62 -> 96 bpm, 31.0 -> 42.5 ----------
def thump(f=52, dur=0.20):
    n = int(dur * SR)
    x = np.sin(2 * np.pi * f * np.arange(n) / SR) * env(n, 0.002, dur, 7)
    return x / (np.max(np.abs(x)) + 1e-9)
t = 31.0; beat = 0
while t < 42.42:
    bpm = 62 + (96 - 62) * ((t - 31.0) / 11.5)
    add(thump(50), t, .50, -0.10); add(thump(44), t + 0.155, .36, 0.10)
    beat += 1
    t += 60.0 / bpm

# ---------- 7. riser, cut dead at the pop ----------
n = int(1.15 * SR)
x = hp(noise(n), 900) * np.linspace(0.02, 1.0, n) ** 2.2
sweep = np.sin(2 * np.pi * np.cumsum(np.linspace(180, 1900, n)) / SR) * np.linspace(0, 1, n) ** 3 * 0.25
add(x, 41.02, .26, 0.0); add(sweep, 41.02, .13, 0.0)

# ---------- 8. the pop ----------
pn = int(0.42 * SR)
f = np.linspace(1300, 72, pn) ** 1.25
body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(pn, 0.0008, 0.38, 5.0)
click = noise(pn) * env(pn, 0.0004, 0.006, 30)
pn2 = body + click * 0.55
pn2 /= (np.max(np.abs(pn2)) + 1e-9)
add(pn2, 42.18, 1.0, 0.0)

# ---------- 9. hard silence after the pop ----------
s0, s1 = int(42.63 * SR), int(43.34 * SR)
L[s0:s1] = 0.0; R[s0:s1] = 0.0
# kill the drone before the pop too
k = int(41.90 * SR)
fade = np.linspace(1, 0, int(42.18 * SR) - k)
L[k:int(42.18 * SR)] *= fade; R[k:int(42.18 * SR)] *= fade

# ---------- 10. last low tone under the moral ----------
n = int(4.6 * SR)
tone = np.sin(2 * np.pi * 46 * np.arange(n) / SR) * env(n, 0.9, 3.6, 2.0)
tone /= (np.max(np.abs(tone)) + 1e-9)
add(tone, 50.50, 0.40, 0.0)

# ---------- master ----------
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.55) / 1.55
peak = np.max(np.abs(mix))
mix = mix / peak * 0.89
# tiny fades at the very ends only
fade_in = int(0.05 * SR); mix[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
fade_out = int(0.35 * SR); mix[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]

pcm = (np.clip(mix, -1, 1) * 32767).astype('<i2')
with wave.open(sys.argv[1] if len(sys.argv) > 1 else 'audio/naam.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

rms = np.sqrt(np.mean(mix ** 2))
print(f"wrote {len(mix)/SR:.3f}s  peak {20*np.log10(peak):.2f} dBFS  rms {20*np.log10(rms):.2f} dBFS")
