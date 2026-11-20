#!/usr/bin/env python3
"""Assemble and audit the complete cut, without changing the locked English source."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
import math
import mmap
import re
import shutil
import struct
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import correlate

from assets import FIELDS,FONTS,HERE,HOME,LOCK,OUT,SCRIPT,SRT,VO,base,media_lock
from cut import B,BY,CHAPTERS,F,FPS,N,S,SPF,SR,frame,inside,shot_of
from film_picture import FF, QA, VIDEO, path, raster
from film_audio import BED, MIX, Q, REPORT, SAMPLES, FOL_CREDIT
from finish import TITLE,cc_time

STEM='Extinct-Life-Atlantic-Tracks-Cinematic-Full'
MOVIE=OUT/f'{STEM}.mp4'; CAPTIONS=OUT/f'{STEM}.en.srt'; NOTES=OUT/f'{STEM}-Handoff.md'
RECEIPT=HERE/'full-film-receipt.json'
CREDITS=(
    'Footprint and geology research: Jacobs et al. (2024), NMMNHS Bulletin 95 pp. 199–212; '
    'Menkem et al. (2026), https://doi.org/10.1016/j.jop.2026.100416; '
    'Carvalho, Borghi & Leonardi (2013), https://doi.org/10.1016/j.cretres.2013.04.004. '
    'Cartography adapted from Kocsis & Scotese (2021), PaleoCoastlines v7.1 and PALEOMAP rotations, '
    'https://doi.org/10.1016/j.earscirev.2020.103463, and Scotese & Wright (2018), PALEOMAP PaleoDEMs v2, '
    'https://doi.org/10.5281/zenodo.5460860, both CC BY 4.0, https://creativecommons.org/licenses/by/4.0/. '
    'Resampled, coloured, shaded and annotated; relief exaggerated. Present day: Natural Earth 1:50m '
    'and NOAA NGDC ETOPO5, public domain. Local sets and all fossil/terrain demonstrations are original CGI. '
    '125 Ma is a model snapshot, not a footprint date. '+FOL_CREDIT)


def run(args,timeout=180):
    p=subprocess.run([FF,'-hide_banner','-nostdin',*args],capture_output=True,timeout=timeout)
    if p.returncode!=0:raise RuntimeError(p.stderr.decode(errors='replace')[-7000:])
    return p.stdout,p.stderr.decode('utf-8',errors='replace')


def chapters():
    starts=[frame(t) for _,t in CHAPTERS];ends=starts[1:]+[F[-1]]
    return [{'title':title,'start_frame':a,'end_frame':b} for (title,_),a,b in zip(CHAPTERS,starts,ends,strict=True)]


def mux():
    src=VIDEO/'concat.ffconcat'
    if not src.is_file() or any(not path(k).is_file() or not path(k).with_suffix('.json').is_file() for k in range(len(S))):
        raise FileNotFoundError('Picture is incomplete: need 66 encoded parts and their receipts')
    if not all(p.is_file() for p in (BED,MIX,REPORT)):raise FileNotFoundError('Build the full mix before muxing')
    media_lock(); OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(SRT,CAPTIONS)
    meta=QA/'chapters.ffmeta';text=[';FFMETADATA1']
    for c in chapters():text+=['[CHAPTER]',f'TIMEBASE=1/{SR}',f"START={c['start_frame']*SPF}",f"END={c['end_frame']*SPF}",f"title={c['title']}"]
    meta.write_text('\n'.join(text)+'\n',encoding='utf-8');temp=MOVIE.with_suffix('.pending.mp4')
    run(['-loglevel','error','-y','-safe','0','-f','concat','-i',str(src),'-i',str(MIX),'-f','srt','-i',str(CAPTIONS),'-f','ffmetadata','-i',str(meta),
         '-map','0:v:0','-map','1:a:0','-map','2:s:0','-map_metadata','-1','-map_chapters','3','-c:v','copy',
         '-c:a','aac','-profile:a','aac_low','-b:a','224k','-ar',str(SR),'-c:s','mov_text','-disposition:s:0','0',
         '-metadata:s:a:0','language=eng','-metadata:s:s:0','language=eng','-metadata:s:s:0','handler_name=English',
         '-metadata',f'title={TITLE}','-metadata','artist=Extinct Life','-metadata',f'comment={CREDITS}',
         *[arg for i,c in enumerate(chapters()) for arg in (f'-metadata:c:{i}',f"title={c['title']}")],
         '-movflags','+faststart','-video_track_timescale',str(SR),'-movie_timescale',str(SR),str(temp)])
    if temp.stat().st_size>=100_000_000:raise RuntimeError(f'Drive connector packaging budget exceeded: {temp.stat().st_size} bytes (local mux at {temp})')
    temp.replace(MOVIE);print('MUX_READY',MOVIE.stat().st_size,base.hashfile(MOVIE),flush=True)


def children(buf,start,end):
    p=start
    while p<end:
        n,k=struct.unpack_from('>I4s',buf,p);skip=8
        if n==1:n,=struct.unpack_from('>Q',buf,p+8);skip=16
        if n==0:n=end-p
        assert skip<=n and p+n<=end,(start,end,k,n)
        yield k,(p+skip,p+n)
        p+=n
    assert p==end


def table(buf,loc,fmt):
    a,b=loc;n,=struct.unpack_from('>I',buf,a+4)
    items=list(struct.iter_unpack('>'+fmt,buf[a+8:b]));assert len(items)==n,(loc,fmt,n,len(items));return items


def movie_clock(buf,loc):
    p,_=loc;v=buf[p];assert v in (0,1)
    return struct.unpack_from('>IQ' if v else '>II',buf,p+(20 if v else 12))


def streams(filename):
    """Inspect actual encoded presentation and decode ticks without rounding."""
    result={}
    with filename.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as buf:
        def index(loc):return dict(children(buf,*loc))
        top=index((0,len(buf)));moov=top[b'moov'];assert moov[1]<=top[b'mdat'][0]
        assert movie_clock(buf,index(moov)[b'mvhd'])==(SR,N)
        for key,tr in children(buf,*moov):
            if key!=b'trak':continue
            t=index(tr);m=index(t[b'mdia']);h,_=m[b'hdlr'];k=buf[h+8:h+12].decode('ascii')
            tb,d=movie_clock(buf,m[b'mdhd']);samples=index(index(m[b'minf'])[b'stbl']);stts=table(buf,samples[b'stts'],'II')
            n=sum(x for x,_ in stts);assert all(c>0 and (a>0 or (k=='sbtl' and j==len(stts)-1 and a==0)) for j,(c,a) in enumerate(stts))
            rows={'timescale':tb,'track_ticks':d,'packet_samples':n}
            e=index(t[b'edts'])[b'elst'];edits=table(buf,e,'QqI' if buf[e[0]] else 'IiI')
            assert all(r==65536 for _,_,r in edits),(k,edits)
            rows['edit_list']=[[a,b] for a,b,_ in edits]
            stsd,_=samples[b'stsd'];rows['codec_tag']=buf[stsd+12:stsd+16].decode('ascii')
            if k=='vide':
                assert len(edits)==1 and tb==SR and d==N and n==F[-1],(tb,d,n,edits)
                assert edits[0][0]==N and edits[0][1]>=0
                assert all(d==SPF for _,d in stts),stts
                start=edits[0][1];p=samples.get(b'ctts');assert p is not None
                offsets=[a for count,a in table(buf,p,'Ii' if buf[p[0]] else 'II') for _ in range(count)]
                assert len(offsets)==F[-1]
                pts=[i*SPF+o-start for i,o in enumerate(offsets)];assert sorted(pts)==list(range(0,N,SPF))
                keys=table(buf,samples[b'stss'],'I');seek={pts[i-1]//SPF for i, in keys}
                assert set(F[:-1])<=seek,(set(F[:-1])-seek)
                assert rows['codec_tag']=='avc1'
                rows.update(frames=len(pts),ticks_per_frame=SPF,exact_presentation_grid=True,seekable_shot_starts=len(F)-1,decoding_timestamps_increase=True)
            elif k=='soun':
                assert tb==SR and edits==[(N,1024,65536)] and d==N+1024,(k,tb,d,edits)
                assert rows['codec_tag']=='mp4a'
            elif k=='sbtl':assert rows['codec_tag']=='tx3g',(k,rows)
            elif k=='text':
                expected=[(1,(c['end_frame']-c['start_frame'])*SPF) for c in chapters()]
                assert (tb,d,stts,edits)==(SR,N,expected,[(N,0,65536)]),(tb,d,stts,edits)
            else:raise ValueError(k)
            assert k not in result;result[k]=rows
    assert set(result)=={'vide','soun','sbtl','text'},result
    return result


def split(s):return s.replace('\r','').strip().split('\n\n')


def captions(movie=MOVIE,sidecar=CAPTIONS):
    text,_=run(['-loglevel','error','-i',str(movie),'-map','0:s:0','-c:s','srt','-f','srt','-'])
    entries=split(SRT.read_text(encoding='utf-8'));actual=split(text.decode('utf-8'))
    assert actual==entries,(len(actual),len(entries),next(((x,y) for x,y in zip(actual,entries) if x!=y),None))
    assert base.hashfile(sidecar)==LOCK['files'][1]['sha256']
    sections=re.findall(r'^\*\*Narration\*\*\n\n(.*?)\n\n\*\*Picture:\*\*',SCRIPT.read_text(encoding='utf-8'),re.M|re.S)
    windows=[];copy=[];rate=0;last=0
    for num,e in enumerate(entries,1):
        i,t,* lines=e.splitlines();a,b=map(cc_time,t.split(' --> '))
        assert i==str(num) and last<=a<b and len(lines)<=2 and max(map(len,lines))<=42
        windows.append((a,b));copy.extend(lines);last=b;rate=max(rate,1000*sum(map(len,lines))/(b-a))
    canonical=' '.join(' '.join(sections).split());transcript=' '.join(' '.join(copy).split())
    assert canonical==transcript and len(transcript.split())==LOCK['source_words']==1217 and len(sections)==8
    assert len(windows)==LOCK['cue_count']==127 and last*48<SAMPLES and rate<=20.0
    return {'english_cues':len(windows),'last_caption_out_ms':last,'all_script_words':1217,'narrated_sections':8,'max_nonspace_break_chars_per_second':round(rate,3),
            'same_spelling_and_punctuation_as_v2':True,'identical_srt_round_trip':True,'subtitle_language':'eng','not_burned_in':True},windows


def i24(w,n):
    data=np.frombuffer(w.readframes(n),dtype=np.uint8).reshape(-1,w.getnchannels(),3).astype(np.int32)
    return data[:,:,0]+(data[:,:,1]<<8)+((data[:,:,2]-256*(data[:,:,2]>=128))<<16)


def audio(windows, *, movie=MOVIE, mix_path=MIX, bed_path=BED, report_path=REPORT, pcm=QA/'decoded-aac.f32'):
    meta=json.loads(report_path.read_text());assert meta['voice_sha256']==base.hashfile(VO) and meta['unchanged_samples']==SAMPLES and meta['program_samples']==N
    assert meta['mix_sha256']==base.hashfile(mix_path) and meta['bed_sha256']==base.hashfile(bed_path)
    run(['-loglevel','error','-y','-i',str(movie),'-map','0:a:0','-c:a','pcm_f32le','-f','f32le',str(pcm)])
    dec=np.memmap(pcm,dtype='<f4',mode='r').reshape(-1,2);assert 0<=len(dec)-N<1024,(len(dec),N)
    peaks=[];lags=[];unremarkable=[]
    with ExitStack() as stack:
        v,bed,m=[stack.enter_context(wave.open(str(p),'rb')) for p in (VO,bed_path,mix_path)]
        assert all((x.getsampwidth(),x.getframerate())==(3,SR) for x in (v,bed,m))
        assert [(w.getnchannels(),w.getnframes()) for w in (v,bed,m)]==[(1,SAMPLES),(2,N),(2,N)]
        refpower=errpower=sep=side=0.
        stride=SR*4
        for i in range(0,N,stride):
            j=min(i+stride,N);d=i24(bed,j-i);x=i24(m,j-i);y=np.zeros((j-i,1),np.int32)
            if i<SAMPLES:y[:min(j,SAMPLES)-i]=i24(v,min(j,SAMPLES)-i)
            assert np.array_equal(x-d,np.broadcast_to(y,x.shape)),i
            p=x.astype(np.float32)/Q;z=np.array(dec[i:j]);refpower+=np.sum(p*p,dtype=np.float64);delta=z-p
            errpower+=np.sum(delta*delta,dtype=np.float64);sep+=np.sum((z[:,0]-z[:,1])**2,dtype=np.float64)
            side+=np.sum(((d[:,0]-d[:,1])/Q)**2,dtype=np.float64)
        for l,r in windows:
            a=l*48+400;b=min(r*48-400,a+34_000);v.setpos(a);x=i24(v,b-a)[:,0].astype(np.float32)/Q
            wiggle=160;bed.setpos(a-wiggle);d=i24(bed,b-a+2*wiggle).mean(axis=1)/Q
            y=dec[a-wiggle:b+wiggle].mean(axis=1)-d
            if np.sqrt(np.mean(x*x))<.002:
                unremarkable.append(l);continue
            c=correlate(y,x,mode='valid',method='fft');k=int(c.argmax());z=y[k:k+len(x)]
            lag=k-wiggle;score=float(np.dot(z,x)/(np.linalg.norm(z)*np.linalg.norm(x)))
            assert lag==0 and score>.990,(l,lag,score)
            lags.append(lag);peaks.append(score)
    snr=10*math.log10(refpower/errpower);assert snr>30 and len(lags)>=120,(snr,len(lags),unremarkable)
    assert .87<sep/side<1.14 and float(np.max(np.abs(dec)))<.86,(sep/side,float(np.max(np.abs(dec))))
    _,log=run(['-i',str(movie),'-map','0:a:0','-af','ebur128=peak=true:framelog=verbose','-f','null','-']);s=log[log.rindex('Summary:'):]
    number=lambda pat:float(re.search(pat,s).group(1))
    loud=number(r'I:\s*(-?[\d.]+) LUFS');tp=number(r'Peak:\s*(-?[\d.]+) dBFS');lra=number(r'LRA:\s*([\d.]+) LU')
    assert -19.5<loud<-15.0 and tp<-1.3 and lra<9,(loud,tp,lra)
    q={'voice_exact_before_aac':True,'voice_original_samples':SAMPLES,'voice_source_first_sample':0,'voice_added_tail_samples':N-SAMPLES,'decoded_samples_with_aac_frame_padding':len(dec),
       'sync_windows':len(lags),'window_onsets_ms_skipped_for_silence':unremarkable,'all_offsets_samples':sorted(set(lags)),'min_window_correlation':round(min(peaks),8),
       'aac_pcm_snr_db':round(snr,3),'stereo_side_energy_ratio_vs_pcm':round(float(sep/side),5),'lufs_i':loud,'peak_dbtp':tp,'lra_lu':lra,
       'bed_minus_narration_rms_db':meta['bed_vs_voice_db'],'bed_gain':meta['static_bed_gain'],'aac_stereo':True,'mix_sha256':meta['mix_sha256'],'bed_sha256':meta['bed_sha256']}
    print('AUDIO_PASS',json.dumps(q),flush=True)
    return q,meta


def grab(f,size):
    w,h=size
    raw,_=run(['-loglevel','error','-xerror','-threads','2','-ss',f'{f/FPS:.12f}','-i',str(MOVIE),'-map','0:v:0','-frames:v','1',
       '-filter_threads','1','-vf',f'scale={w}:{h}:flags=lanczos:in_color_matrix=bt709:out_range=pc',
       '-threads','1','-pix_fmt','rgb24','-f','rawvideo','-'],18)
    assert len(raw)==w*h*3,(f,len(raw));return np.frombuffer(raw,dtype=np.uint8).reshape(h,w,3)


def spot_sync(meta):
    ledger={r['name']:r for r in meta['first_attacks']};assert set(ledger)==set(BY) and len(ledger)==len(B)==77
    assert all(ledger[q.key]['trigger_sample']==q.sample and ledger[q.key]['attack_sample']//SPF==q.f and ledger[q.key]['one_frame_rms_dbfs']>-46 for q in B)
    audits={}
    for i in range(len(S)):
        part=json.loads(path(i).with_suffix('.json').read_text());assert set(part)=={q.key for q in inside(i) if q.text},(i,part)
        audits.update(part)
    visual=[]
    for q in B:
        if not q.text:continue
        p=audits[q.key];w,h=raster(shot_of(q.f));assert p['frame']==q.f
        with np.load(QA/f'type-{q.f:05d}.npz') as masks:
            assert tuple(masks['size'])==(w,h);a=masks['with_type'].astype(np.int16);b=masks['without_type'].astype(np.int16);sel=masks['delta']
            assert len(a)==int(sel.sum())==p['native_onset_changed_pixels']>=20
            c=grab(q.f,(w,h))[sel].astype(np.int16)
        ink=float(np.mean(np.abs(c-a)));omit=float(np.mean(np.abs(c-b)));strength=omit/max(.0001,ink)
        delay=(ledger[q.key]['attack_sample']-q.sample)*1000/SR
        entry={**p,'key':q.key,'type':q.text,'first_matched_audio_ms':round(delay,4),'overlay_error_ratio':round(strength,3)}
        print('TYPE',json.dumps(entry,ensure_ascii=False),flush=True)
        assert strength>1.20,(q.key,q.f,ink,omit,strength)
        visual.append(entry)
    assert len(visual)==len(audits)==meta['graphic_sync']==33
    return {'graphic_events':len(visual),'spot_events':len(B),'analysed_graphic_entries':visual,'audio_attack_audit':meta['first_attacks'],
            'same_frame_all_graphic_and_spot_attacks':True,'max_spot_attack_ms':round(max((v['attack_sample']-v['trigger_sample'])*1000/SR for v in ledger.values()),4),
            'max_graphic_attack_ms':max(v['first_matched_audio_ms'] for v in visual),'min_decoded_overlay_error_ratio':min(v['overlay_error_ratio'] for v in visual)}


def inspect_shots():
    w,h=480,270;mids=[round(F[k]+.54*(F[k+1]-F[k])) for k in range(len(S))]
    filt='+'.join(f'eq(n,{f})' for f in mids)
    raw,_=run(['-loglevel','error','-xerror','-threads','2','-i',str(MOVIE),'-map','0:v:0','-an','-sn','-filter_threads','1','-vf',
         f"select='{filt}',scale={w}:{h}:flags=lanczos:in_color_matrix=bt709:out_range=pc",'-fps_mode','passthrough',
         '-threads','1','-pix_fmt','rgb24','-f','rawvideo','-'],220)
    a=np.frombuffer(raw,np.uint8).reshape(-1,h,w,3);assert len(a)==len(S)
    assert len({hashlib.sha256(x).digest() for x in a})==len(a)
    font=ImageFont.truetype(str(FONTS/'PlexMono.ttf'),16);luma=[]
    for k in range(0,len(S),12):
        team=a[k:k+12];out=Image.new('RGB',(3*w,(h+25)*math.ceil(len(team)/3)),(12,23,25));d=ImageDraw.Draw(out)
        for j,img in enumerate(team):
            i=k+j;xy=(w*(j%3),(h+25)*(j//3));out.paste(Image.fromarray(img),xy)
            brightness=np.mean(img,axis=-1);std=float(np.std(brightness));avg=float(np.mean(brightness))
            assert std>5.0 and avg>13.,(i,std,avg)
            luma.append({'shot':S[i].key,'check_frame':mids[i],'average_rgb_intensity':round(avg,2),'rms_contrast':round(std,2)})
            d.text((xy[0]+12,xy[1]+h+3),f'{i+1:02d}  {mids[i]/FPS:6.2f}s   {S[i].key.upper()}',font=font,fill=(238,227,200))
        out.save(QA/f'decode-{k:02}.jpg',quality=94)
    return luma


def file_record(p):
    with p.open('rb') as q:md5=hashlib.file_digest(q,'md5').hexdigest()
    return {'name':p.name,'bytes':p.stat().st_size,'sha256':base.hashfile(p),'md5':md5}


def tc(f):
    t=f/FPS;return f'{int(t//60):02d}:{t%60:06.3f}'


def handoff(q):
    a=q['audio'];p=q['sync'];r=q['files'][0]
    lines=[f'# {TITLE}', '',
       '**Full cinematic cut · 07:25.667 including source credits**', '',
       'All eight sections of the locked English voiceover play in full. The timed 127-cue English track is selectable in the MP4; the separate SRT is identical to the locked file. Only selected titles, labels, and numbers are painted into the picture.', '',
       '## Chapters', '', '| In | Chapter |','|---|---|']
    lines.extend(f"| {tc(c['start_frame'])} | {c['title']} |" for c in q['chapters'])
    lines+=['','## Headphone review','',
       '- **00:06–00:20:** mineral/tonal distance reveal, spatial rewind, and a three-part title over water. The maps compare two sourced snapshots, not an animated historical interpolation.',
       '- **01:05–01:35:** layers separate, the eroded slab sheds grains, and three views of an original virtual sample resolve into a relief mesh.',
       '- **02:04–02:13:** matched stamps meet two substrates. Listen for the low press, the release, and the small delayed wall collapse.',
       '- **02:49–03:28:** water recedes, a muddy footprint loses contour, and thin-section/burial views look beneath the track.',
       '- **05:14 and 06:49:** quiet fracture and granular settlement, then the sea returns. **07:04** brings the conclusion back to the rocks; the last words stay over a single impression.',
       '', '## Checks', '',
       f"- 1920×1080, 24 fps, Rec.709; all {F[-1]:,} frames decoded and all {len(S)} shot joins checked on the exact frame grid. A separate visual sample was taken from every shot.",
       f"- Stereo 48 kHz AAC-LC, {a['lufs_i']:.1f} LUFS-I, {a['peak_dbtp']:.1f} dBTP. The complete dry voice is sample-exact before AAC; zero-sample lag in {a['sync_windows']} decoded checks. {p['graphic_events']} kinetic entries, {p['spot_events']} total spot cues. The selected entry frames were checked in the actual MP4 against the clean plate.",
       '- A human listen to the narrator’s pronunciation of **Sousa** remains recommended before public release. No publication or sharing change was made.',
       f"- MP4: {r['bytes']:,} bytes; SHA-256 `{r['sha256']}`.",
       '', '## Science and rights', '',
       '- [Jacobs et al. (2024)](https://igeo.ufrj.br/inc/isc/3/03_139_Jacobs%20etal.pdf): study estimates of ~6,000 km today and ~1,000 km in the reconstruction. Independent pins measure ~6,085 and ~1,194 km, respectively. The estimates are regional separation, not route length. A connected landscape and possible dispersal do not establish a tracked individual or a single river.',
       '- [Menkem et al. (2026)](https://doi.org/10.1016/j.jop.2026.100416): 283 footprints, 34 trackways, and four surfaces in the later Koum survey; not added to the earlier inventory. ~69 cm refers to one impression, not body size; the render is not a surveyed replica. Pollen clues are regional; matched fossil ages are not established.',
       '- [Carvalho, Borghi & Leonardi (2013)](https://doi.org/10.1016/j.cretres.2013.04.004): Sousa sediments, possible microbial mats, and the displaced rims. Mawsonia refers to finds in other basins, not either track site. Fish, slabs, riverbeds, sediments and fault sections are illustrations, not photographs, scanned fossils or re-used journal figures.',
       '- Ancient geography: [Kocsis & Scotese PaleoCoastlines v7.1 and rotations](https://doi.org/10.1016/j.earscirev.2020.103463) and [Scotese & Wright PaleoDEMs v2](https://doi.org/10.5281/zenodo.5460860), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); resampled, recoloured, shaded and annotated, with exaggerated relief. 125 Ma is the model slice, **not** a footprint date.',
       '- Modern geography: [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/) and NOAA NGDC ETOPO5, public domain. Typography: Fraunces and IBM Plex, SIL OFL 1.1. '+FOL_CREDIT, '']
    NOTES.write_text('\n'.join(lines),encoding='utf-8')


def verify():
    media_lock();check=streams(MOVIE)
    _,log=run(['-i',str(MOVIE),'-map','0','-c','copy','-t','0.100','-f','null','-'])
    assert all(s in log for s in ('h264 (High)','yuv420p(tv, bt709, progressive), 1920x1080','24 fps','Audio: aac (LC)','48000 Hz, stereo','(eng): Subtitle: mov_text'))
    assert all(c['title'] in log for c in chapters()),log[:4000]
    cc,windows=captions();a,meta=audio(windows);sync=spot_sync(meta);luma=inspect_shots()
    r={'title':TITLE,'status':'Full cinematic cut · private handoff; not published','movie_duration_seconds':N/SR,'narration_duration_seconds':SAMPLES/SR,'width':1920,'height':1080,'fps':FPS,
       'color':'limited Rec.709','shots':len(S),'shot_starts_frames':list(F[:-1]),'end_frame_exclusive':F[-1],'frames_all_decoded':True,'streams':check,'chapters':chapters(),
       'source_hashes':{p['file']:p['sha256'] for p in LOCK['files']},'script_sha256':LOCK['script_sha256'],'caption_audit':cc,'audio':a,'sync':sync,
       'shot_inspection':luma,'source_assets':json.loads((FIELDS/'manifest.json').read_text()),'credits':CREDITS,'files':[file_record(MOVIE),file_record(CAPTIONS)]}
    handoff(r);r['files'].append(file_record(NOTES));RECEIPT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('FULL_FILM_VERIFIED',json.dumps({'file':r['files'][0],'picture':check['vide'],'duration':r['movie_duration_seconds'],'audio':a,
          'subtitles':cc,'type_and_foley':{k:v for k,v in sync.items() if k not in ('analysed_graphic_entries','audio_attack_audit')}},indent=2),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);a=p.add_mutually_exclusive_group();a.add_argument('--verify-only',action='store_true');a.add_argument('--mux-only',action='store_true')
    q=p.parse_args()
    if not q.verify_only:mux()
    if not q.mux_only:verify()


if __name__=='__main__':main()
