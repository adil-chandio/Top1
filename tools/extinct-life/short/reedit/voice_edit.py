"""Remove interior air from the original performances, not syllables."""
from __future__ import annotations
from functools import lru_cache
import json

import numpy as np
from scipy.ndimage import gaussian_filter1d

from clock import HERE, SOURCE, MIX, QA, SR, INTRO_MS, PAUSES_MS, finish, dump, digest
from spec import TAKES
from mix import ar, db, decoded, envelope, eq, savewav, take_spans, windows, WORD


@lru_cache(maxsize=1)
def voice():
    locked=json.loads((HERE.parent/'inputs.json').read_text())['private_vo_and_diffuse_detail']
    parts=[];cues=[];original=[];edits=[];target=INTRO_MS*SR//1000
    for stem,old_frame,texts in TAKES:
        p=SOURCE/'vo'/f'{stem}.wav';h=digest(p)
        assert h==locked[f'vo/{stem}.wav']
        words,phrases=take_spans(p,texts);x=decoded(p)
        # Match whole takes before cutting them. Don't flatten every word with
        # a compressor. The small de-esser tracks actual sibilant energy.
        y=eq(x,72,11950)
        lev=windows(y);active=lev[lev>max(.0028,float(lev.max())*.11)]
        g=np.clip(.087/np.quantile(active,.65),.28,6.9);y*=g
        s=eq(y,5480,11050);m=eq(y,540,4600)
        mask=np.clip((np.sqrt(gaussian_filter1d(s*s,106))-.037-.39*np.sqrt(gaussian_filter1d(m*m,141)))/.097,0,.46)
        y-=s*mask
        wpos=0;old_offset=old_frame/30-max(0,words[0][1]-.036)
        for text,aa,bb in phrases:
            # Interior 8–12 ms cosine fades never touch aligned words. Wider
            # guards keep f/s/t and the voiced release on 'route' intact.
            start,end=ar(aa),ar(bb)
            lo,hi=max(0,start-ar(.047)),min(len(x),end+ar(.061))
            blob=y[lo:hi].copy();blob*=envelope(len(blob),.008,.012)
            off=target-start;l,r=lo+off,hi+off
            assert l>=0 and (not parts or l>=parts[-1][0]+len(parts[-1][1])),(text,l)
            # Check the splice edges against actual signal energy, not the
            # alignment alone. Omitted tails can contain breath, not speech.
            level=max(np.max(windows(blob)),.001)
            edges=[float(np.max(windows(t))) for t in (y[lo:lo+ar(.009)],y[hi-ar(.011):hi])]
            assert max(edges)<.16*level,(text,[db(z) for z in edges],db(level))
            parts.append((l,blob))
            count=len(WORD.findall(text.lower()));ws=words[wpos:wpos+count];wpos+=count
            aligned=[dict(token=k,start=ar(a)+off,end=ar(b)+off) for k,a,b in ws]
            assert aligned[0]['start']==target and aligned[-1]['end']==end+off
            cues.append(dict(text=text,speech_start=target,speech_end=end+off,words=aligned))
            original.append((round((old_offset+aa)*SR),round((old_offset+bb)*SR)))
            edits.append(dict(source=p.name,sha256=h,trim_48k=[lo,hi],anchor=target,destination=[l,r],
                              gain_db=round(db(float(g)),3),edge_to_peak_db=[round(db(z/level),1) for z in edges]))
            j=len(cues)-1
            if j<len(PAUSES_MS):target=end+off+PAUSES_MS[j]*SR//1000
        assert wpos==len(words)
    t=finish(cues);n=t['samples'];a=np.zeros(n,np.float32)
    for l,blob in parts:a[l:l+len(blob)]=blob
    for i,c in enumerate(cues):
        nxt=cues[i+1]['speech_start'] if i+1<len(cues) else n
        # 14 full, accessible sentences; visual phrase subdivisions below
        # this layer are derived from the same per-word timestamps.
        c['start_sample']=c['speech_start'];c['end_sample']=min(nxt-ar(.023),c['speech_end']+ar(.10))
        assert c['end_sample']>c['speech_end']
    old_gaps=[round((v[0]-u[1])*1000/SR,1) for u,v in zip(original,original[1:])]
    gaps=[round((v['speech_start']-u['speech_end'])*1000/SR,1) for u,v in zip(cues,cues[1:])]
    loop_gap=(n-cues[-1]['speech_end']+cues[0]['speech_start'])*1000/SR
    x=windows(eq(a,170,5200));is_voice=x>10**(-43/20)
    # 10 ms RMS measurement across the electrical voice stem, including loop.
    bin0=np.flatnonzero(is_voice);quiet_max=max(int(np.max(np.diff(bin0)))-1,int(len(x)-bin0[-1]+bin0[0]-1))*10
    assert max(gaps)<=170 and loop_gap<253 and quiet_max<=300,(gaps,loop_gap,quiet_max)
    pace=dict(previous_seconds=34.0,recut_seconds=round(t['seconds'],3),previous_phrase_gaps_ms=old_gaps,
        phrase_gaps_ms=gaps,previous_max_ms=max(old_gaps),longest_gap_ms=max(gaps),
        voiced_rms_longest_gap_ms=quiet_max,voiced_rms_gate_dbfs=-43,
        first_word_ms=INTRO_MS,loop_word_gap_ms=round(loop_gap,1),speech_audio_respeed=False)
    return a,cues,edits,t,pace


if __name__=='__main__':
    a,c,e,t,p=voice();MIX.mkdir(parents=True,exist_ok=True)
    savewav(MIX/'narration-edit.wav',a);dump(QA/'pacing.json',dict(pace=p,timeline=t,cues=c,edits=e))
    print('NARRATION_RECUT',p,flush=True);print('CLOCK',t,flush=True)
    for x in c:print(f"{x['speech_start']/SR:.3f}–{x['speech_end']/SR:.3f}  {x['text']}")
