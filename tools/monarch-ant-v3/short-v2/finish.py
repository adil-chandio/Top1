"""Phone-oriented grade, picture labels and tightly spotted phrase captions."""
import argparse
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont
from layout import BASE,CACHE,WORK,QA,FONT,EXPORT,NATIVE,FPS,FRAMES,TITLE,edit

FF=os.environ.get('FFMPEG','ffmpeg')
W,H=EXPORT
RAW=NATIVE[0]*NATIVE[1]*4
PAPER='#fff4de';YELLOW='#ffd88f';TEAL='#a9e3cd';ASH='#e4e8dc'
ANCHORS=[(271,392,'01','IN AIR',TEAL),(392,496,'02','ON SAND',YELLOW),
         (620,660,None,'CLEARS THE RIM',TEAL),(696,759,None,'BACK IN THE PIT',YELLOW),
         (759,844,None,'LAB TEST',TEAL),(844,932,None,'GLUE AT THE TIPS',TEAL)]
# Layout within left < 83% and top/mid field. Lower area belongs to the phone UI.
FONT_SHA='acad6de1fc93436f5c0f1f4137751ef04f1aea3063e7036535970ffcfbd79f72'
KEYS={'sliding','antlion','flicks','midair','snap','lift','sand','airborne','clears','rim','wall',
      'right','stranger','glued','shut','out'}


def ease(n):
    n=min(1.,max(0.,n));return n*n*(3.-2.*n)


@lru_cache(maxsize=26)
def font(size,weight):
    a=ImageFont.truetype(str(FONT),size);a.set_variation_by_axes([weight]);return a


@lru_cache(maxsize=2)
def grade_curve(cool):
    x=np.linspace(0,1,256)
    z=np.interp(x,[0,.08,.22,.47,.77,1],[.001,.058,.185,.485,.808,.986])
    hump=np.sin(np.pi*z)**1.35;sh=(1-z)**3
    if cool:
        a=np.concatenate([z+.010*hump,z+.018*hump+.009*sh,z+.030*hump+.015*sh])
    else:
        a=np.concatenate([z+.053*hump,z+.018*hump+.004*sh,z-.018*hump+.009*sh])
    return np.round(np.clip(a,0,1)*255).astype('B').tolist()


@lru_cache(maxsize=8)
def left_wash(a):
    y=np.linspace(0,1,735);x=np.linspace(0,1,W)
    d=np.minimum(1.,(y+.23)*5.)*np.clip((1.-y)*1.77,0,1)**1.50
    f=1.-.78*np.clip((x-.61)/.39,0,1)**1.07
    return Image.fromarray(np.rint(d[:,None]*f[None,:]*a).astype('B'))


@lru_cache(maxsize=20)
def label(stamp,line,color):
    a=Image.new('RGBA',(810,78));d=ImageDraw.Draw(a)
    if stamp:
        d.rounded_rectangle((4,11,75,60),radius=10,fill=(7,20,20,222),outline=(224,242,223,82),width=2)
        d.text((39,35),stamp,font=font(30,658),fill=color,anchor='mm')
        x=91
    else:
        d.rounded_rectangle((3,16,9,55),radius=2,fill=color);x=28
    # Tracking at subtitle scale. Not an interface lookalike or progress meter.
    for c in line:
        d.text((round(x),22),c,font=font(32,685),fill=color,anchor='lt',stroke_width=2,stroke_fill='#0e1716')
        x+=font(32,685).getlength(c)+2.65
    assert x<775
    return a


@lru_cache(maxsize=2)
def card(final=False):
    a=Image.new('RGBA',(815,276));d=ImageDraw.Draw(a)
    cap='MONARCH CAM  /  01A' if final else 'THIS ANT JUMPS'
    x=10
    for ch in cap:
        d.text((round(x),13),ch,font=font(38 if final else 44,660),fill=ASH,anchor='lt',stroke_width=2,stroke_fill='#111716')
        x+=font(38 if final else 44,660).getlength(ch)+3.4
    if not final:
        d.text((5,78),'WITH A BITE.',font=font(103,700),fill=YELLOW,anchor='lt',stroke_width=3,stroke_fill='#171713')
        d.rounded_rectangle((9,192,118,199),radius=3,fill=YELLOW)
    else:
        d.text((5,70),'SAME TRAP.',font=font(80,700),fill=PAPER,anchor='lt',stroke_width=3,stroke_fill='#141814')
        d.text((5,158),'NO SNAP.',font=font(80,700),fill=YELLOW,anchor='lt',stroke_width=3,stroke_fill='#141814')
    x=a.getchannel('A').getbbox();assert 73+x[2]<906 and 224+x[3]<519
    return a


def place(im,b,x,y,alpha=1.):
    m=b.getchannel('A');im.paste(b,(x,y),m if alpha>=.998 else m.point(lambda o:round(o*alpha)))


