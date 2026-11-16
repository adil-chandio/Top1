import unittest
from analyze import metrics

class MetricsTests(unittest.TestCase):
    def test_empty(self):
        self.assertIsNone(metrics([])['median_views'])
    def test_missing_is_not_zero(self):
        self.assertEqual(metrics([{}, {'view_count': 100}])['median_views'],100)
    def test_zero_is_valid(self):
        self.assertEqual(metrics([{'view_count':0}])['n_with_views'],1)
    def test_even_median(self):
        self.assertEqual(metrics([{'view_count':v} for v in [1,3,7,9]])['median_views'],5)
    def test_outlier_concentration(self):
        self.assertAlmostEqual(metrics([{'view_count':v} for v in [90,9,1]])['top_two_share'],.99)
    def test_million_threshold(self):
        self.assertEqual(metrics([{'view_count':v} for v in [999999,1000000]])['million_count'],1)
if __name__=='__main__':unittest.main()
