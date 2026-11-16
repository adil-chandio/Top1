import copy,hashlib,tempfile,unittest
from pathlib import Path
from accounts_studio.craft import verify,DEPARTMENTS
from accounts_studio.remediation import validate_repair

class CraftTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.job=Path(self.temp.name)
  (self.job/'proof.md').write_text('review fixture, not real media')
  self.r={'artifacts':[{'path':'proof.md','sha256':hashlib.sha256((self.job/'proof.md').read_bytes()).hexdigest()}], 'craft':{k:{'status':'pass','observations':'fixture findings','rationale':'fixture reason','evidence':['proof.md']} for k in DEPARTMENTS['production']},'attribution':'fixture original work'}
 def test_production_contract(self):verify(self.job,'production',self.r)
 def test_sound_cannot_be_omitted(self):
  self.r['craft']['sound_design']['status']='not_applicable'
  with self.assertRaises(ValueError):verify(self.job,'production',self.r)
 def test_typography_can_be_intentionally_omitted(self):
  self.r['craft']['typography']={'status':'not_applicable','observations':'no text needed','rationale':'avoid obscuring the scene action'};verify(self.job,'production',self.r)
 def test_report_only_feasibility_rejected(self):
  r=copy.deepcopy(self.r);r['craft']={k:{'status':'pass','observations':'fixture','rationale':'fixture','evidence':['proof.md']} for k in DEPARTMENTS['feasibility']}
  with self.assertRaises(ValueError):verify(self.job,'feasibility',r)
 def test_missing_department_rejected(self):
  del self.r['craft']['compositing']
  with self.assertRaises(ValueError):verify(self.job,'production',self.r)
 def test_unlisted_evidence_rejected(self):
  self.r['craft']['music']['evidence']=['elsewhere.md']
  with self.assertRaises(ValueError):verify(self.job,'production',self.r)
 def test_changed_evidence_rejected(self):
  (self.job/'proof.md').write_text('changed')
  with self.assertRaises(ValueError):verify(self.job,'production',self.r)

class RepairTests(unittest.TestCase):
 def candidate(self):
  return {'status':'complete','paid_spend':False,'problem':'mask geometry mismatch','acceptance_test':'measured geometry + viewed test','candidates':[{'source_url':'https://github.com/example/fixture','decision_reason':'test fixture only','selected':True,**{k:'fixture' for k in ['license_review','security_review','compatibility','version','test_evidence','comparison','rollback']},'test_passed':True}]}
 def test_valid_contract(self):validate_repair(self.candidate())
 def test_no_untested_solution(self):
  r=self.candidate();r['candidates'][0]['test_passed']=False
  with self.assertRaises(ValueError):validate_repair(r)
 def test_no_unbounded_shortlist(self):
  r=self.candidate();r['candidates']*=4
  with self.assertRaises(ValueError):validate_repair(r)
 def test_license_required(self):
  r=self.candidate();del r['candidates'][0]['license_review']
  with self.assertRaises(ValueError):validate_repair(r)
 def test_rollback_required(self):
  r=self.candidate();del r['candidates'][0]['rollback']
  with self.assertRaises(ValueError):validate_repair(r)
