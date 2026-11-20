"""Conform Monarch Cam's V3 film Foley to the locked 34-second Short V2 picture.

No feature movie audio is sampled. Use the film's licensed, pinned recordings,
processing, positive-contact layers and dry-impact vocabulary on the Short's
actual frame marks. Preserve the existing VO samples and copy only the video
track from the verified Short. Deliver a new MP4, never overwrite the source.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
V3=HERE.parent
sys.path[:0]=[str(V3/'short-v2'),str(V3)]
import sound as short
import check as qc
from layout import CACHE as V2, OUT as V2_OUT, NAME as V2_NAME, FPS, FRAMES, SR, SPF, SAMPLES
from mix import Bus, apply_envelope, band, db, decode, envelope, excerpt, ff, gain, measure, ns, peak_duck, rms, rms_blocks, wav
from pilot_mix import SPOTS as OPEN, synth_hit
from feature_mix import EDIT as FEATURE
from audio_sources import main as verify_bank

C=Path(os.environ.get('MONARCH_SHORT_FOLEY_CACHE','.cache/monarch-ant-short-foley')).resolve()
OUT=Path(os.environ.get('MONARCH_SHORT_FOLEY_DELIVERY','deliverables/monarch-cam-step-6-short-foley')).resolve()
NAME='Monarch-Cam-01A-Bite-To-Jump-Short-Foley-Mix.mp4'
SOURCE_SHA='9d7035435fec950328ab78358944ce0bd9f690de9769c439434e252f8d728046'
CAPTION_SHA='04627edb985b8a15beaba4571e27a900cadfb6fa0a191798568666dea3c4b530'

# V3 references are source frame numbers; target frame numbers are the Short.
# The film's opening is preserved in the feature, so OPEN is also V3 full Foley.
def opening_cue(label):
    hit=[s for s in OPEN if s[1]==label];assert len(hit)==1,label
    f,k,src,d,speed,lo,hi,_,pan,attack,seed=hit[0];return f,k,src,d,speed,lo,hi,pan,attack,seed


def feature_cue(f,key):
    hit=[(i,s) for i,s in enumerate(FEATURE) if s[0]==f and s[1]==key];assert len(hit)==1,(f,key)
    i,(_,label,src,pan,_,d,speed)=hit[0]
    return f,label,src,d,speed,175,2640 if 'wall' in label else 3070,pan,.063 if 'sweep' in src else .005,i


class Foley:
    def __init__(self):
        self.near=Bus(SAMPLES);self.dust=Bus(SAMPLES);self.ledger=[]
    def layer(self,f,ref,level,cap,*,pan=None,tail=False,phone=1.):
        f3,label,src,d,speed,lo,hi,pan0,attack,seed=ref
        x=excerpt(src,d,speed,lo,hi,seed=seed,attack=attack,release=min(.18,d*.5))
        # Small, parallel presence lift on close grains/snaps so the same
        # recorded detail survives mono phone speakers instead of relying on sub.
        z=band(x,900,4100);x=(x+z*(phone-1.)).astype('f')
        q=x[:ns(min(d,.195 if 'sweep' not in src else .39))]
        g=min(gain(level)/(rms(q)+1e-8),cap/(np.max(abs(x))+1e-8))
        b=self.dust if tail else self.near;p=(pan0*.71 if pan is None else pan)
        b.add(x,f/FPS,g,p)
        self.ledger.append(dict(frame=f,sample=round(f*SPF),source_frame_v3=f3,cue=label,source=src,
                                length_s=d,pan=p,source_speed=speed,effective_dbfs=round(db(rms(q)*g),3),tail=tail))
    def opening(self,f,key,level,cap,**kw):
        self.layer(f,opening_cue(key),level,cap,**kw)
    def feature(self,f,f3,key,level,cap,**kw):
        self.layer(f,feature_cue(f3,key),level,cap,**kw)
    def body(self,f,power,pan):
        self.near.add(synth_hit(),f/FPS,power,pan)
        self.ledger.append(dict(frame=f,sample=round(f*SPF),cue='short body of jaw contact',
                                source='V3 pilot_mix.synth_hit',length_s=.156,pan=pan,tail=False))


def conform():
    x=Foley()
    # First strike: the V3 opening's contact, sand trapped under the tips,
    # damped body and blow-out tail. No music transient on this frame.
    for d,k,lev,cap,tail in [
        (0.,'jaw-sand / one dry snap',-17.9,.59,False),
        (.34,'jaw-sand / buried grains',-23.4,.36,False),
        (1.18,'jaw-sand / debris',-24.9,.30,True),
        (7.8,'ejected grit separates',-29.2,.25,True),
    ]:x.opening(5+d,k,lev,cap,tail=tail,phone=1.28)
    x.body(5.19,.078,.098)
    x.opening(0,'sand starts before cut',-35.9,.14,tail=True)
    x.opening(39,'air travels with cut to wide',-32.7,.17,pan=.10,tail=True)
    # Tarsi, a fixed stone, and one rolling grain. Different envelopes on
    # individual grains, not the same loud footstep pasted at every cut.
    for f,key,lev,cap,tail in [
        (65,'front tarsus catches grain',-25.5,.24,False),
        (78,'toe searches',-29.1,.23,False),
        (96,'tarsus slips',-27.7,.23,False),
        (101,'grip shears',-30.0,.24,True),
        (139,'stone and suspended grains',-33.9,.15,True),
        (213.0,'witness grain first tumble',-28.8,.26,False),
        (219,'witness grain taps ridge',-30.9,.20,False),
        (232,'sand slips under COMING',-26.8,.27,True),
        (250.7,'heel skid',-28.7,.23,False),
        (404.5,'last tarsus finds sand',-29.3,.23,False),
        (419,'stance settles',-35.8,.12,True),
    ]:x.opening(f,key,lev,cap,tail=tail,phone=1.23)
    # The pincer cast in the opener; moving grains continue across the cut.
    x.opening(194,'larva head flick / close grit',-21.5,.42,phone=1.34)
    x.opening(196.3,'larva sand cast',-24.9,.30,tail=True,phone=1.32)
    x.opening(208,'cast falls back',-30.0,.19,tail=True)
    # Air comparison MUST NOT have the body, sand or takeoff tail of contact.
    x.feature(328,4180,'unsupported air snap',-20.35,.51,pan=-.055,phone=1.46)
    # Match the film's standalone f4297 start and two offsets. Impact is real
    # in the rig and located on f439 of this shorter edit (not on the cut).
    x.layer(439,(4297,'ground contact 4297','soft-snap',.106,1.04,155,3320,-.31,.0018,0),-17.05,.60,phone=1.32)
    x.layer(439.30,(4297.30,'ground contact / local grains','sand-step',.218,1.12,192,2990,-.279,.008,0),-22.6,.397,phone=1.29)
    x.layer(440.07,(4298.07,'ground contact / sand tail','sand-sweep',.569,1.17,197,2740,-.279,.045,0),-24.4,.31,tail=True,phone=1.36)
    x.body(439.17,.087,-.088)
    x.feature(451.5,4474,'grains pass macro',-29.8,.22,tail=True)
    x.feature(497,4592,'body leaves surface',-31.9,.20,tail=True)
    # Single touchdown and a staggered grit tail. No unrelated wing/air booms.
    x.opening(644,'rim landing / distant sand',-22.7,.40,pan=.16,phone=1.24)
    x.opening(645,'rim landing / grit tail',-30.0,.21,pan=.26,tail=True)
    x.feature(673,5318,'wall approach, no swell',-33.6,.16,tail=True)
    # Long-film's dull wall grit, no dry snap reused for this collision.
    x.feature(696,5325,'wall, dull grain cluster',-18.9,.55,pan=.26,phone=1.24)
    x.feature(696.31,5325.31,'wall, dry settled layer',-25.2,.29,pan=.21,tail=True,phone=1.16)
    x.feature(710,5361,'sand follows her down',-25.9,.29,pan=-.16,tail=True,phone=1.24)
    x.feature(743,5405,'falls back into sand',-27.6,.245,pan=-.19,phone=1.16)
    x.layer(790,(6559,'free jaws on the mock-treatment plate','snap-alt',.098,1.16,330,2670,-.27,.006,7),
            -27.2,.24,pan=-.13,phone=1.29)
    # No click on the glued tips. Sand and harmony remain under the question.
    x.feature(934,8890,'the bowl settles',-31.4,.21,tail=True)
    x.opening(983,'breath across overhead cut',-32.2,.19,tail=True)
    return x


def score_space(s):
    t=np.arange(SAMPLES)/SPF
    curve=np.ones(SAMPLES,dtype='f')
    for f,lead,rel,floor in [(5,5,10,.32),(194,6,11,.54),(328,8,13,.18),(439,10,16,.145),
                             (644,7,10,.42),(696,9,14,.216),(790,5,8,.5)]:
        a=np.interp(t,[f-lead,f-.75,f+3.5,f+rel],[1.,floor,floor,1.]).astype('f')
        np.minimum(curve,a,out=curve)
    return (s*gain(-4.7))*curve[:,None]


def impact_focus(s):
    # Ride the physical contact and its first burst, not the whole effects bus.
    # A broad score trim on its own would not solve this: measure the actual
    # phone-band foreground also, against the previous conformed effect stems.
    t=np.arange(SAMPLES)/SPF;g=np.zeros(SAMPLES,dtype='f')
    for f,boost,hold,end in [(5,6.6,6.9,13),(194,5.15,7.1,14),(328,2.1,3.6,6),
                             (439,6.2,7.7,14),(644,5.6,7.1,12),(696,4.05,7.2,15)]:
        np.maximum(g,np.interp(t,[f-.32,f+.19,f+hold,f+end],[0,boost,boost,0]),out=g)
    z=s*(10**(g/20))[:,None]
    # Soft shoulder only on the largest grains; a hard clip makes these shots
    # sound like a gunshot and squashes their different falloffs.
    p=np.abs(z)>.49
    z[p]=np.sign(z[p])*(.49+.178*np.tanh((np.abs(z[p])-.49)/.178))
    return z


def limiter(y):
    return short.processor(y,'alimiter=limit=.755:attack=4:release=71:level=false:latency=true',2)


def mono_phone(s):return band(np.asarray(s.mean(axis=1),dtype='f'),320,4320)


def foley_proof(old,new,music,vo):
    o,n,m,v=[mono_phone(s) for s in (old,new,music,vo)]
    beats={5:('opening bite and burst',.20),194:('antlion flings sand',.24),328:('dry snap in air',.115),
           439:('jaws hit sand',.235),644:('far rim touchdown',.22),696:('dull wall impact',.22)}
    out={}
    for f,(k,sec) in beats.items():
        ix=f*SPF;segment=slice(ix,ix+ns(sec));a,b,c,d=[db(rms(z[segment])) for z in (o,n,m,v)]
        out[str(f)]=dict(action=k,seconds=f/FPS,previous_foley_db=round(a,2),new_foley_db=round(b,2),
                         raised_db=round(b-a,2),foley_over_score_db=round(b-c,2),foley_vs_voice_db=round(b-d,2))
    return out


def remaster():
    C.mkdir(parents=True,exist_ok=True)
    verify_bank(False) # the exact long-film source hashes, no downloads when available
    original=V2_OUT/(V2_NAME+'.mp4')
    assert sha256(original.read_bytes()).hexdigest()==SOURCE_SHA,'not the approved short picture'
    old=short.build(stems_only=True)
    prevqa=json.loads((V2/'qa/mix.json').read_text())
    assert json.loads(json.dumps(old['takes']))==prevqa['takes'] and old['pace']['max_voice_gap_s']==prevqa['max_voice_gap_s']
    # Rebuild and verify the previous PCM before deriving any isolated baseline.
    y=old['voice']+old['score']+old['effects']+old['bed'];y*=envelope(np.ones(SAMPLES,'f'),.004,.020)[:,None]
    p=C/'meter.wav';wav(y,p);a=measure(p)
    scalar=gain(np.clip(-14.95-a['LUFS_I'],-1,6.2));original_pcm=decode(V2/'work/short-v2-mix.wav',2)
    old_check=limiter(y*scalar);e=float(np.max(abs(original_pcm-old_check)))
    assert e<=1.3e-6,e
    # Keep the old voice fader, not just the words. New Foley completely replaces
    # the earlier effects bus. The new score rides under the transient, not VO.
    voice=old['voice']*scalar
    s=score_space(old['score']*scalar)
    x=conform()
    side=peak_duck(old['mono_voice'],480)
    apply_envelope(x.dust.y,1.-.34*side,480)
    apply_envelope(x.near.y,1.-.064*side,480)
    foley=impact_focus(x.near.y+x.dust.y)
    mix=voice+s+foley+old['bed']*scalar*gain(-1.9)
    mix*=envelope(np.ones(SAMPLES,'f'),.004,.020)[:,None]
    y=limiter(mix)
    assert y.shape==(SAMPLES,2) and np.corrcoef(y.ravel(),mix.ravel())[0,1]>.993
    wav(y,p);z=measure(p)
    assert -16.2<z['LUFS_I']<-14.0 and z['dBTP']<=-1.5,z
    q=foley_proof(old['effects']*scalar,foley,s,voice)
    print('FEATURE_FOLEY_A_B',json.dumps(q,indent=2),flush=True)
    assert min(a['raised_db'] for a in q.values())>=3.,q
    assert min(a['foley_over_score_db'] for a in q.values())>=8.,q
    # In ongoing speech the FX bed still stays under the voice. Brief evidence
    # hits can break through, but the new tail mustn't swallow whole syllables.
    active=rms_blocks(voice.mean(axis=1),ns(.12));total=rms_blocks((foley+s).mean(axis=1),ns(.12))
    i=active>gain(-31);bed_level=20*np.log10(np.maximum(total[i]/active[i],1e-9))
    assert np.percentile(bed_level,90)<-8.,np.percentile(bed_level,[50,90,95])
    dest=C/'short-foley-master.wav';p.replace(dest)
    wav(foley,C/'foley-stem.wav') # local check only, never delivered alone
    proof=dict(reference_sha256=SOURCE_SHA,reference_pcm_max_error=e,frame_count=FRAMES,locked_voice_gain=scalar,
               unchanged_voice_takes=old['takes'],unchanged_voice_pace=old['pace'],foley_checks=q,bed_under_voice_p90=round(float(np.percentile(bed_level,90)),3),
               master=z,spotting=sorted(x.ledger,key=lambda a:a['frame']))
    return original,dest,y,proof


def hash_video(path):
    # Hash every encoded video packet, not container metadata/hexcodes.
    return ff('-loglevel','error','-i',path,'-map','0:v:0','-c:v','copy','-f','hash','-hash','SHA256','-').stdout.decode().strip()


def promote(video):
    captions=V2_OUT/(V2_NAME+'.en.srt')
    assert sha256(captions.read_bytes()).hexdigest()==CAPTION_SHA,'V2 caption timing/content changed'
    name=Path(NAME).stem
    OUT.mkdir(exist_ok=True,parents=True)
    for src,dst in [(captions,OUT/(name+'.en.srt')),(HERE/'upload.txt',OUT/(name+'-Upload.txt')),(video,OUT/NAME)]:
        if src==dst:continue
        temp=dst.with_name(dst.name+'.pending');shutil.copyfile(src,temp);temp.replace(dst)


def mux():
    original,mix,y,proof=remaster();dest=C/'foley.pending.mp4'
    ff('-loglevel','error','-y','-i',original,'-i',mix,'-map','0:v:0','-map','1:a:0',
       '-map_metadata','0','-map_chapters','-1','-c:v','copy','-c:a','aac','-b:a','224k','-ar','48000','-ac','2',
       '-metadata:s:a:0','language=eng','-video_track_timescale','30000','-movflags','+faststart+write_colr',dest)
    h=hash_video(dest);assert h==hash_video(original),h
    pic=qc.encode_gate(dest) # decode all 1,020 frames even though track is copied
    raw=decode(dest,2);assert SAMPLES<=len(raw)<SAMPLES+1024
    x=raw[:SAMPLES];q=measure(dest)
    assert -16.2<q['LUFS_I']<-14.0 and q['dBTP']<=-1.5,q
    corr=[np.corrcoef(x[l:r].ravel(),y[l:r].ravel())[0,1] for s in proof['unchanged_voice_takes'] for l,r in [s['mix_samples']]]
    assert min(corr)>.987,corr
    g=short.runs(rms_blocks(x.mean(axis=1),SR//100)>gain(-51),False)
    assert all(b-a<9 for a,b in g),g
    proof.update(video_packet_hash=h,picture=pic,encoded=q,encoded_mix_min_active_corr=float(min(corr)),
                 final_mix_gap_ms=10*max((b-a for a,b in g),default=0),sample_count=SAMPLES,
                 sha256=sha256(dest.read_bytes()).hexdigest(),bytes=dest.stat().st_size,caption_sha256=CAPTION_SHA)
    assert proof['bytes']<100_000_000
    promote(dest);dest.unlink()
    (C/'receipt.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('FOLEY_SHORT_READY',OUT/NAME,proof['bytes'],proof['sha256'],q,'unchanged video',h,flush=True)


if __name__=='__main__':mux()
