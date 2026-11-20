"""Validate encoded frame/audio clocks, motion anchors, mattes, and locked VO."""
import argparse
from fractions import Fraction
from hashlib import sha256
import json
from math import hypot, isfinite
import os
from pathlib import Path
import re
import shutil
import struct

import numpy as np

from pilot import CONTACT, DELIVERY, FPS, FRAMES, LANDING, PLAN, QA, ROOT, SAMPLES, SPF, SR, TITLE, WORK, dims, make_dirs, picture_trace, voice_plate
from mix import SOURCE, db, decode, ff, measure, rms
from finish import plates
from titles import KEYS, composite, verify_fonts

CUES = [
    (3, 51, 'The ant is climbing.'),
    (65, 121, 'The hill is coming down.'),
    (130, 216, "Her feet keep moving,\nbut she's sliding backwards."),
    (239, 330, 'Below her, two pincers\nrise out of the sand.'),
    (335, 377, "Now watch the ant's head."),
    (389, 416, 'She dips it.'),
    (422, 480, 'Her jaws hit the slope.'),
    (492, 517, "And she's out."),
    (526, 580, 'Those jaws swing inward.'),
    (593, 688, 'So how do they send\nan entire ant up?'),
]


def motion_gate():
    r = picture_trace()
    cut_list = []
    for line in PLAN.read_text().splitlines():
        if not line or line.startswith('#'):continue
        lo,hi,mode,lens,start,stop,name,*pins = line.split()
        lo,hi,lens = int(lo),int(hi),int(lens)
        rows = r[lo:hi];t = [float(p['motion_s']) for p in rows]
        assert all(p['shot']==name and int(p['lens'])==lens for p in rows)
        assert all(isfinite(n) for n in t) and all(b>a for a,b in zip(t,t[1:])), name
        assert abs(t[0]-float(start))<1.e-5 and abs(t[-1]-float(stop))<1.e-5
        for f,v in zip(pins[::2],pins[1::2]):
            assert abs(float(r[int(f)]['motion_s'])-float(v))<1.e-5, name
        cut_list.append(dict(label=name, first=lo, end=hi, lens=lens))
    assert len(cut_list)==11 and cut_list[-1]['end']==FRAMES
    n = CONTACT
    a,b = r[n],r[n+1]
    assert a['shot']==b['shot']=='one_unbroken_contact' and a['lens']==b['lens']=='6'
    tip=float(a['jaw_gap'])
    assert -.002<tip<.002 and float(r[392]['jaw_gap'])>.24
    assert a['support']=='5' and a['airborne']=='0' and b['airborne']=='1' and b['support']=='0'
    assert float(b['y'])-float(a['y'])>.04 and float(b['jaw_gap'])>.02
    assert all(abs(float(r[f][k]))<.91 for f in range(n-10,n+35) for k in ('jaw_ndcx','jaw_ndcy'))
    radius = lambda row: hypot(float(row['x']), 1.035*float(row['z']))
    rim=next(int(q['frame']) for q in r[484:LANDING] if q['airborne']=='1' and float(q['x'])<0 and radius(q)>4.33)
    landed=r[LANDING]
    assert landed['support']=='6' and landed['airborne']=='0' and radius(landed)>4.95 and LANDING>rim
    slide = float(r[146]['x'])-float(r[193]['x'])
    assert slide>.36 and float(r[193]['y'])<float(r[146]['y'])-.09
    assert len({r[x]['support'] for x in range(146,194)})>=2
    assert [int(v['frame']) for v in r if v['foreground_cut']=='1']==list(range(227,241))
    return dict(shots=cut_list, bite=dict(frame=n, seconds=n/FPS, tip_gap_scene_units=tip, first_lift_frame=n+1,
                                         rim_frame=rim, landing_frame=LANDING),
                slip=dict(marker_static_in_set=True, delta_x_scene_units=round(-slide,5)), pincer_cut_frame=234)


