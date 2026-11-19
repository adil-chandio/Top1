#!/usr/bin/env python3
"""Original synthesized ambient score for the gecko draft. No external samples."""
from pathlib import Path
import wave, numpy as np
p=Path(__file__).resolve().parent;out=p/'audio'/'original-bed.wav';out.parent.mkdir(exist_ok=True)
sr=24000;dur=60.8;t=np.arange(round(sr*dur),dtype=np.float64)/sr;rng=np.random.default_rng(3905)
# Low-density tonal drone and filtered noise; no stock music or imitation of reference audio.
fade=np.minimum(np.minimum(t/2,np.maximum(0,(dur-t)/2)),1)
chord=np.sin(2*np.pi*55*t)*.45+np.sin(2*np.pi*82.41*t+.4)*.22+np.sin(2*np.pi*110*t+.7)*.15+np.sin(2*np.pi*164.81*t+1)*.09
slow=.65+.35*np.sin(2*np.pi*.035*t)**2
# Interpolate low-rate random noise for a broad subdued atmospheric layer.
k=int(dur*40)+2;noise=np.interp(t,np.arange(k)/40,rng.normal(0,1,k));noise=np.clip(noise/3,-1,1)
# Restrained swells around explanatory transitions, not diegetic animal sounds.
swells=np.zeros_like(t)
for c in [10.79,20.56,34.40,49.26]:
 envelope=np.exp(-((t-c)/1.2)**2);swells+=.05*envelope*np.sin(2*np.pi*(210*t+8*np.sin(t*.7)))
mono=(.16*chord*slow+.035*noise+swells)*fade*.34
stereo=np.stack((mono,mono*.96),axis=-1);pcm=np.asarray(np.clip(stereo,-.98,.98)*32767,dtype='<i2')
with wave.open(str(out),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())
print(out,'duration',len(t)/sr,'peak',np.max(np.abs(stereo)))
