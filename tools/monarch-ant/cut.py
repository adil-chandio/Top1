"""Frame-accurate review cut: shots annotated against measured locked VO times.

``ends`` are take-master seconds, not script runtime estimates. Positive holds
are inserted into existing clean inter-take gaps. Native 24fps contact/recoil
and failure passages are not optically interpolated.
"""
import argparse
import json
import math
import os
from pathlib import Path

C=Path(os.environ.get('MONARCH_ANT_CACHE','.cache/monarch-cam-ant-film'))
D=Path('.cache/monarch-cam-ant-vo-v1/edit-receipt.json')
F=24
HOLD=[3,3,4,5,4,3,9]
TITLE=['The ground gives way','A trap that moves','The spring inside the head','Follow the contact',
       'A jump is not an escape','Take away the snap','One bite']
# Fields: end (locked take-master sec), asset mode, camera, source clock in/out,
# graphic, extra attenuation. ``None`` ends the take plus its new picture hold.
BEATS=[[
 (3.96,0,10,0,0.61,'reconstruction',0),
 (7.84,1,3,.62,2.12,'reconstruction',0),
 (11.04,3,4,1.97,2.94,'reconstruction',0),
 (15.76,0,0,2.15,3.835,'replay',0),
 (17.37,0,1,3.852,5.68,'reconstruction',0),
 (19.52,6,8,2.22,3.34,'head',0),
 (22.85,0,14,5.71,7.98,'reconstruction',.09),
 (None,8,9,2.83,4.15,'title',.48),
], [
 (26.16,2,2,.70,3.81,'reconstruction',0),
 (28.72,8,16,3.85,5.71,'reconstruction',0),
 (34.96,3,4,.49,1.16,'larva',0),
 (37.66,1,6,.15,1.37,'reconstruction',0),
 (41.54,3,18,2.08,3.11,'reconstruction',0),
 (43.72,2,11,3.09,4.91,'reconstruction',0),
 (50.90,1,3,.48,1.82,'reconstruction',0),
 (55.33,3,4,5.72,6.88,'reconstruction',0),
 (57.78,8,15,6.88,8.00,'reconstruction',0),
 (62.97,3,14,8.09,9.65,'reconstruction',0),
 (65.57,2,11,9.68,11.24,'reconstruction',0),
 (None,1,10,1.48,3.07,'ant',0),
], [
 (77.50,5,5,0,3.65,'head',0),
 (81.66,6,8,.75,2.18,'replay',0),
 (88.04,7,7,.18,2.91,'inside',0),
 (93.02,7,8,2.92,4.17,'inside',0),
 (99.00,7,7,.87,3.20,'elastic',0),
 (108.27,7,8,1.6,3.62,'elastic',0),
 (114.16,6,19,1.6,3.34,'fast',0),
 (118.75,0,1,3.86,5.55,'replay',0),
 (None,2,11,3.32,5.91,'reconstruction',0),
], [
 (124.06,3,18,2.27,3.01,'reconstruction',0),
 (126.88,1,3,1.59,2.20,'reconstruction',0),
 (129.57,1,10,2.20,2.79,'replay',0),
 (134.07,1,17,2.80,3.21,'replay',0),
 (140.13,6,8,2.1,3.64,'free-air',0),
 (143.07,0,0,2.91,3.422,'replay',0),
 (148.48,0,0,3.422,3.552,'replay',0),
 (152.98,0,0,3.552,4.23,'replay',0),
 (156.44,0,1,4.23,5.53,'replay',0),
 (164.52,0,12,3.20,3.89,'replay',0),
 (168.93,9,13,.23,1.52,'reconstruction',0),
 (None,8,14,5.70,7.38,'reconstruction',0),
], [
 (176.94,4,15,2.75,5.37,'failure',0),
 (183.72,4,2,3.41,5.86,'failure',0),
 (189.92,11,14,.70,5.79,'ran',.20),
 (193.24,0,1,3.7,5.56,'jumped',.20),
 (195.52,8,14,6.44,6.78,'caught',.26),
 (202.56,11,10,.90,5.88,'reconstruction',0),
 (209.52,0,14,4.55,7.91,'reconstruction',0),
 (213.56,6,19,.84,2.81,'reconstruction',0),
 (None,12,19,1.18,5.61,'reconstruction',0),
], [
 (221.65,12,7,0,1.51,'restrained',0),
 (228.89,6,19,1.46,3.37,'groups',.20),
 (236.83,11,16,.02,4.25,'handling',.16),
 (243.88,12,8,1.15,4.88,'confound',.12),
 (249.40,6,19,1.78,3.39,'paired',.16),
 (253.82,0,1,3.72,5.60,'results',.20),
 (257.01,4,15,4.13,5.44,'failure',0),
 (None,9,13,.0,2.04,'reconstruction',0),
], [
 (264.11,1,12,.41,1.31,'reprise',0),
 (268.42,0,0,1.40,3.52,'reprise',0),
 (271.27,0,1,3.53,5.72,'reprise',0),
 (276.45,3,18,6.31,6.83,'reconstruction',0),
 (280.73,0,12,3.20,4.29,'reprise',0),
 (284.02,3,4,10.14,11.94,'reconstruction',0),
 (287.29,2,11,2.88,5.21,'reconstruction',0),
 (291.39,0,0,2.46,3.53,'reprise',0),
 (294.98,0,1,3.54,5.87,'reprise',0),
 (297.27,9,13,.41,1.24,'reconstruction',0),
 (None,8,9,7.1,8.41,'end',.50),
]]


