"""Short V2: tight phrase edits, forward VO, separate moving texture & pulse.

No V1 soundtrack reused, no pitch change, no turning up unfilled gaps. The
forced aligner times known words, it does not invent/transcribe dialogue.
"""
from hashlib import sha256
import json
import os
import re
import sys
import tempfile

import numpy as np
from pocketsphinx import Decoder

from layout import BASE,CACHE,HERE,WORK,QA,FRAMES,FPS,SR,SPF,SAMPLES
os.environ.setdefault('MONARCH_V2_CACHE',str(BASE/'v2'))
sys.path.insert(0,str(HERE.parents[1]/'monarch-ant-v2'))
from mix import Bus,apply_envelope,band,db,decode,envelope,excerpt,ff,gain,measure,ns,peak_duck,play,rms,rms_blocks,wav

STORY=json.loads((HERE/'story.json').read_text())
WORDS=re.compile(r"[a-z]+(?:'[a-z]+)?")


def aligned(path,phrases):
    words=[WORDS.findall(x.lower()) for x in phrases];written=[w for ws in words for w in ws]
    d=Decoder(samprate=16000,loglevel='ERROR');d.add_word('antlion','AE N T L AY AH N',False)
    assert all(d.lookup_word(t) for t in written),[t for t in written if not d.lookup_word(t)]
    d.set_align_text(' '.join(written));d.start_utt()
    raw=ff('-loglevel','error','-i',path,'-vn','-ar','16000','-ac','1','-f','s16le','-').stdout
    d.process_raw(raw,False,True);d.end_utt()
    s=[(w.word.split('(')[0],w.start_frame*.01,(w.end_frame+1)*.01) for w in d.seg() if not w.word.startswith(('<','['))]
    assert [w[0] for w in s]==written,(s,written)
    i=0;cuts=[]
    for j,ws in enumerate(words):
        last=i+len(ws)-1;cuts.append(dict(text=phrases[j],st=s[i][1],en=s[last][2],words=s[i:last+1]));i=last+1
    return cuts


def processor(a,af,channels):
    p=ff('-loglevel','error','-f','f32le','-ar',SR,'-ac',channels,'-i','pipe:0','-af',af,'-f','f32le','-',data=a.astype('<f4').tobytes())
    b=np.frombuffer(p.stdout,dtype='<f4').copy()
    return b if channels==1 else b.reshape(-1,channels)


