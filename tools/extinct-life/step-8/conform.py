#!/usr/bin/env python3
"""Conform the new picture and stereo mix, then prove the single film export."""
from __future__ import annotations

import argparse
import json
import math
import shutil
import wave

import numpy as np
from scipy.signal import butter, sosfilt

from common import CACHE, QA, REF, OUT, MASTER, NAME, HERE, F, FPS, N, S, SRT, VO, BY, SR, SPF, reference, sha, save_json
from audit import samples, review
from render import part, sizefor
from mix_cinema import BED, MIX, FX, REPORT
from film_audio import SAMPLES, Q
import finish_film as full
import finish_sound_v2 as red

CAPS = OUT/(NAME+'.en.srt')
NOTES = OUT/(NAME+'-Handoff.md')
RECEIPT = HERE/'cinema-receipt.json'
PENDING=OUT/(NAME+'.pending.mp4')
LABEL='Cinema Edition'
CUES=('stamp-down','stamp-up','edge-chip','erosion-pop','test-down','test-up','slump','impact-bank',
      'bury','rift-down','rift-fill','rift-early')


def picture():
    out = []
    out_text=['ffconcat version 1.0']
    for k,q in enumerate(S):
        p=part(k);row=json.loads(p.with_suffix('.json').read_text())
        a,b=F[k:k+2]
        assert row['key']==q.key and (row['from_frame'],row['to_frame_exclusive'],row['frames'])==(a,b,b-a)
        assert row['shot']==k and row['bytes']==p.stat().st_size and row['sha256']==sha(p),k
        assert row['native']==list(sizefor(k)) and len(row['signature'])==64,k
        out.append(row)
        spec=str(p.resolve()).replace("'","'\\''")
        out_text.extend((f"file '{spec}'",f'duration {(b-a)/FPS:.12f}'))
    target=CACHE/'picture.ffconcat';target.write_text('\n'.join(out_text)+'\n',encoding='utf-8')
    return target,out


def check_mix():
    mix = json.loads(REPORT.read_text())
    assert (mix['program_samples'],mix['voice_sha256'],mix['locked_voice_samples'])==(N,sha(VO),SAMPLES)
    assert (mix['mix_sha256'],mix['bed_sha256'],mix['fx_sha256'])==(sha(MIX),sha(BED),sha(FX))
    attacks={r['name']:r for r in mix['first_attacks']}
    sync={}
    with wave.open(str(FX),'rb') as w:
        assert w.getnframes()==N
        for c in CUES:
            r=attacks[c]; f=BY[c].f
            assert (r['frame'],r['sample'])==(f,SPF*f)
            assert r['attack_sample'] is not None and r['attack_sample']//SPF==f,c
            w.setpos(r['sample']);x=full.i24(w,SPF).astype(np.float32)/Q
            audible=np.flatnonzero(np.max(np.abs(x),axis=1)>10**(-51/20))
            assert len(audible)>0,c
            sync[c]={'frame':f,'time_s':f/FPS,'recording_attack_ms':round((r['attack_sample']-r['sample'])*1000/SR,3),
                'foreground_onset_ms':round(int(audible[0])*1000/SR,3),'first_frame_rms_dbfs':round(20*math.log10(float(np.sqrt(np.mean(x*x)))),3)}
    for k,minimum in (('erosion',4),('valley',4),('sea_entry',5)):
        d=mix['measurements'][k]['upper_mid_difference_dB'];assert d < -minimum,(k,d)
    return mix,sync


