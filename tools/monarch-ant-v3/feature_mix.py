"""Mix the entire V3 feature around fresh picture pins and the approved VO."""
from math import pi
import json
import numpy as np

from pilot import FPS, SR, LEVEL, WORK as PILOT, SPF
from feature_cut import WORK, QA, META, ANCHORS
from mix import Bus, apply_envelope, band, db, decode, envelope, excerpt, gain, measure, native_vo, ns, peak_duck, play, rms, rms_blocks, wav
from pilot_mix import INST, synth_hit

# Use the same PCHIP picture clock as render.cpp, then invert the curve for Foley.
def clock_at(seq, f):
    ds=[(b[1]-a[1])/(b[0]-a[0]) for a,b in zip(seq,seq[1:])]
    for i,((j,a),(k,b)) in enumerate(zip(seq,seq[1:])):
        if f<=k: break
    def tangent(i):
        if i==0 or i==len(ds): return ds[0 if i==0 else -1]
        x,y=seq[i][0]-seq[i-1][0],seq[i+1][0]-seq[i][0]
        return 3*(x+y)/((x+2*y)/ds[i-1]+(2*x+y)/ds[i])
    w=k-j;q=(f-j)/w;r=q*q;s=r*q
    return (2*s-3*r+1)*a+(s-2*r+q)*w*tangent(i)+(-2*s+3*r)*b+(s-r)*w*tangent(i+1)


def at(shot, t):
    seq=[(shot['first'],shot['src'][0]),*shot['pins'],(shot['end']-1,shot['src'][1])]
    for f,v in seq:
        if abs(t-v)<1e-7:return float(f)
    if not seq[0][1]<=t<=seq[-1][1]:return None
    l,h=seq[0][0],seq[-1][0]
    for _ in range(25):
        m=(l+h)*.5
        if clock_at(seq,m)<t:l=m
        else:h=m
    return .5*(l+h)


# Sparse score written to chapter language: tension -> question -> reply. Within
# each air/ground comparison the unsupported close never gets the release chord.
# Absolute frames, low sustain, upper gestures offset in frames (not shareable loops).
MUSIC = [
 (725,'D3 A3','F4:37 E4:108 A3:193'), (915,'Bb2 F3','D4:51 A3:114'),
 (1104,'G3 D4','D4:48 p:C4:158 F4:235'), (1371,'D3 F3','C4:50 A3:136'),
 (1596,'A3 E3','C4:71 p:A3:226'), (1875,'G3 D4','F4:36 E4:143'), (2034,'A2 E3','C4:47'),
 (2206,'D3 A3','D4:35 p:F3:93'), (2343,'A2 E3','p:D3:63 A3:165'),
 (2536,'Bb2 F3','E4:66 F4:163'), (2741,'D3 F3','A3:43 E4:147'),
 (2918,'F3 C4','A3:51 p:F3:168'), (3139,'A2 E3','D4:65'), (3311,'D3 A3','F4:90 E4:136'),
 (3513,'G3 Bb3','D4:57 C4:111'),
 (3730,'D3 F3','A3:75 D4:171'), (3934,'A2 E3','p:D3:105'),
 (4095,'Bb2 F3','F4:58'), (4308,'D3 A3','A3:58 E4:164'),
 (4520,'F3 C4','F4:81 A4:175 E4:246'), (4809,'G3 D4','Bb3:59 A3:156'),
 (5023,'A2 D3','C4:57'),
 (5188,'D3 A3','p:F3:43'), (5360,'Eb3 Bb3','D4:54 A3:124'),
 (5557,'G3 Bb3','Eb4:95'), (5682,'Bb2 F3','p:F3:76 A3:149 p:D4:256'),
 (5950,'G3 D4','Bb3:44 A3:148'), (6151,'Eb3 Bb3','G4:78 Eb4:215'),
 (6398,'A2 D3','D4:58 p:D3:161'),
 (6672,'F3 C4','A3:72 C4:196'), (6907,'G3 D4','p:D4:54 A3:217'),
 (7140,'Bb2 F3','D4:79 F4:158'), (7325,'A2 E3','A3:58 p:F3:151'),
 (7537,'D3 F3','A3:41 F4:148'), (7751,'F3 C4','E4:55 A3:153'),
 (7982,'D3 A3','D4:64 A3:118'), (8182,'Bb2 F3','F4:50 D4:92'),
 (8311,'G3 D4','C4:77 A3:202'), (8512,'F3 C4','F4:45 A4:103'),
 (8656,'A2 E3','D4:41 A3:112'), (8884,'D3 F3 A3','D4:16 A3:44'),
]

