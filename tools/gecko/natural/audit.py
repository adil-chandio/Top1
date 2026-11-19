"""Frame-by-frame QC of the finished moving export (not render previews)."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('file',type=Path)
p.add_argument('--root',type=Path,default=Path('.cache/monarch-gecko/natural'))
a=p.parse_args()
qa=a.root/'qa';qa.mkdir(parents=True,exist_ok=True)
plan=json.loads((a.root/'work'/'plan.json').read_text());fps=plan['fps']; n=plan['frames']
ff=os.environ.get('FFMPEG','ffmpeg');fp=os.environ.get('FFPROBE','ffprobe')
render=lambda *xs:subprocess.check_output([ff,'-nostdin','-hide_banner','-v','error','-xerror','-threads','2',*xs])
frames=render('-i',str(a.file),'-map','0:v:0','-an','-filter_threads','1','-vf','scale=90:160:flags=area,format=gray','-pix_fmt','gray','-f','rawvideo','-')
assert len(frames)==n*90*160,len(frames)
q=np.frombuffer(frames,dtype=np.uint8).reshape(n,160,90)
cut={s['frame'] for s in plan['entries'] if s['source']!='settle'}
delta=np.r_[0.,np.mean(np.abs(q[1:].astype(np.int16)-q[:-1].astype(np.int16)),axis=(1,2))]
dup=[i for i in range(1,n) if np.array_equal(q[i],q[i-1])]
first_fade=round(fps*61.42); low=np.nonzero(q.mean(axis=(1,2))<11)[0].tolist()
assert not any(i<first_fade for i in low),f'Unexpected dark frames {low}'
assert not dup,f'Exact duplicate moving frames {dup}'
seams=sorted({p['first'] for p in plan['parts']}|{plan['outFrame']})
checks=[]
for i in seams:
    if i<3 or i in cut or i+4>=n:continue
    background=[delta[j] for j in range(i-3,i+5) if j not in cut and j!=i]
    maximum=max(background,default=0)
    limit=max(2.45,maximum*1.9+.7)
    checks.append({'frame':i,'seconds':round(i/fps,5),'meanLumaJump':round(float(delta[i]),3),'maxNeighbor':round(float(maximum),3),'limit':round(limit,3)})
violations=[c for c in checks if c['meanLumaJump']>=c['limit']]
assert not violations,f'Unexpected trace seam: {violations}'
pts=json.loads(subprocess.check_output([fp,'-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(a.file)]))['frames']
assert len(pts)==n and all(abs(float(s['best_effort_timestamp_time'])-i/fps)<1.01e-6 for i,s in enumerate(pts)), 'Frame clock mismatch'

# Actual editorial and action landmarks: first eye, all shots, touchdown,
# release checkpoints and the last visible image before the fade.
review=[int(s['frame']+(s['end']-s['frame'])*.53) for s in plan['entries'] if s['source']!='settle']
review=sorted(set(review+[0,76,791,822,888,933,963,980,982,n-22]))
filt='+'.join(f'eq(n\\,{i})' for i in review)
thumbs=render('-i',str(a.file),'-an','-filter_threads','1','-vf',f'select={filt},scale=162:288:flags=area','-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-')
assert len(thumbs)==len(review)*162*288*3
images=np.frombuffer(thumbs,dtype=np.uint8).reshape(-1,288,162,3)
names={i:next(s['kind'] for s in plan['entries'] if s['frame']<=i<s['end']) for i in review}
cols=8;sheet=Image.new('RGB',(cols*172,((len(review)+cols-1)//cols)*319),(17,25,31));draw=ImageDraw.Draw(sheet)
for j,(i,im) in enumerate(zip(review,images)):
    x,y=(j%cols)*172+5,(j//cols)*319+3
    sheet.paste(Image.fromarray(im),(x,y));draw.text((x+2,y+291),f'{i/fps:05.2f}s  {names[i]}',fill=(217,231,230))
sheet.save(qa/'moving-export-review.jpg',quality=94)
result={'framesDecoded':n,'regularPTS':True,'exactAdjacentDuplicates':dup,'darkFramesInFadeOnly':low,
        'rangeContinuity':checks,'reviewFrames':review,'maxInShotLumaJump':round(max(float(delta[i]) for i in range(1,n) if i not in cut),3)}
(qa/'motion.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'{n} frame samples, {len(checks)} continuous render joins, {len(review)} editorial/detail extracts; no duplicates or timing errors')
