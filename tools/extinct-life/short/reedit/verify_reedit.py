#!/usr/bin/env python3
"""Instrumented encode, gap, graphics and handoff checks for the revised Short."""
from __future__ import annotations
import argparse
import json
import re
from shutil import copyfile

import numpy as np
from PIL import Image
from scipy.signal import correlate

from clock import CACHE, QA, MIX, OUT, PENDING, MASTER, CAPTIONS, STUDIO, NAME, TITLE, W, H, FPS, SR, FP, digest, dump, finish
from mix import decoded, meter, ff, db, rms, eq, srt, windows
from verify import root_boxes, stride, studio as base_studio, file_detail


def inputs(tag):
    r=json.loads((QA/f'{tag}-build.json').read_text());m=json.loads((QA/'mix.json').read_text())
    assert r['program_audio']==m['sha256']==digest(MIX/'program.wav')
    assert json.loads(json.dumps(finish(m['cues'])))==r['timeline']==m['timeline']
    assert r['trace']['frame_rows']==r['timeline']['frames']
    return r,m


def tracks(movie,t,size):
    _,log=ff(['-i',movie,'-map','0:v:0','-map','0:a:0','-c','copy','-t','0.05','-f','null','-'])
    l=log.split('Stream mapping:')[0];w,h=size
    assert len(re.findall(r'Stream #0:\d+',l))==2 and 'displaymatrix' not in l
    d=f'00:00:{t["seconds"]:05.2f}';fields=[f'Duration: {d}',f'{w}x{h}',f'{FPS} fps','start: 0.000000',
        'Video: h264 (High)','yuv420p(tv, bt709, progressive)','(eng): Audio: aac (LC)','48000 Hz, stereo']
    assert all(x in l for x in fields),(fields,l)
    a=root_boxes(movie);assert a[0]==b'ftyp' and a.index(b'moov')<a.index(b'mdat')
    assert 2_800_000<movie.stat().st_size<99_500_000
    return dict(format='H.264 High / AAC-LC',seconds=t['seconds'],size=size,fps=FPS,sample_rate=SR,channels=2,faststart=True)


def picture(movie,r,tag):
    t=r['timeline'];c=t['cuts'];n=t['frames'];e=t['events'];g=r['graphics']
    frames=stride(movie,'scale=72:128:flags=area',(72,128)).astype(np.float32);assert len(frames)==n
    luma=frames@np.array([.2126,.7152,.0722],np.float32);spread=luma.std((1,2));assert min(spread)>11 and min(luma.mean((1,2)))>23
    distance=lambda a,b:float(np.mean(np.abs(a-b)))
    step=np.mean(np.abs(np.diff(frames,axis=0)),axis=(1,2,3))
    hard={f:round(float(step[f-1]),2) for f in c[1:-1] if f!=t['art']['rewind']}
    assert min(hard.values())>6.0 and step[t['art']['rewind']-1]<3.3,(hard,step[t['art']['rewind']-1])
    loop=distance(frames[0],frames[-1]);ref=float(np.median(np.r_[step[-6:],step[:4]]));assert loop<6.2 and loop<ref*2.09+.22,(loop,ref)
    # Hook must change tangibly through the first contact, not hold on a
    # title card. The caption schema and pin frames are audited independently.
    hook=distance(frames[0,22:89],frames[e['hook_impact']+7,22:89]);assert hook>10,hook
    p=g['pin_frames'];assert p['today']>=72 and p['past']>=100 and p['rewind']>=21,p
    assert g['captioned_frames']>n*.91 and g['perspective_extrusion_plates']>n*.90,g
    x=g['text_bounds'];assert 'CGI DEMO' in x['demo'] and 'SAME FOOT · SAME SCALE · CGI' in x['comparison']
    assert 'ILLUSTRATIVE TRACK SURFACE' in x['brazil'] and 'ILLUSTRATIVE TRACK SURFACE' in x['cameroon']
    assert 'MAP SNAPSHOT · NOT A TRACK DATE' in x['past'] and 'Brazil region' in x['past pins'] and 'Cameroon region' in x['past pins']
    frames_to_check=sorted(set([0,5,18,32,42,c[2]-1,c[3]-1,e['lip_chip'],e['lip_chip']+5,c[4]+20,c[5]+23,c[6]+18,c[7]+41,
                               e['map_rewind']+28,e['map_land']+16,c[9]+48,c[10]+18,n-2,n-1]))
    sel='+'.join(f'eq(n,{i})' for i in frames_to_check)
    im=stride(movie,f"select='{sel}',scale=360:640:flags=lanczos",(360,640));assert len(im)==len(frames_to_check)
    target=QA/(tag+'-encoded-phone');target.mkdir(exist_ok=True)
    for f,b in zip(frames_to_check,im,strict=True):Image.fromarray(b).save(target/f'f{f:04d}.jpg',quality=95,subsampling=0)
    return dict(frames=n,hard_cut_distance=hard,continuous_atlas=True,loop_distance=round(loop,4),near_loop_motion=round(ref,4),
                hook_distance=round(hook,3),decoded_phone_frames=frames_to_check,min_luma_sd=round(float(min(spread)),3),
                captions_frames=g['captioned_frames'],extruded_plates=g['perspective_extrusion_plates'])


