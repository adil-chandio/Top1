#!/usr/bin/env python3
"""Tactile stereo mix. Every editorial and physical accent has a real sample onset."""
from __future__ import annotations

import json
import math
import wave

import numpy as np
from scipy.ndimage import gaussian_filter1d

from assets import HOME,AUDIO, VO,LOCK, base,media_lock
from cut import B, F, N, S, SPF, SR
import sound as common
from sound import FOL_CREDIT, FOL_LOCK, db_peak, db_rms, env, filter_, modal, pan_stereo, smooth, tbase, add
from finish import Q, int_samples

common.FOL=AUDIO
DIR=HOME/'mix'; BED=DIR/'stereo-bed.wav'; MIX=DIR/'program.wav'; REPORT=DIR/'sound-audit.json'
SAMPLES=LOCK['sample_frames']


def hz(n):return 440*2**((n-69)/12)


class Console:
    def __init__(self,vo):
        self.score=np.zeros((N,2),dtype=np.float32);self.space=np.zeros_like(self.score);self.fx=np.zeros_like(self.score)
        self.vo=vo;self.r=np.random.default_rng(260503231);self.cues=[]

    def noise(self,n,a,b):
        z=filter_(self.r.standard_normal(n,dtype=np.float32),2,a,b)
        return z/max(1e-7,np.sqrt(np.mean(z*z)))

    def soundstage(self,mono,p,diffuse=.20):
        # Equal-power spot, low-level crossfeed and irregular micro reflections.
        # This is stereo placement, not a claim of binaural room measurement.
        clip=pan_stereo(mono,p);src=clip.copy()
        for offset,g in ((31,.30),(1607,.27),(2859,.16),(4467,.14),(8731,.083),(12037,.051)):
            if offset>=len(clip):break
            clip[offset:,0]+=diffuse*g*src[:-offset,1]
            clip[offset:,1]+=diffuse*g*src[:-offset,0]
        return clip

    def gravel(self,i,t,speed=1):
        a=common.foley(i);a=np.interp(np.arange(len(t),dtype=np.float32)*speed,np.arange(len(a)),a,left=0,right=0).astype(np.float32)
        # Take the bright edges off individual grains, not the whole soundtrack.
        return filter_(a,1,96,5450.)

    def scatter(self,t,count,lo,hi,speed=.89,inst=.71):
        x=np.zeros(len(t),dtype=np.float32);j=0
        for at in (.0,*self.r.uniform(.014,inst,size=count-1)):
            k=round(at*SR);n=min(len(t)-k,round(SR*(.14+.045*self.r.random())))
            if n<8:continue
            tt=t[:n];w=self.gravel(('02','07','05','08')[j%4],tt,speed*(.87+.3*self.r.random()));j+=1
            y=self.noise(n,lo,hi);w+=.037*y*np.exp(-tt*17.)
            x[k:k+n]+=w*env(tt,n/SR,.0027,.052)*(.88 if at==0 else self.r.uniform(.06,.27))
        return x

    def make(self,q):
        key=q.sound;s=q.gain;pan=q.pan;p,qf=q.key,q.f
        dur={'glass':.94,'title':1.29,'airchime':1.15,'waterglass':1.02,'droplet':1.12,'mineral':.65,'dry':.53,
             'step':.43,'press':1.16,'peel':1.08,'break':1.62,'granules':1.32,'bristle':1.58,'brook':2.45,'churn':1.52}[key]
        t=tbase(round(dur*SR));n=len(t); tail=env(t,dur,.0033,.245 if dur>.75 else .13)
        tap=(1-np.exp(-t*578))*np.exp(-t*55.5)
        if key in ('glass','airchime','title','waterglass','droplet'):
            root={'glass':62,'airchime':57,'title':50,'waterglass':60,'droplet':55}[key]
            if p.startswith('title-'):root={'title-a':50,'title-b':57,'title-c':65}[p]
            if p=='rocks-answer':root=50
            if p in ('now','gap-returns'):root=62
            if p=='then':root=57
            freq=hz(root); resonance=.15 if key in ('glass','droplet') else .10
            z=.046*modal(t,freq,5.46 if key!='glass' else 9.1,resonance)
            z+=.019*modal(t,freq*.5007,7.6,.18)
            z+=.017*tap*self.noise(n,750,2700)
            if key in ('airchime','title'):
                z+=.011*modal(t,freq*1.336,6.4,.11)+.010*modal(t,174.0,9.1,.16)
                z+=.009*(1-np.exp(-t*13))*np.exp(-t*3.2)*self.noise(n,306,1800)
            if key in ('droplet','waterglass'):
                phase=2*np.pi*(390*t+185*(1-np.exp(-5.8*t))*t)
                z+=.026*np.sin(phase)*np.exp(-t*10.81)+.016*self.noise(n,290,2070)*np.exp(-t*3.93)
                pan=pan+.19*smooth(t/.72)
            elif key=='glass':
                j=round(.173*SR); z[j:]+=.014*modal(t[:n-j],freq*1.50,13.8,.12)*env(t[:n-j],dur-.173,.009,.13)
        elif key in ('mineral','dry','step','break','granules'):
            bankid={'mineral':'05','dry':'07','step':'08','break':'02','granules':'02'}[key]
            amt=.053 if key!='granules' else .048
            grains=(self.scatter(t,12,290,2860,.85,.84) if key in ('break','granules') else self.gravel(bankid,t,.93+pan*.19))
            f0=225+92*pan if key=='mineral' else 128+53*pan if key=='step' else 171+37*pan
            z=amt*grains+.023*modal(t,f0,10.12,.36)+.013*tap*self.noise(n,548,2780)
            if key=='break':z+=.041*modal(t,88.,12.43,.21)+.018*self.noise(n,169,811)*np.exp(-t*8.12)
            if key=='granules':z+=.017*self.noise(n,315,2310)*np.exp(-t*4.7)
        elif key=='press':
            d=2*np.pi*(93.0*t-36.3*t*t)
            z=.124*np.sin(d)*np.exp(-t*9.5)+.047*modal(t,165.2,18.5,.09)
            z+=.030*self.noise(n,153,952)*np.exp(-t*6.9)+.060*self.scatter(t,9,273,2097,.63,.51)
        elif key=='peel':
            base=.67*self.gravel('07',t,.78)+.43*self.gravel('05',t,.92)
            z=.048*base + .022*modal(t,116.7,14.2,.23)+.021*self.noise(n,305,1760)*np.exp(-t*3.21)
            z+=.015*np.sin(t*2131+t*t*186)*np.exp(-t*34)
        elif key=='bristle':
            mod=(.69+.31*np.sin(2*np.pi*t*2.92+.66*np.sin(t*9.17)))
            z=.021*self.noise(n,542,3178)*mod*np.exp(-t*2.17)+.034*self.scatter(t,13,682,2390,1.23,.94)
            z+=.010*modal(t,234.,14.7,.31)
        elif key=='brook':
            wave=(.65+.35*np.sin(t*5.6+.72*np.sin(t*2.48)))
            z=(.024*self.noise(n,416,2560)*wave+.014*self.noise(n,118,802))*env(t,dur,.09,.78)
            z+=.019*modal(t,277.18,8.92,.21)
            pan=pan+.38*smooth(t/1.3)-.16
        elif key=='churn':
            wave=env(t,dur,.144,.41);pan=pan-.36+.72*smooth(t/.82)
            d=2*np.pi*(72*t+31.*t*t-19.86*t**3)
            z=.040*modal(t,107.2,12.1,.13)+.048*np.sin(d)*wave+.024*self.noise(n,210,2180)*(.19+.81*wave)
            z+=.018*modal(t,479.8,12.5,.09)
        else:raise ValueError(key)
        clip=self.soundstage(z*tail*s,pan,.32 if key in ('airchime','title','waterglass','brook') else .19)
        # Preserve spoken edges, but spot the first 140 ms above the local room bed.
        listen=round(.14*SR);v=db_rms(self.vo[q.sample:q.sample+listen]);zdb=db_rms(clip[:listen]);ceiling=-16.25 if key in ('press','churn') else -18.1
        gain=0
        if q.text and v>-43:
            gain=min(6.4,max(1.55,v-17.4-zdb))
        elif key in ('title','glass','break','peel','granules','droplet'):
            gain=2.05
        clip*=10**(min(gain,ceiling-db_peak(clip))/20)
        peak=db_peak(clip)
        fired=np.flatnonzero(np.max(np.abs(clip),axis=1)>10**(-57/20))
        assert len(fired) and fired[0]<SPF,(q,fired[:1])
        add(self.fx,q.sample,clip)
        self.cues.append({'name':p,'frame':qf,'trigger_sample':q.sample,'attack_sample':q.sample+int(fired[0]),'text':q.text,
                          'family':key,'peak_dbfs':round(peak,2),'one_frame_rms_dbfs':round(db_rms(clip[:SPF]),2)})

    def ambience(self):
        settings={
            'grit':(.0100,141,1260,.76),'mud':(.0121,183,1660,.62),'brook':(.0208,129,1944,1.31),
            'globe':(.0126,50,660,.69),'wind':(.0132,161,1810,.31),'studio':(.0072,125,969,.44),
            'glass':(.0099,179,1342,.71),'fault':(.0138,43,610,.48),'water':(.0182,61,1121,.86),
        }
        for k,q in enumerate(S):
            # J and L cuts – water and location air slightly lead some pictures,
            # leaving the graphic and individual material transient on its frame.
            leeway=.34 if q.air in ('brook','wind','water') else .23
            l=max(0,round(q.f*SPF-leeway*SR));r=min(N,round(F[k+1]*SPF+(.55 if q.air in ('brook','water') else .36)*SR))
            t=tbase(r-l);length=(r-l)/SR;lvl,lo,hi,tempo=settings[q.air]
            a=self.noise(len(t),lo,hi);br=self.noise(len(t),max(112,lo*.83),min(3000,hi*1.33));de=self.noise(len(t),max(31,lo*.48),hi*.56)
            wet=(.65+.24*np.sin(2*np.pi*t*tempo+.7*k)+.10*np.sin(2*np.pi*t*.73+.83*k))
            wet2=(.60+.28*np.cos(t*5.11+k*.42)+.10*np.sin(t*3.27))
            motion=(((k%6)-2.5)*.091+.224*np.sin(2*np.pi*t*.125+k*.43))
            shape=env(t,length,.41 if l else .06,.55)
            sample=a*wet+br*(.19+.12*wet2)+.22*de
            if q.air in ('brook','water'):
                # Random closely spaced laminar events, not a looping water file.
                sample=a*wet*.80+br*.36*wet2+.29*de
                for j in range(12):
                    at=self.r.uniform(.10,max(.12,length-.6));i=round(at*SR);m=min(len(t)-i,round(.46*SR));z=t[:m]
                    rip=.27*self.noise(m,325,2290)*env(z,m/SR,.059,.214)
                    sample[i:i+m]+=rip
            clip=self.soundstage(sample*shape*lvl,motion,.23)
            add(self.space,l,clip)

    def music(self):
        # Tuned beds of the same slowly evolving motif, with different
        # instrument envelopes and a resolution specifically under the ending.
        # Cues are scene-direct, not looped or generated narration.
        at=[.04,4.02,11.32,19.08,28.20,36.01,43.74,53.62,61.0,68.20,77.0,85.19,95.09,103.28,113.86,124.44,
            135.,145.18,156.54,168.10,178.83,188.13,198.30,209.89,218.96,231.09,242.39,253.51,264.67,275.70,286.67,
            297.43,308.03,319.68,330.98,342.10,352.46,361.40,370.69,381.58,393.16,401.30,413.16,424.10,435.70]
        harm=[(38,50,57,65),(34,46,53,60),(36,48,55,62),(38,50,57,64),(34,46,57,65),(41,53,57,64),(38,50,55,60),
               (34,46,53,62),(38,50,57,60),(41,53,57,64),(36,48,55,57),(34,46,55,60),(38,50,57,64),(38,50,53,57),
               (46,53,57,60),(48,55,60,67),(41,53,57,62),(38,50,53,57),(36,48,55,59),(41,53,60,64),(34,46,53,60),
               (36,48,55,62),(38,50,57,65),(41,53,57,67),(38,50,57,64),(36,48,55,62),(34,46,57,60),(41,53,60,65),
               (38,50,55,62),(36,48,57,62),(34,46,53,60),(38,50,53,65),(48,55,57,62),(41,53,57,64),(38,50,57,62),
               (34,46,53,65),(36,48,55,62),(38,50,57,64),(41,53,57,62),(34,46,53,60),(36,48,55,62),(38,50,57,65),
               (34,46,53,60),(38,50,57,64),(38,50,57,62)]
        for i,(entrance,notes) in enumerate(zip(at,harm,strict=True)):
            dur=(at[i+1]-entrance+1.48) if i+1<len(at) else N/SR-entrance
            volume=(.020 if i in (3,11,18,23,34,42,43) else .0168)*(.91 if 14<=i<=17 else 1.)
            for j,note in enumerate(notes):
                start=round((entrance+j*.21)*SR);n=min(N-start,round((dur-j*.21)*SR));t=tbase(n);w=2*np.pi*hz(note)*t
                a,b,c=self.r.uniform(0,2*np.pi,3)
                drift=.28*np.sin(t*2.14+a)+.15*np.sin(t*.75+c)
                tone=(np.sin(w+drift+a)+.25*np.sin(2.002*w+.69*drift+b)+.093*np.cos(w*2.997+1.44*drift+c))
                breath=(.87+.085*np.sin(t*1.39+i*.7)+.051*np.cos(t*.69+j*.82));attack=1.4+j*.24
                note=volume*tone*breath*env(t,n/SR,attack,1.53+j*.08)*(.72 if j else 1.)
                add(self.score,start,self.soundstage(note,(-.14,-.57,.51,.13)[j],.21))
            if i%2==0 or i in (3,37,43):
                for j,s in enumerate((1.48,2.87,4.5,6.32)):
                    h=round((entrance+s+.13*(i%3))*SR)
                    if h>=N:continue
                    t=tbase(min(N-h,round(3.40*SR)));note=notes[(j+2)%4]+(12 if ((i+j)%5==3) else 0);w=hz(note)
                    pluck=modal(t,w,1.91+j*.15,.21)+.10*modal(t,w*.503,3.62,.19)
                    p=pluck*env(t,3.40,.022,.63)*(.018 if i in (3,26,43) else .0132)
                    add(self.score,h,self.soundstage(p,(-.35,.18,.24,-.06)[j],.46))


