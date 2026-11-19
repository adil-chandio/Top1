#!/usr/bin/env python3
"""Join three narration takes and build approximate captions, without time-stretching."""
from pathlib import Path
import wave, hashlib, json, re
P=Path(__file__).resolve().parent
parts=[P/'audio'/f'narration-part-{i}.wav' for i in range(1,4)]
chunks=[['A gecko can hold onto a wall.','So how does it let go\nwith every step?',"The secret isn't just a strong grip.","It's how that grip is controlled.","Under a Tokay gecko's toes are tiny,\nhair-like structures called setae.","Their branching tips make extremely\nclose contact with the surface."],["They aren't suction cups.","At that tiny scale, van der Waals\nforces help those tips adhere.",'But direction matters.','A pull toward the base of the toe,\nalong the surface, helps support the grip.','To release, a gecko can curl\nits toes away from the surface.','This movement helps the foot detach.'],['That toe movement is called\ndigital hyperextension.',"Don't confuse it with the angles\nof the microscopic hairs beneath it.","So a gecko doesn't simply\nyank its foot off the wall.",'Close contact, the direction of loading,\nand controlled toe movement','work together to make gripping\nand letting go possible.']]
blobs=[];rate=None;offset=0;times=[];params=None
for p in parts:
 with wave.open(str(p),'rb') as w:
  shape=(w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getcomptype());assert params is None or params==shape;params=shape;rate=w.getframerate();data=w.readframes(w.getnframes());dur=w.getnframes()/rate;times.append({'file':p.name,'start':offset,'duration':dur,'end':offset+dur,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});offset+=dur;blobs.append(data)
out=P/'audio'/'gecko-narration-v2.wav'
with wave.open(str(out),'wb') as w:
 w.setnchannels(params[0]);w.setsampwidth(params[1]);w.setframerate(rate);w.writeframes(b''.join(blobs))
def stamp(t):
 ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
# Weighted estimates within each recorded part; not forced alignment or actual word timing.
srt=[];n=1
for part,ps in zip(chunks,times):
 weights=[len(re.sub(r'\s+',' ',v).strip()) for v in part];total=sum(weights);elapsed=0
 for line,weight in zip(part,weights):
  a=ps['start']+ps['duration']*elapsed/total;elapsed+=weight;b=ps['start']+ps['duration']*elapsed/total
  srt.append(f'{n}\n{stamp(a)} --> {stamp(b)}\n{line}\n');n+=1
(P/'CAPTIONS_V2_ESTIMATED.srt').write_text('\n'.join(srt))
manifest={'voice':'voice-00 (selected in this session)','script':'SCRIPT_REVISED_ENGLISH.md','sample_rate_hz':rate,'channels':params[0],'parts':times,'duration_seconds':offset,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'caption_timing':'Character-weighted estimates within each measured clip, not acoustic alignment','assistant_listening':'not performed','spelling_note':'Narration uses spoken words and omits typographic dashes in final sentence.'}
(P/'NARRATION_V2_RECEIPT.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
