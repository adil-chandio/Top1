import unittest,json,sys,math
from pathlib import Path
sys.path.insert(0,str(Path('research/monarch_cam_gecko_batch2').resolve()))
from toe_cycle_geometry import surface,centerline,contact_flags,LENGTH,RINGS
class MotionChecks(unittest.TestCase):
 def test_fractional_poses_no_penetration(self):
  for i in range(180):self.assertGreaterEqual(min(v[2] for v in surface(30+30*i/179)),0)
 def test_contact_prefix_and_monotonic_release(self):
  prev=RINGS
  for i in range(180):
   flags=contact_flags(30+30*i/179)
   self.assertEqual(flags,sorted(flags,reverse=True));self.assertLessEqual(sum(flags),prev);prev=sum(flags)
  self.assertEqual(prev,0)
 def test_centerline_length_stays_fixed(self):
  for i in range(180):
   c=centerline(30+30*i/179)
   self.assertAlmostEqual(sum(math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(c,c[1:])),LENGTH,places=9)
 def test_sound_technical_measurements_only(self):
  r=json.loads(Path('research/monarch_cam_gecko_batch4/SOUND_DRAFT_RECEIPT.json').read_text())
  self.assertLessEqual(r['master_measured_true_peak_db'],-1.8);self.assertTrue(-17<r['master_measured_lufs']<-15)
  self.assertIn('NOT performed',r['listening_QC'])
if __name__=='__main__':unittest.main()
