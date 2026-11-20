"""Fail delivery on audio holes, mistimed motion, or encoded media drift."""
from fractions import Fraction
from hashlib import sha256
from io import BytesIO
import csv
import json
from math import hypot
import re
import shutil
import struct

import numpy as np
from PIL import Image,ImageDraw
from layout import BASE,CACHE,HERE,WORK,QA,OUT,NAME,FRAMES,FPS,SPF,SR,SAMPLES,NATIVE,EXPORT,edit
from sound import decode,ff,gain,measure,rms_blocks,runs
from finish import Comp,RAW


def trace():
    records={};takes=edit()
    for s in takes:
        aa,bb=s['lo'],s['hi'];old=s['source'];a,b=(old[0],old[1]) if old else (aa,aa)
        src=(BASE if old else CACHE)/'trace'/f'{a}.csv'
        with src.open() as f: r=[q for q in csv.DictReader(f) if b<=int(q['frame'])<b+bb-aa]
        assert [int(q['frame']) for q in r]==list(range(b,b+bb-aa)),s
        assert all(q['shot']==s['shot'] and int(q['lens'])==s['cam'] for q in r),s
        c=[float(q['motion_s']) for q in r];assert all(v>u for u,v in zip(c,c[1:])),s
        if not old:
            assert abs(c[0]-s['model'][0])<.000012 and abs(c[-1]-s['model'][1])<.000012,s
            assert all(abs(c[k-aa]-t)<.000012 for k,t in s['pins']),s
        for k,q in enumerate(r,aa):records[k]=dict(q,output_frame=k)
    assert len(records)==FRAMES
    for f in (5,439):
        a,b=records[f],records[f+1]
        assert a['shot']==b['shot'] and int(a['support'])==5 and a['airborne']=='0' and 0<float(a['jaw_gap'])<.002,a
        assert b['support']=='0' and b['airborne']=='1' and float(b['y'])-float(a['y'])>.020,b
        assert abs(float(a['jaw_ndcx']))<.9 and abs(float(a['jaw_ndcy']))<.68,a
    assert all(records[f]['x']=='0' and records[f]['y']=='0' and records[f]['airborne']=='0' for f in range(271,392))
    assert abs(float(records[328]['jaw_ndcx']))<.94
    def radius(q):return hypot(float(q['x']),1.035*float(q['z']))
    rim=next(f for f in range(606,644) if radius(records[f])>4.33 and float(records[f]['x'])<0)
    assert records[rim]['airborne']=='1' and records[644]['airborne']=='0' and records[644]['support']=='6'
    a=records[696];assert records[695]['airborne']=='1' and a['airborne']=='0' and abs(float(a['jaw_gap'])-.009)<.001
    assert radius(records[758])<3.2 and float(records[758]['y'])<float(a['y'])-.30
    # Difference at the raw loop splice is small but nonzero. Typography resets
    # intentionally, because the final question and opening hook are distinct.
    raw=[]
    for f in (0,FRAMES-1):
        s=next(x for x in takes if x['lo']<=f<x['hi'])
        with (CACHE/'plates'/f"{s['lo']}.rgba").open('rb') as h:
            h.seek(RAW*(f-s['lo']));p=h.read(RAW)
        raw.append(np.asarray(Image.frombuffer('RGBA',NATIVE,p,'raw','RGBA',0,-1).resize((270,480)).convert('RGB'),dtype='f'))
    seam=float(np.mean(abs(raw[0]-raw[1])));assert 0.005<seam<4.5,seam
    return dict(picture_takes=len(takes),reused_spans=sum(s['source'] is not None for s in takes),native_size=NATIVE,
                opener_strike=5,open_air=328,ground_contact=439,rim_cross=rim,touchdown=644,wall=696,raw_loop_mae=seam)


def encode_gate(p):
    raw=ff('-threads',2,'-i',p,'-map','0:v:0','-an','-vf','showinfo','-fps_mode','passthrough','-f','null','-').stderr.decode()
    head=raw.split('Stream mapping:')[0];streams=[s.strip() for s in head.splitlines() if re.match(r'^\s*Stream #0:',s)]
    assert 'Duration: 00:00:34.00, start: 0.000000' in head
    assert len(streams)==2 and all(z in streams[0] for z in ('h264 (High)','1080x1920','yuv420p(tv, bt709','30 fps','SAR 1:1')),streams
    assert all(u in streams[1] for u in ('Audio: aac (LC)', '48000 Hz, stereo')),streams
    dt=1/(Fraction(re.search(r'config in time_base: (\d+/\d+)',raw).group(1))*FPS)
    stamps=re.findall(r'\bn:\s*(\d+)\s+pts:\s*(\d+)\s+pts_time:[^\n]*?\bchecksum:([\dA-F]{8})',raw)
    assert len(stamps)==FRAMES and dt.denominator==1 and all(int(f)==i and int(t)==i*dt for i,(f,t,h) in enumerate(stamps))
    assert raw.count('color_range:tv color_space:bt709 color_primaries:bt709 color_trc:bt709')==FRAMES
    assert not any(x[2]==y[2] for x,y in zip(stamps,stamps[1:])), 'repeated adjacent frames'
    with p.open('rb') as f:
        top=[];u=p.stat().st_size
        while f.tell()<u:
            start=f.tell();n,k=struct.unpack('>I4s',f.read(8));size=8
            if n==1:n=struct.unpack('>Q',f.read(8))[0];size=16
            if n==0:n=u-start
            assert size<=n<=u-start;top.append(k);f.seek(start+n)
        assert top.index(b'moov')<top.index(b'mdat')
    return dict(frames=FRAMES,fps=FPS,resolution=EXPORT,duration_seconds=FRAMES/FPS,rec709=True,stream_headers=streams)


