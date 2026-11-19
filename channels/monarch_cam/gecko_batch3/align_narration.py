#!/usr/bin/env python3
"""Transcript-constrained alignment, not an independent speech verification."""
import json,re,subprocess,tempfile,wave,os
from pathlib import Path
from pocketsphinx import Decoder
P=Path(__file__).resolve().parent
text=(P/'CAPTIONS_V2_ESTIMATED.srt').read_text().strip()
blocks=text.split('\n\n'); captions=[' '.join(b.splitlines()[2:]) for b in blocks]
def normalize(text):
 text=text.lower().replace('—',' ').replace('hair-like','hair like')
 return re.findall(r"[a-z]+(?:'[a-z]+)?",text)
sets=[captions[:6],captions[6:12],captions[12:]]
starts=[0,20.32,41.04]; results=[]; allc=[]
def stamp(t):
 ms=max(0,round(t*1000));h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
for i,group in enumerate(sets,1):
 d=Decoder(samprate=16000,loglevel='ERROR')
 for word,phone in {'tokay':'T OW K EY','setae':'S IY T IY','waals':'W AA L Z','hyperextension':'HH AY P ER IH K S T EH N SH AH N',"gecko's":'G EH K OW Z'}.items():d.add_word(word,phone)
 tokens=[w for c in group for w in normalize(c)]
 missing=sorted(set(w for w in tokens if not d.lookup_word(w)))
 if missing:raise RuntimeError(f'Missing pronunciation {missing}')
 d.set_align_text(' '.join(tokens));f=P/'audio'/f'narration-part-{i}.wav'
 with tempfile.NamedTemporaryFile(suffix='.wav') as tmp:
  subprocess.run([os.environ.get('FFMPEG','ffmpeg'),'-v','error','-y','-i',str(f),'-ar','16000','-ac','1','-c:a','pcm_s16le',tmp.name],check=True)
  with wave.open(tmp.name,'rb') as inp:data=inp.readframes(inp.getnframes())
 d.start_utt();d.process_raw(data,False,True);d.end_utt()
 segments=[s for s in d.seg() if not s.word.startswith('<') and not s.word.startswith('[')]
 if len(segments)!=len(tokens):raise RuntimeError(f'part {i}: alignment produced {len(segments)} words expected {len(tokens)}')
 words=[{'word':token,'start':round(starts[i-1]+s.start_frame/100,2),'end':round(starts[i-1]+(s.end_frame+1)/100,2)} for token,s in zip(tokens,segments)]
 results.extend(words);j=0
 for c in group:
  n=len(normalize(c));a,b=words[j]['start'],words[j+n-1]['end'];j+=n
  if b<=a:raise RuntimeError(f'invalid cue {c}')
  allc.append({'start':a,'end':b,'text':c})
for a,b in zip(allc,allc[1:]):
 if a['end']>b['start']:raise RuntimeError('Overlapping cues')
# retain original line breaks from draft
out=[]
for i,(b,c) in enumerate(zip(blocks,allc),1):
 txt='\n'.join(b.splitlines()[2:]);out.append(f"{i}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{txt}\n")
(P/'CAPTIONS_V2_ALIGNED_DRAFT.srt').write_text('\n'.join(out))
(P/'ALIGNMENT_V2.json').write_text(json.dumps({'method':'PocketSphinx transcript-constrained alignment on three 16 kHz conversions; manual dictionary entries for technical terms','not_independent_transcription':True,'accuracy':'approximate; no listening, pronunciation or caption-sync certification','words':results,'cues':allc},indent=2)+'\n')
print('Aligned',len(results),'words and',len(allc),'cues; inspect timing before use.')
