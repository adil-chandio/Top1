"""Narrated promo mix on the 1,020-frame clock. No source-film bus or time stretch."""
from hashlib import sha256
import json
import os
import sys

import numpy as np
from common import CACHE, FPS, FRAMES, HERE, SR, SPF, SAMPLES, WORK, QA

os.environ.setdefault('MONARCH_V2_CACHE',str(CACHE/'v2'))
sys.path.insert(0,str(HERE.parents[1]/'monarch-ant-v2'))
from mix import Bus, db, decode, envelope, excerpt, ff, gain, measure, ns, play, rms, wav

VOICE=json.loads((HERE/'voice.json').read_text())

# Picture anchors: first bite f8; antlion f207; suspended click f365; primary
# bite f475; rim f578 / landing 596; second bite f627; wall f690. Do not add a
# takeoff thump to the suspended snap, or a landing cue to a flight pose.
FOLEY=[
 (2,'breath of grit','sand-sweep',.29,1.28,-37.3,.15,3),
 (19,'first grit fan','gravel_07',.18,1.11,-34.6,.27,1),
 (53,'foot shifts','sand-step',.16,1.05,-38.5,-.24,0),
 (72,'tarsus pushes off','gravel_02',.132,1.19,-37.9,.18,0),
 (87,'feet drag with the slide','sand-sweep',.69,1.16,-33.5,-.19,2),
 (113,'grain passes the lens','gravel_08',.185,1.37,-32.1,.17,1),
 (123,'grain recedes','gravel_05',.20,1.18,-37.3,-.21,2),
 (151,'pit perspective','sand-sweep',.55,.88,-40.0,-.07,1),
 (207,'head flick','sand-step-alt',.24,1.10,-31.2,.16,0),
 (211,'arc of grit','sand-sweep',.51,1.31,-34.7,.34,0),
 (227,'grit settles','gravel_07',.21,.96,-36.2,-.27,0),
 (252,'front legs settle','sand-step',.18,.91,-37.6,.20,0),
 (277,'fine slide under the jaws','sand-sweep',.72,.93,-39.1,-.23,3),
 (437,'tarsus at contact setup','gravel_02',.18,.96,-39.0,-.22,0),
 (495,'sand separates','gravel_08',.24,1.15,-34.8,-.27,1),
 (531,'pass across the bowl','sand-sweep',.72,1.28,-37.0,.29,0),
 (596,'far side landing','sand-step-alt',.26,.96,-31.1,.20,0),
 (601,'the landing tail','gravel_02',.20,.90,-37.0,.29,0),
 (686,'wall approaches','sand-sweep',.22,1.12,-37.4,.26,1),
 (690,'short blunt wall contact','gravel_05',.26,.72,-26.9,.22,0),
 (692,'wall grains shake loose','sand-step-alt',.26,.83,-35.3,.13,0),
 (708,'slides back down','sand-sweep',.92,.92,-34.0,-.22,2),
 (735,'comes to rest','sand-step',.19,.85,-34.8,-.19,0),
 (776,'free jaw in paired study','snap-alt',.083,1.17,-37.7,.12,0),
 (923,'same trap sand tail','sand-sweep',1.21,.81,-39.0,.13,2),
 (1001,'grains before loop','sand-sweep',.61,.88,-38.6,-.16,1),
]
# Motion heard on small speakers: a restrained score with a gap around the air
# snap and no expository swell or ad sting at the last line.
SCORE=[
 (13,'cello','D3',4.8,-29.2,-.27),(36,'cello','A3',2.9,-33.0,.27),
 (52,'pizzicato_strings','D4',.71,-32.5,-.28),(91,'acoustic_grand_piano','A3',1.5,-31.2,.19),
 (131,'cello','Bb2',3.6,-32.0,-.29),(143,'cello','F3',3.0,-34.1,.29),
 (196,'acoustic_grand_piano','F4',1.95,-32.2,.18),(232,'pizzicato_strings','D4',.67,-34.6,-.18),
 (246,'cello','A2',3.2,-31.0,-.26),(291,'acoustic_grand_piano','E4',1.3,-33.0,.18),
 (390,'cello','A3',2.9,-33.0,-.22),(486,'cello','D3',3.2,-26.8,-.23),
 (496,'cello','A3',3.0,-30.0,.23),(511,'acoustic_grand_piano','F4',2.36,-29.6,-.15),
 (567,'acoustic_grand_piano','A4',1.9,-32.1,.24),
 (617,'cello','D3',2.87,-32.5,-.33),(647,'acoustic_grand_piano','Eb4',1.75,-33.3,.26),
 (733,'cello','G3',3.23,-33.5,.21),(762,'acoustic_grand_piano','Bb3',2.1,-33.5,-.21),
 (807,'pizzicato_strings','D4',.66,-36.6,.21),(826,'cello','A2',4.05,-30.0,-.23),
 (872,'acoustic_grand_piano','E4',2.80,-32.64,.20),(938,'acoustic_grand_piano','Bb3',2.7,-34.2,-.20),
 (991,'cello','A3',1.6,-34.1,.20),
]


