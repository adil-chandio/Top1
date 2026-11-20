#!/usr/bin/env python3
"""Conform the new picture to the exact Sound Redesign AAC, text, and chapters."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image, ImageDraw

from render import CACHE, EDITED, OUT, QA, RETAINED, part, stamp
import finish_film as full
import finish_sound_v2 as red
from cut import B, BY, F, FPS, N, S, SR

NAME='Extinct-Life-Atlantic-Tracks-Investigation-Cut'
MOVIE=OUT/f'{NAME}.mp4'; CAPTIONS=OUT/f'{NAME}.en.srt'; NOTES=OUT/f'{NAME}-Handoff.md'
RECEIPT=Path(__file__).with_name('investigation-receipt.json')
LOOKS=(
    ('00:00–00:26','Same-scale prints share the frame. One atlas view measures the modern Atlantic gap, then reveals the independent 125 Ma model. The title rides the landscape reveal instead of holding the sequence.'),
    ('01:01–01:36','Separate walking surfaces, a breaking edge, and simulated overlapping camera views resolve into an illustrative 3D mesh of what remains.'),
    ('02:01–02:16','Two identical three-toed stamps hit together. Watch the shallow, firmer edge stay defined as the wall on the wetter side collapses after release.'),
    ('02:49–03:34','The original water retreat and exposure give way to grain contacts, possible microbial binding and a cutaway of new sediment sealing the marked surface.'),
    ('04:01–04:55','Matching riverbanks do not prove a shared river. Turn the comparison sideways: separate deposits, a regional pollen clue, and broad, unresolved age windows.'),
    ('05:57–06:35','The coelacanth comes toward camera before a life-to-fossil match cut. Fragments from other basins add an independent test, not a traced river. Three shorter illustrations distinguish possible future tests from discoveries.'),
    ('06:45–07:19','The basin stretches and floods. We revisit the present gap and the two prints. The final schematic holds each impression to its own bed as the underlying blocks separate, then cuts back to the opening print.'),
)
ACTIONS=('edge-chip','erosion-pop','erosion-tail','scan-read','scan-side','photos','reconstruction','length','test-down','test-up','slump','firm-soft',
    'drain','impact-bank','erosion-wash','cement','mat','bury','seal','pollen','age','fault-light','rift-down','rift-fill','valley-water',
    'mawsonia','other-basins','more-sites','better-dates','better-fossils','rift-early','rift-late','gap-returns','rocks-answer','gentle-close')
SHEETS=(
    ('opening-and-answer',(0,47,95,170,257,394,513,10000,10122,10174,10231,10316)),
    ('mud-impacts',(2943,2975,2981,2986,3016,3089,3093,3103,3117,3129,3151,3210)),
    ('dating-test',(5858,6048,6227,6375,6546,6642,6778,6865,6932,6980,7039,7134)),
    ('erosion-and-grains',(1863,1870,1899,2007,2130,2259,4106,4268,4544,4761,4946,4982)),
    ('fish-and-rift',(8586,8726,8780,8865,9106,9247,9341,9422,9729,9812,9837,9884)),
)


def preflight():
    ref=json.loads(red.RECEIPT.read_text(encoding='utf-8'));record=ref['files'][0]
    assert full.file_record(red.MOVIE)==record,'Incorrect Sound Redesign video lock'
    assert full.file_record(red.CAPTIONS)==ref['files'][1],'Incorrect English caption lock'
    assert ref['frames']==ref['decoded_video_frames']==F[-1] and ref['fps']==FPS
    assert ref['chapters']==full.chapters() and ref['audio']['all_offsets_samples']==[0]
    return ref


def select_parts(initial=None,redone=()):
    initial=initial or stamp();current=stamp()
    if set(redone)-set(EDITED):raise ValueError('Only revised shots can be amended')
    if initial==current and redone:raise ValueError('Amendment does not identify a separate render pass')
    x=['ffconcat version 1.0'];parts=[]
    for k in range(len(S)):
        p=part(k);a,b=F[k:k+2];digest=full.base.hashfile(p);n=p.stat().st_size
        if k in EDITED:
            q=json.loads(p.with_suffix('.json').read_text());version=current if k in redone else initial
            assert (q['from_frame'],q['to_frame_exclusive'],q['frames'],q['sha256'],q['bytes'],q['rev'])==(a,b,b-a,digest,n,version),('shot not pinned to the selected pass',k)
        parts.append({'shot':k,'key':S[k].key,'from_frame':a,'to_frame_exclusive':b,'bytes':n,'sha256':digest,
                      'pass':('refinement' if k in redone else 'rebuild') if k in EDITED else 'retained'})
        spec=str(p.resolve()).replace("'","'\\''")
        x += [f"file '{spec}'",f'duration {(b-a)/FPS:.12f}']
    m=CACHE/'picture-lock.ffconcat';m.write_text('\n'.join(x)+'\n')
    return m,parts,{'initial':initial,'current':current,'amended_shots':list(redone)}


def mux(manifest,target,ref):
    full.run(['-loglevel','error','-xerror','-y','-f','concat','-safe','0','-i',str(manifest),'-i',str(red.MOVIE),
      '-map','0:v:0','-map','1:a:0','-map','1:s:0','-map_metadata','1','-map_chapters','1','-c','copy','-disposition:s:0','0',
      '-metadata',f'title={full.TITLE} | Investigation Cut',
      *[v for i,c in enumerate(ref['chapters']) for v in (f'-metadata:c:{i}',f"title={c['title']}")],
      '-movflags','+faststart','-write_btrt','0','-video_track_timescale',str(SR),'-movie_timescale',str(SR),str(target)],180)
    print('INVESTIGATION_MUXED',target.stat().st_size,flush=True)


def aac_packet_log(p):
    buf,_=full.run(['-loglevel','error','-xerror','-i',str(p),'-map','0:a:0','-c','copy','-f','framehash','-hash','sha256','-'],90)
    return {'sample_log_sha256':sha256(buf).hexdigest(),'media_packet_count':sum(not r.startswith(b'#') for r in buf.splitlines() if r)}


def decoded_audio(p):
    buf,_=full.run(['-loglevel','error','-xerror','-i',str(p),'-map','0:a:0','-c:a','pcm_f32le','-f','hash','-hash','sha256','-'],90)
    return buf.decode().strip().split('=',1)[1]


def decode_samples(p,frames,size=(448,252)):
    marks='+'.join(f'eq(n,{f})' for f in frames);w,h=size
    data,_=full.run(['-loglevel','error','-xerror','-err_detect','explode','-threads','2','-i',str(p),'-map','0:v:0','-an','-sn','-dn',
        '-filter_threads','1','-vf',f"select='{marks}',scale={w}:{h}:flags=bicubic:in_color_matrix=bt709:out_range=pc,format=rgb24",
        '-fps_mode','passthrough','-threads','1','-f','rawvideo','-'],300)
    assert len(data)==len(frames)*h*w*3,(p,len(data),len(frames))
    return dict(zip(frames,np.frombuffer(data,dtype=np.uint8).reshape(len(frames),h,w,3),strict=True))


def visual_audit(movie):
    refs={k:[F[k]+6,(F[k]+F[k+1])//2,F[k+1]-2] for k in range(len(S))}
    sample=sorted({f for rr in refs.values() for f in rr}|{f for _,rr in SHEETS for f in rr}|
                  {int(np.clip(BY[name].f+j,0,F[-1]-1)) for name in ACTIONS for j in (-3,0,8,20)})
    pics=decode_samples(movie,sample)
    archived=decode_samples(red.MOVIE,sorted({f for rr in refs.values() for f in rr}))
    edits={}
    for k,frames in refs.items():
        delta=[round(float(np.mean(np.abs(pics[f].astype('int16')-archived[f].astype('int16')))),3) for f in frames]
        if k in RETAINED:assert all(np.array_equal(pics[f],archived[f]) for f in frames),(k,delta)
        else:assert min(delta)>2,(k,delta)
        edits[str(k)]={'key':S[k].key,'baseline_probe_rgb_mae':delta,'frames':frames}
    for name,rr in SHEETS:
        w,h=448,252;gap=8;sheet=Image.new('RGB',(3*(w+gap)+gap,4*(h+38)+gap),(13,22,29));pen=ImageDraw.Draw(sheet)
        for i,f in enumerate(rr):
            x=gap+(i%3)*(w+gap);y=gap+(i//3)*(h+38);sheet.paste(Image.fromarray(pics[f]),(x,y))
            pen.text((x+8,y+h+10),f'{full.tc(f)}  /  frame {f:,}',fill=(232,224,201),font_size=17)
        sheet.save(QA/f'decoded-{name}.jpg',quality=94)
    for kkey in ('test-down','test-up','slump','rift-down','rift-early','rift-late','rocks-answer'):
        f=BY[kkey].f
        for j in (-3,0,8,20):Image.fromarray(pics[f+j]).save(QA/f'impact-{kkey}-{j:+03d}.png')
    return {'shot_probes':edits,'edited_original_shots':list(EDITED),'retained_original_shots':list(RETAINED),
            'anchor_probes':{name:{'frame':BY[name].f,'s':BY[name].f/FPS,'samples':BY[name].sample} for name in ACTIONS},
            'sample_frames':len(sample),'representative_frames_not_viewer_retention_data':True}


def verify(target,ref,parts=None,passes=None):
    layout=full.streams(target)
    for name,x in ref['streams'].items():
        if name=='vide':
            assert {k:v for k,v in layout[name].items() if k!='edit_list'}=={k:v for k,v in x.items() if k!='edit_list'}
        else:assert layout[name]==x,(name,layout[name],x)
    current=red.track_fingerprints(target);old=ref['locked_track_fingerprints']
    assert old['video']['sample_bytes_sha256']!=current['video']['sample_bytes_sha256']
    assert all(current[q]==old[q] for q in ('subtitles','chapters')),'Subtitle or chapter timing/payload changed'
    _,log=full.run(['-i',str(target),'-map','0','-c','copy','-t','0.100','-f','null','-'])
    for marker in ('h264 (High)','yuv420p(tv, bt709, progressive), 1920x1080','24 fps','Audio: aac (LC)','48000 Hz, stereo','(eng): Subtitle: mov_text'):
        assert marker in log,marker
    assert all(c['title'] in log for c in ref['chapters'])
    aac=aac_packet_log(target);audio=decoded_audio(target)
    assert aac==aac_packet_log(red.MOVIE) and aac['media_packet_count']==layout['soun']['packet_samples']
    assert audio==decoded_audio(red.MOVIE),'Decoded stereo samples differ'
    caption,_=full.captions(target,red.CAPTIONS);assert caption==ref['caption_audit']
    print('AUDIO_CAPTIONS_CHAPTERS_BIT_EXACT',aac['media_packet_count'],caption['english_cues'],len(ref['chapters']),flush=True)
    frames=red.check_decode(target);print('ALL_VIDEO_FRAMES_DECODED',frames,flush=True)
    QA.mkdir(exist_ok=True,parents=True);proof=visual_audit(target);print('DECODED_VISUAL_PROBES',proof['sample_frames'],flush=True)
    return {'title':full.TITLE,'status':'Investigation Cut · review only, not published','duration_s':N/SR,'fps':FPS,'decoded_video_frames':frames,
            'picture_is_new':True,'audio_is_remuxed_not_reencoded':True,'red_sound_and_timing_lock':ref['files'][0],
            'visual_audit':proof,'encoded_parts':parts,'render_passes':passes,'streams':layout,'video_samples_sha256':current['video']['sample_bytes_sha256'],
            'aac_packet_log':aac,'decoded_stereo_pcm_f32le_sha256':audio,'encoded_subtitle_and_chapter_track_matches':True,
            'caption_audit':caption,'chapters':ref['chapters'],'voice_source_sha256':ref['source_voice_sha256'],'audio_measurements_from_identical_red_program':{
                k:ref['audio'][k] for k in ('lufs_i','peak_dbtp','sync_windows','all_offsets_samples')},
            'source_audio_anchors':len(B),'human_pronunciation_signoff':False}


def handoff(r,ref):
    m=r['files'][0];x=[f'# {full.TITLE}', '', '**Investigation Cut · Full-film picture revision · 07:25.667 · Review only**', '',
        'This edit turns the comparison into a sequence of visible tests: match the prints, try the same stamp in two muds, challenge an apparent match in time, and follow the rocks rather than the dinosaur. It is a separate file. '+
        'The Sound Redesign review is the comparison baseline and stays intact; its recorded narration, stereo mix and all original sample timing are unchanged.', '',
        '## Where to look', '', '| Film time | Picture change |','|---|---|',*[f'| **{t}** | {q} |' for t,q in LOOKS], '',
        '## What the picture does not claim', '',
        '- The **125 Ma** atlas is an independent geographic model, not a footprint date. The distances are regional approximations (about 6,000 km now, 1,000 km in the model), not the length of an animal’s journey. The sweep exposes two sourced snapshots. The splitting blocks are a schematic, not a plate motion interpolation.',
        '- Print outlines, **~69 cm** demonstration, camera views, grain/cement, pollen and fish are original illustrations, not site photography, a survey mesh or an exact specimen. The length is one impression (TK-034), not body size. A mineral cement or possible microbial mat is part of a preservation interpretation, not evidence of one universal process.',
        '- Similar riverbanks and partially overlapping broad age assignments do not establish the same river or the same day. Regional pollen in other deposits does not directly date either footprint bed. The displayed age bars are schematic, not numerical endpoints; Mawsonia finds come from other basins, not the track sites. No plotted individual trail.', '',
        '## Version and verification', '',
        f"- 1080p24 Rec.709 H.264; all **{r['decoded_video_frames']:,}** frames decoded on the original 24 fps grid. **{len(EDITED)}** original shot slots revised (some now have internal cuts); **{len(RETAINED)}** selected useful action beats retained. The 66 shot starts remain seekable.",
        f"- All **{r['aac_packet_log']['media_packet_count']:,}** compressed AAC packets and the stereo decoder output match the Sound Redesign bit-for-bit. No new mix, gain shift, voice synthesis or AAC encoding. Same **−17.1 LUFS-I / −1.8 dBTP** programme and **127** selectable English cues. The English SRT sidecar has the same timing and text; all nine chapter entries are unchanged.",
        f"- Verified against the delivered MP4, with **{r['visual_audit']['sample_frames']}** decoded picture samples and checks around contact, lift, slump, fault, water entry and the rock answer. This is technical / visual QA, not viewer retention data, owner playback approval or a release signoff.",
        '- Before release, listen to **Sousa** at **03:34–03:39** for pronunciation. No publication, permission change or archive replacement.',
        f"- `{m['name']}` · {m['bytes']:,} bytes · SHA-256 `{m['sha256']}`.", '', '## Unchanged chapters', '',
        '| In | Chapter |','|---|---|',*[f"| {full.tc(q['start_frame'])} | {q['title']} |" for q in ref['chapters']], '',
        '## Attribution', '',
        '- Research: [Jacobs et al. (2024)](https://igeo.ufrj.br/inc/isc/3/03_139_Jacobs%20etal.pdf); [Menkem et al. (2026)](https://doi.org/10.1016/j.jop.2026.100416); [Carvalho, Borghi & Leonardi (2013)](https://doi.org/10.1016/j.cretres.2013.04.004).',
        '- Cartography: [Kocsis & Scotese PaleoCoastlines and rotations](https://doi.org/10.1016/j.earscirev.2020.103463) and [Scotese & Wright PaleoDEMs v2](https://doi.org/10.5281/zenodo.5460860), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), resampled, recoloured, shaded and annotated. Present day: [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/) & NOAA ETOPO5, public domain. Type: Fraunces and IBM Plex, SIL OFL 1.1.',
        '- Sound: original arrangement; recordings trimmed, layered, equalized, pitch/time-shaped and spatialized where needed. The result is illustrative, not site recording or endorsement. Same credits embedded in the file.', '',
        '| Recordist / library | License |','|---|---|']
    x.extend(f"| [{q['credit']}]({q['original_url']}) | [{q['license']}]({q['license_url']}) |" for q in ref['sound_sources'])
    NOTES.write_text('\n'.join(x)+'\n',encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify-only',action='store_true')
    p.add_argument('--initial-pass');p.add_argument('--redone',nargs='+',type=int,choices=EDITED,default=())
    x=p.parse_args()
    if bool(x.initial_pass)!=bool(x.redone) or x.verify_only and x.initial_pass:p.error('Pass --initial-pass and --redone together, for a two-pass conform only')
    ref=preflight();OUT.mkdir(parents=True,exist_ok=True)
    if x.verify_only:
        old=json.loads(RECEIPT.read_text());assert full.file_record(MOVIE)==old['files'][0];parts=old['encoded_parts'];passes=old['render_passes'];target=MOVIE
    else:
        m,parts,passes=select_parts(x.initial_pass,tuple(sorted(set(x.redone))));target=MOVIE.with_suffix('.pending.mp4');mux(m,target,ref)
    r=verify(target,ref,parts,passes)
    if target!=MOVIE:
        target.replace(MOVIE);shutil.copyfile(red.CAPTIONS,CAPTIONS)
    else:assert full.base.hashfile(CAPTIONS)==ref['files'][1]['sha256']
    r['files']=[full.file_record(MOVIE),full.file_record(CAPTIONS)];handoff(r,ref);r['files'].append(full.file_record(NOTES))
    RECEIPT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('INVESTIGATION_CUT_VERIFIED',json.dumps(r['files'],ensure_ascii=False),flush=True)


if __name__=='__main__':main()
