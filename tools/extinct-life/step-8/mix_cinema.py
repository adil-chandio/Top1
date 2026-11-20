#!/usr/bin/env python3
"""Scene-remix on the locked 48 kHz voice; no processing of the dry narration."""
from __future__ import annotations
import argparse
import json
import math
import wave

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import lfilter, sosfilt

from common import CACHE, N, S, F, SR, SPF, BY, VO, media_lock, save_json, sha, reference
import sound_v2 as v2
from film_audio import sample_bytes, wave_out, Q, SAMPLES
from sound import add, db_rms, env, smooth, tbase

DIR = CACHE/'sound'; BED = DIR/'stereo-bed.wav'; MIX = DIR/'program.wav'
FX = DIR/'foreground.wav'; REPORT = DIR/'mix-lock.json'
# These are mix decisions, not synthesized sounds for every graphics animation.
MUTE = frozenset(('title-b','title-c','mayo-type','bank-near','more-bank','gap-spark','scan-side',
    'soft-print-holds','quieter-wet-settle','ocean-pull','branching-riffle','midwater-click','lobed-fin',
    'rocks-answer','close-grain','antique-hold','dated-neighbour','place-other-slab','out-of-the-lab'))
GAIN = {'title-a':-3.,'now':-2.8,'then':-2.6,'old-lock':-5.8,'rewind-scan':-2.3,
    'scan-read':-4.,'photos':-5.,'reconstruction':-2.3,'to-brazil':-4.2,
    'close-earth':-4.3,'rift-down':-3.1,'rift-early':-1.9,'rift-late':-4.0,
    'river-entrance':-3.1,'sousa-current':-2.5,'stamp-down':-.4,'stamp-up':-1.0,
    'test-down':-1.2,'test-up':-.7,'slump':-1.35,'slump-grains':-3.55,'wash-left':-6.8,
    'valley-water':-1.3,'erosion-wash':-1.65,'through-the-water':-3.4,'air-release':-3.3,
    'water-line':-2.8,'gap-returns':-3.3,'gentle-close':-1.6,'credits-on':-3.1}
WATER = {'title','mayo','ripples','drain','wear','sousa-water','banks','fill','valleys','generations','fish','fish-basins'}
PHYSICAL = ('stamp-down','stamp-up','edge-chip','erosion-pop','test-down','test-up','slump','impact-bank',
            'erosion-wash','bury','rift-down','rift-fill','rift-early','rift-late')


def peaking(x, db, hz=3290., width=.83):
    # Broad inverse bell. The lows, stereo fluctuations and water texture stay.
    a = 10**(db/40.); w = 2*math.pi*hz/SR
    c = -2*math.cos(w); s = math.sin(w)/(2*width)
    return lfilter([1+s*a,c,1-s*a],[1+s/a,c,1-s/a],x,axis=0).astype(np.float32)


