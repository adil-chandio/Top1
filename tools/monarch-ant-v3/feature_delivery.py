"""Verify the actual V3 MP4, then promote the full feature separately from the pilot."""
import argparse
import csv
from fractions import Fraction
import json
from math import cos, hypot, isfinite, sin
from pathlib import Path
import re
import shutil

import numpy as np
from PIL import Image, ImageDraw
from delivery import fast_start, motion_gate as opening_gate
from feature_cut import ANCHORS, DELIVER, EDL, FPS, META, NAME, MASTER, QA, WORK
from feature_finish import OPENING, OPENING_SHA, compose, filehash, image
from feature_mix import voice
from feature_titles import PROTECTED, marks, plan
from feature_words import load_words, srt
from pilot import QA as PILOT_QA, WORK as PILOT_WORK, ROOT, SPF
from mix import SOURCE, db, decode, ff, measure, rms
from platepack import frames as packed_frames

FRAMES = ANCHORS[-1]
CONTACTS = (441,4297,5267,7636,8186,8492,8873)
PROOF = (519,707,708,772,848,936,1248,1403,2039,2410,2411,2524,2569,2663,2726,
         2767,2944,3093,3233,3428,3545,4140,4188,4296,4297,4298,4320,4408,4474,4719,4738,5267,
         5298,5299,5325,5371,5416,5474,5591,5689,5785,5866,5940,6130,6499,6701,6767,6899,
         6969,7158,7280,7346,7507,7566,7669,8025,8186,8220,8417,8550,8873,8951,8993)


def trace_gate(m):
    r={}; out=QA/'feature-native-trace.csv'
    paths=[PILOT_QA/f'native-{j}.csv' for j in range(4)]
    paths.extend(QA/f"take-{s['first']}.csv" for s in m['shots'] if s['beat']>1)
    headers=None
    with out.open('w',newline='') as dest:
        wt=None
        for p in paths:
            with p.open() as f:
                a=csv.DictReader(f)
                if headers is None:
                    headers=a.fieldnames; wt=csv.DictWriter(dest,fieldnames=headers);wt.writeheader()
                assert a.fieldnames==headers
                for q in a:
                    i=int(q['frame']);assert i==len(r);r[i]=q;wt.writerow(q)
    assert len(r)==FRAMES
    mark=marks(); assert sorted(mark)==list(range(ANCHORS[1],FRAMES))
    for s in m['shots']:
        lo,hi=s['first'],s['end'];ts=[]
        for f in range(lo,hi):
            q=r[f]; t=float(q['motion_s']);ts.append(t)
            assert isfinite(t) and q['shot']==s['subject'] and int(q['lens'])==s['camera']
        assert abs(ts[0]-s['src'][0])<2e-5 and abs(ts[-1]-s['src'][1])<2e-5
        assert all(b>a for a,b in zip(ts,ts[1:])),s['subject']
        for f,t in s['pins']:assert abs(ts[f-lo]-t)<2e-5,(s['subject'],f,ts[f-lo],t)
    def y(f):return float(r[f]['y'])
    def gap(f):return float(r[f]['jaw_gap'])
    def radius(f):return hypot(float(r[f]['x']),1.035*float(r[f]['z']))
    table={}
    for f in CONTACTS:
        a,b=r[f],r[f+1]
        assert a['shot']==b['shot'] and abs(gap(f))<.002 and a['support']=='5' and a['airborne']=='0',a
        assert y(f+1)>y(f) and b['airborne']=='1' and gap(f+1)>.003,b
        zero=next(n for n in range(f+1,f+9) if r[n]['support']=='0' and r[n]['airborne']=='1')
        table[str(f)]=dict(subject=a['shot'],contact_frame=f,first_lift_frame=f+1,first_no_near_tarsi_frame=zero,scene_units_gap=gap(f))
    r0=next(f for f in range(4642,4738) if r[f]['airborne']=='1' and float(r[f]['x'])<0 and radius(f)>4.33)
    assert radius(4738)>4.95 and r[4738]['airborne']=='0' and r[4738]['support']=='6'
    assert all(abs(float(r[f][k]))<.92 for f in range(4286,4333) for k in ('jaw_ndcx','jaw_ndcy'))
    for f in (4297,4408,5325,8873):
        for name,ndc in [('body','body_ndc'),('tip','jaw_ndc')]:
            assert abs((mark[f][name+'_x']-.5)*2-float(r[f][ndc+'x']))<1.8e-5
            assert abs((.5-mark[f][name+'_y'])*2-float(r[f][ndc+'y']))<1.8e-5
    # Verify that the imagined 'snap in air' is distinct from the upward launch.
    assert len({tuple(r[f][k] for k in 'xyz') for f in range(4078,4261)})==1
    assert mark[4099]['jaw_angle']>1.2 and mark[4235]['jaw_angle']<.09
    for f in range(6658,6785):
        # Distal spacing for the illustrated bond, independently of camera crop.
        t=mark[f]['jaw_angle'];tip_span=2*abs(.153+.730*sin(t)-.079*.76*cos(t))
        assert 0.<tip_span<.018,(f,tip_span)
    a=max(range(5270,5325),key=y);hit=5325;return_f=5416
    assert radius(a)<4.33 and y(a)>y(hit)+.8 and radius(return_f)<min(2.5,radius(hit)-1.)
    assert r[hit-1]['airborne']=='1' and r[hit]['airborne']=='0' and abs(gap(hit))<.02
    assert r[return_f]['airborne']=='0' and y(return_f)<y(hit)-.6
    return dict(opening=opening_gate()['bite'],contact_beats=table,alternate=dict(rim_frame=r0,landing_frame=4738),
                failed_jump=dict(apex_frame=a,wall_frame=hit,fall_back_frame=return_f,wall_gap_scene_units=gap(hit)),
                no_external_surface=dict(first_frame=4078,last_frame=4260,body_fixed=True))


