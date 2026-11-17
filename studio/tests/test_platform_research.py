import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio.platform_research import video_url,channel_url,metadata,discover,baseline,import_evidence,packet,sample,observation,verify_bundle,digest
class PlatformTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
 def test_canonical_video(self):
  for value in ('W9KfHky9sMo','https://youtu.be/W9KfHky9sMo?t=2','https://www.youtube.com/shorts/W9KfHky9sMo'):
   self.assertEqual(video_url(value),'https://www.youtube.com/watch?v=W9KfHky9sMo')
 def test_unsafe_urls_rejected(self):
  for x in ('http://youtube.com/watch?v=W9KfHky9sMo','https://youtube.com.evil.test/watch?v=W9KfHky9sMo','https://youtube.com@evil.test/watch?v=W9KfHky9sMo','https://127.0.0.1/a','--exec','https://youtube.com/playlist?list=x'):
   with self.assertRaises(ValueError):video_url(x)
 def test_channel_separate_formats(self):
  self.assertEqual(channel_url('https://www.youtube.com/@saveourseas','shorts'),'https://www.youtube.com/@saveourseas/shorts')
 def test_channel_unsafe(self):
  with self.assertRaises(ValueError):channel_url('https://evil.test/@foo')
 def test_metadata_never_viewing(self):
  r=metadata({'id':'W9KfHky9sMo','formats':[{'url':'secret-signed-url'}]})
  self.assertEqual(r['access'],'metadata_only');self.assertNotIn('formats',r['data'])
 def test_discovery_bounded(self):
  with self.assertRaises(ValueError):discover('whales',21)
 def test_discovery_actual_adapter_arguments(self):
  with patch('studio.platform_research.ytdlp',return_value={'entries':[{'id':'W9KfHky9sMo','title':'Fixture'}]}) as tool:
   r=discover('whales',3);self.assertEqual(len(r['candidates']),1);self.assertIn('ytsearch3:whales',tool.call_args.args[0])
 def target(self):return {'id':'target','channel_id':'channel','format':'long','age_band':'30-90d','views':1000}
 def cohort(self):return [{**self.target(),'id':str(i),'views':100} for i in range(5)]
 def test_baseline_comparable_only(self):
  self.assertEqual(baseline(self.target(),self.cohort())['relative_views'],10)
 def test_baseline_insufficient(self):
  with self.assertRaises(ValueError):baseline(self.target(),self.cohort()[:4])
 def test_baseline_no_mixed_format(self):
  rows=self.cohort();rows[0]['format']='short'
  with self.assertRaises(ValueError):baseline(self.target(),rows)
 def test_baseline_no_duplicate_samples(self):
  with self.assertRaises(ValueError):baseline(self.target(),[self.cohort()[0]]*5)
 def test_capture_does_not_upgrade_access(self):
  src=self.root/'actual.txt';src.write_text('Synthetic captured page text fixture')
  r=import_evidence(self.root/'capture','W9KfHky9sMo',src,'page_text','fixture','topic_winner')
  self.assertFalse(r['viewed_video']);self.assertFalse(r['listened_audio']);self.assertEqual(r['sha256'],digest(src))
 def test_capture_fake_video_label_rejected(self):
  with self.assertRaises(ValueError):import_evidence(self.root,'W9KfHky9sMo','no-file','video','fixture','topic_winner')
 def test_every_stage_gets_tools(self):
  for s in ('intelligence','idea','story','script','feasibility','production','qc','packaging','delivery'):
   self.assertIn('acquire',packet(s)['tools']);self.assertEqual(packet(s)['priority'][0],'youtube_long')
 def test_segment_bounds(self):
  with self.assertRaises(ValueError):sample('missing',self.root,'W9KfHky9sMo',0,61,'fixture')
 def fixture(self):
  (self.root/'segment.mp4').write_bytes(b'synthetic fixture, not actual video')
  (self.root/'audio.wav').write_bytes(b'synthetic fixture, not actual audio')
  m={'url':video_url('W9KfHky9sMo'),'source_start':20,'duration_requested':5,'duration_actual':4.9,'audio_extracted':True,'files':[{'path':x,'sha256':digest(self.root/x)} for x in ('segment.mp4','audio.wav')]}
  (self.root/'media_evidence.json').write_text(json.dumps(m))
  return {'executor':'fixture-reviewer','mode':'combined','start':0,'end':4,'observation':'Fixture observation, not real review','interpretation':'Fixture','application':'Fixture decision','do_not_copy':'No reference assets','method':'fixture-only','actually_inspected':True}
 def test_timestamp_binding(self):
  r=observation(self.root,self.fixture());self.assertEqual(r['source_start'],20);self.assertEqual(r['source_end'],24)
 def test_text_not_av(self):
  n=self.fixture();n['method']='transcript'
  with self.assertRaises(ValueError):observation(self.root,n)
 def test_timestamp_outside_media(self):
  n=self.fixture();n['end']=5
  with self.assertRaises(ValueError):observation(self.root,n)
 def test_tampered_media_blocks_observation(self):
  n=self.fixture();(self.root/'segment.mp4').write_bytes(b'changed')
  with self.assertRaises(ValueError):observation(self.root,n)
 def test_missing_audio_blocks_listening(self):
  n=self.fixture();p=self.root/'media_evidence.json';m=json.loads(p.read_text());m['audio_extracted']=False;p.write_text(json.dumps(m))
  with self.assertRaises(ValueError):observation(self.root,n)
 def test_bundle_required_for_strict_brief(self):
  (self.root/'creative_brief.json').write_text(json.dumps({'platform_reference_policy':{'require_av_before_production':True}}))
  with self.assertRaises(ValueError):verify_bundle(self.root,'feasibility',{'artifacts':[]})
 def test_valid_synthetic_bundle_contract(self):
  observation(self.root,self.fixture())
  (self.root/'creative_brief.json').write_text(json.dumps({'platform_reference_policy':{'require_av_before_production':True}}))
  r={'platform_references':[{'lane':'adjacent_craft','format':'youtube_long','selection_reason':'Fixture','applied_decision':'Fixture','media_manifest':'media_evidence.json','observations':'observations.json'}],'artifacts':[{'path':p.name,'sha256':digest(p)} for p in self.root.iterdir() if p.is_file()]}
  verify_bundle(self.root,'feasibility',r)
 def test_metadata_only_cannot_satisfy_bundle(self):
  self.test_valid_synthetic_bundle_contract();p=self.root/'observations.json';p.write_text('[]')
  r={'platform_references':[{'lane':'topic_winner','format':'youtube_long','selection_reason':'Fixture','applied_decision':'Fixture','media_manifest':'media_evidence.json','observations':'observations.json'}],'artifacts':[{'path':p.name,'sha256':digest(p)} for p in self.root.iterdir() if p.is_file()]}
  with self.assertRaises(ValueError):verify_bundle(self.root,'production',r)

 def test_observation_rejects_path_escape(self):
  n=self.fixture();p=self.root/'media_evidence.json';m=json.loads(p.read_text());m['files'][0]['path']='../outside';p.write_text(json.dumps(m))
  with self.assertRaises(ValueError):observation(self.root,n)
 def test_new_worker_request_includes_platform_tools(self):
  from studio.pipeline import create
  from studio.session import step
  job=create(self.root/'jobs','monarch_cam','Synthetic platform packet fixture')
  self.assertEqual(step(job),'awaiting_worker')
  r=json.loads((job/'intelligence-1/request.json').read_text())
  self.assertIn('acquire',r['platform_research']['tools']);self.assertTrue(r['creative_brief']['platform_reference_policy']['require_av_before_production'])
