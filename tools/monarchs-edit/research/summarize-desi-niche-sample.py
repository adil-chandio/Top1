#!/usr/bin/env python3
"""Validate and summarize the frozen 20 Nov public YouTube extracts. No network."""

import csv
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATE = '2026-11-20'
VIDEO_ID = re.compile(r'[A-Za-z0-9_-]{11}\Z')


def load(kind):
    with (HERE / f'desi-niche-{kind}-{DATE}.csv').open(encoding='utf-8', newline='') as source:
        rows = list(csv.DictReader(source))
    assert rows and all(None not in row and all(value is not None for value in row.values()) for row in rows), kind
    return rows


def median(values):
    ordered = sorted(values)
    mid = len(ordered) // 2
    return ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def main():
    videos = load('videos')
    channels = load('channels')
    charts = load('charts')
    search = load('search-screen')
    groups, panels = defaultdict(list), defaultdict(list)
    ids = set()
    for row in videos:
        vid = row['video_id']
        assert VIDEO_ID.fullmatch(vid) and vid not in ids, vid
        ids.add(vid)
        assert row['source_url'] == f'https://www.youtube.com/watch?v={vid}', vid
        age = (date.fromisoformat(row['observed_on_utc']) - date.fromisoformat(row['date_on_watch'])).days
        assert age == int(row['age_calendar_days']) >= 0, vid
        assert int(row['duration_s']) > 0 and int(row['public_views']) >= 0, vid
        assert not row['public_likes'] or int(row['public_likes']) >= 0, vid
        if row['comparison_group']:
            groups[row['comparison_group']].append(row)

    for row in search:
        assert VIDEO_ID.fullmatch(row['video_id']), row['video_id']
        assert row['video_url'].endswith(row['video_id']), row['video_id']
        panels[row['panel_id']].append(row)
    for panel, rows in panels.items():
        assert sorted(int(row['extract_position']) for row in rows) == list(range(1, 6)), panel
        assert len({row['search_url'] for row in rows}) == 1 and len({row['video_id'] for row in rows}) == 5, panel

    assert len({row['handle'].lower() for row in channels}) == len(channels)
    assert all(date.fromisoformat(row['joined']) <= date.fromisoformat(row['observed_on_utc']) for row in channels)
    assert all(int(row['value_as_displayed_count']) >= 0 for row in charts)
    n_unique_cards = len({row['video_id'] for row in search})
    print(f'{len(videos)} direct videos / {len({r["channel"] for r in videos})} Watch channels; '
          f'{len(channels)} About snapshots; {len(charts)} chart observations; '
          f'{len(search)} search cards ({n_unique_cards} distinct IDs) / {len(panels)} query panels.')
    print('Only ledger-marked cohorts below. Single channel/format; use calendar ages, not matched hours.')
    for key, rows in groups.items():
        assert len(rows) > 1 and len({(r['channel'], r['format']) for r in rows}) == 1, key
        views = sorted(int(r['public_views']) for r in rows)
        ages = [int(r['age_calendar_days']) for r in rows]
        durations = [int(r['duration_s']) for r in rows]
        print(f'{key}: n={len(rows)}, age {min(ages)}–{max(ages)} calendar days, '
              f'{min(durations)}–{max(durations)}s, median {median(views):,}, '
              f'range {views[0]:,}–{views[-1]:,}, '
              f'top/sum {views[-1]/sum(views):.1%}, without top median {median(views[:-1]):,}')

    atm = next(r for r in videos if r['video_id'] == 'NArAKj4zbB8')
    discover = next(r for r in channels if r['handle'] == '@discoverinsideworld')
    print(f'Discover ATM Watch / channel About views (different cache times): '
          f'{int(atm["public_views"]) / int(discover["lifetime_views_display"]):.1%}')


if __name__ == '__main__':
    main()
