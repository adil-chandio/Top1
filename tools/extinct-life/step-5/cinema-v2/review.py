#!/usr/bin/env python3
"""Mux and verify the cinematic revision without touching the original review."""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw
from scipy.signal import correlate

from cues import CUTS, CUES, END, FPS, FRAMES, NSAMPLES, SPF, SR
from geometry import HERE, OUT, PACK, QA, base, raw_dir, sizes
from motion import FF, Trace, compose, enc_dir
from sound import BED, FOL_CREDIT, FX, MIX, REPORT, VOICE, Q, audio, db_rms, int_samples
from finish import SRT, TITLE, cc_time, locked
from verify_opening import check_clocks

STEM='Extinct-Life-Atlantic-Tracks-Opening-3D-v2'
MOVIE=OUT/f'{STEM}.mp4'
CC=OUT/f'{STEM}.en.srt'
NOTES=OUT/f'{STEM}-Review-Notes.md'
RECEIPT=HERE/'opening-3d-v2-receipt.json'
V1=HERE.parent/'opening-3d-receipt.json'
CREDITS=('Cartography adapted from Kocsis & Scotese (2021), PaleoCoastlines v7.1 and PALEOMAP rotations, '
         'https://doi.org/10.1016/j.earscirev.2020.103463, and Scotese & Wright (2018), PALEOMAP PaleoDEMs v2, '
         'https://doi.org/10.5281/zenodo.5460860. Both CC BY 4.0, https://creativecommons.org/licenses/by/4.0/. '
         'Resampled and annotated; relief exaggerated. Present-day Natural Earth + NOAA NGDC ETOPO5, public domain. '
         '125 Ma is a model snapshot, not a footprint date. Local terrain and footprints are CGI illustrations. '+FOL_CREDIT)


def run(args, timeout=120):
    q=subprocess.run([FF,'-hide_banner','-nostdin',*args],capture_output=True,timeout=timeout)
    if q.returncode!=0:raise RuntimeError(q.stderr.decode(errors='replace')[-4500:])
    return q.stdout,q.stderr.decode('utf-8',errors='replace')


def split(s):return s.replace('\r','').strip().split('\n\n')


def cc():
    blocks=split(SRT.read_text()); cue=[x for x in blocks if cc_time(x.splitlines()[1].split(' --> ')[1])<=int(END*1000)]
    assert cue==blocks[:18] and cue[-1].endswith('was moving on that patch of ground.')
    CC.write_text('\n\n'.join(cue)+'\n',encoding='utf-8');return cue


def mux():
    out=enc_dir(); src=out/'concat.ffconcat'
    if not src.is_file():raise FileNotFoundError(f'Incomplete picture: {src}')
    if not (MIX.exists() and BED.exists() and REPORT.exists()):audio()
    OUT.mkdir(exist_ok=True,parents=True);cc();pending=MOVIE.with_suffix('.pending.mp4')
    cmd=['-loglevel','error','-y','-safe','0','-f','concat','-i',str(src),'-i',str(MIX),'-f','srt','-i',str(CC),
         '-map','0:v:0','-map','1:a:0','-map','2:s:0','-c:v','copy','-bsf:v',f'setts=pts=N*{SPF}:dts=N*{SPF}:duration={SPF}:time_base=1/{SR}',
         '-c:a','aac','-profile:a','aac_low','-b:a','288k','-ar',str(SR),'-c:s','mov_text','-disposition:s:0','0',
         '-metadata:s:a:0','language=eng','-metadata:s:s:0','language=eng','-metadata:s:s:0','handler_name=English',
         '-map_metadata','-1','-map_chapters','-1','-metadata',f'title={TITLE} — 3D opening review v2','-metadata',f'comment={CREDITS}',
         '-movflags','+faststart','-video_track_timescale',str(SR),'-movie_timescale',str(SR),str(pending)]
    run(cmd);assert 0<pending.stat().st_size<100_000_000;pending.replace(MOVIE)
    print('MOVIE_READY',MOVIE,MOVIE.stat().st_size,base.hashfile(MOVIE),flush=True)


