"""Keep render, composite, and encode separate so type can be revised cheaply."""
import argparse
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw
from pilot import ENDS, FPS, FRAMES, QA, ROOT, SAMPLES, WORK, dims, make_dirs, plate_range
from mix import FF, ff
from titles import composite, verify_fonts


def plates(frames):
    w,h = dims()
    size = w*h*4
    selected = sorted(set(frames))
    for i in range(len(ENDS)-1):
        p,lo,hi = plate_range(i,w,h)
        picks = [f for f in selected if lo<=f<hi]
        if not picks:
            continue
        with p.open('rb') as src:
            for f in picks:
                if src.tell()!=(f-lo)*size:
                    src.seek((f-lo)*size)
                a=src.read(size)
                if len(a)!=size:raise EOFError((p,f,len(a)))
                yield f, Image.frombytes('RGBA',(w,h),a,'raw','RGBA',0,-1)


def board(path, frames, clean):
    w,h = 480,270
    columns = 3
    a = Image.new('RGB', (columns*w, ((len(frames)+columns-1)//columns)*(h+29)), (24,31,30))
    d = ImageDraw.Draw(a)
    for j,(i,im) in enumerate(plates(frames)):
        x,y=(j%columns)*w,(j//columns)*(h+29)
        px = im if clean else composite(im,i)
        a.paste(px.convert('RGB').resize((w,h),Image.Resampling.LANCZOS),(x,y))
        d.text((x+12,y+h+7),f'{i:03} / {i/FPS:5.2f}s',fill=(231,229,214))
    a.save(path, quality=95)
    print(path)


def render(clean=False):
    w,h=dims()
    p=WORK/('clean-picture.mp4' if clean else 'v3-picture.mp4')
    q=p.with_suffix('.pending.mp4')
    # Interpret the rendered R'G'B' as full range and explicitly convert to Rec.709.
    # One CFR encode with no interpolation, B-frame timestamps verified in QA.
    args=[FF,'-hide_banner','-nostdin','-xerror','-loglevel','warning','-y','-filter_threads','1',
          '-f','rawvideo','-pixel_format','rgb24','-framerate',str(FPS),'-video_size',f'{w}x{h}','-i','pipe:0',
          '-vf','scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p',
          '-an','-c:v','libx264','-threads','2','-preset','fast','-crf','16','-maxrate','9500k','-bufsize','19000k',
          '-profile:v','high','-g','60','-keyint_min','15','-pix_fmt','yuv420p','-video_track_timescale','30000',
          '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv',
          '-fps_mode','passthrough','-movflags','+faststart+write_colr',str(q)]
    with subprocess.Popen(args, stdin=subprocess.PIPE) as sub:
        assert sub.stdin is not None
        try:
            for f,im in plates(range(FRAMES)):
                if not clean:composite(im,f)
                sub.stdin.write(im.convert('RGB').tobytes())
                if (f+1)%120==0:print(f'V3 finish: {f+1}/{FRAMES} frames',flush=True)
            sub.stdin.close()
            if sub.wait():raise RuntimeError('FFmpeg rejected the picture encode')
        except BaseException:
            sub.kill();raise
    q.replace(p)
    return p


def mux(picture):
    p=WORK/'v3-opening-review.mp4'
    q=p.with_suffix('.pending.mp4')
    ff('-loglevel','warning','-y','-i',picture,'-i',WORK/'v3-mix.wav',
       '-map','0:v:0','-map','1:a:0','-map_metadata','-1','-map_chapters','-1',
       '-c:v','copy', '-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0',
       '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv',
       '-af',f'atrim=end_sample={SAMPLES}', '-c:a','aac','-b:a','224k','-ar','48000','-ac','2',
       '-metadata','title=This Ant Bites the Ground to Escape — V3 Opening Pilot',
       '-metadata','artist=Monarch Cam','-metadata:s:a:0','language=eng',
       '-movie_timescale','48000','-movflags','+faststart+write_colr',q)
    q.replace(p)
    return p


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--board', help='comma-separated frames to composite to a QA board')
    cli.add_argument('--out',type=Path,default=QA/'composite-board.jpg')
    cli.add_argument('--clean',action='store_true',help='skip graphics, keep the native grade')
    a=cli.parse_args()
    make_dirs()
    if not a.clean:verify_fonts()
    if a.board:
        fs=sorted(set(int(i) for i in a.board.split(',')))
        if not fs or min(fs)<0 or max(fs)>=FRAMES:cli.error('board frames outside opening')
        board(a.out,fs,a.clean)
    else:
        p=render(a.clean)
        if not a.clean:p=mux(p)
        print(f'V3_COMPOSITE_READY {p}')


if __name__=='__main__':main()