def audio(movie,m):
    t=m['timeline'];n=t['samples'];a=decoded(movie,2);p=decoded(MIX/'program.wav',2);dry=decoded(MIX/'narration-reference.wav')
    assert len(p)==len(dry)==n and n<=len(a)<=n+1024,(len(a),n)
    a=a[:n];assert np.max(np.abs(a))<.95 and np.isfinite(a).all()
    snr=db(rms(p))-db(rms(p-a));assert snr>33,snr
    loud=meter(movie);assert -17.55<=loud['lufs_i']<=-16.30 and loud['dbtp']<=-1.45,loud
    y=eq(a.mean(1),185,4800);v=eq(dry,185,4800);bed=y-v;obs=[];d=112;lags=[]
    for c in m['cues']:
        l=max(d,c['speech_start']);h=min(n-d,c['speech_end'])
        z=correlate(p[l-d:h+d].mean(1),a[l:h].mean(1),mode='valid',method='fft');lags.append(int(np.argmax(z))-d)
        obs.append(round(db(rms(v[l:h]))-db(rms(bed[l:h])),2))
    assert all(x==0 for x in lags) and min(obs)>=10.0 and np.median(obs)>14.75,(obs,lags)
    cuts=m['cues'];gaps=[round((v['speech_start']-u['speech_end'])*1000/SR,1) for u,v in zip(cuts,cuts[1:])]
    assert max(gaps)<=180 and all(x>80 for x in gaps) and m['pacing']['phrase_gaps_ms']==gaps
    # Audit the actual delivered phone-band signal as well as the voice
    # spans. Every overlapping 80 ms window carries speech, Foley or score.
    yy=np.r_[y[-7*480:],y,y[:7*480]];rms80=db(float(np.sqrt(np.min(np.mean(np.lib.stride_tricks.sliding_window_view(yy.reshape(-1,480).var(1),8),axis=-1)))))
    assert rms80>-46,rms80
    quiet=windows(v)>10**(-43/20);ids=np.flatnonzero(quiet);quiet_ms=10*max(int(np.max(np.diff(ids)))-1,len(quiet)-ids[-1]+ids[0]-1)
    assert quiet_ms<=300,quiet_ms
    timings={x['name']:x for x in m['event_checks']};assert set(timings)==set(t['events'])
    for k,x in timings.items():
        assert x['frame']==t['events'][k] and x['attack_ms']<12 and x['phone_band_dbfs']>(-53.5 if k=='lip_chip' else -50),(k,x)
    s=db(rms(a[-1]-a[0]));near=db(rms(np.diff(np.concatenate((a[-5600:],a[:4500])),axis=0)))
    assert s<-51 and s<near+3.4,(s,near)
    mix_s=m['pacing']
    return dict(loudness=loud,aac_snr_db=round(snr,3),cue_aac_offsets_samples=lags,voice_to_bed_db=obs,
                longest_phrase_gap_ms=max(gaps),longest_10ms_voice_density_gap_ms=quiet_ms,lowest_80ms_phone_band_db=round(rms80,2),
                seam_sample_delta_dbfs=round(s,2),first_word_ms=mix_s['first_word_ms'],loop_word_gap_ms=mix_s['loop_word_gap_ms'],
                accents=list(timings.values()),note='Instrumented sync and phone-band checks, not a human listening or pronunciation sign-off.')


def studio(m):
    content,stats=base_studio(m)
    content=content.replace('SHORT 01 · STUDIO','SHORT 01 · V2 KINETIC RECUT · STUDIO')
    content=content.replace('34 seconds',f"{m['timeline']['seconds']:.1f} seconds").replace('Atlantic-Tracks-Short-01.',NAME+'.')
    content=content.replace('Fraunces and IBM Plex','Space Grotesk, Fraunces and IBM Plex')
    content=content.replace('try the lift at 0:01.267','try the lift around 0:01.400')
    content=content.replace('around 0:12–0:16','around 0:08.5–0:12.1')
    title=content.split('TITLE — copy the next line\n',1)[1].splitlines()[0];assert title==TITLE and CAPTIONS.name in content and MASTER.name in content
    desc=content.split('through the hashtags\n\n',1)[1].split('\n\nTAGS —',1)[0]
    stats['description']=len(desc);assert len(desc)<5000
    return content,stats


def verify(tag='native',check_only=False):
    r,m=inputs(tag);t=r['timeline'];f=MASTER if check_only else (
        PENDING.with_name(NAME+'-Phone-Proof.mp4') if tag=='phone' else PENDING)
    assert digest(f)==r['encode_sha256']
    tr=tracks(f,t,r['size']);pic=picture(f,r,tag);au=audio(f,m)
    print('RECUT_ENCODE_VERIFIED',tr,flush=True)
    print('RECUT_VIEW_SYNC_VERIFIED',pic['frames'],pic['loop_distance'],au['aac_snr_db'],au['longest_phrase_gap_ms'], flush=True)
    if tag=='phone':
        dump(QA/'phone-verified.json',dict(streams=tr,picture=pic,audio=au));return
    en=srt(m['cues']);assert (MIX/'captions.srt').read_text()==en and len(re.findall(r' --> ',en))==14
    content,stats=studio(m)
    if check_only:assert CAPTIONS.read_text()==en and STUDIO.read_text()==content
    else:
        OUT.mkdir(parents=True,exist_ok=True);copyfile(MIX/'captions.srt',CAPTIONS);STUDIO.write_text(content,encoding='utf-8');f.replace(MASTER)
    dump(QA/'verified.json',dict(title=TITLE,version='V2 Kinetic Recut',status='Owner review, unpublished',streams=tr,picture=pic,
        audio=au,pacing=m['pacing'],render=r,english_cues=14,metadata_characters=stats,
        files=[file_detail(p) for p in [MASTER,CAPTIONS,STUDIO]]))
    print('ATLANTIC_SHORT_V2_VERIFIED',MASTER.stat().st_size,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--phone',action='store_true');g.add_argument('--verify-only',action='store_true')
    x=p.parse_args();verify('phone' if x.phone else 'native',x.verify_only)
