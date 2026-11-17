import json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class TimingTests(unittest.TestCase):
 def test_word_timestamps_bounded_and_ordered(self):
  j=json.loads((ROOT/'ENGLISH_WORD_ALIGNMENT.json').read_text());last=0
  for w in j['words']:
   self.assertLessEqual(last,w['start']);self.assertLess(w['start'],w['end']);self.assertLessEqual(w['end'],j['duration']);last=w['end']
 def test_captions_cover_transcript_once(self):
  a=json.loads((ROOT/'ENGLISH_WORD_ALIGNMENT.json').read_text())['words'];c=json.loads((ROOT/'ENGLISH_CAPTION_CUES.json').read_text())['cues']
  actual=[re.sub(r'\(\d+\)$','',w['word']) for w in a]
  expected=re.findall(r"[a-z]+(?:'[a-z]+)?",' '.join(x['text'] for x in c).lower())
  self.assertEqual(expected,actual)
 def test_caption_cues_dont_overlap(self):
  cues=json.loads((ROOT/'ENGLISH_CAPTION_CUES.json').read_text())['cues']
  for a,b in zip(cues,cues[1:]):self.assertLessEqual(a['end'],b['start'])
 def test_beat_partition_and_full_decode(self):
  j=json.loads((ROOT/'STORY_ANIMATIC_RECEIPT.json').read_text());bs=j['beat_bounds']
  self.assertEqual(bs[0][1],0);self.assertEqual(bs[-1][2],66)
  for a,b in zip(bs,bs[1:]):self.assertEqual(a[2],b[1])
  self.assertEqual(j['full_decode_exit'],0);self.assertEqual(j['full_decode_errors'],'')
if __name__=='__main__':unittest.main()
