import base64
import math
from pathlib import Path
import tempfile
import unittest
from build_claw_motion_proxy import build, sample, EVENTS


class MotionProxyTests(unittest.TestCase):
    def test_event_order(self):
        self.assertLess(EVENTS['closure_start'], EVENTS['closure_end'])
        self.assertLessEqual(EVENTS['closure_end'], EVENTS['jet_start'])
        self.assertLess(EVENTS['jet_start'], EVENTS['cavity_start'])
        self.assertLess(EVENTS['cavity_start'], EVENTS['collapse'])

    def test_hinge_rotates_and_closes(self):
        self.assertAlmostEqual(sample(0)[0], .85)
        self.assertAlmostEqual(sample(1)[0], 0)
        angles = [sample(i/120)[0] for i in range(121)]
        self.assertTrue(all(a>=b for a,b in zip(angles,angles[1:])))

    def test_cavity_precedes_pressure_marker(self):
        self.assertGreater(sample(1.4)[2], .5)
        self.assertEqual(sample(1.4)[3], .001)
        self.assertEqual(sample(EVENTS['collapse'])[2], .001)
        self.assertGreater(sample(EVENTS['collapse'])[3], .001)

    def test_finite_nonnegative_scales(self):
        for i in range(361):
            self.assertTrue(all(math.isfinite(x) for x in sample(i/120)))
            self.assertTrue(all(x>0 for x in sample(i/120)[1:]))

    def test_serialization_and_hierarchy(self):
        with tempfile.TemporaryDirectory() as temp:
            doc=build(Path(temp)/'proxy.gltf')
            data=base64.b64decode(doc['buffers'][0]['uri'].split(',')[1])
            self.assertEqual(len(data),doc['buffers'][0]['byteLength'])
            for v in doc['bufferViews']:
                self.assertEqual(v['byteOffset']%4,0)
                self.assertLessEqual(v['byteOffset']+v['byteLength'],len(data))
            hinge=next(n for n in doc['nodes'] if n['name']=='Dactyl hinge')
            self.assertEqual(len(hinge['children']),1)
            self.assertEqual(len(doc['animations'][0]['channels']),4)
            self.assertFalse(doc['extras']['production_approved'])


if __name__=='__main__':
    unittest.main()
