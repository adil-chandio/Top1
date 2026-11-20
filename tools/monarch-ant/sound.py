"""Original procedural Foley, sample-locked VO editing, and stereo review mix.

SFX are designed, not insect recordings. No VO resynthesis, EQ, compression,
or time warping. Mix-level gain and silence insertions are measured separately.
"""
from functools import lru_cache
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import subprocess
import wave

import numpy as np

SR = 48000
VO_SHA = '4a3d3c596005cee1f077cc24c0b3a8e55ae9c29614b1f4ed77d119fd5fbf5929'
CACHE = Path(os.environ.get('MONARCH_ANT_CACHE', '.cache/monarch-cam-ant-film'))
VO = Path('deliverables/monarch-cam-step-3/Monarch-Cam-Ant-VO-v1.wav')
FF = os.environ.get('FFMPEG', 'ffmpeg')

def samples(t):
    return round(t*SR)


def db(a):
    return 20*math.log10(max(1.e-14,a))


def fade(n, attack, release):
    e = np.ones(n, dtype=np.float32)
    for k, in_edge in [(max(0,min(n,samples(attack))), True), (max(0,min(n,samples(release))), False)]:
        if k:
            r=.5-.5*np.cos(np.linspace(0,np.pi,k,dtype='float32'))
            if in_edge: e[:k]*=r
            else: e[-k:]*=r[::-1]
    return e


@lru_cache(maxsize=64)
def band(n, lo, hi):
    f=np.fft.rfftfreq(n,1/SR)
    return ((1-np.exp(-np.square(f/lo)))*np.exp(-np.power(f/hi,2))).astype('float32')


def noise(r,n,lo,hi):
    x=r.standard_normal(n,dtype='float32')
    y=np.fft.irfft(np.fft.rfft(x)*band(n,lo,hi), n).astype('float32')
    return y/(np.sqrt(np.mean(y*y))+1e-12)