def sample_bytes(s):
    assert np.max(np.abs(s))<Q
    return np.stack((s&255,(s>>8)&255,(s>>16)&255),axis=-1).astype(np.uint8).tobytes()


def wave_out(p):
    w=wave.open(str(p),'wb');w.setnchannels(2);w.setsampwidth(3);w.setframerate(SR);return w


def mix():
    media_lock(); DIR.mkdir(parents=True,exist_ok=True)
    source=int_samples(VO,SAMPLES)[:,0];dry=np.zeros(N,np.int32);dry[:SAMPLES]=source
    del source
    narr=dry.astype(np.float32)/Q
    c=Console(narr)
    for beat in B:c.make(beat)
    c.ambience();c.music()
    vol=np.sqrt(np.mean(narr.reshape(-1,200)**2,axis=1));ctrl=gaussian_filter1d(vol,10.)
    step=SR*4;peak=0.;sums=np.zeros(4,np.float64);fpeak=0.
    score_shape=[(9.92,.21,.37),(19.47,.16,.58),(49.20,.17,.59),(77.63,.23,.75),(124.17,.24,.59),(177.20,.48,.65),
                 (203.45,.32,.66),(313.5,.38,.70),(360.5,.94,.48),(418.1,.63,.50),(422.07,1.15,.87),(431.37,.78,.51)]
    def block(i,j):
        t=np.arange(i,j,dtype=np.float32)/SR
        d=smooth((np.repeat(ctrl[i//200:j//200],200)-.0095)/.109)[:,None]
        duck=np.ones(j-i,dtype=np.float32)
        for onset,span,depth in score_shape:
            if t[-1]<onset-span*3 or t[0]>onset+span*3:continue
            duck*=1-depth*np.exp(-.5*((t-onset)/span)**2)
        end=smooth((N/SR-t)/1.45)[:,None];front=smooth(t/.023)[:,None]
        music=c.score[i:j]*(1-.52*d)*duck[:,None]
        air=c.space[i:j]*(1-.40*d)*(1-.26*(1-duck[:,None]))
        detail=c.fx[i:j]*(1-.20*d)
        return (music+air+detail)*end*front,music,air,detail
    for i in range(0,N,step):
        j=min(N,i+step); bed,music,air,detail=block(i,j)
        peak=max(peak,float(np.max(np.abs(narr[i:j,None]+bed))));fpeak=max(fpeak,float(np.max(np.abs(detail))))
        for z,x in enumerate((bed,music,air,detail)):sums[z]+=np.sum(x*x,dtype=np.float64)
    gain=1. if peak<.83 else .88
    paths=[p.with_suffix('.partial.wav') for p in (BED,MIX)];g=0.
    with wave_out(paths[0]) as bd, wave_out(paths[1]) as mx:
        for i in range(0,N,step):
            j=min(N,i+step); y,_,_,_=block(i,j); d=np.rint(y*(Q*gain)).astype(np.int32)
            m=d+dry[i:j,None];g=max(g,np.max(np.abs(m))/Q);bd.writeframesraw(sample_bytes(d));mx.writeframesraw(sample_bytes(m))
    assert g<.853,(g,peak)
    for p,q in zip(paths,(BED,MIX),strict=True):p.replace(q)
    baselevel=20*math.log10(max(1e-9,math.sqrt(np.mean(narr*narr))))
    levels=10*np.log10(sums/(N*2));info={'voice_sha256':LOCK['files'][0]['sha256'],'unchanged_samples':SAMPLES,'program_samples':N,'static_bed_gain':gain,
        'bed_vs_voice_db':round(float(levels[0]-baselevel+20*np.log10(gain)),3),'bed_loudness_rms_dbfs':round(float(levels[0]),3),
        'score_ambience_fx_rms_dbfs':np.round(levels[1:],3).tolist(),'fx_peak_dbfs':round(20*np.log10(fpeak),3),
        'program_peak_dbfs':round(20*np.log10(g),3),'graphic_sync':sum(bool(b.text) for b in B),'spots':len(B),'first_attacks':c.cues,
        'bed_sha256':base.hashfile(BED),'mix_sha256':base.hashfile(MIX),'foley':FOL_CREDIT,'foley_hashes':FOL_LOCK}
    assert -19<info['bed_vs_voice_db']<-12,(info['bed_vs_voice_db'],levels)
    REPORT.write_text(json.dumps(info,indent=2)+'\n')
    print('MIX_READY',json.dumps({k:v for k,v in info.items() if k not in ('first_attacks','foley_hashes')},indent=2),flush=True)


if __name__=='__main__':mix()
