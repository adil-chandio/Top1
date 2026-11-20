"""V2 export gates: exact media clocks, decoded pixels, contact, and locked VO."""
import argparse
import csv
from fractions import Fraction
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import shutil

import numpy as np
from cut import ROOT, SOURCE, SR, VO
from mix import QA, W, decode, ff, measure, native_vo, rms, db

D=Path(os.environ.get('MONARCH_V2_DELIVERY','deliverables/monarch-cam-step-4-v2'))
EXPORT='Monarch-Cam-Ant-Cinematic-Cut-v2.mp4'
KEYS=['first_dip_contact_and_recoil','proof_contact_other_side','failed_launch_wall_hit_and_fall','one_bite_closing_contact']


def setup():
    return json.loads((W/'film-v2.json').read_text())


def native_gate(m):
    with (QA/'v2-native-trace.csv').open() as g:rows=list(csv.DictReader(g))
    assert len(rows)==m['frames'] and all(int(p['frame'])==i for i,p in enumerate(rows))
    by_name={s['subject']:s for s in m['shots']}
    for s in m['shots']:
        a,z=s['first'],s['end'];r=rows[a:z]
        assert all(p['subject']==s['subject'] and int(p['camera'])==s['camera'] for p in r)
        assert all(float(b['motion_s'])>float(a['motion_s']) for a,b in zip(r,r[1:])),s['subject']
        assert all(abs(float(rows[f]['motion_s'])-v)<1.e-5 for f,v in s['pins']),s['subject']
    result={}
    coords=lambda r:[float(r['body_'+k]) for k in 'xyz']
    radius=lambda r:math.hypot(float(r['body_x']),1.035*float(r['body_z']))
    for key in KEYS:
        shot=by_name[key];f=next(f for f,t in shot['pins'] if t==3.42);a,b=rows[f:f+2]
        assert float(a['jaw_tip_gap'])<.002 and float(a['jaw_tip_gap'])>-.002 and a['support']=='5' and a['airborne']=='0'
        assert b['airborne']=='1' and float(b['jaw_tip_gap'])>0.004
        assert coords(b)[1]>coords(a)[1] and a['camera']==b['camera'] and a['subject']==b['subject'],key
        # The very slow other-side take initially moves less than the tarsal
        # proximity tolerance; distinguish first lift from zero near-ground toes.
        free=next((int(p['frame']) for p in rows[f+1:min(shot['end'],f+5)] if p['support']=='0' and p['airborne']=='1'),None)
        assert free is not None,key
        result[key]=dict(contact_frame=f,contact_s=f/m['fps'],lift_frame=f+1,
                         no_near_ground_tarsi_frame=free,tip_clearance_on_contact=float(a['jaw_tip_gap']))
    for key in ('opener_crosses_the_far_lip','clearance_from_across_the_bowl'):
        a=by_name[key];take=rows[a['first']:a['end']];lip=next(p for p in take if p['airborne']=='1' and radius(p)>4.33 and float(p['body_x'])<0)
        land=next(p for p in take if p['airborne']=='0' and p['support']=='6' and radius(p)>4.95)
        assert int(land['frame'])>int(lip['frame'])
        result[key]=dict(rim_frame=int(lip['frame']),landing_frame=int(land['frame']))
    a=by_name[KEYS[2]];f=next(f for f,t in a['pins'] if t==4.4728);hit=rows[f];end=rows[a['end']-1]
    top=max(rows[a['first']:f],key=lambda r:coords(r)[1]);assert coords(top)[1]>coords(hit)[1]+.80 and radius(top)<4.33
    assert abs(float(hit['jaw_tip_gap']))<.020 and rows[f-1]['airborne']=='1' and hit['airborne']=='0'
    assert radius(end)<radius(hit)-1.0 and radius(end)<2.5 and end['airborne']=='0'
    result[KEYS[2]].update(wall_frame=f,wall_s=f/m['fps'],apex_frame=int(top['frame']),falls_back_frame=int(end['frame']))
    air=by_name['snap_in_air_no_external_support'];r=rows[air['first']:air['end']]
    assert len({tuple(coords(p)) for p in r})==1 and all(p['airborne']=='0' for p in r)
    return result