# Close editorial spot accents. Quantitative labels get light felt detents, not
# victory ticks. Physical contacts below get separate prepared recordings.
EDIT = [
 (755,'topography mark','gravel_07',-.29,-47.,.21,1.1), (858,'rim diagram','sand-sweep',.11,-44.,.58,.95),
 (916,'identify larva','gravel_02',-.40,-46.,.19,1.19), (1238,'rising fan','sand-sweep',.30,-40.3,.61,1.25),
 (1307,'sand comes down','sand-step-alt',-.23,-41.,.26,.98), (1419,'sliding layer','sand-sweep',.16,-41.6,.88,.91),
 (1708,'slope graphic settles','gravel_05',-.25,-45.,.19,.92),
 (2354,'small latch detent','snap-alt',.22,-43.7,.091,1.10), (2406,'into the cutaway','sand-sweep',.20,-45.,.42,.9),
 (2490,'load rises','sand-sweep',-.28,-46.,.66,.88), (2555,'shell flex mark','gravel_02',.20,-46.,.13,1.07),
 (2650,'tensed attachment','sand-sweep',.33,-47.,.46,1.16), (2727,'schematic release','soft-snap',-.19,-40.,.091,1.24),
 (2921,'push contact marker','gravel_07',.10,-45.4,.13,1.18), (3078,'pull marker','gravel_02',-.17,-45.8,.13,1.23),
 (3387,'timing mark','snap-alt',.20,-45.,.073,1.26), (3403,'light high-speed detail','soft-snap',.20,-44.6,.091,1.23),
 (3794,'macro tarsus','sand-step',-.31,-39.8,.16,1.11), (4023,'tarsus unloads','gravel_05',.26,-42.2,.13,.94),
 (4180,'unsupported air snap','snap-alt',.15,-37.2,.108,1.18),
 (4474,'grains pass macro','gravel_08',.29,-37.5,.25,1.02), (4481,'quartz slides past','sand-sweep',-.01,-40.3,.71,1.21),
 (4592,'body leaves surface','sand-sweep',.25,-43.0,.70,1.15), (4738,'far side landing','sand-step-alt',.38,-37.4,.225,.91),
 (5318,'wall approach, no swell','sand-sweep',.30,-44.6,.38,.90),
 (5325,'wall, dull grain cluster','gravel_05',.34,-34.2,.218,.82),
 (5325.31,'wall, dry settled layer','sand-step-alt',.28,-41.0,.30,.87),
 (5361,'sand follows her down','sand-sweep',-.13,-38.0,1.12,.80), (5405,'falls back into sand','gravel_07',-.10,-41.,.24,.91),
 (5660,'lab total felt click','gravel_02',-.23,-48.,.110,1.22), (5752,'running row','gravel_08',-.25,-46.,.137,.99),
 (5811,'jump row','gravel_07',.14,-46.,.13,1.03), (5910,'caught row','gravel_05',.21,-47.4,.14,.94),
 (6489,'condition cut','sand-sweep',.19,-47.8,.61,.98), (6926,'three conditions line','gravel_02',0.,-47.,.13,1.18),
 (7367,'compare like with like','gravel_08',-.21,-45.5,.17,1.18),
 (7482,'two handled group bracket','gravel_07',.15,-45.1,.18,1.11), (7671,'added escape route','sand-sweep',.18,-43.0,.54,1.17),
 (8092,'grit slips in reprise','sand-sweep',-.26,-39.8,.71,.90),
 (8223,'the spot empties','sand-sweep',.24,-41.8,.72,1.04), (8388,'sand goes up','gravel_05',-.18,-39.2,.20,1.09),
 (8519,'ant goes up','sand-sweep',.22,-42.8,.69,1.17),
 (8723,'ground remains moving','sand-sweep',-.24,-43.0,.93,.84),
 (8890,'the bowl settles','sand-sweep',.05,-43.7,1.46,.86),
]
SPECIAL = {4297:1.0, 5267:.77, 7636:.54, 8186:.83, 8492:.55, 8873:1.}


