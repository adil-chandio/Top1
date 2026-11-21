#!/usr/bin/env python3
"""Verify the encoded Short before promoting picture, captions and Studio copy."""
from __future__ import annotations
import argparse
import json
from hashlib import md5
from pathlib import Path
import re
from shutil import copyfile
import struct

import numpy as np
from PIL import Image
from scipy.signal import correlate, sosfilt

from mix import MIX, ff, decoded, rms, db, kernel, meter
from spec import CACHE, QA, OUT, FIELDS, W, H, FRAMES, SR, FPS, N, TITLE, NAME, CUTS, digest, dump

WAITING=CACHE/'encode'/(NAME+'.pending.mp4')
MASTER=OUT/(NAME+'.mp4')
CAPTIONS=OUT/(NAME+'.en.srt')
STUDIO=OUT/(NAME+'-Studio.txt')


def root_boxes(path):
    m=[];end=path.stat().st_size
    with path.open('rb') as f:
        while f.tell()<end:
            base=f.tell();n,k=struct.unpack('>I4s',f.read(8));h=8
            if n==1:n=struct.unpack('>Q',f.read(8))[0];h=16
            elif n==0:n=end-base
            assert h<=n<=end-base,(n,k,base,end)
            m.append(k);f.seek(base+n)
    return m


def tracks(movie):
    _,log=ff(['-i',movie,'-map','0:v:0','-map','0:a:0','-c','copy','-t','0.05','-f','null','-'])
    ins=log.split('Stream mapping:',1)[0]
    for text in ['Duration: 00:00:34.00','start: 0.000000','Video: h264 (High)','yuv420p(tv, bt709, progressive)',
                 f'{W}x{H}',f'{FPS} fps','(eng): Audio: aac (LC)','48000 Hz, stereo']:
        assert text in ins,(text,ins)
    assert len(re.findall(r'Stream #0:\d+',ins))==2 and 'displaymatrix' not in ins
    boxes=root_boxes(movie);assert boxes[0]==b'ftyp' and boxes.index(b'moov')<boxes.index(b'mdat')
    assert 8_000_000<movie.stat().st_size<99_500_000
    return dict(format='H.264 High / AAC-LC',frame_size=[W,H],fps=FPS,pixel_layout='yuv420p',colour='BT.709 limited',
        audio_rate=SR,channels=2,fast_start=True,seconds=FRAMES/FPS)


def stride(movie,args,size):
    w,h=size
    q,_=ff(['-v','error','-xerror','-i',movie,'-map','0:v:0','-an','-vf',args,'-fps_mode','passthrough','-pix_fmt','rgb24','-f','rawvideo','-'])
    return np.frombuffer(q,np.uint8).reshape(-1,h,w,3)


def picture(movie):
    frames=stride(movie,'scale=72:128:flags=area',(72,128)).astype(np.int16)
    assert len(frames)==FRAMES
    # Every frame must have a meaningful luminance distribution. This also
    # catches warm or blue flat frames which a blackdetect-only pass would miss.
    luma=frames.mean(axis=-1);sig=luma.std((1,2));score=luma.mean((1,2));assert min(sig)>11 and min(score)>18
    d=np.mean(np.abs(np.diff(frames,axis=0)),axis=(1,2,3))
    loop=float(np.mean(np.abs(frames[0]-frames[-1])))
    near=float(np.median(np.r_[d[-5:],d[:3]]));assert loop<7.0 and loop<near*2.1+.12,(loop,near)
    # Six true accents vs the one continuous modern→ancient camera shot.
    cuts=[f for f in CUTS[1:-1] if f!=574]
    assert all(d[f-1]>6 for f in cuts) and d[573]<1.50,[(f,d[f-1]) for f in CUTS[1:-1]]
    form=[0,5,14,29,38,55,82,92,103,117,149,169,179,189,204,214,239,262,289,317,350,379,460,544,604,633,676,784,853,914,952,992,1019]
    dst=QA/'encoded-phone';dst.mkdir(exist_ok=True)
    expr='+'.join(f'eq(n,{x})' for x in form)
    views=stride(movie,f"select='{expr}',scale=360:640:flags=lanczos",(360,640));assert len(views)==len(form)
    for f,im in zip(form,views,strict=True):Image.fromarray(im).save(dst/f'f{f:04d}.jpg',quality=94,subsampling=0)
    meta=json.loads((QA/'render-layout.json').read_text());assert meta['frame_audit']['probes']==FRAMES and meta['map_annotated_frames']>=244
    assert 'CGI DEMO' in meta['safe_text_bounds']['formation']
    assert 'ILLUSTRATIVE TRACK SURFACE' in meta['safe_text_bounds']['brazil'] and 'ILLUSTRATIVE TRACK SURFACE' in meta['safe_text_bounds']['cameroon']
    assert 'BRAZIL' not in meta['safe_text_bounds']['cameroon'] and '125 MILLION YEARS AGO' in meta['safe_text_bounds']['past']
    return dict(decoded_frames=len(frames),hard_cuts=cuts,continuous_globe=True,
        decoded_phone_probes=form,min_luma_stdev=round(float(min(sig)),3),
        loop_mae_at_72x128=round(loop,4),adjacent_motion_mae=round(near,4),
        first_frame_not_black=True,safe_text_rectangles=sum(map(len,meta['safe_text_bounds'].values())))


