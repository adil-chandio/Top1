"""Finish the fresh 9:16 picture, retaining evidence and the continuous loop seam."""
import argparse
from functools import lru_cache
from hashlib import sha256
import os
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from common import CACHE, EXPORT, FONT, FPS, FRAMES, NATIVE, QA, WORK, read_plan

WIDTH,HEIGHT=EXPORT
FF = os.environ.get('FFMPEG','ffmpeg')
FONT_SHA='acad6de1fc93436f5c0f1f4137751ef04f1aea3063e7036535970ffcfbd79f72'
# Coords use the 1080x1920 export. Numbers and marks are editorial labels, never
# real measurements, proxies for a YouTube button, or captions requiring sound.
SAFEX,SAFEY = 83,234
PAPER='#fbf4e2'; AMBER='#f6ce8e'; TEAL='#a9dccb'; SILVER='#c8dcd8'
CUES=[
    # lo, hi, top label, heading, accent, heading size, shadow strength
    (3,49,'THAT JUMP STARTED WITH',['A BITE.'],AMBER,106,.39),
    (135,243,'ANTLION PIT',[],PAPER,0,.54),
    (319,422,'01  /  AIR',[],TEAL,0,.27),
    (371,422,None,['NO LIFT.'],PAPER,84,.26),
    (423,529,'02  /  SAND',[],AMBER,0,.35),
    (480,529,None,['LIFT.'],PAPER,84,.33),
    (696,744,'SECOND JUMP',['STILL INSIDE.'],AMBER,79,.51),
    (749,807,'JAW RESTRAINT TEST',[],SILVER,0,.24),
    (815,911,'JAW RESTRAINT TEST',['JAWS SEALED.'],SILVER,81,.22),
    (913,990,'MONARCH CAM  /  01A',['SAME TRAP.','NO SNAP.'],AMBER,81,.66),
]


def ease(t):
    t=min(1.,max(0.,t));return t*t*(3.-2.*t)


@lru_cache(maxsize=16)
def font(size,weight):
    face=ImageFont.truetype(str(FONT),size);face.set_variation_by_axes([weight]);return face


def print_tracking(draw, at, txt, face, color, extra):
    x,y=at
    for t in txt:
        draw.text((round(x),y),t,font=face,fill=color,anchor='lt')
        x+=face.getlength(t)+extra
    return x


@lru_cache(maxsize=24)
def layer(label,lines,tone,size):
    # Render a cropped art layer, with soft shadow; only the picture above the
    # subject is touched. The graphic does not compete with swipe UI at bottom.
    size0=(835,258)
    a=Image.new('RGBA',size0);d=ImageDraw.Draw(a)
    if label:
        d.rounded_rectangle((6,16,10,43),radius=2,fill=tone)
        x=print_tracking(d,(33,15),label,font(31 if len(label)<18 else 28,610),tone,2.28)
        if x>805: raise ValueError(f'label outside layout {label}')
    for i,line in enumerate(lines):
        d.text((6,68+i*(size-1)),line,font=font(size,700),fill=tone if len(lines)>1 and i==1 else PAPER,anchor='lt')
        if 6+font(size,700).getlength(line)>812: raise ValueError(f'title outside layout {line}')
    m=a.getchannel('A');box=m.getbbox();assert box and box[2]+SAFEX<916 and box[3]+SAFEY<580
    soft=m.filter(ImageFilter.GaussianBlur(4.7)).point(lambda a:round(a*.66));b=Image.new('RGBA',size0,(4,9,9,0));b.putalpha(soft)
    b.alpha_composite(a)
    return b


@lru_cache(maxsize=2)
def tone_curve(cool):
    x=np.arange(256,dtype='f')/255
    val=np.clip((x-.22)*1.102+.220,0,1)
    mid=np.maximum(0.,4*val*(1-val));shadow=(1-val)**2
    if cool:
        a=[val+.012*mid,val+.015*mid+.008*shadow,val+.021*mid+.013*shadow]
    else:
        a=[val+.042*mid,val+.014*mid+.005*shadow,val-.017*mid+.014*shadow]
    return np.rint(np.clip(np.concatenate(a),0,1)*255).astype('B').tolist()


@lru_cache(maxsize=96)
def wash(alpha):
    # Soft print-light only underneath the upper-left editorial area.
    y=np.arange(741,dtype='f'); x=np.linspace(0.,1.,WIDTH)
    v=(np.clip((740-y)/360,0.,1.)**1.62)*np.minimum(1.,(y+136)/313)
    u=1.-.80*np.clip((x-.56)/.44,0,1)**1.2
    mask=np.rint(v[:,None]*u[None,:]*alpha).astype('B');return Image.fromarray(mask)


