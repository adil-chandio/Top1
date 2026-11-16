import datetime as dt,hashlib,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio.pipeline import create,validate,tick,NOW

class PipelineTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.job=create(self.temp.name,'monarch_cam','20-second pilot, no final-film authorization')
  self.p=self.job/'evidence.md';self.p.write_text('real evidence')
 def result(self):
  return {'status':'complete','paid_spend':False,'research':{'checked_at':NOW().isoformat(),'question':'Which model?','decision':'Reject unlicensed asset','sources':[{'url':'https://github.com/example/source','finding':'test fixture, not real research'}]},'artifacts':[{'path':'evidence.md','sha256':hashlib.sha256(self.p.read_bytes()).hexdigest()}]}
 def test_other_channel_paused(self):
  other=create(self.temp.name,'extinct_life','do not start before user approves channel switch')
  self.assertEqual(tick(other),'paused_other_channel')
  state=json.loads((other/'state.json').read_text())
  self.assertEqual(state['stage'],0);self.assertEqual(state['attempts'],{})
 def test_valid_research(self):validate(self.job,'story',self.result())
 def test_missing_research(self):
  r=self.result();r['research']['sources']=[]
  with self.assertRaises(ValueError):validate(self.job,'story',r)
 def test_stale_research(self):
  r=self.result();r['research']['checked_at']=(NOW()-dt.timedelta(days=5)).isoformat()
  with self.assertRaises(ValueError):validate(self.job,'script',r)
 def test_path_escape(self):
  r=self.result();r['artifacts'][0]['path']='../outside'
  with self.assertRaises(ValueError):validate(self.job,'story',r)
 def test_mutated_artifact(self):
  r=self.result();self.p.write_text('changed')
  with self.assertRaises(ValueError):validate(self.job,'story',r)
 def test_quality_fail(self):
  with self.assertRaises(ValueError):validate(self.job,'feasibility',self.result())
 def test_no_runtime_blocks(self):
  with patch.dict(os.environ,{},clear=True):self.assertEqual(tick(self.job),'blocked')
 def test_independent_review_required(self):
  with patch.dict(os.environ,{'STUDIO_WORKER_COMMAND':'python worker.py','STUDIO_REVIEWER_COMMAND':'python worker.py'},clear=True):self.assertEqual(tick(self.job),'blocked')
 def test_retry_budget(self):
  with patch.dict(os.environ,{'STUDIO_WORKER_COMMAND':'worker','STUDIO_REVIEWER_COMMAND':'reviewer'},clear=True),patch('studio.pipeline.invoke',side_effect=ValueError('rejected')):
   self.assertEqual(tick(self.job),'queued');self.assertEqual(tick(self.job),'queued');self.assertEqual(tick(self.job),'blocked')
 def test_accepted_stage_advances(self):
  r=self.result();review={'approved':True,'inspected_artifacts':[r['artifacts'][0]['sha256']],'findings':'fixture inspected'}
  with patch.dict(os.environ,{'STUDIO_WORKER_COMMAND':'worker','STUDIO_REVIEWER_COMMAND':'reviewer'},clear=True),patch('studio.pipeline.invoke',side_effect=[r,review]):tick(self.job)
  self.assertEqual(json.loads((self.job/'state.json').read_text())['stage'],1)
 def test_wrong_review_hash_rejected(self):
  with patch.dict(os.environ,{'STUDIO_WORKER_COMMAND':'worker','STUDIO_REVIEWER_COMMAND':'reviewer'},clear=True),patch('studio.pipeline.invoke',side_effect=[self.result(),{'approved':True,'inspected_artifacts':['wrong'],'findings':'fixture'}]):tick(self.job)
  self.assertEqual(json.loads((self.job/'state.json').read_text())['stage'],0)
if __name__=='__main__':unittest.main()