def decode_info(path,limit=None,extract=False):
    lim=[] if limit is None else ['-frames:v',limit]
    target=['-f','null','-']; filt='showinfo'
    if extract:
        assert limit is None and PROOF[-1]==FRAMES-1
        folder=QA/'encoded';folder.mkdir(exist_ok=True)
        filt+=',select='+ '+'.join(f'eq(n\\,{i})' for i in PROOF)+',scale=480:270:flags=lanczos'
        target=['-q:v',2,folder/'%03d.jpg']
    t=ff('-y','-threads',2,'-i',path,'-map','0:v:0','-an',*lim,'-filter_threads',2,'-vf',filt,'-fps_mode','passthrough',*target).stderr.decode(errors='replace')
    hdr=[q.strip() for q in t.split('Stream mapping:',1)[0].splitlines() if re.match(r'^\s*Stream #0:',q)]
    timebase=Fraction(re.search(r'config in time_base: (\d+/\d+)',t).group(1));dt=1/(timebase*FPS)
    hits=re.findall(r'\bn:\s*(\d+)\s+pts:\s*(\d+)\s+pts_time:[^\n]*?\bchecksum:([\dA-F]{8})\s+plane_checksum:\[([^\]]+)\]',t)
    assert dt.denominator==1
    assert all(int(i)==n and int(p)==n*dt for n,(i,p,*_) in enumerate(hits)), 'non-CFR clock'
    assert t.count('color_range:tv color_space:bt709 color_primaries:bt709 color_trc:bt709')==len(hits)
    return hdr,timebase,[(c,x) for _,_,c,x in hits]


