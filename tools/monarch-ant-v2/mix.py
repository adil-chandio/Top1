"""Render native, sample-spotted Foley and an original score to a stereo film mix."""
from base64 import b64decode
from functools import lru_cache
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import subprocess

import numpy as np
from cut import ROOT, SR, SOURCE
from score import build_score

FF=os.environ.get('FFMPEG','ffmpeg')
VO=Path(os.environ.get('MONARCH_VO_WAV','deliverables/monarch-cam-step-3/Monarch-Cam-Ant-VO-v1.wav'))
A=ROOT/'audio'
W=ROOT/'work'
QA=ROOT/'qa'
LEVEL=10**(-.90/20)  # One scalar only on original narration; no reshaping or stretch.


def ff(*args, data=None):
    p=subprocess.run([FF,'-nostdin','-hide_banner','-xerror',*map(str,args)],input=data,capture_output=True)
    if p.returncode!=0:raise RuntimeError(p.stderr.decode(errors='replace')[-8000:])
    return p


def decode(path,channels=1,af=None,blob=None):
    edit=['-af',af] if af else []
    p=ff('-loglevel','error','-threads','1','-i',path,'-map','0:a:0','-vn',*edit,
         '-ar',SR,'-ac',channels,'-f','f32le','-',data=blob)
    x=np.frombuffer(p.stdout,dtype='<f4').copy()
    return x if channels==1 else x.reshape(-1,channels)


def native_vo():
    assert sha256(VO.read_bytes()).hexdigest()==SOURCE, 'not the locked voice master'
    return decode(VO)


def sinefade(n,secs):
    m=min(n,ns(secs));return np.sin(np.linspace(0,np.pi*.5,m,dtype=np.float32))**2


def envelope(x,a,b):
    r=x.copy();e=sinefade(len(r),a);q=sinefade(len(r),b)
    if len(e):r[:len(e)]*=e
    if len(q):r[-len(q):]*=q[::-1]
    return r


def ns(s):return round(float(s)*SR)


def gain(db):return float(10**(float(db)/20))


def db(r):return float(20*np.log10(max(float(r),1.e-12)))


def rms(x):return float(np.sqrt(np.mean(np.square(x,dtype='float64'))))


def band(x,lo,hi):
    if len(x)<48: return x.copy()
    f=np.fft.rfftfreq(len(x),1./SR)
    h=(1.-np.exp(-np.square(f/lo)))*np.exp(-np.power(f/hi,3.0))
    # The transient is prepared with leading and trailing fades so the FFT
    # filtering does not add circular wraparound to the cut boundaries.
    return np.fft.irfft(np.fft.rfft(x)*h,n=len(x)).astype(np.float32)


def measure(path):
    rc=ff('-threads',1,'-i',path,'-map','0:a:0','-vn','-af','loudnorm=I=-19.5:TP=-2:LRA=8:print_format=json','-f','null','-')
    raw=rc.stderr.decode();j,_=json.JSONDecoder().raw_decode(raw[raw.rfind('{'):]);
    return {k:float(j[v]) for k,v in [('LUFS_I','input_i'),('dBTP','input_tp'),('LRA','input_lra')]}


def wav(x,path):
    assert x.dtype==np.float32 and np.isfinite(x).all()
    ff('-loglevel','error','-f','f32le','-ac',1 if x.ndim==1 else x.shape[1],'-ar',SR,'-i','pipe:0',
       '-c:a','pcm_s24le','-y',path,data=x.tobytes())


class Bus:
    def __init__(self,n):self.y=np.zeros((n,2),dtype=np.float32)
    def add(self,x,start,g=1.,pan=0.):
        l=ns(start);a=max(0,l);b=min(l+len(x),len(self.y))
        if b<=a:return
        s=x[a-l:b-l]*g;p=(float(pan)+1.)*np.pi*.25
        self.y[a:b,0]+=s*np.cos(p);self.y[a:b,1]+=s*np.sin(p)


