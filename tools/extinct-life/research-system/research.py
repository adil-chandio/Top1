#!/usr/bin/env python3
"""Bounded research collector; public sources only, no API-derived scores."""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
YT_API = 'https://www.googleapis.com/youtube/v3/'
AGENT = 'ExtinctLifeResearch/0.1 (research client)'
KEYS = ('YOUTUBE_API_KEY', 'YTAP1', 'YTAPI1', 'YT_KEY', 'YT_API_KEY')
ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
CHANNEL_ID = re.compile(r'^UC[A-Za-z0-9_-]{22}$')
DOI = re.compile(r'^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$')

class FetchError(Exception):
    pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def get_json(url, key=None):
    headers = {'User-Agent': AGENT, 'Accept': 'application/json'}
    if key:
        headers['X-Goog-Api-Key'] = key
    req = urllib.request.Request(url, headers=headers)
    # Never forward a credential on redirect; public source requests need no keys.
    opener = urllib.request.build_opener(NoRedirect()) if key else urllib.request.build_opener()
    try:
        with opener.open(req, timeout=25) as response:
            payload = response.read(3_000_001)
        if len(payload) > 3_000_000:
            raise FetchError('response exceeded size limit')
        return json.loads(payload)
    except urllib.error.HTTPError as exc:
        # Do not expose exception text, URL, response body or headers.
        raise FetchError(f'HTTP {exc.code}') from None
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        raise FetchError('network or JSON error') from None

def load_config(path):
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    if not (1 <= len(config['channels']) <= 8 and 1 <= len(config['candidates']) <= 5 and 1 <= len(config['science_queries']) <= 5):
        raise ValueError('config must have 1-8 channels and 1-5 candidates and science queries')
    for c in config['channels']:
        if not CHANNEL_ID.fullmatch(c['id']):
            raise ValueError('invalid channel ID')
    for c in config['candidates']:
        if not re.fullmatch(r'[a-z0-9-]{1,60}', c['id']) or not DOI.fullmatch(c['doi']):
            raise ValueError('invalid candidate ID or DOI')
    for field, maximum in [('videos_per_channel', 50), ('search_results_per_query', 15), ('science_results_per_query', 15)]:
        if not 1 <= config[field] <= maximum:
            raise ValueError('config result limit out of bounds')
    return config

def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def yt_request(endpoint, params, key, fetch=get_json):
    if endpoint not in ('channels', 'playlistItems', 'videos', 'search'):
        raise ValueError('unsupported endpoint')
    return fetch(YT_API + endpoint + '?' + urllib.parse.urlencode(params), key=key)

def video_details(ids, key, fetch=get_json):
    # Preserve YouTube's returned values, do not compute scores or rankings.
    ids = list(dict.fromkeys(x for x in ids if ID.fullmatch(x)))
    items = []
    for n in range(0, len(ids), 50):
        body = yt_request('videos', {'part': 'snippet,contentDetails,statistics', 'id': ','.join(ids[n:n+50]), 'maxResults': 50}, key, fetch)
        items.extend(body.get('items', []))
    return items

def compact_video(item):
    s, stats, content = item.get('snippet', {}), item.get('statistics', {}), item.get('contentDetails', {})
    thumbs = s.get('thumbnails', {})
    thumb = (thumbs.get('high') or thumbs.get('medium') or thumbs.get('default') or {}).get('url')
    return {'id': item.get('id'), 'title': s.get('title'), 'channel_title': s.get('channelTitle'),
            'published_at': s.get('publishedAt'), 'duration_iso8601': content.get('duration'),
            'view_count': stats.get('viewCount'), 'like_count': stats.get('likeCount'),
            'comment_count': stats.get('commentCount'), 'thumbnail_url': thumb}

