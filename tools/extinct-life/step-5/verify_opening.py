#!/usr/bin/env python3
"""Verify the actual review MP4 and write a small reproducibility receipt."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import struct
import subprocess

import numpy as np
from PIL import Image, ImageDraw
from scipy.signal import correlate

from finish import AUDIO, BED, CC, CLOCK, END, FPS, FRAMES, HERE, MIX, MOVIE, NSAMPLES, OUT, Q, SRT, STEM, TITLE, VOICE, int_samples, locked
from picture import CACHE, FF, PACK, SHOT_NAMES, Trace, hashfile, native_size, part_dir


def run(args, timeout=120):
    proc=subprocess.run([FF,'-hide_banner','-nostdin',*args],capture_output=True,check=True,timeout=timeout)
    return proc.stdout,proc.stderr.decode('utf-8',errors='replace')


def children(buf,lo,hi):
    while lo<hi:
        size,k=struct.unpack_from('>I4s',buf,lo); width=8
        if size==1:size,=struct.unpack_from('>Q',buf,lo+8); width=16
        if size==0:size=hi-lo
        assert width<=size and lo+size<=hi,(k,lo,size)
        yield k,lo+width,lo+size
        lo+=size
    assert lo==hi


def find(buf,loc,k):return next(b[1:] for b in children(buf,*loc) if b[0]==k)


def clock(buf,loc):
    p,_=loc;v=buf[p]
    return struct.unpack_from('>IQ' if v else '>II',buf,p+(20 if v else 12))


def rows(buf,loc,width):
    p,q=loc
    n,=struct.unpack_from('>I',buf,p+4)
    a=list(struct.iter_unpack('>'+'I'*width,buf[p+8:q]));assert n==len(a)
    return a


def check_clocks(file,smoke=False):
    b=file.read_bytes();top=(0,len(b)); moov=find(b,top,b'moov'); assert moov[1]<=find(b,top,b'mdat')[0]
    assert clock(b,find(b,moov,b'mvhd'))==(CLOCK,NSAMPLES)
    tracks={}
    for magic,ss,ee in children(b,*moov):
        if magic!=b'trak':continue
        track=(ss,ee);m=find(b,track,b'mdia');p,_=find(b,m,b'hdlr');kind=b[p+8:p+12].decode('ascii')
        assert kind not in tracks
        sample=find(b,find(b,m,b'minf'),b'stbl')
        edit_ed=find(b,find(b,track,b'edts'),b'elst')
        p,_=edit_ed
        assert b[p]==0 and struct.unpack_from('>I',b,p+4)[0]==1,(kind,p)
        edit_duration,media_start,rate=struct.unpack_from('>IiI',b,p+8)
        assert rate==65536
        sr,n=clock(b,find(b,m,b'mdhd'))
        track_info={'timescale':sr,'media_samples':n,'edit_duration_ticks':edit_duration,'media_start':media_start}
        if kind=='vide':
            assert (sr,n,media_start,edit_duration)==(CLOCK,NSAMPLES,0,NSAMPLES)
            counts=Counter()
            for c,d in rows(b,find(b,sample,b'stts'),2):counts[d]+=c
            assert counts=={CLOCK//FPS:FRAMES[-1]},counts
            assert not any(k==b'ctts' for k,_,_ in children(b,*sample)), 'video is IP-only, no reorder'
            keyframes={k-1 for k, in rows(b,find(b,sample,b'stss'),1)}
            if not smoke:assert set(FRAMES[:-1])<=keyframes,(FRAMES,keyframes)
            track_info.update(frames=FRAMES[-1],ticks_per_frame=CLOCK//FPS,seekable_shot_starts=len(set(FRAMES[:-1])&keyframes))
        if kind=='soun':
            assert sr==CLOCK and media_start==1024 and edit_duration==NSAMPLES,(sr,n,media_start,edit_duration)
            assert 0<=n-NSAMPLES-media_start<1024
        tracks[kind]=track_info
    assert set(tracks)=={'vide','soun','sbtl'}
    return tracks


def check_track(movie):
    source=int_samples(VOICE,NSAMPLES); mix=int_samples(MIX,NSAMPLES); bed=int_samples(BED,NSAMPLES)
    assert mix.shape==bed.shape==(NSAMPLES,2) and source.shape==(NSAMPLES,1)
    assert np.array_equal(mix-bed,np.broadcast_to(source,bed.shape))
    raw,_=run(['-loglevel','error','-i',str(movie),'-map','0:a:0','-c:a','pcm_f32le','-f','f32le','-'])
    decoded=np.frombuffer(raw,dtype='<f4').reshape(-1,2)
    assert 0<=decoded.shape[0]-NSAMPLES<1024,decoded.shape
    rec=decoded[:NSAMPLES].mean(axis=1)-bed.mean(axis=1)/Q
    ref=source[:,0]/Q
    delta=[]; peak=[]
    for t in (.097,1.48,2.65,4.20,6.28,10.19,11.53,15.24,18.10,19.50,27.38,29.18,35.15,37.83,44.13,47.21,49.54,53.36,57.25,59.81):
        a=round(t*CLOCK);z=min(NSAMPLES-420,a+24_000);r=ref[a:z];w=rec[a-420:z+420]
        score=correlate(w,r,mode='valid',method='fft'); j=int(score.argmax());lag=j-420
        q=w[j:j+(z-a)];corr=float(np.dot(q,r)/(np.linalg.norm(q)*np.linalg.norm(r)))
        assert lag==0 and corr>.992,(t,lag,corr)
        delta.append(lag);peak.append(corr)
    _, ff=run(['-i',str(movie),'-map','0:a:0','-af','ebur128=peak=true:framelog=verbose','-f','null','-'])
    ff=ff[ff.rindex('Summary:'):]
    i=float(re.search(r'I:\s*(-?\d+(\.\d+)?) LUFS',ff).group(1))
    p=float(re.search(r'Peak:\s*(-?\d+(\.\d+)?) dBFS',ff).group(1))
    assert -20<i<-15 and p<-1.3,(i,p)
    assert abs(float(np.max(np.abs(decoded))))<.891
    return {'pre_aac_voice_bit_exact_after_subtracting_bed':True,'source_sample_zero':0,'decoded_samples':int(len(decoded)),
            'checked_sync_points':len(delta),'all_sync_offsets_samples':sorted(set(delta)),'worst_narration_correlation':round(min(peak),7),
            'integrated_lufs':i,'true_peak_dbtp':p,'aac_stereo':True,**json.loads((AUDIO/'mix.json').read_text())}


def check_captions(movie):
    data,_=run(['-loglevel','error','-i',str(movie),'-map','0:s:0','-c:s','srt','-f','srt','-'])
    blocks=lambda x:x.replace('\r','').strip().split('\n\n')
    out=blocks(data.decode('utf-8')); canon=blocks(SRT.read_text());
    assert out==blocks(CC.read_text())==canon[:18],(len(out),len(canon))
    return {'language':'eng','canonical_first_cues':len(out),'last_cue_out':'00:01:00.673','english_caption_round_trip':True}


def check_trace():
    base=part_dir();pos=[]; counts=0
    for i,(a,b) in enumerate(zip(FRAMES,FRAMES[1:]),1):
        lo=[]
        with (base/f'{i:02d}.csv').open() as q:
            for f in range(a,b):
                t=Trace.read(q);assert t.frame==f and t.shot==i-1
                lo.append(t)
            assert not q.read()
        counts+=len(lo)
        d=math.dist(lo[0].camera,lo[-1].camera)
        assert d>.13,(i,d)
        pos.append({'shot':i,'move_length':round(d,4),'render_resolution':native_size(i-1),'frames':b-a})
        if i in (3,4):
            focus=lo[65:] if i==4 else lo
            for t in focus:
                first,second=t.pins[i==4]
                for p in (first,second):assert p[-1] and .09<p[0]<.94 and .44<p[1]<.95,(i,p)
                span=abs(first[0]-second[0])
                assert (span>.37 if i==3 else span<.16),(i,span)
        if i==7:
            # All four horizon leaders must remain on screen through the count.
            assert all(90<x<1380 and 112<y<976 for t in lo if t.frame/FPS>=33.9 for x,y in t.layers)
    assert counts==FRAMES[-1]
    return pos


def proof(movie):
    q=CACHE/'qa';q.mkdir(exist_ok=True)
    poses=(1.0,3.5,5.5,8.25,10.75,12.48,15.875,18.4,22.20,29.43,34.70,39.60,45.9,49.41,51.79,54.0,57.44,60.62)
    all_hashes=set();w,h=704,396
    for j in range(2):
        canvas=Image.new('RGB',(1320,271*3),'#0a171a');pen=ImageDraw.Draw(canvas)
        for i,t in enumerate(poses[j*9:j*9+9]):
            tick=round(t*FPS)/FPS
            raw,_=run(['-loglevel','error','-ss',f'{tick:.9f}','-threads','2','-i',str(movie),'-map','0:v:0','-frames:v','1','-vf',
                       f'scale={w}:{h}:in_color_matrix=bt709:out_range=pc','-pix_fmt','rgb24','-f','rawvideo','-threads','1','-'])
            assert len(raw)==w*h*3,(t,len(raw))
            v=Image.frombytes('RGB',(w,h),raw)
            assert np.asarray(v).std()>10
            dest=q/f'encoded-{round(t*FPS):04d}.jpg';v.save(dest,quality=96)
            all_hashes.add(hashfile(dest));x,y=(i%3*440,i//3*271)
            canvas.paste(v.resize((440,248),Image.Resampling.LANCZOS),(x,y))
            pen.text((x+11,y+251),f'{tick:06.2f}s',fill='#fff1dc')
        canvas.save(q/f'encoded-opening-{j+1}.jpg',quality=93)
    assert len(all_hashes)==len(poses)
    return len(poses)


def handoff(payload):
    msg=[f'# {TITLE} — opening review','',
        '**3D approval cut only. Not a release master. No later scenes authorized.**','',
        'The 60.708-second edit starts at the locked English v2 voiceover’s sample zero. The out follows “on that patch of ground” and keeps the whole sentence and caption intact. The dry voice is unchanged beneath an original low-level stereo score and effects bed. The MP4 has selectable English captions; the adjacent SRT contains the same 18 verbatim cues.','',
        '| Time in | Picture |','|---|---|']
    marks=('Low camera over a reddish siltstone impression (Sousa).','Match cut to a cooler Koum imprint.',
           'Orbit on present-day topography, two regional pins and ≈6,000 km distance bracket.',
           'World-space scan onto the separately sourced 125 Ma relief; ≈1,000 km comparison.',
           'Title over a low flyover of an illustrative ancient floodplain.',
           'Return to the modern sphere; dive to the regional Koum marker.',
           'Oblique view across four distinct exposed surfaces.',
           'Modern riverbed concept, not field footage.',
           'Raking survey view, 283 footprints studied at one site.',
           'A generic footfall deforms the sediment. Not an identified species.',
           'Tracking shot along adjacent impressions; 34 documented trackways.',
           'Follow the local sequence and direction within this example trackway.')
    for lo,text in zip(FRAMES,marks):
        t=lo/FPS;msg.append(f'| 00:{t:06.3f} | {text} |')
    msg+=['','## Science, rights and attribution','',
          '- Distances in the narrative and labels are the rounded regional estimates in [Jacobs et al. (2024)](https://igeo.ufrj.br/inc/isc/3/03_139_Jacobs%20etal.pdf). The pinned coordinates in this independent model compare ~6,085 km and ~1,194 km; the two estimates are not exact distances between fossil specimens. The bracket is distance, not a line of travel.',
          '- The same planet radius and lens are used through the time reveal. **125 Ma is a model snapshot, not the footprints’ age.** The rewind is an editorial transition between two maps, not a reconstructed progression. The four surfaces and survey counts are based on [Menkem et al. (2026)](https://doi.org/10.1016/j.jop.2026.100416). Track casts, strata, rock and river scenes are original CGI illustrations, not replicas of the study figures, specimen scans or a witnessed crossing.',
          '- **Ancient coast and rotations:** Kocsis & Scotese (2021), [PaleoCoastlines v7.1 and PALEOMAP v19o_r1c](https://doi.org/10.1016/j.earscirev.2020.103463), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Resampled, recoloured, displaced and annotated for this film.',
          '- **Ancient height:** Scotese & Wright (2018), [PALEOMAP PaleoDEMs v2](https://doi.org/10.5281/zenodo.5460860), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Adapted from the checksum-pinned 125 Ma 8-bit mirror; resampled, shaded and relief exaggerated. **Modern:** [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/) v5.1.2 1:50m coastlines; NOAA NGDC ETOPO5, repacked by voxiverse; both public domain. Relief exaggerated in both views.',
          '- Typography: Fraunces and IBM Plex under SIL OFL 1.1. Rock albedos are generated textures; all motion, lighting, geometry and score/FX are original to this review cut. No prior-film footage or reference-only imagery used.','',
          '## Playback checks','',
          f'- {FRAMES[-1]:,} frames, 1920×1080, 24 fps, limited Rec.709. Each shot start is seekable. All frames decode.',
          f'- 48 kHz stereo AAC, {payload["audio"]["integrated_lufs"]:.1f} LUFS-I, {payload["audio"]["true_peak_dbtp"]:.1f} dBTP. Sample-accurate dry narration placement verified across the edit. A human playback check of the pronunciation of Sousa is still recommended before any release.',
          f'- MP4 SHA-256: `{hashfile(MOVIE)}`','']
    p=OUT/f'{STEM}-Review-Notes.md';p.write_text('\n'.join(msg),encoding='utf-8');return p


def verify(movie,smoke):
    source=locked(); streams=check_clocks(movie,smoke); audio=check_track(movie); cc=check_captions(movie)
    if smoke:
        print(json.dumps({'smoke_pass':True,'streams':streams,'audio':audio,'captions':cc},indent=2));return
    _, log=run(['-i',str(movie),'-c','copy','-t','0.100','-f','null','-'])
    assert 'h264 (High)' in log and 'yuv420p(tv, bt709, progressive), 1920x1080' in log and '24 fps' in log
    assert 'Audio: aac (LC)' in log and '48000 Hz, stereo' in log and '(eng): Subtitle: mov_text' in log
    run(['-loglevel','error','-xerror','-threads','2','-i',str(movie),'-map','0:v:0','-an','-sn','-f','null','-'])
    count=proof(movie)
    payload={'title':TITLE,'status':'first-minute 3D cut / awaiting owner approval','duration_seconds':END,'fps':FPS,
             'color':'Rec.709 limited range','size':[1920,1080],'all_frames_decode':True,'stills_extracted_and_checked':count,
             'shot_count':len(SHOT_NAMES),'shot_start_frames':FRAMES[:-1],'rewind_frame':FRAMES[3],'shot_audit':check_trace(),
             'tracks':streams,'captions':cc,'audio':audio,'script_sha256':source['script_sha256'],
             'geography':json.loads((PACK/'world.json').read_text())}
    p=handoff(payload)
    payload['files']=[{'name':f.name,'size':f.stat().st_size,'sha256':hashfile(f)} for f in (MOVIE,CC,p)]
    (HERE/'opening-3d-receipt.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(payload,indent=2))


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--smoke',type=Path);a=cli.parse_args()
    verify(a.smoke or MOVIE,a.smoke is not None)


if __name__=='__main__':main()