def prepare():
    rec=json.loads(D.read_text()); samples=rec['samples']; beats=rec['beats'];sr=rec['sample_rate']
    if sr!=48000 or samples!=13987270 or [i['picture_hold_budget_seconds'] for i in beats]!=HOLD:
        raise ValueError('Cut is not based on the locked narrator asset')
    splices=[0]+[(a['end_sample_exclusive']+b['start_sample'])//2 for a,b in zip(beats,beats[1:])]+[samples]
    timeline=[];events=[];vo=[];chapters=[];offset=0;frame=0
    def add(f0,f1,mode,cam,begin,end,key,dark):
        if f1<=f0: raise ValueError((f0,f1,mode,cam,begin,end,key))
        timeline.append(dict(first=f0,end=f1,mode=mode,cam=cam,src=[begin,end],overlay=key,dark=dark))
        for typ,t,vol in eventlist(mode,cam,key):
            if begin<=t<end:
                time=(f0+(f1-f0-1)*(t-begin)/(end-begin))/F
                events.append([typ,round(time,5),vol])
    for i,shots in enumerate(BEATS):
        v0,v1=splices[i:i+2];vo.append((v0,v1,v0+offset*sr));chapters.append((frame,TITLE[i]))
        final=(v1+sr*(offset+HOLD[i]))/sr
        for cut,mode,cam,begin,end,key,dark in shots:
            # In the finale's coda, its three absolute VO base-clock cuts are
            # beyond the voice line but still inside the explicit 9s picture hold.
            at=round(F*(final if cut is None else cut+offset))
            add(frame,at,mode,cam,begin,end,key,dark);frame=at
        offset+=HOLD[i]
    precredit=frame
    add(frame,frame+144,8,9,8.41,9.82,'sources',.65);frame+=144
    assert offset==31
    meta={'frames':frame,'precredit_frames':precredit,'fps':F,'vo_ranges':vo,'chapters':chapters,'events':sorted(events,key=lambda x:x[1]),'shots':timeline}
    w=C/'work';w.mkdir(exist_ok=True,parents=True)
    (w/'film.json').write_text(json.dumps(meta,indent=2)+'\n')
    with (w/'film.plan').open('w') as f:
        for r in timeline:
            a,b=r['src'];print(r['first'],r['end'],r['mode'],r['cam'],a,b,r['overlay'],r['dark'],file=f)
    keys=sorted(set(r['overlay'] for r in timeline))
    print(f'{len(timeline)} shots · {frame} frames · {frame/F:.3f} s with source card · {len(events)} Foley cues')
    return keys


def eventlist(mode,cam,key):
    if mode in (0,1,4):
        vol=1.0 if key not in {'replay','reprise','failure'} else .81
        a=[('feet',.11,.59),('slide',.60,.70),('feet',1.47,.58),('feet',2.05,.37)]
        if mode in (0,4): a += [('strike',3.42,vol)]
        if mode==0: a += [('land',5.48,.70),('feet',5.67,.44)]
        if mode==4: a += [('fall',4.47,.76),('slide',4.61,.42)]
        return a
    if mode==3:
        return [('flick',x,.77) for x in (.38,1.41,2.56,6.05,8.24,10.5)]
    if mode in (6,7) and key not in {'groups','fast','paired'}:
        return [('openair',3.13,.46)]
    if mode in (2,8) and cam in (2,11,16):
        return [('slide',x,.31) for x in (1.93,4.16,5.18,9.95)]
    if mode in (9,11):return [('feet',x,.54) for x in (.22,1.47,2.41,3.37,4.57,5.27)]
    return []


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('width',type=int);a.add_argument('height',type=int);z=a.parse_args()
    from prepare import assets,make
    names=prepare();assets();make(z.width,z.height,names)
