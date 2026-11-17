import json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class ReviewCaptionChecks(unittest.TestCase):
 def test_exact_transcript_coverage(self):
  cues=json.loads((ROOT/'REVIEW_CAPTION_CUES.json').read_text())['cues']
  ws=json.loads((ROOT.parent/'monarch_cam_gecko_batch3/ENGLISH_WORD_ALIGNMENT.json').read_text())['words']
  self.assertEqual(re.findall(r"[a-z]+(?:'[a-z]+)?",' '.join(c['text'] for c in cues).lower()),[re.sub(r'\(\d+\)$','',w['word']) for w in ws])
 def test_protected_terms_not_split_between_cues(self):
  texts=[c['text'].lower() for c in json.loads((ROOT/'REVIEW_CAPTION_CUES.json').read_text())['cues']]
  for term in ['van der waals','digital hyperextension',"tokay gecko's"]:self.assertTrue(any(term in t for t in texts))
 def test_times_ordered_and_bounded(self):
  last=0
  for c in json.loads((ROOT/'REVIEW_CAPTION_CUES.json').read_text())['cues']:
   self.assertGreaterEqual(c['start'],last);self.assertGreater(c['end'],c['start']);self.assertLessEqual(c['end'],63.68);last=c['end']
 def test_export_review_remains_bounded(self):
  j=json.loads((ROOT/'REVIEW_CUT_RECEIPT.json').read_text());self.assertEqual(j['full_decode_exit'],0);self.assertFalse(j['final_pass']);self.assertEqual(j['macro_frames'],48);self.assertEqual(j['decoded_macro_check']['unique_frames'],8)
if __name__=='__main__':unittest.main()
