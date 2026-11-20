"""Every original shot sampled on a shared pupil-sized frame grid."""
from __future__ import annotations
import argparse
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import QA, REF, F, S, BY, FF, reference, save_json
from finish_film import tc

GROUPS = ((0,7),(7,15),(15,24),(24,34),(34,42),(42,52),(52,59),(59,66))
BEATS = ('now','old-lock','then','mayo-type','stamp-down','stamp-up','test-down','test-up','slump',
         'drain','erosion-wash','pollen','rift-down','valley-water','rift-early','rift-late','rocks-answer')


def samples(movie, frames, size=(336,189)):
    w,h = size
    pick = '+'.join(f'eq(n,{i})' for i in frames)
    b = subprocess.check_output([FF,'-v','error','-xerror','-threads','2','-i',str(movie),'-map','0:v:0','-an','-sn','-dn',
        '-filter_threads','1','-vf',f"select='{pick}',scale={w}:{h}:flags=area:in_color_matrix=bt709:out_range=pc,format=rgb24",
        '-fps_mode','passthrough','-c:v','rawvideo','-threads','1','-f','rawvideo','-'],timeout=360)
    if len(b) != len(frames)*w*h*3: raise ValueError(f'Expected {len(frames)} frames at {w}x{h} from {movie}, got {len(b) // (w*h*3)}')
    return dict(zip(frames, np.frombuffer(b,np.uint8).reshape(-1,h,w,3), strict=True))


def board(pics, groups, prefix):
    QA.mkdir(exist_ok=True,parents=True)
    h,w = next(iter(pics.values())).shape[:2]
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
    for k,rows in enumerate(groups,1):
        out = Image.new('RGB',(14+len(rows[0][1])*(w+7),8+len(rows)*(h+26)),(12,17,22))
        d = ImageDraw.Draw(out)
        for j,(label,frames) in enumerate(rows):
            y = 7+j*(h+26)
            for i,f in enumerate(frames):
                x = 8+i*(w+7); out.paste(Image.fromarray(pics[f]),(x,y))
                d.text((x,y+h+3),f'{label if i==0 else ""}  {tc(f)}',font=font,fill=(223,227,218))
        out.save(QA/f'{prefix}-{k:02}.jpg',quality=92)


def review(movie,tag):
    refs = [[(f'{k:02}  {S[k].key}',(F[k]+3,(F[k]+F[k+1])//2,F[k+1]-3)) for k in range(a,b)] for a,b in GROUPS]
    acts = [[(key, tuple(BY[key].f+i for i in (-2,2,11,23))) for key in BEATS[a:a+5]] for a in range(0,len(BEATS),5)]
    all_frames = sorted({f for group in refs+acts for _,frames in group for f in frames})
    p = samples(movie, all_frames)
    board(p, refs, f'{tag}-coverage'); board(p, acts, f'{tag}-action')
    stats = []
    for group in refs:
        for label,frames in group:
            ims = np.stack([p[f] for f in frames]).astype(np.int16)
            a = np.mean(np.abs(np.diff(ims,axis=0)),axis=(1,2,3))
            luma=(ims*np.asarray([.2126,.7152,.0722])).sum(axis=-1)
            stats.append(dict(shot=label,frames=frames,rgb_mae=list(a.round(2)),luma_p10=round(float(np.percentile(luma,10)),2),
                              luma_p90=round(float(np.percentile(luma,90)),2)))
    save_json(QA/f'{tag}-visual.json',dict(samples=len(p),shots=stats))
    print('VISUAL_AUDIT_READY',tag,len(stats),len(p),flush=True)
    return p


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--master');x=a.parse_args()
    if x.master:
        from pathlib import Path
        review(Path(x.master),'master')
    else:
        reference();review(REF,'reference')
