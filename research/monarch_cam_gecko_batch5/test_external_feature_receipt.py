import unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class ExternalFeatureReceiptChecks(unittest.TestCase):
 def setUp(self):self.j=json.loads((ROOT/'EXTERNAL_FEATURE_CORRECTION_RECEIPT.json').read_text())
 def test_claw_identities(self):
  f=self.j['external_feature_check'];self.assertEqual(f['claws'],['II','III','IV','V']);self.assertEqual(f['clawless_digit'],'I');self.assertEqual(f['shortest_digit'],'I')
 def test_no_false_anatomy_or_final_pass(self):
  self.assertFalse(self.j['final_pass']);self.assertFalse(self.j['external_feature_check']['biological_joint_validation'])
 def test_export_and_crop_bounds(self):
  self.assertEqual(self.j['full_decode_exit'],0);self.assertEqual(self.j['full_decode_errors'],'');self.assertEqual(self.j['seconds'],66)
  for box in [self.j['hero_crop'],self.j['pad_crop'],self.j['macro_crop']]:
   a,b,c,d=box;self.assertTrue(0<=a<c<=512 and 0<=b<d<=512)
if __name__=='__main__':unittest.main()