def mux(concat,meta,out=PENDING):
    args=['-loglevel','error','-xerror','-y','-safe','0','-f','concat','-i',str(concat),'-i',str(REF),'-i',str(MIX),
        '-map','0:v:0','-map','2:a:0','-map','1:s:0','-map_metadata','1','-map_chapters','1','-c:v','copy',
        '-c:a','aac','-profile:a','aac_low','-b:a','288k','-ar',str(SR),'-c:s','copy','-disposition:s:0','0',
        '-metadata:s:a:0','language=eng','-metadata:s:s:0','language=eng','-metadata:s:s:0','handler_name=English',
        '-metadata',f'title={full.TITLE} | {LABEL}','-metadata','artist=Extinct Life','-metadata',f'comment={red.attribution(meta)}',
        *[v for i,c in enumerate(full.chapters()) for v in (f'-metadata:c:{i}',f"title={c['title']}")],
        '-movflags','+faststart','-write_btrt','0','-video_track_timescale',str(SR),'-movie_timescale',str(SR),str(out)]
    full.run(args,260)
    size=out.stat().st_size
    if size>=100_000_000:
        raise ValueError(f'Drive delivery budget exceeded: {size:,} bytes')
    print('CONFORM_READY',size,flush=True)


def phone(meta,pcm):
    old=QA/'archive-aac.f32'
    full.run(['-loglevel','error','-xerror','-y','-i',str(REF),'-map','0:a:0','-c:a','pcm_f32le','-f','f32le',str(old)],150)
    before=np.memmap(old,dtype='<f4',mode='r').reshape(-1,2)
    after=np.memmap(pcm,dtype='<f4',mode='r').reshape(-1,2)
    assert len(before)==len(after) and N<=len(after)<N+1024
    keys=((250,4800),(2500,5000));fil=[butter(2,v,fs=SR,btype='bandpass',output='sos') for v in keys]
    notes={}
    def db(x):return round(float(10*np.log10(np.mean(x*x)+1e-20)),3)
    with wave.open(str(VO),'rb') as v:
        for key,stat in meta['measurements'].items():
            a,b=(round(t*SR) for t in stat['seconds']);v.setpos(a)
            voice=full.i24(v,b-a)[:,0].astype(np.float32)/Q
            iso0=before[a:b].mean(axis=1)-voice;iso1=after[a:b].mean(axis=1)-voice
            q=[]
            for f in fil:q.append([db(sosfilt(f,x)) for x in (iso0,iso1,voice)])
            notes[key]={'seconds':stat['seconds'],'old_new_voice_dbfs':dict(zip(('phone_mono_250–4800','presence_mono_2500–5000'),q,strict=True))}
            if key in ('mayo','erosion','valley','fault','sea_entry'):assert q[0][1]<q[0][0]-1.1,(key,q)
            if key in ('erosion','valley'):assert q[1][1]<q[1][2]-2,(key,q)
    return notes