def check_picture(p):
    hdr,tb,d=decode_info(p,extract=True);assert len(d)==FRAMES
    w,h=MASTER;v=[x for x in hdr if 'Video:' in x];a=[x for x in hdr if 'Audio:' in x]
    assert len(v)==len(a)==1 and all(x in v[0] for x in ('Video: h264 (High)',f'{w}x{h}','tv, bt709','30 fps')),(a,v)
    assert 'Audio: aac (LC)' in a[0] and '48000 Hz, stereo' in a[0],a
    _,_,o=decode_info(OPENING,ANCHORS[1]);assert len(o)==ANCHORS[1] and o==d[:ANCHORS[1]], 'opening not pixel-identical'
    dup=[i for i in range(1,len(d)) if d[i]==d[i-1]]
    assert not dup,dup
    fast_start(p)
    return dict(frames=len(d),fps=FPS,resolution=MASTER,time_base=str(tb),opening_identical_frames=len(o),
                adjacent_identical_frames=dup,streams=hdr,fast_start=True)


def check_graphics(m):
    report=plan();tests=tuple(f for f in CONTACTS[1:]+(5325,8294,8951) if any(a<=f<b for a,b in PROTECTED))
    for f in tests:
        s=next(x for x in m['shots'] if x['first']<=f<x['end'])
        for n,w,h,p in packed_frames(WORK/f"take-{s['first']}.plates"):
            if n==f:
                im=image(p,w,h);before=im.tobytes();assert compose(im,n).tobytes()==before,n;break
        else:raise AssertionError(f'missing clean frame {f}')
    return dict(passages=report,protected_ranges=PROTECTED,checked_native_clean_frames=list(tests))


def check_audio(p,m):
    a=decode(p,2);n=FRAMES*SPF;assert a.shape==(n,2),(a.shape,n)
    v=voice(m);z=a.mean(axis=1);del a
    corr=[]
    for pass_no, (lo,hi,dst) in enumerate(m['vo_ranges'],1):
        values=[]
        for i in range(dst,dst+hi-lo-38400,28800):
            x=v[i:i+38400];active=(x.reshape(40,960)**2).mean(axis=1)>.00010
            if active.sum()<5:continue
            k=np.repeat(active,960)
            values.append(float(np.corrcoef(x[k],z[i:i+38400][k])[0,1]))
        assert len(values)>23 and min(values)>.972,(pass_no,len(values),min(values))
        corr.append(dict(chapter=pass_no,windows=len(values),min=min(values),median=float(np.median(values))))
    a=decode(WORK/'feature-mix.wav',2);o=decode(PILOT_WORK/'v3-mix.wav',2)
    n0=ANCHORS[1]*SPF
    assert np.array_equal(a[:n0],o), 'unapproved change to PCM opening'
    assert np.max(np.abs(a[n0]-a[n0-1]))<.002
    fx=decode(WORK/'feature-foley.wav',2).mean(axis=1); acc={}
    for f in (*CONTACTS,4180,5325,4738):
        k=f*SPF;pulse=fx[k:k+3840];before=db(max(rms(fx[k-3840:k]),10**(-90/20)))
        amp=db(rms(pulse));pw=np.abs(np.fft.rfft(pulse*np.hanning(len(pulse))))**2
        hf=100*float(pw[320:].sum()/max(pw.sum(),1e-21));assert amp>-54 and amp-before>8 and hf<1.15,(f,amp,amp-before,hf)
        acc[str(f)]=dict(sample=k,first_80ms_dBFS=amp,preceding_contrast_dB=amp-before,percent_at_or_above_4kHz=hf)
    loud=measure(p);assert -21.1<loud['LUFS_I']<-18.6 and loud['dBTP']<-2.8
    return dict(samples=n,loudness=loud,vo_sha256=SOURCE,original_pcm_opening_samples=n0,zero_offset_voice_corr=corr,cue_onsets=acc)


