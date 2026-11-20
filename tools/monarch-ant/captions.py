"""Make a soft-caption sidecar with Script V1 wording, aligned to measured VO.

ASR tokens supply timing only (not on-screen text). In particular, retain
'larva' and the expanded numbers/percent exactly as written in Script V1.
"""
import argparse
import hashlib
import json
from difflib import SequenceMatcher
from pathlib import Path
import re
import textwrap

C=Path('.cache/monarch-cam-ant-vo-v1')
SCRIPT=Path('deliverables/monarch-cam-step-2/Monarch-Cam-Ant-Narration.txt')
SHA='791bd0618e4f916fe965a81268977566da12d7506e1fbd070a5657d300db814d'
TOK=re.compile(r"[a-z0-9]+(?:['’][a-z]+)?|%",re.I)
HEAD=['The ant is climbing.', 'From above,', 'These jaws don’t have to snap.',
      'Back in the pit,', 'Here’s a jump with a different ending.',
      'In a second experiment,', 'Watch the first escape again.']
EXP={'117':['one','hundred','and','seventeen'],'15':['fifteen'],'%':['percent'],'larvae':['larva']}

def load(n):return json.loads((C/n).read_text())

def stamp(s):
    t=round(s*1000);h,t=divmod(t,3600000);m,t=divmod(t,60000);s,t=divmod(t,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{t:03d}'


def align(timing,out):
    text=SCRIPT.read_text();data=SCRIPT.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError('script is not the locked Script V1')
    src=load('edit-receipt.json')['beats']; old=load('edit-receipt-first.json')['beats']
    first={x['beat']:x['timed_words'] for x in load('whisper-review.json')['results']}
    takes={x['beat']:x['timed_words'] for x in load('whisper-pickups.json')['results']}
    rec=json.loads(timing.read_text()); vt=rec['vo_ranges']; fps=rec['fps']; work=[];coverage=[]
    starts=[text.index(k) for k in HEAD]+[len(text)]
    for i,b in enumerate(src):
        n=i+1; begin=b['start_sample']/48000; off=(vt[i][2]-vt[i][0])/48000
        adj=begin if n in takes else (b['start_sample']-old[i]['start_sample'])/48000
        p=' '.join(text[starts[i]:starts[i+1]].split());m=list(TOK.finditer(p));t0=[j.group().lower().replace('’',"'") for j in m];t1=[];times=[]
        for q in takes.get(n,first[n]):
            for token in TOK.findall(q['word'].lower().replace('’',"'")):
                ex=EXP.get(token,[token]); a=q['start_s']+adj+off;z=q['end_s']+adj+off
                for u,k in enumerate(ex):
                    t1.append(k);times.append((a+(z-a)*u/len(ex),a+(z-a)*(u+1)/len(ex)))
        lookup={}; exact_count=0
        for tag,a,b,c,d in SequenceMatcher(None,t0,t1,autojunk=False).get_opcodes():
            if tag=='equal':
                exact_count+=b-a
                for j,k in zip(range(a,b),range(c,d)):lookup[j]=times[k]
            elif tag in ('replace','delete') and a<b:
                start=times[c][0] if c<len(times) else times[-1][1]-.06
                end=times[d-1][1] if d>c else start+.07
                for j in range(a,b):lookup[j]=(start+(end-start)*(j-a)/(b-a),start+(end-start)*(j-a+1)/(b-a))
        coverage.append(exact_count/len(t0))
        if coverage[-1]<.96:raise ValueError(f'unreliable ASR timing for beat {n}: {coverage[-1]:.3f}')
        j=0
        while j<len(m):
            best=None
            for k in range(j+1,min(len(m),j+18)+1):
                start=m[j].start();end=m[k].start() if k<len(m) else len(p)
                value=p[start:end].strip();lines=textwrap.wrap(value,width=42,break_long_words=False,break_on_hyphens=False)
                if len(lines)>2 or lookup[k-1][1]-lookup[j][0]>5.3:break
                is_stop=bool(re.search(r'[.!?]$',value)); weak=bool(re.search(r'[,;:]$',value))
                # Prefer real phrase endings but do not trap one-word tails.
                best=max(best or (-1,0,''),(min(len(value),77)+(38 if is_stop else (13 if weak else 0)),k,'\n'.join(lines)))
                if is_stop and (k-j)>2:break
            if best is None:raise ValueError('cannot wrap captions')
            _,k,value=best
            lo=lookup[j][0]-.04;hi=max(lookup[k-1][1]+.14,lo+.80)
            work.append([max(0.,lo),min(hi,rec['frames']/fps),value]); j=k
    output=[]
    for i,(a,b,value) in enumerate(work):
        if i+1<len(work):b=min(b,work[i+1][0]-.011)
        if b<=a:raise ValueError(f'overlapping caption {i}')
        output.append(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{value}\n')
    out.write_text('\n'.join(output)+'\n')
    print(f'{len(output)} caption cues. Exact timing token match by beat: '+', '.join(f'{a:.2%}' for a in coverage))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('timing',type=Path);p.add_argument('output',type=Path);a=p.parse_args();align(a.timing,a.output)