class CinemaSound(v2.Soundstage):
    def surf(self,d,p,key):
        t=tbase(round(d*SR)); n=len(t)
        if key=='rift-late':
            z=self.bank.field('ocean',n,30.4,78,3700)
            # The sea moves in behind the dry fault, not a splash over the VO.
            pulse=env(t,d,.52,.78)*(.51+.49*smooth(t/1.52))
            return self.spatial(peaking(z,-2.3)*pulse[:,None]*.155,p-.32*smooth(t/2.2),.80)
        if key in ('erosion-wash','valley-water','wash-left','sousa-current','drain','river-entrance','valley-approach'):
            name,at,rr={
              'erosion-wash':('stream',62.7,(132,4200)), 'valley-water':('stream',87.3,(105,4900)),
              'wash-left':('stream',18.9,(167,4140)), 'sousa-current':('stream',57.8,(117,4530)),
              'drain':('river',24.7,(148,4520)), 'river-entrance':('river',9.1,(135,4510)),
              'valley-approach':('stream',85.3,(105,4250))}[key]
            z=peaking(self.bank.field(name,n,at,*rr),-3.4 if key in ('erosion-wash','valley-water') else -2.0)
            mask=env(t,d,.096 if key=='drain' else .15,.52)
            mask*=1-.74*smooth(t/d) if key=='drain' else .65+.35*smooth(t/.54)
            return self.spatial(z*mask[:,None]*.148,p-.12+.29*smooth(t/d),.85)
        return peaking(super().surf(d,p,key),-1.7)

    def build(self,key,kind,pan,seed):
        if key=='sousa-current':
            d=2.55;flow=self.surf(d,pan,key)
            near=self.source('wet1',.56,.79,167,2780)*.30
            return flow+self.arrange(d,[(.032,near,pan+.38)])
        if key in ('test-down','stamp-down','impact-bank'):
            d=1.12; t=tbase(round(d*SR))
            weight=(.208*v2.resonator(t,124,64,10.9,.27)+.069*self.noise(len(t),133,553)*np.exp(-t*9))*env(t,d,.005,.23)
            sand=.38*self.source('sand2',.31,1.12,147,3910)+.29*self.source('hard1',.31,.86,190,3440)
            water=self.source('wet1',.48,.87,155,3120)*.58
            return self.arrange(d,[(0,weight,.02 if key=='test-down' else pan*.40),(0,sand,-.58 if key=='test-down' else pan-.10),
                    (.012,water,.51 if key=='test-down' else pan+.09),(.091,self.crumbs(.34,seed,.29),pan+.14)])
        if key in ('test-up','stamp-up'):
            d=.96; t=tbase(round(d*SR));
            rub=.10*v2.resonator(t,174,71,9.8,.34)*env(t,d,.013,.22)
            wet=self.source('wet2',.60,.78,162,3100)*.60
            film=v2.fixed_time(wet,d)+rub
            return self.arrange(d,[(0,film,.49 if key=='test-up' else pan),(.019,self.source('sand1',.32,.98,220,3720)*.44,-.54)])
        if key=='slump':
            t=tbase(round(1.45*SR));h=env(t,len(t)/SR,.019,.51)
            s=.61*self.crumbs(len(t)/SR,seed,.74,True)+.093*self.noise(len(t),154,1450)*np.exp(-t*3.2)
            return self.place(s*h,.44-.22*smooth(t/.95),.18)
        if key=='rewind-scan':
            t=tbase(round(2.36*SR));air=self.bank.field('wind',len(t),2.13,105,1630).mean(axis=1)
            y=(.63*air+.16*v2.resonator(t,118,64,1.34,.29))*env(t,2.36,.105,.74)
            return self.place(y,-.48+.78*smooth(t/1.34),.45)
        if key=='title-a':return peaking(self.bell(key,1.9,-.14,-.32),-2.6)
        if key=='rift-down' or key=='rift-early':return peaking(super().build(key,kind,pan,seed),-2.1,2920)
        return super().build(key,kind,pan,seed)

    def spot(self,key,kind,when,pan,seed,main=False,text=False,gain=1.):
        if key in MUTE:return
        at=when*SPF
        x=self.build(key,kind,pan,seed); focus=round((.43 if kind in ('churn','surge','brook') else .34)*SR)
        t=tbase(len(x)); x*=env(t,len(x)/SR,.0028,.070)[:,None]
        v=db_rms(self.vox[max(0,at-3500):min(N,at+16500)])
        hero=key in v2.HERO
        d=np.clip(v-(5.6 if hero else 10.8),-28.3 if hero else -35.8,-21.2 if hero else -26.8)
        if key in ('test-down','test-up'):d+=1.45
        if key=='rift-down':d=-23.6
        if not main:d=np.clip(v-11.9,-36.4,-29.2)
        if key=='floodplain-in':d+=2.1
        x*=v2.g(float(d)+GAIN.get(key,0)-db_rms(x[:focus]))*min(1.15,max(.85,gain**.55))
        cap=v2.g(-11.25 if hero else -15.0);x=cap*np.tanh(x/cap)
        onset=np.flatnonzero(np.max(np.abs(x[:SPF]),axis=1)>v2.g(-53.))
        row = dict(name=key,family=kind,frame=when,sample=at,attack_sample=at+int(onset[0]) if len(onset) else None,
                   focus_dbfs=round(db_rms(x[:focus]),3),first_frame_dbfs=round(db_rms(x[:SPF]),3),pan=pan)
        (self.spots if main else self.extras).append(row);add(self.fx,at,x)
        if hero:self.dip(at,.28 if key in PHYSICAL else .64,.77 if kind not in ('brook','surge') else 1.14)

    def spaces(self):
        levels={'brook':-31.5,'water':-34.1,'grit':-39.1,'mud':-37.4,'globe':-41,'wind':-33.6,'studio':-43.2,'glass':-41.4,'fault':-36.8}
        for k,q in enumerate(S):
            wet=q.key in WATER; lead=.49 if wet else .25;tail=.67 if wet else .38
            a=max(0,q.f*SPF-round(lead*SR));z=min(N,F[k+1]*SPF+round(tail*SR)); t=tbase(z-a); n=len(t);d=n/SR
            level=v2.g(levels[q.air]);fade=env(t,d,lead+.10 if a else .047,tail+.09)
            if wet:
                gain={'mayo':-.1,'wear':.25,'valleys':-.06,'sousa-water':.50,'fish':-.45}.get(q.key,0.)
                bed=self.water_ambience(q,n,t,level*v2.g(gain))
                out=peaking(bed,{'wear':-3.85,'valleys':-4.1,'mayo':-2.6,'sousa-water':-3.0,'banks':-2.5}.get(q.key,-1.8))
            elif q.air in ('wind','grit','mud'):
                z=self.bank.field('wind',n,k*1.42+.16,106 if q.air=='wind' else 155,1930)
                pan=-.21+.32*np.sin(.30*t+k*.26)
                out=self.spatial(z,pan,.59)*level
                if q.air=='mud':out+=.29*level*self.spatial(self.bank.field('lake',n,21.11+.72*k,147,2730),-.5*pan,.65)
            elif q.air=='fault':
                z=self.bank.field('shaker',n,k*.54,142,2070).mean(axis=1)
                out=level*self.place(.66*z+.31*self.noise(n,49,242),.19*np.sin(.52*t),.30)
                if q.key=='rift':
                    i=max(0,BY['rift-late'].sample-a); u=tbase(n-i)
                    sea=self.bank.field('ocean',n-i,30.4,89,3440)
                    add(out,i,v2.g(-31.5)*self.spatial(peaking(sea,-2.4),.20-.35*smooth(u/3.3),.89)*env(u,len(u)/SR,.85,.44)[:,None])
            else:
                low,high=(80,660) if q.air=='globe' else (132,1220) if q.air=='studio' else (171,1630)
                x=self.noise(n,low,high)*(.76+.24*np.cos(.41*t+k*.27)**2)
                out=level*self.place(x,.25*np.sin(.32*t+k*.51),.29)
            add(self.amb,a,out*fade[:,None])

    def music(self):
        super().music()
        # Reorchestrate the underlying cue bed as the argument turns. Long
        # bows carry edits; the stamp/rock sounds, not pulses, give those tests pace.
        moments=((47.4,51.1,.44,.67,1.42),(119.8,132.31,.55,1.01,1.18),
                 (173.4,182.75,.26,.56,.90),(210.0,218.60,.20,1.48,1.84),
                 (312.0,319.4,.43,.95,.96),(402.62,410.90,.57,.95,1.43))
        for a,b,drop,up,down in moments:
            i,j=round(a*SR),round(b*SR);t=tbase(j-i)
            weight=env(t,(j-i)/SR,up,down)
            self.score[i:j] *= (1-drop*weight)[:,None]
        # Four unhurried breaths at key scale changes, cut from the pinned
        # struck/bowed instruments. No new stock music, no sequence of UI pips.
        bridges=((18.93,3.25,'bowD',.7937,-.34,-39.8),
                 (208.35,3.81,'bowG',.8909,.29,-40.7),
                 (327.43,3.57,'bowD',.7492,-.24,-39.2),
                 (429.34,3.64,'bowG',.8909,.22,-41.2))
        for at,d,key,speed,pan,level in bridges:
            n=round(d*SR);t=tbase(n);src=self.source(key,d,speed,132,2380)
            src=src*(v2.g(level)/max(1e-6,v2.rms(src)))*env(t,d,.83,1.33)
            add(self.score,round(at*SR),self.place(src,pan,.58))


