"""QC for the NAAM PRIME cut: contact sheet + measured gates."""
import os, subprocess, json, sys
import numpy as np
from PIL import Image
from imageio_ffmpeg import get_ffmpeg_exe

FF = get_ffmpeg_exe()
ROOT = os.path.dirname(os.path.abspath(__file__))
MP4 = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(
    os.path.join(ROOT, "..", "..", "deliverables", "MONARCH_NAAM_PRIME_1080x1920.mp4"))
OUT = os.path.join(ROOT, "build")


def probe(path):
    r = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    return r


def frames_at(times, w=270, h=480):
    outs = []
    for i, t in enumerate(times):
        p = os.path.join(OUT, f"qc_{i:02d}.png")
        subprocess.run([FF, "-y", "-ss", f"{t:.2f}", "-i", MP4, "-frames:v", "1",
                        "-vf", f"scale={w}:{h}", p], capture_output=True)
        outs.append(Image.open(p).convert("RGB"))
    return outs


def main():
    info = probe(MP4)
    print(info[-500:])
    dur = 48.0
    n_shot = 8
    times = [(i + 0.5) * (dur / n_shot) for i in range(n_shot)]
    ims = frames_at(times)
    sheet = Image.new("RGB", (270 * 4, 480 * 2), (12, 12, 12))
    for i, im in enumerate(ims):
        sheet.paste(im, (270 * (i % 4), 480 * (i // 4)))
    sp = os.path.join(OUT, "CONTACT_SHEET.png")
    sheet.save(sp)
    print("SHEET", sp)

    # decoded-frame metrics on a sparse grid
    p = subprocess.run([FF, "-v", "error", "-i", MP4, "-vf", "fps=2,scale=180:320",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8)
    fr = a.reshape(-1, 320, 180, 3).astype(np.float32) / 255
    print(f"sampled frames {len(fr)}")
    lum = fr.mean((1, 2, 3))
    diffs = np.abs(np.diff(fr, axis=0)).mean((1, 2, 3))
    print(f"luma mean {lum.mean()*255:.1f} min {lum.min()*255:.1f} max {lum.max()*255:.1f}")
    print(f"black frames {(lum < 0.02).sum()} / {len(lum)}")
    print(f"motion mean {diffs.mean():.4f} max {diffs.max():.4f} "
          f"min {diffs.min():.4f}")
    # repetition gate: identical consecutive samples
    dup = (diffs < 0.0015).sum()
    print(f"frozen pairs {dup} / {len(diffs)}")
    ss = 1 - np.mean((fr[0] - fr[-1]) ** 2) / np.mean((fr[0] - fr[0].mean()) ** 2)
    print(f"SSIM-ish(first,last) {ss:.3f}")


if __name__ == "__main__":
    main()