def voice(m):
    v=np.zeros(m['frames']*SPF,dtype=np.float32);full=native_vo()
    for lo,hi,dst in m['vo_ranges']:
        v[dst:dst+hi-lo]=full[lo:hi]*LEVEL
    return v


def build():
    m=json.loads(META.read_text()); v=voice(m); n=len(v); fx=Bus(n); sc=Bus(n);ledger=[]; notes=[]
    def add(frame,name,src,d,speed,pan,level, lo=175, hi=3000, attack=.009, cap=.115, seed=0):
        ix=round(frame*SPF)
        x=excerpt(src,d,speed,lo,hi,seed=seed,attack=attack,release=min(d*.49,.185))
        count=min(len(x),ns(.43))
        g=min(gain(level)/max(1e-6,rms(x[:count])),cap/(np.max(np.abs(x))+1e-6))
        fx.add(x,ix/SR,g,pan)
        ledger.append(dict(frame=frame,sample=ix,cue=name,recording=src,duration_s=d,pan=pan,level=round(db(g*rms(x[:count])),3)))
    for i,(f,label,rec,pan,level,d,speed) in enumerate(EDIT):
        add(f,label,rec,d,speed,pan,level,hi=2640 if 'wall' in label else 3070,
            attack=.063 if 'sweep' in rec else .005,cap=.164 if f==5325 else .114,seed=i)
    impactbody=synth_hit()
    for ix,(frame,w) in enumerate(SPECIAL.items()):
        p=(-.31,.24,.21,-.12,.24,.37)[ix]
        s='soft-snap' if ix%2==0 else 'snap-alt'
        lab=f'ground contact {frame}'
        add(frame,lab,s,.106,1.04 if ix%2==0 else .92,p,-30.5+db(w),155,3320,.0018,cap=.18*w,seed=ix)
        add(frame+.30,lab+' / local grains','sand-step',.218,1.12,p*.9,-35.4+db(w),192,2990,.008,.128*w,ix)
        add(frame+1.07,lab+' / sand tail','sand-sweep',.569,1.17,p*.9,-40.0+db(w),197,2740,.045,.107*w,ix)
        fx.add(impactbody,(frame+.17)/FPS,.023*w,p*.22)
    for idx,q in enumerate(m['shots']):
        if q['beat']==1: continue
        mode=q['mode'];h=q['subject']; p=0.21 if q['camera'] in (52,55,69,72,79,81) else -.19
        def mark(t):return at(q,t)
        if mode in (0,1,4,9,11,13):
            if mode==1 or mode==11:
                ts=(.22,.57,.83,1.21,1.52,1.88,2.18,2.45,2.71,3.25,3.66,4.06,4.48,4.91)
            elif mode in (9,13):ts=(.16,.48,.83,1.21,1.57,1.89)
            else:ts=(2.96,3.13,5.56)
            last=-100
            for j,t in enumerate(ts):
                f=mark(t)
                if f is None or f-last<17 or any(abs(f-c)<9 for c in SPECIAL) or (5180<f<5418):continue
                sample=('sand-step','gravel_02','sand-step-alt','gravel_07')[(idx+j)%4]
                add(f,'tarsus / '+h,sample,.151, .96+.12*(j%3), p,-42.2+(1.6 if mode==11 else 0), 208,3020,.009,.086,idx+j)
                last=f
        if mode==3:
            for t in (.38,1.41,2.56,6.05,8.24,10.5,12.3):
                f=mark(t)
                if f is None:continue
                add(f,'larva flick / '+h,'gravel_05',.197,.95,p,-37.7,174,3070,.006,.125,idx)
                add(f+1.41,'flicked sand / '+h,'sand-sweep',.68,1.19,-p*.66,-40.5,218,2920,.032,.105,idx)
        if mode in (2,8,10,21,23):
            f=q['first']+min(47,(q['end']-q['first'])*.47)
            if f<8945:add(f,'moving bank / '+h,'sand-sweep',.88,.85+.08*(idx%4),p*.46,-45.,155,2330,.14,.082,idx)
        if mode==15:
            for t in (2.38,4.43,7.54,9.):
                f=mark(t)
                if f is not None:add(f,'mock-treatment rig snap','snap-alt',.098,1.16,-.27,-43.0,330,2670,.006,.079,idx)
    for i,(f,bass,score) in enumerate(MUSIC):
        stop=MUSIC[i+1][0] if i+1<len(MUSIC) else 9015
        for j,note in enumerate(bass.split()):
            start=f+j*9; dur=max(.58,(stop-start)/FPS+.53)
            level=-37.6-j*2.0
            play(sc,INST['cello'],note,start/FPS,dur,level,(-.26,.32,.04)[j],1.)
            notes.append([start,'cello',note,dur,level])
        for line in score.split():
            data=line.split(':'); instr='pizz' if len(data)==3 else 'piano';tone,offset=data[-2:];at_f=f+int(offset)
            d=.91 if instr=='pizz' else (2.40 if i%3 else 3.01)
            level=-39.4 if instr=='pizz' else -36.6 + (i%3-1)*.60
            play(sc,INST[instr],tone,at_f/FPS,d,level,-.28+(i%5)*.14,1.)
            notes.append([at_f,instr,tone,d,level])
    duck=peak_duck(v);t=np.arange(len(duck),dtype=np.float64)*.02*FPS
    score_ctl=np.ones(len(t));fx_ctl=np.ones(len(t))
    for f,inw,outw,low in [(2411,19,28,.45),(2727,39,48,.15),(3403,25,42,.38),(4180,25,34,.13),
         (4297,48,37,.054),(5267,44,122,.065),(5325,34,75,.035),(7636,27,43,.22),(8186,24,52,.15),
         (8492,23,48,.22),(8873,51,42,.048)]:
        score_ctl=np.minimum(score_ctl,np.interp(t,[f-inw,f-5,f+5,f+outw],[1,low,low,1]))
    for f in (4297,5267,7636,8186,8492,8873):
        dip=np.interp(t,[f-27,f-12,f-1,f+2],[1,.66,.57,1]);fx_ctl=np.minimum(fx_ctl,dip)
    # The final word and the last contact share a beat. Keep the transient,
    # then drop the grit tail under the end of "bite", not the locked voice.
    fx_ctl=np.minimum(fx_ctl,np.interp(t,[8873,8874.5,8875.6,8884,8889],[1,1,.44,.44,1]))
    apply_envelope(sc.y,score_ctl*(1.-.66*duck),SR//50);apply_envelope(fx.y,fx_ctl*(1.-.26*duck),SR//50)
    final=ns(.91)
    fade=np.cos(np.linspace(0,pi/2,final,dtype=np.float32))**2
    for b in (sc,fx):b.y[-final:]*=fade[:,None]
    a=v[:,None]+fx.y+sc.y
    # The established first movement is the approved PCM mix; not AAC-to-AAC.
    first=ANCHORS[1]*SPF
    for bus,src in [(a,'v3-mix.wav'),(fx.y,'v3-foley.wav'),(sc.y,'v3-score.wav')]:
        y=decode(PILOT/src,2); assert y.shape==(first,2)
        bus[:first]=y
    assert np.isfinite(a).all() and np.max(np.abs(a))<.81
    wav(a.astype(np.float32),WORK/'feature-mix.wav');wav(fx.y,WORK/'feature-foley.wav');wav(sc.y,WORK/'feature-score.wav')
    B=ns(.12);vr=rms_blocks(v,B);bed=rms_blocks((sc.y+fx.y).mean(axis=1),B)
    i=vr>gain(-37.); perc=np.percentile(20*np.log10(np.maximum(bed[i]/vr[i],1e-8)),[50,90,95,99]);
    stat=dict(premix=measure(WORK/'feature-mix.wav'),vo_gain_db=db(LEVEL),
              active_bed_percentiles={str(k):float(y) for k,y in zip([50,90,95,99],perc)},spot_layers=len(ledger),score_notes=len(notes),samples=n)
    (WORK/'feature-spotting.json').write_text(json.dumps(dict(foley=sorted(ledger,key=lambda x:x['frame']),score=notes),indent=1)+'\n')
    (QA/'feature-mix.json').write_text(json.dumps(stat,indent=2)+'\n')
    print(json.dumps(stat,indent=2))
    assert -21.4<stat['premix']['LUFS_I']<-18.6 and stat['premix']['dBTP']<-2.8
    assert perc[2]<-12.3
    print('FEATURE_MIX_READY',flush=True)


if __name__=='__main__':build()