def stills(subset=PROOF):
    folder=QA/'encoded'
    for i in range(0,len(subset),12):
        b=subset[i:i+12];w,h=480,270;a=Image.new('RGB',(w*3,((len(b)+2)//3)*(h+24)),(20,28,26));d=ImageDraw.Draw(a)
        for j,f in enumerate(b):
            x,y=j%3*w,j//3*(h+24)
            with Image.open(folder/f'{i+j+1:03}.jpg') as im:a.paste(im,(x,y))
            d.text((x+10,y+h+4),f'VERIFIED  ·  {f:04}  /  {f/FPS:.2f}s',fill=(222,229,207))
        a.save(QA/f'encoded-board-{i//12+1}.jpg',quality=96)


def notes(path,r):
    ts=lambda f:f'{(f/FPS)//60:02.0f}:{(f/FPS)%60:05.2f}'
    audio=r['audio']['loudness'];wall=r['motion']['failed_jump']['wall_frame'];rim=r['motion']['alternate']['rim_frame']
    pnote=OPENING.with_name(OPENING.stem+'-Review-and-Credits.txt').read_text(encoding='utf-8')
    credits=pnote.split('ASSET CREDITS — retain with any future published export\n',1)[1].split('\nMP4 SHA-256:',1)[0].strip().replace('as a new opening score.','into a new score for this edit.')
    path.write_text(f'''MONARCH CAM — THIS ANT BITES THE GROUND TO ESCAPE
V3 FULL CINEMATIC CUT · 04:59.80 · 1920×1080 · 30 fps · H.264 Rec.709 · 48 kHz stereo AAC

REVIEW POINTS
00:00.00  Wahi approved opening. 00:14.70 par jaw contact aur lift par koi type nahi.
00:23.60  Upar se dent, rim se funnel. Larva ki sand upar; side ki dhalan neeche.
01:17.23  Locked-open hinge. 01:20.37 par match-cut se anatomy khulti hai; capsule push aur attachment pull alag hain.
01:50.73  77 microseconds lab mein mean jaw closure hai, ant ke hawa mein rehne ka waqt nahi.
02:15.93  Air snap without a surface. {ts(4297)} par asli farq: jaws sand ko touch karti hain, phir lift.
{ts(rim)}  Wide mein rim ke paar; {ts(4738)} par far-side landing.
{ts(wall)}  Wall hit. Ant rim se bahar nahi nikalti; wapas pit mein girti hai.
03:07.37  117 observed lab trials: running / jump escape / caught are separate outcomes.
04:08.47  Mock aur restrained: dono handled. Untouched baseline alag hai.
{ts(8873)}  Aakhri contact, phir khali bowl. Koi end card ya outro VO add nahi ki.

PICTURE AND SOUND
The approved first 708 decoded pictures are pixel-identical. Its 48 kHz PCM mix is carried through
before the single whole-film AAC encode. Selected English voice and the seven exact sample placements
are unchanged from the locked edit; no rate change, new read, or replacement. Graphics add emphasis
and clarify comparisons; the optional .en.srt covers the whole narration. No caption track is forced.
The continuation uses independently evaluated native 3D frames rendered at 1280×720, mastered to the
1080p delivery grid, with no V1 or V2 frames or optical-flow interpolation. The opener stays native 1080p.

Score and picture-synced Foley are separate, with a thinner air snap, a dry jaw/sand hit and lift answer,
a dull wall hit, and a closing cue after the last strike. They are designed sounds, not insect field
recordings. Measured encode: {audio['LUFS_I']:.2f} LUFS-I, {audio['dBTP']:.2f} dBTP. Full decode,
frame cadence, locked-voice correlation, Foley onsets and selected encoded image checks were performed.
These are technical checks, not a claim of audience retention or listening approval.

SCIENCE AND REPRESENTATION
• This is illustrative CGI. The grains, pivot labels, trajectories, timing, and lab dishes are not
  footage, CT data, measured forces, individual trial paths, or a reconstruction of actual lab apparatus.
• Observation: 117 lab trials with O. brunneus and third-instar larvae from three Myrmeleon species
  (M. carolinus, M. crudelis, M. mobilis). Fig. 3 specifically shows M. carolinus. The study only scored
  encounters after an attack. 15% of trials involved a jaw-propelled escape from the pit. This is distinct
  from 26.5% of observed jaw strikes generating jumps, including jumps that did not clear the pit.
  Three jumps hit a pit wall and fell back. “Caught” means held below the sand for at least 60 seconds,
  not proven dead. Fractions for running and catches are approximate as stated in the paper/narration.
• Restraint: 76 replicates per condition, separate from the 117 observation trials. Untouched baseline;
  mock (chilled, glue outside the mandibles, snap available); restrained (chilled, jaw tips held by glue).
  Both handled treatments reduced running success versus untouched. The mock–restrained comparison
  isolates snap availability better; the added escapes came via jumps. The schematic dishes denote
  conditions, not sample counts. No population-wide or field survival rate is implied.
• Mean closure measured from the initial latched position to 90° rotation was about 77 µs. It is not
  jaw–sand contact duration or flight time. The head capsule pushes; the recoiling muscle–apodeme unit
  pulls at a different point. Both act on the same jaw. The cutaway is a simplified explanatory model.

PRIMARY REFERENCES
Larabee & Suarez (2015), Mandible-Powered Escape Jumps in Trap-Jaw Ants Increase Survival Rates
During Predator–Prey Encounters. PLOS ONE 10(5), e0124871. https://doi.org/10.1371/journal.pone.0124871
Sutton et al. (2022), Dual spring force couples yield multifunctionality and ultrafast, precision rotation
in tiny biomechanical systems. J. Exp. Biol. 225, jeb244077. https://doi.org/10.1242/jeb.244077
Büsse et al. (2021), granular pit maintenance in Euroleon nostras (separate species/experiment).
https://pmc.ncbi.nlm.nih.gov/articles/PMC8440033/

ASSET CREDITS — retain with any future published export
{credits}

REVIEW COPY — not published. V2 and the approved V3 pilot remain separate and unchanged.
Workspace master MP4 SHA-256: {r['sha256']}
''',encoding='utf-8')


def report(path):
    m=json.loads(META.read_text());assert filehash(OPENING)==OPENING_SHA and m['vo_sha256']==SOURCE
    r=dict(duration_seconds=FRAMES/FPS,bytes=path.stat().st_size,sha256=filehash(path),takes=len(m['shots']),chapters=7)
    r['motion']=trace_gate(m);r['graphics']=check_graphics(m);print('TRACE_AND_GRAPHICS_QA_PASSED',flush=True)
    r['picture']=check_picture(path);print('DECODED_PICTURE_QA_PASSED',flush=True)
    r['audio']=check_audio(path,m);print('DECODED_AUDIO_QA_PASSED',flush=True)
    (QA/'feature-delivery.json').write_text(json.dumps(r,indent=2)+'\n')
    stills();print('FEATURE_QA_READY',flush=True)
    return r


def deliver(path):
    with (QA/'feature-delivery.json').open() as src:r=json.load(src)
    assert r['sha256']==filehash(path) and r['picture']['frames']==FRAMES
    D=DELIVER; A=D/'source-assets';A.mkdir(parents=True,exist_ok=True)
    p=D/f'{NAME}.mp4';t=p.with_suffix('.pending.mp4')
    shutil.copy2(path,t); assert filehash(t)==r['sha256']
    n=srt(load_words(),D/f'{NAME}.en.srt');assert n>70
    notes(D/f'{NAME}-Review-and-Credits.txt',r)
    for q in [EDL,META,WORK/'projection.csv',WORK/'feature-spotting.json',WORK/'locked-words.json',
              QA/'feature-native-trace.csv',QA/'feature-delivery.json',QA/'feature-mix.json',
              *list((ROOT/'assets'/'fonts').glob('*-OFL.txt')),ROOT/'assets'/'fonts'/'sources.json']:
        shutil.copy2(q,A/q.name)
    t.replace(p)
    print(f'FEATURE_DELIVERED {p} · {r["bytes"]:,} bytes · SHA-256 {r["sha256"]}',flush=True)


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--path',type=Path,default=WORK/f'{NAME}.mp4')
    g=cli.add_mutually_exclusive_group();g.add_argument('--promote',action='store_true');g.add_argument('--trace-only',action='store_true')
    a=cli.parse_args()
    if a.promote:deliver(a.path)
    elif a.trace_only:print(json.dumps(trace_gate(json.loads(META.read_text())),indent=2))
    else:report(a.path)
