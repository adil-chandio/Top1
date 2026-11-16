"""Actual optional Node/Three integration tests; no synthetic creative approval.
Skipped in source-only environments without the recovered licensed asset/tool install.
"""
import hashlib,json,shutil,subprocess,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[2]/'research/monarch_cam_market/motion'
READY=bool(shutil.which('node') and (BASE/'out/tools/node_modules/three/package.json').exists() and (BASE/'out/orca/orca_decoded.glb').exists())
@unittest.skipUnless(READY,'optional licensed asset and Node rig tools absent')
class MetricRigIntegrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.asset=BASE/'out/orca/orca_decoded.glb';cls.before=hashlib.sha256(cls.asset.read_bytes()).hexdigest()
  for script in ('crosscheck_orca_loader.mjs','test_metric_orca_rig.mjs'):
   subprocess.run(['node',str(BASE/script)],check=True,capture_output=True,timeout=30)
  cls.native=json.loads((BASE/'out/orca/three_native_crosscheck.json').read_text());cls.metric=json.loads((BASE/'out/orca/metric_rig_test.json').read_text())
 def test_supported_loader_exposes_incompatible_legacy_skin(self):
  self.assertGreater(max(x['bbox_extent'][1] for x in self.native['samples']),100)
 def test_metric_bind_preserves_original_geometry(self):
  self.assertLess(self.metric['bind_max_error'],1e-5);self.assertEqual(self.metric['vertices'],1656)
 def test_metric_samples_bounded(self):
  self.assertEqual(len(self.metric['samples']),9)
  self.assertTrue(all(x['max_extent_ratio']<1.5 and x['max_displacement_from_bind_metres']<1 for x in self.metric['samples']))
 def test_original_asset_not_modified(self):
  self.assertEqual(self.before,hashlib.sha256(self.asset.read_bytes()).hexdigest());self.assertFalse(self.metric['biomechanics_validated']);self.assertFalse(self.metric['independent_review'])
