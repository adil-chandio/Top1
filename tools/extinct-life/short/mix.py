#!/usr/bin/env python3
"""New narration, tactile frame-pinned Foley, scene ambience, and stereo score."""
from __future__ import annotations
from functools import lru_cache
import json
import math
import re
import subprocess
import wave

import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
from scipy.signal import butter, resample_poly, sosfilt
from pocketsphinx import Decoder
import imageio_ffmpeg

from spec import CACHE, QA, HERE, BANK, FPS, FRAMES, SR, N, TAKES, EVENTS, digest, dump

FF=imageio_ffmpeg.get_ffmpeg_exe()
MIX=CACHE/'mix'; VO=CACHE/'vo'
WORD=re.compile(r"[a-z]+(?:'[a-z]+)?")
FP=SR//FPS


def ff(args,data=None):
    p=subprocess.run([FF,'-hide_banner','-nostdin',*map(str,args)],input=data,capture_output=True,timeout=70)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-2000:])
    return p.stdout, p.stderr.decode(errors='replace')


def ar(t):return round(SR*t)


def db(x):return 20*math.log10(max(1e-10,x))


def gain(x):return 10**(.05*x)


def rms(x):return float(np.sqrt(np.mean(x*x,dtype=np.float64)))


def windows(x):
    h=480;r=np.pad(x,(0,(-len(x))%h)).reshape(-1,h)
    return np.sqrt(np.mean(r*r,axis=1))


@lru_cache(maxsize=48)
def kernel(lo,hi):return butter(2,(lo,hi),btype='bandpass',fs=SR,output='sos')


def eq(x,lo,hi):return sosfilt(kernel(lo,hi),x,axis=0).astype(np.float32)


def decoded(p,ch=1):
    raw,_=ff(['-v','error','-i',p,'-vn','-ac',ch,'-ar',SR,'-f','f32le','-'])
    a=np.frombuffer(raw,'<f4').copy()
    return a if ch==1 else a.reshape(-1,ch)


def take_spans(p,phrases):
    expected=[WORD.findall(t.lower()) for t in phrases]
    joined=[w for ws in expected for w in ws]
    dec=Decoder(samprate=16000,frate=100,loglevel='ERROR')
    for w,phon in {'kilometres':'K IH L AA M AH T ER Z','landmass':'L AE N D M AE S','toed':'T OW D'}.items():
        if not dec.lookup_word(w):dec.add_word(w,phon,False)
    assert all(dec.lookup_word(x) for x in joined),[x for x in joined if not dec.lookup_word(x)]
    raw,_=ff(['-v','error','-i',p,'-ar','16000','-ac','1','-f','s16le','-'])
    dec.set_align_text(' '.join(joined));dec.start_utt();dec.process_raw(raw,full_utt=True);dec.end_utt()
    a=[(q.word.split('(')[0],q.start_frame*.01,(q.end_frame+1)*.01) for q in dec.seg() if not q.word.startswith(('<','['))]
    assert [w for w,_,_ in a]==joined,(p,a,joined)
    n=0;out=[]
    for text,tokens in zip(phrases,expected,strict=True):
        m=n+len(tokens);out.append((text,a[n][1],a[m-1][2]));n=m
    return a,out


def voice():
    result=np.zeros(N,np.float32);rec=[];caps=[]
    for name,frame,phrases in TAKES:
        p=VO/f'{name}.wav';words,cues=take_spans(p,phrases);x=decoded(p)
        assert words[0][1]<.48 and words[-1][2]<len(x)/SR+.012,(name,words[0],words[-1],len(x)/SR)
        lo=max(0,ar(words[0][1]-.036));hi=min(len(x),ar(words[-1][2]+.049))
        b=eq(x[lo:hi],68,11750)
        # Broadband take matching, not stretching. Small band-selective gain
        # rides only when a sibilant exceeds its local speech level.
        loud=windows(b);active=loud[loud>max(.0028,np.max(loud)*.11)]
        scale=min(6.9,max(.28,.085/float(np.quantile(active,.65))))
        b=b*scale
        s=eq(b,5300,10750);mid=eq(b,550,4250)
        h=gaussian_filter1d(s*s,100,mode='nearest');f=gaussian_filter1d(mid*mid,140,mode='nearest')
        a=np.clip((np.sqrt(h)-.037-.39*np.sqrt(f))*.98/.093,0,.48)
        b-=s*a.astype(np.float32)
        b*=envelope(len(b),.014,.026)
        start=frame*FP;end=start+len(b)
        assert end<N and not np.any(result[start:end]),(name,start,end)
        result[start:end]=b
        for text,v,w in cues:
            c=dict(text=text,start_sample=max(start,start+ar(v)-lo),end_sample=min(end,start+ar(w)-lo))
            assert c['end_sample']>c['start_sample']
            caps.append(c)
        rec.append(dict(name=name,sha256=digest(p),start=start,end=end,trim_native_at_48k=[lo,hi],
            gain_db=round(db(scale),3),active_rms_db=round(db(float(np.median(active))*scale),2),forced_word_spans=words))
    # One visual line can remain readable through a natural syllable gap, but
    # we never move its start earlier than the corresponding spoken words.
    for j,c in enumerate(caps):
        next_at=caps[j+1]['start_sample'] if j+1<len(caps) else N-ar(.46)
        wanted=max(c['end_sample']+ar(.34 if j+1==len(caps) else .095),c['start_sample']+ar(max(.67,len(c['text'])/23)))
        c['end_sample']=min(next_at-ar(.020),wanted)
        assert c['end_sample']-c['start_sample']>=ar(.30),c
    assert caps[0]['start_sample']/SR<.145 and caps[-1]['end_sample']/SR<33.6
    return result,caps,rec