def normalized_take(path, ranges):
    x=decode(path,af='highpass=f=78:p=2,lowpass=f=10800:p=2')
    r=np.concatenate([x[ns(a):ns(b)] for a,b in ranges]);hop=SR//100
    a=np.sqrt(np.mean(r[:len(r)//hop*hop].reshape(-1,hop)**2,axis=1))
    voiced=a[a>max(1.e-5,np.percentile(a,82)*.081)]
    assert len(voiced)>20 and np.max(np.abs(x))<.99
    x=x*(gain(-20.0)/rms(voiced))
    # Control short peaks, not the pacing or pitch from the selected read.
    z=ff('-loglevel','error','-f','f32le','-ar',SR,'-ac',1,'-i','pipe:0','-af',
        'acompressor=threshold=0.132:ratio=2.35:attack=6.6:release=76:knee=2.25:makeup=1',
        '-f','f32le','-',data=x.astype('<f4').tobytes())
    x=np.frombuffer(z.stdout,'<f4').copy(); high=np.abs(x)>.475
    x[high]=np.sign(x[high])*(.475+.094*np.tanh((np.abs(x[high])-.475)/.094))
    assert np.max(np.abs(x))<.57
    return x


def voice_bus():
    v=np.zeros(SAMPLES,dtype='f');ledger=[];takes={}
    for take in VOICE['take_text']:
        src=CACHE/'vo'/f'{take}.wav'
        ranges=[(e['in'],e['out']) for e in VOICE['edits'] if e['take']==take]
        takes[take]=(normalized_take(src,ranges),sha256(src.read_bytes()).hexdigest())
    end=0
    for e in VOICE['edits']:
        a=e['frame']*SPF;lo,hi=ns(e['in']),ns(e['out']);x,hash_=takes[e['take']]
        assert hi<=len(x) and a>=end and a+hi-lo<SAMPLES
        end=a+hi-lo;v[a:end]=envelope(x[lo:hi],.012,.025)
        ledger.append(dict(**e,src_samples=[lo,hi],mix_samples=[a,end],take_sha256=hash_))
    return v,ledger


def make_srt():
    def t(x):
        ms=round(x*1000);s,m=divmod(ms,1000);mn,s=divmod(s,60);h,mn=divmod(mn,60)
        return f'{h:02}:{mn:02}:{s:02},{m:03}'
    s='';last=0
    for j,(a,b,text) in enumerate(VOICE['captions'],1):
        assert last<=a<b<FRAMES/FPS
        s+=f'{j}\n{t(a)} --> {t(b)}\n{text}\n\n';last=b
    return s


def build():
    WORK.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    voice,led=voice_bus();score=Bus(SAMPLES);fx=Bus(SAMPLES);cues=[]
    for f,inst,note,d,level,pan in SCORE:
        play(score,inst,note,f/FPS,d,level,pan,1.)
    def spot(f,title,src,d,rate,level,pan,seed=0,attack=None,hi=None):
        x=excerpt(src,d,rate,129 if 'wall' in title else 152,hi or (3250 if 'sand' in src else 3890),
                  seed=seed,attack=attack or (.052 if src=='sand-sweep' else .005),release=min(d*.44,.12))
        g=min(gain(level)/(rms(x[:min(len(x),ns(.29))])+1.e-8),.295/(np.max(np.abs(x))+1.e-8))
        fx.add(x,f/FPS,g,pan);cues.append(dict(frame=f,name=title,recording=src,sample=round(f*SPF)))
    for cue in FOLEY:spot(*cue)
    spot(365,'air snap / no substrate','soft-snap',.109,1.19,-29.9,-.09,attack=.002,hi=4650)
    for j,(f,pan,loud) in enumerate([(8,.28,1.7),(475,-.26,0.),(627,-.24,-1.8)]):
        spot(f,'sand snap / jaw contact','soft-snap',.121,1.11,-28.6+loud,pan,attack=.0018,hi=4500)
        spot(f+.26,'contact grain cluster','sand-step',.20,.88,-29.9+loud,pan*.75,attack=.004,hi=3520)
        spot(f+1.45,'small sand fan','sand-sweep',.56,1.26,-35.2+loud,pan*.7,j,attack=.028,hi=3250)
    ctl=[(0,.50),(18,.65),(73,.69),(134,.70),(206,.59),(241,.79),(291,.53),(347,.18),(356,.047),
         (376,.067),(393,.48),(448,.44),(469,.18),(479,.24),(491,.79),(526,.93),(589,.63),(613,.54),
         (671,.48),(684,.15),(702,.22),(726,.48),(745,.64),(782,.57),(837,.63),(927,.57),(959,.63),(985,.77),(1020,.39)]
    times=np.arange(SAMPLES)/SPF
    score.y*=np.interp(times,*np.asarray(ctl).T).astype('f')[:,None]
    vo=np.repeat(voice[:,None],2,axis=1)*np.float32(.84)
    bus=vo+fx.y+score.y
    bus*=envelope(np.ones(SAMPLES,dtype="f"),.017,.045)[:,None]
    assert bus.shape==(SAMPLES,2) and np.max(np.abs(bus))<.93
    tmp=WORK/'mix-untrimmed.wav';dest=WORK/'short-mix.wav'
    wav(bus,tmp);a=measure(tmp)
    # A single output trim keeps perspective and modest headroom for AAC.
    g=min(-16.45-a['LUFS_I'],-2.30-a['dBTP']);y=(bus*gain(g)).astype('f');wav(y,dest)
    m=measure(dest); assert -20.8<m['LUFS_I']<-14.3 and m['dBTP']<=-2.2,m
    alias=WORK/'short.en.srt';alias.write_text(make_srt())
    proof=dict(voice=VOICE['voice'],dialogue_edits=led,sources=VOICE['take_text'],spotting=sorted(cues,key=lambda z:z['frame']),
               samples=SAMPLES,sample_rate=SR,trim_db=round(g,4),meter=m,
               dialogue_rms_db=round(db(rms(vo)),2),score_rms_db=round(db(rms(score.y)),2),
               effects_rms_db=round(db(rms(fx.y)),2),sha256=sha256(dest.read_bytes()).hexdigest())
    (QA/'mix.json').write_text(json.dumps(proof,indent=2)+'\n')
    tmp.unlink();print(f'SHORT_MIX_READY {m} · {SAMPLES} samples per channel',flush=True)


if __name__=='__main__':build()