def take(k,t):
    src=CACHE/'vo'/f"{t['take']}.wav";cues=aligned(src,t['phrases'])
    lo,hi=t['trim'];drop=t['tighten']; x=decode(src,af='highpass=f=76:p=2,lowpass=f=11300:p=2,equalizer=f=2630:t=q:w=1.16:g=1.5')
    arp=[];quiet=[];cur=lo
    for a,b in drop:
        assert lo<=cur<a<b<hi
        y=x[ns(a):ns(b)];v=db(rms(y));quiet.append(round(v,2));assert v<-51,(t['take'],a,b,v)
        arp.append((cur,a));cur=b
    arp.append((cur,hi));clips=[envelope(x[ns(a):ns(b)],.007,.009) for a,b in arp]
    n=np.concatenate(clips);lev=rms_blocks(n,SR//100);sp=lev[lev>max(1.e-5,np.quantile(lev,.81)*.073)]
    assert .71<len(sp)/len(lev)<1 and 0.001<rms(sp)<.37,(t['take'],len(sp)/len(lev))
    n=n*(gain(-17.55+(0.36 if k==0 else 0.))/rms(sp))
    n=processor(n,'acompressor=threshold=0.112:ratio=3.05:attack=5.5:release=67:knee=2.4:makeup=1',1)
    over=np.abs(n)>.45
    n[over]=np.sign(n[over])*(.45+.106*np.tanh((np.abs(n[over])-.45)/.106))
    def map_time(u):
        s0=max(lo,min(hi,u));return (ns(s0)-ns(lo)-sum(max(0,min(ns(b),ns(s0))-ns(a)) for a,b in drop))/SR
    for q in cues:
        q['st']=map_time(q['st']);q['en']=map_time(q['en']);q['words']=[[w,map_time(a),map_time(b)] for w,a,b in q['words']]
    return n,cues,dict(take=t['take'],sha256=sha256(src.read_bytes()).hexdigest(),cut_silence_rms_db=quiet,source_ranges=arp)


def runs(a,flag=True):
    mask=np.asarray(a,dtype=bool) if flag else ~np.asarray(a,dtype=bool)
    d=np.flatnonzero(np.diff(np.r_[False,mask,False]));return [(int(l),int(h)) for l,h in zip(d[::2],d[1::2])]


def vo_edit():
    v=np.zeros(SAMPLES,'f');ends=[];all_=[];a=ns(.003)
    for i,t in enumerate(STORY['takes']):
        n,cs,info=take(i,t);b=a+len(n)
        assert a<b<=len(v),(a,b,len(v));v[a:b]=n
        info['mix_samples']=[a,b];ends.append(info)
        for q in cs:
            q['start']=q.pop('st')+a/SR;q['end']=q.pop('en')+a/SR
            q['words']=[[w,lo+a/SR,hi+a/SR] for w,lo,hi in q['words']];all_.append(q)
        a=b+ns([.043,.061,.050,.047,.049,.0][i])
    assert 33.70<a/SR<34
    # 10ms windows, tracked independently of the Foley and score. The user
    # complained about the gaps in the narration, not merely muted samples.
    r=rms_blocks(v,SR//100);z=r>gain(-48);g=runs(z,False)
    longest=max(b-a for a,b in g)/100;first=float(np.flatnonzero(z)[0]/100);last=float((np.flatnonzero(z)[-1]+1)/100)
    assert first<=.075 and last>=33.50 and longest<=.56,(first,last,longest,g)
    for i,q in enumerate(all_):
        # Phrase cards get a tiny visual lead, never ahead of the previous word.
        end=all_[i+1]['start'] if i+1<len(all_) else min(33.97,q['end']+.12)
        q['display_start']=round(max(0,q['start']-.04 if not i else max(all_[i-1]['end'],q['start']-.035)),3)
        q['display_end']=round(min(end+.02,max(q['end']+.095,q['display_start']+.40)),3)
    for a,b in zip(all_,all_[1:]):a['display_end']=min(a['display_end'],b['display_start'])
    assert all(q['display_end']-q['display_start']>.31 for q in all_)
    return v,ends,all_,dict(first_vo_s=first,last_vo_s=last,max_voice_gap_s=longest,voice_windows_above_minus48db=int(np.count_nonzero(z)))

# Film accents, not stock effects. Frames are output anchors rather than guessed
# from an earlier edit: 5 / 328 / 439 / 644 / 696 / 790.
FOLEY=[
 (0,'sand against the slope','sand-sweep',.69,.96,-32.2,-.17,3),
 (17,'grit fan opens','gravel_08',.165,1.14,-31.0,.26,0),
 (37,'upward takeoff tail','sand-sweep',.61,1.29,-34.7,.22,1),
 (64,'first foot loses purchase','sand-step',.182,1.13,-30.1,-.21,0),
 (88,'toe searches for grip','sand-step-alt',.16,.94,-33.0,.24,0),
 (99,'shear below the foot','sand-sweep',.78,.84,-31.8,-.20,2),
 (116,'pull across bowl','sand-sweep',.46,.92,-36.2,.18,3),
 (155,'sand falls into basin','gravel_07',.20,.74,-36.8,.16,0),
 (194,'antlion flick','sand-step-alt',.24,1.13,-26.7,.17,0),
 (196,'antlion grit cascade','sand-sweep',.72,1.17,-30.2,.26,1),
 (215,'bouncing individual grain','gravel_05',.18,1.23,-33.1,.12,0),
 (232,'sand shears under the worker','sand-sweep',1.04,.93,-30.8,-.23,0),
 (252,'sliding step','gravel_02',.21,1.15,-34.7,-.13,1),
 (410,'foreleg pressure','sand-step',.22,.88,-33.8,.24,0),
 (455,'grain rush','sand-sweep',.54,1.24,-31.5,.18,3),
 (497,'soft whoosh of grit, not wind','sand-sweep',.65,1.48,-35.0,-.24,1),
 (552,'grain trail dissolves','gravel_08',.20,1.13,-36.9,-.17,1),
 (626,'rim grains scatter','sand-sweep',.66,1.17,-36.9,.30,2),
 (644,'far side touchdown','sand-step-alt',.26,.95,-28.6,.19,0),
 (647,'stone tarsus release','gravel_02',.19,.87,-35.2,.22,0),
 (669,'second wingless flight','sand-sweep',.55,1.26,-33.1,-.15,3),
 (696,'dull wall clip','gravel_05',.254,.77,-24.5,.29,0),
 (698,'wall moves under the ant','gravel_07',.225,.84,-31.1,.16,0),
 (715,'fall back into the bowl','sand-sweep',1.15,.82,-30.0,-.20,1),
 (744,'settle back in sand','sand-step',.26,.93,-31.0,-.23,0),
 (790,'unrestrained snap on study plate','snap-alt',.103,1.19,-32.5,-.21,1),
 (848,'lab focus pull','gravel_02',.149,1.22,-40.3,.19,0),
 (935,'pit returns under the question','sand-sweep',1.22,.84,-32.0,-.12,2),
 (983,'pre-strike sand texture','sand-sweep',1.39,.90,-33.8,.20,3),
]


def score(c):
    # Articulated motif and sustained harmony cover the whole run without a
    # weaponized bass drop/pause. Cello and clock are always below the voice.
    chords=[(0,'D3 A3','D3 A3 F3 A3'),(122,'Bb2 F3','F3 D4 F3 Bb3'),(265,'G3 D4','G3 D4 Bb3 D4'),
            (391,'A2 E3','E3 A3 E4 A3'),(494,'D3 A3','D3 A3 F4 A3'),(611,'F3 C4','F3 C4 A3 C4'),
            (663,'Eb3 Bb3','Eb3 Bb3 G3 Bb3'),(742,'A2 E3','A2 E3 C4 E3'),(856,'D3 F3','D3 F3 A3 E4'),
            (939,'A2 E3','A2 E3 Bb3 E3')]
    for i,(f,ch,pulse) in enumerate(chords):
        end=chords[i+1][0] if i+1<len(chords) else FRAMES
        for j,t in enumerate(ch.split()):play(c,'cello',t,max(0,f-9+4*j)/FPS,(end-f)/FPS+.47,-28.5-2.8*j,(-.26,.29)[j],.95)
        notes=pulse.split()
        for j,n in enumerate(range(f+5,end,15 if i in (0,1,4,6) else 16)):
            if 319<=n<=337 or 695<=n<=710:continue
            play(c,'pizzicato_strings',notes[j%len(notes)],n/FPS,.73,-29.4+(j%4==0)*1.9,-.28+.142*(j%5),1.)
        for j,n in enumerate(range(f+31,end,57)):
            play(c,'acoustic_grand_piano',notes[(j+2)%len(notes)],n/FPS,1.36,-31.3,-.26+.35*(j%2),.98)
    # Soft, short tuned pressure pulses translate on a phone; no canned beat.
    t=np.arange(ns(.33),dtype='f')/SR
    h=np.sin(2*np.pi*(78*t+1.9*(1.-np.exp(-t*17.))))*.72+np.sin(2*np.pi*159*t)*.28
    h=envelope((h*np.exp(-t*15)).astype('f'),.008,.058)
    for f in (5,36,65,94,123,153,185,210,240,272,302,357,388,416,445,475,502,533,565,597,628,660,685,729,758,789,819,852,883,913,945,976,1006):
        c.add(h,f/FPS,gain(-28.5 if f in (5,240,445,660,758,945) else -32.3),.0)


def ground_tone():
    # Deliberate low granular ground tone, not broadband hiss; downmix-safe.
    bed=Bus(SAMPLES)
    rng=np.random.default_rng(3401020)
    noise=rng.normal(0,1,SAMPLES).astype('f');lo=np.linspace(0.,FRAMES/FPS,SAMPLES,endpoint=False)
    x=band(noise,108,1220)*(.77+.16*np.sin(lo*2.73)+.07*np.sin(lo*5.48+.4)).astype('f')
    bed.add(x,0,gain(-41.2)/rms(x),.06)
    return bed.y


def ride_score(y,duck):
    apply_envelope(y,1.-duck*.28,480)
    points=np.array([(0,.95),(19,1.05),(270,.89),(313,.72),(329,.48),(354,.68),(393,.80),(437,.67),(465,1.02),
                     (662,.85),(693,.64),(709,.83),(758,.99),(843,.88),(913,.83),(951,.92),(1020,.86)])
    y*=np.interp(np.arange(SAMPLES)/SPF,*points.T).astype('f')[:,None]


def caps_srt(c):
    def ts(v):
        a,b=divmod(round(v*1000),1000);m,s=divmod(a,60);return f'00:{m:02}:{s:02},{b:03}'
    return ''.join(f"{i}\n{ts(q['display_start'])} --> {ts(q['display_end'])}\n{q['text']}\n\n" for i,q in enumerate(c,1))


def build(*, stems_only=False):
    """Build the original V2 mix, or return its unmixed buses for later remixes."""
    WORK.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    v,takes,caps,pace=vo_edit();vox=np.repeat(v[:,None],2,axis=1)*np.float32(.91)
    fx=Bus(SAMPLES);m=Bus(SAMPLES);spots=[]
    def spot(f,label,name,length,speed,db_,pan,seed):
        x=excerpt(name,length,speed,114 if 'wall' in label else 146,4400 if 'snap' in name else 3580,
                  seed=seed,attack=.0022 if 'snap' in name else (.062 if name=='sand-sweep' else .009),release=min(length*.4,.126))
        g=min(gain(db_)/(rms(x[:ns(min(length,.24))])+1e-9),.27/(np.max(np.abs(x))+1e-9))
        fx.add(x,f/FPS,g,pan);spots.append(dict(frame=f,name=label,source=name,sample=round(f*SPF)))
    for spot0 in FOLEY: spot(*spot0)
    for j,(f,pan) in enumerate([(5,.30),(439,-.19)]):
        spot(f,'jaw / sand contact','soft-snap',.114,1.13,-24.9,pan,j)
        spot(f+.30,'sand contact grains','sand-step',.205,.86,-27.8,pan,j)
        spot(f+1.08,'sand burst','sand-sweep',.56,1.31,-32.0,pan*.81,j)
    spot(328,'jaw in air without the sand tail','soft-snap',.103,1.26,-26.7,-.15,0)
    room=ground_tone()
    score(m)
    duck=peak_duck(v,480);ride_score(m.y,duck);apply_envelope(fx.y,1.-duck*.13,480)
    if stems_only:
        return dict(voice=vox, mono_voice=v, score=m.y, effects=fx.y, bed=room,
                    takes=takes, captions=caps, pace=pace, spots=spots)
    y=vox+m.y+fx.y+room
    # Closing word ends under texture, not a dead/faded-to-black second.
    y*=envelope(np.ones(SAMPLES,'f'),.004,.020)[:,None]
    f=WORK/'mix-pre.wav';wav(y,f);meter=measure(f)
    y*=gain(np.clip(-14.95-meter['LUFS_I'],-1,6.2))
    z=processor(y,'alimiter=limit=0.755:attack=4:release=71:level=false:latency=true',2)
    assert z.shape==y.shape,(z.shape,y.shape)
    # Require aligned AAC master, not a limiter-induced frame of delay.
    sim=float(np.corrcoef(y.ravel(),z.ravel())[0,1]);assert sim>.995,sim
    dest=WORK/'short-v2-mix.wav';wav(z,dest);mp=measure(dest);f.unlink()
    gaps=runs(rms_blocks(z.mean(axis=1),SR//100)>gain(-51),False)
    for a,b in gaps:assert b-a<=8,(a,b)
    assert -16.1<mp['LUFS_I']<-14.0 and mp['dBTP']<-1.45,mp
    (WORK/'captions.json').write_text(json.dumps(caps,indent=2)+'\n');(WORK/'short-v2.en.srt').write_text(caps_srt(caps))
    proof=dict(meter=mp,**pace,final_mix_floor=-51,final_mix_gap_max_s=max((b-a for a,b in gaps),default=0)/100,
               takes=takes,frames=FRAMES,samples=SAMPLES,voice_id=STORY['voice_id'],spot=sorted(spots,key=lambda q:q['frame']),
               mix_sha256=sha256(dest.read_bytes()).hexdigest(), limiter_corr=sim)
    (QA/'mix.json').write_text(json.dumps(proof,indent=2)+'\n');print(mp,pace,'max mix gap',proof['final_mix_gap_max_s'],flush=True)
    for q in caps:print(f"{q['display_start']:06.3f} {q['display_end']:06.3f}  {q['text']}")


if __name__=='__main__':build()