def audio(p):
    x=decode(p,2);m=decode(WORK/'short-v2-mix.wav',2)
    assert len(m)==SAMPLES and SAMPLES<=len(x)<SAMPLES+1024
    dec=x[:SAMPLES];voice=json.loads((QA/'mix.json').read_text());cor=[]
    for s in voice['takes']:
        a,b=s['mix_samples'];n=float(np.corrcoef(m[a:b].ravel(),dec[a:b].ravel())[0,1]);assert n>.988,n;cor.append(n)
    meter=measure(p);assert -16.0<meter['LUFS_I']<-14 and meter['dBTP']<=-1.4,meter
    mono=dec.mean(axis=1);g=runs(rms_blocks(mono,SR//100)>gain(-51),False)
    assert all(h-l<9 for l,h in g),g
    assert voice['first_vo_s']<=.075 and voice['last_vo_s']>=33.5 and voice['max_voice_gap_s']<=.56
    return dict(encoded=meter,min_synced_narration_corr=min(cor),vo_start_s=voice['first_vo_s'],vo_last_s=voice['last_vo_s'],
                max_voice_gap_s=voice['max_voice_gap_s'],max_mixed_gap_s=max((h-l for l,h in g),default=0)/100,
                floor_test_dbrms=-51,samples=SAMPLES,aac_samples_before_tail_trim=len(x))


def frames(p):
    sets=[(6,62,193,331,448),(540,630,697,805,878),(960,984,1014)]
    for n,fs in enumerate(sets,1):
        b=Image.new('RGB',(1032,402),'#102123');d=ImageDraw.Draw(b)
        d.text((12,10),'MONARCH CAM 01A / SHORT V2 ENCODED · PHONE UI MOCK ONLY',fill='#fff5d9')
        for j,f in enumerate(fs):
            pix=ff('-loglevel','error','-ss',f'{f/FPS:.7f}','-i',p,'-map','0:v:0','-an','-frames:v',1,
                   '-vf','scale=189:336:flags=lanczos','-c:v','png','-f','image2pipe','-').stdout
            im=Image.open(BytesIO(pix)).convert('RGBA');u=Image.new('RGBA',im.size);z=ImageDraw.Draw(u)
            z.rectangle((0,268,189,336),fill=(6,12,12,155));z.text((7,277),'@MonarchCam',fill='#f4ebd1')
            z.text((7,295),'Related video',fill='#f4ebd1');z.text((7,316),'This Ant’s Jump…',fill='#f4ebd1')
            for y in (154,176,198,220,242):z.ellipse((169,y,181,y+12),outline='#fff8e9')
            x=12+j*203;b.paste(Image.alpha_composite(im,u).convert('RGB'),(x,32));d.text((x,376),f'{f/FPS:05.2f}s · {f:04d}',fill='#c9ddd4')
        b.save(QA/f'encoded-v2-phone-{n}.jpg',quality=93)


def verify():
    p=WORK/'short-v2.mp4';m=dict(motion=trace(),picture=encode_gate(p),audio=audio(p));frames(p)
    assert p.stat().st_size<100_000_000;m.update(bytes=p.stat().st_size,sha256=sha256(p.read_bytes()).hexdigest(),name=NAME+'.mp4')
    (QA/'delivery.json').write_text(json.dumps(m,indent=2)+'\n');OUT.mkdir(parents=True,exist_ok=True)
    for src,dst in [(p,f'{NAME}.mp4'),(WORK/'short-v2.en.srt',f'{NAME}.en.srt'),(HERE/'upload.txt',f'{NAME}-Upload.txt')]:
        tmp=OUT/(dst+'.pending');shutil.copyfile(src,tmp);tmp.replace(OUT/dst)
    print('SHORT_V2_VERIFIED',m['name'],m['bytes'],m['sha256'],m['audio'],flush=True)


if __name__=='__main__':verify()
