#!/usr/bin/env python3
"""Build the score/FX bed, extract the approved-length captions, and mux the minute.

VO is copied from timeline zero at unity into both channels; the signal under it
is independent and ducked, never the reverse. No resampling, EQ, new take, time
stretch, or limiter affects the original narration.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import wave

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import butter, sosfilt

from picture import CACHE, CLOCK, END, FF, FPS, FRAMES, HERE, hashfile, part_dir
from prepare_terrain import ROOT, OUT

TITLE='Why These Dinosaur Footprints Are an Ocean Apart'
STEM='Extinct-Life-Atlantic-Tracks-Opening-3D'
INPUT=ROOT/'deliverables/extinct-life-step-3'
VOICE=INPUT/'Extinct-Life-Atlantic-Tracks-VO-v2.wav'
SRT=INPUT/'Extinct-Life-Atlantic-Tracks-VO-v2.en.srt'
CC=OUT/f'{STEM}.en.srt'
MOVIE=OUT/f'{STEM}.mp4'
LOCK=HERE.parent/'step-3/vo-v2-receipt.json'
AUDIO=CACHE/'audio'; BED=AUDIO/'bed.wav'; MIX=AUDIO/'mix.wav'
NSAMPLES=FRAMES[-1]*CLOCK//FPS
Q=2**23


def timebase(n):return np.arange(n,dtype=np.float32)/CLOCK


def shaped(x):
    z=np.clip(x,0,1);return z*z*(3-2*z)


def gate(t,d,a=.2,b=.3):return shaped(t/a)*shaped((d-t)/b)


def hz(midi):return 440*2**((midi-69)/12)


def levels(x):return 20*np.log10(np.maximum(np.sqrt(np.mean(x*x,axis=0,dtype=np.float64)),1e-12))


def int_samples(p,count):
    with wave.open(str(p),'rb') as w:
        assert w.getframerate()==CLOCK and w.getsampwidth()==3 and w.getnframes()>=count
        ch=w.getnchannels();a=np.frombuffer(w.readframes(count),dtype=np.uint8).reshape(-1,ch,3).astype(np.int32)
    upper=a[:,:,2]-256*(a[:,:,2]>=128)
    return a[:,:,0]+(a[:,:,1]<<8)+(upper<<16)


def write24(p,s):
    assert s.ndim==2 and s.shape[1] in (1,2) and np.max(np.abs(s))<Q
    b=np.stack([s&255,(s>>8)&255,(s>>16)&255],axis=-1).astype(np.uint8)
    with wave.open(str(p),'wb') as w:
        w.setnchannels(s.shape[1]);w.setsampwidth(3);w.setframerate(CLOCK);w.writeframes(b.tobytes())


def locked():
    lock=json.loads(LOCK.read_text())
    for f in lock['files']:
        checked=INPUT/f['file']
        assert checked.stat().st_size==f['size'] and hashfile(checked)==f['sha256'],f['file']
    return lock


def cc_time(s):
    h,m,t,ms=map(int,re.split('[:,]',s))
    return ((h*60+m)*60+t)*1000+ms


def captions():
    """Complete cue boundaries only; do not retime or paraphrase the locked take."""
    q=SRT.read_text().strip().split('\n\n')
    cues=[]
    for block in q:
        _,clock,*lines=block.splitlines()
        start,stop=map(cc_time,clock.split(' --> '))
        if stop<=int(END*1000):
            assert int(block.splitlines()[0])==len(cues)+1 and start<stop and 1<=len(lines)<=2
            cues.append(block)
    assert q[:18]==cues and 'was moving on that patch of ground.' in cues[-1] and 'Once the prints stop' not in '\n'.join(cues)
    CC.write_text('\n\n'.join(cues)+'\n',encoding='utf-8')
    return cues


class Score:
    def __init__(self):
        self.music=np.zeros((NSAMPLES,2),np.float32)
        self.fx=np.zeros_like(self.music)
        self.r=np.random.default_rng(81761337)

    def time(self,at,dur):
        origin=round(at*CLOCK); stop=min(NSAMPLES,origin+round(dur*CLOCK))
        assert origin>=0 and stop>origin
        return slice(origin,stop),timebase(stop-origin)

    def add(self,which,idx,w,pan):
        assert -1<=pan<=1
        p=(pan+1)*math.pi/4
        which[idx,0]+=w*math.cos(p);which[idx,1]+=w*math.sin(p)

    def noise(self,t,lo,hi):
        x=self.r.standard_normal(t.size,dtype=np.float32)
        x=sosfilt(butter(2,(lo,hi),btype='bandpass',fs=CLOCK,output='sos'),x).astype(np.float32)
        return x/max(1e-7,float(np.sqrt(np.mean(x*x))))

    def pad(self,at,d,note,amp,pan,attack,tail):
        region,t=self.time(at,d); f=hz(note); phase=2*np.pi*f*t
        p=self.r.uniform(0,2*np.pi,4)
        bow=np.sin(phase+.39*np.sin(2*np.pi*.37*t+p[0])+p[1])
        bow+=.29*np.sin(2.003*phase+.66*np.sin(2*np.pi*.26*t)+p[2])
        bow+=.105*np.sin(3.002*phase+.48*np.sin(2*np.pi*.43*t)+p[3])
        bow+=.075*np.sin(.9991*phase-p[2])
        w=bow*amp*gate(t,d,attack,tail)*(.80+.16*np.sin(2*np.pi*.19*t+p[0])+.04*np.sin(t*2.51+p[1]))
        self.add(self.music,region,w,pan)

    def bell(self,at,note,amp,pan,d=3.2):
        region,t=self.time(at,d); p=2*np.pi*hz(note)*t
        ring=np.sin(p)*np.exp(-t*1.45)+.29*np.sin(2.007*p+.1)*np.exp(-t*2.4)+.16*np.sin(3.96*p)*np.exp(-t*9.)
        self.add(self.music,region,ring*amp*gate(t,d,.023,.71),pan)

    def grit(self,at,d,amp,pan,lo,hi,a=.017,b=.24):
        region,t=self.time(at,d); grain=self.noise(t,lo,hi)
        if hi>900:grain*=.71+.29*np.cos(t*49)*np.cos(t*21.1)
        self.add(self.fx,region,grain*(amp*gate(t,d,a,b)),pan)

    def whoosh(self,at,d,amp,up=True):
        region,t=self.time(at,d)
        m=shaped(t/d); sub=t*(46+(27*m if up else -12*m))
        low=self.noise(t,34,410);shimmer=self.noise(t,572,3020)
        contour=gate(t,d,d*(.66 if up else .18),d*(.2 if up else .81))
        w=amp*contour*(.7*low+.35*shimmer*(.17+.58*m)+.96*np.sin(2*np.pi*sub))
        pan=(-.55+1.10*m) if up else (.38-.58*m)
        self.fx[region,0]+=w*np.cos((pan+1)*math.pi/4);self.fx[region,1]+=w*np.sin((pan+1)*math.pi/4)

    def bump(self,at,amp,pan,d=.62):
        region,t=self.time(at,d)
        env=gate(t,d,.012,min(.25,d*.5))
        thud=np.sin(2*np.pi*(61*t-25*t*t))*np.exp(-10.3*t)+.44*self.noise(t,47,310)*np.exp(-11.1*t)
        self.add(self.fx,region,thud*env*amp,pan)

    def create(self):
        # A sparse suspended tonic opens to a warmer chord on the title cut; no
        # relentless rhythm underneath words. Release on the last whole sentence.
        cues=[(0.,6.7,[38,50,57],.0082,2.0),(4.2,7.5,[34,50,57,60],.0068,1.4),
              (10.89,9.6,[36,48,55,62],.0076,1.24),(18.88,8.2,[38,53,57,64],.0091,1.30),
              (26.2,7.9,[34,50,53,57],.0064,1.2),(32.4,6.1,[36,48,55,57],.0060,1.1),
              (36.96,9.8,[41,53,60,65],.0077,1.7),(43.1,6.9,[38,50,55,60],.0064,1.4),
              (49.1,6.0,[34,46,53,60],.0066,1.4),(53.26,7.5,[38,50,57,62],.0079,1.6)]
        for at,d,notes,amp,attack in cues:
            for j,n in enumerate(notes):
                self.pad(at+j*.045,d-j*.045,n,amp*(1 if j==0 else .75),(.08,-.48,.48,-.20)[j],attack+.11*j,1.17+(.19*j))
        for at,n,a,p in [(2.64,62,.0075,-.23),(5.08,69,.0077,.26),(6.29,65,.0069,-.31),(11.46,64,.0090,.27),
                         (15.58,62,.0089,-.20),(19.64,57,.0132,-.40),(20.32,65,.0101,.46),(22.12,69,.0077,-.30),
                         (27.6,62,.0061,.21),(32.72,60,.0069,-.30),(43.46,57,.0063,.39),(52.85,62,.0060,-.39),
                         (56.86,65,.0054,.16),(57.43,62,.0048,-.21),(58.23,57,.0058,.23)]:
            self.bell(at,n,a,p)
        for dt,g in [(2119,.09),(7127,.055),(12377,.018)]:
            self.music[dt:,0]+=g*self.music[:-dt,1];self.music[dt:,1]+=g*self.music[:-dt,0]

        # Close perspective: soft grit and rim texture. Space widens on the orbit.
        self.grit(0,4.21,.0044,-.46,225,1100,.31,.60)
        self.grit(.16,.52,.0036,.35,700,4200,.16,.26)
        self.grit(2.58,.86,.0075,.26,440,2450,.15,.52)
        self.whoosh(3.83,1.14,.0123)
        self.grit(4.18,5.81,.0037,.26,73,485,.65,.87)
        self.whoosh(9.61,1.93,.0243)
        self.bump(10.89,.020,.02,1.14)
        self.whoosh(11.07,1.37,.0101,False)
        self.grit(13.25,5.98,.0028,-.27,89,509,.89,1.21)
        self.bump(19.59,.023,.02,.79)
        self.grit(19.49,6.76,.0046,-.39,91,511,.81,1.06)
        for pan in (-.59,.64):
            self.grit(20.03,5.86,.0048,pan,432,1920,1.2,1.25)
        self.whoosh(25.83,1.27,.0103)
        self.whoosh(31.08,.94,.0086,False)
        self.grit(31.80,4.54,.0043,-.32,362,1610,.68,.67)
        self.bump(32.73,.0102,.34,.40)
        for pan in (-.66,.62):
            self.grit(36.1,7.38,.0058,pan,343,1687,.59,.67)
            self.grit(36.0,7.32,.0050,pan*.77,69,439,.69,.77)
        self.grit(43.22,1.1,.0062,.44,506,2640,.11,.72)
        self.whoosh(48.36,1.01,.0083,False)
        self.bump(49.31,.0336,.02,.69)
        self.grit(49.30,.65,.0109,.19,212,1415,.019,.47)
        self.grit(49.42,.58,.0062,-.34,776,3230,.049,.38)
        self.grit(50.18,.97,.0083,.14,461,2268,.17,.64)
        self.grit(52.79,.44,.0037,-.32,447,3005,.085,.28)
        for i,t in enumerate((56.70,57.04,57.38,57.72,58.06)):
            self.bump(t,.006 if i%2 else .0078,(-1 if i%2 else 1)*.57,.33)
        return self.music,self.fx


def audio():
    v=locked(); track=int_samples(VOICE,NSAMPLES)
    assert track.shape==(NSAMPLES,1)
    # Final out is in the measured gap after 'ground', before 'Once'.
    a=track[round(60.535*CLOCK):NSAMPLES-32,0].astype(np.float64)/Q
    assert float(levels(a)) < -73, float(levels(a))
    dry=track.astype(np.float32)/Q
    m,fx=Score().create()
    amp=np.sqrt(np.mean(dry.reshape(-1,200)**2,axis=1))
    meter=gaussian_filter1d(amp,11.)
    duck=(1-.41*shaped((np.repeat(meter,200).reshape(-1,1)-.009)/.096))
    t=timebase(NSAMPLES); fade=(shaped(t/.14)*shaped((END-t)/.41)).reshape(-1,1)
    bed=(m+fx)*duck*fade
    pcm=np.rint(bed*Q).astype(np.int32)
    mix=pcm+track
    assert np.max(np.abs(mix))/Q<.883
    AUDIO.mkdir(parents=True,exist_ok=True)
    write24(BED,pcm);write24(MIX,mix)
    report={'duration':END,'voice_source_sha256':v['files'][0]['sha256'],'frames_48k':NSAMPLES,
            'source_gain_db':0.0,'voice_untouched_in_stereo_mix':True,'music_and_fx':'Original synthesized score and spot effects; no sampled music, reuse of reference audio, or stem extraction.',
            'bed_to_voice_rms_db':np.round(levels(bed)-levels(dry),3).tolist(),
            'linear_mix_peak_dbfs':round(float(20*np.log10(np.max(np.abs(mix))/Q)),3),'bed_peak_dbfs':round(float(20*np.log10(np.max(np.abs(bed)))),3),
            'samples_near_edit_rms_dbfs':round(float(levels(a)),3),'mix_sha256':hashfile(MIX),'bed_sha256':hashfile(BED)}
    (AUDIO/'mix.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


def mux(concat=None,output=MOVIE):
    f=concat or part_dir()/'concat.ffconcat'
    if not f.is_file():raise FileNotFoundError(f'Picture must finish before mux: {f}')
    cc=captions();assert cc and MIX.is_file()
    credits=('Adapted geographic model: Kocsis & Scotese (2021), PaleoCoastlines v7.1 and PALEOMAP rotations; '
             'https://doi.org/10.1016/j.earscirev.2020.103463. Scotese & Wright (2018), PALEOMAP PaleoDEMs v2; '
             'https://doi.org/10.5281/zenodo.5460860. Both CC BY 4.0, https://creativecommons.org/licenses/by/4.0/. '
             'Sampled and shaded; relief exaggerated. Modern coast: Natural Earth, modern elevation: NOAA NGDC ETOPO5 (public domain). '
             '125 Ma is a model snapshot, not a date assigned to the footprints. Local geology and trackmarks are original illustrations.')
    tmp=output.with_suffix('.pending.mp4')
    args=[FF,'-hide_banner','-loglevel','warning','-nostdin','-y','-safe','0','-f','concat','-i',str(f),'-i',str(MIX),'-f','srt','-i',str(CC),
          '-map','0:v:0','-map','1:a:0','-map','2:s:0','-c:v','copy','-bsf:v',f'setts=pts=N*2000:dts=N*2000:duration=2000:time_base=1/{CLOCK}',
          '-c:a','aac','-profile:a','aac_low','-b:a','256k','-ar',str(CLOCK),'-c:s','mov_text','-disposition:s:0','0',
          '-metadata:s:a:0','language=eng','-metadata:s:s:0','language=eng','-metadata:s:s:0','handler_name=English',
          '-map_metadata','-1','-map_chapters','-1','-metadata',f'title={TITLE} — 3D opening review','-metadata',f'comment={credits}',
          '-movflags','+faststart','-video_track_timescale',str(CLOCK),'-movie_timescale',str(CLOCK),str(tmp)]
    subprocess.run(args,check=True)
    assert 0<tmp.stat().st_size<100_000_000
    tmp.replace(output)
    print(f'MUX_READY: {output} | {output.stat().st_size:,} bytes | {hashfile(output)}',flush=True)


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--audio-only',action='store_true')
    a=cli.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    audio();captions()
    if not a.audio_only:mux()


if __name__=='__main__':main()
