"""Descriptive metrics only; no view velocity, earnings or causal virality scores."""
import csv
import datetime as dt
import json
from pathlib import Path
import statistics
BASE=Path(__file__).parent

def metrics(entries):
    eligible=[x for x in entries if isinstance(x.get('view_count'),(int,float)) and x['view_count']>=0]
    counts=[x['view_count'] for x in eligible]
    total=sum(counts)
    return {'n_with_views':len(counts),'median_views':statistics.median(counts) if counts else None,'min_views':min(counts) if counts else None,'max_views':max(counts) if counts else None,'million_count':sum(v>=1000000 for v in counts),'top_two_share':sum(sorted(counts,reverse=True)[:2])/total if total else None}

def main():
    snap=json.loads((BASE/'data/snapshot.json').read_text());data=json.loads((BASE/'data/enrichment.json').read_text())
    unique={e['id']:e for s in snap['searches'] for e in s.get('entries',[]) if e.get('id')}
    cutoff=dt.datetime(2026,11,15,tzinfo=dt.timezone.utc).timestamp()
    rows=[]; videos=[]
    for c in data['channels']:
        d=c['data'];entries=d.get('entries',[])
        # Approximate dates are not exact publication receipts. Exclusion is conservative only.
        eligible=[e for e in entries if not e.get('timestamp') or e['timestamp']<cutoff]
        row={'handle':c['requested_handle'],'channel_id':d.get('channel_id') or d.get('id'),'followers_displayed':d.get('channel_follower_count'),'selection_reason':c['selection_reason'],'entries_returned':len(entries),'excluded_future_estimated_date':len(entries)-len(eligible),**metrics(eligible)}
        rows.append(row)
        for e in entries:videos.append({'handle':c['requested_handle'],'video_id':e.get('id'),'title':e.get('title'),'views_displayed':e.get('view_count'),'duration_s':e.get('duration'),'estimated_timestamp':e.get('timestamp'),'date_precision':'approximate_relative_date_not_API','excluded_future_estimate':bool(e.get('timestamp') and e['timestamp']>=cutoff),'url':'https://www.youtube.com/watch?v='+str(e.get('id',''))})
    for name,rs in [('channel_comparison.csv',rows),('video_inventory.csv',videos)]:
        with (BASE/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=rs[0].keys());w.writeheader();w.writerows(rs)
    summary={'discovery_queries':len(snap['searches']),'successful_discovery_queries':sum(s.get('status')=='success' for s in snap['searches']),'unique_discovery_videos':len(unique),'nonempty_discovery_channel_ids':len({e['channel_id'] for e in unique.values() if e.get('channel_id')}),'channels_attempted':len(rows),'channel_inventories_successful':sum(c['data']['status']=='success' for c in data['channels']),'inventory_entries':len(videos),'inventory_unique_video_ids':len({e['video_id'] for e in videos if e['video_id']}),'date_search_attempts':len(data['recent_searches']),'date_search_successes':sum(s['data']['status']=='success' for s in data['recent_searches']),'excluded_future_estimated_date':sum(r['excluded_future_estimated_date'] for r in rows),'date_warning':'Runner 2026-11-16 differs from trusted 2026-11-14; counters not backdated. Dates reconstructed from relative labels are not exact.','rows':rows}
    (BASE/'SUMMARY.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
