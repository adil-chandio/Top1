#!/usr/bin/env python3
"""Scene-specific score, foreground foley and sound design on the picture clock.

The stereo bed is a separate, ducked bus. It is added to a byte-checked copy
of the locked voice at unity, with no processing on the voice itself.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import butter, sosfilt

from cues import CUTS, CUES, END, FPS, NSAMPLES, SPF, SR
from geometry import CACHE, MATS, base
from motion import FF
from finish import VOICE, Q, int_samples, write24, locked

AUDIO=CACHE/'mix'
MIX=AUDIO/'cinema-mix.wav'
BED=AUDIO/'cinema-bed.wav'
FX=AUDIO/'foreground-fx.wav'
REPORT=AUDIO/'mix-audit.json'
FOL=MATS/'kenney-rpg'
FOL_LOCK={
    '02':'059b4f4dc06729b0e273ef87ea0196780a95fe39b273a20dedd51dc8f2404b59',
    '05':'2fa84e8df921ee9690cc259b5aa7a8205e224df1961dea0481daae827bae7475',
    '07':'58de8e1b118d719e8b8b53ebcd65c6601493d42c73b23674e19bc3c31920b78e',
    '08':'6a778ccb3273ffa632ad5ebb78d1df60decbe268d821da8127b7e13529fcb640',
}
FOL_CREDIT='RPG Audio gravel foley by Kenney Vleugels, Kenney.nl, CC0 1.0. Four checksum-pinned one-shots, filtered and layered. All other audio is original synthesis.'


def tbase(n):return np.arange(n,dtype=np.float32)/SR


def smooth(q):
    q=np.clip(q,0.,1.); return q*q*(3-2*q)


def env(t,d,atk=.006,rel=.20):return smooth(t/atk)*smooth((d-t)/rel)


def db_rms(x):return float(20*np.log10(max(1e-12,np.sqrt(np.mean(np.square(x.astype(np.float64)))))))


def db_peak(x):return float(20*np.log10(max(1e-12,np.max(np.abs(x)))))


def hz(n):return 440.*2**((n-69.)/12.)


def pan_stereo(x,p):
    v=(np.clip(p,-1,1)+1)*np.pi/4
    return np.stack((x*np.cos(v),x*np.sin(v)),axis=1).astype(np.float32)


def add(buf,k,x):
    j=max(0,int(k)); z=min(len(buf),int(k)+len(x))
    if j<z:buf[j:z]+=x[j-int(k):z-int(k)]


def filter_(a,n,low,high):
    kind,wn=('bandpass',(low,high)) if low>0 else ('lowpass',high)
    return sosfilt(butter(n,wn,fs=SR,btype=kind,output='sos'),a).astype(np.float32)


def modal(t,f,decay,brightness=.44):
    p=2*np.pi*f*t
    return (np.sin(p)*np.exp(-t*decay)+brightness*np.sin(p*1.996+.27)*np.exp(-t*(decay*1.90))
            +.21*np.sin(p*2.546-.3)*np.exp(-t*(decay*2.71))+.084*np.cos(p*4.13)*np.exp(-t*(decay*3.8)))


@lru_cache(maxsize=6)
def foley(number):
    p=FOL/f'gravel_{number}.wav';assert base.hashfile(p)==FOL_LOCK[number],p
    raw=subprocess.check_output([FF,'-hide_banner','-loglevel','error','-nostdin','-i',str(p),'-ac','1','-ar',str(SR),'-f','f32le','-c:a','pcm_f32le','-'])
    a=np.frombuffer(raw,dtype='<f4').astype(np.float32)
    act=np.flatnonzero(np.abs(a)>.010*np.max(np.abs(a)))
    a=a[max(0,int(act[0])-90):min(len(a),int(act[-1])+960)]
    return a/max(1e-7,np.max(np.abs(a)))


class Console:
    def __init__(self):
        self.scores=np.zeros((NSAMPLES,2),np.float32);self.air=np.zeros_like(self.scores);self.fx=np.zeros_like(self.scores)
        self.r=np.random.default_rng(4192073);self.cues=[]

    def rnd(self,n,lo,hi):
        x=filter_(self.r.standard_normal(n,dtype=np.float32),2,lo,hi)
        return x/max(1e-7,np.sqrt(np.mean(x*x)))

    def grit(self,number,speed,t,d):
        a=foley(number);u=np.arange(len(t),dtype=np.float32)*speed
        x=np.interp(u,np.arange(len(a)),a,left=0.,right=0.).astype(np.float32)
        return env(t,d,.0018,.068) * x

    def tail(self,clip,amount=.13):
        a=clip.copy()
        for d,w in ((1319,.42),(3591,.27),(6331,.16),(8435,.13),(11057,.069)):
            if len(a)>d:
                a[d:,0]+=w*amount*clip[:-d,1]
                a[d:,1]+=w*amount*clip[:-d,0]
        return a

    def sound(self,c,vox):
        name=c.voice; go=c.strength
        duration={'grain-bed':1.55,'rock-type':.51,'cut-gravel':.42,'air-approach':1.23,'orbit-mark':.88,'point':.45,
                  'old-point':.47,'measure':.79,'old-measure':.74,'suction':.58,'rewind':1.26,'arrival':1.05,
                  'title-bed':1.57,'lift':.70,'resolve':.98,'layer':.49,'water-open':1.38,'water-type':.73,
                  'count':.58,'old-count':.52,'impact':1.10,'peel':.98,'step':.39}[name]
        t=tbase(round(duration*SR)); span=env(t,duration,rel=.21 if duration>.62 else .119)
        tick=(1-np.exp(-t*480.))*np.exp(-t*31.)
        p=c.pan
        d=c.move/FPS
        if name=='grain-bed':
            w=.031*modal(t,71.,6.) + .011*self.rnd(len(t),165,1880)*np.exp(-3.2*t) + .042*self.grit('02',.85,t,duration)
        elif name in ('rock-type','cut-gravel','layer'):
            bank='05' if name=='rock-type' else ('02' if name=='cut-gravel' else ('07' if c.id in ('layer-1','layer-3') else '08'))
            f=251+74*p if name=='rock-type' else 143+96*p
            grain=self.grit(bank,1.10+p*.19,t,duration)
            w=.048*grain+.018*modal(t,f,8.1)+.018*tick*self.rnd(len(t),510,2670)
            if name=='layer':w+=.017*modal(t,92.0+(p+.1)*74,12.3)
            if name=='cut-gravel':w+=.028*modal(t,80.0,18.);p+=.05
        elif name in ('orbit-mark','point','old-point'):
            # Brief metal-on-glass ping under the sweep of the location pointer.
            f=(548 if name=='point' else 450 if name=='old-point' else 293)+179*p
            w=(.040*modal(t,f,15 if name!='orbit-mark' else 6.5,.26)+.021*tick*self.rnd(len(t),1040,2650))
            if name=='orbit-mark':w+=.012*modal(t,92.,9.7)+.008*self.rnd(len(t),473,3020)*np.exp(-t*5.8)
        elif name in ('measure','old-measure','count','old-count'):
            # The signature is a clean front edge then a much smaller lock component.
            f=(286 if name.startswith('old') else 359)+(62 if 'count' in name else 0)
            w=(.040*modal(t,f,8.4,.39)+.017*modal(t,128.7 if 'count' in name else 169,16.7))
            w+=.021*tick*self.rnd(len(t),562,2580)
            for j,v in enumerate((.26,.51,.78)):
                if j>0 and 'count' in name:continue
                u=t-d*v;r=np.maximum(0.,u);a=(u>=0)*env(r,.10,.003,.078)
                w+=a*(.017-.0029*j)*modal(r,f*(1.12+.09*j),22.,.33)
            if 'count' in name:w+=.028*self.grit('07',1.32,t,duration)
        elif name in ('air-approach','suction'):
            rising=smooth(t/(duration*.69));p=p+(.6 if name=='suction' else .44)*rising
            rush=self.rnd(len(t),100,2000)*(.29+.69*rising)+.35*self.rnd(len(t),71,365)
            fr=2*np.pi*t*(62+63*rising)
            w=(.025*rush+.019*np.sin(fr))*rising
        elif name=='rewind':
            shape=smooth(t/.16)*smooth((duration-t)/.31)
            # Bass, an airy ascending layer, and fine grains across the stereo field.
            p=p-.52+.97*smooth(t/.81)
            phase=2*np.pi*(48*t+61*t*t-17*t**3)
            w=.051*modal(t,92,10.,.13)+.041*np.sin(phase)*shape
            w+=.024*self.rnd(len(t),260,2520)*(.17+.83*shape)
            w+=.021*modal(t,590,15.2,.29)
        elif name in ('arrival','title-bed'):
            f=72 if name=='title-bed' else 86
            w=.057*modal(t,f,4.8,.16)+.031*modal(t,173.4 if name=='title-bed' else 293.66,6.3,.26)
            w+=.010*self.rnd(len(t),510,2690)*exp_decay(t,4.54)
            w+=.014*self.rnd(len(t),133,760)*exp_decay(t,3.1)
        elif name in ('lift','resolve'):
            note={'title-one':50,'title-two':53,'title-three':57,'sequence':62}.get(c.id,57)
            w=.045*modal(t,hz(note),4.8,.38)
            w+=.023*self.rnd(len(t),600,2950)*tick+.009*np.sin(2*np.pi*t*(112+177*t))*np.exp(-t*7)
            if name=='resolve':w+=.017*modal(t,hz(note+12),5.,.24)+.015*modal(t,92.2,5.86)
        elif name in ('water-open','water-type'):
            sweep=.63+.37*np.sin(4.1+np.pi*2*.81*t)
            fizz=self.rnd(len(t),374,2180)*sweep+.46*self.rnd(len(t),78,542)
            w=(.022*fizz+.021*modal(t,166.7,10.61))*exp_decay(t,1.63)
            if name=='water-type':w+=.031*modal(t,396.,9.56,.27)
        elif name=='impact':
            # Two audible layers near contact and a quieter granular settling tail.
            base=np.sin(2*np.pi*(89.2*t-35.7*t*t))*exp_decay(t,9.6)
            chest=np.sin(2*np.pi*(157.2*t-73.2*t*t)+.2)*np.exp(-t*16.7)
            mud=self.rnd(len(t),142,844)*(.73+.27*np.cos(t*43.2))*np.exp(-t*7.1)
            gravel=self.grit('02',.64,t,duration)*.91+self.grit('05',.85,t,duration)*.38
            w=.113*base+.044*chest+.028*mud+.078*gravel
            for j,delay in enumerate((.062,.131,.219,.302)):
                i=round(delay*SR);q=t[:len(t)-i]
                w[i:]+=(.017-j*.0027)*self.grit(('02','07','08','05')[j],1.+j*.19,q,.19)
        elif name=='peel':
            airy=self.rnd(len(t),306,1840)*env(t,duration,.015,.23)
            mineral=self.grit('05',.79,t,duration)+self.grit('08',1.13,t,duration)*.40
            w=.051*mineral+.023*airy*np.exp(-t*3.33)+.029*modal(t,114,12.1,.14)
        elif name=='step':
            i=int(c.id[-1]);w=.033*modal(t,159.0+i*13.6,18.7,.38)
            w+=.038*self.grit(('02','05','07','08')[i%4],1.13+i*.034,t,duration)+.011*tick*self.rnd(len(t),950,2500)
        else:raise ValueError(name)
        x=pan_stereo(go*np.clip(w*span,-.225,.225),p);x=self.tail(x,.14 if 'point' in name or 'lift'==name else .08)
        # Spot in the transient against the *local* voice level. Protect quiet
        # moments, but don't bury a type cue under the stressed next syllable.
        mix_spot_db=0.
        if c.show:
            n=round(.14*SR); v=db_rms(vox[c.sample:c.sample+n]); fx=db_rms(x[:n]);
            aim=(v-18.7)-fx if v>-41. else 0.
            mix_spot_db=min(5.6,max(1.4,aim),max(0.,-17.3-db_peak(x)))
        elif name in ('impact','peel','cut-gravel'):
            mix_spot_db=min(1.3,max(0.,-17.35-db_peak(x)))
        x*=10**(mix_spot_db/20.)
        # The actual generated signal, not merely a cue-sheet annotation.
        mono=np.max(np.abs(x),axis=1);on=np.flatnonzero(mono>10**(-57/20))
        start=int(on[0]) if len(on) else None
        if c.show or name in ('impact','peel','rewind'):
            assert start is not None and start<SPF,(c.id,start)
        add(self.fx,c.sample,x)
        self.cues.append({'id':c.id,'fx':name,'picture_frame':c.frame,'trigger_sample':c.sample,
                          'signal_first_above_minus57_dbfs':None if start is None else c.sample+start,
                          'onset_samples_after_trigger':start,'first_frame_rms_dbfs':round(db_rms(x[:SPF]),2),
                          'isolated_peak_dbfs':round(db_peak(x),2),'spot_gain_db':round(mix_spot_db,2),'graphic_cue':c.show})

    def music(self):
        # D minor with delayed fourths and added seconds, played as soft bowed
        # partials with an independent felt-mallet motif. One composed arc, not a loop.
        beds=[(.06,4.41,(38,50,57),.017,1.60),(3.97,6.39,(34,46,53,60),.019,1.46),
              (10.88,8.97,(36,48,55,62),.020,1.00),(18.92,8.10,(38,50,53,57,64),.024,1.24),
              (25.66,7.65,(34,46,53,57),.017,1.23),(31.94,5.47,(36,48,55,60),.016,1.61),
              (36.19,9.15,(41,53,57,65),.019,1.37),(43.45,6.39,(38,50,55,60),.016,1.12),
              (49.53,5.50,(34,46,53,57),.014,1.28),(53.66,7.40,(38,50,57,62),.019,1.68)]
        for at,d,notes,lvl,attack in beds:
            N=min(NSAMPLES-round(at*SR),round(d*SR));t=tbase(N)
            for i,n in enumerate(notes):
                off=i*.065;u=np.maximum(0,t-off);ph=2*np.pi*hz(n)*u
                a=self.r.uniform(0,2*np.pi,size=3);shape=env(u,d-off,attack+i*.11,1.10+i*.153)
                swell=.84+.11*np.sin(t*1.47+a[0])+.05*np.sin(t*2.91+a[1])
                harm=np.sin(ph+.32*np.sin(2.11*t+a[1])+a[0])+.32*np.sin(ph*2.003+.58*np.sin(1.21*t)+a[2])+.095*np.cos(ph*2.999-a[1])
                w=lvl*shape*swell*harm*(.79 if i else .97)
                add(self.scores,round(at*SR),pan_stereo(w,(-.07,-.45,.51,-.27,.23)[i]))
        notes=[(.61,62,.016,-.4),(2.91,57,.018,.37),(4.56,65,.017,-.24),(6.87,69,.015,.27),
               (11.79,64,.021,.41),(13.43,62,.016,-.36),(16.48,57,.023,.08),
               (19.71,62,.019,-.35),(20.19,65,.023,.37),(20.91,69,.020,.07),(22.39,74,.014,.34),
               (26.82,65,.014,-.30),(28.59,62,.019,.33),(33.37,60,.016,-.28),(36.72,65,.021,.25),
               (38.59,69,.016,-.31),(40.58,72,.013,.37),(43.59,62,.015,-.34),(46.59,60,.012,.09),
               (50.91,57,.018,.25),(52.93,62,.015,-.27),(56.72,65,.018,.30),(57.68,62,.015,-.33),
               (58.72,57,.017,.22),(59.71,50,.013,.10)]
        for at,n,lvl,p in notes:
            t=tbase(min(round(3.75*SR),NSAMPLES-round(at*SR)))
            warm=modal(t,hz(n),1.85,.27)*env(t,3.75,.016,.68)
            add(self.scores,round(at*SR),self.tail(pan_stereo(warm*lvl,p),.43))
        dry=self.scores.copy()
        for i,w in ((3401,.098),(6983,.075),(11793,.050),(18629,.033),(25619,.017)):
            self.scores[i:,0]+=w*dry[:-i,1];self.scores[i:,1]+=w*dry[:-i,0]

    def atmosphere(self):
        beds=[(0.,4.10,.0072,124,1470,.38,.45,-.10,'dry'),(3.77,6.85,.0102,59,613,.77,.72,.07,'deep'),
              (10.79,8.81,.0087,74,836,.61,.82,.11,'deep'),(19.23,7.42,.0143,140,2240,.63,.94,.22,'water'),
              (25.96,6.46,.0087,111,740,.63,.71,-.11,'deep'),(31.80,4.35,.0084,170,1331,.39,.58,-.17,'dry'),
              (36.01,7.49,.0184,128,1882,.41,.67,.14,'water'),(43.15,5.34,.0086,149,1520,.57,.47,-.10,'dry'),
              (48.04,4.83,.0089,163,1464,.36,.50,.03,'dry'),(52.45,8.26,.0081,143,1717,.56,.75,-.07,'dry')]
        for at,d,lvl,lo,hi,attack,release,p,kind in beds:
            t=tbase(min(round(d*SR),NSAMPLES-round(at*SR)))
            mid=self.rnd(len(t),lo,hi);trans=self.rnd(len(t),max(123,lo*.8),min(3200,hi*1.54));rel=self.rnd(len(t),lo*.75,hi*.83)
            flow=(.68+.20*np.sin(2*np.pi*.79*t)+.11*np.sin(2*np.pi*1.37*t+.82))
            if kind=='water':
                # Streams are diffuse, and individual lapping waves have a slower decorrelated channel.
                pulse=(.66+.34*np.sin(t*5.61+1.32*np.sin(t*1.56)))
                mid=mid*.77*flow+trans*.40*pulse
                lvl*=1.16
            else:mid=(.72*mid+.20*trans)*flow
            mono=mid*lvl*env(t,d,attack,release)
            stereo=pan_stereo(mono,p)
            band=lvl*env(t,d,attack+.08,release)*(.42+.58*flow)
            stereo[:,0]+=rel*band*.31
            delay=min(263,len(t)//8)
            if delay:stereo[delay:,1]+=band[delay:]*trans[:-delay]*.31
            add(self.air,round(at*SR),stereo)


def exp_decay(t,r):return np.exp(-r*t)


def audio():
    lock=locked();voice=int_samples(VOICE,NSAMPLES)
    assert voice.shape==(NSAMPLES,1)
    dry=(voice.astype(np.float32)/Q)[:,0]
    c=Console()
    for q in CUTS:c.sound(q,dry)
    c.music();c.atmosphere()
    RMS=np.sqrt(np.mean(dry.reshape(-1,200)**2,axis=1))
    control=np.repeat(gaussian_filter1d(RMS,9.),200)
    active=smooth((control-.009)/.113)[:,None]
    score=c.scores*(1-.46*active);air=c.air*(1-.38*active);fx=c.fx*(1-.19*active)
    t=tbase(NSAMPLES);tail=env(t,END,.014,.54).reshape(-1,1)
    bed=(score+air+fx)*tail
    # Keep headroom by reducing only the other buses in the unlikely event of an overload.
    # This is a gain cap, not a limiter on narration. Most frames are at exactly 1.0.
    tests=np.maximum(np.abs(dry[:,None]+bed),1e-8)
    pk=float(np.max(tests));gain=1. if pk<.846 else .92
    bed*=gain;fx*=tail*gain
    i=np.round(bed*Q).astype(np.int32); mixed=i+voice
    assert np.max(np.abs(mixed))/Q<.88
    AUDIO.mkdir(parents=True,exist_ok=True)
    write24(BED,i);write24(MIX,mixed);write24(FX,np.round(fx*Q).astype(np.int32))
    old_mix_db=[db_rms(bed[:,j])-db_rms(dry) for j in range(2)]
    assert min(old_mix_db)>-21,(old_mix_db,db_peak(fx))
    assert -20<db_peak(fx)<-9,(db_peak(fx),db_rms(fx))
    assert min(d['first_frame_rms_dbfs'] for d in c.cues if d['graphic_cue'])>-48
    path={'voice_sha256':lock['files'][0]['sha256'],'duration_seconds':END,'samples_48k':NSAMPLES,'voice_added_at_sample':0,
          'voice_trimmed_to_sentence_boundary_only':True,'vox_unity_no_dsp':True,'fx_cue_basis':'One authoritative frame grid. Graphic and matching sound share a trigger sample on that frame.',
          'cue_rows':c.cues,'graphic_fx_cues':sum(d['graphic_cue'] for d in c.cues),'total_spotted_cues':len(c.cues),
          'bed_minus_voice_rms_db':[round(v,3) for v in old_mix_db],
          'score_rms_dbfs':round(db_rms(score*tail),3),'ambience_rms_dbfs':round(db_rms(air*tail),3),
          'foreground_fx_rms_dbfs':round(db_rms(fx),3),'foreground_fx_peak_dbfs':round(db_peak(fx),3),
          'mix_peak_dbfs':round(db_peak(mixed/Q),3),'bed_peak_cap_static_gain':gain,'foley':FOL_CREDIT,'foley_sha256':FOL_LOCK,
          'mix_sha256':base.hashfile(MIX),'bed_sha256':base.hashfile(BED),'fx_sha256':base.hashfile(FX)}
    REPORT.write_text(json.dumps(path,indent=2)+'\n')
    print('MIX_READY',json.dumps({k:v for k,v in path.items() if k not in ('cue_rows','foley_sha256')},indent=2))
    return path


if __name__=='__main__':audio()
