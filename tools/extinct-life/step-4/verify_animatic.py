#!/usr/bin/env python3
"""Verify muxed frame/sample clocks, subtitle round trip and outline the QA receipt."""
from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path
import re
import struct
import subprocess

import numpy as np
from scipy.signal import correlate

from render_animatic import CLOCK, FF, FPS, HERE, OUT, RECEIPT, SHOTS, SRT, STEM, WAV, frames, sha


def index_atoms(data, start, end):
    offset = start
    while offset < end:
        size, name = struct.unpack_from('>I4s', data, offset)
        hdr = 8
        if size == 1:
            size, = struct.unpack_from('>Q', data, offset + hdr)
            hdr += 8
        if size == 0:
            size = end - offset
        assert hdr <= size <= end - offset, (name, offset, size, end)
        yield name, offset, offset + hdr, offset + size
        offset += size
    assert offset == end


def box_children(data, info):
    return list(index_atoms(data, info[2], info[3]))


def box_child(data, info, target):
    return next(x for x in box_children(data, info) if x[0] == target)


def ints_table(data, box, width):
    b,e = box[2:]
    count, = struct.unpack_from('>I', data, b+4)
    found = list(struct.iter_unpack('>'+'I'*width, data[b+8:e]))
    assert len(found) == count
    return found


def time_fields(data, box):
    p = box[2]
    return struct.unpack_from('>IQ' if data[p] else '>II',data,p+(20 if data[p] else 12))