@lru_cache(maxsize=35)
def captions(text,color):
    h=180; size=59
    txt=text[0].upper()+text[1:];pieces=txt.split();bits=[];line=[];px=0.
    maximum=818
    for x in pieces:
        w=font(size,695).getlength(x+' ')
        if line and px+w>maximum:bits.append(line);line=[];px=0
        line.append(x);px+=w
    if line:bits.append(line)
    assert 1<=len(bits)<=2,(text,bits)
    a=Image.new('RGBA',(846,h));d=ImageDraw.Draw(a);face=font(size,695);seek=0
    for k,row in enumerate(bits):
        s=sum(face.getlength(el+' ') for el in row)-face.getlength(' ')
        x=(846-s)*.5
        # Paint word runs to enable a quiet one-color emphasis within the phrase.
        for el in row:
            key=el.lower().strip('.,?!:;');is_key=key in KEYS and seek==0
            d.text((round(x),13+k*69),el,font=face,fill=color if is_key else PAPER,
                   anchor='lt',stroke_width=4,stroke_fill='#111615')
            x+=face.getlength(el+' ');seek+=is_key
    shadow=a.getchannel('A').filter(ImageFilter.GaussianBlur(5.7)).point(lambda a:round(a*.83))
    b=Image.new('RGBA',a.size,(7,12,12,0));b.putalpha(shadow);b.alpha_composite(a)
    xmin,ymin,xmax,ymax=b.getchannel('A').getbbox();assert 54+xmax<=918 and ymax<163
    return b


class Comp:
    def __init__(self):
        if sha256(FONT.read_bytes()).hexdigest()!=FONT_SHA:raise ValueError('incorrect type asset')
        self.cue=json.loads((WORK/'captions.json').read_text());self.timeline=edit()
    def path(self,s):
        p=s['source']
        return ((BASE/'plates'/f'{p[0]}.rgba',p[1]-p[0]) if p else (CACHE/'plates'/f"{s['lo']}.rgba",0))
    def prep(self):
        for s in self.timeline:
            p,offset=self.path(s);assert p.stat().st_size>=RAW*(offset+s['hi']-s['lo']),s
            if not s['source']:assert p.stat().st_size==RAW*(s['hi']-s['lo']),s
    def frame(self,raw,f,s):
        assert len(raw)==RAW,(s['shot'],f,len(raw))
        cool=s['mode'] in (6,12,15)
        a=Image.frombuffer('RGBA',NATIVE,raw,'raw','RGBA',0,-1).convert('RGB')
        im=a.resize(EXPORT,Image.Resampling.LANCZOS).point(grade_curve(cool))
        im=im.filter(ImageFilter.UnsharpMask(radius=1.18,percent=28,threshold=3))
        clock=(f+.48)/FPS
        if f<61:
            im.paste((8,14,13),(0,0,W,735),left_wash(137));place(im,card(),73,234)
        elif 932<=f<989:
            im.paste((8,14,13),(0,0,W,735),left_wash(175));place(im,card(True),73,223)
        for lo,hi,stamp,line,color in ANCHORS:
            if lo<=f<hi:
                op=ease((f-lo+1)/4)*ease((hi-f)/4)
                place(im,label(stamp,line,color),73,222+round(7*(1-op)),op)
        if f>=61:
            q=next((p for p in self.cue if p['display_start']<=clock<p['display_end']),None)
            if q is not None:
                # Preserve the tarsal or wall impact silhouettes; the paired lab
                # shot has a text lane in the negative space between the pads.
                mid=1000 if 759<=f<844 else (401 if 692<=f<759 else 1225)
                if 61<=f<111:mid=1293
                if 844<=f<932:mid=1250
                a=ease((clock-q['display_start']+.035)*19.)
                place(im,captions(q['text'],TEAL if cool else YELLOW),54,mid+round(7*(1-a)),a)
        return im
    def still(self,f):
        s=next(x for x in self.timeline if x['lo']<=f<x['hi']);p,offset=self.path(s)
        with p.open('rb') as a:
            a.seek((offset+f-s['lo'])*RAW);b=a.read(RAW)
        return self.frame(b,f,s)


def encode(comp):
    comp.prep();a=WORK/'v2.pending.mp4';b=WORK/'short-v2.mp4'
    cmd=[FF,'-nostdin','-hide_banner','-loglevel','warning','-y','-f','rawvideo','-pixel_format','rgb24',
         '-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0','-i',str(WORK/'short-v2-mix.wav'),
         '-map','0:v:0','-map','1:a:0','-map_metadata','-1','-filter_threads','1',
         '-vf','scale=iw:ih:flags=accurate_rnd+full_chroma_int:out_color_matrix=bt709:out_range=tv,format=yuv420p,setsar=1',
         '-c:v','libx264','-preset','fast','-threads','2','-crf','17.65','-profile:v','high','-level:v','4.1',
         '-x264-params','keyint=60:min-keyint=13:scenecut=40:aq-mode=3',
         '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv',
         '-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-metadata:s:a:0','language=eng',
         '-metadata',f'title={TITLE}','-video_track_timescale','30000','-movflags','+faststart+write_colr',str(a)]
    with (QA/'encode.log').open('w') as log:
        p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
        try:
            assert p.stdin
            for s in comp.timeline:
                plate,offset=comp.path(s)
                with plate.open('rb') as fh:
                    fh.seek(RAW*offset)
                    for f in range(s['lo'],s['hi']):p.stdin.write(comp.frame(fh.read(RAW),f,s).tobytes())
                print(f"V2 FINISHED {s['hi']:04d}/{FRAMES} {s['shot']}",flush=True)
            p.stdin.close()
            if p.wait():raise RuntimeError('See Short V2 encode.log')
        except BaseException:
            p.kill();p.wait();raise
    a.replace(b);print(f'SHORT_V2_MP4_READY {b.stat().st_size} bytes',flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stills');a=ap.parse_args();c=Comp()
    if a.stills:
        for f in map(int,a.stills.split(',')):c.still(f).save(QA/f'comp-{f:04d}.jpg',quality=93,subsampling=0)
    else:encode(c)


if __name__=='__main__':main()
