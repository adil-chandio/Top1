import math,unittest
from toe_cycle_geometry import *

class CycleTest(unittest.TestCase):
 def test_nonpenetration_all_frames(self):
  for f in range(1,FRAMES+1):self.assertGreaterEqual(min(v[2] for v in surface(f)),0)
 def test_centerline_inextensible(self):
  for f in range(1,FRAMES+1):
   c=centerline(f)
   for a,b in zip(c,c[1:]):self.assertAlmostEqual(math.hypot(b[0]-a[0],b[1]-a[1]),LENGTH/(RINGS-1),places=10)
 def test_contact_cycle(self):
  self.assertFalse(any(contact_flags(1)))
  self.assertTrue(all(contact_flags(12)))
  self.assertTrue(all(contact_flags(30)))
  self.assertFalse(any(contact_flags(60)))
 def test_release_distal_first_monotonic(self):
  previous=RINGS
  for f in range(31,53):
   flags=contact_flags(f);count=sum(flags)
   self.assertLessEqual(count,previous);previous=count
   # Contact must be a proximal prefix; no detached island reattaches.
   self.assertEqual(flags,sorted(flags,reverse=True))
 def test_fixed_topology(self):
  self.assertTrue(all(len(surface(f))==RINGS*SIDES for f in range(1,61)))

if __name__=='__main__':unittest.main()
