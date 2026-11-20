"""Decode the delivered stream and validate portrait clock, scene, sound and UI.

All sizes/timestamps evaluated on the actual MP4. The phone board contains a
mock UI purely to test contrast and margins; the export is clean of mock UI.
"""
from fractions import Fraction
from hashlib import sha256
import csv
from io import BytesIO
import json
import math
from pathlib import Path
import re
import shutil
import struct

import numpy as np
from PIL import Image, ImageDraw

from common import CACHE, EXPORT, FPS, FRAMES, HERE, NAME, NATIVE, OUT, QA, SR, SPF, SAMPLES, WORK, read_plan
from picture import still
from sound import VOICE, decode, ff, measure, rms


def trace_gate():
    all_=[];plan=read_plan()
    for s in plan:
        path=CACHE/'trace'/f"{s['lo']}.csv"
        with path.open() as fp:rows=list(csv.DictReader(fp))
        assert [int(x['frame']) for x in rows]==list(range(s['lo'],s['hi']))
        assert all(r['shot']==s['shot'] and int(r['lens'])==s['cam'] for r in rows)
        clock=[float(x['motion_s']) for x in rows]
        assert all(b>a for a,b in zip(clock,clock[1:])),s
        assert abs(clock[0]-s['source'][0])<2.e-5 and abs(clock[-1]-s['source'][1])<2.e-5,s
        for n,t in s['pins']:
            assert abs(clock[n-s['lo']]-t)<2.e-5,(n,t)
        all_.extend(rows)
    assert len(all_)==FRAMES
    def radius(a):return math.hypot(float(a['x']),1.035*float(a['z']))
    _contacts=[]
    for n in (8,475,627):
        a,b=all_[n:n+2];assert a['shot']==b['shot']
        assert abs(float(a['jaw_gap']))<.002 and a['airborne']=='0' and int(a['support'])>=5, a
        assert b['airborne']=='1' and b['support']=='0' and float(b['y'])>float(a['y'])+.020,b
        assert abs(float(a['jaw_ndcx']))<.9 and abs(float(a['jaw_ndcy']))<.73,a
        _contacts.append(dict(frame=n,seconds=n/FPS,lift=n+1,pose=a))
    air=all_[316:422];assert all(x['airborne']=='0' and [x['x'],x['y'],x['z']]==['0','0','0'] for x in air)
    assert abs(float(all_[365]['jaw_ndcx']))<.91 and abs(float(all_[890]['jaw_ndcx']))<.91
    rim=next(int(x['frame']) for x in all_[531:596] if float(x['x'])<0 and radius(x)>4.33)
    assert all_[rim]['airborne']=='1' and all_[596]['support']=='6' and radius(all_[596])>4.95
    wall=all_[690];assert abs(float(wall['jaw_gap'])-.009)<.001 and all_[689]['airborne']=='1' and wall['airborne']=='0'
    assert float(all_[745]['y'])<float(wall['y'])-.3 and radius(all_[745])<3.3
    f0,f1=[np.asarray(still(f).resize((270,480)),dtype='f') for f in (0,FRAMES-1)]
    d=float(np.mean(np.abs(f0-f1)));assert .021<d<4., d
    return dict(takes=len(plan),native_size=NATIVE,bites=_contacts,standalone_air_snap=365,wall=690,clearance=rim,
                landing=596,loop_pixel_mae_8bit=round(d,4))


def fast_start(path):
    seen=[]
    with path.open('rb') as p:
        length=path.stat().st_size
        while p.tell()<length:
            pos=p.tell();n,k=struct.unpack('>I4s',p.read(8));h=8
            if n==1:n=struct.unpack('>Q',p.read(8))[0];h=16
            if n==0:n=length-pos
            assert h<=n<=length-pos;seen.append(k);p.seek(pos+n)
    assert b'ftyp' in seen and seen.index(b'moov')<seen.index(b'mdat')


def picture_gate(path):
    args=['-threads','2','-i',path,'-map','0:v:0','-an','-vf','showinfo','-fps_mode','passthrough','-f','null','-']
    raw=ff(*args).stderr.decode();pre=raw.split('Stream mapping:',1)[0];headers=[s.strip() for s in pre.splitlines() if re.match(r'^\s*Stream #0:',s)]
    w,h=EXPORT
    assert len(headers)==2 and any(all(k in r for k in ('Video: h264 (High)',f'{w}x{h}', 'yuv420p','bt709','30 fps')) for r in headers),headers
    assert any('Audio: aac (LC)' in r and '48000 Hz, stereo' in r for r in headers),headers
    assert 'Duration: 00:00:34.00' in pre and 'start: 0.000000' in pre
    tb=Fraction(re.search(r'config in time_base: (\d+/\d+)',raw).group(1)); dt=1/(tb*FPS)
    assert dt.denominator==1
    rows=re.findall(r'\bn:\s*(\d+)\s+pts:\s*(\d+)\s+pts_time:[^\n]*?\bchecksum:([\dA-F]{8})',raw)
    assert len(rows)==FRAMES,(len(rows),FRAMES,raw[-400:])
    assert all(int(n)==i and int(t)==i*dt for i,(n,t,h) in enumerate(rows))
    assert raw.count('color_range:tv color_space:bt709 color_primaries:bt709 color_trc:bt709')==FRAMES
    dup=[int(b[0]) for a,b in zip(rows,rows[1:]) if a[2]==b[2]]
    assert not dup,dup
    fast_start(path)
    return dict(frames=FRAMES,duration=FRAMES/FPS,fps=FPS,size=EXPORT,streams=headers,decodable=True,duplicate_frames=dup)