def narration():
    s=int_samples(VOICE,NSAMPLES); m=int_samples(MIX,NSAMPLES); d=int_samples(BED,NSAMPLES)
    assert s.shape==(NSAMPLES,1) and m.shape==d.shape==(NSAMPLES,2)
    assert np.array_equal(m-d,np.broadcast_to(s,m.shape))
    meta=json.loads(REPORT.read_text())
    for p,key in ((MIX,'mix_sha256'),(BED,'bed_sha256'),(FX,'fx_sha256')):assert base.hashfile(p)==meta[key]
    vo=s[:,0]/Q
    assert db_rms(vo[round(60.536*SR):NSAMPLES-25])<-73
    q,_=run(['-loglevel','error','-i',str(MOVIE),'-map','0:a:0','-c:a','pcm_f32le','-f','f32le','-']); a=np.frombuffer(q,dtype='<f4').reshape(-1,2)
    assert 0<=len(a)-NSAMPLES<1024
    a=a[:NSAMPLES]
    rms_snr=20*np.log10(np.linalg.norm(m/Q)/np.linalg.norm(a-m/Q))
    assert rms_snr>28.,rms_snr
    review=a.mean(axis=1)-d.mean(axis=1)/Q
    lags=[]; matches=[]
    sample_times=(.107,.57,1.54,2.67,3.57,4.18,6.22,8.89,10.19,11.63,15.42,18.92,19.67,20.17,24.97,28.54,
                32.41,33.46,36.34,40.12,43.55,45.6,48.34,49.44,50.28,53.18,56.71,58.1,59.80)
    for w in sample_times:
        i=round(w*SR);j=min(NSAMPLES-416,i+24000)
        r=vo[i:j]; v=review[i-416:j+416];lag=int(correlate(v,r,mode='valid',method='fft').argmax())-416
        q=v[416+lag:416+lag+len(r)]; corr=np.dot(q,r)/(np.linalg.norm(q)*np.linalg.norm(r))
        assert lag==0 and corr>.991,(w,lag,corr)
        lags.append(lag);matches.append(float(corr))
    _, log=run(['-i',str(MOVIE),'-map','0:a:0','-af','ebur128=peak=true:framelog=verbose','-f','null','-']);q=log[log.rindex('Summary:'):]
    loud=float(re.search(r'I:\s*(-?\d+(\.\d+)?) LUFS',q).group(1)); peak=float(re.search(r'Peak:\s*(-?\d+(\.\d+)?) dBFS',q).group(1))
    assert -19.5<=loud<-15 and peak<=-1.4,(loud,peak)
    return {'exact_pcm_narration_at_unity_before_aac':True,'narration_sync_samples':sorted(set(lags)),'checkpoints':len(lags),
            'worst_window_correlation':round(min(matches),7),'aac_vs_pcm_snr_db':round(float(rms_snr),3),'lufs_i':loud,'peak_dbtp':peak}