def render_mix():
    media_lock();reference();DIR.mkdir(parents=True,exist_ok=True)
    old=v2.REPORT
    ro=json.loads(old.read_text())
    archive=json.loads(v2.HERE.joinpath('sound-v2-receipt.json').read_text())
    assert (ro['mix_sha256'],ro['bed_sha256'],ro['fx_sha256'])==(sha(v2.MIX),sha(v2.BED),sha(v2.FX))
    assert all(ro[f'{key}_sha256']==digest for key,digest in archive['mix_stems'].items())
    # The supplied audio + substrate sounds are the same licensed recording bank.
    bank=v2.RecordingBank(v2.sources());dry=np.zeros(N,np.int32)
    with wave.open(str(VO),'rb') as w:
        assert (w.getnframes(),w.getnchannels(),w.getsampwidth(),w.getframerate())==(SAMPLES,1,3,SR)
        dry[:SAMPLES]=v2.i24(w,SAMPLES)[:,0]
    v=dry.astype(np.float32)/Q
    s=CinemaSound(v,bank);s.all_spots();s.spaces();s.music()
    print('SOUND_DESIGN_READY',len(s.spots),len(s.extras),flush=True)
    # Short forward look for syllables, slower release; retain true onset of each contact.
    energy=np.sqrt(np.mean(v.reshape(-1,200)**2,axis=1));ctrl=gaussian_filter1d(energy,9.0)
    ctrl=np.maximum(ctrl,np.r_[ctrl[7:],np.full(7,ctrl[-1],dtype=np.float32)]*.85)
    block=SR*4
    for i in range(0,N,block):
        j=min(i+block,N);t=np.arange(i,j,dtype=np.float32)/SR
        voice=smooth((np.repeat(ctrl[i//200:j//200],200)-.013)/.072)[:,None]
        release=smooth((N/SR-t)/1.42)[:,None]*smooth(t/.014)[:,None]
        room=s.amb[i:j]; room-=v2.tone(room,2200,5200)*voice*.29; room*=1-.18*voice
        music=s.score[i:j];music*= (1-.34*voice)*np.repeat(s.score_duck[i//200:j//200],200)[:,None]
        turn=smooth((t-421.92)/1.10)*(1-smooth((t-426.28)/1.37));music*= 1-.64*turn[:,None]
        fg=s.fx[i:j];fg*= (1-.12*voice)*release
        s.score[i:j]=(music+room)*release+fg
    head=v2.bed_headroom(s.score,v,.791)
    files=[BED,MIX,FX];tmp=[p.with_suffix('.pending.wav') for p in files]
    with wave_out(tmp[0]) as a,wave_out(tmp[1]) as b,wave_out(tmp[2]) as c:
        peak=0;tr=np.linspace(0,1,200,dtype=np.float32);prev=np.r_[head[:1],head[:-1]]
        for i in range(0,N,block):
            j=min(i+block,N);p=prev[i//200:j//200,None];h=head[i//200:j//200,None]
            gain=np.minimum(h,p+(h-p)*tr).reshape(-1,1)
            bed=np.rint(s.score[i:j]*gain*Q).astype(np.int32);sum_=bed+dry[i:j,None]
            fx=np.rint(s.fx[i:j]*gain*Q).astype(np.int32)
            peak=max(peak,int(np.max(np.abs(sum_))));
            a.writeframesraw(sample_bytes(bed));b.writeframesraw(sample_bytes(sum_));c.writeframesraw(sample_bytes(fx))
    for a,b in zip(tmp,files,strict=True):a.replace(b)
    assert peak/Q<.792
    receipt={'voice_sha256':sha(VO),'locked_voice_samples':SAMPLES,'program_samples':N,'mix_sha256':sha(MIX),'bed_sha256':sha(BED),'fx_sha256':sha(FX),
        'prior_mix_sha256':ro['mix_sha256'],'prior_export_loudness':archive['audio']['lufs_i'],
        'used_sources':sorted(bank.used),'muted_cues':[k for k in sorted(MUTE) if k!='midwater-click'],'first_attacks':s.spots,'additional_attacks':s.extras,
        'headroom_min_gain':float(head.min()),'peak_dbfs':20*math.log10(peak/Q)}
    receipt['measurements']=compare_windows()
    bed_energy=0.
    with wave.open(str(BED),'rb') as w:
        for i in range(0,N,SR*6):
            x=v2.i24(w,SR*6).astype(np.float32)/Q
            bed_energy+=np.sum(x*x,dtype=np.float64)
    receipt['bed_vs_voice_db']=float(10*math.log10(bed_energy/(2*N))-db_rms(v))
    receipt.update(unchanged_samples=SAMPLES,static_bed_gain=1.0)
    save_json(REPORT,receipt)
    print('CINEMA_MIX_READY',receipt['peak_dbfs'],receipt['measurements'],flush=True)


def compare_windows():
    windows={'mayo':(36.5,42.25),'erosion':(177.13,180.58),'valley':(334.63,340.95),
             'mud':(124.10,131.40),'fault':(313.57,316.32),'sea_entry':(408.79,409.14),'answer':(423.25,426.80)}
    result={}
    from contextlib import ExitStack
    with ExitStack() as st:
        old,new,v=[st.enter_context(wave.open(str(p),'rb')) for p in (v2.BED,BED,VO)]
        for key,(a,b) in windows.items():
            n=round((b-a)*SR);out=[]
            for w in (old,new,v):
                w.setpos(round(a*SR));x=v2.i24(w,n).astype(np.float32)/Q
                vals=(db_rms(x),db_rms(sosfilt(v2.eq_kernel(2500,5000),x,axis=0)),db_rms(sosfilt(v2.eq_kernel(250,4800),x.mean(axis=1))))
                out.append([round(i,3) for i in vals])
            result[key]={'seconds':[a,b],'dBFS_columns':['stereo_rms','2.5–5 kHz','phone_band_mono_250–4800 Hz'],'previous_overlay':out[0],'new_overlay':out[1],'unchanged_vo':out[2],
                  'upper_mid_difference_dB':round(out[1][1]-out[0][1],3)}
    return result


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--compare-only',action='store_true');x=a.parse_args()
    if x.compare_only: print(compare_windows())
    else:render_mix()
