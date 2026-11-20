#!/usr/bin/env python3
"""Full-film sound redesign: foreground material Foley, moving water and a lighter score.

This builds a new mix only. The locked narration is added as integer PCM at
unity; the source video, subtitle track and timings are handled separately.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from urllib.parse import quote
import json
import math
import subprocess
import wave

import numpy as np
from scipy.ndimage import gaussian_filter1d, minimum_filter1d
from scipy.signal import butter, sosfilt

from assets import HOME, HERE, VO, LOCK, base, media_lock
from cut import B, BY, F, INDEX, N, S, SPF, SR, frame
from film_audio import Q, SAMPLES, sample_bytes, wave_out
from motion import FF
from sound import add, db_peak, db_rms, env, pan_stereo, smooth, tbase

DIR=HOME/'sound-v2'; LIB=DIR/'sources'; BED=DIR/'stereo-bed.wav'; MIX=DIR/'program.wav'
FX=DIR/'foreground.wav'; REPORT=DIR/'sound-audit.json'
SOURCE_LOCK=HERE/'sound-v2-sources.json'
OLD_BED=HOME/'mix'/'stereo-bed.wav'
OLD_BED_SHA='06af63e094a89d5d1037863924e3d2f5310e8fd76c4945427ef5f4376e27f648'
PLAN={
 'opening grit':(.00,3.65), 'distance reveal':(6.14,7.13), 'map rewind':(9.93,11.93),
 'title movement':(19.56,21.41), 'Mayo Rey stream':(36.50,42.25), 'first mud contact and peel':(49.25,51.10),
 'six separate local steps':(56.75,58.88), 'fracture and crumble':(77.65,80.60),
 'camera and mesh':(85.17,92.65), 'firm vs wet press':(124.10,125.30), 'mud lift and collapse':(128.80,131.40),
 'draining apron':(169.19,172.75), 'shallow water returning':(177.13,180.58),
 'burying sand':(203.45,206.40), 'Sousa bank':(219.44,222.50), 'fault drop':(313.57,316.32),
 'valley stream':(334.63,340.95), 'underwater pass':(360.20,365.23), 'rift then incoming sea':(404.30,411.98),
 'end resolution':(429.86,441.10),
}
HERO={'now','rewind-scan','old-lock','then','title-a','title-b','title-c','mayo-type','stamp-down','stamp-up','edge-chip',
      'erosion-pop','erosion-tail','photos','reconstruction','length','test-down','test-up','slump','drain','impact-bank',
      'erosion-wash','bury','seal','sousa-current','rift-down','rift-fill','valley-water','mawsonia','rift-early','rift-late',
      'gap-returns','rocks-answer','gentle-close'}


def g(db):return 10**(db/20.)


def i24(w,n):
    p=np.frombuffer(w.readframes(n),dtype=np.uint8).reshape(-1,w.getnchannels(),3).astype(np.int32)
    return p[:,:,0]+(p[:,:,1]<<8)+((p[:,:,2]-256*(p[:,:,2]>=128))<<16)


def sources():
    rows=json.loads(SOURCE_LOCK.read_text());LIB.mkdir(parents=True,exist_ok=True)
    def check(a):
        p=LIB/a['file']
        if p.is_file() and p.stat().st_size==a['bytes'] and base.hashfile(p)==a['sha256']:return
        got=subprocess.check_output(['gh','api','-H','Accept: application/vnd.github.raw+json',
               f"repos/{a['repo']}/contents/{quote(a['path'])}?ref={a['commit']}"],timeout=50)
        t=p.with_suffix(p.suffix+'.pending');t.write_bytes(got)
        assert t.stat().st_size==a['bytes'] and base.hashfile(t)==a['sha256'],a['file'];t.replace(p)
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(check,rows))
    assert len({r['key'] for r in rows})==len(rows)
    return {r['key']:r for r in rows if r['license']!='reference'}


@lru_cache(maxsize=80)
def eq_kernel(lo,hi,order=2):
    if not lo:return butter(order,hi,btype='lowpass',fs=SR,output='sos')
    return butter(order,(lo,hi),btype='bandpass',fs=SR,output='sos')


def tone(x,lo,hi,order=2):return sosfilt(eq_kernel(lo,hi,order),x,axis=0).astype(np.float32)


def rms(x):return float(np.sqrt(np.mean(x*x,dtype=np.float64)))


def norm(x):return x/max(1e-8,rms(x))


def resonator(t,f0,f1,fall,partial=.18):
    p=2*np.pi*(f1*t+(f0-f1)*(-np.expm1(-11*t))/11)
    return np.exp(-fall*t)*(np.sin(p)+partial*np.sin(p*1.83+.18)*np.exp(-10*t))


def fixed_time(x,d):
    n=round(d*SR)
    if len(x)>=n:return x[:n].copy()
    y=np.zeros((n,*x.shape[1:]),np.float32);y[:len(x)]=x;return y


def comp(x,n=.58,curve=.7):
    # Smooth transient rounding. Used only on individual source/FX clips.
    peak=max(float(np.max(np.abs(x))),1e-8);y=x/peak
    return np.tanh(y*(1+curve))/np.tanh(1+curve)*n


class RecordingBank:
    def __init__(self,rows):self.rows=rows;self.loaded={};self.used=set()

    def read(self,key):
        self.used.add(key)
        if key not in self.loaded:
            p=LIB/self.rows[key]['file']
            a=subprocess.check_output([FF,'-v','error','-nostdin','-i',str(p),'-ac','2','-ar',str(SR),'-f','f32le','-c:a','pcm_f32le','-'],timeout=35)
            self.loaded[key]=np.frombuffer(a,'<f4').reshape(-1,2)
        return self.loaded[key]

    @lru_cache(maxsize=40)
    def active(self,key):
        a=self.read(key).mean(axis=1,dtype=np.float32)
        # Trim leading silence from transient, not attack: a 2 ms pre-roll.
        gate=np.flatnonzero(np.abs(a)>np.max(np.abs(a))*(.060 if key not in ('plop1','plop3','splash') else .028))
        assert len(gate),key
        start=max(0,int(gate[0])-96)
        if key=='wet1':start+=960
        elif key=='wet2':start+=1920
        # Only the first splash/contact from longer multi-hit recordings.
        limit={'wet1':.58,'wet2':.54,'plop1':.66,'plop3':.64,'splash':.93,'bowD':6.8,'bowG':7.0}.get(key,10.5)
        return a[start:start+round(SR*limit)].copy()

    def one(self,key,d,rate=1.,lo=95,hi=4300,flip=False):
        a=self.active(key)
        if flip:a=a[::-1]
        t=tbase(round(SR*d));idx=np.arange(len(t),dtype=np.float32)*rate
        v=np.interp(idx,np.arange(len(a),dtype=np.float32),a,left=0,right=0).astype(np.float32)
        return tone(v,lo,hi)*env(t,d,.0019,min(.072,d*.30))

    def field(self,key,n,offset,lo,hi,reverse=False):
        a=self.read(key);assert len(a)>=n,(key,n,len(a))
        start=round(offset*SR)%max(1,len(a)-n)
        b=a[start:start+n]
        if reverse:b=b[::-1]
        b=tone(b,lo,hi)
        return norm(b)


class Soundstage:
    def __init__(self,vox,bank):
        self.vox=vox; self.bank=bank
        self.fx=np.zeros((N,2),np.float32);self.amb=np.zeros_like(self.fx);self.score=np.zeros_like(self.fx)
        self.r=np.random.default_rng(64492730);self.spots=[];self.extras=[]
        self.score_duck=np.ones(N//200,np.float32)

    def noise(self,n,lo,hi):return norm(tone(self.r.standard_normal(n,dtype=np.float32),lo,hi))

    def place(self,x,p,diffuse=.22):
        # A near object with a centred low body, plus a broad, non-inverted
        # early reflection. The dry voice never goes through this panner.
        low=tone(x,0,157);near=pan_stereo(x-low,p)+pan_stereo(low,np.asarray(p)*.18)
        y=near.copy()
        for delay,w in ((1111,.26),(2039,.18),(3751,.19),(5989,.14),(7879,.085),(11263,.051)):
            if delay>=len(y):break
            y[delay:]+=near[:-delay,::-1]*(diffuse*w)
        return y

    def spatial(self,z,p,width=.83):
        mid=z.mean(axis=1);side=(z[:,0]-z[:,1])*.5
        width=min(width,.94);a=self.place(mid,p,.09)
        # Preserve the recorded stereo rather than fake a fully decorrelated bed.
        a[:,0]+=.72*width*side;a[:,1]-=.72*width*side
        return a

    def source(self,key,d,speed=1.,lo=90,hi=4100):
        return comp(self.bank.one(key,d,speed,lo,hi),n=.55,curve=.46)

    def arrange(self,d,components):
        t=tbase(round(d*SR));out=np.zeros((len(t),2),np.float32)
        for a,x,p in components:
            add(out,round(a*SR),self.place(x,p,.19))
        return out

    def crumbs(self,d,seed,amount=1.,slow=False):
        # One main chip, then a decelerating string of smaller impacts. Recorded
        # sand and cabasa/ocean drum give different densities to the tail.
        t=tbase(round(d*SR));x=np.zeros(len(t),np.float32)
        shift=[.0,.073,.167,.269,.418,.626,.864,1.13,1.46,1.82]
        names=('pour','gravel2','pour2','sand2','gravel1','stone3','sand1')
        for j,k in enumerate(shift):
            start=round((k*(1.22 if slow else 1.))*SR)
            if start>=len(t):break
            key=names[(j+seed)%len(names)]
            frag=self.source(key,min(.30,d-start/SR),.76+.32*self.r.random(),130,3850+700*self.r.random())
            amount0=(.63 if j==0 else (.38 if j<4 else .31))*math.exp(-j*.092)
            add(x,start,frag*amount0)
        if slow and d+0.5<20:
            grit=self.bank.field('shaker',len(t),4.14+seed*.52,155,2600).mean(axis=1)
            x+=.065*env(t,d,.17,.35)*grit*(.78+.22*np.sin(t*9.7+.5))
        return x*amount

    def wet(self,d,p,variant,amount=1.):
        t=tbase(round(d*SR));n=len(t);a='wet1' if variant%2==0 else 'wet2'
        press=self.source(a,min(.72,d),.76+(variant%4)*.087,103,4200)
        roll=.17*resonator(t,164,76,13.1,.26)*env(t,d,.007,.24)
        bubble=.068*self.noise(n,250,1410)*np.exp(-t*6.7)*env(t,d,.019,.21)
        out=self.place((roll+.084*fixed_time(press,d)+bubble)*amount,p,.22)
        add(out,0,self.place(press*.586*amount,p+.09,.18))
        for j,at in enumerate((.115,.282,.47)):
            if at>=d-.05:continue
            q=self.source('tap' if j==1 else ('plop1' if variant%2 else 'plop3'),min(.31,d-at),.82+.18*j,142,3580)
            add(out,round(SR*at),self.place(q*amount*(.19-j*.025),p+.17-j*.10,.24))
        return out

    def colour(self,d,key,sw=0.):
        t=tbase(round(d*SR));n=len(t)
        lo,hi=94,2300
        a=self.noise(n,lo,hi);b=self.noise(n,481,4900)
        k=.39+.61*smooth((t-.021)/.30)
        shimmer=.068*b*(.32+.68*smooth(t/.28))
        breath=(.151*a*(.64+.36*np.sin(t*6.3+.8))+shimmer)*k*(1-.79*smooth(t/d))
        if key=='close-earth':
            root=83;end=51
        else:root=170+sw*80;end=63+sw*48
        return (breath+.133*resonator(t,root,end,2.8,.255)+.045*resonator(t,2.37*root,1.69*end,5.8))*env(t,d,.017,.27)

    def bell(self,key,d,p,mode=.0):
        note,rate={'now':('vibeD',1.00),'then':('vibeD',.74915),'gap-returns':('vibeD',.94387),'old-lock':('vibeE',1.33484),
             'title-a':('vibeE',.89090),'title-b':('vibeD',.74915),'title-c':('vibeD',1.),'rocks-answer':('vibeE',.89090),
             'mawsonia':('vibeD',.66742),'old-surface':('vibeA',.7071),'cement':('vibeD',1.12246),
             'age':('vibeA',.74915),'pollen':('vibeD',1.25992),'restore-model':('vibeA',.66742),
             'better-dates':('vibeD',1.33484),'range':('vibeD',.89090),'gap-spark':('vibeA',.668),
             'credits-on':('vibeE',.89090)}.get(key,('vibeD',.945+mode*.13))
        z=self.source(note,d,rate,87,3250)
        knock=self.source(('stone3','hard2','stone2')[int(7*abs(mode))%3],min(.22,d),1.04+mode*.15,330,4460)
        out=self.place(z,p,.43);add(out,0,self.place(knock*.18,p*.95,.17))
        if key in ('now','then','gap-returns','old-lock','photos') and d>.68:
            add(out,round(.224*SR),self.place(self.source('stone3',.17,1.19,392,4150)*.18,-p*.91+.43,.21))
            add(out,round(.47*SR),self.place(self.source(note,min(.48,d-.47),rate*1.5,180,2760)*.074,p*.31,.27))
        if key=='mawsonia':
            add(out,round(.16*SR),self.place(self.source('plop3',.52,.86,138,2800)*.20,p-.23,.73))
        return out

    def surf(self,d,p,key):
        t=tbase(round(d*SR));n=len(t)
        if key=='rift-late':
            src=self.bank.field('ocean',n,16.2,72,3450);rat=.18+.82*smooth(t/.71)
        elif key in ('drain','wash-left'):
            src=self.bank.field('river',n,24.8,164,5400);rat=.96-.72*smooth(t/d)
        elif key in ('valley-water','sousa-current'):
            src=self.bank.field('stream',n,62.8+(key=='valley-water')*33.,121,5240);rat=.32+.68*smooth(t/.45)
        else:
            src=self.bank.field('river',n,3.7,115,4900);rat=.30+.70*smooth(t/.44)
        plan=p+.48*smooth(t/d)-.27
        x=self.spatial(src*env(t,d,.015,.42)[:,None]*rat[:,None]*.168,plan,.91)
        spl='splash' if key in ('erosion-wash','rift-late') else 'wet2' if key=='drain' else 'skip'
        add(x,0,self.place(self.source(spl,min(.78,d),.91,138,5100)*.60,p,.27))
        for j,sec in enumerate((.39,1.05,1.88)):
            if sec>d-.16:continue
            y=self.source('plop1' if j%2 else 'plop3',min(.58,d-sec),.87+j*.13,190,3640)
            add(x,round(sec*SR),self.place(y*.29*(1-.18*j),p+.31-j*.17,.25))
        return x

    def fault(self,key,pan,seed):
        # A crack at opening, then the two faces drag across one another before
        # the lower block settles. The rub and small falls live above the sub
        # thump, so the action is legible on a phone, not just on a woofer.
        wide=key=='rift-early';d=3.14 if wide else 2.69
        t=tbase(round(SR*d));n=len(t);move=pan+.76*smooth(t/(.81*d))-.36
        open_t=.19 if wide else .13
        travel=smooth((t-open_t)/.51)*(1.-smooth((t-1.56)/1.04))
        friction=self.bank.field('shaker',n,9.61 if wide else 14.33,187,3350).mean(axis=1)
        rasp=self.noise(n,133,650);flutter=.78+.16*np.sin(32.4*t)+.06*np.sin(77.7*t)
        groan=resonator(t,140 if wide else 178,74 if wide else 99,1.64,.44)
        x=self.place((.163*friction*flutter+.111*rasp+.21*groan)*travel,move,.29)
        layers=[(0.,self.source('crack2' if wide else 'crack1',.29,.81 if wide else .91,118,4500)*.79,pan-.38),
                (.022,self.source('drum',.79,.78 if wide else .92,61,1150)*.59,pan*.30),
                (.43,self.source('hard1',.35,.72,166,3020)*.43,pan+.41),
                (.64 if wide else .59,self.crumbs(1.96,seed,1.06,True),pan+.25),
                (1.07 if wide else .91,self.source('crack1' if wide else 'crack2',.31,.79,150,3250)*.43,pan+.36),
                (1.22 if wide else 1.05,self.source('drum',.72,.82,72,990)*.35,pan*.30)]
        return x+self.arrange(d,layers)

    def build(self,key,kind,pan,seed):
        if key in ('rift-down','rift-early'):return self.fault(key,pan,seed)
        if key in ('rewind-scan','reconstruction') or kind in ('churn','sweep'):
            d=2.10 if key=='rewind-scan' else 1.54
            t=tbase(round(d*SR));move=pan+.97*smooth(t/(.75*d))-.49
            a=self.place(self.colour(d,key,(seed%7)*.06),move,.62)
            add(a,0,self.place(self.source('drum',.68,.91,62,810)*.43,pan,.31))
            b0=.24 if key=='rewind-scan' else .47
            for j,sec in enumerate((.0,b0,b0+.31)):
                z=self.source(('stone3','gravel2','pour2')[j],.28,1.04+j*.15,230,4800)
                add(a,round(sec*SR),self.place(z*(.33-.055*j),pan-.48+j*.43,.23))
            return a
        if kind in ('glass','airchime','title','waterglass'):
            if key in ('scan-read','scan-side','photos'):
                d=1.13 if key=='photos' else .52
                t=tbase(round(d*SR));k=self.source('hard2',d,1.15 if key=='scan-read' else 1.33,322,5050)
                z=self.source('stone3',d,1.19,264,3740);return self.place((k*.55+z*.30)*env(t,d,.0015,.19),pan,.32) if key!='photos' else self.bell(key,d,pan)
            return self.bell(key,1.42 if kind in ('airchime','title') else 1.14,pan,(seed%9)*.128-.46)
        if kind in ('brook','surge'):
            d=3.20 if key in ('rift-late','erosion-wash','drain') else 2.55
            return self.surf(d,pan,key)
        if kind=='droplet':
            d=.87
            drops=[(0,self.source('plop3' if seed%2 else 'plop1',.64,.99+seed%3*.13,126,4480)*.72,pan),
                   (.16,self.source('tap',.29,1.01,231,4710)*.33,pan-.17)]
            t=tbase(round(SR*d));little=.089*resonator(t,484,241,17.1,.12)*env(t,d,.0035,.26)
            return self.arrange(d,drops)+self.place(little,pan+.2*smooth(t/.72),.32)
        if kind=='press':
            d=1.28
            t=tbase(round(SR*d));n=len(t)
            body=(.229*resonator(t,122,59,9.7,.25)+.101*self.noise(n,97,552)*np.exp(-t*10.1))*env(t,d,.0045,.22)
            thud=self.source('drum',.72,.88+(seed%3)*.035,55,1200)*.47
            if key=='test-down':
                # Same picture-frame contact, two very different substrates.
                firm=self.source('hard1',.33,1.1,148,4400)*.91+self.crumbs(.33,seed,.84)
                fines=self.source('sand2',.30,1.21,370,4600)*.33
                wet=self.wet(d,.55,seed,1.11)
                runnel=self.source('wet1',.66,.73,200,2280)*.24
                return self.arrange(d,[(0,firm,-.69),(0,thud,-.14),(0,body,0),(.025,fines,-.61),(.17,runnel,.61)])+wet
            return self.arrange(d,[(0,thud,pan*.40),(0,body,pan),(0,self.crumbs(.78,seed,1.1),pan-.22)])+self.wet(d,pan+.21,seed,.88)
        if kind=='peel' and (key in ('stamp-up','test-up','mud-draw') or key.startswith('subsoil')):
            d=1.75 if key=='test-up' else 1.34;t=tbase(round(SR*d))
            suction=(.167*resonator(t,139,61,8.1,.30)+.059*self.noise(len(t),220,1230)*np.exp(-t*4.7))*env(t,d,.010,.27)
            x=self.place(suction,pan,.36)
            add(x,0,self.place(self.source('wet2',.62,.80,190,3850)*.67,pan+.22,.23))
            add(x,round(.092*SR),self.place(self.source('gravel1',.40,.79,320,3700)*.51,pan-.37,.22))
            add(x,round(.35*SR),self.place(self.source('plop1',.46,1.13,175,3320)*.36,pan+.38,.31))
            if key=='test-up':
                dry_release=self.source('sand1',.33,1.07,313,4500)*.47
                add(x,0,self.place(dry_release,-.58,.16))
            return x
        if kind in ('break','granules','peel','bristle','brush'):
            if kind=='break':
                d=1.54
                v=self.crumbs(d,seed,1.04,True);t=tbase(len(v))
                out=self.place(v,pan+.61*smooth(t/d)-.32,.24)
                add(out,0,self.place(self.source('crack1' if seed%2 else 'crack2',.24,.79,91,4290)*.87,pan,.23))
                add(out,round(.029*SR),self.place(self.source('drum',.71,.91,59,795)*.34,pan*.53,.29))
                add(out,round(.146*SR),self.place(self.source('hard1',.31,.76,135,3270)*.36,pan*.51+.21,.16))
                return out
            if kind=='granules':
                d=2.48 if key=='bury' else 1.81 if 'slump' in key or 'fill' in key else 1.44
                t=tbase(round(d*SR));z=self.crumbs(d,seed,1.47,True)
                p=pan+(.88 if key=='bury' else .57)*smooth(t/d)-(.38 if key=='bury' else .24)
                return self.place(z,p,.29)
            d=1.54 if kind in ('brush','bristle') else 1.01;t=tbase(round(d*SR));n=len(t)
            w=.62+.38*np.cos(5.1*t+1.1*np.sin(7*t))
            is_brush=kind in ('brush','bristle');a='rub2' if seed%2 else 'rub1'
            x=self.place((.077*self.noise(n,328,2710)*w*np.exp(-t*2.8)+.80*self.crumbs(d,seed))*env(t,d,.006,.20),
                         pan+.43*smooth(t/d)-.21,.25)
            add(x,0,self.place(self.source(a if is_brush else 'gravel1',min(d,.72),.73+seed%4*.14,240,4030)*.65,pan,.19))
            if not is_brush:
                add(x,round(.072*SR),self.place(self.source('stone1',.38,.84,116,3420)*.37,-pan*.29,.27))
            return x
        if kind in ('mineral','dry','step'):
            d=.58 if kind!='step' else .41
            if key in ('count','countways','firm-soft'):
                # Counts land on a texture, not a repeated high-pitched UI pip.
                d=.72
            t=tbase(round(d*SR));n=len(t);a=('stone1','gravel2','sand1','hard1')[(seed+1)%4]
            x=self.source(a,d,.84+.08*(seed%6),132,4620)*.80
            if kind=='step':
                x=.54*self.source('hard2',d,.87+seed*.014%(.24),199,3200)+.67*self.source('sand2',d,1.14,190,4200)
                x+=.14*resonator(t,168+seed%5*7,121,20.,.21)*env(t,d,.004,.17)
            else:x+=.139*resonator(t,293+seed%4*21,225,19.2,.32)*env(t,d,.003,.12)
            a=self.place(x,pan,.19)
            if key=='firm-soft':add(a,round(.20*SR),self.place(self.source('wet1',.50,1.22,220,3570)*.38,.57,.14))
            elif kind!='step':add(a,round(.097*SR),self.place(self.source('stone3',min(.24,d-.097),.88+seed*.025%(.30),300,3800)*.23,-pan*.46,.18))
            return a
        raise ValueError((key,kind))

    def dip(self,at,amt,span):
        center=round(at/200);r=round(span*SR/200);j=max(0,center-r);k=min(len(self.score_duck),center+r+1)
        x=(np.arange(j,k,dtype=np.float32)-center)/max(1,r)
        self.score_duck[j:k]*=1-(1-amt)*np.cos(.5*np.pi*x)**2

    def spot(self,key,kind,when,pan,seed,main=False,text=False,gain=1.):
        at=when*SPF;x=self.build(key,kind,pan,seed)
        # Tiny rounded entry may expose the recorded transient, but never an
        # isolated single-sample click at the start of the picture cue.
        t=tbase(len(x));x*=env(t,len(x)/SR,.0022,.065)[:,None]
        voice=db_rms(self.vox[max(0,at-3600):min(N,at+16_800)])
        hero=key in HERO
        if main:
            target=np.clip(voice-(5.1 if hero else 9.7),-28.0 if hero else -33.4,-20.9 if hero else -25.0)
            if key in ('title-a','title-b','title-c'):target=np.clip(target,-28.3,-24.2)
            if key=='gentle-close':target=-30.0
            if key.startswith('small-step'):target=np.clip(voice-7.4,-29.5,-24.5)
            if key in ('test-down','test-up'):target+=2.1
            if key=='rift-down':target=-23.6 # use the spoken pause at the first fracture
        else:
            target=np.clip(voice-10.8,-35.0,-27.3)
            if key in ('first-contact','ocean-pull','river-entrance','close-earth','air-release','subsoil-wipe'):target+=3.2
        # Listen-window matching keeps long sustainable tails as well as attacks.
        focus=round((.325 if kind not in ('churn','surge','brook') else .455)*SR)
        x*=g(float(target)-db_rms(x[:focus]))*min(1.18,max(.84,gain**.66))
        cap=g(-9.1 if hero else -12.2 if main else -14.8)
        # Round only the top of peaky Foley; leave all lower detail intact.
        mag=np.abs(x);start=cap*.72;reach=cap-start
        excess=mag>start
        x[excess]=np.sign(x[excess])*(start+reach*np.tanh((mag[excess]-start)/reach))
        attack=np.flatnonzero(np.max(np.abs(x[:SPF]),axis=1)>g(-54.))
        if main:assert len(attack),(key,db_rms(x[:SPF]),db_peak(x[:SPF]))
        add(self.fx,at,x)
        onset=at+int(attack[0]) if len(attack) else None
        row={'name':key,'family':kind,'frame':when,'trigger_sample':at,'attack_sample':onset,'isolated_attack_sample':onset,
             'text':text,'pan':pan,'foreground':hero,'focus_samples':focus,'focus_rms_dbfs_pre_bus':round(db_rms(x[:focus]),2),
             'one_frame_rms_dbfs':round(db_rms(x[:SPF]),2),'peak_dbfs':round(db_peak(x),2)}
        (self.spots if main else self.extras).append(row)
        if hero:self.dip(at,.23 if kind in ('press','break','peel','churn','surge') else .54,.74 if kind not in ('brook','surge') else 1.19)

    def all_spots(self):
        # Extra movement and low-texture edits are separate from the original
        # first-visible graphic/physical spot ledger. A negative prelap may
        # precede a shot, but never moves its existing exact event anchor.
        additional=(
            ('first-contact',0.000,'brush',-.46),('close-grain',.26,'mineral',.31),('cut-cameroon','koum-intro','brush',.48),
            ('orbit-load',3.94,'sweep',-.42),('rewind-inhale',9.88,'brush',-.62),('antique-hold',13.95,'airchime',.37),
            ('floodplain-in',19.38,'surge',.44),('air-release',22.25,'surge',-.48),('survey-cut','first-horizons','dry',.50),
            ('river-entrance','mayo','surge',-.48),('bank-near',39.87,'droplet',.44),('imprint-rake',44.15,'brush',-.51),
            ('step-tension',48.49,'bruise',-.37),('quieter-wet-settle',51.72,'droplet',.31),('trackway-rake',54.84,'brush',.43),
            ('stone-stop','edge','mineral',.21),('strata-grind',69.37,'brush',-.38),('loose-end',81.91,'granules',-.31),
            ('camera-awake','views','mineral',.47),('mesh-wipe',92.50,'brush',-.43),('rule-settle',102.54,'dry',-.29),
            ('margin-scrub',114.43,'brush',.35),('dry-stamp-load',123.42,'brush',-.57),('soft-print-holds',126.53,'droplet',.58),
            ('slump-grains',130.68,'granules',.48),('clear-to-soft',137.10,'brush',-.47),('dry-edge-match',144.46,'dry',.35),
            ('rippling-in','ripples','surge',-.42),('brittle-match','cracks','dry',.39),('wet-v-dry',165.85,'brush',-.33),
            ('more-bank',170.43,'droplet',.44),('wash-left',178.79,'surge',-.50),('under-the-lens','cement','mineral',.45),
            ('cement-pixels',190.44,'dry',.36),('bridges',197.74,'bristle',-.40),('sand-slide',204.78,'granules',.36),
            ('return-to-bed','preserved','brush',.48),('to-brazil','sousa','sweep',-.42),('agua','sousa-water','surge',.32),
            ('subsoil-wipe',224.19,'peel',-.42),('raised-edge',233.07,'brush',.41),('rim-resolve','held','dry',-.44),
            ('place-other-slab',246.37,'mineral',.54),('new-banks','banks','surge',-.42),('flow-near',257.90,'surge',.44),
            ('not-matching','unmatched','dry',-.30),('pollen-appear','pollen','airchime',.32),('dated-neighbour','regional','dry',-.38),
            ('old-globe-in','restore','sweep',-.34),('bedrock-set','bedrock','mineral',.40),('oblique-fault','structures','airchime',-.26),
            ('fault-creep',315.02,'granules',.38),('sediment-second',323.55,'granules',-.45),('valley-approach','valleys','surge',-.56),
            ('branching-riffle',338.03,'droplet',.49),('habitat-join','possible','sweep',.35),('water-line','fish','surge',-.38),
            ('through-the-water',359.83,'droplet',.45),('lobed-fin',364.33,'surge',.32),('surface-change','fish-basins','dry',.49),
            ('evidence-rake',373.61,'brush',-.31),('one-pattern','patterns','mineral',-.27),('another-pattern',378.27,'dry',.42),
            ('out-of-the-lab','still-possible','sweep',-.31),('close-earth','rift','churn',-.24),('ocean-pull',407.94,'surge',.45),
            ('return-the-camera','return','sweep',-.28),('gap-spark',416.10,'glass',.52),('rock-touch','last-print','brush',-.46),
            ('last-impression',435.36,'mineral',.30),
        )
        for i,q in enumerate(B):self.spot(q.key,q.sound,q.f,q.pan,i,True,bool(q.text),q.gain)
        # Use the literal shot key here; do not re-round a shot's frame number.
        for i,(key,t,kind,p) in enumerate(additional):
            f=F[INDEX[t]] if isinstance(t,str) else frame(t)
            self.spot(key,'brush' if kind=='bruise' else kind,f,p,i+100)
        for sec,depth,width in ((48.99,.16,1.58),(76.92,.32,1.17),(124.01,.14,1.80),(129.13,.13,1.82),
               (169.36,.34,1.28),(204.24,.19,1.70),(314.14,.14,1.25),(408.12,.14,2.31),(422.91,.085,2.05)):
            self.dip(round(sec*SR),depth,width)

    def water_ambience(self,shot,n,t,level):
        # Source segments and stereo trajectories are assigned by scene. Dry
        # rock scenes are not played under the same stream as river scenes.
        name=shot.key
        source,offset,bounds,pan={
            'title':('stream',40.2,(180,4650),-.26),'mayo':('river',4.7,(127,4800),-.24),
            'ripples':('lake',8.73,(139,3890),.28),'drain':('river',18.7,(149,4220),-.08),
            'wear':('lake',20.86,(124,4140),.17),'sousa-water':('stream',64.2,(105,5230),-.32),
            'banks':('river',33.10,(115,4970),.32),'fill':('lake',25.6,(138,3250),-.20),
            'valleys':('stream',92.7,(122,4600),-.10),'generations':('lake',42.3,(136,4680),.11),
            'fish':('river',45.3,(72,1280),-.13),'fish-basins':('lake',27.71,(112,1610),.10),
        }.get(name,('stream',98.8,(133,3860),.10))
        p=pan+.24*np.sin(.41*t+shot.var*.63);length=n/SR
        a=self.bank.field(source,n,offset,*bounds)
        if name=='drain':a*= (1-.81*smooth((t-.75)/3.25))[:,None]
        elif name=='wear':a*= (.31+.69*smooth((t-.79)/3.57))[:,None]
        elif name=='fish-basins':a*= (1-.76*smooth(t/2.55))[:,None]
        a=self.spatial(a,p,.91 if source!='lake' else .63)
        if source in ('lake','stream'):
            b=self.bank.field('river',n,offset*.2+7.5,594,4470)
            a+=.22*self.spatial(b,-.35+p*.39,.80)*(.76+.24*np.cos(.61*t))[:,None]
        if name=='fish':
            a*= (.63+.37*np.cos(.57*t-1.1)**2)[:,None]
            a+=.17*self.place(self.noise(n,266,855),.27*np.sin(.51*t),.45)
        return a*level

    def spaces(self):
        def amp(db):return g(db)
        field_level={'brook':-30.,'water':-33.,'grit':-39.,'mud':-37.,'globe':-41.,'wind':-33.,'studio':-43.,'glass':-40.,'fault':-34.}
        for i,q in enumerate(S):
            water=q.air in ('brook','water') or q.key=='wear';lead=.36 if water else .22;tail=.53 if water else .34
            a=max(0,round(SPF*q.f-lead*SR));z=min(N,round(SPF*F[i+1]+tail*SR));n=z-a;t=tbase(n);d=n/SR
            vol=amp(field_level[q.air])
            mask=env(t,d,lead+.20 if a else .043,.59 if water else .41)
            if water:
                x=self.water_ambience(q,n,t,amp(-30.5) if q.key=='wear' else vol)
            elif q.air in ('grit','wind','mud'):
                wind=self.bank.field('wind',n,i*2.39+.27,116 if q.air=='wind' else 146,1730 if q.air=='mud' else 2390)
                drift=(-.24+.47*np.sin(.23*t+i*.58));x=self.spatial(wind,drift,.51)*vol
                if q.air=='mud':
                    b=self.bank.field('lake',n,11.45+.87*i,210,2940)
                    x+=.54*vol*self.spatial(b,-drift,.52)*(.39+.61*smooth(t/.92))[:,None]
                if q.air=='grit' and q.key not in ('last-print','which-journey'):
                    for j,pos in enumerate((.42,d*.52,d-.34)):
                        if pos<0 or pos+.24>=d:continue
                        sound=self.source(('sand2','rub1','gravel2')[(i+j)%3],.25,.90+i*.041%(.33),210,3220)
                        add(x,round(pos*SR),self.place(sound*g(-32.2),(.51 if (i+j)%2 else -.48),.11))
            elif q.air=='fault':
                rock=self.bank.field('shaker',n,i*.74,132,2240).mean(axis=1)
                rumble=self.noise(n,49,273);shaped=.47+.53*np.sin(.46*t-.8)**2
                drift=.31*np.sin(.61*t-.62)
                x=self.place(.82*vol*rock*shaped+.44*vol*rumble,drift,.36)
                if q.key=='rift':
                    first=max(0,BY['rift-late'].sample-a)
                    y=tbase(n-first);sea=self.bank.field('ocean',len(y),30.4,84,3890)
                    add(x,first,self.spatial(sea,.31-.47*smooth(y/3.7),.85)*(g(-25.5)*env(y,len(y)/SR,.67,.43))[:,None])
            else:
                lo,hi=(78,580) if q.air=='globe' else (132,1250) if q.air=='studio' else (205,1560)
                u=self.noise(n,lo,hi);v=self.noise(n,lo*1.5,hi*1.4)
                x=self.place(vol*(.80*u+.28*v)*(.60+.40*np.sin(.28*t+i*.7)**2),.27*np.sin(.46*t+i*.54),.31)
            add(self.amb,a,x*mask[:,None])

    def music(self):
        # Bowed harmonics as a continuous room of tone. The soft mallet motif
        # opens only at a few turns and at the closing card; Foley drives pace.
        data=(
         (1.45,(50,57,64)),(10.8,(46,53,62)),(18.74,(38,50,57)),(25.15,(36,48,55)),(35.94,(41,53,60)),(46.42,(38,53,57)),
         (56.78,(34,53,60)),(67.8,(36,48,57)),(78.2,(38,50,57)),(89.5,(41,53,64)),(100.6,(38,53,57)),(111.44,(36,50,55)),
         (121.9,(34,50,57)),(132.04,(36,48,55)),(145.04,(38,53,57)),(155.3,(41,53,60)),(166.9,(38,50,57)),(176.2,(46,53,62)),
         (186.21,(38,50,65)),(196.1,(36,48,55)),(207.8,(38,50,57)),(218.39,(41,53,60)),(228.6,(38,53,57)),(239.48,(34,46,57)),
         (250.05,(36,52,55)),(261.49,(38,50,65)),(272.1,(41,53,64)),(283.26,(36,48,55)),(294.15,(38,50,57)),(305.39,(34,50,57)),
         (316.36,(36,48,55)),(327.47,(38,50,57)),(338.35,(41,53,64)),(348.4,(38,53,57)),(359.42,(36,48,55)),(369.8,(34,46,57)),
         (382.4,(41,53,60)),(393.10,(36,48,55)),(403.8,(34,46,57)),(413.56,(36,50,55)),(424.4,(38,50,57)),(435.4,(38,50,62)),
        )
        for i,(at,notes) in enumerate(data):
            ahead=data[i+1][0] if i+1<len(data) else N/SR;d=min(N/SR-at,ahead-at+1.63)
            for j,k in enumerate(notes):
                pos=at+.27*j;n=round((d-.27*j)*SR);t=tbase(n);freq=440*2**((k-69)/12)
                if j==0:
                    p=2*np.pi*freq*t+.18*np.sin(1.8*t+i*.84)
                    x=(np.sin(p)+.29*np.cos(2.0004*p+.62)+.105*np.sin(3.0013*p-.81))*(.65+.35*np.sin(1.1*t+.75*i)**2)
                    x=tone(x,42,460)*env(t,len(t)/SR,1.86,2.25)*.024
                else:
                    root=62 if j==2 else 55;name='bowD' if j==2 else 'bowG';speed=2**((k-root)/12.)
                    take=self.bank.active(name);head=round(.26*SR);tail=len(take)-round(.68*SR)-head
                    idx=head+(np.arange(n,dtype=np.float32)*speed)%tail
                    sig=np.interp(idx,np.arange(len(take),dtype=np.float32),take).astype(np.float32)
                    # At each wrap overlap a small part of the alternate tail.
                    phase=idx-head;cross=round(.43*SR);sel=phase>=tail-cross;u=smooth((phase[sel]-(tail-cross))/cross)
                    pre=np.interp(phase[sel]-(tail-cross),np.arange(len(take),dtype=np.float32),take).astype(np.float32)
                    sig[sel]=sig[sel]*(1-u)+pre*u
                    x=tone(sig,90,2760);x*=g(-39.8 if j==1 else -43.4)/max(1e-8,rms(x));x*=env(t,len(t)/SR,1.65+j*.29,2.13)
                add(self.score,round(pos*SR),self.place(x,(-.12,-.54,.47)[j],.51))
        # Real soft mallet samples, pitched into a restrained recurring motif.
        lead=(
            (3.22,50,.73,-.42),(5.18,57,.60,.41),(16.82,57,.75,-.24),(22.4,62,.61,.34),(24.67,65,.49,.25),
            (37.35,53,.59,-.32),(41.80,60,.50,.40),(59.94,57,.47,-.21),(74.30,55,.64,.42), (93.42,64,.60,.22),
            (101.22,57,.45,-.21),(143.0,57,.53,.19),(155.98,65,.63,-.32),(186.04,57,.51,.26),(199.4,55,.49,-.32),
            (211.50,57,.60,.30),(222.18,60,.63,-.25),(250.95,55,.54,.31),(270.41,62,.43,.21),(292.97,57,.54,-.31),
            (304.86,53,.52,.24),(329.17,50,.55,-.35),(339.73,62,.58,.25),(356.42,55,.52,-.29),(362.83,60,.60,.34),
            (396.72,53,.57,.25),(412.61,50,.49,-.37),(427.05,57,.43,.36),(436.14,50,.65,-.30),
            (438.69,57,.53,.37),(439.23,62,.95,-.22),(440.96,65,.69,.36),(442.46,69,.62,-.32),
        )
        for at,note,gain,pan in lead:
            d=min(3.8,N/SR-at);source='vibeD' if note<66 else 'vibeA';root=62 if note<66 else 69
            a=self.source(source,d,2**((note-root)/12.),104,3080)
            a*=g(-29.1 if at>=438.6 else -35.)*gain/max(1e-8, rms(a[:SR//2]))
            a*=env(tbase(len(a)),d,.014,1.01)
            add(self.score,round(at*SR),self.place(a,pan,.68))


def bed_headroom(bed,narr,cap=.80):
    # Exact source preservation: apply only a slow, local gain ceiling to
    # the stereo overlay. A 32 ms look-around avoids isolated clipped attacks.
    need=np.ones(N//200,np.float32);step=SR*4
    for i in range(0,N,step):
        j=min(N,i+step);b=bed[i:j];v=narr[i:j,None];mag=np.abs(b)
        ceiling=(cap-v*np.sign(b))/np.maximum(1e-7,mag)
        need[i//200:j//200]=np.clip(ceiling.min(axis=1).reshape(-1,200).min(axis=1),0.,1.)
    floor=minimum_filter1d(need,size=13,mode='nearest');sm=gaussian_filter1d(floor,3.2)
    return np.minimum(sm,need)


def mix():
    media_lock();DIR.mkdir(parents=True,exist_ok=True)
    bank=RecordingBank(sources())
    with wave.open(str(VO),'rb') as w:
        assert (w.getnframes(),w.getnchannels(),w.getsampwidth(),w.getframerate())==(SAMPLES,1,3,SR)
        dry=np.zeros(N,np.int32)
        for i in range(0,SAMPLES,6*SR):dry[i:min(i+6*SR,SAMPLES)]=i24(w,6*SR)[:,0]
    v=dry.astype(np.float32)/Q
    c=Soundstage(v,bank);c.all_spots();print('FOLEY_SPOTTED',len(c.spots),len(c.extras),flush=True)
    c.spaces();c.music();print('ENVIRONMENT_AND_SCORE_READY',len(bank.used),flush=True)
    phase=np.sqrt(np.mean(v.reshape(-1,200)**2,axis=1));ctrl=gaussian_filter1d(phase,5.5)
    block=SR*4;power=np.zeros(4,np.float64)
    for i in range(0,N,block):
        j=min(i+block,N);t=np.arange(i,j,dtype=np.float32)/SR
        s=smooth((np.repeat(ctrl[i//200:j//200],200)-.014)/.072)[:,None]
        tail=smooth((N/SR-t)/1.34)[:,None];start=smooth(t/.010)[:,None]
        # Local narration carve on ambience and score in the presence band;
        # retain the attack of the SFX, its left/right shape and its low body.
        music=c.score[i:j]*(1-.39*s)*np.repeat(c.score_duck[i//200:j//200],200)[:,None]
        air=c.amb[i:j];spl=air-tone(air,660,7400);air*=1-.16*s;air-=.21*s*(air-spl)
        detail=c.fx[i:j]*(1-.105*s); detail*=tail*start
        c.fx[i:j]=detail;c.score[i:j]=(music+air)*tail*start+detail
        for k,o in enumerate((c.score[i:j],music,air,detail)):power[k]+=np.sum(o*o,dtype=np.float64)
    head=bed_headroom(c.score,v)
    outputs=[f.with_suffix('.partial.wav') for f in (BED,MIX,FX)];peak=0.
    with wave_out(outputs[0]) as b, wave_out(outputs[1]) as m, wave_out(outputs[2]) as f:
        for i in range(0,N,block):
            j=min(i+block,N);l=np.repeat(head[i//200:j//200],200)[:,None]
            # Bin constraint is exact; interpolation below it removes steps.
            tr=np.linspace(0,1,200,dtype=np.float32)
            prev=head[max(0,i//200-1):j//200-1] if i else np.r_[head[:1],head[:j//200-1]]
            cur=head[i//200:j//200];l=np.minimum(l,(prev[:,None]+(cur-prev)[:,None]*tr).reshape(-1,1))
            fx=np.rint(c.fx[i:j]*l*Q).astype(np.int32);d=np.rint(c.score[i:j]*l*Q).astype(np.int32);out=d+dry[i:j,None]
            peak=max(peak,float(np.max(np.abs(out)))/Q)
            b.writeframesraw(sample_bytes(d));m.writeframesraw(sample_bytes(out));f.writeframesraw(sample_bytes(fx))
    assert peak<=.80001,peak
    for s,p in zip(outputs,(BED,MIX,FX),strict=True):s.replace(p)
    del c.amb
    real=analyze(v,c.spots,c.extras)
    info={'voice_sha256':LOCK['files'][0]['sha256'],'unchanged_samples':SAMPLES,'program_samples':N,
          'static_bed_gain':1.,'bed_vs_voice_db':real['global_bed_vs_voice_db'],'overall_rms_dbfs_pre_headroom':np.round(10*np.log10(power/(N*2)),3).tolist(),
          'overlay_min_headroom_gain':round(float(head.min()),7),'overlay_controlled_frames_240hz':int(np.sum(head<.997)),
          'graphic_sync':sum(q['text'] for q in c.spots),'spots':len(c.spots),'supporting_spots':len(c.extras),
          'first_attacks':c.spots,'additional_attacks':c.extras,'program_peak_dbfs':round(20*math.log10(peak),3),
          'bed_sha256':base.hashfile(BED),'mix_sha256':base.hashfile(MIX),'fx_sha256':base.hashfile(FX),'used_sources':sorted(bank.used),
          'local_comparison':real}
    REPORT.write_text(json.dumps(info,indent=2)+'\n')
    print('REMIX_READY',json.dumps({k:v for k,v in info.items() if k not in ('first_attacks','additional_attacks','used_sources')},indent=2),flush=True)


def analyze(vo,spots,extra):
    assert len(spots)==77 and len(extra)>=50 and sum(r['text'] for r in spots)==33
    compare=OLD_BED.is_file() and base.hashfile(OLD_BED)==OLD_BED_SHA
    energy=np.zeros(2,np.float64);anchors={};near=[]
    with wave.open(str(BED),'rb') as b, wave.open(str(FX),'rb') as fx:
        for i in range(0,N,SR*6):
            x=i24(b,SR*6).astype(np.float32)/Q
            energy[0]+=np.sum(x*x,dtype=np.float64)
            energy[1]+=np.sum((x[:,0]-x[:,1])**2,dtype=np.float64)
        for row in spots:
            at=row['trigger_sample'];n=min(N-at,row['focus_samples']);fx.setpos(at)
            x=i24(fx,n).astype(np.float32)/Q
            start=np.flatnonzero(np.max(np.abs(x[:SPF]),axis=1)>g(-54.))
            assert len(start),(row['name'],at,db_peak(x[:SPF]))
            row['attack_sample']=at+int(start[0]);row['one_frame_rms_dbfs']=round(db_rms(x[:SPF]),3)
            row['foreground_focus_rms_dbfs']=round(db_rms(x),3)
            row['score_free_focus_vo_dbfs']=round(db_rms(vo[at:at+n]),3)
            if row['foreground'] and row['score_free_focus_vo_dbfs']>-36:near.append(row['foreground_focus_rms_dbfs']-row['score_free_focus_vo_dbfs'])
        a=wave.open(str(OLD_BED),'rb') if compare else None
        try:
            for label,(lo,hi) in PLAN.items():
                i=round(lo*SR);n=round((hi-lo)*SR);b.setpos(i);fx.setpos(i)
                new=i24(b,n).astype(np.float32)/Q;s=i24(fx,n).astype(np.float32)/Q
                old=None
                if a is not None:
                    a.setpos(i);old=i24(a,n).astype(np.float32)/Q
                r={'in_s':lo,'out_s':hi,'bed_rms_dbfs':round(db_rms(new),3),'voice_rms_dbfs':round(db_rms(vo[i:i+n]),3),
                   'foreground_rms_dbfs':round(db_rms(s),3),'side_mid_db':round(db_rms(new[:,0]-new[:,1])-db_rms(new[:,0]+new[:,1]),3)}
                if old is not None:
                    r['v1_bed_rms_dbfs']=round(db_rms(old),3);r['increase_vs_v1_db']=round(r['bed_rms_dbfs']-r['v1_bed_rms_dbfs'],3)
                anchors[label]=r
        finally:
            if a is not None:a.close()
    voice=db_rms(vo);b=10*math.log10(energy[0]/(2*N));delta=b-voice
    assert -15.<delta<-4.5,(delta,b,voice)
    assert len(near)>=25 and np.median(near)>-12.,np.median(near)
    result={'global_bed_rms_dbfs':round(b,3),'global_bed_vs_voice_db':round(delta,3),
            'foreground_vs_narration_median_db_at_active_hero_cues':round(float(np.median(near)),3),
            'stereo_side_dbfs':round(10*math.log10(energy[1]/(4*N)),3),'anchors':anchors}
    if compare:
        drops=[r['increase_vs_v1_db'] for r in anchors.values()]
        result.update(median_anchor_increase_db=round(float(np.median(drops)),3),minimum_anchor_increase_db=min(drops))
        assert np.median(drops)>=6. and min(drops)>2.5,drops
    return result


if __name__=='__main__':mix()
