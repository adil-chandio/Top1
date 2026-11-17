"""Original quiet non-diegetic transition textures + selected English voice.
No music/borrowed effects. Technical loudness checks are NOT listening approval.
"""
from pathlib import Path
import numpy as np
import wave,json,hashlib,subprocess,re
import imageio_ffmpeg
OUT=Path('studio/runtime/gecko/motion-pass');OUT.mkdir(parents=True,exist_ok=True)
voice=Path('studio/runtime/gecko/narration/english-narration-v1.wav');SR=24000
with wave.open(str(voice),'rb') as w:
 assert w.getframerate()==SR and w.getsampwidth()==2 and w.getnchannels()==1
 a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float64)/32768
mix=np.zeros(66*SR);mix[:len(a)]=a
rng=np.random.default_rng(20261114)
# Air textures underline editorial scale/direction changes, not literal adhesion physics.
events=[(11.08,.25),(26.59,.18),(33.2,.24)]
for t,duration in events:
 n=round(duration*SR);noise=rng.normal(0,1,n);filtered=np.convolve(noise,np.ones(13)/13,mode='same');env=np.sin(np.linspace(0,np.pi,n))**2
 effect=filtered*env*.012;start=round(t*SR);mix[start:start+n]+=effect
assert np.max(np.abs(mix))<1
raw=OUT/'dialogue-texture-premaster.wav'
with wave.open(str(raw),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((mix*32767).astype('<i2').tobytes())
ff=imageio_ffmpeg.get_ffmpeg_exe()
first=subprocess.run([ff,'-hide_banner','-i',str(raw),'-af','loudnorm=I=-16:TP=-2:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
match=re.search(r'\{\s*"input_i".*?\}',first.stderr,re.S);assert match;stats=json.loads(match.group())
fil='loudnorm=I=-16:TP=-2:LRA=7:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true:print_format=json'.format(**stats)
master=OUT/'sound-draft-v1.wav'
subprocess.run([ff,'-v','error','-y','-i',str(raw),'-af',fil,'-ar','48000','-ac','2','-c:a','pcm_s16le',str(master)],check=True)
check=subprocess.run([ff,'-hide_banner','-i',str(master),'-af','loudnorm=I=-16:TP=-2:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);out=json.loads(re.search(r'\{\s*"input_i".*?\}',check.stderr,re.S).group())
receipt={'file':str(master),'sha256':hashlib.sha256(master.read_bytes()).hexdigest(),'seconds':66,'sample_rate':48000,'channels':2,'provenance':'selected voice09 + original deterministic noise textures; noBGM/externalSFX','events':[{'time':t,'duration':n,'role':'quiet editorial transition,not literal adhesive sound'} for t,n in events],'loudnorm_input_measurements':stats,'master_measured_lufs':float(out['input_i']),'master_measured_true_peak_db':float(out['input_tp']),'listening_QC':'NOT performed; pronunciation,prosody,seam and effects balance remain open','status':'technical mastered draft only'}
assert -17<float(out['input_i'])<-15 and float(out['input_tp'])<=-1.8
Path('research/monarch_cam_gecko_batch4/SOUND_DRAFT_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