BANK=re.compile(r'''["']([A-G][#b]?-?\d+)["']\s*:\s*["']data:audio/mp3;base64,([A-Za-z0-9+/=]+)["']''')


@lru_cache(maxsize=3)
def bank(name):
    # Deliberately parse static data; do not execute JS from the download.
    return dict(BANK.findall((A/'instruments'/f'{name}.js').read_text()))


@lru_cache(maxsize=100)
def note(name,key):
    x=decode('pipe:0',blob=b64decode(bank(name)[key],validate=True))
    ix=np.flatnonzero(np.abs(x)>max(.0004,np.max(np.abs(x))*.017))
    if len(ix)==0:raise ValueError((name,key,'empty sample'))
    x=x[max(0,ix[0]-384):]
    hi={'acoustic_grand_piano':1820,'pizzicato_strings':1990,'cello':1460}[name]
    return band(envelope(x,.012,.04),61,hi)


def play(bus,name,key,t,d,level,pan,power):
    x=note(name,key)
    if name=='cello':
        # Lengthen only isolated score samples by crossfading the sustained
        # center. Fade at the written release; no audio stretch on dialogue.
        if len(x)<ns(d):
            a=ns(min(.46,len(x)/SR*.24));b=max(a+ns(.20),len(x)-ns(.30));b=min(b,len(x))
            loop=x[a:b];ov=max(1,min(ns(.18),len(loop)//3)); x=x[:b].copy()
            w=sinefade(ov,ov/SR)
            while len(x)<ns(d):
                x=np.concatenate((x[:-ov],x[-ov:]*(1-w)+loop[:ov]*w,loop[ov:]))
        x=envelope(x[:ns(d)],.62,min(1.03,d*.38))
        cap=.060
    else:
        x=envelope(x[:ns(d)],.023 if name.startswith('acoustic') else .016,min(.32,d*.36));cap=.063
    focus=x[:min(len(x),ns(1.45))] if name!='cello' else x
    amp=gain(level)*power/max(1.e-7,rms(focus));amp=min(amp,cap/(np.max(np.abs(x))+1.e-7))
    bus.add(x,t,amp,pan)
    for delay,echo,side in [(.033,.095,-.32),(.059,.099,.33),(.109,.057,.51),(.157,.032,-.42)]:
        bus.add(x,t+delay,amp*echo,np.clip(pan*.33+side,-.66,.66))


@lru_cache(maxsize=12)
def recording(name):return decode(A/'downloaded'/f'{name}.wav',2)


def excerpt(name,length,speed,lo,hi,seed=0,attack=.008,release=.097):
    a=recording(name);mid=a.mean(axis=1)
    if 'sweep' in name:
        # The downloaded mirror is a 3.29 s excerpt. Use separate localized
        # slices, not the original's sustained paper rasp as a background bed.
        if seed%4==0:u=.164
        elif seed%4==1:u=.762
        elif seed%4==2:u=1.472
        else:u=2.087
        start=ns(u)
    else:
        q=np.max(np.abs(mid));on=np.flatnonzero(np.abs(mid)>=.095*q)
        start=max(0,int(on[0])-ns(.0035)) if on.size else 0
    src=mid[start:min(len(mid),start+ns(length*speed)+2)]
    idx=np.arange(ns(length),dtype=np.float32)*speed
    x=np.interp(idx,np.arange(len(src)),src,right=0.).astype(np.float32)
    x=band(envelope(x,attack,min(release,length*.46)),lo,hi)
    return envelope(x,attack*.61,min(release*.45,length*.34))


LAYER={
 # sample, seconds, HP, LP, level (active onset RMS), offset, attack
 'tarsus':[('step',.153,180,2770,-42.0,0,.009)],
 'loose_sand':[('sand-sweep',.66,166,2430,-40.5,0,.090),('gravel',.16,160,1680,-49.2,.055,.019)],
 'ground_strike':[('snap',.115,135,2200,-32.2,0,.0035),('step',.224,158,2770,-37.6,.012,.021),('sand-sweep',.41,162,2110,-44.8,.040,.043)],
 'grain_release':[('gravel',.147,170,2350,-41.5,.01,.013),('sand-sweep',.382,173,2350,-44.0,.080,.058)],
 'landing':[('step',.25,145,2350,-38.7,0,.010),('gravel',.23,220,2440,-43.5,.045,.019)],
 'wall_clip':[('gravel_05',.238,136,2140,-35.7,0,.006),('sand-step-alt',.27,170,2790,-40.6,.037,.019)],
 'sand_return':[('sand-sweep',.72,167,2290,-43.0,0,.091)],
 'flick':[('sand-step',.18,180,2860,-41.8,0,.013),('gravel',.20,190,2030,-42.9,.06,.032),('sand-sweep',.49,158,2300,-43.8,.077,.079)],
 'air_click':[('snap',.108,234,2440,-37.6,0,.0048)],
 'cambered_click':[('soft-snap',.114,245,2160,-41.2,0,.005)],
}


def foley(bus,meta):
    audit=[];used=set(); rng=np.random.default_rng(20151177)
    for i,event in enumerate(meta['events']):
        t=event['time_s'];name=event['name'];scene=event['scene'];p=event['pan']
        amp=event['level'];r=[]
        for j,(s,d,lo,hi,level,off,a) in enumerate(LAYER[name]):
            if s=='step':s=('sand-step','sand-step-alt','gravel_07','gravel_08')[(i+j)%4]
            if s=='gravel':s=('gravel_02','gravel_05','gravel_07','gravel_08')[(i+j)%4]
            if s=='snap':s=('soft-snap','snap-alt')[(i+j)%2]
            v=float(rng.uniform(.87,1.13));x=excerpt(s,d,v,lo,hi,seed=i+j,attack=a)
            n0=ns(min(d,.120 if 'sweep' not in s else .26))
            amp0=gain(level)*amp/max(1.e-7,rms(x[:n0]));amp0=min(amp0,.094/(np.max(np.abs(x))+1.e-7))
            bus.add(x,t+off,amp0,p*(1-j*.14));r.append(dict(source=s,start=round(t+off,6),end=round(t+off+len(x)/SR,6),speed=round(v,4)))
            used.add(s)
        audit.append(dict(scene=scene,cue=name,film_time=t,recordings=r))
    return audit,sorted(used)


def rms_blocks(x,width):
    return np.sqrt(np.mean(np.square(x[:len(x)//width*width].reshape(-1,width),dtype=np.float64),axis=1))


def peak_duck(x,size=960):
    env=rms_blocks(x,size);z=np.arange(len(env),dtype='float64')
    voice=np.clip((np.log10(np.maximum(env,1.e-6)) +2.43)/.84,0,1)
    ahead=np.maximum.reduce([np.interp(z+u,z,voice,right=0.) for u in (0,2,5,8)])
    # Hold across short breaths, then ease back up over several hundred ms.
    for i in range(1,len(ahead)):ahead[i]=max(ahead[i],ahead[i-1]*.943)
    w=np.hanning(13);return np.convolve(ahead,w/w.sum(),mode='same')


def automation(meta):
    # Additional gain dips around action rather than a louder broadband effect.
    authored={'first_dip_contact_and_recoil':.70,'proof_contact_other_side':.60,
              'grain_ejecta_extreme_macro':.77,'failed_launch_wall_hit_and_fall':.84,
              'one_bite_closing_contact':.68,'snap_in_air_no_external_support':.76}
    nsamp=meta['frames']*(SR//meta['fps']);t=np.arange((nsamp+959)//960,dtype=np.float64)*.02
    curve=np.ones(len(t),dtype=np.float32)
    for s in meta['shots']:
        v=authored.get(s['subject'])
        if v is None:continue
        a=s['first']/meta['fps'];b=s['end']/meta['fps']
        x=np.interp(t,[a-.27,a+.16,b-.12,b+.46],[1,v,v,1],left=1,right=1)
        curve=np.minimum(curve,x).astype(np.float32)
    return curve


def apply_envelope(x,levels,width):
    # Blockwise interpolation avoids pumping and large allocation on a full mix.
    for start in range(0,len(x),width*320):
        y=min(start+width*320,len(x));g=np.interp(np.arange(start,y)/width,np.arange(len(levels)),levels).astype(np.float32)
        x[start:y]*=g[:,None]


def main():
    W.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    m=json.loads((W/'film-v2.json').read_text());frames=m['frames'];n=frames*(SR//m['fps']);v=native_vo()
    voice=np.zeros(n,dtype=np.float32)
    for lo,hi,t in m['vo_ranges']:
        voice[t:t+hi-lo]=v[lo:hi]*LEVEL
    del v
    f=Bus(n);music=Bus(n);tracks=build_score(music,m,play);cues,sources=foley(f,m)
    duck=peak_duck(voice);speed=SR//50;curve=automation(m)
    if len(curve)>len(duck):duck=np.pad(duck,(0,len(curve)-len(duck)),mode='edge')
    music_d=(1.-.62*duck)*curve;fx_d=1.-.24*duck
    apply_envelope(music.y,music_d,speed);apply_envelope(f.y,fx_d,speed)
    # Intro starts in moving sand instead of a full-level chord on frame one.
    # A slow resolved tail stays audible until the final image clears.
    u=sinefade(n,.36);v=sinefade(n,1.16)
    for bus in [f,music]:
        bus.y[:len(u)]*=u[:,None];bus.y[-len(v):]*=v[::-1,None]
    mix=music.y+f.y+voice[:,None]
    assert np.max(np.abs(mix))<.82,'needs headroom; do not squash the narrator'
    for x,p in [(music.y,'score-v2.wav'),(f.y,'foley-v2.wav'),(mix,'mix-v2.wav')]:wav(x,W/p)
    m16=ns(.12);vb=rms_blocks(voice,m16);fb=rms_blocks((f.y[:,0]+f.y[:,1])*.5,m16);sb=rms_blocks((music.y[:,0]+music.y[:,1])*.5,m16)
    mb=rms_blocks((mix[:,0]+mix[:,1])*.5,m16);active=vb>gain(-37.); under=np.hypot(fb,sb)
    relative=20*np.log10(np.maximum(1.e-12,under[active]/vb[active]))
    quiet=(mb<gain(-59.));quiet[:3]=False;quiet[-8:]=False
    groups=[(int(q[0]),int(q[-1])+1) for q in np.split(np.where(quiet)[0],np.where(np.diff(np.where(quiet)[0])>1)[0]+1) if len(q)]
    ledger=dict(voice_gain_db=db(LEVEL),score_cue_count=len(tracks),foley_cue_count=len(cues),recordings=sources,
                dialogue_relative_bed_dB_percentiles={str(k):float(np.percentile(relative,k)) for k in (5,50,90,95,99)},
                near_silent_windows_s=[(a*.12,b*.12) for a,b in groups if b-a>=3],
                premix=measure(W/'mix-v2.wav'),score_after_duck=measure(W/'score-v2.wav'),foley_after_duck=measure(W/'foley-v2.wav'),
                sample_peak_dBFS=db(np.max(np.abs(mix))),samples=n)
    assert ledger['premix']['dBTP']<-2.9 and -21.0<ledger['premix']['LUFS_I']<-18.6
    assert ledger['dialogue_relative_bed_dB_percentiles']['95']<-13.0
    assert all(b-a<.49 for a,b in ledger['near_silent_windows_s']), ledger['near_silent_windows_s']
    path=QA/'v2-audio.json';path.write_text(json.dumps(ledger,indent=2)+'\n')
    (W/'spotting-v2.json').write_text(json.dumps(dict(foley=cues,score=tracks),indent=2)+'\n')
    print(path.read_text(),end='');print('V2_AUDIO_READY')

if __name__=='__main__':main()