def audio_and_graphics():
    m=json.loads(REPORT.read_text());p=enc_dir();seen={};paths=raw_dir();moves=[]
    for i,(lo,hi) in enumerate(zip(FRAMES,FRAMES[1:]),1):
        new=json.loads((p/f'{i:02d}-events.json').read_text())
        assert not set(seen)&set(new)
        seen.update(new)
        tr=[Trace(line) for line in (paths/f'{i:02d}.csv').read_text().splitlines()]
        assert len(tr)==hi-lo and all(v.f==f for v,f in zip(tr,range(lo,hi),strict=True))
        d=math.dist(tr[0].cam,tr[-1].cam)
        assert d>.30,(i,d)
        moves.append({'index':i,'frames':len(tr),'native_raster':sizes(i-1),'camera_length':round(d,3)})
        if i in (3,4):
            for one in tr[50:] if i==4 else tr:
                x,y=one.sites[i==4]
                assert x[-1] and y[-1] and abs(x[0]-y[0])<(.16 if i==4 else .58)
                if i==3: assert abs(x[0]-y[0])>.365
        if i==7:
            for one in tr[39:]:assert all(90<y<976 and 70<x<1545 for x,y in one.layers), (one.f,one.layers)
        if i==12:
            for j in range(6):
                one=tr[CUES[f'step-{j+1}'].frame-lo]; x,y=one.steps[j];assert 40<x<1880 and 126<y<1054
    fx={v['id']:v for v in m['cue_rows']}
    assert len(fx)==len(CUTS) and len(seen)==m['graphic_fx_cues']==32
    onsets=[]
    for name,frame in seen.items():
        o=fx[name];start=o['signal_first_above_minus57_dbfs']
        assert o['graphic_cue'] and frame==o['picture_frame']==CUES[name].frame
        assert frame*SPF==o['trigger_sample'] and start//SPF==frame
        assert o['first_frame_rms_dbfs']>-48
        onsets.append(start-frame*SPF)
    for event in ('contact','release','rewind'):
        y=fx[event];assert y['signal_first_above_minus57_dbfs']//SPF==CUES[event].frame
    onset_proof=pixel_onsets()
    return {'graphic_cues_audited':len(seen),'spot_fx_count':len(fx),'full_signal_timing_verified':True,
            'visual_onset_in_final_encode':onset_proof,
            'max_early_attack_ms_after_same_frame':round(max(onsets)/SR*1000,4),
            'spot_fx_peak_dbfs':m['foreground_fx_peak_dbfs'],'spot_differences_db':m['bed_minus_voice_rms_db'],
            'score_rms_dbfs':m['score_rms_dbfs'],'ambience_rms_dbfs':m['ambience_rms_dbfs'],
            'cue_rows':m['cue_rows'],'camera_moves':moves}


def pixel_onsets():
    """Check the visible event against the same clean plate, with and without its layer.

    Match decoded pixels against those two references at 960x540. This catches
    transparent entries, off-frame art, and one-frame mistakes hidden by a cue log.
    For the three title lines test the letterforms only, not their decorative rule.
    """
    graphics=[c for c in CUTS if c.show]; w,h=960,540
    filt='+'.join(f'eq(n,{c.frame})' for c in graphics)
    raw,_=run(['-loglevel','error','-threads','2','-i',str(MOVIE),'-map','0:v:0','-filter_threads','1',
               '-vf',f"select='{filt}',scale={w}:{h}:flags=lanczos:in_color_matrix=bt709:out_range=pc",
               '-fps_mode','passthrough','-pix_fmt','rgb24','-c:v','rawvideo','-threads','1','-f','rawvideo','-'])
    imgs=np.frombuffer(raw,dtype='uint8').reshape(-1,h,w,3)
    assert len(imgs)==len(graphics)
    root=raw_dir();rows=[]
    for q,picture in zip(graphics,imgs,strict=True):
        k=next(j for j,(l,u) in enumerate(zip(FRAMES,FRAMES[1:])) if l<=q.frame<u)
        n=sizes(k);stride=math.prod(n)*4;at=q.frame-FRAMES[k]
        traces=(root/f'{k+1:02}.csv').read_text().splitlines()
        with (root/f'{k+1:02}.rgba').open('rb') as fp:
            def load(f):
                fp.seek(stride*f)
                return Image.frombytes('RGBA',n,fp.read(stride)),Trace(traces[f])
            if at:
                pre,tt=load(at-1)
                assert compose(pre,tt).tobytes()==compose(pre,tt,omit=q.id).tobytes(),q.id
            src,t=load(at)
        a=np.asarray(compose(src,t).resize((w,h),Image.Resampling.LANCZOS),dtype=np.int16)
        b=np.asarray(compose(src,t,omit=q.id).resize((w,h),Image.Resampling.LANCZOS),dtype=np.int16)
        where=np.max(np.abs(a-b),axis=2)>18
        if q.id.startswith('title-'):
            y=(376+105*('title-one','title-two','title-three').index(q.id))//2
            where[:y]=False;where[y+50:]=False
        count=int(where.sum());assert count>=10,(q.id,count)
        changed=np.mean(np.abs(picture[where]-b[where]));err=np.mean(np.abs(picture[where]-a[where]));
        assert changed>err*1.27,(q.id,changed,err)
        rows.append({'id':q.id,'visible_frame':q.frame,'contrast_pixels_at_960x540':count,
                     'error_without_overlay_over_error_with_overlay':round(float(changed/max(1e-8,err)),3)})
    return rows