class Bus:
    def __init__(self,T,seed):
        self.T=T; self.r=np.random.default_rng(seed); self.y=np.zeros((samples(T),2),dtype='float32')

    def place(self,x,t,amp=1,pan=0):
        n=len(x); l=samples(t); h=min(l+n,len(self.y)); j=max(0,l)
        if h<=j: return
        x=x[j-l:h-l]*amp
        # Pan values never hard-left/right; no ping-pong transients in headphones.
        th=(np.asarray(pan)+1)*np.pi*.25
        if th.ndim: th=th[j-l:h-l]
        self.y[j:h,0]+=x*np.cos(th)
        self.y[j:h,1]+=x*np.sin(th)

    def ambience(self,amp=.014):
        # Overlap-add independent broad, gently shaped air layers (no obvious loop).
        # Per-band bandwidth and softness chosen to leave the speech band open.
        for i in range(math.ceil(self.T/9)+1):
            d=12.; n=samples(d);t=i*9.-1.;u=np.arange(n,dtype=np.float32)/SR
            envelop=fade(n,2.1,2.1)*(.72+.20*np.cos(2*np.pi*(u/17+i*.49)))
            a=noise(self.r,n,123,525)+.32*noise(self.r,n,175,1590)
            self.place(a*envelop,t,amp*self.r.uniform(.74,1.10),.14*np.sin(u*.22+i))
            a=noise(self.r,n,240,1050)
            self.place(a*envelop,t,amp*.31,self.r.uniform(-.51,-.19))

    def grain(self,t,d=1.,a=.036,pan=.06,kind='sand'):
        n=max(240,samples(d));u=np.arange(n,dtype=np.float32)/SR
        # A broad brush of rubbing sand, plus dozens of discrete smoothed grit ticks.
        base=noise(self.r,n,260,2100)*(.69+.13*np.sin(u*13))
        env=fade(n,min(.105,d*.23),min(.22,d*.53))*np.exp(-u*(1.4 if kind=='spray' else .42)/d)
        self.place(base*env,t,a,pan+.10*np.sin(u/d*np.pi))
        count=max(5,int(81*d))
        for _ in range(count):
            x=self.r.uniform(.005,d);lt=self.r.uniform(.016,.048);nn=samples(lt); v=np.arange(nn,dtype=np.float32)/SR
            env=fade(nn,min(.004,lt*.25),lt*.58)*np.exp(-v*52)
            track=noise(self.r,nn,370,2400+self.r.uniform(-440,520))
            f=self.r.uniform(525,1210)
            rind=(.22*np.sin(2*np.pi*f*v)+track)*env
            self.place(rind,t+x,a*self.r.uniform(.12,.43)*(1-.7*x/d),np.clip(pan+self.r.uniform(-.29,.29),-.63,.63))

    def tick(self,t,pan,amount):
        n=samples(.085);u=np.arange(n,dtype=np.float32)/SR
        sound=(.58*noise(self.r,n,220,1580)+.31*np.sin(u*2*np.pi*328))*np.exp(-48*u)*fade(n,.007,.018)
        self.place(sound,t,amount,pan)

    def snap(self,t,pan=.26,amount=.088,grounded=True):
        n=samples(.208);u=np.arange(n,dtype=np.float32)/SR
        color=.43*np.sin(u*2*np.pi*447)+.19*np.sin(u*2*np.pi*824)+.11*np.sin(u*2*np.pi*1387)
        body=color*np.exp(-u*44)*fade(n,.004,.025)
        friction=noise(self.r,n,370,2380)*np.exp(-u*61)*fade(n,.007,.027)
        self.place((body+.61*friction),t,amount,pan)
        if grounded:
            self.grain(t+.020,.71,amount*.41,pan-.05,'spray')
            self.tick(t+.082,pan-.07,amount*.21)

    def event(self,kind,t,amp=1):
        if kind=='strike': self.snap(t,.23,.089*amp)
        elif kind=='openair': self.snap(t,0,.057*amp,False)
        elif kind=='slide': self.grain(t,1.27,.044*amp,.02)
        elif kind=='flick':
            self.tick(t,-.24,.017*amp)
            self.grain(t+.025,.72,.043*amp,-.23,'spray')
        elif kind=='fall':
            self.tick(t,.12,.050*amp)
            self.grain(t+.023,1.24,.042*amp,.10,'spray')
        elif kind=='land':
            self.tick(t,-.25,.052*amp)
            self.grain(t+.033,.61,.030*amp,-.21)
        elif kind=='feet':
            for i in range(6): self.tick(t+i*.12,-.19+.10*np.sin(i*1.4),.016*amp*self.r.uniform(.73,1.24))
        else: raise ValueError(kind)


def loudness(a):
    ff=[FF,'-hide_banner','-nostdin','-nostats','-f','f32le','-ar',str(SR),'-ac','2','-i','pipe:0',
        '-af','loudnorm=I=-18:TP=-2:LRA=11:print_format=json','-f','null','-']
    p=subprocess.run(ff,input=np.asarray(a,dtype='<f4').tobytes(),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True)
    s=p.stderr.decode(errors='replace');value,_=json.JSONDecoder().raw_decode(s[s.rfind('{'):])
    return {'LUFS_I':float(value['input_i']),'dBTP':float(value['input_tp']),'LRA':float(value['input_lra'])}


def write(path, y):
    i=np.rint(np.clip(y,-.99999988,.99999988)*8388608.).astype('<i4')
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(3);w.setframerate(SR)
        w.writeframes(i.view(np.uint8).reshape(-1,4)[:,:3].tobytes())


def read_locked():
    sha=hashlib.sha256(VO.read_bytes()).hexdigest()
    if sha!=VO_SHA: raise ValueError('Batch 3 locked WAV checksum mismatch')
    with wave.open(str(VO),'rb') as r:
        if (r.getframerate(),r.getnchannels(),r.getsampwidth(),r.getnframes())!=(SR,1,3,13987270):
            raise ValueError('unexpected Batch 3 WAV format')
        b=np.frombuffer(r.readframes(r.getnframes()),dtype=np.uint8).reshape(-1,3).astype(np.int32)
    return ((b[:,0] | b[:,1]<<8 | b[:,2]<<16)<<8).astype(np.float32)/float(1<<31)