def collect_youtube(config, key, fetch=get_json):
    output = {'source': 'YouTube Data API v3', 'retrieved_at': timestamp(), 'channels': [], 'candidate_searches': [], 'errors': []}
    if not key:
        output['errors'].append('No configured API key was available to this run.')
        return output
    for channel in config['channels']:
        group = {'requested_name': channel['name'], 'requested_id': channel['id'], 'videos': [], 'status': 'error'}
        output['channels'].append(group)
        try:
            body = yt_request('channels', {'part': 'snippet,contentDetails', 'id': channel['id']}, key, fetch)
            entries = body.get('items', [])
            if not entries:
                raise FetchError('channel not found or unavailable')
            record = entries[0]
            group['youtube_channel_title'] = record.get('snippet', {}).get('title')
            uploads = record.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
            if not uploads:
                raise FetchError('uploads playlist unavailable')
            page = yt_request('playlistItems', {'part': 'contentDetails', 'playlistId': uploads, 'maxResults': config['videos_per_channel']}, key, fetch)
            ids = [i.get('contentDetails', {}).get('videoId', '') for i in page.get('items', [])]
            items = {i.get('id'): compact_video(i) for i in video_details(ids, key, fetch)}
            group['videos'] = [items[i] for i in ids if i in items]
            if not group['videos']:
                raise FetchError('uploads returned no accessible videos')
            group['status'] = 'ok'
        except FetchError as exc:
            group['error'] = str(exc)
            output['errors'].append(f"Channel {channel['name']}: {exc}")
    for c in config['candidates']:
        group = {'candidate_id': c['id'], 'query': c['search'], 'videos': [], 'status': 'error'}
        output['candidate_searches'].append(group)
        try:
            found = yt_request('search', {'part': 'snippet', 'type': 'video', 'q': c['search'], 'order': 'relevance', 'maxResults': config['search_results_per_query']}, key, fetch)
            ids = [i.get('id', {}).get('videoId', '') for i in found.get('items', [])]
            items = {i.get('id'): compact_video(i) for i in video_details(ids, key, fetch)}
            group['videos'] = [items[i] for i in ids if i in items]
            group['status'] = 'ok'
        except FetchError as exc:
            group['error'] = str(exc)
            output['errors'].append(f"Search {c['id']}: {exc}")
    return output