def audio(movie,mix):
    source=decoded(MIX/'program.wav',2);y=decoded(movie,2)
    assert len(source)==N and N<=len(y)<=N+1024,(len(source),len(y));y=y[:N]
    assert np.max(np.abs(y))<.97 and np.isfinite(y).all()
    snr=db(rms(source))-db(rms(y-source));assert snr>30.0,snr
    lim=meter(movie);assert -18.2<=lim['lufs_i']<=-16.55 and lim['dbtp']<-1.35,lim
    d=128;tone=decoded(MIX/'narration-reference.wav');assert len(tone)==N
    band=kernel(185,4800);centre=sosfilt(band,y.mean(1),axis=0);narr=sosfilt(band,tone,axis=0)
    cues=[];off=[]
    for c in mix['cues']:
        l,r=c['start_sample'],c['end_sample'];L=max(d,l);R=min(N-d,r)
        reference=source[L-d:R+d].mean(1);probe=y[L:R].mean(1);s=correlate(reference,probe,mode='valid',method='fft');lag=int(np.argmax(s))-d
        off.append(lag);a=narr[L:R];b=centre[L:R]-a
        q=db(rms(a))-db(rms(b));cues.append(round(q,2))
    assert off==[0]*len(cues) and min(cues)>9.0 and np.median(cues)>15,(off,cues)
    fx=decoded(MIX/'foley-reference.wav',2);f=sosfilt(band,fx.mean(1));events={}
    for a in mix['event_checks']:
        t=a['frame']*SR//FPS;delta=a['transient_after_frame_ms'];event=a['name']
        # Verify the short crack, lift, and wet landing remain real midband
        # transients rather than a sub-bass-only waveform after folding to mono.
        q=db(rms(f[t:t+round(.165*SR)]));assert q>(-58 if event in ('lip_drip','map_rewind') else -50),(event,q)
        events[event]=dict(frame=a['frame'],audio_attack_ms=delta,foley_phone_band_dbfs=round(q,2))
    gap=db(rms(y[-1]-y[0]));guide=db(rms(np.diff(np.concatenate([y[-6100:],y[:3500]]),axis=0)))
    assert gap<-55 and gap<guide+5,(gap,guide)
    return dict(loudness=lim,aac_decoded_snr_db=round(snr,3),cue_offsets_samples=off,
        voice_to_residual_db_phone_mono_185_to_4800=cues,event_checks=events,seam_step_dbfs=round(gap,2),
        note='Signal checks and word alignment, not human listening approval')


