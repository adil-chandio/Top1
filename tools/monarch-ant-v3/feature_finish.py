"""Finish chapter-local composites and preserve the approved opening picture.

A picture-only stream per chapter; continuous 48 kHz mix below. The opener
enters the join as the already approved encoded H.264, not a re-creation.
"""
import argparse
from hashlib import file_digest, sha256
import json
import os
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw
from feature_cut import ANCHORS, FPS, META, NAME, MASTER, QA, WIDTH, HEIGHT, WORK
from feature_titles import compose, plan
from platepack import frames
from pilot import DELIVERY, SPF, TITLE, TOOLS
from mix import FF, ff
from titles import verify_fonts

OPENING = DELIVERY/f'{TITLE}.mp4'
OPENING_SHA = '7bae0cf26ab7711e9f9a17c248fb716c32d1594dd26ab3b718f423f1fae519da'
COLORS = ['-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv']
VUI = 'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0'


def filehash(p):
    with p.open('rb') as q:return file_digest(q,'sha256').hexdigest()


def image(data,w,h):
    return Image.frombytes('RGBA',(w,h),data.tobytes(),'raw','RGBA',0,-1)


def board(fills, out):
    m=json.loads(META.read_text()); picks=sorted(set(fills))
    w,h=480,270;layout=Image.new('RGB',(3*w,(h+27)*((len(picks)+2)//3)),(20,28,25)); d=ImageDraw.Draw(layout)
    j=0
    for s in m['shots']:
        if s['beat']==1 or not any(s['first']<=f<s['end'] for f in picks):continue
        for f,x,y,b in frames(WORK/f"take-{s['first']}.plates"):
            if f not in picks:continue
            a=compose(image(b,x,y),f).convert('RGB').resize((w,h),Image.Resampling.LANCZOS)
            ox,oy=(j%3)*w,(j//3)*(h+27);layout.paste(a,(ox,oy));d.text((ox+9,oy+h+5),f'{f:04}  /  {f/FPS:.2f}s   ·   '+s['subject'].replace('_',' '),fill=(223,226,211));j+=1
    assert j==len(picks),(j,picks)
    layout.save(out,quality=96);print(out)


def fingerprint(s):
    c=sha256()
    for p in (Path(__file__),TOOLS/'feature_titles.py',TOOLS/'titles.py',WORK/'projection.csv'):
        c.update(p.read_bytes())
    c.update(json.dumps(s,sort_keys=True).encode())
    for a in s:
        p=WORK/f"take-{a['first']}.plates";t=p.stat()
        c.update(f'{p.name}:{t.st_mtime_ns}:{t.st_size}'.encode())
    return c.hexdigest()


def encode(ch, force=False):
    assert 2<=ch<=7
    m=json.loads(META.read_text());s=[z for z in m['shots'] if z['beat']==ch]
    lo,hi=ANCHORS[ch-1:ch+1];assert (s[0]['first'],s[-1]['end'])==(lo,hi)
    p=WORK/f'picture-{ch}.mp4'; r=p.with_suffix('.signature');q=p.with_suffix('.pending.mp4')
    pin=fingerprint(s)
    if not force and p.is_file() and r.is_file() and r.read_text().strip()==pin:return p
    # High quality single delivery encode. Smooth but distinct native frames;
    # well-defined limited range conversion, no padding, new cadence, or blur.
    w,h=MASTER;scale=f'scale={w}:{h}:flags=lanczos:in_range=pc:out_range=tv:out_color_matrix=bt709,setsar=1,format=yuv420p'
    args=[FF,'-hide_banner','-nostdin','-xerror','-loglevel','warning','-y','-filter_threads','2',
          '-f','rawvideo','-pixel_format','rgb24','-framerate',str(FPS),'-video_size',f'{WIDTH}x{HEIGHT}','-i','pipe:0',
          '-vf',scale,'-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','17',
          '-maxrate','6200k','-bufsize','12400k','-profile:v','high','-level:v','4.1','-g','60','-keyint_min','15',
          '-pix_fmt','yuv420p','-video_track_timescale','30000',*COLORS,
          '-fps_mode','passthrough','-movflags','+faststart+write_colr',str(q)]
    i=lo
    with subprocess.Popen(args,stdin=subprocess.PIPE) as sub:
        try:
            assert sub.stdin is not None
            for z in s:
                for f,x,y,b in frames(WORK/f"take-{z['first']}.plates"):
                    assert f==i and x==WIDTH and y==HEIGHT
                    im=compose(image(b,x,y),i).convert('RGB')
                    sub.stdin.write(im.tobytes());i+=1
                print(f'V3 composite {ch}: {i-lo}/{hi-lo} · {z["subject"]}',flush=True)
            sub.stdin.close()
            if sub.wait():raise RuntimeError('Chapter encode failed')
        except BaseException:
            sub.kill();raise
    assert i==hi
    q.replace(p);r.write_text(pin+'\n');print(f'FEATURE_PICTURE_CHAPTER_{ch} READY ({p.stat().st_size:,} bytes)',flush=True)
    return p


def mux():
    assert filehash(OPENING)==OPENING_SHA
    m=json.loads(META.read_text()); p=WORK/'picture-1.mp4'
    ff('-loglevel','warning','-y','-i',OPENING,'-map','0:v:0','-c:v','copy','-an','-map_metadata','-1','-map_chapters','-1','-video_track_timescale','30000',p)
    concat=WORK/'feature.ffconcat'; meta=WORK/'feature.ffmetadata'
    concat.write_text('ffconcat version 1.0\n'+''.join(f"file 'picture-{j+1}.mp4'\nduration {(b-a)/FPS:.6f}\n"
                                              for j,(a,b) in enumerate(zip(ANCHORS,ANCHORS[1:]))))
    chapters=('Coming down','The funnel','Two springs','The outside push','Airborne is not out','The comparison','One bite')
    meta.write_text(';FFMETADATA1\ntitle=This Ant Bites the Ground to Escape — V3 Full Cinematic Cut\nartist=Monarch Cam\n'+
                    ''.join(f'[CHAPTER]\nTIMEBASE=1/{FPS}\nSTART={a}\nEND={b}\ntitle={k}\n' for a,b,k in zip(ANCHORS,ANCHORS[1:],chapters)))
    for ch in range(2,8):
        expected=fingerprint([z for z in m['shots'] if z['beat']==ch]); r=WORK/f'picture-{ch}.signature'
        assert r.read_text().strip()==expected,f'stale composites: chapter {ch}'
    p=WORK/f'{NAME}.mp4';q=p.with_suffix('.pending.mp4')
    ff('-loglevel','warning','-y','-f','concat','-safe',1,'-i',concat,'-i',WORK/'feature-mix.wav','-i',meta,
       '-map','0:v:0','-map','1:a:0','-map_metadata','2','-map_chapters','2',
       '-c:v','copy','-bsf:v',VUI,*COLORS,'-video_track_timescale','30000',
       '-af',f'atrim=end_sample={ANCHORS[-1]*SPF}','-c:a','aac','-b:a','224k','-ar','48000','-ac','2','-metadata:s:a:0','language=eng',
       '-movie_timescale','48000','-movflags','+faststart+write_colr',q)
    q.replace(p);print(f'FEATURE_MUX_READY {p} {p.stat().st_size:,} bytes',flush=True);return p


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('chapters',nargs='*',type=int);ap.add_argument('--force',action='store_true');ap.add_argument('--mux',action='store_true')
    ap.add_argument('--board',type=str);ap.add_argument('--out',type=Path,default=QA/'feature-composite.jpg')
    a=ap.parse_args();verify_fonts();plan()
    if a.board:board(list(map(int,a.board.split(','))),a.out);return
    for ch in a.chapters or ([] if a.mux else range(2,8)):encode(ch,a.force)
    if a.mux:mux()


if __name__=='__main__':main()