def collect_science(config, fetch=get_json):
    result = {'source': 'Crossref and Europe PMC', 'retrieved_at': timestamp(), 'candidates': [], 'discoveries': [], 'errors': []}
    for c in config['candidates']:
        entry = {'candidate_id': c['id'], 'doi': c['doi'], 'status': 'error'}
        result['candidates'].append(entry)
        try:
            data = fetch('https://api.crossref.org/works/' + urllib.parse.quote(c['doi'], safe='/'))['message']
            entry.update({'title': (data.get('title') or [''])[0], 'publisher': data.get('publisher'), 'status': 'ok'})
        except (FetchError, KeyError, TypeError) as exc:
            entry['error'] = str(exc) if isinstance(exc, FetchError) else 'missing metadata'
            result['errors'].append(f"Crossref {c['id']}: {entry['error']}")
    for query in config['science_queries']:
        entry = {'query': query, 'status': 'error', 'results': []}
        result['discoveries'].append(entry)
        # Dynamic window is a discovery filter, not a scientific verification.
        first_year = dt.datetime.now(dt.timezone.utc).year - 2
        terms = f'TITLE_ABS:({query}) AND FIRST_PDATE:[{first_year}-01-01 TO 2100-01-01] sort_date:y'
        params = urllib.parse.urlencode({'query': terms, 'format': 'json', 'pageSize': config['science_results_per_query']})
        try:
            data = fetch('https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + params)
            entry.update({'status': 'ok', 'hit_count': data.get('hitCount'), 'results': [
                {'title': x.get('title'), 'doi': x.get('doi'), 'date': x.get('firstPublicationDate'),
                 'source': x.get('source'), 'journal': x.get('journalTitle'), 'id': x.get('id')}
                for x in data.get('resultList', {}).get('result', [])]})
        except FetchError as exc:
            entry['error'] = str(exc)
            result['errors'].append(f'Europe PMC discovery: {exc}')
    return result

def timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')

def esc(value):
    return str(value if value is not None else 'unavailable').replace('|', '\\|').replace('\r', ' ').replace('\n', ' ')

def video_table(videos):
    lines = ['| Video | Uploaded UTC | Duration | Views | Thumbnail |', '|---|---|---|---:|---|']
    for v in videos:
        vid = v.get('id', '')
        if not ID.fullmatch(vid):
            continue
        title = esc(v.get('title')).replace('[', r'\[').replace(']', r'\]')
        thumb = v.get('thumbnail_url') or ''
        thumb_link = f'[link]({thumb})' if thumb.startswith('https://i.ytimg.com/') else 'unavailable'
        lines.append(f"| [{title}](https://www.youtube.com/watch?v={vid}) | {esc(v.get('published_at'))} | {esc(v.get('duration_iso8601'))} | {esc(v.get('view_count'))} | {thumb_link} |")
    return lines

def validate_review(config, review):
    candidates = {c['id'] for c in config['candidates']}
    winner, alternative = review.get('recommended_id'), review.get('alternative_id')
    if winner not in candidates or alternative not in candidates or winner == alternative:
        raise ValueError('review needs different valid winner and alternative IDs')
    for field in ('reason', 'science_limit', 'visual_proof', 'overlap', 'alternative_reason'):
        if not isinstance(review.get(field), str) or not review[field].strip():
            raise ValueError('review missing required qualitative field')
    sources = review.get('sources')
    if not isinstance(sources, list) or not sources or not all(isinstance(x, str) and x.startswith('https://') for x in sources):
        raise ValueError('review needs HTTPS source links')
    return review

def make_report(config, youtube, science, semantic=None, review=None):
    lines = ['# Extinct Life — research desk', '', f'Generated UTC: {timestamp()}',
        '', '**Scope:** Read-only public-data research. Snapshot views are lifetime counts, not same-age counts, CTR, retention or a viral prediction. YouTube results are incomplete and thumbnails were not automatically inspected.',
        '', '**Policy gate:** No API-derived outlier ratios, scores, cross-channel aggregates, content tags or YouTube-based automated ranking are calculated. YouTube requires explicit approval for additional derived metrics; see README. Researcher must review evidence and choose an idea.',
        '', '## Topic decision worksheet', '', 'Not an automated winner. Mark each candidate after examining the scientific paper, competition, visual feasibility and rights. The scientific and YouTube sections are separate sources.', '']
    if review:
        review = validate_review(config, review)
        names = {c['id']: c['name'] for c in config['candidates']}
        lines += [f"**Human recommendation:** {esc(names[review['recommended_id']])}",
                  f"- Reason: {esc(review['reason'])}", f"- Science limit: {esc(review['science_limit'])}",
                  f"- Visual proof / rights: {esc(review['visual_proof'])}", f"- Existing coverage: {esc(review['overlap'])}",
                  f"- Alternative: {esc(names[review['alternative_id']])} — {esc(review['alternative_reason'])}",
                  *[f'- Source: {esc(s)}' for s in review['sources']], '']
    for c in config['candidates']:
        lines += [f"### {esc(c['name'])}", f"- Question: {esc(c['question'])}", f"- Primary paper: https://doi.org/{c['doi']}",
                  '- Science / certainty: **review required**', '- Existing coverage / meaningful difference: **review required**', '- Visual proof / rights: **review required**', '- Decision: **not yet selected**' if not review else '- Refer to human decision above.', '']
    lines += ['## YouTube channel inventories', '', f"Retrieved: {esc(youtube.get('retrieved_at'))}. Each group is a bounded recent uploads playlist, not a complete channel history. YouTube API source; no calculation of derived metrics.", '']
    for group in youtube.get('channels', []):
        lines += [f"### {esc(group.get('requested_name'))}", f"Status: {esc(group.get('status'))}", '']
        if group.get('error'): lines += [f"Error: {esc(group['error'])}", '']
        if group.get('videos'): lines += video_table(group['videos']) + ['']
    lines += ['## YouTube candidate search', '', 'Top results by YouTube API relevance, not exhaustive; search may include unrelated videos. Review each case manually.', '']
    for group in youtube.get('candidate_searches', []):
        lines += [f"### {esc(group.get('candidate_id'))}", f"Query: {esc(group.get('query'))} · status: {esc(group.get('status'))}", '']
        if group.get('error'): lines += [f"Error: {esc(group['error'])}", '']
        if group.get('videos'): lines += video_table(group['videos']) + ['']
    if youtube.get('errors'): lines += ['### YouTube errors', *[f'- {esc(e)}' for e in youtube['errors']], '']
    lines += ['## Scientific sources — separate from YouTube', '', 'Metadata and search leads only. PPR denotes a preprint; relevance, peer review, claims, image rights and full text are not automatically verified.', '']
    for c in science.get('candidates', []):
        lines += [f"- {esc(c.get('candidate_id'))}: {esc(c.get('title'))} — DOI {esc(c.get('doi'))} ({esc(c.get('status'))})"]
    for group in science.get('discoveries', []):
        lines += ['', f"### Discovery query: {esc(group.get('query'))} ({esc(group.get('status'))})", '']
        if group.get('error'): lines += [f"Error: {esc(group['error'])}"]
        for p in group.get('results', []):
            doi = p.get('doi')
            link = f'https://doi.org/{doi}' if doi and DOI.fullmatch(doi) else 'DOI unavailable'
            lines += [f"- {esc(p.get('date'))} — {esc(p.get('title'))} · source {esc(p.get('source'))} · {link}"]
    if science.get('errors'): lines += ['', '### Scientific-source errors', *[f'- {esc(e)}' for e in science['errors']]]
    if semantic:
        lines += ['', '## Model-assisted scientific lead matching', '', 'Local Hugging Face model compares only the independent scientific titles/questions, not YouTube API data. Similarity is not a probability, audience demand, scientific reliability or viral prediction. Validate against human labels.', '']
        for group in semantic.get('candidates', []):
            lines += [f"### {esc(group.get('candidate_id'))}"]
            for hit in group.get('matches', []):
                lines += [f"- {esc(hit.get('title'))} — cosine {esc(hit.get('similarity'))}; DOI {esc(hit.get('doi'))}"]
        if semantic.get('error'): lines += [f"Model error: {esc(semantic['error'])}"]
    lines += ['', '## Limits and next gate', '', '- Human review must separate observations from hypotheses and investigate reuse rights.', '- No competitor private CTR, retention, impressions, watch time or real-time velocity is available.', '- Search results and publication metadata are incomplete; missing or failed sources are not negative evidence.', '- No upload, script, narration or publication is performed by this tool.', '']
    return '\n'.join(lines)

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=('youtube', 'science', 'report', 'gate'))
    p.add_argument('--config', default=str(BASE / 'config.json'))
    p.add_argument('--out', required=True)
    p.add_argument('--review', help='Optional human-authored qualitative decision JSON (report command only)')
    args = p.parse_args(argv)
    config, out = load_config(args.config), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.command == 'youtube':
        key = next((os.environ.get(k) for k in KEYS if os.environ.get(k)), None)
        result = collect_youtube(config, key)
        save(out / 'youtube.json', result)
        print('::notice::YouTube collection status: ' + ('PARTIAL_OR_FAILED' if result['errors'] else 'OK'))
        for index, group in enumerate(result['channels'], 1):
            print(f"::notice::Configured channel {index}: {group['status']}")
        for index, group in enumerate(result['candidate_searches'], 1):
            print(f"::notice::Configured topic search {index}: {group['status']}")
        return 1 if result['errors'] else 0
    if args.command == 'science':
        result = collect_science(config)
        save(out / 'science.json', result)
        print('::notice::Scientific source collection status: ' + ('PARTIAL_OR_FAILED' if result['errors'] else 'OK'))
        return 1 if result['errors'] else 0
    if args.command == 'report':
        def read_or(path, fallback):
            return json.loads(path.read_text(encoding='utf-8')) if path.exists() else fallback
        yt = read_or(out / 'youtube.json', {'errors': ['YouTube collection did not run.']})
        science = read_or(out / 'science.json', {'errors': ['Science collection did not run.']})
        semantic = read_or(out / 'semantic.json', {'error': 'Semantic step did not run.'})
        review = validate_review(config, json.loads(Path(args.review).read_text(encoding='utf-8'))) if args.review else None
        (out / 'REPORT.md').write_text(make_report(config, yt, science, semantic, review), encoding='utf-8')
        print('Research report assembled; see short-lived Actions artifact. No YouTube API data printed in logs.')
        return 0
    missing = [name for name in ('youtube.json', 'science.json', 'semantic.json', 'REPORT.md') if not (out / name).exists()]
    errors = []
    for name in ('youtube.json', 'science.json'):
        path = out / name
        if path.exists() and json.loads(path.read_text(encoding='utf-8')).get('errors'):
            errors.append(name)
    sem = out / 'semantic.json'
    if sem.exists() and json.loads(sem.read_text(encoding='utf-8')).get('error'):
        errors.append('semantic.json')
    if missing or errors:
        print('Research quality gate: INCOMPLETE — missing or failed source(s), see artifact.')
        return 1
    print('Research quality gate: collection complete; expert review still required.')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, json.JSONDecodeError):
        print('Research system error: invalid configuration, data or output path; details suppressed.', file=sys.stderr)
        sys.exit(2)
