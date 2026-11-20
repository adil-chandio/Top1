#!/usr/bin/env python3
"""Render (or sample) the v2 voice-led review cut. No TTS or final mixing.

Dependencies: Python 3.11+, Pillow, scipy, numpy, pyshp, imageio-ffmpeg 0.6.
See asset-lock.json, ../step-2/map-sources.json and README.md for inputs.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import wave

import imageio_ffmpeg
from PIL import Image, ImageDraw

from artwork import Art, CACHE, ROOT, HERE, SIZE
from timeline import END, FPS, SHOTS, frames

FF = imageio_ffmpeg.get_ffmpeg_exe()
WORK = CACHE/'animatic'
OUT = ROOT/'deliverables/extinct-life-step-4'
VO = ROOT/'deliverables/extinct-life-step-3'
STEM = 'Extinct-Life-Atlantic-Tracks-Animatic-v1'
WAV = VO/'Extinct-Life-Atlantic-Tracks-VO-v2.wav'
SRT = VO/'Extinct-Life-Atlantic-Tracks-VO-v2.en.srt'
RECEIPT = HERE.parent/'step-3/vo-v2-receipt.json'
CLOCK = 48000
ASSETS = HERE/'asset-lock.json'

# Stable frames are encoded from a single image. Short animated passages
# re-render only where a parameter (light, level, position, etc.) changes.
STATES = {
    ('map','open'): (2.645,6.225), ('map','rewind'): (15.395,), ('map','possible'): (345.829,),
    ('map','back'): (415.1,), ('title',''): (24.485,),
    ('imprint','count'): (45.538,), ('imprint','ruler'): (102.107,), ('imprint','rim'): (230.718,),
    ('imprint','end'): (433.419,), ('imprint','fade'): ((177.458,180.608),),
    ('tracks','way'): (48.078,48.778,49.478,50.178,50.878,52.778), ('tracks','stop'): (60.728,),
    ('stack','four'): ((65.3,68.4),), ('stack','erosion'): ((77.718,79.818),),
    ('scan','views'): (84.158,84.998,85.838,87.838), ('scan','relief'): ((90.518,92.918),),
    ('stamp','press'): ((122.257,125.117),126.077,128.147),
    ('textures','marks'): (157.688,160.828), ('bed','drain'): ((168.9,172.6),172.778), ('bed','bury'): ((202.968,205.968),),
    ('micro','cement'): (189.858,), ('fault','sink'): ((312.463,315.563),(316.363,319.163)),
    ('fault','stages'): (402.879,405.759,408.28), ('fish','intro'): (362.5,),
    ('network','generations'): (349.1,351.25,353.4), ('network','test'): (376.789,377.439,377.989),
    ('network','better'): (384.019,386.15,387.7),
}


def sha(file):
    with file.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def inputs(args):
    r=json.loads(RECEIPT.read_text())
    official=HERE.parent/'step-2/Extinct-Life-Atlantic-Tracks-Script-v2.md'
    assert sha(official) in (r['script_sha256'],r.get('repository_script_sha256'))
    expected={f['file']: f for f in r['files']}
    for f in (WAV,SRT):
        assert f.stat().st_size==expected[f.name]['size'] and sha(f)==expected[f.name]['sha256']
    with wave.open(str(WAV),'rb') as f:
        assert f.getnframes()==r['sample_frames'] and (f.getframerate(),f.getnchannels(),f.getsampwidth())==(CLOCK,1,3)
    assert r['duration_seconds']==r['sample_frames']/CLOCK
    asset=json.loads(ASSETS.read_text())
    for key,path in (('art',args.art),('fonts',args.fonts)):
        for f in asset[key]:
            assert sha(path/f['file'])==f['sha256'],f['file']
    f=frames()
    assert len(f)==len(SHOTS)+1 and all(x<y for x,y in zip(f,f[1:])) and f[0]==0
    assert abs(f[1]/FPS-r['opening_rewind_estimate_s'])<1/FPS
    assert f[-2]/FPS >= r['duration_seconds'] and f[-2]/FPS-r['duration_seconds']<1/FPS
    assert f[-1]-f[-2] == round(6.5*FPS)
    return r,Art(args.sources,args.art,args.fonts)


def fmt(seconds):
    ms=round(seconds*1000)
    mm,tail=divmod(ms,60000); ss,ms=divmod(tail,1000)
    return f'{mm:02d}:{ss:02d}.{ms:03d}'


def section_for(v,seconds):
    # Use rounded boundaries so first frames of a scene get its section mark.
    ticks = [round(s['edit_in']*FPS) for s in v['scenes']]
    return bisect_right(ticks,round(seconds*FPS))


def still(art,v,k,t):
    s=SHOTS[k]
    return art.frame(s,t,section_for(v,t),(SHOTS[k+1].at if k+1<len(SHOTS) else END))


def proof(path,v,art):
    path.mkdir(parents=True,exist_ok=True)
    timing=frames()
    viewed = [.10,4.1,6.52,10.33,15.6,22,30,39,46.0,53.2,61.2,70.2,
              80.2,88.7,92.25,104,117,124.6,129.55,134.2,139,146,153,161.4,166,173,181.9,
              190,198,207,213,216,220,225,232,237,244,256,265,272,276,284,292,297,303,309,318,324,
              330,337,346.3,354,364,371,380,388.5,397,411,416,421,425,436,441]
    assert all(isinstance(x,(float,int)) and x<END for x in viewed)
    index = sorted(set(bisect_right(timing,round(t*FPS))-1 for t in viewed))
    print(f'Proof samples: {len(viewed)} frames in {len(index)} of {len(SHOTS)} shots',flush=True)
    for offset in range(0,len(viewed),12):
        samples=viewed[offset:offset+12]
        sheet=Image.new('RGB',(1152,240*((len(samples)+2)//3)),(10,16,21))
        d=ImageDraw.Draw(sheet)
        for i,t in enumerate(samples):
            k=bisect_right(timing,round(t*FPS))-1
            im=still(art,v,k,t)
            pos=(384*(i%3),240*(i//3))
            sheet.paste(im.resize((384,216),Image.Resampling.LANCZOS),pos)
            d.text((pos[0]+10,pos[1]+220),f'{k+1:02d}  {fmt(t)}  {SHOTS[k].style} / {SHOTS[k].variant}',fill='#e0e8de')
        sheet.save(path/f'stills-{offset//12+1:02d}.jpg',quality=90)


def render_key(s,t):
    if s.style=='photo':
        return t
    modes=[]
    for change in STATES.get((s.style,s.variant),()):
        if isinstance(change,tuple):
            a,b=change
            if a<=t<b:
                return t
            modes.append(t>=b)
        else:
            modes.append(t>=change)
    return tuple(modes)


def encode_shot(clip, v, art, k, lo, hi):
    shot=SHOTS[k]
    count=hi-lo
    first=lo/FPS
    final=(hi-1)/FPS
    tmp=clip.with_suffix('.tmp.mp4')
    cmd=[FF,'-hide_banner','-loglevel','error','-nostdin','-y']
    # Coherent colour conversion and a shared video clock for stream-copy concat.
    opts=['-an','-frames:v',str(count),'-c:v','libx264','-threads','2','-preset','veryfast',
          '-pix_fmt','yuv420p','-profile:v','high','-crf','19.5','-maxrate','1540k','-bufsize','2400k',
          '-g','48','-keyint_min','24','-bf','0','-color_range','tv','-colorspace','bt709',
          '-color_primaries','bt709','-color_trc','bt709','-video_track_timescale',str(CLOCK),
          '-movie_timescale',str(CLOCK),str(tmp)]
    cvt='scale=out_color_matrix=bt709:out_range=tv,format=yuv420p'
    keys=[render_key(shot,i/FPS) for i in range(lo,hi)]
    if keys.count(keys[0])==count:
        png=clip.with_suffix('.png')
        still(art,v,k,first).save(png,compress_level=2)
        subprocess.run([*cmd,'-framerate',str(FPS),'-i',str(png),'-filter_threads','1',
                        '-vf',f'{cvt},loop=loop={count-1}:size=1',*opts],check=True)
        png.unlink()
    else:
        p=subprocess.Popen([*cmd,'-f','rawvideo','-pixel_format','rgb24','-video_size',f'{SIZE[0]}x{SIZE[1]}',
                            '-r',str(FPS),'-i','-','-filter_threads','1','-vf',cvt,*opts],stdin=subprocess.PIPE)
        before=None
        assert p.stdin is not None
        try:
            for j,frame in enumerate(range(lo,hi)):
                key=keys[j]
                if key!=before:
                    data=still(art,v,k,frame/FPS).tobytes()
                    before=key
                p.stdin.write(data)
            p.stdin.close()
            assert p.wait()==0,clip
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()
    tmp.replace(clip)


def encode(v,art,args):
    frame_list=frames()
    h=hashlib.sha256()
    for p in (HERE/'artwork.py', HERE/'timeline.py', Path(__file__), ASSETS,RECEIPT):
        h.update(p.read_bytes())
    parts=args.work/('video-'+h.hexdigest()[:14]); parts.mkdir(parents=True,exist_ok=True)
    pattern=['ffconcat version 1.0']
    for i,(lo,hi) in enumerate(zip(frame_list,frame_list[1:])):
        path=parts/f'{i+1:02d}.mp4'
        if not path.exists():
            t0=time.monotonic()
            encode_shot(path,v,art,i,lo,hi)
            print(f'Shot {i+1:02d}/{len(SHOTS)} | {fmt(lo/FPS)} | {SHOTS[i].style}/{SHOTS[i].variant} | {time.monotonic()-t0:.1f}s',flush=True)
        pattern.extend((f"file '{path.name}'",f'duration {(hi-lo)/FPS:.9f}'))
    concat=parts/'concat.ffconcat'
    concat.write_text('\n'.join(pattern)+'\n')
    return mux(concat,args.out)


def mux(concat, out):
    frame_list=frames()
    out.mkdir(parents=True,exist_ok=True)
    movie=out/f'{STEM}.mp4'
    tmp=movie.with_suffix('.tmp.mp4')
    tick=CLOCK//FPS
    n=frame_list[-1]*tick
    # The concat protocol expresses segment durations in integer microseconds.
    # Rewrite the B-frame-free video packet clock, not the PCM clock, to eliminate
    # at-most-one-tick rounding at picture cuts. No video re-encoding here.
    ts=f'setts=pts=N*{tick}:dts=N*{tick}:duration={tick}:time_base=1/{CLOCK}'
    subprocess.run([FF,'-hide_banner','-loglevel','error','-nostdin','-y','-f','concat','-safe','0','-i',str(concat),
                    '-i',str(WAV),'-i',str(SRT),'-map','0:v:0','-map','1:a:0','-map','2:s:0',
                    '-c:v','copy','-bsf:v',ts,'-c:a','aac','-b:a','144k','-af',f'apad=whole_len={n}',
                    '-c:s','mov_text','-metadata:s:s:0','language=eng','-metadata:s:s:0','handler_name=English (VO v2)',
                    '-disposition:s:0','0','-metadata','title=Why These Dinosaur Footprints Are an Ocean Apart — Animatic',
                    '-metadata','comment=Review cut; unretimed VO v2; no music or effects. See shot handoff for sources.',
                    '-video_track_timescale',str(CLOCK),'-movie_timescale',str(CLOCK),'-movflags','+faststart',str(tmp)],check=True)
    assert tmp.stat().st_size<100_000_000, 'Drive staging cap'
    tmp.replace(movie)
    print(f'Exported {movie} • {fmt(frame_list[-1]/FPS)} • {movie.stat().st_size:,} bytes',flush=True)
    return movie


def handoff(v,movie,out):
    f=frames()
    content=[
        '# Why These Dinosaur Footprints Are an Ocean Apart', '',
        '**Extinct Life · Atlantic Tracks · first animatic / VO v2**', '',
        f'**{fmt(f[-1]/FPS)}** at 1920×1080, {FPS} fps. Same {fmt(v["duration_seconds"])} English narration from time zero; '
        'the only extra time is an end source card and frame rounding. Narration only, no score or sound effects. '
        'Selectable English subtitles are embedded; use the existing v2 SRT in the edit.', '',
        'Script v2 · '
        'VO v2 · '
        'English SRT v2 · '
        'Voice timing', '',
        '## Watch these moments', '',
        f'- **{fmt(f[1]/FPS)}** map rewind, followed by the on-land distance estimate; title after the reveal.',
        '- **01:04.558** four distinct track-bearing surfaces; **01:27.838** overlapping photographs; **01:42.107** ≈69 cm is the print length.',
        '- **05:45.829** the proposed dispersal area, then **05:57.009** the separate fish evidence. No measured route or witnessed crossing.',
        '- **07:03.739** “The rocks.” Keep both region pins distinct for the last reveal.', '',
        '## Cut list', '',
        'Frame-rounded edit intervals, start inclusive and end exclusive. The editorial notes may include a line-aligned event within the shot.', '',
        '| # | Picture in–out | Image | What to hold or change in final picture |', '|---:|:---|:---|:---|',
    ]
    for k,(s,a,b) in enumerate(zip(SHOTS,f,f[1:]),1):
        content.append(f'| {k:02d} | {fmt(a/FPS)}–{fmt(b/FPS)} | {s.heading.replace(chr(10)," ")} | {s.edit} |')
    content += [
        '', '## Source and production boundaries', '',
        '- Present-day coastline: [Natural Earth 1:110m land, v5.1.2](https://www.naturalearthdata.com/about/terms-of-use/), public domain, cropped and styled.',
        '- Ancient coastline: Kocsis & Scotese (2021), [PaleoCoastlines v7.1, 125 Ma](https://doi.org/10.1016/j.earscirev.2020.103463), '
        '[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); cropped, recolored and annotated. The 125 Ma panel is a model, not a footprint date. '
        'Markers denote regions. Approximate separation labels are study summaries, not distances travelled.',
        '- Distances, structures and proposed dispersal: [Jacobs et al. (2024), Bulletin 95, pp. 199–212](https://igeo.ufrj.br/inc/isc/3/03_139_Jacobs%20etal.pdf). '
        'The fish evidence comes from other basins; not a fossil found in either set of footprints.',
        '- Four surfaces, the 283/34 inventory, TK-034 and sedimentology: [Menkem et al. (2026)](https://doi.org/10.1016/j.jop.2026.100416). '
        'Original explanation diagrams, no reused paper plates or model.',
        '- Sousa preservation interpretation: [Carvalho, Borghi & Leonardi (2013)](https://doi.org/10.1016/j.cretres.2013.04.004). '
        'Separate basin, no matched animal or identical date claimed.',
        '- All fossil outlines, sections and texture panels here are original schematics. The three landscape plates are AI illustrations (generalized riverbed, riverbank and ancient valley), not field footage, survey imagery, or exact reconstructions. Fraunces and IBM Plex fonts: SIL Open Font License 1.1.',
        '- Rough picture review only. Listen-check the place and animal names in VO v2, especially Sousa, before picture lock. No public release. Leave v1 VO and its SRT in the archive.', '',
        f'**Review file:** `{movie.name}` · SHA-256 `{sha(movie)}`', '',
    ]
    (out/f'{STEM}-Shot-Handoff.md').write_text('\n'.join(content))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--proof',action='store_true')
    p.add_argument('--sources',type=Path,default=CACHE/'sources')
    p.add_argument('--art',type=Path,default=OUT/'illustration-sources')
    p.add_argument('--fonts',type=Path,default=WORK/'fonts')
    p.add_argument('--out',type=Path,default=OUT)
    p.add_argument('--work',type=Path,default=WORK)
    a=p.parse_args()
    v,art=inputs(a)
    if a.proof:
        proof(a.work/'proof',v,art)
    else:
        movie=encode(v,art,a)
        handoff(v,movie,a.out)


if __name__=='__main__':
    main()