def check_picture(path,m):
    data=ff('-threads',2,'-i',path,'-map','0:v:0','-an','-vf','showinfo','-fps_mode','passthrough','-f','null','-').stderr.decode(errors='replace')
    heads=[h for h in data.split('Stream mapping:',1)[0].splitlines() if re.match(r'^\s*Stream #0:',h)]
    assert len(heads)==2 and any('1280x720' in h and 'bt709' in h and '30 fps' in h and 'Video: h264' in h for h in heads),heads
    assert any('Audio: aac' in h and '48000 Hz, stereo' in h for h in heads),heads
    tb=Fraction(re.search(r'config in time_base: (\d+/\d+)',data).group(1));step=1/(tb*m['fps'])
    assert step.denominator==1
    hits=re.findall(r'\bn:\s*(\d+)\s+pts:\s*(\d+)\s+pts_time:[^\n]*?\bchecksum:([\dA-F]{8})',data)
    assert len(hits)==m['frames'], (len(hits),m['frames'],data[-1400:])
    assert all(int(j)==i and int(p)==i*step for i,(j,p,h) in enumerate(hits)), 'non-CFR presentation timestamps'
    dup=[i for i in range(1,len(hits)) if hits[i][2]==hits[i-1][2]]
    key_ranges=[(z['first'],z['end']) for z in m['shots'] if z['subject'] in KEYS]
    assert all(not any(lo<=k<hi for lo,hi in key_ranges) for k in dup),'a repeated decoded frame in contact or failure'
    return dict(fps=m['fps'],video_frames=len(hits),timebase=str(tb),frames_with_same_pixels_as_previous=dup,streams=heads)


def audio_gate(path,m,motion):
    a=decode(path,2);duration=m['frames']*SR//m['fps']; assert len(a)==duration,(len(a),duration)
    mid=np.mean(a,axis=1);del a
    words=native_vo();corr=[]
    for lo,hi,dst in m['vo_ranges']:
        for k in range(0,hi-lo-38400,38400):
            v=words[lo+k:lo+k+38400];z=mid[dst+k:dst+k+38400]
            active=np.mean(v.reshape(40,960)**2,axis=1)>=.00010
            if int(active.sum())<5:continue
            mask=np.repeat(active,960);u,w=v[mask],z[mask];u=u-u.mean();w=w-w.mean()
            corr.append(float(np.dot(u,w)/np.sqrt(np.dot(u,u)*np.dot(w,w))))
    assert len(corr)>300 and min(corr)>.975,(min(corr),len(corr))
    foley=decode(W/'foley-v2.wav',2).mean(axis=1);onsets={}
    for k in KEYS:
        t=motion[k]['contact_s'];c=round(t*SR)
        # Compare the audible onset window with a quiet slice immediately before it.
        before=max(10**(-90/20),rms(foley[c-3840:c]));first=foley[c:c+3840];ratio=db(rms(first))-db(before)
        assert rms(first)>10**(-58/20) and ratio>5., (k,db(rms(first)),ratio)
        power=np.abs(np.fft.rfft(first*np.hanning(len(first))))**2
        hf=100.*float(power[320:].sum()/max(power.sum(),1.e-20));assert hf<1.0,(k,hf)
        onsets[k]={'seconds':t,'contact_first_80ms_dBFS':db(rms(first)),
                   'gain_vs_preceding_80ms_dB':ratio,'percent_energy_at_4kHz_and_above':hf}
    r=measure(path);assert r['dBTP']<-2.7 and -21.0<r['LUFS_I']<-18.6
    return dict(audio_samples=duration,encoded_loudness=r,locked_vo_active_windows=len(corr),
                zero_offset_worst_correlation=min(corr),zero_offset_median_correlation=float(np.median(corr)),cue_onsets=onsets)


def mux(picture,mix,target,samples=None):
    audio_args=['-af',f'atrim=end_sample={samples}'] if samples is not None else []
    ff('-loglevel','warning','-i',picture,'-i',mix,'-map','0:v:0','-map','1:a:0','-map_chapters','-1','-map_metadata','-1',
       '-c:v','copy','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv',
       *audio_args,'-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-metadata','title=This Ant Bites the Ground to Escape — V2',
       '-metadata','artist=Monarch Cam','-metadata:s:a:0','language=eng','-movie_timescale','48000','-movflags','+faststart+write_colr','-y',target)