def compare_visual(movie):
    # Compare footage before looking at the encode, so a bad conform cannot
    # earn a pass just because the old tape also decodes cleanly.
    p=review(movie,'master')
    summary=json.loads((QA/'master-visual.json').read_text())
    marks=[(F[k]+F[k+1])//2 for k in range(len(S))]
    q=samples(REF,marks);rows=[]
    for k,f in enumerate(marks):
        a=p[f].astype(np.float32);b=q[f].astype(np.float32)
        signal=np.std(a.mean(axis=-1));change=float(np.mean(np.abs(a-b)))
        check=summary['shots'][k]
        assert signal>5.5 and a.mean()>10.,(k,signal,a.mean())
        assert change>2.6,(k,change)
        assert max(check['rgb_mae'])>0.52,(k,check)
        rows.append({'shot':k,'key':S[k].key,'midframe':f,'mean_luma_std':round(float(signal),3),
            'mean_rgb_change_vs_IC':round(change,3),'within_shot_rgb_delta':check['rgb_mae']})
    return {'frames_reviewed':summary['samples'],'comparison_shots':rows,'all_shots_differ_from_archive':True,
        'median_shot_midpoint_delta':round(float(np.median([x['mean_rgb_change_vs_IC'] for x in rows])),3)}


def verify(movie,ref,parts,meta,sync):
    check=full.streams(movie)
    _,log=full.run(['-i',str(movie),'-map','0','-c','copy','-t','0.1','-f','null','-'],65)
    for marker in ('h264 (High)','yuv420p(tv, bt709, progressive), 1920x1080','24 fps','Audio: aac (LC)','48000 Hz, stereo','(eng): Subtitle: mov_text'):
        assert marker in log,marker
    for c in ref['chapters']:assert c['title'] in log,c
    time=red.track_fingerprints(movie)
    # reference() already verified the whole IC file against its receipt.
    lock=red.track_fingerprints(REF)
    assert lock['video']['sample_bytes_sha256']==ref['video_samples_sha256']
    assert all(time[k]==lock[k] for k in ('subtitles','chapters'))
    assert time['video']['sample_bytes_sha256']!=lock['video']['sample_bytes_sha256']
    print('GRID_AND_TEXT_LOCKED',F[-1],len(S),flush=True)
    cc,windows=full.captions(movie,CAPS)
    pcm=QA/'cinema-aac.f32'
    audio,_=full.audio(windows,movie=movie,mix_path=MIX,bed_path=BED,report_path=REPORT,pcm=pcm)
    assert audio['all_offsets_samples']==[0] and audio['sync_windows']==cc['english_cues']==127
    phone_audit=phone(meta,pcm)
    frames=red.check_decode(movie); print('ALL_FRAMES_DECODED',frames,flush=True)
    visual=compare_visual(movie)
    return dict(title=full.TITLE,edition=LABEL,status='Owner review only; not published',
        duration_s=N/SR,frames=frames,fps=FPS,original_archive=ref['files'][0],streams=check,track_fingerprints=time,
        current_aac_packets=check['soun']['packet_samples'],
        chapters=ref['chapters'],caption_audit=cc,picture=visual,parts=parts,sync=sync,
        audio=audio,decoded_phone_band=phone_audit,stem_measurements=meta['measurements'],sound_sources=red.credit_rows(meta),
        voice_source_sha256=meta['voice_sha256'],human_pronunciation_signoff=False)


def handoff(r):
    a=r['audio'];q=r['stem_measurements'];mp4=r['files'][0]
    notes=[f'# {full.TITLE}', '', f'**{LABEL} · 07:25.667 · 1080p / 24 fps · Owner review**', '',
           'One complete revision of the same film. The Investigation Cut and Sound Redesign remain intact. The English delivery, the timing grid, and the scientific qualifications remain locked.', '',
           'The edit ties each scene to the next question: a gap in space, a print that changes with the mud, rocks we can compare in time, a possible habitat connection, and the rocks that actually moved.', '',
           '| Time | What changed |','|---|---|',
           '| 00:00–00:36 | Recessed track surfaces, moving curved Earth, the two sourced epochs, then a title over a 3D floodplain. Cartographic pins move with the land; both numbers are regional separations. |',
           '| 00:36–02:31 | Field and near-ground camera paths, foot weight and release, a fractured edge, retained photogrammetry logic, and a matched tool in firm and soft mud. |',
           '| 02:31–03:34 | Raking light for ripple and crack evidence, a water front that intersects the terrain, and close grain, mat and burial illustrations. |',
           '| 03:34–04:55 | Curved Brazil locator, two separately lit riverbanks, preserved rims and a comparison of broad rock-age windows. |',
           '| 04:55–06:43 | Rotating reconstruction, layered section motion, a valley and separate habitats, plus a rigged coelacanth-to-fossil cut. Other basin finds are kept separate from footprint finds. |',
           '| 06:43–07:19 | Dry fault movement precedes rising water. Return to the present gap, then the paired prints. The prints stay in their beds as the blocks part. No new journey line. |',
           '', '## Sound and checks', '',
           f"- The stereo mix was rendered from the dry voice, scene ambience, reshaped music and spot effects. Keeping all {a['voice_original_samples']:,} original narration samples before AAC let us test all {a['sync_windows']} spoken windows at zero decoded sample lag.",
           f"- In the isolated overlay the 2.5–5 kHz band is **{abs(q['erosion']['upper_mid_difference_dB']):.1f} dB lower** during erosion and **{abs(q['valley']['upper_mid_difference_dB']):.1f} dB lower** in the valley than on the preceding cut. Encoded stereo and a restricted mono playback band were both measured. These are signal checks, not human listening approval.",
           f"- **{a['lufs_i']:.1f} LUFS-I / {a['peak_dbtp']:.1f} dBTP**, 48 kHz stereo AAC. All {r['frames']:,} video frames decoded; {r['picture']['frames_reviewed']} visual samples on 66 shots. Nine original chapters and all 127 selectable English captions; the `.en.srt` matches.",
           '- Pronunciation: the locked take uses the cue **Sohza** for *Sousa*. A human listen at **03:34–03:39** is still recommended before publication; the narration has not been respoken.', '',
           '## Science and sources', '',
           '- 125 Ma refers to the geographic reconstruction, not the date of a track. The 6,000 and 1,000 km figures compare regions; neither is a travel distance. The ≈69 cm figure describes one impression. Similar outlines, sediments and broad ages do not show the same animal, river or day. All local 3D examples are illustrations.',
           '- [Jacobs et al. (2024)](https://igeo.ufrj.br/inc/isc/3/03_139_Jacobs%20etal.pdf), [Menkem et al. (2026)](https://doi.org/10.1016/j.jop.2026.100416), [Carvalho, Borghi & Leonardi (2013)](https://doi.org/10.1016/j.cretres.2013.04.004).',
           '- Ancient maps adapted from [Kocsis & Scotese PaleoCoastlines / rotations](https://doi.org/10.1016/j.earscirev.2020.103463) and [Scotese & Wright PaleoDEMs v2](https://doi.org/10.5281/zenodo.5460860), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Present-day basemap: Natural Earth and NOAA ETOPO5, public domain. Display type: Fraunces and IBM Plex, SIL OFL 1.1.',
           '- Sound recordings were edited, mixed and spatialized as illustrations, not represented as location recordings or endorsements. Credits are also embedded in the MP4.', '',
           '| Recordist / library | License |','|---|---|']
    notes.extend(f"| [{s['credit']}]({s['original_url']}) | [{s['license']}]({s['license_url']}) |" for s in r['sound_sources'])
    notes.extend(['',f"`{mp4['name']}` · {mp4['bytes']:,} bytes · SHA-256 `{mp4['sha256']}`",''])
    NOTES.write_text('\n'.join(notes),encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify-only',action='store_true');p.add_argument('--audio-preflight',action='store_true');x=p.parse_args()
    ref=reference();meta,sync=check_mix();OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    if x.audio_preflight:
        probe=QA/'audio-check.mp4';full.run(['-loglevel','error','-y','-i',str(REF),'-i',str(MIX),'-map','1:a:0','-map','0:s:0',
            '-c:s','copy','-c:a','aac','-b:a','288k','-ar',str(SR),'-movie_timescale',str(SR),str(probe)],160)
        cc,windows=full.captions(probe,SRT)
        pcm=QA/'preflight.f32'
        a,_=full.audio(windows,movie=probe,mix_path=MIX,bed_path=BED,report_path=REPORT,pcm=pcm)
        assert a['sync_windows']==cc['english_cues']==127 and a['all_offsets_samples']==[0]
        phone(meta,pcm)
        print('AUDIO_PREFLIGHT_READY',cc['english_cues'],a['lufs_i'],a['peak_dbtp'],flush=True);return
    concat,parts=picture();target=MASTER if x.verify_only else PENDING
    if x.verify_only:assert full.file_record(target)==json.loads(RECEIPT.read_text())['files'][0]
    else:
        shutil.copyfile(SRT,CAPS);mux(concat,meta,target)
    record=verify(target,ref,parts,meta,sync)
    if not x.verify_only:target.replace(MASTER)
    record['files']=[full.file_record(MASTER),full.file_record(CAPS)]
    handoff(record);record['files'].append(full.file_record(NOTES));save_json(RECEIPT,record)
    print('CINEMA_EDITION_VERIFIED',json.dumps(record['files'],ensure_ascii=False),flush=True)


if __name__=='__main__':main()
