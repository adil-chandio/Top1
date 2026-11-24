import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('research', BASE / 'research.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def config():
    return {
        'channels': [{'name': 'Test Channel', 'id': 'UC' + 'a' * 22}],
        'videos_per_channel': 2, 'search_results_per_query': 2,
        'science_results_per_query': 2, 'science_queries': ['dinosaur fossil'],
        'candidates': [{'id': 'sample', 'name': 'Sample', 'doi': '10.1234/test',
                        'search': 'fossil evidence', 'question': 'How did the fossil form?'}],
    }


def fake_fetch(url, key=None):
    if 'youtube/v3/channels?' in url:
        return {'items': [{'snippet': {'title': 'Test Channel'}, 'contentDetails': {'relatedPlaylists': {'uploads': 'UPLOADS'}}}]}
    if 'youtube/v3/playlistItems?' in url:
        return {'items': [{'contentDetails': {'videoId': 'a' * 11}}, {'contentDetails': {'videoId': 'b' * 11}}]}
    if 'youtube/v3/search?' in url:
        return {'items': [{'id': {'videoId': 'b' * 11}}]}
    if 'youtube/v3/videos?' in url:
        return {'items': [{'id': x * 11, 'snippet': {'title': f'Video {x}', 'publishedAt': '2026-10-01T00:00:00Z'},
                           'statistics': {'viewCount': str(n)}, 'contentDetails': {'duration': 'PT10M'}}
                          for x, n in [('a', 100), ('b', 30)]]}
    if 'api.crossref.org' in url:
        return {'message': {'title': ['Primary paper'], 'publisher': 'Publisher'}}
    if 'europepmc' in url:
        return {'hitCount': 1, 'resultList': {'result': [{'title': 'Discovery', 'doi': '10.1234/a', 'source': 'PPR'}]}}
    raise AssertionError('unexpected request')

class ResearchTests(unittest.TestCase):
    def test_real_config_is_valid(self):
        self.assertEqual(len(r.load_config(BASE / 'config.json')['channels']), 4)

    def test_invalid_doi_and_bounds_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            c = config(); c['candidates'][0]['doi'] = '../secret'
            path = Path(t) / 'c.json'; path.write_text(json.dumps(c))
            with self.assertRaises(ValueError): r.load_config(path)
            c['candidates'][0]['doi'] = '10.1234/a'; c['videos_per_channel'] = 51
            path.write_text(json.dumps(c))
            with self.assertRaises(ValueError): r.load_config(path)

    def test_collection_preserves_group_and_youtube_search_order(self):
        result = r.collect_youtube(config(), 'fake-key', fake_fetch)
        self.assertFalse(result['errors'])
        self.assertEqual([v['id'] for v in result['channels'][0]['videos']], ['a' * 11, 'b' * 11])
        self.assertEqual([v['id'] for v in result['candidate_searches'][0]['videos']], ['b' * 11])
        self.assertEqual(result['channels'][0]['videos'][0]['view_count'], '100')
        self.assertNotIn('fake-key', json.dumps(result))
        self.assertNotIn('ratio', result['channels'][0]['videos'][0])

    def test_partial_failure_does_not_masquerade_as_success(self):
        def fail_channel(url, key=None):
            if 'youtube/v3/channels?' in url: raise r.FetchError('HTTP 403')
            return fake_fetch(url, key)
        result = r.collect_youtube(config(), 'fake-key', fail_channel)
        self.assertEqual(result['channels'][0]['status'], 'error')
        self.assertEqual(result['candidate_searches'][0]['status'], 'ok')
        self.assertTrue(result['errors'])

    def test_missing_key_is_error_and_no_request(self):
        result = r.collect_youtube(config(), None, lambda *a, **k: self.fail('network should not run'))
        self.assertTrue(result['errors'])
        self.assertEqual(result['channels'], [])

    def test_science_discovery_source_is_kept_and_preprint_not_mislabelled(self):
        result = r.collect_science(config(), fake_fetch)
        self.assertFalse(result['errors'])
        self.assertEqual(result['discoveries'][0]['results'][0]['source'], 'PPR')
        self.assertEqual(result['candidates'][0]['title'], 'Primary paper')

    def test_report_labels_missing_and_does_not_fabricate_winner(self):
        report = r.make_report(config(), {'errors': ['No key']}, {'errors': ['Source unavailable']}, {'error': 'Not run'})
        self.assertIn('No key', report)
        self.assertIn('Source unavailable', report)
        self.assertIn('not yet selected', report)
        self.assertIn('Not an automated winner', report)
        self.assertIn('not automatically inspected', report)
        self.assertIn('Model error', report)

    def test_human_decision_requires_evidence_and_distinct_valid_choices(self):
        c = config()
        c['candidates'].append({'id': 'second', 'name': 'Second', 'question': 'Why?', 'doi': '10.1234/other', 'search': 'other'})
        review = {'recommended_id': 'sample', 'alternative_id': 'second', 'reason': 'Reason',
                  'science_limit': 'Unknown', 'visual_proof': 'Check rights', 'overlap': 'Existing video',
                  'alternative_reason': 'Strong backup', 'sources': ['https://example.test/source']}
        report = r.make_report(c, {}, {}, review=review)
        self.assertIn('Human recommendation:', report)
        self.assertIn('Strong backup', report)
        review['alternative_id'] = 'sample'
        with self.assertRaises(ValueError): r.validate_review(c, review)
        review['alternative_id'] = 'second'; review['sources'] = []
        with self.assertRaises(ValueError): r.validate_review(c, review)

    def test_markdown_escapes_table_separators(self):
        video = {'id': 'a' * 11, 'title': 'One | Two\nThree', 'view_count': '123'}
        table = '\n'.join(r.video_table([video]))
        self.assertIn('One \\| Two Three', table)

    def test_gate_detects_missing_and_report_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(r.main(['report', '--out', temp]), 0)
                self.assertEqual(r.main(['gate', '--out', temp]), 1)
            self.assertIn('did not run', (Path(temp) / 'REPORT.md').read_text())

    def test_gate_requires_all_success(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            cfg = config(); cfg_path = out / 'config.json'; cfg_path.write_text(json.dumps(cfg))
            r.save(out / 'youtube.json', r.collect_youtube(cfg, 'fake', fake_fetch))
            r.save(out / 'science.json', r.collect_science(cfg, fake_fetch))
            r.save(out / 'semantic.json', {'candidates': [{'matches': [{'title': 'example'}]}]})
            (out / 'REPORT.md').write_text('ok')
            args = ['gate', '--out', temp, '--config', str(cfg_path)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(r.main(args), 0)
                r.save(out / 'science.json', {'errors': ['fail']})
                self.assertEqual(r.main(args), 1)
                r.save(out / 'science.json', r.collect_science(cfg, fake_fetch))
                r.save(out / 'semantic.json', {'candidates': []})
                self.assertEqual(r.main(args), 1)

    def test_request_does_not_leak_key_on_http_error(self):
        from urllib.error import HTTPError
        class Broken:
            def open(self, req, timeout):
                raise HTTPError(req.full_url, 403, 'secret-like error text', {}, None)
        with patch.object(r.urllib.request, 'build_opener', return_value=Broken()):
            with self.assertRaises(r.FetchError) as exc:
                r.get_json('https://example.test', key='sensitive')
            self.assertEqual(str(exc.exception), 'HTTP 403')

if __name__ == '__main__': unittest.main()
