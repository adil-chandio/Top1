#!/usr/bin/env python3
"""A continuous tactile edit: matched material impacts, underscored voice, no bed dropouts."""
from __future__ import annotations
from math import pi

import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d

from clock import MIX, QA, SR, FP, dump, digest
from voice_edit import voice
from mix import Sound, ar, db, envelope, eq, gain, meter, rms, savewav, srt, stamp, windows


class RecutSound(Sound):
    def __init__(self,timeline):
        super().__init__()
        self.t=timeline;self.n=timeline['samples'];self.frames=timeline['frames']
        self.fx=np.zeros((self.n,2),np.float32);self.env=np.zeros_like(self.fx);self.music=np.zeros_like(self.fx)
        self.stems=[]

    def put(self,out,c,frame,amp,pan=0,dt=0,room=.16):
        s=frame*FP+ar(dt);v=stamp(c,s,amp,pan,room)
        l=len(out)-s
        if l>0:out[s:s+min(l,len(v))]+=v[:l]
        if len(v)>l:out[:len(v)-l]+=v[l:]

    def motion(self,name,f):
        layer=[];fx=np.zeros_like(self.fx);wet=name.startswith(('hook','soft','lip'))
        def clip(k,d,rate,lo,hi,amp,pan,dt=0,offset=0):
            self.put(fx,self.clip(k,d,rate,lo,hi,offset),f,amp,pan,dt,.19)
            layer.append([k,round(dt*SR),amp])
        def tone(key,d,amp,pan,fn,dt=0):
            x=np.arange(ar(d),dtype=np.float32)/SR
            self.put(fx,(fn(x)*envelope(len(x),.0025,min(.07,d*.2))).astype(np.float32),f,amp,pan,dt,.10)
            layer.append([key,round(SR*dt),amp])
        if name.endswith('_impact'):
            prime=name=='hook_impact'
            tone('contact body (original)',.25,.125 if prime else .080,-.08,
                 lambda t:np.sin(2*pi*(51*t+.47*(1-np.exp(-27*t))))*np.exp(-22*t))
            clip('wet1' if wet else 'hard1',.234,.94,145,4920,.162 if prime else .119,-.12,offset=.016 if wet else 0)
            clip('plop1' if wet else 'sand1',.272,1.14,220,6810,.078 if prime else .056,.18,.019)
            clip('gravel1',.31,.99,380,5920,.039,.25,.044)
        elif name.endswith('_lift'):
            clip('wet2' if wet else 'sand2',.286,.87 if wet else .93,213,6040,.097 if wet else .068,-.21,offset=.012)
            clip('plop3' if wet else 'gravel2',.27,1.17,310,6670,.066 if wet else .039,.23,.042)
            if wet:tone('wet release (original)',.138,.016,-.13,
                         lambda t:np.sin(2*pi*(194*t+1.4*(1-np.exp(-52*t))))*np.exp(-28*t),.058)
        elif name.endswith('_slump'):
            clip('pour',.49,.88,208,5630,.088,-.23)
            clip('gravel2',.27,1.13,295,5890,.036,.23,.102)
            clip('plop3',.15,1.21,390,6970,.049,.09,.041)
        elif name=='lip_cut':
            clip('rub1',.24,1.22,325,3530,.038,-.12)
            clip('sand2',.18,1.18,480,5890,.039,.14,.026)
        elif name=='lip_chip':
            clip('plop3',.188,1.33,290,6690,.078,-.24)
            clip('pour2',.30,.98,390,6030,.040,.23,.037)
        elif name=='match_reveal':
            clip('stone2',.22,.83,350,5200,.048,-.25)
            clip('stone3',.22,1.09,320,5590,.039,.24,.067)
        elif name in ('brazil_cut','cameroon_cut'):
            clip('stone1' if name=='brazil_cut' else 'stone2',.20,.94 if name=='brazil_cut' else .72,335,5800,.057,-.18 if name=='brazil_cut' else .22)
            clip('gravel2',.28,1.03,431,5850,.033,.06,.026)
        elif name=='globe_cut':
            clip('bowG',.42,.88,210,3560,.035,-.14)
            clip('rub2',.31,1.24,258,3860,.047,.2,.016)
            tone('atlas entry (original)',.28,.059,.04,
                 lambda t:np.sin(2*pi*(69*t+.35*(1-np.exp(-26*t))))*np.exp(-12*t))
        elif name=='map_rewind':
            clip('rub2',.57,.87,245,3850,.055,-.18)
            clip('bowD',.93,.84,165,2400,.042,.22,.057)
            tone('windback sweep (original)',.65,.022,0,
                 lambda t:np.sin(2*pi*(378*t+114*(1-np.exp(-6*t))))*np.exp(-4.5*t),.014)
        elif name=='map_land':
            clip('vibeD',.56,.847,211,4590,.053,.22)
            clip('stone3',.22,.72,250,3220,.027,-.07,.034)
        elif name=='rock_cut':
            clip('sand1',.22,.86,319,4700,.043,-.11)
            tone('strata cut (original)',.19,.057,-.06,lambda t:np.sin(2*pi*64*t)*np.exp(-23*t))
        elif name=='rock_chip':
            clip('crack1',.24,.91,249,5180,.071,.10)
            clip('gravel2',.36,.95,350,6720,.049,-.23,.039)
        elif name=='return_air':
            clip('sand2',.29,.78,285,3620,.040,-.20)
            clip('wet2',.23,1.03,183,4420,.028,.15,.044)
        else:raise KeyError(name)
        self.fx+=fx
        self.stems.append((name,f,fx[f*FP:f*FP+ar(.17)].copy(),layer))

    def deck(self):
        # Circular, shaped beds; near-bank water eases into a much broader
        # atlas bed and comes back under the descending step on replay.
        t=np.arange(self.n,dtype=np.float32)/SR;d=self.t['seconds'];a=self.t['art']
        def smooth(x):return x*x*(3-2*x)
        atlas=smooth(np.clip((t-a['today']/30+.18)/.47,0,1))*smooth(np.clip((a['strata']/30+.33-t)/.49,0,1))
        wind=.77+.23*np.cos(2*pi*(t-.35)/d)
        for k,lo,hi,level,off,mod in (
            ('wind',122,3420,.0147,2.37,wind*(1-.42*atlas)),
            ('lake',190,3740,.0124,1.57,.37+.63*(1-atlas)),
            ('stream',214,4170,.0083,4.35,.17+.83*(1-atlas)),
            ('ocean',124,2120,.0093,.98,.31+.69*atlas)):
            x=self.source(k,2).copy();L=ar(.22);total=len(x)-L;assert total>L
            u=smooth(np.linspace(0,1,L,dtype=np.float32)[:,None]);x[:L]=x[total:]*(1-u)+x[:L]*u
            pad=ar(.36);b=eq(x[(np.arange(-pad,self.n)+ar(off))%total],lo,hi);body=b[pad:].copy()
            body[-L:]=body[-L:]*(1-u)+b[pad-L:pad]*u
            self.env+=body*(level/max(.0004,rms(body)))*mod[:,None]
        # Original 4/4 pulse built from small struck sounds, a note pattern
        # and a quiet counter-rhythm. The atlas opens the filter and widens the
        # pattern, not a stock sweep laid across a long unvoiced hold.
        beat=d/50
        def notes(k,where,rate,length,amp,pan,lo,hi,attack=.008):
            src=self.source(k);s=np.interp(np.arange(ar(length))*rate,np.arange(len(src)),src,left=0,right=0).astype(np.float32)
            s=eq(s,lo,hi)*envelope(len(s),attack,min(.29,length*.55))
            i=ar(where)%self.n;self.put(self.music,s/max(np.max(np.abs(s)),.002),i//FP,amp,pan,(i%FP)/SR,.33)
        for j in range(50):
            b=.167+j*beat
            # Long bowed beds support a dry stick-and-vibes groove. Fade and
            # wrap note tails into the incoming step instead of looping a pop.
            if j%4==0:notes('bowG' if (j//4)%3==1 else 'bowD',b+.057,.79 if j<30 else .94,2.05,.036,-.37 if j%8 else .37,84,3040,.34)
            if j%4 in (0,2):notes('drum',b,.86 if j%4==0 else 1.05,.217,.038 if j%4==0 else .025,-.06,112,3140)
            if j%4!=0:notes('shaker',b+.17,.92+(j%3)*.11,.13,.019,-.31 if j%2 else .31,590,6900)
            if j%8 in (1,3,6):
                m=('vibeD','vibeA','vibeE')[(j//2)%3]
                notes(m,b+.046,.86 if j<29 else 1.03,.64,.035,.37 if j%8==1 else -.29,185,3600)
            if 31<=j<=40 and j%2==0:notes('vibeE',b+.21,.92,.72,.027,.40,213,4360)


def build():
    MIX.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    a,cues,edits,t,pace=voice();s=RecutSound(t)
    for k,f in t['events'].items():s.motion(k,f)
    s.deck()
    e=np.sqrt(gaussian_filter1d(a*a,430,mode='wrap'))
    ahead=gaussian_filter1d(maximum_filter1d(e,size=4911,mode='wrap'),975,mode='wrap')
    q=np.clip((ahead-.008)/.063,0,1)[:,None]
    # Keep the Foley's weight in the lower harmonics; turn down the competing
    # consonant bands of the score and moving air during actual speech.
    hero=s.fx*(1-.29*q)-eq(s.fx,410,5450)*(.29*q)
    bed=s.env*(1-.64*q)+s.music*(1-.72*q)
    # AAC's first MDCT window can make a tiny edit-point discontinuity on a
    # non-zero sample even if the underlying ambience is circular. Use only
    # a six-millisecond edge taper on the bed (not an editorial pause).
    edge=ar(.006);taper=np.sin(np.linspace(0,pi/2,edge,dtype=np.float32))**2
    bed[:edge]*=taper[:,None];bed[-edge:]*=taper[::-1,None]
    v=a*.87
    x=(v[:,None]+hero+bed).astype(np.float32)
    pre=MIX/'preflight.wav';savewav(pre,x);raw=meter(pre)
    k=gain(-16.85-raw['lufs_i']);x*=k
    peak=maximum_filter1d(np.max(np.abs(x),axis=1),size=285,mode='wrap')
    lim=gaussian_filter1d(np.minimum(1,gain(-2.63)/np.maximum(peak,.00001)),115,mode='wrap')
    x*=lim[:,None];assert min(lim)>.73
    out=MIX/'program.wav';savewav(out,x);stats=meter(out)
    assert -17.3<=stats['lufs_i']<=-16.35 and stats['dbtp']<=-1.72,stats
    attacks=[]
    for name,f,fxy,layers in s.stems:
        l=f*FP;r=l+len(fxy);scaled=(fxy*(1-.29*q[l:r])-eq(fxy,410,5450)*(.29*q[l:r]))*(k*lim[l:r,None])
        h=np.flatnonzero(np.max(np.abs(scaled[:FP]),axis=1)>.00068)
        assert len(h) and h[0]*1000/SR<=15,(name,h[:1])
        attacks.append(dict(name=name,frame=f,attack_ms=round(h[0]*1000/SR,3),
                            phone_band_dbfs=round(db(rms(eq(scaled.mean(1),185,4800))),2),layers=layers))
    savewav(MIX/'narration-reference.wav',v*k*lim)
    savewav(MIX/'foley-reference.wav',hero*k*lim[:,None])
    savewav(MIX/'deck-reference.wav',bed*k*lim[:,None])
    (MIX/'captions.srt').write_text(srt(cues),encoding='utf-8')
    dump(QA/'mix.json',dict(timeline=t,pacing=pace,cues=cues,voice_edits=edits,sha256=digest(out),
                           loudness=stats,peak_limit_db=round(db(float(min(lim))),2),event_checks=attacks,
                           source_credits=s.notes(),score_info={'pulse_bpm':round(3000/t['seconds'],2),'circular':True}))
    print('V2_AUDIO_READY',stats,pace['longest_gap_ms'],'ms max phrase gap',len(attacks),'frame-pinned events',flush=True)


if __name__=='__main__':build()
