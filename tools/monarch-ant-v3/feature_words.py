"""Align the approved English transcript to the seven locked takes; optional SRT."""
from difflib import SequenceMatcher
from hashlib import sha256
import json
import os
from pathlib import Path
import re

from pilot import FPS, SR
from feature_cut import ANCHORS, META, WORK

V = Path(os.environ.get('MONARCH_VO_EDIT_DIR','.cache/monarch-cam-ant-vo-v1'))
SCRIPT = Path(os.environ.get('MONARCH_SCRIPT_TXT','deliverables/monarch-cam-step-2/Monarch-Cam-Ant-Narration.txt'))
PARAS = (0,6,10,14,19,23,27,30)


def tokens(w):
    t=w.lower().replace('’',"'").replace('–','-').replace('—','-')
    t=re.sub(r'\b117\b','one hundred and seventeen',t)
    t=re.sub(r'\b15\s*%','fifteen percent',t)
    t=re.sub(r'\bbackward\b','backwards',t)
    t=re.sub(r'\bant[ -]+lion\b','antlion',t)
    return re.findall(r"[a-z]+(?:'[a-z]+)?|[\d]+",t)


def load_words():
    m=json.loads(META.read_text());prev=json.loads((V/'edit-receipt-first.json').read_text())
    locked=json.loads((V/'edit-receipt.json').read_text())
    review=json.loads((V/'whisper-review.json').read_text());pickup=json.loads((V/'whisper-pickups.json').read_text())
    assert locked['wav_sha256']==m['vo_sha256'] and review['wav_sha256']==prev['wav_sha256']
    assert sha256(SCRIPT.read_bytes()).hexdigest()==locked['script_text_sha256']
    by={k['beat']:k for k in pickup['results']}
    para=re.split(r'\n\n+',SCRIPT.read_text().strip());assert len(para)==PARAS[-1]
    output=[]
    for i in range(7):
        r=by.get(i+1,review['results'][i]);words=r['timed_words'];base=m['vo_ranges'][i]
        shift=(base[2]-base[0]+locked['beats'][i]['start_sample']) / SR
        if i+1 not in by:shift-=prev['beats'][i]['start_sample']/SR
        clean=[]; targets=[]; source=[]
        for j in range(PARAS[i],PARAS[i+1]):
            for x in para[j].split():
                for t in tokens(x):targets.append((t,len(clean)))
                clean.append(dict(word=x, beat=i+1, paragraph=j, hits=[]))
        j=0
        while j<len(words):
            x=words[j];k=j+1
            if k<len(words) and [x['word'].lower().strip('.,? -'),words[k]['word'].lower().strip('.,? -')] in (['ant','lion'],['15','%']):k+=1
            for t in tokens(' '.join(y['word'] for y in words[j:k])):
                source.append((t,x['start_s']+shift,words[k-1]['end_s']+shift))
            j=k
        comp=SequenceMatcher(a=[t for t,_ in targets],b=[t for t,*_ in source],autojunk=False)
        if comp.ratio()<.987:raise ValueError(('check transcript',i+1,comp.ratio()))
        for tag,l,k,a,b in comp.get_opcodes():
            if tag not in ('equal','replace') or k-l!=b-a:raise ValueError((i+1,tag,targets[l:k],source[a:b]))
            for (_,ix),(t,t0,t1) in zip(targets[l:k],source[a:b]):clean[ix]['hits'].append((t0,t1))
        for x in clean:
            hits=x.pop('hits');assert hits,x
            x['a']=max(ANCHORS[i]/FPS,min(v[0] for v in hits));x['b']=min(ANCHORS[i+1]/FPS,max(v[1] for v in hits))
            assert x['a']<=x['b'],x
        output.extend(clean)
    assert len(output)==811,len(output)
    (WORK/'locked-words.json').write_text(json.dumps(output,ensure_ascii=False,indent=1)+'\n')
    return output


def cap_lines(words):
    text=' '.join(words)
    if len(text)<=37:return text
    opts=[]
    for i in range(1,len(words)):
        a,b=' '.join(words[:i]),' '.join(words[i:]);
        if max(len(a),len(b))>39:continue
        prior=words[i-1][-1] in ',;:.?!'
        orphan=words[i-1].lower() in ('a','the','to','of','and','an','as','by','but','with')
        opts.append((abs(len(a)-len(b)) - 8*prior + 14*orphan,a,b))
    if not opts:return None
    _,a,b=min(opts);return f'{a}\n{b}'


def srt(rows,path):
    clips=[];i=0
    while i<len(rows):
        j=i+1; x=rows[i]
        while j<len(rows):
            y=rows[j]
            if y['paragraph']!=x['paragraph'] or y['a']-rows[j-1]['b']>.52:break
            if j-i>=4 and rows[j-1]['word'][-1:] in ('.','?','!',';'):break
            if y['b']-x['a']>4.35 or not cap_lines([a['word'] for a in rows[i:j+1]]):break
            j+=1
        line=cap_lines([a['word'] for a in rows[i:j]])
        assert line
        t=x['a']; last=rows[j-1]['b']; stop=min(ANCHORS[x['beat']]/FPS,last+.22)
        if j<len(rows):stop=min(stop,rows[j]['a'])
        assert stop>t,(i,j,stop,t)
        clips.append((t,stop,line));i=j
    def stamp(t):
        n=round(1000*t);secs,ms=divmod(n,1000);m,s=divmod(secs,60)
        return f'00:{m:02d}:{s:02d},{ms:03d}'
    assert ' '.join(line.replace('\n',' ') for _,_,line in clips)==' '.join(r['word'] for r in rows)
    path.write_text(''.join(f'{n}\n{stamp(a)} --> {stamp(b)}\n{k.replace(chr(8217),chr(39))}\n\n' for n,(a,b,k) in enumerate(clips,1)),encoding='utf-8')
    return len(clips)


def log_words(rows):
    print('Per-paragraph VO marks in absolute frames:')
    for k in range(PARAS[-1]):
        r=[x for x in rows if x['paragraph']==k]; print(f'{k:02}:', '  '.join(f'{x["word"]}@{round(x["a"]*FPS)}' for x in r))


if __name__=='__main__':
    w=load_words();log_words(w);print(srt(w,WORK/'feature.en.srt'),'caption cues')