def phone_QA():
    frames=(25,76,141,154,212,259,287,379,453,477,488,513,719,838,966,1098,1183,1188,1219,1282,1366,1409,1453)
    imgs=[]; size=(768,432);w,h=size
    for f in frames:
        raw,_=run(['-loglevel','error','-ss',f'{f/FPS:.9f}','-threads','2','-i',str(MOVIE),'-map','0:v:0','-frames:v','1','-vf',
                   f'scale={w}:{h}:in_color_matrix=bt709:out_range=pc','-pix_fmt','rgb24','-threads','1','-f','rawvideo','-'])
        assert len(raw)==3*w*h,(f,len(raw))
        im=Image.frombytes('RGB',size,raw);x=np.asarray(im); assert x.std()>13 and x.mean()>35
        imgs.append(im.copy());im.save(QA/f'encoded-v2-{f:04d}.jpg',quality=94)
    assert len({base.hashfile(QA/f'encoded-v2-{f:04d}.jpg') for f in frames})==len(frames)
    for q in range(3):
        prs=list(zip(frames,imgs,strict=True))[q*8:q*8+8]; board=Image.new('RGB',(1360,403*((len(prs)+1)//2)),(6,13,22));p=ImageDraw.Draw(board)
        for i,(f,im) in enumerate(prs):
            xy=(i%2*680,i//2*403);board.paste(im.resize((680,382),Image.Resampling.LANCZOS),xy);p.text((xy[0]+10,xy[1]+385),f'{f/FPS:06.3f}s / REVIEW ENCODE',fill=(249,234,202))
        board.save(QA/f'v2-encoded-proof-{q+1}.jpg',quality=93)
    return len(frames)


def file_record(p):return {'name':p.name,'size':p.stat().st_size,'sha256':base.hashfile(p)}


def verify():
    src=locked(); assert MOVIE.exists();QA.mkdir(exist_ok=True,parents=True)
    for f in json.loads(V1.read_text())['files']:
        if f['name'].endswith('.mp4') or 'srt' in f['name']:assert f==file_record(OUT/f['name']),f
    stream=check_clocks(MOVIE)
    assert stream['vide']['frames']==FRAMES[-1]
    _,log=run(['-i',str(MOVIE),'-c','copy','-t','0.100','-f','null','-'])
    assert 'h264 (High)' in log and 'yuv420p(tv, bt709, progressive), 1920x1080' in log and '24 fps' in log
    assert '48000 Hz, stereo' in log and 'Audio: aac (LC)' in log and '(eng): Subtitle: mov_text' in log
    run(['-loglevel','error','-xerror','-threads','2','-i',str(MOVIE),'-map','0:v:0','-an','-sn','-f','null','-'])
    r,_=run(['-loglevel','error','-i',str(MOVIE),'-map','0:s:0','-c:s','srt','-f','srt','-'])
    assert split(r.decode())==split(CC.read_text())==split(SRT.read_text())[:18]
    a=narration(); spot=audio_and_graphics(); sample=phone_QA()
    rec={'title':TITLE,'version':'3D opening v2; awaiting owner approval; no later scenes rendered',
         'duration_seconds':END,'resolution':[1920,1080],'fps':FPS,'frame_count':FRAMES[-1],
         'color':'limited Rec.709','decoded_all_frames':True,'stills_decoded_for_visual_qc':sample,
         'voiceset':'Locked English v2 (audition 02)','voice_sha256':src['files'][0]['sha256'],
         'english_cues_round_trip':18,'last_caption_out':'00:01:00.673','mux_clocks':stream,'audio':a,
         'motion_sound_sync':spot,'geography':json.loads((PACK/'world.json').read_text()),
         'preserved_v1_video_and_captions':True,'picture_cache_key':raw_dir().name,'encoded_key':enc_dir().name,'credits':CREDITS}
    NOTES.write_text(notes(rec),encoding='utf-8')
    rec['files']=[file_record(p) for p in (MOVIE,CC,NOTES)]
    RECEIPT.write_text(json.dumps(rec,indent=2)+'\n')
    print('VERIFIED',json.dumps({'movie':rec['files'][0],'audio':a,'graphic_cues':spot['graphic_cues_audited'],
                                'spotted_sound_cues':spot['spot_fx_count'],'max_onset_ms':spot['max_early_attack_ms_after_same_frame'],
                                'english_cues':18,'duration':END},indent=2),flush=True)


def notes(rec):
    a=rec['audio']
    return f'''# {TITLE} — cinematic opening v2

**60.708 s approval cut.** Holds the rest of the film until the owner approves. The original review remains unchanged. The edit starts with the locked v2 voice at sample zero and ends after “on that patch of ground.” The embedded and sidecar captions contain the same first 18 cues, unchanged.

## Moments to review

| Cue | What to hear and see |
|---|---|
| 0:00–0:04 | Low, lit close-ups; differently coloured stone, softer contact shadows, and a textured match cut. Location names are masked on under a short mineral sound. |
| 0:06.208 | Distance type, its rule, and the two-sided bracket build; central tonal attack and restrained lock accents. No line of travel is implied. |
| 0:10.208–0:11.458 | Rewind suction, stereo sweep and low lock on the 3D scan of the separate 125 Ma globe. Model age is not an individual footprint date. |
| 0:19.708–0:20.208 | Three masked lines over a shallow, lit water/terrain scene. Each line is paired with its own tonal entry. |
| 0:32.417–0:36.208 | Count and four world-tracked geological surface marks with individual gravel-based cues. Illustration, not a measured section. |
| 0:36.208–0:43.333 | Shift from rock ambience to the illustrated Mayo Rey river; water shimmer and quieter, wide stream texture underneath. |
| 0:49.292 | Physical foot contact, shadow, soft displacement and depth-occluded grit. Low weight plus granular foley; release at 0:50.333. Not a known individual or identified species. |
| 0:56.792–0:58.458 | Six grounded local direction marks, spaced on individual dry steps. This is only movement across a small patch, not migration evidence. |

## Technical verification

- 1,457 frames at 24 fps, 1920×1080 Rec.709. Full video decode and exact picture/VO and subtitle clocks checked. Every shot has a seekable start.
- {rec['motion_sound_sync']['graphic_cues_audited']} graphic/SFX events derived from a common frame grid, including the three title lines, labels and numerical reveals. Each matching transient first crosses the audit threshold in its graphic's frame. The **43** total spot cues also include entries, anticipations and physical Foley. Score and location atmospheres are separate.
- Stereo 48 kHz AAC-LC; {a['lufs_i']:.1f} LUFS-I and {a['peak_dbtp']:.1f} dBTP. Subtracting the bed from the pre-AAC mix recovers exact original voice samples in both channels. No lag at {a['checkpoints']} check windows after AAC. Nothing re-recorded or stretched.
- CGI is new picture, textured and lit in world space, not an animated still. The modern/past geometry inputs and scientific caveats remain as in the verified original. Gravity, particles, regional labels and geology are explanatory, not a representation of a witnessed animal or crossing.
- MP4 SHA-256 `{base.hashfile(MOVIE)}`.

## Sources

{CREDITS}

Distances: rounded scholarly regional estimates, not lengths of a route. Four surfaces, 283 footprints and 34 trackways refer to the later Koum survey (Menkem et al., 2026, doi:10.1016/j.jop.2026.100416). Fonts: Fraunces and IBM Plex, SIL OFL 1.1. No footage or score from reference videos was used.
'''


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--mix',action='store_true');a.add_argument('--verify-only',action='store_true');q=a.parse_args()
    if q.mix:audio()
    if not q.verify_only:mux()
    verify()


if __name__=='__main__':main()
