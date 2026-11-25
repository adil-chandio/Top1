#!/usr/bin/env python3
"""Deterministic tests for the outlier scanner -- no network, no API key."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
SCRIPT = ROOT / "tools/research-agent/outlier_scan.py"
SCHEMA = ROOT / "tools/research-agent/outlier_scan.schema.json"

spec = importlib.util.spec_from_file_location("outlier_scan", SCRIPT)
scan_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan_module)

KEY = "SENSITIVE_TEST_KEY_123"
VIDEO_A = "aaaaaaaaaa1"
VIDEO_B = "bbbbbbbbbb2"
CHANNEL_A = "UC" + "a" * 22
CHANNEL_B = "UC" + "b" * 22
PLAYLIST_A = "UU" + "a" * 22
PLAYLIST_B = "UU" + "b" * 22
NEIGHBOURS_A = [f"an{i:09d}" for i in range(12)]
NEIGHBOURS_B = [f"bn{i:09d}" for i in range(12)]
ANCHOR = "2026-10-01T12:00:00Z"


def video_item(video_id, channel, published, views, subs, title, duration="PT45S"):
    return {
        "id": video_id,
        "snippet": {
            "title": title, "channelId": channel, "channelTitle": f"Channel {channel[:4]}",
            "publishedAt": published, "thumbnails": {"high": {"url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"}},
        },
        "statistics": {"viewCount": str(views), "subscriberCount": str(subs)},
        "contentDetails": {"duration": duration},
    }


def build_fixture():
    base = {
        "id": {"videoId": VIDEO_A, "channelId": CHANNEL_A, "channelTitle": "Channel A"},
        "snippet": {"title": "Candidate A", "channelId": CHANNEL_A, "channelTitle": "Channel A", "publishedAt": ANCHOR},
    }
    other = {
        "id": {"videoId": VIDEO_B, "channelId": CHANNEL_B, "channelTitle": "Channel B"},
        "snippet": {"title": "Candidate B", "channelId": CHANNEL_B, "channelTitle": "Channel B", "publishedAt": ANCHOR},
    }
    a_details = video_item(VIDEO_A, CHANNEL_A, ANCHOR, 100_000, 50_000, "Ice on metal", "PT45S")
    b_details = video_item(VIDEO_B, CHANNEL_B, ANCHOR, 5_000, 500_000, "Big channel video", "PT120S")
    a_neighbours = [
        video_item(vid, CHANNEL_A, f"2026-09-{25 + i:02d}T12:00:00Z" if i < 6 else f"2026-10-{2 + i - 6:02d}T12:00:00Z",
                   10_000, 50_000, f"Upload {i}")
        for i, vid in enumerate(NEIGHBOURS_A)
    ]
    return {"responses": [
        {"endpoint": "search", "params": {}, "body": {"items": [base, other]}},
        {"endpoint": "videos", "params": {"id": f"{VIDEO_A},{VIDEO_B}"}, "body": {"items": [a_details, b_details]}},
        {"endpoint": "channels", "params": {}, "body": {"items": [
            {"id": CHANNEL_A, "contentDetails": {"relatedPlaylists": {"uploads": PLAYLIST_A}}},
            {"id": CHANNEL_B, "contentDetails": {"relatedPlaylists": {"uploads": PLAYLIST_B}}},
        ]}},
        {"endpoint": "playlistItems", "params": {"playlistId": PLAYLIST_A}, "body": {"items": [
            {"contentDetails": {"videoId": vid}} for vid in [VIDEO_A, *NEIGHBOURS_A]
        ]}},
        {"endpoint": "videos", "params": {"id": ",".join(NEIGHBOURS_A)}, "body": {"items": a_neighbours}},
    ]}


class OutlierScanTests(unittest.TestCase):
    def setUp(self):
        self.fixture = build_fixture()
        self.fetch = scan_module.FixtureFetch(self.fixture)

    def test_scan_filters_ranks_and_counts_quota(self):
        report = scan_module.scan(
            keywords=["everyday physics"], min_views=3_000, max_subs=100_000,
            min_ratio=2.0, fmt="short", lookback_days=180, key=None, fetch=self.fetch,
        )
        self.assertEqual(report["stats"]["candidates_seen"], 2)
        self.assertEqual(report["stats"]["qualified"], 1)
        self.assertEqual(report["outliers"][0]["video_id"], VIDEO_A)
        self.assertEqual(report["outliers"][0]["surrounding_sample_size"], 10)
        self.assertAlmostEqual(report["outliers"][0]["outlier_multiple"], 10.0, places=3)
        self.assertEqual(report["outliers"][0]["format_hint"], "short")
        self.assertGreater(report["stats"]["quota_units_estimate"], 100)
        self.assertEqual(report["stats"]["excluded"]["above-max-subscribers"], 1)
        self.assertEqual(report["outliers"][0]["url"], f"https://www.youtube.com/watch?v={VIDEO_A}")

    def test_median_excludes_candidate_and_requires_five_neighbours(self):
        uploads = [{"video_id": VIDEO_A, "published_at": ANCHOR, "views": 9_999_999}]
        uploads += [{"video_id": f"n{i:010d}", "published_at": f"2026-09-{20 + i:02d}T12:00:00Z", "views": 10_000}
                    for i in range(10)]
        median, sample = scan_module.median_surrounding(VIDEO_A, ANCHOR, uploads)
        self.assertEqual(median, 10_000.0)
        self.assertEqual(sample, 10)
        short = [{"video_id": "x0000000001", "published_at": ANCHOR, "views": 1}]
        self.assertEqual(scan_module.median_surrounding("y0000000001", ANCHOR, short), (None, 1))

    def test_key_never_appears_in_artifact(self):
        def leaky_fetch(url, key=None):
            raise scan_module.FetchError(f"HTTP 403 for {key} at {url}")

        report = scan_module.scan(
            keywords=["everyday physics"], min_views=3_000, max_subs=100_000,
            min_ratio=2.0, fmt="short", lookback_days=180, key=KEY, fetch=leaky_fetch,
        )
        self.assertTrue(report["errors"])
        self.assertNotIn(KEY, json.dumps(report))
        self.assertIn("[REDACTED]", " ".join(report["errors"]))

    def test_keyword_and_format_validation(self):
        with self.assertRaises(ValueError):
            scan_module.parse_keywords(",".join(str(i) for i in range(6)))
        with self.assertRaises(ValueError):
            scan_module.parse_keywords("physics;drop table")
        with self.assertRaises(ValueError):
            scan_module.parse_format("ultra")
        self.assertEqual(scan_module.parse_format("SHORT"), "short")

    def test_cli_fixture_mode_and_key_requirement(self):
        env = {k: v for k, v in os.environ.items() if k not in scan_module.KEY_NAMES}
        with tempfile.TemporaryDirectory() as tmp:
            fixture_path = Path(tmp) / "fixture.json"
            fixture_path.write_text(json.dumps(self.fixture), encoding="utf-8")
            out_path = Path(tmp) / "outlier_scan.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--fixture", str(fixture_path), "--out", str(out_path),
                 "--format", "short"],
                env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertIn("synthetic", data["source"])
            self.assertEqual(data["parameters"]["format"], "short")

            blocked = subprocess.run(
                [sys.executable, str(SCRIPT), "--keywords", "physics", "--out", str(Path(tmp) / "blocked.json")],
                env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("No YouTube API key", blocked.stderr)

    def test_artifact_matches_schema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema not installed")
        report = scan_module.scan(
            keywords=["everyday physics"], min_views=3_000, max_subs=100_000,
            min_ratio=2.0, fmt="short", lookback_days=180, key=None, fetch=self.fetch,
        )
        jsonschema.validate(report, json.loads(SCHEMA.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
