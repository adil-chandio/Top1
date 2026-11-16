import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio.guards import delivery_preflight
class GuardTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.job=Path(self.tmp.name)
  self.state={'outputs':{},'accepted_reviews':{}}
  for stage in ('production','qc','packaging'):
   path=self.job/(stage+'.mp4' if stage=='production' else stage+'.txt');path.write_text('fixture only')
   sha=hashlib.sha256(path.read_bytes()).hexdigest();result={'artifacts':[{'path':path.name,'sha256':sha}]}
   self.state['outputs'][stage]=result
   review=self.job/(stage+'-review.json');review.write_text(json.dumps({'approved':True,'inspected_artifacts':[sha]}))
   self.state['accepted_reviews'][stage]={'path':review.name,'sha256':hashlib.sha256(review.read_bytes()).hexdigest()}
  self.state['outputs']['qc']['reviewed_production_sha256']=self.state['outputs']['production']['artifacts'][0]['sha256']
 def test_valid_receipt_chain(self):
  with patch('studio.guards.production_preflight'):self.assertTrue(delivery_preflight(self.job,self.state))
 def test_render_gate_cannot_be_bypassed(self):
  with patch('studio.guards.production_preflight',side_effect=ValueError('not ready')):
   with self.assertRaises(ValueError):delivery_preflight(self.job,self.state)
 def test_missing_qc_blocks_delivery(self):
  del self.state['outputs']['qc']
  with patch('studio.guards.production_preflight'):
   with self.assertRaises(ValueError):delivery_preflight(self.job,self.state)
 def test_no_self_approved_delivery(self):
  del self.state['accepted_reviews']['qc']
  with patch('studio.guards.production_preflight'):
   with self.assertRaises(ValueError):delivery_preflight(self.job,self.state)
 def test_modified_video_blocks_delivery(self):
  (self.job/'production.mp4').write_text('different')
  with patch('studio.guards.production_preflight'):
   with self.assertRaises(ValueError):delivery_preflight(self.job,self.state)
 def test_user_rejection_blocks_delivery(self):
  self.state['user_rejected']=True
  with patch('studio.guards.production_preflight'):
   with self.assertRaises(ValueError):delivery_preflight(self.job,self.state)
 def test_modified_review_blocks_delivery(self):
  (self.job/'qc-review.json').write_text('{}')
  with patch('studio.guards.production_preflight'):
   with self.assertRaises(ValueError):delivery_preflight(self.job,self.state)