def video_clock(file):
    raw=file.read_bytes()
    outer=list(index_atoms(raw,0,len(raw)))
    moov=next(x for x in outer if x[0]==b'moov')
    assert moov[1] < next(x[1] for x in outer if x[0]==b'mdat')
    fmt,duration = time_fields(raw,box_child(raw,moov,b'mvhd'))
    n = frames()[-1]*(CLOCK//FPS)
    assert (fmt,duration)==(CLOCK,n), (fmt,duration)
    tracks = {}
    for track in box_children(raw,moov):
        if track[0]!=b'trak':
            continue
        mdia=box_child(raw,track,b'mdia')
        handler=box_child(raw,mdia,b'hdlr')[2]
        handler=raw[handler+8:handler+12].decode('ascii')
        sample=box_child(raw,box_child(raw,mdia,b'minf'),b'stbl')
        md_clock,md_duration=time_fields(raw,box_child(raw,mdia,b'mdhd'))
        tracks[handler]=dict(clock=md_clock,duration=md_duration)
        if handler=='vide':
            stts=ints_table(raw,box_child(raw,sample,b'stts'),2)
            sample_durations={ticks for _,ticks in stts}
            assert sample_durations=={CLOCK//FPS}, sample_durations
            assert md_clock==CLOCK and md_duration==n and sum(c for c,t in stts)==frames()[-1]
            stss=ints_table(raw,box_child(raw,sample,b'stss'),1)
            assert {lo+1 for lo in frames()[:-1]} <= {key for key, in stss}
            tracks[handler].update(frames=frames()[-1],duration_ticks_per_frame=CLOCK//FPS,seekable_shot_starts=len(frames())-1)
        if handler=='soun':
            assert md_clock==CLOCK and abs(n-md_duration)<=1024, (n,md_duration)
    assert sorted(tracks)==['sbtl','soun','vide'], tracks.keys()
    return tracks


def run(args, timeout=180):
    p=subprocess.run([FF,'-hide_banner','-nostdin',*args],capture_output=True,check=True,timeout=timeout)
    return p.stdout,p.stderr


def pcm(file,stream):
    out,_=run(['-v','error','-i',str(file),'-map',stream,'-ac','1','-ar',str(CLOCK),'-c:a','pcm_f32le','-f','f32le','-'])
    return np.frombuffer(out,dtype='<f4')


def vo_sync(movie,v):
    source,review = pcm(WAV,'0:a:0'),pcm(movie,'0:a:0')
    n = frames()[-1]*(CLOCK//FPS)
    assert len(source)==v['sample_frames'] and 0<=len(review)-n<1024, (len(source),len(review),n)
    offsets=[]; scores=[]
    spots=[.08,6.0,10.15,100.0,214.1,275.5,362.4,423.0,437.2]+[s['speech_start'] for s in v['scenes']]
    for sec in spots:
        idx=round(sec*CLOCK)
        a,b=idx,idx+36_000
        reference=source[a:b]
        window=review[a-640:b+640]
        metric=correlate(window,reference,mode='valid',method='fft')
        peak=int(metric.argmax()); lag=peak-640
        raw_dot=np.dot(reference,window[peak:peak+len(reference)])
        score=float(raw_dot/(np.linalg.norm(reference)*np.linalg.norm(window[peak:peak+len(reference)])))
        assert abs(lag)<=1 and score>.987,(sec,lag,score)
        scores.append(score); offsets.append(lag)
    rms_loss=abs(20*math.log10(float(np.linalg.norm(review[:len(source)]))/float(np.linalg.norm(source))))
    assert rms_loss < .35
    assert np.max(np.abs(review[len(source)+2048:])) < .00012, 'Credits should be silent'
    assert np.max(np.abs(review))<1.
    return {'sites_tested':len(spots),'lag_samples':sorted(set(offsets)),'lowest_correlation':round(min(scores),7),
            'rms_level_difference_db':round(rms_loss,5),'full_source_sample_count':len(source),'audio_codec':'AAC-LC encoded once'}


def subs(movie):
    out,_=run(['-loglevel','error','-i',str(movie),'-map','0:s:0','-c:s','srt','-f','srt','-'])
    conv=lambda s:s.replace('\r','').strip().split('\n\n')
    before=conv(SRT.read_text()); after=conv(out.decode('utf-8'))
    assert before==after, next((x for x in zip(before,after) if x[0]!=x[1]),(len(before),len(after)))
    assert len(after)==127
    return {'embedded_english_cues':len(after),'timing_and_text_match_v2_srt':True}


def main():
    movie=OUT/f'{STEM}.mp4'; handoff=OUT/f'{STEM}-Shot-Handoff.md'
    v=json.loads(RECEIPT.read_text())
    streams=video_clock(movie)
    audio=vo_sync(movie,v)
    cc=subs(movie)
    _,metadata=run(['-i',str(movie),'-c','copy','-t','0.10','-f','null','-'])
    log=metadata.decode('utf-8')
    assert 'h264 (High)' in log and 'yuv420p(tv, bt709, progressive), 1920x1080' in log and '24 fps' in log
    assert 'Audio: aac (LC)' in log and '48000 Hz, mono' in log
    assert '(eng): Subtitle: mov_text' in log
    run(['-loglevel','error','-xerror','-threads','2','-i',str(movie),'-map','0:v:0','-an','-f','null','-'],timeout=180)
    review_hash=sha(movie)
    assert review_hash in handoff.read_text()
    assert 0<movie.stat().st_size<100_000_000
    payload={
        'title':'Why These Dinosaur Footprints Are an Ocean Apart',
        'kind':'prep animatic; not final CGI/picture lock',
        'vo_source':'English v2, no time stretch, trims or score',
        'duration_seconds':frames()[-1]/FPS,'script_sha256':v['script_sha256'], 'vo_sha256':sha(WAV),'srt_sha256':sha(SRT),
        'voice_duration_seconds':v['duration_seconds'],'section_count':len(v['scenes']),'shot_count':len(SHOTS),
        'rewind_frame':frames()[1],'rewind_seconds':frames()[1]/FPS,'credits_in_seconds':frames()[-2]/FPS,
        'video':{'size':[1920,1080],'fps':FPS,'color':'Rec.709 limited range','stream_validation':streams},
        'audio':audio,'captions':cc,'all_frames_decode':True,
        'files':[{'name':f.name,'size':f.stat().st_size,'sha256':sha(f)} for f in (movie,handoff)],
    }
    (HERE/'animatic-v1-receipt.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(payload,indent=2))


if __name__=='__main__':
    main()
