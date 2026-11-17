import copy,hashlib,tempfile,unittest
from pathlib import Path
from studio.release_gate import check,REQUIRED
class ReleaseTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  (self.root/'fixture').write_text('test evidence, not actual creative approval')
  self.m={'channel':'monarch_cam','ready_for_full_render':True,'gates':dict.fromkeys(REQUIRED,True),'evidence':[{'gate':k,'path':'fixture','sha256':hashlib.sha256((self.root/'fixture').read_bytes()).hexdigest()} for k in REQUIRED]}
 def test_complete_contract(self):self.assertTrue(check(self.m,self.root))
 def test_not_ready_rejects(self):
  self.m['ready_for_full_render']=False
  with self.assertRaises(ValueError):check(self.m,self.root)
 def test_sound_not_skipped(self):
  self.m['gates']['sound_listening_review']=False
  with self.assertRaises(ValueError):check(self.m,self.root)
 def test_editing_evidence_required(self):
  self.m['evidence']=[e for e in self.m['evidence'] if e['gate']!='editing_blueprint']
  with self.assertRaises(ValueError):check(self.m,self.root)
 def test_tampering_rejected(self):
  (self.root/'fixture').write_text('changed')
  with self.assertRaises(ValueError):check(self.m,self.root)
