"""Clock for the rebuilt portrait cut. The old promo and feature remain separate."""
import os
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=Path(os.environ.get('MONARCH_SHORT_BASE','.cache/monarch-ant-short')).resolve()
CACHE=Path(os.environ.get('MONARCH_SHORT_V2_CACHE','.cache/monarch-ant-short-v2')).resolve()
WORK= CACHE/'work'
QA= CACHE/'qa'
OUT=Path(os.environ.get('MONARCH_SHORT_V2_DELIVERY','deliverables/monarch-cam-step-6-short-v2')).resolve()
NAME='Monarch-Cam-01A-Bite-To-Jump-Short-V2'
TITLE='This Ant’s Jump Started With a Bite'
NATIVE=(810,1440)
EXPORT=(1080,1920)
FPS,FRAMES,SR = 30,1020,48000
SPF,SAMPLES = SR//FPS, FRAMES*SR//FPS
FONT=Path(os.environ.get('MONARCH_SHORT_FONT','.cache/monarch-ant-packaging/fonts/SpaceGrotesk.ttf')).resolve()
REUSE = {int(k): v for k,v in json.loads((HERE/'reuse.json').read_text()).items()}


def edit():
    a=[]
    for row in (HERE/'edit.plan').read_text().splitlines():
        if not row or row.startswith('#'):continue
        lo,hi,mode,cam,shot,t0,t1,*pins=row.split();lo,hi,mode,cam=map(int,(lo,hi,mode,cam))
        src=REUSE.get(lo)
        a.append(dict(lo=lo,hi=hi,cam=cam,mode=mode,shot=shot,source=src,model=[float(t0),float(t1)],
                      pins=[(int(f),float(t)) for f,t in zip(pins[::2],pins[1::2])]))
    assert a[0]['lo']==0 and a[-1]['hi']==FRAMES and all(x['hi']==y['lo'] for x,y in zip(a,a[1:]))
    assert all(x['hi']-x['lo']>=18 for x in a)
    return a
