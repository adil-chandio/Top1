import json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class CaptionReadabilityChecks(unittest.TestCase):
 def test_exact_words_and_terms(self):
  old=json.loads((ROOT.parent/'monarch_cam_gecko_batch4/REVIEW_CAPTION_CUES.json').read_text())['cues']
  new=json.loads((ROOT/'READABILITY_CAPTION_CUES.json').read_text())['cues']
  words=lambda c:re.findall(r"[a-z]+(?:'[a-z]+)?",' '.join(x['text'] for x in c).lower())
  self.assertEqual(words(old),words(new))
  for term in ['van der Waals','digital hyperextension',"They aren't suction cups."]:
   self.assertTrue(any(term in c['text'] for c in new))
 def test_readability_and_nonoverlap(self):
  cues=json.loads((ROOT/'READABILITY_CAPTION_CUES.json').read_text())['cues'];end=0
  for c in cues:
   self.assertGreaterEqual(c['start'],end);self.assertGreaterEqual(c['end']-c['start'],.7)
   self.assertLessEqual(len(c['text'])/(c['end']-c['start']),20.01);end=c['end']
  self.assertLessEqual(end,63.68)
 def test_receipt_scope_and_identical_audio(self):
  j=json.loads((ROOT/'CAPTION_READABILITY_RECEIPT.json').read_text())
  self.assertTrue(j['aac_stream_identical']);self.assertTrue(j['decoded_samples_inspected'])
  self.assertEqual(j['full_decode_exit'],0);self.assertEqual(j['caption_flags_after'],0)
  self.assertFalse(j['actual_listening']);self.assertFalse(j['final_pass'])
 def test_current_survey_identity_and_limits(self):
  j=json.loads((ROOT/'CURRENT_CANDIDATE_WHOLE_AUDIT.json').read_text())
  self.assertEqual(j['decoded_frames'],1584);self.assertEqual(len(j['sample_times_seconds']),66)
  self.assertTrue(j['sheets_actually_inspected']);self.assertFalse(j['native_playback'])
  self.assertFalse(j['listening']);self.assertFalse(j['final_pass'])
if __name__=='__main__':unittest.main()
