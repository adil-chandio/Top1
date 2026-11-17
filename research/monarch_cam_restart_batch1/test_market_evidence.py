"""Offline integrity checks; cannot certify science, viewing quality, or audience causality."""
import datetime,json,statistics,unittest
from pathlib import Path
P=Path(__file__).parent
class EvidenceTests(unittest.TestCase):
 def test_primary_inventory(self):
  rows=[]
  for f in ['ANIMAL_PERFORMANCE_COHORTS.json','ADDITIONAL_PRIMARY_COHORTS.json','CONTEXTUAL_PRIMARY_CONTROLS.json','BIZARRE_BEASTS_CURRENT_COHORT.json','TIERZOO_PRIMARY_CONTROLS.json']:
   j=json.loads((P/f).read_text());rows.extend([r for c in j['cohorts'] for r in c['rows']] if 'cohorts' in j else j['rows'])
  self.assertEqual(len(rows),46);self.assertEqual(len({r['id'] for r in rows}),46)
  self.assertEqual(sum(bool(r.get('thumbnail_inspected')) for r in rows),17)
  for r in rows:
   self.assertLessEqual(datetime.date.fromisoformat(r['upload_date']),datetime.date(2026,11,14))
   self.assertTrue(r['url'].endswith(r['id']))
 def test_additional_medians(self):
  for c in json.loads((P/'ADDITIONAL_PRIMARY_COHORTS.json').read_text())['cohorts']:
   eligible=[r for r in c['rows'] if r['sample_median_ratio'] is not None]
   self.assertEqual(c['median_views'],statistics.median(r['views'] for r in eligible))
   for r in eligible:self.assertEqual(r['sample_median_ratio'],round(r['views']/c['median_views'],3))
 def test_strands(self):
  j=json.loads((P/'BIZARRE_BEASTS_CURRENT_COHORT.json').read_text())
  for c in j['strand_comparisons']:
   rr=[r for r in j['rows'] if r['strand']==c['strand'] and r['in_mature_window']]
   self.assertEqual(len(rr),c['n_mature']);self.assertEqual(statistics.median(r['views_snapshot'] for r in rr),c['median_views'])
 def test_inspection_provenance_and_local_cleanup(self):
  j=json.loads((P/'THUMBNAIL_INSPECTION_REGISTER.json').read_text());notes=(P/j['notes']).read_text()
  self.assertEqual(len(j['rows']),17)
  self.assertEqual(len(list(Path('studio/runtime/market-thumbnails').glob('*.jpg'))),0)
  for r in j['rows']:
   self.assertIn(r['id'],notes);self.assertTrue(r['actual_image_opened']);self.assertTrue(r['local_copy_deleted'])
   self.assertEqual(len(r['source_sha256']),64);self.assertEqual(len(r['inspection_copy_sha256']),64)
 def test_secondary_sources(self):
  j=json.loads((P/'SECONDARY_PLATFORM_EVIDENCE.json').read_text())
  self.assertEqual(len(j['instagram']['rows']),3);self.assertEqual(len(j['tiktok']['rows']),4)
  for r in j['tiktok']['rows']:self.assertIn(r['id'],r['url'])
if __name__=='__main__':unittest.main()
