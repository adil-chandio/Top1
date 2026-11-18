import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio.pipeline import create,save,tick
from studio.connector_delivery import prepare,finalize
class ConnectorTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.job=create(Path(t.name),'monarch_cam','Connector test')
  video=self.job/'test.mp4';video.write_bytes(b'fixture-not-real-video')
  self.sha=hashlib.sha256(video.read_bytes()).hexdigest();self.md5=hashlib.md5(video.read_bytes()).hexdigest()
  s=json.loads((self.job/'state.json').read_text());s.update(stage=8,outputs={'production':{'artifacts':[{'path':'test.mp4','sha256':self.sha}]}});save(self.job/'state.json',s)
  self.guard=patch('studio.connector_delivery.delivery_preflight');self.guard.start();self.addCleanup(self.guard.stop)
  self.decode=patch('studio.connector_delivery.subprocess.run');self.decode.start();self.addCleanup(self.decode.stop)
 def task(self):
  with patch('studio.media.ffmpeg_command',return_value='/fixture/ffmpeg'):return prepare(self.job)
 def meta(self,t):return {'id':'fixture-remote-id','name':t['name'],'parents':[t['folder']],'size':t['bytes'],'md5Checksum':t['md5']}
 def test_prepare_uses_bound_folder(self):
  t=self.task();self.assertEqual(t['folder'],json.loads((self.job/'creative_brief.json').read_text())['drive_folder_id']);self.assertEqual(tick(self.job),'awaiting_connector')
 def test_success_waits_for_user(self):
  t=self.task();r=finalize(self.job,self.meta(t),{'permissions':[{'type':'user','role':'owner'}]})
  self.assertEqual(r['sha256'],self.sha);self.assertEqual(json.loads((self.job/'state.json').read_text())['status'],'awaiting_user_evaluation')
 def test_wrong_hash_fails(self):
  t=self.task();m=self.meta(t);m['md5Checksum']='bad'
  with self.assertRaises(ValueError):finalize(self.job,m,{'permissions':[]})
 def test_wrong_folder_fails(self):
  t=self.task();m=self.meta(t);m['parents']=['wrong']
  with self.assertRaises(ValueError):finalize(self.job,m,{'permissions':[]})
 def test_public_file_fails(self):
  t=self.task()
  with self.assertRaises(ValueError):finalize(self.job,self.meta(t),{'permissions':[{'type':'anyone'}]})
 def test_incomplete_permissions_fail(self):
  t=self.task()
  with self.assertRaises(ValueError):finalize(self.job,self.meta(t),{'permissions':[],'nextPageToken':'more'})
 def test_missing_permission_evidence_fails(self):
  t=self.task()
  with self.assertRaises(ValueError):finalize(self.job,self.meta(t),{})
 def test_preflight_is_not_bypassed(self):
  with patch('studio.connector_delivery.delivery_preflight',side_effect=ValueError('real guard')):
   with self.assertRaises(ValueError):self.task()
 def test_no_repeated_finalize(self):
  t=self.task();m=self.meta(t);finalize(self.job,m,{'permissions':[]})
  with self.assertRaises(ValueError):finalize(self.job,m,{'permissions':[]})

 def test_connector_snake_case_wrapped_metadata(self):
  t=self.task();m=self.meta(t);m['md5_checksum']=m.pop('md5Checksum')
  r=finalize(self.job,{'success':True,'file':m},{'success':True,'permissions':[],'next_page_token':None})
  self.assertEqual(r['file_id'],'fixture-remote-id')
 def test_connector_failure_cannot_be_finalized(self):
  t=self.task()
  with self.assertRaises(ValueError):finalize(self.job,{'success':False,'file':self.meta(t)},{'permissions':[]})