def titles(im,f):
    a=[]
    for lo,hi,name,ls,tone,sz,g in CUES:
        if not lo<=f<hi:continue
        # A little rise and settle; no repeated karaoke bouncing or cut-to-black.
        o=ease((f-lo+1)/6)*ease((hi-f)/5)
        a.append((o,name,tuple(ls),tone,sz,g))
    if not a:return im
    ap=max(round(255*o*g) for o,_,_,_,_,g in a)
    im.paste((8,13,13),(0,0,WIDTH,741),wash(ap))
    for o,name,ls,tone,sz,_ in a:
        img=layer(name,ls,tone,sz)
        if o<.999:
            m=img.getchannel('A').point(lambda x:round(x*o))
        else:m=img.getchannel('A')
        im.paste(img,(SAFEX,SAFEY+round(12*(1-o))),m)
    return im


def frame_image(raw,native,f,shot):
    raw=Image.frombuffer('RGBA',native,raw,'raw','RGBA',0,-1).convert('RGB')
    return titles(raw.resize(EXPORT,Image.Resampling.LANCZOS).point(tone_curve(shot in {'air_snap','lab_pair','held_shut'})),f)


def still(f,plan=None):
    for s in plan or read_plan():
        if not s['lo']<=f<s['hi']:continue
        n=NATIVE[0]*NATIVE[1]*4
        with (CACHE/'plates'/f"{s['lo']}.rgba").open('rb') as a:
            a.seek((f-s['lo'])*n);b=a.read(n)
        if len(b)!=n:raise ValueError(f'partial plate in preview frame {f}')
        return frame_image(b,NATIVE,f,s['shot'])
    raise ValueError(f'frame outside edit: {f}')


def encode():
    WORK.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    plan=read_plan();h=[(CACHE/'trace'/f"{s['lo']}.build").read_text().strip() for s in plan]
    assert len(set(h))==1,'portrait plates were built on different materials or optics'
    n=NATIVE[0]*NATIVE[1]*4
    for s in plan:
        assert (CACHE/'plates'/f"{s['lo']}.rgba").stat().st_size==n*(s['hi']-s['lo']),s
    p=WORK/'short.pending.mp4';full=WORK/'short.mp4'
    args=[FF,'-y','-nostdin','-hide_banner','-loglevel','warning','-f','rawvideo','-pixel_format','rgb24',
          '-video_size',f'{WIDTH}x{HEIGHT}','-framerate',str(FPS),'-i','pipe:0','-i',str(WORK/'short-mix.wav'),
          '-map','0:v:0','-map','1:a:0','-map_metadata','-1','-filter_threads','1','-vf',
          'scale=iw:ih:flags=accurate_rnd+full_chroma_int:out_color_matrix=bt709:out_range=tv,format=yuv420p,setsar=1',
          '-threads','2','-c:v','libx264','-preset','fast','-crf','17.7','-profile:v','high','-level:v','4.1',
          '-x264-params','keyint=60:min-keyint=15:scenecut=40:aq-mode=3',
          '-color_range','tv','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
          '-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-metadata:s:a:0','language=eng',
          '-metadata','title=Monarch Cam 01A — That Jump Started With a Bite','-video_track_timescale','30000',
          '-movflags','+faststart+write_colr',str(p)]
    with (QA/'encode.log').open('w') as log:
        enc=subprocess.Popen(args,stdin=subprocess.PIPE,stderr=log)
        try:
            assert enc.stdin
            for s in plan:
                with (CACHE/'plates'/f"{s['lo']}.rgba").open('rb') as a:
                    for f in range(s['lo'],s['hi']):
                        b=a.read(n)
                        if len(b)!=n:raise IOError(f'incomplete native plate {f}')
                        enc.stdin.write(frame_image(b,NATIVE,f,s['shot']).tobytes())
                print(f"SHORT_COMPOSITE {s['hi']:04d}/{FRAMES} {s['shot']}",flush=True)
            enc.stdin.close()
            if enc.wait()!=0:raise RuntimeError('FFmpeg composition failed; see encode.log')
        except BaseException:
            enc.kill();enc.wait();raise
    p.replace(full);print('SHORT_ENCODE_READY',full,full.stat().st_size,flush=True)


def main():
    if sha256(FONT.read_bytes()).hexdigest()!=FONT_SHA: raise ValueError('expected pinned Space Grotesk treatment')
    ap=argparse.ArgumentParser();ap.add_argument('--stills');a=ap.parse_args()
    if a.stills:
        QA.mkdir(parents=True,exist_ok=True)
        for f in map(int,a.stills.split(',')):
            still(f).save(QA/f'comp-{f:04d}.jpg',quality=93,subsampling=0)
    else:encode()


if __name__=='__main__':main()