def studio(mix):
    descriptions=[
        'Same dinosaur foot, two different prints. In firm mud the toe outlines hold. In softer mud the walls can slump as the foot lifts.',
        'Three-toed dinosaur tracks occur in the Sousa Basin of Brazil and the Koum Basin of Cameroon, roughly 6,000 km apart today. A reconstruction of Early Cretaceous Gondwana puts both site regions on connected land. That makes a land route possible; it doesn’t establish a continuous trail or tell us which animals made both sets of tracks.',
        'The 3D mud demo, fossil surfaces and rock section are illustrations, not field footage or specimen scans. The 125-million-year map is a geographic snapshot, not the date of a footprint. This Short includes synthetic narration and generated material textures.',
        'RESEARCH\n• Jacobs et al. (2024) — The Early Cretaceous Borborema–Cameroon Dinosaur Dispersal Corridor: https://igeo.ufrj.br/inc/isc/3/03_139_Jacobs%20etal.pdf\n• Menkem et al. (2026) — Koum Basin sedimentology and dinosaur tracks: https://doi.org/10.1016/j.jop.2026.100416\n• Falkingham & Gatesy (2014) — how a print develops in sediment: https://doi.org/10.1073/pnas.1416252111',
        'MAP & SOUND CREDITS\n• Kocsis & Scotese, PaleoCoastlines and rotations (https://doi.org/10.1016/j.earscirev.2020.103463), and Scotese & Wright, PaleoDEMs v2 (https://doi.org/10.5281/zenodo.5460860); resampled, recoloured, relit and annotated (relief exaggerated). CC BY 4.0: https://creativecommons.org/licenses/by/4.0/\n• Modern geography: Natural Earth and NOAA NGDC ETOPO5 (public domain).',
    ]
    attr={'Benboncan':'stone fracture','Erdie':'hard-surface step','AGFX':'wet footsteps'}
    licensed=[f"{a['credit']} ({attr[a['credit']]}) — {a['source']}" for a in mix['source_credits'] if a['license']=='CC-BY-3.0']
    assert len(licensed)==len(attr)
    descriptions[-1]+='\n• Foley, edited and layered (CC BY 3.0 — https://creativecommons.org/licenses/by/3.0/): '+'; '.join(licensed)+'.'
    cc0=list(dict.fromkeys(a['credit'] for a in mix['source_credits'] if a['license']=='CC0-1.0'))
    descriptions[-1]+='\n• Additional sound and score samples (CC0, edited): '+', '.join(cc0)+'.\n• Type: Fraunces and IBM Plex (SIL OFL 1.1).'
    descriptions.append('#DinosaurFootprints #Paleontology #Shorts')
    desc='\n\n'.join(descriptions)
    tags='dinosaur footprints, dinosaur tracks, fossil tracks, Brazil Cameroon dinosaur tracks, Sousa Basin, Koum Basin, Early Cretaceous, Gondwana, South Atlantic, paleontology, sedimentology, Extinct Life, Monarch Extinct Channel'
    assert 0<len(TITLE)<=100 and len(desc)<=5000 and len(tags)<=500
    st=f'''ATLANTIC TRACKS — SHORT 01 · STUDIO PASTE SHEET
Monarch Extinct Channel | 34 seconds | Portrait 9:16 | Owner review

TITLE — copy the next line
{TITLE}

DESCRIPTION — copy from here through the hashtags

{desc}

TAGS — paste in the separate Tags field
{tags}

PINNED COMMENT — optional, after release
A map can show where land was connected. What would you look for in the rocks to test whether dinosaurs could have used that connection?

STUDIO SETTINGS — internal, not part of the description
• Master: {MASTER.name}. Category: Science & Technology. Original language: English. Use {CAPTIONS.name} if uploading an English accessibility track; the MP4 also has readable on-picture captions.
• Audience: general-audience science, not designed for children; confirm in Studio. Altered content recommendation: Yes for the realistic reconstructed scenes/synthetic material. https://support.google.com/youtube/answer/14328491
• Related video: select “Why Are These Dinosaur Footprints an Ocean Apart?” (Atlantic Tracks — Cinema Edition) once it is public or unlisted on the same channel, if advanced features are enabled. No spoken promotion, raw link, or end screen needed. https://support.google.com/youtube/answer/14075157
• If selecting a Shorts thumbnail frame in the app, try the lift at 0:01.267. Use the actual frame, not the long-form cover. No separate thumbnail supplied.
• Owner playback check before release: listen to Brazil/Cameroon around 0:12–0:16, and check mud sounds, the English captions and the loop in the mobile preview. No YouTube upload, scheduling, or publication is part of this handoff.
'''
    return st,dict(title=len(TITLE),description=len(desc),tags=len(tags))


def file_detail(p):return dict(name=p.name,bytes=p.stat().st_size,sha256=digest(p),md5=md5(p.read_bytes()).hexdigest())


def verify(check_only=False):
    authored=json.loads((QA/'build.json').read_text());p=MASTER if check_only else WAITING
    assert digest(p)==authored['encode_sha256'] and authored['frames']==FRAMES
    mix=json.loads((QA/'mix.json').read_text());assert authored['program_audio']==mix['sha256']==digest(MIX/'program.wav')
    s=tracks(p);print('PORTRAIT_CONTAINER_VERIFIED',s,flush=True)
    v=picture(p);print('SHORT_ALL_FRAMES_AND_REPLAY_VERIFIED',v['decoded_frames'],v['loop_mae_at_72x128'],flush=True)
    a=audio(p,mix);print('SHORT_AUDIO_VERIFIED',a['loudness'],a['aac_decoded_snr_db'],flush=True)
    lines=(MIX/'captions.srt').read_text().strip().split('\n\n');assert len(lines)==len(mix['cues'])==14
    for i,(line,c) in enumerate(zip(lines,mix['cues'],strict=True),1):
        j,t,x=line.split('\n');assert int(j)==i and x==c['text'] and '-->' in t and c['end_sample']<N
    s2,chars=studio(mix)
    OUT.mkdir(parents=True,exist_ok=True)
    if check_only:
        assert STUDIO.read_text()==s2 and CAPTIONS.read_bytes()==(MIX/'captions.srt').read_bytes()
    else:
        copyfile(MIX/'captions.srt',CAPTIONS);STUDIO.write_text(s2,encoding='utf-8');p.replace(MASTER)
    result=dict(title=TITLE,status='Owner review only; not published',streams=s,visual=v,audio=a,english_cues=len(lines),
        metadata_characters=chars,render=authored,approximate_model_distance_km=json.loads((FIELDS/'world.json').read_text())['distance_km'],
        files=[file_detail(f) for f in (MASTER,CAPTIONS,STUDIO)])
    dump(QA/'verified.json',result)
    print('ATLANTIC_SHORT_VERIFIED',MASTER.stat().st_size,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');verify(p.parse_args().verify_only)
