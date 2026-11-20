#!/usr/bin/env python3
"""Remux and verify the sound-redesigned full film from the locked review MP4.

No renderer or opening inputs are needed. The original MP4 supplies the AVC,
subtitle and chapter tracks. Only the soundtrack is replaced.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
import mmap
import re
import shutil
import struct
import wave

import numpy as np
from scipy.signal import butter, sosfilt

import finish_film as full
from assets import HERE, LOCK, OUT, SRT, VO, base, media_lock
from cut import B, BY, F, FPS, N, SPF, SR
from sound_v2 import BED, DIR, FX, MIX, PLAN, Q, REPORT, SOURCE_LOCK, SAMPLES, db_rms, i24

STEM=full.STEM+'-Sound-Redesign'
SOURCE=full.MOVIE; MOVIE=OUT/f'{STEM}.mp4'; CAPTIONS=OUT/f'{STEM}.en.srt'; NOTES=OUT/f'{STEM}-Handoff.md'
RECEIPT=HERE/'sound-v2-receipt.json'; DECODED=DIR/'decoded-sound-v2.f32'; ORIGINAL=DIR/'decoded-original.f32'
REVIEW=(
    ('00:06', 'The modern distance lands with a stone tick and a soft mallet note. Around **00:10** the map sweeps across the stereo field into the 125 Ma snapshot.'),
    ('00:37 / 00:49', 'Moving stream water gives way to a close foot compression, then a wet release. At **00:57**, six separate steps cross the near field.'),
    ('01:18', 'Listen for the initial rock fracture, followed by the separate pieces shedding from the edge.'),
    ('02:04–02:11', 'Firm mud on the left has a short dry crunch; the soft mud on the right has a thicker push and suction as the stamp lifts. The smaller grains collapse afterwards.'),
    ('02:49 / 02:57 / 03:24', 'Water drains, comes back over the exposed print, then gives way to dry burial grit.'),
    ('05:14', 'A sharp fault crack opens into sliding rock; a second, deeper settling hit follows.'),
    ('05:35 / 06:02', 'Open valley water gives way to a more filtered underwater space at the fish.'),
    ('06:45–06:52', 'The late rift fractures first. A recorded wave builds into the space instead of playing beneath the entire sequence.'),
)
LICENSES={'CC0-1.0':'https://creativecommons.org/publicdomain/zero/1.0/', 'CC-BY-3.0':'https://creativecommons.org/licenses/by/3.0/'}


def source_lock():
    p=json.loads(full.RECEIPT.read_text());r=p['files'][0]
    assert r['name']==SOURCE.name and SOURCE.stat().st_size==r['bytes'] and base.hashfile(SOURCE)==r['sha256'], SOURCE
    assert p['frames_all_decoded'] and p['end_frame_exclusive']==F[-1]
    assert p['audio']['voice_exact_before_aac'] and p['audio']['all_offsets_samples']==[0]
    return p


def credit_rows(meta):
    selected=set(meta['used_sources']);orig={};found=set()
    for x in json.loads(SOURCE_LOCK.read_text()):
        if x['key'] not in selected:continue
        k=(x['credit'],x['original_url'],x['license']);orig.setdefault(k,[]).append(x['key']);found.add(x['key'])
    assert found==selected
    return [{'credit':a,'original_url':b,'license':c,'license_url':LICENSES[c],'keys':ks} for (a,b,c),ks in orig.items()]


def attribution(meta):
    # Preserve the picture credits; the current Foley credit replaces the
    # rejected mix's credits. Include full CC BY attribution in-file too.
    body=full.CREDITS.removesuffix(full.FOL_CREDIT).strip()
    new='Sound redesign: recordings edited, layered, equalized, and spatialized; original arrangement. '
    rows=credit_rows(meta)
    new+='; '.join(f"{q['credit']} ({q['original_url']}, {q['license']})" for q in rows)+'. '
    new+='Licenses: '+', '.join(LICENSES.values())+'. No endorsement implied.'
    return body+' '+new


def mux(picture):
    meta=json.loads(REPORT.read_text());assert base.hashfile(MIX)==meta['mix_sha256']
    OUT.mkdir(parents=True,exist_ok=True);temp=MOVIE.with_suffix('.pending.mp4')
    chapters=full.chapters();assert picture['chapters']==chapters
    full.run(['-loglevel','error','-xerror','-y','-i',str(SOURCE),'-i',str(MIX),'-map','0:v:0','-map','1:a:0','-map','0:s:0',
              '-map_metadata','0','-map_chapters','0','-c:v','copy','-c:s','copy','-disposition:s:0','0',
              '-c:a','aac','-profile:a','aac_low','-b:a','288k','-ar',str(SR),
              '-metadata:s:a:0','language=eng','-metadata:s:s:0','language=eng','-metadata:s:s:0','handler_name=English',
              '-metadata',f'title={full.TITLE} | Sound Redesign','-metadata','artist=Extinct Life','-metadata',f'comment={attribution(meta)}',
              *[arg for i,c in enumerate(chapters) for arg in (f'-metadata:c:{i}',f"title={c['title']}")],
              '-movflags','+faststart','-write_btrt','0','-video_track_timescale',str(SR),'-movie_timescale',str(SR),str(temp)],260)
    assert temp.stat().st_size<100_000_000,temp.stat().st_size
    assert full.streams(temp)==picture['streams']
    shutil.copyfile(SRT,CAPTIONS);temp.replace(MOVIE)
    print('REMUX_READY',MOVIE.stat().st_size,base.hashfile(MOVIE),flush=True)


def track_fingerprints(file):
    """Compare actual samples + decode/display info, independent of interleave.

    Chunk layout and nominal bitrate headers can differ in an audio remux.
    The AVC configuration, colour metadata, sample bytes, composition/decode
    offsets, sync samples and subtitle/chapter samples may not.
    """
    names={b'vide':'video',b'sbtl':'subtitles',b'text':'chapters'};out={}
    with file.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as buf:
        def boxes(loc):return dict(full.children(buf,*loc))
        def read(loc):return buf[loc[0]:loc[1]]
        top=boxes((0,len(buf)));mdat_lo,mdat_hi=top[b'mdat']
        for kind,track in full.children(buf,*top[b'moov']):
            if kind!=b'trak':continue
            t=boxes(track);m=boxes(t[b'mdia']);h=m[b'hdlr'][0]+8;role=buf[h:h+4]
            if role not in names:continue
            q=boxes(boxes(m[b'minf'])[b'stbl']);d=q[b'stsd'];u,v=d
            assert struct.unpack_from('>I',buf,u+4)==(1,)
            ((codec,entry),)=full.children(buf,u+8,v)
            assert codec=={b'vide':b'avc1',b'sbtl':b'tx3g',b'text':b'text'}[role]
            j=entry[0]+(78 if role==b'vide' else 38)
            ext={k:read(r) for k,r in full.children(buf,j,entry[1]) if k!=b'btrt'}
            expected={b'avcC',b'colr'} if role==b'vide' else {b'ftab'}
            assert expected<=set(ext),(role,ext.keys())
            description=codec+buf[entry[0]:j]+b''.join(k+v for k,v in sorted(ext.items()))
            u,v=q[b'stsz'];fixed,n=struct.unpack_from('>II',buf,u+4)
            sizes=[fixed]*n if fixed else [a for a, in struct.iter_unpack('>I',buf[u+12:v])]
            assert len(sizes)==n
            addresses=full.table(buf,q[b'stco'],'I') if b'stco' in q else full.table(buf,q[b'co64'],'Q')
            runs=full.table(buf,q[b'stsc'],'III');assert runs[0][0]==1 and runs[-1][0]<=len(addresses)
            payload=hashlib.sha256();index=j=0
            for chunk,(off,) in enumerate(addresses,1):
                if j+1<len(runs) and chunk==runs[j+1][0]:j+=1
                _,number,description_index=runs[j];assert description_index==1 and index+number<=n
                end=off+sum(sizes[index:index+number]);assert mdat_lo<=off<=end<=mdat_hi
                payload.update(buf[off:end]);index+=number
            assert index==n
            entries={'sample_bytes_sha256':payload.hexdigest(),'sample_count':n,'sample_description_sha256':hashlib.sha256(description).hexdigest()}
            for field in (b'stts',b'ctts',b'stss',b'stsz'):
                if field in q:entries[field.decode()+'_sha256']=hashlib.sha256(read(q[field])).hexdigest()
            for field,loc in (('media_clock_language',m[b'mdhd']),('edit_list',t[b'edts']),('handler',m[b'hdlr'])):
                entries[field+'_sha256']=hashlib.sha256(read(loc)).hexdigest()
            out[names[role]]=entries
    assert set(out)==set(names.values())
    return out


def check_decode(file):
    stdout,_=full.run(['-loglevel','error','-nostats','-xerror','-err_detect','explode','-threads','2','-i',str(file),
        '-map','0:v:0','-an','-sn','-dn','-fps_mode','passthrough','-progress','pipe:1','-f','null','-'],300)
    progress=stdout.decode();frames=[int(n) for n in re.findall(r'^frame=\s*(\d+)$',progress,re.M)]
    assert frames and frames[-1]==F[-1] and progress.strip().endswith('progress=end'),progress[-500:]
    return frames[-1]


def phone_check():
    # Same VO, same scene and no gain normalization of either version. Filter
    # a mono sum to simulate limited playback bandwidth. Quantify the overlay
    # on both actual decoded exports; this is not a claim of human playback.
    full.run(['-loglevel','error','-xerror','-y','-i',str(SOURCE),'-map','0:a:0','-c:a','pcm_f32le','-f','f32le',str(ORIGINAL)],110)
    old,new=[np.memmap(p,dtype='<f4',mode='r').reshape(-1,2) for p in (ORIGINAL,DECODED)]
    assert len(old)==len(new) and N<=len(new)<N+1024
    eq=butter(2,(250,4800),btype='bandpass',fs=SR,output='sos');stats={}
    with ExitStack() as stack:
        v,b,f=[stack.enter_context(wave.open(str(p),'rb')) for p in (VO,BED,FX)]
        for k,(lo,hi) in PLAN.items():
            i=max(0,round((lo-.050)*SR));sample=round(lo*SR);j=round(hi*SR);pre=sample-i
            y=np.zeros(j-i,dtype=np.float32);u=max(0,min(j,SAMPLES)-i)
            if u:
                v.setpos(i);y[:u]=i24(v,u)[:,0]/Q
            band_vo=sosfilt(eq,y)[pre:]
            iso=[sosfilt(eq,p[i:j].mean(axis=1)-y)[pre:] for p in (old,new)]
            b.setpos(i);bnew=i24(b,j-i).astype(np.float32)/Q
            f.setpos(i);fnew=i24(f,j-i).astype(np.float32)/Q
            o,n=map(db_rms,iso);vdb=db_rms(band_vo)
            mid=db_rms(bnew[pre:].mean(axis=1));both=db_rms(bnew[pre:]);fdb=db_rms(sosfilt(eq,fnew.mean(axis=1))[pre:])
            row={'from_s':lo,'to_s':hi,'original_mono_band_overlay_dbfs':round(o,3),'redesign_mono_band_overlay_dbfs':round(n,3),
                 'redesign_mono_band_foley_dbfs':round(fdb,3),'unchanged_mono_band_voice_dbfs':round(vdb,3),
                 'change_mono_band_overlay_db':round(n-o,3),'stereo_to_mono_fold_loss_db':round(both-mid,3)}
            stats[k]=row
    improvements=[x['change_mono_band_overlay_db'] for x in stats.values()];total_loss=max(x['stereo_to_mono_fold_loss_db'] for x in stats.values())
    median=round(float(np.median(improvements)),3)
    assert median>=6.5 and min(improvements)>2. and total_loss<4.2,(median,min(improvements),total_loss)
    return {'comparison':'decoded AAC, (L+R)/2, bandpass 250–4800 Hz, unchanged dry narration subtracted',
            'review_windows':len(stats),'median_overlay_increase_db':median,'min_overlay_increase_db':min(improvements),
            'max_stereo_to_mono_fold_loss_db':total_loss,'windows':stats}


def sync(meta):
    ledger={r['name']:r for r in meta['first_attacks']};assert set(ledger)==set(BY) and len(ledger)==len(B)==77
    for q in B:
        a=ledger[q.key]
        assert a['trigger_sample']==q.sample and a['one_frame_rms_dbfs']>-46,(q.key,a)
        assert all(a[k]//SPF==q.f for k in ('attack_sample','isolated_attack_sample')),(q.key,a)
    return {'picture_spots':len(ledger),'supporting_spots':len(meta['additional_attacks']),'kinetic_graphic_entries':sum(bool(q.text) for q in B),
        'all_anchor_attacks_on_original_frame':True,
        'max_foreground_bus_attack_delay_ms':round(1000/SR*max(a['attack_sample']-a['trigger_sample'] for a in ledger.values()),4),
        'max_isolated_attack_delay_ms':round(1000/SR*max(a['isolated_attack_sample']-a['trigger_sample'] for a in ledger.values()),4),
        'anchors':list(ledger.values()),'supporting':meta['additional_attacks']}


def handoff(r):
    a=r['audio'];m=r['small_speaker_simulation'];s=r['sync'];f=r['files'][0]
    text=[f'# {full.TITLE}', '', '**Sound Redesign · Full film · 07:25.667 · For review**', '',
          'The first full cut’s audio was too far behind the narration. This pass rebuilds the soundtrack scene by scene: close contact sounds, distinctly wet and dry materials, recorded wind and water, and a restrained score that gives those actions space. It is not a volume increase on the old mix.', '',
          'The picture is the original 1080p24 cut, copied without re-encoding. The locked English narration was not replayed, shifted, processed, or changed in level. The MP4 carries all 127 selectable English captions; the matching `.en.srt` is included for players that do not show embedded text.', '',
          '## Where to listen', '', '| Film time | Change |','|---|---|']
    text.extend(f'| **{t}** | {note} |' for t,note in REVIEW)
    text+=['','To compare, play the original and the redesign at the same device volume and seek to the same time. Start with **02:04–02:11** or **06:45–06:52**. Headphones reveal the movement, but the material changes are in the mono mix as well.', '',
           '## Verification', '',
           f"- All **{r['decoded_video_frames']:,}** frames of the revised export decoded. All AVC sample bytes, composition/decode timing and keyframes, timed subtitle samples and chapter entries match the original.",
           f"- Stereo AAC-LC at 48 kHz: **{a['lufs_i']:.1f} LUFS-I / {a['peak_dbtp']:.1f} dBTP**. Subtracting the designed overlay from the pre-AAC integer mix recovers the exact dry recording. **{a['sync_windows']}** decoded narration checkpoints match at zero samples of lag. **{s['picture_spots']}** matched spot cues + **{s['supporting_spots']}** supporting effects; the **{s['kinetic_graphic_entries']}** existing type entries keep their original cue frames.",
           f"- At {m['review_windows']} representative moments, the decoded effects/music overlay was a median **+{m['median_overlay_increase_db']:.1f} dB** above the old overlay after a mono fold and 250–4,800 Hz bandwidth check, not an increase in the narration level. This is a small-speaker simulation, not human approval.",
           "- The original review file and both opening versions are preserved. **Sousa** at 03:34–03:39 still merits a human pronunciation check before release. Nothing published or made public.",
           f"- Revised MP4: {f['bytes']:,} bytes · SHA-256 `{f['sha256']}`.", '',
           '## Sound credits', '',
           'Recordings were trimmed, repitched or time-shaped as needed, layered, equalized, and spatially placed. They represent the scenes editorially; they are not field recordings from the fossil sites.', '',
           '| Original recordist / library | Material used | Rights |','|---|---|---|']
    material={'wind':'Location wind','stream':'Stream','river':'Brook / creek','ocean':'Waves in Veracruz','lake':'Small shore laps',
              'plop1':'Rock into water (take 1)','plop3':'Rock into water (take 3)','tap':'Puddle splash','splash':'Splash','skip':'Stick thrown into water',
              'gravel1':'Gravel dig / loose gravel','sand1':'Sand footsteps','crack1':'Stone cracks','hard1':'Hard-surface footsteps','wet1':'Water footsteps',
              'stone1':'RPG Audio stone steps','vibeD':'Vibraphone (mallet and bowed), bass drum, cabasa and ocean drum'}
    for q in r['sound_sources']:
        key=next((k for k in q['keys'] if k in material),q['keys'][0]);label=material.get(key,', '.join(q['keys']))
        text.append(f"| [{q['credit']}]({q['original_url']}) | {label} | [{q['license']}]({q['license_url']}) |")
    text+=['','No endorsement is implied. The build pins source files and per-asset credit documents.','',
           '## Picture sources and interpretation', '',
           '- Footprint and geology research: [Jacobs et al. (2024)](https://igeo.ufrj.br/inc/isc/3/03_139_Jacobs%20etal.pdf), [Menkem et al. (2026)](https://doi.org/10.1016/j.jop.2026.100416), and [Carvalho, Borghi & Leonardi (2013)](https://doi.org/10.1016/j.cretres.2013.04.004). The two modeled distances compare regions; they are not a route, and do not establish a single individual, age or linked river.',
           '- Ancient geography: [Kocsis & Scotese PaleoCoastlines v7.1 and PALEOMAP rotations](https://doi.org/10.1016/j.earscirev.2020.103463) and [Scotese & Wright PaleoDEMs v2](https://doi.org/10.5281/zenodo.5460860), both [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Resampled, recoloured, shaded and annotated with exaggerated relief. 125 Ma is the model time, not a dated footprint.',
           '- Present day: [Natural Earth 1:50m](https://www.naturalearthdata.com/about/terms-of-use/) and NOAA NGDC ETOPO5, public domain. All renderings of tracks, terrain, sediments and fish are original CGI illustrations. Fonts: Fraunces and IBM Plex, SIL OFL 1.1.', '',
           '## Unchanged chapters', '', '| In | Chapter |','|---|---|']
    text.extend(f"| {full.tc(q['start_frame'])} | {q['title']} |" for q in r['chapters']);text.append('')
    NOTES.write_text('\n'.join(text),encoding='utf-8')


def verify(picture):
    streams=full.streams(MOVIE);assert streams==picture['streams']
    source_track=track_fingerprints(SOURCE);actual=track_fingerprints(MOVIE)
    for k in source_track:
        assert source_track[k]==actual[k],(k,{field:(v,actual[k].get(field)) for field,v in source_track[k].items() if v!=actual[k].get(field)})
    _,log=full.run(['-i',str(MOVIE),'-map','0','-c','copy','-t','0.100','-f','null','-'])
    for x in ('h264 (High)','yuv420p(tv, bt709, progressive), 1920x1080','24 fps','Audio: aac (LC)','48000 Hz, stereo','(eng): Subtitle: mov_text'):
        assert x in log,(x,log[-2000:])
    assert all(c['title'] in log for c in picture['chapters']),log[-4000:]
    cc,windows=full.captions(MOVIE,CAPTIONS);assert cc==picture['caption_audit']
    print('PICTURE_CAPTIONS_AND_CHAPTERS_MATCH',flush=True)
    a,meta=full.audio(windows,movie=MOVIE,mix_path=MIX,bed_path=BED,report_path=REPORT,pcm=DECODED)
    assert a['sync_windows']==127 and a['all_offsets_samples']==[0] and base.hashfile(FX)==meta['fx_sha256']
    s=sync(meta);mobile=phone_check();print('MONO_BAND_PASS',mobile['median_overlay_increase_db'],mobile['min_overlay_increase_db'],flush=True)
    frames=check_decode(MOVIE)
    r={'title':full.TITLE,'status':'Sound redesign · full-film review, not published','duration_s':N/SR,'fps':FPS,'frames':F[-1],
       'original_review':picture['files'][0],
       'picture_and_caption_samples_identical':True,'video_reencoded':False,'locked_track_fingerprints':actual,'streams':streams,'decoded_video_frames':frames,
       'chapters':picture['chapters'],'caption_audit':cc,'audio':a,'source_voice_sha256':LOCK['files'][0]['sha256'],'sync':s,
       'local_overlay':meta['local_comparison'],'small_speaker_simulation':mobile,'sound_sources':credit_rows(meta),
       'sound_source_lock_sha256':base.hashfile(SOURCE_LOCK),'mix_stems':{k:meta[k+'_sha256'] for k in ('bed','mix','fx')},
       'voice_human_pronunciation_review':'Sousa, 03:34–03:39; not a human signoff',
       'files':[full.file_record(MOVIE),full.file_record(CAPTIONS)]}
    handoff(r);r['files'].append(full.file_record(NOTES));RECEIPT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('FULL_SOUND_REDESIGN_VERIFIED',json.dumps({'file':r['files'][0],'decoded_frames':frames,'audio':a,'phone_pass_windows':mobile['review_windows'],
        'median_phone_audibility_gain_db':mobile['median_overlay_increase_db'],'max_mono_fold_loss_db':mobile['max_stereo_to_mono_fold_loss_db'],
        'sync':{k:v for k,v in s.items() if k not in ('anchors','supporting')}},indent=2),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);x=p.add_mutually_exclusive_group();x.add_argument('--verify-only',action='store_true');x.add_argument('--mux-only',action='store_true')
    args=p.parse_args();media_lock();picture=source_lock()
    if not args.verify_only:mux(picture)
    if not args.mux_only:verify(picture)


if __name__=='__main__':main()
