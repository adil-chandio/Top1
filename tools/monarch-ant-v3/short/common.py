"""The isolated Shorts clock; the feature timeline is never an output here."""
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = Path(os.environ.get('MONARCH_SHORT_CACHE', '.cache/monarch-ant-short')).resolve()
WORK = CACHE/'work'
QA = CACHE/'qa'
OUT = Path(os.environ.get('MONARCH_SHORT_DELIVERY','deliverables/monarch-cam-step-6-short')).resolve()
NAME = 'Monarch-Cam-01A-Bite-To-Jump-Short'
FPS, FRAMES, SR = 30, 1020, 48000
SPF, SAMPLES = SR//FPS, FRAMES*SR//FPS
NATIVE, EXPORT = (810, 1440), (1080, 1920)
DEFAULT_FONT = Path('.cache/monarch-ant-packaging/fonts/SpaceGrotesk.ttf')
FONT = Path(os.environ.get('MONARCH_SHORT_FONT', DEFAULT_FONT))


def read_plan():
    a=[]
    for row in (HERE/'edit.plan').read_text().splitlines():
        if not row or row.startswith('#'): continue
        lo,hi,mode,cam,t0,t1,shot,*pins=row.split()
        a.append(dict(lo=int(lo),hi=int(hi),mode=int(mode),cam=int(cam),shot=shot,
                      source=[float(t0),float(t1)],pins=[[int(f),float(t)] for f,t in zip(pins[::2],pins[1::2])]))
    if a[0]['lo']!=0 or a[-1]['hi']!=FRAMES or any(x['hi']!=y['lo'] for x,y in zip(a,a[1:])):
        raise ValueError('short editorial clock must cover exactly 1,020 contiguous pictures')
    return a
