import hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio.pipeline import create,tick,save,ROOT,CONFIG
from studio.lifecycle import select_job,feedback,validate_upstream
class LifecycleTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
  self.job=create(self.base,'monarch_cam','Fixture opening scope')
 def load(self):return json.loads((self.job/'state.json').read_text())
 def write(self,s):save(self.job/'state.json',s)
 def delivery(self):
  s=self.load();s['status']='awaiting_user_evaluation';s['delivery']={'link':'https://example.org/fixture'}
  s['outputs']={'script':{'artifacts':[]},'production':{'artifacts':[{'path':'old.mp4','sha256':'oldhash'}]},'qc':{'artifacts':[]},'packaging':{'artifacts':[]}}
  s['accepted_reviews']={'production':{'path':'review','sha256':'fixture'},'qc':{}};s['attempts']={'feasibility':2};self.write(s)
 def test_one_unfinished_job_owns_channel(self):
  other=create(self.base,'monarch_cam','Later job')
  self.assertEqual(select_job(self.base,'monarch_cam'),self.job)
  self.assertEqual(tick(other),'paused_previous_video')
 def test_awaiting_user_blocks_later_job(self):
  self.delivery();create(self.base,'monarch_cam','Later job')
  self.assertIsNone(select_job(self.base,'monarch_cam'))
 def test_blocked_first_job_does_not_skip_to_next(self):
  s=self.load();s['status']='blocked';self.write(s);create(self.base,'monarch_cam','Later')
  self.assertIsNone(select_job(self.base,'monarch_cam'))
 def test_accept_requires_delivered(self):
  with self.assertRaises(ValueError):feedback(self.job,'accept','fixture')
 def test_accept_does_not_switch_channel(self):
  self.delivery();feedback(self.job,'accept','User explicitly accepted fixture')
  self.assertEqual(self.load()['status'],'accepted');self.assertEqual(CONFIG['active_channel'],'monarch_cam')
 def test_rejection_invalidates_downstream(self):
  self.delivery();s=feedback(self.job,'reject','Captions and sound rejected')
  self.assertEqual(s['stage'],CONFIG['stages'].index('feasibility'))
  self.assertNotIn('production',s['outputs']);self.assertNotIn('qc',s['accepted_reviews'])
  self.assertIn('script',s['outputs']);self.assertNotIn('delivery',s)
  self.assertIn('oldhash',s['rejected_video_hashes']);self.assertTrue(s['user_rejected'])
 def test_rework_preserves_history_and_attempt_paths(self):
  self.delivery();s=feedback(self.job,'revise','Need new approach')
  self.assertEqual(s['attempts']['feasibility'],2);self.assertEqual(s['revision_attempts'],{})
  self.assertEqual(s['revisions'][0]['delivery']['link'],'https://example.org/fixture')
 def test_feedback_not_allowed_to_restart_after_production(self):
  self.delivery()
  with self.assertRaises(ValueError):feedback(self.job,'revise','Fix','qc')
 def test_brief_snapshot_tamper_blocks(self):
  s=self.load();(self.job/'creative_brief.json').write_text('{}')
  with self.assertRaises(ValueError):validate_upstream(self.job,s)
 def test_delivered_state_not_reexecuted(self):
  self.delivery();self.assertEqual(tick(self.job),'awaiting_user_evaluation')
 def test_real_fixture_subprocesses_advance_one_stage(self):
  fixture=ROOT/'studio/tests/fixture_runtime.py'
  env={'STUDIO_WORKER_COMMAND':f'{sys.executable} {fixture} --role worker','STUDIO_REVIEWER_COMMAND':f'{sys.executable} {fixture} --role reviewer'}
  with patch.dict(os.environ,env):self.assertEqual(tick(self.job),'queued')
  s=self.load();self.assertEqual(s['stage'],1);self.assertIn('intelligence',s['accepted_reviews'])
  request=json.loads((self.job/'intelligence-1/request.json').read_text())
  self.assertIn('creative_north_star',request['creative_brief']);self.assertEqual(request['responsibility']['owner'],'research_lead')
 def test_upstream_mutation_blocks_continuation(self):
  s=self.load();p=self.job/'a.txt';p.write_text('original');s['outputs']={'story':{'artifacts':[{'path':'a.txt','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}};p.write_text('modified')
  with self.assertRaises(ValueError):validate_upstream(self.job,s)

 def test_delivery_waits_for_user_not_auto_accept(self):
  s=self.load();s['stage']=CONFIG['stages'].index('delivery');self.write(s)
  with patch('studio.drive.deliver',return_value={'link':'https://example.org/fixture'}):
   self.assertEqual(tick(self.job),'awaiting_user_evaluation')
  self.assertNotEqual(self.load()['status'],'accepted')
