"""Offline transcript-constrained alignment, not independent transcription/listening QC.
Requires pocketsphinx5.1.1. OOV phone entries are alignment hints, not pronunciation approval.
"""
import audioop,json,re,wave,hashlib
from pathlib import Path
from pocketsphinx import Decoder
ROOT=Path('studio/runtime/gecko/narration')
TEXTS=["A gecko can hold onto a wall. So how does it let go with every step? The secret isn't just a strong grip. It's how that grip is controlled. Under a Tokay gecko's toes are tiny, hair-like structures called setae. Their branching tips make extremely close contact with the surface. They aren't suction cups. At that tiny scale, van der Waals forces help those tips adhere. But direction matters. A pull toward the base of the toe, along the surface, helps support the grip.","To release, the toe starts curling back at its tip. Contact progressively breaks from the tip toward the base, rather than the whole pad lifting at once. That toe movement is called digital hyperextension. Don't confuse it with the angles of the microscopic hairs beneath it. So a gecko doesn't simply yank its foot off the wall. Close contact, the direction of loading, and controlled toe movement work together to make gripping, and letting go, possible."]
words=[];offset=0
for i,text in enumerate(TEXTS,1):
 path=ROOT/f'english-part{i}.wav'
 with wave.open(str(path),'rb') as w:
  assert w.getnchannels()==1 and w.getsampwidth()==2
  dur=w.getnframes()/w.getframerate();pcm,_=audioop.ratecv(w.readframes(w.getnframes()),2,1,w.getframerate(),16000,None)
 d=Decoder(samprate=16000,loglevel='ERROR')
 for word,phones in {"gecko's":'G EH K OW Z','tokay':'T OW K EY','setae':'S IY T IY','waals':'W AA L Z','hyperextension':'HH AY P ER IH K S T EH N SH AH N'}.items():d.add_word(word,phones)
 normalized=' '.join(re.findall(r"[a-z]+(?:'[a-z]+)?",text.lower()))
 for word in normalized.split():
  if d.lookup_word(word) is None:raise RuntimeError('Missing dictionary word:'+word)
 d.set_align_text(normalized);d.start_utt();d.process_raw(pcm,full_utt=True);d.end_utt()
 for s in d.seg():
  if s.word.startswith('<') or s.word.startswith('['):continue
  words.append({'word':s.word,'start':round(offset+s.start_frame/100,3),'end':round(offset+(s.end_frame+1)/100,3),'part':i})
 offset+=dur
out={'method':'PocketSphinx5.1.1 transcript-constrained word alignment; approximate acoustic boundaries','not_independent_transcript':True,'pronunciation_QC':'not established by alignment','duration':round(offset,2),'audio_sha256':hashlib.sha256((ROOT/'english-narration-v1.wav').read_bytes()).hexdigest(),'words':words}
Path('research/monarch_cam_gecko_batch3/ENGLISH_WORD_ALIGNMENT.json').write_text(json.dumps(out,indent=2)+'\n')
print('aligned',len(words),'words; duration',offset)