def proof(out,stats):
    T=193/24; bus=Bus(T,0x8de0333);bus.ambience(.014)
    for kind,t,amp in [('feet',.09,.92),('slide',.65,.78),('flick',1.41,.91),('feet',1.87,.65),('flick',2.56,.38),
                       ('strike',82/24,1.),('land',5.48,.92),('feet',5.68,.55),('feet',6.78,.35)]:
        bus.event(kind,t,amp)
    env=fade(len(bus.y),.060,.57)
    # Silence, then natural short reaction. No pre-lift cue.
    u=np.arange(len(env),dtype=np.float32)/SR
    env*=1-.50*np.exp(-((u-3.14)/.27)**2)
    y=bus.y*env[:,None];pre=loudness(y)
    gain=min(-21.5-pre['LUFS_I'],-2.7-pre['dBTP']); y*=10**(gain/20)
    check=loudness(y);write(out,y)
    stats.write_text(json.dumps({'proof':check,'sample_peak_dBFS':db(np.max(abs(y))),
        'duration_s':T,'gain_dB':gain,'jaw_contact_frame':82,'jaw_foley_s':82/24,
        'note':'Designed stereo Foley; no live insect recordings, score or narration.'},indent=2)+'\n')
    print(stats.read_text(),end='')


def film(out,stats,timing):
    z=json.loads(timing.read_text()); T=z['frames']/24; bus=Bus(T,0x514930b);bus.ambience(.009)
    for kind,t,amp in z['events']: bus.event(kind,t,amp*1.58)
    v0=read_locked();v=np.zeros(samples(T), dtype=np.float32);blocks=[];written=0
    for a,b,at in z['vo_ranges']:
        v[at:at+b-a]=v0[a:b];blocks.append((a,b,at));written+=b-a
        if not np.array_equal(v[at:at+b-a],v0[a:b]): raise ValueError('Sample placement failure')
    if written!=len(v0) or blocks[0][0]!=0 or blocks[-1][1]!=len(v0) or any(b!=c for (_,b,_),(c,_,_) in zip(blocks,blocks[1:])):
        raise ValueError('The picture edit must include all locked VO samples once, in order')
    # Sidechain envelope gently suppresses grit/air around spoken phrases. Unrelated
    # picture holds stay quiet, with no constant score or artificial sub impacts.
    n=960;d=np.pad(v,(0,(-len(v))%n)).reshape(-1,n);rms=np.sqrt(np.mean(d*d,axis=1));ctrl=np.clip((rms-.005)/.065,0,1)
    g=np.empty_like(ctrl);gain=0.
    for i,k in enumerate(ctrl):
        gain+=(k-gain)*(.6 if k>gain else .092);g[i]=gain
    x=np.arange(len(v),dtype='float32')/n
    env=np.interp(x,np.arange(len(g),dtype='float32'),g).astype('float32')
    bed=bus.y*(1-.61*env[:,None]);bed*=fade(len(v),.095,1.25)[:,None]
    y=v[:,None]+bed
    pre=loudness(y)
    gain=min(-19.-pre['LUFS_I'],-2.1-pre['dBTP']);y*=10**(gain/20)
    check=loudness(y);write(out,y)
    vals={'mix':check,'sample_peak_dBFS':db(np.max(abs(y))), 'gain_dB':gain,'duration_s':T,
          'retained_VO_samples':written,'VO_sha256':VO_SHA,'VO_placement':'No time stretch or word edits. Preserved source samples with silence insertions and a single mix gain.',
          'Foley_rms_dBFS':db(np.sqrt(np.mean(bed*bed))),
          'VO_rms_dBFS':db(np.sqrt(np.mean(v*v))),
          'note':'Designed Foley, no score and no live insect sounds. Technical metrics are not a substitute for headphone preference.'}
    stats.write_text(json.dumps(vals,indent=2)+'\n');print(stats.read_text(),end='')


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('kind',choices=['proof','film']);p.add_argument('out',type=Path);p.add_argument('stats',type=Path);p.add_argument('--timing',type=Path);a=p.parse_args()
    if a.kind=='proof': proof(a.out,a.stats)
    else: film(a.out,a.stats,a.timing)
