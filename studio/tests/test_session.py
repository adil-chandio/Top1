import datetime as dt,hashlib,json,tempfile,unittest
from pathlib import Path
from studio.pipeline import create,save
from studio.session import step,submit
class SessionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.base=Path(self.tmp.name);self.job=create(self.base,'monarch_cam','Session fixture only')
 def state(self):return json.loads((self.job/'state.json').read_text())
 def candidate(self):
  p=self.job/'fixture.txt';p.write_text('Test evidence, not actual research')
  return {'status':'complete','paid_spend':False,'research':{'checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),'question':'Test?','decision':'Fixture decision','sources':[{'url':'https://example.org','finding':'Synthetic fixture only'}]},'artifacts':[{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}
 def worker(self):
  self.assertEqual(step(self.job),'awaiting_worker');result=self.candidate()
  submit(self.job,result,'test-author',['synthetic-test-data'])
  self.assertEqual(step(self.job),'awaiting_reviewer');return result
 def test_missing_runtime_replaced_by_real_pending_task(self):
  self.assertEqual(step(self.job),'awaiting_worker')
  s=self.state();self.assertTrue(Path(s['pending_task']['request']).is_file());self.assertEqual(s['stage'],0)
 def test_waiting_does_not_consume_retry_budget(self):
  for _ in range(5):step(self.job)
  s=self.state();self.assertEqual(s['attempts']['intelligence'],1);self.assertEqual(s['revision_attempts']['intelligence'],1)
 def test_distinct_review_advances(self):
  r=self.worker();submit(self.job,{'approved':True,'inspected_artifacts':[r['artifacts'][0]['sha256']],'findings':'Synthetic fixture bytes checked'},'test-reviewer',['byte-inspection'],True)
  self.assertEqual(step(self.job),'queued');s=self.state();self.assertEqual(s['stage'],1);self.assertNotIn('pending_task',s)
 def test_same_executor_cannot_approve(self):
  r=self.worker();submit(self.job,{'approved':True},'test-author',['test'],True)
  self.assertEqual(step(self.job),'queued');self.assertEqual(self.state()['stage'],0);self.assertIn('same executor',self.state()['blocker'])
 def test_no_independent_context_blocks(self):
  self.worker();submit(self.job,{'approved':True},'test-reviewer',['test'])
  step(self.job);self.assertIn('independent context',self.state()['blocker'])
 def test_bad_artifact_not_accepted(self):
  step(self.job);r=self.candidate();r['artifacts'][0]['sha256']='bad'
  submit(self.job,r,'test-author',['test']);step(self.job)
  self.assertEqual(self.state()['stage'],0);self.assertIn('hash mismatch',self.state()['blocker'])
 def test_request_tamper_rejected(self):
  step(self.job);task=self.state()['pending_task'];Path(task['request']).write_text('{}')
  with self.assertRaises(ValueError):submit(self.job,self.candidate(),'test-author',['test'])
 def test_no_overwrite_of_submission(self):
  step(self.job);r=self.candidate();submit(self.job,r,'test-author',['test'])
  with self.assertRaises(ValueError):submit(self.job,r,'test-author',['test'])
 def test_waiting_job_owns_queue(self):
  step(self.job);other=create(self.base,'monarch_cam','Second fixture')
  self.assertEqual(step(other),'paused_previous_video')
 def test_failing_review_new_attempt_folder(self):
  self.worker();submit(self.job,{'approved':False,'findings':'Need correction'},'test-reviewer',['test'],True)
  step(self.job);step(self.job)
  self.assertTrue((self.job/'intelligence-2/request.json').is_file());self.assertTrue((self.job/'intelligence-1/result.json').is_file())
