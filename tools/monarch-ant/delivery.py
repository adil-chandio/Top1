"""Mux a review copy and check the encoded media, locked voice and scene events."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

import numpy as np
from sound import CACHE, FF, loudness, read_locked

D=Path('deliverables/monarch-cam-step-4')
PROOF=D/'Monarch-Cam-Ant-Contact-Proof-v1.mp4'
CUT=D/'Monarch-Cam-Ant-Rough-Cut-v1.mp4'
SRT=D/'Monarch-Cam-Ant-English.srt'


def run(*args):
    return subprocess.run([FF,'-hide_banner','-nostdin','-xerror',*map(str,args)],
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)


def ffmeta(meta):
    def esc(s):return re.sub(r'([=;#\\])',r'\\\1',s)
    f=meta['fps']; entries=meta['chapters']+[[meta['precredit_frames'],'Sources']]
    tails=entries[1:]+[[meta['frames'],'']]
    text=[';FFMETADATA1','title=This Ant Bites the Ground to Escape','artist=Monarch Cam']
    for ((a,name),(b,_)) in zip(entries,tails):
        text+=['[CHAPTER]',f'TIMEBASE=1/{f}',f'START={a}',f'END={b}',f'title={esc(name)}']
    return '\n'.join(text)+'\n'


def proof_gate(trace):
    rows=list(csv.DictReader(trace.open()))
    assert len(rows)==193 and [int(p['frame']) for p in rows]==list(range(193)), 'proof must have 193 native frames'
    f=next(i for i,p in enumerate(rows) if 3.35<float(p['motion_s'])<3.423 and
           float(p['jaw_tip_gap'])<.0018 and p['airborne']=='0')
    p,n=rows[f:f+2]; assert p['camera']==n['camera']=='0' and p['support']=='5' and n['support']=='0'
    assert float(p['toe_1_gap'])>.10 and float(n['body_y'])-float(p['body_y'])>.12
    assert n['airborne']=='1' and float(n['jaw_tip_gap'])>.1 and float(n['body_x'])<float(p['body_x'])
    lip=next(k for k,q in enumerate(rows) if float(q['body_x'])<-4.33 and q['airborne']=='1')
    clear=next(k for k,q in enumerate(rows) if float(q['body_x'])<-5.07 and q['support']=='6')
    assert f==82 and lip==127 and 112<lip<clear<=135
    return {'contact_frame':f,'recoil_first_frame':f+1,'center_clears_rim_frame':lip,
            'outside_six_support_frame':clear,'camera_cut_frame':112,
            'contact_tolerance_as_rendered_scene_units':float(p['jaw_tip_gap'])}


def failure_gate(trace):
    rows=[r for r in csv.DictReader(trace.open()) if r['scene']=='4' and r['camera']=='15']
    assert rows, 'failure sequence missing'
    results=[]
    for r in rows:
        if results and int(r['frame'])<=int(results[-1][-1]['frame'])+1:
            results[-1].append(r)
        else:results.append([r])
    r0=next(r for r in results if float(r[0]['motion_s'])<3.1)
    contact=min(r0,key=lambda r:abs(float(r['motion_s'])-3.42)); collision=min(r0,key=lambda r:abs(float(r['motion_s'])-4.4728))
    apex=max(r0,key=lambda r:float(r['body_y']));final=r0[-1]
    r=lambda p:math.hypot(float(p['body_x']),float(p['body_z']))
    assert float(apex['body_y'])>float(collision['body_y'])+.60
    assert r(collision)-r(final)>.8 and r(final)<3.0 and r(apex)<4.33 and final['airborne']=='0'
    return {k:int(r['frame']) for k,r in [('strike_frame',contact),('apex_frame',apex),('wall_frame',collision),('returned_in_pit_frame',final)]}


def decode(path,frames,size,target):
    p=run('-i',path,'-map','0:v:0','-map','0:a:0','-af','loudnorm=I=-19:TP=-2:LRA=11:print_format=json',
          '-nostats','-progress','pipe:1','-f','null','-')
    e=p.stderr.decode(errors='replace'); report=p.stdout.decode()
    assert re.search(r'frame='+str(frames)+r'\n(?:[^\n]*\n)*progress=end',report)
    assert size in e and re.search(r'\b24 fps\b',e) and re.search(r'yuv420p\(tv, bt709(?:,|/)',e)
    assert '48000 Hz, stereo' in e
    d,_=json.JSONDecoder().raw_decode(e[e.rfind('{'):]); mix={'LUFS_I':float(d['input_i']),'dBTP':float(d['input_tp']),'LRA':float(d['input_lra'])}
    assert abs(mix['LUFS_I']-target)<.6 and mix['dBTP']<=-2.
    return {'video_frames':frames,'fps':24,'raster':size,'duration_s':frames/24,'encoded_loudness':mix,
            'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def dialogue(path,meta):
    pcm=run('-loglevel','error','-i',path,'-map','0:a:0','-vn','-ar','48000','-ac','1','-f','f32le','-').stdout
    actual=np.frombuffer(pcm,dtype='<f4'); source=read_locked(); corr=[]; whole=[]
    assert len(actual)==meta['frames']*2000, 'decoded audio/sample count differs from picture'
    def pearson(u,v):
        u=u-u.mean();v=v-v.mean()
        return float(np.dot(u,v)/np.sqrt(np.dot(u,u)*np.dot(v,v)))
    for a,b,dst in meta['vo_ranges']:
        ref=source[a:b]; y=actual[dst:dst+b-a]
        for k in range(0,len(ref)-38400,38400):
            u=ref[k:k+38400];v=y[k:k+38400]
            # Test samples while the voice is present. A deliberate Foley-only
            # tail in the same 800 ms window must not count as mismatched VO.
            active=np.mean(u.reshape(40,960)**2,axis=1)>=1.e-4
            if active.sum()<5:continue
            pick=np.repeat(active,960)
            corr.append(pearson(u[pick],v[pick]));whole.append(pearson(u,v))
    assert len(corr)>160 and min(corr)>.975, 'dialogue is not sample-aligned in review encode'
    return {'active_0.8s_windows':len(corr),'min_zero_offset_correlation':min(corr),
            'median_zero_offset_correlation':float(np.median(corr)),
            'voice_active_mask':'20 ms source RMS >= -40 dBFS, at least 100 ms active per window',
            'min_correlation_including_foley_only_pauses':min(whole)}


def build():
    C=CACHE/'work';Q=CACHE/'qa';meta=json.loads((C/'film.json').read_text());meta_p=C/'film.ffmeta';meta_p.write_text(ffmeta(meta))
    tmp=C/'rough-cut.v1-before-qa.mp4'
    run('-loglevel','error','-i',C/'film-picture.mp4','-i',C/'film-mix-v1.wav','-i',SRT,'-f','ffmetadata','-i',meta_p,
        '-map','0:v:0','-map','1:a:0','-map','2:0','-map_metadata','3','-map_chapters','3','-disposition:s:0','0',
        '-metadata:s:s:0','language=eng','-metadata:s:s:0','handler_name=English (Script V1)',
        '-c:v','copy','-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0',
        '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv',
        '-c:a','aac','-b:a','192k','-c:s','mov_text','-movie_timescale','48000','-movflags','+faststart+write_colr','-y',tmp)
    r=decode(tmp,meta['frames'],'768x432',-19)
    if r['bytes']>=100000000: raise ValueError('Review copy exceeded the Drive attachment budget')
    r['dialogue_check']=dialogue(tmp,meta);r['failure_motion']=failure_gate(Q/'film-motion.csv')
    r['cuts']=len(meta['shots']);r['vo_source_sha256']='4a3d3c596005cee1f077cc24c0b3a8e55ae9c29614b1f4ed77d119fd5fbf5929'
    r['chapter_frames']=meta['chapters'];r['native_contact_wide_clearance_and_failure']=True
    r['cut_type']='Seven-beat review assembly. B-roll proxy sampling; not a release master.'
    tmp.replace(CUT);result=Q/'film-delivery.json';result.write_text(json.dumps(r,indent=2)+'\n')
    print(result.read_text(),end='')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['proof','film']);a=p.parse_args()
    if a.kind=='proof':
        q=CACHE/'proof'/'qa';r=decode(PROOF,193,'1280x720',-21.5);r['geometry']=proof_gate(q/'contact-motion.csv')
        (q/'contact-delivery.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
    else:build()
