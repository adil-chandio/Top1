"""Bounded public metadata survey. Never logs request URLs or credentials.
Search is relevance-ranked, English/US-biased, not a representative market census.
Approximate upper quota budget: 800 search units + <100 other units.
No audiovisual, private retention, CTR, or impressions analysis is claimed.
"""
import datetime as dt
import json
import os
from pathlib import Path
import statistics
import urllib.request
import urllib.parse
import urllib.error

OUT = Path(__file__).parent / 'results'
KEY = os.environ.get('YOUTUBE_API_KEY', '')
NOW = dt.datetime.now(dt.timezone.utc)
QUERIES = [
    'bear encounter play dead', 'bear attack survival animation',
    'bear outside house why returns', 'crocodile encounter survival',
    'snake in house what to do', 'bee swarm attack survival',
    'shark encounter what to do', 'glass frog transparent blood',
]


def api(resource, **params):
    params['key'] = KEY
    url = 'https://www.googleapis.com/youtube/v3/' + resource + '?' + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=40) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not print exception strings: they may include credential-bearing URLs.
        reason = 'unknown'
        try:
            payload = json.load(exc)
            reason = payload['error']['errors'][0]['reason']
        except Exception:
            pass
        raise RuntimeError(f'YouTube API HTTP {exc.code}; reason={reason}') from None
    except Exception:
        raise RuntimeError('YouTube API network/parse failure; request details suppressed') from None


def batches(values, n=50):
    for i in range(0, len(values), n):
        yield values[i:i+n]


def video_records(ids):
    records = []
    for batch in batches(list(dict.fromkeys(ids))):
        records.extend(api('videos', part='snippet,statistics,contentDetails', id=','.join(batch))['items'])
    return records


def metric(v):
    s = v['snippet']
    stats = v.get('statistics', {})
    days = max(1, (NOW - dt.datetime.fromisoformat(s['publishedAt'].replace('Z', '+00:00'))).total_seconds()/86400)
    views = int(stats.get('viewCount', 0))
    return dict(id=v['id'], title=s['title'], channel_id=s['channelId'], channel=s['channelTitle'],
                published=s['publishedAt'], duration=v['contentDetails']['duration'], views=views,
                likes=int(stats.get('likeCount', 0)), comments=int(stats.get('commentCount', 0)),
                lifetime_views_per_day=round(views/days, 2),
                url='https://www.youtube.com/watch?v='+v['id'])


def main():
    if not KEY:
        raise RuntimeError('YOUTUBE_API_KEY is unavailable to workflow')
    provenance = {}
    # Include known references for a direct comparison even if search omits them.
    ids = ['o3_i8rDSMaE', 'v58WL-1TxNU', 's-zkGuh42l4', '0ztB7XsB3Do']
    searches = []
    for q in QUERIES:
        data = api('search', part='snippet', q=q, type='video', maxResults=25,
                   order='relevance', relevanceLanguage='en', regionCode='US')
        found = [item['id']['videoId'] for item in data['items']]
        searches.append({'query': q, 'ids': found})
        for vid in found:
            provenance.setdefault(vid, []).append(q)
        ids.extend(found)
    videos = video_records(ids)
    # Channel baselines for 12 strongest search matches by lifetime views.
    ranked = sorted(videos, key=lambda v: int(v.get('statistics', {}).get('viewCount', 0)), reverse=True)
    channel_ids = list(dict.fromkeys(v['snippet']['channelId'] for v in ranked))[:12]
    channels = api('channels', part='snippet,statistics,contentDetails', id=','.join(channel_ids))['items']
    baselines = []
    for channel in channels:
        playlist = channel['contentDetails']['relatedPlaylists']['uploads']
        items = api('playlistItems', part='contentDetails', playlistId=playlist, maxResults=25)['items']
        recent = video_records([v['contentDetails']['videoId'] for v in items])
        rows = [metric(v) for v in recent]
        baselines.append({'channel_id': channel['id'], 'channel': channel['snippet']['title'],
                          'recent_uploads': rows,
                          'median_recent_views': statistics.median([r['views'] for r in rows]) if rows else None,
                          'warning': 'Mixed formats and unequal upload ages; not normalized outperformance.'})
    rows = [dict(metric(v), matched_queries=provenance.get(v['id'], [])) for v in videos]
    result = {'collected_at_utc': NOW.isoformat(), 'searches': searches, 'videos': rows,
              'channel_baselines': baselines,
              'limitations': ['Single public snapshot: no current velocity measured.',
                               'Lifetime views/day is not recent growth.',
                               'Relevance sampling and query/channel selection bias.',
                               'Shorts and long videos not directly comparable; duration retained.',
                               'No private retention, CTR, impressions, demographics or causal proof.',
                               'No audiovisual inspection or safety validation performed by collector.']}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'public-evidence.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print(f'API successful; collected {len(rows)} videos and {len(baselines)} channel samples. No credentials exported.')


if __name__ == '__main__':
    main()