def audio_gate(path):
    p=decode(WORK/'short-mix.wav',2); raw=decode(path,2); assert len(p)==SAMPLES
    x=decode(path,2,af=f'atrim=end_sample={SAMPLES}')
    # An AAC LC tail may decode through the last 1024-sample packet. The MP4
    # display clock and trimmed program are precisely 34 seconds.
    assert SAMPLES<=len(raw)<SAMPLES+1024 and x.shape==p.shape,(len(raw),x.shape)
    corr=[]
    for q in json.loads((QA/'mix.json').read_text())['dialogue_edits']:
        l,h=q['mix_samples'];a=x[l:h].ravel();b=p[l:h].ravel()
        v=np.corrcoef(a,b)[0,1];corr.append(float(v))
    assert min(corr)>.985,corr
    m=measure(path);assert -20.<m['LUFS_I']<-14.0 and m['dBTP']<=-1.7,m
    return dict(meter=m,program_samples=SAMPLES,decoder_samples=len(raw),min_dialogue_span_corr=min(corr),encoder_rms_error_db=20*math.log10(rms(x-p)))


def encoded_still(path,f):
    data=ff('-loglevel','error','-ss',f'{f/FPS:.6f}','-i',path,'-map','0:v:0','-an','-frames:v','1',
            '-vf','scale=360:640:flags=lanczos','-c:v','png','-f','image2pipe','-').stdout
    return Image.open(BytesIO(data)).convert('RGB')


def phone_board(path):
    frames=[10,22,156,217,367,394,475,499,584,703,768,869,943,980,1019]
    sizes=(192,341);cw=209;rh=372
    for j in range(3):
        b=Image.new('RGB',(5*cw+16,rh+49),'#132222');d=ImageDraw.Draw(b)
        d.text((13,12),'MONARCH CAM / SHORT · ENCODED MOBILE CHECK  •  UI MOCK ONLY',fill='#fcf5dd')
        for i,f in enumerate(frames[j*5:(j+1)*5]):
            im=encoded_still(path,f).resize(sizes,Image.Resampling.LANCZOS).convert('RGBA')
            scrub=Image.new('RGBA',sizes);u=ImageDraw.Draw(scrub)
            u.rectangle((0,277,192,341),fill=(6,10,11,145))
            u.text((10,287),'@MonarchCam',fill='#fff6e4')
            u.text((10,305),'▷  Related video',fill='#fff6e4')
            u.text((10,321),'This Ant’s Jump…',fill='#fff6e4')
            for y in range(180,274,22):u.ellipse((172,y,183,y+11),outline='#faeee1',width=1)
            im=Image.alpha_composite(im,scrub).convert('RGB');left=i*cw+13
            b.paste(im,(left,37));d.text((left,382),f'{f/FPS:05.2f}s · f{f:04d}',fill='#c1dacd')
        b.save(QA/f'encoded-phone-{j+1}.jpg',quality=92)


def promote(path):
    spec=dict(motion=trace_gate(),picture=picture_gate(path),sound=audio_gate(path))
    phone_board(path); assert path.stat().st_size<100_000_000
    spec.update(filename=f'{NAME}.mp4',bytes=path.stat().st_size, sha256=sha256(path.read_bytes()).hexdigest(),
            built_in_cta='narrative question only; no spoken viewing instruction, arrow or fake UI',
            voice=VOICE['voice'],captions_cues=len(VOICE['captions']))
    (QA/'delivery.json').write_text(json.dumps(spec,indent=2)+'\n');OUT.mkdir(parents=True,exist_ok=True)
    for src,name in [(path,f'{NAME}.mp4'),(WORK/'short.en.srt',f'{NAME}.en.srt'),(HERE/'upload.txt',f'{NAME}-Upload.txt')]:
        dest=OUT/name;tmp=dest.with_suffix('.pending');shutil.copyfile(src,tmp);tmp.replace(dest)
    print(f"SHORT_DELIVERY_READY {OUT/ (NAME+'.mp4')} {spec['bytes']} bytes {spec['sha256']}\n{spec['sound']}",flush=True)


if __name__=='__main__':promote(WORK/'short.mp4')