def package(m,receipt):
    """Save small rebuild inputs, not scratch plates, stems, sample banks or renders."""
    s=D/'source-assets';s.mkdir(parents=True,exist_ok=True)
    for a in [ROOT/'assets'/f'{n}.png' for n in ['fine-quartz','fern-light','chitin-micro']]+[
        W/'film-v2.plan',W/'film-v2.json',W/'spotting-v2.json',QA/'v2-audio.json',QA/'v2-delivery.json',QA/'v2-native-trace.csv',
        ROOT/'audio'/'audio-sources.json',ROOT/'audio'/'kenney-rpg-license.txt',ROOT/'audio'/'instr-readme.txt']:
        shutil.copy2(a,s/a.name)
    shutil.copy2(VO,s/'vo-edit-receipt.json')
    files=list((ROOT/'audio'/'downloaded').glob('*.wav'))+list((ROOT/'audio'/'instruments').glob('*.js'))
    (s/'source-checksums.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
    notes(s,m,receipt)


def notes(s,m,r):
    by_name={p['subject']:p for p in m['shots']}
    contact=r['motion'];get=lambda k:contact[k]['contact_s']
    def stamp(sec):return f'{int(sec)//60:02}:{sec%60:05.2f}'
    def start(k):return by_name[k]['first']/m['fps']
    times=[(0,'Pairon ki grip aur dhalan par phisalna.'),(get(KEYS[0]),'Pehla jaw-to-sand contact; foran baad ant zameen chhorti hai.'),
           (contact['opener_crosses_the_far_lip']['rim_frame']/m['fps'],'Wide shot: ant pit ki rim ke paar.'),
           (start('loading_both_elastic_elements'),'3D cutaway: head shell aur muscle attachment.'),
           (get(KEYS[1]),'Doosri taraf se slow-mo: jaws, sand aur recoil. Agle shots mein grains aur poori clearance.'),
           (contact[KEYS[2]]['wall_s'],'Nakaam jump: deewar se takra kar wapas pit mein.'),
           (start('compare_only_the_handled_groups'),'Do handled groups ka muqabla.'),
           (get(KEYS[3]),'Aakhri snap, phir sirf pit ka shaant closing shot.')]
    pages='\n'.join(f'{stamp(sec)}  {description}' for sec,description in times)
    audio=r['encoded_loudness']
    text=f'''MONARCH CAM — THIS ANT BITES THE GROUND TO ESCAPE
V2 · Cinematic review cut

{stamp(m['duration_s'])} / 1280×720 / 30 fps / H.264 Rec.709 + 48 kHz stereo AAC
{len(m['shots'])} cuts; {m['frames']:,} native rendered frames. No captions, cards, graphic overlays, or subtitle track.

REVIEW POINTS (Roman Urdu)
{pages}

PICTURE & SOUND
V2 recomposes the full English episode around the selected Step 03 voice and its original takes/pickups. The narration has no rate change or replacement. There are no V1 video frames, blends, or interpolated slow-motion frames. The scene is evaluated for every output frame; fixed camera sets retain cached static color and depth, not cached animation. The reprise is covered from different positions, with separately staged inset shots.

The original score is written for this edit, using felt-filtered piano, cello and pizzicato string samples. Score dips under the voice and at the featured jaw contacts; recorded footfalls, fine sand drag, close clicks and grit form separate, placeable cues. These are designed sounds, not recordings of insects. No continuous noise bed. Encoded integrated level {audio['LUFS_I']:.2f} LUFS and true peak {audio['dBTP']:.2f} dBTP. Full decode, sample timing, frame cadence, geometry and selected stills checked. Loudness and sync tests are not a listener approval; please review on the headphones or device you normally use.

SCIENCE AND REPRESENTATION
This is CGI, not lab footage, a CT scan, or a measurement of an individual trajectory. Timescale and geometric tracer units are illustrative. The three specimens/sand dishes show experimental conditions schematically, not sample counts, lab apparatus, or a measured trial. 'Caught' is not a claim that an individual was killed. The published counts are laboratory results, not estimated survival rates in nature.

• Larabee & Suarez (2015), Mandible-Powered Escape Jumps in Trap-Jaw Ants Increase Survival Rates during Predator–Prey Encounters. PLOS ONE 10(5), e0124871. Figs. 3–4, Tables 1–2. https://doi.org/10.1371/journal.pone.0124871
• Sutton et al. (2022), dual spring actuation in trap-jaw ant mandibles. J. Exp. Biol. 225, jeb244077. Fig. 5/Table 1. 77 microseconds refers to mean jaw closure, not flight time. https://doi.org/10.1242/jeb.244077
• Büsse et al. (2021), antlion pit/granular substrate study; evidence of maintenance in Euroleon nostras, not a measurement of the focal species' exact flick timing. https://pmc.ncbi.nlm.nih.gov/articles/PMC8440033/
• Generated texture/backplate images used as material inputs; worker, larva, terrain, cameras, particles and cutaway rendered in 3D. No reference photograph or study recording is shown as film footage.

AUDIO CREDITS — retain alongside the film or in its description at any later publication
• Kenney (Kenney Vleugels), RPG Audio, gravel_02 / 05 / 07 / 08, CC0 1.0. https://kenney.nl/assets/rpg-audio . Pinned audio mirror: https://github.com/evanlin23/blocky-stories/tree/328f356539d059f360175b66f3a88b2ba78e7c91/assets/audio/steps/gravel
• crashoverride6, “Sand on Paper, Dragged - Long,” CC0 1.0, via a mirrored excerpt. https://freesound.org/people/crashoverride6/sounds/146408/
• BranndyBottle, “sandwalking_step1.wav” / “sandwalking_step2.wav,” CC0 1.0. https://freesound.org/people/BranndyBottle/sounds/464699/ and https://freesound.org/people/BranndyBottle/sounds/464695/
• OwlStorm (Ashe Kirk / Owlish Media), “Click / Finger Snap,” CC0 1.0. https://freesound.org/people/OwlStorm/sounds/151214/
• VCKHaze, “Single Finger Snap,” CC0 1.0. https://freesound.org/people/VCKHaze/sounds/332604/
• Individual Freesound clips were retrieved as WAV files from WilhelmSFX at ec4875a35d265b5431e3ba81fef6cc0ca0281bfc. The named original clip licenses, not the entire collection's rights, were checked. Edits: trimming, speed, soft-band filtering, stereo placement, layering and fades. CC0: https://creativecommons.org/publicdomain/zero/1.0/
• FluidR3_GM instrument samples (Frank Wen and contributors; packaged by Benjamin Gleitzman): acoustic grand piano, cello, pizzicato strings. Sample distribution declares Creative Commons Attribution 3.0 US: https://creativecommons.org/licenses/by/3.0/us/ . Pinned distribution and notice: https://github.com/gleitz/midi-js-soundfonts/tree/044fab8e1456bfafc5776e86dfd6bb8697149aef . Samples excerpted, filtered, shaped, mixed and arranged into a new score, not an unmodified library track.

REVIEW COPY, NOT PUBLISHED
V1 is left intact. This V2 is submitted for review, not presented as approved or as evidence of retention.
MP4 SHA-256: {r['sha256']}
'''
    (D/'Monarch-Cam-Ant-V2-Review-and-Credits.txt').write_text(text,encoding='utf-8')


def build():
    m=setup();D.mkdir(parents=True,exist_ok=True);p=W/'review-v2-before-qa.mp4'
    motion=native_gate(m);mux(W/'v2-picture.mp4',W/'mix-v2.wav',p)
    r=dict(duration_s=m['duration_s'],bytes=p.stat().st_size,sha256=sha256(p.read_bytes()).hexdigest(),
           motion=motion,shots=len(m['shots']),native_evaluations=m['frames'],vo_sha256=SOURCE)
    assert r['bytes']<100_000_000,r['bytes']
    r.update(check_picture(p,m));r.update(audio_gate(p,m,motion))
    (QA/'v2-delivery.json').write_text(json.dumps(r,indent=2)+'\n');package(m,r)
    # Promote only after picture, audio and provenance gates are complete.
    dest=D/EXPORT;shutil.copyfile(p,dest.with_suffix('.building.mp4'));dest.with_suffix('.building.mp4').replace(dest)
    print(json.dumps(r,indent=2));print('V2_REVIEW_READY')


if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('--opening-test',action='store_true');z=cli.parse_args()
    if z.opening_test:
        a=setup();frames=a['chapters'][1][0];a['frames']=frames;out=W/'opening-timing-test.mp4'
        mux(W/'chapter-renders/chapter-1.mp4',W/'mix-v2.wav',out,frames*(SR//a['fps']))
        print(json.dumps(check_picture(out,a),indent=2));print('opening audio samples:',len(decode(out,2)),'expected:',frames*(SR//a['fps']))
    else:build()