def matte_gate():
    verify_fonts()
    proof = {}
    anchors = [0,109,173,233,234,304,426,441,442,484,519,551,580,682]
    for f, im in plates(anchors):
        mask = np.asarray(im.getchannel('A'))
        a=np.asarray(im.convert('RGB'))
        if f in (233,234):
            h,w=mask.shape
            core=(mask[h//10:h*9//10,w//10:w*9//10] > 204).mean()
            assert core>.975,(f,core)
            proof[f'pincer_center_area_{f}']=round(float(core),5)
        b=np.asarray(composite(im,f).convert('RGB'))
        diff=np.any(a!=b,axis=2)
        if (fully := mask==255).any():
            assert not diff[fully].any(), ('type painted onto an opaque actor pixel', f)
        band=next((x for x in KEYS if x[0]<=f<x[1]), None)
        if band:
            assert diff.any(),f
        else:
            assert not diff.any(),f
    return proof


def fast_start(path):
    seen=[]
    with path.open('rb') as p:
        length=path.stat().st_size
        while p.tell()<length:
            pos=p.tell(); size,tag=struct.unpack('>I4s',p.read(8));h=8
            if size==1:size=struct.unpack('>Q',p.read(8))[0];h=16
            if size==0:size=length-pos
            assert h<=size<=length-pos
            seen.append(tag);p.seek(pos+size)
    assert b'ftyp' in seen and seen.index(b'moov')<seen.index(b'mdat'),seen


def picture_gate(path):
    text=ff('-threads',2,'-i',path,'-map','0:v:0','-an','-vf','showinfo','-fps_mode','passthrough','-f','null','-').stderr.decode()
    headers=[h.strip() for h in text.split('Stream mapping:',1)[0].splitlines() if re.match(r'^\s*Stream #0:',h)]
    w,h=dims()
    assert len(headers)==2 and any(all(v in row for v in ('Video: h264 (High)',f'{w}x{h}','bt709','30 fps')) for row in headers),headers
    assert any('Audio: aac (LC)' in row and '48000 Hz, stereo' in row for row in headers), headers
    timebase=Fraction(re.search(r'config in time_base: (\d+/\d+)',text).group(1)); dt=1/(timebase*FPS)
    assert dt.denominator==1
    hits=re.findall(r'\bn:\s*(\d+)\s+pts:\s*(\d+)\s+pts_time:[^\n]*?\bchecksum:([\dA-F]{8})',text)
    assert len(hits)==FRAMES,(len(hits),FRAMES,text[-1200:])
    assert text.count('color_range:tv color_space:bt709 color_primaries:bt709 color_trc:bt709')==FRAMES, 'incomplete Rec.709 tags'
    assert all(int(j)==i and int(p)==i*dt for i,(j,p,h) in enumerate(hits)), 'non-CFR clock'
    identical=[i for i in range(1,len(hits)) if hits[i][2]==hits[i-1][2]]
    assert not identical,identical
    fast_start(path)
    return dict(resolution=[w,h], fps=FPS, timebase=str(timebase), frames=len(hits), duplicate_decoded_frames=identical, streams=headers)


def audio_gate(path):
    a=decode(path,2)
    assert a.shape==(SAMPLES,2), a.shape
    mono=np.mean(a,axis=1);v,placement=voice_plate()
    correlations=[]
    for i in range(0,len(v)-38400,24000):
        x,y=v[i:i+38400],mono[i:i+38400]
        active=np.mean(x.reshape(40,960)**2,axis=1)>=.00010
        if active.sum()<5:continue
        sel=np.repeat(active,960)
        correlations.append(float(np.corrcoef(x[sel],y[sel])[0,1]))
    assert len(correlations)>24 and min(correlations)>.973,(len(correlations),min(correlations))
    foley=decode(WORK/'v3-foley.wav',2).mean(axis=1)
    c=CONTACT*SPF
    before, after=foley[c-3840:c],foley[c:c+3840]
    pulse=db(rms(after)); contrast=pulse-db(max(rms(before),10**(-90/20)))
    power=np.abs(np.fft.rfft(after*np.hanning(len(after))))**2
    high=100.*power[320:].sum()/max(power.sum(),1.e-18)
    assert pulse>-46 and contrast>12 and high<2, (pulse,contrast,high)
    land=LANDING*SPF
    assert db(rms(foley[land:land+3840]))>-52
    m=measure(path)
    assert -21.5<m['LUFS_I']<-18.6 and m['dBTP']<-2.9,m
    return dict(samples=len(a), loudness=m, voiced_windows=len(correlations), vo_min_corr=min(correlations),
                vo_median_corr=float(np.median(correlations)), source_sha256=SOURCE, source_placements=placement,
                strike=dict(first_sample=c, first_80ms_dBFS=pulse, gain_vs_preceding_80ms_dB=contrast,
                            percent_at_and_above_4k=float(high), landing_first_sample=land))


def write_srt(path):
    def stamp(f):
        m=round(1000*f/FPS);s,m=divmod(m,1000);n,s=divmod(s,60)
        return f'00:{n:02d}:{s:02d},{m:03d}'
    script=Path(os.environ.get('MONARCH_SCRIPT_TXT','deliverables/monarch-cam-step-2/Monarch-Cam-Ant-Narration.txt'))
    normalize=lambda s:' '.join(s.replace('’',"'").split())
    assert normalize(' '.join(x[2] for x in CUES))==normalize(script.read_text().split('From above,',1)[0])
    assert all(0<=a<b<=FRAMES and max(map(len,text.splitlines()))<=37 for a,b,text in CUES)
    assert all(a[1]<=b[0] for a,b in zip(CUES,CUES[1:]))
    path.write_text(''.join(f'{i}\n{stamp(a)} --> {stamp(b)}\n{text}\n\n' for i,(a,b,text) in enumerate(CUES,1)),encoding='utf-8')


def notes(path, r):
    a=r['audio']['loudness'];p=r['picture'];v=r['motion']['bite'];w,h=p['resolution']
    lines=f'''MONARCH CAM — THIS ANT BITES THE GROUND TO ESCAPE
V3 OPENING PILOT · 00:23.60 · {w}×{h} · 30 fps · Rec.709 · Stereo AAC 48 kHz

REVIEW POINTS
00:00.00  Macro mein pehle pairon ka contact; phir sand apni jagah chhor deti hai.
00:04.10  Pathar wahi rehta hai. Pair chal rahe hain, lekin ant uske muqable mein neeche phisalti hai.
00:06.47  Camera ek grain ko follow karta hai. 00:07.80 par pincer ke peechhe cut chhupa hai.
00:14.70  Jaw tips sand ko hit karti hain. Isi shot mein recoil, lift aur sand ka spray; is par type nahi rakhi.
00:{v['rim_frame']/FPS:05.2f}  Wide mein rim clear hoti hai; landing 00:17.30 par.
00:17.47  3D jaw study mein cyan arcs actual animated tips ke sweep ko trace karti hain. Phir sawal: go up kaise?

SCOPE
This is the first 23.60 seconds only, not the full V3 film. Same selected English VO, same edit positions
and constant V2 VO gain (−0.90 dB), no timing or performance change. Four typography passages add emphasis;
for every word of narration, load the optional .srt in the player. No subtitles are forced over the strike.
V2 remains a separate, unchanged deliverable. This is a review copy, not a publication or viewer result.

PICTURE & SOUND
11 newly rendered viewpoints/takes; 708 native frames. No V2 video frames or generated in-between frames.
Original Foley edit from the recordings below plus a single damped synthesis layer on the strike. Cello,
piano and pizzicato score re-arranged around this cut. Music narrows before the strike, then replies after
lift. Encoded audio: {a['LUFS_I']:.2f} LUFS-I, {a['dBTP']:.2f} dBTP. Full-file decode, frame clocks, sync to the
locked VO, cue onset, and selected encoded images checked. Please audition the mix on your usual device.

SCIENCE
An illustrative CGI sequence; not footage, a measured individual trajectory, or lab timing. The first
jaw-to-sand contact is visibly distinct from subsequent lift. Arc guides show jaw motion in the model,
not the direction of the ground's force. No field survival rate is implied.
• Larabee & Suarez (2015), Mandible-Powered Escape Jumps in Trap-Jaw Ants Increase Survival Rates
  during Predator–Prey Encounters, PLOS ONE 10(5), e0124871. https://doi.org/10.1371/journal.pone.0124871
• Sutton et al. (2022), Dual spring force couples yield multifunctionality and ultrafast,
  precision rotation in trap-jaw ant mandibles, J. Exp. Biol. 225, jeb244077. https://doi.org/10.1242/jeb.244077

ASSET CREDITS — retain with any future published export
• Generated sand/bokeh material plates; inherited chitin material and ant geometry re-lit in native 3D.
• Space Grotesk, Florian Karsten and contributors; IBM Plex Mono, IBM Corp. SIL Open Font License 1.1.
  Source revisions/font notices in source-assets. https://github.com/google/fonts/tree/5bd87dfc525c8a0d1d8529d3684716e00c3fc59a/ofl
• Kenney (Kenney Vleugels), RPG Audio, gravel_02 / 05 / 07 / 08, CC0 1.0. https://kenney.nl/assets/rpg-audio
  Mirror: https://github.com/evanlin23/blocky-stories/tree/328f356539d059f360175b66f3a88b2ba78e7c91/assets/audio/steps/gravel
• crashoverride6, “Sand on Paper, Dragged - Long,” CC0 1.0, mirrored excerpt. https://freesound.org/people/crashoverride6/sounds/146408/
• BranndyBottle, “sandwalking_step1.wav” / “sandwalking_step2.wav,” CC0 1.0.
  https://freesound.org/people/BranndyBottle/sounds/464699/ · https://freesound.org/people/BranndyBottle/sounds/464695/
• OwlStorm (Ashe Kirk / Owlish Media), “Click / Finger Snap,” CC0 1.0. https://freesound.org/people/OwlStorm/sounds/151214/
• VCKHaze, “Single Finger Snap,” CC0 1.0. https://freesound.org/people/VCKHaze/sounds/332604/
  Individual Freesound clips sourced as WAV from WilhelmSFX at ec4875a35d265b5431e3ba81fef6cc0ca0281bfc.
  They are trimmed, speed-edited, equalized, panned and layered; these are not insect field recordings.
  CC0: https://creativecommons.org/publicdomain/zero/1.0/
• FluidR3_GM instrument samples: Frank Wen and contributors, packaged by Benjamin Gleitzman.
  Pinned distribution and notice: https://github.com/gleitz/midi-js-soundfonts/tree/044fab8e1456bfafc5776e86dfd6bb8697149aef
  CC BY 3.0 US per distribution: https://creativecommons.org/licenses/by/3.0/us/
  Piano, pizzicato strings and cello filtered, shaped, mixed, and arranged as a new opening score.

MP4 SHA-256: {r['sha256']}
'''
    path.write_text(lines,encoding='utf-8')


def deliver(path):
    report=dict(duration_seconds=FRAMES/FPS, bytes=path.stat().st_size, sha256=sha256(path.read_bytes()).hexdigest())
    assert report['bytes']<100_000_000
    report.update(motion=motion_gate(), matte=matte_gate(), picture=picture_gate(path), audio=audio_gate(path),
                  titles=[dict(start=lo, end=hi, label=k) for lo,hi,k in KEYS])
    (QA/'delivery.json').write_text(json.dumps(report, indent=2)+'\n')
    assets=DELIVERY/'source-assets'; assets.mkdir(parents=True,exist_ok=True)
    paths=[PLAN, QA/'delivery.json', QA/'mix.json', WORK/'spotting.json', WORK/'jaw-guide.csv',
           *[QA/f'native-{i}.csv' for i in range(4)],
           ROOT/'assets'/'dune-quartz.png', ROOT/'assets'/'forest-bokeh.png',
           *list((ROOT/'assets'/'fonts').glob('*-OFL.txt')), ROOT/'assets'/'fonts'/'sources.json']
    for f in paths:shutil.copy2(f, assets / f.name)
    write_srt(DELIVERY/f'{TITLE}.en.srt')
    notes(DELIVERY/f'{TITLE}-Review-and-Credits.txt',report)
    out=DELIVERY/f'{TITLE}.mp4'; pending=out.with_suffix('.pending.mp4')
    shutil.copyfile(path,pending);pending.replace(out)
    print(json.dumps(report,indent=2))
    print(f'V3_OPENING_PILOT_READY {out}')


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--input',type=Path,default=WORK/'v3-opening-review.mp4')
    a=cli.parse_args();make_dirs();deliver(a.input)
