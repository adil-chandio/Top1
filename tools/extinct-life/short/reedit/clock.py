"""One sample clock for the V2 recut, ranging from dry narrations to geometry."""
from __future__ import annotations
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from spec import CACHE as SOURCE, ROOT, W, H, FPS, SR, MATS, FIELDS, TITLE, dump, digest

CACHE=SOURCE/'reedit'
QA=CACHE/'qa'
MIX=CACHE/'mix'
NAME='Atlantic-Tracks-Short-01-V2'
OUT=ROOT/'deliverables/extinct-life-short-01-v2'
MASTER=OUT/(NAME+'.mp4')
CAPTIONS=OUT/(NAME+'.en.srt')
STUDIO=OUT/(NAME+'-Studio.txt')
PENDING=CACHE/'encode'/(NAME+'.pending.mp4')
FP=SR//FPS
# Sample-accurate spaces between the original phrase spans. Stops are longer
# than commas, but no one is left waiting for the edit to catch up with speech.
PAUSES_MS=(130,142,145,113,138,170,155,129,156,134,118,159,146)
INTRO_MS=56
TAIL_MS=156


def frame(sample):return round(sample/FP)


def finish(cues):
    p=lambda i:frame(cues[i]['speech_start'])
    def word(i,v):return next(frame(w['start']) for w in cues[i]['words'] if w['token']==v)
    frames=(cues[-1]['speech_end']+round(TAIL_MS*SR/1000)+FP-1)//FP
    # Cut just ahead of new subjects. Within a subject, cut on the verb.
    firm,soft,lip,compare=p(2)-2,p(3)-2,word(4,'slump')-1,p(5)-1
    brazil,cameroon,today,rewind=p(6)-2,p(7)-2,p(8)-2,p(9)-1
    strata,returning=p(12)-2,word(13,'hints')-2
    cuts=(0,firm,soft,lip,compare,brazil,cameroon,today,rewind,strata,returning,frames)
    e={
        'hook_impact':5,'hook_lift':26,'hook_slump':37,
        'firm_impact':firm+5,'firm_lift':firm+27,
        'soft_impact':soft+5,'soft_lift':soft+27,'soft_slump':soft+37,
        'lip_cut':lip,'lip_chip':word(4,'lifts')+1,'match_reveal':compare,
        'brazil_cut':brazil,'cameroon_cut':cameroon,'globe_cut':today,
        'map_rewind':p(9)+2,'map_land':word(10,'atlantic')+8,
        'rock_cut':strata,'rock_chip':strata+14,'return_air':returning,
    }
    art=dict(wipe_begin=e['map_rewind']+1,wipe_end=e['map_land'],lip_chip=e['lip_chip'],
             today=today,rewind=rewind,strata=strata,returning=returning)
    assert 700<frames<790 and all(b-a>=27 for a,b in zip(cuts,cuts[1:]))
    assert lip<e['lip_chip']<compare and rewind<art['wipe_begin']<art['wipe_end']<strata
    probes={0,1,5,12,26,37,47,frames-2,frames-1}
    for a,b in zip(cuts,cuts[1:]):probes.update((a,min(a+7,b-1),(3*a+b)//4,(a+b)//2,b-1))
    probes.add((art["wipe_begin"]+art["wipe_end"])//2)
    for k in ('soft_slump','lip_chip','map_rewind','map_land','rock_chip'):
        n=e[k];probes.update((n,n+5,n+10))
    return dict(frames=frames,samples=frames*FP,seconds=frames/FPS,cuts=cuts,events=e,art=art,probes=sorted(probes))


def header(t):
    array=', '.join(map(str,t['cuts']))
    values='\n'.join(f'constexpr int {k}={v};' for k,v in t['art'].items())
    return f'''// Generated from V2 narration samples. Do not hand-edit.
#pragma once
#include <array>
namespace recut_clock {{
constexpr int fps={FPS}, last={t['frames']};
constexpr std::array<int, {len(t['cuts'])}> cuts={{ {array} }};
{values}
}}
'''
