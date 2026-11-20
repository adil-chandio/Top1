"""Targeted native-frame replacements for V1's original soft wide-jump proxies.

This is a one-time patch for that render; the current renderer already protects
these shot ranges at native cadence when building a new review from scratch.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

C=Path(os.environ.get('MONARCH_ANT_CACHE','.cache/monarch-cam-ant-film'))/'work'
FF=os.environ.get('FFMPEG','ffmpeg')
BASE=[FF,'-hide_banner','-nostdin','-xerror','-loglevel','warning']
BYTES=768*432*3//2


def review_sections(m):
    return [s for s in m['shots'] if s['mode']==0 and s['cam'] in (1,14) and s['src'][0]<5.54 and s['src'][1]>3.17]


def patches():
    m=json.loads((C/'film.json').read_text());s=review_sections(m);first=0
    with (C/'native-wides.plan').open('w') as f:
        for a in s:
            n=a['end']-a['first']; print(first,first+n,a['mode'],a['cam'],*a['src'],a['overlay'],a['dark'],file=f)
            first+=n
    print(f'{len(s)} wide jump sections · {first} native replacement frames',flush=True)


def combine():
    m=json.loads((C/'film.json').read_text());sections=review_sections(m);idx=0;expected=0
    original=C/'film-picture.mp4';alt=C/'native-wides.mp4';final=C/'film-picture-polished.mp4'
    def raw(p):
        return subprocess.Popen(BASE+['-threads','2','-i',str(p),'-map','0:v:0','-threads','1','-pix_fmt','yuv420p','-f','rawvideo','-'],stdout=subprocess.PIPE)
    procs=[raw(original),raw(alt)]
    try:
        proc=subprocess.Popen(BASE+['-f','rawvideo','-pixel_format','yuv420p','-video_size','768x432','-framerate','24','-i','-',
              '-c:v','libx264','-threads','2','-preset','veryfast','-crf','17','-maxrate','1950k','-bufsize','3800k',
              '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv','-g','48',
              '-movflags','+faststart','-y',str(final)], stdin=subprocess.PIPE)
        procs.append(proc); old,new=(p.stdout for p in procs[:2])
        for n in range(m['frames']):
            b=old.read(BYTES)
            if len(b)!=BYTES:raise ValueError(f'Review base dropped frame {n}')
            if idx<len(sections) and n==sections[idx]['end']:idx+=1
            if idx<len(sections) and sections[idx]['first']<=n<sections[idx]['end']:
                b=new.read(BYTES)
                if len(b)!=BYTES:raise ValueError(f'Replacement dropped frame {n}')
                expected+=1
            proc.stdin.write(b)
        if old.read(1) or new.read(1):raise ValueError('Video has more frames than its plan')
        proc.stdin.close()
        if any(p.wait()!=0 for p in procs):raise ValueError('Frame replacement failed')
        if expected!=sum(s['end']-s['first'] for s in sections):raise ValueError('Some patches were not used')
        (C/'native-wides-receipt.json').write_text(json.dumps({'ranges':[[a['first'],a['end']] for a in sections],'replaced':expected},indent=2)+'\n')
        original.rename(C/'film-picture-before-native-wides.mp4');final.replace(original)
        print(f'{expected} wide frames replaced, total unchanged: {m["frames"]}',flush=True)
    finally:
        for p in procs:
            if p.poll() is None:p.kill();p.wait()


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=('plan','apply'));x=a.parse_args()
    (patches if x.action=='plan' else combine)()
