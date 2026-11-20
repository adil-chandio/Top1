#!/usr/bin/env python3
"""Build local contact sheets from native plates or composited frames."""
import argparse
from pathlib import Path
import subprocess
import time

from PIL import Image, ImageDraw

from render import CACHE, FIELDS, NATIVE, PROG, F, S, build, parse_mark

# Representative keyframes, intentionally bracketing the physical impacts.
BOARDS=(
 ((0,.4),(1,1.4),(2,3.4),(3,.55),(3,5.5),(4,1.3),(4,5.1),(5,4.4),(6,3.6),
  (12,3),(13,5.7),(14,2),(14,7.7),(15,5.7),(16,4.1),(17,3.6),(18,5),(19,7)),
 ((20,1.7),(20,2.8),(20,4.1),(20,6.7),(20,8.67),(20,9.5),(20,10.58),(21,3.3),(22,5.7),
  (23,4.6),(24,3.9),(27,3.6),(30,4),(30,9.8),(31,6.8),(32,3.95),(36,4.9),(38,4.4)),
 ((39,6.7),(40,1.5),(40,8.7),(41,3.6),(42,2.8),(43,4.6),(44,5.2),(45,4.8),(46,3.7),
  (47,3.7),(48,4.2),(49,.75),(49,4.8),(50,5),(51,3.4),(52,2.3),(52,6.7),(53,4.6)),
 ((54,5.9),(55,.72),(55,2.8),(55,6.7),(55,8.9),(56,3.5),(56,7),(57,2.8),(58,6.3),
  (58,10.6),(59,4.1),(60,2.3),(60,6.7),(60,8.7),(61,4.2),(63,4.5),(64,0),(64,7.2)),
)


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--clean',action='store_true')
    a.add_argument('--boards',type=int,nargs='+',choices=range(1,len(BOARDS)+1),default=range(1,len(BOARDS)+1));a.add_argument('--compile',action='store_true');args=a.parse_args()
    if args.compile:build()
    if not args.clean:
        from graphics import compose
    boards={i:BOARDS[i-1] for i in args.boards}
    o=CACHE/'tests';o.mkdir(exist_ok=True,parents=True)
    stem='plates' if args.clean else 'comp'
    frames=sorted({F[k]+round(a*24) for b in boards.values() for k,a in b});spec=o/f'{stem}-frames.txt';spec.write_text('\n'.join(map(str,frames))+'\n')
    trace=o/f'{stem}-marks.csv';w,h=NATIVE;start=time.monotonic()
    with trace.open('w+') as tf,subprocess.Popen([str(PROG),str(FIELDS),str(w),str(h),'--samples',str(spec),str(trace)],stdout=subprocess.PIPE) as p:
        for f in frames:
            raw=p.stdout.read(w*h*3)
            if len(raw)!=w*h*3:raise RuntimeError(f'Render stopped before {f}')
            row=tf.readline();k,tr=parse_mark(row,f);im=Image.frombytes('RGB',(w,h),raw)
            if not args.clean:im=compose(im,k,f,tr)
            im.save(o/f'{stem}-{f:05}.jpg',quality=94)
        if p.wait()!=0:raise RuntimeError('Native renderer failed')
    for i,board in boards.items():
        iw,ih=400,225;gap=8;sh=Image.new('RGB',(3*(iw+gap)+gap,6*(ih+36)+gap),(15,24,30));a=ImageDraw.Draw(sh)
        for j,(k,t) in enumerate(board):
            r=F[k]+round(t*24);x=gap+(j%3)*(iw+gap);y=gap+(j//3)*(ih+36)
            with Image.open(o/f'{stem}-{r:05}.jpg') as im:sh.paste(im.resize((iw,ih),Image.Resampling.LANCZOS),(x,y))
            a.text((x+8,y+ih+9),f'{k:02}  {S[k].key}   {r/24:06.2f}s',fill=(229,218,190),font_size=17)
        sh.save(o/f'{stem}-{i}.jpg',quality=93)
    print('FRAMING_TESTS_READY',len(frames),round(time.monotonic()-start,2),flush=True)


if __name__=='__main__':main()