def envelope(n,rise,fall):
    x=np.ones(n,np.float32);a=min(n//2,ar(rise));b=min(n//2,ar(fall))
    if a:x[:a]=np.sin(np.linspace(0,np.pi*.5,a,dtype=np.float32))**2
    if b:x[-b:]=np.cos(np.linspace(0,np.pi*.5,b,dtype=np.float32))**2
    return x


def stamp(c,where,vol,pan=0,room=.0):
    if len(c.shape)==1:
        a=.25*np.pi*(1+pan);v=np.column_stack((c*np.cos(a),c*np.sin(a)))*vol
    else:v=c*vol
    for d,k in ((331,.24),(1109,.17),(2789,.092)):
        if room and len(v)>d:v[d:]+=v[:-d,::-1]*(room*k)
    count=min(len(v),N-where)
    return v[:count]


class Sound:
    def __init__(self):
        self.fx=np.zeros((N,2),np.float32);self.env=np.zeros_like(self.fx);self.music=np.zeros_like(self.fx)
        self.lock={row['key']:row for row in json.loads((HERE.parent/'step-6/sound-v2-sources.json').read_text())}
        self.used=set();self.events=[]
    @lru_cache(maxsize=25)
    def source(self,key,ch=1):
        row=self.lock[key];p=BANK/row['file'];assert p.stat().st_size==row['bytes'] and digest(p)==row['sha256'],key
        self.used.add(key);return decoded(p,ch)
    def clip(self,k,d,rate,lo,hi,offset=0):
        x=self.source(k)
        first=np.flatnonzero(np.abs(x)>max(.00035,float(np.max(np.abs(x)))*.075))[0]
        j=max(0,int(first)+ar(offset)-65)
        # Remove silent lead-in after EQ/resampling too: some plop kernels
        # otherwise begin a whole frame after they are placed on the timeline.
        a=np.interp(j+np.arange(ar(d+.12),dtype=np.float32)*rate,np.arange(len(x),dtype=np.float32),x,left=0,right=0).astype(np.float32)
        a=eq(a,lo,hi);peak=float(np.max(np.abs(a[:ar(min(d+.1,.26))])))
        hits=np.flatnonzero(np.abs(a)>max(.000052,peak*.072));assert len(hits),k
        j=max(0,min(int(hits[0])-ar(.004),ar(.115)))
        a=a[j:j+ar(d)]*envelope(ar(d),.0021,min(.070,d*.32))
        return a/max(.001,np.max(np.abs(a)))
    def put(self,out,c,frame,amp,pan=0,dt=0,room=.16):
        n=frame*FP+ar(dt);a=stamp(c,n,amp,pan,room);out[n:n+len(a)]+=a
    def foley(self,name):
        f=EVENTS[name];layer=[]
        # Each primary transient is a real material recording. Smaller secondary
        # transients arrive after contact instead of piling up on the same sample.
        def p(k,d,rate,lo,hi,amp,pan,dt=0,offset=0):
            s=self.clip(k,d,rate,lo,hi,offset);self.put(self.fx,s,f,amp,pan,dt)
            layer.append([k,round(dt*SR),amp])
        if name.endswith('impact'):
            wet=name!='firm_impact';t=np.arange(ar(.27))/SR
            pulse=np.sin(2*np.pi*(49*t+19*(1-np.exp(-21*t))/21))*(1-np.exp(-210*t))*np.exp(-23*t)
            self.put(self.fx,pulse.astype(np.float32),f,.104 if name=='hook_impact' else .079,-.18,0,.10)
            p('wet1' if wet else 'hard1',.28,.91,155,4200,.127 if name=='hook_impact' else .090,-.12,0,.022 if wet else .0)
            p('plop1' if wet else 'sand1',.33,1.09,220,5450,.047,.16,.017)
            p('gravel1',.30,.97,290,4850,.042,.24,.043)
        elif name.endswith('lift'):
            firm=name=='firm_lift'
            p('sand2' if firm else 'wet2',.35,.79 if firm else .87,170,4850,.058 if firm else .080,-.22,0,.012)
            p('gravel2' if firm else 'plop3',.26,1.16,290,6100,.036,.21,.058)
        elif name.endswith('slump'):
            p('pour',.63,.82,225,4500,.057,-.26,0)
            p('plop3',.20,1.13,160,3500,.034,.21,.025)
            p('gravel2',.28,1.18,270,5800,.029,.33,.144)
        elif name=='lip_drip':p('plop3',.19,1.39,320,6300,.046,-.24)
        elif name=='rock_chip':
            p('crack1',.26,.83,190,3860,.062,.09)
            p('gravel2',.43,.91,365,6450,.050,-.29,.042)
        elif name=='map_rewind':
            p('rub2',.92,.85,240,2400,.024,-.11)
            # A low airy ribbon carries the reveal. No graphic click or riser hit.
            p('bowG',1.36,.89,159,2270,.033,.22,.083)
        else:raise ValueError(name)
        self.events.append(dict(name=name,frame=f,seconds=f/FPS,layers=layer))
    def ambience(self):
        t=np.arange(N,dtype=np.float32)/SR
        def beds(k,lo,hi,amp,offset,m):
            b=self.source(k,2).copy();L=ar(.14);length=len(b)-L
            assert length>L
            u=np.linspace(0,1,L,dtype=np.float32)[:,None];u=u*u*(3-2*u)
            b[:L]=b[length:]*(1-u)+b[:L]*u
            # Two circular blends: the fixed source loop, and the beginning
            # of the program. Filter actual pre-roll rather than zero padding.
            P=ar(.31);i=(np.arange(-P,N)+ar(offset))%length
            z=eq(b[i],lo,hi);body=z[P:].copy()
            body[-L:]=body[-L:]*(1-u)+z[P-L:P]*u
            self.env+=body*(amp/max(.00014,rms(body)))*m[:,None]
        map_room=np.clip((t-16.57)/.40,0,1)*np.clip((27.45-t)/.55,0,1)
        near=(.50+.50*np.cos(2*np.pi*(t-.8)/34))*(1-map_room)
        beds('wind',115,3300,.013,2.37,.84-.55*map_room)
        beds('lake',185,4100,.012,1.57,.18+.74*near)
        beds('stream',225,2470,.0057,4.35,(1-map_room)*(.41+.24*np.sin(6*np.pi*t/34)))
    def score(self):
        # Sparse, original arrangement using the same permitted family of bowed
        # and struck instrument samples as Cinema Edition.
        phrases=[('bowD',.19,6.8,.70,-.22,.029),('vibeD',2.78,2.67,.91,.11,.031),
                 ('bowG',5.69,5.28,.82,.16,.028),('vibeA',9.52,2.25,.89,-.19,.024),
                 ('bowD',12.08,7.12,.89,.23,.027),('vibeE',14.79,2.16,.75,-.09,.022),
                 ('bowG',17.76,7.57,.70,-.22,.026),('vibeA',21.51,3.22,.91,.10,.037),
                 ('bowD',25.06,6.21,.84,.24,.024),('vibeD',28.18,2.20,.82,-.27,.028),
                 ('bowG',30.11,3.80,.705,.15,.020)]
        for key,start,dur,rate,pan,amp in phrases:
            x=self.source(key);dt=np.arange(ar(dur),dtype=np.float32)*rate
            v=np.interp(dt,np.arange(len(x),dtype=np.float32),x,left=0,right=0).astype(np.float32)
            v=eq(v,83,2440)*envelope(len(v),.49 if key.startswith('bow') else .024,.94)
            v=v/max(.003,np.max(np.abs(v)));where=ar(start);m=stamp(v,where,amp,pan,.37)
            self.music[where:where+len(m)]+=m
    def notes(self):
        uniq={}
        for k in sorted(self.used):
            r=self.lock[k];key=(r['credit'],r['original_url'],r['license']);uniq.setdefault(key,[]).append(k)
        return [dict(credit=a,source=b,license=c,keys=d) for (a,b,c),d in uniq.items()]


def savewav(p,x):
    data=np.rint(np.clip(x,-.999999,.999999)*8388608).astype(np.int32).ravel()
    bits=np.stack([data&255,(data>>8)&255,(data>>16)&255],axis=1)
    with wave.open(str(p),'wb') as w:w.setnchannels(1 if x.ndim==1 else 2);w.setframerate(SR);w.setsampwidth(3);w.writeframes(bits.astype(np.uint8).tobytes())


def meter(p):
    _,log=ff(['-i',p,'-vn','-af','ebur128=peak=true','-f','null','-'])
    m=log.rsplit('Summary:',1)[-1]
    vals=[float(re.search(q,m).group(1)) for q in (r'I:\s+([\d.-]+) LUFS',r'LRA:\s+([\d.-]+) LU',r'Peak:\s+([\d.-]+) dBFS')]
    return dict(lufs_i=vals[0],lra=vals[1],dbtp=vals[2])


def srt(cues):
    def fmt(s):
        z=round(s*1000/SR);h,z=divmod(z,3600000);m,z=divmod(z,60000);s,z=divmod(z,1000)
        return f'{h:02d}:{m:02d}:{s:02d},{z:03d}'
    return '\n\n'.join(f"{i}\n{fmt(c['start_sample'])} --> {fmt(c['end_sample'])}\n{c['text']}" for i,c in enumerate(cues,1))+'\n'


def build():
    MIX.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    a,cues,locked=voice();s=Sound()
    for name in EVENTS:s.foley(name)
    s.ambience();s.score()
    mono=s.fx.mean(1);p=gaussian_filter1d(a*a,530,mode='nearest');e=np.sqrt(p)
    z=gaussian_filter1d(mono*mono,390,mode='nearest');m=np.sqrt(z)
    d=1-np.maximum(np.clip(e/.067,0,.42),np.clip(m/.118,0,.42));d=d.astype(np.float32)
    # The decoded phone-band check heard the opening plop and narration in the
    # same band. Use an anticipatory, slow-release clarity ride instead of
    # hard-compressing the consonants or shifting the frame-locked contact.
    lead=gaussian_filter1d(maximum_filter1d(e,size=4367,mode='nearest'),844,mode='nearest')
    clarity=np.clip((lead-.012)/.065,0,1).astype(np.float32)[:,None]
    hero=s.fx*(1-.40*clarity)
    bed=s.env*(.81+.19*d[:,None])*(1-.47*clarity)+s.music*d[:,None]*(1-.35*clarity)+hero
    # Equal-power centre offset for speech. Avoid gain jumps between hands-off
    # review and the long cut, without flattening the contact transients.
    v=a*.84;x=v[:,None]+bed
    tmp=MIX/'preflight.wav';savewav(tmp,x);old=meter(tmp)
    scale=gain(-17.44-old['lufs_i']);x*=scale
    mx=maximum_filter1d(np.max(np.abs(x),axis=1),size=235,mode='nearest')
    lim=np.minimum(1,gain(-2.73)/np.maximum(mx,.00001));lim=gaussian_filter1d(lim,112,mode='nearest')
    applied_db=db(float(np.min(lim)))
    x*=lim[:,None]
    path=MIX/'program.wav';savewav(path,x);stats=meter(path)
    if not(-17.95<=stats['lufs_i']<=-16.50 and stats['dbtp']<=-1.68):raise ValueError(stats)
    assert min(lim)>.72,applied_db
    savewav(MIX/'narration-reference.wav',v*scale*lim)
    savewav(MIX/'foley-reference.wav',hero*scale*lim[:,None])
    (MIX/'captions.srt').write_text(srt(cues),encoding='utf-8')
    attacks=[]
    for item in s.events:
        lo=item['frame']*FP;k=s.fx[lo:lo+FP];i=np.flatnonzero(np.max(np.abs(k),axis=1)>.00072)
        assert len(i) and i[0]<FP*(.36 if item['name'].endswith('_impact') else .80),(item['name'],i[:1]);attacks.append({**item,'transient_after_frame_ms':round(i[0]*1000/SR,3)})
    dump(QA/'mix.json',dict(samples=N,stereo=True,clip_stats=stats,pre_level=old,peak_limit_db=applied_db,
        verified_voice_id='voice-02',fresh_takes=locked,cues=cues,event_checks=attacks,
        source_credits=s.notes(),sha256=digest(path),voice_time_stretch=False))
    print('SHORT_MIX_READY',stats,len(cues),'phrases',len(attacks),'synced events',flush=True)

if __name__=='__main__':build()
